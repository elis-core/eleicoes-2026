# Milestone A data-quality report — initial checkpoint

**Date:** 9 November 2026  
**Evidence level:** official catalogue verified; no raw votes downloaded.

| Check | Status | Evidence |
|---|---|---|
| 2026 RN section-level ZIP listed by TSE | Catalogue-verified | RN resource ID 41e881d8-35fc-4f7c-b194-87dd61ae259b |
| 2026 nationwide presidential section-level ZIP listed | Catalogue-verified | Presidential resource page |
| RN first/second-round ballot ZIPs listed | Catalogue-verified | TSE boletim de urna catalogue |
| Actual ZIP file SHA-256 and archive integrity | **Not tested** | Download unavailable |
| Actual CSV schema and rows | **Not tested** | Raw records unavailable |
| Presidential count conservation by section | **Not tested** | Raw records unavailable |
| Electorate ≥ turnout checks | **Not tested** | Raw records unavailable |
| Round-1/round-2 section joins | **Not tested** | Raw records unavailable |
| Municipality/UF reconciliation | **Not tested** | Raw records unavailable |
| Historic 2022 comparability | **Not tested** | Official 2022 raw records not retrieved |
| Previous empirical benchmark reproduction | **Not tested** | Source code and exact inputs not recovered |

**No empirical equations, electoral counts, model improvements or predictive intervals are reported.**

## Blocking conditions

Binary ZIP requests through web were rejected as unsupported content type, and shell requests to the official CDN failed DNS resolution in this execution environment. A separate download mechanism also failed. The actual files must be fetched and preserved on a network-enabled runner before any real data quality claims.

## Operational controls

Treat previously studied RN municipalities as exposed; never select them for an untouched external validation. Hold back the 2026 second-round outcomes of reserved municipalities before model selection. Preserve separate forecast regimes (conditional on actual second-round turnout versus fully prospective).
