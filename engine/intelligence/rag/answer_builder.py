#!/usr/bin/env python3
"""PRODUCTION ANSWER-BUILDER — STORY-GBA-W3.1
================================================

The MISSING synthesis floor of the RAG response path.

Until this module, the anti-hallucination gate built by STORY-GBA-W1.2
(``pipeline.attach_verification``) + STORY-GBA-F4.1 (block-vs-flag decision)
was a **vault without a door**: fully constructed, fail-safe, fully tested —
but NO production prose generator ever invoked it. ``pipeline.query`` only
fuses retrieval context (no LLM); ``query_orchestrator.query_full`` returns
ranked chunks (no synthesis). The single real prose generator in the Python
tree (``engine/jarvis/voice/orchestrator.py``) feeds on SYSTEM context, not a
RAG ``PipelineResult`` (W1.2 Completion Notes §Ressalvas) — out of scope.

This builder closes that gap. The production-grade target path (story §"Caminho
-alvo de produção"):

    query (str)
       │
       ▼
    pipeline.query(query_text)  ───────────▶ PipelineResult (.results = chunks)
       │                                            │
       ▼                                            │
    synthesize_prose(query, PipelineResult)  ◀──────┘   (LLM grounded ONLY in
       │                                                  the chunks; fail-open)
       ▼  response (str, prose)
    attach_verification(response, pipeline_result)   (pipeline.py:256 — the W1.2
       │                                              + F4.1 gate; SOLE faithful-
       ▼                                              ness decision point)
    dict verificado  →  respeita block (delivered:False) / flag (delivered:True)

⭐ LOAD-BEARING INVARIANT — FAIL-OPEN (mirrors ``query_expansion._llm_expand``
   at ``engine/intelligence/rag/query_expansion.py:148``)
---------------------------------------------------------------------------
Synthesis is best-effort. ANY generation-edge failure (no ``OPENAI_API_KEY``,
timeout, HTTP error, invalid JSON, empty context, provider hiccup) degrades to
an EXTRACTIVE answer assembled from the retrieved chunks — it NEVER raises and
NEVER breaks the response path. The degrade is flagged in the returned dict
(``synthesis_mode: "extractive_fallback"``). An LLM synthesis floor that can
derail the response path on a provider hiccup is the exact anti-pattern this
story rejects.

RNF-1 (caixa-preta): this module is a pure CONSUMER. It imports ``pipeline``
and calls ``query`` / ``attach_verification`` with their signatures intact. It
NEVER reads or writes ``hhem_gate.py``, ``self_rag``'s threshold, or any of the
6 other protected files. ``attach_verification`` is the ONLY faithfulness
decision point — this builder never re-implements a threshold.

Provider: OpenAI Chat Completions (same provider/discipline as
``query_expansion._llm_expand`` — ``OPENAI_API_KEY``, ANTHROPIC absent). No key
hardcode; no new gateway invented (REUSE > CREATE).

Version: 1.0.0
Story:   STORY-GBA-W3.1
"""

from __future__ import annotations

import argparse
import sys

from engine.config import get_config
from engine.intelligence.rag import pipeline

# --- synthesis model + timeout (mirror query_expansion discipline) ----------
# gbrain/query_expansion default synthesis slot is openai gpt-4o-mini. We keep
# the same canonical small model; an operator can override via config without a
# code change (same lazy-read discipline as RAG_EXPANSION_MODEL).
DEFAULT_SYNTHESIS_MODEL = "gpt-4o-mini"

# (connect, read) timeout — mirrors EXPANSION_TIMEOUT=(5,20) at
# query_expansion.py:62. A stalled socket fail-opens (extractive fallback)
# instead of hanging the whole response path (AC5).
SYNTHESIS_TIMEOUT = (5, 20)

# How many chunks of grounding evidence to inject into the synthesis prompt.
# Bounded so the prompt stays within budget; the retriever already ranked them.
MAX_GROUNDING_CHUNKS = 8

# Per-chunk character cap so one huge chunk can't blow the prompt budget.
MAX_CHUNK_CHARS = 1200

# Extractive-fallback assembly bound (chars) — keeps the degraded answer sane.
MAX_EXTRACTIVE_CHARS = 2000


