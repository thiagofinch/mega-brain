"""
worker_modes.py -- Worker Execution Modes for Agent Spawning
============================================================

Three distinct modes control how much context an agent inherits when
spawned by the pipeline coordinator:

- **FORK** -- inherits context + cache from the parent (research tasks).
- **SPAWN** -- starts with a clean slate (verification tasks).
- **RESUME** -- restores saved state and continues (correction tasks).

Architecture Decision
---------------------
The decision matrix maps task types to modes by default, but any step
can override its mode via the config cascade.  This gives the coordinator
a sensible autopilot while allowing per-step tuning.

Data Flow::

    config cascade    override?
         ↓               ↓
    task_type  →  DECISION_MATRIX  →  WorkerMode
         ↑               ↑
    context_overlap   override wins

Public API
----------
- ``WorkerMode``         -- enum with FORK, SPAWN, RESUME
- ``DECISION_MATRIX``    -- default task_type → WorkerMode mapping
- ``select_mode()``      -- resolve mode for a given task
- ``apply_mode()``       -- prepare agent context according to mode
- ``ModeConfig``         -- per-step mode configuration dataclass

Version: 1.0.0
Date: 2026-04-02
Epic: MCE-V22 / Story MCE22-1.3
"""

from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("mce.worker_modes")


# ---------------------------------------------------------------------------
# WorkerMode enum
# ---------------------------------------------------------------------------


class WorkerMode(str, Enum):
    """Execution modes for agent workers.

    Each mode defines a different context inheritance strategy:

    - ``FORK``:   Agent receives a deep copy of the parent's context and
                  cache.  Best for tasks that build on prior work (research,
                  analysis, extraction).

    - ``SPAWN``:  Agent starts with an empty context.  Best for tasks that
                  need a clean perspective (verification, validation, QA).

    - ``RESUME``: Agent restores previously saved state and continues from
                  where it left off.  Best for tasks that were interrupted
                  or need correction passes.
    """

    FORK = "fork"
    SPAWN = "spawn"
    RESUME = "resume"


# ---------------------------------------------------------------------------
# Decision Matrix -- default task_type → WorkerMode
# ---------------------------------------------------------------------------

#: Default mapping from task type keywords to worker modes.
#: The orchestrator consults this when no explicit override is set.
#:
#: Think of it like campaign segmentation:
#:   - research leads → warm audience (FORK, inherits context)
#:   - verification → cold audience (SPAWN, fresh perspective)
#:   - correction → retargeting (RESUME, picks up where left off)
DECISION_MATRIX: dict[str, WorkerMode] = {
    # Research / analysis tasks → inherit everything
    "research": WorkerMode.FORK,
    "analysis": WorkerMode.FORK,
    "extraction": WorkerMode.FORK,
    "ingest": WorkerMode.FORK,
    "batch": WorkerMode.FORK,
    "chunk": WorkerMode.FORK,
    "enrich": WorkerMode.FORK,
    # Verification / validation → clean slate
    "verification": WorkerMode.SPAWN,
    "validation": WorkerMode.SPAWN,
    "qa": WorkerMode.SPAWN,
    "audit": WorkerMode.SPAWN,
    "review": WorkerMode.SPAWN,
    # Correction / continuation → resume from state
    "correction": WorkerMode.RESUME,
    "fix": WorkerMode.RESUME,
    "retry": WorkerMode.RESUME,
    "continue": WorkerMode.RESUME,
    "revision": WorkerMode.RESUME,
}

#: Fallback mode when task type is not in the decision matrix and no
#: override is configured.  FORK is the safest default -- inheriting
#: context is better than losing it.
DEFAULT_MODE: WorkerMode = WorkerMode.FORK


# ---------------------------------------------------------------------------
# ModeConfig -- per-step configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModeConfig:
    """Per-step mode configuration.

    Allows a step in the DAG to override the default decision matrix
    and set explicit mode preferences.

    Attributes:
        mode_override: Explicit mode for this step.  If set, bypasses
                       the decision matrix entirely.
        context_keys:  For FORK mode, limit inherited context to these
                       keys only (empty = inherit all).
        state_key:     For RESUME mode, the key to look up saved state.
        clean_cache:   For SPAWN mode, whether to also clear the cache
                       (default True -- full clean slate).
    """

    mode_override: WorkerMode | None = None
    context_keys: tuple[str, ...] = ()
    state_key: str = ""
    clean_cache: bool = True


# ---------------------------------------------------------------------------
# select_mode() -- resolve mode for a task
# ---------------------------------------------------------------------------


