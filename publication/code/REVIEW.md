# Review — publicação de documentos

2026-11-08 — PASS para integridade dos arquivos e implementação do fluxo de publicação.

Conferidos: sete relatórios, seis ZIPs, catálogo sem versões duplicadas, caminhos imutáveis com SHA-256, reimportação idempotente, recusa de corrupção e de alteração de versão. JavaScript com sintaxe válida. A automação valida os mesmos arquivos antes do commit do bot e falha sem modificar a main caso a conferência não passe.

Este parecer cobre a disponibilização técnica. Não constitui nova revisão estatística dos relatórios. A execução e o commit de publicação ficam registrados no Actions; a verificação dos links em produção é realizada após o Pages concluir.
