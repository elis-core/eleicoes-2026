#!/usr/bin/env python3
"""Render a human-readable report from actual reproducible EQ-PRB-001 v0.2 outputs."""
import json
from pathlib import Path
import mistune

ROOT=Path(__file__).resolve().parent
j=json.loads((ROOT/'results_v0.2.json').read_text(encoding='utf-8'))
r=j['results']
fmt=lambda x:f'{100*x:.1f}%'
rows=[]
for a in r:
    h=a['generator'];d=a['d_class']
    rows.append(f"| {h} | {d} | {a['detections']}/1.000 | {fmt(a['detection_rate'])} | "
                + (fmt(a['correct_temporal_scenario_fraction']) if a['correct_temporal_scenario_fraction'] is not None else '—')
                + ' | '+(fmt(a['correct_D_fraction_positives']) if a['correct_D_fraction_positives'] is not None else '—')+' |')
interval=next(a['predictive_intervals_holdout'] for a in r if a['generator']=='H11' and a['d_class']=='D3')
intervalrows=[]
for target in ('50','80','95'):
    b=interval['marginal'][target]
    intervalrows.append(f"| {target}% | " + ' | '.join(fmt(b[c]['coverage']) for c in ('W','L','B','N')) + ' |')
text=f"""# EQ-PRB-001 — Inferência probabilística sintética e identificabilidade

**Versão:** 0.2 · **Data:** 2026-11-08 · **Estado:** experimento executado, com falhas relevantes de identificabilidade e de calibração preditiva.

## 1. Resumo executivo

A v0.1 conseguia recuperar uma regra quando conhecia todas as contagens anteriores à transformação. A v0.2 remove esse acesso do **avaliador** e testa contagens inteiras sintéticas observadas juntamente com uma referência comportamental sintética amostrada independentemente. Os valores latentes são retidos somente no simulador para verificar as identidades contábeis.

**Resultado principal:** no cenário de referência sem transformação, o procedimento emitiu **23/1.000 alarmes (2,3%)**, com limite superior unilateral exato de 95% **3,24%**. Nas alternativas com transformação apenas em um turno, a detecção foi **58,0%–65,3%**, abaixo da meta de **80%**. Em cenários de dois turnos, variou entre **78,3% e 82,2%**. Quando uma mudança *natural* de comportamento reproduziu a mesma forma do sinal, houve **829/1.000 alarmes (82,9%)**, mesmo sem qualquer transformação das contagens.

**Interpretação:** bom controle do alarme sob a hipótese nula estreitamente especificada **não se transfere automaticamente** para hipóteses nulas comportamentais mais flexíveis. A regularidade estatística encontrada não identifica, por si só, a causa do padrão.

## 2. Desenho executado e observabilidade

- **Unidade sintética:** 5 municípios × 8 locais × 8 seções = **320 seções**, com dois turnos e quatro categorias (W, L, B, N).
- **Divisão externa:** **30 locais / 240 seções** no treinamento, **10 locais / 80 seções** exclusivamente no teste; todos os dois turnos de um mesmo local ficam na mesma partição.
- **Estados ocultos:** \\(X_{{s,t}}\\), contagens inteiras anteriores à transformação, **não são entradas de seleção de modelo**. O simulador as armazena apenas para auditoria.
- **Referência externa simulada:** amostra independente artificial de **1.800 observações por seção e turno** (tamanho especialmente informativo, não um levantamento disponível ou alegado real).
- **Hipótese mecânica sintética:** somente B → W, com \\(m_{{s,t}}=\\min(B_{{s,t}},\\lfloor\\alpha_{{s,t}}B_{{s,t}}+0,5\\rfloor)\\). Preserva integralmente \\(W+L+B+N=C\\).
- **Taxa simulada:** \\(\\alpha_{{s,t}}=\\operatorname{{clip}}(a g(z_{{s,t}})+u_{{\\ell}}+v_{{s,t}},0,0,85)\\) nos turnos habilitados, com \\(a=0,27\\). D0 sem efeitos aleatórios; D1 variação por seção; D2 por local; D3 combinação.
- **Alternativas temporais:** H00 (nenhum turno), H01 (segundo), H10 (primeiro), H11 (ambos).
- **Biblioteca pré-fixada:** **{j['model_library_size']} candidatos**, contando H00 e as combinações 3 hipóteses temporais × 2 formas de taxa × 3 amplitudes × 4 classes de heterogeneidade.
- **Referência comportamental nula:** variações naturais por seção e por local com desvios-padrão de **0,004** e **0,006** na proporção de B; as funções de tendência de nível e de z em cada turno são ajustadas apenas com dados de treinamento.
- **Pontuação:** pseudologverossimilhança preditiva **gaussiana multivariada** para o contraste proporção de B na referência menos a proporção observada. Matriz de covariância por local com componentes compartilhados; **não** é uma verossimilhança exata dos quatro inteiros.

### Regras de avaliação

Foram executadas **{j['null_calibration_replicates']} replicações nulas independentes para calibração** do processo de busca integral e **{j['independent_evaluation_replicates_per_generator']} replicações de avaliação por gerador**: H00, doze combinações H01/H10/H11 × D0–D3, mais a alternativa comportamental de estresse. **Total: 15.500 conjuntos sintéticos**. As amostras de calibração e avaliação são disjuntas. A regra seleciona pelo escore de treinamento e calcula no teste reservado o ganho em relação ao modelo H00. O limiar é o quantil 97,5% da distribuição nula de calibração, restringido a valores não negativos: **{j['calibration_threshold_conservative_97_5_percentile']:.3f} unidades do escore**.

## 3. Resultados completos de seleção

| Gerador | Classe D | Alarmes | Taxa de detecção | Seleção correta de H no treino | Seleção correta de D no treino |
|---|---|---:|---:|---:|---:|
{chr(10).join(rows)}

A taxa da tabela é o evento **escore do candidato selecionado menos escore H00 no teste maior que o limiar calibrado**. Uma taxa de seleção correta de H não é automaticamente uma detecção; a seleção ocorre antes de consultar o limiar do teste.

**Controle de falso alarme dentro do modelo nulo especificado:** 23/1.000, 2,3%, limite superior unilateral exato de 95% **{fmt(r[0]['upper_one_sided_95_ci_detection_rate'])}**. A exigência de limite superior ≤ 5% foi satisfeita **somente para essa hipótese nula sintética restrita**.

**Poder estatístico:** o objetivo de pelo menos 80% **não foi atingido em todos os cenários**. Os casos de apenas um turno ficaram abaixo de 80%, e H11-D3 ficou em 78,3%.

**Identificação dos efeitos aleatórios:** a classe D3 verdadeira foi escolhida corretamente em apenas **0,1%** dos casos de H11-D3; D1 também foi quase sempre confundida. A família de candidatos não identifica de modo confiável a estrutura de variabilidade.

## 4. Calibração de intervalos — cenário H11-D3

Na mesma bateria de 1.000 replicações, foram testadas **160.000 previsões seção–turno** nos 10 locais reservados de cada realização. As coberturas efetivamente observadas foram:

| Intervalo nominal | W | L | B (brancos) | N (nulos) |
|---|---:|---:|---:|---:|
{chr(10).join(intervalrows)}

A cobertura conjunta da região retangular de Bonferroni projetada para 95% foi **{fmt(interval['simultaneous_four_95_bonferroni_coverage'])}**, abaixo do nominal. Há **subcobertura** em B e W; os intervalos não são considerados calibrados para todas as categorias. Usou-se aproximação normal, com parâmetros de tendência ajustados no treinamento e sem correção completa de sua incerteza. Os intervalos são marginalmente aproximados, não derivados de uma distribuição conjunta exata dos quatro inteiros.

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

- \\`eq_prb_001_v02.py\\`: gerador, biblioteca e inferência sintética, replicações e intervalos.
- \\`verify_v02.py\\`: verificações de conservação, divisão por local, matriz de covariância e consistência.
- \\`results_v0.2.json\\`: todos os indicadores e ressalvas em formato estruturado.
- \\`calibration_results.csv\\`: resumo comparativo por cenário.
- \\`synthetic_holdout_example.csv\\`: realização sintética de auditoria, com estados latentes identificados como dados do simulador.
- \\`experiment_log.txt\\`: registro da execução.

Reprodução com **Python 3**, **NumPy {j['numpy_version']}**, **SciPy {j['scipy_version']}**:

\\`python eq_prb_001_v02.py > experiment_log.txt\\`

\\`python verify_v02.py\\`

A semente de NumPy é **{j['seed']}**, gerador PCG64. O tempo de execução pode variar; os resultados estatísticos, e não a duração, integram o arquivo determinístico. A execução sobrescreve os arquivos de resultados na mesma pasta. Este relatório é derivado dos resultados efetivamente calculados, sem números imputados.

**Escopo:** exercício matemático em dados inventados, sem inferências sobre o resultado de qualquer eleição real ou sistemas de votação.
"""
text=text.replace('\\`','`')
(ROOT/'RELATORIO_EQ-PRB-001_v0.2.md').write_text(text,encoding='utf-8')
html=mistune.create_markdown(plugins=['table'])(text)
css='''body{max-width:1100px;margin:auto;padding:35px 22px;background:#f9fafb;color:#142337;font:16px/1.62 system-ui,-apple-system,Segoe UI,sans-serif}h1{font-size:2rem;color:#112548}h2{margin-top:2.5rem;color:#162b4e;border-bottom:1px solid #dce2eb;padding-bottom:.35rem}table{border-collapse:collapse;width:100%;font-size:.86rem;display:block;overflow-x:auto}td,th{border:1px solid #dae1e9;padding:.55rem .65rem;text-align:left}th{background:#eaf0f6;white-space:nowrap}tr:nth-child(even){background:white}code{background:#edf1f5;padding:.1rem .3rem;border-radius:4px}li{margin:.35rem 0}blockquote{border-left:3px solid #48668e;padding-left:1rem}strong{color:#172d4d}p{margin:.85rem 0}a{color:#174fa1} @media print{body{background:white;padding:0}}'''
(ROOT/'RELATORIO_EQ-PRB-001_v0.2.html').write_text(f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EQ-PRB-001 v0.2 — Relatório</title><style>{css}</style></head><body>{html}</body></html>',encoding='utf-8')
print('report files',len(text),len(html))
