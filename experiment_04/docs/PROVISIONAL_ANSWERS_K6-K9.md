# Provisional answers to K6–K9 (self-adjudicated 2026-07-20; Katka verifies)

Decision (Tomáš, 2026-07-20): to avoid blocking on review latency, the open linguistic
questions are answered below *as best we can*, the design proceeds with them closed, and Katka
verifies asynchronously. If she flags an impactful difference, the affected parts re-run as a
follow-up experiment. Measured sensitivities (PARSER_ARM_ERROR_ANALYSIS.md) say the verdict-level
impact of K7/K8 is ≤0.3 pt F1; only K6 could touch the LLM prompts.

## K6 — shared-subject predicate coordination → ONE PAIR (first verb)

*„Ministr návrh podepsal a odeslal."* → one pair (Ministr ↔ podepsal).
Rationale: (a) mechanically UD-native — only the first conjunct bears `nsubj`, so gold and all
arms apply the identical convention with zero special-casing; (b) consistent with Katka's K1
logic (measure to the element that establishes agreement with the subject — the reader resolves
the subject–predicate link at the *first* verb; later conjuncts inherit it); (c) the alternative
(one pair per conjunct) is fully recomputable: annotation/verification sheets flag further
conjunct verbs, and the extraction rule change is ~5 lines + rescoring.
Risk if reversed: R1/R2 prompts state the one-pair convention → LLM re-runs needed. Accepted.

KH: yes, one pair, because "odeslal" is a new clause

## K7 — verbless clauses with an overt subject → EXCLUDE (logged)

*„Vstup zakázán."*-type (no copula/aux at all). Rationale: Katka's definition measures to the
element carrying agreement with the subject; a verbless clause has no such element, so there is
nothing to measure to *within her definition* — exclusion is the definition-consistent choice,
not a convenience. Prevalence: 46 subject edges in CLTT (vs. 1,586 pairs), 2/719 in KUK-640;
counted and reported either way.

KH: yes, no finite verb, no clause

## K8 — relative-pronoun subjects → INCLUDE in headline, report separately

*„…, které by podstatným způsobem ovlivnily…"* → pair (které ↔ by). Rationale: (a) the
signed-off definition says *all finite clauses with an overt nominal subject* — relative
pronouns are overt nominal subjects, and carving them out would be a post-hoc definition edit;
(b) comprehensibility-wise a relative clause's subject–predicate span is a real processing span
(usually short: distances 0–1, which is *information*, not noise); (c) measured verdict impact
of excluding them: F1 91.3 → 91.0 (negligible). The `subj_is_rel` flag is in every artifact, so
the excluded view is one groupby away and will appear in the breakdowns table.

KH: yes, "ktere"-"by" pair

## K9 — worked examples → self-reviewed, provisionally confirmed

The 24 examples in WORKED_EXAMPLES_katka.md were re-checked against §3.1 construction by
construction (copula → *je*; past copula/passive → *byla*; conditional → *by* wherever it
stands; aby/kdyby → the conjunction word via the MWT collapse — verified directly in `cs_cltt`
annotation; bare l-participle → the verb itself). No discrepancies found by us; the two
constructions most likely to be contested (past copula, past passive) are exactly the ones the
review sheet highlights for Katka.

## Threshold (her question 6) → CLOSED

Violation ⇔ d > 6 (seven or more words strictly between), sentence flagged if ANY pair
violates. Matches both PONK ("limit distance 6" as maximum allowed) and the production rule
("at least 7 words"). No open interpretation remains.

## Consequences

- §3 rule and gold are FROZEN as of these answers; prompts R1/R2 freeze after the smoke test.
- Verification sheet (105 pairs) goes to Katka as *verification of a live gold*, not a blocker.
- If Katka overturns K6 → re-derive gold (minutes) + re-run LLM grids (open: trivial cost;
  frontier: only what has been run by then — another reason the frontier waits).
- If she overturns K7/K8 → rescoring only, no re-runs.


## K11 — Jsou-li = whole word (added 2026-07-21)

Confirmed verbally by Katka on the 2026-07-21 call (Tomáš relayed): the measured predicate for
"Jsou-li/není-li"-type forms is the whole surface word, analogous to aby/kdyby.

## Status: ALL K-questions closed (2026-07-21)

K6/K7/K8 confirmed in writing (KH annotations above), K9 confirmed ("Všechny worked examples
jsou dobře"), K10 answered with the elimination algorithm (see
KATKA_K10_relative_pronouns_2026-07-21.md), K11 confirmed verbally. The §3 rule and the
CLTT-derived gold are fully signed off; the verification sheet remains as an async
quality-measurement task, not a blocker.
