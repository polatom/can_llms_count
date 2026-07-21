# Katka — K10: vztažné zájmeno podmět × předmět (odpověď 2026-07-21, verbatim)

Kontext: otázka 7 z QUESTIONS_katka_2026-07-20.md (chyby párování u vztažných zájmen).
Algoritmus níže je implementován v R4 (`src/prompts/r4_procedural_pairing.txt`).

---

Vztažná zájmena:

Postup: U každého slova ve vedlejší vztažné větě (tj. vedlejší věta uvozená vztažným zájmenem
nebo předložkou a vztažným zájmenem - např. Kamarádi, o kterých jsem mluvila) otestuj jeho pád.
Pokud vztažné zájmeno může být nominativ (v praxi by se to snad mělo týkat jen tvarů "které",
"která", "již" a "jež", pokud jsem něco neopominula), testuj dál. Pokud ve vedlejší větě
nenajdeš žádný jiný nominativ, pak je vztažné zájmeno nominativ a tudíž podmět. Pokud ve
vedlejší větě najdeš alespoň jeden další nominativ, pak je tento nominativ podmětem a vztažné
zájmeno podmět není (a není ani nominativ, typicky se bude jednat o akuzativ = 4. pád). Proč?
Protože věta má pouze jeden podmět (respektive může to být několikanásobný podmět v koordinaci,
ale vztažné zájmeno nikdy v koordinaci s jiným podmětem v téže clause nebude).

Příklad 1: "Poznamenala jsem si informace, které musí obsahovat zpráva." -> "které" může být
morfologicky nominativ. Hledám dál. "Musí" není nominativ, "obsahovat" není nominativ, "zpráva"
může být nominativ. Aha, "zpráva" je podmět.

Příklad 2: "Poznamenala jsem si informace, které byly vyvěšeny na nástěnce." -> "které" může
být morfologicky nominativ. Hledám dál. "Byly" není nominativ, "vyvěšeny" není nominativ, "na"
není nominativ, "nástěnce" není nominativ. Žádný další nominativ jsem nenašla, takže podmětem
bude "které".

Příklad 3: "Četla jsem o městech, která navštívily Lucka a Petra." -> "která" může být
morfologicky nominativ. Hledám dál. "Navštívily" nominativ není, "Lucka" nominativ je. Takže
"Lucka" bude podmět. Jelikož jsem našla jiný nominativ, můžu se zastavit, protože jsem jasně
určila, že "která" podmět není. Reálně se však jedná o mnohonásobný podmět "Lucka" a "Petra".

Příklad 4: "Četla jsem o městech, která stojí na pobřeží." -> Tohle je problém. "Která" i
"pobřeží" může být morfologicky podmět. Desambiguace celé vedlejší věty je jednoduchá, protože
před "pobřeží" je předložka "na" a nominativ nikdy předložku nemá. Je tedy na zvážení přidat
nějaké univerzální pravidlo, že pokud před podstatným jménem stojí předložka, automaticky to
není nominativ. Problém by pak mohlo být něco jako "Četla jsem o městech, která stojí na jižním
pobřeží Francie." - jednak je mezi "na" a "pobřeží" ještě vložené adjektivum, takže předložka
není těsně před podstatným jménem, a jednak se objevuje další větný člen "Francie" v genitivu,
který ale morfologicky může být nominativ. Tohle je případ, kdy by moje poučka s hledáním
dalšího nominativu selhala. Řešením je asi jedině buď sémantika nebo detailní větný rozbor, kde
by se ukázalo, že "Francie" je závislá na "pobřeží", což by podmět nikdy nebyl.

---

## Destilace pro R4 (naše implementace)

1. Tvary vztažných zájmen, které NIKDY nejsou nominativ (kterou, kterého, kterému, kterých,
   kterým, kterými, níž, nichž, němuž, jehož, jejíž…) → nikdy podmět.
2. Tvary, které nominativ být MOHOU (který, která, které, kteří, jenž, jež, již) → eliminační
   test: projdi ostatní slova téže vedlejší věty; najdeš-li jiný možný nominativ (bez
   předložky!), je podmětem ON a zájmeno ne; nenajdeš-li žádný, podmětem je zájmeno.
3. Univerzální pomůcka: jméno po předložce (i s vloženými přídavnými jmény) není nominativ.
4. Známé selhání (Katka, příklad 4b): morfologicky nominativní genitivy („…pobřeží Francie")
   eliminační test zmatou; plné řešení = syntax/sémantika. Přijatelné reziduum.
