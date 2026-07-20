# Experiment 02 — Methodology (v3.1)

Status: **v3.1 — converged design; §3 task definition reviewed and signed off by Katka
(2026-07-16, except K6 provisional per §3.3); open items in §11.** Self-contained; experiment_01
is cited for motivation only, no artifacts reused. Prior drafts in git history: v1 `b165f70`,
v2 `0d6834c`. Deliberately simplified for a short paper: one question, one figure.

---

## 1. Goal and context

**Research question in one sentence:** *Can a pure-LLM rule — raw sentence in, verdict out, no
pre- or post-processing — measure subject–predicate distance in unfiltered Czech legal text well
enough to replace a deterministic parser pipeline, and how much model capability and how good a
rule formulation does it take?*

**The two experimental axes:**
- **Model capability** (ordered axis): open ~30B → open ~70B → frontier → frontier with
  reasoning. "How low can we go?"
- **Rule formulation** (categorical axis): the production-style prose rule vs. a procedural
  rewrite of the same rule. Two points now; the formulation space (other definitions, other
  scaffolds) is future work — explored further only if the procedural formulation wins (§12).

**Practical motivation (SPRINT).** SPRINT rules are prose prompts written by lawyers; the app
sends each sentence plus the rule prompt to an LLM and parses `{has_violation, reason,
suggestion}` from the reply. The production distance rule (obtained: §5.2 R1) does not work well —
the finding that motivated this work. The alternative — UDPipe plus a hand-coded extractor — is
accurate but is *per-rule engineering*: code written and maintained per rule, only for phenomena a
parser exposes. A pure-LLM rule is *per-rule prose*: deployable in today's SPRINT by editing rule
text. The economics favor the LLM path wherever it is good enough; this experiment measures
whether and when it is.

**Scientific motivation (exp_01 sequel).** Experiment_01 showed on filtered (single-main-clause)
legal Czech that the LLM bottleneck is *counting*, not role identification — large open models
name the right words but miscount the span ~28–36% of the time even when handed the parse, and
the instability cannot be tuned away. Two things exp_01 could not answer: (a) do
frontier/reasoning models close the counting gap end-to-end? (b) does scaffolded prompting
(explicit enumeration with a counter — the scratchpad/CoT-counting mechanism,
`docs/RELATED_WORK.md` Thread A) close it at open-model sizes? Both are answered here, on harder
(unfiltered) data and against human gold.

## 2. Research questions and hypotheses

- **RQ1 (parity):** Does the best pure-LLM configuration reach the parser baseline at the verdict
  level on unfiltered legal Czech?
  **H1:** the frontier model with reasoning comes within ~5 pts of the parser baseline's verdict
  accuracy. (Genuinely open: the parser baseline's own accuracy on unfiltered text is unknown —
  §5.1 measures it.)
- **RQ2 (capability floor):** How does verdict accuracy scale down the capability axis — what is
  the least capable model that remains viable?
  **H2:** accuracy degrades monotonically down the axis; ~30B is below viability under either
  formulation. (The ≤8B regime is omitted as settled — exp_01: ≤16% naming, ~0% counting.)
- **RQ3 (formulation effect):** How much does the procedural formulation buy at each capability
  level?
  **H3:** R2 beats R1 everywhere, and the gain *grows* with capability (echoing exp_01's H3:
  scaffolding does not rescue weak models).
- **RQ4 (mechanism, from scoring only):** Where do residual errors live?
  **H4:** for open models, errors concentrate in counting (right words, wrong distance); frontier
  reasoning shifts the residual to identification (wrong words, correctly counted).

## 3. Task definition

**Unit of evaluation: the sentence** as segmented by UDPipe (KUK) or by the gold treebank (CLTT).
Sentence segmentation of legal Czech is a known fallible upstream step (exp_01: UDPipe splits ~60%
of CLTT gold sentences differently); it is held fixed and inherited by all conditions equally.

**Output per sentence: the set of all subject–predicate pairs** of finite clauses with an overt
nominal subject — possibly empty (fragments, headings, verbless enumeration items) and possibly
plural (multi-clause sentences, coordination of clauses). For each pair: subject word, predicate
word, their 1-based word positions, the distance — plus the sentence-level verdict (§3.5).

### 3.1 Predicate (Katka's definition — operationalized in UD; reviewed 2026-07-16)

