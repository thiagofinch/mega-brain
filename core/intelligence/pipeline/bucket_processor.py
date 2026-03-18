#!/usr/bin/env python3
"""
BUCKET PROCESSOR — Unified 3-Layer Knowledge Ingest
====================================================
Processes files from any of the 3 knowledge buckets:
  - external  (Bucket 1): Expert materials → dna, dossiers, playbooks
  - workspace (Bucket 2): Business data → _org, _finance, _meetings, _team
  - personal  (Bucket 3): Cognitive/private → _email, _calls, _cognitive

Each bucket has its own inbox/ with typed subdirectories.
Files are classified, extracted, and routed to the correct destination.

Version: 1.0.0
Date: 2026-03-06
"""

import json
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from core.paths import (
    KNOWLEDGE_EXTERNAL,
    KNOWLEDGE_PERSONAL,
    LOGS,
    PERSONAL_CALLS,
    PERSONAL_COGNITIVE,
    PERSONAL_EMAIL,
    PERSONAL_MESSAGES,
    ROUTING,
    WORKSPACE,
    WORKSPACE_AUTOMATIONS,
    WORKSPACE_FINANCE,
    WORKSPACE_MEETINGS,
    WORKSPACE_ORG,
    WORKSPACE_TEAM,
    WORKSPACE_TOOLS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# BUCKET DEFINITIONS
# ---------------------------------------------------------------------------

BUCKETS = {
    "external": {
        "path": KNOWLEDGE_EXTERNAL,
        "inbox": ROUTING["external_inbox"],
        "color": "blue",
        "label": "Expert Knowledge",
        "layer": "L2",
        "subdirs": {
            "dna": KNOWLEDGE_EXTERNAL / "dna",
            "dossiers": KNOWLEDGE_EXTERNAL / "dossiers",
            "playbooks": KNOWLEDGE_EXTERNAL / "playbooks",
            "sources": KNOWLEDGE_EXTERNAL / "sources",
        },
    },
    "workspace": {
        "path": WORKSPACE,
        "inbox": ROUTING["workspace_inbox"],
        "color": "red",
        "label": "Business Intelligence",
        "layer": "L2/L3",
        "subdirs": {
            "org": WORKSPACE_ORG,
            "team": WORKSPACE_TEAM,
            "finance": WORKSPACE_FINANCE,
            "meetings": WORKSPACE_MEETINGS,
            "automations": WORKSPACE_AUTOMATIONS,
            "tools": WORKSPACE_TOOLS,
        },
    },
    "personal": {
        "path": KNOWLEDGE_PERSONAL,
        "inbox": ROUTING["personal_inbox"],
        "color": "green",
        "label": "Cognitive Layer",
        "layer": "L3",
        "subdirs": {
            "email": PERSONAL_EMAIL,
            "messages": PERSONAL_MESSAGES,
            "calls": PERSONAL_CALLS,
            "cognitive": PERSONAL_COGNITIVE,
        },
    },
}


# ---------------------------------------------------------------------------
# CLASSIFICATION
# ---------------------------------------------------------------------------

# Workspace classification patterns
WORKSPACE_PATTERNS = {
    "org": [
        r"organograma",
        r"org\s*chart",
        r"hierarquia",
        r"estrutura.*time",
        r"headcount",
        r"departamento",
    ],
    "team": [
        r"cargo",
        r"role",
        r"job\s*description",
        r"\bJD\b",
        r"contrata",
        r"requisitos.*vaga",
        r"onboarding",
    ],
    "finance": [
        r"\bMRR\b",
        r"\bCAC\b",
        r"\bLTV\b",
        r"\bchurn\b",
        r"receita",
        r"faturamento",
        r"\bDRE\b",
        r"P&L",
        r"fluxo.*caixa",
        r"cash\s*flow",
        r"budget",
        r"custo\s*fixo",
    ],
    "meetings": [
        r"reuni[aã]o",
        r"meeting",
        r"call\b",
        r"standup",
        r"daily",
        r"retrospectiva",
        r"1[:\-]1",
        r"one.*on.*one",
        r"ata\b",
    ],
    "automations": [
        r"automa[çc][aã]o",
        r"\bn8n\b",
        r"zapier",
        r"make\.com",
        r"workflow",
        r"integra[çc][aã]o",
    ],
    "tools": [
        r"\bCRM\b",
        r"ferramenta",
        r"software",
        r"plataforma",
        r"clickup",
        r"notion",
        r"slack",
        r"hubspot",
    ],
}

# Personal classification patterns
PERSONAL_PATTERNS = {
    "email": [
        r"email",
        r"e-mail",
        r"inbox",
        r"newsletter",
        r"digest",
    ],
    "messages": [
        r"whatsapp",
        r"telegram",
        r"mensagem",
        r"chat\b",
        r"DM\b",
        r"direct\s*message",
    ],
    "calls": [
        r"liga[çc][aã]o",
        r"call\b",
        r"telefonema",
        r"grava[çc][aã]o",
        r"transcri[çc][aã]o.*call",
    ],
    "cognitive": [
        r"reflex[aã]o",
        r"journal",
        r"di[áa]rio",
        r"insight.*pessoal",
        r"nota.*mental",
        r"observa[çc][aã]o",
        r"aprendizado",
        r"sa[uú]de",
        r"health",
        r"rela[çc]",
        r"growth",
    ],
}


def classify_content(text: str, bucket: str) -> str:
    """Classify content into a subdirectory based on keyword patterns.

    Args:
        text: Content to classify (first 2000 chars used).
        bucket: One of 'external', 'workspace', 'personal'.

    Returns:
        Subdirectory name (e.g., 'finance', 'meetings', 'cognitive').
    """
    sample = text[:2000].lower()

    if bucket == "workspace":
        patterns = WORKSPACE_PATTERNS
    elif bucket == "personal":
        patterns = PERSONAL_PATTERNS
    else:
        return "sources"  # external defaults to sources/

    scores: dict[str, int] = {}
    for category, regexes in patterns.items():
        score = sum(1 for r in regexes if re.search(r, sample, re.IGNORECASE))
        if score > 0:
            scores[category] = score

    if not scores:
        # Default per bucket
        defaults = {"workspace": "meetings", "personal": "cognitive"}
        return defaults.get(bucket, "sources")

    return max(scores, key=scores.get)


# ---------------------------------------------------------------------------
# INBOX SCANNER
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".yaml", ".yml", ".csv", ".docx", ".pdf"}


