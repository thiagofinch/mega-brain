#!/usr/bin/env python3
"""
sync_agent_registry.py -- Sync agents on disk with ecosystem-registry.yaml

Scans agents/**/*.md and reconciles with agents/_registry/ecosystem-registry.yaml.

Modes:
    (default)   -- adds stub entries for unregistered agents
    --check     -- read-only, exit 1 if drift detected

Part of the Tool Intelligence Layer (MegaBrain Python-first architecture).
"""

import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip3 install pyyaml", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
AGENTS_DIR = PROJECT_ROOT / "agents"
REGISTRY_PATH = AGENTS_DIR / "_registry" / "ecosystem-registry.yaml"

# Files that count as agent definitions
AGENT_FILES = {"agent.md", "sow.md"}


def scan_agents_on_disk() -> dict[str, Path]:
    """Walk agents/ and find all agent directories with agent.md or sow.md."""
    found = {}
    if not AGENTS_DIR.exists():
        return found

    for root, dirs, files in os.walk(AGENTS_DIR):
        # Skip _registry, _templates, hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith(("_", "."))]

        root_path = Path(root)
        for f in files:
            if f.lower() in AGENT_FILES:
                rel = root_path.relative_to(PROJECT_ROOT)
                # Derive ID from directory name
                agent_id = root_path.name
                agent_path = str(rel / f)
                found[agent_id] = agent_path
    return found


def load_registry() -> tuple[dict, str]:
    """Load ecosystem-registry.yaml. Returns (parsed, raw_text)."""
    raw = REGISTRY_PATH.read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw)
    return parsed, raw


def get_registered_ids(registry: dict) -> set[str]:
    """Extract all agent IDs from registry."""
    agents = registry.get("agents", [])
    if not agents:
        return set()
    return {a.get("id", "") for a in agents if isinstance(a, dict)}


def derive_category(agent_path: str) -> str:
    """Derive category from path, e.g. agents/business/advisors/foo/agent.md -> business/advisors."""
    parts = agent_path.split("/")
    # agents / category... / agent-name / agent.md
    if len(parts) >= 4:
        return "/".join(parts[1:-2])
    return "unknown"


def derive_bucket(category: str) -> str:
    """Derive bucket from category."""
    if category.startswith("business"):
        return "business"
    if category.startswith("external/cargo"):
        return "cargo"
    if category.startswith("external"):
        return "external"
    if category.startswith("personal"):
        return "personal"
    if category.startswith("system"):
        return "system"
    return "unknown"


def main():
    args = sys.argv[1:]
    check_mode = "--check" in args

    if not REGISTRY_PATH.exists():
        print(f"Error: Registry not found: {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)

    on_disk = scan_agents_on_disk()
    registry, raw = load_registry()
    registered_ids = get_registered_ids(registry)

    # Find agents on disk not in registry
    missing = {aid: path for aid, path in on_disk.items() if aid not in registered_ids}

    # Find agents in registry not on disk
    orphaned = registered_ids - set(on_disk.keys())

    print("")
    print("Agent Registry Sync")
    print("=" * 20)
    print(f"Agents on disk:       {len(on_disk)}")
    print(f"Agents in registry:   {len(registered_ids)}")
    print(f"Missing from registry: {len(missing)}")
    print(f"Orphaned in registry:  {len(orphaned)}")

    if missing:
        print("\nMissing agents:")
        for aid, path in sorted(missing.items()):
            print(f"  + {aid} ({path})")

    if orphaned:
        print("\nOrphaned agents (in registry but not on disk):")
        for aid in sorted(orphaned):
            print(f"  - {aid}")

    print("")

    if check_mode:
        if missing or orphaned:
            print("DRIFT DETECTED.")
            sys.exit(1)
        print("OK: Registry matches disk.")
        sys.exit(0)

    # Default mode -- add missing stubs
    if not missing:
        print("No changes needed.")
        sys.exit(0)

    agents_list = registry.get("agents", [])
    for aid, path in sorted(missing.items()):
        category = derive_category(path)
        bucket = derive_bucket(category)
        agents_list.append(
            {
                "id": aid,
                "category": category,
                "bucket": bucket,
                "path": path,
                "profile": None,
                "status": "active",
                "capabilities": [],
                "tags": [],
            }
        )

    registry["agents"] = agents_list

    # Write back
    try:
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            yaml.dump(registry, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"Registry updated: {REGISTRY_PATH}")
        print(f"Added {len(missing)} agent(s).")
    except Exception as e:
        print(f"Error writing registry: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
