#!/usr/bin/env python3
"""
THEME ANALYZER - Intelligence Layer v1.0
==========================================
Extrai e normaliza temas de TODOS os formatos de chunk e insight do Mega Brain.

Formatos suportados:
- AH-BP001: key_concepts[], section, framework_name
- CG-SM001: temas[], pessoas[], meta.speaker
- RAG migrated: metadata.theme, topic_hint, mentions[]
- SS001 legacy: topic, entities[], keywords[]
- Insights: themes[], type (METRIC/FRAMEWORK/PRINCIPLE/TACTIC)

Para cada tema extraido:
1. Normaliza via entity_normalizer
2. Atualiza occurrence_count no ENTITY-REGISTRY
3. Mapeia tema -> dominio via DOMAINS-TAXONOMY
4. Detecta roles mencionados e associa ao tema

Output: {themes_found, themes_new, roles_mentioned, domains_touched, persons_found}

Versao: 1.0.0
Data: 2026-02-24
"""

import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from entity_normalizer import (
    load_registry, save_registry, normalize_entity,
    normalize_text, get_domain_aliases, load_taxonomy
)

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
CHUNKS_DIR = BASE_DIR / "processing" / "chunks"
INSIGHTS_DIR = BASE_DIR / "processing" / "insights"

# ---------------------------------------------------------------------------
# DOSSIER THEME ID MAP
# ---------------------------------------------------------------------------
# Maps known dossier theme IDs (used in CG-SM001 format) to readable names
DOSSIER_THEME_MAP = {
    "01-ESTRUTURA-TIME": "estrutura-time-vendas",
    "02-PROCESSO-VENDAS": "processo-vendas",
    "03-OUTBOUND": "outbound",
    "04-COMISSIONAMENTO": "comissionamento",
    "05-METRICAS": "metricas-vendas",
    "06-FUNIL-APLICACAO": "funil-aplicacao",
    "07-PRICING": "pricing-ofertas",
    "08-HIRING": "hiring-contratacao",
    "09-GESTAO": "gestao-lideranca",
    "10-CULTURA": "cultura-organizacional",
    "11-SCRIPTS-VENDAS": "scripts-vendas",
    "12-OBJECOES": "objecoes",
    "13-FOLLOW-UP": "follow-up",
    "14-SHOW-RATES": "show-rates",
    "15-CALL-FUNNELS": "call-funnels",
    "16-ONBOARDING": "onboarding",
    "17-CUSTOMER-SUCCESS": "customer-success",
    "18-REFERRAL": "referral",
    "19-RETENTION": "retention",
    "20-SCALING": "scaling-operacoes",
    "21-MINDSET": "mindset",
    "22-OFERTAS": "ofertas",
}


# ---------------------------------------------------------------------------
# CHUNK PROCESSORS (one per format)
# ---------------------------------------------------------------------------
def process_ah_format(chunk, source_id):
    """
    Process AH-BP001 format chunks.
    Fields: key_concepts[], section, type, framework_name, content
    """
    themes = []
    roles = []
    persons = []

    # Extract from key_concepts
    for concept in chunk.get("key_concepts", []):
        themes.append(concept)

    # framework_name is a strong theme signal
    fw = chunk.get("framework_name")
    if fw:
        themes.append(fw)

    # section can hint at theme
    section = chunk.get("section", "")
    if section and section not in ("START HERE",):
        themes.append(section)

    return {"themes": themes, "roles": roles, "persons": persons}


def process_cg_format(chunk, source_id):
    """
    Process CG-SM001 format chunks.
    Fields: temas[], pessoas[], meta.speaker, texto
    """
    themes = []
    roles = []
    persons = []

    # temas already mapped to dossier IDs
    for tema_id in chunk.get("temas", []):
        readable = DOSSIER_THEME_MAP.get(tema_id, tema_id)
        themes.append(readable)

    # pessoas explicitly listed
    for pessoa in chunk.get("pessoas", []):
        persons.append(pessoa)

    # Speaker from meta
    meta = chunk.get("meta", {})
    speaker = meta.get("speaker")
    if speaker:
        persons.append(speaker)

    return {"themes": themes, "roles": roles, "persons": persons}


