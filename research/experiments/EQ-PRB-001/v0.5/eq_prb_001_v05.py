#!/usr/bin/env python3
"""EQ-PRB-001 v0.5: continuous partial-identification bounds with independent panels.

100% synthetic. No observed election data are loaded. UK English.
No function is fitted separately to individual observed sections.

Core scientific assumption: independent paired calibration panels at the SAME
section/round indices are representative samples from the actual latent
behavioural probabilities p_i and baseline q_i. This strong assumption is NOT
guaranteed by independence alone, and is deliberately violated in a stress test.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import time
from pathlib import Path
import numpy as np

SEED=20261108
MUNICIPALITIES=5
SITES_PER_MUNI=8
N_SITES=MUNICIPALITIES*SITES_PER_MUNI
N_SECTIONS=8
CATEGORIES=('W','L','B','N')
SHAPE=(N_SITES,2,N_SECTIONS)
P_MAX=.20
TRUE_A=.377  # off the v0.4 amplitude grid (.06, .12, ..., .42)
RATE_EFFECT_BOUND=.15  # relative: ±.10 polling-place + ±.05 section
PANEL_ALPHA=.01
MOMENT_ALPHA_PAIRED=.05
MOMENT_ALPHA_ENVELOPE=.04  # combined with 1% panel guarantee -> >=95%

site=np.arange(N_SITES)[:,None,None]
turn=np.arange(2)[None,:,None]
section=np.arange(N_SECTIONS)[None,None,:]
z=np.broadcast_to(np.sin(.79*(site+1)+.61*(section+1)+.22*turn),SHAPE).copy()
C=np.broadcast_to((290+(site*13+section*31+turn*19)%150).astype(int),SHAPE).copy()
qB=np.clip(.069+.012*z+.004*np.sin(.83*site+.5*turn),.03,.14)
qN=np.broadcast_to(.033+.005*np.cos(.5*section+turn),SHAPE).copy()
qL=np.clip(.39-.055*z+.009*np.cos(.33*site),.15,.65)
qW=1-qB-qN-qL
Q=np.stack((qW,qL,qB,qN),axis=-1)
TRAIN_SITES=np.array([i for i in range(N_SITES) if i%8 not in (2,7)])
TEST_SITES=np.array([i for i in range(N_SITES) if i%8 in (2,7)])
GROUPS=[(part,sites,t) for part,sites in [('train',TRAIN_SITES),('holdout',TEST_SITES)] for t in range(2)]
assert len(TRAIN_SITES)==30 and len(TEST_SITES)==10
assert np.all(Q>0) and np.allclose(Q.sum(axis=-1),1)


def shape_fn(name):
    if name=='constant': return np.ones(SHAPE)
    if name=='step': return .22+.78*(z>.12)
    if name=='logistic': return .20+.80/(1+np.exp(-5*(z-.12)))
    raise ValueError(name)


def mask(h):
    flag={'H00':(0,0),'H01':(0,1),'H10':(1,0),'H11':(1,1)}[h]
    return np.broadcast_to(np.asarray(flag)[None,:,None],SHAPE)

FAMILIES=[(h,s) for h in ('H01','H10','H11') for s in ('constant','step','logistic')]
F=np.stack([shape_fn(s)*mask(h) for h,s in FAMILIES])
ACTIVE=np.stack([mask(h) for h,s in FAMILIES])
NF=len(FAMILIES)


def draw_four(rng,n,p):
    """Multinomial W,L,B,N, using independent binomial draws per section."""
    b=rng.binomial(n,p[...,2])
    rem=n-b
    w=rng.binomial(rem,np.clip(p[...,0]/(1-p[...,2]),0,1))
    rem2=rem-w
    ll=rng.binomial(rem2,np.clip(p[...,1]/(p[...,1]+p[...,3]),0,1))
    return np.stack((w,ll,b,rem2-ll),axis=-1)


def synthetic_worlds(rng,n_worlds,n_reference,n_panel,scenario):
    """All rates and latent probabilities used by generator only, not by inversion."""
    site_effect=rng.uniform(-.0015,.0015,size=(n_worlds,N_SITES,1,1))
    section_effect=rng.uniform(-.001,.001,size=(n_worlds,*SHAPE))
    natural=site_effect+section_effect
    natural_step=scenario in ('natural_step','H00_biased_panel')
    if natural_step:
        natural=natural-.30*qB[None]*shape_fn('step')[None]
    pb=qB[None]+natural
    probs=np.broadcast_to(Q,(n_worlds,*Q.shape)).copy()
    probs[...,2]=pb
    probs[...,0]=qW[None]-(pb-qB[None])
    if not (np.all(probs>0) and np.allclose(probs.sum(axis=-1),1) and np.max(pb)<P_MAX):
        raise AssertionError('Generator probability invariant violated')
    latent=draw_four(rng,np.broadcast_to(C,(n_worlds,*C.shape)),probs)

    temporal='H00' if scenario in ('natural_stable','natural_step','H00_biased_panel') else scenario[:3]
    a=TRUE_A*shape_fn('step')[None]*mask(temporal)[None]
    if scenario=='H11_D3_offgrid':
        us=rng.uniform(-.10,.10,size=(n_worlds,N_SITES,1,1))
        vs=rng.uniform(-.05,.05,size=(n_worlds,*SHAPE))
        a=np.clip(a*(1+us+vs),0,1)
    moved=np.floor(latent[...,2]*a+.5).astype(np.int64)
    observed=latent.copy(); observed[...,0]+=moved;observed[...,2]-=moved
    if not (np.all(observed>=0) and np.array_equal(observed.sum(axis=-1),np.broadcast_to(C,(n_worlds,*C.shape)))):
        raise AssertionError('Exact integer conservation failed')
    ref=rng.binomial(n_reference,np.broadcast_to(qB,(n_worlds,*SHAPE)))
    paired_base=rng.binomial(n_panel,np.broadcast_to(qB,(n_worlds,*SHAPE)))
    paired_actual_prob=pb.copy()
    if scenario=='H00_biased_panel':
        # External behavioural panel fails to represent actual natural change.
        paired_actual_prob=np.clip(pb+.024*shape_fn('step')[None],.001,P_MAX-.001)
    paired_actual=rng.binomial(n_panel,paired_actual_prob)
    return {'Y':observed,'R':ref,'P':paired_actual,'Q':paired_base,
            'truth_natural_max':np.max(np.abs(natural),axis=(1,2,3)),
            'truth_panel_mismatch_max':np.max(np.abs(paired_actual_prob-pb),axis=(1,2,3))}


def interval_intersection(c,k,u,h=0.,upper=.60):
    """Exact intervals for |c-a*k| <= u+a*h, 0<=a<=upper, h>=0.

    Both sides are affine in a. Intersect four half-spaces rather than
    discretising the amplitude. Handles positive, negative and zero slopes.
    """
    c,k,u,h=np.broadcast_arrays(*[np.asarray(v,float) for v in (c,k,u,h)])
    lo=np.zeros_like(c); hi=np.full_like(c,upper); ok=np.ones_like(c,bool)
    # Recast two inequalities as value <= a*slope.
    for value,slope in ((c-u,k+h),(-c-u,h-k)):
        near=np.abs(slope)<=1e-14
        ratio=value/np.where(near,1.,slope)
        lo=np.where(slope>1e-14,np.maximum(lo,ratio),lo)
        hi=np.where(slope< -1e-14,np.minimum(hi,ratio),hi)
        ok &=~(near&(value>1e-12))
    ok &=lo<=hi+1e-12
    return lo,hi,ok


def confidence_sets(data,n_reference,n_panel,method,rate_bound=RATE_EFFECT_BOUND):
    """Test-inversion confidence intervals for H x shape x continuous amplitude.

    Paired method: Z=R/n_ref + P/n_panel - Q/n_panel; E[Z_i]=p_i,
    conditional on representative, independent sampling.
    Envelope method: Z=R/n_ref, and a 99% simultaneously-valid upper
    confidence bound d>=max_i|p_i-q_i| is derived ONLY from paired panels.
    Moment tests spend 5% paired; 4% envelope (1% spent on d).

    For a candidate a,f: E[(1-a*f)*Z-Y_B/C] is bounded by rounding
    (<0.5/C) and multiplicative rate heterogeneity (P_MAX*a*f*rate_bound).
    Conditional bounded-differences of each independent Bernoulli contribution
    yield four Bonferroni-corrected finite-sample McDiarmid radii. The bounds
    are *constant in a* by replacing (1-a*f)^2 <= 1, making the off-grid
    interval intersection exact (no numerical amplitude grid).
    """
    Y=data['Y'][...,2]/C[None]
    ref=data['R']/n_reference
    diff=(data['P']-data['Q'])/n_panel
    worlds=Y.shape[0]
    ncells=int(np.prod(SHAPE))
    eps=math.sqrt(math.log(4*ncells/PANEL_ALPHA)/(2*n_panel))
    d_hat=np.max(np.abs(diff),axis=(1,2,3))+2*eps
    if method=='paired':
        Z=ref+diff
        spent=MOMENT_ALPHA_PAIRED
        survey_variance_coefficient=(1/n_reference+2/n_panel)
        nuisance=np.zeros(worlds)
    elif method=='envelope':
        Z=ref
        spent=MOMENT_ALPHA_ENVELOPE
        survey_variance_coefficient=1/n_reference
        nuisance=d_hat
    else: raise ValueError(method)
    lower=np.zeros((worlds,NF));upper=np.full((worlds,NF),.60)
    alive=np.ones((worlds,NF),bool)
    zero_accepted=np.ones(worlds,bool)
    group_records=[]
    for part,sites,t in GROUPS:
        y=Y[:,sites,t].reshape(worlds,-1)
        zscore=Z[:,sites,t].reshape(worlds,-1)
        f=F[:,sites,t].reshape(NF,-1)
        active=ACTIVE[:,sites,t].reshape(NF,-1)
        ci=C[sites,t].reshape(-1)
        m=ci.size
        c=zscore.mean(axis=1)-y.mean(axis=1)
        k=zscore@f.T/m
        rounderr=float(.5*np.mean(1/ci))
        radius=math.sqrt(.5*math.log(2*len(GROUPS)/spent)*
                         (np.sum(1/ci)+m*survey_variance_coefficient)/m**2)
        threshold=radius+rounderr+nuisance[:,None]
        slope_allowance=P_MAX*rate_bound*f.mean(axis=1)[None]
        l,h,valid=interval_intersection(c[:,None],k,threshold,slope_allowance)
        lower=np.maximum(lower,l)
        upper=np.minimum(upper,h)
        alive &=valid & (lower<=upper+1e-12)
        # H00 has no rate heterogeneity; its natural-bound/paired radius applies.
        zero_accepted &=np.abs(c)<=radius+rounderr+nuisance+1e-12
        group_records.append({'partition':part,'round':int(t+1),'sections':int(m),
                              'max_noise_radius':radius,'rounding_radius':rounderr})
    lower=np.where(alive,lower,np.nan);upper=np.where(alive,upper,np.nan)
    family_count=alive.sum(axis=1)+zero_accepted.astype(int)
    return {'lower':lower,'upper':upper,'alive':alive,'H00':zero_accepted,
            'family_count':family_count,'d_hat':d_hat,'groups':group_records}


def summarise(data,output,scenario,method,n_reference,n_panel,rate_bound):
    w=output['alive'].shape[0]
    is_h00=scenario in ('natural_stable','natural_step','H00_biased_panel')
    correct_temporal='H00' if is_h00 else scenario[:3]
    true_index=FAMILIES.index((correct_temporal,'step')) if not is_h00 else None
    truth_cover=(output['H00'] if is_h00 else
                 output['alive'][:,true_index]&
                 (output['lower'][:,true_index]<=TRUE_A+1e-12)&
                 (output['upper'][:,true_index]>=TRUE_A-1e-12))
    true_width=(output['upper'][:,true_index]-output['lower'][:,true_index]) if not is_h00 else np.full(w,np.nan)
    h00=output['H00'];count=output['family_count'];correct=int(truth_cover.sum())
    result={'scenario':scenario,'method':method,'n_reference':int(n_reference),'n_panel':int(n_panel),
            'rate_envelope':rate_bound,'replicates':int(w),
            'assumptions_valid':scenario!='H00_biased_panel',
            'true_family_inclusion_count':correct,'true_family_inclusion':correct/w,
            'H00_retained_count':int(h00.sum()),'H00_retained':float(h00.mean()),
            'mean_compatible_families':float(count.mean()),
            'median_compatible_families':float(np.median(count)),
            'mean_true_family_amplitude_width':float(np.nanmean(true_width)) if np.any(np.isfinite(true_width)) else None,
            'median_calibrated_natural_envelope':float(np.median(output['d_hat'])) if method=='envelope' else None,
            'empirical_calibrated_envelope_coverage':float(np.mean(output['d_hat']>=data['truth_natural_max'])) if method=='envelope' else None,
            'max_realised_natural_shift':float(np.max(data['truth_natural_max'])),
            'max_realised_panel_mismatch':float(np.max(data['truth_panel_mismatch_max'])),
            'families_including_H00':int(h00.sum()),
            'example_first_trial':{'H00_retained':bool(h00[0]),
                'compatible_families':[{'temporal':h,'shape':sh,'amplitude_interval':
                                       [round(float(output['lower'][0,i]),6),round(float(output['upper'][0,i]),6)]}
                                      for i,(h,sh) in enumerate(FAMILIES) if output['alive'][0,i]]}}
    return result


def run(seed,replicates,output):
    cases=[]
    scenarios=('natural_stable','natural_step','H01_D0_offgrid',
               'H11_D0_offgrid','H11_D3_offgrid','H00_biased_panel')
    for s in scenarios:
        for npanel in (100,1000,10000):
            cases.append((s,1800,npanel))
    for nref in (75,300):
        cases.append(('H11_D3_offgrid',nref,10000))
    records=[];start=time.time()
    for case_idx,(scenario,nref,npanel) in enumerate(cases):
        independent_seed=seed+1_000_003*case_idx+101
        rng=np.random.default_rng(independent_seed)
        worlds=synthetic_worlds(rng,replicates,nref,npanel,scenario)
        for method in ('paired','envelope'):
            rate=RATE_EFFECT_BOUND
            out=confidence_sets(worlds,nref,npanel,method,rate)
            record=summarise(worlds,out,scenario,method,nref,npanel,rate)
            record['seed']=independent_seed
            record['group_thresholds']=out['groups']
            records.append(record)
        print(f'case {case_idx+1:02d}/{len(cases)} {scenario:20s} reference={nref:4d} panel={npanel:5d}',flush=True)
    # Additional optimistically zero-heterogeneity analysis only where valid.
    for scenario in ('H11_D0_offgrid','natural_stable'):
        nref,npanel=1800,10000
        idx=cases.index((scenario,nref,npanel))
        rng=np.random.default_rng(seed+1_000_003*idx+101)
        worlds=synthetic_worlds(rng,replicates,nref,npanel,scenario)
        out=confidence_sets(worlds,nref,npanel,'paired',rate_bound=0.)
        r=summarise(worlds,out,scenario,'paired_exact_rate',nref,npanel,0.)
        r['seed']=seed+1_000_003*idx+101;r['group_thresholds']=out['groups'];records.append(r)
    output.mkdir(parents=True,exist_ok=True)
    with (output/'results_v0.5.json').open('w',encoding='utf-8') as f:
        json.dump({'experiment':'EQ-PRB-001','version':'0.5','date':'2026-11-08',
          'scope':'synthetic-only; not evidence of actual electoral activity',
          'seed':seed,'n_replicates_per_case':replicates,'n_independent_cases':len(cases),
          'n_independent_synthetic_worlds':len(cases)*replicates,
          'n_sites':N_SITES,'n_sections':N_SITES*N_SECTIONS,'n_rounds':2,
          'train_sites':TRAIN_SITES.tolist(),'test_sites':TEST_SITES.tolist(),
          'amplitude_domain':[0,.6],'true_offgrid_amplitude':TRUE_A,
          'families':[{'temporal':h,'shape':sh} for h,sh in FAMILIES],
          'assumption_details':{
            'paired_panel':'Independent, representative binomial samples from same section-round natural p_B and baseline q_B; no source latent counts supplied to inference.',
            'relative_rate_heterogeneity_bound':RATE_EFFECT_BOUND,
            'blank_probability_upper_bound':P_MAX,
            'envelope_probability_budget':PANEL_ALPHA,
            'paired_moment_error_budget':MOMENT_ALPHA_PAIRED,
            'envelope_moment_error_budget':MOMENT_ALPHA_ENVELOPE,
            'conditional_independence':'Independent individual binomial draws in source counts, target references and calibration panels, given shared location effects.',
            'optimistic_case':'paired_exact_rate valid for D0 and H00 only',
            'negative_control':'biased behavioural panel invalidates p-panel representativeness and the nominal coverage guarantee.'},
          'records':records},f,ensure_ascii=False,indent=2)
    keys=['scenario','method','n_reference','n_panel','rate_envelope','replicates',
          'assumptions_valid','true_family_inclusion_count','true_family_inclusion',
          'H00_retained_count','H00_retained','mean_compatible_families',
          'median_compatible_families','mean_true_family_amplitude_width',
          'median_calibrated_natural_envelope','empirical_calibrated_envelope_coverage','seed']
    with (output/'identified_intervals_summary.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
        for r in records:writer.writerow({k:r.get(k) for k in keys})
    (output/'examples.json').write_text(json.dumps([{'scenario':r['scenario'],
            'method':r['method'],'n_reference':r['n_reference'],'n_panel':r['n_panel'],
            'example':r['example_first_trial']} for r in records],indent=2),encoding='utf-8')
    print(f'Completed {len(cases)*replicates:,} independent worlds and {len(records)} set evaluations in {time.time()-start:.1f}s',flush=True)
    return records


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,default=SEED)
    parser.add_argument('--replicates',type=int,default=1000)
    parser.add_argument('--out',type=Path,default=Path(__file__).parent)
    a=parser.parse_args()
    run(a.seed,a.replicates,a.out)
if __name__=='__main__':main()
