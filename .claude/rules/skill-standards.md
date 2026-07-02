---
paths:
  - ".claude/skills/**"
  - ".claude/skills/skill-registry.yaml"
---
# Skill Standards -- Mega Brain

Applies when creating, editing, or validating skills in `.claude/skills/`.

## Canonical Frontmatter Schema

Every skill MUST have a YAML frontmatter block at the top of its `SKILL.md`.

### Required Fields (ALL skills)

```yaml
---
name: "{skill-id}"                    # kebab-case, matches directory name
description: "..."                    # 1-2 sentences explaining purpose
version: "1.0.0"                      # semver (major.minor.patch)
owner_squad: "{squad-name}"           # squad responsible for maintenance
megabrain_tier: "Tier1|Tier2|Tier3"      # MEGABRAIN compliance level
context: conversation                 # execution context (conversation | fork) — see Decision Matrix below
agent: general-purpose                # agent type
user-invocable: true|false            # can users call directly via /skill-name
---
```

### Context Field — Decision Matrix (NON-NEGOTIABLE)

The `context` field controls where the skill executes. **`conversation` is the default** — 74% of skills require it. `fork` is for self-contained, isolated tools only.

**Valid values:** `conversation` | `fork`

| Question | If YES | Severity |
|----------|--------|----------|
| Q1: Uses TeamCreate, Agent(), or SendMessage? | MUST `conversation` | BLOCKING |
| Q2: Uses Task(subagent_type)? | MUST `conversation` | BLOCKING |
| Q3: Invokes another multi-agent skill (/roundtable, /wave-execute)? | MUST `conversation` | BLOCKING |
| Q4: Persists state (.json, checkpoints)? | SHOULD `conversation` | WARNING |
| Q5: Needs conversation history (prior decisions, session context)? | SHOULD `conversation` | WARNING |
| Q6: Self-contained and deterministic (validation, CLI wrapper, doc gen)? | CAN `fork` | INFO |

**Patterns → fork (isolated execution):**
- Pure validation logic (validate-skill, validate-story-draft)
- CLI tool wrappers (coderabbit-review, llm-scan)
- Document generation from explicit inputs (handoff)

**Patterns → conversation (shared context):**
- Multi-agent orchestration (roundtable, deep-strategic-planning)
- Task delegation to Mega Brain agents (commit, deploy, execute-epic)
- Multi-phase workflows with state (epic-cycle, wave-execute, story-cycle)
- Skills referencing prior conversation decisions

**Any value other than `fork` or `conversation` is invalid and MUST be rejected by validation.**

### Optional Fields

```yaml
depends_on: ["/handoff", "/roundtable"]  # cross-skill dependencies
invokes: ["/roundtable"]                 # skills this one calls during execution
license: "..."                           # for third-party or forked skills
argument-hint: "[args description]"      # hint for CLI usage
```

## MEGABRAIN Tier Definitions

| Tier | Name | Description |
|------|------|-------------|
| **Tier 1** | Basic | Minimal compliance. Skill has frontmatter, owner, version, and a functional SKILL.md. |
| **Tier 2** | Standard | Tier 1 + process_id + MEGABRAIN mode + config.yaml with artifact_contracts. |
| **Tier 3** | Full | Tier 2 + complete MEGABRAIN architecture (molecules/atoms/tokens) + templates/ + checklists/ + data/. |

### Tier Requirements Matrix

