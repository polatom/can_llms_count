**Literature Review: Relevant Academic Papers**

I performed targeted, multi-query searches across web results, arXiv, ACL Anthology, OpenReview, Nature, and related sources for topics including LLM counting/arithmetic limitations, structured/syntactic prompting (CoNLL-U/dependency parsing), dependency distance/syntactic complexity (esp. subject-predicate), Czech legal parsing (UDPipe/CLTT), and hybrid LLM+structure approaches. Below are the **most directly relevant papers** (prioritized for fit to your experiment; exhaustive but filtered to high-relevance ones, ~8 core). Each includes:

- Quick summary of relevance to *your* setup (RQ1–3, H1–H4, silver standard, proxy task for SPRINT counting rules, hybrid implications).
- Download link (prefer open/arXiv/ACL PDF where available; some Nature may require institutional access but often OA).

### LLM Counting / Exact Computation Limitations (Core Motivation for Proxy Task + "Can't Reliably Count" Narrative)
These directly back your use of linear token distance as a minimal, objective probe of LLM reliability on exact counting (independent of heavy semantics/knowledge). They show pattern-matching failures, off-by-one, abrupt collapse on extended counts, tokenization sensitivity, and finite internal states — aligning perfectly with H4 (degrades with length) and the SPRINT "counting rules" framing (e.g., para limits, future complexity).

- **Dai, T. & Fan, J. (2026). Language models fail at extended rule following.** arXiv:2605.02028.  
  *Relevance*: Introduces "Stable Counting Capacity" as a *minimal probe* for reliable rule-following in LLMs (exactly your framing of subject-predicate distance as narrow proxy for broader SPRINT counting/structural rules). All models fail beyond model-specific thresholds (finite internal "count states" exhaust → abrupt guessing); persists despite scale, CoT, or tools. Strongly supports silver-only design + explicit limitations (we measure agreement with UDPipe, not truth) and H3/H4. Perfect citation for "counting as probe of LLM reliability."  
  **Download**: https://arxiv.org/abs/2605.02028 (PDF: https://arxiv.org/pdf/2605.02028)

- **"Counting Ability of Large Language Models and Impact of Tokenization" (2024).** arXiv:2410.19730.  
  *Relevance*: Tokenization choices dramatically affect LLM counting performance. Directly relevant because your distance is *token-linear count* and KUK legal texts have noted artifacts (hyphenation, OCR, sentence boundaries per your data inspection). Suggests post-hoc analysis of errors vs. tokenization issues.  
  **Download**: https://arxiv.org/abs/2410.19730

- **"Why Do Large Language Models (LLMs) Struggle to Count Letters?" (2024).** arXiv:2412.18626.  
  *Relevance*: Documents persistent failures on simple character/token counting (e.g., "r" in "strawberry" analogs); not just frequency but operation complexity. Analogous to your exact distance calc; supports that raw-text regime (regime 1) will underperform and structure (CoNLL-U) may help bypass token issues.  
  **Download**: https://arxiv.org/abs/2412.18626

- **"Can Large Language Models Help with Model Counting?" (2024/2025).** OpenReview.  
  *Relevance*: LLMs struggle with exact counting problems (fragile to encoding changes) but improve markedly when *generating code* to compute counts. Directly bolsters your hybrid SPRINT recommendation (LLM for higher-level judgment + deterministic extractor for distance from parse) and H3 (structure compensates).  
  **Download**: https://openreview.net/forum?id=JZCgbU8irx

### LLM + Structured/Syntactic Input (CoNLL-U, Rules, Dependency Parsing)
These validate testing regimes 2 vs. 3 (self-generated vs. given CoNLL-U/structure) and show symbolic rules/contexts boost LLM performance on parsing-like tasks, especially zero/few-shot.

- **Ginn, M. & Palmer, A. (2025). LLM Dependency Parsing with Symbolic Rules (or In-Context Rules).** ACL Anthology (XLLM Workshop @ ACL 2025).  
  *Relevance*: Two-stage paradigm: LLM generates symbolic rules from examples → uses them for UD parsing (CoNLL-U-like output: ID, word, head, relation). Rules/contexts significantly improve zero-shot UAS/LAS; benefit diminishes with more examples. Validates your CoNLL-U-given regime and hybrid symbolic+LLM prompting for syntactic/structural tasks. Failure modes (overgeneralization) useful for your error taxonomy.  
  **Download**: https://aclanthology.org/2025.xllm-1.17.pdf (or anthology page)

- Related: Papers on U-DepPLLaMA / LLM-based UD parsing (various 2024–2025) show LLMs can produce CoNLL-U-style output but benefit from structure/rules. (Search "U-DepPLLaMA" or "LLM Universal Dependency Parsing" for arXiv variants.)

