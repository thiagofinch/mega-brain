#!/usr/bin/env python3
"""Governance Auto-Update — PostToolUse (Write|Edit).
Detects writes to watched files, triggers governance doc regeneration.
Never blocks (exit 1 = warn only). CONST-005.
"""
import json, subprocess, sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
WATCH_PREFIXES = ("core/engine/rules/", "core/intelligence/pipeline/mce/")
WATCH_EXACT = {
    "core/paths.py", "pyproject.toml", "biome.json",
    "package.json", ".claude/settings.json",
}


def _to_relative(file_path: str) -> str:
    try:
        return str(Path(file_path).resolve().relative_to(_ROOT))
    except (ValueError, OSError):
        return file_path


def _matches(rel: str) -> bool:
    if rel in WATCH_EXACT:
        return True
    return any(rel.startswith(p) for p in WATCH_PREFIXES)


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        event = json.loads(raw)
        if event.get("tool_name", "") not in ("Write", "Edit"):
            sys.exit(0)
        file_path = event.get("tool_input", {}).get("file_path", "")
        if not file_path:
            sys.exit(0)
        rel = _to_relative(file_path)
        if not _matches(rel):
            sys.exit(0)

        fname = Path(rel).name
        result = subprocess.run(
            [sys.executable, "-m", "core.governance.engine", "all"],
            cwd=str(_ROOT), capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            print(json.dumps({"message": f"Governance docs regenerated (triggered by {fname})"}))
            sys.exit(0)
        else:
            err = (result.stderr or result.stdout or "unknown").strip()[:200]
            print(json.dumps({"warning": f"Governance regeneration failed: {err}"}))
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print(json.dumps({"warning": "Governance regeneration timed out (>10s)"}))
        sys.exit(1)
    except Exception as exc:
        print(json.dumps({"warning": f"Governance hook error: {exc!s}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
