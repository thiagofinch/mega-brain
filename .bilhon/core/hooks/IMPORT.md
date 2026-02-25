# Hooks Import Reference

> **Tipo:** Import Reference
> **Fonte:** /.claude/hooks/
> **Status:** Active

## Descricao

Esta pasta e uma referencia para os hooks localizados em `/.claude/hooks/`.

O BILHON OS mantém retrocompatibilidade completa com a estrutura `.claude/`.
Os hooks originais continuam funcionando normalmente.

## Hooks Disponíveis

Os 33 hooks do Mega Brain estao em `/.claude/hooks/`:

- `creation_validator.py` - PreToolUse
- `post_batch_cascading.py` - PostToolUse
- `enforce_dual_location.py` - PostToolUse
- `session_autosave_v2.py` - Multiple triggers
- `skill_router.py` - UserPromptSubmit
- `quality_watchdog.py` - PostToolUse
- ... (e mais 27 hooks)

## Como Funciona

```
USER PROMPT
    │
    ▼
/.claude/hooks/skill_router.py → Keyword matching
    │
    ▼
Skill/Sub-agent auto-ativado
```

## Novos Hooks BILHON OS

Hooks específicos do BILHON OS serão adicionados aqui conforme implementados:

- [ ] `health_check_hook.py` - Health check do AIOS
- [ ] `quality_gates_hook.py` - Quality gates do Ralph Local
- [ ] `cost_tracking_hook.py` - Cost tracking do Ralph Inferno
