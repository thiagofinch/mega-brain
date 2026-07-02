#!/usr/bin/env python3
"""
ADAPTIVE ROUTER - Phase 5.1
=============================
Classifies queries and routes to the optimal retrieval pipeline.

Pipeline options (fastest → most thorough):
  A: BM25 only        (~15ms)  - Factual lookup
  B: Hybrid            (~80ms)  - Standard semantic + keyword
  C: Hybrid + Graph   (~200ms) - Analytical, cross-expert
  D: Full pipeline    (~500ms) - Maximum recall
  E: LLM-only          (~0ms)  - No retrieval needed

Versao: 1.0.0
Data: 2026-03-01
"""

import re
import sys
import time
from enum import Enum

from .graph_query import graph_search
from .hybrid_index import get_index_for_bucket
from .hybrid_query import (
    RERANK_CANDIDATES,
    QueryResult,
    apply_reranker,
    hybrid_search,
    reranker_enabled,
    strategic_order,
)
from .query_expansion import expand_query, expansion_enabled


# ---------------------------------------------------------------------------
# PIPELINE DEFINITIONS
# ---------------------------------------------------------------------------
class Pipeline(Enum):
    BM25_ONLY = "A"
    HYBRID = "B"
    HYBRID_GRAPH = "C"
    FULL = "D"
    LLM_ONLY = "E"


PIPELINE_CONFIG = {
    Pipeline.BM25_ONLY: {
        "name": "BM25 Only",
        "description": "Fast keyword lookup",
        "expected_latency_ms": 15,
        "top_k": 5,
    },
    Pipeline.HYBRID: {
        "name": "Hybrid (Vector + BM25)",
        "description": "Standard semantic + keyword search",
        "expected_latency_ms": 80,
        "top_k": 10,
    },
    Pipeline.HYBRID_GRAPH: {
        "name": "Hybrid + Graph",
        "description": "Cross-expert analysis with knowledge graph",
        "expected_latency_ms": 200,
        "top_k": 15,
    },
    Pipeline.FULL: {
        "name": "Full Pipeline",
        "description": "All retrieval strategies combined",
        "expected_latency_ms": 500,
        "top_k": 20,
    },
    Pipeline.LLM_ONLY: {
        "name": "LLM Only",
        "description": "No retrieval needed",
        "expected_latency_ms": 0,
        "top_k": 0,
    },
}


# ---------------------------------------------------------------------------
# INTENT CLASSIFICATION
# ---------------------------------------------------------------------------
INTENT_PATTERNS = {
    "greeting": [
        r"^(?:oi|ola|hey|hi|hello|bom dia|boa tarde|boa noite)",
        r"^(?:como vai|tudo bem|e ai)",
    ],
    "meta": [
        r"(?:quem|who).*(?:voce|you|sou|am)",
        r"(?:o que|what).*(?:voce faz|you do|consegue|can you)",
        r"(?:help|ajuda|como funciona|how.*work)",
    ],
    "factual_simple": [
        r"^(?:qual|what|quanto|how much|quando|when).*\?$",
        r"(?:defina|define|o que [eé]|what is)",
        r"(?:me diga|tell me).*(?:numero|number|taxa|rate|percentual|percent)",
    ],
    "factual_complex": [
        r"(?:compare|comparar|diferenca|difference|versus|vs\.?)",
        r"(?:lista|list|quais|which).*(?:todos|all|principais|main)",
        r"(?:explique|explain|detalhe|detail|aprofunde|deep dive)",
    ],
    "analytical": [
        r"(?:por que|why|como|how).*(?:funciona|works|deveria|should)",
        r"(?:estrategia|strategy|plano|plan|recomend|recommend)",
        r"(?:melhor|best|ideal|otim|optim)",
    ],
    "cross_expert": [
        r"(?:o que|what).*(?:todos|all|experts?|especialistas)",
        r"(?:consenso|consensus|concordam|agree|divergem|disagree)",
        r"(?:quem mais|who else|outros|other).*(?:fala|says|pensa|thinks)",
    ],
    "hierarchical": [
        r"(?:trace|rastrear|caminho|path|hierarquia|hierarchy)",
        r"(?:da filosofia|from philosophy).*(?:metodologia|methodology)",
        r"(?:dna|cognitiv).*(?:cascade|cascata)",
    ],
}


