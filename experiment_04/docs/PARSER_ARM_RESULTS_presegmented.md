# Parser arm (PRESEGMENTED) — results vs. CLTT gold (PRELIMINARY: pending K6–K9 sign-off)

UDPipe 2 `czech-pdt-ud-2.15-241121` (LINDAT API, tokenizer=presegmented — unit forced to one sentence) on the raw text of all 1121 gold sentence
units; §3 extraction with sub-sentence union and word-offset mapping (§5.1).
Gold may shift when Katka's K6–K9 answers land; rescoring is deterministic and cheap.

## Verdict (violation ⇔ any pair d > 6) — the deployment metric

| metric | value |
|---|--:|
| accuracy | **99.0%** |
| precision | 97.9% |
| recall | 96.4% |
| F1 | 97.1% |
| confusion (gold→pred) | TP 187 · FP 4 · FN 7 · TN 923 |

## Pair extraction

- gold pairs 1586, predicted 1576
- form-matched: 1512 → precision 95.9%, recall 95.3%, F1 95.6%
- index-exact matched: 1510 (95.2% of gold)
- distance on form-matched pairs: exact 99.8%, ±1 99.8%, MAE 0.06

## Segmentation (the known upstream error)

- units kept as one sentence by UDPipe: 1121 (100.0%)
- split into 2: 0 (0.0%); into 3+: 0 (0.0%)
- word-count mismatches after union mapping: 0
