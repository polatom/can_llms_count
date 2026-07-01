# Methodology — Can LLMs Reliably Count? (Subject–Predicate Distance in Czech Legal Text)

Status: **draft v2 — design locked pending supervisor review; data downloaded and locally
inspected; no code written yet**

This document specifies the *science*: hypotheses, formal task definition, experimental design,
sampling, statistical analysis plan, and validity threats. It intentionally does **not** cover
engineering/pipeline mechanics (see `IMPLEMENTATION_PLAN.md` for that) — this is the document to
argue with before we write code.

Decisions already made (per discussion):
- **Model access**: OpenRouter API key available → both small and large models sourced there.
- **Standard for this iteration**: **silver-only** (UDPipe parses on KUK), no new human gold
  annotation yet. Linguist-experts are available on-demand for small-scale spot checks *if/when
  results warrant it* (see §7).
- **Scale**: full-scale run (not a token pilot) — dataset is small enough that cost/time isn't a
  blocker, and a small-N pilot wouldn't be convincing on its own.
- **Timeline**: NLLP deadline ~1 month out; target getting a first full run + draft analysis done
  before Friday's supervisor meeting.

---

## 1. Research questions and hypotheses

**RQ1 (role identification).** Can LLMs correctly identify the main-clause subject (podmět) and
predicate (přísudek) of a Czech legal sentence, relative to UDPipe's silver parse?

**RQ2 (counting).** Given correct (or given) role identification, can LLMs correctly compute the
exact linear token distance between them?

**RQ3 (structure helps).** Does supplying explicit syntactic structure (CoNLL-U) — either
self-generated or given — improve performance over raw text, and does the effect size differ by
model size?

Formal hypotheses, to be tested per §6:

- **H1 (regime effect)**: Distance-accuracy(regime 3: gold/silver CoNLL-U given) >
  Distance-accuracy(regime 2: self-generated CoNLL-U) > Distance-accuracy(regime 1: raw text).
- **H2 (model-size effect)**: Large models > small models on both role-F1 and distance accuracy,
  in every regime.
- **H3 (interaction / "structure compensates for size")**: The gap between small and large models
  shrinks in regime 3 relative to regime 1 — i.e., structured input helps small models
  disproportionately more. This is the hypothesis with the most direct payoff for SPRINT: if true,
  it justifies "give the LLM structured context" as a cheap mitigation; if false (small models stay
  bad even with CoNLL-U), it justifies "never trust an LLM with counting, use a deterministic
  extractor" more strongly.
- **H4 (length/depth effect)**: Accuracy (all regimes) degrades with sentence length and with
  syntactic embedding depth (number of intervening clause boundaries) — legal Czech's long,
  nominalized, multiply-embedded sentences are the adversarial case, not an incidental one.

**What would falsify/weaken the "LLMs can't count" narrative**: if regime-1 (raw text) accuracy is
already high (say >90% exact-distance match) and doesn't degrade with length — that would suggest
the task is too easy / not a good probe, and we'd need a harder task or longer sentences.

---

## 2. Task formalization

Given sentence `S = w1...wn`, let `p` = token index of the main-clause subject (`nsubj`/`csubj`
dependent of the root or main verbal head) and `q` = token index of the predicate (the verbal head
`p` depends on, or root in copular constructions). Distance:

```
d = |p − q| − 1
```

(count of tokens strictly between them, linear surface order — not tree depth). This is a
deliberately narrow, objectively scoreable proxy for the broader class of SPRINT "counting" rules
(§ 39 odst. 2 paragraph limits, future cognitive-complexity metrics based on reference nesting).

**Why subject–predicate distance, specifically (not an arbitrary choice of metric)**: dependency
distance is an established syntactic-complexity / working-memory-load marker in the
psycholinguistics literature — longer linear distance between syntactically dependent words
increases cognitive cost because the head must be held in memory until its dependent appears (see
Gao & He 2024, §7.5). Subject–predicate distance is the single most load-bearing instance of this
in a sentence: it is the backbone dependency almost every finite clause has. This gives the task a
direct, citable link to comprehensibility, not just an ad hoc "let's count tokens" framing.

