#!/usr/bin/env python3
"""
memory_capture.py -- PostToolUse Hook
=====================================
Captures agent execution results and writes to agent memory.
Only captures kops-* and dops-* agent completions.

Exit codes:
  0 = Always (never blocks, never warns)
Trigger: PostToolUse (Agent)
Timeout: 30
"""
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MEMORY_DIR = PROJECT_ROOT / ".data" / "agent_memory"

TRACKED_PREFIXES = ("kops-", "dops-", "devops-megabrain")


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        hook_input = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Agent":
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    tool_result = hook_input.get("tool_result", "")

    agent_name = tool_input.get("subagent_type", "")
    if not agent_name or not any(agent_name.startswith(p) for p in TRACKED_PREFIXES):
        sys.exit(0)

    # Build memory entry
    prompt = tool_input.get("prompt", "")
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "agent": agent_name,
        "task_summary": prompt[:200],
        "result_summary": str(tool_result)[:300] if tool_result else "",
        "type": "execution",
        "importance": 0.5,
    }

    # Write to agent memory
    agent_dir = MEMORY_DIR / agent_name
    agent_dir.mkdir(parents=True, exist_ok=True)
    memory_file = agent_dir / "memories.jsonl"

    try:
        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Fail silently

    sys.exit(0)


if __name__ == "__main__":
    main()
