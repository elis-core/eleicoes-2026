# EQ-PRB-001 v0.11 — Independent Frozen Model Selection

**8 November 2026 · UK English · Completed synthetic milestone**

## Data scope

Every count is simulated. No actual election results, voter information,
software or voting-system infrastructure are evaluated. The source code
includes 8 integer-count sections per site, both rounds and four synthetic
categories. Latent counts are available to the generator for test assertions
but **never to the identification estimator**.

The version contains 6 comparison rows, each based on
1,000 independently seeded worlds for its generator configuration.
Methods/thresholds reusing the same worlds are *paired comparisons* and do not
increase the independent sample count.

## How to reproduce

Tested on Python 3.13.5 with NumPy 2.3.5 and Mistune 3.2.1.
From this directory, run:

```bash
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python experiment.py --version v0.11 --output . > execution.log
OPENBLAS_NUM_THREADS=1 python verify.py --version v0.11 --directory . > verify.log
python build_report.py --version v0.11 --directory .
```

**Important:** run `sha256sum -c MANIFEST.sha256` *before* regeneration.
The commands overwrite reproducible output files and can change file-level
hashes because of environment/serialization differences.

## Files

- `core.py`: synthetic two-round generator, fitting, conformal scores and exact algebraic interval inversion.
- `experiment.py`: version-specific scenario runner, fixed seeds and generated summary metrics.
- `verify.py`: integer accounting, independent brute-force interval check, finite-sample resolution, no-target-leakage, repeatability and result audits.
- `build_report.py`: builds the UK-English HTML/Markdown technical report.
- `results.json`, `metrics.csv`: executed outcomes (machine-readable).
- `RELATORIO_EQ-PRB-001_v0.11.md`, `.html`: methodology and findings.
- `execution.log`, `verify.log`: run receipts.
- `MANIFEST.sha256`: released file integrity manifest.

## Scientific caution

Independent source-site calibration is an assumption in these mathematical
simulations, not a verified external observation. False exclusions and positive
identification bounds depend on conditional site exchangeability, representative
reference data and rate/rounding assumptions. The procedure is **not validated
for real electoral results** and does not uniquely establish any conversion.

GitHub PRs do not automatically publish these reports in the Atlas UI.
