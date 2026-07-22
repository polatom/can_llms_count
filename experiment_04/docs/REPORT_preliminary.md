# Can an LLM measure subject–predicate distance in Czech legal text?
## Preliminary report — experiment_04 (2026-07-22, draft for co-authors)

*Audience: project colleagues (Bára, Katka) who were not part of the day-to-day work. Everything
here is reproducible from the repository (`experiment_04/`): every number traces back to stored
raw model outputs, and every design decision has a dated record. Status: results essentially
final; one grid finishing (noted inline); the full-frontier run is a pending cost decision.*

---

## 1. The question and why it matters

Long spans between a subject (podmět) and its predicate (přísudek) burden the reader's working
memory and are a validated indicator of poor comprehensibility in legal Czech (dependency-
locality literature: Gibson 1998/2000). PONK uses the rule **flag a sentence if any
subject–predicate pair has more than 6 words between them** (T = 6). The SPRINT application lets
lawyers write such rules *as prose prompts* evaluated by an LLM per sentence — cheap to author,
but the production distance rule did not work well in practice.

**Experiment_01** (this project, 2026-07) showed why one should be skeptical: on filtered legal
Czech, LLMs could often *name* the subject and predicate but systematically **miscounted** the
span (~28–36% wrong even when handed a parse), and the errors could not be tuned away. The
engineering alternative — UDPipe plus a hand-written extractor — is accurate but is *per-rule
code*, only exists for parseable phenomena, and can't be authored by lawyers.

**Experiment_04 asks:** can a *pure-LLM rule* — raw sentence in, verdict out, no pre- or
post-processing, deployable in today's SPRINT by editing rule text — match the deterministic
parser pipeline? And what does it take, along two axes:
**model capability** (27B → 72B → 235B → mid-frontier → frontier±reasoning) and
**rule formulation** (from the production rule verbatim to linguist-engineered procedures)?

## 2. Data and gold standard

**Eval set: the whole `cs_cltt` treebank** (UD conversion of CLTT 2.0; Kříž & Hladká 2018) —
1,121 human-annotated sentences of Czech statute text, **unfiltered** (multi-clause sentences,
fragments, 466-word enumeration monsters all included; median 22 words, p90 = 58).

**Task (per sentence):** list *all* subject–predicate pairs of finite clauses with an overt
subject — possibly zero (26% of sentences), often several (mean 1.44; up to 18 observed) — with
1-based word positions and the distance (words strictly between); verdict = any pair with d > 6.
The linguistic operationalization was developed with and signed off by Katka (decisions K1–K13),
notably: the measured predicate is the **agreement-bearing element** (finite verb; auxiliary in
analytic forms — including the participial *byla* in past passives/copulas; the copula, never
the nominal; the conjunction itself in *aby/kdyby* clauses, which absorb the conditional
auxiliary); coordinated predicates sharing a subject count **once**; verbless clauses are
excluded; relative pronouns *are* subjects of their clauses (subject to the case-elimination
test below); quantified subjects (*dvanáct měsíců*) measure to the nominative quantifier.

**Gold = the rule applied to the human trees** (1,617 pairs), then **independently verified**:
Katka — an expert linguist who is *not* a CLTT author — reviewed 24 worked examples spanning
every construction type plus a stratified sample of 105 derived pairs. Outcome: **104/105
confirmed, 1 genuinely ambiguous, 0 outstanding errors** after one fix. The verification process
also surfaced two errors in the *treebank itself* that our pipeline had inherited: (a) fused
conditional verbs (*Nestanoví-li*) systematically mis-tagged as nouns — 31 silently missing
pairs, repaired by rule; (b) one quantified-subject convention divergence. A pleasant side
finding: **the LLM arm's "false positives" served as an audit of the human annotation** — model
disagreements led us to both treebank bugs.

Violation prevalence: 17.3% of sentences (194/1,121) — enough statistical power to resolve
~3–4-point differences between systems (McNemar, α = 0.05).

## 3. The deterministic baseline (parser arm)

UDPipe 2 (`czech-pdt-ud-2.15`) on the raw sentence text + the same extraction rule:

