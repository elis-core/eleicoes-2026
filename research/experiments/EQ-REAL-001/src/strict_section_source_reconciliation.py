#!/usr/bin/env python3
"""Strict section×candidate/category cross-source equality for RN presidential votes.

Source archives remain unmodified. Requires pandas for nationwide CSV streaming.
"""
import argparse
import collections
import csv
import io
import json
import zipfile
from pathlib import Path

KEYS = ('NR_TURNO','CD_MUNICIPIO','NR_ZONA','NR_SECAO','NR_VOTAVEL')

def read_bu(path):
    totals={}
    duplicates=0
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        member=next(x for x in z.namelist() if x.lower().endswith('.csv'))
        with z.open(member) as f:
            reader=csv.DictReader(io.TextIOWrapper(f,encoding='latin-1',newline=''),delimiter=';')
            for row in reader:
                if row['DS_CARGO_PERGUNTA']!='Presidente':continue
                key=tuple(row[k] for k in KEYS)
                if key in totals:duplicates+=1
                totals[key]=totals.get(key,0)+int(row['QT_VOTOS'])
    return totals,duplicates

def read_br(path):
    import pandas as pd
    totals={}
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        member=next(x for x in z.namelist() if x.lower().endswith('.csv'))
        cols=list(KEYS)+['SG_UF','DS_CARGO','QT_VOTOS']
        for chunk in pd.read_csv(z.open(member),dtype=str,sep=';',encoding='latin1',
                                 usecols=cols,chunksize=250000):
            rn=chunk[(chunk['SG_UF']=='RN')&(chunk['DS_CARGO'].str.upper()=='PRESIDENTE')]
            for row in rn[list(KEYS)+['QT_VOTOS']].itertuples(index=False,name=None):
                key=row[:-1]
                totals[key]=totals.get(key,0)+int(row[-1])
    return totals

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--br',required=True,type=Path)
    p.add_argument('--first',required=True,type=Path)
    p.add_argument('--second',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    x,dx=read_bu(args.first)
    y,dy=read_bu(args.second)
    bu={**x,**y}
    if len(bu)!=len(x)+len(y):raise ValueError('Duplicate keys across round files')
    br=read_br(args.br)
    discrepancies=[{'key':key,'bu':bu.get(key),'br':br.get(key)}
                   for key in sorted(bu.keys()|br.keys()) if bu.get(key)!=br.get(key)]
    result={'bu_records':len(bu),'br_records':len(br),
            'duplicate_bu_rows':dx+dy,
            'identical_keys':set(bu)==set(br),
            'discrepancy_count':len(discrepancies),
            'discrepancy_sample':discrepancies[:20]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    if discrepancies or dx or dy:raise SystemExit('Strict source mismatch or duplicated BU category')

if __name__=='__main__':main()
