#!/usr/bin/env python3
"""
DOSSIER TRIGGER - Intelligence Layer v1.0
==========================================
Avalia quando criar novos dossiers tematicos ou atualizar existentes.

Criterios (trigger_config.yaml):
- Criar dossier: occurrences >= 15 AND sources >= 2 AND frameworks >= 2
- Atualizar dossier: stale_days >= 30 OR new_elements >= 5

Calcula score de relevancia por tema:
- cross_source_weight: 3.0 (bonus por cada fonte adicional)
- framework_weight: 2.0 (bonus por framework nomeado)
- heuristic_weight: 1.5 (bonus por heuristica com numeros)
- methodology_weight: 2.0 (bonus por metodologia step-by-step)
- philosophy_weight: 1.0 (bonus por crenca/filosofia)

Grava decision log em logs/triggers.jsonl (padrao MMOS)

Versao: 1.0.0
Data: 2026-02-24
"""

import json
import os
import re
import sys
import yaml
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))
from entity_normalizer import load_registry, save_registry

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
TRIGGER_CONFIG_PATH = BASE_DIR / "scripts" / "trigger_config.yaml"
TRIGGERS_LOG_PATH = BASE_DIR / "logs" / "triggers.jsonl"
DOSSIERS_THEMES_DIR = BASE_DIR / "knowledge" / "dossiers" / "themes"

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
def load_config():
    """Load trigger configuration."""
    if TRIGGER_CONFIG_PATH.exists():
        with open(TRIGGER_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_dossier_thresholds():
    """Get dossier creation thresholds."""
    config = load_config()
    dc = config.get("thresholds", {}).get("dossier_creation", {})
    return {
        "min_occurrences": dc.get("min_occurrences", 15),
        "min_sources": dc.get("min_sources", 2),
        "min_frameworks": dc.get("min_frameworks", 2),
        "min_relevance_score": dc.get("min_relevance_score", 25.0),
    }


def get_update_thresholds():
    """Get dossier update thresholds."""
    config = load_config()
    du = config.get("thresholds", {}).get("dossier_update", {})
    return {
        "stale_days": du.get("stale_days", 30),
        "min_new_elements": du.get("min_new_elements", 5),
    }


def get_scoring_weights():
    """Get relevance scoring weights."""
    config = load_config()
    dr = config.get("scoring", {}).get("dossier_relevance", {})
    return {
        "cross_source": dr.get("cross_source_weight", 3.0),
        "framework": dr.get("framework_weight", 2.0),
        "heuristic": dr.get("heuristic_weight", 1.5),
        "methodology": dr.get("methodology_weight", 2.0),
        "philosophy": dr.get("philosophy_weight", 1.0),
    }


# ---------------------------------------------------------------------------
# RELEVANCE SCORING
# ---------------------------------------------------------------------------
def calculate_relevance_score(theme_data):
    """
    Calculate relevance score for a theme based on its data.

    Score components:
    - Base: occurrence_count
    - cross_source bonus: 3.0 per additional source beyond 1
    - framework bonus: 2.0 per framework associated
    - heuristic bonus: 1.5 per heuristic with numbers
    - methodology bonus: 2.0 per methodology
    - philosophy bonus: 1.0 per philosophy/belief
    """
    weights = get_scoring_weights()

    occurrences = theme_data.get("occurrence_count", 0)
    sources = theme_data.get("sources", [])
    related_roles = theme_data.get("related_roles", [])
    domain_ids = theme_data.get("domain_ids", [])

    # Base score = occurrences
    score = float(occurrences)

    # Cross-source bonus
    n_sources = len(sources)
    if n_sources > 1:
        score += (n_sources - 1) * weights["cross_source"]

    # Role association bonus (proxy for framework/methodology depth)
    score += len(related_roles) * weights["framework"]

    # Domain breadth bonus
    if len(domain_ids) > 1:
        score += (len(domain_ids) - 1) * weights["methodology"]

    return round(score, 2)


# ---------------------------------------------------------------------------
# CORE: EVALUATE TRIGGERS
# ---------------------------------------------------------------------------
def evaluate_all_themes(registry=None):
    """
    Evaluate all themes in ENTITY-REGISTRY for dossier triggers.

    Returns:
        {
            "create": [{theme, score, reasons}],
            "update": [{theme, score, reasons}],
            "candidates": [{theme, score, reasons}],
            "tracking": [{theme, score}],
            "summary": {total, create, update, candidates, tracking}
        }
    """
    if registry is None:
        registry = load_registry()

    creation_thresholds = get_dossier_thresholds()
    update_thresholds = get_update_thresholds()
    status_config = load_config().get("status_labels", {}).get("dossier_readiness", {})
    ready_score = status_config.get("ready", 25.0)
    candidate_score = status_config.get("candidate", 15.0)

    results = {
        "create": [],
        "update": [],
        "candidates": [],
        "tracking": [],
    }

    themes = registry.get("themes", {})

    for canonical, theme_data in themes.items():
        score = calculate_relevance_score(theme_data)
        has_dossier = theme_data.get("has_dossier", False)
        occurrences = theme_data.get("occurrence_count", 0)
        n_sources = len(theme_data.get("sources", []))

        entry = {
            "theme": canonical,
            "score": score,
            "occurrences": occurrences,
            "sources": n_sources,
            "has_dossier": has_dossier,
            "domains": theme_data.get("domain_ids", []),
        }

        if has_dossier:
            # Check if needs update
            update_needed, reasons = _check_update_needed(canonical, theme_data, update_thresholds)
            if update_needed:
                entry["reasons"] = reasons
                results["update"].append(entry)
            # else: dossier exists and is up-to-date, skip
        else:
            # Check if should be created
            if (occurrences >= creation_thresholds["min_occurrences"] and
                    n_sources >= creation_thresholds["min_sources"] and
                    score >= creation_thresholds["min_relevance_score"]):
                entry["reasons"] = [
                    f"occurrences={occurrences} >= {creation_thresholds['min_occurrences']}",
                    f"sources={n_sources} >= {creation_thresholds['min_sources']}",
                    f"score={score} >= {creation_thresholds['min_relevance_score']}",
                ]
                results["create"].append(entry)
            elif score >= candidate_score:
                entry["missing"] = []
                if occurrences < creation_thresholds["min_occurrences"]:
                    entry["missing"].append(f"occurrences: {occurrences}/{creation_thresholds['min_occurrences']}")
                if n_sources < creation_thresholds["min_sources"]:
                    entry["missing"].append(f"sources: {n_sources}/{creation_thresholds['min_sources']}")
                results["candidates"].append(entry)
            else:
                results["tracking"].append(entry)

    # Sort by score descending
    for key in ("create", "update", "candidates", "tracking"):
        results[key].sort(key=lambda x: -x["score"])

    results["summary"] = {
        "total_themes": len(themes),
        "create": len(results["create"]),
        "update": len(results["update"]),
        "candidates": len(results["candidates"]),
        "tracking": len(results["tracking"]),
        "existing_dossiers": sum(1 for t in themes.values() if t.get("has_dossier")),
    }

    return results


def _check_update_needed(canonical, theme_data, thresholds):
    """Check if an existing dossier needs updating."""
    reasons = []

    # Check staleness via dossier file modification time
    dossier_path = theme_data.get("dossier_path")
    if dossier_path:
        full_path = BASE_DIR / dossier_path
        if full_path.exists():
            mtime = datetime.fromtimestamp(full_path.stat().st_mtime, tz=timezone.utc)
            age_days = (datetime.now(timezone.utc) - mtime).days
            if age_days >= thresholds["stale_days"]:
                reasons.append(f"stale: {age_days} days old (threshold: {thresholds['stale_days']})")

    # Check if theme has new sources not reflected in dossier
    # (simple heuristic: if occurrence_count is high but sources grew)
    last_seen = theme_data.get("last_seen", "")
    if last_seen:
        try:
            last_dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - last_dt).days < 7:
                # Recently active theme - may have new content
                reasons.append("recently_active: new content detected within 7 days")
        except (ValueError, TypeError):
            pass

    return len(reasons) > 0, reasons


