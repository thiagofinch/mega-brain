"""
step_result.py -- StepResult schema for MCE Pipeline Log System
===============================================================

Defines the data contract between pipeline steps and the log renderer.
Every step (or microstep) that wants to appear in the real-time log
must emit a StepResult. The renderer reads it and renders — it does
NOT need to know what the step does internally.

Key design:
  - metrics:  free-form dict — any key/value pair renders automatically
  - outputs:  list of StepOutput — what was produced (artifacts, entities, etc.)
  - impacts:  list of StepImpact — what was affected downstream
  - alerts:   list of StepAlert — triggers, conflicts, anomalies, new roles

When a new microstep is added to the pipeline, it just needs to emit
a StepResult with microstep_id filled. The renderer renders it without
any code changes.

Constraints:
    - dataclasses only — no external deps.
    - All fields optional except step_id, slug, status.
    - Never raises — uses defaults everywhere.

Version: 1.0.0
Date: 2026-03-28
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Sub-components
# ---------------------------------------------------------------------------


@dataclass
class StepOutput:
    """A single item produced by a step — artifact, entity, dossier, skill, etc."""

    label: str
    value: Any
    output_type: str  # "artifact" | "agent_created" | "dossier_updated" |
    # "skill_linked" | "cargo_new" | "conflict_detected" |
    # "canonical_entry" | "decision" | "workspace_sync"
    highlight: bool = False  # True = render with star/emphasis
    chunk_ids: list[str] = field(default_factory=list)
    source_id: str = ""  # which source generated this output


@dataclass
class StepImpact:
    """What was affected downstream — agent, dossier, index, workspace, etc."""

    target: str  # path or agent name
    count: int
    impact_type: str  # "insights_cascaded" | "memory_updated" |
    # "dossier_enriched" | "rag_indexed" |
    # "skills_added" | "tools_linked"
    bucket: str = ""  # "external" | "business" | "personal"
    is_cross_bucket: bool = False


@dataclass
class StepAlert:
    """Trigger, conflict, anomaly, new role, or any condition needing attention."""

    level: str  # "trigger" | "critical" | "warn" | "info"
    category: str  # "new_cargo" | "conflict" | "anomaly" |
    # "digest_error" | "threshold" | "decision_auto"
    message: str
    action_required: bool = False
    reversible: bool = True
    detail: str = ""  # extra context for human reading
    related_ids: list[str] = field(default_factory=list)  # chunk_ids, conflict IDs, etc.


@dataclass
class BucketMetrics:
    """Per-bucket distribution data."""

    files: int = 0
    chunks: int = 0
    insights: int = 0
    entities: int = 0
    is_primary: bool = False
    confidence: float = 0.0
    rag_index: str = ""


@dataclass
class StepResult:
    """
    Complete data emitted by a step or microstep after execution.

    Usage:
        result = StepResult(
            step_id=5,
            step_name="INSIGHT EXTRACTION",
            slug="alex-hormozi",
            status="COMPLETE",
            metrics={
                "total_insights": 84,
                "high": 31,
                "by_tag": {"HEURISTICA": 27, "FILOSOFIA": 18}
            },
            outputs=[
                StepOutput("INSIGHTS-STATE.json", "84 insights", "artifact"),
            ],
            impacts=[
                StepImpact("AGENT-CLOSER MEMORY.md", 34, "insights_cascaded"),
            ],
            alerts=[
                StepAlert("trigger", "new_cargo", "SETTER: 22 menções ≥ threshold"),
            ]
        )

    For microsteps, fill microstep_id and microstep_name:
        result = StepResult(
            step_id=10,
            microstep_id="10.4",
            microstep_name="FRAMEWORK SKILL CONVERTER",
            ...
        )
    """

    # --- Required ---
    step_id: int
    slug: str
    status: str  # "COMPLETE" | "PARTIAL" | "FAILED" | "PENDING" | "RUNNING"

    # --- Step identity ---
    step_name: str = ""
    step_type: str = ""  # "llm" | "deterministic" | "human"
    squad: str = ""  # "gate" | "parse" | "canon" | "dig" | "behav" |
    # "psych" | "voice" | "guard" | "scribe" | "weave" |
    # "clone" | "index" | "ops"

    # --- Microstep (optional) ---
    microstep_id: str | None = None  # "10.1" | "10.4" | "13.2"
    microstep_name: str | None = None

    # --- Timing ---
    duration_seconds: float = 0.0
    timestamp: str = ""

    # --- Content ---
    metrics: dict[str, Any] = field(default_factory=dict)
    outputs: list[StepOutput] = field(default_factory=list)
    impacts: list[StepImpact] = field(default_factory=list)
    alerts: list[StepAlert] = field(default_factory=list)

    # --- Universal panels ---
    bucket: str = "external"
    bucket_external: BucketMetrics = field(default_factory=BucketMetrics)
    bucket_business: BucketMetrics = field(default_factory=BucketMetrics)
    bucket_personal: BucketMetrics = field(default_factory=BucketMetrics)
    bucket_intersections: list[str] = field(default_factory=list)
    routing_mode: str = "AUTO"

    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    quality_score: str | None = None  # "LEGENDARY" | "EXCELLENT" | "GOOD" | ...
    quality_roi: float = 0.0

    # --- Integrity (filled by renderer from manifest comparison) ---
    artifacts_expected: int = 0
    artifacts_found: int = 0
    artifacts_missing: list[str] = field(default_factory=list)
    integrity_pct: float = 100.0
    digest_error: bool = False
    digest_error_detail: str = ""

    # --- Background/Foreground visibility (MCE21-3.4) ---
    is_background: bool = False  # True for proactive tasks (dream, rag indexation)

    # --- Chronicler ---
    chronicler_note: str = ""

    def is_microstep(self) -> bool:
        return self.microstep_id is not None

    def gate_passed(self) -> bool:
        if not self.checkpoints:
            return True
        return all(c.get("passed", True) for c in self.checkpoints if c.get("blocking"))

    def has_alerts_at_level(self, level: str) -> bool:
        return any(a.level == level for a in self.alerts)

    def to_json_path_key(self) -> str:
        """Returns the key used to save/load this result as JSON."""
        if self.microstep_id:
            return f"step_{self.microstep_id.replace('.', '_')}_result"
        return f"step_{self.step_id:02d}_result"
