# Experiment 01 — supervisor summary

**Question:** Can LLMs reliably identify the main subject (podmět) and predicate (přísudek) of a
Czech legal sentence and count the linear word-distance between them — and does giving them the
syntactic structure (CoNLL-U) help? A deliberately narrow, objectively-scoreable proxy for SPRINT's
"counting"-type LPV rules.

**Bottom line:** Small models (≤10B) cannot do it at all; large open models (70B-class) read the
structure reasonably well but **still miscount the distance ~28–36% of the time even when handed the
parse and the correct words** — the weak link is counting itself; no model is reliable end-to-end,
and the instability cannot be tuned away. For structural/counting rules the defensible engineering
choice is a **deterministic extractor over the UD parse — not an LLM** (≈99% accurate and
zero-variance vs. ≤65% for the best
LLM condition).

---

## What we ran

- **Data:** KUK 1.0 (legal/administrative Czech, UDPipe silver parses). 910k sentences → 415k pass a
  single-main-clause filter → **N=640** stratified eval set (length × distance buckets, tail
  over-sampled; balanced 160 each across the 4 sub-corpora).
- **Task/metric:** distance = words strictly between subject and its head (the predicate), counted in
  whitespace-words. Silver gold from UDPipe. Predicate = head-of-subject (copula → nominal part);
  *provisional, pending linguist sign-off.*
- **Models (family-matched, all open, fp8, provider-pinned):** Llama-3.1-8B / Llama-3.3-70B,
  Qwen-2.5-7B / Qwen-2.5-72B.
- **Design:** 3 regimes (raw text · self-generated CoNLL-U · CoNLL-U given) × 4 models × 3 runs
  (temp 0) = **23,040 generations**. Full prompt+response traces stored. Real cost **$7.73**.

---

## Headline results — distance exact-match (%)

| model | raw text | self-CoNLL-U | CoNLL-U given |
|---|--:|--:|--:|
| Llama-8B | 8.0 | 8.2 | 4.2 |
| Qwen-7B | 7.4 | 12.2 | 23.9 |
| Llama-70B | 20.9 | 26.1 | **59.6** |
| Qwen-72B | 25.3 | 39.1 | **64.9** |

**The ceiling:** the single best condition — Qwen-72B *handed the gold parse*, needing only to find
`nsubj`, follow HEAD, and subtract — is **64.9% exact, i.e. ~35% wrong when given the answer's
structure.**

### The decisive decomposition: naming the words vs. counting the span

With the parse supplied, separate *naming* the correct subject/predicate words from *counting* the
distance between them:

| model (CoNLL-U given) | names both words | distance exact | **exact \| both named** |
|---|--:|--:|--:|
| Qwen-72B | 82.7% | 64.7% | **72.3%** |
| Llama-70B | 86.7% | 59.6% | **63.8%** |
| Qwen-7B | 41.0% | 23.5% | 38.4% |
| Llama-8B | 45.5% | 4.2% | **0.1%** |

- **The weak link is counting, not structure-reading.** Given the parse, large models *name* the
  right subject/predicate ~83–87% of the time (identifying *which* words is largely solved), yet
  **even when they name both words correctly they still miscount the span ~28–36% of the time**. The
  miscounting is in word *positions*: they name the predicate 93–97% of the time but place it
  correctly only ~55% — the count drifts with sentence length.
- **The small model genuinely cannot count** — Llama-8B is 0.1% exact even when it named both words.

---

## Hypotheses

- **H1 (structure helps):** ✅ Regime effect large and significant for the big models — raw → CoNLL-U-
  given is **+38 pts (Llama-70B)** and **+39 pts (Qwen-72B)**, McNemar p ≈ 10⁻⁴⁵–10⁻⁴⁷. The value is
  in *being handed* the parse, not generating it (self-CoNLL-U helps only modestly).
