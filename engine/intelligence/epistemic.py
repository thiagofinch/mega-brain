"""epistemic.py — Helpers for EPISTEMIC PROTOCOL formato (Story MCE-3.12).

Two functions:
  - format_epistemic_response(facts, recommendation, hypothesis=None) -> str
  - validate_epistemic_response(text) -> dict {valid: bool, missing: [...], ...}

Reference rule: .claude/rules/epistemic-standards.md
Reference checklist: .claude/rules/epistemic-checklist.md
"""

from __future__ import annotations

import re
from typing import Any

# Markers that indicate a CRITICAL claim
CRITICAL_KEYWORDS = ("NUNCA", "SEMPRE", "MUST", "BLOCKER", "CRITICAL", "VETO", "REQUIRED")
MARKERS = ("FATOS", "RECOMENDACAO", "RECOMENDAÇÃO", "HIPOTESE", "HIPÓTESE", "[FONTE:")
FONTE_RE = re.compile(r"\[FONTE:[^\]]+\]")


def is_critical_claim(text: str) -> bool:
    """Return True if text contains any CRITICAL keyword."""
    if not text or not isinstance(text, str):
        return False
    upper = text.upper()
    return any(kw in upper for kw in CRITICAL_KEYWORDS)


def has_markers(text: str) -> bool:
    """Return True if text contains at least one EPISTEMIC marker."""
    if not text:
        return False
    return any(m in text for m in MARKERS)


def format_epistemic_response(
    facts: list[dict[str, str]],
    recommendation: dict[str, str] | None = None,
    hypothesis: dict[str, str] | None = None,
) -> str:
    """Render a response following the EPISTEMIC formato.

    Args:
        facts: list of {source: "path:line", quote: "..."} dicts.
        recommendation: dict with {position, justification, confidence, missing_evidence?}.
        hypothesis: dict with {hypothesis, validation_required, risk}.

    Returns:
        Formatted markdown response.
    """
    parts: list[str] = []

    # FATOS
    if facts:
        parts.append("## FATOS\n")
        for f in facts:
            src = f.get("source", "unknown")
            quote = f.get("quote", "").strip()
            parts.append(f"- [FONTE:{src}]")
            if quote:
                parts.append(f'  > "{quote}"')
        parts.append("")

    # RECOMENDAÇÃO
    if recommendation:
        parts.append("## RECOMENDAÇÃO\n")
        parts.append(f"**Posição:** {recommendation.get('position', '')}")
        parts.append(f"**Justificativa:** {recommendation.get('justification', '')}")
        parts.append(f"**Confiança:** {recommendation.get('confidence', 'MEDIA').upper()}")
        if recommendation.get("missing_evidence"):
            parts.append(f"**Missing evidence:** {recommendation['missing_evidence']}")
        parts.append("")

    # HIPÓTESE
    if hypothesis:
        parts.append("## HIPÓTESE\n")
        parts.append(f"**Hipótese:** {hypothesis.get('hypothesis', '')}")
        parts.append(f"**Validação requerida:** {hypothesis.get('validation_required', '')}")
        parts.append(f"**Risco se errada:** {hypothesis.get('risk', '')}")
        parts.append("")

    return "\n".join(parts).strip() + "\n"


def validate_epistemic_response(text: str) -> dict[str, Any]:
    """Validate that a response with CRITICAL claims follows the formato.

    Returns:
        dict {
          valid: bool,
          is_critical: bool,
          has_markers: bool,
          fatos_count: int,
          fontes_count: int,
          missing: list[str],  # list of issues
        }
    """
    result: dict[str, Any] = {
        "valid": True,
        "is_critical": False,
        "has_markers": False,
        "fatos_count": 0,
        "fontes_count": 0,
        "missing": [],
    }

    if not text or not isinstance(text, str):
        result["valid"] = True  # empty is not invalid
        return result

    result["is_critical"] = is_critical_claim(text)
    result["has_markers"] = has_markers(text)
    result["fatos_count"] = text.count("## FATOS") + text.count("##FATOS")
    result["fontes_count"] = len(FONTE_RE.findall(text))

    if result["is_critical"] and not result["has_markers"]:
        result["valid"] = False
        result["missing"].append("missing_critical_marker")

    if result["has_markers"] and "## FATOS" in text and result["fontes_count"] == 0:
        result["valid"] = False
        result["missing"].append("fatos_section_without_fonte_citation")

    return result
