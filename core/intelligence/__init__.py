# core/intelligence/ - Processing Scripts
# Scripts that detect roles, generate skills, analyze themes, etc.

from .task_orchestrator import (
    TaskOrchestrator,
    load_workflow,
    list_workflows,
    resolve_workflow,
    load_task_definition,
    resolve_task,
    ExecutionState,
    WorkflowDefinition,
    WorkflowPhase,
    TaskDefinition,
)

from .autonomous_processor import (
    AutonomousProcessor,
    FileQueue,
    QueueItem,
    ProcessingResult,
    ProcessorState,
)

__all__ = [
    'TaskOrchestrator',
    'load_workflow',
    'list_workflows',
    'resolve_workflow',
    'load_task_definition',
    'resolve_task',
    'ExecutionState',
    'WorkflowDefinition',
    'WorkflowPhase',
    'TaskDefinition',
    'AutonomousProcessor',
    'FileQueue',
    'QueueItem',
    'ProcessingResult',
    'ProcessorState',
]