def classify_intent(query: str) -> str:
    """Classify query intent.

    Returns: greeting, meta, factual_simple, factual_complex,
             analytical, cross_expert, hierarchical
    """
    query_lower = query.lower().strip()

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                return intent

    # Default: if short query, likely factual; if long, likely analytical
    if len(query_lower.split()) <= 5:
        return "factual_simple"
    return "analytical"


def select_pipeline(query: str, intent: str | None = None) -> Pipeline:
    """Select the best pipeline for a query based on intent.

    Args:
        query: The search query
        intent: Pre-classified intent (auto-classifies if None)

    Returns: Pipeline enum value
    """
    if intent is None:
        intent = classify_intent(query)

    routing = {
        "greeting": Pipeline.LLM_ONLY,
        "meta": Pipeline.LLM_ONLY,
        "factual_simple": Pipeline.BM25_ONLY,
        "factual_complex": Pipeline.HYBRID,
        "analytical": Pipeline.HYBRID_GRAPH,
        "cross_expert": Pipeline.HYBRID_GRAPH,
        "hierarchical": Pipeline.FULL,
    }

    return routing.get(intent, Pipeline.HYBRID)


# ---------------------------------------------------------------------------
# BM25-ONLY SEARCH (Pipeline A)
# ---------------------------------------------------------------------------
def _bm25_only_search(query: str, top_k: int = 5, bucket: str = "external") -> dict:
    """BM25-only retrieval -- no vector search, no RRF fusion.

    Uses the BM25 index directly for fast keyword lookup.
    Returns the same result shape as hybrid_search for compatibility.

    STORY-RAG-ANSWER-BUCKET-ROUTING: the BM25 fast path (factual_simple / short
    queries) must honor the requested bucket too — otherwise a business query
    routed to Pipeline A would still hit the external index. ``bucket="external"``
    preserves the legacy default so no existing caller changes behavior.
    """
    t0 = time.time()

    idx = get_index_for_bucket(bucket)
    if not idx.built or not idx.chunks:
        return {
            "query": query,
            "error": "Index not built. Run hybrid_index.py --bm25-only first.",
        }

    # Reranker coverage (STORY-RERANKER-BM25-COVERAGE): the BM25 fast path used
    # to skip the cross-encoder entirely. When the reranker is ON we fetch a
    # WIDER candidate pool (so zerank-2/cohere has something to reorder) and
    # rerank before truncating to top_k — same posture as ``hybrid_search``.
    # OFF ⇒ legacy fast path (just top_k, ~15ms). apply_reranker fail-opens on
    # any error, so search reliability is unchanged.
    rerank_on = reranker_enabled()
    pool = max(RERANK_CANDIDATES, top_k) if rerank_on else top_k
    bm25_results = idx.bm25.query(query, top_k=pool)

    candidates: list[tuple[int, float]] = [(d, s) for d, s in bm25_results]
    if rerank_on:
        candidates = apply_reranker(query, candidates, idx.chunks)
    candidates = candidates[:top_k]

    results = []
    for rank, (doc_idx, score) in enumerate(candidates):
        chunk = idx.get_chunk(doc_idx)
        if chunk:
            results.append(QueryResult(chunk, score, rank + 1))

    ordered = strategic_order([(i, r.score) for i, r in enumerate(results)])
    results = [results[i] for i, _ in ordered if i < len(results)]

    latency = (time.time() - t0) * 1000

    return {
        "query": query,
        "results": [r.to_dict() for r in results],
        "total_candidates": len(bm25_results),
        "pipeline": {
            "backend": "bm25_only",
            "bm25": len(bm25_results),
            "reranked": rerank_on,
        },
        "latency_ms": round(latency, 1),
    }


