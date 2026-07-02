#!/usr/bin/env python3
"""deliberation_gate.py — PostToolUse hook (DELIBERATION-GATE-1.0).

Observes Write/Edit tool calls that produce `.claude/deliberation-state.yaml`.
Reads the state file, evaluates the confidence gate, and either:
  - Triggers /tribunal PESADA (AC1: confidence ∈ [60, 80))
  - Skips with log entry (AC3: >= 80 high_confidence)
  - Escalates to human (AC4: < 60 low_confidence)
  - Blocks tribunal if ceiling reached (AC2: round_count >= 2)
  - Blocks tribunal if token budget exceeded (AC2a: cost_tokens.conclave > budget_cap)

Design:
  - NEVER returns {"continue": false} (A6: graceful degradation)
  - Always exits 0 — hook is an OBSERVER + TRIGGER, not a gatekeeper
  - Logs every evaluation to .logs/deliberation/{YYYY-MM-DD}.jsonl (AC9)
  - stdlib + PyYAML only (no external deps beyond project standard)
  - Timeout budget: 15s (gate + subprocess detach, not waiting for tribunal)

AC traceability:
  AC1  — _gate_evaluate() → "triggered"
  AC2  — round_count >= 2 check → skip_reason=ceiling_reached
  AC2a — cost_tokens.conclave > budget_cap check → skip_reason=budget_exceeded
  AC3  — confidence >= 80 → skip_reason=high_confidence
  AC4  — confidence < 60 → escalation_reason=low_confidence
  AC8  — user_overrides.no_tribunal / force_tribunal / tribunal_mode
  AC9  — _log_event() appends to .logs/deliberation/{date}.jsonl

Story: DELIBERATION-GATE-1.0
Hook event: PostToolUse
Matcher: Write|Edit (filter: deliberation-state.yaml)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Optional PyYAML — graceful fallback if unavailable (A6)
# ---------------------------------------------------------------------------
try:
    import yaml  # type: ignore[import-untyped]

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parent.parent.parent))
_STATE_FILE = _ROOT / ".claude" / "deliberation-state.yaml"
_SETTINGS_FILE = _ROOT / ".claude" / "settings.json"
_LOG_DIR = _ROOT / ".logs" / "deliberation"
_SCHEMA_FILE = _ROOT / ".claude" / "schemas" / "deliberation-state.schema.yaml"

# Default budget cap (AC2a) — overridable via settings.json:deliberation_gate.budget_cap
_DEFAULT_BUDGET_CAP = 25_000

# Confidence thresholds (matching sintetizador-conclave.md:113-119)
_THRESHOLD_HIGH = 80   # >= 80: skip (AC3)
_THRESHOLD_LOW = 60    # < 60: escalate (AC4)
# ∈ [60, 80) → trigger (AC1)

# Hard ceiling: max rounds per query (AC2)
_MAX_ROUNDS = 2


# ---------------------------------------------------------------------------
# Log helpers (AC9)
# ---------------------------------------------------------------------------

def _today_log_path() -> Path:
    """Return .logs/deliberation/YYYY-MM-DD.jsonl path."""
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    return _LOG_DIR / f"{date_str}.jsonl"


def _log_event(event: dict[str, Any]) -> None:
    """Append one JSON line to today's deliberation log. Never raises."""
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = _today_log_path()
        entry: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "hook": "deliberation_gate",
            **event,
        }
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # logging failure must never propagate (A6)


# ---------------------------------------------------------------------------
# Settings reader
# ---------------------------------------------------------------------------

def _read_budget_cap() -> int:
    """Read deliberation_gate.budget_cap from settings.json. Falls back to default."""
    try:
        raw = _SETTINGS_FILE.read_text(encoding="utf-8")
        data: dict[str, Any] = json.loads(raw)
        cap = data.get("deliberation_gate", {}).get("budget_cap", _DEFAULT_BUDGET_CAP)
        return int(cap)
    except Exception:
        return _DEFAULT_BUDGET_CAP


# ---------------------------------------------------------------------------
# State file reader
# ---------------------------------------------------------------------------

def _load_state() -> dict[str, Any] | None:
    """Load and parse deliberation-state.yaml. Returns None on any failure."""
    if not _YAML_AVAILABLE:
        _log_event({"status": "skipped", "reason": "yaml_unavailable"})
        return None
    if not _STATE_FILE.exists():
        return None
    try:
        raw = _STATE_FILE.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            _log_event({"status": "error", "reason": "state_not_dict"})
            return None
        return data
    except Exception as exc:
        _log_event({"status": "error", "reason": "yaml_parse_error", "detail": str(exc)})
        return None


