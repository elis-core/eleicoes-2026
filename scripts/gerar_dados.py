#!/usr/bin/env python3
"""Converte os ZIPs presidenciais do TSE em pacotes estáticos do Atlas."""
import argparse
import base64
import gzip
import hashlib
import json
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

ANOS = (2026, 2022, 2018, 2014, 2010)
CHAVE = ["SG_UF", "CD_MUNICIPIO", "NR_TURNO"]
SEC = CHAVE + ["NR_ZONA", "NR_SECAO"]
LOCAL = "NR_LOCAL_VOTACAO"
TOTAIS = ["QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES", "QT_TOTAL_VOTOS_VALIDOS",
          "QT_VOTOS_BRANCOS", "QT_TOTAL_VOTOS_NULOS"]
CD, NM, NS = "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_SECAO"
NOME_LOCAL = "NM_LOCAL_VOTACAO"
ENDERECO = "DS_LOCAL_VOTACAO_ENDERECO"
PASTAS = ["detalhe_votacao_munzona", "votacao_candidato_munzona", "detalhe_votacao_secao", "votacao_secao"]


def extrair(pasta, ano, fonte, colunas, blocos=False):
    nome = f"{fonte}_{ano}"
    caminho = pasta / f"{nome}{'_BR' if fonte == 'votacao_secao' else ''}.zip"
    with ZipFile(caminho) as zip_:
        with zip_.open(f"{nome}_BR.csv") as arquivo:
            leitor = pd.read_csv(arquivo, sep=";", encoding="latin-1", usecols=colunas,
                                 keep_default_na=False, chunksize=350_000 if blocos else None)
            if blocos:
                for trecho in leitor:
                    yield trecho.loc[trecho.SG_UF.ne("ZZ") & trecho.CD_CARGO.eq(1)]
            else:
                yield leitor.loc[leitor.SG_UF.ne("ZZ") & leitor.CD_CARGO.eq(1)]


def nomes_locais(pasta, ano):
    with ZipFile(pasta / f"eleitorado_local_votacao_{ano}.zip") as zip_:
        with zip_.open(f"eleitorado_local_votacao_{ano}.csv") as arquivo:
            cols = ["SG_UF", CD, "NR_ZONA", LOCAL, NOME_LOCAL, "DS_ENDERECO"]
            return pd.read_csv(arquivo, sep=";", encoding="latin-1", usecols=cols, keep_default_na=False)


def compactar(df, numeros):
    saida = defaultdict(dict)
    for idx, *valores in df.itertuples(index=True, name=None):
        uf, mun, turno = idx
        saida[uf].setdefault(str(mun).zfill(5) if mun else "", {})[str(turno)] = valores[:6] + [
            [num, qtd] for num, qtd in zip(numeros, valores[6:]) if qtd > 0
        ]
    return dict(saida)


