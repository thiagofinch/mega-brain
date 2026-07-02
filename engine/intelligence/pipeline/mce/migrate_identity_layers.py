#!/usr/bin/env python3
"""
MIGRATE IDENTITY LAYERS - L9 (Obsessions) & L10 (Paradoxes)
=============================================================
Promotes obsessions and paradoxes from inline INSIGHTS-STATE.json
fields to standalone YAML files per person.

Sources (checked in priority order):
    1. artifacts/mce/{slug}/INSIGHTS-STATE.json  (primary - Step 7 extraction)
    2. knowledge/external/dna/persons/{slug}/VALUES-HIERARCHY.yaml  (legacy, if exists)
    3. knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml  (legacy, if exists)

Outputs (per person):
    knowledge/external/dna/persons/{slug}/OBSESSIONS.yaml   (L9)
    knowledge/external/dna/persons/{slug}/PARADOXES.yaml     (L10)

Behavior:
    - DOES NOT delete from source files (backward compatibility)
    - Merges obsessions/paradoxes from all sources, deduplicating by ID
    - Skips persons that already have standalone files (unless --force)
    - --dry-run mode shows what would happen without writing

Version: 1.0.0
Date: 2026-03-27
Story: Phase 1 - L9/L10 Promotion
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(_ROOT))

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

_PERSONS_DIR = _ROOT / "knowledge" / "external" / "dna" / "persons"
_ARTIFACTS_MCE_DIR = _ROOT / "artifacts" / "mce"
_GLOBAL_INSIGHTS = _ROOT / "artifacts" / "insights" / "INSIGHTS-STATE.json"


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> dict[str, Any]:
    """Read a JSON file, returning empty dict on failure.

    Handles both wrapped and unwrapped INSIGHTS-STATE.json formats:
      - Unwrapped: ``{"obsessions": {...}, "paradoxes": {...}, ...}``
      - Wrapped: ``{"insights_state": {"obsessions": {...}, ...}}``
    """
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        # Unwrap insights_state envelope if present
        if "insights_state" in data and isinstance(data["insights_state"], dict):
            data = data["insights_state"]
        return data
    except Exception:
        logger.warning("Failed to parse JSON: %s", path)
        return {}


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML file, returning empty dict on failure."""
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        logger.warning("Failed to parse YAML: %s", path)
        return {}


