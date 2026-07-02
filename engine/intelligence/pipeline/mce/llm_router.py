"""llm_router.py -- Pluggable LLM router for MCE pipeline steps
==================================================================

Why this exists
---------------
Every LLM call in the MCE pipeline used to go straight to Gemini Flash via
``llm_extractor.run_prompt``. That meant:

  - No way to swap providers without editing source (paralelização blocked).
  - No prompt caching (Anthropic SDK supports ephemeral 5min cache; reuse
    of long system prompts pays full input cost every time on Gemini).
  - No structured output via Anthropic ``tool_use`` (more deterministic
    than relying on Gemini's JSON-mode being well-behaved).
  - Latency for Sage steps (~3s per insight extraction call) is the
    single biggest contributor to MCE wall-clock time. Anthropic Haiku 4.5
    runs the same prompt in ~500ms.

This module exposes a thin abstraction:

  >>> router = LLMRouter()
  >>> router.run_prompt("Hi", provider="anthropic")
  '...response...'

Selection priority (highest first):

  1. Explicit ``provider=`` argument on the call.
  2. Env override per step: ``MCE_LLM_{STEP_UPPER}`` (e.g.
     ``MCE_LLM_INSIGHTS=anthropic`` redirects Sage.insight_extraction).
  3. Env default: ``MCE_LLM_PROVIDER`` (e.g. ``anthropic``).
  4. Built-in default: ``gemini`` (backward compat — preserves existing
     behaviour for all callers that haven't migrated yet).

The router never raises ``ImportError`` for a missing SDK — it falls back
to the configured default if the requested provider is unavailable. This
keeps tests/CI green even on machines that pinned only one provider.

Supported providers
-------------------
  - ``gemini``     -- google-genai (existing path; reused via llm_extractor)
  - ``anthropic``  -- anthropic SDK (Haiku 4.5 by default)
  - ``openai``     -- openai SDK (gpt-4o-mini by default)

Each provider exposes the same logical contract:
  - ``text``: str input (the assembled prompt)
  - ``structured_schema``: optional JSON-schema dict for structured output
  - Returns: raw text response (str).

Status
------
Added 2026-05-13 as part of V2 (Frente 2 of MCE 7→12 validation roadmap).
``llm_extractor.run_prompt`` now delegates here; existing call-sites work
unchanged with Gemini as default.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("mce.llm_router")


# ─────────────────────────────────────────────────────────────────────────────
# Defaults
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_PROVIDER = "gemini"
_VALID_PROVIDERS = ("gemini", "anthropic", "openai")

_ANTHROPIC_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_OPENAI_DEFAULT_MODEL = "gpt-4o-mini"
# Gemini default model is owned by llm_extractor (MCE_LLM_MODEL env).


# ─────────────────────────────────────────────────────────────────────────────
# Errors
# ─────────────────────────────────────────────────────────────────────────────


class LLMRouterError(RuntimeError):
    """Base class for router-level errors."""


class ProviderUnavailableError(LLMRouterError):
    """Raised when the requested provider has no usable SDK or credentials.

    The router catches this internally and falls back to the configured
    default; callers will only see it if BOTH the requested provider AND
    the fallback are unavailable.
    """


# ─────────────────────────────────────────────────────────────────────────────
# Provider resolution
# ─────────────────────────────────────────────────────────────────────────────


def _step_env_var(step: str | None) -> str | None:
    """Map a step name to its env var (e.g. 'insights' -> 'MCE_LLM_INSIGHTS')."""
    if not step:
        return None
    cleaned = step.strip().upper().replace("-", "_").replace(".", "_")
    return f"MCE_LLM_{cleaned}"


def _resolve_provider(
    *,
    explicit: str | None,
    step: str | None,
) -> str:
    """Apply selection priority: explicit > step env > global env > default."""
    if explicit:
        normalized = explicit.strip().lower()
        if normalized not in _VALID_PROVIDERS:
            raise ValueError(f"Unknown provider {explicit!r} — expected one of {_VALID_PROVIDERS}")
        return normalized

    step_var = _step_env_var(step)
    if step_var:
        v = os.environ.get(step_var)
        if v:
            v = v.strip().lower()
            if v in _VALID_PROVIDERS:
                return v
            logger.warning(
                "Ignored invalid %s=%r — expected one of %s", step_var, v, _VALID_PROVIDERS
            )

    v = os.environ.get("MCE_LLM_PROVIDER", "").strip().lower()
    if v:
        if v in _VALID_PROVIDERS:
            return v
        logger.warning(
            "Ignored invalid MCE_LLM_PROVIDER=%r — expected one of %s", v, _VALID_PROVIDERS
        )

    return _DEFAULT_PROVIDER


# ─────────────────────────────────────────────────────────────────────────────
# Gemini  (delegates to llm_extractor — preserves backward compat)
# ─────────────────────────────────────────────────────────────────────────────


def _run_gemini(
    prompt: str,
    *,
    max_output_tokens: int | None = None,
    structured_schema: dict | None = None,
) -> str:
    """Call Gemini via the existing llm_extractor.run_prompt.

    ``structured_schema`` is accepted but ignored on the Gemini path — the
    existing llm_extractor wraps a free-form text call. Callers that need
    Gemini structured output should keep using gemini_analyzer.py for the
    fixed-task surface.
    """
    from engine.intelligence.pipeline.mce import llm_extractor

    return llm_extractor._run_prompt_via_gemini(prompt, max_output_tokens=max_output_tokens)


# ─────────────────────────────────────────────────────────────────────────────
# Anthropic
# ─────────────────────────────────────────────────────────────────────────────


def _resolve_anthropic_key() -> str | None:
    """Resolve Anthropic API key. Env first, fall back to .env at project root."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    from pathlib import Path

    root = Path(__file__).resolve().parents[4]
    env_file = root / ".env"
    if not env_file.exists():
        return None
    try:
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("ANTHROPIC_API_KEY="):
                candidate = line.split("=", 1)[1].strip().strip('"').strip("'")
                if candidate:
                    os.environ.setdefault("ANTHROPIC_API_KEY", candidate)
                    return candidate
    except OSError as exc:
        logger.debug(".env read failed for Anthropic key: %s", exc)
    return None


