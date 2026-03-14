#!/usr/bin/env python3
"""
ASSOCIATIVE MEMORY (HippoRAG 2) - Phase 4.4
=============================================
Implements Personalized PageRank over the knowledge graph
to find associative connections that vector search misses.

When a query arrives:
1. Activate seed nodes (query → matching entities)
2. Run Personalized PageRank from seeds
3. Return top-K activated nodes (associatively related)

This finds connections like:
- "Christmas Tree Structure" → similar patterns from OTHER experts
- "commission 10%" → related compensation models across persons

Versao: 1.0.0
Data: 2026-03-01
"""

import re
from collections import defaultdict

from .graph_builder import KnowledgeGraph, get_graph

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
PPR_ALPHA = 0.15  # Teleport probability (higher = more focused on seeds)
PPR_ITERATIONS = 20  # Max iterations for convergence
PPR_TOLERANCE = 1e-6  # Convergence threshold
DEFAULT_TOP_K = 15  # Default results to return


# ---------------------------------------------------------------------------
# SEED ACTIVATION
# ---------------------------------------------------------------------------
def activate_seeds(
    query: str,
    graph: KnowledgeGraph | None = None,
    max_seeds: int = 10,
) -> dict[str, float]:
    """Find seed nodes in the graph that match the query.

    Uses keyword matching against entity labels and IDs.
    Returns: {entity_id: activation_score}
    """
    g = graph or get_graph()
    seeds: dict[str, float] = {}

    # Tokenize query
    query_lower = query.lower()
    query_tokens = set(re.findall(r"[a-z\u00e0-\u024f]{3,}", query_lower))

    if not query_tokens:
        return seeds

    # Score each entity
    for entity_id, entity in g.entities.items():
        score = 0.0

        # Match against label
        label_lower = entity.label.lower()
        label_tokens = set(re.findall(r"[a-z\u00e0-\u024f]{3,}", label_lower))
        overlap = query_tokens & label_tokens
        if overlap:
            score += len(overlap) / max(len(query_tokens), 1)

        # Match against domains
        for domain in entity.domains:
            domain_lower = domain.lower()
            if any(t in domain_lower for t in query_tokens):
                score += 0.3

        # Match against entity ID
        id_lower = entity_id.lower().replace("-", " ")
        if any(t in id_lower for t in query_tokens):
            score += 0.2

        # Exact substring match in label (bonus)
        for token in query_tokens:
            if len(token) >= 4 and token in label_lower:
                score += 0.4

        # Weight by entity weight
        score *= entity.weight

        if score > 0:
            seeds[entity_id] = score

    # Take top seeds
    sorted_seeds = sorted(seeds.items(), key=lambda x: -x[1])
    return dict(sorted_seeds[:max_seeds])


# ---------------------------------------------------------------------------
# PERSONALIZED PAGERANK
# ---------------------------------------------------------------------------
def personalized_pagerank(
    graph: KnowledgeGraph,
    seeds: dict[str, float],
    alpha: float = PPR_ALPHA,
    max_iter: int = PPR_ITERATIONS,
    tolerance: float = PPR_TOLERANCE,
) -> dict[str, float]:
    """Run Personalized PageRank from seed nodes.

    Args:
        graph: The knowledge graph
        seeds: {entity_id: activation_score} seed nodes
        alpha: Teleport probability (restart to seeds)
        max_iter: Maximum iterations
        tolerance: Convergence threshold

    Returns: {entity_id: ppr_score} for all reachable nodes
    """
    if not seeds:
        return {}

    # Normalize seed scores to form teleport distribution
    total_seed = sum(seeds.values())
    teleport: dict[str, float] = {k: v / total_seed for k, v in seeds.items()}

    # Initialize scores
    all_nodes = set(graph.entities.keys())
    scores: dict[str, float] = defaultdict(float)
    for node_id, t_score in teleport.items():
        scores[node_id] = t_score

    # Iterative PPR
    for _iteration in range(max_iter):
        new_scores: dict[str, float] = defaultdict(float)

        # Teleport component
        for node_id, t_score in teleport.items():
            new_scores[node_id] += alpha * t_score

        # Random walk component
        for node_id in all_nodes:
            if scores[node_id] == 0:
                continue

            neighbors = graph.adj.get(node_id, [])
            if not neighbors:
                # Dangling node: distribute to teleport
                for t_id, t_score in teleport.items():
                    new_scores[t_id] += (1 - alpha) * scores[node_id] * t_score
                continue

            # Distribute score to neighbors (weighted)
            total_weight = sum(w for _, _, w in neighbors)
            for neighbor_id, _rel, weight in neighbors:
                share = (1 - alpha) * scores[node_id] * (weight / max(total_weight, 1e-9))
                new_scores[neighbor_id] += share

        # Check convergence
        diff = sum(abs(new_scores[n] - scores[n]) for n in all_nodes)
        scores = new_scores

        if diff < tolerance:
            break

    return dict(scores)


