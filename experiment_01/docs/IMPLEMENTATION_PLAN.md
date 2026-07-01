# Implementation Plan — "Can LLMs Reliably Count?" (Subject–Predicate Distance)

Status: **draft v0 — for discussion**
Source materials: `chat.md` (original notes), `nllp_sprint_llm_counting-1.pdf` (Grok-generated
paper draft), `SPRINT_pro_legislativni_tvorbu.md` (project context).

This plan turns the Grok paper draft into an executable research plan: what data we need, what
we build, what we measure, and how that becomes a submittable 4-page NLLP short paper.

---

## 0. Restating the research question

Can LLMs (small vs. large), given a Czech legal sentence, correctly identify the main
**podmět** (subject) / **přísudek** (predicate) pair and compute the exact linear token distance
between them — and does giving the model a **CoNLL-U** (UD parse) representation instead of raw
text change that?

Distance definition (from the draft, adopted as-is):
`d = |p − q| − 1` — number of tokens strictly between subject and predicate, linear order, not
tree depth.

Three prompting regimes × two model sizes = 6 conditions, benchmarked against UDPipe (silver) and
a small human-verified (gold) subset:

1. **Raw text → distance.** Model reads raw sentence, outputs subject, predicate, distance.
2. **Raw text → CoNLL-U → distance.** Model produces its own CoNLL-U parse first, then computes
   distance from it.
3. **Gold/silver CoNLL-U → distance.** Model is given the UDPipe parse and only has to locate the
   `nsubj` row, follow its head, and count.

**Why this matters for SPRINT**: several LPV rules require counting/structural measurement
(e.g. čl. 39 odst. 2 — max ~6 paragraphs per §; future "cognitive complexity" metrics). If LLMs
can't reliably count even in this narrow, well-defined task, SPRINT should not implement
counting-based rules as pure LLM prompts — it needs a deterministic structural-feature extractor
instead (or LLM + structured context, i.e. regime 3).

---

## 1. Decisions (resolved) and remaining open items

Resolved per discussion:
1. **Compute/API access**: OpenRouter API key available (`.env`, gitignored) → small + large
   models both sourced there.
2. **CLTT 2.0 access**: downloaded, no license gate (CC BY-NC-SA 4.0, same as KUK).
3. **KUK dataset identity**: resolved — the two LINDAT links were **not** two KUK versions. One
   is CLTT 2.0, the other is KUK 1.0 (see `METHODOLOGY.md` §4 for full detail). KUK 1.0 itself
   already contains parallel raw-`TXT/` and UD-`CoNLL-U/` subdirectories per sub-corpus, which is
   what the raw-vs-structured regimes need. Also checked **KUK 0.0** (predecessor) — it's a strict
   subset of KUK 1.0 with no UD annotation; not needed.
4. **Human annotation**: deferred, trigger-based (see `METHODOLOGY.md` §7) — silver-only for this
   iteration, linguist-experts on standby.
5. **Scope**: full-scale (not pilot-only) — dataset supply is not a constraint (~450k sentences in
   KUK 1.0).
6. **Timeline/authorship**: NLLP deadline ~1 month out, target max progress before Friday
   supervisor meeting; authorship TBD (likely user + supervisor, possibly annotator).

Second review pass (see `METHODOLOGY.md` §9) resolved all remaining open items:
- **≥2 models per size class** (not 1) — design is now 3 regimes × 4 `model_id` × 3 runs = 36
  generations/sentence (2× cost vs. the original single-model-per-class plan); cost mitigation
  options logged in `METHODOLOGY.md` §5 (trim N first, not runs/models).
- **Sampling scope**: pool across all 4 KUK sub-corpora, not a single one — avoids confounding
  length/depth effects with sub-corpus register.
- **CLTT conversion**: proceed with `udapi` (no existing UFAL-internal tool identified).
- Target N still finalized once `extract_pairs.py`/`sample_eval_set.py` exist and show the real
  filtering yield.

Design is locked pending supervisor sign-off; no code written yet.

---

## 2. Proposed repo structure (`experiment_01/`)

```
experiment_01/
  docs/
    chat.md                          # original notes (done)
    SPRINT_pro_legislativni_tvorbu.md # context (done)
    nllp_sprint_llm_counting-1.pdf   # Grok draft paper (done)
    IMPLEMENTATION_PLAN.md           # this file
    METHODOLOGY.md                   # science spec (done)
  data/
    raw/                             # KUK_1.0/, cltt_2.0/ (downloaded, gitignored)
    processed/                       # filtered sentence pool, sampled eval set
    annotations/                     # human gold annotations (podmet/prisudek/distance) — deferred
  src/
    fetch_data.py                    # download + verify KUK/CLTT
    extract_pairs.py                 # parse CoNLL-U, extract (subject, predicate, distance) per sentence
    sample_eval_set.py               # stratified sampling, filtering (single nsubj-verb pair)
    prompts/
      raw_text.txt
      raw_to_conllu.txt
      conllu_input.txt
    run_llm.py                       # run all 3 regimes x N models over eval set
    score.py                         # role-F1, distance exact/±1/±2, MAE, consistency (3 runs, temp=0)
    error_analysis.py                # categorize failure types
  results/
    runs/                            # raw model outputs per condition (jsonl)
    tables/                          # aggregated metrics (csv/markdown) for the paper
  paper/
    (LaTeX source, if we want to edit Grok's PDF source directly instead of regenerating)
  README.md                          # how to reproduce
```

