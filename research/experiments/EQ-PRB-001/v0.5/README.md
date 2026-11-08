# EQ-PRB-001 v0.5 — Off-grid partial identification

**8 November 2026 | UK English | Exploratory | Synthetic data only**

This version adds **continuous-amplitude partial identification** and **independently measured behavioural constraints** to the mathematical exercise begun in v0.1–v0.4.

The experiment does **not** use observed election results, voting-system infrastructure, or evidence of actual alterations. All count transformations are hypothetical mathematical scenarios. A candidate equation being compatible (or H00 being excluded) is not evidence of a real-world mechanism.

## Results at a glance

- 20,000 independently generated synthetic two-round datasets: 20 configurations × 1,000 independent datasets each; 42 procedure/assumption evaluations, with deliberate reuse of worlds for method comparisons.
- 5 invented municipalities, 40 sites, 320 sections, 2 rounds; 30 whole sites for training and 10 held out.
- Nine frozen temporal/shape families with **analytically computed continuous amplitude intervals** on `[0, 0.60]`, plus H00. The generating amplitude `0.377` is off the v0.4 grid.
- In properly specified matched-panel trials, the true on-family/off-grid amplitude remained compatible. In a deliberately biased-panel stress test, H00 was wrongly excluded at high precision.
- The 99%-calibrated conservative behavioural envelope was valid but too wide to eliminate any family in the tested settings.

See [the technical report](RELATORIO_EQ-PRB-001_v0.5.md) and [HTML report](RELATORIO_EQ-PRB-001_v0.5.html). The full JSON results contain the identification intervals for one representative trial of each configuration and experiment-level statistics for all 20,000 worlds.

**Important assumption:** the hypothetical external behavioural panel consists of independent, **representative**, matched section-round samples from the same latent behavioural distribution as the synthetic source counts. Independence does not establish representativeness; that condition would require independent substantive justification in any application.

## Reproduce

Tested with Python 3.13, NumPy 2.3.5, SciPy 1.17.0, Mistune 3.2.1.

```bash
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python eq_prb_001_v05.py --seed 20261108 --replicates 1000 --out . > execution.log
OPENBLAS_NUM_THREADS=1 python verify_v05.py
python build_report.py
sha256sum -c MANIFEST.sha256
```

**Verify the released files before re-running** using `sha256sum -c MANIFEST.sha256`. A rerun overwrites numerical outputs and the execution receipt; regenerating the report replaces both report files. The manifest records the original release bytes. Operating systems or dependency variations may change some serialisation details.

## Files

| File | Purpose |
|---|---|
| `eq_prb_001_v05.py` | Frozen synthetic generators, independent panels, analytical interval inversion, 20,000-world evaluation |
| `verify_v05.py` | Exact interval-solver checks against a numerical grid; accounting, assumptions and results tests |
| `build_report.py` | Regenerate UK-English Markdown and HTML from the results JSON |
| `results_v0.5.json` | Complete 42 evaluations, interval examples, seeds, model assumptions |
| `identified_intervals_summary.csv` | Compact comparison of retention, inclusion, interval widths and envelopes |
| `examples.json` | One per-case display of compatible continuous intervals |
| `execution.log` | Successful full-run execution receipt |
| `RELATORIO_EQ-PRB-001_v0.5.md` | Technical report in UK English |
| `RELATORIO_EQ-PRB-001_v0.5.html` | Standalone HTML report |
| `requirements.txt` | Dependency versions |
| `MANIFEST.sha256` | SHA-256 checksums of released files, excluding itself |

Intended GitHub path: `research/experiments/EQ-PRB-001/v0.5/`. This research artefact does not change the Atlas website or deploy public content.
