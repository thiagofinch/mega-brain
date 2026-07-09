#!/usr/bin/env python3
"""
KNOWLEDGE GRAPH BUILDER - Phase 4.2 + MCE Extension
=====================================================
Builds a knowledge graph from DNA YAML files.
Extracts entities (5 DNA layers + 5 MCE layers + Pessoa + Dominio)
and relationships.

MCE layers (Mind-Clone Enhancement):
- behavioral_pattern  (from BEHAVIORAL-PATTERNS.yaml)
- value               (from VALUES-HIERARCHY.yaml)
- obsession           (from OBSESSIONS.yaml L9, fallback: VALUES-HIERARCHY.yaml, VOICE-DNA.yaml)
- paradox             (from PARADOXES.yaml L10, fallback: VALUES-HIERARCHY.yaml, VOICE-DNA.yaml)
- voice_trait          (from VOICE-DNA.yaml -- signature phrases, metaphors)

Supports LazyGraphRAG pattern: community summaries generated on-demand.

Versao: 2.1.0
Data: 2026-03-28
"""

import json
import logging
import os
import time
from collections import defaultdict
from pathlib import Path

import yaml

try:  # sibling module — package import in all real usage; fallback for direct-script run
    from . import derivational_edges as _derivational
except ImportError:  # pragma: no cover - direct ``python graph_builder.py`` execution
    import derivational_edges as _derivational  # type: ignore

logger = logging.getLogger(__name__)

# STORY-213.W1.2 — the derivational spine (GERA/PRODUZ/MATERIALIZA/IMPLEMENTA +
# PERTENCE_A via entity.domains) is env-gated, default OFF, so the DEFAULT build stays
# byte-identical to today (the golden PPR + structural characterizations hold, AC4/AC5)
# and W4.2's conclave A/B can compare braço A (spine OFF) vs braço B (spine ON).
# Mirrors the ONTOLOGY_HOTPATH_ENABLED kill-switch convention.
_DERIVATIONAL_TRUTHY = ("1", "true", "yes", "on")


def derivational_edges_enabled() -> bool:
    """Kill-switch ``MB_DERIVATIONAL_EDGES_ENABLED`` (default OFF — STORY-213.W1.2)."""
    return (
        os.environ.get("MB_DERIVATIONAL_EDGES_ENABLED", "0").strip().lower()
        in _DERIVATIONAL_TRUTHY
    )

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DNA_DIR = BASE_DIR / "knowledge" / "external" / "dna" / "persons"
GRAPH_DIR = BASE_DIR / ".data" / "knowledge_graph"

# STORY-RAG-VM-G2: one graph file per bucket (Art. XIII isolation is STRUCTURAL —
# separate files, never merged in runtime). The external bucket keeps the legacy
# default ``GRAPH_FILE`` pointing at ``graph-external.json``; ``graph.json`` is kept
# as an ALIAS (cheap copy on save) for ONE release so read-only stats readers that
# still hardcode ``graph.json`` (health_check, mcp_tools, log_generator) don't break.
LEGACY_GRAPH_FILE = GRAPH_DIR / "graph.json"


def graph_file_for_bucket(bucket: str = "external") -> Path:
    """Resolve the on-disk graph path for a bucket → ``graph-{bucket}.json``.

    The single seam that maps ``bucket`` → file. Callers (rebuild, enrich, the PPR
    loader) go through this so the naming contract lives in ONE place.
    """
    return GRAPH_DIR / f"graph-{bucket}.json"


# Default file = external bucket. Kept named ``GRAPH_FILE`` so every existing
# importer (rag_integration, hyperedge_materializer, CLI) keeps working unchanged
# while now resolving to ``graph-external.json`` instead of ``graph.json``.
GRAPH_FILE = graph_file_for_bucket("external")
# Durable hyperedge sidecar (STORY-HGA-F2.2 / constraint R1). build_graph() replays
# it at the end (business bucket only — STORY-RAG-VM-G2), so materialized hyperedges
# survive the per-bucket overwrite. Absent/empty = no-op → byte-identical graph.
OVERLAY_FILE = GRAPH_DIR / "he-overlay.json"

# DNA layer file → top-level key mapping
LAYER_KEYS = {
    "FILOSOFIAS.yaml": "filosofias",
    "MODELOS-MENTAIS.yaml": "modelos_mentais",
    "HEURISTICAS.yaml": "heuristicas",
    "FRAMEWORKS.yaml": "frameworks",
    "METODOLOGIAS.yaml": "metodologias",
}

# MCE layer file → (top-level key, entity type) mapping
MCE_LAYER_KEYS = {
    "BEHAVIORAL-PATTERNS.yaml": {
        "key": "behavioral_patterns",
        "entity_type": "behavioral_pattern",
        "rel_type": "MANIFESTA",
    },
    "VALUES-HIERARCHY.yaml": {
        "sections": {
            "values": {
                "entity_type": "value",
                "rel_type": "PRIORIZA",
            },
            "obsessions": {
                "entity_type": "obsession",
                "rel_type": "OBSECADO_COM",
            },
            "paradoxes": {
                "entity_type": "paradox",
                "rel_type": "TENSIONA_PARADOXO",
            },
        },
    },
    "VOICE-DNA.yaml": {
        "key": "signature_phrases",
        "entity_type": "voice_trait",
        "rel_type": "EXPRESSA",
        "alt_keys": ["metaphors", "catchphrases", "verbal_patterns"],
    },
    "OBSESSIONS.yaml": {
        "key": "obsessions",
        "entity_type": "obsession",
        "rel_type": "OBSECADO_COM",
        "alt_keys": ["obsessoes"],
    },
    "PARADOXES.yaml": {
        "key": "paradoxes",
        "entity_type": "paradox",
        "rel_type": "TENSIONA_PARADOXO",
        "alt_keys": ["paradoxos"],
    },
}

# ---------------------------------------------------------------------------
# STORY-S3 (completude-total): MULTI-SOURCE ROUTING
# ---------------------------------------------------------------------------
# Founder decision (locked 2026-06-30): INCLUDE EVERYTHING. Every source in the
# table enters the graph — never excluded, only TAGGED (source_type + quality_tier)
# so downstream query (S4) can FILTER noise without losing it from the brain.
#
# Each entry maps ``bucket → on-disk source dir`` and the provenance tags every
# node from that dir carries. ``quality_tier``:
#   curated     — human/LLM-distilled, structured authoring (dossier, playbook, insight)
#   structured  — has frontmatter/schema but mechanically produced (source, advisory-board)
#   raw         — unprocessed capture (inbox, meeting refs)
#
# Art. XIII isolation is STRUCTURAL: a bucket only ever reads its OWN dirs here,
# so a business source can never land in the external graph (and vice-versa).
# ``recursive`` walks subdirs (sorted) for honest determinism.
SOURCE_ROUTING: dict[str, list[dict]] = {
    "external": [
        {"dir": "dossiers", "source_type": "dossier", "quality_tier": "curated"},
        {"dir": "playbooks", "source_type": "playbook", "quality_tier": "curated"},
        {"dir": "sources", "source_type": "source", "quality_tier": "structured"},
        {"dir": "inbox", "source_type": "inbox", "quality_tier": "raw"},
    ],
    "business": [
        {"dir": "advisory-board", "source_type": "advisory-board", "quality_tier": "structured"},
        {"dir": "the-machine", "source_type": "the-machine", "quality_tier": "curated"},
        {"dir": "insights", "source_type": "insight", "quality_tier": "curated"},
        {"dir": "dossiers", "source_type": "dossier", "quality_tier": "curated"},
        {"dir": "sources", "source_type": "source", "quality_tier": "structured"},
        {"dir": "inbox", "source_type": "inbox", "quality_tier": "raw"},
    ],
    "personal": [
        {"dir": "dossiers", "source_type": "dossier", "quality_tier": "curated"},
        {"dir": "cognitive", "source_type": "personal", "quality_tier": "curated"},
        {"dir": "inbox", "source_type": "inbox", "quality_tier": "raw"},
    ],
}

# Workspace TTL → bucket routing (Art. XIV layer hierarchy). Workspace is BUSINESS
# data (per-BU L0-L4) → routes to the BUSINESS graph only (Art. XIII: never external/
# personal). Each layer carries a TTL; nodes from short-TTL layers are VOLATILE and
# tagged so the prune pass (and S4) can treat churn explicitly without deleting them.
# TTLs mirror CLAUDE.md "Workspace (L0-L4)".
WORKSPACE_BUCKET = "business"
WORKSPACE_LAYER_TTL_DAYS = {
    "L0-identity": 365,
    "L1-strategy": 90,
    "L2-tactical": 60,
    "L3-product": 30,
    "L4-operational": 7,
}
# A layer is VOLATILE when its TTL is short enough that the doc is expected to churn
# between rebuilds. L3/L4 (≤30d) are volatile; L0-L2 are durable. Volatile nodes are
# NEVER pruned for being volatile — the tag is a filter signal, not a delete trigger.
WORKSPACE_VOLATILE_TTL_THRESHOLD_DAYS = 30

# File extensions an honest text adapter can open. PDFs/binaries are recorded as a
# document node by FILENAME only (no fabricated body) — extraction_gap on content.
_TEXT_SUFFIXES = {".md", ".yaml", ".yml"}
_DOC_SUFFIXES = _TEXT_SUFFIXES | {".pdf", ".txt", ".json"}

# Entity types
ENTITY_TYPES = [
    "pessoa",
    "dominio",
    "filosofia",
    "modelo_mental",
    "heuristica",
    "framework",
    "metodologia",
    # MCE entity types
    "behavioral_pattern",
    "value",
    "obsession",
    "paradox",
    "voice_trait",
    # Hypergraph (STORY-HGA-F2.1 / GAP-HE-001): synthetic node-event H that
    # represents an N-ary relation. It is the star-expansion center; PPR flows
    # probability *through* it (2-hop) between co-participants. Ignored by the
    # ontology layer (type not in LAYER_HIERARCHY).
    "hyperedge",
    # STORY-S3 (completude-total): multi-source graph. ``fonte`` is the synthetic
    # anchor node-event for a non-DNA source family (one per source_type); ``documento``
    # is a single ingested file (dossier/playbook/source/inbox/meeting/insight/
    # advisory-board/the-machine/personal); ``workspace_doc`` is a workspace L0-L4
    # artifact (volatile per TTL). These live in a component DISJOINT from the DNA
    # subgraph — no edge touches a DNA-built node — so PPR over DNA seeds is unmoved
    # (AC4/RNF-1). All ignored by the ontology layer (types not in LAYER_HIERARCHY).
    "fonte",
    "documento",
    "workspace_doc",
]

