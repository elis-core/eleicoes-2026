#!/usr/bin/env python3
"""Rebuild 2022 RN presidential section CSV and compare historical section keys."""
import argparse,csv,json,collections,hashlib
from pathlib import Path
from historical_bu_audit import read_bu

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--2022-first',dest='first',type=Path,required=True)
    p.add_argument('--2022-second',dest='second',type=Path,required=True)
    p.add_argument('--2026-sections',dest='sections',type=Path,required=True)
    p.add_argument('--output-sections',dest='output_sections',type=Path,required=True)
    p.add_argument('--output-report',dest='output_report',type=Path,required=True)
    a=p.parse_args()
    r1,_=read_bu(a.first);r2,_=read_bu(a.second)
    if set(r1)!=set(r2):raise ValueError('2022 first/second round section mismatch')
    columns=['CD_MUNICIPIO','NR_ZONA','NR_SECAO','E1','C1','A1','E2','C2','A2',
             'LULA1','BOLSONARO1','OTHERS1','B1','N1','LULA2','BOLSONARO2','B2','N2']
    a.output_sections.parent.mkdir(parents=True,exist_ok=True)
    with a.output_sections.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for key in sorted(r1):
            x,y=r1[key],r2[key]
            row=dict(zip(columns[:3],key))
            for roundno,record in ((1,x),(2,y)):
                m=record['meta'];v=record['votes']
                for label,meta in (('E','electorate'),('C','turnout'),('A','abstention')):
                    row[f'{label}{roundno}']=m[meta]
                row[f'LULA{roundno}']=v.get('nominal_13',0)
                row[f'BOLSONARO{roundno}']=v.get('nominal_22',0)
                row[f'B{roundno}']=v.get('blank',0)
                row[f'N{roundno}']=v.get('null',0)
                if roundno==1:row['OTHERS1']=sum(n for cat,n in v.items() if cat.startswith('nominal_') and cat not in ('nominal_13','nominal_22'))
                component=sum(int(row[k]) for k in ((('LULA1','BOLSONARO1','OTHERS1','B1','N1') if roundno==1 else ('LULA2','BOLSONARO2','B2','N2'))))
                if component!=int(row[f'C{roundno}']):raise ValueError('2022 conservation check failed')
            writer.writerow(row)
    now={}
    with a.sections.open(newline='',encoding='utf-8') as f:
        for row in csv.DictReader(f):
            now[(row['CD_MUNICIPIO'],row['NR_ZONA'],row['NR_SECAO'])]=row
    shared=set(r1)&set(now)
    result={'2022_sections':len(r1),'2026_sections':len(now),
            'shared_section_keys':len(shared),
            '2022_only':len(set(r1)-set(now)),'2026_only':len(set(now)-set(r1)),
            'different_polling_place_ids':sum(
                r1[k]['meta']['local']!=now[k]['NR_LOCAL_VOTACAO_1'] or
                r2[k]['meta']['local']!=now[k]['NR_LOCAL_VOTACAO_2'] for k in shared),
            'changed_first_round_electorate':sum(
                r1[k]['meta']['electorate']!=int(now[k]['E1']) for k in shared),
            'sha256_2022_derived_csv':sha256(a.output_sections)}
    a.output_report.parent.mkdir(parents=True,exist_ok=True)
    a.output_report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
