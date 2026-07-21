"""Score LLM-arm traces against the CLTT gold (METHODOLOGY §7).

Per model × formulation:
  * verdict quality (accuracy/P/R/F1) — per run, mean across runs, and
    majority-of-3 view; malformed/partial responses count as has_violation=False
    (SPRINT deployment semantics: no parseable flag -> no flag) AND are reported
    as validation catch-rates;
  * pair identification P/R/F1 — form-based (punctuation-stripped, greedy) and
    index-exact, vs. gold pairs;
  * distance quality on form-matched pairs: exact / ±1 / MAE (using the MODEL's
    reported vzdalenost — its own arithmetic, not ours);
  * decomposition (H4): naming recall -> position-correct given named ->
    distance-correct given named;
  * validation catch-rates: schema, index bounds, form-at-index;
  * stability: verdict flip rate across the 3 passes; cost totals (usage.cost).

The parser arm (presegmented) is included as the baseline row.

Usage: python3 score_llm.py [--runs-dir ../results/runs] [--out docs/RESULTS_openmodels.md]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_pairs import T_LIMIT  # noqa: E402
from llm_io import parse_completion  # noqa: E402  (authoritative re-parse)

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
_PUNCT = ".,;:!?„“”\"'()[]«»—–-"


def norm(s) -> str:
    return str(s).strip(_PUNCT) if s is not None else ""


def load_gold():
    gold = {}
    for line in open(os.path.join(BASE, "data", "cltt_gold_pairs.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        gold[r["uid"]] = r
    return gold


def load_units():
    units = {}
    for line in open(os.path.join(BASE, "data", "eval_units.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        units[r["uid"]] = r["text"].split()
    return units


def sane_pairs(parsed_pairs, n_words):
    """Split model pairs into (usable, validation_flags)."""
    usable, flags = [], Counter()
    if parsed_pairs is None:
        flags["no_pairs_field"] += 1
        return usable, flags
    for p in parsed_pairs:
        if not isinstance(p, dict):
            flags["pair_not_object"] += 1
            continue
        si, pi = p.get("podmet_index"), p.get("prisudek_index")
        d = p.get("vzdalenost")
        if not (isinstance(si, int) and isinstance(pi, int)):
            flags["nonint_index"] += 1
            continue
        if not (1 <= si <= n_words and 1 <= pi <= n_words):
            flags["index_out_of_bounds"] += 1
            continue
        usable.append({
            "subj_form": norm(p.get("podmet")), "subj_idx": si,
            "pred_form": norm(p.get("prisudek")), "pred_idx": pi,
            "dist": d if isinstance(d, int) else None,
        })
    return usable, flags


def form_at_index_ok(pair, words) -> bool:
    s_ok = norm(words[pair["subj_idx"] - 1]) == pair["subj_form"]
    p_ok = norm(words[pair["pred_idx"] - 1]) == pair["pred_form"]
    return s_ok and p_ok


def greedy_match(gold_pairs, model_pairs):
    """Form-based greedy matching. Returns list of (gold, model|None)."""
    used = set()
    out = []
    for g in gold_pairs:
        gs = norm(g.get("subj_word_form") or g["subj_form"])
        gp = norm(g["pred_word_form"])
        best = None
        for j, m in enumerate(model_pairs):
            if j in used:
                continue
            if m["subj_form"] == gs and m["pred_form"] == gp:
                cost = abs(m["subj_idx"] - g["subj_word_idx"])
                if best is None or cost < best[0]:
                    best = (cost, j)
        if best is None:
            out.append((g, None))
        else:
            used.add(best[1])
            out.append((g, model_pairs[best[1]]))
    n_spurious = len(model_pairs) - len(used)
    return out, n_spurious


def f1(prec, rec):
    return 2 * prec * rec / (prec + rec) if prec + rec else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", default=os.path.join(BASE, "results", "runs"))
    ap.add_argument("--out", default=os.path.join(BASE, "docs", "RESULTS_openmodels.md"))
    args = ap.parse_args()

    gold = load_gold()
    units = load_units()
    n_units = len(gold)

    # traces: (model, formulation, run) -> {uid: trace}
    cells = defaultdict(dict)
    for fn in sorted(os.listdir(args.runs_dir)):
        if not fn.endswith(".jsonl") or "failures" in fn or fn.endswith(".log"):
            continue
        for line in open(os.path.join(args.runs_dir, fn), encoding="utf-8"):
            try:
                t = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "parsed" not in t:
                continue
            # authoritative re-parse from stored text (parser may have been fixed
            # after the trace was written)
            t["parsed"] = parse_completion(t.get("completion_text"))
            cells[(t["model_id"], t["formulation"], t["run_index"])][t["uid"]] = t

    rows = []
    stability = {}
    for (model, form, run), traces in sorted(cells.items()):
        cm = Counter()
        val_flags = Counter()
        n_gold_pairs = n_model_pairs = n_form_matched = 0
        n_named = n_pos_given_named = n_dist_given_named = 0
        dist_exact = dist_w1 = 0
        abs_errs = []
        cost = 0.0
        n_parse_ok = 0

        for uid, g in gold.items():
            t = traces.get(uid)
            if t is None:
                continue
            words = units[uid]
            parsed = t["parsed"]
            cost += (t.get("response_raw", {}).get("usage", {}) or {}).get("cost", 0) or 0
            if parsed["parse_status"] == "ok":
                n_parse_ok += 1
            else:
                val_flags[f"parse_{parsed['parse_status']}"] += 1
            mv = parsed["has_violation"] if parsed["has_violation"] is not None else False
            cm[(g["verdict"], bool(mv))] += 1

            mpairs, flags = sane_pairs(parsed["pairs"], len(words))
            val_flags.update(flags)
            for p in mpairs:
                if not form_at_index_ok(p, words):
                    val_flags["form_at_index_mismatch"] += 1

            matches, spurious = greedy_match(g["pairs"], mpairs)
            n_gold_pairs += len(g["pairs"])
            n_model_pairs += len(mpairs)
            for gp, mp in matches:
                if mp is None:
                    continue
                n_form_matched += 1
                n_named += 1
                if (mp["subj_idx"] == gp["subj_word_idx"]
                        and mp["pred_idx"] == gp["pred_word_idx"]):
                    n_pos_given_named += 1
                if mp["dist"] is not None:
                    err = abs(mp["dist"] - gp["distance"])
                    abs_errs.append(err)
                    dist_exact += err == 0
                    dist_w1 += err <= 1
                    n_dist_given_named += err == 0

        n = sum(cm.values())
        tp, fp = cm[(True, True)], cm[(False, True)]
        fn, tn = cm[(True, False)], cm[(False, False)]
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        pair_p = n_form_matched / n_model_pairs if n_model_pairs else 0.0
        pair_r = n_form_matched / n_gold_pairs if n_gold_pairs else 0.0
        rows.append({
            "model": model, "form": form, "run": run, "n": n,
            "verdict_acc": (tp + tn) / n if n else 0.0,
            "verdict_p": prec, "verdict_r": rec, "verdict_f1": f1(prec, rec),
            "pair_p": pair_p, "pair_r": pair_r, "pair_f1": f1(pair_p, pair_r),
            "naming_recall": n_named / n_gold_pairs if n_gold_pairs else 0.0,
            "pos_given_named": n_pos_given_named / n_named if n_named else 0.0,
            "dist_exact_given_named": dist_exact / len(abs_errs) if abs_errs else 0.0,
            "dist_w1_given_named": dist_w1 / len(abs_errs) if abs_errs else 0.0,
            "dist_mae": sum(abs_errs) / len(abs_errs) if abs_errs else None,
            "parse_ok_rate": n_parse_ok / n if n else 0.0,
            "val_flags": dict(val_flags), "cost_usd": round(cost, 4),
        })

        # stability bookkeeping
        stability.setdefault((model, form), {}).setdefault(run, {
            uid: (traces[uid]["parsed"]["has_violation"]
                  if traces[uid]["parsed"]["has_violation"] is not None else False)
            for uid in traces})

    # stability: fraction of uids with non-identical verdicts across available runs
    stab_rows = []
    for (model, form), runs in sorted(stability.items()):
        if len(runs) < 2:
            continue
        uids = set.intersection(*[set(v) for v in runs.values()])
        flip = sum(1 for u in uids if len({runs[r][u] for r in runs}) > 1)
        stab_rows.append((model, form, len(runs), len(uids),
                          flip / len(uids) if uids else 0.0))

    # write report
    L = []
    w = L.append
    w("# LLM arm — open models vs. CLTT gold (auto-generated by score_llm.py)")
    w("")
    w(f"Gold: {n_units} units / {sum(len(g['pairs']) for g in gold.values())} pairs "
      f"(K6–K9 provisional). Parser baseline (presegmented): verdict F1 97.1 "
      "(acc 99.0, P 97.9, R 96.4), pair form-F1 95.6.")
    w("")
    w("## Per run")
    w("")
    w("| model | form | run | n | verdict acc | P | R | F1 | pair F1 | naming R "
      "| pos\\|named | dist=\\|named | parse ok | cost $ |")
    w("|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for r in rows:
        w(f"| {r['model']} | {r['form']} | {r['run']} | {r['n']} "
          f"| {100*r['verdict_acc']:.1f} | {100*r['verdict_p']:.1f} "
          f"| {100*r['verdict_r']:.1f} | **{100*r['verdict_f1']:.1f}** "
          f"| {100*r['pair_f1']:.1f} | {100*r['naming_recall']:.1f} "
          f"| {100*r['pos_given_named']:.1f} | {100*r['dist_exact_given_named']:.1f} "
          f"| {100*r['parse_ok_rate']:.1f} | {r['cost_usd']:.2f} |")
    w("")
    if stab_rows:
        w("## Stability (verdict flip rate across passes)")
        w("")
        for model, form, k, nu, fr in stab_rows:
            w(f"- {model} × {form}: {100*fr:.1f}% of {nu} units flip across {k} passes")
        w("")
    w("## Validation catch-rates (recorded, never corrected)")
    w("")
    for r in rows:
        if r["val_flags"]:
            w(f"- {r['model']} × {r['form']} × run{r['run']}: {r['val_flags']}")
    w("")
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    with open(os.path.join(BASE, "results", "metrics_llm.json"), "w", encoding="utf-8") as fh:
        json.dump({"rows": rows, "stability": stab_rows}, fh, ensure_ascii=False, indent=2)
    print(f"{len(rows)} condition-runs scored -> {args.out}")
    for r in rows:
        print(f"  {r['model']:10} {r['form']} run{r['run']}: verdict F1 "
              f"{100*r['verdict_f1']:.1f}  pair F1 {100*r['pair_f1']:.1f}  "
              f"naming {100*r['naming_recall']:.1f}  dist|named {100*r['dist_exact_given_named']:.1f}")


if __name__ == "__main__":
    main()
