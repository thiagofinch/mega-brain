"""
session_compactor.py -- Orchestrator-Level Session Context Compaction
=====================================================================

Compacts accumulated context at the ORCHESTRATOR level (not chunk-level).
This is distinct from ``context_compactor.py`` which operates on individual
chunks within a single step -- this module operates across the full session
of an orchestrator run, summarizing completed steps while keeping recent
ones intact.

Strategy
--------
1. **GROUP** -- Split session context into step boundaries.
2. **CLASSIFY** -- For each step, classify content as preservable or
   discardable.
3. **COMPACT** -- Old (non-recent) steps are summarized, keeping only
   facts, decisions, and entity definitions while discarding verbose
   reasoning and failed attempts.
4. **TRIGGER** -- Compaction fires automatically when accumulated context
   exceeds 80% of the token budget.

Preservation Rules
------------------
- Facts (explicit assertions, measurements, data points)
- Decisions (choices made with rationale)
- Entity definitions (named entities, schemas, configs introduced)
- Step outcomes (final result of each completed step)

Discard Rules
-------------
- Verbose reasoning chains (intermediate thinking)
- Failed attempts and their error traces
- Repetitive confirmations and acknowledgments
- Raw tool output that has already been summarized

Usage::

    from engine.intelligence.pipeline.mce.session_compactor import SessionCompactor

    compactor = SessionCompactor(token_budget=128_000)
    result = compactor.compact(session_entries)
    # result["entries"]       -- compacted entry list
    # result["stats"]         -- compaction statistics
    # result["compacted"]     -- True if compaction occurred
    # result["trigger_fired"] -- True if 80% threshold was exceeded

Constraints:
    - stdlib + token_counter only (no LLM calls).
    - Never mutates input entries (returns new lists/dicts).
    - Preserves step ordering.

Version: 1.0.0
Date: 2026-04-02
Story: MCE22-2.5
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from engine.intelligence.pipeline.mce.token_counter import count_tokens

logger = logging.getLogger("mce.session_compactor")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_TOKEN_BUDGET: int = 128_000
DEFAULT_TRIGGER_PCT: float = 0.80  # Trigger compaction at 80% of budget
DEFAULT_PRESERVE_RECENT: int = 2  # Always keep the last N steps intact
DEFAULT_SUMMARY_MAX_TOKENS: int = 200  # Max tokens per step summary


# ---------------------------------------------------------------------------
# Step Entry Protocol
# ---------------------------------------------------------------------------

# Session entries are dicts with at least:
#   step_id: str          -- unique step identifier
#   step_index: int       -- ordinal position in the session
#   content: str          -- the text content of the step
#   role: str             -- "orchestrator" | "tool" | "user" | "system"
#   status: str           -- "completed" | "in_progress" | "failed"
#   metadata: dict        -- optional structured metadata
#
# Content classification markers (embedded in content):
#   [DECISION] ...        -- preserved
#   [FACT] ...            -- preserved
#   [ENTITY] ...          -- preserved
#   [REASONING] ...       -- discardable
#   [ATTEMPT] ...         -- discardable if step completed
#   [ERROR] ...           -- discardable if step completed


# ---------------------------------------------------------------------------
# Content Classifier
# ---------------------------------------------------------------------------

# Patterns that signal preservable content
_PRESERVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\[DECISION\]", re.IGNORECASE),
    re.compile(r"\[FACT\]", re.IGNORECASE),
    re.compile(r"\[ENTITY\]", re.IGNORECASE),
    re.compile(r"\[OUTCOME\]", re.IGNORECASE),
    re.compile(r"\[RESULT\]", re.IGNORECASE),
    re.compile(
        r"(?:decided|chosen|selected|confirmed|defined|established)\s+(?:to|that)", re.IGNORECASE
    ),
    re.compile(r"(?:the answer is|conclusion:|final result:|output:)", re.IGNORECASE),
]

# Patterns that signal discardable content
_DISCARD_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\[REASONING\]", re.IGNORECASE),
    re.compile(r"\[ATTEMPT\]", re.IGNORECASE),
    re.compile(r"\[ERROR\]", re.IGNORECASE),
    re.compile(r"\[RETRY\]", re.IGNORECASE),
    re.compile(r"(?:let me think|thinking through|considering|hmm)", re.IGNORECASE),
    re.compile(r"(?:traceback|exception|stack trace)", re.IGNORECASE),
    re.compile(r"(?:trying again|retrying|attempt \d+)", re.IGNORECASE),
]


def classify_line(line: str) -> str:
    """Classify a single line as 'preserve' or 'discard'.

    Lines matching preserve patterns are kept.  Lines matching discard
    patterns are dropped.  Ambiguous lines default to 'preserve' (safe).

    Args:
        line: A single line of step content.

    Returns:
        ``"preserve"`` or ``"discard"``.
    """
    stripped = line.strip()
    if not stripped:
        return "discard"

    for pat in _PRESERVE_PATTERNS:
        if pat.search(stripped):
            return "preserve"

    for pat in _DISCARD_PATTERNS:
        if pat.search(stripped):
            return "discard"

    # Default: preserve (safe -- never lose data by accident)
    return "preserve"


def extract_preservable_content(content: str) -> str:
    """Extract only the preservable lines from step content.

    Splits content into lines, classifies each, and joins the
    preserved lines back together.

    Args:
        content: Full step content text.

    Returns:
        Filtered text with only preservable content.
    """
    if not content:
        return ""

    lines = content.split("\n")
    preserved = [line for line in lines if classify_line(line) == "preserve"]
    return "\n".join(preserved).strip()


# ---------------------------------------------------------------------------
# Step Grouping
# ---------------------------------------------------------------------------


def group_by_step(entries: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group session entries by step_id into ordered step groups.

    Entries without a ``step_id`` are placed in a group with the
    previous step, or in their own group if they come first.

    Args:
        entries: List of session entry dicts.

    Returns:
        List of step groups (each group is a list of entries sharing
        the same step_id).
    """
    if not entries:
        return []

    groups: list[list[dict[str, Any]]] = []
    current_step_id: str | None = None
    current_group: list[dict[str, Any]] = []

    for entry in entries:
        step_id = entry.get("step_id")

        if step_id != current_step_id:
            if current_group:
                groups.append(current_group)
            current_group = [entry]
            current_step_id = step_id
        else:
            current_group.append(entry)

    if current_group:
        groups.append(current_group)

    return groups


