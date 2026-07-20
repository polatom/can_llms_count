
## Q

How does udpipe work?

## A

**UDPipe** is a trainable, open-source pipeline (primarily from Charles University’s Institute of Formal and Applied Linguistics) for performing core natural language processing tasks on text: sentence segmentation, tokenization, part-of-speech (POS) tagging, lemmatization, and dependency parsing. It is designed around the **Universal Dependencies (UD)** framework and CoNLL-U format, making it language-agnostic and easy to train on annotated treebank data.

### Core Pipeline Stages
UDPipe processes text through these sequential (but integrated) components:

1. **Tokenizer / Sentence Segmenter** — Splits raw text into sentences and tokens. It uses a single-layer bidirectional GRU (Gated Recurrent Unit) neural network. It handles joint sentence segmentation and tokenization, including space markup (e.g., `SpaceAfter=No` in CoNLL-U).

2. **Tagger (Morphological Analysis + POS Tagging)** — Assigns Universal POS tags (UPOS), language-specific tags (XPOS), morphological features (FEATS), and lemmas. It relies on **MorphoDiTa** (an averaged perceptron-based tagger with a guesser for unknown words based on suffixes). Multiple models can be combined for different tag types.

3. **Dependency Parser** — Builds syntactic dependency trees using **Parsito**, a fast transition-based parser with a neural-network classifier. It predicts head words and dependency relations (DEPREL).

The pipeline supports input in raw text (which gets tokenized) or pre-tokenized formats like CoNLL-U, and outputs in CoNLL-U or other formats (plain text, vertical, etc.).

### How Models Work
- Each pre-trained model (`.udpipe` file) bundles a tokenizer, tagger, and parser trained on UD treebanks.
- Models are available for dozens of languages (50+ in UD 2.x releases).
- Training is straightforward using CoNLL-U files: `udpipe --train model.udpipe training.conllu`. You can train subsets of components (e.g., only the parser) and customize hyperparameters.

### Usage Examples
**Command-line (most common):**
```bash
# Full pipeline on raw text
udpipe --tokenize --tag --parse english-ewt-ud-2.5-191206.udpipe input.txt

# Or pipe text
echo "This is a test sentence." | udpipe --tokenize --tag --parse model.udpipe
```

**In code (e.g., Python via ufal.udpipe bindings):**
```python
from ufal.udpipe import Model, Pipeline, ProcessingError

model = Model.load("model.udpipe")
pipeline = Pipeline(model, "tokenize", Pipeline.DEFAULT, Pipeline.DEFAULT, "conllu")
result = pipeline.process("Your text here.")
```

### Key Strengths and Design
- **Efficiency** — Lightweight, fast, and low memory footprint compared to heavier neural models; good for production/baseline use.
- **Trainability** — No external data needed beyond CoNLL-U; supports custom models.
- **Bindings** — C++ core, with official bindings for Python, Java, Perl, C#, and community options (e.g., R package).
- **Output** — Rich CoNLL-U with lemmas, tags, features, heads, and relations.

**Note on Versions**: UDPipe 1.x (the widely used version described here) has detailed manuals. UDPipe 2 exists with improvements, but 1.x models and docs are still heavily referenced.

