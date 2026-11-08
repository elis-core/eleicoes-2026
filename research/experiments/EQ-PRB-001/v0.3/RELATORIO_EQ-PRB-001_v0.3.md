# EQ-PRB-001 v0.3 — Behavioural alternatives, reference uncertainty and predictive calibration

**Date:** 8 November 2026  
**Experiment:** EQ-PRB-001  
**Version:** 0.3  
**Status:** Executed; exploratory, **not statistically validated**.  
**Language:** UK English.

> **Synthetic-only research:** No election returns, voting-system logs or real personal data were used. The reported transformations are invented mathematical mechanisms. None of the findings establishes that any such transformation occurred in an election.

## 1. Executive findings

The v0.2 method could distinguish some known synthetic transformations from a narrow natural-behaviour benchmark but raised many alarms when a *natural* change resembled a hypothetical transformation. Version 0.3 investigated this confounding directly and checked the precision of predictive intervals.

The decisive result is **lack of unique mechanistic identification** once sufficiently flexible natural behaviour is admissible. A threshold calibrated on four synthetic natural-behaviour models reduces false alarms but also sharply reduces the ability to detect transformations. In one tested configuration the one-sided 95% upper false-alarm limit exceeds the prescribed 5% bound, and numerous signal configurations fail the 80% detection objective.

The protocol generated **12,000** independent calibration worlds for the four H00 variants, **27,000** independent evaluation worlds and **9,000** separate worlds for prediction-interval calibration: **48,000 synthetic worlds** in all.

## 2. Design and observations

- Five invented municipalities; 40 polling places, eight sections each (320 sections per synthetic two-round dataset).
- Thirty entire polling places for training and ten entire polling places for evaluation, retaining both rounds in the same partition.
- Four generated count categories: W (putative beneficiary), L (other finalist), B (blank) and N (null). All transformations conserve the exact integer turnout total and move only B→W. This deliberately does **not** cover the whole mechanism library envisaged in the wider research specification.
- At fitting time the latent pre-transformation category counts are not available; scoring receives observed synthetic counts and independently simulated reference counts. The *candidate design still knows the true synthetic baseline probability function* q_B, which is a substantial oracle advantage.
- Candidate search: 73 models including H00, H01, H10, H11; two signal shapes, three amplitudes and D0–D3 random-effect structures. A Gaussian multilevel pseudo-predictive score, not an exact count likelihood, is used.
- Competing behavioural baselines: **restricted** (intercept and linear term per round), **quadratic** (adds curvature) and **behavioural envelope** (adds exactly signal-shaped natural preference functions). All are pooled functions; none fits a free coefficient to every section.
- Independent reference sample sizes of 1,800, 300 or 75 observations **per section and round** are artificial experimental conditions, not claims about survey availability.
- Four H00 calibration/evaluation generators: stable natural variation, natural step change, natural logistic change and natural quadratic change; five positive generators: H01-D0, H01-D3, H10-D3, H11-D0 and H11-D3.
- For each reference size: 1,000 independent calibration worlds per H00 generator; 1,000 independent evaluation worlds per generator; and 1,000 further worlds for interval calibration in each of H00-D0, H01-D3 and H11-D3.

## 3. Signal identification versus a composite natural-behaviour null

For each design, a frozen search selects the highest training pseudo-score among all 73 candidates. The evaluation statistic is the held-out pseudo-score improvement of that selected candidate over H00. The **narrow** threshold is the higher-method 97.5th percentile under stable H00 only. The **composite** threshold is the maximum of the separately calibrated 97.5th percentiles under all four H00 generators. Evaluation draws are independent of the draws that determine thresholds.

### 3.1. Detection of a two-round H11-D3 transformation

| Independent reference per section/round | Restricted: narrow H00 | Restricted: composite H00 | Quadratic: composite H00 | Behavioural envelope: composite H00 |
|---:|---:|---:|---:|---:|
| 1,800 | 74.0% | 1.8% | 3.9% | 16.4% |
| 300 | 58.9% | 2.3% | 3.0% | 17.8% |
| 75 | 32.0% | 2.1% | 3.3% | 9.1% |

The composite-null calibration sharply reduces the ability to flag H11-D3, because natural-behaviour generators include a comparable expected shift. A wider behaviour model can absorb the same mean pattern; identifying the generator therefore requires independent restrictions rather than a more complicated curve fit.

