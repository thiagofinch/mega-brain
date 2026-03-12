#!/usr/bin/env python3
"""
QUERY ANALYZER - Smart Context Assembly (Phase 1.1)
====================================================
Analyzes a query BEFORE loading agents. Maps question → domains → agents.
Uses DOMAINS-TAXONOMY.yaml (18 domains with aliases) and entity_normalizer
for fuzzy matching.

Zero external deps (stdlib + PyYAML only).

Usage:
    python3 core/intelligence/query_analyzer.py "Devo mudar comissao do closer?"
    # Returns: domains=["compensation","vendas"], agents=["CRO","CFO","CLOSER"]

Versao: 1.0.0
Data: 2026-03-01
"""

import json
import re
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # mega-brain/
TAXONOMY_PATH = BASE_DIR / "knowledge" / "external" / "dna" / "DOMAINS-TAXONOMY.yaml"
AGENTS_DIR = BASE_DIR / "agents"
CARGO_DIR = AGENTS_DIR / "cargo"
MINDS_DIR = AGENTS_DIR / "minds"

# ---------------------------------------------------------------------------
# TAXONOMY CACHE
# ---------------------------------------------------------------------------
_taxonomy_cache: dict | None = None


def load_taxonomy() -> dict:
    """Load DOMAINS-TAXONOMY.yaml with caching."""
    global _taxonomy_cache
    if _taxonomy_cache is not None:
        return _taxonomy_cache
    if TAXONOMY_PATH.exists():
        with open(TAXONOMY_PATH, encoding="utf-8") as f:
            _taxonomy_cache = yaml.safe_load(f) or {}
    else:
        _taxonomy_cache = {}
    return _taxonomy_cache


def _build_domain_keyword_map() -> dict[str, str]:
    """Build flat map: keyword/alias/subdominio → domain_id."""
    tax = load_taxonomy()
    kw_map: dict[str, str] = {}
    for dom in tax.get("dominios", []):
        did = dom["id"]
        kw_map[did.lower()] = did
        for alias in dom.get("aliases", []):
            kw_map[alias.lower()] = did
        for sub in dom.get("subdominios", []):
            kw_map[sub.lower()] = did
    return kw_map


def _build_cargo_domain_map() -> dict[str, dict]:
    """Build map: CARGO_NAME → {dominios_primarios, dominios_secundarios, ...}."""
    tax = load_taxonomy()
    return {k.upper(): v for k, v in tax.get("cargos", {}).items()}


def _build_person_domain_map() -> dict[str, dict]:
    """Build map: PERSON_NAME → {expertise_primaria, expertise_secundaria, ...}."""
    tax = load_taxonomy()
    return {k.upper(): v for k, v in tax.get("pessoas", {}).items()}


# ---------------------------------------------------------------------------
# AGENT DISCOVERY
# ---------------------------------------------------------------------------
_agent_path_cache: dict[str, Path] | None = None


def discover_agents() -> dict[str, Path]:
    """Discover all cargo agent directories. Returns {AGENT_NAME: path}."""
    global _agent_path_cache
    if _agent_path_cache is not None:
        return _agent_path_cache

    agents: dict[str, Path] = {}

    # Scan cargo agents (e.g. agents/cargo/sales/closer/)
    if CARGO_DIR.exists():
        for category in CARGO_DIR.iterdir():
            if not category.is_dir() or category.name.startswith(("_", ".")):
                continue
            for agent_dir in category.iterdir():
                if not agent_dir.is_dir() or agent_dir.name.startswith(("_", ".")):
                    continue
                agent_md = agent_dir / "AGENT.md"
                if agent_md.exists():
                    name = agent_dir.name.upper().replace("-", "_")
                    # Normalize common variations
                    name_map = {
                        "CLOSER": "CLOSER",
                        "BDR": "BDR",
                        "SDS": "SDS",
                        "LNS": "LNS",
                        "CRO": "CRO",
                        "CFO": "CFO",
                        "CMO": "CMO",
                        "COO": "COO",
                        "SALES_MANAGER": "SALES-MANAGER",
                        "SALES_LEAD": "SALES-LEAD",
                        "SALES_COORDINATOR": "SALES-COORDINATOR",
                        "CUSTOMER_SUCCESS": "CUSTOMER-SUCCESS",
                        "HR_DIRECTOR": "HR-DIRECTOR",
                        "NEPQ_SPECIALIST": "NEPQ-SPECIALIST",
                        "PAID_MEDIA_SPECIALIST": "PAID-MEDIA-SPECIALIST",
                    }
                    canonical = name_map.get(name, agent_dir.name.upper())
                    agents[canonical] = agent_dir

    _agent_path_cache = agents
    return agents


def _cargo_name_to_taxonomy_key(cargo_name: str) -> str:
    """Convert agent dir name to taxonomy key format (e.g. closer → CLOSER)."""
    return cargo_name.upper().replace("_", "-")


# ---------------------------------------------------------------------------
# QUERY ANALYSIS
# ---------------------------------------------------------------------------
def tokenize_query(query: str) -> list[str]:
    """Tokenize query into lowercase words and common n-grams."""
    query_lower = query.lower()
    # Remove punctuation except hyphens
    clean = re.sub(r"[^\w\s-]", " ", query_lower)
    words = clean.split()

    # Generate bigrams for compound terms
    tokens = list(words)
    for i in range(len(words) - 1):
        tokens.append(f"{words[i]}-{words[i+1]}")
        tokens.append(f"{words[i]} {words[i+1]}")

    return tokens


