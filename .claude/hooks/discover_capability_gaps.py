#!/usr/bin/env python3
"""
discover_capability_gaps.py -- Detect gaps in the Tool Intelligence Layer

Detects 3 types of gaps:
1. Agents in agents/ not mapped in ecosystem-registry.yaml
2. MCP servers in .mcp.json without a declared capability in capability-registry.yaml
3. Service adapters in services/ without a declared capability

Exit codes:
    0 -- gaps found (report printed)
    1 -- error
    2 -- no gaps found

Part of the Tool Intelligence Layer (MegaBrain Python-first architecture).
"""

import json
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML required.", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
AGENTS_DIR = PROJECT_ROOT / "agents"
SERVICES_DIR = PROJECT_ROOT / "services"
ECOSYSTEM_REGISTRY = AGENTS_DIR / "_registry" / "ecosystem-registry.yaml"
CAPABILITY_REGISTRY = AGENTS_DIR / "_registry" / "capability-registry.yaml"
MCP_JSON = PROJECT_ROOT / ".mcp.json"

AGENT_FILES = {"agent.md", "sow.md"}


def scan_agents_on_disk() -> set[str]:
    found = set()
    if not AGENTS_DIR.exists():
        return found
    for root, dirs, files in os.walk(AGENTS_DIR):
        dirs[:] = [d for d in dirs if not d.startswith(("_", "."))]
        for f in files:
            if f.lower() in AGENT_FILES:
                found.add(Path(root).name)
    return found


def load_yaml_safe(path: Path):
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def main():
    gaps = []
    total_checks = 0

    # --- GAP 1: Agents not in ecosystem-registry ---
    total_checks += 1
    eco = load_yaml_safe(ECOSYSTEM_REGISTRY)
    registered_ids = set()
    if eco and eco.get("agents"):
        registered_ids = {a.get("id", "") for a in eco["agents"] if isinstance(a, dict)}

    disk_agents = scan_agents_on_disk()
    unregistered = disk_agents - registered_ids
    if unregistered:
        gaps.append(
            {
                "type": "unregistered_agents",
                "description": "Agents on disk not in ecosystem-registry.yaml",
                "items": sorted(unregistered),
            }
        )

    # --- GAP 2: MCP servers without capability ---
    total_checks += 1
    cap_reg = load_yaml_safe(CAPABILITY_REGISTRY)
    capabilities = cap_reg.get("capabilities", {}) if cap_reg else {}

    # Collect all mcp_server_keys declared in capability-registry
    declared_mcp_keys = set()
    for cap in capabilities.values():
        for prov in cap.get("providers", []):
            if prov.get("type") == "mcp" and prov.get("mcp_server_key"):
                declared_mcp_keys.add(prov["mcp_server_key"])

    # Load .mcp.json
    mcp_keys = set()
    try:
        with open(MCP_JSON, encoding="utf-8") as f:
            mcp_data = json.load(f)
        mcp_keys = set((mcp_data.get("mcpServers") or mcp_data).keys())
    except Exception:
        pass

    unmapped_mcp = mcp_keys - declared_mcp_keys
    if unmapped_mcp:
        gaps.append(
            {
                "type": "unmapped_mcp_servers",
                "description": "MCP servers in .mcp.json without capability in capability-registry.yaml",
                "items": sorted(unmapped_mcp),
            }
        )

    # --- GAP 3: Service adapters without capability ---
    total_checks += 1
    if SERVICES_DIR.exists():
        # Collect all service_adapter paths from capability-registry
        declared_adapters = set()
        for cap in capabilities.values():
            sa = cap.get("service_adapter")
            if sa:
                # Normalize: "services/clickup/" -> "clickup"
                normalized = sa.strip("/").split("/")[-1] if "/" in sa else sa
                declared_adapters.add(normalized)

        # Scan services/ on disk
        service_dirs = set()
        for item in SERVICES_DIR.iterdir():
            if item.is_dir() and not item.name.startswith(("_", ".")):
                service_dirs.add(item.name)

        unmapped_services = service_dirs - declared_adapters
        # Filter out known non-capability services (infrastructure, internal)
        infra_services = {
            "env-loader.cjs",
            "enforcement",
            "event-bus",
            "file-service",
            "hybrid",
            "local-rag",
            "llm-router",
            "sync-engine",
            "the-hub",
            "symphony",
            "bridge",
            "etl",
        }
        unmapped_services -= infra_services

        if unmapped_services:
            gaps.append(
                {
                    "type": "unmapped_service_adapters",
                    "description": "Service directories without matching capability",
                    "items": sorted(unmapped_services),
                }
            )

    # --- Report ---
    print("")
    print("Capability Gap Discovery")
    print("=" * 25)
    print(f"Checks performed: {total_checks}")
    print(f"Gaps found:       {len(gaps)}")

    if not gaps:
        print("\nNo gaps detected.")
        print("")
        sys.exit(2)

    for gap in gaps:
        print(f"\n[{gap['type'].upper()}] {gap['description']}")
        for item in gap["items"]:
            print(f"  - {item}")

    print("")
    sys.exit(0)


if __name__ == "__main__":
    main()
