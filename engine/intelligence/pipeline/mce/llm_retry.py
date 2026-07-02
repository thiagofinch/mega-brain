"""Shared LLM transport resilience — timeout + transient-error backoff.

Why this exists
---------------
Every embedding call-site in the ingest path already carries an explicit
timeout plus a jittered backoff loop (``pipeline/embedder.py`` reuses
``pipeline/embed_retry.py``; ``rag/hybrid_index._openai_embed`` and
``rag/embedding_config._openai_embed`` set ``timeout=(10, 120)``). The
**LLM** call-sites did NOT: the Gemini path
(``llm_extractor._run_prompt_via_gemini``), the Anthropic path
(``llm_router._run_anthropic``), the standalone ``GeminiAnalyzer`` and the
``OpenAIProvider`` all blocked on a socket ``read()`` with no ceiling. When
the provider saturated under parallel ingest, the call hung indefinitely
(observed: 7+ min idle on a Cloudflare TLS keep-alive, TCP ESTABLISHED but
no data flow) — the whole pipeline stalled on one un-returning HTTPS call.

Two-stage extraction (now the default ``MCE_EXTRACTION_MODE``) makes this
twice as likely: node pass + edge pass = 2x LLM calls per ingest.

Design boundary (why a thin layer over ``embed_retry``)
-------------------------------------------------------
The *delay math* is identical to the embedding path: exponential backoff
(2s, 4s, 8s, 16s, 32s; capped 60s), ±30% jitter to decorrelate concurrent
workers, ``Retry-After`` parsed as a floor. That math lives in
``embed_retry.compute_retry_delay`` / ``parse_retry_after`` /
``extract_retry_after`` and is REUSED here verbatim (IDS: REUSE > CREATE).

What differs is the *retryable-error predicate*. Embeddings only retry 429
(``embed_retry.is_rate_limit_error``) — a deliberately narrow net so a bad
key / dim mismatch fails fast. LLM transport must ALSO retry the transient
classes that produce the indefinite hang: read/connect timeouts, connection
resets, and 5xx server errors. ``is_transient_llm_error`` widens the net to
those while still treating 4xx-non-429 (bad key, invalid request) as
permanent — fail-fast, never burn retries on a deterministic error.

Terminal contract
------------------
On exhaustion this module RE-RAISES the last exception. Each call-site keeps
its own typed wrapper (``LLMCallFailedError``, ``GeminiAnalysisError``,
``RuntimeError``) which the existing non-blocking callers already catch
(two-stage → single-pass, graphrag → skip, briefing → mechanical). The goal
is fail-FAST-then-loud, never hang.

Constants
---------
``LLM_CALL_TIMEOUT_S`` — the per-call wall-clock ceiling handed to each SDK
client. 60s is generous for a single completion yet bounds the hang. Tunable
via ``MCE_LLM_TIMEOUT_S``.

``MAX_LLM_RETRIES`` — total attempts. 4 (3 retries) balances surviving a
transient blip against not multiplying load during a real outage.
"""

from __future__ import annotations

import logging
import os

# REUSE the proven delay math from the embedding path (DRY — single source of
# truth for backoff schedule, jitter, and Retry-After parsing).
from engine.intelligence.pipeline.embed_retry import (
    compute_retry_delay,
    extract_retry_after,
)

logger = logging.getLogger("mce.llm_retry")

# Per-call transport ceiling. genai/anthropic/openai SDKs each take a client
# timeout; this is the seconds value (callers convert to ms where the SDK
# wants ms, e.g. google-genai HttpOptions).
_DEFAULT_TIMEOUT_S = 60.0
# Total attempts (1 initial + retries). 4 = 1 + 3 retries.
MAX_LLM_RETRIES = 4

# Transient markers in the rendered exception message. These are the classes
# that manifest as the indefinite hang or a recoverable server-side blip.
# 429 is included so the LLM path also honors rate-limit backoff (the embedding
# predicate already covers it; we re-include the marker here for message-only
# matches that don't carry a status code).
_TRANSIENT_MARKERS = (
    "429",
    "Too Many Requests",
    "rate limit",
    "RateLimitError",
    "timeout",
    "timed out",
    "ReadTimeout",
    "ConnectTimeout",
    "ConnectionError",
    "Connection reset",
    "Connection aborted",
    "RemoteDisconnected",
    "Server disconnected",
    "ServiceUnavailable",
    "InternalServerError",
    "APIConnectionError",
    "APITimeoutError",
    "502",
    "503",
    "504",
    "500",
    "overloaded",
    "Overloaded",
)

# Status codes treated as transient (retryable). 429 + the 5xx family.
_TRANSIENT_STATUS = frozenset({429, 500, 502, 503, 504})


