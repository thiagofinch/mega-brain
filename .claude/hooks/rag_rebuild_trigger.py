#!/usr/bin/env python3
"""
RAG REBUILD TRIGGER -- PostToolUse Hook (Write|Edit)
====================================================
Fires when a Write or Edit completes on any file under knowledge/.
Checks staleness via staleness_checker and emits a warning if any
RAG index needs rebuilding.

This is notification-only -- it warns operators but does NOT trigger
an automatic rebuild (too expensive for a hook).

Hook:     PostToolUse (matcher: Write|Edit)
Timeout:  30000ms
Exit:     0 = no action needed, 1 = warn (stale index)
          NEVER exits with code 2 (block)

Version: 1.0.0
Date: 2026-03-16
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> None:
    """Check if a knowledge/ file was modified and warn if RAG index is stale."""
    try:
        input_data = sys.stdin.read()
    except Exception:
        sys.exit(0)

    if not input_data or not input_data.strip():
        sys.exit(0)

    try:
        hook_input = json.loads(input_data)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    # ── FAST PATH: only fire on Write/Edit ──
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    # ── FAST PATH: only fire on knowledge/ paths ──
    # Normalize to relative path for consistent matching.
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
    try:
        rel_path = str(Path(file_path).resolve().relative_to(project_dir))
    except (ValueError, OSError):
        rel_path = file_path

    if not rel_path.startswith("knowledge/") and "/knowledge/" not in file_path:
        sys.exit(0)

    # ── SLOW PATH: import staleness checker and evaluate ──
    # Add project root to sys.path so core.intelligence.rag is importable.
    project_root = str(project_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from core.intelligence.rag.staleness_checker import check_staleness
    except ImportError:
        # staleness_checker not available -- cannot check, exit silently.
        sys.exit(0)

    try:
        result = check_staleness(bucket="all")
    except Exception:
        # Any failure in staleness check -- exit silently, never block.
        sys.exit(0)

    if not result.get("is_stale", False):
        # All indexes are fresh -- nothing to warn about.
        sys.exit(0)

    # ── Build warning message ──
    stale_buckets = []
    for bucket_name, info in result.get("buckets", {}).items():
        if isinstance(info, dict) and info.get("is_stale", False):
            if info.get("index_exists", False):
                age = info.get("index_age_hours", -1)
                age_str = f"{age:.1f}h old" if age >= 0 else "age unknown"
                stale_buckets.append(f"{bucket_name} ({age_str})")
            else:
                stale_buckets.append(f"{bucket_name} (not built)")

    bucket_list = ", ".join(stale_buckets) if stale_buckets else "unknown"

    print(
        f"[rag_rebuild_trigger] RAG index is stale. "
        f"Affected buckets: {bucket_list}. "
        f"Run /rag-rebuild to update."
    )

    # Exit code 1 = warn. NEVER exit code 2 (block).
    sys.exit(1)


if __name__ == "__main__":
    main()
