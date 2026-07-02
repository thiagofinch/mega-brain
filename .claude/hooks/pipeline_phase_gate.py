#!/usr/bin/env python3
"""
pipeline_phase_gate.py -- Phase Gate Enforcement (WARN, NOT BLOCK)
==================================================================
PostToolUse hook that tracks pipeline phase progression and warns
when logs are missing for completed phases.

Checks:
  1. After writing to processing/ or knowledge/ dirs, verifies that
     the corresponding batch log exists in logs/batches/
  2. Warns if a phase is being skipped (e.g., Phase 4 without Phase 2 chunks)
  3. Tracks phase state in .claude/mission-control/PHASE-GATE-STATE.json

Version: 1.0.0
Date: 2026-03-07
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = os.environ.get(
    "CLAUDE_PROJECT_DIR",
    str(Path(__file__).resolve().parent.parent.parent),
)

ROOT = Path(PROJECT_DIR)
STATE_FILE = ROOT / ".claude" / "mission-control" / "PHASE-GATE-STATE.json"
LOGS_DIR = ROOT / "logs" / "batches"
PROCESSING = ROOT / "processing"

# Phase indicators: which directories indicate which phase
PHASE_INDICATORS = {
    "chunks": 2,
    "canonical": 3,
    "insights": 4,
    "narratives": 5,
    "semantic": 4,
}


def load_state() -> dict:
    """Load or create phase gate state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "phases_completed": [],
        "last_phase": 0,
        "warnings": [],
        "last_updated": None,
    }


def save_state(state: dict) -> None:
    """Save phase gate state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["last_updated"] = datetime.now().isoformat()
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def check_phase_gate(file_path: str) -> dict | None:
    """Check if a file write indicates a phase and validate prerequisites.

    Returns warning dict if issue found, None if OK.
    """
    path = Path(file_path)

    # Only check writes to processing/ directory
    try:
        rel = path.relative_to(PROCESSING)
    except ValueError:
        return None

    # Determine which phase this write belongs to
    subdir = rel.parts[0] if rel.parts else ""
    phase = PHASE_INDICATORS.get(subdir)
    if phase is None:
        return None

    state = load_state()

    # Check for skipped phases
    expected_prev = phase - 1
    if expected_prev > 1 and expected_prev not in state["phases_completed"]:
        warning = {
            "type": "phase_skip",
            "current_phase": phase,
            "missing_phase": expected_prev,
            "message": f"Phase {phase} started but Phase {expected_prev} not completed",
        }
        state["warnings"].append(warning)
        save_state(state)
        return warning

    # Track this phase
    if phase not in state["phases_completed"]:
        state["phases_completed"].append(phase)
        state["last_phase"] = phase
    save_state(state)

    return None


def check_log_exists() -> dict | None:
    """Check if batch logs exist for recent processing.

    Returns warning if no logs found in last 24h of processing.
    """
    if not LOGS_DIR.exists():
        return None

    # Check if any processing state files were modified recently
    chunks_state = PROCESSING / "chunks" / "CHUNKS-STATE.json"
    if not chunks_state.exists():
        return None

    chunks_mtime = chunks_state.stat().st_mtime

    # Find most recent batch log
    batch_logs = sorted(LOGS_DIR.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not batch_logs:
        return {
            "type": "missing_log",
            "message": "Processing detected but no batch logs found in logs/batches/",
        }

    latest_log_mtime = batch_logs[0].stat().st_mtime

    # If chunks are newer than latest log by more than 1 hour
    if chunks_mtime - latest_log_mtime > 3600:
        return {
            "type": "stale_log",
            "message": "Processing state is newer than latest batch log. Generate logs.",
        }

    return None


def main():
    """Hook entry point (PostToolUse)."""
    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}
    except (json.JSONDecodeError, OSError):
        print(json.dumps({"continue": True}))
        return

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only check Write/Edit operations
    if tool_name not in ("Write", "Edit"):
        print(json.dumps({"continue": True}))
        return

    file_path = tool_input.get("file_path", "")
    if not file_path:
        print(json.dumps({"continue": True}))
        return

    warnings = []

    # Check phase gate
    phase_warning = check_phase_gate(file_path)
    if phase_warning:
        warnings.append(phase_warning["message"])

    # Check log existence
    log_warning = check_log_exists()
    if log_warning:
        warnings.append(log_warning["message"])

    feedback = None
    if warnings:
        feedback = "[PHASE-GATE] " + " | ".join(warnings)

    print(
        json.dumps(
            {
                "continue": True,  # WARN, not BLOCK
                "feedback": feedback,
            }
        )
    )


if __name__ == "__main__":
    main()
