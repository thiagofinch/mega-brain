"""
teammate_context.py -- Isolated Agent Context via contextvars
=============================================================

Provides per-agent context isolation using Python's ``contextvars`` module,
which is the equivalent of Node.js ``AsyncLocalStorage``.  Each async task
or thread gets its own copy of the context variable automatically -- no
locks, no leaking between parallel agents.

Usage::

    from engine.intelligence.pipeline.mce.teammate_context import (
        TeammateContext,
        teammate_context,
        get_context,
    )

    # Context manager (preferred):
    async with teammate_context("agent-001", {"agent_name": "Analyst"}):
        ctx = get_context()
        assert ctx.agent_id == "agent-001"
        assert ctx.metadata["agent_name"] == "Analyst"

    # Direct API:
    tc = TeammateContext()
    tc.set_context("agent-002", {"team_name": "research"})
    ctx = tc.get_context()
    tc.clear_context()

Version: 1.0.0
Date: 2026-04-02
Epic: MCE-V22 / Story MCE22-1.1
"""

from __future__ import annotations

import contextvars
import logging
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("mce.teammate_context")

# ---------------------------------------------------------------------------
# TeammateInfo -- immutable snapshot of agent context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TeammateInfo:
    """Immutable snapshot of the context for a single agent.

    Frozen dataclass ensures that once set, the context cannot be
    accidentally mutated by downstream code.

    Attributes:
        agent_id:   Unique identifier for the agent instance.
        agent_name: Human-readable agent name (e.g. ``"Analyst"``).
        team_name:  Name of the team/squad this agent belongs to.
        is_lead:    Whether this agent is the team lead / coordinator.
        mce_steps:  List of MCE pipeline steps this agent is responsible for.
        tier:       Agent tier classification (e.g. ``"Core"``, ``"Pro"``).
        metadata:   Arbitrary extra metadata dict for extensibility.
    """

    agent_id: str
    agent_name: str = ""
    team_name: str = ""
    is_lead: bool = False
    mce_steps: tuple[str, ...] = ()
    tier: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Module-level ContextVar -- the isolation primitive
# ---------------------------------------------------------------------------

#: The single ContextVar that holds the current agent's TeammateInfo.
#: Each async task / thread gets its own copy automatically via Python's
#: contextvars machinery -- this is how isolation is achieved without locks.
_current_teammate: contextvars.ContextVar[TeammateInfo | None] = contextvars.ContextVar(
    "current_teammate", default=None
)


# ---------------------------------------------------------------------------
# TeammateContext class -- direct API
# ---------------------------------------------------------------------------


class TeammateContext:
    """Isolated context storage per agent via ``contextvars.ContextVar``.

    This class wraps the module-level ``_current_teammate`` ContextVar and
    provides a clean API for setting, getting, and clearing agent context.

    Thread-safe and async-safe by construction: ``contextvars.ContextVar``
    automatically isolates values per-task in asyncio and per-thread in
    threading.

    Example::

        tc = TeammateContext()
        tc.set_context("agent-001", {
            "agent_name": "Analyst",
            "team_name": "research",
            "is_lead": False,
            "mce_steps": ["ingest", "batch"],
            "tier": "Core",
        })
        info = tc.get_context()
        assert info.agent_id == "agent-001"
        tc.clear_context()
    """

    def set_context(self, agent_id: str, metadata: dict[str, Any] | None = None) -> TeammateInfo:
        """Set the context for the current agent.

        Extracts well-known keys from *metadata* into typed fields on
        ``TeammateInfo`` and stores the rest in ``metadata.metadata``.

        Args:
            agent_id: Unique identifier for the agent.
            metadata: Optional dict with agent metadata.  Well-known keys:
                      ``agent_name``, ``team_name``, ``is_lead``,
                      ``mce_steps``, ``tier``.  All others go into
                      the ``metadata`` catch-all dict.

        Returns:
            The ``TeammateInfo`` instance that was stored.

        Raises:
            ValueError: If *agent_id* is empty or whitespace-only.
        """
        if not agent_id or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        meta = metadata or {}

        # Extract well-known fields, leave the rest in extra.
        well_known = {"agent_name", "team_name", "is_lead", "mce_steps", "tier"}
        extra = {k: v for k, v in meta.items() if k not in well_known}

        # Normalize mce_steps to tuple for immutability.
        raw_steps = meta.get("mce_steps", ())
        if isinstance(raw_steps, list):
            raw_steps = tuple(raw_steps)

        info = TeammateInfo(
            agent_id=agent_id.strip(),
            agent_name=str(meta.get("agent_name", "")),
            team_name=str(meta.get("team_name", "")),
            is_lead=bool(meta.get("is_lead", False)),
            mce_steps=raw_steps,
            tier=str(meta.get("tier", "")),
            metadata=extra,
        )

        _current_teammate.set(info)
        logger.debug(
            "Context set for agent %s (team=%s, lead=%s)", agent_id, info.team_name, info.is_lead
        )
        return info

    def get_context(self) -> TeammateInfo | None:
        """Return the ``TeammateInfo`` for the current execution context.

        Returns ``None`` if no context has been set (i.e. called outside
        of an agent scope).
        """
        return _current_teammate.get()

    def clear_context(self) -> None:
        """Clear the agent context for the current execution scope.

        After this call, ``get_context()`` returns ``None``.
        """
        _current_teammate.set(None)
        logger.debug("Context cleared")


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

#: Singleton instance used by the module-level convenience functions.
_default_instance = TeammateContext()


def set_context(agent_id: str, metadata: dict[str, Any] | None = None) -> TeammateInfo:
    """Module-level shortcut for ``TeammateContext().set_context(...)``."""
    return _default_instance.set_context(agent_id, metadata)


def get_context() -> TeammateInfo | None:
    """Module-level shortcut for ``TeammateContext().get_context()``."""
    return _default_instance.get_context()


def clear_context() -> None:
    """Module-level shortcut for ``TeammateContext().clear_context()``."""
    _default_instance.clear_context()


# ---------------------------------------------------------------------------
# Context managers -- the preferred way to scope agent context
# ---------------------------------------------------------------------------


@asynccontextmanager
async def teammate_context(agent_id: str, metadata: dict[str, Any] | None = None):
    """Async context manager that sets and clears agent context automatically.

    Usage::

        async with teammate_context("agent-001", {"agent_name": "Analyst"}):
            ctx = get_context()
            # ctx is available here
        # ctx is cleared here

    Args:
        agent_id: Unique identifier for the agent.
        metadata: Optional dict with agent metadata.

    Yields:
        The ``TeammateInfo`` that was set.
    """
    info = set_context(agent_id, metadata)
    try:
        yield info
    finally:
        clear_context()


@contextmanager
def teammate_context_sync(agent_id: str, metadata: dict[str, Any] | None = None):
    """Synchronous context manager variant for non-async code paths.

    Usage::

        with teammate_context_sync("agent-001", {"agent_name": "Analyst"}):
            ctx = get_context()

    Args:
        agent_id: Unique identifier for the agent.
        metadata: Optional dict with agent metadata.

    Yields:
        The ``TeammateInfo`` that was set.
    """
    info = set_context(agent_id, metadata)
    try:
        yield info
    finally:
        clear_context()
