#!/usr/bin/env python3
"""
BOOTSTRAP REGISTRY - Intelligence Layer v1.0
==============================================
Popula o ENTITY-REGISTRY.json inicial a partir de TODOS os dados existentes:

1. CANONICAL-MAP.json  -> 17 persons (migra e depreca)
2. DOMAINS-TAXONOMY    -> 12 dominios, 13 cargos, 6 persons
3. Role-Tracking.md    -> contagens historicas de mencoes
4. Dossiers existentes -> 22 themes + 8 persons (has_dossier=True)
5. Agents existentes   -> 14 cargo + 5 person agents (has_agent=True)
6. Theme Analyzer      -> extrai temas dos 92 chunk + 5 insight files

Output: ENTITY-REGISTRY.json pre-populado (~100+ entidades)

ATENCAO: Este script so deve ser rodado UMA VEZ para bootstrap.
Depois, o entity_normalizer.py cuida das atualizacoes incrementais.

Versao: 1.0.0
Data: 2026-02-24
"""

import json
import os
import re
import sys
import yaml
from pathlib import Path
from datetime import datetime, timezone

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from entity_normalizer import (
    create_empty_registry, save_registry, load_taxonomy,
    normalize_text, REGISTRY_PATH
)

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
CANONICAL_MAP_PATH = BASE_DIR / "processing" / "canonical" / "CANONICAL-MAP.json"
TAXONOMY_PATH = BASE_DIR / "knowledge" / "dna" / "DOMAINS-TAXONOMY.yaml"
ROLE_TRACKING_PATH = BASE_DIR / "system" / "backups" / "v3.4.0-pre-refactor" / "05-agents" / "discovery" / "role-tracking.md"
DOSSIERS_PERSONS = BASE_DIR / "knowledge" / "dossiers" / "persons"
DOSSIERS_THEMES = BASE_DIR / "knowledge" / "dossiers" / "themes"
AGENTS_PERSONS = BASE_DIR / "agents" / "persons"
AGENTS_CARGO = BASE_DIR / "agents" / "cargo"

NOW = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# EXISTING AGENTS MAP (hardcoded from filesystem scan)
# ---------------------------------------------------------------------------
EXISTING_PERSON_AGENTS = [
    "alex-hormozi", "cole-gordon", "jeremy-haynes",
    "jeremy-miner", "the-scalable-company"
]

EXISTING_CARGO_AGENTS = [
    "CRO", "CMO", "COO", "CFO",
    "BDR", "CLOSER", "SDS", "LNS",
    "SALES-MANAGER", "SALES-LEAD", "SALES-COORDINATOR",
    "CUSTOMER-SUCCESS", "NEPQ-SPECIALIST", "PAID-MEDIA-SPECIALIST"
]

# Theme dossier filenames -> canonical theme names
EXISTING_THEME_DOSSIERS = {
    "DOSSIER-01-ESTRUTURA-TIME": "estrutura-time-vendas",
    "DOSSIER-02-PROCESSO-VENDAS": "processo-vendas",
    "DOSSIER-03-CONTRATACAO": "contratacao",
    "DOSSIER-04-COMISSIONAMENTO": "comissionamento",
    "DOSSIER-05-METRICAS": "metricas-vendas",
    "DOSSIER-07-PRICING": "pricing-ofertas",
    "DOSSIER-09-GESTAO": "gestao-lideranca",
    "DOSSIER-10-CULTURA-GAMIFICACAO": "cultura-gamificacao",
    "DOSSIER-5-PILARES-PRE-VENDAS": "5-pilares-pre-vendas",
    "DOSSIER-BUSINESS-OPERATING-SYSTEMS": "business-operating-systems",
    "DOSSIER-CALL-FUNNELS": "call-funnels",
    "DOSSIER-CLOSER-FRAMEWORK": "closer-framework",
    "DOSSIER-CRM-AUTOMACAO": "crm-automacao",
    "DOSSIER-FUNIL-RH": "funil-rh",
    "DOSSIER-HIERARQUIA-SDR": "hierarquia-sdr",
    "DOSSIER-HIGH-TICKET-BR": "high-ticket-br",
    "DOSSIER-KLT-FRAMEWORK": "klt-framework",
    "DOSSIER-NEPQ-METHODOLOGY": "nepq-methodology",
    "DOSSIER-OBJECTION-HANDLING": "objection-handling",
    "DOSSIER-PAID-MEDIA-SCALING": "paid-media-scaling",
    "DOSSIER-SDR-OUTBOUND": "sdr-outbound",
    "DOSSIER-SHOW-RATES": "show-rates",
}