# ---------------------------------------------------------------------------
# ASSOCIATIVE QUERY
# ---------------------------------------------------------------------------
class AssociativeResult:
    """Result from associative memory query."""

    def __init__(
        self, entity_id: str, entity_type: str, label: str, person: str, score: float, is_seed: bool
    ):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.label = label
        self.person = person
        self.score = score
        self.is_seed = is_seed

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "label": self.label,
            "person": self.person,
            "score": round(self.score, 6),
            "is_seed": self.is_seed,
        }


def associative_search(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    exclude_seeds: bool = False,
    person_filter: str | None = None,
    graph: KnowledgeGraph | None = None,
) -> dict:
    """Find associatively related concepts using PPR.

    Args:
        query: Natural language query
        top_k: Number of results
        exclude_seeds: If True, don't include seed nodes in results
        person_filter: If set, only return results from this person
        graph: KnowledgeGraph instance

    Returns:
        {
            "query": str,
            "seeds": [{entity_id, score}, ...],
            "results": [AssociativeResult.to_dict(), ...],
            "total_activated": int,
        }
    """
    g = graph or get_graph()

    if not g.built:
        return {"query": query, "error": "Graph not built"}

    # Step 1: Activate seeds
    seeds = activate_seeds(query, graph=g)

    if not seeds:
        return {
            "query": query,
            "seeds": [],
            "results": [],
            "total_activated": 0,
        }

    # Step 2: Run PPR
    ppr_scores = personalized_pagerank(g, seeds)

    # Step 3: Build results
    results: list[AssociativeResult] = []

    for entity_id, score in ppr_scores.items():
        if score <= 0:
            continue

        entity = g.get_entity(entity_id)
        if not entity:
            continue

        # Skip non-content types (domains, agents)
        if entity.type in ("dominio", "agente"):
            continue

        if exclude_seeds and entity_id in seeds:
            continue

        if person_filter and entity.person.lower() != person_filter.lower():
            continue

        results.append(
            AssociativeResult(
                entity_id=entity.id,
                entity_type=entity.type,
                label=entity.label,
                person=entity.person,
                score=score,
                is_seed=entity_id in seeds,
            )
        )

    # Sort by score
    results.sort(key=lambda r: -r.score)
    results = results[:top_k]

    return {
        "query": query,
        "seeds": [
            {"entity_id": k, "score": round(v, 4)}
            for k, v in sorted(seeds.items(), key=lambda x: -x[1])
        ],
        "results": [r.to_dict() for r in results],
        "total_activated": len([s for s in ppr_scores.values() if s > 0]),
    }


