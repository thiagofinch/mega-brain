"""Ingestion Guard — Phase 0 deduplication for the MCE pipeline.

Runs BEFORE classification/routing to prevent duplicate processing.
Uses a persistent registry that tracks:
- Identity: source_id (Fireflies/Read.ai ID) or composite(title+date)
- Integrity: word count + SHA-256 body hash (content minus header)

Verdicts (action, kind):
    NEW         ("process",     "proceed")    — never seen → process fully
    INCREMENTAL ("incremental", "proceed")    — same source, larger body → process delta
    DUPLICATE   ("skip",        "duplicate")  — exact hash match → HALT_OK (success=True)
    TOO_SMALL   ("skip",        "too_small")  — body < MIN_BODY_WORDS → HALT_OK
    CORRUPTED   ("skip",        "corrupted")  — same source, smaller/truncated → HALT_FAIL
    UNREADABLE  ("skip",        "unreadable") — OS error reading file → HALT_FAIL

Downstream callers inspect verdict.kind (not just verdict.action) to
decide whether the skip is benign (success=True) or a failure.

Registry (priority order):
  1. PostgreSQL content_hashes table (via BrainEngine) — primary after migration
  2. .data/ingestion-registry.json — fallback during transition period

Usage from orchestrate.py::

    from engine.intelligence.pipeline.ingestion_guard import guard_ingest

    verdict = guard_ingest(file_path)
    if verdict.action == "skip":
        # Must inspect verdict.kind to differentiate benign vs failure skips:
        #   "duplicate"  -> HALT_OK   (success=True, pipeline stops)
        #   "corrupted"  -> HALT_FAIL (success=False, pipeline stops)
        #   "too_small"  -> HALT_OK   (success=True, pipeline stops)
        #   "unreadable" -> HALT_FAIL (success=False, pipeline stops)
        if verdict.kind in {"corrupted", "unreadable"}:
            return _build_result("ingest", success=False, skipped=True, ...)
        return _build_result("ingest", success=True, skipped=True, ...)
    # ... continue with classify/route/etc (NEW or INCREMENTAL)

CLI::

    python -m engine.intelligence.pipeline.ingestion_guard check "path/to/file.txt"
    python -m engine.intelligence.pipeline.ingestion_guard stats
    python -m engine.intelligence.pipeline.ingestion_guard reset

Version: 1.1.0 (W2-001.7: DB-first with JSON fallback)
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_REGISTRY_PATH = _PROJECT_ROOT / ".data" / "ingestion-registry.json"

# Minimum words to consider a file worth processing
MIN_BODY_WORDS = 50

# Header marker — both fireflies_sync and read_ai_harvester use this
_HEADER_END_PATTERN = re.compile(r"^={10,}$", re.MULTILINE)

# Source ID patterns in header line — accept both legacy (plain) and current (markdown)
_FIREFLIES_ID = re.compile(r"(?:Transcript ID:|\*\*ID Fireflies:\*\*)\s*(\S+)")
_READAI_ID = re.compile(r"(?:Meeting ID:|\*\*ID Read\.ai:\*\*)\s*(\S+)")

# Title extraction — accepts "Title: X" or first markdown "# X" heading
_TITLE_PATTERN = re.compile(r"^(?:Title:\s*(.+)|#\s+(.+))$", re.MULTILINE)
_DATE_PATTERN = re.compile(r"^(?:Date:\s*(.+)|\*\*Data:\*\*\s*(.+))$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class IngestVerdict:
    """Result of the ingestion guard check.

    The ``kind`` attribute differentiates the sub-types of a skip verdict so
    downstream orchestrators can decide whether to treat the skip as benign
    (``"duplicate"``, ``"too_small"``) or as a failure (``"corrupted"``,
    ``"unreadable"``). For ``action in {"process","incremental"}`` the kind
    is ``"proceed"``.
    """

    action: str  # "process" | "skip" | "incremental"
    reason: str
    identity_key: str
    body_hash: str
    word_count: int
    previous_word_count: int = 0
    delta_start_word: int = 0  # for incremental: word index to start from

    @property
    def kind(self) -> str:
        """Fine-grained classification of this verdict.

        Values:
            "duplicate"  -- benign skip, exact hash match
            "corrupted"  -- failure skip, same source but smaller/truncated
            "too_small"  -- benign skip, body under MIN_BODY_WORDS
            "unreadable" -- failure skip, OS error reading the file
            "proceed"    -- action is "process" or "incremental"
        """
        if self.action != "skip":
            return "proceed"
        reason = (self.reason or "").lower()
        if "exact duplicate" in reason or "hash match" in reason:
            return "duplicate"
        if "smaller" in reason or "truncation" in reason:
            return "corrupted"
        if "too small" in reason or "below" in reason:
            return "too_small"
        if "cannot read" in reason:
            return "unreadable"
        # Default conservative: treat unknown skip as corrupted (fail-closed).
        return "corrupted"


@dataclass
class RegistryEntry:
    """A single entry in the ingestion registry."""

    identity_key: str
    body_hash: str
    word_count: int
    file_path: str
    source_id: str | None = None
    title: str | None = None
    date: str | None = None
    ingested_at: str = ""
    batch_id: str | None = None
    slug: str | None = None
    chunks_generated: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_key": self.identity_key,
            "body_hash": self.body_hash,
            "word_count": self.word_count,
            "file_path": self.file_path,
            "source_id": self.source_id,
            "title": self.title,
            "date": self.date,
            "ingested_at": self.ingested_at,
            "batch_id": self.batch_id,
            "slug": self.slug,
            "chunks_generated": self.chunks_generated,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RegistryEntry:
        return cls(
            identity_key=d.get("identity_key", ""),
            body_hash=d.get("body_hash", ""),
            word_count=d.get("word_count", 0),
            file_path=d.get("file_path", ""),
            source_id=d.get("source_id"),
            title=d.get("title"),
            date=d.get("date"),
            ingested_at=d.get("ingested_at", ""),
            batch_id=d.get("batch_id"),
            slug=d.get("slug"),
            chunks_generated=d.get("chunks_generated", 0),
        )


# ---------------------------------------------------------------------------
# Header parsing
# ---------------------------------------------------------------------------


def _parse_header(text: str) -> dict[str, str | None]:
    """Extract metadata from the standard Mega Brain transcript header.

    Returns dict with keys: source_id, title, date.
    """
    result: dict[str, str | None] = {"source_id": None, "title": None, "date": None}

    m = _FIREFLIES_ID.search(text)
    if m:
        result["source_id"] = f"fireflies:{m.group(1)}"
    else:
        m = _READAI_ID.search(text)
        if m:
            result["source_id"] = f"readai:{m.group(1)}"

    m = _TITLE_PATTERN.search(text)
    if m:
        result["title"] = (m.group(1) or m.group(2) or "").strip()

    m = _DATE_PATTERN.search(text)
    if m:
        result["date"] = (m.group(1) or m.group(2) or "").strip()

    return result


def _extract_body(text: str) -> str:
    """Extract body content (everything after the last header separator).

    The standard format has 3 lines of '=' separators. Body starts after
    the 3rd separator.
    """
    separators = list(_HEADER_END_PATTERN.finditer(text))
    if len(separators) >= 3:
        return text[separators[2].end() :].strip()
    if len(separators) >= 2:
        return text[separators[1].end() :].strip()
    # No clear header — treat entire text as body
    return text.strip()


def _compute_identity_key(header: dict[str, str | None]) -> str:
    """Compute a stable identity key for a piece of content.

    Priority:
    1. source_id (Fireflies/Read.ai transcript ID) — most reliable
    2. composite(normalized_title + date) — fallback for manual uploads
    """
    if header.get("source_id"):
        return header["source_id"]

    title = (header.get("title") or "unknown").lower().strip()
    date = (header.get("date") or "unknown").strip()
    composite = f"{title}|{date}"
    return f"composite:{hashlib.sha256(composite.encode()).hexdigest()[:16]}"


def _hash_body(body: str) -> str:
    """Canonical SHA-256 of body content. Delegates to engine.intelligence.pipeline.hashing
    (single source of truth — see STORY-OS-001 AC10).

    Normalizations applied: UTF-8 NFC, line endings LF, strip BOM. This ensures
    hash equality between Phase 0 ingestion-registry and obsidian-sync vault
    frontmatter (mb_content_hash). Hash drift between systems was finding F3
    of the 2026-05-06 roundtable.
    """
    from engine.intelligence.pipeline.hashing import canonical_hash

    return canonical_hash(body)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class IngestionRegistry:
    """Persistent registry tracking all ingested content."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _REGISTRY_PATH
        self._entries: dict[str, dict[str, Any]] = {}
        # STORY-A3: reverse index body_hash -> identity_key (first-wins) so the
        # SAME body arriving via a DIFFERENT path/identity is detected as a
        # cross-path duplicate. Built on load, maintained on register.
        self._body_hash_index: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._entries = data.get("entries", {})
            except (json.JSONDecodeError, OSError):
                self._entries = {}
        self._rebuild_body_hash_index()

    def _rebuild_body_hash_index(self) -> None:
        """STORY-A3: (re)build the body_hash -> identity_key reverse map.

        First-wins (RN-1 determinism): when two entries share a body_hash, the
        one whose entry is encountered first in the persisted dict wins. Since
        the persisted dict preserves insertion order and the guard only ever
        registers the FIRST occurrence as new (the 2nd becomes a cross-path
        SKIP), the winning identity_key is stable across reloads.
        """
        index: dict[str, str] = {}
        for ident, raw in self._entries.items():
            bh = raw.get("body_hash")
            if bh and bh not in index:
                index[bh] = ident
        self._body_hash_index = index

    def lookup_by_body_hash(self, body_hash: str) -> RegistryEntry | None:
        """STORY-A3: return the FIRST-registered entry carrying *body_hash*.

        Used for cross-path dedup: a hit under a DIFFERENT identity_key means the
        identical body was already ingested by another path.
        """
        if not body_hash:
            return None
        ident = self._body_hash_index.get(body_hash)
        if ident is None:
            return None
        return self.lookup(ident)

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0.0",
            "updated_at": datetime.now(UTC).isoformat(),
            "total_entries": len(self._entries),
            "entries": self._entries,
        }
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def lookup(self, identity_key: str) -> RegistryEntry | None:
        raw = self._entries.get(identity_key)
        if raw:
            return RegistryEntry.from_dict(raw)
        return None

    def register(self, entry: RegistryEntry) -> None:
        entry.ingested_at = datetime.now(UTC).isoformat()
        self._entries[entry.identity_key] = entry.to_dict()
        # STORY-A3: keep the reverse index first-wins — only set the body_hash
        # owner if not already claimed by an earlier identity_key.
        if entry.body_hash and entry.body_hash not in self._body_hash_index:
            self._body_hash_index[entry.body_hash] = entry.identity_key
        self._save()

    def update_after_processing(
        self,
        identity_key: str,
        *,
        batch_id: str | None = None,
        chunks_generated: int = 0,
        slug: str | None = None,
    ) -> None:
        """Update entry metadata after pipeline processing completes."""
        if identity_key in self._entries:
            if batch_id:
                self._entries[identity_key]["batch_id"] = batch_id
            if chunks_generated:
                self._entries[identity_key]["chunks_generated"] = chunks_generated
            if slug:
                self._entries[identity_key]["slug"] = slug
            self._save()

    # -- STORY-GBA-W2.8: replay-safe propagation flag (D3) --------------------
    # The guard registers a content hash BEFORE cmd_finalize propagates it. A
    # crash in that window leaves the entry registered-but-not-propagated; the
    # next run's DUPLICATE verdict would skip it forever. ``fully_propagated``
    # is the signal the reaper consults to treat such entries as re-processable.
    # NOTE: ``register`` (the guard's path) NEVER sets this — it is set true
    # ONLY by ``mark_fully_propagated`` after finalize completes.

    def mark_fully_propagated(self, identity_key: str) -> None:
        """Mark an entry's metadata ``fully_propagated=True`` (post-finalize).

        Idempotent: a no-op if the key is absent. Called from the orchestrator
        AFTER cmd_finalize completes propagation — never from ``guard_ingest``.
        """
        if identity_key in self._entries:
            self._entries[identity_key]["fully_propagated"] = True
            self._save()

    def is_fully_propagated(self, identity_key: str) -> bool:
        """Read the replay-safety signal (default False/absent = not propagated).

        Returns False when the key is unknown OR the flag is absent/false — both
        mean "not (proven) fully propagated", so the reaper re-processes.
        """
        raw = self._entries.get(identity_key)
        if not raw:
            return False
        return bool(raw.get("fully_propagated", False))

    def stats(self) -> dict[str, Any]:
        return {
            "total_entries": len(self._entries),
            "registry_path": str(self._path),
            "registry_exists": self._path.exists(),
        }

    def reset(self) -> None:
        self._entries = {}
        self._body_hash_index = {}
        self._save()


