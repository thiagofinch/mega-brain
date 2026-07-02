#!/usr/bin/env python3
"""checkpoint_observer.py — PostToolUse soft-warn hook (Story MCE-4.3a).

Observes Write/Edit tool calls that touch .data/artifacts/ or knowledge/
pipeline state files, loads PIPELINE-STATE.json for the affected slug, runs
validate_pre_conditions + validate_post_conditions from enforcement.py, and
appends any violations to:

  .data/logs/checkpoint-violations.jsonl  — operational violations log
  .data/journey/checkpoint.jsonl          — Art. IX journey events

This hook NEVER returns {"continue": false} — soft-warn only.
V1 = observe + log.  Fail-closed flip lives in MCE-4.3b (PreToolUse).

Exit codes:
  0 = OK (always, including when violations are found)

Kill switches:
  MCE_CHECKPOINT_OBSERVER_DISABLED=1  — silently exit without logging

Pattern follows epistemic_validator.py (PostToolUse, append-only JSONL).

Finding F-12 (roundtable 2026-05-17): cmd_finalize already calls
cmd_identity_checkpoint in orchestrate.py:4375-4380.  This hook operates at
TOOL level (individual file writes), NOT at pipeline PHASE level.  Do NOT
invoke cmd_identity_checkpoint or cmd_finalize from here — orthogonal layers.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — resolved relative to project root (CLAUDE_PROJECT_DIR)
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
_VIOLATIONS_LOG = _PROJECT_ROOT / ".data" / "logs" / "checkpoint-violations.jsonl"
_JOURNEY_LOG = _PROJECT_ROOT / ".data" / "journey" / "checkpoint.jsonl"

# Artifact patterns that indicate a pipeline state file is being touched.
_ARTIFACT_PATTERNS = (".data/artifacts/", "knowledge/")


# ---------------------------------------------------------------------------
# Import enforcement.py — graceful fallback if engine path not on sys.path
# ---------------------------------------------------------------------------


def _import_enforcement():  # type: ignore[return]
    """Attempt to import enforcement.py; return module or None on failure."""
    engine_root = _PROJECT_ROOT / "engine" / "intelligence" / "pipeline" / "mce"
    engine_str = str(engine_root)
    if engine_str not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    try:
        from engine.intelligence.pipeline.mce import enforcement  # type: ignore[import]

        return enforcement
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Slug extraction
# ---------------------------------------------------------------------------


def _extract_slug(file_path: str) -> str | None:
    """Extract pipeline slug from a .data/artifacts/mce/{slug}/... path."""
    parts = Path(file_path).parts
    # Look for  …/.data/artifacts/mce/{slug}/…
    try:
        mce_idx = next(i for i, p in enumerate(parts) if p == "mce")
        if mce_idx + 1 < len(parts):
            return parts[mce_idx + 1]
    except StopIteration:
        pass
    return None


def _is_artifact_path(file_path: str) -> bool:
    """Return True when file_path touches a monitored artifact area."""
    norm = file_path.replace("\\", "/")
    return any(pat in norm for pat in _ARTIFACT_PATTERNS)


# ---------------------------------------------------------------------------
# Journal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def _handle_violations(
    slug: str,
    phase: str,
    violations: list[str],
    from_state: str,
) -> None:
    """Append violation records to both log files."""
    record: dict = {
        "entity_id": slug,
        "entity_type": "pipeline_slug",
        "event_type": "checkpoint_failed",
        "phase": phase,
        "violations": violations,
        "from_state": from_state,
        "timestamp": _now_iso(),
        "triggered_by": "checkpoint_observer.py",
    }
    _append_jsonl(_VIOLATIONS_LOG, record)
    _append_jsonl(_JOURNEY_LOG, record)


def main() -> int:
    # Kill switch
    if os.environ.get("MCE_CHECKPOINT_OBSERVER_DISABLED"):
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    if not isinstance(payload, dict):
        return 0

    # Extract file path from PostToolUse payload (Write/Edit shape).
    file_path = (
        payload.get("file_path")
        or payload.get("path")
        or payload.get("input", {}).get("file_path", "")
        or ""
    )
    if not isinstance(file_path, str):
        file_path = ""

    # Only observe writes that touch monitored artifact paths.
    if not file_path or not _is_artifact_path(file_path):
        return 0

    slug = _extract_slug(file_path)
    if not slug:
        # Path is in artifacts area but not under a slug — skip.
        return 0

    enforcement = _import_enforcement()
    if enforcement is None:
        # Cannot load enforcement module — log a meta-warning and exit clean.
        _append_jsonl(
            _VIOLATIONS_LOG,
            {
                "entity_id": slug,
                "entity_type": "pipeline_slug",
                "event_type": "checkpoint_observer_import_error",
                "phase": "unknown",
                "violations": ["enforcement.py could not be imported"],
                "from_state": "pre",
                "timestamp": _now_iso(),
                "triggered_by": "checkpoint_observer.py",
            },
        )
        return 0

    # Load existing pipeline state (empty dict for new slugs — first-run safe).
    state: dict = enforcement.load_pipeline_state(slug, _PROJECT_ROOT)

    # Use a generic phase label since we are observing at tool level, not
    # phase level.  A PostToolUse event does not carry phase context.
    phase = "tool_write"

    pre_violations: list[str] = enforcement.validate_pre_conditions(slug, phase, state)
    post_violations: list[str] = enforcement.validate_post_conditions(slug, phase, state)

    if pre_violations:
        _handle_violations(slug, phase, pre_violations, "pre")

    if post_violations:
        _handle_violations(slug, phase, post_violations, "post")

    # Soft-warn: always exit 0, never block.
    return 0


if __name__ == "__main__":
    sys.exit(main())
