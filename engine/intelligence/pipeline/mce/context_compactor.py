"""
context_compactor.py -- 4-Stage Context Compaction Pipeline + Circuit Breaker
==============================================================================

Intelligently reduces context window usage while preserving evidence
chains (source_id -> chunk_id -> claim).  Designed to sit between the
chunk collection phase and the LLM prompt assembly in the MCE pipeline.

4 Stages
--------
1. **COUNT**     -- Count tokens per chunk via token_counter.
2. **CHECK**     -- Compare total against configurable threshold.
3. **COMPACT**   -- Rank chunks by priority, summarize low-priority ones.
4. **MARK**      -- Tag compacted chunks with traceability metadata.

Circuit Breaker (Story MCE21-1.3)
---------------------------------
After N consecutive compaction failures (default 3), the circuit breaker
**opens** and compaction is skipped entirely until a successful compaction
resets the counter.  Two states only: CLOSED (normal) and OPEN (skip).
Half-open is explicitly out of scope.

When the breaker opens, the ``on_circuit_breaker_open`` hook is emitted
via HookBus with ``failure_count`` and ``last_error``.

Evidence chain invariant: ``source_id`` and ``chunk_id`` are NEVER removed
from any chunk, even after compaction.  This is the non-negotiable contract
that keeps the pipeline's traceability intact.

Usage::

    from engine.intelligence.pipeline.mce.context_compactor import ContextCompactor

    compactor = ContextCompactor()
    result = compactor.run(chunks, max_tokens=100_000)
    # result["chunks"]       -- compacted chunk list
    # result["stats"]        -- compaction statistics
    # result["compacted"]    -- True if any compaction occurred

Constraints:
    - stdlib + token_counter only (no LLM calls in Stage 3 -- heuristic for now).
    - Never mutates input chunks (returns new dicts).
    - Never drops source_id or chunk_id.

Version: 1.1.0
Date: 2026-04-01
Story: MCE21-1.3 (Circuit Breaker), MCE2-1.1 (original)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from engine.intelligence.pipeline.mce.token_counter import (
    count_tokens,
    count_tokens_for_chunks,
    estimate_context_usage,
)

logger = logging.getLogger("mce.context_compactor")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLD_PCT: float = 0.80  # 80% of context window
DEFAULT_MAX_TOKENS: int = 128_000
DEFAULT_SUMMARY_SENTENCES: int = 3  # Keep first N sentences for truncated chunks
DEFAULT_MAX_CONSECUTIVE_FAILURES: int = 3  # Circuit breaker threshold


# ---------------------------------------------------------------------------
# Circuit Breaker (Story MCE21-1.3)
# ---------------------------------------------------------------------------


class CircuitBreaker:
    """Two-state circuit breaker for compaction failures.

    States: CLOSED (normal operation) and OPEN (compaction skipped).
    Half-open is explicitly out of scope per story MCE21-1.3.

    After ``max_failures`` consecutive compaction failures, the breaker
    opens and compaction is bypassed.  A successful compaction resets
    the failure counter to zero.

    Args:
        max_failures: Consecutive failures before the breaker opens.
                      Configurable via config cascade key ``circuit_breaker_max``.
    """

    def __init__(self, max_failures: int = DEFAULT_MAX_CONSECUTIVE_FAILURES) -> None:
        self._max_failures = max(1, max_failures)
        self._consecutive_failures: int = 0
        self._is_open: bool = False
        self._last_error: str | None = None

    # -- Public API --------------------------------------------------------

    @property
    def is_open(self) -> bool:
        """True when the breaker is open (compaction should be skipped)."""
        return self._is_open

    @property
    def failure_count(self) -> int:
        """Number of consecutive failures recorded."""
        return self._consecutive_failures

    @property
    def max_failures(self) -> int:
        """Threshold after which the breaker opens."""
        return self._max_failures

    @property
    def last_error(self) -> str | None:
        """String representation of the last recorded failure."""
        return self._last_error

    def record_success(self) -> None:
        """Record a successful compaction -- resets failure counter."""
        self._consecutive_failures = 0
        # Note: breaker stays open once opened (no half-open).
        # Only an explicit reset() or a new ContextCompactor instance
        # will close it again.  This is intentional for safety.
        if not self._is_open:
            self._last_error = None

    def record_failure(self, error: Exception | str) -> bool:
        """Record a compaction failure.

        Args:
            error: The exception or error message from the failed compaction.

        Returns:
            True if this failure caused the breaker to OPEN (threshold reached).
        """
        self._consecutive_failures += 1
        self._last_error = str(error)
        logger.warning(
            "Circuit breaker: failure %d/%d -- %s",
            self._consecutive_failures,
            self._max_failures,
            self._last_error,
        )

        if self._consecutive_failures >= self._max_failures and not self._is_open:
            self._is_open = True
            logger.error(
                "Circuit breaker OPEN after %d consecutive failures",
                self._consecutive_failures,
            )
            return True  # Breaker just opened

        return False

    def reset(self) -> None:
        """Force-close the breaker and reset all counters.

        Use for testing or manual recovery.
        """
        self._consecutive_failures = 0
        self._is_open = False
        self._last_error = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize breaker state for observability."""
        return {
            "is_open": self._is_open,
            "consecutive_failures": self._consecutive_failures,
            "max_failures": self._max_failures,
            "last_error": self._last_error,
        }


