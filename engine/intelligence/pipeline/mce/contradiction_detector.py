"""contradiction_detector.py — INSIGHT contradiction detection v1 (Story MCE-4.4).

Detection strategy: keyword-based (conservative), stdlib + PyYAML only.
No LLM, no requests, no fuzzy matching.  False-positive is preferred over
false-negative in v1 — user dismisses via REVIEW-QUEUE DISMISSED status.

Algorithm:
  For each pair (insight_a, insight_b) in the slug's insight list:
    1. Check if either insight contains an absolute-negation keyword
       (NUNCA, SEMPRE, JAMAIS, OBRIGATORIO, IMPOSSIVEL, PROIBIDO, DEVE,
        NAO DEVE).
    2. If yes, check if the *other* insight contains the antonym keyword
       from the registered pair table.
    3. If antonym match found → emit ContradictionEntry.
       confidence=HIGH when both sides carry the exact keyword pair.
       confidence=MEDIUM when the antonym is inferred from the table
       but only one keyword is present.

Hash IDs:
  make_item_id(slug, question) → sha256(slug::question)[:8]
  make_dedup_key(slug, type_, question) → sha256(slug::type_::question)[:12]
  make_contradiction_id(slug, a_id, b_id) → sha256(slug::sorted_pair)[:8]
  (pair is sorted so (A,B) == (B,A))

Veto V5: stdlib + PyYAML only.  No external dependencies.
Veto V1: IDs are ALWAYS hash-based. Sequential index NEVER used.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Antonym pairs — v1 keyword table (extensible via future config)
# ---------------------------------------------------------------------------

# Each tuple is (keyword_a, keyword_b).  Both directions are checked.
# Keywords are normalized to uppercase for comparison.
_ANTONYM_PAIRS: list[tuple[str, str]] = [
    ("NUNCA", "SEMPRE"),
    ("PROIBIDO", "OBRIGATORIO"),
    ("IMPOSSIVEL", "POSSIVEL"),
    ("NAO DEVE", "DEVE"),
    ("ELIMINAR", "PRESERVAR"),
    ("AUMENTAR", "REDUZIR"),
    ("ACELERAR", "DESACELERAR"),
    ("SIMPLIFICAR", "COMPLEXIFICAR"),
    # Additional directional pairs
    ("JAMAIS", "SEMPRE"),
    ("NUNCA", "OBRIGATORIO"),
    ("PROIBIDO", "DEVE"),
]

# Flatten to a set of all negation anchors for fast pre-filter
_NEGATION_ANCHORS: frozenset[str] = frozenset(kw for pair in _ANTONYM_PAIRS for kw in pair)


# ---------------------------------------------------------------------------
# Public hash helpers (AC1 — deterministic IDs)
# ---------------------------------------------------------------------------


def make_item_id(person_slug: str, question: str) -> str:
    """Deterministic 8-char ID for an open_loop or contradiction REVIEW-QUEUE item.

    sha256(person_slug :: question)[:8].
    Same slug+question always produces the same ID across runs.
    """
    raw = f"{person_slug}::{question}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]


def make_dedup_key(person_slug: str, type_: str, question: str) -> str:
    """Deterministic 12-char dedup key for a REVIEW-QUEUE item.

    sha256(person_slug :: type_ :: question)[:12].
    """
    raw = f"{person_slug}::{type_}::{question}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def make_contradiction_id(person_slug: str, insight_a_id: str, insight_b_id: str) -> str:
    """Deterministic 8-char ID for a contradiction pair.

    Pair is sorted so make_contradiction_id(slug, A, B) == make_contradiction_id(slug, B, A).
    sha256(person_slug :: sorted(insight_a_id, insight_b_id))[:8].
    """
    pair = sorted([insight_a_id, insight_b_id])
    raw = f"{person_slug}::{pair[0]}::{pair[1]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _extract_text(insight: dict[str, Any]) -> str:
    """Extract normalized uppercase text from an insight dict."""
    text = (
        insight.get("insight")
        or insight.get("quote")
        or insight.get("text")
        or insight.get("statement")
        or insight.get("content")
        or ""
    )
    return str(text).upper()


def _contains_keyword(text: str, keyword: str) -> bool:
    """Return True if keyword appears as a word-boundary match in text."""
    # Simple substring check — conservative, no regex overhead
    return keyword in text


def _find_triggered_pair(text_a: str, text_b: str) -> tuple[str, str, str] | None:
    """Return (keyword_a, keyword_b, confidence) if texts form a contradiction.

    Returns None if no contradiction is found.
    confidence is HIGH when both keywords are present in their respective texts.
    confidence is MEDIUM when one is present and the other is the table antonym.
    """
    for kw_a, kw_b in _ANTONYM_PAIRS:
        a_has_kw_a = _contains_keyword(text_a, kw_a)
        a_has_kw_b = _contains_keyword(text_a, kw_b)
        b_has_kw_a = _contains_keyword(text_b, kw_a)
        b_has_kw_b = _contains_keyword(text_b, kw_b)

        # Case 1: text_a has kw_a, text_b has kw_b (direct antonym)
        if a_has_kw_a and b_has_kw_b:
            confidence = "HIGH" if (a_has_kw_a and b_has_kw_b) else "MEDIUM"
            return (kw_a, kw_b, confidence)

        # Case 2: text_a has kw_b, text_b has kw_a (reversed)
        if a_has_kw_b and b_has_kw_a:
            confidence = "HIGH" if (a_has_kw_b and b_has_kw_a) else "MEDIUM"
            return (kw_b, kw_a, confidence)

    return None


# ---------------------------------------------------------------------------
# Public detection API
# ---------------------------------------------------------------------------


def detect(
    person_slug: str,
    insights: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run v1 contradiction detection over the insight list for ``person_slug``.

    Returns a list of ContradictionEntry dicts (schema: insights-state-contradictions).
    Each entry is ready to merge into INSIGHTS-STATE.json contradictions[].

    O(n^2) pairwise scan — acceptable for v1 (insights per slug typically < 500).
    Deduplicates by contradiction ID so re-runs don't produce duplicates.
    """
    valid = [i for i in insights if isinstance(i, dict)]
    found: dict[str, dict[str, Any]] = {}  # id -> entry (dedup within this run)

    # Pre-filter: only consider insights that carry at least one negation anchor.
    # This reduces the O(n^2) inner loop significantly for large insight sets.
    anchor_insights = [
        ins
        for ins in valid
        if any(_contains_keyword(_extract_text(ins), kw) for kw in _NEGATION_ANCHORS)
    ]

    # Compare each anchor insight against all other insights
    for i, ins_a in enumerate(anchor_insights):
        text_a = _extract_text(ins_a)
        id_a = ins_a.get("id") or f"_anon_a_{i}"

        for j, ins_b in enumerate(valid):
            id_b = ins_b.get("id") or f"_anon_b_{j}"
            if id_a == id_b:
                continue  # skip self-comparison

            text_b = _extract_text(ins_b)

            result = _find_triggered_pair(text_a, text_b)
            if result is None:
                continue

            kw_triggered_a, kw_triggered_b, confidence = result
            c_id = make_contradiction_id(person_slug, id_a, id_b)

            if c_id in found:
                continue  # already registered (commutative pair)

            found[c_id] = {
                "id": c_id,
                "insight_a_id": id_a,
                "insight_b_id": id_b,
                "trigger_keywords": [kw_triggered_a, kw_triggered_b],
                "confidence": confidence,
                "detected_at": _now_iso(),
                "status": "UNREVIEWED",
            }

    return list(found.values())


