"""Deep error analysis of qwen-72b × R4 (best open config) vs. CLTT gold.

Answers (2026-07-21): where exactly does it fail, and is cross-pass majority
voting a free precision fix? All from stored traces — zero API calls.

1. Verdict FP/FN causes per run + majority-of-3.
2. Naming-miss breakdown (pairs/sentence, construction, rel-pron, distance).
3. Spurious-pair categories (invented subject / wrong pairing / duplicates).
4. Pair-level cross-run stability: do spurious pairs reproduce across passes
   the way real ones do? -> simulated VOTING arm: keep pairs appearing in >=2
   of 3 runs (median distance), recompute verdicts, score.

Output: docs/QWEN_R4_ERROR_ANALYSIS.md (+ stdout).
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


def norm(s) -> str:
    return str(s).strip(_P) if s is not None else ""


def main() -> None:
    gold = {json.loads(l)["uid"]: json.loads(l)
            for l in open(os.path.join(BASE, "data", "cltt_gold_pairs.jsonl"),
                          encoding="utf-8")}
    units = {json.loads(l)["uid"]: json.loads(l)["text"].split()
             for l in open(os.path.join(BASE, "data", "eval_units.jsonl"), encoding="utf-8")}

    # qwen r4 traces per run
    runs: dict[int, dict[str, dict]] = defaultdict(dict)
    for l in open(os.path.join(BASE, "results", "runs", "qwen-72b.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        if r["formulation"] == "r4":
            runs[r["run_index"]][r["uid"]] = parse_completion(r.get("completion_text"))

    def model_pairs(parsed, n_words):
        out = []
        for q in (parsed["pairs"] or []):
            if not isinstance(q, dict):
                continue
            si, pi, d = q.get("podmet_index"), q.get("prisudek_index"), q.get("vzdalenost")
            if not (isinstance(si, int) and isinstance(pi, int)):
                continue
            out.append({"s": norm(q.get("podmet")), "p": norm(q.get("prisudek")),
                        "si": si, "pi": pi,
                        "d": d if isinstance(d, int) else abs(si - pi) - 1})
        return out

    def gkey(gp):
        return (norm(gp.get("subj_word_form") or gp["subj_form"]), norm(gp["pred_word_form"]))

    L, w = [], None
    L.append("# qwen-72b × R4 — error anatomy (from stored traces)")
    L.append("")

    # ---------- per-run verdict causes + miss/spurious breakdowns (run 1 detail)
    fn_causes, fp_causes = Counter(), Counter()
    miss_by, all_by = Counter(), Counter()
    spur = Counter()
    for run in (1, 2, 3):
        for uid, g in gold.items():
            parsed = runs[run].get(uid)
            if parsed is None:
                continue
            mp = model_pairs(parsed, len(units[uid]))
            mset = [(m["s"], m["p"]) for m in mp]
            avail = list(mset)
            matches = []
            for gp in g["pairs"]:
                k = gkey(gp)
                if k in avail:
                    avail.remove(k)
                    matches.append((gp, next(m for m in mp if (m["s"], m["p"]) == k)))
                else:
                    matches.append((gp, None))
            mv = parsed["has_violation"] if parsed["has_violation"] is not None else False
            gv = g["verdict"]
            if run == 1:
                npair = str(min(len(g["pairs"]), 3)) + ("+" if len(g["pairs"]) >= 3 else "")
                for gp, m in matches:
                    dims = [f"pairs/sent={npair}",
                            f"rel={gp['subj_is_rel']}",
                            f"db={'0-1' if gp['distance']<=1 else '2-4' if gp['distance']<=4 else '5-9' if gp['distance']<=9 else '10+'}"]
                    for dim in dims:
                        all_by[dim] += 1
                        if m is None:
                            miss_by[dim] += 1
                # spurious categorization
                gsubj = {gkey(gp)[0] for gp in g["pairs"]}
                gpred = {gkey(gp)[1] for gp in g["pairs"]}
                used_keys = Counter((m["s"], m["p"]) for _gp, m in matches if m)
                seen_pi = Counter()
                for m in mp:
                    k = (m["s"], m["p"])
                    if used_keys.get(k, 0) > 0:
                        used_keys[k] -= 1
                        seen_pi[m["pi"]] += 1
                        continue
                    if seen_pi.get(m["pi"], 0) or any(x is not m and x["pi"] == m["pi"] for x in mp):
                        spur["duplicate_same_predicate"] += 1
                    elif m["p"] in gpred:
                        spur["gold_predicate_wrong_subject"] += 1
                    else:
                        spur["predicate_not_measured_in_gold"] += 1
                    seen_pi[m["pi"]] += 1
            if gv and not mv:
                viol = [(gp, m) for gp, m in matches if gp["distance"] > T_LIMIT]
                if viol and all(m is None for _gp, m in viol):
                    fn_causes["violating_pair_missed"] += 1
                elif viol:
                    fn_causes["violating_pair_found_but_underestimated_or_unflagged"] += 1
                else:
                    fn_causes["no_violating_gold_pair_matchable"] += 1
            if mv and not gv:
                over = [m for m in mp if m["d"] > T_LIMIT]
                matched_ids = {id(m) for _gp, m in matches if m}
                if any(id(m) not in matched_ids for m in over):
                    fp_causes["spurious_pair_over_threshold"] += 1
                elif over:
                    fp_causes["matched_pair_distance_overestimated"] += 1
                else:
                    fp_causes["flag_without_over_threshold_pair"] += 1

    L.append("## Verdict error causes (3 runs pooled)")
    L.append("")
    L.append(f"- False negatives ({sum(fn_causes.values())}): {dict(fn_causes)}")
    L.append(f"- False positives ({sum(fp_causes.values())}): {dict(fp_causes)}")
    L.append("")
    L.append("## Naming misses (run 1)")
    L.append("")
    for pref in ("pairs/sent", "rel", "db"):
        row = ", ".join(f"{k.split('=')[1]}: {100*miss_by[k]/all_by[k]:.0f}% ({miss_by[k]}/{all_by[k]})"
                        for k in sorted(all_by) if k.startswith(pref))
        L.append(f"- by {pref}: {row}")
    L.append("")
    L.append(f"## Spurious pairs (run 1): {sum(spur.values())} — {dict(spur.most_common())}")
    L.append("")

    # ---------- cross-run pair stability + voting simulation
    stab_matched, stab_spur = Counter(), Counter()
    cmv = Counter()
    pair_hits = pair_gold = pair_pred = 0
    for uid, g in gold.items():
        per_run = []
        for run in (1, 2, 3):
            parsed = runs[run].get(uid)
            per_run.append(model_pairs(parsed, len(units[uid])) if parsed else [])
        counts = Counter()
        dists = defaultdict(list)
        for mp in per_run:
            seen = set()
            for m in mp:
                k = (m["s"], m["p"])
                if k in seen:
                    continue
                seen.add(k)
                counts[k] += 1
                dists[k].append(m["d"])
        gks = Counter(gkey(gp) for gp in g["pairs"])
        for k, c in counts.items():
            (stab_matched if gks.get(k) else stab_spur)[c] += 1
        # voting: keep pairs in >=2 runs, median distance
        voted = {k: sorted(ds)[len(ds) // 2] for k, ds in dists.items() if counts[k] >= 2}
        vv = any(d > T_LIMIT for d in voted.values())
        cmv[(g["verdict"], vv)] += 1
        pair_pred += len(voted)
        avail = Counter(gks)
        for k in voted:
            if avail.get(k):
                avail[k] -= 1
                pair_hits += 1
        pair_gold += len(g["pairs"])

    def dist_pct(c):
        t = sum(c.values())
        return {k: f"{100*v/t:.0f}%" for k, v in sorted(c.items())}

    tp, fp = cmv[(True, True)], cmv[(False, True)]
    fn, tn = cmv[(True, False)], cmv[(False, False)]
    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    f1v = 2 * prec * rec / (prec + rec) if prec + rec else 0
    pp = pair_hits / pair_pred if pair_pred else 0
    pr = pair_hits / pair_gold if pair_gold else 0
    pf = 2 * pp * pr / (pp + pr) if pp + pr else 0

    L.append("## Cross-run pair stability (appearances across the 3 passes)")
    L.append("")
    L.append(f"- pairs that MATCH gold: {dist_pct(stab_matched)} (n={sum(stab_matched.values())})")
    L.append(f"- SPURIOUS pairs: {dist_pct(stab_spur)} (n={sum(stab_spur.values())})")
    L.append("")
    L.append("## Simulated majority-vote arm (pairs in ≥2/3 runs, median distance)")
    L.append("")
    L.append(f"- verdict: acc {100*(tp+tn)/sum(cmv.values()):.1f}%, P {100*prec:.1f}%, "
             f"R {100*rec:.1f}%, **F1 {100*f1v:.1f}** (TP {tp} FP {fp} FN {fn} TN {tn})")
    L.append(f"- pairs: precision {100*pp:.1f}%, recall {100*pr:.1f}%, **F1 {100*pf:.1f}**")
    L.append("")

    out = os.path.join(BASE, "docs", "QWEN_R4_ERROR_ANALYSIS.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
