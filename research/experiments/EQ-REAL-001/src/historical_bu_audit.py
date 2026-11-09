#!/usr/bin/env python3
"""Year-neutral TSE presidential bweb audit. No cross-year elector identity assumptions."""
import argparse
import collections
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

REQUIRED = {'DS_CARGO_PERGUNTA','CD_MUNICIPIO','NR_ZONA','NR_SECAO',
            'CD_TIPO_VOTAVEL','NR_VOTAVEL','QT_VOTOS','QT_COMPARECIMENTO',
            'QT_APTOS','QT_ABSTENCOES'}
KEY = ('CD_MUNICIPIO','NR_ZONA','NR_SECAO')

def read_bu(path):
    result, totals = {}, collections.Counter()
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None, 'ZIP CRC failure'
        members = [n for n in z.namelist() if n.lower().endswith('.csv')]
        if len(members) != 1:
            raise ValueError('Expected one CSV member')
        with z.open(members[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='latin-1', newline=''), delimiter=';')
            missing = REQUIRED - set(reader.fieldnames or [])
            if missing: raise ValueError('Missing fields: '+str(sorted(missing)))
            for row in reader:
                if row['DS_CARGO_PERGUNTA'] != 'Presidente': continue
                totals['presidential_rows'] += 1
                key = tuple(row[k] for k in KEY)
                p = result.setdefault(key, {'meta':{
                    'turnout':int(row['QT_COMPARECIMENTO']),
                    'electorate':int(row['QT_APTOS']),
                    'abstention':int(row['QT_ABSTENCOES'])},'votes':{}})
                m=p['meta']
                if (m['turnout'] != int(row['QT_COMPARECIMENTO']) or
                    m['electorate'] != int(row['QT_APTOS']) or
                    m['abstention'] != int(row['QT_ABSTENCOES'])):
                    totals['metadata_conflict_rows'] += 1
                typ=row['CD_TIPO_VOTAVEL']
                if typ=='1':cat='nominal_'+row['NR_VOTAVEL']
                elif typ=='2':cat='blank'
                elif typ=='3':cat='null'
                else: raise ValueError('Unknown vote category: '+typ)
                if cat in p['votes']:totals['duplicate_category_rows']+=1
                p['votes'][cat]=p['votes'].get(cat,0)+int(row['QT_VOTOS'])
    for p in result.values():
        m,v=p['meta'],p['votes']
        for name in ('electorate','turnout','abstention'): totals[name]+=m[name]
        if sum(v.values())!=m['turnout']:totals['failed_turnout_identity']+=1
        if m['electorate']!=m['turnout']+m['abstention']:totals['failed_electorate_identity']+=1
        for name,count in v.items():totals[name]+=count
    totals['sections']=len(result)
    totals['municipalities']=len({k[0] for k in result})
    return result,dict(totals)

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--first',type=Path,required=True)
    p.add_argument('--second',type=Path,required=True)
    p.add_argument('--year',type=int,choices=(2022,2026),required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    one,x=read_bu(a.first)
    two,y=read_bu(a.second)
    keys=set(one)&set(two)
    result={'year':a.year,'sha256':{a.first.name:sha256(a.first),a.second.name:sha256(a.second)},
            'first':x,'second':y,'round_join':{'matches':len(keys),
            'first_only':len(set(one)-set(two)),'second_only':len(set(two)-set(one))},
            'warnings':['Ballot numbers are year-specific; do not infer constant candidate identity.',
                        'No cross-year section or elector continuity is implied.']}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
