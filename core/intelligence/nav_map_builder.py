#!/usr/bin/env python3
"""
NAVIGATION MAP BUILDER
======================
Resolves pending navigation mappings in NAVIGATION-MAP.json by matching
dossier section headers against RAG chunk index metadata.

The Cole Gordon entry is the reference format and MUST remain unchanged.

Strategy:
  1. Load NAVIGATION-MAP.json (knowledge/external/)
  2. Load RAG chunk indexes (external + business)
  3. For each dossier with _pending_mapping: true:
     a. Read the actual .md file, extract ## section headers
     b. Match headers against chunks whose source_file ends with that dossier filename
     c. Group matched chunk_ids by section name
  4. Write resolved sections back in Cole Gordon reference format
  5. Preserve any entry that is already resolved (not _pending_mapping)

Idempotent: running twice produces identical output.
Zero external deps beyond stdlib.

Version: 1.0.0
Date: 2026-03-16
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# PATHS (using core.paths constants)
# ---------------------------------------------------------------------------
try:
    from core.paths import DATA, KNOWLEDGE_EXTERNAL, ROOT
except ImportError:
    # Fallback for direct execution outside package context
    ROOT = Path(__file__).resolve().parent.parent.parent
    DATA = ROOT / ".data"
    KNOWLEDGE_EXTERNAL = ROOT / "knowledge" / "external"

NAV_MAP_PATH = KNOWLEDGE_EXTERNAL / "NAVIGATION-MAP.json"
DOSSIERS_PERSONS = KNOWLEDGE_EXTERNAL / "dossiers" / "persons"
DOSSIERS_THEMES = KNOWLEDGE_EXTERNAL / "dossiers" / "themes"
DOSSIERS_SYSTEM = KNOWLEDGE_EXTERNAL / "dossiers" / "system"

# RAG index locations
RAG_INDEX_CHUNKS = DATA / "rag_index" / "chunks.json"
RAG_BUSINESS_CHUNKS = DATA / "rag_business" / "chunks.json"

# The Cole Gordon entry is the reference and must never be modified
PROTECTED_ENTRIES = frozenset({"DOSSIER-COLE-GORDON.md"})


# ---------------------------------------------------------------------------
# DATA LOADERS
# ---------------------------------------------------------------------------
def load_json(path: Path) -> Any:
    """Load a JSON file. Returns None if file does not exist."""
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    """Write JSON with pretty formatting and no ASCII escaping."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    # Ensure trailing newline
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n")


def load_all_chunks() -> list[dict]:
    """Load chunks from all available RAG indexes."""
    all_chunks: list[dict] = []
    for chunks_path in (RAG_INDEX_CHUNKS, RAG_BUSINESS_CHUNKS):
        raw = load_json(chunks_path)
        if raw and isinstance(raw, list):
            all_chunks.extend(raw)
    return all_chunks


# ---------------------------------------------------------------------------
# CHUNK INDEX BUILDER
# ---------------------------------------------------------------------------
def build_chunk_lookup(chunks: list[dict]) -> dict[str, dict[str, list[str]]]:
    """Build a lookup: {source_filename: {section_name: [chunk_ids]}}.

    Chunks have a ``source_file`` field like
    ``knowledge/external/dossiers/persons/DOSSIER-ALEX-HORMOZI.md``
    and a ``section`` field that corresponds to the dossier's ``##`` header.

    We key by the filename (last path component) so we can match against
    NAVIGATION-MAP entries which use filenames as keys.
    """
    lookup: dict[str, dict[str, list[str]]] = {}

    for chunk in chunks:
        source_file = chunk.get("source_file", "")
        section = chunk.get("section", "")
        chunk_id = chunk.get("chunk_id", "")

        if not source_file or not chunk_id:
            continue

        filename = Path(source_file).name

        if filename not in lookup:
            lookup[filename] = {}

        if section not in lookup[filename]:
            lookup[filename][section] = []

        lookup[filename][section].append(chunk_id)

    # Sort chunk_ids within each section for deterministic output
    for filename in lookup:
        for section in lookup[filename]:
            lookup[filename][section] = sorted(set(lookup[filename][section]))

    return lookup


# ---------------------------------------------------------------------------
# SECTION EXTRACTOR
# ---------------------------------------------------------------------------
def extract_section_headers(filepath: Path) -> list[str]:
    """Extract ## section headers from a dossier markdown file.

    Returns a list of section names (without the ``## `` prefix) in order.
    """
    if not filepath.exists():
        return []

    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    headers: list[str] = []
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            header = stripped[3:].strip()
            if header:
                headers.append(header)

    return headers


