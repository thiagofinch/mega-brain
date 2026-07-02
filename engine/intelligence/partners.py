"""Partners Registry — CLI + library for external partners catalog.

Reads/writes ``workspace/_system/partners-registry.yaml`` (single source
of truth for parceiros, prestadores, vendors that are NOT your own BUs).

Used by:
    - scripts/ingest-with-entity-discovery.py::decide_destination (AC-3)
    - engine/intelligence/pipeline/batch_auto_creator.py::infer_entities (AC-4)

CLI:
    python3 -m engine.intelligence.partners list
    python3 -m engine.intelligence.partners get <slug>
    python3 -m engine.intelligence.partners add --slug X --domain Y --bucket business
    python3 -m engine.intelligence.partners lookup-domain <domain>

Library:
    from engine.intelligence.partners import (
        load_registry, get_partner, lookup_by_domain,
        list_business_slugs, list_external_slugs,
    )

Story: MCE-INGEST-ROBUSTNESS (Wave 2, AC-6) — 2026-05-27.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # graceful — CLI will warn, library returns empty registry

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "workspace" / "_system" / "partners-registry.yaml"

# In-memory cache (60s TTL — AC-3 constraint)
_CACHE: dict[str, Any] = {"data": None, "loaded_at": 0.0}
_CACHE_TTL_S = 60.0


def _load_yaml_safe(path: Path) -> dict[str, Any]:
    """Read YAML, fail-open (returns empty registry on any error)."""
    if yaml is None:
        return {"partners": [], "aliases": {}, "version": "fallback"}
    if not path.exists():
        return {"partners": [], "aliases": {}, "version": "missing"}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            return {"partners": [], "aliases": {}, "version": "invalid-shape"}
        data.setdefault("partners", [])
        data.setdefault("aliases", {})
        return data
    except Exception:
        return {"partners": [], "aliases": {}, "version": "parse-error"}


def load_registry(*, force: bool = False) -> dict[str, Any]:
    """Load registry with 60s TTL cache."""
    now = time.monotonic()
    if not force and _CACHE["data"] is not None and (now - _CACHE["loaded_at"]) < _CACHE_TTL_S:
        return _CACHE["data"]  # type: ignore[return-value]
    data = _load_yaml_safe(REGISTRY_PATH)
    _CACHE["data"] = data
    _CACHE["loaded_at"] = now
    return data


def get_partner(slug: str) -> dict[str, Any] | None:
    """Return partner dict by slug, or None."""
    registry = load_registry()
    for p in registry.get("partners", []):
        if isinstance(p, dict) and p.get("slug") == slug:
            return p
    return None


def lookup_by_domain(domain: str) -> dict[str, Any] | None:
    """Find partner that owns the given email domain (case-insensitive)."""
    d = domain.lower().strip()
    if d.startswith("@"):
        d = d[1:]
    registry = load_registry()
    for p in registry.get("partners", []):
        if not isinstance(p, dict):
            continue
        for owned in p.get("domains", []) or []:
            if isinstance(owned, str) and owned.lower() == d:
                return p
    return None


def list_business_slugs() -> set[str]:
    """All slugs that map to business bucket (partners + aliases.business_force).

    Note: business UNIT slugs (workspace/businesses/*) are discovered by the
    caller separately — this function only covers PARTNERS that route to
    business. The two are merged at decide_destination.
    """
    registry = load_registry()
    slugs: set[str] = set()
    for p in registry.get("partners", []):
        if isinstance(p, dict) and p.get("bucket") == "business":
            sl = p.get("slug")
            if isinstance(sl, str):
                slugs.add(sl)
    aliases = registry.get("aliases", {}) or {}
    for sl in aliases.get("business_force", []) or []:
        if isinstance(sl, str):
            slugs.add(sl)
    return slugs


def list_external_slugs() -> set[str]:
    """All slugs explicitly forced to external bucket."""
    registry = load_registry()
    slugs: set[str] = set()
    for p in registry.get("partners", []):
        if isinstance(p, dict) and p.get("bucket") == "external":
            sl = p.get("slug")
            if isinstance(sl, str):
                slugs.add(sl)
    aliases = registry.get("aliases", {}) or {}
    for sl in aliases.get("external_force", []) or []:
        if isinstance(sl, str):
            slugs.add(sl)
    return slugs


def list_business_units() -> set[str]:
    """Discover business-unit slugs from filesystem (workspace/businesses/*).

    Returns kebab-case dir names. Returns an empty set if the workspace dir
    is missing (graceful degradation — BUs are discovered, never hardcoded).
    """
    workspace_dir = REPO_ROOT / "workspace" / "businesses"
    if workspace_dir.is_dir():
        return {p.name for p in workspace_dir.iterdir() if p.is_dir() and not p.name.startswith(".")}
    # Graceful degradation (AC-3): no workspace dir => no business units.
    return set()


def all_business_slugs() -> set[str]:
    """Union of business units + business-bucket partners + forced aliases."""
    return list_business_units() | list_business_slugs()


def add_partner(
    *,
    slug: str,
    display_name: str | None = None,
    company: str | None = None,
    domains: list[str] | None = None,
    relationship: str = "outro",
    bucket: str = "business",
    notes: str | None = None,
    added_via: str = "cli",
) -> dict[str, Any]:
    """Append a new partner to the registry. Fail if slug exists."""
    if yaml is None:
        raise RuntimeError("PyYAML not installed — cannot write registry")
    registry = _load_yaml_safe(REGISTRY_PATH)
    existing = [p for p in registry.get("partners", []) if isinstance(p, dict)]
    if any(p.get("slug") == slug for p in existing):
        raise ValueError(f"Partner with slug={slug!r} already exists")
    entry = {
        "slug": slug,
        "display_name": display_name or slug,
        "company": company,
        "domains": domains or [],
        "relationship": relationship,
        "bucket": bucket,
        "notes": notes,
        "added_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "added_via": added_via,
    }
    existing.append(entry)
    registry["partners"] = existing
    registry["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(registry, f, allow_unicode=True, sort_keys=False)
    # invalidate cache
    _CACHE["data"] = None
    return entry


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cmd_list(args: argparse.Namespace) -> int:
    registry = load_registry()
    partners = registry.get("partners", []) or []
    if args.json:
        print(json.dumps(partners, indent=2, ensure_ascii=False, default=str))
        return 0
    if not partners:
        print("(empty registry)")
        return 0
    print(f"{'SLUG':24s} {'BUCKET':10s} {'RELATIONSHIP':12s} {'DOMAINS':40s}  COMPANY")
    print("-" * 100)
    for p in partners:
        if not isinstance(p, dict):
            continue
        doms = ", ".join(p.get("domains", []) or [])[:38]
        print(
            f"{(p.get('slug') or '')[:24]:24s} "
            f"{(p.get('bucket') or '')[:10]:10s} "
            f"{(p.get('relationship') or '')[:12]:12s} "
            f"{doms:40s}  {p.get('company') or ''}"
        )
    print(f"\nTotal: {len(partners)} partner(s)")
    print(f"Business units (workspace/businesses/*): {sorted(list_business_units())}")
    return 0


def _cmd_get(args: argparse.Namespace) -> int:
    p = get_partner(args.slug)
    if not p:
        print(f"Not found: {args.slug}", file=sys.stderr)
        return 1
    print(json.dumps(p, indent=2, ensure_ascii=False, default=str))
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    try:
        entry = add_partner(
            slug=args.slug,
            display_name=args.display_name,
            company=args.company,
            domains=args.domain or [],
            relationship=args.relationship,
            bucket=args.bucket,
            notes=args.notes,
        )
    except (ValueError, RuntimeError) as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 1
    print(f"Added: {entry['slug']} -> bucket={entry['bucket']}")
    print(json.dumps(entry, indent=2, ensure_ascii=False))
    return 0


def _cmd_lookup(args: argparse.Namespace) -> int:
    p = lookup_by_domain(args.domain)
    if not p:
        print(f"No partner owns domain: {args.domain}", file=sys.stderr)
        return 1
    print(json.dumps(p, indent=2, ensure_ascii=False, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="partners",
        description="Partners Registry CLI (Story MCE-INGEST-ROBUSTNESS AC-6)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp_list = sub.add_parser("list", help="List all partners")
    sp_list.add_argument("--json", action="store_true")
    sp_list.set_defaults(func=_cmd_list)

    sp_get = sub.add_parser("get", help="Get a partner by slug")
    sp_get.add_argument("slug")
    sp_get.set_defaults(func=_cmd_get)

    sp_add = sub.add_parser("add", help="Add a new partner")
    sp_add.add_argument("--slug", required=True)
    sp_add.add_argument("--display-name")
    sp_add.add_argument("--company")
    sp_add.add_argument("--domain", action="append", help="Repeatable")
    sp_add.add_argument("--relationship", default="outro",
                         choices=["prestador", "parceiro", "cliente", "vendor", "investor", "outro"])
    sp_add.add_argument("--bucket", default="business",
                         choices=["business", "external", "personal"])
    sp_add.add_argument("--notes")
    sp_add.set_defaults(func=_cmd_add)

    sp_lk = sub.add_parser("lookup-domain", help="Find partner that owns a domain")
    sp_lk.add_argument("domain")
    sp_lk.set_defaults(func=_cmd_lookup)

    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
