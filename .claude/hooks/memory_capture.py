#!/usr/bin/env python3
# CONNECTED — W1-001.6: delegates to engine/memory_manager.py
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
from datetime import datetime

STATE_PATH = os.path.join(os.path.dirname(__file__), ".memory-state.json")

# Minimum output length to consider "meaningful"
MIN_OUTPUT_LENGTH = 50

_project_root = os.environ.get(
    "CLAUDE_PROJECT_DIR", os.path.join(os.path.dirname(__file__), "..", "..")
)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from engine.memory_manager import write_memory as _mm_write

    _HAS_MEMORY_MANAGER = True
except ImportError:
    _HAS_MEMORY_MANAGER = False


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
    """Append via engine/memory_manager (canonical path)."""
    if _HAS_MEMORY_MANAGER:
        _mm_write(agent_slug, entry)
    else:
        mem_dir = os.path.join(_project_root, ".data", "agent_memory", agent_slug)
        os.makedirs(mem_dir, exist_ok=True)
        with open(os.path.join(mem_dir, "memories.jsonl"), "a") as f:
            f.write(json.dumps(entry) + "\n")


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
        agent_dir = os.path.join(_project_root, ".data", "agent_memory", agent_slug)
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
