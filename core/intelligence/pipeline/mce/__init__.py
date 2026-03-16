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

from core.intelligence.pipeline.mce.cache import CacheStats, MCECache, make_cache_key
from core.intelligence.pipeline.mce.log_renderer import (
    render_pipeline_footer,
    render_pipeline_header,
    render_progressive,
    render_step_start,
)
from core.intelligence.pipeline.mce.gemini_analyzer import (
    GeminiAnalysisError,
    GeminiAnalyzer,
    GeminiNotConfiguredError,
)
from core.intelligence.pipeline.mce.metadata_manager import MetadataManager
from core.intelligence.pipeline.mce.metrics import MetricsTracker
from core.intelligence.pipeline.mce.orchestrate import (
    cmd_batch,
    cmd_finalize,
    cmd_full,
    cmd_ingest,
    cmd_status,
)
from core.intelligence.pipeline.mce.state_machine import PipelineStateMachine
from core.intelligence.pipeline.mce.workflow_detector import WorkflowMode, detect

__all__ = [
    "CacheStats",
    "GeminiAnalysisError",
    "GeminiAnalyzer",
    "GeminiNotConfiguredError",
    "MCECache",
    "MetadataManager",
    "MetricsTracker",
    "PipelineStateMachine",
    "WorkflowMode",
    "cmd_batch",
    "cmd_finalize",
    "cmd_full",
    "cmd_ingest",
    "cmd_status",
    "detect",
    "make_cache_key",
    "render_pipeline_footer",
    "render_pipeline_header",
    "render_progressive",
    "render_step_start",
]
__version__ = "2.0.0"
