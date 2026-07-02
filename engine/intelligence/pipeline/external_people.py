"""external_people.py -- External/Expert party lookup for entity routing.
=========================================================================

Single source of truth for answering one question during ingestion:

    classify(name) -> slug | None
       "Does this candidate name map to a KNOWN external expert (someone who
        already has an agent persona on disk OR is registered as an external
        partner)?"  Returns the canonical kebab-case slug ("alex-hormozi").

WHY THIS EXISTS
---------------
The filename parser (``batch_auto_creator.parse_filename_evidence``) turns
ANY 2-3 consecutive Title-Case tokens into a "person" candidate. So a book
titled "100M Playbook Pricing (Alex Hormozi) (Z-Library)" yields persons
like ["Playbook Pricing", "Alex Hormozi"] — and the REAL author loses to
the fake one because ``infer_entities`` blindly took ``persons[0]``.

There was NO check against the experts we ALREADY know. The directory
``agents/external/alex-hormozi/`` exists, but nothing in the routing path
ever consulted it. ``internal_people.py`` already provides the symmetric
slot for founder/collaborators; this module is its external counterpart.

With this module, ``infer_entities`` can iterate the filename person
candidates and pick the FIRST one that resolves to a known external slug,
overriding the positional ``persons[0]`` default. "Alex Hormozi" wins over
"Playbook Pricing" because Alex Hormozi is a known expert and Playbook
Pricing is not.

DATA SOURCES (union, cheap + cached)
------------------------------------
    A. agents/external/* directories — the strongest signal. Each dir name
       IS a canonical expert slug (alex-hormozi, cole-gordon, ...). The
       ``_*`` / ``example`` / ``cargo`` scaffolding dirs are excluded.
    B. partners-registry external slugs (engine.intelligence.partners.
       list_external_slugs) — external-bucket partners + ``external_force``
       aliases. These are ALSO accepted as known external slugs.

NORMALIZATION
-------------
A candidate name ("Alex Hormozi") is slugified ("alex-hormozi") and matched
against the known-slug set, accent-insensitive. We additionally register the
slug-derived NAME form ("alex hormozi") so a name lookup resolves even if the
caller passes a spaced display name. Mirrors internal_people.py exactly.

Tolerances (fail-open):
    - Missing agents/external dir  -> registry slugs only.
    - Missing PyYAML / registry    -> directory slugs only.
    - Malformed entries            -> skipped individually.

Cache: process-level dict with a 60s monotonic TTL (mirrors
internal_people.py / partners.py).

Story: STORY-ONDA1-author-routing (2026-06-27).
Epic: MCE-INGESTION-INTEGRITY.
"""

from __future__ import annotations

import re
import time
import unicodedata
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

# engine/intelligence/pipeline/external_people.py -> repo root is parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]
EXTERNAL_AGENTS_DIR = REPO_ROOT / "agents" / "external"

# Directory names under agents/external/ that are scaffolding / non-expert and
# must NEVER be treated as a known external person slug.
_EXCLUDED_EXTERNAL_DIRS: frozenset[str] = frozenset(
    {
        "_example",
        "example",
        "cargo",
        "_registry",
        "_template",
        "_templates",
    }
)

# ---------------------------------------------------------------------------
# CACHE
# ---------------------------------------------------------------------------

_CACHE: dict[str, Any] = {"index": None, "loaded_at": 0.0}
_CACHE_TTL_S = 60.0


# ---------------------------------------------------------------------------
# NORMALIZATION HELPERS  (identical contract to internal_people.py)
# ---------------------------------------------------------------------------


