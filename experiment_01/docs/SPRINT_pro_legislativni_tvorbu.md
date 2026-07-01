# SPRINT jako nástroj pro legislativní tvorbu

**Podkladový (diskuzní) dokument**
Datum: 2026-06-09 · Autor podkladu: tým SPRINT · Status: **draft k diskuzi — žádná myšlenka není předem vyloučena**

> Poznámka k umístění: dokument je uložen ve složce `docs/2026-07-15_legislativni_rada/` (zadání zmiňovalo `2026-07-10`, ale reálná složka s podklady z Legislativní rady vlády nese datum `07-15`). Ve složce jsou dva podklady stažené z webu LRV:
> - **`LPV_projednana-verze_1.pdf`** — *Legislativní pravidla vlády* (úplné znění, 66 stran). Procesní i obsahové a hlavně **legislativně-technické** požadavky na tvorbu předpisů.
> - **`Metodicke_pokyny_UZ.pdf`** — *Metodické pokyny pro zajišťování prací při plnění legislativních závazků z členství ČR v EU* (37 stran). Gesce, **srovnávací tabulka** (EU ↔ ČR), analýza dopadů, hodnocení slučitelnosti.

---

## 0. Shrnutí na jednu stránku (TL;DR)

Chceme ze SPRINTu udělat **„IDE + linter + statickou analýzu pro tvorbu práva“**. Vyjdeme z toho, co SPRINT už dnes umí (pravidla psaná právníky, LLM hodnocení textu na úrovni věty / odstavce / sekce / dokumentu, testování pravidel přes F1, verzování pravidel) a doplníme tři vrstvy:

1. **Mikro (věta / odstavec) — „linter“.** Strojově kontrolovatelná legislativně-technická pravidla z LPV (citace, zkratky, terminologie, číslovky, „obdobně/přiměřeně“, jen normativní povaha textu…). **Tohle SPRINT umí už dnes** — stačí napsat pravidla. Rychlá, levná, nízkoriziková výhra.
2. **Makro (kapitola / dokument) — „architektonická pravidla“.** Struktura předpisu, jednota předmětu úpravy, úplnost důvodové zprávy a RIA, přítomnost a správnost přechodných / zrušovacích / účinnostních ustanovení.
3. **Systém (celý právní řád) — „RAG + grafová analýza“.** Konzistence napříč Sbírkou zákonů, detekce kolizí a duplicit, „find references“ k novelizovaným ustanovením, mrtvá zmocnění, dangling odkazy, soulad s ústavním pořádkem, judikaturou ÚS a právem EU (CELEX). Tady je největší přidaná hodnota i největší výzkumná náročnost.

**Cílová skupina:** kdokoli, kdo **vytváří** návrh (ministerský legislativec, poslanec, kraj, veřejnost) i kdo ho **hodnotí** (LRV, připomínkové místo, odborná i laická veřejnost). Stejný nástroj „spustím lokálně, než to pošlu dál“ — jako když si vývojář pustí CI na svém stroji před `git push`.

**Vůdčí metafora:** *Česká legislativa je velká codebase.* Chceme do ní bezpečně přidávat funkce (nové předpisy), odstraňovat a zjednodušovat staré části (mrtvý kód), a hlídat konzistenci a zdraví celku (statická analýza, linting, testy). Tahle metafora není jen rétorická — jak ukážeme níže, **LPV samy popisují novelizaci jako `diff`** (tučně = přidáno, přeškrtnuto = smazáno) a Metodické pokyny popisují **traceability matici** mezi EU a českým právem. Software-engineering nástroje na tyto úlohy existují desítky let.

---

## 1. Co SPRINT dnes je (výchozí stav)

Krátká rekapitulace, abychom stavěli na faktech (zdroje: `README.md`, `backend/db/models.py`, `backend/services/evaluator.py`, `backend/services/llm_client.py`, `frontend-react/src/types/index.ts`):

