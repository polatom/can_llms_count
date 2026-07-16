# Experiment 02 — Methodology (draft v1, for review)

Status: **draft — pending review by Katka (linguistic operationalization, §3) and Tomáš (roster,
budget, open questions §12).** Self-contained: everything needed to run experiment_02 is defined
here; experiment_01 is cited for motivation only, no artifacts are reused.

---

## 1. Goal and context

**Main objective (practical):** find a reliable, affordable, maintainable way to measure the
subject–predicate distance in Czech legal sentences — the validated proxy for comprehensibility
that PONK-style rules need — and determine which of three candidate production pipelines should
implement it.

**Context.** Experiment_01 established, on a filtered (single-main-clause) sample of legal Czech:
(1) LLMs' weak link is *counting*, not role identification — large open models name the right
subject/predicate ~83–87% given a parse but still miscount the span ~28–36% of the time;
(2) structured input helps a lot (+38–39 pts) but not to reliability;
(3) the instability cannot be tuned away — majority voting does not improve accuracy;
(4) UDPipe agrees with human gold ~99% on role labels where it commits (single-clause parses).

Experiment_02 changes three things at once, deliberately:
- **No linguistic filtering** — the eval set includes multi-clause sentences, pro-drop clauses,
  coordination, fragments/headings: exactly the material a comprehensibility linter must handle.
