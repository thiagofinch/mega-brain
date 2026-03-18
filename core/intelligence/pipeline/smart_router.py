"""
smart_router.py -- Active File Router (Phase 1.3)
===================================================
Closes the observe-to-act gap.  Takes a ScopeDecision from
scope_classifier.classify() and ACTS on it: moves files to the correct
bucket inbox, creates .ref.yaml pointers in cascade buckets, or queues
ambiguous files for manual triage.

Downstream, it triggers inbox_organizer.organize_inbox() on every
affected bucket so files get sorted into entity/type subdirectories.

Integration model::

    scope_classifier.classify(ctx) -> ScopeDecision
                |
                v
    smart_router.route(file_path, decision) -> RouteResult
                |
                +--> [confidence >= 0.8] MOVE file to correct bucket inbox
                |
                +--> [cascade_buckets]   CREATE reference files in cascade inboxes
                |
                +--> [confidence < 0.8]  LOG to triage queue (no move)
                |
                +--> [after move/copy]   TRIGGER inbox_organizer on destination

What It Does NOT Do:

- Does NOT classify files (that is scope_classifier's job)
- Does NOT organize within a bucket (that is inbox_organizer's job)
- Does NOT process files downstream (no chunking, no RAG, no batch creation)
- Does NOT delete original files on cascade (creates references, not copies)
- Does NOT override human triage decisions (triage queue is advisory)

Version: 1.0.0
Date: 2026-03-10
Spec: docs/plans/epic1-phase1.3-smart-router-spec.md
Depends On: Phase 1.1 (scope_classifier.py) -- COMPLETE
"""

from __future__ import annotations

import json
import logging
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

from core.paths import LOGS, MISSION_CONTROL, ROUTING

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ROUTE ACTION CONSTANTS
# ---------------------------------------------------------------------------

ACTION_MOVE = "move"  # File moved to different bucket inbox
ACTION_REFERENCE = "reference"  # Reference file created in cascade bucket
ACTION_TRIAGE = "triage"  # Low confidence, queued for manual review
ACTION_NOOP = "noop"  # File already in correct bucket, no action

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# Confidence threshold for auto-routing (move without human approval)
AUTO_ROUTE_THRESHOLD = 0.80

# Confidence threshold below which we skip routing entirely (too uncertain)
SKIP_THRESHOLD = 0.30

# Reference file version (for future format migrations)
REF_VERSION = 1

# Triage queue maximum entries (FIFO eviction of oldest resolved entries)
TRIAGE_MAX_ENTRIES = 500

# Log file path
SMART_ROUTER_LOG = LOGS / "smart-router.jsonl"

# Triage queue path (files needing manual review)
TRIAGE_QUEUE = MISSION_CONTROL / "TRIAGE-QUEUE.json"

# Bucket inbox lookup -- resolved from core.paths ROUTING table
BUCKET_INBOXES: dict[str, Path] = {
    "external": ROUTING["external_inbox"],
    "business": ROUTING["business_inbox"],
    "personal": ROUTING["personal_inbox"],
}

# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------


@dataclass
class RouteResult:
    """Output of smart_router.route().

    Attributes:
        file_path: Original file path.
        action: ACTION_MOVE | ACTION_REFERENCE | ACTION_TRIAGE | ACTION_NOOP.
        source_bucket: Bucket the file was in.
        destination_bucket: Where primary routing sent it (same as source for noop).
        moved_to: New absolute path after move (empty if not moved).
        references_created: Absolute paths of .ref.yaml files created.
        triage_reason: Why file was sent to triage (empty if not triaged).
        confidence: From ScopeDecision (pass-through for logging).
        organized_buckets: Buckets where inbox_organizer was triggered.
        duration_ms: Total routing time in milliseconds.
    """

    file_path: str = ""
    action: str = ACTION_NOOP
    source_bucket: str = ""
    destination_bucket: str = ""
    moved_to: str = ""
    references_created: list[str] = field(default_factory=list)
    triage_reason: str = ""
    confidence: float = 0.0
    organized_buckets: list[str] = field(default_factory=list)
    duration_ms: int = 0


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(UTC).isoformat()


