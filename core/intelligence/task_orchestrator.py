#!/usr/bin/env python3
"""
Task Orchestrator - Workflow execution engine for Mega Brain pipeline.

Reads workflow YAML files from core/workflows/ and executes tasks sequentially,
tracking state between tasks and managing checkpoint validation.

Usage:
    from core.intelligence import TaskOrchestrator

    orchestrator = TaskOrchestrator('wf-pipeline-full')
    result = orchestrator.execute(inputs={'files': ['data.txt']})
"""

import json
import os
import re
import yaml
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# ============================================================================
# Configuration and Constants
# ============================================================================

PROJECT_DIR = Path(os.getenv('CLAUDE_PROJECT_DIR', '.')).resolve()
WORKFLOW_DIR = PROJECT_DIR / 'core' / 'workflows'
TASK_DIR = PROJECT_DIR / 'core' / 'tasks'
STATE_PATH = PROJECT_DIR / '.claude' / 'mission-control' / 'ORCHESTRATOR-STATE.json'
LOG_PATH = PROJECT_DIR / 'logs' / 'orchestrator-execution.jsonl'


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class TaskDefinition:
    """Represents a parsed task from a task markdown file."""
    task_id: str
    name: str
    execution_type: str
    responsible: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    path: Optional[Path] = None


@dataclass
class WorkflowPhase:
    """Represents a phase in a workflow."""
    id: str
    name: str
    description: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    checkpoint: Optional[Dict[str, Any]] = None
    order: int = 0


@dataclass
class WorkflowDefinition:
    """Represents a complete workflow configuration."""
    id: str
    name: str
    description: str = ""
    phases: List[WorkflowPhase] = field(default_factory=list)
    transitions: List[Dict[str, Any]] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressReport:
    """Progress report for workflow execution."""
    current_task: str
    current_phase: str
    progress_percent: float
    tasks_completed: int
    tasks_total: int
    estimated_remaining_seconds: Optional[int]
    started_at: str
    elapsed_seconds: int


@dataclass
class ExecutionState:
    """Tracks the execution state of a workflow."""
    workflow_id: str
    current_phase: Optional[str] = None
    current_step: int = 0
    status: str = "not_started"  # not_started, in_progress, completed, failed
    history: List[Dict[str, Any]] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    phase_outputs: Dict[str, Any] = field(default_factory=dict)
    task_timings: Dict[str, float] = field(default_factory=dict)
    phase_started_at: Optional[str] = None


# ============================================================================
# YAML Loading Functions
# ============================================================================

