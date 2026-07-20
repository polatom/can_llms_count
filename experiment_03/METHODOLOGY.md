# Experiment 03 — Methodology (design sketch)

Status: **sketch — not scheduled.** Captures the "scenario 2" design converged on 2026-07-17 so
it survives until exp_02 delivers its prerequisites (§6). Numbers marked ~ are placeholders to be
fixed from exp_02 outputs.

---

## 1. Goal

**Can an LLM improve parser-based subject–predicate extraction *where the parser actually
breaks* — the complex, pathological legal sentences that are also exactly where comprehensibility
is compromised?**

Exp_01/exp_02 establish the division of labor on *typical* text: deterministic extraction wins,
LLM counting is the weak link. But the deterministic pipeline's errors concentrate in long,
multi-clause, heavily embedded sentences — the very population a comprehensibility linter exists
to flag. On that population the parser baseline is far below its headline accuracy, there is real
headroom, and the LLM's comparative advantage (semantics: agreement plausibility, argument
structure, legal-domain knowledge) is actually engaged. This is the scientifically interesting
regime and the practically decisive one: a linter that fails precisely on the pathological
sentences fails at its job.

## 2. Why this must be a separate paper (the power argument)

On a *random* sample of legal Czech the parser is right on the order of ~90–95%+ of sentences
(exp_02 §5.1 — the "parser arm" — measures this precisely). A 200-sentence random gold set then contains only ~10–20
parser-error cases — far too few to demonstrate any significant LLM gain, and the corrector must
also not break the ~180+ correct parses (LLM identification accuracy is itself ~85% at 70B,
per exp_01). A "boost" experiment on random data is doomed to an underpowered null result.

**The fix is enrichment sampling (§3): evaluate on a deliberately hard sample where the parser
baseline is low enough (~70–85%) for a gain to be measurable.** That changes the population, the
claim, and the annotation plan — a different paper, not a bigger exp_02.

## 3. Data — enrichment-sampled hard cases

Candidate hardness signals, to be combined (union, each flag logged as metadata):

- **Parser disagreement:** UDPipe vs. a second parser (Stanza / Trankit, Czech models) disagree
  on `nsubj` or on the §3-rule predicate for the same sentence. Cheap, principled, catches
  genuine ambiguity. (Caveat: also catches segmentation/tokenization mismatch — hold
  segmentation fixed as in exp_02 and diff only within identical sentence spans.)
- **Structural suspicion:** extreme length (top decile), clause count ≥ 3, deep embedding,
  non-projective arcs, multiple candidate nominatives (case-syncretism risk).
- **Exp_02 error inventory:** sentences where exp_02's parser arm disagreed with gold, and
  sentences where strong LLMs failed — imported directly (`experiment_02` deliverable 5).

Target: **N ≈ 300–400 enriched sentences**, human-annotated (same §3 task definition and
annotation guidelines as exp_02 — inherited, already signed off by Katka; the targeted-60 from
exp_02 serve as the annotation-protocol pilot). Double-annotation of a subset for IAA on *hard*
cases specifically — expected lower than exp_02's IAA; that number is itself a finding (how
well-defined is the task where it matters most?).

## 4. Conditions

1. **Parser alone** (UDPipe → §3 extractor) — the baseline whose failure motivates everything.
2. **Parser ensemble control** (UDPipe × Stanza agreement/voting) — the cheap non-LLM upgrade;
   the LLM must beat this to justify itself.
3. **Parser + LLM corrector** (the experimental arm): LLM receives the sentence + the parse
   (compact rendering) and may **confirm or amend** the subject/predicate pairs. Gating variants:
   (a) LLM sees all sentences; (b) LLM invoked only on flagged-hard sentences (disagreement /
   suspicion signals) — the deployable version.
4. **LLM alone** (best exp_02 configuration) — control: does the parse input help or hurt on
   hard sentences?

Model roster: the best-performing configurations from exp_02 (frontier ± reasoning, ~70B open);
no size ladder — the size question is answered by exp_02.

## 5. Metrics

- **Net correction rate** (primary): (parser errors fixed − correct parses broken) / parser
  errors, on hard-set gold. An LLM that fixes 20 and breaks 15 is noise; report both components.
- Pair identification P/R/F1 and distance accuracy on the hard set, per condition.
- Verdict impact at T = 6: how many *flag decisions* change, and in which direction.
- Per-phenomenon breakdown (which pathologies does the LLM actually help with: attachment?
  syncretism? coordination scope? pro-drop recovery?).
- Cost/latency of the gated pipeline vs. its accuracy gain.

## 6. Prerequisites (from exp_02) and open questions

Prerequisites: exp_02 error inventory + traces; measured parser-arm accuracy on unfiltered text
(the headroom number — if it comes out ≥ ~97%, this experiment shrinks or dies, honestly);
annotation guidelines + protocol; Katka's capacity for a second annotation round.

Open questions:
- **Q1:** second parser choice (Stanza vs. Trankit) and its Czech-legal behavior.
- **Q2:** gold for hard cases where even annotators disagree — adjudication protocol
  (Katka + second annotator + discussion?), or exclude-with-report.
- **Q3:** does the corrector see one parse or both (disagreeing) parses? (Both = "arbitration"
  framing, likely stronger prompt.)

## 7. Adjacent module (optional, needs data that does not yet exist)

**Semantic triage of correct flags** (from the exp_02-era brainstorming): among sentences where
the distance is *correctly* measured and d ≥ T, which flags reflect real comprehension difficulty
("needless" complexity vs. justified-but-hard)? Requires per-sentence human difficulty data
(reading times, comprehension tests, or ratings — LiFR-Law-style). Kept here as a named module so
it is not lost; it shares the hard-sentence population with the main design but is **blocked on
difficulty data** and would otherwise be graded against nothing.

## 8. Out of scope

Fine-tuning (parser or LLM); rewriting/simplification of flagged sentences (own project);
sentence segmentation (held fixed, again); new comprehensibility metrics (surprisal/DLT — future
work shared with the triage module).
