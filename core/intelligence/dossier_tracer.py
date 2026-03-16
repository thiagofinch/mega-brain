"""
core/intelligence/dossier_tracer.py -- Dossier Traceability Engine

Adds inline ^[DNA-ID] citations to dossier paragraphs by fuzzy-matching
paragraph content against DNA YAML entries (all 5 layers).

Enforces the agent-traceability constitution rule:
  All agent content must be 100% traceable to sources.

Usage:
    python3 -m core.intelligence.dossier_tracer                  # all dossiers
    python3 -m core.intelligence.dossier_tracer --person "Name"  # single person
    python3 -m core.intelligence.dossier_tracer --dry-run        # preview only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Path resolution (uses core.paths when importable, falls back to manual)
# ---------------------------------------------------------------------------
try:
    from core.paths import (
        ARTIFACTS,
        KNOWLEDGE_EXTERNAL,
        KNOWLEDGE_BUSINESS,
    )
except ImportError:
    _ROOT = Path(__file__).resolve().parent.parent.parent
    ARTIFACTS = _ROOT / "artifacts"
    KNOWLEDGE_EXTERNAL = _ROOT / "knowledge" / "external"
    KNOWLEDGE_BUSINESS = _ROOT / "knowledge" / "business"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DNA_LAYERS = [
    "HEURISTICAS",
    "FRAMEWORKS",
    "MODELOS-MENTAIS",
    "FILOSOFIAS",
    "METODOLOGIAS",
]

SIMILARITY_THRESHOLD = 0.45  # Minimum ratio for a fuzzy match
MAX_CITATIONS_PER_PARAGRAPH = 3  # Cap citations to avoid noise

# Lines that should never receive citations
SKIP_LINE_PATTERNS = re.compile(
    r"^(#|>|\||\s*[-*]\s*\*\*Fontes?\*\*|```|---|\[\[|!\[)", re.IGNORECASE
)

REPORT_PATH = ARTIFACTS / "traceability-report.json"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class DNAEntry:
    """Single DNA entry loaded from a YAML layer file."""

    entry_id: str
    name: str
    description: str
    layer: str
    person_slug: str

    @property
    def citation_tag(self) -> str:
        """Format the ID as an inline citation: ^[HEUR-LO-001]."""
        return f"^[{self.entry_id}]"


@dataclass
class TraceResult:
    """Traceability result for one dossier file."""

    dossier: str
    person: str
    total_paragraphs: int = 0
    traced: int = 0
    coverage_pct: float = 0.0
    citations_added: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------
def _normalize(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace, remove punctuation."""
    # NFD decompose then strip combining chars (accents)
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Lowercase
    lowered = ascii_text.lower()
    # Remove non-alphanumeric except spaces
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    # Collapse whitespace
    return re.sub(r"\s+", " ", cleaned).strip()


# ---------------------------------------------------------------------------
# DNA Loading
# ---------------------------------------------------------------------------
def _load_entries_from_yaml(path: Path, person_slug: str) -> list[DNAEntry]:
    """Load DNA entries from a single YAML file."""
    if not path.exists():
        return []

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return []

    if not data or not isinstance(data, dict):
        return []

    layer_name = path.stem  # e.g. HEURISTICAS, FRAMEWORKS

    # Handle both YAML structures:
    #   Old: { entries: [...] }            (Hormozi)
    #   New: { heuristics: [...] }         (Liam Ottley)
    #   MCE: { entries: [...] }            (Jordan Lee)
    entries_list: list[dict[str, Any]] = []
    for key in ("entries", "heuristics", "frameworks", "philosophies",
                "mental_models", "methodologies"):
        if key in data and isinstance(data[key], list):
            entries_list = data[key]
            break

    results: list[DNAEntry] = []
    for entry in entries_list:
        entry_id = str(entry.get("id", "")).strip()
        if not entry_id:
            continue

        # Get description text (handles both 'description' and 'descricao')
        desc = entry.get("description", entry.get("descricao", ""))
        name = entry.get("name", entry.get("nome", ""))

        # Combine name + description for richer matching surface
        combined = f"{name} {desc}".strip()
        if not combined:
            continue

        results.append(
            DNAEntry(
                entry_id=entry_id,
                name=str(name),
                description=str(combined),
                layer=layer_name,
                person_slug=person_slug,
            )
        )

    return results


