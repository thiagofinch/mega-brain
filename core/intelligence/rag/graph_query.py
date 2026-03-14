#!/usr/bin/env python3
"""
GRAPH QUERY ENGINE - Phase 4.5
================================
Combines graph-based retrieval (Phase 4) with hybrid retrieval (Phase 3).

Classifies queries by type and routes to the best strategy:
- GLOBAL:       "What do all experts say about X?"     → Community summaries
- ONTOLOGICAL:  "Which heuristics apply to Y?"         → OG-RAG ontology layer
- ASSOCIATIVE:  "Who said something similar to Z?"     → HippoRAG PPR
- HIERARCHICAL: "Trace from philosophy to methodology" → Ontology hierarchy
- FACTUAL:      "What is the commission rate?"         → Hybrid search (Phase 3)

Results from graph queries are combined with hybrid search via RRF.

Versao: 1.0.0
Data: 2026-03-01
"""

import re
import sys
import time

from .associative_memory import associative_search
from .graph_builder import KnowledgeGraph, detect_communities, get_graph
from .hybrid_query import hybrid_search
from .ontology_layer import (
    LAYER_HIERARCHY,
    query_by_layer,
    trace_hierarchy,
)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
GRAPH_WEIGHT = 0.4  # Weight of graph results in fusion
HYBRID_WEIGHT = 0.6  # Weight of hybrid search results in fusion


# ---------------------------------------------------------------------------
# QUERY CLASSIFICATION
# ---------------------------------------------------------------------------
QUERY_PATTERNS = {
    "global": [
        r"(?:o que|what).*(?:todos|all|experts?|everyone|consenso|consensus)",
        r"(?:qual|what).*(?:consenso|consensus|agreement|concordam|agree)",
        r"(?:como|how).*(?:todos|all|experts?).*(?:veem|see|think|pensam)",
    ],
    "ontological": [
        r"(?:quais|which|que).*(?:heurist|framework|metodolog|filosofi|modelo)",
        r"(?:heurist|framework|metodolog).*(?:para|for|sobre|about)",
        r"(?:regras?|rules?).*(?:para|for|sobre|about)",
        r"(?:threshold|limiar|limite|gate).*(?:para|for|de)",
    ],
    "associative": [
        r"(?:quem|who).*(?:mais|else|também|also|similar).*(?:fala|said|talks|diz)",
        r"(?:parecido|similar|like|como).*(?:conceito|concept|ideia|idea)",
        r"(?:outros?|other).*(?:experts?|pessoas?|persons?)",
        r"(?:cross|cruzar|cruzamento).*(?:expert|fonte|source)",
    ],
    "hierarchical": [
        r"(?:trace|rastrear|caminho|path).*(?:filosofia|metodologia|framework)",
        r"(?:da |from ).*(?:filosofia|philosophy).*(?:até|to|ate).*(?:metodologia|methodology)",
        r"(?:hierarquia|hierarchy|cascata|cascade).*(?:dna|cognitiv)",
    ],
}


def classify_query(query: str) -> str:
    """Classify query type based on patterns.

    Returns: "global", "ontological", "associative", "hierarchical", or "factual"
    """
    query_lower = query.lower()

    for query_type, patterns in QUERY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                return query_type

    return "factual"


# ---------------------------------------------------------------------------
# GRAPH QUERY STRATEGIES
# ---------------------------------------------------------------------------
def _query_global(query: str, graph: KnowledgeGraph, top_k: int) -> list[dict]:
    """Global query: find community summaries across experts."""
    communities = detect_communities(graph)

    # Extract domain from query
    query_lower = query.lower()
    query_tokens = set(re.findall(r"[a-z\u00e0-\u024f]{3,}", query_lower))

    results = []
    for comm in communities:
        domain_tokens = set(re.findall(r"[a-z\u00e0-\u024f]{3,}", comm["domain"].lower()))
        overlap = query_tokens & domain_tokens
        if overlap:
            # Get entities from this community
            for eid in comm["entities"][:top_k]:
                entity = graph.get_entity(eid)
                if entity:
                    results.append(
                        {
                            "entity_id": entity.id,
                            "entity_type": entity.type,
                            "label": entity.label,
                            "person": entity.person,
                            "domain": comm["domain"],
                            "score": entity.weight * (len(overlap) / max(len(query_tokens), 1)),
                            "strategy": "global",
                        }
                    )

    results.sort(key=lambda r: -r["score"])
    return results[:top_k]


