"""
hook_bus.py -- Async Non-Blocking Hook Bus for the MCE Pipeline
================================================================

Architecture Decision
---------------------
The MCE governance system has **three** complementary layers:

- **Synapse** (``mce.yaml``) holds *declarative* rules.
- **qa_gates** (``qa_gates.py``) executes *imperative* blocking checks.
- **hook_bus** (this module) provides *async non-blocking* observability hooks.

Hooks OBSERVE, gates BLOCK.  They coexist without interference.

``qa_gates.py`` is NOT modified by this module.  The hook bus fires
at pipeline step boundaries (pre/post), on errors, and on state changes.
Hook failure in non-blocking mode never stops the pipeline.

Import Direction
----------------
``orchestrate.py`` imports this module.  This module MUST NOT import
``orchestrate.py`` or ``state_machine.py`` -- one-way dependency::

    orchestrate.py  -->  hook_bus.py
    orchestrate.py  -->  qa_gates.py  (unchanged)
    orchestrate.py  -->  state_machine.py

Public API -- Class Level
-------------------------
- ``HookBus()`` -- singleton-friendly bus with global enable toggle
- ``register(event, handler, priority=0)`` -- add a handler
- ``unregister(event, handler)`` -- remove a specific handler
- ``emit(event, payload)`` -- async non-blocking (fire-and-forget via threading)
- ``emit_blocking(event, payload) -> HookResult`` -- sync for vetos/human checkpoints
- ``enable_all(enabled=True)`` -- global toggle
- ``list_handlers(event) -> list[dict]`` -- introspection
- ``clear(event=None)`` -- remove all handlers for an event or all events

Public API -- Module Level (Custom Hook Registration)
-----------------------------------------------------
- ``register_hook(event, handler, priority=0)`` -- register on the singleton bus
- ``unregister_hook(event, handler)`` -- remove from the singleton bus
- ``clear_hooks(event=None)`` -- clear handlers on the singleton bus

Custom hook failure is ALWAYS non-blocking (fire-and-forget, log error).
Handlers with higher priority run first.

17 Event Types
--------------
pre_step, post_step, on_error, on_qa_gate, on_state_change, on_veto,
on_cost_threshold, pre_llm_call, post_llm_call, on_parallel_group_start,
on_parallel_group_complete, on_human_checkpoint, on_circuit_breaker_open,
on_policy_denied, on_session_paused, on_session_resumed, on_task_complete

Constraints
~~~~~~~~~~~
- stdlib only (no external deps, no LLM calls).
- Every function is DETERMINISTIC and side-effect-isolated.
- Non-blocking hooks swallow ALL exceptions (logged, never raised).
- Blocking hooks (on_veto, on_human_checkpoint) propagate results.

Version: 1.3.0
Date: 2026-04-02
Story: MCE22-1.6 -- Task Notification Protocol (added ON_TASK_COMPLETE)
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger("mce.hook_bus")

# ---------------------------------------------------------------------------
# 17 Canonical Event Types
# ---------------------------------------------------------------------------


class HookEvent(str, Enum):
    """Canonical event types for the MCE Hook Bus.

    17 events covering every observable pipeline boundary.
    """

    PRE_STEP = "pre_step"
    POST_STEP = "post_step"
    ON_ERROR = "on_error"
    ON_QA_GATE = "on_qa_gate"
    ON_STATE_CHANGE = "on_state_change"
    ON_VETO = "on_veto"
    ON_COST_THRESHOLD = "on_cost_threshold"
    PRE_LLM_CALL = "pre_llm_call"
    POST_LLM_CALL = "post_llm_call"
    ON_PARALLEL_GROUP_START = "on_parallel_group_start"
    ON_PARALLEL_GROUP_COMPLETE = "on_parallel_group_complete"
    ON_HUMAN_CHECKPOINT = "on_human_checkpoint"
    ON_CIRCUIT_BREAKER_OPEN = "on_circuit_breaker_open"
    ON_POLICY_DENIED = "on_policy_denied"
    ON_SESSION_PAUSED = "on_session_paused"
    ON_SESSION_RESUMED = "on_session_resumed"
    ON_TASK_COMPLETE = "on_task_complete"


# Events where emit_blocking() is the expected dispatch method.
# These are the only events where handler failure CAN block the pipeline.
BLOCKING_EVENTS: frozenset[str] = frozenset(
    {
        HookEvent.ON_VETO.value,
        HookEvent.ON_HUMAN_CHECKPOINT.value,
    }
)

# All valid event names (for fast membership check).
VALID_EVENTS: frozenset[str] = frozenset(e.value for e in HookEvent)


# ---------------------------------------------------------------------------
# Hook Result
# ---------------------------------------------------------------------------


@dataclass
class HookResult:
    """Result of a blocking hook emission.

    Attributes:
        event: The event that was emitted.
        success: True if ALL handlers succeeded without veto.
        vetoed: True if any handler returned a veto signal.
        veto_reason: Reason string from the first vetoing handler.
        handler_results: Individual results from each handler.
        duration_ms: Total wall-clock time for all handlers.
    """

    event: str
    success: bool = True
    vetoed: bool = False
    veto_reason: str = ""
    handler_results: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0


# ---------------------------------------------------------------------------
# Handler Registration Entry
# ---------------------------------------------------------------------------


@dataclass
class _HandlerEntry:
    """Internal record for a registered handler."""

    event: str
    handler: Callable[..., Any]
    priority: int = 0
    name: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            self.name = getattr(self.handler, "__name__", repr(self.handler))


# ---------------------------------------------------------------------------
# HookBus
# ---------------------------------------------------------------------------


class HookBus:
    """Async non-blocking hook bus for MCE pipeline observability.

    Handlers registered for non-blocking events run in daemon threads.
    Handlers registered for blocking events (on_veto, on_human_checkpoint)
    run synchronously when dispatched via ``emit_blocking()``.

    Hook failure in non-blocking mode NEVER blocks the pipeline.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[_HandlerEntry]] = {ev: [] for ev in VALID_EVENTS}
        self._enabled: bool = True
        self._lock: threading.Lock = threading.Lock()
        # Metrics: how many times each event was emitted
        self._emit_count: dict[str, int] = {ev: 0 for ev in VALID_EVENTS}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(
        self,
        event: str,
        handler: Callable[..., Any],
        priority: int = 0,
    ) -> None:
        """Register a handler for an event type.

        Args:
            event: One of the 17 canonical event names (see HookEvent).
            handler: Callable that receives ``(event: str, payload: dict)``.
                     For blocking events, the handler may return a dict with
                     ``{"vetoed": True, "reason": "..."}`` to signal a veto.
            priority: Higher priority handlers run first. Default 0.

        Raises:
            ValueError: If the event name is not one of the 17 canonical types.
        """
        event = self._normalize_event(event)
        entry = _HandlerEntry(event=event, handler=handler, priority=priority)
        with self._lock:
            self._handlers[event].append(entry)
            # Keep sorted by priority descending (highest first)
            self._handlers[event].sort(key=lambda e: e.priority, reverse=True)
        logger.debug(
            "Registered handler '%s' for event '%s' (priority=%d)", entry.name, event, priority
        )

    def emit(self, event: str, payload: dict[str, Any] | None = None) -> None:
        """Emit an event asynchronously (fire-and-forget).

        Each handler runs in its own daemon thread.  Exceptions are caught
        and logged -- they NEVER propagate to the caller.

        Args:
            event: One of the 17 canonical event names.
            payload: Arbitrary dict passed to each handler.
        """
        if not self._enabled:
            return

        event = self._normalize_event(event)
        payload = payload or {}

        with self._lock:
            handlers = list(self._handlers.get(event, []))
            self._emit_count[event] = self._emit_count.get(event, 0) + 1

        if not handlers:
            return

        for entry in handlers:
            t = threading.Thread(
                target=self._safe_run,
                args=(entry, event, payload),
                daemon=True,
                name=f"hook-{event}-{entry.name}",
            )
            t.start()

    def emit_blocking(
        self,
        event: str,
        payload: dict[str, Any] | None = None,
    ) -> HookResult:
        """Emit an event synchronously and collect results.

        Used for blocking events (on_veto, on_human_checkpoint) where the
        pipeline needs to wait for handler responses.

        Args:
            event: One of the 17 canonical event names.
            payload: Arbitrary dict passed to each handler.

        Returns:
            HookResult with aggregated handler responses.
        """
        if not self._enabled:
            return HookResult(event=event)

        event = self._normalize_event(event)
        payload = payload or {}

        with self._lock:
            handlers = list(self._handlers.get(event, []))
            self._emit_count[event] = self._emit_count.get(event, 0) + 1

        result = HookResult(event=event)
        t0 = time.monotonic()

        for entry in handlers:
            handler_t0 = time.monotonic()
            try:
                ret = entry.handler(event, payload)
                handler_ms = (time.monotonic() - handler_t0) * 1000

                handler_info: dict[str, Any] = {
                    "handler": entry.name,
                    "success": True,
                    "duration_ms": round(handler_ms, 1),
                }

                # Check for veto signal
                if isinstance(ret, dict) and ret.get("vetoed"):
                    result.vetoed = True
                    result.success = False
                    reason = ret.get("reason", "Handler vetoed without reason")
                    result.veto_reason = reason
                    handler_info["vetoed"] = True
                    handler_info["reason"] = reason
                    logger.warning(
                        "Hook '%s' vetoed event '%s': %s",
                        entry.name,
                        event,
                        reason,
                    )

                if isinstance(ret, dict):
                    handler_info["result"] = ret

                result.handler_results.append(handler_info)

            except Exception as exc:
                handler_ms = (time.monotonic() - handler_t0) * 1000
                logger.error(
                    "Blocking hook '%s' failed for event '%s': %s",
                    entry.name,
                    event,
                    exc,
                    exc_info=True,
                )
                result.handler_results.append(
                    {
                        "handler": entry.name,
                        "success": False,
                        "error": str(exc),
                        "duration_ms": round(handler_ms, 1),
                    }
                )
                # For blocking events, handler failure is NOT a veto.
                # Only explicit {"vetoed": True} counts as a veto.

        result.duration_ms = round((time.monotonic() - t0) * 1000, 1)
        return result

    def enable_all(self, enabled: bool = True) -> None:
        """Global toggle for all hooks.

        Args:
            enabled: If False, all emit() and emit_blocking() calls become
                     no-ops.  Handlers remain registered.
        """
        self._enabled = enabled
        logger.info("HookBus globally %s", "enabled" if enabled else "disabled")

    def list_handlers(self, event: str) -> list[dict[str, Any]]:
        """List registered handlers for an event.

        Args:
            event: One of the 17 canonical event names.

        Returns:
            List of dicts with handler name, priority, and event.
        """
        event = self._normalize_event(event)
        with self._lock:
            return [
                {
                    "name": entry.name,
                    "priority": entry.priority,
                    "event": entry.event,
                }
                for entry in self._handlers.get(event, [])
            ]

    @property
    def enabled(self) -> bool:
        """Whether the bus is globally enabled."""
        return self._enabled

    @property
    def emit_counts(self) -> dict[str, int]:
        """Number of times each event has been emitted."""
        with self._lock:
            return dict(self._emit_count)

    @property
    def total_handlers(self) -> int:
        """Total number of registered handlers across all events."""
        with self._lock:
            return sum(len(hl) for hl in self._handlers.values())

    def clear(self, event: str | None = None) -> None:
        """Remove all handlers for an event, or all events if None.

        Args:
            event: Specific event to clear, or None for all.
        """
        with self._lock:
            if event is None:
                for ev in self._handlers:
                    self._handlers[ev] = []
            else:
                ev = self._normalize_event(event)
                self._handlers[ev] = []

    def unregister(self, event: str, handler: Callable[..., Any]) -> bool:
        """Remove a specific handler from an event.

        Args:
            event: One of the 17 canonical event names.
            handler: The exact callable that was previously registered.

        Returns:
            True if the handler was found and removed, False otherwise.
        """
        event = self._normalize_event(event)
        with self._lock:
            before = len(self._handlers[event])
            self._handlers[event] = [
                entry for entry in self._handlers[event] if entry.handler is not handler
            ]
            removed = before - len(self._handlers[event])

        if removed:
            logger.debug(
                "Unregistered handler for event '%s' (removed %d)",
                event,
                removed,
            )
            return True

        logger.debug(
            "Handler not found for event '%s' -- nothing to unregister",
            event,
        )
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_event(self, event: str) -> str:
        """Validate and normalize an event name.

        Accepts both raw strings and HookEvent enum members.
        """
        if isinstance(event, HookEvent):
            return event.value

        val = event.lower().strip()
        if val not in VALID_EVENTS:
            raise ValueError(
                f"Unknown hook event '{event}'. " f"Valid events: {sorted(VALID_EVENTS)}"
            )
        return val

    @staticmethod
    def _safe_run(
        entry: _HandlerEntry,
        event: str,
        payload: dict[str, Any],
    ) -> None:
        """Run a handler in a thread-safe, exception-swallowing wrapper.

        This is used by emit() for non-blocking dispatch.
        Exceptions are logged but NEVER propagated.
        """
        try:
            entry.handler(event, payload)
        except Exception as exc:
            logger.error(
                "Non-blocking hook '%s' failed for event '%s': %s",
                entry.name,
                event,
                exc,
                exc_info=True,
            )
            # Swallowed -- pipeline continues regardless.


