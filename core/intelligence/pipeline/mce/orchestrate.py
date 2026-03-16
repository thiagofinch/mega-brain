"""
orchestrate.py -- MCE Pipeline Orchestrator
============================================

Deterministic orchestrator that chains all non-LLM Python scripts into
one executable command interface.  The MCE Skill calls this for each
pipeline phase; LLM work (prompts) stays in the Skill.

Commands
--------
``ingest <file>``
    Classify, route, and organize a raw source file into the correct
    knowledge bucket.  Returns JSON with classification result.

``batch <source_slug>``
    Scan organized inbox for the given slug, create batches, trigger
    memory enrichment and workspace sync.  Returns JSON with batch IDs.

``finalize <slug>``
    Post-extraction finalization: memory enrichment from INSIGHTS-STATE,
    workspace sync, final metrics.  Returns JSON summary.

``status [slug]``
    Show current pipeline state, metadata, and metrics for a slug (or
    all active slugs if omitted).  Returns JSON.

``full <file>``
    Shortcut: ``ingest`` then ``batch`` then print status.  Does NOT
    run LLM phases -- those are the Skill's job.

Every command:
- Updates :class:`PipelineStateMachine` on relevant transitions.
- Updates :class:`MetadataManager` with phase progress.
- Starts/stops :class:`MetricsTracker` timers.
- Appends a structured JSON line to the JSONL audit log.
- Prints a single JSON object to stdout on success.

Constraints
~~~~~~~~~~~
- stdlib + PyYAML + python-dotenv only (no LLM calls).
- Exit 0 on success, 1 on handled error, 2 on fatal.

Usage::

    python -m core.intelligence.pipeline.mce.orchestrate ingest "path/to/file.txt"
    python -m core.intelligence.pipeline.mce.orchestrate batch alex-hormozi
    python -m core.intelligence.pipeline.mce.orchestrate finalize alex-hormozi
    python -m core.intelligence.pipeline.mce.orchestrate status alex-hormozi
    python -m core.intelligence.pipeline.mce.orchestrate full "path/to/file.txt"

Version: 1.0.0
Date: 2026-03-10
"""

from __future__ import annotations

import json
import logging
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path for direct invocation
# ---------------------------------------------------------------------------

from core.paths import ROOT as _PROJECT_ROOT


# ---------------------------------------------------------------------------
# Module imports (after path fix)
# ---------------------------------------------------------------------------

from core.intelligence.pipeline.mce.metadata_manager import MetadataManager  # noqa: E402
from core.intelligence.pipeline.mce.metrics import MetricsTracker  # noqa: E402
from core.intelligence.pipeline.mce.state_machine import PipelineStateMachine  # noqa: E402
from core.intelligence.pipeline.mce.workflow_detector import detect as detect_workflow  # noqa: E402

logger = logging.getLogger("mce.orchestrate")

# ---------------------------------------------------------------------------
# Lazy imports -- only loaded when the command that needs them runs.
# This avoids import-time failures if optional deps are missing.
# ---------------------------------------------------------------------------


def _import_scope_classifier():
    """Lazy import for scope_classifier to avoid heavy startup."""
    from core.intelligence.pipeline.scope_classifier import (
        ClassificationContext,
        classify,
    )

    return classify, ClassificationContext


def _import_smart_router():
    """Lazy import for smart_router."""
    from core.intelligence.pipeline.smart_router import route

    return route


def _import_inbox_organizer():
    """Lazy import for inbox_organizer."""
    from core.intelligence.pipeline.inbox_organizer import organize_inbox

    return organize_inbox


def _import_batch_auto_creator():
    """Lazy import for batch_auto_creator."""
    from core.intelligence.pipeline.batch_auto_creator import scan_and_create

    return scan_and_create


def _import_memory_enricher():
    """Lazy import for memory_enricher."""
    from core.intelligence.pipeline.memory_enricher import enrich_from_insights_state

    return enrich_from_insights_state


def _import_workspace_sync():
    """Lazy import for workspace_sync."""
    from core.intelligence.pipeline.workspace_sync import sync

    return sync


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

try:
    from core.paths import ARTIFACTS, LOGS, MISSION_CONTROL, ROUTING
