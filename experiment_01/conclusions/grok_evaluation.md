prompt

alright, we ran the experiments and the results are not very encouraging

let me know what do you think about the design/execution of the experiment
find any weaknesses, design flaws and other suspicious potential issues
give me your interpretation of the results, keeping in mind that our primary goal is the practicality, i.e. we want to know what setup is best for actually implementing counting-based rules, considering we would prefer replacing rule-based systems (like PONK) with pure LLM-based approach.
essentially, i'm asking what does this tell us about the possibility of using pure LLM-based approach for rules requiring role idnetification and counting; my ideal is to achieve reasonable performance with local model using no additional tools. do you see path towards that goal? maybe involving smaller Czech-legislation-finetuned LLMs? or even, when we compromise, using UD pipe and THEN small local LLM?

response

**1. Design and execution assessment**

The experiment is **strong overall** — one of the cleaner, more transparent LLM evaluation setups I've seen for a narrow but high-stakes proxy task. It directly addresses the core question ("can we trust LLMs for structural/counting rules in legislative drafting?") with a deliberately minimal, objectively scoreable probe (subject–predicate linear word distance) that is grounded in established psycholinguistic metrics (dependency distance as cognitive load) and tied to real SPRINT/LPV needs.

**Strengths** (from the provided METHODOLOGY v3, IMPLEMENTATION log, and results summary):
- **Rigorous controls and reproducibility**: Within-sentence paired design (every sentence sees every condition), 3× temp-0 runs with full traces stored, provider+quantization pinning, exact prompt/response logging, real USD cost capture via OpenRouter `usage`. The `cell_id` / `uid` fix for non-unique `sent_id` shows attention to detail. Stratified sampling (length × distance buckets, tail oversampled, balanced across 4 KUK sub-corpora) deliberately stresses the hard cases where H4 predicts failure.
- **Decomposition and diagnostics**: Regime 2 (self-generated CoNLL-U) + deterministic recompute from the model's own parse separates "bad parsing" from "bad counting given parse." This is excellent for actionable insight. Parser QC on `cs_cltt` (99.3% agreement on labels where UDPipe commits) is a smart, low-cost way to bound silver-oracle noise without new annotation.
- **Scale and transparency**: Full 23k generations on real legal text, open family-matched models (Llama/Qwen pairs), cost ~$7.73 actual, all artifacts released (traces, metrics, error taxonomy). Ties cleanly to prior literature (counting fragility, structured prompting, dep distance).
- **Execution quality**: Data fully extracted/verified, `extract_pairs.py` + word-mapping logic validated (zero mismatches), harness handles resume/retry, smoke tests passed. The IMPLEMENTATION log shows disciplined iteration and bug fixes before the big run.

It is a **model of how to do a focused, engineering-oriented LLM paper** for NLLP/ACL-style venues. The proxy framing + explicit scope limitation ("predicts but does not prove for other counting rules") is intellectually honest.

**2. Weaknesses, design flaws, and suspicious issues**

Most are minor or already mitigated/flagged in the docs, but here are the ones that stand out for scrutiny:

- **Predicate operationalization is still provisional** (head-of-subject = root, copula logged separately). This is the single biggest threat to construct validity. If a linguist later prefers "measure to the finite verb/copula" instead, distances shift and some results (especially copular clauses, ~18–25% of data) could move. The paper correctly flags this; it should be resolved (or sensitivity analysis added) before camera-ready.
- **Silver-only standard** (even with 99.3% QC): You are measuring *agreement with UDPipe*, not linguistic truth. The QC bounds label noise well for sentences UDPipe parses cleanly, but segmentation differences (~60% of gold sentences split differently) are real and upstream of any counting rule. This is acceptable for the current paper but worth a short "limitations" paragraph.
- **Only one prompt formulation per regime** and no ablation on few-shot/examples or output format. Literature (Ginn & Palmer 2025 on in-context rules for dep parsing) shows structure/rules help; a small prompt sweep or "add explicit UD guidelines" variant could have strengthened the "structure helps" claim without much extra cost.
- **Model selection**: Family-matched open models + fp8 pinning is good for reproducibility/local deployment, but it leaves open whether the counting bottleneck is universal or partly an artifact of these specific post-training/quantization stacks. (Frontier closed models were deliberately avoided — reasonable for the "open/local" goal, but worth noting.)
- **Stratification + sub-corpus balancing**: Oversampling the long/far tail is correct for power on H4. Balancing the 4 sub-corpora (instead of population-proportional) improves generalizability claims but makes the small corpora (esp. OmbuFlyers) heavily oversampled → less independent. The docs already discuss the trade-off; it's fine but should be stated.
- **No mixed-effects model in final write-up** (deferred): With effect sizes this large it probably doesn't change conclusions, but for formal inference on the interaction (H3) it would have been cleaner.
- **Minor**: Distance counted in whitespace-words (human-meaningful, good) but models see tokens. The MWT/word-mapping logic is solid, but any tokenization mismatch could inflate "counting" errors in regime 1. Regime 2's tolerant CoNLL-U parser is necessary but adds a small parsing layer that isn't purely "LLM."

None of these invalidate the conclusions; they are the normal "room for improvement" items in a solid first experiment. The design is **not** suspiciously flawed — it is cautious and well-documented.

