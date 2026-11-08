#!/usr/bin/env python3
"""EQ-PRB-001 v0.3 — synthetic partial identification and prediction calibration.

UK English. NO real election data are loaded. All data are synthetic.
The observable data are integer category counts and an independently generated
reference sample; latent pre-transformation votes are never passed to fitting.
Reproduces the v0.2 Gaussian pseudo-score, and adds competing natural drifts,
independent precision sweeps, an explicitly composite H00 reference, and
split-calibrated marginal and four-category simultaneous prediction intervals.

Not an exact latent integer likelihood; not a claim about actual electoral data.
"""
from __future__ import annotations
import argparse
import csv
import json
import time
from pathlib import Path
import numpy as np
from scipy.stats import beta as beta_dist, norm
import scipy

HERE=Path(__file__).resolve().parent
SEED=20261108
MUNICIPALITIES=5
LOCS_PER_MUNI=8
SECTS_PER_LOC=8
NL=MUNICIPALITIES*LOCS_PER_MUNI
T=2
TRAIN=np.array([l for l in range(NL) if l%LOCS_PER_MUNI not in (2,7)])
TEST=np.array([l for l in range(NL) if l%LOCS_PER_MUNI in (2,7)])
SIG_B_LOC=.006
SIG_B_SEC=.004
SIG_A_LOC=.11
SIG_A_SEC=.08
A=.27
SHAPES=('step','logistic')
AMPLITUDES=(.17,.27,.37)
D_CLASSES=('D0','D1','D2','D3')
TEMPORAL={'H00':(0,0),'H01':(0,1),'H10':(1,0),'H11':(1,1)}

loc=np.arange(NL)[:,None,None]
trn=np.arange(T)[None,:,None]
sec=np.arange(SECTS_PER_LOC)[None,None,:]
z=np.broadcast_to(np.sin(.79*(loc+1)+.61*(sec+1)+.22*trn), (NL,T,SECTS_PER_LOC)).copy()
C=(290+(loc*13+sec*31+trn*19)%150).astype(int)
C=np.broadcast_to(C,(NL,T,SECTS_PER_LOC)).copy()
qB=np.clip(.069+.012*z+.004*np.sin(.83*loc+.5*trn),.03,.14)
qN=np.broadcast_to(.033+.005*np.cos(.5*sec+trn),qB.shape).copy()
qL=np.clip(.39-.055*z+.009*np.cos(.33*loc),.15,.65)
qW=1-qB-qN-qL
Q=np.stack((qW,qL,qB,qN),axis=-1)
assert np.min(Q)>0 and np.allclose(Q.sum(axis=-1),1)

def shape_fn(name):
    if name=='step':return .22+.78*(z>.12)
    if name=='logistic':return .20+.80/(1+np.exp(-5*(z-.12)))
    if name=='quadratic':return .18+.82*((z+1)/2)**2
    if name=='none':return np.zeros_like(z)
    raise ValueError(name)

def mask(h):
    return np.broadcast_to(np.array(TEMPORAL[h])[None,:,None],qB.shape)

def make_design(kind):
    # Columns do not depend on any generated outcomes. Round-specific pooled basis.
    feats=[]
    for t in range(T):
        indicator=np.broadcast_to((trn==t),qB.shape).astype(float)
        feats.extend([indicator,indicator*z])
        if kind in ('quadratic','behavioural-envelope'):
            feats.append(indicator*z*z)
        if kind=='behavioural-envelope':
            # Exact signal-shaped natural preferences are admissible as nuisance.
            feats.extend([indicator*qB*shape_fn(s) for s in SHAPES])
    return np.stack(feats,axis=-1).reshape(NL,T*SECTS_PER_LOC,-1)