- **Editor + hodnoticí panel.** Dvoupanelové UI: vlevo rich-text editor (TinyMCE), vpravo výsledky hodnocení jako rozbalovací karty (porušení, odůvodnění, návrh opravy). Stack: FastAPI + PostgreSQL + React.
- **Pravidlo (`Rule`)** má `name`, `prompt_content` (JSON: `instructions`, `definition`, `conditions`, `teaching_examples` ve formátu „špatně → dobře“, `testset`) a **úroveň aplikace** `document_section_application ∈ {sentence, paragraph, section, document}`. Pravidla se přiřazují kategoriím dokumentů a lze je per-dokument zapnout/vypnout.
- **Hodnocení** je asynchronní, LLM-based, paralelní (jedna korutina na pravidlo, dávkování jednotek), s **diferenciálním cachováním** (nezměněné věty se znovu nehodnotí). Výstup na jednotku: `{has_violation, reason, suggestion}`. Vše se ukládá (kompletní auditní stopa: text jednotky, odeslaný prompt, výsledek, čas).
- **Vývoj pravidel řízený testy.** Pravidlo má testset; měří se precision / recall / F1 / konzistence. Pravidla jsou verzovaná (`rule_history`) — lze je porovnávat a vracet.
- **LLM provider** přepínatelný přes env (UFAL endpoint / OpenAI / OpenRouter). Default dnes **`anthropic/claude-sonnet-4.6`** přes OpenRouter (sleduje se i cena za request).
- **RAG / retrieval: zatím žádný.** Čistě LLM hodnocení bez vyhledávání v externím korpusu. (To je přesně vrstva 3, kterou chceme přidat.)

**Klíčový závěr:** architektura SPRINTu (pravidla jako data psaná právníky + testset + verze + úrovně granularity + auditní stopa) je pro legislativu **ideální základ**. Mikro-vrstvu lze spustit prakticky beze změny kódu — jen psaním pravidel.

---

## 2. Vůdčí metafora: právní řád jako codebase

Tahle tabulka je jádro dokumentu — z ní plyne, které nástroje SW vývoje se nabízí převzít.

| Software | Legislativa | Co z toho plyne pro nástroj |
|---|---|---|
| Repozitář / monorepo | Sbírka zákonů a mez. smluv / eSbírka | Jeden verzovaný „zdroj pravdy“, nad kterým běží analýzy |
| Soubor / modul | Zákon, nařízení, vyhláška | Jednotka vlastnictví (gestor), verzování, závislostí |
| Funkce / blok | §, odstavec, písmeno, bod | Přirozená jednotka pro chunking a hodnocení (lepší než „chunk po 500 znacích“) |
| Import / volání / dependency | Odkaz na jiný předpis / ustanovení (čl. 45 LPV) | **Graf závislostí** → „find references“, dopad novely |
| Deklarace typu / proměnné | Definice pojmu, legislativní zkratka (čl. 40, 44 LPV) | Kontrola konzistence použití, „nepoužitá deklarace“ |
| **Pull request / commit / `diff`** | **Novela** — LPV čl. 54 odst. 7: nově vkládané **tučně**, rušené **přeškrtnuté** | Novela *je* diff. Lze ji aplikovat (patch) → konsolidované znění |
| Commit message / PR popis | Důvodová zpráva (čl. 9 LPV) | Strukturovaná, kontrolovatelná na úplnost |
| Mazání kódu | Zrušovací ustanovení (čl. 52 LPV) | Explicitní, úplné; kontrola, že nezůstanou „dangling“ odkazy |
| Migrace / backward compat | Přechodná ustanovení (čl. 51 LPV) | Kontrola přítomnosti při zásahu do existujících vztahů |
| Release / deployment date / feature flag | Nabytí účinnosti (čl. 53 LPV) | Kontrola formátu, dostatečné legisvakance, žádná retroaktivita |
| Mrtvý kód | Obsoletní předpisy, zmocnění bez prováděcího předpisu, nikdy neúčinná ustanovení | **Dead-code analysis** nad celou Sbírkou |
| DRY / single source of truth | Zákaz recepce (čl. 46 LPV: „ustanovení se zpravidla nepřejímá, vhodnější je odkaz“) | Detekce duplicit / překryvů úprav |
| Linter / static analysis | Legislativně-technické požadavky (Hlavy III–VII LPV) | **Vrstva 1 — přímý kandidát na SPRINT pravidla** |
| Type checker / schema validace | Formální struktura (nadpisy, úvodní věty, číslování) | Strukturální pravidla na úrovni dokumentu |
| Architecture fitness functions | Jednota předmětu úpravy (čl. 39 odst. 4), zákaz „přílepků“ | **Vrstva 2 — pravidla na úrovni celého dokumentu** |
| Requirements traceability matrix | **Srovnávací / rozdílová tabulka EU ↔ ČR** (Metodické pokyny čl. 6a, příloha 5 LPV, CELEX) | Automatizovatelná traceability (viz §6.4) |
| CI/CD pipeline & gates | Připomínkové řízení → LRV → vláda → PSP | Hodnocení = lokální „pre-commit hook“ před vstupem do pipeline |
| Code review | Připomínkové řízení, posouzení LRV | Nástroj připraví reviewerovi „diff s anotacemi“ |
| Sémantické verzování | „ve znění pozdějších předpisů“, úplné znění (čl. 62, 64 LPV) | Point-in-time pohled na právo |
| Tech debt | Legislativní dluh, nekonzistence, fragmentace | Měřitelný a vizualizovatelný „dashboard zdraví“ |
| Refactoring | Rekodifikace | Nástroj jako asistent při velkém přepisu |

