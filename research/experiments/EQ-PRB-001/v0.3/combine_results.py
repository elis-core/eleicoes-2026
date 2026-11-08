#!/usr/bin/env python3
"""Combine separately seeded, independent EQ-PRB-001 v0.3 precision runs."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SIZES=[1800,300,75]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=ROOT)
    args=p.parse_args();root=args.root
    pieces=[]
    for n in SIZES:
        f=root/f'run{n}'/'results_v0.3.json'
        part=json.loads(f.read_text(encoding='utf-8'))
        assert part['reference_sizes']==[n],(n,part['reference_sizes'])
        assert part['entirely_synthetic']
        assert len(part['scores'])==27 and len(part['prediction_intervals'])==3
        pieces.append(part)
    initial=pieces[0]
    summary={k:v for k,v in initial.items() if k not in ('scores','prediction_intervals','reference_sizes','seed','composite_false_alarm_control_on_tested_nulls','all_tested_signals_meet_80_percent_detection')}
    summary.update({'reference_sizes':SIZES,
                    'seeds_by_reference_size':{str(n):p['seed'] for n,p in zip(SIZES,pieces)},
                    'scores':[item for p in pieces for item in p['scores']],
                    'prediction_intervals':[item for p in pieces for item in p['prediction_intervals']]})
    assert len(summary['scores'])==81 and len(summary['prediction_intervals'])==9
    nulls=[r for r in summary['scores'] if r['generator']=='H00']
    positives=[r for r in summary['scores'] if r['generator']!='H00']
    summary.update({
        'all_tested_composite_nulls_upper_95_below_5_percent':all(r['upper_one_sided95_composite_null']<=.05 for r in nulls),
        'all_tested_positives_meet_80_percent_power':all(r['false_or_detection_rate_composite']>=.8 for r in positives),
        'worst_composite_null':max(nulls,key=lambda r:r['upper_one_sided95_composite_null']),
        'highest_composite_positive_detection':max(positives,key=lambda r:r['false_or_detection_rate_composite']),
        'independent_calibration_worlds':sum(p['null_calibration_replicates_per_natural_generator']*4 for p in pieces),
        'independent_evaluation_worlds':sum(p['evaluation_replicates_per_generator']*9 for p in pieces),
        'independent_interval_calibration_worlds':sum(p['null_calibration_replicates_per_natural_generator']*3 for p in pieces),
        'statistical_status':'exploratory, not validated; tested composite null fails one confidence criterion and power < 80% in multiple scenarios',
        'mechanism_identified':False,
    })
    # Overall significance cannot be inferred from individual 95% intervals as
    # a joint guarantee across 36 tested null configurations.
    summary['multiple_comparisons_warning']='Individual one-sided 95% confidence limits are not a simultaneous familywise 95% guarantee across 36 composite-null configurations.'
    (root/'results_v0.3.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for filename,key in [('model_comparison.csv','scores'),('intervals.csv','prediction_intervals')]:
        if key=='scores':
            rows=summary['scores'];fields=list(rows[0])
        else:
            rows=[]
            for p in summary['prediction_intervals']:
                for level,cats in p['assessment']['marginal'].items():
                    for cat,m in cats.items():
                        rows.append({'reference_n':p['reference_n'],'generator':p['generator'],'D':p['D'],
                                     'level':level,'category':cat,
                                     'raw_coverage':m['raw']['coverage'],
                                     'calibrated_coverage':m['split_calibrated']['coverage'],
                                     'raw_mean_width_pp':m['raw']['mean_width_percentage_points'],
                                     'calibrated_mean_width_pp':m['split_calibrated']['mean_width_percentage_points'],
                                     'calibrated_critical':m['calibrated_critical_value']})
            fields=list(rows[0])
        with (root/filename).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    print('COMBINED:',len(summary['scores']),'model comparisons;',len(summary['prediction_intervals']),
          'interval assessments;',summary['independent_calibration_worlds']+summary['independent_evaluation_worlds']+
          summary['independent_interval_calibration_worlds'],'synthetic replicate worlds')

if __name__=='__main__':main()
