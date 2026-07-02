"""
dream_task.py -- Proactive Background Agent for Session Memory Consolidation
=============================================================================

Architecture Decision
---------------------
DreamTask is a **proactive background step** that runs during idle time to
consolidate fragmented session memory into optimized context.  It reduces
token waste on the next active session by pre-compacting memory.

Think of it like defragmenting a hard drive -- except it is session memory,
and it runs only when the system is idle and the budget allows it.

Integration Points
------------------
::

    dream_task.py  -->  context_compactor.py  (CircuitBreaker reuse)
    dream_task.py  -->  cost_tracker.py       (budget check before execute)
    dream_task.py  -->  hook_bus.py           (on_dream_start/complete/skipped)
    dream_task.py  -->  config_cascade.py     (DreamConfig resolution)
    dream_task.py  -->  state_machine.py      (_state_dir for lock file path)

3 Trigger Gates
---------------
All three must pass for a dream to execute:

1. **time_gate**    -- At least N hours since last dream run.
2. **session_gate** -- At least N sessions since last dream run.
3. **lock_check**   -- No other dream currently running (lock file absent).

Safety Layers
~~~~~~~~~~~~~
- Budget check BEFORE execution (cost_tracker.check_budget).
- CircuitBreaker stops retries after N consecutive failures.
- Lock file prevents concurrent dream executions per slug.
- Disabled by default (enabled: false in dream_config.yaml).

Hook Events (3 new events, emitted via existing HookBus)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- ``on_dream_start``    -- Dream execution begins.
- ``on_dream_complete`` -- Dream finished successfully.
- ``on_dream_skipped``  -- Dream was skipped (with reason).

These use the existing HookBus.emit() (fire-and-forget, non-blocking).
Since they are not in the canonical 14 HookEvent enum, they are emitted
as raw strings -- HookBus._normalize_event() will reject them, so we
bypass validation by calling handlers directly via a safe wrapper.

Pipeline Manifest
~~~~~~~~~~~~~~~~~
DreamTask exposes ``manifest_entry()`` returning a dict suitable for
inclusion in PIPELINE-MANIFEST.json as a background step.

Constraints
~~~~~~~~~~~
- stdlib + PyYAML only (no external deps, no network at import).
- Every function is DETERMINISTIC and side-effect-isolated (except lock I/O).
- Hook failure never blocks dream execution.

Version: 1.0.0
Date: 2026-04-01
Story: MCE21-3.1 -- Dream Task (Proactive Background Agent)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from engine.intelligence.pipeline.mce.context_compactor import CircuitBreaker
from engine.intelligence.pipeline.mce.cost_tracker import BudgetCheck, CostTracker

logger = logging.getLogger("mce.dream_task")


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class DreamResult:
    """Result of a dream task execution or skip.

    Attributes:
        triggered_by: Which trigger caused the dream ("time_gate",
                      "session_gate", "manual", or "scheduled").
        duration_ms: Wall-clock time of dream execution in milliseconds.
                     Zero if skipped.
        memories_consolidated: Number of memory fragments consolidated.
                               Zero if skipped.
        cost_usd: Estimated cost of the dream execution in USD.
                  Zero if skipped.
        skipped_reason: If the dream was skipped, explains why.
                        None if the dream executed successfully.
        success: True if the dream completed without error.
        timestamp: ISO 8601 timestamp of when the dream ran (or was skipped).
    """

    triggered_by: str = "unknown"
    duration_ms: float = 0.0
    memories_consolidated: int = 0
    cost_usd: float = 0.0
    skipped_reason: str | None = None
    success: bool = False
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()

    @property
    def was_skipped(self) -> bool:
        """True if the dream was skipped rather than executed."""
        return self.skipped_reason is not None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for manifest/observability."""
        return {
            "triggered_by": self.triggered_by,
            "duration_ms": round(self.duration_ms, 1),
            "memories_consolidated": self.memories_consolidated,
            "cost_usd": round(self.cost_usd, 6),
            "skipped_reason": self.skipped_reason,
            "success": self.success,
            "timestamp": self.timestamp,
            "was_skipped": self.was_skipped,
        }


