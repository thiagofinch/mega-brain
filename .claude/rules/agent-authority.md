# Agent Authority

Applies when any agent is activated.

## Exclusive Authorities

| Agent | Exclusive Operations |
|-------|---------------------|
| `@devops` | `git push`, `gh pr create/merge`, MCP management, CI/CD, releases |
| `@pm` | `*execute-epic`, `*create-epic`, requirements, spec writing |
| `@po` | `*validate-story-draft`, backlog prioritization, story scope edits |
| `@sm` | `*draft` / `*create-story`, story template selection |
| `@dev` | Local git ops (`add/commit/branch/stash/diff`), story checkboxes/file list |
| `@architect` | System architecture, tech selection, complexity assessment |
| `@data-engineer` | Schema DDL, query optimization, RLS, migrations (delegated from @architect) |
| `@mega-brain-master` | Framework governance, can execute ANY task, override boundaries |

**@dev BLOCKED from:** `git push`, `gh pr create/merge`, MCP management, editing story AC/scope/title.

## Delegation Protocol

### Git Push Flow
```
ANY agent → @devops *push
```

### Schema Design Flow
```
@architect (decides technology) → @data-engineer (implements DDL)
```

### Story Flow
```
@sm *draft → @po *validate → @dev *develop → @qa *qa-gate → @devops *push
```

### Epic Flow
```
@pm *create-epic → @pm *execute-epic → @sm *draft (per story)
```

## Escalation Rules

1. Agent cannot complete task → Escalate to @mega-brain-master
2. Quality gate fails → Return to @dev with specific feedback
3. Constitutional violation detected → BLOCK, require fix before proceed
4. Agent boundary conflict → @mega-brain-master mediates

## MCP Governance

**ONLY `@devops`** can manage MCP servers (add, remove, configure).

Other agents are MCP **consumers**, not administrators.
