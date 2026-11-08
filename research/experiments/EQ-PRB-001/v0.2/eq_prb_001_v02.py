#!/usr/bin/env python3
"""EQ-PRB-001 v0.2: synthetic latent-data mechanism identification.

All inputs are invented synthetic data. No real-world electoral datasets are read.
Inference observes only synthetic published counts, an *independent* synthetic
behavioural-reference sample, and pre-registered covariates/probabilities.
The latent pre-transformation counts are reserved for generator audit only.

Gaussian multilevel pseudo predictive scores on B-count contrasts, calibrated by
an independent, integer-count H00 simulation of the entire candidate search.
This is NOT an exact count likelihood or a causal claim.
"""
from __future__ import annotations
import csv, json, time
import scipy
from pathlib import Path
import numpy as np
from scipy.stats import beta as beta_dist, norm

ROOT=Path(__file__).resolve().parent
SEED=20261108
RNG=np.random.default_rng(SEED)
N_MUNI,N_LOC_PER_MUNI,N_SECT=5,8,8
NL=N_MUNI*N_LOC_PER_MUNI
T=2
S=NL*T*N_SECT
REF_N=1800 # Hypothetical high-information independent reference PER SECTION; not a realistic survey claim.
SIG_B_LOC=.006
SIG_B_SEC=.004
SIG_A_LOC=.11
SIG_A_SEC=.08
TRUE_A=.27
TRUE_SHAPE='step'
TRAIN_LOC=np.array([l for l in range(NL) if l%N_LOC_PER_MUNI not in (2,7)])
TEST_LOC=np.array([l for l in range(NL) if l%N_LOC_PER_MUNI in (2,7)])
N_CALIB=1500
N_EVAL=1000
ALPHAS=[.17,.27,.37]
SHAPES=['step','logistic']
D_CLASSES=['D0','D1','D2','D3']
TEMPORAL={'H00':(0,0),'H01':(0,1),'H10':(1,0),'H11':(1,1)}

loc=np.arange(NL)[:,None,None]
trn=np.arange(T)[None,:,None]
sec=np.arange(N_SECT)[None,None,:]
municipality=loc//N_LOC_PER_MUNI
# Fixed covariate depends only on section-local synthetic metadata, not outcomes.
z=np.broadcast_to(np.sin(.79*(loc+1)+.61*(sec+1)+.22*trn), (NL,T,N_SECT)).copy()
C=(290+(loc*13+sec*31+trn*19)%150).astype(int)
C=np.broadcast_to(C,(NL,T,N_SECT)).copy()
qB=np.clip(.069+.012*z+.004*np.sin(.83*loc+.5*trn),.03,.14)
qN=np.broadcast_to(.033+.005*np.cos(.5*sec+trn),qB.shape).copy()
qL=np.clip(.39-.055*z+.009*np.cos(.33*loc),.15,.65)
qW=1-qB-qN-qL
Q=np.stack([qW,qL,qB,qN],axis=-1)
assert np.max(np.abs(Q.sum(axis=-1)-1))<1e-12 and np.min(Q)>0

# X nuisance: arbitrary round-specific intercept + slope in z (4 coefficients).
X=np.zeros((NL,T,N_SECT,4))
for t in range(T):
    X[:,t,:,2*t]=1
    X[:,t,:,2*t+1]=z[:,t,:]
X=X.reshape(NL,T*N_SECT,4)
qflat=qB.reshape(NL,T*N_SECT)
Cflat=C.reshape(NL,T*N_SECT)
basevar=(qflat*(1-qflat)*(1/Cflat+1/REF_N)+SIG_B_SEC**2)
W0=(1/basevar[TRAIN_LOC]).reshape(-1)
Xtrain=X[TRAIN_LOC].reshape(-1,4)
Xtest=X[TEST_LOC].reshape(-1,4)
# Common frozen WLS for natural flexible nuisance per round; the test locations
# are not used in fitting. Candidate correction is deterministic and precomputed.
Bmat=np.linalg.solve(Xtrain.T@(W0[:,None]*Xtrain),Xtrain.T*W0[None,:])

def shape_fn(name):
    if name=='step':return .22+.78*(z>.12)
    if name=='logistic':return .20+.80/(1+np.exp(-5*(z-.12)))
    raise ValueError(name)

def active_mask(h):
    return np.asarray(TEMPORAL[h])[None,:,None].repeat(NL,axis=0).repeat(N_SECT,axis=2)

