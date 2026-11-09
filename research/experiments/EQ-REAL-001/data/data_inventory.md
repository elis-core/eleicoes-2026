# EQ-REAL-001 data inventory — updated 9 November 2026

**Evidence status:** Actual RN 2022 and 2026 presidential results and nationwide BR 2022/2026 archives have now been inspected and reconciled; no predictive search has been carried out.

| Dataset | Archive bytes | Local SHA-256 and ZIP CRC | Presidential section-level cross-source audit |
|---|---|---|---|
| 2022 RN first-round BU | Uploaded | Passed | Exact match against BR on all (round, municipality, zone, section, vote category) records |
| 2022 RN second-round BU | Uploaded | Passed | Exact match against BR |
| 2022 nationwide presidential `votacao_secao_2022_BR.zip` | Uploaded | Passed | 82,711 RN first+second-round records; zero count differences |
| 2026 RN first-round BU | Uploaded | Passed | Exact match against BR |
| 2026 RN second-round BU | Uploaded | Passed | Exact match against BR |
| 2026 nationwide presidential `votacao_secao_2026_BR.zip` | Uploaded | Passed | 89,660 RN first+second-round records; zero count differences |
| 2026 RN state `votacao_secao_2026_RN.zip` | Uploaded | Passed | **No presidential records**, not used for presidential modelling |
| REL-RN-004, REL-RN-005, EQ-CMP-RN-001 original code/splits | Not recovered | Not applicable | **Not independently reproduced** |
| Official TSE SHA-512 companion hashes | Not retrieved | **Pending** | Self-generated SHA-256 is not a replacement for matching official hash |
| 2022–2026 RN section continuity | Derived | 7,565 shared identifier keys | Administrative/geographic stability is unproven |

Local ZIP SHA-256 values, source names, exact totals, script versions and limitations are in `reports/2022_2026_official_crosssource_audit.md`, `data/historical_2022_sources.csv` and `data/SHA256_uploaded_sources.txt`.

**Dataset policy:** 2026 RN outcomes were observed during the audit; do not describe this region as a pristine external test. Choose and freeze municipalities from previously unexamined states before reading 2026 test targets. Cross-year matching by section keys is not a guarantee of population continuity.

Derived per-section 2022 and 2026 CSVs were created and supplied in the working conversation; full binary source ZIPs and derived CSVs have **not** been committed to GitHub. The branch contains executable extraction/reconciliation source and manifests. All official source URLs remain in the inventories.
