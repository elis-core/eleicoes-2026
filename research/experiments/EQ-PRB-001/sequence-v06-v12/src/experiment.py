#!/usr/bin/env python3
"""Sequential release runner for EQ-PRB-001 v0.6 to v0.12.

Each release freezes one version's experiments and generates independently
seeded synthetic trials. Run from the release directory after core.py is copied
there. No observed election data, no runtime network access.
"""
from __future__ import annotations
import argparse
import csv
from dataclasses import dataclass,replace
from datetime import date
import json
import math
from pathlib import Path
import numpy as np
from core import (AMPLITUDE,CATEGORY,FAMILIES,make_world,fit_predict,thresholds,
                  infer_one,summary,checks,unweighted_quantile,intersect_affine,
                  wilson_upper,scores_on_cal)

VERSION_TO_INT={'v0.6':6,'v0.7':7,'v0.8':8,'v0.9':9,'v0.10':10,'v0.11':11,'v0.12':12}
PURPOSE={
  'v0.6':'External-site calibration and geographic transport',
  'v0.7':'Known-ratio weighted conformal calibration under geographic covariate shift',
  'v0.8':'Site-level dependence and simultaneous-coverage calibration',
  'v0.9':'Sensitivity bounds for unmeasured geographic and reference-panel bias',
  'v0.10':'Competing synthetic donor flows and mechanism ambiguity',
  'v0.11':'Frozen model selection with fully separate validation and evaluation sites',
  'v0.12':'Independent stress-matrix audit and pre-defined readiness gates',
}


def record(version,label,w,inf,method,extras=None):
    d={'version':version,'condition':label,'method':method,'generator':w.scenario,
       'synthetic_worlds':int(w.n_worlds),'independent_training_sites':int(w.n_train),
       'independent_calibration_sites':int(w.n_cal),'heldout_target_sites':int(w.n_target),
       'sections_per_site':8,'turns':2,
       **summary(w,inf,w.scenario)}
    if extras:d.update(extras)
    # per-world site-level error rates; world is independent unit for uncertainty
    trial_false=(~inf['h00']).mean(axis=1)
    d['H00_exclusion_per_site_pct']=float(100*trial_false.mean())
    d['H00_exclusion_per_site_mc_se_pct']=float(100*trial_false.std(ddof=1)/np.sqrt(len(trial_false)))
    d['H00_exclusion_any_of_10_pct']=float(100*(~inf['h00'].all(axis=1)).mean())
    if w.scenario=='H00':
        count=int((~inf['h00'].all(axis=1)).sum())
        d['simultaneous_false_alarm_one_sided_Wilson95_upper_pct']=100*float(wilson_upper(count,w.n_worlds))
    return d


def run_single(version,tag,seed,replicates=1000,scenario='H00',
               shifted=False,unmeasured_shift=0.,random_rates=False,
               method='joint',model='step',alpha=.05,extra_tolerance=0.,n_cal=80):
    w=make_world(seed,replicates=replicates,scenario=scenario,shifted=shifted,
                 unmeasured_shift=unmeasured_shift,random_rates=random_rates,n_cal=n_cal)
    assert checks(w)
    pred=fit_predict(w,model)
    q=thresholds(w,pred,alpha=alpha,method=method)
    inf=infer_one(w,pred,q,extra_tolerance=extra_tolerance)
    return record(version,tag,w,inf,method,{'model':model,'alpha':alpha,
                 'assumed_natural_shift_bound':extra_tolerance,
                 'actual_target_natural_shift':unmeasured_shift,
                 'known_covariate_shift':bool(shifted),
                 'random_rate_generator':bool(random_rates),
                 'calibration_quantile_design':'site-level max over both rounds',
                 'calibration_sites_are_independent':True})


def run_v06(version,R):
    cases=[('H00 matched source/target','H00',False,0.,False),
           ('H11 blank transfer, fixed','H11_B',False,0.,False),
           ('H11 blank transfer, random','H11_B',False,0.,True),
           ('H00 covariate shift','H00',True,0.,False),
           ('H00 unmeasured natural shift','H00',False,-.018,False),
           ('H11 transfer + covariate shift','H11_B',True,0.,True)]
    for j,(tag,s,geo,delta,random) in enumerate(cases):
        R.append(run_single(version,tag,seed=60101+127*j,scenario=s,shifted=geo,
                            unmeasured_shift=delta,random_rates=random))