# Relationship types
REL_TYPES = [
    "TEM",  # Pessoa → DNA entry
    "PERTENCE_A",  # Entry → Dominio
    "GERA",  # Filosofia → ModeloMental
    "PRODUZ",  # ModeloMental → Heuristica
    "MATERIALIZA",  # Heuristica → Framework
    "IMPLEMENTA",  # Framework → Metodologia
    "RELACIONADA_COM",  # Cross-layer reference (filosofia_relacionada, etc.)
    "COMPLEMENTA",  # Pessoa → Pessoa
    "TENSIONA",  # Pessoa → Pessoa (conflict)
    "ALINHA",  # Pessoa → Pessoa (agreement)
    "CONSOME",  # Agente → Pessoa DNA
    # MCE relationship types
    "MANIFESTA",  # Pessoa → behavioral_pattern
    "PRIORIZA",  # Pessoa → value
    "OBSECADO_COM",  # Pessoa → obsession
    "TENSIONA_PARADOXO",  # Pessoa → paradox
    "EXPRESSA",  # Pessoa → voice_trait
    # Hypergraph (STORY-HGA-F2.1 / GAP-HE-001): hyperedge-node H ↔ participant.
    # Deliberately NOT "RELACIONADA_COM" — the spike (STORY-HGA-F0.1) proved that
    # CROSS_RELS already contains "RELACIONADA_COM" (ontology_layer.py:36) and the
    # ontology traverse accepts it (:157), which would leak H into trace_hierarchy.
    # "PARTICIPA" is in neither DOWNWARD_RELS nor CROSS_RELS → F4 doubly-guarded.
    "PARTICIPA",  # hyperedge-node H → member (and reverse, via add_edge)
    # STORY-S3 (completude-total): a non-DNA source document belongs to its source
    # family anchor (``FONTE:{source_type}`` → ``DOC:...``). Deliberately NOT a
    # cross/downward ontology rel — keeps the multi-source component disjoint from
    # the DNA ontology so PPR over DNA seeds never reaches it (AC4/RNF-1).
    "CONTEM",  # fonte anchor → documento (and reverse, via add_edge)
]


# ---------------------------------------------------------------------------
# ENTITY & EDGE MODELS
# ---------------------------------------------------------------------------
class Entity:
    """A node in the knowledge graph."""

    __slots__ = (
        "domains",
        "id",
        "label",
        "layer",
        "metadata",
        "person",
        "quality_tier",
        "source_type",
        "type",
        "weight",
    )

    def __init__(self, entity_id: str, entity_type: str, label: str, **kwargs):
        self.id = entity_id
        self.type = entity_type
        self.label = label
        self.person = kwargs.get("person", "")
        self.domains = kwargs.get("domains", [])
        self.layer = kwargs.get("layer", "")
        self.weight = kwargs.get("weight", 1.0)
        self.metadata = kwargs.get("metadata", {})
        # STORY-S3 (completude-total): provenance tags. ``None`` sentinel (NOT "")
        # so untagged nodes — every DNA/MCE node built before S3 added per-source
        # tagging — serialize byte-identically (omit-when-None in ``to_dict``,
        # mirroring ``Edge.t_start``). AC7/No-Invention: an absent tag is a real
        # extraction gap (``null``), never a fabricated default.
        #   source_type  ∈ {dna, dossier, playbook, source, inbox, meeting,
        #                    workspace, insight, advisory-board, the-machine, personal}
        #   quality_tier ∈ {curated, structured, raw}
        self.source_type = kwargs.get("source_type")  # default None (sentinel)
        self.quality_tier = kwargs.get("quality_tier")  # default None (sentinel)

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "person": self.person,
            "domains": self.domains,
            "layer": self.layer,
            "weight": self.weight,
        }
        # Omit-when-None (mirrors Edge.t_start): a node without a provenance tag —
        # every node produced before S3 wired per-source tagging — serializes
        # byte-identically to the pre-S3 graph. CRITICAL for AC4/RNF-1
        # (graph-external.json DNA subset must not move byte-a-byte).
        if self.source_type is not None:
            d["source_type"] = self.source_type
        if self.quality_tier is not None:
            d["quality_tier"] = self.quality_tier
        return d


class Edge:
    """A relationship in the knowledge graph.

    Temporal + evidence fields (STORY-HGA-F1.1, ported from Hyper-Extract's
    ``EdgeSchema`` @ SHA 4e333f847f1d) are ADDITIVE and omit-when-empty:

    - ``t_start``: interval(s) when the relationship begins/is active (default []).
    - ``t_end``: interval(s) when the relationship ceases to hold (default []).
    - ``t_obs``: observation timestamp(s), populated post-processing (default None
      — sentinel, mirrors the upstream ``default=None``).
    - ``atomic_facts``: verbatim source sentences that justify this edge — the
      anti-hallucination evidence trail (default []).

    All four are omitted from ``to_dict`` when empty/None, so a ``graph.json``
    produced before this story serializes byte-identically.
    """

    __slots__ = (
        "atomic_facts",
        "metadata",
        "rel_type",
        "source",
        "t_end",
        "t_obs",
        "t_start",
        "target",
        "weight",
    )

    def __init__(self, source: str, target: str, rel_type: str, **kwargs):
        self.source = source
        self.target = target
        self.rel_type = rel_type
        self.weight = kwargs.get("weight", 1.0)
        self.metadata = kwargs.get("metadata", {})
        # Temporal + evidence — None sentinels avoid any shared mutable default.
        t_start = kwargs.get("t_start")
        t_end = kwargs.get("t_end")
        atomic_facts = kwargs.get("atomic_facts")
        self.t_start = t_start if t_start is not None else []
        self.t_end = t_end if t_end is not None else []
        self.t_obs = kwargs.get("t_obs")  # default None (sentinel, kept as-is)
        self.atomic_facts = atomic_facts if atomic_facts is not None else []

    def to_dict(self) -> dict:
        d = {
            "source": self.source,
            "target": self.target,
            "rel_type": self.rel_type,
            "weight": self.weight,
        }
        if self.metadata:
            d["metadata"] = self.metadata
        # Omit-when-empty: legacy edges (no temporal) serialize unchanged.
        if self.t_start:
            d["t_start"] = self.t_start
        if self.t_end:
            d["t_end"] = self.t_end
        if self.t_obs:
            d["t_obs"] = self.t_obs
        if self.atomic_facts:
            d["atomic_facts"] = self.atomic_facts
        return d


class Hyperedge:
    """An N-ary relationship — the LOSSLESS source-of-truth (STORY-HGA-F2.1).

    Where ``Edge`` is binary (one ``source`` → one ``target``), a ``Hyperedge``
    records that N entities co-participated in the SAME event/relation (a meeting,
    a collaboration, an N-party transaction). Collapsing it into K*(K-1)/2 binary
    pairs is lossy — it asserts every pair is *directly* related and forgets they
    were jointly part of one fact.

    Ported from Hyper-Extract's hyperedge model (``hypergraph.py`` @ SHA
    4e333f847f1d): identity is the **sorted set** of participants, so ``{A,B}`` and
    ``{B,A}`` map to the same hyperedge (``edge_key_extractor`` :165/190 →
    ``f"{rel}_{sorted(participants)}"``). Carries the temporal/evidence fields of
    HE-002 so they live in ONE addressable place rather than scattered over pairs.

    This model is the *truth*. ``KnowledgeGraph.add_hyperedge`` produces the
    *derived view* the PPR consumes — a star-expansion (1 node-event H + N member
    edges). The PPR walker is never edited (RNF-1): the view enters ``graph.adj``
    upstream via the existing ``add_edge`` door.
    """

    __slots__ = (
        "atomic_facts",
        "metadata",
        "participants",
        "rel_label",
        "rel_type",
        "t_end",
        "t_obs",
        "t_start",
        "weight",
    )

    def __init__(
        self,
        participants: list[str],
        rel_label: str,
        *,
        rel_type: str = "PARTICIPA",
        weight: float = 1.0,
        **kwargs,
    ):
        # Sorted-set identity — {A,B} == {B,A}. Mirrors HE hypergraph.py:165/190.
        self.participants = sorted(participants)
        self.rel_label = rel_label
        self.rel_type = rel_type
        self.weight = weight
        self.metadata = kwargs.get("metadata", {})
        # Temporal + evidence (HE-002) — None sentinels avoid shared mutable defaults.
        t_start = kwargs.get("t_start")
        t_end = kwargs.get("t_end")
        atomic_facts = kwargs.get("atomic_facts")
        self.t_start = t_start if t_start is not None else []
        self.t_end = t_end if t_end is not None else []
        self.t_obs = kwargs.get("t_obs")  # default None (sentinel)
        self.atomic_facts = atomic_facts if atomic_facts is not None else []

    @property
    def id(self) -> str:
        """Stable, dedup-safe synthetic id of the node-event H.

        ``he::{rel_label}::m1|m2|...|mN`` with members SORTED — so re-adding the
        same hyperedge (any participant order) yields the same id (idempotent).
        """
        return f"he::{self.rel_label}::" + "|".join(self.participants)

    @property
    def arity(self) -> int:
        return len(self.participants)