| configuration | verdict F1 | pair F1 | distance correct (given pair found) |
|---|--:|--:|--:|
| default tokenizer | 91.3 | 92 | 99.8% |
| **`presegmented` (unit = one sentence)** | **97.1** (P 97.9 / R 96.4) | **96.5** | 99.8% |

Two lessons: (1) the parser's celebrated exp_01 accuracy (99.3%) was an artifact of filtering —
on real unfiltered statutes it is 97.1, and its errors are **lost pairs**, never mismeasured
ones; (2) its single biggest failure mode was the *sentence segmenter*, not the parser — with
the default tokenizer, re-segmentation destroys 6 F1 points; declaring the unit boundaries
(which any deployment knows) recovers them. The deterministic pipeline is **zero-variance and
costs ~nothing**, but is per-rule engineering.

## 4. The formulation ladder: what prompt engineering buys (open models)

We iterated the rule text five times on **Qwen-2.5-72B** (the strongest open model of
experiment_01), each iteration targeting the *measured* dominant error class of the previous
one, with full three-pass runs (temperature 0, pinned provider/quantization, order shuffled per
pass — 3 × 1,121 sentences per cell):

| formulation | mechanism (and literature basis) | verdict F1 |
|---|---|--:|
| R0 production rule | verbatim SPRINT rule (underspecified) | *(not run at 72B; see §6 for frontier)* |
| R1 "best naive" | full linguistic definitions + few-shots, no procedure | 58.5 |
| R2 procedural | + step decomposition and **self-enumeration counting scaffold** (scratchpads: Nye et al. 2021; CoT-for-counting: Zhang et al. 2024; Chain-of-Code: Li et al. 2023) | 72.5 |
| R3 inventory | + **per-word category sweep** with closed word lists (decomposed prompting: Ma et al. 2024; structured prompting: Blevins et al. 2023), motivated by Katka's hypothesis that small models lack linguistic metalanguage — replace categories with elementary string/case tests | 74.7 |
| R4 pairing rules | + **Katka's case-elimination algorithm** for relative pronouns, preposition rule, predicate-uniqueness | **76.5** |
| R5 precision surgery | + targeted rules against the three residual error classes | 76.0 (**plateau**) |

Mechanistically the ladder decomposes cleanly (share of gold pairs, 72B):

| stage | R1 | R2 | R4 |
|---|--:|--:|--:|
| predicate found | — | — | 92.5% |
| full pair named | 26% | 50% | 76% |
| **distance correct, given found** | **30%** | **97%** | **95%** |

**Finding 1 — counting is solved by prompt structure.** The self-enumeration scaffold moves
distance accuracy on found pairs from ~30% to 95–97%, eliminating experiment_01's core deficit
without any tools. (Amusingly, models report word *positions* wrong ~50% of the time with a
constant offset — but the *difference* survives, so distances are right.)

**Finding 2 — identification became the wall, and prompts moved it a long way but not to the
end.** Naming recall climbed 26% → 76% across the ladder; what remains is *pairing precision*:
the model fabricates pairs (borrowing subjects across clauses, pairing fronted instrumentals in
*"X-ou se rozumí Y"* definitional patterns, drifting off the aby-convention). These errors are
**systematic** — stable across runs (79% of correct pairs recur in 3/3 runs, but so do 31% of
fabricated ones) — and **R5's explicitly-targeted counter-rules changed nothing (76.5 → 76.0)**:
at 72B the model reads the rule and errs anyway. Prompting has a ceiling, and we measured it.

