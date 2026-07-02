"""
core/intelligence/pipeline/agg_builder.py — Cross-Expert Domain Aggregation Builder

Reads DNA YAMLs from each expert's person dir, merges entries per domain
into AGG-{DOMAIN}.yaml files in knowledge/external/dna/domains/{domain}/.

Usage:
    from engine.intelligence.pipeline.agg_builder import build_all_domains
    results = build_all_domains()

    # Single domain:
    from engine.intelligence.pipeline.agg_builder import build_agg_for_domain
    path = build_agg_for_domain("vendas", ["alex-hormozi", "cole-gordon", "jeremy-miner"])
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from engine.paths import EXTERNAL_DNA_DOMAINS, EXTERNAL_DNA_PERSONS

logger = logging.getLogger(__name__)

# ── Domain-to-Expert mapping ────────────────────────────────────────────────
# Each domain lists which experts contribute and their authority weight (0.0-1.0).
DOMAIN_CONFIG: dict[str, dict[str, float]] = {
    "vendas": {
        "alex-hormozi": 0.85,
        "cole-gordon": 0.90,
        "jeremy-miner": 0.85,
        "jordan-lee": 0.70,
        "sales-methodology": 0.60,
    },
    "marketing": {
        "alex-hormozi": 0.80,
        "jeremy-haynes": 0.90,
        "liam-ottley": 0.75,
    },
    "offers": {
        "alex-hormozi": 0.95,
        "sam-oven": 0.80,
    },
    "outbound": {
        "cole-gordon": 0.85,
        "jordan-lee": 0.90,
    },
    "hiring": {
        "alex-hormozi": 0.80,
        "richard-linder": 0.90,
        "the-scalable-company": 0.75,
    },
    "leadership": {
        "alex-hormozi": 0.85,
        "sam-oven": 0.80,
    },
    "pricing": {
        "alex-hormozi": 0.90,
        "jeremy-haynes": 0.80,
        "sam-oven": 0.75,
    },
    "funnels": {
        "alex-hormozi": 0.80,
        "jeremy-haynes": 0.90,
        "cole-gordon": 0.75,
    },
    "ads": {
        "jeremy-haynes": 0.95,
        "liam-ottley": 0.70,
    },
    "content": {
        "liam-ottley": 0.85,
        "jeremy-haynes": 0.75,
    },
    "customer-success": {
        "alex-hormozi": 0.80,
        "cole-gordon": 0.75,
    },
    "finance": {
        "alex-hormozi": 0.85,
        "sam-oven": 0.70,
    },
    # AI agent orchestration / operating-systems domain
    # (STORY-MCE-AI-SYSTEMS-DOMAIN). Seeded with jake-van-clief (ICM author).
    "ai-systems": {
        "jake-van-clief": 0.90,
    },
}

# DNA layer files and their layer codes (lowercase filenames as found on disk).
DNA_LAYERS: dict[str, str] = {
    "filosofias.yaml": "L1_FILOSOFIAS",
    "modelos-mentais.yaml": "L2_MODELOS_MENTAIS",
    "heuristicas.yaml": "L3_HEURISTICAS",
    "frameworks.yaml": "L4_FRAMEWORKS",
    "metodologias.yaml": "L5_METODOLOGIAS",
}


def _load_yaml(path: Path) -> dict[str, Any] | None:
    """Safely load a YAML file, returning None on failure."""
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as exc:
        logger.warning("Failed to load %s: %s", path, exc)
        return None


def _find_layer_file(expert_dir: Path, layer_filename: str) -> Path | None:
    """Find layer file case-insensitively."""
    # Try exact match first
    exact = expert_dir / layer_filename
    if exact.exists():
        return exact
    # Try uppercase (some experts have HEURISTICAS.yaml)
    upper = expert_dir / layer_filename.upper()
    if upper.exists():
        return upper
    # Try case-insensitive scan
    target = layer_filename.lower()
    for child in expert_dir.iterdir():
        if child.name.lower() == target:
            return child
    return None


def _extract_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract entries list from a DNA YAML regardless of structure variation.

    Handles multiple key naming conventions found across experts:
    - Standard: 'entries' (alex-hormozi, cole-gordon)
    - Layer-specific: 'frameworks', 'heuristicas', 'filosofias', etc. (jeremy-haynes)
    - English variants: 'heuristics', 'philosophies', 'methodologies' (liam-ottley)
    """
    if not data:
        return []

    # Known content keys in order of preference
    content_keys = [
        "entries",
        "frameworks",
        "heuristicas",
        "heuristics",
        "filosofias",
        "philosophies",
        "metodologias",
        "methodologies",
        "modelos_mentais",
        "modelos-mentais",
        "mental_models",
        "mental-models",
    ]

    for key in content_keys:
        value = data.get(key)
        if isinstance(value, list) and value:
            return value

    # Fallback: find any list value that looks like entries
    skip_keys = {
        "pessoa",
        "slug",
        "versao",
        "updated",
        "total_entries",
        "version",
        "person",
        "layer",
        "pipeline_run",
        "prior_run",
        "source_count",
        "metadata",
    }
    for key, value in data.items():
        if key in skip_keys:
            continue
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return value

    return []


