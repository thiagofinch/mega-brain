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
    from core.paths import (
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
        from core.intelligence.pipeline.inbox_organizer import organize_inbox

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
        from core.intelligence.pipeline.sop_detector import (
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

        from core.intelligence.dossier.dossier_compiler import compile_dossier

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

        from core.intelligence.agents.agent_generator import generate_agent

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

        from core.intelligence.pipeline.insight_speaker_linker import (
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
_ROUTES: list[tuple[str, callable]] = [
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
