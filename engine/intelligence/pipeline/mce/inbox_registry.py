"""INBOX-REGISTRY — Input File Registry — Story MCE-11.16.

Tracks **source files that were ingested** (inputs) in contrast to
``FILE-REGISTRY.json`` which tracks pipeline **output artifacts**.

Why two registries?
    FILE-REGISTRY.json  → "which files did this slug produce?"
    INBOX-REGISTRY.json → "which source files were ingested and fully
                           propagated?"

The input registry answers founder questions like:
    - "Was Liam Ottley video LO-0003 fully processed? MD5=?"
    - "Which files have INCOMPLETE propagation right now?"
    - "Did I already ingest this file?"

Entry point:
    update_inbox_registry(slug, source_file, bucket="external") -> dict

Art. XII (Pipeline MCE Integrity): fail-open — exceptions NEVER abort
cmd_finalize.  Callers must wrap in try/except.

Schema version 1.0.0 — see STORY-MCE-11.16 AC1.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical root — matches the pattern across orchestrate.py and propagation_tracker.py
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_ARTIFACTS = _PROJECT_ROOT / ".data" / "artifacts"
_INBOX_REGISTRY_FILE = _ARTIFACTS / "INBOX-REGISTRY.json"

# Maximum source entries to retain (prune oldest on overflow)
_MAX_ENTRIES = 200

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _atomic_write_json(data: dict[str, Any], target: Path) -> None:
    """Write *data* to *target* atomically via temp file + os.replace.

    Mirrors the Art. X atomic write pattern used across orchestrate.py and
    propagation_tracker.py.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path_str = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, default=str)
            fh.write("\n")
        os.replace(tmp_path_str, target)
    except Exception:
        try:
            os.unlink(tmp_path_str)
        except OSError:
            pass
        raise


def _load_registry(registry_path: Path) -> dict[str, Any]:
    """Load existing INBOX-REGISTRY.json or return a fresh skeleton."""
    if registry_path.exists():
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("inbox_registry: cannot read existing file: %s", exc)
    return {
        "version": "1.0.0",
        "last_updated": _now_iso(),
        "total_sources": 0,
        "sources": {},
    }


def _compute_md5(file_path: Path) -> str:
    """Compute MD5 hex digest of *file_path* in chunks to handle large files.

    For video/audio files we read in 64 KB blocks to avoid loading multi-GB
    binaries into memory.  MD5 is used for identity (fast dedup signal) while
    SHA-256 (content_hash) is used for integrity.
    """
    m = hashlib.md5()
    try:
        with file_path.open("rb") as fh:
            for block in iter(lambda: fh.read(65536), b""):
                m.update(block)
    except OSError as exc:
        logger.warning("inbox_registry: cannot compute MD5 for %s: %s", file_path, exc)
        return ""
    return m.hexdigest()


def _compute_content_hash(file_path: Path) -> str:
    """Compute SHA-256 hex digest with canonical normalisation for text files.

    For text-based sources (transcripts, PDFs converted to text) we apply the
    canonical_hash normalisation (NFC + LF endings).  For binary files we fall
    back to a raw SHA-256 without normalisation.
    """
    try:
        suffix = file_path.suffix.lower()
        if suffix in {".md", ".txt", ".json", ".yaml", ".yml"}:
            from engine.intelligence.pipeline.hashing import canonical_hash

            text = file_path.read_text(encoding="utf-8", errors="replace")
            return canonical_hash(text)
        else:
            # Binary: raw SHA-256
            h = hashlib.sha256()
            with file_path.open("rb") as fh:
                for block in iter(lambda: fh.read(65536), b""):
                    h.update(block)
            return h.hexdigest()
    except OSError as exc:
        logger.warning("inbox_registry: cannot compute content_hash for %s: %s", file_path, exc)
        return ""


def _prune_oldest(sources: dict[str, Any], max_entries: int = _MAX_ENTRIES) -> None:
    """Remove oldest entries in-place when *sources* exceeds *max_entries*."""
    if len(sources) <= max_entries:
        return
    # Sort by ingested_at ascending (oldest first) — drop from the front
    sorted_keys = sorted(
        sources.keys(),
        key=lambda k: sources[k].get("ingested_at", ""),
    )
    keys_to_drop = sorted_keys[: len(sources) - max_entries]
    for k in keys_to_drop:
        del sources[k]


