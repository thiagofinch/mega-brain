"""
inbox_watcher.py -- FSEvents Daemon for Inbox Directories
==========================================================
Long-running daemon that monitors all ``*/inbox/`` directories via macOS
FSEvents (through the ``watchdog`` library) and triggers the
classify-then-organize pipeline when new files land.

Closes the dead-file gap: files arriving via Finder drag-and-drop, browser
download, ``cp`` in terminal, or rsync from an external drive are now
automatically classified and organized -- not just files written by Claude
Code via the PostToolUse hook.

Usage::

    # Foreground (verbose)
    python -m core.intelligence.pipeline.inbox_watcher --verbose

    # One-shot sweep (process existing files, then exit)
    python -m core.intelligence.pipeline.inbox_watcher --once

    # Dry-run (log what would be processed, do not call classify/organize)
    python -m core.intelligence.pipeline.inbox_watcher --dry-run

Version: 1.0.0
Date: 2026-03-10
Spec: docs/plans/epic1-phase1.2-inbox-watcher-spec.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import signal
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from core.paths import ROUTING

# ---------------------------------------------------------------------------
# MODULE CONSTANTS
# ---------------------------------------------------------------------------

logger = logging.getLogger("inbox_watcher")

# Directories to monitor -- sourced from core.paths, never hardcoded.
# NOTE: workspace/inbox removed (S-02). All content routes to knowledge buckets.
WATCHED_DIRS: dict[str, Path] = {
    "external": ROUTING["external_inbox"],
    "business": ROUTING["business_inbox"],
    "personal": ROUTING["personal_inbox"],
}

# Debounce window in seconds.
DEBOUNCE_SECONDS: float = 2.0

# File readiness: maximum retry attempts and probe interval.
READINESS_MAX_RETRIES: int = 3
READINESS_PROBE_INTERVAL: float = 0.5
READINESS_RETRY_INTERVAL: float = 1.0

# Heartbeat interval (seconds) for state file updates.
HEARTBEAT_INTERVAL: float = 60.0

# Ignore pattern -- files that must NEVER trigger the pipeline.
IGNORE_PATTERN: re.Pattern[str] = re.compile(
    r"^\..*"  # dotfiles (.DS_Store, .hidden, etc.)
    r"|\.DS_Store$"
    r"|Thumbs\.db$"
    r"|\.gitkeep$"
    r"|.*\.(crdownload|part|download|tmp|swp|swo|partial)$"
    r"|^~\$"  # Office lock files
    r"|__pycache__",
    re.IGNORECASE,
)

# State and log paths from core.paths ROUTING.
STATE_PATH: Path = ROUTING["watcher_state"]
LOG_PATH: Path = ROUTING["watcher_log"]


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(UTC).isoformat()


def _should_ignore(filename: str) -> bool:
    """Return True if *filename* matches the ignore pattern."""
    return bool(IGNORE_PATTERN.search(filename))


def _resolve_bucket(path: Path) -> str | None:
    """Match a file path to its inbox bucket.

    Returns ``'external'``, ``'business'``, ``'personal'``, or ``None``.
    """
    for bucket, inbox_path in WATCHED_DIRS.items():
        try:
            path.relative_to(inbox_path)
            return bucket
        except ValueError:
            continue
    return None


def _file_ready(path: Path) -> bool:
    """Check that *path* exists and its size has stabilized.

    Retries up to ``READINESS_MAX_RETRIES`` times with 1-second intervals.
    Between size probes within a single attempt, waits 500 ms.

    Returns:
        ``True`` if the file is ready to process, ``False`` otherwise.
    """
    for attempt in range(READINESS_MAX_RETRIES):
        if not path.exists():
            logger.warning("File vanished before processing: %s", path)
            return False

        try:
            size_a = path.stat().st_size
        except OSError:
            logger.warning("Cannot stat file: %s", path, exc_info=True)
            return False

        if size_a == 0:
            # Empty file -- could still be writing.
            time.sleep(READINESS_RETRY_INTERVAL)
            continue

        time.sleep(READINESS_PROBE_INTERVAL)

        if not path.exists():
            logger.warning("File vanished during readiness check: %s", path)
            return False

        try:
            size_b = path.stat().st_size
        except OSError:
            logger.warning("Cannot stat file (probe 2): %s", path, exc_info=True)
            return False

        if size_a == size_b:
            return True

        # Size changed -- file still being written.
        logger.debug(
            "File size unstable (%d -> %d), retry %d/%d: %s",
            size_a,
            size_b,
            attempt + 1,
            READINESS_MAX_RETRIES,
            path,
        )
        time.sleep(READINESS_RETRY_INTERVAL)

    logger.error(
        "File not ready after %d attempts (size unstable): %s",
        READINESS_MAX_RETRIES,
        path,
    )
    return False


# ---------------------------------------------------------------------------
# LOGGING (JSONL)
# ---------------------------------------------------------------------------


def _log_event(
    path: Path,
    source_bucket: str,
    *,
    classified_bucket: str = "",
    confidence: float = 0.0,
    source_type: str = "unknown",
    detected_entities: list[str] | None = None,
    debounce_ms: int = 2000,
    readiness_attempts: int = 1,
    processing_ms: int = 0,
    event: str = "file_processed",
    error: str = "",
) -> None:
    """Append one JSONL line to the watcher log."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry: dict[str, object] = {
            "timestamp": _now_iso(),
            "event": event,
            "file_path": str(path),
            "file_size_bytes": path.stat().st_size if path.exists() else 0,
            "source_bucket": source_bucket,
        }
        if event == "file_processed":
            entry.update(
                {
                    "classified_bucket": classified_bucket,
                    "confidence": confidence,
                    "source_type": source_type,
                    "detected_entities": detected_entities or [],
                    "debounce_ms": debounce_ms,
                    "readiness_attempts": readiness_attempts,
                    "processing_ms": processing_ms,
                }
            )
        if error:
            entry["error"] = error
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write watcher log", exc_info=True)


