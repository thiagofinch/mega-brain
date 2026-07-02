#!/usr/bin/env python3
"""
UNIFIED RAG PIPELINE - The Orchestrator
=========================================
Single entry point that connects:
  adaptive_router -> retrieval -> memory -> fusion -> output

Usage:
    from engine.intelligence.rag.pipeline import query
    result = query("What commission structure should I use?", agent_id="closer")

Versao: 1.0.0
Data: 2026-03-07
"""

import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PipelineResult:
    """Complete result from the unified pipeline."""

    query: str
    intent: str
    pipeline: str  # A/B/C/D/E
    pipeline_name: str
    context: str  # Final fused context for LLM
    rag_context: str = ""  # RAG chunks only
    memory_context: str = ""  # Agent + shared memory only
    results: list[dict] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    latency_ms: float = 0.0
    memory_included: bool = False
    chunk_count: int = 0


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------


def query(
    query_text: str,
    agent_id: str | None = None,
    pipeline: str | None = None,
    max_tokens: int = 8000,
    include_memory: bool = True,
    bucket: str = "external",
) -> PipelineResult:
    """Unified query through the full RAG + Memory pipeline.

    Steps:
        1. Classify intent (adaptive_router)
        2. Route to retrieval pipeline (BM25/Hybrid/Graph/Full)
        3. Build adaptive memory context (context_scorer + memory_manager)
        4. Fuse RAG context + memory context
        5. Return PipelineResult with full metadata

    Args:
        query_text: The search query
        agent_id: Active agent for memory lookup (optional)
        pipeline: Force specific pipeline A/B/C/D/E (auto-selects if None)
        max_tokens: Max context tokens
        include_memory: Whether to include agent/shared memory
        bucket: Knowledge bucket to retrieve from ("external" | "business" |
            "personal"). STORY-RAG-ANSWER-BUCKET-ROUTING forwards it to
            ``route_query`` so the answer chain reaches the right index. Default
            ``"external"`` preserves backward-compat for every existing caller.
    """
    t0 = time.time()

    # Step 1: Classify intent
    from .adaptive_router import Pipeline, classify_intent, route_query

    intent = classify_intent(query_text)

    # Step 2: Select and execute retrieval pipeline
    forced = None
    if pipeline:
        pipeline_map = {p.value: p for p in Pipeline}
        forced = pipeline_map.get(pipeline.upper())

    retrieval = route_query(
        query_text, pipeline=forced, max_tokens=max_tokens, bucket=bucket
    )

    rag_context = retrieval.get("context", "")
    results = retrieval.get("results", [])
    sources = retrieval.get("sources", [])

    # Step 3: Build adaptive memory context
    memory_context = ""
    if include_memory and intent not in ("greeting", "meta"):
        memory_context = _build_memory_context(query_text, agent_id, intent)

    # Step 4: Fuse contexts (70% RAG, 30% memory)
    char_limit = max_tokens * 4
    rag_budget = int(char_limit * 0.7) if memory_context else char_limit
    mem_budget = char_limit - rag_budget

    # Trim RAG context if needed
    if len(rag_context) > rag_budget:
        rag_context = rag_context[:rag_budget]
    if memory_context and len(memory_context) > mem_budget:
        memory_context = memory_context[:mem_budget]

    # Combine
    parts = []
    if rag_context:
        parts.append(rag_context)
    if memory_context:
        parts.append(memory_context)
    final_context = "\n\n---\n\n".join(parts)

    latency = round((time.time() - t0) * 1000, 1)

    result = PipelineResult(
        query=query_text,
        intent=intent,
        pipeline=retrieval.get("pipeline", "?"),
        pipeline_name=retrieval.get("pipeline_name", "?"),
        context=final_context,
        rag_context=rag_context,
        memory_context=memory_context,
        results=results,
        sources=sources,
        latency_ms=latency,
        memory_included=bool(memory_context),
        chunk_count=len(results),
    )

    # S6: QueryTrace — non-blocking, never raises
    try:
        from .query_trace import QueryTrace, persist_trace
        from .self_rag import MATCH_THRESHOLD

        trace = QueryTrace(
            query_text=query_text,
            bucket=retrieval.get("bucket", "external"),
            retrieval_scores=[
                {"chunk_id": r.get("chunk_id", ""), "score": r.get("score", 0.0)}
                for r in results[:30]
            ],
            pipeline_selected=retrieval.get("pipeline", "?"),
            chunk_count=len(results),
            latency_ms=latency,
            threshold_applied=MATCH_THRESHOLD,
        )
        persist_trace(trace)
    except Exception:
        pass  # Trace failure never blocks the query

    return result


