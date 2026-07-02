---
task: consult-chief
name: 'Task: Consult Chief (Squad Planning)'
version: "3.1.1"
category: operations
difficulty: intermediate
responsavel: '@plan-architect'
responsavel_type: Agent
atomic_layer: Molecule
elicit: false
estimated_time: 30-60min
model: sonnet
Entrada:
- campo: brief
  tipo: markdown
  obrigatorio: true
  default: null
Saida:
- campo: deliverable
  tipo: markdown
pre_condition: Squad config (squads/{id}/config.yaml) readable and demand_context provided
post_condition: Chief consultation output emitted with selected agents, task list, estimated cost, and dependencies
performance:
  error_handling: graceful with fallback + retry
domain: tactical
task_id: consult-chief
squad: orquestrador-global
status: ready
execution_type: hybrid
orchestration_boundary:
  live_routing_performed: false
  external_dispatch_performed: false
  workspace_write_performed: false
megabrain_validation:
  last_run: "20260514-validate-deep"
  validated_at: "2026-05-15T00:00:00Z"
  validator: mega-brain/megabrain-chief
  mode: deep
  squad: orquestrador-global
  status: pass
  evidence:
    - schema_contract_normalized
    - task_boundary_declared
    - plan_only_orchestration_preserved
---

# Task: Consult Chief (Squad Planning)

## Metadata
```yaml
id: consult-chief
name: Consultar Chief para Planejamento de Squad
version: 1.0.0
executor: team-coordinator
workflow: executar-com-team
estimated_time: 1-2 minutes per squad
```

## Purpose

Formalizar a consulta ao "chief" de um squad durante o planejamento de execucao multi-squad.
O Maestro **simula** a perspectiva do chief lendo a configuracao do squad, selecionando agentes
relevantes, definindo tarefas e estimando custo. Chiefs nao existem como agentes rodando durante
planejamento — este task e uma leitura estruturada de configs.

---

## Trigger

```yaml
trigger:
  type: internal
  event: "Chamado pelo execute-multi-squad-team (Fase 0, Step 0.3)"
  sources:
    - "execute-multi-squad-team.md (durante planejamento staged)"
    - "Maestro orchestration (consulta manual via *consult)"
  note: "Task interno — nao acionado diretamente pelo usuario"
```

---

## Input Requirements

| Campo | Tipo | Obrigatorio | Exemplo |
|-------|------|-------------|---------|
| squad_id | string | Sim | "copywriting" |
| demand_context | object | Sim | {demand: "Criar sales page", tipo: "landing_page"} |
| available_inputs | list | Nao | ["pesquisa-mercado.md", "briefing.md"] |
| stage_number | number | Nao | 2 |
| previous_stage_outputs | list | Nao | ["stage-1/squad-01-deep-scraper/"] |

---

## Execution Flow

### Step 1: Carregar Configuracao do Squad

```
Ler: squads/{squad_id}/config.yaml
Extrair:
  - agents (todos os tiers)
  - components (tasks, templates, checklists)
  - knowledge (domain knowledge)
  - problems_solved
  - quality_standards
```

### Step 2: Selecionar Agentes Relevantes

Com base na demanda e na config do squad:

```
Para cada agente no squad:
  - Avaliar se o role/description e relevante para a demanda
  - Classificar relevancia: essencial | util | nao_necessario
  - Selecionar apenas agentes essenciais e uteis

Resultado: lista de agentes selecionados com justificativa
```

**Regras de selecao:**
- Manter chief do squad (entry_agent) sempre
- Incluir agentes cujo `role` ou `description` match com a demanda
- Excluir agentes de tier inferior se tier superior cobre a necessidade
- Maximo de agentes = config.team_config.max_agents ou default 5

### Step 3: Definir Padrao e Tarefas

```
1. Identificar padrao de execucao do squad:
   - Verificar team_config.patterns se existe
   - Ou inferir: pipeline | parallel-workers | builder-validator

2. Para cada agente selecionado, definir tarefas:
   - Baseado nos components.tasks do squad
   - Filtrado pela demanda
   - Com inputs e outputs esperados

3. Mapear dependencias entre tarefas:
   - Quais tarefas sao sequenciais vs paralelas
   - Quais outputs alimentam quais inputs
```

### Step 4: Calcular Custo Estimado

```
Para cada agente selecionado:
  - Atribuir modelo conforme MODEL-STRATEGY.md:
    - chief/architect → opus
    - implementer/writer → sonnet
    - researcher/classifier → haiku
  - Estimar tarefas (numero de tasks)
  - Calcular custo relativo: opus=3x, sonnet=1x, haiku=0.3x

Resultado: tabela de custo por agente + total
```

### Step 5: Gerar Chief Report

Compilar todas as informacoes em um report estruturado.

---

## Output: Chief Report

