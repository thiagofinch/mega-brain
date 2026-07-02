#!/usr/bin/env python3
"""
capability_hint_injector.py -- Capability Hint Injector (MegaBrain)

Hook: UserPromptSubmit

Layered matching pipeline (TIL-12 + TIL-19):

    1. KEYWORD MATCH   (Wave 0 path -- preserved, <5ms budget)
       Substring scan against capability-keyword-index.json.

    2. SEMANTIC FALLBACK (TIL-12 AC1)
       If keyword match returns nothing:
         - load .data/capability-embeddings.npy + meta json
         - embed prompt via OpenAI text-embedding-3-large (canonical)
         - cosine top-1 >= 0.85           -> inject directly (high confidence)
         - 0.60 <= top-1 < 0.85           -> collect top-5, go to step 3
         - top-1 < 0.60                   -> no injection
       Fail-open: missing OPENAI_API_KEY or missing cache => skip semantic
       silently and return keyword-only result.

    3. LLM RE-RANK (TIL-12 AC2)
       Ask Claude API (claude-haiku-4-5) "which of these candidates, if any,
       matches?" with a hard 2s timeout. On timeout or any error, fall back
       to top-1 embedding regardless of score (never block the prompt).

    4. DEFER-LOADING SHAPE (TIL-19 AC3)
       Any capability with `defer_loading: true` is NEVER auto-injected.
       Instead, a SINGLE per-session meta-hint is emitted advising the
       agent to call search_capabilities('your need'). Session sentinel
       at .data/meta-hint-injected-{session_id} ensures one-shot.

Telemetry (TIL-12 AC6):
    Each invocation appends a JSON line to .data/capability-hints-metrics.jsonl
    using the schema documented at docs/architecture/capability-hints-metrics.schema.md.

Fail-open semantics: exit 0 silently on any error or no match. The injector
MUST NEVER block a user prompt.

Story: TIL-12 (semantic + rerank) + TIL-19 (search tool + defer-loading) +
       TIL-21 (OTel GenAI drift detection — PIONEER)

TIL-21 addition:
    Each capability injection emits an OTel-shaped span via the
    engine.intelligence.metrics.otel_capability_tracer module. Spans land in
    `.data/otel/capability-traces-{date}.jsonl`. The tracer is fail-open: if
    `opentelemetry-sdk` is missing OR the file write fails, the hook continues
    silently. AC1.1 latency cap: < 20ms p95 overhead — measured by
    scripts/til-21/tests/test_drift_detection.py::test_latency_overhead.

ADR: ADR-TIL-001 (hooks dir = Python only)
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
INDEX_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-keyword-index.json"
REGISTRY_PATH = PROJECT_ROOT / "agents" / "_registry" / "capability-registry.yaml"
DATA_DIR = PROJECT_ROOT / ".data"
EMB_PATH = DATA_DIR / "capability-embeddings.npy"
META_PATH = DATA_DIR / "capability-embeddings-meta.json"
METRICS_PATH = DATA_DIR / "capability-hints-metrics.jsonl"

# Thresholds (TIL-12 AC1)
HIGH_CONF_THRESHOLD = 0.85
MIN_RERANK_THRESHOLD = 0.60
RERANK_TOP_K = 5

# Budgets (TIL-12 AC5)
LLM_RERANK_TIMEOUT_S = 2.0


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    """Lowercase and strip accents for matching."""
    text = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _prompt_hash(prompt: str) -> str:
    """SHA-256 truncated 12-char of the raw prompt (telemetry, no leak)."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]


