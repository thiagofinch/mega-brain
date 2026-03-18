"""
workflow_detector.py -- Greenfield/Brownfield Workflow Detector for MCE
========================================================================

Auto-detects whether a pipeline run is **greenfield** (new person, no
existing artifacts) or **brownfield** (update existing person with new
sources or MCE layers).

Usage::

    from core.intelligence.pipeline.mce.workflow_detector import detect

    mode = detect("alex-hormozi")
    print(mode)
    # WorkflowMode(mode='brownfield', has_agent=True, has_dna=True,
    #              has_mce=False, new_sources=['source3.txt'], delta_sources=[])

    if mode.is_greenfield:
        print("Fresh start -- full pipeline")
    else:
        print(f"Updating existing agent -- {len(mode.new_sources)} new sources")

Version: 1.0.0
Date: 2026-03-10
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("mce.workflow_detector")

# ---------------------------------------------------------------------------
# Imports: core.paths (with standalone fallback)
# ---------------------------------------------------------------------------

try:
    from core.paths import AGENTS_EXTERNAL, KNOWLEDGE_EXTERNAL, ROUTING
except ImportError:
    _ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
    AGENTS_EXTERNAL = _ROOT / "agents" / "external"
    KNOWLEDGE_EXTERNAL = _ROOT / "knowledge" / "external"
    _MISSION_CONTROL = _ROOT / ".claude" / "mission-control"
    ROUTING = {"mce_state": _MISSION_CONTROL / "mce"}


# ---------------------------------------------------------------------------
# WorkflowMode dataclass
# ---------------------------------------------------------------------------


@dataclass
class WorkflowMode:
    """Result of workflow detection for a persona slug.

    Attributes:
        mode: ``"greenfield"`` (no existing artifacts) or ``"brownfield"``
              (existing artifacts found).
        has_agent: Whether ``agents/external/{slug}/AGENT.md`` exists.
        has_dna: Whether ``knowledge/external/dna/persons/{slug}/`` has content.
        has_mce: Whether MCE-specific YAMLs exist in the MCE state directory.
        new_sources: List of source filenames found in inbox but NOT in
                     existing DNA-CONFIG.yaml.
        delta_sources: List of sources that exist in both but may have
                       been updated (reserved for future diff detection).
    """

    mode: str = "greenfield"
    has_agent: bool = False
    has_dna: bool = False
    has_mce: bool = False
    new_sources: list[str] = field(default_factory=list)
    delta_sources: list[str] = field(default_factory=list)

    @property
    def is_greenfield(self) -> bool:
        """Return *True* if this is a fresh pipeline run."""
        return self.mode == "greenfield"

    @property
    def is_brownfield(self) -> bool:
        """Return *True* if existing artifacts were detected."""
        return self.mode == "brownfield"

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary representation."""
        return {
            "mode": self.mode,
            "has_agent": self.has_agent,
            "has_dna": self.has_dna,
            "has_mce": self.has_mce,
            "new_sources": self.new_sources,
            "delta_sources": self.delta_sources,
        }


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------


def _check_agent(slug: str) -> bool:
    """Check if an agent directory with AGENT.md exists."""
    agent_dir = AGENTS_EXTERNAL / slug
    agent_md = agent_dir / "AGENT.md"
    return agent_md.exists()


def _check_dna(slug: str) -> bool:
    """Check if DNA directory exists and has at least one YAML file."""
    dna_dir = KNOWLEDGE_EXTERNAL / "dna" / "persons" / slug
    if not dna_dir.exists():
        return False
    yaml_files = list(dna_dir.glob("*.yaml")) + list(dna_dir.glob("*.yml"))
    return len(yaml_files) > 0


def _check_mce(slug: str) -> bool:
    """Check if MCE state files exist for the slug."""
    mce_base: Path = Path(ROUTING.get("mce_state", Path(".claude/mission-control/mce")))
    mce_dir = mce_base / slug
    if not mce_dir.exists():
        return False
    yaml_files = list(mce_dir.glob("*.yaml")) + list(mce_dir.glob("*.yml"))
    return len(yaml_files) > 0


