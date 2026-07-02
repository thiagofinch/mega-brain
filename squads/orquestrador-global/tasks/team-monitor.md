---
task: team-monitor
name: 'Task: Team Monitor'
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
pre_condition: Team spawned and running with active team_id
post_condition: Monitoring loop completed with health report, alerts triggered, and corrective actions logged
performance:
  error_handling: graceful with fallback + retry
domain: tactical
task_id: team-monitor
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

# Task: Team Monitor

## Metadata
```yaml
id: team-monitor
name: Monitoramento Continuo do Time
version: 1.0.0
executor: team-coordinator
workflow: executar-com-team
estimated_time: continuous
```

## Purpose

Observar continuamente um time de agentes em execucao, detectando problemas como agentes ociosos, tarefas travadas e bloqueios em cadeia, alertando o lider e tomando acoes corretivas automaticas quando thresholds sao excedidos.

---

## Input Requirements

| Campo | Tipo | Obrigatorio | Exemplo |
|-------|------|-------------|---------|
| team_id | string | Nao | "team-copywriting-20260206" |
| poll_interval | number | Nao | 15 (seconds) |
| idle_threshold | number | Nao | 60 (seconds) |
| stall_threshold | number | Nao | 120 (seconds) |
| max_duration | number | Nao | 600 (seconds) |

## Trigger

```yaml
trigger:
  type: automatic
  event: "Team spawned and running"
  sources:
    - "execute-team Phase 4"
    - "Manual *team-monitor command"
```

---

## Execution Flow

### Phase 1: Initialize Monitor (1-2s)

**Task 1.1: Load Team Configuration**
- Executor: @team-coordinator
- Input: team_id or current active team
- Output: team config with agents, tasks, thresholds

```yaml
monitor_config:
  team_id: "team-copywriting-20260206"
  agents: ["copywriter", "designer"]
  poll_interval: 15  # seconds
  thresholds:
    idle_warning: 60      # agent idle for 60s -> warning
    idle_critical: 120    # agent idle for 120s -> auto-reassign
    stall_warning: 120    # task stalled for 120s -> alert
    stall_critical: 300   # task stalled for 300s -> escalate
    max_duration: 600     # total team time limit
  counters:
    warnings_sent: 0
    reassignments: 0
    escalations: 0
```

### Phase 2: Monitoring Loop (continuous)

**Task 2.1: Poll Task Progress**
- Executor: @team-coordinator
- Tool: TaskList
- Frequency: every poll_interval seconds

```yaml
poll_cycle:
  action: "TaskList"
  on_each_poll:
    - record_timestamp: "current time"
    - compare_with_previous: "detect changes since last poll"
    - check_agent_activity: "map tasks to agents"
    - evaluate_thresholds: "check against configured limits"
```

**Task 2.2: Detect Idle Agents**
- Executor: @team-coordinator
- Input: task list, agent activity history
- Detection: agent has no in_progress tasks and has pending tasks available

```yaml
idle_detection:
  condition: |
    agent.current_tasks.in_progress == 0
    AND agent.assigned_tasks.pending > 0
    AND time_since_last_activity > idle_threshold
  levels:
    warning:
      threshold: 60s
      action: "SendMessage to agent asking for status"
      message: "You have pending tasks but appear idle. Status update?"
    critical:
      threshold: 120s
      action: "Auto-reassign pending tasks to another available agent"
      log: "Agent {name} idle for {duration}. Reassigning tasks."
```

**Task 2.3: Detect Stalled Tasks**
- Executor: @team-coordinator
- Input: task list, task timing history
- Detection: task in in_progress state without updates for too long

```yaml
stall_detection:
  condition: |
    task.status == "in_progress"
    AND time_since_status_change > stall_threshold
  levels:
    warning:
      threshold: 120s
      action: "SendMessage to task owner asking for progress"
      message: "Task '{subject}' has been in progress for {duration}. Need help?"
    critical:
      threshold: 300s
      action: "Alert team lead, consider reassignment"
      log: "Task '{subject}' stalled for {duration}. Escalating."
```

**Task 2.4: Detect Blocked Chains**
- Executor: @team-coordinator
- Input: task dependencies, task statuses
- Detection: circular or deep dependency chains causing cascading blocks

```yaml
block_detection:
  checks:
    circular_dependency:
      condition: "Task A blocked by B, B blocked by A"
      action: "Break cycle by unblocking one task"
      severity: "critical"
    deep_chain:
      condition: "Chain of 3+ blocked tasks"
      action: "Prioritize resolution of root blocker"
      severity: "warning"
    orphaned_block:
      condition: "Task blocked by completed or deleted task"
      action: "Remove invalid blockedBy reference"
      severity: "auto-fix"
```

**Task 2.5: Check Duration Limit**
- Executor: @team-coordinator
- Input: team start time, max_duration
- Detection: team has exceeded maximum allowed execution time

```yaml
duration_check:
  condition: "elapsed_time > max_duration"
  action: "Trigger forced shutdown with partial delivery"
  warning_at: "80% of max_duration"
  message: "Team approaching time limit. {remaining}s remaining."
```

### Phase 3: Alert and Action (on-demand)

**Task 3.1: Send Alerts**
- Executor: @team-coordinator
- Tool: SendMessage
- Target: affected agent or team lead

