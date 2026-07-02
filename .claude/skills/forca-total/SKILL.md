---
name: "forca-total"
description: "Use quando o operador pedir /força-total para um plano de orquestração global antes de executar: descobrir squads/capabilities, sintetizar DAG, paralelização, critical path, riscos FMEA, pre-mortem, handoff e next_action. SEMPRE despeja o plano completo (todos os agentes, workflows, tasks, ordem) e PARA para aprovação humana ANTES de avançar (Step 1 quality-gate). Triggers: força-total, forca-total, orquestração global, global orchestration plan, plan.yaml, plan.md, Mermaid DAG, critical path, capability discovery, pre-mortem. Produz plano global, DAG, resumo de 3 linhas, top risks e handoff. NOT for plano técnico local; use plan-architect para plano técnico especializado."
version: "1.1.1"
user-invocable: true
activation_type: "pipeline"
agent: "plan-architect"
owner_squad: "orquestrador-global"
---

# forca-total — Orquestração Global com Quality Gate

> **Auto-Trigger:** Quando o operador pedir orquestração global, plano antes de executar, descoberta de squads/agentes, DAG de execução, ou força-total
> **Keywords:** "forca-total", "força-total", "orquestração global", "orquestracao global", "plano de orquestração", "global orchestration", "DAG", "critical path", "capability discovery", "pre-mortem", "plano antes de executar", "qual agente"
> **Prioridade:** ALTA

> **Skill canonical entry-point** para o squad `orquestrador-global` no MegaBrain.
> Renomeada de `orquestrador-global` → `forca-total` (interface de ativação).
> O squad interno (motor) continua `orquestrador-global`; `/forca-total` é a porta de entrada.
>
> Source: `squads/orquestrador-global/agents/plan-architect.md`
> ADR: `docs/adrs/ADR-PA-001-plan-architect-model-defaults.md` (ACCEPTED 2026-04-28)

## When to use this skill

Invoque quando precisar:

1. **Receber demanda informal** em linguagem natural e transformar em plano executável
2. **Discovery cross-squad** — saber quais capabilities (squads, agents, skills, tasks, workflows) existem para uma demanda
3. **DAG synthesis** — decompor demanda em nós com dependências, paralelização, critical path (CPM)
4. **Risk assessment** — FMEA RPN per-node antes de executar
5. **Plan-only mode** — quer ver o plano antes de spawnar nada

**NÃO use** quando:
- Já sabe exatamente qual agent invocar diretamente (ex: `@dev fix bug X`)
- Tarefa é trivial (1 file edit) — overhead do planning não vale
- Quer execução imediata — esta skill produz APENAS plano (plan-only por design)

## Usage

```
/força-total Lançar curso de IA pra Black Friday
/força-total mode=COMPLEX Refatorar dashboard sales p/ multi-tenant
/força-total mode=CRITICAL Investigar incidente prod gateway-ai
/força-total budget=10 Criar SOP de onboarding cliente
/força-total --dry-run Lançar campanha
```

---

## STEP 1 — Quality Gate Automático (NON-NEGOTIABLE)

**Após receber a query, ANTES de qualquer avanço, a skill SEMPRE executa o Step 1:**

1. Roda discovery (L1 intent + L2 capability-cartographer + L3 roteador) consultando o catálogo real (`.data/agent-routing-index.json`).
2. **DESPEJA NO CHAT o plano de execução completo** em formato legível:

```
📋 PLANO DE EXECUÇÃO — Step 1 Quality Gate

Demanda: {query do operador}
Modo: {SIMPLE|COMPLEX|CRITICAL}  |  Confiança: {0-1}

═══ 🤖 AGENTES SELECIONADOS ═══
┌──────┬────┬────────────────────────────┬──────────────┬─────────────────────────────────┐
│ Nó   │ ✦  │ Agente / Squad             │ Papel        │ O que faz                       │
├──────┼────┼────────────────────────────┼──────────────┼─────────────────────────────────┤
│ N0   │ 🕵️ │ {squad}/{agente}           │ {role}       │ {o que faz}                     │
│      │ 🧠 │ {squad}/{agente}           │ {role}       │ {o que faz}                     │
├──────┼────┼────────────────────────────┼──────────────┼─────────────────────────────────┤
│ N1   │ 📋 │ {squad}/{agente}           │ {role}       │ {o que faz}                     │
└──────┴────┴────────────────────────────┴──────────────┴─────────────────────────────────┘
    (cada agente ganha 1 ícone próprio na coluna ✦; linha horizontal separa cada grupo de Nó)

═══ 🔄 WORKFLOWS ═══
┌────────────────────┬───────────────────────────────────────────────────────────────┐
│ Workflow           │ Descrição (se aplicável)                                       │
├────────────────────┼───────────────────────────────────────────────────────────────┤
│ {workflow-id}      │ {descrição}                                                    │
└────────────────────┴───────────────────────────────────────────────────────────────┘

═══ 📦 TASKS POR NÓ ═══
┌──────┬────────────────────────┬──────────────────────────────────┬───────────┐
│ Nó   │ Task                   │ Input → Output                   │ Duração   │
├──────┼────────────────────────┼──────────────────────────────────┼───────────┤
│ N1   │ {task}                 │ {input} → {output}               │ ~{dur}    │
└──────┴────────────────────────┴──────────────────────────────────┴───────────┘

═══ 🗺️ ORDEM DE EXECUÇÃO (DAG) ═══

  Legenda:  🌱 root   ──▶ depende de   ‖ paralelo   ⚡ critical path
            ⏸ gate    🔁 loop          🔗 embed/handoff

   WAVE 0 ─ paralelo             WAVE 1 ─ pós-N0           WAVE 2
  ┌───────────────────┐         ┌───────────────┐
  │ 🌱 N0 {nome}      │────┬───▶│ N1 {nome}     │──┬──▶ ⚡ N{x} {nome}
  │    (ROOT)         │    ├───▶│ N{y} {nome}   │  │
  └───────────────────┘    └───▶│ N{z} {nome}   │  └──▶ N{w} {nome} 🔗 embed N{i}
  ┌───────────────────┐  (indep.)└───────────────┘             │
  │ N{i} {nome}       │───────────────────────────────────────┘
  └───────────────────┘

  ⚡ Critical path : N0 ──▶ N1 ──▶ {N{x} ‖ N{w}}      ⏱ {duração total}
  ‖ Paralelos     : Wave0 {N0 ‖ N{i}} · Wave1 {N1 ‖ N{y} ‖ N{z}}
  ⏸ Gates         : {nó}@RPN>300 → pre-mortem · {nó}@deadline → handoff

═══ ⚠️ RISCOS (FMEA) ═══
  Severidade: 🚨 ALTO (RPN>300) · ⚠️ MÉDIO (150–300) · 🔻 BAIXO (<150)
┌───────┬──────┬───────────────────────────────────┬───────┬──────────────────────────┐
│ Sev   │ Nó   │ Risco                             │ RPN   │ Mitigação                │
├───────┼──────┼───────────────────────────────────┼───────┼──────────────────────────┤
│ ALTO  │ N0   │ {risco}                           │ {n}   │ {mitigação}              │
│ MÉDIO │ N3   │ {risco}                           │ {n}   │ {mitigação}              │
│ BAIXO │ N6   │ {risco}                           │ {n}   │ {mitigação}              │
└───────┴──────┴───────────────────────────────────┴───────┴──────────────────────────┘
```

