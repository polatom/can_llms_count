# Parser arm — results vs. CLTT gold (PRELIMINARY: pending K6–K9 sign-off)

UDPipe 2 `czech-pdt-ud-2.15-241121` (LINDAT API) on the raw text of all 1121 gold sentence
units; §3 extraction with sub-sentence union and word-offset mapping (§5.1).
Gold may shift when Katka's K6–K9 answers land; rescoring is deterministic and cheap.

## Verdict (violation ⇔ any pair d > 6) — the deployment metric

| metric | value |
|---|--:|
| accuracy | **97.1%** |
| precision | 96.6% |
| recall | 86.6% |
| F1 | 91.3% |
| confusion (gold→pred) | TP 168 · FP 6 · FN 26 · TN 921 |

## Pair extraction

- gold pairs 1586, predicted 1600
- form-matched: 1463 → precision 91.4%, recall 92.2%, F1 91.8%
- index-exact matched: 1461 (92.1% of gold)
- distance on form-matched pairs: exact 99.8%, ±1 99.8%, MAE 0.09

## Segmentation (the known upstream error)

- units kept as one sentence by UDPipe: 603 (53.8%)
- split into 2: 465 (41.5%); into 3+: 53 (4.7%)
- word-count mismatches after union mapping: 0
