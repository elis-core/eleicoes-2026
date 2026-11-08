#!/usr/bin/env python3
"""Independent verification of EQ-PRB-001 v0.5 (synthetic only)."""
import csv
import json
import math
import sys
from pathlib import Path
import numpy as np
import eq_prb_001_v05 as m


def test_affine_intervals():
    rng=np.random.default_rng(516)
    a=rng.uniform(-.06,.09,1000)
    b=rng.uniform(-.12,.12,1000)
    u=rng.uniform(.001,.06,1000)
    h=rng.uniform(0,.08,1000)
    # Include zero/negative slopes and nearly degenerate intervals.
    b[:15]=0;h[:15]=0
    l,r,ok=m.interval_intersection(a,b,u,h)
    assert np.all((l[ok]>=-1e-9)&(r[ok]<=.6+1e-9))
    grid=np.linspace(0,.6,3001)
    brute=np.abs(a[:,None]-grid[None,:]*b[:,None])<=u[:,None]+grid[None,:]*h[:,None]+1e-12
    predicted=ok[:,None]&(grid[None,:]>=l[:,None]-1e-12)&(grid[None,:]<=r[:,None]+1e-12)
    if not np.array_equal(brute,predicted):
        ix=np.where(np.any(brute!=predicted,axis=1))[0]
        raise AssertionError(f'Affine inequality solver disagreed with grid check at {ix[:10].tolist()}')
    print('PASS: exact analytical intervals agree with 3,001-point independent grid check (1,000 test inequalities)')


def test_synthetic_conservation_and_holdout():
    assert len(m.TRAIN_SITES)==30 and len(m.TEST_SITES)==10
    assert not set(m.TRAIN_SITES)&set(m.TEST_SITES)
    rng=np.random.default_rng(42)
    for scenario in ('natural_stable','natural_step','H01_D0_offgrid','H11_D0_offgrid','H11_D3_offgrid','H00_biased_panel'):
        data=m.synthetic_worlds(rng,12,300,1000,scenario)
        assert np.array_equal(data['Y'].sum(axis=-1),np.broadcast_to(m.C,(12,*m.C.shape)))
        assert np.min(data['Y'])>=0
        assert np.all(data['R']>=0) and np.all(data['R']<=300)
        assert np.all(data['P']>=0) and np.all(data['P']<=1000)
        assert np.all(data['Q']>=0) and np.all(data['Q']<=1000)
        assert np.all(data['truth_natural_max']>=0)
        if scenario!='H00_biased_panel':assert np.all(data['truth_panel_mismatch_max']==0)
        else:assert np.all(data['truth_panel_mismatch_max']>0)
    print('PASS: 4-category integer conservation, panel bounds, and 30/10 site holdout')


def test_coverage_logic():
    rng=np.random.default_rng(27182)
    data=m.synthetic_worlds(rng,100,1800,10000,'H11_D3_offgrid')
    paired=m.confidence_sets(data,1800,10000,'paired')
    idx=m.FAMILIES.index(('H11','step'))
    assert np.mean(paired['alive'][:,idx]&
                   (paired['lower'][:,idx]<=m.TRUE_A)&
                   (paired['upper'][:,idx]>=m.TRUE_A))>.90
    no_transfer=m.synthetic_worlds(rng,100,1800,10000,'natural_step')
    assert np.mean(m.confidence_sets(no_transfer,1800,10000,'paired')['H00'])>.90
    print('PASS: known off-grid rate inclusion and natural-step no-transfer stress (100 independent pilot worlds each)')


def test_released_summary():
    root=Path(__file__).parent
    path=root/'results_v0.5.json'
    if not path.exists():
        print('SKIP: full-run results not present in output directory')
        return
    data=json.loads(path.read_text())
    assert data['n_independent_synthetic_worlds']==data['n_independent_cases']*data['n_replicates_per_case']
    assert data['n_independent_synthetic_worlds']==20000
    assert len(data['records'])==42
    assert sum(1 for r in data['records'] if not r['assumptions_valid'])==6
    for r in data['records']:
        assert r['replicates']==1000
        assert 0<=r['true_family_inclusion']<=1 and 0<=r['H00_retained']<=1
        assert 0<=r['mean_compatible_families']<=10
        assert r['true_family_inclusion_count']==round(r['replicates']*r['true_family_inclusion'])
        if r['method']=='envelope':
            assert r['median_calibrated_natural_envelope']>=0
            assert r['empirical_calibrated_envelope_coverage']>=0
    print('PASS: released 20,000-world result counts, assumption flags and numerical ranges')

if __name__=='__main__':
    test_affine_intervals()
    test_synthetic_conservation_and_holdout()
    test_coverage_logic()
    test_released_summary()