def run_v07(version,R):
    cases=[('Exchangeable H00','H00',False),
           ('Known covariate-shift H00','H00',True),
           ('Known covariate-shift H11-B','H11_B',True)]
    for j,(tag,scenario,geo) in enumerate(cases):
        seed=70101+127*j
        w=make_world(seed,scenario=scenario,shifted=geo)
        pred=fit_predict(w,'step')
        for method in ('joint','weighted'):
            q=thresholds(w,pred,method=method)
            inf=infer_one(w,pred,q)
            R.append(record(version,tag,w,inf,method,{'known_analytic_density_ratio':bool(geo),
                      'density_ratio':'w(x)=1+0.8x for the shifted target population',
                      'require_conditional_invariance':True}))


def run_v08(version,R):
    for ncal in (80,240):
        for scenario in ('H00','H11_B'):
            w=make_world(80100+ncal*10+(0 if scenario=='H00' else 1),scenario=scenario,n_cal=ncal)
            pred=fit_predict(w)
            for method in ('joint','bonferroni'):
                q=thresholds(w,pred,method=method)
                inf=infer_one(w,pred,q)
                R.append(record(version,f'{scenario}, calibration sites={ncal}',w,inf,method,
                                {'multiple_site_rule':'Bonferroni alpha=.05/10' if method=='bonferroni' else 'Unadjusted site alpha=.05',
                                 'conformal_resolution':'A finite Bonferroni threshold requires at least 199 calibration sites',
                                 'nominal_joint_target':.95}))


def run_v09(version,R):
    for scenario,delta in (('H00',-.015),('H11_B',-.015),('H00',0.)):
        w=make_world(90101+len(R)*31,scenario=scenario,unmeasured_shift=delta)
        pred=fit_predict(w)
        q=thresholds(w,pred)
        for assumed in (0.,.005,.015,.025):
            inf=infer_one(w,pred,q,extra_tolerance=assumed)
            R.append(record(version,f'{scenario}: actual natural shift {delta:+.3f}',w,inf,'site_joint_plus_sensitivity',
                            {'actual_natural_shift':delta,'externally_assumed_absolute_shift_bound':assumed,
                             'bound_covers_simulated_shift':abs(delta)<=assumed,
                             'bound_is_exogenous_not_estimated_from_target':True}))


def _donor_inference(w,pred,alpha=.05):
    # 3 donor-category tests; calibration alpha is Bonferroni-corrected.
    all_q=np.stack([thresholds(w,pred,alpha=alpha/3,category=d) for d in range(3)],axis=-1)
    W=w.n_worlds;T=w.n_target
    zero=np.ones((W,T),dtype=bool)
    for d in range(3):
        err=np.abs(pred[:,w.target_slice,:,d]-w.obs[:,w.target_slice,:,d])
        zero &=np.all(err<=all_q[:,:,d,None],axis=2)
    comp=[];tru=[];width=[]; details={}
    # For each alternative donor, other two categories must behave as no-transfer.
    for d,donor in enumerate(CATEGORY):
        q=all_q[:,:,d]
        inf=infer_one(w,pred,q,category=d,models=[('H11','step')])
        good=inf['alive'][:,:,0]
        for other in range(3):
            if other==d:continue
            e=np.abs(pred[:,w.target_slice,:,other]-w.obs[:,w.target_slice,:,other])
            good &=np.all(e<=all_q[:,:,other,None],axis=2)
        cv=good & (inf['lower'][:,:,0]<=AMPLITUDE+1e-10) & (inf['upper'][:,:,0]>=AMPLITUDE-1e-10)
        comp.append(good)
        tru.append(cv)
        width.append(np.where(good,inf['upper'][:,:,0]-inf['lower'][:,:,0],np.nan))
        details[donor]={'retained_site_pct':float(100*good.mean()),
                        'true_amplitude_inside_site_pct':float(100*cv.mean())}
    compatible=np.stack(comp,axis=-1)
    return {'zero':zero,'compatible':compatible,'true_contains':np.stack(tru,axis=-1),
            'threshold':all_q,'details':details}


