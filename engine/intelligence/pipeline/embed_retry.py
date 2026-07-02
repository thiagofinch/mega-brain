"""Shared 429 backoff helper — STORY-GBA-W2.2.

Pure, side-effect-free retry-delay math, extracted so the 5-attempt 429 loop
that already lives in ``rag/hybrid_index.py::_embed_texts`` (rebuild path) is not
duplicated in substance when ported to ``pipeline/embedder.py::embed_chunks``
(ingestion path).

Design boundary (why a helper and not a full shared loop):
    The rebuild loop and the ingestion loop diverge in their TERMINAL behavior —
    rebuild fails OPEN (fills the batch with zero vectors and continues, to keep
    a partial index buildable), while ingestion fails LOUD (raises
    ``EmbeddingFailedError`` so ``pipeline_transaction`` rolls back, per W2.1).
    Sharing the whole loop would force parametrizing the exhaust behavior and the
    embed callable (rebuild uses ``requests`` directly; ingestion uses the OpenAI
    SDK client), which would change ``_embed_texts``'s shape and risk a rebuild
    regression (RNF-1 forbids touching black-box behavior; DRY must not regress).
    So only the genuinely pure piece — the delay computation — is shared here.
    The loop itself is ported inline at each site (form duplicated, math DRY).

Mechanics ported conceptually from gbrain ``src/commands/embed.ts`` @ 4ee530f
(``embedBatchWithBackoff`` / ``parseRetryDelayMs``):
    - exponential backoff base schedule (2s, 4s, 8s, 16s, 32s; capped at 60s),
      matching the existing rebuild loop ``min(2**attempt * 2, 60)``;
    - ±30% jitter so concurrent workers don't resynchronize on the next 429 wave
      (gbrain ``RATE_LIMIT_JITTER = 0.3``);
    - ``Retry-After`` parsed (HTTP-date or delta-seconds) AND the OpenAI-style
      "try again in Xms/Xs" message, used as a FLOOR for the delay (we never wait
      LESS than the server asked).
"""

from __future__ import annotations

import random
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

# Backoff schedule knobs — mirror the existing rebuild loop so the ingestion
# path inherits the SAME exponential ramp the rebuild already proved in prod.
BACKOFF_BASE_SECONDS = 2.0  # delay = BACKOFF_BASE * 2**attempt
BACKOFF_CAP_SECONDS = 60.0  # ceiling regardless of attempt or Retry-After floor
MAX_EMBED_RETRIES = 5  # total attempts (was max_retries=2 on the SDK shim)
RATE_LIMIT_JITTER = 0.3  # ±30% — gbrain D2 herd-decorrelation

# OpenAI-style transient-rate-limit signals (the SDK surfaces 429 as text in the
# exception when the raw client is used). detect both the status code and the
# canonical phrasing.
_RATE_LIMIT_MARKERS = ("429", "Too Many Requests", "rate limit", "RateLimitError")


def is_rate_limit_error(exc: BaseException) -> bool:
    """True when ``exc`` looks like a transient 429 rate-limit.

    Checks (in order, cheapest first):
      1. a structured ``status`` / ``status_code`` == 429 on the exception or its
         ``.cause`` chain (the OpenAI SDK sets ``status_code`` on APIStatusError);
      2. the rendered message contains a known rate-limit marker.
    Non-429 errors return False so the caller re-raises immediately instead of
    burning retries on a permanent failure (bad key, dim mismatch, etc.).
    """
    cur: BaseException | None = exc
    for _ in range(5):  # bounded cause-chain walk (gbrain detect429FromCause)
        if cur is None:
            break
        status = getattr(cur, "status_code", None) or getattr(cur, "status", None)
        if status == 429:
            return True
        cur = getattr(cur, "__cause__", None) or getattr(cur, "cause", None)

    msg = str(exc)
    return any(marker.lower() in msg.lower() for marker in _RATE_LIMIT_MARKERS)