Dvě věci stojí za zdůraznění, protože z nich plyne, že **nejde o vynucenou analogii**:

- **Novela = `diff`.** LPV čl. 54 odst. 5 dokonce definují „větu“ pro své účely („ustanovení nečleněné na pododstavce/body, začínající velkým písmenem a končící tečkou“) a celá Hlava VI je v podstatě **specifikace patch formátu** (čl. 55–59: úvodní věta novely, body, vkládání/rušení/nahrazování slov a vět, přečíslování, poznámky pod čarou). Tohle je strojově zpracovatelné a aplikovatelné.
- **Odkazy = graf.** Čl. 45 (odkaz uvnitř / na jiný předpis), čl. 61–74 (druhy citací — úplná, zkrácená, slovní; citace §, odstavce, písmen, bodů, vět, čísel) tvoří **přesnou citační gramatiku**. Z ní lze deterministicky vytěžit citační graf (jako „go to definition“ a „find references“ v IDE).

---

## 3. Persony a uživatelské scénáře

| Persona | Co chce | Analogie SW |
|---|---|---|
| **Ministerský legislativec / autor návrhu** | Napsat technicky čistý návrh, projít LRV napoprvé | Vývojář, který si pouští linter před `push` |
| **Předkladatel věcného záměru** | Ověřit úplnost RIA, struktury, EU souladu | Autor RFC / design doc s checklistem |
| **Připomínkové místo / LRV** | Rychle vidět technické vady + diff s anotacemi | Reviewer s automaticky předvyplněnými poznámkami |
| **Poslanec / pozměňovací návrh** | Ověřit, že přílepek nemění nesouvisející věci, že nerozbije odkazy | Autor PR, který nechce breaking change |
| **Veřejnost / NNO / akademik** | Pochopit a posoudit návrh zveřejněný ve veřejné knihovně legislativního procesu | Open-source contributor, čte diff a CI report |
| **Správce právního řádu (gestor, MV/ÚV)** | Sledovat „zdraví“ celku, plánovat rekodifikace | Tech lead s dashboardem tech-debtu |

Dva základní toky:
- **Authoring (tvorba):** píšu návrh v editoru → po větě / při uložení běží mikro-linting → před odesláním spustím makro a systémovou kontrolu → vygeneruji podklady (srovnávací tabulka, checklist důvodové zprávy).
- **Review (hodnocení):** nahraju cizí návrh → dostanu anotovaný dokument s porušeními, odůvodněními a odkazy do právního řádu → exportuji jako připomínky.

---

## 4. Spolupráce s právníky: pravidla jako „kód“ (test-driven)

Zadání počítá s **právníky, kteří z existujících pravidel vytvoří SPRINT pravidla.** SPRINT pro to už má ideální workflow (`prompt_content` + `teaching_examples` + `testset` + F1 + verze). Navrhujeme to zformalizovat:

**Životní cyklus pravidla (obdoba vývoje funkce):**
1. **Specifikace** — právník vezme článek LPV / metodický pokyn a vytyčí, *co* pravidlo kontroluje a *na jaké úrovni* (věta / odstavec / sekce / dokument).
2. **Definice + instrukce** — napíše `definition`/`instructions` (co je porušení, co ne).
3. **Učící příklady** — `teaching_examples` ve formátu „špatně → dobře“ (few-shot). Ideálně z reálných stanovisek LRV.
4. **Testset** — sada vět s `expected_violation`. **Toto je „unit test“ pravidla.** Pravidlo se nesmí aktivovat, dokud nemá slušné F1.
5. **Review pravidla** — druhý právník pravidlo recenzuje (jako code review). Pravidlo má **vlastníka (gestora)** — přímá obdoba gesce z Metodických pokynů (čl. 3).
6. **Verze + aktivace** — `rule_history` drží historii; aktivuje se konkrétní verze. Při změně LPV se pravidlo „novelizuje“ (a re-testuje).

