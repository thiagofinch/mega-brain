# /força-total — Orquestração Global (MegaBrain)

> Mecanismo de orquestração global do MegaBrain: recebe uma demanda em linguagem
> natural, descobre as capabilities (squads/agents/skills/tasks/workflows), roteia
> para os melhores agentes e produz um plano de execução completo (DAG + riscos +
> handoff) **com Step 1 quality-gate** — despeja o plano e PARA para aprovação
> humana antes de qualquer avanço.
>
> Transferido de `the-hub` (squad orquestrador-global v3.1.1) com paridade total.
> Interface de ativação renomeada: `orquestrador-global` → **`/força-total`**.

## Arquitetura

```
        DEMANDA (linguagem natural)
              │
              ▼
   ┌─────────────────────────────┐
   │  /força-total (skill)        │
   │  STEP 1 — QUALITY GATE       │ ◀── despeja plano + PARA p/ aprovação
   └──────────────┬──────────────┘
                  │ (aprovado)
   ┌──────────────▼──────────────┐
   │  squad orquestrador-global   │  (o motor — nome interno preservado)
   │  L1 intent-parser            │
   │  L2 capability-cartographer  │ ◀── lê catálogo + capability-cache
   │  L3 roteador (scoring)       │
   │  L4 dag-architect + FMEA     │
   │  L5 validate + audit         │
   │  L6 handoff (NÃO executa)    │
   └─────────────────────────────┘
              │
              ▼
   plano (plan.json) → plan-to-swarm → /swarm-execute (execução)
```

## Componentes (inventário)

| Componente | Path | Papel |
|------------|------|-------|
| Skill entry-point | `.claude/skills/força-total/SKILL.md` | Interface + Step 1 quality-gate |
| Skill alias (superseded) | `.claude/skills/orquestrador-global/SKILL.md` | Redirect → /força-total |
| Squad motor | `squads/orquestrador-global/` | 7 agentes + scripts + workflows + knowledge |
| Catálogo | `.data/agent-routing-index.json` | 737 candidatos (93 squads) |
| Registries | `squads/mega-brain/data/agent-registry.yaml` + `chief-interface-registry.yaml` | Metadados de agentes/chiefs |
| Recomendador | `scripts/agents-recommend.js` | "query → melhor agente" |
| Gerador catálogo | `scripts/build-agent-routing-index.js` | Escaneia squads → catálogo |
| Gerador registries | `scripts/sync-agent-registry.js` | Escaneia squads → registries |
| Gerador skills-chief | `scripts/sync-chief-skills.js` | Cria skills projetadas dos entry_agents |
| Hooks | `.claude/hooks/pre-execution-block.sh` + `post-plan-validate.sh` | Plan-only enforcement |
| Injector | `scripts/capability-hint-injector.js` | Sugestão passiva por prompt |

> **Nota ESM:** o MegaBrain é `"type": "module"`. Os scripts de routing rodam como
> CommonJS via `scripts/package.json` (`{"type":"commonjs"}`). Não renomear para `.cjs`.

## Runbook de Manutenção

**Sempre que o ecossistema muda** (novo agente, squad, skill, chief), regenere os
catálogos — eles ficam stale em silêncio:

```bash
# 1. (se criou/declarou novo entry_agent) gerar skills-chief projetadas
node scripts/sync-chief-skills.js

# 2. gerar os registries (metadados de agentes/chiefs)
node scripts/sync-agent-registry.js

# 3. gerar o catálogo de roteamento
npm run build:agent-routing-index

# 4. validar (espelha o CI)
npm run validate:agent-routing:ci
```

| Mudou no repo | Rodar |
|---------------|-------|
| Novo agente / squad | sync-agent-registry → build-agent-routing-index |
| Novo entry_agent (chief) | sync-chief-skills → sync-agent-registry → build |
| Nova skill | build-agent-routing-index |
| Antes de usar /força-total "pra valer" | build (recomendável) |

## Uso

```
/força-total Lançar curso de IA pra Black Friday
/força-total mode=CRITICAL Investigar incidente prod
/força-total --dry-run Campanha
```

O **Step 1** é automático e obrigatório: após a query, a skill despeja o plano
completo (agentes, workflows, tasks, ordem, riscos) e pede aprovação (s/n) antes
de gerar o plano canônico. Plan-only por design — nunca executa sozinho.

## Referências

- Skill: `.claude/skills/força-total/SKILL.md`
- Rule plan-only: `.claude/rules/plan-architect-execution-handoff.md`
- SOP catálogo: `docs/reference/agent-routing-catalog-update-sop.md`
- Catálogo humano: `docs/reference/agent-entrypoints.md`
- Agente: `squads/orquestrador-global/agents/plan-architect.md`
