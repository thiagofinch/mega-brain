#!/usr/bin/env python3
"""
Agent Memory Persister Hook v1.0 (Mega Brain)

Persists session learnings to the active agent's memory file at session end.
Adapted from: aios-core/.claude/hooks/agent_memory_persister.py

LIFECYCLE:
  READ:  skill_router.py (UserPromptSubmit) -> loads .claude/agent-memory/{slug}/MEMORY.md
  WRITE: post_batch_cascading.py (PostToolUse) -> writes batch learnings
  WRITE: THIS HOOK (SessionEnd) -> writes session summary

BEHAVIOR:
- Reads active agent from STATE.json (session.agent_active)
- Appends a session entry to .claude/agent-memory/{slug}/MEMORY.md
- Creates the memory file if it doesn't exist
- Fail-open: NEVER blocks session end

EXIT CODES:
- 0: Always (advisory only, never blocks)

Hook Type: SessionEnd
"""

import json
import sys
import os
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
STATE_DIR = PROJECT_ROOT / ".claude" / "jarvis"
STATE_FILE = STATE_DIR / "STATE.json"
AGENT_MEMORY_DIR = PROJECT_ROOT / ".claude" / "agent-memory"

# Internal time budget (ms)
INTERNAL_TIMEOUT_MS = 3000


def load_state() -> dict:
    """Load current state."""
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def get_active_agent(state: dict) -> str | None:
    """Extract active agent slug from STATE.json."""
    # Check session.agent_active (set by skill_router/post_tool_use)
    session = state.get("session", {})
    agent = session.get("agent_active")
    if agent and isinstance(agent, str) and agent.strip():
        return agent.strip()
    return None


def get_session_metadata(state: dict) -> dict:
    """Extract useful session metadata for the memory entry."""
    accumulated = state.get("accumulated", {})
    pipeline = state.get("pipeline", {})

    return {
        "session_id": state.get("session_id", "unknown"),
        "ended_at": datetime.now().isoformat(),
        "files_processed": pipeline.get("files_processed", 0),
        "progress_percent": accumulated.get("progress_percent", 0),
        "current_step": pipeline.get("current_step", "unknown"),
    }


def get_memory_path(agent_slug: str) -> Path:
    """Resolve agent memory path."""
    return AGENT_MEMORY_DIR / agent_slug / "MEMORY.md"


def create_memory_file(memory_path: Path, agent_slug: str) -> None:
    """Create a new MEMORY.md with header."""
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    header = f"""# {agent_slug} - Agent Memory

> Auto-managed by hooks. Do not edit manually.
> READ: skill_router.py (on activation)
> WRITE: agent_memory_persister.py (on session end)

---

"""
    memory_path.write_text(header, encoding='utf-8')


def build_session_entry(agent_slug: str, metadata: dict) -> str:
    """Build a markdown session entry to append to MEMORY.md."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M")
    session_id_short = metadata.get("session_id", "unknown")[:8]

    lines = [
        f"## Session {date_str} [{session_id_short}]",
        "",
        f"- **Step:** {metadata.get('current_step', 'unknown')}",
        f"- **Progress:** {metadata.get('progress_percent', 0)}%",
        f"- **Files processed:** {metadata.get('files_processed', 0)}",
        "",
        "---",
        "",
    ]

    return "\n".join(lines)


def append_to_memory(memory_path: Path, entry: str) -> bool:
    """Append session entry to MEMORY.md, trimming if over 200 lines."""
    try:
        if not memory_path.exists():
            return False

        content = memory_path.read_text(encoding='utf-8')
        new_content = content.rstrip('\n') + '\n\n' + entry

        final_lines = new_content.split('\n')
        if len(final_lines) > 200:
            header = final_lines[:20]
            recent = final_lines[-175:]
            final_lines = header + ["", "<!-- Older entries trimmed by agent_memory_persister.py -->", ""] + recent

        memory_path.write_text('\n'.join(final_lines), encoding='utf-8')
        return True
    except Exception:
        return False


def check_timeout(start_time):
    """Check if we've exceeded internal time budget."""
    elapsed_ms = (time.time() - start_time) * 1000
    return elapsed_ms > INTERNAL_TIMEOUT_MS


def main():
    """Main hook execution with timeout protection."""
    start_time = time.time()

    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data.strip() else {}

        state = load_state()
        if not state:
            print(json.dumps({"continue": True}))
            return

        raw_slug = get_active_agent(state)
        if not raw_slug:
            print(json.dumps({"continue": True}))
            return

        if check_timeout(start_time):
            print(json.dumps({
                "continue": True,
                "feedback": "[MB] Memory persister skipped (timeout after state load)"
            }))
            return

        agent_slug = raw_slug
        memory_path = get_memory_path(agent_slug)

        if not memory_path.exists():
            create_memory_file(memory_path, agent_slug)

        if check_timeout(start_time):
            print(json.dumps({
                "continue": True,
                "feedback": "[MB] Memory persister skipped (timeout before entry build)"
            }))
            return

        metadata = get_session_metadata(state)
        entry = build_session_entry(agent_slug, metadata)
        success = append_to_memory(memory_path, entry)

        output = {"continue": True}

        if success:
            elapsed_ms = round((time.time() - start_time) * 1000)
            output["feedback"] = f"[MB] Session memory persisted for @{agent_slug} ({elapsed_ms}ms)"
        else:
            output["feedback"] = f"[MB] Could not persist memory for @{agent_slug}"

        print(json.dumps(output))

    except Exception as e:
        print(json.dumps({
            "continue": True,
            "feedback": f"[MB] Memory persister error (fail-open): {str(e)}"
        }))


if __name__ == "__main__":
    main()