# ---------------------------------------------------------------------------
# Step Summarizer
# ---------------------------------------------------------------------------


def summarize_step(
    step_entries: list[dict[str, Any]],
    max_tokens: int = DEFAULT_SUMMARY_MAX_TOKENS,
) -> dict[str, Any]:
    """Summarize a completed step into a compact representation.

    Extracts preservable content from all entries in the step,
    truncates to ``max_tokens``, and produces a summary entry.

    Args:
        step_entries: All entries belonging to a single step.
        max_tokens: Maximum tokens for the summary.

    Returns:
        A single summary entry dict with the compacted content.
    """
    if not step_entries:
        return {"step_id": "unknown", "content": "", "compacted": True}

    first = step_entries[0]
    step_id = first.get("step_id", "unknown")
    step_index = first.get("step_index", 0)
    status = "completed"

    # Check all entries for status
    for entry in step_entries:
        if entry.get("status") == "in_progress":
            status = "in_progress"
        elif entry.get("status") == "failed" and status != "in_progress":
            status = "failed"

    # Collect all content and extract preservable lines
    all_content_parts: list[str] = []
    for entry in step_entries:
        content = entry.get("content", "")
        preserved = extract_preservable_content(content)
        if preserved:
            all_content_parts.append(preserved)

    combined = "\n".join(all_content_parts)

    # Truncate to token budget
    current_tokens = count_tokens(combined)
    if current_tokens > max_tokens and combined:
        # Simple truncation: take first N characters proportionally
        ratio = max_tokens / max(current_tokens, 1)
        char_limit = max(10, int(len(combined) * ratio))
        combined = combined[:char_limit].rstrip() + " [...]"

    # Collect metadata from all entries
    decisions: list[str] = []
    facts: list[str] = []
    entities: list[str] = []

    for entry in step_entries:
        meta = entry.get("metadata", {})
        if isinstance(meta, dict):
            if "decisions" in meta and isinstance(meta["decisions"], list):
                decisions.extend(meta["decisions"])
            if "facts" in meta and isinstance(meta["facts"], list):
                facts.extend(meta["facts"])
            if "entities" in meta and isinstance(meta["entities"], list):
                entities.extend(meta["entities"])

    return {
        "step_id": step_id,
        "step_index": step_index,
        "content": combined,
        "role": "summary",
        "status": status,
        "compacted": True,
        "original_entry_count": len(step_entries),
        "metadata": {
            "decisions": decisions,
            "facts": facts,
            "entities": entities,
        },
    }


