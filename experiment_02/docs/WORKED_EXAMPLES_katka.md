# Worked examples for Katka — §3 extraction rule on CLTT gold trees

Purpose (METHODOLOGY §4.2): confirm that the mechanical rule (predicate = finite element
of the predicate complex; subject = nsubj head word) matches your definition, per
construction type. All examples below come from human-annotated `cs_cltt` trees, so any
error is in OUR rule, not in a parser. For each: numbered words, the extracted pair,
the distance (words strictly between). **Please mark each ✓ or correct it.**

Derivation over the whole treebank: 1121 sentences → 1586 pairs. Distribution: finite verb / l-participle: 1147, copular — finite copula (je): 350, passive — finite aux (je/bude vydána): 33, passive — past aux (byla vydána): 31, conditional (by): 9, aby/kdyby (absorbed by): 9, analytic — aux (jsem/bude …): 4, copular — past copula (byla): 3

## finite verb / l-participle  (1147 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-test.conllu::299`
  - 1:Ministerstvo 2:vede 3:registr 4:vydaných 5:standardů.
  - pair: **Ministerstvo** (word 1) ↔ **vede** (word 2) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-dev.conllu::40`
  - 1:(4) 2:Rezervy 3:nesmějí 4:mít 5:aktivní 6:zůstatek.
  - pair: **Rezervy** (word 2) ↔ **nesmějí** (word 3) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::146`
  - 1:Stanovená 2:doba 3:nesmí 4:přesáhnout 5:účetní 6:období.
  - pair: **doba** (word 2) ↔ **nesmí** (word 3) → distance **0**
  - [ ] ✓ / correction: 

## copular — finite copula (je)  (350 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::260`
  - 1:Porušením 2:vzájemného 3:zúčtování 4:nejsou 5:případy 6:upravené 7:účetními 8:metodami.
  - pair: **případy** (word 5) ↔ **nejsou** (word 4) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::257`
  - 1:Stanovení 2:těchto 3:povinností 4:na 5:smluvním 6:základě 7:není 8:dotčeno.
  - pair: **Stanovení** (word 1) ↔ **není** (word 7) → distance **5**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::43`
  - 1:Informace 2:je 3:srovnatelná, 4:jestliže 5:splňuje 6:požadavky 7:stanovené 8:v 9:§_7_odst._3_až_5.
  - pair: **Informace** (word 1) ↔ **je** (word 2) → distance **0**
  - [ ] ✓ / correction: 

