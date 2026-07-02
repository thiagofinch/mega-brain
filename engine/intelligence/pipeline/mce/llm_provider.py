"""
llm_provider.py -- LLM Provider Abstraction for MCE Pipeline
=============================================================

Strategy Pattern abstraction that decouples the pipeline from any
specific LLM vendor.  Adding a new provider (Claude, GPT, etc.)
requires only implementing the ``LLMProvider`` ABC.

Current providers:
- ``GeminiProvider`` -- wraps the existing ``GeminiAnalyzer``

Factory:
- ``get_provider(name)`` -- returns a ready-to-use provider instance

Usage::

    from engine.intelligence.pipeline.mce.llm_provider import get_provider

    provider = get_provider("gemini")
    result = provider.analyze("Classify this text...", task="classify_dna_layer")
    tokens = provider.count_tokens("How many tokens is this?")
    cost = provider.get_cost(input_tokens=500, output_tokens=100)

Constraints:
    - stdlib + project deps only (no new external deps).
    - Provider implementations MUST be stateless across analyze() calls
      (state like token usage is tracked externally by cost_hook).
    - analyze_streaming() is a forward-looking interface -- providers
      that don't support streaming raise NotImplementedError.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-2.8
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Iterator

from engine.intelligence.pipeline.mce.gemini_analyzer import (
    GeminiAnalyzer,
)
from engine.intelligence.pipeline.mce.token_counter import count_tokens as tc_count_tokens

logger = logging.getLogger("mce.llm_provider")


# ---------------------------------------------------------------------------
# Price Table (per 1K tokens, USD) -- shared across providers
# ---------------------------------------------------------------------------

PRICE_TABLE: dict[str, dict[str, float]] = {
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
}

_FALLBACK_PRICE: dict[str, float] = {"input": 0.001, "output": 0.002}


# ---------------------------------------------------------------------------
# LLMProvider ABC
# ---------------------------------------------------------------------------


class LLMProvider(ABC):
    """Abstract base class for LLM provider integrations.

    Every provider MUST implement:
    - ``analyze()``         -- send prompt, get text response
    - ``count_tokens()``    -- count tokens in a text string
    - ``get_cost()``        -- calculate cost from token counts
    - ``model_name``        -- property returning the active model identifier

    Optional override:
    - ``analyze_streaming()`` -- streaming variant (default raises NotImplementedError)
    """

    @abstractmethod
    def analyze(self, prompt: str, **kwargs: Any) -> str:
        """Send a prompt to the LLM and return the text response.

        Args:
            prompt: The full prompt string to send.
            **kwargs: Provider-specific options (e.g., ``task`` for Gemini).

        Returns:
            The model's response text (stripped).

        Raises:
            RuntimeError: If the provider is not configured or the call fails.
        """

    def analyze_streaming(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Stream a response from the LLM, yielding text chunks.

        Default implementation raises NotImplementedError.  Providers
        that support streaming override this method.

        Args:
            prompt: The full prompt string to send.
            **kwargs: Provider-specific options.

        Yields:
            Text chunks as they arrive from the model.

        Raises:
            NotImplementedError: If the provider does not support streaming.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support streaming yet. "
            "See MCE2-4.1 for streaming implementation."
        )

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: The text to tokenize.

        Returns:
            Token count (always >= 0).
        """

    @abstractmethod
    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for a given number of input/output tokens.

        Uses per-1K-token pricing from the provider's price table.

        Args:
            input_tokens: Number of tokens sent to the model.
            output_tokens: Number of tokens received from the model.

        Returns:
            Cost in USD as a float.
        """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the active model identifier (e.g. 'gemini-2.0-flash')."""


# ---------------------------------------------------------------------------
# GeminiProvider
# ---------------------------------------------------------------------------