def find_cross_expert_connections(
    concept: str,
    source_person: str | None = None,
    graph: KnowledgeGraph | None = None,
) -> dict:
    """Find how a concept from one expert connects to other experts.

    Example: "Christmas Tree Structure" (Hormozi) → similar patterns from others

    Args:
        concept: Concept name or ID
        source_person: The person who originated the concept (optional)
        graph: KnowledgeGraph instance

    Returns: Results grouped by person
    """
    g = graph or get_graph()

    # Search with concept, excluding source person from filter
    result = associative_search(
        query=concept,
        top_k=30,
        graph=g,
    )

    # Group by person
    by_person: dict[str, list[dict]] = defaultdict(list)
    for r in result.get("results", []):
        person = r.get("person", "unknown")
        by_person[person].append(r)

    # If source_person specified, move them to separate section
    source_results = by_person.pop(source_person, []) if source_person else []

    return {
        "concept": concept,
        "source_person": source_person,
        "source_results": source_results,
        "cross_expert": dict(by_person),
        "total_experts": len(by_person),
        "seeds": result.get("seeds", []),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse
    import time

    parser = argparse.ArgumentParser(description="Associative Memory (HippoRAG)")
    parser.add_argument(
        "--build", action="store_true", help="Load/validate graph and confirm readiness"
    )
    parser.add_argument("--query", type=str, help="Query text")
    parser.add_argument(
        "--cross-expert", type=str, help="Find cross-expert connections for concept"
    )
    parser.add_argument("--source-person", type=str, help="Source person for cross-expert query")
    parser.add_argument("--top-k", type=int, default=15)
    # Support positional query for backwards compatibility
    parser.add_argument("query_positional", nargs="?", help=argparse.SUPPRESS)
    args = parser.parse_args()

    query = args.query or args.query_positional

    print(f"\n{'=' * 60}")
    print("ASSOCIATIVE MEMORY (HippoRAG 2)")
    print(f"{'=' * 60}\n")

    if args.build:
        t0 = time.time()
        g = get_graph()
        elapsed = time.time() - t0
        stats = g.stats
        print(f"Graph loaded in {elapsed:.3f}s")
        print(f"Status: {'READY' if g.built else 'NOT BUILT'}")
        print(f"Entities: {stats['total_entities']}")
        print(f"Edges: {stats['total_edges']}")
        print(f"Adjacency entries: {len(g.adj)}")
        print(f"\nBy type:")
        for t, c in sorted(stats["entities_by_type"].items()):
            print(f"  {t}: {c}")
        print(f"\nBy relation:")
        for r, c in sorted(stats["edges_by_type"].items()):
            print(f"  {r}: {c}")
        print(f"\nAssociative memory index: READY")
        print(
            f"PPR config: alpha={PPR_ALPHA}, iterations={PPR_ITERATIONS}, tolerance={PPR_TOLERANCE}"
        )

    elif args.cross_expert:
        result = find_cross_expert_connections(
            args.cross_expert,
            source_person=args.source_person,
        )
        print(f"Concept: {result['concept']}")
        print(f"Source: {result['source_person'] or 'any'}")
        print(f"Cross-expert connections: {result['total_experts']} experts\n")

        if result["source_results"]:
            print(f"  From {result['source_person']}:")
            for r in result["source_results"][:5]:
                print(
                    f"    [{r['entity_type']}] {r['entity_id']}: "
                    f"{r['label'][:50]} (score={r['score']:.4f})"
                )

        for person, entries in result["cross_expert"].items():
            print(f"\n  From {person}:")
            for r in entries[:5]:
                print(
                    f"    [{r['entity_type']}] {r['entity_id']}: "
                    f"{r['label'][:50]} (score={r['score']:.4f})"
                )

    elif query:
        result = associative_search(query, top_k=args.top_k)
        print(f"Query: {result['query']}")
        print(f"Seeds: {len(result['seeds'])}")
        print(f"Activated: {result['total_activated']}\n")

        print("Seeds:")
        for s in result["seeds"][:5]:
            print(f"  {s['entity_id']}: {s['score']:.4f}")

        print(f"\nResults ({len(result['results'])}):")
        for r in result["results"]:
            seed_marker = " [SEED]" if r["is_seed"] else ""
            print(
                f"  [{r['entity_type']}] {r['entity_id']}: "
                f"{r['label'][:50]} (person={r['person']}, "
                f"score={r['score']:.6f}){seed_marker}"
            )
    else:
        print("Usage:")
        print("  --build                     Validate graph, show stats")
        print('  --query "text"              Associative search')
        print('  --cross-expert "concept"    Cross-expert connections')

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
