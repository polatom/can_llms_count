# Methodology — Can LLMs Reliably Count? (Subject–Predicate Distance in Czech Legal Text)

Status: **draft v3 — design locked pending supervisor review; full dataset extracted &
checksum-manifested (all 4 KUK sub-corpora + metadata); no code written yet**

v3 changes (post-review): predicate operationalized as head-of-subject (§2, *provisional — to
confirm with linguists*); distance unit fixed to whitespace-words as the single canonical target
across all regimes (§2, §6); OpenRouter provider/quantization pinning added (§5); CLTT QC to use the
existing `cs_cltt` UD gold instead of hand-converting PML (§3); regime-2 to report both its CoNLL-U
and its own distance so parse-error vs count-error can be decomposed (§5, §6); stale "single model
per class" threat corrected (§8); corpus file/sentence counts corrected (§4).

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

Given sentence `S = w1...wn`, let `p` = index of the main-clause subject and `q` = index of the
predicate. Distance:

```
d = |p − q| − 1
```

(count of tokens strictly between them, linear surface order — not tree depth). This is a
deliberately narrow, objectively scoreable proxy for the broader class of SPRINT "counting" rules
(§ 39 odst. 2 paragraph limits, future cognitive-complexity metrics based on reference nesting).

**Operationalizing subject and predicate (provisional — to be confirmed with linguist colleagues).**
- **Subject** = the `nsubj` dependent of the sentence root; `p` is its token index.
- **Predicate** = the **head token of that subject** (`q = head(p)`), *whatever its part of speech*.
  This is chosen deliberately: it is exactly the head–dependent pair the dependency-distance
  literature (§7.5, Gao & He 2024) measures, it is fully deterministic (read the `nsubj` row, follow
  its `HEAD`), and it handles **copular/nominal predicates for free** — in UD, "Petr *je* učitel"
  attaches `nsubj(Petr → učitel)` with `je` as a `cop` child of the nominal root `učitel`, so
  head-of-subject = `učitel`, i.e. the Czech *jmenná část přísudku*. We additionally **log the
  copula token index** as a secondary field so the alternative (measure-to-copula) can be checked
  post hoc without re-running.
- **`csubj` (clausal subject): excluded from the primary set, count logged.** A clausal subject has
  no single well-defined position (which of its tokens is `p`?); reporting these separately is
  cleaner than inventing a convention.

**Distance unit — whitespace-words, canonical across all three regimes.** A "token" for the metric
is a whitespace-delimited run of characters (word), **not** a CoNLL-U/UD token. Rationale: (a) it is
the human- and SPRINT-meaningful unit; (b) it is the only unit a model can be asked to count on
*raw text* (regime 1) without being handed a tokenization standard it can't see — measuring against
UD-token distance there would score tokenization-convention mismatch as "counting error." The silver
gold (`p`, `q`, `d`) is therefore **recomputed in whitespace-word units** by mapping each UD token
to its containing word via the CoNLL-U `TokenRange` character offsets (a concrete `extract_pairs.py`
subtask; note UD splits punctuation into its own tokens, so UD-token distance ≠ word distance).
**All three regimes are scored against this same word-distance gold** — in regimes 2/3 the CoNLL-U
is a reasoning aid, but the question asked is always "how many words lie strictly between subject and
predicate," so H1 compares like against like rather than across different targets.

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
- We should still use an **existing manual gold legal treebank** as a **parser-quality control** —
  this doesn't require new annotation. This gives us an independent estimate of "how much should we
  trust UDPipe's nsubj identification and distance computation on legal-register Czech" and lets us
  put an error bar / caveat on the whole silver-only benchmark rather than presenting it as
  unqualified truth. **Preferred gold source: the existing `cs_cltt` UD treebank** (Universal
  Dependencies), which is already CoNLL-U — so gold `nsubj`/head/distance extract with the *same*
  code as KUK, and we avoid hand-converting CLTT 2.0's PML via `udapi` (which would add its own
  PDT→UD mapping noise onto the very noise-floor estimate we're trying to make). **To verify before
  relying on it**: that `cs_cltt` derives from CLTT 2.0's sentences and hasn't materially diverged;
  if it has, fall back to the PML→`udapi` route. (The Grok literature review conflated CLTT 2.0 with
  `cs_cltt` — they are related but not identical resources.)
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
- **KUK 1.0**: CC BY-NC-SA 4.0 license. **6,275 `.conllu` files, ~910,000 sentences** total across
  all four sub-corpora (ESO 5,615 files / FrBo 319 / KUKY 224 / OmbuFlyers 117). *(Full archive
  re-extracted and verified against the zip on 2026-07-01 — an earlier partial extraction had only
  3 of 4 sub-corpora, no `metadata/`, and ~3,244 files / ~450k sentences; the sampling design in this
  section depends on all four being present, so this is now fixed. See `data/CHECKSUMS.md`.)* Parses
  confirmed genuine UD-standard CoNLL-U (UDPipe 2,
  `czech-pdt-ud-2.15` model, plus NameTag 3 NE tags), with proper `nsubj`/`root` dependency labels
  — directly usable for extraction without conversion. Already visible in spot-checked files:
  realistic legal-text messiness (sentence-boundary detection errors on case-number headers,
  hyphenation artifacts) — useful motivating evidence for the paper's premise.