```yaml
alert_types:
  idle_warning:
    recipient: "{idle_agent}"
    type: "message"
    content: "Status check: you appear idle. Task '{pending_task}' is waiting."
  stall_warning:
    recipient: "{task_owner}"
    type: "message"
    content: "Task '{subject}' in progress for {duration}. Report progress or blockers."
  escalation:
    recipient: "team-lead"
    type: "message"
    content: "Issue detected: {issue_description}. Action needed."
  duration_warning:
    recipient: "team-lead"
    type: "message"
    content: "Team time limit at 80%. Consider wrapping up."
```

**Task 3.2: Auto-Reassign Tasks**
- Executor: @team-coordinator
- Tool: TaskUpdate
- Condition: idle or stall threshold exceeded and auto-action enabled

```yaml
auto_reassign:
  condition: "threshold exceeded AND available_agent exists"
  steps:
    - find_available_agent: "Agent with lowest task count and not blocked"
    - action: "TaskUpdate"
      params:
        taskId: "{stalled_task_id}"
        owner: "{new_agent_name}"
    - notify_original: "SendMessage to original owner"
    - notify_new: "SendMessage to new owner with task context"
    - log: "Reassigned task '{subject}' from {old} to {new}"
```

### Phase 4: Exit Conditions

```yaml
exit_conditions:
  all_complete:
    condition: "All tasks status == completed"
    action: "Stop monitoring, proceed to synthesis"
    log: "All tasks completed. Monitoring ended."
  timeout:
    condition: "elapsed > max_duration"
    action: "Force stop, trigger partial delivery"
    log: "Time limit exceeded. Forcing completion."
  manual_stop:
    condition: "User issues *team-shutdown or Ctrl+C"
    action: "Clean exit, save state"
    log: "Monitoring stopped by user."
  all_failed:
    condition: "All agents idle with no completable tasks"
    action: "Escalate to user with diagnostic"
    log: "Team deadlocked. Escalating."
```

---

## Output Structure

```yaml
resultado:
  status: "monitoring | completed | timeout | escalated"

  monitoring_summary:
    total_polls: N
    duration: "Xm Xs"
    issues_detected: N
    warnings_sent: N
    auto_reassignments: N
    escalations: N

  issues_log:
    - timestamp: "..."
      type: "idle_warning | stall_warning | block_detected | duration_warning"
      agent: "agent-name"
      task: "task-subject"
      action_taken: "description"
      resolved: true | false

  final_state:
    tasks_completed: N
    tasks_remaining: N
    agents_active: N
    exit_reason: "all_complete | timeout | manual | deadlock"
```

---

## Quality Gates

### Gate 1: Monitor Active
- [ ] Poll interval configured and running
- [ ] Thresholds set appropriately
- [ ] Agent tracking initialized

### Gate 2: Detection Accuracy
- [ ] Idle agents correctly identified
- [ ] Stalled tasks correctly identified
- [ ] Blocked chains detected
- [ ] No false positives in first 3 cycles

### Gate 3: Response Actions
- [ ] Alerts sent within 5s of detection
- [ ] Auto-reassignment successful when triggered
- [ ] Escalations reach team lead

---

## Success Metrics

| Metrica | Alvo | Descricao |
|---------|------|-----------|
| Detection latency | < 1 poll cycle | Issues detected within one poll interval |
| False positive rate | < 5% | Incorrect issue detection |
| Auto-resolve rate | > 60% | Issues resolved without escalation |
| Alert delivery | 100% | All alerts successfully sent |

---

## Rollback Points

```yaml
rollback:
  monitor_crash:
    action: "Restart monitoring from current state"
    message: "Monitor restarted. Resuming observation."

  false_reassignment:
    action: "TaskUpdate to restore original owner"
    message: "Reassignment reverted. Task returned to {original_owner}."

  escalation_loop:
    condition: "Same issue escalated 3+ times"
    action: "Stop escalation, present full diagnostic to user"
    message: "Recurring issue detected. Manual intervention needed."
```

---

## Example

### Input
```yaml
team_id: "team-copywriting-20260206"
poll_interval: 15
idle_threshold: 60
stall_threshold: 120
```

### Monitoring Cycle
```yaml
# Poll 1 (t=0s)
tasks:
  - {id: "1", status: "in_progress", owner: "copywriter"}
  - {id: "2", status: "pending", owner: "copywriter", blockedBy: ["1"]}
  - {id: "3", status: "in_progress", owner: "designer"}
  - {id: "4", status: "pending", owner: "designer", blockedBy: ["2","3"]}
state: "All agents active. No issues."

# Poll 5 (t=60s)
tasks:
  - {id: "1", status: "completed", owner: "copywriter"}
  - {id: "2", status: "in_progress", owner: "copywriter"}
  - {id: "3", status: "in_progress", owner: "designer"}  # still in_progress
  - {id: "4", status: "pending", owner: "designer", blockedBy: ["2","3"]}
state: "Designer task 3 in_progress for 60s. Within threshold."

# Poll 9 (t=120s)
tasks:
  - {id: "1", status: "completed", owner: "copywriter"}
  - {id: "2", status: "completed", owner: "copywriter"}
  - {id: "3", status: "in_progress", owner: "designer"}  # 120s now
  - {id: "4", status: "pending", owner: "designer", blockedBy: ["3"]}
issue_detected:
  type: "stall_warning"
  agent: "designer"
  task: "3 - Create visual mockup"
  duration: "120s"
action_taken:
  - SendMessage to designer: "Task 'Create visual mockup' in progress for 120s. Need help?"
```

## Integration

- **Squad:** orquestrador-global
- **Upstream:** *definir tasks que alimentam esta*
- **Downstream:** *definir tasks que esta alimenta*
