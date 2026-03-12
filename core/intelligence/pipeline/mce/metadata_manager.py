"""
metadata_manager.py -- Metadata Manager for MCE Pipeline
=========================================================

Tracks detailed progress per pipeline run: which phases completed,
how many artifacts were produced, source files processed, attempt
counts for retried phases, etc.

Persists to YAML at::

    .claude/mission-control/mce/{slug}/metadata.yaml

Human-readable by design -- operators can ``cat`` the file and
immediately understand pipeline progress.

Usage::

    from core.intelligence.pipeline.mce.metadata_manager import MetadataManager

    mgr = MetadataManager("alex-hormozi", mode="brownfield")
    mgr.add_source("hormozi-leads-workshop.txt", chunks=45, insights=12)
    mgr.mark_phase_complete("chunking", chunks_created=45)
    mgr.mark_phase_attempt("mce_extraction", attempt=2)
    mgr.save()

    # Resume in a new session:
    mgr2 = MetadataManager.load("alex-hormozi")
    print(mgr2.pipeline_status)  # "in_progress"

Version: 1.0.0
Date: 2026-03-10
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Imports: core.paths (with standalone fallback)
# ---------------------------------------------------------------------------

try:
    from core.paths import ROUTING
except ImportError:
    _ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
    _MISSION_CONTROL = _ROOT / ".claude" / "mission-control"
    ROUTING = {"mce_state": _MISSION_CONTROL / "mce"}

logger = logging.getLogger("mce.metadata_manager")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"

VALID_PHASES: list[str] = [
    "chunking",
    "entity_resolution",
    "knowledge_extraction",
    "mce_extraction",
    "identity_checkpoint",
    "consolidation",
    "agent_generation",
    "validation",
]

VALID_STATUSES: list[str] = [
    "not_started",
    "in_progress",
    "complete",
    "failed",
    "paused",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _metadata_dir(slug: str) -> Path:
    """Return the directory for a given persona slug's MCE metadata."""
    base: Path = ROUTING.get("mce_state", Path(".claude/mission-control/mce"))
    return Path(base) / slug


def _metadata_path(slug: str) -> Path:
    """Return the YAML metadata file path for a given persona slug."""
    return _metadata_dir(slug) / "metadata.yaml"


# ---------------------------------------------------------------------------
# MetadataManager
# ---------------------------------------------------------------------------


