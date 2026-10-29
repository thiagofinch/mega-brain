# Claude Code Hooks

Hooks de governança e automação do Mega Brain. A fiação fica em `.claude/settings.json`; os scripts ficam nesta pasta (`.claude/hooks/`).

## Arquitetura

Cada hook roda por evento do Claude Code. Os scripts Python são chamados por `pyrun.sh`, que escolhe um interpretador Python 3 disponível (e sai em silêncio se não houver nenhum).

| Evento | Hooks registrados |
|--------|-------------------|
| SessionStart | 8 |
| UserPromptSubmit | 10 |
| PreToolUse | 19 |
| PostToolUse | 29 |
| PreCompact | 1 |
| Stop | 12 |

### SessionStart

`session_start.py`, `skill_indexer.py`, `inbox_age_alert.py`, `session_index.py`, `memory_persistence.py`, `startup_health.py`, `hook_auditor.py`, `cleanup_expired_review_queue.py`

### UserPromptSubmit

`synapse-engine.js`, `skill_router.py`, `quality_watchdog.py`, `user_prompt_submit.py`, `enforce_plan_mode.py`, `pending_tracker.py`, `capability_hint_injector.py`, `canon_hint_injector.py`, `enforce_pipeline_integrity.py`, `personal_access_logger.py`

### PreToolUse

`enforcement_guard.py`, `claude_md_guard.py`, `creation_validator.py`, `directory_contract_guard.py`, `pre_commit_audit.py`, `agent_deprecation_guard.py`, `pipeline_merge_guard.py`, `structure-validation.py`, `workspace_contract_guard.py`, `constitution_gate.py`, `bucket_isolation_guard.py`, `validate_product_registry.py`, `validate_insights_state_schema.py`, `chronicler_registry_guard.py`, `capability_enforcement.py`, `enforce-git-push-authority.sh`, `enforce-story-reference.sh`, `enforce-quality-first.sh`, `brain_first_lookup.py`

### PostToolUse

`post_tool_use.py`, `enforce_dual_location.py`, `agent_creation_trigger.py`, `epistemic_validator.py`, `checkpoint_observer.py`, `agent_index_updater.py`, `claude_md_agent_sync.py`, `agent_memory_persister.py`, `post_batch_cascading.py`, `pipeline_phase_gate.py`, `pipeline_orchestrator.py`, `mce_step_logger.py`, `pipeline_manifest_watcher.py`, `product-completeness.py`, `rag_rebuild_trigger.py`, `governance_auto_update.py`, `canon_index_rebuilder.py`, `invalidate_capability_embeddings.py`, `env_change_detector.py`, `claude_md_audit.py`, `refresh_navigation_map.py`, `density_trigger.py`, `dossier_frontmatter_validator.py`, `deliberation_gate.py`, `deliberation_convergence.py`, `rag_post_rebuild_validator.py`, `promotion_detector_hook.py`, `audit_log_cross_bucket.py`, `post-edit-lint.sh`

### PreCompact

`precompact-session-digest.js`

### Stop

`delivery_guardian.py`, `stop_hook_completeness.py`, `session_end.py`, `ralph_wiggum.py`, `session_index.py`, `mce_session_reporter.py`, `stop_workspace_audit.py`, `memory_persistence.py`, `quiet_hours_gate.py`, `post_task_suggester.py`, `chronicler_emission_backstop.py`, `mce_log_autodump.py`

## Hooks que são no-op nesta distribuição

Alguns hooks dependem de artefatos que não fazem parte da distribuição pública (gate de recuperação "brain-first", validadores de governança do workspace, detector de promoção, runner de digest do PreCompact, registry de capabilities). Eles continuam registrados em `settings.json`, mas terminam em silêncio, sem imprimir nada e sem bloquear: `brain_first_lookup.py`, `stop_workspace_audit.py`, `promotion_detector_hook.py`, `precompact-session-digest.js`. Os de capabilities (`capability_enforcement.py`, `post_task_suggester.py`, `capability_hint_injector.py`, `invalidate_capability_embeddings.py`) ficam desligados sem o registry. O motivo de cada um está no docstring do próprio arquivo.

## Exit Codes

| Code | Significado |
|------|-------------|
| 0 | Permitido (operação continua) |
| 2 | Bloqueado (operação cancelada, mostra stderr) |
| Outro | Erro não-bloqueante |

## Input Format

Hooks recebem JSON via stdin:

```json
{
  "session_id": "abc123",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file"
  },
  "cwd": "/path/to/project"
}
```

## Debugging

Para testar um hook manualmente:

```bash
echo '{"tool_name": "Write", "tool_input": {"file_path": "workspace/x.md"}}' | CLAUDE_PROJECT_DIR="$PWD" python3 .claude/hooks/workspace_contract_guard.py
echo $?
```

Para auditar a saúde de todos os hooks registrados (existência, sintaxe, caminhos antigos): `python3 .claude/hooks/hook_auditor.py`.

## Configuração

Hooks são configurados em `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/pyrun.sh\" \"$CLAUDE_PROJECT_DIR/.claude/hooks/enforcement_guard.py\"",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

## Manutenção

Para adicionar novo hook:

1. Criar o arquivo em `.claude/hooks/` (Python, só stdlib + PyYAML).
2. Registrar em `.claude/settings.json`.
3. Documentar neste README.
4. Testar com casos reais (e rodar `hook_auditor.py`).

Regra de ouro: um hook que depende de algo ausente nunca imprime erro nem bloqueia; degrada para no-op silencioso e registra o motivo no docstring.
