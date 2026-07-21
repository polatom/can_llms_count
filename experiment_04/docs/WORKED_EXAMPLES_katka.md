# Worked examples for Katka — §3 extraction rule on CLTT gold trees

Purpose (METHODOLOGY §4.2): confirm that the mechanical rule (predicate = the
agreement-bearing element of the predicate complex; subject = nsubj head word) matches
your definition, per construction type. All examples below come from human-annotated
`cs_cltt` trees, so any error is in OUR rule, not in a parser.

How to read the examples:
- A sentence may contain **several** pairs (one per finite clause with an overt subject —
  relative clauses included). The ★ line is the pair illustrating the section's
  construction; the following line lists the sentence's remaining pairs for context.
- Long sentences are shown as numbered windows around the ★ pair; (…) marks omitted text.
- Section labels come from UD relations; for participial predicates the copular/passive
  distinction may blur — please judge the measured PAIR, the label is only a grouping.
- **Please mark each ✓ or correct it.**

Derivation over the whole treebank: 1121 sentences → 1586 pairs. Distribution: finite verb / l-participle: 1147, copular — finite copula (je): 350, passive — finite aux (je/bude vydána): 33, passive — past aux (byla vydána): 31, conditional (by): 9, aby/kdyby (absorbed by): 9, analytic — aux (jsem/bude …): 4, copular — past copula (byla): 3

## finite verb / l-participle  (1147 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-test.conllu::299`
  - 1:Ministerstvo 2:vede 3:registr 4:vydaných 5:standardů.
  - ★ featured pair: **Ministerstvo** (word 1) ↔ **vede** (word 2) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-dev.conllu::40`
  - 1:(4) 2:Rezervy 3:nesmějí 4:mít 5:aktivní 6:zůstatek.
  - ★ featured pair: **Rezervy** (word 2) ↔ **nesmějí** (word 3) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::146`
  - 1:Stanovená 2:doba 3:nesmí 4:přesáhnout 5:účetní 6:období.
  - ★ featured pair: **doba** (word 2) ↔ **nesmí** (word 3) → distance **0**
  - [ ] ✓ / correction: 

## copular — finite copula (je)  (350 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::260`
  - 1:Porušením 2:vzájemného 3:zúčtování 4:nejsou 5:případy 6:upravené 7:účetními 8:metodami.
  - ★ featured pair: **případy** (word 5) ↔ **nejsou** (word 4) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::257`
  - 1:Stanovení 2:těchto 3:povinností 4:na 5:smluvním 6:základě 7:není 8:dotčeno.
  - ★ featured pair: **Stanovení** (word 1) ↔ **není** (word 7) → distance **5**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::43`
  - 1:Informace 2:je 3:srovnatelná, 4:jestliže 5:splňuje 6:požadavky 7:stanovené 8:v 9:§_7_odst._3_až_5.
  - ★ featured pair: **Informace** (word 1) ↔ **je** (word 2) → distance **0**
  - [ ] ✓ / correction: 

## copular — past copula (byla)  (3 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-test.conllu::2`
  - 1:Nástupnická 2:účetní 3:jednotka, 4:která 5:nebyla 6:zúčastněnou 7:účetní 8:jednotkou, 9:otevírá 10:účetní 11:knihy 12:ke 13:dni 14:zápisu 15:přeměny 16:společnosti 17:do 18:obchodního 19:rejstříku 20:s 21:účinky 22:od 23:rozhodného 24:dne 25:v 26:souladu 27:s 28:metodou 29:přeměny 30:společnosti.
  - ★ featured pair: **která** (word 4) ↔ **nebyla** (word 5) → distance **0**
  - all other pairs in this sentence: jednotka@3 ↔ otevírá@9 (d=5)
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::449`
  - (…) 31:který 32:je 33:účetní 34:jednotkou, 35:nástupnická 36:účetní 37:jednotka, 38:která 39:nebyla 40:zúčastněnou 41:účetní 42:jednotkou, 43:nebo 44:účetní 45:jednotka 46:uvedená (…)
  - ★ featured pair: **která** (word 38) ↔ **nebyla** (word 39) → distance **0**
  - all other pairs in this sentence: den@8 ↔ neshoduje@9 (d=0); společnost@19 ↔ upraví,@49 (d=29); která@20 ↔ je@21 (d=0); který@31 ↔ je@32 (d=0)
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-dev.conllu::143`
  - (…) 160:finančního 161:majetku 162:a 163:způsob 164:jejich 165:zaúčtování; 166:pokud 167:nebyl 168:cenný 169:papír, 170:podíl 171:a 172:derivát 173:oceněn 174:reálnou 175:hodnotou 176:nebo (…)
  - ★ featured pair: **papír** (word 169) ↔ **nebyl** (word 167) → distance **1**
  - all other pairs in this sentence: jednotka@4 ↔ uvede@8 (d=3); které@26 ↔ jsou@27 (d=0); které@65 ↔ jsou@66 (d=0); jednotka@180 ↔ uvede@178 (d=1); které@192 ↔ nejsou@193 (d=0); informace@200 ↔ jsou-li@198 (d=1); závazky@210 ↔ uvedou@208 (d=1); kategorie@245 ↔ liší@251 (d=5); prodej@258 ↔ je@256 (d=1); které@275 ↔ nejsou@276 (d=0); rizika@288 ↔ jsou@287 (d=0); zveřejnění@298 ↔ je@297 (d=0); jednotka@322 ↔ uzavřely@335 (d=12); které@354 ↔ jsou@355 (d=0); transakce@364 ↔ jsou@362 (d=1); informace@388 ↔ jsou@386 (d=1); výraz@400 ↔ má@403 (d=2)
  - [ ] ✓ / correction: 

