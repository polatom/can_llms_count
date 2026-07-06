# Results — first full run (2026-07-01)

Silver-standard run over the N=640 stratified eval set, 4 family-matched open models
(Llama-3.1-8B / Llama-3.3-70B, Qwen-2.5-7B / Qwen-2.5-72B; all fp8, provider-pinned), 3 prompting
regimes, 3 runs each at temperature 0 = **23,040 generations**. Metrics vs. UDPipe silver gold
(word-distance). Source: `results/scored.jsonl`, `results/metrics_by_condition.csv`.

**Real cost (from `usage.cost`): $7.73** total (llama-8b $0.19, llama-70b $1.05, qwen-7b $2.94,
qwen-72b $3.55). Reconciliation: `COST_REPORT.md` used an optimistic chars→token ratio (3.5) and
pre-Together qwen prices; real token volume ran ~40–60% higher and qwen-7b on Together is ~7× Phala.
Order-of-magnitude was right (single-digit $); update the ratio to ~2.4 chars/token for Czech+CoNLL-U.

## Headline metrics — distance exact-match (%) and role identification

| model | regime | format-ok | **exact** | ±1 | ±2 | MAE | both-roles | run-consistency |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| llama-8b | raw_text | 99.9 | 8.0 | 29.5 | 50.0 | 4.00 | 5.2 | 43.0 |
| llama-8b | raw→conllu | 93.1 | 8.2 | 40.7 | 56.6 | 4.27 | 18.0 | 23.0 |
| llama-8b | conllu-given | 100 | 4.2 | 51.6 | 60.3 | 3.56 | 35.4 | 79.7 |
| llama-70b | raw_text | 99.4 | 20.9 | 42.7 | 55.4 | 3.60 | 10.6 | 65.6 |
| llama-70b | raw→conllu | 99.5 | 26.1 | 43.8 | 57.5 | 3.35 | 20.1 | 40.3 |
| llama-70b | conllu-given | 100 | **59.6** | 67.5 | 79.9 | 1.80 | 50.8 | 83.4 |
| qwen-7b | raw_text | 100 | 7.4 | 20.3 | 35.4 | 6.01 | 2.8 | 82.5 |
| qwen-7b | raw→conllu | 98.7 | 12.2 | 42.8 | 54.9 | 4.47 | 21.3 | 64.3 |
| qwen-7b | conllu-given | 98.3 | 23.9 | 51.5 | 63.2 | 3.43 | 32.1 | 96.8 |
| qwen-72b | raw_text | 100 | 25.3 | 49.4 | 68.0 | 2.72 | 15.5 | 66.1 |
| qwen-72b | raw→conllu | 99.9 | 39.1 | 56.3 | 71.1 | 2.34 | 32.0 | 48.4 |
| qwen-72b | conllu-given | 99.7 | **64.9** | 71.1 | 84.0 | 1.24 | 51.6 | 97.0 |

(run-consistency = % of 3-run triplets with identical answers, temp 0, pinned provider.)

## Hypothesis verdicts

- **H1 (structure helps: conllu-given > self-conllu > raw)** — **supported.** Exact-match rises with
  structure for 3/4 models (e.g. qwen-72b 25→39→65; llama-70b 21→26→60). Exception: llama-8b's *exact*
  barely moves (8→8→4), but its ±1 and role-ID jump sharply (see H3 nuance).
- **H2 (size: large > small)** — **strongly supported**, within family and every regime. Llama 70b ≫ 8b
  (raw 21 vs 8; conllu-given 60 vs 4). Qwen 72b ≫ 7b (raw 25 vs 7; conllu-given 65 vs 24).
- **H3 (structure *compensates for size* — helps small models more)** — **REJECTED (and this is the
  key SPRINT finding).** On exact-match, structure *widens* the size gap: raw gap ≈ 13–18 pts,
  conllu-given gap ≈ 41–55 pts. Large models convert the given parse into a correct count; small
  models do not (llama-8b: 4% exact even *handed* the parse). **Nuance:** structure *does* help small
  models get *approximately* right and locate roles (llama-8b ±1: 30→52; both-roles: 5→35; qwen-7b
  ±1: 20→52) — but turning "approximately right" into "exactly right" (the actual counting) still
  needs capability the small models lack. → Giving an LLM structured context is **not** a reliable
  substitute for a deterministic counter, especially at small scale.