EXISTING_PERSON_DOSSIERS = [
    "Alex Hormozi", "Cole Gordon", "Jeremy Haynes", "Jeremy Miner",
    "Jordan Lee", "Richard Linder", "Sam Oven", "The Scalable Company"
]

# Historical role mention counts from role-tracking.md
ROLE_TRACKING_DATA = {
    "BDR": {"mentions": 15, "status": "CRIADO", "sources": ["SS001", "G4001", "FSS001"]},
    "SDS": {"mentions": 20, "status": "CRIADO", "sources": ["SS001", "G4001", "FSS001", "CG004"]},
    "CLOSER": {"mentions": 40, "status": "CRIADO", "sources": ["SS001", "CG003", "G4001", "FSS001", "CG004"]},
    "SALES-MANAGER": {"mentions": 55, "status": "CRIADO", "sources": ["SS001", "CG001", "G4001", "FSS001", "CG004"]},
    "SALES-LEAD": {"mentions": 15, "status": "CRIADO", "sources": ["CG001"]},
    "SALES-COORDINATOR": {"mentions": 10, "status": "CRIADO", "sources": ["CG001", "FSS001"]},
    "LNS": {"mentions": 12, "status": "CRIADO", "sources": ["CG002", "CG003", "FSS001"]},
    "CUSTOMER-SUCCESS": {"mentions": 12, "status": "CRIADO", "sources": ["G4002", "FSS001"]},
    "SETTER": {"mentions": 15, "status": "CRITICO", "sources": ["FSS001", "G4001"]},
    "SALES-FARMING": {"mentions": 10, "status": "CRITICO", "sources": ["FSS001"]},
    "HR-DIRECTOR": {"mentions": 8, "status": "IMPORTANTE", "sources": ["HR001"]},
    "SALES-OPS": {"mentions": 5, "status": "IMPORTANTE", "sources": ["CG002"]},
    "STAR-EMPLOYEE": {"mentions": 5, "status": "IMPORTANTE", "sources": ["HR001"]},
    "CUSTOMER-SERVICE": {"mentions": 3, "status": "RASTREAR", "sources": ["HR001"]},
    "SALES-REP": {"mentions": 2, "status": "RASTREAR", "sources": ["MM001"]},
    "MARKETING-MANAGER": {"mentions": 1, "status": "RASTREAR", "sources": ["MM001"]},
}


