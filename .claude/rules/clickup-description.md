---
paths:
  - "services/clickup/**"
  - "squads/clickup-*/**"
  - "squads/team-ops-squad/**"
  - "squads/backlog-ops/**"
---

# ClickUp Task Description Rules v3.0 — MegaBrain Hub

Applies when any agent updates task descriptions in ClickUp via API or when configuring SuperAgent instructions.

**Roundtable:** RT-JL-001 (2026-03-30) — 7/7 decisions unanimous
**Ref:** docs/architecture/roundtable-journey-log-superagent-2026-03-30.md

## Description Contract — 3 Zones (NON-NEGOTIABLE)

Every task description follows this invariant structure:

```
┌─────────────────────────────────────┐
│  ZONE 1: BODY                       │
│  Task header, metadata, instruções  │
│  Writer: Claude Code helpers ONLY   │
│  Rule: SuperAgent NEVER touches     │
├─────────────────────────────────────┤
│  ---                                │
├─────────────────────────────────────┤
│  ZONE 2: ## Journey Log             │
│  Entries cronológicas (bullet)      │
│  Writers: Claude Code + SuperAgent  │
│  Format: - **TS** — texto (agent)   │
│  Rule: ONLY append, NEVER rewrite   │
├─────────────────────────────────────┤
│  ZONE 3: ## Task Digest             │
│  Generated ONLY when status = done  │
│  Writer: SuperAgent ONLY            │
│  Template: by task_type             │
│  Rule: 1 generation, never updated  │
└─────────────────────────────────────┘
```

### Zone Boundaries

| Boundary | Marker | Description |
|----------|--------|-------------|
| Zone 1 → Zone 2 | `---` + `## Journey Log` | Fixed separator. Everything above = body. |
| Zone 2 → Zone 3 | `## Task Digest` | Appears ONLY when task reaches `done`. |

## API Limitation: No Partial Updates

The ClickUp API v2 does NOT support partial description updates. Every PUT replaces the entire description. Use the helpers in `services/clickup/tasks.js`.

## Markdown Rendering (NON-NEGOTIABLE)

| Field | Renders Markdown? | Use When |
|-------|-------------------|----------|
| `description` | **NO** — raw text | **NEVER** for updates |
| `markdown_description` | **YES** — renders in ClickUp | **ALWAYS** for updates |

When reading, use `includeMarkdownDescription: true`:
```javascript
const task = await getTask(taskId, { includeMarkdownDescription: true });
```

## Journey Log Format (Zone 2) — CANONICAL v3.1

**One format for ALL writers (Claude Code AND SuperAgent):**

```markdown
- {COR} {ÍCONE} **YYYY-MM-DD HH:MM** — [CATEGORIA] {descrição do evento} ({pessoa} via {agente})
```

### Anatomy

| Part | Required | Description |
|------|----------|-------------|
| `{COR}` | Yes | 🟢 normal, 🟡 attention, 🔴 critical |
| `{ÍCONE}` | Yes | Category icon (see table below) |
| `**YYYY-MM-DD HH:MM**` | Yes | Timestamp in bold |
| `[CATEGORIA]` | Optional | Category tag for filtering |
| `{descrição}` | Yes | Event description — concise, factual |
| `({pessoa} via {agente})` | Yes | WHO did it + THROUGH which agent/tool |

### Author Format: `({pessoa} via {agente})`

| Origin | Person | Agent | Output |
|--------|--------|-------|--------|
| ClickUp (human action) | The person who acted | SuperAgent name | `({pessoa} via {agente})` |
| ClickUp (system/auto) | "Sistema" | SuperAgent name | `(Sistema via {agente})` |
| Claude Code (user asks) | User name | Tool/agent used | `({pessoa} via {agente})` |
| Automated skill | Who invoked | Skill name | `({pessoa} via {skill})` |

### Severity Colors

| Color | Meaning | Keywords |
|-------|---------|----------|
| 🔴 | CRITICAL | erro, problema, urgente, reprovado, rejeitado, bloqueado, atrasado, crítico, falha |
| 🟡 | ATTENTION | ajustar, dúvida, aguardando, pendente, alterar, refazer, revisar |
| 🟢 | NORMAL | aprovado, concluído, postado, enviado, registrado, atualizado, progresso |

### Category Icons

| Category | Icon | When |
|----------|------|------|
| `[AJUSTE-CLIENTE]` | 👤 | Client feedback/request |
| `[AJUSTE-TIME]` | 👥 | Team member adjustment |
| `[STATUS]` | 🔄 | Status transitions |
| `[CUSTOM-FIELD]` | 📊 | Custom field changes |
| `[ANEXO]` | 📎 | File attachments |
| `[DATA]` | 📅 | Date changes |
| `[COMENTÁRIO]` | 💬 | Comments |
| `[VÍDEO-FEEDBACK]` | 🎬 | Video feedback |
| `[ERRO]` | ⚠️ | Errors |
| `[APROVAÇÃO]` | ✅ | Approvals |
| `[REJEIÇÃO]` | ❌ | Rejections |
| `[ENTREGA]` | 🚀 | Deliveries/deployments |
| `[BLOQUEIO]` | 🚫 | Blockers |
| `[GERAL]` | 📋 | General events (default) |