def _get_existing_sources(slug: str) -> set[str]:
    """Extract source filenames from existing DNA-CONFIG.yaml.

    Looks for the ``dna_sources`` key (list of dicts with a ``file`` or
    ``filename`` field) or ``materiais_fonte`` (list of strings).

    Returns:
        Set of normalized source filenames found in the config.
    """
    dna_dir = KNOWLEDGE_EXTERNAL / "dna" / "persons" / slug
    config_path = dna_dir / "DNA-CONFIG.yaml"

    if not config_path.exists():
        return set()

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        logger.warning("Failed to read DNA-CONFIG.yaml for %s: %s", slug, exc)
        return set()

    if not isinstance(data, dict):
        return set()

    sources: set[str] = set()

    # Strategy 1: dna_sources (list of dicts with 'file' or 'filename')
    dna_sources = data.get("dna_sources", [])
    if isinstance(dna_sources, list):
        for entry in dna_sources:
            if isinstance(entry, dict):
                name = entry.get("file") or entry.get("filename") or ""
                if name:
                    sources.add(str(name).strip())
            elif isinstance(entry, str):
                sources.add(entry.strip())

    # Strategy 2: materiais_fonte (flat list of filenames)
    mat_fonte = data.get("materiais_fonte", [])
    if isinstance(mat_fonte, list):
        for entry in mat_fonte:
            if isinstance(entry, str) and entry.strip():
                sources.add(entry.strip())

    return sources


def _get_inbox_sources(slug: str) -> list[str]:
    """List source files in the inbox for the given slug.

    Checks both ``knowledge/external/inbox/{slug}/`` and common
    variations (uppercase, with spaces, etc.).

    Returns:
        List of filenames found in the inbox directory.
    """
    inbox_base = KNOWLEDGE_EXTERNAL / "inbox"
    if not inbox_base.exists():
        return []

    # Try exact slug match first, then case-insensitive search
    slug_dir = inbox_base / slug
    if not slug_dir.exists():
        # Try common patterns (e.g. "ALEX HORMOZI" for "alex-hormozi")
        slug_upper = slug.replace("-", " ").upper()
        for d in inbox_base.iterdir():
            if d.is_dir() and d.name.upper().replace("_", " ") == slug_upper:
                slug_dir = d
                break
        else:
            return []

    # Collect text/transcript files
    extensions = {".txt", ".docx", ".pdf", ".md", ".rtf"}
    files: list[str] = []
    for f in slug_dir.rglob("*"):
        if f.is_file() and f.suffix.lower() in extensions:
            files.append(f.name)
    return sorted(files)


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------


def detect(slug: str) -> WorkflowMode:
    """Detect workflow mode for a persona slug.

    Examines the filesystem to determine whether this is a greenfield
    (new person) or brownfield (update existing) pipeline run.

    Args:
        slug: Persona slug (e.g. ``"alex-hormozi"``).

    Returns:
        A :class:`WorkflowMode` dataclass with detection results.
    """
    has_agent = _check_agent(slug)
    has_dna = _check_dna(slug)
    has_mce = _check_mce(slug)

    # Determine mode
    is_brownfield = has_agent or has_dna or has_mce
    mode = "brownfield" if is_brownfield else "greenfield"

    # Determine new vs existing sources
    new_sources: list[str] = []
    delta_sources: list[str] = []

    if is_brownfield:
        existing = _get_existing_sources(slug)
        inbox_files = _get_inbox_sources(slug)

        for f in inbox_files:
            if f in existing:
                delta_sources.append(f)
            else:
                new_sources.append(f)

        logger.info(
            "Brownfield detected for %s: agent=%s, dna=%s, mce=%s, new_sources=%d, delta=%d",
            slug,
            has_agent,
            has_dna,
            has_mce,
            len(new_sources),
            len(delta_sources),
        )
    else:
        # Greenfield: all inbox files are new
        new_sources = _get_inbox_sources(slug)
        logger.info(
            "Greenfield detected for %s: %d sources in inbox",
            slug,
            len(new_sources),
        )

    return WorkflowMode(
        mode=mode,
        has_agent=has_agent,
        has_dna=has_dna,
        has_mce=has_mce,
        new_sources=new_sources,
        delta_sources=delta_sources,
    )
