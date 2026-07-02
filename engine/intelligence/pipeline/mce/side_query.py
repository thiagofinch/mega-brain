"""
side_query.py -- Lightweight Side-Channel LLM Call for MCE Pipeline
===================================================================

Provides a dedicated LLM call function for classification, scoring, and
routing decisions that need a cheaper/faster model WITHOUT consuming the
main pipeline token budget.

Architecture
------------
::

    MAIN PIPELINE                    SIDE QUERY
    ─────────────                    ──────────
    cost_tracker.py ── budget A      side_query() ── budget B (SEPARATE)
    llm_provider.py ── gemini        anthropic SDK ── sonnet

The two budgets are completely independent.  ``side_query()`` tracks its
own token usage via ``SideQueryTracker`` and never touches ``CostTracker``.

Public API
----------
- ``side_query(system_prompt, messages, **kwargs) -> str``
- ``side_query_json(system_prompt, messages, **kwargs) -> dict``
- ``get_side_query_usage() -> dict``
- ``reset_side_query_usage() -> None``

Constraints
~~~~~~~~~~~
- stdlib + anthropic SDK only (already a project dependency).
- Thread-safe via threading.Lock on the tracker.
- DETERMINISTIC mock path for tests (no real API calls).
- Timeout enforced at the HTTP level (not asyncio).

Version: 1.0.0
Date: 2026-04-02
Story: MCE22-2.2
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("mce.side_query")

# ---------------------------------------------------------------------------
# Model Configuration
# ---------------------------------------------------------------------------

# Default model for side queries -- cheap, fast, good enough for classification
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TIMEOUT = 30  # seconds

# Alias map: short names -> full model identifiers
MODEL_ALIASES: dict[str, str] = {
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-3-5-haiku-20241022",
}

# Price per 1K tokens (USD) -- mirrors llm_provider.PRICE_TABLE format
SIDE_QUERY_PRICES: dict[str, dict[str, float]] = {
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
}

_FALLBACK_PRICE: dict[str, float] = {"input": 0.003, "output": 0.015}


# ---------------------------------------------------------------------------
# Usage Tracker (separate from main pipeline CostTracker)
# ---------------------------------------------------------------------------


@dataclass
class SideQueryUsage:
    """Accumulated usage for all side_query calls in the current session.

    This is intentionally separate from the main pipeline's CostTracker.
    The pipeline budget tracks gemini/main-model calls; this tracker
    covers only side-channel classification/scoring calls.
    """

    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    calls: list[dict[str, Any]] = field(default_factory=list)


class SideQueryTracker:
    """Thread-safe tracker for side_query token usage and cost.

    Completely independent from the main pipeline CostTracker.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._usage = SideQueryUsage()

    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_s: float,
    ) -> None:
        """Record a completed side_query call."""
        prices = SIDE_QUERY_PRICES.get(model, _FALLBACK_PRICE)
        cost = (input_tokens / 1000.0) * prices["input"] + (output_tokens / 1000.0) * prices[
            "output"
        ]

        with self._lock:
            self._usage.total_calls += 1
            self._usage.total_input_tokens += input_tokens
            self._usage.total_output_tokens += output_tokens
            self._usage.total_cost_usd += cost
            self._usage.calls.append(
                {
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": round(cost, 6),
                    "duration_s": round(duration_s, 3),
                }
            )

    def get_usage(self) -> dict[str, Any]:
        """Return current usage snapshot as a dict."""
        with self._lock:
            return {
                "total_calls": self._usage.total_calls,
                "total_input_tokens": self._usage.total_input_tokens,
                "total_output_tokens": self._usage.total_output_tokens,
                "total_cost_usd": round(self._usage.total_cost_usd, 6),
                "calls": list(self._usage.calls),
            }

    def reset(self) -> None:
        """Reset all tracked usage to zero."""
        with self._lock:
            self._usage = SideQueryUsage()


# Module-level tracker instance (singleton per process)
_tracker = SideQueryTracker()


# ---------------------------------------------------------------------------
# Client Management
# ---------------------------------------------------------------------------

_client_lock = threading.Lock()
_client: Any = None  # anthropic.Anthropic instance, lazily created


def _get_client() -> Any:
    """Lazily create and return the Anthropic client.

    Uses ANTHROPIC_API_KEY from environment. Thread-safe.

    Raises:
        RuntimeError: If ANTHROPIC_API_KEY is not set.
    """
    global _client

    if _client is not None:
        return _client

    with _client_lock:
        # Double-check after acquiring lock
        if _client is not None:
            return _client

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Side query requires an Anthropic API key. "
                "Set it in .env or environment variables."
            )

        try:
            from anthropic import Anthropic

            _client = Anthropic(api_key=api_key)
            logger.info("Anthropic client initialized for side_query")
            return _client
        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. " "Install with: pip install anthropic"
            )


def _resolve_model(model: str) -> str:
    """Resolve a model alias to a full model identifier.

    Args:
        model: Short alias ("sonnet", "haiku") or full model name.

    Returns:
        Full model identifier string.
    """
    return MODEL_ALIASES.get(model, model)


# ---------------------------------------------------------------------------
# Core Function: side_query
# ---------------------------------------------------------------------------