def load_person_dna(person_slug: str) -> list[DNAEntry]:
    """Load all DNA entries for a person across both knowledge buckets."""
    all_entries: list[DNAEntry] = []

    for bucket in (KNOWLEDGE_EXTERNAL, KNOWLEDGE_BUSINESS):
        dna_dir = bucket / "dna" / "persons" / person_slug
        if not dna_dir.is_dir():
            continue

        for layer_name in DNA_LAYERS:
            yaml_path = dna_dir / f"{layer_name}.yaml"
            all_entries.extend(_load_entries_from_yaml(yaml_path, person_slug))

    return all_entries


# ---------------------------------------------------------------------------
# Person slug extraction
# ---------------------------------------------------------------------------
def _slug_from_dossier_path(dossier_path: Path) -> str:
    """Extract person slug from dossier filename.

    DOSSIER-ALEX-HORMOZI.md -> alex-hormozi
    DOSSIER-COLE-GORDON.md  -> cole-gordon
    """
    stem = dossier_path.stem  # DOSSIER-ALEX-HORMOZI
    # Remove DOSSIER- prefix (case-insensitive)
    if stem.upper().startswith("DOSSIER-"):
        slug = stem[8:]  # everything after "DOSSIER-"
    else:
        slug = stem
    return slug.lower()


# ---------------------------------------------------------------------------
# Paragraph extraction
# ---------------------------------------------------------------------------
def _is_traceable_paragraph(text: str) -> bool:
    """Check if a text block should be considered for tracing.

    Skip: headers, blockquotes, table rows, code blocks, separators,
    wiki links, image embeds, very short lines.
    """
    stripped = text.strip()
    if not stripped:
        return False
    if len(stripped) < 30:
        return False
    if SKIP_LINE_PATTERNS.match(stripped):
        return False
    # Skip lines that are entirely inside a table
    if stripped.startswith("|") and stripped.endswith("|"):
        return False
    return True


def _extract_paragraphs(content: str) -> list[tuple[int, int, str]]:
    """Extract traceable paragraphs with their line positions.

    Returns list of (start_line, end_line, text) tuples.
    Line numbers are 0-indexed into the lines array.
    """
    lines = content.split("\n")
    paragraphs: list[tuple[int, int, str]] = []

    in_code_block = False
    para_start: int | None = None
    para_lines: list[str] = []

    for i, line in enumerate(lines):
        # Track code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            # Flush current paragraph
            if para_lines and para_start is not None:
                text = "\n".join(para_lines)
                if _is_traceable_paragraph(text):
                    paragraphs.append((para_start, i - 1, text))
                para_lines = []
                para_start = None
            continue

        if in_code_block:
            continue

        stripped = line.strip()

        if not stripped:
            # Empty line -> end of paragraph
            if para_lines and para_start is not None:
                text = "\n".join(para_lines)
                if _is_traceable_paragraph(text):
                    paragraphs.append((para_start, i - 1, text))
                para_lines = []
                para_start = None
        else:
            # Skip headers, separators, etc.
            if SKIP_LINE_PATTERNS.match(stripped):
                # Flush current paragraph first
                if para_lines and para_start is not None:
                    text = "\n".join(para_lines)
                    if _is_traceable_paragraph(text):
                        paragraphs.append((para_start, i - 1, text))
                    para_lines = []
                    para_start = None
                continue

            if para_start is None:
                para_start = i
            para_lines.append(line)

    # Flush final paragraph
    if para_lines and para_start is not None:
        text = "\n".join(para_lines)
        if _is_traceable_paragraph(text):
            paragraphs.append((para_start, len(lines) - 1, text))

    return paragraphs


# ---------------------------------------------------------------------------
# Fuzzy matching
# ---------------------------------------------------------------------------
def _already_cited(paragraph: str, entry_id: str) -> bool:
    """Check if the paragraph already has this citation."""
    return f"^[{entry_id}]" in paragraph


