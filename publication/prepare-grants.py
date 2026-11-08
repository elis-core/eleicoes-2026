import json
import os
from pathlib import Path
import re
import boto3
from botocore.config import Config

endpoint = os.environ['R2_ENDPOINT']
bucket = os.environ['R2_BUCKET']
assert re.fullmatch(r'https://[a-f0-9]{32}\.r2\.cloudflarestorage\.com', endpoint)
assert bucket == 'elis-atlas-data'
client = boto3.client('s3', endpoint_url=endpoint, region_name='auto', config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}))
manifest = json.loads(Path('stage/publication/manifest.json').read_text())
grants = []
for doc in manifest['documentos']:
    for entry in doc['arquivos']:
        key = f'documentos/arquivos/{doc["id"]}/v{doc["versao"]}/{entry["sha256"]}/{entry["nome"]}'
        mime = 'text/html; charset=utf-8' if entry['tipo'] == 'html' else 'application/zip'
        grants.append(dict(nome=entry['nome'], tamanho=entry['tamanho'], sha256=entry['sha256'], content_type=mime,
            url=client.generate_presigned_url('put_object', Params={'Bucket': bucket, 'Key': key, 'ContentType': mime, 'CacheControl': 'public, max-age=31536000, immutable'}, ExpiresIn=1800)))
Path(os.environ['GRANTS_FILE']).write_text(json.dumps({'files': grants}))
print('Prepared 13 narrowly scoped upload grants; credentials retained in runner.')