class GeminiProvider(LLMProvider):
    """LLMProvider implementation wrapping the existing GeminiAnalyzer.

    Delegates analysis to ``GeminiAnalyzer``, token counting to
    ``token_counter.count_tokens()``, and cost calculation to the
    shared price table.

    Args:
        model: Gemini model identifier.
        max_retries: Retry attempts for API calls (passed to GeminiAnalyzer).
        base_delay: Base backoff delay in seconds (passed to GeminiAnalyzer).
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> None:
        self._model = model
        self._analyzer = GeminiAnalyzer(
            model_name=model,
            max_retries=max_retries,
            base_delay=base_delay,
        )
        logger.info(
            "GeminiProvider initialized: model=%s configured=%s",
            model,
            self._analyzer.is_configured,
        )

    # -- LLMProvider interface -----------------------------------------------

    def analyze(self, prompt: str, **kwargs: Any) -> str:
        """Analyze text using Gemini.

        Requires ``task`` keyword argument matching one of the registered
        Gemini tasks (classify_dna_layer, extract_entities,
        score_source_quality).

        Args:
            prompt: The text to analyze.
            **kwargs: Must include ``task`` (str).

        Returns:
            Model response text.

        Raises:
            GeminiNotConfiguredError: If GOOGLE_API_KEY is not set.
            GeminiAnalysisError: If the call fails after retries.
            ValueError: If ``task`` is missing or invalid.
        """
        task = kwargs.get("task")
        if task is None:
            raise ValueError(
                "GeminiProvider.analyze() requires 'task' keyword argument. "
                "Valid tasks: classify_dna_layer, extract_entities, score_source_quality"
            )
        return self._analyzer.analyze(prompt, task=task)

    def analyze_streaming(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Simulate streaming by splitting a batch response into chunks.

        Calls ``analyze()`` internally and yields the result sentence by
        sentence (splitting on ". ") to simulate streaming behavior.
        This allows the full streaming pipeline to be tested end-to-end
        without requiring the real Gemini streaming API.

        TODO: Replace with real Gemini streaming API integration.
              The google-genai SDK supports ``generate_content(stream=True)``
              which returns an iterator of ``GenerateContentResponse`` chunks.
              When implementing real streaming, replace the body of this
              method while keeping the same Iterator[str] return type.

        Args:
            prompt: The full prompt string to send.
            **kwargs: Must include ``task`` (str) for the underlying analyze().

        Yields:
            Text chunks (sentences) as they would arrive from a streaming API.
        """
        # Get the full batch response first
        full_response = self.analyze(prompt, **kwargs)

        # Simulate streaming by splitting on sentence boundaries.
        # Split on ". " to preserve the period in each chunk, then
        # yield each sentence as a separate chunk.
        sentences = full_response.split(". ")
        for i, sentence in enumerate(sentences):
            is_last = i == len(sentences) - 1
            # Re-attach the period + space except for the last chunk
            if not is_last:
                yield sentence + ". "
            else:
                yield sentence

    def count_tokens(self, text: str) -> int:
        """Count tokens using the shared token_counter module.

        Delegates to ``token_counter.count_tokens()`` which uses tiktoken
        when available, falling back to chars/4 heuristic.

        Args:
            text: The text to tokenize.

        Returns:
            Token count (always >= 0).
        """
        return tc_count_tokens(text, model=self._model)

    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD using the shared price table.

        Args:
            input_tokens: Tokens sent to the model.
            output_tokens: Tokens received from the model.

        Returns:
            Cost in USD.
        """
        prices = PRICE_TABLE.get(self._model, _FALLBACK_PRICE)
        input_cost = (input_tokens / 1000.0) * prices["input"]
        output_cost = (output_tokens / 1000.0) * prices["output"]
        return input_cost + output_cost

    @property
    def model_name(self) -> str:
        """Return the Gemini model identifier."""
        return self._model

    # -- convenience ---------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        """Return True if the underlying GeminiAnalyzer has an API client."""
        return self._analyzer.is_configured

    @property
    def usage(self) -> Any:
        """Access the underlying GeminiAnalyzer's token usage tracker."""
        return self._analyzer.usage

    def __repr__(self) -> str:
        return f"GeminiProvider(model={self._model!r}, " f"configured={self.is_configured})"


# ---------------------------------------------------------------------------
# OpenAIProvider
# ---------------------------------------------------------------------------


