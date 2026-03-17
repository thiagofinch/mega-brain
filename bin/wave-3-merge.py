#!/usr/bin/env python3
"""
Wave 3 — Merge & Validate
==========================
Merges per-entity MCE artifacts into global files and validates cross-references.

Tasks:
    3.1 Merge CANONICAL-MAP (per-entity → global)
    3.2 Merge INSIGHTS-STATE (per-entity → global)
    3.3 Update AGENT-INDEX.yaml
    3.4 Generate completion report

Usage:
    python3 bin/wave-3-merge.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# -- Project paths ----------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.paths import (  # noqa: E402
    AGENTS,
    ARTIFACTS,
    KNOWLEDGE_EXTERNAL,
    LOGS,
    MISSION_CONTROL,
    ROOT as PROJECT_ROOT,
)

# -- Logging ----------------------------------------------------------------
LOG_DIR = LOGS / "wave-mce"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "wave-3-merge.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)
log = logging.getLogger("wave-3")

# -- State ------------------------------------------------------------------
WAVE_STATE_FILE = MISSION_CONTROL / "WAVE-STATE.json"
MCE_DIR = ARTIFACTS / "mce"


def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_json(path: Path, data: dict, dry_run: bool = False) -> None:
    if dry_run:
        log.info(f"  [DRY] Would write: {path.relative_to(PROJECT_ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"  WROTE: {path.relative_to(PROJECT_ROOT)}")


# ===========================================================================
# TASK 3.1: Merge CANONICAL-MAP
# ===========================================================================
def task_merge_canonical(dry_run: bool = False) -> dict:
    """Merge per-entity CANONICAL-MAP.json files into global."""
    log.info("=" * 60)
    log.info("TASK 3.1: Merge CANONICAL-MAP")
    log.info("=" * 60)

    global_path = ARTIFACTS / "canonical" / "CANONICAL-MAP.json"
    global_map = load_json(global_path)
    stats = {"entities_merged": 0, "new_entries": 0, "existing_updated": 0}

    if not MCE_DIR.exists():
        log.info("  No MCE artifacts found. Skipping.")
        return stats

    for entity_dir in sorted(MCE_DIR.iterdir()):
        if not entity_dir.is_dir():
            continue
        local_map_path = entity_dir / "CANONICAL-MAP.json"
        if not local_map_path.exists():
            continue

        local_map = load_json(local_map_path)
        stats["entities_merged"] += 1

        # Merge entities
        global_entities = global_map.setdefault("entities", {})
        local_entities = local_map.get("entities", {})

        for canonical, data in local_entities.items():
            if not isinstance(data, dict):
                continue
            if canonical in global_entities:
                # Merge variants (handle both list of strings and list of dicts)
                existing_raw = global_entities[canonical].get("variants", [])
                new_raw = data.get("variants", [])
                # Normalize to strings for dedup
                def to_str(v):
                    return v if isinstance(v, str) else str(v)
                existing_set = set(to_str(v) for v in existing_raw)
                for v in new_raw:
                    vs = to_str(v)
                    if vs not in existing_set:
                        existing_raw.append(v)
                        existing_set.add(vs)
                global_entities[canonical]["variants"] = existing_raw
                # Merge other fields
                for key in data:
                    if key != "variants" and key not in global_entities[canonical]:
                        global_entities[canonical][key] = data[key]
                stats["existing_updated"] += 1
            else:
                global_entities[canonical] = data
                stats["new_entries"] += 1

    global_map["merged_at"] = datetime.now(timezone.utc).isoformat()
    v = global_map.get("version", 0)
    global_map["version"] = (int(v) if isinstance(v, (int, float)) else 1) + 1
    save_json(global_path, global_map, dry_run)

    log.info(f"  Result: {stats['entities_merged']} entity files merged, "
             f"{stats['new_entries']} new, {stats['existing_updated']} updated")
    return stats


# ===========================================================================
# TASK 3.2: Merge INSIGHTS-STATE
# ===========================================================================
def task_merge_insights(dry_run: bool = False) -> dict:
    """Merge per-entity INSIGHTS-STATE.json files into global."""
    log.info("=" * 60)
    log.info("TASK 3.2: Merge INSIGHTS-STATE")
    log.info("=" * 60)

    global_path = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
    global_state = load_json(global_path)
    stats = {"entities_merged": 0, "insights_added": 0, "duplicates_skipped": 0}

    if not MCE_DIR.exists():
        log.info("  No MCE artifacts found. Skipping.")
        return stats

    # Track existing insight IDs for dedup
    global_persons = global_state.setdefault("persons", {})
    existing_ids: set[str] = set()
    for person_data in global_persons.values():
        insights_list = person_data if isinstance(person_data, list) else person_data.get("insights", [])
        for insight in insights_list:
            if isinstance(insight, dict):
                iid = insight.get("id") or insight.get("chunk_id", "")
                if iid:
                    existing_ids.add(iid)

    for entity_dir in sorted(MCE_DIR.iterdir()):
        if not entity_dir.is_dir():
            continue
        local_path = entity_dir / "INSIGHTS-STATE.json"
        if not local_path.exists():
            continue

        local_state = load_json(local_path)
        stats["entities_merged"] += 1

        local_persons = local_state.get("persons", {})
        for person_slug, person_data in local_persons.items():
            # Handle both formats: list or dict with "insights" key
            if isinstance(person_data, list):
                local_insights = person_data
                local_extra = {}
            elif isinstance(person_data, dict):
                local_insights = person_data.get("insights", [])
                local_extra = {k: v for k, v in person_data.items() if k != "insights"}
            else:
                continue

            # Ensure global person is a dict
            if isinstance(global_persons.get(person_slug), list):
                global_persons[person_slug] = {"slug": person_slug, "insights": global_persons[person_slug]}
            global_person = global_persons.setdefault(person_slug, {"slug": person_slug, "insights": []})
            if isinstance(global_person, list):
                global_person = {"slug": person_slug, "insights": global_person}
                global_persons[person_slug] = global_person
            global_insights = global_person.setdefault("insights", [])

            for insight in local_insights:
                if not isinstance(insight, dict):
                    continue
                iid = insight.get("id") or insight.get("chunk_id", "")
                if iid and iid in existing_ids:
                    stats["duplicates_skipped"] += 1
                    continue
                global_insights.append(insight)
                if iid:
                    existing_ids.add(iid)
                stats["insights_added"] += 1

            # Merge behavioral_patterns if present
            if "behavioral_patterns" in local_extra:
                existing_patterns = global_person.get("behavioral_patterns", [])
                existing_names = {p.get("name", "") for p in existing_patterns if isinstance(p, dict)}
                for pattern in local_extra["behavioral_patterns"]:
                    if isinstance(pattern, dict) and pattern.get("name", "") not in existing_names:
                        existing_patterns.append(pattern)
                global_person["behavioral_patterns"] = existing_patterns

            # Merge identity layers if present
            for key in ["value_hierarchy", "obsessions", "paradoxes"]:
                if key in local_extra:
                    global_person[key] = local_extra[key]

    global_state["merged_at"] = datetime.now(timezone.utc).isoformat()
    v = global_state.get("version", 0)
    global_state["version"] = (int(v) if isinstance(v, (int, float)) else 1) + 1
    save_json(global_path, global_state, dry_run)

    log.info(f"  Result: {stats['entities_merged']} entities, "
             f"{stats['insights_added']} insights added, "
             f"{stats['duplicates_skipped']} duplicates skipped")
    return stats


# ===========================================================================
# TASK 3.3: Update AGENT-INDEX.yaml
# ===========================================================================
def task_update_agent_index(dry_run: bool = False) -> dict:
    """Scan agents/ and update AGENT-INDEX.yaml."""
    log.info("=" * 60)
    log.info("TASK 3.3: Update AGENT-INDEX.yaml")
    log.info("=" * 60)

    import yaml

    index_path = AGENTS / "AGENT-INDEX.yaml"
    stats = {"agents_found": 0, "new_agents": 0, "updated": 0}

    if not index_path.exists():
        log.warning("  AGENT-INDEX.yaml not found. Skipping.")
        return stats

    index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}

    # Scan external agents
    external_dir = AGENTS / "external"
    if external_dir.exists():
        # Handle AGENT-INDEX format: external can be list or dict
        ext_section = index.get("external", [])
        if isinstance(ext_section, dict):
            ext_section = ext_section.get("agents", [])
        slugs_in_index = set()
        for a in ext_section:
            if isinstance(a, dict):
                slugs_in_index.add(a.get("slug", a.get("name", "")))
            elif isinstance(a, str):
                slugs_in_index.add(a)

        for agent_dir in sorted(external_dir.iterdir()):
            if not agent_dir.is_dir() or agent_dir.name.startswith((".", "_")):
                continue
            agent_md = agent_dir / "AGENT.md"
            if agent_md.exists():
                stats["agents_found"] += 1
                if agent_dir.name not in slugs_in_index:
                    stats["new_agents"] += 1
                    log.info(f"  NEW agent found: external/{agent_dir.name}")

    # Scan business agents
    business_dir = AGENTS / "business"
    if business_dir.exists():
        for category in sorted(business_dir.iterdir()):
            if not category.is_dir() or category.name.startswith((".", "_")):
                continue
            for agent_dir in sorted(category.iterdir()):
                if not agent_dir.is_dir() or agent_dir.name.startswith("."):
                    continue
                if (agent_dir / "AGENT.md").exists():
                    stats["agents_found"] += 1

    index["metadata"] = index.get("metadata", {})
    index["metadata"]["last_audit"] = datetime.now(timezone.utc).isoformat()
    index["metadata"]["total_agents"] = stats["agents_found"]

    if not dry_run:
        index_path.write_text(
            yaml.dump(index, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
        stats["updated"] = 1

    log.info(f"  Result: {stats['agents_found']} agents found, {stats['new_agents']} new")
    return stats


# ===========================================================================
# TASK 3.4: Completion report
# ===========================================================================
def task_completion_report(all_stats: dict, dry_run: bool = False) -> dict:
    """Generate final completion report."""
    log.info("=" * 60)
    log.info("TASK 3.4: Completion Report")
    log.info("=" * 60)

    report_path = LOG_DIR / "COMPLETION-REPORT.md"

    # Collect entity completion status
    entities_complete = []
    entities_incomplete = []

    if MCE_DIR.exists():
        for entity_dir in sorted(MCE_DIR.iterdir()):
            if not entity_dir.is_dir():
                continue
            completion = entity_dir / "COMPLETION.json"
            if completion.exists():
                data = load_json(completion)
                entities_complete.append({
                    "slug": entity_dir.name,
                    "steps": data.get("steps_completed", 0),
                    "timestamp": data.get("timestamp", "?"),
                })
            else:
                entities_incomplete.append(entity_dir.name)

    # Validate cross-references
    validation_results = _validate_cross_refs()

    report = f"""# MCE Pipeline — Completion Report

