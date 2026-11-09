# EQ-REAL-001 — Real-data presidential equation discovery, Mission v1.0

**Milestone A started and a first *actual* RN 2026 pilot completed on 9 November 2026.**

## Verified pilot

The user provided three TSE-labelled 2026 RN archives, followed by two 2022 RN BU ZIPs and nationwide presidential section ZIPs for 2022 and 2026. The two `bweb` files contain **8,115** presidential polling sections in each round, covering **167** municipalities. All 8,115 municipality/zone/section identifiers match across rounds; the section-level presidential counts conserve turnout exactly, with **zero** missing category-key duplicates or turnout/electorate identity failures. See [the audit report](reports/rn_real_data_pilot_2026-11-09.md), [data quality report](reports/data_quality_report.md) and [source SHA-256 hashes](data/SHA256_uploaded_sources.txt).

The uploaded `votacao_secao_2026_RN.zip` was inspected; despite its name it contains *no presidential rows* (only state offices). The actual presidential analysis therefore uses the two official-labelled ballot-bulletin ZIPs, not invented data.

**Partial provenance:** ZIP bytes, SHA-256 and CRC are verified locally; their official TSE companion SHA-512 hashes have not yet been compared. Nationwide BR 2022 and 2026 presidential archives now agree exactly with corresponding RN BU inputs on all 82,711 and 89,660 RN section/category count records respectively. The 2022–2026 join has 7,565 matching section IDs, though many polling places/electorate counts differ. Further independent municipality aggregate verification, official TSE SHA-512 comparison and administrative continuity analysis remain open.

### Reproduce the audit from original archive bytes

```bash
python3 src/validate_rn.py \
  --first /path/to/bweb_1t_RN_051020261403.zip \
  --second /path/to/bweb_2t_RN_261020260742.zip \
  --output rn_audit.json \
  --section-csv rn_presidential_sections.csv
```

The script generates a complete 8,115-row section-level data file (four target categories plus turnout and original identifiers) without dependence on synthetic data. The full derived CSV was exported in the working conversation; it is **not yet committed as a repository blob**. The script and upstream source checksums are committed to support reproduction on a runner holding the source archives.

Other scripts include `src/acquire.py` and `src/inspect_archives.py` for network-enabled source recovery and streaming archive structure inspection. The new real-data validation script is distinct from the prior acquisition-only mocked unit test.

## Planned next work

1. Recover and check official TSE SHA-512 signature companion resources and reconcile RN aggregate totals independently.
2. Investigate **205** section aggregation flags and **1,584** changed electorate counts before asserting geographic population continuity.
3. The actual official 2022 RN baseline data have been acquired and reconciled; recover original REL-RN-004, REL-RN-005 and EQ-CMP-RN-001 code/splits, and compare multiple no-transformation behavioural baselines on historical data.
4. Freeze independent municipality selection and the expanded prediction error framework **before** running external validation or tuning equations against reserved outcomes.
5. Fit and compare exact-count-conserving equations against flexible legitimate no-transformation behavioural baselines, using both symmetric finalist assignments and distinct known-turnout/prospective regimes.

The original five municipal high-precision conditions remain high-precision targets; promising/exploratory levels need pretest calibration. Good predictions do not prove a particular transformation or generating mechanism.

## Coordination

Research only; no changes to Atlas Pages, Worker or R2 production code. New branch/PR remains draft and must not be merged without authorisation. Authenticated GitHub user observed: `rochasamurai`; no claim of bot-authored commits.

## Historical recovery and first behavioural reference (9 November 2026)

- See [2022/2026 cross-source audit](reports/2022_2026_official_crosssource_audit.md) and [source receipts](data/historical_2022_sources.csv).
- First 2022 *known-turnout* no-transformation continuity reference executed across all 7,674 RN sections. Four-category summed section absolute error **116,490 votes**; per-section, per-category MAE **3.7950**. This is **not** an externally tested equation nor a prospective prediction. See [baseline report](reports/observed_2022_behavioural_reference.md), [versioned source](src/continuity_baseline_2022.py) and [results](validation/observed_2022_continuity_baseline.json).
- **0 of 167** municipalities meet all four original very narrow category accuracy limits with that simple reference. The fifth high-precision comparator-improvement requirement is not applicable to this baseline itself. This reinforces the need for independent, stronger behavioural comparators and non-binary success tiers; it is not an inference of transformation.
- Full derived CSVs are available as downloadable conversation files and reproducible from original archives; GitHub currently contains their scripts, provenance, reports and compact metrics rather than the CSV blobs themselves.
