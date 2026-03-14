#!/usr/bin/env python3
"""
NAVIGATION MAP BUILDER - Phase 2.3
====================================
Populates NAVIGATION-MAP.json with real section->chunk_id mappings.
Reads actual dossier files, extracts ## section headers, and finds
chunk_ids mentioned in each section's content.

Replaces _pending_mapping: true entries with actual section maps.

Zero external deps (stdlib + json only).

Versao: 1.0.0
Data: 2026-03-01
"""

import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # mega-brain/
NAV_MAP_PATH = BASE_DIR / "knowledge" / "NAVIGATION-MAP.json"
DOSSIERS_DIR = BASE_DIR / "knowledge" / "external" / "dossiers"

# Patterns for chunk_id references in dossier content
# Matches: CG001_010, AH-YT007_001, chunk_199, BATCH-041, etc.
CHUNK_ID_PATTERNS = [
    # Standard format: XX000_000
    re.compile(r"\b([A-Z]{2}\d{3}_\d{3})\b"),
    # Extended format: XX-YY000_000
    re.compile(r"\b([A-Z]{2}-[A-Z]{2,4}\d{3}_\d{3})\b"),
    # chunk_NNN format
    re.compile(r"\b(chunk_\d+)\b"),
    # Source ID format: XX-XXNNN
    re.compile(r"\b([A-Z]{2}-[A-Z]{2,4}\d{3})\b"),
]

# Pattern for BATCH references: [BATCH-041]
BATCH_PATTERN = re.compile(r"\[BATCH-(\d{3})\]")