def detect_domains(query: str) -> list[tuple[str, float]]:
    """
    Detect domains relevant to the query.

    Returns list of (domain_id, relevance_score) sorted by score desc.
    Score: 1.0 = exact keyword match, 0.7 = alias match, 0.5 = subdomain match.
    """
    kw_map = _build_domain_keyword_map()
    tokens = tokenize_query(query)

    domain_scores: dict[str, float] = {}

    for token in tokens:
        token_clean = token.strip().lower()
        if token_clean in kw_map:
            domain_id = kw_map[token_clean]
            # Score based on match type (domain id = 1.0, alias/sub = 0.8)
            tax = load_taxonomy()
            domain_ids = {d["id"] for d in tax.get("dominios", [])}
            score = 1.0 if token_clean in domain_ids else 0.8
            domain_scores[domain_id] = max(domain_scores.get(domain_id, 0), score)

    # Sort by score descending
    return sorted(domain_scores.items(), key=lambda x: -x[1])


def detect_agents_mentioned(query: str) -> list[str]:
    """Detect agent names explicitly mentioned in the query."""
    query_lower = query.lower()
    mentioned = []

    # Check common agent references
    agent_patterns = {
        "CLOSER": [r"\bcloser\b", r"\bfechador\b"],
        "CRO": [r"\bcro\b", r"\bchief revenue\b"],
        "CFO": [r"\bcfo\b", r"\bchief financial\b", r"\bfinanceiro\b"],
        "CMO": [r"\bcmo\b", r"\bchief marketing\b"],
        "COO": [r"\bcoo\b", r"\bchief operations\b", r"\boperacoes\b"],
        "SALES-MANAGER": [r"\bsales.?manager\b", r"\bgerente.?de.?vendas\b"],
        "BDR": [r"\bbdr\b", r"\bbusiness.?development\b"],
        "SDS": [r"\bsds\b", r"\bsales.?development\b"],
        "HR-DIRECTOR": [r"\bhr\b", r"\brecursos.?humanos\b", r"\brh\b"],
    }

    for agent, patterns in agent_patterns.items():
        for pat in patterns:
            if re.search(pat, query_lower):
                if agent not in mentioned:
                    mentioned.append(agent)
                break

    return mentioned


def select_agents_for_domains(
    domains: list[tuple[str, float]],
    mentioned_agents: list[str],
    max_agents: int = 5,
) -> list[tuple[str, float, str]]:
    """
    Select relevant agents based on detected domains.

    Returns list of (agent_name, relevance_score, reason) sorted by score desc.
    """
    cargo_map = _build_cargo_domain_map()
    available_agents = discover_agents()

    agent_scores: dict[str, tuple[float, str]] = {}

    # Explicitly mentioned agents get highest priority
    for agent in mentioned_agents:
        if agent in available_agents or agent in cargo_map:
            agent_scores[agent] = (1.0, "explicitly mentioned")

    # Score agents by domain overlap
    domain_ids = {d: s for d, s in domains}
    for cargo_name, cargo_data in cargo_map.items():
        # Check if agent actually exists on disk
        if cargo_name not in available_agents:
            continue

        score = 0.0
        reasons = []

        for dom in cargo_data.get("dominios_primarios", []):
            if dom in domain_ids:
                score += 0.6 * domain_ids[dom]
                reasons.append(f"primary:{dom}")

        for dom in cargo_data.get("dominios_secundarios", []):
            if dom in domain_ids:
                score += 0.3 * domain_ids[dom]
                reasons.append(f"secondary:{dom}")

        if score > 0:
            reason = ", ".join(reasons[:3])
            existing = agent_scores.get(cargo_name, (0, ""))
            if score > existing[0]:
                agent_scores[cargo_name] = (score, reason)

    # Sort and limit
    sorted_agents = sorted(agent_scores.items(), key=lambda x: -x[1][0])
    return [
        (name, score, reason)
        for name, (score, reason) in sorted_agents[:max_agents]
    ]


# ---------------------------------------------------------------------------
# MAIN ANALYSIS FUNCTION
# ---------------------------------------------------------------------------
def analyze_query(query: str, max_agents: int = 5) -> dict:
    """
    Full query analysis pipeline.

    Args:
        query: The question/decision to analyze
        max_agents: Maximum number of agents to recommend

    Returns:
        {
            "query": str,
            "domains": [{"id": str, "score": float}],
            "mentioned_agents": [str],
            "recommended_agents": [{"name": str, "score": float, "reason": str, "path": str}],
            "context_budget_kb": int
        }
    """
    domains = detect_domains(query)
    mentioned = detect_agents_mentioned(query)
    agents = select_agents_for_domains(domains, mentioned, max_agents)
    available = discover_agents()

    # Calculate context budget: ~30KB per agent for trimmed context
    budget_kb = len(agents) * 30

    return {
        "query": query,
        "domains": [{"id": d, "score": round(s, 2)} for d, s in domains],
        "mentioned_agents": mentioned,
        "recommended_agents": [
            {
                "name": name,
                "score": round(score, 2),
                "reason": reason,
                "path": str(available.get(name, "")),
            }
            for name, score, reason in agents
        ],
        "context_budget_kb": budget_kb,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 query_analyzer.py \"<query>\"")
        print("Example: python3 query_analyzer.py \"Devo mudar comissao do closer?\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    result = analyze_query(query)

    print(f"\n{'='*70}")
    print("QUERY ANALYSIS")
    print(f"{'='*70}")
    print(f"Query: {result['query']}")
    print("\nDomains detected:")
    for d in result["domains"]:
        print(f"  - {d['id']} (score: {d['score']})")

    print(f"\nMentioned agents: {result['mentioned_agents'] or 'none'}")

    print("\nRecommended agents:")
    for a in result["recommended_agents"]:
        print(f"  - {a['name']} (score: {a['score']}, reason: {a['reason']})")

    print(f"\nContext budget: ~{result['context_budget_kb']}KB")
    print(f"{'='*70}\n")

    # Also output JSON for piping
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
