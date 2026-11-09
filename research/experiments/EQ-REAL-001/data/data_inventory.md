# Data inventory — verified RN pilot, 9 November 2026

| Source | Scope | Observed status |
|---|---|---|
| Uploaded `bweb_1t_RN_051020261403.zip` | 2026 RN first round BU | **ZIP verified**, 747,317 records, 58,164 presidential rows, 8,115 sections |
| Uploaded `bweb_2t_RN_261020260742.zip` | 2026 RN second round BU | **ZIP verified**, 63,676 records, 31,496 presidential rows, 8,115 sections |
| Uploaded `votacao_secao_2026_RN.zip` | 2026 RN section voting | **ZIP verified**, 721,333 records; **no presidential records** (only state offices) |
| Official TSE `Resultados 2026` catalogue | Nationwide section-level presidential ZIP | Catalogue listed, nationwide archive not retrieved |
| GitHub `dados/2026/presidente/RJ` | RJ presidential site datasets | Directory exists; not verified as official raw section data |
| GitHub `dados/2022/presidente/RJ` | Historical RJ | Directory exists; unverified |
| REL-RN-004 / REL-RN-005 / EQ-CMP-RN-001 | Prior empirical benchmarks | Prior descriptions only; original code and split lists not yet recovered |
| Cloudflare R2 | Potential raw archive storage | Not inspected |
| 2022 official RN TSE raw records | Historic comparability | Not yet acquired |

## Reproducible audit

See `../reports/rn_real_data_pilot_2026-11-09.md` and `../src/validate_rn.py`. The BU ZIPs produce 8,115 fully matched presidential section keys across 167 municipalities, with zero failed turnout conservation checks. Source archive SHA-256 values appear in `SHA256_uploaded_sources.txt`.

**Provenance distinction:** ZIP integrity and local bytes verified; external official TSE SHA-512 companion checksum confirmation and independent aggregate reconciliation remain outstanding. Uploaded `votacao_secao` archive is unsuitable as presidential input.

**Exposure control:** prior inspected RN municipalities cannot serve as untouched tests. The newly derived full section CSV is a raw observation cache, **not model training data**. Independent test list and metrics are not frozen.
