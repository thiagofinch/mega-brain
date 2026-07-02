# Schema Index

> **Versão:** 1.3.0
> **Última Atualização:** 2026-05-22
> **Changelog:** 1.3.0 — Phase 1 MCE-6.0: `insights-state` and `narratives-state` gain `unmapped_observations[]` escape hatch (additive, optional, backwards-compatible).

## Schemas Disponíveis

| Schema | Arquivo de Estado | Propósito | Versão | Tipo |
|--------|-------------------|-----------|--------|------|
| `chunks-state.schema.json` | `/artifacts/chunks/CHUNKS-STATE.json` | Chunks extraídos das fontes | 1.0.0 | deterministic |
| `canonical-map.schema.json` | `/artifacts/canonical/CANONICAL-MAP.json` | Mapa de entidades canônicas | 1.0.0 | deterministic |
| `insights-state.schema.json` | `/artifacts/insights/INSIGHTS-STATE.json` | Insights extraídos | **1.3.0** | cognitive-output |
| `narratives-state.schema.json` | `/artifacts/narratives/NARRATIVES-STATE.json` | Narrativas sintetizadas | **1.3.0** | cognitive-output |
| `file-registry.schema.json` | `/system/REGISTRY/file-registry.json` | Registry de arquivos processados | 1.0.0 | deterministic |
| `decisions-registry.schema.json` | `/logs/SYSTEM/decisions-registry.json` | Decisões e precedentes | 1.0.0 | deterministic |

## Schema Classification (Phase 1 Audit — MCE-6.0)

**Cognitive-output schemas** (written by LLM-producing cmds, receive `unmapped_observations[]` escape hatch):
- `insights-state.schema.json` — written by `cmd_insights` via Gemini Flash batched LLM extraction
- `narratives-state.schema.json` — written by `cmd_narrative` via `narrative_merger` synthesis

**Deterministic-output schemas** (written by algorithm/Python, no escape hatch needed):
- `chunks-state.schema.json` — written by `cmd_batch`/`cmd_process_batch` (text splitting)
- `canonical-map.schema.json` — written by `cmd_entities` (entity dedup + alias resolution)
- `file-registry.schema.json` — written by `cmd_ingest` (filesystem metadata)
- `decisions-registry.schema.json` — written by agent governance system

## unmapped_observations Field Spec (v1.3.0)

```json
{
  "unmapped_observations": [
    {
      "type": "string",
      "content": "string",
      "confidence": 0.0,
      "chunk_id": "SOURCE_ID-NNN"
    }
  ]
}
```

Rules:
- `maxItems: 3` — cap enforced at schema level
- `chunk_id` is REQUIRED — no observation without provenance anchor
- `default: []` — optional field, backwards-compatible with all existing artifacts
- Use ONLY after exhausting all 10 DNA layers (classification_pressure in prompts)

## Sistema de IDs Unificado

### Padrões de ID

| Tipo | Formato | Exemplo |
|------|---------|---------|
| Source ID | `PREFIX` + `NNN` | `JL001`, `SRC004`, `SRC005` |
| Chunk ID | `SOURCE_ID` + `-` + `NNN` | `JL001-001`, `SRC004-015` |
| Decision ID | `YYYYMMDDHHMMSS-ORIGIN-DEST` | `20251215130249-CRO-CFO` |
| Precedent ID | `PREC-YYYY-NNN` | `PREC-2025-001` |

### Prefixos de Fonte Registrados

| Prefixo | Pessoa/Canal | Empresa |
|---------|--------------|---------|
| `JL` | Jordan Lee | AI Business |
| `CJ` | um colaborador Show | - |
| `MT` | um colaborador | um colaborador Podcast |
| `HR` | Alex Hormozi | - |
| `CG` | Cole Gordon | - |
| `SS` | Sam Oven | uma universidade |

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