def _run_anthropic(
    prompt: str,
    *,
    max_output_tokens: int | None = None,
    structured_schema: dict | None = None,
    model: str | None = None,
) -> str:
    """Call Anthropic Claude Haiku (default) and return the text response.

    Prompt caching: the assembled prompt is sent as a single user message
    with ``cache_control=ephemeral``. Repeated calls inside the 5min TTL
    window reuse cached tokens (Anthropic charges only ~10% of input cost
    on cache hits). Per-step prompt templates therefore amortize nicely.

    Structured output: when ``structured_schema`` is provided, the prompt
    is wrapped in a ``tool_use`` definition so Claude is guaranteed to
    return JSON matching the schema. We then materialize the tool input
    as a JSON string and return it (callers can pass it to
    ``extract_json`` or parse directly).
    """
    api_key = _resolve_anthropic_key()
    if not api_key:
        raise ProviderUnavailableError("ANTHROPIC_API_KEY not set")

    try:
        import anthropic  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ProviderUnavailableError(
            "anthropic SDK not installed — pip install anthropic"
        ) from exc

    from engine.intelligence.pipeline.mce.llm_retry import (
        MAX_LLM_RETRIES,
        call_with_retry,
        resolve_timeout_s,
    )

    chosen_model = (
        model or os.environ.get("MCE_LLM_ANTHROPIC_MODEL", "").strip() or _ANTHROPIC_DEFAULT_MODEL
    )
    max_tok = max_output_tokens or 4096

    # NON-NEGOTIABLE: explicit transport timeout on the client. Without it the
    # Anthropic SDK can block indefinitely on a stalled TLS keep-alive when the
    # provider saturates under parallel ingest (the Cloudflare hang). The SDK's
    # own ``max_retries`` is disabled (=0) so our shared ``call_with_retry`` is
    # the single source of truth for backoff timing (no retry multiplication).
    client = anthropic.Anthropic(
        api_key=api_key,
        timeout=resolve_timeout_s(),
        max_retries=0,
    )

    if structured_schema:
        tool_name = "emit_structured_output"
        # Anthropic input_schema follows JSON-schema dialect.
        tools = [
            {
                "name": tool_name,
                "description": "Emit the structured output for this MCE step.",
                "input_schema": structured_schema,
            }
        ]

        def _structured_call() -> str:
            message = client.messages.create(
                model=chosen_model,
                max_tokens=max_tok,
                tools=tools,
                tool_choice={"type": "tool", "name": tool_name},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                                "cache_control": {"type": "ephemeral"},
                            }
                        ],
                    }
                ],
            )
            # Find the tool_use block.
            for block in message.content or []:
                if getattr(block, "type", None) == "tool_use":
                    import json as _json

                    return _json.dumps(block.input)
            # Should not happen given tool_choice=tool, but fall back gracefully.
            for block in message.content or []:
                if getattr(block, "type", None) == "text":
                    return block.text  # type: ignore[attr-defined]
            return ""

        return call_with_retry(
            _structured_call, max_attempts=MAX_LLM_RETRIES, label="anthropic"
        )

    # Free-form text path
    def _freeform_call() -> str:
        message = client.messages.create(
            model=chosen_model,
            max_tokens=max_tok,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                }
            ],
        )
        for block in message.content or []:
            if getattr(block, "type", None) == "text":
                return (block.text or "").strip()  # type: ignore[attr-defined]
        return ""

    return call_with_retry(_freeform_call, max_attempts=MAX_LLM_RETRIES, label="anthropic")


