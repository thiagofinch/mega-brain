---
task: team-shutdown
name: 'Task: Team Shutdown'
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
pre_condition: Active team_id with running agents and tasks
post_condition: Team gracefully terminated with final outputs collected, context saved, and resources released
performance:
  error_handling: graceful with fallback + retry
domain: tactical
task_id: team-shutdown
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

# Task: Team Shutdown

## Metadata
```yaml
id: team-shutdown
name: Encerrar Time de Agentes
version: 1.0.0
executor: team-coordinator
workflow: executar-com-team
estimated_time: 5-15s
```

## Purpose

Encerrar graciosamente um time de agentes em execucao, coletando outputs finais, salvando contexto e artefatos, e limpando recursos do time.

---

## Input Requirements

| Campo | Tipo | Obrigatorio | Exemplo |
|-------|------|-------------|---------|
| team_id | string | Nao | "team-copywriting-20260206" |
| force | boolean | Nao | false |
| save_context | boolean | Nao | true |
| reason | string | Nao | "Task complete" |

## Trigger

```yaml
trigger:
  type: command
  event: "*team-shutdown"
  sources:
    - "Input do usuario"
    - "execute-team Phase 6"
    - "team-monitor timeout"
    - "Manual intervention"
```

---

## Execution Flow

### Phase 1: Pre-Shutdown Assessment (1-2s)

**Task 1.1: Check Team State**
- Executor: @team-coordinator
- Tool: TaskList
- Output: current team state snapshot

```yaml
pre_shutdown:
  action: "TaskList"
  assess:
    tasks_completed: N
    tasks_in_progress: N
    tasks_pending: N
    agents_active: ["list"]
    agents_idle: ["list"]
    has_unsaved_work: true | false
```

**Task 1.2: Warn About In-Progress Work**
- Executor: @team-coordinator
- Condition: tasks still in_progress and force=false

```yaml
warning:
  condition: "tasks_in_progress > 0 AND force == false"
  action: "Ask user for confirmation"
  message: |
    {N} tasks still in progress:
    - {task_subjects}
    Proceed with shutdown? Outputs may be incomplete.
    Use *team-shutdown --force to force shutdown.
```

### Phase 2: Graceful Shutdown (3-10s)

**Task 2.1: Send Shutdown Requests**
- Executor: @team-coordinator
- Tool: SendMessage (shutdown_request) to each agent
- Sequence: parallel to all agents

```yaml
shutdown_requests:
  for_each_agent:
    - action: "SendMessage"
      params:
        type: "shutdown_request"
        recipient: "{agent.name}"
        content: "Team shutting down. Reason: {reason}. Please finalize and save your current work."
    - wait_for: "shutdown_response"
    - timeout: 30s
```

**Task 2.2: Handle Shutdown Responses**
- Executor: @team-coordinator
- Input: shutdown_response from each agent

```yaml
response_handling:
  approved:
    action: "Mark agent as shut down"
    log: "Agent {name} confirmed shutdown."

  rejected:
    reason_captured: true
    action_if_force_false:
      - "Log rejection reason"
      - "Notify user: Agent {name} rejected shutdown: {reason}"
      - "Ask user: force shutdown or wait?"
    action_if_force_true:
      - "Log rejection"
      - "Force terminate after 10s grace period"
      - "Log: Agent {name} force-terminated."

  timeout:
    action: "Treat as unresponsive"
    log: "Agent {name} did not respond to shutdown. Force terminating."
    force_terminate: true
```

**Task 2.3: Collect Final Outputs**
- Executor: @team-coordinator
- Tool: TaskGet for each completed task
- Output: all agent deliverables

```yaml
output_collection:
  for_each_task:
    - action: "TaskGet"
      params:
        taskId: "{task.id}"
    - extract: "task output, metadata, completion status"
    - store: "in session output buffer"
  aggregate:
    completed_outputs: ["..."]
    partial_outputs: ["..."]  # from in_progress tasks
    pending_tasks: ["..."]    # never started
```

### Phase 3: Save Context (2-5s)

**Task 3.1: Save Session Artifacts**
- Executor: @team-coordinator
- Output: files written to disk

```yaml
save_artifacts:
  base_path: ".data/team-outputs/{session-id}/"
  files:
    execution_plan:
      path: "execution-plan.yaml"
      content: "Original execution plan with final status annotations"

    agent_outputs:
      path: "agent-outputs/"
      content:
        - "{agent-name}-output.md"  # per agent deliverable
        - "..."

    merged_result:
      path: "merged-result.md"
      content: "Final synthesized output (if synthesis completed)"

    metrics:
      path: "metrics.yaml"
      content:
        total_duration: "Xs"
        tasks_completed: N
        tasks_total: N
        agents_used: N
        model_usage:
          opus: N
          sonnet: N
          haiku: N
        issues_encountered: N
        auto_reassignments: N

    session_log:
      path: "session-log.yaml"
      content: "Chronological log of all events, polls, alerts, actions"
```

**Task 3.2: Save Resumption Context**
- Executor: @team-coordinator
- Condition: has incomplete tasks
- Output: context for potential resume

```yaml
resumption_context:
  condition: "tasks_pending > 0 OR tasks_in_progress > 0"
  path: ".data/team-outputs/{session-id}/resume-context.yaml"
  content:
    original_demand: "..."
    squad: "..."
    pattern: "..."
    completed_work: ["task outputs"]
    remaining_tasks:
      - id: "task-X"
        subject: "..."
        status: "pending"
        context: "what was known at shutdown"
    resume_instructions: "To resume, run *execute-team --resume {session-id}"
```

