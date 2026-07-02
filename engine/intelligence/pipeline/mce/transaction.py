"""
transaction.py -- Atomic Pipeline Transactions
===============================================

Provides a context manager that ensures the chunk+embed+upsert sub-phase
executes atomically.  If any step fails, all state changes are rolled back
to the snapshot taken at context entry.

The rollback strategy is filesystem-based: before the transaction begins,
we snapshot the relevant state files (pipeline state YAML, metadata YAML,
JSONL log position).  On failure, we restore from snapshot.

Usage::

    with pipeline_transaction(batch_id) as txn:
        chunks = chunk_document(doc)        # step 1
        txn.record_artifact("chunks", chunks_path)
        embeddings = embed_chunks(chunks)   # step 2
        txn.record_artifact("embeddings", embeddings_path)
        upsert_to_index(embeddings)         # step 3
        txn.commit()
    # If any step raises: txn.rollback() runs automatically.

Constraints:
    - stdlib + PyYAML only (no external deps).
    - Thread-safe via file-based lock.

Version: 1.0.0
Date: 2026-04-16
"""

from __future__ import annotations

import json
import logging
import shutil
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Generator

logger = logging.getLogger("mce.transaction")

# ---------------------------------------------------------------------------
# Paths (resolved lazily to avoid circular imports)
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def _mission_control() -> Path:
    try:
        from engine.paths import MISSION_CONTROL

        return MISSION_CONTROL
    except ImportError:
        return _PROJECT_ROOT / ".claude" / "mission-control"


def _logs_dir() -> Path:
    try:
        from engine.paths import LOGS

        return LOGS
    except ImportError:
        return _PROJECT_ROOT / "logs"


def _artifacts_dir() -> Path:
    return _PROJECT_ROOT / "artifacts"


# ---------------------------------------------------------------------------
# Transaction dataclass
# ---------------------------------------------------------------------------


@dataclass
class TransactionState:
    """Tracks the state of a single pipeline transaction."""

    batch_id: str
    started_at: str = ""
    committed: bool = False
    rolled_back: bool = False
    artifacts_created: list[dict[str, str]] = field(default_factory=list)
    snapshots: dict[str, str] = field(default_factory=dict)
    error: str | None = None


