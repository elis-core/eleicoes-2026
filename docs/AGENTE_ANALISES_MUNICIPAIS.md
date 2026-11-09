# Processo de análises municipais do Atlas

Versão 1.1 · 7 de novembro de 2026

## Objetivo e papéis

Produzir análises reproduzíveis de municípios, conferir os resultados e publicar versões no Atlas com a identidade `elis-atlas-publisher[bot]`.

| Papel | Identificador proposto | Responsabilidade e saída |
| --- | --- | --- |
| Analista | `elis-atlas-analyst` | Selecionar o próximo recorte, consolidar fontes, calcular e redigir HTML, metadados e HANDOFF.md |
| Validador | `elis-atlas-validator` | Conferir cálculos, denominadores, cobertura, fontes e conclusões. Produzir REVIEW.md e o veredito vinculado aos hashes |
| Publicador | `elis-atlas-publisher` | Executar o publicador autenticado como GitHub App, verificar arquivos no R2 e abrir o PR do catálogo |

Esta é uma definição operacional independente de fornecedor. Pode ser usada como instrução de agentes no ELIS Core ou executada em sessões separadas de análise e revisão. O pacote inclui a fila, o catálogo e o publicador. A execução de modelos depende do executor onde os agentes forem instalados.

## Seleção e continuidade

1. Ler a versão atual da fila `analises/fila.json` no repositório, quando já publicada, e conciliá-la com `analises/catalogo.json`.
2. Escolher até cinco municípios ainda sem análise, respeitando prioridades explícitas do responsável. A fila inicial usa ordem alfabética e contém os 167 municípios do RN. Os seis relatórios existentes aguardam revisão para publicação.
3. Trabalhar em um município por vez. Registrar a chave `(ano, UF, código TSE do município)` e um identificador da execução. Não usar o código IBGE no lugar do código TSE.
4. Atualizar atividade e estado no HANDOFF.md. Uma execução interrompida continua a partir dos artefatos conferidos. Uma revisão nova substitui o veredito anterior, com data e hashes atuais.

Estados previstos são `na_fila`, `em_analise`, `aguardando_dados`, `em_revisao`, `revisado`, `publicacao_preparada` e `publicado`. O catálogo que entrou em `main` confirma a publicação no portal. O status proposto em um PR só se torna público após o merge.

## Instrução do analista

Para cada município, obter as contagens por cargo e turno, a votação nominal e o detalhe por seção. Usar os geradores e os módulos de leitura já existentes no repositório. Registrar a versão dos dados e os hashes das fontes usadas. Uma nova análise deve especificar os turnos efetivamente disponíveis.

Incluir presidente, governador e senador. Candidaturas usam votos válidos do cargo. Brancos, nulos e válidos usam o total de votos do cargo. Comparecimento e abstenção usam aptos. Em 2026, Senado tem duas escolhas por eleitor e turno único. Preservar separadamente nulos comuns, técnicos, anulados e anulados sub judice conforme a base.

O relatório deve conter resultados por cargo, todas as candidaturas, cobertura e denominadores, comparações entre os turnos disponíveis, gráficos por seção, fontes e limitações. Preservar valores ausentes. Para brancos e nulos, identificar explicitamente qualquer faixa de tolerância escolhida. A faixa de ±3% do exercício é uma comparação com a hipótese de taxa constante.

Fatores calculados usando o resultado observado devem ser apresentados como ajustes descritivos. Inferências sobre transições individuais ou conversões exigem hipóteses e identificação adicionais. Usar referências comportamentais com incerteza explícita quando a análise avançar para esse tipo de inferência.

Nomear os arquivos com município, data ISO, descrição e versão. Exemplo `Natal_2026-11-07_Analise_Eleitoral_v1.1.html`. Emitir um HTML autônomo e, quando disponível, o PDF correspondente. Validar a leitura em celular e a impressão. Evitar conteúdo ativo nos relatórios publicados.

## Instrução do validador

Recalcular as somas do município e das seções, conferir candidatos e percentuais e verificar os casos sem conciliação. Conferir os gráficos e a correspondência de zona e seção entre turnos. Verificar se o texto distingue descrição, cenários condicionais e inferência.

Produzir um REVIEW.md datado com PASS ou FAIL, escopo da conferência, fontes e erros pendentes. O revisor deve ser diferente do autor da análise. Após PASS, registrar no `bundle.json` o status `PASS` e o identificador do revisor. O campo `artefatos_sha256` vincula o veredito aos arquivos atuais. Qualquer alteração posterior exige uma nova revisão e, para uma versão já publicada, uma nova versão do relatório.

O publicador verifica integridade e identidade. A revisão científica do analista e do validador continua sendo uma etapa própria.

## Instrução do publicador

1. Executar os testes e `--validar`.
2. Exigir PASS para cada análise do lote e conferir o vínculo da revisão com os arquivos.
3. Autenticar como App ID `5627105`, slug `elis-atlas-publisher`, da organização `elis-core`. Resolver a instalação pela API e validar o bot ID `352893640`.
4. Enviar os arquivos para chaves imutáveis no R2 e comparar o SHA-256 dos bytes lidos no domínio público com os originais.
5. Preparar o catálogo e a fila sobre o HEAD atual de `main`. Abrir branch e PR como o bot, incluindo os registros da revisão.
6. Após o merge e a conclusão do Pages, conferir catálogo, links de HTML e PDF e o atalho do Explorador. Registrar os links e o commit no HANDOFF.md.

Se houver falha, manter o catálogo anterior ativo e registrar o ponto de retomada. Repetir uploads para as mesmas chaves de hash é idempotente. Uma versão publicada com outros hashes exige incremento de versão. O rollback consiste em restaurar o catálogo anterior pelo mesmo fluxo de revisão.

## Execução inicial

```powershell
node .\scripts\fila.cjs 5
node --test .\scripts\verificar-processo.cjs
node .\scripts\publicar-analises.cjs --validar
```

Para registrar uma próxima análise, criar um JSON de metadados com `uf`, `municipio`, `nome`, `ano`, `versao`, `data`, `cargos` e `periodos` (turnos disponíveis por cargo), e executar o comando abaixo.

```powershell
node .\scripts\registrar-analise.cjs .\metadados.json .\Municipio_2026-11-07_Analise_Eleitoral_v1.0.html
```

O PDF pode ser informado como terceiro argumento. O registro começa com revisão pendente.


## Instalação da estrutura — versão 1.1

Executar scripts/publicar-analises.cjs --instalar CAMINHO_DO_PEM para abrir o PR do catálogo, atalhos e fila. Esse modo preserva catálogo e fila existentes e pode instalar a navegação enquanto os relatórios aguardam revisão. Não envia arquivos ao R2 nem altera o veredito de nenhuma análise.

O modo --publicar continua exigindo revisão PASS do lote e confirmação dos arquivos públicos no R2. As conferências em verificacao/ são evidência técnica sobre o snapshot e não substituem a revisão independente. A instalação dos perfis e seu agendamento no ELIS Core permanecem etapas do executor.