### Phase 4: Cleanup (1-2s)

**Task 4.1: Delete Team**
- Executor: @team-coordinator
- Tool: TeamDelete

```yaml
cleanup:
  action: "TeamDelete"
  params:
    team_id: "{team_id}"
  on_success: "Team resources freed"
  on_failure: "Log error, team may need manual cleanup"
```

**Task 4.2: Present Final Summary**
- Executor: @team-coordinator
- Output: formatted summary to user

```yaml
final_summary:
  format: "markdown"
  sections:
    - header: "Team {name} - Shutdown Complete"
    - results: "What was accomplished"
    - incomplete: "What remains (if any)"
    - artifacts: "Where outputs are saved"
    - metrics: "Performance summary"
    - resume: "How to resume (if applicable)"
```

---

## Output Structure

```yaml
resultado:
  status: "shutdown_complete | shutdown_partial | shutdown_forced"

  shutdown_details:
    team_name: "team-copywriting-20260206"
    reason: "Task complete"
    force_used: false
    duration: "8s"

  agent_responses:
    - agent: "copywriter"
      response: "approved"
      final_output: "available"
    - agent: "designer"
      response: "approved"
      final_output: "available"

  work_summary:
    tasks_completed: 4
    tasks_incomplete: 0
    tasks_total: 4
    deliverables_saved: true

  artifacts:
    path: ".data/team-outputs/{session-id}/"
    files:
      - "execution-plan.yaml"
      - "agent-outputs/copywriter-output.md"
      - "agent-outputs/designer-output.md"
      - "merged-result.md"
      - "metrics.yaml"
      - "session-log.yaml"

  resumable: false  # true if incomplete tasks exist
  resume_command: null  # "*execute-team --resume {session-id}" if resumable
```

---

## Quality Gates

### Gate 1: Pre-Shutdown
- [ ] Team state assessed
- [ ] User warned about in-progress work (if applicable)
- [ ] Confirmation received (if not force)

### Gate 2: Shutdown Requests
- [ ] All agents received shutdown_request
- [ ] All responses collected or timed out
- [ ] Rejected shutdowns handled appropriately

### Gate 3: Output Collection
- [ ] All completed task outputs collected
- [ ] Partial outputs from in-progress tasks captured
- [ ] No data loss

### Gate 4: Persistence
- [ ] Artifacts saved to disk
- [ ] Metrics recorded
- [ ] Resume context saved (if applicable)

### Gate 5: Cleanup
- [ ] TeamDelete executed
- [ ] Final summary presented
- [ ] All resources freed

---

## Success Metrics

| Metrica | Alvo | Descricao |
|---------|------|-----------|
| Shutdown time | < 15s | Graceful shutdown duration |
| Agent response rate | 100% | Agents responding to shutdown |
| Data preservation | 100% | All outputs saved successfully |
| Clean exit | 100% | No orphaned resources |

---

## Rollback Points

```yaml
rollback:
  shutdown_rejected:
    condition: "Agent rejects shutdown and user does not force"
    action: "Resume monitoring, keep team running"
    message: "Shutdown cancelled. Team continues running."

  save_fails:
    condition: "Cannot write artifacts to disk"
    action: "Output results to console as fallback"
    message: "Could not save to disk. Displaying results in console."

  teamdelete_fails:
    condition: "TeamDelete call fails"
    action: "Log error, notify user of manual cleanup needed"
    message: "Team cleanup incomplete. May need manual intervention."

  partial_collection:
    condition: "Some agent outputs could not be collected"
    action: "Save what is available, note missing items"
    message: "Some outputs could not be collected from unresponsive agents."
```

---

## Example

### Input
```yaml
team_id: "team-copywriting-20260206"
force: false
save_context: true
reason: "All tasks completed"
```

### Processing
```yaml
# Phase 1: Pre-shutdown
assessment:
  tasks_completed: 4
  tasks_in_progress: 0
  tasks_pending: 0
  agents_active: 0
  agents_idle: 2  # both finished
  has_unsaved_work: false
  # No warning needed - all tasks complete

# Phase 2: Shutdown
requests:
  - agent: "copywriter"
    sent: "shutdown_request"
    response: "approved"
    time: "1.2s"
  - agent: "designer"
    sent: "shutdown_request"
    response: "approved"
    time: "0.8s"

outputs_collected:
  - task_1: "3 headline variations"
  - task_2: "Body copy for each variation"
  - task_3: "Visual mockup"
  - task_4: "Final design composition"

# Phase 3: Save
saved_to: ".data/team-outputs/abc123-def456/"
files_written: 6

# Phase 4: Cleanup
team_deleted: true
```

### Output
```markdown
## Team Shutdown Complete

**Team:** team-copywriting-20260206
**Duration:** 32s total | 5s shutdown
**Status:** All tasks completed successfully

### Results
- 4/4 tasks completed
- 2 agents shut down gracefully
- All outputs collected and saved

### Artifacts
Saved to: `.data/team-outputs/abc123-def456/`
- execution-plan.yaml
- agent-outputs/copywriter-output.md
- agent-outputs/designer-output.md
- merged-result.md
- metrics.yaml
- session-log.yaml

### Performance
| Metric | Value |
|--------|-------|
| Total time | 32s |
| Agent utilization | 88% |
| Tasks completed | 4/4 |
| Models used | 2x Sonnet |
```

## Integration

- **Squad:** orquestrador-global
- **Upstream:** *definir tasks que alimentam esta*
- **Downstream:** *definir tasks que esta alimenta*
