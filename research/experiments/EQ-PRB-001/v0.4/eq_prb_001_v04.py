#!/usr/bin/env python3
"""EQ-PRB-001 v0.4: partial identification for synthetic paired-round counts.

UK English. Uses *only synthetic data*. This is a statistical modelling exercise,
not an assessment of voting-system operation or of any real election.

Finite-sample guarantee: inversion of group-wise bounded-differences moment tests
conditional on the stated bounded natural shifts, independent reference sampling,
independent voter category draws conditional on site effects, and a bound on rate
heterogeneity. It is not a universal guarantee without those assumptions.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
from typing import NamedTuple

import numpy as np
import scipy
from scipy.special import gammaln, logsumexp

SEED=20261108
MUNICIPALITIES=5
SITES_PER_MUNICIPALITY=8
SECTIONS_PER_SITE=8
N_SITES=MUNICIPALITIES*SITES_PER_MUNICIPALITY
CATEGORIES=('W','L','B','N')
TURNOUT_SHAPE=(N_SITES,2,SECTIONS_PER_SITE)
QMAX=0.20  # Deliberately conservative upper bound on baseline blank probability.
NOMINAL_ALPHA=0.30
SITE_ALPHA_BOUND=0.035
SECTION_ALPHA_BOUND=0.020
RATE_BOUND=SITE_ALPHA_BOUND+SECTION_ALPHA_BOUND
SITE_BEHAVIOUR_BOUND=0.0015
SECTION_BEHAVIOUR_BOUND=0.001
TRUE_NATURAL_ENVELOPE=SITE_BEHAVIOUR_BOUND+SECTION_BEHAVIOUR_BOUND
N_REPLICATES=1000
REFERENCE_SIZES=(1800,300,75)
NATURAL_ENVELOPES=(.0025,.010,.035)
RATE_ENVELOPES=(0.,.055)

site=np.arange(N_SITES)[:,None,None]
turn=np.arange(2)[None,:,None]
section=np.arange(SECTIONS_PER_SITE)[None,None,:]
z=np.broadcast_to(np.sin(.79*(site+1)+.61*(section+1)+.22*turn), TURNOUT_SHAPE).copy()
C=np.broadcast_to((290+(site*13+section*31+turn*19)%150).astype(int),TURNOUT_SHAPE).copy()
qB=np.clip(.069+.012*z+.004*np.sin(.83*site+.5*turn),.03,.14)
qN=np.broadcast_to(.033+.005*np.cos(.5*section+turn),TURNOUT_SHAPE).copy()
qL=np.clip(.39-.055*z+.009*np.cos(.33*site),.15,.65)
qW=1-qB-qN-qL
Q=np.stack((qW,qL,qB,qN),axis=-1)
TRAIN_SITES=np.array([i for i in range(N_SITES) if i%8 not in (2,7)])
TEST_SITES=np.array([i for i in range(N_SITES) if i%8 in (2,7)])
assert np.all(Q>0) and np.allclose(Q.sum(axis=-1),1)
assert len(TRAIN_SITES)==30 and len(TEST_SITES)==10


def shape_fn(name:str)->np.ndarray:
    if name=='constant': return np.ones(TURNOUT_SHAPE)
    if name=='step': return .22+.78*(z>.12)
    if name=='logistic': return .20+.80/(1+np.exp(-5*(z-.12)))
    raise ValueError(name)


def temporal_mask(h:str)->np.ndarray:
    flags={'H00':(0,0),'H01':(0,1),'H10':(1,0),'H11':(1,1)}[h]
    return np.broadcast_to(np.array(flags)[None,:,None],TURNOUT_SHAPE)


class Candidate(NamedTuple):
    temporal:str
    shape:str
    amplitude:float


def candidate_library()->tuple[list[Candidate],np.ndarray,np.ndarray]:
    # Frozen before observing data; no per-section post-hoc parameters.
    candidates=[Candidate('H00','none',0.)]
    rates=[np.zeros(TURNOUT_SHAPE)]
    actives=[np.zeros(TURNOUT_SHAPE)]
    for h in ('H01','H10','H11'):
        for shape in ('constant','step','logistic'):
            for amp in (.06,.12,.18,.24,.30,.36,.42):
                candidates.append(Candidate(h,shape,amp))
                rates.append(amp*shape_fn(shape)*temporal_mask(h))
                actives.append(temporal_mask(h).astype(float))
    return candidates,np.stack(rates),np.stack(actives)

CANDIDATES,RATES,ACTIVES=candidate_library()
NC=len(CANDIDATES)
assert NC==64

# Training and holdout contain disjoint entire sites (both rounds kept together).
GROUPS=[(name,locs,t) for name,locs in (
    ('training',TRAIN_SITES),('holdout',TEST_SITES)) for t in (0,1)]


def draw_multinomial_via_binomial(rng,n,p):
    """Vectorised multinomial categories W,L,B,N, with independent voters."""
    b=rng.binomial(n,p[...,2]);left=n-b
    w=rng.binomial(left,np.clip(p[...,0]/(1-p[...,2]),0,1))
    left2=left-w
    l=rng.binomial(left2,np.clip(p[...,1]/(p[...,1]+p[...,3]),0,1))
    n0=left2-l
    return np.stack((w,l,b,n0),axis=-1)


def simulate(rng:np.random.Generator,nrep:int,reference_size:int,scenario:str,
             reference_bias:bool=False)->dict:
    """Generate and reveal Y and REF; latent X is never supplied to inversion."""
    site_drift=rng.uniform(-SITE_BEHAVIOUR_BOUND,SITE_BEHAVIOUR_BOUND,size=(nrep,N_SITES,1,1))
    sec_drift=rng.uniform(-SECTION_BEHAVIOUR_BOUND,SECTION_BEHAVIOUR_BOUND,size=(nrep,*TURNOUT_SHAPE))
    nat=site_drift+sec_drift
    if scenario=='natural_step':
        # H00; a change in behavioural probabilities, not any transformation.
        nat=nat-NOMINAL_ALPHA*qB[None]*shape_fn('step')[None]
    pb=qB[None]+nat
    assert np.min(pb)>.001 and np.max(pb)<QMAX
    pp=np.broadcast_to(Q,(nrep,*Q.shape)).copy()
    pp[...,2]=pb
    pp[...,0]=qW[None]-(pb-qB[None])
    assert np.allclose(pp.sum(axis=-1),1) and np.min(pp)>0
    latent=draw_multinomial_via_binomial(rng,np.broadcast_to(C,(nrep,*C.shape)),pp)
    if scenario in ('H01_D0','H10_D0','H11_D0','H11_D3'):
        h=scenario[:3]
    else:
        h='H00'
    alpha=NOMINAL_ALPHA*shape_fn('step')[None]*temporal_mask(h)[None]
    if scenario=='H11_D3':
        ul=rng.uniform(-SITE_ALPHA_BOUND,SITE_ALPHA_BOUND,size=(nrep,N_SITES,1,1))
        vs=rng.uniform(-SECTION_ALPHA_BOUND,SECTION_ALPHA_BOUND,size=(nrep,*TURNOUT_SHAPE))
        alpha=np.clip(alpha+(ul+vs)*temporal_mask(h)[None],0,1)
    moved=np.floor(latent[...,2]*alpha+.5).astype(int)
    Y=latent.copy();Y[...,0]+=moved;Y[...,2]-=moved
    assert np.all(Y>=0) and np.array_equal(Y.sum(axis=-1),np.broadcast_to(C,(nrep,*C.shape)))
    ref_p=np.broadcast_to(Q,(nrep,*Q.shape)).copy()
    if reference_bias:
        # Biased reference sampling is model misspecification, not a transformation.
        bias=.022*shape_fn('step')[None]
        ref_p[...,2]=qB[None]+bias
        ref_p[...,0]=qW[None]-bias
    ref=draw_multinomial_via_binomial(rng,np.full((nrep,*C.shape),reference_size),ref_p)
    assert np.all(ref>=0) and np.all(ref.sum(axis=-1)==reference_size)
    return {'Y':Y,'REF':ref}


def moment_confidence_sets(data:dict,reference_size:int,natural_envelope:float,
                           rate_envelope:float,alpha_familywise:float=.05)->dict:
    """Invert four two-sided, finite-sample moment inequalities.

    H0 for a fixed candidate: each site's natural p_B shift relative to the
    independent reference q_B is deterministically bounded by |δ|<=d; the
    actual transformation rate differs from its frozen nominal function by
    <=rate_envelope on active rounds, and q_B<=QMAX. The natural and rate
    fluctuations may be dependent across sections within sites. Conditional on
    those effects, individual latent draws and reference draws are independent.

    For B~Bin(C,p), Y_B=B-round(a*B), its expectation differs from
    C*(1-a)*p by <=1/2; its dependence on each of C Bernoulli trials has
    bounded difference <=1. Likewise each reference trial has difference
    1/ref_n. McDiarmid + union bound over four specified groups yields >=95%
    coverage of the true candidate under exactly these premises. Inverting
    fixed-candidate tests does not require a Bonferroni factor for the number
    of candidate equations. Coverage is unconditional over reference sampling
    and does not rely on observing latent counts.
    """
    y=data['Y'][...,2]/C[None]
    r=data['REF'][...,2]/reference_size
    nrep=len(y)
    accepted=np.ones((nrep,NC),dtype=bool)
    train_accept=np.ones_like(accepted)
    group_margins=[]
    for group_idx,(part,sites,round_index) in enumerate(GROUPS):
        yv=y[:,sites,round_index].reshape(nrep,-1)
        rv=r[:,sites,round_index].reshape(nrep,-1)
        aa=RATES[:,sites,round_index].reshape(NC,-1)
        active=ACTIVES[:,sites,round_index].reshape(NC,-1)
        cc=C[sites,round_index].reshape(-1)
        m=cc.size
        # Shape (replicates, candidate models): residual = (1-a)*reference - observed.
        residual=(rv@(1-aa).T)/m-yv.mean(axis=1,keepdims=True)
        radius=np.sqrt(.5*math.log(2*len(GROUPS)/alpha_familywise)*
                 (np.sum((1-aa)**2/reference_size+1/cc[None],axis=1)/m**2))
        rounding=.5*np.mean(1/cc)
        nuisance=natural_envelope*(1-aa).mean(axis=1)
        heterogeneity=QMAX*rate_envelope*active.mean(axis=1)
        threshold=radius+rounding+nuisance+heterogeneity
        accept=np.abs(residual)<=threshold[None,:]+1e-12
        if part=='training': train_accept &=accept
        accepted &=accept
        group_margins.append({'partition':part,'round':round_index+1,
                              'sections':int(m),
                              'maximum_H00_allowed_mean_difference':float(threshold[0]),
                              'H00_noise_radius':float(radius[0]),
                              'H00_nuisance_radius':float(nuisance[0])})
    final=accepted
    true_names=[f'{c.temporal}:{c.shape}:{c.amplitude:.2f}' for c in CANDIDATES]
    ampl=np.array([c.amplitude for c in CANDIDATES]);h=np.array([c.temporal for c in CANDIDATES])
    nmodels=np.sum(final,axis=1)
    amin=np.where(final,ampl[None],np.inf).min(axis=1)
    amax=np.where(final,ampl[None],-np.inf).max(axis=1)
    assert np.all(nmodels>0) or natural_envelope<TRUE_NATURAL_ENVELOPE or rate_envelope==0
    return {'train':train_accept,'final':final,'n_models':nmodels,
            'amplitude_min':np.where(np.isfinite(amin),amin,np.nan),
            'amplitude_max':np.where(np.isfinite(amax),amax,np.nan),
            'H00_retained':final[:,0],
            'H01_retained':final[:,h=='H01'].any(axis=1),
            'H10_retained':final[:,h=='H10'].any(axis=1),
            'H11_retained':final[:,h=='H11'].any(axis=1),
            'margins':group_margins,'candidate_names':true_names}


def exact_four_count_logpmf(y:np.ndarray,p:np.ndarray,rate:np.ndarray)->np.ndarray:
    """Exact integer multinomial observation likelihood under rounded B->W.

    Sum over all compatible *latent* B counts, which are unobserved. Valid for
    a fixed p and deterministic alpha; no Gaussian or continuous approximation.
    p has W,L,B,N order; y[...,4] is observed integer counts. Batch-vectorised.
    The number of compatible xB is small for alpha<=0.6. The analytic inverse
    interval is exhaustively scanned, with exact rounding verification.
    """
    yy=np.asarray(y,dtype=int)
    pp=np.broadcast_to(np.asarray(p,float),yy.shape)
    aa=np.broadcast_to(np.asarray(rate,float),yy.shape[:-1])
    if np.any(aa<0) or np.any(aa>.6):raise ValueError('Rate must be in [0,.6].')
    if np.any(pp<=0) or not np.allclose(pp.sum(axis=-1),1):raise ValueError('Invalid probabilities')
    tot=yy.sum(axis=-1)
    b=yy[...,2];w=yy[...,0]
    centre=np.floor(b/(1-aa)).astype(int)
    offsets=np.arange(-4,6)
    xB=centre[...,None]+offsets
    moved=xB-b[...,None]
    valid=(xB>=0)&(xB<=tot[...,None])&(moved>=0)&(moved<=w[...,None])
    valid &=xB-np.floor(aa[...,None]*np.maximum(xB,0)+.5).astype(int)==b[...,None]
    xW=w[...,None]-moved
    # Individual multinomial probability of each compatible latent vector.
    X=np.stack((xW,np.broadcast_to(yy[...,1,None],xW.shape),xB,
                np.broadcast_to(yy[...,3,None],xW.shape)),axis=-1)
    xgood=np.maximum(X,0)
    logp=gammaln(tot+1)[...,None]-np.sum(gammaln(xgood+1),axis=-1)
    logp+=np.sum(xgood*np.log(pp[...,None,:]),axis=-1)
    return logsumexp(np.where(valid,logp,-np.inf),axis=-1)


def exact_likelihood_demo(seed:int=20261204,n_worlds:int=120)->dict:
    """Oracle fixed-probability comparison: *not* a real-data identification test."""
    rng=np.random.default_rng(seed)
    true_rate=NOMINAL_ALPHA*shape_fn('step')*temporal_mask('H11')
    alt=Q.copy()
    alt[...,2]=qB*(1-true_rate)
    alt[...,0]=qW+qB*true_rate
    # The alternative has the same *expected* blank and beneficiary proportions
    # ignoring rounding O(1/C), but a different higher-order count distribution.
    # The inference code is given oracle Q here (explicit upper bound on ability).
    heldC=C[TEST_SITES]
    heldQ=Q[TEST_SITES]
    heldAlt=alt[TEST_SITES]
    heldRate=true_rate[TEST_SITES]
    scores={}
    for origin in ('deterministic_rounded','natural_mean_matched'):
        p=heldQ if origin=='deterministic_rounded' else heldAlt
        counts=draw_multinomial_via_binomial(rng,
              np.broadcast_to(heldC,(n_worlds,*heldC.shape)),
              np.broadcast_to(p,(n_worlds,*p.shape)))
        if origin=='deterministic_rounded':
            moved=np.floor(counts[...,2]*heldRate[None]+.5).astype(int)
            counts[...,0]+=moved;counts[...,2]-=moved
        L1=exact_four_count_logpmf(counts,heldQ[None],heldRate[None]).sum(axis=(1,2,3))
        L0=exact_four_count_logpmf(counts,heldAlt[None],np.zeros_like(heldRate)[None]).sum(axis=(1,2,3))
        delta=L1-L0
        scores[origin]={'worlds':n_worlds,'mean_ll_gain_rounded_over_natural':float(delta.mean()),
                        'sd_ll_gain':float(delta.std(ddof=1)),
                        'fraction_prefer_rounded':float((delta>0).mean()),
                        'min_gain':float(delta.min()),'max_gain':float(delta.max())}
    return {'oracle_assumption':'The four true source probabilities Q per section are known exactly to the scorer.',
            'heldout_sites':len(TEST_SITES),'observations_per_world':int(heldC.size),
            'rate':'H11 step amplitude 0.30, D0, deterministic half-up rounding',
            'natural_comparator':'Multinomial with matched first-order means; no transformation',
            'results':scores,
            'interpretation':'Only a controlled higher-order diagnostic; flexible unknown natural distributions can remove separation.'}


def cp_upper(x:int,n:int,confidence:float=.95)->float:
    from scipy.stats import beta
    return float(beta.ppf(confidence,x+1,n-x)) if x<n else 1.


def test_details(results:np.ndarray,scenario:str)->dict:
    if scenario=='H00' or scenario in ('natural_step','reference_bias'):
        return {'true_index':0,'true_temporal':'H00'}
    temporal=scenario[:3]
    idx=[i for i,c in enumerate(CANDIDATES)
         if c.temporal==temporal and c.shape=='step' and abs(c.amplitude-NOMINAL_ALPHA)<1e-12][0]
    return {'true_index':idx,'true_temporal':temporal}


def run(ref_sizes:list[int],nrep:int,seed:int,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    allrows=[];samples=[];seeds={};records=0
    scenarios=['H00','H01_D0','H10_D0','H11_D0','H11_D3','natural_step','reference_bias']
    for rn in ref_sizes:
        for si,sc in enumerate(scenarios):
            myseed=int(seed+10000*rn+97*si)
            rng=np.random.default_rng(myseed)
            dat=simulate(rng,nrep,rn,'H00' if sc=='reference_bias' else sc,
                         reference_bias=(sc=='reference_bias'))
            truth=test_details(np.empty(0),sc)
            nrep_dat=len(dat['Y']); records+=nrep_dat
            seeds[f'{rn}:{sc}']=myseed
            # Do not expose simulator's latent counts, p_B, rate or category means
            # to moment_confidence_sets; it receives only Y and independent REF.
            for d in NATURAL_ENVELOPES:
                for e in RATE_ENVELOPES:
                    inferred=moment_confidence_sets(dat,rn,d,e)
                    final=inferred['final'];train=inferred['train']
                    truth_retained=final[:,truth['true_index']]
                    # Configurations outside assumed d/e constraints must not be
                    # labelled coverage tests of a correctly specified model.
                    valid_d=(d>=TRUE_NATURAL_ENVELOPE)
                    if sc=='natural_step':
                        valid_d=d>=TRUE_NATURAL_ENVELOPE+NOMINAL_ALPHA*float(np.max(qB*shape_fn('step')))
                    if sc=='reference_bias':valid_d=d>=TRUE_NATURAL_ENVELOPE+.022
                    valid_e=(sc!='H11_D3' or e>=RATE_BOUND-1e-12)
                    valid=valid_d and valid_e
                    empty=int(np.sum(inferred['n_models']==0))
                    count=int(np.sum(truth_retained))
                    zero_retained=int(np.sum(inferred['H00_retained']))
                    report={
                        'scenario':sc,'reference_n':rn,'natural_envelope':d,
                        'rate_envelope':e,'n':nrep_dat,
                        'assumptions_correctly_cover_generator':bool(valid),
                        'true_candidate_retained_count':count,
                        'true_candidate_retained_rate':count/nrep_dat,
                        'true_candidate_retention_one_sided_95_lower':
                           1-cp_upper(nrep_dat-count,nrep_dat),
                        'H00_retained_count':zero_retained,
                        'H00_retained_rate':zero_retained/nrep_dat,
                        'H00_excluded_count':nrep_dat-zero_retained,
                        'H00_excluded_rate':1-zero_retained/nrep_dat,
                        'H00_exclusion_one_sided_95_upper':cp_upper(nrep_dat-zero_retained,nrep_dat),
                        'mean_identified_set_size':float(np.mean(inferred['n_models'])),
                        'median_identified_set_size':float(np.median(inferred['n_models'])),
                        'mean_training_set_size':float(np.mean(train.sum(axis=1))),
                        'empty_set_count':empty,
                        'H01_retained_rate':float(inferred['H01_retained'].mean()),
                        'H10_retained_rate':float(inferred['H10_retained'].mean()),
                        'H11_retained_rate':float(inferred['H11_retained'].mean()),
                        'mean_amplitude_width_nonempty':float(np.nanmean(
                            inferred['amplitude_max']-inferred['amplitude_min'])) if empty<nrep_dat else None}
                    allrows.append(report)
                    if (sc in ('H00','H11_D3','natural_step','reference_bias')
                            and rn in (75,1800) and d in (.0025,.035) and e==.055):
                        samples.append({'reference_n':rn,'scenario':sc,'d':d,'e':e,
                           'replicate':0,'candidate_set':[name for name,yes in zip(inferred['candidate_names'],final[0]) if yes],
                           'amplitude_bounds':[float(inferred['amplitude_min'][0]),float(inferred['amplitude_max'][0])]
                             if inferred['n_models'][0] else None,
                           'group_margins':inferred['margins']})
            print('completed',rn,sc,'worlds',nrep_dat,flush=True)
    exact=exact_likelihood_demo(seed=seed+123,n_worlds=120)
    result={
      'experiment':'EQ-PRB-001','version':'0.4','date':'2026-11-08',
      'language':'UK English','entirely_synthetic':True,
      'summary_status':'Exploratory partial-identification study; no unique mechanism identified',
      'references':{'previous_experiment':'EQ-PRB-001 v0.3','method':'Bonferroni over four group tests, McDiarmid bounded differences, finite-sample moment inversion'},
      'synthetic_geometry':{'municipalities':MUNICIPALITIES,'sites':N_SITES,
           'sections_per_site':SECTIONS_PER_SITE,'rounds':2,
           'training_sites':TRAIN_SITES.tolist(),'holdout_sites':TEST_SITES.tolist()},
      'candidate_library':{'n_candidates':NC,'candidates':[c._asdict() for c in CANDIDATES],
           'amplitudes':[.06,.12,.18,.24,.30,.36,.42],
           'shapes':['constant','step','logistic'],
           'temporal_patterns':['H00','H01','H10','H11']},
      'protocol':{'seed':seed,'reference_sizes':ref_sizes,'replications_per_scenario_precision':nrep,
           'independent_evaluation_worlds':records,'scenarios':scenarios,
           'natural_envelopes':list(NATURAL_ENVELOPES),'rate_envelopes':list(RATE_ENVELOPES),
           'assumed_baseline_probability_upper_bound':QMAX,
           'familywise_confidence':.95,'number_of_group_tests':len(GROUPS),
           'train_and_holdout_separated_by_entire_site':True,
           'random_rounded_transfer':'m=floor(alpha*latent_blank+0.5), Bobs=latent_blank-m',
           'no_posthoc_per_section_parameters':True,
           'notes':['A confidence set covers the exact grid candidate with >=95% theoretical probability only when every stated bound and sampling condition holds.',
            'The set is a finite-grid set, not a continuous confidence region for all possible equations.',
            'The true candidate parameter is deliberately on the pre-specified grid; this favours recovery.',
            'The procedure has no access to true latent counts, qB, site effects or random transfer rates.',
            'Correctness of the reference/natural envelope is not inferable from these count data alone.',
            'Ordinary natural step changes and biased independent reference samples are analysed as misspecification stress tests.']},
       'seeds_by_scenario_precision':seeds,
       'scores':allrows,'examples':samples,'exact_likelihood':exact,
       'identification_limit':{
         'statement':'Independent B->W binomial thinning of a multinomial component and a natural-only multinomial with shifted category probabilities can be exactly observationally equivalent.',
         'scope':'Stochastic independent thinning only; NOT exact equality for deterministic half-up integer rounding.',
         'consequence':'Even a valid partial-identification confidence set may remain broad or contain H00 despite a true simulated transformation.'}}
    (out/'results_v0.4.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    with (out/'identified_sets.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(allrows[0]));writer.writeheader();writer.writerows(allrows)
    (out/'examples.json').write_text(json.dumps(samples,indent=2)+'\n',encoding='utf-8')
    print('Finished:',records,'independent synthetic worlds;',len(allrows),'evaluations;',
          NC,'frozen candidate models')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,default=SEED)
    p.add_argument('--replicates',type=int,default=N_REPLICATES)
    p.add_argument('--reference-sizes',type=int,nargs='+',default=list(REFERENCE_SIZES))
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent)
    a=p.parse_args()
    run(a.reference_sizes,a.replicates,a.seed,a.out)
