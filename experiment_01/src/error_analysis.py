"""Error taxonomy + instability deep-dive over results/scored.jsonl.

Three analyses:
  A. Failure taxonomy per (model × regime): malformed / correct / off-by-one /
     moderate (2-3) / large (>=4), over- vs under-count, and role errors.
  B. PURE COUNTING failure: distance accuracy *restricted to* cases where the
     model got BOTH subject and predicate right — isolates counting from parsing.
  C. Instability: within-triplet spread magnitude, agreement pattern, whether
     majority-vote-of-3 rescues accuracy, and where instability concentrates
     (by distance bucket, and vs. correctness).

Writes results/error_analysis.json + console report. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict


def category(r: dict) -> str:
    if not r["format_ok"]:
        return "malformed"
    if r.get("exact"):
        return "correct"
    ae = r.get("abs_err")
    if ae == 1:
        return "off_by_one"
    if ae is not None and ae <= 3:
        return "moderate_2_3"
    return "large_4plus"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scored", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.scored, encoding="utf-8")]

    # ---------- A. taxonomy per (model, regime) ----------
    tax = defaultdict(Counter)
    direction = defaultdict(Counter)
    for r in rows:
        key = (r["model_id"], r["regime"])
        tax[key][category(r)] += 1
        if r["format_ok"] and not r.get("exact"):
            direction[key]["overcount" if r["signed_err"] > 0 else "undercount"] += 1

    # ---------- B. pure counting failure (roles correct) ----------
    pure = {}
    for key in tax:
        m, reg = key
        sub = [r for r in rows if r["model_id"] == m and r["regime"] == reg
               and r["format_ok"] and r["both_roles"]]
        if sub:
            exact = sum(1 for r in sub if r["exact"])
            pure[key] = {"n_both_roles_ok": len(sub),
                         "exact_given_roles": round(exact / len(sub), 4),
                         "miscount_given_roles": round(1 - exact / len(sub), 4)}

    # ---------- C. instability ----------
    trip = defaultdict(list)  # (uid,model,regime) -> [dist_pred over runs] (format_ok only)
    trip_exact = defaultdict(list)
    for r in rows:
        if r["format_ok"]:
            k = (r["uid"], r["model_id"], r["regime"])
            trip[k].append(r["dist_pred"])
            trip_exact[k].append(bool(r.get("exact")))

    instab = {}
    for (m, reg) in tax:
        ks = [k for k in trip if k[1] == m and k[2] == reg and len(trip[k]) >= 2]
        spreads = [max(v) - min(v) for k, v in ((k, trip[k]) for k in ks)]
        allsame = sum(1 for s in spreads if s == 0)
        # majority-vote accuracy vs mean single-run accuracy
        maj_correct = single_correct = single_total = 0
        for k in ks:
            v = trip[k]
            mode = Counter(v).most_common(1)[0][0]
            # majority answer exact? need gold; recover from any run's exactness mapping:
            # exact iff mode == gold; but we only stored exactness per run. Use: a run is
            # exact iff its pred == gold, so gold = pred of an exact run if any, else infer.
            gold = None
            for pred, ex in zip(v, trip_exact[k]):
                if ex:
                    gold = pred
                    break
            if gold is None:
                gold = "__nogold__"  # no run was exact → majority can't be exact either
            maj_correct += 1 if mode == gold else 0
            single_correct += sum(trip_exact[k])
            single_total += len(v)
        instab[(m, reg)] = {
            "n_triplets": len(ks),
            "pct_all_agree": round(100 * allsame / len(ks), 1) if ks else None,
            "mean_spread": round(statistics.mean(spreads), 2) if spreads else None,
            "median_spread": statistics.median(spreads) if spreads else None,
            "p90_spread": sorted(spreads)[int(len(spreads) * 0.9)] if spreads else None,
            "max_spread": max(spreads) if spreads else None,
            "single_run_exact_pct": round(100 * single_correct / single_total, 1) if single_total else None,
            "majority_vote_exact_pct": round(100 * maj_correct / len(ks), 1) if ks else None,
        }

    # instability vs distance bucket (pooled over models), raw_text + conllu_input
    instab_by_bucket = defaultdict(lambda: [0, 0])  # (regime,bucket)->[varying,total]
    for k, v in trip.items():
        if len(v) < 2:
            continue
        reg = k[2]
        # bucket from any row of this triplet
        bucket = next((r["gold_distance_bucket"] for r in rows
                       if r["uid"] == k[0] and r["model_id"] == k[1] and r["regime"] == reg), None)
        instab_by_bucket[(reg, bucket)][1] += 1
        if len(set(v)) > 1:
            instab_by_bucket[(reg, bucket)][0] += 1

    result = {
        "taxonomy": {f"{m}|{reg}": dict(c) for (m, reg), c in tax.items()},
        "direction_of_error": {f"{m}|{reg}": dict(c) for (m, reg), c in direction.items()},
        "pure_counting_given_roles": {f"{m}|{reg}": v for (m, reg), v in pure.items()},
        "instability": {f"{m}|{reg}": v for (m, reg), v in instab.items()},
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    # ---------- console ----------
    print("=== B. PURE COUNTING FAILURE — distance accuracy WHEN both roles correct ===")
    print(f"{'model':10s} {'regime':14s} {'n(roles ok)':>12s} {'exact|roles':>12s} {'miscount|roles':>15s}")
    for (m, reg), v in sorted(pure.items()):
        print(f"{m:10s} {reg:14s} {v['n_both_roles_ok']:>12d} "
              f"{v['exact_given_roles']*100:>11.1f}% {v['miscount_given_roles']*100:>14.1f}%")

    print("\n=== C. INSTABILITY (temp 0, pinned provider) ===")
    print(f"{'model':10s} {'regime':14s} {'agree%':>7s} {'meanSpread':>11s} {'p90':>4s} {'max':>4s} "
          f"{'1run%':>6s} {'maj%':>6s}")
    for (m, reg), v in sorted(instab.items()):
        print(f"{m:10s} {reg:14s} {v['pct_all_agree']:>7} {v['mean_spread']:>11} "
              f"{v['p90_spread']:>4} {v['max_spread']:>4} "
              f"{v['single_run_exact_pct']:>6} {v['majority_vote_exact_pct']:>6}")

    print("\n=== C2. % of triplets that VARY, by gold distance bucket (pooled models) ===")
    buckets = ["0-1", "2-4", "5-9", "10-+"]
    print(f"{'regime':16s}" + "".join(f"{b:>10s}" for b in buckets))
    for reg in ["raw_text", "raw_to_conllu", "conllu_input"]:
        cells = []
        for b in buckets:
            var, tot = instab_by_bucket[(reg, b)]
            cells.append(f"{100*var/tot:.0f}%" if tot else "-")
        print(f"{reg:16s}" + "".join(f"{c:>10s}" for c in cells))

    print("\n=== A. TAXONOMY (share of generations) ===")
    cats = ["correct", "off_by_one", "moderate_2_3", "large_4plus", "malformed"]
    print(f"{'model':10s} {'regime':14s}" + "".join(f"{c:>13s}" for c in cats))
    for (m, reg), c in sorted(tax.items()):
        tot = sum(c.values())
        print(f"{m:10s} {reg:14s}" + "".join(f"{100*c[k]/tot:>12.1f}%" for k in cats))

    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
