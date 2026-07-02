#!/usr/bin/env python3
"""
Workspace Health Check — SessionStart Hook
===========================================
Runs the workspace governance health check on session start and prints
a summary line with score, new regressions, and known failures.

Hook Type: SessionStart
Date: 2026-03-23
Timeout: 5000ms

OUTPUT:
- Clean:       [Workspace] Score: 100/100 | Clean
- Regressions: [Workspace] Score: 85/100 | 2 new regressions | 3 known
- Skip:        [Workspace] Health check skipped — validators not yet configured

EXIT CODES:
- Always 0 (informational, never blocking)

ERROR HANDLING: fail-OPEN
- If validators don't exist -> skip message
- Any exception -> print error, exit 0
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def main():
    """Hook entry point. Always exits 0."""
    try:
        # Consume stdin (required by hook contract)
        sys.stdin.read()

        # Check if governance validators exist before importing
        validators_dir = PROJECT_ROOT / "core" / "governance" / "validators"
        runner_path = validators_dir / "runner.py"
        if not runner_path.exists():
            print("[Workspace] Health check skipped — validators not yet configured")
            sys.exit(0)

        # Add project root to sys.path so imports work
        root_str = str(PROJECT_ROOT)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

        from engine.governance.workspace_health import run_health_check

        report = run_health_check(PROJECT_ROOT)

        score = report.get("score", 0)
        new_regressions = report.get("new_regressions", [])
        known_failures = report.get("known_failures", [])

        # Build summary line
        parts = [f"[Workspace] Score: {score}/100"]

        if not new_regressions and not known_failures:
            parts.append("Clean")
        else:
            if new_regressions:
                parts.append(
                    f"{len(new_regressions)} new regression{'s' if len(new_regressions) != 1 else ''}"
                )
            if known_failures:
                parts.append(f"{len(known_failures)} known")

        summary = " | ".join(parts)
        print(summary)

        # List new regressions (max 3) if any
        if new_regressions:
            for name in new_regressions[:3]:
                print(f"  -> {name}")
            if len(new_regressions) > 3:
                print(f"  -> ... and {len(new_regressions) - 3} more")

    except Exception as e:
        print(f"[Workspace] Health check error: {e}")

    sys.exit(0)


if __name__ == "__main__":
    main()
