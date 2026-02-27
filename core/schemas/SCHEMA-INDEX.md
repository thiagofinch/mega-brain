# Schema Index

> **Versão:** 1.0.0
> **Última Atualização:** 2025-12-17

## Schemas Disponíveis

| Schema | Arquivo de Estado | Propósito |
|--------|-------------------|-----------|
| `chunks-state.schema.json` | `/artifacts/chunks/CHUNKS-STATE.json` | Chunks extraídos das fontes |
| `canonical-map.schema.json` | `/artifacts/canonical/CANONICAL-MAP.json` | Mapa de entidades canônicas |
| `insights-state.schema.json` | `/artifacts/insights/INSIGHTS-STATE.json` | Insights extraídos |
| `narratives-state.schema.json` | `/artifacts/narratives/NARRATIVES-STATE.json` | Narrativas sintetizadas |
| `file-registry.schema.json` | `/system/REGISTRY/file-registry.json` | Registry de arquivos processados |
| `decisions-registry.schema.json` | `/logs/SYSTEM/decisions-registry.json` | Decisões e precedentes |

## Sistema de IDs Unificado

### Padrões de ID

| Tipo | Formato | Exemplo |
|------|---------|---------|
| Source ID | `PREFIX` + `NNN` | `JL001`, `CG003`, `HR001` |
| Chunk ID | `SOURCE_ID` + `-` + `NNN` | `JL001-001`, `CG003-015` |
| Decision ID | `YYYYMMDDHHMMSS-ORIGIN-DEST` | `20251215130249-CRO-CFO` |
| Precedent ID | `PREC-YYYY-NNN` | `PREC-2025-001` |

### Prefixos de Fonte Registrados

| Prefixo | Pessoa/Canal | Empresa |
|---------|--------------|---------|
| `JL` | Jordan Lee | AI Business |
| `CJ` | Charlie Johnson Show | - |
| `MT` | Max Tornow | Max Tornow Podcast |
| `HR` | Alex Hormozi | - |
| `CG` | Cole Gordon | - |
| `SS` | Sam Oven | Setterlun University |

## Foreign Keys (Rastreabilidade)

```
file-registry.json
    ├─ source_id ──────────────────┐
    └─ chunk_count                 │
                                   ▼
CHUNKS-STATE.json ◄────────────────┘
    ├─ source_id
    └─ chunks[]
        └─ chunk_id ───────────────┐
                                   │
INSIGHTS-STATE.json ◄──────────────┤
    └─ chunk_id                    │
        └─ insight_id ─────────────┤
                                   │
NARRATIVES-STATE.json ◄────────────┤
    └─ evidence_chain[] (chunk_ids)│
                                   │
decisions-registry.json ◄──────────┘
    └─ chunk_ids[]
    └─ sources[] (knowledge files)
```

## Validação

### Usando Python

```python
import json
import jsonschema

# Load schema
with open('system/SCHEMAS/chunks-state.schema.json') as f:
    schema = json.load(f)

# Load data
with open('artifacts/chunks/CHUNKS-STATE.json') as f:
    data = json.load(f)

# Validate
jsonschema.validate(data, schema)
```

### CLI (se jsonschema instalado)

```bash
python -m jsonschema -i CHUNKS-STATE.json chunks-state.schema.json
```

## Regras de Incremento

1. **Nunca deletar** - apenas adicionar ou marcar como deprecated
2. **Sempre validar** antes de salvar
3. **Incrementar version** em cada mudança
4. **Manter change_log** para auditoria