**Governance:** Katalog pravidel je sám codebase. Doporučujeme:
- **Závaznost pravidla**: `MUST` (legislativně-technická vada → blokující), `SHOULD` (doporučení), `INFO` (upozornění). Mapuje se na „zásadní připomínku“ vs. „doporučení“ v připomínkovém řízení (čl. 5 odst. 7 LPV).
- **Provenience**: každé pravidlo cituje konkrétní článek LPV / metodiky, ze kterého vychází (auditovatelnost, snadná aktualizace při novele LPV).
- **Sdílny pravidel** s LRV: pravidla nejsou „náš výklad“, ale formalizace praxe LRV — proto je vhodné je s LRV ladit a stvrzovat.

> **Riziko a jeho ošetření:** ne každé LPV-pravidlo je 1:1 strojově ověřitelné (mnohá vyžadují právní úsudek). Proto **každé porušení je návrh, ne verdikt** — s odůvodněním a citací zdroje, k odsouhlasení člověkem. Sbíráme zpětnou vazbu (accept/reject), která slouží jako signál pro ladění pravidel i jako metrika kvality.

---

## 5. Vrstva 1 — Mikro: legislativně-technický „linter“ (věta / odstavec)

**Nejrychlejší výhra. Běží na dnešním SPRINTu beze změny kódu.** Z LPV (zejm. Hlavy III–VII) plyne bohatý katalog strojově ověřitelných pravidel. Ukázkový **startovní katalog** (každé = jedno SPRINT pravidlo s testsetem):

**Citace (čl. 61–75) — vysoce mechanické, ideální pro LLM + i regex:**
- Úplná citace má tvar „Zákon č. 1/1991 Sb., o zaměstnanosti“ a za názvem navazujícím dalším textem následuje čárka (čl. 61).
- Při druhé a další citaci se použije zkrácená citace bez názvu (čl. 62).
- Citace § / odstavce: „§ 3 odst. 3“, „odst.“ jen ve spojení s § (jinak se „odstavec“ vypisuje) (čl. 71); „§§“ nelze (čl. 70 odst. 3).
- Citace vět slovně: „věta třetí“, „věta poslední“ — nikoli „podle předchozí věty/odstavce“ (čl. 57 odst. 2 návrhové části, čl. 73).
- Citace čísel bez teček a závorek, čárky jen mezi výčty (čl. 74).
- Správné zkratky úředních sbírek: „Sb.“, „Sb. m. s.“, „Úř. věst.“ (čl. 75).

**Terminologie a jazyk (čl. 39–44):**
- Předpis obsahuje **jen ustanovení normativní povahy** (čl. 39 odst. 1) — detekce proklamací, odůvodnění, „vaty“.
- Terminologická jednotnost v rámci předpisu (čl. 40 odst. 1) — stejný pojem = stejné slovo, žádná synonyma pro tutéž věc.
- Nový pojem se definuje; definice ≠ legislativní zkratka (čl. 40 odst. 2).
- Legislativní zkratka: zavedení „(dále jen „…“)“, alespoň jedno slovo, ne v nadpisu/poznámce/názvu, **důsledné používání po zavedení** (čl. 44).
- „obdobně“ vs. „přiměřeně“ — správné použití u odkazů (čl. 41).
- Číslovky a peněžní částky: „1 000 Kč“, „1 000 EUR“, číslovky určité arabsky, neurčité slovy, měsíc v datu slovem (čl. 43, 40 odst. 3).
- Oznamovací způsob přítomného času, jednotné číslo (čl. 40 odst. 5).
- Cizí slova jen výjimečně (čl. 40 odst. 4).

**Odkazy a poznámky (čl. 45–47):**
- Vnitřní odkaz „odstavec 3“ / „§ 3 odst. 3“ podle kontextu (čl. 45 odst. 1).
- Poznámka pod čarou nemá normativní povahu → detekce normativního obsahu v poznámce (čl. 47 odst. 1) — *klasický „code smell“*.
- Recepce: nepřejímat cizí ustanovení, raději odkaz (čl. 46) — **DRY linter**.

