#!/usr/bin/env python3
"""Create the UK English Markdown and standalone HTML technical reports from JSON."""
from __future__ import annotations
import json,datetime,html
from pathlib import Path
import mistune

ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/'results_v0.3.json').read_text(encoding='utf-8'))

def pick(n,design,h,d='D0',natural='none'):
    hits=[r for r in DATA['scores'] if (r['reference_n'],r['design'],r['generator'],r['D'],r['natural'])==(n,design,h,d,natural)]
    assert len(hits)==1
    return hits[0]

def percent(v):return f'{v*100:.1f}%'
def pp(v):return f'{v:.2f}'
def bound(v):return f'{v*100:.2f}%'

def report():
    out=[]
    def put(*lines):out.extend(lines)
    put('# EQ-PRB-001 v0.3 — Behavioural alternatives, reference uncertainty and predictive calibration',
        '', '**Date:** 8 November 2026  \\n**Experiment:** EQ-PRB-001  \\n**Version:** 0.3  \\n**Status:** Executed; exploratory, **not statistically validated**.  \\n**Language:** UK English.',
        '', '> **Synthetic-only research:** No election returns, voting-system logs or real personal data were used. The reported transformations are invented mathematical mechanisms. None of the findings establishes that any such transformation occurred in an election.',
        '', '## 1. Executive findings',
        '', 'The v0.2 method could distinguish some known synthetic transformations from a narrow natural-behaviour benchmark but raised many alarms when a *natural* change resembled a hypothetical transformation. Version 0.3 investigated this confounding directly and checked the precision of predictive intervals.',
        '', 'The decisive result is **lack of unique mechanistic identification** once sufficiently flexible natural behaviour is admissible. A threshold calibrated on four synthetic natural-behaviour models reduces false alarms but also sharply reduces the ability to detect transformations. In one tested configuration the one-sided 95% upper false-alarm limit exceeds the prescribed 5% bound, and numerous signal configurations fail the 80% detection objective.',
        '', f'The protocol generated **{DATA["independent_calibration_worlds"]:,}** independent calibration worlds for the four H00 variants, **{DATA["independent_evaluation_worlds"]:,}** independent evaluation worlds and **{DATA["independent_interval_calibration_worlds"]:,}** separate worlds for prediction-interval calibration: **{DATA["independent_calibration_worlds"]+DATA["independent_evaluation_worlds"]+DATA["independent_interval_calibration_worlds"]:,} synthetic worlds** in all.',
        '', '## 2. Design and observations',
        '', '- Five invented municipalities; 40 polling places, eight sections each (320 sections per synthetic two-round dataset).',
        '- Thirty entire polling places for training and ten entire polling places for evaluation, retaining both rounds in the same partition.',
        '- Four generated count categories: W (putative beneficiary), L (other finalist), B (blank) and N (null). All transformations conserve the exact integer turnout total and move only B→W. This deliberately does **not** cover the whole mechanism library envisaged in the wider research specification.',
        '- At fitting time the latent pre-transformation category counts are not available; scoring receives observed synthetic counts and independently simulated reference counts. The *candidate design still knows the true synthetic baseline probability function* q_B, which is a substantial oracle advantage.',
        '- Candidate search: 73 models including H00, H01, H10, H11; two signal shapes, three amplitudes and D0–D3 random-effect structures. A Gaussian multilevel pseudo-predictive score, not an exact count likelihood, is used.',
        '- Competing behavioural baselines: **restricted** (intercept and linear term per round), **quadratic** (adds curvature) and **behavioural envelope** (adds exactly signal-shaped natural preference functions). All are pooled functions; none fits a free coefficient to every section.',
        '- Independent reference sample sizes of 1,800, 300 or 75 observations **per section and round** are artificial experimental conditions, not claims about survey availability.',
        '- Four H00 calibration/evaluation generators: stable natural variation, natural step change, natural logistic change and natural quadratic change; five positive generators: H01-D0, H01-D3, H10-D3, H11-D0 and H11-D3.',
        '- For each reference size: 1,000 independent calibration worlds per H00 generator; 1,000 independent evaluation worlds per generator; and 1,000 further worlds for interval calibration in each of H00-D0, H01-D3 and H11-D3.',
        '', '## 3. Signal identification versus a composite natural-behaviour null',
        '', 'For each design, a frozen search selects the highest training pseudo-score among all 73 candidates. The evaluation statistic is the held-out pseudo-score improvement of that selected candidate over H00. The **narrow** threshold is the higher-method 97.5th percentile under stable H00 only. The **composite** threshold is the maximum of the separately calibrated 97.5th percentiles under all four H00 generators. Evaluation draws are independent of the draws that determine thresholds.',
        '', '### 3.1. Detection of a two-round H11-D3 transformation',
        '', '| Independent reference per section/round | Restricted: narrow H00 | Restricted: composite H00 | Quadratic: composite H00 | Behavioural envelope: composite H00 |',
        '|---:|---:|---:|---:|---:|')
    for n in (1800,300,75):
        a=pick(n,'restricted','H11','D3');b=pick(n,'quadratic','H11','D3');c=pick(n,'behavioural-envelope','H11','D3')
        put(f'| {n:,} | {percent(a["false_or_detection_rate_restricted"])} | {percent(a["false_or_detection_rate_composite"])} | {percent(b["false_or_detection_rate_composite"])} | {percent(c["false_or_detection_rate_composite"])} |')
    put('', 'The composite-null calibration sharply reduces the ability to flag H11-D3, because natural-behaviour generators include a comparable expected shift. A wider behaviour model can absorb the same mean pattern; identifying the generator therefore requires independent restrictions rather than a more complicated curve fit.',
        '', '### 3.2. False alarms from a natural step change (H00, no transformation)',
        '', '| Reference | Behavioural model | Narrow H00 alarms | Composite H00 alarms | Composite alarms (out of 1,000) | One-sided 95% upper limit |',
        '|---:|---|---:|---:|---:|---:|')
    for n in (1800,300,75):
        for design in ('restricted','quadratic','behavioural-envelope'):
            a=pick(n,design,'H00',natural='step')
            put(f'| {n:,} | {design} | {percent(a["false_or_detection_rate_restricted"])} | {percent(a["false_or_detection_rate_composite"])} | {a["count_composite"]} | {bound(a["upper_one_sided95_composite_null"])} |')
    worst=DATA['worst_composite_null']
    put('', f'**Pre-specified false-alarm confidence objective not met:** the most demanding tested result is reference n={worst["reference_n"]:,}, quadratic design, natural step: {worst["count_composite"]}/1,000 alarms (empirical {percent(worst["false_or_detection_rate_composite"])}) with upper bound {bound(worst["upper_one_sided95_composite_null"])} > 5.00%. Although many individual null configurations meet the bound, it is incorrect to report universal calibration success.',
        '', '**Multiplicity qualification:** the stated upper bounds are individual one-sided 95% binomial bounds; they are not a joint 95% familywise confidence guarantee across the 36 H00 design/precision/generator configurations. Calibration of the adaptive model search is included in the statistic, but does not remove this separate uncertainty.',
        '', '### 3.3. Consequences for the decision rule',
        '', '- The 80% target for detection is **not attained consistently**: under composite-null calibration it fails repeatedly, including the H11-D3 restricted example in every reference-size regime.',
        '- A decision of “identified transformation mechanism” is explicitly **withheld**. A positive score can at most indicate departure from one specified natural-behaviour model; if the reference class contains an observationally equivalent process, no score can uniquely label the process.',
        '- D0–D3 are searched as candidates, but the evaluation generators in v0.3 cover D0 and D3 for selected temporal patterns; comprehensive four-way D-structure recovery remains out of scope.',
        '', '## 4. Split-calibrated prediction intervals',
        '', 'The predictive mean and Gaussian standard deviations are calculated from observed synthetic counts, independent reference counts and training-only coefficients. For each generator and reference precision, a **separate** independent sample of 1,000 synthetic worlds determines empirical standardised-residual quantiles for nominal 50%, 80% and 95% intervals. These cut-offs are subsequently assessed on a disjoint 1,000-world evaluation sample. Four-category 95% joint intervals use the empirical quantile of the per-section maximum standardised error; they are **not** simultaneous over every section in an election.',
        '', '### 4.1. H11-D3 results — nominal 95% intervals',
        '', '| Reference n | W coverage: raw → calibrated | B coverage: raw → calibrated | B mean width (pp): raw → calibrated | Four-category joint coverage: raw → calibrated |',
        '|---:|---:|---:|---:|---:|')
    for n in (1800,300,75):
        p=next(x for x in DATA['prediction_intervals'] if x['reference_n']==n and x['generator']=='H11')
        a=p['assessment'];W=a['marginal']['95']['W'];B=a['marginal']['95']['B'];joint=a['simultaneous95']
        put(f'| {n:,} | {percent(W["raw"]["coverage"])} → {percent(W["split_calibrated"]["coverage"])} | {percent(B["raw"]["coverage"])} → {percent(B["split_calibrated"]["coverage"])} | {pp(B["raw"]["mean_width_percentage_points"])} → {pp(B["split_calibrated"]["mean_width_percentage_points"])} | {percent(joint["raw_bonferroni"]["joint_coverage"])} → {percent(joint["split_calibrated"]["joint_coverage"])} |')
    put('', 'The raw H11-D3 B intervals under-covered at high reference precision. Split calibration corrected coverage within the named synthetic generator, generally by producing wider intervals. At reference n=1,800, mean B interval width grew from 6.72 to 7.93 percentage points. The corresponding four-category joint coverage increased from 92.6% to 95.0%.',
        '', '**Calibration limitation:** these are empirical rates pooled across held-out section-round predictions. The 1,000 simulation-world replicates are independent but observations within one world share location-level effects. No general distribution-free coverage guarantee, transport guarantee across alternative generators, or simultaneous confidence statement across all sections is claimed.',
        '', 'Results for 50% and 80%, all categories, all evaluated generator types and mean widths are retained in `intervals.csv` and `results_v0.3.json`.',
        '', '## 5. Mathematical identification limit',
        '', 'Let latent counts satisfy `X ~ Multinomial(C, (p_W,p_L,p_B,p_N))`. In one synthetic mechanism, every B category draw independently changes to W with probability α. After marginalising over the latent counts:',
        '', '`Y ~ Multinomial(C, (p_W + α p_B, p_L, (1−α) p_B, p_N))`.',
        '', 'In a competing **natural-behaviour-only** model, suppose the actual category probabilities are already `(p_W + α p_B, p_L, (1−α) p_B, p_N)` and no transformation occurs. The two models then have **exactly the same law for all observable category counts Y**, for any C. If the independent baseline reference has the same distribution under both models, it cannot separate them either.',
        '', 'For an illustrative invented probability vector `(0.48, 0.39, 0.09, 0.04)` and α = 0.27, both produce `(0.5043, 0.39, 0.0657, 0.04)` for the observable categories.',
        '', 'This is a proof of **observational equivalence for random independent thinning**, not a claim of exact equality for the v0.2/v0.3 *deterministic half-up rounding* of a fixed number of votes. It establishes a clear boundary for unique identification in the broader probabilistic mechanism family.',
        '', '## 6. Controls and reproducibility',
        '', '- Independent random seeds: 20261108 (reference n=1,800), 20261109 (n=300), 20261110 (n=75). NumPy PCG64; fixed generator and model search code.',
        '- Verification script checks exact count conservation, reference multinomial totals, location-disjoint validation, candidate count, numerical Woodbury versus dense covariance score, and zero residual signal under the behavioural envelope when its mean basis contains the candidate signal.',
        '- Generation and selection use only synthetic data. No observed 2026 results enter the programme.',
        '- `model_comparison.csv` contains 81 scored comparisons (3 reference sizes × 3 behavioural baselines × 9 evaluation generators); `results_v0.3.json` also retains 9 interval assessments.',
        '', '## 7. Constraints on interpretation',
        '', '1. The modelling task is a mathematical exercise in the behaviour of statistical models. It does not attribute any event to a system, process, person or actor.',
        '2. The candidate B→W transfer is an intentionally limited illustrative component; it does not implement L→W or other-first-round preferences. H00/H01/H10/H11 are *temporal simulation scenarios*, not descriptions of electoral events.',
        '3. q_B, the reference design and the natural-behaviour functional classes are partially shared between the simulator and inference procedure; this remains an **oracle advantage** even though individual latent counts are hidden.',
        '4. Reference samples of 75, 300 and 1,800 per section-round are hypothetical, not descriptions of feasible election surveys.',
        '5. The pseudo-score is Gaussian and does not solve the exact discrete latent-count likelihood in the full methodology.',
        '6. Behavioural changes outside the four tested null generators can produce additional false positives; no exhaustive statement is possible.',
        '7. Because one individual false-alarm upper bound exceeds 5% and power falls short of 80% for many scenarios, **v0.3 must not be designated a validated detection method**.',
        '', '## 8. Recommended next experiment (v0.4)',
        '', 'Prioritise **partial identification and independent behavioural constraints**, rather than a larger unconstrained equation search:',
        '', '1. Define explicit external constraints on the latent behaviour baseline and test a graded family from high-information independent reference to weak or biased reference; report *identified sets* of mechanisms rather than a forced single winner.',
        '2. Replace the approximate B-only score with an integer-count predictive likelihood for W/L/B/N and examine how the chosen likelihood changes intervals and rankings.',
        '3. Specify a composite natural-behaviour null more broadly before seeing evaluation outcomes; compute a simultaneous confidence accounting for the ensemble of tested null generators, not merely one-sided bounds per generator.',
        '4. Include transformations and natural effects with the same first two moments but different higher-order dependence; check whether held-out distributional scoring provides real separation.',
        '5. Keep the model search and evaluation locations strictly separated and report no unique attribution when observational equivalence remains.',
        '', '## 9. File manifest',
        '', '- `eq_prb_001_v03.py` — self-contained synthetic generator, model search and split interval assessment.',
        '- `run1800/`, `run300/`, `run75/` — raw, independently seeded numerical runs and logs.',
        '- `combine_results.py`, `results_v0.3.json`, `model_comparison.csv`, `intervals.csv` — deterministic compilation of the runs.',
        '- `verify_v03.py` — independent arithmetic, rank and structural checks.',
        '- `build_report.py` — render this report in Markdown and standalone HTML.',
        '- `MANIFEST.sha256` — file integrity manifest (excludes itself).',
        '', '**Conclusion:** v0.3 establishes a reproducible negative identifiability result alongside improved within-generator predictive calibration. It does not establish a reproducible equation for any real election.', '')
    return '\n'.join(out).replace('  \\n','  \n')

