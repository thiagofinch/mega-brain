---
task: team-status
name: 'Task: Team Status'
version: "3.1.1"
category: operations
difficulty: intermediate
responsavel: '@dag-architect'
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
pre_condition: Active team_id provided or inferable from session
post_condition: Team status report emitted with per-agent state, task progress, and summary metrics
performance:
  error_handling: graceful with fallback + retry
domain: tactical
task_id: team-status
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

# Task: Team Status

## Metadata
```yaml
id: team-status
name: Consultar Status do Time
version: 1.0.0
executor: team-coordinator
workflow: executar-com-team
estimated_time: 2-5s
```

## Purpose

Consultar o estado atual de um time de agentes em execucao, coletando status de cada agente e tarefa, e apresentando um relatorio formatado ao usuario.

---

## Input Requirements

| Campo | Tipo | Obrigatorio | Exemplo |
|-------|------|-------------|---------|
| team_id | string | Nao | "team-copywriting-20260206" |
| verbose | boolean | Nao | true |

## Trigger

```yaml
trigger:
  type: command
  event: "*team-status"
  sources:
    - "Input do usuario"
    - "Maestro monitoring"
    - "Periodic auto-check"
```

---

## Execution Flow

### Phase 1: Gather Data (1-2s)

**Task 1.1: Read Task List**
- Executor: @team-coordinator
- Tool: TaskList
- Output: all tasks with status, owner, blockedBy

```yaml
task_list_query:
  action: "TaskList"
  extract:
    - task_id
    - subject
    - status: "pending | in_progress | completed"
    - owner: "agent name or empty"
    - blockedBy: "list of blocking task IDs"
```

**Task 1.2: Determine Agent States**
- Executor: @team-coordinator
- Input: task list data
- Output: per-agent state summary

```yaml
agent_states:
  for_each_agent:
    derive_from_tasks:
      idle: "No in_progress tasks and has pending tasks"
      active: "Has at least one in_progress task"
      completed: "All assigned tasks completed"
      blocked: "All pending tasks are blocked by other tasks"
```

### Phase 2: Analyze Progress (1-2s)

**Task 2.1: Calculate Metrics**
- Executor: @team-coordinator
- Input: task list, agent states
- Output: progress metrics

```yaml
metrics:
  tasks_completed: N
  tasks_in_progress: N
  tasks_pending: N
  tasks_blocked: N
  tasks_total: N
  completion_percentage: "XX%"
  agents_active: N
  agents_idle: N
  agents_completed: N
  agents_total: N
  blockers:
    - task_id: "X"
      subject: "..."
      blocking: ["task-Y", "task-Z"]
  estimated_remaining: "Xmin"
```

### Phase 3: Format Report (1s)

**Task 3.1: Generate Status Report**
- Executor: @team-coordinator
- Template: team-status-report-tmpl.md
- Output: formatted report

```yaml
report_format:
  header:
    team_name: "team-copywriting-20260206"
    pattern: "parallel"
    elapsed_time: "1m 23s"
    status: "running | completing | stalled"
  progress_bar: "[=========>    ] 67% (4/6 tasks)"
  agents_table:
    columns: ["Agent", "Status", "Current Task", "Completed"]
    rows:
      - ["copywriter", "active", "Writing body copy", "2/3"]
      - ["designer", "idle", "-", "1/2"]
  blockers_section:
    - "Task 'Final design' blocked by 'Write body copy'"
  timeline:
    estimated_completion: "~2min remaining"
```

---

## Output Structure

```yaml
resultado:
  status: "reported"

  team:
    name: "team-copywriting-20260206"
    pattern: "parallel"
    elapsed: "1m 23s"
    state: "running | completing | stalled | completed"

  progress:
    completed: 4
    in_progress: 1
    pending: 1
    blocked: 0
    total: 6
    percentage: 67

  agents:
    - name: "copywriter"
      state: "active"
      current_task: "Writing body copy"
      tasks_done: 2
      tasks_total: 3
    - name: "designer"
      state: "idle"
      current_task: null
      tasks_done: 1
      tasks_total: 2

  blockers: []

  estimated_remaining: "~2min"

  report_text: "Formatted markdown report for display"
```

---

## Quality Gates

### Gate 1: Data Collection
- [ ] TaskList returned successfully
- [ ] All tasks accounted for
- [ ] Agent states derived correctly

### Gate 2: Report
- [ ] Progress metrics accurate
- [ ] Blockers identified
- [ ] Report formatted and readable

---

## Success Metrics

| Metrica | Alvo | Descricao |
|---------|------|-----------|
| Response time | < 3s | Time to generate status report |
| Accuracy | 100% | Task counts match actual |
| Blocker detection | 100% | All blocked tasks identified |

---

## Rollback Points

```yaml
rollback:
  tasklist_fails:
    action: "Report error, suggest user check team exists"
    message: "Could not retrieve task list. Team may have been shut down."

  no_active_team:
    action: "Inform user no team is running"
    message: "No active team found. Use *execute-team to start one."
```

---

## Example

### Input
```yaml
team_id: null  # use current active team
verbose: true
```

### Processing
```yaml
# Phase 1: TaskList returns
tasks:
  - id: "1"
    subject: "Write headline variations"
    status: "completed"
    owner: "copywriter"
  - id: "2"
    subject: "Write body copy"
    status: "in_progress"
    owner: "copywriter"
  - id: "3"
    subject: "Create visual mockup"
    status: "completed"
    owner: "designer"
  - id: "4"
    subject: "Final design composition"
    status: "pending"
    owner: "designer"
    blockedBy: ["2"]

# Phase 2: Derive states
agents:
  - copywriter: "active" (task 2 in_progress)
  - designer: "blocked" (task 4 blocked by task 2)
```

### Output
```markdown
## Team Status: team-copywriting-20260206

**Pattern:** pipeline | **Elapsed:** 1m 23s | **State:** running

### Progress
[===========>      ] 50% (2/4 tasks completed)

### Agents
| Agent | Status | Current Task | Progress |
|-------|--------|-------------|----------|
| copywriter | active | Write body copy | 1/2 |
| designer | blocked | - | 1/2 |

### Blockers
- "Final design composition" waiting on "Write body copy" (copywriter)

### Estimated Completion
~2 minutes remaining
```

## Integration

- **Squad:** orquestrador-global
- **Upstream:** *definir tasks que alimentam esta*
- **Downstream:** *definir tasks que esta alimenta*
