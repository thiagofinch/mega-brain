#!/usr/bin/env python3
"""
UNIFIED RAG PIPELINE - The Orchestrator
=========================================
Single entry point that connects:
  adaptive_router -> retrieval -> memory -> fusion -> output

Usage:
    from core.intelligence.rag.pipeline import query
    result = query("What commission structure should I use?", agent_id="closer")

Versao: 1.0.0
Data: 2026-03-07
"""

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
    """
    t0 = time.time()

    # Step 1: Classify intent
    from .adaptive_router import Pipeline, classify_intent, route_query, select_pipeline

    intent = classify_intent(query_text)

    # Step 2: Select and execute retrieval pipeline
    forced = None
    if pipeline:
        pipeline_map = {p.value: p for p in Pipeline}
        forced = pipeline_map.get(pipeline.upper())

    retrieval = route_query(query_text, pipeline=forced, max_tokens=max_tokens)

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

    return PipelineResult(
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


def verify(response: str, pipeline_result: PipelineResult) -> dict:
    """Post-generation verification using Self-RAG.

    Checks if the response is faithful to the retrieved chunks.

    Returns:
        dict with faithfulness_score, unsupported_claims, corrections
    """
    try:
        from .self_rag import verify_response

        chunks = [
            r.get("text", r.get("text_preview", r.get("label", "")))
            for r in pipeline_result.results
            if r
        ]
        return verify_response(response, chunks)
    except Exception:
        return {"faithfulness_score": -1, "error": "self_rag not available"}


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

        from core.intelligence.context_scorer import build_adaptive_context

        return build_adaptive_context(
            query=query_text,
            agent_id=agent_id,
            intent=intent,
            include_shared=True,
        )
    except Exception:
        # Fallback: direct memory_manager access
        try:
            from core.intelligence.memory_manager import get_shared_store, get_store

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