class Search:
    def __init__(self,ref_n,design):
        self.ref_n=int(ref_n)
        self.design=design
        self.X=make_design(design)
        self.qflat=qB.reshape(NL,T*SECTS_PER_LOC)
        self.basevar=(self.qflat*(1-self.qflat)*(1/C.reshape(NL,-1)+1/ref_n)+SIG_B_SEC**2)
        w=(1/self.basevar[TRAIN]).reshape(-1)
        xt=self.X[TRAIN].reshape(-1,self.X.shape[-1])
        self.Bmat=np.linalg.solve(xt.T@(w[:,None]*xt),xt.T*w[None,:])
        self.models=[]
        self.add('H00','none',0.,'D0')
        for h in ('H01','H10','H11'):
            for shape in SHAPES:
                for a in AMPLITUDES:
                    for d in D_CLASSES:
                        self.add(h,shape,a,d)
        assert len(self.models)==73

    def add(self,h,shape,a,d):
        active=mask(h)
        mu=(qB*a*shape_fn(shape)*active).reshape(NL,T*SECTS_PER_LOC)
        corr=self.Bmat@mu[TRAIN].reshape(-1)
        ptr=mu[TRAIN]-np.einsum('lsk,k->ls',self.X[TRAIN],corr)
        pte=mu[TEST]-np.einsum('lsk,k->ls',self.X[TEST],corr)
        sl=SIG_A_LOC if d in ('D2','D3') else 0.
        ss=SIG_A_SEC if d in ('D1','D3') else 0.
        self.models.append(dict(h=h,shape=shape,a=a,d=d,active=active,mu=mu,
                                ptr=ptr,pte=pte,sigloc=sl,sigsec=ss,
                                train_cov=self.cov(active,sl,ss,TRAIN),
                                test_cov=self.cov(active,sl,ss,TEST)))

    def cov(self,active,sigloc,sigsec,subset):
        p=(qB*active).reshape(NL,T*SECTS_PER_LOC)[subset]
        diag=self.basevar[subset]+(sigsec*p)**2
        w=1/diag
        b=SIG_B_LOC;a=sigloc
        s00=1+b*b*np.sum(w,axis=1)
        s01=b*a*np.sum(w*p,axis=1)
        s11=1+a*a*np.sum(w*p*p,axis=1)
        det=s00*s11-s01*s01
        assert np.all(det>0)
        logdet=np.sum(np.log(diag),axis=1)+np.log(det)
        return w,p,b,a,s00,s01,s11,det,logdet

    @staticmethod
    def score(r,cov):
        w,p,b,a,s00,s01,s11,det,logdet=cov
        sr=np.sum(r*w,axis=2)*b
        sp=np.sum(r*w*p,axis=2)*a
        quad=np.sum(r*r*w,axis=2)-(s11*sr*sr-2*s01*sr*sp+s00*sp*sp)/det
        return -.5*np.sum(quad+logdet[None,:],axis=1)

    def fit(self,data):
        Y,R=data['Y'],data['REF']
        n=len(Y)
        diff=(R[...,2]/self.ref_n-Y[...,2]/C).reshape(n,NL,T*SECTS_PER_LOC)
        beta=diff[:,TRAIN].reshape(n,-1)@self.Bmat.T
        train_res=diff[:,TRAIN]-np.einsum('rj,lsj->rls',beta,self.X[TRAIN])
        test_res=diff[:,TEST]-np.einsum('rj,lsj->rls',beta,self.X[TEST])
        trains=np.empty((n,len(self.models)),dtype=float)
        tests=np.empty_like(trains)
        for i,m in enumerate(self.models):
            trains[:,i]=self.score(train_res-m['ptr'][None,:,:],m['train_cov'])
            tests[:,i]=self.score(test_res-m['pte'][None,:,:],m['test_cov'])
        selected=np.argmax(trains,axis=1)
        delta=tests[np.arange(n),selected]-tests[:,0]
        return {'selected':selected,'delta':delta,'beta':beta,
                'train_scores':trains,'test_scores':tests}

    def predictive_arrays(self,data,fit):
        """Prediction does not use simulator-only latent counts, alpha or moved."""
        Y=data['Y'][:,TEST]
        R=data['REF'][:,TEST]
        idx=fit['selected'];n=len(idx)
        shifts=np.empty((n,len(TEST),T*SECTS_PER_LOC))
        sigmaB=np.empty_like(shifts)
        for k,m in enumerate(self.models):
            use=np.flatnonzero(idx==k)
            if len(use)==0:continue
            shifts[use]=np.einsum('rj,lsj->rls',fit['beta'][use],self.X[TEST])+m['mu'][TEST][None,:,:]
            p=(qB*m['active']).reshape(NL,T*SECTS_PER_LOC)[TEST]
            sigmaB[use]=np.sqrt(self.basevar[TEST][None,:,:]+SIG_B_LOC**2+
                    (m['sigloc']*p[None,:,:])**2+(m['sigsec']*p[None,:,:])**2)
        shifts=shifts.reshape(n,len(TEST),T,SECTS_PER_LOC)
        sigmaB=sigmaB.reshape(n,len(TEST),T,SECTS_PER_LOC)
        pred=R/self.ref_n
        wb=pred[...,0]+pred[...,2]
        pred[...,2]=np.clip(pred[...,2]-shifts,0,wb)
        pred[...,0]=wb-pred[...,2]
        # Approximation retained from v0.2 for an interpretable controlled comparison.
        varW=qW[None,TEST]*(1-qW[None,TEST])*(1/C[None,TEST]+1/self.ref_n)
        varB=qB[None,TEST]*(1-qB[None,TEST])*(1/C[None,TEST]+1/self.ref_n)
        sigmaW=np.sqrt(varW+np.maximum(0,sigmaB**2-varB))
        sigmaL=np.broadcast_to(np.sqrt(qL[None,TEST]*(1-qL[None,TEST])*(1/C[None,TEST]+1/self.ref_n)),sigmaB.shape)
        sigmaN=np.broadcast_to(np.sqrt(qN[None,TEST]*(1-qN[None,TEST])*(1/C[None,TEST]+1/self.ref_n)),sigmaB.shape)
        sigma=np.stack((sigmaW,sigmaL,sigmaB,sigmaN),axis=-1)
        obs=Y/C[None,TEST,:,:,None]
        assert np.allclose(pred.sum(axis=-1),1.)
        return obs,pred,sigma

