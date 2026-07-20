# Parser arm — error analysis (Q1–Q3, 2026-07-20)

## Q1 — end-to-end distance performance (per GOLD pair, form matching)

| status | pairs | share |
|---|--:|--:|
| found, distance exact | 1460 | 92.1% |
| found, distance wrong | 3 | 0.2% |
| missed entirely | 123 | 7.8% |

Distance-wrong error sizes |Δd| (5 = 5+): {5: 3}

## Q2 — where the errors come from

**Miss rate by unit segmentation:** whole units 1.7% (9/518), split units 10.7% (114/1068)

**Miss rate by gold distance:** 0-1: 3.2% (32/994), 2-4: 12.1% (36/298), 5-9: 23.0% (41/178), 10+: 12.1% (14/116)

**Miss rate by construction:** finite-verb: 9.5% (109/1147), copular: 3.7% (13/350), passive/analytic-aux: 1.5% (1/68), conditional: 0.0% (0/9), aby/kdyby: 0.0% (0/9), copular-past: 0.0% (0/3)

**Missed pairs, rel-pron vs other subjects:** {'nonrel': 115, 'rel': 8}

**Verdict FN causes (26 sentences):** {'all_violating_pairs_missed': 24, 'violating_pair_found_but_underestimated': 2}; by segmentation: {'whole': 2, 'split': 24}
**Verdict FP causes (6 sentences):** {'spurious_pair_over_threshold': 6}

## Q3 — sensitivity to Katka's pending answers

- **K8 (exclude relative-pronoun-subject pairs from both sides):** verdict acc 97.1%, P 96.4%, R 86.2%, F1 91.0% (TP 162 FP 6 FN 26 TN 927)
  vs. current acc 97.1%, P 96.6%, R 86.6%, F1 91.3% (TP 168 FP 6 FN 26 TN 921)
- **K7 (verbless clauses) prevalence in CLTT:** 46 excluded subject edges (vs. 1,586 pairs) — negligible either way.
- **K6 (per-conjunct pairs):** would apply the same rule change to gold and parser arm
  symmetrically (shared extraction code); it can add violating pairs on both sides but
  cannot fix parse/segmentation errors — direction: roughly neutral, recomputable.
