"""
dossier_compiler.py -- Compile scattered insights into structured dossiers
=========================================================================
Reads per-person insights from INSIGHTS-STATE.json and compiles them into
formatted dossier markdown files. When a dossier already exists, new insights
are merged into existing sections (append, not replace).

Routing:
    External bucket -> knowledge/external/dossiers/persons/DOSSIER-{NAME}.md
    Business bucket -> knowledge/business/dossiers/persons/DOSSIER-{NAME}.md

Domain classification uses DOMAINS-TAXONOMY.yaml (not hardcoded strings).

Usage:
    python3 -m core.intelligence.pipeline.dossier_compiler --person "Cole Gordon"
    python3 -m core.intelligence.pipeline.dossier_compiler --all
    python3 -m core.intelligence.pipeline.dossier_compiler --person "Pedro Valério" --dry-run

Version: 1.0.0
Date: 2026-03-16
Story: W2.1
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from core.paths import (
    ARTIFACTS,
    KNOWLEDGE_BUSINESS,
    KNOWLEDGE_EXTERNAL,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

INSIGHTS_STATE_PATH = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
DOMAINS_TAXONOMY_PATH = KNOWLEDGE_EXTERNAL / "dna" / "DOMAINS-TAXONOMY.yaml"

EXTERNAL_DOSSIERS_DIR = KNOWLEDGE_EXTERNAL / "dossiers" / "persons"
BUSINESS_DOSSIERS_DIR = KNOWLEDGE_BUSINESS / "dossiers" / "persons"

# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------


@dataclass
class Insight:
    """A single extracted insight attributed to a person."""

    id: str
    text: str
    tag: str = ""
    priority: str = "MEDIUM"
    confidence: str = "MEDIUM"
    chunks: list[str] = field(default_factory=list)
    quote: str = ""
    source: str = ""
    person: str = ""
    status: str = ""


@dataclass
class PersonInsights:
    """All insights for a single person, ready for compilation."""

    name: str
    bucket: str  # "external" or "business"
    insights: list[Insight] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


@dataclass
class CompilationResult:
    """Result of compiling a dossier."""

    person: str
    output_path: Path
    total_insights: int
    domains_used: list[str]
    is_update: bool  # True if dossier already existed (merge)
    new_insights_added: int


# ---------------------------------------------------------------------------
# TAXONOMY LOADER
# ---------------------------------------------------------------------------


class DomainTaxonomy:
    """Loads DOMAINS-TAXONOMY.yaml and provides classification methods."""

    def __init__(self, taxonomy_path: Path = DOMAINS_TAXONOMY_PATH):
        self.domains: list[dict] = []
        self.pessoas: dict[str, dict] = {}
        self._domain_lookup: dict[str, dict] = {}
        self._alias_to_id: dict[str, str] = {}
        self._tag_to_domains: dict[str, list[str]] = {}
        self._load(taxonomy_path)

    def _load(self, path: Path) -> None:
        if not path.exists():
            logger.warning("DOMAINS-TAXONOMY.yaml not found at %s, using fallback", path)
            return
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        self.domains = data.get("dominios", [])
        self.pessoas = data.get("pessoas", {})

        for dom in self.domains:
            dom_id = dom["id"]
            self._domain_lookup[dom_id] = dom
            for alias in dom.get("aliases", []):
                self._alias_to_id[alias.lower()] = dom_id

        # Build tag -> domains mapping based on known patterns
        self._tag_to_domains = {
            "[FILOSOFIA]": ["mindset"],
            "[MODELO-MENTAL]": ["mindset"],
            "[HEURISTICA]": ["vendas", "operations"],
            "[FRAMEWORK]": ["scaling", "operations"],
            "[METODOLOGIA]": ["operations"],
        }

    def classify_insight(self, insight: Insight) -> str:
        """Classify an insight into a domain ID using tag + keyword heuristics."""
        # Step 1: Try tag-based classification
        tag = insight.tag.strip()
        candidates = self._tag_to_domains.get(tag, [])

        # Step 2: Keyword scan against domain aliases
        text_lower = (insight.text + " " + insight.quote).lower()
        keyword_hits: dict[str, int] = {}
        for dom in self.domains:
            dom_id = dom["id"]
            score = 0
            # Check domain ID itself
            if dom_id in text_lower:
                score += 2
            # Check aliases
            for alias in dom.get("aliases", []):
                if alias.lower() in text_lower:
                    score += 1
            # Check subdomains
            for sub in dom.get("subdominios", []):
                if sub.lower() in text_lower:
                    score += 1
            if score > 0:
                keyword_hits[dom_id] = score

        # Step 3: Merge tag candidates with keyword hits
        if keyword_hits:
            best = max(keyword_hits, key=keyword_hits.get)
            return best
        if candidates:
            return candidates[0]

        # Step 4: Fallback to "general" (uncategorized)
        return "general"

    def is_external_person(self, name: str) -> bool:
        """Check if a person is in the external taxonomy (known expert)."""
        slug = name.upper().replace(" ", "-")
        return slug in self.pessoas

    def get_person_expertise(self, name: str) -> list[str]:
        """Get primary expertise domains for a known external person."""
        slug = name.upper().replace(" ", "-")
        pessoa = self.pessoas.get(slug, {})
        return pessoa.get("expertise_primaria", [])

    def get_domain_label(self, domain_id: str) -> str:
        """Get human-readable label for a domain ID."""
        dom = self._domain_lookup.get(domain_id)
        if dom:
            return dom.get("descricao", domain_id.title())
        return domain_id.title()


# ---------------------------------------------------------------------------
# INSIGHTS LOADER
# ---------------------------------------------------------------------------


def _slugify(name: str) -> str:
    """Convert a person name to a filesystem-safe slug. 'Cole Gordon' -> 'COLE-GORDON'."""
    # Normalize unicode (remove accents)
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    # Replace spaces/special chars with hyphens
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-")
    return slug.upper()


def load_insights_state(path: Path = INSIGHTS_STATE_PATH) -> dict:
    """Load and return the full INSIGHTS-STATE.json."""
    if not path.exists():
        logger.error("INSIGHTS-STATE.json not found at %s", path)
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def gather_person_insights(
    state: dict,
    person_name: str,
    taxonomy: DomainTaxonomy,
) -> PersonInsights | None:
    """
    Gather all insights for a specific person from INSIGHTS-STATE.json.

    Handles two data shapes in the 'persons' section:
    1. List of insights (person-level entries like "Alex Hormozi")
    2. Dict with 'insights' key (meeting-level entries like "MEET-0026")

    For meeting-level entries, filters insights by the 'person' field.
    """
    persons_data = state.get("persons", {})
    all_insights: list[Insight] = []
    sources: set[str] = set()

    # Determine bucket
    is_external = taxonomy.is_external_person(person_name)

    # Pass 1: Check if person has a direct entry (person-level)
    direct_entry = persons_data.get(person_name)
    if direct_entry is not None:
        if isinstance(direct_entry, list):
            # Person-level list of insights (e.g., "Alex Hormozi": [...])
            for raw in direct_entry:
                ins = _parse_insight(raw)
                ins.person = person_name
                all_insights.append(ins)
                if ins.source:
                    sources.add(ins.source)
        elif isinstance(direct_entry, dict) and "insights" in direct_entry:
            # Meeting-keyed dict with insights list, filter by person
            source_id = direct_entry.get("source", "")
            for raw in direct_entry.get("insights", []):
                if raw.get("person", "") == person_name:
                    ins = _parse_insight(raw)
                    ins.person = person_name
                    if source_id:
                        ins.source = source_id
                        sources.add(source_id)
                    all_insights.append(ins)

    # Pass 2: Scan ALL entries for meeting-level insights attributed to this person
    for key, entry in persons_data.items():
        if key == person_name:
            continue  # Already processed above
        if not isinstance(entry, dict) or "insights" not in entry:
            continue
        source_id = entry.get("source", key)
        bucket_from_entry = entry.get("bucket", "")
        for raw in entry.get("insights", []):
            if raw.get("person", "") == person_name:
                ins = _parse_insight(raw)
                ins.person = person_name
                ins.source = source_id
                sources.add(source_id)
                all_insights.append(ins)
                # If this person appears in business meetings, note it
                if bucket_from_entry == "business" and is_external:
                    # External expert mentioned in business meetings stays external
                    pass

    # Also check the top-level 'categories' section for insights matching this person
    # (Jordan Lee / Liam Ottley style entries are person-level lists, already handled above)

    if not all_insights:
        return None

    bucket = "external" if is_external else "business"
    return PersonInsights(
        name=person_name,
        bucket=bucket,
        insights=all_insights,
        sources=sorted(sources),
    )


def _parse_insight(raw: dict) -> Insight:
    """Parse a raw insight dict into an Insight dataclass.

    Handles the 'source' field being either a string or a dict
    (e.g., {"source_type": "course", "source_id": "LO-001", ...}).
    """
    raw_source = raw.get("source", "")
    if isinstance(raw_source, dict):
        source_str = raw_source.get("source_id", "") or raw_source.get("source_title", "")
    else:
        source_str = str(raw_source)

    return Insight(
        id=raw.get("id", ""),
        text=raw.get("insight", ""),
        tag=raw.get("tag", ""),
        priority=raw.get("priority", "MEDIUM"),
        confidence=raw.get("confidence", "MEDIUM"),
        chunks=raw.get("chunks", []),
        quote=raw.get("quote", ""),
        source=source_str,
        person=raw.get("person", ""),
        status=raw.get("status", ""),
    )


def get_all_person_names(state: dict) -> list[str]:
    """
    Extract all unique person names from INSIGHTS-STATE.json.

    Returns names from:
    - Direct person-level entries (where key is a person name, not MEET-XXXX)
    - Per-insight 'person' fields inside meeting-level entries
    """
    names: set[str] = set()
    persons_data = state.get("persons", {})

    for key, entry in persons_data.items():
        # Skip meeting-keyed entries at top level
        if key.startswith("MEET-"):
            # Scan insights for person names
            if isinstance(entry, dict):
                for raw in entry.get("insights", []):
                    person = raw.get("person", "")
                    if person:
                        names.add(person)
        else:
            # Person-level entry
            if isinstance(entry, list) and entry:
                names.add(key)
            elif isinstance(entry, dict):
                # Dict entry like Thiago Finch or Diego Monet
                # Only add if they have insights somewhere
                if entry.get("insight_count", 0) > 0:
                    names.add(key)

    return sorted(names)


# ---------------------------------------------------------------------------
# DOSSIER FORMATTING
# ---------------------------------------------------------------------------

DOSSIER_HEADER_TEMPLATE = """# DOSSIER -- {name}

