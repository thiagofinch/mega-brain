#!/usr/bin/env python3
"""
QUERY ORCHESTRATOR — Cross-Bucket RAG Search
=============================================
Infrastructure layer that receives natural language queries and searches
across knowledge buckets (external, business, personal) using BM25.

This is a LIBRARY FUNCTION, not an agent. Agents like sua-organizacao-oracle
consume this as a tool.

Architecture (from RT-AUDIT-2026-04-06, Q6):

    Query Orchestrator (infrastructure layer)
      -> Receives natural language query
      -> Routes to correct RAG bucket(s)
      -> Executes BM25 search in parallel
      -> Merges and ranks results cross-bucket
      -> Returns top-K with source attribution

    sua-organizacao-oracle (agent layer)
      -> Uses Query Orchestrator as a TOOL
      -> Applies business reasoning to results

Version: 1.0.0
Date: 2026-04-09
Ref: docs/architecture/roundtable-mega-brain-audit-decisions-2026-04-06.md (Q6)
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path

from engine.paths import KNOWLEDGE_PERSONAL, RAG_BUSINESS, RAG_INDEX

# ---------------------------------------------------------------------------
# DATA TYPES
# ---------------------------------------------------------------------------
VALID_BUCKETS = ("external", "business", "personal")

BUCKET_INDEX_DIRS: dict[str, Path] = {
    "external": RAG_INDEX,
    "business": RAG_BUSINESS,
    "personal": KNOWLEDGE_PERSONAL / "index",
}


@dataclass
class SearchResult:
    """A single search result with full source attribution."""

    text: str
    source_file: str
    bucket: str  # external | business | personal
    score: float
    chunk_id: str
    person: str = ""
    domain: str = ""
    section: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# Intents whose retrieval benefits from the graph/PPR (HippoRAG-2) path.
# These are the cross-expert / associative / analytical queries — "who else
# said something similar", "what do all experts agree on", "trace from X to Y".
# Factual single-expert lookups deliberately stay on the per-bucket BM25 path
# (no graph cost, no latency regression). Ref: STORY-GBA-W1.1.
GRAPH_ROUTED_INTENTS = frozenset({"cross_expert", "analytical", "hierarchical"})


@dataclass
class QueryResponse:
    """Full response from a query execution."""

    query: str
    results: list[SearchResult]
    buckets_searched: list[str]
    latency_ms: float
    errors: dict[str, str] = field(default_factory=dict)
    strategy: str = "hybrid"  # "hybrid" (BM25 per-bucket) | "hybrid_graph" (PPR)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "buckets_searched": self.buckets_searched,
            "latency_ms": round(self.latency_ms, 1),
            "total_results": len(self.results),
            "strategy": self.strategy,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# INDEX HELPERS
# ---------------------------------------------------------------------------
def _index_exists(index_dir: Path) -> bool:
    """Check whether a usable BM25 index exists at the given directory."""
    return (index_dir / "chunks.json").exists() and (index_dir / "bm25.json").exists()


def _search_single_bucket(
    question: str,
    bucket_name: str,
    index_dir: Path,
    top_k: int,
    filters: dict | None = None,
) -> list[SearchResult]:
    """Search a single bucket's BM25 index. Returns typed SearchResult list.

    Gracefully returns empty list if index missing or load fails.

    ``filters`` (STORY-F1-15 / 12b) is forwarded to ``hybrid_search`` so the
    ontology / metadata pre-filter propagates the whole read chain
    (store WHERE composite + query-layer filter). Default ``None`` = no filter.
    """
    if not _index_exists(index_dir):
        return []

    from .hybrid_index import HybridIndex
    from .hybrid_query import hybrid_search

    idx = HybridIndex()
    if not idx.load(index_dir):
        return []

    # S4 fix (2026-04-24): propagate bucket_name to hybrid_search.
    # Without this, hybrid_search defaults to bucket="external" which makes
    # pgvector RRF query the external Supabase table regardless of which
    # local HybridIndex was loaded — causing bucket/source_file mismatch
    # in SearchResult (bucket label says "business" but source_file is
    # knowledge/external/...). Ref: docs/stories/epic-rag-integrity-recovery/
    raw = hybrid_search(question, top_k=top_k, index=idx, bucket=bucket_name, filters=filters)
    if "error" in raw:
        return []

    results: list[SearchResult] = []
    for item in raw.get("results", []):
        # Get full text from the chunk if available
        chunk_text = item.get("text_preview", "")
        # Try to get full text from the index
        chunk_id = item.get("chunk_id", "")
        if chunk_id and idx.chunks:
            for chunk in idx.chunks:
                if chunk.get("chunk_id") == chunk_id:
                    chunk_text = chunk.get("text", chunk_text)
                    break

        results.append(
            SearchResult(
                text=chunk_text,
                source_file=item.get("source_file", ""),
                bucket=bucket_name,
                score=item.get("score", 0.0),
                chunk_id=chunk_id,
                person=item.get("person", ""),
                domain=item.get("domain", ""),
                section=item.get("section", ""),
            )
        )

    return results


# ---------------------------------------------------------------------------
# QUERY ORCHESTRATOR
# ---------------------------------------------------------------------------
def query(
    text: str,
    buckets: list[str] | None = None,
    top_k: int = 10,
    filters: dict | None = None,
) -> list[SearchResult]:
    """Search across knowledge buckets and return ranked results.

    Args:
        text: Natural language query.
        buckets: Which buckets to search. None = all 3.
            Valid values: "external", "business", "personal".
        top_k: Number of results to return.
        filters: Optional ontology / metadata pre-filter (STORY-F1-15 / 12b) —
            a dict of ``{person|domain|layer|source_type|quality_tier|entity_type|
            community_id|graph_id: value}`` propagated the whole read chain.

    Returns:
        List of SearchResult sorted by score descending, with source
        attribution (bucket + file + score).
    """
    response = query_full(text, buckets=buckets, top_k=top_k, filters=filters)
    return response.results


def _route_cross_expert(text: str, top_k: int) -> list[SearchResult] | None:
    """Route a cross-expert/associative query through the graph/PPR pipeline.

    This is the bridge STORY-GBA-W1.1 adds: the REST path (``query_full``) can
    now REACH the HippoRAG-2 Personalized PageRank that was previously wired
    ONLY via ``mcp_server.handle_search_cross_expert``. We REUSE the exact same
    entrypoint the MCP uses — ``adaptive_router.route_query(HYBRID_GRAPH)`` —
    which dispatches to ``graph_search`` -> ``associative_search`` ->
    ``personalized_pagerank`` (the black box is CALLED, never modified; RNF-1).

    Returns:
        A list of ``SearchResult`` mapped from the fused graph results, or
        ``None`` to signal the caller should FALL BACK to the per-bucket BM25
        path (graph not built, router unavailable, or no fused hits). Fail-open:
        any failure degrades to the legacy path, never breaks search.
    """
    try:
        from .adaptive_router import Pipeline, route_query
    except Exception:
        return None  # router unavailable -> fall back to BM25 path

    try:
        routed = route_query(text, pipeline=Pipeline.HYBRID_GRAPH)
    except Exception:
        return None  # any routing failure -> fail-open to BM25 path

    fused = routed.get("results", []) or []
    if not fused:
        # Graph not built / no associative hits -> let the caller use BM25 so
        # the cross-expert query still returns SOMETHING (no empty regression).
        return None

    results: list[SearchResult] = []
    for r in fused:
        # Fused items key the chunk/entity id under "id" (see
        # graph_query._fuse_graph_and_hybrid). Chunk-sourced items also carry
        # source_file; entity-sourced items carry the concept label only.
        chunk_id = r.get("id") or r.get("chunk_id") or ""
        text_val = r.get("text_preview") or r.get("label") or r.get("text") or ""
        results.append(
            SearchResult(
                text=text_val,
                source_file=r.get("source_file", ""),
                bucket="external",  # cross-expert knowledge lives in external
                score=float(r.get("score", 0.0)),
                chunk_id=chunk_id,
                person=r.get("person", ""),
                domain=r.get("domain", ""),
                section=r.get("section", ""),
            )
        )
    return results[:top_k]


def _ontology_hotpath_enabled() -> bool:
    """Kill-switch for the F1-17 ontology hot-path routing (default OFF).

    Local mirror of ``ontology_layer.ontology_hotpath_enabled`` — kept inline so
    the OFF hot-path never imports ``ontology_layer`` (zero new import cost when
    the flag is absent, preserving AC4 byte-identical routing). Same env var:
    ``ONTOLOGY_HOTPATH_ENABLED``.
    """
    return os.environ.get("ONTOLOGY_HOTPATH_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _route_ontological(text: str, top_k: int) -> list[SearchResult] | None:
    """Route an ontological/hierarchical query through the ontology LAYER traversal.

    STORY-F1-17: env-gated (``ONTOLOGY_HOTPATH_ENABLED``, default OFF). Dispatches
    the per-layer traversal (``ontology_layer.query_by_layer``) across the
    recognized ``LAYER_HIERARCHY`` (5 legacy types OFF / 12 Object Types ON)
    instead of the default associative/PPR path (AC2). We REUSE the traversal
    black box unchanged — it is CALLED, never modified. Only reached when the flag
    is ON (see ``query_full``), so the OFF path stays import-free.

    Returns:
        A list of ``SearchResult`` mapped from the ontology entities, or ``None``
        to signal FALL BACK to the existing cross-expert/BM25 path. Fail-open: any
        failure OR an empty traversal degrades to the legacy path (no empty
        regression, search never breaks).

    Nuance (F0-13 QA-3 dormancy): the traversal SPINE rels
    (GERA/PRODUZ/MATERIALIZA/IMPLEMENTA/RELACIONADA_COM) are 0-live today, so this
    surfaces per-layer entities (including the 7 newly-recognized Object Types
    when ON) but not multi-hop chains — real chain value awaits edge population
    ([7b]/F2). The expansion delivers a traversal that is READY, not fabricated
    edges.
    """
    try:
        from . import ontology_layer as ol
    except Exception:
        return None  # ontology layer unavailable -> fall back to the legacy path

    try:
        collected: list = []
        for layer in ol.LAYER_HIERARCHY:
            collected.extend(ol.query_by_layer(layer))
    except Exception:
        return None  # any traversal failure -> fail-open to the legacy path

    if not collected:
        # Graph not built / no entities -> let the caller use the legacy path so
        # the ontological query still returns SOMETHING (no empty regression).
        return None

    collected.sort(key=lambda r: -r.score)

    results: list[SearchResult] = []
    for r in collected[:top_k]:
        results.append(
            SearchResult(
                text=r.label,
                source_file="",  # ontology atoms are graph nodes, not chunks
                bucket="external",  # DNA ontology lives in the external bucket
                score=float(r.score),
                chunk_id=r.entity_id,
                person=r.person,
                domain="",
                section=r.entity_type,  # surface the recognized layer/type
            )
        )
    return results


def query_full(
    text: str,
    buckets: list[str] | None = None,
    top_k: int = 10,
    filters: dict | None = None,
) -> QueryResponse:
    """Full query with metadata (latency, errors, buckets searched).

    Same as query() but returns QueryResponse with diagnostics.

    Routing (STORY-GBA-W1.1): cross-expert / associative / analytical queries
    are routed through the graph/PPR pipeline (HYBRID_GRAPH) so the REST path
    reaches HippoRAG-2 Personalized PageRank. Factual single-expert queries
    stay on the per-bucket BM25 path (unchanged latency + behavior).

    Filtered retrieval (STORY-F1-15 / 12b): when ``filters`` is provided the
    graph/PPR and ontology fast-routes are BYPASSED — those paths surface graph
    nodes / associative fusions that do not carry the per-chunk ontology payload
    (entity_type/source_type/…), so they cannot honour a typed pre-filter. A
    typed query therefore takes the filterable per-bucket hybrid path, where the
    filter propagates all the way to the store WHERE composite. ``filters=None``
    (default) preserves the pre-12b routing byte-for-byte.
    """
    t0 = time.time()

    # Resolve buckets
    if buckets is None:
        target_buckets = list(VALID_BUCKETS)
    else:
        target_buckets = [b for b in buckets if b in VALID_BUCKETS]
        if not target_buckets:
            target_buckets = list(VALID_BUCKETS)

    # ----- CROSS-EXPERT ROUTING (graph/PPR) ---------------------------------
    # Cross-expert knowledge lives in the external bucket; only route to the
    # graph path when external is in scope (preserves bucket isolation, Art.
    # XIII — a business/personal-only query is never answered with external
    # graph hits). Classification REUSES adaptive_router.classify_intent.
    # 12b: a typed pre-filter (`filters`) forces the filterable hybrid path — the
    # graph/ontology routes below do not carry the ontology payload to filter on.
    if "external" in target_buckets and not filters:
        try:
            from .adaptive_router import classify_intent

            intent = classify_intent(text)
        except Exception:
            intent = "factual_simple"

        # ----- ONTOLOGICAL ROUTING (layer traversal) — STORY-F1-17 -----------
        # Env-gated (ONTOLOGY_HOTPATH_ENABLED, default OFF). When ON, an
        # ontological/hierarchical query dispatches the ontology LAYER traversal
        # (query_by_layer) instead of the default associative/PPR path (AC2). Flag
        # OFF => this branch short-circuits on the env read => routing is
        # byte-identical to today (AC4 — hierarchical still falls through to
        # _route_cross_expert below). Fail-open: _route_ontological returns None on
        # failure/empty => fall through to the cross-expert/BM25 path.
        if _ontology_hotpath_enabled() and intent == "hierarchical":
            onto_results = _route_ontological(text, top_k)
            if onto_results is not None:
                latency_ms = (time.time() - t0) * 1000
                response = QueryResponse(
                    query=text,
                    results=onto_results,
                    buckets_searched=["external"],
                    latency_ms=latency_ms,
                    strategy="ontology_traversal",
                )
                try:
                    from engine.intelligence.pipeline.consultation_logger import (
                        log_query_response,
                    )

                    log_query_response(
                        querying_agent="query_orchestrator", response=response
                    )
                except Exception:
                    pass
                return response
            # ontology path yielded nothing -> fall through to cross-expert/BM25.

        if intent in GRAPH_ROUTED_INTENTS:
            graph_results = _route_cross_expert(text, top_k)
            if graph_results is not None:
                latency_ms = (time.time() - t0) * 1000
                response = QueryResponse(
                    query=text,
                    results=graph_results,
                    buckets_searched=["external"],
                    latency_ms=latency_ms,
                    strategy="hybrid_graph",
                )
                try:
                    from engine.intelligence.pipeline.consultation_logger import (
                        log_query_response,
                    )

                    log_query_response(
                        querying_agent="query_orchestrator", response=response
                    )
                except Exception:
                    pass
                return response
            # graph path yielded nothing -> fall through to BM25 path below.

    # Search buckets in parallel
    all_results: list[SearchResult] = []
    errors: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=len(target_buckets)) as executor:
        futures = {}
        for bucket_name in target_buckets:
            index_dir = BUCKET_INDEX_DIRS.get(bucket_name)
            if index_dir is None:
                continue
            future = executor.submit(
                _search_single_bucket, text, bucket_name, index_dir, top_k, filters
            )
            futures[future] = bucket_name

        for future in as_completed(futures):
            bucket_name = futures[future]
            try:
                bucket_results = future.result()
                all_results.extend(bucket_results)
            except Exception as e:
                errors[bucket_name] = str(e)

    # Sort by score descending
    all_results.sort(key=lambda r: r.score, reverse=True)

    # Deduplicate by chunk_id (keep highest score)
    seen: set[str] = set()
    deduplicated: list[SearchResult] = []
    for result in all_results:
        if result.chunk_id and result.chunk_id in seen:
            continue
        if result.chunk_id:
            seen.add(result.chunk_id)
        deduplicated.append(result)

    latency_ms = (time.time() - t0) * 1000

    response = QueryResponse(
        query=text,
        results=deduplicated[:top_k],
        buckets_searched=target_buckets,
        latency_ms=latency_ms,
        errors=errors,
    )

    # Auto-log every query for observability (RT-AUDIT-2026-04-06, Action #13)
    try:
        from engine.intelligence.pipeline.consultation_logger import log_query_response

        log_query_response(querying_agent="query_orchestrator", response=response)
    except Exception:
        pass  # Logging failure must never break search

    return response


# ---------------------------------------------------------------------------
# CONVENIENCE FUNCTIONS
# ---------------------------------------------------------------------------
def search_external(
    text: str, top_k: int = 10, filters: dict | None = None
) -> list[SearchResult]:
    """Search only the external (expert) knowledge bucket.

    ``filters`` (STORY-F1-15 / 12b): optional ontology / metadata pre-filter,
    e.g. ``{"entity_type": "heuristica", "person": "cole-gordon"}``.
    """
    return query(text, buckets=["external"], top_k=top_k, filters=filters)


def search_business(
    text: str, top_k: int = 10, filters: dict | None = None
) -> list[SearchResult]:
    """Search only the business (meetings, calls, ops) bucket."""
    return query(text, buckets=["business"], top_k=top_k, filters=filters)


def search_personal(
    text: str, top_k: int = 10, filters: dict | None = None
) -> list[SearchResult]:
    """Search only the personal (founder cognitive) bucket."""
    return query(text, buckets=["personal"], top_k=top_k, filters=filters)


def parse_filters_arg(raw: str | None) -> dict | None:
    """Parse a CLI/MCP ``key=value,key2=value2`` filter string → dict | None.

    STORY-F1-15 / 12b. Blank / malformed pairs are skipped (never a crash); an
    empty result is returned as ``None`` so an empty filter string is identical to
    "no filter" (backward-compat). Keys/values are trimmed; the store layer
    whitelists the keys (unknown keys are inert), so this parser stays permissive.
    """
    if not raw:
        return None
    out: dict[str, str] = {}
    for pair in raw.split(","):
        if "=" not in pair:
            continue
        key, _, value = pair.partition("=")
        key, value = key.strip(), value.strip()
        if key and value:
            out[key] = value
    return out or None


def available_buckets() -> dict[str, dict]:
    """Return metadata about each bucket's index status.

    Returns:
        {bucket_name: {"index_dir": str, "exists": bool, "has_chunks": bool}}
    """
    import json

    status: dict[str, dict] = {}
    for bname, index_dir in BUCKET_INDEX_DIRS.items():
        exists = _index_exists(index_dir)
        chunk_count = 0
        if exists:
            chunks_file = index_dir / "chunks.json"
            try:
                data = json.loads(chunks_file.read_text())
                chunk_count = len(data) if isinstance(data, list) else 0
            except Exception:
                pass
        status[bname] = {
            "index_dir": str(index_dir),
            "exists": exists,
            "chunk_count": chunk_count,
        }
    return status


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point for query orchestrator."""
    if len(sys.argv) < 2:
        print(
            "Usage: python3 -m engine.intelligence.rag.query_orchestrator "
            "<query> [bucket1,bucket2] [--filter key=value,key2=value2]"
        )
        print()
        print("Examples:")
        print('  python3 -m engine.intelligence.rag.query_orchestrator "offer creation framework"')
        print(
            '  python3 -m engine.intelligence.rag.query_orchestrator "team meeting notes" business'
        )
        print('  python3 -m engine.intelligence.rag.query_orchestrator "closing" external,business')
        print(
            '  python3 -m engine.intelligence.rag.query_orchestrator "closing" external '
            '--filter entity_type=heuristica,person=cole-gordon'
        )
        print()
        print("Filter keys (12b): person, domain, layer, source_type, quality_tier,")
        print("                   entity_type, community_id, graph_id")
        print()

        # Show bucket status
        print("Bucket Status:")
        for bname, info in available_buckets().items():
            marker = "OK" if info["exists"] else "--"
            chunks = info["chunk_count"]
            print(f"  [{marker}] {bname:10s}  {chunks:>5} chunks  {info['index_dir']}")
        sys.exit(1)

    question = sys.argv[1]

    # Parse remaining args: an optional bucket list (comma-separated buckets) and
    # an optional `--filter key=value,...` flag (12b). Order-independent for the
    # filter flag; the first non-flag positional is treated as the bucket list.
    rest = sys.argv[2:]
    filter_raw: str | None = None
    bucket_raw: str | None = None
    i = 0
    while i < len(rest):
        tok = rest[i]
        if tok == "--filter" and i + 1 < len(rest):
            filter_raw = rest[i + 1]
            i += 2
            continue
        if bucket_raw is None:
            bucket_raw = tok
        i += 1

    # Parse optional bucket filter
    target_buckets: list[str] | None = None
    if bucket_raw:
        target_buckets = [b.strip() for b in bucket_raw.split(",") if b.strip() in VALID_BUCKETS]
        if not target_buckets:
            target_buckets = None

    filters = parse_filters_arg(filter_raw)

    print(f"\n{'=' * 60}")
    print("QUERY ORCHESTRATOR")
    print(f"{'=' * 60}")
    print(f"Query:   {question}")
    print(f"Buckets: {target_buckets or 'all'}")
    if filters:
        print(f"Filters: {filters}")
    print()

    response = query_full(question, buckets=target_buckets, filters=filters)

    print(f"Searched: {', '.join(response.buckets_searched)}")
    print(f"Results:  {len(response.results)}  ({response.latency_ms:.1f}ms)")
    if response.errors:
        for bkt, err in response.errors.items():
            print(f"  ERROR [{bkt}]: {err}")
    print()

    for i, r in enumerate(response.results, 1):
        print(f"  #{i} [{r.score:.4f}] ({r.bucket}) {r.chunk_id}")
        print(f"     File: {r.source_file}")
        if r.person:
            print(f"     Person: {r.person}")
        print(f"     {r.text[:120]}...")
        print()

    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