**Nadpisy a úvodní věty (čl. 30–38):**
- Na konci nadpisu se nepíše tečka (čl. 30 odst. 9).
- Předepsané tvary nadpisů zákona / nařízení / vyhlášky (čl. 31–33) a úvodních vět (čl. 36–38).
- § by zpravidla neměl mít více než 6 odstavců (čl. 39 odst. 2) — měřitelné.

**Účinnost a varianty:**
- Účinnost zpravidla k 1. 1. nebo 1. 7.; zákaz retroaktivity; předepsané formulace (čl. 53).
- Varianty se značí „V A R I A N T A …“, min. 2, stejně členěné (čl. 42 odst. 3).

> Tyto věci dnes právníci LRV hledají očima. Mikro-linter je najde za vteřiny, konzistentně, s odkazem na článek LPV a návrhem opravy. **Část z nich (citace, zkratky, číslovky) je dokonce čistě regexová** — doporučujeme **hybridní pravidla**: deterministický check (rychlý, 100% jistý) + LLM tam, kde je potřeba úsudek. (To je drobné rozšíření SPRINTu: typ pravidla „deterministické“.)

---

## 6. Vrstva 2 a 3 — Makro a Systém

### 6.1 Makro (kapitola / dokument) — „architektonická pravidla“

Běží na úrovni `section` / `document`, kontext = celý návrh (případně i důvodová zpráva). Příklady:

- **Jednota předmětu úpravy** (čl. 39 odst. 4: nelze upravovat různorodé věci, jež spolu nesouvisejí) → **detekce „přílepků“**. Toto je *architecture fitness function*.
- **Struktura a členění** (čl. 25–30, 39 odst. 3): rozsáhlý předpis členěn na části/hlavy/díly; nadpisy vystihují obsah; ucelené úseky.
- **Úplnost důvodové zprávy** (čl. 9 odst. 2 — body a) až q)): zhodnocení ústavnosti, EU souladu, dopadů na rozpočet, korupčních rizik, soukromí/osobních údajů, dopadů na rodinu, digitálního vyloučení atd. → **checklist coverage** (jako „test coverage“ — žádný povinný oddíl nesmí chybět).
- **RIA / hodnocení dopadů** (čl. 4, obecné zásady): přítomnost a vnitřní konzistence závěrů.
- **Přechodná / zrušovací / účinnostní ustanovení**: přítomna tam, kde mají být; zrušovací ustanovení **úplné** (vyjmenovává všechny rušené předpisy — čl. 52).
- **Soulad důvodové zprávy s textem**: zvláštní část DZ se člení po §; neopakuje text ustanovení (čl. 12 odst. 4).

### 6.2 Systém (celý právní řád) — proč nestačí „obyčejné RAG“

Zadání správně označuje systémovou vrstvu za **velmi důležitou** a předpokládá „nějaký RAG systém“. Klíčový poznatek: **legislativa není volný text** — má strukturu (§/odst./písm./bod) a **explicitní odkazy**. Proto navrhujeme **hybrid: znalostní graf + vektorové vyhledávání**, ne jen embeddings.

- **Grafová (deterministická) část — „kompilátor/LSP“:**
  Z citační gramatiky (čl. 45, 61–74) postavíme **citační graf** celého právního řádu (uzly = předpisy a jejich ustanovení; hrany = odkazy, zmocnění, novely, derogace). Z něj zadarmo plyne:
  - **„Go to definition“ / „find references“**: kde je § definován, kdo na něj odkazuje.
  - **Dopad novely („blast radius“)**: změním-li ustanovení, graf ukáže všechna ustanovení a předpisy, která ho citují → seznam toho, co je třeba prověřit / novelizovat. (Přesně to vyžaduje čl. 10 odst. 3 LPV — při zrušení zákona dořešit prováděcí předpisy.)
  - **Dangling odkazy**: citace na zrušené/neexistující ustanovení = „broken link“ / *null pointer*.
  - **Mrtvý kód**: zmocnění bez prováděcího předpisu; nikdy neúčinná ustanovení; předpisy, na něž nikdo neodkazuje a jsou fakticky obsoletní.

