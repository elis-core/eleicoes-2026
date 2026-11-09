# Actual verified RN 2026 bweb presidential schema — 9 November 2026

**Input:** archive CSV member `bweb_1t_RN_051020261403.csv` or `bweb_2t_RN_261020260742.csv`, Latin-1, semicolon-delimited, quoted headers. Only rows with `DS_CARGO_PERGUNTA == Presidente`.

| Canonical field | TSE CSV field | Notes |
|---|---|---|
| year | `ANO_ELEICAO` | 2026 |
| round | `NR_TURNO` | 1 or 2 |
| office | `DS_CARGO_PERGUNTA` | President |
| UF | `SG_UF` | RN |
| municipality | `CD_MUNICIPIO`, `NM_MUNICIPIO` | Original code preserved |
| zone/section | `NR_ZONA`, `NR_SECAO` | Key with municipality |
| polling place | `NR_LOCAL_VOTACAO` | Official ID, not inferred |
| electorate | `QT_APTOS` | Round-specific |
| turnout | `QT_COMPARECIMENTO` | Round-specific |
| abstention | `QT_ABSTENCOES` | Round-specific |
| category type | `CD_TIPO_VOTAVEL` | 1 nominal, 2 blank, 3 null |
| candidate | `NR_VOTAVEL` | 13 Lula; 22 Flávio Bolsonaro in this source |
| count | `QT_VOTOS` | Integer, summed by source key/category |
| section aggregation | `DS_SECOES_AGREGADAS` | 205 matched keys with non-null flag in either round |

B = type 2, N = type 3. In round 1, eliminated-candidate counts are preserved by `NR_VOTAVEL`; O1 is their sum excluding nominees 13 and 22. The second round includes only the two finalist candidate types plus B/N. Missing B/N records within an otherwise verified section are treated as zero, not as absent section records.

**Warning:** `votacao_secao_2026_RN.zip` (uploaded) has no presidential rows; use the BU files for this pilot. No 2022 schema or municipality/UF-level independent audit is yet certified.