def select_mode(
    task_type: str,
    *,
    context_overlap: float = 0.0,
    step_config: ModeConfig | None = None,
) -> WorkerMode:
    """Resolve the ``WorkerMode`` for a given task.

    Resolution order (highest precedence first):
        1. ``step_config.mode_override`` (config cascade per-step)
        2. ``DECISION_MATRIX`` lookup by ``task_type``
        3. Context overlap heuristic
        4. ``DEFAULT_MODE`` fallback

    Args:
        task_type:       Type/category of the task (e.g. ``"research"``).
                         Matched case-insensitively against DECISION_MATRIX.
        context_overlap: Float 0.0-1.0 indicating how much of the parent's
                         context is relevant to this task.  High overlap
                         (>0.7) favors FORK; low overlap (<0.3) favors SPAWN.
                         Only used when task_type is not in the matrix.
        step_config:     Optional per-step configuration.  If its
                         ``mode_override`` is set, it wins unconditionally.

    Returns:
        The resolved ``WorkerMode``.

    Raises:
        ValueError: If ``context_overlap`` is outside [0.0, 1.0].
    """
    if not (0.0 <= context_overlap <= 1.0):
        raise ValueError(f"context_overlap must be between 0.0 and 1.0, got {context_overlap}")

    # 1. Config override (highest precedence)
    if step_config is not None and step_config.mode_override is not None:
        logger.debug(
            "Mode override for task_type=%s: %s (from step_config)",
            task_type,
            step_config.mode_override.value,
        )
        return step_config.mode_override

    # 2. Decision matrix lookup
    normalized = task_type.strip().lower()
    if normalized in DECISION_MATRIX:
        mode = DECISION_MATRIX[normalized]
        logger.debug(
            "Mode from decision matrix for task_type=%s: %s",
            task_type,
            mode.value,
        )
        return mode

    # 3. Context overlap heuristic (when task_type not in matrix)
    if context_overlap >= 0.7:
        logger.debug(
            "Mode from context_overlap=%.2f for task_type=%s: FORK",
            context_overlap,
            task_type,
        )
        return WorkerMode.FORK
    if context_overlap <= 0.3:
        logger.debug(
            "Mode from context_overlap=%.2f for task_type=%s: SPAWN",
            context_overlap,
            task_type,
        )
        return WorkerMode.SPAWN

    # 4. Default fallback
    logger.debug(
        "Mode fallback for task_type=%s (overlap=%.2f): %s",
        task_type,
        context_overlap,
        DEFAULT_MODE.value,
    )
    return DEFAULT_MODE


# ---------------------------------------------------------------------------
# apply_mode() -- prepare agent context per mode
# ---------------------------------------------------------------------------


@dataclass
class ModeResult:
    """Result of applying a worker mode.

    Attributes:
        mode:           The mode that was applied.
        context:        The context dict the agent should start with.
        cache:          The cache dict the agent should start with.
        resumed_state:  For RESUME mode, the restored state (or None).
    """

    mode: WorkerMode
    context: dict[str, Any] = field(default_factory=dict)
    cache: dict[str, Any] = field(default_factory=dict)
    resumed_state: dict[str, Any] | None = None


def apply_mode(
    mode: WorkerMode,
    *,
    parent_context: dict[str, Any] | None = None,
    parent_cache: dict[str, Any] | None = None,
    saved_state: dict[str, Any] | None = None,
    step_config: ModeConfig | None = None,
) -> ModeResult:
    """Prepare the agent's starting context according to the worker mode.

    Args:
        mode:           The ``WorkerMode`` to apply.
        parent_context: Context dict from the parent agent (for FORK).
        parent_cache:   Cache dict from the parent agent (for FORK).
        saved_state:    Previously saved agent state (for RESUME).
        step_config:    Optional per-step config for fine-tuning.

    Returns:
        ``ModeResult`` with the prepared context, cache, and state.
    """
    parent_context = parent_context or {}
    parent_cache = parent_cache or {}
    config = step_config or ModeConfig()

    if mode == WorkerMode.FORK:
        # Deep copy to prevent mutation leaking back to parent.
        context = deepcopy(parent_context)
        cache = deepcopy(parent_cache)

        # If context_keys specified, filter to only those keys.
        if config.context_keys:
            allowed = set(config.context_keys)
            context = {k: v for k, v in context.items() if k in allowed}

        logger.debug(
            "FORK mode applied: %d context keys, %d cache keys",
            len(context),
            len(cache),
        )
        return ModeResult(mode=mode, context=context, cache=cache)

    if mode == WorkerMode.SPAWN:
        # Clean slate -- empty context and optionally empty cache.
        cache = {} if config.clean_cache else deepcopy(parent_cache)

        logger.debug(
            "SPAWN mode applied: clean context, cache %s",
            "cleared" if config.clean_cache else "preserved",
        )
        return ModeResult(mode=mode, context={}, cache=cache)

    if mode == WorkerMode.RESUME:
        # Restore from saved state.
        if saved_state is None:
            logger.warning(
                "RESUME mode requested but no saved_state provided -- "
                "falling back to FORK behavior"
            )
            return ModeResult(
                mode=mode,
                context=deepcopy(parent_context),
                cache=deepcopy(parent_cache),
            )

        state_copy = deepcopy(saved_state)
        context = state_copy.get("context", {})
        cache = state_copy.get("cache", {})

        logger.debug(
            "RESUME mode applied: restored %d context keys, %d cache keys",
            len(context),
            len(cache),
        )
        return ModeResult(
            mode=mode,
            context=context,
            cache=cache,
            resumed_state=state_copy,
        )

    # Should never reach here, but defensive.
    raise ValueError(f"Unknown WorkerMode: {mode}")
