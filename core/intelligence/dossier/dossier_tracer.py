#!/usr/bin/env python3
"""
DOSSIER TRACER - Phase 2.2
============================
Scans dossier files and adds inline DNA references where content matches
DNA YAML entries (HEURISTICAS, FRAMEWORKS, FILOSOFIAS, MODELOS-MENTAIS,
METODOLOGIAS).

For each paragraph in a dossier, tries to match against DNA entries by
comparing keywords, IDs, and content. Adds inline refs like ^[HEUR-AH-001]
where a match is found. Generates coverage report.

Zero external deps (stdlib + PyYAML only).

Versao: 1.0.0
Data: 2026-03-01
"""

import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # mega-brain/
DOSSIERS_DIR = BASE_DIR / "knowledge" / "dossiers"
DNA_DIR = BASE_DIR / "knowledge" / "dna" / "persons"

# DNA layer files and their ID prefixes
DNA_LAYERS = {
    "HEURISTICAS.yaml": "HEUR",
    "FRAMEWORKS.yaml": "FW",
    "FILOSOFIAS.yaml": "FIL",
    "MODELOS-MENTAIS.yaml": "MM",
    "METODOLOGIAS.yaml": "MET",
}


# ---------------------------------------------------------------------------
# DNA LOADER
# ---------------------------------------------------------------------------
class DNAEntry:
    """Represents a single DNA entry (heuristic, framework, etc.)."""

    __slots__ = ("id", "layer", "person", "keywords", "content_preview",
                 "dominios", "chunk_ids")

    def __init__(self, entry_id: str, layer: str, person: str,
                 keywords: List[str], content_preview: str,
                 dominios: List[str], chunk_ids: List[str]):
        self.id = entry_id
        self.layer = layer
        self.person = person
        self.keywords = keywords
        self.content_preview = content_preview
        self.dominios = dominios
        self.chunk_ids = chunk_ids


def _extract_keywords(entry: dict) -> List[str]:
    """Extract matchable keywords from a DNA YAML entry."""
    keywords = []

    # Common fields that contain matchable text
    for field in ("regra", "nome", "descricao", "principio", "titulo",
                  "name", "description", "title", "rule"):
        val = entry.get(field, "")
        if isinstance(val, str) and val:
            # Extract significant words (>3 chars)
            words = re.findall(r'[a-zA-Z\u00C0-\u024F]{4,}', val.lower())
            keywords.extend(words)
            # Also keep the full text for phrase matching
            keywords.append(val.lower())

    # Domain keywords
    for dom in entry.get("dominios", []):
        if isinstance(dom, str):
            keywords.append(dom.lower())

    return keywords


def _extract_content_preview(entry: dict) -> str:
    """Extract a content preview string for matching."""
    parts = []
    for field in ("regra", "nome", "descricao", "principio", "titulo",
                  "name", "description", "acao_recomendada",
                  "contexto_de_uso", "passos", "steps"):
        val = entry.get(field)
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(str(item))
    return " ".join(parts)[:500].lower()


