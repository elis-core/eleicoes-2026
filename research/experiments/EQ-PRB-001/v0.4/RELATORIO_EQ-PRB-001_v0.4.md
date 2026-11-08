# EQ-PRB-001 v0.4 — Partial identification under behavioural constraints

**Date:** 8 November 2026  
**Status:** Executed; exploratory statistical experiment, not a uniquely identifying method.  
**Language:** UK English  
**Scope:** 100% synthetic paired-round category-count data; no actual election returns, voting-system evidence or personal data.

> **Interpretation guardrail:** Every transformation described here is an invented mathematical scenario. The experiment does not establish that any transformation happened in a real election. A compatible equation is not proof of a causal mechanism.

## 1. Executive findings

Version 0.3 showed that a sufficiently flexible natural-behaviour model could absorb the same average shift as a proposed count transformation. Version 0.4 therefore **returns sets of compatible equations**, rather than choosing a single putative generator. A candidate is retained only when it passes four pre-specified moment inequalities under stated bounds on natural behaviour and rate heterogeneity.

After a small exploratory pilot, the final parameter grid was frozen; the subsequent evaluation generated **21,000 independent synthetic datasets** (seven generators × three independently seeded reference-precision conditions × 1,000 datasets), evaluated **64 candidate equations** and **126** constraint combinations. There are five invented municipalities, 40 sites and eight sections at each site, in two rounds: 30 complete sites are used for training and 10 complete sites remain held out, preserving both rounds together. For the study's frozen candidate-grid cases, the correct candidate was retained in **all 93 correctly specified evaluation configurations**; these 100% empirical inclusion rates are deliberately conservative and are not a universal coverage guarantee.

**Main negative result:** when the independently justified natural-behaviour envelope is broad enough to accommodate alternative natural explanations, a hypothetical transformation and the no-transformation scenario usually remain jointly compatible. Under the broadest envelope, all 64 candidates survive in every assessed H11-D3 configuration. **Unique identification has not been attained.**

## 2. Tight-envelope sensitivity: detection versus misinterpretation

The following results use a natural-behaviour envelope of **±0.25 percentage points** in the underlying blank-category probability and allow a transformation-rate deviation of **±0.055** on active rounds. Both figures are *assumed bounds* for the simulation, not measured facts. The rate bound covers the bounded D3 location-plus-section variation generated here. Each percentage uses **1,000 independent synthetic trials**.

| Independent reference size | H00 exclusion: synthetic H11-D3 | Mean identified-set size | H00 exclusion: synthetic natural step | H00 exclusion: biased reference |
|---:|---:|---:|---:|---:|
| 1,800 | 100.0% | 21.0/64 | 100.0% | 100.0% |
| 300 | 98.3% | 26.6/64 | 98.0% | 97.7% |
| 75 | 7.2% | 62.4/64 | 8.2% | 9.2% |


The apparent detection of a natural step change (H00) or a biased independent reference is a **model-misspecification failure**, not a valid demonstration of a transformation: neither generator satisfies the tight behavioural-envelope premise. Under these cases, excluding H00 is scientifically misleading. At reference size 1,800 the H11-D3 setting excludes H00 in all 1,000 trials but still retains an average **21.0 distinct equations out of 64**; the result is therefore not uniquely identified even in the favourable regime.

## 3. Graded behavioural constraints and reference precision

The natural-envelope levels are 0.25, 1.00 and 3.50 percentage points, frozen for the final evaluation after pilot design. The exploratory pilot means this study is not a formally preregistered confirmatory experiment. The smallest is correct for the constructed stable-behaviour generators (bounded site variation ±0.15 pp and section variation ±0.10 pp); it is **not** correct for the deliberately misspecified natural-step and reference-bias stress tests. The largest also covers those stress-test generators. The independent reference sample sizes (75, 300 and 1,800 per section/round) are mathematical counterfactuals, not assertions about practical field surveys.

| Reference | Natural envelope (percentage points) | H00 retained with H11-D3 | Mean compatible equations | H00 retained under natural-step H00 |
|---:|---:|---:|---:|---:|
| 1,800 | 0.25 | 0.0% | 21.0/64 | 0.0% |
| 1,800 | 1.00 | 100.0% | 64.0/64 | 100.0% |
| 1,800 | 3.50 | 100.0% | 64.0/64 | 100.0% |
| 300 | 0.25 | 1.7% | 26.6/64 | 2.0% |
| 300 | 1.00 | 100.0% | 64.0/64 | 100.0% |
| 300 | 3.50 | 100.0% | 64.0/64 | 100.0% |
| 75 | 0.25 | 92.8% | 62.4/64 | 91.8% |
| 75 | 1.00 | 100.0% | 64.0/64 | 100.0% |
| 75 | 3.50 | 100.0% | 64.0/64 | 100.0% |


The wide envelope yields **the complete 64-model library** for the H11-D3 example at each precision. This is the central partial-identification result: in that regime the data and declared bounds permit the no-transformation rule, multiple temporal patterns and multiple rate shapes. More reference observations alone cannot resolve this overlap without stronger and externally justified restrictions on behaviour.

