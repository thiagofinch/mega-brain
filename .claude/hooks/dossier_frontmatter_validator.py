#!/usr/bin/env python3
"""
dossier_frontmatter_validator.py
PostToolUse hook — V1 soft warn (no block).

Fires after Edit or Write on any file matching:
    knowledge/external/dossiers/themes/*.md

Checks:
    1. File starts with ---  (has frontmatter)
    2. Frontmatter contains required fields: slug, theme, category, last_updated

Emits WARN to stderr. Does NOT block (exit 0 always).

Story: MCE-12.7
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = {"slug", "theme", "category", "last_updated"}

THEMES_GLOB = "knowledge/external/dossiers/themes/"


def is_theme_dossier(file_path: str) -> bool:
    """Return True if the edited/written file is a theme dossier."""
    norm = file_path.replace("\\", "/")
    return THEMES_GLOB in norm and norm.endswith(".md")


def extract_frontmatter_fields(content: str) -> set[str]:
    """Return set of field names found in the YAML frontmatter block."""
    if not content.startswith("---"):
        return set()
    # Find closing ---
    end = content.find("\n---", 3)
    if end == -1:
        return set()
    fm_block = content[3:end]
    found: set[str] = set()
    for line in fm_block.splitlines():
        m = re.match(r"^([a-z_]+):", line)
        if m:
            found.add(m.group(1))
    return found


def main() -> None:
    # PostToolUse sends hook input via stdin as JSON
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    # Extract file path from hook payload
    file_path: str = ""

    # Claude Code PostToolUse payload structure
    tool_input = data.get("tool_input", {})
    if isinstance(tool_input, dict):
        file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    # Fallback: check tool_result if present
    if not file_path:
        tool_result = data.get("tool_result", {})
        if isinstance(tool_result, dict):
            file_path = tool_result.get("file_path", "")

    if not file_path:
        sys.exit(0)

    if not is_theme_dossier(file_path):
        sys.exit(0)

    # Resolve absolute path
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", str(Path.cwd()))
    abs_path = Path(file_path) if Path(file_path).is_absolute() else Path(project_dir) / file_path

    if not abs_path.exists():
        sys.exit(0)

    try:
        content = abs_path.read_text(encoding="utf-8")
    except Exception:
        sys.exit(0)

    # Check 1: has frontmatter
    if not content.startswith("---"):
        print(
            f"[dossier_frontmatter_validator] WARN: {abs_path.name} "
            f"has no YAML frontmatter. Run: python3 scripts/migrate_dossier_frontmatter.py",
            file=sys.stderr,
        )
        sys.exit(0)

    # Check 2: required fields present
    found_fields = extract_frontmatter_fields(content)
    missing = REQUIRED_FIELDS - found_fields
    if missing:
        print(
            f"[dossier_frontmatter_validator] WARN: {abs_path.name} "
            f"frontmatter missing required fields: {sorted(missing)}",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
