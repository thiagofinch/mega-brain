---
task: execute-team
name: 'Task: Executar Time de Agentes'
version: "3.1.1"
category: operations
difficulty: intermediate
responsavel: '@dag-architect'
responsavel_type: Agent
atomic_layer: Molecule
elicit: false
estimated_time: 30s-10min
model: sonnet
Entrada:
- campo: brief
  tipo: markdown
  obrigatorio: true
  default: null
Saida:
- campo: deliverable
  tipo: markdown
pre_condition: Demand received with target squad/pattern resolvable from registry
post_condition: Agent Team spawned and ran to completion with consolidated output and team logs persisted
performance:
  error_handling: graceful with fallback + retry
domain: tactical
task_id: execute-team
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

# Task: Execute Team

## Metadata
```yaml
id: execute-team
name: Executar Time de Agentes
version: 1.0.0
executor: team-coordinator
workflow: executar-com-team
estimated_time: 30s-10min
```

## Purpose

Receber uma demanda, analisar sua complexidade, planejar e criar um time de agentes (Agent Team) para executar a solicitacao em paralelo usando Claude Agent SDK tools (TeamCreate, TaskCreate, SendMessage).

---

## Input Requirements

| Campo | Tipo | Obrigatório | Exemplo |
|-------|------|-------------|---------|
| demand | string | Sim | "Criar landing page completa com copy e design" |
| squad_target | string | Não | "copywriting" |
| team_pattern | string | Não | "pipeline" / "parallel" / "specialist" |
| max_agents | number | Não | 5 |

## Trigger

```yaml
trigger:
  type: command
  event: "*execute-team"
  sources:
    - "Input do usuario"
    - "Maestro orchestration"
    - "Outro squad via SendMessage"
```

---

## Execution Flow

### Phase 1: Demand Analysis (2-5s)

**Task 1.1: Classify Intent**
- Executor: @classificador-intenção
- Input: demand, contexto_usuario
- Output: structured intent with domain, complexity, urgency
- Tempo: ~2s

```yaml
output_analysis:
  domain: "marketing | development | operations | creative | analytics"
  task_type: "create | analyze | execute | review | optimize"
  complexity: "low | medium | high | critical"
  urgency: "low | normal | high | critical"
  keywords: ["keyword1", "keyword2"]
  confidence: 0.XX
  summary: "Brief summary of demand"
  estimated_agents: N
  multi_squad: false
```

**Task 1.2: Identify Target Squad**
- Executor: @roteador
- Input: intent analysis, SQUAD-REGISTRY
- Output: target squad(s) and available agents
- Tempo: ~1s

```yaml
output_target:
  primary_squad: "squad-name"
  secondary_squads: []  # if multi-squad needed
  available_agents:
    - name: "agent-name"
      role: "specialist-role"
      model_tier: "opus | sonnet | haiku"
```

**Task 1.3: Determine Complexity**
- Executor: @team-coordinator
- Input: intent, agent count, task dependencies
- Output: team pattern recommendation

```yaml
output_complexity:
  pattern: "pipeline | parallel | specialist | swarm"
  reason: "Why this pattern was chosen"
  estimated_tasks: N
  estimated_duration: "Xmin"
  parallel_potential: 0.XX  # 0-1, how parallelizable
```

### Phase 2: Team Planning (3-5s)

**Task 2.1: Select Team Pattern**
- Executor: @team-coordinator
- Input: complexity analysis, TEAM-PATTERNS reference
- Output: selected pattern with configuration

```yaml
team_patterns:
  pipeline:
    description: "Sequential chain, output of A feeds B"
    use_when: "Tasks have strict dependencies"
    agents: 2-4
  parallel:
    description: "Independent work streams merged at end"
    use_when: "Tasks are independent"
    agents: 2-6
  specialist:
    description: "Lead + specialists for specific subtasks"
    use_when: "Complex task requiring diverse expertise"
    agents: 3-5
  swarm:
    description: "Dynamic task claiming from shared pool"
    use_when: "Many similar subtasks"
    agents: 3-8
  battle-royale:
    description: "Adversarial competition with voting, debate, and board review"
    use_when: "Maximum quality needed, squad has 6+ agents, high-stakes deliverable"
    agents: 6-17
    reference: "TEAM-PATTERNS.md#pattern-6-battle-royale"
    detection: "Auto-detected when squad.yaml has battle.enabled=true"
```

**Battle Royale Auto-Detection:**

When `*execute-team` is invoked with `--pattern battle` or when the target squad has `battle.enabled: true` in its `squad.yaml`, the coordinator MUST:

1. Load the squad's `battle` config from `squad.yaml`
2. Load the specialized workflow from `battle.workflow_ref`
3. Use the 5-phase Battle sequence instead of the standard execution flow
4. Report progress per phase: "Fase 1/5 — Briefing", "Fase 2/5 — Produção", etc.
5. Support `--type {battle-type}` to select which battle configuration to use

```yaml
# Battle-specific execution command
trigger:
  command: "*execute-team --pattern battle --squad {squad} --type {type}"
  # OR auto-detected from squad config
  auto_detect:
    condition: "squad.yaml → battle.enabled == true"
    pattern_override: "battle-royale"
    workflow_override: "squad.yaml → battle.workflow_ref"
```

See `TEAM-PATTERNS.md#pattern-6-battle-royale` for full implementation details and `BATTLE-CONFIG-SCHEMA.md` for configuration reference.

**Task 2.2: Choose Agents and Assign Models**
- Executor: @team-coordinator
- Input: pattern, squad agents, MODEL-STRATEGY
- Output: agent roster with model assignments

```yaml
model_strategy:
  team_lead:
    model: "opus"
    reason: "Complex coordination and synthesis"
  specialist:
    model: "sonnet"
    reason: "Balanced capability for focused tasks"
  worker:
    model: "haiku"
    reason: "Fast execution for well-defined subtasks"
```

**Task 2.3: Create Execution Plan**
- Executor: @team-coordinator
- Input: agents, pattern, demand breakdown
- Output: full execution plan with tasks and dependencies

```yaml
execution_plan:
  team_name: "team-{squad}-{timestamp}"
  pattern: "parallel"
  agents:
    - id: "agent-1"
      name: "copywriter"
      role: "Headline and body copy"
      model: "sonnet"
      tasks: ["task-1", "task-2"]
    - id: "agent-2"
      name: "designer"
      role: "Visual layout and assets"
      model: "sonnet"
      tasks: ["task-3", "task-4"]
  tasks:
    - id: "task-1"
      subject: "Write headline variations"
      assigned_to: "agent-1"
      blocked_by: []
    - id: "task-2"
      subject: "Write body copy"
      assigned_to: "agent-1"
      blocked_by: ["task-1"]
    - id: "task-3"
      subject: "Create visual mockup"
      assigned_to: "agent-2"
      blocked_by: []
    - id: "task-4"
      subject: "Final design composition"
      assigned_to: "agent-2"
      blocked_by: ["task-3", "task-2"]
  dependencies:
    task-2: ["task-1"]
    task-4: ["task-3", "task-2"]
```

### Phase 3: Team Spawning (5-15s)

**Task 3.1: Create Team**
- Executor: @team-coordinator
- Tool: TeamCreate
- Input: team_name, agents list

```yaml
team_create:
  action: "TeamCreate"
  params:
    name: "team-{squad}-{timestamp}"
    description: "Team for: {demand_summary}"
```

**Task 3.2: Spawn Agent Instances**
- Executor: @team-coordinator
- Tool: Task (subagent spawn) for each agent
- Input: agent persona, model, initial instructions

```yaml
spawn_sequence:
  for_each_agent:
    - action: "Task tool (subagent)"
      params:
        description: |
          You are {agent.name}, a {agent.role} specialist.
          Your mission: {agent.task_description}
          Squad context: {squad.context}
          Report results via TaskUpdate when complete.
        subagent_type: "agent"
        model: "{agent.model}"
```

**Task 3.3: Create Work Items**
- Executor: @team-coordinator
- Tool: TaskCreate for each work item
- Input: execution plan tasks

```yaml
task_creation:
  for_each_task:
    - action: "TaskCreate"
      params:
        subject: "{task.subject}"
        description: "{task.full_description}"
        activeForm: "{task.active_form}"
    - action: "TaskUpdate"
      params:
        taskId: "{created_task_id}"
        addBlockedBy: "{task.blocked_by}"
        owner: "{task.assigned_to}"
```

### Phase 4: Monitoring (continuous)

**Task 4.1: Poll Task Progress**
- Executor: @team-coordinator
- Tool: TaskList (periodic)
- Frequency: every 10-30s depending on complexity

```yaml
monitoring:
  poll_interval: "10s"  # for high urgency, 30s for normal
  check:
    - all_tasks_status: "pending | in_progress | completed"
    - blocked_tasks: "any tasks stuck in blocked state"
    - idle_agents: "agents with no active tasks"
  thresholds:
    idle_warning: "60s"    # agent idle for 60s
    stall_warning: "120s"  # task in_progress for 120s without update
    max_duration: "600s"   # total team execution limit
```

**Task 4.2: Handle Issues**
- Executor: @team-coordinator
- Tool: SendMessage for alerts, TaskUpdate for reassignment

