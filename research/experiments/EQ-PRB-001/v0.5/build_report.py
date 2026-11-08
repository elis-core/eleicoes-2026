#!/usr/bin/env python3
"""Build deterministic UK-English Markdown/HTML reports from v0.5 JSON outputs."""
from __future__ import annotations
from pathlib import Path
import json
import math
import mistune
from scipy.stats import beta

ROOT=Path(__file__).parent
DATA=json.loads((ROOT/'results_v0.5.json').read_text(encoding='utf-8'))
ROWS=DATA['records']


def lookup(scenario,n_panel,method='paired',n_reference=1800):
    match=[r for r in ROWS if r['scenario']==scenario and r['n_panel']==n_panel and
           r['method']==method and r['n_reference']==n_reference]
    if len(match)!=1: raise AssertionError((scenario,n_panel,method,n_reference,len(match)))
    return match[0]


def perc(v):return f'{v*100:.1f}%'

def proportion_upper_95(k,n):
    if k>=n:return 1.0
    return float(beta.ppf(.95,k+1,n-k))


def main():
    scenarios=['natural_stable','natural_step','H01_D0_offgrid','H11_D0_offgrid',
               'H11_D3_offgrid','H00_biased_panel']
    pretty=['Natural behaviour, stable','Natural step change (no transformation)',
            'Hypothetical H01, fixed rate','Hypothetical H11, fixed rate',
            'Hypothetical H11, site/section variation','Natural step with biased behavioural panel']
    heads=['100','1,000','10,000']
    lines=[]
    def add(x=''):lines.append(x)
    add('# EQ-PRB-001 v0.5 — Independent behavioural panels and off-grid partial identification')
    add('**Date:** 8 November 2026  ')
    add('**Status:** Executed, exploratory; not pre-registered or externally validated  ')
    add('**Scope:** Synthetic paired-round mathematical counts only; UK English')
    add('')
    add('> **Interpretation:** Every transfer rule below is a hypothetical mathematical generator. No real electoral returns, operational evidence, or voting software were analysed. Compatibility or exclusion is conditional on the model and external-panel assumptions, and does not demonstrate that any transformation occurred in practice.')
    add('')
    add('## Executive summary')
    add('')
    add('- Implemented **analytical continuous-amplitude intervals** for the nine H01/H10/H11 × constant/step/logistic equation families, with amplitude **a ∈ [0, 0.60]**, plus the separate exact H00 no-transformation hypothesis. No numerical amplitude grid is used by the interval solver.')
    add('- Generated **20,000 independently seeded synthetic two-round datasets**: six generator scenarios each at three behavioural-panel precisions, plus two additional independent reference-precision experiments, all with 1,000 trials. These worlds were reused within each case for two identification procedures, giving **42 procedure/assumption comparisons**, not 42 independent batches.')
    add('- Preserved **40 polling places (320 sections), five hypothetical municipalities, two rounds, and a 30/10 whole-site training/holdout partition**. Latent before-transformation counts were generated but were not supplied to inference.')
    add('- Compared a **matched independent behavioural panel** against a **finite-sample conservative envelope derived from the same independent samples**. Under favourable matched-panel conditions, H00 can be excluded while 3–6 equation families remain compatible; the true off-grid generator was included in all correctly specified evaluated configurations. The conservative envelope instead retained all ten families throughout this design.')
    add('- Deliberate **panel representativeness failure** caused exclusion of true H00 in all 1,000 high-precision stress trials. This is a model-misspecification failure, not evidence for a transfer.')
    add('')
    add('## 1. Results for the paired-panel procedure')
    add('')
    add('Each row is 1,000 independently generated synthetic datasets; the independent baseline reference has 1,800 draws per section and round. The rate-heterogeneity envelope is multiplicative ±15%. "H00 retained" measures whether zero transformation remains compatible. The true equation family was retained in all properly specified rows of these cases; this does **not** establish universal coverage or unique identification.')
    add('')
    add('| Synthetic generator | Panel draws per section/round | H00 retained | Mean compatible families (of 10) | Mean width of true-family amplitude interval |')
    add('|---|---:|---:|---:|---:|')
    for scenario,name in zip(scenarios,pretty):
        for panel in (100,1000,10000):
            r=lookup(scenario,panel)
            width='n/a' if r['mean_true_family_amplitude_width'] is None else f"{r['mean_true_family_amplitude_width']:.3f}"
            add(f"| {name} | {panel:,} | {perc(r['H00_retained'])} | {r['mean_compatible_families']:.2f} | {width} |")
    add('')
    add('The H00 and nine positive-rate families are **nested at amplitude zero** under the multiplicative model. Therefore ten compatible families under H00 do not represent ten distinct positive-transfer mechanisms. For the H11-D3 generator with 10,000 panel draws, three function families remain compatible, and the mean amplitude interval width is approximately **0.446** of the full 0.600 range. That is partial, not unique, identification.')
    add('')
    add('For the stable H00 and natural-step H00 generators, there were 0 false exclusions across 1,000 trials each at n_panel=10,000. The exact one-sided 95% binomial upper confidence bound for an observed 0/1,000 false-exclusion rate is **'+perc(proportion_upper_95(0,1000))+'**. This is an empirical check within these two synthetic generators, not a general false-alarm certificate. For the invalid biased-panel generator, 1,000/1,000 true H00 models were excluded at the same precision.')
    add('')
    add('## 2. Independent reference precision and alternative constraints')
    add('')
    add('| H11-D3, panel size 10,000 | H00 retained | Mean true-family amplitude width |')
    add('|---|---:|---:|')
    for ref in (75,300,1800):
        r=lookup('H11_D3_offgrid',10000,n_reference=ref)
        add(f"| Independent reference {ref:,} | {perc(r['H00_retained'])} | {r['mean_true_family_amplitude_width']:.3f} |")
    add('')
    r0=lookup('H11_D0_offgrid',10000,'paired_exact_rate')
    r1=lookup('H11_D0_offgrid',10000)
    add(f"For the deterministic-rate H11 generator, assuming the rate is **known to have no location/section heterogeneity** (a valid but stronger constraint for D0 only) reduced the mean compatible amplitude width from **{r1['mean_true_family_amplitude_width']:.3f}** to **{r0['mean_true_family_amplitude_width']:.3f}**. The zero-heterogeneity specification is not valid for D3 and was not scored as though it were.")
    add('')
    add('### Why the conservative envelope remains broad')
    add('')
    add('A separate, distribution-free panel calibration takes the **maximum absolute measured behavioural difference over all 640 section-round positions**, then adds a simultaneous 99% sampling-error allowance. The result is mathematically protective but very conservative:')
    add('')
    add('| Panel draws | Median calibrated envelope for stable natural behaviour | H00 retained under H11-D3 | Mean compatible families |')
    add('|---|---:|---:|---:|')
    for panel in (100,1000,10000):
        r0=lookup('natural_stable',panel,'envelope')
        r=lookup('H11_D3_offgrid',panel,'envelope')
        add(f"| {panel:,} | {r0['median_calibrated_natural_envelope']:.3f} | {perc(r['H00_retained'])} | {r['mean_compatible_families']:.2f} |")
    add('')
    add('The conservative envelope retained **all ten families** in every tested configuration, including the hypothetical transformation cases. Its loss of precision is an important finding: a guaranteed per-cell behavioural envelope can be too wide to identify even a sizeable hypothetical signal. A direct matched-panel adjustment is more informative only under its stronger representativeness and independence premises.')
    add('')
    add('## 3. Mathematical specification')
    add('')
    add('For synthetic section-round index i, the latent blank count is X_B,i, the observed count is Y_B,i, turnout is C_i and a candidate transformation has amplitude a and frozen shape f_i ∈ [0, 1]. For active rounds:')
    add('')
    add('```text')
    add('Y_B,i = X_B,i − floor(alpha_i × X_B,i + 0.5)')
    add('Y_W,i = X_W,i + floor(alpha_i × X_B,i + 0.5)')
    add('alpha_i = a f_i (1 + u_site(i) + v_i),  |u_site(i)| <= 0.10, |v_i| <= 0.05')
    add('```')
    add('')
    add('In H00 or an inactive round, alpha_i=0. Exact integer conservation of all four category counts is checked in every generated dataset. The off-grid generating amplitude is **a = 0.377**, deliberately not one of the v0.4 candidates.')
    add('')
    add('Let p_i be the unknown latent blank probability and q_i the independently sampled baseline blank probability, with p_i, q_i <= 0.20. Let R_i ~ Binomial(n_ref, q_i) be an independent baseline reference, P_i ~ Binomial(n_panel, p_i) an independent *representative* behavioural panel, and Q_i ~ Binomial(n_panel, q_i) a second independent baseline panel. Every sampling draw is independent given the site-level parameters; the site-level parameters themselves may be shared across sections.')
    add('')
    add('The paired correction is Z_i = R_i/n_ref + (P_i−Q_i)/n_panel; conditional on panel representativeness, **E[Z_i] = p_i**. Neither p_i nor latent X_B,i is given to the identification routine.')
    add('')
    add('For each of **four fixed groups** (training/holdout × round), define')
    add('')
    add('```text')
    add('c_g = mean_i[ Z_i − Y_B,i/C_i ]')
    add('k_g = mean_i[ f_i Z_i ]')
    add('u_g = 0.5 × mean_i[1/C_i]')
    add('      + sqrt( log(2×4/0.05) / (2 m_g²) × Σ_i [1/C_i + 1/n_ref + 2/n_panel] )')
    add('h_g = 0.20 × 0.15 × mean_i[f_i]')
    add('```')
    add('')
    add('A candidate family/amplitude passes the group only when **|c_g − a k_g| <= u_g + a h_g**. Both sides are affine in a, so each group produces an interval obtainable through linear half-space intersection. The final compatible interval is the intersection of all four groups and **[0, 0.60]**. H00 is tested separately with amplitude zero and no rate-heterogeneity term.')
    add('')
    add('The rounding term permits a maximum half-count discrepancy per section. The concentration term uses conditional bounded differences of independent category draws and independent panel draws; four group tests share a 5% Bonferroni budget. For a correctly specified off-grid candidate in one of the stated families, the resulting set has a **conditional nominal inclusion guarantee of at least 95%** under those assumptions. This claim applies to the true candidate amplitude, *not* to uniformly correct classification of all other candidate mechanisms.')
    add('')
    add('### Alternative 99%-calibrated behavioural envelope')
    add('')
    add('Without using the measured panel difference as a direct correction, calculate')
    add('')
    add('```text')
    add('epsilon = sqrt( log(4 × 640 / 0.01) / (2 n_panel) )')
    add('d_hat = max over 640 positions |P_i/n_panel − Q_i/n_panel| + 2 epsilon')
    add('```')
    add('')
    add('Under independent representative binomial sampling, a union bound ensures **Pr[d_hat >= max_i |p_i−q_i|] >= 99%**. The envelope procedure uses Z=R/n_ref, substitutes d_hat into the behavioural allowance, and allocates 4% to the four moment tests. The two failure budgets sum to 5%, giving conditional at-least-95% inclusion of the true fixed candidate when *all* premises hold. This envelope is expected to be wide in small/medium panels and is not a recommendation to impose it on real datasets without independent justification.')
    add('')
    add('## 4. Failure modes and evidential requirements')
    add('')
    add('**Independent sampling does not imply representativeness.** The matched panel must sample the same latent behavioural distribution p_i at the same section-round resolution as the source counts. Without such a justified linkage, its precision can produce confidently wrong exclusion results. The deliberately biased-panel stress test samples P from a different distribution; its collapse of H00 coverage is expected and explicitly invalidates the nominal inference claim.')
    add('')
    add('**Site-level dependence matters.** The generator includes common site drift and a separate section component. The four holdout groups contain whole sites: 30 training, 10 held out. The concentration argument conditions on common site-level effects and assumes independent individual category draws and independent survey draws, not unconditional site independence.')
    add('')
    add('**Flexible natural behaviour may be observationally equivalent.** A broad envelope leaves the complete family library compatible. An identified interval can contain multiple functions; a small interval still does not establish causality. Excluding H00 within a restrictive family is not proof that a transformation occurred.')
    add('')
    add('**The synthetic external panel is hypothetical.** The study does not establish that an equivalent independent, representative, sufficiently granular behavioural panel exists for real electoral observations. Such a source, its sampling frame and error structure would have to be independently demonstrated before transferring the method.')
    add('')
    add('## 5. Reproducibility and checks')
    add('')
    add('- Generator seed **20261108**, with independent seed offsets for each of 20 data-generating cases; NumPy PCG64. Fixed 1,000 worlds per case, 20,000 total. The same datasets are reused for paired and envelope procedure comparisons within a case; procedure results should **not** be counted as independent datasets.')
    add('- Standalone Python source (`eq_prb_001_v05.py`), unit/integration tests (`verify_v05.py`), numerical outputs (`results_v0.5.json`, `identified_intervals_summary.csv`, `examples.json`) and execution receipt are distributed with a SHA-256 manifest.')
    add('- The interval solver was compared to a **3,001-point grid** for 1,000 independent test inequalities, with exact agreement; actual inference remains continuous and grid-free.')
    add('- Verified exact integer conservation, panel count bounds, disjoint whole-site holdout, representativeness-failure labels, correct off-grid amplitude inclusion in independent pilot simulations, and full-run result counts.')
    add('- No scientific parameter was adjusted after viewing the final 1,000-world results. Initial prototype and pilot development preceded the frozen full evaluation; therefore this remains **exploratory**, not formally preregistered.')
    add('')
    add('## 6. Recommended v0.6 research direction')
    add('')
    add('Investigate transportable behavioural constraints with *separately located* calibration sites rather than matched sampling at the target sites, and test partial-identification under distribution shift, bounded selection bias and joint confidence across multiple transfer mechanisms. Prioritise diagnostic checks of external-panel representativeness. Do not claim unique identification unless competing families are demonstrably excluded under independently supportable assumptions.')
    add('')
    add('**Bottom line:** Version 0.5 demonstrates that real-valued equation intervals can be computed without discretisation, and that independent, representative behavioural data can narrow compatible families in a controlled synthetic environment. It also demonstrates that representativeness failures can invalidate the conclusion even as survey sample size increases.')
    md='\n'.join(lines)+'\n'
    (ROOT/'RELATORIO_EQ-PRB-001_v0.5.md').write_text(md,encoding='utf-8')
    html=mistune.create_markdown(plugins=['table'])(md)
    html_doc='''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EQ-PRB-001 v0.5 — Off-grid partial identification</title><style>
:root{color-scheme:light}body{font:15px/1.58 system-ui,-apple-system,Segoe UI,sans-serif;max-width:1020px;margin:0 auto;padding:32px;color:#213049;background:#f8fafc}
h1,h2,h3{line-height:1.2;color:#10213c}h1{font-size:30px}h2{padding-top:18px;border-top:1px solid #dce4ee;margin-top:32px}blockquote{border-left:4px solid #d97706;background:#fffbeb;padding:12px 18px;margin:18px 0}
table{border-collapse:collapse;background:white;width:100%;display:block;overflow-x:auto}th,td{border:1px solid #d8e0eb;padding:7px 9px;text-align:left;font-size:13px}th{background:#eaf1fa}tr:nth-child(2n){background:#f3f7fc}pre{overflow:auto;background:#eef3fa;padding:14px;border-radius:8px}code{font-family:ui-monospace,Consolas,monospace}p,li{max-width:100ch}a{color:#1451a0}</style></head><body>'''+html+'</body></html>'
    (ROOT/'RELATORIO_EQ-PRB-001_v0.5.html').write_text(html_doc,encoding='utf-8')
    print(f'Built UK-English Markdown ({len(md):,} characters) and HTML ({len(html_doc):,} characters)')

if __name__=='__main__':main()
