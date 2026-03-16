#!/usr/bin/env python3
"""
Drift Detection Hook — Warn when agent source files are edited.

PostToolUse hook that detects when Edit or Write tools modify an agent
source file (AGENT.md, SOUL.md, MEMORY.md) and emits a warning with
the recompile command.

Fast path: <5ms exit for non-matching paths (95%+ of edits).
Always exits 0 (info only, never blocks).

Hook: PostToolUse | Timeout: 5000ms | Version: 1.0.0
"""

import json
import sys


def main() -> None:
    """Check if edited file is an agent source and warn if stale."""
    try:
        input_data = sys.stdin.read()
    except Exception:
        sys.exit(0)

    if not input_data:
        sys.exit(0)

    try:
        hook_input = json.loads(input_data)
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    # ── FAST PATH: skip non-agent files ──
    if "/agents/" not in file_path:
        sys.exit(0)

    # Only trigger for actual source files
    source_files = ("AGENT.md", "SOUL.md", "MEMORY.md")
    if not file_path.endswith(source_files):
        sys.exit(0)

    # Skip templates
    if "/_templates/" in file_path:
        sys.exit(0)

    # ── SLOW PATH: extract slug and category ──
    # Path format: .../agents/{category}/.../{slug}/{FILE}.md
    parts = file_path.split("/agents/")
    if len(parts) < 2:
        sys.exit(0)

    after_agents = parts[1]  # e.g. "external/liam-ottley/SOUL.md"
    segments = after_agents.split("/")

    if len(segments) < 2:
        sys.exit(0)

    # Category is the first segment
    category = segments[0]

    # Slug is the parent directory of the source file
    # Remove the filename to get the directory path
    dir_segments = segments[:-1]  # remove "SOUL.md" etc.
    slug = dir_segments[-1]  # last directory segment is the slug

    # Skip if slug looks like a category folder, not an agent
    skip_slugs = {"external", "cargo", "business", "personal", "system",
                  "conclave", "sales", "c-level", "marketing", "collaborators",
                  "finance", "_unclassified", "dev-ops", "knowledge-ops"}
    if slug in skip_slugs:
        sys.exit(0)

    filename = segments[-1]

    print(
        f"[recompile_alert] {filename} modified for agent '{slug}'. "
        f"Command file may be stale. Run:\n"
        f"  python3 -m core.intelligence.agents.activation_generator "
        f"generate {slug} --category {category} --force"
    )


if __name__ == "__main__":
    main()