class SideQueryError(Exception):
    """Raised when a side_query call fails."""


class SideQueryTimeoutError(SideQueryError):
    """Raised when a side_query call exceeds its timeout."""


def side_query(
    system_prompt: str,
    messages: list[dict[str, str]],
    *,
    model: str = "sonnet",
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: float = DEFAULT_TIMEOUT,
    json_mode: bool = False,
    temperature: float = 0.0,
) -> str:
    """Make a lightweight LLM call separate from the main pipeline.

    This function is the primary entry point for classification, scoring,
    and routing decisions that need a fast/cheap model.

    Args:
        system_prompt: System instructions for the model.
        messages: List of message dicts with "role" and "content" keys.
                  Example: [{"role": "user", "content": "Classify this."}]
        model: Model alias ("sonnet", "haiku") or full model name.
               Default: "sonnet" (claude-sonnet-4-20250514).
        max_tokens: Maximum tokens in the response. Default: 1024.
        timeout: Request timeout in seconds. Default: 30.
        json_mode: If True, instructs the model to return valid JSON.
                   Appends JSON instruction to system prompt.
        temperature: Sampling temperature. Default: 0.0 (deterministic).

    Returns:
        Model response text as a string.

    Raises:
        SideQueryError: If the API call fails.
        SideQueryTimeoutError: If the call exceeds the timeout.
        RuntimeError: If ANTHROPIC_API_KEY is not set or anthropic not installed.
    """
    resolved_model = _resolve_model(model)
    effective_system = system_prompt

    if json_mode:
        effective_system = (
            f"{system_prompt}\n\n"
            "IMPORTANT: You MUST respond with valid JSON only. "
            "No markdown, no explanation, no code fences. Just the JSON object."
        )

    client = _get_client()
    start_time = time.monotonic()

    try:
        response = client.messages.create(
            model=resolved_model,
            max_tokens=max_tokens,
            system=effective_system,
            messages=messages,
            temperature=temperature,
            timeout=timeout,
        )
    except Exception as exc:
        duration = time.monotonic() - start_time
        exc_name = type(exc).__name__

        # Detect timeout-like errors
        if "timeout" in exc_name.lower() or "timed out" in str(exc).lower():
            logger.error(
                "side_query timeout after %.1fs: model=%s",
                duration,
                resolved_model,
            )
            raise SideQueryTimeoutError(f"Side query timed out after {timeout}s") from exc

        logger.error(
            "side_query failed after %.1fs: model=%s error=%s",
            duration,
            resolved_model,
            exc,
        )
        raise SideQueryError(f"Side query failed: {exc}") from exc

    duration = time.monotonic() - start_time

    # Extract response text
    result_text = ""
    if response.content:
        result_text = response.content[0].text

    # Track usage -- completely separate from main pipeline budget
    input_tokens = getattr(response.usage, "input_tokens", 0)
    output_tokens = getattr(response.usage, "output_tokens", 0)

    _tracker.record(
        model=resolved_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_s=duration,
    )

    logger.info(
        "side_query complete: model=%s tokens=%d+%d duration=%.1fs",
        resolved_model,
        input_tokens,
        output_tokens,
        duration,
    )

    return result_text


def side_query_json(
    system_prompt: str,
    messages: list[dict[str, str]],
    **kwargs: Any,
) -> dict[str, Any]:
    """Make a side_query call and parse the response as JSON.

    Convenience wrapper that sets json_mode=True and parses the result.

    Args:
        system_prompt: System instructions for the model.
        messages: List of message dicts.
        **kwargs: Passed to side_query() (model, max_tokens, timeout, etc).

    Returns:
        Parsed JSON as a dict.

    Raises:
        SideQueryError: If the response is not valid JSON.
        SideQueryTimeoutError: If the call exceeds its timeout.
    """
    kwargs["json_mode"] = True
    raw = side_query(system_prompt, messages, **kwargs)

    # Strip markdown code fences if model included them despite instructions
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json or ```) and last line (```)
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("side_query_json: invalid JSON response: %s", raw[:200])
        raise SideQueryError(
            f"Side query returned invalid JSON: {exc}. "
            f"Raw response (first 200 chars): {raw[:200]}"
        ) from exc


# ---------------------------------------------------------------------------
# Usage Accessors (module-level)
# ---------------------------------------------------------------------------


def get_side_query_usage() -> dict[str, Any]:
    """Return cumulative usage stats for all side_query calls.

    Returns a dict with:
    - total_calls: int
    - total_input_tokens: int
    - total_output_tokens: int
    - total_cost_usd: float
    - calls: list of per-call details

    This data is SEPARATE from the main pipeline CostTracker.
    """
    return _tracker.get_usage()


def reset_side_query_usage() -> None:
    """Reset side_query usage counters to zero.

    Call this at the start of a new pipeline run to isolate
    per-run cost tracking.
    """
    _tracker.reset()
    logger.debug("Side query usage tracker reset")


# ---------------------------------------------------------------------------
# Testing Utilities
# ---------------------------------------------------------------------------


def _reset_client() -> None:
    """Reset the cached Anthropic client. FOR TESTS ONLY."""
    global _client
    with _client_lock:
        _client = None
