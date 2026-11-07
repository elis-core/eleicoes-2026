# Presidente, Governador e Senador

O Explorador e o chat usam o filtro `cargo`. Presidente conserva a cobertura nacional e histórica. O piloto de Governador e Senador cobre 2026 nos 16 municípios do AP, 167 do RN e 92 do RJ, com locais e seções.

O catálogo `dados/cargos-2026.json` lista os arquivos, seus hashes SHA-256, os turnos disponíveis e a versão do conjunto. Os novos arquivos ficam em `dados/2026/cargos-v1`. Os pacotes municipais preservam as seis contagens do formato presidencial e acrescentam os totais de votos do cargo e as categorias detalhadas em um objeto próprio. Os dados são carregados conforme o recorte solicitado.

## Taxas

Candidatos usam os votos válidos do cargo. Comparecimento e abstenção usam aptos. Brancos, nulos e válidos usam o total de votos do cargo. Em 2026, Senador tem duas escolhas por eleitor e disputa em turno único. Nulos comuns e técnicos são componentes do total de nulos. Anulados e anulados sub judice são categorias próprias.

## Cobertura

A falta de uma disputa no turno e a ausência de cobertura são informadas separadamente. O piloto mostra Governador no primeiro turno em AP e RJ e em ambos os turnos no RN. Senado tem apenas o primeiro turno. O histórico dos novos cargos está em preparação. A resposta parcial conserva os valores presentes e os valores ausentes como `null`.

## Geração e verificação

`scripts/gerar_cargos_2026.py FONTES dados --ufs AP RN RJ` lê os CSVs oficiais por UF de detalhe municipal/zona, nominal municipal/zona, detalhe de seção e votação por seção. Requer os quatro arquivos de cada UF e o catálogo presidencial atual.

O gerador exige conciliação entre o detalhe municipal e os nominais válidos. A destinação dos votos por seção usa a classificação municipal/zona. O restante só é atribuído a outra categoria quando os totais da zona o identificam univocamente. Uma seção sem conciliação conserva os valores observados que podem ser publicados e recebe valores indisponíveis na distribuição afetada.

`node scripts/test_cargos_2026.mjs` verifica hashes, somas de seções e municípios, candidatos, taxas do Senado e cobertura. A geração de 7 de novembro de 2026 conciliou 103.523 registros de seção por cargo e turno, sem pendências no piloto.

## Worker

O módulo `workers/elis-atlas-customer-service/atlas-cargos-chat.mjs` usa a mesma lógica de leitura e cálculo de `assets/atlas-cargos.mjs`. O instalador aplica alterações pontuais ao Worker existente e copia os módulos necessários. A interpretação mantém o provedor configurado no servidor. O campo `cargo` integra o esquema e os filtros da consulta.

O envio privado de relatos segue pela entrada existente `atlas-com-questoes.mjs`. A rota de chat devolve as fontes e a versão dos dados. A publicação da interface verifica duas consultas reais na API, a versão, o CORS e a rota de relatos.

## Publicação

A implantação do pacote acontece em três etapas. Primeiro, o GitHub App publica os dados e os módulos de apoio. Depois da conclusão do Pages, o responsável atualiza e valida o Worker com Wrangler. Por fim, o App publica a interface. O publicador guarda os SHAs das etapas em um arquivo local e verifica a versão de `main` antes de cada envio.

A sessão de desenvolvimento verificou a interface em ambiente DOM, os cálculos e as rotas com interpretação simulada, além do dry-run do Worker. O navegador de QA estava indisponível. A publicação requer conferir visualmente desktop e celular e validar as consultas reais de produção.
