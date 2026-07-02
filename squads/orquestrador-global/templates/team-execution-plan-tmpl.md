# Team Execution Plan Template

> Template para plano de execucao apresentado ao usuario ANTES de spawnar uma equipe de agentes

## Metadata

```yaml
template:
  id: team-execution-plan
  name: Team Execution Plan
  agent: team-coordinator
  output_format: markdown
  requires_approval: true
```

---

# Team Execution Plan | {{plan_id}}

**Timestamp:** {{timestamp}}
**Demand ID:** {{demand_id}}
**Status:** Aguardando Aprovacao

---

## Resumo da Demanda

### Solicitacao Original
```
{{user_input}}
```

### Intencao Classificada
| Campo | Valor |
|-------|-------|
| **Dominio** | {{domain}} |
| **Tipo de Tarefa** | {{task_type}} |
| **Complexidade** | {{complexity}} |
| **Urgencia** | {{urgency}} |
| **Outputs Esperados** | {{expected_outputs}} |

---

## Squad Selecionado

| Campo | Valor |
|-------|-------|
| **Squad** | {{squad_name}} |
| **Score de Match** | {{match_score}} |
| **Chief** | {{squad_chief}} |
| **Max Agentes** | {{max_agents}} |

---

## Padrao de Equipe

### Padrao Selecionado: {{pattern_name}}

| Campo | Valor |
|-------|-------|
| **Padrao** | {{pattern_name}} |
| **Justificativa** | {{pattern_justification}} |
| **Comunicacao** | {{communication_flow}} |
| **Paralelismo** | {{parallelism_level}} |

### Por que este padrao?
```
{{pattern_reasoning}}
```

---

## Agentes da Equipe

### Composicao

| # | Agente | Papel | Modelo | Tarefas Estimadas | Justificativa do Modelo |
|---|--------|-------|--------|-------------------|------------------------|
| 1 | {{agent_1_name}} | {{agent_1_role}} | {{agent_1_model}} | {{agent_1_tasks_count}} | {{agent_1_model_reason}} |
| 2 | {{agent_2_name}} | {{agent_2_role}} | {{agent_2_model}} | {{agent_2_tasks_count}} | {{agent_2_model_reason}} |
| 3 | {{agent_3_name}} | {{agent_3_role}} | {{agent_3_model}} | {{agent_3_tasks_count}} | {{agent_3_model_reason}} |
| 4 | {{agent_4_name}} | {{agent_4_role}} | {{agent_4_model}} | {{agent_4_tasks_count}} | {{agent_4_model_reason}} |

### Detalhamento por Agente

#### {{agent_1_name}} ({{agent_1_role}})
- **Modelo:** {{agent_1_model}}
- **Contexto:** {{agent_1_context}}
- **Tarefas:**
  1. {{agent_1_task_1}}
  2. {{agent_1_task_2}}

#### {{agent_2_name}} ({{agent_2_role}})
- **Modelo:** {{agent_2_model}}
- **Contexto:** {{agent_2_context}}
- **Tarefas:**
  1. {{agent_2_task_1}}
  2. {{agent_2_task_2}}

---

## Dependencias de Tarefas

### Diagrama de Dependencias

```
{{dependency_diagram}}

Exemplo:
  [Pesquisa] ──→ [Briefing] ──┬──→ [Thumbnail 1]
                               ├──→ [Thumbnail 2]
                               └──→ [Thumbnail 3]

Legenda:
  ──→  Depende de (sequencial)
  ┬──→ Fork (paralelo)
```

### Tabela de Dependencias

| Task ID | Tarefa | Agente | Depende de | Tipo |
|---------|--------|--------|------------|------|
| T1 | {{task_1}} | {{task_1_agent}} | - | Inicial |
| T2 | {{task_2}} | {{task_2_agent}} | T1 | Sequencial |
| T3 | {{task_3}} | {{task_3_agent}} | T2 | Paralelo |
| T4 | {{task_4}} | {{task_4_agent}} | T2 | Paralelo |
| T5 | {{task_5}} | {{task_5_agent}} | T3, T4 | Convergencia |

### Fases de Execucao

| Fase | Tarefas | Paralelismo | Agentes Ativos |
|------|---------|-------------|----------------|
| 1 | T1 | Nenhum | 1 |
| 2 | T2 | Nenhum | 1 |
| 3 | T3, T4 | 2 tarefas paralelas | 2 |
| 4 | T5 | Nenhum | 1 |

---

## Estimativa de Recursos

### Modelos Utilizados

| Modelo | Agentes | Tarefas | Custo Relativo |
|--------|---------|---------|----------------|
| opus | {{opus_agents}} | {{opus_tasks}} | {{opus_cost}} |
| sonnet | {{sonnet_agents}} | {{sonnet_tasks}} | {{sonnet_cost}} |
| haiku | {{haiku_agents}} | {{haiku_tasks}} | {{haiku_cost}} |
| **Total** | **{{total_agents}}** | **{{total_tasks}}** | **{{total_cost_relative}}** |

### Estimativa de Tokens

| Categoria | Estimativa |
|-----------|-----------|
| **Input tokens** | ~{{estimated_input_tokens}} |
| **Output tokens** | ~{{estimated_output_tokens}} |
| **Custo relativo** | {{cost_category}} (baixo/medio/alto) |

---

## Fila Multi-Squad

> Secao presente apenas quando a demanda requer execucao de multiplos squads

### Ordem de Execucao