| Requirement | Tier 1 | Tier 2 | Tier 3 |
|-------------|--------|--------|--------|
| SKILL.md with frontmatter | REQUIRED | REQUIRED | REQUIRED |
| `name` field | REQUIRED | REQUIRED | REQUIRED |
| `description` field | REQUIRED | REQUIRED | REQUIRED |
| `version` field | REQUIRED | REQUIRED | REQUIRED |
| `owner_squad` field | REQUIRED | REQUIRED | REQUIRED |
| `megabrain_tier` field | REQUIRED | REQUIRED | REQUIRED |
| `context` field | REQUIRED | REQUIRED | REQUIRED |
| `agent` field | REQUIRED | REQUIRED | REQUIRED |
| `user-invocable` field | REQUIRED | REQUIRED | REQUIRED |
| config.yaml | OPTIONAL | REQUIRED | REQUIRED |
| process_id in config.yaml | OPTIONAL | REQUIRED | REQUIRED |
| MEGABRAIN mode declared | OPTIONAL | REQUIRED | REQUIRED |
| Registered in process-registry | OPTIONAL | REQUIRED | REQUIRED |
| templates/ directory (1+ file) | OPTIONAL | OPTIONAL | REQUIRED |
| checklists/ directory (1+ file) | OPTIONAL | OPTIONAL | REQUIRED |
| data/ directory (1+ file) | OPTIONAL | OPTIONAL | REQUIRED |
| scripts/ directory (1+ file) | OPTIONAL | OPTIONAL | RECOMMENDED |
| artifact_contracts[] in config.yaml | OPTIONAL | OPTIONAL | REQUIRED |
| Tokens in token-registry.yaml | OPTIONAL | OPTIONAL | REQUIRED |
| MEGABRAIN molecules/atoms/tokens | OPTIONAL | OPTIONAL | REQUIRED |

### Current Skill Tier Assignments

| Skill | Owner Squad | Tier |
|-------|-------------|------|
| handoff | mega-brain | Tier 3 |
| roundtable | mega-brain | Tier 3 |
| wave-execute | mega-brain | Tier 3 |
| tech-search | infra-ops-squad | Tier 1 |
| coderabbit-review | infra-ops-squad | Tier 1 |
| synapse | mega-brain | Tier 1 |
| skill-creator | mega-brain | Tier 1 |
| service-file-parser | infra-ops-squad | Tier 1 |
| service-google-drive | infra-ops-squad | Tier 1 |
| design-system-ops | design-squad | Tier 1 |

## Versioning Policy

Skills follow [Semantic Versioning](https://semver.org/):

| Change Type | Version Bump | Approval Required |
|-------------|-------------|-------------------|
| Breaking changes (API, template format, removed features) | **Major** (X.0.0) | Roundtable review |
| New features, new atoms, new templates | **Minor** (0.X.0) | Owner squad approval |
| Bug fixes, documentation, typos | **Patch** (0.0.X) | Owner squad approval |

### Rules

1. Major version bumps REQUIRE a roundtable review before merge
2. Minor and patch version bumps require owner squad sign-off
3. Version in SKILL.md frontmatter MUST match version in config.yaml (if config.yaml exists)
4. Changelog SHOULD be maintained for Tier 2+ skills

## Naming Convention

- **Skill directory:** kebab-case, descriptive (`wave-execute`, `tech-search`)
- **SKILL.md `name` field:** matches directory name exactly
- **Activation:** `/skill-name` (e.g., `/handoff`, `/roundtable`)
- **Service skills:** prefix with `service-` (e.g., `service-file-parser`)
- **Third-party/forked skills:** keep original name, add `license` field

## File Structure Requirements

### Tier 1 (Basic)

```
.claude/skills/{skill-name}/
  SKILL.md              # REQUIRED -- skill definition with frontmatter
```

### Tier 2 (Standard)

```
.claude/skills/{skill-name}/
  SKILL.md              # REQUIRED -- skill definition with frontmatter
  config.yaml           # REQUIRED -- process_id, mode, artifact_contracts
```

### Tier 3 (Full)

```
.claude/skills/{skill-name}/
  SKILL.md              # REQUIRED -- skill definition with frontmatter
  config.yaml           # REQUIRED -- full MEGABRAIN configuration
  templates/            # REQUIRED -- output templates (1+ file)
  checklists/           # REQUIRED -- quality checklists (1+ file)
  data/                 # REQUIRED -- knowledge base files (1+ file)
  scripts/              # RECOMMENDED -- automation scripts
  workflows/            # RECOMMENDED -- machine-readable pipeline YAML
```

## Registry Governance

- All skills MUST be tracked in `squads/infra-ops-squad/data/service-catalog.yaml` (Tier 2+ required, Tier 1 recommended)
- Skill file changes (`.claude/skills/*/SKILL.md`) are monitored by the registry governance check
- Corresponding registry: `service-catalog.yaml`

---

*Skill Standards v1.0 -- Mega Brain*
*Phase 3.2 | MEGABRAIN Skills Compliance Roadmap | Epic 68*
