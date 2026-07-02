#!/usr/bin/env python3
"""
bin/refresh-registry.py — Deterministic Ecosystem Registry Generator

Zero LLM. Pure filesystem traversal. Regenerates
agents/_registry/ecosystem-registry.yaml from the current directory tree.

Usage:
    python3 bin/refresh-registry.py                          # Regenerate live registry
    python3 bin/refresh-registry.py --output /tmp/test.yaml  # Write to custom path

Story 4.5 | Epic AGENT-ARCH | ADR-004 D3
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
DEFAULT_OUTPUT = AGENTS_DIR / "_registry" / "ecosystem-registry.yaml"

KEBAB_CASE = re.compile(r"^[a-z0-9]+([-.][a-z0-9]+)*$")

# Directories to skip during scan
SKIP_DIRS = {
    "_templates", "_registry", "_preserved", "_example", "example",
    "discovery", "__pycache__", ".DS_Store",
    "config", "scripts", "templates", "workflows",
}

# Root-level dirs under agents/ to skip (vestigial duplicates, deleted in Story 4.10)
SKIP_ROOT_DIRS = {"conclave"}

# Files that indicate "this is NOT an agent directory"
NON_AGENT_FILES = {"README.md", "SHARED-RULES.md"}

# Path prefix → category mapping (order matters: longer prefixes first)
CATEGORY_MAP = [
    ("system/pipeline-ops", "system/pipeline-ops"),
    ("system/conclave", "system/conclave"),
    ("system/dev-ops", "system/dev-ops"),
    ("system/knowledge-ops", "system/knowledge-ops"),
    # Catch-all for other system/* roots that aren't ops-suffixed (funnel-cartographer,
    # canon-populator, voc-miner, etc.). Must come AFTER the more-specific system/*
    # prefixes above so they win.
    ("system", "system"),
    ("business/collaborators", "business/collaborators"),
    ("business/partners", "business/partners"),
    ("business/advisors", "business/advisors"),
    ("business/alumni", "business/alumni"),
    ("business/meetings", "business/meetings"),
    # business-masters is a hyphenated top-level on disk (NOT business/masters)
    ("business-masters", "business-masters"),
    ("personal", "personal"),
    # Post-Wave 4 topology
    ("external/cargo", "external/cargo"),
    ("external/minds", "external/minds"),
    # Fallback: any external/{slug} not under minds/ or cargo/ → external/minds
    ("external", "external/minds"),
]

# Known partners (categorized via TAXONOMY rules) — populate with your own partner slugs
PARTNERS = set()

# Known deprecated agents
DEPRECATED = {"atlas", "sage", "lens", "echo", "forge"}


def infer_category(rel_path: Path, agent_id: str) -> str:
    """Infer category from the repo-relative path of the agent directory."""
    parts = rel_path.parts  # e.g., ('external', 'alex-hormozi')

    # Special case: partners
    if agent_id in PARTNERS:
        return "business/partners"

    path_str = "/".join(parts)

    for prefix, category in CATEGORY_MAP:
        if path_str.startswith(prefix):
            # For cargo, append the department
            if prefix == "external/cargo" and len(parts) >= 3:
                dept = parts[2]  # external/cargo/{dept}/...
                return f"external/cargo/{dept}"
            return category

    return "unknown"


def find_entry_file(agent_dir: Path) -> Path | None:
    """Find the primary entry file for an agent directory."""
    candidates = [
        agent_dir / "agent.md",
        agent_dir / "AGENT.md",
    ]
    for c in candidates:
        if c.exists():
            return c

    # Fallback: any .md file at depth 0
    md_files = sorted(agent_dir.glob("*.md"))
    for md in md_files:
        if md.name not in NON_AGENT_FILES:
            return md

    # Fallback: activation.yaml
    activation = agent_dir / "activation.yaml"
    if activation.exists():
        return activation

    return None


def find_profile(agent_dir: Path) -> str | None:
    """Check if profile.md exists in the agent directory."""
    profile = agent_dir / "profile.md"
    if profile.exists():
        return str(profile.relative_to(ROOT))
    return None


def parse_frontmatter(file_path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    if not content.startswith("---"):
        return {}

    end = content.find("---", 3)
    if end == -1:
        return {}

    frontmatter = content[3:end].strip()
    try:
        parsed = yaml.safe_load(frontmatter)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def is_agent_directory(d: Path) -> bool:
    """Determine if a directory contains an agent (has entry files)."""
    if d.name in SKIP_DIRS:
        return False
    if d.name.startswith("."):
        return False
    # Must have at least one .md or .yaml file
    has_content = any(d.glob("*.md")) or any(d.glob("*.yaml"))
    return has_content


def scan_agents() -> list[dict]:
    """Walk agents/ and build registry entries."""
    entries = []

    # Walk the agents directory looking for agent directories
    # An "agent directory" is a leaf directory containing agent files
    for category_root in sorted(AGENTS_DIR.iterdir()):
        if not category_root.is_dir():
            continue
        if category_root.name in SKIP_DIRS:
            continue
        if category_root.name in SKIP_ROOT_DIRS:
            continue
        if category_root.name.startswith("."):
            continue

        _scan_recursive(category_root, entries)

    return entries


def _scan_recursive(directory: Path, entries: list[dict], depth: int = 0):
    """Recursively scan for agent directories."""
    if directory.name in SKIP_DIRS or directory.name.startswith("."):
        return

    # Check if this directory IS an agent (has entry file)
    entry_file = find_entry_file(directory)

    if entry_file is not None:
        # This is an agent directory
        rel_path = directory.relative_to(AGENTS_DIR)
        agent_id = directory.name

        # Parse frontmatter for overrides
        fm = parse_frontmatter(entry_file) if entry_file.suffix == ".md" else {}

        # Build entry
        category = fm.get("category", infer_category(rel_path, agent_id))

        # For cargo agents, prefix id with department to avoid duplicates
        # e.g., cargo/sales/closer → "sales-closer", cargo/c-level/cfo → "c-level-cfo"
        derived_id = agent_id
        if category.startswith("external/cargo/") and not fm.get("id"):
            dept = category.split("/")[-1]
            derived_id = f"{dept}-{agent_id}"

        entry = {
            "id": fm.get("id", derived_id),
            "category": category,
            "path": str(entry_file.relative_to(ROOT)),
            "profile": find_profile(directory),
            "status": fm.get("status", "deprecated" if agent_id in DEPRECATED else "active"),
            "capabilities": fm.get("capabilities", []),
            "tags": fm.get("tags", []),
        }

        # Validate id is kebab-case
        if not KEBAB_CASE.match(entry["id"]):
            entry["id"] = re.sub(r"[^a-z0-9-]", "-", entry["id"].lower()).strip("-")

        entries.append(entry)

    # Also recurse into subdirectories (for nested structures like cargo/sales/closer/)
    for sub in sorted(directory.iterdir()):
        if sub.is_dir() and sub.name not in SKIP_DIRS and not sub.name.startswith("."):
            _scan_recursive(sub, entries, depth + 1)


def build_registry(agents: list[dict]) -> dict:
    """Build the full registry document."""
    # Sort by category, then by id
    agents.sort(key=lambda a: (a["category"], a["id"]))

    # Deduplicate by (category, id) — keep first occurrence
    seen = set()
    unique = []
    for a in agents:
        key = (a["category"], a["id"])
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return {
        "registry": {
            "version": "1.0.0",
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generator": "bin/refresh-registry.py",
            "schema_version": "1",
        },
        "agents": unique,
    }


def write_registry(registry: dict, output_path: Path):
    """Write registry YAML with category section comments."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Custom YAML output for readability
    lines = []
    lines.append("registry:")
    lines.append(f'  version: "{registry["registry"]["version"]}"')
    lines.append(f'  last_updated: "{registry["registry"]["last_updated"]}"')
    lines.append(f'  generator: "{registry["registry"]["generator"]}"')
    lines.append(f'  schema_version: "{registry["registry"]["schema_version"]}"')
    lines.append("")
    lines.append("agents:")

    current_category = None
    for agent in registry["agents"]:
        cat = agent["category"]
        if cat != current_category:
            current_category = cat
            lines.append(f"  # -- {cat} " + "-" * max(1, 60 - len(cat)))
            lines.append("")

        lines.append(f'  - id: {agent["id"]}')
        lines.append(f'    category: {agent["category"]}')
        lines.append(f'    path: {agent["path"]}')
        if agent["profile"] is None:
            lines.append("    profile: null")
        else:
            lines.append(f'    profile: {agent["profile"]}')
        lines.append(f'    status: {agent["status"]}')
        lines.append(f'    capabilities: {yaml.dump(agent["capabilities"], default_flow_style=True).strip()}')
        lines.append(f'    tags: {yaml.dump(agent["tags"], default_flow_style=True).strip()}')
        lines.append("")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(registry["agents"])


def main():
    parser = argparse.ArgumentParser(description="Regenerate ecosystem-registry.yaml from filesystem")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                       help=f"Output path (default: {DEFAULT_OUTPUT.relative_to(ROOT)})")
    args = parser.parse_args()

    agents = scan_agents()
    registry = build_registry(agents)
    count = write_registry(registry, args.output)

    try:
        display = args.output.relative_to(ROOT)
    except ValueError:
        display = args.output
    print(f"Registry regenerated: {count} agents -> {display}")


if __name__ == "__main__":
    main()