def verify(response: str, pipeline_result: PipelineResult) -> dict:
    """Post-generation verification using Self-RAG + HHEM gate.

    Stage 1 (always): heuristic faithfulness via self_rag (~1ms, zero-LLM)
    Stage 2 (conditional): HHEM-2.1-Open when faithfulness < 0.60 (~50-200ms)

    Returns:
        dict with faithfulness_score, verdict, hhem_score, hallucination_warning
    """
    chunks = [
        r.get("text", r.get("text_preview", r.get("label", "")))
        for r in pipeline_result.results
        if r
    ]

    # Stage 1: heuristic self-RAG (TRANSCEND T2 preserved — zero-LLM forever)
    try:
        from .self_rag import verify_response

        verification = verify_response(response, chunks)
    except Exception:
        verification = {"faithfulness": -1, "verdict": "unknown", "error": "self_rag not available"}

    faithfulness = verification.get("faithfulness", -1.0)

    # Stage 2: HHEM gate (S8) — only when faithfulness < 0.60
    hhem_result = {
        "triggered": False,
        "hhem_score": -1.0,
        "hallucination_warning": False,
        "available": True,
    }
    if faithfulness >= 0 and faithfulness < 0.60:
        try:
            from .hhem_gate import check_response

            context = "\n".join(c for c in chunks if c)[:4000]
            hhem_result = check_response(
                query=pipeline_result.query,
                context=context,
                response=response,
                faithfulness_score=faithfulness,
            )
        except Exception:
            pass  # HHEM unavailable — non-blocking

    return {
        **verification,
        "hhem_score": hhem_result["hhem_score"],
        "hhem_triggered": hhem_result["triggered"],
        "hallucination_warning": hhem_result["hallucination_warning"],
    }


# Faithfulness band -> verdict label, mirrors self_rag.verify_response so the
# caller can report a verdict even if Stage 1 returns an error (-1).
_VERDICT_HIGH = 0.9
_VERDICT_MID = 0.6

# STORY-GBA-F4.1 — the block threshold the CALLER gates on. Default mirrors the
# HHEM_TRIGGER_THRESHOLD (0.60) referenced in the @po decision (story AC), but is
# now an ACTIVE gate (block), not informational. Configurable via env so latency
# vs strictness can be tuned per deployment (D4: "SIM, com threshold
# configurável"). RNF-1: this lives in the caller — `hhem_gate.py` core is never
# read or written for the decision.
FAITHFULNESS_BLOCK_THRESHOLD = 0.60

# Env var that overrides the default at runtime (lazy-read, same pattern as
# store_resolver / postgres_store). Out-of-range / unparseable values fall back
# to the default — a misconfigured env must NEVER silently disable the gate.
FAITHFULNESS_BLOCK_THRESHOLD_ENV = "HHEM_BLOCK_THRESHOLD"

# Message delivered IN PLACE of a blocked response. The original (blocked)
# response is preserved under `blocked_response` for observability/audit, but is
# NOT delivered to the user — that is the whole point of block-vs-flag.
BLOCKED_RESPONSE_MESSAGE = (
    "[BLOCKED: a resposta gerada nao passou no gate de fidelidade (faithfulness "
    "abaixo do threshold) e foi barrada para evitar alucinacao. Reformule a "
    "pergunta ou consulte as fontes diretamente.]"
)


