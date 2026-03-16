#!/usr/bin/env python3
"""
MEMORY SPLITTER
===============
Splits monolithic MEMORY.md into per-domain files under a memory/ subdirectory.
Uses DOMAINS-TAXONOMY.yaml for domain classification.
Backs up original MEMORY.md as MEMORY.md.bak.

Result:
  agents/cargo/sales/closer/
  +-- MEMORY.md         <- Lightweight index (~5KB)
  +-- MEMORY.md.bak     <- Backup of original
  +-- memory/
      +-- _INDEX.yaml
      +-- vendas.md
      +-- compensation.md
      +-- ...

Zero external deps (stdlib + PyYAML only).

Usage:
  python3 -m core.intelligence.memory_splitter CLOSER
  python3 -m core.intelligence.memory_splitter all --dry-run
  python3 -m core.intelligence.memory_splitter --min-kb 100

Versao: 1.0.0
Data: 2026-03-16
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# PATHS (from core.paths, isolated for standalone use)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_EXTERNAL = ROOT / "knowledge" / "external"
AGENTS = ROOT / "agents"
TAXONOMY_PATH = KNOWLEDGE_EXTERNAL / "dna" / "DOMAINS-TAXONOMY.yaml"

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DEFAULT_UNCATEGORIZED_DOMAIN = "geral"
BACKUP_SUFFIX = ".bak"

# Priority sections that stay in the index MEMORY.md (not split into domains)
INDEX_SECTION_KEYWORDS = {
    "team agreement",
    "quem sou eu",
    "padroes decisorios",
    "padrao decisorio",
    "metadados de contexto",
    "knowledge base locations",
}


# ---------------------------------------------------------------------------
# SECTION PARSER
# ---------------------------------------------------------------------------
@dataclass
class MemorySection:
    """Represents a ## section in MEMORY.md."""

    title: str
    content: str
    start_line: int
    end_line: int
    size_bytes: int = 0
    domains_matched: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.size_bytes = len(self.content.encode("utf-8"))


def parse_memory_sections(text: str) -> list[MemorySection]:
    """Parse MEMORY.md text into a list of ## sections.

    Each section starts at a `## ` heading and includes all content
    until the next `## ` heading or end of file.
    """
    lines = text.split("\n")
    sections: list[MemorySection] = []
    current_title = ""
    current_lines: list[str] = []
    current_start = 0

    for i, line in enumerate(lines):
        if line.startswith("## "):
            if current_title or current_lines:
                content = "\n".join(current_lines)
                sections.append(
                    MemorySection(
                        title=current_title,
                        content=content,
                        start_line=current_start,
                        end_line=i - 1,
                    )
                )
            current_title = line[3:].strip()
            current_lines = [line]
            current_start = i
        else:
            current_lines.append(line)

    # Last section
    if current_title or current_lines:
        content = "\n".join(current_lines)
        sections.append(
            MemorySection(
                title=current_title,
                content=content,
                start_line=current_start,
                end_line=len(lines) - 1,
            )
        )

    return sections


# ---------------------------------------------------------------------------
# TAXONOMY LOADER
# ---------------------------------------------------------------------------
_taxonomy_cache: dict | None = None


def load_taxonomy() -> dict:
    """Load DOMAINS-TAXONOMY.yaml with caching."""
    global _taxonomy_cache
    if _taxonomy_cache is not None:
        return _taxonomy_cache
    try:
        with open(TAXONOMY_PATH, encoding="utf-8") as f:
            _taxonomy_cache = yaml.safe_load(f) or {}
    except FileNotFoundError:
        _taxonomy_cache = {}
    return _taxonomy_cache


# ---------------------------------------------------------------------------
# DOMAIN CLASSIFIER
# ---------------------------------------------------------------------------
def _build_keyword_to_domain() -> dict[str, str]:
    """Build flat map: keyword -> domain_id from DOMAINS-TAXONOMY.yaml.

    Maps domain IDs, aliases, and subdomain names all to their parent domain ID.
    This gives us a wide vocabulary for keyword matching against section content.
    """
    tax = load_taxonomy()
    kw_map: dict[str, str] = {}
    for dom in tax.get("dominios", []):
        did = dom["id"]
        for key in [did, *dom.get("aliases", []), *dom.get("subdominios", [])]:
            kw_map[key.lower()] = did
    return kw_map


def classify_section(section: MemorySection, kw_map: dict[str, str]) -> str:
    """Classify a MEMORY section into a domain using keyword matching.

    Scoring: title keyword match = 3 points, content match = 1 point.
    Returns domain_id with highest score, or DEFAULT_UNCATEGORIZED_DOMAIN.
    """
    title_lower = section.title.lower()
    # Only scan first 3000 chars of content for performance on large sections
    content_sample = section.content[:3000].lower()

    domain_scores: dict[str, int] = {}
    for keyword, domain_id in kw_map.items():
        hits = 0
        if keyword in title_lower:
            hits += 3
        if keyword in content_sample:
            hits += 1
        if hits > 0:
            domain_scores[domain_id] = domain_scores.get(domain_id, 0) + hits

    if not domain_scores:
        return DEFAULT_UNCATEGORIZED_DOMAIN

    return max(domain_scores, key=domain_scores.get)  # type: ignore[arg-type]