def processar(pasta, ano):
    print(f"{ano}: leitura", flush=True)
    detalhe, nominal, detalhe_sec, nominal_sec = PASTAS
    totais = next(extrair(pasta, ano, detalhe, set(CHAVE + [NM, "CD_CARGO", *TOTAIS, "QT_VOTOS_NULOS"]).__contains__))
    if TOTAIS[-1] not in totais:
        totais[TOTAIS[-1]] = totais.QT_VOTOS_NULOS
    col_cand = CHAVE + ["CD_CARGO", "NR_CANDIDATO", "NM_URNA_CANDIDATO",
                        "NM_CANDIDATO", "QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"]
    cand = next(extrair(pasta, ano, nominal, set(col_cand).__contains__))
    valor = "QT_VOTOS_NOMINAIS_VALIDOS" if "QT_VOTOS_NOMINAIS_VALIDOS" in cand else "QT_VOTOS_NOMINAIS"
    positivos = cand.loc[cand[valor].gt(0)]
    cadastro = {int(n): [urna, nome] for n, urna, nome in positivos[
        ["NR_CANDIDATO", "NM_URNA_CANDIDATO", "NM_CANDIDATO"]
    ].drop_duplicates("NR_CANDIDATO").itertuples(index=False, name=None)}
    numeros = sorted(cadastro)
    votacao = cand.groupby(CHAVE + ["NR_CANDIDATO"])[valor].sum().unstack(fill_value=0).reindex(columns=numeros, fill_value=0)
    resumo = totais.groupby(CHAVE)[TOTAIS].sum().join(votacao, how="left").fillna(0).astype(int)
    if not resumo[numeros].sum(axis=1).eq(resumo[TOTAIS[3]]).all():
        raise ValueError(f"{ano}: soma dos candidatos municipais diverge dos válidos")
    estadual = resumo.groupby(level=["SG_UF", "NR_TURNO"]).sum().reset_index()
    estadual[CD] = 0
    municipal = compactar(pd.concat([resumo, estadual.set_index(CHAVE)]), numeros)
    municipios = {(uf, str(m).zfill(5)): nome for uf, m, nome in totais[["SG_UF", CD, NM]].drop_duplicates().itertuples(index=False, name=None)}

    metricas_sec = TOTAIS[:3] + ["QT_VOTOS_NOMINAIS", "QT_VOTOS_BRANCOS", "QT_VOTOS_NULOS"]
    detalhes = next(extrair(pasta, ano, detalhe_sec, set(SEC + [LOCAL, "CD_CARGO", NOME_LOCAL, ENDERECO] + metricas_sec).__contains__))
    chaves_locais = ["SG_UF", CD, "NR_ZONA", LOCAL]
    if NOME_LOCAL not in detalhes:
        locais = nomes_locais(pasta, ano).rename(columns={"DS_ENDERECO": ENDERECO})
    else:
        locais = detalhes
    locais = locais.loc[locais[LOCAL].gt(0), chaves_locais + [NOME_LOCAL, ENDERECO]].drop_duplicates(chaves_locais)
    validos_turno = {(t, num) for t, num in positivos[["NR_TURNO", "NR_CANDIDATO"]].itertuples(index=False, name=None)}
    blocos = []
    numeros_registrados = sorted(cand.loc[cand.QT_VOTOS_NOMINAIS.gt(0), "NR_CANDIDATO"].unique())
    col_sec = set(SEC + ["CD_CARGO", "NR_VOTAVEL", "QT_VOTOS", "SQ_CANDIDATO"])
    for trecho in extrair(pasta, ano, nominal_sec, col_sec.__contains__, True):
        # A votação por seção também pode registrar candidato ausente da
        # votação nominal oficial, por exemplo por indeferimento posterior.
        candidatura = trecho.NR_VOTAVEL.isin(numeros_registrados)
        if "SQ_CANDIDATO" in trecho:
            candidatura |= pd.to_numeric(trecho.SQ_CANDIDATO, errors="coerce").gt(0)
        trecho = trecho.loc[candidatura & trecho.QT_VOTOS.gt(0)]
        blocos.append(trecho.groupby(SEC + ["NR_VOTAVEL"]).QT_VOTOS.sum())
    votos = pd.concat(blocos).groupby(level=list(range(6))).sum().unstack(fill_value=0)
    votos["nominais_brutos"] = votos.sum(axis=1)
    votos = votos.reindex(columns=numeros + ["nominais_brutos"], fill_value=0)
    for turno in (1, 2):
        votos.loc[votos.index.get_level_values("NR_TURNO") == turno,
                  [n for n in numeros if (turno, n) not in validos_turno]] = 0
    base = detalhes.groupby(SEC)[metricas_sec].sum()
    base[LOCAL] = detalhes.groupby(SEC)[LOCAL].first()
    base = base.join(votos, how="left").fillna(0).astype(int)
    ajustado = base[numeros].sum(axis=1)
    # O detalhe da seção informa os nominais brutos. A destinação dos votos
    # no arquivo município/zona determina quais entram nos válidos.
    base["consistente"] = base.pop("nominais_brutos").eq(base[metricas_sec[3]])
    divergentes = int((~base["consistente"]).sum())
    base.loc[base["consistente"], metricas_sec[3]] = ajustado[base["consistente"]]
    validos_por_municipio = base.groupby(level=CHAVE)[metricas_sec[3]].sum()
    confronto = validos_por_municipio.to_frame("secoes").join(resumo[TOTAIS[3]], how="outer")
    divergencias_mun = int(confronto.secoes.ne(confronto[TOTAIS[3]]).sum())
    base = base.reorder_levels(["SG_UF", CD, "NR_ZONA", NS, "NR_TURNO"]).sort_index()
    dados = defaultdict(lambda: {"l": {}, "s": {}})
    for uf, mun, zona, local, nome, endereco in locais.itertuples(index=False, name=None):
        if uf != "ZZ" and isinstance(nome, str) and not nome.startswith("#"):
            dados[(uf, str(mun).zfill(5))]["l"][f"{zona}:{local}"] = [nome, "" if endereco.startswith("#") else endereco]
    for (uf, mun, zona, secao, turno), *vals in base.itertuples(index=True, name=None):
        q = vals[:6]
        local = vals[6]
        votos_sec = vals[7:-1]
        if not vals[-1]:
            q[3] = None
        linha = [local, *q, *votos_sec] if vals[-1] else [local, *q]
        item = dados[(uf, str(mun).zfill(5))]["s"].setdefault(f"{zona}:{secao}", [None, None])
        item[turno - 1] = linha
    print(f"{ano}: {len(base):,} seção–turnos, {divergentes:,} divergências nominais", flush=True)
    turnos = {t: sorted(n for tt, n in validos_turno if tt == t) for t in (1, 2)}
    controle = {"secoes_turno": len(base), "divergencias_nominais": divergentes,
                "municipios_turno_com_diferenca_de_validos_por_fonte": divergencias_mun}
    return municipal, municipios, cadastro, numeros, turnos, dict(dados), controle


