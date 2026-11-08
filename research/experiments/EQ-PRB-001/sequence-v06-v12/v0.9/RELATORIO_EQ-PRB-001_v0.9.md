# EQ-PRB-001 v0.9 — Sensitivity to unmeasured shifts and external-panel bias
**Date:** 8 November 2026  
**Status:** Executed synthetic study; exploratory and not externally validated  
**Language:** UK English  
**Data provenance:** 100% synthetic mathematical counts. No observed electoral returns, operational records or software were analysed.

## 1. Research objective

**Main question.** What happens if the target's natural blank-vote probability differs systematically from its independently located donor reference?
An externally stipulated absolute bound `delta` is added to the identification tolerance. The four pre-specified bounds are 0, 0.005, 0.015 and 0.025, while a target natural shift of -0.015 is generated without any transformation.
**Scope restriction.** The sensitivity bounds are assumed, not learned from target outcomes. Inflating a bound protects compatibility but does not establish that its numerical value is justified in an external application.

## 2. Design and frozen calculation
The generator creates two rounds of integer W/L/B/N counts, eight sections per simulated site, and disjoint training, calibration and target sites. A latent transfer is an explicitly hypothetical generator, not an inference about observed voting.
\[m_{s,t,j}=\lfloor a\, f(x_s,t)(1+u_s+v_{s,t,j}) X_{D,s,t,j} + 0.5\rfloor,\qquad a=0.377\text{ in positive synthetic generators}.\]

The receiving category W increases by exactly `m`; donor category D decreases by `m`. All other counts and turnout remain unchanged. The generator alone can access the latent `X`, while the identification routine receives only donor-site reference panels, observable counts and site covariates.

An ex-ante behavioural regression is fitted on independent training-site panels. Site-level conformal calibration uses the maximum of the absolute residuals across both rounds. Each candidate off-grid amplitude `a in [0, 0.60]` must satisfy the affine constraints

`|p_hat - Y_D/C - a*f*p_hat| <= q_site + delta + 4/C_site + a*(0.22*0.15*f)`

where `q_site` is calibrated at donor sites, `delta` is an externally set sensitivity allowance, and `4/C_site` bounds eight integer roundings of at most half a vote apiece. The candidate amplitude interval is the exact algebraic intersection of those affine inequalities; the probabilistic model that motivates the inequalities is an approximation.

**Validity:** split-conformal marginal H00 coverage requires site exchangeability (or, for weighted conformal, an exact density ratio and invariant conditional distribution). No unconditional coverage theorem is asserted for the positive-transfer confidence sets. All positive-amplitude inclusion rates below are empirical.

## 3. Executed results
12 procedure/condition rows from **1,000 independently seeded worlds per distinct generator configuration**. Rows comparing methods or sensitivity bounds reuse the same worlds and must not be counted as additional independent datasets.

| Configuration | Method | H00 retained/site | H00 retained/all 10 | Compatible families/site | True amplitude covered/site |
|---|---|---:|---:|---:|---:|
| H00: actual natural shift -0.015; allowed 0.000 | site_joint_plus_sensitivity | 79.4% | 12.3% | 9.08 | —% |
| H00: actual natural shift -0.015; allowed 0.005 | site_joint_plus_sensitivity | 90.7% | 40.2% | 9.64 | —% |
| H00: actual natural shift -0.015; allowed 0.015 | site_joint_plus_sensitivity | 99.2% | 92.6% | 9.97 | —% |
| H00: actual natural shift -0.015; allowed 0.025 | site_joint_plus_sensitivity | 100.0% | 99.9% | 10.00 | —% |
| H11_B: actual natural shift -0.015; allowed 0.000 | site_joint_plus_sensitivity | 49.0% | 0.1% | 6.68 | 99.6% |
| H11_B: actual natural shift -0.015; allowed 0.005 | site_joint_plus_sensitivity | 54.4% | 0.3% | 6.88 | 100.0% |
| H11_B: actual natural shift -0.015; allowed 0.015 | site_joint_plus_sensitivity | 56.9% | 0.3% | 7.14 | 100.0% |
| H11_B: actual natural shift -0.015; allowed 0.025 | site_joint_plus_sensitivity | 70.8% | 3.7% | 8.57 | 100.0% |
| H00: actual natural shift +0.000; allowed 0.000 | site_joint_plus_sensitivity | 95.1% | 61.0% | 9.72 | —% |
| H00: actual natural shift +0.000; allowed 0.005 | site_joint_plus_sensitivity | 98.7% | 88.0% | 9.93 | —% |
| H00: actual natural shift +0.000; allowed 0.015 | site_joint_plus_sensitivity | 100.0% | 99.6% | 10.00 | —% |
| H00: actual natural shift +0.000; allowed 0.025 | site_joint_plus_sensitivity | 100.0% | 100.0% | 10.00 | —% |

The H00 column is **retention**, not evidence of the absence or presence of a transformation. Under an H00 generator, its complement measures a false exclusion; under an H11 generator, it measures a degree of discrimination. All-ten-site retention must not be confused with the nominal 95% per-site calibration.

## 4. Version-specific interpretation
- Under a -0.015 natural shift, H00 per-site retention was **79.4%** with no allowance, and **99.2%** with an assumed 0.015 allowance.
- Widening the allowance to 0.025 increased retention to **100.0%**, but the mean number of compatible families moved towards all ten.
- The accuracy of an assumed shift bound is the central unresolved external-data condition.

## 5. Reproducibility and scientific limitations
- The first 80 sites are for model training, a distinct set is used for conformity calibration, and the final ten sites are held out. In v0.11/v0.12, a further 40 of the labelled calibration sites are reserved for frozen model selection before a separate 80-site calibration.
- Exact four-category count conservation and non-negative integers are asserted on every generated dataset; the source code contains explicit checks.
- One thousand independent Monte Carlo worlds are generated per scenario; method comparisons on the same worlds are paired experiments, not separate replicates.
- All candidate equations and behavioural models are deliberately limited. No universal recovery, uniquely identified mechanism, or real-data fraud diagnostic is claimed.
- Version design and parameters were refined during an exploratory synthetic series; the programmes were not independently preregistered or audited.
- A nominal per-site conformal result does not extend automatically to familywise tests, transported populations or positive-rate confidence sets.

## 6. Reproduction
Python 3.13 and NumPy 2.3.5 were used. Commands from the release directory:
```bash
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python experiment.py --version v0.9 --output . > execution.log
OPENBLAS_NUM_THREADS=1 python verify.py --version v0.9 --directory . > verify.log
python build_report.py --version v0.9 --directory .
sha256sum -c MANIFEST.sha256
```
Re-running replaces generated results and logs. Run `sha256sum -c MANIFEST.sha256` **before** regeneration to verify the released originals. The reports are UK English.

## 7. Next research decision
**v0.9 is an executed synthetic research milestone, not a conclusion about actual election outcomes.**