```yaml
issue_handling:
  idle_agent:
    action: "SendMessage to agent asking for status"
    escalate_after: "2 attempts"
  stalled_task:
    action: "TaskUpdate to reassign, or SendMessage to unblock"
    escalate_after: "1 reassignment"
  blocked_chain:
    action: "Identify blocker, prioritize resolution"
    escalate_after: "notify user if critical path"
```

### Phase 5: Synthesis (5-15s)

**Task 5.1: Collect Outputs**
- Executor: @team-coordinator
- Input: completed tasks from all agents
- Output: raw collected results

```yaml
collection:
  for_each_completed_task:
    - read: "task output from TaskGet"
    - validate: "output meets quality criteria"
    - store: "in synthesis buffer"
  wait_for: "all tasks completed or timeout"
```

**Task 5.2: Merge Results**
- Executor: @team-coordinator (opus model)
- Input: all agent outputs
- Output: unified deliverable

```yaml
merge_strategy:
  pipeline: "Chain outputs sequentially"
  parallel: "Combine independent outputs into unified result"
  specialist: "Lead integrates specialist contributions"
  swarm: "Aggregate and deduplicate results"
```

**Task 5.3: Quality Check**
- Executor: @team-coordinator
- Input: merged result
- Output: quality assessment

```yaml
quality_check:
  completeness: "All requested items delivered"
  consistency: "No contradictions between agent outputs"
  quality: "Meets minimum quality threshold"
  action_if_fail: "Request revision from specific agent"
```

### Phase 6: Shutdown (3-5s)

**Task 6.1: Shutdown Agents**
- Executor: @team-coordinator
- Tool: SendMessage (shutdown_request) to each agent

```yaml
shutdown:
  for_each_agent:
    - action: "SendMessage"
      params:
        type: "shutdown_request"
        recipient: "{agent.name}"
        content: "Task complete. Shutting down team."
    - wait_for: "shutdown_response (approve)"
    - timeout: "30s, then force terminate"
```

**Task 6.2: Save Context**
- Executor: @team-coordinator
- Output: session artifacts saved

```yaml
save_context:
  path: ".data/team-outputs/{session-id}/"
  files:
    - "execution-plan.yaml"
    - "agent-outputs/"
    - "merged-result.md"
    - "metrics.yaml"
```

**Task 6.3: Cleanup**
- Executor: @team-coordinator
- Tool: TeamDelete

```yaml
cleanup:
  action: "TeamDelete"
  params:
    team_id: "{team_id}"
  then: "Present final summary to user"
```

---

## Output Structure

```yaml
resultado:
  status: "completed | partial | failed"

  team:
    name: "team-copywriting-20260206"
    pattern: "parallel"
    agents_used: 3
    tasks_completed: 5
    tasks_total: 5
    duration: "45s"

  deliverable:
    summary: "Description of what was produced"
    outputs:
      - agent: "copywriter"
        result: "..."
      - agent: "designer"
        result: "..."
    merged_result: "Final unified output"

  metrics:
    total_time: "45s"
    agent_utilization: 0.85
    parallel_efficiency: 0.72
    quality_score: 0.90
    model_costs:
      opus: 1
      sonnet: 2
      haiku: 0

  session_id: "uuid"
  artifacts_path: ".data/team-outputs/{session-id}/"
```

---

## Quality Gates

### Gate 1: Demand Analysis
- [ ] Intent classified with confidence >= 0.70
- [ ] Target squad identified
- [ ] Complexity assessed
- [ ] Team pattern selected

### Gate 2: Team Planning
- [ ] Agents selected from squad roster
- [ ] Models assigned per MODEL-STRATEGY
- [ ] Execution plan has no circular dependencies
- [ ] All tasks have assigned owners

### Gate 3: Team Spawning
- [ ] TeamCreate successful
- [ ] All agents spawned without errors
- [ ] All TaskCreate items created with correct dependencies
- [ ] Agents acknowledged their assignments

### Gate 4: Monitoring
- [ ] No agents idle beyond threshold
- [ ] No tasks stalled beyond threshold
- [ ] Blockers detected and addressed
- [ ] Progress reported at intervals

### Gate 5: Synthesis
- [ ] All agent outputs collected
- [ ] Results merged without conflicts
- [ ] Quality check passed
- [ ] Deliverable is complete

### Gate 6: Shutdown
- [ ] All agents received shutdown_request
- [ ] All agents confirmed shutdown
- [ ] Context saved to disk
- [ ] TeamDelete executed
- [ ] Final summary presented to user

---

## Success Metrics

| Métrica | Alvo | Descrição |
|---------|------|-----------|
| Spawn time | < 15s | Time to create team and spawn all agents |
| Task completion | > 95% | Percentage of tasks completed successfully |
| Agent utilization | > 80% | Time agents spent actively working vs idle |
| Parallel efficiency | > 70% | Actual speedup vs sequential execution |
| Quality score | > 85% | Merged result quality assessment |
| Total duration | < 5min | End-to-end for medium complexity demands |