# ---------------------------------------------------------------------------
# CHUNK TEXT EXTRACTION
# ---------------------------------------------------------------------------
def _chunk_text(result: dict) -> str:
    """Extract the chunk text from a single ``PipelineResult.results`` entry.

    Mirrors EXACTLY how ``pipeline.verify()`` reads chunk text
    (``pipeline.py:162-166``): prefer ``text``, then ``text_preview``, then
    ``label``. Using the same key precedence guarantees the prose is grounded in
    the SAME text the faithfulness scorer will check it against — otherwise we
    could ground on one field and be scored against another.
    """
    if not result:
        return ""
    return str(result.get("text", result.get("text_preview", result.get("label", "")))).strip()


def _grounding_chunks(pipeline_result: pipeline.PipelineResult) -> list[str]:
    """Collect the non-empty chunk texts that will ground the synthesis.

    Capped at MAX_GROUNDING_CHUNKS and per-chunk MAX_CHUNK_CHARS. These are the
    ONLY evidence the LLM is allowed to use (AC2 — no parametric knowledge).
    """
    chunks: list[str] = []
    for r in pipeline_result.results:
        text = _chunk_text(r)
        if not text:
            continue
        if len(text) > MAX_CHUNK_CHARS:
            text = text[:MAX_CHUNK_CHARS]
        chunks.append(text)
        if len(chunks) >= MAX_GROUNDING_CHUNKS:
            break
    return chunks


# ---------------------------------------------------------------------------
# GROUNDED SYNTHESIS (LLM) — fail-open INNER, mirrors query_expansion._llm_expand
# ---------------------------------------------------------------------------
def synthesize_prose(query: str, pipeline_result: pipeline.PipelineResult) -> str | None:
    """Synthesize a prose answer grounded EXCLUSIVELY in the retrieved chunks.

    Literal discipline port of ``query_expansion._llm_expand``
    (``query_expansion.py:148``): reads ``OPENAI_API_KEY`` via config, calls
    OpenAI Chat Completions with a bounded timeout, and on ANY failure returns
    ``None`` (the INNER fail-open signal) so the orchestrator can degrade to an
    extractive answer. NEVER raises.

    The prompt injects ONLY the chunk evidence and instructs the model to answer
    strictly from it (AC2 grounding prompt). If there is NO evidence to ground
    on, we return ``None`` rather than inviting the model to hallucinate from
    parametric knowledge — the extractive fallback (which is honest about having
    no synthesis) takes over.

    Returns:
        The synthesized prose string, or ``None`` to signal fallback.
    """
    api_key = get_config("OPENAI_API_KEY")
    if not api_key:
        # Mirror query_expansion: no provider available => signal fallback.
        return None

    chunks = _grounding_chunks(pipeline_result)
    if not chunks:
        # No grounding evidence => do NOT let the LLM invent from parametric
        # knowledge (AC2). Signal fallback; the extractive path is honest.
        return None

    model = get_config("RAG_SYNTHESIS_MODEL", default=DEFAULT_SYNTHESIS_MODEL)

    evidence = "\n\n".join(f"[Chunk {i + 1}]\n{c}" for i, c in enumerate(chunks))
    prompt = "\n".join(
        [
            "You are a careful assistant. Answer the user's question using ONLY "
            "the evidence chunks provided below.",
            "Ground every statement in the chunks. Do NOT add facts that are not "
            "present in the evidence. Do NOT use outside/parametric knowledge.",
            "If the evidence does not contain the answer, say so plainly instead "
            "of inventing one.",
            "Write a direct, coherent prose answer (no bullet lists unless the "
            "evidence is itself a list). Match the language of the question.",
            "",
            "=== EVIDENCE (the ONLY source you may use) ===",
            evidence,
            "=== END EVIDENCE ===",
            "",
            f"Question: {query}",
            "Answer (grounded strictly in the evidence above):",
        ]
    )

    try:
        import requests

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=SYNTHESIS_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            return None
        return content.strip()
    except Exception:
        # INNER fail-open (mirrors query_expansion._llm_expand): synthesis is
        # best-effort; any error => None => extractive fallback. Never raises.
        return None