# ---------------------------------------------------------------------------
# NAV MAP LOADER
# ---------------------------------------------------------------------------
def load_nav_map() -> dict:
    """Load NAVIGATION-MAP.json."""
    if not NAV_MAP_PATH.exists():
        return {
            "version": "2.0.0",
            "dossiers": {"persons": {}, "themes": {}},
        }
    with open(NAV_MAP_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_nav_map(nav_map: dict) -> None:
    """Save NAVIGATION-MAP.json with pretty formatting."""
    with open(NAV_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(nav_map, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# DOSSIER PARSER
# ---------------------------------------------------------------------------
def extract_sections_with_chunks(filepath: Path) -> dict[str, list[str]]:
    """Read a dossier file and extract section headers with their chunk_ids.

    Returns: {section_name: [chunk_id, ...]}
    """
    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    lines = content.split("\n")
    sections: dict[str, list[str]] = {}
    current_section = ""
    current_content: list[str] = []

    for line in lines:
        if line.startswith("## "):
            # Save previous section
            if current_section:
                chunk_ids = _extract_chunk_ids("\n".join(current_content))
                if chunk_ids:
                    sections[current_section] = sorted(set(chunk_ids))
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    # Last section
    if current_section:
        chunk_ids = _extract_chunk_ids("\n".join(current_content))
        if chunk_ids:
            sections[current_section] = sorted(set(chunk_ids))

    return sections


def _extract_chunk_ids(text: str) -> list[str]:
    """Extract all chunk_id-like references from text."""
    found: list[str] = []

    for pattern in CHUNK_ID_PATTERNS:
        for match in pattern.finditer(text):
            found.append(match.group(1))

    return found


def count_total_chunks(sections: dict[str, list[str]]) -> int:
    """Count total unique chunk_ids across all sections."""
    all_chunks: set[str] = set()
    for chunks in sections.values():
        all_chunks.update(chunks)
    return len(all_chunks)


# ---------------------------------------------------------------------------
# MAP BUILDER
# ---------------------------------------------------------------------------
def build_nav_map(dry_run: bool = False) -> dict:
    """Build/update NAVIGATION-MAP.json from actual dossier files.

    Returns:
        {
            "updated": int,
            "skipped": int,
            "already_mapped": int,
            "details": [...],
        }
    """
    nav_map = load_nav_map()
    dossiers = nav_map.get("dossiers", {})

    stats = {
        "updated": 0,
        "skipped": 0,
        "already_mapped": 0,
        "new_entries": 0,
        "details": [],
    }

    # Process persons dossiers
    _process_dossier_category(
        dossiers.get("persons", {}),
        DOSSIERS_DIR / "persons",
        "persons",
        stats,
        dry_run,
    )

    # Process themes dossiers
    _process_dossier_category(
        dossiers.get("themes", {}),
        DOSSIERS_DIR / "themes",
        "themes",
        stats,
        dry_run,
    )

    # Also discover dossier files not yet in nav_map
    _discover_new_dossiers(dossiers, stats, dry_run)

    if not dry_run:
        from datetime import datetime

        nav_map["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        save_nav_map(nav_map)

    return stats


def _process_dossier_category(
    category_map: dict,
    dossier_dir: Path,
    category_name: str,
    stats: dict,
    dry_run: bool,
) -> None:
    """Process all dossiers in a category (persons or themes)."""
    for filename, entry in category_map.items():
        sections = entry.get("sections", {})

        # Check if already mapped (not _pending_mapping)
        if not sections.get("_pending_mapping", False):
            stats["already_mapped"] += 1
            stats["details"].append(
                {
                    "file": filename,
                    "category": category_name,
                    "action": "already_mapped",
                    "sections": len(sections),
                }
            )
            continue

        # Find the actual file
        filepath = dossier_dir / filename
        if not filepath.exists():
            # Try with path from entry
            alt_path = entry.get("path", "")
            if alt_path:
                filepath = BASE_DIR / alt_path.lstrip("/")
            if not filepath.exists():
                stats["skipped"] += 1
                stats["details"].append(
                    {
                        "file": filename,
                        "category": category_name,
                        "action": "skipped",
                        "reason": "file not found",
                    }
                )
                continue

        # Extract sections and chunk_ids
        new_sections = extract_sections_with_chunks(filepath)

        if not new_sections:
            # File exists but no chunk_ids found in content
            # Still replace _pending_mapping with empty sections dict
            # so we know we've scanned it
            stats["details"].append(
                {
                    "file": filename,
                    "category": category_name,
                    "action": "scanned_no_chunks",
                    "sections_found": 0,
                }
            )
            if not dry_run:
                entry["sections"] = {}
                entry["total_chunks"] = 0
            stats["updated"] += 1
            continue

        # Update entry
        if not dry_run:
            entry["sections"] = new_sections
            entry["total_chunks"] = count_total_chunks(new_sections)

        stats["updated"] += 1
        stats["details"].append(
            {
                "file": filename,
                "category": category_name,
                "action": "updated",
                "sections": len(new_sections),
                "total_chunks": count_total_chunks(new_sections),
            }
        )


def _discover_new_dossiers(
    dossiers: dict,
    stats: dict,
    dry_run: bool,
) -> None:
    """Find dossier files not yet in NAVIGATION-MAP.json."""
    for category in ("persons", "themes"):
        cat_dir = DOSSIERS_DIR / category
        if not cat_dir.exists():
            continue

        existing = set(dossiers.get(category, {}).keys())

        for filepath in sorted(cat_dir.glob("DOSSIER-*.md")):
            if filepath.name in existing:
                continue

            # New dossier not in nav_map
            new_sections = extract_sections_with_chunks(filepath)

            new_entry = {
                "path": str(filepath.relative_to(BASE_DIR)),
                "sections": new_sections if new_sections else {},
                "total_chunks": count_total_chunks(new_sections),
            }

            if category == "persons":
                new_entry["source_ids"] = []
            else:
                new_entry["contributing_persons"] = []

            if not dry_run:
                dossiers.setdefault(category, {})[filepath.name] = new_entry

            stats["new_entries"] += 1
            stats["details"].append(
                {
                    "file": filepath.name,
                    "category": category,
                    "action": "new_entry",
                    "sections": len(new_sections),
                    "total_chunks": count_total_chunks(new_sections),
                }
            )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Build/update NAVIGATION-MAP.json from dossier files"
    )
    parser.add_argument("--dry-run", action="store_true", help="Only report what would change")
    args = parser.parse_args()

    print(f"\n{'=' * 60}")
    print("NAVIGATION MAP BUILDER")
    print(f"{'=' * 60}")
    if args.dry_run:
        print("[DRY RUN] No files will be modified.\n")

    result = build_nav_map(dry_run=args.dry_run)

    # Summary
    print(f"Updated: {result['updated']}")
    print(f"Already mapped: {result['already_mapped']}")
    print(f"New entries: {result['new_entries']}")
    print(f"Skipped: {result['skipped']}")

    # Details
    if result["details"]:
        print("\nDetails:")
        for d in result["details"]:
            action = d["action"]
            if action == "updated":
                print(f"  {d['file']}: {d['sections']} sections, {d['total_chunks']} chunks")
            elif action == "new_entry":
                print(f"  {d['file']}: NEW - {d['sections']} sections, {d['total_chunks']} chunks")
            elif action == "already_mapped":
                print(f"  {d['file']}: already mapped ({d['sections']} sections)")
            elif action == "scanned_no_chunks":
                print(f"  {d['file']}: scanned, no chunk_ids found")
            elif action == "skipped":
                print(f"  {d['file']}: SKIPPED - {d.get('reason', 'unknown')}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
