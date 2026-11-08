#!/usr/bin/env python3
"""Importa artefactos existentes; nunca executa análises eleitorais."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def check_file(path, entry):
    if path.stat().st_size != entry['tamanho']:
        raise ValueError('Tamanho divergente: ' + entry['nome'])
    if hashlib.file_digest(path.open('rb'), 'sha256').hexdigest() != entry['sha256']:
        raise ValueError('SHA-256 divergente: ' + entry['nome'])
    if entry['tipo'] == 'zip':
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError('ZIP corrompido: ' + bad)
    elif entry['tipo'] == 'html':
        text = path.read_text(encoding='utf-8')
        if not re.search(r'<html\b', text, re.I) or not re.search(r'</html>', text, re.I):
            raise ValueError('HTML incompleto: ' + entry['nome'])
    else:
        raise ValueError('Tipo não permitido')

def validate(catalog, root=ROOT):
    assert catalog['schema'] == 1
    seen = set()
    count = 0
    for doc in catalog['documentos']:
        key = (doc['id'], doc['versao'])
        if key in seen:
            raise ValueError('Versão duplicada: ' + str(key))
        seen.add(key)
        for entry in doc['arquivos']:
            path = root / entry['caminho']
            if not path.resolve().is_relative_to((root / 'documentos/arquivos').resolve()):
                raise ValueError('Caminho inválido')
            check_file(path, entry)
            count += 1
    return count

def render(catalog, root=ROOT):
    esc = html.escape
    cards = []
    for doc in sorted(catalog['documentos'], key=lambda x: (x['ordem'], x['versao'])):
        links = []
        for f in doc['arquivos']:
            url = '../' + f['caminho']
            size = f['tamanho'] / 1048576
            label = 'Abrir relatório' if f['tipo'] == 'html' else 'Baixar pacote de reprodução'
            attrs = ' target="_blank" rel="noopener"' if f['tipo'] == 'html' else ' download'
            links.append(f'<li><a href="{esc(url)}"{attrs}>{label} · {f["tipo"].upper()}</a> <span class="file-size">{size:.2f} MB</span><details><summary>Conferir integridade</summary><p>{esc(f["nome"])}</p><code>SHA-256: {f["sha256"]}</code></details></li>')
        cards.append(f'<article class="panel document-card" data-search="{esc(doc["titulo"])}"><p class="overline">Etapa {doc["ordem"]:02d} · {esc(doc["id"])}</p><h2>{esc(doc["titulo"])}</h2><p class="hint">Versão {esc(doc["versao"])} · {esc(doc["data"])}</p><ul>{"".join(links)}</ul></article>')
    text = '''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Documentos | Atlas Eleitoral</title><meta name="description" content="Relatórios e pacotes de reprodução da busca de equações nos dois turnos."><link rel="stylesheet" href="../assets/atlas.css?v=20261105-aliancas"><link rel="stylesheet" href="../assets/atlas-documents.css?v=20261108"><script src="../assets/atlas-documents.js?v=20261108" defer></script></head>
<body><a class="skip" href="#documentos">Ir para os documentos</a><header class="top"><div class="wrap top-inner"><a class="brand" href="../"><span>Atlas <b>Eleitoral</b><small>Electoral Integrity Strategies (ELIS)</small></span></a><nav aria-label="Navegação principal"><a href="../#explorador">Explorador</a><a href="../#estudos">Estudos</a><a href="./" aria-current="page">Documentos</a></nav></div></header>
<main class="wrap documents-main" id="documentos"><p class="overline">Pesquisa e reprodução</p><h1>Busca de equações nos dois turnos</h1><p class="documents-intro">Acompanhe as sete etapas da investigação, leia os relatórios e baixe os dados e códigos disponíveis em cada pacote.</p><p class="hint">Estes documentos registam métodos, testes e limitações. Relações entre totais agregados não identificam transições individuais de voto.</p><div class="panel documents-filter" hidden><label for="document-search">Encontrar documento</label><input id="document-search" type="search" placeholder="Título ou tema"><p id="document-count" role="status"></p></div><div class="documents-grid">''' + ''.join(cards) + '''</div><p><a href="catalogo.json">Catálogo completo em JSON</a> · <a href="../">Voltar ao Atlas</a></p></main><footer><div class="wrap"><strong>Atlas Eleitoral</strong><span>Electoral Integrity Strategies (ELIS)</span></div></footer></body></html>
'''
    (root / 'documentos/index.html').write_text(text, encoding='utf-8')

def import_files(source, manifest, root=ROOT):
    source = Path(source)
    dest = root / 'documentos/catalogo.json'
    catalog = json.loads(dest.read_text()) if dest.exists() else {'schema': 1, 'documentos': []}
    pending = []
    for doc in manifest['documentos']:
        if not re.fullmatch(r'[A-Z0-9-]+', doc['id']) or not re.fullmatch(r'\d+\.\d+', doc['versao']):
            raise ValueError('Identificador ou versão inválidos')
        new_doc = dict(doc, arquivos=[])
        for entry in doc['arquivos']:
            if Path(entry['nome']).name != entry['nome'] or not re.fullmatch(r'[a-f0-9]{64}', entry['sha256']):
                raise ValueError('Nome ou hash inválidos')
            matches = list(source.rglob(entry['nome']))
            if len(matches) != 1:
                raise ValueError('Esperado um arquivo: ' + entry['nome'])
            check_file(matches[0], entry)
            relative = f'documentos/arquivos/{doc["id"]}/v{doc["versao"]}/{entry["sha256"]}/{entry["nome"]}'
            target = root / relative
            if target.exists():
                check_file(target, entry)
            new_doc['arquivos'].append(dict(entry, caminho=relative))
            pending.append((matches[0], target))
        old = next((d for d in catalog['documentos'] if (d['id'], d['versao']) == (doc['id'], doc['versao'])), None)
        if old and old != new_doc:
            raise ValueError('Uma versão existente não pode ser alterada: ' + doc['id'])
        if not old:
            catalog['documentos'].append(new_doc)
    for origin, target in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copyfile(origin, target)
    validate(catalog, root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    render(catalog, root)
    return catalog

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origem', type=Path)
    parser.add_argument('--manifesto', type=Path)
    parser.add_argument('--validar', action='store_true')
    args = parser.parse_args()
    if args.validar:
        catalog = json.loads((ROOT / 'documentos/catalogo.json').read_text())
    elif args.origem and args.manifesto:
        catalog = import_files(args.origem, json.loads(args.manifesto.read_text()))
    else:
        parser.error('Use --validar ou --origem e --manifesto')
    print(f'PASS: {len(catalog["documentos"])} documentos, {validate(catalog)} arquivos íntegros')