class OpenAIProvider(LLMProvider):
    """LLMProvider implementation using OpenAI Chat Completions API.

    Used as Gemini fallback when MCE_LLM_PROVIDER=openai is set.
    Cheaper than gpt-4o for routine extraction (gpt-4o-mini = $0.00015/1K input).

    Story: MCE-16.2

    Args:
        model: OpenAI model identifier (default: gpt-4o-mini).
        max_retries: Retry attempts for API calls.
        base_delay: Base backoff delay in seconds.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> None:
        import os

        self._model = model
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self._client = None

        if self._api_key:
            try:
                from openai import OpenAI

                from engine.intelligence.pipeline.mce.llm_retry import resolve_timeout_s

                # NON-NEGOTIABLE: explicit transport timeout so a stalled TLS
                # keep-alive cannot hang the pipeline. SDK retries disabled (=0)
                # — the shared ``call_with_retry`` in ``analyze()`` owns backoff
                # timing (exp + ±30% jitter + Retry-After), no multiplication.
                self._client = OpenAI(
                    api_key=self._api_key,
                    timeout=resolve_timeout_s(),
                    max_retries=0,
                )
            except ImportError:
                logger.warning("openai package not installed; OpenAIProvider unavailable")

        logger.info(
            "OpenAIProvider initialized: model=%s configured=%s",
            model,
            self.is_configured,
        )

    # -- LLMProvider interface -----------------------------------------------

    def analyze(self, prompt: str, **kwargs: Any) -> str:
        """Analyze text using OpenAI Chat Completions.

        Accepts (and ignores) Gemini-specific ``task`` kwarg for cross-provider
        compatibility. Other kwargs (``temperature``, ``max_tokens``) are passed
        through to the API.

        Args:
            prompt: The text to analyze.
            **kwargs: Optional ``temperature``, ``max_tokens``.
                      ``task`` accepted but ignored (Gemini-specific).

        Returns:
            Model response text (stripped).

        Raises:
            RuntimeError: If OPENAI_API_KEY not set or call fails after retries.
        """
        if self._client is None:
            raise RuntimeError(
                "OpenAIProvider not configured. "
                "Set OPENAI_API_KEY and install `openai` package."
            )

        # Ignore Gemini-specific kwargs
        kwargs.pop("task", None)
        kwargs.pop("structured_schema", None)

        temperature = kwargs.pop("temperature", 0.7)
        max_tokens = kwargs.pop("max_tokens", None)

        from engine.intelligence.pipeline.mce.llm_retry import call_with_retry

        def _one_call() -> str:
            params: dict[str, Any] = {
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            response = self._client.chat.completions.create(**params)
            content = response.choices[0].message.content or ""
            return content.strip()

        # Transient transport errors (timeout/5xx/429/conn) are retried with
        # exponential backoff + ±30% jitter + Retry-After floor (shared math).
        # A permanent error (bad key, invalid request) fails fast. On exhaustion
        # the last exception is re-raised, normalized to RuntimeError so the
        # caller's existing surface (RuntimeError) is preserved.
        try:
            return call_with_retry(
                _one_call, max_attempts=self._max_retries, label="openai-provider"
            )
        except Exception as exc:
            raise RuntimeError(
                f"OpenAIProvider failed after {self._max_retries} attempts: {exc}"
            ) from exc

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken when available, fallback to chars/4."""
        return tc_count_tokens(text, model=self._model)

    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD using PRICE_TABLE."""
        prices = PRICE_TABLE.get(self._model, _FALLBACK_PRICE)
        input_cost = (input_tokens / 1000.0) * prices["input"]
        output_cost = (output_tokens / 1000.0) * prices["output"]
        return input_cost + output_cost

    @property
    def model_name(self) -> str:
        """Return the OpenAI model identifier."""
        return self._model

    # -- convenience ---------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        """Return True if OPENAI_API_KEY is set and client initialized."""
        return self._client is not None and bool(self._api_key)

    def __repr__(self) -> str:
        return f"OpenAIProvider(model={self._model!r}, configured={self.is_configured})"


# ---------------------------------------------------------------------------
# Provider Registry & Factory
# ---------------------------------------------------------------------------

_PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
}


def register_provider(name: str, provider_class: type[LLMProvider]) -> None:
    """Register a new provider class in the factory registry.

    Args:
        name: Short name for the provider (e.g. "claude", "openai").
        provider_class: A class implementing LLMProvider.
    """
    _PROVIDER_REGISTRY[name] = provider_class
    logger.info("Registered LLM provider: %s -> %s", name, provider_class.__name__)


def get_provider(name: str = "gemini", **kwargs: Any) -> LLMProvider:
    """Factory function to create a provider instance by name.

    Args:
        name: Provider name (default: "gemini").
              Must be registered in ``_PROVIDER_REGISTRY``.
        **kwargs: Passed to the provider constructor.

    Returns:
        An initialized LLMProvider instance.

    Raises:
        ValueError: If the provider name is not registered.
    """
    provider_class = _PROVIDER_REGISTRY.get(name)
    if provider_class is None:
        available = sorted(_PROVIDER_REGISTRY.keys())
        raise ValueError(f"Unknown LLM provider {name!r}. " f"Available providers: {available}")
    return provider_class(**kwargs)
