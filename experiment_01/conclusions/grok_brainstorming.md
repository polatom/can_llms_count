prompt

alright, maybe our thinking about this is too limited: in truth, we don't really care about the EXACT distance - we care about comprehensibility. the distance is verified proxy for it but maybe something like "semantic/informational density/content" between subject and predicate (i.e. how much "happens" between them that reader needs to soak in) is crucial. is there a respectable way we could measure any of this?
with that another question: is there any way we could measure the cognitive load of LLM when providing response to a prompt? time/tokens/logit profile etc.?

response

**Yes — shifting from "exact numeric distance" to something closer to actual human comprehensibility / cognitive load is a smart and natural evolution.** The linear word distance you used is a *validated but crude proxy* (rooted in Dependency Locality Theory). There are more nuanced, respectable ways to quantify "how much the reader has to hold in working memory and integrate between the subject and predicate."

### 1. Respectable ways to measure semantic/informational/cognitive load between subject and predicate

Here are the strongest, academically grounded options, ranked by how feasible they are with the data and parses you already have (KUK + UD trees from `extract_pairs.py`).

#### A. Dependency Locality Theory (DLT) measures (best direct upgrade)
**Ted Gibson’s Dependency Locality Theory (1998, 2000)** is the classic psycholinguistic framework that treats linear distance as a *proxy* for two costs:
- **Integration cost**: How far back you have to reach to connect a new word to its head (decay + interference in working memory).
- **Storage (memory) cost**: Number of predicted but unintegrated heads you have to keep active.

**Subject–predicate distance is literally one of the canonical examples** in DLT papers.

**Computable from your existing UD parses** (very cheap):
- **Integration cost approximation**: Sum of distances of all dependents that attach across the subject–predicate span (or just the longest dependency that crosses the span).
- **Number of new discourse referents / entities** introduced in the intervening material (you already have NameTag NE tags in KUK).
- **Number of intervening clauses / embedding depth** (you already log `intervening_clauses` and `tree_depth` — this is excellent).
- **Yngve or Frazier depth** of the material between subject and predicate (center-embedding is especially costly).

These are "respectable" — hundreds of papers in *Cognition*, *Journal of Memory and Language*, etc., use them to predict reading times and acceptability.

#### B. Surprisal-based measures (the current gold standard in psycholinguistics)
**Surprisal theory** (Levy 2008 and many follow-ups): The processing difficulty of a word is proportional to its **surprisal** = –log P(word | left context). Cumulative surprisal in the span between subject and predicate is a direct measure of "how much unexpected/new information the reader has to soak in."

**How to compute it with what you have**:
- Take any reasonably strong Czech or multilingual LM (your Qwen-72B or even a smaller local one fine-tuned on legal text would work).
- For each sentence, compute word-by-word surprisal on the raw text.
- Sum (or average) the surprisal of all words strictly between the subject and predicate.
- You can also do **conditional surprisal** given the subject (i.e., how surprising is the material once the subject is known?).

This is extremely well-validated against human reading times and is used in dozens of recent ACL/EMNLP/CogSci papers. It captures *semantic/informational density* far better than raw token count because it weights content by how predictable/unpredictable it is in context.

#### C. Other strong, computable proxies for "informational density"
- **Proposition / event density**: Number of verbal predicates, clauses, or semantic frames (via a semantic role labeler or even just counting finite verbs) in the intervening material.
- **Entity / referent density + coreference load**: How many *new* entities are introduced between subject and predicate, and how many have to be kept active (you already have NE tags + can run a simple coreference tool).
- **Semantic drift / embedding-based measures**: Average cosine distance in embedding space between the subject embedding and each intervening word (or between subject and predicate). High drift = more "content" the reader has to integrate.
- **Idea density** measures (used in Alzheimer's / readability research — the same community that uses dependency distance).

All of these are "respectable" (published, reproducible) and can be layered on top of your existing 415k gold pairs with relatively little new code.

**Recommendation for SPRINT**:  
Start with **DLT-style integration cost + cumulative surprisal** (computed from your UD trees + a local LM). These are cheap, theoretically grounded, and directly address "how much the reader has to hold and process between the core subject and predicate." You could add them as additional features in your linter rules or as better evaluation targets for future LLM experiments. Exact numeric distance can stay as a simple baseline.

### 2. Measuring the LLM’s own "cognitive load" during generation

Yes — there are several practical, increasingly standard ways to quantify how "hard" the model finds the task. These are useful diagnostics (e.g., does the model show high uncertainty precisely on long-distance cases?).

#### Practical proxies you can extract from (or cheaply add to) your existing pipeline

| Measure | What it captures | How to get it in your setup | Difficulty |
|---------|------------------|-----------------------------|------------|
| **Generation time / tokens-per-second** | Overall computational effort | Already in your `run_llm.py` traces (timestamp + usage) | Trivial |
| **Output length / tokens generated** | How much "reasoning" the model produces before answering | Traces | Trivial |
| **Per-token entropy of output distribution** | Model uncertainty at each step (high entropy = "I'm not sure what comes next") | Re-run sample with `logprobs=True` (or equivalent on OpenRouter/local) and compute –Σ p log p | Easy |
| **Logit-based uncertainty** (e.g. LogU, entropy of first token of the distance number, margin between top logits) | Token-level confidence | Same as above; several recent papers (2025) formalize this | Easy |
| **Attention / activation patterns** (open models only) | Where the model is "looking" when generating the distance (e.g., does it attend back to the subject?) | Hook into `transformers` model for a subsample | Medium |
| **KV-cache pressure / memory usage during generation** | Working-memory analog inside the model | Monitor during local inference | Medium |
| **Surprisal of the model's own output** | How predictable/surprising the model's answer is given the prompt | Compute with the same model or a reference LM | Easy |

**Most actionable right now**:
- Re-run a stratified subsample (or the full eval set if cheap) requesting `logprobs` / token probabilities.
- Compute **entropy per generation step**, especially on the tokens that output the distance number.
- Correlate high-entropy steps with long subject–predicate distance or high human-style surprisal in the input span. This would be a nice diagnostic: "the model itself struggles exactly where humans would."

These measures are now standard in LLM interpretability and uncertainty quantification papers (entropy, logit margins, LogU frameworks, etc.).

### Practical next steps for your project

1. **Extend your existing extraction pipeline** (`extract_pairs.py` or a new `load_measures.py`):
   - Add DLT-style integration cost and number of intervening new entities/referents.
   - Add cumulative surprisal using one of your local models (or even the same Qwen/Llama you already ran).

2. **For LLM-side diagnostics**: Add a small script that re-processes your existing traces (or a subsample) with logprobs enabled and computes per-step entropy + correlation with distance/surprisal features.

3. **For SPRINT linter rules**: These richer features (integration cost + surprisal in the subject–predicate span) could become *much better* signals than raw distance for "this sentence is likely hard to comprehend." You could even train a small regressor on top of them to predict "comprehensibility risk."

This direction feels more aligned with the actual goal (comprehensibility of legislative text) than exact integer distance, while still being fully automatable and grounded in solid science.

Would you like me to sketch concrete code additions (e.g., how to compute integration cost or surprisal from your current JSONL outputs), suggest specific papers for the write-up, or help design a small follow-up experiment that adds these measures?