# ─────────────────────────────────────────────────────────────────────────────
# OpenAI
# ─────────────────────────────────────────────────────────────────────────────


def _resolve_openai_key() -> str | None:
    """Resolve OpenAI API key. Env first, fall back to .env at project root."""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    from pathlib import Path

    root = Path(__file__).resolve().parents[4]
    env_file = root / ".env"
    if not env_file.exists():
        return None
    try:
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("OPENAI_API_KEY="):
                candidate = line.split("=", 1)[1].strip().strip('"').strip("'")
                if candidate:
                    os.environ.setdefault("OPENAI_API_KEY", candidate)
                    return candidate
    except OSError as exc:
        logger.debug(".env read failed for OpenAI key: %s", exc)
    return None


def _run_openai(
    prompt: str,
    *,
    max_output_tokens: int | None = None,
    structured_schema: dict | None = None,
    model: str | None = None,
) -> str:
    """Call OpenAI gpt-4o-mini (default) and return the text response.

    Structured output: when ``structured_schema`` is provided, we use
    ``response_format={"type": "json_schema", ...}`` so the response is
    guaranteed to match the schema (OpenAI's strict structured output).
    Returns the JSON string verbatim; callers can ``json.loads`` it.
    """
    api_key = _resolve_openai_key()
    if not api_key:
        raise ProviderUnavailableError("OPENAI_API_KEY not set")

    try:
        from openai import OpenAI  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ProviderUnavailableError("openai SDK not installed — pip install openai") from exc

    from engine.intelligence.pipeline.mce.llm_retry import (
        MAX_LLM_RETRIES,
        call_with_retry,
        resolve_timeout_s,
    )

    chosen_model = (
        model or os.environ.get("MCE_LLM_OPENAI_MODEL", "").strip() or _OPENAI_DEFAULT_MODEL
    )
    max_tok = max_output_tokens or 4096

    # MCE-2.2 hunt: explicit timeout so httpx receive_response_headers cannot
    # stall the pipeline indefinitely (observed live hang in Step 5). The SDK's
    # own retries are disabled (=0) so our shared ``call_with_retry`` owns the
    # backoff timing — exponential + ±30% jitter + Retry-After floor, identical
    # to the Gemini/Anthropic/embedding paths (no retry multiplication).
    client = OpenAI(api_key=api_key, timeout=resolve_timeout_s(), max_retries=0)

    if structured_schema:

        def _structured_call() -> str:
            response = client.chat.completions.create(
                model=chosen_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tok,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "mce_step_output",
                        "schema": structured_schema,
                        "strict": False,
                    },
                },
            )
            choice = response.choices[0]
            return (choice.message.content or "").strip()

        return call_with_retry(_structured_call, max_attempts=MAX_LLM_RETRIES, label="openai")

    def _freeform_call() -> str:
        response = client.chat.completions.create(
            model=chosen_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tok,
        )
        choice = response.choices[0]
        return (choice.message.content or "").strip()

    return call_with_retry(_freeform_call, max_attempts=MAX_LLM_RETRIES, label="openai")


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


