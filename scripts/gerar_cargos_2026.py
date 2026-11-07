#!/usr/bin/env python3
"""Gera o piloto por cargo, preservando a destinação oficial dos votos."""
import argparse
import base64
import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

CARGOS = {"3": "governador", "5": "senador"}
CAMPOS = ["QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES", "QT_TOTAL_VOTOS_VALIDOS",
          "QT_VOTOS_BRANCOS", "QT_TOTAL_VOTOS_NULOS", "QT_VOTOS", "QT_VOTOS_NULOS",
          "QT_VOTOS_NULOS_TECNICOS", "QT_TOTAL_VOTOS_ANULADOS", "QT_TOTAL_VOTOS_ANUL_SUBJUD"]
BASE = "2026/cargos-v1"


def ler(path):
    with path.open(encoding="latin1", newline="") as f:
        yield from csv.DictReader(f, delimiter=";")


def chave(r):
    return r["CD_CARGO"], r["CD_MUNICIPIO"].zfill(5), r["NR_ZONA"], int(r["NR_TURNO"])


def elegivel(r, uf):
    return r["SG_UF"] == uf and r["CD_CARGO"] in CARGOS and r["CD_ELEICAO"] in ("6259", "6260")


def serializar(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()


def gravar(root, relative, obj, files, compressed=False):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    value = serializar(obj)
    if compressed:
        value = base64.b64encode(gzip.compress(value, mtime=0))
    path.write_bytes(value)
    files[relative] = hashlib.sha256(value).hexdigest()


def fonte(path, dataset, uf, por_uf=False):
    name = dataset + "_2026" + (f"_{uf}" if por_uf else "") + ".zip"
    with path.open("rb") as f:
        sha = hashlib.file_digest(f, "sha256").hexdigest()
    return {"url": f"https://cdn.tse.jus.br/estatistica/sead/odsele/{dataset}/{name}",
            "membro": path.name, "sha256_membro": sha}


def gerar_uf(source, target, uf, catalog, files):
    paths = {dataset: source / f"{dataset}_2026_{uf}.csv" for dataset in
             ("detalhe_votacao_munzona", "votacao_candidato_munzona", "detalhe_votacao_secao", "votacao_secao")}
    # Os ZIPs podem conter todos os estados; só extraímos o membro solicitado.
    if not paths["detalhe_votacao_munzona"].exists():
        with ZipFile(source / "detalhe_votacao_munzona_2026.zip") as z:
            z.extract(paths["detalhe_votacao_munzona"].name, source)
    totals = defaultdict(lambda: [0] * len(CAMPOS))
    latest = {}
    for r in ler(paths["detalhe_votacao_munzona"]):
        if elegivel(r, uf):
            key = chave(r)
            totals[key] = [a + int(r[k]) for a, k in zip(totals[key], CAMPOS)]
            latest[key[0]] = max(latest.get(key[0], "0001-01-01"),
                                 datetime.strptime(r["DT_ULTIMA_TOTALIZACAO"], "%d/%m/%Y").date().isoformat())
    nominal = defaultdict(Counter)
    candidates = defaultdict(dict)
    destination = {}
    for r in ler(paths["votacao_candidato_munzona"]):
        if not elegivel(r, uf):
            continue
        key, num = chave(r), r["NR_CANDIDATO"]
        nominal[key][num] += int(r["QT_VOTOS_NOMINAIS_VALIDOS"])
        record = {"nome": r["NM_URNA_CANDIDATO"], "nomeCompleto": r["NM_CANDIDATO"],
                  "partido": r["SG_PARTIDO"], "id": r["SQ_CANDIDATO"]}
        previous = candidates[(key[0], key[3])].setdefault(num, record)
        if previous != record:
            raise ValueError(f"{uf} cadastro divergente para {key}, {num}")
        valid, raw = int(r["QT_VOTOS_NOMINAIS_VALIDOS"]), int(r["QT_VOTOS_NOMINAIS"])
        label = r["NM_TIPO_DESTINACAO_VOTOS"].casefold()
        category = (
            "valid" if label == "válido" and valid == raw else
            "subjudice" if "sub judice" in label else
            "technicalNull" if "técnic" in label else
            "annulled" if "anulad" in label else "unknown"
        )
        if valid and valid != raw:
            category = "unknown"
        dest_key = (*key, num)
        if dest_key in destination and destination[dest_key] != category:
            raise ValueError("Destinação divergente")
        destination[dest_key] = category
    for key, values in totals.items():
        if values[0] != values[1] + values[2] or sum(nominal[key].values()) != values[3]:
            raise ValueError(f"{uf} apuração e nominais divergem em {key}")
        if values[5] != values[7] + values[8] or values[6] != sum(values[i] for i in (3,4,5,9,10)):
            raise ValueError(f"{uf} categorias divergentes em {key}")

    sections = {}
    locations = defaultdict(dict)
    for r in ler(paths["detalhe_votacao_secao"]):
        if not elegivel(r, uf):
            continue
        key = chave(r)
        section = (*key, r["NR_SECAO"])
        if section in sections:
            raise ValueError(f"Seção duplicada {section}")
        sections[section] = {
            "local": f'{key[2]}:{int(r["NR_LOCAL_VOTACAO"])}',
            "values": [int(r[f]) for f in ("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES")] +
                      [0, int(r["QT_VOTOS_BRANCOS"]), int(r["QT_VOTOS_NULOS"])],
            "totalVotes": 0, "ordinaryNull": int(r["QT_VOTOS_NULOS"]), "technicalNull": 0,
            "annulled": 0, "subjudice": 0, "unknown": 0,
            "votes": Counter(), "rawNominal": int(r["QT_VOTOS_NOMINAIS"]),
            "observedBlank": 0, "observedNull": 0, "observedNominal": 0
        }
        name = r.get("NM_LOCAL_VOTACAO", "")
        address = r.get("DS_LOCAL_VOTACAO_ENDERECO", "")
        locations[key[:2]][sections[section]["local"]] = [name, address]

    for r in ler(paths["votacao_secao"]):
        if not elegivel(r, uf):
            continue
        key = chave(r)
        section = (*key, r["NR_SECAO"])
        value = int(r["QT_VOTOS"])
        if value < 0 or section not in sections:
            raise ValueError("Votação fora do detalhe")
        item = sections[section]
        item["totalVotes"] += value
        num = r["NR_VOTAVEL"]
        if num in ("95", "96"):
            item["observedBlank" if num == "95" else "observedNull"] += value
            continue
        item["observedNominal"] += value
        category = destination.get((*key, num), "unknown")
        if category == "valid":
            item["votes"][num] += value
            item["values"][3] += value
        else:
            item[category] += value

    by_zone = defaultdict(list)
    for section, row in sections.items():
        by_zone[section[:4]].append(row)
    # Só distribui o restante entre categorias quando os totais por zona o identificam univocamente.
    unavailable = Counter()
    for key, rows in by_zone.items():
        official = totals.get(key)
        if official is None:
            raise ValueError(f"Seção sem apuração municipal {key}")
        unknown = sum(row["unknown"] for row in rows)
        destination_field = None
        for field, idx in (("technicalNull",8), ("annulled",9), ("subjudice",10)):
            residual = official[idx] - sum(row[field] for row in rows)
            if residual == unknown and unknown:
                if destination_field is not None:
                    destination_field = None
                    break
                destination_field = field
        if destination_field:
            for row in rows:
                row[destination_field] += row["unknown"]
                row["unknown"] = 0
        actual = [sum(row["values"][i] for row in rows) for i in range(6)]
        actual[5] += sum(row["technicalNull"] for row in rows)
        nominal_actual = sum((row["votes"] for row in rows), Counter())
        consistent = (
            actual == official[:6] and nominal_actual == +nominal[key] and
            sum(row["totalVotes"] for row in rows) == official[6] and
            all(not row["unknown"] and
                row["observedBlank"] == row["values"][4] and
                row["observedNull"] == row["ordinaryNull"] and
                row["observedNominal"] == row["rawNominal"] and
                row["totalVotes"] == row["values"][3] + row["values"][4] + row["values"][5] +
                    row["technicalNull"] + row["annulled"] + row["subjudice"] for row in rows)
        )
        for row in rows:
            row["values"][5] += row["technicalNull"]
            for field in ("rawNominal", "unknown", "observedBlank", "observedNull", "observedNominal"):
                row.pop(field)
            row["votes"] = dict(row["votes"])
            if not consistent:
                unavailable[key[0]] += 1
                row["values"][3] = row["values"][5] = None
                row["technicalNull"] = row["annulled"] = row["subjudice"] = None
                row["votes"] = None
            row["consistent"] = consistent

    sources = [fonte(path,dataset,uf,dataset == "votacao_secao") for dataset,path in paths.items()]
    coverage = {}
    for code, cargo in CARGOS.items():
        municipal = defaultdict(lambda: defaultdict(lambda: [0] * len(CAMPOS)))
        votes = defaultdict(lambda: defaultdict(Counter))
        for (c,city,zone,turn), values in totals.items():
            if c != code:
                continue
            for area in (city, ""):
                municipal[area][turn] = [a+b for a,b in zip(municipal[area][turn], values)]
                votes[area][turn].update(nominal[(c,city,zone,turn)])
        if set(municipal) - {""} != set(catalog["uf"][uf]):
            raise ValueError(f"{uf} municípios ausentes em {cargo}")
        records, extras = {}, {}
        for city, turns in municipal.items():
            records[city] = {turn: values[:6] + [[int(n),v] for n,v in sorted(votes[city][turn].items()) if v]
                             for turn,values in turns.items()}
            extras[city] = {turn: dict(zip(
                ("totalVotes","ordinaryNull","technicalNull","annulled","subjudice"),values[6:]))
                for turn,values in turns.items()}
        base = f"{BASE}/{cargo}/{uf}"
        gravar(target,f"{base}/municipios.json", {
            "schema":2,"ano":2026,"cargo":cargo,"uf":uf,"registros":records,"extras":extras,
            "candidatos":{turn:items for (c,turn),items in candidates.items() if c==code},
            "ultima_totalizacao":latest[code],"fontes":sources
        },files)
        detail = defaultdict(lambda: {"schema":2,"cargo":cargo,"ano":2026,"uf":uf,"locais":{},"secoes":{}})
        for (c,city,zone,turn,section), row in sections.items():
            if c == code:
                item = detail[city]
                item["secoes"].setdefault(f"{zone}:{section}", {})[turn] = row
                item["locais"].update(locations[(c,city)])
        for city, pack in detail.items():
            gravar(target,f"{base}/secoes-{city}.json.gz.b64",pack,files,True)
        turns = sorted(municipal[""])
        decided_first_round = cargo == "senador" or (
            max(votes[""].get(1, {}).values(), default=0) > municipal[""].get(1, [0]*len(CAMPOS))[3] / 2
        )
        coverage[cargo] = {
            "base":base,"turnos":turns,"municipios":sorted(municipal.keys()-{""}),
            "detalhados":sorted(detail),"ultima_totalizacao":latest[code],
            "secoes_sem_conciliacao":unavailable[code],
            "segundo_turno":"disponivel" if 2 in turns else
                "nao_houve_disputa" if decided_first_round else "nao_publicado"
        }
        print(uf,cargo,len(municipal)-1,"municípios",len(detail),"detalhados",
              unavailable[code],"seções sem conciliação",flush=True)
    return coverage


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("fontes",type=Path)
    p.add_argument("destino",type=Path)
    p.add_argument("--ufs",nargs="+",default=["AP","RN","RJ"])
    args=p.parse_args()
    catalog=json.loads((args.destino/"catalogo.json").read_text())
    files={}
    coverage={uf:gerar_uf(args.fontes,args.destino,uf,catalog,files) for uf in args.ufs}
    manifest={"schema":1,"ano":2026,"gerado_em":datetime.now(timezone.utc).isoformat(),
              "cargos":["governador","senador"],"ufs":coverage,"arquivos":files}
    manifest["versao"]=hashlib.sha256(serializar({"ufs":coverage,"arquivos":files})).hexdigest()
    (args.destino/"cargos-2026.json").write_bytes(serializar(manifest))
    print("Versão",manifest["versao"],len(files),"arquivos",flush=True)


if __name__=="__main__":
    main()
