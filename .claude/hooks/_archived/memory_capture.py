# ARCHIVED 2026-04-16 — W1-001.6
# Logic consolidated into engine/memory_manager.py
# Replacement stub in .claude/hooks/memory_capture.py

#!/usr/bin/env python3
"""
memory_capture.py — PostToolUse hook (Agent tool)
Captures when the Agent tool is used (subagent completions) and writes
execution summaries to .data/agent_memory/{agent}/memories.jsonl.

Only tracks meaningful completions (skips trivial ones).

Fail-open: always exits 0.
"""

import json
import os
import sys
import time
from datetime import datetime

AGENT_MEMORY_ROOT = os.path.join(
    os.environ.get("CLAUDE_PROJECT_DIR", os.path.join(os.path.dirname(__file__), "..", "..")),
    ".data",
    "agent_memory",
)
STATE_PATH = os.path.join(os.path.dirname(__file__), ".memory-state.json")

# Minimum output length to consider "meaningful"
MIN_OUTPUT_LENGTH = 50
MAX_JSONL_ENTRIES = 500


def load_state() -> dict:
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"prompt_count": 0, "active_agent": None}


def detect_agent_from_tool(tool_input: dict) -> str:
    """Try to detect which agent was invoked from the tool input."""
    # The Agent tool typically has a 'skill' or 'agent' field
    for key in ("skill", "agent", "name", "agent_id"):
        val = tool_input.get(key, "")
        if val:
            return val.lower().replace("@", "").strip()
    # Try to parse from prompt/instruction
    prompt = tool_input.get("prompt", tool_input.get("instruction", ""))
    if prompt:
        agent_map = {
            "@dev": "dev",
            "@qa": "qa",
            "@architect": "architect",
            "@pm": "pm",
            "@po": "po",
            "@sm": "sm",
            "@analyst": "analyst",
            "@data-engineer": "data-engineer",
            "@ux-design-expert": "ux-design-expert",
            "@devops": "devops",
            "@master": "mega-brain-master",
        }
        for trigger, slug in agent_map.items():
            if trigger in prompt.lower():
                return slug
    return ""


def write_memory_entry(agent_slug: str, entry: dict) -> None:
    """Append a JSONL entry to the agent's memories file."""
    mem_dir = os.path.join(AGENT_MEMORY_ROOT, agent_slug)
    os.makedirs(mem_dir, exist_ok=True)
    jsonl_path = os.path.join(mem_dir, "memories.jsonl")

    with open(jsonl_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Trim if over limit
    try:
        with open(jsonl_path) as f:
            lines = f.readlines()
        if len(lines) > MAX_JSONL_ENTRIES:
            with open(jsonl_path, "w") as f:
                f.writelines(lines[-MAX_JSONL_ENTRIES:])
    except OSError:
        pass


def main():
    try:
        raw = ""
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
        if not raw.strip():
            return

        input_data = {}
        try:
            input_data = json.loads(raw)
        except json.JSONDecodeError:
            return

        tool_name = input_data.get("tool_name", "")

        # Only act on Agent tool
        if tool_name != "Agent":
            return

        tool_input = input_data.get("tool_input", {})
        tool_output = input_data.get("tool_output", "")

        # Skip trivial completions
        output_str = str(tool_output)
        if len(output_str) < MIN_OUTPUT_LENGTH:
            return

        # Detect which agent was involved
        agent_slug = detect_agent_from_tool(tool_input)
        if not agent_slug:
            # Fall back to active agent from state
            state = load_state()
            agent_slug = state.get("active_agent", "")
        if not agent_slug:
            return

        # Verify agent directory exists (or create it)
        agent_dir = os.path.join(AGENT_MEMORY_ROOT, agent_slug)
        if not os.path.isdir(agent_dir):
            os.makedirs(agent_dir, exist_ok=True)

        # Build entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_slug,
            "tool": tool_name,
            "summary": output_str[:300],  # Truncate for storage
            "input_preview": str(tool_input)[:200],
        }

        write_memory_entry(agent_slug, entry)

    except Exception:
        pass  # fail-open


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