def run_v10(version,R):
    for j,scenario in enumerate(('H00','H11_B','H11_N','H11_L')):
        w=make_world(100101+137*j,scenario=scenario)
        pred=fit_predict(w)
        res=_donor_inference(w,pred)
        zero=res['zero']; comp=res['compatible']
        row={'version':version,'condition':f'{scenario}: three competing donor categories',
             'generator':scenario,'synthetic_worlds':int(w.n_worlds),
             'heldout_target_sites':w.n_target,
             'H00_retained_per_site_pct':float(100*zero.mean()),
             'H00_retained_all_sites_pct':float(100*zero.all(axis=1).mean()),
             'mean_compatible_mechanisms_per_site':float((comp.sum(axis=-1)+zero).mean()),
             'compatible_mechanism_retention':res['details'],
             'donor_labels':list(CATEGORY),
             'categorywise_alpha':.05/3,
             'simultaneous_across_sites_guaranteed':False}
        if scenario!='H00':
            idx=CATEGORY.index(scenario.split('_')[-1])
            row['true_donor_retained_per_site_pct']=float(100*comp[:,:,idx].mean())
            row['true_donor_amplitude_covered_per_site_pct']=float(100*res['true_contains'][:,:,idx].mean())
            row['true_donor_amplitude_covered_all_sites_pct']=float(100*res['true_contains'][:,:,idx].all(axis=1).mean())
        R.append(row)


def select_with_validation(w):
    """Freeze model using donor validation sites; calibrate on distinct sites."""
    assert w.n_cal>=120
    a=fit_predict(w,'step');b=fit_predict(w,'quadratic')
    i=w.n_train
    v=slice(i,i+40)
    # Inference source: donor validation site observations only, no target votes.
    av=np.mean(np.abs(a[:,v,:,0]-w.obs[:,v,:,0]),axis=(1,2))
    bv=np.mean(np.abs(b[:,v,:,0]-w.obs[:,v,:,0]),axis=(1,2))
    choice=bv<av
    chosen=np.where(choice[:,None,None,None],b,a)
    # Conformal calibration is held separate from donor validation.
    c=slice(i+40,i+120)
    score=np.max(np.abs(chosen[:,c,:,0]-w.obs[:,c,:,0]),axis=2)
    q=unweighted_quantile(score,.05)
    return chosen,np.broadcast_to(q[:,None],(w.n_worlds,w.n_target)).copy(),choice


def run_v11(version,R):
    for j,scenario in enumerate(('H00','H11_B')):
        w=make_world(110101+137*j,scenario=scenario,n_cal=120)
        chosen,q,selection=select_with_validation(w)
        # Explicit no-leakage check: selection code reads only donor-site slices.
        tampered=replace(w,obs=w.obs.copy())
        tampered.obs[:,w.target_slice,:,:]=np.nan
        _,_,selection_after_target_removal=select_with_validation(tampered)
        assert np.array_equal(selection,selection_after_target_removal)
        inf=infer_one(w,chosen,q)
        R.append(record(version,f'{scenario}: frozen model choice',w,inf,'external_validation_freeze',
                        {'selected_quadratic_pct':float(100*selection.mean()),
                         'selection_sites':40,'independent_conformal_calibration_sites':80,
                         'selection_unaffected_by_removing_all_target_outcomes':True,
                         'models_compared':['step','quadratic'],
                         'selection_metric':'mean absolute donor validation residual'}))
        for k,model in enumerate(('step','quadratic')):
            pred=fit_predict(w,model)
            cal=slice(w.n_train+40,w.n_train+120)
            sc=np.max(np.abs(pred[:,cal,:,0]-w.obs[:,cal,:,0]),axis=2)
            q2=np.broadcast_to(unweighted_quantile(sc,.05)[:,None],(w.n_worlds,w.n_target))
            inf2=infer_one(w,pred,q2)
            R.append(record(version,f'{scenario}: fixed {model} comparator',w,inf2,'frozen_comparator',
                            {'model':model,'selection_sites':40,'calibration_sites':80}))


