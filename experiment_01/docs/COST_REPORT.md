# Cost & token-budget report — full LLM run

Generated 2026-07-01 by `src/estimate_cost.py` from the **actual** eval set
(`data/processed/eval_set.jsonl`, N=640), the **measured** prompt overhead
(`src/prompts/`), the real sentence texts, and the real CoNLL-U blocks fed by
regime 3 / emitted by regime 2. Machine-readable copy: `results/cost_estimate.json`.

## TL;DR

- **Full run ≈ $20** (central estimate, all 4 models, 3 runs). **Cost is not a blocker.**
- **~94% of the cost is the single frontier model** (~$18.7). The three open-weight models together
  cost **~$1.2**.
- Total token volume across all 4 models ≈ **23M tokens** (~90% input, driven by regime-3 CoNLL-U).

## Design being priced

`640 sentences × 3 regimes × 4 model_ids × 3 runs = 23,040 generations.`

Per **one** model (each model runs the identical load), central `cpt=3.5`:

| | Input tokens | Output tokens | Total |
|---|--:|--:|--:|
| Per model (×3 runs) | 5,183,790 | 576,582 | 5,760,372 |

Output is small because two of three regimes emit only a short JSON answer; regime 2 additionally
emits a CoNLL-U parse (estimated at ~22 chars/token line). Input dominates because regime 3 feeds the
full real CoNLL-U block.

Prompt fixed overhead (system + 2 few-shot examples), measured: raw_text **1,340 ch**,
raw_to_conllu **1,817 ch**, conllu_input **2,182 ch**.

## Per-model cost (central, illustrative prices)

Prices are **illustrative OpenRouter placeholders, USD per 1M tokens — verify per chosen slug**
(and pin provider + quantization per METHODOLOGY §5, which can shift price).

| Model (role) | $/M in | $/M out | Run cost |
|---|--:|--:|--:|
| small-1 (~8B open) | 0.02 | 0.03 | $0.12 |
| small-2 (~7–12B open) | 0.05 | 0.10 | $0.32 |
| large-1 (~70B open) | 0.12 | 0.30 | $0.80 |
| large-2 (frontier) | 2.50 | 10.00 | $18.73 |
| **Total** | | | **≈ $19.96** |

## Sensitivity

**chars→token ratio** (Czech + CoNLL-U is subword-heavy; central 3.5). Total tokens across all 4
models:

| Ratio | Input | Output | Total |
|---|--:|--:|--:|
| 3.0 (pessimistic) | 24.2M | 2.69M | 26.9M |
| 3.5 (central) | 20.7M | 2.31M | 23.0M |
| 4.0 (optimistic) | 18.1M | 2.02M | 20.2M |

Cost scales ~linearly, so the ±15% token swing moves the total roughly $17–$23.

**Other levers (all linear):**
- **N**: doubling to N≈1,280 → ~$40. Even N=5,000 stays well under $200.
- **Frontier model choice**: swapping large-2 for a pricier tier (e.g. $5/$15 per M) → run ≈ $32
  total; a $15/$60 "premium reasoning" tier → run ≈ $95 total. Still not a blocker.
- **Runs**: dropping the frontier model from 3→2 runs (METHODOLOGY §5 asymmetric option) cuts ~1/3
  of its cost (~$6). Not worth the loss to the consistency metric at these prices.
- **Regime 2 output** is the only estimated (not measured) quantity; even doubling it changes total
  cost by <5% (output is a small share and cheap on open models).

## Takeaways for the harness

1. Budget is trivial — optimize for **scientific quality, not cost**. No need to trim N, runs, or
   models for money reasons; the §5 cost-mitigation options are effectively moot at this scale.
2. The **frontier model is the only line item that matters** — worth choosing it deliberately and
   pinning it (provider + quantization) so the ~$19 buys a reproducible artifact.
3. Rate limits / latency (not $) are the real operational constraint for 23k calls — design
   `run_llm.py` for retries, caching of completed (sentence×regime×model×run) cells, and resumability.