# ---------------------------------------------------------------------------
# Gate evaluation (core logic)
# ---------------------------------------------------------------------------

def _gate_evaluate(state: dict[str, Any], budget_cap: int) -> tuple[str, dict[str, Any]]:
    """Evaluate gate conditions. Returns (verdict, context_dict).

    Verdict values:
      "trigger"  — invoke /tribunal (AC1)
      "skip"     — high_confidence, ceiling_reached, budget_exceeded, user_no_tribunal (AC2/AC2a/AC3/AC8)
      "escalate" — low_confidence (AC4) or force path not matching trigger window
    """
    query_id: str = str(state.get("query_id", "unknown"))
    confidence: int = int(state.get("round1_confidence", 0))
    round_count: int = int(state.get("round_count", 1))
    tribunal_recommended: bool = bool(state.get("tribunal_recommended", False))

    cost_tokens: dict[str, Any] = state.get("cost_tokens", {})
    conclave_tokens: int = int(cost_tokens.get("conclave", 0))

    overrides: dict[str, Any] = state.get("user_overrides", {})
    no_tribunal: bool = bool(overrides.get("no_tribunal", False))
    force_tribunal: bool = bool(overrides.get("force_tribunal", False))
    tribunal_mode: str = str(overrides.get("tribunal_mode", "PESADA"))

    ctx: dict[str, Any] = {
        "query_id": query_id,
        "round1_confidence": confidence,
        "round_count": round_count,
        "cost_tokens_conclave": conclave_tokens,
        "budget_cap": budget_cap,
        "tribunal_mode": tribunal_mode,
    }

    # AC8: --no-tribunal override (highest priority skip)
    if no_tribunal:
        ctx["skip_reason"] = "user_override_no_tribunal"
        return "skip", ctx

    # AC2: hard ceiling — never trigger if already ran tribunal
    if round_count >= _MAX_ROUNDS:
        ctx["skip_reason"] = "ceiling_reached"
        ctx["warning"] = f"tribunal already ran (round_count={round_count}); ceiling={_MAX_ROUNDS}"
        return "skip", ctx

    # AC2a: token budget check — cancel before evaluating confidence
    if conclave_tokens > budget_cap:
        ctx["skip_reason"] = "budget_exceeded"
        ctx["cost_tokens_conclave"] = conclave_tokens
        ctx["budget_cap"] = budget_cap
        return "skip", ctx

    # AC8: --force-tribunal override (bypasses confidence window)
    if force_tribunal:
        ctx["tribunal_recommended"] = True
        ctx["force_override"] = True
        return "trigger", ctx

    # AC4: low confidence → escalate human
    if confidence < _THRESHOLD_LOW:
        ctx["escalation_reason"] = "low_confidence"
        return "escalate", ctx

    # AC3: high confidence → skip (emit direct)
    if confidence >= _THRESHOLD_HIGH:
        ctx["skip_reason"] = "high_confidence"
        return "skip", ctx

    # AC1: confidence ∈ [60, 80) → trigger tribunal
    # Also honour sintetizador's explicit tribunal_recommended flag
    if _THRESHOLD_LOW <= confidence < _THRESHOLD_HIGH:
        ctx["tribunal_recommended"] = tribunal_recommended
        return "trigger", ctx

    # Fallback (should not reach here given integer confidence)
    ctx["skip_reason"] = "confidence_out_of_range"
    return "skip", ctx


# ---------------------------------------------------------------------------
# Tribunal trigger (AC1)
# ---------------------------------------------------------------------------