def detect_current_bucket(file_path: Path) -> str:
    """Determine which bucket a file currently resides in.

    Checks file_path against known bucket inbox paths from core.paths.ROUTING.

    Returns:
        'external' | 'business' | 'personal' | 'unknown'
    """
    path_str = str(file_path).replace("\\", "/")
    for bucket, inbox_path in BUCKET_INBOXES.items():
        inbox_str = str(inbox_path).replace("\\", "/")
        if path_str.startswith(inbox_str):
            return bucket
    return "unknown"


def _resolve_collision(dest: Path) -> Path:
    """Handle destination file collision by appending timestamp suffix.

    Args:
        dest: Desired destination path.

    Returns:
        Original path if no collision, or a timestamped variant.
    """
    if not dest.exists():
        return dest
    ts = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return dest.with_name(f"{dest.stem}_{ts}{dest.suffix}")


def _is_ref_file(file_path: Path) -> bool:
    """Check if a file is a .ref.yaml reference file.

    Returns:
        True if the file's name ends with .ref.yaml.
    """
    return file_path.name.endswith(".ref.yaml")


# ---------------------------------------------------------------------------
# CORE OPERATIONS
# ---------------------------------------------------------------------------


def move_to_bucket(file_path: Path, target_bucket: str) -> Path:
    """Move a file from its current location to the target bucket's inbox.

    Steps:
        1. Resolve target inbox path from BUCKET_INBOXES.
        2. Compute destination: {target_inbox}/{filename}.
        3. Handle collision (append timestamp suffix if file exists).
        4. Create parent dirs if needed.
        5. shutil.move(source, destination).
        6. Return new absolute path.

    Args:
        file_path: Absolute path to source file.
        target_bucket: One of 'external', 'business', 'personal'.

    Returns:
        New absolute path of the moved file.

    Raises:
        FileNotFoundError: If source does not exist.
        ValueError: If target_bucket is not recognized.
        OSError: If move fails.
    """
    if not file_path.exists():
        msg = f"Source file does not exist: {file_path}"
        raise FileNotFoundError(msg)

    if target_bucket not in BUCKET_INBOXES:
        msg = f"Unknown target bucket: {target_bucket}. Valid: {list(BUCKET_INBOXES.keys())}"
        raise ValueError(msg)

    target_inbox = BUCKET_INBOXES[target_bucket]
    dest = target_inbox / file_path.name
    dest = _resolve_collision(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(file_path), str(dest))
    return dest