> **Padrão didático (NON-NEGOTIABLE):** as seções AGENTES / WORKFLOWS / TASKS / RISCOS
> renderizam como TABELAS ASCII (bordas `┌─┬─┐`), e o bloco `🗺️ ORDEM DE EXECUÇÃO (DAG)`
> como desenho de boxes/setas com waves rotuladas — nunca a forma compacta de uma linha.
> O visual vem antes da prosa. Na tabela AGENTES, cada agente ganha 1 ícone próprio na coluna
> `✦` (semântico ao seu papel) e uma linha horizontal `├──┼──┤` separa cada grupo de Nó.
> Ícones nos headers de seção (🤖 🔄 📦 🗺️ ⚠️) e na legenda/DAG
> (🌱 root · ⚡ critical · ‖ paralelo · ⏸ gate · 🔁 loop · 🔗 embed). Severidade FMEA na legenda
> acima da tabela (🚨 ALTO · ⚠️ MÉDIO · 🔻 BAIXO); a coluna `Sev` fica em texto para alinhar a
> tabela. Sem bolinhas coloridas dentro de células.

3. **PARA e pede aprovação explícita:**

```
⏸ Aprova este plano? (s/n)
   • s → avança para gerar o plano canônico completo (plan.json) + handoff
   • n → operador ajusta a demanda ou os agentes, e o Step 1 re-roda
```

**Invariante:** a skill NUNCA avança do Step 1 sem aprovação humana explícita. O despejo do plano + o gate de aprovação são obrigatórios em TODA invocação. Isto é o quality-gate que impede execução cega de orquestração — o operador SEMPRE vê os nomes de todos os agentes/workflows/tasks/ordem antes de qualquer avanço.

---

## Pipeline (6 phases)

```
DEMAND
  ↓
[STEP 1 — QUALITY GATE]  ← despeja plano + PARA para aprovação (NON-NEGOTIABLE)
  ↓ (só avança com aprovação)
[L1] intent-parser → confidence + parsed{domain,complexity,BUs,deadline}
     elicitation gate (if confidence<0.7, max 3 questions)
  ↓
[L2] capability-cartographer → ranked capabilities (cache-first via scan-capabilities.js)
  ↓
[L3] roteador + RoutingDecision v2 → selected_capabilities com routing_decision_id, alternatives, score_breakdown, hard gates e IDS decisions
  ↓
[L4] dag-architect (plan_only=true) → DAG + CPM + parallel groups
     risk-assessor → FMEA RPN per node
     [pre-mortem if RPN_max>300 OR mode=CRITICAL]
  ↓
[L5] validate-plan.js (cycle/schema/routing/constitutional) → audit-plan.js (persist + register)
  ↓
[L6] HANDOFF: 3-line summary + Mermaid + top risks + next_action (NOT executed)
```

## Output

Persistido em `outputs/plans/{date}_{slug}/`:
- `plan.yaml` / `plan.md` / `plan.json` — canonical (gitignored)
- `audit.jsonl` — provenance (committed)

Plus appends:
- `squads/orquestrador-global/data/plan-registry.yaml` (plan index)
- `.data/audit-trail.jsonl` (audit)

## Plan-only por design (P1 — NON-NEGOTIABLE)

`/força-total` e o agente `plan-architect` são **plan-only**: produzem o plano e NUNCA executam.
Enforced por `.claude/hooks/pre-execution-block.sh`. A execução é via:
`plan-to-swarm.js` → `/swarm-execute` (ou adapter equivalente do MegaBrain).

## References

- Source agent: `squads/orquestrador-global/agents/plan-architect.md`
- Catálogo: `.data/agent-routing-index.json` (gerado por `scripts/build-agent-routing-index.js`)
- Recomendador: `scripts/agents-recommend.js`
- Rule de execução: `.claude/rules/plan-architect-execution-handoff.md`
