"""
Read.ai Transcript Harvester — bulk downloads meeting transcripts from Read.ai API.

YOLO mode: autonomous, continuous, checkpointed, resumable.

CLI:
    python3 -m core.intelligence.pipeline.read_ai_harvester run
    python3 -m core.intelligence.pipeline.read_ai_harvester resume
    python3 -m core.intelligence.pipeline.read_ai_harvester stop
    python3 -m core.intelligence.pipeline.read_ai_harvester status

Architecture:
    Read.ai API → [HARVESTER] → staging/ → [ROUTER] → inbox/empresa|pessoal/MEETINGS/
                                                         ↓ (every N pessoal)
                                                    [GARDENER] reorganizes
"""

import base64
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.intelligence.pipeline.read_ai_config import ReadAIConfig, load_config
from core.intelligence.pipeline.read_ai_gardener import PessoalGardener
from core.intelligence.pipeline.read_ai_router import MeetingRouter

# ============================================================================
# Constants
# ============================================================================

MAX_RETRIES = 3
BACKOFF_BASE = 2  # 2^attempt seconds
REQUEST_TIMEOUT = 30  # seconds per HTTP request


# ============================================================================
# State
# ============================================================================

@dataclass
class HarvestState:
    """Persistent state for resume support."""

    version: str = "1.0.0"
    status: str = "idle"  # idle, running, completed, stopped, failed
    started_at: str | None = None
    stopped_at: str | None = None
    last_updated: str | None = None

    # Progress
    meetings_discovered: int = 0
    meetings_downloaded: int = 0
    meetings_skipped: int = 0
    meetings_failed: int = 0

    # Routing
    routed_empresa: int = 0
    routed_pessoal: int = 0
    pessoal_since_garden: int = 0

    # Tag counter
    next_tag_number: int = 1

    # Already-processed meeting IDs (for resume)
    processed_ids: list[str] = field(default_factory=list)

    # Pagination
    last_page_token: str | None = None
    all_pages_fetched: bool = False

    # Gardener
    gardener_runs: int = 0


def _load_state(path: Path) -> HarvestState:
    """Load state from JSON file."""
    if not path.exists():
        return HarvestState()
    try:
        with open(path) as f:
            data = json.load(f)
        # Handle list fields that may be missing
        s = HarvestState()
        for k, v in data.items():
            if hasattr(s, k):
                setattr(s, k, v)
        return s
    except (json.JSONDecodeError, OSError):
        return HarvestState()