def parse_retry_after(
    value: str | None, *, now: datetime | None = None
) -> float | None:
    """Parse an HTTP ``Retry-After`` header value into seconds.

    Supports the two RFC 7231 forms plus the OpenAI message form:
      - delta-seconds: ``"30"`` → ``30.0``
      - HTTP-date:     ``"Wed, 21 Oct 2026 07:28:00 GMT"`` → seconds until then
      - OpenAI msg:    ``"Please try again in 248ms"`` / ``"... in 1.5s"``

    Returns the number of seconds to wait, or ``None`` when nothing parseable is
    found (caller then relies on the exponential schedule alone). Never returns a
    negative value (an already-elapsed HTTP-date floors at 0.0).
    """
    if not value:
        return None
    value = value.strip()

    # delta-seconds (pure integer)
    if value.isdigit():
        return float(value)

    # OpenAI-style "try again in 248ms" / "try again in 1.5s"
    ms = re.search(r"try again in (\d+)\s*ms", value, re.IGNORECASE)
    if ms:
        return int(ms.group(1)) / 1000.0
    sec = re.search(r"try again in ([\d.]+)\s*s", value, re.IGNORECASE)
    if sec:
        return float(sec.group(1))

    # HTTP-date
    try:
        dt = parsedate_to_datetime(value)
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            ref = now or datetime.now(UTC)
            return max(0.0, (dt - ref).total_seconds())
    except (TypeError, ValueError):
        pass

    return None


def extract_retry_after(exc: BaseException) -> float | None:
    """Best-effort pull of a ``Retry-After`` floor (seconds) from an exception.

    Looks at, in order: a ``response.headers['retry-after']`` on the exception
    (OpenAI SDK ``APIStatusError`` exposes ``.response``), then the rendered
    message (covers the "try again in Xms" phrasing). Returns ``None`` when
    nothing is found.
    """
    # Structured header on the SDK error's response object.
    resp = getattr(exc, "response", None)
    headers = getattr(resp, "headers", None)
    if headers is not None:
        try:
            raw = headers.get("retry-after") or headers.get("Retry-After")
        except AttributeError:
            raw = None
        parsed = parse_retry_after(raw)
        if parsed is not None:
            return parsed

    # Fall back to the message body (OpenAI embeds the hint there).
    return parse_retry_after(str(exc))


def compute_retry_delay(
    attempt: int,
    *,
    retry_after: float | None = None,
    rng: random.Random | None = None,
) -> float:
    """Compute the seconds to sleep before the next retry.

    Algorithm (REUSE of the rebuild ramp + gbrain jitter/Retry-After):
      1. base = min(BACKOFF_BASE * 2**attempt, BACKOFF_CAP)  — exp. backoff;
      2. floor = max(base, retry_after) when the server sent a Retry-After hint —
         we never wait LESS than asked, but the hint is still capped at the ceiling
         to bound a malicious/huge header;
      3. jitter = uniform ±RATE_LIMIT_JITTER (±30%) applied to the floored delay;
      4. result clamped to [0, BACKOFF_CAP * (1 + jitter)] and never negative.

    ``attempt`` is zero-based (attempt 0 = the delay after the FIRST failure).
    ``rng`` is injectable for deterministic tests (defaults to module ``random``).
    """
    r = rng or random
    base = min(BACKOFF_BASE_SECONDS * (2 ** attempt), BACKOFF_CAP_SECONDS)

    floor = base
    if retry_after is not None and retry_after > 0:
        # Respect the server's ask as a floor, but cap it so a bogus header
        # (e.g. Retry-After: 86400) can't stall the pipeline for a day.
        floor = max(base, min(retry_after, BACKOFF_CAP_SECONDS))

    # ±30% jitter: factor in [1 - 0.3, 1 + 0.3].
    jitter_factor = 1.0 + (r.random() * 2 - 1) * RATE_LIMIT_JITTER
    delay = floor * jitter_factor
    return max(0.0, delay)