def simulate(rng,n,ref_n,h='H00',d='D0',natural='none',a=A,shape='step'):
    g=shape_fn(shape)
    natloc=rng.normal(0,SIG_B_LOC,size=(n,NL,1,1))
    natsec=rng.normal(0,SIG_B_SEC,size=(n,NL,T,SECTS_PER_LOC))
    pb=qB[None]+natloc+natsec
    # Entire natural shift is from ordinary preferences, not a transformation.
    if natural!='none':
        pb=pb-a*qB[None]*shape_fn(natural)[None]*mask('H11')[None]
    pb=np.clip(pb,.003,.30)
    pw=qW[None]+qB[None]-pb
    bs=rng.binomial(C[None],pb)
    rem=C[None]-bs
    ws=rng.binomial(rem,np.clip(pw/(1-pb),0,1))
    rem2=rem-ws
    ls=rng.binomial(rem2,np.clip(qL[None]/(qL+qN)[None],0,1))
    ns=rem2-ls
    latent=np.stack((ws,ls,bs,ns),axis=-1)
    active=mask(h)
    al=rng.normal(0,SIG_A_LOC if d in ('D2','D3') else 0.,size=(n,NL,1,1))
    ass=rng.normal(0,SIG_A_SEC if d in ('D1','D3') else 0.,size=(n,NL,T,SECTS_PER_LOC))
    alpha=np.clip(a*g[None]+al+ass,0,.85)*active[None]
    moved=np.minimum(bs,np.floor(alpha*bs+.5).astype(int))
    Y=latent.copy();Y[...,0]+=moved;Y[...,2]-=moved
    assert np.all(Y>=0) and np.array_equal(Y.sum(axis=-1),np.broadcast_to(C,bs.shape))
    br=rng.binomial(ref_n,qB,size=(n,NL,T,SECTS_PER_LOC))
    rr=ref_n-br
    wr=rng.binomial(rr,qW/(1-qB))
    rr2=rr-wr
    lr=rng.binomial(rr2,qL/(qL+qN))
    nr=rr2-lr
    REF=np.stack((wr,lr,br,nr),axis=-1)
    assert np.all(REF.sum(axis=-1)==ref_n)
    return {'Y':Y,'REF':REF}

