"""
agent_gatekeeper.py -- Art. VII Compliance: L2 vs L3 Agent Creation Gate
=========================================================================
Before Phase 5 creates or updates an agent, this gate checks existence:

  - Agent EXISTS  -> L2 autonomous cascade update (no approval needed)
  - Agent ABSENT  -> L3 queue for human approval (appended to .data/l3-approval-queue.jsonl)

Thread-safe: uses fcntl.flock for concurrent worker access to the queue file.
Deduplication: same slug is never queued twice (merges source_files instead).

Story: PIP-007
Version: 1.0.0
Date: 2026-04-16
"""

from __future__ import annotations

import fcntl
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.intelligence.utils.agent_files import find_agent_file  # MCE-13.6
from engine.paths import AGENTS_BUSINESS, AGENTS_EXTERNAL, ROOT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

DATA_DIR = ROOT / ".data"
L3_QUEUE_PATH = DATA_DIR / "l3-approval-queue.jsonl"


# ---------------------------------------------------------------------------
# AgentGatekeeper
# ---------------------------------------------------------------------------


class AgentGatekeeper:
    """Phase 5 gate: routes slugs to L2 update or L3 approval queue.

    Usage:
        gatekeeper = AgentGatekeeper()
        if gatekeeper.agent_exists(slug):
            cascade_update_existing(slug)
            gatekeeper.record_l2_update(slug)
        else:
            gatekeeper.queue_for_approval(slug, source_files, batch_id)
    """

    def __init__(self, queue_path: Path | None = None) -> None:
        self.queue_path = queue_path or L3_QUEUE_PATH
        self._l2_count = 0
        self._l3_count = 0

    # ── Existence Check ───────────────────────────────────────────────────

    def agent_exists(self, slug: str) -> bool:
        """Check if agent file exists in external/ or business/ paths.

        MCE-13.6: uses find_agent_file for case-insensitive lookup, supporting
        both the new lowercase convention and legacy UPPERCASE naming.

        Checks:
          - agents/external/{slug}/agent.md (or AGENT.md fallback)
          - agents/business/{slug}/agent.md (or AGENT.md fallback)
          - agents/business/collaborators/{slug}/agent.md (or AGENT.md fallback)
        """
        dirs_to_check = [
            AGENTS_EXTERNAL / slug,
            AGENTS_BUSINESS / slug,
            AGENTS_BUSINESS / "collaborators" / slug,
        ]
        return any(find_agent_file(d, "agent.md") is not None for d in dirs_to_check)

    # ── L2 Recording ─────────────────────────────────────────────────────

    def record_l2_update(self, slug: str) -> None:
        """Record that a slug was updated via L2 autonomous path."""
        self._l2_count += 1
        logger.info("[L2] Agent updated autonomously: %s", slug)

    # ── L3 Queue ─────────────────────────────────────────────────────────

    def is_already_queued(self, slug: str) -> bool:
        """Check if slug already has a pending entry in the approval queue."""
        if not self.queue_path.exists():
            return False
        try:
            with open(self.queue_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("slug") == slug and entry.get("status") == "pending":
                            return True
                    except json.JSONDecodeError:
                        continue
        except OSError:
            return False
        return False

    def queue_for_approval(
        self,
        slug: str,
        source_files: list[str | Path],
        batch_id: str = "",
    ) -> None:
        """Append slug to L3 approval queue with deduplication.

        Thread-safe via fcntl.flock. If slug already pending, merges
        source_files into existing entry rather than creating duplicate.
        """
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)

        source_strs = [str(f) for f in source_files]
        now_iso = datetime.now(UTC).isoformat()

        # Open file for read+write (create if absent)
        with open(self.queue_path, "a+", encoding="utf-8") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                # Read all existing entries
                fh.seek(0)
                lines = fh.readlines()
                entries: list[dict[str, Any]] = []
                found_idx: int | None = None

                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        entries.append({})
                        continue
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                        if entry.get("slug") == slug and entry.get("status") == "pending":
                            found_idx = i
                    except json.JSONDecodeError:
                        entries.append({})

                if found_idx is not None:
                    # Merge source_files into existing entry (dedup)
                    existing = entries[found_idx]
                    existing_files = set(existing.get("source_files", []))
                    existing_files.update(source_strs)
                    existing["source_files"] = sorted(existing_files)
                    existing["last_updated"] = now_iso
                    entries[found_idx] = existing

                    # Rewrite the entire file
                    fh.seek(0)
                    fh.truncate()
                    for entry in entries:
                        if entry:
                            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        else:
                            fh.write("\n")
                else:
                    # Append new entry
                    new_entry = {
                        "slug": slug,
                        "requested_at": now_iso,
                        "source_files": source_strs,
                        "status": "pending",
                        "batch_id": batch_id,
                    }
                    fh.seek(0, 2)  # Seek to end
                    fh.write(json.dumps(new_entry, ensure_ascii=False) + "\n")
                    self._l3_count += 1

                logger.info("[L3] Agent queued for approval: %s", slug)
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)

    # ── Gate Decision ────────────────────────────────────────────────────

    def gate(
        self,
        slug: str,
        source_files: list[str | Path],
        batch_id: str = "",
    ) -> str:
        """Run the full gate decision for a slug.

        Returns:
            "l2" if agent exists (cascade update path)
            "l3" if agent is new (queued for approval)
        """
        if self.agent_exists(slug):
            self.record_l2_update(slug)
            return "l2"
        else:
            self.queue_for_approval(slug, source_files, batch_id)
            return "l3"

    # ── Summary ──────────────────────────────────────────────────────────

    @property
    def l2_count(self) -> int:
        return self._l2_count

    @property
    def l3_count(self) -> int:
        return self._l3_count

    def summary(self) -> str:
        """Return pipeline-end summary string."""
        return (
            f"Phase 5 complete: {self._l2_count} agents updated (L2 autonomous), "
            f"{self._l3_count} new agents queued for L3 approval"
        )
