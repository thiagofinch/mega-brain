"""
qa_gates.py -- Deterministic Validation Engine for the MCE Pipeline
====================================================================

Architecture Decision
---------------------
The MCE governance system has two complementary halves:

- **Synapse** (``core/engine/rules/workflows/mce.yaml``) holds *declarative*
  rules: gate definitions, veto conditions, severity levels, and transition
  mappings.  It answers "what should be checked?"

- **qa_gates** (this module) executes *imperative* checks: it reads actual
  artifact files on disk, validates their content against checkpoint criteria
  from ``mce_checkpoints.yaml``, and returns structured pass/fail results.
  It answers "did the check pass?"

This separation keeps rules editable in YAML while keeping validation logic
in testable, deterministic Python.

Import Direction (CRITICAL)
---------------------------
``state_machine.py`` imports condition functions from this module.
This module MUST NOT import ``state_machine.py`` -- doing so creates a
circular import.  The dependency arrow is one-way::

    state_machine.py  -->  qa_gates.py  -->  (reads YAML, reads artifacts)

Public API
----------
- ``validate_step(step, slug, **kwargs)`` -- validate a single pipeline step
- ``validate_handoff(from_step, to_step, slug)`` -- validate handoff contract
- ``get_gate_status(slug)`` -- overview of all step statuses
- ``can_start_chunking(event)`` ... ``can_finish(event)`` -- condition functions
  for ``transitions`` library (``send_event=True``)

Constraints
~~~~~~~~~~~
- stdlib + PyYAML + python-dotenv ONLY (no external deps, no LLM calls)
- Every function is DETERMINISTIC (reads files, checks thresholds, returns dicts)
- Never crashes -- catches all exceptions, returns failed check with detail

CLI::

    python3 -m core.intelligence.pipeline.mce.qa_gates --step 3 --slug alex-hormozi

Version: 1.0.0
Date: 2026-03-17
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Imports: core.paths (with standalone fallback)
# ---------------------------------------------------------------------------
from core.paths import (
    AGENTS_EXTERNAL,
    ARTIFACTS,
    KNOWLEDGE_EXTERNAL,
    LOGS,
    MISSION_CONTROL,
    ROUTING,
)

logger = logging.getLogger("mce.qa_gates")

# ---------------------------------------------------------------------------
# Output Paths (from ROUTING, never hardcoded)
# ---------------------------------------------------------------------------

_QA_LOG: Path = Path(ROUTING.get("quality_gaps", LOGS)) / "quality-gaps.jsonl"
_HANDOFF_LOG: Path = Path(ROUTING.get("handoff", LOGS / "handoffs")) / "mce-handoffs.jsonl"
_MCE_STATE_DIR: Path = Path(ROUTING.get("mce_state", MISSION_CONTROL / "mce"))

# ---------------------------------------------------------------------------
# Artifact Paths (canonical locations)
# ---------------------------------------------------------------------------

CHUNKS_STATE: Path = ARTIFACTS / "chunks" / "CHUNKS-STATE.json"
CANONICAL_MAP: Path = ARTIFACTS / "canonical" / "CANONICAL-MAP.json"
INSIGHTS_STATE: Path = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"

# ---------------------------------------------------------------------------
# Checkpoint Registry (lazy-loaded singleton)
# ---------------------------------------------------------------------------

_checkpoints_cache: dict[str, Any] | None = None
_gates_cache: dict[str, Any] | None = None


def _load_checkpoints() -> dict[str, Any]:
    """Load ``mce_checkpoints.yaml`` once and cache it.

    Returns an empty dict (with a logged warning) if the file is missing or
    unparseable -- never raises.
    """
    global _checkpoints_cache
    if _checkpoints_cache is not None:
        return _checkpoints_cache

    cp_path = Path(__file__).parent / "mce_checkpoints.yaml"
    if not cp_path.exists():
        logger.warning("mce_checkpoints.yaml not found at %s -- validation will be partial", cp_path)
        _checkpoints_cache = {}
        return _checkpoints_cache

    try:
        with open(cp_path, encoding="utf-8") as fh:
            _checkpoints_cache = yaml.safe_load(fh) or {}
    except Exception as exc:
        logger.warning("Failed to parse mce_checkpoints.yaml: %s", exc)
        _checkpoints_cache = {}

    return _checkpoints_cache


def _load_gates() -> dict[str, Any]:
    """Load ``mce.yaml`` quality gates once and cache them."""
    global _gates_cache
    if _gates_cache is not None:
        return _gates_cache

    from core.paths import CORE

    gates_path = CORE / "engine" / "rules" / "workflows" / "mce.yaml"
    if not gates_path.exists():
        logger.warning("mce.yaml not found at %s -- gate definitions unavailable", gates_path)
        _gates_cache = {}
        return _gates_cache

    try:
        with open(gates_path, encoding="utf-8") as fh:
            _gates_cache = yaml.safe_load(fh) or {}
    except Exception as exc:
        logger.warning("Failed to parse mce.yaml: %s", exc)
        _gates_cache = {}

    return _gates_cache


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _check(name: str, passed: bool, detail: str, *, blocking: bool = True) -> dict[str, Any]:
    """Build a single check result dict."""
    return {"name": name, "passed": passed, "detail": detail, "blocking": blocking}


def _safe_json_load(path: Path) -> Any:
    """Load a JSON file, returning ``None`` on any error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _safe_yaml_load(path: Path) -> Any:
    """Load a YAML file, returning ``None`` on any error."""
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except Exception:
        return None


