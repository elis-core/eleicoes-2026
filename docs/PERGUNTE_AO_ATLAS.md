# Pergunte ao Atlas

O chat fica no topo das páginas em português e inglês. O Worker interpreta as perguntas e devolve os filtros, resultados, períodos, lacunas e fontes. O navegador aplica os filtros retornados ao Explorador e apresenta a resposta nos cartões, gráficos e tabelas do painel de resultados. A conversa mantém uma confirmação curta e o acesso ao painel.

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

## Painel compartilhado e histórico

Chat e formulário do Explorador usam a mesma função de consulta e apresentação. A resposta sincroniza cargo, UF, município, local, seção, modo e períodos, além do link compartilhável e CSV. Consultas sobre um indicador destacam a respectiva linha. A interface confere os períodos, a cobertura, os números e, quando informada, a versão dos dados da resposta antes de substituir o painel. Uma falha preserva o último resultado válido. Uma alteração manual dos filtros cancela a pergunta pendente, impedindo que uma resposta antiga substitua a seleção mais recente.

O painel lateral guarda até 50 perguntas no `localStorage` deste navegador. No celular, aparece recolhido acima do campo de pergunta. Selecionar uma pergunta concluída reabre seus filtros e recalcula o painel com os dados atuais, sem nova chamada ao modelo. O histórico permanece após recarregar a página, pode ser limpo e não é sincronizado entre dispositivos. Se o armazenamento estiver indisponível, funciona somente na sessão. Os rascunhos de relatos e comprovantes privados não são incluídos neste histórico.

## Páginas de análise

`assets/atlas-analyses.js` procura uma análise publicada para município, cargo e ano. Os estudos existentes de Macapá e Campos dos Goytacazes são reconhecidos. A integração também lê o futuro `/analises/catalogo.json`, com `schema: 1`, uma lista `analises` e os campos `uf`, `municipio`, `ano`, `nome`, `cargos`, `data`, `versao` e `arquivos.html.url`. A ausência desse catálogo não impede as consultas. A correspondência usa os nomes e códigos de municípios do Atlas.

Pedidos explícitos como “Abra a análise de Macapá para presidente em 2026” abrem uma nova aba a partir da ação do usuário. O chat sempre oferece também o link “Abrir análise em nova aba”, caso o navegador bloqueie a abertura. As URLs aceitas ficam no próprio Atlas em `/municipios/` ou `/analises/`, ou no domínio oficial do R2 em `/analises/`. Não são gerados relatórios HTML novos por esta interface. Sem análise publicada para o recorte, o Atlas mantém a orientação e a consulta aos dados disponíveis.

## Validação desta interface — 7 de novembro de 2026

Testes de DOM com respostas controladas e dados reais do repositório verificaram troca de cargo, comparação, pergunta de seguimento, seção sem cobertura histórica, turno sem disputa, falha de conexão, concorrência entre chat e filtros, histórico após recarga, CSV e links. A prévia foi aberta no navegador em desktop e em uma área de 390 × 730 pixels, com envio por teclado, reabertura de pergunta e análise em nova aba. O campo permaneceu visível na primeira tela móvel, sem foco automático. A prévia usou respostas controladas; a publicação deve confirmar os endpoints reais pelo comando `--validar-worker` do pacote de entrega e fazer uma consulta após o GitHub Pages terminar.

Esta atualização é somente da interface e não exige implantar novamente o Worker.
