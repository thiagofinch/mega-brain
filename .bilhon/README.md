# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                              BILHON OS v1.0                                  ║
# ║                 "IA com tentaculos que orquestra orquestracoes"              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

## O Que e BILHON OS?

BILHON OS e a unificacao de 4 sistemas de IA separados em um sistema coeso:

| Sistema | Contribuicao | Status |
|---------|--------------|--------|
| **Mega Brain** | Base, 30 regras, 33 hooks, DNA 5 camadas | NATIVO |
| **AIOS** | 12 agentes tech, health check, schemas | IMPORTADO |
| **Ralph Inferno** | 3-loop, notifications, cost tracking | IMPORTADO |
| **Ralph Local** | Quality gates, compound learning | IMPORTADO |

## Estrutura de Pastas

```
.bilhon/
├── core/                           # Core do BILHON OS
│   ├── config/                     # Configuracoes centrais
│   │   └── bilhon-config.yaml      # Config master
│   ├── hooks/                      # Import de /.claude/hooks/
│   ├── skills/                     # Import de /.claude/skills/
│   ├── state/                      # Estados do sistema
│   ├── schemas/                    # JSON Schemas (AIOS)
│   ├── health/                     # Health check (AIOS)
│   ├── security/                   # Security checks (Ralph Inferno)
│   ├── lib/                        # Utilities (Ralph Inferno)
│   ├── workflow/                   # Workflow scripts (Ralph)
│   ├── learning/                   # Compound learning (Ralph Local)
│   ├── tracking/                   # Cost tracking
│   └── quality/                    # Quality gates (Ralph Local)
├── jarvis/                         # Import de /.claude/jarvis/
├── mission-control/                # Import de /.claude/mission-control/
└── README.md                       # Este arquivo
```

## Retrocompatibilidade

**IMPORTANTE:** A pasta `.claude/` continua funcionando normalmente.

O BILHON OS NAO substitui `.claude/`, ele EXTENDE:

- `.claude/hooks/` → Continua sendo a fonte de hooks
- `.claude/skills/` → Continua sendo a fonte de skills
- `.claude/jarvis/` → Continua sendo o cerebro JARVIS

`.bilhon/` adiciona:
- Novos componentes (health, quality, workflow)
- Configuracao centralizada (bilhon-config.yaml)
- Integracoes unificadas (MCP Hub)

## Sistema de Agentes (4 Tiers)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TIER 1: ORCHESTRATOR                                                       │
│  └── JARVIS (cerebro central)                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 2: COUNCIL (via /council)                                             │
│  ├── PERSONS (7): Hormozi, Cole, Miner, Haynes, FSS, G4, Scalable          │
│  ├── CARGOS (11): CRO, CFO, CMO, COO, Closer, BDR, etc.                    │
│  └── TECH (12): dev, architect, devops, qa, pm, sm, etc.                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 3: SUB-AGENTS (auto-ativacao)                                         │
│  └── /.claude/jarvis/sub-agents/                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 4: DISCOVERY ROLES (para novos projetos)                              │
│  └── Analyst, UX Designer, PM, Architect, Business Analyst                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Workflows Disponiveis

1. **Content Pipeline** (JARVIS): 5 fases para processamento de conhecimento
2. **Project Workflow** (BILHON OS): 6 fases para desenvolvimento de software
   - Phase 0: Bootstrap
   - Phase 1: Discovery (5 roles)
   - Phase 2: Planning (stories + specs)
   - Phase 3: Development (3-loop)
   - Phase 4: Release
   - Phase 5: Learning (compound)

## Arquivos de Configuracao

| Arquivo | Proposito |
|---------|-----------|
| `bilhon-config.yaml` | Configuracao central do sistema |
| `/CLAUDE.md` | Regras do JARVIS (30 regras) |
| `/reference/RULES/` | Rule Groups (lazy loading) |

## Status de Implementacao

- [x] SPEC-000: Clone repositories (/_IMPORT/)
- [x] SPEC-001: Create .bilhon/ structure
- [ ] SPEC-002: Import 12 AIOS tech agents
- [ ] SPEC-003: Implement unified project workflow
- [ ] SPEC-004: Create MCP Hub
- [ ] SPEC-005: Implement quality system
- [ ] SPEC-006: Notifications + cost tracking
- [ ] SPEC-007: Compound learning

---

**Versao:** 1.0.0
**Data:** 2026-01-17
**Autor:** JARVIS (BILHON OS)
