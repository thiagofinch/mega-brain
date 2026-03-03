# nero-enricher

Ativa o @nero-enricher para CORTEX Cascade e agent enrichment.

## Uso

```
/AIOS:agents:nero-enricher
@nero-enricher
```

## Quando Usar

- Propagar DNA para agents operacionais
- Atualizar dossiers incrementalmente
- Rastrear roles mencionados no material
- Executar CORTEX Cascading (SOUL → AGENT → MEMORY)

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*enrich {persona}` | Inicia enrichment completo |
| `*role-track` | Rastreia menções de roles |
| `*dossier {persona}` | Atualiza dossier incrementalmente |
| `*cascade` | Executa CORTEX Cascading |
| `*propagate` | Propaga DNA para cargo agents |
| `*flags` | Lista agent creation flags |
| `*report` | Gera relatório de enrichment |
| `*exit` | Desativa agente |

## CORTEX Cascading Order

```
SOUL.md (core identity)
    ↓
AGENT.md (capabilities)
    ↓
MEMORY.md (knowledge base)
```

## Role Tracking Thresholds

| Menções | Flag | Ação |
|---------|------|------|
| ≥10 | 🔴 CRIAR AGENTE | Novo agent recomendado |
| 5-9 | 🟡 MONITORAR | Acompanhar crescimento |
| <5 | ⚪ REGISTRAR | Apenas log |

## Dossier Rules

```
❌ NUNCA substituir, SEMPRE adicionar
✓ Histórico incremental obrigatório
✓ Chunk ID reference inline: [chunk_AH047_12]
✓ Timestamp em cada incremento
```

## Exemplo

```
@nero-enricher *cascade --persona cole-gordon --propagate-to closer,bdr
```

## Agentes Relacionados

- `@nero-synthesis` - Upstream (unified_dna.yaml)
- `@nero-architect` - Parallel (SOUL.md updates)
- Cargo Agents (@closer, @bdr) - Downstream (DNA propagation)
