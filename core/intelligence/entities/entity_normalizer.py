#!/usr/bin/env python3
"""
ENTITY NORMALIZER - Intelligence Layer v1.0
============================================
Canonicalizacao continua de entidades (pessoas, temas, roles, conceitos).

Resolve:
- Exact match nos aliases do ENTITY-REGISTRY
- Fuzzy match via difflib (threshold 0.85)
- Domain-aware boost para roles/temas
- Auto-merge acima de 0.95 similaridade
- Review queue entre 0.85-0.95

Usado por: theme_analyzer.py, role_detector.py, bootstrap_registry.py,
           post_batch_cascading.py v3.0

Versao: 1.0.0
Data: 2026-02-24
"""

import json
import os
import re
import sys
import yaml
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
REGISTRY_PATH = BASE_DIR / "processing" / "canonical" / "ENTITY-REGISTRY.json"
TAXONOMY_PATH = BASE_DIR / "knowledge" / "dna" / "DOMAINS-TAXONOMY.yaml"
TRIGGER_CONFIG_PATH = BASE_DIR / "scripts" / "trigger_config.yaml"
REVIEW_QUEUE_PATH = BASE_DIR / "processing" / "canonical" / "review_queue.jsonl"

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DEFAULT_FUZZY_THRESHOLD = 0.85
DEFAULT_AUTO_MERGE_THRESHOLD = 0.95
DEFAULT_MIN_OCCURRENCES_TO_CONFIRM = 3


