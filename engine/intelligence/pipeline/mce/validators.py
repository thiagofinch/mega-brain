"""
validators.py -- Deterministic Step Validators for the MCE Pipeline
====================================================================

ADR-G5 "Mapping: Agent to Step to Validator" -- one function per LLM step
plus the surrounding worker steps. Each validator reads artifacts from disk
and returns a structured dict that matches the ADR's "Validation Command"
contract exactly, so ``orchestrate.py cmd_validate`` can dispatch here and
emit the verdict to SKILL.md verbatim.

Contract (every validator returns)::

    {
      "command": "validate",
      "step_id": "<Sxx-name>",
      "slug": slug,
      "success": bool,
      "validator": "<function name>",
      "checks": { ... per-step bool+count fields ... },
      "fsm_state": "<current PipelineStateMachine state>",
      "fsm_next": "<suggested next state>" | None,
      "timestamp": "<ISO8601 UTC>",
      # on failure:
      "error": "<human-readable reason>",
      "recovery_hint": "<actionable next step>"
    }

Constraints (Constitution Art. I + ADR-G5)::

- stdlib + PyYAML only. No LLM clients. No external HTTP.
- Never raises: every check is wrapped, errors become ``success=False``.
- Fail-closed: missing artifact / unparseable artifact / threshold miss
  all produce ``success=False``.

Thresholds (documented source inline per check)::
- Sprint 0 (AD-8 PR-001/PR-002): chunk_count > 0, insights_count > 0.
- Identity gate (squads/megabrain-pipeline-squad/config.yaml lines 386-394):
  L6>=3 patterns, L7>=3 values, L8>=5 phrases, L9>=2 obsessions, L10>=1.
- RAG gate: chunks_post > 0 AND chunks_post >= chunks_pre
  (orchestrate.cmd_rag_index + config.yaml MCE-QG-RAG).
- Agent-gen: 15 agent files per Phase 5 template.

CLI (manual testing, non-authoritative)::

    python3 -m engine.intelligence.pipeline.mce.validators <step_id> <slug>

Version: 1.0.0  (Sprint 0 — ADR-G5 ACCEPTED 2026-04-15)
"""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path bootstrap (direct invocation friendly)
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Canonical artifact paths (duplicated intentionally: validators.py stays
# self-contained per ADR-G5 stdlib constraint).
# ---------------------------------------------------------------------------

_ARTIFACTS: Path = _PROJECT_ROOT / "artifacts"
_KNOWLEDGE: Path = _PROJECT_ROOT / "knowledge"
_AGENTS: Path = _PROJECT_ROOT / "agents"
_MISSION_CONTROL: Path = _PROJECT_ROOT / ".claude" / "mission-control"
_MCE_STATE: Path = _MISSION_CONTROL / "mce"

# Global canonical entity map (cross-slug by design — D6)
_CANONICAL_MAP: Path = _ARTIFACTS / "canonical" / "CANONICAL-MAP.json"

# Legacy fallbacks kept for transitional slugs that never moved to per-slug dirs.
_CHUNKS_STATE_LEGACY: Path = _ARTIFACTS / "chunks" / "CHUNKS-STATE.json"
_INSIGHTS_STATE_LEGACY: Path = _ARTIFACTS / "insights" / "INSIGHTS-STATE.json"


# ---------------------------------------------------------------------------
# Thresholds (all configurable — hard-coded here only when no YAML source).
# ---------------------------------------------------------------------------

# Source: squads/megabrain-pipeline-squad/config.yaml MCE-QG-3 + PR-001.
_MIN_CHUNKS: int = 1

# Source: squads/megabrain-pipeline-squad/config.yaml MCE-QG-5 + PR-002.
_MIN_INSIGHTS: int = 1

# Source: squads/megabrain-pipeline-squad/config.yaml lines 386-394
# (phase_d_profile.ATM-VALIDATE-IDENTITY-GATE.thresholds).
_IDENTITY_GATE_THRESHOLDS: dict[str, int] = {
    "L6_min_patterns": 3,  # behavioral patterns
    "L6_min_chunk_ids_per_pattern": 2,
    "L7_min_values": 3,  # values hierarchy tier-1 (+ others)
    "L8_min_phrases": 5,  # VOICE-DNA signature phrases
    "L9_min_obsessions": 2,
    "L10_min_paradoxes": 1,
}

# Source: Phase 5 mind-clone template (15 files).
# agents/{bucket}/{slug}/ must contain at minimum these 15 files.
# MCE-13.6: core four files use lowercase canonical names; validators must use
# find_agent_file for case-insensitive existence checks.
_REQUIRED_AGENT_FILES: tuple[str, ...] = (
    "agent.md",
    "soul.md",
    "memory.md",
    "dna-config.yaml",
    "INSIGHTS.md",
    "CONFIG.yaml",
    "FILOSOFIAS.yaml",
    "MODELOS-MENTAIS.yaml",
    "HEURISTICAS.yaml",
    "FRAMEWORKS.yaml",
    "METODOLOGIAS.yaml",
    "VOICE-DNA.yaml",
    "VALUES-HIERARCHY.yaml",
    "OBSESSIONS.yaml",
    "PARADOXES.yaml",
)


# ---------------------------------------------------------------------------
# Helpers (self-contained per ADR-G5 "do not cross-import qa_gates privates")
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Current UTC timestamp as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _safe_json(path: Path) -> Any | None:
    """Load JSON or return None on any error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _safe_yaml(path: Path) -> Any | None:
    """Load YAML or return None on any error."""
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except Exception:
        return None


def _chunks_state(slug: str) -> Path:
    """Per-slug CHUNKS-STATE.json (MCE-1.2 isolation), with legacy fallback."""
    p = _ARTIFACTS / "chunks" / slug / "CHUNKS-STATE.json"
    if p.exists():
        return p
    return _CHUNKS_STATE_LEGACY if _CHUNKS_STATE_LEGACY.exists() else p


def _insights_state(slug: str) -> Path:
    """Per-slug INSIGHTS-STATE.json, with legacy fallback."""
    p = _ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
    if p.exists():
        return p
    return _INSIGHTS_STATE_LEGACY if _INSIGHTS_STATE_LEGACY.exists() else p


def _slug_state_dir(slug: str) -> Path:
    """MCE mission-control state dir for a slug."""
    return _MCE_STATE / slug


def _detect_bucket(slug: str) -> str:
    """Detect which knowledge bucket a slug lives in.

    Filesystem heuristic: first agent dir that exists wins.
    Defaults to ``"external"`` if no evidence.
    """
    for b in ("personal", "business", "external"):
        if (_AGENTS / b / slug).is_dir():
            return b
    return "external"


def _dna_dir(slug: str, bucket: str | None = None) -> Path:
    """DNA dir for a slug under the correct bucket."""
    b = bucket or _detect_bucket(slug)
    if b == "personal":
        return _KNOWLEDGE / "personal" / "dna"
    if b == "business":
        return _KNOWLEDGE / "business" / "people" / slug
    return _KNOWLEDGE / "external" / "dna" / "persons" / slug


def _agent_dir(slug: str, bucket: str | None = None) -> Path:
    """Agent dir for a slug under the correct bucket."""
    b = bucket or _detect_bucket(slug)
    return _AGENTS / b / slug


def _dossier_path(slug: str, bucket: str | None = None) -> Path:
    """Expected dossier path for a slug."""
    b = bucket or _detect_bucket(slug)
    bucket_root = _KNOWLEDGE / {
        "external": "external",
        "business": "business",
        "personal": "personal",
    }.get(b, "external")
    formatted = slug.upper().replace("-", " ").replace("_", " ")
    name = "-".join(formatted.split())
    return bucket_root / "dossiers" / "persons" / f"DOSSIER-{name}.md"


def _fsm_info(slug: str) -> tuple[str, str | None]:
    """Return (current_state, suggested_next_state) for a slug.

    The mapping below mirrors state_machine.TRANSITIONS -- we do NOT import
    the machine here because constructing it has side effects (it loads
    persisted YAML). Reading the raw state file is enough for a snapshot.
    """
    state_yaml = _slug_state_dir(slug) / "pipeline_state.yaml"
    current = "init"
    data = _safe_yaml(state_yaml)
    if isinstance(data, dict):
        current = str(data.get("state", data.get("current_state", "init")) or "init")

    # Minimal forward chain (matches state_machine.TRANSITIONS happy path).
    chain = [
        "init",
        "ingesting",
        "batching",
        "chunking",
        "entity_resolution",
        "insight_extraction",
        "mce_behavioral",
        "mce_identity",
        "mce_voice",
        "identity_checkpoint",
        "consolidation",
        "rag_indexation",
        "agent_generation",
        "finalizing",
        "reporting",
        "complete",
    ]
    nxt: str | None = None
    if current in chain:
        idx = chain.index(current)
        if idx + 1 < len(chain):
            nxt = chain[idx + 1]
    return current, nxt


def _build(
    step_id: str,
    slug: str,
    validator: str,
    *,
    success: bool,
    checks: dict[str, Any],
    error: str | None = None,
    recovery_hint: str | None = None,
) -> dict[str, Any]:
    """Assemble the ADR-G5 "Validation Command" response dict."""
    fsm_state, fsm_next = _fsm_info(slug)
    out: dict[str, Any] = {
        "command": "validate",
        "step_id": step_id,
        "slug": slug,
        "success": bool(success),
        "validator": validator,
        "checks": checks,
        "fsm_state": fsm_state,
        "fsm_next": fsm_next if success else None,
        "timestamp": _now_iso(),
    }
    if not success:
        out["error"] = error or "validation failed"
        out["recovery_hint"] = recovery_hint or "inspect checks{} for the first failed condition"
    return out


# ---------------------------------------------------------------------------
# Individual validators
# ---------------------------------------------------------------------------


def validate_ingestion_guard(slug: str) -> dict[str, Any]:
    """S00 — Phase 0 dedup verdict emission (pipeline-ops: gate).

    Success when the ingestion_guard registered this slug with a valid
    identity_key. We inspect the JSON registry because the actual verdict
    was returned by orchestrate.cmd_ingest and already honoured the
    HALT_OK/HALT_FAIL contract (PR-003).
    """
    step_id = "S00-guard"
    validator = "validate_ingestion_guard"
    registry_path = _PROJECT_ROOT / ".data" / "ingestion-registry.json"
    checks: dict[str, Any] = {
        "registry_exists": registry_path.exists(),
        "slug_registered": False,
    }
    if not registry_path.exists():
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="ingestion-registry.json is missing",
            recovery_hint="run orchestrate.py ingest <file> to populate the registry",
        )

    data = _safe_json(registry_path) or {}
    entries = data.get("entries", {}) if isinstance(data, dict) else {}
    slug_registered = any(isinstance(e, dict) and e.get("slug") == slug for e in entries.values())
    checks["slug_registered"] = slug_registered
    checks["total_entries"] = len(entries) if isinstance(entries, dict) else 0

    if not slug_registered:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"slug '{slug}' has no entry in the ingestion registry",
            recovery_hint=f"run orchestrate.py ingest <file-for-{slug}> first",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


def validate_chunks(slug: str) -> dict[str, Any]:
    """S02 — chunking (pipeline-ops: parse). PR-001 zero-check.

    Contract: CHUNKS-STATE.json exists, is valid JSON, chunks[] list is
    present with >= _MIN_CHUNKS entries, every entry has chunk_id.
    """
    step_id = "S02-chunk"
    validator = "validate_chunks"
    path = _chunks_state(slug)
    checks: dict[str, Any] = {
        "artifact_path": str(path),
        "artifact_exists": path.exists(),
        "schema_valid": False,
        "chunks_count": 0,
        "min_chunks_met": False,
        "chunk_ids_unique": False,
    }

    if not path.exists():
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"CHUNKS-STATE.json not found at {path}",
            recovery_hint="re-run S02-chunk; SKILL.md should write the artifact before validating",
        )

    data = _safe_json(path)
    if not isinstance(data, dict):
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="CHUNKS-STATE.json is not a JSON object",
            recovery_hint="the chunker emitted malformed output; re-run with the correct template",
        )
    chunks = data.get("chunks", [])
    if not isinstance(chunks, list):
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="CHUNKS-STATE.json.chunks is not a list",
            recovery_hint="re-run chunking with prompt-1.1-chunking.md",
        )
    checks["schema_valid"] = True
    count = len(chunks)
    checks["chunks_count"] = count
    # PR-001: zero-check. chunks_count MUST be > 0.
    checks["min_chunks_met"] = count >= _MIN_CHUNKS
    ids = [c.get("chunk_id", c.get("id")) for c in chunks if isinstance(c, dict)]
    checks["chunk_ids_unique"] = len(set(ids)) == len(ids) and all(i for i in ids)

    if not checks["min_chunks_met"]:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"chunks_count is {count} -- PR-001 requires >= {_MIN_CHUNKS}",
            recovery_hint="source content too thin or chunker failed; re-run S02-chunk with different parameters",
        )
    if not checks["chunk_ids_unique"]:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="chunk_ids are missing or not unique",
            recovery_hint="regenerate chunks; ensure each chunk has a unique chunk_id",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


def validate_entities(slug: str) -> dict[str, Any]:
    """S04 — entity resolution (pipeline-ops: canon).

    Contract: CANONICAL-MAP.json exists, has entities, the source slug has
    a canonical entry.
    """
    step_id = "S04-entity"
    validator = "validate_entities"
    checks: dict[str, Any] = {
        "artifact_path": str(_CANONICAL_MAP),
        "artifact_exists": _CANONICAL_MAP.exists(),
        "schema_valid": False,
        "entities_count": 0,
        "source_person_entry": False,
    }
    if not _CANONICAL_MAP.exists():
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"CANONICAL-MAP.json not found at {_CANONICAL_MAP}",
            recovery_hint="re-run S04-entity with prompt-1.2-entity-resolution.md",
        )
    data = _safe_json(_CANONICAL_MAP)
    if not isinstance(data, dict):
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="CANONICAL-MAP.json is not a JSON object",
            recovery_hint="re-run S04-entity; the entity resolver emitted malformed output",
        )
    checks["schema_valid"] = True
    entities = data.get("entities", data.get("persons", {}))
    if isinstance(entities, dict):
        count = len(entities)
        slug_norm = slug.lower().replace("-", " ").replace("_", " ")
        has_entry = any(
            slug_norm in k.lower().replace("-", " ").replace("_", " ") for k in entities
        )
    elif isinstance(entities, list):
        count = len(entities)
        slug_norm = slug.lower().replace("-", " ").replace("_", " ")
        has_entry = any(
            isinstance(e, dict)
            and slug_norm
            in str(e.get("canonical_name", e.get("name", "")))
            .lower()
            .replace("-", " ")
            .replace("_", " ")
            for e in entities
        )
    else:
        count = 0
        has_entry = False
    checks["entities_count"] = count
    checks["source_person_entry"] = has_entry

    if count == 0:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="entities_count is 0",
            recovery_hint="re-run S04-entity; entity resolver produced no entities",
        )
    if not has_entry:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"no canonical entry found for slug '{slug}'",
            recovery_hint=f"verify the entity resolver mapped the source to '{slug}' or an alias",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


def validate_insights(slug: str) -> dict[str, Any]:
    """S05 — insight extraction (pipeline-ops: dig). PR-002 zero-check.

    Contract: INSIGHTS-STATE.json exists, has insights for this slug,
    insights_count >= _MIN_INSIGHTS, every insight carries chunk refs.
    """
    step_id = "S05-insight"
    validator = "validate_insights"
    path = _insights_state(slug)
    checks: dict[str, Any] = {
        "artifact_path": str(path),
        "artifact_exists": path.exists(),
        "schema_valid": False,
        "insights_count": 0,
        "min_insights_met": False,
        "all_have_chunk_refs": False,
    }
    if not path.exists():
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"INSIGHTS-STATE.json not found at {path}",
            recovery_hint="re-run S05-insight with prompt-2.1-insight-extraction.md",
        )
    data = _safe_json(path)
    if not isinstance(data, dict):
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="INSIGHTS-STATE.json is not a JSON object",
            recovery_hint="re-run S05-insight; extractor emitted malformed output",
        )
    checks["schema_valid"] = True

    # Locate this slug's insights (nested under persons[slug] or flat).
    person_insights: list[Any] = []
    persons = data.get("persons", {})
    if isinstance(persons, dict):
        slug_norm = slug.lower()
        for key, pdata in persons.items():
            if slug_norm in str(key).lower().replace("-", " ").replace("_", " ") and isinstance(
                pdata, dict
            ):
                person_insights = pdata.get("insights", [])
                break
    if not person_insights:
        flat = data.get("insights", [])
        if isinstance(flat, list):
            person_insights = flat

    count = len(person_insights)
    checks["insights_count"] = count
    # PR-002: zero-check. insights_count MUST be > 0.
    checks["min_insights_met"] = count >= _MIN_INSIGHTS

    if count == 0:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"insights_count is 0 -- PR-002 requires >= {_MIN_INSIGHTS}",
            recovery_hint="re-run S05-insight; check source material has substantive content",
        )

    missing = 0
    for ins in person_insights:
        if isinstance(ins, dict):
            refs = ins.get("chunks") or ins.get("chunk_ids") or []
            if not refs:
                missing += 1
    checks["all_have_chunk_refs"] = missing == 0
    if missing:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"{missing}/{count} insights missing chunk references",
            recovery_hint="re-run S05-insight; every insight must cite its source chunk_ids",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


def validate_dna_tags(slug: str) -> dict[str, Any]:
    """S06 — DNA tagging (pipeline-ops: weave/dig).

    Contract: insights in INSIGHTS-STATE carry DNA layer tags (L1..L10).
    """
    step_id = "S06-dna-tag"
    validator = "validate_dna_tags"
    path = _insights_state(slug)
    checks: dict[str, Any] = {
        "artifact_path": str(path),
        "artifact_exists": path.exists(),
        "insights_inspected": 0,
        "insights_with_tags": 0,
        "tag_coverage_pct": 0.0,
    }
    if not path.exists():
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"INSIGHTS-STATE.json not found at {path}",
            recovery_hint="run S05-insight first, then S06-dna-tag",
        )
    data = _safe_json(path) or {}
    persons = data.get("persons", {}) if isinstance(data, dict) else {}
    insights: list[Any] = []
    if isinstance(persons, dict):
        for key, pdata in persons.items():
            if slug.lower() in str(key).lower() and isinstance(pdata, dict):
                insights = pdata.get("insights", [])
                break
    if not insights and isinstance(data, dict):
        insights = data.get("insights", []) or []
    inspected = len(insights)
    with_tags = sum(
        1
        for i in insights
        if isinstance(i, dict) and (i.get("dna_layers") or i.get("tags") or i.get("layer"))
    )
    checks["insights_inspected"] = inspected
    checks["insights_with_tags"] = with_tags
    checks["tag_coverage_pct"] = round((with_tags / inspected * 100), 2) if inspected else 0.0

    if inspected == 0:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="no insights to tag",
            recovery_hint="re-run S05-insight first",
        )
    # Threshold: 80% tag coverage (same as traceability check in config.yaml).
    if checks["tag_coverage_pct"] < 80.0:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"tag coverage {checks['tag_coverage_pct']}% < 80%",
            recovery_hint="re-run S06-dna-tag with prompt-2.1-dna-tags.md",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


def validate_behavioral(slug: str) -> dict[str, Any]:
    """S07 — behavioral extraction (pipeline-ops: behav).

    Contract: behavioral_patterns.json exists OR
    INSIGHTS-STATE.persons[slug].behavioral_patterns present. Each pattern
    must cite >= _IDENTITY_GATE_THRESHOLDS['L6_min_chunk_ids_per_pattern']
    chunk_ids.
    """
    step_id = "S07-behavioral"
    validator = "validate_behavioral"
    state_dir = _slug_state_dir(slug)
    candidate_paths = [
        state_dir / "behavioral_patterns.json",
        state_dir / "mce_behavioral.json",
    ]
    patterns: list[Any] = []
    source_path: Path | None = None
    for p in candidate_paths:
        if p.exists():
            raw = _safe_json(p)
            if isinstance(raw, dict):
                patterns = raw.get("behavioral_patterns") or raw.get("patterns") or []
            elif isinstance(raw, list):
                patterns = raw
            if patterns:
                source_path = p
                break
    if not patterns:
        # Fallback: look inside INSIGHTS-STATE.persons[slug].behavioral_patterns
        is_path = _insights_state(slug)
        data = _safe_json(is_path)
        if isinstance(data, dict):
            persons = data.get("persons", {})
            if isinstance(persons, dict):
                for key, pdata in persons.items():
                    if slug.lower() in str(key).lower() and isinstance(pdata, dict):
                        bp = pdata.get("behavioral_patterns") or []
                        if isinstance(bp, list):
                            patterns = bp
                            source_path = is_path
                        break

    checks: dict[str, Any] = {
        "source_path": str(source_path) if source_path else None,
        "patterns_count": len(patterns),
        "min_patterns_met": len(patterns) >= _IDENTITY_GATE_THRESHOLDS["L6_min_patterns"],
        "weak_patterns": 0,
    }
    weak = sum(
        1
        for p in patterns
        if isinstance(p, dict)
        and len(p.get("chunk_ids") or p.get("chunks") or p.get("evidence") or [])
        < _IDENTITY_GATE_THRESHOLDS["L6_min_chunk_ids_per_pattern"]
    )
    checks["weak_patterns"] = weak

    if not checks["min_patterns_met"]:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"behavioral patterns={len(patterns)} < {_IDENTITY_GATE_THRESHOLDS['L6_min_patterns']}",
            recovery_hint="re-run S07-behavioral with prompt-mce-behavioral.md",
        )
    if weak > 0:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"{weak} patterns have < {_IDENTITY_GATE_THRESHOLDS['L6_min_chunk_ids_per_pattern']} chunk_ids",
            recovery_hint="re-run S07-behavioral; each pattern must cite >= 2 chunk_ids",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


def validate_identity(slug: str) -> dict[str, Any]:
    """S08 — identity extraction (pipeline-ops: psych).

    Contract: identity_layer.json has value_hierarchy with Tier 1 entries
    and exactly 1 MASTER obsession.
    """
    step_id = "S08-identity"
    validator = "validate_identity"
    state_dir = _slug_state_dir(slug)
    data: Any = None
    source: Path | None = None
    for p in (state_dir / "identity_layer.json", state_dir / "mce_identity.json"):
        if p.exists():
            data = _safe_json(p)
            if data is not None:
                source = p
                break

    checks: dict[str, Any] = {
        "source_path": str(source) if source else None,
        "tier1_values": 0,
        "master_obsessions": 0,
        "tier1_ok": False,
        "master_ok": False,
    }
    if not isinstance(data, dict):
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="identity_layer.json not found or not parseable",
            recovery_hint="re-run S08-identity with prompt-mce-identity.md",
        )
    hierarchy = data.get("value_hierarchy", data.get("values", []))
    tier1 = 0
    if isinstance(hierarchy, list):
        for v in hierarchy:
            if isinstance(v, dict) and str(v.get("tier", v.get("level", ""))).lower() in {
                "1",
                "tier 1",
                "tier_1",
            }:
                tier1 += 1
    elif isinstance(hierarchy, dict):
        t1 = hierarchy.get("tier_1", hierarchy.get("Tier 1", []))
        tier1 = len(t1) if isinstance(t1, list) else (1 if t1 else 0)
    checks["tier1_values"] = tier1
    checks["tier1_ok"] = tier1 >= 1

    obsessions = data.get("obsessions", data.get("core_obsessions", []))
    master = 0
    if isinstance(obsessions, list):
        for o in obsessions:
            if isinstance(o, dict):
                if str(o.get("classification", o.get("tier", ""))).upper() == "MASTER":
                    master += 1
            elif isinstance(o, str) and "MASTER" in o.upper():
                master += 1
    checks["master_obsessions"] = master
    checks["master_ok"] = master == 1

    if not checks["tier1_ok"]:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="value_hierarchy has no Tier 1 values",
            recovery_hint="re-run S08-identity; prompt must produce at least 1 Tier 1 value",
        )
    if not checks["master_ok"]:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"expected exactly 1 MASTER obsession, found {master}",
            recovery_hint="re-run S08-identity; ensure exactly one obsession is classified MASTER",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


def validate_voice(slug: str) -> dict[str, Any]:
    """S09 — voice extraction (pipeline-ops: voice).

    Contract: VOICE-DNA.yaml present with >= _MIN_PHRASES signature_phrases,
    >= 3 behavioral_states, >= 6 tone dimensions.
    """
    step_id = "S09-voice"
    validator = "validate_voice"
    bucket = _detect_bucket(slug)
    voice_path = _dna_dir(slug, bucket) / "VOICE-DNA.yaml"
    checks: dict[str, Any] = {
        "artifact_path": str(voice_path),
        "artifact_exists": voice_path.exists(),
        "signature_phrases": 0,
        "behavioral_states": 0,
        "voice_dimensions": 0,
    }
    if not voice_path.exists():
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"VOICE-DNA.yaml not found at {voice_path}",
            recovery_hint="re-run S09-voice with prompt-mce-voice.md",
        )
    data = _safe_yaml(voice_path)
    if not isinstance(data, dict):
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="VOICE-DNA.yaml not parseable",
            recovery_hint="re-run S09-voice; YAML was malformed",
        )
    phrases = data.get("signature_phrases", data.get("catchphrases", []))
    phrases = phrases if isinstance(phrases, list) else []
    states = data.get("behavioral_states", data.get("states", []))
    if isinstance(states, dict):
        states = list(states.keys())
    states = states if isinstance(states, list) else []
    dims = data.get("tone_dimensions", data.get("dimensions", data.get("voice_dimensions", {})))
    dim_count = len(dims) if isinstance(dims, dict | list) else 0

    checks["signature_phrases"] = len(phrases)
    checks["behavioral_states"] = len(states)
    checks["voice_dimensions"] = dim_count

    # Threshold source: squads/megabrain-pipeline-squad/config.yaml L8_min_phrases=5.
    min_phrases = _IDENTITY_GATE_THRESHOLDS["L8_min_phrases"]
    if len(phrases) < min_phrases:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"signature_phrases={len(phrases)} < {min_phrases}",
            recovery_hint="re-run S09-voice; VOICE-DNA requires >= 5 signature phrases",
        )
    if len(states) < 3:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"behavioral_states={len(states)} < 3",
            recovery_hint="re-run S09-voice; VOICE-DNA requires >= 3 behavioral states",
        )
    if dim_count < 6:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"voice_dimensions={dim_count} < 6",
            recovery_hint="re-run S09-voice; VOICE-DNA requires 6 tone dimensions",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


def validate_identity_gate(slug: str) -> dict[str, Any]:
    """S10 — identity gate (pipeline-ops: guard, AD-7 auto-validator).

    Aggregates thresholds across L6-L10 per squads/megabrain-pipeline-squad/
    config.yaml lines 386-394. Replaces the old human approval step; this
    function is the auto-quality-gate that AD-7 mandates.
    """
    step_id = "S10-checkpoint"
    validator = "validate_identity_gate"
    bucket = _detect_bucket(slug)
    dna = _dna_dir(slug, bucket)

    # Collect counts from whatever layer files exist.
    behavioral = (
        _safe_yaml(dna / "BEHAVIORAL-PATTERNS.yaml")
        if (dna / "BEHAVIORAL-PATTERNS.yaml").exists()
        else None
    )
    values = (
        _safe_yaml(dna / "VALUES-HIERARCHY.yaml")
        if (dna / "VALUES-HIERARCHY.yaml").exists()
        else None
    )
    voice = _safe_yaml(dna / "VOICE-DNA.yaml") if (dna / "VOICE-DNA.yaml").exists() else None
    obsessions = _safe_yaml(dna / "OBSESSIONS.yaml") if (dna / "OBSESSIONS.yaml").exists() else None
    paradoxes = _safe_yaml(dna / "PARADOXES.yaml") if (dna / "PARADOXES.yaml").exists() else None

    def _count_list_like(obj: Any, *keys: str) -> int:
        if isinstance(obj, list):
            return len(obj)
        if isinstance(obj, dict):
            for k in keys:
                if k in obj and isinstance(obj[k], list):
                    return len(obj[k])
            # If keys all miss, count top-level leaves.
            return len(obj)
        return 0

    l6 = _count_list_like(behavioral, "behavioral_patterns", "patterns")
    l7 = _count_list_like(values, "values", "hierarchy", "tier_1")
    l8 = (
        _count_list_like(
            voice.get("signature_phrases") if isinstance(voice, dict) else None,
        )
        if voice
        else 0
    )
    l9 = _count_list_like(obsessions, "obsessions", "core_obsessions")
    l10 = _count_list_like(paradoxes, "paradoxes")

    t = _IDENTITY_GATE_THRESHOLDS
    checks: dict[str, Any] = {
        "L6_patterns": l6,
        "L6_ok": l6 >= t["L6_min_patterns"],
        "L7_values": l7,
        "L7_ok": l7 >= t["L7_min_values"],
        "L8_phrases": l8,
        "L8_ok": l8 >= t["L8_min_phrases"],
        "L9_obsessions": l9,
        "L9_ok": l9 >= t["L9_min_obsessions"],
        "L10_paradoxes": l10,
        "L10_ok": l10 >= t["L10_min_paradoxes"],
    }
    failures = [k for k, v in checks.items() if k.endswith("_ok") and v is False]
    if failures:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"identity gate thresholds failed: {failures}",
            recovery_hint="re-run the failing DNA layer extractions (S07/S08/S09) with stricter prompts",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


def validate_consolidation(slug: str) -> dict[str, Any]:
    """S11 — dossier + DNA consolidation (pipeline-ops: scribe).

    Contract: dossier exists, all required DNA YAMLs present in dna dir.
    """
    step_id = "S11-consolidation"
    validator = "validate_consolidation"
    bucket = _detect_bucket(slug)
    dossier = _dossier_path(slug, bucket)
    dna = _dna_dir(slug, bucket)
    required_dna = (
        "FILOSOFIAS.yaml",
        "MODELOS-MENTAIS.yaml",
        "HEURISTICAS.yaml",
        "FRAMEWORKS.yaml",
        "METODOLOGIAS.yaml",
        "OBSESSIONS.yaml",
        "PARADOXES.yaml",
    )
    found = [f for f in required_dna if (dna / f).exists()]
    checks: dict[str, Any] = {
        "dossier_path": str(dossier),
        "dossier_exists": dossier.exists(),
        "dna_dir": str(dna),
        "dna_files_found": len(found),
        "dna_files_expected": len(required_dna),
        "missing_dna_files": [f for f in required_dna if f not in found],
    }
    if not dossier.exists():
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"dossier not found at {dossier}",
            recovery_hint="re-run S11-consolidation with dossier-compilation.md",
        )
    if len(found) != len(required_dna):
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"missing DNA YAMLs: {checks['missing_dna_files']}",
            recovery_hint="re-run S11-consolidation; all 7 DNA YAMLs must be present",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


def validate_rag_index(slug: str) -> dict[str, Any]:
    """S12 — RAG indexation (pipeline-ops: index). PR-004 gate.

    Contract: most recent RAG rebuild for this slug's bucket produced
    chunks_post > 0 AND chunks_post >= chunks_pre. We read the dedicated
    RAG indexation log (logs/rag-indexation.jsonl) for the latest entry
    involving this slug or its bucket.
    """
    step_id = "S12-rag"
    validator = "validate_rag_index"
    log_path = _PROJECT_ROOT / "logs" / "rag-indexation.jsonl"
    checks: dict[str, Any] = {
        "log_path": str(log_path),
        "log_exists": log_path.exists(),
        "latest_entry_found": False,
        "chunks_pre": None,
        "chunks_post": None,
        "gate_passed": False,
    }
    if not log_path.exists():
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error="rag-indexation.jsonl not found -- did you run cmd_rag_index?",
            recovery_hint="run `python3 -m engine.intelligence.pipeline.mce.orchestrate rag-index <slug>`",
        )
    latest: dict[str, Any] | None = None
    try:
        with open(log_path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if isinstance(obj, dict) and obj.get("slug") == slug:
                    latest = obj
    except Exception as exc:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"could not read rag-indexation.jsonl: {exc}",
            recovery_hint="check file permissions",
        )
    if latest is None:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"no rag-indexation entry found for slug '{slug}'",
            recovery_hint=f"run orchestrate rag-index {slug} first",
        )
    pre = latest.get("chunks_pre", 0) or 0
    post = latest.get("chunks_post", 0) or 0
    # PR-004: post > 0 AND post >= pre (same rule as orchestrate.cmd_rag_index).
    gate = post > 0 and post >= pre
    checks["latest_entry_found"] = True
    checks["chunks_pre"] = pre
    checks["chunks_post"] = post
    checks["gate_passed"] = gate

    if not gate:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"RAG gate failed: chunks_post={post} chunks_pre={pre}",
            recovery_hint="BM25 rebuild produced no new chunks or lost chunks; investigate the bucket",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


def validate_agent_generation(slug: str) -> dict[str, Any]:
    """S13 — agent generation (pipeline-ops: clone).

    Contract: all 15 required mind-clone files exist under agents/{bucket}/{slug}/.
    """
    step_id = "S13-agent-gen"
    validator = "validate_agent_generation"
    bucket = _detect_bucket(slug)
    agent_dir = _agent_dir(slug, bucket)
    found: list[str] = []
    missing: list[str] = []
    # MCE-13.6: use find_agent_file for the four core files to support both
    # lowercase (new) and UPPERCASE (legacy) conventions.
    _CORE_FILES = {"agent.md", "soul.md", "memory.md", "dna-config.yaml"}
    try:
        from engine.intelligence.utils.agent_files import find_agent_file as _faf
        _faf_available = True
    except Exception:
        _faf_available = False

    for name in _REQUIRED_AGENT_FILES:
        if name.lower() in _CORE_FILES and _faf_available:
            exists = _faf(agent_dir, name) is not None
        else:
            exists = (agent_dir / name).exists()
        if exists:
            found.append(name)
        else:
            missing.append(name)
    checks: dict[str, Any] = {
        "agent_dir": str(agent_dir),
        "files_found": len(found),
        "files_expected": len(_REQUIRED_AGENT_FILES),
        "missing_files": missing,
    }
    if missing:
        return _build(
            step_id,
            slug,
            validator,
            success=False,
            checks=checks,
            error=f"{len(missing)} agent files missing: {missing}",
            recovery_hint="re-run S13-agent-gen from the Phase 5 template expansion",
        )
    return _build(step_id, slug, validator, success=True, checks=checks)


# ---------------------------------------------------------------------------
# Dispatch registry (ADR-G5: one entry per step_id)
# ---------------------------------------------------------------------------

VALIDATORS: dict[str, Callable[[str], dict[str, Any]]] = {
    "S00-guard": validate_ingestion_guard,
    "S02-chunk": validate_chunks,
    "S04-entity": validate_entities,
    "S05-insight": validate_insights,
    "S06-dna-tag": validate_dna_tags,
    "S07-behavioral": validate_behavioral,
    "S08-identity": validate_identity,
    "S09-voice": validate_voice,
    "S10-checkpoint": validate_identity_gate,
    "S11-consolidation": validate_consolidation,
    "S12-rag": validate_rag_index,
    "S13-agent-gen": validate_agent_generation,
}


# ---------------------------------------------------------------------------
# Manual-test CLI
# ---------------------------------------------------------------------------


def _main(argv: list[str] | None = None) -> int:
    """Ad-hoc CLI: python3 -m engine.intelligence.pipeline.mce.validators <step> <slug>."""
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2 or args[0] in {"-h", "--help"}:
        print(
            "Usage: python3 -m engine.intelligence.pipeline.mce.validators <step_id> <slug>\n"
            f"Valid step_ids: {sorted(VALIDATORS)}",
            file=sys.stderr,
        )
        return 1 if len(args) != 2 else 0
    step_id, slug = args
    fn = VALIDATORS.get(step_id)
    if fn is None:
        print(f"Unknown step_id '{step_id}'. Valid: {sorted(VALIDATORS)}", file=sys.stderr)
        return 1
    result = fn(slug)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(_main())