class LLMRouter:
    """Stateless router. Picks a provider per call.

    The class is mostly a namespace — it carries no state today. A future
    iteration can add per-provider client caching here without touching
    call-sites.
    """

    def run_prompt(
        self,
        prompt: str,
        *,
        provider: str | None = None,
        step: str | None = None,
        structured_schema: dict | None = None,
        max_output_tokens: int | None = None,
        model: str | None = None,
    ) -> str:
        """Route the prompt to the chosen provider and return raw text.

        Args:
            prompt: Assembled prompt (system + user instructions inline).
            provider: ``gemini`` | ``anthropic`` | ``openai``. If omitted,
                the env-driven selection in ``_resolve_provider`` is used.
            step: Logical step name (e.g. ``insights``, ``behavioral``).
                Used to pick per-step env override
                (``MCE_LLM_{STEP_UPPER}``).
            structured_schema: Optional JSON-schema dict for structured
                output. Honored on anthropic + openai; ignored on gemini
                (gemini path is text-only here; use gemini_analyzer.py
                for fixed-task structured calls).
            max_output_tokens: Optional cap on completion tokens.
            model: Override the per-provider default model.

        Returns:
            The raw text response from the chosen provider. Use
            ``llm_extractor.extract_json`` to parse JSON envelopes.

        Raises:
            ProviderUnavailableError if BOTH the chosen and default
            providers are unavailable.
            ValueError if ``provider`` is an unknown identifier.
        """
        chosen = _resolve_provider(explicit=provider, step=step)
        logger.debug(
            "LLMRouter.run_prompt(step=%s) -> provider=%s schema=%s",
            step,
            chosen,
            "yes" if structured_schema else "no",
        )

        try:
            return self._dispatch(
                chosen,
                prompt,
                max_output_tokens=max_output_tokens,
                structured_schema=structured_schema,
                model=model,
            )
        except ProviderUnavailableError as exc:
            if chosen == _DEFAULT_PROVIDER:
                raise
            logger.warning(
                "Provider %s unavailable (%s) — falling back to %s",
                chosen,
                exc,
                _DEFAULT_PROVIDER,
            )
            return self._dispatch(
                _DEFAULT_PROVIDER,
                prompt,
                max_output_tokens=max_output_tokens,
                structured_schema=structured_schema,
                model=None,  # default-provider keeps its own model selection
            )

    def _dispatch(
        self,
        provider: str,
        prompt: str,
        *,
        max_output_tokens: int | None,
        structured_schema: dict | None,
        model: str | None,
    ) -> str:
        if provider == "gemini":
            return _run_gemini(
                prompt,
                max_output_tokens=max_output_tokens,
                structured_schema=structured_schema,
            )
        if provider == "anthropic":
            return _run_anthropic(
                prompt,
                max_output_tokens=max_output_tokens,
                structured_schema=structured_schema,
                model=model,
            )
        if provider == "openai":
            return _run_openai(
                prompt,
                max_output_tokens=max_output_tokens,
                structured_schema=structured_schema,
                model=model,
            )
        # Defensive — _resolve_provider should never produce anything else.
        raise ValueError(f"Unsupported provider {provider!r}")


# Module-level convenience  ----------------------------------------------------

_router_singleton: LLMRouter | None = None


def get_router() -> LLMRouter:
    global _router_singleton
    if _router_singleton is None:
        _router_singleton = LLMRouter()
    return _router_singleton


def run_prompt(
    prompt: str,
    *,
    provider: str | None = None,
    step: str | None = None,
    structured_schema: dict | None = None,
    max_output_tokens: int | None = None,
    model: str | None = None,
) -> str:
    """Module-level shortcut to ``get_router().run_prompt(...)``."""
    return get_router().run_prompt(
        prompt,
        provider=provider,
        step=step,
        structured_schema=structured_schema,
        max_output_tokens=max_output_tokens,
        model=model,
    )


def resolve_provider(step: str | None = None, explicit: str | None = None) -> str:
    """Public helper — useful for diagnostics + tests."""
    return _resolve_provider(explicit=explicit, step=step)


def is_provider_available(provider: str) -> bool:
    """Cheap probe — returns True if both SDK + credentials are present."""
    provider = provider.strip().lower()
    if provider == "gemini":
        try:
            from engine.intelligence.pipeline.mce.llm_extractor import is_available

            return is_available()
        except Exception:
            return False
    if provider == "anthropic":
        if not _resolve_anthropic_key():
            return False
        try:
            import anthropic  # noqa: F401

            return True
        except ImportError:
            return False
    if provider == "openai":
        if not _resolve_openai_key():
            return False
        try:
            import openai  # noqa: F401

            return True
        except ImportError:
            return False
    return False


__all__ = [
    "LLMRouter",
    "LLMRouterError",
    "ProviderUnavailableError",
    "get_router",
    "is_provider_available",
    "resolve_provider",
    "run_prompt",
]
