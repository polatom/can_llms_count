"""Error analysis of the parser arm (answers to 2026-07-20 questions).

Q1  End-to-end distance performance: per GOLD pair — found with exact distance /
    found with wrong distance / missed entirely (form-based matching). This is
    stricter than "distance on matched pairs".
Q2  Cause decomposition: verdict false negatives (gold violation, parser clean)
    and false positives, categorized (violating pair missed vs. found-but-
    mismeasured vs. spurious), cross-tabbed with UDPipe re-segmentation.
    Miss-rate by construction type, gold distance, split status.
Q3  Sensitivity to Katka's pending answers: K8 rescore (relative-pronoun
    subject pairs excluded from both sides), K7 prevalence in CLTT.

Output: docs/PARSER_ARM_ERROR_ANALYSIS.md (+ stdout summary).
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_pairs import T_LIMIT  # noqa: E402

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def kind_of(p: dict) -> str:
    if p["pred_in_mwt"]:
        return "aby/kdyby"
    if p["pred_mood_cnd"]:
        return "conditional"
    if p["pred_is_cop"]:
        return "copular-past" if p["pred_verbform"] == "Part" else "copular"
    if p["pred_is_aux"]:
        return "passive/analytic-aux"
    return "finite-verb"


def dbucket(d: int) -> str:
    return "0-1" if d <= 1 else "2-4" if d <= 4 else "5-9" if d <= 9 else "10+"


def greedy_form_match(gold: list[dict], pred: list[dict]):
    used = set()
    out = []  # (gold_pair, pred_pair | None)
    for g in gold:
        best = None
        for j, p in enumerate(pred):
            if j in used:
                continue
            if p["subj_form"] == g["subj_form"] and p["pred_word_form"] == g["pred_word_form"]:
                cost = abs(p["subj_word_idx"] - g["subj_word_idx"])
                if best is None or cost < best[0]:
                    best = (cost, j)
        if best is None:
            out.append((g, None))
        else:
            used.add(best[1])
            out.append((g, pred[best[1]]))
    spurious = [p for j, p in enumerate(pred) if j not in used]
    return out, spurious


def verdict(pairs, exclude_rel=False) -> bool:
    return any(p["distance"] > T_LIMIT for p in pairs
               if not (exclude_rel and p.get("subj_is_rel")))


def main() -> None:
    gold = {json.loads(l)["uid"]: json.loads(l)
            for l in open(os.path.join(BASE, "data", "cltt_gold_pairs.jsonl"),
                          encoding="utf-8")}
    parser = {json.loads(l)["uid"]: json.loads(l)
              for l in open(os.path.join(BASE, "data", "parser_arm",
                                         "parser_pairs.jsonl"), encoding="utf-8")}

    # --- Q1: per-gold-pair end-to-end status
    status = Counter()
    err_dist = Counter()  # |Δd| for found-wrong
    miss_by_kind = Counter()
    all_by_kind = Counter()
    miss_by_db = Counter()
    all_by_db = Counter()
    miss_by_split = Counter()
    all_by_split = Counter()
    miss_rel = Counter()

    fn_causes = Counter()
    fp_causes = Counter()
    fn_split = Counter()

    cm = Counter()
    cm_norel = Counter()
    k7 = 0

    for uid, g in gold.items():
        p = parser[uid]
        split = "split" if p["n_subsentences"] > 1 else "whole"
        k7 += g["nonverbal_nsubj_excluded"]
        matches, spurious = greedy_form_match(g["pairs"], p["pairs"])

        for gp, pp in matches:
            k = kind_of(gp)
            db = dbucket(gp["distance"])
            all_by_kind[k] += 1
            all_by_db[db] += 1
            all_by_split[split] += 1
            if pp is None:
                status["missed"] += 1
                miss_by_kind[k] += 1
                miss_by_db[db] += 1
                miss_by_split[split] += 1
                miss_rel["rel" if gp.get("subj_is_rel") else "nonrel"] += 1
            elif pp["distance"] == gp["distance"]:
                status["found_exact"] += 1
            else:
                status["found_wrong_dist"] += 1
                err_dist[min(abs(pp["distance"] - gp["distance"]), 5)] += 1

        # verdict confusions
        gv, pv = g["verdict"], p["verdict"]
        cm[(gv, pv)] += 1
        gnr = verdict(g["pairs"], exclude_rel=True)
        pnr = verdict(p["pairs"], exclude_rel=True)
        cm_norel[(gnr, pnr)] += 1

        # FN cause decomposition
        if gv and not pv:
            fn_split[split] += 1
            viol = [(gp, pp) for gp, pp in matches if gp["distance"] > T_LIMIT]
            if all(pp is None for gp, pp in viol):
                fn_causes["all_violating_pairs_missed"] += 1
            elif any(pp is not None and pp["distance"] <= T_LIMIT for gp, pp in viol):
                fn_causes["violating_pair_found_but_underestimated"] += 1
            else:
                fn_causes["mixed"] += 1
        if pv and not gv:
            over = [q for q in p["pairs"] if q["distance"] > T_LIMIT]
            matched_preds = {id(pp) for _g, pp in matches if pp is not None}
            if any(id(q) not in matched_preds for q in over):
                fp_causes["spurious_pair_over_threshold"] += 1
            else:
                fp_causes["matched_pair_overestimated"] += 1

    n_gold = sum(all_by_kind.values())

    def pct(a, b):
        return f"{100.0*a/b:.1f}%" if b else "n/a"

    def vm(c):
        tp, fp = c[(True, True)], c[(False, True)]
        fn, tn = c[(True, False)], c[(False, False)]
        n = tp + fp + fn + tn
        prec = tp / (tp + fp) if tp + fp else 0
        rec = tp / (tp + fn) if tp + fn else 0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
        return (f"acc {pct(tp+tn, n)}, P {100*prec:.1f}%, R {100*rec:.1f}%, "
                f"F1 {100*f1:.1f}% (TP {tp} FP {fp} FN {fn} TN {tn})")

    L = []
    w = L.append
    w("# Parser arm — error analysis (Q1–Q3, 2026-07-20)")
    w("")
    w("## Q1 — end-to-end distance performance (per GOLD pair, form matching)")
    w("")
    w("| status | pairs | share |")
    w("|---|--:|--:|")
    w(f"| found, distance exact | {status['found_exact']} | {pct(status['found_exact'], n_gold)} |")
    w(f"| found, distance wrong | {status['found_wrong_dist']} | {pct(status['found_wrong_dist'], n_gold)} |")
    w(f"| missed entirely | {status['missed']} | {pct(status['missed'], n_gold)} |")
    w("")
    w(f"Distance-wrong error sizes |Δd| (5 = 5+): {dict(sorted(err_dist.items()))}")
    w("")
    w("## Q2 — where the errors come from")
    w("")
    w("**Miss rate by unit segmentation:** "
      f"whole units {pct(miss_by_split['whole'], all_by_split['whole'])} "
      f"({miss_by_split['whole']}/{all_by_split['whole']}), "
      f"split units {pct(miss_by_split['split'], all_by_split['split'])} "
      f"({miss_by_split['split']}/{all_by_split['split']})")
    w("")
    w("**Miss rate by gold distance:** "
      + ", ".join(f"{b}: {pct(miss_by_db[b], all_by_db[b])} ({miss_by_db[b]}/{all_by_db[b]})"
                  for b in ["0-1", "2-4", "5-9", "10+"]))
    w("")
    w("**Miss rate by construction:** "
      + ", ".join(f"{k}: {pct(miss_by_kind[k], all_by_kind[k])} ({miss_by_kind[k]}/{all_by_kind[k]})"
                  for k, _ in all_by_kind.most_common()))
    w("")
    w(f"**Missed pairs, rel-pron vs other subjects:** {dict(miss_rel)}")
    w("")
    w(f"**Verdict FN causes ({sum(fn_causes.values())} sentences):** {dict(fn_causes)}; "
      f"by segmentation: {dict(fn_split)}")
    w(f"**Verdict FP causes ({sum(fp_causes.values())} sentences):** {dict(fp_causes)}")
    w("")
    w("## Q3 — sensitivity to Katka's pending answers")
    w("")
    w(f"- **K8 (exclude relative-pronoun-subject pairs from both sides):** verdict {vm(cm_norel)}")
    w(f"  vs. current {vm(cm)}")
    w(f"- **K7 (verbless clauses) prevalence in CLTT:** {k7} excluded subject edges "
      f"(vs. 1,586 pairs) — negligible either way.")
    w("- **K6 (per-conjunct pairs):** would apply the same rule change to gold and parser arm")
    w("  symmetrically (shared extraction code); it can add violating pairs on both sides but")
    w("  cannot fix parse/segmentation errors — direction: roughly neutral, recomputable.")
    w("")
    with open(os.path.join(BASE, "docs", "PARSER_ARM_ERROR_ANALYSIS.md"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