# ---------------------------------------------------------------------------
# EXTRACTIVE FALLBACK — honest degrade from the retrieved context
# ---------------------------------------------------------------------------
def _extractive_answer(pipeline_result: pipeline.PipelineResult) -> str:
    """Assemble an extractive answer from the retrieved chunks/context.

    Used when synthesis is unavailable (no key / timeout / error / empty
    context). It is deliberately a faithful echo of the retrieved evidence —
    grounded by construction, so it can only pass (or be flagged) at the gate,
    never falsely block. Honest degrade: it surfaces what was actually
    retrieved instead of an invented prose answer.
    """
    chunks = _grounding_chunks(pipeline_result)
    if chunks:
        body = "\n\n".join(chunks)
    else:
        # Last resort: the fused context (may itself be empty — that's fine,
        # the gate fail-opens on an unknown score for an empty response path).
        body = (pipeline_result.context or "").strip()
    if len(body) > MAX_EXTRACTIVE_CHARS:
        body = body[:MAX_EXTRACTIVE_CHARS]
    return body


# ---------------------------------------------------------------------------
# PUBLIC API — build_answer
# ---------------------------------------------------------------------------
def build_answer(
    query: str,
    *,
    agent_id: str | None = None,
    buckets: list[str] | None = None,  # STORY-RAG-ANSWER-BUCKET-ROUTING: now ACTIVE
    pipeline_name: str | None = None,
    include_memory: bool = True,
) -> dict:
    """Production answer-builder: grounded synthesis + mandatory verification.

    The synthesis floor STORY-GBA-W3.1 adds. Orchestrates the target path:

      1. ``pipeline.query(...)`` (``pipeline.py:46``) → grounded
         ``PipelineResult`` (the ``.results`` chunks are the source of truth).
      2. ``synthesize_prose(query, pipeline_result)`` → prose grounded ONLY in
         those chunks (AC2). On ``None`` (LLM down / no key / empty context /
         error), degrade to ``_extractive_answer`` (AC4 fail-open).
      3. ``pipeline.attach_verification(response, pipeline_result)``
         (``pipeline.py:256``) → the SOLE faithfulness decision; returns the
         verified dict, honoring block (``delivered:False``) / flag
         (``delivered:True``). This builder NEVER re-implements the threshold
         (AC3).

    The returned dict is the ``attach_verification`` dict (response /
    verification / verification_action / delivered / [blocked_response /
    blocked / block_threshold]) PLUS builder metadata:

        {
            ...attach_verification fields...,
            "query": str,
            "synthesis_mode": "llm" | "extractive_fallback",
            "chunk_count": int,
            "pipeline": str,
        }

    NEVER raises on the generation edge — fail-open is the contract (AC4).

    Args:
        query: The user question.
        agent_id: Optional agent for memory lookup (passed to pipeline.query).
        buckets: Knowledge bucket(s) to retrieve from. STORY-RAG-ANSWER-BUCKET-
            ROUTING activates this (was reserved/no-op): the FIRST bucket is
            threaded into ``pipeline.query(bucket=...)`` so the answer chain
            reaches the requested index. ``None`` defaults to ``"external"``
            (backward-compat). Multi-bucket fusion is OUT of scope for this story
            — ``buckets[0]`` is the explicit single bucket honored.
        pipeline_name: Optional forced retrieval pipeline (A/B/C/D/E).
        include_memory: Whether pipeline.query includes agent/shared memory.
    """
    # Resolve the single retrieval bucket from the (now-active) buckets arg.
    # buckets[0] when provided, else the legacy default "external". Multi-bucket
    # fusion is intentionally OUT of scope (story §OUT) — one explicit bucket.
    bucket = buckets[0] if buckets else "external"

    # Step 1: grounded retrieval. pipeline.query is itself robust; if it were to
    # fail we still must not break the response path, so we guard it and degrade
    # to an empty PipelineResult (the gate fail-opens on an empty/unknown path).
    try:
        pipeline_result = pipeline.query(
            query,
            agent_id=agent_id,
            pipeline=pipeline_name,
            include_memory=include_memory,
            bucket=bucket,
        )
    except Exception:
        pipeline_result = pipeline.PipelineResult(
            query=query,
            intent="unknown",
            pipeline="?",
            pipeline_name="?",
            context="",
        )

    # Step 2: grounded synthesis with fail-open degrade to extractive.
    synthesis_mode = "llm"
    prose = synthesize_prose(query, pipeline_result)
    if prose is None:
        synthesis_mode = "extractive_fallback"
        prose = _extractive_answer(pipeline_result)

    # Step 3: MANDATORY verification — the SOLE faithfulness decision point
    # (AC3). attach_verification is itself belt-and-suspenders non-raising, but
    # we guard once more so the builder can NEVER break the response path.
    try:
        verified = pipeline.attach_verification(prose, pipeline_result)
    except Exception:
        # Ultra-defensive: shape a flag-equivalent verified dict so callers can
        # always branch on the same keys. (attach_verification already never
        # raises; this is pure Art. XII spirit insurance.)
        verified = {
            "response": prose,
            "verification": {
                "faithfulness": -1.0,
                "verdict": "unknown",
                "hhem_triggered": False,
                "hallucination_warning": False,
                "error": "attach_verification_failed",
            },
            "verification_action": "flag",
            "delivered": True,
        }

    # Annex builder metadata WITHOUT touching the gate's keys (no override of
    # response / verification / verification_action / delivered).
    verified["query"] = query
    verified["synthesis_mode"] = synthesis_mode
    verified["chunk_count"] = pipeline_result.chunk_count
    verified["pipeline"] = pipeline_result.pipeline
    return verified