def _resolve_source_id(slug: str, source_file: Path) -> str:
    """Return a canonical source_id for this (slug, source_file) pair.

    Priority:
        1. Derive from ingestion_guard's identity_key logic (reads file header).
        2. Fall back to batch_auto_creator.derive_source_code(slug).
        3. Fall back to slug itself.
    """
    # Attempt 1: ingestion guard identity
    try:
        from engine.intelligence.pipeline.ingestion_guard import (
            _compute_identity_key,
            _parse_header,
        )

        text = source_file.read_text(encoding="utf-8", errors="replace")
        header = _parse_header(text)
        identity_key = _compute_identity_key(header)
        if identity_key:
            return identity_key
    except Exception:
        pass

    # Attempt 2: source code from batch_auto_creator
    try:
        from engine.intelligence.pipeline.batch_auto_creator import derive_source_code

        code = derive_source_code(slug)
        if code:
            return code
    except Exception:
        pass

    # Fallback: slug
    return slug


def _read_propagation_summary(slug: str) -> dict[str, Any] | None:
    """Read the PROPAGATION-GAPS.json entry for *slug* and extract a compact summary.

    Returns None if PROPAGATION-GAPS.json has not been written yet for this slug
    (MCE-11.4 not yet run or failed).

    The compact summary mirrors the shape required by AC5:
        {
            "chunks":   {"count": N, "status": "OK|MISSING"},
            "insights": {"count": N, "status": "OK|MISSING"},
            "dossier":  {"updated": true|false},
            "agents_updated": ["agent/path", ...]
        }
    """
    gaps_file = _ARTIFACTS / "PROPAGATION-GAPS.json"
    if not gaps_file.exists():
        return None

    try:
        data = json.loads(gaps_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("inbox_registry: cannot read PROPAGATION-GAPS.json: %s", exc)
        return None

    sources = data.get("sources", {})
    if not isinstance(sources, dict):
        return None

    # The tracker keys entries by source_id or slug — try both patterns
    entry: dict[str, Any] | None = None

    # Direct key match
    if slug in sources:
        entry = sources[slug]
    else:
        # Scan for any entry whose slug field matches
        for _key, val in sources.items():
            if isinstance(val, dict) and val.get("slug") == slug:
                entry = val
                break

    if entry is None:
        return None

    gaps = entry.get("gaps", {})
    gap1 = gaps.get("GAP-TYPE-1", {})
    gap2 = gaps.get("GAP-TYPE-2", {})
    gap3 = gaps.get("GAP-TYPE-3", {})
    gap4 = gaps.get("GAP-TYPE-4", {})

    return {
        "chunks": {
            "count": gap1.get("count", 0),
            "status": "OK" if gap1.get("status") == "PASS" else "MISSING",
        },
        "insights": {
            "count": gap2.get("count", 0),
            "status": "OK" if gap2.get("status") == "PASS" else "MISSING",
        },
        "dossier": {
            "updated": bool(gap3.get("updated", False)),
        },
        "agents_updated": gap4.get("agents_updated", []),
    }


def _determine_status(
    slug: str,
    md5: str,
    existing_sources: dict[str, Any],
) -> str:
    """Return the status string for a new/updated INBOX-REGISTRY entry.

    Logic:
        DUPLICATE   — same MD5 already exists in the registry under a
                      DIFFERENT source_id (i.e. the file was re-ingested)
        COMPLETE    — PROPAGATION-GAPS says gap_count == 0
        INCOMPLETE  — PROPAGATION-GAPS says gap_count > 0
        PROCESSING  — PROPAGATION-GAPS not yet written for this slug
    """
    # DUPLICATE check: is this MD5 already present for a different slug/source?
    if md5:
        for _sid, entry in existing_sources.items():
            if entry.get("md5") == md5 and entry.get("slug") != slug:
                return "DUPLICATE"

    # Read propagation outcome
    gaps_file = _ARTIFACTS / "PROPAGATION-GAPS.json"
    if not gaps_file.exists():
        return "PROCESSING"

    try:
        data = json.loads(gaps_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "PROCESSING"

    sources = data.get("sources", {})
    entry: dict[str, Any] | None = None

    if slug in sources:
        entry = sources[slug]
    else:
        for _key, val in sources.items():
            if isinstance(val, dict) and val.get("slug") == slug:
                entry = val
                break

    if entry is None:
        return "PROCESSING"

    gap_count = entry.get("gap_count", -1)
    if gap_count == 0:
        return "COMPLETE"
    if gap_count > 0:
        return "INCOMPLETE"
    return "PROCESSING"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def update_inbox_registry(
    slug: str,
    source_file: Path | str,
    bucket: str = "external",
    *,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    """Write or update the INBOX-REGISTRY.json entry for *slug*/*source_file*.

    Called from cmd_finalize (Story MCE-11.16 AC2).  Idempotent — running
    multiple times for the same slug updates the existing entry in-place.

    Args:
        slug:          Person/source slug (e.g. "liam-ottley").
        source_file:   Path to the original ingested file.  May be absolute or
                       relative to the project root.
        bucket:        Knowledge bucket ("external", "business", "personal").
        registry_path: Override for the registry file path (used in tests to
                       redirect writes to tmp_path).

    Returns:
        The entry dict that was written.
    """
    target = registry_path or _INBOX_REGISTRY_FILE
    source_path = Path(source_file)

    # Make file_path repo-relative for portability (Constitution Art. XIV portable-paths)
    try:
        repo_relative = str(source_path.relative_to(_PROJECT_ROOT))
    except ValueError:
        repo_relative = str(source_path)

    # ------------------------------------------------------------------
    # 1. Compute cryptographic identifiers
    # ------------------------------------------------------------------
    md5 = _compute_md5(source_path) if source_path.exists() else ""
    content_hash = _compute_content_hash(source_path) if source_path.exists() else ""

    # ------------------------------------------------------------------
    # 2. Derive source_id
    # ------------------------------------------------------------------
    source_id = _resolve_source_id(slug, source_path) if source_path.exists() else slug

    # ------------------------------------------------------------------
    # 3. Load existing registry
    # ------------------------------------------------------------------
    registry = _load_registry(target)
    sources: dict[str, Any] = registry.get("sources", {})
    if not isinstance(sources, dict):
        sources = {}

    # ------------------------------------------------------------------
    # 4. Preserve ingested_at from existing entry (idempotent)
    # ------------------------------------------------------------------
    now = _now_iso()
    existing_entry = sources.get(source_id, {})
    ingested_at = existing_entry.get("ingested_at") or now

    # ------------------------------------------------------------------
    # 5. Determine status via PROPAGATION-GAPS.json (MCE-11.4 integration)
    # ------------------------------------------------------------------
    status = _determine_status(slug, md5, sources)

    # ------------------------------------------------------------------
    # 6. Build propagation_summary from PROPAGATION-GAPS.json
    # ------------------------------------------------------------------
    propagation_summary = _read_propagation_summary(slug)

    # ------------------------------------------------------------------
    # 7. Build entry
    # ------------------------------------------------------------------
    entry: dict[str, Any] = {
        "source_id": source_id,
        "file_path": repo_relative,
        "md5": md5,
        "content_hash": content_hash,
        "status": status,
        "slug": slug,
        "bucket": bucket,
        "ingested_at": ingested_at,
        "processed_at": now,
        "propagation_summary": propagation_summary,
    }

    # ------------------------------------------------------------------
    # 8. Upsert into registry and prune
    # ------------------------------------------------------------------
    sources[source_id] = entry
    _prune_oldest(sources, _MAX_ENTRIES)

    registry["sources"] = sources
    registry["last_updated"] = now
    registry["total_sources"] = len(sources)

    # ------------------------------------------------------------------
    # 9. Atomic write
    # ------------------------------------------------------------------
    _atomic_write_json(registry, target)

    logger.info(
        "inbox_registry: wrote entry for %s (source_id=%s, status=%s, md5=%s...)",
        slug,
        source_id,
        status,
        md5[:8] if md5 else "n/a",
    )
    return entry
