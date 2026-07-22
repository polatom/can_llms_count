# Can an LLM measure subject–predicate distance in Czech legal text?
## Preliminary report — experiment_04 (2026-07-22, draft for project colleagues)

*This report is written for colleagues who were not part of the day-to-day work; it tells the
whole story so that we can agree on a clean design for the paper. Everything is reproducible
from the repository (`experiment_04/`): every number traces back to stored raw model outputs,
and every design decision has a dated record. Results are essentially final; two small items
were completing at writing time and are marked as such.*

---

## 0. How to read this report — terms used throughout

- **Pair** — one (subject, predicate) couple in a sentence, with the **distance** = number of
  words strictly between them. A sentence can contain zero pairs (headings, fragments,
  clauses with unexpressed subjects) or many (one per finite clause with an overt subject).
- **Verdict** — the per-sentence decision a comprehensibility linter actually delivers:
  *violation* if **any** pair has distance > 6 (the PONK limit), else *clean*.
- **Precision / recall / F1** — for verdicts: *precision* = of the sentences the system flags,
  how many really are violations (low precision = many false alarms); *recall* = of the true
  violations, how many the system catches (low recall = misses); *F1* = the harmonic mean of
  the two, a single balance number. **Verdict F1** measures the flag quality; **pair F1**
  measures the underlying extraction quality (did the system find the same pairs as the gold
  standard — matching by the words of subject and predicate).
- **"Distance correct given found"** — among pairs the system did find, how often the counted
  distance is exactly right. This isolates *counting* skill from *finding* skill.
- **Formulation (R0–R5)** — a version of the rule text (the prompt). R0 is the production rule
  as deployed in SPRINT; R1–R5 are our successive rewrites (full texts in Appendix A).