def run_v12(version,R):
    cases=[('H00 representative','H00',False,0.,False),
           ('H00 known covariate shift','H00',True,0.,False),
           ('H00 unmeasured natural shift','H00',False,-.015,False),
           ('H11 fixed rate','H11_B',False,0.,False),
           ('H11 site+section heterogeneity','H11_B',False,0.,True),
           ('H11 with known geographic shift','H11_B',True,0.,True)]
    for j,(tag,scenario,geo,delta,random) in enumerate(cases):
        w=make_world(120101+137*j,scenario=scenario,shifted=geo,
                     unmeasured_shift=delta,random_rates=random,n_cal=120)
        pred,q,choice=select_with_validation(w)
        # Frozen, externally motivated sensitivity delta; no target fitting.
        inf=infer_one(w,pred,q,extra_tolerance=.015)
        r=record(version,tag,w,inf,'frozen_selected_model_and_sensitivity',
                 {'externally_specified_natural_shift_tolerance':.015,
                  'sites_used_for_model_selection':40,'sites_used_for_calibration':80,
                  'sites_used_for_external_evaluation':10,
                  'target_covariate_shifted':geo,'true_target_natural_shift':delta,
                  'true_rate_heterogeneity':random})
        if scenario=='H00':
            false=int((~inf['h00'].all(axis=1)).sum())
            r['readiness_FWER_false_alarm_upper_le_5pct']=bool(wilson_upper(false,w.n_worlds)<=.05)
        else:
            power=1-inf['h00'].all(axis=1).mean()
            r['readiness_power_at_least_80pct']=bool(power>=.80)
            r['readiness_true_equation_joint_coverage_at_least_95pct']=bool(r.get('true_amplitude_covered_all_sites_pct',0)>=95)
        R.append(r)


def run(version,replicates=1000,output='.'):
    assert replicates==1000, 'Published release configuration is frozen at 1,000 replicates per scenario.'
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    records=[]
    dispatch={'v0.6':run_v06,'v0.7':run_v07,'v0.8':run_v08,'v0.9':run_v09,
              'v0.10':run_v10,'v0.11':run_v11,'v0.12':run_v12}
    dispatch[version](version,records)
    payload={'project':'EQ-PRB-001','version':version,'purpose':PURPOSE[version],
       'date':'2026-11-08','evidence_type':'Synthetic mathematical experiments only',
       'independent_replicates_per_generator':replicates,
       'assumptions':[
         'External donor sites, calibration sites and held-out target sites are disjoint.',
         'Only model source features and donor-site panel counts are fitted; no target outcomes enter training.',
         'Site-level exchangeability is required for ordinary conformal H00 marginal calibration.',
         'Covariate-shift weighted conformal assumes an exactly known density ratio and conditional invariance.',
         'Off-grid inverted intervals approximate rounded rates by a bounded deterministic moment error and heterogeneity allowance; positive-mechanism coverage is empirical, not an unconditional theorem.',
         'Reported tests remain synthetic and do not establish a mechanism in real election data.',
       ],'results':records,
       'completion':'executed and verified (exploratory, not preregistered or real-data validated)'}
    (out/'results.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    # Flat metrics are convenient for reproducibility and independent review.
    selected=['version','condition','method','generator','synthetic_worlds',
             'H00_retained_per_site_pct','H00_retained_all_sites_pct',
             'H00_exclusion_per_site_pct','H00_exclusion_any_of_10_pct',
             'mean_compatible_families_per_site','true_amplitude_covered_per_site_pct',
             'true_amplitude_covered_all_sites_pct','mean_true_interval_width',
             'mean_compatible_mechanisms_per_site']
    with (out/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=selected);writer.writeheader()
        for row in records:writer.writerow({k:row.get(k,'') for k in selected})
    return payload

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--version',required=True,choices=sorted(VERSION_TO_INT));
    parser.add_argument('--output',default='.');args=parser.parse_args()
    result=run(args.version,output=args.output)
    for r in result['results']:
        print(f"{args.version}: {r['condition']}: method={r['method']}, "
              f"H00 retained per site={r.get('H00_retained_per_site_pct',float('nan')):.1f}%, "
              f"all sites={r.get('H00_retained_all_sites_pct',float('nan')):.1f}%")
    print(f"completed {args.version}: {len(result['results'])} evaluation rows")