def load_workflow(workflow_path: Path) -> WorkflowDefinition:
    """
    Parse a workflow YAML file and return a typed WorkflowDefinition.

    Args:
        workflow_path: Path to the workflow YAML file

    Returns:
        WorkflowDefinition object with parsed workflow configuration

    Raises:
        FileNotFoundError: If workflow file doesn't exist
        yaml.YAMLError: If YAML is malformed
        ValueError: If required fields are missing
    """
    if not workflow_path.exists():
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

    with open(workflow_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data or 'workflow' not in data:
        raise ValueError(f"Invalid workflow structure in {workflow_path}")

    wf_data = data['workflow']

    # Parse phases
    phases = []
    for idx, phase_data in enumerate(wf_data.get('phases', [])):
        phase = WorkflowPhase(
            id=phase_data.get('id', f'phase_{idx}'),
            name=phase_data.get('name', f'Phase {idx}'),
            description=phase_data.get('description', ''),
            steps=phase_data.get('steps', []),
            checkpoint=phase_data.get('checkpoint'),
            order=idx
        )
        phases.append(phase)

    workflow = WorkflowDefinition(
        id=wf_data.get('id', workflow_path.stem),
        name=wf_data.get('name', ''),
        description=wf_data.get('description', ''),
        phases=phases,
        transitions=wf_data.get('transitions', []),
        inputs=wf_data.get('inputs', {}),
        outputs=wf_data.get('outputs', {})
    )

    return workflow


def list_workflows() -> List[Path]:
    """
    List all workflow YAML files in the WORKFLOW_DIR.

    Returns:
        List of Path objects for all .yaml files in core/workflows/
    """
    if not WORKFLOW_DIR.exists():
        return []

    return sorted(WORKFLOW_DIR.glob('*.yaml'))


def resolve_workflow(workflow_id: str) -> Optional[Path]:
    """
    Find a workflow file by its ID.

    Args:
        workflow_id: The workflow ID (e.g., 'wf-pipeline-full')

    Returns:
        Path to the workflow file, or None if not found
    """
    # Try direct match first
    direct_path = WORKFLOW_DIR / f"{workflow_id}.yaml"
    if direct_path.exists():
        return direct_path

    # Search all workflows for matching ID
    for wf_path in list_workflows():
        try:
            wf = load_workflow(wf_path)
            if wf.id == workflow_id:
                return wf_path
        except Exception:
            continue

    return None


# ============================================================================
# Task Resolution Functions
# ============================================================================

def load_task_definition(task_path: Path) -> TaskDefinition:
    """
    Parse a task markdown file and extract the task definition.

    Args:
        task_path: Path to the task markdown file

    Returns:
        TaskDefinition object with parsed task metadata

    Raises:
        FileNotFoundError: If task file doesn't exist
        ValueError: If task anatomy table is missing
    """
    if not task_path.exists():
        raise FileNotFoundError(f"Task file not found: {task_path}")

    with open(task_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract task anatomy table
    anatomy_pattern = r'\|\s*Field\s*\|\s*Value\s*\|.*?\n((?:\|[^\n]+\n)+)'
    match = re.search(anatomy_pattern, content, re.DOTALL)

    if not match:
        raise ValueError(f"Task anatomy table not found in {task_path}")

    # Parse table rows
    anatomy = {}
    for line in match.group(1).split('\n'):
        if '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                anatomy[parts[0]] = parts[1]

    # Extract inputs and outputs sections
    inputs = _extract_table_section(content, r'## Inputs')
    outputs = _extract_table_section(content, r'## Outputs')

    task_def = TaskDefinition(
        task_id=anatomy.get('task_id', task_path.stem),
        name=anatomy.get('task_name', task_path.stem),
        execution_type=anatomy.get('execution_type', 'Agent'),
        responsible=anatomy.get('responsible', '@jarvis'),
        inputs=inputs,
        outputs=outputs,
        description=anatomy.get('description', ''),
        path=task_path
    )

    return task_def


def resolve_task(task_ref: str) -> Path:
    """
    Convert a task reference to a full file path.

    Args:
        task_ref: Task reference (e.g., "tasks/process-batch.md")

    Returns:
        Full Path to the task file

    Raises:
        FileNotFoundError: If task file doesn't exist
    """
    # Handle both absolute and relative references
    if task_ref.startswith('tasks/'):
        task_path = TASK_DIR / task_ref.replace('tasks/', '')
    else:
        task_path = PROJECT_DIR / task_ref

    if not task_path.exists():
        raise FileNotFoundError(f"Task file not found: {task_path}")

    return task_path


def _extract_table_section(content: str, section_header: str) -> Dict[str, Any]:
    """Extract a table section from markdown content."""
    pattern = rf'{section_header}.*?\n\|[^\n]+\|.*?\n((?:\|[^\n]+\n)+)'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return {}

    result = {}
    for line in match.group(1).split('\n'):
        if '|' in line and not line.strip().startswith('|---'):
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                result[parts[0]] = {
                    'type': parts[1] if len(parts) > 1 else '',
                    'required': parts[2] if len(parts) > 2 else '',
                    'description': parts[3] if len(parts) > 3 else ''
                }

    return result


# ============================================================================
# State Management
# ============================================================================

def create_default_state(workflow_id: str) -> ExecutionState:
    """
    Create a new default execution state for a workflow.

    Args:
        workflow_id: The workflow ID

    Returns:
        ExecutionState object with initial values
    """
    return ExecutionState(
        workflow_id=workflow_id,
        started_at=datetime.utcnow().isoformat(),
        status="not_started"
    )


def load_state() -> Optional[ExecutionState]:
    """
    Load the current execution state from disk.

    Returns:
        ExecutionState object if state file exists, None otherwise
    """
    if not STATE_PATH.exists():
        return None

    try:
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Reconstruct ExecutionState from dict
        state = ExecutionState(**data)
        return state
    except Exception:
        return None


def save_state(state: ExecutionState) -> None:
    """
    Save the execution state to disk.

    Args:
        state: ExecutionState object to save
    """
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(asdict(state), f, indent=2)


def log_execution(event: Dict[str, Any]) -> None:
    """
    Append an execution event to the JSONL log.

    Args:
        event: Dictionary containing event data
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    event['timestamp'] = datetime.utcnow().isoformat()

    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event) + '\n')


# ============================================================================
# Core Orchestrator Class
# ============================================================================

class TaskOrchestrator:
    """
    Main orchestrator class that executes workflows by sequencing tasks.

    The orchestrator reads workflow definitions, resolves task references,
    and manages execution state across multiple phases and steps.

    Usage:
        orch = TaskOrchestrator('wf-pipeline-full')
        result = orch.execute({'files': ['data.txt']})
    """

    def __init__(self, workflow_id: str):
        """
        Initialize the orchestrator with a workflow.

        Args:
            workflow_id: ID of the workflow to execute

        Raises:
            FileNotFoundError: If workflow doesn't exist
        """
        workflow_path = resolve_workflow(workflow_id)
        if not workflow_path:
            raise FileNotFoundError(f"Workflow not found: {workflow_id}")

        self.workflow = load_workflow(workflow_path)
        self.state = load_state() or create_default_state(workflow_id)
        self.task_cache: Dict[str, TaskDefinition] = {}

        log_execution({
            'event': 'orchestrator_initialized',
            'workflow_id': workflow_id,
            'phases': len(self.workflow.phases)
        })

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all phases of the workflow sequentially.

        Args:
            inputs: Initial input data for the workflow

        Returns:
            Dict with 'success' boolean and 'outputs' dict
        """
        self.state.status = "in_progress"
        self.state.started_at = datetime.utcnow().isoformat()
        save_state(self.state)

        log_execution({
            'event': 'workflow_started',
            'workflow_id': self.workflow.id,
            'inputs': list(inputs.keys())
        })

        for phase in self.workflow.phases:
            result = self._execute_phase(phase, inputs)
            if not result['success']:
                self.state.status = "failed"
                save_state(self.state)
                return result

            # Accumulate outputs from each phase
            inputs.update(result.get('outputs', {}))

        self.state.status = "completed"
        self.state.completed_at = datetime.utcnow().isoformat()
        save_state(self.state)

        log_execution({
            'event': 'workflow_completed',
            'workflow_id': self.workflow.id,
            'duration_seconds': self._calculate_duration()
        })

        return {'success': True, 'outputs': inputs}

    def _execute_phase(self, phase: WorkflowPhase, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all steps in a workflow phase.

        Args:
            phase: WorkflowPhase object to execute
            inputs: Input data for the phase

        Returns:
            Dict with 'success' boolean and optional 'outputs'
        """
        self.state.current_phase = phase.id
        self.state.current_step = 0
        save_state(self.state)

        log_execution({
            'event': 'phase_started',
            'phase_id': phase.id,
            'phase_name': phase.name
        })

        phase_outputs = {}

        for idx, step in enumerate(phase.steps):
            self.state.current_step = idx
            save_state(self.state)

            result = self._execute_step(step, inputs)
            if not result['success']:
                return result

            phase_outputs.update(result.get('outputs', {}))

        # Store phase outputs in state
        self.state.phase_outputs[phase.id] = phase_outputs

        log_execution({
            'event': 'phase_completed',
            'phase_id': phase.id
        })

        return {'success': True, 'outputs': phase_outputs}

    def _execute_step(self, step: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single workflow step.

        Args:
            step: Step configuration dictionary
            inputs: Input data for the step

        Returns:
            Dict with 'success' boolean and execution metadata
        """
        if 'execute' in step:
            exec_config = step['execute']

            if 'task' in exec_config:
                task_def = self._resolve_and_cache_task(exec_config['task'])

                log_execution({
                    'event': 'task_identified',
                    'task_id': task_def.task_id,
                    'task_name': task_def.name,
                    'responsible': task_def.responsible
                })

                # Return task for Claude to execute
                return {
                    'success': True,
                    'task': asdict(task_def),
                    'needs_execution': True,
                    'outputs': {}
                }

        return {'success': True, 'outputs': {}}

    def _resolve_and_cache_task(self, task_ref: str) -> TaskDefinition:
        """
        Resolve a task reference and cache the result.

        Args:
            task_ref: Task reference string

        Returns:
            TaskDefinition object
        """
        if task_ref not in self.task_cache:
            task_path = resolve_task(task_ref)
            self.task_cache[task_ref] = load_task_definition(task_path)

        return self.task_cache[task_ref]

    def get_current_task(self) -> Optional[TaskDefinition]:
        """
        Get the current task to be executed based on state.

        Returns:
            TaskDefinition if there's a current task, None otherwise
        """
        if not self.state.current_phase:
            return None

        # Find the current phase
        current_phase = None
        for phase in self.workflow.phases:
            if phase.id == self.state.current_phase:
                current_phase = phase
                break

        if not current_phase or self.state.current_step >= len(current_phase.steps):
            return None

        step = current_phase.steps[self.state.current_step]
        if 'execute' in step and 'task' in step['execute']:
            return self._resolve_and_cache_task(step['execute']['task'])

        return None

    def mark_task_complete(self, task_id: str, outputs: Dict[str, Any]) -> None:
        """
        Mark a task as complete and record its outputs.

        Args:
            task_id: ID of the completed task
            outputs: Output data from the task
        """
        self.state.history.append({
            'task_id': task_id,
            'completed_at': datetime.utcnow().isoformat(),
            'outputs': outputs
        })

        save_state(self.state)

        log_execution({
            'event': 'task_completed',
            'task_id': task_id,
            'outputs': list(outputs.keys())
        })

    def _calculate_duration(self) -> float:
        """Calculate execution duration in seconds."""
        if not self.state.started_at or not self.state.completed_at:
            return 0.0

        start = datetime.fromisoformat(self.state.started_at)
        end = datetime.fromisoformat(self.state.completed_at)
        return (end - start).total_seconds()

    def get_progress(self) -> ProgressReport:
        """Calculate and return current execution progress."""
        total_tasks = sum(len(p.steps) for p in self.workflow.phases)
        completed = self._count_completed_tasks()
        progress = (completed / total_tasks * 100) if total_tasks > 0 else 0

        avg_time = self._calculate_avg_task_time()
        remaining_tasks = total_tasks - completed
        estimated_remaining = int(avg_time * remaining_tasks) if avg_time else None

        return ProgressReport(
            current_task=self._get_current_task_name(),
            current_phase=self.state.current_phase or "not_started",
            progress_percent=round(progress, 1),
            tasks_completed=completed,
            tasks_total=total_tasks,
            estimated_remaining_seconds=estimated_remaining,
            started_at=self.state.started_at or "",
            elapsed_seconds=self._calculate_elapsed()
        )

    def _count_completed_tasks(self) -> int:
        """Count tasks marked complete in history."""
        return len(self.state.history)

    def _calculate_avg_task_time(self) -> float:
        """Calculate average task execution time from timings."""
        if not self.state.task_timings:
            return 0.0
        return sum(self.state.task_timings.values()) / len(self.state.task_timings)

    def _get_current_task_name(self) -> str:
        """Get the name of the current task being executed."""
        task = self.get_current_task()
        return task.name if task else "No active task"

    def _calculate_elapsed(self) -> int:
        """Calculate elapsed seconds since workflow started."""
        if not self.state.started_at:
            return 0
        start = datetime.fromisoformat(self.state.started_at)
        return int((datetime.utcnow() - start).total_seconds())


# ============================================================================
# Public API
# ============================================================================

def print_usage():
    print("""
Task Orchestrator - Mega Brain Pipeline
========================================

Usage:
    python3 task_orchestrator.py <command> [args]

Commands:
    list                    List available workflows
    status                  Show current execution status
    run <workflow_id>       Run a workflow (e.g., wf-ingest)
    progress                Show progress of current execution
    reset                   Reset orchestrator state

Examples:
    python3 task_orchestrator.py list
    python3 task_orchestrator.py run wf-ingest
    python3 task_orchestrator.py status
    """)


def cmd_list():
    """List available workflows."""
    print("[JARVIS] Available workflows:")
    for wf_path in list_workflows():
        wf = load_workflow(wf_path)
        phases = len(wf.phases)
        print(f"  - {wf.id}: {wf.name} ({phases} phases)")


def cmd_status():
    """Show current execution status."""
    state = load_state()
    if not state:
        print("[JARVIS] No active execution. Run a workflow first.")
        return

    print("[JARVIS] Orchestrator Status")
    print(f"  Workflow: {state.workflow_id}")
    print(f"  Phase: {state.current_phase or 'not started'}")
    print(f"  Status: {state.status}")
    print(f"  Started: {state.started_at or 'N/A'}")


def cmd_run(workflow_id: str):
    """Run a workflow."""
    print(f"[JARVIS] Starting workflow: {workflow_id}")
    orch = TaskOrchestrator(workflow_id)
    progress = orch.get_progress()
    print(f"  Total tasks: {progress.tasks_total}")
    print(f"  Current task: {progress.current_task}")
    print("[JARVIS] Workflow ready. Execute with Claude agent.")


def cmd_progress():
    """Show progress of current execution."""
    state = load_state()
    if not state:
        print("[JARVIS] No active execution.")
        return

    orch = TaskOrchestrator(state.workflow_id)
    orch.state = state
    progress = orch.get_progress()

    print("[JARVIS] Execution Progress")
    print(f"  Current Task: {progress.current_task}")
    print(f"  Progress: {progress.progress_percent}%")
    print(f"  Completed: {progress.tasks_completed}/{progress.tasks_total} tasks")
    if progress.estimated_remaining_seconds:
        mins = progress.estimated_remaining_seconds // 60
        secs = progress.estimated_remaining_seconds % 60
        print(f"  Estimated Remaining: {mins}m {secs}s")
    print(f"  Elapsed: {progress.elapsed_seconds}s")


def cmd_reset():
    """Reset orchestrator state."""
    if STATE_PATH.exists():
        STATE_PATH.unlink()
    print("[JARVIS] Orchestrator state reset.")


def main():
    import sys
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'list':
        cmd_list()
    elif command == 'status':
        cmd_status()
    elif command == 'run':
        if len(sys.argv) < 3:
            print("[ERROR] Usage: run <workflow_id>")
            sys.exit(1)
        cmd_run(sys.argv[2])
    elif command == 'progress':
        cmd_progress()
    elif command == 'reset':
        cmd_reset()
    else:
        print(f"[ERROR] Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == '__main__':
    main()


__all__ = [
    'TaskOrchestrator',
    'ProgressReport',
    'load_workflow',
    'list_workflows',
    'resolve_workflow',
    'load_task_definition',
    'resolve_task',
    'ExecutionState',
    'WorkflowDefinition',
    'WorkflowPhase',
    'TaskDefinition',
]
