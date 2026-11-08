#!/usr/bin/env python3
"""Independent numerical/accounting checks for EQ-PRB-001 v0.2."""
import csv, json
from pathlib import Path
import numpy as np
import eq_prb_001_v02 as e
p=Path(__file__).resolve().parent
r=json.loads((p/'results_v0.2.json').read_text())
assert r['model_library_size']==73
assert r['null_calibration_replicates']==1500
assert r['independent_evaluation_replicates_per_generator']==1000
assert len(r['results'])==14
assert len(e.TRAIN_LOC)==30 and len(e.TEST_LOC)==10
assert not set(e.TRAIN_LOC)&set(e.TEST_LOC)
assert np.array_equal(e.Q.sum(axis=-1).round(12),np.ones_like(e.qB))
# Numerically verify the 2-rank Woodbury log-score against a dense 16x16 matrix.
for m in (e.MODELS[0],e.MODELS[11],e.MODELS[35],e.MODELS[-1]):
    parts=e.cov_parts(m,e.TEST_LOC[:1])
    w,pe,b,a,s00,s01,s11,det,logdet=parts
    diag=1/w[0]
    V=np.diag(diag)+b*b*np.ones((16,16))+a*a*np.outer(pe[0],pe[0])
    x=np.arange(16,dtype=float)/100-0.08
    close=-.5*(x@np.linalg.solve(V,x)+np.linalg.slogdet(V)[1])
    fast=e.pseudo_logscore(x[None,None,:],parts)[0]
    assert abs(close-fast)<1e-9, (m['h'],m['d'],fast,close)
with (p/'synthetic_holdout_example.csv').open(encoding='utf-8') as f:
    rows=list(csv.DictReader(f))
assert len(rows)==640
for item in rows:
    n=int(item['turnout'])
    la=[int(item[f'latent_{c}']) for c in ('W','L','B','N')]
    ob=[int(item[f'observed_{c}']) for c in ('W','L','B','N')]
    ref=[int(item[f'reference_{c}']) for c in ('W','L','B','N')]
    m=int(item['moved_B_to_W'])
    assert min(la)>=0 and min(ob)>=0 and sum(la)==sum(ob)==n
    assert sum(ref)==1800
    assert ob==[la[0]+m,la[1],la[2]-m,la[3]]
    assert item['partition']==('test' if int(item['location']) in e.TEST_LOC else 'train')
assert r['null_upper_95_less_equal_5_percent']
assert not r['all_positive_meet_80_percent_power']
print('PASS — 73 candidates, full integer accounting, location disjointness, exact matrix identity, calibration metadata')
