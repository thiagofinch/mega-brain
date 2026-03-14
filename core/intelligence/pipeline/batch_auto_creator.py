"""
batch_auto_creator.py -- Automatic Batch Creator for Pipeline Jarvis
====================================================================
Scans organized inbox directories, detects when enough unprocessed files
accumulate for a person, and auto-creates batches using batch_governor's
partition logic.

Closes the organize-to-process gap: after files are classified, routed,
and organized into ``knowledge/external/inbox/{person}/{type}/``, this
module detects unprocessed files and creates BATCH-XXX JSON + MD logs
(dual-location per REGRA #8).

Usage::

    # Default: scan and create batches
    python3 core/intelligence/pipeline/batch_auto_creator.py

    # Dry-run: show what would be created, write nothing
    python3 core/intelligence/pipeline/batch_auto_creator.py --dry-run

    # Status: show registry stats
    python3 core/intelligence/pipeline/batch_auto_creator.py status

    # Force: batch even if below MIN_FILES threshold
    python3 core/intelligence/pipeline/batch_auto_creator.py --force

Version: 1.0.0
Date: 2026-03-10
Spec: docs/plans/epic1-phase1.4-batch-auto-creator-spec.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# IMPORTS: core.paths and batch_governor
# ---------------------------------------------------------------------------

try:
    from core.paths import LOGS, MISSION_CONTROL, ROUTING
except ImportError:
    # Fallback for standalone execution
    _ROOT = Path(__file__).resolve().parent.parent.parent.parent
    LOGS = _ROOT / "logs"
    MISSION_CONTROL = _ROOT / ".claude" / "mission-control"
    ROUTING = {
        "external_inbox": _ROOT / "knowledge" / "external" / "inbox",
        "batch_log": LOGS / "batches",
        "batch_registry": MISSION_CONTROL / "BATCH-REGISTRY.json",
        "batch_auto_creator_log": LOGS / "batch-auto-creator.jsonl",
    }

try:
    from core.intelligence.pipeline.batch_governor import MAX_BATCH_SIZE, partition_files
except ImportError:
    MAX_BATCH_SIZE = 5

    def partition_files(files: list[Path], max_size: int = MAX_BATCH_SIZE) -> list[dict]:
        """Minimal fallback if batch_governor is not importable."""
        batches = []
        num = 1
        for i in range(0, len(files), max_size):
            chunk = files[i : i + max_size]
            batches.append(
                {
                    "id": f"BATCH-{num:03d}",
                    "source_hint": "unknown",
                    "files": [str(f) for f in chunk],
                    "count": len(chunk),
                    "total_size": sum(f.stat().st_size for f in chunk if f.exists()),
                }
            )
            num += 1
        return batches


logger = logging.getLogger("batch_auto_creator")

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# Minimum unprocessed files per person to trigger auto-batching.
MIN_FILES: int = int(os.environ.get("BATCH_MIN_FILES", "3"))

# Registry file path.
BATCH_REGISTRY_PATH: Path = ROUTING.get("batch_registry", MISSION_CONTROL / "BATCH-REGISTRY.json")

# Log paths (dual-location per REGRA #8).
BATCH_JSON_DIR: Path = MISSION_CONTROL / "batch-logs"
BATCH_MD_DIR: Path = ROUTING.get("batch_log", LOGS / "batches")

# JSONL audit log.
AUTO_CREATOR_LOG: Path = ROUTING.get("batch_auto_creator_log", LOGS / "batch-auto-creator.jsonl")

# Only scan external bucket for now (business/personal later).
SCAN_BUCKETS: list[str] = ["external"]

# File extensions eligible for batching.
BATCHABLE_EXTENSIONS: set[str] = {".txt", ".md", ".docx", ".pdf"}

# Files to always skip.
SKIP_NAMES: set[str] = {".DS_Store", "Thumbs.db", ".gitkeep", "__pycache__"}

# ---------------------------------------------------------------------------
# SOURCE CODE MAP
# ---------------------------------------------------------------------------

SOURCE_CODE_MAP: dict[str, str] = {
    "alex-hormozi": "AH",
    "cole-gordon": "CG",
    "jeremy-haynes": "JH",
    "jeremy-miner": "JM",
    "sam-oven": "SO",
    "pedro-valerio": "PV",
    "alan-nicolas": "AN",
    "richard-linder": "RL",
    "jordan-lee": "JL",
    "tallis-gomes": "TG",
    "g4-educacao": "G4",
    "the-scalable-company": "TSC",
    "full-sales-system": "FSS",
    "thiago-finch": "TF",
}


# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------


@dataclass
class BatchResult:
    """Represents one created batch."""

    batch_id: str = ""
    source_code: str = ""
    source_name: str = ""
    files: list[str] = field(default_factory=list)
    file_count: int = 0
    total_size_bytes: int = 0
    json_path: str = ""
    md_path: str = ""
    cascading_triggered: bool = False
    created_at: str = ""


@dataclass
class ScanResult:
    """Aggregated result of a full scan."""

    batches_created: list[BatchResult] = field(default_factory=list)
    files_scanned: int = 0
    files_already_batched: int = 0
    files_below_threshold: dict[str, int] = field(default_factory=dict)
    persons_scanned: int = 0
    duration_ms: int = 0


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(UTC).isoformat()


def derive_source_code(entity_slug: str) -> str:
    """Convert entity slug to a 2-3 char source code for batch IDs.

    Strategy:
        1. Check SOURCE_CODE_MAP for known overrides.
        2. Fall back to first letter of each hyphen-separated word, uppercased.
        3. Cap at 3 characters.

    Examples::

        'jeremy-haynes'      -> 'JH'
        'cole-gordon'        -> 'CG'
        'the-scalable-company' -> 'TSC'
        'new-person'         -> 'NP'
    """
    if entity_slug in SOURCE_CODE_MAP:
        return SOURCE_CODE_MAP[entity_slug]

    parts = entity_slug.split("-")
    code = "".join(p[0].upper() for p in parts if p)
    return code[:3] if code else "UNK"


def _humanize_source_name(entity_slug: str) -> str:
    """Convert entity slug to a human-readable name.

    Example: 'jeremy-haynes' -> 'Jeremy Haynes'
    """
    return " ".join(w.capitalize() for w in entity_slug.split("-"))


def collect_batchable_files(person_dir: Path) -> list[Path]:
    """Recursively collect all batchable files under a person directory.

    Walks ``{person_dir}/{type}/`` subdirectories. Includes only files
    with extensions in ``BATCHABLE_EXTENSIONS``. Skips dotfiles,
    ``.ref.yaml``, and ``SKIP_NAMES``.

    Returns:
        Sorted list of absolute Paths.
    """
    files: list[Path] = []
    if not person_dir.is_dir():
        return files

    for f in person_dir.rglob("*"):
        if not f.is_file():
            continue
        if f.name in SKIP_NAMES:
            continue
        if f.name.startswith("."):
            continue
        if f.name.endswith(".ref.yaml"):
            continue
        if f.suffix.lower() not in BATCHABLE_EXTENSIONS:
            continue
        files.append(f.resolve())

    return sorted(files)


def _extract_batch_number(batch_id: str) -> int:
    """Extract the numeric portion from a batch ID.

    Examples::

        'BATCH-128-JH' -> 128
        'BATCH-001'    -> 1
        'BATCH-2025'   -> 2025
    """
    match = re.search(r"BATCH-(\d+)", batch_id)
    if match:
        return int(match.group(1))
    return 0


# ---------------------------------------------------------------------------
# REGISTRY (load / save / bootstrap)
# ---------------------------------------------------------------------------


def _try_flock(f: object, operation: int) -> None:
    """Attempt fcntl.flock; no-op on platforms without fcntl (Windows)."""
    try:
        import fcntl

        fcntl.flock(f.fileno(), operation)  # type: ignore[union-attr]
    except (ImportError, AttributeError, OSError):
        pass  # Non-Unix or virtual file; skip locking


def load_or_init_registry() -> dict:
    """Load ``BATCH-REGISTRY.json`` or create it via bootstrap.

    On first run, scans existing batch JSON logs to seed the registry
    so that previously-batched files are not re-processed.
    """
    if BATCH_REGISTRY_PATH.exists():
        try:
            text = BATCH_REGISTRY_PATH.read_text(encoding="utf-8")
            data = json.loads(text)
            if isinstance(data, dict) and "version" in data:
                return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Corrupt registry, bootstrapping fresh: %s", exc)

    return _bootstrap_registry()


def _bootstrap_registry() -> dict:
    """Scan existing batch-logs to create the initial registry."""
    registry: dict = {
        "version": 1,
        "updated_at": _now_iso(),
        "next_batch_number": 1,
        "files": {},
        "batches": {},
    }

    if not BATCH_JSON_DIR.exists():
        return registry

    max_num = 0
    for json_file in sorted(BATCH_JSON_DIR.glob("BATCH-*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        batch_id = data.get("batch_id", "")
        source = data.get("source", "")
        source_name = data.get("source_name", "")

        num = _extract_batch_number(batch_id)
        if num > max_num:
            max_num = num

        # Register files from this batch (legacy: filenames only, not full paths).
        files_processed = data.get("files_processed", [])
        if not isinstance(files_processed, list):
            # Some old batches store file count as int, not file list.
            files_processed = []
        for filename in files_processed:
            key = f"legacy:{filename}"
            registry["files"][key] = {
                "batch_id": batch_id,
                "batched_at": data.get("generated_at", ""),
                "source_name": source_name,
                "legacy": True,
            }

        registry["batches"][batch_id] = {
            "source_name": source_name,
            "source_code": source,
            "file_count": data.get("files_count", 0),
            "created_at": data.get("generated_at", ""),
            "status": data.get("status", "UNKNOWN"),
        }

    registry["next_batch_number"] = max_num + 1
    return registry


def save_registry(registry: dict) -> None:
    """Write the registry to disk with file locking."""
    BATCH_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    registry["updated_at"] = _now_iso()

    try:
        with open(BATCH_REGISTRY_PATH, "w", encoding="utf-8") as f:
            _try_flock(f, 2)  # LOCK_EX
            json.dump(registry, f, indent=2, ensure_ascii=False, default=str)
            f.flush()
            _try_flock(f, 8)  # LOCK_UN
    except ImportError:
        # fcntl not available (Windows) -- write without locking
        BATCH_REGISTRY_PATH.write_text(
            json.dumps(registry, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )


def _is_file_batched(registry: dict, file_path: Path) -> bool:
    """Check if a file is already in the registry.

    Checks both the absolute path (new-style) and legacy filename stem.
    """
    abs_str = str(file_path)
    if abs_str in registry.get("files", {}):
        return True

    # Check against legacy entries by filename stem.
    stem = file_path.stem
    legacy_key = f"legacy:{stem}"
    if legacy_key in registry.get("files", {}):
        return True

    # Also check if the full filename (with extension) is a legacy entry.
    legacy_name_key = f"legacy:{file_path.name}"
    if legacy_name_key in registry.get("files", {}):
        return True

    return False


def register_files(
    registry: dict,
    batch_id: str,
    entity_slug: str,
    source_code: str,
    file_paths: list[str],
) -> None:
    """Add files to the registry's files dict and batches dict.

    Mutates *registry* in-place. Caller is responsible for saving.
    """
    now = _now_iso()

    for fp in file_paths:
        registry["files"][fp] = {
            "batch_id": batch_id,
            "batched_at": now,
            "source_name": entity_slug,
        }

    registry["batches"][batch_id] = {
        "source_name": entity_slug,
        "source_code": source_code,
        "file_count": len(file_paths),
        "created_at": now,
        "status": "CREATED",
    }


# ---------------------------------------------------------------------------
# BATCH FILE WRITERS
# ---------------------------------------------------------------------------


def write_batch_json(
    batch_id: str,
    source_code: str,
    entity_slug: str,
    file_paths: list[str],
    total_size: int,
) -> Path:
    """Write ``BATCH-XXX-YY.json`` to ``.claude/mission-control/batch-logs/``.

    Format matches existing batch JSONs for backward compatibility.
    """
    BATCH_JSON_DIR.mkdir(parents=True, exist_ok=True)

    json_filename = f"{batch_id}.json"
    json_path = BATCH_JSON_DIR / json_filename

    # Avoid collision: if file already exists, increment
    attempts = 0
    while json_path.exists() and attempts < 10:
        num = _extract_batch_number(batch_id)
        num += 1
        batch_id = f"BATCH-{num:03d}-{source_code}"
        json_filename = f"{batch_id}.json"
        json_path = BATCH_JSON_DIR / json_filename
        attempts += 1

    data = {
        "batch_id": batch_id,
        "source": source_code,
        "source_name": _humanize_source_name(entity_slug),
        "created_at": datetime.now(UTC).strftime("%Y-%m-%d"),
        "md_file": f"{batch_id.split('-' + source_code)[0]}.md"
        if source_code
        else f"{batch_id}.md",
        "files_processed": [Path(f).name for f in file_paths],
        "files_count": len(file_paths),
        "themes": [],
        "dna_metrics": {
            "filosofias": 0,
            "modelos_mentais": 0,
            "heuristicas": 0,
            "frameworks": 0,
            "metodologias": 0,
        },
        "frameworks_extracted": [],
        "total_elements": 0,
        "status": "CREATED",
        "cascading_executed": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "auto_created": True,
    }

    json_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    return json_path


def write_batch_md(
    batch_id: str,
    source_code: str,
    entity_slug: str,
    file_paths: list[str],
    total_size: int,
) -> Path:
    """Write ``BATCH-XXX.md`` to ``logs/batches/`` (dual-location per REGRA #8).

    Generates a pre-extraction batch log compatible with the MCE pipeline.
    Full MCE progressive log is generated by the pipeline orchestrator using
    ``core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md``.
    """
    BATCH_MD_DIR.mkdir(parents=True, exist_ok=True)

    # MD filename uses the numeric part only (e.g., BATCH-130.md)
    num = _extract_batch_number(batch_id)
    md_filename = f"BATCH-{num:03d}.md"
    md_path = BATCH_MD_DIR / md_filename

    human_name = _humanize_source_name(entity_slug)
    now_date = datetime.now(UTC).strftime("%Y-%m-%d")
    now_full = datetime.now(UTC).isoformat()

    file_list_lines = "\n".join(
        f"| {i + 1} | `{Path(f).name}` | pending |" for i, f in enumerate(file_paths)
    )

    content = f"""# {batch_id}

> **Auto-generated by batch_auto_creator.py**
> **Date:** {now_date}
> **Status:** CREATED (pre-extraction)
> **Template:** MCE-PIPELINE-LOG-TEMPLATE.md v1.0.0

---

## META

| Field | Value |
|-------|-------|
| Batch ID | {batch_id} |
| Source | {source_code} ({human_name}) |
| Entity slug | {entity_slug} |
| Files | {len(file_paths)} |
| Total Size | {total_size:,} bytes |
| Pipeline status | CLASSIFIED |
| Auto-Created | Yes |
| Generated At | {now_full} |

---

## 1. CLASSIFICATION -- Atlas [@] COMPLETO

**Decision:** external @ auto-created
**Routing:** AUTO (batch_auto_creator)

---

## 2. ORGANIZATION -- Atlas [@] COMPLETO

| Field | Value |
|-------|-------|
| Entity detected | {entity_slug} |
| Batch ID | {batch_id} |
| Files in batch | {len(file_paths)} |

---

## EXTRACTION METRICS (populated by pipeline)

### DNA Layers (5-layer)

| Layer | Count |
|-------|-------|
| Filosofias | 0 |
| Modelos Mentais | 0 |
| Heuristicas | 0 |
| Frameworks | 0 |
| Metodologias | 0 |
| **Total** | **0** |

### MCE Layers (populated by MCE pipeline)

| Layer | Count |
|-------|-------|
| Behavioral Patterns | 0 |
| Values Hierarchy | 0 |
| Voice DNA phrases | 0 |

> Run `/pipeline-mce {entity_slug}` to execute full MCE extraction.
> Full progressive log: `core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md`

---

## ARQUIVOS PROCESSADOS

| # | Arquivo | Tema |
|---|---------|------|
{file_list_lines}

---

## DESTINO DO CONHECIMENTO

> To be determined during pipeline extraction.

- Agentes: {source_code} (Person Agent)
- Playbooks: pending
- DNAs: pending (5-layer + MCE)
- Dossiers: pending

---

*Auto-created by batch_auto_creator.py at {now_full}*
"""

    md_path.write_text(content, encoding="utf-8")
    return md_path


# ---------------------------------------------------------------------------
# CASCADING
# ---------------------------------------------------------------------------


def trigger_cascading(md_path: Path) -> bool:
    """Invoke ``post_batch_cascading.py`` on a newly created batch.

    Returns True if cascading completed successfully, False otherwise.
    """
    try:
        from core.intelligence.pipeline.post_batch_cascading import (
            process_batch_for_cascading,
        )

        process_batch_for_cascading(md_path)
        return True
    except ImportError:
        logger.debug("post_batch_cascading not available; skipping cascading")
        return False
    except Exception as exc:
        logger.warning("Cascading failed for %s: %s", md_path, exc)
        return False


def trigger_memory_enrichment(
    batch_id: str,
    entity_slug: str,
    file_paths: list[str],
) -> bool:
    """Invoke ``memory_enricher.enrich()`` with stub insights from this batch.

    Creates minimal Insight dicts (one per file) so the enricher can route
    them to the correct agents. Full insight extraction happens in Phase 4;
    this seeds the connection so enrichment can occur incrementally.

    Returns True if enrichment ran without errors, False otherwise.
    """
    try:
        from core.intelligence.pipeline.memory_enricher import enrich

        insights = [
            {
                "person_slug": entity_slug,
                "chunk_id": f"{batch_id}:{Path(fp).stem}",
                "title": f"Batch file: {Path(fp).name}",
                "content": "",
                "tag": derive_source_code(entity_slug),
                "batch_id": batch_id,
                "path_raiz": fp,
            }
            for fp in file_paths
        ]
        result = enrich(insights)
        if result.get("errors"):
            logger.warning(
                "Memory enrichment had errors for %s: %s",
                batch_id,
                result["errors"],
            )
        return not result.get("errors")
    except ImportError:
        logger.debug("memory_enricher not available; skipping enrichment")
        return False
    except Exception as exc:
        logger.warning("Memory enrichment failed for %s: %s", batch_id, exc)
        return False


def trigger_workspace_sync() -> bool:
    """Invoke ``workspace_sync.sync()`` after batch creation and enrichment.

    Syncs validated business knowledge to the prescriptive workspace layer.
    Non-fatal: if workspace_sync is not importable or fails, batch creation
    still succeeds.

    Returns True if sync ran without errors, False otherwise.
    """
    try:
        from core.intelligence.pipeline.workspace_sync import sync

        result = sync()
        if result.errors:
            logger.warning("Workspace sync had errors: %s", result.errors)
        return not result.errors
    except ImportError:
        logger.debug("workspace_sync not available; skipping workspace sync")
        return False
    except Exception as exc:
        logger.warning("Workspace sync failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# JSONL AUDIT LOG
# ---------------------------------------------------------------------------


def _log_scan_result(result: ScanResult, *, dry_run: bool = False) -> None:
    """Append one JSONL line to the auto-creator audit log."""
    try:
        AUTO_CREATOR_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": _now_iso(),
            "files_scanned": result.files_scanned,
            "files_already_batched": result.files_already_batched,
            "persons_scanned": result.persons_scanned,
            "batches_created": len(result.batches_created),
            "batch_ids": [b.batch_id for b in result.batches_created],
            "files_below_threshold": result.files_below_threshold,
            "dry_run": dry_run,
            "duration_ms": result.duration_ms,
        }
        with open(AUTO_CREATOR_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write auto-creator log", exc_info=True)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------


def scan_and_create(
    *,
    dry_run: bool = False,
    buckets: list[str] | None = None,
    force: bool = False,
) -> ScanResult:
    """Scan organized inbox directories and create batches for unprocessed files.

    Args:
        dry_run: If True, report what would be created but do not write anything.
        buckets: Override ``SCAN_BUCKETS`` (for testing or future multi-bucket).
        force: If True, batch even if below ``MIN_FILES`` threshold (min 1 file).

    Returns:
        ScanResult describing all actions taken.
    """
    start_time = time.monotonic()
    registry = load_or_init_registry()
    target_buckets = buckets or SCAN_BUCKETS
    threshold = 1 if force else MIN_FILES

    result = ScanResult()

    for bucket in target_buckets:
        inbox_key = f"{bucket}_inbox"
        inbox_root = ROUTING.get(inbox_key)
        if inbox_root is None:
            logger.warning("No ROUTING key for %r, skipping", inbox_key)
            continue

        inbox_root = Path(inbox_root)
        if not inbox_root.exists():
            logger.debug("Inbox root does not exist: %s", inbox_root)
            continue

        # Collect person directories (first-level subdirs).
        person_dirs = sorted(
            d for d in inbox_root.iterdir() if d.is_dir() and not d.name.startswith("_")
        )
        result.persons_scanned += len(person_dirs)

        for person_dir in person_dirs:
            entity_slug = person_dir.name
            source_code = derive_source_code(entity_slug)

            # Collect all batchable files under this person.
            all_files = collect_batchable_files(person_dir)
            result.files_scanned += len(all_files)

            # Filter out already-batched files.
            unprocessed = [f for f in all_files if not _is_file_batched(registry, f)]
            already_batched = len(all_files) - len(unprocessed)
            result.files_already_batched += already_batched

            # Check threshold.
            if len(unprocessed) < threshold:
                if unprocessed:
                    result.files_below_threshold[entity_slug] = len(unprocessed)
                continue

            # Partition using batch_governor (respects MAX_BATCH_SIZE=5).
            batches = partition_files(unprocessed, max_size=MAX_BATCH_SIZE)

            for batch_plan in batches:
                batch_files: list[str] = batch_plan["files"]
                batch_count: int = batch_plan["count"]
                batch_total_size: int = batch_plan.get("total_size", 0)

                if dry_run:
                    result.batches_created.append(
                        BatchResult(
                            batch_id=f"BATCH-{registry['next_batch_number']:03d}-{source_code}",
                            source_code=source_code,
                            source_name=entity_slug,
                            files=batch_files,
                            file_count=batch_count,
                            total_size_bytes=batch_total_size,
                            json_path="(dry-run)",
                            md_path="(dry-run)",
                            cascading_triggered=False,
                            created_at=_now_iso(),
                        )
                    )
                    registry["next_batch_number"] += 1
                    continue

                # Assign batch ID.
                batch_num = registry["next_batch_number"]
                batch_id = f"BATCH-{batch_num:03d}-{source_code}"

                # Collision check: if JSON file already exists, increment.
                collision_attempts = 0
                while (BATCH_JSON_DIR / f"{batch_id}.json").exists() and collision_attempts < 10:
                    batch_num += 1
                    batch_id = f"BATCH-{batch_num:03d}-{source_code}"
                    collision_attempts += 1

                registry["next_batch_number"] = batch_num + 1

                # Create JSON log.
                json_path = write_batch_json(
                    batch_id, source_code, entity_slug, batch_files, batch_total_size
                )

                # Create MD log (dual-location, REGRA #8).
                md_path = write_batch_md(
                    batch_id, source_code, entity_slug, batch_files, batch_total_size
                )

                # Register files in registry.
                register_files(registry, batch_id, entity_slug, source_code, batch_files)

                # Trigger cascading (non-fatal if it fails).
                cascading_ok = trigger_cascading(md_path)

                # Trigger memory enrichment (non-fatal if it fails).
                trigger_memory_enrichment(batch_id, entity_slug, batch_files)

                # Trigger workspace sync (non-fatal if it fails).
                trigger_workspace_sync()

                result.batches_created.append(
                    BatchResult(
                        batch_id=batch_id,
                        source_code=source_code,
                        source_name=entity_slug,
                        files=batch_files,
                        file_count=batch_count,
                        total_size_bytes=batch_total_size,
                        json_path=str(json_path),
                        md_path=str(md_path),
                        cascading_triggered=cascading_ok,
                        created_at=_now_iso(),
                    )
                )

                logger.info(
                    "Created %s: %d files from %s (%s)",
                    batch_id,
                    batch_count,
                    entity_slug,
                    source_code,
                )

    # Save registry (skip in dry-run).
    if not dry_run:
        save_registry(registry)

    # Append to JSONL audit log.
    _log_scan_result(result, dry_run=dry_run)

    result.duration_ms = int((time.monotonic() - start_time) * 1000)
    return result


# ---------------------------------------------------------------------------
# STATUS COMMAND
# ---------------------------------------------------------------------------


def show_status() -> None:
    """Print registry statistics to stdout."""
    if not BATCH_REGISTRY_PATH.exists():
        print("No BATCH-REGISTRY.json found. Run scan_and_create() first.")
        return

    registry = load_or_init_registry()
    total_files = len(registry.get("files", {}))
    total_batches = len(registry.get("batches", {}))
    next_num = registry.get("next_batch_number", 0)
    updated = registry.get("updated_at", "never")
    legacy_count = sum(1 for v in registry.get("files", {}).values() if v.get("legacy"))

    print("BATCH-REGISTRY.json Status")
    print(f"  Total files registered:  {total_files}")
    print(f"  Legacy entries:          {legacy_count}")
    print(f"  New-style entries:       {total_files - legacy_count}")
    print(f"  Total batches:           {total_batches}")
    print(f"  Next batch number:       {next_num}")
    print(f"  Last updated:            {updated}")


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------


def main() -> int:
    """Parse CLI arguments and run the appropriate command."""
    parser = argparse.ArgumentParser(
        prog="batch_auto_creator",
        description="Automatic batch creator for the Pipeline Jarvis.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="scan",
        choices=["scan", "status"],
        help="Command to run (default: scan).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created, write nothing.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Batch even if below MIN_FILES threshold (min 1 file).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Set log level to DEBUG.",
    )

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    if args.command == "status":
        show_status()
        return 0

    result = scan_and_create(
        dry_run=args.dry_run,
        force=args.force,
    )

    # Print summary.
    prefix = "[DRY-RUN] " if args.dry_run else ""
    print(f"\n{prefix}Scan complete in {result.duration_ms}ms")
    print(f"  Persons scanned:    {result.persons_scanned}")
    print(f"  Files scanned:      {result.files_scanned}")
    print(f"  Already batched:    {result.files_already_batched}")
    print(f"  Batches created:    {len(result.batches_created)}")

    if result.batches_created:
        for b in result.batches_created:
            print(f"    {b.batch_id}: {b.file_count} files ({b.source_name})")

    if result.files_below_threshold:
        print("  Below threshold:")
        for person, count in result.files_below_threshold.items():
            print(f"    {person}: {count} files (need {MIN_FILES})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
