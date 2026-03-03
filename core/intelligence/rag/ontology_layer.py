#!/usr/bin/env python3
"""
ONTOLOGY LAYER (OG-RAG) - Phase 4.3
======================================
Anchors retrieval in the DNA 5-layer ontology.
Provides ontology-aware retrieval that respects the hierarchy:

  FILOSOFIA → MODELO_MENTAL → HEURISTICA → FRAMEWORK → METODOLOGIA

Key features:
- Ontology-anchored retrieval (+55% fact recall per OG-RAG paper)
- Hierarchy traversal (trace from philosophy to methodology)
- Cross-layer expansion (find related concepts across layers)
- Threshold-based filtering (numeric heuristics)

Versao: 1.0.0
Data: 2026-03-01
"""

import sys
from typing import Dict, List, Optional, Set, Tuple

from .graph_builder import KnowledgeGraph, get_graph

# ---------------------------------------------------------------------------
# ONTOLOGY CONFIG
# ---------------------------------------------------------------------------
# Layer hierarchy (top to bottom)
LAYER_HIERARCHY = [
    "filosofia",
    "modelo_mental",
    "heuristica",
    "framework",
    "metodologia",
]

# Relationship types that connect layers downward
DOWNWARD_RELS = ["GERA", "PRODUZ", "MATERIALIZA", "IMPLEMENTA"]
CROSS_RELS = ["RELACIONADA_COM"]

# Default expansion depth
DEFAULT_DEPTH = 2


# ---------------------------------------------------------------------------
# ONTOLOGY QUERY TYPES
# ---------------------------------------------------------------------------
class OntologyResult:
    """Result from an ontology-aware query."""

    def __init__(self, entity_id: str, entity_type: str, label: str,
                 person: str, score: float, path: List[str]):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.label = label
        self.person = person
        self.score = score
        self.path = path  # Trail of entity IDs from root to this entity

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "label": self.label,
            "person": self.person,
            "score": round(self.score, 4),
            "path": self.path,
        }


# ---------------------------------------------------------------------------
# ONTOLOGY QUERIES
# ---------------------------------------------------------------------------
def trace_hierarchy(
    entity_id: str,
    direction: str = "both",
    max_depth: int = DEFAULT_DEPTH,
    graph: Optional[KnowledgeGraph] = None,
) -> List[OntologyResult]:
    """Trace the ontology hierarchy from an entity.

    Args:
        entity_id: Starting entity ID (e.g., "HEUR-AH-025")
        direction: "up" (toward filosofias), "down" (toward metodologias), "both"
        max_depth: Maximum traversal depth
        graph: KnowledgeGraph instance

    Returns: List of OntologyResult with hierarchy path
    """
    g = graph or get_graph()
    entity = g.get_entity(entity_id)
    if not entity:
        return []

    results: List[OntologyResult] = []
    visited: Set[str] = {entity_id}

    # Add starting entity
    results.append(OntologyResult(
        entity_id=entity.id,
        entity_type=entity.type,
        label=entity.label,
        person=entity.person,
        score=1.0,
        path=[entity.id],
    ))

    if direction in ("up", "both"):
        _traverse(g, entity_id, "up", max_depth, visited, [entity_id], results)

    if direction in ("down", "both"):
        _traverse(g, entity_id, "down", max_depth, visited, [entity_id], results)

    return results


def _traverse(
    graph: KnowledgeGraph,
    current_id: str,
    direction: str,
    depth: int,
    visited: Set[str],
    path: List[str],
    results: List[OntologyResult],
) -> None:
    """Recursive traversal of ontology hierarchy."""
    if depth <= 0:
        return

    neighbors = graph.get_neighbors(current_id)
    current_entity = graph.get_entity(current_id)
    current_layer_idx = _get_layer_index(current_entity.type if current_entity else "")

    for neighbor_id, rel_type, weight in neighbors:
        if neighbor_id in visited:
            continue

        neighbor = graph.get_entity(neighbor_id)
        if not neighbor or neighbor.type not in LAYER_HIERARCHY:
            continue

        neighbor_layer_idx = _get_layer_index(neighbor.type)

        # Check direction
        if direction == "up" and neighbor_layer_idx >= current_layer_idx:
            continue
        if direction == "down" and neighbor_layer_idx <= current_layer_idx:
            continue

        # Include cross-layer and hierarchy relationships
        if rel_type not in DOWNWARD_RELS + CROSS_RELS + ["RELACIONADA_COM"]:
            continue

        visited.add(neighbor_id)
        new_path = path + [neighbor_id]
        score = weight * (0.8 ** (len(new_path) - 1))  # Decay with distance

        results.append(OntologyResult(
            entity_id=neighbor.id,
            entity_type=neighbor.type,
            label=neighbor.label,
            person=neighbor.person,
            score=score,
            path=new_path,
        ))

        _traverse(graph, neighbor_id, direction, depth - 1,
                  visited, new_path, results)


