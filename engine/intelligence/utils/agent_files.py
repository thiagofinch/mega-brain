"""Centralized helper for resolving agent files across naming conventions.

MCE-12.1 standardized external/business/personal agents to lowercase
(agent.md, soul.md, memory.md, dna-config.yaml). Cargo agents in
agents/external/cargo/ remain UPPERCASE for backward compat.

This helper tries lowercase first, UPPERCASE fallback.

Story: MCE-13.5
"""
from __future__ import annotations

from pathlib import Path

# Canonical agent file basenames (lowercase) and legacy UPPERCASE variants
AGENT_FILES_CANONICAL = ("agent.md", "soul.md", "memory.md", "dna-config.yaml")
AGENT_FILES_LEGACY = ("AGENT.md", "SOUL.md", "MEMORY.md", "DNA-CONFIG.yaml")

# Map lowercase basename -> UPPERCASE legacy basename
_LOWER_TO_UPPER: dict[str, str] = {
    "agent.md": "AGENT.md",
    "soul.md": "SOUL.md",
    "memory.md": "MEMORY.md",
    "dna-config.yaml": "DNA-CONFIG.yaml",
}


def find_agent_file(agent_dir: Path, name: str) -> Path | None:
    """Find an agent file by name, trying lowercase first, UPPERCASE fallback.

    Args:
        agent_dir: directory containing the agent files
        name: basename without case sensitivity (e.g. "agent.md" or "AGENT.md")

    Returns:
        Path to the file if found (lowercase preferred), else None.
    """
    if not agent_dir.is_dir():
        return None

    lower = agent_dir / name.lower()
    if lower.exists():
        return lower

    # Try UPPERCASE variants for known files
    upper_name = _LOWER_TO_UPPER.get(name.lower())
    if upper_name:
        upper = agent_dir / upper_name
        if upper.exists():
            return upper

    return None


def agent_has_files(
    agent_dir: Path, required: tuple[str, ...] = AGENT_FILES_CANONICAL
) -> bool:
    """Check if agent_dir contains all required files (case-insensitive)."""
    return all(find_agent_file(agent_dir, name) is not None for name in required)


def find_all_agent_dirs(root: Path, marker: str = "agent.md") -> list[Path]:
    """Find all agent directories under root that contain a marker file.

    Tries lowercase marker first, UPPERCASE fallback. Returns sorted list of dirs.
    """
    if not root.is_dir():
        return []
    dirs: set[Path] = set()
    for candidate in root.rglob("*"):
        if not candidate.is_dir():
            continue
        if find_agent_file(candidate, marker) is not None:
            dirs.add(candidate)
    return sorted(dirs)