def scan_inbox(bucket: str) -> list[dict]:
    """Scan a bucket's inbox for unprocessed files.

    Args:
        bucket: One of 'external', 'workspace', 'personal'.

    Returns:
        List of dicts with file metadata.
    """
    config = BUCKETS[bucket]
    inbox_path = config["inbox"]
    files = []

    if not inbox_path.exists():
        logger.warning("Inbox path does not exist: %s", inbox_path)
        return files

    for filepath in inbox_path.rglob("*"):
        if not filepath.is_file():
            continue
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if filepath.name.startswith("."):
            continue

        # Determine inbox subfolder (e.g., inbox/meetings/file.txt → "meetings")
        rel = filepath.relative_to(inbox_path)
        inbox_subfolder = rel.parts[0] if len(rel.parts) > 1 else ""

        files.append(
            {
                "path": filepath,
                "name": filepath.name,
                "size": filepath.stat().st_size,
                "extension": filepath.suffix.lower(),
                "inbox_subfolder": inbox_subfolder,
                "bucket": bucket,
            }
        )

    return sorted(files, key=lambda f: f["name"])


# ---------------------------------------------------------------------------
# FILE READER
# ---------------------------------------------------------------------------


def read_file_content(filepath: Path) -> str:
    """Read text content from a file.

    Args:
        filepath: Path to the file.

    Returns:
        Text content (empty string on failure).
    """
    try:
        if filepath.suffix.lower() in {".txt", ".md", ".csv"}:
            return filepath.read_text(encoding="utf-8")
        elif filepath.suffix.lower() in {".json"}:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif filepath.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(filepath.read_text(encoding="utf-8"))
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        else:
            logger.warning("Unsupported file type for reading: %s", filepath.suffix)
            return ""
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as e:
        logger.warning("Failed to read %s: %s", filepath, e)
        return ""


# ---------------------------------------------------------------------------
# PROCESSOR
# ---------------------------------------------------------------------------


