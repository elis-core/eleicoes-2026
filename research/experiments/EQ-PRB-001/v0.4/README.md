# EQ-PRB-001 v0.4 — Partial identification

**8 November 2026 | UK English | Synthetic data only | Exploratory research**

Version 0.4 follows the v0.3 identifiability findings. It returns a **finite set of compatible mathematical count-transformation rules** under explicitly bounded natural changes in category probabilities. It does not infer any real-world election process or use actual electoral returns.

## Scientific outcome

- 21,000 independent synthetic two-round dataset worlds; 7 generators × 3 independent reference-sample sizes × 1,000 worlds.
- 64 frozen candidate models including no transformation H00 and hypothetical temporal patterns H01/H10/H11, with constant/step/logistic rates.
- 126 evaluated constraint combinations (3 reference sizes × 7 generators × 3 natural-behaviour envelopes × 2 rate-heterogeneity envelopes), reusing the same independent worlds across constraint settings.
- Correct on-grid generating candidate was included in all 93 **correctly specified configuration tests**, but this is an unusually conservative synthetic construction and is **not** a general coverage validation.
- Under a broad natural-behaviour envelope, H00 and all other 63 equations remained compatible in the H11-D3 trials: **no unique identification**.
- A separate exact four-category **integer-count** likelihood, summing over compatible latent blank counts, was checked by exhaustive normalisation for totals 1–7.

See the [UK-English technical report](RELATORIO_EQ-PRB-001_v0.4.md), or [standalone HTML](RELATORIO_EQ-PRB-001_v0.4.html). The report distinguishes valid-assumption experiments from natural-behaviour/reference-bias **misspecification stress tests**.

**Research limitation:** The 64-model grid was frozen after a small exploratory pilot and before the full 21,000-world run; this is *not* a formally preregistered experiment. True amplitudes were deliberately chosen on this grid. The 95% finite-sample inclusion claim applies conditionally only to the frozen grid and the stated bounded-shift/independence assumptions, not arbitrary data or continuous equation spaces.

## Reproduce

Requires Python 3.13, NumPy 2.3.5, SciPy 1.17.0 and Mistune 3.2.1 (Mistune is used only to build the HTML report). On a suitably provisioned machine, run:

```bash
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python eq_prb_001_v04.py --seed 20261108 --replicates 1000 --reference-sizes 1800 300 75 --out . > execution.log
OPENBLAS_NUM_THREADS=1 python verify_v04.py
python build_report.py
```

Use `sha256sum -c MANIFEST.sha256` **before** rerunning if you want to verify the released outputs without overwriting them. Running the analysis replaces `results_v0.4.json`, `identified_sets.csv`, `examples.json` and `execution.log`. Re-running `build_report.py` replaces the two reports. Differences under alternative dependency versions must be reported, not silently assumed equivalent.

## Contents

| File | Purpose |
|---|---|
| `eq_prb_001_v04.py` | Synthetic generation, fixed 64-model library, conditional confidence-set inversion and exact integer likelihood |
| `verify_v04.py` | Unit/integration verification and exhaustive small-count likelihood normalisation |
| `build_report.py` | Deterministic report generator using the stored results |
| `results_v0.4.json` | Full numerical results, assumptions, seeds and candidate definitions |
| `identified_sets.csv` | All 126 evaluated configurations, including assumption-validity flags and confidence-set sizes |
| `examples.json` | Representative compatible-equation sets, with four groupwise decision thresholds |
| `execution.log` | Full-run execution receipt |
| `RELATORIO_EQ-PRB-001_v0.4.md` | UK-English report |
| `RELATORIO_EQ-PRB-001_v0.4.html` | Standalone HTML report |
| `requirements.txt` | Reproducible Python package versions |
| `MANIFEST.sha256` | Integrity hashes for the files, excluding itself and the ZIP |

There is no dependency on v0.3 at runtime. The intended repository path is `research/experiments/EQ-PRB-001/v0.4/`; the earlier v0.1–v0.3 artefacts remain unchanged.
