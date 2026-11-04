#!/usr/bin/env python3
"""Gera Governador e Senado do RJ a partir dos CSVs RJ dos ZIPs oficiais do TSE."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from gerar_dados import CD, CHAVE, TOTAIS, compactar, gravar_totais_por_cargo

CARGOS = {3: "governador", 5: "senador"}
FILTRO = ["ANO_ELEICAO", "CD_CARGO", "CD_ELEICAO", *CHAVE]
NOMINAL = "QT_VOTOS_NOMINAIS_VALIDOS"
BRUTO = "QT_VOTOS_NOMINAIS"
CADASTRO = ["NR_CANDIDATO", "NM_URNA_CANDIDATO", "SG_PARTIDO", "NM_COLIGACAO",
            "DS_COMPOSICAO_COLIGACAO", "SG_FEDERACAO"]


def ler_csv(path, campos):
    dados = pd.read_csv(path, sep=";", encoding="latin-1", usecols=FILTRO + campos,
                        keep_default_na=False)
    return dados.loc[dados.ANO_ELEICAO.eq(2026) & dados.CD_ELEICAO.eq(6259) &
                     dados.NR_TURNO.eq(1) & dados.SG_UF.eq("RJ") &
                     dados.CD_CARGO.isin(CARGOS)].copy()


def fonte(path, conjunto):
    with path.open("rb") as arquivo:
        digest = hashlib.file_digest(arquivo, "sha256").hexdigest()
    return {
        "url": f"https://cdn.tse.jus.br/estatistica/sead/odsele/{conjunto}/{conjunto}_2026.zip",
        "membro": f"{conjunto}_2026_RJ.csv",
        "sha256_membro": digest,
    }


def gerar(detalhe_path, nominal_path, destino):
    catalogo = json.loads((destino / "catalogo.json").read_text())
    municipios = {int(codigo) for codigo in catalogo["uf"]["RJ"]}
    if len(municipios) != 92:
        raise ValueError("O catálogo do RJ precisa conter 92 municípios.")
    detalhe = ler_csv(detalhe_path, [*TOTAIS, "DT_ULTIMA_TOTALIZACAO"])
    nominal = ler_csv(nominal_path, [*CADASTRO, BRUTO, NOMINAL])
    fontes = [fonte(detalhe_path, "detalhe_votacao_munzona"),
              fonte(nominal_path, "votacao_candidato_munzona")]

    for codigo, cargo in CARGOS.items():
        apuracao = detalhe.loc[detalhe.CD_CARGO.eq(codigo)]
        votos = nominal.loc[nominal.CD_CARGO.eq(codigo)]
        resumo = apuracao.groupby(CHAVE)[TOTAIS].sum()
        if set(resumo.index.get_level_values(CD)) != municipios or set(votos[CD]) != municipios:
            raise ValueError(f"{cargo}: cobertura municipal divergente.")
        candidatos = votos[CADASTRO].drop_duplicates()
        if candidatos.NR_CANDIDATO.duplicated().any():
            raise ValueError(f"{cargo}: cadastro divergente para o mesmo número.")
        validos = votos.groupby(CHAVE + ["NR_CANDIDATO"])[NOMINAL].sum().unstack(fill_value=0)
        numeros = sorted(validos.columns)
        resumo = resumo.join(validos, how="left")
        if not resumo[numeros].sum(axis=1).eq(resumo[TOTAIS[3]]).all():
            raise ValueError(f"{cargo}: votos nominais válidos divergem da apuração municipal.")
        estadual = resumo.sum().to_frame().T
        estadual.index = pd.MultiIndex.from_tuples([("RJ", 0, 1)], names=CHAVE)
        registros = compactar(pd.concat([resumo, estadual]), numeros)["RJ"]
        brutos = votos.groupby("NR_CANDIDATO")[BRUTO].sum()
        fichas = {int(n): {
            "nome": nome, "partido": partido, "coligacao": coligacao,
            "composicao": composicao, "federacao": federacao, "votos_nominais_uf": int(brutos[n]),
        } for n, nome, partido, coligacao, composicao, federacao in candidatos.sort_values(
            "NR_CANDIDATO").itertuples(index=False, name=None)}
        data = pd.to_datetime(apuracao.DT_ULTIMA_TOTALIZACAO, format="%d/%m/%Y").max()
        gravar_totais_por_cargo(destino, 2026, cargo, "RJ", registros,
                              candidatos=fichas, ultima_totalizacao=data.date().isoformat(), fontes=fontes)
        print(f"{cargo}: {len(municipios)} municípios e {int(estadual.iloc[0][TOTAIS[3]])} votos válidos.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("detalhe", type=Path)
    parser.add_argument("nominal", type=Path)
    parser.add_argument("destino", type=Path)
    args = parser.parse_args()
    gerar(args.detalhe, args.nominal, args.destino)
