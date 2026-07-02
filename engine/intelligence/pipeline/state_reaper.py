"""
state_reaper.py -- Stale State Reaper
======================================

Scans `.claude/mission-control/mce/` for pipeline slugs stuck in
non-terminal states and marks them as ``failed`` with reason
``stale_state_recovery``.

This prevents the MCE Step Logger from misfiring on stale states
and ensures clean pipeline execution on fresh batches.

Run at the START of /process-inbox pre-flight, before any processing.

Usage:
    from engine.intelligence.pipeline.state_reaper import StaleStateReaper

    reaper = StaleStateReaper()
    result = reaper.run()
    # result = {"slug-name": "old_state", ...}

Constraints:
    - stdlib + PyYAML only
    - Never raises -- returns empty dict on error
    - Logs to stdout for operator visibility

Version: 1.0.0
Date: 2026-04-16
Story: STORY-PIP-004
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

logger = logging.getLogger("pipeline.state_reaper")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
MCE_STATE_DIR = PROJECT_DIR / ".claude" / "mission-control" / "mce"

# States that indicate the pipeline is DONE -- do not touch these.
TERMINAL_STATES = {"complete", "completed", "failed", "skipped"}


# ---------------------------------------------------------------------------
# StaleStateReaper
# ---------------------------------------------------------------------------


class StaleStateReaper:
    """Scans MCE state directories and marks non-terminal slugs as failed.

    Terminal states (untouched): complete, completed, failed, skipped.
    All other states (running, paused, in_progress, init, ingesting,
    batching, etc.) are considered stale and are reset to ``failed``.

    Args:
        mce_dir: Override the MCE state directory (for testing).
    """

    def __init__(self, mce_dir: Path | None = None) -> None:
        self._mce_dir = mce_dir or MCE_STATE_DIR

    def run(self) -> dict[str, str]:
        """Execute the reaper scan.

        Returns:
            Dict mapping slug name to its OLD state for all slugs
            that were marked as failed. Empty dict if none were changed.
        """
        if yaml is None:
            logger.warning("[REAPER] PyYAML not available -- skipping reaper")
            return {}

        if not self._mce_dir.exists() or not self._mce_dir.is_dir():
            logger.info("[REAPER] MCE state dir not found: %s", self._mce_dir)
            return {}

        marked: dict[str, str] = {}

        for slug_dir in sorted(self._mce_dir.iterdir()):
            if not slug_dir.is_dir():
                continue

            state_file = slug_dir / "pipeline_state.yaml"
            if not state_file.exists():
                continue

            try:
                result = self._process_slug(slug_dir.name, state_file)
                if result is not None:
                    marked[slug_dir.name] = result
            except Exception as exc:
                logger.warning("[REAPER] Error processing %s: %s", slug_dir.name, exc)

        # Summary log
        if marked:
            slugs_list = ", ".join(f"{s} (was: {st})" for s, st in marked.items())
            print(f"[REAPER] Marked {len(marked)} slugs as failed " f"(stale states): {slugs_list}")
            logger.info("[REAPER] Marked %d slugs as failed (stale states)", len(marked))
        else:
            logger.info("[REAPER] No stale slugs found -- all clean")

        return marked

    def _process_slug(self, slug: str, state_file: Path) -> str | None:
        """Process a single slug's pipeline_state.yaml.

        Returns:
            The old state string if it was marked, or None if skipped.
        """
        with open(state_file, encoding="utf-8") as f:
            state = yaml.safe_load(f)

        if not isinstance(state, dict):
            return None

        current_state = state.get("state", state.get("status", ""))
        if not current_state:
            return None

        # Skip terminal states
        if str(current_state).lower() in TERMINAL_STATES:
            return None

        # Mark as failed
        old_state = str(current_state)
        state["state"] = "failed"
        state["reason"] = "stale_state_recovery"
        state["recovered_at"] = datetime.now(UTC).isoformat()

        with open(state_file, "w", encoding="utf-8") as f:
            yaml.dump(state, f, default_flow_style=False, allow_unicode=True)

        print(f"[REAPER] Marked {slug} as failed (was: {old_state})")
        logger.info("[REAPER] Marked %s as failed (was: %s)", slug, old_state)

        return old_state


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def reap_stale_states(mce_dir: Path | None = None) -> dict[str, str]:
    """Run the stale state reaper and return results.

    Convenience wrapper for use in pre-flight pipelines.

    Args:
        mce_dir: Optional override for MCE state directory.

    Returns:
        Dict of {slug: old_state} for all marked slugs.
    """
    reaper = StaleStateReaper(mce_dir=mce_dir)
    return reaper.run()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    result = reap_stale_states()

    if result:
        print(f"\nSummary: Marked {len(result)} slugs as failed (stale states)")
        for slug, old in sorted(result.items()):
            print(f"  - {slug}: {old} -> failed")
        sys.exit(0)
    else:
        print("\nNo stale slugs found.")
        sys.exit(0)
