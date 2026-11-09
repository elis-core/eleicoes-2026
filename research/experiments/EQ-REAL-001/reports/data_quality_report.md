# RN 2026 actual-data quality checkpoint — 9 November 2026

See [RN verified pilot](rn_real_data_pilot_2026-11-09.md).

- Three uploaded TSE-labelled ZIP archives: ZIP CRC check passed, downloaded-byte SHA-256 recorded.
- Presidential data **only** in uploaded round-1 and round-2 bweb archives; `votacao_secao_2026_RN.zip` contains 0 presidential rows.
- Round 1: 58,164 presidential rows / 8,115 sections / 167 municipalities; 2,171,013 turnout.
- Round 2: 31,496 presidential rows / 8,115 sections / 167 municipalities; 2,232,823 turnout.
- 8,115/8,115 matches on municipality, electoral zone and section.
- First and second rounds: **0** failures `C = sum(candidate votes)+blank+null`, **0** failures `E=C+abstention`, **0** turnout bounds failures, **0** duplicate candidate/category rows.
- 0 polling-place ID changes; **205** matched sections flagged as aggregated in one or both rounds.
- **1,584** sections differ in registered electorate between rounds; must preserve round-specific electorate.
- Outstanding: compare with independently published municipality/UF totals; recover TSE SHA-512 companions; review aggregation semantics and round-to-round geographic continuity; obtain 2022 real reference.

The first empirical checkpoint is **not** a statement of validated predictive performance. No symbolic equation fitted, no predictive benchmark rerun, no external municipality test performed.
