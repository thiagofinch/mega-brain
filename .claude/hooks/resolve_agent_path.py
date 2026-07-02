#!/usr/bin/env python3
"""
resolve_agent_path.py — Canonical Agent Path Resolver (Mega Brain)

Resolves the canonical MEMORY.md path for any agent slug by consulting
the ecosystem registry with a fallback chain.

RESOLUTION ORDER:
  1. agents/_registry/ecosystem-registry.yaml (canonical registry)
  2. Filesystem scan: agents/external/{slug}/MEMORY.md
  3. Filesystem scan: agents/external/cargo/*/{slug}/MEMORY.md
  4. Filesystem scan: agents/business/*/{slug}/MEMORY.md
  5. Filesystem scan: agents/system/{slug}/MEMORY.md
  6. Fallback: .data/agent_memory/{slug}/MEMORY.md (last resort, runtime dir)

USAGE:
  from resolve_agent_path import resolve_memory_path
  path = resolve_memory_path(project_root, "closer")
  # -> /path/to/agents/external/cargo/sales/closer/MEMORY.md

DEPENDENCIES: stdlib + PyYAML (optional, graceful degradation to fallback)
EXIT: This is a library module, not a hook. No exit codes.
"""

import os
from pathlib import Path

# Optional: PyYAML for registry parsing
try:
    import yaml

    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# Cache the registry in memory for the session (avoids re-parsing per call)
_registry_cache: dict | None = None
_registry_cache_mtime: float = 0.0


def _load_registry(project_root: Path) -> list[dict]:
    """Load ecosystem-registry.yaml and return the agents list."""
    global _registry_cache, _registry_cache_mtime

    registry_path = project_root / "agents" / "_registry" / "ecosystem-registry.yaml"
    if not registry_path.exists():
        return []

    # Use mtime-based cache to avoid re-parsing within the same session
    try:
        current_mtime = registry_path.stat().st_mtime
    except OSError:
        return _registry_cache or []

    if _registry_cache is not None and current_mtime == _registry_cache_mtime:
        return _registry_cache

    if not _HAS_YAML:
        return []

    try:
        with open(registry_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        agents = data.get("agents", []) if isinstance(data, dict) else []
        _registry_cache = agents
        _registry_cache_mtime = current_mtime
        return agents
    except Exception:
        return _registry_cache or []


def _resolve_from_registry(project_root: Path, agent_slug: str) -> Path | None:
    """Try to resolve MEMORY.md from the ecosystem registry."""
    agents = _load_registry(project_root)
    if not agents:
        return None

    for agent in agents:
        if not isinstance(agent, dict):
            continue
        if agent.get("id") == agent_slug:
            agent_file = agent.get("path", "")
            if agent_file:
                # path is like "agents/external/cargo/sales/closer/agent.md"
                # MEMORY.md lives in the same directory
                agent_dir = project_root / Path(agent_file).parent
                memory_path = agent_dir / "MEMORY.md"
                return memory_path
    return None


def _resolve_from_filesystem(project_root: Path, agent_slug: str) -> Path | None:
    """Scan common agent directories for MEMORY.md."""
    candidates = [
        # Direct external agent
        project_root / "agents" / "external" / agent_slug / "MEMORY.md",
    ]

    # Cargo agents (scan subdirs: c-level, sales, marketing, operations)
    cargo_base = project_root / "agents" / "external" / "cargo"
    if cargo_base.is_dir():
        try:
            for subdir in cargo_base.iterdir():
                if subdir.is_dir():
                    candidate = subdir / agent_slug / "MEMORY.md"
                    candidates.append(candidate)
        except OSError:
            pass

    # Business agents (scan subdirs: advisors, partners, etc.)
    business_base = project_root / "agents" / "business"
    if business_base.is_dir():
        try:
            for subdir in business_base.iterdir():
                if subdir.is_dir():
                    candidate = subdir / agent_slug / "MEMORY.md"
                    candidates.append(candidate)
        except OSError:
            pass

    # System agents
    candidates.append(project_root / "agents" / "system" / agent_slug / "MEMORY.md")

    # Personal agents
    candidates.append(project_root / "agents" / "personal" / agent_slug / "MEMORY.md")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def resolve_memory_path(project_root: Path | str, agent_slug: str) -> Path:
    """
    Resolve the canonical MEMORY.md path for an agent slug.

    Args:
        project_root: Path to the mega-brain project root
        agent_slug: Agent identifier (e.g., "closer", "cfo", "alex-hormozi")

    Returns:
        Path to MEMORY.md (may not exist yet — caller should check/create)
    """
    root = Path(project_root) if isinstance(project_root, str) else project_root

    if not agent_slug or not isinstance(agent_slug, str):
        return root / ".data" / "agent_memory" / "unknown" / "MEMORY.md"

    slug = agent_slug.strip().lower()

    # 1. Try ecosystem registry (canonical source)
    result = _resolve_from_registry(root, slug)
    if result is not None:
        return result

    # 2. Try filesystem scan (covers agents not in registry)
    result = _resolve_from_filesystem(root, slug)
    if result is not None:
        return result

    # 3. Last resort: runtime memory directory
    return root / ".data" / "agent_memory" / slug / "MEMORY.md"
