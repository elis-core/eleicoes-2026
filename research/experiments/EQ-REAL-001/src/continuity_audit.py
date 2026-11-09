#!/usr/bin/env python3
"""Audit 2026 RN section aggregation flags without modifying source ZIPs."""
import argparse, collections, csv, io, json, pathlib, zipfile

KEY = ("CD_MUNICIPIO", "NR_ZONA", "NR_SECAO")
FIELDS = ("DS_SECOES_AGREGADAS", "QT_APTOS", "QT_COMPARECIMENTO", "NR_LOCAL_VOTACAO", "NM_MUNICIPIO")

def read(path):
    sections = {}
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None, "ZIP CRC failure"
        name = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
        with archive.open(name) as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", newline=""), delimiter=";"):
                if row["DS_CARGO_PERGUNTA"] != "Presidente":
                    continue
                key = tuple(row[k] for k in KEY)
                if key not in sections:
                    sections[key] = {f:row[f] for f in FIELDS}
    return sections

def analyse(first, second):
    if set(first) != set(second):
        raise ValueError("Round-specific section keys differ; audit cannot assume 1:1 join")
    classes, changed_electorate, municipalities = collections.Counter(), collections.Counter(), collections.defaultdict(collections.Counter)
    deltas, flagged = [], []
    for key in sorted(first):
        a, b = first[key], second[key]
        x, y = a["DS_SECOES_AGREGADAS"], b["DS_SECOES_AGREGADAS"]
        category = ("none" if x == "#NULO#" and y == "#NULO#"
                    else "both_same" if x == y
                    else "only_round1" if x != "#NULO#" and y == "#NULO#"
                    else "only_round2" if x == "#NULO#" and y != "#NULO#"
                    else "changed")
        classes[category] += 1
        municipality = a["NM_MUNICIPIO"]
        municipalities[municipality][category] += 1
        delta = int(b["QT_APTOS"]) - int(a["QT_APTOS"])
        if delta:
            changed_electorate[category] += 1
            deltas.append(delta)
        if category != "none":
            flagged.append({"municipality_code":key[0],"zone":key[1],"section":key[2],
                "municipality":municipality,"aggregation_round1":x,"aggregation_round2":y,
                "aggregation_class":category,"electorate_round1":a["QT_APTOS"],
                "electorate_round2":b["QT_APTOS"],
                "turnout_round1":a["QT_COMPARECIMENTO"],"turnout_round2":b["QT_COMPARECIMENTO"]})
    return {"matched_sections":len(first),"aggregation_classes":dict(classes),
        "electorate_changed_by_class":dict(changed_electorate),
        "electorate_delta_min":min(deltas, default=0),
        "electorate_delta_max":max(deltas, default=0),
        "municipalities_with_flags":sum(any(category != "none" and n > 0 for category,n in counts.items()) for counts in municipalities.values()),
        "top_municipalities":sorted([{"municipality":name,
            "flagged":sum(n for category,n in counts.items() if category != "none"),
            "total":sum(counts.values())} for name,counts in municipalities.items()
            if any(category != "none" for category in counts)],key=lambda r:-r["flagged"])[:15]},flagged

def main():
    p=argparse.ArgumentParser()
    for name in ("first","second","output","flagged-csv"):
        p.add_argument("--"+name, type=pathlib.Path, required=True)
    args=p.parse_args()
    report, flagged=analyse(read(args.first), read(args.second))
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with args.flagged_csv.open("w",newline="",encoding="utf-8") as file:
        writer=csv.DictWriter(file,fieldnames=list(flagged[0]))
        writer.writeheader()
        writer.writerows(flagged)
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
