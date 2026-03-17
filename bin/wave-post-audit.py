#!/usr/bin/env python3
"""
Wave Post-Audit — 11-Point Checklist Validator
================================================
Validates pipeline execution against the complete 11-point audit checklist.
Incorporates rules from OLD Mega Brain: cascading validation, skip reasons,
expected vs actual destinations, DNA completeness scoring.

Usage:
    python3 bin/wave-post-audit.py [--slug SLUG] [--all] [--fix]

Port from OLD MB rules:
    RULE #21: Cascateamento obrigatório de theme dossiers
    RULE #22: Cascateamento multi-destino pós-batch
    RULE #23: Validação automática da Fase 5
    RULE #24: Template V3 enforcement
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.paths import (  # noqa: E402
    AGENTS,
    ARTIFACTS,
    KNOWLEDGE_BUSINESS,
    KNOWLEDGE_EXTERNAL,
    KNOWLEDGE_PERSONAL,
    LOGS,
    MISSION_CONTROL,
    ROOT as PROJECT_ROOT,
)

# Logging
LOG_DIR = LOGS / "wave-mce"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "wave-post-audit.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)
log = logging.getLogger("post-audit")


def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


# ============================================================================
# CHECKLIST 1: Leitura geral da execução
# ============================================================================
def check_1_execution_reading() -> dict:
    """Audit pipeline execution logs for completeness."""
    log.info("=" * 60)
    log.info("CHECK 1: Leitura geral da execução")
    log.info("=" * 60)

    results = {"status": "PASS", "items": [], "skip_reasons": []}

    # Check MCE step logger
    step_log = LOGS / "mce-step-logger.jsonl"
    orchestrate_log = LOGS / "mce-orchestrate.jsonl"

    if step_log.exists():
        lines = step_log.read_text(encoding="utf-8").strip().split("\n")
        entries = [json.loads(l) for l in lines if l.strip()]
        slugs_processed = set()
        steps_by_slug: dict[str, set] = {}
        for e in entries:
            slug = e.get("slug", "unknown")
            step = e.get("step", 0)
            slugs_processed.add(slug)
            steps_by_slug.setdefault(slug, set()).add(step)

        results["items"].append(f"MCE step log: {len(entries)} entries, {len(slugs_processed)} slugs")

        # Check for incomplete pipelines (missing steps)
        expected_steps = {3, 4, 5, 6, 7, 8, 10}
        for slug, steps in steps_by_slug.items():
            missing = expected_steps - steps
            if missing:
                results["skip_reasons"].append({
                    "slug": slug,
                    "missing_steps": sorted(missing),
                    "reason": "Pipeline incomplete — steps not executed",
                    "severity": "HIGH",
                })
    else:
        results["items"].append("MCE step log: NOT FOUND")
        results["status"] = "WARN"

    if orchestrate_log.exists():
        lines = orchestrate_log.read_text(encoding="utf-8").strip().split("\n")
        entries = [json.loads(l) for l in lines if l.strip()]
        results["items"].append(f"Orchestrate log: {len(entries)} entries")
    else:
        results["items"].append("Orchestrate log: NOT FOUND")

    log.info(f"  Result: {results['status']} — {len(results['skip_reasons'])} skip reasons found")
    return results


# ============================================================================
# CHECKLIST 2: Criação e ativação de agentes
# ============================================================================
def check_2_agent_creation() -> dict:
    """Verify agent creation completeness."""
    log.info("=" * 60)
    log.info("CHECK 2: Criação e ativação de agentes")
    log.info("=" * 60)

    results = {"status": "PASS", "created": [], "should_exist_but_missing": [], "skip_reasons": []}

    # Load insights to find entities with 3+ insights (MCE threshold)
    insights_state = load_json(ARTIFACTS / "insights" / "INSIGHTS-STATE.json")
    persons = insights_state.get("persons", {})

    for slug, person_data in persons.items():
        # Handle both formats: list of insights or dict with "insights" key
        if isinstance(person_data, list):
            insight_count = len(person_data)
        elif isinstance(person_data, dict):
            insight_count = len(person_data.get("insights", []))
        else:
            insight_count = 0

        # Normalize slug for agent dir lookup
        agent_slug = slug.lower().replace(" ", "-")
        agent_dir = AGENTS / "external" / agent_slug

        has_agent = (agent_dir / "AGENT.md").exists()

        if has_agent:
            results["created"].append({"slug": agent_slug, "insights": insight_count})
        elif insight_count >= 3:
            results["should_exist_but_missing"].append({
                "slug": agent_slug,
                "insights": insight_count,
                "reason": f"Has {insight_count} insights (≥3 threshold) but no AGENT.md",
                "severity": "HIGH",
            })
            results["status"] = "FAIL"

    # Check agents that exist but have no insights (might be from old pipeline)
    # Normalize person keys for comparison
    normalized_persons = {k.lower().replace(" ", "-") for k in persons}
    for bucket in ["external", "business"]:
        agents_dir = AGENTS / bucket
        if not agents_dir.exists():
            continue
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir() or agent_dir.name.startswith((".", "_")):
                continue
            if (agent_dir / "AGENT.md").exists():
                slug = agent_dir.name
                if slug not in normalized_persons:
                    results["skip_reasons"].append({
                        "slug": slug,
                        "reason": "Agent exists but has NO insights in INSIGHTS-STATE",
                        "severity": "MEDIUM",
                    })

    # Check AGENT-INDEX.yaml sync
    import yaml
    index_path = AGENTS / "AGENT-INDEX.yaml"
    if index_path.exists():
        index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
        index_slugs = set()
        for section in index.values():
            if isinstance(section, dict) and "agents" in section:
                for a in section["agents"]:
                    if isinstance(a, dict):
                        index_slugs.add(a.get("slug", ""))

        # Find agents on disk not in index
        for bucket in ["external", "business"]:
            agents_dir = AGENTS / bucket
            if not agents_dir.exists():
                continue
            for agent_dir in agents_dir.iterdir():
                if agent_dir.is_dir() and (agent_dir / "AGENT.md").exists():
                    if agent_dir.name not in index_slugs:
                        results["skip_reasons"].append({
                            "slug": agent_dir.name,
                            "reason": "Agent exists on disk but NOT in AGENT-INDEX.yaml",
                            "severity": "MEDIUM",
                        })

    log.info(f"  Created: {len(results['created'])}")
    log.info(f"  Should exist but missing: {len(results['should_exist_but_missing'])}")
    log.info(f"  Skip reasons: {len(results['skip_reasons'])}")
    return results


# ============================================================================
# CHECKLIST 3: Incremento de temas
# ============================================================================
def check_3_theme_increment() -> dict:
    """Verify theme dossiers were incremented when they should have been."""
    log.info("=" * 60)
    log.info("CHECK 3: Incremento de temas")
    log.info("=" * 60)

    results = {"status": "PASS", "incremented": [], "should_increment_but_didnt": [], "skip_reasons": []}

    insights_state = load_json(ARTIFACTS / "insights" / "INSIGHTS-STATE.json")
    themes_dir = KNOWLEDGE_EXTERNAL / "dossiers" / "themes"

    # Collect themes from insights
    theme_counts: dict[str, int] = {}
    persons = insights_state.get("persons", {})
    for person_data in persons.values():
        insights_list = person_data if isinstance(person_data, list) else person_data.get("insights", [])
        for insight in insights_list:
            if not isinstance(insight, dict):
                continue
            for theme in insight.get("themes", []):
                theme_upper = theme.upper().replace(" ", "-")
                theme_counts[theme_upper] = theme_counts.get(theme_upper, 0) + 1

    # Check which themes have dossiers
    existing_dossiers = set()
    if themes_dir.exists():
        for f in themes_dir.iterdir():
            if f.name.startswith("DOSSIER-") and f.name.endswith(".md"):
                theme_name = f.name.replace("DOSSIER-", "").replace(".md", "")
                existing_dossiers.add(theme_name)
                results["incremented"].append(theme_name)

    # Themes with 5+ insights but no dossier (RULE #21 from old MB)
    for theme, count in sorted(theme_counts.items(), key=lambda x: -x[1]):
        if count >= 5 and theme not in existing_dossiers:
            results["should_increment_but_didnt"].append({
                "theme": theme,
                "insight_count": count,
                "reason": f"Theme has {count} insights (≥5 threshold) but no dossier",
                "severity": "MEDIUM",
            })

    if results["should_increment_but_didnt"]:
        results["status"] = "WARN"

    log.info(f"  Existing theme dossiers: {len(existing_dossiers)}")
    log.info(f"  Themes needing dossiers: {len(results['should_increment_but_didnt'])}")
    return results


# ============================================================================
# CHECKLIST 4: Auditoria de dossiers
# ============================================================================
def check_4_dossier_audit() -> dict:
    """Audit person and theme dossiers for completeness."""
    log.info("=" * 60)
    log.info("CHECK 4: Auditoria de dossiers")
    log.info("=" * 60)

    results = {"status": "PASS", "person_dossiers": [], "missing_person_dossiers": [],
               "theme_dossiers": [], "skip_reasons": []}

    # Check person dossiers
    for bucket_name, bucket_path in [("external", KNOWLEDGE_EXTERNAL), ("business", KNOWLEDGE_BUSINESS)]:
        persons_dir = bucket_path / "dossiers" / "persons"
        if not persons_dir.exists():
            continue
        for f in persons_dir.iterdir():
            if f.name.startswith("DOSSIER-") and f.name.endswith(".md") and "EXAMPLE" not in f.name:
                results["person_dossiers"].append({
                    "name": f.name,
                    "bucket": bucket_name,
                    "size_kb": round(f.stat().st_size / 1024, 1),
                })

    # Check which agents have dossiers
    for bucket in ["external", "business"]:
        agents_dir = AGENTS / bucket
        if not agents_dir.exists():
            continue
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir() or not (agent_dir / "AGENT.md").exists():
                continue
            slug = agent_dir.name
            expected_dossier = f"DOSSIER-{slug.upper()}.md"
            bucket_path = KNOWLEDGE_EXTERNAL if bucket == "external" else KNOWLEDGE_BUSINESS
            dossier_path = bucket_path / "dossiers" / "persons" / expected_dossier
            if not dossier_path.exists():
                results["missing_person_dossiers"].append({
                    "slug": slug,
                    "expected": str(dossier_path.relative_to(PROJECT_ROOT)),
                    "reason": "Agent exists but person dossier missing",
                    "severity": "MEDIUM",
                })

    if results["missing_person_dossiers"]:
        results["status"] = "WARN"

    log.info(f"  Person dossiers: {len(results['person_dossiers'])}")
    log.info(f"  Missing: {len(results['missing_person_dossiers'])}")
    return results


# ============================================================================
# CHECKLIST 5: Criação de novos temas e dossiers
# ============================================================================
def check_5_new_themes_dossiers() -> dict:
    """Check for newly created themes and dossiers in this wave."""
    log.info("=" * 60)
    log.info("CHECK 5: Criação de novos temas e dossiers")
    log.info("=" * 60)

    results = {"status": "PASS", "new_themes": [], "new_dossiers": []}

    # Check MCE artifacts for new creations
    mce_dir = ARTIFACTS / "mce"
    if mce_dir.exists():
        for entity_dir in mce_dir.iterdir():
            if entity_dir.is_dir():
                completion = entity_dir / "COMPLETION.json"
                if completion.exists():
                    data = load_json(completion)
                    results["new_dossiers"].append({
                        "slug": entity_dir.name,
                        "steps_completed": data.get("steps_completed", 0),
                    })

    log.info(f"  New dossiers from MCE: {len(results['new_dossiers'])}")
    return results


# ============================================================================
# CHECKLIST 6: Cascateamentos (RULE #22 from old MB)
# ============================================================================
def check_6_cascading() -> dict:
    """Validate cascading completeness — the CORE audit from old MB."""
    log.info("=" * 60)
    log.info("CHECK 6: Cascateamentos (RULE #22)")
    log.info("=" * 60)

    results = {"status": "PASS", "cascaded": [], "expected_not_cascaded": [], "skip_reasons": []}

    insights_state = load_json(ARTIFACTS / "insights" / "INSIGHTS-STATE.json")
    persons = insights_state.get("persons", {})

    for slug, person_data in persons.items():
        if isinstance(person_data, list):
            insight_count = len(person_data)
        elif isinstance(person_data, dict):
            insight_count = len(person_data.get("insights", []))
        else:
            insight_count = 0
        if insight_count < 1:
            continue

        agent_slug = slug.lower().replace(" ", "-")
        expected_destinations = []
        actual_destinations = []

        # Expected: person agent MEMORY.md should be enriched
        agent_memory = AGENTS / "external" / agent_slug / "MEMORY.md"
        expected_destinations.append(("agent_memory", str(agent_memory.relative_to(PROJECT_ROOT))))
        if agent_memory.exists():
            actual_destinations.append("agent_memory")

        # Expected: person dossier should exist/be updated
        dossier = KNOWLEDGE_EXTERNAL / "dossiers" / "persons" / f"DOSSIER-{agent_slug.upper()}.md"
        expected_destinations.append(("person_dossier", str(dossier.relative_to(PROJECT_ROOT))))
        if dossier.exists():
            actual_destinations.append("person_dossier")

        # Expected: DNA files should exist (if 3+ insights)
        if insight_count >= 3:
            dna_dir = KNOWLEDGE_EXTERNAL / "dna" / "persons" / agent_slug
            dna_files = list(dna_dir.glob("*.yaml")) if dna_dir.exists() else []
            expected_destinations.append(("dna_files", str(dna_dir.relative_to(PROJECT_ROOT))))
            if len(dna_files) >= 5:
                actual_destinations.append("dna_files")

        # Log cascading status
        missing = [d[0] for d in expected_destinations if d[0] not in actual_destinations]
        if missing:
            results["expected_not_cascaded"].append({
                "slug": slug,
                "insights": insight_count,
                "missing_destinations": missing,
                "expected": [d[1] for d in expected_destinations],
                "reason": f"Expected cascading to {missing} but not found",
                "severity": "HIGH" if "dna_files" in missing else "MEDIUM",
            })
            results["status"] = "WARN"
        else:
            results["cascaded"].append({"slug": slug, "destinations": len(expected_destinations)})

    log.info(f"  Cascaded OK: {len(results['cascaded'])}")
    log.info(f"  Missing cascading: {len(results['expected_not_cascaded'])}")
    return results


# ============================================================================
# CHECKLIST 7: Salvamento e persistência
# ============================================================================
def check_7_persistence() -> dict:
    """Verify all artifacts saved in correct locations."""
    log.info("=" * 60)
    log.info("CHECK 7: Salvamento e persistência")
    log.info("=" * 60)

    results = {"status": "PASS", "files_verified": 0, "misplaced": []}

    # Core state files
    expected_files = [
        ARTIFACTS / "chunks" / "CHUNKS-STATE.json",
        ARTIFACTS / "canonical" / "CANONICAL-MAP.json",
        ARTIFACTS / "insights" / "INSIGHTS-STATE.json",
    ]

    for f in expected_files:
        if f.exists():
            results["files_verified"] += 1
        else:
            results["misplaced"].append({
                "expected": str(f.relative_to(PROJECT_ROOT)),
                "reason": "Core state file missing",
                "severity": "HIGH",
            })

    if results["misplaced"]:
        results["status"] = "WARN"

    log.info(f"  Files verified: {results['files_verified']}")
    log.info(f"  Missing: {len(results['misplaced'])}")
    return results


# ============================================================================
# CHECKLIST 8: Criação de agente (mind-clone)
# ============================================================================
def check_8_mind_clone() -> dict:
    """Verify mind-clone agent file completeness (Template V3)."""
    log.info("=" * 60)
    log.info("CHECK 8: Criação de agente (mind-clone)")
    log.info("=" * 60)

    results = {"status": "PASS", "complete_agents": [], "incomplete_agents": []}

    required_files = ["AGENT.md", "SOUL.md", "MEMORY.md", "DNA-CONFIG.yaml", "ACTIVATION.yaml"]

    for bucket in ["external", "business"]:
        agents_dir = AGENTS / bucket
        if not agents_dir.exists():
            continue
        for agent_dir in agents_dir.rglob("AGENT.md"):
            slug_dir = agent_dir.parent
            slug = slug_dir.name
            missing = [f for f in required_files if not (slug_dir / f).exists()]
            if missing:
                results["incomplete_agents"].append({
                    "slug": slug,
                    "bucket": bucket,
                    "missing_files": missing,
                    "severity": "MEDIUM",
                })
            else:
                results["complete_agents"].append({"slug": slug, "bucket": bucket})

    if results["incomplete_agents"]:
        results["status"] = "WARN"

    log.info(f"  Complete agents: {len(results['complete_agents'])}")
    log.info(f"  Incomplete agents: {len(results['incomplete_agents'])}")
    return results


# ============================================================================
# CHECKLIST 9: Extração de DNAs
# ============================================================================
def check_9_dna_extraction() -> dict:
    """Verify DNA extraction completeness with scoring."""
    log.info("=" * 60)
    log.info("CHECK 9: Extração de DNAs")
    log.info("=" * 60)

    results = {"status": "PASS", "entities": [], "missing_dna": []}

    dna_layers = ["FILOSOFIAS.yaml", "MODELOS-MENTAIS.yaml", "HEURISTICAS.yaml",
                  "FRAMEWORKS.yaml", "METODOLOGIAS.yaml"]
    mce_layers = ["VOICE-DNA.yaml"]

    dna_root = KNOWLEDGE_EXTERNAL / "dna" / "persons"
    if not dna_root.exists():
        results["status"] = "WARN"
        return results

    for entity_dir in sorted(dna_root.iterdir()):
        if not entity_dir.is_dir() or entity_dir.name.startswith("."):
            continue

        slug = entity_dir.name
        existing = [f.name for f in entity_dir.iterdir() if f.name.endswith(".yaml")]

        # Score: how many of the 6 expected files exist
        knowledge_score = sum(1 for f in dna_layers if f in existing)
        mce_score = sum(1 for f in mce_layers if f in existing)
        total_score = knowledge_score + mce_score
        max_score = len(dna_layers) + len(mce_layers)
        pct = round(total_score / max_score * 100) if max_score > 0 else 0

        entity_result = {
            "slug": slug,
            "knowledge_layers": f"{knowledge_score}/5",
            "mce_layers": f"{mce_score}/1",
            "completeness": f"{pct}%",
            "missing": [f for f in dna_layers + mce_layers if f not in existing],
        }

        if pct == 100:
            results["entities"].append(entity_result)
        else:
            results["missing_dna"].append(entity_result)

    if results["missing_dna"]:
        results["status"] = "WARN"

    log.info(f"  Complete DNA: {len(results['entities'])}")
    log.info(f"  Incomplete DNA: {len(results['missing_dna'])}")
    for e in results["missing_dna"]:
        log.info(f"    {e['slug']}: {e['completeness']} — missing: {e['missing']}")
    return results


# ============================================================================
# CHECKLIST 10: Cobertura por camadas
# ============================================================================
def check_10_layer_coverage() -> dict:
    """Verify all 3 knowledge buckets were processed."""
    log.info("=" * 60)
    log.info("CHECK 10: Cobertura por camadas")
    log.info("=" * 60)

    results = {"status": "PASS", "layers": {}}

    for name, path in [("external", KNOWLEDGE_EXTERNAL),
                       ("business", KNOWLEDGE_BUSINESS),
                       ("personal", KNOWLEDGE_PERSONAL)]:
        inbox_files = list((path / "inbox").rglob("*")) if (path / "inbox").exists() else []
        inbox_count = len([f for f in inbox_files if f.is_file() and not f.name.startswith(".")])

        dossier_dir = path / "dossiers" / "persons"
        dossier_count = len(list(dossier_dir.glob("DOSSIER-*.md"))) if dossier_dir.exists() else 0

        dna_dir = path / "dna" / "persons" if name == "external" else None
        dna_count = 0
        if dna_dir and dna_dir.exists():
            dna_count = len([d for d in dna_dir.iterdir() if d.is_dir() and any(d.glob("*.yaml"))])

        results["layers"][name] = {
            "inbox_files": inbox_count,
            "dossiers": dossier_count,
            "dna_entities": dna_count,
            "status": "processed" if dossier_count > 0 or dna_count > 0 else "unprocessed",
        }

        if results["layers"][name]["status"] == "unprocessed" and inbox_count > 0:
            results["status"] = "WARN"

    for name, data in results["layers"].items():
        log.info(f"  {name}: inbox={data['inbox_files']}, dossiers={data['dossiers']}, "
                 f"dna={data['dna_entities']}, status={data['status']}")
    return results


# ============================================================================
# CHECKLIST 11: Diagnóstico final
# ============================================================================
def check_11_final_diagnostic(all_checks: dict) -> dict:
    """Consolidate all checks into final diagnostic."""
    log.info("=" * 60)
    log.info("CHECK 11: Diagnóstico final")
    log.info("=" * 60)

    results = {
        "overall_status": "PASS",
        "checks_passed": 0,
        "checks_warned": 0,
        "checks_failed": 0,
        "acertos": [],
        "omissoes": [],
        "bugs": [],
    }

    for check_num, check_data in all_checks.items():
        status = check_data.get("status", "UNKNOWN")
        if status == "PASS":
            results["checks_passed"] += 1
            results["acertos"].append(f"Check {check_num}: PASS")
        elif status == "WARN":
            results["checks_warned"] += 1
            results["omissoes"].append(f"Check {check_num}: WARN — has skip reasons or missing items")
        elif status == "FAIL":
            results["checks_failed"] += 1
            results["bugs"].append(f"Check {check_num}: FAIL — critical issue")
            results["overall_status"] = "FAIL"

    if results["checks_failed"] > 0:
        results["overall_status"] = "FAIL"
    elif results["checks_warned"] > 0:
        results["overall_status"] = "WARN"

    log.info(f"  PASSED: {results['checks_passed']}")
    log.info(f"  WARNED: {results['checks_warned']}")
    log.info(f"  FAILED: {results['checks_failed']}")
    log.info(f"  OVERALL: {results['overall_status']}")
    return results


# ============================================================================
# MAIN
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="Wave Post-Audit — 11-Point Checklist")
    parser.add_argument("--slug", help="Audit specific entity")
    parser.add_argument("--all", action="store_true", help="Audit everything")
    args = parser.parse_args()

    start = time.time()
    log.info("=" * 60)
    log.info("WAVE POST-AUDIT — 11-Point Checklist Validator")
    log.info(f"Started: {datetime.now(timezone.utc).isoformat()}")
    log.info("=" * 60)

    all_checks = {}

    all_checks[1] = check_1_execution_reading()
    all_checks[2] = check_2_agent_creation()
    all_checks[3] = check_3_theme_increment()
    all_checks[4] = check_4_dossier_audit()
    all_checks[5] = check_5_new_themes_dossiers()
    all_checks[6] = check_6_cascading()
    all_checks[7] = check_7_persistence()
    all_checks[8] = check_8_mind_clone()
    all_checks[9] = check_9_dna_extraction()
    all_checks[10] = check_10_layer_coverage()
    all_checks[11] = check_11_final_diagnostic(all_checks)

    elapsed = time.time() - start

    # Save report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(elapsed, 1),
        "checks": all_checks,
    }

    report_path = LOG_DIR / "POST-AUDIT-REPORT.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # Generate markdown report
    md_report = generate_markdown_report(all_checks, elapsed)
    md_path = LOG_DIR / "POST-AUDIT-REPORT.md"
    md_path.write_text(md_report, encoding="utf-8")

    log.info("")
    log.info("=" * 60)
    log.info(f"POST-AUDIT COMPLETE — {all_checks[11]['overall_status']}")
    log.info(f"  JSON: {report_path}")
    log.info(f"  MD: {md_path}")
    log.info(f"  Duration: {elapsed:.1f}s")
    log.info("=" * 60)

    # Exit code based on result
    if all_checks[11]["overall_status"] == "FAIL":
        sys.exit(1)
    sys.exit(0)


def generate_markdown_report(all_checks: dict, elapsed: float) -> str:
    """Generate human-readable markdown report."""
    diag = all_checks[11]

    report = f"""# Post-Audit Report — 11-Point Checklist