# ---------------------------------------------------------------------------
# SECTION MATCHER
# ---------------------------------------------------------------------------
def match_sections_to_chunks(
    dossier_filename: str,
    dossier_dir: Path,
    chunk_lookup: dict[str, dict[str, list[str]]],
) -> dict[str, list[str]] | None:
    """Match a dossier's section headers to RAG chunk IDs.

    Returns a dict of {section_name: [chunk_ids]} or None if the dossier
    file cannot be found or has no matchable sections.

    The matching strategy:
      1. Look up the dossier filename in the chunk_lookup
      2. Also check for "filename 2" variant (RAG indexer creates duplicates)
      3. For each section header in the dossier, find matching chunks
      4. Sections with no matching chunks are still included (empty list)
         to indicate we scanned them
    """
    filepath = dossier_dir / dossier_filename
    if not filepath.exists():
        return None

    headers = extract_section_headers(filepath)
    if not headers:
        return {}

    # Gather chunk sections from all filename variants
    # The RAG indexer sometimes creates "DOSSIER-NAME 2.md" duplicates
    stem = Path(dossier_filename).stem
    suffix = Path(dossier_filename).suffix
    filename_variants = [
        dossier_filename,
        f"{stem} 2{suffix}",
    ]

    available_sections: dict[str, list[str]] = {}
    for variant in filename_variants:
        if variant in chunk_lookup:
            for sec_name, cids in chunk_lookup[variant].items():
                if sec_name in available_sections:
                    # Merge chunk_ids from duplicate file entries
                    existing = set(available_sections[sec_name])
                    existing.update(cids)
                    available_sections[sec_name] = sorted(existing)
                else:
                    available_sections[sec_name] = list(cids)

    # Match dossier headers to available chunk sections
    result: dict[str, list[str]] = {}
    for header in headers:
        if header in available_sections:
            result[header] = available_sections[header]
        else:
            # Try case-insensitive match
            matched = False
            for avail_sec, cids in available_sections.items():
                if avail_sec.lower() == header.lower():
                    result[header] = cids
                    matched = True
                    break
            if not matched:
                # Section exists in dossier but no chunks found
                result[header] = []

    return result


# ---------------------------------------------------------------------------
# NAV MAP RESOLVER
# ---------------------------------------------------------------------------
def resolve_pending_mappings(dry_run: bool = False) -> dict[str, Any]:
    """Main entry point: resolve all _pending_mapping entries.

    Returns a stats dict with counts and details.
    """
    nav_map = load_json(NAV_MAP_PATH)
    if nav_map is None:
        return {
            "error": f"NAVIGATION-MAP.json not found at {NAV_MAP_PATH}",
            "resolved": 0,
            "already_mapped": 0,
            "protected": 0,
            "skipped": 0,
            "details": [],
        }

    chunks = load_all_chunks()
    chunk_lookup = build_chunk_lookup(chunks)

    stats: dict[str, Any] = {
        "resolved": 0,
        "already_mapped": 0,
        "protected": 0,
        "skipped": 0,
        "no_chunks_found": 0,
        "details": [],
    }

    dossiers = nav_map.get("dossiers", {})

    # Category -> directory mapping
    category_dirs = {
        "persons": DOSSIERS_PERSONS,
        "themes": DOSSIERS_THEMES,
        "system": DOSSIERS_SYSTEM,
    }

    for category, dossier_dir in category_dirs.items():
        category_entries = dossiers.get(category, {})
        for filename, entry in category_entries.items():
            # Protect reference entries
            if filename in PROTECTED_ENTRIES:
                stats["protected"] += 1
                stats["details"].append(
                    {
                        "file": filename,
                        "category": category,
                        "action": "protected",
                        "reason": "reference entry preserved",
                    }
                )
                continue

            sections = entry.get("sections", {})

            # Check if already resolved (no _pending_mapping flag)
            if not sections.get("_pending_mapping", False):
                stats["already_mapped"] += 1
                stats["details"].append(
                    {
                        "file": filename,
                        "category": category,
                        "action": "already_mapped",
                        "sections": len(sections),
                    }
                )
                continue

            # Resolve this entry
            matched = match_sections_to_chunks(
                filename, dossier_dir, chunk_lookup
            )

            if matched is None:
                stats["skipped"] += 1
                stats["details"].append(
                    {
                        "file": filename,
                        "category": category,
                        "action": "skipped",
                        "reason": "dossier file not found on disk",
                    }
                )
                continue

            if not matched:
                stats["no_chunks_found"] += 1
                stats["details"].append(
                    {
                        "file": filename,
                        "category": category,
                        "action": "no_chunks",
                        "reason": "no section headers found in dossier",
                    }
                )
                if not dry_run:
                    entry["sections"] = {}
                    entry["total_chunks"] = 0
                    entry["last_updated"] = _now_iso()
                continue

            # Count total unique chunk_ids
            all_cids: set[str] = set()
            for cids in matched.values():
                all_cids.update(cids)
            total_chunks = len(all_cids)

            # Filter out sections with empty chunk lists for cleaner output
            # (matching Cole Gordon format: only sections with actual chunks)
            resolved_sections = {
                sec: cids for sec, cids in matched.items() if cids
            }

            if not dry_run:
                entry["sections"] = resolved_sections
                entry["total_chunks"] = total_chunks
                entry["last_updated"] = _now_iso()

            stats["resolved"] += 1
            stats["details"].append(
                {
                    "file": filename,
                    "category": category,
                    "action": "resolved",
                    "sections_total": len(matched),
                    "sections_with_chunks": len(resolved_sections),
                    "total_chunks": total_chunks,
                }
            )

    # Update statistics block
    if not dry_run:
        _update_statistics(nav_map)
        nav_map["last_updated"] = _now_iso()
        save_json(NAV_MAP_PATH, nav_map)

    return stats


