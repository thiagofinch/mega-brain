"""internal_people.py -- Internal/Founder party lookup for entity routing.
=========================================================================

Single source of truth for answering two questions during ingestion:

    1. is_internal(name_or_email)        -> bool
       "Is this person an internal party (founder, collaborator, partner,
        advisor) of your organization's ecosystem?"

    2. match_collaborator(name_or_email) -> str | None
       "If internal, what is their canonical kebab-case slug AND what kind
        of relationship is it?"  (returns the slug; relationship_type is
        exposed via classify(...))

WHY THIS EXISTS
---------------
The pipeline previously routed any "person name in filename" to the
``external`` bucket (treated like an expert). That silently misclassified
PARTNER / NEGOTIATION / COLLABORATOR calls where the FOUNDER is himself a
participant. A founder in his own negotiation is a BUSINESS relationship,
never an external expert.

This module supplies the "internal-party present?" signal so
decide_destination / infer_entities can OVERRIDE the person->external
default when an internal/founder party is detected.

DATA SOURCES (union, cheap + cached)
------------------------------------
    A. Founder constants (from env — the strongest, always-present signal):
         emails:  any @<founder-domain> address + exact founder emails
         name:    founder display name (slug derived from it)
       Configure via environment variables (see FOUNDER CONSTANTS below):
         MEGA_BRAIN_OWNER_NAME, MEGA_BRAIN_OWNER_EMAIL,
         MEGA_BRAIN_FOUNDER_DOMAINS, MEGA_BRAIN_FOUNDER_EMAILS
    B. workspace/businesses/*/L0-identity/people-registry.yaml
         -> people[].{id,name,type,agent_category}
    C. workspace/businesses/*/L1-strategy/team-registry.yaml
         -> teams[].members[].person_id   (names not always present)

RELATIONSHIP TYPE
-----------------
A matched internal party is classified into one of:
    "founder"      -> type == founder  (the configured owner)
    "collaborator" -> type in {employee, contractor} OR agent_category
                      contains "collaborators", OR present only in a
                      team-registry (team membership == collaborator)
    "partner"      -> type == partner  / agent_category contains "partners"
    "advisor"      -> type == advisor  / agent_category contains "advisors"

A counterpart who is NOT internal is classified by the CALLER as
"partner" / "negotiation" (an external party in a founder call). That
decision lives in decide_destination, not here — this module only knows
about INTERNAL people.

Tolerances (fail-open):
    - Missing PyYAML            -> founder constants only.
    - Missing/partial registry  -> skip that file, keep going.
    - Malformed entries         -> skipped individually.

Cache: process-level dict with a 60s monotonic TTL (mirrors partners.py).

Story: STORY-MCE-FOUNDER-ROUTING (2026-06-09).
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment without PyYAML
    yaml = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

# engine/intelligence/pipeline/internal_people.py -> repo root is parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]
BUSINESSES_DIR = REPO_ROOT / "workspace" / "businesses"

# ---------------------------------------------------------------------------
# FOUNDER CONSTANTS (always-present signal, independent of registries)
# ---------------------------------------------------------------------------
# All values are configured via environment variables so the engine ships
# free of any organization-specific identity. Defaults are empty (no founder
# constants) — the module then relies purely on the workspace registries
# (sources B and C). Configure these for your own organization:
#
#   MEGA_BRAIN_OWNER_NAME       e.g. "Jane Doe"            (founder display name)
#   MEGA_BRAIN_OWNER_EMAIL      e.g. "jane@example.com"    (exact founder email)
#   MEGA_BRAIN_FOUNDER_DOMAINS  e.g. "example.com,example.com.br" (host domains)
#   MEGA_BRAIN_FOUNDER_EMAILS   e.g. "contact@example.com,info@example.com"


def _env_set(var: str) -> frozenset[str]:
    """Parse a comma-separated env var into a lowercase frozenset (empty if unset)."""
    raw = os.environ.get(var, "")
    return frozenset(item.strip().lower() for item in raw.split(",") if item.strip())


# Email domains that ALWAYS belong to the host/founder side.
FOUNDER_DOMAINS: frozenset[str] = _env_set("MEGA_BRAIN_FOUNDER_DOMAINS")

# Exact founder emails (in addition to any @<FOUNDER_DOMAIN> address).
_owner_email_env = os.environ.get("MEGA_BRAIN_OWNER_EMAIL", "").strip().lower()
FOUNDER_EMAILS: frozenset[str] = _env_set("MEGA_BRAIN_FOUNDER_EMAILS") | (
    frozenset({_owner_email_env}) if _owner_email_env else frozenset()
)

# Founder identity. slug -> set of normalized name spellings (derived from the
# configured owner name; empty when no owner name is configured).
_owner_name_env = os.environ.get("MEGA_BRAIN_OWNER_NAME", "").strip()
FOUNDER_SLUG = (
    re.sub(r"-+", "-", re.sub(r"[\s_]+", "-", re.sub(r"[^\w\s-]", "", _owner_name_env.lower())))
    .strip("-")
    if _owner_name_env
    else ""
)


def _derive_founder_names(name: str) -> frozenset[str]:
    """Build the set of normalized name spellings recognized for the founder.

    Includes the full name plus each individual token (so "Jane" or "Doe"
    alone still resolves). Empty when no name is configured.
    """
    if not name:
        return frozenset()
    norm = re.sub(r"\s+", " ", name.lower().strip())
    spellings = {norm}
    spellings.update(tok for tok in norm.split(" ") if tok)
    return frozenset(spellings)


FOUNDER_NAMES: frozenset[str] = _derive_founder_names(_owner_name_env)

# Relationship types this module can emit for an INTERNAL match.
RELATIONSHIP_FOUNDER = "founder"
RELATIONSHIP_COLLABORATOR = "collaborator"
RELATIONSHIP_PARTNER = "partner"
RELATIONSHIP_ADVISOR = "advisor"

# ---------------------------------------------------------------------------
# CACHE
# ---------------------------------------------------------------------------

_CACHE: dict[str, Any] = {"index": None, "loaded_at": 0.0}
_CACHE_TTL_S = 60.0

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}")


# ---------------------------------------------------------------------------
# NORMALIZATION HELPERS
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


def _looks_like_email(token: str) -> bool:
    return "@" in token and bool(_EMAIL_RE.search(token))


def _extract_email(token: str) -> str | None:
    m = _EMAIL_RE.search(token or "")
    return m.group(0).lower() if m else None


def _slug_to_name(slug: str) -> str:
    """'jane-doe' -> 'jane doe' (normalized name key)."""
    return _norm_name(slug.replace("-", " "))


def _relationship_from_entry(person_type: str | None, agent_category: str | None) -> str:
    """Map a people-registry entry to a relationship_type.

    Priority: explicit ``type`` field, then ``agent_category`` substring.
    Defaults to collaborator (team membership implies collaboration).
    """
    t = (person_type or "").lower().strip()
    cat = (agent_category or "").lower()

    if t == "founder":
        return RELATIONSHIP_FOUNDER
    if t == "partner":
        return RELATIONSHIP_PARTNER
    if t == "advisor":
        return RELATIONSHIP_ADVISOR
    if t in {"employee", "contractor"}:
        return RELATIONSHIP_COLLABORATOR

    # Fall back to agent_category hints.
    if "partners" in cat:
        return RELATIONSHIP_PARTNER
    if "advisors" in cat:
        return RELATIONSHIP_ADVISOR
    if "collaborators" in cat or "personal" in cat:
        return RELATIONSHIP_COLLABORATOR

    return RELATIONSHIP_COLLABORATOR


# ---------------------------------------------------------------------------
# INDEX BUILD
# ---------------------------------------------------------------------------


def _load_yaml_safe(path: Path) -> dict[str, Any] | None:
    if yaml is None or not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _build_index() -> dict[str, Any]:
    """Build the internal-people index from founder constants + registries.

    Returns a dict with:
        by_name:  {normalized_name -> (slug, relationship_type)}
        by_slug:  {slug -> relationship_type}
        emails:   set[str]      (exact founder emails)
        domains:  set[str]      (founder email domains)
    """
    by_name: dict[str, tuple[str, str]] = {}
    by_slug: dict[str, str] = {}

    # --- A. Founder constants (only when an owner identity is configured) -
    if FOUNDER_SLUG:
        for nm in FOUNDER_NAMES:
            by_name[_norm_name(nm)] = (FOUNDER_SLUG, RELATIONSHIP_FOUNDER)
        by_slug[FOUNDER_SLUG] = RELATIONSHIP_FOUNDER

    def _register(slug: str, name: str | None, rel: str) -> None:
        slug = (slug or "").strip()
        if not slug:
            if name:
                slug = _slugify(name)
            if not slug:
                return
        # Founder always wins; never downgrade.
        if slug == FOUNDER_SLUG:
            rel = RELATIONSHIP_FOUNDER
        by_slug.setdefault(slug, rel)
        # Register name spellings (explicit name + slug-derived name).
        name_keys = set()
        if name:
            name_keys.add(_norm_name(name))
        name_keys.add(_slug_to_name(slug))
        for nk in name_keys:
            if nk and nk not in by_name:
                by_name[nk] = (slug, by_slug.get(slug, rel))

    if BUSINESSES_DIR.is_dir():
        for biz_dir in sorted(BUSINESSES_DIR.iterdir()):
            if not biz_dir.is_dir() or biz_dir.name.startswith("."):
                continue

            # --- B. people-registry.yaml -------------------------------
            pr = _load_yaml_safe(biz_dir / "L0-identity" / "people-registry.yaml")
            if pr:
                people = pr.get("people")
                # people can be a list[dict] OR a dict (placeholder {}).
                if isinstance(people, list):
                    for p in people:
                        if not isinstance(p, dict):
                            continue
                        rel = _relationship_from_entry(
                            p.get("type"), p.get("agent_category")
                        )
                        _register(
                            slug=str(p.get("id") or ""),
                            name=p.get("name"),
                            rel=rel,
                        )

            # --- C. team-registry.yaml (membership => collaborator) ----
            tr = _load_yaml_safe(biz_dir / "L1-strategy" / "team-registry.yaml")
            if tr:
                teams = tr.get("teams")
                if isinstance(teams, list):
                    for team in teams:
                        if not isinstance(team, dict):
                            continue
                        members = team.get("members")
                        if not isinstance(members, list):
                            continue
                        for m in members:
                            if not isinstance(m, dict):
                                continue
                            pid = str(m.get("person_id") or "").strip()
                            if not pid:
                                continue
                            # Only ADD if not already classified by a
                            # people-registry (which carries richer type info).
                            if pid not in by_slug:
                                _register(
                                    slug=pid,
                                    name=m.get("name"),
                                    rel=RELATIONSHIP_COLLABORATOR,
                                )

    return {
        "by_name": by_name,
        "by_slug": by_slug,
        "emails": set(FOUNDER_EMAILS),
        "domains": set(FOUNDER_DOMAINS),
    }


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


def classify(name_or_email: str) -> tuple[str, str] | None:
    """Return (slug, relationship_type) if internal, else None.

    Accepts a raw name ("Jane Doe"), a slug ("jane-doe"), or an
    email ("jane@example.com" / "contact@example.com"). Email match
    wins (it is the strongest signal); then slug; then normalized name.
    """
    if not name_or_email or not isinstance(name_or_email, str):
        return None

    idx = _get_index()
    raw = name_or_email.strip()

    # 1. Email path (strongest).
    if _looks_like_email(raw):
        email = _extract_email(raw)
        if email:
            if email in idx["emails"]:
                return (FOUNDER_SLUG, RELATIONSHIP_FOUNDER)
            domain = email.rsplit("@", 1)[-1]
            if domain in idx["domains"]:
                # Any @founder-domain address is the founder side.
                return (FOUNDER_SLUG, RELATIONSHIP_FOUNDER)
        # An email NOT on a founder domain is not internal (here).
        return None

    # 2. Slug path (exact kebab-case).
    candidate_slug = raw.lower()
    if candidate_slug in idx["by_slug"]:
        return (candidate_slug, idx["by_slug"][candidate_slug])

    # 3. Name path (accent-insensitive). Try full, then slugified form.
    nkey = _norm_name(raw)
    if nkey in idx["by_name"]:
        return idx["by_name"][nkey]

    slugged = _slugify(raw)
    if slugged in idx["by_slug"]:
        return (slugged, idx["by_slug"][slugged])

    # 4. Founder partial-name fallback (e.g. a single name token alone).
    if nkey in FOUNDER_NAMES:
        return (FOUNDER_SLUG, RELATIONSHIP_FOUNDER)

    return None


def is_internal(name_or_email: str) -> bool:
    """True iff the person is an internal party (founder/collaborator/...)."""
    return classify(name_or_email) is not None


def is_founder(name_or_email: str) -> bool:
    """True iff the person is specifically the founder (the configured owner)."""
    result = classify(name_or_email)
    return bool(result and result[1] == RELATIONSHIP_FOUNDER)


def match_collaborator(name_or_email: str) -> str | None:
    """Return the canonical slug if the person is internal, else None.

    Named ``match_collaborator`` per the founder directive: it answers
    "does this counterpart map to a known internal person (collaborator
    table)?". The relationship granularity is available via classify().
    """
    result = classify(name_or_email)
    return result[0] if result else None


def relationship_type(name_or_email: str) -> str | None:
    """Return the relationship_type string if internal, else None."""
    result = classify(name_or_email)
    return result[1] if result else None
