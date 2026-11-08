# Relatórios e pacotes do Atlas

Os 13 arquivos da coleção Busca de equações são publicações de artefactos existentes. A importação não recalcula nem altera as análises. A área pública fica em `/documentos/`, com sete etapas, sete HTMLs e seis ZIPs.

## Importar e validar

```bash
python3 scripts/importar-documentos.py --origem /caminho/dos/arquivos --manifesto /caminho/manifest.json
python3 scripts/importar-documentos.py --validar
```

O manifesto usa o mesmo formato de `documentos/catalogo.json`, sem exigir o campo `caminho` dos arquivos de entrada. Cada documento tem identificador, título, versão, data, ordem e lista de arquivos; cada arquivo tem nome, tipo (`html` ou `zip`), tamanho em bytes e SHA-256. A importação é idempotente. Conteúdo diferente exige nova versão. Os caminhos incluem identificador, versão e hash; não há substituição silenciosa de uma versão publicada.

## Publicação pelo App

A branch `atlas-documentos-publish` contém o workflow `publish-atlas-documents.yml`. O environment `atlas-r2` gera autorizações S3 PUT temporárias, limitadas aos 13 caminhos imutáveis. As autorizações são cifradas com uma chave pública de transferência e somente o executor que tem a chave privada consegue lê-las. Nenhuma credencial R2 ou chave privada sai do Actions. O executor transfere os arquivos binários diretamente ao R2; o workflow lê os bytes no domínio público, confere tamanho, SHA-256 e ZIPs e publica os arquivos e o catálogo na `main` com o App `elis-atlas-publisher`.

O App usa o secret `ATLAS_PUBLISHER_PRIVATE_KEY` e a variável `ATLAS_PUBLISHER_CLIENT_ID`. O transporte R2 usa os mesmos secrets e variáveis já utilizados em `publish-atlas-data-r2.yml`. Não se imprime Base64 de arquivos nem as autorizações temporárias.

O workflow trabalha sobre a `main` mais recente, acrescenta os documentos e insere apenas o link de navegação nas páginas iniciais PT/EN. O push é normal, sem force. Concorrência ou arquivos inesperados fazem a publicação parar para revisão. O GitHub Pages publica o commit do bot.

## R2 opcional

O GitHub é a origem dos links desta publicação. O bucket `elis-atlas-data` serve como transporte binário e réplica, preservando as chaves `documentos/arquivos/...` e os hashes. Usar `Content-Type: text/html; charset=utf-8` para HTML, `application/zip` para ZIP, e cache imutável nos caminhos com hash. O catálogo e os links públicos continuam a apontar para o GitHub até haver uma alteração explícita, após verificar os bytes no domínio público do R2. A configuração e os secrets R2 existentes ficam preservados em `docs/PUBLICACAO_R2.md`.

## Recuperação de 8 de novembro de 2026

Base conferida: `4f9c0b1f9a31582aa812def339458b860ed855d2`. Não havia branch, PR nem workflow publicado para esta coleção. O ambiente da sessão de equações e o código não publicado não estavam disponíveis; os 13 artefactos foram recuperados dos arquivos salvos. O registro anterior identifica a etapa `Encoding ZIP File as Base64`, mas não contém a exceção detalhada. No teste desta sessão, a saída do executor foi truncada a aproximadamente 1 MiB ao tentar transportar 2.165.612 caracteres Base64. A codificação em si terminou; o limite estava na passagem do resultado. Os blocos de 512 KiB ficam abaixo desse limite após a codificação. Não se afirma que esta foi a exceção original, cujo detalhe não foi recuperado. A transferência limitada em blocos evita transportar uma representação Base64 de todos os ZIPs em uma única operação.
