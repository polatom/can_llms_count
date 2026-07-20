# Otázky pro Katku — experiment_02 (2026-07-20)

Kontext: metodika experimentu_02 je zamrazená (METHODOLOGY.md v3.1), tvoje definice přísudku
z minulé revize je zapracovaná a mechanicky ověřená na CLTT (ručně anotované stromy). Zbývá
pár rozhodnutí a jedna kontrola. Odhad času: ~45–60 min na otázky 1–4, anotace (otázka 5) dle
tvých možností.

## 1. Kontrola pracovních příkladů (nejdůležitější)

V `docs/WORKED_EXAMPLES_katka.md` je ~20 příkladů z CLTT — pro každý typ konstrukce věta
s očíslovanými slovy, vyznačený pár podmět↔přísudek a spočítaná vzdálenost. Prosím projít a
u každého ✓ nebo oprava.

Zvláštní pozornost prosím dvěma nově doplněným řádkům (odhalila je kontrola dat):
- **minulé pasivum:** *„Dne 11. 7. 2013 **byla** provedena kontrola…"* — měříme k **byla**
  (pomocné sloveso; nese shodu v rodě a čísle). Souhlasíš?
- **minulá spona:** *„Spolupráce rodiny s centrem **byla** však krátkodobá…"* — měříme k
  **byla** (spona). Souhlasíš?

(Technické pozadí: v UD nejsou minulé tvary „být" značené jako finitní — jsou to l-příčestí.
Pravidlo jsme upravili: 1. finitní aux/spona → 2. příčesťové aux/spona → 3. samotné sloveso.)

## 2. K6 — koordinace se sdíleným podmětem (potvrzení provizorního rozhodnutí)

*„Ministr návrh podepsal a odeslal."* — jeden podmět, dvě určitá slovesa. Provizorně počítáme
**jeden pár** (vzdálenost k prvnímu slovesu). Anotátoři ale značí i další slovesa (jen jako
příznak), takže obě varianty půjdou přepočítat bez re-anotace. Souhlasíš s „jedním párem" pro
hlavní čísla?

## 3. K7 — věty beze slovesa s vyjádřeným podmětem

Vzácné případy (2 z 719 podmětových hran ve vzorku): podmět navěšený na jmenný predikát bez
jakékoli spony/pomocného slovesa (elipsa, typ *„Vstup zakázán"* bez „je"). Aktuálně je
**vylučujeme** (není k čemu měřit — žádný člen nesoucí shodu). Alternativa: měřit k samotnému
jmennému predikátu. Co preferuješ?

## 4. K8 — vztažné věty

Vedlejší věty vztažné dávají páry s podmětem-zájmenem: *„…metody, **které by** podstatným
způsobem ovlivnily…"* → pár *které* ↔ *by*, vzdálenost 0. Podle definice („všechny finitní
klauze s vyjádřeným podmětem") je zahrnujeme; vzdálenosti jsou tam typicky malé. Zahrnout
(aktuální stav), nebo vykazovat zvlášť? (Příznak v datech máme, obě varianty jsou spočitatelné.)

## 5. Anotace zlatého standardu

- **Rozsah: 260 vět** (200 náhodných z evaluačního vzorku + 60 cílených na vzácné jevy:
  spona, pro-drop, netypický slovosled, synkretismus, fragmenty, aby-věty).
- Formát: list s očíslovanými slovy, značíš všechny páry podmět↔přísudek indexy slov
  (0, 1 i více párů na větu; u koordinace navíc příznak dalších sloves — viz K6).
- **50 vět nezávisle anotuje i Tomáš** (měření shody; tvoje verze je rozhodující).
- Před začátkem dostaneš `ANNOTATION_GUIDELINES.md` (vznikne z tvých odpovědí na 1–4).
- Otázka: **stihneš to do ~2 týdnů?** Případně navrhni rozsah, který je realistický.

## 6. Potvrzení prahu (drobnost)

PONK limit 6 interpretujeme jako: **v pořádku ⇔ mezi podmětem a přísudkem je nejvýše 6 slov;
porušení ⇔ 7 a více slov** (tj. d > 6). Sedí to tak s PONKem?