### Dependency Distance as Syntactic Complexity / Cognitive Load Metric
Validates your distance definition (linear |p-q|-1 between subject/predicate or head-dependent) as established proxy for complexity/working memory load — ties directly to SPRINT cognitive-complexity rules and legal text readability.

- **Gao, N. & He, Q. (2024). A dependency distance approach to the syntactic complexity variation in the connected speech of Alzheimer’s disease.** *Humanities and Social Sciences Communications* (Nature).  
  *Relevance*: Defines dependency distance exactly as linear positional distance between syntactic head and dependent (includes nsubj/subject-predicate relations). Mean dependency distance (MDD) measures complexity/working memory load; shorter distances = simplified structures under cognitive deficit. Your subject-predicate distance is a targeted, automatable instance. Supports H4 and framing as cognitive proxy for legal drafting (long embedded sentences in law increase load).  
  **Download**: https://www.nature.com/articles/s41599-024-03509-0 (open access version available)

### Czech Legal Parsing Resources (CLTT / UDPipe QC)
Confirms your CLTT-based parser-quality control step is not only feasible but standard (CLTT was created precisely for legal-domain parser eval).

- **Kríž, V. & Hladká, B. (2018). Czech Legal Text Treebank 2.0.** LREC 2018 (and related 1.0/UD conversion papers).  
  *Relevance*: The exact manual gold treebank (1,121 sentences, legal domain from Czech laws) underlying UD_Czech-CLTT. Used for parser accuracy (incl. nsubj/root). Directly justifies running UDPipe on CLTT for your silver-noise-floor estimate (nsubj-F1, distance agreement).  
  **Download**: https://aclanthology.org/L18-1713.pdf (or L16-1378 for 1.0); UD treebank: https://universaldependencies.org/treebanks/cs_cltt/index.html + GitHub (PML/Treex formats noted**Literature Review: Relevant Academic Papers**

I performed targeted, multi-query searches across web results, arXiv, ACL Anthology, OpenReview, Nature, and related sources for topics including LLM counting/arithmetic limitations, structured/syntactic prompting (CoNLL-U/dependency parsing), dependency distance/syntactic complexity (esp. subject-predicate), Czech legal parsing (UDPipe/CLTT), and hybrid LLM+structure approaches. Below are the **most directly relevant papers** (prioritized for fit to your experiment; exhaustive but filtered to high-relevance ones, ~8 core). Each includes:

- Quick summary of relevance to *your* setup (RQ1–3, H1–H4, silver standard, proxy task for SPRINT counting rules, hybrid implications).
- Download link (prefer open/arXiv/ACL PDF where available; some Nature may require institutional access but often OA).

### LLM Counting / Exact Computation Limitations (Core Motivation for Proxy Task + "Can't Reliably Count" Narrative)
These directly back your use of linear token distance as a minimal, objective probe of LLM reliability on exact counting (independent of heavy semantics/knowledge). They show pattern-matching failures, off-by-one, abrupt collapse on extended counts, tokenization sensitivity, and finite internal states — aligning perfectly with H4 (degrades with length) and the SPRINT "counting rules" framing (e.g., para limits, future complexity).

- **Dai, T. & Fan, J. (2026). Language models fail at extended rule following.** arXiv:2605.02028.  
  *Relevance*: Introduces "Stable Counting Capacity" as a *minimal probe* for reliable rule-following in LLMs (exactly your framing of subject-predicate distance as narrow proxy for broader SPRINT counting/structural rules). All models fail beyond model-specific thresholds (finite internal "count states" exhaust → abrupt guessing); persists despite scale, CoT, or tools. Strongly supports silver-only design + explicit limitations (we measure agreement with UDPipe, not truth) and H3/H4. Perfect citation for "counting as probe of LLM reliability."  
  **Download**: https://arxiv.org/abs/2605.02028 (PDF: https://arxiv.org/pdf/2605.02028)

- **"Counting Ability of Large Language Models and Impact of Tokenization" (2024).** arXiv:2410.19730.  
  *Relevance*: Tokenization choices dramatically affect LLM counting performance. Directly relevant because your distance is *token-linear count* and KUK legal texts have noted artifacts (hyphenation, OCR, sentence boundaries per your data inspection). Suggests post-hoc analysis of errors vs. tokenization issues.  
  **Download**: https://arxiv.org/abs/2410.19730

- **"Why Do Large Language Models (LLMs) Struggle to Count Letters?" (2024).** arXiv:2412.18626.  
  *Relevance*: Documents persistent failures on simple character/token counting (e.g., "r" in "strawberry" analogs); not just frequency but operation complexity. Analogous to your exact distance calc; supports that raw-text regime (regime 1) will underperform and structure (CoNLL-U) may help bypass token issues.  
  **Download**: https://arxiv.org/abs/2412.18626

