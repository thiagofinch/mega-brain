#!/usr/bin/env python3
"""
agent_deprecation_guard.py -- PreToolUse Hook
==============================================

Detects when Python files are created/modified in pipeline directories
and warns if agent wrapper files (.claude/agents/kops-*.md, dops-*.md)
may need updating to reference the new/changed script.

Prevents silent agent deprecation -- the #1 risk when agents have
hardcoded script references.

Exit codes:
  0 = No agents affected (silent pass)
  1 = Warning: agents may need updating (does NOT block)
  2 = Never used (this hook never blocks)

Trigger: PreToolUse (Write, Edit)
Timeout: 30

ERROR HANDLING: fail-OPEN
  - Internal exceptions -> exit(0) ALLOW (don't block on internal errors)
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()

# Directories that, when a .py file is created/modified, may affect agents
WATCHED_DIRS = [
    "core/intelligence/pipeline/",
    "core/intelligence/pipeline/mce/",
    "core/intelligence/rag/",
    "core/intelligence/",
    "core/templates/phases/",
    ".claude/hooks/",
]

# Agent file glob patterns to scan
AGENT_GLOBS = [
    ".claude/agents/kops-*.md",
    ".claude/agents/dops-*.md",
]


def resolve_rel_path(file_path: str) -> str:
    """Convert absolute path to project-relative path."""
    try:
        return str(Path(file_path).resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return file_path


def find_watched_dir(rel_path: str) -> str:
    """Return the watched directory that contains rel_path, or empty string."""
    # Sort by length descending so more specific dirs match first
    # e.g. core/intelligence/pipeline/mce/ before core/intelligence/
    sorted_dirs = sorted(WATCHED_DIRS, key=len, reverse=True)
    for watched in sorted_dirs:
        if rel_path.startswith(watched):
            return watched
    return ""


def scan_agents(matched_dir: str, file_name: str, rel_path: str):
    """Scan agent files for references to the matched directory."""
    import glob as glob_mod

    affected = []

    for pattern in AGENT_GLOBS:
        full_pattern = str(PROJECT_ROOT / pattern)
        for agent_file in glob_mod.glob(full_pattern):
            agent_path = Path(agent_file)
            agent_name = agent_path.stem
            try:
                content = agent_path.read_text(encoding="utf-8")
            except Exception:
                continue

            # Check if agent references this directory (with or without trailing slash)
            dir_clean = matched_dir.rstrip("/")
            references_dir = dir_clean in content

            # Also check for the parent directory pattern
            # e.g., if matched_dir is core/intelligence/pipeline/mce/,
            # also check core/intelligence/pipeline/
            parent_dir = str(Path(dir_clean).parent)
            if not references_dir and parent_dir != ".":
                references_dir = parent_dir in content

            if not references_dir:
                continue

            # Check if the specific file is already referenced
            references_file = file_name in content

            # Also check if the full relative path is referenced
            if not references_file:
                references_file = rel_path in content

            if not references_file:
                affected.append(
                    {
                        "agent": agent_name,
                        "agent_file": str(agent_path.relative_to(PROJECT_ROOT)),
                        "references_dir": matched_dir,
                        "missing_ref": file_name,
                    }
                )

    return affected


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"decision": "allow"}))
            sys.exit(0)

        hook_input = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only care about Write and Edit
    if tool_name not in ("Write", "Edit"):
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    # Get the file path being written/edited
    file_path = tool_input.get("file_path", "")
    if not file_path:
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    # Only care about .py files and .md files in template dirs
    is_py = file_path.endswith(".py")
    is_template = file_path.endswith(".md") and "core/templates/" in file_path
    if not is_py and not is_template:
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    # Convert to relative path
    rel_path = resolve_rel_path(file_path)

    # Check if file is in a watched directory
    matched_dir = find_watched_dir(rel_path)
    if not matched_dir:
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    # Scan agent files for references to this directory
    file_name = Path(rel_path).name
    affected_agents = scan_agents(matched_dir, file_name, rel_path)

    if not affected_agents:
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    # Build warning message
    agent_lines = []
    for a in affected_agents:
        agent_lines.append(
            f"  - {a['agent']} ({a['agent_file']}): "
            f"references {a['references_dir']} but NOT {a['missing_ref']}"
        )
    agent_list = "\n".join(agent_lines)

    warning = {
        "warning": (
            f"[AGENT DEPRECATION GUARD] New/modified file: {rel_path}\n"
            f"These agents reference {matched_dir} but may not know about "
            f"{file_name}:\n{agent_list}\n"
            f"Consider updating these agent files to reference the new script."
        ),
    }

    print(json.dumps(warning))
    sys.exit(1)  # Warning, not block


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # fail-OPEN: internal errors must never block the developer
        print(json.dumps({"decision": "allow", "error": str(e)}))
        sys.exit(0)