def process_file(file_meta: dict) -> dict:
    """Process a single file from an inbox.

    Args:
        file_meta: Dict from scan_inbox with file metadata.

    Returns:
        Processing result dict.
    """
    filepath = file_meta["path"]
    bucket = file_meta["bucket"]
    config = BUCKETS[bucket]

    content = read_file_content(filepath)
    if not content:
        return {
            "status": "skipped",
            "reason": "empty or unreadable",
            "file": str(filepath),
        }

    # Classify: use inbox subfolder as hint, or auto-classify
    if file_meta["inbox_subfolder"] and file_meta["inbox_subfolder"] in config["subdirs"]:
        category = file_meta["inbox_subfolder"]
    else:
        category = classify_content(content, bucket)

    # Destination
    dest_dir = config["subdirs"].get(category, config["path"])
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / filepath.name

    # Write to destination
    dest_file.write_text(content, encoding="utf-8")

    return {
        "status": "processed",
        "file": str(filepath),
        "bucket": bucket,
        "category": category,
        "destination": str(dest_file),
        "size": len(content),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def process_bucket(bucket: str) -> dict:
    """Process all files in a bucket's inbox.

    Args:
        bucket: One of 'external', 'workspace', 'personal'.

    Returns:
        Summary dict with results.
    """
    if bucket not in BUCKETS:
        return {"error": f"Unknown bucket: {bucket}. Valid: {list(BUCKETS.keys())}"}

    config = BUCKETS[bucket]
    files = scan_inbox(bucket)

    if not files:
        return {
            "bucket": bucket,
            "label": config["label"],
            "layer": config["layer"],
            "files_found": 0,
            "message": f"No files in {config['inbox']}",
        }

    results = []
    for f in files:
        result = process_file(f)
        results.append(result)

    processed = [r for r in results if r["status"] == "processed"]
    skipped = [r for r in results if r["status"] == "skipped"]

    summary = {
        "bucket": bucket,
        "label": config["label"],
        "layer": config["layer"],
        "files_found": len(files),
        "processed": len(processed),
        "skipped": len(skipped),
        "results": results,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    # Log the processing
    _write_process_log(summary)

    return summary


def process_all_buckets() -> dict:
    """Process all 3 buckets sequentially.

    Returns:
        Combined summary for all buckets.
    """
    all_results = {}
    for bucket in BUCKETS:
        all_results[bucket] = process_bucket(bucket)
    return all_results


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------


def _write_process_log(summary: dict) -> None:
    """Write processing log to logs/ directory."""
    log_dir = LOGS / "bucket-processing"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"bucket-{summary['bucket']}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False, default=str) + "\n")


# ---------------------------------------------------------------------------
# STATUS
# ---------------------------------------------------------------------------


def bucket_status() -> dict:
    """Get status of all 3 knowledge buckets.

    Returns:
        Dict with file counts per bucket and subdirectory.
    """
    status = {}
    for name, config in BUCKETS.items():
        bucket_info = {
            "label": config["label"],
            "layer": config["layer"],
            "path": str(config["path"]),
            "inbox_files": 0,
            "processed_files": 0,
            "subdirs": {},
        }

        # Count inbox files
        inbox = config["inbox"]
        if inbox.exists():
            bucket_info["inbox_files"] = sum(
                1 for f in inbox.rglob("*") if f.is_file() and not f.name.startswith(".")
            )

        # Count processed files per subdir
        for subdir_name, subdir_path in config["subdirs"].items():
            count = 0
            if subdir_path.exists():
                count = sum(
                    1 for f in subdir_path.rglob("*") if f.is_file() and not f.name.startswith(".")
                )
            bucket_info["subdirs"][subdir_name] = count
            bucket_info["processed_files"] += count

        status[name] = bucket_info

    return status


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        # Show status
        status = bucket_status()
        print("\n=== MEGA BRAIN — 3-Layer Knowledge Status ===\n")
        for name, info in status.items():
            icon = {"external": "🔵", "workspace": "🔴", "personal": "🟢"}[name]
            print(f"  {icon} {info['label']} ({info['layer']})")
            print(f"     Inbox: {info['inbox_files']} files")
            print(f"     Processed: {info['processed_files']} files")
            for subdir, count in info["subdirs"].items():
                marker = "✓" if count > 0 else "○"
                print(f"       {marker} {subdir}: {count}")
            print()
        return 0

    bucket = sys.argv[1]
    if bucket == "all":
        results = process_all_buckets()
        for name, summary in results.items():
            print(
                f"\n[{name}] {summary.get('label', '')}: "
                f"{summary.get('processed', 0)} processed, "
                f"{summary.get('skipped', 0)} skipped"
            )
    elif bucket in BUCKETS:
        summary = process_bucket(bucket)
        print(
            f"\n[{bucket}] {summary.get('label', '')}: "
            f"{summary.get('processed', 0)} processed, "
            f"{summary.get('skipped', 0)} skipped"
        )
    else:
        print("Usage: python bucket_processor.py [external|workspace|personal|all]")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