# ---------------------------------------------------------------------------
# CLI (Constitution Art. I — CLI First) — AC7
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    """Entry CLI: ``python3 -m engine.intelligence.rag.answer_builder "<query>"``.

    Exercises ``build_answer`` end-to-end and prints the verified result: the
    delivered prose, the faithfulness verdict, the block/flag action, and the
    synthesis mode. The feature is exercisable from the CLI BEFORE any UI.
    """
    parser = argparse.ArgumentParser(
        prog="python3 -m engine.intelligence.rag.answer_builder",
        description="Grounded answer-builder with mandatory anti-hallucination verification.",
    )
    parser.add_argument("query", help="The question to answer (grounded in retrieved chunks).")
    parser.add_argument("--agent", dest="agent_id", default=None, help="Agent id for memory lookup.")
    parser.add_argument(
        "--bucket",
        dest="buckets",
        action="append",
        default=None,
        help="Knowledge bucket to retrieve from: external|business|personal "
        "(default external). The first --bucket is the active retrieval bucket.",
    )
    parser.add_argument(
        "--pipeline",
        dest="pipeline_name",
        default=None,
        help="Force retrieval pipeline A/B/C/D/E (auto-selects if omitted).",
    )
    parser.add_argument(
        "--no-memory",
        dest="include_memory",
        action="store_false",
        help="Disable agent/shared memory in retrieval.",
    )
    args = parser.parse_args(argv)

    out = build_answer(
        args.query,
        agent_id=args.agent_id,
        buckets=args.buckets,
        pipeline_name=args.pipeline_name,
        include_memory=args.include_memory,
    )

    verification = out.get("verification", {})
    sep = "=" * 60
    print(f"\n{sep}")
    print("ANSWER-BUILDER (grounded synthesis + verification)")
    print(sep)
    print(f"Query           : {out.get('query', args.query)}")
    print(f"Synthesis mode  : {out.get('synthesis_mode', '?')}")
    print(f"Pipeline        : {out.get('pipeline', '?')}")
    print(f"Chunks          : {out.get('chunk_count', 0)}")
    print(f"Faithfulness    : {verification.get('faithfulness', '?')}")
    print(f"Verdict         : {verification.get('verdict', '?')}")
    print(f"Action          : {out.get('verification_action', '?')}")
    print(f"Delivered       : {out.get('delivered', '?')}")
    if out.get("verification_action") == "block":
        print(f"Block threshold : {out.get('block_threshold', '?')}")
    print(f"\n{'-' * 60}\nRESPONSE (delivered):\n{'-' * 60}")
    print(out.get("response", ""))
    if out.get("verification_action") == "block":
        print(f"\n{'-' * 60}\nBLOCKED_RESPONSE (audit, NOT delivered):\n{'-' * 60}")
        print(out.get("blocked_response", ""))
    print(f"\n{sep}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