- **Predicate = finite verb** (Katka's definition, §3) — replacing exp_01's provisional
  head-of-subject rule.
- **Human gold as the primary standard** — silver (UDPipe) is demoted to secondary large-N support,
  since silver is least trustworthy exactly on the newly-included complex sentences.

## 2. Research questions

- **RQ1 (identification):** Can LLMs identify subject–predicate pairs in *unfiltered*,
  free-word-order Czech legal text, measured against human gold? Which linguistic phenomena
  (pro-drop, coordination, non-SVO order, copular predicates, syncretism, fragments) drive failure?
- **RQ2 (counting):** Is the counting bottleneck irreducible? Specifically: (a) does pre-numbering
  the words in the prompt (externalizing the count into preprocessing) eliminate it for mid-size
  open models? (b) does frontier scale and/or test-time reasoning eliminate it end-to-end?
- **RQ3 (pipelines):** Which production pipeline gives the best accuracy × stability × cost ×
  maintainability trade-off:
  - **A — deterministic:** UDPipe → rule-based extractor (PONK-style); no LLM.
  - **B — frontier end-to-end:** one prompt, raw text in, pairs + distances out.
  - **C — hybrid:** cheap preprocessing (numbered word list, optional compact UDPipe hints) →
    small/mid open LLM selects pairs by index → code computes distances.

## 3. Task definition

**Unit of evaluation: the sentence** as segmented by UDPipe (KUK) or by the gold treebank (CLTT).
Sentence segmentation of legal Czech is a known fallible upstream step (exp_01: UDPipe splits ~60%
of CLTT gold sentences differently); it is held fixed here and inherited by all pipelines equally.

**Output per sentence: the set of all subject–predicate pairs** of finite clauses with an overt
nominal subject — possibly empty (fragments, headings, verbless enumeration items) and possibly
plural (multi-clause sentences, coordination of clauses). For each pair: subject word, predicate
word, their 1-based word positions, and the distance.

### 3.1 Predicate (Katka's definition — operationalized in UD, needs her sign-off)

Per the paper draft (§ *Subject and predicate in free word order languages*): the predicate for
measurement purposes is **the verb in finite form, or the auxiliary verb in analytic verb forms
and modal constructions — i.e. the element that carries grammatical agreement with the subject.**
For verbo-nominal (copular) predicates: **the copula**, not the nominal part.
(Note: this *reverses* exp_01's provisional rule, which measured to the nominal part.)

UD operationalization — for each clause whose predicate head is a verb or a copular nominal:

| clause type | example | measured predicate token |
|---|---|---|
| simple finite verb | *Soud **rozhodl** …* | the verb itself |
| analytic past (aux present) | *… **jsem** rozhodl* | the finite AUX (*jsem*) |
| analytic past 3rd person (no aux) | *Soud **rozhodl** o …* | the l-participle itself |
| analytic future | *Soud **bude** rozhodovat* | the finite AUX (*bude*) |
| conditional | *Soud **by** rozhodl* | the conditional AUX (*by/bych/bys*) — **K2** |
| passive | *Rozhodnutí **bylo** vydáno* | the finite AUX (*bylo*) |
| copular (verbo-nominal) | *Zákon **je** účinný* | the copula (*je*) |
| multiple auxiliaries | *Soud **by** byl rozhodl* | the **leftmost** finite AUX — proposal, **K1** |

Mechanically: take the clause head; if it has finite `aux`/`aux:pass`/`cop` children, the measured
predicate is the *leftmost* finite one; otherwise the clause head itself (which is then a finite
verb or l-participle).

### 3.2 Subject

The word bearing the `nsubj`/`nsubj:pass` relation to the clause head (the head word of the
subject phrase; for coordinated subjects, the first conjunct — the UD head — **K3**).

### 3.3 Exclusions and null cases (inside sentences that are all kept)

- **Pro-drop clauses** (finite predicate, no overt subject): no pair is produced for that clause.
  Systems must *not* hallucinate a subject — false positives are penalized via precision (§8).
- **Clausal subjects** (`csubj`): excluded from pairs (no single word position); counted and
  reported. **K4**
- **Fragments / verbless headings:** gold = empty set. Correctly returning "no pairs" is scored.

### 3.4 Distance

`d = |pos(subject) − pos(predicate)| − 1`, counted in **whitespace-separated words** (1-based;
punctuation glued to a word belongs to that word; multiword tokens like *aby* = one word).

Token→word mapping (from CoNLL-U): collapse multiword-token ranges into one surface unit, then
increment the word counter only after units not marked `SpaceAfter=No`. (Port of exp_01's
`assign_word_indices`, validated there with zero mismatches against raw text.) The same code
generates the numbered word lists used in pipeline C prompts and in annotation sheets, so gold,
prompts, and scoring share one coordinate system.

## 4. Data

**Source:** KUK 1.0 (four sub-corpora, UDPipe-parsed silver) + CLTT 2.0 / `cs_cltt` (human gold
trees). Fresh sample; nothing reused from exp_01.

**Filtering: none linguistic.** Only technical exclusions, each logged with counts:
exact-duplicate sentences after whitespace normalization (legal boilerplate), and length > 200
words (context sanity; expected rare). Fragments, headings, multi-clause monsters all stay in.

### 4.1 Main eval set (silver, N = 640)

Stratified sample from unfiltered KUK:
- **Strata:** number of finite clauses (0 / 1 / 2 / 3+, from silver) × sentence length
  (≤10 / 11–25 / 26–45 / 46+ words), with the multi-clause and long cells oversampled relative to
  population (they are the PONK-relevant tail), and the distance tail of the first pair oversampled
  within the 1-clause stratum (continuity with exp_01's H4-style analysis).
- **Sub-corpora:** balanced 160 × 4 (continuity with exp_01; population-proportional weights
  reported as a secondary view). **T3**

### 4.2 Human gold (primary standard)

- **KUK-200 (new annotation, Katka):** 140 sentences sampled from the 640 (proportionally across
  strata — enables direct silver-vs-gold noise measurement on eval items) + 60 targeted at rare
  phenomena: copular predicates, pro-drop-heavy multi-clause sentences, non-SVO orders, syncretic
  nominative/accusative candidates, fragments. Annotation = mark all pairs by word index on
  pre-numbered word lists (tooling: a simple TSV/HTML sheet; guidelines doc to be drafted as
  `ANNOTATION_GUIDELINES.md` after §3 sign-off).
- **IAA:** 50 of the 200 double-annotated (second annotator: Bára? **T4**); report pair-level
  agreement and distance agreement.
- **CLTT-derived gold (free):** apply the §3 rule mechanically to `cs_cltt` gold trees →
  gold pairs for ~1k unfiltered legal sentences at zero annotation cost. Katka reviews ~20 worked
  examples (stratified over the §3.1 table rows) instead of annotating. Domain caveat (accounting
  law) reported.

### 4.3 Silver noise floor, re-measured

Exp_01's 99.3% parser-agreement figure was measured on single-clause commits only. Re-run the
noise floor on **unfiltered** CLTT: UDPipe-parse the raw text, extract pairs per §3, compare
against CLTT-derived gold. This yields the honest accuracy of **pipeline A** on complex legal
Czech — a genuinely open number, and the benchmark the LLM pipelines must beat or approach.

## 5. Pipelines (RQ3) and prompt conditions

All pipelines produce the same output schema: JSON list of
`{"podmet": str, "podmet_index": int, "prisudek": str, "prisudek_index": int, "vzdalenost": int}`
(empty list allowed).

**Prompt style (B and C): procedural, pseudo-code steps.** One prompt formulation per condition,
structured as an explicit step sequence rather than a single instruction:
1. identify all predicates (§3.1 definition + examples);
2. for each predicate, identify its overt subject if any (§3.2 definition + examples);
3. branch on what was found — no pair (pro-drop, fragment) → empty list; one pair; multiple
   pairs (multi-clause, coordination) → list all.
The branching is not prompt sophistication for its own sake — it mirrors the §3.3 task definition
that unfiltered text forces. Few-shot examples cover each branch: simple SVO, copular, analytic
form, pro-drop (no pair), multi-clause (two pairs), fragment (empty).

**Design principle (from exp_01): the model never produces a number it had to count for.** Every
count is either precomputed into the input (word numbering, C) or derived from the model's output
in code (subtraction, validation). No prompt asks the model to count words, simulate a regex, or
"execute" a code snippet — simulated execution is the exact skill exp_01 showed to be broken, and
real code execution (tool use) is a different pipeline class (§13).

- **A — UDPipe + deterministic extractor.** UDPipe 2 (same model as KUK silver) → §3 extraction
  code → pairs + distances. Zero LLM, zero variance. Its implementation complexity (LOC, rules,
  edge cases handled) is *recorded* as data for the maintainability comparison.
- **B — frontier end-to-end.** Raw sentence text in the prompt; model identifies pairs, positions,
  and computes distances itself. This is "pipeline 2" (expensive but simple). Run with 2–3 frontier
  models; for one of them, both reasoning-off and reasoning-on (RQ2b).
- **C — hybrid (the target).** Two input variants, both with distances computed **in code** from
  the model-selected indices (`vzdalenost` requested from the model only as a consistency check,
  never scored as the pipeline output):
  - **C1 — numbered words:** prompt contains the pre-numbered word list (`1:Zákon 2:je 3:účinný.`);
    the model selects pairs by index. Tests whether externalizing the count is sufficient.
  - **C2 — numbered words + parse hints:** C1 plus a compact, human-readable UDPipe extract —
    only `nsubj`, `aux`, `cop`, and clause-head edges, rendered as `word#i ←nsubj— word#j` lines.
    No full CoNLL-U anywhere (exp_01 showed it is unstable to generate and unnecessary to give).

**Post-processing validation (all LLM pipelines, deterministic, in code):**
1. schema check (valid JSON, required fields, integer indices);
2. index bounds (1 ≤ index ≤ n_words — subsumes "distance < sentence length");
3. subject index ≠ predicate index;
4. **form-at-index check:** the reported word form must equal the word actually at the reported
   index. This catches exp_01's signature failure (right word, wrong position) deterministically.
Validation results are *recorded* for every generation (catch rates by check, model, condition —
reported as a finding). **Optional C+retry variant:** one re-prompt with the specific validation
error appended; implemented only if trace analysis shows validation catches a meaningful share of
errors (decided after the main run, no re-run needed for the analysis itself). Validation flags
and retries; it never auto-corrects from the parse — that would collapse C into A.

**Dropped from exp_01:** self-generated CoNLL-U (least stable regime; diagnostic job done),
full-CoNLL-U-given (superseded by C2), LLM-verifies/repairs-UDPipe (out of scope).

## 6. RQ2 counting probes (subset only)

On a ~200-sentence subset (stratified by length), models from B and C answer isolated probes:

- **P1 — locate:** "What is the word position of *X*?" (endpoint word given, occurrence
  disambiguated by a context snippet). Exp_01 says this is the broken skill (~55% at 70B).
- **P2 — count between:** both endpoint words given, return the distance.
- **P3 — subtract:** two positions given, return |p−q|−1 (arithmetic control; expected ~100%).

Run with reasoning-off and reasoning-on where available. P1/P2/P3 decompose *count = locate +
subtract* and localize whatever failure remains at frontier scale.

## 7. Models (verify availability/pricing on OpenRouter at implementation time)

| role | candidates | runs |
|---|---|---|
| frontier (pipeline B) | 2–3 of: OpenAI GPT-5.x, Anthropic Claude Sonnet/Opus 4.x, xAI Grok 4, Google Gemini 3 | 3 × temp 0 (or provider default if temp unsupported) |
| frontier reasoning toggle (B + probes) | one of the above with effort/thinking low ↔ high | 3 × each mode |
| open anchor (B-style raw + C1 + C2) | Qwen-2.5-72B (bridge to exp_01) | 3 × temp 0, fp8, provider-pinned |
| open mid (C1 + C2) | one of ~30B class, e.g. Qwen3-32B / Gemma-3-27B | 3 × temp 0, pinned |
| open small (C1 + C2) | one of ~8B class, modern | 3 × temp 0, pinned |

Decoding: temperature 0 and pinned provider+quantization wherever the API allows; for reasoning
models, record the actual sampling/effort parameters and treat run-to-run spread as a measured
property (it is part of the RQ3 stability criterion, not a nuisance to hide). Full prompt+response
traces and real `usage.cost` captured as in exp_01.

## 8. Metrics

**Identification (RQ1) — pair-level P/R/F1** against gold. A predicted pair matches a gold pair by
*word form* of both endpoints (order-insensitive within the pair; greedy alignment, ties broken by
index proximity). Strict index-based matching reported separately — the gap between form-based and
index-based matching *is* the positioning failure, so keeping both is the exp_01 decomposition in
metric form.

**Distance (RQ2) — on form-matched pairs:** exact / ±1 / MAE. Plus the probe accuracies (§6).

**Practical rule verdict (RQ3, secondary):** per sentence, "flag if any pair has d ≥ T" (T from
PONK / Katka — **K5**); report flag agreement with gold. This is the metric closest to what a
deployed linter does.

**Stability:** across the 3 runs — exact-set match of the full pair list; per-pair distance spread.

**Cost & complexity:** real USD per 1k sentences per pipeline; latency; for A, implementation
complexity (LOC / rules / documented edge cases) as the maintainability datum.

**Breakdowns:** by clause count, length bucket, distance bucket, sub-corpus, and phenomenon flags
(copular, pro-drop present, non-SVO, coordination, fragment) — phenomenon flags derived from
silver, verified on gold subset.

## 9. Hypotheses (falsifiable, pre-registered here)

- **H1 (identification degrades with structure):** pair F1 drops with clause count and on
  pro-drop-containing sentences; the dominant new error class is hallucinated subjects in pro-drop
  clauses and missed pairs in embedded/coordinated clauses.
- **H2 (externalized counting works):** with numbered-word input (C1/C2), distance accuracy *on
  correctly identified pairs* is ≥ 95% even for the ~8B model — i.e. the counting bottleneck is
  eliminated by preprocessing, not by scale. (Exp_01 predicts this: naming was never the main
  failure; positioning and arithmetic were, and both are externalized.)
- **H3 (reasoning helps counting, at a price):** frontier reasoning-on substantially improves
  end-to-end distance accuracy over reasoning-off (probes P1/P2 localize where), but at a large
  cost multiple and without reaching pipeline A's stability.
- **H4 (pipeline ranking):** on human gold, A ≥ C2 > C1 ≫ B-non-reasoning for exact distance;
  C2 lands within ~5 pts of A while replacing A's hand-coded tree rules with a prompt. (If instead
  A clearly dominates C2 even on unfiltered text, that *is* the paper's answer: keep the linter
  deterministic.)

## 10. Relationship to the joint paper

- RQ1 → pays off Katka's free-word-order section (per-phenomenon identification results).
- RQ2 → the "can LLMs count" arc continued to frontier/reasoning scale; probes give the mechanism.
- RQ3 → the abstract's "how traditional NLP tools and LLMs can be used together", answered with a
  decision matrix (accuracy × stability × cost × maintainability) instead of a vague hybrid claim.
- Gold data (KUK-200 + CLTT-derived pairs + IAA) → the draft's "Golden Truth Data" experiment item
  and a citable data contribution.

## 11. Budget and scale (order of magnitude)

~640 × (B: 3–4 model-modes × 3 runs) + ~640 × (C: 3 models × 2 variants × 3 runs) + probes
(~200 × ~6 model-modes × 3 probes) ≈ **~15k generations** (vs. 23k in exp_01). Cost dominated by
frontier + reasoning tokens: estimate **$150–500** (exp_01 open-model baseline was $7.73; frontier
per-token prices are 20–100×, reasoning inflates output tokens further). Real cost captured from
`usage`; not a hard constraint per Tomáš.

## 12. Open questions

For **Katka** (blocking §3 sign-off; worked examples will be prepared for each):
- **K1:** multiple auxiliaries (*by byl rozhodl*) — leftmost finite AUX as the measured predicate?
- **K2:** conditional — is *by* (3rd person, no person agreement) the right target, or the
  l-participle?
- **K3:** coordinated subjects (*ministr a náměstek*) — first conjunct (UD head) as the subject
  word?
- **K4:** clausal subjects (`csubj`) — exclude from pairs (report counts only)?
- **K5:** what distance threshold T does PONK / the comprehensibility literature suggest for the
  rule-verdict metric (§8)?

For **Tomáš**:
- **T1:** budget ceiling for the frontier roster (pick 2 vs. 3 frontier models)?
- **T2:** which frontier models exactly (availability + API knobs to be verified at run time)?
- **T3:** sub-corpora balanced 160×4 (continuity) vs. population-proportional — keep balanced?
- **T4:** second annotator for the IAA subset — Bára?

## 13. Out of scope (explicitly)

Surprisal/DLT-style comprehensibility metrics (next paper); sentence-segmentation study (upstream,
own paper — segmentation is held fixed and its caveat reported); LLM-repairs-UDPipe experiments;
fine-tuning Czech legal models; prompt-engineering sweeps beyond the C1/C2 contrast;
**tool-use / code-interpreter pipelines** (model executing real code via function calling): a
different architecture class, and for this task strictly dominated by pre-numbering + code
post-processing — the only computation left after identification is one subtraction. (Asking the
model to *simulate* code/regex execution in-prompt is not execution and is excluded by the §5
design principle.)
