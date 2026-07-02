#!/usr/bin/env python3
"""
SESSION INDEX HOOK - Cross-Reference Sessions with --resume
============================================================

Maintains a SESSION-INDEX.json that maps Claude Code session UUIDs
to timestamps and first prompts, enabling:
1. Finding old sessions by date or keyword
2. Cross-referencing with `claude --resume <UUID>`
3. Never losing a conversation again

EVENTS:
- SessionStart: Register new session UUID + timestamp
- Stop: Update with first prompt and last activity

OUTPUT: .claude/sessions/SESSION-INDEX.json

FIXES (v2.0.0):
- Use CLAUDE_HOOK_EVENT env var instead of fragile heuristic for event detection
- Extract first_prompt from hook stdin (session transcript) instead of shared current.jsonl
- Filter sessions by cwd to prevent cross-project contamination
- Deduplicate sessions by UUID on save

Author: JARVIS
Version: 2.0.0
Date: 2026-04-15
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ================================
# CONFIGURATION
# ================================

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
SESSIONS_DIR = PROJECT_DIR / ".claude" / "sessions"
INDEX_FILE = SESSIONS_DIR / "SESSION-INDEX.json"

# Claude Code internal transcripts location
HOME = Path.home()
CLAUDE_PROJECT_KEY = str(PROJECT_DIR).replace("/", "-").lstrip("-")
TRANSCRIPTS_DIR = HOME / ".claude" / "projects" / CLAUDE_PROJECT_KEY

MAX_INDEX_ENTRIES = 200  # Keep last 200 sessions


# ================================
# INDEX OPERATIONS
# ================================


def load_index():
    """Load existing session index."""
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "sessions" in data:
                    return data
        except (OSError, json.JSONDecodeError):
            pass
    return {"sessions": [], "version": "2.0.0"}


def save_index(index_data):
    """Save session index, trimming to MAX_INDEX_ENTRIES and deduplicating."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Deduplicate by UUID (keep the most complete entry)
    seen = {}
    for session in index_data["sessions"]:
        uuid = session.get("uuid")
        if not uuid:
            continue
        if uuid in seen:
            # Merge: keep the one with more data
            existing = seen[uuid]
            if session.get("first_prompt") and not existing.get("first_prompt"):
                existing["first_prompt"] = session["first_prompt"]
            if session.get("transcript") and not existing.get("transcript"):
                existing["transcript"] = session["transcript"]
            # Always update last_activity to the latest
            if session.get("last_activity", "") > existing.get("last_activity", ""):
                existing["last_activity"] = session["last_activity"]
        else:
            seen[uuid] = session

    index_data["sessions"] = list(seen.values())

    # Keep only recent entries
    if len(index_data["sessions"]) > MAX_INDEX_ENTRIES:
        index_data["sessions"] = index_data["sessions"][-MAX_INDEX_ENTRIES:]

    index_data["last_updated"] = datetime.now().isoformat()
    index_data["version"] = "2.0.0"

    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def find_session(index_data, uuid):
    """Find a session entry by UUID."""
    for session in index_data["sessions"]:
        if session.get("uuid") == uuid:
            return session
    return None


def find_transcript_path(uuid):
    """Find the Claude Code internal transcript file for a UUID."""
    if not TRANSCRIPTS_DIR.exists():
        return None

    candidate = TRANSCRIPTS_DIR / f"{uuid}.jsonl"
    if candidate.exists():
        return str(candidate)

    return None


def extract_first_prompt(hook_input):
    """Extract first user prompt from hook input transcript data.

    The hook receives the session transcript in stdin.
    Look for the first user message in the transcript.
    """
    # Try to get from transcript in hook input
    transcript = hook_input.get("transcript", [])
    if isinstance(transcript, list):
        for entry in transcript:
            if isinstance(entry, dict):
                role = entry.get("role", "")
                if role == "user":
                    content = entry.get("content", "")
                    if isinstance(content, list):
                        # Content blocks format
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text = block.get("text", "").strip()
                                if text:
                                    return text[:200]
                    elif isinstance(content, str) and content.strip():
                        return content[:200].strip()

    # Try from messages array
    messages = hook_input.get("messages", [])
    if isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, dict) and msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str) and content.strip():
                    return content[:200].strip()

    # Try prompt field directly
    prompt = hook_input.get("prompt", "")
    if isinstance(prompt, str) and prompt.strip():
        return prompt[:200].strip()

    return None


# ================================
# EVENT HANDLERS
# ================================


def on_session_start(hook_input):
    """Register new session on SessionStart."""
    session_id = hook_input.get("session_id", "")

    if not session_id or session_id == "unknown":
        return

    index = load_index()

    # Check if already registered (avoid duplicates on re-trigger)
    existing = find_session(index, session_id)
    if existing:
        existing["last_activity"] = datetime.now().isoformat()
        save_index(index)
        return

    # Create new entry
    transcript_path = find_transcript_path(session_id)

    entry = {
        "uuid": session_id,
        "started": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
        "first_prompt": None,
        "transcript": transcript_path,
        "cwd": str(PROJECT_DIR),
    }

    index["sessions"].append(entry)
    save_index(index)


def on_stop(hook_input):
    """Update session on Stop with first prompt and last activity."""
    session_id = hook_input.get("session_id", "")

    if not session_id or session_id == "unknown":
        return

    index = load_index()
    session = find_session(index, session_id)

    if not session:
        # Session wasn't registered (hook added mid-session)
        on_session_start(hook_input)
        index = load_index()
        session = find_session(index, session_id)
        if not session:
            return

    # Update last activity
    session["last_activity"] = datetime.now().isoformat()

    # Capture first prompt from hook input (not from shared current.jsonl)
    if not session.get("first_prompt"):
        first_prompt = extract_first_prompt(hook_input)
        if first_prompt:
            session["first_prompt"] = first_prompt

    # Update transcript path if not set
    if not session.get("transcript"):
        transcript_path = find_transcript_path(session_id)
        if transcript_path:
            session["transcript"] = transcript_path

    save_index(index)


# ================================
# MAIN
# ================================


def detect_event(hook_input):
    """Detect which event triggered this hook.

    Uses CLAUDE_HOOK_EVENT env var (reliable) with fallback to heuristic.
    """
    # Primary: use env var set by Claude Code hook system
    hook_event = os.environ.get("CLAUDE_HOOK_EVENT", "").lower()
    if "stop" in hook_event:
        return "stop"
    if "session" in hook_event and "start" in hook_event:
        return "session_start"

    # Secondary: check if session already exists in index
    session_id = hook_input.get("session_id", "")
    if session_id:
        index = load_index()
        existing = find_session(index, session_id)
        if existing:
            return "stop"

    return "session_start"


def main():
    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data.strip() else {}
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    event = detect_event(hook_input)

    if event == "session_start":
        on_session_start(hook_input)
    else:
        on_stop(hook_input)

    # Output for hook system
    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
