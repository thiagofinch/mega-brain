"""
narrative_merger.py — Narrative Metabolism merge logic (MCE-4.1)
================================================================

Provides three public functions:
  - merge_narrative_entry(existing, incoming, domain, bucket) -> dict
  - get_merge_rules(domain) -> dict
  - validate_bucket(entry) -> None

Stack: stdlib + PyYAML only. Zero LLM. Zero external dependencies.

Art. XIII compliance: bucket field mandatory, cross-bucket writes blocked.
Story MCE-4.1 — Wave 2.
"""

from __future__ import annotations

__all__ = [
    "get_merge_rules",
    "merge_narrative_entry",
    "validate_bucket",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_BUCKETS: frozenset[str] = frozenset({"external", "business", "personal"})

# Per-domain merge rules (AC3). 10 canonical domains.
# strategy:    append       — accumulate all entries (ordered, no clobber)
#              replace      — newest entry wins entirely
#              merge_latest — keep N most recent, dedup by dedup_key
# dedup_key:   field used to identify duplicates within the domain
# max_entries: hard cap (0 = unlimited)
_DEFAULT_MERGE_RULES: dict[str, dict[str, object]] = {
    "vendas": {
        "strategy": "append",
        "dedup_key": "slug",
        "max_entries": 0,
    },
    "ads": {
        "strategy": "merge_latest",
        "dedup_key": "slug",
        "max_entries": 50,
    },
    "offers": {
        "strategy": "replace",
        "dedup_key": "slug",
        "max_entries": 10,
    },
    "content": {
        "strategy": "append",
        "dedup_key": "slug",
        "max_entries": 0,
    },
    "marketing": {
        "strategy": "merge_latest",
        "dedup_key": "slug",
        "max_entries": 0,
    },
    "finance": {
        "strategy": "replace",
        "dedup_key": "slug",
        "max_entries": 0,
    },
    "hiring": {
        "strategy": "append",
        "dedup_key": "slug",
        "max_entries": 20,
    },
    "outbound": {
        "strategy": "merge_latest",
        "dedup_key": "slug",
        "max_entries": 30,
    },
    "leadership": {
        "strategy": "append",
        "dedup_key": "slug",
        "max_entries": 0,
    },
    "customer-success": {
        "strategy": "merge_latest",
        "dedup_key": "slug",
        "max_entries": 0,
    },
}

# Universal fallback for unregistered domains.
_UNIVERSAL_DEFAULT_RULE: dict[str, object] = {
    "strategy": "append",
    "dedup_key": "slug",
    "max_entries": 0,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_bucket(entry: dict) -> None:  # type: ignore[type-arg]
    """Raise ValueError if *entry* has a missing, empty, or invalid bucket.

    Art. XIII compliance gate — called before any write to NARRATIVES-STATE.json.

    Args:
        entry: dict that MUST contain a ``bucket`` key with a valid value.

    Raises:
        ValueError: if ``bucket`` is absent, empty string, or not in
            {external, business, personal}.
    """
    bucket = entry.get("bucket")
    if bucket is None:
        raise ValueError(
            "Missing 'bucket' field in narrative entry. "
            "Art. XIII (Knowledge Bucket Isolation) requires explicit bucket declaration. "
            f"Valid values: {sorted(VALID_BUCKETS)}"
        )
    if not isinstance(bucket, str) or bucket.strip() == "":
        raise ValueError(
            f"Empty 'bucket' field in narrative entry. " f"Valid values: {sorted(VALID_BUCKETS)}"
        )
    if bucket not in VALID_BUCKETS:
        raise ValueError(f"Invalid bucket '{bucket}'. " f"Valid values: {sorted(VALID_BUCKETS)}")


def get_merge_rules(domain: str) -> dict:  # type: ignore[type-arg]
    """Return merge rules for *domain*.

    If *domain* is not in the canonical 10-domain registry, returns the
    universal default rule (append, dedup by slug, unlimited).  This ensures
    new/unknown domains never crash the pipeline while still having safe
    defaults.

    Rules are per-domain and isolated — ``vendas`` rules NEVER contaminate
    ``finance`` rules (AC3 isolation guarantee).

    Args:
        domain: lowercase domain string (e.g. ``"vendas"``, ``"finance"``).

    Returns:
        dict with keys ``strategy``, ``dedup_key``, ``max_entries``.
    """
    return dict(_DEFAULT_MERGE_RULES.get(domain, _UNIVERSAL_DEFAULT_RULE))


def merge_narrative_entry(
    existing: dict,  # type: ignore[type-arg]
    incoming: dict,  # type: ignore[type-arg]
    domain: str,
    bucket: str,
) -> dict:  # type: ignore[type-arg]
    """Apply domain merge rule to combine *existing* and *incoming* entries.

    Cross-bucket writes are blocked — if ``existing["bucket"]`` is set and
    differs from *bucket*, a ValueError is raised (Art. XIII).

    The merge strategy is looked up via ``get_merge_rules(domain)`` and applied:

    - ``append``:       Concatenate ``entries`` lists; dedup by ``dedup_key``.
    - ``replace``:      Incoming fully replaces existing content fields.
    - ``merge_latest``: Keep the N most recent entries (``max_entries`` cap).

    Args:
        existing: Current state dict for this person/theme entry.  May be
            empty dict if the entry is new.
        incoming: New data to merge in.  MUST carry a ``bucket`` field matching
            *bucket*.
        domain:   Domain string (e.g. ``"vendas"``).  Determines merge strategy.
        bucket:   Bucket string (``"external" | "business" | "personal"``).
            Must match both *incoming* and *existing* (if non-empty).

    Returns:
        Merged dict.  Always contains ``bucket`` field.

    Raises:
        ValueError: if bucket validation fails or cross-bucket write detected.
    """
    # Validate incoming entry carries a proper bucket
    incoming_with_bucket = {**incoming, "bucket": bucket}
    validate_bucket(incoming_with_bucket)

    # Cross-bucket guard: existing entry must not belong to a different bucket
    existing_bucket = existing.get("bucket")
    if existing_bucket and existing_bucket != bucket:
        raise ValueError(
            f"Cross-bucket write blocked: existing entry has bucket='{existing_bucket}' "
            f"but incoming targets bucket='{bucket}'. "
            "Art. XIII prohibits cross-bucket mutations."
        )

    rules = get_merge_rules(domain)
    strategy: str = str(rules["strategy"])
    dedup_key: str = str(rules["dedup_key"])
    max_entries: int = int(rules["max_entries"])  # type: ignore[arg-type]

    # Start from a copy of existing so we never mutate caller state
    result = dict(existing)
    result["bucket"] = bucket

    if strategy == "replace":
        # Newest wins — overwrite all content fields from incoming
        for k, v in incoming.items():
            result[k] = v
        result["bucket"] = bucket  # always enforce

    elif strategy == "append":
        existing_entries: list = list(result.get("entries", []))
        incoming_entries: list = list(incoming.get("entries", []))
        combined = _dedup_entries(existing_entries + incoming_entries, dedup_key)
        if max_entries > 0:
            combined = combined[-max_entries:]
        result["entries"] = combined
        # Merge scalar fields (incoming wins)
        for k, v in incoming.items():
            if k not in ("entries", "bucket"):
                result[k] = v

    elif strategy == "merge_latest":
        existing_entries = list(result.get("entries", []))
        incoming_entries = list(incoming.get("entries", []))
        combined = _dedup_entries(existing_entries + incoming_entries, dedup_key)
        # merge_latest: sort by last_updated if available, take newest N
        combined = _sort_by_recency(combined)
        if max_entries > 0:
            combined = combined[-max_entries:]
        result["entries"] = combined
        for k, v in incoming.items():
            if k not in ("entries", "bucket"):
                result[k] = v

    else:
        # Unknown strategy — safe fallback: incoming overrides
        for k, v in incoming.items():
            result[k] = v
        result["bucket"] = bucket

    return result


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _dedup_entries(
    entries: list,  # type: ignore[type-arg]
    dedup_key: str,
) -> list:  # type: ignore[type-arg]
    """Deduplicate *entries* by *dedup_key*, keeping last occurrence.

    Entries without the dedup_key are always kept (no dedup possible).
    Preserves insertion order of first occurrence, latest value wins.

    Args:
        entries:   List of dicts.
        dedup_key: Key to use for deduplication.

    Returns:
        Deduplicated list.
    """
    seen: dict[object, int] = {}
    result: list = []
    for entry in entries:
        key_val = entry.get(dedup_key) if isinstance(entry, dict) else None
        if key_val is None:
            result.append(entry)
        elif key_val in seen:
            # Update in place (latest wins)
            result[seen[key_val]] = entry
        else:
            seen[key_val] = len(result)
            result.append(entry)
    return result


def _sort_by_recency(
    entries: list,  # type: ignore[type-arg]
) -> list:  # type: ignore[type-arg]
    """Sort entries by ``last_updated`` ascending (oldest first, newest last).

    Entries without ``last_updated`` sort before those that have it.

    Args:
        entries: List of dicts.

    Returns:
        Sorted list.
    """

    def _key(entry: dict) -> str:  # type: ignore[type-arg]
        if not isinstance(entry, dict):
            return ""
        return str(entry.get("last_updated", ""))

    return sorted(entries, key=_key)
