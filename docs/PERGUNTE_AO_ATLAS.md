# Pergunte ao Atlas

O chat fica no topo das páginas em português e inglês. O Worker interpreta as perguntas e devolve os filtros, resultados, períodos, lacunas e fontes. O navegador formata a tabela com as mesmas funções do Explorador e abre o recorte com os filtros retornados.

## Desenvolvimento

Sirva a raiz com `python -m http.server 8000 --bind 127.0.0.1` e abra `http://127.0.0.1:8000/` ou `/en/`. Nesse modo a interface usa um interpretador local e simula relatos. `?atlas-chat-api=local` usa um servidor de teste de mesma origem quando o endereço está em loopback.

## API publicada

`productionApi.origin`, em `assets/atlas-chat.js`, aponta para o Worker validado em `workers.dev`. Para mudar para `https://atlas-api.electoralintegrity.org`, valide o domínio, `GET /api/health` e o CORS de `OPTIONS` e `POST /api/chat` com a origem do Atlas antes de atualizar a configuração. Atualize a versão do script nos dois HTMLs.

`POST /api/chat` recebe `message`, `filters` e `history`. O Worker retorna `type: "result"` ou `"no_data"` com `filters`, `periods`, `table`, `notes`, `explorerUrl` e `sources`, ou mensagens de esclarecimento e escopo. Os valores ausentes são `null` e aparecem como um traço.

## Relatos privados

A interface mantém a opção desativada em produção enquanto `/api/questoes` estiver indisponível. Antes de ativar `productionApi.reports`, valide submissão após revisão, comprovante opaco e consulta de situação privada. Após a triagem e publicação, o protocolo é o número da Issue criada pelo GitHub App. Credenciais e relatos originais ficam no servidor.