def _append_metric(entry: dict) -> None:
    """Append one JSON line to the metrics file. Best-effort, never raise."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with METRICS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _session_id_from_hookdata(hook_data: dict) -> str:
    """Stable session id for one-shot meta-hint tracking."""
    sid = hook_data.get("session_id") or hook_data.get("sessionId")
    if sid:
        return str(sid)[:32]
    # Fallback: PID-stable, lifetime ~ process; safe-ish
    return f"pid-{os.getppid()}"


def _meta_hint_sentinel(session_id: str) -> Path:
    return DATA_DIR / f"meta-hint-injected-{session_id}"


# ---------------------------------------------------------------------------
# Keyword path (Wave 0 -- preserved)
# ---------------------------------------------------------------------------


def load_index() -> dict | None:
    """Load the pre-built keyword index."""
    try:
        with open(INDEX_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def match_capabilities(prompt_normalized: str, index: dict) -> list[dict]:
    """Match keywords against the normalized prompt. Returns unique capability matches."""
    entries = index.get("entries", [])
    resolved = index.get("resolvedCapabilities", {})

    matched = {}
    for entry in entries:
        kw = entry.get("keyword", "")
        cap_id = entry.get("capability_id", "")
        if not kw or not cap_id:
            continue
        if kw in prompt_normalized and cap_id not in matched:
            cap_result = resolved.get(cap_id, {})
            matched[cap_id] = {
                "capability_id": cap_id,
                "matched_keyword": kw,
                "available": cap_result.get("available", False),
                "provider": cap_result.get("resolved_provider", {}),
                "user_action_required": cap_result.get("user_action_required", False),
                "context_cost_estimate": cap_result.get("context_cost_estimate"),
            }

    return list(matched.values())


# ---------------------------------------------------------------------------
# Defer-loading awareness (TIL-19 AC3)
# ---------------------------------------------------------------------------


def _load_registry() -> dict | None:
    """Best-effort YAML load of capability-registry."""
    try:
        import yaml  # PyYAML
    except ImportError:
        return None
    try:
        return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _defer_loading_set(registry: dict | None) -> set[str]:
    """Return set of capability_ids with defer_loading: true."""
    if not registry:
        return set()
    caps = registry.get("capabilities") or {}
    return {cid for cid, c in caps.items() if (c or {}).get("defer_loading") is True}


# ---------------------------------------------------------------------------
# Semantic fallback (TIL-12 AC1, AC4)
# ---------------------------------------------------------------------------


def _semantic_topk(prompt: str, top_k: int = RERANK_TOP_K) -> list[tuple[str, float]] | None:
    """Return [(capability_id, cosine), ...] sorted desc, or None if unavailable.

    Fail-open: returns None when numpy/meta/cache/API key are missing.
    """
    try:
        import numpy as np
    except ImportError:
        return None

    if not EMB_PATH.exists() or not META_PATH.exists():
        return None

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    # Make engine importable
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    try:
        from engine.intelligence.rag.embedding_config import DIMENSIONS, MODEL
        from engine.intelligence.rag.hybrid_index import _openai_embed
    except Exception:
        return None

    try:
        import numpy as np

        matrix = np.load(EMB_PATH)
        with META_PATH.open(encoding="utf-8") as f:
            meta = json.load(f)
        cap_ids = [c["capability_id"] for c in meta.get("capabilities", [])]
        if matrix.shape[0] != len(cap_ids) or matrix.shape[1] != int(DIMENSIONS):
            return None
    except Exception:
        return None

    try:
        prompt_vec = _openai_embed(
            [prompt[:8000]], model=MODEL, api_key=api_key, dimensions=int(DIMENSIONS)
        )
        prompt_arr = np.asarray(prompt_vec[0], dtype=np.float32)
    except Exception:
        return None

    # Cosine similarity (assumes embeddings are L2-normalized by OpenAI)
    try:
        # Normalize defensively
        def _norm(a):
            n = np.linalg.norm(a, axis=-1, keepdims=True)
            n = np.where(n == 0, 1.0, n)
            return a / n

        mat_n = _norm(matrix)
        p_n = _norm(prompt_arr[None, :])[0]
        scores = (mat_n @ p_n).astype(np.float32)
        order = np.argsort(-scores)[:top_k]
        return [(cap_ids[int(i)], float(scores[int(i)])) for i in order]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# LLM re-rank (TIL-12 AC2)
# ---------------------------------------------------------------------------


def rerank_with_llm(
    prompt: str, candidates: list[tuple[str, float]], registry: dict | None
) -> str | None:
    """Ask Claude API which capability best matches. Returns capability_id or None.

    Fail-open with 2s timeout. Never raises.
    """
    if not candidates:
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        import anthropic  # type: ignore
    except ImportError:
        return None

    caps = (registry or {}).get("capabilities") or {}

    lines = [
        "Which of these capabilities, if any, matches what the user needs?",
        f"User prompt: {prompt[:400]}",
        "Candidates:",
    ]
    for cid, _score in candidates:
        c = caps.get(cid) or {}
        desc = (c.get("description") or "").strip()
        bc = c.get("business_context") or {}
        pra_que = (bc.get("pra_que") or "").strip()
        suffix = f" | pra_que: {pra_que}" if pra_que else ""
        lines.append(f"- {cid}: {desc}{suffix}")
    lines.append("Return only the ID of the best match, or 'none' if none match.")
    user_msg = "\n".join(lines)

    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=LLM_RERANK_TIMEOUT_S)
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=64,
            messages=[{"role": "user", "content": user_msg}],
        )
        text_parts = []
        for block in resp.content or []:
            t = getattr(block, "text", None)
            if t:
                text_parts.append(t)
        answer = "".join(text_parts).strip().split()
        if not answer:
            return None
        token0 = answer[0].strip(".,;:'\"`").lower()
        if token0 == "none":
            return None
        # Validate it's actually one of our candidates (avoid hallucinated ids)
        valid_ids = {cid.lower(): cid for cid, _ in candidates}
        return valid_ids.get(token0)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Hint formatting
# ---------------------------------------------------------------------------


def _hint_for_match(match: dict) -> str:
    cap_id = match["capability_id"]
    available = match.get("available", False)
    provider = match.get("provider") or {}
    provider_type = provider.get("type", "unknown") if provider else "unknown"
    provider_id = provider.get("id", "unknown") if provider else "unknown"

    if available:
        return f"[CAPABILITY] {cap_id}: available via {provider_type} ({provider_id})"
    user_action = match.get("user_action_required")
    if user_action and isinstance(user_action, dict):
        return f"[CAPABILITY] {cap_id}: unavailable. {user_action.get('action', '')}"
    return f"[CAPABILITY] {cap_id}: unavailable"


def _hint_from_capability_id(cap_id: str, index: dict, kw_label: str = "semantic") -> str | None:
    """Build a hint line from a capability id by looking up the resolved index."""
    resolved = (index.get("resolvedCapabilities") or {}).get(cap_id, {})
    if not resolved:
        return None
    m = {
        "capability_id": cap_id,
        "matched_keyword": kw_label,
        "available": resolved.get("available", False),
        "provider": resolved.get("resolved_provider", {}),
        "user_action_required": resolved.get("user_action_required", False),
    }
    return _hint_for_match(m)


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------


def main():
    t0 = time.perf_counter()
    match_type = "none"
    chosen_cap_id: str | None = None
    similarity_score: float | None = None
    rerank_used = False

    try:
        raw_input = sys.stdin.read()
        if not raw_input or not raw_input.strip():
            return
        try:
            hook_data = json.loads(raw_input)
        except (json.JSONDecodeError, ValueError):
            return

        prompt = hook_data.get("prompt", hook_data.get("query", ""))
        if not prompt or len(prompt) < 3:
            return

        # Load keyword index (still required for hint formatting + resolved providers)
        index = load_index()
        if not index or not index.get("entries"):
            # Try building the index on-the-fly (first run)
            try:
                import subprocess

                subprocess.run(
                    [
                        sys.executable,
                        str(
                            PROJECT_ROOT / ".claude" / "hooks" / "build_capability_keyword_index.py"
                        ),
                    ],
                    cwd=str(PROJECT_ROOT),
                    capture_output=True,
                    timeout=5,
                )
                index = load_index()
            except Exception:
                pass
            if not index or not index.get("entries"):
                return

        # ---- Defer-loading awareness (TIL-19 AC3) ----
        registry = _load_registry()
        deferred = _defer_loading_set(registry)

        # ---- Step 1: Keyword match ----
        prompt_normalized = normalize_text(prompt)
        keyword_matches = match_capabilities(prompt_normalized, index)

        # Filter out deferred capabilities from auto-injection
        kept = [m for m in keyword_matches if m["capability_id"] not in deferred]
        had_deferred_match = len(keyword_matches) != len(kept)

        hints: list[str] = []

        if kept:
            match_type = "keyword"
            for m in kept:
                hints.append(_hint_for_match(m))
            # Prefer first matched cap for telemetry
            chosen_cap_id = kept[0]["capability_id"]

        # ---- Step 2: Semantic fallback (only if no keyword hit) ----
        if not kept:
            topk = _semantic_topk(prompt, top_k=RERANK_TOP_K)
            if topk:
                # Filter deferred from semantic candidates too
                topk = [(cid, s) for cid, s in topk if cid not in deferred]
            if topk:
                top1_id, top1_score = topk[0]
                similarity_score = top1_score
                if top1_score >= HIGH_CONF_THRESHOLD:
                    match_type = "embedding"
                    chosen_cap_id = top1_id
                    hint = _hint_from_capability_id(top1_id, index, kw_label="semantic")
                    if hint:
                        hints.append(hint)
                elif top1_score >= MIN_RERANK_THRESHOLD:
                    # ---- Step 3: LLM re-rank ----
                    rerank_used = True
                    rerank_pick = rerank_with_llm(prompt, topk, registry)
                    if rerank_pick:
                        match_type = "llm_rerank"
                        chosen_cap_id = rerank_pick
                        hint = _hint_from_capability_id(rerank_pick, index, kw_label="rerank")
                        if hint:
                            hints.append(hint)
                    else:
                        # Fallback to top-1 embedding regardless (never block)
                        match_type = "embedding"
                        chosen_cap_id = top1_id
                        hint = _hint_from_capability_id(top1_id, index, kw_label="semantic")
                        if hint:
                            hints.append(hint)
                # else: top1 < 0.60 -> no injection

        # ---- Step 4: Meta-hint (TIL-19 AC3) ----
        # Inject a single per-session discovery hint if (a) we had no other hints
        # AND there are deferred capabilities OR a deferred keyword match was suppressed.
        session_id = _session_id_from_hookdata(hook_data)
        sentinel = _meta_hint_sentinel(session_id)
        if not hints and (deferred or had_deferred_match):
            if not sentinel.exists():
                try:
                    DATA_DIR.mkdir(parents=True, exist_ok=True)
                    sentinel.touch()
                except Exception:
                    pass
                total = len((registry or {}).get("capabilities") or {}) or len(
                    index.get("resolvedCapabilities") or {}
                )
                hints.append(
                    f"[CAPABILITY] Tool discovery: search_capabilities('your need') "
                    f"-- {total} capabilities indexed."
                )
                if match_type == "none":
                    match_type = "meta_hint"

        # ---- Emit ----
        if hints:
            additional_context = "\n".join(hints)
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "UserPromptSubmit",
                            "additionalContext": additional_context,
                        }
                    }
                )
            )
    except Exception:
        # Fail-open: never block the user
        pass
    finally:
        # Telemetry (best-effort)
        try:
            entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "match_type": match_type,
                "capability_id": chosen_cap_id if chosen_cap_id else "none",
                "similarity_score": similarity_score,
                "rerank_used": rerank_used,
                "latency_ms": round((time.perf_counter() - t0) * 1000.0, 3),
                "prompt_hash": _prompt_hash(
                    locals().get("prompt", "") if "prompt" in locals() else ""
                ),
            }
            _append_metric(entry)
        except Exception:
            pass
        # TIL-21: OTel GenAI span emission (fail-open). Only emit when we
        # actually selected a capability — skipping "none" keeps signal-to-
        # noise high for drift analysis (drift cares about declared vs actual
        # USE, not about prompts that matched nothing).
        try:
            if chosen_cap_id and chosen_cap_id != "none":
                if str(PROJECT_ROOT) not in sys.path:
                    sys.path.insert(0, str(PROJECT_ROOT))
                from engine.intelligence.metrics.otel_capability_tracer import (
                    emit_capability_span,
                )

                # Resolve description from registry (best-effort)
                try:
                    reg = _load_registry()
                    caps = (reg or {}).get("capabilities") or {}
                    cap_obj = caps.get(chosen_cap_id) or {}
                    cap_desc = cap_obj.get("description") or ""
                except Exception:
                    cap_desc = ""

                emit_capability_span(
                    capability_id=chosen_cap_id,
                    capability_description=cap_desc,
                    prompt=locals().get("prompt", "") if "prompt" in locals() else "",
                    match_type=match_type,
                    similarity_score=similarity_score,
                    extra_attrs={"til.rerank_used": rerank_used},
                )
        except Exception:
            # Fail-open — never block the user prompt
            pass


if __name__ == "__main__":
    main()
