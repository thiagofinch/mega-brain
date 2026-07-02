"""
Quiet Hours Gate — Stop hook that records (does NOT block) sessions during quiet hours.

During quiet hours (default 00:00-07:00) the hook logs a single end-of-session
breadcrumb to .data/held-messages.jsonl so the morning briefing knows that
work happened overnight. It NEVER blocks the Stop event — blocking on Stop
forces Claude into a continuation loop (the harness interprets exit 2 as
"keep going"), which previously generated an infinite respond-block-respond
cycle.

Outside quiet hours the hook is a no-op. Idempotency is preserved with a
per-session marker file so the same session is only logged once even if
Stop fires multiple times in the window.

Config via env vars:
    QUIET_HOURS_START  (int, default 0)  — hour to start logging (inclusive)
    QUIET_HOURS_END    (int, default 7)  — hour to stop logging (exclusive)

Exit codes: ALWAYS 0. Stop hooks must never block.

Story: W4-001.3
Fix: 2026-05-04 — replaced exit(2)/decision:block with exit(0) silent log
     after infinite-loop incident reported by o fundador. Stop hooks returning
     exit 2 cause Claude Code to immediately re-prompt the assistant,
     producing dozens of "Quiet hours active" entries per minute.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────
QUIET_START = int(os.environ.get("QUIET_HOURS_START", "0"))
QUIET_END = int(os.environ.get("QUIET_HOURS_END", "7"))

PROJECT_ROOT = Path(
    os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parent.parent.parent)
)
HELD_MESSAGES_PATH = PROJECT_ROOT / ".data" / "held-messages.jsonl"
SESSION_MARKER_DIR = PROJECT_ROOT / ".data" / "quiet-hours-marks"


def is_quiet_hours(now=None):
    """Check if current time falls within quiet hours window."""
    hour = (now or datetime.now()).hour
    if QUIET_START < QUIET_END:
        # Simple range: e.g. 0-7
        return QUIET_START <= hour < QUIET_END
    else:
        # Wrapping range: e.g. 22-6 means 22,23,0,1,2,3,4,5
        return hour >= QUIET_START or hour < QUIET_END


def already_logged(session_id: str) -> bool:
    """Idempotency: return True if this session was already logged today."""
    if not session_id or session_id == "unknown":
        return False
    SESSION_MARKER_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    marker = SESSION_MARKER_DIR / f"{today}__{session_id}.mark"
    if marker.exists():
        return True
    try:
        marker.touch()
    except OSError:
        # Best effort — if filesystem fails, allow the log to proceed
        return False
    return False


def enqueue_breadcrumb(input_data: dict) -> None:
    """Append a single end-of-session breadcrumb to held-messages.jsonl."""
    HELD_MESSAGES_PATH.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool_name": input_data.get("tool_name", ""),
        "tool_input": input_data.get("tool_input", {}),
        "session_id": input_data.get("session_id", os.environ.get("CLAUDE_SESSION_ID", "unknown")),
        "quiet_window": f"{QUIET_START:02d}:00-{QUIET_END:02d}:00",
        "status": "session-ended-during-quiet-hours",
    }

    try:
        with open(HELD_MESSAGES_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # Never fail the Stop event because of a logging issue.
        pass


def main():
    try:
        raw = sys.stdin.read()
        input_data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, Exception):
        input_data = {}

    if not is_quiet_hours():
        sys.exit(0)

    session_id = input_data.get("session_id", os.environ.get("CLAUDE_SESSION_ID", "unknown"))
    if not already_logged(session_id):
        enqueue_breadcrumb(input_data)

    # ALWAYS exit 0. Never block Stop — blocking causes infinite re-prompt loop.
    sys.exit(0)


if __name__ == "__main__":
    main()