- **"Can Large Language Models Help with Model Counting?" (2024/2025).** OpenReview.  
  *Relevance*: LLMs struggle with exact counting problems (fragile to encoding changes) but improve markedly when *generating code* to compute counts. Directly bolsters your hybrid SPRINT recommendation (LLM for higher-level judgment + deterministic extractor for distance from parse) and H3 (structure compensates).  
  **Download**: https://openreview.net/forum?id=JZCgbU8irx

### LLM + Structured/Syntactic Input (CoNLL-U, Rules, Dependency Parsing)
These validate testing regimes 2 vs. 3 (self-generated vs. given CoNLL-U/structure) and show symbolic rules/contexts boost LLM performance on parsing-like tasks, especially zero/few-shot.

- **Ginn, M. & Palmer, A. (2025). LLM Dependency Parsing with Symbolic Rules (or In-Context Rules).** ACL Anthology (XLLM Workshop @ ACL 2025).  
  *Relevance*: Two-stage paradigm: LLM generates symbolic rules from examples → uses them for UD parsing (CoNLL-U-like output: ID, word, head, relation). Rules/contexts significantly improve zero-shot UAS/LAS; benefit diminishes with more examples. Validates your CoNLL-U-given regime and hybrid symbolic+LLM prompting for syntactic/structural tasks. Failure modes (overgeneralization) useful for your error taxonomy.  
  **Download**: https://aclanthology.org/2025.xllm-1.17.pdf (or anthology page)

- Related: Papers on U-DepPLLaMA / LLM-based UD parsing (various 2024–2025) show LLMs can produce CoNLL-U-style output but benefit from structure/rules. (Search "U-DepPLLaMA" or "LLM Universal Dependency Parsing" for arXiv variants.)

### Dependency Distance as Syntactic Complexity / Cognitive Load Metric
Validates your distance definition (linear |p-q|-1 between subject/predicate or head-dependent) as established proxy for complexity/working memory load — ties directly to SPRINT cognitive-complexity rules and legal text readability.

- **Gao, N. & He, Q. (2024). A dependency distance approach to the syntactic complexity variation in the connected speech of Alzheimer’s disease.** *Humanities and Social Sciences Communications* (Nature).  
  *Relevance*: Defines dependency distance exactly as linear positional distance between syntactic head and dependent (includes nsubj/subject-predicate relations). Mean dependency distance (MDD) measures complexity/working memory load; shorter distances = simplified structures under cognitive deficit. Your subject-predicate distance is a targeted, automatable instance. Supports H4 and framing as cognitive proxy for legal drafting (long embedded sentences in law increase load).  
  **Download**: https://www.nature.com/articles/s41599-024-03509-0 (open access version available)

### Czech Legal Parsing Resources (CLTT / UDPipe QC)
Confirms your CLTT-based parser-quality control step is not only feasible but standard (CLTT was created precisely for legal-domain parser eval).

- **Kríž, V. & Hladká, B. (2018). Czech Legal Text Treebank 2.0.** LREC 2018 (and related 1.0/UD conversion papers).  
  *Relevance*: The exact manual gold treebank (1,121 sentences, legal domain from Czech laws) underlying UD_Czech-CLTT. Used for parser accuracy (incl. nsubj/root). Directly justifies running UDPipe on CLTT for your silver-noise-floor estimate (nsubj-F1, distance agreement).  
  **Download**: https://aclanthology.org/L18-1713.pdf (or L16-1378 for 1.0); UD treebank: https://universaldependencies.org/treebanks/cs_cltt/index.html + GitHub (PML/Treex formats noted in your meth — use udapi for conversion).

- Supporting: Straka et al. UDPipe papers (CoNLL 2017/2018) and evaluations mentioning CLTT as legal-domain test case (genre effects on accuracy).

**Other quick mentions** (lower priority but useful):
- General CoT/structured reasoning surveys (e.g., "Something-of-Thought in LLM Prompting") — support regime testing but less specific than above.
- Legal text complexity/simplification papers (e.g., on statutes, cross-references, RDF subject-predicate-object triples in legal ontologies) — tangential for SPRINT motivation but less syntactic than your distance metric.

These ~6–8 papers form a tight, citable core for the NLLP paper (motivation + related work sections). All are recent (2024–2026) and active areas.

**Assessment of Intent/Scope/Methodology (Incorporating Literature)**

