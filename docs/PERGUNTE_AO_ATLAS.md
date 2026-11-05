# Pergunte ao Atlas

A interface usa o mesmo catálogo, filtros, arquivos, versão R2 e cálculos do Explorador. Os dados da resposta são calculados no navegador a partir desses arquivos. A API interpreta a pergunta e devolve os filtros. As mensagens usam texto simples.

## Teste em desenvolvimento

Sirva a raiz do repositório com `python -m http.server 8000 --bind 127.0.0.1` e abra `http://127.0.0.1:8000/` ou `/en/`. O modo local usa um interpretador simples em português e inglês para exercitar a interface com dados reais do Explorador. Os comprovantes começam por `DEV-` e existem apenas na página aberta. Para testar os contratos HTTP com um servidor local que implemente os endpoints, abra a página com `?atlas-chat-api=local`. Essa opção só funciona em loopback.

## API prevista para produção

Configure `productionApi.origin` em `assets/atlas-chat.js`. O endereço previsto é `https://atlas-api.electoralintegrity.org`. Autorize o domínio do Atlas via CORS para `POST`, `OPTIONS` e `Content-Type: application/json`. A ativação em produção depende de validar os dois endpoints e o navegador no domínio oficial. Depois, mude `productionApi.enabled` para `true` e atualize a versão de `atlas-chat.js` nos dois HTMLs.

### POST /api/chat

Recebe `message`, `locale`, `explorer` (filtros ativos), `previousSelection` e `previousMetric` quando disponíveis e `history` com até cinco mensagens anteriores do visitante. Os filtros abaixo usam os mesmos códigos e valores do Explorador.

- Exemplo de resultado. `{"kind":"result","selection":{"uf":"AP","municipio":"06050","mode":"analisar","turno":"2"},"metric":"m:2"}`.
- Para comparação histórica, use `"mode":"comparar"`, `"comparacao":"historico1"` ou `"historico2"` e `"ano":"2022"` (2010, 2014, 2018 ou 2022). Para comparar os turnos de 2026, use `"comparacao":"turnos"`.
- `local` e `secao` usam `zona:código`. `municipio` usa o código TSE como texto, preservando zeros à esquerda. Informe a UF sempre.
- Omitir `metric` mostra todos os indicadores e candidatos disponíveis. Os indicadores vão de `m:0` (aptos) a `m:5` (nulos), na ordem do Explorador. Para candidato, use `c:` seguido do nome completo em maiúsculas, sem diacríticos.
- Solicite somente o filtro essencial ausente com `{"kind":"clarification","message":"Qual é a zona eleitoral?"}`. Use `kind: "unsupported"` para escopos sem suporte. Use o idioma de `locale`.

### POST /api/questoes

- Com `action: "submit"`, recebe `summary`, `requestId` e `locale` após a confirmação do visitante. Armazene o relato em triagem privada. Trate o `requestId` como chave idempotente para reenvios.
- A resposta inicial é `{"status":"received","receipt":"<código-privado-opaco>"}`. O código privado deve ser imprevisível e não deve aparecer em URLs, logs públicos ou Issues. Mostre-o somente ao visitante.
- Com `action: "status"`, recebe `receipt` e devolve apenas o estado autorizado por esse código. Use `received`, `triage` ou `{"status":"published","issueNumber":123}`. O número do protocolo surge quando a Issue é publicada e é o próprio `issueNumber`. A interface gera o link oficial para a Issue a partir desse número.
- A triagem decide o conteúdo público antes de abrir a Issue. A chave da API, as credenciais do GitHub App e o relato original ficam no servidor.
