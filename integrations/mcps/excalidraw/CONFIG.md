# Excalidraw MCP

> **Status:** ✅ ATIVO
> **Fonte:** Mega Brain (nativo)

## Comandos Disponiveis

| Comando | Descricao |
|---------|-----------|
| `create_element` | Criar novo elemento |
| `update_element` | Atualizar elemento existente |
| `delete_element` | Deletar elemento |
| `query_elements` | Buscar elementos |
| `get_resource` | Obter recurso (scene, library, theme) |
| `group_elements` | Agrupar elementos |
| `ungroup_elements` | Desagrupar |
| `align_elements` | Alinhar elementos |
| `distribute_elements` | Distribuir elementos |
| `lock_elements` | Travar elementos |
| `unlock_elements` | Destravar elementos |
| `create_from_mermaid` | Criar diagrama de Mermaid |
| `batch_create_elements` | Criar multiplos elementos |

## Tipos de Elementos

- `rectangle`
- `ellipse`
- `diamond`
- `arrow`
- `text`
- `label`
- `freedraw`
- `line`

## Exemplos

```python
# Criar retangulo
mcp__excalidraw__create_element(
    type="rectangle",
    x=100, y=100,
    width=200, height=100,
    backgroundColor="#e3f2fd"
)

# Criar de Mermaid
mcp__excalidraw__create_from_mermaid(
    mermaidDiagram="graph TD; A[Start]-->B[Process]; B-->C[End]"
)

# Criar multiplos elementos
mcp__excalidraw__batch_create_elements(elements=[
    {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 50},
    {"type": "text", "x": 10, "y": 20, "text": "Hello"}
])
```
