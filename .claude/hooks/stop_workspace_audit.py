#!/usr/bin/env python3
"""
Workspace Audit — Stop Hook
============================
Runs the workspace health check at session end, compares with the
session-start score, and warns if the score degraded.

Hook Type: Stop
Date: 2026-03-23
Timeout: 5000ms

OUTPUT:
- Improved:  [Workspace Audit] Score: 85->90 (+5) | Improved
- Stable:    [Workspace Audit] Score: 90->90 (0) | Stable
- Degraded:  [Workspace Audit] Score: 90->75 (-15) | Degraded

EXIT CODES:
- 0: Stable or improved (auto-saves baseline)
- 1: Degraded by 5+ points (warn)

ERROR HANDLING: fail-OPEN
- Any exception -> exit 0 (never crash session end)
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()


def main():
    """Hook entry point."""
    try:
        # Consume stdin (required by hook contract)
        sys.stdin.read()

        # Check if governance validators exist
        validators_dir = PROJECT_ROOT / "engine" / "governance" / "validators"
        runner_path = validators_dir / "runner.py"
        if not runner_path.exists():
            print("[Workspace Audit] Skipped — validators not yet configured")
            sys.exit(0)

        # Add project root to sys.path
        root_str = str(PROJECT_ROOT)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

        from engine.governance.workspace_health import (
            load_baseline,
            run_health_check,
            save_baseline,
        )

        # Load baseline (session-start score)
        baseline = load_baseline(PROJECT_ROOT)
        baseline_score = baseline.get("score", 0) if baseline else None

        # Run current health check
        report = run_health_check(PROJECT_ROOT)
        current_score = report.get("score", 0)

        if baseline_score is not None:
            delta = current_score - baseline_score
            delta_str = f"+{delta}" if delta >= 0 else str(delta)

            if delta <= -5:
                label = "Degraded"
            elif delta > 0:
                label = "Improved"
            else:
                label = "Stable"

            msg = f"[Workspace Audit] Score: {baseline_score}->{current_score} ({delta_str}) | {label}"

            if delta <= -5:
                # Warn on degradation — stderr required for exit(1) hooks
                sys.stderr.write(msg + "\n")
                sys.exit(1)
            else:
                # Stable or improved: save baseline
                save_baseline(PROJECT_ROOT, report)
                sys.exit(0)
        else:
            # No baseline existed: save current as first baseline
            save_baseline(PROJECT_ROOT, report)
            print(f"[Workspace Audit] Score: {current_score}/100 | First baseline saved")
            sys.exit(0)

    except Exception as e:
        # Graceful failure: never crash session end
        print(f"[Workspace Audit] Error: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()
