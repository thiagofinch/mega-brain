"""
message_grouping.py -- Message Grouping by API Turn
=====================================================

Groups a flat list of messages into TurnGroups, where each turn
represents one complete API round (request + response).  TurnGroups
are the atomic unit that the compaction pipeline operates on --
a turn is NEVER split mid-compaction.

Turn Detection
--------------
A new turn boundary is detected when:
1. The ``step_id`` field changes between consecutive messages.
2. If ``step_id`` is absent, a role transition from non-user to
   ``user`` signals a new turn (the user is starting a new request).
3. If neither signal is present, all messages form a single turn.

Integration with context_compactor
----------------------------------
``compact_by_turn`` wraps the ContextCompactor so that compaction
decisions are made at the turn level.  When a turn must be removed
to fit the budget, the entire turn is dropped -- never partially
truncated.  This preserves conversational coherence.

Usage::

    from engine.intelligence.pipeline.mce.message_grouping import (
        TurnGroup,
        group_by_turn,
        compact_by_turn,
    )

    groups = group_by_turn(messages)
    result = compact_by_turn(groups, max_tokens=100_000)

Constraints:
    - stdlib + token_counter only (no LLM calls).
    - Never mutates input messages (returns new structures).
    - Turn integrity is the non-negotiable invariant.

Version: 1.0.0
Date: 2026-04-01
Story: MCE21-2.1
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from engine.intelligence.pipeline.mce.token_counter import count_tokens

logger = logging.getLogger("mce.message_grouping")


# ---------------------------------------------------------------------------
# TurnGroup Dataclass
# ---------------------------------------------------------------------------


@dataclass
class TurnGroup:
    """A group of messages belonging to a single API turn.

    A turn is the atomic unit of compaction -- it is NEVER split.
    Each turn has a unique ``turn_id`` (sequential), the messages
    that belong to it, a precomputed ``token_count``, and the
    ``step_id`` that triggered the boundary (if available).

    Attributes:
        turn_id: Sequential identifier for this turn (0-based).
        messages: List of message dicts belonging to this turn.
        token_count: Total token count across all messages in this turn.
        step_id: The step_id that defines this turn's boundary.
                 None if grouping was done by role transition.
    """

    turn_id: int = 0
    messages: list[dict[str, Any]] = field(default_factory=list)
    token_count: int = 0
    step_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for observability and logging."""
        return {
            "turn_id": self.turn_id,
            "message_count": len(self.messages),
            "token_count": self.token_count,
            "step_id": self.step_id,
        }


# ---------------------------------------------------------------------------
# Turn Boundary Detection
# ---------------------------------------------------------------------------


def _detect_boundary_by_step_id(messages: list[dict[str, Any]]) -> bool:
    """Check if messages have usable step_id fields for boundary detection.

    Returns True if at least 2 distinct step_id values exist, meaning
    step_id is a viable grouping key.
    """
    step_ids = {m.get("step_id") for m in messages if m.get("step_id") is not None}
    return len(step_ids) >= 2


def _detect_boundary_by_role(messages: list[dict[str, Any]]) -> bool:
    """Check if messages have role fields for boundary detection.

    Returns True if at least one message has a ``role`` field.
    """
    return any(m.get("role") is not None for m in messages)


# ---------------------------------------------------------------------------
# group_by_turn -- Core Grouping Function
# ---------------------------------------------------------------------------