def json_bytes(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()


def gravar_compactado(caminho, objeto):
    caminho.write_bytes(base64.b64encode(gzip.compress(json_bytes(objeto), mtime=0)))


def escrever_pacotes(pasta, prefixo, itens, limite=480_000):
    # Agrupa municípios vizinhos em pacotes pequenos, sem baixar o país inteiro.
    pacote, estimativa, numero, indice = {}, 0, 0, {}

    def gravar():
        if pacote:
            gravar_compactado(pasta / f"{prefixo}-{numero}.json.gz.b64", pacote)

    for chave, valor in itens:
        tamanho = len(gzip.compress(json_bytes(valor), compresslevel=1))
        if pacote and estimativa + tamanho > limite:
            gravar()
            pacote, estimativa, numero = {}, 0, numero + 1
        pacote[chave] = valor
        estimativa += tamanho
        indice[chave] = numero
    gravar()
    return indice


def fontes(pasta):
    base = "https://cdn.tse.jus.br/estatistica/sead/odsele/"
    for ano in ANOS:
        categorias = PASTAS + (["eleitorado_local_votacao"] if ano <= 2014 else [])
        for fonte in categorias:
            nome = f"{fonte}_{ano}{'_BR' if fonte == 'votacao_secao' else ''}.zip"
            if fonte == "eleitorado_local_votacao":
                nome = f"eleitorado_local_votacao_{ano}.zip"
                fonte = "eleitorado_locais_votacao"
            caminho = pasta / nome
            with caminho.open("rb") as arquivo:
                sha = hashlib.file_digest(arquivo, "sha256").hexdigest()
            yield {"ano": ano, "url": base + fonte + "/" + nome, "sha256": sha, "bytes": caminho.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origem", type=Path)
    parser.add_argument("destino", type=Path)
    parser.add_argument("--processos", type=int, default=2)
    args = parser.parse_args()
    args.destino.mkdir(parents=True, exist_ok=True)
    catalogo, indice, ufs, relatorio = {}, {}, {}, {}
    with ProcessPoolExecutor(max_workers=args.processos) as pool:
        trabalhos = {ano: pool.submit(processar, args.origem, ano) for ano in ANOS}
        for ano, trabalho in trabalhos.items():
            municipal, nomes, candidatos, ordem, turnos, detalhes, relatorio[ano] = trabalho.result()
            catalogo[ano] = {"candidatos": candidatos, "ordem": ordem, "turnos": turnos}
            indice[ano] = {}
            for uf, registros in sorted(municipal.items()):
                if ano == ANOS[0]:
                    ufs[uf] = {m: nomes[uf, m] for m in registros if m}
                gravar_compactado(args.destino / f"municipios-{ano}-{uf}.json.gz.b64", registros)
            del municipal
            por_uf = defaultdict(list)
            for (uf, mun), dado in sorted(detalhes.items()):
                if dado["s"]:
                    por_uf[uf].append((mun, dado))
            for uf, itens in por_uf.items():
                indice[ano][uf] = escrever_pacotes(args.destino, f"secoes-{ano}-{uf}", itens)
    (args.destino / "catalogo.json").write_bytes(json_bytes({"uf": ufs, "anos": catalogo, "indice": indice}))
    (args.destino / "fontes.json").write_text(json.dumps(
        {"arquivos": list(fontes(args.origem)), "controle": relatorio}, ensure_ascii=False, indent=2) + "\n")
    print(f"Gravados {len(list(args.destino.iterdir()))} arquivos em {args.destino}", flush=True)


if __name__ == "__main__":
    main()
