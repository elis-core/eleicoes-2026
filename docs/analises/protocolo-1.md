# O que pode explicar a mudança no resultado presidencial entre os turnos de 2026?

**Protocolo [#1](https://github.com/elis-core/eleicoes-2026/issues/1) · 5 de novembro de 2026 · Versão 0.1 · Em triagem**

**Origem:** consulta externa anonimizada

**Recorte:** eleição presidencial de 2026, com RJ, SP e MG como ponto de partida e referências de 2022 e 2026 para governador.

## Pergunta

O pedido propõe examinar cinco pontos relacionados.

1. Procurar incoerências na totalização.
2. Medir quão incomum foi a mudança sob hipóteses de comportamento eleitoral, usando a eleição para governador como referência em 2022 e 2026. Examinar as alianças em RJ, SP e MG.
3. Testar se a redução de brancos e nulos é compatível com uma hipótese de reclassificação em favor de Lula.
4. Estimar transições de votos entre Flávio Bolsonaro e Lula e testar a hipótese distinta de reatribuição técnica.
5. Variar parâmetros em cenários simulados de alteração de contagens para avaliar o que os testes conseguiriam detectar.

## Resposta preliminar

A mudança pode ser investigada. Primeiro, é possível conferir se o resultado totalizado corresponde aos boletins nas seções verificadas. Em paralelo, é possível medir quão rara foi a mudança sob um modelo de comportamento eleitoral com hipóteses declaradas. Os números agregados, por si só, admitem várias combinações de mudança de voto, comparecimento e escolhas dos eleitores dos candidatos eliminados. Este registro documenta a triagem e o plano de verificação. [Metodologia](metodologia.md) · [Inferência ecológica com identificação parcial](https://gking.harvard.edu/publication/ecological-regression-with-partial-identification/)

## Como verificamos

A triagem verificou em quais eleições estaduais há dois turnos comparáveis. Os testes sobre os arquivos das seções e o modelo estatístico ainda estão pendentes.

| UF | Governador em 2022 | Governador em 2026 | Uso na análise |
|---|---|---|---|
| RJ | Decidido no 1º turno | Decidido no 1º turno após retotalização | Contexto estadual e caso documentado de alteração do denominador dos válidos |
| SP | Houve 2º turno | Decidido no 1º turno | Comparação entre turnos para governador em 2022 e contexto estadual nos dois anos |
| MG | Decidido no 1º turno | Decidido no 1º turno | Contexto estadual nos dois anos |

No RJ, o TRE-RJ confirmou a vitória de Douglas Ruas no primeiro turno após excluir dos votos válidos os votos atribuídos a Anthony Garotinho por decisão judicial. Os votos nominais de Ruas permaneceram em 4.271.199. A diferença entre publicações do mesmo turno tem uma causa documentada e é um caso de controle para a conferência de versões. Para comparações de governador entre turnos em 2026, considerar UFs com votação efetiva nos dois turnos, como Amazonas e Espírito Santo. [TRE-RJ, 2022](https://www.tre-rj.jus.br/comunicacao/noticias/2022/Outubro/eleicoes-2022-tre-rj-homologa-resultado-do-primeiro-turno) · [TRE-RJ, retotalização de 2026](https://www.tre-rj.jus.br/comunicacao/noticias/2026/Outubro/retotalizacao-de-votos-aponta-douglas-ruas-como-vencedor-no-primeiro-turno-para-o-governo-do-rj) · [TSE, SP 2022](https://www.tse.jus.br/comunicacao/noticias/2022/Outubro/tarcisio-de-freitas-republicanos-vence-disputa-pelo-governo-de-sao-paulo) · [TSE, SP 2026](https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/em-sao-paulo-tarcisio-de-freitas-e-eleito-governador-no-1o-turno) · [TSE, MG 2022](https://www.tse.jus.br/comunicacao/noticias/2022/Outubro/minas-gerais-reelege-o-governador-romeu-zema-novo) · [TSE, MG 2026](https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/cleitinho-azevedo-republicanos-e-eleito-governador-de-minas-gerais) · [TSE, locais com segundo turno para governador em 2026](https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/2o-turno-tera-diferentes-combinacoes-de-votos-dependendo-do-local)

### H1 · A soma dos boletins corresponde à totalização?

Conciliar o BU original recolhido por fiscal, quando disponível, o BU publicado e os resultados oficiais por seção, cargo, turno e versão. Recalcular totais nominais, brancos, nulos e comparecimento onde os campos forem equivalentes. Separar diferenças de fonte, boletins pendentes ou substituídos e retotalizações documentadas. A unidade do teste é a seção ou o conjunto agregado identificado no boletim. Uma diferença de contagem que persista depois dessa conciliação é uma ocorrência técnica verificável. Registrar valores exatos, cobertura e primeiro ponto da cadeia em que as fontes divergem. [Dados de BU de 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna) · [Painel da evolução da totalização](https://evolucao-totalizacao.tse.jus.br/)

### H2 · Quão rara foi a mudança sob um modelo de comportamento eleitoral?

Definir antes da comparação confirmatória o indicador primário, por exemplo a variação da margem entre os finalistas usando o mesmo denominador nos dois turnos. Usar a variação de comparecimento, os votos dos candidatos eliminados, o perfil histórico e o contexto estadual. Para alianças, classificar vínculo partidário ou de coligação, apoio público datado, apoio dividido ou ausência de confirmação. Verificar cada classificação em fonte datada e por turno. Apoio político é uma variável contextual. O voto para governador não determina o voto presidencial.

Construir uma distribuição de referência em disputas comparáveis com dois turnos efetivos. Calibrar o modelo em eleições e áreas históricas e testar sua capacidade de previsão fora da amostra de ajuste, com agrupamento geográfico. Comparar o indicador observado com o intervalo preditivo e, se houver calibração suficiente, reportar a frequência de variações tão extremas quanto a observada **sob o modelo declarado**. Essa frequência mede raridade sob aquelas premissas. Uma estimativa de probabilidade de fraude exigiria evidência e hipóteses de outra natureza. Se a base histórica for pequena, publicar o intervalo e a sensibilidade às escolhas do modelo.

### H3 · A queda de brancos e nulos sustenta a hipótese de reclassificação?

Separar brancos, nulos decorrentes da votação e anulações administrativas ou judiciais. Construir uma referência para o segundo turno com comparecimento, candidatos disponíveis e variação histórica. Para uma reclassificação hipotética, a assinatura esperada no **mesmo turno** é uma perda de votos em branco ou nulos igual ao ganho nominal atribuído ao beneficiário, mantendo o total de votos registrados na comparação. Verificar se a assinatura aparece em fontes realmente comparáveis e permanece após conciliar o RDV, o BU e a totalização. Uma relação entre a queda e o ganho **entre turnos** também pode resultar de comportamento eleitoral. Se uma alteração hipotética ocorrer antes do RDV e do BU, a coincidência entre esses registros pode deixar o caso inconclusivo. [Arquivos de urna de 2026](https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/resultados-do-2o-turno-das-eleicoes-2026-estao-disponiveis-em-pagina-do-tse)

### H4 · O que se pode estimar sobre a transição de Flávio Bolsonaro para Lula?

Separar duas hipóteses. A primeira é uma mudança legítima de escolha entre turnos. Em seções pareadas, construir uma matriz com as categorias do primeiro e do segundo turno, incluindo candidatos eliminados, brancos, nulos e abstenção. Para um universo fixo de N eleitores comparáveis, com F₁ votos para Flávio no primeiro turno e L₂ para Lula no segundo, a célula Flávio → Lula está entre **máx(0, F₁ + L₂ − N)** e **mín(F₁, L₂)**. Se o universo mudou, tratar entradas, saídas e remanejamentos explicitamente ou excluir o par da estimativa principal. Esses limites podem ser amplos. Estimativas mais precisas dependem de hipóteses testadas ou de evidência adicional, como pesquisa em painel.

A segunda hipótese é uma reatribuição técnica dentro do mesmo turno. Nesse cenário, a retirada de uma quantidade de votos de Flávio e a adição da mesma quantidade a Lula manteriam o total de válidos e alterariam a margem entre ambos pelo dobro dessa quantidade. Para testar a ocorrência, procurar discrepâncias nas fontes correspondentes à etapa investigada. Um ajuste que reproduza a margem entre turnos, sozinho, é insuficiente. [Inferência ecológica com identificação parcial](https://gking.harvard.edu/publication/ecological-regression-with-partial-identification/)

### H5 · Que alterações os testes conseguiriam detectar?

Usar cópias sintéticas com resultado de referência conhecido. Variar, separadamente e em conjunto, a quantidade reclassificada de brancos, a quantidade de nulos e a transferência entre os finalistas. Aplicar mudanças em proporções fixadas antes do teste, em seções dispersas ou concentradas, e simular efeitos em etapas distintas da cadeia. Medir taxa de detecção por magnitude e cobertura e taxa de falsos alertas em cenários sem alteração, inclusive com mudanças legítimas de comparecimento. Guardar parâmetros, sementes quando usadas, entradas e resultados.

Com L, F, B e N como contagens iniciais, aplicar (L + b + n + f, F − f, B − b, N − n), em que b, n e f são quantidades inteiras entre zero e os respectivos totais de origem. O total registrado é preservado e a margem Lula − Flávio muda em b + n + 2f.

Exemplo ilustrativo de uma seção sintética. A simulação reclassifica 6 brancos e 4 nulos em favor de Lula e transfere 15 votos de Flávio para Lula.

| Cenário | Lula | Flávio | Brancos | Nulos | Total | Margem Lula − Flávio |
|---|---:|---:|---:|---:|---:|---:|
| Referência sintética | 400 | 450 | 30 | 20 | 900 | −50 |
| Após alteração simulada | 425 | 435 | 24 | 16 | 900 | −10 |

Se a alteração simulada atingir apenas a totalização, o confronto com o BU de referência a revela. Se todas as saídas disponíveis na simulação forem produzidas a partir dos mesmos totais alterados, o teste de consistência pode passar. A simulação mede sensibilidade e delimita quais evidências seriam necessárias para avançar.

## Limites e próximos passos

1. Identificar seções e documentos originais para iniciar H1. Até esta versão, o pedido não veio acompanhado de um BU específico ou de registros de uma seção.
2. Selecionar a referência histórica, confirmar e datar as alianças e publicar os critérios de pareamento e de comparação antes de avaliar H2.
3. Executar H3 e H4 sobre dados validados, com limites explícitos. Usar H5 para mostrar quais desvios os testes identificariam.
4. Atualizar a issue com o andamento. Após revisão, publicar nesta página uma resposta por hipótese para futura apresentação no Atlas Eleitoral.

## Fontes

- [Metodologia para investigar dúvidas sobre os resultados eleitorais](metodologia.md)
- [Protocolo público e histórico de andamento](https://github.com/elis-core/eleicoes-2026/issues/1)
- [Portal de Dados Abertos do TSE, resultados de 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026)
