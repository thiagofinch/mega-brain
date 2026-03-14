"""
Fireflies.ai Transcript Sync Engine -- polls Fireflies GraphQL API,
downloads new transcripts, classifies them, and writes to the appropriate
inbox bucket.

Architecture:
    Fireflies GraphQL API -> [SYNC] -> classify -> inbox/empresa|pessoal/MEETINGS/

CLI:
    python3 -m core.intelligence.pipeline.fireflies_sync run
    python3 -m core.intelligence.pipeline.fireflies_sync status
    python3 -m core.intelligence.pipeline.fireflies_sync backfill
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.intelligence.pipeline.fireflies_config import (
    FirefliesConfig,
    load_config,
)
from core.intelligence.pipeline.meeting_router import MeetingRouter

# ============================================================================
# Constants
# ============================================================================

MAX_RETRIES = 3
BACKOFF_BASE = 2  # 2^attempt seconds
REQUEST_TIMEOUT = 30

# ============================================================================
# GraphQL Queries
# ============================================================================

_QUERY_LIST_TRANSCRIPTS = """\
{
  transcripts {
    id
    title
    date
    duration
    organizer_email
  }
}
"""

_QUERY_FULL_TRANSCRIPT = """\
query($id: String!) {
  transcript(id: $id) {
    id
    title
    date
    duration
    organizer_email
    speakers {
      id
      name
    }
    sentences {
      index
      speaker_name
      text
      start_time
      end_time
    }
    summary {
      keywords
      action_items
      overview
    }
    meeting_attendees {
      displayName
      email
    }
  }
}
"""


# ============================================================================
# Sync Engine
# ============================================================================


class FirefliesSync:
    """Polls Fireflies API, downloads new transcripts, formats,
    classifies, and writes to inbox."""

    def __init__(self, config: FirefliesConfig) -> None:
        self.config = config
        self.router = MeetingRouter(
            company_domains=config.company_domains,
            company_keywords=config.company_keywords,
        )
        self.state = self._load_state()

    # ── Public API ─────────────────────────────────────────────────

    def run(self) -> dict[str, Any]:
        """Main entry point.  Discovers new transcripts, processes them.

        Returns:
            Summary dict with counts and status.
        """
        errors = self.config.validate()
        if errors:
            return {"success": False, "errors": errors}

        self._log("sync_started", {})

        transcripts = self._fetch_transcripts()
        processed_set = set(self.state.get("processed_ids", []))
        new_ones = [t for t in transcripts if t.get("id") not in processed_set]

        self._log(
            "discovery_complete",
            {
                "total": len(transcripts),
                "new": len(new_ones),
            },
        )

        succeeded = 0
        failed = 0

        for t in new_ones:
            tid = t.get("id", "")
            try:
                self._process_transcript(tid)
                succeeded += 1
            except Exception as exc:
                failed += 1
                self._log("error", {"id": tid, "error": str(exc)})

        self._save_state()

        return {
            "success": True,
            "status": "completed",
            "discovered": len(transcripts),
            "new": len(new_ones),
            "succeeded": succeeded,
            "failed": failed,
            "total_processed": self.state.get("meetings_processed", 0),
            "empresa": self.state.get("routed_empresa", 0),
            "pessoal": self.state.get("routed_pessoal", 0),
        }

    def backfill(self) -> dict[str, Any]:
        """Process ALL transcripts, ignoring previously processed IDs."""
        self.state["processed_ids"] = []
        self._save_state()
        return self.run()

    def status(self) -> dict[str, Any]:
        """Return current state summary."""
        return {
            "meetings_processed": self.state.get("meetings_processed", 0),
            "routed_empresa": self.state.get("routed_empresa", 0),
            "routed_pessoal": self.state.get("routed_pessoal", 0),
            "last_sync_at": self.state.get("last_sync_at", "Never"),
            "known_ids": len(self.state.get("processed_ids", [])),
            "next_tag_number": self.state.get("next_tag_number", 1),
        }

    # ── Fetch ──────────────────────────────────────────────────────

    def _fetch_transcripts(self) -> list[dict[str, Any]]:
        """GraphQL query to list all transcripts."""
        data = self._graphql_request(_QUERY_LIST_TRANSCRIPTS)
        return data.get("transcripts") or []

    def _fetch_full_transcript(self, transcript_id: str) -> dict[str, Any]:
        """GraphQL query to get single transcript with all details."""
        data = self._graphql_request(
            _QUERY_FULL_TRANSCRIPT,
            variables={"id": transcript_id},
        )
        return data.get("transcript") or {}

    # ── Process ────────────────────────────────────────────────────

    def _process_transcript(self, transcript_id: str) -> None:
        """Full pipeline for one transcript:
        fetch -> format -> classify -> write -> log."""
        data = self._fetch_full_transcript(transcript_id)
        if not data:
            raise RuntimeError(f"Empty response for transcript {transcript_id}")

        formatted = self._format_transcript(data)

        # Gather attendee emails, filtering out junk
        attendee_emails = _extract_valid_emails(data.get("meeting_attendees"))

        classification = self.router.classify(
            organizer_email=data.get("organizer_email", ""),
            attendee_emails=attendee_emails,
            title=data.get("title", ""),
        )

        tag = self._next_tag()
        filename = self._build_filename(tag, data.get("title", "Untitled"))

        dest_dir = (
            self.config.empresa_dir
            if classification.bucket == "empresa"
            else self.config.pessoal_dir
        )
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename

        # Avoid overwrites
        if dest_path.exists():
            stem = dest_path.stem
            suffix = dest_path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        dest_path.write_text(formatted, encoding="utf-8")

        # Auto-organize within the bucket inbox (entity/type structure)
        # MeetingRouter uses "empresa"/"pessoal" but organize_inbox expects
        # "business"/"personal" — map between the two naming conventions.
        _BUCKET_MAP = {"empresa": "business", "pessoal": "personal"}
        org_bucket = _BUCKET_MAP.get(classification.bucket, "business")
        try:
            from core.intelligence.pipeline.inbox_organizer import organize_inbox

            organize_inbox(org_bucket)
        except Exception as exc:
            self._log(
                "organize_warning",
                {
                    "bucket": org_bucket,
                    "error": str(exc),
                },
            )

        # Update state
        self.state.setdefault("processed_ids", []).append(transcript_id)
        self.state["meetings_processed"] = self.state.get("meetings_processed", 0) + 1
        if classification.bucket == "empresa":
            self.state["routed_empresa"] = self.state.get("routed_empresa", 0) + 1
        else:
            self.state["routed_pessoal"] = self.state.get("routed_pessoal", 0) + 1
        self.state["last_sync_at"] = datetime.now(timezone.utc).isoformat()

        self._log(
            "processed",
            {
                "id": transcript_id,
                "tag": tag,
                "title": data.get("title"),
                "bucket": classification.bucket,
                "score": classification.score,
                "confidence": classification.confidence,
                "destination": str(dest_path),
            },
        )

        # Checkpoint after every transcript
        self._save_state()

    # ── Formatting ─────────────────────────────────────────────────

    def _format_transcript(self, data: dict[str, Any]) -> str:
        """Format transcript into Mega Brain standard .txt format.

        Output matches the existing format from read_ai_harvester.py:
        - Header with ``===``
        - Title, Date, Duration, Participants, Source
        - Summary section
        - Action Items section
        - Keywords section
        - Transcript with ``[HH:MM:SS] Speaker Name:`` format
        """
        # Date -- Fireflies returns epoch MILLISECONDS
        date_str = _epoch_ms_to_str(data.get("date"))

        # Duration -- Fireflies returns minutes as float
        duration_raw = data.get("duration", 0)
        duration_min = (
            round(duration_raw) if isinstance(duration_raw, float) else int(duration_raw or 0)
        )

        # Participants
        attendees = [
            a.get("displayName") or a.get("email", "?")
            for a in (data.get("meeting_attendees") or [])
        ]

        lines: list[str] = [
            "=" * 55,
            "MEETING TRANSCRIPT",
            "=" * 55,
            f"Title: {data.get('title', 'Untitled')}",
            f"Date: {date_str}",
            f"Duration: {duration_min} minutes",
            f"Participants: {', '.join(attendees) or 'Unknown'}",
            f"Source: Fireflies.ai | Transcript ID: {data.get('id', 'N/A')}",
            "=" * 55,
            "",
        ]

        # Summary
        summary: dict[str, Any] = data.get("summary") or {}

        if summary.get("overview"):
            lines.extend(["--- SUMMARY ---", summary["overview"], ""])

        # Action items -- may be string or list
        raw_items = summary.get("action_items")
        if raw_items:
            lines.append("--- ACTION ITEMS ---")
            items: list[str] = (
                raw_items
                if isinstance(raw_items, list)
                else [s for s in raw_items.split("\n") if s.strip()]
            )
            for item in items:
                item = item.strip()
                if item:
                    lines.append(f"  - {item}")
            lines.append("")

        # Keywords -- may be list or string
        raw_kw = summary.get("keywords")
        if raw_kw:
            lines.append("--- KEYWORDS ---")
            kw_list: list[str] = raw_kw if isinstance(raw_kw, list) else [raw_kw]
            lines.extend([", ".join(str(k) for k in kw_list), ""])

        # Transcript sentences
        sentences: list[dict[str, Any]] = data.get("sentences") or []
        if sentences:
            lines.extend(["--- TRANSCRIPT ---", ""])
            last_speaker: str | None = None
            for s in sentences:
                speaker = s.get("speaker_name", "Unknown")
                text = s.get("text", "")
                start = float(s.get("start_time", 0))
                ts = _seconds_to_timestamp(start)

                if speaker != last_speaker:
                    lines.append(f"[{ts}] {speaker}:")
                    last_speaker = speaker
                lines.extend([text, ""])

        return "\n".join(lines)

    # ── Tagging ────────────────────────────────────────────────────

    def _next_tag(self) -> str:
        """Generate next MEET-XXXX tag.

        Scans filesystem to find highest existing tag, then takes the
        max of that and the state counter to avoid collisions.
        """
        existing_nums: list[int] = []
        tag_pattern = re.compile(r"\[MEET-(\d+)\]")

        for d in [self.config.empresa_dir, self.config.pessoal_dir]:
            if d.exists():
                for f in d.iterdir():
                    match = tag_pattern.search(f.name)
                    if match:
                        existing_nums.append(int(match.group(1)))

        state_num = self.state.get("next_tag_number", 1)
        max_existing = (max(existing_nums) + 1) if existing_nums else 1
        next_num = max(state_num, max_existing)

        self.state["next_tag_number"] = next_num + 1
        return f"[MEET-{next_num:04d}]"

    def _build_filename(self, tag: str, title: str) -> str:
        """Build safe filename from tag and title."""
        safe_title = re.sub(r'[<>:"/\\|?*]', "", title).strip()[:120]
        return f"{tag} {safe_title}.txt"

    # ── GraphQL ────────────────────────────────────────────────────

    def _graphql_request(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute GraphQL request against Fireflies API with retry."""
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        body = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            self.config.graphql_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
                "User-Agent": "MegaBrain-FirefliesSync/1.0",
            },
        )

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                    result: dict[str, Any] = json.loads(resp.read().decode("utf-8"))

                if "errors" in result:
                    raise RuntimeError(f"GraphQL errors: {json.dumps(result['errors'])}")
                return result.get("data", {})

            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code == 429 or exc.code >= 500:
                    time.sleep(BACKOFF_BASE ** (attempt + 1))
                    continue
                raise

            except (urllib.error.URLError, OSError) as exc:
                last_error = exc
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_BASE ** (attempt + 1))
                    continue
                raise

        raise RuntimeError(f"GraphQL request failed after {MAX_RETRIES} attempts: {last_error}")

    # ── State ──────────────────────────────────────────────────────

    def _load_state(self) -> dict[str, Any]:
        """Load sync state from JSON file, or return fresh state."""
        if self.config.state_path.exists():
            try:
                return json.loads(self.config.state_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

        return {
            "version": "1.0.0",
            "status": "idle",
            "last_sync_at": None,
            "meetings_processed": 0,
            "routed_empresa": 0,
            "routed_pessoal": 0,
            "next_tag_number": 1,
            "processed_ids": [],
        }

    def _save_state(self) -> None:
        """Persist state to JSON file."""
        self.config.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.state_path.write_text(
            json.dumps(self.state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ── Logging ────────────────────────────────────────────────────

    def _log(self, event: str, data: dict[str, Any]) -> None:
        """Append structured entry to JSONL log."""
        log_file = self.config.log_dir / "fireflies-sync.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "fireflies",
            "event": event,
            **data,
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ============================================================================
# Helpers
# ============================================================================


def _epoch_ms_to_str(date_value: Any) -> str:
    """Convert epoch milliseconds (or other formats) to YYYY-MM-DD HH:MM."""
    if date_value is None:
        return "Unknown"
    if isinstance(date_value, (int, float)) and date_value > 1e12:
        dt = datetime.fromtimestamp(date_value / 1000, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M")
    if isinstance(date_value, (int, float)) and date_value > 0:
        # Possibly epoch seconds
        dt = datetime.fromtimestamp(date_value, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(date_value)


def _seconds_to_timestamp(seconds: float) -> str:
    """Convert seconds float to HH:MM:SS string."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _extract_valid_emails(
    attendees: list[dict[str, Any]] | None,
) -> list[str]:
    """Extract valid email addresses from Fireflies meeting_attendees.

    Filters out:
    - Missing/empty emails
    - Google Calendar group IDs (``@group.calendar.google.com``)
    - Resource calendar addresses
    """
    if not attendees:
        return []

    valid: list[str] = []
    for a in attendees:
        email = (a.get("email") or "").strip()
        if not email or "@" not in email:
            continue
        if "@group.calendar.google.com" in email:
            continue
        if "@resource.calendar.google.com" in email:
            continue
        valid.append(email)
    return valid


# ============================================================================
# CLI
# ============================================================================


def _print_usage() -> None:
    print("""
Fireflies.ai Transcript Sync
==============================

Usage:
    python3 -m core.intelligence.pipeline.fireflies_sync <command>

Commands:
    run        Sync new transcripts from Fireflies
    status     Show current sync state
    backfill   Re-process ALL transcripts (clears processed_ids)
    """)


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        _print_usage()
        sys.exit(1)

    cmd = sys.argv[1].lower()
    config = load_config()
    sync = FirefliesSync(config)

    if cmd == "run":
        result = sync.run()
        if result.get("success"):
            print(f"Sync completed.")
            print(f"  Discovered:  {result['discovered']}")
            print(f"  New:         {result['new']}")
            print(f"  Succeeded:   {result['succeeded']}")
            print(f"  Failed:      {result['failed']}")
            print(f"  Empresa:     {result['empresa']}")
            print(f"  Pessoal:     {result['pessoal']}")
        else:
            print(f"Failed: {result.get('errors')}", file=sys.stderr)
            sys.exit(1)

    elif cmd == "status":
        s = sync.status()
        print("Fireflies Sync Status:")
        print(f"  Processed:   {s['meetings_processed']}")
        print(f"  Empresa:     {s['routed_empresa']}")
        print(f"  Pessoal:     {s['routed_pessoal']}")
        print(f"  Last sync:   {s['last_sync_at']}")
        print(f"  Known IDs:   {s['known_ids']}")
        print(f"  Next tag:    MEET-{s['next_tag_number']:04d}")

    elif cmd == "backfill":
        print("Backfilling all transcripts...")
        result = sync.backfill()
        if result.get("success"):
            print(f"Backfill completed: {result['succeeded']} processed.")
        else:
            print(f"Failed: {result.get('errors')}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        _print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
