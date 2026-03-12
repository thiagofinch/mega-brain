# core/intelligence/ - Processing Scripts
# Scripts that detect roles, generate skills, analyze themes, etc.

from .pipeline.autonomous_processor import (
    AutonomousProcessor,
    FileQueue,
    ProcessingResult,
    ProcessorState,
    QueueItem,
)
from .pipeline.task_orchestrator import (
    ExecutionState,
    TaskDefinition,
    TaskOrchestrator,
    WorkflowDefinition,
    WorkflowPhase,
    list_workflows,
    load_task_definition,
    load_workflow,
    resolve_task,
    resolve_workflow,
)

__all__ = [
    'AutonomousProcessor',
    'ExecutionState',
    'FileQueue',
    'ProcessingResult',
    'ProcessorState',
    'QueueItem',
    'TaskDefinition',
    'TaskOrchestrator',
    'WorkflowDefinition',
    'WorkflowPhase',
    'list_workflows',
    'load_task_definition',
    'load_workflow',
    'resolve_task',
    'resolve_workflow',
]