- **Vektorová (sémantická) část — „podobnost bez explicitního odkazu“:**
  Embeddings nad korpusem (chunkováno **po přirozených jednotkách** — §/odstavec, ne arbitrárně!) + hybridní vyhledávání (BM25 + dense). Slouží k:
  - **Detekci duplicit / překryvů úprav** (DRY na úrovni celého řádu) — dvě ustanovení upravující totéž jinak.
  - **Terminologické konzistenci napříč souvisejícími předpisy** (čl. 40 odst. 1 to **výslovně vyžaduje** — soulad s terminologií v navazujících předpisech). Bez retrievalu to LLM neumí — musí vidět, jak je pojem definován jinde.
  - **Vyhledání kolidujících ustanovení** (lex specialis/posterior/superior) při zavádění nové úpravy.
  - **Retrieval relevantní judikatury ÚS** a nálezů (čl. 4 odst. 3, čl. 9 odst. 2 písm. d) — soulad s ústavním pořádkem a judikaturou).

### 6.3 Architektura systémové vrstvy (návrh)

```
            ┌─────────────────────────────────────────────┐
            │  Korpus: eSbírka (XML/strukturovaná data),    │
            │  Sbírka zákonů, EUR-Lex/CELEX, nálezy ÚS      │
            └───────────────┬───────────────┬───────────────┘
                            │ ingest        │ ingest
                ┌───────────▼──────┐  ┌─────▼───────────────┐
                │ Parser struktury │  │ Embedding pipeline   │
                │ §/odst./odkazy   │  │ (chunk po ustanovení)│
                └───────┬──────────┘  └─────────┬───────────┘
                        │                        │
              ┌─────────▼─────────┐    ┌─────────▼─────────┐
              │ Citační/derogační │    │ Vektorový index    │
              │ GRAF (knowledge   │    │ (hybrid BM25+dense)│
              │ graph)            │    │ + point-in-time    │
              └─────────┬─────────┘    └─────────┬─────────┘
                        └───────────┬────────────┘
                            ┌───────▼────────┐
                            │ Retrieval/Graph │  ← rozšíření SPRINT evaluatoru:
                            │ context provider│    pravidlo si vyžádá kontext
                            └───────┬────────┘
                                    │ (citace zdrojů!)
                            ┌───────▼────────┐
                            │ LLM hodnocení   │  → reason + suggestion + ZDROJE
                            └────────────────┘
```

**Důležité vlastnosti:**
- **Point-in-time / verzování práva (= git).** Každý předpis má historii; novela = commit; „ve znění k datu“ = checkout. Hodnotíme vždy proti **platnému znění k relevantnímu datu** (jinak halucinace o neaktuálním právu).
- **Citace zdrojů povinně.** Každé systémové porušení musí nést odkaz na konkrétní ustanovení/nález, ze kterého plyne. SPRINT už ukládá `reason` + odeslaný prompt → rozšíříme o `sources`. **Bez citace zdroje není závěr přípustný** (auditovatelnost, důvěra právníků).
- **Datové zdroje:** ideálně oficiální eSbírka ve strukturované podobě (odkazy a struktura „zdarma“). EU právo přes EUR-Lex (CELEX identifikátory — viz §6.4).

### 6.4 Automatizace EU traceability (Metodické pokyny → kód)

Metodické pokyny (čl. 6a) a příloha č. 5 LPV vyžadují **srovnávací / rozdílovou tabulku**: vlevo ustanovení předpisu EU (CELEX), vpravo implementující ustanovení ČR. **To je requirements-traceability matrix.** Nabízí se:
- **Asistované zarovnání (alignment)**: pro každé ustanovení směrnice najít kandidátní implementující ustanovení návrhu (sémantické vyhledávání) → předvyplnit tabulku → právník potvrdí/opraví.
- **Kontrola pokrytí transpozice**: které články směrnice nejsou pokryty žádným ustanovením návrhu (gap) — „transpozice coverage“.
- **Referenční povinnost** (Metodické pokyny čl. 2 odst. 2 písm. e): kontrola, že transponující předpis na směrnici odkazuje.
- **Generování přílohy** ve formátu přílohy 5 LPV (CELEX, název v českém znění dle Úř. věst.).

Tohle je konkrétní, ohraničená a velmi žádaná funkce — kandidát na samostatný modul s rychlou návratností.

---

## 7. Vlajkové „killer“ funkce (kreativní, k diskuzi — nic není vyloučeno)

