"""
Fireflies.ai Transcript Sync Engine -- polls Fireflies GraphQL API,
downloads new transcripts, classifies them, and writes to the appropriate
inbox bucket.

Architecture:
    Fireflies GraphQL API -> [DEDUP] -> [SYNC] -> classify -> inbox/empresa|pessoal/MEETINGS/

Dedup layer (Story CALL-2):
    Pre-classifier dedup by composite key: normalised_title + hour_bucket.
    State persisted in .data/fireflies-dedup-seen.json (gitignored).
    Root cause: Google Meet recordings appear in all participants' Drives with
    different fileIds. poll-recordings.mjs uploads one per Drive account.
    Dedup here catches duplicates regardless of source (multi-Drive, webhook, manual).

CLI:
    python3 -m core.intelligence.pipeline.fireflies_sync run
    python3 -m core.intelligence.pipeline.fireflies_sync status
    python3 -m core.intelligence.pipeline.fireflies_sync backfill
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.intelligence.pipeline.fireflies_config import (
    FirefliesConfig,
    load_config,
)
from engine.intelligence.pipeline.meeting_router import MeetingRouter

# ============================================================================
# Constants
# ============================================================================

MAX_RETRIES = 3
BACKOFF_BASE = 2  # 2^attempt seconds
REQUEST_TIMEOUT = 30
MIN_TRANSCRIPT_WORDS = 50  # skip transcripts with fewer words (header-only / corrupted)

# Dedup: TTL for entries in the seen-state (30 days in seconds)
DEDUP_TTL_SECONDS = 30 * 24 * 3600

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
    meeting_link
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
# Dedup Engine (Story CALL-2)
# ============================================================================

# Regex patterns to strip from titles before hashing for dedup.
# Google Meet appends date + timezone + " - Recording" to all titles.
# Format examples:
#   "DAILY MARKETING + SCORECARD - 2026 05 27 08 55 GMT-03:00 - Recording"
#   "DAILY MARKETING + SCORECARD - 2026 05 27 08 55 GMT-03 00 - Recording"
#
# The pattern matches the separator + date + time + timezone + " - Recording"
# all the way to end of string, in one pass.  The timezone separator can be
# either a colon (GMT-03:00) or a space (GMT-03 00).
_TITLE_STRIP_RE = re.compile(
    r"""\s+-\s+            # separator before date
        \d{4}\s+\d{2}\s+\d{2}   # date "2026 05 27"
        \s+\d{2}\s+\d{2}        # time "08 55"
        \s+GMT[+-]\d{2}[\s:]\d{2}  # timezone "GMT-03:00" or "GMT-03 00"
        \s+-\s+Recording         # trailing "- Recording"
        \s*$                     # optional trailing whitespace
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _normalise_title(title: str) -> str:
    """Strip date/timezone/recording suffix from a Google Meet title.

    "DAILY MARKETING + SCORECARD - 2026 05 27 08 55 GMT-03:00 - Recording"
    -> "DAILY MARKETING + SCORECARD"
    """
    cleaned = _TITLE_STRIP_RE.sub("", title or "").strip().upper()
    # Collapse multiple whitespace
    return re.sub(r"\s+", " ", cleaned)