### 3.2. False alarms from a natural step change (H00, no transformation)

| Reference | Behavioural model | Narrow H00 alarms | Composite H00 alarms | Composite alarms (out of 1,000) | One-sided 95% upper limit |
|---:|---|---:|---:|---:|---:|
| 1,800 | restricted | 81.4% | 2.9% | 29 | 3.93% |
| 1,800 | quadratic | 73.5% | 4.1% | 41 | 5.29% |
| 1,800 | behavioural-envelope | 0.2% | 0.2% | 2 | 0.63% |
| 300 | restricted | 63.3% | 1.9% | 19 | 2.78% |
| 300 | quadratic | 54.3% | 1.7% | 17 | 2.54% |
| 300 | behavioural-envelope | 1.2% | 1.2% | 12 | 1.94% |
| 75 | restricted | 34.6% | 3.1% | 31 | 4.16% |
| 75 | quadratic | 24.8% | 3.6% | 36 | 4.73% |
| 75 | behavioural-envelope | 2.1% | 2.1% | 21 | 3.01% |

**Pre-specified false-alarm confidence objective not met:** the most demanding tested result is reference n=1,800, quadratic design, natural step: 41/1,000 alarms (empirical 4.1%) with upper bound 5.29% > 5.00%. Although many individual null configurations meet the bound, it is incorrect to report universal calibration success.

**Multiplicity qualification:** the stated upper bounds are individual one-sided 95% binomial bounds; they are not a joint 95% familywise confidence guarantee across the 36 H00 design/precision/generator configurations. Calibration of the adaptive model search is included in the statistic, but does not remove this separate uncertainty.

### 3.3. Consequences for the decision rule

- The 80% target for detection is **not attained consistently**: under composite-null calibration it fails repeatedly, including the H11-D3 restricted example in every reference-size regime.
- A decision of “identified transformation mechanism” is explicitly **withheld**. A positive score can at most indicate departure from one specified natural-behaviour model; if the reference class contains an observationally equivalent process, no score can uniquely label the process.
- D0–D3 are searched as candidates, but the evaluation generators in v0.3 cover D0 and D3 for selected temporal patterns; comprehensive four-way D-structure recovery remains out of scope.

## 4. Split-calibrated prediction intervals

The predictive mean and Gaussian standard deviations are calculated from observed synthetic counts, independent reference counts and training-only coefficients. For each generator and reference precision, a **separate** independent sample of 1,000 synthetic worlds determines empirical standardised-residual quantiles for nominal 50%, 80% and 95% intervals. These cut-offs are subsequently assessed on a disjoint 1,000-world evaluation sample. Four-category 95% joint intervals use the empirical quantile of the per-section maximum standardised error; they are **not** simultaneous over every section in an election.

### 4.1. H11-D3 results — nominal 95% intervals

| Reference n | W coverage: raw → calibrated | B coverage: raw → calibrated | B mean width (pp): raw → calibrated | Four-category joint coverage: raw → calibrated |
|---:|---:|---:|---:|---:|
| 1,800 | 93.1% → 95.0% | 90.4% → 95.0% | 6.72 → 7.93 | 92.6% → 95.0% |
| 300 | 93.7% → 94.8% | 91.6% → 94.9% | 8.08 → 8.96 | 93.6% → 94.9% |
| 75 | 94.5% → 94.9% | 94.9% → 95.1% | 10.84 → 10.90 | 95.4% → 95.0% |

The raw H11-D3 B intervals under-covered at high reference precision. Split calibration corrected coverage within the named synthetic generator, generally by producing wider intervals. At reference n=1,800, mean B interval width grew from 6.72 to 7.93 percentage points. The corresponding four-category joint coverage increased from 92.6% to 95.0%.

**Calibration limitation:** these are empirical rates pooled across held-out section-round predictions. The 1,000 simulation-world replicates are independent but observations within one world share location-level effects. No general distribution-free coverage guarantee, transport guarantee across alternative generators, or simultaneous confidence statement across all sections is claimed.

Results for 50% and 80%, all categories, all evaluated generator types and mean widths are retained in `intervals.csv` and `results_v0.3.json`.

## 5. Mathematical identification limit