def _query_ontological(query: str, graph: KnowledgeGraph, top_k: int) -> list[dict]:
    """Ontological query: find entries via OG-RAG ontology layer."""
    results = []

    # Detect target layer
    query_lower = query.lower()
    target_layer = None
    for layer in LAYER_HIERARCHY:
        if layer in query_lower or layer.replace("_", " ") in query_lower:
            target_layer = layer
            break

    # Detect domain from query
    query_tokens = set(re.findall(r"[a-z\u00e0-\u024f]{3,}", query_lower))

    if target_layer:
        # Query specific layer
        layer_results = query_by_layer(target_layer, graph=graph)
        for r in layer_results[:top_k]:
            results.append(
                {
                    "entity_id": r.entity_id,
                    "entity_type": r.entity_type,
                    "label": r.label,
                    "person": r.person,
                    "score": r.score,
                    "strategy": "ontological",
                    "path": r.path,
                }
            )
    else:
        # Try to match domains
        for entity in graph.entities.values():
            if entity.type not in LAYER_HIERARCHY:
                continue
            domain_match = any(
                t in d.lower() for d in entity.domains for t in query_tokens if len(t) >= 4
            )
            label_match = any(t in entity.label.lower() for t in query_tokens if len(t) >= 4)
            if domain_match or label_match:
                score = entity.weight
                if label_match:
                    score *= 1.5
                results.append(
                    {
                        "entity_id": entity.id,
                        "entity_type": entity.type,
                        "label": entity.label,
                        "person": entity.person,
                        "score": score,
                        "strategy": "ontological",
                    }
                )

    results.sort(key=lambda r: -r["score"])
    return results[:top_k]


def _query_associative(query: str, graph: KnowledgeGraph, top_k: int) -> list[dict]:
    """Associative query: use HippoRAG PPR for cross-expert discovery."""
    assoc_result = associative_search(query, top_k=top_k, graph=graph)

    results = []
    for r in assoc_result.get("results", []):
        results.append(
            {
                "entity_id": r["entity_id"],
                "entity_type": r["entity_type"],
                "label": r["label"],
                "person": r["person"],
                "score": r["score"],
                "strategy": "associative",
                "is_seed": r.get("is_seed", False),
            }
        )

    return results


def _query_hierarchical(query: str, graph: KnowledgeGraph, top_k: int) -> list[dict]:
    """Hierarchical query: trace ontology from one layer to another."""
    results = []

    # Try to find a specific entity ID in the query
    id_match = re.search(r"((?:FIL|MM|HEUR|FW|MET)-[A-Z]+-\d+)", query.upper())
    if id_match:
        entity_id = id_match.group(1)
        trace_results = trace_hierarchy(entity_id, direction="both", graph=graph)
        for r in trace_results:
            results.append(
                {
                    "entity_id": r.entity_id,
                    "entity_type": r.entity_type,
                    "label": r.label,
                    "person": r.person,
                    "score": r.score,
                    "strategy": "hierarchical",
                    "path": r.path,
                }
            )
    else:
        # Fall back to associative search
        return _query_associative(query, graph, top_k)

    return results[:top_k]