For full details, check the official site: [https://ufal.mff.cuni.cz/udpipe](https://ufal.mff.cuni.cz/udpipe), the user's manual, or the papers on CoNLL 2017/2018 shared tasks. It's excellent for multilingual baselines or when you need fast, trainable UD-compatible annotations.

## Q

I am interested only in predicate/subject identification in Czech (legal texts). Could ii use a specialized lower-level tool, maybe with additional finetuning? Is this task unequivocal or are there edge cases with ambiguities?

Is there a way i could make a midsize model (70B llama eg) to perform at similar level (ideally without finetuning)?

## A

**Yes — specialized lower-level tools are a strong fit for predicate/subject identification in Czech (especially legal texts), and the task has real ambiguities/edge cases.** A mid-size model like a 70B Llama can get reasonably close via prompting and hybrids, but pure zero/few-shot prompting without any domain adaptation or external tools is unlikely to fully match a well-tuned specialized parser on accuracy and consistency for complex legal sentences.

### Specialized lower-level tools
The most practical options are dependency parsers (or rule-based systems) that output explicit syntactic relations. Subjects are typically labeled `nsubj` (or `nsubj:pass`, `csubj`, etc.), and the predicate is usually the root or the main verbal head (including copular constructions).

- **UDPipe / UDPipe 2** (from ÚFAL, Charles University) is the strongest general recommendation. It is trainable, language-agnostic when given CoNLL-U data, provides full pipelines (tokenization → morphology/POS/lemmas → dependency parsing), and has solid Czech models trained on Prague Dependency Treebank (PDT) data, CAC, FicTree, and the **Czech Legal Text Treebank (CLTT)**.  
  Domain shift matters: a PDT-trained model drops noticeably on legal text (roughly mid-60s LAS in older evaluations), while a model trained/fine-tuned on CLTT reaches the mid-to-high 70s. Recent UDPipe 2 models (especially those using PDT-C data) also deliver very high morphology accuracy (tagging ~98%+, lemmatization even higher when combined with a morphological dictionary). You can fine-tune relatively easily on your own legal data or on CLTT.

- **Czech Legal Text Treebank (CLTT)** is particularly relevant. It contains ~1,121 manually annotated dependency trees from real legal documents (Accounting Act and a related decree). Annotations follow the PDT-style analytical layer (dependency trees with syntactic functions). CLTT 2.0 additionally includes semantic (subject, predicate, object) triples for definitions, rights, and obligations. It is freely available from LINDAT and ideal both as evaluation data and as fine-tuning material.

- **SET parser** (NLP Centre, Masaryk University) is a more “lower-level”/rule-based alternative. It uses pattern-matching rules (currently ~80–220 rules for Czech) and incremental segmentation. It outputs dependency relations and has been explicitly applied to subject–predicate agreement checking and related grammar tasks. Because the rules are human-editable, it is well suited for injecting legal-domain patterns or constraints. It expects morphologically tagged input (pair it with MorphoDiTa or similar).

- Supporting tools: **MorphoDiTa** (high-accuracy Czech morphological analysis, tagging, and lemmatization; dictionary-based + statistical, trainable) is almost always useful as preprocessing. Hybrid systems that combine deep learning with a morphological dictionary at inference time further reduce errors.

You can train or fine-tune UDPipe (or a modern neural dependency parser) on CLTT + any additional legal data you annotate. For pure subject/predicate extraction you do not need the full tree—simple post-processing of the parse (find finite verbs / roots and their `nsubj` dependents, respecting agreement) often suffices. Rule-based overlays or constrained decoding can further enforce legal-specific conventions.

### Is the task unequivocal? Edge cases and ambiguities
No — it is not fully unequivocal. Czech morphology and agreement provide strong cues (case, gender, number, person), but several sources of ambiguity remain, and legal texts amplify some of them:

- **Null/pro-drop subjects** — Czech frequently omits the subject; the verb’s agreement morphology encodes it.
- **Free word order + case syncretism** — Nominative/accusative forms can overlap, so position alone is unreliable; the parser must rely on case and agreement.
- **Complex and very long sentences** — Legal Czech is notorious for long, multi-clause constructions with coordination, embedding, and nominalizations. Identifying the *main* predicate vs. subordinate ones is non-trivial.
- **Attachment ambiguities** — Prepositional phrases, relative clauses, and modifiers can attach in multiple plausible ways.
- **Reflexives (“se”/“si”)** and passives — Attachment and voice interpretation can be ambiguous.
- **Copular and nominal predicates** — The syntactic predicate may be an adjective or noun rather than a full verb; the subject still agrees with the copula or the predicative element.
- **Legal-specific phenomena** — Definitions, rights/obligations formulations, modal constructions, and highly formal register introduce additional patterns that general models see less often.

Parsers (statistical or neural) still make errors on these, especially under domain shift. Manual error analyses in related Czech work frequently cite incorrect dependency trees as a major source of downstream failures in legal information extraction.

### Getting a mid-size model (e.g., 70B Llama) to similar performance without finetuning
Pure zero-shot or light few-shot prompting can work for simpler sentences but typically lags specialized parsers on complex legal Czech (similar findings appear for related Czech structured tasks such as anaphora resolution, where prompting reached ~74% while fine-tuned smaller models reached ~88%).

Practical ways to close the gap *without* full fine-tuning:

- **Strong few-shot + structured prompting** — Provide several CLTT-style examples (or your own) showing the desired output format (e.g., “Subject: …; Predicate: …” or a simplified CoNLL-U snippet). Use step-by-step instructions: (1) identify finite verbs / potential predicates, (2) find nominative NPs that agree in gender/number/person, (3) handle clauses and coordination, (4) output in a rigid JSON or tabular format. Explicit reasoning steps and constrained formats help reduce hallucinations.
- **Hybrid approach (most effective)** — Run UDPipe (or SET) first, then feed the parse + original sentence to the LLM. Ask it to verify, correct, or select among alternatives, or to extract/interpret the *semantic* subject–predicate (especially useful for rights/obligations). This leverages the specialized tool’s accuracy while using the LLM’s reasoning for residual ambiguities or higher-level legal interpretation.
- **RAG / in-context retrieval** — Retrieve the most similar annotated legal sentences from CLTT (or a small curated set) and include them in the prompt.
- **Morphology + agreement constraints** — Pre-process with MorphoDiTa/UDPipe morphology and inject the features into the prompt or as hard constraints.

A well-prompted 70B model can approach specialized-tool performance on straightforward cases and is more flexible for semantic nuances, but it will generally be slower, less consistent, and more expensive than a fine-tuned UDPipe model for high-volume or production use. For best results on legal Czech, the recommended path is still: use/fine-tune a specialized parser (UDPipe + CLTT) as the core subject/predicate extractor, and optionally layer an LLM on top for refinement or explanation.

If you share more details (e.g., volume of data, whether you can annotate a small seed set, exact output format needed, or latency constraints), I can suggest a more concrete pipeline or evaluation setup.

## Q

Tell me more about the hybrid approach - could LLMs actually improve performance on legal czsch thanks to semantics? Has it (or something similar) been done? Also, could i get good results with finetuned 70B llama?

## A

**Yes, LLMs can improve performance on legal Czech subject/predicate identification via semantics, and hybrid systems are a practical and increasingly explored direction.** Fine-tuning a 70B-class Llama is feasible and can yield strong results, especially with parameter-efficient methods and domain data.

### How the hybrid approach works and why semantics help
A typical hybrid pipeline looks like this:

1. Run a specialized syntactic tool (UDPipe/UDPipe 2, SET, or a neural dependency parser fine-tuned on CLTT/PDT) to produce a high-precision candidate parse or a set of candidates (with attachment scores or alternative trees).
2. Feed the original sentence + the parse (or multiple candidates) to an LLM.
3. Ask the LLM to:
   - Verify agreement and structural validity.
   - Resolve remaining ambiguities using meaning (e.g., “which nominative NP is the logical agent/holder of the right/obligation?”).
   - Correct attachments that are syntactically possible but semantically implausible in a legal context.
   - Map the syntactic subject/predicate to a higher-level semantic triple (subject–predicate–object), which is exactly what CLTT 2.0 annotates for definitions, rights, and obligations.
   - Output a cleaned or re-ranked result in a constrained format (JSON, simplified CoNLL-U, or explicit “Subject: …; Predicate: …”).

**Why semantics help specifically on legal Czech:**
- Pure syntactic parsers rely heavily on morphology, case agreement, and patterns learned from mostly news/fiction data (PDT, FicTree, etc.). Legal texts feature very long sentences, heavy nominalization, formal register, and domain-specific constructions. Domain shift measurably hurts LAS (PDT-trained models drop substantially on CLTT).
- Ambiguities that syntax alone cannot resolve (prepositional-phrase attachment, coordination scope, pro-drop recovery, which of several nominatives is the true subject in complex clauses) often become clear once meaning and legal context are considered.
- Legal language has predictable semantic patterns (who holds a right/obligation, what is being defined, modal structures). An LLM can leverage this world/legal knowledge, while a pure parser cannot.
- The LLM can also act as a post-processor that enforces consistency with morphological features or legal conventions that the base parser missed.

This is not pure speculation. Related work shows:
- Self-correction loops (LLM generates a parse, then uses grammar rules or a second pass guided by detected errors) improve both in-domain and cross-domain parsing accuracy.
- LLMs can re-rank or correct traditional parser outputs effectively, and hybrids that combine LLM-generated trees with traditional parser scores produce higher-quality synthetic data or final analyses.
- Step-by-step prompting (first POS, then heads/labels, with a simple tabular/CoNLL-like format) lets LLMs reach competitive or state-of-the-art dependency parsing results across many languages, including those with richer morphology.
- In legal NLP more broadly, hybrids of LLMs + structured/symbolic components improve consistency and reduce hallucinations on tasks that require both linguistic form and domain meaning (clause extraction, statutory analysis, argument mining).

For Czech specifically, direct published hybrids for subject/predicate on legal text are still limited, but the building blocks exist: CLTT provides both syntactic gold and semantic (subject–predicate–object) annotations; Czech legal argument-mining and NER work already uses Llama-family models (including continued pre-training on legal Czech data); and fine-tuned smaller models clearly outperform pure prompting on related structured Czech tasks such as anaphora resolution.

### Can you get good results with a finetuned 70B Llama?
**Yes.** Recent work shows that fine-tuning LLMs (including Llama-3 variants) for dependency parsing is effective. Key observations:

- Choice of output representation matters (e.g., Stanford-style dependency tuples vs. lexicalized trees). Some formats produce more valid trees; others produce higher-quality attachments.
- Fine-tuning improves handling of longer dependencies to some extent (helpful for legal sentences).
- Multilingual or carefully designed supervised fine-tuning (SFT) can yield strong Universal Dependencies results; step-by-step or structured formats further reduce format errors and hallucinations.
- On Czech-related structured prediction, fine-tuned models (even smaller ones such as mT5-large) substantially outperform pure prompting of larger LLMs. Domain-adapted Llama variants (continued pre-training or fine-tuning on Czech legal material) already show gains on argument classification and related tasks.

**Practical considerations for a 70B model:**
- **Data** — CLTT is small (~1,100 sentences). Mix it with PDT (or PDT-C), CAC, and synthetically augmented legal sentences generated by a strong LLM (prompted to produce CoNLL-U-style annotations that respect Czech morphology). This is a common and effective strategy.
- **Efficiency** — Full fine-tuning of 70B is expensive. Use LoRA / QLoRA (or similar PEFT methods). This is routinely done for domain adaptation of 70B-class models and is feasible on a modest number of high-memory GPUs.
- **Output validity** — Constrain generation (guided decoding, grammar constraints, or post-validation against morphology/agreement and tree properties such as single-root, no cycles). A second verification pass (self-correction or a traditional parser) further stabilizes results.
- **Expected outcome** — A well-executed fine-tune should match or exceed a strong UDPipe baseline on pure syntactic subject/predicate identification for legal Czech, while also providing better semantic role mapping and robustness on the long, complex sentences typical of the domain. A hybrid (fine-tuned 70B + UDPipe) would likely be even stronger and more reliable.

**Recommended path**  
Start with a lightweight hybrid (off-the-shelf or CLTT-fine-tuned UDPipe + prompted or lightly fine-tuned smaller LLM) for quick gains and error analysis. Then, if resources allow, move to full PEFT fine-tuning of a 70B model on a mixed CLTT + PDT + synthetic legal set, using a structured output format and validation. Evaluate both pure syntactic accuracy (against CLTT gold) and higher-level semantic subject/predicate triples (using CLTT’s semantic layer).

This combination of specialized syntactic tools and LLM semantic reasoning is currently one of the most promising ways to push performance on domain-specific, morphologically rich legal Czech.

## Q

excellent stuff. let me give you a bit more context:

* i'm interested in comprehensibility of Czech legal texts - the distance between predicate/subject reduces comprehensibility, so it's useful to flag sentences that have this metric above certain threshold

questions

1. can you think of (or find) other similar metrics impacting comprehensbility that could be built from conllu (or similar NLP) outputs (subordinate clauses etc.)

2. ultimately, we are interested in flagging and *rewriting/fixing* sentences in Czech legal text that are *needlessly* incomprehensible (legalese vs plain language). for now we are using mostly rule-based system (passives, nominalizations, too many negatives, etc.) but we are looking to expand this with LLMs, i.e. using LLMs to detect specific phenomena in legal text that affect comprehensibilty (not a question, more description of our approach)

3. there are readability metrics, but those are limited; i wonder if we could find a shortcut - could we use LLMs "measure" comprehensibility? is there something like "cognitive load" in LLMs that could be measured?

## A

**Great context — this aligns perfectly with ongoing Czech readability research (e.g., projects like LiFR and PONK at ÚFAL/Charles University, which study exactly these issues in administrative/legal texts).** Predicate-subject distance (a form of dependency distance) is a solid proxy for processing difficulty, as longer distances increase working memory load. Below are targeted answers to your three questions.

### 1. Other similar metrics from CoNLL-U (or dependency parses) impacting comprehensibility
Dependency parses (CoNLL-U) are rich sources for syntactic complexity metrics. Many correlate with human readability judgments, especially in legal/administrative domains (long sentences, nominalizations, embedding). Here are strong candidates you can extract/compute directly or with minor post-processing:

- **Dependency/Mean/Max Dependency Distance (MDD)** — Average or maximum linear distance (in words or tokens) between a head and its dependents. Closely related to your predicate-subject metric. High values signal "crossing" or distant relations that burden working memory.
- **Maximum Tree Depth / Sentence Depth** — Depth of the dependency tree (or height from root). Deeper trees = more embedding/nesting.
- **Subordinate Clause Ratio / Number of Subordinate Clauses** — Count of `advcl`, `acl`, `ccomp`, `xcomp`, `acl:relcl`, etc. Heavy subordination (especially center-embedded or right-branching in Czech) reduces readability.
- **Clausal Modifiers / Participial/Adverbial Clauses** — Frequency of participial constructions (`acl` with participles) or adverbial clauses (`advcl`). Common in Czech legal style and known to complicate processing.
- **Noun Phrase Complexity** — Average length/depth of NPs (`nmod`, `amod`, `det`, prepositional modifiers). Legal texts favor heavy nominalizations and complex NPs.
- **Coordination Density** — Number/frequency of `conj` and `cc` relations. Over-coordination creates long flat structures that are hard to parse.
- **Passive Voice Ratio** — Proportion of passive constructions (`aux:pass`, `nsubj:pass`). Increases distance and reduces agentivity.
- **Average Sentence Length** + **Clauses per Sentence** — Classic but still useful when combined with parse features.
- **Crossings / Non-Projectivity** — Count of crossing dependencies (non-projective arcs). Rare in well-formed text but indicative of complexity.

**Implementation tips**:
- Use libraries like `conllu` (Python) + `spacy`/`udapi` or UDPipe output directly.
- Aggregate at sentence or document level (mean, max, std dev).
- Combine into composite scores (e.g., via regression or random forest, as in Russian legal complexity models). Research on Russian/Czech legal texts shows syntactic features (especially clausal and phrasal complexity) often outperform traditional readability formulas like ARI/Flesch when predicting human comprehension.

These metrics cluster into **clausal** (embedding, subordination) and **phrasal** (NP complexity) groups, both relevant for legal Czech.

### 2. Expanding rule-based detection with LLMs for flagging + rewriting
Your rule-based system (passives, nominalizations, negatives, etc.) is a strong foundation. LLMs excel at detecting subtler or context-dependent phenomena that rules miss, and they can propose rewrites.

**Detection/Flagging Ideas** (LLM as classifier or feature extractor):
- Prompt for phenomena like: excessive center-embedding, vague referents, logical inconsistencies in rights/obligations, overly abstract nominal chains, or "garden-path" structures.
- Use few-shot prompting with examples from CLTT or your annotated set.
- Hybrid: Run syntactic metrics first (flag high-distance or deep-tree sentences), then LLM for semantic/pragmatic issues (e.g., "Does this sentence clearly assign responsibility?").
- Output structured JSON: {"phenomena": ["long dep distance", "heavy nominalization"], "score": 0.85, "explanation": "..."}.

**Rewriting/Fixing**:
- LLMs are already strong at controlled simplification (plain language rewriting while preserving legal meaning). Use self-refinement: generate a simplification → evaluate against original meaning/metrics → iterate.
- Prompt engineering: "Rewrite this Czech legal sentence in plain language, keeping legal precision. Minimize predicate-subject distance. Avoid passives where possible."
- Hybrid safeguards: Post-rewrite, re-parse with UDPipe and check that key metrics (distance, voice, etc.) improved without introducing new errors. Validate semantic triples (subject-predicate-object) against CLTT-style annotation.
- Evaluation: Use human ratings or comprehension tests (as in LiFR-Law corpus, which has paraphrased Czech admin/legal texts with reading comprehension scores).

This is actively researched — Czech projects explore linguistic factors in readability and tools like PONK combine rules/metrics with potential for LLM integration. Broader legal NLP shows LLM-assisted simplification improves comprehension (e.g., measurable gains in MCQ accuracy and reduced self-reported cognitive load).

### 3. Using LLMs to "measure" comprehensibility / cognitive load proxies
Traditional readability formulas are limited (they ignore syntax/semantics deeply). LLMs offer promising proxies, though they are not perfect substitutes for human eye-tracking or comprehension tests.

- **Surprisal / Perplexity** — A strong proxy for processing difficulty. Compute how "surprised" an LLM is by each word given context (negative log-probability). Higher local surprisal correlates with longer reading times and lower comprehensibility. Useful for highlighting difficult spans in legal texts. Models trained on Czech (or multilingual) can capture this.
- **Cognitive Load Indicators** — LLMs don't have direct "cognitive load," but you can approximate via:
  - Activation patterns or entropy in intermediate layers (research explores this).
  - Self-reported or simulated load: Prompt the LLM to rate difficulty or predict human reading ease.
  - Eye-tracking proxies: Surprisal + syntactic metrics predict fixation durations.
- **Direct LLM-as-Judge** — Prompt a strong model (e.g., Czech-capable Llama or Mistral variant) with few-shot examples of easy/hard legal sentences and their human ratings. It can output a holistic score or per-sentence difficulty. Combine with your metrics for a hybrid score. Studies show LLMs can approximate readability but are noisy zero-shot proxies; calibration with human data helps.

**Caveats and Best Practice**:
- LLMs may underestimate legal-domain difficulty if not adapted (continued pre-training or fine-tuning on Czech legal helps).
- Validate against human data (comprehension tests, eye-tracking if possible). Research shows traditional formulas + syntactic metrics + LLM surprisal together predict real reading ease better than any alone.
- For rewriting loop: Use LLM to simplify flagged sentences, measure before/after metrics + LLM "ease" score, and iterate.

This fits well with Czech efforts (e.g., PONK tool for admin/legal readability, LiFR project). You could build a prototype pipeline: UDPipe → complexity metrics → LLM flagging/rewriting → re-evaluation. If you'd like, I can help sketch code/prompts or suggest specific datasets/models (e.g., CLTT, LiFR-Law corpus).

Let me know how to proceed — e.g., example prompts, metric computation code, or a small prototype idea!

## Q

two things

* let's go back to our subject/predicate distance to draft specific experiment: i want to test how LLMs (~80B) can be used to enhance what we get from UDpipe (or some other generic tool) with semantics. that's a neat topic, but need specifics

* tell me more about: 1. surprisal/perplexity, 2. activation patterns or entropy in intermediate layers; as measures of text comprehensibility - do they correlate well with humans? what does the research day?

## A

**Excellent — both topics are actionable and grounded in current research.** I'll address them directly.

### 1. Specific Experiment: Enhancing UDPipe Subject/Predicate Distance with LLM Semantics (~70-80B class models)
**Goal**: Quantify how much semantic reasoning from a large LLM improves upon (or complements) pure syntactic distance from UDPipe for predicting human comprehensibility in Czech legal texts. Focus on "needlessly" long distances (syntactically distant but semantically recoverable vs. genuinely hard cases).

#### Experimental Design (Feasible with modest resources)
**Data**:
- Use **CLTT** (Czech Legal Text Treebank, ~1,121 sentences) as the core gold set — it has both syntactic dependencies and semantic subject–predicate–object triples (ideal for "semantic distance").
- Supplement with a small set of your own or LiFR-Law-style paraphrases + human comprehension scores if available.
- Split: Train/validation on PDT/CAC mix + CLTT subset; test on held-out legal sentences.

**Pipeline**:
1. **Baseline (Syntactic Only)**:
   - Run UDPipe 2 (PDT-C or CLTT-tuned model) on raw text → CoNLL-U.
   - Compute **Predicate-Subject Distance**: For each finite verb (predicate root or main verb), find its `nsubj` (or `nsubj:pass`, `csubj`) dependent. Measure linear word distance (or dependency path length). Aggregate per sentence: max/mean/std.
   - Flag sentences above a threshold (e.g., >8–10 words, tuned on human data).

2. **LLM Semantic Enhancement** (the interesting part):
   - **Input to LLM**: Original sentence + UDPipe parse (as text or structured JSON: list of tokens, heads, deprels, especially candidate subjects/predicates).
   - **Prompt Strategy** (few-shot or chain-of-thought):
     - Step 1: Confirm syntactic parse and compute baseline distance.
     - Step 2: Reason semantically: "In this legal context, is the syntactic subject the logical agent/holder of the right/obligation? Are there implicit/pro-dropped elements? Suggest the most plausible semantic subject-predicate pairing and an effective distance (accounting for recoverability)."
     - Step 3: Output structured: `{"syntactic_distance": X, "semantic_effective_distance": Y, "explanation": "...", "rewrite_suggestion": "..."}`.
   - Models: Llama-3.1/3.3 70B (or similar ~80B-class, e.g., Qwen2.5-72B, Mistral-Large). Use LoRA/quantization for efficiency. Run in few-shot mode first; optionally fine-tune on CLTT semantic triples.

3. **Metrics & Evaluation**:
   - **Human Ground Truth**: Collect or use existing ratings — reading time, comprehension accuracy (MCQs on who/what the predicate applies to), or perceived difficulty.
   - **Correlation**: How well does LLM-adjusted distance predict human scores vs. raw UDPipe distance?
   - **Improvement**: % reduction in false positives (flagging sentences that humans find easy despite long syntactic distance) and false negatives.
   - **Rewrite Quality**: Automatic metrics (before/after syntactic distance, semantic fidelity via entailment or triple matching) + human judgment on plain-language versions.
   - Ablations: LLM without parse context vs. with; different prompt styles; smaller vs. larger models.

**Expected Outcomes & Why It Works**:
- UDPipe gives reliable syntax but misses semantic recoverability (e.g., a distant subject that is the clear topic via discourse or legal convention).
- LLM adds world/legal knowledge and reasoning → better "effective cognitive distance."
- Hybrids like this (parser candidates + LLM reranking/correction) improve parsing and downstream tasks in related work; for legal Czech, it should help with the long sentences and formal structures you care about.
- Practical win: A hybrid scorer that flags "needlessly complex" sentences (high syntactic distance + poor semantic recoverability) and proposes rewrites.

**Quick Prototype Steps** (if you want to implement):
- Use `ufal.udpipe` or Hugging Face UDPipe wrapper + `transformers` for LLM.
- Start with 8B/70B in 4-bit quantization for speed.
- Evaluate on 100–200 CLTT sentences with a small human pilot.

This is a neat, publishable experiment — it directly bridges syntactic tools and semantic LLMs for your comprehensibility goal.

### 2. Surprisal/Perplexity and Activation Patterns/Entropy as Comprehensibility Measures
**Research Summary** (strong but not perfect correlation with humans; best as proxies when combined with other features):

#### Surprisal / Perplexity
- **Definition**: Surprisal of a word = −log P(word | previous context) from a language model. Perplexity is the exponential average surprisal across a sequence (how "surprised" the model is overall).
- **Link to Comprehensibility**: Higher local surprisal correlates with longer human reading times (eye-tracking fixations), lower comprehension, and higher cognitive effort. Unpredictable words/phrases increase processing load. Too-predictable (very low surprisal) passages can also feel dense or formulaic in legal texts.
- **Evidence**:
  - Classic psycholinguistics + modern LM studies show surprisal predicts self-paced reading times and eye movements well, especially in English and other languages.
  - In readability work (including legal/admin texts), surprisal-based metrics highlight difficult spans better than traditional formulas in some cases.
  - Czech-specific explorations (e.g., entropy/surprisal in administrative texts) exist and align with human difficulty.
  - Limitations: Depends on the LM (needs good Czech coverage; domain-adapted models perform better on legal text). Global perplexity is weaker than local surprisal for pinpointing issues. Correlates with humans but is noisy alone — combine with syntactic metrics for best results.

#### Activation Patterns or Entropy in Intermediate Layers
- **Idea**: Look inside the LLM (not just output probabilities). Measure entropy (uncertainty) across neurons/attention heads or activation magnitudes in middle layers when processing the text. High entropy/activation in certain layers may signal "effort" or integration difficulty.
- **Research**:
  - Some studies probe LLMs as cognitive models: higher intermediate-layer surprisal-like measures or specific attention patterns correlate with human processing difficulty (e.g., on complex syntax or ambiguous sentences).
  - Layer-wise analysis shows early layers handle surface form, later layers semantics/world knowledge — mismatches or high activity in integration layers can proxy cognitive load.
  - Evidence is emerging but mixed: Promising correlations in controlled experiments (e.g., center-embedded sentences evoke more "effort"), but not yet as robust or widely validated as behavioral surprisal. Not a direct "cognitive load meter" yet — more a research tool.
  - Practical use: Extractable via libraries like `transformer-lens` or Hugging Face hooks. Feasible but more compute-heavy than perplexity.

**Overall Correlation with Humans**:
- Both are solid proxies (especially surprisal) and outperform old formulas on nuanced texts, but research emphasizes they are **noisy zero-shot predictors**. Best performance comes from hybrids: syntactic features (from UDPipe) + LM surprisal + (optionally) layer probes + human calibration data.
- In legal/complex domains, they help detect "where the reader will struggle" even if overall readability scores look okay.
- Recent papers note that LLMs themselves can be prompted to judge readability, but surprisal-based methods are more interpretable and grounded.

For your use case, start with **word-level surprisal from a Czech-capable LLM** on flagged high-distance sentences — it will highlight whether the long distance is genuinely burdensome (high surprisal around subject/predicate) or easily recoverable (low surprisal thanks to context/semantics). This directly feeds your flagging + rewriting loop.

If you want, I can draft sample code/prompts for the experiment or suggest specific models/datasets for surprisal computation in Czech. Let me know the next step!

## Q

## A

## Q

## A

## Q

## A

## Q

## A

