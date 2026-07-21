"""Granular qwen-72b × R4 analysis (2026-07-21 follow-up questions).

1. FUNNEL per gold pair (averaged over the 3 passes): predicate found ->
   pair named -> positions correct -> distance correct; plus model-side
   precision and sentence-level verdicts.
2. VOTING CURVE: keep pairs appearing in >=1 / >=2 / ==3 of 3 passes ->
   pair + verdict metrics per threshold (the k-repetition intuition).
3. STABLE ERRORS: spurious pairs recurring in all 3 passes (categorized,
   with examples) and gold pairs never found in any pass (with sentence
   stats) -> common denominators.
4. PROBLEM SET: uids with verdict wrong (vs gold) in >=2 of 3 passes ->
   data/eval_problem.jsonl for the minimalist frontier probe.

Zero API calls. Output: docs/QWEN_R4_DEEP_DIVE.md + data/eval_problem.jsonl.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_pairs import T_LIMIT  # noqa: E402
from llm_io import parse_completion  # noqa: E402

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
_P = ".,;:!?„“”\"'()[]«»—–-"
norm = lambda s: str(s).strip(_P) if s is not None else ""  # noqa: E731


def main() -> None:
    gold = {json.loads(l)["uid"]: json.loads(l)
            for l in open(os.path.join(BASE, "data", "cltt_gold_pairs.jsonl"), encoding="utf-8")}
    units = {json.loads(l)["uid"]: json.loads(l)
             for l in open(os.path.join(BASE, "data", "eval_units.jsonl"), encoding="utf-8")}

    runs: dict[int, dict[str, dict]] = defaultdict(dict)
    for l in open(os.path.join(BASE, "results", "runs", "qwen-72b.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        if r["formulation"] == "r4":
            runs[r["run_index"]][r["uid"]] = parse_completion(r.get("completion_text"))

    def mpairs(parsed):
        out = []
        for q in (parsed["pairs"] or []):
            if isinstance(q, dict) and isinstance(q.get("podmet_index"), int) \
                    and isinstance(q.get("prisudek_index"), int):
                d = q.get("vzdalenost")
                out.append({"s": norm(q.get("podmet")), "p": norm(q.get("prisudek")),
                            "si": q["podmet_index"], "pi": q["prisudek_index"],
                            "d": d if isinstance(d, int) else abs(q["podmet_index"] - q["prisudek_index"]) - 1})
        return out

    gk = lambda gp: (norm(gp.get("subj_word_form") or gp["subj_form"]),  # noqa: E731
                     norm(gp["pred_word_form"]))

    # ---------------- 1. funnel (pooled over runs)
    F = Counter()
    n_model_pairs = 0
    for run in (1, 2, 3):
        for uid, g in gold.items():
            parsed = runs[run].get(uid)
            if parsed is None:
                continue
            mp = mpairs(parsed)
            n_model_pairs += len(mp)
            avail = list(mp)
            preds_avail = [m["p"] for m in mp]
            for gp in g["pairs"]:
                F["gold"] += 1
                s, p = gk(gp)
                if p in preds_avail:
                    F["pred_found"] += 1
                m = next((x for x in avail if x["s"] == s and x["p"] == p), None)
                if m is None:
                    continue
                avail.remove(m)
                F["pair_named"] += 1
                si_ok = m["si"] == gp["subj_word_idx"]
                pi_ok = m["pi"] == gp["pred_word_idx"]
                F["subj_pos_ok"] += si_ok
                F["pred_pos_ok"] += pi_ok
                F["both_pos_ok"] += si_ok and pi_ok
                F["dist_ok"] += m["d"] == gp["distance"]
                F["fully_ok"] += (m["d"] == gp["distance"]) and si_ok and pi_ok

    # ---------------- 2. voting curve + 3. stable errors + 4. problem set
    curve = {}
    stable_spur = Counter()
    stable_spur_ex = []
    never_found = []
    wrong_verdict_runs = Counter()
    for thr in (1, 2, 3):
        cm = Counter()
        hits = pred_n = gold_n = 0
        for uid, g in gold.items():
            counts = Counter()
            dists = defaultdict(list)
            per_run_verdict_wrong = 0
            for run in (1, 2, 3):
                parsed = runs[run].get(uid)
                if parsed is None:
                    continue
                mv = parsed["has_violation"] if parsed["has_violation"] is not None else False
                if bool(mv) != g["verdict"]:
                    per_run_verdict_wrong += 1
                seen = set()
                for m in mpairs(parsed):
                    k = (m["s"], m["p"])
                    if k in seen:
                        continue
                    seen.add(k)
                    counts[k] += 1
                    dists[k].append(m["d"])
            if thr == 1:
                wrong_verdict_runs[uid] = per_run_verdict_wrong
                gkeys = Counter(gk(gp) for gp in g["pairs"])
                for k, c in counts.items():
                    if c == 3 and not gkeys.get(k):
                        stable_spur[uid] += 1
                        if len(stable_spur_ex) < 12:
                            stable_spur_ex.append((uid, k, dists[k]))
                found_keys = set(counts)
                for gp in g["pairs"]:
                    if gk(gp) not in found_keys:
                        never_found.append((uid, gp))
            voted = {k: sorted(ds)[len(ds) // 2] for k, ds in dists.items() if counts[k] >= thr}
            vv = any(d > T_LIMIT for d in voted.values())
            cm[(g["verdict"], vv)] += 1
            gkeys = Counter(gk(gp) for gp in g["pairs"])
            avail = Counter(gkeys)
            for k in voted:
                if avail.get(k):
                    avail[k] -= 1
                    hits += 1
            pred_n += len(voted)
            gold_n += len(g["pairs"])
        tp, fp = cm[(True, True)], cm[(False, True)]
        fn, tn = cm[(True, False)], cm[(False, False)]
        P = tp / (tp + fp) if tp + fp else 0
        R = tp / (tp + fn) if tp + fn else 0
        pp = hits / pred_n if pred_n else 0
        pr = hits / gold_n if gold_n else 0
        curve[thr] = dict(vP=P, vR=R, vF=2 * P * R / (P + R) if P + R else 0,
                          pP=pp, pR=pr, pF=2 * pp * pr / (pp + pr) if pp + pr else 0,
                          fp=fp, fn=fn)

    # never-found stats
    nf_stats = Counter()
    nf_viol = []
    for uid, gp in never_found:
        g = gold[uid]
        nf_stats["total"] += 1
        nf_stats[f"pairs/sent={min(len(g['pairs']),3)}{'+' if len(g['pairs'])>=3 else ''}"] += 1
        if gp["subj_is_rel"]:
            nf_stats["rel_pron"] += 1
        if gp["distance"] > T_LIMIT:
            nf_stats["VIOLATING (d>6)"] += 1
            if len(nf_viol) < 8:
                nf_viol.append((uid, gk(gp), gp["distance"], units[uid]["n_words"]))

    # problem set: verdict wrong in >=2 runs
    problem = [uid for uid, c in wrong_verdict_runs.items() if c >= 2]
    with open(os.path.join(BASE, "data", "eval_problem.jsonl"), "w", encoding="utf-8") as fh:
        for uid in sorted(problem):
            fh.write(json.dumps({"uid": uid, "text": units[uid]["text"],
                                 "n_words": units[uid]["n_words"]}, ensure_ascii=False) + "\n")

    # ---------------- report
    L = []
    w = L.append
    g_n = F["gold"]
    w("# qwen-72b × R4 — deep dive")
    w("")
    w("## 1. The funnel (per gold pair, pooled over 3 passes; N = %d pair-evaluations)" % g_n)
    w("")
    w("| stage | rate |")
    w("|---|--:|")
    w(f"| predicate word emitted in SOME pair | {100*F['pred_found']/g_n:.1f}% |")
    w(f"| full pair named (subject + predicate) | {100*F['pair_named']/g_n:.1f}% |")
    w(f"| … subject position exact (given named) | {100*F['subj_pos_ok']/F['pair_named']:.1f}% |")
    w(f"| … predicate position exact (given named) | {100*F['pred_pos_ok']/F['pair_named']:.1f}% |")
    w(f"| … both positions exact (given named) | {100*F['both_pos_ok']/F['pair_named']:.1f}% |")
    w(f"| … distance exact (given named) | {100*F['dist_ok']/F['pair_named']:.1f}% |")
    w(f"| pair fully correct end-to-end (named+positions+distance) | {100*F['fully_ok']/g_n:.1f}% of gold |")
    w(f"| model pairs emitted per sentence (avg) | {n_model_pairs/3/len(gold):.2f} |")
    w("")
    w("## 2. Voting curve (keep pairs appearing in ≥k of 3 passes)")
    w("")
    w("| k | pair P | pair R | pair F1 | verdict P | verdict R | verdict F1 | FP | FN |")
    w("|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for thr in (1, 2, 3):
        c = curve[thr]
        w(f"| {thr} | {100*c['pP']:.1f} | {100*c['pR']:.1f} | {100*c['pF']:.1f} "
          f"| {100*c['vP']:.1f} | {100*c['vR']:.1f} | **{100*c['vF']:.1f}** | {c['fp']} | {c['fn']} |")
    w("")
    w("## 3a. Stable spurious pairs (in ALL 3 passes, not in gold)")
    w("")
    w(f"- sentences affected: {len(stable_spur)}; stable spurious pairs: {sum(stable_spur.values())}")
    w("- examples (uid, pair, per-run distances):")
    for uid, k, ds in stable_spur_ex:
        w(f"  - `{uid.split('::')[0].split('/')[-1]}::{uid.split('::')[1]}` "
          f"**{k[0]} ↔ {k[1]}** d={ds} — {units[uid]['text'][:90]}…")
    w("")
    w("## 3b. Gold pairs never found in ANY pass")
    w("")
    w(f"- {dict(nf_stats)}")
    w("- violating (d>6) never-found examples:")
    for uid, k, d, nw in nf_viol:
        w(f"  - d={d}, sent {nw}w: **{k[0]} ↔ {k[1]}** — {units[uid]['text'][:90]}…")
    w("")
    w(f"## 4. Problem set: {len(problem)} sentences with wrong verdict in ≥2/3 passes")
    w("")
    w("→ `data/eval_problem.jsonl` (frontier probe target).")
    w("")
    out = os.path.join(BASE, "docs", "QWEN_R4_DEEP_DIVE.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
