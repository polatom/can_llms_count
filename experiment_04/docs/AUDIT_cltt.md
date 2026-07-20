# CLTT gold — descriptive statistics (experiment_04 §4.1, §4.3)

Derived by `src/derive_cltt_gold.py` (§3 rule on `cs_cltt` human trees). Regenerate after
any rule change; verification status tracked in §4.1 of METHODOLOGY.md.

| quantity | count | share |
|---|--:|--:|
| sentences (whole treebank, unfiltered) | 1121 | |
| gold pairs | 1586 | 1.41/sentence |
| **verdict positives (any d > 6)** | **194** | **17.3%** |
| near-threshold sentences (d ∈ [4, 9]) | 233 | 20.8% |
| zero-pair sentences | 294 | 26.2% |
| fragments (no finite clause) | 263 | 23.5% |
| sentences with ≥1 pro-drop clause | 259 | 23.1% |
| relative-pronoun-subject pairs (K8) | 277 | 17.5% of pairs |

Pair distance buckets (d): 0-1: 994, 2-4: 298, 5-9: 178, 10+: 116

Construction types (§3 classification): finite verb / l-participle: 1147, copular — finite copula (je): 350, passive — finite aux (je/bude vydána): 33, passive — past aux (byla vydána): 31, conditional (by): 9, aby/kdyby (absorbed by): 9, analytic — aux (jsem/bude …): 4, copular — past copula (byla): 3

## Metric family (§4.3) — mean / median / p90 per sentence

| metric | mean | median | p90 |
|---|--:|--:|--:|
| sentence length (words) | 28.5 | 22 | 58 |
| dependency tree depth | 6.2 | 6 | 10 |
| subordinate clauses | 0.9 | 0 | 3 |
| coordinations (conj) | 2.3 | 1 | 5 |
| passive markers | 0.4 | 0 | 1 |
| max subject–predicate distance | 4.7 | 2 | 12 |
