"""
dag_executor.py -- DAG-Driven Step Executor for MCE Pipeline
=============================================================

Executes pipeline steps according to the DAG dependency graph.
Supports both parallel execution (via asyncio.gather when the PARALLEL
feature gate is enabled) and sequential fallback (v1 behavior).

Architecture
------------
::

    DAGExecutor
      |-- execute_all(step_runner)      # DAG-driven execution loop
      |-- execute_sequential(step_runner) # v1 fallback (topo order)
      |
      v
    DAGEngine          # dependency resolution
    HookBus            # on_parallel_group_start/complete events
    FeatureGates       # PARALLEL gate check
    Semaphore          # concurrency cap (max_parallel from CascadeConfig)

The step_runner callable receives a step_id (str) and returns a dict
with step results.  The executor does not know or care what each step
does internally -- it only orchestrates the execution order.

Design Decisions
~~~~~~~~~~~~~~~~
- execute_all() is async because parallel execution requires asyncio.gather.
  Sequential fallback wraps sync calls in asyncio to maintain the same
  interface.
- The executor does NOT import orchestrate.py step functions directly.
  Instead, the caller passes a step_runner callable.  This keeps the
  dependency arrow one-way: orchestrate -> dag_executor, never the reverse.
- Hook emissions (on_parallel_group_start/complete) are fire-and-forget
  via the HookBus non-blocking emit().
- max_parallel (default 3, from CascadeConfig/defaults.yaml) controls the
  asyncio.Semaphore that caps how many steps can run simultaneously.  When
  max_parallel=1, parallel groups execute sequentially one at a time.
- Parallel group timing: wall-clock and sum-of-individual times are tracked
  so callers can measure the actual speedup from parallelism.
- Error isolation: if one parallel step fails, others continue to completion.
  Errors are collected and surfaced in the result dict, never cancel siblings.

Constraints
~~~~~~~~~~~
- stdlib + asyncio only (no external deps).
- The step_runner can be sync or async -- the executor wraps sync
  functions in asyncio.to_thread() for parallel mode.
- Thread-safe: DAGEngine.mark_completed() is the only mutation.

Version: 2.0.0
Date: 2026-04-01
Story: MCE2-3.2 -- Parallel Execution Queue (hardening + semaphore)
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import TYPE_CHECKING, Any, Callable

from engine.intelligence.pipeline.mce.dag import DAGEngine
from engine.intelligence.pipeline.mce.feature_gates import FeatureGates
from engine.intelligence.pipeline.mce.hook_bus import HookBus
from engine.intelligence.pipeline.mce.step_plugin import StepPlugin
from engine.intelligence.pipeline.mce.streaming_runner import StreamingStepRunner

if TYPE_CHECKING:
    from engine.intelligence.pipeline.mce.policy_limits import PolicyDecision, PolicyLimiter

logger = logging.getLogger("mce.dag_executor")

# Default concurrency cap when no CascadeConfig is provided.
_DEFAULT_MAX_PARALLEL = 3

# Type alias for step runner callables
StepRunner = Callable[[str], dict[str, Any]]
AsyncStepRunner = Callable[[str], Any]  # returns Awaitable[dict]


class DAGExecutor:
    """Executes pipeline steps according to DAG dependency order.

    The executor queries the DAGEngine for ready steps, checks the
    PARALLEL feature gate, and dispatches steps either in parallel
    (asyncio.gather) or sequentially.

    Concurrency is capped by an asyncio.Semaphore whose limit is
    ``max_parallel`` (from CascadeConfig, default 3).

    Args:
        dag: DAGEngine instance with the dependency graph.
        hook_bus: HookBus for emitting parallel group events.
        feature_gates: FeatureGates for checking the PARALLEL gate.
        max_parallel: Maximum concurrent steps in a parallel group.
            Resolved from CascadeConfig or defaults to 3.  Setting
            max_parallel=1 forces all parallel groups to run
            sequentially (one step at a time within the group).
        streaming_runner: Optional StreamingStepRunner for LLM-type steps.
            When provided and the STREAMING feature gate is enabled,
            LLM steps use streaming execution instead of batch.
            Steps are identified as LLM-type via the ``llm_steps`` set.
        llm_steps: Set of step_ids that are LLM-type steps.  When
            streaming_runner is provided, these steps use streaming
            execution.  If None, no steps are treated as LLM-type.
        step_plugins: Optional dict mapping step_id -> StepPlugin instance.
            When provided, the executor reads ``is_concurrency_safe``
            from each plugin to decide scheduling strategy:
            - Safe steps: eligible for asyncio.gather (parallel).
            - Unsafe steps: run serially with exclusive write lock.
            When not provided, all steps are assumed safe (backward
            compatible with pre-MCE21 behavior).
        policy_limiter: Optional PolicyLimiter instance.  When provided,
            each step is checked against the policy before execution.
            Steps denied by policy are skipped with a ``policy_denied``
            result and an ``on_policy_denied`` hook emission.  When not
            provided, all steps execute without policy checks (backward
            compatible).

    Example::

        dag = DAGEngine(dependencies)
        executor = DAGExecutor(dag, hook_bus, feature_gates, max_parallel=3)

        async def run_step(step_id: str) -> dict:
            # ... execute the step ...
            return {"step": step_id, "success": True}

        results = await executor.execute_all(run_step)
    """

    def __init__(
        self,
        dag: DAGEngine,
        hook_bus: HookBus,
        feature_gates: FeatureGates,
        max_parallel: int = _DEFAULT_MAX_PARALLEL,
        streaming_runner: StreamingStepRunner | None = None,
        llm_steps: set[str] | None = None,
        step_plugins: dict[str, StepPlugin] | None = None,
        policy_limiter: PolicyLimiter | None = None,
    ) -> None:
        self._dag = dag
        self._hook_bus = hook_bus
        self._gates = feature_gates
        self._max_parallel = max(1, max_parallel)
        self._streaming_runner = streaming_runner
        self._llm_steps = llm_steps or set()
        self._step_plugins = step_plugins or {}
        self._policy_limiter = policy_limiter
        self._parallel_group_timings: list[dict[str, Any]] = []
        self._policy_denied_steps: list[str] = []
        # Exclusive lock for concurrency-unsafe (write) steps.
        # Initialized lazily per execute_all() call (one lock per run).
        self._write_lock: asyncio.Lock | None = None

    # -- Concurrency safety helpers (MCE21-1.2) ------------------------------

    def _is_step_safe(self, step_id: str) -> bool:
        """Check if a step is safe for concurrent execution.

        Looks up the StepPlugin instance in the step_plugins registry
        and reads its ``is_concurrency_safe`` property.  When no plugin
        is registered for the step_id, defaults to True (backward
        compatible -- assumes safe).

        Args:
            step_id: The step to check.

        Returns:
            True if the step can run concurrently, False if it needs
            exclusive (serial) execution.
        """
        plugin = self._step_plugins.get(step_id)
        if plugin is None:
            return True  # Backward compat: unknown steps assumed safe
        return plugin.is_concurrency_safe

    def _partition_by_safety(
        self,
        step_ids: list[str],
    ) -> tuple[list[str], list[str]]:
        """Split steps into concurrency-safe and concurrency-unsafe groups.

        Args:
            step_ids: List of step IDs to partition.

        Returns:
            Tuple of (safe_steps, unsafe_steps).
        """
        safe: list[str] = []
        unsafe: list[str] = []
        for sid in step_ids:
            if self._is_step_safe(sid):
                safe.append(sid)
            else:
                unsafe.append(sid)
        return safe, unsafe

    # -- Policy check helper (MCE21-1.1) ------------------------------------

    def _check_policy(
        self,
        step_id: str,
        action: str = "execute",
        *,
        slug: str | None = None,
    ) -> PolicyDecision | None:
        """Check if a step is allowed by the policy limiter.

        Returns None when no policy limiter is configured (backward
        compatible -- all steps allowed).  Returns a PolicyDecision
        when a limiter is present.

        Args:
            step_id: Step to check.
            action: Action to check (default "execute").
            slug: Optional persona slug for per-slug overrides.

        Returns:
            PolicyDecision or None if no limiter configured.
        """
        if self._policy_limiter is None:
            return None
        return self._policy_limiter.check(step_id, action, slug=slug)

    def _apply_policy_filter(
        self,
        step_ids: list[str],
        results: dict[str, dict[str, Any]],
        execution_order: list[str],
        *,
        slug: str | None = None,
    ) -> list[str]:
        """Filter step_ids through the policy limiter.

        Steps denied by policy are immediately marked completed in the
        DAG with a policy_denied result.  Only allowed steps are returned.

        Args:
            step_ids: Steps to filter.
            results: Results dict to populate for denied steps.
            execution_order: Execution order list to append denied steps.
            slug: Optional persona slug for per-slug overrides.

        Returns:
            List of step_ids that passed the policy check.
        """
        if self._policy_limiter is None:
            return step_ids

        allowed: list[str] = []
        for sid in step_ids:
            decision = self._check_policy(sid, "execute", slug=slug)
            if decision is not None and not decision.allowed:
                logger.warning(
                    "Step '%s' denied by policy: %s",
                    sid,
                    decision.reason,
                )
                results[sid] = {
                    "step": sid,
                    "success": False,
                    "policy_denied": True,
                    "reason": decision.reason,
                }
                self._dag.mark_completed(sid)
                execution_order.append(sid)
                self._policy_denied_steps.append(sid)
            else:
                allowed.append(sid)

        return allowed

    # -- Main Execution Loop ------------------------------------------------

    async def execute_all(
        self,
        step_runner: StepRunner | AsyncStepRunner,
    ) -> dict[str, Any]:
        """Execute all steps following DAG dependency order.

        For each iteration:
        1. Ask DAG for ready steps (all deps satisfied, not yet completed).
        2. If PARALLEL gate is enabled and multiple steps are ready:
           - Emit on_parallel_group_start hook.
           - Run steps concurrently via asyncio.gather, capped by
             max_parallel semaphore.
           - Track wall-clock vs sum-of-individual timing.
           - Emit on_parallel_group_complete hook (with timing data).
        3. Otherwise: run ready steps sequentially.
        4. Mark completed steps in the DAG.
        5. Repeat until all steps are done.

        Args:
            step_runner: Callable that takes a step_id (str) and returns
                         a dict with step results.  Can be sync or async.

        Returns:
            Dict with:
            - results: dict mapping step_id -> step result dict
            - execution_order: list of step_ids in actual execution order
            - parallel_groups_executed: count of parallel group dispatches
            - parallel_group_timings: list of timing dicts per group
            - total_duration_ms: wall-clock time for all steps
        """
        t0 = time.monotonic()
        results: dict[str, dict[str, Any]] = {}
        execution_order: list[str] = []
        parallel_groups_executed = 0
        is_parallel = self._gates.gate("parallel")
        self._parallel_group_timings = []

        runner = self._wrap_runner(step_runner)
        semaphore = asyncio.Semaphore(self._max_parallel)
        # One write lock per execution run for concurrency-unsafe steps.
        self._write_lock = asyncio.Lock()
        # Reset policy state for new run
        self._policy_denied_steps = []
        if self._policy_limiter is not None:
            self._policy_limiter.reset_call_counts()

        while not self._dag.is_complete():
            ready = self._dag.get_ready_steps()

            if not ready:
                # Safety: if no steps are ready but DAG is not complete,
                # something is wrong (should not happen with valid DAG)
                remaining = self._dag.remaining
                logger.error(
                    "DAG deadlock: no ready steps but %d remaining: %s",
                    len(remaining),
                    remaining,
                )
                break

            # Policy filter: remove steps denied by policy (MCE21-1.1)
            ready = self._apply_policy_filter(
                ready,
                results,
                execution_order,
            )

            if not ready:
                # All ready steps were denied by policy -- continue to
                # let the DAG find next batch.
                continue

            if is_parallel and len(ready) > 1:
                # Partition ready steps by concurrency safety (MCE21-1.2).
                # Safe steps run via asyncio.gather (parallel).
                # Unsafe steps run serially with exclusive write lock.
                safe_steps, unsafe_steps = self._partition_by_safety(ready)

                if unsafe_steps:
                    logger.info(
                        "Concurrency partition: safe=%s, unsafe=%s",
                        safe_steps,
                        unsafe_steps,
                    )

                # Parallel execution for safe steps (with semaphore cap)
                parallel_groups_executed += 1

                self._hook_bus.emit(
                    "on_parallel_group_start",
                    {
                        "steps": ready,
                        "safe_steps": safe_steps,
                        "unsafe_steps": unsafe_steps,
                        "group_index": parallel_groups_executed,
                        "max_parallel": self._max_parallel,
                    },
                )

                logger.info(
                    "Executing parallel group #%d: %s (max_parallel=%d, safe=%d, unsafe=%d)",
                    parallel_groups_executed,
                    ready,
                    self._max_parallel,
                    len(safe_steps),
                    len(unsafe_steps),
                )

                # Track individual step durations for timing analysis
                step_durations: dict[str, float] = {}

                async def _run_with_semaphore(
                    sid: str,
                    durations: dict[str, float],
                ) -> dict[str, Any]:
                    """Run a step behind the semaphore and record its duration."""
                    async with semaphore:
                        step_t0 = time.monotonic()
                        try:
                            res = await runner(sid)
                        except Exception as exc:
                            dur = (time.monotonic() - step_t0) * 1000
                            durations[sid] = dur
                            raise exc
                        dur = (time.monotonic() - step_t0) * 1000
                        durations[sid] = dur
                        return res

                # Wall-clock timing for the whole group
                group_t0 = time.monotonic()

                # Phase 1: Run safe steps in parallel via asyncio.gather
                safe_task_results: list[dict[str, Any] | Exception] = []
                if safe_steps:
                    tasks = [_run_with_semaphore(step_id, step_durations) for step_id in safe_steps]
                    safe_task_results = await asyncio.gather(
                        *tasks,
                        return_exceptions=True,
                    )

                # Phase 2: Run unsafe steps serially with exclusive lock
                unsafe_task_results: list[dict[str, Any] | Exception] = []
                for sid in unsafe_steps:
                    assert self._write_lock is not None
                    async with self._write_lock:
                        step_t0 = time.monotonic()
                        try:
                            res = await runner(sid)
                            unsafe_task_results.append(res)
                        except Exception as exc:
                            dur = (time.monotonic() - step_t0) * 1000
                            step_durations[sid] = dur
                            unsafe_task_results.append(exc)
                            continue
                        dur = (time.monotonic() - step_t0) * 1000
                        step_durations[sid] = dur

                group_wall_ms = (time.monotonic() - group_t0) * 1000

                # Process safe results
                for step_id, result in zip(safe_steps, safe_task_results):
                    if isinstance(result, Exception):
                        logger.error(
                            "Step '%s' failed in parallel group: %s",
                            step_id,
                            result,
                        )
                        results[step_id] = {
                            "step": step_id,
                            "success": False,
                            "error": str(result),
                        }
                    else:
                        results[step_id] = result

                    self._dag.mark_completed(step_id)
                    execution_order.append(step_id)

                # Process unsafe results
                for step_id, result in zip(unsafe_steps, unsafe_task_results):
                    if isinstance(result, Exception):
                        logger.error(
                            "Step '%s' (unsafe/serial) failed: %s",
                            step_id,
                            result,
                        )
                        results[step_id] = {
                            "step": step_id,
                            "success": False,
                            "error": str(result),
                        }
                    else:
                        results[step_id] = result

                    self._dag.mark_completed(step_id)
                    execution_order.append(step_id)

                # Compute timing metrics
                sum_individual_ms = sum(step_durations.values())
                timing = {
                    "group_index": parallel_groups_executed,
                    "steps": ready,
                    "safe_steps": safe_steps,
                    "unsafe_steps": unsafe_steps,
                    "wall_clock_ms": round(group_wall_ms, 1),
                    "sum_individual_ms": round(sum_individual_ms, 1),
                    "speedup_ratio": (
                        round(sum_individual_ms / group_wall_ms, 2) if group_wall_ms > 0 else 1.0
                    ),
                    "step_durations_ms": {s: round(step_durations.get(s, 0), 1) for s in ready},
                    "max_parallel": self._max_parallel,
                }
                self._parallel_group_timings.append(timing)

                self._hook_bus.emit(
                    "on_parallel_group_complete",
                    {
                        "steps": ready,
                        "safe_steps": safe_steps,
                        "unsafe_steps": unsafe_steps,
                        "group_index": parallel_groups_executed,
                        "results": {s: results.get(s, {}) for s in ready},
                        "timing": timing,
                    },
                )

            else:
                # Sequential execution (default / PARALLEL=false)
                for step_id in ready:
                    logger.info("Executing step: %s", step_id)
                    try:
                        result = await runner(step_id)
                        results[step_id] = result
                    except Exception as exc:
                        logger.error("Step '%s' failed: %s", step_id, exc)
                        results[step_id] = {
                            "step": step_id,
                            "success": False,
                            "error": str(exc),
                        }
                    self._dag.mark_completed(step_id)
                    execution_order.append(step_id)

        elapsed = (time.monotonic() - t0) * 1000

        return {
            "results": results,
            "execution_order": execution_order,
            "parallel_groups_executed": parallel_groups_executed,
            "parallel_group_timings": list(self._parallel_group_timings),
            "policy_denied_steps": list(self._policy_denied_steps),
            "total_duration_ms": round(elapsed, 1),
            "is_complete": self._dag.is_complete(),
            "dag_summary": self._dag.to_dict(),
        }

    @property
    def max_parallel(self) -> int:
        """Current concurrency cap for parallel groups."""
        return self._max_parallel

    @property
    def parallel_group_timings(self) -> list[dict[str, Any]]:
        """Timing data from the last execute_all() run."""
        return list(self._parallel_group_timings)

    @property
    def policy_denied_steps(self) -> list[str]:
        """Steps denied by policy in the last execution run."""
        return list(self._policy_denied_steps)

    @property
    def has_streaming(self) -> bool:
        """Whether a streaming runner is configured and STREAMING gate is on."""
        return self._streaming_runner is not None and self._gates.gate("streaming")

    # -- Sequential Fallback ------------------------------------------------

    async def execute_sequential(
        self,
        step_runner: StepRunner | AsyncStepRunner,
    ) -> dict[str, Any]:
        """Execute all steps in strict topological order (v1 fallback).

        Ignores the PARALLEL feature gate entirely.  Steps are executed
        one at a time in the topological sort order.

        Args:
            step_runner: Callable that takes a step_id and returns a result dict.

        Returns:
            Same structure as execute_all().
        """
        t0 = time.monotonic()
        results: dict[str, dict[str, Any]] = {}
        execution_order: list[str] = []

        runner = self._wrap_runner(step_runner)

        # Reset policy state for new run
        self._policy_denied_steps = []
        if self._policy_limiter is not None:
            self._policy_limiter.reset_call_counts()

        for step_id in self._dag.topological_sort():
            # Policy check before execution (MCE21-1.1)
            decision = self._check_policy(step_id, "execute")
            if decision is not None and not decision.allowed:
                logger.warning(
                    "Step '%s' denied by policy (sequential): %s",
                    step_id,
                    decision.reason,
                )
                results[step_id] = {
                    "step": step_id,
                    "success": False,
                    "policy_denied": True,
                    "reason": decision.reason,
                }
                self._dag.mark_completed(step_id)
                execution_order.append(step_id)
                self._policy_denied_steps.append(step_id)
                continue

            logger.info("Executing step (sequential): %s", step_id)
            try:
                result = await runner(step_id)
                results[step_id] = result
            except Exception as exc:
                logger.error("Step '%s' failed: %s", step_id, exc)
                results[step_id] = {
                    "step": step_id,
                    "success": False,
                    "error": str(exc),
                }
            self._dag.mark_completed(step_id)
            execution_order.append(step_id)

        elapsed = (time.monotonic() - t0) * 1000

        return {
            "results": results,
            "execution_order": execution_order,
            "parallel_groups_executed": 0,
            "policy_denied_steps": list(self._policy_denied_steps),
            "total_duration_ms": round(elapsed, 1),
            "is_complete": self._dag.is_complete(),
            "dag_summary": self._dag.to_dict(),
        }

    # -- Helpers ------------------------------------------------------------

    @staticmethod
    def _wrap_runner(
        step_runner: StepRunner | AsyncStepRunner,
    ) -> AsyncStepRunner:
        """Wrap a sync step_runner into an async one if needed.

        If the runner is already async (a coroutine function), return as-is.
        If sync, wrap in asyncio.to_thread() so it can participate in
        asyncio.gather() for parallel execution.
        """
        if inspect.iscoroutinefunction(step_runner):
            return step_runner

        async def async_wrapper(step_id: str) -> dict[str, Any]:
            return await asyncio.to_thread(step_runner, step_id)

        return async_wrapper
