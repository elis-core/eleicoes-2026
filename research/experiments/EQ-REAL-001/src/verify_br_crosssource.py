#!/usr/bin/env python3
"""Streaming RN presidential reconciliation: nationwide BR ZIP versus RN BU ZIPs.

Requires pandas. This script only reads actual election records; it does not fit models.
"""
import argparse
import collections
import csv
import io
import json
import zipfile
from pathlib import Path

def read_bu(path):
    totals=collections.Counter()
    keys=set()
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        member=next(x for x in z.namelist() if x.lower().endswith('.csv'))
        with z.open(member) as raw:
            for r in csv.DictReader(io.TextIOWrapper(raw,encoding='latin-1',newline=''),delimiter=';'):
                if r['DS_CARGO_PERGUNTA']!='Presidente':continue
                keys.add((r['NR_TURNO'],r['CD_MUNICIPIO'],r['NR_ZONA'],r['NR_SECAO']))
                totals[(r['NR_TURNO'],r['NR_VOTAVEL'])]+=int(r['QT_VOTOS'])
    return totals,keys

def read_br(path):
    import pandas as pd
    totals=collections.Counter()
    keys=set()
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        member=next(x for x in z.namelist() if x.lower().endswith('.csv'))
        fields=['SG_UF','DS_CARGO','NR_TURNO','NR_VOTAVEL','QT_VOTOS',
                'CD_MUNICIPIO','NR_ZONA','NR_SECAO']
        for chunk in pd.read_csv(z.open(member),sep=';',encoding='latin-1',
                                  dtype=str,usecols=fields,chunksize=250000):
            subset=chunk[(chunk['SG_UF']=='RN') & (chunk['DS_CARGO'].str.upper()=='PRESIDENTE')].copy()
            if subset.empty:continue
            subset['QT_VOTOS']=subset['QT_VOTOS'].astype('int64')
            for (round_,vote),count in subset.groupby(['NR_TURNO','NR_VOTAVEL'])['QT_VOTOS'].sum().items():
                totals[(round_,vote)]+=int(count)
            keys.update(tuple(r) for r in subset[['NR_TURNO','CD_MUNICIPIO','NR_ZONA','NR_SECAO']].drop_duplicates().itertuples(index=False,name=None))
    return totals,keys

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--br',required=True,type=Path)
    p.add_argument('--first',required=True,type=Path)
    p.add_argument('--second',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    br,bkeys=read_br(a.br)
    x,xkeys=read_bu(a.first)
    y,ykeys=read_bu(a.second)
    bu=x+y
    out={'vote_totals_match':br==bu,'section_keys_match':bkeys==(xkeys|ykeys),
         'br_sections':len(bkeys),'bu_sections':len(xkeys|ykeys),
         'by_round_and_vote_number':{f'{rnd}:{vote}':count for (rnd,vote),count in sorted(br.items())},
         'only_br_categories':{str(k):v for k,v in (br-bu).items()},
         'only_bu_categories':{str(k):v for k,v in (bu-br).items()},
         'only_br_section_keys':len(bkeys-(xkeys|ykeys)),
         'only_bu_section_keys':len((xkeys|ykeys)-bkeys)}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(out,indent=2,ensure_ascii=False))
    if not(out['vote_totals_match'] and out['section_keys_match']):raise SystemExit('Cross-source mismatch')

if __name__=='__main__':main()
