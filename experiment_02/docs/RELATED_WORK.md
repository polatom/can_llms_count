# Related work — working notes (experiment_02)

Purpose: literature grounding for the two rule formulations (R1/R2, METHODOLOGY §5.2) and raw
material for the paper's related-work section. Each entry: what it shows → why it matters here.
Status: working draft; verify venues/versions at citation time.

## Thread A — can LLMs count, and what makes them count better

- **Yehudai et al., *When Can Transformers Count to n?*** ([arXiv:2407.15160](https://arxiv.org/abs/2407.15160)) —
  theory + experiments: exact counting in a single forward pass breaks once vocabulary exceeds
  embedding dimension; SOTA pretrained models show the predicted failures. → Counting failure is
  architectural, not a knowledge gap; motivates scaffolds rather than better instructions.
- **Zhang et al.(?), *Counting Ability of LLMs and Impact of Tokenization*** ([arXiv:2410.19730](https://arxiv.org/abs/2410.19730)) —
  without CoT, transformers are constant-depth (TC⁰), while counting needs depth growing with
  length; CoT alleviates this, **but only with strict step templates** (explicit counter at each
  step); free-form CoT skips steps; token/format alignment (one item per step) is critical. →
  Direct design spec for R2's enumeration pass (`i: word` lines, running counter).
- **Nye et al., *Show Your Work: Scratchpads for Intermediate Computation***
  ([arXiv:2112.00114](https://arxiv.org/abs/2112.00114)) — emitting intermediate steps
  dramatically improves multi-step computation (long addition, program execution). → The
  foundational result behind the R2 scaffold.
- **Li et al., *Chain of Code*** ([arXiv:2312.04474](https://arxiv.org/abs/2312.04474)) —
  pseudocode that the LM "executes" stepwise (LMulator) beats plain CoT (+12% BBH). → Validates
  the pseudocode-procedure style of the SPRINT `_mod` rule and R2.
- **THINK-AND-EXECUTE / *Language Models as Compilers*** ([review](https://liner.com/review/language-models-as-compilers-simulating-pseudocode-execution-improves-algorithmic-reasoning)) —
  task-level pseudocode + simulated execution outperforms CoT/PoT on algorithmic reasoning. →
  Same mechanism, independent confirmation.
- **Enumeration-first prompting** ([arXiv:2603.29943](https://arxiv.org/html/2603.29943v2)) —
  enumerate instances (with distinguishing detail), deduplicate, then count: consistently improves
  counting accuracy and MAE. → Recent confirmation of enumerate-then-count ordering.
- ***The Genius Paradox*** ([ResearchGate](https://www.researchgate.net/publication/392503679_LLM_The_Genius_Paradox_A_Linguistic_and_Math_Expert's_Struggle_with_Simple_Word-based_Counting_Problems)) —
  word-based counting failures persist in models that excel at math benchmarks. → Framing:
  benchmark skill ≠ counting reliability.
- **Exp_01 internal evidence** (this repo, `experiment_01/`) — counting, not naming, is the
  bottleneck (~28–36% miscount given correct endpoints at 70B); self-generated token enumeration
  (the CoNLL-U regime) nearly doubled counting-given-naming (qwen-72b 33.5→65.8%) despite being
  unstable overall. → The mechanism R2 isolates was already visible in our own traces.

## Thread B — prompting LLMs for linguistic structure (POS / subjects / parsing)

- **Blevins et al., *Prompting Language Models for Linguistic Structure***
  ([arXiv:2211.07830](https://arxiv.org/abs/2211.07830)) — structured prompting (tag-per-token,
  iterative) elicits POS/NER/chunking from LLMs; format matters as much as knowledge. → Baseline
  technique for identification-style outputs.
- **Decomposed Prompting for multilingual linguistic structure**
  ([arXiv:2402.18397](https://arxiv.org/html/2402.18397v2)) — decomposing sequence labeling into
  per-item questions beats iterative prompting on UD POS across 38 languages, zero/few-shot. →
  Supports R2's step decomposition (predicates first, then subjects, then positions).
- **Ginn & Palmer, *LLM Dependency Parsing with In-Context Rules***
  ([ACL Anthology 2025.xllm-1.17](https://aclanthology.org/2025.xllm-1.17/)) — LLM-generated or
  human annotation-guideline rules in-context improve **zero-shot** parsing on 8 low-resource UD
  languages, but the benefit **disappears with a few labeled in-context examples**. → Caution for
  R2: definitions+rules may matter less than good worked examples; our R1-vs-R2 contrast varies
  both together (deliberately — R2 is "the best rule a lawyer could write", not a factorized
  ablation), and the paper should say so.
- **Better Benchmarking LLMs for Zero-Shot Dependency Parsing**
  ([arXiv:2502.20866](https://arxiv.org/html/2502.20866v1)) — SOTA LLMs remain weak at full
  parsing even with careful prompts; evaluation format pitfalls inflate/deflate results. →
  Supports our choice to ask for *pairs only*, never full trees (exp_01 already showed
  self-CoNLL-U is the least stable regime), and to validate output format deterministically.
- **Arabic morphosyntactic tagging & parsing with LLMs**
  ([arXiv:2603.16718](https://arxiv.org/pdf/2603.16718)) — example selection/ordering dominates
  few-shot performance on morphologically rich language structure tasks. → Freeze few-shot
  examples once (smoke test only), document selection.
- **LLM-based UD annotation for code-switched/low-resource text**
  ([arXiv:2506.07274](https://arxiv.org/html/2506.07274v1)) — LLMs as annotators for UD in hard
  settings: usable but error patterns differ from parsers. → Adjacent support for exp_03's
  complementarity question.
- **PoS tagging evaluation (PROPOR 2024)**
  ([ACL Anthology 2024.propor-1.46](https://aclanthology.org/2024.propor-1.46.pdf)) — LLM POS
  tagging still lags fine-tuned taggers for morphology-rich languages. → Sets expectations for
  identification accuracy ceilings in Czech.

## Thread C — task context (to merge with co-authors' draft bibliography)

- Dependency distance & processing load (Gibson DLT; Liu MDD line) — already covered in the paper
  draft's intro; K5 threshold (T = 6) comes from PONK practice.
- Czech word order, subject/predicate identification, garden paths — Katka's §4 in the draft
  (Zikánová, Uhlířová, Radimský refs live in `paper/latex/custom.bib`).
- exp_01 write-up (this repo) — the "LLMs can't count" result this experiment extends.

## Gaps to fill before submission

- Czech-specific LLM syntax evaluations (BenCzechMark? Czech GLUE-style suites) — quick pass.
- Any 2025/2026 work on LLM counting *scaffolds* specifically for linguistic distance metrics
  (nothing found so far — if that holds, novelty claim for R2-on-distance stands).
- Verify the arXiv:2603.* entries' final venues (very recent).