def _resolve_block_threshold() -> float:
    """Resolve the active faithfulness block threshold (env override > default).

    Lazy env read (resolved per call, same discipline as the store resolvers) so
    tests and deployments can flip it without re-importing the module. A value
    outside [0.0, 1.0] or unparseable falls back to FAITHFULNESS_BLOCK_THRESHOLD
    — fail-safe: a broken config keeps the gate at its documented default rather
    than disabling protection.
    """
    raw = (os.environ.get(FAITHFULNESS_BLOCK_THRESHOLD_ENV) or "").strip()
    if not raw:
        return FAITHFULNESS_BLOCK_THRESHOLD
    try:
        value = float(raw)
    except ValueError:
        return FAITHFULNESS_BLOCK_THRESHOLD
    if 0.0 <= value <= 1.0:
        return value
    return FAITHFULNESS_BLOCK_THRESHOLD


def attach_verification(
    response: str,
    pipeline_result: PipelineResult,
) -> dict:
    """Production caller for ``verify()`` — the response-path assembly seam.

    THIS is the function STORY-GBA-W1.2 adds: until now ``verify()`` was an
    ORPHAN (docstring + ``__main__`` + tests, zero production caller). Any
    response-generating consumer (agent answer assembly, REST answer builder,
    voice loop) calls this AFTER it has a generated ``response`` and the
    ``PipelineResult`` that fed it, to attach faithfulness metadata.

    FLAG-ONLY (W1.2 contract): the response text is returned BYTE-IDENTICAL.
    This function NEVER mutates, truncates, reorders, redacts, or blocks the
    response. It only ANNEXES a ``verification`` metadata block:
    ``{faithfulness, verdict, hhem_triggered, ...}``.

    Stage flow (delegated to ``verify()`` — the orphan now reached):
      Stage 1  Self-RAG token-overlap (zero-LLM, ~1ms) -> faithfulness.
      Stage 2  HHEM gate fires ONLY when faithfulness < 0.60 (flag, not block).

    Args:
        response: The generated response text (delivered to the user verbatim).
        pipeline_result: The retrieval result that grounded the response;
            ``verify()`` reads its ``results`` chunks as the source of truth.

    Returns:
        dict with the response intact plus verification metadata::

            {
                "response": str,            # BYTE-IDENTICAL to input
                "verification": {faithfulness, verdict, hhem_triggered, ...},
                "verification_action": "flag",  # F4.1 may make this "block"
                "delivered": True,          # W1.2: always delivered (flag-only)
            }
    """
    # Run the (now-reached) orphan. verify() is itself fully non-blocking and
    # never raises — but we belt-and-suspenders it so the response path can
    # NEVER be broken by a verification failure (Art. XII spirit).
    try:
        verification = verify(response, pipeline_result)
    except Exception:
        verification = {
            "faithfulness": -1.0,
            "verdict": "unknown",
            "hhem_triggered": False,
            "hallucination_warning": False,
            "error": "verify_failed",
        }

    faithfulness = verification.get("faithfulness", -1.0)

    # ---- F4.1 EXTENSION POINT (block-vs-flag decision) — NOW ACTIVE -------
    # The @po decision for F4.1 (HANDOFF §8, row F4.1) is EXPLICIT: the
    # block-vs-flag decision lives HERE in the caller, NOT inside the
    # caixa-preta `hhem_gate.py` (which stays `git diff` empty, RNF-1).
    #
    # W1.2 left this as ALWAYS "flag" (response delivered intact regardless of
    # score). STORY-GBA-F4.1 flips it: a response whose faithfulness is a VALID
    # score (>= 0) and falls BELOW the configurable threshold is BLOCKED — its
    # text is replaced with BLOCKED_RESPONSE_MESSAGE and `delivered` becomes
    # False. We read the score `verify()` already produced; the HHEM NLI
    # evaluation in `hhem_gate.py` is never modified — only the caller decides.
    #
    # faithfulness == -1.0 means Stage 1 could not score (self_rag unavailable /
    # error). We do NOT block on an UNKNOWN score — blocking requires positive
    # evidence of low faithfulness, never absence of evidence (fail-open on the
    # scorer, fail-closed only on a real low score).
    block_threshold = _resolve_block_threshold()
    should_block = 0.0 <= faithfulness < block_threshold

    verification_action = "block" if should_block else "flag"
    # ----------------------------------------------------------------------

    # Persist faithfulness into the QueryTrace slot already reserved for it
    # (query_trace.QueryTrace.faithfulness_score / hhem_* fields). Non-blocking:
    # a trace failure NEVER affects response delivery.
    try:
        from .query_trace import QueryTrace, persist_trace

        persist_trace(
            QueryTrace(
                query_text=pipeline_result.query,
                bucket="external",
                pipeline_selected=pipeline_result.pipeline,
                chunk_count=pipeline_result.chunk_count,
                latency_ms=pipeline_result.latency_ms,
                faithfulness_score=faithfulness,
                hhem_hallucination_probability=verification.get("hhem_score", -1.0),
                hallucination_warning=bool(verification.get("hallucination_warning", False)),
            )
        )
    except Exception:
        pass  # Observability failure never blocks the response.

    if should_block:
        # BLOCK (F4.1): the hallucinated response is NOT delivered. We surface a
        # safe placeholder and preserve the original under `blocked_response`
        # for audit/observability. `delivered` is False so the response path can
        # branch on it. The verification metadata is kept intact.
        return {
            "response": BLOCKED_RESPONSE_MESSAGE,
            "blocked_response": response,  # original, for audit — NOT delivered
            "verification": verification,
            "verification_action": "block",
            "blocked": True,
            "block_threshold": block_threshold,
            "delivered": False,
        }

    # FLAG (W1.2 contract preserved for faithfulness >= threshold OR unknown
    # score): response delivered verbatim, only metadata annexed.
    return {
        "response": response,  # delivered verbatim, never altered.
        "verification": verification,
        "verification_action": verification_action,
        "block_threshold": block_threshold,
        "delivered": True,
    }