In contrast, under valid narrow bounds, the no-transformation rule can be excluded at high precision without selecting a unique temporal pattern or curve. A statistical confidence set describes **compatibility conditional on assumptions**; its size does not measure the probability that a particular candidate is true.

## 4. Mathematical definition of the identified set

For synthetic section-round index \(i\), let \(C_i\) be observed turnout, \(X_{B,i}\) the latent count in category B, \(Y_{B,i}\) the published synthetic B count, and \(R_{B,i}\) an independent reference count based on \(n\) draws. The discrete transformation is

\[
Y_{B,i}=X_{B,i}-\left\lfloor\alpha_i X_{B,i}+\tfrac12\right\rfloor,\qquad
Y_{W,i}=X_{W,i}+\left\lfloor\alpha_i X_{B,i}+\tfrac12\right\rfloor.
\]

Other categories remain unchanged, and **all four integer counts sum exactly to \(C_i\)**. The candidate grid freezes \(\alpha_i(\theta)=a f(z_i)\mathbf{1}[\mathrm{round}(i)\in H]\) before simulation. It includes H00 (zero), H01, H10 and H11; constant, step and logistic shapes; and seven amplitudes 0.06 to 0.42, giving 64 candidates including H00.

The behavioural and reference assumptions are

\[
X_{B,i}\mid p_i\sim\operatorname{Binomial}(C_i,p_i),\quad
R_{B,i}\sim\operatorname{Binomial}(n,q_i),\quad
|p_i-q_i|\le d,\quad q_i\le0.20.
\]

For active rounds, the realised rate differs from the candidate curve by at most \(e\), and zero is required on inactive rounds. In particular, **the latent count \(X_B\), the true reference probability \(q\) and the simulated random effects are not supplied to the identification routine**. Only synthetic observations \(Y\), independent reference counts \(R\), turnout, site/round identifiers and frozen candidate covariates are available.

For each of four groups (training round 1 and 2, held-out round 1 and 2), with \(m_g\) sections, invert the statistic

\[
T_g(\theta)=\frac1{m_g}\sum_{i\in g}
\left[(1-\alpha_i(\theta))\frac{R_{B,i}}{n}-\frac{Y_{B,i}}{C_i}\right].
\]

Candidate \(\theta\) survives only if \(|T_g(\theta)|\le U_g(\theta)\) in **all four groups**, where

\[
\begin{aligned}
U_g(\theta)=&\ d\,\overline{(1-\alpha(\theta))}_g
+0.20\,e\,\overline{I_{\rm active}}_g
+\frac{1}{2m_g}\sum_{i\in g}\frac1{C_i}\\
&+\sqrt{\frac{\log(2\cdot4/0.05)}{2m_g^2}\sum_{i\in g}
\left[\frac{(1-\alpha_i(\theta))^2}{n}+\frac1{C_i}\right]}.
\end{aligned}
\]

The first two terms cover bounded unknown natural preferences and bounded rate heterogeneity; the third covers deterministic half-up rounding (at most half a count per section); the last is a conditional bounded-differences concentration radius for independent category draws and reference draws. Within-site dependencies are allowed through shared **bounded effects**, while the individual draws are conditionally independent. The four-test Bonferroni allocation provides a **minimum 95% inclusion probability for a true *on-grid* candidate when all assumptions hold**, not a confidence guarantee for every off-grid equation or for arbitrary natural behaviours.

There is deliberately **no multiplication by 64 in the test threshold**: a confidence set is obtained by inverting valid tests for each fixed candidate, so inclusion of the *true* candidate does not depend on the total number tested. Four separate group inequalities *do* require multiplicity control for the advertised full-set coverage. Group holdouts are used both to prevent location leakage and to report training-only versus fully refined set sizes.

## 5. Exact integer-count likelihood diagnostic

The procedure independently implements the **exact four-category observation likelihood**, conditional on fixed latent category probabilities \(p=(p_W,p_L,p_B,p_N)\) and a fixed deterministic half-up rate \(\alpha\). It sums multinomial probabilities over *all compatible latent B counts*:

\[
\Pr(Y=y\mid p,\alpha)=\sum_{x_B:\ x_B-\lfloor\alpha x_B+\frac12\rfloor=y_B}
\frac{C!}{x_W!x_L!x_B!x_N!}\prod_{k\in\{W,L,B,N\}}p_k^{x_k},
\]

where \(x_L=y_L\), \(x_N=y_N\), \(x_W=y_W-(x_B-y_B)\) and all latent counts must be non-negative. Independent tests exhaustively enumerate all reported outcomes for counts 1–7 across six rates and verify that their likelihoods sum to **1.0000000000** within numerical tolerance.

A restricted 120-world **oracle diagnostic**, on 10 held-out sites (160 section-round observations per world), compares a deterministic H11 step-rate generator with a natural-only multinomial whose **first-order means** are matched, ignoring a rounding error of up to half a count. Because the scorer is intentionally given the *true latent source probabilities*, this is an **upper-bound illustration** rather than a procedure available for observed unknown-source data.

