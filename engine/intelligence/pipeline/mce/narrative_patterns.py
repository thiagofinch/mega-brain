"""
narrative_patterns.py — Pattern detection and consensus analysis for NARRATIVES-STATE
=====================================================================================

Implements two public functions:

  - detect_patterns(insights, threshold=4) -> list[dict]
      Groups insights by tag. When a tag has >= threshold occurrences it is
      declared a pattern. Returns sorted by occurrence_count descending.
      Capped at MAX_PATTERNS_PER_EXPERT to avoid unbounded growth.

  - detect_consensus(slugs_dict, high_confidence_threshold=0.8) -> list[dict]
      Receives a mapping of slug -> insight list (already loaded by caller).
      For each tag, checks if 2+ distinct slugs have high-confidence insights.
      Returns consensus entries where at least 2 experts converge.

  - merge_patterns_incremental(existing, incoming) -> list[dict]
      Merges incoming patterns into existing list. Increments occurrence_count
      on match, adds new entry otherwise. Respects MAX_PATTERNS_PER_EXPERT cap.

  - merge_consensus_incremental(existing, incoming) -> list[dict]
      Merges incoming consensus into existing list. Adds new experts to
      existing topic entry. Deduplicates by topic.

Stack: stdlib only. Zero LLM. Zero external dependencies.
Story: MCE-11.15 — patterns_identified + consensus_points in NARRATIVES-STATE.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

__all__ = [
    "detect_consensus",
    "detect_patterns",
    "merge_consensus_incremental",
    "merge_patterns_incremental",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum occurrences for a tag to be declared a pattern (AC2).
_DEFAULT_THRESHOLD: int = 4

# Hard cap: keep only top N patterns per expert (Risk #3 mitigation).
MAX_PATTERNS_PER_EXPERT: int = 20

# Confidence strings considered "high" for consensus detection (AC3).
_HIGH_CONFIDENCE_STRINGS: frozenset[str] = frozenset({"HIGH", "high", "ALTA", "alta"})

# Minimum numeric confidence for consensus (e.g. when stored as float 0.0-1.0).
_HIGH_CONFIDENCE_NUMERIC: float = 0.8


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(tz=UTC).isoformat()


def _normalize_tag(raw_tag: str) -> str:
    """Strip brackets and normalise case for grouping.

    Examples:
        "[HEURISTICA]" -> "HEURISTICA"
        "HEURISTIC"    -> "HEURISTIC"
        "[FILOSOFIA]"  -> "FILOSOFIA"
    """
    cleaned = raw_tag.strip()
    # Remove surrounding brackets: [TAG] -> TAG
    cleaned = re.sub(r"^\[|\]$", "", cleaned)
    return cleaned.strip().upper()


def _extract_tag(insight: dict[str, Any]) -> str:
    """Return the canonical tag for *insight*.

    Prefer ``tag`` field (e.g. ``[HEURISTICA]``), fall back to ``dna_tag``
    (e.g. ``HEURISTIC``), then ``UNKNOWN``.
    """
    raw = insight.get("tag") or insight.get("dna_tag") or "UNKNOWN"
    return _normalize_tag(str(raw))


def _confidence_is_high(confidence: Any) -> bool:
    """Return True if *confidence* represents a high-confidence value.

    Accepts:
      - Strings: "HIGH", "ALTA", "high", etc.
      - Floats / ints: >= 0.8
    """
    if isinstance(confidence, str):
        return confidence.strip() in _HIGH_CONFIDENCE_STRINGS
    if isinstance(confidence, int | float):
        return float(confidence) >= _HIGH_CONFIDENCE_NUMERIC
    return False


def _derive_pattern_name(tag: str, first_insight: dict[str, Any]) -> str:
    """Derive a human-readable pattern name from tag + first insight context.

    Uses the first 60 characters of the insight text as a name hint. If the
    insight text is not available, falls back to "{tag} pattern".

    Args:
        tag:           Normalized tag string (e.g. "HEURISTICA").
        first_insight: First insight dict in the tag group.

    Returns:
        Human-readable pattern name string.
    """
    insight_text: str = str(first_insight.get("insight") or first_insight.get("text") or "").strip()
    if insight_text:
        # Truncate at first sentence break or 60 chars
        truncated = insight_text[:60]
        # Cut at sentence boundary if present within 60 chars
        for sep in (".", "!", "?", ";"):
            idx = insight_text.find(sep)
            if 0 < idx < 60:
                truncated = insight_text[:idx]
                break
        return f"{tag}: {truncated}"
    return f"{tag} pattern"


def _compute_adaptive_threshold(insights: list[dict[str, Any]], base: int) -> int:
    """Compute threshold with corpus-size guard (Risk #1 mitigation).

    For small corpora (< 20 insights), the threshold is adjusted proportionally:
        threshold = max(base, ceil(len(insights) * 0.15))

    This prevents a 10-insight corpus from declaring everything a pattern at
    threshold=4.

    Args:
        insights: Full insight list for the expert.
        base:     Base threshold value (default 4).

    Returns:
        Effective threshold (always >= base when corpus is large).
    """
    import math

    n = len(insights)
    if n < 20:
        proportional = math.ceil(n * 0.15)
        return max(base, proportional)
    return base


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_patterns(
    insights: list[dict[str, Any]],
    threshold: int = _DEFAULT_THRESHOLD,
) -> list[dict[str, Any]]:
    """Detect recurring patterns in *insights* by tag frequency.

    A pattern is declared when a tag appears in >= *threshold* insights.
    The threshold is adjusted for small corpora (< 20 insights) via
    ``_compute_adaptive_threshold``.

    Args:
        insights:  List of insight dicts. Each must have ``tag`` or ``dna_tag``.
        threshold: Minimum occurrences to declare a pattern. Default: 4.

    Returns:
        List of pattern dicts sorted descending by ``occurrence_count``.
        Capped at ``MAX_PATTERNS_PER_EXPERT`` entries (top by count).
        Schema per entry:
        ::

            {
                "pattern_name": str,
                "tag": str,
                "occurrence_count": int,
                "examples": list[str],   # up to 3 insight IDs
                "confidence": float,     # avg of numeric confidence
                "first_seen": str,       # ISO-8601
                "last_seen": str,        # ISO-8601
            }
    """
    if not insights:
        return []

    effective_threshold = _compute_adaptive_threshold(insights, threshold)

    # Group insights by normalised tag
    tag_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ins in insights:
        tag = _extract_tag(ins)
        tag_groups[tag].append(ins)

    patterns: list[dict[str, Any]] = []
    now = _now_iso()

    for tag, group in tag_groups.items():
        if len(group) < effective_threshold:
            continue

        # Compute average confidence (convert string levels to floats)
        def _conf_to_float(c: Any) -> float:
            if isinstance(c, int | float):
                return float(c)
            mapping = {
                "HIGH": 0.9,
                "ALTA": 0.9,
                "MEDIUM": 0.7,
                "MEDIA": 0.7,
                "LOW": 0.5,
                "BAIXA": 0.5,
            }
            return mapping.get(str(c).strip().upper(), 0.7)

        conf_avg = sum(_conf_to_float(ins.get("confidence", "MEDIUM")) for ins in group) / len(
            group
        )

        # Collect up to 3 example insight IDs
        examples = [
            str(ins.get("id") or ins.get("insight_id") or "")
            for ins in group[:3]
            if ins.get("id") or ins.get("insight_id")
        ]

        patterns.append(
            {
                "pattern_name": _derive_pattern_name(tag, group[0]),
                "tag": tag,
                "occurrence_count": len(group),
                "examples": examples,
                "confidence": round(conf_avg, 4),
                "first_seen": now,
                "last_seen": now,
            }
        )

    # Sort by occurrence descending, cap at MAX_PATTERNS_PER_EXPERT
    patterns.sort(key=lambda p: -p["occurrence_count"])
    return patterns[:MAX_PATTERNS_PER_EXPERT]


def detect_consensus(
    slugs_dict: dict[str, list[dict[str, Any]]],
    high_confidence_threshold: float = _HIGH_CONFIDENCE_NUMERIC,
) -> list[dict[str, Any]]:
    """Detect consensus points across multiple experts.

    A consensus is declared when 2+ distinct slugs (experts) have insights
    with the same normalised tag AND high confidence.

    Only slugs processed in the last 30 days are considered (Risk #2
    mitigation). Caller is responsible for pre-filtering if needed; this
    function accepts ``slugs_dict`` as provided.

    Args:
        slugs_dict:               Mapping of ``slug -> list[insight_dict]``.
                                  Each insight should have ``tag``/``dna_tag``
                                  and ``confidence``.
        high_confidence_threshold: Numeric floor for considering a confidence
                                   value "high". Default: 0.8. String values
                                   are mapped via ``_confidence_is_high``.

    Returns:
        List of consensus dicts sorted descending by ``insight_count``.
        Schema per entry:
        ::

            {
                "topic": str,          # normalised tag used as topic key
                "experts": list[str],  # slugs with high-confidence insights
                "shared_tag": str,
                "confidence_avg": float,
                "insight_count": int,
                "summary": str,
            }
    """
    if not slugs_dict or len(slugs_dict) < 2:
        return []

    # tag -> {slug -> [insight, ...]}
    tag_to_slug_insights: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for slug, insights in slugs_dict.items():
        for ins in insights:
            if not _confidence_is_high(ins.get("confidence")):
                continue
            tag = _extract_tag(ins)
            tag_to_slug_insights[tag][slug].append(ins)

    consensus: list[dict[str, Any]] = []

    for tag, slug_map in tag_to_slug_insights.items():
        agreeing_slugs = list(slug_map.keys())
        if len(agreeing_slugs) < 2:
            continue  # AC4: consensus requires >= 2 experts

        # Collect all high-confidence insights across agreeing slugs
        all_insights: list[dict[str, Any]] = []
        for slug_insights in slug_map.values():
            all_insights.extend(slug_insights)

        def _conf_to_float(c: Any) -> float:
            if isinstance(c, int | float):
                return float(c)
            mapping = {
                "HIGH": 0.9,
                "ALTA": 0.9,
                "MEDIUM": 0.7,
                "MEDIA": 0.7,
                "LOW": 0.5,
                "BAIXA": 0.5,
            }
            return mapping.get(str(c).strip().upper(), 0.7)

        conf_avg = sum(_conf_to_float(ins.get("confidence")) for ins in all_insights) / len(
            all_insights
        )

        # Build summary from first insight of each agreeing expert
        expert_samples = [slug_map[s][0].get("insight", "") for s in agreeing_slugs[:2]]
        summary = f"{' e '.join(agreeing_slugs[:3])} convergem em: " + (
            expert_samples[0][:80] if expert_samples else tag
        )

        consensus.append(
            {
                "topic": tag.lower().replace("_", "-"),
                "experts": sorted(agreeing_slugs),
                "shared_tag": tag,
                "confidence_avg": round(conf_avg, 4),
                "insight_count": len(all_insights),
                "summary": summary,
            }
        )

    consensus.sort(key=lambda c: -c["insight_count"])
    return consensus


def merge_patterns_incremental(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge *incoming* patterns into *existing* without duplication (AC5).

    Matching is by ``tag`` field. On match:
      - Increment ``occurrence_count`` by incoming count.
      - Update ``last_seen`` to incoming ``last_seen``.
      - Extend ``examples`` (dedup, keep up to 5).
      - Recompute ``confidence`` as weighted average.

    New patterns (tag not in existing) are appended.

    Result is re-sorted by ``occurrence_count`` descending and capped at
    ``MAX_PATTERNS_PER_EXPERT``.

    Args:
        existing: Current patterns list from NARRATIVES-STATE.
        incoming: Freshly detected patterns list.

    Returns:
        Merged, sorted, capped patterns list.
    """
    merged: dict[str, dict[str, Any]] = {p["tag"]: dict(p) for p in existing}

    for inc in incoming:
        tag = inc["tag"]
        if tag in merged:
            ex = merged[tag]
            ex_count = int(ex.get("occurrence_count", 0))
            inc_count = int(inc.get("occurrence_count", 0))
            total = ex_count + inc_count

            # Weighted confidence average
            ex_conf = float(ex.get("confidence", 0.7))
            inc_conf = float(inc.get("confidence", 0.7))
            if total > 0:
                new_conf = round((ex_conf * ex_count + inc_conf * inc_count) / total, 4)
            else:
                new_conf = ex_conf

            # Merge examples (dedup, cap at 5)
            combined_examples = list(
                dict.fromkeys(list(ex.get("examples", [])) + list(inc.get("examples", [])))
            )[:5]

            merged[tag] = {
                **ex,
                "occurrence_count": total,
                "confidence": new_conf,
                "examples": combined_examples,
                "last_seen": inc.get("last_seen", ex.get("last_seen", _now_iso())),
            }
        else:
            merged[tag] = dict(inc)

    result = sorted(merged.values(), key=lambda p: -p["occurrence_count"])
    return result[:MAX_PATTERNS_PER_EXPERT]


def merge_consensus_incremental(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge *incoming* consensus entries into *existing* without duplication (AC5).

    Matching is by ``topic`` field. On match:
      - Add new experts to ``experts`` list (dedup).
      - Update ``insight_count`` by adding incoming count.
      - Recompute ``confidence_avg``.

    New topics are appended.

    Args:
        existing: Current consensus_points list from NARRATIVES-STATE.
        incoming: Freshly detected consensus entries.

    Returns:
        Merged consensus list sorted by ``insight_count`` descending.
    """
    merged: dict[str, dict[str, Any]] = {c["topic"]: dict(c) for c in existing}

    for inc in incoming:
        topic = inc["topic"]
        if topic in merged:
            ex = merged[topic]
            # Merge expert lists (dedup, preserve order)
            combined_experts = list(
                dict.fromkeys(list(ex.get("experts", [])) + list(inc.get("experts", [])))
            )
            ex_count = int(ex.get("insight_count", 0))
            inc_count = int(inc.get("insight_count", 0))
            total = ex_count + inc_count

            ex_conf = float(ex.get("confidence_avg", 0.8))
            inc_conf = float(inc.get("confidence_avg", 0.8))
            new_conf = (
                round((ex_conf * ex_count + inc_conf * inc_count) / total, 4)
                if total > 0
                else ex_conf
            )

            merged[topic] = {
                **ex,
                "experts": sorted(combined_experts),
                "insight_count": total,
                "confidence_avg": new_conf,
                # Prefer incoming summary if it mentions more experts
                "summary": inc.get("summary", ex.get("summary", "")),
            }
        else:
            merged[topic] = dict(inc)

    result = sorted(merged.values(), key=lambda c: -c["insight_count"])
    return result
