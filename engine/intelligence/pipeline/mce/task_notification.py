"""
task_notification.py -- Structured Task Completion Notifications
===============================================================

Provides the ``TaskNotification`` dataclass and helper functions for
emitting structured completion signals from agents to the orchestrator.

Architecture
------------
When an agent finishes a task, it creates a ``TaskNotification`` and
calls ``notify_task_complete()``.  This function:

1. Emits ``on_task_complete`` via the ``HookBus`` (so observers can react).
2. Returns the notification for the orchestrator to read between DAG steps.
3. Notifications can be persisted to the pipeline manifest for audit.

Data Flow::

    agent completes task
          ↓
    notify_task_complete(notification)
          ↓
    hook_bus.emit("on_task_complete", payload)
          ↓                    ↓
    observers react     orchestrator reads
                              ↓
                    manifest persistence (optional)

Public API
----------
- ``TaskNotification`` -- frozen dataclass with completion fields
- ``notify_task_complete()`` -- emit notification via hook_bus
- ``collect_notifications()`` -- gather all notifications for a run
- ``notifications_to_manifest()`` -- serialize for manifest persistence

Version: 1.0.0
Date: 2026-04-02
Epic: MCE-V22 / Story MCE22-1.6
"""

from __future__ import annotations

import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from engine.intelligence.pipeline.mce.hook_bus import (
    HookEvent,
    get_hook_bus,
)

logger = logging.getLogger("mce.task_notification")


# ---------------------------------------------------------------------------
# TaskStatus enum
# ---------------------------------------------------------------------------


class TaskStatus(str, Enum):
    """Possible statuses for a completed task notification.

    - ``SUCCESS``:  Task completed normally.
    - ``FAILED``:   Task encountered an unrecoverable error.
    - ``SKIPPED``:  Task was skipped (e.g. gate condition not met).
    - ``PARTIAL``:  Task completed but with degraded output.
    """

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


