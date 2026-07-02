"""entity_resolver.py — Entity Resolution + Canonical Map (Story MCE-13.22).

Resolves entity aliases using substring + token overlap heuristics (stdlib only,
no ML/embeddings). Populates CANONICAL-MAP.json with a canonical_entities block
that maps aliases to their canonical form.

Key behavior:
  - "Hormozi" + "alex-hormozi" + "$100M Offers author" → resolve to same entity
  - Threshold: 0.85 confidence (string similarity >= 0.85 OR exact slug match)
  - Output: CANONICAL-MAP.json updated with aliases{} and review_queue[]
  - Non-blocking: exceptions are caught by caller

Stack: stdlib only (difflib, re, json, pathlib). Zero LLM. Zero imports of
       orchestrate.py.

Story: MCE-13.22
"""

from __future__ import annotations

import json
import logging
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Confidence threshold for alias resolution
ALIAS_CONFIDENCE_THRESHOLD = 0.85

# Maximum entities to add to review_queue (prevents oversized output)
_MAX_REVIEW_QUEUE = 50

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalise_name(name: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    text = name.lower()
    text = re.sub(r"['\"\$\.\,\!\?\-\_]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _token_overlap_ratio(a: str, b: str) -> float:
    """Return token overlap as Jaccard similarity (0.0-1.0).

    J = |A ∩ B| / |A ∪ B|
    """
    tokens_a = set(_normalise_name(a).split())
    tokens_b = set(_normalise_name(b).split())
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def _sequence_similarity(a: str, b: str) -> float:
    """SequenceMatcher ratio on normalised strings."""
    na, nb = _normalise_name(a), _normalise_name(b)
    if not na and not nb:
        return 1.0
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def _slug_to_display(slug: str) -> str:
    """Convert slug to display name: 'alex-hormozi' → 'Alex Hormozi'."""
    return " ".join(part.capitalize() for part in slug.replace("_", "-").split("-"))


def _is_substring_match(candidate: str, canonical: str) -> bool:
    """Return True if normalised candidate is a substring of canonical (or vice versa).

    This handles cases like "Hormozi" ⊂ "Alex Hormozi".
    """
    nc = _normalise_name(candidate)
    ncan = _normalise_name(canonical)
    return (nc in ncan or ncan in nc) and len(nc) >= 3


def compute_similarity(candidate: str, canonical: str) -> float:
    """Composite similarity: max(sequence_ratio, token_jaccard, substring_boost).

    Returns a value in [0.0, 1.0].
    """
    seq = _sequence_similarity(candidate, canonical)
    tok = _token_overlap_ratio(candidate, canonical)
    sub = 0.9 if _is_substring_match(candidate, canonical) else 0.0
    return max(seq, tok, sub)


# ---------------------------------------------------------------------------
# Core resolution logic
# ---------------------------------------------------------------------------


def resolve_entity_aliases(
    entities: dict[str, list[str]],
    slug: str,
) -> tuple[dict[str, list[str]], dict[str, str], list[dict[str, Any]]]:
    """Resolve aliases within and across entity categories.

    For each entity, compute similarity against all known canonical forms
    (including the slug itself). Entities with similarity >= ALIAS_CONFIDENCE_THRESHOLD
    are merged. Low-confidence candidates go to review_queue.

    Args:
        entities:  Dict with persons/companies/products/concepts lists.
        slug:      Pipeline slug (used as canonical anchor for persons).

    Returns:
        Tuple of:
          - resolved_entities: same structure as entities but deduplicated
          - aliases_map: {alias_string: canonical_string}
          - review_queue: [{candidate, best_match, confidence, reason}]
    """
    aliases_map: dict[str, str] = {}
    review_queue: list[dict[str, Any]] = []

    slug_display = _slug_to_display(slug)

    def _resolve_category(items: list[str], extra_anchors: list[str]) -> list[str]:
        """Resolve items within a category, using extra_anchors as canonical seeds."""
        canonical_set: list[str] = list(extra_anchors)  # ordered, preserving insertion order
        resolved: list[str] = list(extra_anchors)

        for item in items:
            if not item or not item.strip():
                continue
            item = item.strip()

            # Already resolved this item?
            if item in aliases_map:
                continue

            best_match: str | None = None
            best_score = 0.0

            # Check against all known canonical forms
            for canon in canonical_set:
                score = compute_similarity(item, canon)
                if score > best_score:
                    best_score = score
                    best_match = canon

            if best_score >= ALIAS_CONFIDENCE_THRESHOLD and best_match:
                # High confidence: this is an alias of best_match
                if item.lower() != best_match.lower():
                    aliases_map[item] = best_match
                    logger.debug(
                        "entity_resolver: '%s' → '%s' (score=%.3f)", item, best_match, best_score
                    )
            elif best_score >= 0.5 and best_match:
                # Medium confidence: flag for review
                if len(review_queue) < _MAX_REVIEW_QUEUE:
                    review_queue.append(
                        {
                            "candidate": item,
                            "best_match": best_match,
                            "confidence": round(best_score, 3),
                            "reason": "similarity_below_threshold",
                        }
                    )
                # Still add as new canonical (conservative)
                canonical_set.append(item)
                resolved.append(item)
            else:
                # New entity — add to canonical set
                canonical_set.append(item)
                resolved.append(item)

        # Return deduplicated list (preserve order, no aliases)
        seen: set[str] = set()
        deduped: list[str] = []
        for item in resolved:
            key = _normalise_name(item)
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        return deduped

    # Person resolution: slug display name is the primary anchor
    person_anchors = [slug_display] if slug_display else []
    resolved_persons = _resolve_category(entities.get("persons", []), person_anchors)

    resolved_companies = _resolve_category(entities.get("companies", []), [])
    resolved_products = _resolve_category(entities.get("products", []), [])
    resolved_concepts = _resolve_category(entities.get("concepts", []), [])

    resolved_entities = {
        "persons": resolved_persons,
        "companies": resolved_companies,
        "products": resolved_products,
        "concepts": resolved_concepts,
    }

    return resolved_entities, aliases_map, review_queue


# ---------------------------------------------------------------------------
# Public API: cmd_resolve_entities (called from orchestrate.py)
# ---------------------------------------------------------------------------


def resolve_entities_for_slug(
    slug: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Load CANONICAL-MAP.json for slug, resolve aliases, write updated map.

    This is the primary entry point called by orchestrate.cmd_resolve_entities.

    Returns:
        Dict with keys: status, slug, aliases_found, review_queue_size, entities_resolved.
        status: 'updated' | 'no_map' | 'error'
    """
    if root is None:
        root = Path(__file__).resolve().parent.parent.parent.parent.parent

    canonical_path = root / ".data" / "artifacts" / "canonical" / slug / "CANONICAL-MAP.json"

    if not canonical_path.exists():
        logger.debug("entity_resolver: no CANONICAL-MAP.json for %s — skipping", slug)
        return {
            "status": "no_map",
            "slug": slug,
            "aliases_found": 0,
            "review_queue_size": 0,
            "entities_resolved": 0,
        }

    try:
        data = json.loads(canonical_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("entity_resolver: failed to load CANONICAL-MAP.json for %s: %s", slug, exc)
        return {
            "status": "error",
            "slug": slug,
            "error": str(exc),
            "aliases_found": 0,
            "review_queue_size": 0,
            "entities_resolved": 0,
        }

    entities_raw = data.get("entities") or data.get("canonical_entities") or {}
    if not entities_raw:
        return {
            "status": "no_entities",
            "slug": slug,
            "aliases_found": 0,
            "review_queue_size": 0,
            "entities_resolved": 0,
        }

    resolved_entities, aliases_map, review_queue = resolve_entity_aliases(entities_raw, slug)

    total_resolved = sum(len(v) for v in resolved_entities.values())

    # Update CANONICAL-MAP.json with resolution results
    data["entities"] = resolved_entities
    data["canonical_entities"] = resolved_entities
    data["aliases"] = aliases_map
    data["review_queue"] = review_queue
    data["resolution_meta"] = {
        "threshold": ALIAS_CONFIDENCE_THRESHOLD,
        "aliases_found": len(aliases_map),
        "review_queue_size": len(review_queue),
        "resolved_at": _now_iso(),
    }

    try:
        canonical_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(
            "entity_resolver: updated CANONICAL-MAP.json for %s — aliases=%d review=%d",
            slug,
            len(aliases_map),
            len(review_queue),
        )
    except Exception as exc:
        logger.warning("entity_resolver: failed to write CANONICAL-MAP.json for %s: %s", slug, exc)
        return {
            "status": "error",
            "slug": slug,
            "error": str(exc),
            "aliases_found": len(aliases_map),
            "review_queue_size": len(review_queue),
            "entities_resolved": total_resolved,
        }

    return {
        "status": "updated",
        "slug": slug,
        "aliases_found": len(aliases_map),
        "review_queue_size": len(review_queue),
        "entities_resolved": total_resolved,
    }


def _now_iso() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()
