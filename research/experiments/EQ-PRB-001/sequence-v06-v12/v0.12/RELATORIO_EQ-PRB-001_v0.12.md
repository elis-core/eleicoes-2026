# EQ-PRB-001 v0.12 — Independent stress-matrix readiness audit
**Date:** 8 November 2026  
**Status:** Executed synthetic study; exploratory and not externally validated  
**Language:** UK English  
**Data provenance:** 100% synthetic mathematical counts. No observed electoral returns, operational records or software were analysed.

## 1. Research objective

**Main question.** Does the frozen v0.11 selection scheme, combined with an externally assumed 0.015 absolute natural-shift allowance, satisfy the pre-defined false-alarm and power objectives on fresh synthetic random seeds?
The six stress scenarios include representative H00, known geographical H00 shift, unmeasured natural H00 shift, deterministic H11, heterogeneous H11 and geographically shifted H11. The audit calculates the one-sided 95% Wilson upper bound on false alarms in 1,000 independent worlds.
**Scope restriction.** This audit is independent by random seed, not by research team or data-generating programme. The workflow was developed during earlier synthetic pilots and is not preregistered; its performance is not established on actual elections.

## 2. Design and frozen calculation
The generator creates two rounds of integer W/L/B/N counts, eight sections per simulated site, and disjoint training, calibration and target sites. A latent transfer is an explicitly hypothetical generator, not an inference about observed voting.
\[m_{s,t,j}=\lfloor a\, f(x_s,t)(1+u_s+v_{s,t,j}) X_{D,s,t,j} + 0.5\rfloor,\qquad a=0.377\text{ in positive synthetic generators}.\]

The receiving category W increases by exactly `m`; donor category D decreases by `m`. All other counts and turnout remain unchanged. The generator alone can access the latent `X`, while the identification routine receives only donor-site reference panels, observable counts and site covariates.

An ex-ante behavioural regression is fitted on independent training-site panels. Site-level conformal calibration uses the maximum of the absolute residuals across both rounds. Each candidate off-grid amplitude `a in [0, 0.60]` must satisfy the affine constraints

`|p_hat - Y_D/C - a*f*p_hat| <= q_site + delta + 4/C_site + a*(0.22*0.15*f)`

where `q_site` is calibrated at donor sites, `delta` is an externally set sensitivity allowance, and `4/C_site` bounds eight integer roundings of at most half a vote apiece. The candidate amplitude interval is the exact algebraic intersection of those affine inequalities; the probabilistic model that motivates the inequalities is an approximation.

**Validity:** split-conformal marginal H00 coverage requires site exchangeability (or, for weighted conformal, an exact density ratio and invariant conditional distribution). No unconditional coverage theorem is asserted for the positive-transfer confidence sets. All positive-amplitude inclusion rates below are empirical.

## 3. Executed results
6 procedure/condition rows from **1,000 independently seeded worlds per distinct generator configuration**. Rows comparing methods or sensitivity bounds reuse the same worlds and must not be counted as additional independent datasets.

| Generator condition | H00 retained/site | H00 retained/all 10 | False-alarm upper 95% | Readiness decision |
|---|---:|---:|---:|---|
| H00 representative | 100.0% | 99.8% | 0.6% | PASS |
| H00 known covariate shift | 100.0% | 99.9% | 0.4% | PASS |
| H00 unmeasured natural shift | 99.2% | 92.3% | 9.2% | FAIL |
| H11 fixed rate | 69.3% | 4.3% | —% | PASS |
| H11 site+section heterogeneity | 69.4% | 4.3% | —% | PASS |
| H11 with known geographic shift | 55.1% | 0.7% | —% | PASS |

The H00 column is **retention**, not evidence of the absence or presence of a transformation. Under an H00 generator, its complement measures a false exclusion; under an H11 generator, it measures a degree of discrimination. All-ten-site retention must not be confused with the nominal 95% per-site calibration.

## 4. Version-specific interpretation
- The representative and covariate-shifted H00 cases passed their 5% upper-bound checks, but the unmeasured-shift H00 case **FAILED**, with upper bound **9.20%**.
- The three H11 tests met the stipulated detection and synthetic true-family coverage rules, but a pass in positive generators does not cancel a failed false-alarm criterion.
**Overall readiness: FAIL.** No broad statement of statistical validation is justified.

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
OPENBLAS_NUM_THREADS=1 python experiment.py --version v0.12 --output . > execution.log
OPENBLAS_NUM_THREADS=1 python verify.py --version v0.12 --directory . > verify.log
python build_report.py --version v0.12 --directory .
sha256sum -c MANIFEST.sha256
```
Re-running replaces generated results and logs. Run `sha256sum -c MANIFEST.sha256` **before** regeneration to verify the released originals. The reports are UK English.

## 7. Next research decision
**v0.12 is an executed synthetic research milestone, not a conclusion about actual election outcomes.**