**Important framing point**: this is a proxy task, not the SPRINT rule itself. We should be
explicit in the paper about what generalization claim we're making — success/failure here
predicts, but does not prove, LLM (un)reliability on *other* counting rules (paragraph counts,
reference depth, etc.). This is a limitation to state, not hide.

---

## 3. What "silver-only" means here, precisely

Since we are not doing new human gold annotation for `experiment_01`, **UDPipe's own parse is
being treated as ground truth** for both role identification and distance. This has one important
scientific consequence worth foregrounding rather than burying:

> We are measuring **agreement with UDPipe**, not agreement with linguistic truth. A model that
> makes an error in the exact same place UDPipe does would score as "correct"; conversely a model
> that is linguistically right where UDPipe is wrong would score as "wrong."

This is an acceptable and common simplification for silver-standard benchmarks, **but**:
- We should still run UDPipe against **CLTT 2.0** (existing manual gold treebank) as a
  **parser-quality control** — this doesn't require new annotation, CLTT is already
  human-annotated. This gives us an independent estimate of "how much should we trust UDPipe's
  nsubj identification and distance computation on legal-register Czech" and lets us put an error
  bar / caveat on the whole silver-only benchmark rather than presenting it as unqualified truth.
- This CLTT-based noise-floor estimate is **in scope now** (it's not new annotation, just running
  UDPipe against an existing resource) — recommend keeping it in Phase 0/1 even though we're
  deferring new human annotation of KUK.
- New human annotation of a KUK subsample is deferred to a trigger-based fast-follow (§7), not
  dropped from the plan.

---

## 4. Datasets

| Dataset | Role | Status |
|---|---|---|
| KUK 1.0 | Source of eval sentences + silver CoNLL-U (UDPipe parses) | **Downloaded & verified** (`experiment_01/data/raw/KUK_1.0/`) |
| CLTT 2.0 | Independent manual gold treebank — **parser quality control only**, not a source of eval sentences for the main LLM benchmark | **Downloaded & verified** (`experiment_01/data/raw/cltt_2.0/`) |

**Corrected understanding vs. original notes** (`chat.md` referred to "Kuk 1 vs 2" as if there
were two versions of KUK to compare raw-vs-annotated — this was a misreading):

- The two LINDAT links in the notes actually point to **two different datasets**, not two KUK
  versions: one is **CLTT 2.0**, the other is **KUK 1.0**. There is no "KUK 2.0."
- **KUK 1.0 itself already contains both raw and annotated text** — each of its 4 sub-corpora
  (FrBo, ESO, OmbuFlyers, KUKY) has parallel `TXT/` (raw) and `UD/` (UDPipe CoNLL-U) subdirectories.
  So the raw-vs-structured comparison our prompting regimes need is available *within* KUK 1.0.
- **KUK 0.0** (predecessor, checked for comparison) is a strict subset of KUK 1.0: same 3 of the 4
  sources (no KUKY), **no UD/CoNLL-U annotation, no NameTag NER** — just raw TXT. It adds nothing
  KUK 1.0 doesn't already have; not needed for this project.
- **KUKY 1.0** exists as a separate LINDAT item, but KUK 1.0's README confirms its texts are
  already folded into KUK 1.0's `KUKY/` subdirectory — no separate download needed.

**Verified corpus facts (from local inspection):**
- **KUK 1.0**: CC BY-NC-SA 4.0 license. ~10,000 `.conllu` files, **~450,000 sentences** total
  across FrBo/ESO/OmbuFlyers/KUKY. Parses confirmed genuine UD-standard CoNLL-U (UDPipe 2,
  `czech-pdt-ud-2.15` model, plus NameTag 3 NE tags), with proper `nsubj`/`root` dependency labels
  — directly usable for extraction without conversion. Already visible in spot-checked files:
  realistic legal-text messiness (sentence-boundary detection errors on case-number headers,
  hyphenation artifacts) — useful motivating evidence for the paper's premise.
- **CLTT 2.0**: **not CoNLL-U** — it's PML (Prague Markup Language, PDT-style, separate w/m/a/t
  layers), with additional `treex` (Treex format) and `json` exports. Only ~17–18 documents (much
  smaller, as expected for a manually annotated gold resource). **This means Phase 2 (UDPipe vs.
  CLTT parser-quality control) requires a conversion/reading step** (e.g. via `udapi`, which reads
  PML natively, or the `.treex.gz` files) before we can compute comparable nsubj-F1/distance
  agreement — a small added engineering task, not a blocker, but worth planning for explicitly
  rather than assuming CLTT is already CoNLL-U.

