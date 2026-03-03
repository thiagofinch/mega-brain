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
- Stop: Update with first prompt (captured from continuous_save JSONL)

OUTPUT: .claude/sessions/SESSION-INDEX.json

Author: JARVIS
Version: 1.0.0
Date: 2026-03-01
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path


# ================================
# CONFIGURATION
# ================================

PROJECT_DIR = Path(os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd()))
SESSIONS_DIR = PROJECT_DIR / ".claude" / "sessions"
INDEX_FILE = SESSIONS_DIR / "SESSION-INDEX.json"
CURRENT_JSONL = SESSIONS_DIR / "current.jsonl"

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
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and "sessions" in data:
                    return data
        except (json.JSONDecodeError, IOError):
            pass
    return {"sessions": [], "version": "1.0.0"}


def save_index(index_data):
    """Save session index, trimming to MAX_INDEX_ENTRIES."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Keep only recent entries
    if len(index_data["sessions"]) > MAX_INDEX_ENTRIES:
        index_data["sessions"] = index_data["sessions"][-MAX_INDEX_ENTRIES:]

    index_data["last_updated"] = datetime.now().isoformat()

    try:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
    except IOError:
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


def extract_first_prompt_from_jsonl():
    """Extract first user prompt from current.jsonl."""
    if not CURRENT_JSONL.exists():
        return None

    try:
        with open(CURRENT_JSONL, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get('type') == 'user_message':
                        content = entry.get('content', '')
                        # Return first 200 chars for searchability
                        return content[:200].strip()
                except json.JSONDecodeError:
                    continue
    except IOError:
        pass

    return None


# ================================
# EVENT HANDLERS
# ================================

def on_session_start(hook_input):
    """Register new session on SessionStart."""
    session_id = hook_input.get('session_id', '')

    if not session_id or session_id == 'unknown':
        return

    index = load_index()

    # Check if already registered (avoid duplicates on re-trigger)
    existing = find_session(index, session_id)
    if existing:
        # Update started timestamp
        existing["last_activity"] = datetime.now().isoformat()
        save_index(index)
        return

    # Create new entry
    transcript_path = find_transcript_path(session_id)

    entry = {
        "uuid": session_id,
        "started": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
        "first_prompt": None,  # Will be filled on Stop
        "transcript": transcript_path,
        "cwd": str(PROJECT_DIR)
    }

    index["sessions"].append(entry)
    save_index(index)


def on_stop(hook_input):
    """Update session on Stop with first prompt and last activity."""
    session_id = hook_input.get('session_id', '')

    if not session_id or session_id == 'unknown':
        return

    index = load_index()
    session = find_session(index, session_id)

    if not session:
        # Session wasn't registered (hook added mid-session)
        # Register it now
        on_session_start(hook_input)
        index = load_index()
        session = find_session(index, session_id)
        if not session:
            return

    # Update last activity
    session["last_activity"] = datetime.now().isoformat()

    # Try to capture first prompt if not already set
    if not session.get("first_prompt"):
        first_prompt = extract_first_prompt_from_jsonl()
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
    """Detect which event triggered this hook."""
    # If there's a stop_reason or the hook is called from Stop event,
    # we treat it as Stop. Otherwise, SessionStart.
    # We use the presence of 'stop_reason' or the absence of 'prompt'
    # combined with existing session in index as heuristic.

    session_id = hook_input.get('session_id', '')

    # Check if this session is already in the index
    if session_id:
        index = load_index()
        existing = find_session(index, session_id)
        if existing:
            # Already registered = this is a Stop event
            return 'stop'

    return 'session_start'


def main():
    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data.strip() else {}
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    event = detect_event(hook_input)

    if event == 'session_start':
        on_session_start(hook_input)
    else:
        on_stop(hook_input)

    # Output for hook system
    print(json.dumps({"continue": True}))


if __name__ == '__main__':
    main()
