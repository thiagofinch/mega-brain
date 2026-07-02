"""Centralized reader for ROLE-TRACKING.json with explicit schema.

Centralizes duplicated read patterns in log_generator.py into a single
source of truth. Schema is declared via TypedDict.

Schema (.data/artifacts/ROLE-TRACKING.json):
{
  "schema_version": "1.0.0",
  "updated_at": "<ISO timestamp>",
  "persons": [
    {
      "slug": str,
      "bucket": str,
      "domains": [str],
      "themes": [str],
      "last_updated": str
    }
  ]
}

Story: MCE-17.0 — Fase 2 T7
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from typing import TypedDict
except ImportError:  # Python < 3.8 fallback
    from typing_extensions import TypedDict  # type: ignore[assignment]

try:
    from engine.paths import ARTIFACTS as _ARTIFACTS

    _DEFAULT_PATH = _ARTIFACTS / "ROLE-TRACKING.json"
except ImportError:
    # Fallback when engine.paths is unavailable (e.g. standalone test)
    _DEFAULT_PATH = Path(".data/artifacts/ROLE-TRACKING.json")


class PersonRecord(TypedDict, total=False):
    """Single person entry in ROLE-TRACKING.json persons list."""

    slug: str
    bucket: str
    domains: list[str]
    themes: list[str]
    last_updated: str


class RoleTrackingSchema(TypedDict, total=False):
    """Root schema of ROLE-TRACKING.json."""

    schema_version: str
    updated_at: str
    persons: list[PersonRecord]


def load_role_tracking(path: Path | None = None) -> RoleTrackingSchema:
    """Load ROLE-TRACKING.json with schema validation.

    Returns ``{"persons": []}`` if the file is missing.
    Raises ``ValueError`` if the root structure is not a dict or if
    ``persons`` is present but is not a list.

    Args:
        path: Optional override path. Defaults to the canonical artifact path
              (``.data/artifacts/ROLE-TRACKING.json`` resolved via engine.paths).

    Returns:
        RoleTrackingSchema dict. The ``persons`` key is always present and is
        always a list — callers can safely iterate without guarding for None.
    """
    p = path if path is not None else _DEFAULT_PATH

    if not p.exists():
        return {"persons": []}

    raw: Any = json.loads(p.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise ValueError(
            f"ROLE-TRACKING root must be a dict, got {type(raw).__name__!r}"
        )

    if "persons" not in raw:
        # Missing key — treat as empty rather than hard-fail (migration safety).
        return {"persons": []}

    if not isinstance(raw["persons"], list):
        raise ValueError(
            f"ROLE-TRACKING.persons must be a list, got "
            f"{type(raw['persons']).__name__!r}"
        )

    return raw  # type: ignore[return-value]


def iter_persons(rt: RoleTrackingSchema) -> list[PersonRecord]:
    """Return the persons list from a loaded RoleTrackingSchema.

    Always returns a list — never ``None``.  Callers can iterate directly::

        for person in iter_persons(rt):
            do_something(person["slug"])
    """
    return rt.get("persons") or []


def find_person(rt: RoleTrackingSchema, slug: str) -> PersonRecord | None:
    """Return the PersonRecord whose ``slug`` matches, or ``None``.

    Args:
        rt: A loaded RoleTrackingSchema (from :func:`load_role_tracking`).
        slug: The person slug to find (e.g. ``"cole-gordon"``).

    Returns:
        The matching ``PersonRecord`` dict, or ``None`` if not found.
    """
    for person in iter_persons(rt):
        if isinstance(person, dict) and person.get("slug") == slug:
            return person
    return None