def _match_paragraph_to_dna(
    paragraph: str,
    dna_entries: list[DNAEntry],
    threshold: float | None = None,
) -> list[tuple[DNAEntry, float]]:
    """Find DNA entries that fuzzy-match a paragraph.

    Uses SequenceMatcher on normalized text. Returns matches sorted by
    descending similarity, capped at MAX_CITATIONS_PER_PARAGRAPH.
    """
    if threshold is None:
        threshold = SIMILARITY_THRESHOLD

    norm_para = _normalize(paragraph)
    if not norm_para:
        return []

    matches: list[tuple[DNAEntry, float]] = []

    for entry in dna_entries:
        if _already_cited(paragraph, entry.entry_id):
            continue

        norm_desc = _normalize(entry.description)
        if not norm_desc:
            continue

        # Use the shorter text as the reference for ratio calculation.
        # This prevents long dossier paragraphs from diluting the score
        # when compared against concise DNA descriptions.
        ratio = SequenceMatcher(None, norm_para, norm_desc).ratio()

        # Also check if the DNA description is substantially contained
        # in the paragraph (substring-like matching for short entries).
        if len(norm_desc) < len(norm_para):
            # Quick containment check: look for key phrases
            desc_words = set(norm_desc.split())
            para_words = set(norm_para.split())
            if len(desc_words) > 3:
                overlap = len(desc_words & para_words) / len(desc_words)
                # Boost ratio if high word overlap
                ratio = max(ratio, overlap * 0.9)

        if ratio >= threshold:
            matches.append((entry, ratio))

    # Sort by similarity descending, cap at max
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:MAX_CITATIONS_PER_PARAGRAPH]