def _strip_accents(s: str) -> str:
    """Remove combining accents so 'Conceição' matches 'conceicao'."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _norm_name(name: str) -> str:
    """Lowercase, accent-stripped, whitespace-collapsed name key."""
    s = _strip_accents(name or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _slugify(name: str) -> str:
    """Title/spaced name -> kebab-case slug. Mirrors batch_auto_creator._slugify."""
    s = _strip_accents(name or "").lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def _slug_to_name(slug: str) -> str:
    """'alex-hormozi' -> 'alex hormozi' (normalized name key)."""
    return _norm_name(slug.replace("-", " "))


# ---------------------------------------------------------------------------
# INDEX BUILD
# ---------------------------------------------------------------------------


def _discover_agent_slugs() -> set[str]:
    """Slugs from agents/external/* directories (excluding scaffolding)."""
    slugs: set[str] = set()
    if not EXTERNAL_AGENTS_DIR.is_dir():
        return slugs
    try:
        for child in EXTERNAL_AGENTS_DIR.iterdir():
            if not child.is_dir():
                continue
            name = child.name
            if name.startswith(".") or name in _EXCLUDED_EXTERNAL_DIRS:
                continue
            # An expert dir is itself a canonical slug. Re-slugify to be safe
            # (accent-insensitive, collapses any stray separators).
            sl = _slugify(name)
            if sl:
                slugs.add(sl)
    except OSError:
        return slugs
    return slugs


def _registry_external_slugs() -> set[str]:
    """External slugs from the partners-registry (fail-open to empty)."""
    try:
        from engine.intelligence.partners import list_external_slugs

        slugs = list_external_slugs()
        return {s for s in slugs if isinstance(s, str) and s}
    except Exception:
        return set()


def _build_index() -> dict[str, Any]:
    """Build the external-people index from agent dirs + registry.

    Returns a dict with:
        by_slug:  set[str]                 (canonical known external slugs)
        by_name:  {normalized_name -> slug}  (slug-derived name spellings)
    """
    by_slug: set[str] = set()
    by_name: dict[str, str] = {}

    for sl in _discover_agent_slugs() | _registry_external_slugs():
        by_slug.add(sl)
        # Register the slug-derived name spelling so a spaced display name
        # ("alex hormozi") resolves the same as the slug ("alex-hormozi").
        nk = _slug_to_name(sl)
        if nk and nk not in by_name:
            by_name[nk] = sl

    return {"by_slug": by_slug, "by_name": by_name}


def _get_index(*, force: bool = False) -> dict[str, Any]:
    now = time.monotonic()
    idx = _CACHE["index"]
    if not force and idx is not None and (now - _CACHE["loaded_at"]) < _CACHE_TTL_S:
        return idx  # type: ignore[return-value]
    idx = _build_index()
    _CACHE["index"] = idx
    _CACHE["loaded_at"] = now
    return idx


def reset_cache() -> None:
    """Force the next lookup to rebuild the index (used by tests)."""
    _CACHE["index"] = None
    _CACHE["loaded_at"] = 0.0


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------


def classify(name: str) -> str | None:
    """Return the canonical external slug if known, else None.

    Accepts a raw display name ("Alex Hormozi") or a kebab-case slug
    ("alex-hormozi"). Matching is accent-insensitive. Resolution order:

        1. Exact slug (the candidate is already kebab-case and known).
        2. Slugified name ("Alex Hormozi" -> "alex-hormozi", known).
        3. Normalized-name table (slug-derived spellings).

    Returns None when the candidate is NOT a known external expert — the
    caller then falls back to its positional default.
    """
    if not name or not isinstance(name, str):
        return None

    idx = _get_index()
    raw = name.strip()

    # 1. Exact slug path.
    candidate_slug = raw.lower()
    if candidate_slug in idx["by_slug"]:
        return candidate_slug

    # 2. Slugified name path ("Alex Hormozi" -> "alex-hormozi").
    slugged = _slugify(raw)
    if slugged in idx["by_slug"]:
        return slugged

    # 3. Normalized-name table (slug-derived spellings).
    nkey = _norm_name(raw)
    if nkey in idx["by_name"]:
        return idx["by_name"][nkey]

    return None


def is_external(name: str) -> bool:
    """True iff the candidate maps to a known external expert."""
    return classify(name) is not None


def list_known_slugs() -> set[str]:
    """Return the current set of known external slugs (diagnostic)."""
    return set(_get_index()["by_slug"])
