# sync-agents

```yaml
---
task: TSK-102
execution_type: Worker
responsible: "@agent-creator"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Sync Agents Across IDEs |
| status | active |
| responsible_executor | @agent-creator |
| execution_type | Worker |
| input | agent_id, source_ide |
| output | synced config files |
| action_items | 4 steps |
| acceptance_criteria | All IDEs have consistent agent configs |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| agent_id | string | no | Specific agent to sync (or all) |
| source_ide | string | no | Source IDE (.claude default) |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| claude_config | yaml | .claude/agents.yaml | Claude Code agents |
| cursor_config | yaml | .cursor/agents.yaml | Cursor agents |
| windsurf_config | yaml | .windsurf/agents.yaml | Windsurf agents |

---

## Execution

### Phase 1: Read Source
1. Read `agents/persona-registry.yaml` as source of truth
2. Parse all agent entries

### Phase 2: Generate IDE Configs
1. Transform registry format to IDE-specific format
2. Generate summary configs for each IDE

### Phase 3: Write Configs
1. Write to `.claude/agents.yaml`
2. Write to `.cursor/agents.yaml`
3. Write to `.windsurf/agents.yaml`

### Phase 4: Verify
1. Validate all configs are valid YAML
2. Report sync status

---

## IDE Config Format

```yaml
# .claude/agents.yaml (example)
version: "1.0"
synced_from: "agents/persona-registry.yaml"
last_sync: "2026-02-27T10:00:00Z"

agents:
  conclave:
    - id: critic
      command: "/critic"
      path: "agents/conclave/critico-metodologico/"
    - id: devils-advocate
      command: "/advocate"
      path: "agents/conclave/advogado-do-diabo/"

  minds:
    - id: cole-gordon
      command: "/cole"
      path: "agents/minds/cole-gordon/"
```

---

## Acceptance Criteria

- [ ] All IDE configs exist
- [ ] Configs are valid YAML
- [ ] All agents from registry are present
- [ ] last_sync timestamp updated

---

**Task Version:** 1.0.0
