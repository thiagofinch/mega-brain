#!/usr/bin/env python3
"""
Session Autosave Hook - Mega Brain
Tracks tool usage for session persistence.
Called as PostToolUse hook for Bash, Write, Edit.

Usage: python3 session_autosave.py <TOOL_NAME> "<TOOL_INPUT>"
Exit codes: 0 = success, 1 = warning (non-blocking)
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path

MEGA_BRAIN_ROOT = os.getenv("MEGA_BRAIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SESSION_DIR = Path(MEGA_BRAIN_ROOT) / ".claude" / "sessions"
AUTOSAVE_LOG = SESSION_DIR / "autosave-activity.jsonl"


def main():
    tool_name = sys.argv[1] if len(sys.argv) > 1 else "UNKNOWN"
    tool_input = sys.argv[2] if len(sys.argv) > 2 else ""

    try:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "input_preview": tool_input[:200] if tool_input else "",
        }

        with open(AUTOSAVE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    except Exception:
        # Non-critical - never block execution
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
