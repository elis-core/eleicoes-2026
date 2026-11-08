#!/usr/bin/env python3
"""Independent checks for synthetic EQ-PRB-001 v0.3 outputs and algebra."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import eq_prb_001_v03 as v

ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'results_v0.3.json').read_text(encoding='utf-8'))
assert r['version']=='0.3' and r['entirely_synthetic']
assert r['reference_sizes']==[1800,300,75]
assert r['seeds_by_reference_size']=={'1800':20261108,'300':20261109,'75':20261110}
assert len(r['scores'])==81 and len(r['prediction_intervals'])==9
assert set(v.TRAIN).isdisjoint(set(v.TEST)) and len(v.TRAIN)==30 and len(v.TEST)==10
assert v.C.shape==(40,2,8)
assert np.allclose(v.Q.sum(axis=-1),1.)
assert np.min(v.Q)>0
assert r['independent_calibration_worlds']==12000
assert r['independent_evaluation_worlds']==27000
assert r['independent_interval_calibration_worlds']==9000
assert not r['mechanism_identified']
# Inference input contains ONLY observed and reference count arrays.
rng=np.random.default_rng(123)
data=v.simulate(rng,5,75,h='H11',d='D3')
assert set(data)=={'Y','REF'}
assert data['Y'].shape==(5,40,2,8,4)
assert np.min(data['Y'])>=0
assert np.array_equal(data['Y'].sum(axis=-1),np.broadcast_to(v.C,data['Y'].shape[:-1]))
assert np.array_equal(data['REF'].sum(axis=-1),np.full(data['REF'].shape[:-1],75))
for design in ('restricted','quadratic','behavioural-envelope'):
    s=v.Search(300,design)
    assert len(s.models)==73
    assert np.linalg.matrix_rank(s.X[v.TRAIN].reshape(-1,s.X.shape[-1]))==s.X.shape[-1]
    f=s.fit(v.simulate(np.random.default_rng(120),3,300,h='H11',d='D3'))
    assert f['selected'].shape==(3,) and f['delta'].shape==(3,)
    assert np.all(np.isfinite(f['delta']))
    # Verify the Woodbury pseudo-score against 16x16 dense inversion.
    for model in (s.models[0],s.models[11],s.models[-1]):
        cv=model['test_cov']
        w,p,b,a,s00,s01,s11,det,logdet=cv
        V=np.diag(1/w[0])+b*b*np.ones((16,16))+a*a*np.outer(p[0],p[0])
        x=np.linspace(-.05,.05,16)
        target=-.5*(x@np.linalg.solve(V,x)+np.linalg.slogdet(V)[1])
        fast=s.score(x[None,None,:],tuple(a[:1] if isinstance(a,np.ndarray) else a for a in cv))[0]
        assert abs(target-fast)<1e-8,(design,model['h'],model['d'],target,fast)
    if design=='behavioural-envelope':
        # Exact signal-shaped natural changes are in the nuisance span: mean
        # patterns cannot distinguish the transformation from that behaviour.
        for m in s.models:
            assert np.max(np.abs(m['ptr']))<1e-10
            assert np.max(np.abs(m['pte']))<1e-10
    pred_data=v.simulate(np.random.default_rng(456),5,300,h='H11',d='D3')
    obs,pred,sigma=s.predictive_arrays(pred_data,s.fit(pred_data))
    assert obs.shape==(5,10,2,8,4)
    assert np.allclose(obs.sum(axis=-1),1.) and np.allclose(pred.sum(axis=-1),1.)
    assert np.min(sigma)>0
for row in r['scores']:
    assert row['n']==1000
    assert row['count_restricted']==int(round(row['false_or_detection_rate_restricted']*1000))
    assert row['count_composite']==int(round(row['false_or_detection_rate_composite']*1000))
    assert row['null_threshold_composite']>=row['null_threshold_restricted']
for p in r['prediction_intervals']:
    assert p['calibration_replicates']==1000 and p['test_replicates']==1000
    for level,cat in p['assessment']['marginal'].items():
        assert level in ('50','80','95')
        assert len(cat)==4
        for value in cat.values():
            assert 0<=value['raw']['coverage']<=1
            assert 0<=value['split_calibrated']['coverage']<=1
assert r['equivalence']['model'].startswith('independent B-to-W thinning')
print('PASS: synthetic accounting, 30/10 location split, 73 candidates, full-rank nuisance,')
print('      dense/Woodbury identity, exact behavioural-envelope mean confounding,')
print('      separate replication counts, 81 score rows and 9 interval assessments.')