def _is_index_section(title: str) -> bool:
    """Check if a section title matches priority/index patterns."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in INDEX_SECTION_KEYWORDS)


# ---------------------------------------------------------------------------
# AGENT DISCOVERY
# ---------------------------------------------------------------------------
def discover_agents() -> dict[str, Path]:
    """Discover all agents that have a MEMORY.md file.

    Scans agents/ directory tree for any directory containing MEMORY.md.
    Returns {agent_name: agent_dir_path}.
    """
    agents: dict[str, Path] = {}
    if not AGENTS.exists():
        return agents

    for memory_file in AGENTS.rglob("MEMORY.md"):
        agent_dir = memory_file.parent
        # Skip memory/ subdirectories (already-split files)
        if agent_dir.name == "memory":
            continue
        agents[agent_dir.name] = agent_dir

    return agents


# ---------------------------------------------------------------------------
# SPLITTER CORE
# ---------------------------------------------------------------------------
def split_memory(
    agent_path: Path,
    dry_run: bool = False,
) -> dict:
    """Split MEMORY.md into per-domain files.

    Args:
        agent_path: Path to agent directory (e.g. agents/cargo/sales/closer/)
        dry_run: If True, only report what would happen -- no files modified.

    Returns dict with split results including domain breakdown.
    """
    memory_path = agent_path / "MEMORY.md"
    if not memory_path.exists():
        return {"error": f"MEMORY.md not found at {memory_path}"}

    # Read and parse
    full_text = memory_path.read_text(encoding="utf-8")
    original_size = len(full_text.encode("utf-8"))
    sections = parse_memory_sections(full_text)

    if not sections:
        return {"error": "No sections found in MEMORY.md"}

    # Build keyword map from taxonomy
    kw_map = _build_keyword_to_domain()

    # Classify each section
    domain_sections: dict[str, list[MemorySection]] = {}
    index_secs: list[MemorySection] = []

    for sec in sections:
        if _is_index_section(sec.title):
            index_secs.append(sec)
            continue
        domain = classify_section(sec, kw_map)
        domain_sections.setdefault(domain, []).append(sec)

    # Prepare paths
    memory_dir = agent_path / "memory"
    backup_path = agent_path / f"MEMORY.md{BACKUP_SUFFIX}"

    if dry_run:
        result = {
            "agent": agent_path.name,
            "original_size_kb": round(original_size / 1024, 1),
            "sections_total": len(sections),
            "index_sections": len(index_secs),
            "domains": {},
            "dry_run": True,
        }
        for domain, secs in sorted(domain_sections.items()):
            size = sum(s.size_bytes for s in secs)
            result["domains"][domain] = {
                "sections": len(secs),
                "size_kb": round(size / 1024, 1),
                "file": f"memory/{domain}.md",
            }
        return result

    # --- WRITE FILES ---

    # 1. Backup original MEMORY.md as MEMORY.md.bak
    if not backup_path.exists():
        shutil.copy2(memory_path, backup_path)

    # 2. Create memory/ directory
    memory_dir.mkdir(exist_ok=True)

    # 3. Write per-domain files
    index_entries: list[dict] = []

    for domain, secs in sorted(domain_sections.items()):
        domain_file = memory_dir / f"{domain}.md"
        parts = [f"# MEMORY: {domain.upper()}\n"]
        parts.append(f"> Domain: {domain}")
        parts.append(f"> Sections: {len(secs)}")
        parts.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        for sec in secs:
            parts.append(sec.content)

        domain_file.write_text("\n\n".join(parts), encoding="utf-8")
        size = domain_file.stat().st_size

        index_entries.append(
            {
                "domain": domain,
                "file": f"memory/{domain}.md",
                "sections": len(secs),
                "size_bytes": size,
                "section_titles": [s.title for s in secs],
            }
        )

    # 4. Write memory/_INDEX.yaml
    index_yaml = {
        "version": "1.0.0",
        "generated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "agent": agent_path.name,
        "original_memory_size_bytes": original_size,
        "domains": index_entries,
        "total_domain_files": len(index_entries),
        "total_sections_split": sum(e["sections"] for e in index_entries),
        "index_sections_kept": len(index_secs),
    }
    index_path = memory_dir / "_INDEX.yaml"
    with open(index_path, "w", encoding="utf-8") as f:
        yaml.dump(
            index_yaml,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    # 5. Write new lightweight MEMORY.md (index + priority sections only)
    new_memory = _build_index_memory(agent_path.name, index_secs, index_entries, original_size)
    memory_path.write_text(new_memory, encoding="utf-8")

    # Build result
    result = {
        "agent": agent_path.name,
        "original_size_kb": round(original_size / 1024, 1),
        "new_index_size_kb": round(len(new_memory.encode("utf-8")) / 1024, 1),
        "sections_total": len(sections),
        "index_sections": len(index_secs),
        "domains": {},
        "backup_path": str(backup_path),
        "memory_dir": str(memory_dir),
        "dry_run": False,
    }
    for entry in index_entries:
        result["domains"][entry["domain"]] = {
            "sections": entry["sections"],
            "size_kb": round(entry["size_bytes"] / 1024, 1),
            "file": entry["file"],
        }

    return result


def _build_index_memory(
    agent_name: str,
    index_sections: list[MemorySection],
    domain_entries: list[dict],
    original_size: int,
) -> str:
    """Build the lightweight index MEMORY.md that replaces the original.

    Contains:
    - Header with metadata (original size, split count, generation date)
    - Domain files table (domain | sections | size | file path)
    - Priority sections inline (team agreement, decision patterns, etc.)
    """
    parts = []
    parts.append(f"# MEMORY: {agent_name.upper()}\n")
    parts.append("> **Type:** Split index (domain files in `memory/` directory)")
    parts.append(f"> **Original size:** {round(original_size / 1024, 1)}KB")
    parts.append(f"> **Split into:** {len(domain_entries)} domain files")
    parts.append(f"> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Domain index table
    parts.append("## DOMAIN FILES\n")
    parts.append("| Domain | Sections | Size | File |")
    parts.append("|--------|----------|------|------|")
    for entry in domain_entries:
        size_kb = round(entry["size_bytes"] / 1024, 1)
        parts.append(
            f"| {entry['domain']} | {entry['sections']} | {size_kb}KB | `{entry['file']}` |"
        )
    parts.append("")

    # Keep priority/index sections inline
    if index_sections:
        parts.append("---\n")
        for sec in index_sections:
            parts.append(sec.content)
            parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# BATCH SPLIT (all agents)
# ---------------------------------------------------------------------------
def split_all_agents(
    min_memory_kb: int = 50,
    dry_run: bool = False,
) -> list[dict]:
    """Split MEMORY.md for all agents whose file exceeds min_memory_kb.

    Args:
        min_memory_kb: Only split if MEMORY.md > this size (default 50KB)
        dry_run: If True, only report -- no files modified.

    Returns list of result dicts per agent.
    """
    agents = discover_agents()
    results = []

    for _name, path in sorted(agents.items()):
        memory_path = path / "MEMORY.md"
        if not memory_path.exists():
            continue
        size_kb = memory_path.stat().st_size / 1024
        if size_kb < min_memory_kb:
            continue

        result = split_memory(path, dry_run=dry_run)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Split monolithic MEMORY.md into per-domain files"
    )
    parser.add_argument(
        "agent",
        nargs="?",
        help="Agent name (e.g. CLOSER) or 'all' for batch processing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report what would happen",
    )
    parser.add_argument(
        "--min-kb",
        type=int,
        default=50,
        help="Minimum MEMORY.md size in KB to split (default: 50)",
    )
    args = parser.parse_args()

    if not args.agent or args.agent.lower() == "all":
        print(f"\n{'=' * 60}")
        print("MEMORY SPLITTER - Batch Mode")
        print(f"{'=' * 60}")
        if args.dry_run:
            print("[DRY RUN] No files will be modified.\n")

        results = split_all_agents(min_memory_kb=args.min_kb, dry_run=args.dry_run)
        if not results:
            print("No agents with MEMORY.md above threshold.")
            return

        for r in results:
            if "error" in r:
                print(f"  {r.get('agent', '?')}: ERROR - {r['error']}")
                continue
            print(f"\n  {r['agent']}:")
            print(f"    Original: {r['original_size_kb']}KB, {r['sections_total']} sections")
            if not args.dry_run:
                print(f"    New index: {r.get('new_index_size_kb', '?')}KB")
            print(f"    Domains: {len(r['domains'])}")
            for dom, info in r["domains"].items():
                print(f"      {dom}: {info['sections']} sections, {info['size_kb']}KB")
    else:
        agents = discover_agents()
        canonical = args.agent.upper().replace("-", "_")
        # Find agent by name (case-insensitive, hyphen/underscore agnostic)
        agent_path = None
        for name, path in agents.items():
            if (
                name.upper().replace("-", "_") == canonical
                or name.upper() == args.agent.upper()
            ):
                agent_path = path
                break

        if not agent_path:
            print(
                f"Agent '{args.agent}' not found. Available: {', '.join(sorted(agents.keys()))}"
            )
            sys.exit(1)

        result = split_memory(agent_path, dry_run=args.dry_run)
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"\n{'=' * 60}")
        print(f"MEMORY SPLITTER: {result['agent']}")
        print(f"{'=' * 60}")
        if args.dry_run:
            print("[DRY RUN] No files will be modified.\n")
        print(f"Original: {result['original_size_kb']}KB, {result['sections_total']} sections")
        if not args.dry_run:
            print(f"New index: {result.get('new_index_size_kb', '?')}KB")
            print(f"Backup: {result.get('backup_path', 'N/A')}")
        print(f"Index sections kept: {result['index_sections']}")
        print(f"\nDomains ({len(result['domains'])}):")
        for dom, info in result["domains"].items():
            print(f"  {dom}: {info['sections']} sections, {info['size_kb']}KB -> {info['file']}")
        print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
