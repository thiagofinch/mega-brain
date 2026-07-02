#!/usr/bin/env python3
"""
rag_integration.py -- MCE Pipeline -> RAG Integration Layer
============================================================
Bridges MCE pipeline output to RAG system. Called by the index agent
after pipeline completion to make new knowledge immediately searchable.

Functions:
    rebuild_rag_index(slug, skip_vectors=False)
    enrich_knowledge_graph(slug)
    update_navigation_map(slug)
    update_tag_resolver(slug)
    validate_conclave_readiness(slug)
    update_domain_contracts(slug)

All functions are non-fatal (catch exceptions, return status dict).

EVO-4.2: RAG auto-rebuild after MCE pipeline completion.
EVO-4.3: Domain Contracts auto-update based on insight keywords.

Version: 1.0.0
Date: 2026-03-28
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import yaml

from engine.paths import (
    AGENTS_EXTERNAL,
    ARTIFACTS,
    KNOWLEDGE_EXTERNAL,
    ROOT,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DNA_DIR = KNOWLEDGE_EXTERNAL / "dna" / "persons"
NAV_MAP_PATH = KNOWLEDGE_EXTERNAL / "NAVIGATION-MAP.json"
TAG_RESOLVER_PATH = KNOWLEDGE_EXTERNAL / "TAG-RESOLVER.json"
CANONICAL_MAP_PATH = ARTIFACTS / "canonical" / "CANONICAL-MAP.json"
DOMAIN_CONTRACTS_PATH = ROOT / "core" / "intelligence" / "rag" / "domain_contracts.yaml"
INSIGHTS_DIR = ARTIFACTS / "insights"

# 10 DNA layer files (5 classic + 5 MCE)
DNA_LAYER_FILES = [
    "FILOSOFIAS.yaml",
    "MODELOS-MENTAIS.yaml",
    "HEURISTICAS.yaml",
    "FRAMEWORKS.yaml",
    "METODOLOGIAS.yaml",
    "BEHAVIORAL-PATTERNS.yaml",
    "VALUES-HIERARCHY.yaml",
    "VOICE-DNA.yaml",
    "OBSESSIONS.yaml",
    "PARADOXES.yaml",
]

# 5 required conclave agent files
CONCLAVE_AGENT_FILES = [
    "AGENT.md",
    "SOUL.md",
    "MEMORY.md",
    "DNA-CONFIG.yaml",
    "ACTIVATION.yaml",
]

# Domain keyword mapping for contract matching (EVO-4.3)
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "comercial": [
        "vendas",
        "comissão",
        "comissao",
        "closer",
        "objeção",
        "objecao",
        "conversion rate",
        "sales script",
        "close rate",
        "pipeline de vendas",
        "script de vendas",
        "sdr",
        "setter",
        "prospeccao",
        "prospecção",
        "discovery call",
        "cold calling",
    ],
    "marketing-growth": [
        "tráfego pago",
        "trafego pago",
        "anúncio",
        "anuncio",
        "criativo",
        "funil",
        "roas",
        "cac",
        "custo por lead",
        "cpl",
        "escala de campanha",
        "copy de anuncio",
        "paid traffic",
        "ads",
        "media buying",
        "landing page",
    ],
    "offer-pricing": [
        "oferta",
        "precificação",
        "precificacao",
        "garantia",
        "grand slam offer",
        "value equation",
        "equação de valor",
        "equacao de valor",
        "valor percebido",
        "empacotamento",
        "irresistible offer",
        "pricing",
    ],
}

# Minimum keyword matches to associate a slug with a domain
DOMAIN_MATCH_THRESHOLD = 3

# HE-002 temporal/evidence — DNA layer files carry an observation timestamp under
# one of these top-level keys (classic layers use ``updated``; MCE layers use
# ``data_extracao``). We read whichever is present, in order. This is the WHEN the
# knowledge was extracted/observed — a genuinely DERIVABLE t_obs, never fabricated.
_T_OBS_KEYS = ("updated", "data_extracao", "data", "updated_at")

# Per-entry fields that hold a VERBATIM source sentence (the anti-hallucination
# evidence for an edge). ``quote`` (classic DNA layers) is an actual transcript
# quote. We deliberately DO NOT treat paraphrased fields (description/evidence/
# action/resolution) as atomic_facts — those are LLM summaries, not verbatim
# source text, and mislabeling paraphrase as verbatim evidence would violate
# extraction-no-fallbacks (honesty over coverage).
_VERBATIM_QUOTE_KEYS = ("quote", "verbatim", "source_quote")


def _read_t_obs(data: dict[str, Any]) -> str | None:
    """Return the layer file's observation timestamp, or None (no fabrication).

    DERIVABLE evidence only: the timestamp the DNA layer was extracted/observed.
    Returns None when the file declares no timestamp — never a synthesized value.
    """
    if not isinstance(data, dict):
        return None
    for key in _T_OBS_KEYS:
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _entry_atomic_facts(entry: Any) -> list[str]:
    """Return verbatim source sentence(s) backing an edge, or [] (no fabrication).

    Only reads genuinely verbatim fields (``quote`` etc.). Paraphrased summary
    fields are intentionally excluded — an empty list is the honest answer when
    no verbatim quote exists for the entry.
    """
    if not isinstance(entry, dict):
        return []
    facts: list[str] = []
    for key in _VERBATIM_QUOTE_KEYS:
        val = entry.get(key)
        if isinstance(val, str) and val.strip():
            facts.append(val.strip())
    return facts


# ---------------------------------------------------------------------------
# 1. rebuild_rag_index
# ---------------------------------------------------------------------------
def rebuild_rag_index(
    slug: str,
    skip_vectors: bool = False,
) -> dict[str, Any]:
    """Rebuild RAG index for the external bucket after MCE pipeline completion.

    Imports ``core.intelligence.rag.rebuild.rebuild`` and calls it
    with ``bucket="external"``. If *skip_vectors* is True, only the BM25
    index is rebuilt (no vector embeddings).

    Returns:
        Dict with ``status``, ``chunks_indexed``, ``duration_ms``.
    """
    t0 = time.time()
    try:
        from engine.intelligence.rag.rebuild import rebuild

        result = rebuild(bucket="external", skip_vectors=skip_vectors)

        chunks = 0
        if isinstance(result, dict) and "external" in result:
            chunks = result["external"].get("chunks", 0)

        duration_ms = int((time.time() - t0) * 1000)
        logger.info(
            "rebuild_rag_index: slug=%s chunks=%d duration=%dms",
            slug,
            chunks,
            duration_ms,
        )
        return {
            "status": "ok",
            "chunks_indexed": chunks,
            "duration_ms": duration_ms,
            "raw": result,
        }
    except Exception as exc:
        duration_ms = int((time.time() - t0) * 1000)
        logger.error("rebuild_rag_index failed for %s: %s", slug, exc)
        return {
            "status": "error",
            "error": str(exc),
            "duration_ms": duration_ms,
        }


# ---------------------------------------------------------------------------
# 2. enrich_knowledge_graph
# ---------------------------------------------------------------------------
def enrich_knowledge_graph(slug: str) -> dict[str, Any]:
    """Enrich the knowledge graph with DNA data for *slug*.

    Reads all 10 DNA YAML files from the slug's person directory.
    For each file, adds entity nodes (type matches the layer name) and
    edges: TEM (person -> entry), PERTENCE_A (entry -> domain).

    Returns:
        Dict with ``nodes_added``, ``edges_added``.
    """
    try:
        from engine.intelligence.rag.graph_builder import (
            GRAPH_FILE,
            LAYER_KEYS,
            MCE_LAYER_KEYS,
            Edge,
            Entity,
            KnowledgeGraph,
            _load_yaml_entries,
        )

        person_dir = DNA_DIR / slug
        if not person_dir.exists():
            return {
                "status": "error",
                "error": f"DNA directory not found: {person_dir}",
                "nodes_added": 0,
                "edges_added": 0,
            }

        # Load existing graph or create new
        graph = KnowledgeGraph()
        if GRAPH_FILE.exists():
            try:
                raw = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
                # The persisted graph stores ``entities`` as a dict
                # ({entity_id: {...}}); older snapshots used a list. Accept both
                # so a re-run never crashes on the normal (dict) shape — the bug
                # that silently produced 0 edges on every existing graph.
                _raw_entities = raw.get("entities", [])
                _entity_iter = (
                    _raw_entities.values()
                    if isinstance(_raw_entities, dict)
                    else _raw_entities
                )
                for ent in _entity_iter:
                    graph.add_entity(
                        Entity(
                            entity_id=ent["id"],
                            entity_type=ent["type"],
                            label=ent["label"],
                            person=ent.get("person", ""),
                            domains=ent.get("domains", []),
                            layer=ent.get("layer", ""),
                            weight=ent.get("weight", 1.0),
                        )
                    )
                for edg in raw.get("edges", []):
                    # Preserve HE-002 temporal/evidence fields on reload so a
                    # re-run never strips them from previously-enriched edges
                    # (omit-when-empty keeps legacy edges byte-identical).
                    graph.add_edge(
                        Edge(
                            source=edg["source"],
                            target=edg["target"],
                            rel_type=edg["rel_type"],
                            weight=edg.get("weight", 1.0),
                            metadata=edg.get("metadata", {}),
                            t_start=edg.get("t_start"),
                            t_end=edg.get("t_end"),
                            t_obs=edg.get("t_obs"),
                            atomic_facts=edg.get("atomic_facts"),
                        )
                    )
            except (json.JSONDecodeError, KeyError, TypeError) as load_err:
                logger.warning("Could not load existing graph, starting fresh: %s", load_err)

        initial_entities = len(graph.entities)
        initial_edges = len(graph.edges)

        person_id = f"PESSOA:{slug}"

        # Ensure person entity exists
        if person_id not in graph.entities:
            graph.add_entity(
                Entity(
                    entity_id=person_id,
                    entity_type="pessoa",
                    label=slug.replace("-", " ").title(),
                    person=slug,
                )
            )

        # Process classic DNA layers (5 layers)
        for filename, key in LAYER_KEYS.items():
            filepath = person_dir / filename
            if not filepath.exists():
                continue
            try:
                data = yaml.safe_load(filepath.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                continue
            if not isinstance(data, dict):
                continue

            # HE-002: layer observation timestamp (DERIVABLE — when extracted).
            t_obs = _read_t_obs(data)

            # Derive entity type from layer key (e.g. "filosofias" -> "filosofia")
            entity_type = key.rstrip("s")
            # Modern DNA files nest entries under ``entries`` (not under ``key``);
            # _load_yaml_entries handles both shapes (key, then any-list fallback),
            # so this no longer silently reads zero entries on current DNA.
            entries = _load_yaml_entries(filepath, key)
            if isinstance(entries, list):
                for i, entry in enumerate(entries):
                    label = entry.get("nome", entry.get("name", f"{key}_{i}"))
                    eid = f"{entity_type}:{slug}:{label}"
                    domains = entry.get("dominios", entry.get("domains", []))
                    # HE-002 evidence: verbatim source quote backing this edge.
                    atomic_facts = _entry_atomic_facts(entry)

                    graph.add_entity(
                        Entity(
                            entity_id=eid,
                            entity_type=entity_type,
                            label=label,
                            person=slug,
                            domains=domains,
                            layer=key,
                        )
                    )
                    graph.add_edge(
                        Edge(
                            source=person_id,
                            target=eid,
                            rel_type="TEM",
                            t_obs=t_obs,
                            atomic_facts=atomic_facts,
                        )
                    )
                    # Add PERTENCE_A edges for each domain
                    for dom in domains if isinstance(domains, list) else []:
                        dom_id = f"DOMINIO:{dom}"
                        if dom_id not in graph.entities:
                            graph.add_entity(
                                Entity(
                                    entity_id=dom_id,
                                    entity_type="dominio",
                                    label=dom,
                                )
                            )
                        graph.add_edge(
                            Edge(
                                source=eid,
                                target=dom_id,
                                rel_type="PERTENCE_A",
                                t_obs=t_obs,
                            )
                        )

        # Process MCE layers (5 layers)
        for filename, config in MCE_LAYER_KEYS.items():
            filepath = person_dir / filename
            if not filepath.exists():
                continue
            try:
                data = yaml.safe_load(filepath.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                continue
            if not isinstance(data, dict):
                continue

            # HE-002: layer observation timestamp (DERIVABLE — when extracted).
            t_obs = _read_t_obs(data)

            if "sections" in config:
                # Multi-section file (e.g. VALUES-HIERARCHY.yaml)
                for section_key, section_cfg in config["sections"].items():
                    entries = data.get(section_key, [])
                    if isinstance(entries, list):
                        for i, entry in enumerate(entries):
                            label = (
                                entry.get("nome", entry.get("name", ""))
                                if isinstance(entry, dict)
                                else str(entry)
                            )
                            if not label:
                                label = f"{section_key}_{i}"
                            eid = f"{section_cfg['entity_type']}:{slug}:{label}"
                            atomic_facts = _entry_atomic_facts(entry)
                            graph.add_entity(
                                Entity(
                                    entity_id=eid,
                                    entity_type=section_cfg["entity_type"],
                                    label=label,
                                    person=slug,
                                    layer=section_key,
                                )
                            )
                            graph.add_edge(
                                Edge(
                                    source=person_id,
                                    target=eid,
                                    rel_type=section_cfg["rel_type"],
                                    t_obs=t_obs,
                                    atomic_facts=atomic_facts,
                                )
                            )
            else:
                # Single-section file
                top_key = config.get("key", "")
                entries = data.get(top_key, [])
                # Try alt_keys if primary is empty
                if not entries and "alt_keys" in config:
                    for alt in config["alt_keys"]:
                        entries = data.get(alt, [])
                        if entries:
                            break

                if isinstance(entries, list):
                    for i, entry in enumerate(entries):
                        label = (
                            entry.get("nome", entry.get("name", ""))
                            if isinstance(entry, dict)
                            else str(entry)
                        )
                        if not label:
                            label = f"{config['entity_type']}_{i}"
                        eid = f"{config['entity_type']}:{slug}:{label}"
                        atomic_facts = _entry_atomic_facts(entry)
                        graph.add_entity(
                            Entity(
                                entity_id=eid,
                                entity_type=config["entity_type"],
                                label=label,
                                person=slug,
                                layer=top_key,
                            )
                        )
                        graph.add_edge(
                            Edge(
                                source=person_id,
                                target=eid,
                                rel_type=config["rel_type"],
                                t_obs=t_obs,
                                atomic_facts=atomic_facts,
                            )
                        )

        # Save updated graph
        GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
        graph_data = {
            "entities": [e.to_dict() for e in graph.entities.values()],
            "edges": [e.to_dict() for e in graph.edges],
        }
        GRAPH_FILE.write_text(
            json.dumps(graph_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        nodes_added = len(graph.entities) - initial_entities
        edges_added = len(graph.edges) - initial_edges

        logger.info(
            "enrich_knowledge_graph: slug=%s nodes_added=%d edges_added=%d",
            slug,
            nodes_added,
            edges_added,
        )
        return {
            "status": "ok",
            "nodes_added": nodes_added,
            "edges_added": edges_added,
        }
    except Exception as exc:
        logger.error("enrich_knowledge_graph failed for %s: %s", slug, exc)
        return {
            "status": "error",
            "error": str(exc),
            "nodes_added": 0,
            "edges_added": 0,
        }


# ---------------------------------------------------------------------------
# 3. update_navigation_map
# ---------------------------------------------------------------------------
def update_navigation_map(slug: str) -> dict[str, Any]:
    """Update NAVIGATION-MAP.json with dossier sections for *slug*.

    Reads the existing navigation map, checks if the slug's dossier
    sections are mapped. If not, discovers sections from the dossier
    file and adds mappings for new sections -> chunk_ids.

    Returns:
        Dict with ``sections_added``.
    """
    try:
        if not NAV_MAP_PATH.exists():
            return {
                "status": "error",
                "error": f"NAVIGATION-MAP.json not found at {NAV_MAP_PATH}",
                "sections_added": 0,
            }

        nav_map = json.loads(NAV_MAP_PATH.read_text(encoding="utf-8"))
        dossiers = nav_map.get("dossiers", {})
        persons = dossiers.get("persons", {})

        dossier_key = f"DOSSIER-{slug.upper()}.md"

        # If dossier already mapped, check if it has sections
        if dossier_key in persons and persons[dossier_key].get("sections"):
            logger.info(
                "update_navigation_map: slug=%s already mapped with %d sections",
                slug,
                len(persons[dossier_key]["sections"]),
            )
            return {"status": "ok", "sections_added": 0}

        # Try to discover sections from dossier file
        dossier_path = KNOWLEDGE_EXTERNAL / "dossiers" / "persons" / dossier_key
        sections: dict[str, list[str]] = {}

        if dossier_path.exists():
            content = dossier_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("## ") and not stripped.startswith("###"):
                    section_name = stripped[3:].strip()
                    sections[section_name] = []
        else:
            # Derive sections from DNA layer files
            person_dir = DNA_DIR / slug
            if person_dir.exists():
                for layer_file in DNA_LAYER_FILES:
                    fpath = person_dir / layer_file
                    if fpath.exists():
                        section_name = layer_file.replace(".yaml", "").replace("-", " ").title()
                        sections[section_name] = []

        if not sections:
            return {"status": "ok", "sections_added": 0}

        # Add to navigation map
        persons[dossier_key] = {
            "path": f"/knowledge/external/dossiers/persons/{dossier_key}",
            "source_ids": [],
            "sections": sections,
        }
        dossiers["persons"] = persons
        nav_map["dossiers"] = dossiers

        NAV_MAP_PATH.write_text(
            json.dumps(nav_map, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info(
            "update_navigation_map: slug=%s sections_added=%d",
            slug,
            len(sections),
        )
        return {"status": "ok", "sections_added": len(sections)}
    except Exception as exc:
        logger.error("update_navigation_map failed for %s: %s", slug, exc)
        return {
            "status": "error",
            "error": str(exc),
            "sections_added": 0,
        }


# ---------------------------------------------------------------------------
# 4. update_tag_resolver
# ---------------------------------------------------------------------------
def update_tag_resolver(slug: str) -> dict[str, Any]:
    """Update TAG-RESOLVER.json with entity tags from CANONICAL-MAP.json.

    Reads the canonical map for entity aliases, checks which are missing
    from the tag resolver, and adds them.

    Returns:
        Dict with ``tags_added``.
    """
    try:
        if not TAG_RESOLVER_PATH.exists():
            return {
                "status": "error",
                "error": f"TAG-RESOLVER.json not found at {TAG_RESOLVER_PATH}",
                "tags_added": 0,
            }
        if not CANONICAL_MAP_PATH.exists():
            return {
                "status": "error",
                "error": f"CANONICAL-MAP.json not found at {CANONICAL_MAP_PATH}",
                "tags_added": 0,
            }

        tag_resolver = json.loads(TAG_RESOLVER_PATH.read_text(encoding="utf-8"))
        canonical = json.loads(CANONICAL_MAP_PATH.read_text(encoding="utf-8"))

        tag_to_path = tag_resolver.get("tag_to_path", {})
        canonical_map = canonical.get("canonical_state", {}).get("canonical_map", {})

        tags_added = 0

        # Find entities matching slug (slug is kebab-case, canonical names may differ)
        slug_label = slug.replace("-", " ").lower()
        for entity_name, aliases in canonical_map.items():
            name_lower = entity_name.lower()
            # Match if entity name contains the slug parts
            if slug_label not in name_lower and name_lower not in slug_label:
                continue

            # Add entity tags for DNA files
            person_dir = DNA_DIR / slug
            if not person_dir.exists():
                continue

            for layer_file in DNA_LAYER_FILES:
                fpath = person_dir / layer_file
                if not fpath.exists():
                    continue
                tag_key = f"{slug.upper()}:{layer_file.replace('.yaml', '')}"
                if tag_key not in tag_to_path:
                    tag_to_path[tag_key] = str(fpath.relative_to(ROOT))
                    tags_added += 1

        if tags_added > 0:
            tag_resolver["tag_to_path"] = tag_to_path
            # Update stats
            stats = tag_resolver.get("stats", {})
            stats["total_files_scanned"] = stats.get("total_files_scanned", 0) + tags_added
            stats["files_with_tag"] = stats.get("files_with_tag", 0) + tags_added
            tag_resolver["stats"] = stats

            TAG_RESOLVER_PATH.write_text(
                json.dumps(tag_resolver, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        logger.info("update_tag_resolver: slug=%s tags_added=%d", slug, tags_added)
        return {"status": "ok", "tags_added": tags_added}
    except Exception as exc:
        logger.error("update_tag_resolver failed for %s: %s", slug, exc)
        return {"status": "error", "error": str(exc), "tags_added": 0}


# ---------------------------------------------------------------------------
# 5. validate_conclave_readiness
# ---------------------------------------------------------------------------
def validate_conclave_readiness(slug: str) -> dict[str, Any]:
    """Validate that all required files exist for a conclave agent.

    Checks:
    - ``agents/external/{slug}/`` has all 5 files (AGENT.md, SOUL.md,
      MEMORY.md, DNA-CONFIG.yaml, ACTIVATION.yaml)
    - ``knowledge/external/dna/persons/{slug}/`` has all 10 YAML files

    Returns:
        Dict with ``ready`` (bool), ``missing_files`` (list),
        ``total_layers`` (int).
    """
    try:
        agent_dir = AGENTS_EXTERNAL / slug
        person_dir = DNA_DIR / slug
        missing: list[str] = []

        # Check 5 agent files
        for fname in CONCLAVE_AGENT_FILES:
            fpath = agent_dir / fname
            if not fpath.exists():
                missing.append(f"agents/external/{slug}/{fname}")

        # Check 10 DNA layer files
        total_layers = 0
        for fname in DNA_LAYER_FILES:
            fpath = person_dir / fname
            if fpath.exists():
                total_layers += 1
            else:
                missing.append(f"knowledge/external/dna/persons/{slug}/{fname}")

        ready = len(missing) == 0

        logger.info(
            "validate_conclave_readiness: slug=%s ready=%s missing=%d total_layers=%d",
            slug,
            ready,
            len(missing),
            total_layers,
        )
        return {
            "status": "ok",
            "ready": ready,
            "missing_files": missing,
            "total_layers": total_layers,
        }
    except Exception as exc:
        logger.error("validate_conclave_readiness failed for %s: %s", slug, exc)
        return {
            "status": "error",
            "error": str(exc),
            "ready": False,
            "missing_files": [],
            "total_layers": 0,
        }


# ---------------------------------------------------------------------------
# 6. update_domain_contracts (EVO-4.3)
# ---------------------------------------------------------------------------
def update_domain_contracts(slug: str) -> dict[str, Any]:
    """Auto-update domain contracts based on insight keyword matching.

    Reads ``core/intelligence/rag/domain_contracts.yaml`` and the central
    ``artifacts/insights/INSIGHTS-STATE.json``. Extracts all insight text
    and checks against domain keyword sets. If a slug matches a domain
    (>= 3 keyword matches), adds the slug's DNA files to that domain's
    ``always_read`` list.

    Returns:
        Dict with ``domains_matched`` (list), ``files_added`` (int).
    """
    try:
        if not DOMAIN_CONTRACTS_PATH.exists():
            return {
                "status": "error",
                "error": f"domain_contracts.yaml not found at {DOMAIN_CONTRACTS_PATH}",
                "domains_matched": [],
                "files_added": 0,
            }

        # Load domain contracts
        contracts_raw = yaml.safe_load(DOMAIN_CONTRACTS_PATH.read_text(encoding="utf-8"))
        contracts = contracts_raw.get("contracts", {})

        # Collect all insight text for keyword matching
        insight_texts: list[str] = []

        # Try INSIGHTS-STATE.json (central state file)
        insights_state_path = INSIGHTS_DIR / "INSIGHTS-STATE.json"
        if insights_state_path.exists():
            try:
                state = json.loads(insights_state_path.read_text(encoding="utf-8"))
                categories = state.get("categories", {})
                for _cat_name, cat_data in categories.items():
                    for ins in cat_data.get("insights", []):
                        text = ins.get("insight", "")
                        if text:
                            insight_texts.append(text.lower())
            except (json.JSONDecodeError, KeyError):
                pass

        # Also try slug-specific insight files (pattern: {PREFIX}-insights.json)
        slug_upper = slug.upper()
        slug_prefix = slug_upper.replace("-", "")[:2]
        for fpath in INSIGHTS_DIR.glob("*.json"):
            fname = fpath.name.upper()
            if slug_upper in fname or slug_prefix in fname:
                try:
                    data = json.loads(fpath.read_text(encoding="utf-8"))
                    for ins in data.get("insights", []):
                        text = ins.get("insight", ins.get("text", ""))
                        if text:
                            insight_texts.append(text.lower())
                except (json.JSONDecodeError, KeyError):
                    pass

        if not insight_texts:
            logger.info("update_domain_contracts: no insights found for %s", slug)
            return {"status": "ok", "domains_matched": [], "files_added": 0}

        # Combine all insight text for matching
        combined_text = " ".join(insight_texts)

        # Check each domain for keyword matches
        domains_matched: list[str] = []
        total_files_added = 0

        person_dir = DNA_DIR / slug
        if not person_dir.exists():
            return {
                "status": "error",
                "error": f"DNA directory not found: {person_dir}",
                "domains_matched": [],
                "files_added": 0,
            }

        for domain_key, keywords in DOMAIN_KEYWORDS.items():
            match_count = sum(1 for kw in keywords if kw.lower() in combined_text)
            if match_count < DOMAIN_MATCH_THRESHOLD:
                continue

            domains_matched.append(domain_key)
            logger.info(
                "update_domain_contracts: slug=%s matched domain=%s (%d keywords)",
                slug,
                domain_key,
                match_count,
            )

            # Get or create domain contract
            domain_contract = contracts.get(domain_key, {})
            always_read = domain_contract.get("always_read", [])
            always_read_set = set(always_read)

            # Add slug's DNA files that exist
            files_added_for_domain = 0
            for layer_file in DNA_LAYER_FILES:
                fpath = person_dir / layer_file
                if not fpath.exists():
                    continue
                rel_path = str(fpath.relative_to(ROOT))
                if rel_path not in always_read_set:
                    always_read.append(rel_path)
                    always_read_set.add(rel_path)
                    files_added_for_domain += 1

            # Also add dossier if it exists
            dossier_path = (
                KNOWLEDGE_EXTERNAL / "dossiers" / "persons" / f"DOSSIER-{slug.upper()}.md"
            )
            if dossier_path.exists():
                rel_dossier = str(dossier_path.relative_to(ROOT))
                if rel_dossier not in always_read_set:
                    always_read.append(rel_dossier)
                    files_added_for_domain += 1

            if files_added_for_domain > 0:
                domain_contract["always_read"] = always_read
                contracts[domain_key] = domain_contract
                total_files_added += files_added_for_domain

        # Write updated contracts if changes were made
        if total_files_added > 0:
            contracts_raw["contracts"] = contracts
            DOMAIN_CONTRACTS_PATH.write_text(
                yaml.dump(contracts_raw, default_flow_style=False, allow_unicode=True),
                encoding="utf-8",
            )

        logger.info(
            "update_domain_contracts: slug=%s domains=%s files_added=%d",
            slug,
            domains_matched,
            total_files_added,
        )
        return {
            "status": "ok",
            "domains_matched": domains_matched,
            "files_added": total_files_added,
        }
    except Exception as exc:
        logger.error("update_domain_contracts failed for %s: %s", slug, exc)
        return {
            "status": "error",
            "error": str(exc),
            "domains_matched": [],
            "files_added": 0,
        }
