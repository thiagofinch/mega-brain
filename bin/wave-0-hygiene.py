#!/usr/bin/env python3
"""
Wave 0 — Pipeline Hygiene Script
=================================
Deterministic cleanup: dedup, reclassify, consolidate, reset state.
Zero LLM calls. Pure file operations.

Usage:
    python3 bin/wave-0-hygiene.py [--dry-run] [--task N]

Tasks:
    1. Dedup meetings (business/inbox/meetings/ vs _unclassified/calls/)
    2. Reclassify personal→business (9 misrouted meetings)
    3. Consolidate shadow dossiers (workspace/ops/meetings/ → knowledge/business/dossiers/)
    4. Classify unclassified meetings (scope_classifier on _unclassified/)
    5. Fix naming inconsistencies (sam-ovens → sam-oven)
    6. Reset stuck pipeline state
    7. Clean empty dirs
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# -- Project paths ----------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.paths import (  # noqa: E402
    KNOWLEDGE_BUSINESS,
    KNOWLEDGE_EXTERNAL,
    KNOWLEDGE_PERSONAL,
    LOGS,
    MISSION_CONTROL,
    ROOT as PROJECT_ROOT,
    WORKSPACE,
)

# -- Logging ----------------------------------------------------------------
LOG_DIR = LOGS / "wave-mce"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "wave-0-hygiene.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)
log = logging.getLogger("wave-0")

# -- State ------------------------------------------------------------------
WAVE_STATE_FILE = MISSION_CONTROL / "WAVE-STATE.json"


def load_wave_state() -> dict:
    if WAVE_STATE_FILE.exists():
        return json.loads(WAVE_STATE_FILE.read_text(encoding="utf-8"))
    return {"waves": {}, "created": datetime.now(timezone.utc).isoformat()}


def save_wave_state(state: dict) -> None:
    WAVE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["updated"] = datetime.now(timezone.utc).isoformat()
    WAVE_STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# -- Helpers ----------------------------------------------------------------
def file_hash(path: Path) -> str:
    """MD5 hash of file content for dedup comparison."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_move(src: Path, dst: Path, dry_run: bool = False) -> bool:
    """Move file, creating parent dirs. Returns True if moved."""
    if not src.exists():
        log.warning(f"  SKIP (not found): {src}")
        return False
    if dst.exists():
        log.warning(f"  SKIP (dst exists): {dst}")
        return False
    if dry_run:
        log.info(f"  [DRY] MOVE {src.relative_to(PROJECT_ROOT)} → {dst.relative_to(PROJECT_ROOT)}")
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    log.info(f"  MOVED {src.relative_to(PROJECT_ROOT)} → {dst.relative_to(PROJECT_ROOT)}")
    return True


def safe_delete(path: Path, dry_run: bool = False) -> bool:
    """Delete file. Returns True if deleted."""
    if not path.exists():
        return False
    if dry_run:
        log.info(f"  [DRY] DELETE {path.relative_to(PROJECT_ROOT)}")
        return True
    path.unlink()
    log.info(f"  DELETED {path.relative_to(PROJECT_ROOT)}")
    return True