@dataclass
class DreamConfig:
    """Configuration for the DreamTask, loaded via config cascade.

    Attributes:
        enabled: Master toggle.  False = dream never runs.
        time_gate_hours: Minimum hours since last dream.
        session_gate_count: Minimum sessions since last dream.
        max_budget_usd: Max cost per dream execution.
        lock_file: Lock file name (relative to slug state dir).
        circuit_breaker_max_failures: Consecutive failures before breaker opens.
    """

    enabled: bool = False
    time_gate_hours: int = 24
    session_gate_count: int = 5
    max_budget_usd: float = 0.50
    lock_file: str = ".dream.lock"
    circuit_breaker_max_failures: int = 3

    @classmethod
    def from_config_cascade(cls, config: Any) -> DreamConfig:
        """Build DreamConfig from a CascadeConfig instance.

        Reads dream_* keys from the cascade.  Missing keys fall back to
        the class defaults (which match dream_config.yaml).

        Args:
            config: A CascadeConfig instance (or any object with .get(key, default)).

        Returns:
            DreamConfig populated from the cascade.
        """
        return cls(
            enabled=_as_bool(config.get("dream_enabled", False)),
            time_gate_hours=_as_int(config.get("dream_time_gate_hours", 24)),
            session_gate_count=_as_int(config.get("dream_session_gate_count", 5)),
            max_budget_usd=_as_float(config.get("dream_max_budget_usd", 0.50)),
            lock_file=str(config.get("dream_lock_file", ".dream.lock")),
            circuit_breaker_max_failures=_as_int(
                config.get("dream_circuit_breaker_max_failures", 3)
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize for observability."""
        return {
            "enabled": self.enabled,
            "time_gate_hours": self.time_gate_hours,
            "session_gate_count": self.session_gate_count,
            "max_budget_usd": self.max_budget_usd,
            "lock_file": self.lock_file,
            "circuit_breaker_max_failures": self.circuit_breaker_max_failures,
        }


# ---------------------------------------------------------------------------
# DreamTask
# ---------------------------------------------------------------------------


class DreamTask:
    """Proactive background agent for session memory consolidation.

    Checks three trigger gates (time, session, lock), validates budget,
    and runs a background consolidation pass.  Uses CircuitBreaker to
    stop after N consecutive failures.

    Args:
        slug: Persona slug (e.g. ``"alex-hormozi"``).
        config: DreamConfig instance (or built from CascadeConfig).
        cost_tracker: CostTracker for budget checking.
        hook_bus: Optional HookBus for emitting dream events.
        state_dir: Override for the state directory.  If None, derives
                   from the standard MCE state path.
    """

    def __init__(
        self,
        slug: str,
        config: DreamConfig | None = None,
        cost_tracker: CostTracker | None = None,
        hook_bus: object | None = None,
        state_dir: Path | None = None,
    ) -> None:
        self.slug = slug
        self.config = config or DreamConfig()
        self._cost_tracker = cost_tracker or CostTracker()
        self._hook_bus = hook_bus
        self._circuit_breaker = CircuitBreaker(
            max_failures=self.config.circuit_breaker_max_failures,
        )

        # Resolve state directory
        if state_dir is not None:
            self._state_dir = state_dir
        else:
            self._state_dir = self._default_state_dir(slug)

        # Dream state file tracks last run metadata
        self._dream_state_path = self._state_dir / "dream_state.yaml"
        self._lock_path = self._state_dir / self.config.lock_file

        # Load last dream state from disk
        self._last_run: dict[str, Any] = self._load_dream_state()

        # History of dream results this session
        self._history: list[DreamResult] = []

    # -- Trigger Gates -------------------------------------------------------

    def check_triggers(self) -> bool:
        """Evaluate all 3 trigger gates.

        Returns True only if ALL gates pass:
        1. time_gate   -- enough time since last dream
        2. session_gate -- enough sessions since last dream
        3. lock_check   -- no concurrent dream running

        Returns:
            True if all gates pass and a dream should run.
        """
        if not self.config.enabled:
            logger.debug("DreamTask disabled by config for %s", self.slug)
            return False

        time_ok = self._check_time_gate()
        session_ok = self._check_session_gate()
        lock_ok = self._check_lock()

        all_pass = time_ok and session_ok and lock_ok

        logger.info(
            "DreamTask triggers for %s: time=%s session=%s lock=%s -> %s",
            self.slug,
            time_ok,
            session_ok,
            lock_ok,
            "PASS" if all_pass else "FAIL",
        )

        return all_pass

    def _check_time_gate(self) -> bool:
        """Gate 1: Has enough time elapsed since last dream?"""
        last_ts = self._last_run.get("last_run_timestamp")
        if last_ts is None:
            # Never ran before -- gate passes
            return True

        try:
            last_dt = datetime.fromisoformat(str(last_ts))
            now = datetime.now(UTC)
            # Make last_dt timezone-aware if it is not already
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=UTC)
            hours_elapsed = (now - last_dt).total_seconds() / 3600.0
            return hours_elapsed >= self.config.time_gate_hours
        except (ValueError, TypeError) as exc:
            logger.warning("Invalid last_run_timestamp %r: %s", last_ts, exc)
            return True  # Graceful: if state is corrupt, allow the dream

    def _check_session_gate(self) -> bool:
        """Gate 2: Have enough sessions elapsed since last dream?"""
        sessions_since = self._last_run.get("sessions_since_last_dream", 0)
        try:
            count = int(sessions_since)
        except (ValueError, TypeError):
            count = 0
        return count >= self.config.session_gate_count

    def _check_lock(self) -> bool:
        """Gate 3: Is no other dream currently running (lock file absent)?"""
        if self._lock_path.exists():
            logger.debug("Dream lock file exists at %s", self._lock_path)
            return False
        return True

    # -- Budget Check --------------------------------------------------------

    def check_budget(self, budget_usd: float | None = None) -> BudgetCheck:
        """Check if budget allows a dream execution.

        Args:
            budget_usd: Budget limit.  If None, uses config.max_budget_usd.

        Returns:
            BudgetCheck from cost_tracker.
        """
        limit = budget_usd if budget_usd is not None else self.config.max_budget_usd
        return self._cost_tracker.check_budget(limit)

    # -- Execute -------------------------------------------------------------

    def execute(self, slug: str | None = None) -> DreamResult:
        """Execute the dream task for a given slug.

        Full execution flow:
        1. Check if enabled
        2. Check triggers (time, session, lock)
        3. Check budget
        4. Check circuit breaker
        5. Acquire lock
        6. Emit on_dream_start
        7. Run consolidation
        8. Release lock
        9. Emit on_dream_complete
        10. Save state

        Args:
            slug: Override slug.  If None, uses the instance slug.

        Returns:
            DreamResult with execution details.
        """
        target_slug = slug or self.slug

        # Gate 0: Enabled check
        if not self.config.enabled:
            result = DreamResult(
                triggered_by="disabled",
                skipped_reason="dream_task disabled in config",
            )
            self._emit_hook("on_dream_skipped", result)
            self._history.append(result)
            return result

        # Gate 1-3: Trigger gates
        if not self.check_triggers():
            reason = self._diagnose_trigger_failure()
            result = DreamResult(
                triggered_by="trigger_check",
                skipped_reason=reason,
            )
            self._emit_hook("on_dream_skipped", result)
            self._history.append(result)
            return result

        # Gate 4: Budget check
        budget = self.check_budget()
        if budget.exceeded:
            result = DreamResult(
                triggered_by="budget_check",
                skipped_reason=(
                    f"budget exceeded: spent ${budget.spent_usd:.4f} "
                    f"of ${budget.budget_usd:.4f} limit"
                ),
            )
            self._emit_hook("on_dream_skipped", result)
            self._history.append(result)
            logger.warning(
                "DreamTask skipped for %s: budget exceeded (spent $%.4f / $%.4f)",
                target_slug,
                budget.spent_usd,
                budget.budget_usd,
            )
            return result

        # Gate 5: Circuit breaker
        if self._circuit_breaker.is_open:
            result = DreamResult(
                triggered_by="circuit_breaker",
                skipped_reason=(
                    f"circuit breaker OPEN after "
                    f"{self._circuit_breaker.failure_count} consecutive failures"
                ),
            )
            self._emit_hook("on_dream_skipped", result)
            self._history.append(result)
            return result

        # All gates passed -- execute the dream
        return self._run_dream(target_slug)

    def _run_dream(self, slug: str) -> DreamResult:
        """Internal: acquire lock, run consolidation, release lock.

        This is the actual execution path after all gates have passed.
        """
        # Acquire lock
        self._acquire_lock()

        # Emit start hook
        self._emit_hook("on_dream_start", {"slug": slug})

        t0 = time.monotonic()
        try:
            # --- Consolidation logic ---
            # The actual memory consolidation is a placeholder that counts
            # fragments in the dream state directory.  In production, this
            # would invoke the context compactor on stored session memories.
            consolidated = self._consolidate_memories(slug)

            duration_ms = (time.monotonic() - t0) * 1000.0

            # Estimate cost (placeholder: proportional to fragments)
            estimated_cost = consolidated * 0.001  # ~$0.001 per fragment

            result = DreamResult(
                triggered_by="scheduled",
                duration_ms=duration_ms,
                memories_consolidated=consolidated,
                cost_usd=estimated_cost,
                skipped_reason=None,
                success=True,
            )

            # Record success on circuit breaker
            self._circuit_breaker.record_success()

            # Accumulate cost
            self._cost_tracker.accumulate(
                step_id="dream_task",
                input_tokens=consolidated * 100,  # rough estimate
                output_tokens=consolidated * 50,
                model="dream-consolidator",
                cost_usd=estimated_cost,
            )

            # Save dream state
            self._save_dream_state(result)

            # Emit complete hook
            self._emit_hook("on_dream_complete", result)

            logger.info(
                "DreamTask completed for %s: %d memories consolidated in %.1fms ($%.4f)",
                slug,
                consolidated,
                duration_ms,
                estimated_cost,
            )

        except Exception as exc:
            duration_ms = (time.monotonic() - t0) * 1000.0

            # Record failure on circuit breaker
            just_opened = self._circuit_breaker.record_failure(exc)

            result = DreamResult(
                triggered_by="scheduled",
                duration_ms=duration_ms,
                skipped_reason=f"execution failed: {exc}",
                success=False,
            )

            if just_opened:
                logger.error(
                    "DreamTask circuit breaker OPEN for %s after %d failures",
                    slug,
                    self._circuit_breaker.failure_count,
                )

            logger.error(
                "DreamTask failed for %s: %s (%.1fms, failures: %d/%d)",
                slug,
                exc,
                duration_ms,
                self._circuit_breaker.failure_count,
                self._circuit_breaker.max_failures,
            )

        finally:
            self._release_lock()

        self._history.append(result)
        return result

    def _consolidate_memories(self, slug: str) -> int:
        """Consolidate session memory fragments for a slug.

        This is a **placeholder implementation** that counts YAML files
        in the state directory as "memory fragments".  The real implementation
        would invoke ContextCompactor on stored session memories.

        Args:
            slug: The persona slug.

        Returns:
            Number of memory fragments consolidated.
        """
        memory_dir = self._state_dir
        if not memory_dir.is_dir():
            return 0

        # Count YAML files as proxy for memory fragments
        fragments = list(memory_dir.glob("*.yaml"))
        # Exclude our own state files from the count
        excluded = {"dream_state.yaml", "pipeline_state.yaml", "config.yaml"}
        real_fragments = [f for f in fragments if f.name not in excluded]

        return len(real_fragments)

    # -- Trigger Diagnosis ---------------------------------------------------

    def _diagnose_trigger_failure(self) -> str:
        """Build a human-readable reason for why triggers failed."""
        reasons: list[str] = []

        if not self._check_time_gate():
            last_ts = self._last_run.get("last_run_timestamp", "unknown")
            reasons.append(
                f"time_gate: last run at {last_ts}, " f"need {self.config.time_gate_hours}h gap"
            )

        if not self._check_session_gate():
            sessions = self._last_run.get("sessions_since_last_dream", 0)
            reasons.append(
                f"session_gate: {sessions} sessions since last dream, "
                f"need {self.config.session_gate_count}"
            )

        if not self._check_lock():
            reasons.append(f"lock_check: lock file exists at {self._lock_path}")

        return "; ".join(reasons) if reasons else "unknown trigger failure"

    # -- Lock Management -----------------------------------------------------

    def _acquire_lock(self) -> None:
        """Create the dream lock file."""
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path.write_text(
            f"locked_at: {datetime.now(UTC).isoformat()}\n"
            f"slug: {self.slug}\n"
            f"pid: {os.getpid()}\n",
            encoding="utf-8",
        )
        logger.debug("Dream lock acquired: %s", self._lock_path)

    def _release_lock(self) -> None:
        """Remove the dream lock file."""
        try:
            if self._lock_path.exists():
                self._lock_path.unlink()
                logger.debug("Dream lock released: %s", self._lock_path)
        except OSError as exc:
            logger.warning("Failed to release dream lock: %s", exc)

    # -- State Persistence ---------------------------------------------------

    def _load_dream_state(self) -> dict[str, Any]:
        """Load dream state from YAML on disk."""
        if not self._dream_state_path.exists():
            return {}
        try:
            text = self._dream_state_path.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
            return data if isinstance(data, dict) else {}
        except (yaml.YAMLError, OSError) as exc:
            logger.warning("Failed to load dream state for %s: %s", self.slug, exc)
            return {}

    def _save_dream_state(self, result: DreamResult) -> None:
        """Persist dream state to YAML."""
        self._dream_state_path.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "slug": self.slug,
            "last_run_timestamp": result.timestamp,
            "last_result": result.to_dict(),
            "sessions_since_last_dream": 0,  # Reset after dream
            "total_dreams_run": self._last_run.get("total_dreams_run", 0) + 1,
            "updated_at": datetime.now(UTC).isoformat(),
        }

        try:
            self._dream_state_path.write_text(
                yaml.dump(state, default_flow_style=False, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            self._last_run = state
        except OSError as exc:
            logger.error("Failed to save dream state for %s: %s", self.slug, exc)

    # -- Hook Emission -------------------------------------------------------

    def _emit_hook(self, event: str, data: Any) -> None:
        """Emit a dream hook event via the HookBus.

        Dream events (on_dream_start, on_dream_complete, on_dream_skipped)
        are NOT in the canonical HookEvent enum.  We use a safe wrapper
        that duck-types: any bus with emit(event, payload) works.

        Fire-and-forget -- hook failure never blocks dream execution.
        """
        if self._hook_bus is None:
            return

        payload: dict[str, Any] = {
            "event": event,
            "slug": self.slug,
        }

        if isinstance(data, DreamResult):
            payload["result"] = data.to_dict()
        elif isinstance(data, dict):
            payload.update(data)

        try:
            # Use emit() which fires in a daemon thread (non-blocking).
            # For dream-specific events not in HookEvent, the bus will
            # reject them via _normalize_event.  We catch that gracefully.
            self._hook_bus.emit(event, payload)
        except (ValueError, AttributeError, TypeError) as exc:
            # ValueError: unknown event (not in HookEvent enum)
            # AttributeError: bus has no emit method
            # TypeError: wrong signature
            logger.debug(
                "Dream hook '%s' not emitted (expected for non-canonical events): %s",
                event,
                exc,
            )
        except Exception as exc:
            logger.error("Failed to emit dream hook '%s': %s", event, exc)

    # -- Pipeline Manifest Integration ---------------------------------------

    def manifest_entry(self) -> dict[str, Any]:
        """Return a dict suitable for inclusion in PIPELINE-MANIFEST.json.

        This makes the dream task visible as a background step in the
        pipeline audit renderer.
        """
        last_result = self._last_run.get("last_result", {})

        return {
            "step_id": "dream_task",
            "step_type": "background",
            "name": "Dream Task -- Memory Consolidation",
            "description": "Proactive background agent that consolidates session memory during idle time",
            "enabled": self.config.enabled,
            "config": self.config.to_dict(),
            "circuit_breaker": self._circuit_breaker.to_dict(),
            "last_result": last_result,
            "total_dreams_run": self._last_run.get("total_dreams_run", 0),
        }

    # -- Session Counter -----------------------------------------------------

    def increment_session_counter(self) -> int:
        """Increment the sessions_since_last_dream counter.

        Call this at the start of each new pipeline session so the
        session_gate knows when enough sessions have accumulated.

        Returns:
            New session count.
        """
        count = self._last_run.get("sessions_since_last_dream", 0)
        try:
            count = int(count) + 1
        except (ValueError, TypeError):
            count = 1

        self._last_run["sessions_since_last_dream"] = count

        # Persist the updated count
        if self._dream_state_path.parent.exists():
            self._last_run["updated_at"] = datetime.now(UTC).isoformat()
            try:
                self._dream_state_path.write_text(
                    yaml.dump(
                        self._last_run,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                    ),
                    encoding="utf-8",
                )
            except OSError as exc:
                logger.warning("Failed to persist session counter: %s", exc)

        return count

    # -- Introspection -------------------------------------------------------

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        """The circuit breaker instance for this dream task."""
        return self._circuit_breaker

    @property
    def history(self) -> list[DreamResult]:
        """Dream execution history for this session."""
        return list(self._history)

    @property
    def last_run(self) -> dict[str, Any]:
        """Last dream run state (loaded from disk)."""
        return dict(self._last_run)

    def __repr__(self) -> str:
        return (
            f"DreamTask(slug={self.slug!r}, "
            f"enabled={self.config.enabled}, "
            f"breaker_open={self._circuit_breaker.is_open})"
        )

    # -- Static helpers ------------------------------------------------------

    @staticmethod
    def _default_state_dir(slug: str) -> Path:
        """Derive the default state directory for a slug.

        Reuses the same path convention as state_machine.py.
        """
        try:
            from engine.paths import ROUTING

            base: Path = ROUTING.get("mce_state", Path(".claude/mission-control/mce"))
        except ImportError:
            _root = Path(__file__).resolve().parent.parent.parent.parent.parent
            base = _root / ".claude" / "mission-control" / "mce"
        return Path(base) / slug


# ---------------------------------------------------------------------------
# Value coercion helpers (match config_cascade.py style)
# ---------------------------------------------------------------------------


def _as_bool(value: Any) -> bool:
    """Coerce a value to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower().strip() in ("true", "1", "yes")
    return bool(value)


def _as_int(value: Any) -> int:
    """Coerce a value to int with fallback."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _as_float(value: Any) -> float:
    """Coerce a value to float with fallback."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0
