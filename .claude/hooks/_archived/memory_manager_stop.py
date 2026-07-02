# ARCHIVED 2026-04-16 — W1-001.6
# Logic consolidated into engine/memory_manager.py
# Replacement stub in .claude/hooks/memory_manager_stop.py

#!/usr/bin/env python3
"""
memory_manager_stop.py — Stop hook
On session end: scans all agent MEMORY.md files, consolidates near-duplicates
using Jaccard similarity, prunes entries over 200 lines per agent, and reports
what was cleaned.

Fail-open: always exits 0.
"""

import json
import os
import sys
from datetime import datetime

AGENT_MEMORY_ROOT = os.path.join(
    os.environ.get("CLAUDE_PROJECT_DIR", os.path.join(os.path.dirname(__file__), "..", "..")),
    ".data",
    "agent_memory",
)
STATE_PATH = os.path.join(os.path.dirname(__file__), ".memory-state.json")
MAX_LINES_PER_AGENT = 200
JACCARD_THRESHOLD = 0.7  # Lines with >= 70% word overlap are near-duplicates


def jaccard_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity between two strings (word-level)."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def deduplicate_lines(lines: list) -> list:
    """Remove near-duplicate lines using Jaccard similarity."""
    if len(lines) <= 1:
        return lines
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "---":
            result.append(line)
            continue
        # Check against recent lines (last 20) for duplicates
        is_dup = False
        check_range = result[-20:] if len(result) > 20 else result
        for existing in check_range:
            existing_stripped = existing.strip()
            if not existing_stripped:
                continue
            if jaccard_similarity(stripped, existing_stripped) >= JACCARD_THRESHOLD:
                is_dup = True
                break
        if not is_dup:
            result.append(line)
    return result


def process_memory_file(mem_path: str) -> dict:
    """Process a single MEMORY.md: deduplicate and prune."""
    stats = {"path": mem_path, "before": 0, "after": 0, "removed": 0}
    try:
        with open(mem_path) as f:
            lines = f.readlines()
        stats["before"] = len(lines)

        if len(lines) <= 5:
            stats["after"] = len(lines)
            return stats

        # Find header end
        header_end = 0
        for i, line in enumerate(lines):
            if line.strip() == "---" and i > 0:
                header_end = i + 1
                break

        header = lines[:header_end]
        body = lines[header_end:]

        # Deduplicate body
        body = deduplicate_lines(body)

        # Prune to max lines
        max_body = MAX_LINES_PER_AGENT - len(header)
        if len(body) > max_body:
            body = body[-max_body:]

        final = header + body
        stats["after"] = len(final)
        stats["removed"] = stats["before"] - stats["after"]

        if stats["removed"] > 0:
            with open(mem_path, "w") as f:
                f.writelines(final)

    except OSError:
        pass

    return stats


def reset_state():
    """Reset session state for next session."""
    try:
        state = {
            "prompt_count": 0,
            "active_agent": None,
            "session_start": None,
            "last_cleanup": datetime.now().isoformat(),
        }
        with open(STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
    except OSError:
        pass


def main():
    try:
        # Scan all agent memory directories
        if not os.path.isdir(AGENT_MEMORY_ROOT):
            return

        report = []
        for agent_dir in sorted(os.listdir(AGENT_MEMORY_ROOT)):
            agent_path = os.path.join(AGENT_MEMORY_ROOT, agent_dir)
            if not os.path.isdir(agent_path):
                continue
            mem_path = os.path.join(agent_path, "MEMORY.md")
            if os.path.exists(mem_path):
                stats = process_memory_file(mem_path)
                if stats["removed"] > 0:
                    report.append(stats)

        # Reset session state
        reset_state()

        # Report what was cleaned (via stderr for visibility)
        if report:
            summary = []
            for r in report:
                agent = os.path.basename(os.path.dirname(r["path"]))
                summary.append(
                    f"  {agent}: {r['before']} -> {r['after']} lines "
                    f"(-{r['removed']} duplicates/overflow)"
                )
            msg = "[memory-cleanup] Session end cleanup:\n" + "\n".join(summary)
            print(msg, file=sys.stderr)

    except Exception:
        pass  # fail-open


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
