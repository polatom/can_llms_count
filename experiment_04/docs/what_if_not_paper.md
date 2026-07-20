# What would we do differently if SPRINT performance were the only goal?

Discussion note, 2026-07-20 (Tomáš + Claude). Thought experiment: drop the publishable-paper
goal; optimize purely for the performance of SPRINT's counting-based rules. What changes?

## 1. Ship the known answer instead of proving it

The engineering-optimal implementation of the subject–predicate distance rule is already known
(exp_01): UDPipe + deterministic extractor — ~99% where the parse commits, zero variance,
negligible cost. Pure-LLM is on the table only because of SPRINT's ops model (prose rules cheap,
code rules need engineering). The first engineering move is therefore not an experiment but a
one-time platform investment: a **structural rule engine** next to the LLM rule engine, exposing
parse-derived quantities (distances, clause counts, passives, depths) to lawyer-authored rules.
Experiment_04's RQ1 ("can pure-LLM match the parser?") is a question engineering doesn't need
answered — engineering happily uses the parser.

## 2. Build enumerate–classify–aggregate as a platform feature, not a hypothesis

For rules the parser can't serve (rule-defined countables — TooManyNegation is the archetype),
the fix is generic: one shared pre/post layer — numbered words into the prompt, the model
classifies/selects items, code counts, compares to the threshold, validates (form-at-index),
retries once, **abstains on failure**. ~50 lines serving every counting rule SPRINT will ever
have. It converts the LLM's job from what it is bad at (counting) to what it is good at
(classification), across the whole rule family at once. The paper deliberately excludes this
layer to keep the pure-LLM question clean; engineering would build it first.

## 3. Iterate prompts freely, on silver

The paper freezes one R1 and one R2 and buys gold to score them. Engineering follows SPRINT's own
rule lifecycle: dev/test split, iterate the rule text like code until testset F1 plateaus,
version in `rule_history`. Dev data can be **silver** (UDPipe labels are free at 10k-sentence
scale; label noise barely matters while climbing a gradient). Human eyes only on the final
acceptance set. Katka's definition work remains fully load-bearing either way — any
implementation needs the operationalized definition.

## 4. Optimize precision and abstention, not balanced F1

A linter lives and dies by precision — false flags erode lawyer trust much faster than misses
erode value. Graceful degradation: abstain-and-log beats confidently-wrong. Tune the
near-threshold band (d ∈ 5–8) specifically. And move evaluation into production: SPRINT already
stores accept/reject feedback per violation — that telemetry, per rule version, beats any offline
benchmark. Wire a dashboard, not a figure.

## 5. Collapse the model grid

No 4 model-modes × 2 formulations × 3 runs, no anti-caching protocol, no McNemar. Fix the
deployment envelope first (allowed models: cost, latency, data-residency for legislative drafts),
pick one model inside it, iterate, ship behind a flag, A/B against the current rule.
Run-consistency gets one sanity check, not a study.

## 6. Segmentation gets MORE attention, not less

Exp_01 showed sentence boundaries are the largest upstream error source in legal text, and every
counting rule inherits them. The paper holds segmentation fixed and footnotes it. Engineering
would audit how SPRINT actually chunks documents into units — likely a bigger real-world accuracy
lever than anything inside the rule prompt.

## What survives under both framings (dual-use artifacts)

- Katka's predicate operationalization (§3) — the deterministic extractor needs it too.
- The CLTT-derived validation of the extraction rule — QA for the structural engine.
- The counting-must-be-externalized insight and the R2 procedural pattern — R2 *is* the interim
  fix deployable today by editing rule text, whatever the paper concludes.

## The fork

The two goals diverge on the **first action**: the paper says "run the controlled comparison";
engineering says "build the structural engine + shared counting-safe layer and skip the
question." Which framing pays off depends on SPRINT's appetite for platform work:

- **Engineering capacity exists** → the experiment's practical payoff shrinks to the R2 template
  and the triage principle; build the layers.
- **Prose-rules-only for the foreseeable future** → "how far can prose rules alone go" *is* the
  engineering question, and experiment_04 is close to what a pure-engineering effort would run
  anyway, minus the gold rigor.

Action item: put this fork explicitly to the SPRINT team (KMH) — the answer determines whether
the paper's conclusion lands as "here's your roadmap" or "here's why you need the engineers."
