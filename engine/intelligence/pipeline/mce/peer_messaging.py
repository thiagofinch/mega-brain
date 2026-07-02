"""
peer_messaging.py -- Agent-to-Agent Peer Messaging System
=========================================================

Provides the high-level API for agents to communicate directly with each
other without going through the orchestrator for every interaction.

Architecture
------------
Peer Messaging builds on top of the ``Mailbox`` (MCE22-3.1) and
``TeammateContext`` (MCE22-1.1) modules.  The messaging layer provides:

- Point-to-point: ``send_message(A, B, content)`` -- A sends to B
- Broadcast: ``broadcast(A, content)`` -- A sends to all teammates
- Inbox integration: agents read their inbox at the start of each turn

The ``Mailbox`` handles filesystem persistence (JSONL).  This module
handles the messaging protocol: routing, broadcast fan-out, message type
validation, and convenience functions.

Data Flow::

    Agent A                    Mailbox                    Agent B
    ─────────                  ───────                    ─────────
    send_message(A, B, "hi")
         │
         └──▶ Mailbox.write_to_mailbox(B, msg)
                    │
                    └──▶ {B}.jsonl  (appended)
                              │
              next turn ──────┘
                    │
         Agent B calls read_inbox(B)
                    │
                    └──▶ returns [PeerMessage(from=A, content="hi")]

    broadcast(A, "alert")
         │
         ├──▶ Mailbox.write_to_mailbox(B, msg)
         ├──▶ Mailbox.write_to_mailbox(C, msg)
         └──▶ Mailbox.write_to_mailbox(D, msg)
              (fan-out to all teammates except sender)

Public API
----------
- ``send_message(from_agent, to_agent, content, msg_type)`` -- point-to-point
- ``broadcast(from_agent, content, msg_type)`` -- fan-out to all teammates
- ``read_inbox(agent_id)`` -- consume all pending messages
- ``peek_inbox(agent_id)`` -- inspect without consuming
- ``get_peer_messenger()`` -- get or create the singleton PeerMessenger

Constraints
~~~~~~~~~~~
- stdlib only (no external deps).
- Thread-safe (delegates to Mailbox locks).
- Broadcast discovers teammates from mailbox file listing.

Version: 1.0.0
Date: 2026-04-02
Epic: MCE-V22 / Story MCE22-3.1
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from engine.intelligence.pipeline.mce.mailbox import Mailbox, PeerMessage

logger = logging.getLogger("mce.peer_messaging")


# ---------------------------------------------------------------------------
# PeerMessenger -- the high-level messaging facade
# ---------------------------------------------------------------------------


class PeerMessenger:
    """High-level facade for agent-to-agent messaging.

    Wraps a ``Mailbox`` instance and provides convenience methods for
    point-to-point messaging, broadcasting, and inbox reading.

    The PeerMessenger also tracks registered teammates for broadcast
    fan-out.  Teammates can be registered explicitly via
    ``register_teammate()`` or discovered from existing inbox files.

    Args:
        mailbox: The ``Mailbox`` instance to use for persistence.
    """

    def __init__(self, mailbox: Mailbox) -> None:
        self._mailbox = mailbox
        self._teammates: set[str] = set()
        self._lock = threading.Lock()

    @property
    def mailbox(self) -> Mailbox:
        """The underlying Mailbox instance."""
        return self._mailbox

    @property
    def teammates(self) -> frozenset[str]:
        """Currently registered teammate IDs (read-only snapshot)."""
        with self._lock:
            return frozenset(self._teammates)

    def register_teammate(self, agent_id: str) -> None:
        """Register an agent ID as a known teammate for broadcast.

        Args:
            agent_id: The agent's unique identifier.
        """
        with self._lock:
            self._teammates.add(agent_id)
        logger.debug("Teammate registered: %s", agent_id)

    def register_teammates(self, agent_ids: list[str] | set[str]) -> None:
        """Register multiple agent IDs as teammates.

        Args:
            agent_ids: Collection of agent identifiers.
        """
        with self._lock:
            self._teammates.update(agent_ids)
        logger.debug("Teammates registered: %s", agent_ids)

    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        msg_type: str = "message",
    ) -> PeerMessage:
        """Send a point-to-point message from one agent to another.

        Creates a ``PeerMessage`` and writes it to the recipient's
        mailbox.  If ``to_agent`` is ``'*'``, delegates to ``broadcast()``.

        Args:
            from_agent: ID of the sending agent.
            to_agent:   ID of the receiving agent, or ``'*'`` for broadcast.
            content:    Message body.
            msg_type:   One of ``'message'``, ``'shutdown_request'``,
                        ``'shutdown_response'``.  Defaults to ``'message'``.

        Returns:
            The ``PeerMessage`` that was sent.

        Raises:
            ValueError: If ``from_agent`` or ``to_agent`` is empty.
            ValueError: If ``msg_type`` is not a valid type.
        """
        if not from_agent or not from_agent.strip():
            raise ValueError("from_agent must be a non-empty string")
        if not to_agent or not to_agent.strip():
            raise ValueError("to_agent must be a non-empty string")

        # Broadcast shorthand.
        if to_agent == "*":
            return self.broadcast(from_agent, content, msg_type)

        message = PeerMessage(
            from_agent=from_agent.strip(),
            to_agent=to_agent.strip(),
            content=content,
            msg_type=msg_type,
        )

        self._mailbox.write_to_mailbox(to_agent.strip(), message)

        logger.info(
            "Message sent: %s -> %s (type=%s, %d chars)",
            from_agent,
            to_agent,
            msg_type,
            len(content),
        )
        return message

    def broadcast(
        self,
        from_agent: str,
        content: str,
        msg_type: str = "message",
    ) -> PeerMessage:
        """Broadcast a message to all registered teammates.

        Creates a single ``PeerMessage`` with ``to_agent='*'`` and
        writes a copy to every teammate's mailbox (except the sender).

        Teammates are discovered from: (1) explicitly registered IDs,
        and (2) existing inbox files in the mailbox directory.

        Args:
            from_agent: ID of the sending agent.
            content:    Message body.
            msg_type:   One of ``'message'``, ``'shutdown_request'``,
                        ``'shutdown_response'``.  Defaults to ``'message'``.

        Returns:
            The broadcast ``PeerMessage`` (with ``to_agent='*'``).

        Raises:
            ValueError: If ``from_agent`` is empty.
            ValueError: If ``msg_type`` is not a valid type.
        """
        if not from_agent or not from_agent.strip():
            raise ValueError("from_agent must be a non-empty string")

        from_agent = from_agent.strip()

        message = PeerMessage(
            from_agent=from_agent,
            to_agent="*",
            content=content,
            msg_type=msg_type,
        )

        # Discover all teammates: registered + inbox file owners.
        with self._lock:
            all_teammates = set(self._teammates)
        all_teammates.update(self._mailbox.list_inboxes())

        # Exclude the sender from broadcast recipients.
        recipients = all_teammates - {from_agent}

        for recipient in sorted(recipients):
            self._mailbox.write_to_mailbox(recipient, message)

        logger.info(
            "Broadcast sent: %s -> %d recipients (type=%s, %d chars)",
            from_agent,
            len(recipients),
            msg_type,
            len(content),
        )
        return message

    def read_inbox(self, agent_id: str) -> list[PeerMessage]:
        """Read and clear all messages from an agent's inbox.

        This is the consume operation.  After reading, the inbox is
        cleared.  Agents should call this at the start of each turn.

        Args:
            agent_id: ID of the agent whose inbox to read.

        Returns:
            List of ``PeerMessage`` objects in chronological order.
        """
        return self._mailbox.read_inbox(agent_id)

    def peek_inbox(self, agent_id: str) -> list[PeerMessage]:
        """Read all messages from an agent's inbox without clearing.

        Useful for monitoring and debugging.

        Args:
            agent_id: ID of the agent whose inbox to peek.

        Returns:
            List of ``PeerMessage`` objects in chronological order.
        """
        return self._mailbox.peek_inbox(agent_id)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_messenger: PeerMessenger | None = None
_messenger_lock = threading.Lock()


def get_peer_messenger(base_dir: str | Path | None = None) -> PeerMessenger:
    """Get or create the module-level singleton PeerMessenger.

    On first call, creates a ``Mailbox`` at the specified ``base_dir``
    (or the default location) and wraps it in a ``PeerMessenger``.

    Args:
        base_dir: Root directory for mailbox storage.  If ``None``, a
                  default must have been set via a prior call or
                  ``init_peer_messaging()``.

    Returns:
        The singleton ``PeerMessenger``.

    Raises:
        RuntimeError: If no ``base_dir`` was provided and no singleton exists.
    """
    global _default_messenger
    if _default_messenger is not None:
        return _default_messenger

    with _messenger_lock:
        if _default_messenger is not None:
            return _default_messenger

        if base_dir is None:
            raise RuntimeError(
                "PeerMessenger not initialized. "
                "Call init_peer_messaging(base_dir) first, or "
                "pass base_dir to get_peer_messenger()."
            )

        mailbox = Mailbox(base_dir)
        _default_messenger = PeerMessenger(mailbox)
        logger.info("PeerMessenger initialized at %s", base_dir)

    return _default_messenger


def init_peer_messaging(base_dir: str | Path) -> PeerMessenger:
    """Initialize the peer messaging singleton with a mailbox directory.

    Convenience function that ensures the singleton is created with the
    specified base directory.  Safe to call multiple times (idempotent
    after first call -- subsequent calls return the existing singleton).

    Args:
        base_dir: Root directory for mailbox storage.

    Returns:
        The initialized ``PeerMessenger``.
    """
    return get_peer_messenger(base_dir)


def reset_peer_messaging() -> None:
    """Reset the module-level singleton.  Useful for testing."""
    global _default_messenger
    with _messenger_lock:
        _default_messenger = None


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------


def send_message(
    from_agent: str,
    to_agent: str,
    content: str,
    msg_type: str = "message",
) -> PeerMessage:
    """Module-level shortcut for ``PeerMessenger.send_message()``.

    Requires the singleton to be initialized via ``init_peer_messaging()``.

    Args:
        from_agent: ID of the sending agent.
        to_agent:   ID of the receiving agent, or ``'*'`` for broadcast.
        content:    Message body.
        msg_type:   Message type.  Defaults to ``'message'``.

    Returns:
        The ``PeerMessage`` that was sent.
    """
    messenger = get_peer_messenger()
    return messenger.send_message(from_agent, to_agent, content, msg_type)


def broadcast(
    from_agent: str,
    content: str,
    msg_type: str = "message",
) -> PeerMessage:
    """Module-level shortcut for ``PeerMessenger.broadcast()``.

    Args:
        from_agent: ID of the sending agent.
        content:    Message body.
        msg_type:   Message type.  Defaults to ``'message'``.

    Returns:
        The broadcast ``PeerMessage``.
    """
    messenger = get_peer_messenger()
    return messenger.broadcast(from_agent, content, msg_type)


def read_inbox(agent_id: str) -> list[PeerMessage]:
    """Module-level shortcut for ``PeerMessenger.read_inbox()``.

    Args:
        agent_id: ID of the agent whose inbox to read.

    Returns:
        List of ``PeerMessage`` objects.
    """
    messenger = get_peer_messenger()
    return messenger.read_inbox(agent_id)


def peek_inbox(agent_id: str) -> list[PeerMessage]:
    """Module-level shortcut for ``PeerMessenger.peek_inbox()``.

    Args:
        agent_id: ID of the agent whose inbox to peek.

    Returns:
        List of ``PeerMessage`` objects.
    """
    messenger = get_peer_messenger()
    return messenger.peek_inbox(agent_id)