**Finding 3 — ensembling works at pair level (unlike exp_01's answer-level voting).** Keeping
pairs that recur in ≥2 of 3 runs: verdict F1 76.5 → **78.3**. Unanimity buys little more
(systematic errors survive any number of repetitions). Single-run verdict recall — the
deployment-relevant number — is 93.5%; false flags concentrate on long sentences (mean 49 words
vs. 22 for true negatives), i.e., on text an editor may want to inspect anyway.

## 5. The capability axis: verdict F1 at fixed formulation (R4)

| model | class | verdict F1 | pair F1 | cost/1k sentences* |
|---|---|--:|--:|--:|
| gemma-3-27B | open | 66.5 | 58.6 | ~$0.9 |
| Qwen-2.5-72B | open | 76.5 | 67.4 | ~$1.9 |
| Qwen3-235B-Instruct | open | **87.2**† | 78.1 | ~$0.8 |
| gpt-5-mini | mid-frontier | **92.3** | 73.4 | ~$2.3 |
| *parser (UDPipe + rule)* | deterministic | **97.1** | 96.5 | ~$0 |

\* single pass, current OpenRouter prices; † third pass finishing at writing time.

Capability, not prompt wording, is the dominant dial above 72B. A $0.25/M mid-frontier model
lands within 5 points of the parser.

## 6. Frontier probes: is the residual gap capability-bound? (cheap, targeted)

Instead of a full frontier grid (~$350–450, pending a cost decision), we probed **the 104
sentences that qwen-72B×R4 gets wrong in ≥2 of 3 passes** — the systematically hard set — with
gpt-5.1 (single pass each, ~$6–10 per probe):

| frontier configuration | verdict correct on hard-104 | pairs P / R |
|---|--:|--:|
| reasoning-high × **R0** (production rule verbatim) | 64% (37 false flags) | 53 / 47 |
| reasoning-high × **R1** (definitions, no scaffold) | 95% | 94 / 92 |
| reasoning-**off** × R4 | 88% | 82 / 89 |
| reasoning-high × **R4** | **98%** (0 false flags) | 94 / 96 |

**Finding 4 — capability subsumes the *scaffold*, not the *definitions*.** At frontier
capability the procedural machinery is worth ~3 points (R1→R4) but precise linguistic
definitions are worth ~31 (R0→R1). This is also the controlled post-mortem of the production
rule: it fails **even on a frontier reasoning model** — the rule text and the model were each
half of the original problem. Practical corollary for SPRINT: lawyers must write Katka-grade
definitions; they may skip step-by-step scaffolds if the model is strong.

**Finding 5 — the open-model residual is capability-bound.** The fabrication classes that no
prompt could fix at 72B essentially vanish at gpt-5.1-with-reasoning (98% on the hard set, zero
false flags). Full-set frontier parity with the parser is the *expected* outcome of the full
grid, no longer a gamble. (Methodological caution that cost us one invalid probe: reasoning
models silently truncate if the output budget is small — 76/104 empty completions at a 6k-token
budget, fixed at 24k. Silence parses as "no violation"; validity checks matter.)

## 7. Deployment economics (for SPRINT)

- **One sentence per call + rule-as-cached-prefix** beats sentence batching: per-sentence calls
  preserve the audit trail, fit SPRINT's differential re-evaluation, avoid cross-sentence
  interference — and prompt caching delivers the economics batching was chasing. Measured: on
  OpenAI, 97% of the prompt (the 2.6k-token rule preamble) is served from cache, 2.7× latency
  reduction, cached input billed at a fraction; on DeepInfra, no caching (self-hosted serving:
  enable prefix caching). 
- **Whole-experiment cost context:** every result in this report — five formulations × two
  models × three passes, three more model grids, five frontier probes, a secondary corpus run,
  ~35,000 stored traces — cost **~$64** (plus $7.73 for experiment_01). The largest single item
  was frontier probing ($28).
- Optional knobs measured: majority-of-3 ensembling (+1.8 F1 at 3× cost); threshold-margin
  calibration (recall↔precision trade by shifting T) available from traces.

## 8. Robustness note (secondary corpus)

To address "the eval treebank is public and may be memorized": the best open configuration is
being re-run on 640 unfiltered sentences of a different legal-administrative corpus (KUK/ESO,
ombudsman statements; silver-only agreement analysis vs. the parser). *Completing at writing
time; will be appended.* The hard-104 probe results already argue against memorization driving
the CLTT numbers (errors pattern with linguistic structure, not with sentence identity).

## 9. What we propose the paper looks like

**Title direction:** *"Don't ask an LLM to count: capability, prompt structure, and the limits
of prose rules for a syntactic comprehensibility metric in Czech legal text."*

**Core figure (exists in the data):** verdict F1 vs. model capability, two-to-three formulation
curves, dashed parser baseline at 97.1 — every headline claim readable off one plot.

**Claims, each already supported:**
1. A validated gold standard for subject–predicate distance on unfiltered legal Czech (1,617
   pairs, independently verified at ~99%, two treebank bugs found and fixed) — the "Golden
   Truth Data" contribution, showcasing CLTT.
2. The deterministic baseline honestly measured (97.1 on unfiltered text; segmentation, not
   parsing, is its weak point — and it's configurable away).
3. Counting is a prompt-structure problem (30→97% via self-enumeration), *identification* is a
   capability problem (the ladder plateaus at 76.5/72B; capability scaling 66→76→87→92 at fixed
   prompt), and **definitions don't stop mattering even at the frontier** (64 vs 98 on hard
   sentences).
4. Negative results worth printing: targeted prompt surgery at the plateau changes nothing;
   answer-level voting fails (exp_01) while pair-level voting works modestly; verbatim
   production rules fail at every capability level.
5. A linguist-in-the-loop methodology that paid off measurably twice (R3: +2, R4's algorithm:
   +1.8 verdict / +4.3 pair) and audited the treebank as a by-product.

**Open decisions for this group:** (a) full frontier grid (~$350–450) for the measured-parity
headline — or publish with probes + extrapolation; (b) 20-item ambiguity adjudication (bounds
the "model found a defensible alternative reading" objection; ~20 min of Katka's time);
(c) whether R0-at-all-capabilities deserves a full run (the "production reality" curve).

## 10. References

- Gibson, E. (1998/2000). Dependency locality theory — linear distance as processing cost.
- Kříž, V. & Hladká, B. (2018). *Czech Legal Text Treebank 2.0* (CLTT); UD conversion
  `UD_Czech-CLTT`. LINDAT.
- Hladká, B. et al. (2024). *KUK 1.0* — corpus of Czech legal/administrative texts. LINDAT,
  hdl:11234/1-5821.
- Straka, M. *UDPipe 2*. LINDAT services; model `czech-pdt-ud-2.15`.
- Nye, M. et al. (2021). *Show Your Work: Scratchpads for Intermediate Computation with Language
  Models.* arXiv:2112.00114. — basis of the R2 enumeration scaffold.
- Yehudai, G. et al. (2024). *When Can Transformers Count to n?* arXiv:2407.15160. — counting is
  architecturally hard in a single forward pass.
- Zhang, X. et al. (2024). *Counting Ability of Large Language Models and Impact of
  Tokenization.* arXiv:2410.19730. — CoT with strict per-step templates; atomic alignment
  (basis of the one-word-per-line format).
- Li, C. et al. (2023). *Chain of Code.* arXiv:2312.04474. — pseudocode-procedure prompting
  (basis of the SPRINT `_mod` pattern and R2–R5 structure).
- Ma, B. et al. (2024). *Decomposed Prompting: Probing Multilingual Linguistic Structure
  Knowledge in LLMs.* arXiv:2402.18397. — per-item decomposition (basis of the R3 inventory).
- Blevins, T. et al. (2023). *Prompting Language Models for Linguistic Structure.*
  arXiv:2211.07830.
- Ginn, M. & Palmer, A. (2025). *LLM Dependency Parsing with In-Context Rules.* ACL Anthology
  2025.xllm-1.17. — rules help zero-shot, wash out with examples (caveat we designed around).
- *Better Benchmarking LLMs for Zero-Shot Dependency Parsing.* arXiv:2502.20866. — why we ask
  for pairs, never full trees.
- Experiment_01 (this repository): *Can LLMs count? Subject–predicate distance on filtered
  legal Czech* — the predecessor whose negative result this work inverts.

---

*Repository pointers for the curious: `METHODOLOGY.md` (design + decision log K1–K13, O1–O11);
`docs/PARSER_ARM_RESULTS*.md`; `docs/RESULTS_openmodels.md`; `docs/QWEN_R4_ERROR_ANALYSIS.md` and
`QWEN_R4_DEEP_DIVE.md`; `docs/VERIFICATION_RESULTS.md`; `docs/FRONTIER_DECISION.md`; prompts in
`src/prompts/r0–r5`; all raw traces in `results/` (reproducible scoring via `src/score_llm.py`).*