# ---------------------------------------------------------------------------
# PRIVATE HELPERS
# ---------------------------------------------------------------------------


def _build_memory_context(query_text: str, agent_id: str | None, intent: str) -> str:
    """Build memory context using context_scorer."""
    try:
        # Use context_scorer if available
        root = Path(__file__).resolve().parent.parent.parent.parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))

        from engine.intelligence.context_scorer import build_adaptive_context

        return build_adaptive_context(
            query=query_text,
            agent_id=agent_id,
            intent=intent,
            include_shared=True,
        )
    except Exception:
        # Fallback: direct memory_manager access
        try:
            from engine.intelligence.memory_manager import get_shared_store, get_store

            parts = []
            if agent_id:
                store = get_store(agent_id)
                if store.count > 0:
                    ctx = store.export_for_context(query=query_text, max_chars=4000)
                    if ctx:
                        parts.append(ctx)

            shared = get_shared_store()
            if shared.count > 0:
                ctx = shared.export_for_context(query=query_text, max_chars=2000)
                if ctx:
                    parts.append(ctx)

            return "\n".join(parts)
        except Exception:
            return ""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print('Usage: python3 -m core.intelligence.rag.pipeline "query" [--agent AGENT_ID]')
        sys.exit(1)

    agent_id = None
    args = sys.argv[1:]
    if "--agent" in args:
        idx = args.index("--agent")
        if idx + 1 < len(args):
            agent_id = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]

    query_text = " ".join(args)

    print(f"\n{'=' * 60}")
    print("UNIFIED RAG PIPELINE")
    print(f"{'=' * 60}")
    print(f"Query: {query_text}")
    if agent_id:
        print(f"Agent: {agent_id}")
    print()

    result = query(query_text, agent_id=agent_id)

    print(f"Intent: {result.intent}")
    print(f"Pipeline: {result.pipeline} ({result.pipeline_name})")
    print(f"Chunks: {result.chunk_count}")
    print(f"Memory: {'Yes' if result.memory_included else 'No'}")
    print(f"Latency: {result.latency_ms}ms")
    print(f"Context length: {len(result.context)} chars")

    if result.sources:
        print(f"\nTop sources ({len(result.sources)}):")
        for s in result.sources[:5]:
            person = s.get("person", "")
            source = s.get("source_file", s.get("source", ""))
            chunk = s.get("chunk_id", s.get("id", ""))
            print(f"  [{chunk}] {person} — {source}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