# ---------------------------------------------------------------------------
# BOOTSTRAP FUNCTIONS
# ---------------------------------------------------------------------------
def bootstrap_persons(registry):
    """
    Populate persons from CANONICAL-MAP + DOMAINS-TAXONOMY + existing agents/dossiers.
    """
    persons = registry["persons"]

    # 1. Migrate from CANONICAL-MAP.json
    canonical_entries = []
    if CANONICAL_MAP_PATH.exists():
        with open(CANONICAL_MAP_PATH, "r", encoding="utf-8") as f:
            cmap = json.load(f)
        for canonical, aliases_list in cmap.get("canonical_state", {}).get("canonical_map", {}).items():
            alias_names = [a["alias"] for a in aliases_list if a["alias"] != canonical]
            canonical_entries.append((canonical, alias_names))

    for canonical, aliases in canonical_entries:
        key = canonical
        if key not in persons:
            persons[key] = {
                "canonical": canonical,
                "aliases": aliases,
                "mention_count": 0,
                "sources": [],
                "has_agent": False,
                "has_dna": False,
                "has_dossier": False,
                "domains": [],
                "status": "tracking",
                "created_at": NOW,
                "last_seen": NOW,
                "migrated_from": "CANONICAL-MAP.json"
            }

    # 2. Enrich with DOMAINS-TAXONOMY data
    tax = load_taxonomy()
    for pkey, pdata in tax.get("pessoas", {}).items():
        canonical = pkey.replace("-", " ").title()
        # Find matching person
        match = None
        for k in persons:
            if normalize_text(k) == normalize_text(canonical):
                match = k
                break
            if normalize_text(k) == normalize_text(pkey):
                match = k
                break

        if match:
            persons[match]["domains"] = (
                pdata.get("expertise_primaria", []) +
                pdata.get("expertise_secundaria", [])
            )
            if pdata.get("contexto"):
                persons[match]["taxonomy_context"] = pdata["contexto"]
        else:
            persons[canonical] = {
                "canonical": canonical,
                "aliases": [pkey, pkey.upper(), pkey.lower()],
                "mention_count": 0,
                "sources": [],
                "has_agent": False,
                "has_dna": False,
                "has_dossier": False,
                "domains": (
                    pdata.get("expertise_primaria", []) +
                    pdata.get("expertise_secundaria", [])
                ),
                "taxonomy_context": pdata.get("contexto", ""),
                "status": "tracking",
                "created_at": NOW,
                "last_seen": NOW,
                "migrated_from": "DOMAINS-TAXONOMY.yaml"
            }

    # 3. Mark has_agent from existing person agents
    for agent_slug in EXISTING_PERSON_AGENTS:
        canonical = agent_slug.replace("-", " ").title()
        for k in persons:
            if normalize_text(k) == normalize_text(canonical):
                persons[k]["has_agent"] = True
                persons[k]["agent_path"] = f"agents/persons/{agent_slug}/"
                break

    # 4. Mark has_dossier from existing person dossiers
    for person_name in EXISTING_PERSON_DOSSIERS:
        for k in persons:
            if normalize_text(k) == normalize_text(person_name):
                persons[k]["has_dossier"] = True
                slug = person_name.upper().replace(" ", "-")
                persons[k]["dossier_path"] = f"knowledge/dossiers/persons/DOSSIER-{slug}.md"
                break

    return len(persons)


