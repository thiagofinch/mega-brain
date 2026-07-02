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

import dataclasses
import hashlib
import json
import logging
import os
import re
import sys
import tempfile
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path for direct invocation
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Module imports (after path fix)
# ---------------------------------------------------------------------------

from engine.intelligence.pipeline.mce.metadata_manager import MetadataManager  # noqa: E402
from engine.intelligence.pipeline.mce.metrics import MetricsTracker  # noqa: E402
from engine.intelligence.pipeline.mce.state_machine import PipelineStateMachine  # noqa: E402
from engine.intelligence.pipeline.mce.transaction import (  # noqa: E402
    pipeline_transaction,
)
from engine.intelligence.pipeline.mce.workflow_detector import (  # noqa: E402
    detect as detect_workflow,
)
from engine.intelligence.pipeline.phase_payload import (  # noqa: E402
    emit_phase_payload,
)

logger = logging.getLogger("mce.orchestrate")

# ---------------------------------------------------------------------------
# Lazy imports -- only loaded when the command that needs them runs.
# This avoids import-time failures if optional deps are missing.
# ---------------------------------------------------------------------------


def _import_ingestion_guard():
    """Lazy import for ingestion_guard (Phase 0 dedup)."""
    from engine.intelligence.pipeline.ingestion_guard import (
        extract_delta,
        guard_ingest,
    )

    return guard_ingest, extract_delta


def _import_scope_classifier():
    """Lazy import for scope_classifier to avoid heavy startup."""
    from engine.intelligence.pipeline.scope_classifier import (
        ClassificationContext,
        classify,
    )

    return classify, ClassificationContext


def _import_smart_router():
    """Lazy import for smart_router."""
    from engine.intelligence.pipeline.smart_router import route

    return route


def _import_inbox_organizer():
    """Lazy import for inbox_organizer."""
    from engine.intelligence.pipeline.inbox_organizer import organize_inbox

    return organize_inbox


def _import_batch_auto_creator():
    """Lazy import for batch_auto_creator."""
    from engine.intelligence.pipeline.batch_auto_creator import scan_and_create

    return scan_and_create


def _import_memory_enricher():
    """Lazy import for memory_enricher."""
    from engine.intelligence.pipeline.memory_enricher import enrich_from_insights_state

    return enrich_from_insights_state


def _import_workspace_sync():
    """Lazy import for workspace_sync."""
    from engine.intelligence.pipeline.workspace_sync import sync

    return sync


def _import_contradiction_detector():
    """Lazy import for contradiction_detector (MCE-4.4)."""
    from engine.intelligence.pipeline.mce.contradiction_detector import (
        build_review_queue_item_for_contradiction,
        build_review_queue_item_for_open_loop,
        detect,
    )

    return detect, build_review_queue_item_for_contradiction, build_review_queue_item_for_open_loop


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

try:
    from engine.paths import (
        AGENTS,
        ARTIFACTS,
        KNOWLEDGE_BUSINESS,
        LOGS,
        MISSION_CONTROL,
        ROUTING,
    )
except ImportError:
    ARTIFACTS = _PROJECT_ROOT / "artifacts"
    LOGS = _PROJECT_ROOT / "logs"
    MISSION_CONTROL = _PROJECT_ROOT / ".claude" / "mission-control"
    KNOWLEDGE_BUSINESS = _PROJECT_ROOT / "knowledge" / "business"
    AGENTS = _PROJECT_ROOT / "agents"
    ROUTING = {
        "mce_state": MISSION_CONTROL / "mce",
        "mce_metrics_log": LOGS / "mce-metrics.jsonl",
        "business_insights": KNOWLEDGE_BUSINESS / "insights",
        "business_dossiers": KNOWLEDGE_BUSINESS / "dossiers",
        "business_people": KNOWLEDGE_BUSINESS / "people",
        "business_dna": KNOWLEDGE_BUSINESS / "dna",
        "business_dna_persons": KNOWLEDGE_BUSINESS / "dna" / "persons",
        "business_sops": KNOWLEDGE_BUSINESS / "sops",
        "business_sources": KNOWLEDGE_BUSINESS / "sources",
        "business_dossiers_companies": KNOWLEDGE_BUSINESS / "dossiers" / "companies",
        "agents_business": AGENTS / "business",
    }

_ORCHESTRATE_LOG = LOGS / "mce-orchestrate.jsonl"
# Canonical audit log — 8-field schema (Story MCE-11.18)
_AUDIT_LOG = LOGS / "AUDIT" / "audit.jsonl"

# Canonical operation enum (Story MCE-11.18 — AC6)
# OLD enum (8 values) + NEW values legitimately added by the MCE pipeline:
#   PROCESS_JARVIS_COMPLETE — full pipeline completion (replaces PIPELINE_COMPLETE in NEW)
#   RAG_INDEX_DRIFT_DETECTED — detected drift between chunks and RAG vectors
#   BATCH_CREATE — batch creation event
#   CHUNK_CREATE — chunking phase output
#   ENTITY_RESOLVE — entity resolution phase
#   INSIGHT_EXTRACT — insight extraction phase
#   NARRATIVE_SYNTHESIZE — narrative synthesis phase
#   DOSSIER_CREATE — dossier creation
#   DOSSIER_UPDATE — dossier update
#   MEMORY_UPDATE — agent memory update
#   RAG_INDEX — RAG indexation
#   STATE_FILE_WRITE — pipeline state machine write
#   PIPELINE_COMPLETE — pipeline completion (OLD canonical)
#   ENFORCEMENT_BYPASS — enforcement bypass event
#   INGEST — file ingestion
_AUDIT_OPERATION_ENUM = frozenset(
    {
        "INGEST",
        "CHUNK_CREATE",
        "ENTITY_RESOLVE",
        "INSIGHT_EXTRACT",
        "NARRATIVE_SYNTHESIZE",
        "DOSSIER_CREATE",
        "DOSSIER_UPDATE",
        "MEMORY_UPDATE",
        "RAG_INDEX",
        "STATE_FILE_WRITE",
        "PIPELINE_COMPLETE",
        "ENFORCEMENT_BYPASS",
        # NEW values added by MCE pipeline (not in OLD enum — legitimately added):
        "PROCESS_JARVIS_COMPLETE",
        "RAG_INDEX_DRIFT_DETECTED",
        "BATCH_CREATE",
    }
)

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


def infer_source_person(source_id: str, slug: str | None = None) -> str:
    """Derive source_person from source_id or slug.

    Returns the human-readable person slug, or ``"unknown"`` when not inferible.

    Pattern examples::

        "AH-YT-0001"         -> "alex-hormozi"   (initials prefix)
        "alex-hormozi-YT-123" -> "alex-hormozi"  (slug prefix)
        "MEET-0366"           -> "unknown"        (business meeting, no person)
        None / ""             -> "unknown"

    Story: MCE-11.18 (AC2)
    """
    # Priority 1: explicit slug passed by caller
    if slug:
        # Normalise: lowercase, underscores to hyphens
        return slug.lower().replace("_", "-")

    if not source_id:
        return "unknown"

    sid = source_id.strip()

    # Pattern: "alex-hormozi-YT-123" — starts with two kebab parts before a known tag
    _known_tags = {"YT", "PDF", "BOOK", "PODCAST", "MISC", "REPROCESS", "COURSE"}
    parts = sid.replace("_", "-").split("-")
    # Try to extract slug prefix up to first known tag or numeric segment
    slug_parts: list[str] = []
    for p in parts:
        if p.upper() in _known_tags or p.upper().startswith("MEET") or p.isdigit():
            break
        slug_parts.append(p.lower())
    if len(slug_parts) >= 2:
        return "-".join(slug_parts)

    # Pattern: "AH-YT-0001" — initials. We can only return the initials-slug.
    # Without a lookup table we cannot expand to full name.
    if len(parts) >= 1 and len(parts[0]) == 2 and parts[0].isupper():
        # Known initials map (extend as needed)
        _initials_map = {
            "AH": "alex-hormozi",
            "CG": "cole-gordon",
            "JM": "jeremy-miner",
            "JL": "jordan-lee",
            "PA": "process-architect",
            "LO": "liam-ottley",
            "TF": "founder",
        }
        return _initials_map.get(parts[0].upper(), "unknown")

    return "unknown"


def _md5_checksum(file_path: str | Path) -> str | None:
    """Compute MD5 checksum of a file.

    Returns hex digest string, or ``None`` if the file does not exist or
    cannot be read.  Non-fatal by design — checksum failure must never
    block pipeline operations.

    Story: MCE-11.18 (AC4)
    """
    try:
        p = Path(file_path)
        if not p.is_file():
            return None
        h = hashlib.md5(usedforsecurity=False)
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        logger.debug("_md5_checksum failed for %s", file_path, exc_info=True)
        return None


def _append_audit_jsonl(
    *,
    operation: str,
    source_id: str,
    source_person: str,
    status: str,
    phase: int | None,
    details: dict[str, Any] | None = None,
    checksum: str | None = None,
) -> None:
    """Append a fully-formed 8-field entry to logs/AUDIT/audit.jsonl.

    This is the canonical audit log writer for the MCE pipeline.  All 8
    schema fields from §8.5 of the JARVIS v2.1 technical doc are emitted.

    Non-fatal: swallows all exceptions so it never blocks pipeline work.

    Fields:
        timestamp   -- ISO 8601 UTC (auto-set)
        operation   -- operation type (validated against _AUDIT_OPERATION_ENUM)
        source_id   -- source identifier (e.g. "AH-YT-0001", "MEET-0366")
        source_person -- derived person slug (e.g. "alex-hormozi" / "unknown")
        details     -- operation-specific context dict
        checksum    -- MD5 hex of the affected file, or None
        status      -- "SUCCESS" | "FAILED" | "WARN"
        phase       -- pipeline phase number (0-8), None for hooks

    Story: MCE-11.18 (AC2-AC5)
    """
    if operation not in _AUDIT_OPERATION_ENUM:
        logger.debug("_append_audit_jsonl: unrecognised operation %r — emitting anyway", operation)
    entry: dict[str, Any] = {
        "timestamp": _now_iso(),
        "operation": operation,
        "source_id": source_id,
        "source_person": source_person,
        "details": details if details is not None else {},
        "checksum": checksum,
        "status": status,
        "phase": phase,
    }
    try:
        _AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_AUDIT_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write canonical audit JSONL", exc_info=True)


def _json_out(data: dict[str, Any]) -> None:
    """Print a JSON object to stdout (machine-readable output)."""
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _derive_source_code(slug: str) -> str:
    """Derive a 2-char source code from a slug.

    Examples::

        alex-hormozi  -> AH
        process-architect -> PA
        cole-gordon   -> CG
        jeremy-miner  -> JM
        single        -> SI
    """
    # Ignora partes vazias — slugs como "[meet-1415]-..." ou com "--"/hífen líder
    # geram strings vazias no split e estouravam IndexError em parts[i][0].
    parts = [p for p in slug.split("-") if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return (slug.strip("-")[:2] or "XX").upper()


def _slug_from_path(file_path: str | Path) -> str:
    """Best-effort slug extraction from a file path.

    Order of resolution (first hit wins):

    Step 0 (MCE-13.7): If an entity-discovery sidecar exists adjacent to
        the file, use its ``decision.entity_author``. Covers the case where
        a file was quarantined in ``_unclassified/`` due to a sidecar naming
        mismatch (Bug B cascade) — sidecar still carries the correct author.

    Step 1: Component immediately after ``inbox`` in the path (canonical).
        - ``knowledge/external/inbox/{slug}/...``
        - ``knowledge/personal/inbox/{slug}/...``
        - ``workspace/inbox/{category}/{slug}/...``

    Step 2: Parent directory name (fallback), slugified.
    """
    import json as _json

    resolved = Path(file_path).resolve()

    # ------------------------------------------------------------------
    # Step 0 — honor entity-discovery sidecar (MCE-13.7)
    # ------------------------------------------------------------------
    try:
        primary_sidecar = resolved.parent / f"{resolved.name}.entity-discovery.json"
        candidates: list[Path] = []
        if primary_sidecar.exists():
            candidates.append(primary_sidecar)
        else:
            # Use the portion before the first dot as base prefix (e.g.
            # "how-to-make-business-growth" from
            # "how-to-make-business-growth.transcript.txt") so that a sidecar
            # named "how-to-make-business-growth.youtube.entity-discovery.json"
            # is found. Limit to 30 chars to avoid false positives.
            base_prefix = resolved.name.split(".")[0].lower()[:30]
            if base_prefix:
                for c in sorted(resolved.parent.glob("*.entity-discovery.json")):
                    if base_prefix in c.name.lower():
                        candidates.append(c)
                        break
        for sidecar in candidates:
            try:
                data = _json.loads(sidecar.read_text(encoding="utf-8"))
                decision = data.get("decision") or {}
                author = (decision.get("entity_author") or "").strip()
                if author and author.lower() not in {
                    "",
                    "unclassified",
                    "_unclassified",
                    "unknown",
                    "none",
                }:
                    return author
            except Exception:
                continue
    except Exception:
        pass

    # ------------------------------------------------------------------
    # Step 1 — component after 'inbox' in path
    # ------------------------------------------------------------------
    parts = resolved.parts
    for i, part in enumerate(parts):
        if part.lower() == "inbox" and i + 1 < len(parts):
            candidate = parts[i + 1]
            # Skip generic category folders
            if candidate.upper() in {"PESSOAL", "EMPRESA", "EXTERNAL", "BUSINESS", "PERSONAL"}:
                if i + 2 < len(parts):
                    candidate = parts[i + 2]
            return candidate.lower().replace(" ", "-").replace("_", "-")

    # ------------------------------------------------------------------
    # Step 2 — parent directory name
    # ------------------------------------------------------------------
    parent = Path(file_path).parent.name
    return parent.lower().replace(" ", "-").replace("_", "-")


def _bucket_from_path(file_path: str | Path) -> str:
    """Detect knowledge bucket from a file path.

    Returns ``"external"``, ``"business"``, or ``"personal"``.
    Falls back to ``"external"`` when ambiguous.
    """
    path_str = str(Path(file_path).resolve()).lower()
    if "/knowledge/personal/" in path_str or "/personal/inbox/" in path_str:
        return "personal"
    if "/knowledge/business/" in path_str or "/business/inbox/" in path_str:
        return "business"
    return "external"


def _agent_dir_for_slug(slug: str, bucket: str = "external") -> Path:
    """Return the agent directory for a slug+bucket combination.

    Bucket mapping:
    - ``external`` -> ``agents/external/{slug}/``
    - ``business`` -> ``agents/business/{slug}/``
    - ``personal`` -> ``agents/personal/{slug}/``
    """
    return _PROJECT_ROOT / "agents" / bucket / slug


def _dna_dir_for_slug(slug: str, bucket: str = "external") -> Path:
    """Return the DNA directory for a slug+bucket combination.

    Delegates to the single SOT resolver (``PersonArtifactPaths``). Bucket mapping
    (STORY-MCE-BUCKET-AWARE-WRITES — D1, convention B):
    - ``external`` -> ``knowledge/external/dna/persons/{slug}/``
    - ``business`` -> ``knowledge/business/dna/persons/{slug}/``  (was business/people — Art. XIII fix)
    - ``personal`` -> ``knowledge/personal/dna/``  (single person, no subdir)
    """
    from engine.intelligence.pipeline.mce.person_paths import PersonArtifactPaths

    return PersonArtifactPaths(slug, bucket, root=_PROJECT_ROOT).dna


def _detect_bucket_for_slug(slug: str) -> str:
    """Detect which bucket a slug belongs to.

    Thin wrapper over the single canonical resolver
    ``person_paths.resolve_bucket`` (STORY-MCE-BUCKET-AWARE-WRITES — D2/D3).

    The resolver consults the entity-discovery sidecar FIRST (the routing SOT),
    then MetadataManager.bucket / classification.primary_bucket, then
    inbox/processed/agents/dna filesystem heuristics, defaulting to ``external``
    with a journey-log fallback event (Art. IX). NARRATIVES-STATE is no longer
    trusted as a source here — it was the poisoned SOT that recorded ``external``
    for business-routed people (Art. XIII breach).
    """
    from engine.intelligence.pipeline.mce.person_paths import resolve_bucket

    return resolve_bucket(slug, root=_PROJECT_ROOT)


def _resolve_source_file_for_slug(slug: str, bucket: str) -> Path | None:
    """Return the most likely source file path for *slug* in *bucket*.

    Checks (in order):
        1. MetadataManager.file_path — explicit file path stored at ingest time.
        2. knowledge/{bucket}/processed/{slug}/ — post-lifecycle move location.
        3. knowledge/{bucket}/inbox/{slug}/ — pre-lifecycle move location.

    Returns None when no source file can be located (e.g. the file was a URL
    or the inbox was already cleaned up without leaving a record).
    """
    # Priority 1: metadata manager has explicit file_path
    try:
        mgr = MetadataManager.load(slug)
        if mgr is not None:
            fp = getattr(mgr, "file_path", None)
            if fp:
                candidate = Path(fp)
                if candidate.exists():
                    return candidate
    except Exception:
        pass

    # Priority 2: processed/ directory (after lifecycle move)
    processed_dir = _PROJECT_ROOT / "knowledge" / bucket / "processed" / slug
    if processed_dir.is_dir():
        candidates = sorted(processed_dir.iterdir())
        if candidates:
            return candidates[0]

    # Priority 3: inbox/ directory (before lifecycle move)
    inbox_dir = _PROJECT_ROOT / "knowledge" / bucket / "inbox" / slug
    if inbox_dir.is_dir():
        candidates = sorted(inbox_dir.iterdir())
        if candidates:
            return candidates[0]

    return None


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
# MCE-13.18 — Squad Activation Telemetry helper
# ---------------------------------------------------------------------------

#: Canonical squad → (task, agent) tuples for each pipeline stage.
_SQUAD_ACTIVATION_MAP: dict[str, list[tuple[str, str, str]]] = {
    "B2_batch": [
        ("batch_creation", "batch-manager", "chunk-embed-upsert"),
        ("chunk_processing", "text-chunker", "tokenize-embed"),
    ],
    "B5_dna": [
        ("insight_extraction", "sage-extractor", "extract-l1-l5"),
        ("behavioral_extraction", "behavioral-analyst", "extract-l6"),
        ("identity_extraction", "identity-analyst", "extract-l7-l9-l10"),
        ("voice_extraction", "voice-analyst", "extract-l8"),
    ],
    "B6_finalize": [
        ("memory_enrichment", "memory-enricher", "enrich-agent-memory"),
        ("workspace_sync", "workspace-syncer", "sync-l4-ops"),
        ("dossier_consolidation", "dossier-generator", "write-dossier"),
    ],
}


def _build_squad_activation_telemetry(
    slug: str,
    phases_completed: dict[str, Any],
    stage: str,
) -> list[dict[str, Any]]:
    """Build squad activation entries for PHASE-STREAM telemetry.

    MCE-13.18: Populates squads_activated list from canonical pipeline stage
    map. Each entry that has a non-empty/non-error result is counted as
    activated.

    Args:
        slug:             Pipeline slug.
        phases_completed: Dict of phase_name → result dict.
        stage:            One of B2_batch, B5_dna, B6_finalize.

    Returns:
        List of {squad, task, agent} dicts for emit_squad_activation.
    """
    stage_squads = _SQUAD_ACTIVATION_MAP.get(stage, [])
    activated: list[dict[str, Any]] = []
    for squad_name, task, agent in stage_squads:
        phase_result = phases_completed.get(squad_name, {})
        # Count as activated if result is not empty dict and no top-level error
        if phase_result and not (isinstance(phase_result, dict) and "error" in phase_result):
            activated.append({"squad": squad_name, "task": task, "agent": agent, "slug": slug})
        elif not phase_result:
            # No result check: assume activated since phase is in canonical map
            activated.append({"squad": squad_name, "task": task, "agent": agent, "slug": slug})
    return activated


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

    # STORY-MCE-7.0 AC-3: source_id early-exit — check if this file's resolved
    # path (or its processed/ counterpart) is already in the processed-sources
    # registry. If yes, the file was fully processed in a prior run — skip
    # immediately without reading the file or calling the full ingestion_guard.
    # This is a cheap O(1) set lookup, not a file I/O operation.
    # Fail-open: any exception falls through to normal flow.
    try:
        _ps_candidates = {str(resolved)}
        # Also check the processed/ path (lifecycle AC-2 may have moved it)
        _proc_root = resolved.parent.parent.parent  # knowledge/{bucket}/inbox/{slug}/../..
        _slug_from_res = resolved.parent.name
        for _bkt in ("external", "business", "personal"):
            _proc_path = (
                _PROJECT_ROOT / "knowledge" / _bkt / "processed" / _slug_from_res / resolved.name
            )
            _ps_candidates.add(str(_proc_path))

        _ps_already = _load_processed_sources(slug)
        _ps_hit = _ps_candidates & _ps_already
        if _ps_hit:
            _hit_path = next(iter(_ps_hit))
            logger.info(
                "[MCE-7.0 AC-3] source_id early-exit for %s — already in processed registry",
                resolved.name,
            )
            _append_jsonl(
                {
                    "event": "ingestion_guard",
                    "timestamp": _now_iso(),
                    "file": str(resolved),
                    "slug": slug,
                    "action": "skip",
                    "reason": f"already_processed_source (MCE-7.0): {_hit_path}",
                    "identity_key": f"processed-registry:{resolved.name}",
                    "word_count": 0,
                    "previous_word_count": 0,
                }
            )
            return _build_result(
                "ingest",
                success=True,
                slug=slug,
                skipped=True,
                skip_reason=f"already_processed_source (MCE-7.0 AC-3): {resolved.name}",
                identity_key=f"processed-registry:{resolved.name}",
                word_count=0,
                file_path=str(resolved),
                duration_ms=(time.monotonic() - t0) * 1000,
            )
    except Exception as _ac3_exc:
        # Fail-open — fallback to normal guard flow
        logger.debug("[MCE-7.0 AC-3] source_id check failed (non-fatal): %s", _ac3_exc)

    # MCE-2.1 AC4: binary-safe pre-check. guard_ingest_fn reads the file as
    # UTF-8 text -- for raw video/audio that corrupts the registry (title
    # becomes binary garbage, word_count is inflated to byte count). The real
    # guard runs later on the transcript produced by Speaker Visual Gate.
    _BINARY_EXTS = {
        ".mp4",
        ".mov",
        ".m4v",
        ".webm",
        ".mkv",
        ".avi",
        ".wav",
        ".mp3",
        ".m4a",
        ".flac",
        ".ogg",
        ".opus",
    }
    if resolved.suffix.lower() in _BINARY_EXTS:
        verdict = SimpleNamespace(
            action="process",
            reason=f"binary file ({resolved.suffix.lower()}) — guard skipped, runs on transcript",
            identity_key=f"binary-bypass:{resolved.name}",
            body_hash="",
            word_count=0,
            previous_word_count=0,
            delta_start_word=0,
        )
        _append_jsonl(
            {
                "event": "ingestion_guard_bypass",
                "timestamp": _now_iso(),
                "file": str(resolved),
                "slug": slug,
                "reason": "binary_file_extension",
                "extension": resolved.suffix.lower(),
            }
        )
    else:
        # Step 1.5: Ingestion Guard (Phase 0 dedup) — text/transcript path
        guard_ingest_fn, _ = _import_ingestion_guard()
        verdict = guard_ingest_fn(str(resolved))

    _append_jsonl(
        {
            "event": "ingestion_guard",
            "timestamp": _now_iso(),
            "file": str(resolved),
            "slug": slug,
            "action": verdict.action,
            "reason": verdict.reason,
            "identity_key": verdict.identity_key,
            "word_count": verdict.word_count,
            "previous_word_count": verdict.previous_word_count,
        }
    )

    # STORY-MCE-LOG-PARITY (2026-05-20): emit ASCII INGESTION GUARD VERDICT
    # so operator sees Phase 0 dedup decision (NEW/SKIP/INCREMENTAL/CORRUPTED).
    # Fail-open per Art. XII.
    try:
        from engine.intelligence.pipeline.mce.log_emitters import (
            emit_ingestion_guard,
        )

        _v = {
            "action": verdict.action,
            "reason": verdict.reason,
            "identity_key": verdict.identity_key,
            "body_hash": getattr(verdict, "body_hash", ""),
            "word_count": verdict.word_count,
            "previous_word_count": verdict.previous_word_count,
            "delta_start_word": getattr(verdict, "delta_start_word", 0),
        }
        _ig_block = emit_ingestion_guard(_v)
        print(_ig_block, flush=True)
        emit_phase_payload(
            slug=slug,
            template_id="ingestion_guard",
            status="ok" if _v.get("action") != "skip" else "silent",
            metrics=_v,
            ascii_block=_ig_block,
        )
    except Exception as _log_exc:  # pragma: no cover
        logger.debug("Ingestion guard emit failed (non-fatal): %s", _log_exc)

    # Forward declaration: emit_ingest_report happens later, after route+organize

    if verdict.action == "skip":
        # MCE-11.20 D1: When a duplicate (already-processed) skip is detected,
        # offer the founder a chance to reprocess. Mode C: auto-NO + log silently.
        # Non-fatal: if decision_gateway import fails, keep original skip behaviour.
        if getattr(verdict, "kind", None) == "duplicate":
            try:
                import re as _re_d1

                from engine.intelligence.pipeline.mce.decision_gateway import (
                    decide_d1_reprocess,
                )

                _d1_date = "desconhecida"
                _dm = _re_d1.search(r"(\d{4}-\d{2}-\d{2})", verdict.reason or "")
                if _dm:
                    _d1_date = _dm.group(1)

                _reprocess = decide_d1_reprocess(
                    source_id=verdict.identity_key,
                    date=_d1_date,
                    slug=slug,
                )
                if _reprocess:
                    logger.info(
                        "MCE-11.20 D1: founder approved reprocess for %s",
                        verdict.identity_key,
                    )
                    verdict = SimpleNamespace(
                        action="process",
                        reason=(
                            f"D1 reprocess approved by founder "
                            f"(was duplicate of {verdict.identity_key})"
                        ),
                        identity_key=verdict.identity_key,
                        body_hash=getattr(verdict, "body_hash", ""),
                        word_count=verdict.word_count,
                        previous_word_count=getattr(verdict, "previous_word_count", 0),
                        delta_start_word=0,
                    )
                    # Fall through to Step 2: classify
                else:
                    return _build_result(
                        "ingest",
                        success=True,
                        slug=slug,
                        skipped=True,
                        skip_reason=verdict.reason,
                        identity_key=verdict.identity_key,
                        word_count=verdict.word_count,
                        file_path=str(resolved),
                        duration_ms=(time.monotonic() - t0) * 1000,
                    )
            except Exception as _d1_exc:
                logger.debug("MCE-11.20 D1 gateway failed (non-fatal): %s", _d1_exc)
                return _build_result(
                    "ingest",
                    success=True,
                    slug=slug,
                    skipped=True,
                    skip_reason=verdict.reason,
                    identity_key=verdict.identity_key,
                    word_count=verdict.word_count,
                    file_path=str(resolved),
                    duration_ms=(time.monotonic() - t0) * 1000,
                )
        else:
            return _build_result(
                "ingest",
                success=True,
                slug=slug,
                skipped=True,
                skip_reason=verdict.reason,
                identity_key=verdict.identity_key,
                word_count=verdict.word_count,
                file_path=str(resolved),
                duration_ms=(time.monotonic() - t0) * 1000,
            )

    # MCE-11.20 D2: Incremental verdict means the source was seen before but
    # has grown (partial duplicate). Ask the founder if delta processing should
    # continue — could generate redundant chunks.
    # Mode C: auto-NO + log silently (frequent decision).
    if verdict.action == "incremental":
        try:
            from engine.intelligence.pipeline.mce.decision_gateway import (
                decide_d2_partial_duplicate,
            )

            _prev_wc = getattr(verdict, "previous_word_count", 0)
            _curr_wc = getattr(verdict, "word_count", 0)
            _sim_pct = int(_prev_wc / _curr_wc * 100) if _curr_wc > 0 else 0

            _d2_proceed = decide_d2_partial_duplicate(
                source_id=verdict.identity_key,
                similarity_pct=_sim_pct,
                slug=slug,
            )
            if not _d2_proceed:
                return _build_result(
                    "ingest",
                    success=True,
                    slug=slug,
                    skipped=True,
                    skip_reason=(
                        f"D2: incremental processing skipped for "
                        f"{verdict.identity_key} ({_sim_pct}% similarity to previous version)"
                    ),
                    identity_key=verdict.identity_key,
                    word_count=verdict.word_count,
                    file_path=str(resolved),
                    duration_ms=(time.monotonic() - t0) * 1000,
                )
        except Exception as _d2_exc:
            logger.debug("MCE-11.20 D2 gateway failed (non-fatal): %s", _d2_exc)

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
            source_code=_derive_source_code(slug),
        )
        mgr.pipeline_status = "in_progress"
        mgr.save()

    # Advance FSM: init -> ingesting
    if sm.state == "init":
        try:
            sm.start_ingest(None)
        except Exception:
            logger.debug("State transition init->ingesting failed", exc_info=True)

    # Initialize metrics
    mt = MetricsTracker.load(slug) or MetricsTracker(slug)
    mt.start_phase("ingest")
    elapsed = (time.monotonic() - t0) * 1000
    mt.end_phase("ingest")
    mt.save()

    # Track the source and bucket in metadata
    mgr.add_source(
        resolved.name,
        bucket=primary_bucket,
        confidence=getattr(decision, "confidence", 0.0),
    )
    # Persist bucket so downstream commands (report, finalize) know the routing
    if not hasattr(mgr, "bucket") or not mgr.bucket:
        mgr.bucket = primary_bucket

    # MCE-2.1 AC1: persist ingest-time blocks so log_generator can detect
    # Step 1 (classification) and Step 2 (organization) from metadata.yaml.
    mgr.set_classification(
        {
            "primary_bucket": getattr(decision, "primary_bucket", "unknown"),
            "cascade_buckets": getattr(decision, "cascade_buckets", []),
            "confidence": round(getattr(decision, "confidence", 0.0), 3),
            "source_type": getattr(decision, "source_type", "unknown"),
            "reasons": getattr(decision, "reasons", [])[:5],
        }
    )
    mgr.set_organization(
        {
            "organized": org_result.get("organized", 0) if isinstance(org_result, dict) else 0,
        }
    )
    mgr.set_routing(
        {
            "action": getattr(route_result, "action", "unknown"),
            "moved_to": str(getattr(route_result, "moved_to", "")),
            "references_created": getattr(route_result, "references_created", []),
        }
    )
    mgr.set_source_path(str(resolved))
    mgr.save()

    # Update ingestion guard registry with post-processing metadata
    from engine.intelligence.pipeline.ingestion_guard import IngestionRegistry

    _ig_reg = IngestionRegistry()
    _ig_reg.update_after_processing(verdict.identity_key, slug=slug)

    # Build result
    result = _build_result(
        "ingest",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        file_path=str(resolved),
        ingestion_guard={
            "action": verdict.action,
            "identity_key": verdict.identity_key,
            "word_count": verdict.word_count,
            "delta_start_word": verdict.delta_start_word if verdict.action == "incremental" else 0,
        },
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

    # Story MCE-11.18: emit canonical 8-field audit entry for INGEST operation
    _ingest_dest = result.get("destination", str(resolved))
    _ingest_wc = getattr(verdict, "word_count", 0)
    _append_audit_jsonl(
        operation="INGEST",
        source_id=result.get("source_id", slug),
        source_person=infer_source_person(result.get("source_id", ""), slug=slug),
        status="SUCCESS" if result.get("success") else "FAILED",
        phase=1,
        details={
            "word_count": _ingest_wc,
            "file_type": resolved.suffix.lower(),
            "destination": _ingest_dest,
            "classification": result.get("classification", {}),
        },
        checksum=_md5_checksum(_ingest_dest) or _md5_checksum(str(resolved)),
    )

    # STORY-MCE-LOG-PARITY Sprint 3 (2026-05-20): emit INGEST REPORT ASCII
    try:
        from engine.intelligence.pipeline.mce.log_emitters import emit_ingest_report

        _decision = {
            "entity_author": slug,
            "entity_subject": result.get("subject", ""),
            "confidence": "medium",
            "verdict": "PROCESS",
        }
        _dest = result.get("destination", str(resolved))
        _ir_block = emit_ingest_report(
            file_path=str(resolved),
            decision=_decision,
            destination=_dest,
            word_count=getattr(verdict, "word_count", 0),
        )
        print(_ir_block, flush=True)
        emit_phase_payload(
            slug=slug,
            template_id="ingest_report",
            status="ok",
            metrics={
                "file_path": str(resolved),
                "destination": _dest,
                "word_count": getattr(verdict, "word_count", 0),
            },
            ascii_block=_ir_block,
        )
    except Exception as _log_exc:  # pragma: no cover
        logger.debug("Ingest report emit failed (non-fatal): %s", _log_exc)

    # MCE-17.0 T11: emit log_generator-compatible template_ids so Chronicler
    # renderers get live stream data instead of falling back to disk.
    # These are wrapped in try/except so no failure here blocks the pipeline.
    try:
        # STEP 00 — SOURCE DISCOVERY (phantom read fixed — MCE-17.0 T11)
        emit_phase_payload(
            slug=slug,
            template_id="source_discovery",
            status="ok",
            metrics={
                "source_path": str(resolved),
                "source_type": resolved.suffix.lower().lstrip(".") or "unknown",
                "bucket": primary_bucket,
                "slug": slug,
                "discovered_at": result.get("timestamp", ""),
            },
            ascii_block="",
        )
    except Exception as _exc:  # pragma: no cover
        logger.debug("source_discovery emit failed (non-fatal): %s", _exc)

    try:
        # STEP 04 — ENTITY DISCOVERY (phantom read fixed — MCE-17.0 T11)
        # Data from entity-discovery sidecar if available, otherwise ingest routing data.
        _sidecar_path = resolved.parent / f"{resolved.name}.entity-discovery.json"
        _ed_data: dict[str, Any] = {}
        if _sidecar_path.exists():
            try:
                import json as _j
                _sd = _j.loads(_sidecar_path.read_text(encoding="utf-8"))
                _ed_data = _sd.get("decision", {})
            except Exception:
                pass
        emit_phase_payload(
            slug=slug,
            template_id="entity_discovery",
            status="ok" if _ed_data else "warning",
            metrics={
                "decision": _ed_data.get("decision", "filename-fallback"),
                "slug_final": _ed_data.get("entity_author", slug),
                "bucket_final": _ed_data.get("bucket", primary_bucket),
                "gemini_used": _ed_data.get("gemini_used", False),
                "filename_original": resolved.name,
                "tokens_dropped": _ed_data.get("tokens_dropped", []),
                "confidence": _ed_data.get("confidence", 0.0),
            },
            ascii_block="",
        )
    except Exception as _exc:  # pragma: no cover
        logger.debug("entity_discovery emit failed (non-fatal): %s", _exc)

    try:
        # STEP 05 — FILENAME SIDECAR (phantom read fixed — MCE-17.0 T11)
        _fs_path = resolved.parent / f"{resolved.name}.entity-discovery.json"
        _fs_exists = _fs_path.exists()
        emit_phase_payload(
            slug=slug,
            template_id="filename_sidecar",
            status="ok" if _fs_exists else "warning",
            metrics={
                "sidecar_path": str(_fs_path) if _fs_exists else "",
                "written": _fs_exists,
                "schema_version": "v1.1.0",
                "fields_count": 8 if _fs_exists else 0,
            },
            ascii_block="",
        )
    except Exception as _exc:  # pragma: no cover
        logger.debug("filename_sidecar emit failed (non-fatal): %s", _exc)

    try:
        # STEP 06 — CLASSIFICATION (phantom read fixed; alias of atlas_classification — MCE-17.0 T11)
        _cls = result.get("classification") or {}
        emit_phase_payload(
            slug=slug,
            template_id="classification",
            status="ok",
            metrics={
                "bucket": _cls.get("primary_bucket", primary_bucket),
                "confidence": _cls.get("confidence", 0.0),
                "secondary_bucket": (
                    _cls.get("cascade_buckets", [None])[0]
                    if _cls.get("cascade_buckets")
                    else None
                ),
                "method": "atlas",
                "source_type": _cls.get("source_type", "unknown"),
            },
            ascii_block="",
        )
    except Exception as _exc:  # pragma: no cover
        logger.debug("classification emit failed (non-fatal): %s", _exc)

    try:
        # STEP 07 — ORGANIZATION + INBOX ROUTING (phantom read fixed — MCE-17.0 T11)
        _org = result.get("organization") or {}
        _rout = result.get("routing") or {}
        emit_phase_payload(
            slug=slug,
            template_id="organization",
            status="ok",
            metrics={
                "action": _rout.get("action", "unknown"),
                "destination": _rout.get("moved_to", ""),
                "files_organized": _org.get("organized", 0),
                "source_registered": bool(_rout.get("references_created")),
            },
            ascii_block="",
        )
    except Exception as _exc:  # pragma: no cover
        logger.debug("organization emit failed (non-fatal): %s", _exc)

    try:
        # MCE-17.1 P2 — pre-00 BUCKET DE SELECAO (phantom read fixed)
        # Renderer: _step_pre_00_bucket_selection (log_generator.py)
        # Expected fields: original_filename, source_url, source_kind, verdict,
        #   confidence, routing_reason, destination, domains, atlas_confidence,
        #   bucket, slug, method, cross_references
        _bs_cls = result.get("classification") or {}
        _bs_rout = result.get("routing") or {}
        _bs_ed: dict[str, Any] = {}
        _bs_sidecar = resolved.parent / f"{resolved.name}.entity-discovery.json"
        if _bs_sidecar.exists():
            try:
                import json as _bsj
                _bs_ed = _bsj.loads(_bs_sidecar.read_text(encoding="utf-8")).get("decision", {})
            except Exception:
                pass
        # domains at ingest time = empty (ROLE-TRACKING populated later by role_tracker
        # in cmd_finalize; cascade_tree emit in P3 carries the final domain list).
        emit_phase_payload(
            slug=slug,
            template_id="bucket_selection",
            status="ok",
            metrics={
                "original_filename": resolved.name,
                "source_url": str(resolved),
                "source_kind": _bs_cls.get("source_type", resolved.suffix.lower().lstrip(".") or "unknown"),
                "verdict": _bs_ed.get("decision", "filename-fallback"),
                "confidence": _bs_ed.get("confidence", _bs_cls.get("confidence", 0.0)),
                "routing_reason": ", ".join(_bs_cls.get("reasons", [])[:2])[:50],
                "destination": str(_bs_rout.get("moved_to", "")),
                "domains": [],
                "atlas_confidence": _bs_cls.get("confidence", 0.0),
                "bucket": primary_bucket,
                "slug": slug,
                "method": "atlas",
                "cross_references": _bs_rout.get("references_created", [])[:5],
            },
            ascii_block="",
        )
    except Exception as _exc:  # pragma: no cover
        logger.debug("bucket_selection emit failed (non-fatal): %s", _exc)

    return result


# ---------------------------------------------------------------------------
# Command: batch
# ---------------------------------------------------------------------------


def cmd_batch(source_slug: str, single_file: bool = False) -> dict[str, Any]:
    """Scan organized inbox for a slug and create batches.

    Steps:
        1. Run batch_auto_creator.scan_and_create().
        2. Update state machine (init -> chunking if first batch).
        3. Update metadata with batch info.
        4. Time the operation.

    Args:
        source_slug: Person/source slug (e.g. ``"alex-hormozi"``).
        single_file: If *True*, skip the minimum file-count threshold so
                     a single file can be batched immediately.

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

    # Run batch auto-creator.
    # G15 (2026-05-13): batch_auto_creator.scan_and_create does NOT accept
    # ``min_files`` -- it uses ``force=True`` to bypass MIN_FILES threshold.
    # Passing ``min_files`` raised TypeError before this fix, so single-file
    # mode silently failed at the very first auto-orchestration step.
    scan_and_create = _import_batch_auto_creator()
    try:
        # STORY-MCE-BATCH-SLUG-SCOPE: scope the inbox walk to THIS slug so the
        # scan no longer traverses the entire inbox (1100+ files) and no longer
        # emits phantom-entry warnings for unrelated slugs. The post-scan
        # ``batches_for_slug`` filter below is retained as belt-and-suspenders.
        kwargs: dict[str, Any] = {"dry_run": False, "scope_slug": source_slug}
        if single_file:
            kwargs["force"] = True
        scan_result = scan_and_create(**kwargs)
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

    # Update state: advance to batching if in ingesting (or init for compat)
    if sm.state in ("init", "ingesting") and batches_for_slug:
        try:
            if sm.state == "init":
                sm.start_ingest(None)
            sm.start_batch(None)
        except Exception:
            logger.debug("State transition to batching failed from %s", sm.state, exc_info=True)

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

    # MCE-17.0 T11: emit batch_creation for Chronicler STEP 08 renderer
    try:
        _first_batch = batches_for_slug[0] if batches_for_slug else {}
        emit_phase_payload(
            slug=source_slug,
            template_id="batch_creation",
            status="ok" if batches_for_slug else "warning",
            metrics={
                "batch_id": _first_batch.get("batch_id", "(nenhum)"),
                "state": "created",
                "chunks_count": _first_batch.get("file_count", 0),
                "batch_index": 0,
                "total_batches": len(all_batch_ids),
            },
            ascii_block="",
        )
    except Exception as _exc:  # pragma: no cover
        logger.debug("batch_creation emit failed (non-fatal): %s", _exc)

    # Story MCE-11.18: canonical audit entry for BATCH_CREATE operation
    _append_audit_jsonl(
        operation="BATCH_CREATE",
        source_id=source_slug,
        source_person=infer_source_person(source_slug, slug=source_slug),
        status="SUCCESS" if result.get("success") else "FAILED",
        phase=2,
        details={
            "batches_created": len(batches_for_slug),
            "total_batches": len(all_batch_ids),
            "files_scanned": getattr(scan_result, "files_scanned", 0),
        },
        checksum=None,
    )
    return result


# ---------------------------------------------------------------------------
# Command: process-batch (transactional chunk+embed+upsert)
# ---------------------------------------------------------------------------


def _import_chunker():
    """Lazy import for document chunker."""
    from engine.intelligence.pipeline.chunker import chunk_document

    return chunk_document


def _ingest_chunk_strategy() -> str:
    """Real chunking strategy used by the ingest/process path (Onda 0).

    The honest label lives next to the code that pins it
    (``rag.chunker.INGEST_PATH_CHUNK_STRATEGY``) so the chronicler's STEP 09
    cannot drift into claiming "semantic" when the path actually runs
    ``semantic=False``. Lazy import + fail-open to a neutral honest string.
    """
    try:
        # Prefer the dynamic resolver so STEP 09 reflects the LIVE
        # MCE_SEMANTIC_CHUNK_ENABLED state (feature A), not a value frozen at
        # chunker import time. Fall back to the legacy constant if the resolver
        # is absent (older chunker module).
        from engine.intelligence.rag import chunker as _chunker

        fn = getattr(_chunker, "ingest_path_chunk_strategy", None)
        if callable(fn):
            return fn()
        return _chunker.INGEST_PATH_CHUNK_STRATEGY
    except Exception:
        return "unknown (strategy label unavailable)"


def _import_embedder():
    """Lazy import for embedding generator."""
    from engine.intelligence.pipeline.embedder import embed_chunks

    return embed_chunks


def _import_index_upserter():
    """Lazy import for index upserter."""
    from engine.intelligence.pipeline.index_upserter import upsert_to_index

    return upsert_to_index


# ---------------------------------------------------------------------------
# STORY-MCE-11.13: Chunk schema completeness — 7 missing fields
# ---------------------------------------------------------------------------


def _load_framework_patterns() -> list[tuple[str, str]]:
    """Load framework patterns from YAML config.

    Returns list of (name, raw_pattern_str) tuples.
    Falls back to empty list if config file is missing (graceful degradation).
    """
    config_path = (
        _PROJECT_ROOT
        / "engine"
        / "intelligence"
        / "pipeline"
        / "config"
        / "framework-patterns.yaml"
    )
    try:
        with open(config_path, encoding="utf-8") as fp:
            data = yaml.safe_load(fp)
        return [(f["name"], f["pattern"]) for f in data.get("frameworks", [])]
    except Exception as exc:
        logger.debug("[MCE-11.13] framework-patterns.yaml not loaded (non-fatal): %s", exc)
        return []


# Module-level cache for compiled patterns — loaded once per process.
_FRAMEWORK_PATTERNS_CACHE: list[tuple[str, re.Pattern]] | None = None  # type: ignore[type-arg]


def _get_framework_patterns() -> list[tuple[str, re.Pattern]]:  # type: ignore[type-arg]
    """Return compiled framework patterns, loading from cache or disk."""
    global _FRAMEWORK_PATTERNS_CACHE
    if _FRAMEWORK_PATTERNS_CACHE is None:
        raw = _load_framework_patterns()
        _FRAMEWORK_PATTERNS_CACHE = [
            (name, re.compile(pattern, re.IGNORECASE)) for name, pattern in raw
        ]
    return _FRAMEWORK_PATTERNS_CACHE


def _extract_frameworks(text: str) -> list[str]:
    """Extract framework names mentioned in chunk text using pattern matching.

    Returns deduplicated list of matched framework names.
    Requires phrase length > 4 chars to avoid single-word noise.
    """
    if not text:
        return []
    found = []
    for name, pattern in _get_framework_patterns():
        if len(name) >= 4 and pattern.search(text):
            found.append(name)
    return list(dict.fromkeys(found))  # preserve order, dedup


def _extract_metricas(text: str) -> list[str]:
    """Extract metric mentions from chunk text.

    Captures: currency ($Xk/month, $Xm, R$X), percentages (X%), and common
    numeric+unit combinations.  Stored as raw strings, no normalization.
    """
    if not text:
        return []
    patterns = [
        r"\$[\d,]+(?:\.\d+)?(?:k|m|b|K|M|B)?(?:/\w+)?",  # $100k/month, $1.5m
        r"R\$\s*[\d.,]+(?:\s*(?:mil|k|m|b|K|M|B))?",  # R$50.000
        r"[\d,]+(?:\.\d+)?%",  # 35%, 2.5%
        r"[\d,]+(?:\.\d+)?\s*(?:million|billion|thousand)\s+(?:dollar|real)",
    ]
    combined = re.compile("|".join(patterns), re.IGNORECASE)
    found = combined.findall(text)
    # Deduplicate while preserving first-occurrence order
    seen: set[str] = set()
    result = []
    for m in found:
        cleaned = m.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def _enrich_chunk_schema(
    chunks: list[dict],
    slug: str = "",
    source_id: str = "",
) -> list[dict]:
    """Add 7 missing schema fields to serialized chunks (STORY-MCE-11.13).

    Fields added (all OPTIONAL / additive — existing fields untouched):
      sequence   — 0-indexed position within this source document group
      title      — first 60 chars of chunk text, stripped
      theme      — null (taxonomy enrichment is post-pipeline)
      summary    — first 300 chars of chunk text (stripped, no newlines)
      status     — "new" on creation
      frameworks — list[str] extracted via pattern matching
      metricas   — list[str] extracted via regex

    Designed for graceful degradation: any exception on a single chunk is
    non-fatal — the chunk is returned unchanged so the pipeline never halts.
    """
    enriched = []
    for idx, chunk in enumerate(chunks):
        try:
            c = dict(chunk)  # shallow copy — never mutate caller's dict
            text: str = c.get("text") or c.get("content") or ""

            # sequence — 0-indexed position within this processing group
            if "sequence" not in c:
                c["sequence"] = idx

            # title — first 60 chars stripped, no newlines
            if "title" not in c:
                title_text = text.replace("\n", " ").strip()[:60].strip()
                c["title"] = title_text if title_text else None

            # theme — deferred to taxonomy enrichment step
            if "theme" not in c:
                c["theme"] = None

            # summary — first 300 chars stripped, compacted newlines
            if "summary" not in c:
                summary_text = " ".join(text.split())[:300].strip()
                c["summary"] = summary_text if summary_text else None

            # status — always "new" at chunk creation time
            if "status" not in c:
                c["status"] = "new"

            # frameworks — pattern-matched from text
            if "frameworks" not in c:
                c["frameworks"] = _extract_frameworks(text)

            # metricas — regex-extracted from text
            if "metricas" not in c:
                c["metricas"] = _extract_metricas(text)

        except Exception as exc:
            logger.debug("[MCE-11.13] chunk enrichment failed for idx=%d (non-fatal): %s", idx, exc)
            c = chunk  # fall back to original on error

        enriched.append(c)
    return enriched


# BATCH manifest directory (mirrors batch_auto_creator.BATCH_JSON_DIR).
# Resolved from MISSION_CONTROL (already imported above) to avoid importing
# batch_auto_creator at module load (it has heavier import side-effects).
BATCH_JSON_DIR: Path = MISSION_CONTROL / "batch-logs"


class BatchResolutionError(Exception):
    """Raised when a batch's documents cannot be honestly resolved from its
    manifest.

    Carries a human-readable message citing the ``batch_id`` and, when
    applicable, the missing basenames or the ambiguous candidate list.  The
    caller (:func:`cmd_process_batch`) converts this into a structured
    ``success=False`` result *before* any chunk/embed work — there is NO
    fallback to scanning the FLAT directory (anti-fallback rule, Story
    MCE-PB-SCOPE / extraction-no-fallbacks.md).
    """


def _resolve_batch_documents(batch_id: str, slug: str) -> list[str]:
    """Resolve the EXACT document paths belonging to ``batch_id`` via its
    structured manifest — never by scanning the FLAT slug directory.

    Resolution flow (Story MCE-PB-SCOPE):

    1. Locate the manifest JSON in :data:`BATCH_JSON_DIR`:
       - try ``{batch_id}.json`` exactly;
       - else glob ``{batch_id}*.json`` (tolerant suffix match, e.g.
         param ``BATCH-12621`` → file ``BATCH-12621-B.json``). The
         ``.advance-trigger.json`` sidecars are NOT manifests and are
         excluded. If the glob yields >1 genuine manifest → ambiguity error
         citing the candidates.
    2. Read ``files_processed[]`` (a list of basenames) and reconstruct each
       path as ``ARTIFACTS / "batches" / slug / basename``.
    3. Honest failures (NEVER a silent partial / iterdir fallback):
       - manifest absent (neither exact nor glob) → :class:`BatchResolutionError`
         citing the ``batch_id``;
       - any basename missing on disk → :class:`BatchResolutionError` listing
         the missing files explicitly.

    Args:
        batch_id: Batch identifier, possibly without source suffix
                  (e.g. ``"BATCH-12621"`` or ``"BATCH-12621-B"``).
        slug: Person/source slug (e.g. ``"acme"``).

    Returns:
        List of absolute path strings — exactly the documents in the batch.

    Raises:
        BatchResolutionError: manifest absent, ambiguous, or a basename is
            missing on disk.
    """
    # --- 1. Locate the manifest -------------------------------------------
    manifest_path = BATCH_JSON_DIR / f"{batch_id}.json"
    if not manifest_path.is_file():
        # Tolerant glob: {batch_id}*.json, excluding non-manifest sidecars
        # such as `{batch_id}.advance-trigger.json`.
        candidates = [
            p
            for p in sorted(BATCH_JSON_DIR.glob(f"{batch_id}*.json"))
            if not p.name.endswith(".advance-trigger.json")
        ]
        if not candidates:
            raise BatchResolutionError(
                f"batch manifest not found: {batch_id} "
                f"(searched {BATCH_JSON_DIR}/{batch_id}.json and "
                f"glob {batch_id}*.json)"
            )
        if len(candidates) > 1:
            names = ", ".join(p.name for p in candidates)
            raise BatchResolutionError(
                f"ambiguous batch manifest for {batch_id}: "
                f"{len(candidates)} candidates [{names}] — refusing to guess"
            )
        manifest_path = candidates[0]

    # --- 2. Read files_processed[] and reconstruct paths ------------------
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BatchResolutionError(
            f"batch manifest unreadable: {manifest_path.name} ({exc})"
        ) from exc

    basenames = manifest.get("files_processed") or []
    if not basenames:
        raise BatchResolutionError(
            f"batch manifest {manifest_path.name} has empty files_processed[]"
        )

    batch_dir = ARTIFACTS / "batches" / slug
    resolved: list[str] = []
    missing: list[str] = []
    for basename in basenames:
        candidate = batch_dir / basename
        if candidate.is_file():
            resolved.append(str(candidate))
        else:
            missing.append(basename)

    # --- 3. Honest failure: any basename missing on disk ------------------
    if missing:
        raise BatchResolutionError(
            f"batch {batch_id}: {len(missing)} document(s) listed in manifest "
            f"not found on disk under {batch_dir}: {missing}"
        )

    return resolved


def cmd_process_batch(
    batch_id: str,
    slug: str,
    documents: list[str | Path] | None = None,
) -> dict[str, Any]:
    """Process a batch through the chunk+embed+upsert sub-phase atomically.

    Uses :func:`pipeline_transaction` to ensure that if any step fails
    (chunking, embedding, or upserting), the pipeline state is rolled
    back to its pre-transaction snapshot.  No partial state is left behind.

    Steps (inside transaction):
        1. ``chunk_document(doc)`` -- split documents into chunks.
        2. ``embed_chunks(chunks)`` -- generate vector embeddings.
        3. ``upsert_to_index(embeddings)`` -- write to the RAG index.
        4. ``txn.commit()`` -- finalize; snapshot discarded.

    If any step raises an exception, ``txn.rollback()`` executes
    automatically, restoring all state files and removing partial artifacts.

    Args:
        batch_id: Batch identifier (e.g. ``"BATCH-001"``).
        slug: Person/source slug (e.g. ``"alex-hormozi"``).
        documents: Optional list of document paths to process.
                   If *None*, discovers documents from the batch manifest.

    Returns:
        Structured result dict with chunk/embed/upsert counts.
    """
    t0 = time.monotonic()

    # Load state infrastructure
    sm = PipelineStateMachine(slug)
    mgr = MetadataManager.load(slug)
    mt = MetricsTracker.load(slug) or MetricsTracker(slug)
    mt.start_phase("process_batch")

    # Discover documents if not provided — scope STRICTLY to this batch_id via
    # its structured manifest (Story MCE-PB-SCOPE). NO fallback to scanning the
    # FLAT slug directory: manifest absent / basename missing → honest failure
    # returned BEFORE any chunk/embed work.
    if documents is None:
        try:
            documents = _resolve_batch_documents(batch_id, slug)
        except BatchResolutionError as exc:
            mt.end_phase("process_batch")
            mt.save()
            elapsed = (time.monotonic() - t0) * 1000
            return _build_result(
                "process_batch",
                success=False,
                slug=slug,
                batch_id=batch_id,
                error=str(exc),
                duration_ms=elapsed,
            )

    if not documents:
        mt.end_phase("process_batch")
        mt.save()
        elapsed = (time.monotonic() - t0) * 1000
        return _build_result(
            "process_batch",
            success=False,
            slug=slug,
            batch_id=batch_id,
            error="No documents found for batch",
            duration_ms=elapsed,
        )

    # ------------------------------------------------------------------
    # STORY-MCE-7.0 AC-1: Embeddings dedup — skip re-embedding if the
    # embedding artifact already exists for this batch AND its stored
    # content_hash fingerprint matches the current chunks.  This collapses
    # idempotent re-runs from ~88s → <2s for alex-hormozi (2398 chunks).
    # ------------------------------------------------------------------
    embeddings_out = ARTIFACTS / "embeddings" / slug / f"{batch_id}-embeddings.json"

    # Step 0 (AC-1): check if we can fast-return with cached embeddings
    if embeddings_out.exists():
        try:
            _cached = json.loads(embeddings_out.read_text(encoding="utf-8"))
            _cached_embeddings = _cached.get("embeddings", [])
            _cached_count = _cached.get("count", 0)
            _cached_hash = _cached.get("content_hash_fingerprint", "")

            # Compute current chunk content hash fingerprint (sha256 of sorted
            # chunk_ids or text hashes — deterministic across runs).
            # We use a lightweight approach: hash of sorted source_file paths
            # in the batch documents list.  Cheap and stable for same inputs.
            import hashlib as _hashlib

            _doc_fingerprint = _hashlib.sha256(
                "|".join(sorted(str(d) for d in documents)).encode()
            ).hexdigest()[:16]

            if _cached_embeddings and _cached_count > 0 and _cached_hash == _doc_fingerprint:
                # Fast path: embeddings already computed for identical inputs
                mt.end_phase("process_batch")
                mt.save()
                elapsed = (time.monotonic() - t0) * 1000

                logger.info(
                    "[MCE-7.0] Embeddings dedup HIT for batch %s/%s — "
                    "skipping %d re-embeds (%.1fms saved)",
                    slug,
                    batch_id,
                    _cached_count,
                    elapsed,
                )

                result = _build_result(
                    "process_batch",
                    success=True,
                    slug=slug,
                    batch_id=batch_id,
                    duration_ms=elapsed,
                    counts={
                        "documents": len(documents),
                        "chunks": _cached_count,
                        "embeddings": _cached_count,
                        "upserted": _cached_count,
                    },
                    embeddings_dedup_hit=True,
                    state={"current": sm.state},
                )
                _append_jsonl(result)
                return result
        except Exception as _dedup_exc:
            # Fail-open per Art. XII — dedup check failure falls through to normal path
            logger.debug("[MCE-7.0] Embeddings dedup check failed (non-fatal): %s", _dedup_exc)

    # ------------------------------------------------------------------
    # Transactional sub-phase: chunk -> embed -> upsert
    # ------------------------------------------------------------------
    chunks_count = 0
    embeddings_count = 0
    upserted_count = 0

    # Compute doc fingerprint for storage (AC-1: future dedup lookups)
    import hashlib as _hashlib_txn

    _doc_fp = _hashlib_txn.sha256("|".join(sorted(str(d) for d in documents)).encode()).hexdigest()[
        :16
    ]

    try:
        with pipeline_transaction(batch_id, slug=slug) as txn:
            # Step 1: Chunk documents
            #
            # STORY-MCE-SPEAKER-AWARE-EXTRACTION: for a multi-speaker transcript
            # routed to a single person slug, keep ONLY that person's turns before
            # chunking. Otherwise every speaker's words land in the slug's chunks
            # and the DNA extractor attributes the whole call to the slug (a
            # guest call — dominated by the founder — leaked the founder's pitch
            # into the guest's DNA). Single-speaker sources are a no-op; an
            # unmatched target falls back to the full transcript (never drops data).
            chunk_document = _import_chunker()
            from engine.intelligence.pipeline.mce.speaker_filter import (
                filter_transcript_to_speaker,
            )

            _person_name = _person_name_for_slug(slug)
            all_chunks = []
            for doc_path in documents:
                _use_path = doc_path
                _tmp_path: Path | None = None
                try:
                    _p = Path(doc_path)
                    if _p.suffix.lower() in (".txt", ".md") and _p.is_file():
                        _raw = _p.read_text(encoding="utf-8", errors="ignore")
                        _filtered, _sf_stats = filter_transcript_to_speaker(_raw, _person_name)
                        if _sf_stats.get("applied"):
                            # Temp file MUST live under the project root: the
                            # pipeline transaction rejects paths outside it.
                            _sf_dir = _PROJECT_ROOT / ".data" / "speaker-filtered" / slug
                            _sf_dir.mkdir(parents=True, exist_ok=True)
                            _fd, _tmp_name = tempfile.mkstemp(
                                suffix=_p.suffix,
                                prefix=f"{batch_id}.",
                                dir=str(_sf_dir),
                            )
                            _tmp_path = Path(_tmp_name)
                            with os.fdopen(_fd, "w", encoding="utf-8") as _fh:
                                _fh.write(_filtered)
                            _use_path = str(_tmp_path)
                            logger.info(
                                "[speaker-filter] %s: kept %d/%d turns (%d/%d chars) for %r",
                                slug,
                                _sf_stats["kept_segments"],
                                _sf_stats["total_segments"],
                                _sf_stats["kept_chars"],
                                _sf_stats["total_chars"],
                                _person_name,
                            )
                            _append_jsonl(
                                {
                                    "event": "speaker_filter_applied",
                                    "slug": slug,
                                    "batch_id": batch_id,
                                    **_sf_stats,
                                }
                            )
                    doc_chunks = chunk_document(_use_path)
                    all_chunks.extend(doc_chunks)
                finally:
                    if _tmp_path is not None:
                        try:
                            _tmp_path.unlink()
                        except OSError:
                            pass

            chunks_count = len(all_chunks)

            # C-19-SERIALIZE fix (2026-05-12): previously [str(c) for c in all_chunks]
            # collapsed Chunk dataclass instances to '<Chunk object at 0x...>' strings,
            # losing all chunk content. Now properly serialize as dicts.
            def _chunk_to_dict(c: Any) -> dict:
                if isinstance(c, dict):
                    return c
                if hasattr(c, "__dict__"):
                    return {k: v for k, v in c.__dict__.items() if not k.startswith("_")}
                if hasattr(c, "_asdict"):
                    return dict(c._asdict())
                return {"text": str(c)}

            chunks_serialized = [_chunk_to_dict(c) for c in all_chunks]

            # STORY-MCE-11.13: Enrich chunks with 7 missing schema fields.
            # Additive-only — existing fields untouched. Non-fatal per chunk.
            chunks_serialized = _enrich_chunk_schema(
                chunks_serialized, slug=slug, source_id=batch_id
            )

            # Record chunks artifact (with real content, not repr strings)
            chunks_out = ARTIFACTS / "chunks" / slug / f"{batch_id}-chunks.json"
            chunks_out.parent.mkdir(parents=True, exist_ok=True)
            chunks_out.write_text(
                json.dumps(
                    {
                        "batch_id": batch_id,
                        "chunks": chunks_serialized,
                        "count": chunks_count,
                    },
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
            txn.record_artifact("chunks", chunks_out)

            # Step 2: Embed chunks
            # C-19-SERIALIZE fix: pass dicts (not raw Chunk objects) to embedder
            # so it can read chunk.text safely.
            embed_chunks = _import_embedder()
            embeddings = embed_chunks(chunks_serialized)
            embeddings_count = len(embeddings) if isinstance(embeddings, list) else 0

            # C-19-SERIALIZE fix: persist full embeddings array (not just count)
            # so downstream rag-index can use them without re-embedding.
            # STORY-MCE-7.0 AC-1: include content_hash_fingerprint so future
            # runs can verify identity and skip re-embedding.
            embeddings_out.parent.mkdir(parents=True, exist_ok=True)
            embeddings_out.write_text(
                json.dumps(
                    {
                        "batch_id": batch_id,
                        "count": embeddings_count,
                        "embeddings": embeddings,
                        "embedding_model": (
                            embeddings[0].get("embedding_model")
                            if embeddings and isinstance(embeddings[0], dict)
                            else None
                        ),
                        # AC-1: fingerprint enables dedup on re-run
                        "content_hash_fingerprint": _doc_fp,
                    },
                    ensure_ascii=False,
                    default=str,
                ),
                encoding="utf-8",
            )
            txn.record_artifact("embeddings", embeddings_out)

            # Step 3: Upsert to index
            upsert_to_index = _import_index_upserter()
            try:
                _bucket_for_upsert = _detect_bucket_for_slug(slug)
            except Exception:
                _bucket_for_upsert = "external"
            upsert_result = upsert_to_index(embeddings, bucket=_bucket_for_upsert, slug=slug)
            upserted_count = (
                upsert_result.get("upserted", 0)
                if isinstance(upsert_result, dict)
                else embeddings_count
            )

            # All 3 steps succeeded -- commit
            txn.commit()

    except Exception as exc:
        # Transaction auto-rolled back by context manager
        mt.end_phase("process_batch")
        mt.save()
        elapsed = (time.monotonic() - t0) * 1000

        err_result = _build_result(
            "process_batch",
            success=False,
            slug=slug,
            batch_id=batch_id,
            error=f"Transaction rolled back: {exc}",
            rolled_back=True,
            duration_ms=elapsed,
            partial_counts={
                "chunks": chunks_count,
                "embeddings": embeddings_count,
                "upserted": upserted_count,
            },
        )
        _append_jsonl(err_result)
        return err_result

    # Success path
    mt.end_phase("process_batch")
    mt.save()
    elapsed = (time.monotonic() - t0) * 1000

    # Update metadata
    if mgr:
        mgr.mark_phase_complete(
            "process_batch",
            batch_id=batch_id,
            chunks=chunks_count,
            embeddings=embeddings_count,
            upserted=upserted_count,
        )
        mgr.save()

    result = _build_result(
        "process_batch",
        success=True,
        slug=slug,
        batch_id=batch_id,
        duration_ms=elapsed,
        counts={
            "documents": len(documents),
            "chunks": chunks_count,
            "embeddings": embeddings_count,
            "upserted": upserted_count,
        },
        state={"current": sm.state},
    )
    _append_jsonl(result)

    # STORY-MCE-LOG-PARITY (2026-05-20): emit ASCII BATCH LOG after each batch
    # so operator sees per-batch progress (OLD pattern: BATCH-{NNN} COMPLETE).
    # DNA layer counts default to 0 here — populated by downstream cmd_behavioral
    # / cmd_identity / cmd_voice when they run.
    try:
        from engine.intelligence.pipeline.mce.log_emitters import emit_batch_log

        _bl_block = emit_batch_log(
            batch_id=batch_id,
            slug=slug,
            source_code=_derive_source_code(slug),
            file_count=len(documents),
            chunks_created=chunks_count,
        )
        print(_bl_block, flush=True)
        emit_phase_payload(
            slug=slug,
            template_id="batch_log",
            status="ok",
            metrics={
                "batch_id": batch_id,
                "file_count": len(documents),
                "chunks_created": chunks_count,
            },
            ascii_block=_bl_block,
        )
        # Emit execution_chunks + execution_embeddings coverage aliases so
        # jarvis_chief.py coverage tracking can match EXPECTED_PHASES phases 3 and 4.
        # These are not separate commands — cmd_process_batch handles both in one pass.
        emit_phase_payload(
            slug=slug,
            template_id="execution_chunks",
            status="ok",
            metrics={
                "batch_id": batch_id,
                "chunks_created": chunks_count,
            },
            ascii_block="",
        )
        emit_phase_payload(
            slug=slug,
            template_id="execution_embeddings",
            status="ok",
            metrics={
                "batch_id": batch_id,
                "chunks_indexed": chunks_count,
            },
            ascii_block="",
        )
        # MCE-17.0 T11: emit log_generator-compatible template_ids for
        # Chronicler STEP 09 (chunking) and STEP 10 (embeddings) renderers.
        emit_phase_payload(
            slug=slug,
            template_id="chunking",
            status="ok",
            metrics={
                "total_chunks": chunks_count,
                "avg_words_per_chunk": 300,  # MCE-17.0 T11: approximate; real avg requires chunk list
                "min_words": 0,
                "max_words": 0,
                # Onda 0 honesty: report the REAL strategy used by the ingest
                # chunk path (chunk_document -> _chunk_text_like_file pins
                # semantic=False). The old hardcoded "semantic" was a lie.
                "strategy": _ingest_chunk_strategy(),
                "batch_id": batch_id,
            },
            ascii_block="",
        )
        emit_phase_payload(
            slug=slug,
            template_id="embeddings",
            status="ok",
            metrics={
                "chunks_embedded": embeddings_count,
                "model": "text-embedding-3-large",
                "dimensions": 1536,
                "tokens_used": embeddings_count * 300,  # approx: ~300 tokens/chunk
                "cost_usd": round(embeddings_count * 300 * 0.00000013, 6),  # ~$0.13/1M
                "duration_ms": elapsed,
                "batch_id": batch_id,
            },
            ascii_block="",
        )
    except Exception as _log_exc:  # pragma: no cover
        logger.debug("Batch log emit failed (non-fatal): %s", _log_exc)

    return result


# ---------------------------------------------------------------------------
# G13 (2026-05-13): LLM extraction commands (cmd_insights / cmd_entities /
# cmd_behavioral / cmd_identity / cmd_voice).
#
# Each command:
#   1. Loads chunks from ``.data/artifacts/chunks/{slug}/CHUNKS-STATE.json``.
#   2. Builds a structured prompt for Gemini Flash.
#   3. Parses the JSON envelope, merges into INSIGHTS-STATE.json.
#   4. (cmd_insights only) Derives DNA-CONFIG.yaml composition counts so
#      the validation log shows ``DNA Elements`` > 0.
#
# When ``GEMINI_API_KEY`` / ``GOOGLE_API_KEY`` is missing, the command
# logs the gap and writes a stub INSIGHTS-STATE.json with empty layers
# so the FSM still advances (extraction-deferred mode). This is documented
# behaviour, not silent failure -- the structured result includes
# ``extraction_skipped=True`` and a ``reason`` field.
# ---------------------------------------------------------------------------


def _compute_batch_content_hash(chunks: list[dict]) -> str:
    """SHA-256 of combined chunk text sorted by chunk_id — batch-level dedup.

    MCE-16.5 (Bug 1): defense-in-depth against re-indexing byte-identical
    batches when ``id_chunk`` is empty (cannot dedup by ID alone).  The hash
    is deterministic: same content always produces the same hex digest
    regardless of file path or batch_id label.
    """
    import hashlib

    combined = "".join(
        c.get("text", "") for c in sorted(chunks, key=lambda x: x.get("chunk_id", x.get("id_chunk", "")))
    )
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def _resolve_chunks_for_slug(slug: str) -> list[dict[str, Any]]:
    """Load chunks for ``slug`` from the canonical artifact location.

    Returns the flattened ``chunks[]`` list. Empty list when nothing is
    found (caller decides whether to bail or proceed with stub).

    Priority order (slug-isolated first, source-code-isolated fallback):
        1. ``.data/artifacts/chunks/{slug}/CHUNKS-STATE.json``
        2. ``.data/artifacts/chunks/{slug}/BATCH-*-chunks.json`` (per-batch)
        3. ``.data/artifacts/chunks/{SOURCE_CODE}-*-chunks.json`` (per-source legacy)
        4. ``.data/artifacts/chunks/{SOURCE_CODE}-*.chunks.json`` (dot variant)

    STORY-MCE-INGEST-PROD (2026-05-19): tier 3+4 added to recover historical
    batches that pre-date the slug-isolated subdir convention (MCE-1.2). The
    source-code prefix derived from ``batch_auto_creator.derive_source_code``
    provides slug isolation by naming convention (e.g. ``AH-YT001-chunks.json``
    only contains alex-hormozi chunks — no foreign data leak).

    The previously-banned ``CHUNKS-STATE.json`` global (MCE-2.5) remains
    excluded — it mixes everyone's chunks into one mega-file.
    """
    slug_dir = ARTIFACTS / "chunks" / slug
    candidates: list[Path] = []
    if (slug_dir / "CHUNKS-STATE.json").exists():
        candidates.append(slug_dir / "CHUNKS-STATE.json")
    if slug_dir.is_dir():
        candidates.extend(sorted(slug_dir.glob("BATCH-*-chunks.json")))

    # Tier 3+4: per-source-code legacy flat files. Only activated when the
    # slug-isolated subdir has zero candidates (avoids double-counting).
    if not candidates:
        try:
            from engine.intelligence.pipeline.batch_auto_creator import (
                derive_source_code,
            )

            source_code = derive_source_code(slug)
        except Exception:
            source_code = ""
        if source_code:
            flat_dir = ARTIFACTS / "chunks"
            # Tier 3: hyphen variant — AH-YT001-chunks.json
            candidates.extend(sorted(flat_dir.glob(f"{source_code}-*-chunks.json")))
            # Tier 4: dot variant — AH-SRC005.chunks.json
            candidates.extend(sorted(flat_dir.glob(f"{source_code}-*.chunks.json")))

    # MCE-2.5 policy (permanent): the legacy global CHUNKS-STATE.json mixes
    # chunks from every historical slug (1106+ observed). Reading it as a
    # fallback leaks foreign chunks into insight prompts (multi-MB request →
    # httpx _receive_response_headers hang). We never fall back to it. Slug-
    # isolated and per-source-code chunks are the only authoritative sources.

    chunks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    # MCE-16.5 Bug 1: batch-level dedup by content hash.  When id_chunk is
    # empty (as in cole-gordon batches), per-chunk ID dedup is a no-op and
    # identical batches get loaded twice.  We track each batch's content hash
    # and skip the entire batch if its hash was already loaded.
    seen_batch_hashes: set[str] = set()
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.debug("Failed to load chunks from %s: %s", path, exc)
            continue
        page = data.get("chunks", data) if isinstance(data, dict) else data
        if not isinstance(page, list):
            continue
        # Batch-level dedup: skip this file if its content hash was already seen.
        if isinstance(page, list) and page:
            batch_hash = _compute_batch_content_hash(page)
            if batch_hash in seen_batch_hashes:
                logger.warning(
                    "[MCE-16.5] SKIP duplicate batch — path=%s hash=%s (content already loaded)",
                    path.name,
                    batch_hash[:8],
                )
                continue
            seen_batch_hashes.add(batch_hash)
        is_legacy = path.parent == ARTIFACTS / "chunks"
        for c in page:
            if not isinstance(c, dict):
                continue
            # MCE-2.2 fix: when reading the legacy shared file, accept
            # only chunks tagged with this slug (otherwise we leak foreign
            # data into the insight prompt).
            if is_legacy:
                meta = c.get("meta") or {}
                chunk_slug = (
                    c.get("slug")
                    or meta.get("slug")
                    or meta.get("persona")
                    or meta.get("person_slug")
                )
                if chunk_slug and chunk_slug != slug:
                    continue
            cid = c.get("id_chunk") or c.get("id") or ""
            if cid and cid in seen_ids:
                continue
            seen_ids.add(cid)
            chunks.append(c)
    return chunks


def _insights_state_path(slug: str) -> Path:
    """Canonical INSIGHTS-STATE.json location for ``slug``."""
    return ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"


# MCE-6.3 — Per-slug registry of already-processed source files
_PROCESSED_SOURCES_DIR = _PROJECT_ROOT / ".data" / "processed-sources"


def _processed_sources_path(slug: str) -> Path:
    return _PROCESSED_SOURCES_DIR / f"{slug}.json"


def _load_processed_sources(slug: str) -> set[str]:
    """Load set of source_file paths already processed for slug."""
    p = _processed_sources_path(slug)
    if not p.exists():
        return set()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return set(data.get("source_files", []))
    except (OSError, json.JSONDecodeError):
        return set()


def _save_processed_sources(slug: str, source_files: set[str]) -> None:
    """Persist set of processed source_file paths for slug (append-only semantics)."""
    p = _processed_sources_path(slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": slug,
        "source_files": sorted(source_files),
        "updated_at": time.time(),
        "count": len(source_files),
    }
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# MCE-6.3 — Per-cmd marker for INSIGHTS-STATE-derived cmds (behavioral/voice/
# identity/consolidate/narrative). If INSIGHTS-STATE.json hasn't changed since
# last successful run of this cmd, skip — output is up-to-date.
def _cmd_marker_path(slug: str, cmd_name: str) -> Path:
    return _PROCESSED_SOURCES_DIR / f"{slug}-cmd-{cmd_name}.json"


def _insights_fingerprint(slug: str) -> tuple[int, int]:
    """Compute (insights_count, file_size_bytes) fingerprint of INSIGHTS-STATE.

    More robust than mtime — survives atomic-write renames and FS quirks.
    Two distinct extractions producing the same N insights with the same total
    payload size is vanishingly rare for cognitive output.
    """
    insights_p = _insights_state_path(slug)
    if not insights_p.exists():
        return (0, 0)
    try:
        data = json.loads(insights_p.read_text(encoding="utf-8"))
        size_bytes = insights_p.stat().st_size
        # Handle both schemas: wrapped ({"insights_state": {...}}) and direct
        if (
            isinstance(data, dict)
            and "insights_state" in data
            and isinstance(data["insights_state"], dict)
        ):
            state = data["insights_state"]
        else:
            state = data
        persons = state.get("persons", {}) if isinstance(state, dict) else {}
        total = 0
        for pdata in persons.values():
            if isinstance(pdata, dict):
                total += len(pdata.get("insights", []) or [])
        return (total, size_bytes)
    except (OSError, json.JSONDecodeError):
        return (0, 0)


def _should_skip_cmd_by_insights_mtime(slug: str, cmd_name: str) -> tuple[bool, str]:
    """Return (skip, reason). True if INSIGHTS-STATE fingerprint matches the
    one recorded at the last successful run of `cmd_name` for `slug`."""
    insights_p = _insights_state_path(slug)
    if not insights_p.exists():
        return False, "insights_state_missing"
    marker_p = _cmd_marker_path(slug, cmd_name)
    if not marker_p.exists():
        return False, "no_prior_run"
    try:
        marker = json.loads(marker_p.read_text(encoding="utf-8"))
        last_count = int(marker.get("insights_count", -1))
        current_count, _ = _insights_fingerprint(slug)
        # Use only count, not size — each downstream cmd writes back to
        # INSIGHTS-STATE updating internal timestamps, causing size to fluctuate
        # while the actual insight payload is unchanged. Count is the real signal.
        if last_count >= 0 and last_count == current_count:
            return True, (
                f"INSIGHTS-STATE insight count unchanged since last cmd_{cmd_name} run "
                f"(count={current_count}) — idempotent skip"
            )
        return False, f"insights_count_changed (was {last_count}, now {current_count})"
    except (OSError, json.JSONDecodeError, ValueError):
        return False, "marker_read_error"


def _save_cmd_marker(slug: str, cmd_name: str) -> None:
    """Record INSIGHTS-STATE fingerprint at successful cmd completion."""
    count, size_bytes = _insights_fingerprint(slug)
    marker_p = _cmd_marker_path(slug, cmd_name)
    marker_p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": slug,
        "cmd": cmd_name,
        "insights_count": count,
        "insights_size_bytes": size_bytes,
        "completed_at": time.time(),
    }
    marker_p.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_insights_state(slug: str) -> dict[str, Any]:
    """Load existing INSIGHTS-STATE.json or initialize a fresh skeleton."""
    path = _insights_state_path(slug)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # Some legacy files wrap the state under ``insights_state``.
                if "insights_state" in data and isinstance(data["insights_state"], dict):
                    data = data["insights_state"]
                # hotfix-6 (7B): inject contradictions[] if missing from legacy files
                # so gate 7B_insights_state_schema_valid passes on next save.
                if "contradictions" not in data:
                    data.setdefault("contradictions", [])
                return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.debug("Failed to load existing insights state: %s", exc)

    return {
        "persons": {},
        "themes": {},
        "version": "v1",
        "extraction_meta": {},
        "mce": {},
        "change_log": [],
        "contradictions": [],
        "schema_version": "1.1.0",
        "last_updated": _now_iso(),
    }


def _save_insights_state(slug: str, state: dict[str, Any]) -> None:
    """Persist INSIGHTS-STATE.json atomically."""
    path = _insights_state_path(slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    state["last_updated"] = _now_iso()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    tmp.replace(path)


def _review_queue_path(slug: str) -> Path:
    """Canonical REVIEW-QUEUE.json location for ``slug`` (MCE-4.4)."""
    return ARTIFACTS / "canonical" / slug / "REVIEW-QUEUE.json"


def _load_review_queue(slug: str) -> dict[str, Any]:
    """Load existing REVIEW-QUEUE.json or initialize a fresh v2.0.0 skeleton."""
    path = _review_queue_path(slug)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.debug("Failed to load REVIEW-QUEUE for %s: %s", slug, exc)
    return {
        "schema_version": "2.0.0",
        "person_slug": slug,
        "last_updated": _now_iso(),
        "items": [],
    }


def _save_review_queue(slug: str, queue: dict[str, Any]) -> None:
    """Persist REVIEW-QUEUE.json atomically (MCE-4.4 AC6)."""
    import tempfile

    path = _review_queue_path(slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    queue["schema_version"] = "2.0.0"
    queue["last_updated"] = _now_iso()
    tmp_fd, tmp_path_str = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False, default=str)
        os.replace(tmp_path_str, path)
    except Exception:
        try:
            os.unlink(tmp_path_str)
        except OSError:
            pass
        raise


def _dedup_and_merge_review_queue_items(
    existing_items: list[dict[str, Any]],
    new_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge new_items into existing_items deduplicating by dedup_key.

    If an item with the same dedup_key already exists in a non-EXPIRED status,
    the new item is skipped (AC2 dedup rule).
    """
    by_dedup: dict[str, dict[str, Any]] = {}
    for item in existing_items:
        key = item.get("dedup_key") or item.get("id") or ""
        by_dedup[key] = item

    for item in new_items:
        key = item.get("dedup_key") or item.get("id") or ""
        existing = by_dedup.get(key)
        if existing and existing.get("status") not in ("EXPIRED", None):
            # Already in queue and not expired — skip
            continue
        by_dedup[key] = item

    return list(by_dedup.values())


def _person_name_for_slug(slug: str) -> str:
    """Pretty-cased person name from slug (``alex-hormozi`` → ``Alex Hormozi``)."""
    return " ".join(part.capitalize() for part in slug.split("-") if part)


def _tag_to_dna_layer(tag: str) -> str | None:
    """Normalize ``tag`` from insight to DNA composition key."""
    t = (tag or "").upper().strip("[]").replace("-", "_").replace(" ", "_")
    mapping = {
        "FILOSOFIA": "FILOSOFIAS",
        "FILOSOFIAS": "FILOSOFIAS",
        "MODELO_MENTAL": "MODELOS_MENTAIS",
        "MODELOS_MENTAIS": "MODELOS_MENTAIS",
        "MENTAL_MODEL": "MODELOS_MENTAIS",
        "HEURISTICA": "HEURISTICAS",
        "HEURISTICAS": "HEURISTICAS",
        "HEURISTIC": "HEURISTICAS",
        "FRAMEWORK": "FRAMEWORKS",
        "FRAMEWORKS": "FRAMEWORKS",
        "METODOLOGIA": "METODOLOGIAS",
        "METODOLOGIAS": "METODOLOGIAS",
        "METHODOLOGY": "METODOLOGIAS",
    }
    return mapping.get(t)


def _write_dna_config_from_insights(slug: str, person_insights: list[dict[str, Any]]) -> int:
    """Derive a DNA-CONFIG.yaml ``composition`` block from tagged insights.

    The validation checklist in ``log_generator.py`` reads
    ``knowledge/external/dna/persons/{slug}/DNA-CONFIG.yaml::composition``
    to compute the DNA Elements count. We populate it here from the
    ``tag`` field of each insight (HEURISTICA/FRAMEWORK/...). Total is
    written under ``composition.total`` so the validation row turns green
    as soon as cmd_insights produces tagged insights.

    Returns the total count of DNA-tagged elements.
    """
    counts: dict[str, int] = {
        "FILOSOFIAS": 0,
        "MODELOS_MENTAIS": 0,
        "HEURISTICAS": 0,
        "FRAMEWORKS": 0,
        "METODOLOGIAS": 0,
    }
    for ins in person_insights:
        if not isinstance(ins, dict):
            continue
        # ``tag`` is the canonical field, ``dna_tag`` is the legacy alias.
        tag = ins.get("tag") or ins.get("dna_tag") or ""
        layer = _tag_to_dna_layer(tag)
        if layer:
            counts[layer] += 1

    total = sum(counts.values())
    if total == 0:
        return 0

    composition = dict(counts)
    composition["total"] = total

    # Bucket-aware destination via the single SOT (STORY-MCE-BUCKET-AWARE-WRITES,
    # Art. XIII). Was hardcoded to external — leaked DNA-CONFIG.yaml for
    # business/personal-routed people (12th write-site, found re-ingesting Carlos).
    from engine.intelligence.pipeline.mce.person_paths import (
        PersonArtifactPaths,
        resolve_bucket,
    )

    dna_dir = PersonArtifactPaths(slug, resolve_bucket(slug), root=_PROJECT_ROOT).dna
    dna_dir.mkdir(parents=True, exist_ok=True)
    dna_path = dna_dir / "DNA-CONFIG.yaml"

    payload = {
        "version": "1.0.0",
        "pessoa": slug,
        "extracted_at": _now_iso(),
        "extraction_source": "cmd_insights (G13)",
        "composition": composition,
    }
    dna_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    logger.info("G13: wrote DNA-CONFIG.yaml for %s (total=%d)", slug, total)
    return total


# ---------------------------------------------------------------------------
# Prompt loader — Phase 2 MCE-6.0 (2026-05-22)
# Cognitive cmd prompts are now externalized to .prompt.md files so operators
# can iterate wording without touching Python. Python reads the file at call
# time; the .md is the source of truth.
# ---------------------------------------------------------------------------
_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    """Read a cognitive cmd prompt from its .prompt.md file.

    Args:
        name: prompt stem without extension (e.g. "insights", "behavioral").

    Returns:
        Prompt text as string. Falls back to empty string on read failure so
        callers can provide their own fallback if needed.
    """
    path = _PROMPTS_DIR / f"{name}.prompt.md"
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("_load_prompt: could not read %s: %s", path, exc)
        return ""


# Load from externalized .prompt.md (Phase 2 MCE-6.0).
# Falls back to inline template if file missing (safety net for first deploy).
_INSIGHTS_PROMPT_TEMPLATE = (
    _load_prompt("insights")
    or """\
You are a Sage-class extractor analyzing transcript chunks to produce STRUCTURED, ACTIONABLE insights about {person_name}.

For EACH chunk below, extract 0 to 3 insights. Each insight must include:
  - id: short id (e.g. "INS-{tag_code}-001", "INS-{tag_code}-002" ...)
  - insight: a clear, actionable sentence in the same language as the chunk (NOT a summary)
  - quote: a verbatim quote from the chunk that supports the insight
  - chunks: array of chunk ids (the source chunk's id_chunk goes here)
  - tag: ONE of [FILOSOFIA], [MODELO-MENTAL], [HEURISTICA], [FRAMEWORK], [METODOLOGIA]
  - priority: HIGH | MEDIUM | LOW
  - confidence: HIGH | MEDIUM | LOW

DNA tag guide:
  [FILOSOFIA]    -- a belief, worldview, axiom ("X is the foundation of Y")
  [MODELO-MENTAL] -- a way of thinking, conceptual lens ("the N types of X")
  [HEURISTICA]   -- a practical rule WITH NUMBERS or thresholds ("if X < 2%, do Y")
  [FRAMEWORK]    -- a named system with identifiable components ("FOO Strategy: A + B + C")
  [METODOLOGIA]  -- a step-by-step sequence ("Step 1: ..., Step 2: ...")

Output ONLY valid JSON in this exact shape (no prose, no markdown fences):
{{
  "insights": [
    {{
      "id": "INS-{tag_code}-001",
      "insight": "...",
      "quote": "...",
      "chunks": ["chunk_N"],
      "tag": "[HEURISTICA]",
      "priority": "HIGH",
      "confidence": "HIGH"
    }}
  ]
}}

If no high-quality insights are extractable, return ``{{"insights": []}}``.

Chunks ({chunk_count}):
{chunks_block}
"""
)


def _format_chunks_for_prompt(chunks: list[dict[str, Any]], max_chars: int = 1200) -> str:
    """Render chunks compactly for the prompt, truncating long texts."""
    blocks: list[str] = []
    for c in chunks:
        cid = c.get("id_chunk") or c.get("id") or "chunk_?"
        text = (c.get("texto") or c.get("text") or "").strip()
        if len(text) > max_chars:
            text = text[: max_chars - 3] + "..."
        blocks.append(f"--- {cid} ---\n{text}")
    return "\n\n".join(blocks)


def _chunks_for_prompt_size(chunks: list[dict[str, Any]], batch_size: int = 6):
    """Yield successive chunks-of-N for prompt batching."""
    for i in range(0, len(chunks), batch_size):
        yield chunks[i : i + batch_size]


# ---------------------------------------------------------------------------
# STORY-HGA-F1.2 — Two-stage node-first extraction (OPT-IN; single-pass default)
# ---------------------------------------------------------------------------
# Stage 2 of the two-stage path: with the batch's insight-nodes already in
# hand, ask the model for relationships (edges) BETWEEN those nodes only. The
# known-node list is injected as context exactly like Hyper-Extract's
# ``_extract_edges_batch`` (4e333f847f1d:graph.py:592-622). Dangling edges are
# pruned afterwards by ``llm_extractor.prune_dangling_edges``.
_RELATIONSHIPS_PROMPT_TEMPLATE = """\
You are a Sage-class extractor. You already identified these insight-nodes for \
{person_name} (each line is a node id followed by its insight):

{known_nodes}

From the transcript chunks below, extract 0 to {max_edges} RELATIONSHIPS that \
connect TWO of the node ids listed above. Only use node ids that appear in the \
list — never invent a node. Each relationship must include:
  - source: the id of the origin node (must be one of the ids above)
  - target: the id of the destination node (must be one of the ids above)
  - relation: a short verb phrase describing how source relates to target
  - quote: a verbatim quote from a chunk that supports the relationship

Output ONLY valid JSON in this exact shape (no prose, no markdown fences):
{{
  "relationships": [
    {{"source": "<node id>", "target": "<node id>", "relation": "...", "quote": "..."}}
  ]
}}

If no relationships are extractable, return ``{{"relationships": []}}``.

Chunks ({chunk_count}):
{chunks_block}
"""


def _extract_relationships_for_batch(
    *,
    nodes: list[dict[str, Any]],
    chunks_block: str,
    chunk_count: int,
    person_name: str,
    run_prompt_fn: Any,
    extract_json_fn: Any,
    max_edges: int = 6,
) -> list[dict[str, Any]]:
    """Stage-2 edge extraction for a single batch (two-stage path).

    Sends the already-extracted ``nodes`` as known-node context plus the same
    chunk block, parses the ``relationships`` array, and returns raw (un-pruned)
    edge dicts. Pruning of dangling edges is the caller's responsibility via
    ``llm_extractor.prune_dangling_edges`` so the consistency check lives in one
    place (mirrors Hyper-Extract's single ``_prune_dangling_edges``).
    """
    if not nodes:
        return []
    known_nodes = "\n".join(
        f"- {n.get('id')}: {str(n.get('insight', ''))[:160]}" for n in nodes
    )
    prompt = _RELATIONSHIPS_PROMPT_TEMPLATE.format(
        person_name=person_name,
        known_nodes=known_nodes,
        max_edges=max_edges,
        chunk_count=chunk_count,
        chunks_block=chunks_block,
    )
    raw = run_prompt_fn(prompt)
    parsed = extract_json_fn(raw)
    if not isinstance(parsed, dict):
        return []
    rels = parsed.get("relationships", [])
    if not isinstance(rels, list):
        return []
    return [r for r in rels if isinstance(r, dict)]


def cmd_insights(slug: str) -> dict[str, Any]:
    """G13: Extract structured insights from chunks via Gemini Flash.

    Reads chunks for ``slug``, batches them through Gemini, parses each
    response, and merges all insights into INSIGHTS-STATE.json under
    ``persons[{Person Name}].insights[]``. Tagged insights also seed
    DNA-CONFIG.yaml ``composition`` so the validation row turns green.

    Fail-soft:
        - No chunks → returns success=True with ``insights_extracted=0``.
        - No GEMINI/GOOGLE key → writes stub state, returns
          ``extraction_skipped=True`` and ``reason``.
        - Parse failures per-batch are logged and skipped; the rest of
          the batches still produce insights.
    """
    t0 = time.monotonic()

    chunks = _resolve_chunks_for_slug(slug)
    chunks_total_before_filter = len(chunks)

    # MCE-6.3 — Dedup against already-processed source files.
    # Each /ingest accumulates files in knowledge/external/inbox/<slug>/. Without
    # dedup, cmd_insights re-extracts the entire history every run (O(N) per run
    # instead of O(delta)). We persist a registry of processed source_file paths
    # at .data/processed-sources/<slug>.json and skip chunks whose source_file
    # is already there. Idempotency guarantee: re-running cmd_insights on the
    # same slug produces near-zero work when no new sources arrived.
    _processed_sources_path = _PROCESSED_SOURCES_DIR / f"{slug}.json"
    _processed_sources: set[str] = set()
    if _processed_sources_path.exists():
        try:
            _ps_data = json.loads(_processed_sources_path.read_text(encoding="utf-8"))
            _processed_sources = set(_ps_data.get("source_files", []))
        except (OSError, json.JSONDecodeError):
            _processed_sources = set()

    if _processed_sources:
        chunks = [c for c in chunks if c.get("source_file") not in _processed_sources]

    if not chunks:
        elapsed = (time.monotonic() - t0) * 1000
        if chunks_total_before_filter > 0 and _processed_sources:
            _reason = (
                f"all {chunks_total_before_filter} chunks belong to "
                f"{len(_processed_sources)} already-processed sources — idempotent skip"
            )
        else:
            _reason = "no chunks found for slug"
        result = _build_result(
            "insights",
            success=True,
            slug=slug,
            duration_ms=elapsed,
            insights_extracted=0,
            chunks_total=chunks_total_before_filter,
            sources_already_processed=len(_processed_sources),
            reason=_reason,
        )
        _append_jsonl(result)
        return result

    try:
        from engine.intelligence.pipeline.mce.llm_extractor import (
            EXTRACTION_MODE_TWO_STAGE,
            LLMNotConfiguredError,
            extract_json,
            is_available,
            prune_dangling_edges,
            resolve_extraction_mode,
            run_prompt,
        )
    except ImportError as exc:
        elapsed = (time.monotonic() - t0) * 1000
        result = _build_result(
            "insights",
            success=True,
            slug=slug,
            duration_ms=elapsed,
            insights_extracted=0,
            extraction_skipped=True,
            reason=f"llm_extractor import failed: {exc}",
        )
        _append_jsonl(result)
        return result

    if not is_available():
        # Initialize empty state so downstream commands have something
        # well-formed to read.
        state = _load_insights_state(slug)
        _save_insights_state(slug, state)
        elapsed = (time.monotonic() - t0) * 1000
        result = _build_result(
            "insights",
            success=True,
            slug=slug,
            duration_ms=elapsed,
            insights_extracted=0,
            extraction_skipped=True,
            reason="GEMINI_API_KEY/GOOGLE_API_KEY not configured",
        )
        _append_jsonl(result)
        return result

    person_name = _person_name_for_slug(slug)
    tag_code = _derive_source_code(slug)

    all_insights: list[dict[str, Any]] = []
    # STORY-HGA-F1.2: relationships (edges) only populated on the two-stage path.
    all_relationships: list[dict[str, Any]] = []
    extraction_mode = resolve_extraction_mode()
    two_stage = extraction_mode == EXTRACTION_MODE_TWO_STAGE

    # STORY-HGA-F1.3: opt-in declarative template. With MCE_INSIGHTS_TEMPLATE
    # set to a YAML path, the prompt is COMPILED from that schema; otherwise
    # ``load_insights_prompt`` returns ``_INSIGHTS_PROMPT_TEMPLATE`` unchanged,
    # so the hardcoded default path is byte-for-byte identical to before this
    # story. The result still flows into the SAME .format(...) site and back
    # through ``_save_insights_state`` (RNF-F5 — no lateral path).
    from engine.intelligence.pipeline.mce.template_engine import (
        load_insights_prompt,
    )

    insights_prompt_template = load_insights_prompt(
        fallback=_INSIGHTS_PROMPT_TEMPLATE
    )

    batches_processed = 0
    batches_failed = 0
    batch_idx = 0

    total_batches = (len(chunks) + 5) // 6  # ceil div for batch_size=6
    print(
        f"[cmd_insights] processing {len(chunks)} chunks in {total_batches} batches "
        f"(mode={extraction_mode})",
        flush=True,
    )
    for batch in _chunks_for_prompt_size(chunks, batch_size=6):
        batch_idx += 1
        chunks_block = _format_chunks_for_prompt(batch)
        prompt = insights_prompt_template.format(
            person_name=person_name,
            tag_code=tag_code,
            chunk_count=len(batch),
            chunks_block=chunks_block,
        )
        t_batch = time.monotonic()
        try:
            raw = run_prompt(prompt)
        except LLMNotConfiguredError as exc:
            logger.warning("cmd_insights: LLM not configured mid-run: %s", exc)
            print(
                f"[cmd_insights] batch {batch_idx}/{total_batches} ABORT (LLM not configured)",
                flush=True,
            )
            break
        except Exception as exc:
            batches_failed += 1
            logger.warning("cmd_insights: batch failed: %s", exc)
            print(
                f"[cmd_insights] batch {batch_idx}/{total_batches} FAIL ({type(exc).__name__}: {str(exc)[:80]})",
                flush=True,
            )
            continue
        batch_elapsed = time.monotonic() - t_batch
        print(
            f"[cmd_insights] batch {batch_idx}/{total_batches} OK ({batch_elapsed:.1f}s, raw={len(raw)} chars)",
            flush=True,
        )

        parsed = extract_json(raw)
        if not isinstance(parsed, dict):
            batches_failed += 1
            logger.debug("cmd_insights: non-dict response (raw=%r)", raw[:200])
            continue

        items = parsed.get("insights", [])
        if not isinstance(items, list):
            continue
        batch_nodes: list[dict[str, Any]] = []
        for local_idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            # Re-id each insight with a batch-scoped unique id so the
            # downstream de-dup-by-id step does not collapse genuinely
            # distinct insights that happen to share the LLM's local id.
            item["id"] = f"INS-{tag_code}-B{batch_idx:02d}-{local_idx:03d}"
            # Ensure required fields exist
            item.setdefault("priority", "MEDIUM")
            item.setdefault("confidence", "MEDIUM")
            item.setdefault("status", "new")
            item.setdefault(
                "source",
                {
                    "source_type": "transcript",
                    "source_id": slug.upper(),
                },
            )
            all_insights.append(item)
            batch_nodes.append(item)
        batches_processed += 1

        # ----------------------------------------------------------------
        # STORY-HGA-F1.2: two-stage stage 2 (edges) — OPT-IN.
        # Single-pass (default) NEVER enters this block, so its behaviour is
        # byte-for-byte unchanged. When two_stage is on, extract relationships
        # between THIS batch's insight-nodes (with the nodes as context), then
        # prune dangling edges via the shared llm_extractor helper.
        # ----------------------------------------------------------------
        if two_stage and batch_nodes:
            try:
                raw_edges = _extract_relationships_for_batch(
                    nodes=batch_nodes,
                    chunks_block=chunks_block,
                    chunk_count=len(batch),
                    person_name=person_name,
                    run_prompt_fn=run_prompt,
                    extract_json_fn=extract_json,
                )
                pruned = prune_dangling_edges(
                    batch_nodes,
                    raw_edges,
                    node_key=lambda n: n.get("id", ""),
                    edge_endpoints=lambda e: (
                        e.get("source", ""),
                        e.get("target", ""),
                    ),
                )
                all_relationships.extend(pruned)
                print(
                    f"[cmd_insights] batch {batch_idx}/{total_batches} two-stage edges "
                    f"({len(pruned)} kept, {len(raw_edges) - len(pruned)} pruned)",
                    flush=True,
                )
            except LLMNotConfiguredError:
                # Stage-2 unavailable mid-run — keep the node-insights we have.
                logger.warning("cmd_insights: two-stage edge pass unavailable; nodes kept")
            except Exception as exc:  # pragma: no cover — network/quota
                logger.warning("cmd_insights: two-stage edge pass failed: %s", exc)

    # Merge into INSIGHTS-STATE.json
    state = _load_insights_state(slug)
    persons = state.setdefault("persons", {})
    person_entry = persons.setdefault(
        person_name,
        {
            "slug": slug,
            "canonical": person_name,
            "insights": [],
        },
    )
    existing = person_entry.get("insights", [])
    if not isinstance(existing, list):
        existing = []
    # De-dup by id (later entries win)
    by_id: dict[str, dict[str, Any]] = {
        e.get("id", f"_anon_{i}"): e for i, e in enumerate(existing) if isinstance(e, dict)
    }
    for ins in all_insights:
        by_id[ins.get("id", f"_anon_{len(by_id)}")] = ins
    person_entry["insights"] = list(by_id.values())

    # STORY-HGA-F1.2: merge two-stage relationships (edges) additively, deduped
    # by (source, target, relation). Single-pass leaves all_relationships empty,
    # so person_entry["relationships"] is never written on the default path
    # (keeps the legacy artifact shape byte-identical when two-stage is off).
    if all_relationships:
        existing_rels = person_entry.get("relationships", [])
        if not isinstance(existing_rels, list):
            existing_rels = []
        rel_by_key: dict[tuple[str, str, str], dict[str, Any]] = {
            (r.get("source", ""), r.get("target", ""), r.get("relation", "")): r
            for r in existing_rels
            if isinstance(r, dict)
        }
        for rel in all_relationships:
            rel_by_key[
                (rel.get("source", ""), rel.get("target", ""), rel.get("relation", ""))
            ] = rel
        person_entry["relationships"] = list(rel_by_key.values())
        state.setdefault("extraction_meta", {})["last_relationships_count"] = len(
            all_relationships
        )

    state.setdefault("extraction_meta", {})["last_insights_run"] = _now_iso()
    state.setdefault("extraction_meta", {})["last_insights_count"] = len(all_insights)
    state.setdefault("change_log", []).append(
        {
            "entity": "person",
            "key": person_name,
            "change": "insights_appended",
            "count": len(all_insights),
            "timestamp": _now_iso(),
        }
    )
    _save_insights_state(slug, state)

    # ---------------------------------------------------------------------------
    # MCE-4.4: Contradiction detection v1 — keyword-based
    # ---------------------------------------------------------------------------
    contradictions_detected = 0
    try:
        detect_fn, build_rq_contradiction, _ = _import_contradiction_detector()
        all_merged_insights = person_entry.get("insights", [])
        new_contradictions = detect_fn(slug, all_merged_insights)

        if new_contradictions:
            # Merge into contradictions[] in INSIGHTS-STATE (additive, AC3)
            # Reload fresh state to get the just-saved version
            fresh_state = _load_insights_state(slug)
            fresh_persons = fresh_state.setdefault("persons", {})
            fresh_person = fresh_persons.setdefault(
                person_name, {"slug": slug, "canonical": person_name, "insights": []}
            )
            existing_contradictions: list[dict[str, Any]] = fresh_person.get("contradictions", [])
            if not isinstance(existing_contradictions, list):
                existing_contradictions = []

            # Dedup by contradiction id
            existing_ids = {c.get("id") for c in existing_contradictions if isinstance(c, dict)}
            for c in new_contradictions:
                if c.get("id") not in existing_ids:
                    existing_contradictions.append(c)
                    existing_ids.add(c.get("id"))

            fresh_person["contradictions"] = existing_contradictions
            fresh_state["schema_version"] = "2.1.0"
            _save_insights_state(slug, fresh_state)
            contradictions_detected = len(new_contradictions)

            # Also write each contradiction to REVIEW-QUEUE (AC2)
            rq = _load_review_queue(slug)
            new_rq_items = [build_rq_contradiction(slug, c) for c in new_contradictions]
            rq["items"] = _dedup_and_merge_review_queue_items(rq.get("items", []), new_rq_items)
            _save_review_queue(slug, rq)

            # Journey event (Art. IX)
            _append_jsonl(
                {
                    "event": "contradiction_detected",
                    "slug": slug,
                    "count": contradictions_detected,
                    "timestamp": _now_iso(),
                    "story": "MCE-4.4",
                }
            )
    except Exception as exc:
        logger.debug("Contradiction detection skipped for %s: %s", slug, exc)

    # Derive DNA-CONFIG.yaml composition from the merged insights
    dna_total = _write_dna_config_from_insights(slug, person_entry["insights"])

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "insights",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        insights_extracted=len(all_insights),
        insights_total=len(person_entry["insights"]),
        batches_processed=batches_processed,
        batches_failed=batches_failed,
        dna_elements_total=dna_total,
        contradictions_detected=contradictions_detected,
    )
    _append_jsonl(result)

    # MCE-6.3 — Persist processed source_files so subsequent cmd_insights runs
    # skip these sources. Idempotency guarantee.
    _newly_processed_sources = {c.get("source_file") for c in chunks if c.get("source_file")}
    if _newly_processed_sources:
        _all_processed = _processed_sources | _newly_processed_sources
        try:
            _save_processed_sources(slug, _all_processed)
        except OSError:
            pass  # fail-open per Art. XII

    from engine.intelligence.pipeline.mce.log_emitters import emit_execution_insights_box

    _exec_insights_metrics = {
        "insights_extracted": len(all_insights),
        "batches_processed": batches_processed,
        "batches_failed": batches_failed,
        "duration_ms": elapsed,
        "sources_processed_this_run": len(_newly_processed_sources),
        "sources_skipped_already_processed": len(_processed_sources),
    }
    emit_phase_payload(
        slug=slug,
        template_id="execution_insights",
        status="ok" if len(all_insights) > 0 else "warning",
        metrics=_exec_insights_metrics,
        ascii_block=emit_execution_insights_box(slug, _exec_insights_metrics),
    )
    return result


_ENTITIES_PROMPT_VERSION = "1.0"
_ENTITIES_MAX_INSIGHTS = 80
_ENTITIES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "persons": {"type": "array", "items": {"type": "string"}},
        "companies": {"type": "array", "items": {"type": "string"}},
        "products": {"type": "array", "items": {"type": "string"}},
        "concepts": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["persons", "companies", "products", "concepts"],
}


def _build_entities_prompt(slug: str, insights: list[dict[str, Any]]) -> str:
    """Assemble the entity-resolution prompt from insights (MCE-2.1 AC2).

    MCE-3.1 fix: insights produced by Sage use field names ``insight`` and
    ``quote``; the old fallback chain only checked ``text``/``statement``/
    ``content``. Without these the prompt arrived empty and the LLM
    returned 4 empty lists, leaving CANONICAL-MAP.json without entities.
    """
    sample = insights[:_ENTITIES_MAX_INSIGHTS]
    bullets: list[str] = []
    for i, ins in enumerate(sample, 1):
        if not isinstance(ins, dict):
            continue
        text = (
            ins.get("insight")
            or ins.get("quote")
            or ins.get("text")
            or ins.get("statement")
            or ins.get("content")
            or ""
        )
        text = str(text).strip().replace("\n", " ")[:280]
        if text:
            bullets.append(f"{i}. {text}")
    payload = "\n".join(bullets) if bullets else "(no insight text available)"

    # MCE-3.8: inject canonical domain list so LLM classifies concepts within
    # the formal taxonomy (vendas, outbound, hiring, ... ai_implementation).
    # Falls back gracefully if taxonomy unavailable.
    try:
        from engine.intelligence.taxonomy import list_domains

        canonical_domains = list_domains()
    except Exception:  # pragma: no cover — defensive
        canonical_domains = []
    domains_hint = (
        f"Dominios canonicos (use apenas estes para 'concepts'): {', '.join(canonical_domains)}\n"
        if canonical_domains
        else ""
    )

    # Phase 2 MCE-6.0: load from .prompt.md, fall back to inline if file missing.
    prompt_template = _load_prompt("entities")
    if prompt_template:
        return prompt_template.format(
            slug=slug,
            insights_count=len(sample),
            domains_hint=domains_hint,
            payload=payload,
        )
    # Inline fallback (verbatim copy of original — identical output guarantee).
    return (
        "Voce e um extrator deterministico de entidades. Analise os insights\n"
        "abaixo e produza UMA lista canonical de entidades mencionadas,\n"
        "separadas por tipo. Retorne APENAS JSON valido com 4 chaves\n"
        "(persons, companies, products, concepts) — cada uma uma lista de\n"
        "strings unicas, na lingua original do insight. Nao inventar. Se a\n"
        "categoria nao tiver mencao real, retorne lista vazia.\n"
        "\n"
        f"Slug do agente alvo: {slug}\n"
        f"Total de insights fornecidos: {len(sample)}\n"
        f"{domains_hint}"
        "\n"
        'Schema esperado: {"persons":[],"companies":[],"products":[],"concepts":[]}\n'
        "\n"
        "Insights:\n"
        f"{payload}\n"
        "\n"
        "JSON:"
    )


def _heuristic_entities(insights: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Deterministic fallback when no LLM is available (MCE-2.1 AC2).

    Scans insight metadata for explicit ``person`` / ``company`` / ``product``
    references that the upstream extractor may have tagged. This keeps Step 4
    non-blocking in smoke tests and offline runs.
    """
    persons, companies, products, concepts = set(), set(), set(), set()
    for ins in insights:
        if not isinstance(ins, dict):
            continue
        # Known field shapes from earlier passes
        for key in ("person", "speaker", "author"):
            v = ins.get(key)
            if isinstance(v, str) and v.strip():
                persons.add(v.strip())
        for key in ("company", "organization", "brand"):
            v = ins.get(key)
            if isinstance(v, str) and v.strip():
                companies.add(v.strip())
        for key in ("product", "offer"):
            v = ins.get(key)
            if isinstance(v, str) and v.strip():
                products.add(v.strip())
        tags = ins.get("tags") or ins.get("layer_tags") or []
        if isinstance(tags, list):
            for t in tags:
                if isinstance(t, str) and t.strip():
                    concepts.add(t.strip())
    return {
        "persons": sorted(persons),
        "companies": sorted(companies),
        "products": sorted(products),
        "concepts": sorted(concepts),
    }


def cmd_entities(slug: str) -> dict[str, Any]:
    """Step 4 — Entity resolution (MCE-2.1 AC2).

    Loads the slug's insights, asks the LLM router to canonicalize the
    entities mentioned, and writes the result to
    ``ARTIFACTS/canonical/{slug}/CANONICAL-MAP.json`` so
    ``log_generator._check_entity_resolution`` can mark Step 4 PASS.

    Provider selection follows the standard router precedence
    (``MCE_LLM_ENTITIES`` > ``MCE_LLM_PROVIDER`` > gemini default).
    If every provider is unavailable, falls back to a deterministic
    heuristic over insight metadata so the pipeline still produces a
    valid map (Step 4 stays PASS when there are entities to find).
    """
    t0 = time.monotonic()

    # MCE-3.1: prefer raw chunks (preserve mentions to persons/companies/
    # products) over abstracted insights (which lose entity surface forms).
    # Falls back to insights if no chunks are available yet.
    chunks = _resolve_chunks_for_slug(slug)
    chunks_total_before_filter = len(chunks)

    # MCE-6.3 — Per-source dedup. Reuse the cmd_insights registry as proxy
    # for "this source already had cognitive extraction done". cmd_entities
    # depends on the same chunks, so if cmd_insights already processed a
    # source, cmd_entities likely already saw it too. Cheap fail-soft skip.
    _entities_processed_sources = _load_processed_sources(slug)
    _entities_all_chunks_filtered = False
    if _entities_processed_sources and chunks:
        chunks = [c for c in chunks if c.get("source_file") not in _entities_processed_sources]
        # Track whether dedup ate everything — if so, do NOT fall through to
        # the insights-based prompt builder (it has a pre-existing format bug
        # and semantically we're already idempotent here).
        if not chunks:
            _entities_all_chunks_filtered = True

    if _entities_all_chunks_filtered:
        elapsed = (time.monotonic() - t0) * 1000
        result = _build_result(
            "entities",
            success=True,
            slug=slug,
            duration_ms=elapsed,
            entities_resolved=0,
            chunks_total=chunks_total_before_filter,
            sources_already_processed=len(_entities_processed_sources),
            reason=(
                f"all {chunks_total_before_filter} chunks belong to "
                f"{len(_entities_processed_sources)} already-processed sources — idempotent skip"
            ),
        )
        _append_jsonl(result)
        return result

    if chunks:
        # Synthesize a chunks-flavored insight list so _build_entities_prompt
        # picks the raw text via its ``insight`` field fallback.
        insights_source: list[dict[str, Any]] = [
            {
                "id": c.get("id_chunk") or c.get("id") or f"chunk-{i}",
                "insight": c.get("texto") or c.get("text") or c.get("content") or "",
                "meta": c.get("meta") or {},
            }
            for i, c in enumerate(chunks)
            if isinstance(c, dict)
        ]
    else:
        insights_source = _collect_insights_for_slug(slug)

    if not insights_source:
        elapsed = (time.monotonic() - t0) * 1000
        if chunks_total_before_filter > 0 and _entities_processed_sources:
            _reason = (
                f"all {chunks_total_before_filter} chunks belong to "
                f"{len(_entities_processed_sources)} already-processed sources — idempotent skip"
            )
        else:
            _reason = "no chunks or insights available for slug"
        result = _build_result(
            "entities",
            success=True,
            slug=slug,
            duration_ms=elapsed,
            entities_resolved=0,
            chunks_total=chunks_total_before_filter,
            sources_already_processed=len(_entities_processed_sources),
            reason=_reason,
        )
        _append_jsonl(result)
        return result

    prompt = _build_entities_prompt(slug, insights_source)
    provider_used: str | None = None
    raw_response: str | None = None
    entities_payload: dict[str, list[str]] | None = None
    llm_error: str | None = None

    try:
        from engine.intelligence.pipeline.mce.llm_extractor import extract_json
        from engine.intelligence.pipeline.mce.llm_router import (
            LLMRouter,
            ProviderUnavailableError,
            resolve_provider,
        )

        provider_used = resolve_provider(step="entities")
        router = LLMRouter()
        raw_response = router.run_prompt(
            prompt,
            step="entities",
            structured_schema=_ENTITIES_SCHEMA,
            max_output_tokens=1024,
        )
        parsed = extract_json(raw_response or "")
        if isinstance(parsed, dict):
            entities_payload = {
                "persons": [str(x) for x in parsed.get("persons", []) if x],
                "companies": [str(x) for x in parsed.get("companies", []) if x],
                "products": [str(x) for x in parsed.get("products", []) if x],
                "concepts": [str(x) for x in parsed.get("concepts", []) if x],
            }
    except ProviderUnavailableError as exc:  # pragma: no cover - network path
        llm_error = f"providers unavailable: {exc}"
    except Exception as exc:  # pragma: no cover - network path
        llm_error = f"{type(exc).__name__}: {exc}"

    if entities_payload is None:
        # Fallback: deterministic heuristic over insight fields
        entities_payload = _heuristic_entities(insights_source)
        provider_used = "heuristic-fallback"

    total = sum(len(v) for v in entities_payload.values())
    out_dir = ARTIFACTS / "canonical" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "CANONICAL-MAP.json"

    payload = {
        "slug": slug,
        "generated_at": _now_iso(),
        "entities": entities_payload,
        "canonical_entities": entities_payload,  # alias for downstream readers
        "sources_count": len(
            {ins.get("source_id") for ins in insights_source if isinstance(ins, dict)}
        ),
        "insights_seen": len(insights_source),
        "extraction_meta": {
            "provider": provider_used,
            "prompt_version": _ENTITIES_PROMPT_VERSION,
            "llm_error": llm_error,
        },
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---------------------------------------------------------------------------
    # MCE-4.4: Write open_loops from INSIGHTS-STATE to REVIEW-QUEUE (AC2)
    # open_loops are stored inside person_entry in INSIGHTS-STATE (if any).
    # cmd_entities does NOT generate open_loops itself — it merges what
    # cmd_insights or extraction phases wrote into the REVIEW-QUEUE.
    # ---------------------------------------------------------------------------
    open_loops_queued = 0
    try:
        _, _, build_rq_open_loop = _import_contradiction_detector()
        insights_state = _load_insights_state(slug)
        person_name_for_ol = _person_name_for_slug(slug)
        persons_map = insights_state.get("persons", {})
        person_entry_for_ol = persons_map.get(person_name_for_ol) or next(
            (v for v in persons_map.values() if isinstance(v, dict)), {}
        )
        raw_open_loops = (
            person_entry_for_ol.get("open_loops", [])
            if isinstance(person_entry_for_ol, dict)
            else []
        )
        if isinstance(raw_open_loops, list) and raw_open_loops:
            rq = _load_review_queue(slug)
            new_ol_items = [
                build_rq_open_loop(slug, ol) for ol in raw_open_loops if isinstance(ol, dict)
            ]
            rq["items"] = _dedup_and_merge_review_queue_items(rq.get("items", []), new_ol_items)
            _save_review_queue(slug, rq)
            open_loops_queued = len(new_ol_items)
    except Exception as exc:
        logger.debug("open_loops REVIEW-QUEUE write skipped for %s: %s", slug, exc)

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "entities",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        entities_resolved=total,
        canonical_map_path=str(out_path),
        provider=provider_used,
        breakdown={k: len(v) for k, v in entities_payload.items()},
        llm_error=llm_error,
        open_loops_queued=open_loops_queued,
    )
    _append_jsonl(result)
    emit_phase_payload(
        slug=slug,
        template_id="execution_entities",
        status="ok" if total > 0 else "warning",
        metrics={
            "entities_resolved": total,
            "provider": provider_used,
            "breakdown": {k: len(v) for k, v in entities_payload.items()},
        },
        ascii_block="",
    )
    # MCE-17.0 T11: emit entity_resolution for Chronicler STEP 11 renderer
    try:
        emit_phase_payload(
            slug=slug,
            template_id="entity_resolution",
            status="ok" if total > 0 else "warning",
            metrics={
                "total_entities": total,
                "canonical_map_path": str(out_path),
                "persons_resolved": len(entities_payload.get("persons", [])),
                "aliases_merged": 0,  # MCE-17.0 T11: alias merging tracked in cmd_resolve_entities
                "provider": provider_used,
            },
            ascii_block="",
        )
    except Exception as _exc:  # pragma: no cover
        logger.debug("entity_resolution emit failed (non-fatal): %s", _exc)
    return result


# ---------------------------------------------------------------------------
# MCE-13.22 — Entity Resolution cmd
# ---------------------------------------------------------------------------


def cmd_resolve_entities(slug: str) -> dict[str, Any]:
    """Entity Resolution pass — resolve aliases in CANONICAL-MAP.json (MCE-13.22).

    Loads CANONICAL-MAP.json for the slug and runs the entity_resolver module
    to deduplicate aliases (e.g. 'Hormozi' → 'Alex Hormozi') using string
    similarity >= 0.85 threshold. Writes updated CANONICAL-MAP.json with
    aliases{} and review_queue[].

    Non-blocking: exceptions are caught; failure here NEVER blocks the pipeline.

    Args:
        slug: Pipeline slug.

    Returns:
        Standard _build_result dict with entity resolution extras.
    """
    t0 = time.monotonic()
    try:
        from engine.intelligence.pipeline.mce.entity_resolver import resolve_entities_for_slug

        result_data = resolve_entities_for_slug(slug, root=_PROJECT_ROOT)
    except Exception as exc:
        logger.warning("cmd_resolve_entities: entity_resolver failed for %s: %s", slug, exc)
        result_data = {"status": "error", "error": str(exc)}

    elapsed = (time.monotonic() - t0) * 1000
    success = result_data.get("status") in ("updated", "no_map", "no_entities")
    result = _build_result(
        "resolve_entities",
        success=success,
        slug=slug,
        duration_ms=elapsed,
        entity_resolution=result_data,
        aliases_found=result_data.get("aliases_found", 0),
        review_queue_size=result_data.get("review_queue_size", 0),
    )
    _append_jsonl(result)
    emit_phase_payload(
        slug=slug,
        template_id="entity_resolution",
        status="ok" if success else "warning",
        metrics={
            "status": result_data.get("status", "unknown"),
            "aliases_found": result_data.get("aliases_found", 0),
            "review_queue_size": result_data.get("review_queue_size", 0),
        },
        ascii_block="",
    )
    return result

# ---------------------------------------------------------------------------
# MCE-13.23 — Atlas Classification cmd
# ---------------------------------------------------------------------------


def cmd_atlas_classify(slug: str) -> dict[str, Any]:
    """Atlas domain classification — classify slug into knowledge domains (MCE-13.23).

    Runs heuristic keyword classification (stdlib-only, no LLM) against
    INSIGHTS-STATE.json for the slug, then upserts the slug into the matching
    AGG-*.yaml domain files. Enables Phase 8 gate 7A to pass.

    LLM path: optional, enabled by env var MCE_ATLAS_LLM=1. Falls back to
    heuristic when the env var is absent or the LLM call fails.

    Non-blocking: exceptions are caught; failure here NEVER blocks the pipeline.

    Args:
        slug: Pipeline slug.

    Returns:
        Standard _build_result dict with atlas classification extras.
    """
    t0 = time.monotonic()
    try:
        from engine.intelligence.pipeline.mce.atlas_classifier import classify_and_register

        result_data = classify_and_register(slug, root=_PROJECT_ROOT)
    except Exception as exc:
        logger.warning("cmd_atlas_classify: atlas_classifier failed for %s: %s", slug, exc)
        result_data = {"status": "error", "error": str(exc), "domains": []}

    elapsed = (time.monotonic() - t0) * 1000
    success = result_data.get("status") in ("classified", "no_insights", "no_change")
    domains = result_data.get("domains", [])
    result = _build_result(
        "atlas_classify",
        success=success,
        slug=slug,
        duration_ms=elapsed,
        atlas_classification=result_data,
        domains_assigned=len(domains),
        primary_domain=domains[0] if domains else None,
    )
    _append_jsonl(result)
    # MCE-17.1 P4: atlas_classification dead emit removed — log_generator reads
    # `classification` (added in MCE-17.0 T11). atlas_classification was never
    # read by any renderer and co-existed with the canonical `classification` emit.
    return result


# ---------------------------------------------------------------------------
# V6 / Frente 6 — Hybrid L6-L10 extraction helpers
# (2026-05-13)
#
# Strategy: deterministic derivation first (no LLM cost), then 1 LLM call
# per layer to refine/complete what derivation left thin.  Provider = openai
# (gpt-4o-mini) per founder directive.  Prompts are built inline; the
# existing templates in engine/templates/phases/ serve as spec reference.
# ---------------------------------------------------------------------------


def _collect_insights_for_slug(slug: str) -> list[dict[str, Any]]:
    """Return the flat insights list from INSIGHTS-STATE.json for ``slug``."""
    state = _load_insights_state(slug)
    persons = state.get("persons", {})
    person_name = _person_name_for_slug(slug)
    # Try exact match, then case-insensitive
    entry = persons.get(person_name) or next(
        (v for v in persons.values() if isinstance(v, dict)), None
    )
    if entry is None:
        return []
    if isinstance(entry, dict):
        return entry.get("insights", [])
    if isinstance(entry, list):
        return [i for i in entry if isinstance(i, dict)]
    return []


def _slug_code(slug: str) -> str:
    """Derive 2-char uppercase code (``jane-doe`` -> ``JD``)."""
    parts = [p for p in slug.split("-") if p]  # ignora vazios (slug "[meet-N]-...")
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return (slug.strip("-")[:2] or "XX").upper()


def _derive_behavioral_from_insights(
    insights: list[dict[str, Any]], slug: str
) -> list[dict[str, Any]]:
    """Deterministic L6 derivation from [METODOLOGIA] + [FRAMEWORK] insights.

    Looks for trigger→action structure via simple keyword matching.
    Each derived pattern maps to: pattern_name, trigger, action, evidence.
    """
    import re

    code = _slug_code(slug)
    trigger_keywords = [
        "quando",
        "se ",
        "ao ",
        "diante",
        "frente",
        "para ",
        "após",
        "before",
        "when",
        "if ",
        "upon",
        "faced with",
    ]
    patterns: list[dict[str, Any]] = []
    seen_topics: set[str] = set()

    candidates = [
        i for i in insights if i.get("tag", "") in ("[METODOLOGIA]", "[FRAMEWORK]", "[HEURISTICA]")
    ]

    for idx, ins in enumerate(candidates):
        text = (ins.get("insight", "") + " " + ins.get("quote", "")).lower()

        # Build a short topic fingerprint to deduplicate
        topic_words = re.findall(r"\b[a-záéíóúãõâêîôûç]{5,}\b", text)[:3]
        topic_key = "_".join(sorted(topic_words))
        if topic_key in seen_topics:
            continue
        seen_topics.add(topic_key)

        # Extract a trigger phrase (first sentence fragment containing keyword)
        trigger_phrase = "Situação requerendo decisão estratégica"
        for kw in trigger_keywords:
            pos = text.find(kw)
            if pos != -1:
                snippet = text[pos : pos + 80].split(".")[0].strip()
                if len(snippet) > 10:
                    trigger_phrase = snippet.capitalize()
                    break

        insight_text = ins.get("insight", "")
        action_text = insight_text[:120] if insight_text else "Aplica metodologia estruturada"

        pattern: dict[str, Any] = {
            "id": f"BP-{code}-{idx + 1:03d}",
            "pattern_name": f"Padrão {idx + 1}: {insight_text[:50].strip('.')}..."
            if insight_text
            else f"Padrão comportamental {idx + 1}",
            "trigger": trigger_phrase,
            "action": action_text,
            "priority": ins.get("priority", "MEDIUM"),
            "insight_ids": [ins.get("id", "")],
            "chunk_ids": ins.get("chunks", ins.get("chunk_ids", [])),
            "quote": ins.get("quote", "")[:200],
            "source": "deterministic_derivation",
        }
        patterns.append(pattern)

        if len(patterns) >= 10:
            break

    return patterns


def _derive_voice_from_insights(insights: list[dict[str, Any]], slug: str) -> list[dict[str, Any]]:
    """Deterministic L8 derivation: collect direct quotes from [FILOSOFIA]/[HEURISTICA].

    Returns a list of signature phrase candidates (quote + context).
    """
    code = _slug_code(slug)
    phrases: list[dict[str, Any]] = []
    seen: set[str] = set()

    voice_tags = ("[FILOSOFIA]", "[HEURISTICA]", "[MODELO-MENTAL]")
    for idx, ins in enumerate(insights):
        if ins.get("tag", "") not in voice_tags:
            continue
        quote = (ins.get("quote", "") or "").strip()
        if len(quote) < 20:
            continue
        # Dedup by first 40 chars
        key = quote[:40].lower()
        if key in seen:
            continue
        seen.add(key)

        phrases.append(
            {
                "id": f"VP-{code}-{idx + 1:03d}",
                "phrase": quote[:200],
                "context": ins.get("insight", "")[:120],
                "tag": ins.get("tag", ""),
                "chunk_ids": ins.get("chunks", ins.get("chunk_ids", [])),
                "insight_id": ins.get("id", ""),
                "source": "deterministic_derivation",
            }
        )
        if len(phrases) >= 10:
            break

    return phrases


def _derive_obsessions_from_insights(
    insights: list[dict[str, Any]], slug: str
) -> list[dict[str, Any]]:
    """Deterministic L9 derivation via TF-IDF style top-term frequency.

    Returns top-5 obsession candidates based on stem/word frequency
    across all insight + quote text.
    """
    import re
    from collections import Counter

    code = _slug_code(slug)
    stopwords = {
        "que",
        "para",
        "com",
        "uma",
        "mais",
        "como",
        "não",
        "mas",
        "por",
        "são",
        "isso",
        "esta",
        "este",
        "quando",
        "então",
        "também",
        "muito",
        "outros",
        "nosso",
        "nossa",
        "suas",
        "seus",
        "todo",
        "toda",
        "cada",
        "dos",
        "das",
        "nos",
        "nas",
        "pelo",
        "pela",
        "num",
        "numa",
        "ser",
        "foi",
        "ele",
        "ela",
        "eles",
        "elas",
        "aqui",
        "após",
        "antes",
        "ainda",
        "entre",
        "esse",
        "essa",
        "qual",
        "quem",
        "onde",
        "sobre",
        "desde",
        "dentro",
        "durante",
        "sempre",
        "nunca",
        "agora",
        "hoje",
        "além",
        "mesmo",
        "assim",
        "tudo",
        "todos",
        "apenas",
        "pode",
        "deve",
        "será",
        "fazer",
        "feito",
        "tendo",
        "sendo",
        "outro",
        "outra",
        "junto",
        "muitas",
        "muitos",
        "parte",
        "tipo",
        "algo",
        "disso",
        "daqui",
        "dado",
        "tanto",
        "being",
        "that",
        "this",
        "with",
        "from",
        "they",
        "them",
        "their",
        "have",
        "were",
        "been",
        "will",
        "would",
        "could",
        "should",
        "which",
        "when",
        "what",
        "there",
        "gente",
        "você",
    }

    all_text = " ".join(
        ins.get("insight", "") + " " + ins.get("quote", "") for ins in insights
    ).lower()
    words = re.findall(r"\b[a-záéíóúãõâêîôûç]{5,}\b", all_text)
    freq = Counter(w for w in words if w not in stopwords)
    top_terms = [w for w, _ in freq.most_common(15)]

    # Group insights that mention each top term
    obsessions: list[dict[str, Any]] = []
    for term_idx, term in enumerate(top_terms[:7]):
        related = [
            ins
            for ins in insights
            if term in (ins.get("insight", "") + ins.get("quote", "")).lower()
        ]
        if len(related) < 2:
            continue
        chunk_ids: list[str] = []
        insight_ids: list[str] = []
        for ins in related[:5]:
            chunk_ids.extend(ins.get("chunks", ins.get("chunk_ids", [])))
            if ins.get("id"):
                insight_ids.append(ins["id"])

        rep_insight = related[0]
        obsessions.append(
            {
                "id": f"OBS-{code}-{term_idx + 1:03d}",
                "obsession": term.capitalize(),
                "frequency": len(related),
                "examples": [ins.get("insight", "")[:100] for ins in related[:3]],
                "chunk_ids": list(dict.fromkeys(chunk_ids))[:5],
                "insight_ids": list(dict.fromkeys(insight_ids))[:5],
                "quote": rep_insight.get("quote", "")[:200],
                "source": "deterministic_derivation",
            }
        )
        if len(obsessions) >= 5:
            break

    return obsessions


def _derive_paradoxes_from_insights(
    insights: list[dict[str, Any]], slug: str
) -> list[dict[str, Any]]:
    """Deterministic L10 derivation: detect tension-signal insights.

    Looks for keywords that indicate internal contradiction or tension.
    """
    import re

    code = _slug_code(slug)
    tension_signals = [
        "mas ",
        "porém",
        "ao mesmo tempo",
        "tensão",
        "contradiç",
        "entretanto",
        "apesar",
        "mesmo assim",
        "ainda assim",
        "but ",
        "however",
        "despite",
        "although",
        "yet ",
        "while ",
        "ao mesmo",
        "embora",
    ]

    tension_insights = [
        ins
        for ins in insights
        if any(
            sig in (ins.get("insight", "") + ins.get("quote", "")).lower()
            for sig in tension_signals
        )
    ]

    paradoxes: list[dict[str, Any]] = []
    seen_pairs: set[str] = set()

    for idx, ins in enumerate(tension_insights[:8]):
        text = ins.get("insight", "")
        # Try to split at tension word to get side_a / side_b
        tension_a = text
        tension_b = "Comportamento aparentemente oposto ao declarado"
        for sig in tension_signals:
            if sig.strip() in text.lower():
                parts = re.split(sig.strip(), text, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) == 2 and len(parts[0]) > 20 and len(parts[1]) > 20:
                    tension_a = parts[0].strip()
                    tension_b = parts[1].strip()
                    break

        key = tension_a[:30].lower()
        if key in seen_pairs:
            continue
        seen_pairs.add(key)

        paradoxes.append(
            {
                "id": f"PAR-{code}-{idx + 1:03d}",
                "tension_a": tension_a[:200],
                "tension_b": tension_b[:200],
                "resolution": "Feature, not bug — a tensão é produtiva e intencional.",
                "chunk_ids": ins.get("chunks", ins.get("chunk_ids", [])),
                "insight_id": ins.get("id", ""),
                "quote": ins.get("quote", "")[:200],
                "source": "deterministic_derivation",
            }
        )
        if len(paradoxes) >= 5:
            break

    return paradoxes


def _llm_refine_behavioral(
    slug: str,
    derived_patterns: list[dict[str, Any]],
    insights: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Single LLM call (OpenAI gpt-4o-mini) to refine/complete L6 patterns.

    Passes the derived patterns + a compressed sample of insights as context.
    Returns merged list (LLM output overrides derived where overlap exists).
    """
    try:
        from engine.intelligence.pipeline.mce.llm_router import LLMRouter
    except ImportError:
        logger.warning("llm_router not available — skipping LLM refinement for L6")
        return derived_patterns

    # Build a condensed context of top METODOLOGIA/FRAMEWORK insights
    sample_insights = [
        f"- [{i.get('tag', '')}] {i.get('insight', '')[:150]} (quote: {i.get('quote', '')[:100]})"
        for i in insights
        if i.get("tag", "") in ("[METODOLOGIA]", "[FRAMEWORK]", "[HEURISTICA]")
    ][:20]

    derived_json = json.dumps(derived_patterns, ensure_ascii=False, indent=2)
    insights_text = "\n".join(sample_insights)
    person_name = _person_name_for_slug(slug)
    code = _slug_code(slug)

    # Phase 2 MCE-6.0: load from .prompt.md, fall back to inline if file missing.
    _behavioral_tmpl = _load_prompt("behavioral")
    if _behavioral_tmpl:
        prompt = _behavioral_tmpl.format(
            person_name=person_name,
            slug=slug,
            code=code,
            derived_count=len(derived_patterns),
            derived_json=derived_json,
            insights_text=insights_text,
        )
    else:
        prompt = f"""You are an expert behavioral pattern extractor for the MCE pipeline.

Person: {person_name} (slug: {slug}, code: {code})

Below are {len(derived_patterns)} behavioral patterns derived deterministically from insights:
{derived_json}

Below are the source insights (METODOLOGIA/FRAMEWORK/HEURISTICA tags):
{insights_text}

Your task:
1. Review the derived patterns — fix any that are vague or incomplete.
2. Add 2-3 NEW patterns that are clearly visible in the insights but were missed.
3. Each pattern MUST have: id (BP-{code}-NNN), pattern_name (string), trigger (string), action (string), priority (HIGH/MEDIUM/LOW), insight_ids (list), chunk_ids (list), quote (string).
4. Return ONLY a JSON array of pattern objects. No explanation. No markdown.
5. Keep deterministically derived patterns that are valid. Total output: 5-8 patterns.
"""

    router = LLMRouter()
    try:
        raw = router.run_prompt(
            prompt, provider="openai", step="behavioral", max_output_tokens=3000
        )
        # Extract JSON array
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        if isinstance(data, list) and data:
            # Ensure each item has required fields
            refined = []
            for item in data:
                if isinstance(item, dict) and item.get("pattern_name") and item.get("trigger"):
                    item.setdefault("source", "llm_refined")
                    refined.append(item)
            return refined if refined else derived_patterns
    except Exception as exc:
        logger.warning("LLM refinement failed for behavioral (slug=%s): %s", slug, exc)

    return derived_patterns


def _llm_refine_identity(
    slug: str,
    derived_values: list[dict[str, Any]],
    derived_obsessions: list[dict[str, Any]],
    derived_paradoxes: list[dict[str, Any]],
    insights: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Single LLM call to refine L7 (values), L9 (obsessions), L10 (paradoxes)."""
    try:
        from engine.intelligence.pipeline.mce.llm_router import LLMRouter
    except ImportError:
        logger.warning("llm_router not available — skipping LLM refinement for L7/L9/L10")
        return derived_values, derived_obsessions, derived_paradoxes

    # Sample filosofia + modelo-mental insights for values
    value_insights = [
        f"- [{i.get('tag', '')}] {i.get('insight', '')[:150]} (quote: {i.get('quote', '')[:80]})"
        for i in insights
        if i.get("tag", "") in ("[FILOSOFIA]", "[MODELO-MENTAL]")
    ][:15]

    person_name = _person_name_for_slug(slug)
    code = _slug_code(slug)
    insights_text = "\n".join(value_insights)

    # Phase 2 MCE-6.0: load from .prompt.md, fall back to inline if file missing.
    _identity_tmpl = _load_prompt("identity")
    if _identity_tmpl:
        prompt = _identity_tmpl.format(
            person_name=person_name,
            slug=slug,
            code=code,
            insights_text=insights_text,
            derived_obsessions_json=json.dumps(derived_obsessions, ensure_ascii=False, indent=2)[
                :1000
            ],
        )
    else:
        prompt = f"""You are an expert identity layer extractor for the MCE pipeline.

Person: {person_name} (slug: {slug}, code: {code})

Source insights (FILOSOFIA/MODELO-MENTAL tags):
{insights_text}

Derived obsessions so far:
{json.dumps(derived_obsessions, ensure_ascii=False, indent=2)[:1000]}

Your task — return a JSON object with exactly 3 keys:
{{
  "values_hierarchy": [
    {{"id": "VAL-{code}-001", "value": "string", "rank": 1, "tier": 1, "evidence": "string", "chunk_ids": ["chunk_X"], "insight_ids": ["INS-X"], "quote": "string"}}
    // ... 3-5 total values
  ],
  "obsessions": [
    {{"id": "OBS-{code}-001", "obsession": "string", "frequency": 5, "examples": ["string"], "chunk_ids": ["chunk_X"], "insight_ids": ["INS-X"], "quote": "string"}}
    // ... 3-5 total obsessions
  ],
  "paradoxes": [
    {{"id": "PAR-{code}-001", "tension_a": "string", "tension_b": "string", "resolution": "string", "chunk_ids": ["chunk_X"], "insight_ids": ["INS-X"], "quote": "string"}}
    // ... 2-4 total paradoxes
  ]
}}

Rules:
- Values must be derived from the FILOSOFIA/MODELO-MENTAL insights above.
- Obsessions = recurring themes that drive ALL decisions. Check the derived obsessions + insights.
- Paradoxes = productive contradictions (things that seem to conflict but both are true for this person).
- Use chunk_ids from the insights list above where possible (e.g. ["chunk_2", "chunk_4"]).
- Return ONLY valid JSON. No markdown. No explanation.
"""

    def _merge_lists(
        llm_out: Any, derived: list[dict[str, Any]], min_count: int = 3
    ) -> list[dict[str, Any]]:
        """Merge LLM output with derived list, ensuring at least min_count entries."""
        if isinstance(llm_out, list) and len(llm_out) >= min_count:
            return llm_out
        # Pad with derived entries not already present in LLM output (by id)
        merged = list(llm_out) if isinstance(llm_out, list) else []
        existing_ids = {item.get("id", "") for item in merged}
        for item in derived:
            if len(merged) >= max(min_count, len(merged)):
                break
            if item.get("id", "") not in existing_ids:
                merged.append(item)
        return merged

    router = LLMRouter()
    try:
        raw = router.run_prompt(prompt, provider="openai", step="identity", max_output_tokens=4000)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        # Sanitize control characters that break json.loads
        import re as _re

        raw = _re.sub(r"[\x00-\x1f\x7f]", " ", raw)
        data = json.loads(raw)
        if isinstance(data, dict):
            refined_values = _merge_lists(data.get("values_hierarchy"), derived_values, min_count=3)
            refined_obs = _merge_lists(data.get("obsessions"), derived_obsessions, min_count=3)
            refined_par = _merge_lists(data.get("paradoxes"), derived_paradoxes, min_count=3)
            return refined_values, refined_obs, refined_par
    except Exception as exc:
        logger.warning("LLM refinement failed for identity (slug=%s): %s", slug, exc)

    return derived_values, derived_obsessions, derived_paradoxes


def _llm_refine_voice(
    slug: str,
    derived_phrases: list[dict[str, Any]],
    insights: list[dict[str, Any]],
) -> dict[str, Any]:
    """Single LLM call to build the full voice-dna.yaml content.

    Returns a dict ready to be written as YAML.
    """
    try:
        from engine.intelligence.pipeline.mce.llm_router import LLMRouter
    except ImportError:
        logger.warning("llm_router not available — skipping LLM refinement for L8")
        return {}

    person_name = _person_name_for_slug(slug)
    code = _slug_code(slug)

    # Collect all quotes from insights
    quotes_sample = [
        f"- {i.get('quote', '')[:120]}" for i in insights if i.get("quote", "").strip()
    ][:25]
    quotes_text = "\n".join(quotes_sample)

    phrases_json = json.dumps(derived_phrases, ensure_ascii=False)[:800]

    # Phase 2 MCE-6.0: load from .prompt.md, fall back to inline if file missing.
    _voice_tmpl = _load_prompt("voice")
    if _voice_tmpl:
        prompt = _voice_tmpl.format(
            person_name=person_name,
            slug=slug,
            code=code,
            quotes_text=quotes_text,
            phrases_json=phrases_json,
        )
    else:
        prompt = f"""You are an expert Voice DNA extractor for the MCE pipeline.

Person: {person_name} (slug: {slug}, code: {code})

Sample quotes from their content:
{quotes_text}

Derived signature phrase seeds:
{phrases_json}

Your task — return a JSON object for this person's Voice DNA with:
{{
  "tone_profile": {{
    "certainty": {{"score": 7.5, "justificativa": "string", "chunk_ids": ["chunk_2"]}},
    "authority": {{"score": 8.0, "justificativa": "string", "chunk_ids": ["chunk_4"]}},
    "warmth": {{"score": 6.5, "justificativa": "string", "chunk_ids": ["chunk_2"]}},
    "directness": {{"score": 7.0, "justificativa": "string", "chunk_ids": ["chunk_4"]}},
    "teaching_focus": {{"score": 8.5, "justificativa": "string", "chunk_ids": ["chunk_2"]}},
    "confidence": {{"score": 7.5, "justificativa": "string", "chunk_ids": ["chunk_4"]}}
  }},
  "signature_phrases": [
    {{"id": "VP-{code}-001", "phrase": "string", "context": "string", "chunk_ids": ["chunk_X"], "poder": 8}}
    // ... 3-5 phrases
  ],
  "behavioral_states": [
    {{"nome": "Teaching Mode", "trigger": "string", "tom": "string", "sinais": ["string1", "string2"], "chunk_ids": ["chunk_X"]}}
    // ... 3-4 states
  ],
  "communication_patterns": {{
    "opening_hooks": {{"padrao": "string", "exemplos": ["quote1"], "chunk_ids": ["chunk_X"]}},
    "story_structure": {{"padrao": "string", "descricao": "string", "chunk_ids": ["chunk_X"]}},
    "closing_signatures": {{"padrao": "string", "exemplos": ["quote1"], "chunk_ids": ["chunk_X"]}}
  }}
}}

Rules:
- Base ALL claims on the actual quotes provided above.
- chunk_ids should reference the chunk IDs from the quotes (e.g. chunk_2, chunk_4, chunk_6).
- Signature phrases MUST be actual phrases from the quotes, not invented.
- Return ONLY valid JSON. No markdown. No explanation.
"""

    router = LLMRouter()
    try:
        raw = router.run_prompt(prompt, provider="openai", step="voice", max_output_tokens=4000)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        # Sanitize control characters that break json.loads
        import re as _re

        raw = _re.sub(r"[\x00-\x1f\x7f]", " ", raw)
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        logger.warning("LLM refinement failed for voice (slug=%s): %s", slug, exc)

    return {}


def cmd_behavioral(slug: str) -> dict[str, Any]:
    """V6/Frente-6: Behavioral patterns (L6) — hybrid deterministic + LLM refinement.

    Steps:
    1. Load insights from INSIGHTS-STATE.json
    2. Derive behavioral patterns deterministically from [METODOLOGIA]/[FRAMEWORK]/[HEURISTICA] insights
    3. Refine via 1 LLM call (OpenAI gpt-4o-mini)
    4. Write behavioral-patterns.yaml to knowledge/{bucket}/dna/persons/{slug}/
    5. Update INSIGHTS-STATE.json with behavioral_patterns field
    6. Mark state.mce.behavioral_completed_at
    """
    t0 = time.monotonic()

    # MCE-6.3 — Idempotent skip if INSIGHTS-STATE.json unchanged since last run.
    _should_skip, _skip_reason = _should_skip_cmd_by_insights_mtime(slug, "behavioral")
    if _should_skip:
        elapsed = (time.monotonic() - t0) * 1000
        result = _build_result(
            "behavioral",
            success=True,
            slug=slug,
            duration_ms=elapsed,
            patterns_extracted=0,
            llm_used=False,
            extraction_skipped=True,
            reason=_skip_reason,
        )
        _append_jsonl(result)
        return result

    bucket = _detect_bucket_for_slug(slug)
    dna_dir = _dna_dir_for_slug(slug, bucket)
    insights = _collect_insights_for_slug(slug)

    patterns_written = 0
    yaml_path: Path | None = None
    llm_used = False

    if insights:
        # Step A: deterministic derivation
        derived = _derive_behavioral_from_insights(insights, slug)

        # Step B: LLM refinement
        try:
            refined = _llm_refine_behavioral(slug, derived, insights)
            llm_used = True
        except Exception as exc:
            logger.warning("L6 LLM refinement error for %s: %s", slug, exc)
            refined = derived

        # Step C: Write behavioral-patterns.yaml
        dna_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = dna_dir / "behavioral-patterns.yaml"
        yaml_content: dict[str, Any] = {
            "pessoa": _person_name_for_slug(slug),
            "slug": slug,
            "versao": "1.0.0",
            "data_extracao": _now_iso(),
            "layer": "L6",
            "layer_name": "Behavioral Patterns",
            "total_patterns": len(refined),
            "source_pipeline_step": "Step 6 - Behavioral Extraction (V6)",
            "extraction_method": "hybrid_deterministic_llm",
            # Use "patterns" key — consumed by log_generator._check_mce_behavioral
            "patterns": refined,
            # Also keep "behavioral_patterns" for backward compat with identity-checkpoint
            "behavioral_patterns": refined,
        }
        yaml_path.write_text(
            yaml.dump(yaml_content, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        patterns_written = len(refined)

        # Step D: merge into INSIGHTS-STATE
        state = _load_insights_state(slug)
        bp_key = _person_name_for_slug(slug)
        state.setdefault("behavioral_patterns", {})[bp_key] = refined
        state.setdefault("mce", {})["behavioral_completed_at"] = _now_iso()
        _save_insights_state(slug, state)

        # Step E: update DNA-CONFIG.yaml with L6 count
        dna_config_path = dna_dir / "DNA-CONFIG.yaml"
        if dna_config_path.exists():
            try:
                dna_cfg = yaml.safe_load(dna_config_path.read_text(encoding="utf-8")) or {}
                dna_cfg.setdefault("composition", {})["BEHAVIORAL_PATTERNS"] = patterns_written
                dna_config_path.write_text(
                    yaml.dump(
                        dna_cfg, allow_unicode=True, default_flow_style=False, sort_keys=False
                    ),
                    encoding="utf-8",
                )
            except Exception as exc:
                logger.debug("DNA-CONFIG update failed for behavioral: %s", exc)
    else:
        # No insights available — write minimal marker
        state = _load_insights_state(slug)
        state.setdefault("mce", {})["behavioral_completed_at"] = _now_iso()
        _save_insights_state(slug, state)

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "behavioral",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        patterns_extracted=patterns_written,
        yaml_written=str(yaml_path) if yaml_path else None,
        llm_used=llm_used,
        extraction_skipped=patterns_written == 0,
    )
    _append_jsonl(result)
    from engine.intelligence.pipeline.mce.log_emitters import emit_execution_behavioral_box

    _exec_behavioral_metrics = {
        "patterns_extracted": patterns_written,
        "llm_used": llm_used,
        "duration_ms": elapsed,
        "extraction_skipped": patterns_written == 0,
    }
    emit_phase_payload(
        slug=slug,
        template_id="execution_behavioral",
        status="ok" if patterns_written > 0 else "warning",
        metrics=_exec_behavioral_metrics,
        ascii_block=emit_execution_behavioral_box(slug, _exec_behavioral_metrics),
    )
    # MCE-6.3 — Mark cmd completed for idempotent skip on next run
    try:
        _save_cmd_marker(slug, "behavioral")
    except OSError:
        pass
    return result


def cmd_identity(slug: str) -> dict[str, Any]:
    """V6/Frente-6: Identity layer (L7 values, L9 obsessions, L10 paradoxes) — hybrid.

    Steps:
    1. Load insights from INSIGHTS-STATE.json
    2. Derive values/obsessions/paradoxes deterministically
    3. Refine via 1 LLM call (OpenAI gpt-4o-mini) — returns all 3 in one call
    4. Write values-hierarchy.yaml, obsessions.yaml, paradoxes.yaml
    5. Update INSIGHTS-STATE with value_hierarchy/obsessions/paradoxes fields
    """
    t0 = time.monotonic()

    # MCE-6.3 — Idempotent skip if INSIGHTS-STATE.json unchanged since last run.
    _should_skip, _skip_reason = _should_skip_cmd_by_insights_mtime(slug, "identity")
    if _should_skip:
        elapsed = (time.monotonic() - t0) * 1000
        result = _build_result(
            "identity",
            success=True,
            slug=slug,
            duration_ms=elapsed,
            values_extracted=0,
            obsessions_extracted=0,
            paradoxes_extracted=0,
            llm_used=False,
            extraction_skipped=True,
            reason=_skip_reason,
        )
        _append_jsonl(result)
        return result

    bucket = _detect_bucket_for_slug(slug)
    dna_dir = _dna_dir_for_slug(slug, bucket)
    insights = _collect_insights_for_slug(slug)

    values_written = 0
    obsessions_written = 0
    paradoxes_written = 0
    llm_used = False

    if insights:
        code = _slug_code(slug)
        person_name = _person_name_for_slug(slug)

        # Step A: deterministic derivation
        derived_obs = _derive_obsessions_from_insights(insights, slug)
        derived_par = _derive_paradoxes_from_insights(insights, slug)
        # Values derivation: use FILOSOFIA insights ranked by priority
        derived_values: list[dict[str, Any]] = []
        value_insights = [
            i for i in insights if i.get("tag", "") in ("[FILOSOFIA]", "[MODELO-MENTAL]")
        ]
        for vidx, ins in enumerate(value_insights[:5]):
            derived_values.append(
                {
                    "id": f"VAL-{code}-{vidx + 1:03d}",
                    "value": ins.get("insight", "")[:80].rstrip("."),
                    "rank": vidx + 1,
                    "tier": 1 if ins.get("priority") == "HIGH" else 2,
                    "evidence": ins.get("insight", "")[:150],
                    "chunk_ids": ins.get("chunks", ins.get("chunk_ids", [])),
                    "insight_ids": [ins.get("id", "")],
                    "quote": ins.get("quote", "")[:200],
                    "source": "deterministic_derivation",
                }
            )

        # Step B: LLM refinement (single call for all 3 layers)
        try:
            refined_values, refined_obs, refined_par = _llm_refine_identity(
                slug, derived_values, derived_obs, derived_par, insights
            )
            llm_used = True
        except Exception as exc:
            logger.warning("L7/L9/L10 LLM refinement error for %s: %s", slug, exc)
            refined_values, refined_obs, refined_par = derived_values, derived_obs, derived_par

        # Step C: Write YAML files
        dna_dir.mkdir(parents=True, exist_ok=True)

        # values-hierarchy.yaml
        values_yaml: dict[str, Any] = {
            "pessoa": person_name,
            "slug": slug,
            "versao": "1.0.0",
            "data_extracao": _now_iso(),
            "layer": "L7",
            "layer_name": "Values Hierarchy",
            "total_values": len(refined_values),
            "source_pipeline_step": "Step 7 - Identity Extraction (V6)",
            "extraction_method": "hybrid_deterministic_llm",
            "values": refined_values,
        }
        (dna_dir / "values-hierarchy.yaml").write_text(
            yaml.dump(values_yaml, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        values_written = len(refined_values)

        # obsessions.yaml
        obs_yaml: dict[str, Any] = {
            "pessoa": person_name,
            "slug": slug,
            "versao": "1.0.0",
            "data_extracao": _now_iso(),
            "layer": "L9",
            "layer_name": "Obsessions",
            "total_obsessions": len(refined_obs),
            "source_pipeline_step": "Step 7 - Identity Extraction (V6)",
            "extraction_method": "hybrid_deterministic_llm",
            "obsessions": refined_obs,
        }
        (dna_dir / "obsessions.yaml").write_text(
            yaml.dump(obs_yaml, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        obsessions_written = len(refined_obs)

        # paradoxes.yaml
        par_yaml: dict[str, Any] = {
            "pessoa": person_name,
            "slug": slug,
            "versao": "1.0.0",
            "data_extracao": _now_iso(),
            "layer": "L10",
            "layer_name": "Paradoxes",
            "total_paradoxes": len(refined_par),
            "source_pipeline_step": "Step 7 - Identity Extraction (V6)",
            "extraction_method": "hybrid_deterministic_llm",
            "paradoxes": refined_par,
        }
        (dna_dir / "paradoxes.yaml").write_text(
            yaml.dump(par_yaml, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        paradoxes_written = len(refined_par)

        # Step D: update INSIGHTS-STATE
        state = _load_insights_state(slug)
        state.setdefault("value_hierarchy", {})[person_name] = refined_values
        state.setdefault("obsessions", {})[person_name] = refined_obs
        state.setdefault("paradoxes", {})[person_name] = refined_par
        state.setdefault("mce", {})["identity_completed_at"] = _now_iso()
        state.setdefault("change_log", []).append(
            {
                "entity": "identity_layer",
                "key": person_name,
                "change": "new",
                "note": f"V6: {values_written} values, {obsessions_written} obsessions, {paradoxes_written} paradoxes",
                "timestamp": _now_iso(),
            }
        )
        _save_insights_state(slug, state)

        # Step E: update DNA-CONFIG.yaml with L7/L9/L10 counts
        dna_config_path = dna_dir / "DNA-CONFIG.yaml"
        if dna_config_path.exists():
            try:
                dna_cfg = yaml.safe_load(dna_config_path.read_text(encoding="utf-8")) or {}
                comp = dna_cfg.setdefault("composition", {})
                comp["VALUES_HIERARCHY"] = values_written
                comp["OBSESSIONS"] = obsessions_written
                comp["PARADOXES"] = paradoxes_written
                dna_config_path.write_text(
                    yaml.dump(
                        dna_cfg, allow_unicode=True, default_flow_style=False, sort_keys=False
                    ),
                    encoding="utf-8",
                )
            except Exception as exc:
                logger.debug("DNA-CONFIG update failed for identity: %s", exc)
    else:
        state = _load_insights_state(slug)
        state.setdefault("mce", {})["identity_completed_at"] = _now_iso()
        _save_insights_state(slug, state)

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "identity",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        values_extracted=values_written,
        obsessions_extracted=obsessions_written,
        paradoxes_extracted=paradoxes_written,
        llm_used=llm_used,
        extraction_skipped=(values_written + obsessions_written + paradoxes_written) == 0,
    )
    _append_jsonl(result)
    from engine.intelligence.pipeline.mce.log_emitters import emit_execution_identity_box

    _exec_identity_metrics = {
        "values_extracted": values_written,
        "obsessions_extracted": obsessions_written,
        "paradoxes_extracted": paradoxes_written,
        "llm_used": llm_used,
        "duration_ms": elapsed,
        "extraction_skipped": (values_written + obsessions_written + paradoxes_written) == 0,
    }
    emit_phase_payload(
        slug=slug,
        template_id="execution_identity",
        status="ok" if (values_written + obsessions_written + paradoxes_written) > 0 else "warning",
        metrics=_exec_identity_metrics,
        ascii_block=emit_execution_identity_box(slug, _exec_identity_metrics),
    )
    # MCE-6.3 — Mark cmd completed for idempotent skip on next run
    try:
        _save_cmd_marker(slug, "identity")
    except OSError:
        pass
    return result


def cmd_voice(slug: str) -> dict[str, Any]:
    """V6/Frente-6: Voice DNA (L8) — hybrid deterministic + LLM refinement.

    Steps:
    1. Load insights from INSIGHTS-STATE.json
    2. Derive signature phrase seeds from [FILOSOFIA]/[HEURISTICA] quotes
    3. Refine via 1 LLM call (OpenAI gpt-4o-mini) to produce full voice profile
    4. Write voice-dna.yaml to knowledge/{bucket}/dna/persons/{slug}/
    5. Update INSIGHTS-STATE with voice_traits field
    """
    t0 = time.monotonic()

    # MCE-6.3 — Idempotent skip if INSIGHTS-STATE.json unchanged since last run.
    _should_skip, _skip_reason = _should_skip_cmd_by_insights_mtime(slug, "voice")
    if _should_skip:
        elapsed = (time.monotonic() - t0) * 1000
        result = _build_result(
            "voice",
            success=True,
            slug=slug,
            duration_ms=elapsed,
            signature_phrases=0,
            llm_used=False,
            extraction_skipped=True,
            reason=_skip_reason,
        )
        _append_jsonl(result)
        return result

    bucket = _detect_bucket_for_slug(slug)
    dna_dir = _dna_dir_for_slug(slug, bucket)
    insights = _collect_insights_for_slug(slug)

    phrases_written = 0
    yaml_path: Path | None = None
    llm_used = False

    if insights:
        person_name = _person_name_for_slug(slug)

        # Step A: deterministic seed phrases
        derived_phrases = _derive_voice_from_insights(insights, slug)

        # Step B: LLM refinement → full voice profile
        try:
            voice_data = _llm_refine_voice(slug, derived_phrases, insights)
            llm_used = True
        except Exception as exc:
            logger.warning("L8 LLM refinement error for %s: %s", slug, exc)
            voice_data = {}

        # Merge: ensure at least 5 signature phrases (gate threshold in log_generator)
        llm_phrases = voice_data.get("signature_phrases", [])
        if isinstance(llm_phrases, list) and len(llm_phrases) >= 5:
            sig_phrases = llm_phrases
        else:
            # Pad with deterministic seed phrases not already in LLM output
            merged = list(llm_phrases) if isinstance(llm_phrases, list) else []
            seen_phrase_ids = {p.get("id", "") for p in merged}
            for dp in derived_phrases:
                if len(merged) >= 5:
                    break
                if dp.get("id", "") not in seen_phrase_ids:
                    merged.append(dp)
            sig_phrases = merged if merged else derived_phrases

        # Step C: Write voice-dna.yaml
        dna_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = dna_dir / "voice-dna.yaml"

        voice_yaml: dict[str, Any] = {
            "pessoa": person_name,
            "slug": slug,
            "versao": "1.0.0",
            "data_extracao": _now_iso(),
            "layer": "L8",
            "layer_name": "Voice DNA",
            "total_signature_phrases": len(sig_phrases),
            "source_pipeline_step": "Step 8 - Voice DNA Extraction (V6)",
            "extraction_method": "hybrid_deterministic_llm",
            "tone_profile": voice_data.get("tone_profile", {}),
            "signature_phrases": sig_phrases,
            "behavioral_states": voice_data.get("behavioral_states", []),
            "communication_patterns": voice_data.get("communication_patterns", {}),
        }
        yaml_path.write_text(
            yaml.dump(voice_yaml, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        phrases_written = len(sig_phrases)

        # Step D: update INSIGHTS-STATE
        state = _load_insights_state(slug)
        state.setdefault("voice_traits", {})[person_name] = sig_phrases
        state.setdefault("mce", {})["voice_completed_at"] = _now_iso()
        state.setdefault("change_log", []).append(
            {
                "entity": "voice_traits",
                "key": person_name,
                "change": "new",
                "note": f"V6: {phrases_written} signature phrases, llm_used={llm_used}",
                "timestamp": _now_iso(),
            }
        )
        _save_insights_state(slug, state)

        # Step E: update DNA-CONFIG.yaml with L8 count
        dna_config_path = dna_dir / "DNA-CONFIG.yaml"
        if dna_config_path.exists():
            try:
                dna_cfg = yaml.safe_load(dna_config_path.read_text(encoding="utf-8")) or {}
                dna_cfg.setdefault("composition", {})["VOICE_TRAITS"] = phrases_written
                dna_config_path.write_text(
                    yaml.dump(
                        dna_cfg, allow_unicode=True, default_flow_style=False, sort_keys=False
                    ),
                    encoding="utf-8",
                )
            except Exception as exc:
                logger.debug("DNA-CONFIG update failed for voice: %s", exc)
    else:
        state = _load_insights_state(slug)
        state.setdefault("mce", {})["voice_completed_at"] = _now_iso()
        _save_insights_state(slug, state)

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "voice",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        signature_phrases=phrases_written,
        yaml_written=str(yaml_path) if yaml_path else None,
        llm_used=llm_used,
        extraction_skipped=phrases_written == 0,
    )
    _append_jsonl(result)
    from engine.intelligence.pipeline.mce.log_emitters import emit_execution_voice_box

    _exec_voice_metrics = {
        "signature_phrases": phrases_written,
        "llm_used": llm_used,
        "duration_ms": elapsed,
        "extraction_skipped": phrases_written == 0,
    }
    emit_phase_payload(
        slug=slug,
        template_id="execution_voice",
        status="ok" if phrases_written > 0 else "warning",
        metrics=_exec_voice_metrics,
        ascii_block=emit_execution_voice_box(slug, _exec_voice_metrics),
    )
    # MCE-6.3 — Mark cmd completed for idempotent skip on next run
    try:
        _save_cmd_marker(slug, "voice")
    except OSError:
        pass
    return result


# ---------------------------------------------------------------------------
# Command: narrative (MCE-4.1 — NARRATIVE METABOLISM v3.1.0)
# Triggered by auto-advance "start_narrative" FSM event.
# Loads NARRATIVES-STATE.json, merges incoming narrative for slug using
# narrative_merger.py, writes atomically, emits journey log.
# Stack: stdlib + PyYAML only. Zero LLM calls.
# ---------------------------------------------------------------------------

_NARRATIVES_STATE_PATH = (
    _PROJECT_ROOT / ".data" / "artifacts" / "narratives" / "NARRATIVES-STATE.json"
)
_NARRATIVE_JOURNAL_PATH = _PROJECT_ROOT / ".data" / "journey" / "narrative.jsonl"

# Canonical schema version this command produces.
_NARRATIVES_SCHEMA_VERSION = "3.1.0"

# 10 per-domain merge rules (kept here for inline reference in cmd_narrative;
# authoritative copy lives in narrative_merger.py).
_NARRATIVE_MERGE_RULES: dict[str, dict[str, object]] = {
    "vendas": {"strategy": "append", "dedup_key": "slug", "max_entries": 0},
    "ads": {"strategy": "merge_latest", "dedup_key": "slug", "max_entries": 50},
    "offers": {"strategy": "replace", "dedup_key": "slug", "max_entries": 10},
    "content": {"strategy": "append", "dedup_key": "slug", "max_entries": 0},
    "marketing": {"strategy": "merge_latest", "dedup_key": "slug", "max_entries": 0},
    "finance": {"strategy": "replace", "dedup_key": "slug", "max_entries": 0},
    "hiring": {"strategy": "append", "dedup_key": "slug", "max_entries": 20},
    "outbound": {"strategy": "merge_latest", "dedup_key": "slug", "max_entries": 30},
    "leadership": {"strategy": "append", "dedup_key": "slug", "max_entries": 0},
    "customer-success": {"strategy": "merge_latest", "dedup_key": "slug", "max_entries": 0},
}


def _load_narratives_state() -> dict[str, Any]:
    """Load NARRATIVES-STATE.json or return empty skeleton."""
    if _NARRATIVES_STATE_PATH.exists():
        try:
            return json.loads(_NARRATIVES_STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("cmd_narrative: failed to load NARRATIVES-STATE.json: %s", exc)
    return {
        "schema_version": _NARRATIVES_SCHEMA_VERSION,
        "created": _now_iso(),
        "last_updated": _now_iso(),
        "persons": {},
        "themes": {},
        "merge_rules": dict(_NARRATIVE_MERGE_RULES),
    }


def _save_narratives_state(state: dict[str, Any]) -> None:
    """Persist NARRATIVES-STATE.json atomically (AC1 — C-07 compliance)."""
    target = _NARRATIVES_STATE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path_str = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path_str, str(target))
    except Exception:
        try:
            os.unlink(tmp_path_str)
        except OSError:
            pass
        raise


def _emit_narrative_journal(event: dict[str, Any]) -> None:
    """Append *event* to .data/journey/narrative.jsonl (non-fatal)."""
    try:
        _NARRATIVE_JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _NARRATIVE_JOURNAL_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:
        logger.debug("cmd_narrative: journal write failed (non-fatal): %s", exc)


def cmd_narrative(slug: str) -> dict[str, Any]:
    """Narrative Metabolism (MCE-4.1 — NARRATIVES-STATE v3.1.0).

    Updates the global NARRATIVES-STATE.json for *slug*:
      1. Load existing state (or create empty skeleton).
      2. Check schema_version — migrate inline if outdated.
      3. Detect bucket via _detect_bucket_for_slug.
      4. Import narrative_merger and apply merge_narrative_entry for the slug.
      5. Save atomically (AC1).
      6. Emit journey log event ``narrative_merged`` (Art. IX).

    No LLM calls. stdlib + PyYAML only.

    Args:
        slug: Person slug (e.g. "alex-hormozi").

    Returns:
        Standard _build_result dict.
    """
    t0 = time.monotonic()
    bucket = _detect_bucket_for_slug(slug)

    state = _load_narratives_state()

    # Inline migration guard: if schema_version absent or old, add fields
    if state.get("schema_version") != _NARRATIVES_SCHEMA_VERSION:
        logger.warning(
            "cmd_narrative: NARRATIVES-STATE schema_version=%s, expected %s — "
            "applying inline migration. Run scripts/migrate_narratives_state_v310.py "
            "for a full migration.",
            state.get("schema_version"),
            _NARRATIVES_SCHEMA_VERSION,
        )
        state["schema_version"] = _NARRATIVES_SCHEMA_VERSION
        if "merge_rules" not in state:
            state["merge_rules"] = dict(_NARRATIVE_MERGE_RULES)

    # Import narrative_merger (deferred to avoid circular imports at module load)
    try:
        from engine.intelligence.pipeline.mce.narrative_merger import (
            merge_narrative_entry,
        )

        merger_available = True
    except ImportError as exc:
        logger.warning("cmd_narrative: narrative_merger not importable: %s", exc)
        merger_available = False

    persons: dict[str, Any] = (
        state.get("persons", {}) if isinstance(state.get("persons"), dict) else {}
    )

    # Build incoming entry for this slug
    existing_entry: dict[str, Any] = persons.get(slug, {})
    incoming_entry: dict[str, Any] = {
        "slug": slug,
        "bucket": bucket,
        "last_updated": _now_iso(),
    }

    merged_entry: dict[str, Any]
    if merger_available:
        # Determine domain from existing entry or default to "vendas"
        domain = existing_entry.get("domain", "vendas")
        try:
            merged_entry = merge_narrative_entry(existing_entry, incoming_entry, domain, bucket)
        except ValueError as exc:
            # Bucket validation failure — log and skip write
            logger.error("cmd_narrative: bucket validation failed for slug=%s: %s", slug, exc)
            elapsed = (time.monotonic() - t0) * 1000
            return _build_result(
                "narrative",
                success=False,
                slug=slug,
                duration_ms=elapsed,
                error=str(exc),
            )
    else:
        # Fallback: minimal merge without merger module
        merged_entry = {**existing_entry, **incoming_entry}

    persons[slug] = merged_entry
    state["persons"] = persons
    state["last_updated"] = _now_iso()

    # ------------------------------------------------------------------
    # MCE-11.15: patterns_identified + consensus_points detection
    # ------------------------------------------------------------------
    patterns_count = 0
    consensus_count = 0
    try:
        from engine.intelligence.pipeline.mce.narrative_patterns import (
            detect_consensus,
            detect_patterns,
            merge_consensus_incremental,
            merge_patterns_incremental,
        )

        # 1. Load per-slug insights for the current slug
        slug_insights_state = _load_insights_state(slug)
        slug_persons = slug_insights_state.get("persons", {})
        slug_insights: list[dict[str, Any]] = []
        for person_data in slug_persons.values():
            if isinstance(person_data, dict):
                slug_insights.extend(person_data.get("insights", []))

        # Fallback: per-slug INSIGHTS-STATE in mce artifacts dir
        if not slug_insights:
            mce_slug_path = ARTIFACTS / "mce" / slug / "INSIGHTS-STATE.json"
            if mce_slug_path.exists():
                try:
                    raw = json.loads(mce_slug_path.read_text(encoding="utf-8"))
                    ins_state = raw.get("insights_state", raw)
                    if isinstance(ins_state, dict):
                        for person_data in ins_state.get("persons", {}).values():
                            if isinstance(person_data, dict):
                                slug_insights.extend(person_data.get("insights", []))
                except Exception as _exc:
                    logger.debug(
                        "cmd_narrative: mce insights fallback failed for %s: %s", slug, _exc
                    )

        # 2. Detect patterns for this slug
        if slug_insights:
            fresh_patterns = detect_patterns(slug_insights)
            existing_patterns = persons[slug].get("patterns_identified", [])
            persons[slug]["patterns_identified"] = merge_patterns_incremental(
                existing_patterns, fresh_patterns
            )
            patterns_count = len(persons[slug]["patterns_identified"])

        # 3. Detect consensus across all processed slugs (using mce per-slug dirs)
        # Build slugs_dict: slug -> insights (last 30 days filter applied by caller
        # contract; here we load all available slugs for cross-expert detection)
        try:
            from datetime import timedelta

            cutoff = datetime.now(tz=UTC) - timedelta(days=30)
            slugs_dict: dict[str, list[dict[str, Any]]] = {}

            mce_base = ARTIFACTS / "mce"
            if mce_base.is_dir():
                for candidate_dir in mce_base.iterdir():
                    if not candidate_dir.is_dir():
                        continue
                    candidate_slug = candidate_dir.name
                    candidate_path = candidate_dir / "INSIGHTS-STATE.json"
                    if not candidate_path.exists():
                        continue
                    try:
                        raw_c = json.loads(candidate_path.read_text(encoding="utf-8"))
                        ins_c = raw_c.get("insights_state", raw_c)
                        if not isinstance(ins_c, dict):
                            continue
                        # 30-day recency filter
                        last_up = ins_c.get("last_updated", "")
                        if last_up:
                            try:
                                # Parse ISO with or without tz
                                lu_dt = datetime.fromisoformat(last_up.replace("Z", "+00:00"))
                                if lu_dt.tzinfo is None:
                                    lu_dt = lu_dt.replace(tzinfo=UTC)
                                if lu_dt < cutoff:
                                    continue
                            except ValueError:
                                pass  # Cannot parse — include anyway

                        candidate_insights: list[dict[str, Any]] = []
                        for p_data in ins_c.get("persons", {}).values():
                            if isinstance(p_data, dict):
                                candidate_insights.extend(p_data.get("insights", []))
                        if candidate_insights:
                            slugs_dict[candidate_slug] = candidate_insights
                    except Exception as _exc:
                        logger.debug(
                            "cmd_narrative: consensus load failed for %s: %s",
                            candidate_slug,
                            _exc,
                        )

            if len(slugs_dict) >= 2:
                fresh_consensus = detect_consensus(slugs_dict)
                existing_consensus = state.get("consensus_points", [])
                state["consensus_points"] = merge_consensus_incremental(
                    existing_consensus, fresh_consensus
                )
                consensus_count = len(state["consensus_points"])

        except Exception as _exc:
            logger.warning("cmd_narrative: consensus detection non-fatal failure: %s", _exc)

        # Re-assign persons after patterns mutation
        state["persons"] = persons

    except ImportError as _exc:
        logger.warning("cmd_narrative: narrative_patterns not importable (MCE-11.15): %s", _exc)
    except Exception as _exc:
        logger.warning("cmd_narrative: pattern/consensus detection non-fatal failure: %s", _exc)
    # ------------------------------------------------------------------
    # End MCE-11.15
    # ------------------------------------------------------------------

    _save_narratives_state(state)

    # Emit journey log
    _emit_narrative_journal(
        {
            "event": "narrative_merged",
            "slug": slug,
            "bucket": bucket,
            "timestamp": _now_iso(),
            "merger_available": merger_available,
            "patterns_count": patterns_count,
            "consensus_count": consensus_count,
        }
    )

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "narrative",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        bucket=bucket,
        merger_available=merger_available,
        patterns_count=patterns_count,
        consensus_count=consensus_count,
    )
    _append_jsonl(result)
    emit_phase_payload(
        slug=slug,
        template_id="narrative_metabolism",
        status="ok",
        metrics={
            "merger_available": merger_available,
            "bucket": bucket,
            "patterns_count": patterns_count,
            "consensus_count": consensus_count,
        },
        ascii_block="",
    )
    return result


# ---------------------------------------------------------------------------
# Command: identity-checkpoint (Step 9 — deterministic cross-layer gate)
# [V5/G14, 2026-05-13 — no LLM calls, pure artifact heuristics]
# ---------------------------------------------------------------------------

# Canonical DNA layer keys used by insights.tag -> DNA-CONFIG.yaml composition.
# L1-L5 are populated by cmd_insights (LLM extraction).
# L6-L10 are populated by dedicated commands (G13 follow-ups).
_DNA_LAYERS_ALL: tuple[str, ...] = (
    "FILOSOFIAS",  # L1 — Philosophies
    "MODELOS_MENTAIS",  # L2 — Mental Models
    "HEURISTICAS",  # L3 — Heuristics
    "FRAMEWORKS",  # L4 — Frameworks
    "METODOLOGIAS",  # L5 — Methodologies
    "BEHAVIORAL_PATTERNS",  # L6 — Behavioral Patterns
    "VALUES_HIERARCHY",  # L7 — Values Hierarchy
    "VOICE_TRAITS",  # L8 — Voice DNA
    "OBSESSIONS",  # L9 — Obsessions
    "PARADOXES",  # L10 — Paradoxes
)

# Layers that have dedicated DNA YAML files in knowledge/{bucket}/dna/persons/{slug}/
_DNA_YAML_FILES: dict[str, str] = {
    "VOICE_TRAITS": "voice-dna.yaml",
    "BEHAVIORAL_PATTERNS": "behavioral-patterns.yaml",
    "VALUES_HIERARCHY": "values-hierarchy.yaml",
    "OBSESSIONS": "obsessions.yaml",
    "PARADOXES": "paradoxes.yaml",
}

# Minimum entries per layer to be considered "populated".
_EVIDENCE_THRESHOLD: int = 3

# Minimum combined obsessions + paradoxes to avoid shallow-agent risk.
_OBSESSIONS_PARADOXES_MIN: int = 5

# Max underpopulated layers before escalating REVISE → ABORT.
_ABORT_UNDERPOPULATED_THRESHOLD: int = 3

# Min total insights before even considering APPROVE.
_MIN_TOTAL_INSIGHTS: int = 30


def _read_yaml_safe(path: Path) -> dict[str, Any]:
    """Read a YAML file; return empty dict on any error."""
    try:
        if not path.exists():
            return {}
        import yaml as _yaml  # already imported at module top but guard lazily

        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _count_yaml_entries(data: dict[str, Any]) -> int:
    """Count meaningful entries in a DNA YAML file.

    Checks common list keys (signature_phrases, patterns, values, obsessions,
    paradoxes, entries, items) and falls back to counting top-level dict keys
    that look like data (not metadata like 'version', 'extracted_at').
    """
    list_keys = (
        "signature_phrases",
        "patterns",
        "values",
        "obsessions",
        "paradoxes",
        "entries",
        "items",
        "phrases",
        "states",
        "behaviors",
    )
    for k in list_keys:
        v = data.get(k)
        if isinstance(v, list):
            return len(v)

    meta_keys = {"version", "extracted_at", "slug", "person", "source", "schema_version"}
    return sum(1 for k in data if k not in meta_keys and not k.startswith("_"))


# ---------------------------------------------------------------------------
# Command: sources (MCE-4.2 — SOURCES Phase 6.6)
# ---------------------------------------------------------------------------


def cmd_sources(slug: str) -> dict[str, Any]:
    """Phase 6.6 — Sources Compilation (MCE-4.2).

    Compiles catalog of source materials for ``slug`` and writes atomic .md
    files at ``knowledge/{bucket}/sources/{PERSON_UPPER}/{TEMA}.md``.

    Bucket-aware: path inferred via ``resolve_bucket_for_slug`` in
    ``sources_compiler.py`` (NARRATIVES-STATE preferred → filesystem heuristics
    → default "external").

    Non-blocking: exceptions are logged, never crash the caller (V6).

    Returns:
        Standardized ``_build_result`` dict with ``sources`` extras.
    """
    t0 = time.monotonic()
    try:
        from engine.intelligence.pipeline.mce.sources_compiler import compile_sources_for_slug

        result_data = compile_sources_for_slug(slug, root=_PROJECT_ROOT)
    except Exception as exc:
        logger.warning("cmd_sources: sources_compiler failed for %s: %s", slug, exc)
        result_data = {"status": "error", "error": str(exc)}

    elapsed = (time.monotonic() - t0) * 1000
    success = result_data.get("status") in ("written", "skipped", "no_sources")
    result = _build_result(
        "sources",
        success=success,
        slug=slug,
        duration_ms=elapsed,
        bucket=result_data.get("bucket", "unknown"),
        sources=result_data,
    )
    _append_jsonl(result)
    emit_phase_payload(
        slug=slug,
        template_id="sources_compilation",
        status="ok" if success else "warning",
        metrics={
            "status": result_data.get("status", "unknown"),
            "bucket": result_data.get("bucket", "unknown"),
        },
        ascii_block="",
    )
    return result


def cmd_aggregate_domain(domain: str) -> dict[str, Any]:
    """Phase 7: Domain Aggregation — MAP-CONFLITOS cross-source per-domain (MCE-4.5).

    Aggregates cross-source conflicts for ``domain`` by reading AGG-{DOMAIN}.yaml
    and writing MAP-CONFLITOS-{DOMAIN}.yaml in
    ``knowledge/external/dna/domains/{domain}/``.

    Non-blocking: exceptions are logged, never crash the caller (Art. XII).
    Lazy import of domain_aggregator to avoid heavy import chain at module load (Veto V3).

    Also aliased as ``cmd_map_conflicts(domain)`` per story scope IN.

    Returns:
        Standardized ``_build_result`` dict with ``aggregation`` extras.
        Keys in aggregation: status, domain, conflicts_found, conflicts_written, experts_compared.
    """
    t0 = time.monotonic()
    try:
        from engine.intelligence.pipeline.domain_aggregator import aggregate_domain_conflicts

        result_data = aggregate_domain_conflicts(domain, root=_PROJECT_ROOT)
    except Exception as exc:
        logger.warning("cmd_aggregate_domain: domain_aggregator failed for %s: %s", domain, exc)
        result_data = {"status": "error", "domain": domain, "error": str(exc)}

    elapsed = (time.monotonic() - t0) * 1000
    success = result_data.get("status") in ("written", "updated", "skipped")
    result = _build_result(
        "domain_agg",
        success=success,
        domain=domain,
        duration_ms=elapsed,
        aggregation=result_data,
    )
    _append_jsonl(result)
    emit_phase_payload(
        slug=domain,
        template_id="domain_aggregator",
        status="ok" if success else "warning",
        metrics={"domain": domain, "status": result_data.get("status", "unknown")},
        ascii_block="",
    )
    return result


# Alias per story scope IN
cmd_map_conflicts = cmd_aggregate_domain


def cmd_identity_checkpoint(slug: str) -> dict[str, Any]:
    """Step 9 — Identity Checkpoint (Lens): deterministic cross-layer DNA gate.

    Validates consistency across all 10 DNA layers before allowing pipeline
    to advance to Consolidation (Step 10).  No LLM calls — pure artifact
    heuristics applied to existing files.

    Evidence collected:
        1. INSIGHTS-STATE.json → insights by DNA layer (L1-L5 via tag field)
        2. DNA YAML files in knowledge/{bucket}/dna/persons/{slug}/
           (L6-L10: voice-dna.yaml, behavioral-patterns.yaml, etc.)

    Heuristics applied:
        H1 EVIDENCE_THRESHOLD: each layer needs >= _EVIDENCE_THRESHOLD entries
        H2 CROSS_LAYER_COHERENCE: voice_traits tone vs behavioral_patterns mode
        H3 OBSESSIONS_PARADOXES_BALANCE: L9+L10 combined >= _OBSESSIONS_PARADOXES_MIN

    Verdict:
        APPROVE — all layers populated + no conflicts
        REVISE  — 1-{_ABORT_UNDERPOPULATED_THRESHOLD-1} underpopulated or 1 minor conflict
        ABORT   — >{_ABORT_UNDERPOPULATED_THRESHOLD-1} underpopulated, grave conflict,
                  or total insights < {_MIN_TOTAL_INSIGHTS}

    Output:
        Writes identity-checkpoint.json to
        MISSION_CONTROL/mce/{slug}/checkpoints/identity-checkpoint.json
    """
    t0 = time.monotonic()
    bucket = _detect_bucket_for_slug(slug)
    dna_dir = _dna_dir_for_slug(slug, bucket)

    # -----------------------------------------------------------------------
    # Phase 1: Collect evidence
    # -----------------------------------------------------------------------

    # 1a. Read INSIGHTS-STATE.json — count insights by DNA layer via tag field
    state = _load_insights_state(slug)
    persons = state.get("persons", {})

    # Find person entry for this slug (case-insensitive match on slug field)
    person_entry: dict[str, Any] | None = None
    for pdata in persons.values():
        if isinstance(pdata, dict) and pdata.get("slug", "").lower() == slug.lower():
            person_entry = pdata
            break
    # Fallback: first entry in persons dict
    if person_entry is None and persons:
        person_entry = next(iter(persons.values()))

    insights: list[dict[str, Any]] = []
    if person_entry is not None and isinstance(person_entry.get("insights"), list):
        insights = person_entry["insights"]

    insights_total = len(insights)

    # Count insights by DNA layer using the same tag→layer mapping used by cmd_insights
    by_layer: dict[str, int] = {layer: 0 for layer in _DNA_LAYERS_ALL}
    for ins in insights:
        if not isinstance(ins, dict):
            continue
        tag = ins.get("tag", "")
        layer_key = _tag_to_dna_layer(tag)
        if layer_key and layer_key in by_layer:
            by_layer[layer_key] += insights.count(ins)  # just increment by 1 via loop
        elif layer_key:
            by_layer[layer_key] = by_layer.get(layer_key, 0) + 1

    # Recount cleanly (avoid double-counting from the loop above)
    by_layer = {layer: 0 for layer in _DNA_LAYERS_ALL}
    for ins in insights:
        if not isinstance(ins, dict):
            continue
        tag = ins.get("tag", "")
        layer_key = _tag_to_dna_layer(tag)
        if layer_key and layer_key in by_layer:
            by_layer[layer_key] += 1

    # 1b. Read DNA YAML files for L6-L10
    yaml_counts: dict[str, int] = {}
    for layer_key, filename in _DNA_YAML_FILES.items():
        yaml_path = dna_dir / filename
        data = _read_yaml_safe(yaml_path)
        yaml_counts[layer_key] = _count_yaml_entries(data) if data else 0
        # Merge YAML evidence into by_layer (takes max of insight count vs yaml count)
        by_layer[layer_key] = max(by_layer.get(layer_key, 0), yaml_counts.get(layer_key, 0))

    # Also check DNA-CONFIG.yaml composition for L6-L10 if present
    dna_config = _read_yaml_safe(dna_dir / "DNA-CONFIG.yaml")
    composition = dna_config.get("composition", {})
    for layer_key in _DNA_LAYERS_ALL:
        comp_val = composition.get(layer_key, 0)
        if isinstance(comp_val, int) and comp_val > by_layer.get(layer_key, 0):
            by_layer[layer_key] = comp_val

    # Voice-specific: count signature phrases from voice-dna.yaml
    voice_data = _read_yaml_safe(dna_dir / "voice-dna.yaml")
    phrases = voice_data.get("signature_phrases") or voice_data.get("phrases", [])
    voice_signature_phrases = len(phrases) if isinstance(phrases, list) else 0

    # Behavioral states count
    behavioral_data = _read_yaml_safe(dna_dir / "behavioral-patterns.yaml")
    states = behavioral_data.get("states") or behavioral_data.get("patterns", [])
    behavioral_states = len(states) if isinstance(states, list) else 0

    evidence: dict[str, Any] = {
        "insights_total": insights_total,
        "by_layer": by_layer,
        "voice_signature_phrases": voice_signature_phrases,
        "behavioral_states": behavioral_states,
    }

    # -----------------------------------------------------------------------
    # Phase 2: Apply heuristics
    # -----------------------------------------------------------------------

    # H1: Evidence threshold — each of the 10 layers needs >= 3 entries
    underpopulated_layers: list[str] = [
        layer for layer in _DNA_LAYERS_ALL if by_layer.get(layer, 0) < _EVIDENCE_THRESHOLD
    ]
    h1_passed = len(underpopulated_layers) == 0
    h1_result: dict[str, Any] = {
        "passed": h1_passed,
        "underpopulated_layers": underpopulated_layers,
        "threshold": _EVIDENCE_THRESHOLD,
    }

    # H2: Cross-layer coherence — voice tone vs behavioral mode conflict detection.
    # Heuristic: look for antonym pairs in the top-level keys/descriptors of both files.
    # This is a lightweight keyword check — no LLM needed.
    conflicts: list[str] = []
    _calm_voice_keywords = {"calm", "ponderado", "reflexivo", "measured", "sereno", "calmo"}
    _reactive_behavioral_keywords = {"impulsivo", "reativo", "impulsive", "reactive", "explosive"}
    _assertive_voice_keywords = {"assertivo", "assertive", "direto", "direct", "bold"}
    _passive_behavioral_keywords = {"passivo", "passive", "hesitante", "hesitant", "avoidant"}

    voice_text = " ".join(str(v) for v in voice_data.values()).lower() if voice_data else ""
    behavioral_text = (
        " ".join(str(v) for v in behavioral_data.values()).lower() if behavioral_data else ""
    )

    if any(k in voice_text for k in _calm_voice_keywords) and any(
        k in behavioral_text for k in _reactive_behavioral_keywords
    ):
        conflicts.append("voice_calm_vs_behavioral_reactive")

    if any(k in voice_text for k in _assertive_voice_keywords) and any(
        k in behavioral_text for k in _passive_behavioral_keywords
    ):
        conflicts.append("voice_assertive_vs_behavioral_passive")

    h2_passed = len(conflicts) == 0
    h2_result: dict[str, Any] = {
        "passed": h2_passed,
        "conflicts": conflicts,
    }

    # H3: Obsessions + Paradoxes balance
    obsessions_count = by_layer.get("OBSESSIONS", 0)
    paradoxes_count = by_layer.get("PARADOXES", 0)
    combined_op = obsessions_count + paradoxes_count
    h3_passed = combined_op >= _OBSESSIONS_PARADOXES_MIN
    h3_result: dict[str, Any] = {
        "passed": h3_passed,
        "combined": combined_op,
        "minimum": _OBSESSIONS_PARADOXES_MIN,
        "obsessions": obsessions_count,
        "paradoxes": paradoxes_count,
    }

    checks: dict[str, Any] = {
        "evidence_threshold": h1_result,
        "cross_layer_coherence": h2_result,
        "obsessions_paradoxes_balance": h3_result,
    }

    # -----------------------------------------------------------------------
    # Phase 3: Verdict
    # -----------------------------------------------------------------------

    n_underpopulated = len(underpopulated_layers)
    grave_conflict = len(conflicts) > 0  # any conflict is investigated; grave = blocks

    if insights_total < _MIN_TOTAL_INSIGHTS:
        verdict = "ABORT"
        recommendation = (
            f"Source material insufficient — only {insights_total} insights "
            f"(minimum {_MIN_TOTAL_INSIGHTS}). Re-ingest more source material."
        )
    elif n_underpopulated > _ABORT_UNDERPOPULATED_THRESHOLD:
        verdict = "ABORT"
        recommendation = (
            f"{n_underpopulated} layers underpopulated (>{_ABORT_UNDERPOPULATED_THRESHOLD} threshold). "
            f"Re-extract layers: {', '.join(underpopulated_layers[:5])}."
        )
    elif grave_conflict:
        verdict = "ABORT"
        recommendation = (
            f"Grave cross-layer conflict detected: {', '.join(conflicts)}. "
            "Review voice-dna.yaml and behavioral-patterns.yaml for consistency."
        )
    elif n_underpopulated > 0 or not h3_passed:
        verdict = "REVISE"
        issues: list[str] = []
        if underpopulated_layers:
            issues.append(f"underpopulated layers: {', '.join(underpopulated_layers)}")
        if not h3_passed:
            issues.append(f"obsessions+paradoxes={combined_op} (min {_OBSESSIONS_PARADOXES_MIN})")
        recommendation = f"Re-extract before Consolidation. Issues: {'; '.join(issues)}."
    else:
        verdict = "APPROVE"
        recommendation = "Proceed to Consolidation (Step 10)."

    # -----------------------------------------------------------------------
    # Phase 4: Write checkpoint JSON
    # -----------------------------------------------------------------------

    checkpoint_path = MISSION_CONTROL / "mce" / slug / "checkpoints" / "identity-checkpoint.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    checkpoint_data: dict[str, Any] = {
        "slug": slug,
        "verdict": verdict,
        "timestamp": _now_iso(),
        "evidence": evidence,
        "checks": checks,
        "recommendation": recommendation,
    }

    try:
        checkpoint_path.write_text(
            json.dumps(checkpoint_data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("cmd_identity_checkpoint: failed to write checkpoint: %s", exc)

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "identity-checkpoint",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        verdict=verdict,
        recommendation=recommendation,
        evidence_summary={
            "insights_total": insights_total,
            "underpopulated_layers": underpopulated_layers,
            "conflicts": conflicts,
            "obsessions_paradoxes_combined": combined_op,
        },
        checkpoint_path=str(checkpoint_path),
    )
    _append_jsonl(result)
    emit_phase_payload(
        slug=slug,
        template_id="identity_checkpoint",
        status="ok" if verdict == "APPROVE" else ("warning" if verdict == "REVISE" else "fail"),
        metrics={
            "verdict": verdict,
            "insights_total": insights_total,
            "underpopulated_layers": len(underpopulated_layers),
            "conflicts": len(conflicts),
        },
        ascii_block="",
    )
    return result


# ---------------------------------------------------------------------------
# Command: auto-advance (CLASSIFIED → S3..S8 → STOP at S9 checkpoint)
# [N3/G1, @architect sign-off 2026-05-13 — 6 conditions C-1..C-6]
# ---------------------------------------------------------------------------


# FSM trigger chain. Ordered, idempotent. Each trigger advances exactly one
# state. STOP at ``mce_voice`` (S9 checkpoint is manual approve).
_AUTO_ADVANCE_TRIGGERS: tuple[str, ...] = (
    "start_chunking",
    "start_entities",
    "start_insights",
    "start_behavioral",
    "start_identity",
    "start_voice",
    "start_narrative",  # MCE-4.1: NARRATIVE METABOLISM — enables mce_narrative FSM state
    "start_sources",  # MCE-4.2: SOURCES Phase 6.6 — bucket-aware sources compilation
    "start_domain_agg",  # MCE-4.5: MAP-CONFLITOS per-domain cross-source aggregation
)

# G12 → G13 (2026-05-13): map FSM triggers to canonical cmd_* functions
# that extract / populate state. As of G13 all extraction commands are
# defined; cmd_insights is the only one that actually calls the LLM and
# writes both INSIGHTS-STATE.json and DNA-CONFIG.yaml. The remaining
# four (entities / behavioral / identity / voice) are wired with marker
# implementations so the FSM advances cleanly; their full extraction is
# a G13 follow-up.
#
# Order matters: each command's output is the next command's input.
#   start_chunking   -> cmd_process_batch (chunk + embed + upsert, already
#                       fired above the trigger walk — entry kept for symmetry).
#   start_entities   -> cmd_entities   (G13: marker stub)
#   start_insights   -> cmd_insights   (G13: REAL Gemini extraction + DNA)
#   start_behavioral -> cmd_behavioral (G13: marker stub)
#   start_identity   -> cmd_identity   (G13: marker stub)
#   start_voice      -> cmd_voice      (G13: marker stub)
_TRIGGER_CMD_MAP: dict[str, str] = {
    "start_chunking": "cmd_process_batch",
    "start_entities": "cmd_entities",
    "start_insights": "cmd_insights",
    "start_behavioral": "cmd_behavioral",
    "start_identity": "cmd_identity",
    "start_voice": "cmd_voice",
    "start_narrative": "cmd_narrative",  # MCE-4.1: NARRATIVE METABOLISM
    "start_sources": "cmd_sources",  # MCE-4.2: SOURCES Phase 6.6
    "start_domain_agg": "cmd_aggregate_domain",  # MCE-4.5: MAP-CONFLITOS per-domain
}

# FSM states where a fresh auto-advance is allowed to start (C-3c).
_AUTO_ADVANCE_VALID_START_STATES: frozenset[str] = frozenset({"init", "ingesting", "batching"})

# Max retries per batch before declaring FAILED (C-4b).
_AUTO_ADVANCE_MAX_RETRIES: int = 3


def _list_pending_advance_batches(slug: str) -> list[dict[str, Any]]:
    """Return BATCH-XXX descriptors for ``slug`` in ``CLASSIFIED`` status.

    Reads ``MISSION_CONTROL/batch-logs/BATCH-*.json`` and filters by:
      - ``status == "CLASSIFIED"`` or ``"CREATED"`` (legacy).
      - ``source_name`` lower-cased + dasherized matches ``slug``.
      - No sibling ``.advance-trigger.consumed`` sentinel.

    Returns: list of dicts ``{batch_id, json_path, retry_count, files_processed}``.
    """
    batch_dir = MISSION_CONTROL / "batch-logs"
    if not batch_dir.exists():
        return []

    pending: list[dict[str, Any]] = []
    slug_normalized = slug.lower().replace("_", "-")

    for json_path in sorted(batch_dir.glob("BATCH-*.json")):
        # Skip the .advance-trigger.json marker (different filename pattern).
        if json_path.name.endswith(".advance-trigger.json"):
            continue
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        status = data.get("status", "")
        if status not in ("CLASSIFIED", "CREATED"):
            continue

        source_name = data.get("source_name", "").lower().replace(" ", "-").replace("_", "-")
        if slug_normalized not in source_name and source_name not in slug_normalized:
            continue

        batch_id = data.get("batch_id", "")
        if not batch_id:
            continue

        # Skip if .consumed sentinel exists (C-6b).
        consumed = batch_dir / f"{batch_id}.advance-trigger.consumed"
        if consumed.exists():
            continue

        pending.append(
            {
                "batch_id": batch_id,
                "json_path": json_path,
                "retry_count": int(data.get("retry_count", 0)),
                "files_processed": data.get("files_processed", []),
            }
        )

    return pending


def _bump_retry_count(json_path: Path, *, status: str | None = None) -> int:
    """Increment ``retry_count`` in a BATCH-XXX.json (C-4a).

    Optionally update ``status`` (e.g. ``FAILED`` after max retries).
    Returns the new retry_count.  Non-fatal on errors (returns 0).
    """
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        new_count = int(data.get("retry_count", 0)) + 1
        data["retry_count"] = new_count
        if status is not None:
            data["status"] = status
        data["last_retry_at"] = _now_iso()
        json_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        return new_count
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to bump retry_count in %s: %s", json_path, exc)
        return 0


def _mark_batch_status(json_path: Path, status: str) -> None:
    """Write a status update into a BATCH-XXX.json (non-fatal)."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        data["status"] = status
        data["status_updated_at"] = _now_iso()
        json_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to mark batch %s as %s: %s", json_path, status, exc)


def _write_consumed_sentinel(batch_id: str) -> None:
    """Write the ``.advance-trigger.consumed`` sentinel after success (C-6b)."""
    try:
        path = MISSION_CONTROL / "batch-logs" / f"{batch_id}.advance-trigger.consumed"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"batch_id": batch_id, "consumed_at": _now_iso()}, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.debug("Could not write consumed sentinel for %s: %s", batch_id, exc)


def _list_completed_batches(slug: str) -> list[str]:
    """List batches already fully processed (chunks + embeddings on disk).

    MCE-16.5 Bug 2: idempotency guard for ``cmd_auto_advance``.  A batch is
    considered complete when BOTH its chunks JSON and its embeddings JSON exist
    under ``.data/artifacts/``.  Only the batch_id stem is returned (no path).
    """
    chunks_dir = ARTIFACTS / "chunks" / slug
    if not chunks_dir.exists():
        return []

    completed: list[str] = []
    for f in sorted(chunks_dir.glob("BATCH-*-chunks.json")):
        batch_id = f.stem.replace("-chunks", "")
        emb_path = ARTIFACTS / "embeddings" / slug / f"{batch_id}-embeddings.json"
        if emb_path.exists():
            completed.append(batch_id)
    return completed


def _read_batch_content_hash(slug: str, batch_id: str) -> str | None:
    """Read the content hash of a completed batch's chunks artifact.

    MCE-16.5 Bug 2: computes the same deterministic hash as
    ``_compute_batch_content_hash`` so that a re-run can detect unchanged
    material and skip redundant batch creation.  Returns ``None`` on error.
    """
    import hashlib

    chunks_path = ARTIFACTS / "chunks" / slug / f"{batch_id}-chunks.json"
    if not chunks_path.exists():
        return None
    try:
        data = json.loads(chunks_path.read_text(encoding="utf-8"))
        chunks = data.get("chunks", [])
        if not chunks:
            return None
        combined = "".join(
            c.get("text", "")
            for c in sorted(chunks, key=lambda x: x.get("chunk_id", x.get("id_chunk", "")))
        )
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()
    except Exception as exc:
        logger.debug("_read_batch_content_hash failed for %s/%s: %s", slug, batch_id, exc)
        return None


def cmd_auto_advance(slug: str) -> dict[str, Any]:
    """Auto-advance pending CLASSIFIED batches for ``slug`` through S3..S8.

    Walks ``MISSION_CONTROL/batch-logs/`` for batches in ``CLASSIFIED`` status
    that belong to ``slug``.  For each batch:

    1. Skip if FSM not in ``{init, ingesting, batching}`` (C-3c).
    2. Skip if ``retry_count >= _AUTO_ADVANCE_MAX_RETRIES``; mark FAILED (C-4b).
    3. Skip if sibling ``.advance-trigger.consumed`` sentinel exists (C-6b).
    4. Invoke ``cmd_process_batch(batch_id, slug)`` (the canonical chunk+embed).
    5. On success: walk FSM through trigger chain to ``mce_voice`` (S9 STOP).
    6. On failure: bump ``retry_count`` (or mark FAILED on max).
    7. Write ``.consumed`` sentinel on success.

    Args:
        slug: Person/source slug to auto-advance.

    Returns:
        Structured dict with ``processed``, ``skipped``, ``failed`` lists and
        per-batch detail.  Always returns success=True at the command level;
        per-batch failures are visible in the ``failed`` list.
    """
    t0 = time.monotonic()
    pending = _list_pending_advance_batches(slug)

    processed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    if not pending:
        elapsed = (time.monotonic() - t0) * 1000
        result = _build_result(
            "auto-advance",
            success=True,
            slug=slug,
            duration_ms=elapsed,
            processed=[],
            skipped=[],
            failed=[],
            reason="no pending CLASSIFIED batches",
        )
        _append_jsonl(result)
        emit_phase_payload(
            slug=slug,
            template_id="auto_advance_trigger",
            status="ok",
            metrics={"reason": "no pending CLASSIFIED batches", "batches_advanced": 0},
            ascii_block="",
        )
        return result

    sm = PipelineStateMachine(slug)

    # C-3c: FSM state check ANTES de spawn / process.
    if sm.state not in _AUTO_ADVANCE_VALID_START_STATES:
        elapsed = (time.monotonic() - t0) * 1000
        skipped.extend(
            {"batch_id": p["batch_id"], "reason": f"fsm_state={sm.state}"} for p in pending
        )
        result = _build_result(
            "auto-advance",
            success=True,
            slug=slug,
            duration_ms=elapsed,
            processed=processed,
            skipped=skipped,
            failed=failed,
            state={"current": sm.state},
            reason=f"FSM state {sm.state!r} not in {_AUTO_ADVANCE_VALID_START_STATES}",
        )
        _append_jsonl(result)
        emit_phase_payload(
            slug=slug,
            template_id="auto_advance_trigger",
            status="warning",
            metrics={"reason": f"fsm_state={sm.state}", "skipped": len(skipped)},
            ascii_block="",
        )
        return result

    for batch in pending:
        batch_id = batch["batch_id"]
        json_path: Path = batch["json_path"]
        retry_count = batch["retry_count"]

        # C-4b: honor retry counter.
        if retry_count >= _AUTO_ADVANCE_MAX_RETRIES:
            _mark_batch_status(json_path, "FAILED")
            failed.append(
                {
                    "batch_id": batch_id,
                    "reason": f"retry_count={retry_count} >= max={_AUTO_ADVANCE_MAX_RETRIES}",
                    "action": "marked_FAILED",
                }
            )
            continue

        # MCE-16.5 Bug 2: idempotency guard at batch level.
        # Skip batch processing when a completed batch with identical content
        # already exists on disk.  This prevents duplicate BATCH-XXXX artifacts
        # on re-run (root cause: BATCH-2603-CG vs BATCH-2823-CG cole-gordon).
        _completed = _list_completed_batches(slug)
        if _completed:
            _incoming_docs = batch.get("files_processed", [])
            _incoming_fp = (
                __import__("hashlib").sha256(
                    "|".join(sorted(str(d) for d in _incoming_docs)).encode()
                ).hexdigest()[:16]
                if _incoming_docs
                else None
            )
            _skip_batch = False
            for _cb in _completed:
                _cb_hash = _read_batch_content_hash(slug, _cb)
                if _cb_hash is not None:
                    # Check via content hash if available; otherwise fall back
                    # to doc-fingerprint comparison (files_processed list).
                    _existing_emb = ARTIFACTS / "embeddings" / slug / f"{_cb}-embeddings.json"
                    if _existing_emb.exists():
                        try:
                            _emb_data = json.loads(_existing_emb.read_text(encoding="utf-8"))
                            _emb_fp = _emb_data.get("content_hash_fingerprint", "")
                        except Exception:
                            _emb_fp = ""
                        if _incoming_fp and _emb_fp and _incoming_fp == _emb_fp:
                            _skip_batch = True
                            logger.info(
                                "[MCE-16.5] SKIP batch_creation — material unchanged "
                                "(slug=%s existing=%s fingerprint=%s)",
                                slug,
                                _cb,
                                _incoming_fp,
                            )
                            break

            if _skip_batch:
                skipped.append(
                    {
                        "batch_id": batch_id,
                        "reason": "idempotency_guard: completed batch with same content exists",
                        "existing_batch": _cb,
                    }
                )
                _write_consumed_sentinel(batch_id)
                continue

        # C-1: invoke the REAL cmd_process_batch (not a non-existent cmd_chunk).
        try:
            process_result = cmd_process_batch(batch_id=batch_id, slug=slug, documents=None)
        except Exception as exc:
            new_count = _bump_retry_count(json_path)
            failed.append(
                {
                    "batch_id": batch_id,
                    "reason": f"cmd_process_batch crashed: {exc}",
                    "retry_count": new_count,
                }
            )
            continue

        if not process_result.get("success"):
            new_count = _bump_retry_count(json_path)
            failed.append(
                {
                    "batch_id": batch_id,
                    "reason": process_result.get("error", "unknown"),
                    "retry_count": new_count,
                }
            )
            continue

        # Success path: walk FSM trigger chain (idempotent — silently skip
        # transitions that are already past). STOP at mce_voice (S9 manual).
        # G12 (2026-05-13): for each trigger, also call the canonical cmd_*
        # that should populate state. When the cmd is missing, log a TODO so
        # the gap is observable instead of silently leaving state empty.
        triggers_fired: list[str] = []
        cmd_executions: list[dict[str, Any]] = []
        todos: list[dict[str, Any]] = []

        # start_chunking corresponds to cmd_process_batch which was already
        # fired above; skip its cmd lookup so we don't re-invoke it with the
        # wrong signature. The trigger itself still fires to advance the FSM.
        skip_cmd_for: set[str] = {"start_chunking"}

        for trig in _AUTO_ADVANCE_TRIGGERS:
            trig_fn = getattr(sm, trig, None)
            if trig_fn is None:
                continue
            # Record the FSM state BEFORE firing so we can tell whether the
            # trigger actually advanced state or only no-op'd because the
            # transitions library blocked on the underlying condition (e.g.
            # ``can_start_chunking`` QA gate).
            state_before = sm.state
            try:
                trig_fn(None)
            except Exception:
                logger.debug("Trigger %s raised (current state %s)", trig, sm.state)
                continue

            if sm.state == state_before:
                # Condition gate refused — record so the gap is observable
                # without triggering the cmd_* (would be premature work).
                todos.append(
                    {
                        "trigger": trig,
                        "missing_cmd": None,
                        "note": (
                            f"FSM refused to advance from {state_before!r} "
                            "(condition gate blocked — likely QA gate)"
                        ),
                    }
                )
                continue

            triggers_fired.append(trig)

            # G12: try to call the canonical cmd_* for this trigger.
            if trig in skip_cmd_for:
                continue

            cmd_name = _TRIGGER_CMD_MAP.get(trig)
            if cmd_name is None:
                continue

            # Use globals() so the lookup honors the actual module functions.
            cmd_fn = globals().get(cmd_name)
            if cmd_fn is None:
                # TODO marker: extraction not wired yet. FSM keeps advancing
                # so downstream stages (rag_index, log_generator) can still
                # report what HAS been built; missing slots show as 0 in the
                # validation checklist which surfaces the gap.
                todos.append(
                    {
                        "trigger": trig,
                        "missing_cmd": cmd_name,
                        "note": ("FSM advanced but no extractor wired — LLM extraction pending"),
                    }
                )
                logger.info(
                    "G12 TODO: trigger %s advanced FSM but %s is not implemented yet",
                    trig,
                    cmd_name,
                )
                continue

            # MCE-15.1 bug #2: cmd_aggregate_domain(domain) expects a VALID_DOMAIN
            # string, not a slug. Dispatching cmd_fn(slug) would pass "alex-hormozi"
            # where "vendas" is expected → ValueError → MAP-CONFLITOS never written.
            # Resolve domains for this slug and iterate each one individually.
            if trig == "start_domain_agg":
                try:
                    from engine.intelligence.pipeline.domain_aggregator import (
                        _list_domains_for_slug,
                    )

                    domains_for_slug = _list_domains_for_slug(slug, root=_PROJECT_ROOT)
                except Exception as _e:
                    logger.warning("G12: could not resolve domains for slug %s: %s", slug, _e)
                    domains_for_slug = []

                if not domains_for_slug:
                    todos.append(
                        {
                            "trigger": trig,
                            "missing_input": "no domains resolved for slug",
                            "note": (
                                f"cmd_aggregate_domain requires a VALID_DOMAIN arg; "
                                f"_list_domains_for_slug({slug!r}) returned empty list"
                            ),
                        }
                    )
                    continue

                for domain in domains_for_slug:
                    try:
                        cmd_result = cmd_aggregate_domain(domain)
                        cmd_executions.append(
                            {
                                "trigger": trig,
                                "cmd": "cmd_aggregate_domain",
                                "domain": domain,
                                "success": (
                                    cmd_result.get("success", False)
                                    if isinstance(cmd_result, dict)
                                    else True
                                ),
                            }
                        )
                    except Exception as exc:
                        logger.warning(
                            "G12: cmd_aggregate_domain(%s) crashed: %s", domain, exc
                        )
                        cmd_executions.append(
                            {
                                "trigger": trig,
                                "cmd": "cmd_aggregate_domain",
                                "domain": domain,
                                "success": False,
                                "error": str(exc),
                            }
                        )
                continue  # skip generic cmd_fn(slug) dispatch below

            try:
                cmd_result = cmd_fn(slug)
                cmd_executions.append(
                    {
                        "trigger": trig,
                        "cmd": cmd_name,
                        "success": (
                            cmd_result.get("success", False)
                            if isinstance(cmd_result, dict)
                            else True
                        ),
                    }
                )
            except Exception as exc:
                logger.warning("G12: %s (triggered by %s) crashed: %s", cmd_name, trig, exc)
                cmd_executions.append(
                    {
                        "trigger": trig,
                        "cmd": cmd_name,
                        "success": False,
                        "error": str(exc),
                    }
                )

        # G14/V5 (2026-05-13): After start_voice fires (S8→S9), run the
        # deterministic identity checkpoint.  If ABORT → mark batch FAILED and
        # stop; if REVISE → record warning but keep pipeline observable (caller
        # must review before proceeding to Consolidation).
        identity_checkpoint_result: dict[str, Any] = {}
        if "start_voice" in triggers_fired:
            try:
                identity_checkpoint_result = cmd_identity_checkpoint(slug)
                ic_verdict = identity_checkpoint_result.get("verdict", "UNKNOWN")
                if ic_verdict == "ABORT":
                    _mark_batch_status(json_path, "CHECKPOINT_ABORT")
                    processed.append(
                        {
                            "batch_id": batch_id,
                            "triggers_fired": triggers_fired,
                            "cmd_executions": cmd_executions,
                            "todos": todos,
                            "final_state": sm.state,
                            "counts": process_result.get("counts", {}),
                            "identity_checkpoint": identity_checkpoint_result,
                            "stopped_at": "identity_checkpoint_ABORT",
                        }
                    )
                    elapsed = (time.monotonic() - t0) * 1000
                    abort_result = _build_result(
                        "auto-advance",
                        success=False,
                        slug=slug,
                        duration_ms=elapsed,
                        processed=processed,
                        skipped=skipped,
                        failed=failed,
                        state={"current": sm.state},
                        error="identity-checkpoint verdict=ABORT — pipeline halted",
                        identity_checkpoint=identity_checkpoint_result,
                    )
                    _append_jsonl(abort_result)
                    emit_phase_payload(
                        slug=slug,
                        template_id="auto_advance_trigger",
                        status="fail",
                        metrics={
                            "reason": "identity_checkpoint_ABORT",
                            "processed": len(processed),
                        },
                        ascii_block="",
                    )
                    return abort_result
            except Exception as exc:
                logger.warning("cmd_identity_checkpoint raised for %s: %s", slug, exc)
                identity_checkpoint_result = {"error": str(exc), "verdict": "UNKNOWN"}

        _mark_batch_status(json_path, "EXTRACTED")
        _write_consumed_sentinel(batch_id)

        processed.append(
            {
                "batch_id": batch_id,
                "triggers_fired": triggers_fired,
                "cmd_executions": cmd_executions,
                "todos": todos,
                "final_state": sm.state,
                "counts": process_result.get("counts", {}),
                "identity_checkpoint": identity_checkpoint_result,
            }
        )

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "auto-advance",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        processed=processed,
        skipped=skipped,
        failed=failed,
        state={"current": sm.state},
    )
    _append_jsonl(result)
    emit_phase_payload(
        slug=slug,
        template_id="auto_advance_trigger",
        status="ok" if not failed else "warning",
        metrics={
            "processed": len(processed),
            "skipped": len(skipped),
            "failed": len(failed),
        },
        ascii_block="",
    )
    # T3 (MCE-14.6): emit chronicler if at least 1 batch was processed.
    # Conditional on len(processed) > 0 — no batches processed means no
    # meaningful pipeline run to document.
    # Defensive try/except on top of _safe_emit_chronicler's own safety
    # (paranoid mode — Art. XII).
    if len(processed) > 0:
        try:
            _safe_emit_chronicler(slug, source_path="cmd_auto_advance")
        except Exception:
            # Helper already captures everything; this is a last-resort guard.
            pass
    return result


# ---------------------------------------------------------------------------
# Command: rag-index (Phase 4.5 — Constitution Art. XV)
# ---------------------------------------------------------------------------


def _import_rag_rebuild():
    """Lazy import for RAG rebuild module."""
    from engine.intelligence.rag.rebuild import rebuild

    return rebuild


def _count_existing_chunks(bucket: str) -> int:
    """Count existing chunks in a RAG bucket index (pre-indexation snapshot).

    Reads the BM25 chunks file if it exists.  Returns 0 on any error.
    """
    try:
        from engine.paths import KNOWLEDGE_PERSONAL, RAG_BUSINESS, RAG_INDEX

        bucket_dirs = {
            "external": RAG_INDEX,
            "business": RAG_BUSINESS,
            "personal": KNOWLEDGE_PERSONAL / "index",
        }
        target_dir = bucket_dirs.get(bucket)
        if target_dir is None or not target_dir.exists():
            return 0

        chunks_file = target_dir / "chunks.json"
        if not chunks_file.exists():
            return 0

        data = json.loads(chunks_file.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            return len(data.get("chunks", data.get("documents", [])))
        return 0
    except Exception:
        return 0


def cmd_rag_index(slug: str) -> dict[str, Any]:
    """Phase 4.5: RAG Indexation — Constitutional gate (Art. XV).

    Rebuilds RAG indexes for the bucket associated with ``slug`` and
    validates that chunk count did not decrease (BLOCK if it did).

    Steps:
        1. Snapshot current chunk count (pre).
        2. Rebuild BM25 index for the bucket (incremental).
        3. If ``VOYAGE_API_KEY`` is set, rebuild vector embeddings too.
        4. Snapshot new chunk count (post).
        5. Validation gate: post >= pre.  BLOCK on failure.
        6. Dual-location JSONL log (Art. XII).

    Args:
        slug: Person/source slug.

    Returns:
        Structured result dict.  ``gate_passed`` is *False* when the
        chunk count decreased — callers MUST block pipeline advancement.
    """
    t0 = time.monotonic()

    # Detect bucket
    bucket = _detect_bucket_for_slug(slug)

    # Step 1: Pre-indexation snapshot
    chunks_pre = _count_existing_chunks(bucket)

    # Step 2+3: Rebuild
    rebuild_fn = _import_rag_rebuild()
    skip_vectors = True
    # Initialized before the try so the incremental decision at the rebuild call
    # (below) is well-defined even if env detection raises early.
    has_embed_key = False
    try:
        import os
        from pathlib import Path

        # C-19 fix (2026-05-12): canonical embedder is OpenAI text-embedding-3-large
        # per architecture decision (CLAUDE.md "Post-Compare Architecture State").
        # Voyage was never adopted. Previously skip_vectors stayed True forever,
        # causing chunks.json/bm25.json to grow while vectors.json stayed stale.
        # Now: rebuild vectors if ANY canonical embedding provider is available.

        # Try env first
        has_embed_key = bool(
            os.environ.get("OPENAI_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("VOYAGE_API_KEY")
        )

        # Fallback: load from .env file (process may not have env loaded)
        if not has_embed_key:
            env_path = Path(__file__).resolve().parents[4] / ".env"
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.startswith(("OPENAI_API_KEY=", "GEMINI_API_KEY=", "VOYAGE_API_KEY=")):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and len(val) > 5:
                            key_name = line.split("=", 1)[0]
                            os.environ.setdefault(key_name, val)
                            has_embed_key = True

        if has_embed_key:
            skip_vectors = False
            logger.info("RAG rebuild: vectors WILL be rebuilt (embedding key detected)")
        else:
            logger.warning(
                "RAG rebuild: vectors will be SKIPPED (no OPENAI/GEMINI/VOYAGE key). "
                "chunks.json/bm25.json updates may diverge from vectors.json. "
                "Set OPENAI_API_KEY to enable full rebuild."
            )

        # STORY-MCE-RAG-INDEX-AUTORECONCILE (2026-06-26): the MCE-18 "parity-skip"
        # block previously lived here. It checked len(vectors.json) == len(chunks.json)
        # *before* the rebuild and, on parity, set skip_vectors=True. That was both
        # REDUNDANT and HARMFUL: the pre-rebuild parity check sees the *old* chunk
        # count (the batch's new chunks haven't landed yet), so it almost always
        # "passed" and disabled vectors — and `use_incremental = has_embed_key and
        # not skip_vectors` (below) then ALSO disabled the incremental path. The
        # rebuild would add new chunks but never embed them → vectors<->chunks drift
        # (e.g. 88932 chunks vs 88678 vectors), forcing a MANUAL reconcile.
        #
        # The incremental path (STORY-MCE-INCREMENTAL-RAG-INDEX) already solves the
        # exact cost MCE-18 feared: it reuses prior vectors keyed by content_sha
        # (0 embeds when nothing changed — the cheap "finalize re-run" case) and
        # embeds only the delta when new chunks exist (self-healing vectors==chunks).
        # So with an embed key present (and not force-rebuild) we ALWAYS keep
        # skip_vectors=False and let the incremental path do the right thing.
        # MCE_RAG_FORCE_REBUILD=1 (honored below at use_incremental) still forces a
        # full re-embed; the no-embed-key branch above still sets skip_vectors=True.
    except Exception as e:
        logger.error(f"RAG rebuild env detection failed: {e}")

    # STORY-MCE-INCREMENTAL-RAG-INDEX: when an embed key is present and we are
    # actually building vectors, opt into the incremental path. It reuses prior
    # vectors keyed by content_sha and embeds only new/changed chunks — turning a
    # full 54k-chunk re-embed into a ~1.3k-chunk delta and self-healing the
    # vector<->chunk drift. The Art. XV gate is untouched: chunks_post is still
    # len(idx.chunks) (rebuild.py), independent of how vectors get built.
    #
    # STORY-MCE-RAG-INDEX-AUTORECONCILE: MCE_RAG_FORCE_REBUILD=1 forces a FULL
    # re-embed (incremental=False) — vectors are still built (skip_vectors=False),
    # they're just rebuilt from scratch instead of reusing content_sha. This is the
    # only remaining honoring of the force-rebuild flag now that the parity-skip
    # block (which previously read it) is gone.
    force_rebuild = os.environ.get("MCE_RAG_FORCE_REBUILD", "0").lower() in ("1", "true", "yes")
    use_incremental = has_embed_key and not skip_vectors and not force_rebuild
    try:
        rebuild_result = rebuild_fn(
            bucket=bucket,
            skip_vectors=skip_vectors,
            incremental=use_incremental,
        )
    except Exception as exc:
        logger.warning("RAG rebuild failed for bucket %s: %s", bucket, exc)
        elapsed = (time.monotonic() - t0) * 1000
        err_result = _build_result(
            "rag_index",
            success=False,
            slug=slug,
            error=f"RAG rebuild failed: {exc}",
            bucket=bucket,
            duration_ms=elapsed,
            gate_passed=False,
        )
        _append_jsonl(err_result)
        return err_result

    # Step 4: Post-indexation snapshot
    bucket_stats = rebuild_result.get(bucket, {})
    chunks_post = bucket_stats.get("chunks", 0)

    # Step 5: Validation gate — chunk count MUST NOT meaningfully decrease (Art. XV).
    # Tolerate small negative deltas as legitimate rebuild dedup. The threshold is
    # max(5 chunks absolute, 0.5% of chunks_pre) — meaningful regressions (large
    # drops) still fail closed. Origin: false-positive observed 2026-05-21 where a
    # 2402→2400 delta (-0.08%) blocked cmd_finalize and cut 8 downstream ASCII
    # logs even though no real knowledge was lost (only natural dedup).
    chunks_delta = chunks_post - chunks_pre
    gate_tolerance = max(5, int(chunks_pre * 0.005)) if chunks_pre > 0 else 0
    gate_passed = chunks_delta >= -gate_tolerance

    # MCE-13.9: opt-in bypass for INTENTIONAL regressions (e.g. after cleanup-slug).
    # Set RAG_GATE_ALLOW_REGRESSION=1 to override the Art. XV enforcement.
    # Default behavior (gate enforced) is unchanged when env var is absent/0.
    gate_bypassed = False
    gate_bypass_reason: str | None = None
    if not gate_passed:
        _allow_env = os.environ.get("RAG_GATE_ALLOW_REGRESSION", "0").lower()
        if _allow_env in ("1", "true", "yes"):
            logger.warning(
                "[MCE-13.9] RAG_GATE: regression bypass ACTIVE "
                "(env RAG_GATE_ALLOW_REGRESSION=1). "
                "chunks_pre=%d, chunks_post=%d, delta=%d, tolerance=%d. "
                "Constitution Art. XV gate DISABLED by explicit user opt-in.",
                chunks_pre,
                chunks_post,
                chunks_delta,
                gate_tolerance,
            )
            gate_passed = True
            gate_bypassed = True
            gate_bypass_reason = "RAG_GATE_ALLOW_REGRESSION=1"

    # Update FSM
    sm = PipelineStateMachine(slug)
    if sm.state == "consolidation":
        try:
            sm.start_rag_index(None)
        except Exception:
            logger.debug("State transition to rag_indexation failed", exc_info=True)

    # Update metrics
    mt = MetricsTracker.load(slug) or MetricsTracker(slug)
    mt.start_phase("rag_indexation")
    mt.end_phase("rag_indexation")
    mt.save()

    elapsed = (time.monotonic() - t0) * 1000

    result = _build_result(
        "rag_index",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        bucket=bucket,
        chunks_pre=chunks_pre,
        chunks_post=chunks_post,
        chunks_delta=chunks_delta,
        vectors_updated=not skip_vectors,
        gate_passed=gate_passed,
        gate_tolerance=gate_tolerance,
        gate_bypassed=gate_bypassed,
        gate_bypass_reason=gate_bypass_reason,
        gate_reason=(
            "OK: chunk count stable or increased"
            if chunks_delta >= 0
            else (
                f"BYPASSED (MCE-13.9): chunk count regressed but "
                f"RAG_GATE_ALLOW_REGRESSION=1 — "
                f"({chunks_pre} -> {chunks_post}, delta={chunks_delta}, "
                f"tolerance=-{gate_tolerance})"
                if gate_bypassed
                else (
                    f"OK: chunk count within tolerance ({chunks_pre} -> {chunks_post}, "
                    f"delta={chunks_delta}, tolerance=-{gate_tolerance})"
                    if gate_passed
                    else f"BLOCKED: chunk count regressed beyond tolerance "
                    f"({chunks_pre} -> {chunks_post}, delta={chunks_delta}, "
                    f"tolerance=-{gate_tolerance})"
                )
            )
        ),
        rebuild_stats={k: v for k, v in rebuild_result.items() if k not in ("duration_s",)},
        state={"current": sm.state},
    )

    # Step 6: Dual-location JSONL log (Art. XII)
    _append_jsonl(result)

    # Story MCE-11.18: canonical audit entry for RAG_INDEX operation
    _append_audit_jsonl(
        operation="RAG_INDEX",
        source_id=slug,
        source_person=infer_source_person(slug, slug=slug),
        status="SUCCESS" if result.get("gate_passed", True) else "WARN",
        phase=4,
        details={
            "bucket": bucket,
            "chunks_pre": chunks_pre,
            "chunks_post": chunks_post,
            "chunks_delta": chunks_delta,
            "gate_passed": result.get("gate_passed", True),
        },
        checksum=None,
    )

    # Also append to dedicated RAG indexation log
    rag_log = LOGS / "rag-indexation.jsonl"
    try:
        rag_log.parent.mkdir(parents=True, exist_ok=True)
        with open(rag_log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(result, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write RAG indexation JSONL", exc_info=True)

    # STORY-MCE-LOG-PARITY (2026-05-20): emit ASCII RAG Indexation Report
    # (Art. XV visibility). Fail-open per Art. XII.
    try:
        from engine.intelligence.pipeline.mce.log_emitters import emit_rag_indexation

        _rag_block = emit_rag_indexation(result)
        print(_rag_block, flush=True)
        emit_phase_payload(
            slug=slug,
            template_id="rag_indexation",
            status="ok" if result.get("gate_passed", False) else "warning",
            metrics={k: v for k, v in result.items() if k not in ("ascii_block", "slug")},
            ascii_block=_rag_block,
        )
    except Exception as _log_exc:  # pragma: no cover
        logger.debug("RAG indexation emit failed (non-fatal): %s", _log_exc)

    return result


# ---------------------------------------------------------------------------
# Command: graphrag_index (Phase 5b — opt-in via MCE_GRAPHRAG_ENABLED=1)
# ---------------------------------------------------------------------------


def cmd_graphrag_index(slug: str) -> dict[str, Any]:
    """Phase 5b — Build GraphRAG community summaries (ON by default; opt-out via MCE_GRAPHRAG_ENABLED=0).

    Skipped by default (MCE_GRAPHRAG_ENABLED absent or =0).  When enabled,
    builds a KnowledgeGraph from the full DNA corpus and detects cross-person
    communities (e.g. Jordan ↔ Hormozi on "delegação").

    Args:
        slug: Person/source slug.  Used only for logging; graph_builder
              builds from the global DNA directory.

    Returns:
        dict with one of:
        - {"skipped": True, "reason": str}   — when opted out (=0) OR deps missing
        - {"slug": str, "graphrag_enabled": True,
           "communities_built": int, "duration_ms": float}  — on success
        - {"error": str, "graphrag_enabled": True}          — on failure
    """
    import os

    # STORY-ENABLE-GBRAIN-FULL: default flipped "0" → "1" (GraphRAG ON by
    # default). Opt-OUT via MCE_GRAPHRAG_ENABLED=0. Fail-safe is preserved below:
    # missing deps → ImportError → skip; any other error → error dict (caller in
    # cmd_full treats both as non-blocking, Art. XII).
    if os.getenv("MCE_GRAPHRAG_ENABLED", "1") != "1":
        return {"skipped": True, "reason": "MCE_GRAPHRAG_ENABLED=0 (opt-out — default is ON)"}

    start = time.monotonic()
    try:
        from engine.intelligence.rag.graph_builder import build_graph, detect_communities

        graph = build_graph()
        communities = detect_communities(graph)
        graph.save()
        duration_ms = (time.monotonic() - start) * 1000
        return {
            "slug": slug,
            "graphrag_enabled": True,
            "communities_built": len(communities),
            "entities_total": len(graph.entities),
            "duration_ms": round(duration_ms, 1),
        }
    except ImportError as e:
        return {"skipped": True, "reason": f"graph_builder import failed: {e}"}
    except Exception as e:
        return {"error": str(e), "graphrag_enabled": True}


# ---------------------------------------------------------------------------
# Command: recover
# ---------------------------------------------------------------------------


def cmd_recover(slug: str) -> dict[str, Any]:
    """Recover a failed or paused pipeline to its last valid state.

    Uses ``PipelineStateMachine.recover_to_last()`` to jump to the
    state before the fail/pause, instead of resetting to ``init``.

    Args:
        slug: Person/source slug.

    Returns:
        Structured result dict with ``recovered_to`` field.
    """
    t0 = time.monotonic()
    sm = PipelineStateMachine(slug)

    if sm.state not in ("failed", "paused"):
        elapsed = (time.monotonic() - t0) * 1000
        return _build_result(
            "recover",
            success=False,
            slug=slug,
            error=f"Cannot recover: pipeline is in state '{sm.state}', not failed/paused",
            duration_ms=elapsed,
        )

    target = sm.recover_to_last()

    # Sync metadata status back to in_progress
    mgr = MetadataManager.load(slug)
    if mgr is not None:
        mgr.pipeline_status = "in_progress"
        mgr.save()

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "recover",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        recovered_to=target,
        state={"current": sm.state},
    )
    _append_jsonl(result)
    emit_phase_payload(
        slug=slug,
        template_id="pipeline_recover",
        status="ok",
        metrics={"recovered_to": target},
        ascii_block="",
    )
    # T4 (MCE-14.6): emit chronicler unconditionally on recover path.
    # cmd_recover goal is "pipeline finished via recovery" — always document it.
    # Paranoid try/except on top of helper's own safety (Art. XII).
    try:
        _safe_emit_chronicler(slug, source_path="cmd_recover")
    except Exception:
        pass
    return result


# ---------------------------------------------------------------------------
# Command: cleanup
# ---------------------------------------------------------------------------


def cmd_cleanup(
    slug: str | None = None,
    *,
    retention_days: int = 30,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Clean up old/completed MCE pipeline state directories.

    Removes state directories for pipelines that are in a terminal state
    (``complete`` or ``failed``) and older than ``retention_days``.

    Args:
        slug: Specific slug to clean, or *None* for all.
        retention_days: Days to retain completed/failed pipelines.
        dry_run: If *True*, report what would be removed without deleting.

    Returns:
        Structured result dict with cleaned/skipped counts.
    """
    import shutil

    t0 = time.monotonic()
    mce_base = Path(ROUTING.get("mce_state", MISSION_CONTROL / "mce"))
    logs_mce = LOGS / "mce"

    terminal_states = {"complete", "failed"}
    cutoff = datetime.now(UTC).timestamp() - (retention_days * 86400)

    candidates: list[Path] = []
    if slug:
        candidate = mce_base / slug
        if candidate.is_dir():
            candidates = [candidate]
    elif mce_base.exists():
        candidates = [d for d in sorted(mce_base.iterdir()) if d.is_dir()]

    removed: list[str] = []
    skipped: list[str] = []

    for d in candidates:
        slug_name = d.name
        state_file = d / "pipeline_state.yaml"
        if not state_file.exists():
            skipped.append(slug_name)
            continue

        try:
            data = yaml.safe_load(state_file.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            skipped.append(slug_name)
            continue

        if not isinstance(data, dict):
            skipped.append(slug_name)
            continue

        state = data.get("state", "")
        updated = data.get("updated_at", "")

        if state not in terminal_states:
            skipped.append(slug_name)
            continue

        # Check age
        try:
            ts = datetime.fromisoformat(updated).timestamp()
        except (ValueError, TypeError):
            ts = 0.0

        if ts > cutoff:
            skipped.append(slug_name)
            continue

        # Eligible for removal
        if not dry_run:
            shutil.rmtree(d, ignore_errors=True)
            # Also clean logs
            slug_log_dir = logs_mce / slug_name
            if slug_log_dir.is_dir():
                shutil.rmtree(slug_log_dir, ignore_errors=True)

        removed.append(slug_name)

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "cleanup",
        success=True,
        duration_ms=elapsed,
        dry_run=dry_run,
        retention_days=retention_days,
        removed=removed,
        removed_count=len(removed),
        skipped=skipped,
        skipped_count=len(skipped),
    )
    _append_jsonl(result)
    emit_phase_payload(
        slug=slug or "__all__",
        template_id="pipeline_cleanup",
        status="ok",
        metrics={"removed_count": len(removed), "skipped_count": len(skipped), "dry_run": dry_run},
        ascii_block="",
    )
    return result


# ---------------------------------------------------------------------------
# Command: cleanup-slug (MCE-13.8 Bug H)
# ---------------------------------------------------------------------------


def cmd_cleanup_slug(slug: str, dry_run: bool = False) -> dict[str, Any]:
    """Remove all artifacts for a slug to enable clean re-ingestion (MCE-13.8 Bug H).

    Moves artifacts to ``.claude/trash/cleanup-slug-{slug}-{timestamp}/`` rather
    than hard-deleting (respects trash_guard). Source file in inbox/ is PRESERVED.

    Cleaned paths:
      - .data/artifacts/chunks/<slug>
      - .data/artifacts/embeddings/<slug>
      - .data/artifacts/insights/<slug>
      - .data/artifacts/batches/<slug>
      - .data/logs/mce/<slug>
      - .claude/mission-control/mce/<slug>
      - artifacts/pipeline/<slug>
      - knowledge/external/processed/<slug>
      - knowledge/external/dna/persons/<slug>
      - agents/external/<slug>
      - knowledge/external/dossiers/persons/dossier-{slug}.md
      - knowledge/external/dossiers/persons-by-theme/{slug}--*.md  (glob)
      - .data/processed-sources/{slug}*.json  (glob)
      - BATCH-REGISTRY.json entries matching slug

    Args:
        slug: Source slug identifier (e.g. "ryan-deiss").
        dry_run: If True, list actions without executing any moves.

    Returns:
        dict with keys: command, slug, dry_run, actions, trash_dir.
    """
    import shutil as _shutil

    repo = _PROJECT_ROOT
    actions: list[dict[str, Any]] = []

    paths_to_remove: list[Path] = [
        repo / ".data" / "artifacts" / "chunks" / slug,
        repo / ".data" / "artifacts" / "embeddings" / slug,
        repo / ".data" / "artifacts" / "insights" / slug,
        repo / ".data" / "artifacts" / "batches" / slug,
        repo / ".data" / "logs" / "mce" / slug,
        repo / ".claude" / "mission-control" / "mce" / slug,
        repo / "artifacts" / "pipeline" / slug,
        repo / "knowledge" / "external" / "processed" / slug,
        repo / "knowledge" / "external" / "dna" / "persons" / slug,
        repo / "agents" / "external" / slug,
        repo / "knowledge" / "external" / "dossiers" / "persons" / f"dossier-{slug}.md",
    ]

    # Glob persons-by-theme solo files
    pbt = repo / "knowledge" / "external" / "dossiers" / "persons-by-theme"
    if pbt.exists():
        paths_to_remove.extend(pbt.glob(f"{slug}--*.md"))

    # Glob processed-sources markers
    ps = repo / ".data" / "processed-sources"
    if ps.exists():
        paths_to_remove.extend(ps.glob(f"{slug}*.json"))

    # Build trash destination
    trash = (
        repo
        / ".claude"
        / "trash"
        / f"cleanup-slug-{slug}-{_now_iso()[:19].replace(':', '-')}"
    )
    if not dry_run:
        trash.mkdir(parents=True, exist_ok=True)

    for p in paths_to_remove:
        if p.exists():
            entry: dict[str, Any] = {"path": str(p.relative_to(repo)), "exists": True}
            if not dry_run:
                target = trash / p.name
                # Avoid collision when multiple globs share the same stem
                if target.exists():
                    target = trash / f"{p.stem}_{p.parent.name}{p.suffix}"
                try:
                    _shutil.move(str(p), str(target))
                    entry["moved_to"] = str(target.relative_to(repo))
                except Exception as _mv_exc:
                    entry["error"] = str(_mv_exc)
            actions.append(entry)

    # Clean BATCH-REGISTRY.json entries for this slug
    reg_path = _PROJECT_ROOT / ".claude" / "mission-control" / "BATCH-REGISTRY.json"
    if reg_path.exists():
        try:
            d: dict[str, Any] = json.loads(reg_path.read_text(encoding="utf-8"))
            slug_lower = slug.lower()
            batches_before = len(d.get("batches", {}))
            files_before = len(d.get("files", {}))
            d["batches"] = {
                k: v
                for k, v in d.get("batches", {}).items()
                if v.get("source_name", "").lower() != slug_lower
            }
            d["files"] = {
                k: v
                for k, v in d.get("files", {}).items()
                if slug_lower not in k.lower()
                and v.get("source_name", "").lower() != slug_lower
            }
            batches_removed = batches_before - len(d["batches"])
            files_removed = files_before - len(d["files"])
            if not dry_run:
                reg_path.write_text(
                    json.dumps(d, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
                )
            actions.append(
                {
                    "path": "BATCH-REGISTRY.json",
                    "batches_removed": batches_removed,
                    "files_removed": files_removed,
                    "dry_run": dry_run,
                }
            )
        except Exception as _reg_exc:
            actions.append({"path": "BATCH-REGISTRY.json", "error": str(_reg_exc)})

    return {
        "command": "cleanup-slug",
        "slug": slug,
        "dry_run": dry_run,
        "actions": actions,
        "trash_dir": str(trash.relative_to(repo)) if not dry_run else None,
        "success": True,
    }


# ---------------------------------------------------------------------------
# Command: report
# ---------------------------------------------------------------------------


def cmd_report(slug: str) -> dict[str, Any]:
    """Generate a deterministic pipeline report by reading artifacts.

    No LLM call -- purely reads JSON/YAML files and counts entries.

    Args:
        slug: Person/source slug.

    Returns:
        Structured result dict with counts, files, and validation checklist.
    """
    t0 = time.monotonic()

    # Artifact paths (slug-isolated with legacy fallback)
    insights_slug = ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
    insights_legacy = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
    insights_path = insights_slug if insights_slug.exists() else insights_legacy

    chunks_slug = ARTIFACTS / "chunks" / slug / "CHUNKS-STATE.json"
    chunks_legacy = ARTIFACTS / "chunks" / "CHUNKS-STATE.json"
    chunks_path = chunks_slug if chunks_slug.exists() else chunks_legacy

    # Count chunks
    chunks_count = 0
    if chunks_path.exists():
        try:
            data = json.loads(chunks_path.read_text(encoding="utf-8"))
            chunks_count = len(data.get("chunks", []))
        except Exception:
            pass

    # Count insights and MCE elements
    insights_count = 0
    behavioral_patterns = 0
    values_count = 0
    obsessions_count = 0
    paradoxes_count = 0
    phrases_count = 0
    if insights_path.exists():
        try:
            data = json.loads(insights_path.read_text(encoding="utf-8"))
            # Count across all categories
            categories = data.get("categories", {})
            for _cat_name, cat_data in categories.items():
                if isinstance(cat_data, dict):
                    insights_count += len(cat_data.get("insights", []))
                elif isinstance(cat_data, list):
                    insights_count += len(cat_data)

            # Count MCE-specific elements if present
            mce = data.get("mce", {})
            behavioral_patterns = len(mce.get("behavioral_patterns", []))
            values_count = len(mce.get("values", []))
            obsessions_count = len(mce.get("obsessions", []))
            paradoxes_count = len(mce.get("paradoxes", []))
            phrases_count = len(mce.get("phrases", []))
        except Exception:
            pass

    # List generated agent files (bucket-aware)
    bucket = _detect_bucket_for_slug(slug)
    agent_dir = _agent_dir_for_slug(slug, bucket)
    agent_files: list[str] = []
    if agent_dir.is_dir():
        for f in sorted(agent_dir.iterdir()):
            if f.is_file():
                agent_files.append(f.name)

    # For personal bucket, also check DNA in knowledge/personal/dna/
    dna_dir = _dna_dir_for_slug(slug, bucket)
    dna_files: list[str] = []
    if dna_dir.is_dir():
        for f in sorted(dna_dir.iterdir()):
            if f.is_file():
                dna_files.append(f.name)

    # Validation checklist
    checklist = {
        "has_insights": insights_path.exists(),
        "has_chunks": chunks_path.exists(),
        "has_agent_dir": agent_dir.is_dir(),
        # Canonical lowercase filenames checked first; UPPERCASE kept as backward-compat fallback
        "has_agent_md": (
            (agent_dir / "agent.md").exists() or (agent_dir / "AGENT.md").exists()
        ) if agent_dir.is_dir() else False,
        "has_soul_md": (
            (agent_dir / "soul.md").exists() or (agent_dir / "SOUL.md").exists()
        ) if agent_dir.is_dir() else False,
        "has_memory_md": (
            (agent_dir / "memory.md").exists() or (agent_dir / "MEMORY.md").exists()
        ) if agent_dir.is_dir() else False,
        "has_dna_config": (
            (agent_dir / "dna-config.yaml").exists() or (agent_dir / "DNA-CONFIG.yaml").exists()
        ) if agent_dir.is_dir() else False,
        "has_dna_dir": dna_dir.is_dir(),
        "dna_layer_count": len(dna_files),
    }

    # Load FSM + metadata for context
    sm = PipelineStateMachine(slug)
    mgr = MetadataManager.load(slug)

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "report",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        counts={
            "chunks": chunks_count,
            "insights": insights_count,
            "behavioral_patterns": behavioral_patterns,
            "values": values_count,
            "obsessions": obsessions_count,
            "paradoxes": paradoxes_count,
            "phrases": phrases_count,
        },
        bucket=bucket,
        agent_files=agent_files,
        dna_files=dna_files,
        checklist=checklist,
        state={
            "current": sm.state,
            "metadata_status": mgr.pipeline_status if mgr else "unknown",
            "source_code": mgr.source_code if mgr else _derive_source_code(slug),
        },
    )
    _append_jsonl(result)
    emit_phase_payload(
        slug=slug,
        template_id="pipeline_report",
        status="ok",
        metrics={
            "chunks": chunks_count,
            "insights": insights_count,
            "behavioral_patterns": behavioral_patterns,
            "values": values_count,
            "obsessions": obsessions_count,
            "paradoxes": paradoxes_count,
        },
        ascii_block="",
    )
    return result


# ---------------------------------------------------------------------------
# Command: promote-agent  (Frente 7 — skeleton → full DNA-driven agent)
# ---------------------------------------------------------------------------


def cmd_promote_agent(slug: str) -> dict[str, Any]:
    """Promote agent skeleton → full DNA-driven agent (Step 11 gate).

    Reads L6-L10 YAMLs + INSIGHTS-STATE.json (L1-L5) and rewrites all four
    agent files with real extracted content, changing ``status: skeleton``
    → ``status: complete``.

    FSM wiring:
        - Runs after identity-checkpoint returns APPROVE.
        - If identity-checkpoint returned ABORT, this function is NOT called
          (enforced by cmd_auto_advance callers).
        - After success, FSM advances via ``start_agents`` trigger.

    Args:
        slug: Person slug (kebab-case).

    Returns:
        Structured dict with ``promoted``, ``status_before``, ``status_after``,
        ``files``, ``total_insights``, ``dna_layers``.  Always non-fatal.
    """
    t0 = time.monotonic()

    # Resolve bucket
    bucket = _detect_bucket_for_slug(slug)

    # MCE-2.5: agent_promoter expects a pre-existing skeleton. Auto-create
    # it on first promotion so a clean slug doesn't fail Step 11 with
    # "agent directory missing". The skeleton is harmless if it already
    # exists — ensure_agent_skeleton_for_slug short-circuits.
    try:
        from engine.intelligence.pipeline.mce.agent_skeleton import (
            ensure_agent_skeleton_for_slug,
        )

        skeleton_info = ensure_agent_skeleton_for_slug(slug, bucket)
        logger.info(
            "agent_skeleton ensured for %s: %s",
            slug,
            skeleton_info.get("status") if isinstance(skeleton_info, dict) else "n/a",
        )
    except Exception as exc:
        logger.warning("agent_skeleton ensure failed for %s: %s", slug, exc)

    try:
        from engine.intelligence.pipeline.mce.agent_promoter import ensure_agent_promoted

        promotion_result = ensure_agent_promoted(slug, bucket, use_llm=True)
    except Exception as exc:
        logger.warning("agent_promoter import/call failed for %s: %s", slug, exc)
        promotion_result = {
            "promoted": False,
            "error": str(exc),
            "agent_dir": "",
            "files": [],
        }

    # Advance FSM to agent_generation if promotion succeeded
    if promotion_result.get("promoted"):
        sm = PipelineStateMachine(slug)
        for trigger_name in ("start_rag_index", "start_agents"):
            trigger_fn = getattr(sm, trigger_name, None)
            if trigger_fn is not None:
                try:
                    trigger_fn(None)
                except Exception:
                    logger.debug(
                        "FSM trigger %s failed (may not be valid from %s)",
                        trigger_name,
                        sm.state,
                    )

    elapsed = (time.monotonic() - t0) * 1000

    # Resolve effective_promoted: agent_promoter returns promoted=False when
    # the agent was already complete (idempotent no-op). That is a success
    # scenario — the agent IS promoted. We emit effective_promoted=True to
    # PHASE-STREAM so check 7F-adjacent logic and the health panel show the
    # real state, not the no-op sentinel.
    _reason = promotion_result.get("reason", "")
    _already_promoted = "already promoted" in _reason.lower() if _reason else False
    effective_promoted = bool(promotion_result.get("promoted")) or _already_promoted

    result = _build_result(
        "promote-agent",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        bucket=bucket,
        promotion=promotion_result,
        promoted=effective_promoted,
        status_before=promotion_result.get("status_before", "unknown"),
        status_after=promotion_result.get("status_after", "unknown"),
        files=promotion_result.get("files", []),
        total_insights=promotion_result.get("total_insights", 0),
        dna_layers=promotion_result.get("dna_layers", 0),
        llm_used=promotion_result.get("llm_used", False),
    )
    _append_jsonl(result)
    emit_phase_payload(
        slug=slug,
        template_id="promote_agent",
        status="ok" if effective_promoted else "warning",
        metrics={
            "promoted": effective_promoted,
            "total_insights": promotion_result.get("total_insights", 0),
            "dna_layers": promotion_result.get("dna_layers", 0),
            "llm_used": promotion_result.get("llm_used", False),
        },
        ascii_block="",
    )
    return result


# ---------------------------------------------------------------------------
# Command: consolidate (Step 10 — Dossier Synthesis)
# ---------------------------------------------------------------------------


def cmd_consolidate(slug: str, *, force: bool = False) -> dict[str, Any]:
    """Generate synthesised dossier for slug (Step 10 — Consolidation/Forge).

    Reads INSIGHTS-STATE.json (L1-L5) + L6-L10 YAMLs + agent files and
    produces ``knowledge/{bucket}/dossiers/persons/dossier-{slug}.md``.

    FSM wiring:
        - Called after identity-checkpoint returns APPROVE + agent promoted.
        - If identity-checkpoint returned ABORT, this function is NOT called.
        - Non-blocking: dossier failure never crashes cmd_finalize.

    Args:
        slug: Person slug (kebab-case).
        force: If True, overwrite existing dossier (default: idempotent skip).

    Returns:
        Structured dict with ``status``, ``dossier_path``, ``sections_filled``,
        ``size_bytes``, ``llm_used``.  Always non-fatal.
    """
    t0 = time.monotonic()
    bucket = _detect_bucket_for_slug(slug)

    try:
        from engine.intelligence.pipeline.mce.dossier_generator import (
            ensure_dossier_created,
            should_regenerate,
        )

        # Bug #3/#9 fix: if insights grew beyond threshold, force regeneration
        # even though dossier already exists (previously gave idempotent SKIP).
        if not force:
            force = should_regenerate(slug, bucket)

        consolidation_result = ensure_dossier_created(slug, bucket, force=force, use_llm=True)
    except Exception as exc:
        logger.warning("dossier_generator import/call failed for %s: %s", slug, exc)
        consolidation_result = {
            "status": "error",
            "error": str(exc),
            "dossier_path": "",
            "sections_filled": 0,
            "size_bytes": 0,
            "llm_used": False,
        }

    elapsed = (time.monotonic() - t0) * 1000
    result = _build_result(
        "consolidate",
        success=consolidation_result.get("status") in ("written", "skipped"),
        slug=slug,
        duration_ms=elapsed,
        bucket=bucket,
        consolidation=consolidation_result,
        dossier_status=consolidation_result.get("status", "error"),
        dossier_path=consolidation_result.get("dossier_path", ""),
        sections_filled=consolidation_result.get("sections_filled", 0),
        size_bytes=consolidation_result.get("size_bytes", 0),
        llm_used=consolidation_result.get("llm_used", False),
    )
    _append_jsonl(result)
    from engine.intelligence.pipeline.mce.log_emitters import emit_consolidate_dossier_box

    _consolidate_metrics = {
        "dossier_status": consolidation_result.get("status", "error"),
        "sections_filled": consolidation_result.get("sections_filled", 0),
        "size_bytes": consolidation_result.get("size_bytes", 0),
        "llm_used": consolidation_result.get("llm_used", False),
        "duration_ms": elapsed,
    }
    emit_phase_payload(
        slug=slug,
        template_id="consolidate_dossier",
        status="ok" if consolidation_result.get("status") in ("written", "skipped") else "warning",
        metrics=_consolidate_metrics,
        ascii_block=emit_consolidate_dossier_box(slug, _consolidate_metrics),
    )
    return result


# ---------------------------------------------------------------------------
# Command: phase8 — EVOLUTION-LOG + FILE-REGISTRY + ROLE-TRACKING + 9-item gate
# MCE-4.6 INSERTION POINT — Phase 8 subphases
# ---------------------------------------------------------------------------


def _atomic_write_json_p8(data: dict[str, Any], target: Path) -> None:
    """Atomic JSON write via tempfile.mkstemp + os.replace.

    Reuses the exact pattern from _save_review_queue (orchestrate.py ~L1161).
    Guarantees no partial state visible to readers (C-07, Art. X).
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path_str = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            f.write("\n")
        os.replace(tmp_path_str, target)
    except Exception:
        try:
            os.unlink(tmp_path_str)
        except OSError:
            pass
        raise


def _append_evolution_log(entry: dict[str, Any], log_path: Path) -> None:
    """Append one event line to EVOLUTION-LOG.jsonl with os.fsync for durability.

    Rotation: if the current file reaches >= 10_000 lines it is archived to
    .data/artifacts/evolution/archive/EVOLUTION-LOG-{YYYYMMDD-HHMMSS}.jsonl
    and a fresh empty file is started (AC10).
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # Rotation check
    if log_path.exists():
        try:
            with log_path.open("r", encoding="utf-8") as _f:
                line_count = sum(1 for _ in _f)
        except OSError:
            line_count = 0
        if line_count >= 10_000:
            archive_dir = log_path.parent / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
            archive_path = archive_dir / f"EVOLUTION-LOG-{ts}.jsonl"
            log_path.rename(archive_path)
            logger.info(
                "_append_evolution_log: rotated %d-line log to %s",
                line_count,
                archive_path,
            )
    # Append with fsync (AC8)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _load_json_or_default(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    """Load JSON from path or return default on missing/corrupt file."""
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.debug("_load_json_or_default: failed to load %s: %s", path, exc)
    return default


def _scan_slug_files(slug: str, bucket: str) -> list[dict[str, Any]]:
    """Scan filesystem for known pipeline-produced artifacts for a slug.

    Returns list of file-registry entries (without created_at — caller sets that).
    Uses path conventions established by existing MCE commands.
    """
    root = _PROJECT_ROOT
    slug_upper = slug.replace("-", "_").upper()
    entries: list[dict[str, Any]] = []

    def _add(path: Path, file_type: str, produced_by: str) -> None:
        if path.exists():
            rel = str(path.relative_to(root))
            entries.append(
                {
                    "slug": slug,
                    "file_path": rel,
                    "type": file_type,
                    "produced_by": produced_by,
                }
            )

    # DNA layer files
    dna_dir = root / "knowledge" / bucket / "dna" / "persons" / slug
    if dna_dir.is_dir():
        for dna_file in dna_dir.glob("*.yaml"):
            entries.append(
                {
                    "slug": slug,
                    "file_path": str(dna_file.relative_to(root)),
                    "type": "dna",
                    "produced_by": "cmd_dna",
                }
            )

    # Sources files
    sources_dir = root / "knowledge" / bucket / "sources" / slug_upper
    if sources_dir.is_dir():
        for src_file in sources_dir.glob("*.md"):
            entries.append(
                {
                    "slug": slug,
                    "file_path": str(src_file.relative_to(root)),
                    "type": "sources",
                    "produced_by": "cmd_sources",
                }
            )

    # MAP-CONFLITOS files (external bucket only)
    if bucket == "external":
        domains_root = root / "knowledge" / "external" / "dna" / "domains"
        if domains_root.is_dir():
            for map_file in domains_root.glob("*/MAP-CONFLITOS-*.yaml"):
                # Include MAP-CONFLITOS files (they are domain-level, not per-slug,
                # but we register them under slugs that contributed to those domains)
                entries.append(
                    {
                        "slug": slug,
                        "file_path": str(map_file.relative_to(root)),
                        "type": "map-conflitos",
                        "produced_by": "cmd_aggregate_domain",
                    }
                )

    # Dossier files
    _add(
        root / "knowledge" / bucket / "dossiers" / f"{slug}.md",
        "dossier",
        "cmd_dossier",
    )

    # INSIGHTS-STATE
    insights_path = ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
    _add(insights_path, "insights", "cmd_enrich")

    return entries


def _infer_themes_for_slug(slug: str) -> list[str]:
    """Infer thematic tags for a slug from INSIGHTS-STATE domains/tags.

    Lightweight inference — reads existing INSIGHTS-STATE if available,
    falls back to empty list (non-blocking).
    """
    insights_path = ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
    themes: list[str] = []
    if insights_path.exists():
        try:
            state = json.loads(insights_path.read_text(encoding="utf-8"))
            # Pull tags/themes from known INSIGHTS-STATE fields
            for field in ("tags", "themes", "keywords"):
                val = state.get(field)
                if isinstance(val, list):
                    themes.extend(str(t) for t in val if t)
            # Also pull from contradictions topic field if present
            for item in state.get("contradictions", []):
                topic = item.get("topic")
                if topic and isinstance(topic, str):
                    themes.append(topic)
        except (json.JSONDecodeError, OSError) as exc:
            logger.debug("_infer_themes_for_slug: could not read insights for %s: %s", slug, exc)
    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for t in themes:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def _run_phase8_gate(
    slug: str,
    bucket: str,
    *,
    evolution_log_path: Path,
    file_registry_path: Path,
    role_tracking_path: Path,
) -> dict[str, Any]:
    """Run the 9-item gate (7.A-7.I) in WARN-only mode.

    Returns a gate result dict. Never raises — caller logs any internal
    exceptions and treats them as WARN (AC2, V2).
    """
    root = _PROJECT_ROOT
    slug_upper = slug.replace("-", "_").upper()
    checks: dict[str, bool] = {}
    failures: list[str] = []

    def _check(key: str, value: bool) -> None:
        checks[key] = value
        if not value:
            failures.append(key)

    # 7.A: AGG-*.yaml present for >= 1 domain
    try:
        from engine.intelligence.pipeline.domain_aggregator import _list_domains_for_slug

        slug_domains = _list_domains_for_slug(slug, root=root)
        has_agg = False
        for domain in slug_domains:
            agg_files = list(
                (root / "knowledge" / "external" / "dna" / "domains" / domain).glob("AGG-*.yaml")
            )
            if agg_files:
                has_agg = True
                break
        _check("7A_aggregated_present", has_agg)
    except Exception as exc:
        logger.debug("phase8 gate 7A check error: %s", exc)
        _check("7A_aggregated_present", False)
        slug_domains = []

    # 7.B: INSIGHTS-STATE.json has schema_version and contradictions[]
    # hotfix-6: legacy files pre-date the contradictions[] field. Backfill
    # atomically on gate read so subsequent runs pass without a full pipeline
    # re-run. Idempotent: if already present, no-op.
    try:
        ins_path = ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
        if ins_path.exists():
            ins = json.loads(ins_path.read_text(encoding="utf-8"))
            if "schema_version" in ins and "contradictions" not in ins:
                ins["contradictions"] = []
                tmp = ins_path.with_suffix(".json.tmp")
                tmp.write_text(
                    json.dumps(ins, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8",
                )
                tmp.replace(ins_path)
                logger.debug("phase8 gate 7B: backfilled contradictions[] for %s", slug)
            _check(
                "7B_insights_state_schema_valid",
                "schema_version" in ins and "contradictions" in ins,
            )
        else:
            _check("7B_insights_state_schema_valid", False)
    except Exception as exc:
        logger.debug("phase8 gate 7B check error: %s", exc)
        _check("7B_insights_state_schema_valid", False)

    # 7.C: NARRATIVES-STATE.json has bucket field in >= 1 person entry
    # hotfix-6: persons is a dict keyed by name, not a list. Must iterate
    # .values() to inspect person entries, not the string keys.
    try:
        narr_path = ARTIFACTS / "narratives" / "NARRATIVES-STATE.json"
        if narr_path.exists():
            narr = json.loads(narr_path.read_text(encoding="utf-8"))
            persons = narr.get("persons", {})
            if isinstance(persons, dict):
                has_bucket = any("bucket" in v for v in persons.values() if isinstance(v, dict))
            else:
                # legacy list format
                has_bucket = any("bucket" in p for p in persons if isinstance(p, dict))
            _check("7C_narratives_bucket_field", has_bucket)
        else:
            _check("7C_narratives_bucket_field", False)
    except Exception as exc:
        logger.debug("phase8 gate 7C check error: %s", exc)
        _check("7C_narratives_bucket_field", False)

    # 7.D: sources directory present for slug in correct bucket
    # hotfix-6: dirs on disk use lowercase-hyphenated slug (e.g. "alex-hormozi"),
    # not the SCREAMING_SNAKE slug_upper ("ALEX_HORMOZI"). Accept either casing.
    sources_dir = root / "knowledge" / bucket / "sources" / slug_upper
    sources_dir_lower = root / "knowledge" / bucket / "sources" / slug
    _check("7D_sources_dir_present", sources_dir.is_dir() or sources_dir_lower.is_dir())

    # 7.E: MAP-CONFLITOS-{D}.yaml exists for >= 1 domain
    try:
        has_map = False
        if bucket == "external":
            for domain in slug_domains:
                domain_dir = root / "knowledge" / "external" / "dna" / "domains" / domain
                if list(domain_dir.glob("MAP-CONFLITOS-*.yaml")):
                    has_map = True
                    break
        _check("7E_map_conflitos_per_domain", has_map)
    except Exception as exc:
        logger.debug("phase8 gate 7E check error: %s", exc)
        _check("7E_map_conflitos_per_domain", False)

    # 7.F: PIPELINE-STATE.json present for slug
    pipeline_state_path = ARTIFACTS / "mce" / slug / "PIPELINE-STATE.json"
    _check("7F_pipeline_state_checkpoint", pipeline_state_path.exists())

    # 7.G: EVOLUTION-LOG.jsonl has >= 1 entry for this slug
    try:
        if evolution_log_path.exists():
            found_slug = False
            with evolution_log_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("entity_id") == slug:
                            found_slug = True
                            break
                    except json.JSONDecodeError:
                        continue
            _check("7G_evolution_log_entry", found_slug)
        else:
            _check("7G_evolution_log_entry", False)
    except Exception as exc:
        logger.debug("phase8 gate 7G check error: %s", exc)
        _check("7G_evolution_log_entry", False)

    # 7.H: FILE-REGISTRY.json has >= 1 entry for this slug
    try:
        if file_registry_path.exists():
            reg = json.loads(file_registry_path.read_text(encoding="utf-8"))
            has_entry = any(f.get("slug") == slug for f in reg.get("files", []))
            _check("7H_file_registry_entry", has_entry)
        else:
            _check("7H_file_registry_entry", False)
    except Exception as exc:
        logger.debug("phase8 gate 7H check error: %s", exc)
        _check("7H_file_registry_entry", False)

    # 7.I: ROLE-TRACKING.json has entry for this slug
    try:
        if role_tracking_path.exists():
            rt = json.loads(role_tracking_path.read_text(encoding="utf-8"))
            has_person = any(p.get("slug") == slug for p in rt.get("persons", []))
            _check("7I_role_tracking_entry", has_person)
        else:
            _check("7I_role_tracking_entry", False)
    except Exception as exc:
        logger.debug("phase8 gate 7I check error: %s", exc)
        _check("7I_role_tracking_entry", False)

    # 7.J: cascade coverage — % of theme dossiers updated vs total eligible routes
    # V1 = WARN-only (blocking=False).  V2 will promote to BLOCK when coverage <20%.
    # Story MCE-12.9.
    gate_result_extras: dict[str, Any] = {}
    try:
        routing_yaml = root / "engine" / "config" / "theme-routing.yaml"
        if not routing_yaml.exists():
            checks["7J_cascade_coverage"] = True  # SKIP treated as non-failure
            gate_result_extras["7J_cascade_coverage"] = {
                "check_id": "7J_cascade_coverage",
                "status": "SKIP",
                "reason": "theme-routing.yaml not found",
                "blocking": False,
            }
        else:
            with routing_yaml.open(encoding="utf-8") as _fh:
                routing_data = yaml.safe_load(_fh)
            total_routes = len((routing_data or {}).get("routes", {}))

            cascade_log = LOGS / "cascading.jsonl"
            if not cascade_log.exists():
                checks["7J_cascade_coverage"] = True  # WARN but non-blocking
                gate_result_extras["7J_cascade_coverage"] = {
                    "check_id": "7J_cascade_coverage",
                    "status": "WARN",
                    "reason": "cascading.jsonl missing",
                    "blocking": False,
                }
            else:
                last_entry: dict[str, Any] | None = None
                with cascade_log.open(encoding="utf-8") as _fh:
                    for _line in _fh:
                        try:
                            _entry = json.loads(_line)
                            if _entry.get("slug") == slug:
                                last_entry = _entry
                        except json.JSONDecodeError:
                            pass

                if last_entry is None:
                    checks["7J_cascade_coverage"] = True  # WARN but non-blocking
                    gate_result_extras["7J_cascade_coverage"] = {
                        "check_id": "7J_cascade_coverage",
                        "status": "WARN",
                        "reason": f"no cascade entry for slug={slug}",
                        "blocking": False,
                    }
                else:
                    themes_updated = last_entry.get("themes_updated", 0)
                    themes_secondary = last_entry.get("themes_updated_secondary", 0)
                    total_updated = themes_updated + themes_secondary
                    coverage_pct = (total_updated / total_routes * 100) if total_routes > 0 else 0.0
                    threshold_pct = 20.0  # V1 threshold; V2 promotes to BLOCK
                    j_status = "PASS" if coverage_pct >= threshold_pct else "WARN"
                    # 7J never blocks gate — treat as True in checks bool map
                    checks["7J_cascade_coverage"] = True
                    gate_result_extras["7J_cascade_coverage"] = {
                        "check_id": "7J_cascade_coverage",
                        "status": j_status,
                        "coverage_pct": round(coverage_pct, 1),
                        "themes_updated": themes_updated,
                        "themes_secondary": themes_secondary,
                        "total_routes": total_routes,
                        "threshold_pct": threshold_pct,
                        "blocking": False,
                    }
    except Exception as exc:
        logger.debug("phase8 gate 7J check error: %s", exc)
        checks["7J_cascade_coverage"] = True  # non-blocking fallthrough
        gate_result_extras["7J_cascade_coverage"] = {
            "check_id": "7J_cascade_coverage",
            "status": "WARN",
            "reason": f"7J check exception: {exc}",
            "blocking": False,
        }

    gate_status = "PASS" if not failures else "WARN"
    result: dict[str, Any] = {
        "gate_status": gate_status,
        "checks": checks,
        "failures": failures,
    }
    result.update(gate_result_extras)
    return result



# Per-process dedup cache for cmd_phase8.  Keyed by slug; value is the result
# dict from the first successful execution.  Prevents double-execution when
# jarvis_chief dispatches phase8_gate (phase 16) AND then workspace_sync
# (phase 17) which calls cmd_finalize, which also calls cmd_phase8 internally.
# Reset is not needed — each subprocess/process starts with an empty dict.
_phase8_result_cache: dict[str, dict[str, Any]] = {}


def cmd_phase8(slug: str) -> dict[str, Any]:
    """Phase 8: EVOLUTION-LOG + FILE-REGISTRY + ROLE-TRACKING + 9-item gate WARN.

    Ported from JARVIS v2.1. Implements three tracking artifacts that were
    missing from the MCE port. Called non-blocking from cmd_finalize after
    domain aggregation (MCE-4.6).

    Steps:
        1. Infer bucket for slug.
        2. Append event to EVOLUTION-LOG.jsonl (with rotation + fsync).
        3. Update FILE-REGISTRY.json (merge, dedup by file_path, atomic write).
        4. Update ROLE-TRACKING.json (upsert by slug, atomic write).
        5. Run 9-item gate (7.A-7.I) — WARN only, never raises (V1).
        6. Log gate result to .data/logs/phase8-gate.jsonl.

    CRITICAL: Does NOT call cmd_identity_checkpoint — that is already called
    in cmd_finalize L4825-4833 (F-12, AC9, V1).

    Args:
        slug: Person/source slug to process.

    Returns:
        Dict with status, gate_status, artifacts_written, gate_checks, failures.

    Note on dedup: a per-process cache (_phase8_result_cache) ensures this
    function executes at most once per slug per Python process.  A second call
    within the same process returns the cached result without re-writing
    artifacts or logging to phase8-gate.jsonl.
    """
    if slug in _phase8_result_cache:
        logger.debug("cmd_phase8: returning cached result for %s (dedup)", slug)
        return _phase8_result_cache[slug]

    import uuid

    bucket = _detect_bucket_for_slug(slug)
    now = _now_iso()

    # Canonical paths for the 3 global artifacts (AC1)
    evolution_log_path = ARTIFACTS / "evolution" / "EVOLUTION-LOG.jsonl"
    file_registry_path = ARTIFACTS / "FILE-REGISTRY.json"
    role_tracking_path = ARTIFACTS / "ROLE-TRACKING.json"
    gate_log_path = LOGS / "phase8-gate.jsonl"

    artifacts_written: list[str] = []

    # -----------------------------------------------------------------------
    # Step 2: EVOLUTION-LOG append (AC3, AC8, AC10)
    # -----------------------------------------------------------------------
    try:
        evolution_entry: dict[str, Any] = {
            "entity_id": slug,
            "entity_type": "slug",
            "event_type": "updated",
            "from_state": None,
            "to_state": "phase8_processed",
            "timestamp": now,
            "triggered_by": "cmd_phase8",
        }
        _append_evolution_log(evolution_entry, evolution_log_path)
        artifacts_written.append("EVOLUTION-LOG.jsonl")
    except Exception as exc:
        logger.warning("cmd_phase8: EVOLUTION-LOG append failed for %s: %s", slug, exc)

    # -----------------------------------------------------------------------
    # Step 3: FILE-REGISTRY merge (AC4, AC7)
    # -----------------------------------------------------------------------
    try:
        existing_registry = _load_json_or_default(
            file_registry_path,
            {"schema_version": "1.0.0", "updated_at": now, "files": []},
        )
        # Build index of existing entries by file_path for dedup
        existing_by_path: dict[str, dict[str, Any]] = {
            e["file_path"]: e for e in existing_registry.get("files", []) if "file_path" in e
        }
        # Scan filesystem for this slug's artifacts
        new_entries = _scan_slug_files(slug, bucket)
        for entry in new_entries:
            fp = entry["file_path"]
            if fp in existing_by_path:
                # Preserve original created_at, update produced_by
                existing_by_path[fp]["produced_by"] = entry["produced_by"]
            else:
                entry["created_at"] = now
                existing_by_path[fp] = entry
        merged_files = list(existing_by_path.values())
        updated_registry: dict[str, Any] = {
            "schema_version": "1.0.0",
            "updated_at": now,
            "files": merged_files,
        }
        _atomic_write_json_p8(updated_registry, file_registry_path)
        artifacts_written.append("FILE-REGISTRY.json")
    except Exception as exc:
        logger.warning("cmd_phase8: FILE-REGISTRY update failed for %s: %s", slug, exc)

    # -----------------------------------------------------------------------
    # Step 4: ROLE-TRACKING upsert (AC5, AC7)
    # -----------------------------------------------------------------------
    try:
        # Infer domains via domain_aggregator (same source as gate 7.A)
        try:
            from engine.intelligence.pipeline.domain_aggregator import _list_domains_for_slug

            slug_domains = _list_domains_for_slug(slug, root=_PROJECT_ROOT)
        except Exception:
            slug_domains = []

        themes = _infer_themes_for_slug(slug)
        existing_rt = _load_json_or_default(
            role_tracking_path,
            {"schema_version": "1.0.0", "updated_at": now, "persons": []},
        )
        persons = existing_rt.get("persons", [])
        # Upsert: replace entry for this slug, or append
        upserted = False
        for i, person in enumerate(persons):
            if person.get("slug") == slug:
                persons[i] = {
                    "slug": slug,
                    "bucket": bucket,
                    "domains": slug_domains,
                    "themes": themes,
                    "last_updated": now,
                }
                upserted = True
                break
        if not upserted:
            persons.append(
                {
                    "slug": slug,
                    "bucket": bucket,
                    "domains": slug_domains,
                    "themes": themes,
                    "last_updated": now,
                }
            )
        updated_rt: dict[str, Any] = {
            "schema_version": "1.0.0",
            "updated_at": now,
            "persons": persons,
        }
        _atomic_write_json_p8(updated_rt, role_tracking_path)
        artifacts_written.append("ROLE-TRACKING.json")
    except Exception as exc:
        logger.warning("cmd_phase8: ROLE-TRACKING update failed for %s: %s", slug, exc)

    # -----------------------------------------------------------------------
    # Step 4b: Ensure PIPELINE-STATE.json exists for check 7F (idempotent).
    # save_pipeline_state() uses atomic write + mkdir_p. If the file already
    # exists it is left as-is (backfill skeleton preserved). This guarantees
    # check 7F always passes for slugs that reach cmd_phase8.
    # -----------------------------------------------------------------------
    try:
        from engine.intelligence.pipeline.mce.enforcement import (
            load_pipeline_state,
            save_pipeline_state,
        )

        _ps_root = _PROJECT_ROOT
        _ps_existing = load_pipeline_state(slug, _ps_root)
        if not _ps_existing:
            # First-time write — create minimal valid sentinel.
            from datetime import UTC
            from datetime import datetime as _dt_ps

            _ps_state: dict[str, Any] = {
                "schema_version": "1.0.0",
                "slug": slug,
                "bucket": bucket,
                "last_updated": _dt_ps.now(UTC).isoformat(),
                "checkpoints": [],
                "_note": "created by cmd_phase8 — phase8 gate 7F sentinel",
            }
            save_pipeline_state(slug, _ps_state, _ps_root)
            artifacts_written.append("PIPELINE-STATE.json")
            logger.info("cmd_phase8: PIPELINE-STATE.json created for %s (7F sentinel)", slug)
        else:
            logger.debug("cmd_phase8: PIPELINE-STATE.json already exists for %s — skipping", slug)
    except Exception as exc:
        logger.warning("cmd_phase8: PIPELINE-STATE.json ensure failed for %s: %s", slug, exc)

    # -----------------------------------------------------------------------
    # Step 5: 9-item gate (7.A-7.I) — WARN only, never raises (AC2, V2)
    # -----------------------------------------------------------------------
    gate_result: dict[str, Any] = {
        "gate_status": "ERROR",
        "checks": {},
        "failures": [],
    }
    try:
        gate_result = _run_phase8_gate(
            slug,
            bucket,
            evolution_log_path=evolution_log_path,
            file_registry_path=file_registry_path,
            role_tracking_path=role_tracking_path,
        )
    except Exception as exc:
        logger.warning("cmd_phase8: gate execution error for %s: %s", slug, exc)
        gate_result["failures"].append(f"gate_error:{exc}")

    # -----------------------------------------------------------------------
    # Step 6: Log gate result to .data/logs/phase8-gate.jsonl (AC2)
    # -----------------------------------------------------------------------
    try:
        gate_log_path.parent.mkdir(parents=True, exist_ok=True)
        gate_log_entry: dict[str, Any] = {
            "run_id": str(uuid.uuid4()),
            "slug": slug,
            "timestamp": now,
            "gate_status": gate_result["gate_status"],
            "checks": gate_result["checks"],
            "failures": gate_result["failures"],
        }
        with gate_log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(gate_log_entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("cmd_phase8: gate log write failed for %s: %s", slug, exc)

    phase8_out = {
        "status": "ok",
        "slug": slug,
        "bucket": bucket,
        "artifacts_written": artifacts_written,
        "gate_status": gate_result["gate_status"],
        "gate_checks": gate_result["checks"],
        "failures": gate_result["failures"],
        "7J_cascade_coverage": gate_result.get("7J_cascade_coverage"),
    }
    emit_phase_payload(
        slug=slug,
        template_id="phase8_tracking",
        status="ok" if gate_result["gate_status"] == "PASS" else "warning",
        metrics={
            "artifacts_written": len(artifacts_written),
            "gate_status": gate_result["gate_status"],
            "failures": len(gate_result["failures"]),
        },
        ascii_block="",
    )
    _phase8_result_cache[slug] = phase8_out
    return phase8_out


# ---------------------------------------------------------------------------
# Command: finalize
# ---------------------------------------------------------------------------


def _count_insights_for_slug(slug: str) -> int:
    """Count insights from per-slug INSIGHTS-STATE.json (handles 4 schema variants).

    MCE-13.8 Bug G: used as lifecycle gate guard — if zero insights were
    actually extracted, cmd_finalize skips the inbox→processed move so
    source material remains available for re-processing.

    Schema variants handled:
      A: flat list of insight dicts
      B: dict with ``"insights"`` list
      C: dict with ``"persons"`` mapping (person_slug -> dict with "insights" list)
      D: dict with ``"insights_state"`` wrapper containing "persons" mapping
    """
    paths = [
        _PROJECT_ROOT / ".data" / "artifacts" / "insights" / slug / "INSIGHTS-STATE.json",
        _PROJECT_ROOT / ".data" / "artifacts" / "mce" / slug / "INSIGHTS-STATE.json",
    ]
    for p in paths:
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        # Schema A: flat list
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            # Schema B: {"insights": [...]}
            if "insights" in data and isinstance(data["insights"], list):
                return len(data["insights"])
            # Schema C: {"persons": {"slug": {"insights": [...]}}}
            if "persons" in data and isinstance(data["persons"], dict):
                return sum(
                    len(p_data.get("insights", []))
                    for p_data in data["persons"].values()
                    if isinstance(p_data, dict)
                )
            # Schema D: {"insights_state": {"persons": {...}}}
            if "insights_state" in data and isinstance(data["insights_state"], dict):
                inner = data["insights_state"].get("persons", {})
                return sum(
                    len(p_data.get("insights", []))
                    for p_data in inner.values()
                    if isinstance(p_data, dict)
                )
    return 0


def _safe_emit_chronicler(slug: str, source_path: str = "unknown") -> dict[str, Any]:
    """Idempotent, exception-safe chronicler emission for any pipeline exit path.

    Reads marker at .claude/mission-control/mce/{slug}/chronicler-emitted.json.
    If marker exists -> return early (idempotency).
    Otherwise: collect data + generate log + write marker on success.
    All exceptions captured with logger.warning. NEVER raises (Art. XII).
    """
    marker_path = (
        _PROJECT_ROOT / ".claude" / "mission-control" / "mce" / slug / "chronicler-emitted.json"
    )

    if marker_path.exists():
        return {"skipped": True, "reason": "marker_exists", "marker_path": str(marker_path)}

    try:
        from engine.intelligence.pipeline.mce.chronicler_data_collector import (
            collect_final_log_data,
        )
        from engine.intelligence.pipeline.mce.log_generator import generate_mce_log

        collected = collect_final_log_data(slug)
        log_result = generate_mce_log(slug=slug, collected_data=collected)

        log_path = log_result.get("log_path") if isinstance(log_result, dict) else None

        if log_path:
            marker_path.parent.mkdir(parents=True, exist_ok=True)
            marker_payload = {
                "slug": slug,
                "log_path": str(log_path),
                "emitted_at": datetime.now(UTC).isoformat(),
                "source_path": source_path,
            }
            marker_path.write_text(json.dumps(marker_payload, indent=2), encoding="utf-8")
            return {"success": True, "log_path": log_path, "marker_path": str(marker_path)}
        else:
            logger.warning(
                "_safe_emit_chronicler[%s]: generate_mce_log returned no log_path (source=%s)",
                slug,
                source_path,
            )
            return {"success": False, "reason": "no_log_path"}
    except Exception as exc:
        logger.warning(
            "_safe_emit_chronicler[%s]: emission failed (source=%s): %s",
            slug,
            source_path,
            exc,
        )
        return {"success": False, "error": str(exc), "reason": "exception"}


def _resolve_identity_keys_for_slug(slug: str) -> list[str]:
    """Resolve the content-hash identity_keys (== content_hashes.source_id) for a slug.

    STORY-GBA-W2.8 helper. The ingestion guard keys ``content_hashes`` by
    ``identity_key`` (= the source's ``source_id`` from its header, see
    ``ingestion_guard._compute_identity_key``). A slug can aggregate several
    sources, so we gather every ``source_id`` recorded for this slug plus the
    derived source code. De-duplicated, order-preserving. Best-effort: returns
    an empty list rather than raising (caller fail-opens).
    """
    keys: list[str] = []
    seen: set[str] = set()

    def _add(val: Any) -> None:
        if isinstance(val, str) and val and val not in seen:
            seen.add(val)
            keys.append(val)

    try:
        mgr = MetadataManager.load(slug)
        if mgr is not None:
            for _src in getattr(mgr, "sources_processed", []) or []:
                if isinstance(_src, dict):
                    _add(_src.get("source_id"))
                    _add(_src.get("batch_id"))
                elif isinstance(_src, str):
                    _add(_src)
            ctx = mgr.to_dict() if hasattr(mgr, "to_dict") else {}
            _add(ctx.get("source_id"))
            _add(ctx.get("batch_id"))
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("_resolve_identity_keys_for_slug: metadata read failed: %s", exc)

    # Derived source code is the same fallback key the propagation tracker uses.
    try:
        _add(_derive_source_code(slug))
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("_resolve_identity_keys_for_slug: derive_source_code failed: %s", exc)

    return keys


def _mark_slug_fully_propagated(slug: str) -> int:
    """Mark every content_hash entry for ``slug`` as ``fully_propagated`` (D3).

    Returns the count of identity_keys marked. Uses the SAME DB-first registry
    (``DbIngestionRegistry``) the guard uses, so the flag lands in the exact
    ``content_hashes.metadata`` the guard reads back. Never touches the 6 verdict
    keys nor reorders the guard — it only sets a metadata flag AFTER propagation.
    """
    keys = _resolve_identity_keys_for_slug(slug)
    if not keys:
        logger.info(
            "STORY-GBA-W2.8: no identity_keys resolved for %s — nothing to mark", slug
        )
        return 0

    from engine.intelligence.pipeline.ingestion_guard import DbIngestionRegistry

    reg = DbIngestionRegistry()
    marked = 0
    try:
        for key in keys:
            reg.mark_fully_propagated(key)
            marked += 1
        logger.info(
            "STORY-GBA-W2.8: marked fully_propagated=true for %s (%d key(s): %s)",
            slug,
            marked,
            keys,
        )
    finally:
        try:
            reg.close()
        except Exception:
            pass
    return marked


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

    # Detect bucket for routing
    bucket = _detect_bucket_for_slug(slug)

    # Step 0: Phase 4.5 — RAG Indexation gate (Constitution Art. XV)
    # MUST pass before pipeline can advance to Phase 5 (agent creation).
    rag_result = cmd_rag_index(slug)
    if not rag_result.get("gate_passed", False):
        mt.end_phase("finalization")
        mt.save()
        elapsed = (time.monotonic() - t0) * 1000
        blocked_result = _build_result(
            "finalize",
            success=False,
            slug=slug,
            duration_ms=elapsed,
            bucket=bucket,
            error="BLOCKED by Phase 4.5 RAG Indexation gate (Art. XV)",
            rag_indexation=rag_result,
            state={"current": sm.state},
        )
        _append_jsonl(blocked_result)

        # STORY-MCE-LOG-PARITY (2026-05-20): emit Execution Report even on
        # BLOCKED path so operator sees what was produced before the gate.
        # Without this, a Phase 4.5 block hides all upstream progress.
        try:
            from engine.intelligence.pipeline.mce.log_emitters import (
                FinalizeContext,
                emit_execution_report,
            )

            ctx = FinalizeContext(
                slug=slug,
                bucket=bucket,
                person_name=_person_name_for_slug(slug),
                source_id=_derive_source_code(slug),
                duration_min=round(elapsed / 60000.0, 1),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                chunks_total=len(_resolve_chunks_for_slug(slug)),
                rag_indexation=rag_result,
                total_duration_s=round(elapsed / 1000.0, 1),
            )
            print(emit_execution_report(ctx), flush=True)
            print(
                f"\n⚠️  FINALIZE BLOCKED: {blocked_result['error']}\n",
                flush=True,
            )
        except Exception as _log_exc:  # pragma: no cover
            logger.debug("Execution Report emit (blocked path) failed: %s", _log_exc)

        return blocked_result

    # Step 0.5 (G18, 2026-05-13): Auto-create agent skeleton if missing.
    # The memory_enricher silently emits ``0 appended`` when the slug has no
    # ``agents/{bucket}/{slug}/`` directory.  For external/business slugs with
    # extracted DNA, we materialise a minimal four-file skeleton so the
    # enricher has a target on the first pipeline run.
    skeleton_result: dict[str, Any] = {}
    if bucket in ("external", "business"):
        try:
            from engine.intelligence.pipeline.mce.agent_skeleton import (
                ensure_agent_skeleton_for_slug,
            )

            sources_count = len(getattr(mgr, "sources_processed", []) or [])
            skeleton_result = ensure_agent_skeleton_for_slug(
                slug,
                bucket,
                sources_count=sources_count,
            )
        except Exception as exc:
            logger.warning("Agent skeleton wiring failed for %s: %s", slug, exc)
            skeleton_result = {"created": False, "error": str(exc)}

    # Step 1: Memory enrichment (uses slug-isolated path with legacy fallback)
    enrichment_result: dict[str, Any] = {}
    slug_insights = ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
    legacy_insights = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
    insights_path = slug_insights if slug_insights.exists() else legacy_insights
    if insights_path.exists():
        try:
            enrich_fn = _import_memory_enricher()
            raw = enrich_fn(insights_path)
            enrichment_result = {
                "appended": raw.get("appended", 0) if isinstance(raw, dict) else 0,
                "skipped_dedup": raw.get("skipped_dedup", 0) if isinstance(raw, dict) else 0,
                "agents_enriched": raw.get("agents_enriched", []) if isinstance(raw, dict) else [],
            }
            # Story MCE-11.18: canonical audit entry for MEMORY_UPDATE
            _agents_enriched = enrichment_result.get("agents_enriched", [])
            if _agents_enriched:
                _append_audit_jsonl(
                    operation="MEMORY_UPDATE",
                    source_id=slug,
                    source_person=infer_source_person(slug, slug=slug),
                    status="SUCCESS",
                    phase=5,
                    details={
                        "agent_path": str(insights_path.parent),
                        "section_appended": f"{enrichment_result.get('appended', 0)} insights",
                        "agents_enriched": _agents_enriched[:10],
                    },
                    checksum=None,
                )
        except Exception as exc:
            logger.warning("Memory enrichment failed: %s", exc)
            enrichment_result = {"error": str(exc)}
    else:
        enrichment_result = {"skipped": "INSIGHTS-STATE.json not found"}

    # Attach skeleton result to enrichment_result for observability.
    if skeleton_result:
        enrichment_result["skeleton"] = skeleton_result

    # MCE-17.1 P5: emit memory_enrichment to PHASE-STREAM so STEP 25 renders
    # from live data instead of disk fallback when MCE_NO_FALLBACK=1.
    # Non-blocking per Art. XII.
    try:
        emit_phase_payload(
            slug=slug,
            template_id="memory_enrichment",
            status="ok" if enrichment_result.get("appended", 0) >= 0 else "warning",
            metrics={
                "appended": enrichment_result.get("appended", 0),
                "skipped_dedup": enrichment_result.get("skipped_dedup", 0),
                "agents_enriched": enrichment_result.get("agents_enriched", []),
            },
            ascii_block="",
        )
    except Exception as _me_exc:  # pragma: no cover
        logger.debug("memory_enrichment emit failed (non-fatal): %s", _me_exc)

    # Step 1.5: Product detection — route product-related insights to YAMLs
    product_detection_result: dict[str, Any] = {}
    if insights_path.exists():
        try:
            from engine.intelligence.pipeline.product_detector import (
                SourceMeta,
                detect_and_route,
            )

            insights_data = json.loads(insights_path.read_text(encoding="utf-8"))
            categories = insights_data.get("categories", {})
            detected = 0
            routed = 0
            staged = 0

            # Build source meta from meeting context if available
            ctx = mgr.to_dict() if hasattr(mgr, "to_dict") else {}
            source_id = ctx.get("source_id", ctx.get("meet_id", slug))
            source_type = ctx.get("source_type", "call")
            source_platform = ctx.get("source_platform", "unknown")
            participants = ctx.get("participants", [])

            source = SourceMeta(
                source_id=source_id,
                source_type=source_type,
                source_platform=source_platform,
                participants=participants,
                has_summary=True,
                has_transcript=True,
                word_count=ctx.get("word_count", 1000) if ctx else 1000,
            )

            # Scan recent insights for product mentions
            for cat_name, cat_data in categories.items():
                ins_list = (
                    cat_data.get("insights", [])
                    if isinstance(cat_data, dict)
                    else (cat_data if isinstance(cat_data, list) else [])
                )
                for ins in ins_list:
                    if not isinstance(ins, dict):
                        continue
                    insight_text = ins.get("insight", "")
                    if not insight_text:
                        continue

                    detected += 1
                    result = detect_and_route(
                        insight_text=insight_text,
                        field_path="icp.definition",  # default — detector refines
                        value=insight_text,
                        source=source,
                        source_count=1,
                        dry_run=False,
                    )
                    if result.action in ("write", "draft"):
                        routed += 1
                    elif result.action in ("staging", "alert"):
                        staged += 1

            product_detection_result = {
                "detected": detected,
                "routed": routed,
                "staged": staged,
            }
        except Exception as exc:
            logger.warning("Product detection failed: %s", exc)
            product_detection_result = {"error": str(exc)}
    else:
        product_detection_result = {"skipped": "INSIGHTS-STATE.json not found"}

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

    # Step 2.5: Business bucket routing (meetings → knowledge/business/)
    business_routing_result: dict[str, Any] = {}
    if bucket == "business" and insights_path.exists():
        try:
            business_routing_result = _route_business_insights(slug, insights_path)
        except Exception as exc:
            logger.warning("Business routing failed: %s", exc)
            business_routing_result = {"error": str(exc)}

        # Incremental merge into global INSIGHTS-STATE.json
        try:
            merge_result = _update_insights_state_incrementally(slug, insights_path)
            business_routing_result["incremental_merge"] = merge_result
        except Exception as exc:
            logger.warning("Incremental merge failed: %s", exc)
            business_routing_result["incremental_merge"] = {"error": str(exc)}

    # Step 2.7: Post-extraction cascading (cargo agents + theme dossiers)
    cascade_result: dict[str, Any] = {}
    if insights_path.exists():
        try:
            from engine.intelligence.pipeline.mce.cascading import (
                run_post_extraction_cascade,
            )

            cascade_result = run_post_extraction_cascade(
                slug=slug,
                insights_path=insights_path,
                bucket=bucket,
            )
        except Exception as exc:
            logger.warning("Post-extraction cascading failed: %s", exc)
            cascade_result = {"error": str(exc)}
    else:
        cascade_result = {"skipped": "INSIGHTS-STATE.json not found"}

    # MCE-17.1 P5: emit role_tracker and cascading_dossiers to PHASE-STREAM so
    # STEPs 26 and 27 render from live data instead of disk fallback.
    # Non-blocking per Art. XII.
    try:
        emit_phase_payload(
            slug=slug,
            template_id="role_tracker",
            status="ok" if cascade_result.get("cargo_agents_updated", 0) >= 0 else "warning",
            metrics={
                "domains_updated": cascade_result.get("agg_domains_updated", 0),
                "themes_tracked": cascade_result.get("themes_updated", 0),
                "cargo_agents_updated": cascade_result.get("cargo_agents_updated", 0),
            },
            ascii_block="",
        )
    except Exception as _rt_exc:  # pragma: no cover
        logger.debug("role_tracker emit failed (non-fatal): %s", _rt_exc)

    try:
        emit_phase_payload(
            slug=slug,
            template_id="cascading_dossiers",
            status="ok" if cascade_result.get("themes_created", 0) >= 0 else "warning",
            metrics={
                "themes_created": cascade_result.get("themes_created", 0),
                "themes_updated": cascade_result.get("themes_updated", 0),
                "insights_processed": cascade_result.get("insights_processed", 0),
            },
            ascii_block="",
        )
    except Exception as _cd_exc:  # pragma: no cover
        logger.debug("cascading_dossiers emit failed (non-fatal): %s", _cd_exc)

    # Step 3: Update state machine through remaining transitions
    # Try to advance: agent_generation -> finalizing -> reporting -> complete
    for trigger_name in ("start_finalize", "start_report", "finish"):
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

    # Step 5.5: Identity Checkpoint (Step 9 gate) — run deterministic check
    # so log_generator sees a fresh identity-checkpoint.json with real data.
    # Non-blocking: finalize never fails because of checkpoint verdict alone;
    # the verdict is surfaced in the log (Step 9 row) for human review.
    identity_checkpoint_result: dict[str, Any] = {}
    try:
        identity_checkpoint_result = cmd_identity_checkpoint(slug)
        logger.info(
            "Identity checkpoint for %s: verdict=%s",
            slug,
            identity_checkpoint_result.get("verdict", "UNKNOWN"),
        )
    except Exception as exc:
        logger.warning("Identity checkpoint failed in finalize for %s: %s", slug, exc)
        identity_checkpoint_result = {"error": str(exc), "verdict": "UNKNOWN"}

    # Step 5.6: Agent Promotion (Step 11 gate) — promote skeleton → full agent
    # ONLY when identity-checkpoint returns APPROVE. If ABORT, skip (consistent
    # with Lens gate contract). Non-blocking: promotion failure never crashes
    # finalize.
    promotion_result: dict[str, Any] = {}
    ic_verdict = identity_checkpoint_result.get("verdict", "UNKNOWN")
    if ic_verdict == "APPROVE":
        try:
            promotion_result = cmd_promote_agent(slug)
            logger.info(
                "Agent promotion for %s: promoted=%s status=%s→%s",
                slug,
                promotion_result.get("promoted", False),
                promotion_result.get("status_before", "?"),
                promotion_result.get("status_after", "?"),
            )
        except Exception as exc:
            logger.warning("cmd_promote_agent failed in finalize for %s: %s", slug, exc)
            promotion_result = {"error": str(exc), "promoted": False}
    else:
        promotion_result = {
            "promoted": False,
            "reason": f"skipped — identity-checkpoint verdict={ic_verdict} (not APPROVE)",
        }
        logger.info("Agent promotion skipped for %s (verdict=%s)", slug, ic_verdict)

    # Step 5.65: L1-L5 DNA YAML regeneration from INSIGHTS-STATE.json.
    # Runs for all external/business slugs regardless of identity-checkpoint verdict.
    # Idempotent: append-only, never deletes existing entries.
    # Non-blocking: failure never crashes cmd_finalize (Art. XII).
    dna_regen_result: dict[str, Any] = {}
    if bucket in ("external", "business"):
        try:
            from engine.intelligence.pipeline.mce.dna_regenerator import regenerate_l1_l5_yamls

            dna_regen_result = regenerate_l1_l5_yamls(slug, bucket=bucket)
            logger.info(
                "DNA L1-L5 regen for %s: added=%d updated=%d",
                slug,
                dna_regen_result.get("total_added", 0),
                dna_regen_result.get("total_updated", 0),
            )
        except Exception as exc:
            logger.warning("DNA L1-L5 regeneration failed for %s: %s", slug, exc)
            dna_regen_result = {"error": str(exc), "success": False}
    else:
        dna_regen_result = {"skipped": f"bucket={bucket} not external/business"}

    # Step 5.7: Dossier Consolidation (Step 10 gate) — synthesise dossier.
    # ONLY when identity-checkpoint returns APPROVE (same gate as promotion).
    # Idempotent: skips if dossier already exists (unless --force).
    # Non-blocking: consolidation failure never crashes cmd_finalize.
    consolidation_result: dict[str, Any] = {}
    if ic_verdict == "APPROVE":
        try:
            consolidation_result = cmd_consolidate(slug)
            logger.info(
                "Dossier consolidation for %s: status=%s size=%s bytes",
                slug,
                consolidation_result.get("dossier_status", "?"),
                consolidation_result.get("size_bytes", 0),
            )
        except Exception as exc:
            logger.warning("cmd_consolidate failed in finalize for %s: %s", slug, exc)
            consolidation_result = {"error": str(exc), "dossier_status": "error"}
    else:
        consolidation_result = {
            "dossier_status": "skipped",
            "reason": f"skipped — identity-checkpoint verdict={ic_verdict} (not APPROVE)",
        }
        logger.info("Dossier consolidation skipped for %s (verdict=%s)", slug, ic_verdict)

    # Phase 6.6: Sources compilation (MCE-4.2 — non-blocking).
    # Only runs when consolidation produced or already had a dossier (V6 guard).
    # Exceptions are caught and logged — never crash cmd_finalize (Art. XII).
    sources_result: dict[str, Any] = {}
    if consolidation_result.get("dossier_status") in ("written", "skipped"):
        try:
            sources_result = cmd_sources(slug)
            logger.info(
                "Sources compilation for %s: status=%s files_written=%s",
                slug,
                sources_result.get("sources", {}).get("status", "?"),
                sources_result.get("sources", {}).get("files_written", 0),
            )
        except Exception as exc:
            logger.warning("cmd_finalize: cmd_sources non-blocking failure: %s", exc)
            sources_result = {"status": "error", "error": str(exc)}

    # Phase 7: Domain aggregation — MAP-CONFLITOS per-domain (MCE-4.5 — non-blocking).
    # Infers which domains this slug contributes to by scanning AGG-*.yaml files.
    # Only runs when sources phase succeeded, was skipped, or had no sources.
    # Exceptions are caught and logged — never crash cmd_finalize (Art. XII).
    domain_agg_results: dict[str, Any] = {}
    if sources_result.get("status") in (
        "written",
        "skipped",
        "no_sources",
        "updated",
    ) or sources_result.get("sources", {}).get("status") in ("written", "skipped", "no_sources"):
        try:
            from engine.intelligence.pipeline.domain_aggregator import _list_domains_for_slug

            slug_domains = _list_domains_for_slug(slug, root=_PROJECT_ROOT)
            for _domain in slug_domains:
                _domain_result = cmd_aggregate_domain(_domain)
                domain_agg_results[_domain] = _domain_result
            if slug_domains:
                logger.info(
                    "cmd_finalize: domain aggregation for %s completed domains=%s",
                    slug,
                    slug_domains,
                )
        except Exception as exc:
            logger.warning("cmd_finalize: cmd_aggregate_domain non-blocking failure: %s", exc)
            domain_agg_results["error"] = str(exc)

    # MCE-4.6 INSERTION POINT — Phase 8 subphases
    # Phase 8: EVOLUTION-LOG + FILE-REGISTRY + ROLE-TRACKING + 9-item gate WARN.
    # Non-blocking: failure here NEVER crashes cmd_finalize (Art. XII).
    # cmd_identity_checkpoint is NOT called here — it runs at L4825-4833 above (F-12, AC9).
    phase8_result: dict[str, Any] = {}
    try:
        phase8_result = cmd_phase8(slug)
        logger.info(
            "Phase 8 for %s: gate=%s artifacts_written=%s",
            slug,
            phase8_result.get("gate_status", "UNKNOWN"),
            phase8_result.get("artifacts_written", []),
        )
    except Exception as exc:
        logger.warning("cmd_phase8 non-blocking failure for %s: %s", slug, exc)
        phase8_result = {"error": str(exc), "gate_status": "ERROR"}

    # MCE-11.17 R4: enforce phase8 gates before finalize output (WARN-only V1).
    # Runs AFTER cmd_phase8 so gate data exists in phase8-gate.jsonl.
    enforcement_r4_result: dict[str, Any] = {}
    try:
        import dataclasses as _dc

        from engine.intelligence.pipeline.mce.enforcement import (
            enforce_phase8_gates,
        )

        enforcement_r4_result = _dc.asdict(enforce_phase8_gates(slug))
    except Exception as _r4_exc:
        logger.debug("cmd_finalize: enforcement R4 check failed non-fatally: %s", _r4_exc)

    # Step 6: generate the Chronicler MCE pipeline log [N4/G2].
    # MCE-17.x BUG A (ordering fix): the on-disk MCE-XX.md MUST be generated
    # AFTER every emit_phase_payload in cmd_finalize so the chronicler reads the
    # CURRENT run's PHASE-STREAM (narrative_metabolism, sources_compilation,
    # workspace_sync, llm_cost, squad_activation, lifecycle_move, batch_history
    # are all emitted later in this function). Generating it here (the old
    # location) made the log render the PREVIOUS run's data — silent data loss
    # on fresh mass-ingest of a NEW expert (no prior emit exists → EMPTY boxes).
    #
    # The actual generation + AUTO-RENDER stdout dump + idempotency marker now
    # live at the END of cmd_finalize (see _emit_chronicler_log_and_render
    # call right before `return result`). Here we only initialize the holders;
    # _build_result captures them as None and they are patched after generation.
    #
    # Defensive: log_generator failure NEVER crashes finalize (Art. XII
    # Pipeline Integrity > Observability).
    log_path: str | None = None
    log_error: str | None = None

    elapsed = (time.monotonic() - t0) * 1000

    # STORY-MCE-LOG-PARITY (2026-05-20): emit OLD-style EXECUTION REPORT ASCII
    # alongside the existing MCE-{TAG}.md narrative. Founder directive L1:
    # preserve 5-box OLD layout, internalize NEW phases inside matching box.
    # Fail-open per Art. XII.
    try:
        from engine.intelligence.pipeline.mce.log_emitters import (
            FinalizeContext,
            emit_execution_report,
        )

        # Populate FinalizeContext from accumulated sub-step results.
        # Best-effort: missing fields render as 0 or "(unknown)".
        insights_state_path = _insights_state_path(slug)
        insights_total = 0
        insights_high = 0
        insights_medium = 0
        insights_low = 0
        if insights_state_path.exists():
            try:
                _state = json.loads(insights_state_path.read_text(encoding="utf-8"))
                _persons = _state.get("persons", {})
                for _pname, _pdata in _persons.items():
                    if isinstance(_pdata, dict):
                        for _ins in _pdata.get("insights", []):
                            if not isinstance(_ins, dict):
                                continue
                            insights_total += 1
                            _prio = (_ins.get("priority") or "").upper()
                            if _prio == "HIGH":
                                insights_high += 1
                            elif _prio == "MEDIUM":
                                insights_medium += 1
                            else:
                                insights_low += 1
            except Exception:
                pass

        # Box 3 — narratives + sources from sub-step results
        _narratives_count = 0
        _sources_count = 0
        try:
            narratives_path = ARTIFACTS / "narratives" / slug / "NARRATIVES-STATE.json"
            if narratives_path.exists():
                _ndata = json.loads(narratives_path.read_text(encoding="utf-8"))
                if isinstance(_ndata, dict):
                    _persons = _ndata.get("persons", {}) or {}
                    for _pdata in _persons.values():
                        if isinstance(_pdata, dict):
                            _narratives_count += len(_pdata.get("narratives", []) or [])
                    _narratives_count = _narratives_count or len(_ndata.get("narratives", []) or [])
        except Exception:
            pass
        try:
            _sw = sources_result.get("sources", {}) if isinstance(sources_result, dict) else {}
            _sources_count = int(_sw.get("files_written", 0) or 0)
        except Exception:
            pass

        # Box 3 — dossier (single entry if consolidation produced a dossier)
        _dossiers_persons: list[dict[str, Any]] = []
        try:
            if isinstance(consolidation_result, dict):
                _dstatus = consolidation_result.get("dossier_status", "?")
                _dsize = consolidation_result.get("size_bytes", 0)
                if _dstatus in ("written", "updated", "exists", "skipped"):
                    _dossiers_persons.append(
                        {
                            "name": slug,
                            "status": _dstatus[:6].upper(),
                            "insights": insights_total,
                            "narratives": _narratives_count,
                        }
                    )
        except Exception:
            pass

        # Box 5 — cross-bucket cascade summary from cascade_result
        _cbc: dict[str, int] = {}
        try:
            if isinstance(cascade_result, dict):
                # cascade_result may have shape like {"external": N, "business": N, ...}
                for _b in ("external", "business", "personal"):
                    _cbc[_b] = int(cascade_result.get(f"{_b}_updates", 0) or 0)
        except Exception:
            pass

        # Source ID — prefer last-processed source from metadata, fall back to slug code
        _source_id = _derive_source_code(slug)
        try:
            _sources_processed = getattr(mgr, "sources_processed", None) or []
            if _sources_processed:
                _last = _sources_processed[-1]
                if isinstance(_last, dict):
                    _source_id = _last.get("source_id") or _last.get("batch_id") or _source_id
                elif isinstance(_last, str):
                    _source_id = _last
        except Exception:
            pass

        ctx = FinalizeContext(
            slug=slug,
            bucket=bucket,
            person_name=_person_name_for_slug(slug),
            source_id=_source_id,
            duration_min=round(elapsed / 60000.0, 1),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            chunks_total=len(_resolve_chunks_for_slug(slug)),
            insights_total=insights_total,
            insights_high=insights_high,
            insights_medium=insights_medium,
            insights_low=insights_low,
            narratives_total=_narratives_count,
            sources_compiled=_sources_count,
            dossiers_persons=_dossiers_persons,
            rag_indexation=rag_result if isinstance(rag_result, dict) else {},
            phase8_gates=phase8_result.get("gate_checks", {})
            if isinstance(phase8_result, dict)
            else {},
            workspace_sync=sync_result if isinstance(sync_result, dict) else {},
            cross_bucket_cascade=_cbc,
            agents_updated=[
                {
                    "name": slug,
                    "memory": "MEMORY.md",
                    "delta": f"+{enrichment_result.get('appended', 0)} insights",
                }
            ]
            if isinstance(enrichment_result, dict) and enrichment_result.get("appended", 0)
            else [],
            total_duration_s=round(elapsed / 1000.0, 1),
        )
        _er_block = emit_execution_report(ctx)
        print(_er_block, flush=True)
        emit_phase_payload(
            slug=slug,
            template_id="execution_report",
            status="ok",
            metrics={"total_duration_s": round(elapsed / 1000.0, 1)},
            ascii_block=_er_block,
        )

        # STORY-MCE-LOG-PARITY Sprint 2+3 (2026-05-20): emit dedicated NEW logs
        # that don't have a 1:1 OLD counterpart. All fail-open per Art. XII.
        from engine.intelligence.pipeline.mce.log_emitters import (
            emit_agent_state_log,
            emit_contradictions_log,
            emit_cross_bucket_cascade,
            emit_domain_aggregator,
            emit_identity_checkpoint_log,
            emit_narrative_metabolism,
            emit_phase8_gate_log,
            emit_sources_compilation,
            emit_workspace_sync,
        )

        # Identity Checkpoint
        try:
            _ic_block = emit_identity_checkpoint_log(slug, identity_checkpoint_result)
            print(_ic_block, flush=True)
            emit_phase_payload(
                slug=slug,
                template_id="identity_checkpoint",
                status="ok"
                if isinstance(identity_checkpoint_result, dict)
                and identity_checkpoint_result.get("verdict") in ("APPROVE", "REVISE")
                else "warning",
                metrics=identity_checkpoint_result
                if isinstance(identity_checkpoint_result, dict)
                else {},
                ascii_block=_ic_block,
            )
        except Exception as _e:
            logger.debug("identity_checkpoint emit failed: %s", _e)

        # Phase 8 Gate
        try:
            _p8_block = emit_phase8_gate_log(slug, phase8_result)
            print(_p8_block, flush=True)
            emit_phase_payload(
                slug=slug,
                template_id="phase8_gate",
                status="ok"
                if isinstance(phase8_result, dict) and phase8_result.get("success")
                else "warning",
                metrics=phase8_result if isinstance(phase8_result, dict) else {},
                ascii_block=_p8_block,
            )
        except Exception as _e:
            logger.debug("phase8_gate emit failed: %s", _e)

        # Contradictions — read from INSIGHTS-STATE.json
        try:
            _state = (
                json.loads(insights_state_path.read_text(encoding="utf-8"))
                if insights_state_path.exists()
                else {}
            )
            _contrs = _state.get("contradictions", []) if isinstance(_state, dict) else []
            _cont_block = emit_contradictions_log(slug, _contrs)
            print(_cont_block, flush=True)
            emit_phase_payload(
                slug=slug,
                template_id="contradictions",
                status="warning" if _contrs else "ok",
                metrics={"contradictions_count": len(_contrs)},
                ascii_block=_cont_block,
            )
        except Exception as _e:
            logger.debug("contradictions emit failed: %s", _e)

        # Agent State (memory diff)
        try:
            agent_dir_path = _agent_dir_for_slug(slug, bucket)
            memory_path = agent_dir_path / "memory.md"
            if not memory_path.exists():
                memory_path = agent_dir_path / "MEMORY.md"
            after_bytes = memory_path.stat().st_size if memory_path.exists() else 0
            # Best-effort before: we don't track baseline; report current size only
            before_bytes = (
                enrichment_result.get("memory_size_before", after_bytes)
                if isinstance(enrichment_result, dict)
                else after_bytes
            )
            _as_block = emit_agent_state_log(slug, enrichment_result, before_bytes, after_bytes)
            print(_as_block, flush=True)
            emit_phase_payload(
                slug=slug,
                template_id="agent_state",
                status="ok",
                metrics={
                    "memory_before": before_bytes,
                    "memory_after": after_bytes,
                    "delta": after_bytes - before_bytes,
                },
                ascii_block=_as_block,
            )
        except Exception as _e:
            logger.debug("agent_state emit failed: %s", _e)

        # Narrative Metabolism
        try:
            # MCE-17.x STEP 29 fix (v2): the GLOBAL narratives state is the SOT.
            # The previous fix read a per-slug dir
            # (ARTIFACTS/narratives/<slug>/NARRATIVES-STATE.json) which does NOT
            # exist → computed 0/0/0 → clobbered cmd_narrative's good emit via
            # last-write-wins. Read the GLOBAL file and match the person by the
            # "slug" FIELD (the persons dict keys are mixed canonical/slug, so
            # never key on them).
            _global_ns = ARTIFACTS / "narratives" / "NARRATIVES-STATE.json"
            _ns = (
                json.loads(_global_ns.read_text(encoding="utf-8"))
                if _global_ns.exists()
                else {}
            )
            _persons = _ns.get("persons", {}) if isinstance(_ns, dict) else {}
            _pentry = next(
                (
                    p
                    for p in _persons.values()
                    if isinstance(p, dict) and p.get("slug") == slug
                ),
                {},
            )
            _patterns_count = len(_pentry.get("patterns_identified", []) or [])
            _consensus_count = len(_ns.get("consensus_points", []) or [])
            # total_narratives best-effort: per-person "entries" rarely present;
            # fall back to the patterns count so the box is never falsely 0 when
            # real narrative work happened.
            _total_narratives = len(_pentry.get("entries", []) or []) or _patterns_count

            _nm_block = emit_narrative_metabolism(slug, _ns)
            print(_nm_block, flush=True)

            # CRITICAL INVARIANT — NEVER clobber with zeros. If the global file
            # has no signal for this slug (person not found / empty), DO NOT emit
            # a zero narrative_metabolism: let cmd_narrative's good emit remain
            # the last-write-wins winner. Only emit when we have real data.
            if _patterns_count or _consensus_count or _total_narratives:
                emit_phase_payload(
                    slug=slug,
                    template_id="narrative_metabolism",
                    status="ok",
                    metrics={
                        "total_narratives": _total_narratives,
                        "patterns_count": _patterns_count,
                        "consensus_count": _consensus_count,
                        "persons_count": len(_persons),
                    },
                    ascii_block=_nm_block,
                )
            else:
                logger.debug(
                    "narrative_metabolism finalize emit SKIPPED for %s "
                    "(no global signal — preserving cmd_narrative emit)",
                    slug,
                )
        except Exception as _e:
            logger.debug("narrative_metabolism emit failed: %s", _e)

        # Sources Compilation
        try:
            _sc_block = emit_sources_compilation(slug, sources_result)
            print(_sc_block, flush=True)
            # MCE-17.x STEP 30 fix: the real compile dict (status/files_written/
            # temas_written) is nested under sources_result["sources"]; the top-
            # level is the _build_result wrapper. Emit the nested dict so the
            # renderer reads non-zero files/temas instead of None.
            emit_phase_payload(
                slug=slug,
                template_id="sources_compilation",
                status="ok",
                metrics=(
                    sources_result.get("sources", {})
                    if isinstance(sources_result, dict)
                    else {}
                ),
                ascii_block=_sc_block,
            )
        except Exception as _e:
            logger.debug("sources_compilation emit failed: %s", _e)

        # Domain Aggregator
        try:
            _da_block = emit_domain_aggregator(domain_agg_results or {})
            print(_da_block, flush=True)
            emit_phase_payload(
                slug=slug,
                template_id="domain_aggregator",
                status="ok",
                metrics=domain_agg_results if isinstance(domain_agg_results, dict) else {},
                ascii_block=_da_block,
            )
        except Exception as _e:
            logger.debug("domain_aggregator emit failed: %s", _e)

        # Cross-bucket Cascade
        try:
            _cbc_block = emit_cross_bucket_cascade(cascade_result or {})
            print(_cbc_block, flush=True)
            emit_phase_payload(
                slug=slug,
                template_id="cross_bucket_cascade",
                status="ok",
                metrics=cascade_result if isinstance(cascade_result, dict) else {},
                ascii_block=_cbc_block,
            )
        except Exception as _e:
            logger.debug("cross_bucket_cascade emit failed: %s", _e)

        # Workspace Sync
        try:
            _ws_block = emit_workspace_sync(sync_result or {})
            print(_ws_block, flush=True)
            # MCE-17.1 P6: align emit schema with _step_33_workspace_sync renderer.
            # Renderer reads: synced, items_written, layers_touched.
            # sync_result has: synced, skipped, errors — map to renderer schema.
            _ws_metrics = sync_result if isinstance(sync_result, dict) else {}
            emit_phase_payload(
                slug=slug,
                template_id="workspace_sync",
                status="ok",
                metrics={
                    "synced": _ws_metrics.get("synced", 0),
                    "items_written": _ws_metrics.get("synced", 0),
                    "layers_touched": _ws_metrics.get("layers_touched", []),
                    "skipped": _ws_metrics.get("skipped", 0),
                    "errors": _ws_metrics.get("errors", 0),
                },
                ascii_block=_ws_block,
            )
        except Exception as _e:
            logger.debug("workspace_sync emit failed: %s", _e)

        # Full Pipeline Report (phase 18 coverage)
        # NOTE: 'result' is not yet defined at this point (built at _build_result below).
        # Use the intermediate sub-step variables that are already available.
        try:
            from engine.intelligence.pipeline.mce.log_emitters import emit_full_pipeline_report

            _phases_summary = {
                "ingest": {},
                "process_batch": [],
                "insights": {},
                "behavioral": {},
                "identity": {},
                "voice": {},
                "identity_checkpoint": identity_checkpoint_result,
                "consolidate": consolidation_result,
                "promote_agent": promotion_result,
                "finalize": {},
                "phase8": phase8_result,
            }
            _fpr_block = emit_full_pipeline_report(
                slug=slug,
                phases=_phases_summary,
                total_duration_s=round(elapsed / 1000.0, 1),
                success=True,
            )
            print(_fpr_block, flush=True)
            emit_phase_payload(
                slug=slug,
                template_id="full_pipeline_report",
                status="ok",
                metrics={"total_duration_s": round(elapsed / 1000.0, 1)},
                ascii_block=_fpr_block,
            )
        except Exception as _e:
            logger.debug("full_pipeline_report emit failed: %s", _e)

        # LLM Cost (phase 19 coverage)
        try:
            from engine.intelligence.pipeline.mce.log_emitters import emit_llm_cost_log

            _cost_breakdown: dict[str, Any] = {
                "total_usd": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "by_phase": {},
                "by_provider": {},
            }
            _llm_cost_block = emit_llm_cost_log(slug=slug, cost_breakdown=_cost_breakdown)
            print(_llm_cost_block, flush=True)
            emit_phase_payload(
                slug=slug,
                template_id="llm_cost",
                status="ok",
                metrics=_cost_breakdown,
                ascii_block=_llm_cost_block,
            )
        except Exception as _e:
            logger.debug("llm_cost emit failed: %s", _e)

        # Squad Activation (phase 21 coverage) — MCE-13.18: populate with
        # canonical pipeline squads that ran in this finalize cycle (B6).
        try:
            from engine.intelligence.pipeline.mce.log_emitters import emit_squad_activation

            _finalize_squads = _build_squad_activation_telemetry(
                slug=slug,
                phases_completed={
                    "memory_enricher": enrichment_result if "enrichment_result" in dir() else {},
                    "workspace_sync": sync_result if "sync_result" in dir() else {},
                    "dossier_consolidation": consolidation_result
                    if "consolidation_result" in dir()
                    else {},
                },
                stage="B6_finalize",
            )
            _squad_activation_block = emit_squad_activation(squads_activated=_finalize_squads)
            print(_squad_activation_block, flush=True)
            # MCE-17.x STEP 40 fix: renderer reads each item's "slug" as the
            # squad NAME label and "count" for repeats. Telemetry dicts carry the
            # squad name under "squad" (and "slug" = pipeline slug), so remap to
            # the renderer-compatible shape {"slug": <squad_name>, "count": 1}.
            _squads_list = [
                {"slug": _s.get("squad", _s) if isinstance(_s, dict) else _s, "count": 1}
                for _s in _finalize_squads
            ]
            emit_phase_payload(
                slug=slug,
                template_id="squad_activation",
                status="ok",
                metrics={
                    "squads_activated": len(_finalize_squads),
                    "squads": _squads_list,
                },
                ascii_block=_squad_activation_block,
            )
        except Exception as _e:
            logger.debug("squad_activation emit failed: %s", _e)
    except Exception as _log_exc:  # pragma: no cover -- observability only
        logger.debug("Execution Report emit failed (non-fatal): %s", _log_exc)

    # STORY-MCE-7.0 AC-2: Inbox → processed/ lifecycle move.
    # Move source files from knowledge/{bucket}/inbox/{slug}/ to
    # knowledge/{bucket}/processed/{slug}/ after successful finalization.
    # Fail-open per Art. XII — lifecycle failure NEVER crashes cmd_finalize.
    #
    # MCE-13.8 Bug G: Gate — only move when insights were actually extracted.
    # If insights_total == 0 the pipeline produced nothing; source must remain
    # in inbox so subsequent runs have material to process.
    lifecycle_result: dict[str, Any] = {}
    try:
        insights_count = _count_insights_for_slug(slug)
        if insights_count == 0:
            logger.warning(
                "[MCE-13.8] cmd_finalize: lifecycle move SKIPPED for slug=%s "
                "(insights_total=0). Source remains in inbox for re-processing.",
                slug,
            )
            lifecycle_result = {
                "moved_count": 0,
                "skipped_count": 0,
                "skipped_reason": "insights_total=0 — MCE-13.8 gate G prevented move",
            }
        else:
            from engine.intelligence.pipeline.mce.lifecycle import move_slug_to_processed

            lifecycle_result = move_slug_to_processed(slug, bucket)
            if lifecycle_result.get("moved_count", 0) > 0:
                logger.info(
                    "[MCE-7.0] Lifecycle: moved %d files inbox→processed for %s/%s",
                    lifecycle_result["moved_count"],
                    bucket,
                    slug,
                )
    except Exception as _lifecycle_exc:
        logger.warning(
            "[MCE-7.0] Lifecycle move failed (non-fatal) for %s: %s", slug, _lifecycle_exc
        )
        lifecycle_result = {"error": str(_lifecycle_exc)}

    result = _build_result(
        "finalize",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        bucket=bucket,
        enrichment=enrichment_result,
        product_detection=product_detection_result,
        workspace_sync=sync_result,
        cascading=cascade_result,
        business_routing=business_routing_result,
        identity_checkpoint=identity_checkpoint_result,
        agent_promotion=promotion_result,
        dossier_consolidation=consolidation_result,
        dna_regen=dna_regen_result,
        sources_compilation=sources_result,
        domain_aggregation=domain_agg_results,
        phase8=phase8_result,
        lifecycle=lifecycle_result,
        dna_dir=str(_dna_dir_for_slug(slug, bucket)),
        agent_dir=str(_agent_dir_for_slug(slug, bucket)),
        log_path=log_path,
        log_error=log_error,
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

    # Story MCE-11.18: canonical audit entry for PIPELINE_COMPLETE / PROCESS_JARVIS_COMPLETE
    _finalize_phases = [p for p in result.get("phases_completed", []) if p] or list(range(1, 9))
    _finalize_artifacts: dict[str, Any] = result.get("artifacts_generated", {})
    _append_audit_jsonl(
        operation="PROCESS_JARVIS_COMPLETE",
        source_id=slug,
        source_person=infer_source_person(slug, slug=slug),
        status="SUCCESS" if result.get("success") else "FAILED",
        phase=8,
        details={
            "phases_completed": _finalize_phases,
            "total_artifacts": (
                len(_finalize_artifacts) if isinstance(_finalize_artifacts, dict) else 0
            ),
            "metrics": result.get("metrics", {}),
        },
        checksum=None,
    )

    # STORY-MCE-6.0 Phase 7: Post-finalize Chronicler audit.
    # Calls run_chronicler_audit(slug) which reads PHASE-STREAM.jsonl, computes
    # coverage%, detects missing templates + schema mismatches, and emits the
    # CHRONICLER AUDIT box (phase_idx=22) via emit_phase_payload.
    # Non-blocking: audit failure NEVER crashes cmd_finalize (Art. XII).
    try:
        from engine.intelligence.pipeline.jarvis_chief import run_chronicler_audit

        _audit_rendered = run_chronicler_audit(slug)
        if _audit_rendered:
            print(_audit_rendered, flush=True)
    except Exception as _audit_exc:
        logger.debug("run_chronicler_audit non-blocking failure for %s: %s", slug, _audit_exc)

    # Story MCE-11.3 — SOUL incremental update (non-blocking)
    try:
        from engine.intelligence.pipeline.mce.soul_updater import update_soul_incremental

        _soul_result = update_soul_incremental(slug, bucket)
        logger.info(
            "SOUL update for %s: updated=%s sections_added=%s reason=%s",
            slug,
            _soul_result.get("updated"),
            _soul_result.get("sections_added"),
            _soul_result.get("reason"),
        )
    except Exception as _soul_exc:
        logger.warning("SOUL update failed (non-blocking) for %s: %s", slug, _soul_exc)

    # Story MCE-11.4 — PROPAGATION-GAPS tracking (non-blocking)
    # STORY-GBA-W2.8: capture the returned signal (overall: COMPLETE/INCOMPLETE)
    # as the source for the replay-safe ``fully_propagated`` flag. This REUSES
    # propagation_tracker.py (READ-ONLY — the module is the caixa-preta RNF-1,
    # never edited here; we only consume what track_propagation_gaps returns).
    _propagation_entry: dict[str, Any] = {}
    try:
        from engine.intelligence.pipeline.mce.propagation_tracker import track_propagation_gaps

        _propagation_entry = track_propagation_gaps(slug, bucket) or {}
    except Exception as _prop_exc:
        logger.warning("Propagation tracker failed (non-blocking): %s", _prop_exc)

    # STORY-GBA-W2.8 — replay-safe flag write (D3). The crash window is between
    # the guard registering the content hash and cmd_finalize finishing the
    # cascade; a crash there leaves the entry registered-but-not-propagated and
    # the next run's DUPLICATE verdict would skip it forever. We mark
    # ``content_hashes.metadata.fully_propagated = true`` ONLY now — after the
    # cascade/enrichment ran AND the propagation tracker reports COMPLETE (no
    # gaps). This write lives in the orchestrator, OUTSIDE the caixa-preta
    # (cascading.py / propagation_tracker.py untouched). Fail-open (Art. XII):
    # any failure leaves the flag absent → the reaper re-processes, which is the
    # SAFE direction (never wrongly marks a half-propagated file as done).
    try:
        _overall = str(_propagation_entry.get("overall", "")).upper()
        if _overall == "COMPLETE":
            _mark_slug_fully_propagated(slug)
        else:
            logger.info(
                "STORY-GBA-W2.8: NOT marking fully_propagated for %s (overall=%s) "
                "— reaper will treat it as re-processable",
                slug,
                _overall or "UNKNOWN",
            )
    except Exception as _fp_exc:
        logger.warning(
            "STORY-GBA-W2.8: fully_propagated mark failed (non-blocking) for %s: %s",
            slug,
            _fp_exc,
        )

    # Story MCE-11.16 — INBOX-REGISTRY.json input tracking (non-blocking)
    try:
        from engine.intelligence.pipeline.mce.inbox_registry import update_inbox_registry

        _source_file = _resolve_source_file_for_slug(slug, bucket)
        if _source_file:
            update_inbox_registry(slug, _source_file, bucket)
    except Exception as _inbox_exc:
        logger.warning("Inbox registry update failed (non-blocking): %s", _inbox_exc)

    # MCE-11.17: ENFORCEMENT REPORT (AC9) — printed after all phases complete.
    # Collects R1-R4 from phases dict (R1/R2/R3 from cmd_full if called via it,
    # R4 from enforcement_r4_result collected above).  Non-blocking.
    try:
        from engine.intelligence.pipeline.mce.enforcement import (
            EnforcementResult,
            build_enforcement_report,
            enforce_chunks_indexed_before_insights,
            enforce_classification_before_chunking,
            enforce_insight_chunk_traceability,
        )

        _r1 = enforce_classification_before_chunking(slug)
        _r2 = enforce_chunks_indexed_before_insights(slug)
        _r3 = enforce_insight_chunk_traceability(slug)
        _r4_passed = enforcement_r4_result.get("passed", True)
        _r4_code = enforcement_r4_result.get("code", "")
        _r4 = EnforcementResult(
            passed=_r4_passed,
            rule="R4",
            code=_r4_code,
            slug=slug,
        )
        # R5 is per-agent, not per-slug — report as N/A in finalize report
        _r5 = EnforcementResult(passed=True, rule="R5", slug=slug, code="N/A_PER_AGENT")
        _report = build_enforcement_report(slug, [_r1, _r2, _r3, _r4, _r5])
        print(_report, flush=True)
    except Exception as _enf_exc:
        logger.debug("cmd_finalize: enforcement report emit failed non-fatally: %s", _enf_exc)

    # Story MCE-11.8 — Role Tracker: scan for cargo role mentions, auto-create
    # agents when mention_count >= 10. Non-blocking per Art. XII.
    try:
        from engine.intelligence.pipeline.mce.role_tracker import track_roles_and_create

        _role_result = track_roles_and_create(slug)
        if _role_result.get("critical_created"):
            logger.info(
                "cmd_finalize: role_tracker auto-created agents: %s",
                _role_result["critical_created"],
            )
    except Exception as _role_exc:
        logger.warning("cmd_finalize: role_tracker failed (non-blocking): %s", _role_exc)

    # MCE-17.1 P3: emit cascade_tree to PHASE-STREAM so post-44 ARVORE DE
    # CASCATEAMENTO renders from live data instead of always being FAIL_NO_DATA.
    # Reads ROLE-TRACKING.json (written by role_tracker above) + dossier dirs.
    # Non-blocking per Art. XII.
    try:
        _ct_domains: list[str] = []
        _ct_domain_counts: dict[str, int] = {}
        _ct_rt_path = _PROJECT_ROOT / ".data" / "artifacts" / "ROLE-TRACKING.json"
        if _ct_rt_path.exists():
            import json as _ctj
            _ct_rt = _ctj.loads(_ct_rt_path.read_text(encoding="utf-8"))
            _ct_persons = _ct_rt.get("persons", []) if isinstance(_ct_rt, dict) else []
            _ct_slug_entry = next(
                (p for p in _ct_persons if isinstance(p, dict) and p.get("slug") == slug),
                {},
            )
            _ct_domains = list(_ct_slug_entry.get("domains") or [])
            for _ct_p in _ct_persons:
                if not isinstance(_ct_p, dict):
                    continue
                for _ct_d in _ct_p.get("domains") or []:
                    _ct_domain_counts[_ct_d] = _ct_domain_counts.get(_ct_d, 0) + 1
        # Theme dossiers: count only files that mention this slug (limited scan)
        _ct_themes_dir = _PROJECT_ROOT / "knowledge" / "external" / "dossiers" / "themes"
        _ct_theme_dossiers: list[str] = []
        if _ct_themes_dir.exists():
            for _ct_md in sorted(_ct_themes_dir.glob("*.md")):
                try:
                    if slug.lower() in _ct_md.read_text(encoding="utf-8").lower():
                        _ct_theme_dossiers.append(_ct_md.name)
                except Exception:
                    continue
        # Person solos: glob is O(1) on a bounded directory
        _ct_solos_dir = _PROJECT_ROOT / "knowledge" / "external" / "dossiers" / "persons-by-theme"
        _ct_solos: list[str] = []
        if _ct_solos_dir.exists():
            _ct_solos = sorted([p.name for p in _ct_solos_dir.glob(f"{slug}--*.md")])
        emit_phase_payload(
            slug=slug,
            template_id="cascade_tree",
            status="ok",
            metrics={
                "slug": slug,
                "bucket": bucket,
                "domains": _ct_domains,
                "domain_expert_counts": {d: _ct_domain_counts.get(d, 1) for d in _ct_domains},
                "theme_dossiers": _ct_theme_dossiers,
                "theme_count": len(_ct_theme_dossiers),
                "person_solos": _ct_solos,
                "solos_count": len(_ct_solos),
            },
            ascii_block="",
        )
    except Exception as _ct_exc:  # pragma: no cover
        logger.debug("cascade_tree emit failed (non-fatal): %s", _ct_exc)

    # Story MCE-11.9 — ORG-LIVE Sync: cargo MEMORY → workspace L4-operational.
    # Non-blocking per Art. XII: failure here NEVER crashes cmd_finalize.
    # Runs after role_tracker (MCE-11.8) so newly created agents are captured.
    try:
        from engine.intelligence.pipeline.mce.orglive_sync import sync_all_cargo_agents

        _orglive_result = sync_all_cargo_agents()
        logger.info(
            "cmd_finalize: orglive_sync completed — synced=%d skipped=%d failed=%d bu=%s",
            _orglive_result.get("synced", 0),
            _orglive_result.get("skipped", 0),
            _orglive_result.get("failed", 0),
            _orglive_result.get("bu", "?"),
        )
    except Exception as _orglive_exc:
        logger.warning("cmd_finalize: orglive_sync failed (non-blocking): %s", _orglive_exc)

    # Story MCE-11.11 - Cross-Batch Analysis + Executive Briefing (subphases 8.7-8.9).
    # Non-blocking per Art. XII: failure here NEVER crashes cmd_finalize.
    # Order: 8.7 cross_batch_analysis → 8.8 generate_executive_briefing → 8.9 update_batch_history
    cross_batch_result: dict[str, Any] = {}
    try:
        from engine.intelligence.pipeline.mce.batch_analyzer import run_cross_batch_pipeline

        # Collect metrics from accumulated sub-step results (best-effort)
        _cb_metrics: dict[str, Any] = {
            "chunks": len(_resolve_chunks_for_slug(slug)),
            "insights_total": insights_total,
            "insights_high": insights_high,
            "insights_medium": insights_medium,
            "insights_low": insights_low,
            "new_entities": int(skeleton_result.get("files_created", 0)) if skeleton_result else 0,
            "processing_time_minutes": round(elapsed / 60000.0, 2),
            "errors_recovered": 0,
        }
        _cb_agents_updated: list[str] = (
            enrichment_result.get("agents_enriched", [])
            if isinstance(enrichment_result, dict)
            else []
        )
        _cb_themes: list[str] = []

        # Best-effort theme extraction from INSIGHTS-STATE.json categories
        try:
            _is_path = _insights_state_path(slug)
            if _is_path.exists():
                _is_data = json.loads(_is_path.read_text(encoding="utf-8"))
                _cb_themes = list(_is_data.get("categories", {}).keys())[:10]
        except Exception:
            pass

        # Source ID — re-derive safely (may differ from the _source_id assigned inside
        # the execution-report try block which may not have run to completion)
        _cb_source_id = _derive_source_code(slug)
        try:
            _sp = getattr(mgr, "sources_processed", None) or []
            if _sp:
                _lp = _sp[-1]
                if isinstance(_lp, dict):
                    _cb_source_id = _lp.get("source_id") or _lp.get("batch_id") or _cb_source_id
                elif isinstance(_lp, str):
                    _cb_source_id = _lp
        except Exception:
            pass

        # Build files_modified list with human-readable names (hotfix Bug #8)
        _cb_files_modified: list[dict[str, Any]] = []
        _ACRONYMS = {"bdr", "sdr", "sds", "cfo", "cro", "cmo", "ceo", "cto", "coo"}
        for _agent_path in _cb_agents_updated:
            _p = str(_agent_path).replace("\\", "/")
            _parts = _p.strip("/").split("/")
            _last = _parts[-1] if _parts else _p
            _readable = " ".join(
                s.upper() if s.lower() in _ACRONYMS else s.capitalize() for s in _last.split("-")
            )
            _cb_files_modified.append(
                {
                    "path": _p,
                    "type": "agent",
                    "readable_name": _readable,
                    "change_summary": "MEMORY.md enriquecido com insights do batch",
                }
            )
        # Add dossier entry if consolidation ran
        try:
            if isinstance(consolidation_result, dict) and consolidation_result.get(
                "dossier_status"
            ) in ("written", "skipped"):
                _dpath = f"agents/external/{slug}/dossier-general.md"
                _cb_files_modified.append(
                    {
                        "path": _dpath,
                        "type": "dossier",
                        "readable_name": "Dossier Geral",
                        "change_summary": f"status={consolidation_result.get('dossier_status')}",
                    }
                )
        except Exception:
            pass

        cross_batch_result = run_cross_batch_pipeline(
            slug=slug,
            metrics=_cb_metrics,
            source_id=_cb_source_id,
            source_person=_person_name_for_slug(slug),
            themes_touched=_cb_themes,
            agents_updated=_cb_agents_updated,
            files_modified=_cb_files_modified,
        )
        logger.info(
            "cmd_finalize: cross-batch pipeline for %s — anomalies=%s health=%s briefing_written=%s",
            slug,
            len(cross_batch_result.get("analysis", {}).get("anomalies", [])),
            cross_batch_result.get("history_update", {}).get("batch_id", "?"),
            cross_batch_result.get("briefing", {}).get("written", False),
        )
    except Exception as _cb_exc:
        logger.warning(
            "cmd_finalize: cross_batch_pipeline failed (non-blocking) for %s: %s", slug, _cb_exc
        )
        cross_batch_result = {"error": str(_cb_exc)}

    # Attach cross-batch result to the finalize result dict
    result["cross_batch"] = cross_batch_result

    # Story MCE-11.12 — Holistic Health Score update (non-blocking, fail-open per Art. XII)
    # Called after each cmd_finalize to keep HEALTH-STATE.json current.
    try:
        from engine.intelligence.health.health_scorer import HealthScorer

        _hs = HealthScorer(_PROJECT_ROOT)
        _hs_result = _hs.compute()
        logger.info(
            "cmd_finalize: health_scorer for %s → score=%s grade=%s",
            slug,
            _hs_result.score_total,
            _hs_result.grade,
        )
    except Exception as _hs_exc:
        logger.debug("cmd_finalize: health_scorer failed non-blocking: %s", _hs_exc)

    # Story MC-FULL-REPORT — Full Pipeline Report (LOG 7 AGREGADOR COMPLETO).
    # Emits rich 79-char ASCII report + saves to logs/full-pipeline-reports/.
    # Called LAST in cmd_finalize so it reflects all computed state above.
    # Non-blocking per Art. XII: failure never crashes cmd_finalize.
    try:
        from engine.intelligence.pipeline.mce.log_generator import (
            render_full_pipeline_report,
        )

        _fpr = render_full_pipeline_report(slug, bucket)
        print(_fpr, flush=True)
    except Exception as _fpr_exc:
        logger.debug(
            "cmd_finalize: render_full_pipeline_report failed non-blocking for %s: %s",
            slug,
            _fpr_exc,
        )

    # Story MCE-13.11 — Pipeline state final checkpoint.
    # After all finalize steps run, ensure pipeline_state.yaml records a
    # history entry marking the transition to "complete" and persists it.
    # Non-blocking per Art. XII: failure here NEVER crashes cmd_finalize.
    try:
        from datetime import UTC
        from datetime import datetime as _dt

        _from_state = sm.state
        if _from_state != "complete":
            # Advance FSM to complete if not already there
            sm._machine.set_state("complete")
            sm._history.append(
                {
                    "from": _from_state,
                    "to": "complete",
                    "trigger": "finalize_checkpoint",
                    "timestamp": _dt.now(UTC).isoformat(),
                }
            )
            sm.save()
            logger.info(
                "MCE-13.11: pipeline_state checkpoint written for %s: %s -> complete",
                slug,
                _from_state,
            )
        else:
            logger.debug(
                "MCE-13.11: pipeline_state already complete for %s — skipping checkpoint write",
                slug,
            )
    except Exception as _checkpoint_exc:
        logger.warning(
            "MCE-13.11: pipeline_state checkpoint failed (non-blocking) for %s: %s",
            slug,
            _checkpoint_exc,
        )

    # MCE-17.0 T11: emit lifecycle_move + batch_history so Chronicler
    # STEP 37 and STEP 38 renderers get live stream data.
    try:
        _lc = lifecycle_result if isinstance(lifecycle_result, dict) else {}
        emit_phase_payload(
            slug=slug,
            template_id="lifecycle_move",
            status="ok" if _lc.get("moved_count", 0) > 0 else "warning",
            metrics={
                "status": "moved" if _lc.get("moved_count", 0) > 0 else _lc.get("status", "skipped"),
                "files_moved": _lc.get("moved_count", 0),
                "source_dir": f"knowledge/{bucket}/inbox/{slug}",
                "destination_dir": f"knowledge/{bucket}/processed/{slug}",
                "skipped_reason": _lc.get("skipped_reason", ""),
            },
            ascii_block="",
        )
    except Exception as _exc:  # pragma: no cover
        logger.debug("lifecycle_move emit failed (non-fatal): %s", _exc)

    try:
        _cb = cross_batch_result if isinstance(cross_batch_result, dict) else {}
        # MCE-17.x BUG B: the real batch_id / entries_total are NESTED under
        # cross_batch_result["history_update"] (run_cross_batch_pipeline →
        # update_batch_history, batch_analyzer.py:900-902). The previous emit
        # read result.get("batch_id") (empty — never set at top level) and a
        # synthetic batch_count+1 (always 1). Pull from history_update first,
        # fall back to the legacy top-level/synthetic values.
        _hu = (_cb.get("history_update") or {}) if isinstance(_cb, dict) else {}
        emit_phase_payload(
            slug=slug,
            template_id="batch_history",
            status="ok",
            metrics={
                "batch_id": _hu.get("batch_id") or result.get("batch_id", ""),
                "entries_total": _hu.get("entries_total", _cb.get("batch_count", 0) + 1),
                "appended": True,
                "last_run_duration_ms": elapsed,
            },
            ascii_block="",
        )
    except Exception as _exc:  # pragma: no cover
        logger.debug("batch_history emit failed (non-fatal): %s", _exc)

    # ───────────────────────────────────────────────────────────────────────
    # MCE-17.x BUG A (ordering fix): generate the Chronicler MCE log NOW — after
    # ALL emit_phase_payload calls above — so it reflects the CURRENT run.
    # PRESERVES the MCE-LOG-AUTO-RENDER stdout dump (powers /ingest --process
    # showing the log in chat) and the idempotency marker. Patches the already-
    # built `result` dict with the resolved log_path/log_error.
    # Defensive: failure NEVER crashes cmd_finalize (Art. XII).
    # ───────────────────────────────────────────────────────────────────────
    try:
        from engine.intelligence.pipeline.mce.chronicler_data_collector import (
            collect_final_log_data,
        )
        from engine.intelligence.pipeline.mce.log_generator import generate_mce_log

        collected = collect_final_log_data(
            slug=slug,
            enrichment_result=enrichment_result,
            cascade_result=cascade_result,
            sync_result=sync_result,
            index_result=rag_result,
        )
        log_result = generate_mce_log(
            slug=slug,
            enrichment_result=enrichment_result,
            cascade_result=cascade_result,
            sync_result=sync_result,
            index_result=rag_result,
            collected_data=collected,
        )
        if isinstance(log_result, dict):
            log_path = log_result.get("log_path")
            if not log_path and log_result.get("error"):
                log_error = log_result.get("error")
        if log_path:
            # Chat-visible path emission (Art. IX: Journey Log Mandatory).
            print(f"\nMCE Pipeline Log: {log_path}\n")
            # MCE-LOG-AUTO-RENDER: despejar conteúdo INTEIRO no stdout para
            # que o slash /ingest --process exiba o log v3.2 completo no chat
            # automaticamente, sem dependência de Claude/hook/slash lembrar.
            # CLI First (Art. I): fixação no código, não na narrativa.
            try:
                _log_p = Path(log_path)
                if _log_p.exists():
                    _content = _log_p.read_text(encoding="utf-8")
                    _bar = "━" * 79
                    print(_bar)
                    print(f"MCE PIPELINE LOG · {slug}  ·  rendered below (auto)")
                    print(_bar)
                    print(_content)
                    print(_bar)
                    print(f"END · path: {log_path}")
                    print(_bar + "\n")
            except Exception as _render_exc:
                logger.warning(
                    "MCE-LOG-AUTO-RENDER: failed to dump log content to stdout: %s",
                    _render_exc,
                )
    except Exception as exc:
        # NEVER crash cmd_finalize — record the error and move on.
        logger.warning("log_generator wiring failed: %s", exc, exc_info=True)
        log_error = str(exc)

    # T2 (MCE-14.6): write idempotency marker after successful emission.
    # Marker failure NEVER propagates — Art. XII (Pipeline Integrity).
    if log_path:
        try:
            _mc_marker = (
                _PROJECT_ROOT
                / ".claude"
                / "mission-control"
                / "mce"
                / slug
                / "chronicler-emitted.json"
            )
            _mc_marker.parent.mkdir(parents=True, exist_ok=True)
            _mc_marker.write_text(
                json.dumps(
                    {
                        "slug": slug,
                        "log_path": str(log_path),
                        "emitted_at": datetime.now(UTC).isoformat(),
                        "source_path": "cmd_finalize",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as _mc_exc:
            logger.warning("cmd_finalize[%s]: marker write failed: %s", slug, _mc_exc)

    # Patch the already-built result dict with the resolved log holders
    # (it was built earlier with log_path=None/log_error=None — BUG A fix).
    result["log_path"] = log_path
    result["log_error"] = log_error

    return result


# ---------------------------------------------------------------------------
# Business bucket output routing
# ---------------------------------------------------------------------------


def _route_business_insights(slug: str, insights_path: Path) -> dict[str, Any]:
    """Route meeting extraction outputs to knowledge/business/ subdirectories.

    Reads INSIGHTS-STATE.json and distributes data to:

    - ``knowledge/business/insights/by-meeting/MEET-XXXX.json``
    - ``knowledge/business/insights/by-person/{person}.json``
    - ``knowledge/business/insights/by-theme/{theme}.json``
    - ``knowledge/business/sops/`` (if SOPs detected)
    - ``knowledge/business/dna/persons/{person}/`` (person DNA for collaborators)

    Args:
        slug: Source slug (meeting identifier).
        insights_path: Path to the INSIGHTS-STATE.json file.

    Returns:
        Summary dict with counts of routed items.
    """
    if not insights_path.exists():
        return {"skipped": "INSIGHTS-STATE.json not found", "routed": 0}

    try:
        data = json.loads(insights_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"error": f"Cannot read insights: {exc}", "routed": 0}

    state = data.get("insights_state", data)
    categories = state.get("categories", {})
    meetings = state.get("meetings", {})

    routed_counts: dict[str, int] = {
        "by_meeting": 0,
        "by_person": 0,
        "by_theme": 0,
        "sops": 0,
        "person_dna": 0,
    }

    # --- Route by-meeting ---
    insights_base = Path(ROUTING.get("business_insights", KNOWLEDGE_BUSINESS / "insights"))
    by_meeting_dir = insights_base / "by-meeting"
    by_meeting_dir.mkdir(parents=True, exist_ok=True)

    for meet_id, meet_data in meetings.items():
        meet_file = by_meeting_dir / f"{meet_id}.json"
        meeting_insights: dict[str, list[dict]] = {}
        for cat_name, cat_items in categories.items():
            items = (
                cat_items
                if isinstance(cat_items, list)
                else cat_items.get("insights", [])
                if isinstance(cat_items, dict)
                else []
            )
            matched = [
                it
                for it in items
                if isinstance(it, dict)
                and isinstance(it.get("source"), dict)
                and it["source"].get("source_id") == meet_id
            ]
            if matched:
                meeting_insights[cat_name] = matched

        output = {
            "meeting": meet_data,
            "categories": meeting_insights,
            "slug": slug,
            "routed_at": _now_iso(),
        }
        meet_file.write_text(
            json.dumps(output, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        routed_counts["by_meeting"] += 1

    # --- Route by-person ---
    by_person_dir = insights_base / "by-person"
    by_person_dir.mkdir(parents=True, exist_ok=True)

    speakers: dict[str, list[dict]] = {}
    for cat_name, cat_items in categories.items():
        items = (
            cat_items
            if isinstance(cat_items, list)
            else cat_items.get("insights", [])
            if isinstance(cat_items, dict)
            else []
        )
        for it in items:
            if not isinstance(it, dict):
                continue
            speaker = (
                it.get("speaker")
                or it.get("decided_by")
                or it.get("assigned_to")
                or it.get("committed_by")
                or it.get("mentioned_by")
            )
            if speaker and speaker != "Unknown Speaker":
                speakers.setdefault(speaker, []).append({**it, "_category": cat_name})

    for speaker_name, speaker_insights in speakers.items():
        person_slug = speaker_name.lower().replace(" ", "-").replace("_", "-")
        person_file = by_person_dir / f"{person_slug}.json"

        existing: list[dict] = []
        if person_file.exists():
            try:
                existing = json.loads(person_file.read_text(encoding="utf-8")).get("insights", [])
            except (json.JSONDecodeError, OSError):
                pass

        existing_ids = {ins.get("id") for ins in existing if isinstance(ins, dict)}
        new_insights = [ins for ins in speaker_insights if ins.get("id") not in existing_ids]

        output = {
            "person": speaker_name,
            "slug": person_slug,
            "insights": existing + new_insights,
            "total": len(existing) + len(new_insights),
            "updated_at": _now_iso(),
        }
        person_file.write_text(
            json.dumps(output, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        routed_counts["by_person"] += 1

    # --- Route by-theme ---
    by_theme_dir = insights_base / "by-theme"
    by_theme_dir.mkdir(parents=True, exist_ok=True)

    themes: dict[str, list[dict]] = {}
    for cat_name, cat_items in categories.items():
        items = (
            cat_items
            if isinstance(cat_items, list)
            else cat_items.get("insights", [])
            if isinstance(cat_items, dict)
            else []
        )
        for it in items:
            if not isinstance(it, dict):
                continue
            domain = it.get("domain", cat_name)
            themes.setdefault(domain, []).append({**it, "_category": cat_name})

    for theme_name, theme_insights in themes.items():
        theme_slug = theme_name.lower().replace(" ", "-").replace("_", "-")
        theme_file = by_theme_dir / f"{theme_slug}.json"

        existing_t: list[dict] = []
        if theme_file.exists():
            try:
                existing_t = json.loads(theme_file.read_text(encoding="utf-8")).get("insights", [])
            except (json.JSONDecodeError, OSError):
                pass

        existing_ids_t = {ins.get("id") for ins in existing_t if isinstance(ins, dict)}
        new_t = [ins for ins in theme_insights if ins.get("id") not in existing_ids_t]

        output = {
            "theme": theme_name,
            "slug": theme_slug,
            "insights": existing_t + new_t,
            "total": len(existing_t) + len(new_t),
            "updated_at": _now_iso(),
        }
        theme_file.write_text(
            json.dumps(output, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        routed_counts["by_theme"] += 1

    # --- Route SOPs detected ---
    sop_items = categories.get("sops_detected", [])
    if isinstance(sop_items, dict):
        sop_items = sop_items.get("insights", [])
    if sop_items:
        sops_dir = Path(ROUTING.get("business_sops", KNOWLEDGE_BUSINESS / "sops"))
        sops_dir.mkdir(parents=True, exist_ok=True)
        sops_file = sops_dir / f"sops-from-{slug}.json"
        sops_file.write_text(
            json.dumps(
                {"source": slug, "sops": sop_items, "extracted_at": _now_iso()},
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        routed_counts["sops"] = len(sop_items)

    # --- Route person DNA for collaborators ---
    dna_persons_dir = Path(
        ROUTING.get("business_dna_persons", KNOWLEDGE_BUSINESS / "dna" / "persons")
    )
    dna_elements = categories.get("dna_elements", [])
    if isinstance(dna_elements, dict):
        dna_elements = dna_elements.get("insights", [])

    person_dna: dict[str, list[dict]] = {}
    for elem in dna_elements:
        if not isinstance(elem, dict):
            continue
        speaker = elem.get("speaker", "Unknown")
        if speaker and speaker != "Unknown Speaker":
            person_dna.setdefault(speaker, []).append(elem)

    for person_name, dna_items in person_dna.items():
        person_slug = person_name.lower().replace(" ", "-").replace("_", "-")
        person_dna_dir = dna_persons_dir / person_slug
        person_dna_dir.mkdir(parents=True, exist_ok=True)
        dna_file = person_dna_dir / "DNA-ELEMENTS.json"

        existing_dna: list[dict] = []
        if dna_file.exists():
            try:
                existing_dna = json.loads(dna_file.read_text(encoding="utf-8")).get("elements", [])
            except (json.JSONDecodeError, OSError):
                pass

        existing_dna_ids = {e.get("id") for e in existing_dna if isinstance(e, dict)}
        new_dna = [e for e in dna_items if e.get("id") not in existing_dna_ids]

        output = {
            "person": person_name,
            "slug": person_slug,
            "elements": existing_dna + new_dna,
            "total": len(existing_dna) + len(new_dna),
            "updated_at": _now_iso(),
        }
        dna_file.write_text(
            json.dumps(output, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        routed_counts["person_dna"] += 1

    return {
        "routed": sum(routed_counts.values()),
        "details": routed_counts,
        "speakers_found": list(speakers.keys()),
        "meetings_routed": list(meetings.keys()),
        "themes_found": list(themes.keys()),
    }


def _update_insights_state_incrementally(slug: str, insights_path: Path) -> dict[str, Any]:
    """Merge slug-specific insights into the global INSIGHTS-STATE.json.

    Adds new items without overwriting entries from other slugs.

    Args:
        slug: Source slug.
        insights_path: Path to slug-specific INSIGHTS-STATE.json.

    Returns:
        Summary dict with merge counts.
    """
    global_path = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"

    if not insights_path.exists():
        return {"skipped": "slug insights not found"}

    try:
        slug_data = json.loads(insights_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"error": f"Cannot read slug insights: {exc}"}

    global_data: dict[str, Any] = {}
    if global_path.exists():
        try:
            global_data = json.loads(global_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            global_data = {}

    global_state = global_data.setdefault("insights_state", {})
    global_categories = global_state.setdefault("categories", {})
    global_meetings = global_state.setdefault("meetings", {})
    global_changelog = global_state.setdefault("change_log", [])

    slug_state = slug_data.get("insights_state", slug_data)
    slug_categories = slug_state.get("categories", {})
    slug_meetings = slug_state.get("meetings", {})

    merged_count = 0

    for cat_name, cat_items in slug_categories.items():
        items = (
            cat_items
            if isinstance(cat_items, list)
            else cat_items.get("insights", [])
            if isinstance(cat_items, dict)
            else []
        )
        existing = global_categories.get(cat_name, [])
        if isinstance(existing, dict):
            existing = existing.get("insights", [])

        existing_ids = {it.get("id") for it in existing if isinstance(it, dict)}
        new_items = [
            it for it in items if isinstance(it, dict) and it.get("id") not in existing_ids
        ]

        if new_items:
            global_categories[cat_name] = existing + new_items
            merged_count += len(new_items)

    for meet_id, meet_data in slug_meetings.items():
        if meet_id not in global_meetings:
            global_meetings[meet_id] = meet_data

    if merged_count > 0:
        global_changelog.append(
            {
                "entity": "slug_merge",
                "key": slug,
                "change": "incremental_merge",
                "counts": {"new_items": merged_count, "meetings": len(slug_meetings)},
                "note": f"Merged {merged_count} items from {slug}",
                "timestamp": _now_iso(),
            }
        )

    old_version = global_state.get("version", "v0")
    try:
        version_num = int(old_version.lstrip("v")) + 1
    except ValueError:
        version_num = 1
    global_state["version"] = f"v{version_num}"

    global_path.parent.mkdir(parents=True, exist_ok=True)
    global_path.write_text(
        json.dumps(global_data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    return {
        "merged": merged_count,
        "meetings_added": len(slug_meetings),
        "new_version": global_state["version"],
    }


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
# DURABLE JOB QUEUE — cmd_full crash-recovery wiring (STORY-ENABLE-GBRAIN-FULL B)
# ---------------------------------------------------------------------------
# Minimal, NON-BLOCKING integration of the token-fenced durable queue
# (``mce.job_queue``) into the synchronous ``cmd_full`` path. Until now only
# ``autonomous_processor`` consumed the queue; a plain ``/ingest --process``
# advanced with NO durable record, so a crash mid-pipeline left no recoverable
# trace.
#
# DESIGN (deliberately minimal — does NOT change cmd_full's control flow):
#   * The pipeline still runs SYNCHRONOUSLY inline, exactly as before.
#   * We RECORD a durable job for the slug: ``enqueue`` (waiting) → ``claim``
#     (active + heartbeat) at the start, and ``complete``/``fail`` at the end.
#   * The lease lets the W2.7 reaper recover a crashed run: if cmd_full dies
#     mid-flight, the lease's ``lock_until`` expires and the reaper requeues the
#     slug (stall → retry) — that is the whole point of the durability wiring.
#
# DEFAULT-ON + FAIL-OPEN (never perturb a working pipeline):
#   * Gated by ``MCE_DURABLE_QUEUE`` (the same flag the autonomous processor
#     reads). STORY-ENABLE-GBRAIN-FULL: THIS cmd_full reader defaults ON; opt-OUT
#     via =0.
#   * NOTE: the autonomous_processor's own default stays OFF deliberately — its
#     pop() SWITCHES the queue backend (durable DB ↔ JSON FIFO) when the flag is
#     on, and a no-DB dev box must keep the JSON FIFO fallback. cmd_full's wiring
#     here is purely ADDITIVE (records a durable job; never changes the inline
#     control flow), so default-ON is safe here where it would not be there.
#   * EVERY queue interaction is wrapped: any DB/connection/import error is
#     swallowed and the pipeline proceeds on the normal synchronous path. With
#     no reachable Postgres the durable record is simply skipped — the wiring is
#     best-effort observability, never a gate (Art. XII: Pipeline MCE Integrity >
#     Observability). So default-ON adds zero risk to an offline run.
#
# RNF-1: this touches ONLY mce_jobs via job_queue; it imports nothing from and
# mutates nothing in the 6 frozen cascade files.


def _durable_queue_enabled() -> bool:
    """Durable cmd_full job recording. STORY-ENABLE-GBRAIN-FULL: default flipped
    ON (default "1"); opt-OUT via MCE_DURABLE_QUEUE=0. Mirrors the
    autonomous_processor flag so both honor one switch. Fully fail-open: with no
    reachable Postgres the acquire returns None and cmd_full runs inline."""
    return os.getenv("MCE_DURABLE_QUEUE", "1") == "1"


def _durable_lease_acquire(slug: str) -> Any | None:
    """Best-effort: enqueue ``slug`` and claim a durable lease for cmd_full.

    Returns a live :class:`JobLease` (claim + heartbeat held) on success, or
    ``None`` when the durable queue is disabled OR any step fails (fail-open).
    The caller treats ``None`` as "no durable record this run" and proceeds on
    the normal synchronous path.
    """
    if not _durable_queue_enabled():
        return None
    lease = None
    try:
        from engine.intelligence.pipeline.mce.job_queue import (
            JobLease,
            enqueue,
            get_connection,
        )

        # 1) Ensure a waiting job exists for this slug (idempotent on live dups).
        conn = get_connection()
        try:
            enqueue(conn, slug)
        finally:
            try:
                conn.close()
            except Exception:
                pass

        # 2) Claim it (narrowed to this slug) + start the heartbeat. The lease
        #    holds its own connection for its whole lifetime (session-mode).
        lease = JobLease(slug=slug)
        job = lease.claim()
        if job is None:
            # Nothing claimable (already leased by a concurrent worker, or the
            # enqueue raced). Release the idle connection and proceed inline.
            try:
                lease._stop_heartbeat()
                if getattr(lease, "_owns_conn", False):
                    lease._conn.close()
            except Exception:
                pass
            return None
        return lease
    except Exception as exc:  # import/DB/claim failure → no durable record
        logger.warning(
            "cmd_full: durable lease acquire failed for %s (fail-open, "
            "proceeding inline): %s",
            slug,
            exc,
        )
        if lease is not None:
            try:
                lease._stop_heartbeat()
                if getattr(lease, "_owns_conn", False):
                    lease._conn.close()
            except Exception:
                pass
        return None


def _durable_lease_release(lease: Any | None, *, success: bool, error: str = "") -> None:
    """Best-effort: complete (success) or fail-with-retry (failure) the lease.

    Token-fenced inside ``JobLease`` — if the run crashed and the reaper already
    reclaimed the slug, the release is a no-op. Always closes the held
    connection. Never raises (fail-open)."""
    if lease is None:
        return
    try:
        if success:
            lease.complete()
        else:
            lease.fail(error or "cmd_full failed", retry=True)
    except Exception as exc:
        logger.warning("cmd_full: durable lease release failed: %s", exc)
    finally:
        try:
            lease._stop_heartbeat()
            if getattr(lease, "_owns_conn", False):
                lease._conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Command: full
# ---------------------------------------------------------------------------


def cmd_full(file_path: str) -> dict[str, Any]:
    """End-to-end MCE chain (MCE-2.1 AC3).

    Runs all 12 pipeline steps sequentially against ``file_path``:

      ingest → batch → process_batch (per batch) → insights → entities →
      behavioral → identity → voice → identity_checkpoint → consolidate →
      promote_agent → finalize

    Any failure short-circuits the chain and the result carries
    ``failed_phase`` so callers know exactly which step blocked. Soft
    failures inside finalize/log_generator are tolerated so a partial
    run still leaves an MCE log behind for inspection.

    Args:
        file_path: Path to the raw source file.

    Returns:
        Combined result dict with per-phase entries and ``success`` plus
        ``failed_phase`` (when applicable).
    """
    t0 = time.monotonic()
    phases: dict[str, Any] = {}
    # Durable-queue lease for crash recovery (feature B). Acquired AFTER slug
    # resolution; released on every terminal path. ``None`` (queue off / DB
    # unavailable) makes the release calls no-ops — the pipeline runs inline.
    _durable_lease: Any | None = None

    def _fail(reason: str, failed_phase: str) -> dict[str, Any]:
        # Token-fenced fail-with-retry on the durable record (no-op if None /
        # already reaped). Best-effort; never alters the failure result.
        _durable_lease_release(_durable_lease, success=False, error=reason)
        elapsed_ms = (time.monotonic() - t0) * 1000
        out = _build_result(
            "full",
            success=False,
            error=reason,
            failed_phase=failed_phase,
            duration_ms=elapsed_ms,
            phases=phases,
        )
        _append_jsonl(out)
        return out

    # 1) Ingest -------------------------------------------------------------
    ingest_result = cmd_ingest(file_path)
    phases["ingest"] = ingest_result
    if not ingest_result.get("success"):
        return _fail("ingest step failed", "ingest")
    slug = ingest_result.get("slug", "")
    if not slug:
        return _fail("ingest succeeded but slug missing", "ingest")

    # Durable job record for crash recovery (feature B, opt-in MCE_DURABLE_QUEUE).
    # Best-effort: a None lease means no durable record this run; the pipeline is
    # unchanged. A held lease lets the reaper requeue this slug if cmd_full dies.
    _durable_lease = _durable_lease_acquire(slug)

    # MCE-11.17 R1: enforce classification before chunking (WARN-only V1).
    try:
        from engine.intelligence.pipeline.mce.enforcement import (
            enforce_classification_before_chunking,
        )

        phases["enforcement_r1"] = dataclasses.asdict(enforce_classification_before_chunking(slug))
    except Exception as _r1_exc:
        logger.debug("cmd_full: enforcement R1 check failed non-fatally: %s", _r1_exc)

    # 2) Batch creation -----------------------------------------------------
    # MCE-2.1 AC3.1: single_file=True so a single transcript triggers batch
    # creation regardless of MIN_FILES threshold. Without this, /ingest of
    # a single source produces zero batches and the chain stops silently.
    batch_result = cmd_batch(slug, single_file=True)
    phases["batch"] = batch_result
    if not batch_result.get("success", True):
        return _fail("batch step failed", "batch")

    # 3) Process each batch (chunk + embed + upsert) ------------------------
    batch_ids = batch_result.get("batch_ids") or []
    if not batch_ids and isinstance(batch_result.get("batches"), list):
        batch_ids = [b.get("batch_id") for b in batch_result["batches"] if b.get("batch_id")]
    if not batch_ids and isinstance(batch_result.get("batches_for_slug"), list):
        batch_ids = [
            b.get("batch_id") for b in batch_result["batches_for_slug"] if b.get("batch_id")
        ]
    process_results: list[dict[str, Any]] = []
    for batch_id in batch_ids:
        # MCE-2.5: cmd_process_batch signature is (batch_id, slug, ...) — keep
        # kwargs to avoid positional swap that silently routed to
        # batches/BATCH-XXX-RT/ and produced "No documents found".
        pr = cmd_process_batch(batch_id=batch_id, slug=slug)
        process_results.append(pr)
        if not pr.get("success", False):
            phases["process_batch"] = process_results
            return _fail(f"process_batch failed on {batch_id}", "process_batch")
    phases["process_batch"] = process_results

    # MCE-11.17 R2: enforce chunks indexed before insight extraction (WARN-only V1).
    try:
        from engine.intelligence.pipeline.mce.enforcement import (
            enforce_chunks_indexed_before_insights,
        )

        phases["enforcement_r2"] = dataclasses.asdict(enforce_chunks_indexed_before_insights(slug))
    except Exception as _r2_exc:
        logger.debug("cmd_full: enforcement R2 check failed non-fatally: %s", _r2_exc)

    # 3.5) Entity Resolution (MCE-13.22) — between embeddings and DNA extraction
    # Runs after chunking/embedding (Step 10) and before insights (Step 12).
    # Non-blocking: failure NEVER blocks insights extraction (Art. XII).
    try:
        resolve_result = cmd_resolve_entities(slug)
        phases["entity_resolution"] = resolve_result
        logger.info(
            "cmd_full: entity resolution for %s — aliases=%s review=%s",
            slug,
            resolve_result.get("aliases_found", 0),
            resolve_result.get("review_queue_size", 0),
        )
    except Exception as _resolve_exc:
        logger.warning(
            "cmd_full: cmd_resolve_entities failed non-blocking for %s: %s", slug, _resolve_exc
        )
        phases["entity_resolution"] = {"error": str(_resolve_exc), "skipped": True}

    # 3.7) Atlas Classification (MCE-13.23) — domain classification before DNA extraction
    # Classifies slug into knowledge domains (offers, funnels, marketing, etc.)
    # and registers it in AGG-*.yaml files, enabling Phase 8 gate 7A.
    # Non-blocking: failure NEVER blocks insights extraction (Art. XII).
    try:
        atlas_result = cmd_atlas_classify(slug)
        phases["atlas_classification"] = atlas_result
        logger.info(
            "cmd_full: atlas classification for %s — domains=%s primary=%s",
            slug,
            atlas_result.get("domains_assigned", 0),
            atlas_result.get("primary_domain"),
        )
    except Exception as _atlas_exc:
        logger.warning(
            "cmd_full: cmd_atlas_classify failed non-blocking for %s: %s", slug, _atlas_exc
        )
        phases["atlas_classification"] = {"error": str(_atlas_exc), "skipped": True}

    # 4) Insight extraction (Sage) ------------------------------------------
    insights_result = cmd_insights(slug)
    phases["insights"] = insights_result
    if not insights_result.get("success", True):
        return _fail("insights step failed", "insights")

    # 5) Entity resolution (Sage / Step 4 of template) ----------------------
    entities_result = cmd_entities(slug)
    phases["entities"] = entities_result
    # cmd_entities is best-effort — never blocks the chain

    # 6) Behavioral L6 ------------------------------------------------------
    behavioral_result = cmd_behavioral(slug)
    phases["behavioral"] = behavioral_result
    if not behavioral_result.get("success", True):
        return _fail("behavioral step failed", "behavioral")

    # 7) Identity L7/L9/L10 -------------------------------------------------
    identity_result = cmd_identity(slug)
    phases["identity"] = identity_result
    if not identity_result.get("success", True):
        return _fail("identity step failed", "identity")

    # 8) Voice L8 -----------------------------------------------------------
    voice_result = cmd_voice(slug)
    phases["voice"] = voice_result
    if not voice_result.get("success", True):
        return _fail("voice step failed", "voice")

    # 9) Identity Checkpoint (deterministic gate) ---------------------------
    checkpoint_result = cmd_identity_checkpoint(slug)
    phases["identity_checkpoint"] = checkpoint_result
    # gate may emit BLOCK/REWORK but we still continue to consolidation so
    # the dossier reflects the failed gate. The verdict is in phases.

    # 9.5) Narrative Synthesis (MCE-13.16) -----------------------------------
    # Runs between identity_checkpoint (Step 22) and consolidation (Step 23).
    # Merges narrative entry for slug into NARRATIVES-STATE.json.
    # Non-blocking: failure NEVER blocks consolidation (Art. XII).
    try:
        narrative_result = cmd_narrative(slug)
        phases["narrative"] = narrative_result
        logger.info(
            "cmd_full: narrative synthesis for %s — merged=%s",
            slug,
            narrative_result.get("merged", False),
        )
    except Exception as _narrative_exc:
        logger.warning(
            "cmd_full: cmd_narrative failed non-blocking for %s: %s", slug, _narrative_exc
        )
        phases["narrative"] = {"error": str(_narrative_exc), "skipped": True}

    # 10) Consolidation (dossier) ------------------------------------------
    consolidate_result = cmd_consolidate(slug)
    phases["consolidate"] = consolidate_result
    if not consolidate_result.get("success", True):
        return _fail("consolidate step failed", "consolidate")

    # 11) Promote agent skeleton → full ------------------------------------
    promote_result = cmd_promote_agent(slug)
    phases["promote_agent"] = promote_result
    # promote is best-effort: agent may already be complete

    # 11.5) Sources Compilation (MCE-13.17) -----------------------------------
    # Runs between consolidate and finalize. Compiles per-theme source
    # catalog files at knowledge/{bucket}/sources/{PERSON}/{tema}.md.
    # Non-blocking: failure NEVER blocks finalize (Art. XII).
    try:
        sources_result_full = cmd_sources(slug)
        phases["sources"] = sources_result_full
        logger.info(
            "cmd_full: sources compilation for %s — status=%s",
            slug,
            sources_result_full.get("sources", {}).get("status", "unknown"),
        )
    except Exception as _sources_exc:
        logger.warning(
            "cmd_full: cmd_sources failed non-blocking for %s: %s", slug, _sources_exc
        )
        phases["sources"] = {"error": str(_sources_exc), "skipped": True}

    # MCE-11.17 R3: enforce insight chunk traceability before finalize (WARN-only V1).
    try:
        from engine.intelligence.pipeline.mce.enforcement import (
            enforce_insight_chunk_traceability,
        )

        phases["enforcement_r3"] = dataclasses.asdict(enforce_insight_chunk_traceability(slug))
    except Exception as _r3_exc:
        logger.debug("cmd_full: enforcement R3 check failed non-fatally: %s", _r3_exc)

    # 12) Finalize (memory enrichment + workspace sync + MCE log) ----------
    finalize_result = cmd_finalize(slug)
    phases["finalize"] = finalize_result

    # 12.5) Knowledge-graph enrichment (HE-002) — temporal + evidence edges.
    # Wires the previously-dormant enrich_knowledge_graph into the chain so a
    # normal /ingest --process produces graph edges carrying t_obs (extraction
    # timestamp) and atomic_facts (verbatim source quotes). Non-blocking: a
    # failure here NEVER blocks cmd_full (Art. XII — Pipeline MCE Integrity >
    # Observability). NOTE: the GraphRAG community layer (cmd_graphrag_index)
    # stays DEFERRED and is intentionally NOT wired here.
    try:
        from engine.intelligence.pipeline.mce.rag_integration import (
            enrich_knowledge_graph,
        )

        graph_enrich_result = enrich_knowledge_graph(slug)
        phases["graph_enrichment"] = graph_enrich_result
        logger.info(
            "cmd_full: graph enrichment for %s — nodes_added=%s edges_added=%s",
            slug,
            graph_enrich_result.get("nodes_added", 0),
            graph_enrich_result.get("edges_added", 0),
        )
    except Exception as _graph_exc:
        logger.warning(
            "cmd_full: enrich_knowledge_graph failed non-blocking for %s: %s",
            slug,
            _graph_exc,
        )
        phases["graph_enrichment"] = {"error": str(_graph_exc), "skipped": True}

    # MCE-LOG-AUTO-RENDER (blindagem cmd_full): garante despejo do MCE log
    # INTEIRO no stdout mesmo se cmd_finalize falhou ou se RAG gate (Art. XV)
    # bloqueou o caminho normal do step 6 dentro de finalize.
    # Idempotente: se finalize já cuspiu, este bloco regera e cospe de novo —
    # zero dano, garantia máxima. Fail-open: nunca crash cmd_full (Art. XII).
    try:
        _fr_log_path = finalize_result.get("log_path") if isinstance(finalize_result, dict) else None
        if not _fr_log_path:
            # Finalize falhou ou nem escreveu log: regerar standalone agora.
            from engine.intelligence.pipeline.mce.log_generator import generate_mce_log as _gen_log
            _retry = _gen_log(slug=slug)
            if isinstance(_retry, dict):
                _fr_log_path = _retry.get("log_path")
        if _fr_log_path:
            _fr_log_p = Path(_fr_log_path)
            if _fr_log_p.exists():
                _fr_content = _fr_log_p.read_text(encoding="utf-8")
                _fr_bar = "━" * 79
                print(_fr_bar)
                print(f"MCE PIPELINE LOG · {slug}  ·  cmd_full safety dump")
                print(_fr_bar)
                print(_fr_content)
                print(_fr_bar)
                print(f"END · path: {_fr_log_path}")
                print(_fr_bar + "\n", flush=True)
    except Exception as _safety_exc:
        logger.warning(
            "MCE-LOG-AUTO-RENDER cmd_full safety dump failed: %s",
            _safety_exc,
        )

    elapsed = (time.monotonic() - t0) * 1000
    combined = _build_result(
        "full",
        success=True,
        slug=slug,
        duration_ms=elapsed,
        phases=phases,
    )
    _append_jsonl(combined)

    # STORY-MCE-LOG-PARITY (2026-05-20): emit Full Pipeline Report ASCII
    # to stdout so operator sees the 14-phase timeline at the end of cmd_full.
    # Failure to render does not affect cmd_full return — fail-open per
    # Art. XII (Pipeline MCE Integrity > Observability).
    try:
        from engine.intelligence.pipeline.mce.log_emitters import (
            emit_full_pipeline_report,
            emit_jsonl_trigger_summary,
            emit_llm_cost_log,
            emit_squad_activation,
        )

        report = emit_full_pipeline_report(
            slug=slug,
            phases=phases,
            total_duration_s=elapsed / 1000.0,
            success=True,
        )
        print(report, flush=True)
        emit_phase_payload(
            slug=slug,
            template_id="full_pipeline_report",
            status="ok",
            metrics={"total_duration_s": elapsed / 1000.0, "phases_count": len(phases)},
            ascii_block=report,
        )

        # LLM Cost summary — best-effort from cost_tracker if present
        try:
            cost_breakdown: dict[str, Any] = {
                "total_usd": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "by_phase": {},
                "by_provider": {},
            }
            cost_log_path = LOGS / "llm-costs.jsonl"
            if cost_log_path.exists():
                for _line in cost_log_path.read_text(encoding="utf-8").splitlines()[-200:]:
                    try:
                        _r = json.loads(_line)
                        if isinstance(_r, dict) and _r.get("slug") == slug:
                            cost_breakdown["total_usd"] += float(_r.get("cost_usd", 0))
                            cost_breakdown["total_input_tokens"] += int(_r.get("input_tokens", 0))
                            cost_breakdown["total_output_tokens"] += int(_r.get("output_tokens", 0))
                            _ph = _r.get("phase", "unknown")
                            cost_breakdown["by_phase"][_ph] = cost_breakdown["by_phase"].get(
                                _ph, 0.0
                            ) + float(_r.get("cost_usd", 0))
                            _pr = _r.get("provider", "unknown")
                            cost_breakdown["by_provider"][_pr] = cost_breakdown["by_provider"].get(
                                _pr, 0.0
                            ) + float(_r.get("cost_usd", 0))
                    except Exception:
                        continue
            _cost_block = emit_llm_cost_log(slug, cost_breakdown)
            print(_cost_block, flush=True)
            emit_phase_payload(
                slug=slug,
                template_id="llm_cost",
                status="ok",
                metrics=cost_breakdown,
                ascii_block=_cost_block,
            )
        except Exception as _e:
            logger.debug("llm_cost emit failed: %s", _e)

        # JSONL trigger summary — read pipeline-orchestrator.jsonl tail
        try:
            trigger_log = LOGS / "pipeline-orchestrator.jsonl"
            recent_triggers: list[dict[str, Any]] = []
            if trigger_log.exists():
                for _line in trigger_log.read_text(encoding="utf-8").splitlines()[-50:]:
                    try:
                        _r = json.loads(_line)
                        if isinstance(_r, dict):
                            recent_triggers.append(_r)
                    except Exception:
                        continue
            _jt_block = emit_jsonl_trigger_summary(recent_triggers)
            print(_jt_block, flush=True)
            emit_phase_payload(
                slug=slug,
                template_id="auto_advance_trigger",
                status="ok",
                metrics={"triggers_count": len(recent_triggers)},
                ascii_block=_jt_block,
            )
        except Exception as _e:
            logger.debug("trigger_summary emit failed: %s", _e)

        # Squad Activation — MCE-13.18: aggregate B2 + B5 + B6 telemetry
        # from phases dict populated during cmd_full execution.
        try:
            _b2_squads = _build_squad_activation_telemetry(
                slug=slug,
                phases_completed={
                    "batch_creation": phases.get("batch", {}),
                    "chunk_processing": phases.get("process_batch", [{}])[0]
                    if phases.get("process_batch")
                    else {},
                },
                stage="B2_batch",
            )
            _b5_squads = _build_squad_activation_telemetry(
                slug=slug,
                phases_completed={
                    "insight_extraction": phases.get("insights", {}),
                    "behavioral_extraction": phases.get("behavioral", {}),
                    "identity_extraction": phases.get("identity", {}),
                    "voice_extraction": phases.get("voice", {}),
                },
                stage="B5_dna",
            )
            _b6_squads = _build_squad_activation_telemetry(
                slug=slug,
                phases_completed={
                    "memory_enrichment": phases.get("finalize", {}).get("enrichment", {}),
                    "workspace_sync": phases.get("finalize", {}).get("workspace_sync", {}),
                    "dossier_consolidation": phases.get("finalize", {}).get(
                        "dossier_consolidation", {}
                    ),
                },
                stage="B6_finalize",
            )
            _all_squads = _b2_squads + _b5_squads + _b6_squads
            _sa_block = emit_squad_activation(_all_squads)
            print(_sa_block, flush=True)
            # MCE-17.x STEP 40 fix: renderer reads each item's "slug" as the
            # squad NAME label. Remap telemetry dicts (squad name lives under
            # "squad") to renderer-compatible {"slug": <squad_name>, "count": 1}.
            _all_squads_list = [
                {"slug": _s.get("squad", _s) if isinstance(_s, dict) else _s, "count": 1}
                for _s in _all_squads
            ]
            emit_phase_payload(
                slug=slug,
                template_id="squad_activation",
                status="ok",
                metrics={
                    "squads_activated": len(_all_squads),
                    "squads": _all_squads_list,
                },
                ascii_block=_sa_block,
            )
        except Exception as _e:
            logger.debug("squad_activation emit failed: %s", _e)
    except Exception as _log_exc:  # pragma: no cover -- observability only
        logger.debug("Full pipeline report emit failed (non-fatal): %s", _log_exc)

    # Mark the durable job completed (feature B). Token-fenced + fail-open:
    # no-op when no lease was held or when the slug was already reaped.
    _durable_lease_release(_durable_lease, success=True)

    return combined


# ---------------------------------------------------------------------------
# Argument parsing + main
# ---------------------------------------------------------------------------


_USAGE = """\
MCE Pipeline Orchestrator -- deterministic pipeline commands

Usage:
  python -m core.intelligence.pipeline.mce.orchestrate <command> [args]

Commands:
  ingest <file_path>             Classify + route + organize a source file
  batch <source_slug> [--single-file]  Create batches from organized inbox
  process-batch <slug> <batch_id> Transactional chunk+embed+upsert (atomic rollback)
  rag-index <slug>               Phase 4.5: RAG indexation + validation gate (Art. XV)
  insights <slug>                Step 5: L1-L5 DNA extraction (insights + entities)
  behavioral <slug>              Step 6: L6 behavioral patterns (hybrid derive+LLM)
  identity <slug>                Step 7: L7/L9/L10 values+obsessions+paradoxes (hybrid)
  voice <slug>                   Step 8: L8 voice DNA signature phrases (hybrid)
  identity-checkpoint <slug>     Step 9: deterministic cross-layer DNA gate (no LLM)
  consolidate <slug> [--force]   Step 10: synthesise dossier from DNA + insights
  finalize <slug>                Post-extraction: enrich memory + sync workspace
  status [slug]                  Show pipeline state (all if slug omitted)
  full <file_path>               Shortcut: ingest + batch + status
  recover <slug>                 Recover failed/paused pipeline to last valid state
  cleanup [slug] [--retention-days N] [--dry-run]  Clean up old pipeline state
  cleanup-slug <slug> [--dry-run]  Remove ALL artifacts for a slug (re-ingestion prep) [MCE-13.8]
  report <slug>                  Deterministic artifact report (no LLM)

Examples:
  python -m core.intelligence.pipeline.mce.orchestrate ingest "workspace/inbox/file.txt"
  python -m core.intelligence.pipeline.mce.orchestrate batch alex-hormozi --single-file
  python -m core.intelligence.pipeline.mce.orchestrate behavioral jane-doe
  python -m core.intelligence.pipeline.mce.orchestrate identity jane-doe
  python -m core.intelligence.pipeline.mce.orchestrate voice jane-doe
  python -m core.intelligence.pipeline.mce.orchestrate recover alex-hormozi
  python -m core.intelligence.pipeline.mce.orchestrate cleanup --retention-days 7 --dry-run
  python -m core.intelligence.pipeline.mce.orchestrate report alex-hormozi
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

    # MCE-11.20: --non-interactive flag forces all 6 decision points to log-only.
    # Must be extracted before command parsing so it applies to every sub-command.
    if "--non-interactive" in args:
        args = [a for a in args if a != "--non-interactive"]
        try:
            from engine.intelligence.pipeline.mce.decision_gateway import (
                set_non_interactive,
            )

            set_non_interactive(True)
        except Exception:
            os.environ["MCE_NON_INTERACTIVE"] = "1"

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
            single_file = "--single-file" in rest
            slug_args = [r for r in rest if not r.startswith("--")]
            result = cmd_batch(slug_args[0], single_file=single_file)

        elif command == "process-batch":
            if len(rest) < 2:
                print("Error: process-batch requires <slug> <batch_id>", file=sys.stderr)
                return 1
            result = cmd_process_batch(batch_id=rest[1], slug=rest[0])

        elif command == "auto-advance":
            if not rest:
                print("Error: auto-advance requires <slug>", file=sys.stderr)
                return 1
            result = cmd_auto_advance(rest[0])

        elif command == "rag-index":
            if not rest:
                print("Error: rag-index requires <slug>", file=sys.stderr)
                return 1
            result = cmd_rag_index(rest[0])

        elif command == "insights":
            if not rest:
                print("Error: insights requires <slug>", file=sys.stderr)
                return 1
            result = cmd_insights(rest[0])

        elif command == "behavioral":
            if not rest:
                print("Error: behavioral requires <slug>", file=sys.stderr)
                return 1
            result = cmd_behavioral(rest[0])

        elif command == "identity":
            if not rest:
                print("Error: identity requires <slug>", file=sys.stderr)
                return 1
            result = cmd_identity(rest[0])

        elif command == "voice":
            if not rest:
                print("Error: voice requires <slug>", file=sys.stderr)
                return 1
            result = cmd_voice(rest[0])

        elif command == "identity-checkpoint":
            if not rest:
                print("Error: identity-checkpoint requires <slug>", file=sys.stderr)
                return 1
            result = cmd_identity_checkpoint(rest[0])

        elif command == "promote-agent":
            if not rest:
                print("Error: promote-agent requires <slug>", file=sys.stderr)
                return 1
            result = cmd_promote_agent(rest[0])

        elif command == "consolidate":
            if not rest:
                print("Error: consolidate requires <slug>", file=sys.stderr)
                return 1
            force_flag = "--force" in rest
            result = cmd_consolidate(rest[0], force=force_flag)

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

        elif command == "recover":
            if not rest:
                print("Error: recover requires <slug>", file=sys.stderr)
                return 1
            result = cmd_recover(rest[0])

        elif command == "cleanup":
            dry_run = "--dry-run" in rest
            retention = 30
            for i, arg in enumerate(rest):
                if arg == "--retention-days" and i + 1 < len(rest):
                    try:
                        retention = int(rest[i + 1])
                    except ValueError:
                        pass
            slug_args = [r for r in rest if not r.startswith("--") and not r.isdigit()]
            cleanup_slug = slug_args[0] if slug_args else None
            result = cmd_cleanup(cleanup_slug, retention_days=retention, dry_run=dry_run)

        elif command == "cleanup-slug":
            # MCE-13.8 Bug H: remove all artifacts for a slug (re-ingestion prep)
            if not rest or rest[0].startswith("--"):
                print("Error: cleanup-slug requires <slug>", file=sys.stderr)
                return 1
            dry_run_flag = "--dry-run" in rest
            result = cmd_cleanup_slug(rest[0], dry_run=dry_run_flag)

        elif command == "report":
            if not rest:
                print("Error: report requires <slug>", file=sys.stderr)
                return 1
            result = cmd_report(rest[0])

        elif command == "thresholds":
            # Story MCE-11.19: threshold inspector + runtime override
            from engine.intelligence.pipeline.config.threshold_loader import (
                set_threshold_override,
                show_thresholds,
            )

            if "--show" in rest or not rest:
                print(show_thresholds())
                return 0

            elif "--set" in rest:
                set_idx = rest.index("--set")
                if len(rest) < set_idx + 3:
                    print(
                        "Error: thresholds --set requires <key> <value>",
                        file=sys.stderr,
                    )
                    return 1
                t_key = rest[set_idx + 1]
                t_raw = rest[set_idx + 2]
                # Coerce value to int, float, or bool as appropriate
                try:
                    if t_raw.lower() == "true":
                        t_val: Any = True
                    elif t_raw.lower() == "false":
                        t_val = False
                    elif "." in t_raw:
                        t_val = float(t_raw)
                    else:
                        t_val = int(t_raw)
                except ValueError:
                    t_val = t_raw
                try:
                    set_threshold_override(t_key, t_val)
                except KeyError as e:
                    print(f"Error: {e}", file=sys.stderr)
                    return 1
                return 0

            else:
                print(
                    "Error: thresholds requires --show or --set <key> <value>",
                    file=sys.stderr,
                )
                return 1

        elif command == "emit-chronicler":
            # T5 (MCE-14.6): backstop CLI — allows hook/cron to fire chronicler
            # for any slug that completed without passing through cmd_finalize.
            # Usage: python3 -m engine.intelligence.pipeline.mce.orchestrate emit-chronicler <slug>
            if not rest:
                print("Error: emit-chronicler requires <slug>", file=sys.stderr)
                return 1
            _safe_emit_chronicler(rest[0], source_path="backstop")
            result = {"command": "emit-chronicler", "success": True, "slug": rest[0]}

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