# ---------------------------------------------------------------------------
# STATE FILE
# ---------------------------------------------------------------------------


class WatcherState:
    """Manages ``WATCHER-STATE.json`` read/write."""

    def __init__(self) -> None:
        self.total_events: int = 0
        self.total_processed: int = 0
        self.total_ignored: int = 0
        self.total_errors: int = 0
        self.last_event_at: str = ""
        self.last_processed_file: str = ""
        self.started_at: str = _now_iso()
        self.last_heartbeat: str = self.started_at
        self.status: str = "running"

        # Attempt to load existing stats for continuity.
        self._load()

    def _load(self) -> None:
        if STATE_PATH.exists():
            try:
                data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
                stats = data.get("stats", {})
                self.total_events = stats.get("total_events", 0)
                self.total_processed = stats.get("total_processed", 0)
                self.total_ignored = stats.get("total_ignored", 0)
                self.total_errors = stats.get("total_errors", 0)
            except Exception:
                logger.debug("Could not load existing state; starting fresh")

    def write(self) -> None:
        """Overwrite the state file with current snapshot."""
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0.0",
            "daemon": {
                "pid": os.getpid(),
                "started_at": self.started_at,
                "last_heartbeat": self.last_heartbeat,
                "status": self.status,
            },
            "stats": {
                "total_events": self.total_events,
                "total_processed": self.total_processed,
                "total_ignored": self.total_ignored,
                "total_errors": self.total_errors,
                "last_event_at": self.last_event_at,
                "last_processed_file": self.last_processed_file,
            },
            "watched_dirs": {k: str(v) for k, v in WATCHED_DIRS.items()},
        }
        STATE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# FILE PROCESSING
# ---------------------------------------------------------------------------