- **H4 (degrades with length/distance)** — **supported.** Exact-match by gold distance bucket, pooled:
  raw 26→22→11→**3%**; self-conllu 31→25→19→**12%**; conllu-given 48→51→39→**15%** (buckets 0-1 / 2-4 /
  5-9 / 10+). The long-distance tail collapses in every regime.

## Other findings worth reporting

1. **Even the ceiling can't reliably count.** The best condition — qwen-72b *handed* the gold
   CoNLL-U, needing only to locate `nsubj`, follow HEAD, and count — is **64.9% exact**, i.e. **~35%
   wrong when given the answer's structure.** Direct evidence for "don't trust LLM prompting for
   counting rules."
2. **Reproducibility ≠ reliability.** Even at temp 0 with provider+quant pinned, runs disagree on
   **35.7%** (raw_text) and **55.8%** (self-conllu) of sentence×model triplets; conllu-given is far
   more stable (**10.8%**). So the residual non-determinism is real and regime-dependent — and a
   *consistent* answer can still be *wrong* (llama-8b conllu-given: 80% consistent, 4% correct).
3. **Self-generated CoNLL-U is the least stable regime** (lowest run-consistency, e.g. llama-70b
   40%, qwen-72b 48%) and has the most malformed output (llama-8b 93% format-ok; one llama-70b run
   degenerated into a repetition loop under Novita before we pinned DeepInfra).
4. **llama-8b off-by-one signature**: given CoNLL-U it reaches 52% ±1 but only 4% exact — it locates
   the pair and counts *almost* right, systematically off by one. A clean error-taxonomy exhibit.

## Error analysis & instability (`error_analysis.py` → `results/error_analysis.json`)

**The decisive decomposition — naming the words vs. counting the span** (CoNLL-U-given regime).
Separate two abilities: does the model *name* the correct subject/predicate words, and — given that —
does it get the *distance* right?

| model (CoNLL-U given) | names both words | distance exact | **exact \| both named** |
|---|--:|--:|--:|
| qwen-72b | 82.7% | 64.7% | **72.3%** |
| llama-70b | 86.7% | 59.6% | **63.8%** |
| qwen-7b | 41.0% | 23.5% | 38.4% |
| llama-8b | 45.5% | 4.2% | **0.1%** |

The residual failure is **counting, not structure-reading**:
- Given the parse, the large models *name* the right subject/predicate ~83–87% of the time — so
  identifying *which* words they are is largely solved. But their distance is exact only ~60–65%,
  and **even when they named both words correctly they still miscount the span ~28–36% of the time**
  (qwen-72b 72.3% / llama-70b 63.8% exact given both named).