def load_all_dna_entries() -> List[DNAEntry]:
    """Load all DNA entries from all persons."""
    entries: List[DNAEntry] = []

    if not DNA_DIR.exists():
        return entries

    for person_dir in sorted(DNA_DIR.iterdir()):
        if not person_dir.is_dir() or person_dir.name.startswith(("_", ".")):
            continue
        person = person_dir.name

        for layer_file, prefix in DNA_LAYERS.items():
            yaml_path = person_dir / layer_file
            if not yaml_path.exists():
                continue

            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except (yaml.YAMLError, OSError):
                continue

            # YAML files have a top-level key wrapping the list
            # e.g. heuristicas: [...], frameworks: [...], etc.
            entries_list = None
            if isinstance(data, list):
                entries_list = data
            elif isinstance(data, dict):
                # Find the list inside the dict
                layer_keys = {
                    "HEURISTICAS.yaml": "heuristicas",
                    "FRAMEWORKS.yaml": "frameworks",
                    "FILOSOFIAS.yaml": "filosofias",
                    "MODELOS-MENTAIS.yaml": "modelos_mentais",
                    "METODOLOGIAS.yaml": "metodologias",
                }
                key = layer_keys.get(layer_file, "")
                entries_list = data.get(key)
                if not isinstance(entries_list, list):
                    # Try any list value in the dict
                    for v in data.values():
                        if isinstance(v, list):
                            entries_list = v
                            break
            if not entries_list:
                continue

            for entry in entries_list:
                if not isinstance(entry, dict):
                    continue
                entry_id = entry.get("id", "")
                if not entry_id:
                    continue

                # Extract chunk_ids from evidencias
                chunk_ids = []
                for ev in entry.get("evidencias", []):
                    if isinstance(ev, dict) and "chunk_id" in ev:
                        chunk_ids.append(ev["chunk_id"])
                # Also check direct chunk_ids field
                if "chunk_ids" in entry:
                    cids = entry["chunk_ids"]
                    if isinstance(cids, list):
                        chunk_ids.extend(cids)

                entries.append(DNAEntry(
                    entry_id=entry_id,
                    layer=prefix,
                    person=person,
                    keywords=_extract_keywords(entry),
                    content_preview=_extract_content_preview(entry),
                    dominios=entry.get("dominios", []),
                    chunk_ids=chunk_ids,
                ))

    return entries


# ---------------------------------------------------------------------------
# DOSSIER SCANNER
# ---------------------------------------------------------------------------
def _detect_person_from_dossier(filepath: Path) -> Optional[str]:
    """Try to detect which person a dossier is about from filename."""
    name = filepath.stem.lower()
    # Remove DOSSIER- prefix
    name = re.sub(r"^dossier-", "", name)

    # Map common filename patterns to person directory names
    name_map = {
        "alex-hormozi": "alex-hormozi",
        "cole-gordon": "cole-gordon",
        "jeremy-haynes": "jeremy-haynes",
        "jeremy-miner": "jeremy-miner",
        "jordan-lee": "jordan-lee",
        "sam-oven": "sam-oven",
        "richard-linder": "richard-linder",
        "the-scalable-company": "the-scalable-company",
    }

    for pattern, person_dir in name_map.items():
        if pattern in name:
            return person_dir

    return None


def _already_has_ref(line: str, entry_id: str) -> bool:
    """Check if a line already contains a reference to this entry."""
    return f"^[{entry_id}]" in line or f"[{entry_id}]" in line


def _match_score(text: str, entry: DNAEntry) -> float:
    """Score how well a text block matches a DNA entry (0.0-1.0)."""
    text_lower = text.lower()
    score = 0.0
    matches = 0

    # Check each keyword
    for kw in entry.keywords:
        if len(kw) > 6 and kw in text_lower:
            matches += 1

    if not entry.keywords:
        return 0.0

    # Normalize by keyword count
    keyword_ratio = matches / max(len(entry.keywords), 1)
    score = min(keyword_ratio * 2, 1.0)  # Scale up, cap at 1.0

    # Bonus for entry ID mentioned in text
    if entry.id.lower() in text_lower:
        score = max(score, 0.9)

    # Bonus for chunk_id mentioned
    for cid in entry.chunk_ids:
        if cid.lower() in text_lower:
            score = max(score, 0.8)

    return score


MATCH_THRESHOLD = 0.35  # Minimum score to add a reference