# ---------------------------------------------------------------------------
# Module-level singleton (convenience)
# ---------------------------------------------------------------------------

# Default bus instance.  Import and use directly, or create your own.
_default_bus: HookBus | None = None
_bus_lock = threading.Lock()


def get_hook_bus() -> HookBus:
    """Get or create the module-level singleton HookBus.

    Thread-safe lazy initialization.
    """
    global _default_bus
    if _default_bus is None:
        with _bus_lock:
            if _default_bus is None:
                _default_bus = HookBus()
    return _default_bus


def reset_hook_bus() -> None:
    """Reset the module-level singleton.  Useful for testing."""
    global _default_bus
    with _bus_lock:
        _default_bus = None


# ---------------------------------------------------------------------------
# Public API -- Custom Hook Registration (MCE2-1.3)
# ---------------------------------------------------------------------------


def register_hook(
    event: str,
    handler: Callable[..., Any],
    priority: int = 0,
) -> None:
    """Register a custom hook handler on the singleton bus.

    This is the primary public API for plugin developers to extend pipeline
    behavior with their own event handlers without modifying core code.

    Handlers with higher priority run first.  Custom hook failure is ALWAYS
    non-blocking -- exceptions are logged but never propagate to the pipeline.

    Args:
        event: One of the 17 canonical event names (see ``HookEvent``).
               Both string and ``HookEvent`` enum values are accepted.
        handler: Callable that receives ``(event: str, payload: dict)``.
        priority: Higher priority handlers run first.  Default 0.

    Raises:
        ValueError: If the event name is not one of the 17 canonical types.
        TypeError: If handler is not callable.

    Example::

        from engine.intelligence.pipeline.mce.hook_bus import register_hook

        def my_logger(event, payload):
            print(f"[{event}] {payload}")

        register_hook("post_step", my_logger, priority=5)
    """
    if not callable(handler):
        raise TypeError(f"handler must be callable, got {type(handler).__name__}")
    bus = get_hook_bus()
    bus.register(event, handler, priority)


def unregister_hook(event: str, handler: Callable[..., Any]) -> bool:
    """Remove a custom hook handler from the singleton bus.

    Args:
        event: One of the 17 canonical event names.
        handler: The exact callable that was previously registered.

    Returns:
        True if the handler was found and removed, False otherwise.

    Raises:
        ValueError: If the event name is not one of the 17 canonical types.
    """
    bus = get_hook_bus()
    return bus.unregister(event, handler)


def clear_hooks(event: str | None = None) -> None:
    """Clear all handlers for an event, or all handlers if event is None.

    Args:
        event: Specific event to clear, or None to clear all events.

    Raises:
        ValueError: If event is provided and not one of the 17 canonical types.
    """
    bus = get_hook_bus()
    bus.clear(event)