# ===========================================================================
# TASK 1: Dedup meetings
# ===========================================================================
def task_1_dedup_meetings(dry_run: bool = False) -> dict:
    """Remove duplicate meetings between business/inbox/meetings/ and _unclassified/calls/."""
    log.info("=" * 60)
    log.info("TASK 1: Dedup meetings (business/inbox)")
    log.info("=" * 60)

    meetings_dir = KNOWLEDGE_BUSINESS / "inbox" / "meetings"
    unclassified_dir = KNOWLEDGE_BUSINESS / "inbox" / "_unclassified" / "calls"

    stats = {"duplicates_found": 0, "files_removed": 0, "kept_in": ""}

    if not meetings_dir.exists() or not unclassified_dir.exists():
        log.info("  One or both dirs missing. Skipping.")
        return stats

    # Build hash map of _unclassified/calls/ (canonical location)
    unclassified_hashes: dict[str, Path] = {}
    for f in unclassified_dir.iterdir():
        if f.is_file() and not f.name.startswith("."):
            unclassified_hashes[f.name] = f

    # Find duplicates in meetings/ that also exist in _unclassified/calls/
    for f in sorted(meetings_dir.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            if f.name in unclassified_hashes:
                stats["duplicates_found"] += 1
                # Keep in _unclassified (canonical), remove from meetings/
                if safe_delete(f, dry_run):
                    stats["files_removed"] += 1

    # If meetings/ is now empty, remove it
    if meetings_dir.exists() and not any(meetings_dir.iterdir()):
        if not dry_run:
            meetings_dir.rmdir()
            log.info(f"  REMOVED empty dir: {meetings_dir.relative_to(PROJECT_ROOT)}")

    stats["kept_in"] = "_unclassified/calls/"
    log.info(f"  Result: {stats['duplicates_found']} duplicates found, {stats['files_removed']} removed")
    return stats


# ===========================================================================
# TASK 2: Reclassify personal → business
# ===========================================================================
def task_2_reclassify_personal(dry_run: bool = False) -> dict:
    """Move misclassified business meetings from personal/inbox/ to business/inbox/."""
    log.info("=" * 60)
    log.info("TASK 2: Reclassify personal→business")
    log.info("=" * 60)

    personal_inbox = KNOWLEDGE_PERSONAL / "inbox"
    business_inbox = KNOWLEDGE_BUSINESS / "inbox"
    stats = {"files_moved": 0, "files_skipped": 0}

    if not personal_inbox.exists():
        log.info("  personal/inbox/ not found. Skipping.")
        return stats

    # All subdirs in personal/inbox/ except _unclassified
    for subdir in sorted(personal_inbox.iterdir()):
        if not subdir.is_dir() or subdir.name.startswith("."):
            continue

        for calls_dir in subdir.rglob("calls"):
            if not calls_dir.is_dir():
                continue
            for f in sorted(calls_dir.iterdir()):
                if f.is_file() and not f.name.startswith("."):
                    # Determine target: business/inbox/{entity}/calls/
                    entity = subdir.name
                    # Map entity to business inbox subdir
                    target_dir = business_inbox / entity / "calls"
                    if safe_move(f, target_dir / f.name, dry_run):
                        stats["files_moved"] += 1
                    else:
                        stats["files_skipped"] += 1

    # Also handle _unclassified in personal → goes to business/_unclassified
    personal_unclassified = personal_inbox / "_unclassified"
    if personal_unclassified.exists():
        for type_dir in sorted(personal_unclassified.iterdir()):
            if not type_dir.is_dir():
                continue
            for f in sorted(type_dir.iterdir()):
                if f.is_file() and not f.name.startswith("."):
                    target = business_inbox / "_unclassified" / type_dir.name / f.name
                    if safe_move(f, target, dry_run):
                        stats["files_moved"] += 1
                    else:
                        stats["files_skipped"] += 1

    log.info(f"  Result: {stats['files_moved']} moved, {stats['files_skipped']} skipped")
    return stats


# ===========================================================================
# TASK 3: Consolidate shadow dossiers
# ===========================================================================
def task_3_consolidate_shadow_dossiers(dry_run: bool = False) -> dict:
    """Move shadow dossiers from workspace/ops/meetings/ to knowledge/business/dossiers/."""
    log.info("=" * 60)
    log.info("TASK 3: Consolidate shadow dossiers")
    log.info("=" * 60)

    shadow_dir = WORKSPACE / "ops" / "meetings"
    target_persons = KNOWLEDGE_BUSINESS / "dossiers" / "persons"
    target_themes = KNOWLEDGE_BUSINESS / "dossiers" / "themes"
    stats = {"moved": 0, "skipped_exists": 0, "skipped_other": 0}

    if not shadow_dir.exists():
        log.info("  workspace/ops/meetings/ not found. Skipping.")
        return stats

    for f in sorted(shadow_dir.rglob("*.md")):
        if f.name.startswith("."):
            continue

        name_upper = f.name.upper()

        # Determine target based on content type
        if "DOSSIER-" in name_upper:
            # Check if it's a person or theme dossier
            # Person dossiers typically have person names
            # Theme dossiers have topic keywords
            target_dir = target_persons  # default
            if any(kw in name_upper for kw in [
                "EVENT", "PROCESS", "IP-PROTECTION", "MCP", "VALUE-LADDER",
                "WORKSPACE", "GOVERNANCE", "FRAMEWORK", "METHODOLOGY",
                "SALES-PROCESS", "COMISSION", "METRIC", "PRICING", "CULTURA",
            ]):
                target_dir = target_themes

            target_path = target_dir / f.name
            if target_path.exists():
                # Shadow file exists in canonical location — skip (canonical wins)
                stats["skipped_exists"] += 1
                log.info(f"  SKIP (canonical exists): {f.name}")
                # Delete the shadow copy
                if not dry_run:
                    f.unlink()
                    log.info(f"  DELETED shadow: {f.relative_to(PROJECT_ROOT)}")
            else:
                if safe_move(f, target_path, dry_run):
                    stats["moved"] += 1
        else:
            stats["skipped_other"] += 1

    # Clean empty shadow dir
    if shadow_dir.exists() and not dry_run:
        _clean_empty_dirs(shadow_dir)

    log.info(f"  Result: {stats['moved']} moved, {stats['skipped_exists']} shadow deleted (canonical exists)")
    return stats


# ===========================================================================
# TASK 4: Classify unclassified meetings
# ===========================================================================
def task_4_classify_unclassified(dry_run: bool = False) -> dict:
    """Run scope_classifier on unclassified meetings to route them."""
    log.info("=" * 60)
    log.info("TASK 4: Classify unclassified meetings")
    log.info("=" * 60)

    from core.intelligence.pipeline.scope_classifier import (
        ClassificationContext,
        classify,
    )
    from core.intelligence.pipeline.inbox_organizer import organize_inbox

    unclassified_dir = KNOWLEDGE_BUSINESS / "inbox" / "_unclassified" / "calls"
    stats = {"classified": 0, "remained_unclassified": 0, "errors": 0}

    if not unclassified_dir.exists():
        log.info("  _unclassified/calls/ not found. Skipping.")
        return stats

    for f in sorted(unclassified_dir.iterdir()):
        if not f.is_file() or f.name.startswith("."):
            continue

        try:
            # Read first 5000 chars for classification
            text = f.read_text(encoding="utf-8", errors="replace")[:5000]
            title = f.stem  # filename without extension

            ctx = ClassificationContext(
                text=text,
                filename=f.name,
                file_path=str(f),
                title=title,
                source_type_hint="meeting",
            )

            decision = classify(ctx)

            if decision.detected_entities:
                entity_slug = decision.detected_entities[0]
                target_dir = KNOWLEDGE_BUSINESS / "inbox" / entity_slug / "calls"
                if safe_move(f, target_dir / f.name, dry_run):
                    stats["classified"] += 1
                    log.info(f"    → entity: {entity_slug} (confidence: {decision.confidence:.2f})")
            else:
                stats["remained_unclassified"] += 1
                log.info(f"  NO ENTITY detected for: {f.name}")

        except Exception as e:
            stats["errors"] += 1
            log.error(f"  ERROR classifying {f.name}: {e}")

    log.info(f"  Result: {stats['classified']} classified, {stats['remained_unclassified']} unresolved")
    return stats


# ===========================================================================
# TASK 5: Fix naming
# ===========================================================================
def task_5_fix_naming(dry_run: bool = False) -> dict:
    """Fix naming inconsistencies (sam-ovens → sam-oven)."""
    log.info("=" * 60)
    log.info("TASK 5: Fix naming inconsistencies")
    log.info("=" * 60)

    fixes = [
        {
            "src": KNOWLEDGE_EXTERNAL / "sources" / "sam-ovens",
            "dst": KNOWLEDGE_EXTERNAL / "sources" / "sam-oven",
            "desc": "sam-ovens → sam-oven (sources)",
        },
    ]

    stats = {"fixed": 0, "skipped": 0}

    for fix in fixes:
        src, dst = fix["src"], fix["dst"]
        if src.exists() and not dst.exists():
            if dry_run:
                log.info(f"  [DRY] RENAME {fix['desc']}")
            else:
                shutil.move(str(src), str(dst))
                log.info(f"  RENAMED {fix['desc']}")
            stats["fixed"] += 1
        elif src.exists() and dst.exists():
            # Both exist — merge contents
            log.info(f"  MERGE needed: both {src.name} and {dst.name} exist")
            if not dry_run:
                for f in src.iterdir():
                    target = dst / f.name
                    if not target.exists():
                        shutil.move(str(f), str(target))
                        log.info(f"    MERGED {f.name} into {dst.name}")
                _clean_empty_dirs(src)
            stats["fixed"] += 1
        else:
            log.info(f"  SKIP: {fix['desc']} (source not found)")
            stats["skipped"] += 1

    log.info(f"  Result: {stats['fixed']} fixed, {stats['skipped']} skipped")
    return stats


# ===========================================================================
# TASK 6: Reset pipeline state
# ===========================================================================
def task_6_reset_pipeline_state(dry_run: bool = False) -> dict:
    """Reset stuck pipeline phases in PIPELINE-STATE.json."""
    log.info("=" * 60)
    log.info("TASK 6: Reset stuck pipeline state")
    log.info("=" * 60)

    state_file = MISSION_CONTROL / "PIPELINE-STATE.json"
    stats = {"phases_reset": 0}

    if not state_file.exists():
        log.info("  PIPELINE-STATE.json not found. Skipping.")
        return stats

    state = json.loads(state_file.read_text(encoding="utf-8"))

    # Find stuck phases (in_progress for too long)
    phases = state.get("phases", {})
    for phase_name, phase_data in phases.items():
        if isinstance(phase_data, dict) and phase_data.get("status") == "in_progress":
            log.info(f"  RESETTING stuck phase: {phase_name}")
            if not dry_run:
                phase_data["status"] = "pending"
                phase_data["reset_at"] = datetime.now(timezone.utc).isoformat()
                phase_data["reset_reason"] = "wave-0-hygiene: stuck phase detected"
            stats["phases_reset"] += 1

    if not dry_run and stats["phases_reset"] > 0:
        state_file.write_text(
            json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    log.info(f"  Result: {stats['phases_reset']} phases reset")
    return stats


# ===========================================================================
# TASK 7: Clean empty dirs
# ===========================================================================
def task_7_clean_empty_dirs(dry_run: bool = False) -> dict:
    """Remove empty placeholder directories."""
    log.info("=" * 60)
    log.info("TASK 7: Clean empty directories")
    log.info("=" * 60)

    targets = [
        KNOWLEDGE_PERSONAL / "inbox" / "outsider" / "calls",
        KNOWLEDGE_PERSONAL / "inbox" / "outsider",
        KNOWLEDGE_EXTERNAL / "inbox" / "test-source",
    ]

    stats = {"removed": 0, "skipped": 0}

    for d in targets:
        if d.exists() and d.is_dir():
            children = [c for c in d.iterdir() if not c.name.startswith(".")]
            if not children:
                if dry_run:
                    log.info(f"  [DRY] RMDIR {d.relative_to(PROJECT_ROOT)}")
                else:
                    # Remove .DS_Store if present, then rmdir
                    ds_store = d / ".DS_Store"
                    if ds_store.exists():
                        ds_store.unlink()
                    d.rmdir()
                    log.info(f"  RMDIR {d.relative_to(PROJECT_ROOT)}")
                stats["removed"] += 1
            else:
                log.info(f"  SKIP (not empty): {d.relative_to(PROJECT_ROOT)}")
                stats["skipped"] += 1

    log.info(f"  Result: {stats['removed']} removed, {stats['skipped']} not empty")
    return stats


# -- Helpers ----------------------------------------------------------------
def _clean_empty_dirs(root: Path) -> None:
    """Recursively remove empty directories."""
    for d in sorted(root.rglob("*"), reverse=True):
        if d.is_dir():
            children = [c for c in d.iterdir() if not c.name.startswith(".")]
            if not children:
                # Remove hidden files first
                for hidden in d.iterdir():
                    hidden.unlink()
                d.rmdir()


# ===========================================================================
# MAIN
# ===========================================================================
ALL_TASKS = {
    1: ("Dedup meetings", task_1_dedup_meetings),
    2: ("Reclassify personal→business", task_2_reclassify_personal),
    3: ("Consolidate shadow dossiers", task_3_consolidate_shadow_dossiers),
    4: ("Classify unclassified meetings", task_4_classify_unclassified),
    5: ("Fix naming inconsistencies", task_5_fix_naming),
    6: ("Reset pipeline state", task_6_reset_pipeline_state),
    7: ("Clean empty dirs", task_7_clean_empty_dirs),
}


def main():
    parser = argparse.ArgumentParser(description="Wave 0 — Pipeline Hygiene")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--task", type=int, help="Run specific task (1-7)")
    args = parser.parse_args()

    start = time.time()
    log.info("=" * 60)
    log.info(f"WAVE 0 — PIPELINE HYGIENE {'[DRY RUN]' if args.dry_run else '[LIVE]'}")
    log.info(f"Started: {datetime.now(timezone.utc).isoformat()}")
    log.info("=" * 60)

    state = load_wave_state()
    wave_0 = state.setdefault("waves", {}).setdefault("0", {
        "status": "running",
        "started": datetime.now(timezone.utc).isoformat(),
        "tasks": {},
    })
    wave_0["status"] = "running"

    results = {}
    tasks_to_run = {args.task: ALL_TASKS[args.task]} if args.task else ALL_TASKS

    for task_num, (task_name, task_fn) in tasks_to_run.items():
        try:
            result = task_fn(dry_run=args.dry_run)
            results[task_num] = {"name": task_name, "status": "complete", **result}
            wave_0["tasks"][str(task_num)] = results[task_num]
        except Exception as e:
            log.error(f"TASK {task_num} FAILED: {e}")
            results[task_num] = {"name": task_name, "status": "failed", "error": str(e)}
            wave_0["tasks"][str(task_num)] = results[task_num]

    elapsed = time.time() - start
    wave_0["status"] = "complete"
    wave_0["completed"] = datetime.now(timezone.utc).isoformat()
    wave_0["elapsed_seconds"] = round(elapsed, 1)
    save_wave_state(state)

    # Summary
    log.info("")
    log.info("=" * 60)
    log.info("WAVE 0 — SUMMARY")
    log.info("=" * 60)
    for num, res in results.items():
        status_icon = "●" if res["status"] == "complete" else "✗"
        log.info(f"  [{status_icon}] Task {num}: {res['name']} — {res['status']}")
    log.info(f"  Duration: {elapsed:.1f}s")
    log.info(f"  State: {WAVE_STATE_FILE}")
    log.info(f"  Log: {LOG_FILE}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
