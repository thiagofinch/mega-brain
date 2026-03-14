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
from .hybrid_query import hybrid_search


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
# ROUTER EXECUTION
# ---------------------------------------------------------------------------
def route_query(
    query: str,
    pipeline: Pipeline | None = None,
    max_tokens: int = 8000,
) -> dict:
    """Route a query through the selected pipeline and return results.

    Args:
        query: Search query
        pipeline: Force a specific pipeline (auto-selects if None)
        max_tokens: Max context tokens for RAG context building

    Returns:
        {
            "query": str,
            "intent": str,
            "pipeline": str,
            "pipeline_name": str,
            "results": [...],
            "context": str (formatted for LLM),
            "sources": [...],
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
        "latency_ms": 0,
    }

    if selected == Pipeline.LLM_ONLY:
        result["latency_ms"] = round((time.time() - t0) * 1000, 1)
        return result

    if selected == Pipeline.BM25_ONLY:
        # Fast BM25-only search
        search = hybrid_search(query, top_k=config["top_k"])
        result["results"] = search.get("results", [])
        result["sources"] = _extract_sources(result["results"])

    elif selected == Pipeline.HYBRID:
        # Standard hybrid search
        search = hybrid_search(query, top_k=config["top_k"])
        result["results"] = search.get("results", [])
        result["sources"] = _extract_sources(result["results"])

    elif selected == Pipeline.HYBRID_GRAPH:
        # Hybrid + Graph fusion
        search = graph_search(query, top_k=config["top_k"])
        result["results"] = search.get("fused_results", [])
        result["graph_strategy"] = search.get("strategy", "")
        result["sources"] = _extract_sources_from_fused(result["results"])

    elif selected == Pipeline.FULL:
        # Full pipeline: graph search with all strategies
        search = graph_search(query, top_k=config["top_k"])
        result["results"] = search.get("fused_results", [])
        result["graph_results"] = search.get("graph_results", [])
        result["hybrid_results"] = search.get("hybrid_results", [])
        result["graph_strategy"] = search.get("strategy", "")
        result["sources"] = _extract_sources_from_fused(result["results"])

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
