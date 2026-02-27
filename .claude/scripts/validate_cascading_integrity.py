#!/usr/bin/env python3
"""
Validate Cascading Integrity - Mega Brain Pipeline Hardening

Validates that batch cascading actually updated destination files.

Usage:
    python3 validate_cascading_integrity.py BATCH-050
    python3 validate_cascading_integrity.py BATCH-050 --json
    python3 validate_cascading_integrity.py --all
    python3 validate_cascading_integrity.py --json  # validates all batches

Exit codes:
    0 - PASSED or WARNING
    1 - FAILED
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
LOGS_PATH = PROJECT_ROOT / "logs"
BATCHES_PATH = LOGS_PATH / "batches"
AGENTS_PATH = PROJECT_ROOT / "agents"
PLAYBOOKS_PATH = PROJECT_ROOT / "knowledge" / "playbooks"
DOSSIERS_PATH = PROJECT_ROOT / "knowledge" / "dossiers"
DNA_PATH = PROJECT_ROOT / "knowledge" / "dna"
VERIFIED_LOG = LOGS_PATH / "cascading-verified.jsonl"

# ============================================================================
# DESTINATION EXTRACTION
# ============================================================================

def extract_destinations_from_batch(content: str) -> Dict[str, List[str]]:
    """
    Extract destination files from batch content.

    Parses ASCII box format with emojis:
    🤖 AGENTES A ALIMENTAR
    📘 PLAYBOOKS IMPACTADOS
    🧬 DNAs ENRIQUECIDOS
    📁 DOSSIERS

    Returns:
        Dict with keys: agents, playbooks, dnas, dossiers
    """
    destinations = {
        "agents": [],
        "playbooks": [],
        "dnas": [],
        "dossiers": []
    }

    # Pattern: Extract lines starting with • followed by filename
    # Handles both: • AGENT-SALES-LEADER.md and • DNA-CG.md (+42 elementos)
    item_pattern = re.compile(r'^\s*[•·]\s*([A-Z][A-Za-z0-9_-]+\.md|DNA-[A-Z]+\.(?:md|yaml))', re.MULTILINE)

    # Find sections
    sections = {
        "agents": ["AGENTES A ALIMENTAR", "AGENTES:", "🤖"],
        "playbooks": ["PLAYBOOKS IMPACTADOS", "PLAYBOOKS:", "📘"],
        "dnas": ["DNAs ENRIQUECIDOS", "DNA:", "🧬"],
        "dossiers": ["DOSSIERS", "📁"]
    }

    for dest_type, markers in sections.items():
        for marker in markers:
            # Find section start
            marker_idx = content.find(marker)
            if marker_idx == -1:
                continue

            # Extract text from marker to next section or box end
            section_start = marker_idx
            section_end = content.find("│", section_start + len(marker))
            if section_end == -1:
                section_end = content.find("└", section_start)
            if section_end == -1:
                section_end = len(content)

            section_text = content[section_start:section_end]

            # Extract items
            for match in item_pattern.finditer(section_text):
                filename = match.group(1).strip()
                if filename and filename not in destinations[dest_type]:
                    destinations[dest_type].append(filename)

    return destinations

# ============================================================================
# PATH RESOLUTION
# ============================================================================

def resolve_agent_path(agent_name: str) -> Optional[Path]:
    """
    Resolve agent name to MEMORY.md or AGENT.md path.

    Searches in:
    - agents/cargo/*/
    - agents/minds/*/
    - agents/boardroom/*/
    - agents/sua-empresa/*/
    """
    if not AGENTS_PATH.exists():
        return None

    # Remove extension if present
    base_name = agent_name.replace(".md", "")

    # Search patterns
    search_dirs = ["cargo", "minds", "boardroom", "sua-empresa"]

    for category in search_dirs:
        category_path = AGENTS_PATH / category
        if not category_path.exists():
            continue

        # Search in subdirectories
        for subdir in category_path.iterdir():
            if not subdir.is_dir():
                continue

            # Check MEMORY.md first (preferred)
            memory_path = subdir / "MEMORY.md"
            if memory_path.exists():
                return memory_path

            # Check AGENT.md
            agent_path = subdir / "AGENT.md"
            if agent_path.exists():
                return agent_path

    return None

def resolve_playbook_path(playbook_name: str) -> Optional[Path]:
    """Resolve playbook name to path in knowledge/playbooks/"""
    if not PLAYBOOKS_PATH.exists():
        return None

    # Try exact match
    exact = PLAYBOOKS_PATH / playbook_name
    if exact.exists():
        return exact

    # Try pattern match
    pattern = playbook_name.replace(".md", "")
    for path in PLAYBOOKS_PATH.glob(f"{pattern}*.md"):
        return path

    return None

def resolve_dossier_path(dossier_name: str) -> Optional[Path]:
    """Resolve dossier name to path in knowledge/dossiers/**/"""
    if not DOSSIERS_PATH.exists():
        return None

    # Try exact match in any subdirectory
    pattern = dossier_name.replace(".md", "")
    for path in DOSSIERS_PATH.rglob(f"{pattern}*.md"):
        return path

    return None

def resolve_dna_path(dna_name: str) -> Optional[Path]:
    """Resolve DNA name to path in knowledge/dna/persons/*/DNA.yaml"""
    if not DNA_PATH.exists():
        return None

    # Extract person code (e.g., DNA-CG.md -> CG)
    match = re.match(r'DNA-([A-Z]+)', dna_name)
    if not match:
        return None

    person_code = match.group(1).lower()

    # Search in persons directory
    persons_path = DNA_PATH / "persons"
    if not persons_path.exists():
        return None

    for person_dir in persons_path.iterdir():
        if not person_dir.is_dir():
            continue

        if person_code in person_dir.name.lower():
            dna_file = person_dir / "DNA.yaml"
            if dna_file.exists():
                return dna_file

    return None

# ============================================================================
# VALIDATION LOGIC
# ============================================================================

def check_file_references_batch(file_path: Path, batch_id: str) -> bool:
    """Check if file content references the batch ID."""
    try:
        content = file_path.read_text(encoding='utf-8')
        return batch_id in content
    except Exception:
        return False

def validate_batch_integrity(batch_id: str) -> Dict:
    """
    Validate cascading integrity for a batch.

    Returns:
        Dict with: status, batch_id, errors, warnings, destinations_detail
    """
    result = {
        "batch_id": batch_id,
        "status": "PASSED",
        "errors": [],
        "warnings": [],
        "destinations_total": 0,
        "destinations_detail": {
            "agents": [],
            "playbooks": [],
            "dnas": [],
            "dossiers": []
        },
        "validated_at": datetime.now().isoformat()
    }

    # Normalize batch ID
    if not batch_id.startswith("BATCH-"):
        batch_id = f"BATCH-{batch_id}"

    # Find batch file
    batch_path = None
    for pattern in [f"{batch_id}.md", f"{batch_id}-*.md"]:
        matches = list(BATCHES_PATH.glob(pattern))
        if matches:
            batch_path = matches[0]
            break

    if not batch_path:
        result["status"] = "FAILED"
        result["errors"].append(f"Batch file not found: {batch_id}")
        return result

    # Read batch content
    try:
        content = batch_path.read_text(encoding='utf-8')
    except Exception as e:
        result["status"] = "FAILED"
        result["errors"].append(f"Failed to read batch file: {e}")
        return result

    # Check for cascading section
    if "Cascateamento Executado" not in content and "DESTINO DO CONHECIMENTO" not in content:
        result["status"] = "WARNING"
        result["warnings"].append("No cascading section found in batch")
        return result

    # Extract destinations
    destinations = extract_destinations_from_batch(content)

    # Count total
    result["destinations_total"] = sum(len(v) for v in destinations.values())

    if result["destinations_total"] == 0:
        result["status"] = "WARNING"
        result["warnings"].append("No destinations extracted from batch")
        return result

    # Validate each destination
    resolvers = {
        "agents": resolve_agent_path,
        "playbooks": resolve_playbook_path,
        "dnas": resolve_dna_path,
        "dossiers": resolve_dossier_path
    }

    for dest_type, dest_list in destinations.items():
        resolver = resolvers[dest_type]

        for dest_name in dest_list:
            dest_path = resolver(dest_name)

            detail = {
                "name": dest_name,
                "exists": dest_path is not None,
                "references_batch": False,
                "path": str(dest_path) if dest_path else None
            }

            if dest_path is None:
                result["warnings"].append(f"{dest_type.capitalize()} not found: {dest_name}")
            else:
                detail["references_batch"] = check_file_references_batch(dest_path, batch_id)
                if not detail["references_batch"]:
                    result["warnings"].append(f"{dest_type.capitalize()} exists but doesn't reference batch: {dest_name}")

            result["destinations_detail"][dest_type].append(detail)

    # Determine final status
    if result["errors"]:
        result["status"] = "FAILED"
    elif result["warnings"]:
        result["status"] = "WARNING"

    return result

def validate_all_batches() -> Dict:
    """Validate all batches and return summary."""
    if not BATCHES_PATH.exists():
        return {
            "status": "FAILED",
            "error": "Batches directory not found",
            "total": 0
        }

    batches = list(BATCHES_PATH.glob("BATCH-*.md"))

    summary = {
        "total": len(batches),
        "passed": 0,
        "warning": 0,
        "failed": 0,
        "validated_at": datetime.now().isoformat(),
        "details": []
    }

    for batch_path in batches:
        batch_id = batch_path.stem
        result = validate_batch_integrity(batch_id)

        if result["status"] == "PASSED":
            summary["passed"] += 1
        elif result["status"] == "WARNING":
            summary["warning"] += 1
        else:
            summary["failed"] += 1

        summary["details"].append({
            "batch_id": result["batch_id"],
            "status": result["status"],
            "destinations": result["destinations_total"],
            "errors": len(result["errors"]),
            "warnings": len(result["warnings"])
        })

    return summary

# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """CLI entry point."""
    args = sys.argv[1:]

    json_output = "--json" in args
    if json_output:
        args.remove("--json")

    validate_all = "--all" in args or len(args) == 0

    if validate_all:
        # Validate all batches
        summary = validate_all_batches()

        if json_output:
            print(json.dumps(summary, indent=2))
        else:
            print(f"Validating all batches...")
            print(f"Total: {summary['total']}")
            print(f"PASSED: {summary['passed']}")
            print(f"WARNING: {summary['warning']}")
            print(f"FAILED: {summary['failed']}")

        sys.exit(0 if summary["failed"] == 0 else 1)

    else:
        # Validate single batch
        batch_id = args[0]
        result = validate_batch_integrity(batch_id)

        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Batch: {result['batch_id']}")
            print(f"Status: {result['status']}")
            print(f"Destinations: {result['destinations_total']}")
            if result['errors']:
                print(f"\nErrors:")
                for error in result['errors']:
                    print(f"  - {error}")
            if result['warnings']:
                print(f"\nWarnings:")
                for warning in result['warnings']:
                    print(f"  - {warning}")

        sys.exit(0 if result["status"] != "FAILED" else 1)

if __name__ == "__main__":
    main()
