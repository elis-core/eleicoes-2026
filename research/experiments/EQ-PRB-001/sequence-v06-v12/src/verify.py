#!/usr/bin/env python3
"""Auditable invariants and no-target-leakage checks for EQ-PRB-001 v0.6–v0.12."""
import argparse
import json
from pathlib import Path
from dataclasses import replace
import numpy as np
from core import (make_world,checks,fit_predict,thresholds,intersect_affine,
                  unweighted_quantile,weighted_quantile)


def unit_tests():
    rng=np.random.default_rng(24680)
    c=rng.uniform(-.4,.4,160)
    k=rng.uniform(-.25,.25,160)
    u=rng.uniform(0,.07,160)
    h=rng.uniform(0,.04,160)
    lo,hi,valid=intersect_affine(c,k,u,h)
    grid=np.linspace(0,.6,1201)
    brute=np.abs(c[:,None]-k[:,None]*grid[None,:]) <= u[:,None]+h[:,None]*grid[None,:]+1e-12
    analytic=valid[:,None] & (grid[None,:]>=lo[:,None]-1e-10)&(grid[None,:]<=hi[:,None]+1e-10)
    assert np.array_equal(brute,analytic), 'Affinely inverted confidence intervals disagree with independent exhaustive grid'
    assert np.array_equal(unweighted_quantile(np.zeros((1,80)),.005),np.array([np.inf]))
    assert np.isfinite(unweighted_quantile(np.zeros((1,240)),.005)).all()
    q=weighted_quantile(np.array([[.1,.2,.3]]),np.array([[-1,0,1]]),np.array([[0]]),alpha=.4)
    assert np.allclose(q,.3)
    qinf=weighted_quantile(np.array([[.1,.2,.3]]),np.array([[-1,0,1]]),np.array([[0]]),alpha=.05)
    assert np.isinf(qinf).all()
    # Three separate mechanisms, preserving every count in every round.
    for scenario in ('H00','H11_B','H11_N','H11_L'):
        w=make_world(777,replicates=12,scenario=scenario,random_rates=scenario!='H00')
        assert checks(w)
        assert w.counts.shape[-1]==4
        assert np.array_equal(w.counts.sum(axis=(-1,-2)),w.turnout)
    # Donor fit and conformal calibration must not use target outcomes.
    w=make_world(10101,replicates=12,scenario='H11_B')
    before=fit_predict(w)
    q_before=thresholds(w,before)
    changed=replace(w,obs=w.obs.copy())
    changed.obs[:,changed.target_slice]=np.nan
    after=fit_predict(changed)
    q_after=thresholds(changed,after)
    assert np.array_equal(before,after)
    assert np.array_equal(q_before,q_after)
    # Deterministic seed/parameter replay.
    w2=make_world(10101,replicates=12,scenario='H11_B')
    assert np.array_equal(w.obs,w2.obs)
    assert np.array_equal(w.panels,w2.panels)
    return True


def verify_results(version,path):
    doc=json.loads((Path(path)/'results.json').read_text())
    assert doc['version']==version and doc['independent_replicates_per_generator']==1000
    assert doc['completion'].startswith('executed')
    assert len(doc['results'])>0
    for r in doc['results']:
        assert r['synthetic_worlds']==1000
        assert 0<=r['H00_retained_per_site_pct']<=100
        assert 0<=r['H00_retained_all_sites_pct']<=100
        assert r['H00_retained_all_sites_pct']<=r['H00_retained_per_site_pct']+1e-8
        if 'true_amplitude_covered_per_site_pct' in r:
            assert 0<=r['true_amplitude_covered_per_site_pct']<=100
            assert r['true_amplitude_covered_all_sites_pct']<=r['true_amplitude_covered_per_site_pct']+1e-8
    if version=='v0.7':
        assert len(doc['results'])==6
    if version=='v0.8':
        vacuous=[r for r in doc['results'] if r['method']=='bonferroni' and r['independent_calibration_sites']==80]
        assert len(vacuous)==2 and all(r['fraction_infinite_thresholds']==1. for r in vacuous)
    if version=='v0.9':
        assert any(not r['bound_covers_simulated_shift'] for r in doc['results'])
    if version=='v0.10':
        assert all(len(r['compatible_mechanism_retention'])==3 for r in doc['results'])
    if version=='v0.11':
        assert all(r['selection_unaffected_by_removing_all_target_outcomes'] for r in doc['results'] if r['method']=='external_validation_freeze')
    if version=='v0.12':
        assert len(doc['results'])==6
        assert any(r.get('readiness_FWER_false_alarm_upper_le_5pct') is False for r in doc['results'])
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--version',required=True)
    p.add_argument('--directory',default='.')
    args=p.parse_args()
    assert unit_tests()
    assert verify_results(args.version,args.directory)
    print('PASS: analytic interval inversion, independent numerical grid, seed replay, count conservation,')
    print('PASS: known-ratio weighted conformal, finite-sample resolution, no target leakage,')
    print(f'PASS: {args.version} version-specific results and invariants.')