def process_rag_format(chunk, source_id):
    """
    Process RAG-migrated format chunks.
    Fields: metadata.theme, topic_hint, text, mentions[]
    """
    themes = []
    roles = []
    persons = []

    meta = chunk.get("metadata", {})
    theme = meta.get("theme")
    if theme:
        readable = DOSSIER_THEME_MAP.get(theme, theme)
        themes.append(readable)

    topic = chunk.get("topic_hint", "")
    if topic and not topic.startswith("#"):
        themes.append(topic)

    for mention in chunk.get("mentions", []):
        persons.append(mention)

    return {"themes": themes, "roles": roles, "persons": persons}


def process_ss_format(chunk, source_id):
    """
    Process SS001 legacy format (individual chunk files).
    Fields: topic, entities[], keywords[], content, speaker
    """
    themes = []
    roles = []
    persons = []

    topic = chunk.get("topic", "")
    if topic:
        # Convert SCREAMING_SNAKE to readable
        readable = topic.lower().replace("_", " ").strip()
        if readable and readable not in ("intro context",):
            themes.append(readable)

    for entity in chunk.get("entities", []):
        persons.append(entity)

    for kw in chunk.get("keywords", []):
        themes.append(kw)

    speaker = chunk.get("speaker", "")
    if speaker:
        persons.append(speaker.replace("_", " ").title())

    return {"themes": themes, "roles": roles, "persons": persons}


def process_insight(insight, source_id):
    """
    Process insight format.
    Fields: themes[], type, insight text, source.speaker
    """
    themes = []
    roles = []
    persons = []

    for theme_id in insight.get("themes", []):
        readable = DOSSIER_THEME_MAP.get(theme_id, theme_id)
        themes.append(readable)

    # The insight text itself may contain framework names
    insight_text = insight.get("insight", "")
    itype = insight.get("type", "")
    if itype in ("FRAMEWORK", "METHODOLOGY") and insight_text:
        # Extract framework name (usually before the colon)
        match = re.match(r"^([^:]+):", insight_text)
        if match:
            themes.append(match.group(1).strip())

    speaker = insight.get("source", {}).get("speaker")
    if speaker:
        persons.append(speaker)

    return {"themes": themes, "roles": roles, "persons": persons}


# ---------------------------------------------------------------------------
# FORMAT DETECTOR
# ---------------------------------------------------------------------------
def detect_chunk_format(chunk):
    """Detect which format a chunk uses."""
    if "key_concepts" in chunk and "section" in chunk:
        return "ah"
    if "temas" in chunk and "meta" in chunk:
        return "cg"
    if "metadata" in chunk and "migrated_from_rag" in chunk.get("metadata", {}):
        return "rag"
    if "metadata" in chunk and "theme" in chunk.get("metadata", {}):
        return "rag"
    if "topic" in chunk and "entities" in chunk:
        return "ss"
    if "key_concepts" in chunk:
        return "ah"
    if "temas" in chunk:
        return "cg"
    return "unknown"


FORMAT_PROCESSORS = {
    "ah": process_ah_format,
    "cg": process_cg_format,
    "rag": process_rag_format,
    "ss": process_ss_format,
}