def bootstrap_roles(registry):
    """
    Populate roles from DOMAINS-TAXONOMY + role-tracking data + existing cargo agents.
    """
    roles = registry["roles"]

    # 1. From DOMAINS-TAXONOMY cargos
    tax = load_taxonomy()
    for cargo_key, cargo_data in tax.get("cargos", {}).items():
        canonical = cargo_key.upper()
        roles[canonical] = {
            "canonical": canonical,
            "aliases": [
                cargo_key,
                cargo_key.lower(),
                cargo_key.replace("-", " "),
                cargo_key.replace("-", " ").title(),
            ],
            "mention_count": 0,
            "sources": [],
            "has_agent": False,
            "domain_ids": (
                cargo_data.get("dominios_primarios", []) +
                cargo_data.get("dominios_secundarios", [])
            ),
            "responsibilities": [],
            "pessoa_default": cargo_data.get("pessoa_prioritaria_default", ""),
            "status": "tracking",
            "created_at": NOW,
            "last_seen": NOW,
            "migrated_from": "DOMAINS-TAXONOMY.yaml"
        }

    # 2. Enrich with role-tracking historical data
    for role_key, rt_data in ROLE_TRACKING_DATA.items():
        if role_key in roles:
            roles[role_key]["mention_count"] = rt_data["mentions"]
            roles[role_key]["sources"] = rt_data["sources"]
            roles[role_key]["tracking_status"] = rt_data["status"]
        else:
            # Role from tracking that isn't in taxonomy
            roles[role_key] = {
                "canonical": role_key,
                "aliases": [
                    role_key.lower(),
                    role_key.replace("-", " "),
                    role_key.replace("-", " ").title(),
                ],
                "mention_count": rt_data["mentions"],
                "sources": rt_data["sources"],
                "has_agent": False,
                "domain_ids": [],
                "responsibilities": [],
                "tracking_status": rt_data["status"],
                "status": "tracking",
                "created_at": NOW,
                "last_seen": NOW,
                "migrated_from": "role-tracking.md"
            }

    # 3. Mark has_agent from existing cargo agents
    for agent_key in EXISTING_CARGO_AGENTS:
        canonical = agent_key.upper()
        if canonical in roles:
            roles[canonical]["has_agent"] = True
            # Determine agent path
            slug = agent_key.lower()
            if canonical in ("CRO", "CMO", "COO", "CFO"):
                roles[canonical]["agent_path"] = f"agents/cargo/c-level/{slug}/"
            elif canonical == "PAID-MEDIA-SPECIALIST":
                roles[canonical]["agent_path"] = f"agents/cargo/marketing/{slug}/"
            else:
                roles[canonical]["agent_path"] = f"agents/cargo/sales/{slug}/"

    # 4. Update status based on mention count and agent presence
    for k, role in roles.items():
        mc = role.get("mention_count", 0)
        if role.get("has_agent"):
            role["status"] = "active"
        elif mc >= 10:
            role["status"] = "critical"
        elif mc >= 5:
            role["status"] = "important"
        else:
            role["status"] = "tracking"

    return len(roles)


def bootstrap_themes(registry):
    """
    Populate themes from existing dossiers + DOSSIER_THEME_MAP + theme_analyzer scan.
    """
    themes = registry["themes"]
    domain_aliases = {}

    # Build domain alias map
    tax = load_taxonomy()
    for dom in tax.get("dominios", []):
        did = dom["id"]
        domain_aliases[did] = did
        for a in dom.get("aliases", []):
            domain_aliases[a.lower()] = did

    # 1. From existing theme dossiers
    for dossier_name, canonical in EXISTING_THEME_DOSSIERS.items():
        if canonical not in themes:
            # Infer domain from theme name
            inferred_domains = []
            for word in canonical.split("-"):
                if word in domain_aliases:
                    inferred_domains.append(domain_aliases[word])

            themes[canonical] = {
                "canonical": canonical,
                "aliases": [
                    dossier_name,
                    dossier_name.replace("DOSSIER-", ""),
                    canonical.replace("-", " "),
                    canonical.replace("-", " ").title(),
                ],
                "occurrence_count": 0,
                "sources": [],
                "has_dossier": True,
                "dossier_path": f"knowledge/dossiers/themes/{dossier_name}.md",
                "domain_ids": inferred_domains,
                "related_roles": [],
                "status": "active",
                "created_at": NOW,
                "last_seen": NOW,
                "migrated_from": "filesystem_scan"
            }

    # 2. Map themes to domains more precisely
    theme_domain_map = {
        "estrutura-time-vendas": ["vendas", "scaling"],
        "processo-vendas": ["vendas"],
        "contratacao": ["hiring"],
        "comissionamento": ["compensation"],
        "metricas-vendas": ["operations", "vendas"],
        "pricing-ofertas": ["offers"],
        "gestao-lideranca": ["management"],
        "cultura-gamificacao": ["management"],
        "5-pilares-pre-vendas": ["outbound", "vendas"],
        "business-operating-systems": ["operations", "scaling"],
        "call-funnels": ["marketing", "vendas"],
        "closer-framework": ["vendas"],
        "crm-automacao": ["operations"],
        "funil-rh": ["hiring"],
        "hierarquia-sdr": ["outbound", "vendas"],
        "high-ticket-br": ["vendas", "offers"],
        "klt-framework": ["marketing", "vendas"],
        "nepq-methodology": ["vendas"],
        "objection-handling": ["vendas"],
        "paid-media-scaling": ["marketing"],
        "sdr-outbound": ["outbound"],
        "show-rates": ["vendas", "operations"],
    }

    for canonical, domains in theme_domain_map.items():
        if canonical in themes:
            themes[canonical]["domain_ids"] = domains

    # 3. Map related roles to themes
    theme_role_map = {
        "estrutura-time-vendas": ["SALES-MANAGER", "SALES-LEAD", "BDR", "SDS", "CLOSER"],
        "processo-vendas": ["CLOSER", "SDS", "BDR"],
        "contratacao": ["HR-DIRECTOR", "SALES-MANAGER"],
        "comissionamento": ["SALES-MANAGER", "CFO"],
        "metricas-vendas": ["CRO", "SALES-MANAGER"],
        "pricing-ofertas": ["CRO", "CMO"],
        "gestao-lideranca": ["SALES-MANAGER", "SALES-LEAD", "COO"],
        "closer-framework": ["CLOSER"],
        "hierarquia-sdr": ["BDR", "SDS", "SALES-COORDINATOR"],
        "nepq-methodology": ["CLOSER", "NEPQ-SPECIALIST"],
        "objection-handling": ["CLOSER", "SDS"],
        "sdr-outbound": ["BDR", "SDS"],
        "show-rates": ["LNS", "SALES-COORDINATOR"],
    }

    for canonical, related_roles in theme_role_map.items():
        if canonical in themes:
            themes[canonical]["related_roles"] = related_roles

    return len(themes)


