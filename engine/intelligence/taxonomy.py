"""taxonomy.py — Helper for DOMAINS-TAXONOMY.yaml (Story MCE-3.8).

Provides 3 functions for the canonical domain taxonomy:
  - load_taxonomy() -> dict
  - resolve_domain(text) -> str | None
  - list_domains() -> list[str]

Plus 2 convenience helpers for cargos and pessoas mapping.

Reference: ~/Desktop/Mega Brain/02-KNOWLEDGE/DNA/DOMAINS-TAXONOMY.yaml (v1.0.0)
Current: knowledge/external/dna/_taxonomy/DOMAINS-TAXONOMY.yaml (v2.0.0)
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import yaml

logger = logging.getLogger("intelligence.taxonomy")

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_PATH = (
    _PROJECT_ROOT / "knowledge" / "external" / "dna" / "_taxonomy" / "DOMAINS-TAXONOMY.yaml"
)


@lru_cache(maxsize=1)
def load_taxonomy() -> dict:
    """Load DOMAINS-TAXONOMY.yaml. Cached for the lifetime of the process.

    Returns:
        dict with keys: versao, dominios[], cargos{}, pessoas{}, regras{}
        Empty taxonomy if file missing (defensive — never raises).
    """
    if not TAXONOMY_PATH.exists():
        logger.warning("DOMAINS-TAXONOMY.yaml not found at %s", TAXONOMY_PATH)
        return {"versao": "0.0.0", "dominios": [], "cargos": {}, "pessoas": {}, "regras": {}}

    try:
        data = yaml.safe_load(TAXONOMY_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            logger.error("DOMAINS-TAXONOMY.yaml root is not a dict")
            return {"versao": "0.0.0", "dominios": []}
        return data
    except (yaml.YAMLError, OSError) as exc:
        logger.error("Failed to load DOMAINS-TAXONOMY.yaml: %s", exc)
        return {"versao": "0.0.0", "dominios": []}


def list_domains() -> list[str]:
    """Return canonical domain ids in declaration order.

    Returns:
        List of domain ids (e.g. ["vendas", "outbound", ...]).
    """
    tax = load_taxonomy()
    return [d.get("id", "") for d in tax.get("dominios", []) if isinstance(d, dict) and d.get("id")]


def resolve_domain(text: str) -> str | None:
    """Resolve a free-text domain reference to a canonical domain id.

    Matches by exact id, exact alias (case-insensitive), or normalized text.
    Returns the canonical id if found, else None.

    Args:
        text: Free-form text that might be a domain name or alias.

    Returns:
        Canonical domain id (e.g. "vendas") or None if no match.
    """
    if not text or not isinstance(text, str):
        return None

    needle = text.strip().lower()
    if not needle:
        return None

    tax = load_taxonomy()
    for d in tax.get("dominios", []):
        if not isinstance(d, dict):
            continue
        domain_id = d.get("id", "").lower()
        if needle == domain_id:
            return d["id"]
        aliases = d.get("aliases", [])
        if isinstance(aliases, list):
            normalized_aliases = {str(a).lower() for a in aliases}
            if needle in normalized_aliases:
                return d["id"]
    return None


def list_cargos() -> list[str]:
    """Return all cargo ids defined in the taxonomy."""
    tax = load_taxonomy()
    return list(tax.get("cargos", {}).keys())


def cargo_domains(cargo_id: str) -> dict:
    """Return primary + secondary domains for a cargo.

    Args:
        cargo_id: Cargo id (e.g. "CRO", "CLOSER").

    Returns:
        dict with keys: dominios_primarios, dominios_secundarios, pessoa_prioritaria_default
        Empty dict if cargo not found.
    """
    tax = load_taxonomy()
    return tax.get("cargos", {}).get(cargo_id, {})


def pessoa_expertise(pessoa_id: str) -> dict:
    """Return expertise mapping for a pessoa.

    Args:
        pessoa_id: Pessoa id (e.g. "ALEX-HORMOZI", "JANE-DOE").

    Returns:
        dict with keys: expertise_primaria, expertise_secundaria, contexto
        Empty dict if pessoa not found.
    """
    tax = load_taxonomy()
    return tax.get("pessoas", {}).get(pessoa_id, {})
