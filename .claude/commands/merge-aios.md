# /merge-aios — Framework Integration Command

> **Status:** LEGACY — The staging model (_aios-core/ subdirectories) was replaced by direct installation.
> All content now lives at root level of .claude/skills/, .claude/commands/, .claude/rules/.
> The .aiox/ directory contains development agents, hooks, skills, and protocols.
> This command is preserved for reference but no longer needs to be executed.

## Current Architecture

```
.aiox/                    → Development framework (agents, hooks, skills, protocols)
.claude/skills/                → All skills at root level (native + migrated)
.claude/commands/              → All commands at root level (native + migrated)
.claude/rules/                 → All rules at root level (native + migrated)
.claude/agents/                → Claude Code agent types (24 files)
```

## What Was Already Done

- All skills, commands, rules moved to root level (no _aios-core/ staging)
- All paths verified functional
- settings.json updated with hook references
- package.json negation patterns removed (content is tracked)
- pre-publish-gate.js hardened

## If Re-Integration Is Needed

Run `*validate-completeness` to check current state of all personas and system health.