def process_file(
    file_path: str,
    state: WatcherState,
    *,
    dry_run: bool = False,
) -> None:
    """Run the classify-then-organize pipeline on a single file.

    Args:
        file_path: Absolute path string of the file to process.
        state: Shared ``WatcherState`` instance for stat tracking.
        dry_run: If ``True``, log what *would* happen but skip
            actual classification and organization.
    """
    path = Path(file_path)
    start = time.monotonic()

    # Determine which inbox this file is in.
    bucket = _resolve_bucket(path)
    if bucket is None:
        logger.warning("File not in any monitored inbox: %s", path)
        return

    # Readiness check.
    if not _file_ready(path):
        state.total_errors += 1
        _log_event(
            path,
            bucket,
            event="file_error",
            error=f"File not ready after {READINESS_MAX_RETRIES} attempts (size unstable)",
        )
        state.write()
        return

    state.total_events += 1
    state.last_event_at = _now_iso()

    if dry_run:
        logger.info("[DRY-RUN] Would process: %s (bucket=%s)", path.name, bucket)
        state.total_processed += 1
        state.last_processed_file = path.name
        state.write()
        return

    # Read content sample for classification.
    try:
        content = path.read_text(errors="replace")[:5000]
    except (OSError, UnicodeDecodeError):
        content = ""

    # Classify bucket.
    from core.intelligence.pipeline.scope_classifier import (
        ClassificationContext,
        classify,
    )

    ctx = ClassificationContext(
        text=content,
        filename=path.name,
        file_path=str(path),
        title=path.stem,
    )
    decision = classify(ctx)

    # Route via smart_router (classify -> route -> organize chain).
    # Falls back to direct organize_inbox if smart_router unavailable.
    try:
        from core.intelligence.pipeline.smart_router import route

        route(path, decision)
    except ImportError:
        from core.intelligence.pipeline.inbox_organizer import organize_inbox

        organize_inbox(bucket)

    # Trigger batch auto-creator after organize completes (Phase 1.4).
    try:
        from core.intelligence.pipeline.batch_auto_creator import scan_and_create

        scan_result = scan_and_create()
        if scan_result.batches_created:
            logger.info(
                "batch_auto_creator: created %d batches",
                len(scan_result.batches_created),
            )
    except ImportError:
        pass  # Phase 1.4 not yet deployed
    except Exception as exc:
        logger.warning("batch_auto_creator error: %s", exc)

    elapsed_ms = int((time.monotonic() - start) * 1000)

    # Log watcher-specific event.
    _log_event(
        path,
        bucket,
        classified_bucket=decision.primary_bucket,
        confidence=decision.confidence,
        source_type=decision.source_type,
        detected_entities=decision.detected_entities,
        processing_ms=elapsed_ms,
    )

    state.total_processed += 1
    state.last_processed_file = path.name
    state.write()

    logger.info(
        "Processed: %s -> bucket=%s (classified=%s, conf=%.2f) in %dms",
        path.name,
        bucket,
        decision.primary_bucket,
        decision.confidence,
        elapsed_ms,
    )


# ---------------------------------------------------------------------------
# STARTUP SWEEP
# ---------------------------------------------------------------------------


def startup_sweep(state: WatcherState, *, dry_run: bool = False) -> int:
    """Process any unorganized files already sitting in inbox directories.

    This handles files that arrived while the daemon was down.

    Returns:
        Number of files processed.
    """
    from core.intelligence.pipeline.inbox_organizer import (
        SKIP_NAMES,
        SUPPORTED_EXTENSIONS,
        _is_already_organized,
    )

    processed = 0

    for bucket_key, inbox_path in WATCHED_DIRS.items():
        if not inbox_path.exists():
            continue

        effective_bucket = bucket_key

        # Use the same inbox root that organize_inbox would use.
        from core.intelligence.pipeline.inbox_organizer import BUCKET_INBOXES

        inbox_root = BUCKET_INBOXES.get(effective_bucket)
        if inbox_root is None:
            inbox_root = inbox_path

        all_files = sorted(
            f
            for f in inbox_path.rglob("*")
            if f.is_file()
            and f.name not in SKIP_NAMES
            and not f.name.startswith(".")
            and f.suffix.lower() in SUPPORTED_EXTENSIONS
        )

        for filepath in all_files:
            if _should_ignore(filepath.name):
                continue
            if _is_already_organized(filepath, inbox_root):
                continue
            process_file(str(filepath), state, dry_run=dry_run)
            processed += 1

    if processed > 0:
        logger.info("Startup sweep processed %d file(s)", processed)
    else:
        logger.info("Startup sweep: all inboxes clean")

    return processed


# ---------------------------------------------------------------------------
# EVENT HANDLER
# ---------------------------------------------------------------------------


