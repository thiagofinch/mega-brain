#!/usr/bin/env python3
"""
PIPELINE CHECKPOINT HOOK - Phase 03 Implementation
===================================================

Saves checkpoint state after each pipeline phase (Ingest, Chunk, Canonical) completes.
Enables resumption of pipeline processing if a phase fails, preventing re-processing.

INTEGRATION:
- PostToolUse hook (Edit|Write|MultiEdit)
- State: .claude/mission-control/PIPELINE-STATE.json
- Logs: logs/pipeline-checkpoints.jsonl

PIPELINE PHASES:
- Phase 1 (Ingest): File download/copy, metadata extraction
  Markers: inbox/, ingest
- Phase 2 (Chunk): Text chunking, semantic segmentation
  Markers: processing/chunks/, CHUNKS-STATE.json
- Phase 3 (Canonical): Entity resolution, canonical form creation
  Markers: processing/canonical/, entities

Author: JARVIS
Version: 1.0.0
Date: 2026-02-27
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# =================================
# CONFIGURATION
# =================================

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
STATE_PATH = PROJECT_DIR / ".claude" / "mission-control" / "PIPELINE-STATE.json"
LOG_PATH = PROJECT_DIR / "logs" / "pipeline-checkpoints.jsonl"

# Pipeline phases configuration
PIPELINE_PHASES = {
    "ingest": {"id": "CP_INGEST", "order": 1, "markers": ["inbox/", "ingest", "download"]},
    "chunk": {"id": "CP_CHUNK", "order": 2, "markers": ["chunks/", "CHUNKS-STATE", "chunking"]},
    "canonical": {
        "id": "CP_CANONICAL",
        "order": 3,
        "markers": ["canonical/", "entities", "entity-resolution"],
    },
}


# =================================
# STATE MANAGEMENT
# =================================


def create_default_state() -> dict[str, Any]:
    """
    Create clean state template.

    Returns:
        Default pipeline state structure
    """
    return {
        "version": "1.0.0",
        "current_phase": None,
        "phases": {
            "ingest": {
                "status": "pending",
                "files": [],
                "timestamp": None,
                "checkpoint_id": "CP_INGEST",
            },
            "chunk": {
                "status": "pending",
                "files": [],
                "timestamp": None,
                "checkpoint_id": "CP_CHUNK",
            },
            "canonical": {
                "status": "pending",
                "files": [],
                "timestamp": None,
                "checkpoint_id": "CP_CANONICAL",
            },
        },
        "mce_steps": {},
        "last_checkpoint": None,
        "history": [],
        "retry_enabled": True,
    }


def load_state() -> dict[str, Any]:
    """
    Load PIPELINE-STATE.json or return default.

    Returns:
        Current pipeline state
    """
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                state = json.load(f)
                # Ensure all required keys exist
                if "version" not in state:
                    state["version"] = "1.0.0"
                if "phases" not in state:
                    state["phases"] = create_default_state()["phases"]
                if "mce_steps" not in state:
                    state["mce_steps"] = {}
                if "retry_enabled" not in state:
                    state["retry_enabled"] = True
                return state
        except (json.JSONDecodeError, OSError) as e:
            log_checkpoint(
                {
                    "type": "error",
                    "action": "load_state",
                    "error": str(e),
                    "fallback": "creating_default",
                }
            )

    return create_default_state()


def save_state(state: dict[str, Any]) -> bool:
    """
    Save state to PIPELINE-STATE.json.

    Args:
        state: State dictionary to save

    Returns:
        True if successful, False otherwise
    """
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        log_checkpoint({"type": "error", "action": "save_state", "error": str(e)})
        return False


# =================================
# PHASE DETECTION
# =================================


def detect_phase_from_path(file_path: str) -> str | None:
    """
    Detect pipeline phase from file path.

    Args:
        file_path: Path to check

    Returns:
        Phase name (ingest/chunk/canonical) or None
    """
    normalized_path = file_path.lower().replace("\\", "/")

    for phase_name, config in PIPELINE_PHASES.items():
        for marker in config["markers"]:
            if marker.lower() in normalized_path:
                return phase_name

    return None


def detect_phase_completion(tool_input: dict[str, Any], state: dict[str, Any]) -> str | None:
    """
    Detect if a phase has completed based on tool output.

    Checks for STATE.json updates which typically signal phase completion.

    Args:
        tool_input: Tool input data
        state: Current pipeline state

    Returns:
        Phase name if completion detected, None otherwise
    """
    file_path = tool_input.get("file_path", "")

    # Check for state file updates (strong signal of completion)
    if "STATE.json" in file_path or "STATE.yaml" in file_path:
        phase = detect_phase_from_path(file_path)
        if phase:
            # Check if this phase has files processed
            phase_data = state.get("phases", {}).get(phase, {})
            if phase_data.get("files"):
                return phase

    return None


# =================================
# MCE STEP MARKER DETECTION
# =================================


MCE_STATE_DIR = PROJECT_DIR / ".claude" / "mission-control" / "mce"


def _check_mce_step_markers(tool_input: dict[str, Any]) -> dict[str, Any] | None:
    """Check for MCE step completion markers written by qa_gates.py.

    Scans .claude/mission-control/mce/*/step_*_complete.json for completions.
    Reads the slug from the directory name -- never from tool output text (AC5).

    Returns checkpoint data if any completions found, None otherwise.
    """
    if not MCE_STATE_DIR.exists():
        return None

    completions: dict[str, dict[str, Any]] = {}

    try:
        for slug_dir in MCE_STATE_DIR.iterdir():
            if not slug_dir.is_dir():
                continue
            slug = slug_dir.name
            for marker in sorted(slug_dir.glob("step_*_complete.json")):
                try:
                    data = json.loads(marker.read_text(encoding="utf-8"))
                    step = data.get("step", 0)
                    completions[f"{slug}_step_{step}"] = {
                        "slug": slug,
                        "step": step,
                        "passed": data.get("passed", False),
                        "timestamp": data.get("timestamp", ""),
                        "marker_path": str(marker),
                    }
                except (json.JSONDecodeError, OSError):
                    continue
    except OSError:
        return None

    if not completions:
        return None

    return {
        "source": "mce_step_markers",
        "completions": completions,
        "total_markers": len(completions),
    }


def _update_state_with_mce_markers(
    marker_data: dict[str, Any],
    state: dict[str, Any],
) -> list[str]:
    """Merge MCE step marker data into PIPELINE-STATE.json.

    Compares discovered markers against existing mce_steps entries.
    Only logs NEW completions (ones not already in state).

    Args:
        marker_data: Output from _check_mce_step_markers.
        state: Current pipeline state (mutated in place).

    Returns:
        List of new completion keys that were added.
    """
    mce_steps = state.setdefault("mce_steps", {})
    new_keys: list[str] = []

    for key, info in marker_data.get("completions", {}).items():
        step_str = str(info["step"])
        slug = info["slug"]
        combined_key = f"{slug}:{step_str}"

        if combined_key not in mce_steps:
            mce_steps[combined_key] = {
                "step": info["step"],
                "slug": slug,
                "passed": info.get("passed", False),
                "timestamp": info.get("timestamp", ""),
                "detected_at": datetime.now().isoformat(),
            }
            new_keys.append(combined_key)

    return new_keys


# =================================
# CHECKPOINT OPERATIONS
# =================================


def save_checkpoint(phase: str, files: list[str], status: str = "complete") -> dict[str, Any]:
    """
    Save checkpoint for a phase.

    Args:
        phase: Phase name
        files: List of files processed
        status: Phase status (complete, in_progress, failed)

    Returns:
        Updated state
    """
    state = load_state()

    # Update phase data
    if phase in state["phases"]:
        timestamp = datetime.now().isoformat()
        state["phases"][phase]["status"] = status
        state["phases"][phase]["timestamp"] = timestamp

        # Add new files (avoid duplicates)
        existing_files = set(state["phases"][phase]["files"])
        new_files = [f for f in files if f not in existing_files]
        state["phases"][phase]["files"].extend(new_files)

        # Update current phase
        state["current_phase"] = phase
        state["last_checkpoint"] = {
            "phase": phase,
            "status": status,
            "timestamp": timestamp,
            "file_count": len(state["phases"][phase]["files"]),
        }

        # Add to history
        state["history"].append(
            {
                "phase": phase,
                "status": status,
                "timestamp": timestamp,
                "files_count": len(new_files),
            }
        )

        # Save updated state
        if save_state(state):
            log_checkpoint(
                {
                    "type": "checkpoint_saved",
                    "phase": phase,
                    "status": status,
                    "files_count": len(new_files),
                    "total_files": len(state["phases"][phase]["files"]),
                }
            )

    return state


def can_retry_phase(phase: str) -> bool:
    """
    Check if a phase can be retried.

    Args:
        phase: Phase name

    Returns:
        True if phase can be retried
    """
    state = load_state()

    if not state.get("retry_enabled", True):
        return False

    phase_data = state.get("phases", {}).get(phase, {})
    status = phase_data.get("status", "pending")

    return status in ["failed", "pending", "retry_pending"]


def get_resume_point() -> str | None:
    """
    Get the phase to resume from (first incomplete phase).

    Returns:
        Phase name to resume from, or None if all complete
    """
    state = load_state()

    # Sort phases by order
    phases_by_order = sorted(PIPELINE_PHASES.items(), key=lambda x: x[1]["order"])

    for phase_name, _ in phases_by_order:
        phase_data = state.get("phases", {}).get(phase_name, {})
        status = phase_data.get("status", "pending")

        if status not in ["complete"]:
            return phase_name

    return None


def mark_for_retry(phase: str) -> bool:
    """
    Mark a phase for retry.

    Args:
        phase: Phase name

    Returns:
        True if successful
    """
    state = load_state()

    if phase in state["phases"]:
        state["phases"][phase]["status"] = "retry_pending"
        state["phases"][phase]["files"] = []  # Clear files list

        log_checkpoint(
            {"type": "retry_marked", "phase": phase, "timestamp": datetime.now().isoformat()}
        )

        return save_state(state)

    return False


def get_pipeline_status() -> dict[str, Any]:
    """
    Get formatted status of all phases.

    Returns:
        Status dictionary with phase information
    """
    state = load_state()

    status = {
        "version": state.get("version", "1.0.0"),
        "current_phase": state.get("current_phase"),
        "retry_enabled": state.get("retry_enabled", True),
        "phases": {},
    }

    for phase_name in ["ingest", "chunk", "canonical"]:
        phase_data = state.get("phases", {}).get(phase_name, {})
        status["phases"][phase_name] = {
            "status": phase_data.get("status", "pending"),
            "file_count": len(phase_data.get("files", [])),
            "timestamp": phase_data.get("timestamp"),
            "checkpoint_id": phase_data.get("checkpoint_id", f"CP_{phase_name.upper()}"),
        }

    resume_point = get_resume_point()
    if resume_point:
        status["resume_from"] = resume_point

    # Include MCE step completions
    mce_steps = state.get("mce_steps", {})
    if mce_steps:
        status["mce_steps"] = mce_steps

    return status


# =================================
# LOGGING
# =================================


def log_checkpoint(action: dict[str, Any]) -> None:
    """
    Log checkpoint action to JSONL file.

    Args:
        action: Action data to log
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    action["timestamp"] = datetime.now().isoformat()

    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(action, ensure_ascii=False) + "\n")
    except OSError:
        pass  # Silent fail for logging


# =================================
# VALIDATION
# =================================


def validate_phase_completion(phase: str) -> bool:
    """
    Validate that a phase has actually completed.

    Checks:
    - At least one file was processed
    - State file exists (for chunk and canonical phases)

    Args:
        phase: Phase name

    Returns:
        True if validation passes
    """
    state = load_state()
    phase_data = state.get("phases", {}).get(phase, {})

    # Check: At least one file processed
    files = phase_data.get("files", [])
    if not files:
        return False

    # Check: State file exists for chunk and canonical
    if phase in ["chunk", "canonical"]:
        state_markers = {
            "chunk": PROJECT_DIR / "processing" / "chunks" / "CHUNKS-STATE.json",
            "canonical": PROJECT_DIR / "processing" / "canonical" / "ENTITIES-STATE.json",
        }

        state_file = state_markers.get(phase)
        if state_file and not state_file.exists():
            return False

    return True


# =================================
# MAIN HOOK ENTRY
# =================================


def process_tool_use(tool_input: dict[str, Any]) -> dict[str, Any]:
    """
    Process tool use to detect phase activity.

    Two detection paths run in sequence:
    1. Path-based detection (original 3-phase: ingest/chunk/canonical)
    2. MCE step marker detection (reads step_N_complete.json files)

    Args:
        tool_input: Tool input data

    Returns:
        Hook output
    """
    file_path = tool_input.get("file_path", "")
    feedback_parts: list[str] = []

    # --- Detection Path 1: Original 3-phase path-based detection (CR1) ---
    phase = detect_phase_from_path(file_path)

    if phase:
        state = load_state()

        # Check if phase is in retry mode
        phase_data = state.get("phases", {}).get(phase, {})
        if phase_data.get("status") == "retry_pending":
            # Update to in_progress
            phase_data["status"] = "in_progress"
            save_state(state)
            log_checkpoint({"type": "retry_started", "phase": phase, "file": file_path})

        # Register file as processed
        if file_path not in phase_data.get("files", []):
            save_checkpoint(phase, [file_path], status="in_progress")

        # Check if phase completed
        completed_phase = detect_phase_completion(tool_input, state)
        if completed_phase:
            # Validate completion
            if validate_phase_completion(completed_phase):
                save_checkpoint(completed_phase, [], status="complete")
                feedback_parts.append(
                    f"[JARVIS] Pipeline checkpoint: {completed_phase} phase complete"
                )
            else:
                save_checkpoint(completed_phase, [], status="needs_attention")
                feedback_parts.append(
                    f"[JARVIS] Pipeline checkpoint: {completed_phase} needs attention (validation failed)"
                )

    # --- Detection Path 2: MCE step completion markers (Story 1.8) ---
    marker_data = _check_mce_step_markers(tool_input)

    if marker_data:
        state = load_state()
        new_keys = _update_state_with_mce_markers(marker_data, state)

        if new_keys:
            save_state(state)

            # Log each new completion to JSONL
            for key in new_keys:
                entry = state["mce_steps"][key]
                log_checkpoint(
                    {
                        "type": "mce_step_detected",
                        "phase": f"mce_step_{entry['step']}",
                        "slug": entry["slug"],
                        "step": entry["step"],
                        "passed": entry.get("passed", False),
                        "marker_timestamp": entry.get("timestamp", ""),
                    }
                )

            # Build feedback summary
            steps_found = [state["mce_steps"][k]["step"] for k in new_keys]
            slugs_found = list({state["mce_steps"][k]["slug"] for k in new_keys})
            feedback_parts.append(
                f"[JARVIS] MCE step markers detected: "
                f"steps {steps_found} for {', '.join(slugs_found)}"
            )

    # Combine feedback from both detection paths
    combined_feedback = " | ".join(feedback_parts) if feedback_parts else None
    return {"continue": True, "feedback": combined_feedback}


def main():
    """
    Main entry point for hook and CLI.
    """
    # Check if called with CLI arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            status = get_pipeline_status()
            print("\n=== PIPELINE STATUS ===\n")
            print(f"Version: {status['version']}")
            print(f"Current Phase: {status.get('current_phase', 'None')}")
            print(f"Retry Enabled: {status['retry_enabled']}")

            if "resume_from" in status:
                print(f"Resume From: {status['resume_from']}")

            print("\nPhases:")
            for phase_name, phase_data in status["phases"].items():
                print(f"  {phase_name}:")
                print(f"    Status: {phase_data['status']}")
                print(f"    Files: {phase_data['file_count']}")
                print(f"    Last Update: {phase_data['timestamp'] or 'Never'}")

            mce_steps = status.get("mce_steps", {})
            if mce_steps:
                print("\nMCE Step Completions:")
                for key, step_data in sorted(mce_steps.items()):
                    slug = step_data.get("slug", "?")
                    step = step_data.get("step", "?")
                    passed = step_data.get("passed", False)
                    ts = step_data.get("timestamp", "?")
                    mark = "PASS" if passed else "FAIL"
                    print(f"  [{mark}] {slug} step {step} ({ts})")

            print()
            return

        elif command == "retry":
            phase = sys.argv[2] if len(sys.argv) > 2 else None
            if not phase:
                print("Usage: pipeline_checkpoint.py retry <phase>")
                print("Phases: ingest, chunk, canonical")
                return

            if phase not in PIPELINE_PHASES:
                print(f"Invalid phase: {phase}")
                return

            if mark_for_retry(phase):
                print(f"[JARVIS] Phase '{phase}' marked for retry")
            else:
                print(f"[JARVIS] Failed to mark phase '{phase}' for retry")
            return

        elif command == "resume":
            resume_phase = get_resume_point()
            if resume_phase:
                print(f"[JARVIS] Resume from phase: {resume_phase}")
            else:
                print("[JARVIS] All phases complete - nothing to resume")
            return

        elif command == "reset":
            state = create_default_state()
            if save_state(state):
                print("[JARVIS] Pipeline state reset to default")
            else:
                print("[JARVIS] Failed to reset state")
            return

        else:
            print(f"Unknown command: {command}")
            print("Commands: status, retry <phase>, resume, reset")
            return

    # Hook mode: read from stdin
    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}

        tool_input = hook_input.get("tool_input", {})

        # Process tool use
        output = process_tool_use(tool_input)

        print(json.dumps(output))

    except Exception as e:
        error_output = {
            "continue": True,
            "feedback": f"[JARVIS] Pipeline checkpoint error: {e!s}",
            "error": str(e),
        }
        print(json.dumps(error_output))


if __name__ == "__main__":
    main()