## copular — past copula (byla)  (3 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-test.conllu::2`
  - 1:Nástupnická 2:účetní 3:jednotka, 4:která 5:nebyla 6:zúčastněnou 7:účetní 8:jednotkou, 9:otevírá 10:účetní 11:knihy 12:ke 13:dni 14:zápisu 15:přeměny 16:společnosti 17:do 18:obchodního 19:rejstříku 20:s 21:účinky 22:od 23:rozhodného 24:dne 25:v 26:souladu 27:s 28:metodou 29:přeměny 30:společnosti.
  - pair: **která** (word 4) ↔ **nebyla** (word 5) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::449`
  - 1:(1) 2:Při 3:přeměně 4:společnosti, 5:kdy 6:se 7:rozhodný 8:den 9:neshoduje 10:se 11:dnem 12:zápisu 13:přeměny 14:společnosti 15:do 16:obchodního 17:rejstříku, 18:zúčastněná 19:společnost, 20:která 21:je 22:účetní 23:jednotkou 24:(dále 25:jen 26:„zúčastněná 27:účetní 28:jednotka“), 29:přejímající 30:společník, 31:který 32:je 33:účetní 34:jednotkou, 35:nástupnická 36:účetní 37:jednotka, 38:která 39:nebyla 40:zúčastněnou 41:účetní 42:jednotkou, 43:nebo 44:účetní 45:jednotka 46:uvedená 47:v 48:§_17_odst._5_zákona 49:upraví, 50:za 51:účelem 52:dosažení 53:cíle 54:stanoveného 55:v 56:§_10_zákona 57:o 58:přeměnách, 59:ke 60:dni 61:zápisu 62:přeměny 63:společnosti 64:do 65:obchodního 66:rejstříku 67:účetnictví 68:s 69:účinky 70:od 71:rozhodného 72:dne.
  - pair: **která** (word 38) ↔ **nebyla** (word 39) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-dev.conllu::143`
  - 1:(2) 2:Konsolidující 3:účetní 4:jednotka 5:dále 6:v 7:příloze 8:uvede 9:zejména 10:a) 11:výši 12:odměn 13:vyplacených 14:za 15:účetní 16:období 17:jak 18:v 19:peněžní, 20:tak 21:i 22:v 23:nepeněžní 24:formě 25:osobám, 26:které 27:jsou 28:statutárním 29:orgánem, 30:členům 31:statutárních 32:nebo 33:jiných 34:řídících 35:a 36:dozorčích 37:orgánů, 38:jakož 39:i 40:výši 41:vzniklých 42:nebo 43:sjednaných 44:penzijních 45:závazků 46:k 47:bývalým 48:členům 49:vyjmenovaných 50:orgánů, 51:s 52:uvedením 53:úhrnu 54:za 55:každou 56:kategorii, 57:b) 58:výši 59:záloh, 60:půjček 61:a 62:úvěrů 63:poskytnutých 64:osobám, 65:které 66:jsou 67:statutárním 68:orgánem, 69:členům 70:statutárních 71:nebo 72:jiných 73:řídících 74:a 75:dozorčích 76:orgánů 77:s 78:uvedením 79:úrokové 80:sazby, 81:hlavních 82:podmínek 83:a 84:jakýchkoliv 85:splatných 86:částek, 87:výši 88:všech 89:forem 90:zajištění, 91:s 92:uvedením 93:úhrnu 94:za 95:každou 96:kategorii, 97:c) 98:celkovou 99:částku 100:závazků, 101:které 102:ke 103:dni 104:sestavení 105:konsolidované 106:účetní 107:závěrky 108:mají 109:dobu 110:splatnosti 111:delší 112:než 113:pět 114:let 115:a 116:celkovou 117:částku 118:zajištěných 119:závazků 120:s 121:uvedením 122:povahy 123:a 124:formy 125:tohoto 126:zajištění, 127:d) 128:způsob 129:stanovení 130:reálné 131:hodnoty 132:příslušného 133:majetku 134:a 135:závazků, 136:popis 137:použitého 138:oceňovacího 139:modelu 140:při 141:ocenění 142:cenných 143:papírů 144:a 145:derivátů 146:reálnou 147:hodnotou, 148:změny 149:reálné 150:hodnoty, 151:včetně 152:změn 153:v 154:ocenění 155:podílu 156:ekvivalencí 157:podle 158:jednotlivých 159:druhů 160:finančního 161:majetku 162:a 163:způsob 164:jejich 165:zaúčtování; 166:pokud 167:nebyl 168:cenný 169:papír, 170:podíl 171:a 172:derivát 173:oceněn 174:reálnou 175:hodnotou 176:nebo 177:ekvivalencí, 178:uvede 179:účetní 180:jednotka 181:důvody 182:a 183:případnou 184:výši 185:opravné 186:položky, 187:e) 188:souhrnnou 189:výši 190:finančních 191:závazků, 192:které 193:nejsou 194:uvedeny 195:v 196:konsolidované 197:rozvaze, 198:jsou-li 199:tyto 200:informace 201:užitečné 202:pro 203:posouzení 204:finanční 205:situace; 206:samostatně 207:se 208:uvedou 209:veškeré 210:závazky 211:související 212:s 213:důchody 214:a 215:závazky 216:mezi 217:konsolidující 218:účetní 219:jednotkou 220:a 221:účetními 222:jednotkami 223:nezahrnutými 224:do 225:konsolidované 226:účetní 227:závěrky, 228:f) 229:konsolidované 230:výnosy 231:z 232:běžné 233:činnosti 234:rozvržené 235:podle 236:kategorií 237:činností 238:a 239:podle 240:zeměpisných 241:trhů, 242:pokud 243:se 244:tyto 245:kategorie 246:a 247:trhy 248:mezi 249:sebou 250:podstatně 251:liší 252:z 253:hlediska 254:způsobu, 255:kterým 256:je 257:organizován 258:prodej 259:zboží 260:a 261:výrobků 262:a 263:poskytování 264:služeb 265:spadajících 266:do 267:běžné 268:činnosti, 269:g) 270:charakter 271:a 272:obchodní 273:účel 274:transakcí, 275:které 276:nejsou 277:uvedeny 278:v 279:konsolidované 280:rozvaze, 281:a 282:finanční 283:dopad 284:těchto 285:transakcí, 286:pokud 287:jsou 288:rizika 289:nebo 290:užitky 291:z 292:těchto 293:operací 294:významné 295:a 296:pokud 297:je 298:zveřejnění 299:těchto 300:rizik 301:nebo 302:užitků 303:nezbytné 304:k 305:posouzení 306:finanční 307:situace, 308:h) 309:transakce, 310:s 311:výjimkou 312:transakcí 313:v 314:rámci 315:účetních 316:jednotek 317:v 318:konsolidaci, 319:které 320:konsolidující 321:účetní 322:jednotka, 323:konsolidované 324:účetní 325:jednotky, 326:účetní 327:jednotky 328:pod 329:společným 330:vlivem 331:nebo 332:účetní 333:jednotky 334:přidružené 335:uzavřely 336:se 337:spřízněnou 338:stranou, 339:včetně 340:objemu 341:takových 342:transakcí, 343:povahy 344:vztahu 345:se 346:spřízněnou 347:stranou 348:a 349:ostatních 350:informací 351:o 352:těchto 353:transakcích, 354:které 355:jsou 356:nezbytné 357:k 358:pochopení 359:finanční 360:situace, 361:pokud 362:jsou 363:tyto 364:transakce 365:významné 366:a 367:nebyly 368:uzavřeny 369:za 370:běžných 371:tržních 372:podmínek; 373:informace 374:o 375:jednotlivých 376:transakcích 377:lze 378:seskupovat 379:podle 380:jejich 381:charakteru 382:s 383:výjimkou 384:případů, 385:kdy 386:jsou 387:samostatné 388:informace 389:nezbytné 390:k 391:pochopení 392:dopadu 393:transakcí 394:se 395:spřízněnou 396:stranou 397:na 398:finanční 399:situaci; 400:výraz 401:„spřízněná 402:strana“ 403:má 404:stejný 405:význam 406:jako 407:v 408:mezinárodních 409:účetních 410:standardech 411:upravených 412:právem 413:Evropské 414:unie, 415:i) 416:odděleně 417:informace 418:o 419:celkových 420:nákladech 421:na 422:odměny 423:statutárnímu 424:auditorovi 425:nebo 426:auditorské 427:společnosti 428:za 429:účetní 430:období 431:v 432:členění 433:na 434:1. 435:povinný 436:audit 437:roční 438:účetní 439:závěrky, 440:2. 441:jiné 442:ověřovací 443:služby, 444:3. 445:daňové 446:poradenství, 447:4. 448:jiné 449:neauditorské 450:služby.
  - pair: **papír** (word 169) ↔ **nebyl** (word 167) → distance **1**
  - [ ] ✓ / correction: 

