# Katka — feedback on the prompts (2026-07-21) + disposition

Decision (Tomáš): frozen prompts R1–R4 are NOT changed (results are tied to their SHAs); each
point below is assessed and carried into the next formulation (R5, if any), the paper's
limitations/wording, or dismissed with a measured reason. K11 (Jsou-li = whole word) was
confirmed verbally on the call.

## Verbatim

> **Naive:** definice podmětu — explicitně uvádí pouze zájmena a "jména". Hádám, že to mají být
> podstatná jména. Definice je problematická, protože přehlíží edge cases, ve kterých jsou
> podmětem jiné slovní druhy. Např. "Rychle je lepší než pomalu." Pokud chceme takové případy
> vyřadit z analýzy, je potřeba to explicitně rozhodnout.
>
> **Procedural, krok 1:** "Najdi všechny určité (finitní) klauze věty" — finitní klauze je podle
> mě nesmysl. V určitém tvaru je sloveso, nikoli věta/clause. — k "aby" přidat "kdyby".
> **Krok 2:** stejný problém s definicí podmětu jako u Naive. "JEDEN pár, s prvním slovesem" —
> možná upřesnit? První sloveso od určeného podmětu? **Krok 5:** "Neshodu oprav před odpovědí."
> — nevím, jestli to není málo detailní. "V případě najití neshody zopakuj kroky 3, 4 a 5."
>
> **Procedural inventory, krok 1:** zvláštní formulace — kategorie jen pro slovesa, jinak
> "slova". Určité sloveso: "dá se před něj doplnit ‚on/oni'" — jak by to fungovalo s jinými
> osobami? "Oni půjdeme"? **Krok 3:** u výčtu vztažných zájmen použít uvozovky.

## Assessment and disposition

1. **Non-nominal subjects ("Rychle je lepší než pomalu.")** — measured in the CLTT gold:
   subject UPOS = NOUN 1289, DET 285 (mostly relative/demonstrative pronouns tagged DET), PRON 5,
   **ADV 4, NUM 2, X 1** → non-nominal subjects are **7 of 1,586 pairs (0.4%)**. The gold
   *includes* them (extraction is POS-agnostic: any `nsubj` head); the prompts under-describe
   them. Disposition: prompt wording for R5 broadened ("podmět je nejčastěji jméno nebo
   zájmeno; výjimečně jiný výraz — rozhoduje otázka kdo/co a shoda"); paper notes the 0.4%
   explicitly. NOT a rerun-worthy defect.
2. **"Finitní klauze" is sloppy terminology** — correct; the finite element is the verb, not
   the clause. R5 wording: „věty (klauze) s určitým slovesným tvarem". Also fix in the paper's
   prompt description. (English "finite clause" is standard, so the EN text is fine.)
3. **kdyby examples in R2** — R2's rule line covers aby/kdyby but examples show only aby;
   R3/R4 closed lists already include all kdyby forms. R5: add one kdyby example.
4. **"JEDEN pár s prvním slovesem" under-specified** — gold convention is precise (the verb
   bearing the subject relation = the first conjunct of the coordination); prompt should say
   „s prvním slovesem té koordinace (tím, u kterého podmět stojí)". R5 + paper.
5. **KROK 5 self-check too shallow** — adopt her formulation for R5: „v případě neshody zopakuj
   kroky 3–5". (Frozen R3/R4 keep the weaker check; the measured form-at-index catch-rates
   quantify what it missed.)
6. **"on/oni" finiteness test fails for 1st/2nd person** — valid; legal text is overwhelmingly
   3rd person (exp_01/exp_04 corpora), so measured impact ≈ nil, but the test as stated is
   wrong. R5: „vyjadřuje osobu a číslo (on rozhodne / oni rozhodnou / já rozhodnu…)".
7. **Cosmetics** (inventory category framing; quotes around the pronoun list) — R5.

## Standing note

R5 is NOT currently planned — R4 (running) already implements her K10 algorithm; whether a
further formulation iteration is worth it depends on R4's results and the frontier decision.
This file is the changelog to draw from if/when R5 happens, and the source for the paper's
"prompt development" narrative (linguist-in-the-loop iterations).
