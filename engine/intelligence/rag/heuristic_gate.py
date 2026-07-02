"""
heuristic_gate.py -- Deterministic Heuristic Alignment Checker
===============================================================

Validates extracted insights against expert DNA L3 heuristics using
keyword/regex matching ONLY (zero LLM calls).

Architecture
------------
This is a SEPARATE module from ``qa_gates.py``.  The gate integration
works via an external function call::

    qa_gates.py  -->  heuristic_gate.check()  -->  returns warnings

The module loads L3 HEURISTICAS YAML files for a given expert, converts
each heuristic into keyword/regex pattern rules, and checks extracted
insights for contradictions.

Mode: WARN only -- never BLOCK on heuristic contradiction.

Constraints
~~~~~~~~~~~
- stdlib + PyYAML ONLY (no external deps, no LLM calls)
- Every function is DETERMINISTIC (reads files, matches patterns, returns dicts)
- Never crashes -- catches all exceptions, returns empty warning list

Version: 1.0.0
Date: 2026-03-25
Story: W3.1
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from engine.paths import KNOWLEDGE_EXTERNAL

logger = logging.getLogger("rag.heuristic_gate")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DNA_PERSONS_DIR: Path = KNOWLEDGE_EXTERNAL / "dna" / "persons"

# Negation patterns that invert the meaning of a keyword match.
# When a heuristic says "questions only" and the insight says
# "never use questions", the negation prefix flips the match.
_NEGATION_PREFIXES = re.compile(
    r"\b(?:never|don'?t|do\s+not|avoid|stop|quit|eliminate|"
    r"nunca|n[aã]o\s+(?:use|fa[cç]a|utilize)|"
    r"evite|pare\s+de|elimine)\b",
    re.IGNORECASE,
)

# Window size (in characters) around a keyword hit to check for negation.
_NEGATION_WINDOW = 80


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class HeuristicRule:
    """A single heuristic converted to keyword/regex patterns.

    Attributes:
        heuristic_id: Original ID from the DNA YAML (e.g., ``heu_001``).
        name: Short name of the heuristic.
        keywords: Lowercased keyword phrases extracted from the heuristic.
        contradiction_patterns: Compiled regexes that would indicate
            a contradiction (e.g., negation of the heuristic's keywords).
        source_expert: Expert slug this heuristic belongs to.
    """

    heuristic_id: str = ""
    name: str = ""
    keywords: list[str] = field(default_factory=list)
    contradiction_patterns: list[re.Pattern[str]] = field(default_factory=list)
    source_expert: str = ""


@dataclass
class HeuristicWarning:
    """A single warning produced by the heuristic gate.

    Attributes:
        heuristic_id: Which heuristic was contradicted.
        heuristic_name: Human-readable name of the heuristic.
        insight_text: The extracted insight text that triggered the warning.
        contradiction_type: Type of contradiction detected.
        matched_keyword: The specific keyword/pattern that matched.
        expert_slug: Expert this heuristic belongs to.
    """

    heuristic_id: str = ""
    heuristic_name: str = ""
    insight_text: str = ""
    contradiction_type: str = ""  # "negation", "absence", "keyword_conflict"
    matched_keyword: str = ""
    expert_slug: str = ""

    def to_dict(self) -> dict[str, str]:
        """Serialize to a plain dict for JSONL logging."""
        return {
            "heuristic_id": self.heuristic_id,
            "heuristic_name": self.heuristic_name,
            "insight_text": self.insight_text[:200],
            "contradiction_type": self.contradiction_type,
            "matched_keyword": self.matched_keyword,
            "expert_slug": self.expert_slug,
        }


# ---------------------------------------------------------------------------
# YAML Loading
# ---------------------------------------------------------------------------


def load_heuristics_yaml(slug: str) -> list[dict[str, Any]]:
    """Load L3 HEURISTICAS entries from the DNA YAML for a given expert.

    Handles multiple schema variants found across expert DNA files:
    - ``entries`` key (Hormozi, Cole)
    - ``heuristicas`` key (Pedro, Jeremy Miner)

    Args:
        slug: Expert slug (e.g., ``"alex-hormozi"``).

    Returns:
        List of raw heuristic entry dicts from the YAML.
        Empty list if file not found or unparseable.
    """
    heuristics_path = DNA_PERSONS_DIR / slug / "HEURISTICAS.yaml"

    if not heuristics_path.exists():
        logger.debug("No HEURISTICAS.yaml for '%s' at %s", slug, heuristics_path)
        return []

    try:
        with open(heuristics_path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception:
        logger.warning("Failed to parse HEURISTICAS.yaml for '%s'", slug, exc_info=True)
        return []

    if not isinstance(data, dict):
        return []

    # Try both schema variants
    entries = data.get("entries") or data.get("heuristicas") or []
    if not isinstance(entries, list):
        return []

    return entries


# ---------------------------------------------------------------------------
# Keyword Extraction
# ---------------------------------------------------------------------------


def _extract_keywords_from_entry(entry: dict[str, Any]) -> list[str]:
    """Extract meaningful keyword phrases from a heuristic entry.

    Combines text from name/titulo/nome, description/descricao, and
    quote/citacao fields. Extracts multi-word phrases that carry
    specific meaning (not stopwords).

    Args:
        entry: A single heuristic entry dict.

    Returns:
        List of lowercased keyword phrases (2+ words or significant singles).
    """
    # Collect text from all relevant fields across schema variants
    text_sources: list[str] = []

    for key in ("name", "titulo", "nome"):
        val = entry.get(key, "")
        if val:
            text_sources.append(str(val))

    for key in ("description", "descricao", "enunciado"):
        val = entry.get(key, "")
        if val:
            text_sources.append(str(val))

    for key in ("quote", "citacao"):
        val = entry.get(key, "")
        if val:
            text_sources.append(str(val))

    combined = " ".join(text_sources).lower()

    # Extract quoted phrases first (these are high-signal)
    quoted_phrases: list[str] = re.findall(r'"([^"]{4,60})"', combined)
    quoted_phrases.extend(re.findall(r"'([^']{4,60})'", combined))

    # Extract significant multi-word technical phrases
    # These patterns capture domain-specific concepts
    technical_phrases: list[str] = re.findall(
        r"\b(?:"
        r"\d+[%x]\s+\w+|"  # "70% proven", "3x growth"
        r"\d+[-–]\d+\s+\w+|"  # "7-12 seconds"
        r"\d+\s+(?:days?|hours?|min|seconds?|calls?|offers?|reps?)|"  # "30 days", "3 offers"
        r"(?:bottom|top)\s+\d+%|"  # "bottom 10%"
        r"(?:price|stall|decision\s+maker)|"  # objection types
        r"(?:leaderboard|pattern\s+interrupt|no-based\s+questions?)|"
        r"(?:booking\s+window|close\s+rate|show\s+rate)|"
        r"(?:questions?\s+only|split\s+payment|upfront\s+payment)|"
        r"(?:daily\s+training|spot\s+check|inbox\s+zero)"
        r")\b",
        combined,
    )

    keywords: list[str] = []

    for phrase in quoted_phrases:
        phrase = phrase.strip()
        if len(phrase) >= 4:
            keywords.append(phrase)

    for phrase in technical_phrases:
        phrase = phrase.strip()
        if phrase and phrase not in keywords:
            keywords.append(phrase)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)

    return unique


# ---------------------------------------------------------------------------
# Rule Building
# ---------------------------------------------------------------------------


def build_rules(slug: str) -> list[HeuristicRule]:
    """Load heuristics for an expert and convert to pattern-match rules.

    Args:
        slug: Expert slug (e.g., ``"alex-hormozi"``).

    Returns:
        List of ``HeuristicRule`` objects ready for matching.
    """
    entries = load_heuristics_yaml(slug)
    rules: list[HeuristicRule] = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        heu_id = str(entry.get("id", ""))
        name = str(entry.get("name", "") or entry.get("titulo", "") or entry.get("nome", ""))

        keywords = _extract_keywords_from_entry(entry)
        if not keywords:
            continue

        # Build contradiction patterns: for each keyword, a negation
        # preceding the keyword indicates contradiction
        contradiction_patterns: list[re.Pattern[str]] = []
        for kw in keywords:
            # Escape regex special chars in keyword
            escaped = re.escape(kw)
            # Pattern: negation word within ~80 chars before the keyword
            pattern = re.compile(
                r"(?:"
                + _NEGATION_PREFIXES.pattern
                + r")"
                + r".{0,"
                + str(_NEGATION_WINDOW)
                + r"}"
                + escaped,
                re.IGNORECASE | re.DOTALL,
            )
            contradiction_patterns.append(pattern)

        rules.append(
            HeuristicRule(
                heuristic_id=heu_id,
                name=name,
                keywords=keywords,
                contradiction_patterns=contradiction_patterns,
                source_expert=slug,
            )
        )

    return rules


# ---------------------------------------------------------------------------
# Contradiction Checking
# ---------------------------------------------------------------------------


def _check_insight_against_rule(
    insight_text: str,
    rule: HeuristicRule,
) -> list[HeuristicWarning]:
    """Check a single insight against a single heuristic rule.

    Two detection modes:
    1. **Negation**: The insight contains a keyword from the heuristic
       but preceded by a negation word (e.g., "never use questions"
       contradicts "questions only").
    2. **Keyword conflict**: The insight directly contradicts a
       quantitative heuristic (e.g., insight says "5 offers" when
       heuristic says "3 offers per day").

    Args:
        insight_text: The extracted insight text to check.
        rule: The heuristic rule to check against.

    Returns:
        List of warnings (usually 0 or 1).
    """
    warnings: list[HeuristicWarning] = []
    text_lower = insight_text.lower()

    # Mode 1: Negation detection
    for i, pattern in enumerate(rule.contradiction_patterns):
        match = pattern.search(text_lower)
        if match:
            keyword = rule.keywords[i] if i < len(rule.keywords) else "unknown"
            warnings.append(
                HeuristicWarning(
                    heuristic_id=rule.heuristic_id,
                    heuristic_name=rule.name,
                    insight_text=insight_text,
                    contradiction_type="negation",
                    matched_keyword=keyword,
                    expert_slug=rule.source_expert,
                )
            )
            # One warning per rule is enough (avoid flooding)
            break

    return warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check(
    insights: list[dict[str, Any]],
    expert_slug: str,
) -> list[HeuristicWarning]:
    """Check extracted insights against expert heuristics.

    This is the main public entry point, called by qa_gates.py as
    gate #8 (``content_heuristic_alignment``).

    Args:
        insights: List of insight dicts, each must have at least a
            ``"description"`` or ``"name"`` or ``"descricao"`` field
            containing the insight text.
        expert_slug: The expert whose heuristics to load and check against.

    Returns:
        List of ``HeuristicWarning`` objects. Empty list means no
        contradictions detected (or no heuristics available).
    """
    try:
        return _check_internal(insights, expert_slug)
    except Exception:
        logger.warning(
            "heuristic_gate.check() crashed for '%s'; returning empty",
            expert_slug,
            exc_info=True,
        )
        return []


def _check_internal(
    insights: list[dict[str, Any]],
    expert_slug: str,
) -> list[HeuristicWarning]:
    """Internal implementation (separated for clean error handling)."""
    if not insights or not expert_slug:
        return []

    rules = build_rules(expert_slug)
    if not rules:
        logger.debug("No heuristic rules built for '%s'", expert_slug)
        return []

    all_warnings: list[HeuristicWarning] = []

    for insight in insights:
        if not isinstance(insight, dict):
            continue

        # Extract insight text from various schema fields
        text = str(
            insight.get("description", "")
            or insight.get("descricao", "")
            or insight.get("name", "")
            or insight.get("titulo", "")
            or insight.get("nome", "")
        )
        if not text or len(text) < 10:
            continue

        for rule in rules:
            warnings = _check_insight_against_rule(text, rule)
            all_warnings.extend(warnings)

    return all_warnings


def check_from_file(
    insights_path: Path,
    expert_slug: str,
) -> list[HeuristicWarning]:
    """Load insights from INSIGHTS-STATE.json and check against heuristics.

    Convenience wrapper that reads the insights file and extracts the
    relevant person's insights before delegating to ``check()``.

    Args:
        insights_path: Path to INSIGHTS-STATE.json.
        expert_slug: Expert slug to check.

    Returns:
        List of warnings.
    """
    import json

    if not insights_path.exists():
        return []

    try:
        data = json.loads(insights_path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("Failed to parse %s", insights_path, exc_info=True)
        return []

    if not isinstance(data, dict):
        return []

    # Extract person insights (same logic as qa_gates._validate_step_5)
    person_insights: list[dict[str, Any]] = []
    persons = data.get("persons", {})
    if isinstance(persons, dict):
        slug_normalized = expert_slug.lower().replace("-", " ").replace("_", " ")
        for key, pdata in persons.items():
            key_normalized = key.lower().replace("-", " ").replace("_", " ")
            if slug_normalized in key_normalized or key_normalized in slug_normalized:
                if isinstance(pdata, dict):
                    person_insights = pdata.get("insights", [])
                break

    # Fallback: flat insights list
    if not person_insights:
        person_insights = data.get("insights", [])

    return check(person_insights, expert_slug)
