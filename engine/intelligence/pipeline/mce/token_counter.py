"""
token_counter.py -- Token Counting for MCE Pipeline
====================================================

Provides token estimation for chunks heading into the LLM context window.
Uses tiktoken when available (accurate), falls back to chars/4 heuristic.

The MCE pipeline uses this before sending chunks to Gemini/OpenAI to decide
whether compaction is needed.

Usage::

    from engine.intelligence.pipeline.mce.token_counter import (
        count_tokens,
        estimate_context_usage,
    )

    n = count_tokens("some long text here")
    usage = estimate_context_usage(chunks, "Analyze the following:")

Constraints:
    - stdlib + optional tiktoken -- no other external deps.
    - Never raises on missing tiktoken -- degrades gracefully.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-1.1
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("mce.token_counter")

# ---------------------------------------------------------------------------
# tiktoken availability probe
# ---------------------------------------------------------------------------

_tiktoken_encode = None

try:
    import tiktoken

    # cl100k_base covers GPT-4/3.5; reasonable proxy for Gemini token counts
    _enc = tiktoken.get_encoding("cl100k_base")
    _tiktoken_encode = _enc.encode
    logger.debug("tiktoken available -- using cl100k_base encoding")
except ImportError:
    logger.debug("tiktoken not installed -- falling back to chars/4 heuristic")


# ---------------------------------------------------------------------------
# Model context-window registry
# ---------------------------------------------------------------------------

# Maps model identifiers to their maximum context window in tokens.
# Used by estimate_context_usage to compute budget_pct.
MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    "gemini-1.5-pro": 1_048_576,
    "gemini-1.5-flash": 1_048_576,
    "gemini-2.0-flash": 1_048_576,
    "gpt-4": 8_192,
    "gpt-4-turbo": 128_000,
    "gpt-4o": 128_000,
    "gpt-3.5-turbo": 16_385,
    "claude-3-opus": 200_000,
    "claude-3-sonnet": 200_000,
    "claude-3-haiku": 200_000,
}

DEFAULT_CONTEXT_WINDOW: int = 128_000  # safe fallback


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def count_tokens(text: str, model: str = "gemini-1.5-pro") -> int:
    """Count tokens in a text string.

    Uses tiktoken (cl100k_base) when available for accurate counts.
    Falls back to ``len(text) // 4`` heuristic otherwise -- a widely
    accepted approximation for English text.

    Args:
        text: The text to count tokens for.
        model: Model identifier (currently used for logging; encoding
               is cl100k_base regardless).  Reserved for future per-model
               encodings.

    Returns:
        Estimated token count (always >= 0).
    """
    if not text:
        return 0

    if _tiktoken_encode is not None:
        return len(_tiktoken_encode(text))

    # Fallback: chars / 4 is the standard quick estimate
    return max(1, len(text) // 4)


def count_tokens_for_chunks(
    chunks: list[dict[str, Any]],
    model: str = "gemini-1.5-pro",
    text_key: str = "text",
) -> list[dict[str, Any]]:
    """Count tokens for each chunk and return annotated copies.

    Each returned chunk dict is a **shallow copy** of the original with
    an added ``_token_count`` field.  The original chunks are not mutated.

    Args:
        chunks: List of chunk dicts.  Each must have a ``text`` key
                (configurable via *text_key*).
        model: Model identifier passed to :func:`count_tokens`.
        text_key: Key in each chunk dict that holds the text content.

    Returns:
        List of chunk dicts with ``_token_count`` added.
    """
    result = []
    for chunk in chunks:
        annotated = dict(chunk)  # shallow copy
        content = chunk.get(text_key, "")
        annotated["_token_count"] = count_tokens(content, model=model)
        result.append(annotated)
    return result


def estimate_context_usage(
    chunks: list[dict[str, Any]],
    prompt_template: str = "",
    model: str = "gemini-1.5-pro",
    text_key: str = "text",
) -> dict[str, Any]:
    """Estimate total context usage for a set of chunks + prompt.

    Sums token counts across all chunks and the prompt template to
    produce a usage report against the model's context window.

    Args:
        chunks: List of chunk dicts with a text field.
        prompt_template: The prompt/instruction text that wraps the chunks.
        model: Model identifier for context window lookup.
        text_key: Key in each chunk dict that holds the text content.

    Returns:
        Dict with::

            {
                "total_tokens": int,
                "prompt_tokens": int,
                "chunk_tokens": int,
                "chunk_count": int,
                "context_window": int,
                "budget_pct": float,   # 0.0 - 1.0+
                "over_budget": bool,
                "model": str,
            }
    """
    prompt_tokens = count_tokens(prompt_template, model=model)

    chunk_tokens = 0
    for chunk in chunks:
        content = chunk.get(text_key, "")
        chunk_tokens += count_tokens(content, model=model)

    total_tokens = prompt_tokens + chunk_tokens
    context_window = MODEL_CONTEXT_WINDOWS.get(model, DEFAULT_CONTEXT_WINDOW)
    budget_pct = total_tokens / context_window if context_window > 0 else 1.0

    return {
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "chunk_tokens": chunk_tokens,
        "chunk_count": len(chunks),
        "context_window": context_window,
        "budget_pct": round(budget_pct, 4),
        "over_budget": budget_pct > 1.0,
        "model": model,
    }
