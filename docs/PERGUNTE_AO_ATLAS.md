# Pergunte ao Atlas

O chat fica no topo das páginas em português e inglês. O Worker interpreta as perguntas e devolve os filtros, resultados, períodos, lacunas e fontes. O navegador formata a tabela com as mesmas funções do Explorador e abre o recorte com os filtros retornados.

## Desenvolvimento

Sirva a raiz com `python -m http.server 8000 --bind 127.0.0.1` e abra `http://127.0.0.1:8000/` ou `/en/`. Nesse modo a interface usa um interpretador local e simula relatos. `?atlas-chat-api=local` usa um servidor de teste de mesma origem quando o endereço está em loopback.

## API publicada

`productionApi.origin`, em `assets/atlas-chat.js`, aponta para o Worker validado em `workers.dev`. Para mudar para `https://atlas-api.electoralintegrity.org`, valide o domínio, `GET /api/health` e o CORS de `OPTIONS` e `POST /api/chat` com a origem do Atlas antes de atualizar a configuração. Atualize a versão do script nos dois HTMLs.

`POST /api/chat` recebe `message`, `filters`, `history` e, opcionalmente, `locale`. O Worker retorna `type: "result"` ou `"no_data"` com `filters`, `periods`, `table`, `notes`, `explorerUrl` e `sources`, ou mensagens de esclarecimento e escopo. Os valores ausentes são `null` e aparecem como um traço.

O campo opcional `guidance` contém uma mensagem de orientação e até dois links de consulta. A primeira parte da resposta mostra o limite específico e os dados disponíveis. A segunda oferece opções cuja cobertura o Worker verificou, ou pede outro recorte. As sugestões abrem o Explorador com os filtros correspondentes. Perguntas sobre causas podem receber opções de comparação, pois os totais por si só não identificam o motivo de uma variação.

## Relatos privados

A interface permite revisar o resumo antes do envio. O Worker guarda o texto em D1 e devolve um comprovante privado. A consulta pelo comprovante informa apenas a situação e, após publicação, o número da Issue. O protocolo público é esse mesmo número.

A triagem publica com o GitHub App `elis-atlas-publisher`, usando exclusivamente um texto público preparado pelo revisor. A chave do App permanece no computador do revisor. O relato original e o comprovante não integram a Issue.

O pacote de implantação contém o módulo do Worker, a migração D1 e a CLI de triagem. Valide `GET /api/questoes`, o preflight CORS e o fluxo local antes de publicar a página. O script de publicação da interface exige que a rota do Worker esteja pronta.

## Novos cargos em 2026

O piloto de Governador e Senador usa `cargo` nos filtros e nos links do Explorador. A cobertura, as taxas e a sequência de implantação estão em [CARGOS_2026.md](CARGOS_2026.md). As respostas incluem `dataVersion`, os votos brancos e nulos do cargo e a diferença entre turno sem disputa e dados ainda fora da cobertura.
