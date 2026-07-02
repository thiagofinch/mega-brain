#!/usr/bin/env python3
"""
Pipeline Orchestrator Hook v1.0
================================
Single PostToolUse hook that routes to the appropriate pipeline script
based on what file was written/edited.

Replaces the need for 5 separate hooks.  Parses stdin once, checks
file_path against known patterns, and dispatches to:

  inbox_organizer       -- files written to any bucket inbox
  sop_detector          -- insight JSON written to knowledge/business/insights/
  dossier_compiler      -- dossier_trigger log entry says CREATE
  agent_generator       -- agent_creation_trigger state says READY
  insight_speaker_linker-- meeting transcript written to workspace/inbox/meetings/

Design:
  - Never blocks (always exit 0, always {"continue": true}).
  - Logs every dispatch to logs/pipeline-orchestrator.jsonl.
  - Imports target modules lazily (only when the route matches).
  - stdlib + PyYAML only.

Hook: PostToolUse | Timeout: 10s | Version: 1.0.0
Story: S10 — EPIC-REORG-001
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

try:
    from engine.paths import (
        BUSINESS_INSIGHTS,
        KNOWLEDGE_BUSINESS,
        KNOWLEDGE_EXTERNAL,
        KNOWLEDGE_PERSONAL,
        LOGS,
        MISSION_CONTROL,
        WORKSPACE_INBOX,
    )
except ImportError:
    # Fallback for environments where core.paths is not importable
    KNOWLEDGE_EXTERNAL = _ROOT / "knowledge" / "external"
    KNOWLEDGE_BUSINESS = _ROOT / "knowledge" / "business"
    KNOWLEDGE_PERSONAL = _ROOT / "knowledge" / "personal"
    BUSINESS_INSIGHTS = KNOWLEDGE_BUSINESS / "insights"
    WORKSPACE_INBOX = _ROOT / "workspace" / "inbox"
    LOGS = _ROOT / "logs"
    MISSION_CONTROL = _ROOT / ".claude" / "mission-control"

ORCHESTRATOR_LOG = LOGS / "pipeline-orchestrator.jsonl"

# Bucket inbox roots (mirroring inbox_organizer.py BUCKET_INBOXES)
_INBOX_MARKERS: list[str] = [
    "knowledge/external/inbox/",
    "knowledge/business/inbox/",
    "knowledge/personal/inbox/",
]

# Business insight path marker
_INSIGHT_MARKER = "knowledge/business/insights/"

# Meeting transcript marker (workspace inbox for meetings)
_MEETING_MARKERS: list[str] = [
    "workspace/inbox/meetings/",
    "workspace/inbox/meeting",
    "knowledge/business/inbox/meetings/",
]

# Dossier trigger log — we check this for recent CREATE decisions
_TRIGGER_LOG = LOGS / "triggers.jsonl"

# Agent discovery state — we check for READY persons
_DISCOVERY_STATE = MISSION_CONTROL / "DISCOVERY-STATE.json"


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------


def _log_event(
    route: str,
    file_path: str,
    result: str,
    detail: str = "",
) -> None:
    """Append one event to the orchestrator JSONL log."""
    try:
        ORCHESTRATOR_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "route": route,
            "file_path": file_path,
            "result": result,
            "detail": detail[:300],
        }
        with open(ORCHESTRATOR_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Never let logging crash the hook


# ---------------------------------------------------------------------------
# ROUTE 0: ADVANCE-TRIGGER LISTENER  [N3/G1, @architect C-1..C-6, 2026-05-13]
# ---------------------------------------------------------------------------
#
# Detects writes of ``<batch_id>.advance-trigger.json`` markers and spawns
# ``python -m engine.intelligence.pipeline.mce.orchestrate auto-advance <slug>``
# as a detached subprocess with stdout/stderr captured.
#
# Constraints (binding):
#   - C-2: listener target <500ms (just read marker + flock + Popen + log + exit).
#   - C-3a: marker file is SOLE trigger.
#   - C-3b: ``flock(LOCK_EX|LOCK_NB)`` on sibling ``.advance-trigger.lock``.
#   - C-3c: FSM state check happens INSIDE ``cmd_auto_advance`` (defense in depth).
#   - C-5a: subprocess output → ``logs/mce/<slug>/auto-advance-<batch_id>-<ts>.log``.
#   - C-5b: JSONL audit in ``logs/pipeline-orchestrator.jsonl`` (existing log).
#   - C-6a: requires ``schema_version=1`` + ``expected_state`` in marker.
#   - C-6b: skip if sibling ``.advance-trigger.consumed`` sentinel exists.
# ---------------------------------------------------------------------------


def _try_flock_nb(lock_path: Path):
    """Acquire a non-blocking exclusive flock on ``lock_path``.

    Returns the open file handle (caller is responsible for cleanup), or
    ``None`` if the lock is already held by another process / on non-Unix.

    Note: the file handle is intentionally not wrapped in ``with``; the OS
    releases the lock when the hook process exits.
    """
    try:
        import fcntl
    except ImportError:  # Windows / unusual platform
        return None

    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(lock_path, "a+")  # noqa: SIM115 — deferred close: see docstring
    except OSError:
        return None

    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except OSError:
        try:
            fh.close()
        except OSError:
            pass
        return None


def _route_advance_trigger(file_path: str) -> bool:
    """Detect ``.advance-trigger.json`` writes and spawn ``cmd_auto_advance``.

    Marker payload schema (v1):
        ``{schema_version, status, expected_state, slug, batch_id, ts, ttl_hours, retry_count}``

    Returns True if the route matched (regardless of spawn outcome — handled).
    """
    if not file_path.endswith(".advance-trigger.json"):
        return False

    marker_path = Path(file_path)
    if not marker_path.is_absolute():
        marker_path = _ROOT / marker_path

    if not marker_path.exists():
        _log_event(
            "batch_status",
            file_path,
            "skipped_missing",
            "marker file vanished",
        )
        return True

    # C-6a: schema_version + expected_state required.
    try:
        payload = json.loads(marker_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        _log_event("batch_status", file_path, "skipped_bad_json", str(exc))
        return True

    if payload.get("schema_version") != 1:
        _log_event(
            "batch_status",
            file_path,
            "skipped_bad_schema",
            f"schema_version={payload.get('schema_version')!r}",
        )
        return True

    slug = payload.get("slug", "")
    batch_id = payload.get("batch_id", "")
    if not slug or not batch_id:
        _log_event(
            "batch_status",
            file_path,
            "skipped_incomplete",
            f"slug={slug!r} batch_id={batch_id!r}",
        )
        return True

    # C-6b: skip if .consumed sentinel for this batch already exists.
    consumed = marker_path.parent / f"{batch_id}.advance-trigger.consumed"
    if consumed.exists():
        _log_event(
            "batch_status",
            file_path,
            "skipped_consumed",
            f"batch_id={batch_id}",
        )
        return True

    # C-3b: flock non-blocking on sibling .lock.
    lock_path = marker_path.parent / f"{batch_id}.advance-trigger.lock"
    lock_fh = _try_flock_nb(lock_path)
    if lock_fh is None:
        _log_event(
            "batch_status",
            file_path,
            "skipped_locked",
            f"batch_id={batch_id}",
        )
        return True

    # Build subprocess command.
    cmd = [
        sys.executable,
        "-m",
        "engine.intelligence.pipeline.mce.orchestrate",
        "auto-advance",
        slug,
    ]

    # C-5a: subprocess output → logs/mce/<slug>/auto-advance-<batch_id>-<ts>.log
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_log_path = LOGS / "mce" / slug / f"auto-advance-{batch_id}-{ts}.log"
    try:
        out_log_path.parent.mkdir(parents=True, exist_ok=True)
        out_log = open(out_log_path, "ab")  # noqa: SIM115 — handed to Popen
    except OSError as exc:
        try:
            lock_fh.close()
        except OSError:
            pass
        _log_event(
            "batch_status",
            file_path,
            "popen_failed",
            f"could not open log {out_log_path}: {exc}",
        )
        return True

    # Detached subprocess — caller (hook) returns immediately.
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=out_log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            cwd=str(_ROOT),
            close_fds=True,
            start_new_session=True,
            env=os.environ.copy(),
        )
        # Do NOT call proc.wait(); intentionally fire-and-forget.
        # Note: lock_fh is intentionally NOT released here — the OS releases it
        # when the hook process exits, freeing the slot for the next trigger.
        _log_event(
            "batch_status",
            file_path,
            "spawned",
            f"batch_id={batch_id} slug={slug} pid={proc.pid} log={out_log_path.name}",
        )
    except (OSError, ValueError) as exc:
        try:
            out_log.close()
        except OSError:
            pass
        try:
            lock_fh.close()
        except OSError:
            pass
        _log_event("batch_status", file_path, "popen_failed", str(exc))

    return True


# ---------------------------------------------------------------------------
# ROUTE 1: INBOX ORGANIZER
# ---------------------------------------------------------------------------


def _route_inbox_organizer(file_path: str) -> bool:
    """Trigger inbox_organizer when files land in a bucket inbox.

    Determines which bucket was written to and organizes only that bucket.
    Returns True if handled.
    """
    bucket: str | None = None
    if "knowledge/external/inbox/" in file_path:
        bucket = "external"
    elif "knowledge/business/inbox/" in file_path:
        bucket = "business"
    elif "knowledge/personal/inbox/" in file_path:
        bucket = "personal"

    if bucket is None:
        return False

    try:
        from engine.intelligence.pipeline.inbox_organizer import organize_inbox

        summary = organize_inbox(bucket)
        organized = summary.get("organized", 0)
        _log_event(
            "inbox_organizer",
            file_path,
            "ok",
            f"bucket={bucket} organized={organized}",
        )
        return True
    except Exception as exc:
        _log_event("inbox_organizer", file_path, "error", str(exc))
        return True  # Handled (even if errored) — don't retry other routes


# ---------------------------------------------------------------------------
# ROUTE 2: SOP DETECTOR
# ---------------------------------------------------------------------------


def _route_sop_detector(file_path: str) -> bool:
    """Trigger sop_detector when insight JSON is written to business insights."""
    if _INSIGHT_MARKER not in file_path:
        return False

    if not file_path.endswith(".json"):
        return False

    try:
        from engine.intelligence.pipeline.sop_detector import (
            detect_sops,
            save_sop_draft,
        )

        target = Path(file_path)
        if not target.is_absolute():
            target = _ROOT / target

        sops = detect_sops(target)
        saved_count = 0
        for sop in sops:
            save_sop_draft(sop)
            saved_count += 1

        _log_event(
            "sop_detector",
            file_path,
            "ok",
            f"detected={len(sops)} saved={saved_count}",
        )
        return True
    except Exception as exc:
        _log_event("sop_detector", file_path, "error", str(exc))
        return True


# ---------------------------------------------------------------------------
# ROUTE 3: DOSSIER COMPILER (checks trigger log for CREATE decisions)
# ---------------------------------------------------------------------------


def _route_dossier_compiler(file_path: str) -> bool:
    """Trigger dossier_compiler if the written file is a trigger log with CREATE.

    The dossier_trigger.py writes decisions to logs/triggers.jsonl.
    When that file is updated and the last entry says CREATE, we compile.
    """
    # Only fires when the trigger log itself is written
    if "triggers.jsonl" not in file_path:
        return False

    try:
        if not _TRIGGER_LOG.exists():
            return False

        # Read the last line of the trigger log
        lines = _TRIGGER_LOG.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return False

        last_entry = json.loads(lines[-1])
        decision = last_entry.get("decision", "")
        slug = last_entry.get("tema", "") or last_entry.get("slug", "")
        category = last_entry.get("category", "themes")
        bucket = last_entry.get("bucket", "external")

        if decision != "CREATE" or not slug:
            _log_event("dossier_compiler", file_path, "skip", f"decision={decision}")
            return True

        # ADR-003 (Hybrid Pattern, 2026-05-10) — C-03 SWAP V1->V2 via adapter.
        # V1.0 (engine.intelligence.dossier.dossier_compiler) is non-idempotent
        # (append mode "a"). V2.0 (engine.intelligence.pipeline.dossier_compiler)
        # implements structured field diff. Adapter preserves the caller signature
        # while routing to V2.0. V1.0 module is preserved on disk as @deprecated
        # rollback path (do not delete).
        from engine.intelligence.dossier.dossier_compiler_adapter import compile_dossier

        result_path = compile_dossier(
            slug=slug,
            category=category,
            bucket=bucket,
        )
        _log_event(
            "dossier_compiler",
            file_path,
            "ok",
            f"slug={slug} -> {result_path}",
        )
        return True
    except Exception as exc:
        _log_event("dossier_compiler", file_path, "error", str(exc))
        return True


# ---------------------------------------------------------------------------
# ROUTE 4: AGENT GENERATOR (checks discovery state for READY persons)
# ---------------------------------------------------------------------------


def _route_agent_generator(file_path: str) -> bool:
    """Trigger agent_generator when the discovery state file is written with READY.

    The agent_creation_trigger.py writes DISCOVERY-STATE.json.
    When it contains persons with status=READY, we generate their agents.
    """
    if "DISCOVERY-STATE.json" not in file_path:
        return False

    try:
        if not _DISCOVERY_STATE.exists():
            return False

        state = json.loads(_DISCOVERY_STATE.read_text(encoding="utf-8"))
        persons = state.get("persons", [])
        ready = [p for p in persons if p.get("status") == "READY"]

        if not ready:
            _log_event("agent_generator", file_path, "skip", "no READY persons")
            return True

        from engine.intelligence.agents.agent_generator import generate_agent

        generated_slugs: list[str] = []
        for person in ready:
            slug = person.get("slug", "")
            if not slug:
                continue
            try:
                result = generate_agent(slug=slug, category="external")
                if result.get("created"):
                    generated_slugs.append(slug)
            except Exception as inner_exc:
                _log_event(
                    "agent_generator",
                    file_path,
                    "partial_error",
                    f"slug={slug}: {inner_exc}",
                )

        _log_event(
            "agent_generator",
            file_path,
            "ok",
            f"generated={generated_slugs}",
        )
        return True
    except Exception as exc:
        _log_event("agent_generator", file_path, "error", str(exc))
        return True


# ---------------------------------------------------------------------------
# ROUTE 5: INSIGHT SPEAKER LINKER (meeting transcripts)
# ---------------------------------------------------------------------------


def _route_insight_speaker_linker(file_path: str) -> bool:
    """Trigger insight_speaker_linker for meeting transcripts.

    When a transcript is written to workspace/inbox/meetings/ or
    knowledge/business/inbox/meetings/, we try to find corresponding
    insight JSON and link speakers.
    """
    is_meeting = any(marker in file_path for marker in _MEETING_MARKERS)
    if not is_meeting:
        return False

    # Only process text transcripts
    if not file_path.endswith((".txt", ".md")):
        return False

    try:
        transcript_path = Path(file_path)
        if not transcript_path.is_absolute():
            transcript_path = _ROOT / transcript_path

        if not transcript_path.exists():
            _log_event("insight_speaker_linker", file_path, "skip", "file not found")
            return True

        # Look for corresponding insight JSON.
        # Convention: if transcript is MEET-0001.txt, insight is in
        # knowledge/business/insights/by-meeting/MEET-0001*.json
        stem = transcript_path.stem
        insight_dir = BUSINESS_INSIGHTS / "by-meeting"
        if not insight_dir.exists():
            _log_event("insight_speaker_linker", file_path, "skip", "no insight dir")
            return True

        # Find matching insight files
        candidates = list(insight_dir.glob(f"{stem}*.json"))
        if not candidates:
            # Try with lowercased stem
            candidates = list(insight_dir.glob(f"{stem.lower()}*.json"))

        if not candidates:
            _log_event(
                "insight_speaker_linker",
                file_path,
                "skip",
                f"no insight JSON matching {stem}",
            )
            return True

        from engine.intelligence.pipeline.insight_speaker_linker import (
            link_speakers,
            save_linked_insights,
        )

        linked_total = 0
        for insight_file in candidates:
            result = link_speakers(insight_file, transcript_path)
            if result.get("linked", 0) > 0:
                output_path = insight_dir / f"linked-{insight_file.stem}.json"
                save_linked_insights(result, output_path)
                linked_total += result["linked"]

        _log_event(
            "insight_speaker_linker",
            file_path,
            "ok",
            f"linked={linked_total} files={len(candidates)}",
        )
        return True
    except Exception as exc:
        _log_event("insight_speaker_linker", file_path, "error", str(exc))
        return True


# ---------------------------------------------------------------------------
# ROUTE TABLE
# ---------------------------------------------------------------------------

# Order matters: more specific routes first to avoid false matches.
# advance-trigger MUST run BEFORE inbox_organizer (which is greedy on bucket paths).
_ROUTES: list[tuple[str, callable]] = [
    ("batch_status", _route_advance_trigger),
    ("dossier_compiler", _route_dossier_compiler),
    ("agent_generator", _route_agent_generator),
    ("sop_detector", _route_sop_detector),
    ("insight_speaker_linker", _route_insight_speaker_linker),
    ("inbox_organizer", _route_inbox_organizer),
]


# ---------------------------------------------------------------------------
# HOOK ENTRY POINT
# ---------------------------------------------------------------------------


def main() -> None:
    """PostToolUse hook entry point. Reads JSON from stdin, routes."""
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        # If stdin is empty or not JSON, pass through silently
        print(json.dumps({"continue": True, "error": str(e)}))
        return

    tool_name = data.get("tool_name", "")
    file_path = data.get("tool_input", {}).get("file_path", "")

    # Only act on Write and Edit operations
    if tool_name not in ("Write", "Edit"):
        print(json.dumps({"continue": True}))
        return

    if not file_path:
        print(json.dumps({"continue": True}))
        return

    # Normalize: if absolute, make relative for pattern matching
    normalized = file_path
    root_str = str(_ROOT)
    if normalized.startswith(root_str):
        normalized = normalized[len(root_str) :].lstrip("/")

    # Try each route in order; first match wins
    messages: list[str] = []
    for route_name, route_fn in _ROUTES:
        try:
            handled = route_fn(normalized)
            if handled:
                messages.append(f"[PIPELINE] {route_name} triggered for {Path(normalized).name}")
                break  # First match wins
        except Exception:
            _log_event(route_name, normalized, "crash", traceback.format_exc()[:200])

    # Build response
    response: dict = {"continue": True}
    if messages:
        response["message"] = " | ".join(messages)

    print(json.dumps(response))


if __name__ == "__main__":
    main()
