# EQ-PRB-001 v0.2 — Simulação probabilística e identificabilidade

**Status:** executado, **não validado** quanto a poder, calibração dos intervalos e robustez a mudanças naturais de comportamento.

**Todos os resultados são sintéticos.** Não se utilizaram votos reais, dados eleitorais de 2026 nem resultados de outros anos. O programa apenas examina propriedades matemáticas de modelos concorrentes.

## Resultado resumido

- 73 candidatos; H00/H01/H10/H11, duas formas funcionais, três amplitudes e D0/D1/D2/D3.
- 1.500 replicações independentes de calibração H00 + 1.000 avaliações para cada um dos 14 geradores, total de 15.500 conjuntos sintéticos.
- Null H00 estrito: **2,3%** de alarmes, limite unilateral superior de 95% de **3,24%**.
- Detecção nos modelos de um turno: **58,0%–65,3%**, abaixo da meta de 80%.
- Detecção nos modelos de dois turnos: **78,3%–82,2%**.
- Estresse sem transformação, apenas mudança natural de preferência com forma de degrau: **82,9% de alarmes** — forte evidência de não identificabilidade sob essa ampliação do comportamento admissível.
- Intervalos nominais de 95% para H11-D3: coberturas W **93,1%**, L **94,9%**, B **90,6%**, N **95,1%**.

Para justificativa, diagnóstico e limitações, ver [relatório técnico](RELATORIO_EQ-PRB-001_v0.2.md) ou [versão HTML](RELATORIO_EQ-PRB-001_v0.2.html).

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `eq_prb_001_v02.py` | Gerador, ajuste e busca da biblioteca completa, calibração, avaliação e intervalos |
| `verify_v02.py` | Testes de contabilidade inteira, holdout e álgebra do modelo |
| `build_report.py` | Gera relatórios Markdown e HTML diretamente de `results_v0.2.json` |
| `results_v0.2.json` | Resultados estruturados e hipóteses fixadas |
| `calibration_results.csv` | Avaliação resumida por gerador |
| `synthetic_holdout_example.csv` | Uma realização sintética para auditoria (inclui estados latentes do simulador) |
| `experiment_log.txt` | Log da execução |
| `RELATORIO_EQ-PRB-001_v0.2.md` | Relatório técnico |
| `RELATORIO_EQ-PRB-001_v0.2.html` | Relatório HTML estático |
| `MANIFEST.sha256` | Checksums SHA-256 dos dez arquivos de entrega |

## Reproduzir

Python 3.13, `numpy==2.3.5`, `scipy==1.17.0`, `mistune==3.2.1` (necessário apenas para renderização do HTML). Não requer rede após instalação.

```bash
python eq_prb_001_v02.py > experiment_log.txt
python verify_v02.py
python build_report.py
sha256sum -c MANIFEST.sha256
```

A execução demora de acordo com o equipamento e **sobrescreve** CSV/JSON/log; se quiser verificar os arquivos originais sem reexecutar, comece apenas por `sha256sum -c MANIFEST.sha256`.

Semente fixa `20261108` com NumPy PCG64. Os arquivos estatísticos não incluem a duração da execução, que é variável. A forma da distribuição de geração é pré-fixada: o sucesso da metodologia *não* se extrapola a famílias de comportamento não modeladas. O programa possui um gerador de estresse H00 comportamental que demonstra uma falha importante.

**Nota sobre o relatório:** as fórmulas nos textos são especificações; a inferência implementada é um **escore gaussiano aproximado**, e não a verossimilhança inteira/latente exata contemplada na metodologia ELIS-E2026-MET-BR-001 v1.2. O futuro v0.3 deverá trabalhar a não identificabilidade frente a comportamento natural mais flexível antes de avançar a hipóteses mais complexas.