**Overall Verdict**: Your methodology is **excellent — focused, rigorous, pragmatic, and strongly aligned with (and supported by) the literature**. It will produce a high-quality, actionable short NLLP paper with clear SPRINT engineering payoff. No major flaws; it's conservative where lit demands caution (LLM fragility on exact counts) and ambitious where justified (interaction hypothesis H3). The silver-only + trigger validation + explicit proxy framing is academically sound and avoids common pitfalls.

**Strengths (lit-backed)**:
- **Intent/Scope**: Perfectly scoped for a short whitepaper/proposal. Proxy task (subject-predicate distance) is narrow/objective/automated yet directly motivated by SPRINT (LPV §39(2) para counts + future cognitive complexity via nesting/distances/cross-refs, as in original attached doc). Explicitly states generalization limit ("predicts but does not prove" for other counting rules) — honest and lit-aligned (counting papers emphasize task-specific failures; dep-distance papers treat it as one complexity facet). H3 ("structure compensates for size") is the killer SPRINT takeaway and directly testable.
- **Hypotheses (H1–H4)**: Spot-on. H1/H3 supported by LLM dep-parsing + symbolic rules papers (structure/rules boost esp. zero/few-shot; CoNLL-U-given regime mirrors this). H2 (size) and H4 (length/depth degradation) backed by counting papers (abrupt failures on extended/long sequences; tokenization effects) + dep-distance lit (MDD increases with complexity/length; working memory load). Counting-as-probe papers (Dai & Fan) make your task a "minimal probe" — elegant framing.
- **Design & Analysis**: Within-sentence paired + mixed-effects regression is statistically powerful and controls confounds (length/depth per H4) — best practice. Metrics (exact/±1 match, MAE, consistency, error taxonomy) go beyond significance to engineering insights. Full-scale (not tiny pilot) is right given dataset size and NLLP needs.
- **Silver Standard Handling (§3, §7, §8)**: Transparent and correct. Lit on domain parsing (CLTT exists for legal Czech; UDPipe genre effects noted) justifies CLTT QC as noise-floor (nsubj-F1/distance agreement). "Agreement with UDPipe, not truth" caveat is essential and well-stated. Trigger-based human validation (on parser noise, ambiguous cases, or reviewer request) is pragmatic risk management — lit shows silver is common but noisy in specialized domains.
- **Threats (§8)**: Comprehensive and realistic (silver circularity mitigated; single-model-per-size named; filtering bias; proxy scope; prompt sensitivity). No overclaims.
- **Data/Filtering**: Self-consistent from UDPipe (necessary for silver-only) + logging exclusions (good descriptive stat on "simple" structures in legal Czech). Stratification by length + embedding depth directly tests H4 and matches dep-distance complexity lit.

**Minor Suggestions / Refinements from Lit Review** (none are blockers; for paper polish or Phase 1 tweaks):
- **Citations to add**: 1–2 from counting-probe lit (Dai & Fan 2026 for "minimal probe of rule reliability"; tokenization paper for legal artifacts). 1 from dep-distance (Gao & He 2024) to position your metric as established syntactic/cognitive complexity measure (strengthens SPRINT plain-language relevance). CLTT/UDPipe papers for QC step.
- **Tokenization interaction**: Legal KUK artifacts (hyphenation, boundaries) noted in your inspection — lit shows this hurts LLM counting. Easy post-hoc or note in threats/limitations.
- **Regime 2 (self-generated CoNLL-U)**: LLM dep-parsing papers show symbolic rules/contexts help (beyond plain few-shot). Your current few-shot is solid; could note "rule-augmented" as cheap future ablation or in discussion.
- **CLTT conversion (open item #6)**: Use `udapi` (Python, native PML support, lightweight) unless UFAL has a preferred Treex pipeline. Quick engineering task; aligns with your "small added step" note.
- **No contradictions**: Lit reinforces (doesn't undermine) silver-only conservatism, hybrid push, and length effects. Counting papers even suggest LLMs may be *better at generating code for counts* than computing them → strengthens deterministic extractor recommendation for SPRINT.
- **Timeline/Scale**: Full-scale + NLLP deadline alignment is realistic; lit shows these probes are cheap to run once harness exists.

**Bottom line**: The plan is ready to move to `extract_pairs.py` / harness. It will yield a convincing paper that advances both legal NLP (NLLP) *and* SPRINT practice. The literature confirms this is timely (active work on LLM counting fragility + structured prompting + domain parsing) and your choices (proxy task, silver + QC, interaction hypothesis, paired design) are well-motivated. Minor polish on citations/framing will make it even tighter.

If you want me to draft specific sections (e.g., Related Work paragraph with these cites), expand any paper summary, or help with implementation plan next, just say. Data inspection + this review gives a very solid foundation.