#!/usr/bin/env python3
"""
Agent Index Updater Hook
Auto-updates AGENT-INDEX.yaml when agents are created/modified.

Discovery logic aligned with activation_generator._discover_all_agents()
to ensure both produce the same agent count.

Hook Events: PostToolUse (Write/Edit to agents/)
Version: 2.0.0
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = ROOT / "agents"
AGENT_INDEX = AGENTS_DIR / "AGENT-INDEX.yaml"
UPDATE_LOG = ROOT / "logs" / "agent-index-updates.jsonl"

# Safety guard: if discovered count drops below this fraction of current
# count, abort the update to prevent accidental agent loss.
SAFETY_THRESHOLD = 0.80

# Layer paths
LAYER_PATHS = {
    "L0": "core/jarvis/",
    "L1": "agents/system/",
    "L2": "agents/business/",
    "L3": "agents/external/",
    "L4": "agents/cargo/",
    "L5": "agents/personal/",
    "SUB": ".claude/jarvis/sub-agents/",
}


def parse_stdin():
    """Parse JSON from stdin."""
    try:
        return json.load(sys.stdin)
    except Exception as e:  # noqa: F841
        return {}


def is_agent_file(file_path: str) -> bool:
    """Check if file is an agent definition."""
    path = Path(file_path)
    return (
        "agents/" in file_path
        and path.name in ["AGENT.md", "SOUL.md", "MEMORY.md"]
        and "_templates" not in file_path
    )


def detect_layer(file_path: str) -> str:
    """Detect which layer the agent belongs to."""
    if "agents/system/" in file_path:
        return "L1"
    elif "agents/business/" in file_path:
        return "L2"
    elif "agents/external/" in file_path:
        return "L3"
    elif "agents/cargo/" in file_path:
        return "L4"
    elif "agents/personal/" in file_path:
        return "L5"
    elif "sub-agents/" in file_path:
        return "SUB"
    elif "jarvis/" in file_path:
        return "L0"
    return "UNKNOWN"


def extract_agent_id(file_path: str) -> str:
    """Extract agent ID from path."""
    path = Path(file_path)
    # Go up from AGENT.md to get the agent folder name
    return path.parent.name


def scan_agents() -> dict:
    """Scan all agents and build index.

    Discovery logic mirrors activation_generator._discover_all_agents() exactly:
    - external/: direct children with AGENT.md
    - cargo/: nested 2 levels (cargo/{group}/{agent})
    - business/: rglob to handle 3+ levels of nesting
    - personal/: direct children with AGENT.md
    - system/: nested 2 levels (system/{sub}/AGENT.md or system/{sub}/{agent}/AGENT.md)
    """
    agents = {
        "external": [],
        "cargo": {},
        "business": [],
        "personal": [],
        "system": [],
    }

    # --- External experts (direct children) ---
    external_dir = AGENTS_DIR / "external"
    if external_dir.exists():
        for agent_dir in sorted(external_dir.iterdir()):
            if agent_dir.is_dir() and not agent_dir.name.startswith("_"):
                if (agent_dir / "AGENT.md").exists():
                    agents["external"].append(
                        {
                            "id": agent_dir.name,
                            "path": str(agent_dir.relative_to(ROOT)),
                            "has_soul": (agent_dir / "SOUL.md").exists(),
                            "has_memory": (agent_dir / "MEMORY.md").exists(),
                        }
                    )

    # --- Cargo roles (nested 2 levels: cargo/{group}/{agent}) ---
    cargo_dir = AGENTS_DIR / "cargo"
    if cargo_dir.exists():
        for group_dir in sorted(cargo_dir.iterdir()):
            if group_dir.is_dir():
                group_name = group_dir.name
                if group_name not in agents["cargo"]:
                    agents["cargo"][group_name] = []
                for agent_dir in sorted(group_dir.iterdir()):
                    if agent_dir.is_dir() and (agent_dir / "AGENT.md").exists():
                        agents["cargo"][group_name].append(
                            {"id": agent_dir.name, "path": str(agent_dir.relative_to(ROOT))}
                        )

    # --- Business people (rglob for 3+ level nesting) ---
    business_dir = AGENTS_DIR / "business"
    if business_dir.exists():
        for agent_md in sorted(business_dir.rglob("AGENT.md")):
            agent_dir = agent_md.parent
            if not agent_dir.name.startswith(("_", ".")):
                agents["business"].append(
                    {
                        "id": agent_dir.name,
                        "path": str(agent_dir.relative_to(ROOT)),
                        "has_soul": (agent_dir / "SOUL.md").exists(),
                        "has_memory": (agent_dir / "MEMORY.md").exists(),
                    }
                )

    # --- Personal agents (direct children) ---
    personal_dir = AGENTS_DIR / "personal"
    if personal_dir.exists():
        for agent_dir in sorted(personal_dir.iterdir()):
            if agent_dir.is_dir() and not agent_dir.name.startswith("_"):
                if (agent_dir / "AGENT.md").exists():
                    agents["personal"].append(
                        {
                            "id": agent_dir.name,
                            "path": str(agent_dir.relative_to(ROOT)),
                            "has_soul": (agent_dir / "SOUL.md").exists(),
                            "has_memory": (agent_dir / "MEMORY.md").exists(),
                        }
                    )

    # --- System agents (nested 2 levels, same logic as activation_generator) ---
    system_dir = AGENTS_DIR / "system"
    if system_dir.exists():
        for sub in sorted(system_dir.iterdir()):
            if sub.is_dir():
                if (sub / "AGENT.md").exists():
                    # Direct system agent (e.g., system/jarvis/)
                    agents["system"].append(
                        {
                            "id": sub.name,
                            "path": str(sub.relative_to(ROOT)),
                            "group": None,
                        }
                    )
                else:
                    # Nested system agents (e.g., system/conclave/{agent}, system/dev-ops/{agent})
                    for agent_dir in sorted(sub.iterdir()):
                        if agent_dir.is_dir() and (agent_dir / "AGENT.md").exists():
                            agents["system"].append(
                                {
                                    "id": agent_dir.name,
                                    "path": str(agent_dir.relative_to(ROOT)),
                                    "group": sub.name,
                                }
                            )

    return agents


def _count_current_agents() -> int:
    """Count agents in existing AGENT-INDEX.yaml by parsing the total line."""
    if not AGENT_INDEX.exists():
        return 0
    try:
        for line in AGENT_INDEX.read_text().splitlines():
            if line.strip().startswith("total:"):
                return int(line.split(":")[1].strip())
    except (ValueError, IndexError):
        pass
    return 0


def update_index():
    """Update AGENT-INDEX.yaml with current agents.

    Returns the total agent count, or -1 if safety guard blocked the update.
    """
    agents = scan_agents()

    # Count totals per category
    total_external = len(agents["external"])
    total_cargo = sum(len(v) for v in agents["cargo"].values())
    total_business = len(agents["business"])
    total_personal = len(agents["personal"])
    total_system = len(agents["system"])
    total = total_external + total_cargo + total_business + total_personal + total_system

    # --- Safety guard: block if agent count drops > 20% ---
    current_count = _count_current_agents()
    if current_count > 0 and total < int(current_count * SAFETY_THRESHOLD):
        msg = (
            f"SAFETY GUARD: discovered {total} agents but AGENT-INDEX.yaml has {current_count}. "
            f"Reduction exceeds {int((1 - SAFETY_THRESHOLD) * 100)}% threshold. "
            f"Aborting update to prevent agent loss."
        )
        print(json.dumps({"continue": True, "warning": msg}), file=sys.stderr)
        return -1

    # --- Group system agents by sub-group for output ---
    system_groups: dict[str, list] = {}
    system_direct: list = []
    for agent in agents["system"]:
        group = agent.get("group")
        if group:
            system_groups.setdefault(group, []).append(agent)
        else:
            system_direct.append(agent)

    # --- Generate YAML content ---
    content = f"""# AGENT-INDEX.yaml
