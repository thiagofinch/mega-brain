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

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


#=================================
# CONFIGURATION
#=================================

PROJECT_DIR = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
STATE_PATH = PROJECT_DIR / '.claude' / 'mission-control' / 'PIPELINE-STATE.json'
LOG_PATH = PROJECT_DIR / 'logs' / 'pipeline-checkpoints.jsonl'

# Pipeline phases configuration
PIPELINE_PHASES = {
    'ingest': {
        'id': 'CP_INGEST',
        'order': 1,
        'markers': ['inbox/', 'ingest', 'download']
    },
    'chunk': {
        'id': 'CP_CHUNK',
        'order': 2,
        'markers': ['chunks/', 'CHUNKS-STATE', 'chunking']
    },
    'canonical': {
        'id': 'CP_CANONICAL',
        'order': 3,
        'markers': ['canonical/', 'entities', 'entity-resolution']
    }
}


#=================================
# STATE MANAGEMENT
#=================================

def create_default_state() -> Dict[str, Any]:
    """
    Create clean state template.

    Returns:
        Default pipeline state structure
    """
    return {
        'version': '1.0.0',
        'current_phase': None,
        'phases': {
            'ingest': {
                'status': 'pending',
                'files': [],
                'timestamp': None,
                'checkpoint_id': 'CP_INGEST'
            },
            'chunk': {
                'status': 'pending',
                'files': [],
                'timestamp': None,
                'checkpoint_id': 'CP_CHUNK'
            },
            'canonical': {
                'status': 'pending',
                'files': [],
                'timestamp': None,
                'checkpoint_id': 'CP_CANONICAL'
            }
        },
        'last_checkpoint': None,
        'history': [],
        'retry_enabled': True
    }


def load_state() -> Dict[str, Any]:
    """
    Load PIPELINE-STATE.json or return default.

    Returns:
        Current pipeline state
    """
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # Ensure all required keys exist
                if 'version' not in state:
                    state['version'] = '1.0.0'
                if 'phases' not in state:
                    state['phases'] = create_default_state()['phases']
                if 'retry_enabled' not in state:
                    state['retry_enabled'] = True
                return state
        except (json.JSONDecodeError, OSError) as e:
            log_checkpoint({
                'type': 'error',
                'action': 'load_state',
                'error': str(e),
                'fallback': 'creating_default'
            })

    return create_default_state()


def save_state(state: Dict[str, Any]) -> bool:
    """
    Save state to PIPELINE-STATE.json.

    Args:
        state: State dictionary to save

    Returns:
        True if successful, False otherwise
    """
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        log_checkpoint({
            'type': 'error',
            'action': 'save_state',
            'error': str(e)
        })
        return False


#=================================
# PHASE DETECTION
#=================================

def detect_phase_from_path(file_path: str) -> Optional[str]:
    """
    Detect pipeline phase from file path.

    Args:
        file_path: Path to check

    Returns:
        Phase name (ingest/chunk/canonical) or None
    """
    normalized_path = file_path.lower().replace('\\', '/')

    for phase_name, config in PIPELINE_PHASES.items():
        for marker in config['markers']:
            if marker.lower() in normalized_path:
                return phase_name

    return None


def detect_phase_completion(tool_input: Dict[str, Any], state: Dict[str, Any]) -> Optional[str]:
    """
    Detect if a phase has completed based on tool output.

    Checks for STATE.json updates which typically signal phase completion.

    Args:
        tool_input: Tool input data
        state: Current pipeline state

    Returns:
        Phase name if completion detected, None otherwise
    """
    file_path = tool_input.get('file_path', '')

    # Check for state file updates (strong signal of completion)
    if 'STATE.json' in file_path or 'STATE.yaml' in file_path:
        phase = detect_phase_from_path(file_path)
        if phase:
            # Check if this phase has files processed
            phase_data = state.get('phases', {}).get(phase, {})
            if phase_data.get('files'):
                return phase

    return None


#=================================
# CHECKPOINT OPERATIONS
#=================================

def save_checkpoint(phase: str, files: List[str], status: str = 'complete') -> Dict[str, Any]:
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
    if phase in state['phases']:
        timestamp = datetime.now().isoformat()
        state['phases'][phase]['status'] = status
        state['phases'][phase]['timestamp'] = timestamp

        # Add new files (avoid duplicates)
        existing_files = set(state['phases'][phase]['files'])
        new_files = [f for f in files if f not in existing_files]
        state['phases'][phase]['files'].extend(new_files)

        # Update current phase
        state['current_phase'] = phase
        state['last_checkpoint'] = {
            'phase': phase,
            'status': status,
            'timestamp': timestamp,
            'file_count': len(state['phases'][phase]['files'])
        }

        # Add to history
        state['history'].append({
            'phase': phase,
            'status': status,
            'timestamp': timestamp,
            'files_count': len(new_files)
        })

        # Save updated state
        if save_state(state):
            log_checkpoint({
                'type': 'checkpoint_saved',
                'phase': phase,
                'status': status,
                'files_count': len(new_files),
                'total_files': len(state['phases'][phase]['files'])
            })

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

    if not state.get('retry_enabled', True):
        return False

    phase_data = state.get('phases', {}).get(phase, {})
    status = phase_data.get('status', 'pending')

    return status in ['failed', 'pending', 'retry_pending']