# ---------------------------------------------------------------------------
# KNOWLEDGE GRAPH
# ---------------------------------------------------------------------------
class KnowledgeGraph:
    """In-memory knowledge graph with JSON persistence."""

    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self.edges: list[Edge] = []
        self.adj: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
        self.built = False
        # STORY-F1-7A — persisted communities (``detect_communities`` output).
        # ``None`` is the "not persisted / unknown" sentinel: a fresh graph, or a
        # legacy graph saved before F1-7A (no ``communities`` key on disk), leaves
        # this None so ``get_communities`` recomputes (backward-compat, AC2). A
        # list (possibly ``[]``) means the value was persisted by ``save()`` /
        # hydrated by ``load()`` — an empty list is an HONEST "no community" (AC4),
        # never recomputed away nor fabricated.
        self.communities: list[dict] | None = None

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)
        self.adj[edge.source].append((edge.target, edge.rel_type, edge.weight))
        self.adj[edge.target].append((edge.source, edge.rel_type, edge.weight))

    def add_hyperedge(
        self,
        participants: list[str],
        rel_label: str,
        *,
        rel_type: str = "PARTICIPA",
        weight: float = 1.0,
        t_start: list[str] | None = None,
        t_end: list[str] | None = None,
        t_obs: list[str] | None = None,
        atomic_facts: list[str] | None = None,
        metadata: dict | None = None,
    ) -> str:
        """Star-expand an N-ary hyperedge into 1 node-event H + N member edges.

        The N-ary ``Hyperedge`` is the lossless source-of-truth; the star-expansion
        is the derived *view* the PPR consumes. For members ``{m_1, …, m_N}``:

          1. one synthetic ``Entity(type="hyperedge")`` H — home of ``rel_label``;
          2. N member edges ``H ↔ m_i`` (``rel_type="PARTICIPA"``), each inserted via
             :meth:`add_edge` — the SOLE writer of ``adj`` — which writes BOTH
             directions, so PPR flows probability through H (2-hop) between members.

        Linear (N edges), not clique (O(N²)): a 5-member relation is 5 edges, not 10.
        This is the production API the spike (STORY-HGA-F0.1) proved safe — it does
        NOT touch the PPR walker (RNF-1); the view enters upstream via ``add_edge``.

        The HE temporal/evidence fields (HE-002) ride on the member edges, so a
        time-filtered subgraph can later prune them without re-deriving identity.

        Args:
            participants: member entity ids — ALL must already exist (strict).
            rel_label: human label of the relation (e.g. "collaboration"). Becomes
                the H node label and part of H's id.
            rel_type: edge rel_type for the member edges. Default ``"PARTICIPA"`` —
                deliberately NOT ``"RELACIONADA_COM"`` (that would leak H into the
                ontology layer; see REL_TYPES note).
            weight: edge weight for the member edges.
            t_start, t_end, t_obs, atomic_facts: HE-002 temporal/evidence, copied
                onto each member edge.
            metadata: extra metadata merged onto each member edge (after the
                hyperedge bookkeeping keys).

        Returns:
            The id of the synthetic hyperedge node H.

        Raises:
            ValueError: if any participant does not already exist as a node —
                strict consistency, mirroring HE's ``_prune_dangling_edges``
                (hypergraph.py:540, "ALL participants must exist"). HE prunes; we
                raise, because in mb the caller controls insertion order and a
                dangling hyperedge is a programming error, not noisy LLM output.
        """
        he = Hyperedge(
            participants=participants,
            rel_label=rel_label,
            rel_type=rel_type,
            weight=weight,
            t_start=t_start,
            t_end=t_end,
            t_obs=t_obs,
            atomic_facts=atomic_facts,
        )
        he_id = he.id

        # 1. Strict consistency (RNF-G2 / HE hypergraph.py:540) — ALL participants
        #    must exist BEFORE any star edge is written. Check first so we never
        #    leave a half-built hyperedge (no partial adj mutation on failure).
        missing = [m for m in he.participants if m not in self.entities]
        if missing:
            raise ValueError(
                f"add_hyperedge: {he_id} references unknown nodes: {missing} "
                f"(strict consistency — add all participants as entities first)"
            )

        # 2. The synthetic node-event H (idempotent on the sorted-set id).
        if he_id not in self.entities:
            self.add_entity(
                Entity(entity_id=he_id, entity_type="hyperedge", label=rel_label)
            )

        # 3. N member edges — same door (add_edge) as every other edge, so each
        #    writes BOTH adj directions. PPR is agnostic to rel_type, so it walks
        #    these identically to native edges (associative_memory.py:152).
        for i, member in enumerate(he.participants):
            edge_meta = {
                "type": "hyperedge_member",
                "he_rel": rel_label,
                "member_index": i,
                "arity": he.arity,
            }
            if metadata:
                edge_meta.update(metadata)
            self.add_edge(
                Edge(
                    source=he_id,
                    target=member,
                    rel_type=rel_type,
                    weight=weight,
                    t_start=t_start or [],
                    t_end=t_end or [],
                    t_obs=t_obs,
                    atomic_facts=atomic_facts or [],
                    metadata=edge_meta,
                )
            )
        return he_id

    # ------------------------------------------------------------------
    # Iron Law: Bidirectional Backlinks (W2-001.9)
    # ------------------------------------------------------------------
    def _edge_exists(self, source: str, target: str, rel_type: str) -> bool:
        """Check whether a directed edge source->target with rel_type already exists."""
        return any(
            e.source == source and e.target == target and e.rel_type == rel_type for e in self.edges
        )

    def add_edge_with_backlink(self, edge: Edge) -> None:
        """Add a directed edge A->B and guarantee the reverse backlink B->A exists.

        The backlink carries metadata ``{"type": "backlink", "source": edge.source}``
        so it can be distinguished from edges created directly.
        """
        # 1. Add the forward edge (always)
        self.add_edge(edge)

        # 2. Guarantee the reverse backlink
        if not self._edge_exists(edge.target, edge.source, edge.rel_type):
            backlink = Edge(
                source=edge.target,
                target=edge.source,
                rel_type=edge.rel_type,
                weight=edge.weight,
                metadata={"type": "backlink", "source": edge.source},
            )
            self.add_edge(backlink)

    def enforce_iron_law(self) -> dict:
        """Full-graph consistency pass: for every edge A->B ensure B->A exists.

        Returns a report dict with the number of backlinks that were missing
        and had to be created.
        """
        missing: list[tuple[str, str, str]] = []

        # Build a set of (source, target, rel_type) for O(1) lookup
        existing = {(e.source, e.target, e.rel_type) for e in self.edges}

        for edge in list(self.edges):  # snapshot -- we may append during iteration
            reverse_key = (edge.target, edge.source, edge.rel_type)
            if reverse_key not in existing:
                missing.append(reverse_key)
                existing.add(reverse_key)  # prevent duplicate creation

        for src, tgt, rtype in missing:
            backlink = Edge(
                source=src,
                target=tgt,
                rel_type=rtype,
                weight=1.0,
                metadata={"type": "backlink", "source": tgt},
            )
            self.add_edge(backlink)

        return {
            "checked_edges": len(self.edges) - len(missing),
            "backlinks_created": len(missing),
            "total_edges_after": len(self.edges),
        }

    def get_entity(self, entity_id: str) -> Entity | None:
        return self.entities.get(entity_id)

    def get_neighbors(
        self, entity_id: str, rel_type: str | None = None
    ) -> list[tuple[str, str, float]]:
        """Get neighbors of an entity. Returns [(entity_id, rel_type, weight)]."""
        neighbors = self.adj.get(entity_id, [])
        if rel_type:
            return [(n, r, w) for n, r, w in neighbors if r == rel_type]
        return neighbors

    def get_entities_by_type(self, entity_type: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.type == entity_type]

    def get_entities_by_person(self, person: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.person.lower() == person.lower()]

    def get_entities_by_domain(self, domain: str) -> list[Entity]:
        return [
            e for e in self.entities.values() if domain.lower() in [d.lower() for d in e.domains]
        ]

    @property
    def stats(self) -> dict:
        type_counts = defaultdict(int)
        for e in self.entities.values():
            type_counts[e.type] += 1

        rel_counts = defaultdict(int)
        for edge in self.edges:
            rel_counts[edge.rel_type] += 1

        return {
            "total_entities": len(self.entities),
            "total_edges": len(self.edges),
            "entities_by_type": dict(type_counts),
            "edges_by_type": dict(rel_counts),
        }

    def get_communities(self, min_community_size: int = 3) -> list[dict]:
        """Return persisted communities when available (STORY-F1-7A), else recompute.

        ``self.communities is not None`` means the list was persisted by ``save()``
        / hydrated by ``load()`` — return it as-is. An empty list is an HONEST "no
        community >= min_community_size" (AC4), returned verbatim and NEVER recomputed
        away. ``None`` means a legacy graph saved before F1-7A carried no
        ``communities`` key — recompute on the fly (backward-compat, AC2). The
        recompute path uses the same algorithm and default ``min_community_size`` as
        ``save()``, so persisted and recomputed lists are identical (AC3).
        """
        if self.communities is not None:
            return self.communities
        return detect_communities(self, min_community_size=min_community_size)

    def save(self, filepath: Path | None = None) -> None:
        p = filepath or GRAPH_FILE
        p.parent.mkdir(parents=True, exist_ok=True)

        # STORY-F1-7A — persist the communities ``detect_communities`` already computes
        # instead of throwing them away (they were computed and discarded on every save,
        # forcing ``graph_query`` to recompute on every query). Recompute fresh here so
        # the persisted list is always current with the graph at save time (mitigates
        # stale communities); an empty graph yields ``[]`` (honest, AC4 — never a
        # fabricated community). Cache on the instance so an in-process query after a
        # save reads the persisted list rather than recomputing.
        self.communities = detect_communities(self)

        data = {
            "entities": {k: v.to_dict() for k, v in self.entities.items()},
            "edges": [e.to_dict() for e in self.edges],
            "stats": self.stats,
            "communities": self.communities,
        }

        payload = json.dumps(data, indent=2, ensure_ascii=False)
        with open(p, "w", encoding="utf-8") as f:
            f.write(payload)

        # STORY-RAG-VM-G2 — legacy alias: when the external graph is written, also
        # mirror it to ``graph.json`` for ONE release so read-only stats readers
        # that still hardcode ``graph.json`` (health_check, mcp_tools, log_generator)
        # keep returning external stats. Business/personal graphs do NOT touch the
        # alias (Art. XIII — the alias is external-only). Cheap (~2MB copy); removed
        # once those readers migrate to ``graph-external.json``.
        if p == GRAPH_FILE and p != LEGACY_GRAPH_FILE:
            with open(LEGACY_GRAPH_FILE, "w", encoding="utf-8") as f:
                f.write(payload)

    def load(self, filepath: Path | None = None) -> bool:
        p = filepath or GRAPH_FILE
        if not p.exists():
            return False

        with open(p, encoding="utf-8") as f:
            data = json.load(f)

        # Schema tolerance (STORY-RAG-VM-G1): the canonical on-disk schema is a
        # DICT ({id: entity}), written by ``save()``. A divergent writer
        # (``rag_integration.py::enrich_knowledge_graph``) historically wrote
        # ``entities`` as a LIST, which a dict-only loader could not read
        # (``AttributeError: 'list' object has no attribute 'items'``) — the
        # silent root cause of empty PPR / associative search. Accept both:
        # normalize a list into the canonical ``{id: entity}`` dict (key = the
        # entity's own ``id``), and warn so the legacy format never masks itself.
        raw_entities = data.get("entities", {})
        if isinstance(raw_entities, list):
            logger.warning(
                "graph load: entities veio como lista (schema legado) — "
                "normalizando para dict (%d entidades)",
                len(raw_entities),
            )
            raw_entities = {e["id"]: e for e in raw_entities}

        for eid, edata in raw_entities.items():
            self.entities[eid] = Entity(
                entity_id=edata["id"],
                entity_type=edata["type"],
                label=edata["label"],
                person=edata.get("person", ""),
                domains=edata.get("domains", []),
                layer=edata.get("layer", ""),
                weight=edata.get("weight", 1.0),
                # STORY-S3 provenance tags: read when present, fall back to the
                # None sentinel when absent (legacy nodes / DNA nodes omit them).
                source_type=edata.get("source_type"),
                quality_tier=edata.get("quality_tier"),
            )

        for edata in data.get("edges", []):
            edge = Edge(
                source=edata["source"],
                target=edata["target"],
                rel_type=edata["rel_type"],
                weight=edata.get("weight", 1.0),
                metadata=edata.get("metadata", {}),
                # Temporal + evidence (STORY-HGA-F1.1): read when present,
                # fall back to defaults (None sentinels) when absent.
                t_start=edata.get("t_start"),
                t_end=edata.get("t_end"),
                t_obs=edata.get("t_obs"),
                atomic_facts=edata.get("atomic_facts"),
            )
            self.edges.append(edge)
            self.adj[edge.source].append((edge.target, edge.rel_type, edge.weight))
            self.adj[edge.target].append((edge.source, edge.rel_type, edge.weight))

        # STORY-F1-7A — hydrate persisted communities. A graph saved by F1-7A+ carries
        # a ``communities`` list (possibly ``[]`` honest); a legacy graph saved before
        # F1-7A has no such key → ``None`` sentinel = "not persisted" → ``get_communities``
        # recomputes on demand (backward-compat, AC2 — legacy graphs still load).
        self.communities = data.get("communities")

        self.built = True
        return True