# ---------------------------------------------------------------------------
# Compaction Stats
# ---------------------------------------------------------------------------


@dataclass
class SessionCompactionStats:
    """Tracks what happened during session compaction for observability."""

    total_entries: int = 0
    total_steps: int = 0
    steps_compacted: int = 0
    steps_preserved_recent: int = 0
    entries_before: int = 0
    entries_after: int = 0
    tokens_before: int = 0
    tokens_after: int = 0
    tokens_saved: int = 0
    trigger_fired: bool = False
    budget_usage_before: float = 0.0
    budget_usage_after: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_entries": self.total_entries,
            "total_steps": self.total_steps,
            "steps_compacted": self.steps_compacted,
            "steps_preserved_recent": self.steps_preserved_recent,
            "entries_before": self.entries_before,
            "entries_after": self.entries_after,
            "tokens_before": self.tokens_before,
            "tokens_after": self.tokens_after,
            "tokens_saved": self.tokens_saved,
            "trigger_fired": self.trigger_fired,
            "budget_usage_before": round(self.budget_usage_before, 4),
            "budget_usage_after": round(self.budget_usage_after, 4),
        }


# ---------------------------------------------------------------------------
# SessionCompactor
# ---------------------------------------------------------------------------


class SessionCompactor:
    """Orchestrator-level session context compactor.

    Operates on the full session history of an orchestrator run,
    compacting completed steps while preserving recent work and
    critical content (facts, decisions, entities).

    Distinct from ContextCompactor which operates on individual chunks
    within a single pipeline step.

    Args:
        token_budget: Maximum tokens allowed for the session context.
        trigger_pct: Fraction of budget at which compaction triggers
                     (default 0.80 = 80%).
        preserve_recent: Number of most recent steps to always keep
                         intact (never compacted).
        summary_max_tokens: Maximum tokens per step summary.
    """

    def __init__(
        self,
        token_budget: int = DEFAULT_TOKEN_BUDGET,
        trigger_pct: float = DEFAULT_TRIGGER_PCT,
        preserve_recent: int = DEFAULT_PRESERVE_RECENT,
        summary_max_tokens: int = DEFAULT_SUMMARY_MAX_TOKENS,
    ) -> None:
        self.token_budget = max(1, token_budget)
        self.trigger_pct = trigger_pct
        self.preserve_recent = max(0, preserve_recent)
        self.summary_max_tokens = summary_max_tokens

    # -------------------------------------------------------------------
    # Budget check
    # -------------------------------------------------------------------

    def should_compact(self, entries: list[dict[str, Any]]) -> bool:
        """Check whether session context exceeds the trigger threshold.

        Args:
            entries: Current session entries.

        Returns:
            True if accumulated tokens exceed ``trigger_pct`` of
            ``token_budget``.
        """
        total_tokens = self._count_total_tokens(entries)
        threshold = int(self.token_budget * self.trigger_pct)
        return total_tokens > threshold

    # -------------------------------------------------------------------
    # Main compact pipeline
    # -------------------------------------------------------------------

    def compact(
        self,
        entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Execute session compaction on the provided entries.

        Pipeline:
        1. Count total tokens and check trigger threshold.
        2. Group entries by step boundary.
        3. Identify recent steps (preserved intact) vs old steps.
        4. Summarize old completed steps.
        5. Reassemble the compacted entry list.

        Args:
            entries: List of session entry dicts ordered chronologically.

        Returns:
            Dict with::

                {
                    "entries": list[dict],        # Compacted entry list
                    "stats": SessionCompactionStats,
                    "compacted": bool,            # Whether compaction occurred
                    "trigger_fired": bool,        # Whether threshold was exceeded
                }
        """
        stats = SessionCompactionStats()
        stats.total_entries = len(entries)
        stats.entries_before = len(entries)

        if not entries:
            stats.entries_after = 0
            return {
                "entries": [],
                "stats": stats,
                "compacted": False,
                "trigger_fired": False,
            }

        # Count tokens before
        tokens_before = self._count_total_tokens(entries)
        stats.tokens_before = tokens_before
        stats.budget_usage_before = tokens_before / self.token_budget

        # Check trigger
        trigger_threshold = int(self.token_budget * self.trigger_pct)
        trigger_fired = tokens_before > trigger_threshold
        stats.trigger_fired = trigger_fired

        if not trigger_fired:
            # Below threshold -- return entries as-is
            stats.entries_after = len(entries)
            stats.tokens_after = tokens_before
            stats.budget_usage_after = stats.budget_usage_before
            logger.info(
                "Session compaction: below threshold (%.1f%% < %.1f%%), skipping",
                stats.budget_usage_before * 100,
                self.trigger_pct * 100,
            )
            return {
                "entries": list(entries),
                "stats": stats,
                "compacted": False,
                "trigger_fired": False,
            }

        logger.info(
            "Session compaction: TRIGGERED (%.1f%% > %.1f%%, %d tokens)",
            stats.budget_usage_before * 100,
            self.trigger_pct * 100,
            tokens_before,
        )

        # Group by step
        step_groups = group_by_step(entries)
        stats.total_steps = len(step_groups)

        # Split into old vs recent
        if len(step_groups) <= self.preserve_recent:
            # All steps are recent -- nothing to compact
            stats.steps_preserved_recent = len(step_groups)
            stats.entries_after = len(entries)
            stats.tokens_after = tokens_before
            stats.budget_usage_after = stats.budget_usage_before
            logger.info(
                "Session compaction: only %d steps (preserve_recent=%d), skipping",
                len(step_groups),
                self.preserve_recent,
            )
            return {
                "entries": list(entries),
                "stats": stats,
                "compacted": False,
                "trigger_fired": True,
            }

        old_groups = (
            step_groups[: -self.preserve_recent] if self.preserve_recent > 0 else step_groups
        )
        recent_groups = step_groups[-self.preserve_recent :] if self.preserve_recent > 0 else []

        stats.steps_preserved_recent = len(recent_groups)

        # Compact old steps
        compacted_entries: list[dict[str, Any]] = []
        steps_compacted = 0

        for group in old_groups:
            # Only compact completed steps -- keep in-progress intact
            group_status = self._determine_group_status(group)
            if group_status == "completed":
                summary = summarize_step(group, max_tokens=self.summary_max_tokens)
                compacted_entries.append(summary)
                steps_compacted += 1
            else:
                # Keep non-completed steps intact
                compacted_entries.extend(group)

        stats.steps_compacted = steps_compacted

        # Append recent steps intact
        for group in recent_groups:
            compacted_entries.extend(group)

        # Calculate tokens after
        tokens_after = self._count_total_tokens(compacted_entries)
        stats.entries_after = len(compacted_entries)
        stats.tokens_after = tokens_after
        stats.tokens_saved = tokens_before - tokens_after
        stats.budget_usage_after = tokens_after / self.token_budget

        logger.info(
            "Session compaction: %d steps compacted, %d tokens saved " "(%.1f%% -> %.1f%%)",
            steps_compacted,
            stats.tokens_saved,
            stats.budget_usage_before * 100,
            stats.budget_usage_after * 100,
        )

        return {
            "entries": compacted_entries,
            "stats": stats,
            "compacted": steps_compacted > 0,
            "trigger_fired": True,
        }

    # -------------------------------------------------------------------
    # Internals
    # -------------------------------------------------------------------

    def _count_total_tokens(self, entries: list[dict[str, Any]]) -> int:
        """Sum tokens across all entries."""
        total = 0
        for entry in entries:
            content = entry.get("content", "")
            if content:
                total += count_tokens(content)
        return total

    @staticmethod
    def _determine_group_status(group: list[dict[str, Any]]) -> str:
        """Determine the overall status of a step group.

        If any entry is in_progress, the group is in_progress.
        If all entries are completed (or no status), the group is completed.
        If any entry is failed and none in_progress, the group is failed.
        """
        has_in_progress = False
        has_failed = False

        for entry in group:
            status = entry.get("status", "completed")
            if status == "in_progress":
                has_in_progress = True
            elif status == "failed":
                has_failed = True

        if has_in_progress:
            return "in_progress"
        if has_failed:
            return "failed"
        return "completed"

    def __repr__(self) -> str:
        return (
            f"SessionCompactor("
            f"token_budget={self.token_budget}, "
            f"trigger_pct={self.trigger_pct}, "
            f"preserve_recent={self.preserve_recent})"
        )
