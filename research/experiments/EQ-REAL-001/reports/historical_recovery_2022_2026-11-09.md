# EQ-REAL-001 — Completed 2022 RN source recovery and cross-source audit

Updated 9 November 2026. The two previously unavailable official-labelled 2022 RN BU ZIPs and the nationwide 2022 presidential section ZIP have now been uploaded by the user and checked. A nationwide 2026 presidential section ZIP was also uploaded.

**All four ZIPs passed CRC integrity tests**; SHA-256 digests were computed from the uploaded bytes and recorded in `data/historical_2022_sources.csv`. Official SHA-512 verification against the TSE companion files is still outstanding.

## Verified 2022 RN observations

- 7,674 presidential section identifiers in both rounds, exactly matched across rounds.
- 2022 turnout: 2,090,604 (round 1), 2,108,799 (round 2).
- 2022 Lula: 1,264,179 and 1,326,785.
- 2022 Jair Bolsonaro: 622,731 and 711,381.
- First-round other nominees: 120,354; blanks: 26,151 / 20,585; nulls: 57,189 / 50,048.
- Zero section accounting identity failures in 2022.

The nationwide 2022 BR archive matches **all 82,711 individual RN section/category count records** in the paired BU files with **zero discrepancies**. The 2026 nationwide BR archive likewise matches all **89,660** RN section/category records with zero discrepancies. These are independent file-format/source checks of *published official tallies*, not evidence independent of the election data production chain.

Cross-year comparison: 7,565 section-key matches across 2022 and 2026, 109 keys unique to 2022 and 550 unique to 2026. Of the matches, 459 have a differing polling-place ID, and 7,449 have a different first-round electorate count.

Reproduction: `src/historical_bu_audit.py`, `src/strict_section_source_reconciliation.py`, `src/crossyear_rn.py`.

## Outstanding items

- Obtain TSE official companion checksum resources to verify original authenticity independently.
- Recover earlier real-data research implementations and exact development/test municipality lists. A previous search of available Project/Library documents and inspected GitHub research branches did not locate REL-RN-004, REL-RN-005 or EQ-CMP-RN-001 source code.
- Calibrate behavioural benchmarks from the verified historical observations **without** opening reserved 2026 external test outcomes. Validation plan remains draft.
- Freeze external reserve outside RN, scoring protocol and threshold tiers before equation selection.

No model coefficients or predictive accuracy claims are reported at this stage.
