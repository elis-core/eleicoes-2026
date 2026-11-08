import hashlib
import json
from pathlib import Path
import time
import urllib.request
import urllib.error
import sys

stage = Path('stage')
source = stage / 'assembled'
source.mkdir(exist_ok=True)
manifest = json.loads((stage / 'publication/manifest.json').read_text())
pending = []
for doc in manifest['documentos']:
    for entry in doc['arquivos']:
        key = f'documentos/arquivos/{doc["id"]}/v{doc["versao"]}/{entry["sha256"]}/{entry["nome"]}'
        pending.append((entry, 'https://atlas-data.electoralintegrity.org/' + key))
deadline = time.monotonic() + 900
while pending and time.monotonic() < deadline:
    remaining = []
    for entry, url in pending:
        try:
            with urllib.request.urlopen(url + '?transfer=' + str(time.time_ns()), timeout=30) as response:
                blob = response.read()
            if len(blob) != entry['tamanho'] or hashlib.sha256(blob).hexdigest() != entry['sha256']:
                raise ValueError('Published R2 bytes differ: ' + entry['nome'])
            (source / entry['nome']).write_bytes(blob)
            print('Verified:', entry['nome'], flush=True)
        except (urllib.error.URLError, TimeoutError):
            remaining.append((entry, url))
    pending = remaining
    if pending:
        print(f'Waiting for {len(pending)} uploads', flush=True)
        time.sleep(10)
if pending:
    raise SystemExit('Upload deadline exceeded')
print('All 13 R2 downloads match their expected SHA-256.', flush=True)
