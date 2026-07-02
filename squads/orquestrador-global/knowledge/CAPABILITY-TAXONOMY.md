# Capability Taxonomy — quando escolher cada tipo

> **Consumer:** `agents/intent-parser.md`, `agents/roteador.md` (capability-ranker), `agents/team-coordinator.md` (dag-architect)
> **Story:** STORY-PA-2.1
> **Princípio:** cada capability tem um TIPO específico que governa quando faz sentido escolhê-la — escolher o tipo errado dobra esforço

---

## 5 Categorias Canônicas

| # | Categoria | Path Pattern | Características |
|---|---|---|---|
| 1 | **Squad** | `squads/{name}/` | Coleção governada de agents/tasks/workflows com escopo de domínio |
| 2 | **Agent** | `squads/{n}/agents/*.md` ou `.claude/agents/*.md` | Persona LLM com prompt + responsabilidade clara |
| 3 | **Skill** | `.claude/skills/{name}/SKILL.md` | Workflow auto-contido invocável via `/skill-name` |
| 4 | **Task** | `squads/{n}/tasks/*.{md,yaml}` | Unidade atômica de trabalho com inputs/outputs/gates |
| 5 | **Workflow** | `squads/{n}/workflows/*.{md,yaml}` | Composição de tasks com state machine |

> Capabilities suplementares scaneadas pelo `scan-capabilities.js` mas não decisoras de ranking: hooks, MCPs, packages, services, apps.

---

## Decision Tree — Qual escolher?

```
Demanda chega ao roteador
  │
  ├─ Demanda cobre domínio inteiro (ex: "marketing strategy")?
  │   └─ SIM → Squad. Squads orquestram seus próprios agentes.
  │
  ├─ Demanda é uma decisão/análise específica (ex: "audit este código")?
  │   └─ SIM → Agent. Personas resolvem um tipo de problema.
  │
  ├─ Demanda é um pipeline auto-contido (ex: "make book summary")?
  │   └─ SIM → Skill. Skills wrap pipelines completos.
  │
  ├─ Demanda é um passo único bem definido (ex: "validate story draft")?
  │   └─ SIM → Task. Tasks são unidades atômicas.
  │
  └─ Demanda é multi-passo com dependências (ex: "deploy story end-to-end")?
      └─ SIM → Workflow. Workflows orquestram tasks.
```

---

## 1. Squad — quando escolher

**Sinais:**
- Demanda cruza várias responsabilidades dentro do mesmo domínio
- Você precisa de orquestração entre múltiplos agentes/tasks
- Existe state machine implícita

**Exemplos:**

| Demanda | Squad |
|---|---|
| "Criar SOP de onboarding cliente" | `megabrain-sop` (squad inteiro) |
| "Pesquisa profunda mercado advocacia" | `deep-research` (squad inteiro) |
| "Auditar squad copy e propor melhorias" | `kaizen` (squad inteiro) |

**Anti-pattern:** escolher squad para uma operação atômica (ex: "validar 1 YAML") — overhead desnecessário; use task.

---

## 2. Agent — quando escolher

**Sinais:**
- Decisão ou análise que requer judgment (não-determinístico)
- Persona específica é o ponto-chave (ex: arquitetura precisa de Aria, código precisa de Dex)
- 1 agente resolve 1 tipo de problema

**Exemplos:**

| Demanda | Agent |
|---|---|
| "Reviewar este PR técnico" | `@qa` (Quinn) |
| "Decidir arquitetura de microsserviços" | `@architect` (Aria) |
| "Validar story draft" | `@po` (Pax) |

**Anti-pattern:** invocar agente para trabalho determinístico (ex: copiar arquivo) — usa script.

---

## 3. Skill — quando escolher

**Sinais:**
- Pipeline auto-contido (não precisa do operador acompanhar passo-a-passo)
- Existe `/skill-name` no slash command registry
- Skill é um wrapper de orquestração (Agent Teams + scripts + checklists)

**Exemplos:**

| Demanda | Skill |
|---|---|
| "Resumo do livro X" | `/book-summary` |
| "Quality gate review desta story" | `/review-story` |
| "Roundtable com 3 minds" | `/roundtable` |

**Anti-pattern:** escolher skill quando user já está em meio do trabalho — skills são entry points, não componentes.

---

## 4. Task — quando escolher

**Sinais:**
- Unidade atômica com input + output bem definidos
- Reusável em múltiplos workflows
- < 30min de trabalho típico

**Exemplos:**

| Demanda | Task |
|---|---|
| "Validar YAML changed" | `validate:yaml:changed` |
| "Criar story draft" | `tasks/create-next-story.md` (sm) |
| "Gerar relatório RPN-FMEA" | `tasks/blind-spot-self-audit.yaml` |

**Anti-pattern:** misturar lógica de orquestração dentro de uma task — promova pra workflow.

---

## 5. Workflow — quando escolher

**Sinais:**
- Multi-task com dependências entre elas
- State machine necessária (ex: WIP → Review → Done)
- Gate de aprovação humana entre fases

**Exemplos:**

| Demanda | Workflow |
|---|---|
| "Lançamento de produto end-to-end" | `wf-product-quality-loop.yaml` |
| "Audit cycle de squad" | `cross-squad-audit-cycle.yaml` |
| "Process map 7-phase" | `megabrain-chief` workflow |

**Anti-pattern:** usar workflow para trabalho linear sem ramificação — uma sequência de tasks plain serve.

---

## Cross-references com `capability-cartographer` type tags

| Type tag (cache) | Categoria taxonomy |
|---|---|
| `squad` | Squad |
| `agent` | Agent |
| `skill` | Skill |
| `task` | Task |
| `workflow` | Workflow |
| `template`, `mcp`, `hook`, `app`, `service`, `package` | Suplementares — usadas pelo plan-architect mas não-decisoras de routing |

---

## Common Confusions

| Confusion | Como resolver |
|---|---|
| "Skill vs Workflow?" | Skill é entry point invocável via `/skill`. Workflow é composição interna de tasks. Skills frequentemente envolvem 1 ou mais workflows. |
| "Agent vs Task?" | Agent é uma persona (você "ativa" o agent). Task é uma operação (você "executa" a task — pode usar agent OU script). |
| "Squad vs Agent?" | Squad agrupa múltiplos agents. Roteador escolhe squad primeiro, depois o squad escolhe seu próprio entry-agent. |
| "Task vs Script?" | Task é definição (markdown/yaml descrevendo o que fazer). Script é a implementação determinística (ex: `validate-plan.js`). Tasks podem invocar scripts. |