| Actual synthetic generator | Mean log-likelihood gain: rounded minus natural | Worlds preferring rounded model |
|---|---:|---:|
| Deterministic half-up transformation | +8.90 | 98.3% (118/120) |
| Natural-only first-order match | -10.07 | 0.8% (1/120) |

This does **not** prove that distributions can be uniquely separated once baseline behaviour, higher-order dependence and reference bias are unknown. The two alternatives do not have identical second moments by design. A distinct *stochastic independent thinning* mechanism is exactly observationally equivalent to a suitably changed natural multinomial, as established in v0.3; that equivalence must not be extrapolated to deterministic rounding.

## 6. Validation, interpretation and unresolved issues

- **Accounting:** all observed W, L, B and N synthetic counts are non-negative integers and sum to turnout for each section and round.
- **Partition:** 30 training and 10 held-out sites are disjoint; both rounds of a site stay in the same partition.
- **Frozen final protocol, not formal preregistration:** 64 candidate functions and the three behavioural bounds were fixed before the final 21,000-world evaluation, following exploratory pilot development; no section-specific parameter is fitted after observing those evaluation outcomes.
- **Reference data:** independently generated multinomial counts; source probabilities and source latent counts do not enter confidence-set inference.
- **Confidence qualification:** 93 tested configurations satisfy their stated generator bounds; all retained the exact true on-grid candidate across 1,000 trials each. This does *not* validate assumptions outside the constructed simulation family.
- **Mis-specification:** narrow-envelope alarms under natural-step changes or reference bias are **invalid inferences**, explicitly labelled in `identified_sets.csv`.
- **Rate dependence:** the inequalities allow bounded rate variation on active rounds, but **cannot recover whether that variation is shared by site or independent by section**. More structural data are needed.
- **Other transfer flows:** only a hypothetical B→W component was simulated. L→W, N→W and first-round eliminated-candidate flow were not implemented in v0.4.
- **No unique attribution:** a compatible set, particularly one containing H00, cannot identify a transformation, its origin or any real-world event.
- **No continuous-grid guarantee:** the correct generating amplitudes and functions deliberately occur on the fixed grid; off-grid uncertainty requires a new coverage treatment.
- **No full probabilistic posterior:** this is finite-sample confidence-set inversion for a restricted count component, not posterior inference of the entire four-count latent process.
- **No higher-order moment-matched simulation:** the exact likelihood example matches first-order expectations only. Matching higher-order dependence while allowing behavioural nuisance remains further research.

## 7. Recommended v0.5 decision

Do not enlarge the equation library until **external behavioural constraints** can be justified independently of the target outcomes. A useful v0.5 would derive and validate behavioural-envelope assumptions from a genuinely independent source, propagate source bias and model uncertainty, extend the integer-count construction to additional donor components, and report off-grid robust identified sets. If the necessary restrictions cannot be established, report the compatibility set as wide or unidentified; do not select an equation by convenience.

## 8. Files and reproduction

| Component | Role |
|---|---|
| `eq_prb_001_v04.py` | Synthetic generation, frozen candidate library, confidence-set inversion and exact four-count likelihood |
| `verify_v04.py` | Conservation, disjoint sites, exact small-count likelihood normalisation and mathematical checks |
| `results_v0.4.json` | Reproducible aggregate results, assumptions, seeds, candidate definitions and oracle diagnostic |
| `identified_sets.csv` | All 126 evaluated scenarios, including misspecification flags |
| `examples.json` | Example candidate sets under selected conditions, with the four moment bounds |
| `execution.log` | Full execution receipt |
| `build_report.py` | This report generator |
| `RELATORIO_EQ-PRB-001_v0.4.md` | Editable UK-English research report |
| `RELATORIO_EQ-PRB-001_v0.4.html` | Standalone HTML report |
| `MANIFEST.sha256` | SHA-256 integrity check of released files (excluding the manifest itself) |


Reproduce with Python, NumPy and SciPy (and Mistune for HTML rendering):

```bash
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python eq_prb_001_v04.py --seed 20261108 --replicates 1000 --reference-sizes 1800 300 75 --out . > execution.log
OPENBLAS_NUM_THREADS=1 python verify_v04.py
python build_report.py
sha256sum -c MANIFEST.sha256
```

For an integrity check of the **released, unchanged artefacts**, run `sha256sum -c MANIFEST.sha256` **before** re-running the simulation: regeneration overwrites derived files, and results may differ between dependency versions. `MANIFEST.sha256` excludes itself and the ZIP, preventing cyclic hashes. The scripts and results are versioned together under `research/experiments/EQ-PRB-001/v0.4/`.

**Conclusion:** v0.4 successfully implements partial identification under explicit, testable synthetic assumptions and demonstrates that identification contracts or collapses as those assumptions change. It does **not** produce a uniquely identified equation for any observed election.
