# EQ-PRB-001 — Validação sintética e identificabilidade (v0.1)

**Data:** 2026-11-08 · **Status:** experimento determinístico executado; etapa probabilística não executada.

Esta pasta preserva os **oito arquivos originais** do experimento EQ-PRB-001 v0.1 (código, dados simulados, métricas, registos e relatórios). Os dados são inteiramente **sintéticos**; não correspondem a apurações ou resultados eleitorais reais. Não se deve interpretar a recuperação de regras geradoras previamente incluídas na biblioteca candidata como evidência empírica de conversão de votos.

## Conteúdo

| Arquivo | Finalidade |
|---|---|
| `eq_prb_001.py` | Gerador determinístico e avaliação das funções candidatas |
| `synthetic_section_data.csv` | 320 seções simuladas com dois turnos e cenários H00/H01/H10/H11 |
| `candidate_scores.csv` | Erros de cada regra, cenário e turno |
| `fit_summary.csv` | Melhores ajustes por cenário/turno |
| `results.json` | Resultados estruturados e contraexemplo de identificabilidade |
| `execution_log.json` | Registo da execução |
| `RELATORIO_EQ-PRB-001_v0.1.md` | Relatório técnico Markdown |
| `RELATORIO_EQ-PRB-001_v0.1.html` | Relatório técnico HTML |

## Reproduzir

Requer Python 3 e NumPy; a execução original usou NumPy 2.3.5, gerador PCG64, `seed=20261108`.

```bash
python -m pip install numpy==2.3.5
python eq_prb_001.py > execution_log.json
sha256sum -c MANIFEST.sha256
```

**Atenção:** o programa reescreve `synthetic_section_data.csv`, `candidate_scores.csv`, `fit_summary.csv` e `results.json`. Para verificar integridade do pacote **antes de executar**, rode apenas `sha256sum -c MANIFEST.sha256`. A reexecução pode produzir diferenças de plataforma/versão mesmo com a mesma semente. Os valores SHA-256 em `MANIFEST.sha256` referem-se aos arquivos originais preservados.

A v0.1 demonstra recuperação em condições favoráveis, com contagens latentes conhecidas e regra verdadeira presente na biblioteca. Não implementa inferência hierárquica, previsão intervalar, controle de falsos alarmes nem a bateria de 1.000 replicações por cenário.

**Localização no repositório:** `research/experiments/EQ-PRB-001/v0.1/`. A publicação em branch/PR não altera, por si só, o catálogo ou a navegação pública do Atlas.
