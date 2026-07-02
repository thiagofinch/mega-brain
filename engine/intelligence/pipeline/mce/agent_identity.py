"""
agent_identity.py -- Agent Self-Awareness Identity System
=========================================================

Provides the ``AgentIdentity`` dataclass and ``get_identity()`` callable
so that any agent in the MCE pipeline knows *who it is*, *what team it
belongs to*, and *what role it plays*.

Architecture
------------
AgentIdentity reads from ``TeammateContext`` (MCE22-1.1).  When an agent
is spawned, the orchestrator sets the teammate context; this module reads
it and returns a typed identity object.  Logging is automatically enriched
with ``agent_name`` via a custom ``logging.Filter``.

Data Flow::

    orchestrate.py  →  set_context(agent_id, metadata)
                              ↓
    agent code      →  get_identity()  →  AgentIdentity
                              ↓
    logging         →  IdentityFilter auto-injects agent_name

Public API
----------
- ``AgentIdentity`` -- frozen dataclass with identity fields
- ``get_identity()`` -- reads current TeammateContext, returns AgentIdentity
- ``IdentityFilter`` -- logging filter that injects agent_name into log records
- ``install_identity_logging()`` -- convenience to attach filter to a logger

Version: 1.0.0
Date: 2026-04-02
Epic: MCE-V22 / Story MCE22-1.2
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from engine.intelligence.pipeline.mce.teammate_context import (
    TeammateInfo,
    get_context,
)

logger = logging.getLogger("mce.agent_identity")


# ---------------------------------------------------------------------------
# AgentIdentity dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentIdentity:
    """Immutable identity snapshot for a pipeline agent.

    All fields map 1:1 to ``TeammateInfo`` well-known keys set during
    agent spawn.  The frozen constraint ensures identity cannot be
    tampered with after construction.

    Attributes:
        agent_id:   Unique identifier for this agent instance.
        agent_name: Human-readable name (e.g. ``"Analyst"``).
        team_name:  Team/squad this agent belongs to.
        is_lead:    Whether this agent is the team lead / coordinator.
        mce_steps:  Pipeline steps this agent is responsible for.
        tier:       Agent tier (e.g. ``"Core"``, ``"Pro"``, ``"Enterprise"``).
    """

    agent_id: str
    agent_name: str = ""
    team_name: str = ""
    is_lead: bool = False
    mce_steps: tuple[str, ...] = ()
    tier: str = ""


# ---------------------------------------------------------------------------
# get_identity() -- reads from TeammateContext
# ---------------------------------------------------------------------------


def get_identity() -> AgentIdentity | None:
    """Return the ``AgentIdentity`` for the current execution context.

    Reads from the ``TeammateContext`` contextvar set by the orchestrator
    at agent spawn time.  Returns ``None`` if no context is active (i.e.
    called outside of an agent scope).

    Returns:
        ``AgentIdentity`` if context is set, ``None`` otherwise.
    """
    info: TeammateInfo | None = get_context()
    if info is None:
        return None

    return AgentIdentity(
        agent_id=info.agent_id,
        agent_name=info.agent_name,
        team_name=info.team_name,
        is_lead=info.is_lead,
        mce_steps=info.mce_steps,
        tier=info.tier,
    )


def require_identity() -> AgentIdentity:
    """Return ``AgentIdentity`` or raise if no context is active.

    Use this in code paths where identity MUST be present (i.e. inside
    a properly spawned agent).  Code outside agent scope should use
    ``get_identity()`` and handle ``None``.

    Returns:
        ``AgentIdentity`` for the current agent.

    Raises:
        RuntimeError: If no ``TeammateContext`` is set.
    """
    identity = get_identity()
    if identity is None:
        raise RuntimeError(
            "No agent identity available -- "
            "get_identity() returned None.  "
            "Ensure TeammateContext is set before calling require_identity()."
        )
    return identity


# ---------------------------------------------------------------------------
# IdentityFilter -- auto-inject agent_name into log records
# ---------------------------------------------------------------------------


class IdentityFilter(logging.Filter):
    """Logging filter that injects ``agent_name`` into every log record.

    When attached to a logger or handler, each ``LogRecord`` gets an
    ``agent_name`` attribute that formatters can reference via
    ``%(agent_name)s``.  If no identity is active, defaults to
    ``"unknown"``.

    Example::

        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(agent_name)s] %(message)s")
        )
        handler.addFilter(IdentityFilter())
        logger.addHandler(handler)
    """

    def __init__(self, default_name: str = "unknown") -> None:
        super().__init__()
        self._default_name = default_name

    def filter(self, record: logging.LogRecord) -> bool:
        """Inject agent_name into the log record.  Always returns True."""
        identity = get_identity()
        record.agent_name = (  # type: ignore[attr-defined]
            identity.agent_name if identity and identity.agent_name else self._default_name
        )
        return True


# ---------------------------------------------------------------------------
# install_identity_logging() -- convenience
# ---------------------------------------------------------------------------


def install_identity_logging(
    target_logger: logging.Logger | None = None,
    default_name: str = "unknown",
) -> IdentityFilter:
    """Attach an ``IdentityFilter`` to a logger for automatic agent_name injection.

    If no ``target_logger`` is provided, attaches to the root ``mce`` logger.

    Args:
        target_logger: Logger to attach the filter to.
        default_name:  Fallback name when no identity is active.

    Returns:
        The ``IdentityFilter`` instance (useful for later removal).
    """
    if target_logger is None:
        target_logger = logging.getLogger("mce")

    filt = IdentityFilter(default_name=default_name)
    target_logger.addFilter(filt)

    logger.debug(
        "Identity logging filter installed on logger '%s'",
        target_logger.name,
    )
    return filt
