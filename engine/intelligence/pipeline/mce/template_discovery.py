"""
template_discovery.py -- Template Manifest Discovery
=====================================================

Scans the phase templates directory for manifest.yaml files and returns
structured TemplateManifest dataclasses for each discovered template.

This module enables programmatic discovery of all pipeline templates,
their metadata, step bindings, and artifact contracts.

Usage::

    from engine.intelligence.pipeline.mce.template_discovery import (
        TemplateManifest,
        discover_templates,
    )

    templates = discover_templates()
    for t in templates:
        print(f"{t.name} (step {t.step_id}): {t.input_artifacts} -> {t.output_artifacts}")

Constraints:
    - stdlib + PyYAML only.
    - Never raises -- returns empty list on errors.
    - Idempotent -- safe to call multiple times.

Version: 1.0.0
Date: 2026-04-01
Story: MCE2-2.5
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("mce.template_discovery")

# Default templates directory (resolved relative to project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_DEFAULT_TEMPLATES_DIR = _PROJECT_ROOT / "core" / "templates" / "phases"


# ---------------------------------------------------------------------------
# Data contract
# ---------------------------------------------------------------------------


@dataclass
class TemplateManifest:
    """Metadata for a single pipeline phase template.

    Attributes:
        name: Template identifier (filename stem, e.g. ``"prompt-1.1-chunking"``).
        version: Semantic version string.
        step_id: Pipeline step number this template belongs to.
        step_name: Human-readable step name (e.g. ``"CHUNK"``).
        description: Brief description of what the template does.
        path: Absolute path to the template file on disk.
        input_artifacts: Artifacts required/consumed by this template.
        output_artifacts: Artifacts produced by this template.
    """

    name: str
    version: str = "1.0.0"
    step_id: int = 0
    step_name: str = ""
    description: str = ""
    path: str = ""
    input_artifacts: list[str] = field(default_factory=list)
    output_artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dict for JSON output."""
        return {
            "name": self.name,
            "version": self.version,
            "step_id": self.step_id,
            "step_name": self.step_name,
            "description": self.description,
            "path": self.path,
            "input_artifacts": self.input_artifacts,
            "output_artifacts": self.output_artifacts,
        }


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _parse_manifest_yaml(manifest_path: Path) -> list[dict[str, Any]]:
    """Parse a manifest.yaml and return the list of template entries.

    Args:
        manifest_path: Path to the manifest.yaml file.

    Returns:
        List of raw template dicts, or empty list on error.
    """
    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        logger.warning("Failed to parse manifest %s: %s", manifest_path, exc)
        return []

    if not isinstance(data, dict):
        logger.warning("Manifest %s is not a dict", manifest_path)
        return []

    templates = data.get("templates", [])
    if not isinstance(templates, list):
        logger.warning("Manifest %s: 'templates' is not a list", manifest_path)
        return []

    return templates


def discover_templates(
    directory: str | Path | None = None,
    *,
    manifest_name: str = "manifest.yaml",
) -> list[TemplateManifest]:
    """Discover all templates by scanning for manifest files.

    Looks for a ``manifest.yaml`` in the given directory and parses each
    template entry into a TemplateManifest dataclass.

    Args:
        directory: Templates directory to scan.  Defaults to
            ``core/templates/phases/``.
        manifest_name: Name of the manifest file to look for.

    Returns:
        List of TemplateManifest objects, sorted by (step_id, name).
    """
    templates_dir = Path(directory) if directory else _DEFAULT_TEMPLATES_DIR

    if not templates_dir.is_dir():
        logger.warning("Templates directory not found: %s", templates_dir)
        return []

    manifest_path = templates_dir / manifest_name
    if not manifest_path.is_file():
        logger.warning("No manifest found at %s", manifest_path)
        return []

    raw_entries = _parse_manifest_yaml(manifest_path)
    results: list[TemplateManifest] = []

    for entry in raw_entries:
        if not isinstance(entry, dict):
            continue

        name = entry.get("name", "")
        if not name:
            continue

        # Resolve the template file path
        template_file = templates_dir / f"{name}.md"
        resolved_path = str(template_file) if template_file.is_file() else ""

        manifest = TemplateManifest(
            name=name,
            version=str(entry.get("version", "1.0.0")),
            step_id=int(entry.get("step_id", 0)),
            step_name=str(entry.get("step_name", "")),
            description=str(entry.get("description", "")),
            path=resolved_path,
            input_artifacts=list(entry.get("input_artifacts", [])),
            output_artifacts=list(entry.get("output_artifacts", [])),
        )
        results.append(manifest)

    # Sort by step_id, then name for deterministic ordering
    results.sort(key=lambda m: (m.step_id, m.name))

    logger.info(
        "Discovered %d templates in %s",
        len(results),
        templates_dir,
    )
    return results


def discover_templates_by_step(
    directory: str | Path | None = None,
) -> dict[int, list[TemplateManifest]]:
    """Discover templates and group them by step_id.

    Args:
        directory: Templates directory to scan.

    Returns:
        Dict mapping step_id -> list of TemplateManifest for that step.
    """
    templates = discover_templates(directory)
    by_step: dict[int, list[TemplateManifest]] = {}
    for t in templates:
        by_step.setdefault(t.step_id, []).append(t)
    return by_step