- **CLTT 2.0** (the LINDAT download): **not CoNLL-U** — it's PML (Prague Markup Language, PDT-style,
  separate w/m/a/t layers), with additional `treex` (Treex format) and `json` exports (286 files, of
  which 51 `.w`/`.m`/`.a` layer files + 17 `.treex.gz`), much smaller as expected for a manually
  annotated gold resource. **For the Phase 2 parser-QC step we prefer the existing `cs_cltt` UD
  treebank** (already CoNLL-U — see §3), which sidesteps a PML conversion entirely; converting this
  PML download via `udapi`/`.treex.gz` is the fallback only if `cs_cltt` turns out not to match CLTT
  2.0's sentences.

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
- **Pin the OpenRouter provider and quantization, not just the model slug.** A slug (e.g.
  `meta-llama/llama-3.1-70b-instruct`) is served by multiple upstream providers at different
  quantizations (fp16/fp8/int4); left unpinned, OpenRouter routes per call by price/latency, which
  (a) confounds the `run`-consistency metric (variance may be provider-switching, not model
  non-determinism), (b) breaks reproducibility, and (c) muddies H2 (an fp8 "large" model is a
  different artifact than fp16). Send an explicit `provider` list with `allow_fallbacks: false` and
  a quantization constraint, and **record the actual provider + quantization returned for every
  call**.
- **Regime 2 output spec**: the model returns **both** its self-generated CoNLL-U **and** its own
  word-distance answer. We score its reported distance *and* deterministically recompute distance
  from its emitted CoNLL-U — the two together decompose regime-2 error into *parse error* vs
  *counting-given-own-parse error* (see §6). Requires a **tolerant CoNLL-U parser**, since malformed
  output is a tracked failure mode (§6).

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
- **Regime-2 error decomposition**: compare the model's *reported* distance against distance
  *recomputed deterministically from its own emitted CoNLL-U*. Agreement isolates "counting given
  own parse"; the recomputed-vs-silver gap isolates "parse quality." This separates whether regime-2
  failures come from bad self-parsing or from bad counting over a correct parse — directly informative
  for the SPRINT hybrid recommendation.
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
- **Limited models per size class** — we use ≥2 models per class (§5), which guards against
  single-vendor quirks, but "small" and "large" are still each represented by a handful of specific
  models. Claims generalize to *the models tested*, not to "all small/large models" in the abstract;
  state this rather than overclaim. Provider/quantization is pinned and logged (§5) so a given
  `model_id` is a fixed artifact.
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
6. **CLTT QC gold**: use the existing `cs_cltt` UD treebank (already CoNLL-U) as the parser-QC gold
   rather than hand-converting CLTT 2.0's PML via `udapi` — pending a quick check that `cs_cltt`
   derives from CLTT 2.0 and hasn't diverged; `udapi`/PML is the fallback only if it has (§3).

Data is downloaded, checksum-verified, and extracted locally
(`experiment_01/data/raw/KUK_1.0/`, `experiment_01/data/raw/cltt_2.0/`). Design is ready for the
supervisor discussion; next engineering step after that is `extract_pairs.py`.