def get_resume_point() -> Optional[str]:
    """
    Get the phase to resume from (first incomplete phase).

    Returns:
        Phase name to resume from, or None if all complete
    """
    state = load_state()

    # Sort phases by order
    phases_by_order = sorted(
        PIPELINE_PHASES.items(),
        key=lambda x: x[1]['order']
    )

    for phase_name, _ in phases_by_order:
        phase_data = state.get('phases', {}).get(phase_name, {})
        status = phase_data.get('status', 'pending')

        if status not in ['complete']:
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

    if phase in state['phases']:
        state['phases'][phase]['status'] = 'retry_pending'
        state['phases'][phase]['files'] = []  # Clear files list

        log_checkpoint({
            'type': 'retry_marked',
            'phase': phase,
            'timestamp': datetime.now().isoformat()
        })

        return save_state(state)

    return False


def get_pipeline_status() -> Dict[str, Any]:
    """
    Get formatted status of all phases.

    Returns:
        Status dictionary with phase information
    """
    state = load_state()

    status = {
        'version': state.get('version', '1.0.0'),
        'current_phase': state.get('current_phase'),
        'retry_enabled': state.get('retry_enabled', True),
        'phases': {}
    }

    for phase_name in ['ingest', 'chunk', 'canonical']:
        phase_data = state.get('phases', {}).get(phase_name, {})
        status['phases'][phase_name] = {
            'status': phase_data.get('status', 'pending'),
            'file_count': len(phase_data.get('files', [])),
            'timestamp': phase_data.get('timestamp'),
            'checkpoint_id': phase_data.get('checkpoint_id', f'CP_{phase_name.upper()}')
        }

    resume_point = get_resume_point()
    if resume_point:
        status['resume_from'] = resume_point

    return status


#=================================
# LOGGING
#=================================

def log_checkpoint(action: Dict[str, Any]) -> None:
    """
    Log checkpoint action to JSONL file.

    Args:
        action: Action data to log
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    action['timestamp'] = datetime.now().isoformat()

    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(action, ensure_ascii=False) + '\n')
    except OSError:
        pass  # Silent fail for logging


#=================================
# VALIDATION
#=================================

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
    phase_data = state.get('phases', {}).get(phase, {})

    # Check: At least one file processed
    files = phase_data.get('files', [])
    if not files:
        return False

    # Check: State file exists for chunk and canonical
    if phase in ['chunk', 'canonical']:
        state_markers = {
            'chunk': PROJECT_DIR / 'processing' / 'chunks' / 'CHUNKS-STATE.json',
            'canonical': PROJECT_DIR / 'processing' / 'canonical' / 'ENTITIES-STATE.json'
        }

        state_file = state_markers.get(phase)
        if state_file and not state_file.exists():
            return False

    return True


#=================================
# MAIN HOOK ENTRY
#=================================

def process_tool_use(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process tool use to detect phase activity.

    Args:
        tool_input: Tool input data

    Returns:
        Hook output
    """
    file_path = tool_input.get('file_path', '')

    # Detect phase from file path
    phase = detect_phase_from_path(file_path)

    if not phase:
        return {'continue': True, 'feedback': None}

    state = load_state()

    # Check if phase is in retry mode
    phase_data = state.get('phases', {}).get(phase, {})
    if phase_data.get('status') == 'retry_pending':
        # Update to in_progress
        phase_data['status'] = 'in_progress'
        save_state(state)
        log_checkpoint({
            'type': 'retry_started',
            'phase': phase,
            'file': file_path
        })

    # Register file as processed
    if file_path not in phase_data.get('files', []):
        save_checkpoint(phase, [file_path], status='in_progress')

    # Check if phase completed
    completed_phase = detect_phase_completion(tool_input, state)
    if completed_phase:
        # Validate completion
        if validate_phase_completion(completed_phase):
            save_checkpoint(completed_phase, [], status='complete')
            return {
                'continue': True,
                'feedback': f"[JARVIS] Pipeline checkpoint: {completed_phase} phase complete"
            }
        else:
            save_checkpoint(completed_phase, [], status='needs_attention')
            return {
                'continue': True,
                'feedback': f"[JARVIS] Pipeline checkpoint: {completed_phase} needs attention (validation failed)"
            }

    return {'continue': True, 'feedback': None}


def main():
    """
    Main entry point for hook and CLI.
    """
    # Check if called with CLI arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'status':
            status = get_pipeline_status()
            print("\n=== PIPELINE STATUS ===\n")
            print(f"Version: {status['version']}")
            print(f"Current Phase: {status.get('current_phase', 'None')}")
            print(f"Retry Enabled: {status['retry_enabled']}")

            if 'resume_from' in status:
                print(f"Resume From: {status['resume_from']}")

            print("\nPhases:")
            for phase_name, phase_data in status['phases'].items():
                print(f"  {phase_name}:")
                print(f"    Status: {phase_data['status']}")
                print(f"    Files: {phase_data['file_count']}")
                print(f"    Last Update: {phase_data['timestamp'] or 'Never'}")

            print()
            return

        elif command == 'retry':
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

        elif command == 'resume':
            resume_phase = get_resume_point()
            if resume_phase:
                print(f"[JARVIS] Resume from phase: {resume_phase}")
            else:
                print("[JARVIS] All phases complete - nothing to resume")
            return

        elif command == 'reset':
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

        tool_input = hook_input.get('tool_input', {})

        # Process tool use
        output = process_tool_use(tool_input)

        print(json.dumps(output))

    except Exception as e:
        error_output = {
            'continue': True,
            'feedback': f"[JARVIS] Pipeline checkpoint error: {str(e)}",
            'error': str(e)
        }
        print(json.dumps(error_output))


if __name__ == "__main__":
    main()