# ---------------------------------------------------------------------------
# GRAPH BUILDER
# ---------------------------------------------------------------------------
def build_graph(
    dna_dir: Path | None = None,
    *,
    bucket: str = "external",
    derivational: bool | None = None,
) -> KnowledgeGraph:
    """Build a knowledge graph for ONE bucket from its DNA YAML files.

    STORY-RAG-VM-G2 — multi-bucket isolation (Art. XIII). The builder now scopes to
    a single ``bucket`` (``external`` | ``business`` | ``personal``):

    - the DNA dir is derived as ``knowledge/{bucket}/dna/persons`` (override with an
      explicit ``dna_dir`` for tests);
    - the hyperedge overlay (meeting participants) replays ONLY for the business
      bucket — those participants live in the business bucket, so injecting them into
      the external graph was the leakage AC5 removes;
    - a deterministic stale-pruning pass runs at the end (see ``_prune_stale_persons``).

    Extracts: person / domain / DNA entries (5 layers) / cross-layer relationships /
    person-to-person relationships from CONFIG.yaml.

    A missing DNA dir (e.g. ``knowledge/personal/dna/persons`` does not exist yet) is
    a GRACEFUL no-op: an empty, built=True graph is returned and saved — never a crash
    (AC1 / Risk R6).

    ``derivational`` (STORY-213.W1.2) overrides the ``MB_DERIVATIONAL_EDGES_ENABLED``
    kill-switch: ``None`` → read the env var (default OFF); ``True``/``False`` →
    force. When enabled, the dormant DNA spine (GERA/PRODUZ/MATERIALIZA/IMPLEMENTA +
    PERTENCE_A via ``entity.domains``) is populated from REAL shared provenance; when
    disabled the build is byte-identical to pre-W1.2.
    """
    d = dna_dir or (BASE_DIR / "knowledge" / bucket / "dna" / "persons")
    graph = KnowledgeGraph()
    all_domains: set[str] = set()

    # STORY-213.W1.2 — derivational spine (default OFF; see ``derivational_edges_enabled``).
    # When OFF, EVERY line below behaves exactly as pre-W1.2 (byte-identical build).
    deriv_on = derivational_edges_enabled() if derivational is None else bool(derivational)
    # {person: {atom_type: [(entity_id, provenance_set), ...]}} — populated only when ON,
    # so the derivation runs on real per-person provenance after the full DNA build.
    atoms_prov: dict[str, dict[str, list[tuple[str, set[str]]]]] = {}

    if not d.exists():
        print(f"[GraphBuilder] DNA dir not found for bucket '{bucket}': {d} (no DNA)")
        # Graceful no-op for the DNA portion. STORY-S3: a bucket with no DNA dir can
        # STILL have non-DNA sources (business workspace + advisory-board exist even
        # with zero DNA persons; personal has dossiers without DNA). Founder decision:
        # include everything — so still ingest multi-source before returning. Gated to
        # the DEFAULT real-corpus path (``dna_dir`` not overridden) so a test that
        # passes an explicit non-existent ``dna_dir`` keeps a clean empty graph.
        if dna_dir is None:
            ms_counts = _ingest_multi_source(graph, bucket)
            if ms_counts:
                total = sum(ms_counts.values())
                print(
                    f"[GraphBuilder] S3 multi-source ({bucket}, no DNA): +{total} "
                    f"nodes from {len(ms_counts)} source(s): {ms_counts}"
                )
        graph.built = True
        return graph

    # Process each person
    for person_dir in sorted(d.iterdir()):
        if not person_dir.is_dir() or person_dir.name.startswith(("_", ".")):
            continue

        person = person_dir.name
        person_id = f"PESSOA:{person}"

        # Add person entity
        graph.add_entity(
            Entity(
                entity_id=person_id,
                entity_type="pessoa",
                label=person.replace("-", " ").title(),
                person=person,
            )
        )

        # Process CONFIG.yaml for person-to-person relationships
        config_path = person_dir / "CONFIG.yaml"
        if config_path.exists():
            _process_config(graph, config_path, person, person_id)

        # Process each DNA layer (5 classic layers)
        for filename, key in LAYER_KEYS.items():
            filepath = person_dir / filename
            if not filepath.exists():
                continue

            layer = key
            entries = _load_yaml_entries(filepath, key)

            for entry in entries:
                entry_id = entry.get("id", "")
                if not entry_id:
                    continue

                # Determine label
                label = (
                    entry.get("nome")
                    or entry.get("regra")
                    or entry.get("declaracao")
                    or entry.get("crenca")
                    or entry_id
                )
                if isinstance(label, str) and len(label) > 100:
                    label = label[:100] + "..."

                # STORY-213.W1.2 — when the spine is ON, widen the domain source to the
                # REAL fields the corpus actually populates (dominios + categoria + tags)
                # so PERTENCE_A fires from ``entity.domains`` (issue #141). NULL honesto:
                # an atom with none of those fields yields ``[]`` → no PERTENCE_A edge.
                # OFF = the original behavior (``dominios`` only), byte-identical.
                if deriv_on:
                    domains = _derivational.extract_domains(entry)
                else:
                    domains = entry.get("dominios", [])
                    if isinstance(domains, str):
                        domains = [domains]
                weight = entry.get("peso", 1.0)
                if not isinstance(weight, int | float):
                    weight = 1.0

                # Add entity
                entity_type = _layer_to_type(layer)
                graph.add_entity(
                    Entity(
                        entity_id=entry_id,
                        entity_type=entity_type,
                        label=label,
                        person=person,
                        domains=domains,
                        layer=layer,
                        weight=weight,
                    )
                )

                # Edge: Pessoa → Entry (TEM)
                graph.add_edge(Edge(person_id, entry_id, "TEM", weight=weight))

                # Edge: Entry → Domain (PERTENCE_A)
                for domain in domains:
                    domain_id = f"DOMINIO:{domain.lower()}"
                    if domain_id not in graph.entities:
                        graph.add_entity(
                            Entity(
                                entity_id=domain_id,
                                entity_type="dominio",
                                label=domain,
                            )
                        )
                    all_domains.add(domain.lower())
                    graph.add_edge(Edge(entry_id, domain_id, "PERTENCE_A"))

                # Cross-layer references
                _add_cross_layer_edges(graph, entry, entry_id, layer)

                # STORY-213.W1.2 — capture the atom's REAL provenance so the derivational
                # spine can be derived per-person after the full DNA build (No-Invention:
                # only real, specific, non-gap source units — see derivational_edges).
                if deriv_on:
                    atoms_prov.setdefault(person, {}).setdefault(entity_type, []).append(
                        (entry_id, _derivational.extract_provenance(entry))
                    )

        # Process MCE files (behavioral patterns, values, voice DNA)
        _process_mce_files(graph, person_dir, person, person_id)

    # Iron Law enforcement: guarantee bidirectional backlinks across the graph
    iron_law_report = graph.enforce_iron_law()
    if iron_law_report["backlinks_created"] > 0:
        print(
            f"[GraphBuilder] Iron Law: created {iron_law_report['backlinks_created']} "
            f"backlinks ({iron_law_report['total_edges_after']} total edges)"
        )

    # STORY-213.W1.2 — derive the derivational spine (GERA/PRODUZ/MATERIALIZA/IMPLEMENTA)
    # from shared SPECIFIC provenance between adjacent-layer atoms of the SAME person.
    # Added AFTER enforce_iron_law (like the directional CONTEM edges added by S3 below),
    # so a generative edge stays FORWARD-only (filosofia→modelo_mental) and respects the
    # schema domain/range — no reverse "modelo_mental GERA filosofia". ``add_edge`` still
    # makes ``adj`` bidirectional, so PPR/community reads are unaffected in direction.
    # Every edge carries its lastro in ``metadata.via`` (No-Invention — the audit trail).
    # NULL honesto: a verb with no real shared-provenance pair contributes 0 edges.
    if deriv_on:
        deriv_specs = _derivational.derive_edges(atoms_prov)
        for spec in deriv_specs:
            graph.add_edge(
                Edge(
                    spec["source"],
                    spec["target"],
                    spec["rel_type"],
                    metadata={"derivation": "shared_provenance", "via": spec["via"]},
                )
            )
        if deriv_specs:
            print(
                f"[GraphBuilder] W1.2 derivational spine ({bucket}): "
                f"+{len(deriv_specs)} edges {_derivational.count_by_verb(deriv_specs)}"
            )

    # Durability replay (STORY-HGA-F2.2 / constraint R1): re-apply materialized
    # hyperedges from the sidecar so they survive the per-bucket overwrite. MUST run
    # AFTER node construction (participants must exist for add_hyperedge's strict
    # consistency) and BEFORE built=True. No-op when overlay absent/empty.
    #
    # STORY-RAG-VM-G2 (AC5): the overlay carries MEETING participants, which belong to
    # the BUSINESS bucket. Replaying it into the external graph was the source of the
    # 18 phantom dotted-name nodes. Gate the replay to the business bucket so external
    # never gains them and business gets the legitimate meeting hyperedges.
    if bucket == "business":
        _replay_hyperedge_overlay(graph)

    # STORY-RAG-VM-G2 (AC4): deterministic stale prune. Runs AFTER overlay replay so a
    # node sustained by a LIVE hyperedge is never pruned; runs BEFORE built=True so the
    # persisted graph is already clean.
    #
    # STORY-S3: the prune sees ONLY the finalized DNA subgraph here — multi-source
    # ingestion runs AFTER it, so the prune's double-negative criterion never touches
    # a (non-pessoa) document/workspace node, and a volatile workspace node can never
    # be mistaken for a stale person (it isn't even built yet).
    _prune_stale_persons(graph, d)

    # STORY-S3 (completude-total) — AC1: ingest ALL non-DNA sources for this bucket
    # (dossiers, playbooks, sources, inbox, advisory-board, the-machine, insights,
    # personal, AND workspace L0-L4). Founder decision (locked 2026-06-30): include
    # everything, control noise by TAG not omission. Runs LAST so it is purely
    # additive in a component DISJOINT from the finalized DNA subgraph — PPR over DNA
    # seeds is provably unmoved (AC4/RNF-1). Art. XIII: only this bucket's own dirs.
    #
    # Gated to the DEFAULT real-corpus path (``dna_dir is None``): a caller that pins
    # an explicit ``dna_dir`` (tests, narrow DNA-only rebuilds) gets a PURE DNA graph,
    # which keeps the multi-source pass from coupling to an unrelated DNA fixture and
    # makes the AC4 characterization (DNA-only vs full) a clean A/B.
    if dna_dir is None:
        ms_counts = _ingest_multi_source(graph, bucket)
        if ms_counts:
            total = sum(ms_counts.values())
            # ``stats`` is a computed property — the new ``documento``/``workspace_doc``/
            # ``fonte`` types already surface in ``entities_by_type``. Just log the
            # per-source breakdown for the rebuild observability trail.
            print(
                f"[GraphBuilder] S3 multi-source ({bucket}): +{total} nodes "
                f"from {len(ms_counts)} source(s): {ms_counts}"
            )

    graph.built = True
    return graph


