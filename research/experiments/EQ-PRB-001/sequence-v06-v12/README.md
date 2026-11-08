# EQ-PRB-001 v0.6–v0.12 — Sequential synthetic research

**UK English · 8 November 2026 · seven executed milestones**

All displayed counts and candidate transformations are mathematical
simulations. No real Brazilian election returns, electoral-system software,
or operational records have been analysed. Compatibility and exclusions are
conditional on assumptions about behavioural references and site sampling.

| Version | Topic | Key outcome |
|---|---|---|
| v0.6 | Externally located calibration sites | Single-site calibration does not imply 10-site calibration |
| v0.7 | Known-ratio geographic weighting | Improves marginal synthetic coverage, conditional on exact ratios |
| v0.8 | Familywise test correction | 80-site calibration is vacuous; 240 sites can produce finite bounds |
| v0.9 | Natural behavioural shift sensitivity | Unmeasured shift causes spurious exclusion |
| v0.10 | Multiple possible donor categories | Correct synthetic donor remains compatible but not unique |
| v0.11 | Frozen model selection | Training, model choice, calibration and evaluation remain separate |
| v0.12 | Independent synthetic stress audit | **FAIL** under unmeasured natural shift |

## Source and reproducibility

The four shared, frozen source files in `src/` implement each version's
synthetic simulator, analysis, verification and report rendering. The `v0.x/`
folders contain the version-specific results JSON, metrics CSV and HTML/Markdown
technical reports. The self-contained original version ZIPs include copies of
this source, run logs, checksums and generated results; local ZIP artefacts
are provided separately to the user.

From the directory `src/` (Python 3.13; NumPy 2.3.5, Mistune 3.2.1):

```bash
python -m pip install numpy==2.3.5 mistune==3.2.1
OPENBLAS_NUM_THREADS=1 python experiment.py --version v0.12 --output ../v0.12
OPENBLAS_NUM_THREADS=1 python verify.py --version v0.12 --directory ../v0.12
python build_report.py --version v0.12 --directory ../v0.12
```

Replace `v0.12` consistently to regenerate a prior version. Regeneration
replaces repository results files; use a clean clone or separate output folder.

**Release status:** Exploratory, not preregistered or externally validated.
No unique mechanism is identified. The Atlas website is not changed by this PR.
