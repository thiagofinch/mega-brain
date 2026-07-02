"""
agent_cascade.py -- L2 Autonomous Cascade Update for Existing Agents
=====================================================================
When Phase 5 identifies that an agent already exists, this module performs
the cascade update: enriching the existing agent with new DNA/insights
without requiring human approval (Art. VII L2 tier).

Story: PIP-007
Version: 1.0.0
Date: 2026-04-16
"""

from __future__ import annotations

import logging
from pathlib import Path

from engine.intelligence.utils.agent_files import find_agent_file  # MCE-13.5
from engine.paths import AGENTS_BUSINESS, AGENTS_EXTERNAL

logger = logging.getLogger(__name__)


def _find_agent_dir(slug: str) -> Path | None:
    """Locate the agent directory for a given slug."""
    candidates = [
        AGENTS_EXTERNAL / slug,
        AGENTS_BUSINESS / slug,
        AGENTS_BUSINESS / "collaborators" / slug,
    ]
    for path in candidates:
        # MCE-13.5: use find_agent_file to handle both lowercase and UPPERCASE
        if find_agent_file(path, "agent.md") is not None:
            return path
    return None


def cascade_update_existing(slug: str, source_files: list[str | Path] | None = None) -> bool:
    """Perform L2 autonomous cascade update on an existing agent.

    This updates the agent's MEMORY.md with new source references and
    triggers downstream DNA enrichment. The agent structure itself is
    preserved — only knowledge layers are updated.

    Args:
        slug: Agent slug (e.g. "alex-hormozi")
        source_files: New source files to cascade into the agent

    Returns:
        True if update was performed, False if agent not found.
    """
    agent_dir = _find_agent_dir(slug)
    if agent_dir is None:
        logger.warning("[L2] Cannot cascade: agent dir not found for slug=%s", slug)
        return False

    logger.info("[L2] Updating agent for %s at %s", slug, agent_dir)

    # MCE-13.5: use find_agent_file to resolve memory.md / MEMORY.md
    memory_path = find_agent_file(agent_dir, "memory.md")
    if memory_path is not None:
        _append_cascade_entry(memory_path, slug, source_files or [])
    else:
        logger.info("[L2] memory.md not found for %s, creating minimal entry", slug)
        # Create as lowercase per MCE-12.1
        _create_minimal_memory(agent_dir / "memory.md", slug, source_files or [])

    return True


def _append_cascade_entry(memory_path: Path, slug: str, source_files: list[str | Path]) -> None:
    """Append a cascade update entry to the agent's MEMORY.md."""
    from datetime import UTC, datetime

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    sources_str = ", ".join(str(f) for f in source_files[:5])
    if len(source_files) > 5:
        sources_str += f" (+{len(source_files) - 5} more)"

    entry = f"\n\n## Cascade Update — {now}\n\n- Sources: {sources_str}\n- Type: L2 autonomous (Art. VII)\n"

    with open(memory_path, "a", encoding="utf-8") as f:
        f.write(entry)

    logger.info("[L2] Appended cascade entry to %s", memory_path)


def _create_minimal_memory(memory_path: Path, slug: str, source_files: list[str | Path]) -> None:
    """Create a minimal MEMORY.md with the first cascade entry."""
    from datetime import UTC, datetime

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    sources_str = ", ".join(str(f) for f in source_files[:5])

    content = f"""# MEMORY — {slug}

> Accumulated experience and cascade updates.

## Cascade Update — {now}

- Sources: {sources_str}
- Type: L2 autonomous (Art. VII)
- Note: Initial MEMORY.md created by cascade system
"""

    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(content, encoding="utf-8")
    logger.info("[L2] Created MEMORY.md at %s", memory_path)
