# EQ-PRB-001 — Inferência probabilística sintética e identificabilidade

**Versão:** 0.2 · **Data:** 2026-11-08 · **Estado:** experimento executado, com falhas relevantes de identificabilidade e de calibração preditiva.

## 1. Resumo executivo

A v0.1 conseguia recuperar uma regra quando conhecia todas as contagens anteriores à transformação. A v0.2 remove esse acesso do **avaliador** e testa contagens inteiras sintéticas observadas juntamente com uma referência comportamental sintética amostrada independentemente. Os valores latentes são retidos somente no simulador para verificar as identidades contábeis.

**Resultado principal:** no cenário de referência sem transformação, o procedimento emitiu **23/1.000 alarmes (2,3%)**, com limite superior unilateral exato de 95% **3,24%**. Nas alternativas com transformação apenas em um turno, a detecção foi **58,0%–65,3%**, abaixo da meta de **80%**. Em cenários de dois turnos, variou entre **78,3% e 82,2%**. Quando uma mudança *natural* de comportamento reproduziu a mesma forma do sinal, houve **829/1.000 alarmes (82,9%)**, mesmo sem qualquer transformação das contagens.

**Interpretação:** bom controle do alarme sob a hipótese nula estreitamente especificada **não se transfere automaticamente** para hipóteses nulas comportamentais mais flexíveis. A regularidade estatística encontrada não identifica, por si só, a causa do padrão.

## 2. Desenho executado e observabilidade

- **Unidade sintética:** 5 municípios × 8 locais × 8 seções = **320 seções**, com dois turnos e quatro categorias (W, L, B, N).
- **Divisão externa:** **30 locais / 240 seções** no treinamento, **10 locais / 80 seções** exclusivamente no teste; todos os dois turnos de um mesmo local ficam na mesma partição.
- **Estados ocultos:** \(X_{s,t}\), contagens inteiras anteriores à transformação, **não são entradas de seleção de modelo**. O simulador as armazena apenas para auditoria.
- **Referência externa simulada:** amostra independente artificial de **1.800 observações por seção e turno** (tamanho especialmente informativo, não um levantamento disponível ou alegado real).
- **Hipótese mecânica sintética:** somente B → W, com \(m_{s,t}=\min(B_{s,t},\lfloor\alpha_{s,t}B_{s,t}+0,5\rfloor)\). Preserva integralmente \(W+L+B+N=C\).
- **Taxa simulada:** \(\alpha_{s,t}=\operatorname{clip}(a g(z_{s,t})+u_{\ell}+v_{s,t},0,0,85)\) nos turnos habilitados, com \(a=0,27\). D0 sem efeitos aleatórios; D1 variação por seção; D2 por local; D3 combinação.
- **Alternativas temporais:** H00 (nenhum turno), H01 (segundo), H10 (primeiro), H11 (ambos).
- **Biblioteca pré-fixada:** **73 candidatos**, contando H00 e as combinações 3 hipóteses temporais × 2 formas de taxa × 3 amplitudes × 4 classes de heterogeneidade.
- **Referência comportamental nula:** variações naturais por seção e por local com desvios-padrão de **0,004** e **0,006** na proporção de B; as funções de tendência de nível e de z em cada turno são ajustadas apenas com dados de treinamento.
- **Pontuação:** pseudologverossimilhança preditiva **gaussiana multivariada** para o contraste proporção de B na referência menos a proporção observada. Matriz de covariância por local com componentes compartilhados; **não** é uma verossimilhança exata dos quatro inteiros.

### Regras de avaliação

Foram executadas **1500 replicações nulas independentes para calibração** do processo de busca integral e **1000 replicações de avaliação por gerador**: H00, doze combinações H01/H10/H11 × D0–D3, mais a alternativa comportamental de estresse. **Total: 15.500 conjuntos sintéticos**. As amostras de calibração e avaliação são disjuntas. A regra seleciona pelo escore de treinamento e calcula no teste reservado o ganho em relação ao modelo H00. O limiar é o quantil 97,5% da distribuição nula de calibração, restringido a valores não negativos: **1.140 unidades do escore**.