def _save_state(state: HarvestState, path: Path) -> None:
    """Persist state to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    state.last_updated = datetime.utcnow().isoformat() + "Z"
    with open(path, "w") as f:
        json.dump(asdict(state), f, indent=2)


# ============================================================================
# API Client
# ============================================================================

class ReadAIClient:
    """HTTP client for Read.ai MCP API using OAuth 2.1 Bearer tokens.

    Uses the MCP JSON-RPC endpoint (SSE transport) which supports the
    `expand` parameter for fetching transcript, summary, action_items, etc.
    The REST v1 API only returns metadata without content.
    """

    MCP_URL = "https://api.read.ai/mcp"

    def __init__(self, config: ReadAIConfig):
        self.config = config
        self._token: str | None = None

    def list_meetings(
        self, page_token: str | None = None
    ) -> dict[str, Any]:
        """List meetings with pagination via MCP."""
        args: dict[str, Any] = {"limit": min(self.config.page_size, 10)}
        if page_token:
            args["cursor"] = page_token
        result = self._mcp_call("list_meetings", args)
        # Normalize: MCP returns {data: [...], has_more, ...}
        # Harvester expects {meetings: [...], next_page_token: ...}
        data = result.get("data", [])
        has_more = result.get("has_more", False)
        next_token = data[-1]["id"] if data and has_more else None
        return {"meetings": data, "next_page_token": next_token}

    def get_meeting(self, meeting_id: str) -> dict[str, Any]:
        """Get full meeting details with transcript, summary, and action items."""
        return self._mcp_call("get_meeting_by_id", {
            "id": meeting_id,
            "expand": [
                "summary", "action_items", "transcript",
                "topics", "chapter_summaries", "key_questions",
            ],
        })

    def _mcp_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a Read.ai MCP tool via JSON-RPC over SSE."""
        token = self._get_token()

        body = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }).encode()

        for attempt in range(MAX_RETRIES):
            try:
                req = urllib.request.Request(
                    self.MCP_URL, data=body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                    raw = resp.read().decode("utf-8")

                # Parse SSE response
                for line in raw.split("\n"):
                    if line.startswith("data:"):
                        data = json.loads(line[5:].strip())
                        if "error" in data:
                            raise RuntimeError(f"MCP error: {data['error']}")
                        if "result" in data:
                            content = data["result"].get("content", [])
                            for c in content:
                                text = c.get("text", "")
                                if text.startswith("{"):
                                    return json.loads(text)
                            return data["result"]

                raise RuntimeError(f"No data in MCP response for {tool_name}")

            except urllib.error.HTTPError as e:
                if e.code == 401 and attempt == 0:
                    self._token = None
                    self._refresh_token()
                    token = self._get_token()
                    continue
                if e.code == 429:
                    time.sleep(BACKOFF_BASE ** (attempt + 1))
                    continue
                if e.code >= 500 and attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_BASE ** (attempt + 1))
                    continue
                raise

            except (urllib.error.URLError, OSError):
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_BASE ** (attempt + 1))
                    continue
                raise

        raise RuntimeError(f"MCP call failed after {MAX_RETRIES} attempts: {tool_name}")

    def _get_token(self) -> str:
        """Get access token, raising if not available."""
        if not self._token:
            self._token = self._load_access_token()
        if not self._token:
            raise RuntimeError(
                "No Read.ai access token found. Run:\n"
                "  python3 -m core.intelligence.pipeline.read_ai_oauth authorize\n"
                "to set up OAuth access."
            )
        return self._token

    def _load_access_token(self) -> str | None:
        """Load access token from saved OAuth tokens."""
        from core.intelligence.pipeline.read_ai_oauth import get_access_token
        return get_access_token()

    def _refresh_token(self) -> None:
        """Attempt to refresh expired token."""
        from core.intelligence.pipeline.read_ai_oauth import cmd_refresh
        try:
            cmd_refresh()
            self._token = self._load_access_token()
        except SystemExit:
            pass


# ============================================================================
# Transcript Formatter
# ============================================================================