> **Tipo:** Pessoa ({bucket_label})
> **Sources:** {sources}
> **Ultima atualizacao:** {date}
> **Versao:** {version}
> **Total insights:** {total}

---
"""

DOMAIN_SECTION_TEMPLATE = """## {domain_label}

{insights_block}

---
"""


def _format_insight_block(insight: Insight) -> str:
    """Format a single insight as a markdown block."""
    lines = []
    priority_marker = ""
    if insight.priority == "HIGH":
        priority_marker = " [HIGH]"

    lines.append(f"- **{insight.text}**{priority_marker}")

    if insight.quote:
        lines.append(f'  > "{insight.quote}"')

    ref_parts = []
    if insight.id:
        ref_parts.append(insight.id)
    if insight.chunks:
        ref_parts.extend(insight.chunks)
    if insight.source:
        ref_parts.append(insight.source)
    if ref_parts:
        lines.append(f"  ^[{', '.join(ref_parts)}]")

    return "\n".join(lines)


def compile_dossier(
    person: PersonInsights,
    taxonomy: DomainTaxonomy,
    dry_run: bool = False,
) -> CompilationResult:
    """
    Compile insights into a dossier file.

    If the dossier already exists, appends new insights to matching domain
    sections. Never overwrites existing content.
    """
    # Determine output path
    slug = _slugify(person.name)
    if person.bucket == "external":
        output_dir = EXTERNAL_DOSSIERS_DIR
    else:
        output_dir = BUSINESS_DOSSIERS_DIR

    output_path = output_dir / f"DOSSIER-{slug}.md"

    # Classify insights by domain
    domain_insights: dict[str, list[Insight]] = {}
    for ins in person.insights:
        domain = taxonomy.classify_insight(ins)
        if domain not in domain_insights:
            domain_insights[domain] = []
        domain_insights[domain].append(ins)

    # Check if dossier already exists
    is_update = output_path.exists()
    existing_insight_ids: set[str] = set()

    if is_update:
        existing_content = output_path.read_text(encoding="utf-8")
        # Extract existing insight IDs from ^[...] citations to avoid duplicates
        existing_insight_ids = _extract_existing_ids(existing_content)
    else:
        existing_content = ""

    # Filter out already-compiled insights
    new_domain_insights: dict[str, list[Insight]] = {}
    new_count = 0
    for domain, insights in domain_insights.items():
        new_list = [ins for ins in insights if ins.id not in existing_insight_ids]
        if new_list:
            new_domain_insights[domain] = new_list
            new_count += len(new_list)

    if new_count == 0 and is_update:
        logger.info("No new insights for %s -- dossier is up to date", person.name)
        return CompilationResult(
            person=person.name,
            output_path=output_path,
            total_insights=len(person.insights),
            domains_used=sorted(domain_insights.keys()),
            is_update=True,
            new_insights_added=0,
        )

    if is_update:
        # Merge new insights into existing dossier
        merged = _merge_into_existing(existing_content, new_domain_insights, taxonomy, person)
    else:
        # Build new dossier from scratch
        merged = _build_new_dossier(person, domain_insights, taxonomy)

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path.write_text(merged, encoding="utf-8")
        logger.info(
            "Compiled dossier for %s -> %s (%d new insights)",
            person.name,
            output_path,
            new_count if is_update else len(person.insights),
        )
    else:
        logger.info("[DRY RUN] Would write dossier for %s -> %s", person.name, output_path)

    return CompilationResult(
        person=person.name,
        output_path=output_path,
        total_insights=len(person.insights),
        domains_used=sorted(domain_insights.keys()),
        is_update=is_update,
        new_insights_added=new_count if is_update else len(person.insights),
    )


def _extract_existing_ids(content: str) -> set[str]:
    """Extract insight IDs from existing dossier content.

    Looks for patterns like ^[AH-CP001-001, ...] and extracts all IDs.
    Also looks for insight IDs in markdown bold patterns like **insight text** [ID].
    """
    ids: set[str] = set()
    # Match ^[ref1, ref2, ...] citation blocks
    for match in re.finditer(r"\^\[([^\]]+)\]", content):
        refs = match.group(1)
        for part in refs.split(","):
            part = part.strip()
            # Insight IDs have patterns like AH-CP001-001, MEET0026-001, etc.
            if re.match(r"^[A-Z]+-?\w+-\d+", part) or re.match(r"^MEET\d+-\d+", part):
                ids.add(part)
    return ids


def _build_new_dossier(
    person: PersonInsights,
    domain_insights: dict[str, list[Insight]],
    taxonomy: DomainTaxonomy,
) -> str:
    """Build a complete new dossier from scratch."""
    now = dt.datetime.now(tz=dt.UTC).strftime("%Y-%m-%d")
    bucket_label = "External Expert" if person.bucket == "external" else "Business"

    header = DOSSIER_HEADER_TEMPLATE.format(
        name=person.name,
        bucket_label=bucket_label,
        sources=", ".join(person.sources) if person.sources else "INSIGHTS-STATE.json",
        date=now,
        version="1.0.0",
        total=len(person.insights),
    )

    sections: list[str] = []

    # Sort domains: put expertise domains first for external persons
    expertise = taxonomy.get_person_expertise(person.name) if person.bucket == "external" else []
    sorted_domains = _sort_domains(domain_insights.keys(), expertise)

    for domain in sorted_domains:
        insights = domain_insights[domain]
        domain_label = taxonomy.get_domain_label(domain)
        insights_block = "\n\n".join(_format_insight_block(ins) for ins in insights)

        section = DOMAIN_SECTION_TEMPLATE.format(
            domain_label=domain_label,
            insights_block=insights_block,
        )
        sections.append(section)

    return header + "\n".join(sections)


def _merge_into_existing(
    existing: str,
    new_domain_insights: dict[str, list[Insight]],
    taxonomy: DomainTaxonomy,
    person: PersonInsights,
) -> str:
    """Merge new insights into an existing dossier.

    Strategy: For each domain with new insights, find the matching ## section
    in the existing dossier and append before the section's --- separator.
    If no matching section exists, append a new section at the end.
    """
    result = existing
    now = dt.datetime.now(tz=dt.UTC).strftime("%Y-%m-%d")

    # Update the "Ultima atualizacao" date in header
    result = re.sub(
        r"(\*\*Ultima atualizacao:\*\*)\s*\S+",
        rf"\1 {now}",
        result,
    )

    for domain, insights in new_domain_insights.items():
        domain_label = taxonomy.get_domain_label(domain)
        insights_block = "\n\n".join(_format_insight_block(ins) for ins in insights)
        append_block = f"\n\n{insights_block}"

        # Try to find existing section header
        section_pattern = re.compile(
            rf"(## {re.escape(domain_label)}.*?)((?=\n## )|(?=\n---\s*$)|\Z)",
            re.DOTALL,
        )
        match = section_pattern.search(result)

        if match:
            # Append to existing section (before the next section or end separator)
            insert_pos = match.end(1)
            result = result[:insert_pos] + append_block + result[insert_pos:]
        else:
            # No matching section -- append new section at the end
            new_section = f"\n{DOMAIN_SECTION_TEMPLATE.format(domain_label=domain_label, insights_block=insights_block)}"
            # Insert before the final --- if present, else append
            if result.rstrip().endswith("---"):
                result = result.rstrip()
                result = result[: result.rfind("---")] + new_section + "\n---\n"
            else:
                result = result.rstrip() + "\n\n" + new_section

    return result


def _sort_domains(domains: list[str] | set[str] | dict, expertise: list[str]) -> list[str]:
    """Sort domains: expertise domains first, then alphabetical."""
    domain_list = list(domains) if not isinstance(domains, list) else domains
    expertise_set = set(expertise)

    primary = [d for d in domain_list if d in expertise_set]
    secondary = sorted(d for d in domain_list if d not in expertise_set)
    return primary + secondary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entrypoint for dossier compilation."""
    parser = argparse.ArgumentParser(
        description="Compile insights from INSIGHTS-STATE.json into structured dossiers",
    )
    parser.add_argument(
        "--person",
        type=str,
        help="Person name to compile dossier for (exact match from INSIGHTS-STATE)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="compile_all",
        help="Compile dossiers for all persons with insights",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be compiled without writing files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    if not args.person and not args.compile_all:
        parser.error("Must specify --person NAME or --all")

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Load data
    state = load_insights_state()
    if not state:
        logger.error("Failed to load INSIGHTS-STATE.json")
        return 1

    taxonomy = DomainTaxonomy()

    results: list[CompilationResult] = []

    if args.compile_all:
        names = get_all_person_names(state)
        logger.info("Found %d persons with insights", len(names))
        for name in names:
            person = gather_person_insights(state, name, taxonomy)
            if person and person.insights:
                result = compile_dossier(person, taxonomy, dry_run=args.dry_run)
                results.append(result)
    else:
        person = gather_person_insights(state, args.person, taxonomy)
        if not person or not person.insights:
            logger.error("No insights found for '%s'", args.person)
            return 1
        result = compile_dossier(person, taxonomy, dry_run=args.dry_run)
        results.append(result)

    # Print summary
    print()
    print("=" * 60)
    print("DOSSIER COMPILATION SUMMARY")
    print("=" * 60)
    for r in results:
        status = "UPDATED" if r.is_update else "CREATED"
        if r.new_insights_added == 0:
            status = "UP-TO-DATE"
        print(
            f"  {r.person:<25} {status:<12} "
            f"+{r.new_insights_added} insights  "
            f"[{', '.join(r.domains_used)}]"
        )
        print(f"    -> {r.output_path}")
    print("=" * 60)
    print(f"Total: {len(results)} dossiers processed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