def _prune_stale_persons(graph: KnowledgeGraph, dna_dir: Path) -> int:
    """Remove stale ``pessoa`` nodes — the double-negative criterion (AC4).

    A ``pessoa`` node is pruned **only if BOTH** hold:

      1. it has NO DNA dir on disk under this bucket (``dna_dir/{person}`` absent), AND
      2. it has NO active edge sustaining it (no entry in ``graph.adj`` after this
         build — i.e. no ``TEM``/``PARTICIPA``/etc. touches it).

    This is the safety net the story demands: NEVER a blind "person without DNA"
    deletion (that would kill a legitimate meeting participant, Risk R3). A meeting
    participant lives WITHOUT a DNA dir but WITH a live ``PARTICIPA`` edge from the
    overlay replay → condition (2) is false → it survives. A residual phantom (DNA dir
    gone AND no live edge) → both true → pruned.

    For the external bucket the overlay no longer replays, so any leftover dotted-name
    participant is now edge-less and gets pruned here as defense-in-depth.

    Deterministic: iterates a sorted snapshot, mutates ``entities`` only. Returns the
    number pruned.
    """
    to_prune: list[str] = []
    for eid in sorted(graph.entities):
        ent = graph.entities[eid]
        if ent.type != "pessoa":
            continue
        person = ent.person or (eid.split(":", 1)[1] if ":" in eid else eid)
        has_dna = (dna_dir / person).is_dir()
        has_live_edge = bool(graph.adj.get(eid))
        # Double-negative: prune ONLY when there is neither DNA nor a live edge.
        if not has_dna and not has_live_edge:
            to_prune.append(eid)

    for eid in to_prune:
        graph.entities.pop(eid, None)

    if to_prune:
        print(f"[GraphBuilder] pruned {len(to_prune)} stale pessoa node(s): {to_prune}")
    return len(to_prune)


def _replay_hyperedge_overlay(
    graph: KnowledgeGraph, overlay_path: Path | None = None
) -> int:
    """Re-apply materialized hyperedges from the durable sidecar (STORY-HGA-F2.2).

    rebuild.py:97-98 (`build_graph(); save()`) rebuilds graph.json from the DNA
    YAMLs on every cmd_finalize, which would erase any hyperedge written straight
    into graph.json. So materialized hyperedges live in ``he-overlay.json`` and are
    re-derived here on every rebuild — the same re-derivation discipline as
    Hyper-Extract's export (``hypergraph.py`` @ 4e333f847f1d).

    Each entry is replayed via ``add_hyperedge`` (idempotent on the sorted-set H id),
    re-using the proven F2.1 primitive — NO star-expansion is reimplemented here.

    The overlay is SELF-CONTAINED: ``build_graph`` only constructs nodes from the
    external DNA dir, but a meeting's participants live in the *business* bucket and
    are NOT in that dir. So before invoking ``add_hyperedge`` (which raises on a
    missing participant — RNF-G2), we idempotently upsert each participant as a
    ``pessoa`` node from the entry's own ``participant_labels``. This is what makes
    the hyperedge SURVIVE rebuild.py:97-98: the overlay carries everything needed to
    re-derive both the participant nodes and the hyperedge.

    Overlay absent / empty / unreadable → no-op (0), so a graph with no materialized
    hyperedges loads byte-identical to the legacy format.

    Returns the number of hyperedges replayed.
    """
    p = overlay_path or OVERLAY_FILE
    if not p.exists():
        return 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0

    entries = data.get("hyperedges", []) if isinstance(data, dict) else []
    if not isinstance(entries, list):
        return 0

    replayed = 0
    for entry in entries:
        try:
            participants = entry["participants"]
            rel_label = entry["rel_label"]
        except (KeyError, TypeError):
            continue
        # Self-contained durability: upsert each participant as a pessoa node from the
        # overlay's own labels (business participants aren't in the DNA dir). Idempotent
        # — never overwrites a node the DNA build already produced.
        labels = entry.get("participant_labels", {})
        for member in participants:
            if member not in graph.entities:
                slug = member.split(":", 1)[1] if ":" in member else member
                graph.add_entity(
                    Entity(
                        entity_id=member,
                        entity_type="pessoa",
                        label=labels.get(member, slug),
                        person=slug,
                    )
                )
        graph.add_hyperedge(
            participants=participants,
            rel_label=rel_label,
            rel_type=entry.get("rel_type", "PARTICIPA"),
            t_start=entry.get("t_start") or None,
            atomic_facts=entry.get("atomic_facts") or None,
            metadata=entry.get("metadata") or None,
        )
        replayed += 1
    return replayed


def _load_yaml_entries(filepath: Path, expected_key: str) -> list[dict]:
    """Load entries from a DNA YAML file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return []

    if isinstance(data, dict):
        # Try expected key
        entries = data.get(expected_key)
        if isinstance(entries, list):
            return entries
        # Try any list value
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    elif isinstance(data, list):
        return data

    return []


# ---------------------------------------------------------------------------
# STORY-S3 (completude-total): MULTI-SOURCE NODE ADAPTERS
# ---------------------------------------------------------------------------
# Honest extraction (No Invention / extraction-no-fallbacks.md): pull the REAL
# identity of each file (frontmatter slug/title, first Markdown ``# H1``). When a
# field is absent it stays ``None`` — a real extraction gap — never a fabricated
# default. The node is still created from what DOES exist (the path/stem is always
# real). PDFs/binaries become FILENAME-only document nodes (body unread, no fake
# content).


def _read_frontmatter(filepath: Path) -> dict:
    """Parse a leading ``---`` YAML frontmatter block. Empty dict when absent/invalid.

    Honest: returns only what the file actually declares. No defaults injected.
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            head = f.read(8192)
    except OSError:
        return {}
    if not head.startswith("---"):
        return {}
    end = head.find("\n---", 3)
    if end == -1:
        return {}
    block = head[3:end]
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _first_markdown_h1(filepath: Path) -> str | None:
    """Return the first ``# Heading`` text, or ``None`` (extraction gap) if none."""
    if filepath.suffix.lower() not in _TEXT_SUFFIXES:
        return None
    try:
        with open(filepath, encoding="utf-8") as f:
            for _ in range(200):  # bounded scan — honest, cheap
                line = f.readline()
                if not line:
                    break
                s = line.strip()
                if s.startswith("# "):
                    return s[2:].strip() or None
    except OSError:
        return None
    return None