# ---------------------------------------------------------------------------
# Compaction Stats
# ---------------------------------------------------------------------------


@dataclass
class CompactionStats:
    """Tracks what happened during compaction for observability."""

    stage_1_total_tokens: int = 0
    stage_1_chunk_count: int = 0
    stage_2_within_budget: bool = True
    stage_2_remaining_tokens: int = 0
    stage_2_action_needed: bool = False
    stage_3_chunks_compacted: int = 0
    stage_3_tokens_saved: int = 0
    stage_4_chunks_marked: int = 0
    compacted: bool = False
    circuit_breaker_skipped: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_1_total_tokens": self.stage_1_total_tokens,
            "stage_1_chunk_count": self.stage_1_chunk_count,
            "stage_2_within_budget": self.stage_2_within_budget,
            "stage_2_remaining_tokens": self.stage_2_remaining_tokens,
            "stage_2_action_needed": self.stage_2_action_needed,
            "stage_3_chunks_compacted": self.stage_3_chunks_compacted,
            "stage_3_tokens_saved": self.stage_3_tokens_saved,
            "stage_4_chunks_marked": self.stage_4_chunks_marked,
            "compacted": self.compacted,
            "circuit_breaker_skipped": self.circuit_breaker_skipped,
        }


# ---------------------------------------------------------------------------
# Priority Scorer
# ---------------------------------------------------------------------------


def _compute_chunk_priority(chunk: dict[str, Any]) -> float:
    """Score a chunk's priority for retention during compaction.

    Higher score = higher priority = keep in full.  Lower score = candidate
    for summarization/truncation.

    Scoring factors (additive):
        - entity_count:   more entities referenced = more valuable
        - insight_count:  more insights extracted = more valuable
        - relevance_score: explicit relevance (0.0-1.0) if present
        - has claims:     chunks with claims are critical evidence

    Args:
        chunk: A chunk dict with optional metadata fields.

    Returns:
        Priority score (float, unbounded, higher = more important).
    """
    score = 0.0

    # Entity count -- each entity mentioned adds priority
    entity_count = chunk.get("entity_count", 0)
    if isinstance(entity_count, (int, float)):
        score += entity_count * 2.0

    # Insight count -- insights are the pipeline's output
    insight_count = chunk.get("insight_count", 0)
    if isinstance(insight_count, (int, float)):
        score += insight_count * 3.0

    # Relevance score -- explicit ML/heuristic relevance
    relevance = chunk.get("relevance_score")
    if isinstance(relevance, (int, float)) and relevance is not None:
        score += relevance * 10.0

    # Claims -- if the chunk carries claims, it is evidence
    claims = chunk.get("claims", [])
    if isinstance(claims, list) and len(claims) > 0:
        score += len(claims) * 5.0

    # Confidence -- higher confidence chunks are more trustworthy
    confidence = chunk.get("confidence")
    if isinstance(confidence, (int, float)) and confidence is not None:
        score += confidence * 2.0

    return score


