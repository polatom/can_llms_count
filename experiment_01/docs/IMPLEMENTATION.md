# Implementation — actual build log & details

**Living document.** Records what has actually been built, run, and verified — as opposed to
`IMPLEMENTATION_PLAN.md` (the frozen original plan) and `METHODOLOGY.md` (the science spec, v3).
Where this file and `IMPLEMENTATION_PLAN.md` disagree on execution specifics, **this file wins**;
for the experimental design, `METHODOLOGY.md` v3 is authoritative.

Last updated: 2026-07-01.

---

## 0. Status at a glance

| Piece | State |
|---|---|
| Data downloaded + fully extracted + checksummed | ✅ done |
| `cs_cltt` QC gold verified & placed | ✅ done |
| `src/conllu_utils.py` (CoNLL-U reader, MWT→word mapping) | ✅ done |
| `src/extract_pairs.py` (gold subject/predicate/word-distance) | ✅ done, run over full KUK |
| Predicate operationalization sign-off (linguist) | ⏳ provisional (see `OPEN_QUESTION_predicate_definition.md`) |
| `src/sample_eval_set.py` (stratified sampling) | ✅ done, eval set drawn (N=640, balanced) |
| Prompt templates (3 regimes, Czech) | ✅ done (`src/prompts/`) |
| Cost estimate | ✅ done (`docs/COST_REPORT.md`, ≈$20 full run) |
| `run_llm.py` (harness) | ✅ built; **live smoke test passed** (llama-8b, 9 calls) — cost/provider/tokens/parse all captured |
| Model selection (4 slugs) | ✅ family-matched all-open: Llama 8B/70B + Qwen 7B/72B. **Provider+quant pinned & verified** (DeepInfra·fp8 ×3, Together·fp8 for qwen-7b); all fp8 → quantization held constant across the size comparison. |
| Full run (23,040 calls) | ✅ **complete** — 23,040 generations, 0 outstanding failures, real cost $7.73 (`results/runs/`) |
| `score.py` + scoring | ✅ built + run; metrics in `results/metrics_by_condition.csv`, per-record `results/scored.jsonl`, writeup `docs/RESULTS.md` |
| `error_analysis.py` | ✅ built + run — taxonomy, pure-counting decomposition, instability/majority-vote (`results/error_analysis.json`, writeup in `docs/RESULTS.md`) |
| `cs_cltt` parser noise-floor | ✅ done — role/distance agreement 99.3% (silver labels trustworthy); noise is in segmentation (`results/cltt_noise_floor.json`) |
| mixed-effects model | ⏸ deferred (low marginal value given effect sizes) |
| Paper writeup | ✅ `paper/acl_latex.tex` (ACL template) → compiles to 5-page PDF `paper/acl_latex.pdf` |

---

## 1. Environment & layout

- Python 3.12; scripts are **stdlib-only so far** (no venv required to run extraction).
- OpenRouter API key in `.env` (gitignored) — not yet used.

```
experiment_01/
  data/
    CHECKSUMS.md                 # sha256 + LINDAT handles + cs_cltt provenance
    raw/                         # gitignored
      KUK_1.0/KUK_1.0/data/      # ESO, FrBo, KUKY, OmbuFlyers (+ ../metadata/)
      cltt_2.0/                  # PML/Treex (not used directly — see §3)
      cs_cltt/                   # UD_Czech-CLTT gold CoNLL-U (parser-QC gold)
    processed/
      kuk_pairs.jsonl            # 415k gold pairs — output of extract_pairs.py (GITIGNORED, ~250MB)
      kuk_exclusions.json        # filtering breakdown + examples
      eval_set.jsonl             # the N=640 sampled eval set (tracked; reproducible via --seed)
      eval_set_summary.json      # strata table + covariate breakdown
    results/
      cost_estimate.json           # machine-readable cost/token breakdown
      runs/                         # run_llm.py output: <model_id>.jsonl (full trace) + .failures.jsonl
  config/
    experiment.json                # run params + 4 model slugs/providers/prices (candidates)
  src/
    conllu_utils.py
    extract_pairs.py
    sample_eval_set.py
    estimate_cost.py
    llm_io.py                      # .env, prompt assembly, response parsing (shared by run_llm/score)
    run_llm.py                     # the prompting harness
    prompts/
      raw_text.txt                 # regime 1
      raw_to_conllu.txt            # regime 2
      conllu_input.txt             # regime 3
```

---

## 2. Data — what is actually on disk

Full KUK 1.0 archive re-extracted 2026-07-01 (an earlier extraction was partial — only 3 of 4
sub-corpora, no `metadata/`). Now complete and verified against the zip:

- **6,275 `.conllu` files, 910,373 sentences** across all 4 sub-corpora
  (ESO 5,615 files / FrBo 319 / KUKY 224 / OmbuFlyers 117), plus `metadata/` (26 TSVs, incl. the
  `ClarityPursuit` covariate source).
- UDPipe 2 `czech-pdt-ud-2.15-241121` + NameTag 3; genuine UD CoNLL-U.
- SHA256 of both source zips recorded in `data/CHECKSUMS.md`.

---

## 3. CLTT parser-QC gold — decision & verification

Use the existing **`cs_cltt`** (UD_Czech-CLTT) treebank as the parser-QC gold, **not** a hand
conversion of CLTT 2.0's PML. Verified 2026-07-01:

- `cs_cltt` README states it *"is based on the Czech Legal Text Treebank 2.0"* (1,121 sentences),
  with some upstream annotation fixes — so it is CLTT 2.0's data, already in CoNLL-U.
- Contains `root` (1,121), `nsubj` (1,632), `cop` (438) — everything the QC needs, extractable with
  the *same* code as KUK.
- Placed at `data/raw/cs_cltt/` (train/dev/test = 467/316/338); git commit recorded in CHECKSUMS.md.
- `udapi`/PML conversion is the **fallback** only if `cs_cltt` ever proves to diverge from CLTT 2.0.

---

## 4. Task operationalization as implemented (per METHODOLOGY §2)

- **Subject** `p` = the single `nsubj`/`nsubj:pass` dependent of the sentence root.
- **Predicate** `q` = head of that subject = **the root** (whatever its POS). Copular clauses
  therefore measure to the nominal/adjectival predicate; the **copula index is logged separately**
  (`cop_word`) so "measure-to-copula" is recoverable without re-running. *Provisional — pending
  linguist sign-off (`OPEN_QUESTION_predicate_definition.md`).*
- **Distance** = `|p − q| − 1` in **whitespace-words**. Multiword tokens (Czech `aby`→`aby`+`by`)
  collapse to one word via `conllu_utils.assign_word_indices` (MWT-aware). This is the single
  canonical unit across all three prompting regimes.
- **Clausal subjects** (`csubj`) are excluded from the primary set and counted separately.

### `src/conllu_utils.py`
CoNLL-U reader (`iter_conllu`), `assign_word_indices` (token id → 0-based whitespace-word index,
MWT-collapsed), `tree_depth`. The only subtle piece is the surface-word grouping: a surface unit is
glued to the next iff its MISC has `SpaceAfter=No`; MWT member tokens share the MWT's word index.

### `src/extract_pairs.py`
Reads all KUK `.conllu`, applies the filter (exactly one root, exactly one root-attached `nsubj`,
no clausal-only subject, word length in `[--min-words, --max-words]` default 5–80), computes the
gold record, and logs every exclusion with reasons + examples.

Run:
```bash
python src/extract_pairs.py \
  --kuk-root experiment_01/data/raw/KUK_1.0/KUK_1.0/data \
  --out-dir  experiment_01/data/processed
```
Each output row: `sent_id, subcorpus, variant, source_file, text, subj_{id,form,deprel,word},
pred_{id,form,upos,deprel,word}, is_copula, cop_{id,word}, distance, n_words, n_ud_tokens,
tree_depth, intervening_clauses, word_count_check`.

---

## 5. Extraction results (full KUK, 2026-07-01)

- **910,373 sentences → 415,462 pass (45.6%)**. Pass rate stable across sub-corpora
  (ESO 46.1% / FrBo 40.7% / KUKY 40.1% / OmbuFlyers 38.0%) — pooling across all four is sound.
- **Exclusions**: no main-clause subject 401,426 (mostly headings / nominal fragments — a real
  descriptive finding about legal Czech), clausal-subject-only 72,356, coordinated/multiple subjects
  14,312, length-out-of-bounds 6,790, subj==pred word 27.
- **Distance distribution**: min 0, median 1, mean 2.9, p90 7, **max 70**. Long tail exists but the
  bulk is distance ≤1 → the eval sample must **oversample the long-distance / long-sentence tail**
  (that is where H4 lives).
- **Validation**: **zero** word-count mismatches between the MWT-aware word count and a naive
  `text.split()` across all 415k candidates → the tokenization/word-mapping logic is trustworthy.
- Copular clauses: 17.7% of passing sentences; predicate UPOS = 74% VERB, rest ADJ/NOUN/etc.
  Spot-checked copular examples resolve the predicate to the nominal part correctly.