def cp_upper(x,n):
    return float(beta_dist.ppf(.95,x+1,n-x)) if x<n else 1.

def threshold_from_nulls(calibration,quantile=.975):
    """Conservative maximum of familywise search-score null quantiles."""
    return float(max(0.,*(np.quantile(x,quantile,method='higher') for x in calibration.values())))

def errors_for_calibration(search,data,fit):
    obs,pred,sigma=search.predictive_arrays(data,fit)
    zscore=np.abs(obs-pred)/np.maximum(sigma,1e-12)
    return zscore,obs,pred,sigma

def interval_calibration(zscore,levels=(.50,.80,.95)):
    # Calibration replicates are separate from test replicates.
    qs={}
    for level in levels:
        qs[str(int(level*100))]=[float(np.quantile(zscore[...,j],level,method='higher')) for j in range(4)]
    # An exact-data-generating-model calibration of the max statistic across four
    # categories. The same fitted mechanism selection is applied in both splits.
    qs['simultaneous95']=float(np.quantile(np.max(zscore,axis=-1),.95,method='higher'))
    return qs

def interval_assessment(zscore,obs,pred,sigma,calib):
    result={'marginal':{},'simultaneous95':{},'n_test_observations':int(np.prod(obs.shape[:-1]))}
    for level in (.50,.80,.95):
        name=str(int(level*100))
        rows={}
        for j,cat in enumerate(('W','L','B','N')):
            raw=norm.ppf((1+level)/2)
            tuned=calib[name][j]
            o,p,s=obs[...,j],pred[...,j],sigma[...,j]
            def one(k):
                lo=np.clip(p-k*s,0,1);hi=np.clip(p+k*s,0,1)
                return {'coverage':float(((o>=lo)&(o<=hi)).mean()),
                        'mean_width_percentage_points':float(100*(hi-lo).mean())}
            rows[cat]={'raw':one(raw),'split_calibrated':one(tuned),
                       'calibrated_critical_value':float(tuned)}
        result['marginal'][name]=rows
    crit=calib['simultaneous95']
    rawcrit=norm.ppf(1-.05/8)
    for name,k in [('raw_bonferroni',rawcrit),('split_calibrated',crit)]:
        lo=np.clip(pred-k*sigma,0,1);hi=np.clip(pred+k*sigma,0,1)
        result['simultaneous95'][name]={'joint_coverage':float(np.all((obs>=lo)&(obs<=hi),axis=-1).mean()),
                                        'mean_total_width_percentage_points':float((100*(hi-lo).sum(axis=-1)).mean())}
    result['simultaneous95']['calibrated_critical_value']=crit
    return result