# ---------------------------------------------------------------------------
# CORE: ANALYZE FILE
# ---------------------------------------------------------------------------
def analyze_chunk_file(filepath, registry=None):
    """
    Analyze a single chunk file. Extracts themes, persons, roles.

    Args:
        filepath: path to chunk .json file
        registry: shared ENTITY-REGISTRY dict

    Returns:
        {
            "source_id": str,
            "themes_found": [str],
            "themes_new": [str],
            "roles_mentioned": [str],
            "persons_found": [str],
            "domains_touched": [str],
            "chunk_count": int,
            "format": str
        }
    """
    if registry is None:
        registry = load_registry()

    filepath = Path(filepath)
    if not filepath.exists():
        return {"error": f"File not found: {filepath}"}

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_id = data.get("source_id", data.get("source_hash", filepath.stem))

    # Handle both consolidated files (with "chunks" array) and individual chunk files
    if "chunks" in data:
        chunks = data["chunks"]
    elif "insights" in data:
        # Insight files
        return _analyze_insights_file(data, source_id, registry)
    else:
        # Individual chunk file (SS001 format)
        chunks = [data]

    all_themes = []
    all_persons = []
    all_roles = []
    detected_format = "unknown"

    for chunk in chunks:
        fmt = detect_chunk_format(chunk)
        if fmt == "unknown":
            continue
        detected_format = fmt

        processor = FORMAT_PROCESSORS[fmt]
        result = processor(chunk, source_id)

        all_themes.extend(result["themes"])
        all_persons.extend(result["persons"])
        all_roles.extend(result["roles"])

    # Normalize and deduplicate
    return _normalize_and_compile(
        all_themes, all_persons, all_roles,
        source_id, len(chunks), detected_format, registry
    )


def _analyze_insights_file(data, source_id, registry):
    """Analyze an insights file."""
    all_themes = []
    all_persons = []
    all_roles = []

    for insight in data.get("insights", []):
        result = process_insight(insight, source_id)
        all_themes.extend(result["themes"])
        all_persons.extend(result["persons"])
        all_roles.extend(result["roles"])

    count = data.get("insights_extracted", len(data.get("insights", [])))
    return _normalize_and_compile(
        all_themes, all_persons, all_roles,
        source_id, count, "insight", registry
    )


def _normalize_and_compile(all_themes, all_persons, all_roles,
                           source_id, chunk_count, detected_format, registry):
    """Normalize extracted data and compile results."""
    domain_aliases = get_domain_aliases()

    # Normalize themes
    themes_found = []
    themes_new = []
    domains_touched = set()

    seen_themes = set()
    for raw_theme in all_themes:
        norm = normalize_text(raw_theme)
        if not norm or len(norm) < 2 or norm in seen_themes:
            continue
        seen_themes.add(norm)

        result = normalize_entity(
            raw_theme, "theme", registry=registry,
            source_id=source_id, auto_save=False
        )
        themes_found.append(result["canonical"])
        if result["created"]:
            themes_new.append(result["canonical"])

        # Map to domain
        if norm in domain_aliases:
            domains_touched.add(domain_aliases[norm])
        # Also check entity data for domain_ids
        theme_data = registry.get("themes", {}).get(result["canonical"], {})
        for did in theme_data.get("domain_ids", []):
            domains_touched.add(did)

    # Normalize persons
    persons_found = []
    seen_persons = set()
    for raw_person in all_persons:
        norm = normalize_text(raw_person)
        if not norm or len(norm) < 2 or norm in seen_persons:
            continue
        seen_persons.add(norm)

        result = normalize_entity(
            raw_person, "person", registry=registry,
            source_id=source_id, auto_save=False
        )
        persons_found.append(result["canonical"])

    # Normalize roles
    roles_mentioned = []
    seen_roles = set()
    for raw_role in all_roles:
        norm = normalize_text(raw_role)
        if not norm or len(norm) < 2 or norm in seen_roles:
            continue
        seen_roles.add(norm)

        result = normalize_entity(
            raw_role, "role", registry=registry,
            source_id=source_id, auto_save=False
        )
        roles_mentioned.append(result["canonical"])

    # Deduplicate
    themes_found = list(dict.fromkeys(themes_found))
    themes_new = list(dict.fromkeys(themes_new))
    persons_found = list(dict.fromkeys(persons_found))
    roles_mentioned = list(dict.fromkeys(roles_mentioned))

    return {
        "source_id": source_id,
        "themes_found": themes_found,
        "themes_new": themes_new,
        "roles_mentioned": roles_mentioned,
        "persons_found": persons_found,
        "domains_touched": sorted(domains_touched),
        "chunk_count": chunk_count,
        "format": detected_format,
    }