# ---------------------------------------------------------------------------
# Heuristic Summarizer (Stage 3)
# ---------------------------------------------------------------------------


def _truncate_to_sentences(text: str, max_sentences: int = DEFAULT_SUMMARY_SENTENCES) -> str:
    """Truncate text to the first N sentences.

    Simple sentence boundary detection: splits on `. `, `! `, `? `, or
    newlines followed by a capital letter.  Not perfect, but good enough
    for a heuristic summarizer that will be replaced by LLM summarization
    when MCE2-2.8 (LLM Provider) ships.

    Args:
        text: The text to truncate.
        max_sentences: Maximum number of sentences to keep.

    Returns:
        Truncated text (may be identical if fewer sentences exist).
    """
    if not text:
        return text

    # Split on sentence-ending punctuation followed by space
    sentences: list[str] = []
    current = ""
    for char in text:
        current += char
        if char in ".!?" and len(current.strip()) > 10:
            sentences.append(current.strip())
            current = ""
            if len(sentences) >= max_sentences:
                break

    # If we didn't find enough sentence boundaries, keep what we have
    if not sentences:
        # Fallback: just take first N characters roughly equivalent to N sentences
        cutoff = min(len(text), max_sentences * 100)
        return text[:cutoff].rstrip() + ("..." if len(text) > cutoff else "")

    result = " ".join(sentences)
    if len(sentences) >= max_sentences and len(text) > len(result):
        result += " [...]"
    return result


def _heuristic_summarize(chunk: dict[str, Any], text_key: str = "text") -> dict[str, Any]:
    """Summarize a chunk using heuristic truncation.

    Keeps the first N sentences + all metadata (chunk_id, source_id, etc).
    The ``text`` field is replaced with the truncated version.

    .. note::
        TODO(MCE2-2.8): Replace this heuristic with LLM-based summarization
        once the LLM Provider abstraction is available.  The LLM summarizer
        should produce a semantic summary rather than simple truncation,
        preserving key entities and claims mentioned in the original text.

    Args:
        chunk: The chunk dict to summarize.
        text_key: Key holding the text content.

    Returns:
        New chunk dict with truncated text.
    """
    summarized = dict(chunk)  # shallow copy -- never mutate input
    original_text = chunk.get(text_key, "")
    summarized[text_key] = _truncate_to_sentences(original_text)
    return summarized


# ---------------------------------------------------------------------------
# ContextCompactor
# ---------------------------------------------------------------------------


