"""
memory_selector.py -- Intelligent Memory Selection for MCE Pipeline
===================================================================

Selects the most relevant memories for a given query/task using the
side_query channel (lightweight Sonnet classifier). This keeps memory
selection costs off the main pipeline budget.

Architecture
------------
::

    memory_hierarchy.scan_index()          memory_selector
    ┌──────────────────────────┐         ┌──────────────────────────┐
    │ List[MemoryHeader]       │ ──────> │ select_relevant_memories │
    │ (name, type, desc, mtime)│         │  - filters already_surfaced
    │ (no content loaded)      │         │  - classifies via side_query
    └──────────────────────────┘         │  - applies relevance gate
                                         │  - returns top-k MemoryRef
                                         └──────────────────────────┘

The classifier prompt asks the model to score each memory header on
a 0-10 relevance scale. Only memories scoring above the gate threshold
(default: 7) are included. This implements the "only include if CERTAIN
it will be useful" gate from the story spec.

Public API
----------
- ``MemoryRef`` -- dataclass with path, description, mtime, score
- ``scan_memory_headers(directory) -> list[MemoryHeader]`` -- convenience wrapper
- ``select_relevant_memories(query, headers, max_k, ...) -> list[MemoryRef]``
- ``SurfacedTracker`` -- session-level exclusion tracker

Constraints
~~~~~~~~~~~
- stdlib + side_query only.
- Never reads topic content (only headers).
- Excludes already-surfaced memories within a session.
- Gate threshold is configurable (default 7/10).

Version: 1.0.0
Date: 2026-04-02
Story: MCE22-2.1
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engine.intelligence.pipeline.mce.memory_hierarchy import (
    MemoryHeader,
    scan_index,
)
from engine.intelligence.pipeline.mce.side_query import (
    SideQueryError,
    side_query_json,
)

logger = logging.getLogger("mce.memory_selector")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MAX_K = 5
DEFAULT_GATE_THRESHOLD = 7  # 0-10 scale; only >= 7 passes the gate
DEFAULT_MODEL = "sonnet"

# System prompt for the relevance classifier
_CLASSIFIER_SYSTEM_PROMPT = """\
You are a memory relevance classifier. Given a task query and a list of \
memory headers, score each memory on a 0-10 scale for relevance to the query.

Scoring guide:
- 0-3: Not relevant. The memory has no connection to the query.
- 4-6: Possibly relevant but uncertain. Do NOT include these.
- 7-8: Clearly relevant. The memory directly supports the task.
- 9-10: Essential. The memory is critical for completing the task.

IMPORTANT: Be conservative. Only score >= 7 if you are CERTAIN the memory \
will be useful. When in doubt, score lower. Budget is precious -- every \
memory included consumes context tokens.