1. **Legislativní LSP.** Hover nad „§ 5 odst. 2“ → definice, výskyty (find references), EU původ (CELEX), relevantní judikatura. „Go to definition“ pro odkazy přímo v editoru.
2. **Blast-radius novely.** Označím změnu → graf vykreslí všechna dotčená ustanovení a předpisy + odhad „co se rozbije“ (dangling odkazy, ztracená zmocnění). Reviewer vidí dopad na první pohled.
3. **Konsolidace na jedno kliknutí.** Aplikace novely-`diffu` (Hlava VI LPV) na platné znění → úplné znění (patch apply / merge). Zároveň validace, že diff je formálně korektní podle čl. 55–59.
4. **Linter celého právního řádu — „dashboard zdraví“.** Dávkové spuštění pravidel nad celou Sbírkou → mapa „code smells“: mrtvá zmocnění, dangling odkazy, terminologické nekonzistence, duplicity, předpisy bez prováděcích předpisů. **Měřitelný legislativní tech-debt.** Podklad pro plán rekodifikací a „úklidových“ novel.
5. **Detekce přílepků (rider amendments).** Pozměňovací návrh / novela mění věci nesouvisející s předmětem (ÚS opakovaně rušil) → pravidlo na úrovni celé novely + RAG na předmět dotčených předpisů.
6. **Skóre srozumitelnosti / „cognitive complexity“ ustanovení.** Délka vět, hloubka vnořených odkazů (≈ cyklomatická složitost), počet odstavců v §, počet křížových odkazů potřebných k pochopení. „Plain-language“ metrika napříč návrhem (čl. 2 odst. 2 písm. d) LPV: srozumitelně, jednoznačně).
7. **„Co kdyby“ simulace (property-based testing pro zákony).** Agent „spustí“ návrh na hypotetických případech a hledá mezery, kolize, absurdní výsledky. Velmi experimentální, ale koncepčně mocné — *unit testy pro normu*.
8. **Multi-agent review panel.** Samostatné „lensy“ odpovídající bodům RIA (ústavnost, EU, korupční rizika, ochrana osobních údajů, dopady na rodinu, digitální vyloučení — čl. 4/9 LPV) jako nezávislí hodnotitelé; jejich nálezy se slučují a křížově ověřují.
9. **Návrh „úklidu“.** Nástroj sám navrhne kandidáty na zrušení (mrtvý kód) a konsolidaci duplicit — s vygenerovaným zrušovacím ustanovením (čl. 52).

---

## 8. Návrh fázování (roadmap)

| Fáze | Obsah | Náročnost | Závislost na nové infrastruktuře |
|---|---|---|---|
| **F0 — Příprava** | Sběr reálných stanovisek LRV, definice škály závaznosti, dohoda s právníky na gesci pravidel | nízká | žádná |
| **F1 — Mikro linter** | Katalog legislativně-technických pravidel (§5) + hybridní (regex+LLM) pravidla; čeština-aware už hotová | **nízká** | **běží na dnešním SPRINTu** |
| **F2 — Makro** | Pravidla na úrovni sekce/dokumentu; checklist DZ a RIA; struktura | střední | drobné rozšíření (kontext = celý dokument je už podporován) |
| **F3 — EU traceability** | Asistovaná srovnávací tabulka, CELEX alignment, coverage transpozice | střední–vysoká | EUR-Lex ingest + vektorové vyhledávání |
| **F4 — Systémový RAG + graf** | Citační graf, find references, dangling/dead-code, terminologie napříč řádem, judikatura | **vysoká** | eSbírka ingest, graf, vektorový index, point-in-time |
| **F5 — Vlajkové funkce** | Blast radius, konsolidace, dashboard zdraví, simulace | vysoká | nad F4 |

Logika: **F1 dodá hodnotu během týdnů a získá důvěru právníků; F4/F5 jsou výzkumně nejnáročnější, ale s největším dopadem.** Doporučujeme nepouštět se do RAG, dokud neběží mikro-linter a nemáme zpětnou vazbu.

---

## 9. Rizika, omezení a etika

