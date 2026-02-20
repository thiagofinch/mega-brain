# Google Drive MCP

> **Status:** ✅ ATIVO
> **Fonte:** Mega Brain (nativo)

## Comandos Disponiveis

| Comando | Descricao |
|---------|-----------|
| `gdrive_search` | Buscar arquivos no Drive |
| `gdrive_read_file` | Ler conteudo de arquivo |
| `gsheets_read` | Ler planilha completa ou ranges |
| `gsheets_update_cell` | Atualizar celula de planilha |
| `gdocs_create` | Criar documento Google Docs |

## IDs Importantes ([SUA EMPRESA])

```yaml
kpis_master: "[YOUR_SHEET_ID_HERE]"
dre_2025: "[YOUR_SHEET_ID_HERE]"
hiring_folder: "[YOUR_FOLDER_ID_HERE]"
```

## Exemplos

```python
# Buscar arquivo
result = mcp__gdrive__gdrive_search(query="nome do arquivo")

# Ler planilha inteira
data = mcp__gdrive__gsheets_read(spreadsheetId="ID_AQUI")

# Ler ranges especificos
data = mcp__gdrive__gsheets_read(
    spreadsheetId="ID_AQUI",
    ranges=["Sheet1!A1:B10", "Sheet2!C1:D5"]
)
```
