#!/usr/bin/env python3
"""Synthetic external-site calibration and partial-identification engine, v0.6–0.12.

UK English. All counts are fabricated; no observed election data are loaded.
The tested mathematical transformation transfers a rounded quantity from one
synthetic category to another while conserving every site's turnout exactly.

IMPORTANT: site-level conformal bounds are marginal under source-target site
exchangeability for the no-transformation score. They DO NOT by themselves
certify simultaneous 10-site 95% coverage or the confidence set under a
positive transformation; those claims are assessed empirically only.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np

SEED=20261108
AMPLITUDE=.377
CATEGORY=('B','N','L')
FAMILIES=[(h,s) for h in ('H01','H10','H11') for s in ('constant','step','logistic')]

@dataclass
class World:
    x: np.ndarray       # [replication, site], known geographic covariate
    obs: np.ndarray     # [replication, site, turn, category], shares B,N,L
    counts: np.ndarray  # [replication, site, turn, section, W,L,B,N]
    turnout: np.ndarray # [replication, site, turn]
    panels: np.ndarray  # [replication, training_site, turn, category] independent samples
    n_train: int
    n_cal: int
    n_target: int
    scenario: str
    latent: np.ndarray | None  # generator only; never used by infer()

    @property
    def cal_slice(self):return slice(self.n_train,self.n_train+self.n_cal)
    @property
    def target_slice(self):return slice(self.n_train+self.n_cal,self.n_train+self.n_cal+self.n_target)
    @property
    def n_worlds(self):return self.x.shape[0]


def shape_function(x, name):
    if name=='constant':return np.ones_like(x,dtype=float)
    if name=='step':return .22+.78*(x>.12)
    if name=='logistic':return .20+.80/(1+np.exp(-5*(x-.12)))
    raise ValueError(name)


def features(x,kind):
    """Ex-ante behaviour predictors. No target vote counts enter fitting."""
    x=np.asarray(x)
    t=np.broadcast_to(np.arange(2)[None,None,:],(*x.shape,2))
    z=np.broadcast_to(x[...,None],t.shape)
    col=[np.ones_like(z),z,t.astype(float)]
    if kind in ('step','quadratic'):
        col.append((z>.12).astype(float))
    if kind=='quadratic':col.append(z*z)
    return np.stack(col,axis=-1)


def draw_x(rng,worlds,n_sites,shifted=False):
    u=rng.random((worlds,n_sites))
    if not shifted:return 2*u-1
    # Source x ~ Uniform[-1,1], target density proportional to 1+0.8*x.
    return (-.5+np.sqrt(.01+.8*u))/.4


def make_world(seed,replicates=1000,scenario='H00',n_train=80,n_cal=80,n_target=10,
               panel_size=450, shifted=False, unmeasured_shift=0.0,
               random_rates=False):
    rng=np.random.default_rng(int(seed))
    W=replicates; N=n_train+n_cal+n_target; J=8
    x=np.concatenate((draw_x(rng,W,n_train+n_cal),draw_x(rng,W,n_target,shifted)),axis=1)
    x_site=x[:,:,None,None]
    turn=np.arange(2)[None,None,:,None]
    sect=np.arange(J)[None,None,None,:]
    site_b=rng.normal(0,.007,(W,N,1,1))
    site_n=rng.normal(0,.003,(W,N,1,1))
    site_l=rng.normal(0,.009,(W,N,1,1))
    within=rng.normal(0,.002,(W,N,2,J))
    b=.079+.013*x_site+.005*turn+.006*(x_site>.12)+.002*np.sin(3*x_site)+site_b+within
    n=.034+.003*x_site+.001*turn+site_n+.001*np.cos(sect)
    l=.410-.045*x_site-.007*turn+site_l+.002*np.sin(sect)
    b=np.broadcast_to(b,(W,N,2,J)).copy()
    n=np.broadcast_to(n,(W,N,2,J)).copy()
    l=np.broadcast_to(l,(W,N,2,J)).copy()
    if unmeasured_shift:
        change=unmeasured_shift*shape_function(x[:,n_train+n_cal:],'step')
        b[:,n_train+n_cal:,:,:]+=change[:,:,None,None]
    b=np.clip(b,.012,.22);n=np.clip(n,.012,.12);l=np.clip(l,.20,.68)
    p=np.stack((b,n,l),axis=-1)
    assert np.all(p.sum(axis=-1)<.97)
    C=rng.integers(260,405,size=(W,N,2,J))
    # Exact integer categories: sequential conditional binomial.
    B=rng.binomial(C,b)
    N0=rng.binomial(C-B,n/(1-b))
    L=rng.binomial(C-B-N0,l/(1-b-n))
    W0=C-B-N0-L
    latent=np.stack((W0,L,B,N0),axis=-1).astype(np.int32)
    observed=latent.copy()
    if scenario!='H00':
        parts=scenario.split('_')
        temporal=parts[0]
        donor=parts[1]
        assert temporal in ('H01','H10','H11') and donor in CATEGORY,scenario
        active={'H01':[0,1],'H10':[1,0],'H11':[1,1]}[temporal]
        donor_idx={'B':2,'N':3,'L':1}[donor]
        f=shape_function(x[:,n_train+n_cal:],'step')
        rate=AMPLITUDE*f[:,:,None,None]*np.asarray(active)[None,None,:,None]
        if random_rates:
            u=rng.uniform(-.10,.10,(W,n_target,1,1))
            v=rng.uniform(-.05,.05,(W,n_target,2,J))
            rate=rate*(1+u+v)
        rate=np.broadcast_to(rate,(W,n_target,2,J))
        idx=slice(n_train+n_cal,N)
        moved=np.minimum(observed[:,idx,:,:,donor_idx],np.floor(observed[:,idx,:,:,donor_idx]*rate+.5).astype(np.int32))
        observed[:,idx,:,:,donor_idx]-=moved
        observed[:,idx,:,:,0]+=moved
    assert np.array_equal(observed.sum(axis=-1),C)
    assert np.all(observed>=0)
    T=C.sum(axis=3)
    obs=observed[:,:,:,:,[2,3,1]].sum(axis=3)/T[...,None]
    # Training sites have independent, representative behavioural panels.
    src_p=p[:,:n_train,:,:,:]
    sampled=rng.binomial(panel_size,src_p)
    panels=sampled.sum(axis=3)/(J*panel_size)
    return World(x=x,obs=obs,counts=observed,turnout=T,panels=panels,
                 n_train=n_train,n_cal=n_cal,n_target=n_target,scenario=scenario,
                 latent=latent)


def fit_predict(w,model='step'):
    X=features(w.x,model)
    A=X[:,:w.n_train].reshape(w.n_worlds,-1,X.shape[-1])
    target=w.panels.reshape(w.n_worlds,-1,3)
    lhs=np.einsum('wip,wiq->wpq',A,A)
    lam=np.eye(lhs.shape[-1])*1e-4
    lam[0,0]=0
    beta=np.linalg.solve(lhs+lam,np.einsum('wip,wic->wpc',A,target))
    pred=np.einsum('wsrp,wpc->wsrc',X,beta)
    pred[...,0]=np.clip(pred[...,0],.012,.22)
    pred[...,1]=np.clip(pred[...,1],.012,.12)
    pred[...,2]=np.clip(pred[...,2],.20,.68)
    return pred


def scores_on_cal(w,pred,category=0,group='joint'):
    error=np.abs(pred[:,w.cal_slice,:,category]-w.obs[:,w.cal_slice,:,category])
    if group=='joint':return error.max(axis=2)
    if group=='round1':return error[:,:,0]
    if group=='round2':return error[:,:,1]
    raise ValueError(group)


def unweighted_quantile(scores,alpha=.05):
    n=scores.shape[1]
    k=math.ceil((n+1)*(1-alpha))
    if k>n:return np.full(scores.shape[0],np.inf)
    return np.sort(scores,axis=1)[:,k-1]


def weighted_quantile(scores,x_cal,x_target,alpha=.05):
    """Covariate-shift conformal quantile, with a +infinity test-point atom.

    Known density ratio w(x)=1+0.8x. Valid for marginal no-transfer
    coverage under unchanged conditional distribution and independent sites.
    The result is a separate threshold for each target site.
    """
    W,M=scores.shape;T=x_target.shape[1]
    weights=1+.8*x_cal
    target_w=1+.8*x_target
    sort=np.argsort(scores,axis=1)
    sorted_scores=np.take_along_axis(scores,sort,axis=1)
    sorted_weights=np.take_along_axis(weights,sort,axis=1)
    cw=np.cumsum(sorted_weights,axis=1)
    cut=(1-alpha)*(weights.sum(axis=1)[:,None]+target_w)
    passed=cw[:,:,None]>=cut[:,None,:]
    has=passed.any(axis=1)
    idx=passed.argmax(axis=1)
    val=np.take_along_axis(sorted_scores[:,:,None],idx[:,None,:],axis=1)[:,0,:]
    return np.where(has,val,np.inf)


def thresholds(w,pred,alpha=.05,method='joint',category=0):
    """Thresholds for each target site; no target votes are inspected."""
    cal=scores_on_cal(w,pred,category, 'joint' if method=='weighted' else
                      ('joint' if method in ('joint','bonferroni','inflated') else method))
    if method=='weighted':
        return weighted_quantile(cal,w.x[:,w.cal_slice],w.x[:,w.target_slice],alpha)
    if method=='bonferroni':alpha=alpha/w.n_target
    q=unweighted_quantile(cal,alpha)
    return np.broadcast_to(q[:,None],(w.n_worlds,w.n_target)).copy()


def intersect_affine(c,k,u,h=0,upper=.60):
    """Solve |c - a*k| <= u + a*h exactly for 0<=a<=upper."""
    c,k,u,h=np.broadcast_arrays(np.asarray(c,float),np.asarray(k,float),np.asarray(u,float),np.asarray(h,float))
    lo=np.zeros_like(c);hi=np.full_like(c,upper);valid=np.ones_like(c,dtype=bool)
    for val,slope in ((c-u,k+h),(-c-u,h-k)):
        near=np.abs(slope)<1e-14
        ratio=np.divide(val,slope,out=np.zeros_like(val),where=~near)
        lo=np.where(slope>1e-14,np.maximum(lo,ratio),lo)
        hi=np.where(slope< -1e-14,np.minimum(hi,ratio),hi)
        valid &= ~(near & (val>1e-11))
    valid &=lo<=hi+1e-11
    return lo,hi,valid


def infer_one(w,pred,threshold,category=0,models=FAMILIES,
              hetero_envelope=.15,extra_tolerance=0.,target_slice=None):
    """Off-grid partial identification using aggregate site-by-round moments.

    Conservative a-dependent envelope accounts for bounded site/section rate
    heterogeneity; the additional tolerance is externally specified, not fitted.
    True-family inclusion under transformations is measured empirically.
    """
    ys=w.obs[:,w.target_slice,:,category]
    ps=pred[:,w.target_slice,:,category]
    x=w.x[:,w.target_slice]
    Q0=threshold[:,:,None]+extra_tolerance
    # Each of eight section-level roundings introduces at most 0.5 vote error.
    # Only positive-rate candidates need this correction; exact H00 has none.
    rounded_margin=4.0/w.turnout[:,w.target_slice,:]
    Q=Q0+rounded_margin
    c=ps-ys
    h00=np.all(np.abs(c)<=Q0+1e-12,axis=2)
    lows=[]; highs=[];alive=[]
    for temporal,shape in models:
        active=np.array({'H01':[0,1],'H10':[1,0],'H11':[1,1]}[temporal])[None,None,:]
        f=shape_function(x,shape)[:,:,None]*active
        k=ps*f
        h=.22*hetero_envelope*f
        lo,hi,ok=intersect_affine(c,k,Q,h)
        lo=lo.max(axis=2);hi=hi.min(axis=2)
        good=ok.all(axis=2)&(lo<=hi+1e-11)
        lows.append(np.where(good,lo,np.nan));highs.append(np.where(good,hi,np.nan));alive.append(good)
    return {'h00':h00,'lower':np.stack(lows,axis=-1),'upper':np.stack(highs,axis=-1),
            'alive':np.stack(alive,axis=-1),'threshold':threshold}


def summary(w,inf,scenario,models=FAMILIES):
    h=inf['h00'];alive=inf['alive']
    count=alive.sum(axis=-1)+h
    result={
        'replicates':int(w.n_worlds),'target_sites':int(w.n_target),
        'H00_retained_per_site_pct':float(100*h.mean()),
        'H00_retained_all_sites_pct':float(100*h.all(axis=1).mean()),
        'mean_compatible_families_per_site':float(count.mean()),
        'mean_compatible_families_joint':float((alive.all(axis=1)).sum(axis=-1).mean()+h.all(axis=1).mean()),
        'median_tolerance':float(np.median(inf['threshold'][np.isfinite(inf['threshold'])])) if np.isfinite(inf['threshold']).any() else None,
        'fraction_infinite_thresholds':float(np.mean(~np.isfinite(inf['threshold']))),
    }
    if scenario!='H00':
        temporal,donor=scenario.split('_')[:2]
        # Only the blank category belongs to this family library.
        true_idx=models.index((temporal,'step')) if donor==CATEGORY[0] and (temporal,'step') in models else None
        if true_idx is not None:
            covers=alive[:,:,true_idx] & (inf['lower'][:,:,true_idx]<=AMPLITUDE+1e-11)&(inf['upper'][:,:,true_idx]>=AMPLITUDE-1e-11)
            result.update(true_amplitude_covered_per_site_pct=float(100*covers.mean()),
                          true_amplitude_covered_all_sites_pct=float(100*covers.all(axis=1).mean()),
                          mean_true_interval_width=float(np.nanmean(inf['upper'][:,:,true_idx]-inf['lower'][:,:,true_idx])))
    return result


def checks(w):
    assert np.all(w.counts>=0)
    assert np.array_equal(w.counts.sum(axis=-1).sum(axis=-1),w.turnout)
    assert len(w.x[0])==w.n_train+w.n_cal+w.n_target
    assert w.panels.shape[:2]==(w.n_worlds,w.n_train)
    assert np.all((w.obs>=0)&(w.obs<=1))
    assert np.all(w.obs.sum(axis=-1)<1)
    return True


def wilson_upper(x,n,z=1.6448536269514722):
    """One-sided 95% Wilson upper bound; approximate, not exact binomial."""
    p=x/n
    return (p+z*z/(2*n)+z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n)
