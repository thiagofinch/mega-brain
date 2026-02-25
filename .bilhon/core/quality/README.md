# Quality Gates System

> **Fonte:** Ralph Local
> **Status:** Pending Import

## Descricao

Sistema de 5 quality gates que devem passar antes de marcar uma story como completa.

## Gates

| Gate | Verificacao | Comando |
|------|-------------|---------|
| Gate 1 | Code Quality | lint, no console.log |
| Gate 2 | Type Check | TypeScript 0 errors |
| Gate 3 | Unit Tests | npm test |
| Gate 4 | Integration | Works with existing code |
| Gate 5 | Build | npm run build |

## Regra

```
Story NAO e marcada complete ate TODOS gates passarem
```

## Fluxo

```
Codigo implementado
    │
    ▼
Gate 1: Code Quality ──→ FAIL? ──→ Fix
    │
    ▼ PASS
Gate 2: Type Check ────→ FAIL? ──→ Fix
    │
    ▼ PASS
Gate 3: Unit Tests ────→ FAIL? ──→ Fix
    │
    ▼ PASS
Gate 4: Integration ───→ FAIL? ──→ Fix
    │
    ▼ PASS
Gate 5: Build ─────────→ FAIL? ──→ Fix
    │
    ▼ PASS
Story COMPLETE
```

## Arquivos a Importar

```
/_IMPORT/RALPH-LOCAL/checklists/quality-gates.md
```
