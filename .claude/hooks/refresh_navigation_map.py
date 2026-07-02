#!/usr/bin/env python3
"""refresh_navigation_map.py — PostToolUse hook (Story MCE-3.6 AC5).

Fires after Write/Edit operations. When the touched path lives under
`knowledge/**/dossiers/**/*.md`, runs `bin/refresh-navigation-map.sh`
(which is internally debounced to once per 60s).

Soft-fail by design: any error is logged and the hook exits 0 so it
never blocks tool execution.

Opt-out: set env `MCE_NAV_MAP_DISABLED=1`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))
REFRESH_SCRIPT = PROJECT_DIR / "bin" / "refresh-navigation-map.sh"


def _matches_dossier(path_str: str) -> bool:
    if not path_str:
        return False
    p = Path(path_str)
    parts = p.parts
    try:
        i = parts.index("dossiers")
    except ValueError:
        return False
    if "knowledge" not in parts[:i]:
        return False
    return p.suffix.lower() == ".md"


def main() -> int:
    if os.environ.get("MCE_NAV_MAP_DISABLED") == "1":
        return 0
    if not REFRESH_SCRIPT.is_file():
        return 0

    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except (json.JSONDecodeError, ValueError):
        payload = {}

    tool_input = payload.get("tool_input") or {}
    candidates = [
        tool_input.get("file_path"),
        tool_input.get("path"),
        tool_input.get("notebook_path"),
    ]
    # Multi-file edits surface under tool_input.edits[].file_path
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict):
            candidates.append(edit.get("file_path"))

    if not any(_matches_dossier(str(c)) for c in candidates if c):
        return 0

    try:
        subprocess.run(
            ["bash", str(REFRESH_SCRIPT)],
            cwd=str(PROJECT_DIR),
            timeout=30,
            check=False,
            capture_output=True,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        sys.stderr.write(f"[refresh_navigation_map] non-fatal: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
