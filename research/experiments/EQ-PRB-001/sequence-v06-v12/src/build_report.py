#!/usr/bin/env python3
"""Generate consistent UK-English static research reports from executed JSON results."""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
import mistune

STAGES={
'v0.6':("Independent calibration sites and geographic transport",[
    "**Main question.** Can a behavioural reference learned at distinct synthetic sites be transported to ten held-out sites without accessing their latent pre-transformation counts?",
    "The baseline with source/target exchangeability retained H00 at approximately 95% of individual sites but far less often across all ten. A natural change at target sites without a corresponding donor-site change creates spurious exclusions.",
    "**Scope restriction.** 'External' means a different set of synthetic sites, not an actual independent field survey. The source/calibration populations are programmed rather than empirically justified."
]),
'v0.7':("Known-density-ratio covariate-shift adjustment",[
    "**Main question.** Does weighting donor calibration residuals by a *known* geographical density ratio improve marginal coverage for a different target distribution?",
    "The source covariate has density Uniform[-1,1]; the shifted target has density proportional to `1 + 0.8 x` relative to that source. The weighted method inserts an additional infinity atom for the test-site weight, as required by split weighted conformal scoring.",
    "**Scope restriction.** The density ratio is given by the synthetic generator; it is not estimated or externally verified. Conditional invariance of the outcome given x is a crucial premise. Weighted marginal coverage does not give simultaneous coverage of ten sites."
]),
'v0.8':("Simultaneous coverage and finite calibration resolution",[
    "**Main question.** Can the nominal 95% site-level procedure support a 95% joint statement across ten independently evaluated sites?",
    "Bonferroni allocates `alpha/10=0.005` to each site, producing an infinite split-conformal threshold when only 80 calibration sites are available: `ceil((80+1)*(1-.005))=81>80`. With 240 calibration sites, the correction becomes finite, but less discriminating.",
    "**Scope restriction.** The Bonferroni bound applies to no-transformation site-level exchangeable score tests; positive-amplitude interval coverage still relies on an approximate moment model and is verified empirically."
]),
'v0.9':("Sensitivity to unmeasured shifts and external-panel bias",[
    "**Main question.** What happens if the target's natural blank-vote probability differs systematically from its independently located donor reference?",
    "An externally stipulated absolute bound `delta` is added to the identification tolerance. The four pre-specified bounds are 0, 0.005, 0.015 and 0.025, while a target natural shift of -0.015 is generated without any transformation.",
    "**Scope restriction.** The sensitivity bounds are assumed, not learned from target outcomes. Inflating a bound protects compatibility but does not establish that its numerical value is justified in an external application."
]),
'v0.10':("Competing donor-flow categories",[
    "**Main question.** Can the same synthetic equations distinguish transferring rounded counts from blank, null, and another valid-vote category to a fixed beneficiary?",
    "The three donor-category panels are independently sampled; each donor category is calibrated with `alpha/3`, to account for three tested categories within one site. The receiver's count follows exactly from the integer accounting identity.",
    "**Scope restriction.** Category identification is not equivalent to identifying software, intent or real-world behaviour. Site-level retained rates are not ten-site simultaneous confidence guarantees."
]),
'v0.11':("Frozen specification and independent validation split",[
    "**Main question.** Can selection between two behavioural models be made without inspecting target outcomes or using the same donor sites for both selection and calibration?",
    "The method trains on 80 sites, selects the model on 40 further donor validation sites, calibrates on a different 80 sites, then evaluates ten target sites. It explicitly verifies that deleting all target outcomes leaves the selected model unchanged.",
    "**Scope restriction.** A correct non-leakage split prevents one form of overfitting but does not guarantee transportability, familywise coverage or mechanism uniqueness. Selection performance is assessed against pre-specified fixed-model comparators."
]),
'v0.12':("Independent stress-matrix readiness audit",[
    "**Main question.** Does the frozen v0.11 selection scheme, combined with an externally assumed 0.015 absolute natural-shift allowance, satisfy the pre-defined false-alarm and power objectives on fresh synthetic random seeds?",
    "The six stress scenarios include representative H00, known geographical H00 shift, unmeasured natural H00 shift, deterministic H11, heterogeneous H11 and geographically shifted H11. The audit calculates the one-sided 95% Wilson upper bound on false alarms in 1,000 independent worlds.",
    "**Scope restriction.** This audit is independent by random seed, not by research team or data-generating programme. The workflow was developed during earlier synthetic pilots and is not preregistered; its performance is not established on actual elections."
]),
}