if __name__=='__main__':
    md=report()
    (ROOT/'RELATORIO_EQ-PRB-001_v0.3.md').write_text(md,encoding='utf-8')
    renderer=mistune.create_markdown(plugins=['table'])
    content=renderer(md)
    css='''
:root{font-family:system-ui,-apple-system,Segoe UI,Arial,sans-serif;color:#17202b;background:#f5f7fa}
body{max-width:1160px;margin:0 auto;padding:36px 42px;line-height:1.57}
main{background:white;border:1px solid #e0e6ed;border-radius:12px;padding:38px 50px;box-shadow:0 3px 12px #1c365610}
h1,h2,h3{color:#16385f;line-height:1.24}h1{font-size:2.0em;border-bottom:2px solid #c1d3e5;padding-bottom:20px}
h2{margin-top:35px;border-top:1px solid #e3e9ef;padding-top:19px}blockquote{border-left:4px solid #a54f3d;background:#faf4f1;margin:18px 0;padding:5px 20px}
table{border-collapse:collapse;display:block;overflow-x:auto;width:100%;font-size:13.5px}
th,td{border:1px solid #dae1e9;padding:9px 10px;vertical-align:top}th{background:#e7eef6;color:#16385f}tr:nth-child(even){background:#f8fafc}
code{font-size:0.92em;background:#eff3f7;padding:1px 4px;border-radius:3px}li{margin:4px 0}
footer{margin-top:27px;color:#607080;font-size:0.85em}@media(max-width:700px){body{padding:0}main{padding:20px;border:0;border-radius:0}}'''
    htmltext='<!DOCTYPE html>\n<html lang="en-GB"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>'
    htmltext+='<title>EQ-PRB-001 v0.3 — Synthetic identification and calibration</title><style>'+css+'</style></head><body><main>'+content+'</main>'
    htmltext+='<footer>EQ-PRB-001 v0.3 · Synthetic-only mathematical experiment · 8 November 2026</footer></body></html>\n'
    (ROOT/'RELATORIO_EQ-PRB-001_v0.3.html').write_text(htmltext,encoding='utf-8')
    print('BUILT:',len(md),'Markdown characters;',len(htmltext),'HTML characters')
