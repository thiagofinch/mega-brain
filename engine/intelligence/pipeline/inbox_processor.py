"""
Inbox Processor — Extract and convert files in bucket inboxes.
===============================================================

This module provides pre-processing for files in bucket inboxes before
organization. It converts PDFs and DOCXs to markdown using ss_bridge
(or fallback extractors), making them ready for the knowledge pipeline.

Usage:
    from engine.intelligence.pipeline.inbox_processor import process_inbox

    # Process all extractable files in external inbox
    result = process_inbox("external")

    # Process specific file
    result = process_file(Path("document.pdf"), source_tag="alex-hormozi")

Version: 1.0.0
Date: 2026-03-14
Story: Plan 2 — Skill Seekers Integration
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from engine.paths import LOGS, ROUTING

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────────────────

BUCKET_INBOXES: dict[str, Path] = {
    "external": ROUTING["external_inbox"],
    "business": ROUTING["business_inbox"],
    "personal": ROUTING["personal_inbox"],
}

# Extensions we can extract/convert
EXTRACTABLE_EXTENSIONS = {".pdf", ".docx", ".doc"}

# Skip these files
SKIP_NAMES = {".DS_Store", "Thumbs.db", ".gitkeep"}


# ── Single-item entry point (used by engine.operations.ingest) ─────────────


def process_inbox_item(
    source_path: str,
    bucket: str | None = None,
    **kwargs,
) -> dict:
    """Process a single inbox item through the classify → route pipeline.

    This is the entry point invoked by `engine.operations.ingest(...)`, which
    is what the `mega-brain ingest <path> --process` CLI calls.

    Behavior:
      1. Resolve the path (absolute or relative to repo root).
      2. For extractable binaries (.pdf/.docx/.doc) run `process_file` first
         to convert to markdown.
      3. For text-like files (.txt/.md/.json) or after conversion, run the
         classify → route chain to send the item into the correct bucket
         and trigger downstream MCE processing.

    Args:
        source_path: Path to the file (absolute or repo-relative).
        bucket: Optional bucket hint. If None, classifier decides.
        **kwargs: Passed through to underlying processors.

    Returns:
        dict with: success, input, output, bucket, classified_bucket,
        confidence, source_type, method, error.
    """
    path = Path(source_path)
    if not path.is_absolute():
        # Resolve relative to mega-brain repo root.
        from engine.paths import ROOT as REPO_ROOT
        path = (REPO_ROOT / source_path).resolve()
    else:
        path = path.resolve()

    if not path.exists():
        return {
            "success": False,
            "input": str(path),
            "error": f"File not found: {path}",
        }

    ext = path.suffix.lower()

    # Phase A: Binary → markdown conversion (PDF/DOCX only).
    converted_output: Path | None = None
    if ext in EXTRACTABLE_EXTENSIONS:
        convert_result = process_file(
            path,
            source_tag=kwargs.get("source_tag"),
            bucket=bucket or "external",
            delete_original=kwargs.get("delete_original", False),
            use_fallback=kwargs.get("use_fallback", True),
        )
        if not convert_result.get("success"):
            return {
                "success": False,
                "input": str(path),
                "output": None,
                "error": f"Conversion failed: {convert_result.get('error')}",
                "method": convert_result.get("method"),
            }
        converted_output = Path(convert_result["output"])
        # Continue the chain on the converted markdown file.
        target_path = converted_output
    else:
        target_path = path

    # Phase B: Classify → route chain.
    try:
        content = target_path.read_text(errors="replace")[:5000]
    except (OSError, UnicodeDecodeError) as e:
        return {
            "success": False,
            "input": str(target_path),
            "error": f"Read failed: {e}",
        }

    try:
        from engine.intelligence.pipeline.scope_classifier import (
            ClassificationContext,
            classify,
        )
        ctx = ClassificationContext(
            text=content,
            filename=target_path.name,
            file_path=str(target_path),
            title=target_path.stem,
        )
        decision = classify(ctx)
    except Exception as e:
        logger.exception("classify failed for %s", target_path)
        return {
            "success": False,
            "input": str(target_path),
            "error": f"classify failed: {e}",
        }

    # Route via smart_router (preferred) with fallback to direct organize.
    routed_to = None
    try:
        from engine.intelligence.pipeline.smart_router import route as smart_route
        smart_route(target_path, decision)
        routed_to = "smart_router"
    except ImportError:
        try:
            from engine.intelligence.pipeline.inbox_organizer import organize_inbox
            organize_inbox(decision.primary_bucket or bucket or "external")
            routed_to = "inbox_organizer.fallback"
        except Exception as e:
            return {
                "success": False,
                "input": str(target_path),
                "error": f"routing failed: {e}",
                "classified_bucket": getattr(decision, "primary_bucket", None),
            }
    except Exception as e:
        logger.exception("smart_router failed for %s", target_path)
        return {
            "success": False,
            "input": str(target_path),
            "error": f"smart_router failed: {e}",
            "classified_bucket": getattr(decision, "primary_bucket", None),
        }

    # Phase C: Optional batch auto-creator hook.
    try:
        from engine.intelligence.pipeline.batch_auto_creator import scan_and_create
        scan_result = scan_and_create()
        batches_created = list(getattr(scan_result, "batches_created", []) or [])
    except Exception:
        batches_created = []

    return {
        "success": True,
        "input": str(path),
        "output": str(converted_output) if converted_output else str(target_path),
        "bucket": bucket,
        "classified_bucket": getattr(decision, "primary_bucket", None),
        "confidence": getattr(decision, "confidence", None),
        "source_type": getattr(decision, "source_type", None),
        "method": routed_to,
        "batches_created": batches_created,
        "error": None,
    }


# ── File Processing ─────────────────────────────────────────────────────────


def _detect_source_tag(filepath: Path) -> str:
    """Detect source tag from file path or filename.

    Checks parent directories and filename for known entity patterns.

    Args:
        filepath: Path to the file

    Returns:
        Source tag string (kebab-case) or "_untagged"
    """
    # Check if already in an entity subdirectory
    # e.g., inbox/alex-hormozi/document.pdf -> "alex-hormozi"
    parent_name = filepath.parent.name
    if parent_name and not parent_name.startswith((".", "_", "inbox")):
        return parent_name

    # Check grandparent
    grandparent_name = filepath.parent.parent.name
    if grandparent_name and not grandparent_name.startswith((".", "_", "inbox")):
        return grandparent_name

    # Could integrate with inbox_organizer.detect_entity here
    # For now, return untagged
    return "_untagged"


def process_file(
    filepath: Path,
    source_tag: str | None = None,
    bucket: str = "external",
    delete_original: bool = False,
    use_fallback: bool = True,
) -> dict:
    """Extract/convert a single file to markdown.

    Args:
        filepath: Path to PDF or DOCX file
        source_tag: Optional source tag (auto-detected if None)
        bucket: Knowledge bucket for output
        delete_original: Whether to delete original after successful conversion
        use_fallback: Whether to use lightweight extractors if SS unavailable

    Returns:
        Dict with: success, input, output, method, error
    """
    filepath = Path(filepath).resolve()

    if not filepath.exists():
        return {
            "success": False,
            "input": str(filepath),
            "output": None,
            "method": None,
            "error": "File not found",
        }

    ext = filepath.suffix.lower()
    if ext not in EXTRACTABLE_EXTENSIONS:
        return {
            "success": False,
            "input": str(filepath),
            "output": None,
            "method": None,
            "error": f"Unsupported extension: {ext}",
        }

    # Auto-detect source tag if not provided
    if not source_tag:
        source_tag = _detect_source_tag(filepath)

    try:
        from engine.intelligence.pipeline.ss_bridge import (
            ingest_docx,
            ingest_pdf,
            is_ss_available,
        )

        method = "ss_bridge" if is_ss_available() else "fallback"

        if ext == ".pdf":
            output_path = ingest_pdf(
                filepath,
                source_tag=source_tag,
                bucket=bucket,
                use_fallback=use_fallback,
            )
        elif ext in (".docx", ".doc"):
            output_path = ingest_docx(
                filepath,
                source_tag=source_tag,
                bucket=bucket,
                use_fallback=use_fallback,
            )
        else:
            return {
                "success": False,
                "input": str(filepath),
                "output": None,
                "method": None,
                "error": f"No handler for {ext}",
            }

        # Delete original if requested and conversion succeeded
        if delete_original and output_path.exists():
            filepath.unlink()

        return {
            "success": True,
            "input": str(filepath),
            "output": str(output_path),
            "method": method,
            "error": None,
        }

    except ImportError as e:
        logger.warning("ss_bridge import failed: %s", e)
        return {
            "success": False,
            "input": str(filepath),
            "output": None,
            "method": None,
            "error": f"Import error: {e}",
        }
    except RuntimeError as e:
        return {
            "success": False,
            "input": str(filepath),
            "output": None,
            "method": None,
            "error": str(e),
        }
    except Exception as e:
        logger.exception("Unexpected error processing %s", filepath)
        return {
            "success": False,
            "input": str(filepath),
            "output": None,
            "method": None,
            "error": f"Unexpected: {e}",
        }


# ── Inbox Processing ────────────────────────────────────────────────────────


def process_inbox(
    bucket: Literal["external", "business", "personal"] = "external",
    delete_originals: bool = False,
    use_fallback: bool = True,
) -> dict:
    """Process all extractable files in a bucket inbox.

    Finds PDFs and DOCXs, converts them to markdown, and logs results.

    Args:
        bucket: Which bucket inbox to process
        delete_originals: Whether to delete originals after conversion
        use_fallback: Whether to use lightweight extractors if SS unavailable

    Returns:
        Summary dict with: processed, skipped, failed, results
    """
    if bucket not in BUCKET_INBOXES:
        return {
            "error": f"Unknown bucket: {bucket}",
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "results": [],
        }

    inbox_path = BUCKET_INBOXES[bucket]
    if not inbox_path.exists():
        logger.info("Inbox does not exist: %s", inbox_path)
        return {
            "bucket": bucket,
            "inbox": str(inbox_path),
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "results": [],
        }

    # Find all extractable files
    extractable = []
    for ext in EXTRACTABLE_EXTENSIONS:
        extractable.extend(inbox_path.rglob(f"*{ext}"))
        # Also match uppercase
        extractable.extend(inbox_path.rglob(f"*{ext.upper()}"))

    # Filter out skipped files
    extractable = [
        f
        for f in extractable
        if f.is_file() and f.name not in SKIP_NAMES and not f.name.startswith(".")
    ]

    processed = 0
    skipped = 0
    failed = 0
    results = []

    for filepath in sorted(set(extractable)):
        # Check if markdown version already exists
        md_sibling = filepath.with_suffix(".md")
        if md_sibling.exists():
            skipped += 1
            results.append(
                {
                    "input": str(filepath),
                    "status": "skipped",
                    "reason": "markdown exists",
                }
            )
            continue

        # Process
        result = process_file(
            filepath,
            source_tag=None,  # auto-detect
            bucket=bucket,
            delete_original=delete_originals,
            use_fallback=use_fallback,
        )

        if result["success"]:
            processed += 1
            results.append(
                {
                    "input": str(filepath),
                    "output": result["output"],
                    "status": "processed",
                    "method": result["method"],
                }
            )
        else:
            failed += 1
            results.append(
                {
                    "input": str(filepath),
                    "status": "failed",
                    "error": result["error"],
                }
            )

    summary = {
        "bucket": bucket,
        "inbox": str(inbox_path),
        "processed": processed,
        "skipped": skipped,
        "failed": failed,
        "results": results,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    # Write log
    _write_process_log(summary)

    return summary


def process_all_inboxes(
    delete_originals: bool = False,
    use_fallback: bool = True,
) -> dict:
    """Process extractable files across all bucket inboxes.

    Returns:
        Dict keyed by bucket name with individual summaries.
    """
    results = {}
    for bucket in BUCKET_INBOXES:
        results[bucket] = process_inbox(
            bucket=bucket,
            delete_originals=delete_originals,
            use_fallback=use_fallback,
        )
    return results


# ── Logging ─────────────────────────────────────────────────────────────────


def _write_process_log(summary: dict) -> None:
    """Append process log entry to JSONL file."""
    log_dir = LOGS / "inbox-processor"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"process-{summary.get('bucket', 'unknown')}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False, default=str) + "\n")


# ── CLI ─────────────────────────────────────────────────────────────────────


def main() -> int:
    """CLI entry point.

    Usage:
        python inbox_processor.py                 # status of all inboxes
        python inbox_processor.py external        # process external inbox
        python inbox_processor.py all             # process all inboxes
        python inbox_processor.py <path>          # process single file
    """
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if len(sys.argv) < 2:
        # Status mode
        print("\n=== INBOX PROCESSOR — Status ===\n")

        # Check ss_bridge availability
        try:
            from engine.intelligence.pipeline.ss_bridge import get_bridge_status

            status = get_bridge_status()
            print(f"  SS Available:       {status['ss_available']}")
            print(f"  SS Video Available: {status['ss_video_available']}")
            print(f"  SS Version:         {status['ss_version'] or 'N/A'}")
            print(f"  Fallback Enabled:   {status['fallback_enabled']}")
        except ImportError:
            print("  SS Bridge: Not available (import error)")
        print()

        # Show inbox status
        for bucket, inbox_path in BUCKET_INBOXES.items():
            if not inbox_path.exists():
                print(f"  [{bucket:10s}] (inbox does not exist)")
                continue

            # Count extractable files
            extractable = []
            for ext in EXTRACTABLE_EXTENSIONS:
                extractable.extend(inbox_path.rglob(f"*{ext}"))
                extractable.extend(inbox_path.rglob(f"*{ext.upper()}"))

            extractable = [
                f
                for f in extractable
                if f.is_file() and f.name not in SKIP_NAMES and not f.name.startswith(".")
            ]

            # Count those without markdown sibling
            needs_processing = [f for f in extractable if not f.with_suffix(".md").exists()]

            print(
                f"  [{bucket:10s}] {len(extractable)} extractable, "
                f"{len(needs_processing)} need processing"
            )

        print()
        return 0

    cmd = sys.argv[1]

    # Process single file
    if os.path.isfile(cmd):
        result = process_file(Path(cmd))
        print(f"Input:  {result['input']}")
        print(f"Status: {'success' if result['success'] else 'failed'}")
        if result["success"]:
            print(f"Output: {result['output']}")
            print(f"Method: {result['method']}")
        else:
            print(f"Error:  {result['error']}")
        return 0 if result["success"] else 1

    # Process bucket
    if cmd in BUCKET_INBOXES:
        summary = process_inbox(cmd)
        _print_summary(cmd, summary)
        return 0

    # Process all
    if cmd == "all":
        results = process_all_inboxes()
        for bucket, summary in results.items():
            _print_summary(bucket, summary)
        return 0

    print("Usage: python inbox_processor.py [external|business|personal|all|<file>]")
    return 1


def _print_summary(bucket: str, summary: dict) -> None:
    """Print formatted summary."""
    print(f"\n--- {bucket.upper()} ---")
    if "error" in summary:
        print(f"  Error: {summary['error']}")
        return

    print(f"  Processed: {summary.get('processed', 0)}")
    print(f"  Skipped:   {summary.get('skipped', 0)}")
    print(f"  Failed:    {summary.get('failed', 0)}")

    if summary.get("results"):
        for r in summary["results"]:
            if r["status"] == "processed":
                print(f"    ✓ {Path(r['input']).name} ({r['method']})")
            elif r["status"] == "skipped":
                print(f"    - {Path(r['input']).name} ({r['reason']})")
            else:
                print(f"    ✗ {Path(r['input']).name} ({r['error']})")


if __name__ == "__main__":
    import sys

    sys.exit(main())