def equivalence_demonstration():
    # Exact conditional law for individual Bernoulli thinning: for any C,qW,qB,a,
    # Multinomial(C,qW,qL,qB,qN) followed by B->W iid thinning with rate alpha
    # has the same observed multinomial law as natural q'=(qW+a*qB,qL,(1-a)*qB,qN).
    # This is an analytical identity, not an empirical detection result.
    alpha=.27
    q=np.array([.48,.39,.09,.04]); qp=q.copy();qp[0]+=q[2]*alpha;qp[2]*=(1-alpha)
    assert abs(qp.sum()-1)<1e-12
    # Compare pgf coefficients for a one-vote outcome, which determines the
    # distribution for every fixed C by independence.
    pgf_thinned=np.array([q[0]+q[2]*alpha,q[1],q[2]*(1-alpha),q[3]])
    assert np.allclose(pgf_thinned,qp)
    return {'model':'independent B-to-W thinning, not deterministic rounding',
            'initial_probabilities':q.tolist(),'rate':alpha,
            'observed_probabilities_under_both_generators':qp.tolist(),
            'statement':'Exact observational equivalence for observed integer counts under multinomial voting with independent thinning versus unconstrained natural preference change; the reference sample has the same assumed pre-shift distribution in both models.',
            'qualification':'Deterministic half-up rounding from v0.2 is not claimed to be exactly distributionally equivalent.'}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--calib',type=int,default=1200)
    ap.add_argument('--eval',type=int,default=1000)
    ap.add_argument('--seed',type=int,default=SEED)
    ap.add_argument('--sizes',type=int,nargs='+',default=[1800,300,75])
    ap.add_argument('--out',type=Path,default=HERE)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    assert args.calib>=1000 and args.eval>=1000
    start=time.monotonic();rng=np.random.default_rng(args.seed)
    cases=[('H00','D0','none'),('H00','D0','step'),('H00','D0','logistic'),('H00','D0','quadratic'),
           ('H01','D0','none'),('H01','D3','none'),('H10','D3','none'),('H11','D0','none'),('H11','D3','none')]
    report={'experiment':'EQ-PRB-001','version':'0.3','date':'2026-11-08','language':'en-GB','seed':args.seed,
            'numpy_version':np.__version__,'scipy_version':scipy.__version__,
            'entirely_synthetic':True,'reference_sizes':args.sizes,
            'train_locations':TRAIN.tolist(),'test_locations':TEST.tolist(),
            'null_calibration_replicates_per_natural_generator':args.calib,
            'evaluation_replicates_per_generator':args.eval,
            'cases':[{'h':h,'d':d,'natural':natural} for h,d,natural in cases],
            'model_families':['restricted','quadratic','behavioural-envelope'],
            'method':'Gaussian covariance-adjusted pseudo-score, v0.2 style; reserved polling locations; full 73-candidate selection; composite H00 calibration',
            'composite_null':['none','step','logistic','quadratic'],
            'confidence':'one-sided exact Clopper–Pearson upper 95% binomial bound for null rejection, per null generator',
            'scores':[],'prediction_intervals':[],'equivalence':equivalence_demonstration()}
    for ref_n in report['reference_sizes']:
        searches={name:Search(ref_n,name) for name in report['model_families']}
        calibration={name:{} for name in searches}
        for natural in report['composite_null']:
            data=simulate(rng,args.calib,ref_n,natural=natural)
            for name,s in searches.items():
                calibration[name][natural]=s.fit(data)['delta']
        thresholds={name:{'restricted_null':threshold_from_nulls({'none':calibration[name]['none']}),
                          'composite_null':threshold_from_nulls(calibration[name]),
                          'per_natural_null_97_5_percentile':{n:float(np.quantile(x,.975,method='higher')) for n,x in calibration[name].items()}}
                    for name in searches}
        for name in searches:
            print('THRESHOLD',ref_n,name,thresholds[name]['restricted_null'],thresholds[name]['composite_null'],flush=True)
        for h,d,natural in cases:
            data=simulate(rng,args.eval,ref_n,h=h,d=d,natural=natural)
            for name,s in searches.items():
                fit=s.fit(data);selected=fit['selected']
                temp=np.mean([s.models[int(k)]['h']==h for k in selected]) if h!='H00' else None
                row={'reference_n':ref_n,'design':name,'generator':h,'D':d,'natural':natural,
                     'n':args.eval,'null_threshold_restricted':thresholds[name]['restricted_null'],
                     'null_threshold_composite':thresholds[name]['composite_null'],
                     'false_or_detection_rate_restricted':float(np.mean(fit['delta']>thresholds[name]['restricted_null'])),
                     'false_or_detection_rate_composite':float(np.mean(fit['delta']>thresholds[name]['composite_null'])),
                     'count_restricted':int(np.count_nonzero(fit['delta']>thresholds[name]['restricted_null'])),
                     'count_composite':int(np.count_nonzero(fit['delta']>thresholds[name]['composite_null'])),
                     'selected_H00_fraction':float(np.mean(selected==0)),
                     'selected_true_temporal_fraction':float(temp) if temp is not None else None,
                     'test_delta_mean':float(np.mean(fit['delta'])),
                     'test_delta_median':float(np.median(fit['delta']))}
                if h=='H00':
                    row['upper_one_sided95_composite_null']=cp_upper(row['count_composite'],args.eval)
                    row['upper_one_sided95_restricted_null']=cp_upper(row['count_restricted'],args.eval)
                report['scores'].append(row)
                print('EVAL',ref_n,name,h,d,natural,'restricted',row['count_restricted'],
                      'composite',row['count_composite'],flush=True)
            # Interval calibration H00 baseline, H01-D3 and H11-D3, restricted design.
            if (h,d,natural) in [('H00','D0','none'),('H01','D3','none'),('H11','D3','none')]:
                s=searches['restricted'];fit=s.fit(data)
                holdout_z,obs,pred,sigma=errors_for_calibration(s,data,fit)
                independent=simulate(rng,args.calib,ref_n,h=h,d=d)
                independent_fit=s.fit(independent)
                calib=interval_calibration(errors_for_calibration(s,independent,independent_fit)[0])
                intervals=interval_assessment(holdout_z,obs,pred,sigma,calib)
                report['prediction_intervals'].append({'reference_n':ref_n,'generator':h,'D':d,
                    'design':'restricted','calibration_replicates':args.calib,
                    'test_replicates':args.eval,'quantiles':calib,'assessment':intervals})
    # Nonidentifiability and decision safeguard: abstain on mechanistic attribution
    # if natural generator family contains an observationally equivalent process.
    null_rows=[r for r in report['scores'] if r['generator']=='H00']
    report['composite_false_alarm_control_on_tested_nulls']=all(r['upper_one_sided95_composite_null']<=.05 for r in null_rows)
    signal_rows=[r for r in report['scores'] if r['generator']!='H00']
    report['all_tested_signals_meet_80_percent_detection']=all(r['false_or_detection_rate_composite']>=.8 for r in signal_rows)
    report['mechanism_identified']=False
    report['interpretation']='Model discrimination is only conditional on the specified admissible behavioural class. Exact observational equivalence prohibits unique mechanism identification without extra independent constraints.'
    report['limits']=[
        'All numbers and reference samples are synthetic; no real election information is used.',
        'Reference probability qB is an oracle design function known to the fitted candidate family, an additional simulation advantage.',
        'The score is Gaussian approximate; deterministic half-up integer transforms are applied in the generator.',
        'Intervals are marginal or per-section simultaneous across four categories, not simultaneous across the full election.',
        'Intervals are calibrated on the same named generator family but different independent replicates; transport to another generator is untested.',
        'The behavioural-envelope design includes signal-shaped covariates; it is a sensitivity analysis, not a causal identification model.',
        'The composite-null calibration is a finite battery of four natural generators, not a certification for all natural behavioural changes.',
        'No empirical power or false-alarm claim for the 2026 election, and no inference about any electoral infrastructure.',
    ]
    (args.out/'results_v0.3.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (args.out/'model_comparison.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(report['scores'][0]));w.writeheader();w.writerows(report['scores'])
    with (args.out/'intervals.csv').open('w',newline='',encoding='utf-8') as f:
        cols=['reference_n','generator','D','level','category','raw_coverage','calibrated_coverage','raw_mean_width_pp','calibrated_mean_width_pp','calibrated_critical']
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for p in report['prediction_intervals']:
            for level,categories in p['assessment']['marginal'].items():
                for cat,m in categories.items():
                    w.writerow(dict(reference_n=p['reference_n'],generator=p['generator'],D=p['D'],level=level,category=cat,
                                    raw_coverage=m['raw']['coverage'],calibrated_coverage=m['split_calibrated']['coverage'],
                                    raw_mean_width_pp=m['raw']['mean_width_percentage_points'],
                                    calibrated_mean_width_pp=m['split_calibrated']['mean_width_percentage_points'],
                                    calibrated_critical=m['calibrated_critical_value']))
    duration=round(time.monotonic()-start,2)
    print('FINISHED',len(report['scores']),'comparison rows;',len(report['prediction_intervals']),
          'interval trials;',duration,'seconds; composite H00 control',report['composite_false_alarm_control_on_tested_nulls'],
          'all test signal power',report['all_tested_signals_meet_80_percent_detection'],flush=True)

if __name__=='__main__':main()
