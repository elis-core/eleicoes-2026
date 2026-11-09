#!/usr/bin/env python3
"""Reproduce the RN 2026 presidential section accounting audit from original TSE BU ZIPs."""
import argparse, collections, csv, hashlib, io, json, pathlib, zipfile
K = ("CD_MUNICIPIO", "NR_ZONA", "NR_SECAO")
META = ("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES",
        "NR_LOCAL_VOTACAO", "NM_MUNICIPIO", "DS_SECOES_AGREGADAS")

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1048576), b""):
            digest.update(part)
    return digest.hexdigest()

def load(path):
    sections, duplicate, metadata_errors = {}, 0, 0
    rows, counts = 0, collections.Counter()
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None, "ZIP integrity failure"
        member = next(n for n in archive.namelist() if n.endswith(".csv"))
        with archive.open(member) as binary:
            reader = csv.DictReader(io.TextIOWrapper(binary, encoding="latin-1", newline=""), delimiter=";")
            for item in reader:
                if item["DS_CARGO_PERGUNTA"] != "Presidente":
                    continue
                rows += 1
                key = tuple(item[x] for x in K)
                if key not in sections:
                    sections[key] = {"meta": {x:item[x] for x in META}, "votes": {}}
                record = sections[key]
                if any(item[x] != record["meta"][x] for x in META):
                    metadata_errors += 1
                t, cand = item["CD_TIPO_VOTAVEL"], item["NR_VOTAVEL"]
                if t not in ("1", "2", "3"):
                    raise ValueError("Unknown vote type " + t)
                category = "candidate:" + cand if t == "1" else ("blank" if t == "2" else "null")
                if category in record["votes"]:
                    duplicate += 1
                record["votes"][category] = record["votes"].get(category, 0) + int(item["QT_VOTOS"])
                counts[t] += 1
    return sections, {"presidential_csv_rows": rows, "sections": len(sections),
                      "duplicate_candidate_category_rows": duplicate,
                      "inconsistent_section_metadata_rows": metadata_errors,
                      "vote_type_rows": dict(counts)}

def audit(sections):
    errors = collections.Counter()
    totals = collections.Counter()
    for key, record in sections.items():
        e = int(record["meta"]["QT_APTOS"])
        c = int(record["meta"]["QT_COMPARECIMENTO"])
        a = int(record["meta"]["QT_ABSTENCOES"])
        if sum(record["votes"].values()) != c: errors["vote_sum_vs_turnout"] += 1
        if c + a != e: errors["turnout_plus_abstention_vs_electorate"] += 1
        if not (0 <= c <= e): errors["turnout_bounds"] += 1
        totals.update({"electorate":e, "turnout":c, "abstention":a})
        totals.update(record["votes"])
    return {"failures":dict(errors), "totals":dict(totals),
            "municipality_count":len({k[0] for k in sections})}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--first", required=True, type=pathlib.Path)
    p.add_argument("--second", required=True, type=pathlib.Path)
    p.add_argument("--output", required=True, type=pathlib.Path)
    p.add_argument("--section-csv", type=pathlib.Path)
    args = p.parse_args()
    one, r1 = load(args.first)
    two, r2 = load(args.second)
    keys = set(one) & set(two)
    joined = {"round1":len(one), "round2":len(two), "matched":len(keys),
              "round1_only":len(set(one)-set(two)), "round2_only":len(set(two)-set(one)),
              "polling_place_changed":sum(one[k]["meta"]["NR_LOCAL_VOTACAO"] != two[k]["meta"]["NR_LOCAL_VOTACAO"] for k in keys),
              "aggregation_flagged":sum(one[k]["meta"]["DS_SECOES_AGREGADAS"] != "#NULO#" or two[k]["meta"]["DS_SECOES_AGREGADAS"] != "#NULO#" for k in keys),
              "electorate_changed":sum(one[k]["meta"]["QT_APTOS"] != two[k]["meta"]["QT_APTOS"] for k in keys)}
    result = {"sha256":{args.first.name:sha(args.first), args.second.name:sha(args.second)},
              "round1_metadata":r1, "round2_metadata":r2,
              "round1_audit":audit(one), "round2_audit":audit(two), "join":joined}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    if args.section_csv:
        columns = list(K)+["NM_MUNICIPIO","NR_LOCAL_VOTACAO_1","NR_LOCAL_VOTACAO_2",
                    "E1","C1","A1","E2","C2","A2","LULA1","FLAVIO1","OTHERS1","B1","N1",
                    "LULA2","FLAVIO2","B2","N2","match_status"]
        args.section_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.section_csv.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for key in sorted(set(one)|set(two)):
                row = dict(zip(K, key))
                x, y = one.get(key), two.get(key)
                row["NM_MUNICIPIO"] = (x or y)["meta"]["NM_MUNICIPIO"]
                for record, n in ((x,"1"),(y,"2")):
                    if record is None: continue
                    m, v = record["meta"], record["votes"]
                    row["NR_LOCAL_VOTACAO_"+n] = m["NR_LOCAL_VOTACAO"]
                    for name, orig in (("E","QT_APTOS"),("C","QT_COMPARECIMENTO"),("A","QT_ABSTENCOES")):
                        row[name+n] = m[orig]
                    row["LULA"+n] = v.get("candidate:13",0)
                    row["FLAVIO"+n] = v.get("candidate:22",0)
                    row["B"+n], row["N"+n] = v.get("blank",0), v.get("null",0)
                    if n=="1":
                        row["OTHERS1"] = sum(value for name,value in v.items()
                             if name.startswith("candidate:") and name not in ("candidate:13","candidate:22"))
                row["match_status"] = ("matched" if x and y else "round1_only" if x else "round2_only")
                writer.writerow(row)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
