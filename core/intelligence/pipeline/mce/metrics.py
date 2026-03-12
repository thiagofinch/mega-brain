"""
metrics.py -- Metrics Tracker for MCE Pipeline
===============================================

Tracks wall-clock duration per phase.  Token counting is NOT included
here -- that arrives in Phase 3.4 when Gemini integration lands.

Persists to YAML at::

    .claude/mission-control/mce/{slug}/metrics.yaml

Also appends a one-line JSON summary to the JSONL audit log at::

    logs/mce-metrics.jsonl

Usage::

    from core.intelligence.pipeline.mce.metrics import MetricsTracker

    mt = MetricsTracker("alex-hormozi")
    mt.start_phase("chunking")
    # ... work happens ...
    mt.end_phase("chunking")
    mt.save()

    # Resume in a new session:
    mt2 = MetricsTracker.load("alex-hormozi")
    print(mt2.total_duration_seconds)

Version: 1.0.0
Date: 2026-03-10
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Imports: core.paths (with standalone fallback)
# ---------------------------------------------------------------------------

try:
    from core.paths import LOGS, ROUTING
except ImportError:
    _ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
    LOGS = _ROOT / "logs"
    _MISSION_CONTROL = _ROOT / ".claude" / "mission-control"
    ROUTING = {
        "mce_state": _MISSION_CONTROL / "mce",
        "mce_metrics_log": LOGS / "mce-metrics.jsonl",
    }

logger = logging.getLogger("mce.metrics")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _metrics_dir(slug: str) -> Path:
    """Return the directory for a given persona slug's MCE metrics."""
    base: Path = ROUTING.get("mce_state", Path(".claude/mission-control/mce"))
    return Path(base) / slug


def _metrics_path(slug: str) -> Path:
    """Return the YAML metrics file path for a given persona slug."""
    return _metrics_dir(slug) / "metrics.yaml"


def _jsonl_log_path() -> Path:
    """Return the path to the JSONL audit log for MCE metrics."""
    return Path(ROUTING.get("mce_metrics_log", LOGS / "mce-metrics.jsonl"))


# ---------------------------------------------------------------------------
# PhaseTimer (internal)
# ---------------------------------------------------------------------------


class _PhaseTimer:
    """Tracks start/end wall-clock time for a single phase."""

    __slots__ = ("_mono_start", "ended", "name", "started")

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.started: str = ""
        self.ended: str = ""
        self._mono_start: float = 0.0

    def start(self) -> None:
        self.started = _now_iso()
        self._mono_start = time.monotonic()

    def stop(self) -> None:
        self.ended = _now_iso()

    @property
    def duration_seconds(self) -> float:
        """Return elapsed seconds.  Uses monotonic clock if still running."""
        if self._mono_start and not self.ended:
            return time.monotonic() - self._mono_start
        if self.started and self.ended:
            from datetime import datetime as dt

            try:
                t_start = dt.fromisoformat(self.started)
                t_end = dt.fromisoformat(self.ended)
                return (t_end - t_start).total_seconds()
            except (ValueError, TypeError):
                return 0.0
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.started:
            d["started"] = self.started
        if self.ended:
            d["ended"] = self.ended
        d["duration_seconds"] = round(self.duration_seconds, 1)
        return d

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> _PhaseTimer:
        pt = cls(name)
        pt.started = data.get("started", "")
        pt.ended = data.get("ended", "")
        return pt


# ---------------------------------------------------------------------------
# MetricsTracker
# ---------------------------------------------------------------------------