# ---------------------------------------------------------------------------
# MAIN QUERY ENGINE
# ---------------------------------------------------------------------------
def graph_search(
    query: str,
    top_k: int = 10,
    strategy: str | None = None,
    graph: KnowledgeGraph | None = None,
    include_hybrid: bool = True,
) -> dict:
    """Execute a graph-enhanced search query.

    Args:
        query: Natural language query
        top_k: Number of results
        strategy: Force a specific strategy (auto-classifies if None)
        graph: KnowledgeGraph instance
        include_hybrid: Also run hybrid search and fuse results

    Returns:
        {
            "query": str,
            "strategy": str,
            "graph_results": [...],
            "hybrid_results": [...] (if include_hybrid),
            "fused_results": [...],
            "latency_ms": float,
        }
    """
    t0 = time.time()
    g = graph or get_graph()

    if not g.built:
        return {"query": query, "error": "Graph not built. Run graph_builder.py first."}

    # Classify query
    query_type = strategy or classify_query(query)

    # Route to strategy
    strategies = {
        "global": _query_global,
        "ontological": _query_ontological,
        "associative": _query_associative,
        "hierarchical": _query_hierarchical,
        "factual": _query_associative,  # Factual uses associative as graph component
    }

    strategy_fn = strategies.get(query_type, _query_associative)
    graph_results = strategy_fn(query, g, top_k * 2)  # Get more for fusion

    # Hybrid search
    hybrid_results = []
    if include_hybrid:
        hybrid_output = hybrid_search(query, top_k=top_k)
        hybrid_results = hybrid_output.get("results", [])

    # Fuse results
    fused = _fuse_graph_and_hybrid(graph_results, hybrid_results, top_k)

    latency = (time.time() - t0) * 1000

    return {
        "query": query,
        "strategy": query_type,
        "graph_results": graph_results[:top_k],
        "hybrid_results": hybrid_results[:top_k],
        "fused_results": fused,
        "graph_count": len(graph_results),
        "hybrid_count": len(hybrid_results),
        "latency_ms": round(latency, 1),
    }


def _fuse_graph_and_hybrid(
    graph_results: list[dict],
    hybrid_results: list[dict],
    top_k: int,
) -> list[dict]:
    """Fuse graph and hybrid results using weighted combination.

    Graph results are entity-based, hybrid results are chunk-based.
    We merge by giving each a weighted score contribution.
    """
    fused: dict[str, dict] = {}

    # Score graph results
    for i, r in enumerate(graph_results):
        key = r.get("entity_id", f"graph_{i}")
        score = GRAPH_WEIGHT * r.get("score", 0) * (1.0 / (i + 1))  # Rank discount
        fused[key] = {
            "id": key,
            "label": r.get("label", ""),
            "person": r.get("person", ""),
            "type": r.get("entity_type", ""),
            "source": "graph",
            "strategy": r.get("strategy", ""),
            "score": score,
        }

    # Score hybrid results
    for i, r in enumerate(hybrid_results):
        key = r.get("chunk_id", f"hybrid_{i}")
        score = HYBRID_WEIGHT * r.get("score", 0) * (1.0 / (i + 1))
        if key in fused:
            fused[key]["score"] += score
            fused[key]["source"] = "both"
        else:
            fused[key] = {
                "id": key,
                "label": r.get("text_preview", "")[:80],
                "person": r.get("person", ""),
                "type": "chunk",
                "source": "hybrid",
                "strategy": "hybrid",
                "score": score,
                "source_file": r.get("source_file", ""),
            }

    # Sort by fused score
    sorted_results = sorted(fused.values(), key=lambda x: -x["score"])
    return sorted_results[:top_k]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Graph Query Engine")
    parser.add_argument("query", nargs="?", help="Query text")
    parser.add_argument(
        "--strategy",
        choices=["global", "ontological", "associative", "hierarchical", "factual"],
        help="Force query strategy",
    )
    parser.add_argument("--no-hybrid", action="store_true", help="Disable hybrid search fusion")
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    if not args.query:
        print('Usage: python3 -m core.intelligence.rag.graph_query "query"')
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print("GRAPH QUERY ENGINE")
    print(f"{'=' * 60}")
    print(f"Query: {args.query}\n")

    result = graph_search(
        args.query,
        top_k=args.top_k,
        strategy=args.strategy,
        include_hybrid=not args.no_hybrid,
    )

    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"Strategy: {result['strategy']}")
    print(f"Graph results: {result['graph_count']}")
    print(f"Hybrid results: {result['hybrid_count']}")
    print(f"Latency: {result['latency_ms']}ms\n")

    print("FUSED RESULTS:")
    for i, r in enumerate(result["fused_results"]):
        print(f"  #{i + 1} [{r['source']}] {r['id']}")
        print(f"     {r['label'][:60]}")
        if r.get("person"):
            print(f"     Person: {r['person']}")
        print(f"     Score: {r['score']:.6f}")
        print()

    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
