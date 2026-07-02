#!/usr/bin/env python3
"""deliberation_convergence.py — PostToolUse hook (DELIBERATION-GATE-1.0).

Observes Write/Edit tool calls that update `.claude/deliberation-state.yaml`
AFTER tribunal completion (detected by tribunal_summary field being populated).

Computes disagreement_rate(conclave, tribunal) and decides:
  - disagreement_rate < ε=0.05  → SYNTHESIZE (proceed to sintetizador expanded mode)
  - disagreement_rate >= ε=0.05 → ESCALATE human (NOT round 3 — anti-pattern A2)

Design:
  - NEVER returns {"continue": false} (A6: graceful degradation)
  - Always exits 0
  - Logs to .logs/deliberation/{YYYY-MM-DD}.jsonl (AC9)
  - stdlib + PyYAML only

AC traceability:
  AC5  — disagreement_rate < ε=0.05 → synthesize; >= ε → escalate
  AC9  — logs disagreement_rate + verdict to .logs/deliberation/
  A2   — escalate (NOT round 3) when divergent
  A6   — graceful degradation on any failure

Story: DELIBERATION-GATE-1.0
Hook event: PostToolUse
Matcher: Write|Edit (filter: deliberation-state.yaml with tribunal_summary present)
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
_LOG_DIR = _ROOT / ".logs" / "deliberation"

# Convergence threshold (AC5: ε=0.05)
_EPSILON = 0.05


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
        entry: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "hook": "deliberation_convergence",
            **event,
        }
        with _today_log_path().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # logging failure must never propagate (A6)


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def _load_state() -> dict[str, Any] | None:
    """Load and parse deliberation-state.yaml. Returns None on any failure."""
    if not _YAML_AVAILABLE or not _STATE_FILE.exists():
        return None
    try:
        raw = _STATE_FILE.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _update_state_fields(updates: dict[str, Any]) -> None:
    """Write multiple flat fields into deliberation-state.yaml. Silently no-ops on failure."""
    if not _YAML_AVAILABLE or not _STATE_FILE.exists():
        return
    try:
        raw = _STATE_FILE.read_text(encoding="utf-8")
        data: dict[str, Any] = yaml.safe_load(raw) or {}
        data.update(updates)
        _STATE_FILE.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    except Exception:
        pass  # state update failure must never propagate (A6)


# ---------------------------------------------------------------------------
# Disagreement rate computation (AC5)
# ---------------------------------------------------------------------------

def _compute_disagreement_rate(state: dict[str, Any]) -> float:
    """Compute disagreement_rate from tribunal_summary lexical signals.

    # Disagreement detection by lexical signals from tribunal-chief protocol.
    # Source: squads/tribunal/agents/tribunal-chief.md — closing protocol writes
    # explicit corrobora/contradiz tokens in tribunal_summary. Hook reads contract.
    # Article IV: NOT invention — reading documented protocol output.

    Returns:
      0.02  — convergence tokens detected (corrobora / alinha / confirma / ...)
      0.10  — divergence tokens detected (contradiz / diverge / risco catastrofico / ...)
      0.10  — BOTH sets matched (pathological case: tribunal-chief mal-formado; precaution)
      0.02  — no tokens detected (default conservador, favorece síntese — A6, H5)

    Threshold ε=0.05: values below → SYNTHESIZE; values at/above → ESCALATE human.
    """
    tribunal_summary: str = str(state.get("tribunal_summary", "") or "").lower()

    if not tribunal_summary:
        return 0.02  # default conservador (H5)

    _CONVERGENCE_TOKENS = (
        "corrobora", "alinha", "confirma", "endorses", "concorda",
    )
    _DIVERGENCE_TOKENS = (
        "contradiz", "diverge", "risco catastrofico", "rejeita", "discorda",
    )

    has_convergence = any(tok in tribunal_summary for tok in _CONVERGENCE_TOKENS)
    has_divergence = any(tok in tribunal_summary for tok in _DIVERGENCE_TOKENS)

    if has_divergence and has_convergence:
        # Pathological: tribunal-chief mal-formado — precaution, escalate
        return 0.10

    if has_divergence:
        return 0.10

    if has_convergence:
        return 0.02

    # No signal detected — default conservador (H5)
    return 0.02


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
            return 0

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
            return 0

        # Guard: only run after tribunal has completed (tribunal_summary present)
        tribunal_summary: str = str(state.get("tribunal_summary", "") or "")
        if not tribunal_summary:
            return 0  # tribunal not yet done — nothing to check

        # Guard: only run when gate_status=triggered (tribunal was invoked by gate)
        gate_status: str = str(state.get("gate_status", ""))
        if gate_status != "triggered":
            return 0  # not a gate-triggered session

        # Guard: avoid double-processing (disagreement_rate already computed)
        if state.get("disagreement_rate") is not None:
            return 0

        query_id: str = str(state.get("query_id", "unknown"))
        round1_confidence: int = int(state.get("round1_confidence", 0))

        # Compute disagreement_rate (AC5)
        disagreement_rate = _compute_disagreement_rate(state)

        if disagreement_rate < _EPSILON:
            # Converged → proceed to synthesis (AC5: synthesize path)
            _update_state_fields({
                "disagreement_rate": disagreement_rate,
                "gate_status": "triggered",  # keep triggered; sintetizador reads tribunal_summary
                "timestamps.synthesis_start": datetime.now(UTC).isoformat(),
            })
            _log_event({
                "status": "convergence_synthesize",
                "query_id": query_id,
                "round1_confidence": round1_confidence,
                "disagreement_rate": disagreement_rate,
                "epsilon": _EPSILON,
                "verdict": "SYNTHESIZE",
                "tribunal_triggered": True,
            })

        else:
            # Diverged → escalate human (AC5: NOT round 3 — anti-pattern A2)
            _update_state_fields({
                "disagreement_rate": disagreement_rate,
                "gate_status": "escalated",
                "escalation_reason": "convergence_failure",
            })
            _log_event({
                "status": "convergence_escalate",
                "query_id": query_id,
                "round1_confidence": round1_confidence,
                "disagreement_rate": disagreement_rate,
                "epsilon": _EPSILON,
                "verdict": "ESCALATE_HUMAN",
                "tribunal_triggered": True,
                "note": "disagreement_rate >= epsilon; NOT round 3 (anti-pattern A2)",
            })

    except Exception:
        # Catch-all: hook failure MUST NOT block Claude Code (A6)
        _log_event({"status": "hook_error", "reason": "unhandled_exception"})

    return 0  # always exit 0 (A6)


if __name__ == "__main__":
    sys.exit(main())