## 3. Resultados completos de seleção

| Gerador | Classe D | Alarmes | Taxa de detecção | Seleção correta de H no treino | Seleção correta de D no treino |
|---|---|---:|---:|---:|---:|
| H00 | D0 | 23/1.000 | 2.3% | 40.0% | — |
| H01 | D0 | 644/1.000 | 64.4% | 91.8% | 99.8% |
| H01 | D1 | 582/1.000 | 58.2% | 88.6% | 2.0% |
| H01 | D2 | 580/1.000 | 58.0% | 92.4% | 63.1% |
| H01 | D3 | 586/1.000 | 58.6% | 93.7% | 1.0% |
| H10 | D0 | 646/1.000 | 64.6% | 89.2% | 99.6% |
| H10 | D1 | 593/1.000 | 59.3% | 87.8% | 1.5% |
| H10 | D2 | 653/1.000 | 65.3% | 92.8% | 60.7% |
| H10 | D3 | 598/1.000 | 59.8% | 92.8% | 0.8% |
| H11 | D0 | 822/1.000 | 82.2% | 95.7% | 100.0% |
| H11 | D1 | 800/1.000 | 80.0% | 92.6% | 0.2% |
| H11 | D2 | 802/1.000 | 80.2% | 96.9% | 58.5% |
| H11 | D3 | 783/1.000 | 78.3% | 94.6% | 0.1% |
| H00-natural-shift | D0 | 829/1.000 | 82.9% | — | — |

A taxa da tabela é o evento **escore do candidato selecionado menos escore H00 no teste maior que o limiar calibrado**. Uma taxa de seleção correta de H não é automaticamente uma detecção; a seleção ocorre antes de consultar o limiar do teste.

**Controle de falso alarme dentro do modelo nulo especificado:** 23/1.000, 2,3%, limite superior unilateral exato de 95% **3.2%**. A exigência de limite superior ≤ 5% foi satisfeita **somente para essa hipótese nula sintética restrita**.

**Poder estatístico:** o objetivo de pelo menos 80% **não foi atingido em todos os cenários**. Os casos de apenas um turno ficaram abaixo de 80%, e H11-D3 ficou em 78,3%.

**Identificação dos efeitos aleatórios:** a classe D3 verdadeira foi escolhida corretamente em apenas **0,1%** dos casos de H11-D3; D1 também foi quase sempre confundida. A família de candidatos não identifica de modo confiável a estrutura de variabilidade.

## 4. Calibração de intervalos — cenário H11-D3

Na mesma bateria de 1.000 replicações, foram testadas **160.000 previsões seção–turno** nos 10 locais reservados de cada realização. As coberturas efetivamente observadas foram:

| Intervalo nominal | W | L | B (brancos) | N (nulos) |
|---|---:|---:|---:|---:|
| 50% | 46.8% | 49.9% | 44.9% | 50.0% |
| 80% | 76.6% | 80.0% | 73.8% | 80.1% |
| 95% | 93.1% | 94.9% | 90.6% | 95.1% |

A cobertura conjunta da região retangular de Bonferroni projetada para 95% foi **92.8%**, abaixo do nominal. Há **subcobertura** em B e W; os intervalos não são considerados calibrados para todas as categorias. Usou-se aproximação normal, com parâmetros de tendência ajustados no treinamento e sem correção completa de sua incerteza. Os intervalos são marginalmente aproximados, não derivados de uma distribuição conjunta exata dos quatro inteiros.

## 5. Teste de identificabilidade — mudança natural sem transformação