# ---------------------------------------------------------------------------
# RETRIEVAL DISPATCH (single query)
# ---------------------------------------------------------------------------
def _retrieve_one(
    query: str, selected: Pipeline, config: dict, bucket: str = "external"
) -> dict:
    """Run ONE query through the selected pipeline and return its search dict.

    Extracted from ``route_query`` so the optional query-expansion step can
    invoke the exact same retrieval per variant. The per-pipeline behavior is
    byte-identical to the pre-expansion code path.

    STORY-RAG-ANSWER-BUCKET-ROUTING: ``bucket`` threads down to the index-facing
    searches (``hybrid_search`` / ``_bm25_only_search``) so the answer chain can
    actually retrieve from the requested bucket. Default ``"external"`` preserves
    backward-compat at every hop (#42 fixed the raw search; this passes it down).
    """
    if selected == Pipeline.BM25_ONLY:
        # Fast BM25-only search — no vector search, no RRF fusion
        search = _bm25_only_search(query, top_k=config["top_k"], bucket=bucket)
        return {"results": search.get("results", []), "fused": False}

    if selected == Pipeline.HYBRID:
        # Standard hybrid search (vector + BM25 + RRF fusion)
        search = hybrid_search(query, top_k=config["top_k"], bucket=bucket)
        return {"results": search.get("results", []), "fused": False}

    if selected == Pipeline.HYBRID_GRAPH:
        # Hybrid + Graph fusion
        # graph_search é cross-bucket por design (PPR sobre o grafo cross-pessoa);
        # não aceita param bucket — NÃO inventar um. Limitação documentada na story
        # (OUT of scope: graph_search cross-bucket support).
        search = graph_search(query, top_k=config["top_k"])
        return {
            "results": search.get("fused_results", []),
            "graph_strategy": search.get("strategy", ""),
            "fused": True,
        }

    # Pipeline.FULL — graph search with all strategies
    # graph_search é cross-bucket por design (PPR) — sem param bucket (ver acima).
    search = graph_search(query, top_k=config["top_k"])
    return {
        "results": search.get("fused_results", []),
        "graph_results": search.get("graph_results", []),
        "hybrid_results": search.get("hybrid_results", []),
        "graph_strategy": search.get("strategy", ""),
        "fused": True,
    }


def _merge_variant_results(per_variant: list[list[dict]], top_k: int) -> list[dict]:
    """Merge result lists from multiple query variants into one ranked list.

    Recall-additive union: dedup by chunk/result id, keep each doc's BEST
    (smallest) rank across variants, and break ties by the variant order
    (variant 0 is the ORIGINAL query, so its hits sort first). This guarantees
    the original query's results dominate; expanded variants only contribute
    the recall tail — extra relevant docs the literal query missed. With a
    single variant (the fail-open case) the output equals that variant's list,
    so behavior is unchanged when expansion is off or fails.
    """
    best: dict[str, dict] = {}
    order: dict[str, tuple[int, int]] = {}  # id -> (best_rank, variant_idx)
    for variant_idx, results in enumerate(per_variant):
        for rank, r in enumerate(results):
            rid = r.get("chunk_id") or r.get("id") or ""
            if not rid:
                # No stable id → keep positionally under a synthetic key.
                rid = f"__noid__{variant_idx}_{rank}"
            key = (rank, variant_idx)
            if rid not in order or key < order[rid]:
                order[rid] = key
                best[rid] = r
    ranked_ids = sorted(order, key=lambda rid: order[rid])
    return [best[rid] for rid in ranked_ids[:top_k]]


