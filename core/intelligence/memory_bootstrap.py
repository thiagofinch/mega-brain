#!/usr/bin/env python3
"""
memory_bootstrap.py -- Initialize Memory Directories for All Registered Agents
================================================================================
Reads AGENT-INDEX.yaml, creates .data/agent_memory/{agent_id}/ for every
registered agent, and seeds a genesis memory entry with creation date, role,
and capabilities.

Idempotent: running twice produces the same result. Existing entries are
never overwritten.

Usage:
    python3 -m core.intelligence.memory_bootstrap           # bootstrap all
    python3 -m core.intelligence.memory_bootstrap --dry-run  # preview only
    python3 -m core.intelligence.memory_bootstrap --agent closer  # single agent

Version: 1.0.0
Date: 2026-03-16
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent.parent
AGENT_INDEX_PATH = ROOT / "agents" / "AGENT-INDEX.yaml"
MEMORY_DIR = ROOT / ".data" / "agent_memory"

# ---------------------------------------------------------------------------
# ROLE DESCRIPTIONS (per category, used for genesis entries)
# ---------------------------------------------------------------------------
CATEGORY_ROLES: dict[str, str] = {
    "external": "Expert Mind Clone -- knowledge source for DNA, frameworks, and methodologies",
    "cargo": "Functional Role Agent -- operational execution in specialized domain",
    "business": "Collaborator Clone -- business partner knowledge and context",
    "personal": "Founder Clone -- personal cognitive patterns and decision history",
    "system": "System Infrastructure Agent -- pipeline processing and system operations",
}

# Sub-group specializations within system agents
SYSTEM_GROUP_ROLES: dict[str, str] = {
    "conclave": "Council Agent -- multi-perspective deliberation and debate",
    "dev-ops": "Dev Ops Agent -- development lifecycle automation",
    "knowledge-ops": "Knowledge Ops Agent -- MCE pipeline processing and knowledge extraction",
}

# Mapping from system sub-group to dispatch prefix.
# Squad routing uses prefixed names (kops-atlas, dops-anvil) while
# AGENT-INDEX.yaml uses bare names (atlas, anvil). We create directories
# for BOTH so the hook writes and bootstrap reads are aligned.
DISPATCH_PREFIX: dict[str, str] = {
    "knowledge-ops": "kops",
    "dev-ops": "dops",
}


def load_agent_index() -> dict:
    """Load and parse AGENT-INDEX.yaml."""
    if not AGENT_INDEX_PATH.exists():
        print(f"ERROR: AGENT-INDEX.yaml not found at {AGENT_INDEX_PATH}")
        sys.exit(1)

    with open(AGENT_INDEX_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_all_agents(index: dict) -> list[dict]:
    """Extract a flat list of all agents from the nested AGENT-INDEX structure.

    Returns list of dicts with keys: id, path, category, group, status
    """
    agents: list[dict] = []

    # External agents (flat list)
    for agent in index.get("external", []) or []:
        agents.append({
            "id": agent["id"],
            "path": agent.get("path", ""),
            "category": "external",
            "group": None,
            "status": agent.get("status", "active"),
        })

    # Cargo agents (nested by department)
    cargo = index.get("cargo", {}) or {}
    for dept_name, dept_agents in cargo.items():
        if not isinstance(dept_agents, list):
            continue
        for agent in dept_agents:
            agents.append({
                "id": agent["id"],
                "path": agent.get("path", ""),
                "category": "cargo",
                "group": dept_name,
                "status": agent.get("status", "active"),
            })

    # Business agents (flat list)
    for agent in index.get("business", []) or []:
        agents.append({
            "id": agent["id"],
            "path": agent.get("path", ""),
            "category": "business",
            "group": None,
            "status": agent.get("status", "active"),
        })

    # Personal agents (flat list)
    for agent in index.get("personal", []) or []:
        agents.append({
            "id": agent["id"],
            "path": agent.get("path", ""),
            "category": "personal",
            "group": None,
            "status": agent.get("status", "active"),
        })

    # System agents (nested by sub-group: conclave, dev-ops, knowledge-ops)
    # For kops-*/dops-* groups, also create prefixed alias entries so that
    # memory_capture.py (which writes to prefixed names) finds its dirs.
    system = index.get("system", {}) or {}
    for group_name, group_agents in system.items():
        if not isinstance(group_agents, list):
            continue
        prefix = DISPATCH_PREFIX.get(group_name)
        for agent in group_agents:
            # Canonical entry (bare name from AGENT-INDEX)
            agents.append({
                "id": agent["id"],
                "path": agent.get("path", ""),
                "category": "system",
                "group": group_name,
                "status": agent.get("status", "active"),
            })
            # Prefixed alias entry (dispatch name used by hooks)
            if prefix:
                agents.append({
                    "id": f"{prefix}-{agent['id']}",
                    "path": agent.get("path", ""),
                    "category": "system",
                    "group": group_name,
                    "status": agent.get("status", "active"),
                    "alias_of": agent["id"],
                })

    return agents


def build_genesis_entry(agent: dict) -> dict:
    """Build a genesis memory entry for an agent.

    Contains: creation date, role description, capabilities derived from category.
    """
    category = agent["category"]
    group = agent.get("group")

    # Determine role description
    if category == "system" and group in SYSTEM_GROUP_ROLES:
        role = SYSTEM_GROUP_ROLES[group]
    else:
        role = CATEGORY_ROLES.get(category, "Agent")

    # Build capabilities list based on category + group
    capabilities = _infer_capabilities(category, group, agent["id"])

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "agent": agent["id"],
        "task_summary": "Agent memory initialized via memory_bootstrap.py",
        "type": "genesis",
        "importance": 0.3,
        "role": role,
        "category": category,
        "group": group,
        "capabilities": capabilities,
        "path": agent.get("path", ""),
        "status": agent.get("status", "active"),
    }


def _infer_capabilities(category: str, group: str | None, agent_id: str) -> list[str]:
    """Infer capability tags from agent category and group."""
    caps: list[str] = []

    if category == "external":
        caps = ["expert-consultation", "dna-source", "methodology-reference", "conclave-participant"]
    elif category == "cargo":
        if group == "c-level":
            caps = ["strategic-planning", "executive-decision", "kpi-analysis"]
        elif group == "sales":
            caps = ["sales-methodology", "objection-handling", "pipeline-management"]
        elif group == "marketing":
            caps = ["campaign-strategy", "media-buying", "audience-targeting"]
        else:
            caps = ["domain-execution", "operational-advice"]
    elif category == "business":
        caps = ["collaborator-context", "meeting-insights", "relationship-history"]
    elif category == "personal":
        caps = ["founder-context", "decision-patterns", "cognitive-history"]
    elif category == "system":
        if group == "knowledge-ops":
            caps = ["mce-pipeline", "knowledge-extraction", "dna-processing", "dossier-compilation"]
        elif group == "dev-ops":
            caps = ["code-building", "testing", "deployment", "architecture-review"]
        elif group == "conclave":
            caps = ["deliberation", "critique", "synthesis", "multi-perspective-analysis"]
        else:
            caps = ["system-operations"]

    return caps


def bootstrap_agent(agent: dict, dry_run: bool = False) -> dict:
    """Bootstrap memory directory for a single agent.

    Returns status dict: {id, action, path}
    """
    agent_id = agent["id"]
    agent_dir = MEMORY_DIR / agent_id
    memory_file = agent_dir / "memories.jsonl"

    # Check if genesis already exists
    if memory_file.exists():
        content = memory_file.read_text(encoding="utf-8").strip()
        if content:
            # Check if genesis entry already present
            for line in content.split("\n"):
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "genesis":
                        return {"id": agent_id, "action": "skipped", "path": str(memory_file)}
                except (json.JSONDecodeError, TypeError):
                    continue

    if dry_run:
        return {"id": agent_id, "action": "would_create", "path": str(memory_file)}

    # Create directory
    agent_dir.mkdir(parents=True, exist_ok=True)

    # Build genesis entry
    genesis = build_genesis_entry(agent)

    # Append genesis (preserve any existing non-genesis entries)
    with open(memory_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(genesis, ensure_ascii=False) + "\n")

    return {"id": agent_id, "action": "created", "path": str(memory_file)}


def bootstrap_all(dry_run: bool = False, target_agent: str | None = None) -> dict:
    """Bootstrap memory for all agents in AGENT-INDEX.yaml.

    Args:
        dry_run: If True, preview actions without writing
        target_agent: If set, only bootstrap this specific agent ID

    Returns:
        Summary dict with counts and per-agent results
    """
    index = load_agent_index()
    agents = extract_all_agents(index)

    if target_agent:
        agents = [a for a in agents if a["id"] == target_agent]
        if not agents:
            return {"error": f"Agent '{target_agent}' not found in AGENT-INDEX.yaml"}

    results: list[dict] = []
    created = 0
    skipped = 0

    for agent in agents:
        result = bootstrap_agent(agent, dry_run=dry_run)
        results.append(result)
        if result["action"] == "created" or result["action"] == "would_create":
            created += 1
        else:
            skipped += 1

    return {
        "total_agents": len(agents),
        "created": created,
        "skipped": skipped,
        "dry_run": dry_run,
        "results": results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    dry_run = "--dry-run" in sys.argv
    target_agent = None

    for i, arg in enumerate(sys.argv):
        if arg == "--agent" and i + 1 < len(sys.argv):
            target_agent = sys.argv[i + 1]

    print("=" * 60)
    print("MEMORY BOOTSTRAP")
    if dry_run:
        print("  MODE: dry-run (preview only)")
    if target_agent:
        print(f"  TARGET: {target_agent}")
    print("=" * 60)
    print()

    summary = bootstrap_all(dry_run=dry_run, target_agent=target_agent)

    if "error" in summary:
        print(f"ERROR: {summary['error']}")
        sys.exit(1)

    # Print results table
    print(f"{'Agent ID':<30} {'Action':<15} {'Path'}")
    print("-" * 90)

    for r in summary["results"]:
        # Shorten path for display
        short_path = r["path"].replace(str(ROOT) + "/", "")
        print(f"{r['id']:<30} {r['action']:<15} {short_path}")

    print()
    print("-" * 60)
    print(f"Total agents:  {summary['total_agents']}")
    print(f"Created:       {summary['created']}")
    print(f"Skipped:       {summary['skipped']}")
    print(f"Dry run:       {summary['dry_run']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
