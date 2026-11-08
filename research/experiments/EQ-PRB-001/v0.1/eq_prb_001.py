#!/usr/bin/env python3
"""EQ-PRB-001 v0.1: synthetic/oracle deterministic recovery; no real election data.
Requires numpy. Reproducible: numpy PCG64 seed 20261108.
"""
import csv, json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
SEED=20261108
RNG=np.random.default_rng(SEED)
N_MUNI,N_LOCS,N_PER_LOC=5,8,8
N=N_MUNI*N_LOCS*N_PER_LOC
NAMES=['W','L','B','N']

def rounded(x):
    return np.floor(x+0.5).astype(np.int64)

def transform(X, rate):
    """Only synthetic H-B flow B->W; integer accounting and no negative counts."""
    X=np.asarray(X,dtype=np.int64)
    m=np.minimum(X[:,2],np.maximum(0,rounded(X[:,2]*rate)))
    Y=X.copy();Y[:,0]+=m;Y[:,2]-=m
    assert np.all(Y>=0) and np.all(Y.sum(axis=1)==X.sum(axis=1))
    return Y

def make_latent():
    loc=np.repeat(np.arange(N_MUNI*N_LOCS),N_PER_LOC)
    muni=loc//N_LOCS
    C1=RNG.integers(220,440,size=N)
    C2=np.maximum(120,C1+RNG.integers(-55,31,size=N))
    z=(C2-290.0)/115.0
    # Vary behavioural proportions naturally across sections and locations.
    base=RNG.dirichlet([30,26,5,4],size=N)
    loc_shift=RNG.normal(0,.025,N_MUNI*N_LOCS)
    p2=base.copy()
    p2[:,0]=np.maximum(.01,base[:,0]+loc_shift[loc]+RNG.normal(0,.022,N))
    p2[:,1]=np.maximum(.01,base[:,1]-loc_shift[loc]+RNG.normal(0,.022,N))
    p2=p2/p2.sum(axis=1,keepdims=True)
    X1=np.vstack([RNG.multinomial(int(c),p) for c,p in zip(C1,base)])
    X2=np.vstack([RNG.multinomial(int(c),p) for c,p in zip(C2,p2)])
    return loc,muni,C1,C2,z,X1,X2

def library(z):
    """Fixed model library declared before looking at outputs."""
    return {
      'zero':np.zeros_like(z),
      'constant_0.05':np.full_like(z,.05),
      'constant_0.10':np.full_like(z,.10),
      'constant_0.20':np.full_like(z,.20),
      'linear_clip':np.clip(.09+.055*z,0,1),
      'logistic':1/(1+np.exp(-(-2.3+1.05*z))),
      'threshold':np.where(z>.2,.17,.025),
    }

def errors(Y,hat):
    return int(np.abs(Y-hat).sum()),int(np.count_nonzero(np.any(Y!=hat,axis=1)))

