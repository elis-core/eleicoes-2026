#!/usr/bin/env python3
"""Conditional-on-turnout, no-transformation continuity baseline using actual 2022 RN data.

Does not train on or score 2026 results. Hamilton allocation preserves integer C2 exactly.
"""
import argparse,collections,csv,json,math
from pathlib import Path

def hamilton(turnout,weights):
    if turnout<0:raise ValueError('Negative turnout')
    weights=[max(0,float(w)) for w in weights]
    if sum(weights)==0:weights=[1]*len(weights)
    exact=[turnout*w/sum(weights) for w in weights]
    counts=[math.floor(x) for x in exact]
    remainder=turnout-sum(counts)
    for i in sorted(range(len(counts)),key=lambda i:(-(exact[i]-counts[i]),i))[:remainder]:
        counts[i]+=1
    assert sum(counts)==turnout
    return counts

def run(source,municipal_csv,summary_json):
    groups=collections.defaultdict(lambda:{'actual':[0]*4,'pred':[0]*4,'sec_error':0,'sections':0})
    total_err,sections=0,0
    with source.open(newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            w1=int(r['LULA2022_1']);l1=int(r['BOLSONARO2022_1'])
            other=int(r['OTHER2022_1']);b1=int(r['B2022_1']);n1=int(r['N2022_1'])
            c1=int(r['C2022_1']);c2=int(r['C2022_2'])
            if c1==0:weights=[1,1,0,0]
            elif w1+l1==0:weights=[(c1-b1-n1)/2]*2+[b1,n1]
            else:weights=[(w1+l1+other)*w1/(w1+l1),
                          (w1+l1+other)*l1/(w1+l1),b1,n1]
            pred=hamilton(c2,weights)
            actual=[int(r[k]) for k in ('LULA2022_2','BOLSONARO2022_2','B2022_2','N2022_2')]
            if c2!=sum(actual):raise ValueError('Failed actual 2022 turnout identity')
            group=groups[r['CD_MUNICIPIO']]
            group['sections']+=1
            for j in range(4):
                group['actual'][j]+=actual[j];group['pred'][j]+=pred[j]
            err=sum(abs(a-b) for a,b in zip(actual,pred))
            group['sec_error']+=err;total_err+=err;sections+=1
    result=[]
    for municipality,g in sorted(groups.items()):
        n=sum(g['actual'])
        e=[100*abs(a-b)/n if n else None for a,b in zip(g['actual'],g['pred'])]
        result.append(dict(municipality_code=municipality,sections=g['sections'],
            turnout=n,w_pp=e[0],l_pp=e[1],blank_pp=e[2],null_pp=e[3],
            section_absolute_error=g['sec_error'],
            signed_lula_vote_error=g['pred'][0]-g['actual'][0]))
    municipal_csv.parent.mkdir(parents=True,exist_ok=True)
    with municipal_csv.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(result[0]));writer.writeheader();writer.writerows(result)
    criteria=[0.5,0.5,0.1,0.1]
    meeting=sum(all(r[k] is not None and r[k]<=t for k,t in
            zip(('w_pp','l_pp','blank_pp','null_pp'),criteria)) for r in result)
    stats={'year':2022,'prediction_regime':'conditional-on-observed-C2',
        'baseline':'no-transfer continuity of blank/null rates, eliminated votes shared in first-round finalist ratio; exact Hamilton integer allocation',
        'sections':sections,'municipalities':len(result),
        'sum_section_four_category_absolute_errors':total_err,
        'per_section_four_category_MAE':total_err/sections,
        'per_section_per_category_MAE':total_err/(4*sections),
        'municipalities_meeting_only_four_category_precision_limits':meeting,
        'full_five_condition_high_precision_test':'not applicable to baseline itself',
        'model_not_trained_on_2026':True,
        'external_2026_predictive_validation':False}
    summary_json.parent.mkdir(parents=True,exist_ok=True)
    summary_json.write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(stats,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--2022-sections',dest='sections',required=True,type=Path)
    p.add_argument('--municipal-csv',required=True,type=Path)
    p.add_argument('--summary',required=True,type=Path)
    a=p.parse_args()
    run(a.sections,a.municipal_csv,a.summary)
