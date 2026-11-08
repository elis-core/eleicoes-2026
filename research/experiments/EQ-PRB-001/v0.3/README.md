# EQ-PRB-001 — v0.3 mathematical simulation experiment

**8 November 2026 · UK English · Synthetic data only · Not statistically validated**

This package tests whether a model can distinguish an invented B→W count transformation from changes in natural category preferences. It extends the [EQ-PRB-001 v0.2 experiment](../v0.2/) with alternative behavioural baselines, reference-precision sensitivity and independent split calibration of prediction intervals.

**No real election figures or voting-system data are used.** The exercises test mathematical identifiability. The model does not identify an actual electoral mechanism or establish that any transformation occurred.

## Findings

- 48,000 independent synthetic dataset replicates, including 12,000 null calibration, 27,000 evaluation and 9,000 interval calibration replicates.
- 73 candidate models; 81 model comparisons across three hypothetical reference sample sizes, three behavioural design families and nine synthetic generators.
- A composite natural-behaviour null reduces false positives but also reduces detection; no tested design consistently meets the 80% sensitivity goal.
- A quadratic-behaviour null stress test at reference n=1,800 reports 41/1,000 false alarms and a one-sided 95% upper limit of 5.29%, exceeding the 5% confidence criterion.
- Within-generator split calibration improves the 95% coverage of H11-D3 blank-count intervals from about 90.4% to 95.0% for reference n=1,800, with wider prediction bands.
- Exact theoretical observational equivalence is demonstrated for *independent stochastic thinning*, not for deterministic half-up integer rounding.

Refer to the [full Markdown report](RELATORIO_EQ-PRB-001_v0.3.md) or [standalone HTML report](RELATORIO_EQ-PRB-001_v0.3.html).

## Runtime and reproduction

Requires Python 3.13, `numpy==2.3.5`, `scipy==1.17.0` and, **only for the HTML report**, `mistune==3.2.1`.

Install dependencies in an isolated Python environment, then run from this directory:

```bash
OPENBLAS_NUM_THREADS=1 python eq_prb_001_v03.py --calib 1000 --eval 1000 --sizes 1800 --seed 20261108 --out run1800 > run1800.log
OPENBLAS_NUM_THREADS=1 python eq_prb_001_v03.py --calib 1000 --eval 1000 --sizes 300 --seed 20261109 --out run300 > run300.log
OPENBLAS_NUM_THREADS=1 python eq_prb_001_v03.py --calib 1000 --eval 1000 --sizes 75 --seed 20261110 --out run75 > run75.log
OPENBLAS_NUM_THREADS=1 python combine_results.py
OPENBLAS_NUM_THREADS=1 python verify_v03.py
python build_report.py
sha256sum -c MANIFEST.sha256
```

The last command checks the published originals. **Run `sha256sum -c MANIFEST.sha256` before re-execution** if you want to check the source package unchanged; the earlier commands overwrite result files. Differences across library/platform versions must be documented, rather than silently treated as equivalent.

`OPENBLAS_NUM_THREADS=1` is a reproducibility/performance setting. Each reference sample size uses a separately frozen seed; calibration and evaluation draws are separate portions of the corresponding generated stream.

## Files

| File | Meaning |
|---|---|
| `eq_prb_001_v03.py` | Standalone synthetic generator, search and interval-calibration code |
| `run1800/`, `run300/`, `run75/` | Independently seeded raw outputs (JSON and CSV) |
| `run1800.log`, `run300.log`, `run75.log` | Execution logs |
| `combine_results.py` | Combine the three reference-size runs without re-estimation |
| `results_v0.3.json` | Combined results, method, assumptions and limits |
| `model_comparison.csv` | 81 model comparison rows, including false-alarm bounds |
| `intervals.csv` | Marginal interval coverage and widths for 50%, 80% and 95% |
| `verify_v03.py` | Accounting, covariance and identifiability checks |
| `build_report.py` | Generates the Markdown and HTML report |
| `RELATORIO_EQ-PRB-001_v0.3.md` | Technical report (UK English) |
| `RELATORIO_EQ-PRB-001_v0.3.html` | Standalone reader-friendly HTML report |
| `MANIFEST.sha256` | SHA-256 integrity hashes of the packaged files |

### Research interpretation

The composite-null threshold is the **maximum** of the higher-method 97.5th percentiles computed on four independently simulated natural-behaviour calibration generators. It is *not* a universal finite-sample false-alarm guarantee, nor are the individual 95% binomial bounds a joint guarantee across all 36 null configurations. The true simulator's baseline category probabilities are embedded in the candidate model family, which remains an oracle advantage. The predictive score is Gaussian approximate and the synthetic transfer uses half-up integer rounding.

The exact equivalence proof uses a distinct **independent per-vote stochastic thinning** mechanism; its interpretation must not be extended to imply distributional equality of deterministic rounded transfers.
