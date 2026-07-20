# Experiment 04 — Methodology (v1)

Status: **v1 — CLTT-primary redesign of experiment_02 (decision 2026-07-20).** Identical research
questions, conditions, models, and task definition as experiment_02 v3.1; the **data foundation
changes**: the human-annotated CLTT treebank becomes the primary eval set and gold (derived, then
verified), the new 260-sentence annotation is cancelled, and the frozen KUK-640 becomes a
secondary robustness set. Experiment_02 is kept frozen and unchanged in case we return to it;
experiment_03 (LLM-boost sketch) is unaffected. Self-contained: everything needed to run
experiment_04 is defined here.

---

## 1. Goal and context

**Research question in one sentence:** *Can a pure-LLM rule — raw sentence in, verdict out, no
pre- or post-processing — measure subject–predicate distance in unfiltered Czech legal text well
enough to replace a deterministic parser pipeline, and how much model capability and how good a
rule formulation does it take?*

**The two experimental axes:**
- **Model capability** (ordered axis): open ~30B → open ~70B → frontier → frontier with
  reasoning. "How low can we go?"
- **Rule formulation** (categorical axis, redefined 2026-07-20 — O10): **R1 = the best naive
  rule** (full §3 definitions and examples, no counting scaffold) vs. **R2 = the best procedural
  rule** (same definitions + self-enumeration scaffold + self-check). Task knowledge is held
  constant, so R1-vs-R2 **isolates the counting scaffold**. The production rule verbatim is kept
  as an **optional reference arm R0** (one model only) to preserve the deployed before/after
  story. Further formulation exploration only if R2 wins.

**Practical motivation (SPRINT).** SPRINT rules are prose prompts written by lawyers; the app
sends each sentence plus the rule prompt to an LLM and parses `{has_violation, reason,
suggestion}` from the reply. The production distance rule (§5.2 R1) does not work well — the
finding that motivated this work. The alternative — UDPipe plus a hand-coded extractor — is
accurate but is *per-rule engineering*. A pure-LLM rule is *per-rule prose*: deployable in
today's SPRINT by editing rule text. The economics favor the LLM path wherever it is good enough;
this experiment measures whether and when it is.

**Scientific motivation (exp_01 sequel).** Experiment_01 showed on filtered legal Czech that the
LLM bottleneck is *counting*, not role identification (large open models miscount ~28–36% even
when handed the parse; instability cannot be tuned away). Open questions answered here: (a) do
frontier/reasoning models close the counting gap end-to-end? (b) does scaffolded prompting
(explicit enumeration with a counter — scratchpad/CoT-counting, `docs/RELATED_WORK.md` in
experiment_02) close it at open-model sizes? Both on unfiltered data, against human-tree gold.