def fmt(x,d=1):
    if x is None:return '—'
    if isinstance(x,bool):return 'PASS' if x else 'FAIL'
    if isinstance(x,(int,float)):return f'{x:,.{d}f}'
    return str(x).replace('|','/')


def build(version,directory):
    p=Path(directory);d=json.loads((p/'results.json').read_text());r=d['results']
    title,insights=STAGES[version]
    out=[f'# EQ-PRB-001 {version} — {title}',
         '**Date:** 8 November 2026  ',
         '**Status:** Executed synthetic study; exploratory and not externally validated  ',
         '**Language:** UK English  ',
         '**Data provenance:** 100% synthetic mathematical counts. No observed electoral returns, operational records or software were analysed.',
         '', '## 1. Research objective', *['',*insights],
         '', '## 2. Design and frozen calculation',
         'The generator creates two rounds of integer W/L/B/N counts, eight sections per simulated site, and disjoint training, calibration and target sites. A latent transfer is an explicitly hypothetical generator, not an inference about observed voting.',
         '\\[m_{s,t,j}=\\lfloor a\\, f(x_s,t)(1+u_s+v_{s,t,j}) X_{D,s,t,j} + 0.5\\rfloor,\\qquad a=0.377\\text{ in positive synthetic generators}.\\]',
         '', 'The receiving category W increases by exactly `m`; donor category D decreases by `m`. All other counts and turnout remain unchanged. The generator alone can access the latent `X`, while the identification routine receives only donor-site reference panels, observable counts and site covariates.',
         '', 'An ex-ante behavioural regression is fitted on independent training-site panels. Site-level conformal calibration uses the maximum of the absolute residuals across both rounds. Each candidate off-grid amplitude `a in [0, 0.60]` must satisfy the affine constraints',
         '', '`|p_hat - Y_D/C - a*f*p_hat| <= q_site + delta + 4/C_site + a*(0.22*0.15*f)`',
         '', 'where `q_site` is calibrated at donor sites, `delta` is an externally set sensitivity allowance, and `4/C_site` bounds eight integer roundings of at most half a vote apiece. The candidate amplitude interval is the exact algebraic intersection of those affine inequalities; the probabilistic model that motivates the inequalities is an approximation.',
         '', '**Validity:** split-conformal marginal H00 coverage requires site exchangeability (or, for weighted conformal, an exact density ratio and invariant conditional distribution). No unconditional coverage theorem is asserted for the positive-transfer confidence sets. All positive-amplitude inclusion rates below are empirical.',
         '', '## 3. Executed results',
         f'{len(r)} procedure/condition rows from **1,000 independently seeded worlds per distinct generator configuration**. Rows comparing methods or sensitivity bounds reuse the same worlds and must not be counted as additional independent datasets.',
         '']
    if version=='v0.10':
        out.extend(['| Generator | H00 retained per site | H00 retained at all sites | True donor retained per site | True amplitude covered per site |',
                    '|---|---:|---:|---:|---:|'])
        for e in r:out.append(f"| {e['generator']} | {fmt(e['H00_retained_per_site_pct'])}% | {fmt(e['H00_retained_all_sites_pct'])}% | {fmt(e.get('true_donor_retained_per_site_pct'))}% | {fmt(e.get('true_donor_amplitude_covered_per_site_pct'))}% |")
    elif version=='v0.12':
        out.extend(['| Generator condition | H00 retained/site | H00 retained/all 10 | False-alarm upper 95% | Readiness decision |','|---|---:|---:|---:|---|'])
        for e in r:
            if e['generator']=='H00':gate=e.get('readiness_FWER_false_alarm_upper_le_5pct')
            else:gate=(e.get('readiness_power_at_least_80pct') and e.get('readiness_true_equation_joint_coverage_at_least_95pct'))
            out.append(f"| {e['condition']} | {fmt(e['H00_retained_per_site_pct'])}% | {fmt(e['H00_retained_all_sites_pct'])}% | {fmt(e.get('simultaneous_false_alarm_one_sided_Wilson95_upper_pct'))}% | {fmt(gate)} |")
    else:
        out.extend(['| Configuration | Method | H00 retained/site | H00 retained/all 10 | Compatible families/site | True amplitude covered/site |',
                    '|---|---|---:|---:|---:|---:|'])
        for e in r:
            conf=e['condition']
            if version=='v0.9':conf+=f"; allowed {e['externally_assumed_absolute_shift_bound']:.3f}"
            out.append(f"| {conf} | {e.get('method','')} | {fmt(e['H00_retained_per_site_pct'])}% | {fmt(e['H00_retained_all_sites_pct'])}% | {fmt(e.get('mean_compatible_families_per_site'),2)} | {fmt(e.get('true_amplitude_covered_per_site_pct'))}% |")
    out.extend(['',
      'The H00 column is **retention**, not evidence of the absence or presence of a transformation. Under an H00 generator, its complement measures a false exclusion; under an H11 generator, it measures a degree of discrimination. All-ten-site retention must not be confused with the nominal 95% per-site calibration.',
      '', '## 4. Version-specific interpretation'])
    if version=='v0.6':
        a,b,c=r[0],r[3],r[4]
        out.extend([f"- Exchangeable H00 was retained at **{fmt(a['H00_retained_per_site_pct'])}% per site** but only **{fmt(a['H00_retained_all_sites_pct'])}% across all ten**; this is the familywise calibration failure motivating v0.8.",
                    f"- Geographic covariate shift reduced H00 single-site retention to **{fmt(b['H00_retained_per_site_pct'])}%** in this sample.",
                    f"- An unmeasured natural shift reduced it to **{fmt(c['H00_retained_per_site_pct'])}%**, despite the true generator having no transfer."])
    elif version=='v0.7':
        out.extend([f"- For known covariate shift, weighting raised H00 per-site retention from **{fmt(r[2]['H00_retained_per_site_pct'])}% to {fmt(r[3]['H00_retained_per_site_pct'])}%**.",
                    f"- Even weighted calibration retained H00 at all ten sites in only **{fmt(r[3]['H00_retained_all_sites_pct'])}%** of natural-behaviour worlds.",
                    '- The weight formula is known from the synthetic generator; estimation error in a real density ratio was not assessed.'])
    elif version=='v0.8':
        out.extend([f"- With 80 calibration sites, the Bonferroni thresholds are **infinite in {fmt(100*r[1]['fraction_infinite_thresholds'])}%** of cases; all equations remain admissible.",
                    f"- With 240 calibration sites, simultaneous H00 retention reached **{fmt(r[5]['H00_retained_all_sites_pct'])}%**; the corresponding H11 case retained H00 across all ten sites in **{fmt(r[7]['H00_retained_all_sites_pct'])}%**.",
                    '- The finite-sample conformal resolution threshold for alpha/10=0.005 is at least 199 independent calibration sites.'])
    elif version=='v0.9':
        out.extend([f"- Under a -0.015 natural shift, H00 per-site retention was **{fmt(r[0]['H00_retained_per_site_pct'])}%** with no allowance, and **{fmt(r[2]['H00_retained_per_site_pct'])}%** with an assumed 0.015 allowance.",
                    f"- Widening the allowance to 0.025 increased retention to **{fmt(r[3]['H00_retained_per_site_pct'])}%**, but the mean number of compatible families moved towards all ten.",
                    '- The accuracy of an assumed shift bound is the central unresolved external-data condition.'])
    elif version=='v0.10':
        out.extend([f"- Under no transformation, H00 was retained at **{fmt(r[0]['H00_retained_per_site_pct'])}% per site** but only **{fmt(r[0]['H00_retained_all_sites_pct'])}% across all ten**.",
                    '- The correct synthetic donor was retained at about 97% of individual sites for each of the three positive scenarios, while other donor equations frequently remained compatible.',
                    '- A compatible donor flow does not imply that the flow occurred in real data or identify the generator outside this laboratory setting.'])
    elif version=='v0.11':
        out.extend([f"- Quadratic behavioural regression was selected in **{fmt(r[0]['selected_quadratic_pct'])}%** of H00 worlds and **{fmt(r[3]['selected_quadratic_pct'])}%** of H11 worlds.",
                    '- Selection uses 40 separate donor validation sites, calibration uses another 80, and neither process accesses the ten target sites.',
                    '- The selected scheme did not materially outperform both fixed-model controls. This is not evidence that model selection is necessary.'])
    elif version=='v0.12':
        outcomes=[(e['condition'],e.get('readiness_FWER_false_alarm_upper_le_5pct')) for e in r if e['generator']=='H00']
        out.extend([f"- The representative and covariate-shifted H00 cases passed their 5% upper-bound checks, but the unmeasured-shift H00 case **FAILED**, with upper bound **{fmt(r[2]['simultaneous_false_alarm_one_sided_Wilson95_upper_pct'],2)}%**.",
                    '- The three H11 tests met the stipulated detection and synthetic true-family coverage rules, but a pass in positive generators does not cancel a failed false-alarm criterion.',
                    '**Overall readiness: FAIL.** No broad statement of statistical validation is justified.'])
    out.extend(['', '## 5. Reproducibility and scientific limitations',
    '- The first 80 sites are for model training, a distinct set is used for conformity calibration, and the final ten sites are held out. In v0.11/v0.12, a further 40 of the labelled calibration sites are reserved for frozen model selection before a separate 80-site calibration.',
    '- Exact four-category count conservation and non-negative integers are asserted on every generated dataset; the source code contains explicit checks.',
    '- One thousand independent Monte Carlo worlds are generated per scenario; method comparisons on the same worlds are paired experiments, not separate replicates.',
    '- All candidate equations and behavioural models are deliberately limited. No universal recovery, uniquely identified mechanism, or real-data fraud diagnostic is claimed.',
    '- Version design and parameters were refined during an exploratory synthetic series; the programmes were not independently preregistered or audited.',
    '- A nominal per-site conformal result does not extend automatically to familywise tests, transported populations or positive-rate confidence sets.',
    '', '## 6. Reproduction',
    'Python 3.13 and NumPy 2.3.5 were used. Commands from the release directory:',
    '```bash',
    'python -m pip install -r requirements.txt',
    f'OPENBLAS_NUM_THREADS=1 python experiment.py --version {version} --output . > execution.log',
    f'OPENBLAS_NUM_THREADS=1 python verify.py --version {version} --directory . > verify.log',
    f'python build_report.py --version {version} --directory .',
    'sha256sum -c MANIFEST.sha256',
    '```',
    'Re-running replaces generated results and logs. Run `sha256sum -c MANIFEST.sha256` **before** regeneration to verify the released originals. The reports are UK English.',
    '', '## 7. Next research decision',
    f'**{version} is an executed synthetic research milestone, not a conclusion about actual election outcomes.**'
    ])
    md='\n'.join(out)+'\n'
    (p/f'RELATORIO_EQ-PRB-001_{version}.md').write_text(md,encoding='utf-8')
    body=mistune.create_markdown(plugins=['table'])(md)
    style='''<style>:root{color-scheme:light}body{font:15px/1.6 system-ui,-apple-system,Segoe UI,Arial,sans-serif;max-width:1050px;margin:36px auto;padding:0 24px;color:#1a2735;background:#fff}h1{font-size:29px;line-height:1.25;color:#162f51}h2{border-bottom:1px solid #d9e1eb;padding-bottom:8px;margin-top:36px;color:#234c73}table{width:100%;border-collapse:collapse;margin:16px 0;font-size:13px}th{background:#eef3f9;text-align:left}td,th{padding:9px 10px;border:1px solid #d4dee9;vertical-align:top}tr:nth-child(even){background:#f8fafc}blockquote{border-left:4px solid #66849d;padding-left:16px}code,pre{font-family:ui-monospace,Consolas,monospace;font-size:13px}pre{overflow:auto;background:#f3f6fa;padding:14px;border-radius:8px}p,li{max-width:1000px}footer{color:#65788a;font-size:12px;margin-top:40px}</style>'''
    header=f'<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(version)} · EQ-PRB-001</title>{style}</head><body>'
    (p/f'RELATORIO_EQ-PRB-001_{version}.html').write_text(header+body+'<footer>ELIS / EQ-PRB-001 · Synthetic research only · 8 November 2026</footer></body></html>\n',encoding='utf-8')
    return md

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--version',required=True,choices=STAGES);parser.add_argument('--directory',default='.')
    a=parser.parse_args();build(a.version,a.directory)
