"""threshold_loader.py -- Central loader for pipeline thresholds.

Story: STORY-MCE-11.19
Reads thresholds from thresholds.yaml. Falls back to hardcoded defaults when
the YAML is absent, ensuring backward compatibility with all existing consumers.

Usage:
    from engine.intelligence.pipeline.config.threshold_loader import get_threshold

    val = get_threshold("dna_auto_create.min_density")      # returns 3
    val = get_threshold("entity_resolution.fuzzy_threshold") # returns 0.85
    val = get_threshold("missing.key", default=None)         # returns None
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_THRESHOLDS_YAML = Path(__file__).parent / "thresholds.yaml"

# Hardcoded fallback defaults -- mirrors the values in thresholds.yaml.
# These are ONLY used when thresholds.yaml is missing or unreadable.
# Update thresholds.yaml, not this dict, for permanent changes.
THRESHOLDS_DEFAULTS: dict[str, Any] = {
    "role_creation": {
        "critical": 10,
        "important": 5,
        "track": 1,
        "status": "not_implemented",
    },
    "dna_auto_create": {
        "min_density": 3,
        "max_density": 5,
    },
    "dna_consolidation": {
        "min_density": 4,
        "max_density": 5,
        "status": "not_implemented",
    },
    "entity_resolution": {
        "auto_merge_threshold": 0.95,
        "fuzzy_threshold": 0.85,
        "separated_threshold": 0.85,
    },
    "anomaly_detection": {
        "desvio_pct": 25,
        "window": 5,
        "status": "not_implemented",
    },
    "depara_match_rate": {
        "ok_threshold": 80,
        "warn_threshold": 50,
        "halt_threshold": 0,
        "status": "not_implemented",
    },
    "inbox_age": {
        "urgent_days": 3,
        "normal_days": 1,
    },
    "token_checkpoint": {
        "heuristic_only": True,
        "status": "observational",
    },
    "template_evolution": {
        "min_insights": 3,
        "min_frameworks": 1,
        "status": "not_implemented",
    },
}

# Module-level cache -- loaded once per process, refreshed via load_thresholds(force=True)
_cache: dict[str, Any] | None = None


def load_thresholds(*, force: bool = False) -> dict[str, Any]:
    """Load thresholds from thresholds.yaml.

    Falls back to THRESHOLDS_DEFAULTS if file is missing or invalid.

    Args:
        force: If True, bypass the module cache and reload from disk.

    Returns:
        Dict containing the 'thresholds' subtree from the YAML.
    """
    global _cache

    if _cache is not None and not force:
        return _cache

    if _THRESHOLDS_YAML.exists():
        try:
            import yaml  # stdlib pyyaml -- always available in this project

            raw = yaml.safe_load(_THRESHOLDS_YAML.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and "thresholds" in raw:
                _cache = raw["thresholds"]
                logger.debug(
                    "threshold_loader: loaded %d keys from %s", len(_cache), _THRESHOLDS_YAML
                )
                return _cache
            logger.warning(
                "threshold_loader: thresholds.yaml missing 'thresholds' root key -- using defaults"
            )
        except Exception as exc:
            logger.warning(
                "threshold_loader: cannot parse thresholds.yaml: %s -- using defaults", exc
            )

    logger.debug("threshold_loader: thresholds.yaml not found -- using hardcoded defaults")
    _cache = THRESHOLDS_DEFAULTS
    return _cache


def get_threshold(key: str, default: Any = None) -> Any:
    """Get a threshold value by dot-separated key path.

    Args:
        key: Dot-separated path into the thresholds dict.
             Examples: "dna_auto_create.min_density", "inbox_age.urgent_days"
        default: Value to return when the key path is not found.

    Returns:
        The threshold value, or *default* when not found.

    Examples:
        >>> get_threshold("dna_auto_create.min_density")
        3
        >>> get_threshold("entity_resolution.fuzzy_threshold")
        0.85
        >>> get_threshold("inbox_age.urgent_days")
        3
    """
    data = load_thresholds()
    parts = key.split(".")
    current: Any = data
    for part in parts:
        if not isinstance(current, dict):
            return default
        current = current.get(part)
        if current is None:
            return default
    return current


def set_threshold_override(key: str, value: Any) -> None:
    """Override a threshold value at runtime (non-persistent, current process only).

    WARNING: This does NOT persist -- the override is lost when the process exits.
    To make permanent changes, edit thresholds.yaml directly.

    Args:
        key: Dot-separated path into the thresholds dict.
        value: New value to set.

    Raises:
        KeyError: When the key path does not exist in the current thresholds.
    """
    print(
        "  [WARNING] Runtime override -- nao persiste. "
        "Edite thresholds.yaml para mudanca permanente."
    )

    data = load_thresholds()
    parts = key.split(".")
    current: Any = data

    for part in parts[:-1]:
        if not isinstance(current, dict):
            raise KeyError(f"Key path '{key}' not found -- '{part}' is not a dict")
        if part not in current:
            raise KeyError(f"Key path '{key}' not found -- '{part}' does not exist")
        current = current[part]

    leaf = parts[-1]
    if not isinstance(current, dict):
        raise KeyError(f"Key path '{key}' -- parent is not a dict")
    if leaf not in current:
        raise KeyError(f"Key path '{key}' -- leaf '{leaf}' does not exist in thresholds")

    old_value = current[leaf]
    current[leaf] = value
    logger.info("threshold_loader: runtime override %s: %r -> %r", key, old_value, value)
    print(f"  threshold [{key}]: {old_value!r} -> {value!r}  (runtime only)")


def show_thresholds() -> str:
    """Format all thresholds as a human-readable table for CLI display.

    Returns:
        Formatted string table.
    """
    data = load_thresholds()

    rows: list[tuple[str, str, str]] = []

    for group_key, group_val in data.items():
        if not isinstance(group_val, dict):
            continue
        status = group_val.get("status", "")
        source = group_val.get("source", "")
        # Collect numeric/bool leaf values only (skip metadata keys)
        skip_keys = {"source", "description", "note", "status", "pending_story"}
        numeric_parts = []
        for k, v in group_val.items():
            if k in skip_keys:
                continue
            if isinstance(v, int | float | bool):
                numeric_parts.append(f"{k}={v}")

        value_str = ", ".join(numeric_parts) if numeric_parts else "(see yaml)"
        if status and status not in ("", "observational"):
            value_str += f"  [{status}]"

        # Shorten source for display
        src_short = source.split("(")[0].strip() if source else "-"
        if len(src_short) > 50:
            src_short = src_short[:47] + "..."

        rows.append((group_key, value_str, src_short))

    col_w = [
        max(len(r[0]) for r in rows) if rows else 10,
        max(len(r[1]) for r in rows) if rows else 20,
        max(len(r[2]) for r in rows) if rows else 30,
    ]

    header = f"{'Threshold':<{col_w[0]}}  {'Value':<{col_w[1]}}  {'Source':<{col_w[2]}}"
    separator = "  ".join("-" * w for w in col_w)

    lines = [header, separator]
    for r in rows:
        lines.append(f"{r[0]:<{col_w[0]}}  {r[1]:<{col_w[1]}}  {r[2]:<{col_w[2]}}")

    return "\n".join(lines)