# ---------------------------------------------------------------------------
# Citation injection
# ---------------------------------------------------------------------------
def _inject_citations(
    content: str,
    paragraphs: list[tuple[int, int, str]],
    dna_entries: list[DNAEntry],
    threshold: float | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Inject ^[ID] citations into matching paragraphs.

    Returns (modified_content, list_of_citation_records).
    """
    lines = content.split("\n")
    citations_log: list[dict[str, Any]] = []

    # Process paragraphs in reverse order so line indices stay valid
    for start_line, end_line, para_text in reversed(paragraphs):
        matches = _match_paragraph_to_dna(para_text, dna_entries, threshold=threshold)
        if not matches:
            continue

        # Build citation string
        tags = " ".join(m.citation_tag for m, _ in matches)

        # Append citations to the last line of the paragraph
        last_line = lines[end_line].rstrip()

        # Avoid duplicating if all tags already present
        new_tags = []
        for m, score in matches:
            if not _already_cited(last_line, m.entry_id):
                new_tags.append((m, score))

        if not new_tags:
            continue

        tag_str = " ".join(m.citation_tag for m, _ in new_tags)
        lines[end_line] = f"{last_line} {tag_str}"

        for m, score in new_tags:
            citations_log.append({
                "entry_id": m.entry_id,
                "layer": m.layer,
                "similarity": round(score, 3),
                "paragraph_line": start_line + 1,  # 1-indexed for humans
                "paragraph_preview": para_text[:80].replace("\n", " "),
            })

    return "\n".join(lines), citations_log


# ---------------------------------------------------------------------------
# Dossier discovery
# ---------------------------------------------------------------------------
def discover_dossiers(person_filter: str | None = None) -> list[Path]:
    """Find all person dossier files across knowledge buckets."""
    dossiers: list[Path] = []

    for bucket in (KNOWLEDGE_EXTERNAL, KNOWLEDGE_BUSINESS):
        persons_dir = bucket / "dossiers" / "persons"
        if not persons_dir.is_dir():
            continue

        for md_file in sorted(persons_dir.glob("DOSSIER-*.md")):
            # Skip example files
            if "EXAMPLE" in md_file.stem.upper():
                continue

            if person_filter:
                slug = _slug_from_dossier_path(md_file)
                filter_slug = person_filter.lower().replace(" ", "-")
                if slug != filter_slug:
                    continue

            dossiers.append(md_file)

    return dossiers


# ---------------------------------------------------------------------------
# Core trace function
# ---------------------------------------------------------------------------
def trace_dossier(
    dossier_path: Path,
    dry_run: bool = False,
    threshold: float | None = None,
) -> TraceResult:
    """Trace a single dossier file against its person's DNA entries.

    Args:
        dossier_path: Path to the dossier markdown file.
        dry_run: If True, do not modify the file on disk.
        threshold: Similarity threshold override (default: SIMILARITY_THRESHOLD).

    Returns:
        TraceResult with coverage statistics.
    """
    slug = _slug_from_dossier_path(dossier_path)
    result = TraceResult(
        dossier=str(dossier_path),
        person=slug,
    )

    # Load DNA entries for this person
    dna_entries = load_person_dna(slug)
    if not dna_entries:
        return result

    # Read dossier content
    content = dossier_path.read_text(encoding="utf-8")

    # Extract paragraphs
    paragraphs = _extract_paragraphs(content)
    result.total_paragraphs = len(paragraphs)

    if not paragraphs:
        return result

    # Match and inject citations
    modified_content, citations_log = _inject_citations(
        content, paragraphs, dna_entries, threshold=threshold
    )
    result.citations_added = citations_log
    result.traced = len(set(c["paragraph_line"] for c in citations_log))
    result.coverage_pct = round(
        (result.traced / result.total_paragraphs * 100) if result.total_paragraphs > 0 else 0.0,
        1,
    )

    # Write modified content only if there were matches and not dry-run
    if citations_log and not dry_run:
        dossier_path.write_text(modified_content, encoding="utf-8")

    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def write_report(results: list[TraceResult]) -> Path:
    """Write traceability report to artifacts/traceability-report.json."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "generated": __import__("datetime").datetime.now().isoformat(),
        "total_dossiers": len(results),
        "traced_dossiers": sum(1 for r in results if r.traced > 0),
        "average_coverage_pct": round(
            sum(r.coverage_pct for r in results) / len(results) if results else 0,
            1,
        ),
        "dossiers": [
            {
                "dossier": r.dossier,
                "person": r.person,
                "total_paragraphs": r.total_paragraphs,
                "traced": r.traced,
                "coverage_pct": r.coverage_pct,
                "citations": r.citations_added,
            }
            for r in results
        ],
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    return REPORT_PATH


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for dossier tracing."""
    parser = argparse.ArgumentParser(
        description="Add DNA traceability citations to dossier paragraphs."
    )
    parser.add_argument(
        "--person",
        type=str,
        default=None,
        help='Filter to a single person (e.g. "Alex Hormozi", "jordan-lee")',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview matches without modifying dossier files.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=SIMILARITY_THRESHOLD,
        help=f"Similarity threshold for fuzzy matching (default: {SIMILARITY_THRESHOLD})",
    )
    args = parser.parse_args(argv)

    threshold = args.threshold

    # Discover dossiers
    dossiers = discover_dossiers(person_filter=args.person)
    if not dossiers:
        print(f"No dossiers found{f' for {args.person}' if args.person else ''}.")
        return 1

    print(f"Found {len(dossiers)} dossier(s) to trace.")
    if args.dry_run:
        print("[DRY RUN] Files will not be modified.\n")
    print()

    # Process each dossier
    results: list[TraceResult] = []
    for dossier_path in dossiers:
        slug = _slug_from_dossier_path(dossier_path)
        print(f"Tracing: {slug}")

        result = trace_dossier(dossier_path, dry_run=args.dry_run, threshold=threshold)
        results.append(result)

        if result.traced > 0:
            print(f"  {result.traced}/{result.total_paragraphs} paragraphs traced "
                  f"({result.coverage_pct}% coverage)")
            print(f"  {len(result.citations_added)} citation(s) added")
        else:
            dna_count = len(load_person_dna(slug))
            if dna_count == 0:
                print(f"  No DNA entries found for {slug} -- skipped")
            else:
                print(f"  0% coverage ({dna_count} DNA entries, "
                      f"{result.total_paragraphs} paragraphs, no matches)")
        print()

    # Write report
    report_path = write_report(results)
    print(f"Report written to: {report_path}")

    # Summary
    total_traced = sum(r.traced for r in results)
    total_paras = sum(r.total_paragraphs for r in results)
    total_citations = sum(len(r.citations_added) for r in results)
    avg_coverage = round(
        sum(r.coverage_pct for r in results) / len(results) if results else 0, 1
    )

    print(f"\nSummary:")
    print(f"  Dossiers processed:  {len(results)}")
    print(f"  Total paragraphs:    {total_paras}")
    print(f"  Paragraphs traced:   {total_traced}")
    print(f"  Citations added:     {total_citations}")
    print(f"  Average coverage:    {avg_coverage}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
