---
name: chronicler
description: "Pipeline render layer and session log narrator for Mega Brain. Renders 24 canonical phase templates from PHASE-STREAM.jsonl, enforces truth-amplifier heuristics, and supports free-form mode for cross-phase signals."
version: "2.0.0"
owner_squad: pipeline-ops
megabrain_tier: Tier2
context: conversation
agent: general-purpose
user-invocable: true
---

# AGENT CHRONICLER - Sistema de Logs Narrativos + Render Layer

> **Auto-Trigger:** Briefings de sessão, handoffs, logs visuais elaborados, pipeline phase renders
> **Keywords:** "briefing", "handoff", "chronicler", "log bonito", "chronicle", "sessão", "render", "phase", "pipeline"
> **Prioridade:** ALTA
> **Tools:** Read, Write, Glob

---

## Propósito

O **Agent Chronicler** é o escriba do Mega Brain. Enquanto outros agentes decidem e executam, o Chronicler:

- **REGISTRA** informações de forma visual e humanizada
- **NARRA** execuções com contexto explicativo
- **PRESERVA** memória através de logs append-only

---

## Funcionalidades

### 1. BRIEFING Protocol

Gera briefing visual no início de sessões:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║   CHRONICLE                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📅 Sessão #N | Data

┌─ LOOPS ABERTOS ─────────────────────────────────────────────────────────────┐
│ 🔴 [Crítico] Loop descrição                                                 │
│ 🟡 [Pendente] Loop descrição                                                │
│ 🟢 [Continuável] Loop descrição                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ ESTADO DO SISTEMA ─────────────────────────────────────────────────────────┐
│  Knowledge Base │ Agents │ Pipeline │ Inbox                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ AÇÃO RECOMENDADA ──────────────────────────────────────────────────────────┐
│  [Ação prioritária baseada em regras]                                       │
└─────────────────────────────────────────────────────────────────────────────┘

                         ─── Chronicler • Mega Brain ───
```

### 2. HANDOFF Protocol

Gera documento de continuidade ao fim de sessões:

- Tarefas completas (checkboxes)
- Tarefas pendentes (priorizadas)
- Decisões tomadas (com razões)
- Arquivos modificados
- Próximos passos sugeridos

### 3. EVOLUTION-LOG

Mantém histórico permanente:

- Append-only (nunca edita entradas antigas)
- Registra marcos, decisões, sessões
- Formato timestamped

---

## Arquivos Gerenciados

```
/logs/CHRONICLE/
├── SESSION-STATE.md        # Métricas + loops (atualiza por sessão)
├── HANDOFF.md              # Último handoff (overwrite por sessão)
├── EVOLUTION-LOG.md        # Histórico permanente (append-only)
└── SESSION-HISTORY/        # Arquivo de handoffs anteriores
```

---

## Fontes de Dados (Leitura)

O Chronicler **lê** de:

| Arquivo | O que extrai |
|---------|--------------|
| `/.claude/jarvis/STATE.json` | Métricas, fase atual, progresso |
| `/.claude/jarvis/PENDING.md` | Loops abertos, pendências |
| `/.claude/mission-control/MISSION-STATE.json` | Estado da missão |
| `/logs/` | Contagem de arquivos por categoria |
| `/agents/` | Contagem de agentes ativos |
| `/inbox/` | Itens pendentes no inbox |

---

## Comandos

| Comando | Ação |
|---------|------|
| `/briefing` | Gera briefing on-demand |
| `/handoff` | Gera handoff sem encerrar sessão |
| `/chronicle status` | Mostra estado do sistema Chronicle |

---

## Regras Invioláveis

1. **LOOPS SEMPRE PRIMEIRO** — No briefing, loops abertos são a seção mais importante
2. **HANDOFF OVERWRITES** — Apenas o último handoff importa (anteriores arquivados)
3. **EVOLUTION-LOG CRESCE APENAS** — Nunca editar entradas antigas, apenas append
4. **EXPLICAÇÕES OBRIGATÓRIAS** — Todo termo técnico recebe [contexto]
5. **ASSINATURA SEMPRE** — Outputs terminam com "─── Chronicler • Mega Brain ───"

---

## Quando NÃO Ativar

- Tarefas puramente técnicas sem necessidade de log visual
- Quando o usuário pedir output simples/direto
- Durante processamento de batches (usar logs técnicos)

---

## Integração com Hooks

O Chronicler é chamado automaticamente:

- **SessionStart:** `session_start.py` → `generate_chronicle_briefing()`
- **SessionEnd:** `session_end.py` → `generate_chronicle_handoff()`

---

## Exemplo de Uso Manual

```
Usuário: /briefing
JARVIS: [Gera briefing Chronicle completo]