**Generated:** {datetime.now(timezone.utc).isoformat()}
**Duration:** {elapsed:.1f}s
**Overall Status:** {diag['overall_status']}

---

## Summary

| Metric | Value |
|--------|-------|
| Checks Passed | {diag['checks_passed']} |
| Checks Warned | {diag['checks_warned']} |
| Checks Failed | {diag['checks_failed']} |

---

## Results by Check

"""
    for num in range(1, 11):
        check = all_checks.get(num, {})
        status = check.get("status", "?")
        icon = {"PASS": "●", "WARN": "◐", "FAIL": "✗"}.get(status, "?")
        report += f"### Check {num} — [{icon}] {status}\n\n"

        # Add skip reasons if present
        skip_reasons = check.get("skip_reasons", []) + check.get("should_exist_but_missing", []) + \
                       check.get("expected_not_cascaded", []) + check.get("should_increment_but_didnt", []) + \
                       check.get("missing_person_dossiers", []) + check.get("incomplete_agents", []) + \
                       check.get("missing_dna", []) + check.get("misplaced", [])
        if skip_reasons:
            report += "| Item | Reason | Severity |\n|------|--------|----------|\n"
            for sr in skip_reasons[:20]:  # Limit to 20 items
                item = sr.get("slug", sr.get("theme", sr.get("expected", "?")))
                reason = sr.get("reason", "?")
                severity = sr.get("severity", "?")
                report += f"| {item} | {reason} | {severity} |\n"
            report += "\n"

    report += f"""---

## Acertos
{chr(10).join('- ' + a for a in diag['acertos'])}

## Omissões
{chr(10).join('- ' + o for o in diag['omissoes']) if diag['omissoes'] else '- Nenhuma'}

## Bugs
{chr(10).join('- ' + b for b in diag['bugs']) if diag['bugs'] else '- Nenhum'}

---

*Generated by wave-post-audit.py*
"""
    return report


if __name__ == "__main__":
    main()