| # | Squad | Padrao | Agentes | Recebe de | Passa para |
|---|-------|--------|---------|-----------|-----------|
| 1 | {{queue_squad_1}} | {{queue_pattern_1}} | {{queue_agents_1}} | - | Squad 2 |
| 2 | {{queue_squad_2}} | {{queue_pattern_2}} | {{queue_agents_2}} | Squad 1 | Squad 3 |
| 3 | {{queue_squad_3}} | {{queue_pattern_3}} | {{queue_agents_3}} | Squad 2 | - |

### Handoff Points

| De | Para | Dados Transferidos |
|----|------|--------------------|
| {{handoff_from_1}} | {{handoff_to_1}} | {{handoff_data_1}} |
| {{handoff_from_2}} | {{handoff_to_2}} | {{handoff_data_2}} |

---

## Plano de Execucao por Fases (Staged Execution)

> Secao presente apenas quando multi-squad com stage gates habilitado (2+ squads)

### Visao Geral dos Stages

```
{{#each stages}}
Stage {{number}}: {{name}}
  Squads: {{squad_list}}
  Gate: {{gate_description}}
{{/each}}

Diagrama:
  [Stage 1: {{stage_1_name}}] ──Gate 1──→ [Stage 2: {{stage_2_name}}] ──Gate 2──→ ... ──Gate N──→ [Consolidacao]
```

### Tabela de Stages

| Stage | Nome | Squads | Gate | Criterios de Aceite |
|-------|------|--------|------|---------------------|
{{#each stages}}
| {{number}} | {{name}} | {{squad_names}} | Gate {{number}}: {{gate_name}} | {{acceptance_criteria}} |
{{/each}}

### Dependencias entre Stages

```
{{stage_dependency_diagram}}

Exemplo:
  [Stage 1: Pesquisa] ──→ [Stage 2: Copy + Design] ──→ [Stage 3: Assets] ──→ [Stage 4: Dev]
       |                        |                            |                      |
    Gate 1                   Gate 2                       Gate 3               Gate Final
  (Revisar pesquisa)    (Revisar copy+tokens)       (Revisar assets)      (Pagina entregue)
```

---

## Plano por Squad (Consulta ao Chief)

> Para cada squad envolvido, o Maestro consulta a config do squad e gera um chief report

{{#each squads}}
### {{squad_number}}. {{squad_name}} (Stage {{stage_number}})

| Campo | Valor |
|-------|-------|
| **Squad ID** | {{squad_id}} |
| **Chief** | {{chief_name}} |
| **Dominio** | {{domain}} |
| **Stage** | {{stage_number}} - {{stage_name}} |

#### Agentes Selecionados

| Agente | Role | Modelo | Tasks | Justificativa |
|--------|------|--------|-------|---------------|
{{#each agents}}
| {{name}} | {{role}} | {{model}} | {{task_count}} | {{justification}} |
{{/each}}

#### Tarefas Planejadas

| Task | Agente | Depende de | Inputs | Outputs |
|------|--------|------------|--------|---------|
{{#each tasks}}
| {{name}} | {{agent}} | {{depends_on}} | {{inputs}} | {{outputs}} |
{{/each}}

#### Custo Estimado do Squad

| Modelo | Tasks | Custo Relativo |
|--------|-------|----------------|
{{#each cost_breakdown}}
| {{model}} | {{tasks}} | {{cost}} |
{{/each}}
| **Total** | **{{total_tasks}}** | **{{total_cost}}** |

---
{{/each}}

## Gates de Aprovacao

> Em cada gate entre stages, o usuario decide se avanca, revisa ou modifica

### Opcoes em cada Gate

| Opcao | Descricao |
|-------|-----------|
| **1. Aprovar** | Aceitar entregas do stage e avancar para o proximo |
| **2. Solicitar Revisoes** | Pedir que squad(s) ajustem entregas especificas |
| **3. Modificar Plano** | Alterar stages seguintes (adicionar/remover squads, reordenar) |
| **4. Pausar** | Salvar progresso e pausar execucao (retomavel) |
| **5. Cancelar** | Cancelar execucao restante (outputs anteriores mantidos) |

### Criterios por Gate

{{#each gates}}
#### Gate {{number}}: {{name}}
- **Apos Stage:** {{stage_number}}
- **Criterios de aceite:**
{{#each criteria}}
  - [ ] {{criterion}}
{{/each}}
- **Preview proximo stage:** {{next_stage_preview}}
{{/each}}

---

## Aprovacao

### Resumo para Aprovacao

```
Squad: {{squad_name}}
Padrao: {{pattern_name}}
Agentes: {{total_agents}}
Tarefas: {{total_tasks}}
Custo: {{cost_category}}
{{#if multi_squad}}
Multi-Squad: {{queue_count}} squads em sequencia
{{/if}}
{{#if staged}}
Stages: {{total_stages}} stages com {{total_gates}} gates de aprovacao
Estrutura: {{stage_summary}}
{{/if}}
```

### Opcoes

{{#if staged}}
1. **Aprovar Plano Completo** - Executar todos os stages com gates de aprovacao entre cada um
2. **Aprovar Apenas Stage 1** - Executar primeiro stage e revisar plano antes de continuar
3. **Modificar Plano** - Ajustar stages, squads, agentes ou modelos antes de executar
4. **Cancelar** - Descartar plano e nao executar
{{else}}
1. **Aprovar e Executar** - Spawnar equipe conforme planejado
2. **Modificar Plano** - Ajustar agentes, modelos ou tarefas antes de executar
3. **Cancelar** - Descartar plano e nao executar
{{/if}}

> Aguardando decisao do usuario...

---

**Gerado por:** Team Coordinator v{{version}}
**Timestamp:** {{timestamp}}
