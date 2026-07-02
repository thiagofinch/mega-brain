---
description: Alias de compatibilidade para o comando /process-jarvis
argument-hint: [PATH] [--verbose] [--dry-run] [--auto-enrich]
---

# /pipeline-jarvis - Alias de /process-jarvis

Use este comando apenas como alias de compatibilidade. O contrato canonico de execucao continua em `/process-jarvis`.

## REGRA

- Preserve `$ARGUMENTS` sem alteracao
- Reutilize as mesmas fases, checkpoints, flags e side effects de `/process-jarvis`
- Nao introduza fluxo alternativo

## EXECUCAO

```text
EXECUTE /process-jarvis $ARGUMENTS
```
