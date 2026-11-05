# Metodologia para investigar dúvidas sobre os resultados eleitorais

**Versão 1.0 · 5 de novembro de 2026**

O Atlas Eleitoral recebe perguntas sobre divergências entre pesquisas e resultados, mudanças entre turnos e possíveis erros na urna ou na totalização. O objetivo é transformar cada pergunta em um teste reproduzível, indicar o que a evidência permite concluir e publicar uma resposta que possa ser atualizada quando surgirem novos dados.

## 1. O que motivou a investigação

Na eleição presidencial de 2026, Flávio Bolsonaro ficou à frente no primeiro turno e Lula terminou à frente no segundo. As últimas estimativas de Datafolha e AtlasIntel/Bloomberg também diferiram do resultado divulgado.

| Comparação nacional | Flávio Bolsonaro | Lula |
|---|---:|---:|
| 1º turno, sobre todos os votos válidos | 47,03% | 45,16% |
| 1º turno, recalculado apenas entre os finalistas | 51,01% | 48,99% |
| Último Datafolha, campo de 23 a 24 de outubro | 50,89% | 49,11% |
| Último AtlasIntel/Bloomberg, divulgado em 24 de outubro | 50,80% | 49,20% |
| 2º turno, resultado divulgado pelo TSE | 48,21% | 51,79% |