**3. Interpretation of the results (practicality focus)**

The results are **clear and discouraging for a pure LLM approach to counting-based rules**, exactly as the supervisor summary states.

- **Headline numbers are damning for production use**: Best case (Qwen-72B + gold CoNLL-U) reaches only ~65% exact distance match. Even when the model correctly names both subject and predicate words (~83–87% for the large models), it still miscounts the span 28–36% of the time. Small models are essentially unusable for exact counting (Llama-8B drops to 0.1% exact once you condition on correct naming). This matches the broader literature on LLM counting fragility (tokenization sensitivity, lack of exact symbolic arithmetic, finite internal "count states").
- **The bottleneck is counting, not role identification or structure-reading**. Large models are reasonably good at locating `nsubj` and following HEAD when handed the parse. The failure is in turning those positions into an accurate integer distance. This is the key practical takeaway.
- **Instability is a feature, not a bug to patch**: Even at temperature 0 with pinned provider/quant, up to 56% of triplets vary run-to-run. Majority voting does **not** rescue accuracy (it mostly averages wrong answers). A consistent-but-wrong answer is worse than variable output for a rule engine. Reproducibility ≠ correctness.
- **Silver oracle is trustworthy enough**: 99.3% label agreement on `cs_cltt` means the LLM failures are real, not artifacts of a noisy gold standard. The real upstream issue (sentence segmentation) affects *any* method and should be treated as a first-class preprocessing step.

**For replacing rule-based systems (e.g. PONK) with pure LLM-based counting rules**:
- **Not viable today**. 65% exact (or even 80–85% with tolerance) is too low for legal drafting support where a single miscount can produce an incorrect rule verdict. The combination of low accuracy + high instability makes pure LLM prompting unsuitable for any rule whose output must be deterministic and auditable.
- Structure helps a lot (H1 confirmed, +38–39 pts for large models when given the parse), but not enough to reach production reliability. H3 is rejected: structure *widens* the size gap rather than closing it for exact counting.
- H2 and H4 hold: bigger is better, longer/farther is harder. This is consistent with known LLM weaknesses on long-range exact arithmetic.

**4. Implications for pure LLM-based approach + path forward**

This experiment tells us that **current LLMs (even 70B-class open models) are not a drop-in replacement for deterministic extractors on tasks that require precise role identification + exact counting**. The architecture is statistical pattern-matching, not symbolic arithmetic; counting exact positions or spans remains a fundamental weak point.

**Ideal goal (reasonable performance with local model, no extra tools)**:  
I do **not** see a near-term path to that with pure end-to-end LLM prompting, even with Czech-legislation-finetuned models. Finetuning can improve role identification and legal-domain fluency (smaller Czech models or continued pretraining on KUK/CLTT-style data would help here), but the counting step is likely to remain brittle because it is not primarily a knowledge or fluency problem — it is a symbolic/exact-computation problem. Smaller local models would almost certainly perform *worse* than the 72B results shown.

**Realistic compromise paths (in rough order of practicality for SPRINT)**:

1. **Best engineering choice right now (recommended)**: **Triage rules and use deterministic extractors over a UD parse for anything countable/structural**.  
   - Parser (~99% accurate on labels, zero variance) + trivial Python subtraction for distance/paragraph counts/etc.  
   - LLM only for the parts that genuinely need semantics/pragmatics (e.g., "is this convoluted?" or higher-level judgment on top of the count).  
   - This is exactly what the results + supervisor summary conclude. It is auditable, cheap, and matches the "Czech legislation as codebase" metaphor in the original SPRINT document.

2. **Hybrid with tool use (still practical, keeps LLM in the loop)**: LLM (local or API) calls a deterministic parser (UDPipe or fine-tuned legal parser) as a tool, receives the CoNLL-U or extracted (subject, predicate, distance), then reasons over it. This sidesteps the counting weakness while letting the LLM handle any semantic overlay. Many production agent frameworks already support this cleanly.

3. **Pure LLM + heavy mitigation (only if you must avoid external tools)**:  
   - Use the largest feasible local/open model + explicit chain-of-thought or "think step-by-step about positions" prompting + self-consistency (multiple samples + vote).  
   - Add output constraints / JSON mode + post-processing that forces the model to output indices and then recomputes distance in code.  
   - Finetune a mid-size Czech-legal model on synthetic counting tasks (generate sentences + gold distances, train to output correct JSON). This might push role ID higher and reduce some off-by-one errors, but expect diminishing returns on exact long-distance counting.  
   - Still unlikely to reach the reliability bar for production rules without the deterministic layer.

**Bottom line for your goal**: The experiment strongly supports keeping (or building) a **deterministic structural layer** (UD parse → extractors) as the foundation for counting-based rules and using LLMs only where they add unique value (semantics, judgment, generation). Pure end-to-end local LLM for "role ID + exact count" is not currently practical and shows no clear near-term path without fundamental architectural changes (e.g., hybrid neuro-symbolic systems or external symbolic modules). The results are consistent with the broader literature and give you a clear, evidence-based recommendation rather than wishful thinking.

If you want, I can help draft the "limitations + future work" paragraph for the ACL camera-ready, suggest specific prompt improvements for a follow-up, or sketch the hybrid architecture for SPRINT integration. The data and traces you have are gold for any of that.