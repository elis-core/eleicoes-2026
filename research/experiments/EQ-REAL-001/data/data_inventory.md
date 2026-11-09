# Data inventory — 9 November 2026

| Source | Scope | Verification | Current status |
|---|---|---|---|
| TSE `Resultados - 2026` | Nationwide section-level presidential results; section tally details | Catalogue resource names and RN metadata pages inspected | Listed, **archive not downloaded** |
| TSE `Resultados - 2026 - Boletim de Urna` | RN round 1 and round 2 CSV ZIPs and SHA2 resources | Catalogue and second-round RN metadata page inspected | Listed, **archives/hashes not downloaded** |
| GitHub `dados/2026/presidente/RJ` | Existing RJ presidential data | Path existence checked | Structure and provenance not yet audited |
| GitHub `dados/2022/presidente/RJ` | Existing RJ historical presidential data | Path existence checked | Structure and provenance not yet audited |
| GitHub `research/eq-prb-001-*` branches | Synthetic experiments v0.1–v0.12 | Branches and open PRs #5–#10 checked | Research baseline *methodology*, not empirical election records |
| REL-RN-004 / REL-RN-005 / EQ-CMP-RN-001 | Reported earlier empirical benchmarks | Described in handoff.md only | Underlying original code/data/split lists **not recovered** |
| TSE 2022 official section datasets | Historical source | Handoff names required comparison | **Not yet retrieved** |
| Cloudflare R2 | Potential private large-file storage | No R2 credentials/access exposed in this execution | **Not inspected** |

## Blocker and next step

The TSE CDN ZIPs could not be downloaded from the available execution environment (web fetch rejected binary ZIP content; container DNS resolution failed; alternate download route unsuccessful). Obtain actual source bytes from a network-connected environment using `src/acquire.py`, retain receipt and digest, then inspect and map real columns. No real data counts or row-level audits can be claimed yet.

## Important TSE catalogue caveat

The official catalogue notes a 39-record discrepancy in electorate records associated with temporary voter transfers. Do not automatically subtract 39 from section aggregates; reconcile according to official definitions and traceable records.