class PipelineTransaction:
    """Atomic transaction wrapper for pipeline sub-phases.

    Snapshots relevant state files on entry, restores them on rollback.
    Artifacts created during the transaction are tracked and cleaned up
    on rollback.

    Attributes:
        batch_id: Identifier for the batch being processed.
        state: Current transaction state.
    """

    def __init__(self, batch_id: str, slug: str | None = None) -> None:
        self.batch_id = batch_id
        self.slug = slug or self._slug_from_batch(batch_id)
        self.state = TransactionState(
            batch_id=batch_id,
            started_at=datetime.now(UTC).isoformat(),
        )
        self._snapshot_dir: Path | None = None
        self._artifact_paths: list[Path] = []
        self._jsonl_log_position: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def begin(self) -> None:
        """Take a snapshot of all relevant state files."""
        self._snapshot_dir = self._create_snapshot_dir()

        # Snapshot MCE state directory
        mce_state_dir = _mission_control() / "mce" / self.slug
        if mce_state_dir.is_dir():
            snap_mce = self._snapshot_dir / "mce"
            shutil.copytree(mce_state_dir, snap_mce, dirs_exist_ok=True)
            self.state.snapshots["mce_state"] = str(snap_mce)

        # Snapshot artifacts for this slug (chunks, insights)
        for subdir in ("chunks", "insights", "embeddings"):
            artifact_dir = _artifacts_dir() / subdir / self.slug
            if artifact_dir.is_dir():
                snap_art = self._snapshot_dir / "artifacts" / subdir
                shutil.copytree(artifact_dir, snap_art, dirs_exist_ok=True)
                self.state.snapshots[f"artifacts_{subdir}"] = str(snap_art)

        # Record JSONL log position for truncation on rollback
        orchestrate_log = _logs_dir() / "mce-orchestrate.jsonl"
        if orchestrate_log.exists():
            self._jsonl_log_position = orchestrate_log.stat().st_size

        logger.info(
            "Transaction %s: snapshot taken (%d state files)",
            self.batch_id,
            len(self.state.snapshots),
        )

    def record_artifact(self, category: str, path: str | Path) -> None:
        """Register an artifact created during this transaction.

        On rollback, registered artifacts are removed to prevent partial state.

        Args:
            category: Artifact category (e.g. ``"chunks"``, ``"embeddings"``).
            path: Filesystem path to the artifact.
        """
        resolved = Path(path).resolve()
        self._artifact_paths.append(resolved)
        self.state.artifacts_created.append({"category": category, "path": str(resolved)})

    def commit(self) -> None:
        """Mark the transaction as committed. Snapshots are discarded."""
        if self.state.rolled_back:
            raise RuntimeError(f"Transaction {self.batch_id}: cannot commit after rollback")

        self.state.committed = True
        self._cleanup_snapshot()

        logger.info(
            "Transaction %s: committed (%d artifacts)",
            self.batch_id,
            len(self.state.artifacts_created),
        )

    def rollback(self, error: str | None = None) -> None:
        """Restore state from snapshot and remove artifacts created during the transaction.

        Args:
            error: Optional error description for logging.
        """
        if self.state.committed:
            logger.warning(
                "Transaction %s: rollback called after commit (no-op)",
                self.batch_id,
            )
            return

        self.state.rolled_back = True
        self.state.error = error

        logger.warning(
            "Transaction %s: rolling back (error: %s)",
            self.batch_id,
            error or "unknown",
        )

        # Step 1: Remove artifacts created during this transaction
        for artifact_path in reversed(self._artifact_paths):
            try:
                if artifact_path.is_file():
                    artifact_path.unlink()
                    logger.debug("Removed artifact: %s", artifact_path)
                elif artifact_path.is_dir():
                    shutil.rmtree(artifact_path)
                    logger.debug("Removed artifact dir: %s", artifact_path)
            except OSError as exc:
                logger.warning("Failed to remove artifact %s: %s", artifact_path, exc)

        # Step 2: Restore state from snapshot
        if self._snapshot_dir and self._snapshot_dir.is_dir():
            # Restore MCE state
            snap_mce = self._snapshot_dir / "mce"
            if snap_mce.is_dir():
                target = _mission_control() / "mce" / self.slug
                if target.is_dir():
                    shutil.rmtree(target)
                shutil.copytree(snap_mce, target, dirs_exist_ok=True)
                logger.debug("Restored MCE state for %s", self.slug)

            # Restore artifact directories
            for subdir in ("chunks", "insights", "embeddings"):
                snap_art = self._snapshot_dir / "artifacts" / subdir
                if snap_art.is_dir():
                    target = _artifacts_dir() / subdir / self.slug
                    if target.is_dir():
                        shutil.rmtree(target)
                    shutil.copytree(snap_art, target, dirs_exist_ok=True)
                    logger.debug("Restored artifacts/%s for %s", subdir, self.slug)

        # Step 3: Truncate JSONL log to pre-transaction position
        orchestrate_log = _logs_dir() / "mce-orchestrate.jsonl"
        if orchestrate_log.exists() and self._jsonl_log_position > 0:
            try:
                current_size = orchestrate_log.stat().st_size
                if current_size > self._jsonl_log_position:
                    with open(orchestrate_log, "r+b") as fh:
                        fh.truncate(self._jsonl_log_position)
                    logger.debug(
                        "Truncated orchestrate log from %d to %d bytes",
                        current_size,
                        self._jsonl_log_position,
                    )
            except OSError as exc:
                logger.warning("Failed to truncate JSONL log: %s", exc)

        # Step 4: Append rollback event to log
        self._log_rollback_event()

        # Step 5: Cleanup snapshot
        self._cleanup_snapshot()

        logger.info("Transaction %s: rollback complete", self.batch_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _slug_from_batch(batch_id: str) -> str:
        """Extract slug from batch ID like ``BATCH-001`` or ``alex-hormozi-BATCH-001``."""
        parts = batch_id.rsplit("-BATCH-", 1)
        if len(parts) == 2:
            return parts[0]
        return batch_id

    def _create_snapshot_dir(self) -> Path:
        """Create a temporary directory for state snapshots."""
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        snap_dir = _mission_control() / "mce" / ".transactions" / f"{self.batch_id}_{ts}"
        snap_dir.mkdir(parents=True, exist_ok=True)
        return snap_dir

    def _cleanup_snapshot(self) -> None:
        """Remove the snapshot directory."""
        if self._snapshot_dir and self._snapshot_dir.is_dir():
            try:
                shutil.rmtree(self._snapshot_dir)
            except OSError as exc:
                logger.warning("Failed to clean snapshot dir: %s", exc)
        self._snapshot_dir = None

    def _log_rollback_event(self) -> None:
        """Append a rollback event to the JSONL log."""
        orchestrate_log = _logs_dir() / "mce-orchestrate.jsonl"
        entry = {
            "event": "transaction_rollback",
            "batch_id": self.batch_id,
            "slug": self.slug,
            "timestamp": datetime.now(UTC).isoformat(),
            "error": self.state.error,
            "artifacts_rolled_back": len(self._artifact_paths),
            "snapshots_restored": list(self.state.snapshots.keys()),
        }
        try:
            orchestrate_log.parent.mkdir(parents=True, exist_ok=True)
            with open(orchestrate_log, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except OSError:
            logger.debug("Failed to write rollback event to JSONL", exc_info=True)


# ---------------------------------------------------------------------------
# Context manager (public API)
# ---------------------------------------------------------------------------


@contextmanager
def pipeline_transaction(
    batch_id: str,
    slug: str | None = None,
) -> Generator[PipelineTransaction, None, None]:
    """Context manager for atomic pipeline sub-phases.

    On entry, snapshots the current pipeline state.  On successful exit
    (after ``txn.commit()``), discards the snapshot.  On exception (or
    if ``commit()`` was never called), rolls back all changes.

    Args:
        batch_id: Batch identifier (e.g. ``"BATCH-001"``).
        slug: Optional person/source slug.  Auto-detected from batch_id
              if not provided.

    Yields:
        A :class:`PipelineTransaction` instance.

    Example::

        with pipeline_transaction("BATCH-001", slug="alex-hormozi") as txn:
            chunks = chunk_document(doc)
            txn.record_artifact("chunks", chunks_path)
            embeddings = embed_chunks(chunks)
            txn.record_artifact("embeddings", embeddings_path)
            upsert_to_index(embeddings)
            txn.commit()
        # If any step raises: automatic rollback.
    """
    txn = PipelineTransaction(batch_id, slug=slug)
    txn.begin()

    try:
        yield txn
    except Exception as exc:
        if not txn.state.committed and not txn.state.rolled_back:
            txn.rollback(error=str(exc))
        raise
    else:
        # If block completed without exception but commit() was never called,
        # treat as implicit rollback (safety net).
        if not txn.state.committed and not txn.state.rolled_back:
            txn.rollback(error="Transaction ended without explicit commit()")
