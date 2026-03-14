#!/usr/bin/env python3
"""
Agent Path Resolver v1.0 (Mega Brain)

Resolves agent slug -> canonical MEMORY.md path by reading AGENT-INDEX.yaml.

The mega-brain stores agent memory INSIDE agent directories (not in .claude/agent-memory/).
This resolver bridges the gap so hooks can find the real MEMORY.md location.

RESOLUTION ORDER:
  1. AGENT-INDEX.yaml lookup (canonical source of truth)
  2. Fallback: .claude/agent-memory/{slug}/MEMORY.md (for unindexed agents)

USAGE:
  from resolve_agent_path import resolve_memory_path
  path = resolve_memory_path(PROJECT_ROOT, "cfo")
  # -> /path/to/mega-brain/agents/cargo/c-level/cfo/MEMORY.md
"""

from pathlib import Path

# Cache to avoid re-parsing YAML on every call within same process
_index_cache = None
_index_mtime = 0


def _load_index(project_root: Path) -> dict:
    """Load and cache AGENT-INDEX.yaml."""
    global _index_cache, _index_mtime

    index_path = project_root / "agents" / "AGENT-INDEX.yaml"
    if not index_path.exists():
        return {}

    current_mtime = index_path.stat().st_mtime
    if _index_cache is not None and current_mtime == _index_mtime:
        return _index_cache

    try:
        import yaml

        with open(index_path, encoding="utf-8") as f:
            _index_cache = yaml.safe_load(f) or {}
            _index_mtime = current_mtime
            return _index_cache
    except ImportError:
        # PyYAML not available — try simple line-based parsing
        return _parse_index_simple(index_path)
    except Exception:
        return {}


def _parse_index_simple(index_path: Path) -> dict:
    """Fallback parser when PyYAML is not available. Extracts id->path mappings."""
    global _index_cache, _index_mtime

    result = {"_simple": []}
    try:
        content = index_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        current_id = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- id:"):
                current_id = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("path:") and current_id:
                path_val = stripped.split(":", 1)[1].strip()
                result["_simple"].append({"id": current_id, "path": path_val})
                current_id = None
        _index_cache = result
        _index_mtime = index_path.stat().st_mtime
    except Exception:
        pass
    return result


def _search_agents(index: dict, slug: str) -> str | None:
    """Search all layers in the index for matching agent slug. Returns path or None."""

    # Handle simple parser format
    if "_simple" in index:
        for entry in index["_simple"]:
            if entry.get("id") == slug:
                return entry.get("path")
        return None

    # Search flat lists: minds, conclave
    for layer in ["minds", "conclave"]:
        agents = index.get(layer)
        if isinstance(agents, list):
            for agent in agents:
                if isinstance(agent, dict) and agent.get("id") == slug:
                    return agent.get("path")

    # Search nested dict: cargo (sales, marketing, c-level, etc.)
    cargo = index.get("cargo")
    if isinstance(cargo, dict):
        for _area_key, area_agents in cargo.items():
            if isinstance(area_agents, list):
                for agent in area_agents:
                    if isinstance(agent, dict) and agent.get("id") == slug:
                        return agent.get("path")

    return None


def resolve_memory_path(project_root: Path, agent_slug: str) -> Path:
    """
    Resolve agent slug to canonical MEMORY.md path.

    Resolution order:
      1. AGENT-INDEX.yaml lookup -> agents/{layer}/{agent}/MEMORY.md
      2. Fallback -> .claude/agent-memory/{slug}/MEMORY.md

    Returns Path object (may or may not exist yet).
    """
    index = _load_index(project_root)
    agent_path = _search_agents(index, agent_slug)

    if agent_path:
        canonical = project_root / agent_path / "MEMORY.md"
        if canonical.parent.exists():
            return canonical

    # Fallback for unindexed agents (sub-agents, jarvis, etc.)
    return project_root / ".claude" / "agent-memory" / agent_slug / "MEMORY.md"
