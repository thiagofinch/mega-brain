"""
batch_tracker.py -- Master Progress Panel: BatchStatusTracker
==============================================================
Tracks batch processing progress for /process-inbox parallel pipeline.
Maintains BATCH-STATUS.json with real-time stats and ETA calculation.

Story: PIP-008
Version: 1.0.0
Date: 2026-04-16
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(os.getenv("CLAUDE_PROJECT_DIR", ".")).resolve()
BATCH_STATUS_PATH = PROJECT_DIR / ".claude" / "mission-control" / "mce" / "BATCH-STATUS.json"


# ---------------------------------------------------------------------------
# BatchStatusTracker
# ---------------------------------------------------------------------------


class BatchStatusTracker:
    """Tracks batch processing state and calculates ETA.

    Maintains BATCH-STATUS.json at:
        .claude/mission-control/mce/BATCH-STATUS.json

    Schema:
        {
            "total": N,
            "processed": M,
            "failed": F,
            "active_workers": K,
            "eta": "HH:MM",
            "started_at": ISO,
            "last_updated": ISO,
            "status": "running" | "completed"
        }
    """

    def __init__(self, status_path: Path | None = None) -> None:
        self.status_path = status_path or BATCH_STATUS_PATH
        self._state: dict[str, Any] = {}
        self._active_slugs: list[str] = []

    # ── Initialization ───────────────────────────────────────────────────

    def initialize(self, total: int, max_workers: int = 4) -> None:
        """Create BATCH-STATUS.json with initial state at pipeline start."""
        now = datetime.now(UTC).isoformat()
        self._state = {
            "total": total,
            "processed": 0,
            "failed": 0,
            "active_workers": 0,
            "max_workers": max_workers,
            "eta": "--:--",
            "started_at": now,
            "last_updated": now,
            "status": "running",
        }
        self._active_slugs = []
        self._persist()
        logger.info("BatchStatusTracker initialized: total=%d, max_workers=%d", total, max_workers)

    # ── Worker Tracking ──────────────────────────────────────────────────

    def worker_started(self, slug: str) -> None:
        """Record a worker starting on a slug."""
        if slug not in self._active_slugs:
            self._active_slugs.append(slug)
        self._state["active_workers"] = len(self._active_slugs)
        self._state["last_updated"] = datetime.now(UTC).isoformat()
        self._persist()

    def worker_finished(self, slug: str) -> None:
        """Record a worker finishing a slug (remove from active)."""
        if slug in self._active_slugs:
            self._active_slugs.remove(slug)
        self._state["active_workers"] = len(self._active_slugs)

    # ── File Completion ──────────────────────────────────────────────────

    def record_file_complete(self, slug: str, status: str = "success") -> None:
        """Increment processed/failed count, recalculate ETA.

        Args:
            slug: Slug that was processed
            status: "success" or "failed"
        """
        self._state["processed"] = self._state.get("processed", 0) + 1
        if status == "failed":
            self._state["failed"] = self._state.get("failed", 0) + 1

        self._state["eta"] = self.calculate_eta()
        self._state["last_updated"] = datetime.now(UTC).isoformat()
        self._persist()

    # ── ETA Calculation ──────────────────────────────────────────────────

    def calculate_eta(self) -> str:
        """Calculate ETA based on processing rate.

        Formula: remaining / rate where rate = processed / elapsed_seconds
        Returns "HH:MM" or "--:--" if no files processed yet.
        """
        processed = self._state.get("processed", 0)
        total = self._state.get("total", 0)

        if processed == 0:
            return "--:--"

        started_at_str = self._state.get("started_at", "")
        if not started_at_str:
            return "--:--"

        try:
            started_at = datetime.fromisoformat(started_at_str)
            now = datetime.now(UTC)
            elapsed_seconds = (now - started_at).total_seconds()

            if elapsed_seconds <= 0:
                return "--:--"

            rate = processed / elapsed_seconds  # files per second
            remaining = total - processed

            if rate <= 0:
                return "--:--"

            eta_seconds = remaining / rate
            hours = int(eta_seconds // 3600)
            minutes = int((eta_seconds % 3600) // 60)
            return f"{hours:02d}:{minutes:02d}"
        except (ValueError, TypeError):
            return "--:--"

    # ── Batch Done ───────────────────────────────────────────────────────

    def mark_batch_done(self) -> None:
        """Mark batch as completed with final stats."""
        self._state["status"] = "completed"
        self._state["active_workers"] = 0
        self._state["eta"] = "00:00"
        self._state["last_updated"] = datetime.now(UTC).isoformat()
        self._active_slugs = []
        self._persist()
        logger.info(
            "Batch complete: %d/%d processed, %d failed",
            self._state.get("processed", 0),
            self._state.get("total", 0),
            self._state.get("failed", 0),
        )

    # ── Status Accessors ─────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        """Return current status dict (copy)."""
        status = dict(self._state)
        status["active_slugs"] = list(self._active_slugs)
        return status

    @property
    def elapsed_str(self) -> str:
        """Return formatted elapsed time HH:MM."""
        started_at_str = self._state.get("started_at", "")
        if not started_at_str:
            return "00:00"
        try:
            started_at = datetime.fromisoformat(started_at_str)
            elapsed = (datetime.now(UTC) - started_at).total_seconds()
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            return f"{hours:02d}:{minutes:02d}"
        except (ValueError, TypeError):
            return "00:00"

    def done_summary(self) -> str:
        """Return final summary string for terminal display."""
        total = self._state.get("total", 0)
        processed = self._state.get("processed", 0)
        return f"DONE -- {processed}/{total} files processed in {self.elapsed_str}"

    # ── Persistence ──────────────────────────────────────────────────────

    def _persist(self) -> None:
        """Write current state to BATCH-STATUS.json."""
        try:
            self.status_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.status_path, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.warning("Failed to persist BATCH-STATUS.json: %s", e)

    def load(self) -> None:
        """Load state from BATCH-STATUS.json if it exists."""
        if self.status_path.exists():
            try:
                with open(self.status_path, encoding="utf-8") as f:
                    self._state = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