def build_agg_for_domain(domain: str, expert_weights: dict[str, float] | None = None) -> Path:
    """Read DNA YAMLs from each expert, merge entries for this domain, write AGG file.

    Args:
        domain: Domain name (e.g. "vendas", "marketing").
        expert_weights: Dict of {expert_slug: weight}. If None, uses DOMAIN_CONFIG.

    Returns:
        Path to the generated AGG-{DOMAIN}.yaml file.
    """
    if expert_weights is None:
        expert_weights = DOMAIN_CONFIG.get(domain, {})

    if not expert_weights:
        raise ValueError(f"No expert configuration found for domain '{domain}'")

    domain_dir = EXTERNAL_DNA_DOMAINS / domain
    domain_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    all_entries: list[dict[str, Any]] = []
    experts_meta: list[dict[str, Any]] = []

    for expert_slug, weight in expert_weights.items():
        expert_dir = EXTERNAL_DNA_PERSONS / expert_slug
        if not expert_dir.exists():
            logger.warning("Expert dir not found: %s", expert_dir)
            continue

        layers_contributed: list[str] = []
        expert_entry_count = 0

        for layer_filename, layer_code in DNA_LAYERS.items():
            layer_path = _find_layer_file(expert_dir, layer_filename)
            if layer_path is None:
                continue

            data = _load_yaml(layer_path)
            if data is None:
                continue

            entries = _extract_entries(data)
            if not entries:
                continue

            layers_contributed.append(layer_code)

            for entry in entries:
                merged_entry = {
                    "id": entry.get("id", f"UNKNOWN-{expert_slug}"),
                    "name": entry.get("name", entry.get("titulo", "")),
                    "description": entry.get("description", entry.get("descricao", "")),
                }
                # Preserve quote if present
                quote = entry.get("quote")
                if quote:
                    merged_entry["quote"] = quote

                # Preserve source chunks
                chunks = entry.get("source_chunks", entry.get("chunk_ids", []))
                if chunks:
                    merged_entry["source_chunks"] = chunks

                merged_entry.update(
                    {
                        "confidence": entry.get("confidence", entry.get("confianca", 0.5)),
                        "priority": entry.get("priority", entry.get("prioridade", "MEDIUM")),
                        "origin": expert_slug,
                        "origin_weight": weight,
                        "layer": layer_code,
                    }
                )
                all_entries.append(merged_entry)
                expert_entry_count += 1

        if layers_contributed:
            experts_meta.append(
                {
                    "person": expert_slug,
                    "weight": weight,
                    "layers_contributed": layers_contributed,
                    "entry_count": expert_entry_count,
                    "source_dir": str(
                        expert_dir.relative_to(EXTERNAL_DNA_PERSONS.parent.parent.parent)
                    ),
                }
            )

    # Normalize confidence values to float
    for entry in all_entries:
        conf = entry.get("confidence", 0.5)
        if isinstance(conf, str):
            conf_map = {"HIGH": 0.9, "MEDIUM": 0.7, "LOW": 0.4}
            entry["confidence"] = conf_map.get(conf.upper(), 0.5)

    # Build AGG document
    agg_doc = {
        "version": "1.0",
        "domain": domain,
        "updated": timestamp,
        "pipeline_run": f"AGG-BUILD-{datetime.now(UTC).strftime('%Y-%m-%d')}",
        "total_entries": len(all_entries),
        "total_experts": len(experts_meta),
        "experts": experts_meta,
        "entries": all_entries,
        "conflicts": [],
    }

    output_path = domain_dir / f"AGG-{domain.upper()}.yaml"
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            agg_doc, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120
        )

    logger.info(
        "Built AGG for domain '%s': %d entries from %d experts -> %s",
        domain,
        len(all_entries),
        len(experts_meta),
        output_path,
    )

    return output_path


def build_all_domains() -> dict[str, dict[str, Any]]:
    """Build AGG files for all configured domains.

    Returns:
        Dict mapping domain name to {path, entries, experts} summary.
    """
    results: dict[str, dict[str, Any]] = {}

    for domain in DOMAIN_CONFIG:
        try:
            path = build_agg_for_domain(domain)
            # Read back to get counts
            data = _load_yaml(path)
            results[domain] = {
                "path": str(path),
                "entries": data.get("total_entries", 0) if data else 0,
                "experts": data.get("total_experts", 0) if data else 0,
                "status": "ok",
            }
        except Exception as exc:
            logger.error("Failed to build domain '%s': %s", domain, exc)
            results[domain] = {
                "path": "",
                "entries": 0,
                "experts": 0,
                "status": f"error: {exc}",
            }

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = build_all_domains()
    total_entries = sum(r["entries"] for r in results.values())
    total_experts = len(
        {e for r in results.values() for e in DOMAIN_CONFIG.get(list(DOMAIN_CONFIG.keys())[0], {})}
    )
    print(f"\n{'='*60}")
    print(f"AGG Builder Complete: {len(results)} domains")
    print(f"{'='*60}")
    for domain, info in sorted(results.items()):
        status = "OK" if info["status"] == "ok" else "FAIL"
        print(
            f"  {domain:<20s} {info['entries']:>4d} entries  {info['experts']:>2d} experts  [{status}]"
        )
    print(f"{'='*60}")
    print(f"Total entries across all domains: {total_entries}")
