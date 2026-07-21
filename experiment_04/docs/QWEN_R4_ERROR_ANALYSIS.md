# qwen-72b × R4 — error anatomy (from stored traces)

## Verdict error causes (3 runs pooled)

- False negatives (38): {'violating_pair_missed': 34, 'violating_pair_found_but_underestimated_or_unflagged': 4}
- False positives (296): {'spurious_pair_over_threshold': 284, 'flag_without_over_threshold_pair': 9, 'matched_pair_distance_overestimated': 3}

## Naming misses (run 1)

- by pairs/sent: 1: 12% (52/418), 2: 20% (93/460), 3+: 34% (250/739)
- by rel: False: 23% (308/1340), True: 31% (87/277)
- by db: 0-1: 26% (263/1019), 10+: 19% (22/116), 2-4: 25% (75/305), 5-9: 20% (35/177)

## Spurious pairs (run 1): 802 — {'predicate_not_measured_in_gold': 463, 'gold_predicate_wrong_subject': 301, 'duplicate_same_predicate': 38}

## Cross-run pair stability (appearances across the 3 passes)

- pairs that MATCH gold: {1: '10%', 2: '11%', 3: '79%'} (n=1335)
- SPURIOUS pairs: {1: '47%', 2: '23%', 3: '30%'} (n=1196)

## Simulated majority-vote arm (pairs in ≥2/3 runs, median distance)

- verdict: acc 91.2%, P 68.1%, R 92.3%, **F1 78.3** (TP 179 FP 84 FN 15 TN 843)
- pairs: precision 65.6%, recall 74.5%, **F1 69.8**