def _trigger_tribunal(state: dict[str, Any], ctx: dict[str, Any]) -> None:
    """Detach /tribunal invocation as background subprocess. Does not block.

    Passes only the restricted summary to tribunal (AC6: sycophancy mitigation):
      decision + thesis + reasoning_paragraph + round1_confidence
    Does NOT pass individual agent arguments.
    """
    tribunal_mode = ctx.get("tribunal_mode", "PESADA")
    decision = str(state.get("decision", ""))
    thesis = str(state.get("thesis", ""))
    reasoning = str(state.get("reasoning_paragraph", ""))
    confidence = ctx.get("round1_confidence", 0)

    # Build restricted summary (AC6) — this is ALL tribunal sees of round 1
    restricted_summary = (
        f"[TRIBUNAL INPUT — from deliberation gate, DELIBERATION-GATE-1.0]\n"
        f"Mode: {tribunal_mode}\n"
        f"Round1 confidence: {confidence}%\n"
        f"Decision: {decision}\n"
        f"Thesis: {thesis}\n"
        f"Reasoning: {reasoning}\n"
        f"[NOTE: Individual agent arguments intentionally omitted — sycophancy mitigation AC6]"
    )

    # Write trigger file for tribunal-chief to detect (mirrors .advance-trigger.json pattern)
    trigger_path = _ROOT / ".claude" / "tribunal-trigger.json"
    trigger_payload: dict[str, Any] = {
        "triggered_by": "deliberation_gate",
        "query_id": ctx.get("query_id", "unknown"),
        "tribunal_mode": tribunal_mode,
        "round1_confidence": confidence,
        "restricted_summary": restricted_summary,
        "triggered_at": datetime.now(UTC).isoformat(),
        "story": "DELIBERATION-GATE-1.0",
    }
    try:
        trigger_path.write_text(
            json.dumps(trigger_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        _log_event({
            "status": "trigger_write_failed",
            "query_id": ctx.get("query_id"),
            "detail": str(exc),
        })
        return

    # Update state file: gate_status=triggered, round_count incremented
    _update_state_field("gate_status", "triggered")
    _update_state_field("round_count", 2)
    _update_state_field("timestamps.tribunal_start", datetime.now(UTC).isoformat())

    _log_event({
        "status": "tribunal_triggered",
        "query_id": ctx.get("query_id"),
        "round1_confidence": confidence,
        "tribunal_triggered": True,
        "tribunal_mode": tribunal_mode,
        "cost_tokens": {"conclave": ctx.get("cost_tokens_conclave", 0)},
    })


# ---------------------------------------------------------------------------
# State file field updater
# ---------------------------------------------------------------------------

def _update_state_field(field: str, value: Any) -> None:
    """Update a single field in deliberation-state.yaml. Silently no-ops on failure."""
    if not _YAML_AVAILABLE or not _STATE_FILE.exists():
        return
    try:
        raw = _STATE_FILE.read_text(encoding="utf-8")
        data: dict[str, Any] = yaml.safe_load(raw) or {}

        if "." in field:
            # Nested field (e.g. "timestamps.tribunal_start")
            parts = field.split(".", 1)
            sub = data.setdefault(parts[0], {})
            if isinstance(sub, dict):
                sub[parts[1]] = value
        else:
            data[field] = value

        _STATE_FILE.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    except Exception:
        pass  # state update failure must never propagate (A6)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Entry point. Always returns 0 (A6: graceful degradation)."""
    try:
        # Read PostToolUse stdin payload
        try:
            payload: dict[str, Any] = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            return 0  # no payload — not our trigger

        # Filter: only act when deliberation-state.yaml was written/edited
        file_path: str = str(
            payload.get("tool_input", {}).get("file_path", "")
            or payload.get("file_path", "")
            or ""
        )
        if "deliberation-state.yaml" not in file_path:
            return 0

        # Load state
        state = _load_state()
        if state is None:
            _log_event({"status": "skipped", "reason": "state_file_missing_or_invalid"})
            return 0

        # Read config
        budget_cap = _read_budget_cap()

        # Evaluate gate
        verdict, ctx = _gate_evaluate(state, budget_cap)

        if verdict == "trigger":
            _trigger_tribunal(state, ctx)
            # tribunal_triggered log emitted inside _trigger_tribunal

        elif verdict == "skip":
            skip_reason = ctx.get("skip_reason", "unknown")
            _update_state_field("gate_status", "skipped")
            _update_state_field("skip_reason", skip_reason)

            log_entry: dict[str, Any] = {
                "status": "skip",
                "query_id": ctx.get("query_id"),
                "round1_confidence": ctx.get("round1_confidence"),
                "skip_reason": skip_reason,
                "tribunal_triggered": False,
            }
            if skip_reason == "ceiling_reached":
                log_entry["warning"] = ctx.get("warning", "")
            if skip_reason == "budget_exceeded":
                log_entry["cost_tokens_conclave"] = ctx.get("cost_tokens_conclave")
                log_entry["budget_cap"] = budget_cap
            _log_event(log_entry)

        elif verdict == "escalate":
            escalation_reason = ctx.get("escalation_reason", "low_confidence")
            _update_state_field("gate_status", "escalated")
            _update_state_field("escalation_reason", escalation_reason)
            _log_event({
                "status": "escalate",
                "query_id": ctx.get("query_id"),
                "round1_confidence": ctx.get("round1_confidence"),
                "escalation_reason": escalation_reason,
                "tribunal_triggered": False,
            })

    except Exception:
        # Catch-all: hook failure MUST NOT block Claude Code (A6)
        _log_event({"status": "hook_error", "reason": "unhandled_exception"})

    return 0  # always exit 0 (A6)


if __name__ == "__main__":
    sys.exit(main())
