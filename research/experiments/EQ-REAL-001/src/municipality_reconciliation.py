#!/usr/bin/env python3
"""Aggregate audited presidential section observations to RN municipality totals."""
import argparse, collections, csv, json, pathlib
FIELDS=("E1","C1","A1","E2","C2","A2","LULA1","FLAVIO1","OTHERS1","B1","N1","LULA2","FLAVIO2","B2","N2")

def aggregate(source, destination):
    municipalities=collections.defaultdict(collections.Counter)
    sections=collections.Counter()
    with source.open(newline="",encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key=(row["CD_MUNICIPIO"],row["NM_MUNICIPIO"])
            for field in FIELDS:
                municipalities[key][field]+=int(row[field])
            sections[key]+=1
    result=[]
    for (code,name),counts in sorted(municipalities.items()):
        r={"municipality_code":code,"municipality":name,"sections":sections[(code,name)]}
        r.update({field:counts[field] for field in FIELDS})
        r["round1_residual"]=r["C1"]-sum(r[f] for f in ("LULA1","FLAVIO1","OTHERS1","B1","N1"))
        r["round2_residual"]=r["C2"]-sum(r[f] for f in ("LULA2","FLAVIO2","B2","N2"))
        result.append(r)
    if any(r["round1_residual"] or r["round2_residual"] for r in result):
        raise ValueError("Municipality-level presidential turnout identity failed")
    with destination.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(result[0]))
        writer.writeheader()
        writer.writerows(result)
    return {"municipalities":len(result),"sections":sum(x["sections"] for x in result),
            "round2_turnout":sum(x["C2"] for x in result),"accounting_failures":0}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--sections",required=True,type=pathlib.Path)
    p.add_argument("--output",required=True,type=pathlib.Path)
    args=p.parse_args()
    print(json.dumps(aggregate(args.sections,args.output),indent=2))
