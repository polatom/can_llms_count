# Worked examples for Katka — §3 extraction rule on CLTT gold trees

Purpose (METHODOLOGY §4.2): confirm that the mechanical rule (predicate = finite element
of the predicate complex; subject = nsubj head word) matches your definition, per
construction type. All examples below come from human-annotated `cs_cltt` trees, so any
error is in OUR rule, not in a parser. For each: numbered words, the extracted pair,
the distance (words strictly between). **Please mark each ✓ or correct it.**

Derivation over the whole treebank: 1121 sentences → 1550 pairs. Distribution: finite verb / l-participle: 1147, copular (copula): 350, passive (finite aux): 33, conditional (by): 9, aby/kdyby (absorbed by): 9, analytic (finite aux): 2

## finite verb / l-participle  (1147 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::6`
  - 1:Zbytkovou 2:hodnotou 3:se 4:rozumí 5:snížená 6:předpokládaná 7:zbytková 8:hodnota.
  - pair: **hodnota** (word 8) ↔ **rozumí** (word 4) → distance **3**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-dev.conllu::7`
  - 1:Účetní 2:jednotky 3:neprovádějí 4:účetní 5:operace 6:opravující 7:výši 8:vykázaných 9:odpisů 10:a 11:oprávek 12:v 13:předchozích 14:účetních 15:obdobích.
  - pair: **jednotky** (word 2) ↔ **neprovádějí** (word 3) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-dev.conllu::9`
  - 1:Ložisko 2:těžené 3:podle 4:horních 5:předpisů 6:se 7:odpisuje 8:sazbou 9:na 10:jednotku 11:těženého 12:množství 13:na 14:základě 15:skutečné 16:těžby.
  - pair: **Ložisko** (word 1) ↔ **odpisuje** (word 7) → distance **5**
  - [ ] ✓ / correction: 

## copular (copula)  (350 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::12`
  - 1:(6) 2:Dlouhodobý 3:nehmotný 4:a 5:hmotný 6:majetek, 7:který 8:je 9:majetkem 10:bytových 11:družstev, 12:pokud 13:neslouží 14:k 15:podnikání, 16:se 17:nemusí 18:odpisovat.
  - pair: **který** (word 7) ↔ **je** (word 8) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-dev.conllu::28`
  - 1:Pokud 2:vyřazovaná 3:komponenta 4:není 5:k 6:okamžiku 7:vyřazení 8:odepsána 9:do 10:výše 11:jejího 12:ocenění, 13:provede 14:účetní 15:jednotka 16:odpis 17:zůstatkové 18:ceny 19:vyřazované 20:komponenty 21:do 22:nákladů.
  - pair: **komponenta** (word 3) ↔ **není** (word 4) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-dev.conllu::52`
  - 1:(2) 2:Výpočet 3:odložené 4:daně 5:je 6:založen 7:na 8:závazkové 9:metodě 10:vycházející 11:z 12:rozvahového 13:přístupu.
  - pair: **Výpočet** (word 2) ↔ **je** (word 5) → distance **2**
  - [ ] ✓ / correction: 

## conditional (by)  (9 pairs in CLTT)

*(no clean short example found in CLTT — will supply one from KUK)*

## aby/kdyby (absorbed by)  (9 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::115`
  - 1:Vyloučením 2:se 3:rozumí 4:takové 5:operace, 6:které 7:umožní, 8:aby 9:konsolidovaná 10:účetní 11:závěrka 12:neobsahovala 13:vzájemné 14:transakce, 15:které 16:byly 17:realizovány 18:účetními 19:jednotkami 20:v 21:konsolidaci.
  - pair: **závěrka** (word 11) ↔ **aby** (word 8, measured token: by) → distance **2**
  - [ ] ✓ / correction: 

## passive (finite aux)  (33 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::250`
  - 1:Zobrazení 2:je 3:poctivé, 4:když 5:jsou 6:při 7:něm 8:použity 9:účetní 10:metody 11:způsobem, 12:který 13:vede 14:k 15:dosažení 16:věrnosti.
  - pair: **účetní** (word 9) ↔ **jsou** (word 5) → distance **3**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::172`
  - 1:(5) 2:Tržní 3:hodnotou 4:se 5:rozumí 6:hodnota, 7:která 8:je 9:vyhlášena 10:na 11:evropském 12:regulovaném 13:trhu 14:nebo 15:na 16:zahraničním 17:trhu 18:obdobném 19:regulovanému 20:trhu.
  - pair: **která** (word 7) ↔ **je** (word 8) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::267`
  - 1:Na 2:obě 3:formy 4:podpisového 5:záznamu 6:se 7:přitom 8:pohlíží 9:stejně 10:a 11:obě 12:mohou 13:být 14:použity 15:v 16:případech, 17:kdy 18:je 19:vyžadován 20:vlastnoruční 21:podpis.
  - pair: **podpis** (word 21) ↔ **je** (word 18) → distance **2**
  - [ ] ✓ / correction: 

## analytic (finite aux)  (2 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-test.conllu::166`
  - 1:(4) 2:Účetní 3:jednotky, 4:které 5:nejsou 6:založeny 7:nebo 8:zřízeny 9:za 10:účelem 11:podnikání, 12:uplatňují 13:ustanovení 14:odstavců 15:1 16:až 17:3 18:v 19:souladu 20:s 21:účetními 22:metodami.
  - pair: **které** (word 4) ↔ **nejsou** (word 5) → distance **0**
  - [ ] ✓ / correction: 

## Open category — verbless clauses (new question, K7)

UD sometimes attaches an overt subject to a **non-verbal head with no copula**
(typically a short-form adjective/participle: *„Vstup zakázán“*-type, or elliptical
constructions). Our current rule **excludes** these (no finite element to measure to)
and logs them — they are ~8% of subject edges in the KUK sample (mostly ADJ heads).
Question: exclude (current), or measure to the non-verbal head itself?

- `cs_cltt/cs_cltt-ud-dev.conllu::205`: Hospodářským rokem je účetní období, které může začínat pouze prvním dnem jiného měsíce, než je leden.
- `cs_cltt/cs_cltt-ud-dev.conllu::272`: (1) Nestanoví-li tento zákon nebo zvláštní právní předpis jinak, účetní jednotky jsou povinny vést účetnictví v plném rozsahu.
- `cs_cltt/cs_cltt-ud-test.conllu::127`: (2) Konsolidující účetní jednotky neuvedené v odstavci 1 mohou pro sestavení konsolidované účetní závěrky použít mezinárodní účetní standardy.
- `cs_cltt/cs_cltt-ud-test.conllu::223`: Nestanoví-li tento zákon jinak, platí pro nakládání s nimi zvláštní právní předpisy.

- [ ] exclude (current rule)   [ ] measure to the head   [ ] other: 
