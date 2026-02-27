#!/usr/bin/env python3
"""
AGENT TRIGGER - Intelligence Layer v2.0
========================================
Avalia quando criar novos agentes (person ou cargo) baseado em thresholds.

v2.0 Changes:
- Cargo agents agora usam weighted_score (tiered: established/emerging/emergent)
- Backward compat: se weighted_score ausente, usa mention_count
- Tiered evaluation: established (create) / emerging (track) / emergent (observe)
- Status lifecycle: emergent_candidate -> tracking -> active
- Log inclui weighted_score e tier info

Grava decision log em logs/triggers.jsonl

Versao: 2.0.0
Data: 2026-02-25
"""

import json
import sys
import yaml
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from entity_normalizer import load_registry, load_taxonomy

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
TRIGGER_CONFIG_PATH = BASE_DIR / "scripts" / "trigger_config.yaml"
TRIGGERS_LOG_PATH = BASE_DIR / "logs" / "triggers.jsonl"

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
def load_config():
    if TRIGGER_CONFIG_PATH.exists():
        with open(TRIGGER_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_person_thresholds():
    config = load_config()
    ap = config.get("thresholds", {}).get("agent_creation_person", {})
    return {
        "min_sources": ap.get("min_sources", 2),
        "min_dna_elements": ap.get("min_dna_elements", 30),
        "min_frameworks": ap.get("min_frameworks", 5),
    }


def get_cargo_thresholds():
    """
    Load tiered cargo thresholds from trigger_config.yaml v2.0.

    Returns dict with keys: established, emerging, emergent.
    Each tier has: min_weighted_score, min_sources, domain_match_required, status_output.
    Falls back to flat thresholds if tiered config not found.
    """
    config = load_config()
    ac = config.get("thresholds", {}).get("agent_creation_cargo", {})

    # Check if tiered config exists (v2.0)
    if "established" in ac:
        return {
            "established": {
                "min_weighted_score": ac["established"].get("min_weighted_score", 10),
                "min_sources": ac["established"].get("min_sources", 2),
                "domain_match_required": ac["established"].get("domain_match_required", True),
                "status_output": ac["established"].get("status_output", "active"),
            },
            "emerging": {
                "min_weighted_score": ac["emerging"].get("min_weighted_score", 5),
                "min_sources": ac["emerging"].get("min_sources", 1),
                "domain_match_required": ac["emerging"].get("domain_match_required", False),
                "status_output": ac["emerging"].get("status_output", "tracking"),
                "promotion_rules": ac["emerging"].get("promotion_rules", {
                    "min_weighted_score": 15,
                    "min_sources": 2,
                }),
            },
            "emergent": {
                "min_weighted_score": ac["emergent"].get("min_weighted_score", 3),
                "min_sources": ac["emergent"].get("min_sources", 1),
                "status_output": ac["emergent"].get("status_output", "emergent_candidate"),
            },
            "tiered": True,
        }

    # Fallback to flat thresholds (v1.0 compat)
    return {
        "established": {
            "min_weighted_score": ac.get("min_mentions", 10),
            "min_sources": ac.get("min_sources", 2),
            "domain_match_required": ac.get("domain_match_required", True),
            "status_output": "active",
        },
        "emerging": {
            "min_weighted_score": 5,
            "min_sources": 1,
            "domain_match_required": False,
            "status_output": "tracking",
            "promotion_rules": {"min_weighted_score": 15, "min_sources": 2},
        },
        "emergent": {
            "min_weighted_score": 3,
            "min_sources": 1,
            "status_output": "emergent_candidate",
        },
        "tiered": False,
    }


def _get_weighted_score(data):
    """
    Get weighted_score with fallback to mention_count for backward compat.
    """
    return data.get("weighted_score", data.get("mention_count", 0))


# ---------------------------------------------------------------------------
# EVALUATE PERSON AGENTS
# ---------------------------------------------------------------------------
def evaluate_person_agents(registry=None):
    """
    Evaluate all persons for agent creation triggers.

    Returns:
        {
            "create": [{person, reasons, score}],
            "candidates": [{person, missing}],
            "existing": [{person}],
        }
    """
    if registry is None:
        registry = load_registry()

    thresholds = get_person_thresholds()
    persons = registry.get("persons", {})

    results = {"create": [], "candidates": [], "existing": []}

    for canonical, data in persons.items():
        has_agent = data.get("has_agent", False)
        n_sources = len(data.get("sources", []))
        mention_count = data.get("mention_count", 0)
        domains = data.get("domains", [])

        if has_agent:
            results["existing"].append({
                "person": canonical,
                "agent_path": data.get("agent_path", ""),
                "sources": n_sources,
                "mentions": mention_count,
            })
            continue

        meets_sources = n_sources >= thresholds["min_sources"]
        meets_content = mention_count >= thresholds["min_dna_elements"]
        meets_frameworks = len(domains) >= 2

        reasons = []
        missing = []

        if meets_sources:
            reasons.append(f"sources={n_sources} >= {thresholds['min_sources']}")
        else:
            missing.append(f"sources: {n_sources}/{thresholds['min_sources']}")

        if meets_content:
            reasons.append(f"mentions={mention_count} >= {thresholds['min_dna_elements']} (proxy for DNA)")
        else:
            missing.append(f"mentions: {mention_count}/{thresholds['min_dna_elements']} (proxy for DNA)")

        if meets_frameworks:
            reasons.append(f"domains={len(domains)} (diverse)")
        else:
            missing.append(f"domains: {len(domains)}/2")

        if meets_sources and meets_content:
            results["create"].append({
                "person": canonical,
                "reasons": reasons,
                "sources": n_sources,
                "mentions": mention_count,
                "domains": domains,
            })
        elif n_sources >= 1 or mention_count >= 5:
            results["candidates"].append({
                "person": canonical,
                "missing": missing,
                "sources": n_sources,
                "mentions": mention_count,
            })

    results["create"].sort(key=lambda x: -x["mentions"])
    results["candidates"].sort(key=lambda x: -x["mentions"])

    return results


# ---------------------------------------------------------------------------
# EVALUATE CARGO AGENTS (v2.0 - Tiered with weighted_score)
# ---------------------------------------------------------------------------
def evaluate_cargo_agents(registry=None):
    """
    Evaluate all roles for cargo agent creation using tiered thresholds.

    Uses weighted_score (direct*1.0 + inferred*0.7 + emergent*0.5) instead
    of raw mention_count. Falls back to mention_count if weighted_score absent.

    Tiers:
        established: weighted_score >= 10, sources >= 2 -> CREATE agent
        emerging:    weighted_score >= 5, sources >= 1  -> TRACK (candidate)
        emergent:    weighted_score >= 3, sources >= 1  -> OBSERVE only

    Returns:
        {
            "create": [{role, reasons, weighted_score, tier, ...}],
            "candidates": [{role, missing, tier, ...}],
            "existing": [{role}],
        }
    """
    if registry is None:
        registry = load_registry()

    thresholds = get_cargo_thresholds()
    tax = load_taxonomy()
    taxonomy_cargos = set(k.upper() for k in tax.get("cargos", {}).keys())
    roles = registry.get("roles", {})

    results = {"create": [], "candidates": [], "existing": []}

    for canonical, data in roles.items():
        has_agent = data.get("has_agent", False)
        weighted_score = _get_weighted_score(data)
        mention_count = data.get("mention_count", 0)
        n_sources = len(data.get("sources", []))
        domain_ids = data.get("domain_ids", [])
        status = data.get("status", "tracking")
        breakdown = data.get("mention_breakdown", {})

        if has_agent:
            results["existing"].append({
                "role": canonical,
                "agent_path": data.get("agent_path", ""),
                "mentions": mention_count,
                "weighted_score": weighted_score,
                "sources": n_sources,
            })
            continue

        has_domain = len(domain_ids) > 0 or canonical in taxonomy_cargos

        # --- Tier 1: ESTABLISHED (create agent) ---
        est = thresholds["established"]
        meets_est_score = weighted_score >= est["min_weighted_score"]
        meets_est_sources = n_sources >= est["min_sources"]
        meets_est_domain = has_domain if est.get("domain_match_required", True) else True

        if meets_est_score and meets_est_sources and meets_est_domain:
            reasons = [
                f"weighted_score={weighted_score:.1f} >= {est['min_weighted_score']}",
                f"sources={n_sources} >= {est['min_sources']}",
            ]
            if has_domain:
                reasons.append("domain_match=True")
            if breakdown:
                reasons.append(
                    f"breakdown: direct={breakdown.get('direct', 0)}, "
                    f"inferred={breakdown.get('inferred', 0)}, "
                    f"emergent={breakdown.get('emergent', 0)}"
                )
            results["create"].append({
                "role": canonical,
                "reasons": reasons,
                "mention_count": mention_count,
                "weighted_score": weighted_score,
                "sources": n_sources,
                "domain_ids": domain_ids,
                "tier": "established",
                "status_output": est["status_output"],
            })
            continue

        # --- Tier 2: EMERGING (track, candidate for promotion) ---
        emg = thresholds["emerging"]
        meets_emg_score = weighted_score >= emg["min_weighted_score"]
        meets_emg_sources = n_sources >= emg["min_sources"]

        if meets_emg_score and meets_emg_sources:
            missing = []
            if not meets_est_score:
                missing.append(f"weighted_score: {weighted_score:.1f}/{est['min_weighted_score']}")
            if not meets_est_sources:
                missing.append(f"sources: {n_sources}/{est['min_sources']}")
            if est.get("domain_match_required") and not has_domain:
                missing.append("domain_match: required for established")

            # Check promotion eligibility
            promo = emg.get("promotion_rules", {})
            promo_eligible = (
                weighted_score >= promo.get("min_weighted_score", 15) and
                n_sources >= promo.get("min_sources", 2)
            )

            results["candidates"].append({
                "role": canonical,
                "missing": missing,
                "mention_count": mention_count,
                "weighted_score": weighted_score,
                "sources": n_sources,
                "tier": "emerging",
                "status": status,
                "promotion_eligible": promo_eligible,
            })
            continue

        # --- Tier 3: EMERGENT (observe only) ---
        emt = thresholds["emergent"]
        meets_emt_score = weighted_score >= emt["min_weighted_score"]
        meets_emt_sources = n_sources >= emt["min_sources"]

        if meets_emt_score and meets_emt_sources:
            missing = [
                f"weighted_score: {weighted_score:.1f}/{emg['min_weighted_score']} (need for emerging)",
            ]
            results["candidates"].append({
                "role": canonical,
                "missing": missing,
                "mention_count": mention_count,
                "weighted_score": weighted_score,
                "sources": n_sources,
                "tier": "emergent",
                "status": status,
            })

    results["create"].sort(key=lambda x: -x["weighted_score"])
    results["candidates"].sort(key=lambda x: -x["weighted_score"])

    return results


# ---------------------------------------------------------------------------
# LOG
# ---------------------------------------------------------------------------
def log_decisions(person_results, cargo_results):
    """Log trigger decisions to triggers.jsonl."""
    TRIGGERS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    for entry in person_results.get("create", []):
        log_entry = {
            "timestamp": now,
            "trigger_type": "agent_person_create",
            "entity": entry["person"],
            "reasons": entry["reasons"],
            "mentions": entry["mentions"],
            "sources": entry["sources"],
            "status": "pending",
        }
        with open(TRIGGERS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    for entry in cargo_results.get("create", []):
        log_entry = {
            "timestamp": now,
            "trigger_type": "agent_cargo_create",
            "entity": entry["role"],
            "reasons": entry["reasons"],
            "mention_count": entry["mention_count"],
            "weighted_score": entry.get("weighted_score", 0),
            "sources": entry["sources"],
            "tier": entry.get("tier", "established"),
            "status": "pending",
        }
        with open(TRIGGERS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    should_log = "--log" in sys.argv

    print("\n" + "=" * 70)
    print("  AGENT TRIGGER - Intelligence Layer v2.0 (Tiered Thresholds)")
    print("=" * 70)

    # Person agents
    print("\n--- PERSON AGENTS ---")
    pr = evaluate_person_agents()
    print(f"  Existing: {len(pr['existing'])}")
    for e in pr["existing"]:
        print(f"    [OK] {e['person']} ({e['sources']} sources, {e['mentions']} mentions)")

    if pr["create"]:
        print(f"\n  CREATE TRIGGERS ({len(pr['create'])}):")
        for e in pr["create"]:
            print(f"    [CREATE] {e['person']} ({e['mentions']} mentions, {e['sources']} sources)")
            for r in e["reasons"]:
                print(f"             -> {r}")

    if pr["candidates"]:
        print(f"\n  CANDIDATES ({len(pr['candidates'])}):")
        for e in pr["candidates"][:5]:
            m = ", ".join(e["missing"])
            print(f"    [~] {e['person']} (missing: {m})")

    # Cargo agents (v2.0 - tiered)
    print("\n--- CARGO AGENTS (Tiered v2.0) ---")
    cr = evaluate_cargo_agents()
    print(f"  Existing: {len(cr['existing'])}")
    for e in cr["existing"]:
        ws = e.get("weighted_score", e.get("mentions", 0))
        print(f"    [OK] {e['role']} ({e['sources']} sources, ws={ws:.1f})")

    if cr["create"]:
        print(f"\n  CREATE TRIGGERS - ESTABLISHED ({len(cr['create'])}):")
        for e in cr["create"]:
            print(f"    [CREATE] {e['role']} (ws={e['weighted_score']:.1f}, "
                  f"{e['sources']} sources, tier={e['tier']})")
            for r in e["reasons"]:
                print(f"             -> {r}")

    if cr["candidates"]:
        # Separate by tier
        emerging = [c for c in cr["candidates"] if c.get("tier") == "emerging"]
        emergent = [c for c in cr["candidates"] if c.get("tier") == "emergent"]

        if emerging:
            print(f"\n  EMERGING CANDIDATES ({len(emerging)}):")
            for e in emerging[:5]:
                promo = " [PROMO ELIGIBLE]" if e.get("promotion_eligible") else ""
                m = ", ".join(e["missing"])
                print(f"    [~] {e['role']} (ws={e['weighted_score']:.1f}, "
                      f"status={e.get('status', '?')}){promo}")
                print(f"        missing: {m}")

        if emergent:
            print(f"\n  EMERGENT (Observing) ({len(emergent)}):")
            for e in emergent[:5]:
                print(f"    [.] {e['role']} (ws={e['weighted_score']:.1f}, "
                      f"status={e.get('status', '?')})")

    # Summary
    total_create = len(pr["create"]) + len(cr["create"])
    total_existing = len(pr["existing"]) + len(cr["existing"])
    n_emerging = len([c for c in cr.get("candidates", []) if c.get("tier") == "emerging"])
    n_emergent = len([c for c in cr.get("candidates", []) if c.get("tier") == "emergent"])
    print(f"\n{'='*70}")
    print(f"  SUMMARY: {total_existing} active | {total_create} triggers | "
          f"{n_emerging} emerging | {n_emergent} emergent | "
          f"{len(pr['candidates'])} person candidates")
    print(f"{'='*70}")

    if should_log:
        log_decisions(pr, cr)
        print(f"\n[LOGGED] Decisions written to {TRIGGERS_LOG_PATH}")


if __name__ == "__main__":
    main()