class MetricsTracker:
    """Tracks wall-clock duration per MCE pipeline phase.

    Args:
        slug: Persona slug (e.g. ``"alex-hormozi"``).
    """

    def __init__(self, slug: str) -> None:
        self.slug: str = slug
        self.started: str = _now_iso()
        self._phases: dict[str, _PhaseTimer] = {}
        self._path: Path = _metrics_path(slug)

    # -- phase timing -------------------------------------------------------

    def start_phase(self, phase: str) -> None:
        """Mark the start of a phase.

        If the phase timer already exists and was stopped, calling this
        again resets it (for retries).

        Args:
            phase: Phase name (e.g. ``"chunking"``).
        """
        timer = _PhaseTimer(phase)
        timer.start()
        self._phases[phase] = timer
        logger.debug("Timer started for phase %s (%s)", phase, self.slug)

    def end_phase(self, phase: str) -> None:
        """Mark the end of a phase.

        Args:
            phase: Phase name.  Must have been started via :meth:`start_phase`.

        Raises:
            KeyError: If the phase was never started.
        """
        timer = self._phases.get(phase)
        if timer is None:
            msg = f"Phase {phase!r} was never started for {self.slug!r}"
            raise KeyError(msg)
        timer.stop()
        logger.debug(
            "Timer stopped for phase %s (%s): %.1fs",
            phase,
            self.slug,
            timer.duration_seconds,
        )

    def phase_duration(self, phase: str) -> float:
        """Return the duration (seconds) for a given phase.

        Returns 0.0 if the phase has not been tracked.
        """
        timer = self._phases.get(phase)
        if timer is None:
            return 0.0
        return timer.duration_seconds

    @property
    def total_duration_seconds(self) -> float:
        """Return the sum of all phase durations."""
        return sum(t.duration_seconds for t in self._phases.values())

    @property
    def phases_completed(self) -> int:
        """Return the number of phases that have both start and end times."""
        return sum(1 for t in self._phases.values() if t.ended)

    @property
    def phase_names(self) -> list[str]:
        """Return ordered list of phase names that have been tracked."""
        return list(self._phases.keys())

    # -- persistence --------------------------------------------------------

    def save(self) -> Path:
        """Persist metrics to YAML on disk.

        Returns:
            Path to the written file.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)

        phases_data: dict[str, dict[str, Any]] = {}
        for name, timer in self._phases.items():
            phases_data[name] = timer.to_dict()

        data: dict[str, Any] = {
            "pipeline": self.slug,
            "started": self.started,
            "phases": phases_data,
            "total": {
                "duration_seconds": round(self.total_duration_seconds, 1),
                "phases_completed": self.phases_completed,
            },
        }

        self._path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        logger.debug("Saved MCE metrics for %s", self.slug)
        return self._path

    @classmethod
    def load(cls, slug: str) -> MetricsTracker | None:
        """Load metrics from disk for the given slug.

        Returns:
            A populated ``MetricsTracker`` instance, or *None* if no file
            exists on disk.
        """
        path = _metrics_path(slug)
        if not path.exists():
            return None

        try:
            text = path.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
        except (yaml.YAMLError, OSError) as exc:
            logger.warning("Failed to load MCE metrics for %s: %s", slug, exc)
            return None

        if not isinstance(data, dict):
            return None

        mt = cls(slug)
        mt.started = data.get("started", mt.started)

        for phase_name, phase_data in data.get("phases", {}).items():
            if isinstance(phase_data, dict):
                mt._phases[phase_name] = _PhaseTimer.from_dict(phase_name, phase_data)

        mt._path = path
        logger.info(
            "Loaded MCE metrics for %s: %d phases, %.1fs total",
            slug,
            mt.phases_completed,
            mt.total_duration_seconds,
        )
        return mt

    def append_to_jsonl(self) -> None:
        """Append a summary line to the JSONL audit log.

        Non-fatal: swallows all exceptions so it never blocks pipeline work.
        """
        try:
            log_path = _jsonl_log_path()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            entry: dict[str, Any] = {
                "timestamp": _now_iso(),
                "pipeline": self.slug,
                "total_duration_seconds": round(self.total_duration_seconds, 1),
                "phases_completed": self.phases_completed,
                "phases": {
                    name: round(timer.duration_seconds, 1)
                    for name, timer in self._phases.items()
                },
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except Exception:
            logger.debug("Failed to write MCE metrics JSONL", exc_info=True)

    @property
    def metrics_path(self) -> Path:
        """Return the path to the YAML metrics file."""
        return self._path

    def to_dict(self) -> dict[str, Any]:
        """Return metrics as a plain dictionary (for embedding in reports)."""
        return {
            "pipeline": self.slug,
            "started": self.started,
            "phases": {name: timer.to_dict() for name, timer in self._phases.items()},
            "total": {
                "duration_seconds": round(self.total_duration_seconds, 1),
                "phases_completed": self.phases_completed,
            },
        }

    def __repr__(self) -> str:
        return (
            f"MetricsTracker(slug={self.slug!r}, "
            f"phases={self.phases_completed}, "
            f"total={self.total_duration_seconds:.1f}s)"
        )