Let latent counts satisfy `X ~ Multinomial(C, (p_W,p_L,p_B,p_N))`. In one synthetic mechanism, every B category draw independently changes to W with probability α. After marginalising over the latent counts:

`Y ~ Multinomial(C, (p_W + α p_B, p_L, (1−α) p_B, p_N))`.

In a competing **natural-behaviour-only** model, suppose the actual category probabilities are already `(p_W + α p_B, p_L, (1−α) p_B, p_N)` and no transformation occurs. The two models then have **exactly the same law for all observable category counts Y**, for any C. If the independent baseline reference has the same distribution under both models, it cannot separate them either.

For an illustrative invented probability vector `(0.48, 0.39, 0.09, 0.04)` and α = 0.27, both produce `(0.5043, 0.39, 0.0657, 0.04)` for the observable categories.

This is a proof of **observational equivalence for random independent thinning**, not a claim of exact equality for the v0.2/v0.3 *deterministic half-up rounding* of a fixed number of votes. It establishes a clear boundary for unique identification in the broader probabilistic mechanism family.

## 6. Controls and reproducibility

- Independent random seeds: 20261108 (reference n=1,800), 20261109 (n=300), 20261110 (n=75). NumPy PCG64; fixed generator and model search code.
- Verification script checks exact count conservation, reference multinomial totals, location-disjoint validation, candidate count, numerical Woodbury versus dense covariance score, and zero residual signal under the behavioural envelope when its mean basis contains the candidate signal.
- Generation and selection use only synthetic data. No observed 2026 results enter the programme.
- `model_comparison.csv` contains 81 scored comparisons (3 reference sizes × 3 behavioural baselines × 9 evaluation generators); `results_v0.3.json` also retains 9 interval assessments.

## 7. Constraints on interpretation

1. The modelling task is a mathematical exercise in the behaviour of statistical models. It does not attribute any event to a system, process, person or actor.
2. The candidate B→W transfer is an intentionally limited illustrative component; it does not implement L→W or other-first-round preferences. H00/H01/H10/H11 are *temporal simulation scenarios*, not descriptions of electoral events.
3. q_B, the reference design and the natural-behaviour functional classes are partially shared between the simulator and inference procedure; this remains an **oracle advantage** even though individual latent counts are hidden.
4. Reference samples of 75, 300 and 1,800 per section-round are hypothetical, not descriptions of feasible election surveys.
5. The pseudo-score is Gaussian and does not solve the exact discrete latent-count likelihood in the full methodology.
6. Behavioural changes outside the four tested null generators can produce additional false positives; no exhaustive statement is possible.
7. Because one individual false-alarm upper bound exceeds 5% and power falls short of 80% for many scenarios, **v0.3 must not be designated a validated detection method**.

## 8. Recommended next experiment (v0.4)

Prioritise **partial identification and independent behavioural constraints**, rather than a larger unconstrained equation search:

1. Define explicit external constraints on the latent behaviour baseline and test a graded family from high-information independent reference to weak or biased reference; report *identified sets* of mechanisms rather than a forced single winner.
2. Replace the approximate B-only score with an integer-count predictive likelihood for W/L/B/N and examine how the chosen likelihood changes intervals and rankings.
3. Specify a composite natural-behaviour null more broadly before seeing evaluation outcomes; compute a simultaneous confidence accounting for the ensemble of tested null generators, not merely one-sided bounds per generator.
4. Include transformations and natural effects with the same first two moments but different higher-order dependence; check whether held-out distributional scoring provides real separation.
5. Keep the model search and evaluation locations strictly separated and report no unique attribution when observational equivalence remains.

## 9. File manifest

- `eq_prb_001_v03.py` — self-contained synthetic generator, model search and split interval assessment.
- `run1800/`, `run300/`, `run75/` — raw, independently seeded numerical runs and logs.
- `combine_results.py`, `results_v0.3.json`, `model_comparison.csv`, `intervals.csv` — deterministic compilation of the runs.
- `verify_v03.py` — independent arithmetic, rank and structural checks.
- `build_report.py` — render this report in Markdown and standalone HTML.
- `MANIFEST.sha256` — file integrity manifest (excludes itself).

**Conclusion:** v0.3 establishes a reproducible negative identifiability result alongside improved within-generator predictive calibration. It does not establish a reproducible equation for any real election.