- The miscounting is specifically in **word positions**: the large models name the predicate word
  93–97% of the time but report its correct linear position only ~55% (subject: named 87–88%,
  positioned 73–75%). The endpoint deeper in the sentence (usually the predicate) is mis-positioned
  far more — a count that drifts with length. E.g. it names *provozovatel*/*hradí* correctly but
  places them at positions 30/17 instead of 25/14 → distance 12 vs. gold 10.
- **The small llama cannot count at all** — 0.1% exact even when it named both words.

> Correction note: an earlier version conditioned on both *word indices* matching gold, giving a
> near-100% "exact given roles". That was near-circular (correct positions + a correct subtraction ⇒
> correct distance by construction) and mislabeled counting failures as role-identification. The
> form-based decomposition above correctly isolates the counting step.

### Instability — and why voting won't save it

| regime | mean spread (runs) | p90 | max | single-run exact | **majority-vote exact** |
|---|--:|--:|--:|--:|--:|
| conllu-given | 0.1–1.6 | 0–4 | 23–54 | (per model) | **≈ single-run** |
| raw_text | 0.6–1.7 | 1–4 | 15–44 | | **≈ single-run** |
| self-conllu | 2.6–5.0 | 7–14 | **63** | | **≈ single-run** |

Three things about the instability:
1. **Majority-vote-of-3 does not help** — majority accuracy ≈ single-run accuracy in every cell
   (e.g. qwen-72b raw 25.3→24.8; llama-70b conllu 59.6→60.0). The variance is **not** noise around a
   correct answer the model "really knows"; when it varies, it flip-flops between *wrong* answers.
   So self-consistency / resampling will **not** fix reliability for a production rule.
2. **It's regime-dependent**: `conllu-given` is quite stable (80–97% of triplets identical, spread
   ≈0); `self-conllu` is the unstable one (it re-parses differently each time → different counts).
3. **It tracks difficulty**: for raw text, the fraction of triplets that vary grows with distance
   (29%→41%); for conllu-given it stays flat and low (~8–14%). Instability is a *symptom of the
   model not knowing*, concentrated exactly where it's already failing.

**Resolution for SPRINT (the instability worry, answered):** the fix is not inside the LLM.
(a) The recommended production path — extract the endpoints from the UD parse and compute the
distance in code — has **zero variance and zero counting error** by construction. (b) The
decomposition shows the LLM's own **counting is the weak link**: even given the parse and the
correct words it miscounts ~28–36% of the time, while a parser identifies those endpoints ~99%
correctly (§ noise-floor) and the subtraction is trivial in code. (c) We now have evidence that the
usual LLM mitigations (temperature 0, provider pinning, majority voting) do **not** deliver
repeatable counts. The instability is thus an argument *for* the deterministic design, not a problem
to tune away.

## Parser noise-floor — UDPipe vs. `cs_cltt` human gold (`cltt_noise_floor.py`)

Re-parsed 740 `cs_cltt` gold sentences (that pass our filter) with the *same* UDPipe model that
made the KUK silver (`czech-pdt-ud-2.15-241121`) and compared extracted subject/predicate/distance
to human gold (word units, identical raw text). Result:

- **Where UDPipe commits to a comparable single-main-clause parse (295/740), it agrees with the
  human gold almost perfectly**: subject-word 100%, predicate-word 99.3%, **distance-exact 99.3%**,
  MAE 0.14. → The silver *labels* (nsubj/head/distance) are highly trustworthy on legal Czech.
- **The silver noise is upstream, in sentence segmentation, not role labeling**: for 445/740 gold
  sentences UDPipe split the text into ≥2 sentences (407 into two) — i.e. it disagrees with humans
  about where a "sentence" ends, not about the subject/predicate within one.

**Two consequences:**
1. **The LLM failures are real, not silver artifacts.** Since UDPipe's role/distance matches humans
   ~99% on single-clause sentences, qwen-72b's "35% wrong even given the CoNLL-U" is a genuine model
   limitation, not the oracle being wrong. This survives METHODOLOGY §7 Trigger A (no gold
   re-annotation needed for the labels — parser quality is *not* materially worse on legal Czech).
2. **It grounds the pure-rule recommendation.** A deterministic extractor over the UD parse would be
   ~99% correct on this task (vs the best LLM regime's 65%) *and* zero-variance — so "compute the
   count from the parse, skip the LLM" is not just cheaper/stabler but substantially *more accurate*.
   The one caveat inherited by any approach (LLM or rule) is segmentation: what counts as a
   "sentence" in legal Czech is parser-dependent. Our eval is internally consistent (built on
   UDPipe's own segmentation), but end-to-end deployment must treat sentence boundaries as a
   first-class, fallible step.

## Caveats (per METHODOLOGY §8)

Silver-only (agreement with UDPipe, not linguistic truth; CLTT/`cs_cltt` QC still to run); one
prompt formulation per regime; word-distance metric; provider pinned to one endpoint per model.
Predicate = head-of-subject is still provisional pending linguist sign-off.

One measurement caveat for the pure-counting decomposition: `both_roles` is judged on the reported
**word** index. In `conllu-given`, a model that correctly locates the token but reports its CoNLL-U
**token** index (instead of mapping to a word) is scored as a role error — so some "role errors"
there may be token→word mapping mistakes rather than picking the wrong word. The qualitative pass
(error_analysis follow-up) should separate these; it does not affect the small-vs-large counting
contrast (llama-8b fails counting even when the word index matches).

## Next

`error_analysis.py` (taxonomy over `scored.jsonl`: off-by-one, wrong attachment, tokenization
mismatch, malformed output), the CLTT/`cs_cltt` parser noise-floor, and the mixed-effects model
(distance-exact ~ regime × size + length + depth + (1|sentence) + (1|model_id)) for the paper.