---

## Validation

```yaml
validation:
  schema_version: 1
  when: "post"
  checks:
    - id: "has-demand-classification"
      type: "assertion"
      expression: "output.content && (output.content.includes('domain:') || output.content.includes('task_type:') || output.content.includes('complexity:'))"
      message: "A execução do time deve conter classificação da demanda (domain, task_type, complexity)"
      severity: "CRITICAL"

    - id: "has-team-pattern"
      type: "assertion"
      expression: "output.content && (output.content.includes('pattern:') || output.content.includes('pipeline') || output.content.includes('parallel') || output.content.includes('specialist'))"
      message: "A execução deve conter seleção do padrão de time (pipeline, parallel, specialist, swarm)"
      severity: "CRITICAL"

    - id: "has-squad-assignment"
      type: "assertion"
      expression: "output.content && (output.content.includes('primary_squad:') || output.content.includes('squad:') || output.content.includes('agents_used'))"
      message: "A execução deve conter atribuição de squad e agentes utilizados"
      severity: "HIGH"
  on_fail: "retry"
  max_retries: 2
  escalate_to: "@megabrain-master"
```

## Rollback Points

```yaml
rollback:
  spawn_fails:
    condition: "TeamCreate or agent spawn fails"
    action: "Fallback to conceptual *execute (single-agent mode)"
    message: "Team creation failed. Executing in single-agent mode."

  agent_stuck:
    condition: "Agent idle or stalled beyond threshold"
    action: "Reassign task to another agent or team-coordinator"
    message: "Agent {name} unresponsive. Reassigning task."

  synthesis_incomplete:
    condition: "Not all outputs available at timeout"
    action: "Partial delivery with available results"
    message: "Delivering partial results. {N} of {M} tasks completed."

  quality_fail:
    condition: "Merged result fails quality check"
    action: "Request revision from specific agent(s)"
    message: "Quality below threshold. Requesting revision."

  total_timeout:
    condition: "Team exceeds max_duration"
    action: "Force shutdown, deliver whatever is available"
    message: "Time limit reached. Delivering available results."
```

---

## Example

### Input
```yaml
demand: "Criar 3 variações de headline e body copy para landing page de curso de massagem"
squad_target: "copywriting"
team_pattern: null  # auto-detect
max_agents: 3
```

### Processing
```yaml
# Phase 1: Demand Analysis
analysis:
  domain: "marketing"
  task_type: "create"
  complexity: "medium"
  urgency: "normal"
  keywords: ["headline", "body copy", "landing page", "curso", "massagem"]
  confidence: 0.91
  estimated_agents: 2
  multi_squad: false

target:
  primary_squad: "copywriting"
  available_agents:
    - name: "headline-specialist"
      role: "Headlines and hooks"
      model_tier: "sonnet"
    - name: "body-copy-writer"
      role: "Long-form persuasive copy"
      model_tier: "sonnet"

# Phase 2: Team Planning
plan:
  pattern: "pipeline"
  reason: "Body copy depends on headline direction"
  agents:
    - id: "agent-1"
      name: "headline-specialist"
      model: "sonnet"
      tasks: ["write-headlines"]
    - id: "agent-2"
      name: "body-copy-writer"
      model: "sonnet"
      tasks: ["write-body-copy"]
  tasks:
    - id: "write-headlines"
      subject: "Create 3 headline variations for massage course LP"
      assigned_to: "agent-1"
      blocked_by: []
    - id: "write-body-copy"
      subject: "Write body copy for each headline variation"
      assigned_to: "agent-2"
      blocked_by: ["write-headlines"]

# Phase 3-6: Execution
execution:
  team_created: "team-copywriting-20260206-1430"
  agents_spawned: 2
  tasks_created: 2
  duration: "32s"
```

### Output
```yaml
resultado:
  status: "completed"
  team:
    name: "team-copywriting-20260206-1430"
    pattern: "pipeline"
    agents_used: 2
    tasks_completed: 2
    tasks_total: 2
    duration: "32s"
  deliverable:
    summary: "3 headline variations with matching body copy for massage course LP"
    outputs:
      - agent: "headline-specialist"
        result: "3 headlines: (A) Transforme Suas Mãos em... (B) Curso Profissional... (C) Domine a Arte..."
      - agent: "body-copy-writer"
        result: "3 body copy variations matching each headline approach"
    merged_result: "Complete LP copy package with 3 variations"
  metrics:
    total_time: "32s"
    agent_utilization: 0.88
    quality_score: 0.92
```