### Examples

```markdown
- 🟢 🔄 **2026-03-30 14:00** — [STATUS] Status → doing. Iniciando execução. ({pessoa} via {agente})
- 🔴 👤 **2026-03-30 14:30** — [AJUSTE-CLIENTE] Plataforma reprovou — áudio inaudível. ({cliente} via {agente})
- 🟡 👥 **2026-03-30 16:00** — [AJUSTE-TIME] Volume aumentado -12dB → -6dB. ({pessoa} via {agente})
- 🟢 ✅ **2026-03-30 17:00** — [APROVAÇÃO] Criativo aprovado. Liberado para postagem. ({pessoa} via {agente})
- 🔴 🚫 **2026-03-30 18:00** — [BLOQUEIO] GATE-LEGAL não passou. Aguardando Privacy Policy. ({pessoa} via {agente})
- 🟢 🚀 **2026-03-30 19:00** — [ENTREGA] Deploy v5.0.1 completo. 5/5 testes passando. ({pessoa} via {agente})
```

### Claude Code Helper Usage

```javascript
await appendJournalEntry(taskId, 'Status → doing. Iniciando execução.', 'Task Manager', {
  person: '{pessoa}',
  color: '🟢',
  icon: '🔄',
  category: '[STATUS]'
});

await appendJournalEntry(taskId, 'GATE-LEGAL não passou. Aguardando Privacy Policy.', 'Task Manager', {
  person: '{pessoa}',
  color: '🔴',
  icon: '🚫',
  category: '[BLOQUEIO]'
});
```

**NEVER use heading format** (`#### [timestamp] | [CATEGORY]`) — deprecated as of v3.0.

## Helpers — 3 Operations

| Operation | Helper | Zone |
|-----------|--------|------|
| **Update description body** | `updateTaskDescriptionSafe(taskId, newBody, { journalEntry, agent })` | Zone 1 (preserves Zone 2+3) |
| **Append journal entry** | `appendJournalEntry(taskId, entry, agent)` | Zone 2 only (body untouched) |
| **Read description** | `getTask(taskId, { includeMarkdownDescription: true })` | All zones |

### Rules for Helpers

1. **NEVER** use `client.put('/task/...', { description: ... })` directly
2. **NEVER** use `client.put('/task/...', { markdown_description: ... })` directly
3. `appendJournalEntry()` inserts BEFORE `## Task Digest` if it exists, AFTER last entry otherwise
4. `updateTaskDescriptionSafe()` replaces Zone 1, preserves Zone 2 + Zone 3
5. Both helpers create `## Journey Log` if it doesn't exist

## SuperAgent Contract (for ClickUp AI Agent instructions)

SuperAgents MUST follow these rules:

1. **NEVER modify Zone 1** (body) — read it, don't write it
2. **Write Zone 2 entries** in bullet format only: `- **TS** — texto (agent name)`
3. **Generate Zone 3 (Task Digest)** ONLY when status transitions to `done`
4. **Detect task_type** from custom field and use the matching digest template
5. **ALWAYS read the current description** before writing — preserve all existing content
6. **Append new entries at the end** of Zone 2, before Zone 3 (if exists)

## Task Digest Templates (Zone 3)

Generated by SuperAgent ONLY when `status → done`. Template selected by `task_type`:

### Creative
```markdown
## Task Digest
- **Task:** {name}
- **Linha do tempo:** {start} → {done}
- **Desempenho:** ER {value} | Views {value} | Plays {value}
- **Creator:** {creator} ({plataforma})
- **Ocorrências:** {erros/bloqueios}
- **Aprendizados:** {insights}
```

### Ops / Infra
```markdown
## Task Digest
- **Task:** {name}
- **Linha do tempo:** {start} → {done}
- **Resultado:** {serviços afetados, testes, deploys}
- **Decisões:** {decisions taken}
- **Tempo:** estimado {X} vs real {Y}
- **Aprendizados:** {insights}
```

### Mission
```markdown
## Task Digest
- **Task:** {name}
- **Linha do tempo:** {start} → {done}
- **Tasks concluídas:** {N} | Gates passed: {N}
- **Blockers resolvidos:** {list}
- **Decisões:** {decisions}
- **Aprendizados:** {insights}
```

### Generic (fallback)
```markdown
## Task Digest
- **Task:** {name}
- **Linha do tempo:** {start} → {done}
- **O que foi feito:** {summary}
- **Decisões:** {decisions}
- **Aprendizados:** {insights}
```

## SuperAgent Registry

All SuperAgents MUST be registered in `squads/clickup-ops-squad/data/superagent-registry.yaml`.
Creating a SuperAgent without registry entry violates governance (Mandamento 10).

## Applies To

ALL agents that interact with ClickUp task descriptions:
- Task Manager (`team-ops-squad`)
- ClickUp Ops (`clickup-ops-squad`)
- Sync Engineer (`@sync-engineer`)
- validate-mission-task skill
- materialize-mission.js
- enrich-mission-tasks.js
- Any SuperAgent configured in ClickUp AI

---

*ClickUp Description Rules v3.0 — MegaBrain Hub*
*Roundtable RT-JL-001: 2026-03-30 — 7/7 unanimous*
