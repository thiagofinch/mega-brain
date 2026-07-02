#!/usr/bin/env python3
"""
RELEVANCE SCORER - Deterministic chunk relevance scoring
==========================================================
Score each chunk against its source topic/expert domain using pure
Python heuristics. No LLM calls.

Scoring signals (each contributes 0.0-1.0, then averaged):
  1. keyword_density  — domain-relevant terms vs total tokens
  2. section_signal   — heading/section type bonus (frameworks > filler)
  3. filler_penalty   — penalize chunks that are mostly filler/boilerplate
  4. length_signal    — very short chunks are less useful

Configurable threshold (default: 0.3). Chunks below threshold are stored
but flagged for query-time exclusion.

Version: 1.0.0
Date: 2026-03-25
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DEFAULT_RELEVANCE_THRESHOLD = 0.3

# High-value section names (case-insensitive partial match)
_HIGH_VALUE_SECTIONS = {
    "framework",
    "frameworks",
    "heuristic",
    "heuristicas",
    "heuristics",
    "model",
    "modelos",
    "models",
    "metodologia",
    "metodologias",
    "methodology",
    "filosofia",
    "filosofias",
    "philosophy",
    "strategy",
    "estrategia",
    "principle",
    "principio",
    "decision",
    "decisao",
    "insight",
    "playbook",
    "dna",
    "soul",
    "cognitive",
}

# Low-value / filler section names
_LOW_VALUE_SECTIONS = {
    "changelog",
    "references",
    "credits",
    "license",
    "acknowledgment",
    "table of contents",
    "toc",
    "index",
    "metadata",
    "config",
    "version",
    "appendix",
}

# Filler patterns (boilerplate, timestamps, navigation, etc.)
_FILLER_PATTERNS = [
    re.compile(r"^[-=_*]{3,}$", re.MULTILINE),  # separators
    re.compile(r"^\s*\|.*\|.*\|\s*$", re.MULTILINE),  # table formatting
    re.compile(r"^\s*#{1,6}\s*$", re.MULTILINE),  # empty headers
    re.compile(r"https?://\S+"),  # bare URLs
    re.compile(r"^\s*-\s*$", re.MULTILINE),  # empty bullets
]

# Domain-specific keyword banks (person/domain -> relevant terms)
_DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "sales": {
        "offer",
        "close",
        "commission",
        "objection",
        "pipeline",
        "lead",
        "prospect",
        "deal",
        "revenue",
        "conversion",
        "upsell",
        "pricing",
        "discount",
        "negotiation",
        "value",
        "equation",
        "guarantee",
    },
    "marketing": {
        "campaign",
        "funnel",
        "copy",
        "headline",
        "ctr",
        "conversion",
        "audience",
        "targeting",
        "creative",
        "brand",
        "content",
        "ads",
        "traffic",
        "landing",
        "page",
        "email",
        "sequence",
    },
    "engineering": {
        "architecture",
        "code",
        "deploy",
        "pipeline",
        "test",
        "api",
        "database",
        "schema",
        "index",
        "query",
        "performance",
        "debug",
        "refactor",
        "module",
        "service",
        "function",
        "class",
    },
    "management": {
        "team",
        "hire",
        "fire",
        "culture",
        "kpi",
        "okr",
        "meeting",
        "decision",
        "strategy",
        "leadership",
        "delegation",
        "accountability",
        "performance",
        "review",
        "feedback",
        "onboarding",
    },
}


# ---------------------------------------------------------------------------
# SCORING FUNCTIONS
# ---------------------------------------------------------------------------
def _tokenize_simple(text: str) -> list[str]:
    """Lowercase alpha tokens >= 3 chars."""
    return re.findall(r"[a-z\u00e0-\u024f]{3,}", text.lower())


def _keyword_density_score(tokens: list[str], domain: str) -> float:
    """Score based on domain-relevant keyword density."""
    if not tokens:
        return 0.0

    # Collect relevant keywords from domain + generic high-value terms
    keywords = set()
    domain_lower = domain.lower()
    for key, terms in _DOMAIN_KEYWORDS.items():
        if key in domain_lower or domain_lower in key:
            keywords.update(terms)

    # If no domain match, use a generic baseline (no penalty, but no bonus)
    if not keywords:
        return 0.5

    matches = sum(1 for t in tokens if t in keywords)
    density = matches / len(tokens)
    # Scale: 0% = 0.2, 5% = 0.5, 15%+ = 1.0
    return min(1.0, 0.2 + density * 5.3)


def _section_signal_score(section: str) -> float:
    """Score based on section name quality."""
    if not section:
        return 0.5  # No section info = neutral

    section_lower = section.lower()

    for high in _HIGH_VALUE_SECTIONS:
        if high in section_lower:
            return 1.0

    for low in _LOW_VALUE_SECTIONS:
        if low in section_lower:
            return 0.1

    return 0.5  # Unknown section = neutral


def _filler_penalty_score(text: str) -> float:
    """Penalize chunks that are mostly filler/boilerplate."""
    if not text:
        return 0.0

    total_len = len(text)
    filler_chars = 0

    for pattern in _FILLER_PATTERNS:
        for match in pattern.finditer(text):
            filler_chars += len(match.group())

    filler_ratio = filler_chars / total_len
    # Low filler = high score, high filler = low score
    return max(0.0, 1.0 - filler_ratio * 2.0)


def _length_signal_score(text: str) -> float:
    """Score based on text length -- very short chunks are less useful."""
    length = len(text.strip())
    if length < 50:
        return 0.1
    if length < 150:
        return 0.4
    if length < 300:
        return 0.7
    return 1.0


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------
def score_chunk(text: str, domain: str = "", section: str = "") -> float:
    """Score a single chunk's relevance. Returns 0.0-1.0.

    Args:
        text: The chunk text.
        domain: The domain/topic of the source (e.g., "sales").
        section: The section name within the document.

    Returns:
        Float between 0.0 and 1.0.
    """
    tokens = _tokenize_simple(text)

    keyword_score = _keyword_density_score(tokens, domain)
    section_score = _section_signal_score(section)
    filler_score = _filler_penalty_score(text)
    length_score = _length_signal_score(text)

    # Weighted average: filler and length are sanity checks,
    # keyword and section carry more signal
    weighted = (
        keyword_score * 0.35 + section_score * 0.30 + filler_score * 0.20 + length_score * 0.15
    )

    return round(min(1.0, max(0.0, weighted)), 4)


def score_chunks(chunks: list) -> None:
    """Score all chunks in-place, setting relevance_score on each.

    Args:
        chunks: List of Chunk objects (modified in-place).
    """
    for chunk in chunks:
        if chunk.relevance_score is None:
            chunk.relevance_score = score_chunk(
                chunk.text,
                domain=chunk.domain,
                section=chunk.section,
            )