## conditional (by)  (9 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::87`
  - 1:Stav 2:oprávek 3:je 4:dán 5:součtem 6:odpisů, 7:které 8:by 9:byly 10:účtovány 11:podle 12:odpisového 13:plánu 14:za 15:dobu 16:používání 17:do 18:okamžiku 19:přechodu 20:z 21:daňové 22:evidence 23:na 24:účetnictví.
  - ★ featured pair: **které** (word 7) ↔ **by** (word 8) → distance **0**
  - all other pairs in this sentence: Stav@1 ↔ je@3 (d=1)
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::92`
  - 1:(6) 2:Účetní 3:jednotky, 4:které 5:mají 6:povinnost 7:ověřování 8:podle 9:§_20, 10:nesmí 11:zveřejnit 12:informace, 13:které 14:předtím 15:nebyly 16:ověřeny 17:auditorem, 18:způsobem, 19:který 20:by 21:mohl 22:uživatele 23:uvést 24:v 25:omyl, 26:že 27:auditorem 28:ověřeny 29:byly.
  - ★ featured pair: **který** (word 19) ↔ **by** (word 20) → distance **0**
  - all other pairs in this sentence: jednotky@3 ↔ nesmí@10 (d=6); které@4 ↔ mají@5 (d=0); které@13 ↔ nebyly@15 (d=1)
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-dev.conllu::251`
  - 1:Tam, 2:kde 3:účetní 4:jednotka 5:může 6:volit 7:mezi 8:více 9:možnostmi 10:dané 11:účetní 12:metody 13:a 14:zvolená 15:možnost 16:by 17:zastírala 18:skutečný 19:stav, 20:je 21:účetní 22:jednotka 23:povinna 24:zvolit 25:jinou 26:možnost, 27:která 28:skutečnému 29:stavu 30:odpovídá.
  - ★ featured pair: **možnost** (word 15) ↔ **by** (word 16) → distance **0**
  - all other pairs in this sentence: jednotka@4 ↔ může@5 (d=0); jednotka@22 ↔ je@20 (d=1); která@27 ↔ odpovídá.@30 (d=2)
  - [ ] ✓ / correction: 

## aby/kdyby (absorbed by)  (9 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::115`
  - 1:Vyloučením 2:se 3:rozumí 4:takové 5:operace, 6:které 7:umožní, 8:aby 9:konsolidovaná 10:účetní 11:závěrka 12:neobsahovala 13:vzájemné 14:transakce, 15:které 16:byly 17:realizovány 18:účetními 19:jednotkami 20:v 21:konsolidaci.
  - ★ featured pair: **závěrka** (word 11) ↔ **aby** (word 8, measured token: by) → distance **2**
  - all other pairs in this sentence: operace@5 ↔ rozumí@3 (d=1); které@6 ↔ umožní,@7 (d=0); které@15 ↔ byly@16 (d=0)
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::286`
  - 1:(4) 2:Okamžik 3:se 4:v 5:účetním 6:záznamu 7:zaznamenává 8:s 9:takovou 10:přesností, 11:aby 12:nejistota 13:v 14:určení 15:času 16:neměla 17:za 18:následek 19:nejistotu 20:v 21:určení 22:obsahu 23:účetních 24:případů.
  - ★ featured pair: **nejistota** (word 12) ↔ **aby** (word 11, measured token: by) → distance **0**
  - all other pairs in this sentence: Okamžik@2 ↔ zaznamenává@7 (d=4)
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::140`
  - 1:Pokud 2:banka 3:umožňuje, 4:aby 5:byl 6:ke 7:konci 8:rozvahového 9:dne 10:vykázán 11:pasivní 12:zůstatek 13:u 14:běžného 15:účtu, 16:pak 17:je 18:tento 19:zůstatek 20:obsahem 21:položky 22:„B.IV.2. 23:Krátkodobé 24:bankovní 25:úvěry“.
  - ★ featured pair: **zůstatek** (word 12) ↔ **aby** (word 4, measured token: by) → distance **7**
  - all other pairs in this sentence: banka@2 ↔ umožňuje,@3 (d=0); zůstatek@19 ↔ je@17 (d=1)
  - [ ] ✓ / correction: 