class ContextCompactor:
    """4-stage context compaction pipeline with circuit breaker.

    Reduces total token usage while preserving evidence chains.
    Each stage is independently callable, but :meth:`run` chains all 4.

    The circuit breaker (Story MCE21-1.3) stops compaction attempts after
    N consecutive failures, emitting ``on_circuit_breaker_open`` via
    HookBus.  A successful compaction resets the failure counter.

    Args:
        model: Model identifier for token counting.
        text_key: Key in chunk dicts that holds text content.
        threshold_pct: Budget threshold (0.0-1.0). Compaction triggers
                       when usage exceeds this fraction of max_tokens.
        summary_sentences: Sentences to keep when truncating low-priority chunks.
        max_compact_failures: Consecutive failures before circuit breaker opens.
                              Default 3.  Configurable via config cascade key
                              ``circuit_breaker_max``.
        hook_bus: Optional HookBus for emitting ``on_circuit_breaker_open``.
                  If None, the hook is silently skipped.
    """

    def __init__(
        self,
        model: str = "gemini-1.5-pro",
        text_key: str = "text",
        threshold_pct: float = DEFAULT_THRESHOLD_PCT,
        summary_sentences: int = DEFAULT_SUMMARY_SENTENCES,
        max_compact_failures: int = DEFAULT_MAX_CONSECUTIVE_FAILURES,
        hook_bus: object | None = None,
    ) -> None:
        self.model = model
        self.text_key = text_key
        self.threshold_pct = threshold_pct
        self.summary_sentences = summary_sentences
        self.circuit_breaker = CircuitBreaker(max_failures=max_compact_failures)
        self._hook_bus = hook_bus

    # -------------------------------------------------------------------
    # Stage 1: COUNT
    # -------------------------------------------------------------------

    def count(
        self,
        chunks: list[dict[str, Any]],
        model: str | None = None,
    ) -> list[dict[str, Any]]:
        """Stage 1: Count tokens per chunk.

        Returns annotated chunk copies with ``_token_count`` field added.
        Original chunks are not mutated.

        Args:
            chunks: List of chunk dicts.
            model: Override model (uses instance default if None).

        Returns:
            List of chunk dicts with ``_token_count`` added.
        """
        m = model or self.model
        return count_tokens_for_chunks(chunks, model=m, text_key=self.text_key)

    # -------------------------------------------------------------------
    # Stage 2: CHECK THRESHOLD
    # -------------------------------------------------------------------

    def check_threshold(
        self,
        total_tokens: int,
        max_tokens: int,
        threshold_pct: float | None = None,
    ) -> dict[str, Any]:
        """Stage 2: Check whether total tokens exceed the threshold.

        Args:
            total_tokens: Total token count from Stage 1.
            max_tokens: Maximum tokens allowed (context window budget).
            threshold_pct: Override threshold (uses instance default if None).

        Returns:
            Dict with::

                {
                    "within_budget": bool,
                    "remaining": int,        # tokens remaining before threshold
                    "threshold_tokens": int,  # absolute threshold in tokens
                    "action_needed": bool,    # True if compaction should run
                    "overage": int,           # tokens over threshold (0 if within)
                }
        """
        pct = threshold_pct if threshold_pct is not None else self.threshold_pct
        threshold_tokens = int(max_tokens * pct)
        remaining = threshold_tokens - total_tokens
        within_budget = total_tokens <= threshold_tokens

        return {
            "within_budget": within_budget,
            "remaining": max(0, remaining),
            "threshold_tokens": threshold_tokens,
            "action_needed": not within_budget,
            "overage": max(0, total_tokens - threshold_tokens),
        }

    # -------------------------------------------------------------------
    # Stage 3: COMPACT
    # -------------------------------------------------------------------

    def compact(
        self,
        chunks: list[dict[str, Any]],
        max_tokens: int,
        threshold_pct: float | None = None,
    ) -> list[dict[str, Any]]:
        """Stage 3: Compact chunks by summarizing low-priority ones.

        Ranks chunks by priority (entity count, insight count, relevance,
        claims).  High-priority chunks are kept in full; low-priority chunks
        are truncated to first N sentences.  Compaction continues until the
        total token count fits within the threshold.

        INVARIANT: ``chunk_id`` and ``source_id`` are NEVER removed.

        Args:
            chunks: List of chunk dicts (should have ``_token_count`` from Stage 1).
            max_tokens: Maximum tokens allowed.
            threshold_pct: Override threshold.

        Returns:
            List of chunk dicts (some may be summarized).
        """
        pct = threshold_pct if threshold_pct is not None else self.threshold_pct
        token_budget = int(max_tokens * pct)

        # Sort by priority: lowest priority first (candidates for compaction)
        scored = [(i, _compute_chunk_priority(c), c) for i, c in enumerate(chunks)]
        scored.sort(key=lambda x: x[1])  # ascending -- lowest priority first

        # Calculate current total
        current_total = sum(c.get("_token_count", 0) for c in chunks)

        if current_total <= token_budget:
            # Already within budget -- return as-is
            return [dict(c) for c in chunks]

        # Compact from lowest priority upward until within budget
        compacted_indices: set[int] = set()
        result_chunks = [dict(c) for c in chunks]  # shallow copies

        for idx, _priority, chunk in scored:
            if current_total <= token_budget:
                break

            original_tokens = chunk.get("_token_count", 0)
            if original_tokens <= 0:
                continue

            # Summarize this chunk
            summarized = _heuristic_summarize(chunk, text_key=self.text_key)
            new_tokens = count_tokens(summarized.get(self.text_key, ""), model=self.model)

            tokens_saved = original_tokens - new_tokens
            if tokens_saved <= 0:
                continue  # Summarization didn't help

            summarized["_token_count"] = new_tokens
            result_chunks[idx] = summarized
            compacted_indices.add(idx)
            current_total -= tokens_saved

            logger.debug(
                "Compacted chunk[%d] (priority=%.1f): %d -> %d tokens (saved %d)",
                idx,
                _priority,
                original_tokens,
                new_tokens,
                tokens_saved,
            )

        return result_chunks

    # -------------------------------------------------------------------
    # Stage 4: MARK SNIP BOUNDARY
    # -------------------------------------------------------------------

    def mark_snip_boundary(
        self,
        original_chunks: list[dict[str, Any]],
        compacted_chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Stage 4: Mark compacted chunks with traceability metadata.

        Compares original vs compacted chunks and adds:
        - ``_compacted``: True if this chunk was modified during compaction.
        - ``_original_token_count``: Token count before compaction.

        INVARIANT: ``chunk_id`` and ``source_id`` are preserved (verified).

        Args:
            original_chunks: Chunks as they were before compaction (with _token_count).
            compacted_chunks: Chunks after Stage 3 compaction.

        Returns:
            List of chunk dicts with traceability fields added.

        Raises:
            ValueError: If a compacted chunk is missing chunk_id or source_id
                        that was present in the original (evidence chain broken).
        """
        if len(original_chunks) != len(compacted_chunks):
            raise ValueError(
                f"Chunk count mismatch: original={len(original_chunks)}, "
                f"compacted={len(compacted_chunks)}.  "
                "Compaction must not add or remove chunks."
            )

        result = []
        for orig, comp in zip(original_chunks, compacted_chunks):
            marked = dict(comp)  # shallow copy

            orig_text = orig.get(self.text_key, "")
            comp_text = comp.get(self.text_key, "")
            was_compacted = orig_text != comp_text

            marked["_compacted"] = was_compacted
            marked["_original_token_count"] = orig.get("_token_count", 0)

            # Evidence chain verification: chunk_id and source_id must survive
            orig_chunk_id = orig.get("chunk_id")
            comp_chunk_id = marked.get("chunk_id")
            if orig_chunk_id is not None and comp_chunk_id != orig_chunk_id:
                raise ValueError(
                    f"Evidence chain BROKEN: chunk_id changed from "
                    f"'{orig_chunk_id}' to '{comp_chunk_id}'"
                )

            orig_source_id = orig.get("source_id")
            comp_source_id = marked.get("source_id")
            if orig_source_id is not None and comp_source_id != orig_source_id:
                raise ValueError(
                    f"Evidence chain BROKEN: source_id changed from "
                    f"'{orig_source_id}' to '{comp_source_id}'"
                )

            result.append(marked)

        return result

    # -------------------------------------------------------------------
    # Full Pipeline: run() chains all 4 stages
    # -------------------------------------------------------------------

    def run(
        self,
        chunks: list[dict[str, Any]],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        prompt_template: str = "",
    ) -> dict[str, Any]:
        """Execute the full 4-stage compaction pipeline.

        Chains: count -> check -> compact (if needed) -> mark.

        Args:
            chunks: List of chunk dicts with text content.
            max_tokens: Maximum tokens allowed for the context window.
            prompt_template: Prompt text that accompanies the chunks
                             (counted toward the budget).

        Returns:
            Dict with::

                {
                    "chunks": list[dict],     # Final chunk list
                    "stats": CompactionStats,  # What happened
                    "compacted": bool,         # Whether any compaction occurred
                    "usage": dict,             # Context usage report
                }
        """
        stats = CompactionStats()

        # --- Stage 1: COUNT ---
        counted = self.count(chunks)
        total_chunk_tokens = sum(c.get("_token_count", 0) for c in counted)
        prompt_tokens = count_tokens(prompt_template, model=self.model)
        total_tokens = total_chunk_tokens + prompt_tokens

        stats.stage_1_total_tokens = total_tokens
        stats.stage_1_chunk_count = len(counted)

        logger.info(
            "Stage 1 COUNT: %d chunks, %d tokens (prompt=%d, chunks=%d)",
            len(counted),
            total_tokens,
            prompt_tokens,
            total_chunk_tokens,
        )

        # --- Stage 2: CHECK ---
        check = self.check_threshold(total_tokens, max_tokens)
        stats.stage_2_within_budget = check["within_budget"]
        stats.stage_2_remaining_tokens = check["remaining"]
        stats.stage_2_action_needed = check["action_needed"]

        logger.info(
            "Stage 2 CHECK: within_budget=%s, remaining=%d, action_needed=%s",
            check["within_budget"],
            check["remaining"],
            check["action_needed"],
        )

        # --- Stage 3: COMPACT (only if needed + circuit breaker gate) ---
        if check["action_needed"]:
            if self.circuit_breaker.is_open:
                # Circuit breaker is OPEN -- skip compaction entirely
                compacted = [dict(c) for c in counted]
                stats.circuit_breaker_skipped = True
                logger.warning(
                    "Stage 3 COMPACT: SKIPPED (circuit breaker OPEN, %d consecutive failures)",
                    self.circuit_breaker.failure_count,
                )
            else:
                try:
                    compacted = self.compact(counted, max_tokens)

                    # Count how many were actually compacted
                    compacted_count = 0
                    tokens_saved = 0
                    for orig, comp in zip(counted, compacted):
                        if orig.get(self.text_key, "") != comp.get(self.text_key, ""):
                            compacted_count += 1
                            tokens_saved += orig.get("_token_count", 0) - comp.get(
                                "_token_count", 0
                            )

                    stats.stage_3_chunks_compacted = compacted_count
                    stats.stage_3_tokens_saved = tokens_saved
                    stats.compacted = compacted_count > 0

                    # Record success -- resets failure counter (AC3)
                    self.circuit_breaker.record_success()

                    logger.info(
                        "Stage 3 COMPACT: %d chunks compacted, %d tokens saved",
                        compacted_count,
                        tokens_saved,
                    )
                except Exception as exc:
                    # Record failure and check if breaker should open (AC1, AC2)
                    just_opened = self.circuit_breaker.record_failure(exc)

                    if just_opened:
                        self._emit_circuit_breaker_open()

                    # Graceful degradation: return uncompacted chunks
                    compacted = [dict(c) for c in counted]

                    logger.error(
                        "Stage 3 COMPACT: FAILED (%s), returning uncompacted chunks "
                        "(failures: %d/%d)",
                        exc,
                        self.circuit_breaker.failure_count,
                        self.circuit_breaker.max_failures,
                    )
        else:
            compacted = [dict(c) for c in counted]
            logger.info("Stage 3 COMPACT: skipped (within budget)")

        # --- Stage 4: MARK ---
        marked = self.mark_snip_boundary(counted, compacted)
        marked_count = sum(1 for c in marked if c.get("_compacted", False))
        stats.stage_4_chunks_marked = marked_count

        logger.info("Stage 4 MARK: %d chunks marked as compacted", marked_count)

        # --- Usage report (post-compaction) ---
        usage = estimate_context_usage(
            marked,
            prompt_template=prompt_template,
            model=self.model,
            text_key=self.text_key,
        )

        return {
            "chunks": marked,
            "stats": stats,
            "compacted": stats.compacted,
            "usage": usage,
            "circuit_breaker": self.circuit_breaker.to_dict(),
        }

    # -------------------------------------------------------------------
    # Turn-Aware Compaction (Story MCE21-2.1)
    # -------------------------------------------------------------------

    def run_by_turn(
        self,
        turn_groups: list,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        prompt_template: str = "",
        preserve_last_n: int = 2,
    ) -> dict[str, Any]:
        """Execute turn-aware compaction pipeline.

        Instead of compacting individual chunks, this method treats
        each TurnGroup as an atomic unit.  A turn is either kept in
        its entirety or dropped entirely -- it is NEVER split or
        partially truncated.

        This method delegates to ``message_grouping.compact_by_turn``
        for the actual turn-level compaction, then runs the standard
        4-stage pipeline on the surviving chunks (within each turn).

        .. note::
            Import is deferred to avoid circular imports since
            message_grouping imports from token_counter, and this
            module also imports from token_counter.

        Args:
            turn_groups: List of TurnGroup instances from
                         ``message_grouping.group_by_turn()``.
            max_tokens: Maximum tokens allowed for the context window.
            prompt_template: Prompt text counted toward the budget.
            preserve_last_n: Number of most recent turns that are
                             never dropped (default 2).

        Returns:
            Dict with::

                {
                    "turn_groups": list[TurnGroup],  # Surviving turns
                    "dropped_turns": list[TurnGroup], # Removed turns
                    "stats": dict,                    # Compaction statistics
                    "compacted": bool,                # Whether any turns were dropped
                    "circuit_breaker": dict,          # Breaker state
                }

        Story: MCE21-2.1
        """
        # Deferred import to avoid circular dependency
        from engine.intelligence.pipeline.mce.message_grouping import compact_by_turn

        prompt_tokens = count_tokens(prompt_template, model=self.model)
        adjusted_max = max(1, max_tokens - prompt_tokens)

        result = compact_by_turn(
            turn_groups,
            max_tokens=adjusted_max,
            threshold_pct=self.threshold_pct,
            model=self.model,
            preserve_last_n=preserve_last_n,
        )

        # Enrich result with circuit breaker state for observability
        result["circuit_breaker"] = self.circuit_breaker.to_dict()

        logger.info(
            "Turn-aware compaction: %d/%d turns survived, %d tokens freed",
            result["stats"]["surviving_turns"],
            result["stats"]["total_turns"],
            result["stats"]["tokens_freed"],
        )

        return result

    # -------------------------------------------------------------------
    # Circuit Breaker Hook Emission (Story MCE21-1.3)
    # -------------------------------------------------------------------

    def _emit_circuit_breaker_open(self) -> None:
        """Emit the on_circuit_breaker_open hook when breaker transitions to OPEN.

        Fire-and-forget -- hook failure never blocks the pipeline.
        The hook_bus is duck-typed: any object with an ``emit(event, payload)``
        method works (HookBus, mock, or custom).
        """
        if self._hook_bus is None:
            logger.debug("No HookBus configured -- skipping on_circuit_breaker_open emission")
            return

        payload = {
            "event": "on_circuit_breaker_open",
            "failure_count": self.circuit_breaker.failure_count,
            "max_failures": self.circuit_breaker.max_failures,
            "last_error": self.circuit_breaker.last_error,
        }

        try:
            self._hook_bus.emit("on_circuit_breaker_open", payload)
            logger.info("Emitted on_circuit_breaker_open hook: %s", payload)
        except Exception as exc:
            # Fire-and-forget: hook failure never blocks compaction pipeline
            logger.error("Failed to emit on_circuit_breaker_open: %s", exc)