def make_candidate(h='H00',name='none',a=0.,d='D0'):
    active=active_mask(h)
    m=(qB * a * shape_fn(name) * active) if h!='H00' else np.zeros_like(qB)
    mu=m.reshape(NL,T*N_SECT)
    corr=(Bmat@mu[TRAIN_LOC].reshape(-1))
    projected_train=mu[TRAIN_LOC]-np.einsum('lsk,k->ls',X[TRAIN_LOC],corr)
    projected_test=mu[TEST_LOC]-np.einsum('lsk,k->ls',X[TEST_LOC],corr)
    return dict(h=h,shape=name,a=a,d=d,m=m,mu=mu,
                ptr=projected_train,pte=projected_test,
                sigma_a_loc=SIG_A_LOC if d in ('D2','D3') else 0.,
                sigma_a_sec=SIG_A_SEC if d in ('D1','D3') else 0.,
                active=active)

# Low-rank covariance: independent binomial/reference/section noise +
# location-shared natural variation + location-shared random conversion.
# Inverse and log-det via a 2 x 2 Woodbury identity; no section-wise free fits.
def cov_parts(model, locations):
    mu_active=(qB*model['active']).reshape(NL,T*N_SECT)[locations]
    diag=basevar[locations]+(model['sigma_a_sec']*mu_active)**2
    invd=1/diag
    p=mu_active
    b=SIG_B_LOC
    a=model['sigma_a_loc']
    s00=1+b*b*np.sum(invd,axis=1)
    s01=b*a*np.sum(invd*p,axis=1)
    s11=1+a*a*np.sum(invd*p*p,axis=1)
    det=s00*s11-s01*s01
    assert np.all(det>0)
    logdet=np.sum(np.log(diag),axis=1)+np.log(det)
    return invd,p,b,a,s00,s01,s11,det,logdet

def pseudo_logscore(residual,parts):
    # residual shape (replicates, locations, 16)
    w,p,b,a,s00,s01,s11,det,logdet=parts
    sr=np.sum(residual*w,axis=2)*b
    sp=np.sum(residual*w*p,axis=2)*a
    quad=np.sum(residual**2*w,axis=2)-((s11*sr*sr-2*s01*sr*sp+s00*sp*sp)/det)
    return -.5*np.sum(quad+logdet[None,:],axis=1)

MODELS=[make_candidate()]
for h in ('H01','H10','H11'):
    for shape in SHAPES:
        for a in ALPHAS:
            for d in D_CLASSES:
                MODELS.append(make_candidate(h,shape,a,d))
for m in MODELS:
    m['cov_train']=cov_parts(m,TRAIN_LOC)
    m['cov_test']=cov_parts(m,TEST_LOC)

# Draw integer latent counts and an independently sampled synthetic benchmark.
def simulate(nrep,h,d='D0',shape=TRUE_SHAPE,a=TRUE_A,natural_step=False):
    g=shape_fn(shape)
    natloc=RNG.normal(0,SIG_B_LOC,size=(nrep,NL,1,1))
    natsec=RNG.normal(0,SIG_B_SEC,size=(nrep,NL,T,N_SECT))
    pb=qB[None,:,:,:]+natloc+natsec
    if natural_step:  # no conversion: fully behavioural change with same signal shape
        pb-=a*qB[None,:,:,:]*g[None,:,:,:]*active_mask('H11')[None,:,:,:]
    pb=np.clip(pb,.003,.30)
    pw=qW[None,:,:,:]+qB[None,:,:,:]-pb
    # Generate exact multinomial counts via sequential binomials.
    bs=RNG.binomial(C[None,:,:,:],pb)
    rem=C[None,:,:,:]-bs
    ws=RNG.binomial(rem,np.clip(pw/(1-pb),0,1))
    rem2=rem-ws
    ls=RNG.binomial(rem2,np.clip(qL[None,:,:,:]/(qL+qN)[None,:,:,:],0,1))
    ns=rem2-ls
    latent=np.stack([ws,ls,bs,ns],axis=-1)
    assert np.array_equal(latent.sum(axis=-1),np.broadcast_to(C,bs.shape))
    active=active_mask(h)
    alphaloc=RNG.normal(0,SIG_A_LOC if d in ('D2','D3') else 0.,size=(nrep,NL,1,1))
    alphasec=RNG.normal(0,SIG_A_SEC if d in ('D1','D3') else 0.,size=(nrep,NL,T,N_SECT))
    alpha=np.clip(a*g[None,:,:,:]+alphaloc+alphasec,0,.85)*active[None,:,:,:]
    moved=np.minimum(bs,np.floor(alpha*bs+.5).astype(np.int64))
    Y=latent.copy(); Y[...,0]+=moved;Y[...,2]-=moved
    assert np.min(Y)>=0 and np.array_equal(Y.sum(axis=-1),np.broadcast_to(C,bs.shape))
    # An independent synthetic 1,800-trial reference sample for every section/turn.
    br=RNG.binomial(REF_N,qB,size=(nrep,NL,T,N_SECT))
    rr=REF_N-br
    wr=RNG.binomial(rr,qW/(1-qB))
    rr2=rr-wr
    lr=RNG.binomial(rr2,qL/(qL+qN))
    nr=rr2-lr
    REF=np.stack([wr,lr,br,nr],axis=-1)
    assert np.all(REF.sum(axis=-1)==REF_N)
    return dict(Y=Y,REF=REF,latent=latent,alpha=alpha,moved=moved,natural_step=natural_step)

