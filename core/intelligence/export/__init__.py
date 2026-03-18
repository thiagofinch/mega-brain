"""
Export -- Strategy Pattern for knowledge export formats.
=========================================================

This module provides a pluggable architecture for exporting
Mega Brain knowledge artifacts (playbooks, DNAs, dossiers)
to various formats.

Pattern: Strategy (inspired by Skill Seekers SkillAdaptor)

Available exporters:
- MarkdownExporter: Clean markdown output (default)
- Future: NotionExporter, ConfluenceExporter, etc.
"""

from __future__ import annotations

from .base import KnowledgeExporter
from .markdown_exporter import MarkdownExporter

__all__ = ["KnowledgeExporter", "MarkdownExporter"]

# Registry of available exporters
EXPORTERS: dict[str, type[KnowledgeExporter]] = {
    "markdown": MarkdownExporter,
}


def get_exporter(platform: str) -> KnowledgeExporter:
    """Get exporter instance by platform name.

    Args:
        platform: Platform identifier (e.g., "markdown", "notion")

    Returns:
        Configured exporter instance

    Raises:
        KeyError: If platform not registered
    """
    if platform not in EXPORTERS:
        available = ", ".join(EXPORTERS.keys())
        raise KeyError(f"Unknown platform '{platform}'. Available: {available}")

    return EXPORTERS[platform]()
