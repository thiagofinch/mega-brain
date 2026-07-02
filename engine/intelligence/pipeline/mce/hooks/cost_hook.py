"""
cost_hook.py -- Non-Blocking LLM Cost Accumulator for the MCE Pipeline
=======================================================================

Architecture Decision
---------------------
This hook OBSERVES ``post_llm_call`` events emitted by the HookBus and
accumulates cost data in memory.  It never blocks the pipeline.  The
accumulated data can be exported to the pipeline manifest via
``export_to_manifest()``.

Integration with the full CostTracker module (MCE2-3.4) is OUT OF SCOPE.
This hook provides the data collection foundation that CostTracker will
consume later.

Import Direction
----------------
This module imports ``hook_bus.py``.  Nothing imports this module at the
pipeline orchestration level -- the hook registers itself on construction.

::

    cost_hook.py  -->  hook_bus.py  (one-way)
    orchestrate.py  -->  hook_bus.py  (unchanged)

Public API
----------
- ``CostHook(bus)`` -- construct and auto-register on post_llm_call
- ``get_accumulated_costs() -> list[dict]`` -- all recorded entries
- ``get_total_cost() -> float`` -- sum of cost_usd across all entries
- ``get_cost_by_step(step_id) -> float`` -- cost for a specific step
- ``export_to_manifest() -> dict`` -- formatted for pipeline manifest
- ``reset()`` -- clear accumulated data (useful for testing)

Cost Calculation
~~~~~~~~~~~~~~~~
Uses a static price lookup table with per-1K-token rates.
Default model prices are conservative estimates.  The table is
extensible via ``update_price_table()``.

Constraints
~~~~~~~~~~~
- stdlib + typing only (no external deps).
- Thread-safe via threading.Lock on the accumulator list.
- Handler exceptions are swallowed by the HookBus (non-blocking emit).
- DETERMINISTIC: same input payload always produces same cost entry.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-1.9 -- Cost Hook
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

logger = logging.getLogger("mce.hooks.cost_hook")


# ---------------------------------------------------------------------------
# Default Price Table (per 1K tokens, in USD)
# ---------------------------------------------------------------------------

# Conservative defaults -- can be updated at runtime via update_price_table().
_DEFAULT_PRICE_TABLE: dict[str, dict[str, float]] = {
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
}

# Fallback when model is not in the table.
_FALLBACK_PRICE: dict[str, float] = {"input": 0.001, "output": 0.002}


# ---------------------------------------------------------------------------
# CostHook
# ---------------------------------------------------------------------------


class CostHook:
    """Non-blocking LLM cost accumulator that registers on post_llm_call.

    On construction, auto-registers a handler on the provided HookBus for
    the ``post_llm_call`` event.  Each emission adds a cost entry to the
    internal accumulator.

    Thread-safe: multiple daemon threads can call the handler concurrently.

    Args:
        bus: A HookBus instance to register on.
        price_table: Optional custom price table.  If None, uses defaults.
    """

    def __init__(
        self,
        bus: Any,
        price_table: dict[str, dict[str, float]] | None = None,
    ) -> None:
        self._bus = bus
        self._entries: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._price_table: dict[str, dict[str, float]] = dict(price_table or _DEFAULT_PRICE_TABLE)

        # Auto-register on post_llm_call (AC1)
        self._bus.register(
            "post_llm_call",
            self._handle_post_llm_call,
            priority=0,
        )
        logger.info("CostHook registered on post_llm_call")

    # ------------------------------------------------------------------
    # Handler (called by HookBus in a daemon thread)
    # ------------------------------------------------------------------

    def _handle_post_llm_call(self, event: str, payload: dict[str, Any]) -> None:
        """Process a post_llm_call event and accumulate cost data.

        Expected payload keys:
            step_id (str): Pipeline step identifier.
            input_tokens (int): Tokens sent to the LLM.
            output_tokens (int): Tokens received from the LLM.
            model (str): Model identifier (e.g. "gemini-1.5-pro").

        Optional payload keys:
            cost_usd (float): Pre-calculated cost.  If absent, calculated
                from the price table.
            timestamp (float): Unix timestamp.  If absent, uses time.time().
        """
        step_id = payload.get("step_id", "unknown")
        input_tokens = payload.get("input_tokens", 0)
        output_tokens = payload.get("output_tokens", 0)
        model = payload.get("model", "unknown")
        timestamp = payload.get("timestamp", time.time())

        # Use pre-calculated cost if provided, otherwise compute it
        if "cost_usd" in payload:
            cost_usd = float(payload["cost_usd"])
        else:
            cost_usd = self._calculate_cost(model, input_tokens, output_tokens)

        entry: dict[str, Any] = {
            "step_id": step_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model": model,
            "cost_usd": cost_usd,
            "timestamp": timestamp,
        }

        with self._lock:
            self._entries.append(entry)

        logger.debug(
            "Cost recorded: step=%s model=%s tokens=%d+%d cost=$%.6f",
            step_id,
            model,
            input_tokens,
            output_tokens,
            cost_usd,
        )

    # ------------------------------------------------------------------
    # Cost calculation
    # ------------------------------------------------------------------

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD from token counts and the price table.

        Price table rates are per 1K tokens.

        Args:
            model: Model identifier to look up in the price table.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Cost in USD as a float.
        """
        prices = self._price_table.get(model, _FALLBACK_PRICE)
        input_cost = (input_tokens / 1000.0) * prices["input"]
        output_cost = (output_tokens / 1000.0) * prices["output"]
        return input_cost + output_cost

    # ------------------------------------------------------------------
    # Public query API
    # ------------------------------------------------------------------

    def get_accumulated_costs(self) -> list[dict[str, Any]]:
        """Return all accumulated cost entries.

        Returns:
            List of dicts, each with: step_id, input_tokens, output_tokens,
            model, cost_usd, timestamp.
        """
        with self._lock:
            return list(self._entries)

    def get_total_cost(self) -> float:
        """Return the total accumulated cost in USD.

        Returns:
            Sum of cost_usd across all entries.
        """
        with self._lock:
            return sum(e["cost_usd"] for e in self._entries)

    def get_cost_by_step(self, step_id: str) -> float:
        """Return the total cost for a specific pipeline step.

        Args:
            step_id: The step identifier to filter by.

        Returns:
            Sum of cost_usd for all entries matching step_id.
        """
        with self._lock:
            return sum(e["cost_usd"] for e in self._entries if e["step_id"] == step_id)

    def export_to_manifest(self) -> dict[str, Any]:
        """Format accumulated cost data for pipeline manifest integration.

        Returns:
            Dict with keys: total_cost_usd, entry_count, cost_by_step,
            cost_by_model, entries.
        """
        with self._lock:
            entries = list(self._entries)

        total = sum(e["cost_usd"] for e in entries)

        cost_by_step: dict[str, float] = {}
        for e in entries:
            sid = e["step_id"]
            cost_by_step[sid] = cost_by_step.get(sid, 0.0) + e["cost_usd"]

        cost_by_model: dict[str, float] = {}
        for e in entries:
            m = e["model"]
            cost_by_model[m] = cost_by_model.get(m, 0.0) + e["cost_usd"]

        tokens_total = {
            "input": sum(e["input_tokens"] for e in entries),
            "output": sum(e["output_tokens"] for e in entries),
        }

        return {
            "total_cost_usd": round(total, 6),
            "entry_count": len(entries),
            "tokens_total": tokens_total,
            "cost_by_step": {k: round(v, 6) for k, v in cost_by_step.items()},
            "cost_by_model": {k: round(v, 6) for k, v in cost_by_model.items()},
            "entries": entries,
        }

    # ------------------------------------------------------------------
    # Price table management
    # ------------------------------------------------------------------

    def update_price_table(self, model: str, input_per_1k: float, output_per_1k: float) -> None:
        """Add or update a model's pricing in the lookup table.

        Args:
            model: Model identifier (e.g. "gemini-2.0-pro").
            input_per_1k: Cost per 1K input tokens in USD.
            output_per_1k: Cost per 1K output tokens in USD.
        """
        self._price_table[model] = {
            "input": input_per_1k,
            "output": output_per_1k,
        }
        logger.info(
            "Price table updated: %s = $%.5f/$%.5f per 1K", model, input_per_1k, output_per_1k
        )

    # ------------------------------------------------------------------
    # Reset (for testing)
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear all accumulated cost entries."""
        with self._lock:
            self._entries.clear()
        logger.debug("CostHook entries cleared")
