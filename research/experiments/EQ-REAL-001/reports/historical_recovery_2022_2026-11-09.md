# EQ-REAL-001 — 2022 historical recovery checkpoint (9 November 2026)

## Official sources located

The TSE catalogue `Resultados - 2022` explicitly says the UF-level `votacao_secao_2022_UF` files cover *state offices*, while the presidential section voting data are in `votacao_secao_2022_BR.zip`. Do **not** use `votacao_secao_2022_RN.zip` as presidential data, or equate candidate ballot number 22 across years with the same candidate.

The official 2022 RN `bweb` ballot bulletin ZIPs were also located (first round `bweb_1t_RN_051020221321.zip`, second `bweb_2t_RN_311020221535.zip`). All source URLs and TSE catalogue resource IDs are recorded in `data/historical_2022_sources.csv`.

**Status: located and catalogue-verified, not downloaded.** Network download of the 2022 ZIP archives failed in the execution environment. **No 2022 vote counts, official hashes, or cross-year section matches have been calculated or claimed.** User-supplied original archives or a network-enabled runner are required.

TSE catalogue sources:
- https://dadosabertos.tse.jus.br/dataset/resultados-2022
- https://dadosabertos.tse.jus.br/dataset/resultados-2022-boletim-de-urna

## Previous empirical benchmark recovery

Inspected the current GitHub `main` and the open `research/eq-prb-001-v06-v12-20261108` tree. The research branch contains synthetic EQ-PRB material; it does not establish recovery of REL-RN-004, REL-RN-005 or EQ-CMP-RN-001 original executable implementations and held-out municipality lists. A scoped search of available Project/Library files found no corresponding original data/code. These benchmarks therefore remain **reported but not independently reproduced**.

Files needed to reproduce the claimed figures:
- exact input ZIP/CSV archives, extraction scripts and SHA hashes
- original source and package versions for the three empirical experiments
- exact exposed municipality lists and historical round matching rules
- original train/validation/test lists and scoring scripts

## Control of external test outcomes

The 2026 RN raw dataset was already opened in full for data quality. This does **not** automatically imply that each municipality's performance has been examined, but prior REL-RN exposure records are incomplete. Until those records are recovered, RN municipalities must not be labelled genuinely untouched for EQ-REAL-001's independent test. Select external test municipalities from newly acquired states only after freezing their IDs and exclusions, and prevent target-level inspection before testing. Internal development may still use audited RN data.

## Next verification gates

1. Download both 2022 RN ballot bulletin ZIPs and optional BR presidential section file.
2. Verify source-level SHA-512 companions, archive ZIP CRC and downloaded-byte SHA-256.
3. Run year-neutral extraction and account identities for 2022 separately from 2026.
4. Reconcile administrative section keys across years only after checking municipality/zone changes, section aggregation and population comparability.
5. Reproduce earlier empirical benchmarks only after their exact original implementation and datasets have been recovered; explicitly report any unrecoverable materials.

This is a provenance/methodological checkpoint, **not** an equation-discovery result.