## conditional (by)  (9 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::87`
  - 1:Stav 2:oprávek 3:je 4:dán 5:součtem 6:odpisů, 7:které 8:by 9:byly 10:účtovány 11:podle 12:odpisového 13:plánu 14:za 15:dobu 16:používání 17:do 18:okamžiku 19:přechodu 20:z 21:daňové 22:evidence 23:na 24:účetnictví.
  - pair: **které** (word 7) ↔ **by** (word 8) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::92`
  - 1:(6) 2:Účetní 3:jednotky, 4:které 5:mají 6:povinnost 7:ověřování 8:podle 9:§_20, 10:nesmí 11:zveřejnit 12:informace, 13:které 14:předtím 15:nebyly 16:ověřeny 17:auditorem, 18:způsobem, 19:který 20:by 21:mohl 22:uživatele 23:uvést 24:v 25:omyl, 26:že 27:auditorem 28:ověřeny 29:byly.
  - pair: **který** (word 19) ↔ **by** (word 20) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-dev.conllu::251`
  - 1:Tam, 2:kde 3:účetní 4:jednotka 5:může 6:volit 7:mezi 8:více 9:možnostmi 10:dané 11:účetní 12:metody 13:a 14:zvolená 15:možnost 16:by 17:zastírala 18:skutečný 19:stav, 20:je 21:účetní 22:jednotka 23:povinna 24:zvolit 25:jinou 26:možnost, 27:která 28:skutečnému 29:stavu 30:odpovídá.
  - pair: **možnost** (word 15) ↔ **by** (word 16) → distance **0**
  - [ ] ✓ / correction: 

## aby/kdyby (absorbed by)  (9 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::115`
  - 1:Vyloučením 2:se 3:rozumí 4:takové 5:operace, 6:které 7:umožní, 8:aby 9:konsolidovaná 10:účetní 11:závěrka 12:neobsahovala 13:vzájemné 14:transakce, 15:které 16:byly 17:realizovány 18:účetními 19:jednotkami 20:v 21:konsolidaci.
  - pair: **závěrka** (word 11) ↔ **aby** (word 8, measured token: by) → distance **2**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::286`
  - 1:(4) 2:Okamžik 3:se 4:v 5:účetním 6:záznamu 7:zaznamenává 8:s 9:takovou 10:přesností, 11:aby 12:nejistota 13:v 14:určení 15:času 16:neměla 17:za 18:následek 19:nejistotu 20:v 21:určení 22:obsahu 23:účetních 24:případů.
  - pair: **nejistota** (word 12) ↔ **aby** (word 11, measured token: by) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::140`
  - 1:Pokud 2:banka 3:umožňuje, 4:aby 5:byl 6:ke 7:konci 8:rozvahového 9:dne 10:vykázán 11:pasivní 12:zůstatek 13:u 14:běžného 15:účtu, 16:pak 17:je 18:tento 19:zůstatek 20:obsahem 21:položky 22:„B.IV.2. 23:Krátkodobé 24:bankovní 25:úvěry“.
  - pair: **zůstatek** (word 12) ↔ **aby** (word 4, measured token: by) → distance **7**
  - [ ] ✓ / correction: 

