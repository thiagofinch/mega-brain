# Health Check System

> **Fonte:** AIOS Framework
> **Status:** Pending Import

## Descricao

Sistema de health check com auto-fix em 3 tiers, importado do AIOS.

## Dominios (5)

| Dominio | O que verifica |
|---------|----------------|
| Project | package.json, deps, framework config |
| Local | Git, npm, IDE, disk, memory, network |
| Repository | Git status, branches, conflicts, lockfile |
| Deployment | Env files, CI/CD, Docker |
| Services | MCP, GitHub CLI, Claude Code, APIs |

## Auto-Fix Tiers

| Tier | Comportamento |
|------|---------------|
| Tier 1 | Silent auto-fix (safe, reversible) |
| Tier 2 | Prompted confirmation |
| Tier 3 | Manual guide |

## Modos

- `quick` - < 10 segundos
- `full` - < 60 segundos

## Arquivos a Importar

```
/_IMPORT/AIOS/aios-core-main/.aios-core/core/health-check/
├── health-check.py
├── domains/
│   ├── project.py
│   ├── local.py
│   ├── repository.py
│   ├── deployment.py
│   └── services.py
└── auto-fix/
    ├── tier1.py
    ├── tier2.py
    └── tier3.py
```
