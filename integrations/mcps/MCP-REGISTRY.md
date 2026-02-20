# MCP Registry - [SUA EMPRESA] OS

> **Versao:** 1.0.0
> **Atualizado:** 2026-01-17

## MCPs Registrados

### ATIVOS

| MCP | Comandos | Fonte |
|-----|----------|-------|
| **gdrive** | `gdrive_search`, `gdrive_read_file`, `gsheets_read`, `gsheets_update_cell`, `gdocs_create` | Mega Brain |
| **excalidraw** | `create_element`, `update_element`, `delete_element`, `query_elements`, `create_from_mermaid` | Mega Brain |

### PENDENTES (A Configurar)

| MCP | Comandos Previstos | Fonte |
|-----|-------------------|-------|
| **playwright** | `navigate`, `screenshot`, `click`, `fill`, `extract` | AIOS |
| **desktop-commander** | `execute`, `read_file`, `write_file`, `list_dir` | AIOS |
| **exa** | `search`, `get_contents` | AIOS |

## Como Usar

### gdrive

```
# Buscar arquivos
mcp__gdrive__gdrive_search(query="nome do arquivo")

# Ler arquivo
mcp__gdrive__gdrive_read_file(fileId="...")

# Ler planilha
mcp__gdrive__gsheets_read(spreadsheetId="...")

# Atualizar celula
mcp__gdrive__gsheets_update_cell(fileId="...", range="A1", value="...")
```

### excalidraw

```
# Criar elemento
mcp__excalidraw__create_element(type="rectangle", x=0, y=0, width=100, height=50)

# Criar de Mermaid
mcp__excalidraw__create_from_mermaid(mermaidDiagram="graph TD; A-->B")
```

## Adicionar Novo MCP

1. Criar pasta em `/integrations/mcps/[nome]/`
2. Criar `CONFIG.md` com instrucoes
3. Atualizar este registry
4. Configurar em `settings.json` se necessario