def bootstrap_concepts(registry):
    """
    Seed a few known high-level concepts from the DNA layers.
    These will be expanded by theme_analyzer during processing.
    """
    concepts = registry["concepts"]

    seed_concepts = [
        # L1 - FILOSOFIAS
        {"name": "Help vs Manipulation", "layer": "L1", "domain": "mindset"},
        {"name": "Conviction Selling", "layer": "L1", "domain": "vendas"},
        {"name": "Volume Creates Quality", "layer": "L1", "domain": "vendas"},
        # L2 - MODELOS MENTAIS
        {"name": "Value Equation", "layer": "L2", "domain": "offers"},
        {"name": "Three Buckets", "layer": "L2", "domain": "vendas"},
        {"name": "Heaven Island Hell Island", "layer": "L2", "domain": "vendas"},
        # L3 - HEURISTICAS
        {"name": "100 Calls Per Day", "layer": "L3", "domain": "outbound"},
        {"name": "80/20 Rule", "layer": "L3", "domain": "scaling"},
        # L4 - FRAMEWORKS
        {"name": "CLOSER Framework", "layer": "L4", "domain": "vendas"},
        {"name": "NEPQ", "layer": "L4", "domain": "vendas"},
        {"name": "SPIN Selling", "layer": "L4", "domain": "vendas"},
        {"name": "MEDDIC", "layer": "L4", "domain": "vendas"},
        {"name": "Belief Ladder", "layer": "L4", "domain": "vendas"},
        {"name": "Bridge Framework", "layer": "L4", "domain": "offers"},
        {"name": "Purple Ocean", "layer": "L4", "domain": "marketing"},
        # L5 - METODOLOGIAS
        {"name": "4 Pillars of Closing", "layer": "L5", "domain": "vendas"},
        {"name": "7 Beliefs Framework", "layer": "L5", "domain": "vendas"},
        {"name": "Christmas Tree Outbound", "layer": "L5", "domain": "outbound"},
    ]

    for concept in seed_concepts:
        key = concept["name"]
        if key not in concepts:
            concepts[key] = {
                "canonical": key,
                "aliases": [key.lower(), key.replace(" ", "-").lower()],
                "occurrence_count": 0,
                "sources": [],
                "layer": concept["layer"],
                "domain_ids": [concept["domain"]],
                "status": "seed",
                "created_at": NOW,
                "last_seen": NOW,
                "migrated_from": "bootstrap_seed"
            }

    return len(concepts)