def create_reference(
    original_path: Path,
    target_bucket: str,
    decision: object,
) -> Path:
    """Create a .ref.yaml pointer in the target bucket's inbox.

    The reference file contains metadata about the original file's location
    and why it was cascade-routed. Does NOT copy the actual file.

    Args:
        original_path: Absolute path to the original (primary) file.
        target_bucket: Bucket to create the reference in.
        decision: ScopeDecision object with classification metadata.

    Returns:
        Path to the created .ref.yaml file.
    """
    target_inbox = BUCKET_INBOXES[target_bucket]
    ref_name = f"{original_path.stem}.ref.yaml"
    ref_path = target_inbox / ref_name

    # Skip if reference already exists
    if ref_path.exists():
        logger.debug("Reference already exists, skipping: %s", ref_path)
        return ref_path

    source_bucket = detect_current_bucket(original_path)

    # Build cascade_reason from decision reasons that mention cascade-relevant signals
    cascade_reasons: list[str] = []
    detected_entities: list[str] = []
    scope_confidence: float = 0.0

    if hasattr(decision, "reasons"):
        cascade_reasons = [r for r in decision.reasons if r]
    if hasattr(decision, "detected_entities"):
        detected_entities = list(decision.detected_entities)
    if hasattr(decision, "confidence"):
        scope_confidence = decision.confidence

    ref_data = {
        "ref_version": REF_VERSION,
        "original_path": str(original_path),
        "original_bucket": source_bucket,
        "cascade_reason": ", ".join(cascade_reasons[:5]) if cascade_reasons else "cascade-routing",
        "scope_confidence": scope_confidence,
        "created_at": _now_iso(),
        "detected_entities": detected_entities,
    }

    ref_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ref_path, "w", encoding="utf-8") as f:
        f.write("# Reference file -- Generated by smart_router.py -- DO NOT EDIT MANUALLY\n")
        yaml.dump(ref_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return ref_path


def handle_cascades(
    file_path: Path,
    decision: object,
    result: RouteResult,
) -> None:
    """Create reference files in all cascade buckets.

    For each bucket in decision.cascade_buckets:
        - Skip if bucket == source bucket (already there)
        - Skip if bucket == destination bucket (already moved there)
        - Create .ref.yaml in that bucket's inbox
        - Append path to result.references_created

    Args:
        file_path: Current path of the file (after any moves).
        decision: ScopeDecision with cascade_buckets list.
        result: RouteResult to update with created references.
    """
    cascade_buckets: list[str] = getattr(decision, "cascade_buckets", [])
    if not cascade_buckets:
        return

    current_bucket = detect_current_bucket(file_path)
    dest_bucket = result.destination_bucket

    for bucket in cascade_buckets:
        if bucket == current_bucket:
            continue
        if bucket == dest_bucket:
            continue
        if bucket not in BUCKET_INBOXES:
            logger.debug("Unknown cascade bucket '%s', skipping", bucket)
            continue

        try:
            ref_path = create_reference(file_path, bucket, decision)
            result.references_created.append(str(ref_path))
        except Exception:
            logger.warning("Failed to create cascade reference in %s", bucket, exc_info=True)


def trigger_organizer(bucket: str, result: RouteResult) -> None:
    """Run inbox_organizer.organize_inbox() on the specified bucket.

    Catches and logs errors but never raises (router is non-blocking).
    Appends bucket to result.organized_buckets on success.

    Args:
        bucket: Bucket to organize ('external', 'business', 'personal').
        result: RouteResult to update.
    """
    try:
        from core.intelligence.pipeline.inbox_organizer import organize_inbox

        organize_inbox(bucket)
        result.organized_buckets.append(bucket)
    except ImportError:
        logger.debug("inbox_organizer not available, skipping organize for %s", bucket)
    except Exception:
        logger.warning("inbox_organizer failed for bucket %s", bucket, exc_info=True)


# ---------------------------------------------------------------------------
# TRIAGE QUEUE
# ---------------------------------------------------------------------------


def add_to_triage_queue(
    file_path: Path,
    decision: object,
    current_bucket: str,
) -> None:
    """Add a file to the manual triage queue.

    Reads TRIAGE-QUEUE.json, appends entry, writes back.
    Queue entries contain: file_path, current_bucket, suggested_bucket,
    confidence, reasons, timestamp.

    The queue is a JSON array of objects. Max 500 entries (FIFO eviction).

    Args:
        file_path: Absolute path to the file.
        decision: ScopeDecision from scope_classifier.
        current_bucket: Bucket the file is currently in.
    """
    # Read existing queue
    queue_data: dict = {"version": 1, "updated_at": "", "entries": []}
    if TRIAGE_QUEUE.exists():
        try:
            queue_data = json.loads(TRIAGE_QUEUE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.debug("Could not read triage queue, starting fresh")

    entries: list[dict] = queue_data.get("entries", [])

    # Build new entry
    suggested_bucket = getattr(decision, "primary_bucket", current_bucket)
    confidence = getattr(decision, "confidence", 0.0)
    reasons = getattr(decision, "reasons", [])
    detected_entities = getattr(decision, "detected_entities", [])

    new_entry = {
        "file_path": str(file_path),
        "current_bucket": current_bucket,
        "suggested_bucket": suggested_bucket,
        "confidence": confidence,
        "reasons": reasons[:10],
        "detected_entities": list(detected_entities),
        "added_at": _now_iso(),
        "resolved": False,
        "resolved_at": None,
        "resolved_bucket": None,
    }

    entries.append(new_entry)

    # FIFO eviction: remove oldest resolved entries first, then oldest unresolved
    if len(entries) > TRIAGE_MAX_ENTRIES:
        # First, try evicting resolved entries (oldest first)
        resolved = [e for e in entries if e.get("resolved")]
        unresolved = [e for e in entries if not e.get("resolved")]

        if len(resolved) > 0 and len(entries) > TRIAGE_MAX_ENTRIES:
            # Evict oldest resolved until under limit
            keep_resolved = max(0, TRIAGE_MAX_ENTRIES - len(unresolved))
            entries = unresolved + resolved[-keep_resolved:] if keep_resolved > 0 else unresolved
        else:
            # If still over, evict oldest unresolved
            entries = entries[-TRIAGE_MAX_ENTRIES:]

    queue_data["entries"] = entries
    queue_data["updated_at"] = _now_iso()

    try:
        TRIAGE_QUEUE.parent.mkdir(parents=True, exist_ok=True)
        TRIAGE_QUEUE.write_text(
            json.dumps(queue_data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except OSError:
        logger.warning("Failed to write triage queue", exc_info=True)


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------


def _log_route(result: RouteResult) -> None:
    """Append one JSONL entry to the smart-router log.

    Args:
        result: The RouteResult to log.
    """
    try:
        SMART_ROUTER_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": _now_iso(),
            "file_path": result.file_path,
            "action": result.action,
            "source_bucket": result.source_bucket,
            "destination_bucket": result.destination_bucket,
            "moved_to": result.moved_to,
            "references_created": result.references_created,
            "triage_reason": result.triage_reason,
            "confidence": result.confidence,
            "organized_buckets": result.organized_buckets,
            "duration_ms": result.duration_ms,
        }
        with open(SMART_ROUTER_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write smart-router log", exc_info=True)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------


def route(file_path: str | Path, decision: object) -> RouteResult:
    """Route a file based on scope_classifier's decision.

    This is the main public API. It inspects the ScopeDecision, decides
    whether to move the file, create cascade references, or queue for
    triage, then triggers inbox_organizer on affected buckets.

    Args:
        file_path: Absolute path to the file being routed.
        decision: ScopeDecision from scope_classifier.classify().

    Returns:
        RouteResult describing what actions were taken.
    """
    start_time = time.monotonic()
    fp = Path(file_path) if isinstance(file_path, str) else file_path

    source_bucket = detect_current_bucket(fp)
    confidence = getattr(decision, "confidence", 0.0)
    primary_bucket = getattr(decision, "primary_bucket", source_bucket)

    result = RouteResult(
        file_path=str(fp),
        source_bucket=source_bucket,
        destination_bucket=source_bucket,
        confidence=confidence,
    )

    # --- GUARD: Skip .ref.yaml files (prevent circular routing) ---
    if _is_ref_file(fp):
        result.action = ACTION_NOOP
        result.triage_reason = "ref file skipped"
        result.duration_ms = int((time.monotonic() - start_time) * 1000)
        _log_route(result)
        return result

    # --- GUARD: File disappeared mid-route ---
    if not fp.exists():
        result.action = ACTION_NOOP
        result.triage_reason = "file disappeared before routing"
        result.duration_ms = int((time.monotonic() - start_time) * 1000)
        _log_route(result)
        return result

    # --- GUARD: File in unknown location ---
    if source_bucket == "unknown":
        result.action = ACTION_NOOP
        result.triage_reason = "file not in any recognized bucket inbox"
        result.duration_ms = int((time.monotonic() - start_time) * 1000)
        _log_route(result)
        return result

    # --- GUARD: Skip if confidence too low ---
    if confidence < SKIP_THRESHOLD:
        result.action = ACTION_NOOP
        result.triage_reason = f"confidence {confidence} below skip threshold {SKIP_THRESHOLD}"
        result.duration_ms = int((time.monotonic() - start_time) * 1000)
        _log_route(result)
        return result

    # --- CASE 1: File already in correct bucket ---
    if primary_bucket == source_bucket:
        result.action = ACTION_NOOP
        result.destination_bucket = source_bucket
        # Still handle cascades (file is in right place but has secondary buckets)
        handle_cascades(fp, decision, result)
        trigger_organizer(source_bucket, result)
        result.duration_ms = int((time.monotonic() - start_time) * 1000)
        _log_route(result)
        return result

    # --- CASE 2: High confidence, move to correct bucket ---
    if confidence >= AUTO_ROUTE_THRESHOLD:
        try:
            new_path = move_to_bucket(fp, primary_bucket)
            result.action = ACTION_MOVE
            result.moved_to = str(new_path)
            result.destination_bucket = primary_bucket
            handle_cascades(new_path, decision, result)
            trigger_organizer(primary_bucket, result)
        except (FileNotFoundError, ValueError, OSError) as exc:
            logger.warning("Failed to move file to %s: %s", primary_bucket, exc)
            result.action = ACTION_TRIAGE
            result.triage_reason = f"move failed: {exc}"
            add_to_triage_queue(fp, decision, source_bucket)
        result.duration_ms = int((time.monotonic() - start_time) * 1000)
        _log_route(result)
        return result

    # --- CASE 3: Medium confidence, triage ---
    # (confidence >= SKIP_THRESHOLD but < AUTO_ROUTE_THRESHOLD)
    result.action = ACTION_TRIAGE
    result.triage_reason = (
        f"confidence {confidence} between "
        f"{SKIP_THRESHOLD}-{AUTO_ROUTE_THRESHOLD}: "
        f"current={source_bucket}, suggested={primary_bucket}"
    )
    add_to_triage_queue(fp, decision, source_bucket)
    # Still organize within current bucket
    trigger_organizer(source_bucket, result)
    result.duration_ms = int((time.monotonic() - start_time) * 1000)
    _log_route(result)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli_route(file_path_str: str) -> None:
    """Route a single file from the command line (testing/debugging)."""
    fp = Path(file_path_str).resolve()
    if not fp.exists():
        print(f"File not found: {fp}")
        sys.exit(1)

    from core.intelligence.pipeline.scope_classifier import (
        ClassificationContext,
        classify,
    )

    content = ""
    try:
        content = fp.read_text(errors="replace")[:5000]
    except OSError:
        pass

    ctx = ClassificationContext(
        text=content,
        filename=fp.name,
        file_path=str(fp),
        title=fp.stem,
    )
    decision = classify(ctx)
    result = route(fp, decision)

    print(f"File:        {fp.name}")
    print(f"Action:      {result.action}")
    print(f"Source:      {result.source_bucket}")
    print(f"Destination: {result.destination_bucket}")
    print(f"Confidence:  {result.confidence}")
    if result.moved_to:
        print(f"Moved to:    {result.moved_to}")
    if result.references_created:
        print(f"References:  {result.references_created}")
    if result.triage_reason:
        print(f"Triage:      {result.triage_reason}")
    print(f"Organized:   {result.organized_buckets}")
    print(f"Duration:    {result.duration_ms}ms")


def _cli_triage() -> None:
    """Show the triage queue."""
    if not TRIAGE_QUEUE.exists():
        print("No triage queue found.")
        return

    try:
        data = json.loads(TRIAGE_QUEUE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Error reading triage queue: {exc}")
        return

    entries = data.get("entries", [])
    unresolved = [e for e in entries if not e.get("resolved")]
    resolved = [e for e in entries if e.get("resolved")]

    print("\n=== TRIAGE QUEUE ===")
    print(f"Total: {len(entries)}  |  Unresolved: {len(unresolved)}  |  Resolved: {len(resolved)}")
    print(f"Updated: {data.get('updated_at', 'N/A')}\n")

    if not unresolved:
        print("No files pending triage.")
        return

    for i, entry in enumerate(unresolved, 1):
        fp = Path(entry["file_path"]).name
        print(f"  {i}. {fp}")
        print(
            f"     Current: {entry['current_bucket']}  ->  Suggested: {entry['suggested_bucket']}"
        )
        print(f"     Confidence: {entry['confidence']}  |  Added: {entry['added_at']}")
        if entry.get("reasons"):
            print(f"     Reasons: {', '.join(entry['reasons'][:3])}")
        print()


def _cli_stats() -> None:
    """Show routing stats from the JSONL log."""
    if not SMART_ROUTER_LOG.exists():
        print("No routing log found.")
        return

    counts: dict[str, int] = {}
    total = 0
    total_duration = 0

    with open(SMART_ROUTER_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                action = entry.get("action", "unknown")
                counts[action] = counts.get(action, 0) + 1
                total += 1
                total_duration += entry.get("duration_ms", 0)
            except json.JSONDecodeError:
                continue

    print("\n=== SMART ROUTER STATS ===")
    print(f"Total routes: {total}")
    if total > 0:
        print(f"Avg duration: {total_duration // total}ms")
    print()
    for action, count in sorted(counts.items()):
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {action:12s}: {count:5d}  ({pct:.1f}%)")
    print()


def main() -> int:
    """CLI entry point.

    Usage:
        python smart_router.py route /path/to/file.txt
        python smart_router.py triage
        python smart_router.py stats
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if len(sys.argv) < 2:
        print("Usage: python smart_router.py [route <path> | triage | stats]")
        return 1

    cmd = sys.argv[1]

    if cmd == "route" and len(sys.argv) >= 3:
        _cli_route(sys.argv[2])
        return 0

    if cmd == "triage":
        _cli_triage()
        return 0

    if cmd == "stats":
        _cli_stats()
        return 0

    print("Usage: python smart_router.py [route <path> | triage | stats]")
    return 1


if __name__ == "__main__":
    sys.exit(main())