- **H2 (size):** ✅ Strong within-family, every regime (70B ≫ 8B; 72B ≫ 7B).
- **H3 ("structure compensates for size"):** ❌ **Rejected.** Structure *widens* the size gap on exact
  counting (raw gap ~13–18 pts → CoNLL-U-given gap ~41–55 pts): big models turn the parse into a
  correct count, small ones don't. (Structure *does* help small models get *approximately* right and
  locate roles — but not *exactly* right.)
- **H4 (degrades with length/distance):** ✅ Exact-match collapses on the far tail (CoNLL-U-given:
  48→51→39→**15%** across distance buckets 0-1 / 2-4 / 5-9 / 10+).

---

## Two findings that shape the SPRINT recommendation

**1. The instability cannot be tuned away.** At temperature 0 with provider+quantization pinned, the
3 runs still disagree on **36%** (raw text) / **56%** (self-CoNLL-U) of sentence×model triplets
(CoNLL-U-given is stabler, 11%). Crucially, **majority-vote-of-3 does not improve accuracy** (≈ single
run everywhere): when the model varies it flip-flops between *wrong* answers, so self-consistency /
resampling won't deliver repeatable rule outcomes. And a *consistent* answer can be consistently
*wrong* (Llama-8B CoNLL-U-given: 80% consistent, 4% correct) — reproducibility ≠ correctness.

**2. The silver oracle is trustworthy; the LLM failures are real.** Re-parsing 740 human-gold
`cs_cltt` legal sentences with the same UDPipe model shows **99.3% agreement with human gold** on
subject/predicate/distance where UDPipe commits to a single-clause parse. So the model failures above
are genuine, not oracle noise. The silver noise that *does* exist is in **sentence segmentation**
(UDPipe splits ~60% of gold legal sentences differently) — an upstream issue that affects any method.

---

## Recommendation for SPRINT

For **structural / countable** LPV rules (paragraph counts, reference nesting, subject–predicate
distance, future cognitive-complexity metrics), use a **deterministic extractor over the UD parse** —
not an LLM. Justification, now quantified:

- A rule computing the count from the parse would be **~99% accurate** (the parser noise-floor) and
  **zero-variance**, vs. **≤65%** and unstable for the best LLM condition.
- The LLM's own **counting is the weak link**: even given the parse and the correct endpoints it
  miscounts ~28–36% of the time, whereas a parser identifies those endpoints ~99% correctly and the
  subtraction is trivial in code — so replacing the LLM removes the dominant error source.
- LLM mitigations we might reach for (temp 0, provider pinning, majority voting) demonstrably do
  **not** produce repeatable counts.

"Hybrid (LLM + structured context)" is warranted only for a *different* rule class — those needing
semantic/pragmatic judgement a parser can't express. The key design step is **triaging each rule**
into structural (→ deterministic) vs. semantic (→ LLM).

*Caveat carried by any approach:* sentence-boundary detection in legal Czech is parser-dependent and
must be treated as a fallible first-class step, upstream of any counting rule.

---

## Limitations & next steps

- **Silver-only** (agreement with UDPipe, not linguistic truth) — mitigated by the 99.3% noise-floor;
  no new gold annotation needed for the labels.
- **Predicate = head-of-subject** is provisional — one linguist sign-off outstanding (see
  `OPEN_QUESTION_predicate_definition.md`).
- One prompt formulation per regime; word-distance metric; single pinned provider per model.
- **Proposed experiment_02:** the informative size axis is now **70B vs. frontier**, focused on the
  *counting* bottleneck (does the ~30% miscount-given-endpoints shrink with scale?). Note this is a
  *scientific* question; it would not change the *engineering* recommendation above.
- Optional for the final paper: a mixed-effects model for formal joint CIs/interaction — low marginal
  value given effect sizes this large, so deferred.

*Artifacts:* full metrics `results/metrics_by_condition.csv`; per-generation traces
`results/scored.jsonl`; error/instability `results/error_analysis.json`; noise-floor
`results/cltt_noise_floor.json`; detailed write-up `docs/RESULTS.md`; methodology `docs/METHODOLOGY.md`.