**Why CLTT-primary (the redesign, 2026-07-20).** Measured on the derived gold: CLTT's verdict
prevalence is **17.3% → 194 positive sentences** out of 1,121, versus ≈20 expected positives in
experiment_02's planned 200-sentence gold slice — an order-of-magnitude power upgrade that
*eliminates* the new-annotation effort instead of adding to it (Katka verifies; she does not
annotate). CLTT is also harder, more SPRINT-relevant text (statutes; p90 sentence length 58 words
vs. ESO's 40) and is co-authored by our co-author (Hladká), fitting the joint paper's data
section. Costs of the trade and their mitigations: §4.4.

## 2. Research questions and hypotheses

- **RQ1 (parity):** Does the best pure-LLM configuration reach the parser baseline at the verdict
  level on unfiltered legal Czech?
  **H1:** the frontier model with reasoning comes within ~5 pts of the parser baseline's verdict
  accuracy. (Open: the parser baseline's own accuracy on unfiltered statute text is unknown —
  §5.1 measures it, segmentation error included.)
- **RQ2 (capability floor):** How does verdict accuracy scale down the capability axis?
  **H2:** accuracy degrades monotonically; ~30B is below viability under either formulation.
  (≤8B omitted as settled by exp_01.)
- **RQ3 (formulation effect):** How much does the procedural formulation buy at each capability
  level? **H3:** R2 > R1 everywhere, with the gain *growing* with capability.
- **RQ4 (mechanism, from scoring only):** Where do residual errors live?
  **H4:** open models' errors concentrate in counting (right words, wrong distance); frontier
  reasoning shifts the residual to identification.

## 3. Task definition

Identical to experiment_02 v3.1 §3 (Katka-reviewed 2026-07-16; K6 provisional), summarized here
for self-containment; worked examples: `docs/WORKED_EXAMPLES_katka.md`.

**Unit of evaluation: the sentence as segmented by the CLTT gold treebank** (primary set) or by
UDPipe (KUK secondary set). Segmentation is held fixed per set and inherited by all conditions
equally; the parser arm's internal re-segmentation is handled per §5.1.

**Output per sentence: the set of all subject–predicate pairs** of finite clauses with an overt
nominal subject — possibly empty (fragments; 26% of CLTT sentences have no pair) and possibly
plural (mean 1.41 pairs/sentence in CLTT; up to 18 observed). Per pair: subject word, predicate
word, 1-based word positions, distance. Sentence verdict: **violation ⇔ any pair has d > T,
T = 6** (i.e. seven or more words strictly between; K5 + production rule).

**Pair definition (§3.1–§3.3 of exp_02, unchanged):**
- **Subject** = the `nsubj`/`nsubj:pass` head word (coordinated subjects → first conjunct, K3).
- **Measured predicate = the agreement-bearing element** of the predicate complex, priority:
  (1) finite aux/cop (`VerbForm=Fin`; conditional preferred) — *je, jsem, bude, by*;
  (2) participial aux/cop (`VerbForm=Part`) — *byla* in past passives (*byla provedena*) and past
  copulars (*byla krátkodobá*);
  (3) the clause head itself (finite verb or bare l-participle, *rozhodl*).
  aby/kdyby clauses: the absorbed conditional `by` maps to the surface conjunction word via the
  multiword-token collapse (verified in `cs_cltt`).
- **Distance** `d = |pos(subj) − pos(pred)| − 1` in whitespace words (1-based; glued punctuation
  belongs to its word; MWTs = one word; mapping via `SpaceAfter=No`, ported from exp_01).
- **No pair:** pro-drop clauses (23% of CLTT sentences contain one), `csubj` (counted), verbless
  clauses (subject on a non-verbal head with no aux/cop; rare — K7 open), fragments.
- **Open items:** K6 (shared-subject coordination = one pair, provisional; annotators/verifiers
  flag further conjunct verbs so both conventions stay recomputable), K7 (verbless), K8
  (relative-pronoun subjects — included, flagged `subj_is_rel`; lemma/XPOS fallback because the
  converted CLTT treebank has sparse `PronType` features).

## 4. Data

### 4.1 Primary eval set + gold: CLTT (`cs_cltt`), N = 1,121 — derived gold, verified

`cs_cltt` (UD_Czech-CLTT, from CLTT 2.0; Kříž & Hladká) — **1,121 human-annotated dependency
trees** of Czech statute text (accounting law domain), at repo root `data/raw/cs_cltt/`
(provenance: `data/CHECKSUMS.md`). The whole treebank is used; no sampling, no linguistic
filtering.

**Gold pairs are derived mechanically** by applying the §3 rule to the human trees
(`src/derive_cltt_gold.py` → `data/cltt_gold_pairs.jsonl`): 1,586 pairs. Because the trees are
human-annotated, no parser is involved in the gold — but the gold *is* mediated by our
UD-interpretation layer (§4.4, cost 1). Descriptive statistics: `docs/AUDIT_cltt.md`. Key
figures: verdict prevalence **17.3%** (194 positive sentences); 26.2% zero-pair sentences;
distance tail 116 pairs with d ≥ 10; median length 22 words, p90 = 58, max 466.

**Gold validation (replaces the cancelled annotation):**
1. **Rule sign-off:** Katka reviews ~24 worked examples spanning all construction types
   (`docs/WORKED_EXAMPLES_katka.md`) — any error there is in our rule, not in a parse.
2. **Verification pass (~100 pairs):** Katka verifies a stratified sample of derived pairs —
   *all* pairs of the rare constructions (conditional 9, aby/kdyby 9, past copular 3) + ~80
   random pairs of the common types; for each: sentence (windowed), pair, distance → ✓/correct.
   Verification is ~10× cheaper than annotation and yields a **measured error rate of the derived
   gold**, reported in the paper alongside CLTT's published annotation quality.
3. Disagreements → rule fix + re-derivation (cheap, deterministic), or a documented gold
   correction list.

### 4.2 Secondary set: KUK-640 (ESO), silver-only — robustness and contamination check

The frozen experiment_02 eval set (`../experiment_02/data/eval/eval_640.jsonl`; uniform random
over deduplicated unfiltered ESO, seed 20260717) is reused **without any annotation**: silver
extraction only. Purpose:
- **Contamination check:** `cs_cltt` is a public UD treebank (GitHub); frontier models have
  plausibly seen its sentences *with trees* in pretraining. If the best configurations' agreement
  pattern vs. the parser arm on KUK-640 matches their pattern vs. gold on CLTT, memorization is
  not driving the CLTT results.
- **Domain foothold:** keeps one result in the PONK domain (ombudsman prose) while the primary
  claim moves to statutes.
Run economics: the secondary set is evaluated only with the **best 2 configurations** identified
on CLTT (plus the parser arm), not the full grid.

### 4.3 Descriptive statistics — the metric family

One table from the CLTT gold trees (tree depth, subordinate clauses, coordination density,
passives, max pair distance per sentence; in `docs/AUDIT_cltt.md`), situating the distance rule
in the counting-rule family and documenting rule-firing prevalence on real statute text.

### 4.4 Costs of the CLTT-primary trade (stated, mitigated)

1. **The gold is rule-mediated, not definition-native.** A systematic error in our UD→definition
   layer would propagate into the gold invisibly (both arms scored against the shared mistake —
   the class of bug that the participial-aux fix exposed). Mitigations: the two-step validation
   (§4.1) puts a *measured* bound on exactly this risk; the KUK-640 secondary set provides an
   independent lens (its silver comes from a different pipeline: UDPipe parses, not gold trees).
2. **Public-treebank contamination** (LLM may have memorized cs_cltt trees): mitigated by the
   KUK-640 agreement-pattern check (§4.2) and noted honestly in limitations; the task output
   (Katka-definition pairs, word-based distances, verdicts) appears nowhere verbatim in the
   treebank.
3. **Domain narrowing** to accounting-law statutes: acknowledged; arguably a better fit for the
   SPRINT-legislative framing, and the secondary set keeps the PONK domain represented.

## 5. Conditions

Two arms, identical to experiment_02 v3.1 §5 except for the parser arm's segmentation handling.

### 5.1 Parser arm — deterministic baseline (no LLM)

UDPipe 2 (`czech-pdt-ud-2.15`, the same model used for KUK silver; via the LINDAT API, responses
cached) parses the **raw text of each gold sentence unit**; the §3 extraction code runs over the
result and the verdict is computed.

**Two configurations, both run (2026-07-20); the baseline is the presegmented one:**
- **default tokenizer:** UDPipe re-segments 46% of units; pairs are unioned across sub-sentences
  with word-offset mapping. Measured: verdict F1 91.3 (recall 86.6) — the misses are almost
  entirely segmentation-driven (violating pair split across fragments; see
  `docs/PARSER_ARM_ERROR_ANALYSIS.md`).
- **`tokenizer=presegmented`** (unit declared to be one sentence — the honest deployment
  configuration, since units are defined upstream): verdict **F1 97.1** (acc 99.0, P 97.9,
  R 96.4; TP 187 · FP 4 · FN 7), pair form-F1 **95.6**, distance-given-match 99.8%.
The presegmented config is the baseline the LLM arm must be compared against (anything else
would strawman the parser); the default config is reported as the measured **cost of naive
segmentation** (~6 pts verdict F1). The parser arm's residual error vs. gold = parse errors
only (attachment/labeling), the interpretation layer being shared and separately validated
(§4.1). Implementation complexity (LOC, rules, edge cases) recorded as the maintainability
datum — the presegmented flag is part of it.

### 5.2 LLM arm — pure-LLM rule (prompt-only, SPRINT-compatible)

Raw sentence unit in the prompt; model returns JSON with the pair list **and** the verdict; the
model's own `has_violation` is the scored verdict. No pre/post-processing. Code-side validation
(schema, index bounds, form-at-index) recorded as measurement, never corrected.

Rule formulations (drafts in `src/prompts/`, frozen after Katka + smoke test):
- **R1 — best naive rule** (`r1_naive.txt`): full §3 definitions with examples (predicate =
  agreement-bearing element incl. past *byla* and aby-conjunction; overt-subject requirement;
  pro-drop/fragment/coordination conventions; word/distance definitions), few-shot examples with
  answers — but **no procedure, no enumeration, no self-check**. "The best rule a lawyer could
  write without prompting techniques."
- **R2 — best procedural rule** (`r2_procedural.txt`): the **same definitions**, restructured as
  an explicit procedure (SPRINT `_mod` pattern + the scratchpad/counting literature): (1) find
  finite clauses and predicates; (2) find overt subjects; (3) **enumerate the sentence word by
  word** (one `number: word` line each — the self-enumeration scaffold, atomic-alignment format);
  (4) read off positions, subtract, compare with T = 6; (5) **self-check** endpoints against the
  enumeration. Same few-shot sentences as R1, with the enumeration shown.
- **R0 — production rule verbatim (optional reference arm, one model):**
  (`r0_production_verbatim.txt`) faithful Czech adaptation of the SPRINT export, preserving its
  underspecification (garbled example repaired — O5). Adds ~3.4k generations if run.
Because R1 and R2 share task knowledge and few-shot sentences, **R1-vs-R2 isolates the
scaffold**; R0-vs-R1 measures what better definitions alone buy (the Ginn & Palmer 2025
rules-vs-examples caveat applies to R0-vs-R1 and is stated in the paper). Shared output schema
`{"pairs": [{"podmet", "podmet_index", "prisudek", "prisudek_index", "vzdalenost"}],
"has_violation"}`; scoring strips glued punctuation from word forms before form matching.

## 6. Models and run protocol

| capability slot | candidates (verify on OpenRouter at run time — O2) | modes |
|---|---|---|
| frontier | one of: OpenAI GPT-5.x / Anthropic Claude Opus-Sonnet 4.x / Google Gemini 3 / xAI Grok 4 | reasoning **on** and **off** |
| open ~70B | Qwen-2.5-72B-Instruct (anchor, bridges exp_01) | standard |
| open ~30B | Qwen3-32B or Gemma-3-27B | standard |

**Primary grid:** 1,121 sentences × 4 model-modes × 2 formulations × 3 runs = **26,904
generations**. **Secondary (KUK-640):** best 2 configurations × 3 runs = 3,840. Total ≈ 30.7k.
Cost: open models single-digit USD; frontier reasoning dominates — estimate **$100–400**.

Decoding: temperature 0, pinned provider+quantization where the API allows; reasoning-mode
parameters recorded; run-to-run spread is a measured property. Full traces + real `usage.cost`
captured. **Anti-caching protocol** (as exp_02): three separate full passes per condition, item
order shuffled per pass, provider prompt-caching disabled where exposed, cache-hit fields and
fingerprints logged; interpretation asymmetry stated (caching can only inflate consistency).

## 7. Metrics and analysis

**Primary — verdict quality vs. CLTT gold (N = 1,121, 194 positives) at T = 6 (violation ⇔
d > 6):** accuracy, precision, recall, F1 of `has_violation`. Parser arm scored identically.

**Secondary — measurement quality:** pair identification P/R/F1 matched by word form (greedy,
ties by index proximity; index-based matching reported separately — the form/index gap *is* the
positioning failure); distance exact / ±1 / MAE on form-matched pairs; **decomposition (H4):**
distance-correct given both endpoints named, per model-mode × formulation.

**Stability:** verdict flip rate and exact-set match across the 3 runs (per anti-caching notes).
**Cost:** real USD per 1k sentences per condition; latency.
**Validation catch-rates:** schema / bounds / form-at-index failures per condition.
**Breakdowns:** phenomenon flags (copular incl. past, conditional, aby, pro-drop present,
vs-order, fragment, `subj_is_rel`), pair count, length, distance band (near-threshold d ∈ [4, 9]),
and the targeted rare-construction pairs (diagnosis only).

**Statistical power (the redesign's payoff):** n = 1,121 paired verdicts with 194 positives —
McNemar resolves ~3–4 pt differences at α = 0.05; recall CIs half-width ≤ ~7 pts even in the
worst case. (Experiment_02's gold-200 design resolved only ~7–9 pts.)

**The one figure:** verdict accuracy (y) vs. capability (x: 30B → 70B → frontier →
frontier+reasoning), two curves (R1, R2), dashed horizontal parser baseline + CI, inset with the
H4 identification-vs-counting decomposition. McNemar on paired verdicts for the key comparisons.
**Qualitative error pass:** 20–30 residual errors of the best LLM configuration and of the
parser arm, hand-categorized (feeds the paper's error analysis and exp_03's inventory).

## 8. Execution plan

1. ✅ Derive CLTT gold + audit + worked examples (`src/derive_cltt_gold.py`; done at creation).
2. **Katka:** worked-examples sign-off (K9) + K6/K7/K8 rulings → freeze the rule; generate the
   ~100-pair verification sheet (`src/make_verification_sheet.py`, to write); she verifies →
   measured gold error rate; re-derive if the rule changes.
3. Parser arm: UDPipe-parse the 1,121 raw sentence units (LINDAT API, cached to
   `data/parser_arm/`), union-extraction with word-offset mapping (§5.1), score vs. gold.
4. R1 Czech adaptation + R2 written; frozen after a 20-sentence smoke test (format compliance
   only); roster + providers pinned (O2).
5. Primary grid (26.9k generations), three shuffled passes per condition; resumable harness with
   traces (port of exp_01 `run_llm.py`).
6. Scoring, figure, breakdowns; pick best 2 configs → secondary KUK-640 run (3,840 generations);
   agreement-pattern analysis (§4.2).
7. Error inventory exported for experiment_03.

## 9. Deliverables

1. **The figure + the recommendation:** the least capable model × formulation (if any) whose
   verdict quality reaches the parser baseline on statute text — or the finding that none does.
2. **The R2 rule template** in SPRINT `prompt_content` format.
3. **Gold data:** 1,586 CLTT-derived pairs under the signed-off §3 definition, with a measured
   verification error rate — the first gold dataset for this task, plus the KUK-640 silver set.
4. **The honest parser-baseline number** on unfiltered statute text, segmentation error included.
5. Full traces, costs, code.

## 10. Relationship to other experiments and the joint paper

- **experiment_02 (frozen):** the KUK-primary design with fresh annotation; return to it if the
  CLTT gold fails validation (§4.1) or the contamination check (§4.2) is inconclusive.
- **experiment_03 (sketch):** unchanged; its enrichment sampling draws on KUK silver + this
  experiment's error inventory; its headroom number now comes from §5.1's parser-arm accuracy.
- **Joint paper:** Katka's free-word-order section → RQ1 phenomenon breakdowns; "Golden Truth
  Data" → §4.1 (CLTT-derived + verified — showcasing the co-authors' own treebank); experiments
  → the figure; "LLMs and traditional tools together" → per-rule-prose vs. per-rule-engineering
  economics + exp_03 outlook.

## 11. Open items and decision record

**Open:**
- **O2 (narrowed 2026-07-20):** OpenRouter availability/pricing verified. Frontier candidates
  with a reasoning toggle: `openai/gpt-5.1` ($1.25/$10 per M — cost-optimal primary candidate)
  or `anthropic/claude-sonnet-5` ($2/$10, alternate). Final pick + provider pinning at prompt
  freeze; open ~30B/70B slots re-verified then.
- **O5:** garbled `teaching_examples` + English-testset question → KMH.
- **K6–K9: provisionally CLOSED by self-adjudication (2026-07-20,
  `docs/PROVISIONAL_ANSWERS_K6-K9.md`)** — K6 one pair (first verb); K7 exclude verbless; K8
  include rel-pron subjects in headline + separate breakdown; K9 worked examples self-reviewed.
  The design proceeds; **Katka verifies asynchronously** — impactful reversals (only K6 touches
  prompts) trigger a follow-up re-run, K7/K8 reversals are rescoring-only.

**Resolved (this experiment):**
- **O9** (2026-07-20): CLTT-primary redesign adopted (Tomáš) — power 194 vs. ~20 positives, no
  new annotation; gold-260 cancelled; KUK-640 demoted to secondary. Exp_02 frozen, not rewritten.
- **O10** (2026-07-20): formulation axis redefined (Tomáš) — R1 = best naive, R2 = best
  procedural (same definitions → scaffold isolated); production-verbatim kept as optional R0.
- **O11** (2026-07-20): open ~30B slot = **gemma-3-27b-it** (DeepInfra fp8, pinned) — qwen3-32b
  rejected in the smoke test: the endpoint ignored `reasoning.enabled=false` and hidden thinking
  consumed the whole 6k-token budget (3/40 calls empty). Gemma is natively non-thinking; both
  were named §6 candidates.
- **Prompts frozen v1** (2026-07-20): smoke test passed (gemma-27b 40/40 parse-ok, qwen-72b
  40/40; format compliance only, no metric peeking). Template SHAs recorded per trace.
- **Execution status** (2026-07-20): K6–K9 provisionally closed; open-model grid (gemma-27b +
  qwen-72b × R1/R2 × 3 passes × 1,121 = 13,452 calls) launched; **frontier deferred** until
  open-model results are in — then full grid, a sample, or hard-cases-only (Tomáš's call,
  assuming frontier handles the easy mass well).
- **Parser-arm preliminary results** (2026-07-20, `docs/PARSER_ARM_RESULTS*.md` +
  `docs/PARSER_ARM_ERROR_ANALYSIS.md`): default tokenizer — verdict F1 91.3 (R 86.6), per gold
  pair 92.1% found-exact / 0.2% found-wrong-distance / 7.8% missed; misses **segmentation-driven**
  (split units miss 10.7% vs. 1.7%; 24/26 verdict FNs = violating pair lost in a split unit).
  **`tokenizer=presegmented` fixes most of it:** verdict F1 **97.1** (R 96.4), pair form-F1 95.6
  — adopted as the baseline configuration (§5.1). K7/K8 sensitivity: negligible.
  Consequence for exp_03: verdict-level headroom shrank to 7 FN + 4 FP sentences; remaining
  parser error is genuine parse error (~4.7% of pairs), not segmentation.
- Inherited from experiment_02 v3.1: K1–K5 (Katka 2026-07-16), O1 (production rule obtained),
  O3 (obsolete — no IAA needed under verification design), O6–O8 (ESO population / gold slice /
  data-root move), participial-aux rule fix, T = 6 as *maximum allowed* (violation ⇔ d > 6).

## 12. Out of scope

As experiment_02 v3.1 §12 (no pre/post-processing around the LLM, no parse hints, no tool use,
no fine-tuning, no extra formulations, ≤8B settled, LLM-repairs-UDPipe → exp_03, semantic triage
→ exp_03, surprisal/DLT future work), plus: new human annotation of any kind (the verification
pass is the only human-in-the-loop step).
