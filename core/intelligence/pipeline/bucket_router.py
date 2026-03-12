#!/usr/bin/env python3
"""
BUCKET ROUTER — Cross-Bucket Access Control
=============================================
Enforces which agents can read which knowledge buckets.
Used by the council system (conclave/debate) and RAG queries
to filter results based on the active mode.

Version: 1.0.0
Date: 2026-03-07
"""

import logging
import sys
from pathlib import Path

import yaml

from core.paths import (
    AGENTS,
    KNOWLEDGE_EXTERNAL,
    KNOWLEDGE_PERSONAL,
    WORKSPACE,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MODES
# ---------------------------------------------------------------------------

MODES = {
    "expert-only": {"buckets": ["external"], "description": "Expert knowledge only"},
    "business": {"buckets": ["external", "workspace"], "description": "Experts + company data"},
    "full-3d": {"buckets": ["external", "workspace", "personal"], "description": "All 3 dimensions"},
    "personal": {"buckets": ["personal"], "description": "Personal data only"},
    "company-only": {"buckets": ["workspace"], "description": "Company data only"},
}

BUCKET_PATHS = {
    "external": KNOWLEDGE_EXTERNAL,
    "workspace": WORKSPACE,
    "personal": KNOWLEDGE_PERSONAL,
}


# ---------------------------------------------------------------------------
# AGENT ACCESS
# ---------------------------------------------------------------------------

def load_agent_index() -> dict:
    """Load AGENT-INDEX.yaml and return parsed dict."""
    index_path = AGENTS / "AGENT-INDEX.yaml"
    try:
        with open(index_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError) as e:
        logger.warning("Failed to load AGENT-INDEX.yaml: %s", e)
        return {}


def get_agent_buckets(agent_id: str) -> list[str]:
    """Get the bucket access list for a specific agent.

    Args:
        agent_id: Agent identifier (e.g., 'closer', 'cfo', 'alex-hormozi').

    Returns:
        List of bucket names the agent can access.
        Empty list if agent not found.
    """
    index = load_agent_index()

    # Search minds
    for agent in index.get("minds", []):
        if agent.get("id") == agent_id:
            return agent.get("bucket", ["external"])

    # Search conclave
    for agent in index.get("conclave", []):
        if agent.get("id") == agent_id:
            return agent.get("bucket", ["external", "workspace", "personal"])

    # Search cargo (nested by area)
    for _area, agents in index.get("cargo", {}).items():
        if isinstance(agents, list):
            for agent in agents:
                if agent.get("id") == agent_id:
                    return agent.get("bucket", ["external", "workspace"])

    logger.warning("Agent '%s' not found in AGENT-INDEX.yaml", agent_id)
    return []


# ---------------------------------------------------------------------------
# ACCESS CONTROL
# ---------------------------------------------------------------------------

def get_allowed_paths(mode: str) -> list[Path]:
    """Get filesystem paths allowed for a given mode.

    Args:
        mode: One of 'expert-only', 'business', 'full-3d', 'personal', 'company-only'.

    Returns:
        List of Path objects the mode can access.
    """
    if mode not in MODES:
        logger.warning("Unknown mode '%s', defaulting to expert-only", mode)
        mode = "expert-only"

    return [BUCKET_PATHS[b] for b in MODES[mode]["buckets"]]


def can_agent_access_bucket(agent_id: str, bucket: str) -> bool:
    """Check if an agent can access a specific bucket.

    Args:
        agent_id: Agent identifier.
        bucket: Bucket name ('external', 'workspace', 'personal').

    Returns:
        True if access is allowed.
    """
    allowed = get_agent_buckets(agent_id)
    return bucket in allowed


def filter_paths_for_agent(agent_id: str, paths: list[Path]) -> list[Path]:
    """Filter a list of paths to only those the agent can access.

    Args:
        agent_id: Agent identifier.
        paths: List of file paths to filter.

    Returns:
        Filtered list containing only accessible paths.
    """
    allowed_buckets = get_agent_buckets(agent_id)
    allowed_roots = [BUCKET_PATHS[b] for b in allowed_buckets if b in BUCKET_PATHS]

    filtered = []
    for p in paths:
        resolved = p.resolve() if not p.is_absolute() else p
        for root in allowed_roots:
            try:
                resolved.relative_to(root)
                filtered.append(p)
                break
            except ValueError:
                continue

    return filtered


def get_missing_buckets(mode: str) -> list[str]:
    """Get buckets NOT included in a mode (for partial context signals).

    Args:
        mode: Active mode name.

    Returns:
        List of bucket names not accessible in this mode.
    """
    if mode not in MODES:
        return []
    all_buckets = {"external", "workspace", "personal"}
    active = set(MODES[mode]["buckets"])
    return sorted(all_buckets - active)


def format_missing_context_warning(mode: str) -> str:
    """Generate a warning string about missing bucket context.

    Args:
        mode: Active mode name.

    Returns:
        Warning string, or empty string if all buckets are active.
    """
    missing = get_missing_buckets(mode)
    if not missing:
        return ""

    warnings = []
    bucket_labels = {
        "external": "expert knowledge (frameworks, methodologies, mind clones)",
        "workspace": "company data (financials, team structure, meetings)",
        "personal": "personal context (emails, calls, reflections)",
    }
    for b in missing:
        warnings.append(f"- Without {b}: {bucket_labels.get(b, b)}")

    return "This response does not consider:\n" + "\n".join(warnings)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("\n=== Bucket Router — Access Control ===\n")
        print("Modes:")
        for name, info in MODES.items():
            buckets = ", ".join(info["buckets"])
            print(f"  {name:15s} → [{buckets}]")
        print("\nUsage:")
        print("  python bucket_router.py check <agent_id> <bucket>")
        print("  python bucket_router.py mode <mode_name>")
        print("  python bucket_router.py agent <agent_id>")
        return 0

    cmd = sys.argv[1]

    if cmd == "check" and len(sys.argv) >= 4:
        agent_id = sys.argv[2]
        bucket = sys.argv[3]
        allowed = can_agent_access_bucket(agent_id, bucket)
        print(f"{'ALLOWED' if allowed else 'DENIED'}: {agent_id} → {bucket}")
        return 0 if allowed else 1

    elif cmd == "mode" and len(sys.argv) >= 3:
        mode = sys.argv[2]
        paths = get_allowed_paths(mode)
        print(f"\nMode: {mode}")
        print(f"Paths: {[str(p) for p in paths]}")
        warning = format_missing_context_warning(mode)
        if warning:
            print(f"\n{warning}")
        return 0

    elif cmd == "agent" and len(sys.argv) >= 3:
        agent_id = sys.argv[2]
        buckets = get_agent_buckets(agent_id)
        print(f"\nAgent: {agent_id}")
        print(f"Buckets: {buckets}")
        return 0

    print("Unknown command. Run without arguments for help.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