**Generated:** {datetime.now(timezone.utc).isoformat()}
**Mode:** Wave Execution (4 waves)

---

## Entities Processed

### Complete ({len(entities_complete)})

| # | Entity | Steps | Timestamp |
|---|--------|-------|-----------|
"""
    for i, e in enumerate(entities_complete, 1):
        report += f"| {i} | {e['slug']} | {e['steps']}/12 | {e['timestamp'][:19]} |\n"

    report += f"""
### Incomplete ({len(entities_incomplete)})

"""
    for e in entities_incomplete:
        report += f"- {e}\n"

    report += f"""
---

## Merge Statistics

| Metric | Value |
|--------|-------|
| Canonical entities merged | {all_stats.get('canonical', {}).get('entities_merged', 0)} |
| New canonical entries | {all_stats.get('canonical', {}).get('new_entries', 0)} |
| Insights added | {all_stats.get('insights', {}).get('insights_added', 0)} |
| Duplicate insights skipped | {all_stats.get('insights', {}).get('duplicates_skipped', 0)} |
| Agents found | {all_stats.get('agent_index', {}).get('agents_found', 0)} |
| New agents discovered | {all_stats.get('agent_index', {}).get('new_agents', 0)} |

---

## Cross-Reference Validation

| Check | Result |
|-------|--------|
| Dossier→DNA links | {validation_results.get('dossier_dna', 'N/A')} |
| Agent→Dossier links | {validation_results.get('agent_dossier', 'N/A')} |
| DNA YAML file counts match config | {validation_results.get('dna_counts', 'N/A')} |