# ---------------------------------------------------------------------------
# ROUTER EXECUTION
# ---------------------------------------------------------------------------
def route_query(
    query: str,
    pipeline: Pipeline | None = None,
    max_tokens: int = 8000,
    expand: bool | None = None,
    bucket: str = "external",
) -> dict:
    """Route a query through the selected pipeline and return results.

    Args:
        query: Search query
        pipeline: Force a specific pipeline (auto-selects if None)
        max_tokens: Max context tokens for RAG context building
        expand: Toggle LLM query expansion before retrieval. ``None`` (default)
            resolves to the ``RAG_QUERY_EXPANSION`` config flag (default OFF).
            ``True``/``False`` force it on/off for this call. Expansion is
            FAIL-OPEN: on any failure it falls back to the original query, so
            it can only add recall, never break retrieval.
        bucket: Knowledge bucket to retrieve from ("external" | "business" |
            "personal"). STORY-RAG-ANSWER-BUCKET-ROUTING threads it to
            ``_retrieve_one`` (and thus to ``hybrid_search`` / ``_bm25_only_search``)
            for EVERY variant. Default ``"external"`` keeps existing callers intact.

    Returns:
        {
            "query": str,
            "intent": str,
            "pipeline": str,
            "pipeline_name": str,
            "results": [...],
            "context": str (formatted for LLM),
            "sources": [...],
            "expanded": bool,        # whether >1 query variant was searched
            "query_variants": [...], # the variants actually retrieved
            "latency_ms": float,
        }
    """
    t0 = time.time()

    intent = classify_intent(query)
    selected = pipeline or select_pipeline(query, intent)
    config = PIPELINE_CONFIG[selected]

    result = {
        "query": query,
        "intent": intent,
        "pipeline": selected.value,
        "pipeline_name": config["name"],
        "results": [],
        "context": "",
        "sources": [],
        "expanded": False,
        "query_variants": [query],
        "bucket": bucket,
        "latency_ms": 0,
    }

    if selected == Pipeline.LLM_ONLY:
        result["latency_ms"] = round((time.time() - t0) * 1000, 1)
        return result

    # ----- OPTIONAL query expansion (BEFORE retrieval, fail-open) -----------
    # expand_query() ALWAYS returns the original query first and NEVER raises;
    # when expansion is off/fails it returns [query], collapsing to the exact
    # single-query path below.
    use_expansion = expansion_enabled() if expand is None else bool(expand)
    variants = expand_query(query) if use_expansion else [query]
    result["query_variants"] = variants
    result["expanded"] = len(variants) > 1

    # ----- retrieval (one pass per variant, then recall-additive merge) -----
    fused = False
    extra: dict = {}
    if len(variants) == 1:
        search = _retrieve_one(variants[0], selected, config, bucket=bucket)
        result["results"] = search["results"]
        fused = search.get("fused", False)
        extra = search
    else:
        per_variant = []
        for v in variants:
            search = _retrieve_one(v, selected, config, bucket=bucket)
            per_variant.append(search["results"])
            fused = search.get("fused", False)
            extra = search  # pipeline-shape metadata is identical across variants
        result["results"] = _merge_variant_results(per_variant, config["top_k"])

    # Carry pipeline-specific side fields (graph strategy / sub-result lists).
    if "graph_strategy" in extra:
        result["graph_strategy"] = extra["graph_strategy"]
    if "graph_results" in extra:
        result["graph_results"] = extra["graph_results"]
    if "hybrid_results" in extra:
        result["hybrid_results"] = extra["hybrid_results"]

    result["sources"] = (
        _extract_sources_from_fused(result["results"])
        if fused
        else _extract_sources(result["results"])
    )

    # Build context string for LLM consumption
    if result["results"]:
        result["context"] = _build_context_string(result["results"], max_tokens)

    result["latency_ms"] = round((time.time() - t0) * 1000, 1)
    return result


def _extract_sources(results: list[dict]) -> list[dict]:
    """Extract source references from hybrid search results."""
    sources = []
    for r in results:
        sources.append(
            {
                "chunk_id": r.get("chunk_id", ""),
                "source_file": r.get("source_file", ""),
                "person": r.get("person", ""),
                "section": r.get("section", ""),
            }
        )
    return sources


def _extract_sources_from_fused(results: list[dict]) -> list[dict]:
    """Extract source references from fused results."""
    sources = []
    for r in results:
        sources.append(
            {
                "id": r.get("id", ""),
                "source": r.get("source", ""),
                "person": r.get("person", ""),
                "source_file": r.get("source_file", ""),
            }
        )
    return sources


def _build_context_string(results: list[dict], max_tokens: int) -> str:
    """Build a formatted context string from results for LLM consumption."""
    parts = []
    total_chars = 0
    char_limit = max_tokens * 4  # ~4 chars per token

    for r in results:
        # Get text from different result formats
        text = r.get("text_preview", "") or r.get("label", "") or r.get("text", "")
        if not text:
            continue

        chunk_id = r.get("chunk_id", r.get("id", ""))
        person = r.get("person", "")

        entry = f"[RAG:{chunk_id}]"
        if person:
            entry += f" ({person})"
        entry += f" {text}"

        if total_chars + len(entry) > char_limit:
            break

        parts.append(entry)
        total_chars += len(entry)

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print('Usage: python3 -m core.intelligence.rag.adaptive_router "query"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    print(f"\n{'=' * 60}")
    print("ADAPTIVE ROUTER")
    print(f"{'=' * 60}")
    print(f"Query: {query}\n")

    result = route_query(query)

    print(f"Intent: {result['intent']}")
    print(f"Pipeline: {result['pipeline']} ({result['pipeline_name']})")
    print(f"Results: {len(result['results'])}")
    print(f"Latency: {result['latency_ms']}ms")

    if result["results"]:
        print("\nTop results:")
        for i, r in enumerate(result["results"][:5]):
            rid = r.get("chunk_id", r.get("id", "?"))
            label = r.get("text_preview", r.get("label", ""))[:60]
            print(f"  #{i + 1} {rid}: {label}")

    if result["sources"]:
        print(f"\nSources: {len(result['sources'])}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
