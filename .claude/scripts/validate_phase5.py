#!/usr/bin/env python3
"""Phase 5 Validation Script for Mega Brain Pipeline.

Validates that Phase 5 (Agent Construction) is complete by checking:
1. DNA aggregation files exist
2. Theme dossiers are current (not outdated vs batches)
3. Person agents have required files (AGENT.md, SOUL.md, MEMORY.md, DNA-CONFIG.yaml)
4. Each person agent has a matching DNA directory

Usage:
    python3 .claude/scripts/validate_phase5.py          # Check only
    python3 .claude/scripts/validate_phase5.py --fix     # Check and report fixes needed
    python3 .claude/scripts/validate_phase5.py --verbose  # Detailed output

Exit codes:
    0 = PASSED (Phase 5 ready to close)
    1 = FAILED (issues found, cannot close Phase 5)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

# Allow overriding via env var for testing
_env_root = os.environ.get("MEGA_BRAIN_ROOT")
PROJECT_ROOT = Path(_env_root) if _env_root else Path(__file__).resolve().parent.parent.parent

KNOWLEDGE_EXTERNAL = PROJECT_ROOT / "knowledge" / "external"
AGENTS_EXTERNAL = PROJECT_ROOT / "agents" / "external"
DNA_PERSONS = KNOWLEDGE_EXTERNAL / "dna" / "persons"
DOSSIERS_PERSONS = KNOWLEDGE_EXTERNAL / "dossiers" / "persons"
DOSSIERS_THEMES = KNOWLEDGE_EXTERNAL / "dossiers" / "themes"
LOGS_BATCHES = PROJECT_ROOT / "logs" / "batches"

REQUIRED_AGENT_FILES = ["AGENT.md", "SOUL.md", "MEMORY.md", "DNA-CONFIG.yaml"]


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


def check_agent_completeness(verbose: bool = False) -> list[dict]:
    """Check that each person agent has all required files."""
    issues: list[dict] = []

    if not AGENTS_EXTERNAL.exists():
        issues.append(
            {
                "type": "CRITICAL",
                "message": "agents/external/ directory not found",
                "fix": "Create agents/external/ directory",
            }
        )
        return issues

    for agent_dir in sorted(AGENTS_EXTERNAL.iterdir()):
        if not agent_dir.is_dir() or agent_dir.name.startswith(("_", ".")):
            continue

        missing = [f for f in REQUIRED_AGENT_FILES if not (agent_dir / f).exists()]

        if missing:
            issues.append(
                {
                    "type": "HIGH",
                    "agent": agent_dir.name,
                    "message": f"Missing: {', '.join(missing)}",
                    "fix": f"Create missing files in agents/external/{agent_dir.name}/",
                }
            )
        elif verbose:
            print(f"  OK: {agent_dir.name} -- all {len(REQUIRED_AGENT_FILES)} files present")

    return issues


def check_dna_exists(verbose: bool = False) -> list[dict]:
    """Check that DNA schemas exist for each person agent."""
    issues: list[dict] = []

    if not DNA_PERSONS.exists():
        issues.append(
            {
                "type": "CRITICAL",
                "message": "knowledge/external/dna/persons/ not found",
                "fix": "Create DNA directory structure",
            }
        )
        return issues

    if AGENTS_EXTERNAL.exists():
        for agent_dir in sorted(AGENTS_EXTERNAL.iterdir()):
            if not agent_dir.is_dir() or agent_dir.name.startswith(("_", ".")):
                continue

            dna_dir = DNA_PERSONS / agent_dir.name
            if not dna_dir.exists():
                issues.append(
                    {
                        "type": "HIGH",
                        "agent": agent_dir.name,
                        "message": f"No DNA directory at knowledge/external/dna/persons/{agent_dir.name}/",
                        "fix": f"Run DNA extraction for {agent_dir.name}",
                    }
                )
            elif verbose:
                yaml_count = len(list(dna_dir.glob("*.yaml")))
                print(f"  OK: {agent_dir.name} DNA -- {yaml_count} YAML files")

    return issues


def check_dossiers_current(verbose: bool = False) -> list[dict]:
    """Check that theme and person dossiers exist.

    When batch logs are available, compares dossier modification dates
    against latest batch dates to detect outdated dossiers (RULE #21).
    """
    issues: list[dict] = []

    # Find latest batch modification time (if batches exist)
    latest_batch_mtime: float | None = None
    if LOGS_BATCHES.exists():
        batch_files = list(LOGS_BATCHES.glob("BATCH-*.md"))
        if batch_files:
            latest_batch_mtime = max(f.stat().st_mtime for f in batch_files)

    for dossier_dir, label in [
        (DOSSIERS_PERSONS, "person"),
        (DOSSIERS_THEMES, "theme"),
    ]:
        if not dossier_dir.exists():
            issues.append(
                {
                    "type": "MEDIUM",
                    "message": f"{label} dossiers directory not found: {dossier_dir.relative_to(PROJECT_ROOT)}",
                    "fix": f"Create {label} dossiers from processed batches",
                }
            )
            continue

        dossier_files = list(dossier_dir.glob("*.md"))
        dossier_count = len(dossier_files)

        if dossier_count == 0:
            issues.append(
                {
                    "type": "MEDIUM",
                    "message": f"Zero {label} dossiers in {dossier_dir.relative_to(PROJECT_ROOT)}/",
                    "fix": f"Create {label} dossiers from processed batches",
                }
            )
            continue

        if verbose:
            print(f"  OK: {dossier_count} {label} dossier(s) found")

        # RULE #21 enforcement: check dossier freshness vs batches
        if latest_batch_mtime is not None:
            for dossier_file in sorted(dossier_files):
                dossier_mtime = dossier_file.stat().st_mtime
                if dossier_mtime < latest_batch_mtime:
                    issues.append(
                        {
                            "type": "HIGH",
                            "message": (
                                f"Outdated {label} dossier: {dossier_file.name} "
                                f"(dossier older than latest batch)"
                            ),
                            "fix": f"Update {dossier_file.name} with knowledge from recent batches",
                        }
                    )
                elif verbose:
                    print(f"  OK: {dossier_file.name} -- up to date")

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def validate_phase5(verbose: bool = False, fix: bool = False) -> int:
    """Run all Phase 5 validations.

    Returns:
        0 if PASSED, 1 if FAILED.
    """
    print("=" * 60)
    print("  PHASE 5 VALIDATION")
    print("=" * 60)
    print()

    all_issues: list[dict] = []

    # Check 1: Agent completeness
    print("[1/3] Checking agent completeness...")
    issues = check_agent_completeness(verbose)
    all_issues.extend(issues)
    status = "PASS" if not issues else f"FAIL -- {len(issues)} issue(s)"
    print(f"  {status}")
    print()

    # Check 2: DNA existence
    print("[2/3] Checking DNA schemas...")
    issues = check_dna_exists(verbose)
    all_issues.extend(issues)
    status = "PASS" if not issues else f"FAIL -- {len(issues)} issue(s)"
    print(f"  {status}")
    print()

    # Check 3: Dossiers current
    print("[3/3] Checking dossiers...")
    issues = check_dossiers_current(verbose)
    all_issues.extend(issues)
    status = "PASS" if not issues else f"FAIL -- {len(issues)} issue(s)"
    print(f"  {status}")
    print()

    # Summary
    print("=" * 60)
    critical = sum(1 for i in all_issues if i.get("type") == "CRITICAL")
    high = sum(1 for i in all_issues if i.get("type") == "HIGH")
    medium = sum(1 for i in all_issues if i.get("type") == "MEDIUM")

    if not all_issues:
        print("  RESULT: PASSED")
        print("  Phase 5 is ready to close.")
        return 0

    print("  RESULT: FAILED")
    print(f"  Issues: {critical} CRITICAL, {high} HIGH, {medium} MEDIUM")
    print()

    if fix:
        print("  FIXES NEEDED:")
        for i, issue in enumerate(all_issues, 1):
            agent_str = f" [{issue.get('agent', '')}]" if issue.get("agent") else ""
            print(f"  {i}. [{issue['type']}]{agent_str} {issue['message']}")
            print(f"     Fix: {issue['fix']}")
        print()

    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate Phase 5 completion")
    parser.add_argument("--fix", action="store_true", help="Show detailed fix instructions")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")
    args = parser.parse_args()

    exit_code = validate_phase5(verbose=args.verbose, fix=args.fix)
    sys.exit(exit_code)
