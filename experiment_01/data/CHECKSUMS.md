# Data provenance & checksums

Raw corpora are gitignored (`data/raw/`). This manifest lets "downloaded & verified" be reproducible.

| File | SHA256 | Bytes | LINDAT handle |
|---|---|---|---|
| KUK_1.0.zip | `8db46adf4dc31bb8a2bfb53711d670b88cc37a3b939b30ce95f2c76bc6a3f9a9` | 659261881 | http://hdl.handle.net/11234/1-5821 |
| cltt_2.0.zip | `11d106f410abfdd74e6d6d1abdecacd449222336730e87d6b09f0a5d97253f1f` | 6989730 | (CLTT 2.0, LINDAT) |

## Parser-QC gold: cs_cltt (UD_Czech-CLTT)

Verified 2026-07-01 to derive from CLTT 2.0 (per its README: "based on the Czech Legal Text
Treebank 2.0", 1121 sentences). Used as the parser-quality-control gold (§3) instead of converting
CLTT 2.0 PML. Source: https://github.com/UniversalDependencies/UD_Czech-CLTT

- git commit: `4a970dd58c4231a3d66d3cdb6aea16afb30c536d`
- files: cs_cltt-ud-{train,dev,test}.conllu (467 / 316 / 338 = 1121 sentences)
