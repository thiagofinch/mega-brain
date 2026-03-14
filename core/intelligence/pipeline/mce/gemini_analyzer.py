"""
gemini_analyzer.py -- Gemini Flash 2.0 Wrapper for MCE Pipeline
================================================================

High-volume, low-cost classification via Google Gemini Flash 2.0.
Optional dependency: falls back gracefully when GOOGLE_API_KEY is not set.

Tasks supported:
- ``classify_dna_layer``: Classify text into one of the 5 DNA layers
- ``extract_entities``: Extract named entities from text
- ``score_source_quality``: Score source quality (0-100)

Usage::

    from core.intelligence.pipeline.mce.gemini_analyzer import GeminiAnalyzer

    analyzer = GeminiAnalyzer()
    result = analyzer.analyze("Some expert text...", task="classify_dna_layer")

    # Batch mode
    results = analyzer.analyze_batch(
        ["text1", "text2", "text3"],
        task="extract_entities",
    )

Version: 1.0.0
Date: 2026-03-10
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("mce.gemini_analyzer")

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class GeminiNotConfiguredError(RuntimeError):
    """Raised when GOOGLE_API_KEY is not set in the environment.

    Callers should catch this and fall back to Claude-based extraction.
    """


class GeminiAnalysisError(RuntimeError):
    """Raised when Gemini returns an unexpected or empty response."""


# ---------------------------------------------------------------------------
# Task Prompt Templates
# ---------------------------------------------------------------------------

TASK_PROMPTS: dict[str, str] = {
    "classify_dna_layer": (
        "Classify the following text into EXACTLY ONE of these 5 DNA knowledge layers:\n"
        "1. PHILOSOPHIES - Core beliefs, worldview, values\n"
        "2. MENTAL_MODELS - Thinking and decision frameworks\n"
        "3. HEURISTICS - Practical rules, decision shortcuts, rules of thumb\n"
        "4. FRAMEWORKS - Structured methodologies with named steps\n"
        "5. METHODOLOGIES - Detailed step-by-step implementation processes\n\n"
        "Respond with ONLY the layer name (e.g. 'HEURISTICS'). No explanation.\n\n"
        "Text:\n{text}"
    ),
    "extract_entities": (
        "Extract named entities from the following text. Return a JSON array of objects, "
        "each with 'name' (string), 'type' (PERSON|COMPANY|CONCEPT|METRIC|FRAMEWORK), "
        "and 'context' (brief phrase).\n\n"
        "Respond with ONLY the JSON array. No markdown fencing.\n\n"
        "Text:\n{text}"
    ),
    "score_source_quality": (
        "Score the following text on source quality from 0 to 100 based on:\n"
        "- Specificity (has concrete numbers, examples, steps)\n"
        "- Actionability (can be directly applied)\n"
        "- Originality (unique insight vs generic advice)\n"
        "- Depth (surface-level vs expert-level detail)\n\n"
        "Respond with ONLY a single integer 0-100. No explanation.\n\n"
        "Text:\n{text}"
    ),
}

VALID_TASKS: set[str] = set(TASK_PROMPTS.keys())

# ---------------------------------------------------------------------------
# Token Tracking
# ---------------------------------------------------------------------------


@dataclass
class TokenUsage:
    """Tracks cumulative token usage across analyze calls."""

    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def record(self, input_t: int, output_t: int) -> None:
        """Record token usage for a single call."""
        self.input_tokens += input_t
        self.output_tokens += output_t
        self.calls += 1

    def to_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "calls": self.calls,
        }


# ---------------------------------------------------------------------------
# GeminiAnalyzer
# ---------------------------------------------------------------------------


@dataclass
class GeminiAnalyzer:
    """Wrapper for Google Gemini Flash 2.0 for high-volume classification.

    Args:
        model_name: Gemini model identifier.
        max_retries: Maximum retry attempts with exponential backoff.
        base_delay: Base delay in seconds for exponential backoff.
    """

    model_name: str = "gemini-2.0-flash"
    max_retries: int = 3
    base_delay: float = 1.0
    usage: TokenUsage = field(default_factory=TokenUsage)
    _client: Any = field(default=None, repr=False)

    def __post_init__(self) -> None:
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            # Do NOT initialize client -- analyze() will raise on demand
            self._client = None
            logger.info("GOOGLE_API_KEY not set -- Gemini analyzer will raise on use")
            return

        try:
            import google.generativeai as genai  # type: ignore[import-untyped]

            genai.configure(api_key=api_key)
            self._client = genai.GenerativeModel(self.model_name)
            logger.info("Gemini analyzer initialized with model %s", self.model_name)
        except ImportError:
            logger.warning("google-generativeai not installed -- Gemini analyzer unavailable")
            self._client = None

    # -- core API -----------------------------------------------------------

    def analyze(self, text: str, task: str) -> str:
        """Analyze text using Gemini for the given task.

        Args:
            text: The input text to analyze.
            task: One of ``classify_dna_layer``, ``extract_entities``,
                  ``score_source_quality``.

        Returns:
            The model's response text (stripped).

        Raises:
            GeminiNotConfiguredError: If GOOGLE_API_KEY is not set or library missing.
            GeminiAnalysisError: If all retries fail.
            ValueError: If task is not recognized.
        """
        self._ensure_configured()
        self._validate_task(task)

        prompt = TASK_PROMPTS[task].format(text=text[:8000])  # Truncate for safety
        return self._call_with_retry(prompt)

    def analyze_batch(self, texts: list[str], task: str) -> list[str]:
        """Analyze multiple texts sequentially.

        Args:
            texts: List of input texts.
            task: Task identifier (same as :meth:`analyze`).

        Returns:
            List of response strings, one per input text.

        Raises:
            GeminiNotConfiguredError: If GOOGLE_API_KEY is not set.
            GeminiAnalysisError: If any call fails after all retries.
            ValueError: If task is not recognized.
        """
        self._ensure_configured()
        self._validate_task(task)

        results: list[str] = []
        for i, text in enumerate(texts):
            logger.debug("Batch analyze [%d/%d] task=%s", i + 1, len(texts), task)
            prompt = TASK_PROMPTS[task].format(text=text[:8000])
            result = self._call_with_retry(prompt)
            results.append(result)
        return results

    # -- internal -----------------------------------------------------------

    def _ensure_configured(self) -> None:
        """Raise ``GeminiNotConfiguredError`` if client is not available."""
        if self._client is None:
            api_key = os.environ.get("GOOGLE_API_KEY", "")
            if not api_key:
                msg = (
                    "GOOGLE_API_KEY not set in environment. "
                    "Set it to use Gemini, or handle GeminiNotConfiguredError "
                    "to fall back to Claude."
                )
                raise GeminiNotConfiguredError(msg)
            msg = (
                "google-generativeai library not installed. "
                "Install with: pip install google-generativeai>=0.8.0"
            )
            raise GeminiNotConfiguredError(msg)

    def _validate_task(self, task: str) -> None:
        """Validate that the task is recognized."""
        if task not in VALID_TASKS:
            msg = f"Unknown task {task!r}. Valid tasks: {sorted(VALID_TASKS)}"
            raise ValueError(msg)

    def _call_with_retry(self, prompt: str) -> str:
        """Call Gemini with exponential backoff retry.

        Args:
            prompt: The full prompt to send.

        Returns:
            Response text (stripped).

        Raises:
            GeminiAnalysisError: If all retries exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.generate_content(prompt)

                # Track token usage from response metadata
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    meta = response.usage_metadata
                    input_t = getattr(meta, "prompt_token_count", 0) or 0
                    output_t = getattr(meta, "candidates_token_count", 0) or 0
                    self.usage.record(input_t, output_t)

                # Extract text
                if response.text:
                    return response.text.strip()

                # Gemini returned empty text
                msg = "Gemini returned empty response"
                raise GeminiAnalysisError(msg)

            except GeminiAnalysisError:
                raise
            except GeminiNotConfiguredError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Gemini attempt %d/%d failed: %s -- retrying in %.1fs",
                        attempt,
                        self.max_retries,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "Gemini failed after %d attempts: %s",
                        self.max_retries,
                        exc,
                    )

        msg = f"Gemini failed after {self.max_retries} attempts"
        if last_error:
            msg += f": {last_error}"
        raise GeminiAnalysisError(msg)

    # -- convenience --------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        """Return *True* if the Gemini client is available."""
        return self._client is not None

    def __repr__(self) -> str:
        return (
            f"GeminiAnalyzer(model={self.model_name!r}, "
            f"configured={self.is_configured}, "
            f"calls={self.usage.calls})"
        )