def _extract_document_node(
    filepath: Path, root: Path, *, source_type: str, quality_tier: str
) -> tuple[str, str, str | None, dict] | None:
    """Build (entity_id, label, person, metadata) for ONE source file. Honest.

    Identity precedence (all REAL signals, never fabricated):
      id     = frontmatter ``id``/``slug`` → else ``DOC:{source_type}:{relpath}``
      label  = frontmatter ``title``/``nome`` → first ``# H1`` → else the file stem
      person = frontmatter ``pessoa_id``/``author``/``owner`` → else None (gap)
    ``metadata`` records the relpath + which fields were extracted vs. gapped, so a
    consumer can see provenance + honesty at a glance. Returns ``None`` to skip a
    file that is not an ingestable document (e.g. an index sidecar we choose to skip).
    """
    suffix = filepath.suffix.lower()
    if suffix not in _DOC_SUFFIXES:
        return None  # unknown binary type — skip, never fabricate a node
    try:
        relpath = filepath.relative_to(root).as_posix()
    except ValueError:
        relpath = filepath.name

    fm = _read_frontmatter(filepath) if suffix in _TEXT_SUFFIXES else {}

    raw_id = fm.get("id") or fm.get("slug")
    entity_id = (
        f"DOC:{source_type}:{raw_id}" if raw_id else f"DOC:{source_type}:{relpath}"
    )
    label = (
        fm.get("title")
        or fm.get("nome")
        or _first_markdown_h1(filepath)
        or filepath.stem
    )
    if isinstance(label, str) and len(label) > 100:
        label = label[:100] + "..."
    person = fm.get("pessoa_id") or fm.get("author") or fm.get("owner") or None

    metadata: dict = {"relpath": relpath}
    gaps = []
    if not raw_id:
        gaps.append("id")  # extraction_gap — id derived from path, not declared
    if person is None:
        gaps.append("person")  # extraction_gap — no author declared
    if gaps:
        metadata["extraction_gaps"] = gaps
    return entity_id, label, person, metadata


def _iter_source_files(base: Path) -> list[Path]:
    """Deterministic sorted walk of ingestable files under ``base`` (AC6).

    Skips dotfiles (``.DS_Store``, ``.gitkeep``) and ``_``-prefixed index sidecars
    (``_INDEX.md``) — those are scaffolding, not knowledge documents.
    """
    if not base.exists():
        return []
    out: list[Path] = []
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        name = p.name
        if name.startswith((".", "_")):
            continue
        if p.suffix.lower() not in _DOC_SUFFIXES:
            continue
        out.append(p)
    return out


def _ingest_source_dir(
    graph: KnowledgeGraph,
    base: Path,
    *,
    source_type: str,
    quality_tier: str,
) -> int:
    """Ingest every document under ``base`` as a tagged node in its OWN component.

    Each node hangs off a synthetic ``FONTE:{source_type}`` anchor (CONTEM edge) —
    NEVER linked to a DNA-built node — so PPR over DNA seeds is untouched (AC4).
    Returns the number of document nodes added. Idempotent on re-run (AC6): same
    files → same ids → same graph (``add_entity`` overwrites by id; sorted walk).
    """
    files = _iter_source_files(base)
    if not files:
        return 0

    anchor_id = f"FONTE:{source_type}"
    if anchor_id not in graph.entities:
        graph.add_entity(
            Entity(
                entity_id=anchor_id,
                entity_type="fonte",
                label=source_type.replace("-", " ").title(),
                source_type=source_type,
                quality_tier=quality_tier,
            )
        )

    added = 0
    for fp in files:
        node = _extract_document_node(
            fp, base, source_type=source_type, quality_tier=quality_tier
        )
        if node is None:
            continue
        entity_id, label, person, metadata = node
        graph.add_entity(
            Entity(
                entity_id=entity_id,
                entity_type="documento",
                label=label,
                person=person or "",
                source_type=source_type,
                quality_tier=quality_tier,
                metadata=metadata,
            )
        )
        graph.add_edge(Edge(anchor_id, entity_id, "CONTEM"))
        added += 1
    return added


def _ingest_workspace(graph: KnowledgeGraph, bucket: str) -> int:
    """Ingest workspace L0-L4 docs (Art. XIV) — BUSINESS bucket only (Art. XIII).

    Workspace is per-BU business data, so it routes EXCLUSIVELY to the business
    graph. Each doc node carries its TTL layer + a ``volatile`` flag (L3/L4 churn)
    so the prune pass and S4 can treat volatility explicitly WITHOUT excluding it.
    Nodes hang off ``FONTE:workspace`` — disjoint from DNA (AC4). Returns count.
    """
    if bucket != WORKSPACE_BUCKET:
        return 0
    ws_root = BASE_DIR / "workspace" / "businesses"
    if not ws_root.exists():
        return 0

    anchor_id = "FONTE:workspace"
    if anchor_id not in graph.entities:
        graph.add_entity(
            Entity(
                entity_id=anchor_id,
                entity_type="fonte",
                label="Workspace",
                source_type="workspace",
                quality_tier="structured",
            )
        )

    added = 0
    for bu_dir in sorted(ws_root.iterdir()):
        if not bu_dir.is_dir() or bu_dir.name.startswith((".", "_")):
            continue
        bu = bu_dir.name
        for fp in _iter_source_files(bu_dir):
            try:
                relpath = fp.relative_to(ws_root).as_posix()
            except ValueError:
                relpath = fp.name
            # Layer = first path segment matching an L0-L4 dir (honest; None if none).
            layer = None
            for part in fp.relative_to(bu_dir).parts:
                if part in WORKSPACE_LAYER_TTL_DAYS:
                    layer = part
                    break
            ttl = WORKSPACE_LAYER_TTL_DAYS.get(layer) if layer else None
            volatile = ttl is not None and ttl <= WORKSPACE_VOLATILE_TTL_THRESHOLD_DAYS

            fm = _read_frontmatter(fp) if fp.suffix.lower() in _TEXT_SUFFIXES else {}
            label = fm.get("title") or fm.get("nome") or _first_markdown_h1(fp) or fp.stem
            if isinstance(label, str) and len(label) > 100:
                label = label[:100] + "..."

            metadata: dict = {"relpath": relpath, "bu": bu, "volatile": volatile}
            if layer:
                metadata["ttl_layer"] = layer
                metadata["ttl_days"] = ttl
            else:
                metadata["extraction_gaps"] = ["ttl_layer"]  # not under an L0-L4 dir

            entity_id = f"DOC:workspace:{relpath}"
            graph.add_entity(
                Entity(
                    entity_id=entity_id,
                    entity_type="workspace_doc",
                    label=label,
                    source_type="workspace",
                    # Volatile docs are tagged ``raw`` (filterable churn); durable
                    # L0-L2 docs are ``structured``. Never excluded — only tagged.
                    quality_tier="raw" if volatile else "structured",
                    metadata=metadata,
                )
            )
            graph.add_edge(Edge(anchor_id, entity_id, "CONTEM"))
            added += 1
    return added


def _ingest_multi_source(graph: KnowledgeGraph, bucket: str) -> dict[str, int]:
    """STORY-S3 entrypoint: ingest ALL non-DNA sources for ``bucket`` (AC1).

    Runs AFTER the DNA build + iron-law + overlay + prune are final, so every node
    it adds is purely additive in a component disjoint from the finalized DNA
    subgraph. Deterministic (sorted routing + sorted walk → AC6). Art. XIII: only
    this bucket's own dirs + (for business) workspace are read. Returns per-source
    counts for the rebuild stats / log.
    """
    counts: dict[str, int] = {}
    for entry in SOURCE_ROUTING.get(bucket, []):
        base = BASE_DIR / "knowledge" / bucket / entry["dir"]
        n = _ingest_source_dir(
            graph,
            base,
            source_type=entry["source_type"],
            quality_tier=entry["quality_tier"],
        )
        if n:
            counts[f"{bucket}/{entry['dir']}"] = n
    ws = _ingest_workspace(graph, bucket)
    if ws:
        counts["workspace"] = ws
    return counts


def _layer_to_type(layer: str) -> str:
    """Map layer key to entity type."""
    mapping = {
        "filosofias": "filosofia",
        "modelos_mentais": "modelo_mental",
        "heuristicas": "heuristica",
        "frameworks": "framework",
        "metodologias": "metodologia",
    }
    return mapping.get(layer, layer)


def _add_cross_layer_edges(graph: KnowledgeGraph, entry: dict, entry_id: str, layer: str) -> None:
    """Add cross-layer relationship edges.

    Supports both OLD format (relacionado_a: list) and
    NEW format (filosofia_relacionada: string).
    """
    # filosofia_relacionada (string format)
    fil_ref = entry.get("filosofia_relacionada")
    if fil_ref and isinstance(fil_ref, str) and fil_ref.startswith("FIL-"):
        graph.add_edge(Edge(entry_id, fil_ref, "RELACIONADA_COM"))

    # modelo_mental_relacionado (string format)
    mm_ref = entry.get("modelo_mental_relacionado")
    if mm_ref and isinstance(mm_ref, str) and mm_ref.startswith("MM-"):
        graph.add_edge(Edge(entry_id, mm_ref, "RELACIONADA_COM"))

    # relacionado_a (list format — OLD repo compatibility)
    rel_list = entry.get("relacionado_a", [])
    if isinstance(rel_list, str):
        rel_list = [rel_list]
    if isinstance(rel_list, list):
        for ref in rel_list:
            if isinstance(ref, str) and ref.startswith(("FIL-", "MM-", "HEUR-", "FW-", "MET-")):
                graph.add_edge(Edge(entry_id, ref, "RELACIONADA_COM"))

    # Ontology hierarchy edges (layer → layer above)
    # Filosofia → ModeloMental → Heuristica → Framework → Metodologia
    hierarchy = {
        "modelos_mentais": ("GERA", "filosofia_relacionada"),
        "heuristicas": ("PRODUZ", "modelo_mental_relacionado"),
        "frameworks": ("MATERIALIZA", None),
        "metodologias": ("IMPLEMENTA", None),
    }

    if layer in hierarchy:
        rel_type, ref_field = hierarchy[layer]
        if ref_field:
            # Try new format first, then old format
            ref = entry.get(ref_field)
            if not ref:
                refs = entry.get("relacionado_a", [])
                if isinstance(refs, list) and refs:
                    ref = refs[0]  # Use first related item for hierarchy
            if ref and isinstance(ref, str):
                graph.add_edge(Edge(ref, entry_id, rel_type))


