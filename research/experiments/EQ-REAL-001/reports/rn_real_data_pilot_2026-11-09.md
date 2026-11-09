# RN 2026 — Verified presidential ballot-bulletin pilot (9 November 2026)

**Status:** The three user-provided actual ZIP archives were inspected and passed ZIP CRC verification. Official TSE server-side SHA-512 comparison is **not yet performed** (checksum files not provided); original files were supplied by the user.

## Source file integrity

| Uploaded official-labelled archive | Bytes | SHA-256 |
|---|---:|---|
| `bweb_1t_RN_051020261403.zip` | 54,412,606 | `e5a2a3980e2db6b791d81a019cd3efa8dbb3c4543ff3b1579a84d30cf2a87a3d` |
| `bweb_2t_RN_261020260742.zip` | 4,424,654 | `cf48f4e878bace44e0b3f1ab0c133e0fd59970ca9fc6f317141a9cef7f28d423` |
| `votacao_secao_2026_RN.zip` | 26,162,748 | `5d4866393b97b5e0b48e31dc0907a073718c00dfdfbf149d530d80f8c0e6789c` |

Actual CSV line counts excluding headers: bweb first round **747,317** (presidential **58,164**), bweb second round **63,676** (presidential **31,496**), votacao_secao **721,333** (**zero presidential**). The latter is *not* a valid replacement presidential source: in the supplied archive it contains only state offices.

## Raw presidential sums — no prediction or fitting

| Category | First round | Second round |
|---|---:|---:|
| Lula (candidate 13) | 1,237,963 | 1,413,596 |
| Flávio Bolsonaro (candidate 22) | 720,493 | 737,409 |
| All other presidential candidates | 113,505 | 0 |
| Blank presidential (type 2) | 33,172 | 19,939 |
| Null presidential (type 3) | 65,880 | 61,879 |
| **Turnout** | **2,171,013** | **2,232,823** |
| Registered electorate | 2,659,825 | 2,659,867 |
| Abstention | 488,812 | 427,044 |

Counts use presidential office `DS_CARGO_PERGUNTA == Presidente`, one row per non-zero recorded category, key (`CD_MUNICIPIO`, `NR_ZONA`, `NR_SECAO`). Missing blank/null rows imply zero for aggregation, not a missing observation. Counts must be checked against supplementary official municipal/UF aggregates before national provenance is considered complete.

## Section-level audit results

- **8,115** unique presidential section keys in each round, **167** municipalities.
- **8,115 / 8,115 (100%)** keys match between rounds; no unpaired key.
- Both rounds: **0** failed section count identities `C = sum(candidate)+blank+null`; **0** failed `E=C+abstention`; **0** negative/excess turnout failures.
- **0** duplicated presidential candidate/category rows and **0** within-section inconsistent metadata rows in either round.
- **0** polling-place ID changes across matched keys.
- **205** matched section keys have a non-null section aggregation flag in at least one round: inspect geographic/section mergers before population-continuity claims.
- **1,584** sections have changed registered electorate counts between rounds. This is not automatically an error; preserve as separate inputs.
- **1,343** sections have lower second-round than first-round turnout; turnout must not be assumed monotonically increasing.

## Reproduce

```bash
python3 src/validate_rn.py --first /path/to/bweb_1t_RN_051020261403.zip --second /path/to/bweb_2t_RN_261020260742.zip --output rn_audit.json --section-csv rn_presidential_sections.csv
```

Original source SHA-256 values, rather than filenames alone, are the integrity authority. The script generates all 8,115 rows with original identifiers. This technical report is derived from the uploaded raw files; no synthetic dataset was used.

## Limitations

- Original official TSE SHA-512 companion files not yet verified.
- No independent municipal/UF official aggregate comparison has been completed.
- Matching section numbers does not ensure identical elector composition; aggregation flags require follow-up.
- The earlier REL-RN reports and original code/splits have not been reproduced.
- **No external test municipality has yet been predesignated; the validation plan remains draft.** Do not use any section-level second-round targets for training, calibration or model selection in a future withheld test.
