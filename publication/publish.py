#!/usr/bin/env python3
"""Reconstrói uma transferência validada sobre a main atual."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import sys

stage = Path(sys.argv[1]).resolve()
repo = Path(sys.argv[2]).resolve()
transfer = json.loads((stage / 'publication/transfer.json').read_text())
source = stage / 'assembled'
source.mkdir(exist_ok=True)
for entry in transfer['files']:
    if (source / entry['nome']).name != entry['nome']:
        raise ValueError('Invalid filename')
    if not (source / entry['nome']).is_file():
        raise ValueError('Missing downloaded source')

# Validate all artefacts before copying any code or touching navigation.
spec = importlib.util.spec_from_file_location('importer', stage / 'publication/code/scripts/importar-documentos.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for entry in transfer['files']:
    module.check_file(source / entry['nome'], entry)
for name in transfer['code']:
    if name not in ['scripts/importar-documentos.py', 'assets/atlas-documents.css', 'assets/atlas-documents.js', 'docs/PUBLICACAO_DOCUMENTOS.md', 'HANDOFF.md', 'REVIEW.md']:
        raise ValueError('Unexpected code path')
    origin = stage / 'publication/code' / name
    target = repo / name
    if target.exists() and target.read_bytes() != origin.read_bytes():
        raise ValueError('Existing implementation differs: ' + name)
for name in transfer['code']:
    origin = stage / 'publication/code' / name
    target = repo / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(origin, target)
catalog = module.import_files(source, json.loads((stage / 'publication/manifest.json').read_text()), repo)
for name, url, label in [('index.html', 'documentos/', 'Documentos'), ('en/index.html', '../documentos/', 'Documents')]:
    path = repo / name
    text = path.read_text()
    link = f'<a href="{url}">{label}</a>'
    if link not in text:
        marker = '<a href="#estudos">'
        if text.count(marker) != 1:
            raise ValueError('Navigation structure changed: ' + name)
        text = text.replace(marker, link + marker, 1)
        path.write_text(text)
print(f'PASS: {module.validate(catalog, repo)} arquivos prontos; navegação PT/EN preservada')