def trace_dossier(
    filepath: Path,
    dna_entries: List[DNAEntry],
    dry_run: bool = False,
) -> dict:
    """Add DNA references to a single dossier file.

    Returns:
        {
            "file": str,
            "person": str or None,
            "sections": int,
            "refs_added": int,
            "refs_existing": int,
            "matches": [{"section": str, "entry_id": str, "score": float}],
        }
    """
    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"file": str(filepath), "error": "Could not read file"}

    person = _detect_person_from_dossier(filepath)

    # Filter DNA entries: prefer entries from the same person
    relevant_entries = dna_entries
    if person:
        person_entries = [e for e in dna_entries if e.person == person]
        if person_entries:
            relevant_entries = person_entries

    lines = content.split("\n")
    sections = []
    current_section = ""
    current_lines: List[str] = []
    current_start = 0

    # Parse into sections
    for i, line in enumerate(lines):
        if line.startswith("## "):
            if current_lines:
                sections.append((current_section, current_lines, current_start))
            current_section = line[3:].strip()
            current_lines = [line]
            current_start = i
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_section, current_lines, current_start))

    # Match each section against DNA entries
    refs_added = 0
    refs_existing = 0
    matches_found = []
    modified_lines = list(lines)

    for sec_title, sec_lines, sec_start in sections:
        sec_text = "\n".join(sec_lines)

        for entry in relevant_entries:
            if _already_has_ref(sec_text, entry.id):
                refs_existing += 1
                continue

            score = _match_score(sec_text, entry)
            if score >= MATCH_THRESHOLD:
                matches_found.append({
                    "section": sec_title,
                    "entry_id": entry.id,
                    "score": round(score, 2),
                    "layer": entry.layer,
                })

                if not dry_run:
                    # Add reference at end of the section's first paragraph
                    # Find first non-empty, non-header line in section
                    for j, sl in enumerate(sec_lines):
                        line_idx = sec_start + j
                        if sl.strip() and not sl.startswith("#") and not sl.startswith(">"):
                            # Add ref at end of this line
                            if not _already_has_ref(modified_lines[line_idx], entry.id):
                                modified_lines[line_idx] = (
                                    modified_lines[line_idx].rstrip()
                                    + f" ^[{entry.id}]"
                                )
                                refs_added += 1
                            break

    # Write modified content
    if not dry_run and refs_added > 0:
        filepath.write_text("\n".join(modified_lines), encoding="utf-8")

    return {
        "file": str(filepath.relative_to(BASE_DIR)),
        "person": person,
        "sections": len(sections),
        "refs_added": refs_added,
        "refs_existing": refs_existing,
        "matches": matches_found,
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# BATCH TRACE
# ---------------------------------------------------------------------------
def trace_all_dossiers(dry_run: bool = False) -> dict:
    """Trace all dossier files and generate coverage report.

    Returns:
        {
            "persons_dossiers": [...],
            "theme_dossiers": [...],
            "total_refs_added": int,
            "total_refs_existing": int,
            "coverage": {...},
        }
    """
    dna_entries = load_all_dna_entries()
    if not dna_entries:
        return {"error": "No DNA entries found"}

    results = {
        "dna_entries_loaded": len(dna_entries),
        "persons_dossiers": [],
        "theme_dossiers": [],
        "total_refs_added": 0,
        "total_refs_existing": 0,
    }

    # Process person dossiers
    persons_dir = DOSSIERS_DIR / "persons"
    if persons_dir.exists():
        for f in sorted(persons_dir.glob("DOSSIER-*.md")):
            r = trace_dossier(f, dna_entries, dry_run=dry_run)
            results["persons_dossiers"].append(r)
            results["total_refs_added"] += r.get("refs_added", 0)
            results["total_refs_existing"] += r.get("refs_existing", 0)

    # Process theme dossiers
    themes_dir = DOSSIERS_DIR / "themes"
    if themes_dir.exists():
        for f in sorted(themes_dir.glob("DOSSIER-*.md")):
            r = trace_dossier(f, dna_entries, dry_run=dry_run)
            results["theme_dossiers"].append(r)
            results["total_refs_added"] += r.get("refs_added", 0)
            results["total_refs_existing"] += r.get("refs_existing", 0)

    # Coverage report
    total_dossiers = len(results["persons_dossiers"]) + len(results["theme_dossiers"])
    dossiers_with_refs = sum(
        1 for d in results["persons_dossiers"] + results["theme_dossiers"]
        if d.get("refs_added", 0) > 0 or d.get("refs_existing", 0) > 0
    )

    # Count DNA entries that were matched at least once
    matched_ids = set()
    for d in results["persons_dossiers"] + results["theme_dossiers"]:
        for m in d.get("matches", []):
            matched_ids.add(m["entry_id"])

    results["coverage"] = {
        "total_dossiers": total_dossiers,
        "dossiers_with_refs": dossiers_with_refs,
        "dossier_coverage_pct": round(
            dossiers_with_refs / max(total_dossiers, 1) * 100, 1
        ),
        "total_dna_entries": len(dna_entries),
        "dna_entries_matched": len(matched_ids),
        "dna_coverage_pct": round(
            len(matched_ids) / max(len(dna_entries), 1) * 100, 1
        ),
    }

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Add DNA traceability references to dossier files"
    )
    parser.add_argument(
        "target", nargs="?", default="all",
        help="'all' or path to specific dossier file"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Only report matches without modifying files"
    )
    args = parser.parse_args()

    if args.target == "all":
        print(f"\n{'='*60}")
        print("DOSSIER TRACER - Full Scan")
        print(f"{'='*60}")
        if args.dry_run:
            print("[DRY RUN] No files will be modified.\n")

        result = trace_all_dossiers(dry_run=args.dry_run)

        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"DNA entries loaded: {result['dna_entries_loaded']}\n")

        print("Person Dossiers:")
        for d in result["persons_dossiers"]:
            status = f"+{d.get('refs_added', 0)} new" if d.get("refs_added") else "no changes"
            existing = f", {d['refs_existing']} existing" if d.get("refs_existing") else ""
            print(f"  {d['file']}: {d.get('sections', 0)} sections, {status}{existing}")

        print("\nTheme Dossiers:")
        for d in result["theme_dossiers"]:
            status = f"+{d.get('refs_added', 0)} new" if d.get("refs_added") else "no changes"
            existing = f", {d['refs_existing']} existing" if d.get("refs_existing") else ""
            print(f"  {d['file']}: {d.get('sections', 0)} sections, {status}{existing}")

        cov = result["coverage"]
        print(f"\n{'='*60}")
        print("COVERAGE REPORT")
        print(f"{'='*60}")
        print(f"Dossiers: {cov['dossiers_with_refs']}/{cov['total_dossiers']} "
              f"({cov['dossier_coverage_pct']}%)")
        print(f"DNA entries matched: {cov['dna_entries_matched']}/{cov['total_dna_entries']} "
              f"({cov['dna_coverage_pct']}%)")
        print(f"Total refs added: {result['total_refs_added']}")
        print(f"Total refs existing: {result['total_refs_existing']}")
        print(f"{'='*60}\n")
    else:
        target = Path(args.target)
        if not target.is_absolute():
            target = BASE_DIR / target
        if not target.exists():
            print(f"File not found: {target}")
            sys.exit(1)

        dna_entries = load_all_dna_entries()
        result = trace_dossier(target, dna_entries, dry_run=args.dry_run)

        print(f"\n{'='*60}")
        print(f"DOSSIER TRACER: {result['file']}")
        print(f"{'='*60}")
        if args.dry_run:
            print("[DRY RUN]\n")
        print(f"Person: {result.get('person', 'N/A')}")
        print(f"Sections: {result.get('sections', 0)}")
        print(f"Refs added: {result.get('refs_added', 0)}")
        print(f"Refs existing: {result.get('refs_existing', 0)}")
        if result.get("matches"):
            print(f"\nMatches ({len(result['matches'])}):")
            for m in result["matches"]:
                print(f"  [{m['layer']}] {m['entry_id']} → {m['section']} "
                      f"(score: {m['score']})")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
