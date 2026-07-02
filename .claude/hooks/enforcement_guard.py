#!/usr/bin/env python3
"""enforcement_guard.py — PreToolUse fail-closed hook (Story MCE-4.3b).

When MCE_CHECKPOINT_FAIL_CLOSED=1, blocks Write/Edit tool calls that touch
.data/artifacts/ pipeline state files and have checkpoint violations.

When MCE_CHECKPOINT_FAIL_CLOSED=0 (DEFAULT), behaves as soft-warn — identical
to checkpoint_observer.py (MCE-4.3a). The flip is OPT-IN and deliberate.

Decision: _extract_slug moved from checkpoint_observer.py to enforcement.py as
public extract_slug_from_path() to avoid duplicating logic in both hooks.
See commit message for AC5 compliance trace.

Kill switches:
  MCE_CHECKPOINT_FAIL_CLOSED=0  (default) — soft-warn, never blocks
  MCE_CHECKPOINT_FAIL_CLOSED=1             — fail-closed, blocks on violation

PreToolUse blocking protocol:
  stdout JSON {"continue": false, "stopReason": "<msg>"} — exit code 0.
  Exit code is NOT the blocking signal — JSON stdout is.

Constitution: Art. IX (Journey Log), Art. X (Artifact Contracts),
              Art. XII (Pipeline MCE Integrity).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
_VIOLATIONS_LOG = _PROJECT_ROOT / ".data" / "logs" / "checkpoint-violations.jsonl"
_ENFORCEMENT_JOURNEY = _PROJECT_ROOT / ".data" / "journey" / "enforcement.jsonl"

# Artifact patterns monitored by this hook.
_ARTIFACT_PATTERNS = (".data/artifacts/", "knowledge/")


# ---------------------------------------------------------------------------
# Import enforcement.py — same pattern as checkpoint_observer.py
# ---------------------------------------------------------------------------


def _import_enforcement():  # type: ignore[return]
    """Import enforcement module via package import or direct file load fallback.

    The package import can fail if engine/__init__.py pulls optional deps not
    installed in all environments.  Direct spec load is always safe because
    enforcement.py has zero non-stdlib deps.
    """
    import importlib.util

    root_str = str(_PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    # Try package import first.
    try:
        from engine.intelligence.pipeline.mce import enforcement  # type: ignore[import]

        return enforcement
    except (ImportError, ModuleNotFoundError):
        pass

    # Fallback: load directly from file — bypasses package __init__ chain.
    enforcement_path = (
        _PROJECT_ROOT / "engine" / "intelligence" / "pipeline" / "mce" / "enforcement.py"
    )
    if not enforcement_path.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("enforcement", enforcement_path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        return mod
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _is_artifact_path(file_path: str) -> bool:
    norm = file_path.replace("\\", "/")
    return any(pat in norm for pat in _ARTIFACT_PATTERNS)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def _is_fail_closed() -> bool:
    """Return True when the kill switch is explicitly set to '1'."""
    return os.environ.get("MCE_CHECKPOINT_FAIL_CLOSED", "0") == "1"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    if not isinstance(payload, dict):
        return 0

    # Extract file path from PreToolUse payload shape.
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    file_path: str = (
        tool_input.get("file_path")
        or tool_input.get("path")
        or payload.get("file_path")
        or payload.get("path")
        or ""
    )
    if not isinstance(file_path, str):
        file_path = ""

    # Only guard writes that touch monitored artifact paths.
    if not file_path or not _is_artifact_path(file_path):
        return 0

    enforcement = _import_enforcement()
    if enforcement is None:
        # Cannot load enforcement — pass silently (fail-open on import error).
        return 0

    # Use extract_slug_from_path from enforcement.py (moved there for AC5).
    extract_fn = getattr(enforcement, "extract_slug_from_path", None)
    if extract_fn is None:
        # Fallback: inline extraction (same algorithm as checkpoint_observer).
        parts = Path(file_path).parts
        slug = None
        try:
            mce_idx = next(i for i, p in enumerate(parts) if p == "mce")
            if mce_idx + 1 < len(parts):
                slug = parts[mce_idx + 1]
        except StopIteration:
            pass
    else:
        slug = extract_fn(file_path)

    if not slug:
        return 0

    state: dict = enforcement.load_pipeline_state(slug, _PROJECT_ROOT)
    phase = "tool_write"

    pre_violations: list[str] = enforcement.validate_pre_conditions(slug, phase, state)
    post_violations: list[str] = enforcement.validate_post_conditions(slug, phase, state)
    all_violations = pre_violations + post_violations

    if not all_violations:
        return 0

    # Violations found — check kill switch.
    if not _is_fail_closed():
        # Soft-warn mode: log but do NOT block.
        record = {
            "entity_id": slug,
            "entity_type": "pipeline_slug",
            "event_type": "checkpoint_failed",
            "phase": phase,
            "violations": all_violations,
            "fail_closed": False,
            "timestamp": _now_iso(),
            "triggered_by": "enforcement_guard.py",
        }
        _append_jsonl(_VIOLATIONS_LOG, record)
        return 0

    # Fail-closed mode: emit journey event + block via JSON stdout.
    journey_record = {
        "entity_id": slug,
        "entity_type": "pipeline_slug",
        "event_type": "enforcement_blocked",
        "phase": phase,
        "violations": all_violations,
        "fail_closed": True,
        "timestamp": _now_iso(),
        "triggered_by": "enforcement_guard.py",
    }
    _append_jsonl(_ENFORCEMENT_JOURNEY, journey_record)

    stop_reason = (
        f"CHECKPOINT violation for slug '{slug}' (phase={phase}): {'; '.join(all_violations[:3])}"
    )
    # PreToolUse blocking: JSON to stdout, exit 0.
    print(json.dumps({"continue": False, "stopReason": stop_reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
