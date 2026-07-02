#!/usr/bin/env python3
"""PreToolUse hook: block adds of new emit_* functions without registry entry.

Per AC-8 of STORY-MCE-6.0: if a new emit_{template_id} is added to
engine/intelligence/pipeline/mce/log_emitters.py (or any pipeline file)
without a corresponding entry in .claude/skills/chronicler/chronicler-registry.yaml,
the write is blocked. Prevents drift between emitters and renderers.

Hook: PreToolUse | Matcher: Write|Edit | Timeout: 5000ms
Story: STORY-MCE-6.0 Phase 7
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
REGISTRY = REPO / ".claude" / "skills" / "chronicler" / "chronicler-registry.yaml"


def _read_registry_template_ids() -> set[str]:
    """Parse chronicler-registry.yaml to extract all declared template ids."""
    if not REGISTRY.exists():
        return set()
    text = REGISTRY.read_text(encoding="utf-8")
    # Match "  - id: <foo>" or "    id: <foo>" lines (entries under templates:)
    ids: set[str] = set()
    for line in text.splitlines():
        m = re.match(r"\s+-?\s*id:\s*['\"]?(\w+)['\"]?", line)
        if m:
            ids.add(m.group(1))
    return ids


def _find_emit_fns_in_text(text: str) -> set[str]:
    """Find all `def emit_<template_id>` function definitions in text."""
    return set(re.findall(r"def\s+emit_(\w+)\s*\(", text))


def main() -> int:
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else "{}"
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        data = {}

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only check Write/Edit ops
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return 0

    file_path_str = tool_input.get("file_path", "")
    if not file_path_str:
        return 0

    file_path = Path(file_path_str)
    try:
        rel = file_path.relative_to(REPO)
    except ValueError:
        return 0

    # Only care about pipeline files
    rel_str = str(rel)
    if not (
        rel_str.startswith("engine/intelligence/pipeline")
        or rel_str.startswith("engine\\intelligence\\pipeline")
    ):
        return 0

    # Extract proposed new content
    new_content = tool_input.get("new_string", "") or tool_input.get("content", "")
    if not new_content:
        return 0

    proposed_emits = _find_emit_fns_in_text(new_content)
    if not proposed_emits:
        return 0  # No emit_ functions in change — allow

    registry_ids = _read_registry_template_ids()
    missing = proposed_emits - registry_ids

    if missing:
        missing_list = ", ".join(sorted(missing))
        registry_rel = str(REGISTRY.relative_to(REPO))
        msg = (
            f"\nBLOCKED by chronicler_registry_guard:\n"
            f"  New emit_{{...}} functions without registry entry: {missing_list}\n"
            f"  Add corresponding 'id:' entries to: {registry_rel}\n"
            f"  This prevents drift between emitters and Chronicler renderers.\n"
            f"  Registry format:\n"
            f"    - id: <template_id>\n"
            f"      emitter_fn: <module.path.emit_fn>\n"
            f"      renderer_fn: <module.path.render_fn>\n"
            f"      schema: null  # or path to schema\n"
            f"      phase_idx: <N>\n"
            f"      required: true|false\n"
            f"      description: <short description>\n"
        )
        print(msg, file=sys.stderr)
        sys.stdout.write(json.dumps({"continue": False}) + "\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
