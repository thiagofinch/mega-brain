"""Pre-flight Bootstrap + Manifest for the MCE pipeline.

Creates the batch manifest and ensures all state files exist BEFORE
any worker is dispatched.  Enables crash recovery and resumability:
completed files are skipped on re-run, failed files are retried.

Manifest location:
    .claude/mission-control/mce/PROCESSED-MANIFEST.json

Manifest schema::

    {
      "created_at": "2026-04-16T10:00:00Z",
      "total_files": 118,
      "batch_id": "batch-2026-04-16-001",
      "{slug}/{filename}": "pending" | "completed" | "failed: {error_msg}"
    }

Thread safety:
    ``ManifestUpdater`` uses ``fcntl.flock(LOCK_EX)`` on every
    read-modify-write cycle so multiple workers can call
    ``mark_completed()`` / ``mark_failed()`` concurrently.

Version: 1.0.0  [STORY-PIP-003]
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_MANIFEST_PATH = _PROJECT_ROOT / ".claude" / "mission-control" / "mce" / "PROCESSED-MANIFEST.json"

_INGESTION_REGISTRY_PATH = _PROJECT_ROOT / ".data" / "ingestion-registry.json"

_MCE_BASE = _PROJECT_ROOT / ".claude" / "mission-control" / "mce"

# State files that must exist per slug (empty {} is valid initial state)
_SLUG_STATE_FILES = [
    "CHUNKS-STATE.json",
    "INSIGHTS-STATE.json",
    "CANONICAL-MAP.json",
    "NARRATIVES-STATE.json",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slug_from_path(file_path: Path) -> str:
    """Derive a slug from a file path.

    Looks for the parent directory name relative to the MCE base or
    knowledge directories.  Falls back to parent dir name.
    """
    return file_path.parent.name


def _generate_batch_id() -> str:
    """Generate a unique batch ID based on current timestamp."""
    now = datetime.now(UTC)
    return f"batch-{now.strftime('%Y-%m-%d')}-{now.strftime('%H%M%S')}"


def _file_key(file_path: Path) -> str:
    """Generate the manifest key for a file: ``{slug}/{filename}``."""
    slug = _slug_from_path(file_path)
    return f"{slug}/{file_path.name}"


# ---------------------------------------------------------------------------
# PreFlightBootstrap
# ---------------------------------------------------------------------------


class PreFlightBootstrap:
    """Pre-flight checks that run BEFORE any worker is dispatched.

    Responsibilities:
    1. Create/update ``PROCESSED-MANIFEST.json`` with all batch files.
    2. Bootstrap missing slug state files as ``{}``.
    3. Ensure ``.data/ingestion-registry.json`` exists.
    4. Filter out already-completed files for resumability.
    """

    def __init__(
        self,
        manifest_path: Path | None = None,
        mce_base: Path | None = None,
        ingestion_registry_path: Path | None = None,
    ) -> None:
        self._manifest_path = manifest_path or _MANIFEST_PATH
        self._mce_base = mce_base or _MCE_BASE
        self._ingestion_registry_path = ingestion_registry_path or _INGESTION_REGISTRY_PATH

    # ------------------------------------------------------------------
    # AC 1 + AC 2: create/update manifest
    # ------------------------------------------------------------------

    def create_manifest(self, file_list: list[Path]) -> Path:
        """Create or update the batch manifest.

        If a manifest already exists (previous run), only NEW files are
        added as ``"pending"`` -- existing entries are preserved (AC 8).

        Args:
            file_list: All files in the current batch.

        Returns:
            Path to the manifest file.
        """
        self._manifest_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing manifest if present (AC 8 -- preserve entries)
        existing: dict[str, Any] = {}
        if self._manifest_path.exists():
            try:
                raw = self._manifest_path.read_text(encoding="utf-8")
                existing = json.loads(raw) if raw.strip() else {}
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("PreFlight: corrupt manifest, starting fresh (%s)", exc)
                existing = {}

        # Metadata fields
        if "created_at" not in existing:
            existing["created_at"] = datetime.now(UTC).isoformat()
        if "batch_id" not in existing:
            existing["batch_id"] = _generate_batch_id()

        # Add new files as "pending", preserve existing entries
        for fp in file_list:
            key = _file_key(fp)
            if key not in existing:
                existing[key] = "pending"

        # Update total_files to reflect current batch scope
        file_keys = [k for k in existing if k not in ("created_at", "total_files", "batch_id")]
        existing["total_files"] = len(file_keys)

        self._manifest_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info(
            "PreFlight: manifest created/updated at %s (%d files)",
            self._manifest_path,
            existing["total_files"],
        )
        return self._manifest_path

    # ------------------------------------------------------------------
    # AC 3: bootstrap slug state files
    # ------------------------------------------------------------------

    def bootstrap_slug_state(self, slug: str) -> None:
        """Create missing state files for a slug as empty ``{}``.

        Args:
            slug: The slug directory name under ``mce/``.
        """
        slug_dir = self._mce_base / slug
        slug_dir.mkdir(parents=True, exist_ok=True)

        for state_file in _SLUG_STATE_FILES:
            state_path = slug_dir / state_file
            if not state_path.exists():
                state_path.write_text("{}", encoding="utf-8")
                logger.debug("PreFlight: bootstrapped %s/%s", slug, state_file)

    # ------------------------------------------------------------------
    # AC 4: ensure ingestion registry
    # ------------------------------------------------------------------

    def ensure_ingestion_registry(self) -> None:
        """Create ``.data/ingestion-registry.json`` if absent."""
        self._ingestion_registry_path.parent.mkdir(parents=True, exist_ok=True)

        if not self._ingestion_registry_path.exists():
            self._ingestion_registry_path.write_text("{}", encoding="utf-8")
            logger.info(
                "PreFlight: created ingestion registry at %s",
                self._ingestion_registry_path,
            )

    # ------------------------------------------------------------------
    # AC 7 + AC 8: filter pending files
    # ------------------------------------------------------------------

    def get_pending_files(self, file_list: list[Path]) -> list[Path]:
        """Return only files that are NOT completed in the manifest.

        Files with ``"pending"`` or ``"failed: ..."`` status ARE included
        (retry semantics).  Only ``"completed"`` files are skipped.

        Args:
            file_list: Full file list for the batch.

        Returns:
            Filtered list of files still needing processing.
        """
        if not self._manifest_path.exists():
            return list(file_list)

        try:
            manifest = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return list(file_list)

        pending: list[Path] = []
        for fp in file_list:
            key = _file_key(fp)
            status = manifest.get(key, "pending")
            if status != "completed":
                pending.append(fp)

        skipped = len(file_list) - len(pending)
        if skipped > 0:
            logger.info(
                "PreFlight: skipping %d already-completed files, " "%d remaining",
                skipped,
                len(pending),
            )

        return pending

    # ------------------------------------------------------------------
    # Full pre-flight run
    # ------------------------------------------------------------------

    def run(self, file_list: list[Path]) -> list[Path]:
        """Execute the full pre-flight sequence.

        1. Ensure ingestion registry exists (AC 4).
        2. Create/update manifest (AC 1, 2, 8).
        3. Bootstrap slug state files for all slugs (AC 3).
        4. Return pending files only (AC 7).

        Args:
            file_list: All files in the current batch.

        Returns:
            List of files still needing processing.
        """
        # AC 4
        self.ensure_ingestion_registry()

        # AC 1 + AC 2 + AC 8
        self.create_manifest(file_list)

        # AC 3: bootstrap state for all unique slugs
        slugs_seen: set[str] = set()
        for fp in file_list:
            slug = _slug_from_path(fp)
            if slug not in slugs_seen:
                self.bootstrap_slug_state(slug)
                slugs_seen.add(slug)

        # AC 7
        return self.get_pending_files(file_list)


# ---------------------------------------------------------------------------
# ManifestUpdater (thread-safe)
# ---------------------------------------------------------------------------


class ManifestUpdater:
    """Thread-safe manifest writer for concurrent workers.

    Uses ``fcntl.flock(LOCK_EX)`` on every read-modify-write cycle
    so multiple workers can safely update the manifest simultaneously.
    """

    def __init__(self, manifest_path: Path | None = None) -> None:
        self._manifest_path = manifest_path or _MANIFEST_PATH

    # ------------------------------------------------------------------
    # AC 5: mark completed
    # ------------------------------------------------------------------

    def mark_completed(self, file_path: str) -> None:
        """Mark a file as completed in the manifest.

        Args:
            file_path: The manifest key (``{slug}/{filename}``).
        """
        self._update_entry(file_path, "completed")

    # ------------------------------------------------------------------
    # AC 6: mark failed
    # ------------------------------------------------------------------

    def mark_failed(self, file_path: str, error: str) -> None:
        """Mark a file as failed in the manifest with error detail.

        Args:
            file_path: The manifest key (``{slug}/{filename}``).
            error: Error message describing the failure.
        """
        self._update_entry(file_path, f"failed: {error}")

    # ------------------------------------------------------------------
    # Internal: thread-safe read-modify-write
    # ------------------------------------------------------------------

    def _update_entry(self, key: str, value: str) -> None:
        """Thread-safe update of a single manifest entry.

        Pattern: open -> flock(LOCK_EX) -> read JSON -> update key ->
        write JSON -> funlock -> close.
        """
        path = self._manifest_path

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Open file for read+write (create if missing)
        fd = os.open(str(path), os.O_RDWR | os.O_CREAT)
        try:
            # Acquire exclusive lock -- blocks until available
            fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                # Read current content
                with os.fdopen(os.dup(fd), "r", encoding="utf-8") as rf:
                    rf.seek(0)
                    content = rf.read()

                manifest: dict[str, Any] = {}
                if content.strip():
                    try:
                        manifest = json.loads(content)
                    except json.JSONDecodeError:
                        logger.warning(
                            "ManifestUpdater: corrupt manifest during "
                            "update, preserving what we can"
                        )
                        manifest = {}

                # Update the entry
                manifest[key] = value

                # Write back (truncate first)
                os.lseek(fd, 0, os.SEEK_SET)
                os.ftruncate(fd, 0)
                data = json.dumps(manifest, indent=2, ensure_ascii=False)
                os.write(fd, data.encode("utf-8"))

            finally:
                # Release lock
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    # ------------------------------------------------------------------
    # Utility: read current status
    # ------------------------------------------------------------------

    def get_status(self, file_path: str) -> str | None:
        """Read the current status of a file from the manifest.

        Returns:
            Status string or None if not found.
        """
        if not self._manifest_path.exists():
            return None

        try:
            manifest = json.loads(self._manifest_path.read_text(encoding="utf-8"))
            return manifest.get(file_path)
        except (json.JSONDecodeError, OSError):
            return None
