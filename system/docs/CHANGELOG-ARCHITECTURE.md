# Mega Brain - Architecture Changelog

> Referenced from `.claude/CLAUDE.md`. Updated after each significant improvement session.
> This file is manually curated, not auto-generated.

---

## [2026-02-25] Hardening v1 — First-Time User Experience + Git Protection

### Setup & Onboarding
- Implemented `/setup` wizard with ASCII art banner, 6 interactive steps
- Auto-trigger setup when `.env` missing on first CLI command
- Reorganized `env.example` with clear categories (REQUIRED / RECOMMENDED / OPTIONAL / NOT NEEDED)
- ANTHROPIC_API_KEY documented as not needed with Claude Code
- SUPABASE vars removed from user-facing config (infrastructure only)

### Branch Protection & Contributing
- Created `CONTRIBUTING.md` with branch naming, conventional commits, PR workflow
- Created `.github/CODEOWNERS` — @thiagofinch owns all paths
- Created `.github/PULL_REQUEST_TEMPLATE.md` with quality checklist
- Added deny rules in `settings.json`: `git push`, `git push --force`, `git reset --hard`, `npm publish`

### Skills & Hooks Cleanup
- Renamed 12 numbered skills to kebab-case (e.g., `04-SKILL-KNOWLEDGE-EXTRACTION` → `knowledge-extraction`)
- Removed 11 orphaned hooks not referenced in settings (agent_doctor.py, auto_formatter.py, etc.)
- Cleaned `settings.local.json` references to deleted hooks
- Updated `package.json` files field with new skill names

### IDE Integration
- Created `.cursor/rules/mega-brain.md` — condensed project rules
- Created `.windsurf/rules/mega-brain.md` — condensed project rules
- Created `.antigravity/rules/mega-brain.md` — condensed project rules

### Documentation
- Rewrote `.claude/CLAUDE.md` for first-time users (148 lines, Quick Start, Community vs Pro)
- Synced `.github/layer1-allowlist.txt` with `package.json` files field (no wildcards for skills)
- Created this changelog

### Cross-Platform
- Verified all 23 hooks use `pathlib.Path` (no action needed)
- Confirmed `requirements.txt` documented as PyYAML-only

---

## [2026-02-20] Security Cleanup v2 (CLEANUP2)

- Sanitized SQL schemas and financial data (moneyclub → product)
- `git filter-repo` on git history to remove sensitive data
- Pre-publish gate hardened (`bin/pre-publish-gate.js`)
- Push.js false positives fixed

---

## [2026-02-18] Security Cleanup v1 (CLEANUP1)

- Initial credential audit across all tracked files
- `.gitignore` hardened for `.env`, credentials, sensitive data
- `layer1-allowlist.txt` created for Layer system
- `.gitleaks.toml` configured for automated secret scanning

---

## [2026-01-14] ANTHROPIC-STANDARDS v1.0

- Created `.claude/rules/ANTHROPIC-STANDARDS.md`
- Enforced timeout:30 on all hooks
- Established exit code convention (0=success, 1=warn, 2=block)
- Defined skill header format (Auto-Trigger, Keywords, Priority)

---

## [2026-01-10] Quality & Validation System

- Created `quality_watchdog.py` — meta-agent quality awareness
- Created `validate_phase5.py` — automated Phase 5 validation
- Implemented cascading integrity validation (RULE #21, #22, #26)
- Bug fix: dossiers not being updated when batches were newer

---

## [2025-12-20] Foundation

- Initial Mega Brain architecture (5-phase pipeline)
- JARVIS identity system (DNA personality, boot sequence)
- 30-rule governance framework (RULE-GROUP-1 through 6)
- Skill auto-routing via `skill_router.py` + `skill_indexer.py`
- Session persistence system (`session_autosave_v2.py`)
