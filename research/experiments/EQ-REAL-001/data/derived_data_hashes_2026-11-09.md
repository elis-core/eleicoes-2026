# Derived data SHA-256 checkpoint — 9 November 2026

The exact local output files below were created using the original uploaded bweb ZIPs, and are available as conversation attachments. GitHub stores their regeneration scripts and provenance; these CSV bytes are **not yet committed to GitHub**.

| Local derived file | SHA-256 | Records |
|---|---|---:|
| `rn_presidential_sections.csv` | `2dcad34914e66006b961eb9e2c5c68d6661ded99c2b0cc47131f9173973244ab` | 8,115 |
| `rn_presidential_municipalities_2026.csv` | `cdd639df4fee6b425abec0851a44c39f809b28d0154f7727cf1b40d75e3a1509` | 167 |
| `aggregation_flagged_sections.csv` | `a5c75c42e5b4d9492fcf1b08d5381b0fef20218c2b7822ef9a91785cbcafc0d4` | 205 |

Municipality totals result from summing all 8,115 verified first/second-round sections. All 167 municipality-level presidential turnout identities passed with **0 residual**. This is a within-dataset accounting check, distinct from matching published TSE municipal summary files.

Run:
```sh
python3 src/validate_rn.py --first ORIGINAL_FIRST.zip --second ORIGINAL_SECOND.zip --output rn_audit.json --section-csv rn_presidential_sections.csv
python3 src/municipality_reconciliation.py --sections rn_presidential_sections.csv --output rn_presidential_municipalities_2026.csv
python3 src/continuity_audit.py --first ORIGINAL_FIRST.zip --second ORIGINAL_SECOND.zip --output continuity_audit.json --flagged-csv aggregation_flagged_sections.csv
```

Do not present the fully materialised first- and second-round CSV dataset as an untouched external test by itself. Future external test selection and scoring must be independently frozen and isolated from model development, taking account of previously analysed municipalities.
