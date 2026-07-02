#!/usr/bin/env python3
"""PostToolUse hook: run promotion-detector after cmd_finalize writes.

Triggers when a Bash tool call likely corresponds to cmd_finalize (writes to
artifacts/pipeline/<slug>/PHASE-STREAM.jsonl or produces full_pipeline_report /
squad_activation templates). Calls scripts/promotion-detector.py non-blocking
and logs result to .data/logs/promotion-detector.log.

Fail-open: hook errors never block pipeline.

Hook: PostToolUse | Matcher: Write|Edit|Bash | Timeout: 8000ms
Story: STORY-MCE-6.0 Phase 6
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
_DETECTOR = _ROOT / "scripts" / "promotion-detector.py"
_LOG_DIR = _ROOT / ".data" / "logs"
_LOG_FILE = _LOG_DIR / "promotion-detector.log"

# template_ids that indicate cmd_finalize has just run
_FINALIZE_TEMPLATE_IDS = {
    "full_pipeline_report",
    "squad_activation",
    "llm_cost",
    "chronicler_audit",
}

# File path patterns that indicate a PHASE-STREAM write of a finalize phase
_FINALIZE_PATH_PATTERNS = [
    "PHASE-STREAM.jsonl",
]


def _should_trigger(data: dict) -> bool:
    """Return True if this tool event looks like a cmd_finalize completion."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # PostToolUse fires after the tool ran — check both input and output
    # For Write/Edit: check if file path is PHASE-STREAM.jsonl
    if tool_name in ("Write", "Edit", "MultiEdit"):
        file_path = tool_input.get("file_path", "")
        if "PHASE-STREAM.jsonl" in file_path:
            # Also check if the written content includes a finalize template_id
            new_content = tool_input.get("content", "") or tool_input.get("new_string", "")
            for tid in _FINALIZE_TEMPLATE_IDS:
                if (
                    f'"template_id": "{tid}"' in new_content
                    or f"'template_id': '{tid}'" in new_content
                ):
                    return True
        return False

    # For Bash: check if the command invokes cmd_finalize or orchestrate finalize
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        finalize_signals = [
            "cmd_finalize",
            "finalize",
            "orchestrate.py finalize",
            "orchestrate finalize",
        ]
        return any(sig in cmd for sig in finalize_signals)

    return False


def _log(msg: str) -> None:
    """Append a line to the promotion-detector log. Fail-open."""
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}\n")
    except Exception:
        pass


def main() -> int:
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else "{}"
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        data = {}

    try:
        if not _should_trigger(data):
            return 0

        if not _detector_exists():
            _log("SKIP: scripts/promotion-detector.py not found")
            return 0

        _log("TRIGGER: running promotion-detector after cmd_finalize signal")
        result = subprocess.run(
            [sys.executable, str(_DETECTOR)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(_ROOT),
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(_ROOT)},
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        rc = result.returncode

        _log(f"EXIT={rc} stdout={stdout!r:.200} stderr={stderr!r:.100}")

        if stdout:
            print(f"[promotion-detector] {stdout}", file=sys.stderr)

    except subprocess.TimeoutExpired:
        _log("TIMEOUT: promotion-detector took > 10s, skipped")
    except Exception as exc:
        _log(f"ERROR: {exc}")

    # Always exit 0 — hook is fail-open
    return 0


def _detector_exists() -> bool:
    return _DETECTOR.exists()


if __name__ == "__main__":
    sys.exit(main())