No gerador **H00-natural-shift**, não existe transferência alguma; a probabilidade latente de voto branco sofre uma mudança natural com a mesma forma de degrau da família candidata e W aumenta compensatoriamente. Os quatro inteiros continuam contabilizados de maneira íntegra. Com o limiar **calibrado exclusivamente no H00 mais restrito**, o algoritmo emitiu **829/1.000 alarmes (82,9%)**.

Esse percentual **não** é uma taxa universal de falso positivo do método: é uma falha deliberada sob *deslocamento de distribuição* da hipótese comportamental nula. O teste evidencia que **o conjunto de possíveis comportamentos naturais precisa ser ampliado** e que, sem referências independentes restritivas, uma alteração comportamental pode imitar a regularidade de uma hipótese de transformação.

A construção determinística de v0.1 continua válida: dados observados iguais podem surgir de estados latentes distintos, com e sem transformação. A v0.2 **não resolve** essa não identificabilidade estrutural.

## 6. Conclusões metodológicas e critérios não satisfeitos

1. **Executado:** simulador inteiro, contagens latentes ocultas ao avaliador, quatro classes D, 73 candidatos, dois turnos, validação por local, calibração da seleção completa, 1.000 avaliações por gerador e intervalos preditivos aproximados.
2. **Aprovado somente sob a hipótese nula restrita:** controle de alarme com limite superior de 95% ≤ 5%.
3. **Não aprovado:** poder de 80% para todas as alternativas e calibração de intervalos 50/80/95% para todas as quatro categorias.
4. **Não identificado:** mecanismo probabilístico D0–D3 de modo consistente, nem a separação entre mudança comportamental flexível e conversão hipotética.
5. **Ainda não executado:** distribuição exata conjunta das quatro contagens, parâmetros de transferência por pesquisas reais, transição comportamental individual entre turnos, mecanismos N/L/O, busca simbólica aberta, critérios municipais da metodologia v1.2 e teste externo em dados reais.

## 7. Recomendação para v0.3

Priorizar um **teste de robustez comportamental** antes de ampliar a biblioteca de equações: (a) incluir a família H00 de tendências naturais não lineares e efeitos territoriais; (b) simular referências de precisão progressivamente menor e avaliar sensibilidade; (c) melhorar a distribuição preditiva inteira e intervalos de B/W; (d) só depois tentar distinguir formas de conversão por sua assinatura de arredondamento ou dependência espacial. Se uma alternativa natural admissível reproduz a mesma distribuição dos observados, classificar o mecanismo como **não identificável**, em vez de selecionar um vencedor por maior escore.

**Próxima condição de passagem:** no conjunto ampliado de hipóteses comportamentais, demonstrar limite superior de falso alarme ≤ 5%, poder ≥ 80% nas alternativas pré-especificadas e cobertura confiável dos intervalos preditivos; os três critérios devem valer fora da amostra e sem reescolher o limiar.

## 8. Arquivos, execução e proveniência

- `eq_prb_001_v02.py`: gerador, biblioteca e inferência sintética, replicações e intervalos.
- `verify_v02.py`: verificações de conservação, divisão por local, matriz de covariância e consistência.
- `results_v0.2.json`: todos os indicadores e ressalvas em formato estruturado.
- `calibration_results.csv`: resumo comparativo por cenário.
- `synthetic_holdout_example.csv`: realização sintética de auditoria, com estados latentes identificados como dados do simulador.
- `experiment_log.txt`: registro da execução.

Reprodução com **Python 3**, **NumPy 2.3.5**, **SciPy 1.17.0**:

`python eq_prb_001_v02.py > experiment_log.txt`

`python verify_v02.py`

A semente de NumPy é **20261108**, gerador PCG64. O tempo de execução pode variar; os resultados estatísticos, e não a duração, integram o arquivo determinístico. A execução sobrescreve os arquivos de resultados na mesma pasta. Este relatório é derivado dos resultados efetivamente calculados, sem números imputados.

**Escopo:** exercício matemático em dados inventados, sem inferências sobre o resultado de qualquer eleição real ou sistemas de votação.
