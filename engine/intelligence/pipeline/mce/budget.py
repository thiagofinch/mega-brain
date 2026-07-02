"""
budget.py -- Token Budget Enforcement for the MCE Pipeline
===========================================================

Sits between pipeline steps and the LLM call, ensuring that the assembled
prompt + chunks never exceed the model's context window budget.  When the
budget is exceeded, it delegates to ``context_compactor.run()`` for
automatic compaction and fires the ``on_cost_threshold`` hook for
observability.

Architecture
------------
Uses Facade Pattern -- wraps three lower-level modules into one budget
check-and-enforce API that any pipeline step can call without knowing the
compaction or hook internals.

::

    pipeline step  ──▶  budget.check_budget()   ──▶  token_counter
                        budget.enforce()         ──▶  context_compactor
                                                 ──▶  hook_bus (on_cost_threshold)

Public API
----------
- ``TokenBudget(config, hook_bus)`` -- budget enforcer bound to config cascade
- ``check_budget(prompt, model, step_id)`` -- check without side effects
- ``enforce(chunks, prompt_template, model, step_id)`` -- check + compact + emit
- ``get_model_limit(model)`` -- lookup a model's context window
- ``BudgetCheck`` -- dataclass with check result

Configuration
-------------
- ``context_budget_pct``: fraction of context window to use (default 0.8)
- Per-step override: config key ``budget_pct_{step_id}`` (e.g. ``budget_pct_analyze``)

Constraints
~~~~~~~~~~~
- stdlib + project modules only (no external deps).
- Never mutates input chunks (delegated invariant from context_compactor).
- Hook failure never blocks enforcement (fire-and-forget via HookBus.emit).

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-3.3
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from engine.intelligence.pipeline.mce.config_cascade import CascadeConfig
from engine.intelligence.pipeline.mce.context_compactor import ContextCompactor
from engine.intelligence.pipeline.mce.hook_bus import HookBus, HookEvent
from engine.intelligence.pipeline.mce.token_counter import (
    DEFAULT_CONTEXT_WINDOW,
    MODEL_CONTEXT_WINDOWS,
    count_tokens,
)

logger = logging.getLogger("mce.budget")

# ---------------------------------------------------------------------------
# Default constants
# ---------------------------------------------------------------------------

DEFAULT_BUDGET_PCT: float = 0.80  # 80% of context window


# ---------------------------------------------------------------------------
# BudgetCheck result
# ---------------------------------------------------------------------------


@dataclass
class BudgetCheck:
    """Result of a token budget check.

    Attributes:
        within_budget: True if total tokens fit within the budget threshold.
        total_tokens:  Total tokens counted (prompt + any chunks in the prompt).
        max_tokens:    Absolute token limit for the model's context window.
        budget_tokens: Effective budget (max_tokens * budget_pct).
        remaining:     Tokens still available before hitting budget (0 if over).
        action:        One of "pass", "compact", or "reject".
                       - "pass": within budget, no action needed.
                       - "compact": over budget, auto-compaction recommended.
                       - "reject": over budget even after theoretical compaction
                                   (reserved for future hard-reject logic).
        model:         Model identifier used for the check.
        budget_pct:    Budget percentage that was applied.
    """

    within_budget: bool
    total_tokens: int
    max_tokens: int
    budget_tokens: int
    remaining: int
    action: str  # "pass" | "compact" | "reject"
    model: str = ""
    budget_pct: float = DEFAULT_BUDGET_PCT

    def to_dict(self) -> dict[str, Any]:
        return {
            "within_budget": self.within_budget,
            "total_tokens": self.total_tokens,
            "max_tokens": self.max_tokens,
            "budget_tokens": self.budget_tokens,
            "remaining": self.remaining,
            "action": self.action,
            "model": self.model,
            "budget_pct": self.budget_pct,
        }


# ---------------------------------------------------------------------------
# TokenBudget
# ---------------------------------------------------------------------------


class TokenBudget:
    """Token budget enforcement for the MCE pipeline.

    Binds to a ``CascadeConfig`` for threshold resolution and an optional
    ``HookBus`` for emitting ``on_cost_threshold`` when budget is exceeded.

    Args:
        config: CascadeConfig instance for resolving ``context_budget_pct``
                and per-step overrides (``budget_pct_{step_id}``).
        hook_bus: Optional HookBus for emitting cost threshold hooks.
                  If None, hooks are silently skipped.
    """

    def __init__(
        self,
        config: CascadeConfig,
        hook_bus: HookBus | None = None,
    ) -> None:
        self._config = config
        self._hook_bus = hook_bus

    # ------------------------------------------------------------------
    # Model context window lookup
    # ------------------------------------------------------------------

    @staticmethod
    def get_model_limit(model: str) -> int:
        """Look up the context window size for a model.

        Falls back to ``DEFAULT_CONTEXT_WINDOW`` (128k) for unknown models.

        Args:
            model: Model identifier (e.g. "gemini-1.5-pro", "gpt-4o").

        Returns:
            Maximum context window in tokens.
        """
        return MODEL_CONTEXT_WINDOWS.get(model, DEFAULT_CONTEXT_WINDOW)

    # ------------------------------------------------------------------
    # Budget percentage resolution
    # ------------------------------------------------------------------

    def _resolve_budget_pct(self, step_id: str | None = None) -> float:
        """Resolve the budget percentage from config cascade.

        Per-step override key: ``budget_pct_{step_id}``.
        Falls back to ``context_budget_pct`` from the cascade.
        Final fallback: ``DEFAULT_BUDGET_PCT`` (0.8).

        Args:
            step_id: Optional pipeline step identifier for per-step override.

        Returns:
            Budget percentage as a float between 0.0 and 1.0.
        """
        # Per-step override takes highest priority
        if step_id:
            step_key = f"budget_pct_{step_id}"
            step_val = self._config.get(step_key)
            if step_val is not None:
                try:
                    pct = float(step_val)
                    if 0.0 < pct <= 1.0:
                        logger.debug(
                            "Per-step budget override: %s = %.2f",
                            step_key,
                            pct,
                        )
                        return pct
                except (TypeError, ValueError):
                    pass

        # Global cascade value
        global_val = self._config.get("context_budget_pct")
        if global_val is not None:
            try:
                pct = float(global_val)
                if 0.0 < pct <= 1.0:
                    return pct
            except (TypeError, ValueError):
                pass

        return DEFAULT_BUDGET_PCT

    # ------------------------------------------------------------------
    # check_budget -- pure check, no side effects
    # ------------------------------------------------------------------

    def check_budget(
        self,
        prompt: str,
        model: str | None = None,
        step_id: str | None = None,
    ) -> BudgetCheck:
        """Check whether a prompt fits within the token budget.

        Pure check -- no compaction, no hooks, no side effects.

        Args:
            prompt: The full prompt text to count tokens for.
            model: Model identifier.  If None, resolved from config cascade
                   (key ``model``), then falls back to ``"gemini-1.5-pro"``.
            step_id: Optional pipeline step identifier.  When provided,
                     checks for a per-step budget override at config key
                     ``budget_pct_{step_id}`` before falling back to
                     ``context_budget_pct``.

        Returns:
            BudgetCheck with the result of the check.
        """
        resolved_model = model or self._config.get("model", "gemini-1.5-pro")
        budget_pct = self._resolve_budget_pct(step_id)
        max_tokens = self.get_model_limit(resolved_model)
        budget_tokens = int(max_tokens * budget_pct)

        total_tokens = count_tokens(prompt, model=resolved_model)
        remaining = max(0, budget_tokens - total_tokens)
        within_budget = total_tokens <= budget_tokens

        # Determine action
        if within_budget:
            action = "pass"
        else:
            action = "compact"

        check = BudgetCheck(
            within_budget=within_budget,
            total_tokens=total_tokens,
            max_tokens=max_tokens,
            budget_tokens=budget_tokens,
            remaining=remaining,
            action=action,
            model=resolved_model,
            budget_pct=budget_pct,
        )

        logger.info(
            "Budget check [step=%s, model=%s]: %d / %d tokens (%.0f%% of %d window) -> %s",
            step_id or "global",
            resolved_model,
            total_tokens,
            budget_tokens,
            budget_pct * 100,
            max_tokens,
            action,
        )

        return check

    # ------------------------------------------------------------------
    # enforce -- check + compact + emit hook
    # ------------------------------------------------------------------

    def enforce(
        self,
        chunks: list[dict[str, Any]],
        prompt_template: str,
        model: str | None = None,
        step_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Enforce the token budget on a set of chunks.

        If the prompt + chunks exceed the budget threshold:
        1. Calls ``ContextCompactor.run()`` to compact chunks.
        2. Emits ``on_cost_threshold`` hook via HookBus.
        3. Returns the compacted chunks.

        If within budget, returns the original chunks unchanged.

        Args:
            chunks: List of chunk dicts (with ``text`` key).
            prompt_template: The prompt template that wraps the chunks.
            model: Model identifier.  Resolved from config if None.
            step_id: Optional step identifier for per-step budget override.

        Returns:
            List of chunk dicts -- either original (if within budget) or
            compacted (if over budget).
        """
        resolved_model = model or self._config.get("model", "gemini-1.5-pro")
        budget_pct = self._resolve_budget_pct(step_id)
        max_tokens = self.get_model_limit(resolved_model)

        # Resolve circuit breaker max from config cascade (Story MCE21-1.3)
        cb_max = self._config.get("circuit_breaker_max", 3)
        try:
            cb_max = int(cb_max)
        except (TypeError, ValueError):
            cb_max = 3

        # Build the compactor with the resolved budget percentage
        # and circuit breaker config (MCE21-1.3)
        compactor = ContextCompactor(
            model=resolved_model,
            threshold_pct=budget_pct,
            max_compact_failures=cb_max,
            hook_bus=self._hook_bus,
        )

        # Run the full 4-stage pipeline (count/check/compact/mark)
        result = compactor.run(
            chunks,
            max_tokens=max_tokens,
            prompt_template=prompt_template,
        )

        if result["compacted"]:
            logger.warning(
                "Budget exceeded [step=%s, model=%s]: compacted %d chunks, saved %d tokens",
                step_id or "global",
                resolved_model,
                result["stats"].stage_3_chunks_compacted,
                result["stats"].stage_3_tokens_saved,
            )

            # Emit on_cost_threshold hook (fire-and-forget, never blocks)
            self._emit_cost_threshold(
                step_id=step_id,
                model=resolved_model,
                budget_pct=budget_pct,
                max_tokens=max_tokens,
                stats=result["stats"],
                usage=result["usage"],
            )

            return result["chunks"]

        logger.info(
            "Budget OK [step=%s, model=%s]: %d tokens within %.0f%% threshold",
            step_id or "global",
            resolved_model,
            result["stats"].stage_1_total_tokens,
            budget_pct * 100,
        )

        return result["chunks"]

    # ------------------------------------------------------------------
    # Hook emission
    # ------------------------------------------------------------------

    def _emit_cost_threshold(
        self,
        *,
        step_id: str | None,
        model: str,
        budget_pct: float,
        max_tokens: int,
        stats: Any,
        usage: dict[str, Any],
    ) -> None:
        """Emit the on_cost_threshold hook when budget is exceeded.

        Fire-and-forget -- hook failure never blocks the pipeline.
        """
        if self._hook_bus is None:
            logger.debug("No HookBus configured -- skipping on_cost_threshold emission")
            return

        payload = {
            "event": HookEvent.ON_COST_THRESHOLD.value,
            "step_id": step_id,
            "model": model,
            "budget_pct": budget_pct,
            "max_tokens": max_tokens,
            "budget_tokens": int(max_tokens * budget_pct),
            "total_tokens_before": stats.stage_1_total_tokens,
            "chunks_compacted": stats.stage_3_chunks_compacted,
            "tokens_saved": stats.stage_3_tokens_saved,
            "usage_after": usage,
        }

        self._hook_bus.emit(HookEvent.ON_COST_THRESHOLD.value, payload)
        logger.debug("Emitted on_cost_threshold hook: %s", payload)