**Sentence filtering criteria** (deterministic, applied to KUK's silver parses — since we have no
gold yet, filtering must be self-consistent from UDPipe's own output):
- Exactly one root-attached (or copula-headed) finite clause with exactly one `nsubj`/`csubj`
  dependent — i.e., no subject coordination (`conj` on the nsubj), no multiple finite verbs
  (`parataxis`/multiple roots), no relative-clause subject being mistaken for main-clause subject.
- Sentence length bounds: exclude degenerate very-short sentences (< ~5 tokens, distance is
  trivially small) and excessively long outliers (e.g. > ~80 tokens) that may be OCR/formatting
  artifacts rather than genuine legal sentences — bounds to be set empirically after inspecting
  the length distribution.
- Sentences that fail the filter are **not** discarded silently — log counts and reasons; report
  what fraction of KUK legal sentences even qualify for this narrow task (this is itself an
  interesting descriptive statistic: how common are "simple" subject–predicate structures in legal
  Czech vs. coordinated/multi-clause ones).

**Stratification for sampling** (full-scale eval set): stratify by (a) sentence length bucket and
(b) syntactic embedding depth (number of clausal boundaries between S and predicate, or maximum
dependency-tree depth) — both are the mechanisms hypothesized (H4) to drive difficulty. Sample
proportionally or with oversampling of long/deep sentences to ensure enough statistical power in
exactly the regime we expect failures to concentrate.

**Sampling scope — decided: pool across all of KUK 1.0, not a single sub-corpus.** Draw the
stratified (length × depth) sample from the combined pool of all 4 sub-corpora (FrBo, ESO,
OmbuFlyers, KUKY) rather than restricting to one (e.g. ESO alone). Rationale:
- Restricting to a single sub-corpus would confound length/depth effects with that sub-corpus's
  specific register — e.g. ESO is ombudsman quasi-judicial opinions, OmbuFlyers `redesigns/` are
  *already* plain-language-simplified by design, FrBo `analyses/` is dense legal-expert register.
  A claim about "Czech legal text" should not implicitly become a claim about one narrow genre.
  This directly supports a broader, more defensible claim in the paper.
- KUK's own metadata already flags `ClarityPursuit` (written with special care for plain language)
  and source corpus per document — log both as **covariates/descriptive stats**, not as a full
  stratification axis (crossing them with length × depth would explode the number of strata for
  limited benefit). If a clear source or ClarityPursuit effect shows up post hoc, report it
  descriptively; it is not one of H1–H4 and shouldn't be over-engineered into the primary design.

Target N: to be finalized after inspecting real length/depth distribution in KUK (Phase 0/1 of
implementation plan), but given "full-scale, not a token pilot," we should aim for enough sentences
per stratum × condition to support the statistical model in §6 (rule of thumb: ≥30–50 sentences per
length/depth stratum, likely landing in the 300–600 total sentence range depending on how many
strata we define — to be revisited once we see the data, and traded off against the cost increase
from using ≥2 models per size class, see §5).

---

## 5. Experimental design

**Factors** (fully crossed, within-sentence — i.e. every sentence gets every condition):
- `regime` ∈ {raw_text, raw_to_conllu, conllu_given} (3 levels)
- `model_size` ∈ {small, large} — **decided: ≥2 distinct models per size class** (not just one),
  to make the size-effect claim (H2) more convincing and not an artifact of one vendor's quirks.
  `model_id` becomes a nested factor within `model_size` (e.g. 2 small + 2 large = 4 `model_id`
  values total). Actual OpenRouter model IDs TBD pending budget/availability check.
- `run` ∈ {1, 2, 3} — repeated at temperature 0 to measure **prompt/decoding non-determinism**
  (should be ~0 variance; any non-trivial variance is itself a finding worth reporting)

This gives 3 regimes × 4 `model_id` × 3 runs = **36 generations per sentence** (up from 18 with a
single model per class) — a **2× cost increase**, driven entirely by adding a second model per
size class. Cost mitigation options, to decide once real per-token OpenRouter pricing for the
chosen models is known:
- Keep N (sentence count) as the primary lever to cut if budget is tight, rather than dropping back
  to 1 model per size class or dropping the `run` replication (both of those cut directly into what
  we just decided is worth keeping for a stronger paper).
- If still over budget, consider reducing `run` from 3 to 2 for the secondary model per size class
  only (keep the primary/reference model at 3 runs) — asymmetric, but only affects the consistency
  metric (§6), not the core role/distance metrics that use all runs pooled per condition.
- All prompts in Czech, temperature 0, identical 2–3 few-shot legal examples across
  regimes/models/model_ids for comparability.

**Why within-sentence (paired) design**: lets us use paired statistical tests (e.g. McNemar for
role-F1 binary correctness, paired comparisons for distance error) with much higher power than an
unpaired between-groups design, and controls for sentence-level difficulty as a nuisance variable
directly rather than only through stratification.

---

## 6. Metrics and analysis plan

**Per-generation metrics:**
- Role identification: exact match (surface form + token index) on subject and predicate
  separately, plus a joint "both correct" indicator.
- Distance: signed error (`predicted − silver`), exact match, ±1/±2 tolerance match, and squared
  error (for MAE/RMSE).
- Format validity: did the model even produce a parseable answer (missing/malformed output is a
  failure mode worth tracking separately from "wrong answer").

**Aggregate analysis:**
- Primary model: **mixed-effects regression** — outcome (distance exact-match, or distance error)
  ~ regime × model_size + sentence_length + embedding_depth + (1 | sentence_id) + (1 | model_id).
  The `model_id` random effect accounts for the ≥2 models nested within each `model_size` (§5),
  so between-model variance within a size class is modeled rather than ignored. This directly
  tests H1–H4 while accounting for repeated measures per sentence and controlling for the
  confounds we've named up front rather than discovering them post hoc.
- Consistency: within (sentence × regime × model) triplet of 3 runs, report % with zero variance
  and mean stddev — a secondary, simpler descriptive statistic alongside the regression.
- Error taxonomy (qualitative, on a sample of failures): wrong clause attachment, off-by-one,
  multi-word-term tokenization mismatch, hallucinated/malformed CoNLL-U, other.
- Report effect sizes (not just p-values) given this is a short paper aimed at an actionable
  engineering conclusion for SPRINT, not a pure significance-testing exercise.

**Multiple comparisons**: since we're testing several related hypotheses (H1–H4) on the same
dataset, note this in the paper and prefer the single mixed-effects model (which tests everything
jointly) over a battery of separate pairwise tests where possible.

---

## 7. Deferred human validation — trigger conditions

We are not annotating new gold data now, but the plan should specify **when we would**, so it's
not an open-ended "maybe later":

- Trigger A: if UDPipe-vs-CLTT parser quality (nsubj-F1, distance agreement) on legal-register
  sentences comes back materially worse than in-domain UDPipe benchmarks (e.g. large drop vs.
  UDPipe's reported general-Czech accuracy) — this would mean silver-only results are too noisy to
  trust, and we'd need a KUK gold subsample before submission.
- Trigger B: if the LLM-vs-silver disagreement cases (once we run the harness) look like they're
  concentrated in a specific ambiguous construction — a small-scale human annotation of that
  sample may resolve whether the model or UDPipe is "right." Flag those for a linguist-expert spot
  check rather than resolving by our own judgment call.
- Trigger C: reviewer/supervisor request at the Friday meeting or later — if the silver-only
  framing isn't convincing, we already know who to ask (linguist-experts on standby) and roughly
  how much annotation (~100 sentences, 2 annotators, κ) it would take, per the original draft.

---

## 7.5 Related work (fact-checked; for citation in the paper's motivation/related-work sections)

Reviewed via Grok, then independently verified (titles/authors/venues confirmed by direct lookup)
before trusting for citation — LLM literature-review output is prone to fabricated or
slightly-wrong citations, so treat this as the vetted subset only:

- **LLM counting/tokenization fragility** (motivates the proxy-task framing and H4):
  - Zhang, Cao & You (2024), "Counting Ability of Large Language Models and Impact of
    Tokenization," arXiv:2410.19730 — tokenization choice alone causes up to 80% accuracy swings
    on counting tasks; directly relevant given KUK's OCR/hyphenation artifacts we've already seen.
  - Fu, Ferrando, Conde, Arriaga & Reviriego (2024), "Why Do Large Language Models (LLMs) Struggle
    to Count Letters?", arXiv:2412.18626.
  - Dai & Fan, "Language models fail at extended rule following," arXiv:2605.02028 — **unreviewed
    preprint (2026)**, cite with that caveat; introduces "stable counting capacity" as a minimal
    probe of rule-following reliability, close in spirit to our own framing in §2.
- **Structured input helping LLM parsing** (motivates regimes 2 vs. 3 / H1, H3):
  - Ginn & Palmer (2025), "LLM Dependency Parsing with In-Context Rules," ACL Anthology
    `2025.xllm-1.17` (XLLM Workshop @ ACL 2025) — symbolic/rule context improves zero-shot
    dependency parsing, benefit shrinks with more few-shot examples. (Note: cite by this exact
    title — an earlier internal draft title, "...with Symbolic Rules," is not what was published.)
- **Dependency distance as an established complexity/cognitive-load metric** (grounds our distance
  metric as more than an ad hoc choice, ties to SPRINT's future cognitive-complexity rules):
  - Gao & He (2024), "A dependency distance approach to the syntactic complexity variation in the
    connected speech of Alzheimer's disease," *Humanities and Social Sciences Communications*
    11:995, DOI `10.1057/s41599-024-03509-0`.
- **CLTT provenance** (for citing the treebank itself in §4):
  - Kríž & Hladká (2018), "Czech Legal Text Treebank 2.0," LREC 2018.

**Not included**: an OpenReview link Grok surfaced for "Can Large Language Models Help with Model
Counting?" could not be verified (page required bot-check bypass) — do not cite until manually
confirmed as an accepted, non-withdrawn paper.

---

## 8. Threats to validity (to state explicitly in the paper)

- **Silver-as-truth circularity** (§3) — mitigated by CLTT-based noise-floor estimate, explicitly
  flagged as a limitation, deferred human validation available on trigger.
- **Single model per size class** — a specific model's quirks may not generalize to "all small
  models" / "all large models." We should name this explicitly rather than overclaim; if budget
  allows a second model per class late in the process, that would strengthen the size-effect
  claim, but it's not required for a valid narrow claim about the two models actually tested.
- **Filtering criteria depend on UDPipe itself** — sentences UDPipe parses "cleanly enough" to pass
  our filter may be a biased (easier) subset; report the exclusion rate and reasons transparently.
- **Proxy-task generalization** — success/failure on subject–predicate distance doesn't
  automatically transfer to other SPRINT counting rules (paragraph counts, reference depth); state
  this as a scope limitation, not a proven general claim about "LLMs and counting" writ large.
- **Prompt sensitivity** — results are for one prompt formulation per regime; we are not doing
  prompt-engineering sweeps. Worth a one-line caveat.

---

## 9. Review pass — resolved (design locked for supervisor discussion)

All open items from the previous pass are now resolved:

1. **H1–H4 and silver framing**: confirmed as-is, no change in emphasis.
2. **Stratification variables**: length + embedding depth confirmed, no better/simpler proxy
   identified.
3. **Models per size class**: **≥2 per class**, not 1 — see §5 for the resulting design change
   (36 generations/sentence, up from 18) and the cost-mitigation options logged there. Repeated
   runs for consistency (already in the design as the `run` factor) confirmed as worth keeping.
4. **Sampling scope**: pool across all 4 KUK sub-corpora (not a single one like ESO) — see §4 for
   rationale. Source corpus and `ClarityPursuit` logged as covariates/descriptive stats, not a
   full stratification axis.
5. **Comprehensibility linkage**: added directly in §2 (subject–predicate distance as an instance
   of the established dependency-distance/working-memory-load literature, citing Gao & He 2024 from
   §7.5) — no separate SPRINT-rule citations needed beyond what's already in §2/§7.5.
6. **CLTT PML conversion**: no existing UFAL-internal tool identified — proceed with `udapi`.

Data is downloaded, checksum-verified, and extracted locally
(`experiment_01/data/raw/KUK_1.0/`, `experiment_01/data/raw/cltt_2.0/`). Design is ready for the
supervisor discussion; next engineering step after that is `extract_pairs.py`.