Os números do primeiro turno vêm da publicação do TSE com 99,99% das urnas apuradas. A linha recalculada descreve a posição relativa dos finalistas no primeiro turno. O resultado de Lula ficou 2,68 pontos percentuais acima do Datafolha e 2,59 acima do AtlasIntel. O recorte ilustra duas divergências distintas e documenta apenas dois levantamentos. Avaliar se as variações foram atípicas exige uma referência histórica. [TSE, primeiro turno](https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/flavio-bolsonaro-e-lula-vao-disputar-o-2o-turno-para-a-presidencia-da-republica) · [TSE, segundo turno](https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/presidente-do-tse-anuncia-reeleicao-de-lula-e-faz-balanco-do-2o-turno-das-eleicoes-2026) · [Datafolha](https://www1.folha.uol.com.br/poder/2026/10/datafolha-flavio-bolsonaro-tem-51-dos-votos-validos-e-lula-49-em-empate-tecnico.shtml) · [AtlasIntel/Bloomberg e outros levantamentos](https://noticias.uol.com.br/eleicoes/2026/10/24/datafolha-quaest-palver-btgnexus-atlas-veja-ultimas-pesquisas-do-segundo-turno.amp.htm)

## 2. Recebimento, anonimato e acompanhamento

1. **Receber em privado.** A equipe recebe a pergunta e eventuais anexos. Se for necessário devolver o protocolo, usa o canal pelo qual a pessoa entrou em contato. A pessoa pode optar por apenas consultar o link.
2. **Preparar o resumo público.** Remover nomes, contatos, identificadores, dados pessoais, marcas de captura e metadados que revelem a fonte. Parafrasear trechos que possam identificá-la. Manter arquivos originais necessários à verificação em acesso restrito, separados do repositório público. Preservar o sigilo do voto.
3. **Abrir a issue pela equipe.** O número atribuído pelo GitHub à issue é o número do protocolo público. Por exemplo, a issue `#2` corresponde ao **Protocolo #2**. Registrar pergunta sanitizada, recorte, hipóteses, status e próximos passos. A conta que abre o ticket representa a equipe e pode aparecer publicamente. A pessoa que enviou a pergunta acompanha pelo link sem precisar comentar. Complementos podem chegar pelo canal privado.
4. **Separar protocolo e análise.** Um pedido recebe um protocolo. Quando tiver várias hipóteses, cada uma recebe um identificador dentro dele, como H1 ou H2, com critérios, evidência e conclusão próprios. Pedidos repetidos podem apontar para a análise já existente. A quantidade de encaminhamentos da mesma fonte não aumenta o peso da evidência.
5. **Revisar e responder.** A issue registra as etapas **recebido → em triagem → em análise → em revisão → respondido**. Quando faltarem dados essenciais, indicar **aguardando evidência**. Publicar uma atualização datada quando o status mudar. Antes de aprovar a resposta pública, outra pessoa confere os números, as fontes, as limitações e o anonimato. A issue aponta para a versão revisada. Novas evidências podem justificar reabertura e revisão datada.

Em um repositório público, a issue serve para acompanhamento e o documento versionado serve como resposta. A equipe verifica a anonimização antes de publicar em ambos. [GitHub, visibilidade dos repositórios](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories)

## 3. Ficha para cada hipótese

| Campo | Conteúdo |
|---|---|
| Identificação | Protocolo, identificador da hipótese, data, versão e situação |
| Pergunta | Uma afirmação verificável, formulada sem atribuir culpa ou pressupor o resultado |
| Recorte | Cargo, eleição, turno, UF, município, zona, seção e horário, conforme disponíveis |
| Comparação | Valor observado, valor de referência, denominador, cobertura e razão da comparação |
| Evidência | Origem, data, versão e, para arquivos técnicos, hash e forma de obtenção |
| Teste | Etapa da cadeia, resultado esperado sob cada hipótese, verificações alternativas e regra de decisão |
| Resultado | Diferenças em votos e, quando pertinente, em pontos percentuais, seções verificadas, incerteza e próximos passos |

## 4. Três linhas de verificação

| Linha | Teste inicial | Limite da conclusão |
|---|---|---|
| Pesquisas versus resultado | Inventariar as pesquisas elegíveis por turno e data de campo. Vincular registro no PesqEle e publicação original, separar simulações de confrontos reais e documentar cenário, população, método, indecisos, votos válidos e rodadas faltantes. Comparar o erro por instituto e testar janelas de campo e regras de inclusão. | A margem de erro declarada cobre apenas parte da incerteza. Cobertura, não resposta, comparecimento, mudanças tardias e vieses compartilhados podem produzir divergências. |
| Mudança entre turnos | Comparar votos absolutos, percentual dos válidos e votos por eleitor apto. Decompor as mudanças de comparecimento, brancos, nulos e candidatos eliminados. Fazer o pareamento de seções comparáveis e tratar agregações e remanejamentos à parte. | Os totais descrevem onde houve mudança líquida. Transições individuais entre escolhas exigem dados ou hipóteses adicionais. Comparações entre cargos são referências de contexto. |
| Urna, transmissão e totalização | Na mesma seção, cargo, turno e versão, confrontar BU recolhido no local, BU publicado e registros totalizados. Refazer a soma e verificar boletins pendentes, substituídos ou retificados. Quando pertinente, recontar o RDV e cruzar a ata com o log e os registros de autenticidade do software. | Um BU recolhido no local é referência externa à transmissão e à totalização. BU, RDV e log têm origem no sistema eletrônico. Uma falha anterior à geração desses registros pode ficar fora do alcance dos testes de consistência. |

Para uma hipótese de erro na captura ou no registro local, a evidência mais direta seria um teste controlado e reproduzível com entradas conhecidas e saídas divergentes, ou uma comparação com um registro independente da escolha, quando houver. Um erro demonstrado em teste requer evidência adicional para estimar se ocorreu na eleição, quantos votos afetou e se houve intervenção intencional.

Definir critérios e comparações antes da etapa confirmatória. Ao examinar milhares de seções, separar a descoberta de padrões do teste em outras seções, considerar dependência geográfica e ajustar o critério ao volume de comparações. Registrar resultados positivos, negativos e inconclusivos com a mesma granularidade. [PesqEle](https://www.tse.jus.br/eleicoes/pesquisas-eleitorais) · [AAPOR, precisão das pesquisas](https://aapor.org/polling-accuracy/) · [Dados de BU de 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna) · [Arquivos de urna de 2026](https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/resultados-do-2o-turno-das-eleicoes-2026-estao-disponiveis-em-pagina-do-tse) · [Procedimentos de auditoria do TSE](https://www.tse.jus.br/eleicoes/urna-eletronica/seguranca-da-urna/como-realizar-auditoria)

## 5. Formato da resposta para o Atlas

Cada resposta em Markdown tem protocolo, título em forma de pergunta, data, versão, status, recorte e as seções **Pergunta**, **Resposta**, **Como verificamos**, **Limites e próximos passos** e **Fontes**. A resposta curta informa primeiro o resultado e o escopo do teste. A análise técnica e as tabelas dão suporte à resposta. O Atlas poderá usar o documento revisado e oferecer o link da issue para acompanhamento.

A conclusão por hipótese será uma de quatro situações.

- **Explicada pelos dados.** A diferença foi reconciliada com os registros ou teve causa documentada.
- **Sem discrepância no teste realizado.** Informar a cobertura e as limitações do teste.
- **Inconclusiva por falta de evidência.** Identificar o dado que permitiria avançar.
- **Discrepância confirmada.** Indicar etapa, magnitude, abrangência conhecida e se o efeito sobre o resultado pôde ser determinado.

O piloto usa o RJ para organizar o pareamento e confrontar as visualizações do Atlas com os arquivos originais. Casos com seção identificada e documento original têm prioridade. O calendário oficial prevê 7 de janeiro de 2027 para pedidos fundamentados de verificação pós-pleito por entidades fiscalizadoras e 12 de janeiro para solicitações de arquivos e relatórios em auditorias que demandem preservação da cadeia de custódia. [Resolução TSE nº 23.673/2021](https://www.tse.jus.br/legislacao/compilada/res/2021/resolucao-no-23-673-14-de-dezembro-de-2021) · [Calendário eleitoral](https://www.tse.jus.br/eleicoes/calendario-eleitoral)

## Protocolos registrados

- [Protocolo #2 — Totalização, comportamento eleitoral e cenários simulados](protocolo-2.md)
