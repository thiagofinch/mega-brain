"""
cost_tracker.py -- Comprehensive LLM Cost Tracker for MCE Pipeline
==================================================================

Formalizes cost tracking with per-step breakdown, budget checking,
and manifest-ready export.  Extends the concept from ``metrics.py``
(wall-clock timing) into the cost/token dimension.

Architecture
------------
CostTracker can operate in two modes:

1. **Standalone with context manager** -- wraps pipeline steps and
   captures tokens/cost automatically via an ``LLMProvider``.

2. **Manual accumulation** -- receives token counts directly (e.g.
   from ``CostHook`` entries or external sources).

Both modes feed the same internal accumulator.  A ``from_cost_hook()``
class method bridges CostHook (MCE2-1.9) data into the tracker.

::

    cost_tracker.py  -->  llm_provider.py  (for get_cost / model_name)
    cost_tracker.py  <--  cost_hook.py     (optional, via from_cost_hook)

Data Classes
------------
- ``StepCost``     -- per-step token/cost summary
- ``PipelineCost`` -- total pipeline cost with breakdowns
- ``BudgetCheck``  -- budget compliance result

Public API
----------
- ``CostTracker(provider=None)`` -- construct tracker
- ``track(step_id)``            -- context manager for automatic capture
- ``accumulate(step_id, ...)``  -- manual token/cost entry
- ``get_step_cost(step_id)``    -- StepCost for one step
- ``get_total_cost()``          -- PipelineCost with full breakdown
- ``check_budget(budget_usd)``  -- BudgetCheck result
- ``export_report()``           -- dict for pipeline manifest
- ``from_cost_hook(hook)``      -- import CostHook data into tracker

Constraints
~~~~~~~~~~~
- stdlib + typing only (no new external deps).
- Thread-safe via threading.Lock on the accumulator.
- DETERMINISTIC: same inputs always produce same outputs.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-3.4 -- Cost Tracker
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator

from engine.intelligence.pipeline.mce.llm_provider import (
    _FALLBACK_PRICE,
    PRICE_TABLE,
    LLMProvider,
)

logger = logging.getLogger("mce.cost_tracker")


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class StepCost:
    """Per-step cost summary.

    Aggregates all LLM calls within a single pipeline step.

    Attributes:
        step_id: Pipeline step identifier.
        input_tokens: Total input tokens across all calls in this step.
        output_tokens: Total output tokens across all calls in this step.
        total_tokens: Sum of input + output tokens.
        cost_usd: Total cost in USD for this step.
        calls: Number of LLM calls made in this step.
        avg_latency_ms: Average wall-clock latency per call in milliseconds.
    """

    step_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    calls: int = 0
    avg_latency_ms: float = 0.0


@dataclass
class PipelineCost:
    """Total pipeline cost with breakdowns by step and model.

    Attributes:
        total_tokens: Sum of all tokens across all steps.
        total_cost_usd: Total cost in USD across all steps.
        cost_by_step: Mapping of step_id to cost in USD.
        cost_by_model: Mapping of model name to cost in USD.
        total_calls: Total number of LLM calls across all steps.
    """

    total_tokens: int = 0
    total_cost_usd: float = 0.0
    cost_by_step: dict[str, float] = field(default_factory=dict)
    cost_by_model: dict[str, float] = field(default_factory=dict)
    total_calls: int = 0


@dataclass
class BudgetCheck:
    """Budget compliance result.

    Attributes:
        budget_usd: The budget limit checked against.
        spent_usd: Actual amount spent so far.
        remaining_usd: Budget remaining (can be negative if exceeded).
        exceeded: True if spent > budget.
        utilization_pct: Percentage of budget used (0-100+).
        top_steps: Steps sorted by cost descending (for optimization hints).
    """

    budget_usd: float = 0.0
    spent_usd: float = 0.0
    remaining_usd: float = 0.0
    exceeded: bool = False
    utilization_pct: float = 0.0
    top_steps: list[tuple[str, float]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal entry type
# ---------------------------------------------------------------------------


@dataclass
class _CostEntry:
    """Internal accumulator entry for a single LLM call."""

    step_id: str
    input_tokens: int
    output_tokens: int
    model: str
    cost_usd: float
    latency_ms: float
    timestamp: float


# ---------------------------------------------------------------------------
# CostTracker
# ---------------------------------------------------------------------------


class CostTracker:
    """Comprehensive cost tracker for LLM usage in the MCE pipeline.

    Tracks tokens, cost, and latency per step.  Supports both automatic
    capture via context manager and manual accumulation.

    Thread-safe: concurrent calls to ``accumulate()`` and ``track()``
    are serialized via an internal lock.

    Args:
        provider: Optional LLMProvider for cost calculation.
                  If None, uses the shared PRICE_TABLE directly.
    """

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self._provider = provider
        self._entries: list[_CostEntry] = []
        self._lock = threading.Lock()
        logger.info(
            "CostTracker initialized: provider=%s",
            type(provider).__name__ if provider else "None (manual mode)",
        )

    # ------------------------------------------------------------------
    # Context Manager -- automatic token/cost capture
    # ------------------------------------------------------------------

    @contextmanager
    def track(self, step_id: str) -> Generator[_CostEntry, None, None]:
        """Context manager that measures tokens/cost for a code block.

        Yields a ``_CostEntry`` placeholder that gets populated with
        latency data on exit.  Token and cost data must be fed via
        ``accumulate()`` calls within the block, or by using the
        provider integration.

        Usage::

            with tracker.track("chunking") as t:
                result = do_work()
                tracker.accumulate("chunking", 500, 100, "gemini-2.0-flash")
            # t.latency_ms is now set

        Args:
            step_id: Pipeline step identifier.

        Yields:
            A _CostEntry placeholder with timing data.
        """
        entry = _CostEntry(
            step_id=step_id,
            input_tokens=0,
            output_tokens=0,
            model="",
            cost_usd=0.0,
            latency_ms=0.0,
            timestamp=time.time(),
        )

        start = time.monotonic()
        try:
            yield entry
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000.0
            entry.latency_ms = elapsed_ms
            logger.debug(
                "track(%s) completed: %.1fms",
                step_id,
                elapsed_ms,
            )

    # ------------------------------------------------------------------
    # Manual Accumulation
    # ------------------------------------------------------------------

    def accumulate(
        self,
        step_id: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
        cost_usd: float | None = None,
        latency_ms: float = 0.0,
    ) -> None:
        """Manually accumulate token/cost data for a step.

        If ``cost_usd`` is None, calculates cost from the provider
        (if available) or from the shared PRICE_TABLE.

        Args:
            step_id: Pipeline step identifier.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            model: Model identifier (e.g. "gemini-2.0-flash").
            cost_usd: Pre-calculated cost.  If None, auto-calculated.
            latency_ms: Wall-clock latency in milliseconds.
        """
        if cost_usd is None:
            cost_usd = self._calculate_cost(model, input_tokens, output_tokens)

        entry = _CostEntry(
            step_id=step_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            timestamp=time.time(),
        )

        with self._lock:
            self._entries.append(entry)

        logger.debug(
            "Accumulated: step=%s model=%s tokens=%d+%d cost=$%.6f latency=%.1fms",
            step_id,
            model,
            input_tokens,
            output_tokens,
            cost_usd,
            latency_ms,
        )

    # ------------------------------------------------------------------
    # Cost Calculation (internal)
    # ------------------------------------------------------------------

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD using the provider or shared price table.

        If a provider is set and its model matches, delegates to
        ``provider.get_cost()``.  Otherwise uses the shared PRICE_TABLE.

        Args:
            model: Model identifier.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Cost in USD.
        """
        if self._provider is not None:
            return self._provider.get_cost(input_tokens, output_tokens)

        prices = PRICE_TABLE.get(model, _FALLBACK_PRICE)
        input_cost = (input_tokens / 1000.0) * prices["input"]
        output_cost = (output_tokens / 1000.0) * prices["output"]
        return input_cost + output_cost

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get_step_cost(self, step_id: str) -> StepCost:
        """Return cost summary for a single pipeline step.

        Aggregates all entries matching the given step_id.

        Args:
            step_id: The step identifier to query.

        Returns:
            StepCost with aggregated token counts, cost, and latency.
        """
        with self._lock:
            entries = [e for e in self._entries if e.step_id == step_id]

        if not entries:
            return StepCost(step_id=step_id)

        input_tokens = sum(e.input_tokens for e in entries)
        output_tokens = sum(e.output_tokens for e in entries)
        cost_usd = sum(e.cost_usd for e in entries)
        total_latency = sum(e.latency_ms for e in entries)
        calls = len(entries)
        avg_latency = total_latency / calls if calls > 0 else 0.0

        return StepCost(
            step_id=step_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=round(cost_usd, 6),
            calls=calls,
            avg_latency_ms=round(avg_latency, 2),
        )

    def get_total_cost(self) -> PipelineCost:
        """Return total pipeline cost with breakdowns.

        Provides cost aggregated by step and by model, plus
        total token counts and call counts.

        Returns:
            PipelineCost with full breakdown.
        """
        with self._lock:
            entries = list(self._entries)

        if not entries:
            return PipelineCost()

        total_input = sum(e.input_tokens for e in entries)
        total_output = sum(e.output_tokens for e in entries)
        total_cost = sum(e.cost_usd for e in entries)

        cost_by_step: dict[str, float] = {}
        for e in entries:
            cost_by_step[e.step_id] = cost_by_step.get(e.step_id, 0.0) + e.cost_usd

        cost_by_model: dict[str, float] = {}
        for e in entries:
            cost_by_model[e.model] = cost_by_model.get(e.model, 0.0) + e.cost_usd

        return PipelineCost(
            total_tokens=total_input + total_output,
            total_cost_usd=round(total_cost, 6),
            cost_by_step={k: round(v, 6) for k, v in cost_by_step.items()},
            cost_by_model={k: round(v, 6) for k, v in cost_by_model.items()},
            total_calls=len(entries),
        )

    def check_budget(self, budget_usd: float) -> BudgetCheck:
        """Check whether accumulated costs are within a budget.

        Args:
            budget_usd: Budget limit in USD.

        Returns:
            BudgetCheck with utilization details and top-cost steps.
        """
        pipeline_cost = self.get_total_cost()
        spent = pipeline_cost.total_cost_usd
        remaining = budget_usd - spent
        exceeded = spent > budget_usd
        utilization = (spent / budget_usd * 100.0) if budget_usd > 0 else 0.0

        top_steps = sorted(
            pipeline_cost.cost_by_step.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return BudgetCheck(
            budget_usd=budget_usd,
            spent_usd=round(spent, 6),
            remaining_usd=round(remaining, 6),
            exceeded=exceeded,
            utilization_pct=round(utilization, 2),
            top_steps=top_steps,
        )

    def export_report(self) -> dict[str, Any]:
        """Export cost data as a dict suitable for pipeline manifest.

        Returns:
            Dict with keys: total_cost_usd, total_tokens, total_calls,
            cost_by_step, cost_by_model, steps (detailed per-step data).
        """
        pipeline_cost = self.get_total_cost()

        with self._lock:
            step_ids = list({e.step_id for e in self._entries})

        steps_detail: dict[str, dict[str, Any]] = {}
        for sid in step_ids:
            sc = self.get_step_cost(sid)
            steps_detail[sid] = {
                "input_tokens": sc.input_tokens,
                "output_tokens": sc.output_tokens,
                "total_tokens": sc.total_tokens,
                "cost_usd": sc.cost_usd,
                "calls": sc.calls,
                "avg_latency_ms": sc.avg_latency_ms,
            }

        return {
            "total_cost_usd": pipeline_cost.total_cost_usd,
            "total_tokens": pipeline_cost.total_tokens,
            "total_calls": pipeline_cost.total_calls,
            "cost_by_step": pipeline_cost.cost_by_step,
            "cost_by_model": pipeline_cost.cost_by_model,
            "steps": steps_detail,
        }

    # ------------------------------------------------------------------
    # Integration with CostHook (MCE2-1.9)
    # ------------------------------------------------------------------

    @classmethod
    def from_cost_hook(cls, hook: Any) -> CostTracker:
        """Create a CostTracker populated from a CostHook's accumulated data.

        Bridges the raw accumulator (CostHook) into the formal tracker
        with typed dataclasses and query API.

        Args:
            hook: A CostHook instance with ``get_accumulated_costs()``.

        Returns:
            A new CostTracker with all hook entries imported.
        """
        tracker = cls()
        entries = hook.get_accumulated_costs()

        for entry in entries:
            tracker.accumulate(
                step_id=entry.get("step_id", "unknown"),
                input_tokens=entry.get("input_tokens", 0),
                output_tokens=entry.get("output_tokens", 0),
                model=entry.get("model", "unknown"),
                cost_usd=entry.get("cost_usd"),
            )

        logger.info(
            "CostTracker created from CostHook: %d entries imported",
            len(entries),
        )
        return tracker

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear all accumulated entries."""
        with self._lock:
            self._entries.clear()
        logger.debug("CostTracker entries cleared")

    @property
    def entry_count(self) -> int:
        """Return the number of accumulated entries."""
        with self._lock:
            return len(self._entries)

    def __repr__(self) -> str:
        pc = self.get_total_cost()
        return (
            f"CostTracker(entries={self.entry_count}, "
            f"total=${pc.total_cost_usd:.6f}, "
            f"calls={pc.total_calls})"
        )
