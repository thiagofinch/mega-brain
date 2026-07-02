"""
memory_hierarchy.py -- Two-Level Memory Hierarchy for MCE Pipeline
==================================================================

Implements a two-level memory system:

1. **MEMORY-INDEX.md** -- Compact index file (capped at 200 lines) per agent.
   Contains only frontmatter headers (name, type, description, path) for
   each memory topic. This is the ONLY file scanned during header discovery.

2. **Topic files** -- Full content files in a ``topics/`` subdirectory.
   Loaded ON-DEMAND only when the memory selector confirms relevance.

Architecture
------------
::

    MEMORY-INDEX.md (200-line cap)       topics/
    ┌────────────────────────────┐      ┌─────────────────────┐
    │ --- (frontmatter header 1) │      │ marketing-funnels.md │  <-- loaded on-demand
    │ --- (frontmatter header 2) │      │ pricing-strategy.md  │  <-- loaded on-demand
    │ --- (frontmatter header 3) │      │ tech-stack-notes.md  │  <-- loaded on-demand
    │ ...                        │      └─────────────────────┘
    └────────────────────────────┘

    scan_index() reads ONLY the index → List[MemoryHeader]
    load_topic() reads a SINGLE topic file when selector says "relevant"

Public API
----------
- ``MemoryHeader`` -- dataclass with name, type, description, path, mtime
- ``scan_index(path) -> list[MemoryHeader]`` -- parse index without reading topics
- ``load_topic(path) -> str`` -- load a single topic file on-demand
- ``check_index_health(path) -> IndexHealth`` -- cap enforcement + warning

Constraints
~~~~~~~~~~~
- stdlib only (no external deps).
- Never reads topic content during scan (on-demand only).
- Deterministic -- same input produces same output.
- 200-line cap enforced with warning, not error.

Version: 1.0.0
Date: 2026-04-02
Story: MCE22-2.3
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("mce.memory_hierarchy")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INDEX_FILENAME = "MEMORY-INDEX.md"
TOPICS_DIRNAME = "topics"
INDEX_LINE_CAP = 200

# Frontmatter delimiters (YAML frontmatter blocks in the index)
_FRONTMATTER_DELIMITER = "---"


# ---------------------------------------------------------------------------
# Data Contracts
# ---------------------------------------------------------------------------


@dataclass
class MemoryHeader:
    """Metadata for a single memory entry, parsed from MEMORY-INDEX.md.

    This is a LIGHTWEIGHT reference -- it contains NO content, only metadata.
    Content lives in the topic file at ``path`` and is loaded on-demand.

    Attributes:
        name: Memory topic identifier (e.g. "marketing-funnels").
        type: Category of memory (e.g. "knowledge", "decision", "insight").
        description: Brief description of what this memory contains.
        path: Relative path to the topic file (from the index directory).
        mtime: Last modification timestamp (epoch float) of the topic file.
               0.0 if the file does not exist or cannot be stat'd.
    """

    name: str
    type: str = "knowledge"
    description: str = ""
    path: str = ""
    mtime: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dict."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "path": self.path,
            "mtime": self.mtime,
        }


@dataclass
class IndexHealth:
    """Health report for a MEMORY-INDEX.md file.

    Attributes:
        line_count: Total lines in the index file.
        entry_count: Number of memory entries parsed.
        exceeds_cap: True if line_count > INDEX_LINE_CAP.
        cap: The configured line cap (200).
        warning: Human-readable warning message, or empty string.
    """

    line_count: int = 0
    entry_count: int = 0
    exceeds_cap: bool = False
    cap: int = INDEX_LINE_CAP
    warning: str = ""


# ---------------------------------------------------------------------------
# Index Parsing
# ---------------------------------------------------------------------------


def _parse_frontmatter_block(lines: list[str]) -> dict[str, str]:
    """Parse a single YAML frontmatter block into a dict.

    Handles simple ``key: value`` pairs only (no nested YAML).
    This is intentionally simple -- memory index entries are flat.

    Args:
        lines: Lines BETWEEN the ``---`` delimiters (not including them).

    Returns:
        Dict of key-value pairs.
    """
    result: dict[str, str] = {}
    for line in lines:
        # Match "key: value" or "key:value" patterns
        match = re.match(r"^\s*(\w[\w_-]*)\s*:\s*(.*)$", line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            # Strip surrounding quotes if present
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            result[key] = value
    return result


def _extract_frontmatter_blocks(content: str) -> list[dict[str, str]]:
    """Extract all frontmatter blocks from a MEMORY-INDEX.md file.

    A frontmatter block is delimited by ``---`` on its own line.
    Multiple blocks are supported (one per memory entry).

    Args:
        content: Full text content of the index file.

    Returns:
        List of parsed frontmatter dicts.
    """
    blocks: list[dict[str, str]] = []
    lines = content.split("\n")
    in_block = False
    current_block: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped == _FRONTMATTER_DELIMITER:
            if in_block:
                # End of block
                if current_block:
                    parsed = _parse_frontmatter_block(current_block)
                    if parsed:
                        blocks.append(parsed)
                current_block = []
                in_block = False
            else:
                # Start of block
                in_block = True
                current_block = []
        elif in_block:
            current_block.append(line)

    return blocks


def _resolve_mtime(index_dir: Path, relative_path: str) -> float:
    """Resolve the mtime of a topic file.

    Args:
        index_dir: Directory containing the MEMORY-INDEX.md file.
        relative_path: Relative path from the index to the topic file.

    Returns:
        Modification time as epoch float, or 0.0 if file not found.
    """
    if not relative_path:
        return 0.0

    topic_path = index_dir / relative_path
    try:
        return topic_path.stat().st_mtime
    except (OSError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scan_index(path: str | Path) -> list[MemoryHeader]:
    """Scan a MEMORY-INDEX.md file and return headers WITHOUT loading topics.

    This is the core function for the fast-scan phase. It reads ONLY the
    index file, parses frontmatter blocks, resolves mtimes from the
    filesystem, and returns lightweight MemoryHeader objects.

    Topic file content is NEVER read by this function.

    Args:
        path: Path to the MEMORY-INDEX.md file, OR the directory containing it.

    Returns:
        List of MemoryHeader objects, sorted by mtime (newest first).
        Returns empty list if file not found or unparseable.
    """
    index_path = Path(path)

    # Accept either the file directly or the directory containing it
    if index_path.is_dir():
        index_path = index_path / INDEX_FILENAME

    if not index_path.is_file():
        logger.warning("Memory index not found: %s", index_path)
        return []

    try:
        content = index_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("Failed to read memory index %s: %s", index_path, exc)
        return []

    index_dir = index_path.parent
    blocks = _extract_frontmatter_blocks(content)
    headers: list[MemoryHeader] = []

    for block in blocks:
        name = block.get("name", "")
        if not name:
            continue

        relative_path = block.get("path", "")
        mtime = _resolve_mtime(index_dir, relative_path)

        header = MemoryHeader(
            name=name,
            type=block.get("type", "knowledge"),
            description=block.get("description", ""),
            path=relative_path,
            mtime=mtime,
        )
        headers.append(header)

    # Sort newest first (descending mtime)
    headers.sort(key=lambda h: h.mtime, reverse=True)

    logger.info(
        "Scanned memory index %s: %d entries",
        index_path,
        len(headers),
    )
    return headers


def load_topic(base_dir: str | Path, relative_path: str) -> str:
    """Load the full content of a single topic file on-demand.

    This is called ONLY after the memory selector confirms relevance.
    It reads the complete file content for injection into the pipeline.

    Args:
        base_dir: Base directory (where MEMORY-INDEX.md lives).
        relative_path: Relative path to the topic file (from the index).

    Returns:
        File content as string, or empty string if not found.

    Raises:
        FileNotFoundError: If the topic file does not exist.
    """
    topic_path = Path(base_dir) / relative_path

    if not topic_path.is_file():
        raise FileNotFoundError(
            f"Topic file not found: {topic_path} "
            f"(base_dir={base_dir}, relative_path={relative_path})"
        )

    content = topic_path.read_text(encoding="utf-8")
    logger.debug(
        "Loaded topic file: %s (%d chars)",
        relative_path,
        len(content),
    )
    return content


def check_index_health(path: str | Path) -> IndexHealth:
    """Check the health of a MEMORY-INDEX.md file.

    Verifies:
    - Line count vs the 200-line cap
    - Number of valid entries parsed
    - Emits warning if cap exceeded

    Args:
        path: Path to the MEMORY-INDEX.md file or directory containing it.

    Returns:
        IndexHealth report.
    """
    index_path = Path(path)

    if index_path.is_dir():
        index_path = index_path / INDEX_FILENAME

    if not index_path.is_file():
        return IndexHealth(
            warning=f"Index file not found: {index_path}",
        )

    try:
        content = index_path.read_text(encoding="utf-8")
    except OSError as exc:
        return IndexHealth(
            warning=f"Cannot read index: {exc}",
        )

    line_count = len(content.split("\n"))
    blocks = _extract_frontmatter_blocks(content)
    exceeds = line_count > INDEX_LINE_CAP

    warning = ""
    if exceeds:
        warning = (
            f"MEMORY-INDEX.md exceeds {INDEX_LINE_CAP}-line cap "
            f"({line_count} lines, {len(blocks)} entries). "
            f"Compaction recommended to stay within budget."
        )
        logger.warning(warning)

    return IndexHealth(
        line_count=line_count,
        entry_count=len(blocks),
        exceeds_cap=exceeds,
        cap=INDEX_LINE_CAP,
        warning=warning,
    )