- **LLM halucinace u právní správnosti.** Mitigace: porušení = návrh, ne verdikt; člověk v kličce; povinné citace zdrojů; deterministické checky tam, kde to jde; měření F1.
- **Aktuálnost a správnost korpusu.** Bez point-in-time pohledu hrozí rady k neaktuálnímu právu. Nutný spolehlivý, verzovaný zdroj (eSbírka).
- **Právní odpovědnost a status nástroje.** Nástroj **nenahrazuje** LRV ani právní posouzení; je to asistent / „spell-checker“. Jasně komunikovat.
- **Ochrana citlivých návrhů.** Neveřejné návrhy (před vložením do veřejné knihovny) nesmí unikat do externích LLM bez ošetření. → možnost běhu na **lokálním/UFAL modelu** (SPRINT to už umí přepnout přes provider).
- **Auditovatelnost.** SPRINT už ukládá kompletní stopu (text, prompt, výsledek, čas). Rozšířit o zdroje a verzi pravidla → reprodukovatelnost každého závěru.
- **Důvěra a adopce.** Pravidla musí být formalizací praxe LRV (ne „náš názor“) — proto je s LRV ladit a stvrzovat; transparentně ukazovat, ze kterého článku LPV pravidlo plyne.
- **Měření kvality.** F1 na testsetech + sběr accept/reject od uživatelů jako kontinuální metrika a tréninkový signál.

---

## 10. Otevřené otázky k diskuzi

1. **Zdroj korpusu:** je dostupná eSbírka ve strukturované (XML) podobě s odkazy? Jaké jsou licenční a technické podmínky ingestu?
2. **Rozsah pilotu:** začít na jednom typu předpisu (např. vyhlášky / novely) a jedné agendě?
3. **Vztah k LRV:** chceme pravidla stvrzená LRV jako „oficiální“, nebo nástroj poběží jako nezávislý asistent?
4. **Hosting modelu:** lokální/UFAL model kvůli důvěrnosti vs. silnější komerční modely (Sonnet 4.6) přes bránu?
5. **Deterministické vs. LLM pravidla:** chceme zavést typ „deterministické pravidlo“ (regex/parser) jako rozšíření datového modelu?
6. **EU traceability jako samostatný produkt?** Srovnávací tabulka má jasnou návratnost a ohraničení — možná první „vlajková“ funkce.
7. **Verzování práva:** jak hluboko potřebujeme point-in-time (jen aktuální znění vs. plná historie)?

---

### Příloha A — Mapování LPV → kandidátní SPRINT pravidla (výběr)

| Článek LPV | Téma | Úroveň | Typ | Závaznost |
|---|---|---|---|---|
| čl. 30 odst. 9 | Bez tečky na konci nadpisu | sentence | regex | MUST |
| čl. 40 odst. 1 | Terminologická jednotnost (v rámci předpisu) | document | LLM | MUST |
| čl. 40 odst. 1 | Terminologie napříč souvisejícími předpisy | document | LLM+RAG | SHOULD |
| čl. 41 | „obdobně“ vs. „přiměřeně“ | sentence | LLM | SHOULD |
| čl. 43 / 74 | Číslovky, částky, citace čísel | sentence | regex+LLM | MUST |
| čl. 44 | Legislativní zkratka (zavedení + důsledné užití) | document | LLM | MUST |
| čl. 39 odst. 1 | Jen normativní povaha | paragraph | LLM | MUST |
| čl. 39 odst. 2 | ≤ 6 odstavců v § | section | deterministic | SHOULD |
| čl. 39 odst. 4 | Jednota předmětu úpravy (přílepky) | document | LLM+RAG | MUST |
| čl. 45 / 61–74 | Citační gramatika | sentence | regex+LLM | MUST |
| čl. 47 odst. 1 | Normativní obsah v poznámce pod čarou | paragraph | LLM | MUST |
| čl. 46 | Recepce / duplicita (DRY) | document | LLM+RAG | SHOULD |
| čl. 51 | Přítomnost přechodných ustanovení | document | LLM | SHOULD |
| čl. 52 | Úplnost zrušovacího ustanovení | document | LLM+graf | MUST |
| čl. 53 | Účinnost (formát, legisvakance, retroaktivita) | document | LLM | MUST |
| čl. 9 odst. 2 a)–q) | Úplnost důvodové zprávy | document | LLM | MUST |
| Metod. pokyny čl. 6a | Srovnávací tabulka / coverage transpozice | document | RAG+alignment | MUST |

*(Plný katalog vznikne ve fázi F0–F1 spolu s právníky a testsety.)*
