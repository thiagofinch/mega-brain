"""
MCE Pipeline Infrastructure -- Mega Brain Cognitive Extraction
=============================================================

Seven infrastructure modules that power the MCE pipeline:

- **state_machine**: Finite state machine for pipeline phase transitions
- **metadata_manager**: Tracks detailed progress per pipeline run
- **metrics**: Tracks duration per phase
- **gemini_analyzer**: Gemini Flash 2.0 wrapper for high-volume classification
- **cache**: Two-level cache (memory LRU + disk JSON) for analysis results
- **workflow_detector**: Auto-detects greenfield vs brownfield pipeline runs
- **cli**: CLI entry point for pipeline infrastructure management

All state modules persist to YAML in ``.claude/mission-control/mce/{slug}/``.
Cache persists to JSON in ``.data/mce_cache/``.

Version: 2.0.0
Date: 2026-03-10
"""

from engine.intelligence.pipeline.mce.cache import CacheStats, MCECache, make_cache_key
from engine.intelligence.pipeline.mce.gemini_analyzer import (
    GeminiAnalysisError,
    GeminiAnalyzer,
    GeminiNotConfiguredError,
)
from engine.intelligence.pipeline.mce.metadata_manager import MetadataManager
from engine.intelligence.pipeline.mce.metrics import MetricsTracker
from engine.intelligence.pipeline.mce.orchestrate import (
    cmd_batch,
    cmd_finalize,
    cmd_full,
    cmd_ingest,
    cmd_process_batch,
    cmd_status,
)
from engine.intelligence.pipeline.mce.transaction import (
    PipelineTransaction,
    pipeline_transaction,
)

try:
    from engine.intelligence.pipeline.mce.pipeline_audit_renderer import (
        render_pipeline_audit,
    )
except ImportError:
    render_pipeline_audit = None  # type: ignore[assignment,misc]
from engine.intelligence.pipeline.mce.agent_identity import (
    AgentIdentity,
    IdentityFilter,
    get_identity,
    install_identity_logging,
    require_identity,
)
from engine.intelligence.pipeline.mce.agent_selector import (
    AGENT_REGISTRY,
    STEP_TO_AGENT,
    AgentInfo,
    get_agent_info,
    list_agents,
    list_steps,
    select_agent,
)
from engine.intelligence.pipeline.mce.coordinator_mode import (
    clear_prompt_cache,
    get_coordinator_prompt,
    inject_coordinator_context,
    is_coordinator_mode,
)
from engine.intelligence.pipeline.mce.mailbox import (
    Mailbox,
    PeerMessage,
)
from engine.intelligence.pipeline.mce.peer_messaging import (
    PeerMessenger,
    broadcast,
    get_peer_messenger,
    init_peer_messaging,
    peek_inbox,
    read_inbox,
    reset_peer_messaging,
    send_message,
)
from engine.intelligence.pipeline.mce.state_machine import PipelineStateMachine
from engine.intelligence.pipeline.mce.structured_output import (
    ADVOGADO_SECTIONS,
    CRITICO_CRITERIA,
    AdvogadoOutput,
    AdvogadoSection,
    CriterionScore,
    CriticoOutput,
    OutputValidationResult,
    parse_advogado_output,
    parse_critico_output,
    validate_advogado_output,
    validate_critico_output,
)
from engine.intelligence.pipeline.mce.synthesis_spec import (
    ANTI_PATTERN_PHRASES,
    Finding,
    SpecItem,
    SynthesisSpec,
    ValidationResult,
    format_spec,
    parse_spec,
    validate_spec,
)
from engine.intelligence.pipeline.mce.task_notification import (
    NotificationCollector,
    TaskNotification,
    TaskStatus,
    complete_task,
    notifications_to_manifest,
    notify_task_complete,
)
from engine.intelligence.pipeline.mce.teammate_context import (
    TeammateContext,
    TeammateInfo,
    clear_context,
    get_context,
    set_context,
    teammate_context,
    teammate_context_sync,
)
from engine.intelligence.pipeline.mce.worker_modes import (
    ModeConfig,
    ModeResult,
    WorkerMode,
    apply_mode,
    select_mode,
)
from engine.intelligence.pipeline.mce.workflow_detector import WorkflowMode, detect

__all__ = [
    "ADVOGADO_SECTIONS",
    "AGENT_REGISTRY",
    "ANTI_PATTERN_PHRASES",
    "CRITICO_CRITERIA",
    "STEP_TO_AGENT",
    "AdvogadoOutput",
    "AdvogadoSection",
    "AgentIdentity",
    "AgentInfo",
    "CacheStats",
    "CriterionScore",
    "CriticoOutput",
    "Finding",
    "GeminiAnalysisError",
    "GeminiAnalyzer",
    "GeminiNotConfiguredError",
    "IdentityFilter",
    "MCECache",
    "Mailbox",
    "MetadataManager",
    "MetricsTracker",
    "ModeConfig",
    "ModeResult",
    "NotificationCollector",
    "OutputValidationResult",
    "PeerMessage",
    "PeerMessenger",
    "PipelineStateMachine",
    "PipelineTransaction",
    "SpecItem",
    "SynthesisSpec",
    "TaskNotification",
    "TaskStatus",
    "TeammateContext",
    "TeammateInfo",
    "ValidationResult",
    "WorkerMode",
    "WorkflowMode",
    "apply_mode",
    "broadcast",
    "clear_context",
    "clear_prompt_cache",
    "cmd_batch",
    "cmd_finalize",
    "cmd_full",
    "cmd_ingest",
    "cmd_process_batch",
    "cmd_status",
    "complete_task",
    "detect",
    "format_spec",
    "get_agent_info",
    "get_context",
    "get_coordinator_prompt",
    "get_identity",
    "get_peer_messenger",
    "init_peer_messaging",
    "inject_coordinator_context",
    "install_identity_logging",
    "is_coordinator_mode",
    "list_agents",
    "list_steps",
    "make_cache_key",
    "notifications_to_manifest",
    "notify_task_complete",
    "parse_advogado_output",
    "parse_critico_output",
    "parse_spec",
    "peek_inbox",
    "pipeline_transaction",
    "read_inbox",
    "render_pipeline_audit",
    "require_identity",
    "reset_peer_messaging",
    "select_agent",
    "select_mode",
    "send_message",
    "set_context",
    "teammate_context",
    "teammate_context_sync",
    "validate_advogado_output",
    "validate_critico_output",
    "validate_spec",
]
__version__ = "2.4.0"
