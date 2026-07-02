"""
mailbox.py -- Filesystem-Backed Per-Agent Mailbox
=================================================

Provides the ``Mailbox`` class for persistent, per-agent message storage
using JSONL (JSON Lines) files.  Each agent gets its own inbox file at::

    .claude/mission-control/mce/{slug}/mailbox/{agent_id}.jsonl

Architecture
------------
The mailbox is the persistence layer for the Peer Messaging system
(MCE22-3.1).  ``peer_messaging.py`` builds on top of this module to
provide the ``send_message()`` and ``broadcast()`` convenience API.

The JSONL format was chosen over YAML or plain JSON because:
- Append-only: new messages are appended without rewriting the file
- Crash-safe: a partial write only corrupts the last line
- Line-oriented: easy to parse, easy to tail, easy to debug

Data Flow::

    send_message()  →  Mailbox.write_to_mailbox()  →  {agent}.jsonl
                                                          ↓
    agent turn start  →  Mailbox.read_inbox()  →  List[PeerMessage]
                                                   (clears file)

Public API
----------
- ``Mailbox(base_dir)`` -- mailbox manager for a mission slug
- ``write_to_mailbox(agent_id, message)`` -- append a message to an agent's inbox
- ``read_inbox(agent_id)`` -- read and clear all messages (consume)
- ``peek_inbox(agent_id)`` -- read without clearing (inspect)
- ``inbox_path(agent_id)`` -- return the Path for an agent's inbox file
- ``list_inboxes()`` -- list all agent IDs that have inbox files

Constraints
~~~~~~~~~~~
- stdlib only (no external deps).
- Every function is DETERMINISTIC and side-effect-isolated to the mailbox dir.
- Thread-safe via per-agent file locks.
- Graceful degradation: corrupt lines are skipped with a warning.

Version: 1.0.0
Date: 2026-04-02
Epic: MCE-V22 / Story MCE22-3.1
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("mce.mailbox")


# ---------------------------------------------------------------------------
# PeerMessage dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PeerMessage:
    """Immutable message sent between agents.

    Attributes:
        from_agent: ID of the sending agent.
        to_agent:   ID of the receiving agent (``'*'`` for broadcast).
        content:    Message body (free text or structured string).
        msg_type:   One of ``'message'``, ``'shutdown_request'``,
                    ``'shutdown_response'``.
        timestamp:  ISO 8601 timestamp of when the message was created.
    """

    from_agent: str
    to_agent: str
    content: str
    msg_type: str = "message"
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self) -> None:
        """Validate msg_type against canonical values."""
        valid_types = {"message", "shutdown_request", "shutdown_response"}
        if self.msg_type not in valid_types:
            raise ValueError(
                f"Invalid msg_type '{self.msg_type}'. " f"Must be one of: {sorted(valid_types)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for JSON persistence."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PeerMessage:
        """Deserialize from a plain dict (e.g. from JSONL line).

        Args:
            data: Dict with PeerMessage fields.

        Returns:
            A new ``PeerMessage`` instance.

        Raises:
            KeyError: If required fields are missing.
        """
        return cls(
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            content=data["content"],
            msg_type=data.get("msg_type", "message"),
            timestamp=data.get("timestamp", datetime.now(UTC).isoformat()),
        )


# ---------------------------------------------------------------------------
# Mailbox class
# ---------------------------------------------------------------------------


class Mailbox:
    """Filesystem-backed per-agent mailbox using JSONL files.

    Each agent gets its own inbox file.  Messages are appended as JSON
    lines.  ``read_inbox()`` consumes (reads + clears) the inbox.
    ``peek_inbox()`` reads without clearing.

    Thread-safety is achieved via per-agent ``threading.Lock`` instances.
    Multiple agents can read/write concurrently as long as they target
    different inbox files.

    Args:
        base_dir: Root directory for mailbox storage.  Each agent's inbox
                  lives at ``{base_dir}/{agent_id}.jsonl``.
    """

    def __init__(self, base_dir: str | Path) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()

    @property
    def base_dir(self) -> Path:
        """The root directory for mailbox storage."""
        return self._base_dir

    def _get_lock(self, agent_id: str) -> threading.Lock:
        """Get or create a per-agent lock (thread-safe)."""
        with self._global_lock:
            if agent_id not in self._locks:
                self._locks[agent_id] = threading.Lock()
            return self._locks[agent_id]

    def inbox_path(self, agent_id: str) -> Path:
        """Return the filesystem path for an agent's inbox file.

        Args:
            agent_id: The agent's unique identifier.

        Returns:
            Path to ``{base_dir}/{agent_id}.jsonl``.
        """
        return self._base_dir / f"{agent_id}.jsonl"

    def write_to_mailbox(self, agent_id: str, message: PeerMessage) -> None:
        """Append a message to an agent's inbox file.

        Creates the inbox file if it does not exist.  Appends a single
        JSON line per message.

        Args:
            agent_id: ID of the receiving agent.
            message:  The ``PeerMessage`` to deliver.
        """
        lock = self._get_lock(agent_id)
        inbox = self.inbox_path(agent_id)

        with lock:
            with inbox.open("a", encoding="utf-8") as f:
                f.write(json.dumps(message.to_dict()) + "\n")

        logger.debug(
            "Message written to mailbox: %s -> %s (type=%s)",
            message.from_agent,
            agent_id,
            message.msg_type,
        )

    def read_inbox(self, agent_id: str) -> list[PeerMessage]:
        """Read and clear all messages from an agent's inbox.

        This is the consume operation: after reading, the inbox file is
        truncated.  If the inbox does not exist or is empty, returns an
        empty list.

        Corrupt lines (invalid JSON) are skipped with a warning log.

        Args:
            agent_id: ID of the agent whose inbox to read.

        Returns:
            List of ``PeerMessage`` objects in chronological order.
        """
        lock = self._get_lock(agent_id)
        inbox = self.inbox_path(agent_id)

        with lock:
            if not inbox.exists():
                return []

            messages = self._parse_inbox(inbox)

            # Clear the inbox after reading (consume).
            inbox.write_text("", encoding="utf-8")

        logger.debug(
            "Inbox read and cleared for agent %s: %d messages",
            agent_id,
            len(messages),
        )
        return messages

    def peek_inbox(self, agent_id: str) -> list[PeerMessage]:
        """Read all messages from an agent's inbox without clearing.

        Same as ``read_inbox()`` but does NOT truncate the file.  Useful
        for monitoring and debugging.

        Args:
            agent_id: ID of the agent whose inbox to peek.

        Returns:
            List of ``PeerMessage`` objects in chronological order.
        """
        lock = self._get_lock(agent_id)
        inbox = self.inbox_path(agent_id)

        with lock:
            if not inbox.exists():
                return []

            messages = self._parse_inbox(inbox)

        logger.debug(
            "Inbox peeked for agent %s: %d messages",
            agent_id,
            len(messages),
        )
        return messages

    def list_inboxes(self) -> list[str]:
        """List all agent IDs that have inbox files.

        Returns:
            List of agent IDs (derived from ``*.jsonl`` filenames).
        """
        if not self._base_dir.exists():
            return []

        return sorted(p.stem for p in self._base_dir.glob("*.jsonl") if p.stat().st_size > 0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_inbox(inbox: Path) -> list[PeerMessage]:
        """Parse a JSONL inbox file into PeerMessage objects.

        Corrupt lines are skipped with a warning.  Empty lines are
        silently ignored.

        Args:
            inbox: Path to the JSONL file.

        Returns:
            List of valid ``PeerMessage`` objects.
        """
        messages: list[PeerMessage] = []
        raw = inbox.read_text(encoding="utf-8")

        for line_num, line in enumerate(raw.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue

            try:
                data = json.loads(stripped)
                messages.append(PeerMessage.from_dict(data))
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                logger.warning(
                    "Corrupt message at %s:%d -- skipping: %s",
                    inbox,
                    line_num,
                    exc,
                )

        return messages
