"""
core/governance/ — Auto-generates architecture documentation from configs + filesystem.

This module reads:
- core/paths.py (ROUTING keys, directory structure)
- pyproject.toml (Python tooling: ruff, pyright, pytest)
- biome.json (JS formatting config)
- package.json (dependencies, scripts, version)
- Actual filesystem structure

And writes:
- docs/architecture/coding-standards.md
- docs/architecture/tech-stack.md
- docs/architecture/source-tree.md

Usage:
    from core.governance import engine
    engine.regenerate_all()
"""

from core.governance.engine import (
    generate_all,
    generate_coding_standards,
    generate_source_tree,
    generate_tech_stack,
)

__all__ = [
    "generate_all",
    "generate_coding_standards",
    "generate_tech_stack",
    "generate_source_tree",
]