def score_full_search(data):
    Y,REF=data['Y'],data['REF']
    nrep=len(Y)
    d=(REF[...,2]/REF_N-Y[...,2]/C).reshape(nrep,NL,T*N_SECT)
    dtrain=d[:,TRAIN_LOC].reshape(nrep,-1)
    beta=dtrain@Bmat.T
    rtr=d[:,TRAIN_LOC]-np.einsum('rj,lsj->rls',beta,X[TRAIN_LOC])
    rte=d[:,TEST_LOC]-np.einsum('rj,lsj->rls',beta,X[TEST_LOC])
    train_scores=np.empty((nrep,len(MODELS)))
    test_scores=np.empty_like(train_scores)
    for i,m in enumerate(MODELS):
        train_scores[:,i]=pseudo_logscore(rtr-m['ptr'][None,:,:],m['cov_train'])
        test_scores[:,i]=pseudo_logscore(rte-m['pte'][None,:,:],m['cov_test'])
    selected=np.argmax(train_scores,axis=1)
    delta=test_scores[np.arange(nrep),selected]-test_scores[:,0]
    return dict(selected=selected,delta=delta,beta=beta,rtr=rtr,rte=rte,
                train_scores=train_scores,test_scores=test_scores)

def coverage_metrics(data,fit):
    Y=data['Y'][:,TEST_LOC,:,:,:]
    REF=data['REF'][:,TEST_LOC,:,:,:]
    selected=fit['selected']
    R=len(Y)
    probs=REF/REF_N
    # Posterior predictive mean as independent reference + fitted round-specific
    # natural drift + selected hypothetical synthetic transform. No true X used.
    shifts=np.empty((R,len(TEST_LOC),T*N_SECT),dtype=float)
    sigB=np.empty_like(shifts)
    for idx,m in enumerate(MODELS):
        take=selected==idx
        if not np.any(take):continue
        shifts[take]=np.einsum('rj,lsj->rls',fit['beta'][take],X[TEST_LOC])+m['mu'][TEST_LOC][None,:,:]
        active=(qB*m['active']).reshape(NL,T*N_SECT)[TEST_LOC]
        sigB[take]=np.sqrt(basevar[TEST_LOC][None,:,:]+SIG_B_LOC**2+
            (m['sigma_a_sec']*active)[None,:,:]**2 +
            (m['sigma_a_loc']*active)[None,:,:]**2)
    shifts=shifts.reshape(R,len(TEST_LOC),T,N_SECT)
    sigB=sigB.reshape(R,len(TEST_LOC),T,N_SECT)
    pred=probs.copy()
    wb_pair=pred[...,0]+pred[...,2]
    pred[...,2]=np.clip(pred[...,2]-shifts,0,wb_pair)
    pred[...,0]=wb_pair-pred[...,2]
    assert np.max(np.abs(pred.sum(axis=-1)-1))<1e-12
    # W uncertainty includes same natural/transform perturbations as B, plus
    # independent first-order anchor/count sampling for the W category.
    sigW=np.sqrt(qW[None,TEST_LOC,:,:]*(1-qW[None,TEST_LOC,:,:])*
                 (1/C[None,TEST_LOC,:,:]+1/REF_N) +
                 np.maximum(0,sigB**2-(qB[None,TEST_LOC,:,:]*(1-qB[None,TEST_LOC,:,:])*
                 (1/C[None,TEST_LOC,:,:]+1/REF_N))))
    sigL=np.sqrt(qL[None,TEST_LOC,:,:]*(1-qL[None,TEST_LOC,:,:])*
                 (1/C[None,TEST_LOC,:,:]+1/REF_N))
    sigN=np.sqrt(qN[None,TEST_LOC,:,:]*(1-qN[None,TEST_LOC,:,:])*
                 (1/C[None,TEST_LOC,:,:]+1/REF_N))
    sigL=np.broadcast_to(sigL,sigB.shape)
    sigN=np.broadcast_to(sigN,sigB.shape)
    sigma=np.stack([sigW,sigL,sigB,sigN],axis=-1)
    observed=Y/C[None,TEST_LOC,:,:,None]
    ci={}
    for level in (.50,.80,.95):
        zcrit=norm.ppf((1+level)/2)
        lo=np.maximum(0,pred-zcrit*sigma)
        hi=np.minimum(1,pred+zcrit*sigma)
        covered=(observed>=lo)&(observed<=hi)
        ci[str(int(100*level))]={
            name:{'coverage':float(covered[...,j].mean()),
                  'mean_width_pp':float(100*(hi[...,j]-lo[...,j]).mean())}
            for j,name in enumerate(('W','L','B','N'))}
    # Bonferroni 95%-family simultaneous rectangle, per synthetic section/round
    zcrit=norm.ppf(1-.05/8)
    lo=np.maximum(0,pred-zcrit*sigma);hi=np.minimum(1,pred+zcrit*sigma)
    joint=((observed>=lo)&(observed<=hi)).all(axis=-1).mean()
    return dict(marginal=ci,simultaneous_four_95_bonferroni_coverage=float(joint),
                n_holdout_section_round_observations=int(observed.shape[0]*observed.shape[1]*observed.shape[2]*observed.shape[3]))