Respond with a JSON object:
{
  "scores": [
    {"name": "<memory_name>", "score": <0-10>, "reason": "<brief reason>"},
    ...
  ]
}
"""


# ---------------------------------------------------------------------------
# Data Contracts
# ---------------------------------------------------------------------------


@dataclass
class MemoryRef:
    """Reference to a selected memory, with relevance score.

    This is the OUTPUT of the selection process. It tells the pipeline
    WHICH memories to load (via memory_hierarchy.load_topic) and WHY.

    Attributes:
        name: Memory topic identifier.
        path: Relative path to the topic file.
        description: Brief description of the memory content.
        mtime: Last modification timestamp (epoch float).
        score: Relevance score (0-10) from the classifier.
        reason: Brief explanation of why this memory was selected.
    """

    name: str
    path: str = ""
    description: str = ""
    mtime: float = 0.0
    score: float = 0.0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dict."""
        return {
            "name": self.name,
            "path": self.path,
            "description": self.description,
            "mtime": self.mtime,
            "score": self.score,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Surfaced Tracker (session-level deduplication)
# ---------------------------------------------------------------------------


class SurfacedTracker:
    """Tracks memories that have already been surfaced in the current session.

    Once a memory is surfaced (selected and loaded), it should not be
    re-selected in subsequent calls within the same session. This prevents
    wasting context budget on duplicate memories.

    Thread-safe via threading.Lock.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._surfaced: set[str] = set()

    def mark_surfaced(self, name: str) -> None:
        """Mark a memory as surfaced (already selected this session)."""
        with self._lock:
            self._surfaced.add(name)

    def mark_many_surfaced(self, names: list[str]) -> None:
        """Mark multiple memories as surfaced."""
        with self._lock:
            self._surfaced.update(names)

    def is_surfaced(self, name: str) -> bool:
        """Check if a memory has already been surfaced."""
        with self._lock:
            return name in self._surfaced

    def get_surfaced(self) -> set[str]:
        """Return a copy of all surfaced memory names."""
        with self._lock:
            return set(self._surfaced)

    def reset(self) -> None:
        """Reset the tracker (new session)."""
        with self._lock:
            self._surfaced.clear()

    @property
    def count(self) -> int:
        """Number of memories surfaced so far."""
        with self._lock:
            return len(self._surfaced)


# Module-level tracker instance (one per session/process)
_session_tracker = SurfacedTracker()


def get_session_tracker() -> SurfacedTracker:
    """Return the module-level session tracker."""
    return _session_tracker


def reset_session_tracker() -> None:
    """Reset the session tracker (call at session start)."""
    _session_tracker.reset()
    logger.debug("Memory session tracker reset")


# ---------------------------------------------------------------------------
# Header Scanning (convenience wrapper)
# ---------------------------------------------------------------------------


def scan_memory_headers(directory: str | Path) -> list[MemoryHeader]:
    """Scan a memory directory for headers (frontmatter only, no content).

    Convenience wrapper around ``memory_hierarchy.scan_index()``.

    Args:
        directory: Path to the directory containing MEMORY-INDEX.md.

    Returns:
        List of MemoryHeader objects (name, type, description, path, mtime).
    """
    return scan_index(directory)


# ---------------------------------------------------------------------------
# Relevance Classification via side_query
# ---------------------------------------------------------------------------


def _build_classifier_message(
    query: str,
    candidates: list[MemoryHeader],
) -> list[dict[str, str]]:
    """Build the user message for the relevance classifier.

    Args:
        query: The current task/query description.
        candidates: Memory headers to classify.

    Returns:
        Message list for side_query.
    """
    memory_list = []
    for h in candidates:
        memory_list.append(
            f"- name: {h.name}\n" f"  type: {h.type}\n" f"  description: {h.description}"
        )

    memories_text = "\n".join(memory_list)

    user_content = (
        f"## Current Task\n{query}\n\n"
        f"## Available Memories ({len(candidates)} entries)\n{memories_text}\n\n"
        f"Score each memory for relevance to the task (0-10)."
    )

    return [{"role": "user", "content": user_content}]


def _parse_classifier_response(
    response: dict[str, Any],
    candidates: list[MemoryHeader],
) -> dict[str, tuple[float, str]]:
    """Parse the classifier JSON response into a name -> (score, reason) map.

    Args:
        response: Parsed JSON from side_query_json.
        candidates: Original candidate list (for validation).

    Returns:
        Dict mapping memory name to (score, reason).
    """
    scores_map: dict[str, tuple[float, str]] = {}

    scores_list = response.get("scores", [])
    if not isinstance(scores_list, list):
        logger.warning("Classifier response 'scores' is not a list: %s", type(scores_list))
        return scores_map

    valid_names = {h.name for h in candidates}

    for entry in scores_list:
        if not isinstance(entry, dict):
            continue

        name = entry.get("name", "")
        if name not in valid_names:
            continue

        try:
            score = float(entry.get("score", 0))
        except (TypeError, ValueError):
            score = 0.0

        # Clamp to 0-10
        score = max(0.0, min(10.0, score))
        reason = str(entry.get("reason", ""))

        scores_map[name] = (score, reason)

    return scores_map


# ---------------------------------------------------------------------------
# Public API: select_relevant_memories
# ---------------------------------------------------------------------------


def select_relevant_memories(
    query: str,
    headers: list[MemoryHeader],
    *,
    max_k: int = DEFAULT_MAX_K,
    gate_threshold: float = DEFAULT_GATE_THRESHOLD,
    already_surfaced: set[str] | None = None,
    tracker: SurfacedTracker | None = None,
    model: str = DEFAULT_MODEL,
) -> list[MemoryRef]:
    """Select the most relevant memories for a query using side_query.

    This is the main entry point for memory selection. It:
    1. Filters out already-surfaced memories
    2. Sends candidate headers to side_query for relevance scoring
    3. Applies the gate threshold (only >= threshold pass)
    4. Returns top-k results sorted by score (descending)
    5. Marks selected memories as surfaced in the tracker

    Args:
        query: The current task/query description.
        headers: Memory headers from scan_memory_headers().
        max_k: Maximum memories to return. Default: 5.
        gate_threshold: Minimum score to pass the gate. Default: 7.
        already_surfaced: Set of memory names already surfaced (explicit).
                          If provided, these are ADDED to the tracker's set.
        tracker: SurfacedTracker instance. Default: module-level tracker.
        model: Model alias for side_query. Default: "sonnet".

    Returns:
        List of MemoryRef objects, sorted by score (highest first).
        Each contains path, description, mtime, score, reason.
        Returns empty list if no memories pass the gate.

    Raises:
        SideQueryError: If the side_query call fails (propagated).
    """
    if tracker is None:
        tracker = _session_tracker

    # Merge explicit already_surfaced into the tracker
    if already_surfaced:
        tracker.mark_many_surfaced(list(already_surfaced))

    # Step 1: Filter out already-surfaced memories
    candidates = [h for h in headers if not tracker.is_surfaced(h.name)]

    if not candidates:
        logger.info("No unsurfaced memory candidates available")
        return []

    if not query.strip():
        logger.warning("Empty query provided to select_relevant_memories")
        return []

    # Step 2: Classify via side_query
    messages = _build_classifier_message(query, candidates)

    try:
        response = side_query_json(
            system_prompt=_CLASSIFIER_SYSTEM_PROMPT,
            messages=messages,
            model=model,
            max_tokens=512,
            temperature=0.0,
        )
    except SideQueryError as exc:
        logger.error("Memory classification failed: %s", exc)
        raise

    # Step 3: Parse scores
    scores_map = _parse_classifier_response(response, candidates)

    # Step 4: Apply gate threshold
    passing: list[MemoryRef] = []
    for header in candidates:
        if header.name not in scores_map:
            continue

        score, reason = scores_map[header.name]
        if score < gate_threshold:
            logger.debug(
                "Memory '%s' below gate (%.1f < %.1f): %s",
                header.name,
                score,
                gate_threshold,
                reason,
            )
            continue

        ref = MemoryRef(
            name=header.name,
            path=header.path,
            description=header.description,
            mtime=header.mtime,
            score=score,
            reason=reason,
        )
        passing.append(ref)

    # Step 5: Sort by score (desc) and truncate to max_k
    passing.sort(key=lambda r: r.score, reverse=True)
    selected = passing[:max_k]

    # Step 6: Mark selected as surfaced
    selected_names = [r.name for r in selected]
    tracker.mark_many_surfaced(selected_names)

    logger.info(
        "Memory selection: %d candidates -> %d passed gate -> %d selected (max_k=%d)",
        len(candidates),
        len(passing),
        len(selected),
        max_k,
    )

    return selected