def _write_yaml(path: Path, content: str) -> None:
    """Write YAML string to a file, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _normalize_to_slug(name: str) -> str:
    """Convert a person name to slug form, stripping accents.

    "Jane Doe" -> "jane-doe"
    "Sam Ovens" -> "sam-ovens"
    """
    # Decompose unicode, strip combining marks (accents)
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(c for c in nfkd if not unicodedata.combining(c))
    return ascii_name.lower().replace(" ", "-")


def _slug_to_person_name(slug: str, insights_data: dict[str, Any], key: str) -> str | None:
    """Find the person name key used in INSIGHTS-STATE.json for a given slug.

    The INSIGHTS-STATE.json uses human-readable names as keys (e.g. "Alex Hormozi",
    "Sam Ovens", "Jane Doe") but we need to match them to directory slugs
    (e.g. "alex-hormozi", "sam-oven", "jane-doe").

    Matching strategy:
      1. Exact match after slugifying the person name (handles accents)
      2. Slug is a prefix of the slugified person name (handles truncation like sam-oven vs sam-ovens)
      3. Slugified person name starts with the slug (reversed prefix check)
    """
    section = insights_data.get(key, {})
    if not isinstance(section, dict):
        return None
    for person_name in section:
        candidate_slug = _normalize_to_slug(person_name)
        # Exact match
        if candidate_slug == slug:
            return person_name
        # Prefix match (slug is truncated form of full name)
        if candidate_slug.startswith(slug) or slug.startswith(candidate_slug):
            return person_name
    return None


def _dedup_by_id(items: list[dict]) -> list[dict]:
    """Deduplicate a list of dicts by their 'id' field, keeping first occurrence."""
    seen: set[str] = set()
    result: list[dict] = []
    for item in items:
        item_id = item.get("id", "")
        if item_id and item_id in seen:
            continue
        if item_id:
            seen.add(item_id)
        result.append(item)
    return result


# ---------------------------------------------------------------------------
# SOURCE READERS
# ---------------------------------------------------------------------------


def _read_obsessions_from_insights(slug: str) -> tuple[list[dict], str]:
    """Read obsessions from INSIGHTS-STATE.json for a given slug.

    Checks per-person file first, then falls back to global INSIGHTS-STATE.json.
    Returns (obsessions_list, person_name).
    """
    # Per-person INSIGHTS-STATE.json (primary)
    insights_path = _ARTIFACTS_MCE_DIR / slug / "INSIGHTS-STATE.json"
    data = _read_json(insights_path)
    if data:
        person_name = _slug_to_person_name(slug, data, "obsessions")
        if person_name:
            items = data.get("obsessions", {}).get(person_name, [])
            if isinstance(items, list) and items:
                return items, person_name

    # Global INSIGHTS-STATE.json (fallback)
    global_data = _read_json(_GLOBAL_INSIGHTS)
    if global_data:
        person_name = _slug_to_person_name(slug, global_data, "obsessions")
        if person_name:
            items = global_data.get("obsessions", {}).get(person_name, [])
            if isinstance(items, list) and items:
                return items, person_name

    return [], ""


def _read_paradoxes_from_insights(slug: str) -> tuple[list[dict], str]:
    """Read paradoxes from INSIGHTS-STATE.json for a given slug.

    Checks per-person file first, then falls back to global INSIGHTS-STATE.json.
    Returns (paradoxes_list, person_name).
    """
    # Per-person INSIGHTS-STATE.json (primary)
    insights_path = _ARTIFACTS_MCE_DIR / slug / "INSIGHTS-STATE.json"
    data = _read_json(insights_path)
    if data:
        person_name = _slug_to_person_name(slug, data, "paradoxes")
        if person_name:
            items = data.get("paradoxes", {}).get(person_name, [])
            if isinstance(items, list) and items:
                return items, person_name

    # Global INSIGHTS-STATE.json (fallback)
    global_data = _read_json(_GLOBAL_INSIGHTS)
    if global_data:
        person_name = _slug_to_person_name(slug, global_data, "paradoxes")
        if person_name:
            items = global_data.get("paradoxes", {}).get(person_name, [])
            if isinstance(items, list) and items:
                return items, person_name

    return [], ""


def _read_obsessions_from_values_hierarchy(slug: str) -> list[dict]:
    """Read obsessions from VALUES-HIERARCHY.yaml (legacy location)."""
    path = _PERSONS_DIR / slug / "VALUES-HIERARCHY.yaml"
    data = _read_yaml(path)
    items = data.get("obsessions", [])
    return items if isinstance(items, list) else []


def _read_paradoxes_from_values_hierarchy(slug: str) -> list[dict]:
    """Read paradoxes from VALUES-HIERARCHY.yaml (legacy location)."""
    path = _PERSONS_DIR / slug / "VALUES-HIERARCHY.yaml"
    data = _read_yaml(path)
    items = data.get("paradoxes", [])
    return items if isinstance(items, list) else []


def _read_obsessions_from_voice_dna(slug: str) -> list[dict]:
    """Read obsessions from VOICE-DNA.yaml (legacy location)."""
    path = _PERSONS_DIR / slug / "VOICE-DNA.yaml"
    data = _read_yaml(path)
    items = data.get("obsessions", data.get("obsessoes", []))
    return items if isinstance(items, list) else []


def _read_paradoxes_from_voice_dna(slug: str) -> list[dict]:
    """Read paradoxes from VOICE-DNA.yaml (legacy location)."""
    path = _PERSONS_DIR / slug / "VOICE-DNA.yaml"
    data = _read_yaml(path)
    items = data.get("paradoxes", data.get("paradoxos", []))
    return items if isinstance(items, list) else []


# ---------------------------------------------------------------------------
# YAML GENERATORS
# ---------------------------------------------------------------------------


def _generate_obsessions_yaml(person_name: str, obsessions: list[dict], slug: str) -> str:
    """Generate the content of an OBSESSIONS.yaml file."""
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    header = (
        f"# knowledge/external/dna/persons/{slug}/OBSESSIONS.yaml\n"
        f"# Gerado em: {now[:10]} (Migration: L9 Promotion)\n"
        f"# Fonte: artifacts/mce/{slug}/INSIGHTS-STATE.json + legacy sources\n"
        f"# Versao: 1.0.0\n"
        f"\n"
    )

    data: dict[str, Any] = {
        "pessoa": person_name,
        "versao": "1.0.0",
        "data_extracao": now,
        "layer": "L9",
        "layer_name": "Obsessions",
        "total_obsessions": len(obsessions),
        "source_pipeline_step": "Step 7 - Identity Extraction (migrated)",
        "obsessions": obsessions,
    }

    body = yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )

    return header + body


def _generate_paradoxes_yaml(person_name: str, paradoxes: list[dict], slug: str) -> str:
    """Generate the content of a PARADOXES.yaml file."""
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    header = (
        f"# knowledge/external/dna/persons/{slug}/PARADOXES.yaml\n"
        f"# Gerado em: {now[:10]} (Migration: L10 Promotion)\n"
        f"# Fonte: artifacts/mce/{slug}/INSIGHTS-STATE.json + legacy sources\n"
        f"# Versao: 1.0.0\n"
        f"\n"
    )

    data: dict[str, Any] = {
        "pessoa": person_name,
        "versao": "1.0.0",
        "data_extracao": now,
        "layer": "L10",
        "layer_name": "Paradoxes",
        "total_paradoxes": len(paradoxes),
        "source_pipeline_step": "Step 7 - Identity Extraction (migrated)",
        "paradoxes": paradoxes,
    }

    body = yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )

    return header + body


# ---------------------------------------------------------------------------
# MIGRATION LOGIC
# ---------------------------------------------------------------------------


def migrate_person(slug: str, *, dry_run: bool = False, force: bool = False) -> dict[str, Any]:
    """Migrate obsessions and paradoxes for a single person.

    Returns a report dict with keys: slug, person_name, obsessions_count,
    paradoxes_count, files_created, skipped, errors.
    """
    person_dir = _PERSONS_DIR / slug
    report: dict[str, Any] = {
        "slug": slug,
        "person_name": "",
        "obsessions_count": 0,
        "paradoxes_count": 0,
        "files_created": [],
        "skipped": [],
        "errors": [],
    }

    if not person_dir.exists():
        report["errors"].append(f"Person directory does not exist: {person_dir}")
        return report

    # --- Collect obsessions from all sources ---
    all_obsessions: list[dict] = []
    obs_from_insights, person_name_obs = _read_obsessions_from_insights(slug)
    all_obsessions.extend(obs_from_insights)

    obs_from_vh = _read_obsessions_from_values_hierarchy(slug)
    all_obsessions.extend(obs_from_vh)

    obs_from_vd = _read_obsessions_from_voice_dna(slug)
    all_obsessions.extend(obs_from_vd)

    obsessions = _dedup_by_id(all_obsessions)

    # --- Collect paradoxes from all sources ---
    all_paradoxes: list[dict] = []
    par_from_insights, person_name_par = _read_paradoxes_from_insights(slug)
    all_paradoxes.extend(par_from_insights)

    par_from_vh = _read_paradoxes_from_values_hierarchy(slug)
    all_paradoxes.extend(par_from_vh)

    par_from_vd = _read_paradoxes_from_voice_dna(slug)
    all_paradoxes.extend(par_from_vd)

    paradoxes = _dedup_by_id(all_paradoxes)

    # Determine person name (prefer insights source)
    person_name = person_name_obs or person_name_par or slug.replace("-", " ").title()
    report["person_name"] = person_name
    report["obsessions_count"] = len(obsessions)
    report["paradoxes_count"] = len(paradoxes)

    # --- Write OBSESSIONS.yaml ---
    obs_path = person_dir / "OBSESSIONS.yaml"
    if obs_path.exists() and not force:
        report["skipped"].append(f"OBSESSIONS.yaml already exists for {slug}")
        logger.info("  [SKIP] %s/OBSESSIONS.yaml (already exists, use --force to overwrite)", slug)
    elif obsessions:
        content = _generate_obsessions_yaml(person_name, obsessions, slug)
        if dry_run:
            logger.info(
                "  [DRY-RUN] Would create %s/OBSESSIONS.yaml (%d obsessions)", slug, len(obsessions)
            )
            report["files_created"].append(f"{slug}/OBSESSIONS.yaml (dry-run)")
        else:
            _write_yaml(obs_path, content)
            logger.info("  [CREATED] %s/OBSESSIONS.yaml (%d obsessions)", slug, len(obsessions))
            report["files_created"].append(f"{slug}/OBSESSIONS.yaml")
    else:
        report["skipped"].append(f"No obsessions data found for {slug}")
        logger.info("  [SKIP] %s - no obsessions data in any source", slug)

    # --- Write PARADOXES.yaml ---
    par_path = person_dir / "PARADOXES.yaml"
    if par_path.exists() and not force:
        report["skipped"].append(f"PARADOXES.yaml already exists for {slug}")
        logger.info("  [SKIP] %s/PARADOXES.yaml (already exists, use --force to overwrite)", slug)
    elif paradoxes:
        content = _generate_paradoxes_yaml(person_name, paradoxes, slug)
        if dry_run:
            logger.info(
                "  [DRY-RUN] Would create %s/PARADOXES.yaml (%d paradoxes)", slug, len(paradoxes)
            )
            report["files_created"].append(f"{slug}/PARADOXES.yaml (dry-run)")
        else:
            _write_yaml(par_path, content)
            logger.info("  [CREATED] %s/PARADOXES.yaml (%d paradoxes)", slug, len(paradoxes))
            report["files_created"].append(f"{slug}/PARADOXES.yaml")
    else:
        report["skipped"].append(f"No paradoxes data found for {slug}")
        logger.info("  [SKIP] %s - no paradoxes data in any source", slug)

    return report


def migrate_all(*, dry_run: bool = False, force: bool = False) -> list[dict[str, Any]]:
    """Scan all person directories and migrate obsessions/paradoxes.

    Returns a list of per-person report dicts.
    """
    if not _PERSONS_DIR.exists():
        logger.error("Persons directory does not exist: %s", _PERSONS_DIR)
        return []

    slugs = sorted(
        d.name for d in _PERSONS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")
    )

    logger.info("Found %d person directories in %s", len(slugs), _PERSONS_DIR)

    reports: list[dict[str, Any]] = []
    for slug in slugs:
        logger.info("\nProcessing: %s", slug)
        report = migrate_person(slug, dry_run=dry_run, force=force)
        reports.append(report)

    return reports


# ---------------------------------------------------------------------------
# REPORTING
# ---------------------------------------------------------------------------


def _print_summary(reports: list[dict[str, Any]], dry_run: bool) -> None:
    """Print a summary table of migration results."""
    mode = "DRY-RUN" if dry_run else "MIGRATION"
    border = "=" * 72

    print(f"\n{border}")
    print(f"  L9/L10 IDENTITY LAYERS {mode} REPORT")
    print(border)

    total_persons = len(reports)
    total_obs = sum(r["obsessions_count"] for r in reports)
    total_par = sum(r["paradoxes_count"] for r in reports)
    total_files = sum(len(r["files_created"]) for r in reports)
    total_skipped = sum(len(r["skipped"]) for r in reports)
    total_errors = sum(len(r["errors"]) for r in reports)

    persons_with_data = sum(
        1 for r in reports if r["obsessions_count"] > 0 or r["paradoxes_count"] > 0
    )

    print(f"\n  Persons scanned:     {total_persons}")
    print(f"  Persons with data:   {persons_with_data}")
    print(f"  Total obsessions:    {total_obs}")
    print(f"  Total paradoxes:     {total_par}")
    print(f"  Files created:       {total_files}")
    print(f"  Skipped:             {total_skipped}")
    print(f"  Errors:              {total_errors}")

    if persons_with_data > 0:
        print(f"\n  {'Slug':<30} {'Person':<25} {'Obs':>4} {'Par':>4} {'Files':>6}")
        print(f"  {'-'*30} {'-'*25} {'-'*4} {'-'*4} {'-'*6}")
        for r in reports:
            if r["obsessions_count"] > 0 or r["paradoxes_count"] > 0:
                print(
                    f"  {r['slug']:<30} {r['person_name']:<25} "
                    f"{r['obsessions_count']:>4} {r['paradoxes_count']:>4} "
                    f"{len(r['files_created']):>6}"
                )

    if total_errors > 0:
        print("\n  ERRORS:")
        for r in reports:
            for err in r["errors"]:
                print(f"    [!] {r['slug']}: {err}")

    if total_skipped > 0 and not dry_run:
        print("\n  SKIPPED:")
        for r in reports:
            for skip in r["skipped"]:
                print(f"    [~] {skip}")

    print(f"\n{border}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for identity layers migration."""
    parser = argparse.ArgumentParser(
        description=(
            "Migrate obsessions (L9) and paradoxes (L10) from INSIGHTS-STATE.json "
            "to standalone YAML files per person."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would happen without writing files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing OBSESSIONS.yaml / PARADOXES.yaml files",
    )
    parser.add_argument(
        "--slug",
        type=str,
        default=None,
        help="Migrate only a specific person slug (e.g. alex-hormozi)",
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.dry_run:
        logger.info("[DRY-RUN MODE] No files will be written.\n")

    if args.slug:
        logger.info("Migrating single person: %s", args.slug)
        reports = [migrate_person(args.slug, dry_run=args.dry_run, force=args.force)]
    else:
        reports = migrate_all(dry_run=args.dry_run, force=args.force)

    _print_summary(reports, dry_run=args.dry_run)

    # Exit with error code if any errors occurred
    has_errors = any(r["errors"] for r in reports)
    if has_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
