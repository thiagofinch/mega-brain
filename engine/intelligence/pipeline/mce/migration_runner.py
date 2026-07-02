"""
migration_runner.py -- Versioned Migration System for MCE Pipeline
==================================================================

Discovers, orders, and executes migration files from the ``migrations/``
directory.  Each migration is a Python module with a ``Migration`` class
that has a ``version`` attribute and an ``up(state_data)`` method.

The runner tracks which migrations have been applied via a
``_migration_version`` field in the pipeline state YAML file.  This
makes the system **idempotent**: running the same migrations again
is a no-op.

Flow::

    detect_version(state_data)
        -> "000" (no version field = fresh/legacy)
        -> "001" (already ran migration 001)

    get_pending("000")
        -> [Migration_001, Migration_002, ...]  # all after "000"

    run_pending(state_data)
        -> detect -> get_pending -> execute each -> update version

Usage::

    from engine.intelligence.pipeline.mce.migration_runner import MigrationRunner

    runner = MigrationRunner()
    state_data = yaml.safe_load(state_file.read_text())
    state_data = runner.run_pending(state_data)
    # state_data now has _migration_version updated

Version: 1.0.0
Date: 2026-04-01
Epic: MCE-V2 / Story MCE2-1.7
"""

from __future__ import annotations

import importlib
import logging
import re
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger("mce.migration_runner")

# ---------------------------------------------------------------------------
# Migration protocol -- what every migration class must look like
# ---------------------------------------------------------------------------


class MigrationProtocol(Protocol):
    """Structural type for migration classes."""

    version: str
    description: str

    def up(self, state_data: dict[str, Any]) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Regex to match migration filenames: 001_something.py, 002_another.py
_MIGRATION_FILE_RE = re.compile(r"^(\d{3})_\w+\.py$")

# The key used in pipeline_state.yaml to track migration version
VERSION_KEY = "_migration_version"

# Default version when no migrations have been applied yet
DEFAULT_VERSION = "000"

# Path to the migrations directory (sibling of this file)
_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


# ---------------------------------------------------------------------------
# MigrationRunner
# ---------------------------------------------------------------------------


class MigrationRunner:
    """Discover, order, and execute pipeline state migrations.

    The runner scans the ``migrations/`` directory for numbered Python
    modules, loads their ``Migration`` class, and executes pending ones
    in version order.

    Args:
        migrations_dir: Override the default migrations directory.
                        Useful for testing.
    """

    def __init__(self, migrations_dir: Path | None = None) -> None:
        self._migrations_dir = migrations_dir or _MIGRATIONS_DIR
        self._migrations: list[MigrationProtocol] | None = None

    # -- Discovery ----------------------------------------------------------

    def _discover(self) -> list[MigrationProtocol]:
        """Scan the migrations directory and load all Migration classes.

        Returns a list sorted by version (ascending).

        Each migration file must:
        - Match the pattern ``NNN_description.py`` (3-digit prefix)
        - Contain a ``Migration`` class with ``version`` and ``up()``
        """
        if self._migrations is not None:
            return self._migrations

        migrations: list[MigrationProtocol] = []

        if not self._migrations_dir.is_dir():
            logger.warning("Migrations directory not found: %s", self._migrations_dir)
            self._migrations = []
            return self._migrations

        for file_path in sorted(self._migrations_dir.iterdir()):
            match = _MIGRATION_FILE_RE.match(file_path.name)
            if match is None:
                continue

            version = match.group(1)
            module_name = file_path.stem  # e.g., "001_legacy_states"

            try:
                # Build the full module path for importlib
                package = "core.intelligence.pipeline.mce.migrations"
                spec_name = f"{package}.{module_name}"
                module = importlib.import_module(spec_name)

                migration_cls = getattr(module, "Migration", None)
                if migration_cls is None:
                    logger.warning(
                        "Migration file %s has no Migration class, skipping",
                        file_path.name,
                    )
                    continue

                instance = migration_cls()

                # Validate version consistency
                if instance.version != version:
                    logger.warning(
                        "Migration %s declares version=%r but filename says %r, "
                        "using filename version",
                        file_path.name,
                        instance.version,
                        version,
                    )
                    instance.version = version

                migrations.append(instance)
                logger.debug("Discovered migration: %s (%s)", version, instance.description)

            except Exception as exc:
                logger.error("Failed to load migration %s: %s", file_path.name, exc)

        self._migrations = sorted(migrations, key=lambda m: m.version)
        logger.info("Discovered %d migration(s)", len(self._migrations))
        return self._migrations

    # -- Version Detection --------------------------------------------------

    def detect_version(self, state_data: dict[str, Any]) -> str:
        """Read the current migration version from state data.

        Args:
            state_data: The pipeline state dict (from YAML).

        Returns:
            The version string (e.g., ``"001"``), or ``"000"`` if no
            version tracking exists yet (legacy/fresh state).
        """
        return state_data.get(VERSION_KEY, DEFAULT_VERSION)

    # -- Pending Calculation ------------------------------------------------

    def get_pending(self, current_version: str) -> list[MigrationProtocol]:
        """Return migrations that need to run (version > current).

        Args:
            current_version: The version string to compare against.

        Returns:
            List of Migration instances whose version is greater than
            ``current_version``, sorted ascending.
        """
        all_migrations = self._discover()
        pending = [m for m in all_migrations if m.version > current_version]

        if pending:
            logger.info(
                "Found %d pending migration(s) after version %s: %s",
                len(pending),
                current_version,
                [m.version for m in pending],
            )
        else:
            logger.debug("No pending migrations after version %s", current_version)

        return pending

    # -- Execution ----------------------------------------------------------

    def run_pending(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Detect version, run all pending migrations, update version.

        This is the main entry point.  It:
        1. Reads ``_migration_version`` from state_data
        2. Finds all migrations with version > current
        3. Executes each in order via ``migration.up(state_data)``
        4. Updates ``_migration_version`` to the last applied version

        Idempotent: if no migrations are pending, state_data is returned
        unchanged (no version bump, no side effects).

        Args:
            state_data: The pipeline state dict (from YAML).

        Returns:
            The (possibly modified) state dict with updated
            ``_migration_version``.
        """
        current = self.detect_version(state_data)
        pending = self.get_pending(current)

        if not pending:
            logger.debug("State is up to date at version %s", current)
            return state_data

        logger.info(
            "Running %d migration(s): %s -> %s",
            len(pending),
            current,
            pending[-1].version,
        )

        for migration in pending:
            logger.info(
                "Applying migration %s: %s",
                migration.version,
                migration.description,
            )
            try:
                state_data = migration.up(state_data)
                # Update version after each successful migration
                state_data[VERSION_KEY] = migration.version
                logger.info("Migration %s applied successfully", migration.version)
            except Exception as exc:
                logger.error(
                    "Migration %s failed: %s -- halting migration chain",
                    migration.version,
                    exc,
                )
                # Stop on first failure -- don't skip broken migrations
                break

        return state_data
