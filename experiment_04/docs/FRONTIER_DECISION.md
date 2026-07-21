# Frontier run — decision memo (2026-07-21, for Tomáš)

Open-model grid is complete (20,178 calls incl. R3, **$10.30 total**). This memo lays out the
frontier options with real numbers. Decision needed: which option to run.

## Where the open models landed (3-pass means, vs. parser baseline 97.1 verdict F1)

| config | verdict F1 | verdict P / R | pair F1 | naming recall | dist-correct given found |
|---|--:|--:|--:|--:|--:|
| gemma-27b × R1 | 60.6 | 62/60* | 30.9 | 29.1% | 32% |
| gemma-27b × R2 | 73.8 | 62/87 | 34.3 | 33.5% | 93% |
| gemma-27b × R3 | 63.6 | 50/87 | 55.9 | 63.9% | 94% |
| qwen-72b × R1 | 58.5 | 60/57* | 28.9 | 26.4% | 30% |
| qwen-72b × R2 | 72.5 | 63/87 | 49.3 | 49.8% | 97% |
| **qwen-72b × R3** | **74.4** | 63/91 | **62.0** | **70.8%** | 96% |
(*R1 P/R approximate — see RESULTS_openmodels.md for per-run detail.)

**What the experiment has already established:**
1. **Counting: solved by prompt** (R2/R3 scaffold): ~30% → 93–97% distance-correct given found.
2. **Identification recall: mostly solved by prompt** (R3 inventory): 26% → 71% naming recall
   on the 72B; +40 pts from prompt engineering alone.
3. **The residual gap to the parser is pairing precision + the last ~30% of naming recall**:
   spurious pairs (pair precision ~62% at best) create false flags under the any-pair-over-T
   rule → verdict precision stuck at ~63%, verdict F1 ceiling ~74 on open models.
4. Capability matters exactly where predicted: the 72B converts inventory recall into far
   better pairing precision than the 27B (R3 pair F1 62 vs. 56; verdict +11 pts).
5. Stability: verdict flip rate 7.5–11% across passes (R3 is the most stable formulation).

**The frontier question is now precise:** does frontier capability (± reasoning) fix pairing
precision and residual naming recall — the two things prompts didn't fix?

## Options

- **A. Full frontier grid** — gpt-5.1, reasoning on+off, R2+R3, 3 passes × 1,121
  (13.5k calls; R1 as a single-pass extra for the figure's naive point, +2.2k):
  **~$220–280** (reasoning tokens dominate). Gives: the complete second capability rung for
  the figure, the scaffold×reasoning interaction (does thinking make R3's inventory
  redundant?), full-set McNemar vs. the parser at ~3–4 pt resolution, and the full error
  inventory for exp_03.
- **B. Reasoning-on only, R2+R3, 3 passes** (6.7k calls): **~$110–150.** Loses the
  reasoning-off point (the "is it the thinking or the scale" contrast) but keeps parity
  testing and the interaction.
- **C. Hard-cases-only** (Tomáš's suggestion): frontier on the ~46% of units with ≥2 silver
  pairs (or on model-vs-parser disagreement units — no gold peeking either way), extrapolating
  frontier ≈ open on the easy rest: **~$60–90.** Cheapest, but the headline parity claim
  becomes partially extrapolated — reviewers will notice; and per-phenomenon breakdowns get
  truncated on the easy half.

**Recommendation: A** (or B if budget-sensitive). Rationale: the parity question is the paper's
RQ1 and deserves the full-set measurement; $250 is within the §6 envelope; and C's savings are
small in absolute terms while costing claim strength. C remains attractive as a *pattern for
SPRINT deployment* (route easy sentences to cheap models) — worth a paragraph in the paper
either way, and directly testable post hoc from the full-grid data (which C itself cannot give).

## Also pending (not blocking)
- KUK-640 secondary run: wait until the frontier decision, then run with the final best-2
  configs (contamination/domain check; ~$5–20).
- Katka package ready to send: WORKED_EXAMPLES, VERIFICATION_SHEET, PROVISIONAL_ANSWERS_K6-K9,
  QUESTIONS doc.
- Run traces (59 MB): kept out of git for now; decision on archiving (compress + commit vs.
  external storage) with the final data release.