def _append_jsonl(path: Path, entry: dict[str, Any]) -> None:
    """Append a JSON line to a JSONL file.  Non-fatal on failure."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write JSONL to %s", path, exc_info=True)


def _slug_state_dir(slug: str) -> Path:
    """Return the MCE state directory for a given slug."""
    return _MCE_STATE_DIR / slug


def _dna_dir(slug: str) -> Path:
    """Return the DNA YAML directory for a given slug under knowledge/external."""
    return KNOWLEDGE_EXTERNAL / "dna" / "persons" / slug


def _agent_dir(slug: str) -> Path:
    """Return the agent files directory for a given slug under agents/external."""
    return AGENTS_EXTERNAL / slug


def _dossier_path(slug: str) -> Path:
    """Return the dossier file path for a given slug."""
    formatted = slug.upper().replace("-", " ").replace("_", " ")
    parts = formatted.split()
    name = "-".join(parts)
    return KNOWLEDGE_EXTERNAL / "dossiers" / "persons" / f"DOSSIER-{name}.md"


# ---------------------------------------------------------------------------
# Step Validators (one function per pipeline step, returns list of checks)
# ---------------------------------------------------------------------------


def _validate_step_1_ingest(slug: str, **kwargs: Any) -> list[dict[str, Any]]:
    """Check: file was routed, classification confidence >= 0.5."""
    checks: list[dict[str, Any]] = []

    # Check if any source files exist in inbox or organized location
    inbox_dirs = [
        KNOWLEDGE_EXTERNAL / "inbox" / slug,
        KNOWLEDGE_EXTERNAL / "sources" / slug,
    ]
    file_found = any(d.exists() and any(d.iterdir()) for d in inbox_dirs if d.exists())
    checks.append(_check(
        "file_routed",
        file_found,
        f"Source files found in {slug} inbox/sources" if file_found else "No source files found",
    ))

    # Classification confidence from kwargs or metadata
    confidence = kwargs.get("classification_confidence", 0.0)
    if confidence == 0.0:
        # Try to read from metadata
        meta_path = _slug_state_dir(slug) / "metadata.yaml"
        meta = _safe_yaml_load(meta_path)
        if meta and isinstance(meta, dict):
            sources = meta.get("sources_processed", [])
            if sources and isinstance(sources, list):
                last = sources[-1] if sources else {}
                confidence = last.get("confidence", 0.0) if isinstance(last, dict) else 0.0

    checks.append(_check(
        "classification_confidence",
        confidence >= 0.5,
        f"Confidence {confidence:.2f} (threshold: 0.50)",
    ))

    return checks


def _validate_step_2_batch(slug: str, **kwargs: Any) -> list[dict[str, Any]]:
    """Check: batches_created > 0."""
    checks: list[dict[str, Any]] = []

    # Check batch registry or metadata for batch count
    batch_count = kwargs.get("batches_created", 0)
    if batch_count == 0:
        meta_path = _slug_state_dir(slug) / "metadata.yaml"
        meta = _safe_yaml_load(meta_path)
        if meta and isinstance(meta, dict):
            phases = meta.get("phases", {})
            if isinstance(phases, dict):
                batch_phase = phases.get("batch_creation", {})
                if isinstance(batch_phase, dict):
                    batch_count = batch_phase.get("batches_created", 0)

    checks.append(_check(
        "batches_created",
        batch_count > 0,
        f"{batch_count} batches created" if batch_count > 0 else "No batches created",
    ))

    return checks


def _validate_step_3_chunk(slug: str, **_kwargs: Any) -> list[dict[str, Any]]:
    """Check: CHUNKS-STATE.json exists, chunks[] non-empty, all chunk_ids unique."""
    checks: list[dict[str, Any]] = []

    # File exists
    checks.append(_check(
        "chunks_state_exists",
        CHUNKS_STATE.exists(),
        f"CHUNKS-STATE.json found at {CHUNKS_STATE}" if CHUNKS_STATE.exists()
        else f"CHUNKS-STATE.json NOT found at {CHUNKS_STATE}",
    ))

    if not CHUNKS_STATE.exists():
        checks.append(_check("chunks_count", False, "Cannot check -- file missing"))
        checks.append(_check("chunk_ids_unique", False, "Cannot check -- file missing"))
        return checks

    data = _safe_json_load(CHUNKS_STATE)
    if data is None:
        checks.append(_check("chunks_count", False, "Failed to parse CHUNKS-STATE.json"))
        checks.append(_check("chunk_ids_unique", False, "Failed to parse CHUNKS-STATE.json"))
        return checks

    # Chunks non-empty
    chunks = data.get("chunks", []) if isinstance(data, dict) else []
    chunk_count = len(chunks)
    checks.append(_check(
        "chunks_count",
        chunk_count > 0,
        f"{chunk_count} chunks found",
    ))

    # All chunk_ids unique
    if chunk_count > 0:
        ids = [c.get("chunk_id", c.get("id", "")) for c in chunks if isinstance(c, dict)]
        unique_count = len(set(ids))
        checks.append(_check(
            "chunk_ids_unique",
            unique_count == len(ids),
            f"{unique_count}/{len(ids)} unique chunk IDs",
        ))
    else:
        checks.append(_check("chunk_ids_unique", False, "No chunks to check"))

    return checks


def _validate_step_4_entity(slug: str, **_kwargs: Any) -> list[dict[str, Any]]:
    """Check: CANONICAL-MAP.json exists, has entities, source person has entry."""
    checks: list[dict[str, Any]] = []

    checks.append(_check(
        "canonical_map_exists",
        CANONICAL_MAP.exists(),
        "CANONICAL-MAP.json found" if CANONICAL_MAP.exists()
        else f"CANONICAL-MAP.json NOT found at {CANONICAL_MAP}",
    ))

    if not CANONICAL_MAP.exists():
        checks.append(_check("entities_count", False, "Cannot check -- file missing"))
        checks.append(_check("source_person_entry", False, "Cannot check -- file missing"))
        return checks

    data = _safe_json_load(CANONICAL_MAP)
    if data is None:
        checks.append(_check("entities_count", False, "Failed to parse CANONICAL-MAP.json"))
        checks.append(_check("source_person_entry", False, "Failed to parse"))
        return checks

    # Has entities
    entities = data.get("entities", data.get("persons", {}))
    entity_count = len(entities) if isinstance(entities, (dict, list)) else 0
    checks.append(_check(
        "entities_count",
        entity_count > 0,
        f"{entity_count} entities found",
    ))

    # Source person has entry
    has_entry = False
    slug_lower = slug.lower().replace("-", " ").replace("_", " ")
    if isinstance(entities, dict):
        for key in entities:
            if slug_lower in key.lower().replace("-", " ").replace("_", " "):
                has_entry = True
                break
    elif isinstance(entities, list):
        for ent in entities:
            name = ent.get("canonical_name", ent.get("name", "")) if isinstance(ent, dict) else ""
            if slug_lower in name.lower().replace("-", " ").replace("_", " "):
                has_entry = True
                break

    checks.append(_check(
        "source_person_entry",
        has_entry,
        f"Entry found for '{slug}'" if has_entry else f"No entry found for '{slug}'",
    ))

    return checks


def _validate_step_5_insight(slug: str, **_kwargs: Any) -> list[dict[str, Any]]:
    """Check: INSIGHTS-STATE.json has person entry, insights[] non-empty, each has chunks[]."""
    checks: list[dict[str, Any]] = []

    checks.append(_check(
        "insights_state_exists",
        INSIGHTS_STATE.exists(),
        "INSIGHTS-STATE.json found" if INSIGHTS_STATE.exists()
        else f"INSIGHTS-STATE.json NOT found at {INSIGHTS_STATE}",
    ))

    if not INSIGHTS_STATE.exists():
        checks.append(_check("person_has_insights", False, "Cannot check -- file missing"))
        checks.append(_check("all_insights_have_chunks", False, "Cannot check -- file missing"))
        return checks

    data = _safe_json_load(INSIGHTS_STATE)
    if data is None:
        checks.append(_check("person_has_insights", False, "Failed to parse"))
        checks.append(_check("all_insights_have_chunks", False, "Failed to parse"))
        return checks

    # Find person insights
    person_insights: list[Any] = []
    if isinstance(data, dict):
        persons = data.get("persons", {})
        if isinstance(persons, dict):
            slug_lower = slug.lower()
            for key, pdata in persons.items():
                if slug_lower in key.lower().replace("-", " ").replace("_", " "):
                    if isinstance(pdata, dict):
                        person_insights = pdata.get("insights", [])
                    break
        # Fallback: flat insights list
        if not person_insights:
            person_insights = data.get("insights", [])

    insight_count = len(person_insights)
    checks.append(_check(
        "person_has_insights",
        insight_count > 0,
        f"{insight_count} insights for '{slug}'",
    ))

    # Each insight has chunks
    if insight_count > 0:
        missing_chunks = 0
        for ins in person_insights:
            if isinstance(ins, dict):
                chunk_refs = ins.get("chunks", ins.get("chunk_ids", []))
                if not chunk_refs:
                    missing_chunks += 1
        checks.append(_check(
            "all_insights_have_chunks",
            missing_chunks == 0,
            f"All {insight_count} insights have chunk references"
            if missing_chunks == 0
            else f"{missing_chunks}/{insight_count} insights missing chunk references",
        ))
    else:
        checks.append(_check("all_insights_have_chunks", False, "No insights to check"))

    return checks


def _validate_step_6_behavioral(slug: str, **_kwargs: Any) -> list[dict[str, Any]]:
    """Check: behavioral_patterns exists, each pattern has 2+ chunk_ids."""
    checks: list[dict[str, Any]] = []

    # Look for behavioral data in MCE state or insights
    state_dir = _slug_state_dir(slug)
    behavioral_path = state_dir / "behavioral_patterns.json"
    alt_path = state_dir / "mce_behavioral.json"

    bp_data = None
    for p in (behavioral_path, alt_path):
        if p.exists():
            bp_data = _safe_json_load(p)
            if bp_data is not None:
                break

    # Also check INSIGHTS-STATE for behavioral patterns
    if bp_data is None and INSIGHTS_STATE.exists():
        is_data = _safe_json_load(INSIGHTS_STATE)
        if isinstance(is_data, dict):
            persons = is_data.get("persons", {})
            for key, pdata in persons.items() if isinstance(persons, dict) else []:
                if slug.lower() in key.lower().replace("-", " ").replace("_", " "):
                    if isinstance(pdata, dict):
                        bp_data = pdata.get("behavioral_patterns", None)
                    break

    patterns: list[Any] = []
    if isinstance(bp_data, dict):
        patterns = bp_data.get("behavioral_patterns", bp_data.get("patterns", []))
    elif isinstance(bp_data, list):
        patterns = bp_data

    checks.append(_check(
        "behavioral_patterns_exist",
        len(patterns) > 0,
        f"{len(patterns)} behavioral patterns found"
        if patterns else "No behavioral patterns found",
    ))

    # Each pattern has 2+ chunk_ids
    if patterns:
        weak_patterns = 0
        for pat in patterns:
            if isinstance(pat, dict):
                refs = pat.get("chunk_ids", pat.get("evidence", pat.get("chunks", [])))
                if len(refs) < 2:
                    weak_patterns += 1
        checks.append(_check(
            "min_chunk_ids_per_pattern",
            weak_patterns == 0,
            f"All {len(patterns)} patterns have 2+ chunk references"
            if weak_patterns == 0
            else f"{weak_patterns}/{len(patterns)} patterns have fewer than 2 chunk references",
            blocking=True,
        ))
    else:
        checks.append(_check("min_chunk_ids_per_pattern", False, "No patterns to check"))

    return checks


def _validate_step_7_identity(slug: str, **_kwargs: Any) -> list[dict[str, Any]]:
    """Check: value_hierarchy has Tier 1, exactly 1 MASTER obsession."""
    checks: list[dict[str, Any]] = []

    state_dir = _slug_state_dir(slug)
    identity_path = state_dir / "identity_layer.json"
    alt_path = state_dir / "mce_identity.json"

    id_data = None
    for p in (identity_path, alt_path):
        if p.exists():
            id_data = _safe_json_load(p)
            if id_data is not None:
                break

    # value_hierarchy has Tier 1
    tier1_count = 0
    if isinstance(id_data, dict):
        hierarchy = id_data.get("value_hierarchy", id_data.get("values", []))
        if isinstance(hierarchy, list):
            for val in hierarchy:
                if isinstance(val, dict):
                    tier = val.get("tier", val.get("level", 0))
                    if str(tier) in ("1", "Tier 1", "tier_1"):
                        tier1_count += 1
        elif isinstance(hierarchy, dict):
            tier1 = hierarchy.get("tier_1", hierarchy.get("Tier 1", []))
            tier1_count = len(tier1) if isinstance(tier1, list) else (1 if tier1 else 0)

    checks.append(_check(
        "value_hierarchy_tier1",
        tier1_count >= 1,
        f"{tier1_count} Tier 1 values found" if tier1_count > 0 else "No Tier 1 values found",
    ))

    # Exactly 1 MASTER obsession
    master_count = 0
    if isinstance(id_data, dict):
        obsessions = id_data.get("obsessions", id_data.get("core_obsessions", []))
        if isinstance(obsessions, list):
            for obs in obsessions:
                if isinstance(obs, dict):
                    classification = str(obs.get("classification", obs.get("tier", ""))).upper()
                    if classification == "MASTER":
                        master_count += 1
                elif isinstance(obs, str) and "MASTER" in obs.upper():
                    master_count += 1

    checks.append(_check(
        "master_obsession_count",
        master_count == 1,
        f"{master_count} MASTER obsessions (expected exactly 1)",
    ))

    return checks


def _validate_step_8_voice(slug: str, **_kwargs: Any) -> list[dict[str, Any]]:
    """Check: VOICE-DNA.yaml exists, has signature_phrases (>= 3), behavioral_states, 6 dimensions."""
    checks: list[dict[str, Any]] = []

    voice_path = _dna_dir(slug) / "VOICE-DNA.yaml"
    checks.append(_check(
        "voice_dna_exists",
        voice_path.exists(),
        f"VOICE-DNA.yaml found at {voice_path}" if voice_path.exists()
        else f"VOICE-DNA.yaml NOT found at {voice_path}",
    ))

    if not voice_path.exists():
        checks.append(_check("signature_phrases_count", False, "Cannot check -- file missing"))
        checks.append(_check("behavioral_states_exist", False, "Cannot check -- file missing"))
        checks.append(_check("voice_dimensions_count", False, "Cannot check -- file missing"))
        return checks

    data = _safe_yaml_load(voice_path)
    if data is None:
        checks.append(_check("signature_phrases_count", False, "Failed to parse VOICE-DNA.yaml"))
        checks.append(_check("behavioral_states_exist", False, "Failed to parse"))
        checks.append(_check("voice_dimensions_count", False, "Failed to parse"))
        return checks

    # Signature phrases >= 3
    phrases = data.get("signature_phrases", data.get("catchphrases", []))
    if not isinstance(phrases, list):
        phrases = []
    checks.append(_check(
        "signature_phrases_count",
        len(phrases) >= 3,
        f"{len(phrases)} signature phrases (threshold: 3)",
    ))

    # Behavioral states (3-5)
    states = data.get("behavioral_states", data.get("states", []))
    if not isinstance(states, list):
        states = list(states.keys()) if isinstance(states, dict) else []
    checks.append(_check(
        "behavioral_states_exist",
        len(states) >= 3,
        f"{len(states)} behavioral states found",
    ))

    # 6 tone dimensions
    dimensions = data.get("tone_dimensions", data.get("dimensions", data.get("voice_dimensions", {})))
    dim_count = len(dimensions) if isinstance(dimensions, (dict, list)) else 0
    checks.append(_check(
        "voice_dimensions_count",
        dim_count >= 6,
        f"{dim_count} tone dimensions (threshold: 6)",
    ))

    return checks


def _validate_step_9_checkpoint(slug: str, **kwargs: Any) -> list[dict[str, Any]]:
    """Check: pipeline_state.yaml shows identity_checkpoint -> consolidation transition."""
    checks: list[dict[str, Any]] = []

    state_path = _slug_state_dir(slug) / "pipeline_state.yaml"
    if not state_path.exists():
        checks.append(_check(
            "checkpoint_approved",
            False,
            f"pipeline_state.yaml not found at {state_path}",
        ))
        return checks

    state_data = _safe_yaml_load(state_path)
    if state_data is None:
        checks.append(_check("checkpoint_approved", False, "Failed to parse pipeline_state.yaml"))
        return checks

    # Check if user_decision was APPROVE or current state is beyond identity_checkpoint
    current_state = state_data.get("current_state", state_data.get("state", ""))
    history = state_data.get("history", [])

    # Either the user explicitly approved, or the state has moved past checkpoint
    post_checkpoint_states = {"consolidation", "agent_generation", "validation", "complete"}
    user_decision = kwargs.get("user_decision", "")

    approved = (
        current_state in post_checkpoint_states
        or str(user_decision).upper() == "APPROVE"
        or any(
            isinstance(h, dict) and h.get("to", h.get("dest", "")) == "consolidation"
            for h in (history if isinstance(history, list) else [])
        )
    )

    checks.append(_check(
        "checkpoint_approved",
        approved,
        f"Identity checkpoint approved (state: {current_state})"
        if approved
        else f"Identity checkpoint NOT approved (state: {current_state})",
    ))

    return checks


def _validate_step_10_consolidation(slug: str, **_kwargs: Any) -> list[dict[str, Any]]:
    """Check: dossier exists, 5/5 DNA YAMLs exist, agent files exist."""
    checks: list[dict[str, Any]] = []

    # Dossier exists
    dossier = _dossier_path(slug)
    checks.append(_check(
        "dossier_exists",
        dossier.exists(),
        f"Dossier found at {dossier.name}" if dossier.exists()
        else f"Dossier NOT found at {dossier}",
    ))

    # 5/5 DNA YAMLs
    dna_dir = _dna_dir(slug)
    expected_dna = [
        "FILOSOFIAS.yaml",
        "MODELOS-MENTAIS.yaml",
        "HEURISTICAS.yaml",
        "FRAMEWORKS.yaml",
        "METODOLOGIAS.yaml",
    ]
    found_dna = [f for f in expected_dna if (dna_dir / f).exists()]
    checks.append(_check(
        "dna_yamls_count",
        len(found_dna) == 5,
        f"{len(found_dna)}/5 DNA YAMLs found in {dna_dir.name}/",
    ))

    # Agent files (AGENT.md + SOUL.md + MEMORY.md + DNA-CONFIG.yaml)
    agent_dir = _agent_dir(slug)
    expected_agent = ["AGENT.md", "SOUL.md", "MEMORY.md", "DNA-CONFIG.yaml"]
    found_agent = [f for f in expected_agent if (agent_dir / f).exists()]
    checks.append(_check(
        "agent_files_exist",
        len(found_agent) == len(expected_agent),
        f"{len(found_agent)}/{len(expected_agent)} agent files found in {agent_dir.name}/",
    ))

    return checks


def _validate_step_11_finalize(slug: str, **_kwargs: Any) -> list[dict[str, Any]]:
    """Check: state is complete or validation, metrics saved, log generated."""
    checks: list[dict[str, Any]] = []

    # State is complete or validation
    state_path = _slug_state_dir(slug) / "pipeline_state.yaml"
    state_data = _safe_yaml_load(state_path) if state_path.exists() else None
    current_state = ""
    if isinstance(state_data, dict):
        current_state = state_data.get("current_state", state_data.get("state", ""))

    terminal_states = {"validation", "complete"}
    checks.append(_check(
        "state_is_terminal",
        current_state in terminal_states,
        f"State is '{current_state}'" + (" (terminal)" if current_state in terminal_states else ""),
    ))

    # Metrics saved
    metrics_path = _slug_state_dir(slug) / "metrics.yaml"
    checks.append(_check(
        "metrics_saved",
        metrics_path.exists(),
        "Metrics file found" if metrics_path.exists() else "Metrics file NOT found",
        blocking=False,
    ))

    # Log generated (check logs/sessions for a matching log)
    log_dir = LOGS / "sessions"
    has_log = False
    if log_dir.exists():
        for f in log_dir.iterdir():
            if slug in f.name.lower() and f.suffix in (".md", ".jsonl"):
                has_log = True
                break
    checks.append(_check(
        "log_generated",
        has_log,
        f"Session log found for '{slug}'" if has_log else "No session log found",
        blocking=False,
    ))

    return checks


def _validate_step_12_report(slug: str, **_kwargs: Any) -> list[dict[str, Any]]:
    """Check: validation score >= 70 (count of passing checks / total checks * 100)."""
    checks: list[dict[str, Any]] = []

    # Run all previous step validations to compute a score
    all_checks: list[dict[str, Any]] = []
    for step_num in range(1, 12):
        validator = _STEP_VALIDATORS.get(step_num)
        if validator:
            try:
                step_checks = validator(slug)
                all_checks.extend(step_checks)
            except Exception:
                all_checks.append(_check(f"step_{step_num}_error", False, "Validator error"))

    total = len(all_checks)
    passed_count = sum(1 for c in all_checks if c.get("passed"))
    score = round((passed_count / total * 100), 1) if total > 0 else 0.0

    checks.append(_check(
        "validation_score",
        score >= 70,
        f"Score: {score:.1f}% ({passed_count}/{total} checks passed, threshold: 70%)",
    ))

    # Critical checks (blocking) all pass
    blocking_checks = [c for c in all_checks if c.get("blocking", True)]
    blocking_failures = [c for c in blocking_checks if not c.get("passed")]
    checks.append(_check(
        "critical_checks_pass",
        len(blocking_failures) == 0,
        f"All {len(blocking_checks)} blocking checks pass"
        if not blocking_failures
        else f"{len(blocking_failures)} blocking checks failed: "
        + ", ".join(c["name"] for c in blocking_failures[:5]),
    ))

    return checks


# ---------------------------------------------------------------------------
# Step Validator Registry
# ---------------------------------------------------------------------------

_STEP_VALIDATORS: dict[int, Any] = {
    1: _validate_step_1_ingest,
    2: _validate_step_2_batch,
    3: _validate_step_3_chunk,
    4: _validate_step_4_entity,
    5: _validate_step_5_insight,
    6: _validate_step_6_behavioral,
    7: _validate_step_7_identity,
    8: _validate_step_8_voice,
    9: _validate_step_9_checkpoint,
    10: _validate_step_10_consolidation,
    11: _validate_step_11_finalize,
    12: _validate_step_12_report,
}

# ---------------------------------------------------------------------------
# Public API: validate_step
# ---------------------------------------------------------------------------


def validate_step(step: int, slug: str, **kwargs: Any) -> dict[str, Any]:
    """Validate that a pipeline step completed successfully.

    Args:
        step: MCE pipeline step number (1-12).
        slug: Person slug (e.g., ``"alex-hormozi"``).
        **kwargs: Optional overrides passed to step validators (e.g.,
            ``classification_confidence=0.8``).

    Returns:
        Structured result dict with ``passed``, ``checks``,
        ``blocking_failures``, and ``timestamp``.
    """
    timestamp = _now_iso()

    # Graceful degradation: if checkpoints file missing, skip
    _load_checkpoints()

    # Find validator
    validator = _STEP_VALIDATORS.get(step)
    if validator is None:
        result: dict[str, Any] = {
            "step": step,
            "slug": slug,
            "passed": True,
            "checks": [],
            "blocking_failures": [],
            "timestamp": timestamp,
            "warning": f"No validator for step {step}",
        }
        _append_jsonl(_QA_LOG, result)
        return result

    # Execute validator
    try:
        step_checks = validator(slug, **kwargs)
    except Exception as exc:
        logger.warning("Validator for step %d failed: %s", step, exc)
        step_checks = [_check(f"step_{step}_error", False, f"Validator exception: {exc}")]

    # Determine pass/fail
    blocking_failures = [
        c["name"] for c in step_checks if not c.get("passed") and c.get("blocking", True)
    ]
    all_passed = len(blocking_failures) == 0

    result = {
        "step": step,
        "slug": slug,
        "passed": all_passed,
        "checks": step_checks,
        "blocking_failures": blocking_failures,
        "timestamp": timestamp,
    }

    # Write JSONL to quality_gaps log (always, pass or fail)
    _append_jsonl(_QA_LOG, result)

    # Write JSONL to handoff log (only on pass)
    if all_passed:
        handoff_entry = {
            "from_step": step,
            "to_step": step + 1 if step < 12 else None,
            "slug": slug,
            "passed": True,
            "checks_summary": f"{sum(1 for c in step_checks if c['passed'])}/{len(step_checks)}",
            "timestamp": timestamp,
        }
        _append_jsonl(_HANDOFF_LOG, handoff_entry)

    # Write step completion marker (only on pass)
    if all_passed:
        marker_dir = _slug_state_dir(slug)
        marker_dir.mkdir(parents=True, exist_ok=True)
        marker_path = marker_dir / f"step_{step}_complete.json"
        try:
            marker_data = {
                "slug": slug,
                "step": step,
                "passed": True,
                "timestamp": timestamp,
                "checks_summary": f"{sum(1 for c in step_checks if c['passed'])}/{len(step_checks)}",
            }
            marker_path.write_text(
                json.dumps(marker_data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except Exception:
            logger.debug("Failed to write step marker to %s", marker_path, exc_info=True)

    return result


# ---------------------------------------------------------------------------
# Public API: validate_handoff
# ---------------------------------------------------------------------------


def validate_handoff(from_step: int, to_step: int, slug: str) -> dict[str, Any]:
    """Validate the handoff contract between two pipeline steps.

    Checks that ``from_step`` passed and its artifacts are ready for ``to_step``.

    Args:
        from_step: The step that should be complete.
        to_step: The step about to start.
        slug: Person slug.

    Returns:
        Dict with ``passed``, ``from_step``, ``to_step``, ``artifacts_required``,
        ``artifacts_present``, and ``checks``.
    """
    timestamp = _now_iso()

    # Validate the from_step first
    from_result = validate_step(from_step, slug)
    checks = list(from_result.get("checks", []))

    # Determine expected artifacts for from_step
    artifact_map: dict[int, list[Path]] = {
        1: [KNOWLEDGE_EXTERNAL / "sources" / slug],
        2: [],  # batch state in metadata
        3: [CHUNKS_STATE],
        4: [CANONICAL_MAP],
        5: [INSIGHTS_STATE],
        6: [_slug_state_dir(slug) / "behavioral_patterns.json"],
        7: [_slug_state_dir(slug) / "identity_layer.json"],
        8: [_dna_dir(slug) / "VOICE-DNA.yaml"],
        9: [_slug_state_dir(slug) / "pipeline_state.yaml"],
        10: [_dossier_path(slug), _dna_dir(slug), _agent_dir(slug)],
        11: [_slug_state_dir(slug) / "metrics.yaml"],
    }

    required = artifact_map.get(from_step, [])
    present = [str(a) for a in required if a.exists()]

    result: dict[str, Any] = {
        "from_step": from_step,
        "to_step": to_step,
        "slug": slug,
        "passed": from_result["passed"],
        "checks": checks,
        "blocking_failures": from_result.get("blocking_failures", []),
        "artifacts_required": [str(a) for a in required],
        "artifacts_present": present,
        "timestamp": timestamp,
    }

    _append_jsonl(_QA_LOG, {**result, "type": "handoff"})
    return result


# ---------------------------------------------------------------------------
# Public API: get_gate_status
# ---------------------------------------------------------------------------


def get_gate_status(slug: str) -> dict[str, Any]:
    """Get overall gate status for all steps of a slug.

    Reads step completion markers from the slug's state directory.

    Args:
        slug: Person slug.

    Returns:
        Dict with ``slug`` and ``steps`` mapping step numbers to status dicts.
    """
    steps: dict[int, dict[str, Any]] = {}

    for step_num in range(1, 13):
        marker_path = _slug_state_dir(slug) / f"step_{step_num}_complete.json"
        if marker_path.exists():
            marker_data = _safe_json_load(marker_path)
            if isinstance(marker_data, dict):
                steps[step_num] = {
                    "passed": marker_data.get("passed", False),
                    "checked_at": marker_data.get("timestamp", "unknown"),
                }
            else:
                steps[step_num] = {"passed": None}
        else:
            steps[step_num] = {"passed": None}

    return {"slug": slug, "steps": steps}


# ---------------------------------------------------------------------------
# Condition Functions (for transitions library, send_event=True)
# ---------------------------------------------------------------------------


def _extract_slug(event: Any = None) -> str:
    """Safely extract slug from a transitions event object.

    The ``transitions`` library passes an ``EventData`` object when
    ``send_event=True``.  The slug is expected in ``event.kwargs["slug"]``
    or as the model's ``slug`` attribute.

    Returns ``"__unknown__"`` if extraction fails (keeps conditions testable
    without a real event).
    """
    if event is None:
        return "__unknown__"

    # Try event.kwargs["slug"]
    try:
        kwargs = getattr(event, "kwargs", {})
        if isinstance(kwargs, dict) and "slug" in kwargs:
            return kwargs["slug"]
    except Exception:
        pass

    # Try event.model.slug (PipelineStateMachine stores slug)
    try:
        model = getattr(event, "model", None)
        if model is not None:
            slug_attr = getattr(model, "slug", None) or getattr(model, "_slug", None)
            if slug_attr:
                return str(slug_attr)
    except Exception:
        pass

    return "__unknown__"


def can_start_chunking(event: Any = None) -> bool:
    """Condition: step 1 (ingest) must pass before chunking starts."""
    slug = _extract_slug(event)
    result = validate_step(1, slug)
    return result["passed"]


def can_start_entities(event: Any = None) -> bool:
    """Condition: step 3 (chunking) must pass before entity resolution starts."""
    slug = _extract_slug(event)
    result = validate_step(3, slug)
    return result["passed"]


def can_start_knowledge(event: Any = None) -> bool:
    """Condition: step 4 (entity resolution) must pass before knowledge extraction."""
    slug = _extract_slug(event)
    result = validate_step(4, slug)
    return result["passed"]


def can_checkpoint(event: Any = None) -> bool:
    """Condition: steps 6-8 (MCE extraction phases) must pass before checkpoint."""
    slug = _extract_slug(event)
    for step_num in (6, 7, 8):
        result = validate_step(step_num, slug)
        if not result["passed"]:
            return False
    return True


def can_approve(event: Any = None) -> bool:
    """Condition: step 9 (identity checkpoint) must pass before consolidation."""
    slug = _extract_slug(event)
    result = validate_step(9, slug, user_decision="APPROVE")
    return result["passed"]


def can_start_agents(event: Any = None) -> bool:
    """Condition: step 10 (consolidation) must pass before agent generation."""
    slug = _extract_slug(event)
    result = validate_step(10, slug)
    return result["passed"]


def can_validate(event: Any = None) -> bool:
    """Condition: step 11 (finalize) must pass before validation."""
    slug = _extract_slug(event)
    result = validate_step(11, slug)
    return result["passed"]


def can_finish(event: Any = None) -> bool:
    """Condition: step 12 (report) must pass before marking complete."""
    slug = _extract_slug(event)
    result = validate_step(12, slug)
    return result["passed"]


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def _cli_main(argv: list[str] | None = None) -> int:
    """CLI entry point for standalone validation.

    Usage::

        python3 -m core.intelligence.pipeline.mce.qa_gates --step 3 --slug alex-hormozi
        python3 -m core.intelligence.pipeline.mce.qa_gates --all --slug alex-hormozi
        python3 -m core.intelligence.pipeline.mce.qa_gates --status --slug alex-hormozi

    Returns:
        Exit code (0 = all passed, 1 = some failed).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="MCE Pipeline QA Gates -- Deterministic Validation Engine",
    )
    parser.add_argument("--step", type=int, help="Pipeline step number (1-12)")
    parser.add_argument("--slug", required=True, help="Person slug (e.g. alex-hormozi)")
    parser.add_argument("--all", action="store_true", help="Validate all steps")
    parser.add_argument("--status", action="store_true", help="Show gate status overview")
    parser.add_argument("--handoff", type=int, nargs=2, metavar=("FROM", "TO"),
                        help="Validate handoff between two steps")

    args = parser.parse_args(argv)

    if args.status:
        result = get_gate_status(args.slug)
        print(json.dumps(result, indent=2, default=str))
        return 0

    if args.handoff:
        result = validate_handoff(args.handoff[0], args.handoff[1], args.slug)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["passed"] else 1

    if args.all:
        results = []
        any_failed = False
        for step_num in range(1, 13):
            r = validate_step(step_num, args.slug)
            results.append(r)
            if not r["passed"]:
                any_failed = True
        print(json.dumps(results, indent=2, default=str))
        return 1 if any_failed else 0

    if args.step is not None:
        result = validate_step(args.step, args.slug)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["passed"] else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(_cli_main())