## passive — finite aux (je/bude vydána)  (33 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::250`
  - 1:Zobrazení 2:je 3:poctivé, 4:když 5:jsou 6:při 7:něm 8:použity 9:účetní 10:metody 11:způsobem, 12:který 13:vede 14:k 15:dosažení 16:věrnosti.
  - ★ featured pair: **účetní** (word 9) ↔ **jsou** (word 5) → distance **3**
  - all other pairs in this sentence: Zobrazení@1 ↔ je@2 (d=0); který@12 ↔ vede@13 (d=0)
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::296`
  - 1:Účetní 2:jednotka 3:dále 4:uvede 5:informace 6:o 7:druzích 8:zvířat, 9:která 10:jsou 11:vykazována 12:jako 13:dlouhodobý 14:hmotný 15:majetek 16:a 17:zásoby.
  - ★ featured pair: **která** (word 9) ↔ **jsou** (word 10) → distance **0**
  - all other pairs in this sentence: jednotka@2 ↔ uvede@4 (d=1)
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::410`
  - 1:Do 2:nákladů 3:nebo 4:výnosů 5:jsou 6:zaúčtovány 7:ve 8:stejných 9:obdobích, 10:kdy 11:jsou 12:zaúčtovány 13:náklady 14:nebo 15:výnosy 16:spojené 17:se 18:zajišťovanými 19:položkami.
  - ★ featured pair: **náklady** (word 13) ↔ **jsou** (word 11) → distance **1**
  - [ ] ✓ / correction: 

## passive — past aux (byla vydána)  (31 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-test.conllu::314`
  - 1:Obdobně 2:se 3:postupuje, 4:pokud 5:účetní 6:závěrka 7:nebo 8:konsolidovaná 9:účetní 10:závěrka 11:nebyla 12:za 13:dané 14:účetní 15:období 16:sestavena.
  - ★ featured pair: **závěrka** (word 6) ↔ **nebyla** (word 11) → distance **4**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::285`
  - 1:Účetní 2:jednotka 3:uvede 4:dále, 5:zda 6:byly 7:uzavřeny 8:ovládací 9:smlouvy 10:nebo 11:smlouvy 12:o 13:převodech 14:zisku 15:a 16:jaké 17:povinnosti 18:z 19:nich 20:vyplývají.
  - ★ featured pair: **smlouvy** (word 9) ↔ **byly** (word 6) → distance **2**
  - all other pairs in this sentence: jednotka@2 ↔ uvede@3 (d=0); povinnosti@17 ↔ vyplývají.@20 (d=2)
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::308`
  - 1:Informace 2:podle 3:písmen 4:a)_a_b) 5:není 6:účetní 7:jednotka 8:povinna 9:uvést, 10:pokud 11:byly 12:transakce 13:provedeny 14:mezi 15:účetní 16:jednotkou 17:a 18:jejím 19:jediným 20:společníkem.
  - ★ featured pair: **transakce** (word 12) ↔ **byly** (word 11) → distance **0**
  - all other pairs in this sentence: jednotka@7 ↔ není@5 (d=1)
  - [ ] ✓ / correction: 

## analytic — aux (jsem/bude …)  (4 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-test.conllu::166`
  - 1:(4) 2:Účetní 3:jednotky, 4:které 5:nejsou 6:založeny 7:nebo 8:zřízeny 9:za 10:účelem 11:podnikání, 12:uplatňují 13:ustanovení 14:odstavců 15:1 16:až 17:3 18:v 19:souladu 20:s 21:účetními 22:metodami.
  - ★ featured pair: **které** (word 4) ↔ **nejsou** (word 5) → distance **0**
  - all other pairs in this sentence: jednotky@3 ↔ uplatňují@12 (d=8)
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::144`
  - 1:V 2:případě 3:nákupu 4:nebo 5:prodeje 6:cizí 7:měny 8:za 9:českou 10:měnu 11:lze 12:k 13:okamžiku 14:ocenění 15:použít 16:kurzu, 17:za 18:který 19:byly 20:tyto 21:hodnoty 22:nakoupeny 23:nebo 24:prodány.
  - ★ featured pair: **hodnoty** (word 21) ↔ **byly** (word 19) → distance **1**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::108`
  - 1:Položka 2:obsahuje 3:dále 4:výrobky 5:vlastní 6:výroby, 7:které 8:byly 9:aktivovány 10:a 11:předány 12:do 13:vlastních 14:prodejen, 15:a 16:zvířata 17:vlastního 18:chovu, 19:která 20:dospěla, 21:byla 22:aktivována 23:a 24:jsou 25:určena 26:k 27:prodeji 28:s 29:výjimkou 30:jatečných 31:zvířat.
  - ★ featured pair: **které** (word 7) ↔ **byly** (word 8) → distance **0**
  - all other pairs in this sentence: Položka@1 ↔ obsahuje@2 (d=0); která@19 ↔ dospěla,@20 (d=0)
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