def group_by_turn(
    messages: list[dict[str, Any]],
    model: str = "gemini-1.5-pro",
    text_key: str = "text",
) -> list[TurnGroup]:
    """Group messages by API turn (request/response round).

    Turn boundaries are detected using two strategies, in priority order:

    1. **step_id boundary**: If messages carry ``step_id``, a new turn
       starts whenever step_id changes.
    2. **Role transition**: If step_id is absent, a new turn starts
       when the role transitions from a non-``user`` role back to
       ``user`` (indicating the user is starting a new request).
    3. **Fallback**: If neither signal exists, all messages form one turn.

    Token counts are computed per turn using the token_counter module,
    so the compactor can make budget decisions at the turn level.

    Args:
        messages: Flat list of message dicts.  Expected keys vary by
                  detection strategy but typically include ``role``,
                  ``step_id``, and a text content key.
        model: Model identifier for token counting.
        text_key: Key in message dicts holding text content.
                  Also checks ``content`` as fallback.

    Returns:
        List of TurnGroup instances, ordered by turn_id (0-based).
        Empty input returns empty list.
    """
    if not messages:
        return []

    # Pick the boundary detection strategy
    use_step_id = _detect_boundary_by_step_id(messages)
    use_role = not use_step_id and _detect_boundary_by_role(messages)

    if use_step_id:
        groups = _group_by_step_id(messages)
        logger.info("Grouped %d messages into %d turns via step_id", len(messages), len(groups))
    elif use_role:
        groups = _group_by_role(messages)
        logger.info(
            "Grouped %d messages into %d turns via role transition", len(messages), len(groups)
        )
    else:
        # Fallback: everything is one turn
        groups = [messages]
        logger.info("No boundary signals found -- all %d messages in 1 turn", len(messages))

    # Build TurnGroup instances with token counts
    turn_groups: list[TurnGroup] = []
    for idx, group_msgs in enumerate(groups):
        token_count = _count_group_tokens(group_msgs, model=model, text_key=text_key)
        step_id = group_msgs[0].get("step_id") if group_msgs else None

        turn_groups.append(
            TurnGroup(
                turn_id=idx,
                messages=list(group_msgs),  # defensive copy
                token_count=token_count,
                step_id=step_id,
            )
        )

    return turn_groups


# ---------------------------------------------------------------------------
# Grouping Strategies
# ---------------------------------------------------------------------------