def _now_iso() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _update_statistics(nav_map: dict) -> None:
    """Recalculate the statistics block from current dossier state."""
    dossiers = nav_map.get("dossiers", {})
    total_all = 0
    fully_mapped = 0
    pending = 0
    total_chunks = 0

    category_counts: dict[str, int] = {}

    for category, entries in dossiers.items():
        if not isinstance(entries, dict):
            continue
        count = len(entries)
        category_counts[category] = count
        total_all += count

        for entry in entries.values():
            if not isinstance(entry, dict):
                continue
            sections = entry.get("sections", {})
            if sections.get("_pending_mapping", False):
                pending += 1
            elif sections:
                fully_mapped += 1
            tc = entry.get("total_chunks", 0)
            if isinstance(tc, int):
                total_chunks += tc

    stats = nav_map.get("statistics", {})
    for cat, count in category_counts.items():
        stats[f"total_dossiers_{cat}"] = count
    stats["total_dossiers_all"] = total_all
    stats["fully_mapped"] = fully_mapped
    stats["pending_section_mapping"] = pending
    stats["total_known_chunks"] = total_chunks
    stats["last_index_generated"] = _now_iso()
    nav_map["statistics"] = stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Resolve pending navigation mappings in NAVIGATION-MAP.json "
            "by matching dossier sections to RAG chunk IDs."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without modifying files",
    )
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("  NAVIGATION MAP BUILDER")
    print("=" * 60)

    if args.dry_run:
        print("  [DRY RUN] No files will be modified.")

    print(f"  NAV MAP: {NAV_MAP_PATH}")
    print(f"  RAG INDEX: {RAG_INDEX_CHUNKS}")
    print(f"  RAG BUSINESS: {RAG_BUSINESS_CHUNKS}")
    print()

    result = resolve_pending_mappings(dry_run=args.dry_run)

    if "error" in result:
        print(f"  ERROR: {result['error']}")
        return 1

    # Summary table
    print("  --- Summary ---")
    print(f"  Resolved:       {result['resolved']}")
    print(f"  Already mapped: {result['already_mapped']}")
    print(f"  Protected:      {result['protected']}")
    print(f"  No chunks:      {result['no_chunks_found']}")
    print(f"  Skipped:        {result['skipped']}")
    print()

    # Details
    details = result.get("details", [])
    if details:
        print("  --- Details ---")
        for d in details:
            action = d["action"]
            fname = d["file"]
            cat = d["category"]

            if action == "resolved":
                sec_w = d["sections_with_chunks"]
                sec_t = d["sections_total"]
                tc = d["total_chunks"]
                print(
                    f"  [{cat}] {fname}: "
                    f"RESOLVED {sec_w}/{sec_t} sections, "
                    f"{tc} chunks"
                )
            elif action == "already_mapped":
                print(
                    f"  [{cat}] {fname}: "
                    f"already mapped ({d['sections']} sections)"
                )
            elif action == "protected":
                print(f"  [{cat}] {fname}: PROTECTED (reference entry)")
            elif action == "skipped":
                print(
                    f"  [{cat}] {fname}: "
                    f"SKIPPED ({d.get('reason', 'unknown')})"
                )
            elif action == "no_chunks":
                print(
                    f"  [{cat}] {fname}: "
                    f"NO CHUNKS ({d.get('reason', 'unknown')})"
                )

    print()
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