def load_trigger_config():
    """Load thresholds from trigger_config.yaml."""
    if TRIGGER_CONFIG_PATH.exists():
        with open(TRIGGER_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_thresholds():
    """Get entity canonicalization thresholds."""
    config = load_trigger_config()
    ec = config.get("thresholds", {}).get("entity_canonicalization", {})
    return {
        "fuzzy_threshold": ec.get("fuzzy_threshold", DEFAULT_FUZZY_THRESHOLD),
        "auto_merge_threshold": ec.get("auto_merge_threshold", DEFAULT_AUTO_MERGE_THRESHOLD),
        "min_occurrences_to_confirm": ec.get("min_occurrences_to_confirm", DEFAULT_MIN_OCCURRENCES_TO_CONFIRM),
    }


# ---------------------------------------------------------------------------
# REGISTRY I/O
# ---------------------------------------------------------------------------
def load_registry():
    """Load ENTITY-REGISTRY.json. Returns empty structure if not found."""
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return create_empty_registry()


def save_registry(registry):
    """Save ENTITY-REGISTRY.json with version bump."""
    registry["metadata"]["updated_at"] = datetime.now(timezone.utc).isoformat()
    v = registry["metadata"].get("version", 0)
    registry["metadata"]["version"] = v + 1
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def create_empty_registry():
    """Create empty registry structure."""
    return {
        "metadata": {
            "version": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "description": "ENTITY-REGISTRY - Single Source of Truth for Mega Brain entities"
        },
        "persons": {},
        "themes": {},
        "roles": {},
        "concepts": {}
    }


# ---------------------------------------------------------------------------
# TAXONOMY LOADER
# ---------------------------------------------------------------------------
_taxonomy_cache = None


def load_taxonomy():
    """Load DOMAINS-TAXONOMY.yaml (cached)."""
    global _taxonomy_cache
    if _taxonomy_cache is not None:
        return _taxonomy_cache
    if TAXONOMY_PATH.exists():
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
            _taxonomy_cache = yaml.safe_load(f)
    else:
        _taxonomy_cache = {}
    return _taxonomy_cache


def get_domain_aliases():
    """Build flat map: alias -> domain_id from taxonomy."""
    tax = load_taxonomy()
    alias_map = {}
    for dom in tax.get("dominios", []):
        did = dom["id"]
        alias_map[did.lower()] = did
        for a in dom.get("aliases", []):
            alias_map[a.lower()] = did
        for s in dom.get("subdominios", []):
            alias_map[s.lower()] = did
    return alias_map


def get_role_aliases():
    """Build flat map: alias -> canonical_role from taxonomy."""
    tax = load_taxonomy()
    role_map = {}
    for role_key in tax.get("cargos", {}):
        canonical = role_key.upper()
        role_map[canonical.lower()] = canonical
        # common variations
        nice = canonical.replace("-", " ")
        role_map[nice.lower()] = canonical
    return role_map


def get_person_aliases():
    """Build flat map: alias -> canonical_person from taxonomy."""
    tax = load_taxonomy()
    person_map = {}
    for pkey in tax.get("pessoas", {}):
        canonical = pkey.upper()
        person_map[canonical.lower()] = canonical
        nice = canonical.replace("-", " ")
        person_map[nice.lower()] = canonical
    return person_map


# ---------------------------------------------------------------------------
# NORMALIZATION (text utils)
# ---------------------------------------------------------------------------
def normalize_text(text):
    """Normalize text for comparison: lowercase, strip, collapse whitespace."""
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_entity_key(name):
    """Create a normalized key for registry lookup."""
    return normalize_text(name)


# ---------------------------------------------------------------------------
# FUZZY MATCHING
# ---------------------------------------------------------------------------
def similarity(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def find_best_match(name, candidates, threshold=None):
    """
    Find best fuzzy match for `name` among `candidates`.

    Args:
        name: string to match
        candidates: dict of {canonical: entity_data} or list of canonical names
        threshold: minimum similarity (default from config)

    Returns:
        (canonical_name, score) or (None, 0.0)
    """
    if threshold is None:
        threshold = get_thresholds()["fuzzy_threshold"]

    norm_name = normalize_text(name)
    if not norm_name:
        return None, 0.0

    best_match = None
    best_score = 0.0

    if isinstance(candidates, dict):
        candidate_list = list(candidates.keys())
    else:
        candidate_list = list(candidates)

    for canonical in candidate_list:
        # Check canonical name
        score = similarity(norm_name, canonical)
        if score > best_score:
            best_score = score
            best_match = canonical

        # Check aliases if dict with entity data
        if isinstance(candidates, dict):
            entity = candidates[canonical]
            for alias in entity.get("aliases", []):
                score = similarity(norm_name, alias)
                if score > best_score:
                    best_score = score
                    best_match = canonical

    if best_score >= threshold:
        return best_match, best_score
    return None, 0.0


# ---------------------------------------------------------------------------
# CORE: NORMALIZE ENTITY
# ---------------------------------------------------------------------------
def normalize_entity(name, entity_type, registry=None, source_id=None,
                     auto_save=False, domain_hint=None):
    """
    Main normalization function. Resolves a raw entity name to its canonical form.

    Resolution order:
    1. Exact match on canonical names
    2. Exact match on aliases
    3. Fuzzy match (>= threshold)
    4. Domain-aware boost for roles/themes
    5. New entity creation if no match

    Args:
        name: raw entity name (e.g. "closer", "Alex hormozi", "processo de vendas")
        entity_type: "person" | "theme" | "role" | "concept"
        registry: ENTITY-REGISTRY dict (loaded if None)
        source_id: source that mentioned this entity
        auto_save: save registry after modification
        domain_hint: optional domain_id for context-aware matching

    Returns:
        {
            "canonical": str,
            "match_type": "exact" | "alias" | "fuzzy" | "domain_boost" | "new",
            "score": float,
            "entity_type": str,
            "created": bool
        }
    """
    if registry is None:
        registry = load_registry()

    thresholds = get_thresholds()
    norm_name = normalize_text(name)
    if not norm_name:
        return {"canonical": name, "match_type": "empty", "score": 0.0,
                "entity_type": entity_type, "created": False}

    # Map entity_type to registry section
    section_map = {
        "person": "persons",
        "theme": "themes",
        "role": "roles",
        "concept": "concepts"
    }
    section = section_map.get(entity_type, "concepts")
    entities = registry.get(section, {})

    # ----- STEP 1: Exact match on canonical names -----
    for canonical, data in entities.items():
        if normalize_text(canonical) == norm_name:
            _increment_entity(data, source_id)
            if auto_save:
                save_registry(registry)
            return {"canonical": canonical, "match_type": "exact", "score": 1.0,
                    "entity_type": entity_type, "created": False}

    # ----- STEP 2: Exact match on aliases -----
    for canonical, data in entities.items():
        for alias in data.get("aliases", []):
            if normalize_text(alias) == norm_name:
                _increment_entity(data, source_id)
                if auto_save:
                    save_registry(registry)
                return {"canonical": canonical, "match_type": "alias", "score": 1.0,
                        "entity_type": entity_type, "created": False}

    # ----- STEP 3: Fuzzy match -----
    best_canonical, best_score = find_best_match(name, entities,
                                                  threshold=thresholds["fuzzy_threshold"])

    # ----- STEP 4: Domain-aware boost -----
    if domain_hint and entity_type in ("role", "theme"):
        boosted = _domain_boost(name, entities, domain_hint)
        if boosted and boosted[1] > best_score:
            best_canonical, best_score = boosted

    if best_canonical and best_score >= thresholds["auto_merge_threshold"]:
        # Auto-merge: add as alias
        entity_data = entities[best_canonical]
        if norm_name not in [normalize_text(a) for a in entity_data.get("aliases", [])]:
            entity_data.setdefault("aliases", []).append(name)
        _increment_entity(entity_data, source_id)
        if auto_save:
            save_registry(registry)
        return {"canonical": best_canonical, "match_type": "fuzzy", "score": best_score,
                "entity_type": entity_type, "created": False}

    if best_canonical and best_score >= thresholds["fuzzy_threshold"]:
        # Candidate merge: add to review queue
        _add_to_review_queue(name, best_canonical, best_score, entity_type, source_id)
        _increment_entity(entities[best_canonical], source_id)
        if auto_save:
            save_registry(registry)
        return {"canonical": best_canonical, "match_type": "fuzzy_candidate", "score": best_score,
                "entity_type": entity_type, "created": False}

    # ----- STEP 5: Check taxonomy before creating new -----
    taxonomy_match = _check_taxonomy(name, entity_type)
    if taxonomy_match:
        # Entity known in taxonomy but not in registry - create with taxonomy info
        canonical = taxonomy_match["canonical"]
        if canonical not in entities:
            entities[canonical] = _create_entity(
                canonical, entity_type, source_id,
                aliases=[name] if normalize_text(name) != normalize_text(canonical) else [],
                domain_ids=taxonomy_match.get("domain_ids", [])
            )
            if auto_save:
                save_registry(registry)
            return {"canonical": canonical, "match_type": "taxonomy", "score": 1.0,
                    "entity_type": entity_type, "created": True}

    # ----- STEP 6: New entity -----
    canonical = _make_canonical_name(name, entity_type)
    if canonical not in entities:
        entities[canonical] = _create_entity(canonical, entity_type, source_id)
        if auto_save:
            save_registry(registry)
        return {"canonical": canonical, "match_type": "new", "score": 0.0,
                "entity_type": entity_type, "created": True}

    return {"canonical": canonical, "match_type": "existing", "score": 1.0,
            "entity_type": entity_type, "created": False}


# ---------------------------------------------------------------------------
# BATCH NORMALIZATION
# ---------------------------------------------------------------------------
def normalize_entities_batch(entities_list, entity_type, registry=None,
                             source_id=None, auto_save=True):
    """
    Normalize a list of entity names in batch.

    Args:
        entities_list: list of raw entity names
        entity_type: "person" | "theme" | "role" | "concept"
        registry: shared registry dict
        source_id: source that mentioned these entities
        auto_save: save registry after all normalizations

    Returns:
        list of normalization results
    """
    if registry is None:
        registry = load_registry()

    results = []
    for name in entities_list:
        result = normalize_entity(name, entity_type, registry=registry,
                                  source_id=source_id, auto_save=False)
        results.append(result)

    if auto_save:
        save_registry(registry)

    return results


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------
def _increment_entity(entity_data, source_id=None):
    """Increment occurrence count and add source."""
    count_key = "mention_count" if "mention_count" in entity_data else "occurrence_count"
    entity_data[count_key] = entity_data.get(count_key, 0) + 1
    if source_id:
        sources = entity_data.setdefault("sources", [])
        if source_id not in sources:
            sources.append(source_id)
    entity_data["last_seen"] = datetime.now(timezone.utc).isoformat()


def _create_entity(canonical, entity_type, source_id=None, aliases=None,
                   domain_ids=None):
    """Create a new entity entry."""
    now = datetime.now(timezone.utc).isoformat()
    count_key = "mention_count" if entity_type in ("person", "role") else "occurrence_count"
    entity = {
        "canonical": canonical,
        "aliases": aliases or [],
        count_key: 1,
        "sources": [source_id] if source_id else [],
        "status": "tracking",
        "created_at": now,
        "last_seen": now,
    }
    if entity_type == "theme":
        entity["has_dossier"] = False
        entity["domain_ids"] = domain_ids or []
        entity["related_roles"] = []
    elif entity_type == "role":
        entity["has_agent"] = False
        entity["domain_ids"] = domain_ids or []
        entity["responsibilities"] = []
        entity["mention_breakdown"] = {"direct": 0, "inferred": 0, "emergent": 0}
        entity["weighted_score"] = 0.0
        entity["detection_history"] = []
    elif entity_type == "person":
        entity["has_agent"] = False
        entity["has_dna"] = False
        entity["domains"] = domain_ids or []
    elif entity_type == "concept":
        entity["layer"] = None  # L1-L5
    return entity


def _make_canonical_name(name, entity_type):
    """Create canonical name from raw name."""
    name = name.strip()
    if entity_type == "person":
        # Title Case for persons
        return " ".join(w.capitalize() for w in name.split())
    elif entity_type == "role":
        # UPPER-CASE-WITH-HYPHENS for roles
        return re.sub(r"\s+", "-", name.strip().upper())
    elif entity_type == "theme":
        # lowercase-with-hyphens for themes
        clean = re.sub(r"[^\w\s-]", "", name.lower())
        return re.sub(r"\s+", "-", clean.strip())
    else:
        # Title Case for concepts
        return " ".join(w.capitalize() for w in name.split())


def _domain_boost(name, entities, domain_hint):
    """
    Boost matching score for entities in the same domain.
    If an entity shares the domain_hint, its fuzzy score gets +0.10 boost.
    """
    norm_name = normalize_text(name)
    best_match = None
    best_score = 0.0

    for canonical, data in entities.items():
        domains = data.get("domain_ids", [])
        if domain_hint in domains:
            score = similarity(norm_name, canonical) + 0.10  # domain boost
            if score > best_score:
                best_score = score
                best_match = canonical
            for alias in data.get("aliases", []):
                score = similarity(norm_name, alias) + 0.10
                if score > best_score:
                    best_score = score
                    best_match = canonical

    if best_match and best_score >= get_thresholds()["fuzzy_threshold"]:
        return best_match, min(best_score, 1.0)
    return None


def _check_taxonomy(name, entity_type):
    """Check if entity exists in DOMAINS-TAXONOMY."""
    norm = normalize_text(name)

    if entity_type == "role":
        role_map = get_role_aliases()
        if norm in role_map:
            canonical = role_map[norm]
            tax = load_taxonomy()
            cargo_data = tax.get("cargos", {}).get(canonical, {})
            domains = cargo_data.get("dominios_primarios", []) + cargo_data.get("dominios_secundarios", [])
            return {"canonical": canonical, "domain_ids": domains}

    elif entity_type == "person":
        person_map = get_person_aliases()
        if norm in person_map:
            canonical = person_map[norm]
            tax = load_taxonomy()
            person_data = tax.get("pessoas", {}).get(canonical, {})
            domains = person_data.get("expertise_primaria", []) + person_data.get("expertise_secundaria", [])
            return {"canonical": canonical, "domain_ids": domains}

    elif entity_type == "theme":
        domain_map = get_domain_aliases()
        if norm in domain_map:
            domain_id = domain_map[norm]
            return {"canonical": domain_id, "domain_ids": [domain_id]}

    return None


def _add_to_review_queue(name, candidate_canonical, score, entity_type, source_id):
    """Add merge candidate to review queue."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_name": name,
        "candidate_canonical": candidate_canonical,
        "score": round(score, 4),
        "entity_type": entity_type,
        "source_id": source_id,
        "status": "pending"
    }
    REVIEW_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_QUEUE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    """CLI: test normalization of a single entity."""
    if len(sys.argv) < 3:
        print("Uso: python3 entity_normalizer.py <entity_type> <name>")
        print("  entity_type: person | theme | role | concept")
        print("  name: nome da entidade a normalizar")
        print()
        print("Exemplo: python3 entity_normalizer.py person 'alex hormozi'")
        sys.exit(1)

    entity_type = sys.argv[1]
    name = " ".join(sys.argv[2:])

    result = normalize_entity(name, entity_type, auto_save=False)

    print(f"\n=== ENTITY NORMALIZER ===")
    print(f"Input:      '{name}'")
    print(f"Type:       {entity_type}")
    print(f"Canonical:  '{result['canonical']}'")
    print(f"Match:      {result['match_type']}")
    print(f"Score:      {result['score']:.4f}")
    print(f"Created:    {result['created']}")
    print()


if __name__ == "__main__":
    main()