# ---------------------------------------------------------------------------
# MAIN BOOTSTRAP
# ---------------------------------------------------------------------------
def run_bootstrap(dry_run=False):
    """
    Execute full bootstrap. Creates ENTITY-REGISTRY.json from scratch.
    """
    print("\n" + "=" * 60)
    print("  BOOTSTRAP REGISTRY - Intelligence Layer v1.0")
    print("=" * 60)

    # Safety check
    if REGISTRY_PATH.exists() and not dry_run:
        print(f"\n[WARNING] ENTITY-REGISTRY.json already exists!")
        print(f"  Path: {REGISTRY_PATH}")
        print(f"  Use --force to overwrite or --dry-run to preview.")
        if "--force" not in sys.argv:
            print("\nAborted. Use --force to overwrite.")
            sys.exit(1)

    registry = create_empty_registry()

    # Step 1: Persons
    print("\n--- Step 1: Bootstrapping PERSONS ---")
    n_persons = bootstrap_persons(registry)
    print(f"  Persons loaded: {n_persons}")
    for k, v in registry["persons"].items():
        agent = "[AGENT]" if v.get("has_agent") else "       "
        dossier = "[DOSSIER]" if v.get("has_dossier") else "         "
        print(f"    {agent} {dossier} {k}")

    # Step 2: Roles
    print("\n--- Step 2: Bootstrapping ROLES ---")
    n_roles = bootstrap_roles(registry)
    print(f"  Roles loaded: {n_roles}")
    for k, v in sorted(registry["roles"].items(), key=lambda x: -x[1].get("mention_count", 0)):
        agent = "[AGENT]" if v.get("has_agent") else "       "
        mc = v.get("mention_count", 0)
        status = v.get("status", "?")
        print(f"    {agent} {mc:4d} mentions  [{status:>9s}]  {k}")

    # Step 3: Themes
    print("\n--- Step 3: Bootstrapping THEMES ---")
    n_themes = bootstrap_themes(registry)
    print(f"  Themes loaded: {n_themes}")
    for k, v in registry["themes"].items():
        dossier = "[DOSSIER]" if v.get("has_dossier") else "         "
        domains = ", ".join(v.get("domain_ids", []))
        print(f"    {dossier} {k:<35s} [{domains}]")

    # Step 4: Concepts
    print("\n--- Step 4: Seeding CONCEPTS ---")
    n_concepts = bootstrap_concepts(registry)
    print(f"  Concepts seeded: {n_concepts}")

    # Summary
    print("\n" + "=" * 60)
    print("  BOOTSTRAP SUMMARY")
    print("=" * 60)
    print(f"  Persons:  {n_persons}")
    print(f"  Roles:    {n_roles}")
    print(f"  Themes:   {n_themes}")
    print(f"  Concepts: {n_concepts}")
    print(f"  TOTAL:    {n_persons + n_roles + n_themes + n_concepts}")
    print("=" * 60)

    if dry_run:
        print("\n[DRY RUN] No files written.")
        print(json.dumps(registry, indent=2, ensure_ascii=False)[:3000] + "\n...")
    else:
        save_registry(registry)
        print(f"\n[SAVED] {REGISTRY_PATH}")
        print(f"  Size: {REGISTRY_PATH.stat().st_size:,} bytes")
        print(f"  Version: {registry['metadata']['version']}")

    return registry


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Uso: python3 bootstrap_registry.py [--dry-run] [--force]")
        print()
        print("  --dry-run   Preview sem salvar")
        print("  --force     Sobrescrever ENTITY-REGISTRY.json existente")
        sys.exit(0)

    dry_run = "--dry-run" in sys.argv
    run_bootstrap(dry_run=dry_run)


if __name__ == "__main__":
    main()
