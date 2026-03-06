O que foi adicionado

- `mcp_servers.json`: arquivo de configuração com a entrada `context7` (placeholder de chave).
- `setup_context7.ps1`: script PowerShell para definir a variável de ambiente `CONTEXT7_API_KEY` e atualizar `mcp_servers.json` automaticamente.

Como usar

1) No PowerShell (executar na pasta do workspace):

```powershell
.\setup_context7.ps1 -ApiKey "ctx7sk-SEU_TOKEN_AQUI"
```

2) Reinicie o VS Code se já estiver aberto.

3) Verifique que a variável está setada:

```powershell
Get-ChildItem Env:CONTEXT7_API_KEY
```

4) Se sua ferramenta/projeto lê `mcp_servers.json`, ela automaticamente encontrará a configuração em `mcp_servers.json` no root do workspace.

Segurança

- Não commit seus tokens em repositórios públicos. Use `.gitignore` para excluir `mcp_servers.json` se for o caso.

Precisa que eu adicione `mcp_servers.json` ao `.gitignore` automaticamente?"