def _process_config(graph: KnowledgeGraph, config_path: Path, person: str, person_id: str) -> None:
    """Process CONFIG.yaml for person-to-person relationships."""
    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return

    if not isinstance(config, dict):
        return

    conexoes = config.get("conexoes", {})
    if not isinstance(conexoes, dict):
        return

    for rel_key, rel_type in [
        ("complementa", "COMPLEMENTA"),
        ("tensiona", "TENSIONA"),
        ("alinha", "ALINHA"),
    ]:
        items = conexoes.get(rel_key, [])
        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue
            other_person = item.get("pessoa", "")
            if not other_person:
                continue
            other_id = f"PESSOA:{other_person.lower().replace(' ', '-')}"
            note = item.get("nota", "")
            graph.add_edge(
                Edge(
                    person_id,
                    other_id,
                    rel_type,
                    metadata={"em": item.get("em", ""), "nota": note},
                )
            )

    # Agent consumption relationships
    rastreabilidade = config.get("rastreabilidade", {})
    agents = rastreabilidade.get("agentes_que_consomem", [])
    if isinstance(agents, list):
        for agent in agents:
            if not isinstance(agent, dict):
                continue
            agent_path = agent.get("path", "")
            peso = agent.get("peso", 0.5)
            if agent_path:
                agent_id = f"AGENTE:{agent_path.rstrip('/').split('/')[-1]}"
                if agent_id not in graph.entities:
                    graph.add_entity(
                        Entity(
                            entity_id=agent_id,
                            entity_type="agente",
                            label=agent_path.rstrip("/").split("/")[-1].upper(),
                        )
                    )
                graph.add_edge(Edge(agent_id, person_id, "CONSOME", weight=peso))


# ---------------------------------------------------------------------------
# MCE (Mind-Clone Enhancement) PROCESSING
# ---------------------------------------------------------------------------
def _process_mce_files(
    graph: KnowledgeGraph, person_dir: Path, person: str, person_id: str
) -> None:
    """Process MCE YAML files for a person (behavioral patterns, values, obsessions, paradoxes, voice).

    Gracefully skips if files don't exist (backward compatible).
    L9 (obsessions) and L10 (paradoxes) are processed from standalone files first,
    with fallback to VALUES-HIERARCHY.yaml for backward compatibility.
    """
    _process_behavioral_patterns(graph, person_dir, person, person_id)
    _process_values_hierarchy(graph, person_dir, person, person_id)
    _process_obsessions(graph, person_dir, person, person_id)
    _process_paradoxes(graph, person_dir, person, person_id)
    _process_voice_dna(graph, person_dir, person, person_id)


def _process_behavioral_patterns(
    graph: KnowledgeGraph, person_dir: Path, person: str, person_id: str
) -> None:
    """Process BEHAVIORAL-PATTERNS.yaml → behavioral_pattern entities."""
    filepath = person_dir / "BEHAVIORAL-PATTERNS.yaml"
    if not filepath.exists():
        return

    data = _safe_load_yaml(filepath)
    if not data:
        return

    entries = _extract_list(data, "behavioral_patterns", "patterns", "behaviors")
    for entry in entries:
        entry_id = entry.get("id", "")
        if not entry_id:
            entry_id = _generate_mce_id("BP", person, entry)
            if not entry_id:
                continue

        # STORY-RAG-VM-G2: ``description`` may be null or a non-string in DNA — only
        # slice a real string, else fall through (``None[:100]`` / ``dict[:100]`` raised).
        _desc = entry.get("description")
        _desc_label = _desc[:100] if isinstance(_desc, str) else ""
        label = (
            entry.get("nome")
            or entry.get("name")
            or entry.get("pattern")
            or _desc_label
            or entry_id
        )
        if isinstance(label, str) and len(label) > 100:
            label = label[:100] + "..."

        domains = _extract_domains(entry)
        weight = _extract_weight(entry)

        graph.add_entity(
            Entity(
                entity_id=entry_id,
                entity_type="behavioral_pattern",
                label=label,
                person=person,
                domains=domains,
                layer="behavioral_patterns",
                weight=weight,
            )
        )

        graph.add_edge(Edge(person_id, entry_id, "MANIFESTA", weight=weight))

        for domain in domains:
            _ensure_domain_entity(graph, domain)
            graph.add_edge(Edge(entry_id, f"DOMINIO:{domain.lower()}", "PERTENCE_A"))

        _add_mce_cross_refs(graph, entry, entry_id)


def _process_values_hierarchy(
    graph: KnowledgeGraph, person_dir: Path, person: str, person_id: str
) -> None:
    """Process VALUES-HIERARCHY.yaml → value entities ONLY.

    NOTE: Obsessions and paradoxes were historically extracted from this file.
    As of L9/L10 promotion, they are now processed by dedicated functions:
    - _process_obsessions() reads from OBSESSIONS.yaml (L9) with VH fallback
    - _process_paradoxes() reads from PARADOXES.yaml (L10) with VH fallback
    """
    filepath = person_dir / "VALUES-HIERARCHY.yaml"
    if not filepath.exists():
        return

    data = _safe_load_yaml(filepath)
    if not data:
        return

    # Process values (only values -- obsessions/paradoxes delegated to dedicated functions)
    values = _extract_list(data, "values", "valores", "hierarchy")
    for entry in values:
        entry_id = entry.get("id", "")
        if not entry_id:
            entry_id = _generate_mce_id("VAL", person, entry)
            if not entry_id:
                continue

        label = entry.get("nome") or entry.get("name") or entry.get("value") or entry_id
        if isinstance(label, str) and len(label) > 100:
            label = label[:100] + "..."

        rank = entry.get("rank", entry.get("score", entry.get("peso", 1.0)))
        if not isinstance(rank, int | float):
            rank = 1.0

        domains = _extract_domains(entry)

        graph.add_entity(
            Entity(
                entity_id=entry_id,
                entity_type="value",
                label=label,
                person=person,
                domains=domains,
                layer="values",
                weight=rank,
            )
        )

        graph.add_edge(Edge(person_id, entry_id, "PRIORIZA", weight=rank))

        for domain in domains:
            _ensure_domain_entity(graph, domain)
            graph.add_edge(Edge(entry_id, f"DOMINIO:{domain.lower()}", "PERTENCE_A"))

        _add_mce_cross_refs(graph, entry, entry_id)


def _process_obsessions(
    graph: KnowledgeGraph, person_dir: Path, person: str, person_id: str
) -> None:
    """Process obsessions → obsession entities.

    Fallback chain (first source with data wins):
    1. OBSESSIONS.yaml (L9 standalone -- canonical source)
    2. VALUES-HIERARCHY.yaml "obsessions" field (legacy location)
    3. VOICE-DNA.yaml "obsessions" field (legacy location)
    """
    entries: list[dict] = []

    # 1. Try standalone OBSESSIONS.yaml (canonical L9)
    standalone = person_dir / "OBSESSIONS.yaml"
    if standalone.exists():
        data = _safe_load_yaml(standalone)
        if data:
            entries = _extract_list(data, "obsessions", "obsessoes")

    # 2. Fallback: VALUES-HIERARCHY.yaml
    if not entries:
        vh_path = person_dir / "VALUES-HIERARCHY.yaml"
        if vh_path.exists():
            vh_data = _safe_load_yaml(vh_path)
            if vh_data:
                entries = _extract_list(vh_data, "obsessions", "obsessoes")

    # 3. Fallback: VOICE-DNA.yaml
    if not entries:
        vd_path = person_dir / "VOICE-DNA.yaml"
        if vd_path.exists():
            vd_data = _safe_load_yaml(vd_path)
            if vd_data:
                entries = _extract_list(vd_data, "obsessions", "obsessoes")

    for entry in entries:
        entry_id = entry.get("id", "")
        if not entry_id:
            entry_id = _generate_mce_id("OBS", person, entry)
            if not entry_id:
                continue

        label = entry.get("nome") or entry.get("name") or entry.get("obsession") or entry_id
        if isinstance(label, str) and len(label) > 100:
            label = label[:100] + "..."

        domains = _extract_domains(entry)
        weight = _extract_weight(entry)

        graph.add_entity(
            Entity(
                entity_id=entry_id,
                entity_type="obsession",
                label=label,
                person=person,
                domains=domains,
                layer="obsessions",
                weight=weight,
            )
        )

        graph.add_edge(Edge(person_id, entry_id, "OBSECADO_COM", weight=weight))

        for domain in domains:
            _ensure_domain_entity(graph, domain)
            graph.add_edge(Edge(entry_id, f"DOMINIO:{domain.lower()}", "PERTENCE_A"))

        _add_mce_cross_refs(graph, entry, entry_id)


def _process_paradoxes(
    graph: KnowledgeGraph, person_dir: Path, person: str, person_id: str
) -> None:
    """Process paradoxes → paradox entities.

    Fallback chain (first source with data wins):
    1. PARADOXES.yaml (L10 standalone -- canonical source)
    2. VALUES-HIERARCHY.yaml "paradoxes" field (legacy location)
    3. VOICE-DNA.yaml "paradoxes" field (legacy location)
    """
    entries: list[dict] = []

    # 1. Try standalone PARADOXES.yaml (canonical L10)
    standalone = person_dir / "PARADOXES.yaml"
    if standalone.exists():
        data = _safe_load_yaml(standalone)
        if data:
            entries = _extract_list(data, "paradoxes", "paradoxos")

    # 2. Fallback: VALUES-HIERARCHY.yaml
    if not entries:
        vh_path = person_dir / "VALUES-HIERARCHY.yaml"
        if vh_path.exists():
            vh_data = _safe_load_yaml(vh_path)
            if vh_data:
                entries = _extract_list(vh_data, "paradoxes", "paradoxos")

    # 3. Fallback: VOICE-DNA.yaml
    if not entries:
        vd_path = person_dir / "VOICE-DNA.yaml"
        if vd_path.exists():
            vd_data = _safe_load_yaml(vd_path)
            if vd_data:
                entries = _extract_list(vd_data, "paradoxes", "paradoxos")

    for entry in entries:
        entry_id = entry.get("id", "")
        if not entry_id:
            entry_id = _generate_mce_id("PAR", person, entry)
            if not entry_id:
                continue

        # STORY-RAG-VM-G2: ``tension`` may be a STRING (legacy) or a structured DICT
        # ({side_a, side_b}) — business DNA uses the dict shape. ``dict[:100]`` raised.
        # Only slice when it is actually a string; otherwise fall through to entry_id.
        _tension = entry.get("tension")
        _tension_label = _tension[:100] if isinstance(_tension, str) else ""
        label = (
            entry.get("nome")
            or entry.get("name")
            or entry.get("paradox")
            or _tension_label
            or entry_id
        )
        if isinstance(label, str) and len(label) > 100:
            label = label[:100] + "..."

        domains = _extract_domains(entry)
        weight = _extract_weight(entry)

        graph.add_entity(
            Entity(
                entity_id=entry_id,
                entity_type="paradox",
                label=label,
                person=person,
                domains=domains,
                layer="paradoxes",
                weight=weight,
            )
        )

        graph.add_edge(Edge(person_id, entry_id, "TENSIONA_PARADOXO", weight=weight))

        # Paradox-to-paradox tension (if counterpart specified)
        counterpart = entry.get("counterpart", entry.get("tensiona"))
        if counterpart and isinstance(counterpart, str):
            graph.add_edge(Edge(entry_id, counterpart, "TENSIONA_PARADOXO"))

        for domain in domains:
            _ensure_domain_entity(graph, domain)
            graph.add_edge(Edge(entry_id, f"DOMINIO:{domain.lower()}", "PERTENCE_A"))

        _add_mce_cross_refs(graph, entry, entry_id)


