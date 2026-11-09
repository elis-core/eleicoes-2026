# Milestone A — RN geographic-continuity and independent aggregation cross-check

**Execution date:** 9 November 2026. **Scope:** actual user-supplied TSE-labelled 2026 RN BU ZIPs, not synthetic data. **Validation role:** data-quality checks only; no predictive model has been estimated, no untouched external test designated or opened for validation.

## 1. Section aggregation status by round

The exact same 8,115 (municipality, electoral zone, section) keys occur in both presidential rounds.

| Status from `DS_SECOES_AGREGADAS` | Count |
|---|---:|
| No aggregation indication in either round (`#NULO#`) | 7,910 |
| Aggregation indication, **identical value** in both rounds | 205 |
| Indication newly present in round 2 | 0 |
| Indication absent in round 2 | 0 |
| Aggregation indication changed from one non-null value to another | 0 |

The 205 sections occur in **73 municipalities**. Examples of observed values are `81`, `214`, `150` and `65`, indicating a reference to a section number. Source documentation or independently verified section metadata is still needed to establish the exact aggregation semantics.

Top flagged municipalities: Ceará-Mirim 16, João Câmara 14, Caicó 8, Ielmo Marinho 8, São Gonçalo do Amarante 8, São José de Mipibu 8, Extremoz 7, Pedro Avelino 7.

## 2. Registered-electorate continuity

**1,584** section keys have differing registered electorate counts across rounds: **1,541** among unflagged sections and **43** among flagged sections. Electorate count change ranges from **−41 to +23**. Flag stability alone does not establish a stable individual voting population. Retain E1/E2 as separate fields, and perform sensitivity checks excluding flagged sections and/or changed-electorate sections.

## 3. Independently published result reconciliation

Second-round RN published statewide total sourced to the TSE via Band:
- Lula: **1,413,596**, Flávio Bolsonaro: **737,409**
- Blank: **19,939**, null: **61,879**
- Turnout: **2,232,823**

All five figures match sums computed from the uploaded 2026 RN ballot bulletins.

Source: https://www.band.com.br/politica/eleicoes/2026/apuracao/presidente/rn (retrieved 9 November 2026).

Additional *municipal* cross-check for Natal, 2026 second round:

| Measure | Derived from original BU CSV | Published TSE-sourced municipality result | Delta |
|---|---:|---:|---:|
| Lula | 258,155 | 258,155 | 0 |
| Flávio Bolsonaro | 202,844 | 202,844 | 0 |
| Blank | 4,221 | 4,221 | 0 |
| Null | 12,681 | 12,681 | 0 |
| Turnout | 477,901 | 477,901 | 0 |
| Electorate | 573,154 | 573,154 | 0 |
| Sections | 1,477 | 1,477 | 0 |

Municipal sources:
- https://placareleitoral.org/resultado/rn/natal
- https://www.piranot.com.br/eleicoes/apuracao/?cargo=presidente&municipio=natal&uf=rn

The Natal first-round candidate totals also match a separately published table: Lula **213,790**, Flávio Bolsonaro **192,739**, from https://meusrepresentantes.com.br/municipios/2408102.

**Evidence hierarchy:** independent publisher totals provide a corroboration of sums; they are TSE-derived, not independent measurements of voter intent. This is not yet full reconciliation against original TSE municipal publication resources for all 167 municipalities.

## 4. Remaining verification gates

- Obtain official companion SHA-512 files and check their digest against uploaded archives; SHA-256 and ZIP CRC checks are complete.
- Complete independent municipality-by-municipality comparison for all 167 municipalities, prioritising the TSE official result resource rather than secondary summaries.
- Verify TSE documentation of `DS_SECOES_AGREGADAS` and classify administrative continuity; never infer identical elector populations from 100% identifier matches.
- Recover original empirical scripts/splits and 2022 references.
- Freeze exclusion list and external municipality selection before running any predictive search.

Reproduce section-level continuity with `src/continuity_audit.py` and original source ZIPs.