---

## 3. Phased plan

### Phase 0 — Setup & data acquisition — **done**
- KUK 1.0 and CLTT 2.0 downloaded via LINDAT DSpace REST API, checksum-verified, extracted to
  `experiment_01/data/raw/`. Both CC BY-NC-SA 4.0 (redistribution of small derived samples in a
  paper/repo is compatible with NC/SA use for academic publication; full-corpus redistribution
  would need attribution/share-alike compliance — not a concern for the sampled eval set).
- Confirmed UDPipe version producing KUK's silver CoNLL-U: **UDPipe 2, `czech-pdt-ud-2.15-241121`
  model** (plus NameTag 3 `nametag3-czech-cnec2.0-240830` for NE tags) — both CC BY-NC-SA licensed.
- Confirmed KUK 1.0 vs. KUK 0.0 vs. KUKY 1.0 relationship (see `METHODOLOGY.md` §4) — KUK 1.0 is
  the single dataset we need.
- CLTT 2.0 format confirmed as PML/Treex, not CoNLL-U — added as an explicit Phase 1/2 task
  (conversion) rather than assumed free.

### Phase 1 — Data preparation
- Parse CoNLL-U files; for each sentence extract candidate (podmět, přísudek) pair via `nsubj`/
  `csubj` dependent of root/verbal head, per the formal definition in the draft.
- Filter to sentences with **exactly one** clear main-clause nsubj–verbal-head pair (per §3.2 of
  the draft); flag/exclude coordination and multiple finite verbs (or route to human judges for a
  "primary pair" annotation).
- Stratify by sentence length / embedding depth (the pilot in the draft already suggests length
  and relative-clause depth are the key difficulty drivers).
- Draw the evaluation sample (size depends on answer to open question 5).

### Phase 2 — Human validation layer (silver vs. gold)
- Run UDPipe on CLTT 2.0 text; compute LAS/UAS and nsubj-F1 vs. CLTT's manual gold — quantifies
  parser noise floor.
- Sample ~100 KUK sentences (or a smaller pilot number, e.g. 20–30) for two independent human
  annotations of (podmět, přísudek, distance); compute Cohen's κ and silver/gold disagreement
  rate.
- This phase can run in parallel with Phase 3 if annotators are lined up early — otherwise it's a
  bottleneck to flag now.

### Phase 3 — Prompting harness
- Implement the three prompt templates exactly as specified in the draft (Czech prompts,
  temperature 0).
- Wire up model clients for chosen small/large models (reuse SPRINT's `llm_client.py` pattern if
  useful — same provider abstraction).
- Run each condition **3× per sentence** (consistency check) for all (model × regime) pairs.
- Persist raw outputs (prompt, response, parsed fields) per run — auditability, mirrors SPRINT's
  existing philosophy of storing full trace.

### Phase 4 — Scoring & analysis
- Role identification F1 (surface form / lemma match against gold token id).
- Distance accuracy: exact, ±1, ±2 tolerance; MAE.
- Consistency: stddev across the 3 runs per condition.
- Error categorization: wrong clause attachment, off-by-one, mis-tokenization of multi-word legal
  terms, hallucinated CoNLL-U columns, etc. (qualitative + counts).
- Produce the tables/figures the paper needs (per-condition metrics, model-size x regime
  interaction).

### Phase 5 — Paper finalization
- Replace the qualitative "10-sentence pilot" section in the draft with real pilot/full results.
- Update abstract/conclusion with actual numbers once available.
- Fill in real model names/versions actually used (Grok's draft lists candidates, not
  necessarily what we'll use).
- Decide whether to keep working from the existing PDF/LaTeX or regenerate — need to locate/request
  the LaTeX source if we want to edit directly rather than re-prompting Grok.
- Final pass: author names (if de-anonymizing at submission), citation check, page-limit check (4
  pages, short paper).

---

## 4. Immediate next actions (proposed)

1. Answer the open questions in §1 (especially 1, 2, 5 — they gate everything else).
2. I fetch/inspect the two LINDAT items linked in `chat.md` to confirm which is raw vs.
   CoNLL-U-annotated KUK, and check CLTT 2.0 access requirements.
3. Scaffold `src/` with the fetch/extract scripts (no LLM calls yet) so we can inspect real data
   shape before committing to prompt formats.
4. Once data shape confirmed, build the pilot harness (small N, 1 small + 1 large model) end to
   end, then decide if we scale up.

---

## 5. Risks / things that could change the plan

- **CLTT 2.0 access friction** (manual request, license terms) could delay Phase 2 — worth
  checking immediately.
- **KUK 1.0 CoNLL-U quality on legal genre** may be worse than expected on long embedded
  sentences — exactly the phenomenon the paper is testing, so not fatal, but affects how much we
  can trust silver-only results without Phase 2.
- **API budget/rate limits** for the "large" model if it's a paid API — pilot-first approach
  mitigates this.
- **Filtering step** (single nsubj–verb pair) may throw away most legal sentences (legal Czech is
  full of coordination/long adjuncts) — may need the human "primary pair" fallback annotation
  described in the draft, which adds annotation burden.
