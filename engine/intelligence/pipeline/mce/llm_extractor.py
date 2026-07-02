"""
llm_extractor.py -- Free-form Gemini wrapper for MCE LLM-driven steps
=====================================================================

Why this exists
---------------
``gemini_analyzer.py`` is a hardened wrapper for FIXED-task classification
prompts (``classify_dna_layer``, ``extract_entities``, etc). The MCE
extraction stages (insights, behavioral, identity, voice) need to send
arbitrary prompts assembled from templates under
``engine/templates/phases/`` and parse JSON responses, so the
fixed-task gate is in the way.

This helper exposes ONE function: ``run_prompt(prompt: str) -> str`` --
a thin, retry-aware call that:

1. Resolves ``GEMINI_API_KEY`` / ``GOOGLE_API_KEY`` (env first, then
   parses ``.env``) -- matches the pattern in
   ``engine/intelligence/pipeline/video/pipeline.py``.
2. Picks a model (``MCE_LLM_MODEL`` env override, default
   ``gemini-2.0-flash-exp``) -- Flash is sufficient for structured
   text extraction at 5-50¢/M tokens, which is what the MCE budget
   assumes.
3. Retries with exponential backoff on transient failures.
4. Returns the response text stripped of code fences if present.

JSON helper
-----------
``extract_json(text: str) -> dict | list | None`` strips code fences,
finds the outermost JSON envelope, and parses. Returns ``None`` on
unparseable output so callers can fall back gracefully without raising.

Status
------
Added 2026-05-13 as part of G13 (wire Sage LLM extraction). Replaces
the TODO stubs in ``cmd_auto_advance`` for cmd_insights / cmd_entities
/ cmd_behavioral / cmd_identity / cmd_voice.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("mce.llm_extractor")

_DEFAULT_MODEL = "gemini-2.5-flash"
# Retry policy (attempts + backoff) is now owned by ``mce.llm_retry`` so the
# Gemini transport shares the exact exponential-backoff + jitter + Retry-After
# math used by the embedding path (DRY). Legacy ``_MAX_RETRIES``/``_BASE_DELAY_S``
# constants were retired here when ``_run_prompt_via_gemini`` migrated.


class LLMNotConfiguredError(RuntimeError):
    """Raised when no Gemini/Google API key is available."""


class LLMCallFailedError(RuntimeError):
    """Raised when all retries are exhausted."""


def _resolve_api_key() -> str | None:
    """Resolve API key from env, falling back to project .env file.

    Mirrors the pattern used by ``engine/intelligence/pipeline/video/pipeline.py``
    so behaviour is consistent across the codebase.
    """
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key

    # Parse .env at project root.
    root = Path(__file__).resolve().parents[4]
    env_file = root / ".env"
    if not env_file.exists():
        return None
    try:
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            for prefix in ("GEMINI_API_KEY=", "GOOGLE_API_KEY="):
                if line.startswith(prefix):
                    candidate = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if candidate:
                        os.environ.setdefault("GEMINI_API_KEY", candidate)
                        return candidate
    except OSError as exc:
        logger.debug(".env read failed in llm_extractor: %s", exc)
    return None


def _resolve_model() -> str:
    return os.environ.get("MCE_LLM_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL


def is_available() -> bool:
    """Lightweight probe used by callers to gate LLM-heavy work."""
    return _resolve_api_key() is not None


def _run_prompt_via_gemini(prompt: str, *, max_output_tokens: int | None = None) -> str:
    """Send ``prompt`` to Gemini, return raw text.

    This is the LOW-LEVEL Gemini call. New code should prefer
    ``llm_router.run_prompt`` so provider can be swapped via env. The
    legacy ``run_prompt`` shim below delegates here.

    Raises:
        LLMNotConfigured: if no API key is reachable.
        LLMCallFailed: after all retries are exhausted.
    """
    api_key = _resolve_api_key()
    if not api_key:
        msg = "GEMINI_API_KEY/GOOGLE_API_KEY not set -- cannot call LLM"
        raise LLMNotConfiguredError(msg)

    try:
        from google import genai  # type: ignore[import-untyped]
        from google.genai import types as genai_types  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover -- caller decides fallback
        msg = (
            "google-genai library not installed -- "
            "pip install google-genai or fall back to keyword extraction"
        )
        raise LLMNotConfiguredError(msg) from exc

    from engine.intelligence.pipeline.mce.llm_retry import (
        MAX_LLM_RETRIES,
        call_with_retry,
        resolve_timeout_s,
    )

    # NON-NEGOTIABLE: an explicit transport timeout on the client. Without it,
    # google-genai blocks on a socket read() forever when the provider saturates
    # (observed 7+ min TCP-ESTABLISHED hang on a Cloudflare TLS keep-alive under
    # parallel ingest). google-genai HttpOptions.timeout is in MILLISECONDS.
    timeout_ms = int(resolve_timeout_s() * 1000)
    client = genai.Client(
        api_key=api_key,
        http_options=genai_types.HttpOptions(timeout=timeout_ms),
    )
    model = _resolve_model()

    config: dict[str, Any] = {}
    if max_output_tokens:
        config["max_output_tokens"] = max_output_tokens
    config["temperature"] = 0.2  # keep extraction deterministic-ish

    def _one_call() -> str:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(**config) if config else None,
        )
        text = getattr(response, "text", None)
        if text:
            return text.strip()
        # Empty -- permanent for this attempt (not a transient transport error),
        # so it is NOT retried by call_with_retry; surface as a typed failure.
        raise LLMCallFailedError("Gemini returned empty text")

    # Transient transport errors (timeout / 5xx / 429 / conn reset) are retried
    # with exponential backoff + ±30% jitter + Retry-After floor (shared math).
    # A non-transient error (bad key, empty text) fails fast. On exhaustion the
    # last exception is re-raised — normalized to LLMCallFailedError so callers
    # that catch it (two-stage → single-pass) degrade non-blocking.
    try:
        return call_with_retry(_one_call, max_attempts=MAX_LLM_RETRIES, label="gemini")
    except LLMCallFailedError:
        raise
    except Exception as exc:  # network/quota exhausted
        raise LLMCallFailedError(f"Gemini call failed: {exc}") from exc


def run_prompt(
    prompt: str,
    *,
    max_output_tokens: int | None = None,
    provider: str | None = None,
    step: str | None = None,
    structured_schema: dict | None = None,
) -> str:
    """Backward-compatible shim — delegates to ``llm_router.run_prompt``.

    V2 (2026-05-13): the historical signature ``run_prompt(prompt,
    max_output_tokens=...)`` continues to work unchanged. New kwargs
    (``provider``, ``step``, ``structured_schema``) are passed through to
    the router so callers can opt in to provider selection without a
    second import.

    Errors are normalized: ``LLMNotConfiguredError`` is preserved for the
    no-API-key case (so existing ``try/except LLMNotConfiguredError`` in
    orchestrate.py still works).
    """
    from engine.intelligence.pipeline.mce.llm_router import (
        ProviderUnavailableError,
    )
    from engine.intelligence.pipeline.mce.llm_router import (
        run_prompt as _route,
    )

    try:
        return _route(
            prompt,
            provider=provider,
            step=step,
            structured_schema=structured_schema,
            max_output_tokens=max_output_tokens,
        )
    except ProviderUnavailableError as exc:
        # Preserve the historical error surface — orchestrate.py catches
        # LLMNotConfiguredError to gate downstream behaviour.
        raise LLMNotConfiguredError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Two-stage node-first extraction (STORY-HGA-F1.2 / GAP-HE-003)
# ---------------------------------------------------------------------------
# ADAPT contract: ported from Hyper-Extract
# (git show 4e333f847f1d:hyperextract/types/graph.py)
#   - `_extract_data` dispatcher (:449-466): mode select then prune
#   - `_extract_data_by_two_stage` (:510-571): nodes first, then edges with
#     node context, then global merge
#   - `_prune_dangling_edges` (:624-672): drop edges whose endpoints are not
#     in the node set (consistency check)
#
# Mega-brain divergence vs source: Hyper-Extract is a class with injected
# LangChain Runnables (``node_extractor.batch`` / ``edge_extractor.batch``)
# and pydantic schemas. ``llm_extractor`` is a free-form prompt utility with
# no class state and no schema registry, so the algorithm is reproduced as a
# pure function driven by caller-supplied callables. This keeps the helper
# free of any dependency on ``orchestrate`` internals (slug, chunks,
# INSIGHTS-STATE) — those stay in the orchestrate layer (RNF-F5).
#
# Single-pass remains the DEFAULT path; two-stage is OPT-IN. ``cmd_insights``
# in orchestrate.py decides which to call based on config
# (``MCE_EXTRACTION_MODE``) and routes the two-stage result back through the
# SAME ``_save_insights_state`` writer, so cascading still fires.

from collections.abc import Callable, Sequence  # noqa: E402

EXTRACTION_MODE_SINGLE = "single_pass"
EXTRACTION_MODE_TWO_STAGE = "two_stage"
# STORY-ENABLE-GBRAIN-FULL: default flipped single_pass → two_stage. Two-stage is
# the higher-fidelity extraction (gbrain absorption). The legacy economy path
# stays available via ``MCE_EXTRACTION_MODE=single_pass``. Fail-safe is preserved
# at TWO levels: (1) ``resolve_extraction_mode`` resolves any UNRECOGNIZED value
# to the default — a typo never strands extraction; (2) the two-stage path in
# ``cmd_insights`` is ADDITIVE — it extracts node-insights exactly like single-
# pass, then runs the edge pass inside a try/except that, on LLM-unconfigured /
# network / quota error, logs a warning and KEEPS the node-insights (graceful
# degradation to single-pass output). Flipping the default can never break a run.
_DEFAULT_EXTRACTION_MODE = EXTRACTION_MODE_TWO_STAGE


def resolve_extraction_mode(explicit: str | None = None) -> str:
    """Resolve the extraction mode (two_stage default; single_pass opt-out).

    Precedence: explicit arg > ``MCE_EXTRACTION_MODE`` env > default. The single
    path is requested explicitly via ``single_pass``/``single``/``1``; ANY OTHER
    unrecognized value resolves to the default (two_stage) — a typo never
    silently downgrades fidelity. Runtime fail-safety (two_stage → single on
    error) lives in the two-stage executor, not here.
    """
    raw = (explicit or os.environ.get("MCE_EXTRACTION_MODE") or "").strip().lower()
    if raw in {EXTRACTION_MODE_SINGLE, "single", "single-pass", "singlepass", "1"}:
        return EXTRACTION_MODE_SINGLE
    if raw in {EXTRACTION_MODE_TWO_STAGE, "two-stage", "twostage", "2"}:
        return EXTRACTION_MODE_TWO_STAGE
    return _DEFAULT_EXTRACTION_MODE


def prune_dangling_edges(
    nodes: Sequence[Any],
    edges: Sequence[Any],
    *,
    node_key: Callable[[Any], str],
    edge_endpoints: Callable[[Any], tuple[str, str]],
) -> list[Any]:
    """Drop edges whose endpoints are not present in the node set.

    Faithful port of Hyper-Extract ``_prune_dangling_edges``
    (4e333f847f1d:hyperextract/types/graph.py:624-672). An edge survives only
    when BOTH its source and target keys exist among the extracted nodes;
    otherwise it is a dangling edge and is removed for graph consistency.

    Args:
        nodes: extracted node objects.
        edges: candidate edge objects (may include dangling ones).
        node_key: maps a node to its unique key (mirrors ``node_key_extractor``).
        edge_endpoints: maps an edge to ``(src_key, dst_key)`` (mirrors
            ``nodes_in_edge_extractor``).

    Returns:
        The list of edges whose endpoints strictly exist in ``nodes``.
    """
    valid_node_keys = {node_key(n) for n in nodes}

    refined_edges: list[Any] = []
    dropped_count = 0
    for edge in edges:
        src_key, dst_key = edge_endpoints(edge)
        src_exists = src_key in valid_node_keys
        dst_exists = dst_key in valid_node_keys
        if src_exists and dst_exists:
            refined_edges.append(edge)
        else:
            dropped_count += 1
            logger.debug(
                "Pruning dangling edge: %s -> %s (src_exists=%s, dst_exists=%s)",
                src_key,
                dst_key,
                src_exists,
                dst_exists,
            )

    if dropped_count > 0:
        logger.info(
            "Pruned %d dangling edges to ensure graph consistency.", dropped_count
        )
    return refined_edges


def extract_two_stage(
    *,
    extract_nodes: Callable[[], Sequence[Any]],
    extract_edges: Callable[[Sequence[Any]], Sequence[Any]],
    node_key: Callable[[Any], str],
    edge_endpoints: Callable[[Any], tuple[str, str]],
) -> dict[str, list[Any]]:
    """Run node-first two-stage extraction, then prune dangling edges.

    Faithful port of Hyper-Extract ``_extract_data`` (mode=two_stage path) +
    ``_extract_data_by_two_stage`` (4e333f847f1d:graph.py:449-571), reduced to
    a pure function:

      1. Extract nodes (``extract_nodes``).
      2. Extract edges WITH the extracted nodes as context
         (``extract_edges(nodes)``) — this is the "node context" step that the
         single-pass cannot do (the model sees the entity set before it is
         asked for relations).
      3. Prune dangling edges so the returned graph is internally consistent.

    Chunking/batching is the caller's concern (it owns the prompt assembly and
    the LLM transport), exactly like Hyper-Extract delegates batching to the
    injected Runnables. This helper owns ONLY the two-stage ordering + the
    consistency check.

    Returns:
        ``{"nodes": [...], "edges": [...]}`` — edges already pruned. The caller
        merges this back into INSIGHTS-STATE via the normal orchestrate writer.
    """
    logger.debug("stage=two_stage_start")

    nodes = list(extract_nodes())
    logger.debug("stage=two_stage_node_extraction_complete total_nodes=%d", len(nodes))

    raw_edges = list(extract_edges(nodes))
    logger.debug("stage=two_stage_edge_extraction_complete total_edges=%d", len(raw_edges))

    edges = prune_dangling_edges(
        nodes,
        raw_edges,
        node_key=node_key,
        edge_endpoints=edge_endpoints,
    )
    logger.debug(
        "stage=two_stage_complete nodes=%d edges=%d (pruned %d)",
        len(nodes),
        len(edges),
        len(raw_edges) - len(edges),
    )
    return {"nodes": nodes, "edges": edges}


_FENCE_RE = re.compile(r"^```(?:json|yaml)?\s*\n?|\n?```\s*$", re.MULTILINE)


def extract_json(text: str) -> Any:
    """Best-effort JSON parser for Gemini output.

    Strips ```json fences, finds the outermost {...} or [...] envelope,
    and parses. Returns ``None`` if no valid JSON is recoverable.
    """
    if not text:
        return None
    cleaned = _FENCE_RE.sub("", text).strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fall back: scan for the largest balanced JSON object/array.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        end = cleaned.rfind(closer)
        if start != -1 and end != -1 and end > start:
            candidate = cleaned[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    return None