def _dedup_key(title: str, date_epoch_ms: int | float | None) -> str:
    """Build composite dedup key: normalised_title + hour_bucket.

    Hour bucket = floor(epoch_ms / 3_600_000).
    Tolerates transcripts created within the same hour for the same meeting
    even if their timestamp jitters by a few minutes.
    """
    norm = _normalise_title(title)
    if date_epoch_ms and date_epoch_ms > 0:
        hour_bucket = int(float(date_epoch_ms) // 3_600_000)
    else:
        hour_bucket = 0
    return f"{norm}|{hour_bucket}"


class FirefliesDedup:
    """Persistent dedup state for Fireflies transcripts.

    State format in .data/fireflies-dedup-seen.json:
    {
      "<dedup_key>": {
        "first_seen_id": "MEET-XXXX",
        "first_seen_at": "<ISO>",
        "duplicates_skipped": N
      }
    }

    Root cause documented in docs/adr/ADR-CALL-DEDUP-ROOT-CAUSE.md.
    """

    def __init__(self, state_path: Path) -> None:
        self.state_path = state_path
        self._seen: dict[str, dict[str, Any]] = {}
        self._load()

    # ── Public API ─────────────────────────────────────────────────

    def is_duplicate(self, transcript_id: str, title: str, date_epoch_ms: Any) -> bool:
        """Return True if a transcript with the same dedup key was already seen."""
        key = _dedup_key(title, date_epoch_ms)
        if key not in self._seen:
            return False
        # Not a duplicate of itself (idempotent registration)
        entry = self._seen[key]
        return entry.get("first_seen_id") != transcript_id

    def get_first_seen_id(self, title: str, date_epoch_ms: Any) -> str:
        """Return the first_seen_id for a given dedup key, or empty string."""
        key = _dedup_key(title, date_epoch_ms)
        return self._seen.get(key, {}).get("first_seen_id", "")

    def register(self, transcript_id: str, title: str, date_epoch_ms: Any) -> None:
        """Register a transcript as the canonical version for its dedup key."""
        key = _dedup_key(title, date_epoch_ms)
        if key not in self._seen:
            self._seen[key] = {
                "first_seen_id": transcript_id,
                "first_seen_at": datetime.now(UTC).isoformat(),
                "duplicates_skipped": 0,
            }
        self._save()

    def mark_duplicate_skipped(self, title: str, date_epoch_ms: Any) -> None:
        """Increment duplicate counter for a key."""
        key = _dedup_key(title, date_epoch_ms)
        if key in self._seen:
            self._seen[key]["duplicates_skipped"] = (
                self._seen[key].get("duplicates_skipped", 0) + 1
            )
        self._save()

    def purge_expired(self) -> int:
        """Remove entries older than DEDUP_TTL_SECONDS. Returns purge count."""
        now_iso = datetime.now(UTC).isoformat()
        now_ts = datetime.fromisoformat(now_iso).timestamp()
        expired = [
            k
            for k, v in self._seen.items()
            if _age_seconds(v.get("first_seen_at", ""), now_ts) > DEDUP_TTL_SECONDS
        ]
        for k in expired:
            del self._seen[k]
        if expired:
            self._save()
        return len(expired)

    # ── Persistence ────────────────────────────────────────────────

    def _load(self) -> None:
        if self.state_path.exists():
            try:
                raw = json.loads(self.state_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._seen = raw
            except (json.JSONDecodeError, OSError):
                self._seen = {}
        else:
            self._seen = {}

    def _save(self) -> None:
        """Atomic write: write to temp file then rename."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self._seen, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(str(tmp), str(self.state_path))


def _age_seconds(iso_str: str, now_ts: float) -> float:
    """Return age in seconds of an ISO timestamp string relative to now_ts."""
    if not iso_str:
        return 0.0
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return now_ts - dt.timestamp()
    except ValueError:
        return 0.0


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
        # Dedup engine — persists cross-restart in .data/fireflies-dedup-seen.json
        from engine.paths import DATA  # lazy import to avoid circular at module level

        self.dedup = FirefliesDedup(DATA / "fireflies-dedup-seen.json")
        self.dedup.purge_expired()  # housekeeping on startup

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
        self._count_dedup_skipped_this_run = 0

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
            "skipped": self.state.get("skipped", 0),
            "duplicates_skipped": self._count_dedup_skipped_this_run,
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
            "skipped": self.state.get("skipped", 0),
            "last_sync_at": self.state.get("last_sync_at", "Never"),
            "known_ids": len(self.state.get("processed_ids", [])),
            "next_tag_number": self.state.get("next_tag_number", 1),
            "dedup_seen_keys": len(self.dedup._seen),
        }

    # ── Fetch ──────────────────────────────────────────────────────

    def _fetch_transcripts(self) -> list[dict[str, Any]]:
        """GraphQL query to list all transcripts.

        Populates _transcript_meta_cache for pre-fetch dedup checks.
        """
        data = self._graphql_request(_QUERY_LIST_TRANSCRIPTS)
        transcripts = data.get("transcripts") or []
        # Cache list-level metadata (title + date) keyed by transcript id
        # so _process_transcript can check dedup without a full fetch
        self._transcript_meta_cache: dict[str, dict[str, Any]] = {
            t["id"]: t for t in transcripts if t.get("id")
        }
        return transcripts

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
        dedup -> fetch -> validate sentences -> format -> classify -> write -> log.

        Dedup check (Story CALL-2): before fetching full content, check the
        composite key (normalised_title + hour_bucket) against the seen-state.
        If a duplicate is detected, log [dedup] SKIPPED and mark as processed
        without writing any file to inbox.
        """
        # ── Pre-fetch dedup check using list-level metadata ─────────
        # We need title + date for the key. These were already fetched in the
        # list query. Pull from the cached transcripts list if available,
        # otherwise fetch full data (cost is one extra API call only on first run).
        list_meta = getattr(self, "_transcript_meta_cache", {}).get(transcript_id)

        if list_meta:
            title_preview = list_meta.get("title", "")
            date_preview = list_meta.get("date")

            if self.dedup.is_duplicate(transcript_id, title_preview, date_preview):
                first_id = self.dedup.get_first_seen_id(title_preview, date_preview)
                self._log(
                    "dedup_skipped",
                    {
                        "id": transcript_id,
                        "title": title_preview,
                        "meeting_link": list_meta.get("meeting_link"),
                        "first_seen_id": first_id,
                        "message": (
                            f"[dedup] SKIPPED meeting_title={title_preview!r} "
                            f"first_seen={first_id} duplicate={transcript_id}"
                        ),
                    },
                )
                # Mark as processed so it is not re-attempted next cycle
                self.state.setdefault("processed_ids", []).append(transcript_id)
                self.state["skipped"] = self.state.get("skipped", 0) + 1
                self._count_dedup_skipped_this_run = (
                    getattr(self, "_count_dedup_skipped_this_run", 0) + 1
                )
                self.dedup.mark_duplicate_skipped(title_preview, date_preview)
                return

        # ── Fetch full transcript data ───────────────────────────────
        data = self._fetch_full_transcript(transcript_id)
        if not data:
            raise RuntimeError(f"Empty response for transcript {transcript_id}")

        # ── Post-fetch dedup check (catches cases where list metadata was absent) ─
        title_full = data.get("title", "")
        date_full = data.get("date")
        if self.dedup.is_duplicate(transcript_id, title_full, date_full):
            first_id = self.dedup.get_first_seen_id(title_full, date_full)
            self._log(
                "dedup_skipped",
                {
                    "id": transcript_id,
                    "title": title_full,
                    "first_seen_id": first_id,
                    "message": (
                        f"[dedup] SKIPPED meeting_title={title_full!r} "
                        f"first_seen={first_id} duplicate={transcript_id}"
                    ),
                },
            )
            self.state.setdefault("processed_ids", []).append(transcript_id)
            self.state["skipped"] = self.state.get("skipped", 0) + 1
            self._count_dedup_skipped_this_run = (
                getattr(self, "_count_dedup_skipped_this_run", 0) + 1
            )
            self.dedup.mark_duplicate_skipped(title_full, date_full)
            return

        # Validate sentences exist before creating a file
        sentences = data.get("sentences")
        if not sentences:
            self._log(
                "skipped_empty",
                {
                    "id": transcript_id,
                    "title": data.get("title"),
                    "reason": "sentences null or empty",
                },
            )
            self.state.setdefault("processed_ids", []).append(transcript_id)
            self.state["skipped"] = self.state.get("skipped", 0) + 1
            return

        formatted = self._format_transcript(data)

        # Validate transcript has meaningful content (not just header)
        word_count = len(formatted.split())
        if word_count < MIN_TRANSCRIPT_WORDS:
            self._log(
                "skipped_empty",
                {
                    "id": transcript_id,
                    "title": data.get("title"),
                    "reason": f"word count {word_count} below threshold {MIN_TRANSCRIPT_WORDS}",
                },
            )
            self.state.setdefault("processed_ids", []).append(transcript_id)
            self.state["skipped"] = self.state.get("skipped", 0) + 1
            return

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

        # Register in dedup state — future duplicates of this meeting are SKIPPED
        self.dedup.register(transcript_id, data.get("title", ""), data.get("date"))

        # Auto-organize within the bucket inbox (entity/type structure)
        # MeetingRouter uses "empresa"/"pessoal" but organize_inbox expects
        # "business"/"personal" — map between the two naming conventions.
        _BUCKET_MAP = {"empresa": "business", "pessoal": "personal"}
        org_bucket = _BUCKET_MAP.get(classification.bucket, "business")
        try:
            from engine.intelligence.pipeline.inbox_organizer import organize_inbox

            organize_inbox(org_bucket)
        except Exception as exc:
            self._log(
                "organize_warning",
                {
                    "bucket": org_bucket,
                    "error": str(exc),
                },
            )

        # STORY-MCE-INGEST-ROBUSTNESS AC-5 (2026-05-27): persist bucket
        # decision in MetadataManager so downstream Phase 5
        # _detect_bucket_for_slug reads it via the FIRST heuristic
        # (no need to fall back to filesystem checks).
        try:
            from engine.intelligence.pipeline.mce.metadata_manager import MetadataManager

            # Derive slug from filename (Fireflies tag prefix removed)
            import re as _re_slug
            sanitized = _re_slug.sub(r"^\[\w+-\d+\]\s*", "", filename).strip()
            slug_candidate = _re_slug.sub(r"[^\w]+", "-", sanitized).lower().strip("-")[:80]
            if slug_candidate:
                mgr = MetadataManager.load(slug_candidate)
                if mgr is None:
                    mgr = MetadataManager(slug=slug_candidate, mode="greenfield")
                mgr.set_classification({
                    "primary_bucket": org_bucket,
                    "cascade_buckets": [org_bucket],
                    "confidence": classification.confidence,
                    "source_type": "fireflies-transcript",
                    "reasons": list(classification.reasons),
                })
                mgr.set_source_path(str(dest_path))
                mgr.save()
        except Exception as exc:
            self._log(
                "metadata_persist_warning",
                {
                    "slug_candidate": slug_candidate if 'slug_candidate' in locals() else None,
                    "bucket": org_bucket,
                    "error": str(exc),
                },
            )

        # STORY-MCE-INGEST-ROBUSTNESS AC-8: journey log of bucket decision
        try:
            from engine.intelligence.pipeline.journey_logger import emit_bucket_decision
            emit_bucket_decision(
                entity_id=slug_candidate if 'slug_candidate' in locals() and slug_candidate else "unknown",
                entity_type="meeting",
                from_state=None,
                to_state=org_bucket,
                triggered_by="FirefliesSync.MeetingRouter",
                evidence={
                    "transcript_id": transcript_id,
                    "title": data.get("title", ""),
                    "organizer": data.get("organizer_email", ""),
                    "attendee_count": len(attendee_emails),
                    "classifier_confidence": classification.confidence,
                    "classifier_score": classification.score,
                },
            )
        except Exception:
            pass  # fail-open

        # Update state
        self.state.setdefault("processed_ids", []).append(transcript_id)
        self.state["meetings_processed"] = self.state.get("meetings_processed", 0) + 1
        if classification.bucket == "empresa":
            self.state["routed_empresa"] = self.state.get("routed_empresa", 0) + 1
        else:
            self.state["routed_pessoal"] = self.state.get("routed_pessoal", 0) + 1
        self.state["last_sync_at"] = datetime.now(UTC).isoformat()

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
            "timestamp": datetime.now(UTC).isoformat(),
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
    if isinstance(date_value, int | float) and date_value > 1e12:
        dt = datetime.fromtimestamp(date_value / 1000, tz=UTC)
        return dt.strftime("%Y-%m-%d %H:%M")
    if isinstance(date_value, int | float) and date_value > 0:
        # Possibly epoch seconds
        dt = datetime.fromtimestamp(date_value, tz=UTC)
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
            print("Sync completed.")
            print(f"  Discovered:  {result['discovered']}")
            print(f"  New:         {result['new']}")
            print(f"  Succeeded:   {result['succeeded']}")
            print(f"  Failed:      {result['failed']}")
            print(f"  Skipped:     {result['skipped']}")
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
        print(f"  Skipped:     {s['skipped']}")
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