def _group_by_step_id(messages: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group messages by step_id field.

    Each unique step_id value defines a turn.  Messages with the same
    step_id are kept together in their original order.  Messages without
    a step_id are attached to the preceding turn (or the first turn if
    they appear at the start).
    """
    groups: list[list[dict[str, Any]]] = []
    current_step_id: str | None = None
    current_group: list[dict[str, Any]] = []

    for msg in messages:
        msg_step_id = msg.get("step_id")

        if msg_step_id is not None and msg_step_id != current_step_id:
            # New turn boundary
            if current_group:
                groups.append(current_group)
            current_group = [msg]
            current_step_id = msg_step_id
        else:
            # Same turn (or no step_id -- attach to current)
            current_group.append(msg)

    # Flush last group
    if current_group:
        groups.append(current_group)

    return groups


def _group_by_role(messages: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group messages by role transition.

    A new turn starts when a ``user`` role message appears after a
    non-``user`` message.  This models the API round-trip pattern:
    user sends request, assistant responds, user sends next request.
    """
    groups: list[list[dict[str, Any]]] = []
    current_group: list[dict[str, Any]] = []
    prev_role: str | None = None

    for msg in messages:
        role = msg.get("role", "unknown")

        # New turn: user message after non-user message
        if role == "user" and prev_role is not None and prev_role != "user":
            if current_group:
                groups.append(current_group)
            current_group = [msg]
        else:
            current_group.append(msg)

        prev_role = role

    # Flush last group
    if current_group:
        groups.append(current_group)

    return groups


# ---------------------------------------------------------------------------
# Token Counting per Turn
# ---------------------------------------------------------------------------


def _count_group_tokens(
    messages: list[dict[str, Any]],
    model: str = "gemini-1.5-pro",
    text_key: str = "text",
) -> int:
    """Count total tokens across all messages in a turn group.

    Checks both ``text_key`` and ``content`` as fallback keys for
    message text, since different parts of the pipeline may use
    different key names.

    Args:
        messages: Messages in this turn group.
        model: Model identifier for token counting.
        text_key: Primary key for text content.

    Returns:
        Total token count (sum of all message tokens).
    """
    total = 0
    for msg in messages:
        text = msg.get(text_key) or msg.get("content") or ""
        total += count_tokens(str(text), model=model)
    return total


# ---------------------------------------------------------------------------
# compact_by_turn -- Turn-Aware Compaction
# ---------------------------------------------------------------------------


def compact_by_turn(
    turn_groups: list[TurnGroup],
    max_tokens: int = 128_000,
    threshold_pct: float = 0.80,
    model: str = "gemini-1.5-pro",
    preserve_last_n: int = 2,
) -> dict[str, Any]:
    """Compact turns to fit within a token budget.

    Unlike chunk-level compaction, turn compaction operates on whole
    turns as atomic units.  A turn is either kept entirely or dropped
    entirely -- it is NEVER split or partially truncated.

    The algorithm:
    1. Calculate total tokens across all turns.
    2. If within budget, return all turns unchanged.
    3. If over budget, drop lowest-priority turns (oldest first,
       excluding the last N turns which are always preserved).
    4. Continue dropping until within budget or only preserved turns remain.

    Priority heuristic: recent turns are more relevant than older ones.
    The last ``preserve_last_n`` turns are NEVER dropped (they contain
    the most recent context the user is working with).

    Args:
        turn_groups: List of TurnGroup from group_by_turn().
        max_tokens: Maximum token budget for the context window.
        threshold_pct: Budget threshold (0.0-1.0).  Compaction triggers
                       when usage exceeds this fraction of max_tokens.
        model: Model identifier (reserved for future use).
        preserve_last_n: Number of most recent turns that are never dropped.
                         Default 2 (current turn + previous for context).

    Returns:
        Dict with::

            {
                "turn_groups": list[TurnGroup],  # Surviving turns
                "dropped_turns": list[TurnGroup], # Turns that were removed
                "stats": {
                    "total_turns": int,
                    "surviving_turns": int,
                    "dropped_turns": int,
                    "original_tokens": int,
                    "final_tokens": int,
                    "tokens_freed": int,
                    "compacted": bool,
                },
            }
    """
    if not turn_groups:
        return {
            "turn_groups": [],
            "dropped_turns": [],
            "stats": {
                "total_turns": 0,
                "surviving_turns": 0,
                "dropped_turns": 0,
                "original_tokens": 0,
                "final_tokens": 0,
                "tokens_freed": 0,
                "compacted": False,
            },
        }

    token_budget = int(max_tokens * threshold_pct)
    total_tokens = sum(tg.token_count for tg in turn_groups)

    if total_tokens <= token_budget:
        logger.info(
            "Turn compaction: within budget (%d <= %d), no action needed",
            total_tokens,
            token_budget,
        )
        return {
            "turn_groups": list(turn_groups),
            "dropped_turns": [],
            "stats": {
                "total_turns": len(turn_groups),
                "surviving_turns": len(turn_groups),
                "dropped_turns": 0,
                "original_tokens": total_tokens,
                "final_tokens": total_tokens,
                "tokens_freed": 0,
                "compacted": False,
            },
        }

    # Split into droppable (older) and preserved (recent) turns
    preserve_count = min(preserve_last_n, len(turn_groups))
    droppable = list(turn_groups[:-preserve_count]) if preserve_count < len(turn_groups) else []
    preserved = list(turn_groups[-preserve_count:])

    # Drop from oldest first (lowest turn_id = least recent)
    dropped: list[TurnGroup] = []
    current_tokens = total_tokens

    for turn in droppable:
        if current_tokens <= token_budget:
            break
        dropped.append(turn)
        current_tokens -= turn.token_count
        logger.debug(
            "Dropped turn %d (step_id=%s, %d tokens) -- budget: %d/%d",
            turn.turn_id,
            turn.step_id,
            turn.token_count,
            current_tokens,
            token_budget,
        )

    # Build surviving turns list (droppable that survived + preserved)
    dropped_ids = {t.turn_id for t in dropped}
    surviving = [t for t in droppable if t.turn_id not in dropped_ids] + preserved

    # Re-index surviving turns for clean sequential IDs
    for new_idx, turn in enumerate(surviving):
        turn.turn_id = new_idx

    final_tokens = sum(tg.token_count for tg in surviving)
    tokens_freed = total_tokens - final_tokens

    logger.info(
        "Turn compaction: dropped %d/%d turns, freed %d tokens (%d -> %d)",
        len(dropped),
        len(turn_groups),
        tokens_freed,
        total_tokens,
        final_tokens,
    )

    return {
        "turn_groups": surviving,
        "dropped_turns": dropped,
        "stats": {
            "total_turns": len(turn_groups),
            "surviving_turns": len(surviving),
            "dropped_turns": len(dropped),
            "original_tokens": total_tokens,
            "final_tokens": final_tokens,
            "tokens_freed": tokens_freed,
            "compacted": len(dropped) > 0,
        },
    }
