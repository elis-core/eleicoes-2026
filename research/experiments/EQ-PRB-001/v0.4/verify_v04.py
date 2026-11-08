#!/usr/bin/env python3
"""Independent validation of EQ-PRB-001 v0.4, synthetic-only."""
from __future__ import annotations
import itertools
import json
import math
from pathlib import Path
import numpy as np
import eq_prb_001_v04 as v

ROOT=Path(__file__).resolve().parent
out=json.loads((ROOT/'results_v0.4.json').read_text(encoding='utf-8'))
assert out['version']=='0.4' and out['entirely_synthetic']
assert out['protocol']['independent_evaluation_worlds']==21000
assert out['protocol']['reference_sizes']==[1800,300,75]
assert out['protocol']['replications_per_scenario_precision']==1000
assert len(out['scores'])==3*7*3*2==126
assert len(out['examples'])>0
assert len(v.CANDIDATES)==64 and v.CANDIDATES[0].temporal=='H00'
assert set(v.TRAIN_SITES).isdisjoint(set(v.TEST_SITES))
assert len(v.TRAIN_SITES)==30 and len(v.TEST_SITES)==10
assert set(np.ravel(v.ACTIVES)).issubset({0.,1.})
assert np.allclose(v.Q.sum(axis=-1),1.) and np.min(v.Q)>0
assert np.max(v.qB+v.TRUE_NATURAL_ENVELOPE)<v.QMAX

for scenario in ('H00','H01_D0','H10_D0','H11_D0','H11_D3','natural_step','reference_bias'):
    data=v.simulate(np.random.default_rng(211+len(scenario)),8,75,'H00' if scenario=='reference_bias' else scenario,reference_bias=(scenario=='reference_bias'))
    assert set(data)=={'Y','REF'}  # Fitting cannot receive hidden latent X.
    assert data['Y'].shape==(8,40,2,8,4)
    assert np.all(data['Y']>=0)
    assert np.array_equal(data['Y'].sum(axis=-1),np.broadcast_to(v.C,(8,*v.C.shape)))
    assert np.all(data['REF'].sum(axis=-1)==75)
    sets=v.moment_confidence_sets(data,75,.035,.055)
    assert sets['final'].shape==(8,64)
    assert np.all(sets['final']<=sets['train'])
    assert np.all(sets['n_models']<=64)

# Exact finite sample four-category multinomial likelihood: all feasible
# reported Y are enumerated for small C. This verifies normalisation (no
# missing/multiply counted latent count vectors under rounding).
p=np.array([.48,.39,.09,.04])
for c in range(1,8):
    outputs=[]
    for w in range(c+1):
        for l in range(c-w+1):
            for b in range(c-w-l+1):
                outputs.append((w,l,b,c-w-l-b))
    ys=np.array(outputs,dtype=int)
    for rate in (0.,.04,.14,.30,.47,.60):
        scores=v.exact_four_count_logpmf(ys,p,rate)
        assert not np.any(np.isnan(scores))
        assert abs(float(np.exp(scores).sum())-1)<1e-10,(c,rate,np.exp(scores).sum())

# Verify inversion formula & bounded-difference condition used by McDiarmid.
for rate in np.linspace(0,.60,19):
    vals=np.arange(450)
    f=vals-np.floor(rate*vals+.5)
    assert np.all((np.diff(f)>=0)&(np.diff(f)<=1))
    assert np.max(np.abs(np.floor(rate*vals+.5)-rate*vals))<=.500000001

# A correctly specified candidate should be preserved with at least 95%
# *theoretical* coverage. The simulation is deliberately conservative, so
# requiring every configuration to have >=95% inclusion is a diagnostic,
# not a proof of the theorem or its general applicability.
correct=[r for r in out['scores'] if r['assumptions_correctly_cover_generator']]
assert len(correct)>0
for row in correct:
    assert row['true_candidate_retained_rate']>=.95,(row['scenario'],row['reference_n'],row['natural_envelope'],row['rate_envelope'])
    if row['scenario']=='H00':
        assert row['H00_exclusion_one_sided_95_upper']<=.05

# Reference bias and natural step are false alarms only where restrictive
# natural-envelopes are invalid. The widest envelope must retain H00.
for scenario in ('natural_step','reference_bias'):
    xs=[r for r in out['scores'] if r['scenario']==scenario and r['natural_envelope']==.035]
    assert all(r['assumptions_correctly_cover_generator'] and r['H00_retained_rate']>=.95 for r in xs)

# Frozen candidate library includes the synthetic generating rates. In
# addition, do not overstate first-moment equivalence as distributional
# equivalence for integer-rounded transfers.
assert 'NOT exact equality' in out['identification_limit']['scope']
print('PASS: 21,000 simulations, 126 evaluations, 30/10 site holdout, 64 candidates,')
print('      no latent inputs, exact count conservation, four-way moment inversion,')
print('      small-count multinomial likelihood normalisation, bounded differences,')
print('      true-grid coverage under valid bounds, misspecification stress tests.')