except ImportError:
    ARTIFACTS = _PROJECT_ROOT / "artifacts"
    LOGS = _PROJECT_ROOT / "logs"
    MISSION_CONTROL = _PROJECT_ROOT / ".claude" / "mission-control"
    ROUTING = {
        "mce_state": MISSION_CONTROL / "mce",
        "mce_metrics_log": LOGS / "mce-metrics.jsonl",
    }

_ORCHESTRATE_LOG = LOGS / "mce-orchestrate.jsonl"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Directory names that should never be used as a source slug.
# When _slug_from_path() encounters one of these as the candidate, it walks
# one level higher in the path to find the real person/source directory.
_SLUG_SKIP_DIRS: set[str] = {
    "PESSOAL",
    "EMPRESA",
    "EXTERNAL",
    "BUSINESS",
    "PERSONAL",
    "RAW",
    "CALLS",
    "MEETINGS",
    "INBOX",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _append_jsonl(entry: dict[str, Any]) -> None:
    """Append a JSON line to the orchestrate audit log.

    Non-fatal: swallows all exceptions so it never blocks pipeline work.
    """
    try:
        _ORCHESTRATE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_ORCHESTRATE_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write orchestrate JSONL", exc_info=True)


def _json_out(data: dict[str, Any]) -> None:
    """Print a JSON object to stdout (machine-readable output)."""
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _slug_from_path(file_path: str | Path) -> str:
    """Best-effort slug extraction from a file path.

    Looks for known inbox/sources patterns like:
    - ``knowledge/external/inbox/{slug}/...``
    - ``knowledge/external/sources/{slug}/raw/...``
    - ``knowledge/business/inbox/{category}/{slug}/...``
    - ``knowledge/personal/inbox/{category}/{slug}/...``

    Directory names listed in :data:`_SLUG_SKIP_DIRS` are skipped so the
    function walks up until it finds a meaningful slug.

    Falls back to the immediate parent directory name (also skipping
    entries in ``_SLUG_SKIP_DIRS``), slugified.
    """
    parts = Path(file_path).resolve().parts
    # Try to find 'inbox' or 'sources' in the path and take the next component
    for i, part in enumerate(parts):
        if part.lower() in {"inbox", "sources"} and i + 1 < len(parts):
            candidate = parts[i + 1]
            # Skip generic category / structural folders
            offset = 2
            while candidate.upper() in _SLUG_SKIP_DIRS and i + offset < len(parts):
                candidate = parts[i + offset]
                offset += 1
            if candidate.upper() not in _SLUG_SKIP_DIRS:
                return candidate.lower().replace(" ", "-").replace("_", "-")

    # Fallback: walk up parent directories until we find a non-skip name
    p = Path(file_path).resolve()
    for ancestor in p.parents:
        if ancestor.name and ancestor.name.upper() not in _SLUG_SKIP_DIRS:
            return ancestor.name.lower().replace(" ", "-").replace("_", "-")

    # Ultimate fallback: immediate parent
    parent = Path(file_path).parent.name
    return parent.lower().replace(" ", "-").replace("_", "-")


def _build_result(
    command: str,
    *,
    success: bool,
    slug: str = "",
    duration_ms: float = 0.0,
    **extras: Any,
) -> dict[str, Any]:
    """Build a standardized result dict for JSON output and logging."""
    result: dict[str, Any] = {
        "command": command,
        "success": success,
        "timestamp": _now_iso(),
        "duration_ms": round(duration_ms, 1),
    }
    if slug:
        result["slug"] = slug
    result.update(extras)
    return result


# ---------------------------------------------------------------------------
# Command: ingest
# ---------------------------------------------------------------------------


def cmd_ingest(file_path: str) -> dict[str, Any]:
    """Classify, route, and organize a raw source file.

    Steps:
        1. Validate file exists.
        2. Run scope_classifier.classify() to determine bucket.
        3. Run smart_router.route() to move/reference the file.
        4. Run inbox_organizer.organize_inbox() on affected bucket.
        5. Detect workflow mode (greenfield/brownfield).
        6. Initialize state machine + metadata if first file for this slug.
        7. Log everything to JSONL.

    Args:
        file_path: Path to the raw source file.

    Returns:
        Structured result dict.
    """
    t0 = time.monotonic()
    resolved = Path(file_path).resolve()

    # Step 1: validate
    if not resolved.exists():
        return _build_result(
            "ingest",
            success=False,
            error=f"File not found: {file_path}",
            file_path=str(resolved),
        )

    if not resolved.is_file():
        return _build_result(
            "ingest",
            success=False,
            error=f"Not a file: {file_path}",
            file_path=str(resolved),
        )

    slug = _slug_from_path(resolved)

    # Step 2: classify
    classify_fn, ctx_cls = _import_scope_classifier()
    text = ""
    try:
        raw_bytes = resolved.read_bytes()
        text = raw_bytes.decode("utf-8", errors="replace")[:50_000]
    except OSError as exc:
        return _build_result(
            "ingest",
            success=False,
            slug=slug,
            error=f"Cannot read file: {exc}",
            file_path=str(resolved),
        )

    ctx = ctx_cls(
        text=text,
        filename=resolved.name,
        file_path=str(resolved),
    )

    try:
        decision = classify_fn(ctx)
    except Exception as exc:
        logger.warning("Classification failed for %s: %s", resolved.name, exc)
        return _build_result(
            "ingest",
            success=False,
            slug=slug,
            error=f"Classification failed: {exc}",
            file_path=str(resolved),
            duration_ms=(time.monotonic() - t0) * 1000,
        )

    # Step 3: route
    route = _import_smart_router()
    try:
        route_result = route(str(resolved), decision)
    except Exception as exc:
        logger.warning("Routing failed for %s: %s", resolved.name, exc)
        return _build_result(
            "ingest",
            success=False,
            slug=slug,
            error=f"Routing failed: {exc}",
            file_path=str(resolved),
            classification={
                "primary_bucket": getattr(decision, "primary_bucket", "unknown"),
                "confidence": getattr(decision, "confidence", 0.0),
            },
            duration_ms=(time.monotonic() - t0) * 1000,
        )

    # Step 4: organize inbox
    organize_inbox = _import_inbox_organizer()
    primary_bucket = getattr(decision, "primary_bucket", "external")
    try:
        org_result = organize_inbox(primary_bucket)
    except Exception as exc:
        logger.warning("Inbox organization failed: %s", exc)
        org_result = {"organized": 0, "error": str(exc)}

    # Step 5: workflow detection
    wf_mode = detect_workflow(slug)

    # Step 6: initialize state + metadata if first time
    sm = PipelineStateMachine(slug)
    mgr = MetadataManager.load(slug)
    if mgr is None:
        mgr = MetadataManager(
            slug,
            mode=wf_mode.mode,
            source_code=slug[:2].upper().replace("-", ""),
        )
        mgr.pipeline_status = "in_progress"
        mgr.save()

    # Initialize metrics
    mt = MetricsTracker.load(slug) or MetricsTracker(slug)
    mt.start_phase("ingest")
    elapsed = (time.monotonic() - t0) * 1000
    mt.end_phase("ingest")
    mt.save()

    # Track the source in metadata
    mgr.add_source(
        resolved.name,
        bucket=primary_bucket,
        confidence=getattr(decision, "confidence", 0.0),
    )
    mgr.save()

    # Build result
    result = _build_result(
        "ingest",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        file_path=str(resolved),
        classification={
            "primary_bucket": getattr(decision, "primary_bucket", "unknown"),
            "cascade_buckets": getattr(decision, "cascade_buckets", []),
            "confidence": round(getattr(decision, "confidence", 0.0), 3),
            "source_type": getattr(decision, "source_type", "unknown"),
            "reasons": getattr(decision, "reasons", [])[:5],
        },
        routing={
            "action": getattr(route_result, "action", "unknown"),
            "moved_to": str(getattr(route_result, "moved_to", "")),
            "references_created": getattr(route_result, "references_created", []),
        },
        organization={
            "organized": org_result.get("organized", 0) if isinstance(org_result, dict) else 0,
        },
        workflow={
            "mode": wf_mode.mode,
            "has_agent": wf_mode.has_agent,
            "has_dna": wf_mode.has_dna,
        },
        state={
            "current": sm.state,
            "metadata_status": mgr.pipeline_status,
        },
    )

    # Step 7: JSONL log
    _append_jsonl(result)

    return result


# ---------------------------------------------------------------------------
# Command: batch
# ---------------------------------------------------------------------------


def cmd_batch(source_slug: str) -> dict[str, Any]:
    """Scan organized inbox for a slug and create batches.

    Steps:
        1. Run batch_auto_creator.scan_and_create().
        2. Update state machine (init -> chunking if first batch).
        3. Update metadata with batch info.
        4. Time the operation.

    Args:
        source_slug: Person/source slug (e.g. ``"alex-hormozi"``).

    Returns:
        Structured result dict with batch IDs.
    """
    t0 = time.monotonic()

    # Load/create state infrastructure
    sm = PipelineStateMachine(source_slug)
    mgr = MetadataManager.load(source_slug)
    if mgr is None:
        wf = detect_workflow(source_slug)
        mgr = MetadataManager(
            source_slug,
            mode=wf.mode,
            source_code=source_slug[:2].upper().replace("-", ""),
        )
        mgr.pipeline_status = "in_progress"

    mt = MetricsTracker.load(source_slug) or MetricsTracker(source_slug)
    mt.start_phase("batch_creation")

    # Run batch auto-creator
    scan_and_create = _import_batch_auto_creator()
    try:
        scan_result = scan_and_create(dry_run=False)
    except Exception as exc:
        mt.end_phase("batch_creation")
        mt.save()
        elapsed = (time.monotonic() - t0) * 1000
        err_result = _build_result(
            "batch",
            success=False,
            slug=source_slug,
            error=f"Batch creation failed: {exc}",
            duration_ms=elapsed,
        )
        _append_jsonl(err_result)
        return err_result

    mt.end_phase("batch_creation")
    elapsed = (time.monotonic() - t0) * 1000

    # Extract batch info
    batches_for_slug = []
    all_batch_ids = []
    for br in getattr(scan_result, "batches_created", []):
        bid = getattr(br, "batch_id", "unknown")
        all_batch_ids.append(bid)
        src_name = getattr(br, "source_name", "").lower().replace(" ", "-")
        if src_name == source_slug or source_slug in src_name:
            batches_for_slug.append(
                {
                    "batch_id": bid,
                    "source_code": getattr(br, "source_code", ""),
                    "file_count": getattr(br, "file_count", 0),
                    "total_size_bytes": getattr(br, "total_size_bytes", 0),
                }
            )

    # Update state: move to chunking if still at init
    if sm.state == "init" and batches_for_slug:
        try:
            sm.start_chunking(None)  # transitions sends event
        except Exception:
            logger.debug("State transition init->chunking failed", exc_info=True)

    # Update metadata
    mgr.mark_phase_complete(
        "batch_creation",
        batches_created=len(batches_for_slug),
        all_batches=len(all_batch_ids),
    )
    mgr.save()
    mt.save()

    result = _build_result(
        "batch",
        success=True,
        slug=source_slug,
        duration_ms=elapsed,
        batches_for_slug=batches_for_slug,
        scan_summary={
            "total_batches_created": len(all_batch_ids),
            "files_scanned": getattr(scan_result, "files_scanned", 0),
            "files_already_batched": getattr(scan_result, "files_already_batched", 0),
            "files_below_threshold": getattr(scan_result, "files_below_threshold", 0),
            "scan_duration_ms": getattr(scan_result, "duration_ms", 0),
        },
        state={
            "current": sm.state,
            "metadata_status": mgr.pipeline_status,
        },
    )

    _append_jsonl(result)
    return result


# ---------------------------------------------------------------------------
# Command: finalize
# ---------------------------------------------------------------------------


def cmd_finalize(slug: str) -> dict[str, Any]:
    """Post-extraction finalization.

    Steps:
        1. Run memory_enricher on INSIGHTS-STATE.json.
        2. Run workspace_sync.
        3. Update state machine -> validation -> complete.
        4. Finalize metrics, append to JSONL audit.
        5. Mark metadata as complete.

    Args:
        slug: Person/source slug.

    Returns:
        Structured result dict.
    """
    t0 = time.monotonic()

    sm = PipelineStateMachine(slug)
    mgr = MetadataManager.load(slug) or MetadataManager(slug)
    mt = MetricsTracker.load(slug) or MetricsTracker(slug)
    mt.start_phase("finalization")

    # Step 1: Memory enrichment
    enrichment_result: dict[str, Any] = {}
    insights_path = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
    if insights_path.exists():
        try:
            enrich_fn = _import_memory_enricher()
            raw = enrich_fn(insights_path)
            enrichment_result = {
                "appended": raw.get("appended", 0) if isinstance(raw, dict) else 0,
                "skipped_dedup": raw.get("skipped_dedup", 0) if isinstance(raw, dict) else 0,
                "agents_enriched": raw.get("agents_enriched", []) if isinstance(raw, dict) else [],
            }
        except Exception as exc:
            logger.warning("Memory enrichment failed: %s", exc)
            enrichment_result = {"error": str(exc)}
    else:
        enrichment_result = {"skipped": "INSIGHTS-STATE.json not found"}

    # Step 2: Workspace sync
    sync_result: dict[str, Any] = {}
    try:
        sync_fn = _import_workspace_sync()
        raw_sync = sync_fn(dry_run=False, verbose=False)
        sync_result = {
            "synced": len(getattr(raw_sync, "synced", [])),
            "skipped": getattr(raw_sync, "skipped", 0),
            "errors": getattr(raw_sync, "errors", 0),
        }
    except Exception as exc:
        logger.warning("Workspace sync failed: %s", exc)
        sync_result = {"error": str(exc)}

    # Step 3: Update state machine through remaining transitions
    # Try to advance to validation -> complete
    for trigger_name in ("start_validation", "finish"):
        trigger_fn = getattr(sm, trigger_name, None)
        if trigger_fn is not None:
            try:
                trigger_fn(None)
            except Exception:
                logger.debug(
                    "State transition %s failed (may not be valid from %s)",
                    trigger_name,
                    sm.state,
                )

    # Step 4: finalize metrics
    mt.end_phase("finalization")
    mt.save()
    mt.append_to_jsonl()

    # Step 5: mark metadata complete
    mgr.mark_phase_complete("finalization")
    mgr.mark_complete()
    mgr.save()

    elapsed = (time.monotonic() - t0) * 1000

    result = _build_result(
        "finalize",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        enrichment=enrichment_result,
        workspace_sync=sync_result,
        state={
            "current": sm.state,
            "metadata_status": mgr.pipeline_status,
        },
        metrics={
            "total_duration_seconds": round(mt.total_duration_seconds, 1),
            "phases_timed": mt.phases_completed,
        },
    )

    _append_jsonl(result)
    return result


# ---------------------------------------------------------------------------
# Command: status
# ---------------------------------------------------------------------------


def cmd_status(slug: str | None = None) -> dict[str, Any]:
    """Show current pipeline state for a slug or discover active pipelines.

    Args:
        slug: Person slug, or None to scan for all active slugs.

    Returns:
        Structured result dict.
    """
    t0 = time.monotonic()

    if slug is None:
        # Discover all active MCE pipelines
        mce_base = Path(ROUTING.get("mce_state", MISSION_CONTROL / "mce"))
        active: list[dict[str, Any]] = []
        if mce_base.exists():
            for d in sorted(mce_base.iterdir()):
                if d.is_dir():
                    sm = PipelineStateMachine(d.name)
                    mgr = MetadataManager.load(d.name)
                    active.append(
                        {
                            "slug": d.name,
                            "state": sm.state,
                            "status": mgr.pipeline_status if mgr else "unknown",
                            "phases_complete": len(mgr.completed_phase_names) if mgr else 0,
                        }
                    )

        elapsed = (time.monotonic() - t0) * 1000
        return _build_result(
            "status",
            success=True,
            duration_ms=elapsed,
            active_pipelines=active,
            count=len(active),
        )

    # Single slug status
    sm = PipelineStateMachine(slug)
    mgr = MetadataManager.load(slug)
    mt = MetricsTracker.load(slug)
    wf = detect_workflow(slug)

    status_data: dict[str, Any] = {
        "state_machine": {
            "current_state": sm.state,
            "is_terminal": sm.is_terminal,
            "is_paused": sm.paused,
            "history_length": len(sm.history),
        },
        "workflow": wf.to_dict(),
    }

    if mgr:
        status_data["metadata"] = {
            "pipeline_status": mgr.pipeline_status,
            "mode": mgr.mode,
            "source_code": mgr.source_code,
            "phases_completed": mgr.completed_phase_names,
            "next_phase": mgr.next_incomplete_phase,
            "sources_processed": len(mgr.sources_processed),
        }
    else:
        status_data["metadata"] = None

    if mt:
        status_data["metrics"] = {
            "total_duration_seconds": round(mt.total_duration_seconds, 1),
            "phases_timed": mt.phases_completed,
            "phase_names": mt.phase_names,
        }
    else:
        status_data["metrics"] = None

    elapsed = (time.monotonic() - t0) * 1000
    return _build_result(
        "status",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        **status_data,
    )


# ---------------------------------------------------------------------------
# Command: full
# ---------------------------------------------------------------------------


def cmd_full(file_path: str) -> dict[str, Any]:
    """Shortcut: ingest + batch + status.

    Does NOT run LLM phases.  Those are the Skill's job.

    Args:
        file_path: Path to the raw source file.

    Returns:
        Combined result dict.
    """
    t0 = time.monotonic()

    # Step 1: ingest
    ingest_result = cmd_ingest(file_path)
    if not ingest_result.get("success"):
        return _build_result(
            "full",
            success=False,
            error="Ingest step failed",
            ingest=ingest_result,
            duration_ms=(time.monotonic() - t0) * 1000,
        )

    slug = ingest_result.get("slug", "")

    # Step 2: batch
    batch_result = cmd_batch(slug)

    # Step 3: status
    status_result = cmd_status(slug)

    elapsed = (time.monotonic() - t0) * 1000
    combined = _build_result(
        "full",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        ingest=ingest_result,
        batch=batch_result,
        status=status_result,
    )

    _append_jsonl(combined)
    return combined


# ---------------------------------------------------------------------------
# Argument parsing + main
# ---------------------------------------------------------------------------


_USAGE = """\
MCE Pipeline Orchestrator -- deterministic pipeline commands

Usage:
  python -m core.intelligence.pipeline.mce.orchestrate <command> [args]

Commands:
  ingest <file_path>     Classify + route + organize a source file
  batch <source_slug>    Create batches from organized inbox
  finalize <slug>        Post-extraction: enrich memory + sync workspace
  status [slug]          Show pipeline state (all if slug omitted)
  full <file_path>       Shortcut: ingest + batch + status

Examples:
  python -m core.intelligence.pipeline.mce.orchestrate ingest "knowledge/business/inbox/file.txt"
  python -m core.intelligence.pipeline.mce.orchestrate batch alex-hormozi
  python -m core.intelligence.pipeline.mce.orchestrate finalize alex-hormozi
  python -m core.intelligence.pipeline.mce.orchestrate status
  python -m core.intelligence.pipeline.mce.orchestrate full "inbox/transcript.txt"
"""


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code (0 = success, 1 = handled error, 2 = fatal).
    """
    args = argv if argv is not None else sys.argv[1:]

    # Configure logging to stderr so JSON on stdout stays clean
    logging.basicConfig(
        level=logging.WARNING,
        format="%(name)s: %(message)s",
        stream=sys.stderr,
    )

    if not args or args[0] in ("-h", "--help", "help"):
        print(_USAGE, file=sys.stderr)
        return 0

    command = args[0].lower()
    rest = args[1:]

    try:
        if command == "ingest":
            if not rest:
                print("Error: ingest requires <file_path>", file=sys.stderr)
                return 1
            result = cmd_ingest(rest[0])

        elif command == "batch":
            if not rest:
                print("Error: batch requires <source_slug>", file=sys.stderr)
                return 1
            result = cmd_batch(rest[0])

        elif command == "finalize":
            if not rest:
                print("Error: finalize requires <slug>", file=sys.stderr)
                return 1
            result = cmd_finalize(rest[0])

        elif command == "status":
            slug = rest[0] if rest else None
            result = cmd_status(slug)

        elif command == "full":
            if not rest:
                print("Error: full requires <file_path>", file=sys.stderr)
                return 1
            result = cmd_full(rest[0])

        else:
            print(f'Error: unknown command "{command}"', file=sys.stderr)
            print(_USAGE, file=sys.stderr)
            return 1

    except Exception:
        traceback.print_exc(file=sys.stderr)
        error_entry = {
            "command": command,
            "success": False,
            "timestamp": _now_iso(),
            "error": traceback.format_exc(),
        }
        _append_jsonl(error_entry)
        _json_out({"command": command, "success": False, "error": "Fatal error (see stderr)"})
        return 2

    _json_out(result)
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
