#!/usr/bin/env python3
"""
invalidate_capability_embeddings.py -- PostToolUse hook: mark embedding cache stale

Trigger paths (any Write/Edit hitting one of these marks the cache stale):
  - agents/_registry/capability-registry.yaml          (TIL-12 AC7)
  - .claude/skills/*/business-context.md               (TIL-12 @po condition #4 — L3 source)

Side effect: `touch .data/capability-embeddings.stale` (zero-byte sentinel).

Debounce floor (30s):
  If sentinel exists AND was touched < 30s ago, do not re-touch — prevents
  thundering-herd rebuild signaling during batch edits (e.g., sed -i across
  N capabilities).

Fail-open: any exception logs to stderr and exits 0 — must NEVER block tool flow.

Story: TIL-12 (AC7 + @po condition #4)
Architect Q3: sentinel + 30s debounce floor.
"""

from __future__ import annotations

import fnmatch
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
HOOK_TAG = "[invalidate_capability_embeddings]"

STALE_SENTINEL = PROJECT_ROOT / ".data" / "capability-embeddings.stale"
DEBOUNCE_SECONDS = 30

REGISTRY_REL = "agents/_registry/capability-registry.yaml"
SKILL_CTX_GLOB = ".claude/skills/*/business-context.md"


def _log(msg: str) -> None:
    print(f"{HOOK_TAG} {msg}", file=sys.stderr)


def _matches_trigger(rel_path: str) -> bool:
    if rel_path == REGISTRY_REL:
        return True
    if fnmatch.fnmatch(rel_path, SKILL_CTX_GLOB):
        return True
    return False


def _extract_file_path(event: dict) -> str | None:
    tool_input = event.get("tool_input") or {}
    fp = tool_input.get("file_path") or tool_input.get("filePath") or tool_input.get("path")
    if not fp:
        return None
    try:
        abs_path = Path(fp).resolve()
        rel = abs_path.relative_to(PROJECT_ROOT)
        return str(rel)
    except (ValueError, OSError):
        return None


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        event = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return 0

    rel = _extract_file_path(event)
    if not rel:
        return 0

    if not _matches_trigger(rel):
        return 0

    # Debounce: if sentinel was touched < 30s ago, skip.
    now = time.time()
    if STALE_SENTINEL.exists():
        try:
            if now - STALE_SENTINEL.stat().st_mtime < DEBOUNCE_SECONDS:
                _log(f"debounce hit ({rel}) — sentinel <{DEBOUNCE_SECONDS}s old")
                return 0
        except OSError:
            pass

    try:
        STALE_SENTINEL.parent.mkdir(parents=True, exist_ok=True)
        STALE_SENTINEL.touch(exist_ok=True)
        os.utime(STALE_SENTINEL, (now, now))
        _log(f"marked stale (trigger={rel})")
    except OSError as e:
        _log(f"failed to touch sentinel: {e} (fail-open)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
