# Otázky pro Katku — experiment_04 (2026-07-20; doplněno 2026-07-21 před hovorem)

> **Aktuální stav (21. 7.):** abychom neblokovali běh, otázky 2–4 jsme provizorně zodpověděli
> sami (`PROVISIONAL_ANSWERS_K6-K9.md`) a experiment běžel s nimi — pro hovor tedy stačí
> **potvrdit/vetovat** (dopad má hlavně veto K6). A jedna novinka k tvé hypotéze: měla jsi
> pravdu — když jsme definice přepsali do elementárních testů a uzavřených seznamů tvarů
> („být", aby/kdyby), identifikace párů u 72B modelu stoupla z 50 % na 71 %. Zbývající chyby
> jsou v PÁROVÁNÍ — a k tomu míří dvě nové otázky níže (7 a 8).

## 7. NOVÉ — vztažné zájmeno: podmět × předmět (příčina chyb modelu)

Napsali jsme modelu pravidlo „vztažná zájmena jsou podměty svých vedlejších vět" — a přestřelili:
model teď páruje i vztažná zájmena v předmětové pozici. Příklad z dat:
*„…informace…, **které** musí obsahovat výroční **zpráva**…"* — model: pár które↔musí (špatně);
správně: zpráva↔musí (podmět za přísudkem, „které" je předmět).
**Jaký elementární test doporučíš pro rozlišení?** (Naše ideje: shoda v čísle/rodě s přísudkem;
zkusit dosadit „kdo/co" vs. „koho/co"; kontrola, zda ve vedlejší větě není jiné jméno
v nominativu ve shodě. Co z toho je pro laika/model nejspolehlivější?)

## 8. NOVÉ — slova typu „Jsou-li", „není-li"

U vět jako *„**Jsou-li** obsahem výroční zprávy i informace…"* měříme k „jsou" — na úrovni slov
je to slovo „Jsou-li". Souhlasíš, že měřený přísudek je (celé) slovo „Jsou-li"? (Analogie
s aby/kdyby; technicky opravujeme, aby se vykazovalo celé slovo.)

Kontext: metodika je zamrazená (experiment_04/METHODOLOGY.md), tvoje definice přísudku z minulé
revize je zapracovaná a mechanicky aplikovaná na CLTT (ručně anotované stromy — tvůj a Bářin
treebank). Zlatý standard **odvozujeme z CLTT** — díky tomu NENÍ potřeba anotovat nové věty;
místo anotace tě prosíme o **kontrolu** (bod 5). Odhad času: ~45–60 min na body 1–4 a 6,
kontrola (bod 5) ~1–2 h.

## 1. Kontrola pracovních příkladů (nejdůležitější, blokuje zbytek)

V `docs/WORKED_EXAMPLES_katka.md` je ~24 příkladů z CLTT — pro každý typ konstrukce věta
s očíslovanými slovy, vyznačený pár podmět↔přísudek (★) a spočítaná vzdálenost. Věta může
obsahovat i další páry (vypsané pod ★ řádkem) — kontroluješ jen ten ★. Prosím u každého ✓ nebo
oprava.

Zvláštní pozornost dvěma nově doplněným typům (odhalila je kontrola dat):
- **minulé pasivum:** *„Dne 11. 7. 2013 **byla** provedena kontrola…"* — měříme k **byla**
  (pomocné sloveso; nese shodu v rodě a čísle). Souhlasíš?
- **minulá spona:** *„Spolupráce rodiny s centrem **byla** však krátkodobá…"* — měříme k
  **byla** (spona). Souhlasíš?

(Technické pozadí: v UD nejsou minulé tvary „být" značené jako finitní — jsou to l-příčestí.
Pravidlo: 1. finitní aux/spona → 2. příčesťové aux/spona → 3. samotné sloveso.)

## 2. K6 — koordinace se sdíleným podmětem (potvrzení provizorního rozhodnutí)

*„Ministr návrh podepsal a odeslal."* — jeden podmět, dvě určitá slovesa. Provizorně počítáme
**jeden pár** (vzdálenost k prvnímu slovesu); další slovesa evidujeme jako příznak, takže obě
varianty půjdou přepočítat. Souhlasíš s „jedním párem" pro hlavní čísla?

## 3. K7 — věty beze slovesa s vyjádřeným podmětem

Vzácné případy: podmět navěšený na jmenný predikát bez jakékoli spony/pomocného slovesa
(elipsa, typ *„Vstup zakázán"* bez „je"). Aktuálně je **vylučujeme** (není k čemu měřit — žádný
člen nesoucí shodu). Alternativa: měřit k samotnému jmennému predikátu. Co preferuješ?

## 4. K8 — vztažné věty (v CLTT nezanedbatelné: 17,5 % párů)

Vedlejší věty vztažné dávají páry s podmětem-zájmenem: *„…metody, **které by** podstatným
způsobem ovlivnily…"* → pár *které* ↔ *by*, vzdálenost 0. Podle definice („všechny finitní
klauze s vyjádřeným podmětem") je zahrnujeme; vzdálenosti jsou typicky 0–1. V CLTT je to 277
párů z 1 586. Zahrnout do hlavních čísel (aktuální stav), nebo vykazovat zvlášť? (Příznak
v datech máme, obě varianty jsou spočitatelné.)

## 5. Kontrola odvozeného zlatého standardu (~100 párů, místo anotace)

Zlatý standard = naše pravidlo aplikované na CLTT stromy (1 586 párů). Aby mělo měření oporu,
prosíme o kontrolu vzorku: **všechny páry vzácných konstrukcí** (kondicionál 9, aby/kdyby 9,
minulá spona 3) **+ ~80 náhodných** z běžných typů. Formát stejný jako pracovní příklady
(věta s okny, pár, vzdálenost, ✓/oprava) — list ti vygenerujeme po odsouhlasení bodů 1–4.
Výstupem je změřená chybovost odvozeného goldu do článku (a případné opravy pravidla).

## 6. Potvrzení prahu (drobnost)

PONK limit 6 interpretujeme jako: **v pořádku ⇔ mezi podmětem a přísudkem je nejvýše 6 slov;
porušení ⇔ 7 a více slov** (tj. d > 6). Věta je označena, pokud práh překročí **kterýkoli** její
pár. Sedí to tak s PONKem?