The predicate for measurement purposes is **the element that carries grammatical agreement with
the subject** — the verb in finite form, or the auxiliary verb in analytic verb forms and modal
constructions. Terminology (per Katka's review): **copular predicates** (přísudek jmenný se
sponou, *Petr je prezident*) and **verbo-nominal predicates** (light-verb constructions per
Radimský, *Petr vystavil fakturu*) are distinct types. For copular predicates we measure to **the
copula**, not the nominal part (note: this *reverses* exp_01's provisional rule); for
verbo-nominal predicates, to the finite (light) verb.

| clause type | example | measured predicate token |
|---|---|---|
| simple finite verb | *Soud **rozhodl** …* | the verb itself |
| verbo-nominal (light verb, Radimský) | *Petr **vystavil** fakturu* | the finite verb (*vystavil*) |
| analytic past, 1st/2nd person | *… rozhodl **jsem*** | the finite AUX (*jsem*) |
| analytic past, 3rd person (no aux) | *Soud **rozhodl** o …* | the l-participle itself |
| analytic future | *Soud **bude** rozhodovat* | the finite AUX (*bude*) |
| conditional | *Soud **by** rozhodl* | the conditional AUX (*by*) |
| past conditional (two aux) | *Byl **bys** šel do kina?* | the conditional AUX (*bys*) — **not** necessarily leftmost (K1) |
| passive | *Rozhodnutí **bylo** vydáno* | the finite AUX (*bylo*) |
| copular | *Petr **je** prezident* | the copula (*je*) |
| aby/kdyby clause (absorbed *by*) | *…, **aby** se Petr nemusel zouvat* | the conjunction word (*aby*) — it absorbs the conditional AUX and carries person agreement (*abych/abys/…*) |

**Mechanical rule: the measured predicate is the finite element of the predicate complex** — the
`aux`/`aux:pass`/`cop` child with `VerbForm=Fin` if the clause head has one, otherwise the clause
head itself (then a finite verb or bare l-participle). No positional heuristic: in
past-conditional forms only *by/bys* is finite (`byl` is `VerbForm=Part`), so the rule selects it
wherever it stands, including in questions. Rare double-aux forms without a conditional
(pluperfect *byl jsem přišel*, passive conditional *byl by vydán*) still contain exactly one
finite AUX; the extraction code asserts uniqueness and logs violations.

**aby/kdyby falls out for free:** in UD these conjunctions are multiword tokens — surface *aby* =
`aby` (SCONJ, `mark`) + `by` (AUX, `Mood=Cnd|VerbForm=Fin`, `aux` of the clause head); verified in
`cs_cltt` gold. The finite-element rule selects the `by` token and the §3.4 token→word mapping
assigns it the surface word *aby*/*kdyby* — implementing Katka's decision with no special case.

**Consequence note (metric semantics):** measuring to the agreement-bearing element means that
for conditionals and 1st/2nd-person past forms the target is a second-position clitic (*by,
jsem*), which sits early in the clause regardless of where the lexical verb is — systematically
shorter distances than a measure-to-the-content-verb rule. In legislative text this bites rarely
(legal Czech is overwhelmingly 3rd person, where past tense has no auxiliary), but the annotation
guidelines and the paper must state it.

### 3.2 Subject

The word bearing the `nsubj`/`nsubj:pass` relation to the clause head (head word of the subject
phrase; coordinated subjects → the first conjunct, i.e. the UD head — confirmed, K3).

### 3.3 Null cases and exclusions (inside sentences that are all kept)

- **Pro-drop clauses** (finite predicate, no overt subject): no pair for that clause. Systems
  must *not* hallucinate a subject — false positives are penalized via precision.
- **Clausal subjects** (`csubj`): excluded from pairs (no single word position to measure from —
  confirmed, K4); counted and reported.
- **Fragments / verbless headings:** gold = empty set; correctly returning "no pairs" is scored.
- **Shared-subject predicate coordination** (*Ministr návrh podepsal a odeslal* — one overt
  subject, two finite verbs): **one pair — distance to the first verb** (the mechanical UD
  default; only the first conjunct bears `nsubj`). *Provisional (K6): decided 2026-07-17 in
  Katka's absence; to be confirmed with her later.* **Insurance against a later reversal:**
  annotators additionally mark the further conjunct verbs (flagged, not scored), so *both*
  conventions are recomputable from the stored gold without re-annotation; headline numbers use
  the one-pair convention and a sensitivity check under the per-conjunct convention is reported.

### 3.4 Distance and word positions

`d = |pos(subject) − pos(predicate)| − 1`, in **whitespace-separated words** (1-based;
punctuation glued to a word belongs to it; multiword tokens like *aby* = one word).

Token→word mapping (for gold, from CoNLL-U): collapse multiword-token ranges into one surface
unit, then increment the word counter only after units not marked `SpaceAfter=No` (port of
exp_01's `assign_word_indices`, validated there with zero mismatches). Gold, scoring, and prompt
few-shots share this one coordinate system.

### 3.5 Verdict

Per sentence: **violation ⇔ any pair has d > T, with T = 6** — i.e. seven or more words between
subject and predicate. This matches both PONK ("limit distance 6" = 6 is the maximum allowed,
K5) and the production rule R1 ("separated by at least 7 words" / "more than 6 words").
(Note: v3 wrote `d ≥ 6`, an off-by-one against both sources — caught during the R1 review.)

### 3.6 Relation to UD/UDPipe (does our definition "match" the parser's?)

UDPipe does not define "subject" or "predicate" at the level of §3.1 — it produces Universal
Dependencies annotations (`nsubj`, `aux`, `cop`, `VerbForm`, …) per the **documented UD
guidelines** (universaldependencies.org; Czech-PDT conversion conventions). No reverse
engineering is needed: the labels' semantics are public. The interpretation layer — mapping UD
output to Katka's subject/predicate — is **ours alone**, and it lives in exactly one place: the
§3.1 extraction rule of the parser arm.

Crucially, **the human gold is definition-native and UD-free**: annotators mark pairs on the raw
(pre-numbered) text under Katka's definition, never seeing a parse tree. So there is no
"interpretation on both sides" — the gold side has none. The parser arm's measured error against
gold therefore *includes* any mismatch between the UD-based extraction rule and the linguistic
definition, alongside genuine parse errors; both are part of the honest baseline number (and the
error analysis separates them where possible: extraction-rule mismatches are systematic per
construction type, parse errors are not). Framed for the paper: both error sources are part of
the *real engineering cost of the deterministic path* — a deployed parser rule pays for its
UD-interpretation layer exactly as it pays for parse errors.

## 4. Data

**Source:** KUK 1.0 (four sub-corpora, UDPipe-parsed silver) + CLTT 2.0 / `cs_cltt` (human gold
trees). Fresh sample; nothing reused from exp_01.

### 4.1 Main eval set — random, unfiltered (N = 640, with an audit gate)

**Uniform random sample of sentences** from unfiltered KUK. No linguistic filtering and no
stratification (decision 2026-07-17: representativeness must be self-justifying; the verdict
metric needs realistic prevalence). Only technical exclusions, logged with counts:
exact-duplicate sentences after whitespace normalization (legal boilerplate), sentences > 200
words (context sanity; expected rare). Multi-clause monsters, fragments, headings all stay in.

**Audit gate (before any LLM run):** report per-phenomenon counts on the sample (clause counts,
copular, pro-drop, non-SVO candidates, fragments, near-threshold distances per silver) **and the
verdict prevalence** (share of sentences with d > 6 per silver): with low prevalence the
precision/recall CIs on the random gold-140 get wide (~15% prevalence → only ~20 positive items).
If phenomena or positives are too thin at N = 640, extend the *random* sample and/or the random
gold slice *then* (harness resumable; decision documented) — never stratify, never after results
are known. Sub-corpus, length, clause count etc. kept as metadata for post-hoc breakdowns.

### 4.2 Human gold (primary standard)

- **KUK-200 (new annotation):** 140 sentences sampled at random from the 640 (gold ⊂ eval set →
  parser-arm accuracy measured directly on eval items) + 60 **targeted** at rare phenomena
  (copular, pro-drop-heavy multi-clause, non-SVO, syncretic nominatives, fragments, aby-clauses).
  The targeted 60 are quarantined: per-phenomenon diagnosis only, never pooled into headline
  metrics. Annotation on pre-numbered word sheets under §3 (`ANNOTATION_GUIDELINES.md`, to
  draft); annotator: Katka.
- **IAA:** 50 of the 200 double-annotated. Second annotator: **Tomáš** (O3). A non-linguist
  second annotator is acceptable and even informative here: with a signed-off definition and
  written guidelines, linguist × trained-non-linguist agreement measures exactly what SPRINT
  needs — whether the rule's definition is executable by a careful reader, not only by its
  author. Annotator profiles reported; disagreements adjudicated by Katka later where feasible.
- **CLTT-derived gold (free):** the §3 rule applied mechanically to `cs_cltt` gold trees → gold
  pairs for ~1k unfiltered legal sentences at zero annotation cost; Katka reviews ~20 worked
  examples (one per §3.1 table row where attested). Domain caveat (accounting/tax law) reported.

### 4.3 Descriptive statistics — the metric family (one table, no LLM runs)

From the UDPipe parses of the 640: distribution of subject–predicate distance, plus the sibling
counting metrics a comprehensibility linter would use (max tree depth, subordinate-clause count,
coordination density, passive count per sentence). Purpose: (a) situates the distance rule in the
family of counting rules SPRINT needs; (b) documents how often the T = 6 rule fires on real
unfiltered text (prevalence matters for the verdict metric).

## 5. Conditions

Two arms, deliberately minimal.

### 5.1 Parser arm — deterministic baseline (no LLM)

UDPipe 2 (same model as KUK silver) → §3 extraction code → pairs, distances, verdict. Zero
variance, one run. **Its accuracy against gold-200 is itself an unknown this experiment
measures** — exp_01's 99.3% noise floor was computed on easy single-clause commits only;
unfiltered complex text will be lower, and the gold is definition-native (§3.6), so the number
also absorbs any UD-interpretation mismatch. This directly answers "how do we know the baseline
is right": we don't assume it — the KUK-200 gold exists precisely to measure it (CLTT-derived
gold adds free volume in an adjacent domain; a second-parser ensemble as a robustness upgrade is
exp_03 material). Implementation complexity (LOC, rules, documented edge cases) recorded as the
maintainability datum.

### 5.2 LLM arm — pure-LLM rule (prompt-only, SPRINT-compatible)

Raw sentence in the prompt; model returns JSON with the pair list **and** the verdict. No
preprocessing, no post-computation: the model's own `has_violation` is the scored verdict (SPRINT
deployment semantics). Code-side validation (schema, index bounds, form-at-index) is **recorded
as measurement, never corrected** — catch rates are a reported finding, since in SPRINT nothing
would catch them.

Two **rule formulations** per model (the categorical axis):

- **R1 — production rule (baseline formulation):** the real SPRINT rule
  `docs/sprint-rule-C4DHI_Predicate-Subject_Distance.json` (obtained 2026-07-17 — O1), **adapted
  to Czech**: the export's conditions/definition/instructions are in English with English (EU
  firearms directive) test sentences, so R1 is a faithful Czech translation that deliberately
  preserves the rule's level of (under)specification — no predicate/subject definition, no
  counting procedure, "interdependent" left vague. Known defects kept (they are the production
  reality being measured) except one repair: the garbled `teaching_examples` entry (two examples
  merged mid-sentence in the export) is replaced by its evident intended form, flagged to KMH.
- **R2 — procedural rule:** the same rule rewritten as an explicit procedure (the SPRINT `_mod`
  negation-rule pattern; literature grounding in `docs/RELATED_WORK.md`):
  1. list every finite clause; for each, identify the predicate token per §3.1 (definition +
     examples for each tricky type: copular, analytic, conditional, aby-clause);
  2. for each predicate, identify the overt subject if any (agreement, nominative; pro-drop →
     no pair);
  3. **enumerate the sentence word by word with a running counter** (`1: Zákon`, `2: je`, …) —
     the self-enumeration scratchpad;
  4. read off the two positions from the enumeration, subtract, compare with T = 6, output
     pairs + verdict.
  Few-shot examples cover: simple SVO, copular, conditional, aby/kdyby clause, pro-drop (no
  pair), multi-clause (two pairs), fragment (empty list), one long sentence with d > 6.

One fixed formulation each (no prompt sweeps); shared output schema:
`{"pairs": [{"podmet": str, "podmet_index": int, "prisudek": str, "prisudek_index": int,
"vzdalenost": int}], "has_violation": bool}`.
R1-vs-R2 varies definition *and* scaffold together, deliberately: R2 is "the best rule a lawyer
could write", not a factorized ablation (Ginn & Palmer 2025 suggest rules and examples interact;
see RELATED_WORK Thread B). The paper states this.

**Dropped by design** (v2→v3): any pre/post-processing around the LLM (pre-numbered input with
code-side arithmetic — its mechanistic question is answered by scoring decomposition instead,
§7); parse-hint prompts; the isolated counting-probe battery; validation-triggered retries.

## 6. Models and run protocol

| capability slot | candidates (verify on OpenRouter at run time — O2) | modes |
|---|---|---|
| frontier | one of: OpenAI GPT-5.x / Anthropic Claude Opus-Sonnet 4.x / Google Gemini 3 / xAI Grok 4 | reasoning **on** and **off** (same model — cleanest test-time-compute contrast) |
| open ~70B | Qwen-2.5-72B-Instruct (anchor, bridges exp_01) | standard |
| open ~30B | Qwen3-32B or Gemma-3-27B | standard |

= **4 model-modes × 2 formulations × 3 runs × 640 sentences = 15,360 generations.**
The ≤8B regime is deliberately omitted: exp_01 settled it (≤16% naming on raw text, ~0% exact
counting even given the parse), and unfiltered text is strictly harder; if the figure needs the
floor point, backfilling 8B later is cheap and the harness supports it.

Decoding: temperature 0 and pinned provider+quantization where the API allows; for the reasoning
mode, record actual sampling/effort parameters and treat run-to-run spread as a measured property.
Full prompt+response traces and real `usage.cost` captured (as exp_01). Cost estimate: open
models single-digit USD; frontier with reasoning dominates — **$50–200** total.

**Run-consistency protocol (anti-caching).** Firing an identical prompt 3× back-to-back risks
provider-side effects (prompt/KV caching, request coalescing) that could artificially inflate
run-consistency. Mitigations: (a) runs executed as **separate full passes** (complete run 1 over
all items, then run 2, then run 3), giving temporal separation; (b) item order **shuffled per
pass**; (c) provider prompt-caching disabled where the API exposes a control, and cache-hit
fields in responses logged where reported; (d) provider/system fingerprints and latencies logged
per call. Interpretation is asymmetric and stated in the paper: caching can only *inflate*
consistency, so observed *in*stability is a lower bound on the real thing, while
perfect-consistency claims are checked against the cache-hit/latency logs.

## 7. Metrics and analysis

**Primary — verdict quality vs. gold-200 (random 140) at T = 6 (violation ⇔ d > 6):** accuracy,
precision, recall, F1 of `has_violation`. This is what a deployed SPRINT rule delivers. The
parser arm is scored identically.

**Secondary — measurement quality on the same items:**
- pair identification P/R/F1, matched by **word form** of both endpoints (greedy, ties by index
  proximity); index-based matching reported separately — the form/index gap *is* the positioning
  failure;
- distance exact / ±1 / MAE on form-matched pairs;
- **decomposition (H4):** distance-correct *given* both endpoints correctly named — the exp_01
  instrument, per model-mode × formulation.

**Stability:** across 3 runs — verdict flip rate; exact-set match of pair lists (interpreted per
§6 anti-caching notes).
**Cost:** real USD per 1k sentences per condition; latency.
**Validation catch-rates:** % of generations failing schema / bounds / form-at-index, per
condition (reported, not corrected).
**Breakdowns:** phenomenon flags (copular, pro-drop present, non-SVO, coordination, fragment,
aby-clause), clause count, length, distance band (especially near-threshold d ∈ [4, 9]),
sub-corpus. Targeted-60 and CLTT-derived gold: diagnosis only, reported separately.

**The one figure:** verdict accuracy (y) vs. capability (x: 30B → 70B → frontier →
frontier+reasoning), two curves (R1, R2), dashed horizontal line = parser baseline with its CI;
a small inset (or second panel) with the H4 decomposition (identification vs. counting share of
residual error) so the mechanism claim needs no extra figure. McNemar on paired verdicts for the
key comparisons (R2 vs. R1 per model; best-LLM vs. parser baseline).

**Statistical power (stated up front, checked at the audit gate):** with n = 140 paired verdicts,
McNemar detects differences of roughly ~8–10 pts at α = 0.05 with reasonable power; ~5 pt
differences will not be resolvable on gold — the paper reports CIs and avoids overclaiming close
calls. Precision/recall CIs additionally depend on violation prevalence (§4.1 audit gate); if
prevalence is low, the random gold slice is enlarged, not stratified.

**Qualitative error pass:** 20–30 residual errors of the best LLM configuration and of the parser
arm, hand-categorized by phenomenon (feeds the paper's error-analysis section and exp_03's
inventory).

## 8. Execution plan

1. Sampling + dedup; audit gate (§4.1); freeze eval-640 (`data/eval/`). Descriptive table (§4.3).
2. Extraction code (parser arm) incl. §3.1 finite-element rule + assertions; run on eval-640 and
   on CLTT; worked examples for Katka (~20); freeze `ANNOTATION_GUIDELINES.md` (K6 encoded as
   provisional).
3. Annotation sheets (pre-numbered words) → Katka: 140 random + 60 targeted; 50 double-annotated
   (second annotator: Tomáš).
4. R1 Czech adaptation + R2 written; frozen after a 20-sentence smoke test (format compliance
   only — no metric peeking); model roster + providers pinned and recorded.
5. Full grid (15,360 generations) as three shuffled passes per condition (§6 protocol), resumable
   harness with traces (port of exp_01 `run_llm.py`).
6. Scoring, figure, breakdowns; error inventory exported for experiment_03.

## 9. Deliverables

1. **The figure + the recommendation:** the least capable model × formulation (if any) whose
   verdict quality reaches the parser baseline — or the finding that none does, which settles
   the question in favor of the parser pipeline with unfiltered-text evidence.
2. **The R2 rule template** in SPRINT `prompt_content` format, directly usable in the app.
3. **Gold data:** KUK-200 human-annotated pairs under the signed-off §3 definition + IAA figures
   + CLTT-derived gold pairs — the first human gold for this task.
4. **The honest parser-baseline number** on *unfiltered* legal Czech — the quantified headroom
   that motivates (or kills) experiment_03.
5. Full traces, costs, and code, as in exp_01.

## 10. Relationship to experiment_03 and the joint paper

- **exp_03 (separate paper, `../experiment_03/METHODOLOGY.md`):** the LLM-boost question on an
  enrichment-sampled hard-case set — powered by exp_02's error inventory, annotation protocol,
  and the measured parser-baseline headroom. Also inherits the semantic-triage module.
- **Joint paper mapping:** Katka's free-word-order section → identification results + phenomenon
  breakdowns; "Golden Truth Data" → §4.2; the experiments section → the figure; the abstract's
  "LLMs and traditional tools together" → the per-rule-prose vs. per-rule-engineering economics
  + exp_03 outlook.

## 11. Open items and decision record

**Open:**
- **O2:** frontier model pick + API knobs (reasoning toggle, temp support, cache controls) —
  verify at run time.
- **O5:** flag the garbled `teaching_examples` in the C4DHI export back to KMH; confirm the rule
  is also deployed for Czech text (the export's testset is English — see §5.2 R1 note).

**Resolved:**
- **O1** (2026-07-17): production rule obtained → `docs/sprint-rule-C4DHI_Predicate-Subject_Distance.json`.
  Review findings: (a) rule text and testset are **English** (EU directive sentences) → R1 =
  faithful Czech adaptation, §5.2; (b) threshold semantics "at least 7 words between" → §3.5
  fixed to *violation ⇔ d > 6* (v3 had an off-by-one); (c) one `teaching_examples` entry is
  garbled (two examples merged) → repaired in R1, flagged (O5); (d) no operational definition of
  predicate/subject/clause — preserved in R1 by design, it is the production reality R2 is
  measured against.
- **O3** (2026-07-17): second annotator for IAA-50 = **Tomáš** (rationale in §4.2).
- **O4/K6** (2026-07-17, provisional): shared-subject predicate coordination → **one pair,
  distance to the first verb**; to be confirmed with Katka (§3.3).
- Katka's review (2026-07-16): K1 conditional aux not leftmost; K2 *by* confirmed; K3 first
  conjunct; K4 csubj excluded; K5 T = 6 (as *maximum allowed*, see §3.5); aby/kdyby = conjunction
  word; verbo-nominal ≠ copular.

## 12. Out of scope (explicitly)

Pre/post-processing around the LLM (numbered-input variants, code-side arithmetic, retries);
parse-hint prompts; tool use / code execution; fine-tuning; **additional rule formulations beyond
R1/R2** (the formulation axis is explored further only if R2 wins — e.g. alternative
definitions, factorized definition-vs-scaffold ablations); ≤8B models (settled by exp_01;
backfill possible); LLM-repairs-UDPipe (→ exp_03); semantic triage of flags (→ exp_03, needs
human difficulty data); surprisal/DLT metrics (future work); sentence-segmentation study (held
fixed, caveat reported).
