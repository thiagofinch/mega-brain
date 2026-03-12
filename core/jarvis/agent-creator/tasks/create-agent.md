# create-agent

```yaml
---
task: TSK-101
execution_type: Agent
responsible: "@agent-creator"
---
```

## Task Anatomy

| Field | Value |
|-------|-------|
| task_name | Create New Agent |
| status | active |
| responsible_executor | @agent-creator |
| execution_type | Agent |
| input | layer, id, name, role, source, traits |
| output | AGENT.md, SOUL.md, command.md, registry entry |
| action_items | 8 steps |
| acceptance_criteria | Agent operational and registered |

---

## Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| layer | enum | yes | L0/L1/L2/L3/L4/SUB |
| id | string | yes | Agent ID (kebab-case) |
| name | string | yes | Display name |
| role | string | yes | Role description |
| source | string | no | Origin (pipeline source_id or "manual") |
| traits | array | no | Personality traits |
| element | string | no | Fire/Earth/Air/Water |

---

## Outputs

| Output | Type | Location | Description |
|--------|------|----------|-------------|
| agent_md | md | agents/{layer}/{id}/AGENT.md | Agent definition |
| soul_md | md | agents/{layer}/{id}/SOUL.md | Personality |
| command_md | md | .claude/commands/{id}.md | Activation command |
| registry | yaml | agents/persona-registry.yaml | Registry entry |

---

## Execution

### Phase 1: Validation
**Quality Gate:** QG-101

1. Validate layer is valid (L0, L1, L2, L3, L4, SUB)
2. Validate id is kebab-case and unique
3. Check persona-registry.yaml for duplicates
4. Determine target folder based on layer

```python
LAYER_FOLDERS = {
    "L0": "core/jarvis/",
    "L1": "agents/conclave/",
    "L2": "agents/boardroom/",
    "L3": "agents/minds/",
    "L4": "agents/cargo/",
    "SUB": ".claude/jarvis/sub-agents/"
}
```

### Phase 2: Generate Files
**Quality Gate:** QG-103

1. Load AGENT template from `agents/_templates/TEMPLATE-AGENT-V3.md`
2. Load SOUL template from `core/templates/agents/SOUL-TEMPLATE.md`
3. Fill templates with provided data
4. Generate greetings based on identity level

### Phase 3: Create Command
**Quality Gate:** QG-105

1. Create `.claude/commands/{id}.md`
2. Format:
```markdown
# /{id}

Ativar agente {name}.

## Instrução

Ler e assumir identidade de:
- {layer_folder}/{id}/AGENT.md
- {layer_folder}/{id}/SOUL.md

Responder como {name} com sua voz e perspectiva únicas.
```

### Phase 4: Update Registry
**Quality Gate:** QG-104

1. Read `agents/persona-registry.yaml`
2. Add entry to appropriate section
3. Save updated registry

---

## Acceptance Criteria

- [ ] AGENT.md exists at correct location
- [ ] SOUL.md exists at correct location
- [ ] Command file created
- [ ] Entry added to persona-registry.yaml
- [ ] No duplicate IDs in registry

---

## Handoff

| Next Task | Trigger | Data Passed |
|-----------|---------|-------------|
| sync-agents | creation_complete | agent_id, layer |
| validate-agent | creation_complete | agent_path |

---

## Protocol Reference

See `core/jarvis/agent-creator/AGENT.md` for full context.

---

**Task Version:** 1.0.0