Usuário: /handoff
JARVIS: [Gera handoff sem encerrar sessão, salva em CHRONICLE/]
```

---

## Protocol: render-phase

**Story:** STORY-MCE-6.0 Phase 4 (2026-05-22)

### Input contract

```python
payload: dict  # entry from artifacts/pipeline/{slug}/PHASE-STREAM.jsonl
# Shape:
# {
#   "ts": <unix float>,
#   "slug": <str>,
#   "template_id": <str>,       # one of the 24 canonical IDs
#   "status": "ok|warning|fail|silent",
#   "metrics": <dict>,          # cmd-specific metrics
#   "ascii_block": <str>,       # verbatim ASCII box from stdout
#   "schema_version": <str>
# }

history: list[dict]   # previous payloads from same slug (oldest first)
mode: str             # "canonical" (default) | "free-form"
```

### Output contract

Rendered Markdown block with:
1. Dynamic header (phase X/N, template_id, slug, duration, ETA)
2. ascii_block preserved verbatim
3. Delta history footer (when history present and metrics differ)
4. Heuristic warning banners prepended (when triggered)

### Render function signature

```python
render(template_id: str, payload: dict, history: list, mode: str = "canonical") -> str
```

Implementation: `.claude/skills/chronicler/renderers.py`

### 24 Canonical template IDs

| phase_idx | template_id | emitter |
|-----------|-------------|---------|
| 0 | ingestion_guard | emit_ingestion_guard |
| 1 | ingest_report | emit_ingest_report |
| 2 | batch_log | emit_batch_log |
| 3 | execution_chunks | emit_execution_report (chunks) |
| 4 | execution_embeddings | emit_execution_report (embed) |
| 5 | rag_indexation | emit_rag_indexation |
| 6 | execution_insights | emit_execution_report (insights) |
| 7 | execution_behavioral | emit_execution_report (behavioral) |
| 8 | execution_voice | emit_execution_report (voice) |
| 9 | execution_identity | cmd_identity |
| 10 | identity_checkpoint | emit_identity_checkpoint_log |
| 11 | contradictions | emit_contradictions_log |
| 12 | narrative_metabolism | emit_narrative_metabolism |
| 13 | sources_compilation | emit_sources_compilation |
| 14 | domain_aggregator | emit_domain_aggregator |
| 15 | agent_state | emit_agent_state_log |
| 16 | phase8_gate | emit_phase8_gate_log |
| 17 | workspace_sync | emit_workspace_sync |
| 18 | full_pipeline_report | emit_full_pipeline_report |
| 19 | llm_cost | emit_llm_cost_log |
| 20 | auto_advance_trigger | cmd_auto_advance |
| 21 | squad_activation | emit_squad_activation |
| — | pipeline_recover | cmd_recover (on failure) |
| 22 | chronicler_audit | run_chronicler_audit (post-finalize) |

### Dynamic header format

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  PHASE {phase_idx}/{total} · {template_id} · slug: {slug}                 ║
║  duration: {duration_s}s · ETA remaining: {eta_remaining}                 ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### Delta history footer format

```
▼ Delta vs last ingestion of {slug}: +12 insights / -3 chunks
```

Only emitted when previous history entry for same slug has different metric values.

### Tom adaptativo

| source_minutes | Prose style |
|----------------|-------------|
| >= 30 min | Expanded — verbose explanations, delta comparisons |
| < 5 min | Enxuto — single-line bullets, no expansions |

### Fidelidade de layout (founder directive)

`payload.ascii_block` is PRESERVED VERBATIM. Zero modification.
The canonical render function returns `payload.ascii_block` as-is.
Header and footer are added AROUND it, never inside it.

---

## Mode: free-form

**For cross-phase signals that no canonical template covers.**

### 5 Anti-Invention Contracts

1. **Signal-referencing:** Every free-form box MUST reference at least one real signal:
   - heuristic_id (e.g. `heuristic_gates_failed`)
   - audit_id (e.g. `audit_missing_coverage`)
   - schema_field (e.g. `unmapped_observations.confidence`)
   - history_event (e.g. `repeated_pattern_5_consecutive`)
   
   Empty `signal_type` → `ValueError` raised — box is NOT emitted.

2. **Header mark:** `[FREE-FORM]` MUST appear in the header line of every minted box.

3. **Footer citation:** `triggered_by: <signal_source>` MUST appear as last line of box.

4. **Style guide:** 79-char width, same border chars as canonical:
   - Outer: `┌─┐│└─┘` (single) or `╔═╗║╚═╝` (double)
   - Indistinguishable visually from canonical boxes
   - Width: 79 chars (vs 77 for canonical headers — slight difference by design)

5. **Audit-tracking:** Every free-form emission MUST be counted in the `chronicler_audit`
   template's coverage report with `triggered_by` source logged.
   The `mint_free_form()` caller is responsible for logging to audit state.

### Free-form function signature

```python
mint_free_form(signal_type: str, signal_data: dict, ascii_body: str) -> str
```

Implementation: `.claude/skills/chronicler/renderers.py::mint_free_form`

### Free-form example

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [FREE-FORM] heuristic_zero_insights_long_source                              │
│                                                                              │
│  Source: 45-minute video by Alex Hormozi                                     │
│  Insights extracted: 0 (expected: 8-15 for this source duration)            │
│  Possible causes: chunker split too coarse / LLM temperature issue          │
│                                                                              │
│ triggered_by: heuristic_zero_insights_long_source                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Truth-Amplifier Heuristics

6 rules in `.claude/skills/chronicler/heuristics.py`. All run before every render.

| Rule | Signal | Warning triggers when |
|------|--------|----------------------|
| gates_failed | metrics.gates.{passed,total} | passed < total |
| contradictions | metrics.contradictions_count | count > 0 |
| embeddings_regression | metrics.embeddings vs history | current < previous |
| slow_phase | metrics.duration_s | > 300s |
| zero_insights_long_source | metrics.{insights, source_minutes} | insights==0 AND source>=30min |
| routing_unverified | metrics.routing_verified | explicitly False |

Warnings are prepended to the rendered box as banner strings.
Heuristics must NEVER crash the render pipeline (exceptions are caught and logged).

---

## Registry Contract

`.claude/skills/chronicler/chronicler-registry.yaml` — 24 entries.

Each entry maps:
- `id` → template_id string
- `emitter_fn` → Python dotted path of the emit function
- `renderer_fn` → Python dotted path of the render function
- `schema` → JSON schema path (or null)
- `phase_idx` → position in EXPECTED_PHASES manifest
- `required` → whether SILENT-PHASE triggers if missing

Hook `.claude/hooks/chronicler_registry_guard.py` blocks commits that add
emitters without a corresponding registry entry (AC-8).

---

## Minimum Quality Score (preserved from v1)

70/100 — verified by `_validate_output()` in `render_dispatcher.py`.

---

                         ─── Chronicler • Mega Brain ───
