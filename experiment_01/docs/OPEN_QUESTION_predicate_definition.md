# Open question for linguist review — how to operationalize "predicate" (přísudek)

Status: **open — needs a linguist decision.** Working assumption is locked in `METHODOLOGY.md` §2
as *provisional*; this document exists so a linguist colleague can confirm or overrule it without
reading the whole methodology.

## Context in one paragraph

We are measuring the **linear distance between the subject (podmět) and the predicate (přísudek)**
of the main clause of a Czech legal sentence, as an objective, automatically-scoreable probe of
whether LLMs can "count." Ground truth comes from UDPipe's Universal Dependencies (UD) parses of
KUK 1.0 (silver standard). The distance is:

```
d = (number of whitespace-separated words strictly between subject word and predicate word)
  = |p − q| − 1
```

where `p` and `q` are the word positions of the subject and the predicate. To compute `d`
mechanically for hundreds of thousands of sentences, we need an **unambiguous, reproducible rule**
for which token is "the subject" and which is "the predicate." The subject is easy (the UD `nsubj`
relation). **The predicate is the question.**

## The proposed rule (please confirm or correct)

- **Subject** `p` = the word bearing the `nsubj` (or `nsubj:pass`, passive subject) relation whose
  head is the sentence root. We restrict to sentences with **exactly one** such subject (no
  coordination, one main finite clause).
- **Predicate** `q` = **the head word of that subject**, whatever its part of speech — i.e. we just
  follow the `nsubj` arc up one step to its head.

### Why "head of the subject" rather than "the finite verb"

1. It is *exactly* the head–dependent pair that the dependency-distance / cognitive-load literature
   measures (this is what grounds the whole metric as more than an ad-hoc token count).
2. It is fully deterministic — no need to search the tree for "the verb."
3. **Copular / nominal-predicate clauses fall out correctly for free.** In UD, a sentence like
   *"Podmínkou **je** vydání rozhodnutí"* ("The condition **is** the issuance of a decision") is
   annotated with the **nominal** predicate as the root, the copula *je* attached to it as `cop`,
   and the subject attached to the nominal:

   ```
   nsubj(vydání → Podmínkou)   # subject "Podmínkou"
   cop(vydání → je)            # copula "je" is a dependent, NOT the head
   root(vydání)               # the nominal is the head
   ```

   Under "head of the subject", the predicate is **vydání** (the nominal part, *jmenná část
   přísudku*) — which matches the Czech grammatical notion of *jmenný přísudek se sponou*. Measuring
   to the copula *je* instead would be the non-standard choice.

### What we log as a safety net

Because the copula case is the one most likely to be contested, for every sentence we **also record
the copula token index** (if any) as a secondary field. That means if the linguist prefers
"distance to the copula" for copular clauses, we can recompute both variants from the stored data
**without re-running** the whole pipeline.

## The specific decisions we want a linguist to sign off on

1. **Copular clauses**: is "distance to the nominal predicate (head of subject)" the right target,
   or should it be "distance to the copula (*je/jsou/byl…*)"? (Our default: nominal predicate.)
2. **Passive subjects** (`nsubj:pass`, e.g. *"Rozhodnutí **bylo vydáno**"*): we currently treat
   these exactly like active subjects and measure to their head (the participle). OK?
3. **Clausal subjects** (`csubj`, where the subject is itself a whole clause, e.g. *"Kdo mlčí,
   souhlasí"*): we currently **exclude** these from the primary set (a clause has no single "word
   position" for the subject) and only report how many there were. OK to exclude, or is there a
   principled single-token choice you'd prefer?
4. **Sentence scope**: we take only the **main-clause** subject–predicate pair (subject whose head
   is the sentence root) and drop sentences with multiple finite clauses / coordinated subjects.
   Any concern that this biases the sample toward "easy" sentences in a way that matters
   linguistically?

## Non-questions (already settled, just for context)

- Distance is counted in **whitespace-separated words**, not UD tokens — so punctuation glued to a
  word, and Czech split-tokens like *aby → aby + by*, count as one word. This is settled; it only
  affects the *counting*, not the *definition of subject/predicate*.
- We measure **agreement with UDPipe**, not with linguistic truth (silver standard). A separate
  parser-quality control against the `cs_cltt` gold treebank estimates how noisy UDPipe is on legal
  Czech.

## TL;DR for the linguist

> "We define the předicate as the UD head of the subject (so for *X je Y* it's the nominal *Y*, not
> the copula *je*), skip clausal subjects, and keep only single-main-clause sentences. Does that
> match how you'd identify podmět/přísudek for measuring the distance between them? We store the
> copula position too, so 'measure to the copula' is recoverable if you prefer it."
