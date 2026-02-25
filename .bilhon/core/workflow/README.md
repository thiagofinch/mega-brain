# Workflow Scripts

> **Fonte:** Ralph Inferno + Ralph Local
> **Status:** Pending Import

## Descricao

Scripts de workflow unificados do Ralph Inferno e Ralph Local.

## Ralph 3-Loop Architecture

```
OUTER LOOP (Local machine):
  /ralph:discover → PRD com 5 roles
  /ralph:plan → Specs de implementacao
  /ralph:deploy → Push + Start VM
  /ralph:review → Test tunnels

MIDDLE LOOP (orchestrator.sh):
  max 3 iteracoes para completar todos specs
  retry automatico se specs falham

INNER LOOP (ralph.sh per-spec):
  Build → E2E Test → Design Review → Commit
  Auto-CR se falha + retry
```

## Arquivos a Importar

```
/_IMPORT/RALPH-INFERNO/core/scripts/
├── ralph.sh
├── orchestrator.sh
└── discovery.sh

/_IMPORT/RALPH-LOCAL/workflows/
└── autonomous-loop.md
```
