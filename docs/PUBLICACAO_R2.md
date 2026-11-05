# Publicação dos dados do Atlas no Cloudflare R2

O piloto inclui os totais presidenciais do RJ, com 92 municípios, o agregado estadual e os dois turnos de 2010, 2014, 2018, 2022 e 2026.

## Publicar e ativar uma versão

1. Execute [Publish Atlas Data to R2](https://github.com/elis-core/eleicoes-2026/actions/workflows/publish-atlas-data-r2.yml) na branch `main`. O resumo da execução lista os cinco arquivos depois de validar a leitura pública, a igualdade com os originais e o CORS do Atlas.
2. Se o Bot Fight Mode tiver sido desativado para permitir a verificação automatizada, **reative-o ao encerrar a janela de publicação**, em **Cloudflare → Security → Settings → Bot traffic → Bot Fight Mode**. Faça isso também se a execução for interrompida. O Cloudflare oferece mitigação automática de DDoS em todos os planos. O Bot Fight Mode acrescenta proteção contra tráfego automatizado e pode desafiar clientes legítimos, inclusive o verificador do GitHub Actions. [DDoS Protection](https://developers.cloudflare.com/ddos-protection/) · [Bot Fight Mode](https://developers.cloudflare.com/bots/get-started/bot-fight-mode/)
3. Atualize o campo `release` de `dados/r2-rj-release.json` com o identificador exibido após `/releases/` no resumo da execução bem-sucedida.
4. Após a publicação do site, teste a tabela dos 92 municípios, a comparação histórica e o CSV em [português](https://atlas-brazil-2026.electoralintegrity.org/?uf=RJ&mode=comparar&visao=municipios&comparacao=turnos) e [inglês](https://atlas-brazil-2026.electoralintegrity.org/en/?uf=RJ&mode=comparar&visao=municipios&comparacao=turnos). Na aba **Network** do navegador, um `200` em `atlas-data.electoralintegrity.org` confirma o acesso pelo R2. Se a leitura falhar, o Atlas usa a cópia do GitHub Pages para o ano consultado.

Para voltar a uma versão validada anterior, restaure seu identificador no manifesto. Para usar somente os arquivos do GitHub Pages, defina `"release": null`.
