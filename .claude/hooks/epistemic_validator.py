#!/usr/bin/env python3
"""epistemic_validator.py — PostToolUse soft-warn hook (Story MCE-3.12).

When agent output contains a CRITICAL claim without FATO/RECOMENDACAO/HIPOTESE
markers, log a warning to .data/logs/epistemic-violations.jsonl.

V1 = soft warn (never blocks). V2 future = hard block on push if violations
exceed threshold.

Exit codes:
  0 = OK or warning logged (never blocks)
  Never exits 1 or 2 in V1.

Env var to disable: MCE_EPISTEMIC_VALIDATOR_DISABLED=1
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

LOG_PATH = Path(".data/logs/epistemic-violations.jsonl")

# Inline definitions (duplicated from engine.intelligence.epistemic to avoid
# import errors when hook runs in a thin Python env).
CRITICAL_KEYWORDS = ("NUNCA", "SEMPRE", "MUST", "BLOCKER", "CRITICAL", "VETO", "REQUIRED")
MARKERS = ("FATOS", "RECOMENDACAO", "RECOMENDAÇÃO", "HIPOTESE", "HIPÓTESE", "[FONTE:")


def is_critical_claim(text: str) -> bool:
    if not text:
        return False
    upper = text.upper()
    return any(kw in upper for kw in CRITICAL_KEYWORDS)


def has_markers(text: str) -> bool:
    if not text:
        return False
    return any(m in text for m in MARKERS)


def log_violation(payload: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> int:
    if os.environ.get("MCE_EPISTEMIC_VALIDATOR_DISABLED"):
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # No JSON payload — not our concern, exit clean.
        return 0

    # Extract output text from payload (Claude Code PostToolUse shape)
    output_text = ""
    if isinstance(payload, dict):
        # Multiple possible shapes — try common keys defensively
        output_text = (
            payload.get("output")
            or payload.get("text")
            or payload.get("response")
            or payload.get("content")
            or ""
        )
        if not isinstance(output_text, str):
            output_text = str(output_text)

    if not output_text:
        return 0

    if is_critical_claim(output_text) and not has_markers(output_text):
        log_violation(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "violation": "critical_claim_without_marker",
                "agent": payload.get("agent", "unknown")
                if isinstance(payload, dict)
                else "unknown",
                "tool": payload.get("tool", "unknown") if isinstance(payload, dict) else "unknown",
                "preview": output_text[:300],
            }
        )

    return 0  # never blocks in V1


if __name__ == "__main__":
    sys.exit(main())