---

## Logs

- Wave 0 (Hygiene): `logs/wave-mce/wave-0-hygiene.log`
- Wave 1 (Batch): `logs/wave-mce/wave-1.log`
- Wave 2 (MCE): `logs/wave-mce/*.log` (per entity)
- Wave 3 (Merge): `logs/wave-mce/wave-3-merge.log`
- This report: `logs/wave-mce/COMPLETION-REPORT.md`
"""

    if not dry_run:
        report_path.write_text(report, encoding="utf-8")
        log.info(f"  Report saved: {report_path.relative_to(PROJECT_ROOT)}")
    else:
        log.info(f"  [DRY] Would save report to {report_path.relative_to(PROJECT_ROOT)}")

    return {"entities_complete": len(entities_complete), "entities_incomplete": len(entities_incomplete)}


def _validate_cross_refs() -> dict:
    """Validate cross-references between dossiers, DNA, and agents."""
    results = {}

    # Check: each agent in external/ has matching dossier
    agents_dir = AGENTS / "external"
    dossiers_dir = KNOWLEDGE_EXTERNAL / "dossiers" / "persons"
    dna_dir = KNOWLEDGE_EXTERNAL / "dna" / "persons"

    agent_dossier_ok = 0
    agent_dossier_miss = 0
    dossier_dna_ok = 0
    dossier_dna_miss = 0

    if agents_dir.exists():
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir() or agent_dir.name.startswith((".", "_")):
                continue
            if not (agent_dir / "AGENT.md").exists():
                continue

            slug = agent_dir.name
            dossier_name = f"DOSSIER-{slug.upper().replace('-', '-')}.md"
            if (dossiers_dir / dossier_name).exists():
                agent_dossier_ok += 1
            else:
                agent_dossier_miss += 1

            slug_dna = dna_dir / slug
            if slug_dna.exists() and any(slug_dna.glob("*.yaml")):
                dossier_dna_ok += 1
            else:
                dossier_dna_miss += 1

    results["agent_dossier"] = f"{agent_dossier_ok} OK, {agent_dossier_miss} missing"
    results["dossier_dna"] = f"{dossier_dna_ok} OK, {dossier_dna_miss} missing"
    results["dna_counts"] = "check manually"

    return results


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="Wave 3 — Merge & Validate")
    parser.add_argument("--dry-run", action="store_true", help="Preview without executing")
    args = parser.parse_args()

    start = time.time()
    log.info("=" * 60)
    log.info(f"WAVE 3 — MERGE & VALIDATE {'[DRY RUN]' if args.dry_run else '[LIVE]'}")
    log.info(f"Started: {datetime.now(timezone.utc).isoformat()}")
    log.info("=" * 60)

    all_stats = {}
    all_stats["canonical"] = task_merge_canonical(args.dry_run)
    all_stats["insights"] = task_merge_insights(args.dry_run)
    all_stats["agent_index"] = task_update_agent_index(args.dry_run)
    report = task_completion_report(all_stats, args.dry_run)

    elapsed = time.time() - start

    log.info("")
    log.info("=" * 60)
    log.info("WAVE 3 — COMPLETE")
    log.info(f"  Entities complete: {report['entities_complete']}")
    log.info(f"  Entities incomplete: {report['entities_incomplete']}")
    log.info(f"  Duration: {elapsed:.1f}s")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