# ---------------------------------------------------------------------------
# TaskNotification dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaskNotification:
    """Immutable notification emitted when an agent completes a task.

    The orchestrator reads these between DAG steps to decide whether
    to proceed, retry, or halt.  Notifications are also persisted to
    the pipeline manifest for audit trail.

    Attributes:
        agent_id:     ID of the agent that completed the task.
        status:       Completion status (success, failed, skipped, partial).
        summary:      Human-readable summary of what was done.
        result:       Arbitrary result data from the task.
        tokens_used:  Number of LLM tokens consumed by this task.
        duration:     Wall-clock duration in seconds.
        step_name:    Name of the pipeline step (for DAG correlation).
        timestamp:    ISO 8601 timestamp of completion.
        error:        Error message if status is FAILED.
    """

    agent_id: str
    status: TaskStatus = TaskStatus.SUCCESS
    summary: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    duration: float = 0.0
    step_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for YAML/JSON persistence."""
        data = asdict(self)
        # Convert TaskStatus enum to string value
        data["status"] = self.status.value
        return data


# ---------------------------------------------------------------------------
# Notification Collector -- aggregates notifications per run
# ---------------------------------------------------------------------------


class NotificationCollector:
    """Thread-safe collector that aggregates notifications for a pipeline run.

    The orchestrator creates one collector per run and passes it to
    ``notify_task_complete()``.  After all steps finish, the collector
    holds the complete notification history.

    Usage::

        collector = NotificationCollector()
        notify_task_complete(notification, collector=collector)
        # ... more steps ...
        all_notifications = collector.get_all()
    """

    def __init__(self) -> None:
        self._notifications: list[TaskNotification] = []
        self._lock = threading.Lock()

    def add(self, notification: TaskNotification) -> None:
        """Add a notification to the collection (thread-safe)."""
        with self._lock:
            self._notifications.append(notification)

    def get_all(self) -> list[TaskNotification]:
        """Return all collected notifications (copy of internal list)."""
        with self._lock:
            return list(self._notifications)

    def get_by_step(self, step_name: str) -> list[TaskNotification]:
        """Return notifications for a specific step."""
        with self._lock:
            return [n for n in self._notifications if n.step_name == step_name]

    def get_by_status(self, status: TaskStatus) -> list[TaskNotification]:
        """Return notifications with a specific status."""
        with self._lock:
            return [n for n in self._notifications if n.status == status]

    @property
    def count(self) -> int:
        """Total number of collected notifications."""
        with self._lock:
            return len(self._notifications)

    @property
    def has_failures(self) -> bool:
        """Whether any notification has FAILED status."""
        with self._lock:
            return any(n.status == TaskStatus.FAILED for n in self._notifications)

    def clear(self) -> None:
        """Clear all collected notifications."""
        with self._lock:
            self._notifications.clear()


# ---------------------------------------------------------------------------
# notify_task_complete() -- emit via hook_bus
# ---------------------------------------------------------------------------


def notify_task_complete(
    notification: TaskNotification,
    *,
    collector: NotificationCollector | None = None,
    blocking: bool = False,
) -> TaskNotification:
    """Emit a task completion notification via the hook bus.

    This is the primary function agents call when they finish a task.
    It emits the ``on_task_complete`` event on the hook bus, optionally
    collects the notification, and returns it for the orchestrator.

    Args:
        notification: The ``TaskNotification`` to emit.
        collector:    Optional ``NotificationCollector`` to aggregate
                      notifications across the pipeline run.
        blocking:     If True, use ``emit_blocking()`` instead of ``emit()``.
                      Useful when downstream handlers need to process
                      the notification synchronously.

    Returns:
        The same ``TaskNotification`` (pass-through for chaining).
    """
    bus = get_hook_bus()
    payload = notification.to_dict()

    if blocking:
        result = bus.emit_blocking(HookEvent.ON_TASK_COMPLETE, payload)
        logger.debug(
            "Task notification emitted (blocking) for agent=%s step=%s: %s (%.1fms)",
            notification.agent_id,
            notification.step_name,
            notification.status.value,
            result.duration_ms,
        )
    else:
        bus.emit(HookEvent.ON_TASK_COMPLETE, payload)
        logger.debug(
            "Task notification emitted for agent=%s step=%s: %s",
            notification.agent_id,
            notification.step_name,
            notification.status.value,
        )

    if collector is not None:
        collector.add(notification)

    return notification


# ---------------------------------------------------------------------------
# notifications_to_manifest() -- serialize for persistence
# ---------------------------------------------------------------------------


def notifications_to_manifest(
    notifications: list[TaskNotification],
) -> list[dict[str, Any]]:
    """Convert a list of notifications to manifest-ready dicts.

    The manifest stores notifications as a list of plain dicts under
    the ``task_notifications`` key.  This function handles the
    serialization.

    Args:
        notifications: List of ``TaskNotification`` objects.

    Returns:
        List of plain dicts suitable for YAML persistence.
    """
    return [n.to_dict() for n in notifications]


# ---------------------------------------------------------------------------
# Convenience: create + notify in one call
# ---------------------------------------------------------------------------


def complete_task(
    agent_id: str,
    *,
    status: TaskStatus = TaskStatus.SUCCESS,
    summary: str = "",
    result: dict[str, Any] | None = None,
    tokens_used: int = 0,
    duration: float = 0.0,
    step_name: str = "",
    error: str = "",
    collector: NotificationCollector | None = None,
    blocking: bool = False,
) -> TaskNotification:
    """Create a ``TaskNotification`` and emit it in one call.

    Convenience function that combines notification construction and
    emission.  Used by agents that don't need to customize the
    notification object.

    Args:
        agent_id:    ID of the completing agent.
        status:      Task completion status.
        summary:     Human-readable summary.
        result:      Arbitrary result dict.
        tokens_used: Tokens consumed.
        duration:    Duration in seconds.
        step_name:   Pipeline step name.
        error:       Error message (if failed).
        collector:   Optional collector for aggregation.
        blocking:    Use blocking emit.

    Returns:
        The created and emitted ``TaskNotification``.
    """
    notification = TaskNotification(
        agent_id=agent_id,
        status=status,
        summary=summary,
        result=result or {},
        tokens_used=tokens_used,
        duration=duration,
        step_name=step_name,
        error=error,
    )

    return notify_task_complete(
        notification,
        collector=collector,
        blocking=blocking,
    )