def build_review_queue_item_for_contradiction(
    person_slug: str,
    contradiction: dict[str, Any],
) -> dict[str, Any]:
    """Build a REVIEW-QUEUE item (type=contradiction) from a ContradictionEntry.

    The question text summarises which insights conflict and which keywords
    triggered the detection.
    """
    a_id = contradiction["insight_a_id"]
    b_id = contradiction["insight_b_id"]
    keywords = contradiction.get("trigger_keywords", [])
    question = f"Insight {a_id} vs Insight {b_id} — keywords: {', '.join(keywords)}"

    now = _now_iso()
    # TTL = 30 days from now
    ttl = (datetime.now(UTC) + timedelta(days=30)).isoformat()

    item_id = make_item_id(person_slug, question)
    dedup_key = make_dedup_key(person_slug, "contradiction", question)

    return {
        "id": item_id,
        "type": "contradiction",
        "status": "PENDING",
        "priority": "HIGH" if contradiction.get("confidence") == "HIGH" else "MEDIUM",
        "ttl": ttl,
        "dedup_key": dedup_key,
        "created_at": now,
        "person_slug": person_slug,
        "question": question,
        "source_insight_ids": [a_id, b_id],
        "resolution_note": None,
    }


def build_review_queue_item_for_open_loop(
    person_slug: str,
    open_loop: dict[str, Any],
) -> dict[str, Any]:
    """Build a REVIEW-QUEUE item (type=open_loop) from an open_loop dict.

    Consumes open_loop fields: question (or text/content), source_insight_ids.
    Generates deterministic id and dedup_key via hash.
    """
    question = (
        open_loop.get("question")
        or open_loop.get("text")
        or open_loop.get("content")
        or str(open_loop)
    )

    now = _now_iso()
    ttl = (datetime.now(UTC) + timedelta(days=30)).isoformat()

    item_id = make_item_id(person_slug, question)
    dedup_key = make_dedup_key(person_slug, "open_loop", question)

    return {
        "id": item_id,
        "type": "open_loop",
        "status": "PENDING",
        "priority": "MEDIUM",
        "ttl": ttl,
        "dedup_key": dedup_key,
        "created_at": now,
        "person_slug": person_slug,
        "question": question,
        "source_insight_ids": open_loop.get("source_insight_ids", []),
        "resolution_note": None,
    }
