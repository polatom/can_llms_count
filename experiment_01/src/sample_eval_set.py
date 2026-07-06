"""Draw the stratified evaluation set from the KUK gold pairs.

Stratifies by (sentence-length bucket × word-distance bucket) and allocates an
EQUAL target per non-empty stratum — which deliberately oversamples the long /
far-distance tail relative to its population share, because that tail is where
H4 (accuracy degrades with length/distance) is tested and where the bulk of the
415k pairs are *not* (median distance is 1). See docs/METHODOLOGY.md §4.

Sub-corpus and `ClarityPursuit` are covariates, NOT a stratification axis
(§4/§9) — so the default draw is pooled/random within each stratum; the
resulting sub-corpus breakdown is reported so its skew is visible. Embedding
depth (`intervening_clauses`, `tree_depth`) is carried through as a covariate.

Usage:
    python src/sample_eval_set.py \
        --pairs   experiment_01/data/processed/kuk_pairs.jsonl \
        --out-dir experiment_01/data/processed \
        --per-stratum 40 --seed 20260701

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
from collections import Counter, defaultdict

# Bucket edges. Length in whitespace-words; distance = |p-q|-1 in words.
LENGTH_BUCKETS = [(5, 14), (15, 24), (25, 39), (40, 80)]
DISTANCE_BUCKETS = [(0, 1), (2, 4), (5, 9), (10, 10_000)]


def bucket_label(value: int, buckets: list[tuple[int, int]]) -> str | None:
    for lo, hi in buckets:
        if lo <= value <= hi:
            top = "+" if hi >= 10_000 else str(hi)
            return f"{lo}-{top}"
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--per-stratum", type=int, default=40, help="Target sentences per stratum")
    ap.add_argument("--seed", type=int, default=20260701)
    ap.add_argument(
        "--balance-subcorpus",
        action="store_true",
        help="Spread each stratum's draw as evenly as possible across sub-corpora "
        "(default: pooled random, per METHODOLOGY §4)",
    )
    args = ap.parse_args()
    rng = random.Random(args.seed)

    recs = [json.loads(l) for l in open(args.pairs, encoding="utf-8")]

    strata: dict[tuple[str, str], list] = defaultdict(list)
    skipped = 0
    for r in recs:
        lb = bucket_label(r["n_words"], LENGTH_BUCKETS)
        db = bucket_label(r["distance"], DISTANCE_BUCKETS)
        if lb is None or db is None:
            skipped += 1
            continue
        strata[(lb, db)] = strata[(lb, db)]  # touch
        strata[(lb, db)].append(r)

    def draw(items: list, k: int) -> list:
        if len(items) <= k:
            return list(items)
        if not args.balance_subcorpus:
            return rng.sample(items, k)
        # even spread across sub-corpora present in this stratum
        by_sc: dict[str, list] = defaultdict(list)
        for it in items:
            by_sc[it["subcorpus"]].append(it)
        for v in by_sc.values():
            rng.shuffle(v)
        chosen: list = []
        scs = sorted(by_sc)
        i = 0
        while len(chosen) < k and any(by_sc[sc] for sc in scs):
            sc = scs[i % len(scs)]
            if by_sc[sc]:
                chosen.append(by_sc[sc].pop())
            i += 1
        return chosen

    sample: list = []
    stratum_rows = []
    # deterministic ordering of strata for the report
    ordered = sorted(strata.keys(), key=lambda k: (k[0], k[1]))
    for key in ordered:
        items = strata[key]
        chosen = draw(items, args.per_stratum)
        for c in chosen:
            c2 = dict(c)
            c2["length_bucket"], c2["distance_bucket"] = key
            sample.append(c2)
        stratum_rows.append((key, len(items), len(chosen)))

    rng.shuffle(sample)

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, "eval_set.jsonl")
    with open(out_path, "w", encoding="utf-8") as fh:
        for r in sample:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    dists = [r["distance"] for r in sample]
    lens = [r["n_words"] for r in sample]
    summary = {
        "seed": args.seed,
        "per_stratum": args.per_stratum,
        "balance_subcorpus": args.balance_subcorpus,
        "n_sample": len(sample),
        "n_population": len(recs),
        "skipped_unbucketed": skipped,
        "n_strata_nonempty": len(ordered),
        "sample_distance": {
            "min": min(dists), "median": statistics.median(dists),
            "mean": round(statistics.mean(dists), 2), "max": max(dists),
        },
        "sample_length": {
            "min": min(lens), "median": statistics.median(lens),
            "mean": round(statistics.mean(lens), 2), "max": max(lens),
        },
        "by_subcorpus": dict(Counter(r["subcorpus"] for r in sample).most_common()),
        "copular_frac": round(sum(r["is_copula"] for r in sample) / len(sample), 3),
        "strata": [
            {"length": k[0], "distance": k[1], "available": avail, "sampled": took}
            for k, avail, took in stratum_rows
        ],
    }
    summary_path = os.path.join(args.out_dir, "eval_set_summary.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    # ---- console report ----
    print(f"Population: {len(recs):,}  |  seed={args.seed}  per-stratum={args.per_stratum}  "
          f"balance_subcorpus={args.balance_subcorpus}")
    print(f"\nStrata (length × distance)  available / sampled:")
    dist_cols = [f"{lo}-{'+' if hi>=10_000 else hi}" for lo, hi in DISTANCE_BUCKETS]
    header = "  length \\ dist  " + "".join(f"{c:>14s}" for c in dist_cols)
    print(header)
    for lo, hi in LENGTH_BUCKETS:
        lb = f"{lo}-{hi}"
        cells = []
        for dlo, dhi in DISTANCE_BUCKETS:
            db = f"{dlo}-{'+' if dhi>=10_000 else dhi}"
            avail = len(strata.get((lb, db), []))
            took = next((t for k, a, t in stratum_rows if k == (lb, db)), 0)
            cells.append(f"{took:>4}/{avail:<8}" if avail else f"{'—':>13}")
        print(f"  {lb:>12s}  " + "".join(f"{c:>14s}" for c in cells))
    print(f"\nSAMPLE N = {len(sample):,}")
    print(f"  distance: median {summary['sample_distance']['median']}  "
          f"mean {summary['sample_distance']['mean']}  max {summary['sample_distance']['max']}")
    print(f"  length:   median {summary['sample_length']['median']}  "
          f"mean {summary['sample_length']['mean']}  max {summary['sample_length']['max']}")
    print(f"  by sub-corpus: {summary['by_subcorpus']}")
    print(f"  copular: {summary['copular_frac']*100:.1f}%")
    print(f"\nWrote {out_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
