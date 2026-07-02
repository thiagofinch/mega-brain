#!/usr/bin/env python3
"""
Memory Persistence Hook — Supabase Auto-Save
=============================================
Flushes session observations to Supabase on session Stop.
Loads relevant memories on SessionStart.

Hook events:
  Stop → flush buffer to Supabase observations table
  SessionStart → load recent observations as context hints

Feature flag: MEMORY_SUPABASE_ENABLED=true in .env
Graceful degradation: if Supabase unavailable, silently skips.

Story: RT-MEM-2026-04-11
"""

import json
import os
import sys
import time
from pathlib import Path

PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
BUFFER_PATH = Path(PROJECT_DIR) / ".data" / "memory_buffer.jsonl"
STATE_PATH = Path(PROJECT_DIR) / ".claude" / "hooks" / ".memory-persistence-state.json"


def _add_engine_to_path():
    """Add project root to sys.path so engine imports work."""
    root = Path(PROJECT_DIR)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _load_state() -> dict:
    """Load persistence state."""
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_flush": 0, "total_saved": 0, "sessions": 0}


def _save_state(state: dict):
    """Save persistence state."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _read_buffer() -> list[dict]:
    """Read buffered observations from JSONL file."""
    if not BUFFER_PATH.exists():
        return []
    entries = []
    for line in BUFFER_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _clear_buffer():
    """Clear the observation buffer after successful flush."""
    if BUFFER_PATH.exists():
        BUFFER_PATH.write_text("", encoding="utf-8")


def handle_stop(hook_input: dict) -> dict:
    """Stop hook: flush buffered observations to Supabase."""
    _add_engine_to_path()

    try:
        from engine.providers.memory_supabase import is_enabled, save_observations_batch

        if not is_enabled():
            return {"result": "skip", "reason": "MEMORY_SUPABASE_ENABLED != true"}

        buffer = _read_buffer()
        if not buffer:
            return {"result": "skip", "reason": "empty buffer"}

        saved = save_observations_batch(buffer)
        if saved > 0:
            _clear_buffer()
            state = _load_state()
            state["last_flush"] = time.time()
            state["total_saved"] += saved
            state["sessions"] += 1
            _save_state(state)

        return {"result": "success", "flushed": saved, "buffered": len(buffer)}

    except Exception as e:
        return {"result": "error", "error": str(e)}


def handle_session_start(hook_input: dict) -> dict:
    """SessionStart hook: report memory system status."""
    _add_engine_to_path()

    try:
        from engine.providers.memory_supabase import health_check, is_enabled

        if not is_enabled():
            return {"result": "skip"}

        health = health_check()
        state = _load_state()

        status = "OK" if health["ok"] else "DEGRADED"
        msg = f"[Memory] {status} | {state['total_saved']} obs saved across {state['sessions']} sessions"

        print(json.dumps({"message": msg}))
        return {"result": "success", "status": status}

    except Exception as e:
        return {"result": "error", "error": str(e)}


# ---------------------------------------------------------------------------
# BUFFER API (called by other hooks to queue observations)
# ---------------------------------------------------------------------------


def buffer_observation(
    title: str,
    content: str,
    observation_type: str = "general",
    importance: str = "MEDIUM",
    session_id: str = None,
):
    """Append an observation to the local buffer (flushed on Stop).

    Call this from other hooks (e.g., memory_updater.py) when they
    detect decisions, corrections, or patterns.
    """
    BUFFER_PATH.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "title": title,
        "content": content,
        "observation_type": observation_type,
        "importance": importance,
        "session_id": session_id or f"session-{int(time.time())}",
        "source_type": "hook_auto_capture",
        "buffered_at": time.time(),
    }

    with open(BUFFER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# MAIN (hook entry point)
# ---------------------------------------------------------------------------


def main():
    """Entry point called by Claude Code hook system."""
    try:
        raw = sys.stdin.read()
        hook_input = json.loads(raw) if raw.strip() else {}
    except Exception:
        hook_input = {}

    # Detect which event triggered us
    event = hook_input.get("event", os.environ.get("CLAUDE_HOOK_EVENT", ""))

    if event == "Stop":
        result = handle_stop(hook_input)
    elif event == "SessionStart":
        result = handle_session_start(hook_input)
    else:
        # Called directly — assume stop (flush)
        result = handle_stop(hook_input)

    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