```markdown
## Chief Report: {squad_name}

### Squad
- **ID:** {squad_id}
- **Nome:** {squad_name}
- **Chief:** {chief_agent_name}
- **Dominio:** {domain}

### Agentes Selecionados

| # | Agente | Role | Modelo | Tasks | Justificativa |
|---|--------|------|--------|-------|---------------|
| 1 | {agent} | {role} | {model} | {N} | {why selected} |

### Padrao de Execucao
- **Padrao:** {pattern_name}
- **Justificativa:** {why this pattern}

### Tarefas Planejadas

| Task ID | Tarefa | Agente | Depende de | Inputs | Outputs |
|---------|--------|--------|------------|--------|---------|
| T1 | {task} | {agent} | - | {inputs} | {outputs} |
| T2 | {task} | {agent} | T1 | {inputs} | {outputs} |

### Inputs Necessarios
- {input 1}: {de onde vem}
- {input 2}: {de onde vem}

### Outputs Esperados
- {output 1}: {descricao}
- {output 2}: {descricao}

### Estimativa de Custo

| Modelo | Agentes | Tasks | Custo Relativo |
|--------|---------|-------|----------------|
| opus | {N} | {N} | {Nx3} |
| sonnet | {N} | {N} | {Nx1} |
| haiku | {N} | {N} | {Nx0.3} |
| **Total** | **{N}** | **{N}** | **{total}** |

### Riscos e Dependencias
- {risco 1}
- {dependencia externa}
```

---

## Quality Gates

- [ ] Config do squad lida com sucesso?
- [ ] Ao menos 1 agente selecionado?
- [ ] Padrao de execucao identificado?
- [ ] Todas as tarefas tem inputs e outputs definidos?
- [ ] Custo estimado calculado?

## Success Metrics

| Metrica | Alvo | Descricao |
|---------|------|-----------|
| Config load time | < 2s | Tempo para ler e parsear config do squad |
| Agent selection accuracy | > 90% | Agentes selecionados sao relevantes para a demanda |
| Task coverage | 100% | Todas as tarefas necessarias para a demanda estao mapeadas |
| Cost estimate variance | < 20% | Custo estimado vs custo real da execucao |
| Report completeness | 100% | Todas as secoes do chief report preenchidas |

---

## Error Handling

```yaml
config_not_found:
  acao: "Retornar erro com squad_id e sugerir verificar SQUAD-REGISTRY"
  mensagem: "Config nao encontrada para squad '{squad_id}'. Verificar squads/"

no_agents_match:
  acao: "Retornar warning e sugerir squad alternativo"
  mensagem: "Nenhum agente do squad '{squad_id}' e relevante para esta demanda"

missing_inputs:
  acao: "Listar inputs faltantes e sugerir stage anterior"
  mensagem: "Inputs necessarios nao disponiveis: {lista}. Considerar adicionar squad ao stage anterior"
```

---

## Example

### Input
```yaml
squad_id: "copywriting"
demand_context:
  demand: "Criar sales page para curso de um nicho de saúde"
  tipo: "landing_page"
  publico: "profissionais de saude"
available_inputs:
  - "stage-1/squad-01-deep-scraper/pesquisa-mercado.md"
  - "stage-1/squad-01-deep-scraper/analise-concorrentes.md"
stage_number: 2
```

### Output (Chief Report)
```markdown
## Chief Report: Copywriting

### Squad
- **ID:** copywriting
- **Nome:** Copywriting
- **Chief:** copywriting-chief
- **Dominio:** marketing

### Agentes Selecionados

| # | Agente | Role | Modelo | Tasks | Justificativa |
|---|--------|------|--------|-------|---------------|
| 1 | copywriting-chief | Chief/Strategist | opus | 2 | Estrategia e revisao final |
| 2 | copy-expert | Copywriter | sonnet | 3 | Escrita das secoes da sales page |
| 3 | headline-specialist | Headlines | sonnet | 1 | Headlines e CTAs |

### Padrao de Execucao
- **Padrao:** pipeline
- **Justificativa:** Chief define estrategia → Expert escreve → Specialist refina headlines

### Tarefas Planejadas

| Task ID | Tarefa | Agente | Depende de | Inputs | Outputs |
|---------|--------|--------|------------|--------|---------|
| T1 | Definir estrategia de copy | copywriting-chief | - | pesquisa + briefing | estrategia.md |
| T2 | Escrever secoes da page | copy-expert | T1 | estrategia.md | sales-page-draft.md |
| T3 | Criar headlines e CTAs | headline-specialist | T1 | estrategia.md | headlines.md |
| T4 | Revisar e consolidar | copywriting-chief | T2, T3 | draft + headlines | sales-page-final.md |

### Estimativa de Custo

| Modelo | Agentes | Tasks | Custo Relativo |
|--------|---------|-------|----------------|
| opus | 1 | 2 | 6 |
| sonnet | 2 | 2 | 2 |
| **Total** | **3** | **4** | **8** |
```

## Integration

- **Squad:** orquestrador-global
- **Upstream:** *definir tasks que alimentam esta*
- **Downstream:** *definir tasks que esta alimenta*
