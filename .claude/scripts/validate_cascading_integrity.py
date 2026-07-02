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
# C-17-PATH fix (2026-05-12): batch_auto_creator writes to .data/logs/batches/
# (canonical via engine.paths.LOGS), not logs/batches/. Update validator to match.
# Falls back to logs/ for legacy compatibility.
LOGS_PATH = PROJECT_ROOT / ".data" / "logs"
if not LOGS_PATH.exists():
    LOGS_PATH = PROJECT_ROOT / "logs"  # legacy fallback
BATCHES_PATH = LOGS_PATH / "batches"
AGENTS_PATH = PROJECT_ROOT / "agents"

# C-20 fix (2026-05-12): Validator was only checking knowledge/external/.
# Per Constitution Art. XIII (3 isolated buckets), validator MUST also resolve
# paths in business and personal buckets. Now uses multi-bucket lookup.
KNOWLEDGE_BUCKETS_PATHS = {
    "external": PROJECT_ROOT / "knowledge" / "external",
    "business": PROJECT_ROOT / "knowledge" / "business",
    "personal": PROJECT_ROOT / "knowledge" / "personal",
}
# Legacy single-bucket vars (kept for backward compat with code that imports them)
PLAYBOOKS_PATH = PROJECT_ROOT / "knowledge" / "external" / "playbooks"
DOSSIERS_PATH = PROJECT_ROOT / "knowledge" / "external" / "dossiers"
DNA_PATH = PROJECT_ROOT / "knowledge" / "external" / "dna"
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
    # C-17 fix (2026-05-12): widened regex to accept kebab-case + path separators
    # (real-world filenames). Was: r'^\s*[•·]\s*([A-Z][A-Za-z0-9_-]+\.md|DNA-[A-Z]+\.(?:md|yaml))'
    # Now accepts: AGENT-SALES-LEADER.md, DNA-CG.md, alex-hormozi/MEMORY.md,
    #   dossier-jeremy-miner.md, knowledge/external/dna/persons/x/voice-dna.yaml
    item_pattern = re.compile(
        r'^\s*[•·]\s*([A-Za-z][\w./-]*\.(?:md|yaml|json))',
        re.MULTILINE,
    )

    # Find sections
    sections = {
        "agents": ["AGENTES A ALIMENTAR", "AGENTES:", "🤖"],
        "playbooks": ["PLAYBOOKS IMPACTADOS", "PLAYBOOKS:", "📘"],
        "dnas": ["DNAs ENRIQUECIDOS", "DNA:", "🧬"],
        "dossiers": ["DOSSIERS", "📁"]
    }

    # C-17 fix (2026-05-12): compute proper section boundaries using NEXT
    # section marker, not ASCII box character. Box chars are absent in markdown
    # batches, which caused section text to bleed across markers and produce
    # false-positives in every section.
    all_marker_idxs = []
    for dest_type, markers in sections.items():
        for marker in markers:
            idx = content.find(marker)
            if idx != -1:
                all_marker_idxs.append((idx, dest_type, marker))
    all_marker_idxs.sort()

    for i, (start_idx, dest_type, marker) in enumerate(all_marker_idxs):
        # Boundary: next marker OR ASCII box-end OR end of content
        next_start = all_marker_idxs[i + 1][0] if i + 1 < len(all_marker_idxs) else len(content)
        box_end = content.find("│", start_idx + len(marker))
        if box_end == -1:
            box_end = content.find("└", start_idx)
        if box_end == -1 or box_end > next_start:
            box_end = next_start

        section_text = content[start_idx:box_end]

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

    C-20 fix (2026-05-12): Updated to match REAL agent categories on disk,
    not legacy aspirational ones. Was searching cargo/external/boardroom/
    sua-empresa (legacy); now searches business/business-masters/discovery/
    external/personal/system/cargo (cargo kept for legacy fallback).

    Searches in:
    - agents/business/*/        (Tier 1: business knowledge agents)
    - agents/business-masters/*/ (Tier 2: composite agents)
    - agents/discovery/*/       (Tier 3: discovery agents)
    - agents/external/*/        (External expert mind clones)
    - agents/personal/*/        (Founder/personal agents)
    - agents/system/*/          (System agents: JARVIS, Conclave)
    - agents/cargo/*/           (Legacy cargo agents, fallback)

    Also matches by name (filename stem) when subdir match yields nothing —
    e.g. "AGENT-CG.md" should resolve to alex-hormozi/AGENT.md if "CG" is
    in the directory name.
    """
    if not AGENTS_PATH.exists():
        return None

    # C-20: real categories on disk (verified 2026-05-12)
    search_dirs = [
        "business",
        "business-masters",
        "discovery",
        "external",
        "personal",
        "system",
        "cargo",  # legacy fallback
    ]

    # C-20 path-style support: handle refs like "acme/MEMORY.md" or
    # "alex-hormozi/AGENT.md" — split into agent_dir + file_name, search
    # for {category}/{agent_dir}/{file_name} across all categories.
    if "/" in agent_name:
        agent_dir, file_name = agent_name.split("/", 1)
        agent_dir_lower = agent_dir.lower()
        # Pass A: exact match
        for category in search_dirs:
            category_path = AGENTS_PATH / category
            if not category_path.exists():
                continue
            for subdir in category_path.iterdir():
                if not subdir.is_dir():
                    continue
                if subdir.name.lower() == agent_dir_lower:
                    target = subdir / file_name
                    if target.exists():
                        return target
        # Pass B: substring match on agent_dir
        for category in search_dirs:
            category_path = AGENTS_PATH / category
            if not category_path.exists():
                continue
            for subdir in category_path.iterdir():
                if not subdir.is_dir():
                    continue
                if agent_dir_lower in subdir.name.lower():
                    target = subdir / file_name
                    if target.exists():
                        return target
        return None

    # Remove extension if present (plain-name path)
    base_name = agent_name.replace(".md", "").replace(".yaml", "")

    # Pass 1: direct match — agent_name == subdir name OR file == agent_name
    for category in search_dirs:
        category_path = AGENTS_PATH / category
        if not category_path.exists():
            continue

        for subdir in category_path.iterdir():
            if not subdir.is_dir():
                continue

            # Direct file match: e.g. "MEMORY.md", "AGENT.md", "SOUL.md"
            direct_file = subdir / agent_name
            if direct_file.exists():
                return direct_file

            # Subdir name match (e.g. base_name="alex-hormozi" matches subdir)
            if subdir.name.lower() == base_name.lower():
                # Check MEMORY.md first (preferred)
                memory_path = subdir / "MEMORY.md"
                if memory_path.exists():
                    return memory_path
                agent_path = subdir / "AGENT.md"
                if agent_path.exists():
                    return agent_path

    # Pass 2: fallback — return first MEMORY/AGENT found anywhere matching slug
    for category in search_dirs:
        category_path = AGENTS_PATH / category
        if not category_path.exists():
            continue

        for subdir in category_path.iterdir():
            if not subdir.is_dir():
                continue

            # Slug substring match (e.g. "CG" in "cole-gordon")
            if base_name.lower() in subdir.name.lower():
                memory_path = subdir / "MEMORY.md"
                if memory_path.exists():
                    return memory_path
                agent_path = subdir / "AGENT.md"
                if agent_path.exists():
                    return agent_path

    return None

def resolve_playbook_path(playbook_name: str) -> Optional[Path]:
    """Resolve playbook name to path across ALL 3 knowledge buckets.

    C-20 fix (2026-05-12): Was searching only knowledge/external/playbooks/.
    Now searches external + business + personal per Art. XIII bucket isolation.
    Pass 1: exact match. Pass 2: glob pattern (handles versioned playbooks).
    """
    pattern = playbook_name.replace(".md", "")

    # Pass 1: exact match in each bucket
    for bucket_name, bucket_root in KNOWLEDGE_BUCKETS_PATHS.items():
        playbooks_dir = bucket_root / "playbooks"
        if not playbooks_dir.exists():
            continue
        exact = playbooks_dir / playbook_name
        if exact.exists():
            return exact

    # Pass 2: glob pattern match
    for bucket_name, bucket_root in KNOWLEDGE_BUCKETS_PATHS.items():
        playbooks_dir = bucket_root / "playbooks"
        if not playbooks_dir.exists():
            continue
        for path in playbooks_dir.rglob(f"{pattern}*.md"):
            return path

    return None

def resolve_dossier_path(dossier_name: str) -> Optional[Path]:
    """Resolve dossier name to path across ALL 3 knowledge buckets.

    C-20 fix (2026-05-12): Was searching only knowledge/external/dossiers/.
    Now searches external + business + personal per Art. XIII.
    Each bucket may have dossiers/persons/, dossiers/themes/, etc.

    Case-insensitive: dossier-cole-gordon.md matches DOSSIER-COLE-GORDON.md
    (APFS volumes are case-insensitive by default; this normalizes comparison
    regardless of OS).
    """
    target_lower = dossier_name.lower()
    pattern_lower = dossier_name.replace(".md", "").lower()

    # Pass 1: case-insensitive exact match anywhere under dossiers/
    for bucket_name, bucket_root in KNOWLEDGE_BUCKETS_PATHS.items():
        dossiers_dir = bucket_root / "dossiers"
        if not dossiers_dir.exists():
            continue
        for path in dossiers_dir.rglob("*.md"):
            if path.is_file() and path.name.lower() == target_lower:
                return path

    # Pass 2: case-insensitive prefix match (handles versioned dossiers)
    for bucket_name, bucket_root in KNOWLEDGE_BUCKETS_PATHS.items():
        dossiers_dir = bucket_root / "dossiers"
        if not dossiers_dir.exists():
            continue
        for path in dossiers_dir.rglob("*.md"):
            if path.is_file() and path.name.lower().startswith(pattern_lower):
                return path

    return None

def resolve_dna_path(dna_name: str) -> Optional[Path]:
    """Resolve DNA name to path across ALL 3 knowledge buckets.

    C-20 fix (2026-05-12): Was searching only knowledge/external/dna/persons/.
    Now searches external + business + personal per Art. XIII.

    Accepts multiple naming conventions:
    - "DNA-CG.md"  → match by code "CG" in subdir name
    - "alex-hormozi/DNA-CONFIG.yaml" → match path components
    - "voice-dna.yaml" / "behavioral-patterns.yaml" → match file directly
    - "DNA-acme.md" → match by subdir name token
    """
    # Strip extension for code-style matches
    stem = dna_name.replace(".md", "").replace(".yaml", "").replace(".yml", "")

    # Case A: path-style ref (contains "/") — match path components in each bucket
    if "/" in dna_name:
        leading_dir = dna_name.split("/", 1)[0].lower()
        tail = Path(dna_name).name

        # Pass 1: exact path under dna/ in each bucket (preserves leading dir)
        for bucket_name, bucket_root in KNOWLEDGE_BUCKETS_PATHS.items():
            dna_root = bucket_root / "dna"
            if not dna_root.exists():
                continue
            candidate = dna_root / dna_name
            if candidate.exists():
                return candidate

        # Pass 2: search under persons/{leading_dir}/ — preserves bucket+leading dir
        for bucket_name, bucket_root in KNOWLEDGE_BUCKETS_PATHS.items():
            dna_root = bucket_root / "dna"
            if not dna_root.exists():
                continue
            persons_path = dna_root / "persons"
            if persons_path.exists():
                for person_dir in persons_path.iterdir():
                    if person_dir.is_dir() and person_dir.name.lower() == leading_dir:
                        target = person_dir / tail
                        if target.exists():
                            return target

        # Pass 3: rglob fallback for the filename anywhere under dna/
        for bucket_name, bucket_root in KNOWLEDGE_BUCKETS_PATHS.items():
            dna_root = bucket_root / "dna"
            if not dna_root.exists():
                continue
            for path in dna_root.rglob(tail):
                if path.is_file():
                    return path
        return None

    # Case B: plain filename (no slash) — match across buckets
    # Extract person code from DNA-XX.md style names
    code_match = re.match(r'DNA-([A-Za-z0-9]+)', stem)
    person_code = code_match.group(1).lower() if code_match else stem.lower()

    for bucket_name, bucket_root in KNOWLEDGE_BUCKETS_PATHS.items():
        dna_root = bucket_root / "dna"
        if not dna_root.exists():
            continue

        # Pass 1: exact filename match anywhere under dna/
        for path in dna_root.rglob(dna_name):
            if path.is_file():
                return path

        # Pass 2: persons/ subtree — match by code in dir name
        persons_path = dna_root / "persons"
        if persons_path.exists():
            for person_dir in persons_path.iterdir():
                if not person_dir.is_dir():
                    continue
                if person_code in person_dir.name.lower():
                    # Prefer canonical names in order of priority
                    for candidate_name in ("DNA.yaml", "DNA-CONFIG.yaml", "voice-dna.yaml"):
                        dna_file = person_dir / candidate_name
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