class InboxHandler(FileSystemEventHandler):
    """Watchdog handler for inbox file-created events.

    Uses per-path debounce timers to avoid processing files that are
    still being written (large copies, browser downloads, etc.).
    """

    def __init__(self, state: WatcherState, *, dry_run: bool = False) -> None:
        super().__init__()
        self._state = state
        self._dry_run = dry_run
        self._pending: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        """Called when a file or directory is created."""
        if event.is_directory:
            return

        src_path: str = event.src_path
        filename = Path(src_path).name

        if _should_ignore(filename):
            return

        self._schedule(src_path)

    def _schedule(self, src_path: str) -> None:
        """Schedule debounced processing for *src_path*."""
        with self._lock:
            existing = self._pending.get(src_path)
            if existing is not None:
                existing.cancel()

            timer = threading.Timer(
                DEBOUNCE_SECONDS,
                self._on_timer_fire,
                args=[src_path],
            )
            timer.daemon = True
            self._pending[src_path] = timer
            timer.start()

    def _on_timer_fire(self, src_path: str) -> None:
        """Called when the debounce timer fires for *src_path*."""
        with self._lock:
            self._pending.pop(src_path, None)

        try:
            process_file(src_path, self._state, dry_run=self._dry_run)
        except Exception:
            logger.error("Error processing file: %s", src_path, exc_info=True)
            self._state.total_errors += 1
            self._state.write()

    def cancel_all(self) -> None:
        """Cancel all pending debounce timers (used during shutdown)."""
        with self._lock:
            for timer in self._pending.values():
                timer.cancel()
            self._pending.clear()


# ---------------------------------------------------------------------------
# DAEMON MAIN LOOP
# ---------------------------------------------------------------------------


def run_daemon(*, dry_run: bool = False, once: bool = False, verbose: bool = False) -> int:
    """Start the inbox watcher daemon.

    Args:
        dry_run: Log what would be processed but skip classify/organize.
        once: Run startup sweep only, then exit.
        verbose: Set log level to DEBUG.

    Returns:
        Exit code (0 for clean shutdown, 1 for error).
    """
    # Configure logging.
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    state = WatcherState()
    state.started_at = _now_iso()
    state.status = "running"

    # Ensure watched directories exist.
    for inbox_path in WATCHED_DIRS.values():
        inbox_path.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Inbox watcher starting (pid=%d, dry_run=%s, once=%s)",
        os.getpid(),
        dry_run,
        once,
    )
    for name, path in WATCHED_DIRS.items():
        logger.info("  Watching: %s -> %s", name, path)

    # Write initial state.
    state.write()

    # Run startup sweep.
    startup_sweep(state, dry_run=dry_run)

    if once:
        state.status = "stopped"
        state.write()
        logger.info("--once mode: startup sweep complete, exiting")
        return 0

    # Set up watchdog observer.
    handler = InboxHandler(state, dry_run=dry_run)
    observer = Observer()

    for inbox_path in WATCHED_DIRS.values():
        observer.schedule(handler, str(inbox_path), recursive=True)

    # Graceful shutdown via signals.
    shutdown_event = threading.Event()

    def _on_signal(signum: int, _frame: object) -> None:
        sig_name = signal.Signals(signum).name
        logger.info("Received %s, shutting down...", sig_name)
        shutdown_event.set()

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    observer.start()
    logger.info("Observer started, entering main loop")

    try:
        while not shutdown_event.is_set():
            shutdown_event.wait(timeout=HEARTBEAT_INTERVAL)
            if not shutdown_event.is_set():
                state.last_heartbeat = _now_iso()
                state.write()
    finally:
        logger.info("Shutting down...")
        handler.cancel_all()
        observer.stop()
        observer.join(timeout=10.0)
        state.status = "stopped"
        state.last_heartbeat = _now_iso()
        state.write()
        logger.info("Inbox watcher stopped cleanly")

    return 0


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------


def main() -> int:
    """Parse CLI arguments and start the daemon."""
    parser = argparse.ArgumentParser(
        prog="inbox_watcher",
        description="FSEvents daemon that monitors inbox directories and triggers classify+organize.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be processed but do not call classify/organize.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run startup sweep only, then exit (useful for cron / testing).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Set log level to DEBUG.",
    )

    args = parser.parse_args()
    return run_daemon(dry_run=args.dry_run, once=args.once, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