## passive — finite aux (je/bude vydána)  (33 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-dev.conllu::250`
  - 1:Zobrazení 2:je 3:poctivé, 4:když 5:jsou 6:při 7:něm 8:použity 9:účetní 10:metody 11:způsobem, 12:který 13:vede 14:k 15:dosažení 16:věrnosti.
  - pair: **účetní** (word 9) ↔ **jsou** (word 5) → distance **3**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::296`
  - 1:Účetní 2:jednotka 3:dále 4:uvede 5:informace 6:o 7:druzích 8:zvířat, 9:která 10:jsou 11:vykazována 12:jako 13:dlouhodobý 14:hmotný 15:majetek 16:a 17:zásoby.
  - pair: **která** (word 9) ↔ **jsou** (word 10) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::410`
  - 1:Do 2:nákladů 3:nebo 4:výnosů 5:jsou 6:zaúčtovány 7:ve 8:stejných 9:obdobích, 10:kdy 11:jsou 12:zaúčtovány 13:náklady 14:nebo 15:výnosy 16:spojené 17:se 18:zajišťovanými 19:položkami.
  - pair: **náklady** (word 13) ↔ **jsou** (word 11) → distance **1**
  - [ ] ✓ / correction: 

## passive — past aux (byla vydána)  (31 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-test.conllu::314`
  - 1:Obdobně 2:se 3:postupuje, 4:pokud 5:účetní 6:závěrka 7:nebo 8:konsolidovaná 9:účetní 10:závěrka 11:nebyla 12:za 13:dané 14:účetní 15:období 16:sestavena.
  - pair: **závěrka** (word 6) ↔ **nebyla** (word 11) → distance **4**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::285`
  - 1:Účetní 2:jednotka 3:uvede 4:dále, 5:zda 6:byly 7:uzavřeny 8:ovládací 9:smlouvy 10:nebo 11:smlouvy 12:o 13:převodech 14:zisku 15:a 16:jaké 17:povinnosti 18:z 19:nich 20:vyplývají.
  - pair: **smlouvy** (word 9) ↔ **byly** (word 6) → distance **2**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::308`
  - 1:Informace 2:podle 3:písmen 4:a)_a_b) 5:není 6:účetní 7:jednotka 8:povinna 9:uvést, 10:pokud 11:byly 12:transakce 13:provedeny 14:mezi 15:účetní 16:jednotkou 17:a 18:jejím 19:jediným 20:společníkem.
  - pair: **transakce** (word 12) ↔ **byly** (word 11) → distance **0**
  - [ ] ✓ / correction: 

## analytic — aux (jsem/bude …)  (4 pairs in CLTT)

- `cs_cltt/cs_cltt-ud-test.conllu::166`
  - 1:(4) 2:Účetní 3:jednotky, 4:které 5:nejsou 6:založeny 7:nebo 8:zřízeny 9:za 10:účelem 11:podnikání, 12:uplatňují 13:ustanovení 14:odstavců 15:1 16:až 17:3 18:v 19:souladu 20:s 21:účetními 22:metodami.
  - pair: **které** (word 4) ↔ **nejsou** (word 5) → distance **0**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-test.conllu::144`
  - 1:V 2:případě 3:nákupu 4:nebo 5:prodeje 6:cizí 7:měny 8:za 9:českou 10:měnu 11:lze 12:k 13:okamžiku 14:ocenění 15:použít 16:kurzu, 17:za 18:který 19:byly 20:tyto 21:hodnoty 22:nakoupeny 23:nebo 24:prodány.
  - pair: **hodnoty** (word 21) ↔ **byly** (word 19) → distance **1**
  - [ ] ✓ / correction: 

- `cs_cltt/cs_cltt-ud-train.conllu::108`
  - 1:Položka 2:obsahuje 3:dále 4:výrobky 5:vlastní 6:výroby, 7:které 8:byly 9:aktivovány 10:a 11:předány 12:do 13:vlastních 14:prodejen, 15:a 16:zvířata 17:vlastního 18:chovu, 19:která 20:dospěla, 21:byla 22:aktivována 23:a 24:jsou 25:určena 26:k 27:prodeji 28:s 29:výjimkou 30:jatečných 31:zvířat.
  - pair: **které** (word 7) ↔ **byly** (word 8) → distance **0**
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
