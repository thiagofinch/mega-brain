#!/usr/bin/env python3
"""
MEMORY SPLITTER - Phase 2.1
============================
Splits monolithic MEMORY.md into per-domain files under memory/ directory.
Reuses parse_memory_sections() from context_assembler.py.
Uses DOMAINS-TAXONOMY.yaml for domain classification.

Result:
  agents/cargo/sales/closer/
  +-- MEMORY.md       <- Lightweight index (~5KB)
  +-- memory/
      +-- _INDEX.yaml
      +-- vendas.md
      +-- compensation.md
      +-- ...

Zero external deps (stdlib + PyYAML only).

Versao: 1.0.0
Data: 2026-03-01
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

from .context_assembler import MemorySection, parse_memory_sections
from .query_analyzer import discover_agents, load_taxonomy

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
from core.paths import ROOT

DEFAULT_UNCATEGORIZED_DOMAIN = "geral"
BACKUP_SUFFIX = ".backup"

# Priority sections that go into every split (kept in index MEMORY.md)
INDEX_SECTIONS = {
    "TEAM AGREEMENT",
    "QUEM SOU EU",
    "PADROES DECISORIOS",
    "PADRAO DECISORIO",
    "METADADOS DE CONTEXTO",
    "KNOWLEDGE BASE LOCATIONS",
}


# ---------------------------------------------------------------------------
# DOMAIN CLASSIFIER
# ---------------------------------------------------------------------------
def _build_keyword_to_domain() -> dict[str, str]:
    """Build flat map: keyword -> domain_id from DOMAINS-TAXONOMY.yaml."""
    tax = load_taxonomy()
    kw_map: dict[str, str] = {}
    for dom in tax.get("dominios", []):
        did = dom["id"]
        for key in [did, *dom.get("aliases", []), *dom.get("subdominios", [])]:
            kw_map[key.lower()] = did
    return kw_map


def classify_section(section: MemorySection, kw_map: dict[str, str]) -> str:
    """Classify a MEMORY section into a domain using keyword matching.

    Returns domain_id or DEFAULT_UNCATEGORIZED_DOMAIN.
    """
    title_lower = section.title.lower()
    content_sample = section.content[:3000].lower()

    # Score each domain
    domain_scores: dict[str, int] = {}
    for keyword, domain_id in kw_map.items():
        hits = 0
        # Title match = stronger signal
        if keyword in title_lower:
            hits += 3
        if keyword in content_sample:
            hits += 1
        if hits > 0:
            domain_scores[domain_id] = domain_scores.get(domain_id, 0) + hits

    if not domain_scores:
        return DEFAULT_UNCATEGORIZED_DOMAIN

    # Return highest scoring domain
    return max(domain_scores, key=domain_scores.get)


# ---------------------------------------------------------------------------
# SPLITTER
# ---------------------------------------------------------------------------
def split_memory(
    agent_path: Path,
    dry_run: bool = False,
) -> dict:
    """Split MEMORY.md into per-domain files.

    Args:
        agent_path: Path to agent directory (e.g. agents/cargo/sales/closer/)
        dry_run: If True, only report what would happen

    Returns:
        {
            "agent": str,
            "original_size_kb": float,
            "sections_total": int,
            "domains": {domain_id: {"sections": int, "size_kb": float, "file": str}},
            "index_sections": int,
            "backup_path": str,
            "dry_run": bool,
        }
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

    # Build keyword map
    kw_map = _build_keyword_to_domain()

    # Classify sections
    domain_sections: dict[str, list[MemorySection]] = {}
    index_secs: list[MemorySection] = []

    for sec in sections:
        # Check if it's a priority/index section
        is_index = any(p.lower() in sec.title.lower() for p in INDEX_SECTIONS)
        if is_index:
            index_secs.append(sec)
            continue

        domain = classify_section(sec, kw_map)
        domain_sections.setdefault(domain, []).append(sec)

    # Prepare output
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

    # 1. Backup original
    if not backup_path.exists():
        shutil.copy2(memory_path, backup_path)

    # 2. Create memory/ directory
    memory_dir.mkdir(exist_ok=True)

    # 3. Write domain files
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

    # 4. Write _INDEX.yaml
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
        yaml.dump(index_yaml, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # 5. Write new lightweight MEMORY.md (index only)
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
    """Build the lightweight index MEMORY.md."""
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
    """Split MEMORY.md for all agents whose MEMORY exceeds min_memory_kb.

    Args:
        min_memory_kb: Only split if MEMORY.md > this size
        dry_run: If True, only report

    Returns list of results per agent.
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

    parser = argparse.ArgumentParser(description="Split monolithic MEMORY.md into per-domain files")
    parser.add_argument(
        "agent", nargs="?", help="Agent name (e.g. CLOSER) or 'all' for batch processing"
    )
    parser.add_argument("--dry-run", action="store_true", help="Only report what would happen")
    parser.add_argument(
        "--min-kb", type=int, default=50, help="Minimum MEMORY.md size in KB to split (default: 50)"
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
        # Find agent
        agent_path = None
        for name, path in agents.items():
            if name.upper().replace("-", "_") == canonical or name.upper() == args.agent.upper():
                agent_path = path
                break

        if not agent_path:
            print(f"Agent '{args.agent}' not found. Available: {', '.join(sorted(agents.keys()))}")
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
            print(f"  {dom}: {info['sections']} sections, {info['size_kb']}KB → {info['file']}")
        print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
