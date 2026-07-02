# GOVERNANCE MAP - REGRA → HOOK → ENFORCEMENT

> **Versão:** 1.0.0
> **Criado:** 2026-02-18
> **Referência:** Constitution Article VI, GOV-006
> **Propósito:** Mapear cada REGRA para o(s) hook(s) que a enforce

---

## RULE-GROUP-1: PHASE-MANAGEMENT (Regras 0-10)

| Regra | Nome | Hook(s) de Enforcement | Enforcement Type |
|-------|------|----------------------|------------------|
| REGRA 0 | Identidade JARVIS | `session_start.py` | SessionStart: Carrega JARVIS identity |
| REGRA 1 | Fases Sequenciais e Bloqueantes | `post_batch_cascading.py`, `checkpoint_writer.py` | PostToolUse: Valida fase antes de avançar |
| REGRA 2 | De-Para Obrigatório | `post_batch_cascading.py` | PostToolUse: Verifica mappings |
| REGRA 2.1 | Source Naming | `post_batch_cascading.py` | PostToolUse: Canonical entity check |
| REGRA 3 | Duplicate Prevention | `post_batch_cascading.py` | PostToolUse: Hash check |
| REGRA 4 | Position Mapping | `mission_feed.py` (runtime) | Batch: SOURCE_TO_SLUG mapping |
| REGRA 5 | Logging Obrigatório | `post_tool_use.py`, `ledger_updater.py` | PostToolUse: Auto-log |
| REGRA 6 | Batch Log Format | `post_batch_cascading.py` | PostToolUse: Format validation |
| REGRA 7 | Error Recovery | `checkpoint_writer.py` | PostToolUse: Checkpoint + recovery |
| REGRA 8 | Inbox Organization | `inbox_age_alert.py` | SessionStart: Alert stale files |
| REGRA 9 | Source Attribution | `post_batch_cascading.py` | PostToolUse: Source ID validation |
| REGRA 10 | Pipeline State | `post_tool_use.py` | PostToolUse: STATE.json update |

---

## RULE-GROUP-2: PERSISTENCE (Regras 11-14)

| Regra | Nome | Hook(s) de Enforcement | Enforcement Type |
|-------|------|----------------------|------------------|
| REGRA 11 | Persistência de Sessão | `session_autosave_v2.py`, `session_end.py` | SessionStart/Stop: Auto-save |
| REGRA 12 | Resume Capability | `session_start.py` | SessionStart: Detect unfinished session |
| REGRA 13 | Plan Mode | `enforce_plan_mode.py` | PreToolUse: Enforce plan approval |
| REGRA 14 | Verification Before Advance | `post_output_validator.py` | PostToolUse: Output check |

---

## RULE-GROUP-3: OPERATIONS (Regras 15-17)

| Regra | Nome | Hook(s) de Enforcement | Enforcement Type |
|-------|------|----------------------|------------------|
| REGRA 15 | Paralelismo de Terminais | — (informational) | Nenhum enforcement automático |
| REGRA 16 | [SUA EMPRESA] Context | `session_start.py` | SessionStart: Load business context |
| REGRA 17 | Template/Log Formatting | `auto_formatter.py` | PostToolUse: Format compliance |

---

## RULE-GROUP-4: PHASE-5-SPECIFIC (Regras 18-22)

| Regra | Nome | Hook(s) de Enforcement | Enforcement Type |
|-------|------|----------------------|------------------|
| REGRA 18 | Templates Fase 5 Obrigatórios | `post_output_validator.py` | PostToolUse: Template check |
| REGRA 19 | Cascateamento Knowledge | `post_batch_cascading.py` | PostToolUse: Cascade trigger |
| REGRA 20 | Source-Sync Verification | `session-source-sync.py` | SessionStart: Sync check |
| REGRA 21 | Dossier Freshness | `post_batch_cascading.py` | PostToolUse: Date comparison |
| REGRA 22 | DNA Schema Compliance | `post_output_validator.py` | PostToolUse: 5-layer check |

---

## RULE-GROUP-5: VALIDATION (Regras 23-26)

| Regra | Nome | Hook(s) de Enforcement | Enforcement Type |
|-------|------|----------------------|------------------|
| REGRA 23 | Validação Automática Fase 5 | `post_output_validator.py` | PostToolUse: Script trigger |
| REGRA 24 | Source-Sync Integrity | `session-source-sync.py` | SessionStart: Integrity check |
| REGRA 25 | Template Enforcement | `creation_validator.py` | PreToolUse: Template compliance |
| REGRA 26 | Cascading Integrity | `post_batch_cascading.py` | PostToolUse: Full chain check |

---

## RULE-GROUP-6: AUTO-ROUTING (Regras 27-30)

| Regra | Nome | Hook(s) de Enforcement | Enforcement Type |
|-------|------|----------------------|------------------|
| REGRA 27 | Skill & Sub-Agent Auto-Routing | `skill_router.py`, `skill_indexer.py` | UserPromptSubmit: Keyword match |
| REGRA 28 | Ativação Visível Obrigatória | `multi_agent_hook.py` | PostToolUse: Visual feedback |
| REGRA 29 | Quality Watchdog | `quality_watchdog.py` | PostToolUse: Non-conformity detect |
| REGRA 30 | GitHub Workflow | — (manual) | Nenhum enforcement automático |

---

## HOOKS SEM REGRA DIRETA (System Infrastructure)

| Hook | Evento | Propósito | Regra Relacionada |
|------|--------|-----------|-------------------|
| `agent_doctor.py` | PostToolUse | Health check dos agentes | AGENT-AUTHORITY |
| `agent_memory_persister.py` | SessionEnd | Persiste agent memory | Constitution Art. IV |
| `claude_md_guard.py` | PreToolUse | Bloqueia CLAUDE.md fora de paths | CLAUDE.md Policy |
| `enforce_dual_location.py` | PreToolUse | IDE sync enforcement | — |
| `memory_hints_injector.py` | UserPromptSubmit | Injeta memory hints (MIS) | Constitution Art. IV |
| `memory_updater.py` | PostToolUse | Atualiza JARVIS-MEMORY | REGRA 0 (identity) |
| `notification_system.py` | Notification | Event notifications | — |
| `pattern_analyzer.py` | PostToolUse | Detect recurring patterns | — |
| `pending_tracker.py` | PostToolUse | Track pending items | REGRA 11 (persistence) |
| `post_write_validator.py` | PostToolUse | Validate written files | Constitution Art. I |
| `ralph_wiggum.py` | PostToolUse | Anti-hallucination check | Constitution Art. V |
| `stop_hook_completeness.py` | Stop | Ensure completeness on exit | REGRA 11 (persistence) |
| `subagent_tracker.py` | SubagentStop | Track sub-agent lifecycle | REGRA 27 (routing) |
| `token_checkpoint.py` | PostToolUse | Token usage tracking | — |
| `user_prompt_submit.py` | UserPromptSubmit | Prompt preprocessing | REGRA 27 (routing) |

---

## SUMMARY

| Metric | Count |
|--------|-------|
| Total REGRAs | 31 (0-30) |
| REGRAs com enforcement automático | 28 |
| REGRAs sem enforcement (informational) | 3 (15, 30, parcial) |
| Total hooks | 33 Python files |
| Hooks com REGRA direta | 18 |
| Hooks de infraestrutura | 15 |

---

## CHANGELOG

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0.0 | 2026-02-18 | Criação: mapeamento completo REGRAs ↔ Hooks |
