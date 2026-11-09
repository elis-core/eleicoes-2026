# EQ-REAL-001 — Verified real-data equation discovery (v1.0)

Status: Milestone A **in progress; source catalogue independently checked, raw 2026 section data not yet downloaded** (9 November 2026).

## Objective

Recover and verify the TSE presidential first- and second-round section counts; reproduce prior real-data empirical benchmarks; discover shared integer-conserving predictive equations; validate only against previously unseen municipalities after freezing the protocol. Symmetric assignments of W/L and separate conditional-on-C2 vs prospective predictions are required.

## Implementation and current evidence

- Official source catalogue: https://dadosabertos.tse.jus.br/dataset/resultados-2026
- Official ballot bulletin catalogue: https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna
- The catalogue lists RN and nationwide 2026 section-level resources, plus RN first/second round bulletin ZIPs and SHA2 resources.
- Repository default branch contains `dados/2026/presidente/RJ` and `dados/2022/presidente/RJ`; this is not yet an audited RN section-level resource.
- Download from this execution environment failed due to inaccessible CDN: **do not infer counts, checksums, schemas or sample results**.
- Earlier EQ-PRB-001 PRs #5–#10 are synthetic studies; their reported findings are not 2026 empirical checks.
- The authenticated GitHub connection is `rochasamurai`; this PR does not claim bot authentication.

## Reproduction from a machine with TSE CDN connectivity

```sh
python3 src/acquire.py --manifest data/source_manifest.csv --output-dir /path/to/tse-raw --metadata-output data/download_receipts.csv
python3 src/inspect_archives.py --directory /path/to/tse-raw --output /path/to/archive_inspection.json
python3 -m unittest discover -s tests -v
```

Both scripts are standard-library only. Never modify official archives; retain downloaded bytes and SHA-256. The inspection script scans headers and row counts without loading entire CSVs into spreadsheet software. Extraction and schema mapping must be completed *after* the actual records have been inspected; missing schema fields are not fabricated.

## Research controls

The original five thresholds (0.50pp W/L, 0.10pp B/N and >=10% reduction in section-level absolute error, with >=4/5 municipalities) remain **high-precision targets**. Exploratory and promising cut-offs are provisional until calibrated and frozen using historical data and independently specified benchmarks; final external 2026 outcomes cannot be used to set thresholds. A validated predictive improvement requires genuine out-of-sample superiority over the best appropriate no-transformation comparator with uncertainty.

Do not merge this PR or alter Atlas publication workflows as part of this work.