- **Scaffold** — prompt structure that walks the model through explicit steps (e.g., "number
  the words one per line, then read positions off your own numbering") instead of asking for
  the answer directly.
- **Pass / run** — every configuration was executed **three times** over the whole corpus
  (temperature 0, fixed provider). Differences between passes measure the model's
  *instability*; combining passes is **ensembling** (e.g., **majority vote**: keep a pair if it
  appears in at least 2 of 3 passes).
- **Parser arm / LLM arm** — the two competing implementations: deterministic (UDPipe parser +
  hand-written extraction code) vs. pure LLM (rule text as prompt, sentence in, JSON out, no
  other machinery).
- **Gold / silver / derived gold** — *gold* = human-verified truth; *silver* = automatic
  (parser-produced) approximation. Our gold is *derived*: the agreed linguistic rule applied to
  human-annotated syntax trees, then independently verified by an expert (see §2).
- **hard-104** — the 104 sentences (of 1,121) on which the best open-model configuration is
  *systematically* wrong (wrong verdict in at least 2 of its 3 passes). We use it as a cheap
  probe set: any model that solves these solves precisely what the open model cannot.

## 1. Background and the question

Long spans between a subject (podmět) and its predicate (přísudek) burden the reader's working
memory; the distance between them is a validated indicator of poor comprehensibility in legal
Czech (dependency-locality literature, Gibson 1998/2000). PONK operationalizes this as: **flag
any sentence in which some subject–predicate pair has more than 6 words between them.**

The SPRINT application evaluates such rules by sending each sentence, together with the rule
written *as prose by lawyers*, to an LLM. This is wonderfully cheap to author — no programmers
involved — but the production distance rule performed poorly, which started this project.

**Experiment_01** (2026-07, this repository) diagnosed the failure on a filtered, simplified
version of the task: LLMs could often *name* the right subject and predicate but systematically
**miscounted** the span between them (28–36% wrong even when handed a syntactic parse), and the
errors could not be prompted, sampled, or voted away. The obvious engineering alternative —
UDPipe parser plus a hand-written extraction script — is accurate but is *per-rule code*: it
must be programmed, only exists for phenomena a parser exposes, and can't be maintained by the
lawyers who own the rules.

**Experiment_04 asks the practical question directly:** can a *pure-LLM rule* — raw sentence
in, verdict out, no pre-processing, no post-processing, deployable in today's SPRINT by editing
rule text — match the deterministic parser pipeline on realistic, unfiltered legal text? And
what does the answer depend on? We vary exactly two things:

- **model capability**: open-weights 27B → 72B → 235B → mid-frontier → frontier, ± test-time
  reasoning;
- **rule formulation**: from the production rule verbatim (R0) to successively engineered
  versions (R1–R5), each targeting the measured failure of the previous one.

## 2. Data and the gold standard

**Corpus.** The whole `cs_cltt` treebank — the Universal Dependencies conversion of the Czech
Legal Text Treebank (CLTT 2.0, Kříž & Hladká 2018): **1,121 human-annotated sentences** of real
Czech statutes (accounting law). Deliberately **unfiltered**: multi-clause sentences,
enumeration "monsters" up to 466 words, verbless headings — everything a deployed linter meets.
Median sentence 22 words; 26% of sentences contain no pair at all; the mean is 1.44 pairs per
sentence; 17.3% of sentences are true violations (194 of 1,121) — enough statistical power to
distinguish systems ~3–4 F1 points apart.

**The linguistic definition.** What exactly counts as "the predicate" (and subject) was
developed with and signed off by Katka across thirteen recorded decisions (K1–K13). The
essentials: the measured predicate is the **agreement-bearing element** — the finite verb; the
auxiliary in analytic forms (including the participial *byla* in past passives and past
copulas, an easy-to-miss case); the copula, never the nominal part; and in *aby/kdyby* clauses
the conjunction itself, because it absorbs the conditional auxiliary (*abych = aby + bych*).
Coordinated predicates sharing one subject count **once**. Verbless clauses have no pair.
Relative pronouns are subjects of their clauses — subject to a case-elimination test (Katka's
algorithm, §5/R4). Quantified subjects (*dvanáct měsíců*) measure to the nominative quantifier.

**Deriving and verifying the gold.** Applying this definition mechanically to the human
syntax trees yields **1,617 gold pairs**. Because the trees are human-made, no parser
contaminates the gold — but the *derivation rule* could be wrong, so it was verified: Katka
(an expert linguist who is **not** a CLTT author — this is independent, external verification)
reviewed 24 worked examples covering every construction type, then a stratified sample of 105
derived pairs. Result: **104/105 confirmed, 1 genuinely ambiguous, 0 outstanding errors** after
one fix. The exercise also uncovered two errors in the *treebank itself* that our gold had
inherited — fused conditional verbs (*Nestanoví-li*) systematically mis-tagged as nouns (31
silently missing pairs), and one quantified-subject convention divergence — both repaired.
A finding worth savoring: **the LLM's "false positives" audited the human annotation** — chasing
model–gold disagreements is what led us to both treebank bugs.

## 3. The deterministic baseline (parser arm)

UDPipe 2 parses the raw sentence text; our extraction code (the same §2 definition) reads pairs
off the parse; the verdict follows. Two configurations, an instructive contrast:

| configuration | verdict F1 | pair F1 | distance correct given found |
|---|--:|--:|--:|
| UDPipe default (re-segments sentences itself) | 91.3 | 92 | 99.8% |
| **UDPipe told the unit is one sentence** | **97.1** (precision 97.9, recall 96.4) | **96.5** | 99.8% |

Lessons. (1) Experiment_01's celebrated "99.3% parser accuracy" was an artifact of easy,
filtered sentences — on unfiltered statutes the honest number is **97.1**, and the parser's
errors are entirely *lost pairs* (never mismeasured ones). (2) Its biggest weakness was not
parsing but **sentence segmentation**: left to its own segmenter, UDPipe cuts long statutes
mid-clause and loses the pairs that straddle the cut — six F1 points recovered by one
configuration flag (deployments know their unit boundaries anyway). (3) The parser is
deterministic — zero variance, effectively zero cost — but remains per-rule engineering.

## 4. The formulation ladder: what prompt engineering buys

We wrote five successive versions of the rule and ran each as a full three-pass grid on
**Qwen-2.5-72B** (the strongest open model from experiment_01; "72B" below). Every version
targeted the *measured* dominant error of its predecessor — this is the part of the project
where the linguist was in the loop, and it shows. Full prompt texts: **Appendix A**.

| formulation | what changed (one line) | verdict F1 (72B) |
|---|---|--:|
| R1 "best naive" | complete linguistic definitions + solved examples; no procedure | 58.5 |
| R2 "procedural" | + explicit steps and the **self-enumeration counting scaffold**: the model must number the words one per line, then *read positions off its own numbering* | 72.5 |
| R3 "inventory" | + **per-word category sweep** with closed word lists (all forms of *být*, all *aby/kdyby* words) — replaces grammatical abstractions with string tests a smaller model can execute | 74.7 |
| R4 "pairing rules" | + **Katka's case-elimination algorithm** for relative pronouns, the preposition test, one-pair-per-predicate | **76.5** |
| R5 "precision surgery" | + three rules aimed at the residual error classes | 76.0 — **plateau** |

Why each step worked (or didn't), in plain terms:

- **R1 → R2 (+14 points): counting was the disease, structure the cure.** With R1 the model
  finds a pair and then simply *guesses* the distance — only ~30% of found pairs got the exact
  distance. The R2 scaffold externalizes the count into text the model can re-read: distance
  accuracy on found pairs jumps to **95–97%**, where it stays for all later versions. This
  replicates the scratchpad/chain-of-thought-counting literature (Nye et al. 2021; Zhang et
  al. 2024) and *closes experiment_01's core deficit with prompt text alone*. A curiosity: the
  model's reported word *positions* are wrong about half the time (a constant offset slips into
  its numbering), but the *difference* survives — right distance, wrong coordinates.
- **R2 → R3 (+2 overall, but identification recall 50%→64%):** Katka's hypothesis was that
  mid-size models "don't have enough linguistics" to apply categories like *auxiliary* —
  so R3 replaces categories with elementary tests (closed lists, "can you put *on/oni* before
  it?"). Identification improved substantially; the overall gain was smaller because the extra
  found pairs were imprecisely paired.
- **R3 → R4 (+1.8 verdict, +4 pair F1):** Katka's elimination algorithm for relative pronouns
  (is *které* the subject, or is there another preposition-free nominative in the clause?)
  fixed a whole error class we had measured (her rule, our error data — the collaboration's
  best moment).
- **R4 → R5 (nothing): the ceiling, measured.** R5 added explicit counter-rules against the
  three remaining error classes, each with dedicated examples — and *changed nothing* (76.5 →
  76.0). At 72B the model reads the rule, demonstrably contains it, and errs anyway. This
  negative result matters: prompt engineering has a floor it cannot dig below, and we know
  where it is.

## 5. Where the 72B still fails — anatomy of the residual

Break the task into a funnel over the 1,617 gold pairs (R4, three passes pooled):

| stage | success rate |
|---|--:|
| the predicate word appears in some pair the model emitted | 92.5% |
| the full pair is correct (right subject *and* predicate) | 76.1% |
| the distance is exactly right, among correct pairs | 95.0% |

So the residual problem is **not counting** (solved) and **not finding predicates** (nearly
solved) — it is **pairing**: choosing the right subject for a found predicate, and inventing
pairs that don't exist. The fabricated pairs cluster in three linguistically coherent classes:

1. **Cross-clause borrowing.** In a subordinate clause with an unexpressed subject (*"…, pokud
   neslouží k podnikání"*), the model borrows the subject of the main clause. Linguistically
   the coreference is even true — but the task counts only overt, same-clause subjects, and
   the borrowed pair often crosses the distance threshold, producing a false flag.
2. **Instrumental bait.** In the definitional pattern beloved by Czech statutes —
   *"**Komponentou** se rozumí určená část…"* — the fronted instrumental noun gets picked as
   subject; the real subject is the postposed nominative (*část*). Morphologically unambiguous,
   yet persistent.
3. ***aby*-convention slips.** The model pairs the subject with the content verb inside an
   *aby* clause instead of the conjunction, inflating the distance (e.g., 11 instead of 6 —
   a false flag exactly at the threshold).

Two properties of these errors shaped everything after: they are **systematic** — the same
fabricated pair recurs in all three passes (31% of fabrications are perfectly stable), which is
why **majority-vote ensembling helps only modestly** (76.5 → **78.3** verdict F1; keep pairs
appearing in ≥2 of 3 passes) and more repetitions cannot help further. And they resisted
explicit textual counter-rules (the R5 null result). For a recall-first deployment, the numbers
are friendlier: single-pass verdict recall is **93.5%** (the parser: 96.4%), and false flags
concentrate on long sentences (flagged-but-clean sentences average 49 words vs. 22 for true
negatives) — a false alarm usually lands on text an editor might want to re-read anyway.

## 6. The capability axis: same rule, smarter models

Fixing the formulation at R4 and varying only the model (full three-pass grids):

| model | class | verdict F1 | pair F1 |
|---|---|--:|--:|
| gemma-3-27B | open weights | 66.5 | 58.6 |
| Qwen-2.5-72B | open weights | 76.5 | 67.4 |
| Qwen3-235B-Instruct | open weights | **87.2**† | 78.1 |
| gpt-5-mini | mid-frontier API | **92.3** | 73.4 |
| *parser (UDPipe + code)* | deterministic | **97.1** | 96.5 |

† third pass completing at writing time (first two passes: 86.4 / 86.5).

Above 72B, capability — not prompt wording — is the dominant dial. Notably, a **$0.25-per-
million-token mid-frontier model lands within five points of the parser**, and the open-weights
family alone climbs 66 → 76 → 87 with the identical prompt.

## 7. Frontier probes: cheap answers to two expensive questions

A full frontier grid costs $350–450, so before asking for that budget we probed the **hard-104**
(see §0: the sentences the 72B systematically gets wrong) with gpt-5.1 — single passes, $1–10
each. Two questions:

**(a) Is the residual gap capability-bound?** Yes. On sentences chosen *because* the open model
fails them, the frontier with reasoning solves **98%** (102/104; zero false flags; pair
precision 94% / recall 96%). Without reasoning: 88%. The fabrication classes of §5 essentially
vanish with capability; test-time reasoning adds the last mile.

**(b) Does the frontier still need our prompt engineering?** Split verdict — and this is
perhaps the most useful finding of the project:

| rule given to gpt-5.1 (reasoning on) | correct on hard-104 | pairs P / R |
|---|--:|--:|
| **R0 — the production rule verbatim** | **64%** (37 false flags) | 53 / 47 |
| R1 — full definitions, no scaffold | 95% | 94 / 92 |
| R4 — definitions + scaffold | 98% | 94 / 96 |

**Capability subsumes the *scaffold* (worth ~3 points at the frontier) but not the
*definitions* (worth ~31 points).** Even the strongest model over-flags wildly when handed the
underspecified production rule — which is also the controlled post-mortem of the original
SPRINT experience: the rule text and the model capability were each half of the problem.

*(Methodological footnote that cost us one invalid probe: reasoning models silently truncate
when the output budget is too small — at a 6k-token cap, 76 of 104 responses were empty and
"no violation" was parsed out of silence. All probe results above are from the corrected,
validity-checked rerun.)*

## 8. Robustness: a second corpus

Because `cs_cltt` is public (a conceivable training-data contamination for the models), the best
open configuration was re-run on **640 unfiltered sentences of a different legal-administrative
corpus** (KUK/ESO — ombudsman statements; no human gold there, so we measure *agreement with the
parser pipeline* on identical text): agreement is **85.5%** on the unseen corpus vs. **90.3%**
on CLTT, with the same over-flagging signature on both (model flags ~2× as many sentences as
the parser, catching 80–94% of the parser's flags). A memorized test set would show a dramatic
gap, not five points explainable by domain shift. No memorization signal.

## 9. Deployment economics

- **One sentence per call, rule as a cached prefix.** SPRINT currently batches several
  sentences into one prompt per rule. We recommend the opposite: per-sentence calls (preserves
  the per-unit audit trail, fits SPRINT's differential re-evaluation, avoids cross-sentence
  interference — all our quality numbers hold only under this regime), with the static rule
  preamble (~2.6k tokens) served from **prompt cache**. Measured: on OpenAI, 97% of the prompt
  tokens came from cache with a 2.7× latency reduction and cached input billed at a fraction;
  on DeepInfra, no caching exists (self-hosted serving: enable prefix caching). The prefix must
  be byte-identical and precede the variable sentence — our template layout already complies.
- **Costs.** Everything in this report — five formulations × three passes on two open models,
  three more full model grids, five frontier probes, the second-corpus run, ~35,000 stored
  raw traces — cost **≈ $64** (experiment_01 added $7.73; UDPipe via LINDAT is free). A single
  pass over 1,121 sentences costs ~$1–2.50 for every non-frontier model tested.
- Optional knobs, both measured: majority-of-3 ensembling (+1.8 F1 at 3× cost); threshold
  shifting (trade recall for precision along a measured curve) if F1 rather than recall is the
  target.

## 10. Conclusions

### 10.1 General findings

1. **"LLMs can't count" is a prompt-structure problem, not a model problem.** The
   self-enumeration scaffold takes distance accuracy on found pairs from ~30% to 95–98% on
   every model tested — experiment_01's core deficit, closed with text alone.
2. **Identification is the real frontier, and it scales with capability, not with prompting.**
   Prompt engineering moved the 72B from 58.5 to 76.5 and then hit a measured ceiling (R5
   changed nothing; ensembling adds 1.8; the residual errors are systematic). The same prompt
   scales 66 → 76 → 87 → 92 across the capability axis, and the hard-case probe shows the
   frontier solving 98% of exactly what the 72B cannot.
3. **Definitions never stop mattering.** At frontier capability the scaffold is nearly
   redundant (+3), but precise linguistic definitions are worth +31 on hard sentences. The
   production rule fails at *every* capability level.
4. **The deterministic parser pipeline remains the accuracy champion** (97.1 verdict F1,
   zero variance, ~zero cost) — but its margin over a $0.25/M-token LLM is now five points,
   its errors concentrate in a configurable segmentation step, and it remains per-rule code.
5. **Derived-gold methodology works and pays dividends**: rule-on-human-trees + independent
   expert verification produced a 1,617-pair gold standard at ~1% measured error for about two
   hours of expert time — and the model-vs-gold disagreements audited the treebank itself,
   finding two annotation bugs.

### 10.2 Practical guide for SPRINT (counting-type rules)

- **Write rules at "Katka grade".** Precise, elementary-test definitions (closed word lists,
  case tests, explicit conventions for aby/kdyby, coordination, unexpressed subjects) are the
  single highest-leverage ingredient at every model size. The current production rule format
  (definition + a few conditions) is demonstrably insufficient *even for frontier models*.
- **Add the counting scaffold whenever the evaluating model is below frontier class**: force
  word-numbering before any distance is produced. It is free and removes the counting failure
  mode entirely.
- **Model choice by requirement:**
  - *usable recall today, open weights, on-premise*: Qwen3-235B-class → verdict F1 ~87,
    single-pass recall ~90+%, at ~$1/1k sentences;
  - *near-parser quality, API acceptable*: mid-frontier (gpt-5-mini-class) → F1 ~92;
  - *parser parity*: frontier + reasoning (expected ≈97, pending the full-grid confirmation);
  - *maximum accuracy and auditability, engineering available*: keep the deterministic
    pipeline — and configure segmentation to respect unit boundaries (six free points).
- **Serve it right:** one sentence per call; rule text as byte-identical cached prefix; prefer
  caching-capable serving (OpenAI/Anthropic APIs, or vLLM with prefix caching). Expect
  over-flagging rather than misses (precision ~63–68% at recall ~93% for open models) — in a
  suggestions-not-verdicts workflow (SPRINT's philosophy), false flags mostly land on long
  sentences worth an editor's look anyway.
- **Give reasoning models room:** small output budgets cause *silent* truncation that reads as
  "no violation". Budget generously and validate non-empty outputs.

### 10.3 Proposed paper design

- **Title direction:** *"Don't ask an LLM to count: prompt structure, capability, and the
  limits of prose rules for a syntactic comprehensibility metric in Czech legal text."*
- **One core figure:** verdict F1 (y) vs. model capability (x), one curve per formulation
  (R1/R4 at minimum), dashed parser line at 97.1 — every claim above is readable off it.
  Supporting exhibits: the funnel table (§5), the frontier probe matrix (§7), the gold
  verification summary (§2).
- **Contributions:** (i) the gold dataset + verification protocol (+ treebank fixes);
  (ii) the honest deterministic baseline on unfiltered text; (iii) the formulation ladder with
  its measured ceiling — including the negative results (R5 null, ensembling limits, R0
  failure at all capabilities); (iv) the capability×definition decomposition; (v) the
  linguist-in-the-loop method that produced R3/R4.
- **Fit with the existing draft:** Katka's free-word-order section motivates the
  identification difficulty (§5's error classes are its empirical payoff); the "Golden Truth
  Data" section becomes §2; the abstract's "LLMs and traditional tools together" question gets
  the quantified answer in §10.2.

### 10.4 Open decisions for this group

1. **Full frontier grid** (~$350–450): converts "expected ≈97" into a measured headline. The
   hard-104 probes have de-risked it; it is now a budget question, not a scientific gamble.
2. **Ambiguity adjudication** (~20 min of Katka's time): 20 model–gold disagreements to bound
   the "the model found a defensible alternative reading" objection (current estimate: ~1%).
3. **R0 at all capability levels** (~$10 on open models): completes the "production reality"
   curve for the paper's motivation section.

## 11. References

- Gibson, E. (1998). *Linguistic complexity: locality of syntactic dependencies.* Cognition
  68(1); Gibson, E. (2000). *The dependency locality theory.* — distance ↔ processing cost.
- Kříž, V. & Hladká, B. (2018). *Czech Legal Text Treebank 2.0* (CLTT), and its Universal
  Dependencies conversion `UD_Czech-CLTT`. LINDAT/CLARIAH-CZ.
- Hladká, B., Cinková, S., Kuk, M., Mírovský, J., Novotná, T., Nguyen Zahálková, K. (2024).
  *KUK 1.0* — corpus of Czech legal and administrative texts. LINDAT, hdl:11234/1-5821.
- Straka, M. *UDPipe 2* (model `czech-pdt-ud-2.15`). LINDAT services.
- Nye, M. et al. (2021). *Show Your Work: Scratchpads for Intermediate Computation with
  Language Models.* arXiv:2112.00114. — the enumeration-scaffold ancestor (R2).
- Yehudai, G. et al. (2024). *When Can Transformers Count to n?* arXiv:2407.15160. — why exact
  counting fails in a single forward pass.
- Zhang, X. et al. (2024). *Counting Ability of Large Language Models and Impact of
  Tokenization.* arXiv:2410.19730. — chain-of-thought counting needs strict per-step templates
  and atomically aligned formats (the one-word-per-line design).
- Li, C. et al. (2023). *Chain of Code: Reasoning with a Language Model-Augmented Code
  Emulator.* arXiv:2312.04474. — pseudocode-procedure prompting (the SPRINT `_mod` pattern,
  R2–R5 structure).
- Ma, B. et al. (2024). *Decomposed Prompting: Probing Multilingual Linguistic Structure
  Knowledge in LLMs.* arXiv:2402.18397. — per-item decomposition (the R3 inventory sweep).
- Blevins, T., Gonen, H., Zettlemoyer, L. (2023). *Prompting Language Models for Linguistic
  Structure.* arXiv:2211.07830.
- Ginn, M. & Palmer, A. (2025). *LLM Dependency Parsing with In-Context Rules.* ACL Anthology
  2025.xllm-1.17. — in-context rules help zero-shot but wash out with examples; we therefore
  varied definitions and examples together and said so.
- *Better Benchmarking LLMs for Zero-Shot Dependency Parsing* (2025). arXiv:2502.20866. — why
  we never ask models for full parse trees, only pairs.
- Experiment_01 (this repository, 2026-07): the filtered-task predecessor whose negative
  result ("LLMs can't count") this work decomposes and partially inverts.

---

## Appendix A — the six rule formulations (abridged; full texts in `src/prompts/`)

**A.0 — R0, the production rule (verbatim translation of the deployed SPRINT rule).**
> *Definice:* Identifikuje klauze, ve kterých jsou přísudek a podmět odděleny více než 6 slovy.
> *Podmínky:* (1) Existuje klauze, která obsahuje přísudek a podmět. (2) Přísudek a podmět jsou
> odděleny alespoň 7 slovy. (3) Pořadí přísudku a podmětu není rozhodující. (4) Přísudek a
> podmět jsou vzájemně závislé. *(+ two rewrite examples; no definition of subject, predicate,
> clause, or how to count.)*

**A.1 — R1 "best naive": complete definitions, no procedure.** Adds everything R0 lacks —
predicate = agreement-bearing element with per-construction examples (*bude rozhodovat →
bude; Zákon JE účinný → je; Spolupráce BYLA krátkodobá → byla; …, ABY se pes nemusel ohýbat →
aby*), overt-subject requirement with the pro-drop/fragment/coordination conventions, the
word/distance arithmetic — plus six solved examples. **No steps, no numbering: the model
answers directly.**

**A.2 — R2 "procedural": steps + the counting scaffold.** Same knowledge, restructured:
KROK 1 find finite clauses and their predicates; KROK 2 find overt subjects; **KROK 3 number
the words, one per line (`1: Zákon` …); KROK 4 read both positions off the numbering, subtract,
compare with 6.** The few-shot examples show the numbered listing in full.

**A.3 — R3 "inventory": per-word classification with closed lists.** KROK 1 becomes a sweep:
*for every word* decide — (a) finite verb ("can you put on/oni before it?"), (b) a form of
*být* (closed list: jsem, jsi, je, …, by, bych, jsou-li, …), (c) an *aby/kdyby* word (closed
list), (d) infinitive/participle belonging to a *být* form. Every (a)–(c) word must end up in
exactly one pair or be marked "unexpressed subject" — an accounting invariant that prevents
skipping clauses. Motivated by Katka's "not enough linguistics in small models" hypothesis:
replace grammatical categories with string tests.

**A.4 — R4 "pairing rules": Katka's algorithm.** Adds, verbatim from her answer: relative
pronoun forms that can never be nominative (*kterou, kterých, …*) are never subjects; for the
ambiguous forms (*který, která, které, jenž, jež, již*) scan the clause for another
preposition-free nominative — if found, *that* is the subject; a noun after a preposition
(even with adjectives in between) is never nominative; each predicate in at most one pair.
Plus one new solved example: *"…informace, které musí obsahovat výroční zpráva"* → the subject
of *musí* is *zpráva*, not *které*.

**A.5 — R5 "precision surgery" (the null result).** Three additions targeting §5's classes:
the instrumental test (*slovo v 7. pádě není podmět; u vazby "X-ou se rozumí Y" je podmětem
Y*), the hard same-clause rule (*a clause with an unexpressed subject has NO pair, even when
context makes the actor obvious*), and a self-check step that repairs aby-clause pairs onto
the conjunction and recomputes. Outcome: no measurable change at 72B — the documented ceiling
of prompt engineering at this capability level.
