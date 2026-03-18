#!/usr/bin/env python3
"""
directory_contract_guard.py — PreToolUse hook
Validates that new files are created in approved directories.
WARN (exit 1), not BLOCK (exit 2). Follows ANTHROPIC-STANDARDS.

Trigger: PreToolUse (Write, Edit)
Timeout: 30
"""

import json
import sys
from pathlib import Path

# Directories where new files are PROHIBITED
PROHIBITED_DIRS = [
    "docs",
]

# Suggested alternatives
ALTERNATIVES = {
    "docs": "reference/  (or update core/paths.py if new category needed)",
}


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"decision": "allow"}))
            sys.exit(0)

        tool_input = json.loads(raw)
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    tool_name = tool_input.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    file_path = tool_input.get("tool_input", {}).get("file_path", "")
    if not file_path:
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    # Resolve to relative path from project root
    path = Path(file_path)
    try:
        # Find project root by looking for core/paths.py
        project_root = Path(__file__).resolve().parent.parent.parent
        rel = path.resolve().relative_to(project_root)
    except (ValueError, RuntimeError):
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)  # Outside project, not our concern

    # Check against prohibited directories
    top_dir = rel.parts[0] if rel.parts else ""
    if top_dir in PROHIBITED_DIRS:
        alt = ALTERNATIVES.get(top_dir, "Check core/paths.py for correct location")
        msg = f"[Directory Contract] Writing to '{top_dir}/' is prohibited. Use: {alt}"
        print(json.dumps({"decision": "allow", "message": msg}))
        sys.exit(0)

    print(json.dumps({"decision": "allow"}))
    sys.exit(0)


if __name__ == "__main__":
    main()