class MetadataManager:
    """Tracks detailed progress and artifacts for a single MCE pipeline run.

    Args:
        slug: Persona slug (e.g. ``"alex-hormozi"``).
        mode: ``"greenfield"`` (first time) or ``"brownfield"`` (update existing).
        source_code: Optional 2-3 char source code (e.g. ``"AH"``).
    """

    def __init__(
        self,
        slug: str,
        *,
        mode: str = "greenfield",
        source_code: str = "",
    ) -> None:
        self.slug: str = slug
        self.mode: str = mode
        self.source_code: str = source_code
        self.pipeline_status: str = "not_started"
        self.started_at: str = _now_iso()
        self.updated_at: str = self.started_at
        self.phases_completed: dict[str, dict[str, Any]] = {}
        self.sources_processed: list[dict[str, Any]] = []
        self.version: str = VERSION
        self._path: Path = _metadata_path(slug)

    # -- phase tracking -----------------------------------------------------

    def mark_phase_complete(self, phase: str, **extras: Any) -> None:
        """Mark a phase as completed with optional extra metrics.

        Args:
            phase: Phase name (must be in ``VALID_PHASES``).
            **extras: Arbitrary key-value pairs to store alongside the phase
                      (e.g. ``chunks_created=45``, ``insights=12``).
        """
        if phase not in VALID_PHASES:
            logger.warning("Unknown phase %r -- recording anyway", phase)

        entry: dict[str, Any] = {
            "completed": True,
            "timestamp": _now_iso(),
        }
        entry.update(extras)

        self.phases_completed[phase] = entry
        self.pipeline_status = "in_progress"
        self.updated_at = _now_iso()
        logger.info("Phase %s marked complete for %s", phase, self.slug)

    def mark_phase_attempt(self, phase: str, *, attempt: int = 1) -> None:
        """Record a retry attempt for a phase (without marking it complete).

        Useful for phases that may fail and be retried (e.g. ``mce_extraction``).

        Args:
            phase: Phase name.
            attempt: Attempt number (1-based).
        """
        existing = self.phases_completed.get(phase, {})
        existing["completed"] = False
        existing["attempt"] = attempt
        existing["last_attempt_at"] = _now_iso()
        self.phases_completed[phase] = existing
        self.updated_at = _now_iso()

    def is_phase_complete(self, phase: str) -> bool:
        """Return *True* if the given phase is recorded as complete."""
        entry = self.phases_completed.get(phase, {})
        return bool(entry.get("completed", False))

    @property
    def completed_phase_names(self) -> list[str]:
        """Return a list of phase names that are marked complete."""
        return [
            name
            for name, data in self.phases_completed.items()
            if data.get("completed", False)
        ]

    @property
    def next_incomplete_phase(self) -> str | None:
        """Return the first phase in ``VALID_PHASES`` that is not complete.

        Returns *None* if all phases are complete.
        """
        for phase in VALID_PHASES:
            if not self.is_phase_complete(phase):
                return phase
        return None

    # -- source tracking ----------------------------------------------------

    def add_source(self, filename: str, **extras: Any) -> None:
        """Record a processed source file.

        Args:
            filename: Source file name.
            **extras: Additional metadata (e.g. ``chunks=45``, ``insights=12``).
        """
        entry: dict[str, Any] = {"file": filename}
        entry.update(extras)
        self.sources_processed.append(entry)
        self.updated_at = _now_iso()

    # -- status helpers -----------------------------------------------------

    def mark_complete(self) -> None:
        """Set pipeline status to ``"complete"``."""
        self.pipeline_status = "complete"
        self.updated_at = _now_iso()

    def mark_failed(self, reason: str = "") -> None:
        """Set pipeline status to ``"failed"`` with an optional reason."""
        self.pipeline_status = "failed"
        self.updated_at = _now_iso()
        if reason:
            self.phases_completed.setdefault("_failure", {})["reason"] = reason

    def mark_paused(self) -> None:
        """Set pipeline status to ``"paused"``."""
        self.pipeline_status = "paused"
        self.updated_at = _now_iso()

    # -- persistence --------------------------------------------------------

    def save(self) -> Path:
        """Persist metadata to YAML on disk.

        Returns:
            Path to the written file.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self.updated_at = _now_iso()

        data: dict[str, Any] = {
            "persona": self.slug,
            "mode": self.mode,
            "source_code": self.source_code,
            "pipeline_status": self.pipeline_status,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "phases_completed": self.phases_completed,
            "sources_processed": self.sources_processed,
            "version": self.version,
        }

        self._path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        logger.debug("Saved MCE metadata for %s", self.slug)
        return self._path

    @classmethod
    def load(cls, slug: str) -> MetadataManager | None:
        """Load metadata from disk for the given slug.

        Returns:
            A populated ``MetadataManager`` instance, or *None* if no file
            exists on disk.
        """
        path = _metadata_path(slug)
        if not path.exists():
            return None

        try:
            text = path.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
        except (yaml.YAMLError, OSError) as exc:
            logger.warning("Failed to load MCE metadata for %s: %s", slug, exc)
            return None

        if not isinstance(data, dict):
            return None

        mgr = cls(
            slug,
            mode=data.get("mode", "greenfield"),
            source_code=data.get("source_code", ""),
        )
        mgr.pipeline_status = data.get("pipeline_status", "not_started")
        mgr.started_at = data.get("started_at", mgr.started_at)
        mgr.updated_at = data.get("updated_at", mgr.updated_at)
        mgr.phases_completed = data.get("phases_completed", {})
        mgr.sources_processed = data.get("sources_processed", [])
        mgr.version = data.get("version", VERSION)
        mgr._path = path

        logger.info(
            "Loaded MCE metadata for %s: status=%s, phases=%d",
            slug,
            mgr.pipeline_status,
            len(mgr.completed_phase_names),
        )
        return mgr

    @property
    def metadata_path(self) -> Path:
        """Return the path to the YAML metadata file."""
        return self._path

    def to_dict(self) -> dict[str, Any]:
        """Return metadata as a plain dictionary (for embedding in reports)."""
        return {
            "persona": self.slug,
            "mode": self.mode,
            "source_code": self.source_code,
            "pipeline_status": self.pipeline_status,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "phases_completed": self.phases_completed,
            "sources_processed": self.sources_processed,
            "version": self.version,
        }

    def __repr__(self) -> str:
        return (
            f"MetadataManager(slug={self.slug!r}, "
            f"status={self.pipeline_status!r}, "
            f"phases={len(self.completed_phase_names)})"
        )
