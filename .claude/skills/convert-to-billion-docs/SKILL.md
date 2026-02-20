# CONVERT TO BILLION DOCS

## Trigger
`/convert-to-billion-docs` ou `/billion-docs`

## Objetivo
Converter arquivos Markdown para Google Docs com formatacao visual Billion.

## Estilos Aplicados

### Tipografia
- **Fonte Principal**: Montserrat (fallback: Arial)
- **Titulo (H1)**: 18pt Bold, preto
- **Subtitulo (H2)**: 14pt Bold, #434343
- **Secao (H3+)**: 12pt Bold, #434343
- **Corpo**: 10pt Normal

### Cores Billion
| Elemento | Cor |
|----------|-----|
| Background | #F3F3F3 |
| Header Tabela | #D9D9D9 |
| Bordas | #D9D9D9 |
| Separador | #A0A0A0 |
| Heading | #434343 |

### Formatacao
- Blocos de codigo com fonte Consolas e background cinza
- Tabelas com header em #D9D9D9
- Listas com hifen
- Linhas horizontais em #A0A0A0

## Uso

### Via CLI
```bash
python convert.py <arquivo.md> [folder-id]
```

### Exemplos
```bash
# Converter para pasta padrao
python convert.py ./IOS-REPORT.md

# Converter para pasta especifica
python convert.py ./TEMPLATE.md [YOUR_FOLDER_ID_HERE]
```

## Pre-requisitos

1. Credenciais OAuth configuradas (mesmas do /sync-docs)
2. Escopos necessarios:
   - `https://www.googleapis.com/auth/documents`
   - `https://www.googleapis.com/auth/drive`

## Output

```
=== DOCUMENTO BILLION CRIADO ===
Titulo: [Nome do documento]
URL: https://docs.google.com/document/d/[ID]/edit
Timestamp: 2026-01-20T...
```

## Arquivos Relacionados

- [BILLION-VISUAL-STANDARDS.md](../../../[SUA EMPRESA]-CORE/templates/BILLION-VISUAL-STANDARDS.md)
- [config.json](../sync-docs/config.json)
