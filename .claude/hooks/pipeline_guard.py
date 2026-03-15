#!/usr/bin/env python3
"""
Pipeline Guard Hook v2.0 — PostToolUse (Write|Edit|NotebookEdit)
================================================================
Warns when a file is written outside any known ROUTING path.
Never blocks (always exit 0). Logs warnings to pipeline-guard.jsonl.

Uses core/governance/pipeline_guard.py for validation logic.

Hook: PostToolUse (Write|Edit|NotebookEdit) | Timeout: 30s
Epic 3.2 — Governance Engine
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

LOG_FILE = _ROOT / "logs" / "pipeline-guard.jsonl"


def _log_warning(file_path: str, reason: str) -> None:
    """Append warning to JSONL log."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "file": file_path,
            "reason": reason,
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        hook_input = json.loads(raw)
        tool_name = hook_input.get("tool_name", "")

        if tool_name not in ("Write", "Edit", "NotebookEdit"):
            sys.exit(0)

        file_path = hook_input.get("tool_input", {}).get("file_path", "")
        if not file_path:
            # NotebookEdit uses notebook_path
            file_path = hook_input.get("tool_input", {}).get("notebook_path", "")
        if not file_path:
            sys.exit(0)

        # Use governance module for validation
        try:
            from core.governance.pipeline_guard import validate_output_path
            is_valid, reason = validate_output_path(file_path)
        except ImportError:
            # Fallback: allow if governance module not available
            sys.exit(0)

        if not is_valid:
            _log_warning(file_path, reason)
            print(json.dumps({"continue": True, "warning": reason}))
        elif reason.startswith("WARN:"):
            _log_warning(file_path, reason)
            print(json.dumps({"continue": True, "warning": reason}))
        # else: silent success

    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