# ---------------------------------------------------------------------------
# ANALYZE ALL CHUNKS
# ---------------------------------------------------------------------------
def analyze_all_chunks(registry=None, save=True):
    """
    Analyze ALL chunk and insight files.

    Returns:
        {
            "total_files": int,
            "total_chunks": int,
            "all_themes": Counter,
            "all_persons": Counter,
            "all_roles": Counter,
            "all_domains": Counter,
            "new_themes": [str],
            "files_processed": [dict]
        }
    """
    if registry is None:
        registry = load_registry()

    all_themes = Counter()
    all_persons = Counter()
    all_roles = Counter()
    all_domains = Counter()
    new_themes = []
    files_processed = []
    total_chunks = 0

    # Process chunk files
    chunk_files = sorted(CHUNKS_DIR.glob("*.json"))
    for fpath in chunk_files:
        # Skip state/index files
        if fpath.name in ("CHUNKS-STATE.json", "_INDEX.json", "_rag_export.json"):
            continue

        result = analyze_chunk_file(fpath, registry=registry)
        if "error" in result:
            continue

        files_processed.append({
            "file": fpath.name,
            "source_id": result["source_id"],
            "format": result["format"],
            "themes": len(result["themes_found"]),
            "new_themes": len(result["themes_new"]),
        })

        for t in result["themes_found"]:
            all_themes[t] += 1
        for p in result["persons_found"]:
            all_persons[p] += 1
        for r in result["roles_mentioned"]:
            all_roles[r] += 1
        for d in result["domains_touched"]:
            all_domains[d] += 1
        new_themes.extend(result["themes_new"])
        total_chunks += result["chunk_count"]

    # Process insight files
    insight_files = sorted(INSIGHTS_DIR.glob("*.json"))
    for fpath in insight_files:
        if fpath.name == "INSIGHTS-STATE.json":
            continue

        result = analyze_chunk_file(fpath, registry=registry)
        if "error" in result:
            continue

        files_processed.append({
            "file": fpath.name,
            "source_id": result["source_id"],
            "format": result["format"],
            "themes": len(result["themes_found"]),
            "new_themes": len(result["themes_new"]),
        })

        for t in result["themes_found"]:
            all_themes[t] += 1
        for p in result["persons_found"]:
            all_persons[p] += 1
        for r in result["roles_mentioned"]:
            all_roles[r] += 1
        for d in result["domains_touched"]:
            all_domains[d] += 1
        new_themes.extend(result["themes_new"])

    if save:
        save_registry(registry)

    return {
        "total_files": len(files_processed),
        "total_chunks": total_chunks,
        "all_themes": all_themes,
        "all_persons": all_persons,
        "all_roles": all_roles,
        "all_domains": all_domains,
        "new_themes": list(set(new_themes)),
        "files_processed": files_processed,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    """CLI: analyze chunk/insight files."""
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        print("\n=== THEME ANALYZER: Full Scan ===\n")
        result = analyze_all_chunks(save=True)
        print(f"Files processed: {result['total_files']}")
        print(f"Total chunks:    {result['total_chunks']}")
        print(f"Themes found:    {len(result['all_themes'])}")
        print(f"New themes:      {len(result['new_themes'])}")
        print(f"Persons found:   {len(result['all_persons'])}")
        print(f"Roles found:     {len(result['all_roles'])}")
        print(f"Domains touched: {len(result['all_domains'])}")

        print(f"\n--- Top 20 Themes ---")
        for theme, count in result["all_themes"].most_common(20):
            print(f"  {count:4d}x  {theme}")

        print(f"\n--- Top 10 Persons ---")
        for person, count in result["all_persons"].most_common(10):
            print(f"  {count:4d}x  {person}")

        print(f"\n--- Domains ---")
        for dom, count in result["all_domains"].most_common():
            print(f"  {count:4d}x  {dom}")

    elif len(sys.argv) > 1:
        filepath = sys.argv[1]
        print(f"\n=== THEME ANALYZER: Single File ===\n")
        result = analyze_chunk_file(filepath)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print("Uso:")
        print("  python3 theme_analyzer.py --all          # Analyze all chunks + insights")
        print("  python3 theme_analyzer.py <filepath>     # Analyze single file")
        sys.exit(1)


if __name__ == "__main__":
    main()
