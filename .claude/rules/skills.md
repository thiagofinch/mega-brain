---
paths:
  - ".claude/skills/**"
  - ".claude/skills/skill-registry.yaml"
  - "squads/*/tasks/**"
---
# Skill Rules — Mega Brain

Applies when editing files in `.claude/skills/` or `squads/*/tasks/`.

## Skill Structure (by Tier)

Skills follow a tiered structure based on complexity:

### Tier 1 (Minimal)

```
.claude/skills/{skill-name}/
  SKILL.md              — Skill definition with frontmatter + instructions
```

### Tier 2 (Standard)

```
.claude/skills/{skill-name}/
  SKILL.md              — Skill definition with frontmatter + instructions
  references/           — Reference docs bundled with the skill
  assets/               — Templates, configs, static resources
```

### Tier 3 (Full Pipeline)

```
.claude/skills/{skill-name}/
  SKILL.md              — Skill definition with frontmatter + instructions
  scripts/              — Deterministic scripts (zero external deps)
  references/           — Reference docs bundled with the skill
  assets/               — Templates, configs, static resources
```

## Required Frontmatter Fields

Every `SKILL.md` MUST have YAML frontmatter with these fields:

```yaml
---
name: skill-name                    # kebab-case, matches directory name
description: "What this skill does" # Clear, concise — used by Claude for skill matching
version: "1.0.0"                    # semver
owner_squad: squad-name             # Squad responsible for maintenance
megabrain_tier: Tier1                  # Tier1 | Tier2 | Tier3
context: conversation               # conversation (default) | fork (isolated) — see skill-standards.md Decision Matrix
agent: general-purpose              # general-purpose | agent-specific-name
user-invocable: true                # true if user can invoke directly
---
```

### Optional Frontmatter Fields

```yaml
argument-hint: "[scope: option1|option2]"  # Hint for user arguments
status: active                              # active | mega-brain-core-only | vendored | deprecated
license: "See LICENSE in this directory"    # For third-party/vendored skills
```

## Registration Requirement

Every skill MUST be registered in `.claude/skills/skill-registry.yaml`. When creating or modifying a skill:

1. Ensure `SKILL.md` frontmatter is complete and accurate
2. Add or update the skill entry in `skill-registry.yaml`
3. Update `registry.total_skills` count if adding/removing skills
4. Update `registry.last_updated` date

## Versioning Policy

| Change Type | Version Bump | Approval |
|-------------|-------------|----------|
| Patch (typo, minor fix) | `x.x.+1` | Owner squad |
| Minor (new capability, non-breaking) | `x.+1.0` | Owner squad |
| Major (breaking change, new pipeline) | `+1.0.0` | Roundtable review |

Keep version in `SKILL.md` frontmatter and `skill-registry.yaml` in sync.

## Scripts

Scripts in `scripts/` (Tier 3 skills) MUST be:

1. **Deterministic** — same input produces same output
2. **Zero external dependencies** — no `npm install`, no network calls at import time
3. **Portable** — run on any machine with Node.js 18+
4. **Self-contained** — all logic within the skill directory

## Templates

Templates in `assets/` or `references/` MUST use `{placeholder}` format for variable substitution:

```markdown
# {project_name} Report

Generated on {date} by {agent_name}.
```

## Naming Conventions

- Skill directories: `kebab-case` (e.g., `tech-search`, `wave-execute`)
- SKILL.md: Always uppercase `SKILL.md` (entry point)
- Scripts: `kebab-case.js` or `kebab-case.sh`
- References: `kebab-case.md` or `kebab-case.yaml`

## Vendored Skills

Third-party skills with their own `.git/` directory are treated as vendored:

1. Add `status: vendored` to frontmatter
2. Add `license` field pointing to LICENSE file
3. Do NOT modify vendored content without upstream coordination
4. Do NOT remove `.git/` directories — that is a destructive operation requiring explicit user approval

## Key Files

| File | Purpose |
|------|---------|
| `.claude/skills/skill-registry.yaml` | Canonical catalog of all skills |
| `.claude/skills/{name}/SKILL.md` | Skill entry point and definition |
| `.claude/rules/skills.md` | This governance rule |

---

*Skill Rules v1.0 — Mega Brain*
*Phase 5 MEGABRAIN Skills Compliance Roadmap*