def format_transcript(meeting: dict[str, Any]) -> str:
    """
    Convert Read.ai meeting JSON to timestamped .txt format.

    Handles both MCP format (transcript.turns with start_time_ms) and
    legacy format (speaker_blocks, transcript_blocks).
    """
    title = meeting.get("title", "Untitled Meeting")
    meeting_id = meeting.get("id", meeting.get("meeting_id", "unknown"))

    # Date from start_time_ms (milliseconds since epoch)
    start_ms = meeting.get("start_time_ms")
    end_ms = meeting.get("end_time_ms")
    if start_ms:
        date = datetime.fromtimestamp(start_ms / 1000).strftime("%Y-%m-%d %H:%M")
    else:
        date = meeting.get("date", meeting.get("start_time", "Unknown"))

    # Duration
    if start_ms and end_ms:
        duration = round((end_ms - start_ms) / 60000)
    else:
        duration = meeting.get("duration", meeting.get("duration_minutes", "?"))

    # Platform
    platform = meeting.get("platform", "")

    # Participants
    participants_raw = meeting.get("participants", [])
    if isinstance(participants_raw, list):
        if participants_raw and isinstance(participants_raw[0], dict):
            names = [p.get("name", p.get("email", "?")) for p in participants_raw
                     if p.get("attended", True)]
        else:
            names = participants_raw
    else:
        names = [str(participants_raw)]

    participants_str = ", ".join(names) if names else "Unknown"

    lines = [
        "=" * 55,
        "MEETING TRANSCRIPT",
        "=" * 55,
        f"Title: {title}",
        f"Date: {date}",
        f"Duration: {duration} minutes",
    ]
    if platform:
        lines.append(f"Platform: {platform}")
    lines.extend([
        f"Participants: {participants_str}",
        f"Source: Read.ai | Meeting ID: {meeting_id}",
        "=" * 55,
        "",
    ])

    # Summary
    summary = meeting.get("summary")
    if summary:
        lines.append("--- SUMMARY ---")
        lines.append(summary)
        lines.append("")

    # Action items
    action_items = meeting.get("action_items")
    if action_items:
        lines.append("--- ACTION ITEMS ---")
        for item in action_items:
            lines.append(f"  - {item}")
        lines.append("")

    # Topics
    topics = meeting.get("topics")
    if topics:
        lines.append("--- TOPICS ---")
        for topic in topics:
            lines.append(f"  - {topic}")
        lines.append("")

    # Transcript — MCP format (transcript.turns) or legacy formats
    transcript = meeting.get("transcript")
    if isinstance(transcript, dict):
        # MCP format: {speakers: [...], turns: [...], text: "..."}
        turns = transcript.get("turns", [])
        if turns:
            lines.append("--- TRANSCRIPT ---")
            lines.append("")
            for turn in turns:
                speaker_name = turn.get("speaker", {}).get("name", "Unknown")
                text = turn.get("text", "")
                ts_ms = turn.get("start_time_ms")
                if ts_ms is not None:
                    # Convert ms offset to HH:MM:SS
                    seconds = ts_ms / 1000
                    h = int(seconds // 3600)
                    m = int((seconds % 3600) // 60)
                    s = int(seconds % 60)
                    lines.append(f"[{h:02d}:{m:02d}:{s:02d}] {speaker_name}:")
                else:
                    lines.append(f"{speaker_name}:")
                lines.append(text)
                lines.append("")
        elif transcript.get("text"):
            lines.append("--- TRANSCRIPT ---")
            lines.append("")
            lines.append(transcript["text"])
    elif isinstance(transcript, list):
        # Legacy format: list of blocks
        lines.append("--- TRANSCRIPT ---")
        lines.append("")
        for block in transcript:
            if isinstance(block, dict):
                ts = block.get("timestamp", block.get("start_time", ""))
                speaker = block.get("speaker", block.get("speaker_name", "Unknown"))
                text = block.get("text", block.get("content", ""))
                ts_str = _format_timestamp(ts) if ts else ""
                if ts_str:
                    lines.append(f"[{ts_str}] {speaker}:")
                else:
                    lines.append(f"{speaker}:")
                lines.append(text)
                lines.append("")
            elif isinstance(block, str):
                lines.append(block)
    elif isinstance(transcript, str):
        lines.append("--- TRANSCRIPT ---")
        lines.append("")
        lines.append(transcript)
    else:
        lines.append("(No transcript content available)")

    return "\n".join(lines)


def _format_timestamp(ts: Any) -> str:
    """Convert seconds/ms to HH:MM:SS format."""
    try:
        seconds = float(ts)
        # Detect if milliseconds
        if seconds > 86400:
            seconds = seconds / 1000
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    except (ValueError, TypeError):
        return str(ts)


# ============================================================================
# Main Harvester
# ============================================================================

class ReadAIHarvester:
    """Main harvester engine — YOLO mode."""

    def __init__(self, config: ReadAIConfig | None = None):
        self.config = config or load_config()
        self.client = ReadAIClient(self.config)
        self.router = MeetingRouter(self.config)
        self.gardener = PessoalGardener(self.config)
        self.state = _load_state(self.config.state_path)
        self._log_path = self.config.log_dir / "harvest.jsonl"

    def run(self) -> dict[str, Any]:
        """
        Main YOLO loop: paginate → download → route → checkpoint.

        Runs until all meetings processed or stop signal received.
        """
        errors = self.config.validate()
        if errors:
            return {"success": False, "errors": errors}

        self._clear_stop_signal()
        self.state.status = "running"
        self.state.started_at = datetime.utcnow().isoformat() + "Z"
        _save_state(self.state, self.config.state_path)

        self._log({"event": "harvest_started"})

        downloads_since_ingest = 0

        try:
            # Phase 1: Discover all meetings
            if not self.state.all_pages_fetched:
                self._discover_meetings()

            # Phase 2: Download and route each meeting
            all_meetings = self._get_pending_meetings()
            total = len(all_meetings)
            self._log({"event": "processing_start", "total_pending": total})

            for i, meeting_summary in enumerate(all_meetings):
                if self._should_stop():
                    self.state.status = "stopped"
                    self._log({"event": "stop_signal_received", "processed": i})
                    break

                mid = meeting_summary.get("id", meeting_summary.get("meeting_id", ""))
                if mid in self.state.processed_ids:
                    continue

                # Download full meeting
                try:
                    meeting = self.client.get_meeting(mid)
                except Exception as e:
                    self.state.meetings_failed += 1
                    self._log({"event": "download_failed", "id": mid, "error": str(e)})
                    _save_state(self.state, self.config.state_path)
                    continue

                # Format transcript
                transcript = format_transcript(meeting)

                # Save to staging
                self.config.staging_dir.mkdir(parents=True, exist_ok=True)
                staging_file = self.config.staging_dir / f"{mid}.txt"
                staging_file.write_text(transcript, encoding="utf-8")

                # Classify and route
                router_data = self._extract_router_data(meeting)
                decision = self.router.classify(router_data)

                # Generate tag
                tag = self._next_tag()

                # Move from staging to inbox
                dest = self.router.move_file(staging_file, decision, tag)

                # Update state
                self.state.processed_ids.append(mid)
                self.state.meetings_downloaded += 1
                if decision.bucket == "empresa":
                    self.state.routed_empresa += 1
                else:
                    self.state.routed_pessoal += 1
                    self.state.pessoal_since_garden += 1

                downloads_since_ingest += 1

                self._log({
                    "event": "meeting_processed",
                    "id": mid,
                    "title": decision.title,
                    "bucket": decision.bucket,
                    "score": decision.score,
                    "tag": tag,
                    "destination": str(dest),
                    "progress": f"{i + 1}/{total}",
                })

                # Checkpoint after every download
                _save_state(self.state, self.config.state_path)

                # Gardener trigger
                if (
                    self.state.pessoal_since_garden
                    >= self.config.gardener_trigger
                ):
                    self._log({"event": "gardener_triggered"})
                    result = self.gardener.run()
                    self.state.gardener_runs += 1
                    self.state.pessoal_since_garden = 0
                    self._log({
                        "event": "gardener_completed",
                        "moved": result.files_moved,
                        "themes": result.moves,
                    })
                    _save_state(self.state, self.config.state_path)

                # Ingestion trigger (logged but not auto-executed — Pipeline Jarvis
                # is a separate process that the user/skill triggers)
                if downloads_since_ingest >= self.config.ingestion_batch:
                    self._log({
                        "event": "ingestion_batch_ready",
                        "count": downloads_since_ingest,
                        "message": (
                            "Batch ready for Pipeline Jarvis ingestion. "
                            "Run /process-inbox or /jarvis-full to process."
                        ),
                    })
                    downloads_since_ingest = 0

            # Done
            if self.state.status != "stopped":
                self.state.status = "completed"

        except Exception as e:
            self.state.status = "failed"
            self._log({"event": "harvest_error", "error": str(e)})
            raise

        finally:
            self.state.stopped_at = datetime.utcnow().isoformat() + "Z"
            _save_state(self.state, self.config.state_path)

        return {
            "success": True,
            "status": self.state.status,
            "downloaded": self.state.meetings_downloaded,
            "empresa": self.state.routed_empresa,
            "pessoal": self.state.routed_pessoal,
            "failed": self.state.meetings_failed,
            "gardener_runs": self.state.gardener_runs,
        }

    def resume(self) -> dict[str, Any]:
        """Resume from last saved state."""
        if not self.config.state_path.exists():
            return {"success": False, "error": "No state file found. Run 'run' first."}

        self.state = _load_state(self.config.state_path)
        self._log({"event": "harvest_resumed", "processed_so_far": len(self.state.processed_ids)})
        return self.run()

    def stop(self) -> None:
        """Create stop signal file."""
        self.config.stop_signal.parent.mkdir(parents=True, exist_ok=True)
        self.config.stop_signal.touch()

    def status(self) -> dict[str, Any]:
        """Return current state summary."""
        state = _load_state(self.config.state_path)
        return {
            "status": state.status,
            "started_at": state.started_at,
            "stopped_at": state.stopped_at,
            "last_updated": state.last_updated,
            "meetings_discovered": state.meetings_discovered,
            "meetings_downloaded": state.meetings_downloaded,
            "meetings_failed": state.meetings_failed,
            "routed_empresa": state.routed_empresa,
            "routed_pessoal": state.routed_pessoal,
            "gardener_runs": state.gardener_runs,
            "next_tag": state.next_tag_number,
            "all_pages_fetched": state.all_pages_fetched,
        }

    # ── Internal ────────────────────────────────────────────────────────

    def _discover_meetings(self) -> None:
        """Paginate through list_meetings to discover all meeting IDs."""
        page_token = self.state.last_page_token
        discovered = self.state.meetings_discovered

        while True:
            if self._should_stop():
                break

            response = self.client.list_meetings(page_token=page_token)
            meetings = response.get("meetings", [])
            next_token = response.get("next_page_token")

            discovered += len(meetings)

            # Save meeting summaries to staging for later processing
            summaries_path = self.config.staging_dir / "meeting_summaries.jsonl"
            summaries_path.parent.mkdir(parents=True, exist_ok=True)
            with open(summaries_path, "a") as f:
                for m in meetings:
                    f.write(json.dumps(m) + "\n")

            self.state.meetings_discovered = discovered
            self.state.last_page_token = next_token

            self._log({
                "event": "page_fetched",
                "meetings_on_page": len(meetings),
                "total_discovered": discovered,
                "has_next": bool(next_token),
            })

            if not next_token:
                self.state.all_pages_fetched = True
                break

            page_token = next_token
            _save_state(self.state, self.config.state_path)

        _save_state(self.state, self.config.state_path)
        self._log({"event": "discovery_complete", "total": discovered})

    def _get_pending_meetings(self) -> list[dict[str, Any]]:
        """Load meeting summaries from staging, filter out already processed."""
        summaries_path = self.config.staging_dir / "meeting_summaries.jsonl"
        if not summaries_path.exists():
            return []

        meetings = []
        processed = set(self.state.processed_ids)
        with open(summaries_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                m = json.loads(line)
                mid = m.get("id", m.get("meeting_id", ""))
                if mid and mid not in processed:
                    meetings.append(m)
        return meetings

    def _extract_router_data(self, meeting: dict[str, Any]) -> dict[str, Any]:
        """Extract data needed by MeetingRouter from full meeting response."""
        participants = meeting.get("participants", [])
        emails = []
        for p in participants:
            if isinstance(p, dict):
                email = p.get("email", "")
                if email:
                    emails.append(email)
            elif isinstance(p, str) and "@" in p:
                emails.append(p)

        organizer = meeting.get("organizer_email", "")
        if not organizer and meeting.get("organizer"):
            org = meeting["organizer"]
            if isinstance(org, dict):
                organizer = org.get("email", "")
            elif isinstance(org, str):
                organizer = org

        return {
            "id": meeting.get("id", meeting.get("meeting_id", "")),
            "title": meeting.get("title", ""),
            "organizer_email": organizer,
            "participants": emails,
            "description": meeting.get("description", ""),
        }

    def fetch_single(self, meeting_id: str) -> dict[str, Any]:
        """
        Fetch a single meeting by ID, format, classify, and route it.

        Used by /ingest when a Read.ai URL is provided.
        Reuses existing client, formatter, router, and state.
        """
        errors = self.config.validate()
        if errors:
            return {"success": False, "meeting_id": meeting_id, "error": "; ".join(errors)}

        # Check if already processed
        if meeting_id in self.state.processed_ids:
            self._log({"event": "single_fetch_skipped", "id": meeting_id, "reason": "already processed"})
            # Find existing file
            existing = self._find_existing_meeting(meeting_id)
            if existing:
                return {
                    "success": True,
                    "meeting_id": meeting_id,
                    "tag": "",
                    "destination": str(existing),
                    "bucket": "existing",
                    "title": existing.stem,
                    "error": None,
                    "already_existed": True,
                }

        try:
            # 1. Download full meeting
            meeting = self.client.get_meeting(meeting_id)

            # 2. Format transcript
            transcript = format_transcript(meeting)

            # 3. Stage
            self.config.staging_dir.mkdir(parents=True, exist_ok=True)
            staging_file = self.config.staging_dir / f"{meeting_id}.txt"
            staging_file.write_text(transcript, encoding="utf-8")

            # 4. Classify
            router_data = self._extract_router_data(meeting)
            decision = self.router.classify(router_data)

            # 5. Tag (filesystem-aware)
            tag = self._next_tag_from_filesystem()

            # 6. Route to inbox
            dest = self.router.move_file(staging_file, decision, tag)

            # 7. Update state
            self.state.processed_ids.append(meeting_id)
            self.state.meetings_downloaded += 1
            if decision.bucket == "empresa":
                self.state.routed_empresa += 1
            else:
                self.state.routed_pessoal += 1
            _save_state(self.state, self.config.state_path)

            # 8. Log
            self._log({
                "event": "single_fetch",
                "id": meeting_id,
                "title": decision.title,
                "bucket": decision.bucket,
                "score": decision.score,
                "tag": tag,
                "destination": str(dest),
            })

            return {
                "success": True,
                "meeting_id": meeting_id,
                "tag": tag,
                "destination": str(dest),
                "bucket": decision.bucket,
                "title": decision.title,
                "error": None,
            }

        except Exception as e:
            self._log({"event": "single_fetch_failed", "id": meeting_id, "error": str(e)})
            return {"success": False, "meeting_id": meeting_id, "error": str(e)}

    def _next_tag_from_filesystem(self) -> str:
        """
        Scan all meeting directories for highest MEET-NNNN tag, return next.

        Used by fetch_single() which may run independently of bulk state.
        Scans both configured dirs and the actual meetings directory.
        """
        tag_pattern = re.compile(r"\[MEET-(\d+)\]")
        max_num = 0

        # Scan all directories where meetings might live
        scan_dirs = [
            self.config.empresa_dir,
            self.config.pessoal_dir,
        ]

        for directory in scan_dirs:
            if not directory.exists():
                continue
            for f in directory.rglob("*.txt"):
                match = tag_pattern.search(f.name)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num

        # Also check state counter (bulk harvester may be ahead)
        if self.state.next_tag_number > max_num + 1:
            max_num = self.state.next_tag_number - 1

        next_num = max_num + 1
        self.state.next_tag_number = next_num + 1
        return f"[{self.config.tag_prefix}-{next_num:04d}]"

    def _find_existing_meeting(self, meeting_id: str) -> Path | None:
        """Find an already-downloaded meeting file by scanning for Meeting ID in content."""
        for directory in [self.config.empresa_dir, self.config.pessoal_dir]:
            if not directory.exists():
                continue
            for f in directory.rglob("*.txt"):
                try:
                    # Read only the header (first 512 bytes) for speed
                    with open(f, encoding="utf-8") as fh:
                        header = fh.read(512)
                    if meeting_id in header:
                        return f
                except OSError:
                    continue
        return None

    def _next_tag(self) -> str:
        """Generate next sequential tag like [MEET-0042]."""
        num = self.state.next_tag_number
        self.state.next_tag_number = num + 1
        return f"[{self.config.tag_prefix}-{num:04d}]"

    def _should_stop(self) -> bool:
        """Check if stop signal file exists."""
        return self.config.stop_signal.exists()

    def _clear_stop_signal(self) -> None:
        """Remove stop signal if exists."""
        if self.config.stop_signal.exists():
            self.config.stop_signal.unlink()

    def _log(self, entry: dict[str, Any]) -> None:
        """Append to JSONL log."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
        with open(self._log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")


# ============================================================================
# CLI
# ============================================================================

def parse_meeting_url(url: str) -> str | None:
    """
    Extract meeting ID from a Read.ai URL.

    Supports:
        https://app.read.ai/analytics/meetings/01EXAMPLE000MEETING0ID000000
        https://app.read.ai/analytics/meetings/01EXAMPLE000MEETING0ID000000?tab=...

    Returns meeting_id or None if URL doesn't match.
    """
    pattern = re.compile(r"app\.read\.ai/analytics/meetings/([A-Za-z0-9]+)")
    match = pattern.search(url)
    return match.group(1) if match else None


def _print_usage():
    print("""
Read.ai Transcript Harvester
=============================

Usage:
    python3 -m core.intelligence.pipeline.read_ai_harvester <command>

Commands:
    run       Start harvesting (YOLO mode — runs until done or stopped)
    resume    Resume from last checkpoint
    stop      Send stop signal (graceful shutdown)
    status    Show current harvest status
    fetch     Fetch a single meeting by ID or URL
    """)


def main():
    if len(sys.argv) < 2:
        _print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "run":
        harvester = ReadAIHarvester()
        print("Starting Read.ai Harvest (YOLO mode)...")
        result = harvester.run()
        if result.get("success"):
            print(f"\nCompleted: {result['status']}")
            print(f"  Downloaded: {result['downloaded']}")
            print(f"  Empresa:    {result['empresa']}")
            print(f"  Pessoal:    {result['pessoal']}")
            print(f"  Failed:     {result['failed']}")
            print(f"  Gardener:   {result['gardener_runs']} runs")
        else:
            print(f"Failed: {result.get('errors', result.get('error'))}")
            sys.exit(1)

    elif command == "resume":
        harvester = ReadAIHarvester()
        print("Resuming harvest...")
        result = harvester.resume()
        if result.get("success"):
            print(f"Completed: {result['status']}")
            print(f"  Downloaded: {result['downloaded']}")
        else:
            print(f"Failed: {result.get('error')}")
            sys.exit(1)

    elif command == "stop":
        harvester = ReadAIHarvester()
        harvester.stop()
        print("Stop signal sent. Harvest will stop after current download.")

    elif command == "status":
        harvester = ReadAIHarvester()
        s = harvester.status()
        print("Read.ai Harvest Status:")
        for k, v in s.items():
            print(f"  {k}: {v}")

    elif command == "fetch":
        if len(sys.argv) < 3:
            print("Usage: ... fetch <meeting_id_or_url>")
            sys.exit(1)
        raw = sys.argv[2]
        # Accept both raw ID and full URL
        meeting_id = parse_meeting_url(raw) if "read.ai" in raw else raw
        if not meeting_id:
            print(f"Could not parse meeting ID from: {raw}")
            sys.exit(1)

        harvester = ReadAIHarvester()
        print(f"Fetching meeting {meeting_id}...")
        result = harvester.fetch_single(meeting_id)
        if result.get("success"):
            if result.get("already_existed"):
                print(f"  Already exists: {result['destination']}")
            else:
                print(f"  Tag:    {result['tag']}")
                print(f"  Title:  {result['title']}")
                print(f"  Bucket: {result['bucket']}")
                print(f"  Saved:  {result['destination']}")
        else:
            print(f"Failed: {result.get('error')}")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        _print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