def cp_one_sided_95(x,n):
    return float(beta_dist.ppf(.95,x+1,n-x)) if x<n else 1.

def main():
    ts=time.monotonic()
    # Separate calibration draws. Calibrate the ENTIRE adaptive model search,
    # including comparison against the natural-only model and heldout scoring.
    calibration=score_full_search(simulate(N_CALIB,'H00','D0'))
    # 97.5% quantile as a conservative gate to aim at <=5% upper CI.
    threshold=max(0.,float(np.quantile(calibration['delta'],.975,method='higher')))
    scenarios=[('H00','D0'),*[(h,d) for h in ('H01','H10','H11') for d in D_CLASSES]]
    results=[]
    example=None
    stress=None
    for h,d in scenarios+[('H00-natural-shift','D0')]:
        data=simulate(N_EVAL,'H00' if h=='H00-natural-shift' else h,d,
                      natural_step=(h=='H00-natural-shift'))
        fit=score_full_search(data)
        detection=fit['delta']>threshold
        sel=fit['selected']
        n_detect=int(detection.sum())
        r={'generator':h,'d_class':d,'n_eval':N_EVAL,
           'rejection_threshold':threshold,
           'detections':n_detect,'detection_rate':n_detect/N_EVAL,
           'upper_one_sided_95_ci_detection_rate':cp_one_sided_95(n_detect,N_EVAL),
           'selected_H00_fraction':float((sel==0).mean()),
           'correct_temporal_scenario_fraction':float(np.mean([MODELS[int(k)]['h']==h for k in sel])) if h in TEMPORAL else None,
           'correct_D_fraction_positives':float(np.mean([MODELS[int(k)]['d']==d for k in sel])) if h not in ('H00','H00-natural-shift') else None,
           'mean_test_score_improvement':float(fit['delta'].mean()),
           'median_test_score_improvement':float(np.median(fit['delta']))}
        results.append(r)
        print(f"{h:18s} {d} detect {n_detect:4d}/{N_EVAL}={n_detect/N_EVAL:.3f} "
              f"temp_correct={r['correct_temporal_scenario_fraction']} ",flush=True)
        if (h,d)==('H11','D3'):
            # Use last 1000 complete integer-count replicates for interval coverage.
            r['predictive_intervals_holdout']=coverage_metrics(data,fit)
            # Preserve exactly one draw in a small, readable CSV to audit counts.
            example=dict(Y=data['Y'][0],REF=data['REF'][0],latent=data['latent'][0],
                         alpha=data['alpha'][0],moved=data['moved'][0],selected=int(sel[0]),
                         beta=fit['beta'][0].tolist())
    no=next(x for x in results if x['generator']=='H00')
    signal=[x for x in results if x['generator'] in ('H01','H10','H11')]
    found=all(x['detection_rate']>=.80 for x in signal)
    false_ok=no['upper_one_sided_95_ci_detection_rate']<=.05
    # Strict claims: exceedances correspond to this frozen synthetic benchmark only.
    out={'id':'EQ-PRB-001','version':'0.2','date':'2026-11-08','synthetic_only':True,
         'parent_version':'0.1','seed':SEED,'numpy_version':np.__version__,'scipy_version':scipy.__version__,
         'reference_sample_size_per_section_turn':REF_N,
         'reference_design':'independent hypothetical sample, informative and not claimed available in real elections',
         'sections':NL*N_SECT,'locations':NL,'municipalities':N_MUNI,
         'train_sections':len(TRAIN_LOC)*N_SECT,'test_sections':len(TEST_LOC)*N_SECT,
         'holdout':'two whole locations per municipality; independent by location, across BOTH turns',
         'model_library_size':len(MODELS),'candidate_temporal_scenarios':list(TEMPORAL),
         'candidate_shapes':SHAPES,'candidate_amplitudes':ALPHAS,'candidate_random_effects':D_CLASSES,
         'null_calibration_replicates':N_CALIB,'independent_evaluation_replicates_per_generator':N_EVAL,
         'calibration_threshold_conservative_97_5_percentile':threshold,
         'results':results,'all_positive_meet_80_percent_power':bool(found),
         'null_upper_95_less_equal_5_percent':bool(false_ok),
         'model_assumptions':{'mechanism':'B -> W integer rounding; exact count conservation',
           'latent_X':'unknown to scoring process, used only to generate and audit synthetic data',
           'score':'Gaussian multivariate pseudo log predictive density on independent-reference minus observed B proportions',
           'nuisance':'round-specific intercept and slope of z fit only on training locations',
           'natural_location_sd':SIG_B_LOC,'natural_section_sd':SIG_B_SEC,
           'conversion_location_rate_sd':SIG_A_LOC,'conversion_section_rate_sd':SIG_A_SEC,
           'true_mean_rate_amplitude':TRUE_A,'true_shape':TRUE_SHAPE,
           'true_alpha_formula':'clip(a*g(z)+u_location+v_section,0,0.85), active rounds only',
           'selection':'train score maximization across all candidates including H00; independent test score difference vs H00; 97.5% null calibration of entire selection',
           'test_uses_latent_counts':False},
         'limitations':['Gaussian score is approximate; the synthetic generator uses integer multinomial counts and integer rounding.',
                        'The data generator, covariance family and candidate library share structural assumptions.',
                        'The independent synthetic reference is unusually informative; results depend on its precision.',
                        'Conversion D classes may be unidentifiable under similar natural behavioural random effects.',
                        'The H00-natural-shift stress generator changes preferences without any conversion, creating signal-shaped natural behaviour.',
                        'No election data, no empirical claim about any actual election or system.',
                        'The four-category intervals are Gaussian/marginal approximations, not exact joint count likelihoods.',
                        'Across turns, synthetic first/second-round counts are linked via shared location and covariate, not a full survey-based behavioural transfer matrix.',
                        'Unrestricted behavioural functions and unconstrained latent X can recreate observed counts without transformation.'],
         'execution_duration_is_not_part_of_reproducible_results':True}
    if example is not None:
        with (ROOT/'synthetic_holdout_example.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f)
            w.writerow(['municipality','location','section','round','turnout','z',
                        'latent_W','latent_L','latent_B','latent_N','observed_W','observed_L','observed_B','observed_N',
                        'reference_W','reference_L','reference_B','reference_N','true_alpha','moved_B_to_W','partition'])
            for l in range(NL):
                for t in range(T):
                    for s in range(N_SECT):
                        w.writerow([l//N_LOC_PER_MUNI,l,s,t+1,int(C[l,t,s]),float(z[l,t,s]),
                                    *map(int,example['latent'][l,t,s]),*map(int,example['Y'][l,t,s]),
                                    *map(int,example['REF'][l,t,s]),float(example['alpha'][l,t,s]),
                                    int(example['moved'][l,t,s]),'test' if l in TEST_LOC else 'train'])
    with (ROOT/'calibration_results.csv').open('w',newline='',encoding='utf-8') as f:
        cols=['generator','d_class','n_eval','rejection_threshold','detections','detection_rate',
              'upper_one_sided_95_ci_detection_rate','selected_H00_fraction','correct_temporal_scenario_fraction',
              'correct_D_fraction_positives','mean_test_score_improvement','median_test_score_improvement']
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for r in results:w.writerow({k:r.get(k) for k in cols})
    (ROOT/'results_v0.2.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
    print('RESULTS_DONE',out['all_positive_meet_80_percent_power'],out['null_upper_95_less_equal_5_percent'],
          'elapsed',round(time.monotonic()-ts,3),flush=True)

if __name__=='__main__':main()