# Auto-generated by agent_index_updater.py
# Last updated: {datetime.now().isoformat()}
# Total agents: {total}

version: "5.0.0"
updated: "{datetime.now().strftime("%Y-%m-%d")}"

totals:
  external: {total_external}
  cargo: {total_cargo}
  business: {total_business}
  personal: {total_personal}
  system: {total_system}
  total: {total}

# =============================================================================
# EXTERNAL - Expert Mind Clones
# =============================================================================
external:
"""
    for agent in agents["external"]:
        content += f"""  - id: {agent["id"]}
    path: {agent["path"]}/
    has_soul: {str(agent["has_soul"]).lower()}
    has_memory: {str(agent["has_memory"]).lower()}
    status: active
"""

    content += """
# =============================================================================
# CARGO - Functional Roles
# =============================================================================
cargo:
"""
    for group, group_agents in sorted(agents["cargo"].items()):
        if group_agents:
            content += f"  {group}:\n"
            for agent in group_agents:
                content += f"""    - id: {agent["id"]}
      path: {agent["path"]}/
      status: active
"""

    content += """
# =============================================================================
# BUSINESS - Collaborator Clones
# =============================================================================
business:
"""
    for agent in agents["business"]:
        content += f"""  - id: {agent["id"]}
    path: {agent["path"]}/
    has_soul: {str(agent["has_soul"]).lower()}
    has_memory: {str(agent["has_memory"]).lower()}
    status: active
"""

    content += """
# =============================================================================
# PERSONAL - Founder Clones
# =============================================================================
personal:
"""
    for agent in agents["personal"]:
        content += f"""  - id: {agent["id"]}
    path: {agent["path"]}/
    has_soul: {str(agent["has_soul"]).lower()}
    has_memory: {str(agent["has_memory"]).lower()}
    status: active
"""

    content += """
# =============================================================================
# SYSTEM - Infrastructure Agents
# =============================================================================
system:
"""
    for agent in system_direct:
        content += f"""  - id: {agent["id"]}
    path: {agent["path"]}/
    status: active
"""
    for group_name, group_agents in sorted(system_groups.items()):
        content += f"  {group_name}:\n"
        for agent in group_agents:
            content += f"""    - id: {agent["id"]}
      path: {agent["path"]}/
      status: active
"""

    # Write file
    AGENT_INDEX.write_text(content)
    return total


def log_update(file_path: str, agent_id: str, layer: str):
    """Log index update."""
    UPDATE_LOG.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "trigger_file": file_path,
        "agent_id": agent_id,
        "layer": layer,
        "action": "index_updated",
    }

    with open(UPDATE_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    """Main hook execution."""
    try:
        data = parse_stdin()

        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        if tool_name not in ["Write", "Edit"]:
            print(json.dumps({"continue": True}))
            return

        file_path = tool_input.get("file_path", "")

        # Check if this is an agent file
        if not is_agent_file(file_path):
            print(json.dumps({"continue": True}))
            return

        # Update the index
        agent_id = extract_agent_id(file_path)
        layer = detect_layer(file_path)
        total = update_index()

        if total == -1:
            # Safety guard blocked the update
            return

        log_update(file_path, agent_id, layer)

        print(
            json.dumps(
                {"continue": True, "message": f"AGENT-INDEX.yaml updated ({total} agents)"}
            )
        )

    except Exception as e:
        print(json.dumps({"continue": True, "warning": f"Agent index update error: {e!s}"}))
        sys.exit(0)


if __name__ == "__main__":
    main()