def resolve_timeout_s() -> float:
    """Resolve the per-call LLM timeout in seconds (``MCE_LLM_TIMEOUT_S`` env).

    Falls back to :data:`_DEFAULT_TIMEOUT_S` when unset, empty, non-numeric, or
    non-positive — a misconfigured env var must never disable the timeout
    (NON-NEGOTIABLE: a call MUST always carry a finite ceiling).
    """
    raw = os.environ.get("MCE_LLM_TIMEOUT_S", "").strip()
    if not raw:
        return _DEFAULT_TIMEOUT_S
    try:
        val = float(raw)
    except ValueError:
        logger.warning("Ignored invalid MCE_LLM_TIMEOUT_S=%r — using %.1fs", raw, _DEFAULT_TIMEOUT_S)
        return _DEFAULT_TIMEOUT_S
    if val <= 0:
        logger.warning(
            "Ignored non-positive MCE_LLM_TIMEOUT_S=%r — using %.1fs", raw, _DEFAULT_TIMEOUT_S
        )
        return _DEFAULT_TIMEOUT_S
    return val


def is_transient_llm_error(exc: BaseException) -> bool:
    """True when ``exc`` is a transient LLM transport failure worth retrying.

    Retryable = the classes that cause the indefinite hang or a recoverable
    server blip: read/connect timeouts, connection resets, 5xx, and 429.
    Everything else (auth, invalid request, schema error) is permanent — return
    False so the caller re-raises immediately instead of burning retries on a
    deterministic failure.

    Detection order (cheapest first):
      1. structured ``status_code`` / ``status`` on the exc or its cause chain;
      2. rendered-message marker scan.
    """
    cur: BaseException | None = exc
    for _ in range(5):  # bounded cause-chain walk (mirrors embed_retry)
        if cur is None:
            break
        status = getattr(cur, "status_code", None) or getattr(cur, "status", None)
        if status in _TRANSIENT_STATUS:
            return True
        cur = getattr(cur, "__cause__", None) or getattr(cur, "cause", None)

    msg = str(exc).lower()
    return any(marker.lower() in msg for marker in _TRANSIENT_MARKERS)


def call_with_retry(
    fn,
    *,
    max_attempts: int = MAX_LLM_RETRIES,
    sleep=None,
    rng=None,
    label: str = "llm",
):
    """Invoke ``fn()`` with transient-error backoff; re-raise on exhaustion.

    The single resilience loop shared by every LLM transport. ``fn`` is a
    zero-arg callable that performs ONE provider call (the caller closes over
    its prompt/client). On a transient error (:func:`is_transient_llm_error`)
    we sleep :func:`compute_retry_delay` seconds (exp backoff + ±30% jitter,
    Retry-After honored as a floor) and try again, up to ``max_attempts`` total.

    A NON-transient error aborts immediately (no wasted retries on a bad key).
    After the final transient attempt, the last exception is RE-RAISED so the
    call fails fast-and-loud rather than hanging — the caller's existing
    fallback (two-stage → single, graphrag → skip, briefing → mechanical)
    handles it non-blocking.

    Args:
        fn: zero-arg callable performing one provider call.
        max_attempts: total attempts (default :data:`MAX_LLM_RETRIES`).
        sleep: injectable sleeper (defaults to ``time.sleep``) — tests pass a
            recorder to assert delays without real waits.
        rng: injectable ``random.Random`` for deterministic jitter in tests.
        label: short tag for log lines (e.g. provider name).

    Returns:
        Whatever ``fn()`` returns on the first success.

    Raises:
        The last exception from ``fn()`` — typed by the caller's own wrapper —
        when attempts are exhausted or the error is non-transient.
    """
    if sleep is None:
        import time

        sleep = time.sleep

    last_exc: BaseException | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            # Permanent error → fail fast, do not waste the remaining attempts.
            if not is_transient_llm_error(exc):
                raise
            # Transient on the final attempt → exhausted; re-raise to caller.
            if attempt >= max_attempts - 1:
                logger.error(
                    "%s call exhausted %d attempts (last: %s)",
                    label,
                    max_attempts,
                    exc,
                )
                raise
            retry_after = extract_retry_after(exc)
            delay = compute_retry_delay(attempt, retry_after=retry_after, rng=rng)
            logger.warning(
                "%s call transient failure (%s) — retrying in %.2fs (attempt %d/%d)",
                label,
                type(exc).__name__,
                delay,
                attempt + 1,
                max_attempts,
            )
            sleep(delay)

    # Unreachable — the loop either returns, raises non-transient, or re-raises
    # on the final attempt. Kept as a defensive belt for static analyzers.
    if last_exc is not None:  # pragma: no cover
        raise last_exc
    raise RuntimeError(f"{label} call_with_retry exited without result")  # pragma: no cover


__all__ = [
    "MAX_LLM_RETRIES",
    "call_with_retry",
    "is_transient_llm_error",
    "resolve_timeout_s",
]