def query_by_layer(
    layer: str,
    person: Optional[str] = None,
    domain: Optional[str] = None,
    graph: Optional[KnowledgeGraph] = None,
) -> List[OntologyResult]:
    """Get all entities of a specific ontology layer.

    Args:
        layer: One of LAYER_HIERARCHY values
        person: Filter by person (optional)
        domain: Filter by domain (optional)
        graph: KnowledgeGraph instance

    Returns: List of OntologyResult
    """
    g = graph or get_graph()
    results = []

    for entity in g.get_entities_by_type(layer):
        if person and entity.person.lower() != person.lower():
            continue
        if domain and domain.lower() not in [d.lower() for d in entity.domains]:
            continue

        results.append(OntologyResult(
            entity_id=entity.id,
            entity_type=entity.type,
            label=entity.label,
            person=entity.person,
            score=entity.weight,
            path=[entity.id],
        ))

    return sorted(results, key=lambda r: -r.score)


def find_by_domain(
    domain: str,
    expand: bool = True,
    graph: Optional[KnowledgeGraph] = None,
) -> Dict[str, List[OntologyResult]]:
    """Find all ontology entries for a domain, grouped by layer.

    Args:
        domain: Domain name (e.g., "vendas", "compensation")
        expand: If True, follow cross-layer references
        graph: KnowledgeGraph instance

    Returns: {layer: [OntologyResult, ...]} grouped by ontology layer
    """
    g = graph or get_graph()
    by_layer: Dict[str, List[OntologyResult]] = {
        layer: [] for layer in LAYER_HIERARCHY
    }

    domain_entities = g.get_entities_by_domain(domain)

    for entity in domain_entities:
        if entity.type not in LAYER_HIERARCHY:
            continue

        result = OntologyResult(
            entity_id=entity.id,
            entity_type=entity.type,
            label=entity.label,
            person=entity.person,
            score=entity.weight,
            path=[entity.id],
        )
        by_layer[entity.type].append(result)

        # Expand: trace hierarchy
        if expand:
            expanded = trace_hierarchy(entity.id, direction="both",
                                       max_depth=1, graph=g)
            for exp in expanded:
                if exp.entity_id != entity.id and exp.entity_type in by_layer:
                    # Reduce score for expanded results
                    exp.score *= 0.7
                    by_layer[exp.entity_type].append(exp)

    # Deduplicate and sort
    for layer in by_layer:
        seen = set()
        unique = []
        for r in sorted(by_layer[layer], key=lambda x: -x.score):
            if r.entity_id not in seen:
                seen.add(r.entity_id)
                unique.append(r)
        by_layer[layer] = unique

    return by_layer


def find_conflicts(
    person1: str,
    person2: str,
    graph: Optional[KnowledgeGraph] = None,
) -> List[dict]:
    """Find conflicts/tensions between two persons' ontologies.

    Returns list of conflict descriptions from CONFIG.yaml conexoes.
    """
    g = graph or get_graph()
    conflicts = []

    p1_id = f"PESSOA:{person1.lower()}"
    p2_id = f"PESSOA:{person2.lower()}"

    # Check edges between the two persons
    for edge in g.edges:
        if edge.rel_type == "TENSIONA":
            if ((edge.source == p1_id and edge.target == p2_id) or
                    (edge.source == p2_id and edge.target == p1_id)):
                conflicts.append({
                    "type": "tension",
                    "between": [person1, person2],
                    "topic": edge.metadata.get("em", ""),
                    "note": edge.metadata.get("nota", ""),
                })

    # Find overlapping domains with different approaches
    p1_entities = g.get_entities_by_person(person1)
    p2_entities = g.get_entities_by_person(person2)

    p1_domains = set()
    p2_domains = set()
    for e in p1_entities:
        p1_domains.update(d.lower() for d in e.domains)
    for e in p2_entities:
        p2_domains.update(d.lower() for d in e.domains)

    shared_domains = p1_domains & p2_domains
    for domain in shared_domains:
        p1_heur = [e for e in p1_entities
                   if e.type == "heuristica" and domain in
                   [d.lower() for d in e.domains]]
        p2_heur = [e for e in p2_entities
                   if e.type == "heuristica" and domain in
                   [d.lower() for d in e.domains]]
        if p1_heur and p2_heur:
            conflicts.append({
                "type": "competing_heuristics",
                "domain": domain,
                "person1_count": len(p1_heur),
                "person2_count": len(p2_heur),
            })

    return conflicts


