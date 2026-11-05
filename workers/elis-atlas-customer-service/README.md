# ELIS Atlas Customer Service

O Worker é a API do agente **Pergunte ao Atlas**. O visitante digita na página inicial. A interface envia a mensagem e os filtros ativos. O Worker limita o uso, pede à OpenAI uma interpretação estruturada e confere o recorte no catálogo do Atlas. Se faltar um dado, devolve uma pergunta. Para recortes válidos, o mesmo módulo do Explorador carrega, agrega e compara os resultados. O Worker devolve a tabela, os avisos de cobertura, as fontes com SHA-256 e o link para o recorte.

O piloto responde em português e cobre Presidente. O Explorador oferece consultas simples de 2026 e três comparações com 2026. O Worker segue essa cobertura para que seus links reproduzam a consulta. A implantação deste item cria somente os endpoints de saúde e chat. A recepção privada de relatos e a publicação de Issues têm fluxo próprio.

## Configurar no PowerShell

1. Abra o PowerShell na raiz do checkout que contém este código. Use Node.js 22.13 ou posterior e entre na pasta do Worker.

   ```powershell
   cd workers/elis-atlas-customer-service
   npx --yes wrangler@4.158.0 login
   npx --yes wrangler@4.158.0 whoami
   ```

   Confirme que a conta tem acesso à zona `electoralintegrity.org`. A configuração do Wrangler associa `atlas-api.electoralintegrity.org` como domínio personalizado. Use um nome DNS disponível na zona.

2. Crie uma chave em um projeto da [plataforma OpenAI](https://platform.openai.com/api-keys) com faturamento e acesso a `gpt-4.1-mini`. Para testar localmente, grave `OPENAI_API_KEY=...` no arquivo ignorado `.dev.vars` nesta pasta. Abra um terminal e rode:

   ```powershell
   npx --yes wrangler@4.158.0 dev
   ```

   Em outro terminal, rode:

   ```powershell
   $api = 'http://localhost:8787'
   Invoke-RestMethod "$api/api/health"
   $body = @{message = 'Qual foi a abstenção em Macapá no segundo turno de 2026?'} | ConvertTo-Json -Compress
   $headers = @{Origin = 'https://atlas-brazil-2026.electoralintegrity.org'}
   Invoke-RestMethod "$api/api/chat" -Method Post -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) | ConvertTo-Json -Depth 10
   ```

   Confira `status: ready` na saúde, `type: result` no chat e compare a taxa e a contagem com o link `explorerUrl`.

3. Prepare o deploy e guarde a chave como secret de produção. O primeiro deploy permite testar o domínio e o endpoint de saúde. Até a configuração da chave, o chat devolve HTTP 503.

   ```powershell
   npx --yes wrangler@4.158.0 deploy --dry-run
   npx --yes wrangler@4.158.0 deploy
   npx --yes wrangler@4.158.0 secret put OPENAI_API_KEY
   ```

   Cole a chave quando o Wrangler pedir. Mantenha o **Bot Fight Mode** na configuração de segurança adotada para a zona. Se algum teste de rede falhar, confira os eventos de segurança no painel antes de alterar regras.

4. Troque `$api` por `https://atlas-api.electoralintegrity.org` e repita os testes. Confira também a comparação “Compare o segundo turno de 2026 com o de 2022 em Campos dos Goytacazes”. Valide a consulta por seção no ambiente publicado e a experiência na página antes de habilitar o chat para visitantes.

## Contrato para a landing page

| Campo | Uso |
| --- | --- |
| `message` | Pergunta atual, até 1.200 caracteres. |
| `filters` | Objeto opcional com os campos do Explorador `uf`, `municipio`, `local`, `secao`, `mode`, `turno`, `comparacao` e `ano`. Envie os valores como strings. |
| `history` | Lista opcional com até quatro perguntas anteriores do visitante, da mais antiga à mais recente. Envie o histórico necessário para interpretar respostas curtas a esclarecimentos. |
| `type` e `message` | Exiba `message` como texto. Os tipos são `result`, `no_data`, `clarification`, `unsupported`, `report` e `error`. |
| `filters`, `periods`, `table`, `notes`, `explorerUrl`, `sources` | Campos de `result` e `no_data`. Ao continuar a conversa, reutilize os filtros do resultado anterior quando forem pertinentes. |

Envie JSON por `POST /api/chat`. Renderize cada célula e aviso como texto. As colunas seguem a ordem de `periods`. Em comparações, as diferenças de taxas são em pontos percentuais para candidatos e em variação relativa percentual para indicadores, como no Explorador. Taxa, contagem e diferença indisponíveis aparecem como `null`. As fontes são as URLs dos arquivos lidos com o SHA-256 do conteúdo, e o caminho R2 inclui o identificador da publicação.

O histórico fica a cargo da interface. O Worker envia a pergunta, o histórico fornecido e os filtros à OpenAI para interpretação. Oriente o visitante a usar o chat para dados públicos e a omitir dados pessoais. CORS controla as origens do navegador. O limite de 10 perguntas por minuto por IP vale em cada localidade do Cloudflare.
