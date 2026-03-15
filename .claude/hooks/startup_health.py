#!/usr/bin/env python3
"""
Startup Health Hook v1.0 — SessionStart
========================================
Validates critical directories and state files on session start.
Prints compact health summary. Never blocks (always exit 0).

Hook: SessionStart | Timeout: 5s
Epic 3.3 — Governance Engine
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

# Critical directories that MUST exist
CRITICAL_DIRS = [
    "core",
    "agents",
    "knowledge/external",
    ".claude/hooks",
    ".claude/rules",
    ".claude/skills",
]

# Critical state files that MUST exist
CRITICAL_FILES = [
    "core/paths.py",
    "agents/AGENT-INDEX.yaml",
    ".claude/settings.json",
]

# ROUTING keys to spot-check (sample — not all 131)
ROUTING_SPOT_CHECKS = [
    "logs",
    "artifacts/audit",
    ".data",
    ".claude/sessions",
    ".claude/mission-control",
]


def main():
    try:
        missing_dirs = []
        for d in CRITICAL_DIRS:
            if not (_ROOT / d).is_dir():
                missing_dirs.append(d)

        missing_files = []
        for f in CRITICAL_FILES:
            if not (_ROOT / f).is_file():
                missing_files.append(f)

        missing_routing = []
        try:
            from core.paths import ROUTING
            for key in ROUTING_SPOT_CHECKS:
                path = _ROOT / key
                if not path.parent.exists():
                    missing_routing.append(key)
        except ImportError:
            missing_routing.append("core.paths import failed")

        total_checks = len(CRITICAL_DIRS) + len(CRITICAL_FILES) + len(ROUTING_SPOT_CHECKS)
        total_issues = len(missing_dirs) + len(missing_files) + len(missing_routing)
        passed = total_checks - total_issues

        if total_issues == 0:
            print(f"[Health] {passed}/{total_checks} checks OK")
        else:
            issues = missing_dirs + missing_files + missing_routing
            print(f"[Health] {passed}/{total_checks} OK | Missing: {', '.join(issues[:5])}")

    except Exception as e:
        print(f"[Health] error: {str(e)[:60]}")

    sys.exit(0)


if __name__ == "__main__":
    main()