Full breakdown: `data/processed/kuk_exclusions.json`.

---

## 5b. Evaluation set — `src/sample_eval_set.py`

Stratifies the 415k gold pairs by **sentence-length bucket × word-distance bucket** (4×4 = 16
strata; edges `LENGTH_BUCKETS` 5–14/15–24/25–39/40–80, `DISTANCE_BUCKETS` 0–1/2–4/5–9/10+) and
allocates an **equal target per stratum** — deliberately oversampling the long/far tail where H4
lives (population median distance is 1; the sample's is 4.5).

Run (current official eval set):
```bash
python src/sample_eval_set.py \
  --pairs experiment_01/data/processed/kuk_pairs.jsonl \
  --out-dir experiment_01/data/processed \
  --per-stratum 40 --seed 20260701 --balance-subcorpus
```

- **N = 640** (16 strata × 40; all strata fully populated). Tunable via `--per-stratum`
  (METHODOLOGY §4 suggested 300–600; 40/stratum lands just above at 640).
- **Sub-corpus composition: BALANCED — 160 each (ESO/FrBo/KUKY/OmbuFlyers)** — user decision
  2026-07-01. Rationale: the pooled-random draw came out 95% ESO, which would make the paper's
  "Czech legal text" claim effectively a claim about ombudsman opinions only; balancing lets the
  mixed model test the finding *across* genres (sub-corpus as covariate/random effect). Trade-off
  accepted: the small corpora (esp. OmbuFlyers, ~1% of population) are heavily oversampled and thus
  less independent. `--balance-subcorpus` off = pooled/population-faithful (kept as an option).
- Sample: distance median 4.5 / mean 6.08 / max 42; length median 24.5 / mean 27.7; copular 25%.
- Outputs: `data/processed/eval_set.jsonl` (+ `length_bucket`/`distance_bucket` fields),
  `data/processed/eval_set_summary.json` (strata table, sub-corpus + covariate breakdown). Seeded
  (`--seed 20260701`) → reproducible.

---

## 6. Decisions log (resolved this cycle)

1. Distance unit = whitespace-words, canonical across all regimes. **Settled.**
2. Predicate = head-of-subject; copula logged. **Provisional** (linguist).
3. OpenRouter: pin provider + quantization, log per call (not yet implemented — for `run_llm.py`).
4. CLTT QC via `cs_cltt`. **Settled & verified.**

---

## 5c. Prompt templates — `src/prompts/`

Three Czech templates, one per regime, all eliciting the same JSON answer
(`{podmet, podmet_index, prisudek, prisudek_index, vzdalenost}`) so scoring is uniform:

- `raw_text.txt` (regime 1) — raw sentence → identify subject/predicate, count words between.
- `raw_to_conllu.txt` (regime 2) — model first emits CoNLL-U (between `<conllu>` tags), then the
  JSON; we score its reported distance AND recompute from its CoNLL-U (parse-vs-count split, §6/§5b).
- `conllu_input.txt` (regime 3) — given the real KUK CoNLL-U block, locate `nsubj` → head → count.

Each file has `### SYSTEM` / `### FEWSHOT` / `### USER` sections (split marker for `run_llm.py`),
2 few-shot examples (one verbal predicate, one copular — teaching predicate = nominal part, not the
copula), and the placeholder `{SENTENCE}` or `{CONLLU}`. All three encode the settled definitions:
whitespace-word unit, 1-based indices, distance = |p−q|−1. Regime 3 explicitly instructs converting
UD tokens → words (punctuation/MWT handling) since the input is tokenized but the answer is in words.

## 7. Run size & cost — see `docs/COST_REPORT.md`

`640 × 3 regimes × 4 model_ids × 3 runs = 23,040 generations`, ≈ **23M tokens** (input-dominated by
regime-3 CoNLL-U). Grounded estimate via `src/estimate_cost.py` (real texts + real CoNLL-U blocks +
measured prompt overhead): **full run ≈ $20**, of which **~94% is the single frontier model**; the
three open models total ~$1.2. **Cost is not a blocker** — the §5 cost-mitigation options are moot at
this scale; the real operational constraint is rate-limits/latency over 23k calls. Prices are
illustrative placeholders pending chosen slugs. Full breakdown + sensitivity in `docs/COST_REPORT.md`.

## 8. Harness design decisions (locked before build, 2026-07-01)

- **One sentence per prompt — never batched.** Preserves the 1:1 prompt→response→gold mapping the
  within-sentence paired design needs, avoids batch position/contamination effects, and keeps the
  `run` (temp-0 consistency) factor well-defined (re-send the *identical* single-sentence prompt 3×).
  Cost is irrelevant here so there is no reason to batch. Each call = system + fixed few-shot +
  one target sentence.
- **Full-trace persistence — store exact prompts AND unedited responses.** One append-only JSONL
  record per generation (sentence × regime × model × run). Raw and parsed kept strictly separate
  (parsing never mutates stored raw). Record schema:
  `cell_id` (`<sent_id>|<regime>|<model_id>|<run>`, idempotency key → resumable), `sent_id`,
  `source_file`, `subcorpus`, `regime`, `model_id`, `run_index`, `timestamp`,
  `request` (**exact** messages + params incl. provider routing), `prompt_template_sha`,
  `response_raw` (**full unedited** OpenRouter JSON — includes `usage` and the *actual* provider /
  model / quantization served), `completion_text` (verbatim), `parsed` (fields + `parse_status`).
  The full prompt string is stored per-record (not a reference) so the trace stays valid even if a
  template is later edited. `response_raw.*` provides the provider/quant audit trail (§6 item 3) and
  real token counts to reconcile against `COST_REPORT.md`.
- **Capture real per-call USD cost.** Send `usage: {include: true}` in every request → OpenRouter
  returns `usage.cost` (actual USD charged, reflecting real provider price + caching), alongside
  token counts and `cost_details`. This lands in the stored `response_raw`, so exact spend is
  summable per regime / model / distance bucket / sub-corpus and reconcilable against the estimate.
  Fallback: each response's `id` can be re-queried at `GET /api/v1/generation?id=<id>` for the same
  cost + `native_tokens_*` + provider name + latency if the flag was ever missed.

## 8b. On output variance & consistency (noted after smoke test)

The smoke test showed the same model giving different answers across runs. Two sources, kept
distinct in the analysis:
1. **Infrastructure variance** — provider/quantization/GPU-kernel differences (OpenRouter routed
   llama-8b to DeepInfra *and* Novita, with divergent answers). An artifact of the serving stack,
   **eliminated** by pinning provider+quantization (§5). This is why we pin before the full run.
2. **Residual temp-0 non-determinism + genuine model uncertainty** — FP non-associativity in batched
   GPU decoding, MoE routing, and boundary-flipping when the model isn't confident. This is what the
   `run` factor (§6) measures *after* pinning removes #1.

Framing for the paper / SPRINT: the instability is a **finding, not a bug to fix inside the LLM**.
A model that answers 6/6/13 to one counting task is evidence it can't reliably count → supports
SPRINT's "use a deterministic extractor for counting rules" conclusion. And **reproducibility ≠
correctness**: regime 3 gave a consistent-but-wrong 1/1/1 (gold 0), so consistency and accuracy are
reported as separate axes.

## 9. Next steps

1. **Confirm the 4 model slugs** (2 small + 2 large) + providers/quantizations in
   `config/experiment.json`; the frontier slot is a `CONFIRM/...` placeholder. `run_llm.py` is ready
   and config-driven, so this is the only blocker to a live run.
2. **Smoke test** — `run_llm.py --limit 1 --models small-llama-8b` (~1 sentence, all 3 regimes,
   few cents) to validate the live path + response/cost capture, then scale to the full eval set.
3. `score.py` (role-F1, distance exact/±1/±2, MAE, consistency, regime-2 parse-vs-count
   decomposition) and `error_analysis.py`.

`run_llm.py` is built to the §8 spec: one-sentence-per-call, provider+quant pinning,
`usage:{include:true}`, resumable (skips completed `cell_id`s), retry/backoff, full-trace JSONL.
Validated with `--dry-run`, a live smoke test, provider discovery, and a pinned re-verify (all 4
models 9/9 parse-ok on a single stable provider).

**Before the full run: clear `results/runs/*.jsonl`.** The existing records there are from the
smoke/discovery/sanity passes and used *mixed / unpinned* providers; keeping them would let resume
mix providers into the final dataset. The full run should start clean so every record comes from the
final pinned (provider·fp8) config.

**Bug fixed before the full run (2026-07-01):** `sent_id` resets per CoNLL-U file, so it is NOT
unique across the eval set — only 234 distinct `sent_id`s among the 640 sentences (535 collide).
The harness `cell_id` originally used `sent_id` alone → non-unique → resume would wrongly skip
colliding sentences. Fixed: `uid = "<source_file>::<sent_id>"`, `cell_id = "<uid>|regime|model|run"`,
and `uid` is now stored on every record (the join key for scoring). Caught ~89 calls in; run
restarted clean.