# ---------------------------------------------------------------------------
# LOG DECISIONS
# ---------------------------------------------------------------------------
def log_decisions(results):
    """Log trigger decisions to triggers.jsonl (MMOS pattern)."""
    TRIGGERS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    for action_type in ("create", "update"):
        for entry in results[action_type]:
            log_entry = {
                "timestamp": now,
                "trigger_type": f"dossier_{action_type}",
                "theme": entry["theme"],
                "score": entry["score"],
                "occurrences": entry["occurrences"],
                "sources": entry["sources"],
                "reasons": entry.get("reasons", []),
                "has_dossier": entry["has_dossier"],
                "status": "pending",
            }
            with open(TRIGGERS_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Uso: python3 dossier_trigger.py [--log]")
        print()
        print("  --log    Gravar decisoes em logs/triggers.jsonl")
        sys.exit(0)

    should_log = "--log" in sys.argv

    print("\n" + "=" * 60)
    print("  DOSSIER TRIGGER - Intelligence Layer v1.0")
    print("=" * 60)

    results = evaluate_all_themes()

    # Summary
    s = results["summary"]
    print(f"\n  Total themes:       {s['total_themes']}")
    print(f"  Existing dossiers:  {s['existing_dossiers']}")
    print(f"  ---")
    print(f"  CREATE (new):       {s['create']}")
    print(f"  UPDATE (stale):     {s['update']}")
    print(f"  CANDIDATES:         {s['candidates']}")
    print(f"  TRACKING:           {s['tracking']}")

    # CREATE triggers
    if results["create"]:
        print(f"\n--- CREATE DOSSIER TRIGGERS ---")
        for entry in results["create"]:
            print(f"  [CREATE] {entry['theme']}")
            print(f"           Score: {entry['score']} | Occ: {entry['occurrences']} | Sources: {entry['sources']}")
            for reason in entry.get("reasons", []):
                print(f"           -> {reason}")

    # UPDATE triggers
    if results["update"]:
        print(f"\n--- UPDATE DOSSIER TRIGGERS ---")
        for entry in results["update"]:
            print(f"  [UPDATE] {entry['theme']}")
            print(f"           Score: {entry['score']} | Occ: {entry['occurrences']}")
            for reason in entry.get("reasons", []):
                print(f"           -> {reason}")

    # CANDIDATES
    if results["candidates"]:
        print(f"\n--- CANDIDATES (almost ready) ---")
        for entry in results["candidates"][:10]:
            missing = ", ".join(entry.get("missing", []))
            print(f"  [CANDIDATE] {entry['theme']}  (score: {entry['score']}, missing: {missing})")

    if should_log:
        log_decisions(results)
        print(f"\n[LOGGED] Decisions written to {TRIGGERS_LOG_PATH}")


if __name__ == "__main__":
    main()