# ---------------------------------------------------------------------------
# DB-backed Registry (W2-001.7: content_hashes table)
# ---------------------------------------------------------------------------


class DbIngestionRegistry:
    """DB-first ingestion registry with JSON fallback.

    Attempts to use the PostgreSQL content_hashes table via a raw psycopg2
    connection. Falls back to IngestionRegistry (JSON) if the database is
    not available or the table doesn't exist.

    This ensures zero disruption during the transition period (AC4).
    """

    def __init__(self, json_fallback: IngestionRegistry | None = None) -> None:
        self._json = json_fallback or IngestionRegistry()
        self._conn = None
        self._db_available = False
        self._try_connect()

    def _try_connect(self) -> None:
        """Attempt to connect to PostgreSQL and verify content_hashes table."""
        # MCE-2.1 AC7: explicit env opt-out so AC7 runs can force the JSON
        # fallback when the remote Postgres is unreachable or slow (observed
        # multi-minute SSL socket hangs blocking the whole pipeline).
        import os as _os

        if _os.environ.get("MCE_DISABLE_DB", "").lower() in {"1", "true", "yes"}:
            logger.debug("DbIngestionRegistry: MCE_DISABLE_DB set, skipping DB")
            return
        try:
            from engine.config import get_config

            dsn = get_config("BRAIN_ENGINE_DSN")
            if not dsn:
                host = get_config("BRAIN_ENGINE_HOST", default="localhost")
                port = get_config("BRAIN_ENGINE_PORT", default="5432")
                dbname = get_config("BRAIN_ENGINE_DBNAME", default="megabrain")
                user = get_config("BRAIN_ENGINE_USER", default="postgres")
                password = get_config("BRAIN_ENGINE_PASSWORD", default="")
                dsn = f"host={host} port={port} dbname={dbname} user={user} password={password}"

            import psycopg2

            self._conn = psycopg2.connect(dsn, connect_timeout=5)
            self._conn.autocommit = True

            # Verify table exists
            with self._conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'content_hashes'
                    )
                """)
                if cur.fetchone()[0]:
                    self._db_available = True
                    logger.debug("DbIngestionRegistry: content_hashes table available")
                else:
                    logger.debug(
                        "DbIngestionRegistry: content_hashes table not found, using JSON fallback"
                    )
                    self._conn.close()
                    self._conn = None

        except Exception as exc:
            logger.debug("DbIngestionRegistry: DB not available (%s), using JSON fallback", exc)
            if self._conn:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None

    def lookup(self, identity_key: str) -> RegistryEntry | None:
        """Look up by identity_key. DB first, then JSON fallback."""
        if self._db_available and self._conn:
            try:
                with self._conn.cursor() as cur:
                    # Look up by source_id (which maps to identity_key)
                    cur.execute(
                        "SELECT hash, source_id, bucket, processed_at, metadata "
                        "FROM content_hashes WHERE source_id = %s LIMIT 1",
                        (identity_key,),
                    )
                    row = cur.fetchone()
                    if row:
                        hash_val, source_id, bucket, processed_at, metadata = row
                        meta = metadata if isinstance(metadata, dict) else {}
                        return RegistryEntry(
                            identity_key=source_id or identity_key,
                            body_hash=hash_val,
                            word_count=meta.get("word_count", 0),
                            file_path=meta.get("file_path", ""),
                            source_id=source_id,
                            title=meta.get("title"),
                            date=meta.get("date"),
                            ingested_at=processed_at.isoformat() if processed_at else "",
                            batch_id=meta.get("batch_id"),
                            slug=meta.get("slug"),
                            chunks_generated=meta.get("chunks_generated", 0),
                        )
            except Exception as exc:
                logger.warning("DbIngestionRegistry.lookup DB error: %s, falling back to JSON", exc)

        # Fallback to JSON
        return self._json.lookup(identity_key)

    def lookup_by_body_hash(self, body_hash: str) -> RegistryEntry | None:
        """STORY-A3: cross-path dedup lookup by body_hash. DB first, JSON fallback.

        Reuses the existing ``content_hashes.hash`` column (no DDL — IDS reuse):
        ``hash`` already stores the canonical body hash and carries a unique
        constraint (``ON CONFLICT (hash)``). A hit returns the owning entry; the
        caller compares its identity_key with the incoming one to confirm the
        body arrived via a different path.
        """
        if not body_hash:
            return None
        if self._db_available and self._conn:
            try:
                with self._conn.cursor() as cur:
                    cur.execute(
                        "SELECT hash, source_id, bucket, processed_at, metadata "
                        "FROM content_hashes WHERE hash = %s LIMIT 1",
                        (body_hash,),
                    )
                    row = cur.fetchone()
                    if row:
                        hash_val, source_id, _bucket, processed_at, metadata = row
                        meta = metadata if isinstance(metadata, dict) else {}
                        return RegistryEntry(
                            identity_key=source_id or "",
                            body_hash=hash_val,
                            word_count=meta.get("word_count", 0),
                            file_path=meta.get("file_path", ""),
                            source_id=source_id,
                            title=meta.get("title"),
                            date=meta.get("date"),
                            ingested_at=processed_at.isoformat() if processed_at else "",
                            batch_id=meta.get("batch_id"),
                            slug=meta.get("slug"),
                            chunks_generated=meta.get("chunks_generated", 0),
                        )
            except Exception as exc:
                logger.warning(
                    "DbIngestionRegistry.lookup_by_body_hash DB error: %s, falling back to JSON",
                    exc,
                )
        return self._json.lookup_by_body_hash(body_hash)

    def register(self, entry: RegistryEntry) -> None:
        """Register in both DB and JSON (dual-write during transition)."""
        # Always write to JSON (preserves the fallback)
        self._json.register(entry)

        # Also write to DB if available
        if self._db_available and self._conn:
            try:
                metadata = {
                    "word_count": entry.word_count,
                    "title": entry.title,
                    "date": entry.date,
                    "file_path": entry.file_path,
                    "slug": entry.slug,
                    "batch_id": entry.batch_id,
                    "chunks_generated": entry.chunks_generated,
                    "origin": "ingestion-guard",
                }
                with self._conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO content_hashes (hash, source_id, bucket, processed_at, metadata)
                        VALUES (%s, %s, %s, %s, %s::jsonb)
                        ON CONFLICT (hash) DO UPDATE SET
                            source_id = EXCLUDED.source_id,
                            processed_at = EXCLUDED.processed_at,
                            metadata = EXCLUDED.metadata
                        """,
                        (
                            entry.body_hash,
                            entry.identity_key,
                            _infer_bucket_from_path(entry.file_path),
                            datetime.now(UTC).isoformat(),
                            json.dumps(metadata, default=str),
                        ),
                    )
            except Exception as exc:
                logger.warning("DbIngestionRegistry.register DB error: %s", exc)

    def update_after_processing(
        self,
        identity_key: str,
        *,
        batch_id: str | None = None,
        chunks_generated: int = 0,
        slug: str | None = None,
    ) -> None:
        """Update metadata after processing in both stores."""
        self._json.update_after_processing(
            identity_key, batch_id=batch_id, chunks_generated=chunks_generated, slug=slug
        )

        if self._db_available and self._conn:
            try:
                updates = []
                params: list[Any] = []
                if batch_id:
                    updates.append("metadata = jsonb_set(metadata, '{batch_id}', %s::jsonb)")
                    params.append(json.dumps(batch_id))
                if chunks_generated:
                    updates.append(
                        "metadata = jsonb_set(metadata, '{chunks_generated}', %s::jsonb)"
                    )
                    params.append(json.dumps(chunks_generated))
                if slug:
                    updates.append("metadata = jsonb_set(metadata, '{slug}', %s::jsonb)")
                    params.append(json.dumps(slug))

                if updates:
                    params.append(identity_key)
                    with self._conn.cursor() as cur:
                        cur.execute(
                            f"UPDATE content_hashes SET {', '.join(updates)} WHERE source_id = %s",
                            params,
                        )
            except Exception as exc:
                logger.warning("DbIngestionRegistry.update_after_processing DB error: %s", exc)

    # -- STORY-GBA-W2.8: replay-safe propagation flag (D3) --------------------
    def mark_fully_propagated(self, identity_key: str) -> None:
        """Set ``metadata.fully_propagated = true`` in both stores (post-finalize).

        Mirrors ``update_after_processing``'s ``jsonb_set`` pattern so the flag
        lands inside the EXISTING ``content_hashes.metadata`` jsonb — no DDL
        change, no new column, the 6 verdict keys untouched (D3). Never called
        by ``guard_ingest``; only by the orchestrator after cmd_finalize.
        """
        # JSON store first (preserves the fallback signal).
        self._json.mark_fully_propagated(identity_key)

        if self._db_available and self._conn:
            try:
                with self._conn.cursor() as cur:
                    cur.execute(
                        "UPDATE content_hashes "
                        "SET metadata = jsonb_set(metadata, '{fully_propagated}', %s::jsonb) "
                        "WHERE source_id = %s",
                        (json.dumps(True), identity_key),
                    )
            except Exception as exc:
                logger.warning("DbIngestionRegistry.mark_fully_propagated DB error: %s", exc)

    def is_fully_propagated(self, identity_key: str) -> bool:
        """Read ``metadata.fully_propagated`` (DB first, JSON fallback).

        Default False when unknown / flag absent / false — i.e. the reaper
        treats it as NOT proven-propagated and re-processes. Fail-open to JSON
        on any DB error so a flaky DB never wrongly reports "propagated".
        """
        if self._db_available and self._conn:
            try:
                with self._conn.cursor() as cur:
                    cur.execute(
                        "SELECT metadata FROM content_hashes WHERE source_id = %s LIMIT 1",
                        (identity_key,),
                    )
                    row = cur.fetchone()
                    if row is not None:
                        meta = row[0] if isinstance(row[0], dict) else {}
                        return bool(meta.get("fully_propagated", False))
                    # No DB row → fall through to JSON (dual-write may lag).
            except Exception as exc:
                logger.warning(
                    "DbIngestionRegistry.is_fully_propagated DB error: %s, falling back to JSON",
                    exc,
                )
        return self._json.is_fully_propagated(identity_key)

    def stats(self) -> dict[str, Any]:
        """Combined stats from both stores."""
        result = self._json.stats()
        result["db_available"] = self._db_available
        if self._db_available and self._conn:
            try:
                with self._conn.cursor() as cur:
                    cur.execute("SELECT count(*) FROM content_hashes")
                    result["db_entries"] = cur.fetchone()[0]
            except Exception:
                result["db_entries"] = -1
        return result

    def reset(self) -> None:
        self._json.reset()

    def close(self) -> None:
        """Close the DB connection if open."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
            self._db_available = False


def _infer_bucket_from_path(file_path: str) -> str:
    """Infer knowledge bucket from file path."""
    path_lower = (file_path or "").lower()
    if "knowledge/external" in path_lower or "rag_expert" in path_lower:
        return "external"
    if "knowledge/business" in path_lower or "rag_business" in path_lower:
        return "business"
    if "knowledge/personal" in path_lower:
        return "personal"
    return ""


# ---------------------------------------------------------------------------
# Guard function (main entry point)
# ---------------------------------------------------------------------------


def guard_ingest(
    file_path: str | Path,
    registry: IngestionRegistry | DbIngestionRegistry | None = None,
) -> IngestVerdict:
    """Check a file against the ingestion registry before processing.

    Args:
        file_path: Path to the raw source file.
        registry: Optional registry instance. Defaults to DbIngestionRegistry
                  (DB-first with JSON fallback, W2-001.7).

    Returns:
        IngestVerdict with action and reason.
    """
    reg = registry or DbIngestionRegistry()
    resolved = Path(file_path).resolve()

    # Read file
    try:
        text = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return IngestVerdict(
            action="skip",
            reason=f"cannot read file: {exc}",
            identity_key="",
            body_hash="",
            word_count=0,
        )

    # Parse header and body
    header = _parse_header(text)
    body = _extract_body(text)
    body_hash = _hash_body(body)
    word_count = len(body.split())
    identity_key = _compute_identity_key(header)

    # Check minimum content threshold
    if word_count < MIN_BODY_WORDS:
        return IngestVerdict(
            action="skip",
            reason=f"body too small ({word_count} words < {MIN_BODY_WORDS} threshold)",
            identity_key=identity_key,
            body_hash=body_hash,
            word_count=word_count,
        )

    # Lookup in registry
    existing = reg.lookup(identity_key)

    # STORY-A3: cross-path duplicate detection.
    # When this identity_key is NEW but the SAME body_hash was already registered
    # under a DIFFERENT identity_key (i.e. the same content arrived via another
    # path — the `_unclassified` vs `_unclassified/misc` mirror), skip it as a
    # benign duplicate. First-wins (RN-1): the already-registered occurrence wins;
    # this 2nd path is SKIP and is NOT re-registered. Placed ONLY in the NEW
    # branch so the 6 same-identity verdicts (DUPLICATE/INCREMENTAL/CORRUPTED/
    # TOO_SMALL/UNREADABLE/proceed) are byte-for-byte unchanged (AC-3).
    if existing is None:
        _lookup_bh = getattr(reg, "lookup_by_body_hash", None)
        cross = _lookup_bh(body_hash) if callable(_lookup_bh) else None
        if cross is not None and cross.identity_key != identity_key:
            return IngestVerdict(
                action="skip",
                reason=(
                    f"exact duplicate (cross-path, hash match; "
                    f"first-seen identity={cross.identity_key})"
                ),
                identity_key=identity_key,
                body_hash=body_hash,
                word_count=word_count,
                previous_word_count=cross.word_count,
            )

    if existing is None:
        # NEW — never seen before
        reg.register(
            RegistryEntry(
                identity_key=identity_key,
                body_hash=body_hash,
                word_count=word_count,
                file_path=str(resolved),
                source_id=header.get("source_id"),
                title=header.get("title"),
                date=header.get("date"),
            )
        )
        return IngestVerdict(
            action="process",
            reason="new content",
            identity_key=identity_key,
            body_hash=body_hash,
            word_count=word_count,
        )

    if existing.body_hash == body_hash:
        # DUPLICATE — exact same content
        return IngestVerdict(
            action="skip",
            reason=f"exact duplicate (identity={identity_key}, hash match)",
            identity_key=identity_key,
            body_hash=body_hash,
            word_count=word_count,
            previous_word_count=existing.word_count,
        )

    if word_count > existing.word_count:
        # INCREMENTAL — same source, bigger body
        delta_start = existing.word_count
        # Update registry with new larger version
        reg.register(
            RegistryEntry(
                identity_key=identity_key,
                body_hash=body_hash,
                word_count=word_count,
                file_path=str(resolved),
                source_id=header.get("source_id") or existing.source_id,
                title=header.get("title") or existing.title,
                date=header.get("date") or existing.date,
                batch_id=existing.batch_id,
                slug=existing.slug,
                chunks_generated=existing.chunks_generated,
            )
        )
        return IngestVerdict(
            action="incremental",
            reason=(
                f"same source, larger body ({existing.word_count} → {word_count} words, "
                f"+{word_count - existing.word_count} new)"
            ),
            identity_key=identity_key,
            body_hash=body_hash,
            word_count=word_count,
            previous_word_count=existing.word_count,
            delta_start_word=delta_start,
        )

    # Same source, different hash, but SMALLER or same size — content changed
    if word_count < existing.word_count:
        return IngestVerdict(
            action="skip",
            reason=(
                f"same source but smaller ({word_count} < {existing.word_count} words). "
                "Possible truncation — keeping larger version."
            ),
            identity_key=identity_key,
            body_hash=body_hash,
            word_count=word_count,
            previous_word_count=existing.word_count,
        )

    # Same word count but different hash — content was edited/corrected
    reg.register(
        RegistryEntry(
            identity_key=identity_key,
            body_hash=body_hash,
            word_count=word_count,
            file_path=str(resolved),
            source_id=header.get("source_id") or existing.source_id,
            title=header.get("title") or existing.title,
            date=header.get("date") or existing.date,
        )
    )
    return IngestVerdict(
        action="process",
        reason=(
            "same source, same size but different content (hash changed). "
            "Treating as corrected version."
        ),
        identity_key=identity_key,
        body_hash=body_hash,
        word_count=word_count,
        previous_word_count=existing.word_count,
    )


# ---------------------------------------------------------------------------
# Delta extraction helper
# ---------------------------------------------------------------------------


def extract_delta(text: str, start_word: int) -> str:
    """Extract content starting from a given word index.

    Used for incremental processing: returns only the NEW portion
    of a transcript that wasn't in the previously ingested version.
    """
    body = _extract_body(text)
    words = body.split()
    if start_word >= len(words):
        return ""
    return " ".join(words[start_word:])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("""
Ingestion Guard — Phase 0 Deduplication
========================================

Usage:
    python -m engine.intelligence.pipeline.ingestion_guard check <file>
    python -m engine.intelligence.pipeline.ingestion_guard stats
    python -m engine.intelligence.pipeline.ingestion_guard reset
        """)
        sys.exit(1)

    cmd = sys.argv[1].lower()
    reg = IngestionRegistry()

    if cmd == "check":
        if len(sys.argv) < 3:
            print("Usage: ... check <file>", file=sys.stderr)
            sys.exit(1)
        verdict = guard_ingest(sys.argv[2], registry=reg)
        print(
            json.dumps(
                {
                    "action": verdict.action,
                    "kind": verdict.kind,
                    "reason": verdict.reason,
                    "identity_key": verdict.identity_key,
                    "word_count": verdict.word_count,
                    "previous_word_count": verdict.previous_word_count,
                    "delta_start_word": verdict.delta_start_word,
                },
                indent=2,
            )
        )

    elif cmd == "stats":
        s = reg.stats()
        print(f"Ingestion Registry: {s['total_entries']} entries")
        print(f"Path: {s['registry_path']}")

    elif cmd == "reset":
        reg.reset()
        print("Registry cleared.")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
