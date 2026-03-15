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
- obsession           (from VALUES-HIERARCHY.yaml -- obsessions section)
- paradox             (from VALUES-HIERARCHY.yaml -- paradoxes section)
- voice_trait          (from VOICE-DNA.yaml -- signature phrases, metaphors)

Supports LazyGraphRAG pattern: community summaries generated on-demand.

Versao: 2.0.0
Data: 2026-03-10
"""

import json
import time
from collections import defaultdict
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
from core.paths import KNOWLEDGE_EXTERNAL, KNOWLEDGE_GRAPH

DNA_DIR = KNOWLEDGE_EXTERNAL / "dna" / "persons"
GRAPH_DIR = KNOWLEDGE_GRAPH
GRAPH_FILE = GRAPH_DIR / "graph.json"

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
}

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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "person": self.person,
            "domains": self.domains,
            "layer": self.layer,
            "weight": self.weight,
        }


class Edge:
    """A relationship in the knowledge graph."""

    __slots__ = ("metadata", "rel_type", "source", "target", "weight")

    def __init__(self, source: str, target: str, rel_type: str, **kwargs):
        self.source = source
        self.target = target
        self.rel_type = rel_type
        self.weight = kwargs.get("weight", 1.0)
        self.metadata = kwargs.get("metadata", {})

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "rel_type": self.rel_type,
            "weight": self.weight,
        }


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

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)
        self.adj[edge.source].append((edge.target, edge.rel_type, edge.weight))
        self.adj[edge.target].append((edge.source, edge.rel_type, edge.weight))

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

    def save(self, filepath: Path | None = None) -> None:
        p = filepath or GRAPH_FILE
        p.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "entities": {k: v.to_dict() for k, v in self.entities.items()},
            "edges": [e.to_dict() for e in self.edges],
            "stats": self.stats,
        }

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, filepath: Path | None = None) -> bool:
        p = filepath or GRAPH_FILE
        if not p.exists():
            return False

        with open(p, encoding="utf-8") as f:
            data = json.load(f)

        for eid, edata in data.get("entities", {}).items():
            self.entities[eid] = Entity(
                entity_id=edata["id"],
                entity_type=edata["type"],
                label=edata["label"],
                person=edata.get("person", ""),
                domains=edata.get("domains", []),
                layer=edata.get("layer", ""),
                weight=edata.get("weight", 1.0),
            )

        for edata in data.get("edges", []):
            edge = Edge(
                source=edata["source"],
                target=edata["target"],
                rel_type=edata["rel_type"],
                weight=edata.get("weight", 1.0),
            )
            self.edges.append(edge)
            self.adj[edge.source].append((edge.target, edge.rel_type, edge.weight))
            self.adj[edge.target].append((edge.source, edge.rel_type, edge.weight))

        self.built = True
        return True


# ---------------------------------------------------------------------------
# GRAPH BUILDER
# ---------------------------------------------------------------------------
def build_graph(dna_dir: Path | None = None) -> KnowledgeGraph:
    """Build knowledge graph from all DNA YAML files.

    Extracts:
    - Person entities
    - Domain entities
    - DNA entries (5 layers) as entities
    - Cross-layer relationships
    - Person-to-person relationships from CONFIG.yaml
    """
    d = dna_dir or DNA_DIR
    graph = KnowledgeGraph()
    all_domains: set[str] = set()

    if not d.exists():
        print(f"[GraphBuilder] DNA dir not found: {d}")
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

                domains = entry.get("dominios", [])
                if isinstance(domains, str):
                    domains = [domains]
                weight = entry.get("peso", 1.0)
                if not isinstance(weight, (int, float)):
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

        # Process MCE files (behavioral patterns, values, voice DNA)
        _process_mce_files(graph, person_dir, person, person_id)

    graph.built = True
    return graph


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
    """Process MCE YAML files for a person (behavioral patterns, values, voice).

    Gracefully skips if files don't exist (backward compatible).
    """
    _process_behavioral_patterns(graph, person_dir, person, person_id)
    _process_values_hierarchy(graph, person_dir, person, person_id)
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

        label = (
            entry.get("nome")
            or entry.get("name")
            or entry.get("pattern")
            or entry.get("description", "")[:100]
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
    """Process VALUES-HIERARCHY.yaml → value, obsession, paradox entities."""
    filepath = person_dir / "VALUES-HIERARCHY.yaml"
    if not filepath.exists():
        return

    data = _safe_load_yaml(filepath)
    if not data:
        return

    # Process values
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
        if not isinstance(rank, (int, float)):
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

    # Process obsessions
    obsessions = _extract_list(data, "obsessions", "obsessoes")
    for entry in obsessions:
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

    # Process paradoxes
    paradoxes = _extract_list(data, "paradoxes", "paradoxos")
    for entry in paradoxes:
        entry_id = entry.get("id", "")
        if not entry_id:
            entry_id = _generate_mce_id("PAR", person, entry)
            if not entry_id:
                continue

        label = (
            entry.get("nome")
            or entry.get("name")
            or entry.get("paradox")
            or entry.get("tension", "")[:100]
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
    if not isinstance(weight, (int, float)):
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
    """Get or create the knowledge graph singleton."""
    global _graph
    if _graph is None:
        _graph = KnowledgeGraph()
        if not _graph.load():
            _graph = build_graph()
            _graph.save()
    return _graph


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
