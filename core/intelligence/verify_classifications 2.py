#!/usr/bin/env python3
"""Spot-check verification for audit_layers.py classifier. Tests known file->layer mappings."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_layers import classify_path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# (relative_path, expected_layer, description)
SPOT_CHECKS = [
    # L1 — Core engine
    ('core/tasks/HO-TP-001.md', 'L1', 'Core task file'),
    ('bin/cli.js', 'L1', 'CLI entry point'),
    ('.claude/CLAUDE.md', 'L1', 'Claude integration'),
    ('docs/audit/AUDIT-REPORT.md', 'L1', 'Documentation'),
    # L1 — Root project files
    ('package.json', 'L1', 'NPM package config'),
    ('package-lock.json', 'L1', 'NPM lockfile'),
    ('.gitignore', 'L1', 'Git ignore rules'),
    ('.npmignore', 'L1', 'NPM ignore rules'),
    ('.env.example', 'L1', 'Environment template'),
    ('README.md', 'L1', 'Root documentation'),
    ('CONTRIBUTING.md', 'L1', 'Contribution guide'),
    ('QUICK-START.md', 'L1', 'Quick start guide'),
    ('requirements.txt', 'L1', 'Python dependencies'),
    ('.gitattributes', 'L1', 'Git attributes'),
    ('.gitleaks.toml', 'L1', 'Secret scanning config'),
    # L1 — GitHub
    ('.github/workflows/publish.yml', 'L1', 'CI publish workflow'),
    ('.github/CODEOWNERS', 'L1', 'Code ownership'),
    ('.github/ISSUE_TEMPLATE/bug.md', 'L1', 'Issue template'),
    # L1 — Planning
    ('.planning/ROADMAP.md', 'L1', 'GSD roadmap'),
    ('.planning/STATE.md', 'L1', 'GSD state'),
    ('.planning/phases/09-layer-validation/09-01-PLAN.md', 'L1', 'Phase plan'),
    # L1 — IDE configs
    ('.cursor/rules/mega-brain.md', 'L1', 'Cursor IDE rules'),
    ('.windsurf/agents.yaml', 'L1', 'Windsurf agents'),
    ('.antigravity/README.md', 'L1', 'Antigravity docs'),
    # L1 — Agents scaffold
    ('agents/boardroom/README.md', 'L1', 'Boardroom docs'),
    ('agents/constitution/BASE-CONSTITUTION.md', 'L1', 'Agent constitution'),
    ('agents/AGENT-INDEX.yaml', 'L1', 'Agent index'),
    ('agents/conclave/CONCLAVE-PROTOCOL.md', 'L1', 'Conclave protocol'),
    # L1 — Structure markers
    ('inbox/.gitkeep', 'L1', 'Empty structure marker'),
    ('agents/cargo/.gitkeep', 'L1', 'Empty structure marker'),
    ('knowledge/.gitkeep', 'L1', 'Empty structure marker'),
    # L2 — Premium content
    ('agents/minds/some-agent/AGENT.md', 'L2', 'Mind clone agent'),
    ('agents/cargo/some-role/AGENT.md', 'L2', 'Cargo agent'),
    ('knowledge/dossiers/some-file.md', 'L2', 'Knowledge dossier'),
    # L3 — Personal data
    ('inbox/some-file.txt', 'L3', 'Inbox content'),
    ('logs/some-log.md', 'L3', 'Session log'),
    ('.claude/sessions/SESSION-2026.md', 'L3', 'Claude session'),
    # NEVER — Secrets and system files
    ('.env', 'NEVER', 'Environment secrets'),
    ('credentials.json', 'NEVER', 'OAuth credentials'),
    ('.mcp.json', 'NEVER', 'MCP config with tokens'),
    ('.DS_Store', 'NEVER', 'macOS metadata'),
    # DELETE — Obsolete and stale
    ('some/path/finance-agent/file.md', 'DELETE', 'Obsolete finance agent'),
    ('artifacts/README 2.md', 'DELETE', 'Stale macOS duplicate'),
    ('knowledge/TAG-RESOLVER 2.json', 'DELETE', 'Stale macOS duplicate'),
]

def main():
    passed = 0
    failed = 0
    errors = []
    for rel_path, expected, desc in SPOT_CHECKS:
        abs_path = REPO_ROOT / rel_path
        try:
            layer, reason = classify_path(abs_path, REPO_ROOT, is_file=True)
            if layer == expected:
                passed += 1
            else:
                failed += 1
                errors.append(f"  FAIL: {rel_path} — expected {expected}, got {layer} ({reason})")
        except Exception as e:
            failed += 1
            errors.append(f"  ERROR: {rel_path} — {e}")
    print(f"Spot checks: {passed} passed, {failed} failed (total {passed + failed})")
    if errors:
        print()
        for err in errors:
            print(err)
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
