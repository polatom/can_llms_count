# Gold verification — results (Katka, 2026-07-21)

Sheet: 105 derived pairs (all 25 rare-construction + 80 random; VERIFICATION_SHEET_katka.md).
Response: VERIFICATION_SHEET_katka_response_2026-07-21.md.

| outcome | items | notes |
|---|--:|---|
| confirmed ✓ | **92** | all rare constructions incl. aby/kdyby, conditionals, past copulas |
| wrong | 1 | item 35 — quantified subject (*dvanáct měsíců*): UD heads the genitive noun, definition wants the nominative quantifier. **Rule fixed (K12, provisional), gold re-derived**; the class is a singleton (1/1,586 pairs, measured). |
| genuinely ambiguous | 1 | item 94 (*…, které tvoří mimořádný výsledek…*) — morphological nom/acc ambiguity; gold keeps the treebank reading, flagged in reporting. |
| not verifiable from the sheet | 11 | windowed display cut needed context (our display fault, not gold's) — re-sent with full sentences: VERIFICATION_FOLLOWUP_katka_2026-07-21.md (+ item 35 restated for K12 confirmation). |

**Measured error rate of the derived gold (preliminary, pending the 11 follow-ups):**
1 error / 94 verifiable = **1.1%** (plus 1 ambiguous = worst case 2.1%). For the paper: the
CLTT-derived gold is validated at ~99% pair-level accuracy by the treebank's own co-author,
with the single found error traced to a definition/annotation-convention divergence and fixed
mechanically.

Effect of the K12 fix on results: 1 pair changes (d 5 → 4, both below threshold) — verdicts,
parser-arm metrics (F1 97.1), and LLM scores unchanged at reported precision.
