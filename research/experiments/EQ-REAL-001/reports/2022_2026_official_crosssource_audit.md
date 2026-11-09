# Official cross-source audit: RN 2022 and 2026 — 9 November 2026

## Actual archive bytes examined

The user supplied four new archives: two RN 2022 BU ZIPs and nationwide 2022 and 2026 presidential section ZIPs. Original 2026 RN BU ZIPs were supplied previously. **Every new ZIP passed the internal ZIP CRC test.** SHA-256 below is calculated from the uploaded bytes (not an unverified TSE digest).

| Original file | Bytes | SHA-256 |
|---|---:|---|
| `bweb_1t_RN_051020221321.zip` | 18,274,320 | `22e581875468b79c0329b97ab1d943924999e86aca31aac8833a8712bfa98a90` |
| `bweb_2t_RN_311020221535.zip` | 1,090,336 | `b3aad33d132cdb0ef963c99117d4578161eb37e1d608dbf93aede538b9d440ab` |
| `votacao_secao_2022_BR.zip` | 271,292,455 | `9353993de5cf03778aef44e01d4925e7ee105f5262491d344a2f0dbc956b0139` |
| `votacao_secao_2026_BR.zip` | 241,891,087 | `c928321f63f2d095706fca73d4607c048d2ada23bda6876455d6911aaf1bc9c1` |

TSE catalogue sources: https://dadosabertos.tse.jus.br/dataset/resultados-2022 and https://dadosabertos.tse.jus.br/dataset/resultados-2026.

**Still outstanding:** independent official SHA-512 companion comparison. ZIP CRC and self-computed SHA-256 establish local integrity, not official source authenticity.

## 2022 official RN ballot bulletin sums — reconciled with nationwide 2022 archive

| Presidential category | First round | Second round |
|---|---:|---:|
| Lula | 1,264,179 | 1,326,785 |
| Jair Bolsonaro | 622,731 | 711,381 |
| Other first-round nominees | 120,354 | 0 |
| Blank | 26,151 | 20,585 |
| Null | 57,189 | 50,048 |
| **Turnout / sum of presidential votes** | **2,090,604** | **2,108,799** |
| Electorate (BU only) | 2,554,716 | 2,554,326 |
| Abstention (BU only) | 464,112 | 445,527 |
| Presidential section keys | 7,674 | 7,674 |

2022 first-round BU CSV: 878,328 all-office rows, 52,807 presidential rows. Second round BU CSV: 29,904 presidential rows. The 2022 nationwide presidential section ZIP contains **82,711 RN presidential candidate/category rows** across both rounds, and all RN candidate/category total sums and 7,674 per-round section keys agree with the two 2022 BU ZIPs. Accounting checks: **zero** section-level C versus candidate+blank+null failures; **zero** section-level E versus C+abstention failures.

## 2026 official RN cross-source agreement

The uploaded nationwide 2026 `votacao_secao_2026_BR.zip` contains 89,660 RN presidential candidate/category rows: 8,115 section keys in each round. Candidate and blank/null totals agree exactly with the previously audited 2026 RN BU ZIPs:

| Presidential category | First round | Second round |
|---|---:|---:|
| Lula | 1,237,963 | 1,413,596 |
| Flávio Bolsonaro | 720,493 | 737,409 |
| Other first-round nominees | 113,505 | 0 |
| Blank | 33,172 | 19,939 |
| Null | 65,880 | 61,879 |
| **Turnout** | **2,171,013** | **2,232,823** |
| Presidential section keys | 8,115 | 8,115 |

**Critical candidate-identity rule:** vote number 22 denotes *Jair Bolsonaro in 2022* and *Flávio Bolsonaro in 2026*. Do not treat the two nominees as a stable longitudinal candidate identity or infer individual vote transfers.

## Exact candidate/category-by-section reconciliation

In addition to statewide totals and section-key equality, a strict second pass compared the full (round, municipality, zone, section, vote number) -> integer-vote-count mapping in both sources, scanning the nationwide archives in chunks.

| Year | RN presidential section/category keys in BU | Same keys in nationwide BR | Mismatched keys or vote counts |
|---|---:|---:|---:|
| 2022 | **82,711** | **82,711** | **0** |
| 2026 | **89,660** | **89,660** | **0** |

There were **0** duplicated candidate/category rows in the input RN BU data for either year. This excludes the possibility of offsetting candidate/section discrepancies that cancel out in the statewide total. Reproduce via `src/strict_section_source_reconciliation.py` on each year's BR and paired RN BU ZIPs.

## Historical 2022–2026 key matching

| Measure | Verified |
|---|---:|
| 2022 RN section keys (both 2022 rounds) | 7,674 |
| 2026 RN section keys (both 2026 rounds) | 8,115 |
| Section keys present in both years | 7,565 |
| Present in 2022 only | 109 |
| Present in 2026 only | 550 |
| Matching keys with a different polling-place ID between 2022 and 2026 | 459 |
| Matching keys with changed round-1 registered electorate | 7,449 |
| Municipalities represented among cross-year matching keys | 167 |

Matching uses (TSE municipality code, electoral zone, section), not row position. Neither matched IDs nor unchanged polling-place IDs guarantee individual/population continuity across years. Stratify analyses by stable location, electorate change and administrative aggregation; apply robustness to municipality-level historical effects.

## Files / reproduction

- `src/historical_bu_audit.py` validates two BU rounds for a given year.
- `src/verify_br_crosssource.py` scans nationwide BR presidential CSV via pandas chunks, filters RN, and compares candidate/category counts and section keys to each official-labelled RN BU source; works for 2022 or 2026 and preserves exact candidate numbers.
- `src/strict_section_source_reconciliation.py` verifies the full key/count mapping with zero-error equality as a hard assertion.\n- `src/crossyear_rn.py` reconstructs 2022 section-level counts from 2022 RN BUs and compares section IDs to canonical 2026 RN CSV, outputting an auditable CSV and comparability JSON.
- Full 2022 derived section-level CSV (7,674 rows) was produced in the conversation and its local SHA-256 is `60054535b95e93f9f09abf4c3469bc94e4494b78713ed28479005770d1687822`. It is not committed as a GitHub blob; regenerate with the script using original archives.

## Status of benchmark and independent test

Original REL-RN-004 / REL-RN-005 / EQ-CMP-RN-001 executable code, scores and exposure lists remain unrecovered. The 2022 RN data can serve as a historical behavioural comparison, **not as an untouched 2026 external test**. Since complete 2026 RN outcomes were examined during the audit and earlier RN exposure is unresolved, external reserve selection should prioritise genuinely unexamined municipalities outside RN, with IDs, metrics and thresholds frozen before looking at their second-round targets. **No equation has yet been fitted or externally validated.**