def main():
    loc,muni,C1,C2,z,X1,X2=make_latent()
    rates=library(z)
    # Train and hold out entire polling places (same units on both rounds).
    holdout_locs=np.array([i for i in range(N_MUNI*N_LOCS) if i%N_LOCS in (2,7)])
    test=np.isin(loc,holdout_locs); train=~test
    scenarios={'H00':('zero','zero'),'H01':('zero','linear_clip'),
               'H10':('threshold','zero'),'H11':('logistic','logistic')}
    rows=[]; fits=[]
    for h,(r1,r2) in scenarios.items():
        Y1=transform(X1,rates[r1]); Y2=transform(X2,rates[r2])
        for t,X,Y,true_r in ((1,X1,Y1,r1),(2,X2,Y2,r2)):
            ranking=[]
            for name,rate in rates.items():
                pred=transform(X,rate)
                ae,sects=errors(Y[train],pred[train])
                hae,hsects=errors(Y[test],pred[test])
                ranking.append((ae,name,hae,sects,hsects))
            ranking.sort(key=lambda e:(e[0],e[1]))
            best=ranking[0][0]
            winners=[r for r in ranking if r[0]==best]
            fits.append({'scenario':h,'round':t,'true_rule':true_r,
                         'train_best_abs_error':best,'train_best_candidates':[r[1] for r in winners],
                         'test_abs_error_of_best':ranking[0][2],
                         'test_abs_error_true_rule':errors(Y[test],transform(X,rates[true_r])[test])[0],
                         'train_sections':int(train.sum()),'test_sections':int(test.sum()),
                         'train_locations':int(np.unique(loc[train]).size),
                         'test_locations':int(np.unique(loc[test]).size)})
            for e,name,hae,sects,hsects in ranking:
                rows.append({'scenario':h,'round':t,'rule':name,'true_rule':true_r,
                             'train_abs_error':e,'test_abs_error':hae,
                             'train_mismatch_sections':sects,'test_mismatch_sections':hsects})
    # Explicit non-identifiability construction using observations alone:
    # Y=F(X,theta) also equals identity(Y) if latent X is unconstrained.
    sample=transform(X2,rates['linear_clip'])
    assert np.array_equal(transform(sample,rates['zero']),sample)
    example_idx=int(np.flatnonzero(X2[:,2]>0)[0])
    ident={'section_index':example_idx,
           'latent_before_synthetic_transformation':X2[example_idx].tolist(),
           'observed_synthetic_counts':sample[example_idx].tolist(),
           'alternate_latent_counts_identity_rule':sample[example_idx].tolist(),
           'same_observation_under_both_explanations':True,
           'interpretation':'Without independent constraints on latent X, transformation is not identified from Y alone.'}
    # Integrity assertions: all datasets generated, all scenarios conserving turnout.
    for a,b in scenarios.values():
        for X,r in ((X1,a),(X2,b)):
            Y=transform(X,rates[r]);assert np.array_equal(X.sum(axis=1),Y.sum(axis=1))
    for f in fits:
        assert f['train_best_abs_error']==0 and f['test_abs_error_true_rule']==0
    with (ROOT/'candidate_scores.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    with (ROOT/'fit_summary.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(fits[0]));writer.writeheader();writer.writerows(fits)
    with (ROOT/'synthetic_section_data.csv').open('w',newline='',encoding='utf-8') as f:
        cols=['section_id','municipality_id','location_id','holdout','turnout_1','turnout_2','z']
        cols += [f'latent_T{t}_{c}' for t in (1,2) for c in NAMES]
        cols += [f'observed_{h}_T{t}_{c}' for h in scenarios for t in (1,2) for c in NAMES]
        w=csv.writer(f);w.writerow(cols)
        ys={h:(transform(X1,rates[r1]),transform(X2,rates[r2])) for h,(r1,r2) in scenarios.items()}
        for i in range(N):
            row=[i,int(muni[i]),int(loc[i]),int(test[i]),int(C1[i]),int(C2[i]),float(z[i])]
            row+=X1[i].tolist()+X2[i].tolist()
            for h in scenarios:row+=ys[h][0][i].tolist()+ys[h][1][i].tolist()
            w.writerow(row)
    report={'experiment':'EQ-PRB-001','version':'0.1','seed':SEED,'numpy_version':np.__version__,
      'data_type':'100% synthetic, generated; not 2026 electoral results',
      'n_municipalities':N_MUNI,'n_locations':int(np.unique(loc).size),
      'n_sections':N,'train_sections':int(train.sum()),'test_sections':int(test.sum()),
      'holdout_rule':'locations 2 and 7 (zero-indexed) within each of five municipalities',
      'candidate_library':list(rates),'scenarios':scenarios,'fits':fits,
      'identifiability_counterexample':ident,
      'caveats':['Oracle latent X1,X2 supplied to the evaluator: not feasible in real observed results.',
                 'The true generating rule is contained in the predefined candidate library.',
                 'Only B->W mechanism tested; no other transfer flows.',
                 'This is NOT a test of election fraud, software, or real-world conversion.',
                 'No Bayesian hierarchical inference, stochastic interval evaluation or 1000-replicate calibration yet.']}
    (ROOT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'n_sections':N,'fits':fits,'counterexample':ident},indent=2))
if __name__=='__main__':main()