def _process_voice_dna(
    graph: KnowledgeGraph, person_dir: Path, person: str, person_id: str
) -> None:
    """Process VOICE-DNA.yaml → voice_trait entities."""
    filepath = person_dir / "VOICE-DNA.yaml"
    if not filepath.exists():
        return

    data = _safe_load_yaml(filepath)
    if not data:
        return

    # Collect voice traits from multiple possible sections
    all_traits: list[dict] = []
    for key in (
        "signature_phrases",
        "metaphors",
        "catchphrases",
        "verbal_patterns",
        "frases_signature",
        "metaforas",
    ):
        section = data.get(key)
        if isinstance(section, list):
            for item in section:
                if isinstance(item, dict):
                    if "source_section" not in item:
                        item["source_section"] = key
                    all_traits.append(item)
                elif isinstance(item, str):
                    all_traits.append(
                        {
                            "phrase": item,
                            "source_section": key,
                        }
                    )

    counter = 0
    for entry in all_traits:
        entry_id = entry.get("id", "")
        if not entry_id:
            counter += 1
            abbrev = person[:2].upper()
            entry_id = f"VT-{abbrev}-{counter:03d}"

        label = (
            entry.get("phrase")
            or entry.get("nome")
            or entry.get("name")
            or entry.get("metaphor")
            or entry.get("text")
            or entry_id
        )
        if isinstance(label, str) and len(label) > 100:
            label = label[:100] + "..."

        weight = _extract_weight(entry)

        graph.add_entity(
            Entity(
                entity_id=entry_id,
                entity_type="voice_trait",
                label=label,
                person=person,
                layer="voice_dna",
                weight=weight,
                metadata={"section": entry.get("source_section", "")},
            )
        )

        graph.add_edge(Edge(person_id, entry_id, "EXPRESSA", weight=weight))

        _add_mce_cross_refs(graph, entry, entry_id)


# ---------------------------------------------------------------------------
# MCE HELPERS
# ---------------------------------------------------------------------------
def _safe_load_yaml(filepath: Path) -> dict | None:
    """Safely load a YAML file, returning None on failure."""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return None

    if isinstance(data, dict):
        return data
    return None


def _extract_list(data: dict, *keys: str) -> list[dict]:
    """Extract a list of dicts from data, trying multiple key names."""
    for key in keys:
        section = data.get(key)
        if isinstance(section, list):
            return [e for e in section if isinstance(e, dict)]
    return []


def _extract_domains(entry: dict) -> list[str]:
    """Extract domain list from an entry."""
    domains = entry.get("dominios", entry.get("domains", []))
    if isinstance(domains, str):
        return [domains]
    if isinstance(domains, list):
        return domains
    return []


def _extract_weight(entry: dict) -> float:
    """Extract numeric weight from an entry."""
    weight = entry.get("peso", entry.get("weight", entry.get("score", 1.0)))
    if not isinstance(weight, int | float):
        return 1.0
    return float(weight)


def _generate_mce_id(prefix: str, person: str, entry: dict) -> str:
    """Generate an ID for an MCE entry that lacks one."""
    label = (
        entry.get("nome")
        or entry.get("name")
        or entry.get("pattern")
        or entry.get("value")
        or entry.get("phrase")
        or ""
    )
    if not label:
        return ""
    abbrev = person[:2].upper()
    slug = label[:30].lower().replace(" ", "-").replace("/", "-")
    # Remove non-alphanumeric chars except hyphens
    slug = "".join(c for c in slug if c.isalnum() or c == "-").strip("-")
    return f"{prefix}-{abbrev}-{slug}"


def _ensure_domain_entity(graph: KnowledgeGraph, domain: str) -> None:
    """Ensure a domain entity exists in the graph."""
    domain_id = f"DOMINIO:{domain.lower()}"
    if domain_id not in graph.entities:
        graph.add_entity(
            Entity(
                entity_id=domain_id,
                entity_type="dominio",
                label=domain,
            )
        )


def _add_mce_cross_refs(graph: KnowledgeGraph, entry: dict, entry_id: str) -> None:
    """Add cross-reference edges from MCE entries to DNA entries."""
    # Direct references via related_to / relacionado_a
    rel_list = entry.get("relacionado_a", entry.get("related_to", []))
    if isinstance(rel_list, str):
        rel_list = [rel_list]
    if isinstance(rel_list, list):
        for ref in rel_list:
            if isinstance(ref, str) and ref.startswith(
                ("FIL-", "MM-", "HEUR-", "FW-", "MET-", "BP-", "VAL-", "OBS-", "PAR-", "VT-"),
            ):
                graph.add_edge(Edge(entry_id, ref, "RELACIONADA_COM"))


# ---------------------------------------------------------------------------
# COMMUNITY DETECTION (LazyGraphRAG-style)
# ---------------------------------------------------------------------------
def detect_communities(graph: KnowledgeGraph, min_community_size: int = 3) -> list[dict]:
    """Simple community detection via connected components on domain subgraphs.

    Returns list of communities: [{
        "id": str,
        "domain": str,
        "entities": [entity_id, ...],
        "persons": [person, ...],
        "size": int,
    }]
    """
    communities = []

    # Group entities by domain
    domain_entities: dict[str, set[str]] = defaultdict(set)
    for entity in graph.entities.values():
        for domain in entity.domains:
            domain_entities[domain.lower()].add(entity.id)

    for domain, entity_ids in domain_entities.items():
        if len(entity_ids) < min_community_size:
            continue

        persons = set()
        for eid in entity_ids:
            entity = graph.get_entity(eid)
            if entity and entity.person:
                persons.add(entity.person)

        communities.append(
            {
                "id": f"COMM:{domain}",
                "domain": domain,
                "entities": sorted(entity_ids),
                "persons": sorted(persons),
                "size": len(entity_ids),
            }
        )

    return sorted(communities, key=lambda c: -c["size"])


# ---------------------------------------------------------------------------
# SINGLETON
# ---------------------------------------------------------------------------
_graph: KnowledgeGraph | None = None


def get_graph() -> KnowledgeGraph:
    """Get or create the knowledge graph singleton (EXTERNAL bucket).

    Unchanged contract: the process-wide singleton is the EXTERNAL graph (loads
    ``graph-external.json``, or builds+saves it on a cold cache). Every existing
    consumer that calls ``get_graph()`` keeps getting external — RNF-1 preserved.
    """
    global _graph
    if _graph is None:
        _graph = KnowledgeGraph()
        if not _graph.load():
            _graph = build_graph(bucket="external")
            _graph.save()
    return _graph


# STORY-RAG-VM-G2 — per-bucket graph cache, SEPARATE from the external singleton.
_bucket_graphs: dict[str, KnowledgeGraph] = {}


def get_graph_for_bucket(bucket: str = "external") -> KnowledgeGraph:
    """Load the KnowledgeGraph for ``bucket`` (Art. XIII bucket-aware PPR loader).

    This is the seam the PPR caller uses to feed the walker the RIGHT bucket's graph
    WITHOUT touching ``associative_memory.py`` (RNF-1): the walker still receives a
    ``KnowledgeGraph`` via its ``graph=`` param; only WHICH graph changes here.

    Behavior:
    - ``external`` → delegates to ``get_graph()`` so external keeps its singleton and
      cold-build/save semantics (backward-compat, AC8);
    - other buckets → load ``graph-{bucket}.json`` (cached). If the file does not
      exist (e.g. personal with no DNA yet), returns an empty, ``built=False`` graph so
      the caller FAILS OPEN to BM25 (``graph_search`` returns its "Graph not built"
      branch) instead of crashing or leaking another bucket.

    NEVER builds a non-external graph on demand (that is rebuild.py's job) — a missing
    bucket file means "no graph for this bucket yet", not "build it now".
    """
    if bucket == "external":
        return get_graph()

    cached = _bucket_graphs.get(bucket)
    if cached is not None:
        return cached

    g = KnowledgeGraph()
    g.load(graph_file_for_bucket(bucket))  # built stays False if file is absent
    _bucket_graphs[bucket] = g
    return g


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build Knowledge Graph")
    parser.add_argument("--build", action="store_true", help="Force rebuild")
    parser.add_argument("--stats", action="store_true", help="Show stats only")
    parser.add_argument("--communities", action="store_true", help="Detect communities")
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print("KNOWLEDGE GRAPH BUILDER")
    print(f"{'=' * 60}\n")

    if args.stats and GRAPH_FILE.exists():
        graph = KnowledgeGraph()
        graph.load()
    else:
        t0 = time.time()
        graph = build_graph()
        elapsed = time.time() - t0
        graph.save()
        print(f"Build time: {elapsed:.2f}s")
        print(f"Saved to: {GRAPH_FILE}\n")

    stats = graph.stats
    print(f"Entities: {stats['total_entities']}")
    print(f"Edges: {stats['total_edges']}")
    print("\nBy type:")
    for t, c in sorted(stats["entities_by_type"].items()):
        print(f"  {t}: {c}")
    print("\nBy relation:")
    for r, c in sorted(stats["edges_by_type"].items()):
        print(f"  {r}: {c}")

    if args.communities:
        print(f"\n{'─' * 60}")
        print("COMMUNITIES:\n")
        communities = detect_communities(graph)
        for comm in communities[:15]:
            print(f"  {comm['domain']}: {comm['size']} entities, persons={comm['persons']}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
