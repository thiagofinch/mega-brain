"""
budget_integration.py -- Token Budget Integration for MCE Pipeline
==================================================================

Wires together TokenBudget (enforcement), CostTracker (tracking),
ContextCompactor (compaction when over budget), and HookBus (cost
threshold events) into a single integration layer that the pipeline
orchestrator and DAGExecutor can consume.

Architecture
------------
Uses Mediator Pattern -- coordinates four independent modules into
one unified step-wrapping API.  The orchestrator calls
``wrap_step_execution()`` instead of calling each module directly.

::

    orchestrate.py  -->  BudgetIntegration.wrap_step_execution()
                              |
                              +-->  TokenBudget.enforce()       (pre-step)
                              +-->  CostTracker.track()         (during step)
                              +-->  CostTracker.accumulate()    (after step)
                              +-->  HookBus.emit()              (on threshold)

Public API
----------
- ``BudgetIntegration(config, hook_bus, provider)`` -- construct the integration
- ``wrap_step_execution(step_id, step_fn, chunks, prompt_template, model)``
    -- wrap a pipeline step with budget/cost tracking
- ``get_pipeline_cost_report()`` -- consolidated report for manifest
- ``get_budget_status(budget_usd)`` -- current spend vs budget

Constraints
~~~~~~~~~~~
- stdlib + project modules only (no external deps).
- Never blocks pipeline on hook failure (fire-and-forget).
- Thread-safe: CostTracker uses internal lock.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-3.5 -- Token Budget Integration
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from engine.intelligence.pipeline.mce.budget import TokenBudget
from engine.intelligence.pipeline.mce.config_cascade import CascadeConfig
from engine.intelligence.pipeline.mce.cost_tracker import CostTracker
from engine.intelligence.pipeline.mce.hook_bus import HookBus, HookEvent

logger = logging.getLogger("mce.budget_integration")


# ---------------------------------------------------------------------------
# BudgetIntegration
# ---------------------------------------------------------------------------


class BudgetIntegration:
    """Mediator that wires TokenBudget, CostTracker, and HookBus together.

    Provides a single ``wrap_step_execution()`` method that any pipeline
    step runner can call to get automatic budget enforcement, cost
    tracking, and threshold event emission.

    Args:
        config: CascadeConfig for budget percentage resolution.
        hook_bus: HookBus for emitting cost threshold hooks.
                  If None, hooks are silently skipped.
        provider: Optional LLMProvider for cost calculation.
                  If None, CostTracker uses the shared PRICE_TABLE.
        budget_usd: Optional USD budget limit for the entire pipeline run.
                    When set, cumulative cost checks fire after each step.
    """

    def __init__(
        self,
        config: CascadeConfig,
        hook_bus: HookBus | None = None,
        provider: Any = None,
        budget_usd: float | None = None,
    ) -> None:
        self._config = config
        self._hook_bus = hook_bus
        self._budget_usd = budget_usd

        # Token budget enforcer (handles pre-step budget check + compaction)
        self._token_budget = TokenBudget(config=config, hook_bus=hook_bus)

        # Cost tracker (handles per-step and cumulative cost tracking)
        self._cost_tracker = CostTracker(provider=provider)

        # Running step count for summary
        self._steps_executed: int = 0
        self._steps_compacted: int = 0

        logger.info(
            "BudgetIntegration initialized: budget_usd=%s, hook_bus=%s",
            budget_usd,
            "yes" if hook_bus else "no",
        )

    # ------------------------------------------------------------------
    # Primary API: wrap_step_execution
    # ------------------------------------------------------------------

    def wrap_step_execution(
        self,
        step_id: str,
        step_fn: Callable[..., Any],
        *,
        chunks: list[dict[str, Any]] | None = None,
        prompt_template: str = "",
        model: str | None = None,
    ) -> Any:
        """Wrap a pipeline step with budget enforcement and cost tracking.

        Execution flow:
        1. BEFORE: If chunks provided, enforce token budget (compact if over).
        2. DURING: Execute the step function inside CostTracker.track().
        3. AFTER:  Check cumulative budget, emit hook if threshold exceeded.

        Args:
            step_id: Pipeline step identifier (e.g. "chunking", "enrichment").
            step_fn: Callable that performs the actual step work.
                     Called with no arguments -- the caller should bind
                     any needed args via lambda or functools.partial.
            chunks: Optional list of chunk dicts for pre-step budget check.
                    If None, the pre-step budget enforcement is skipped
                    (useful for steps that don't work with chunks).
            prompt_template: Prompt template used with the chunks.
                             Only relevant when chunks is provided.
            model: Model identifier override.  If None, resolved from config.

        Returns:
            Whatever step_fn returns.
        """
        self._steps_executed += 1
        resolved_model = model or self._config.get("model", "gemini-1.5-pro")

        # --- BEFORE: Pre-step budget enforcement ---
        enforced_chunks = chunks
        if chunks is not None:
            logger.info(
                "Pre-step budget check [step=%s]: %d chunks, model=%s",
                step_id,
                len(chunks),
                resolved_model,
            )
            enforced_chunks = self._token_budget.enforce(
                chunks,
                prompt_template=prompt_template,
                model=resolved_model,
                step_id=step_id,
            )

            # Track whether compaction happened
            if self._chunks_were_compacted(chunks, enforced_chunks):
                self._steps_compacted += 1
                logger.info(
                    "Pre-step compaction triggered [step=%s]",
                    step_id,
                )

        # --- DURING: Execute step with cost tracking ---
        t0 = time.monotonic()
        with self._cost_tracker.track(step_id):
            result = step_fn()
        elapsed_ms = (time.monotonic() - t0) * 1000

        # --- AFTER: Accumulate cost and check cumulative budget ---
        # Extract token usage from the result if available
        input_tokens, output_tokens, step_model = self._extract_usage(result, resolved_model)
        if input_tokens > 0 or output_tokens > 0:
            self._cost_tracker.accumulate(
                step_id=step_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=step_model,
                latency_ms=elapsed_ms,
            )

        # Check cumulative USD budget if configured
        if self._budget_usd is not None:
            self._check_cumulative_budget(step_id)

        logger.info(
            "Step '%s' completed: %.1fms, tokens=%d+%d",
            step_id,
            elapsed_ms,
            input_tokens,
            output_tokens,
        )

        return result

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get_pipeline_cost_report(self) -> dict[str, Any]:
        """Generate a consolidated cost report for the pipeline manifest.

        Returns:
            Dict suitable for embedding in the pipeline manifest under
            a ``cost_report`` key.  Includes per-step breakdown,
            totals, and budget status.
        """
        report = self._cost_tracker.export_report()

        # Add integration-specific metadata
        report["steps_executed"] = self._steps_executed
        report["steps_compacted"] = self._steps_compacted

        if self._budget_usd is not None:
            budget_check = self._cost_tracker.check_budget(self._budget_usd)
            report["budget"] = {
                "budget_usd": budget_check.budget_usd,
                "spent_usd": budget_check.spent_usd,
                "remaining_usd": budget_check.remaining_usd,
                "exceeded": budget_check.exceeded,
                "utilization_pct": budget_check.utilization_pct,
            }

        return report

    def get_budget_status(self, budget_usd: float | None = None) -> dict[str, Any]:
        """Check current spend vs budget.

        Args:
            budget_usd: Budget limit in USD.  If None, uses the instance
                        budget_usd set at construction time.  If both are
                        None, returns spend without budget comparison.

        Returns:
            Dict with spend, budget, remaining, and whether exceeded.
        """
        effective_budget = budget_usd or self._budget_usd
        total_cost = self._cost_tracker.get_total_cost()

        status: dict[str, Any] = {
            "total_cost_usd": total_cost.total_cost_usd,
            "total_tokens": total_cost.total_tokens,
            "total_calls": total_cost.total_calls,
            "steps_executed": self._steps_executed,
            "steps_compacted": self._steps_compacted,
        }

        if effective_budget is not None:
            check = self._cost_tracker.check_budget(effective_budget)
            status["budget_usd"] = check.budget_usd
            status["remaining_usd"] = check.remaining_usd
            status["exceeded"] = check.exceeded
            status["utilization_pct"] = check.utilization_pct
            status["top_steps"] = check.top_steps
        else:
            status["budget_usd"] = None
            status["exceeded"] = None

        return status

    @property
    def cost_tracker(self) -> CostTracker:
        """Expose the underlying CostTracker for direct queries."""
        return self._cost_tracker

    @property
    def token_budget(self) -> TokenBudget:
        """Expose the underlying TokenBudget for direct queries."""
        return self._token_budget

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _chunks_were_compacted(
        original: list[dict[str, Any]],
        enforced: list[dict[str, Any]],
    ) -> bool:
        """Check if any chunks were compacted during enforcement.

        Compares _compacted flags on the enforced chunks.
        """
        for chunk in enforced:
            if chunk.get("_compacted", False):
                return True
        return False

    @staticmethod
    def _extract_usage(
        result: Any,
        default_model: str,
    ) -> tuple[int, int, str]:
        """Extract token usage from a step result.

        Supports multiple formats:
        - ``{"usage": {"input_tokens": N, "output_tokens": M}}``
        - ``{"input_tokens": N, "output_tokens": M}``
        - ``{"tokens": N}`` (treated as input tokens)

        Args:
            result: The step function's return value.
            default_model: Model to use if not found in the result.

        Returns:
            Tuple of (input_tokens, output_tokens, model).
        """
        if not isinstance(result, dict):
            return 0, 0, default_model

        # Format 1: nested usage dict
        usage = result.get("usage", {})
        if isinstance(usage, dict) and usage:
            return (
                usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                usage.get("output_tokens", usage.get("completion_tokens", 0)),
                usage.get("model", result.get("model", default_model)),
            )

        # Format 2: flat tokens in result
        input_t = result.get("input_tokens", 0)
        output_t = result.get("output_tokens", 0)
        if input_t > 0 or output_t > 0:
            return input_t, output_t, result.get("model", default_model)

        # Format 3: single tokens field
        total_tokens = result.get("tokens", 0)
        if total_tokens > 0:
            return total_tokens, 0, result.get("model", default_model)

        return 0, 0, default_model

    def _check_cumulative_budget(self, step_id: str) -> None:
        """Check cumulative USD budget and emit hook if exceeded.

        Fire-and-forget -- hook failure never blocks the pipeline.

        Args:
            step_id: The step that just completed (for context in hook payload).
        """
        if self._budget_usd is None:
            return

        check = self._cost_tracker.check_budget(self._budget_usd)

        if check.exceeded:
            logger.warning(
                "Cumulative budget exceeded after step '%s': $%.6f / $%.6f (%.1f%%)",
                step_id,
                check.spent_usd,
                check.budget_usd,
                check.utilization_pct,
            )

            if self._hook_bus is not None:
                payload = {
                    "event": HookEvent.ON_COST_THRESHOLD.value,
                    "trigger": "cumulative_budget_exceeded",
                    "step_id": step_id,
                    "budget_usd": check.budget_usd,
                    "spent_usd": check.spent_usd,
                    "remaining_usd": check.remaining_usd,
                    "utilization_pct": check.utilization_pct,
                    "top_steps": check.top_steps,
                }
                self._hook_bus.emit(HookEvent.ON_COST_THRESHOLD.value, payload)
                logger.debug("Emitted cumulative budget hook: %s", payload)