def find_numeric_heuristics(
    domain: Optional[str] = None,
    person: Optional[str] = None,
    graph: Optional[KnowledgeGraph] = None,
) -> List[dict]:
    """Find heuristics with numeric thresholds (decision gates).

    These are the most actionable items in the ontology.
    """
    g = graph or get_graph()
    results = []

    for entity in g.get_entities_by_type("heuristica"):
        if person and entity.person.lower() != person.lower():
            continue
        if domain and domain.lower() not in [d.lower() for d in entity.domains]:
            continue

        # Check if entity has threshold metadata
        if entity.metadata.get("has_threshold"):
            results.append({
                "entity_id": entity.id,
                "label": entity.label,
                "person": entity.person,
                "domains": entity.domains,
                "weight": entity.weight,
            })

    return results


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _get_layer_index(entity_type: str) -> int:
    """Get the index of a layer in the hierarchy. -1 if not found."""
    try:
        return LAYER_HIERARCHY.index(entity_type)
    except ValueError:
        return -1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ontology Layer (OG-RAG)")
    parser.add_argument("--trace", type=str, help="Trace hierarchy from entity ID")
    parser.add_argument("--domain", type=str, help="Find by domain")
    parser.add_argument("--layer", type=str, help="Query by layer",
                        choices=LAYER_HIERARCHY)
    parser.add_argument("--person", type=str, help="Filter by person")
    parser.add_argument("--conflicts", nargs=2, help="Find conflicts between persons")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("ONTOLOGY LAYER (OG-RAG)")
    print(f"{'='*60}\n")

    graph = get_graph()
    print(f"Graph: {graph.stats['total_entities']} entities, "
          f"{graph.stats['total_edges']} edges\n")

    if args.trace:
        results = trace_hierarchy(args.trace, graph=graph)
        print(f"Hierarchy trace for: {args.trace}\n")
        for r in results:
            indent = "  " * (len(r.path) - 1)
            print(f"{indent}[{r.entity_type}] {r.entity_id}: "
                  f"{r.label[:60]} (score={r.score:.2f})")

    elif args.domain:
        by_layer = find_by_domain(args.domain, graph=graph)
        print(f"Domain: {args.domain}\n")
        for layer in LAYER_HIERARCHY:
            entries = by_layer[layer]
            if entries:
                print(f"  {layer.upper()} ({len(entries)}):")
                for r in entries[:5]:
                    print(f"    [{r.person}] {r.entity_id}: "
                          f"{r.label[:50]} (score={r.score:.2f})")

    elif args.layer:
        results = query_by_layer(args.layer, person=args.person, graph=graph)
        print(f"Layer: {args.layer} ({len(results)} entries)\n")
        for r in results[:20]:
            print(f"  [{r.person}] {r.entity_id}: {r.label[:60]}")

    elif args.conflicts:
        conflicts = find_conflicts(args.conflicts[0], args.conflicts[1], graph=graph)
        print(f"Conflicts between {args.conflicts[0]} and {args.conflicts[1]}:\n")
        for c in conflicts:
            if c["type"] == "tension":
                print(f"  TENSION in {c['topic']}: {c['note']}")
            else:
                print(f"  COMPETING HEURISTICS in {c['domain']}: "
                      f"{c['person1_count']} vs {c['person2_count']}")
    else:
        # Default: show layer distribution
        for layer in LAYER_HIERARCHY:
            entities = graph.get_entities_by_type(layer)
            print(f"  {layer}: {len(entities)} entities")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
