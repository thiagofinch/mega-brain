#!/usr/bin/env python3
"""
ACTIVATION GENERATOR - IDE Registration Layer v1.0
====================================================
Generates ACTIVATION.yaml for any agent and registers it across all IDEs.

Behavior:
    1. Reads agent's AGENT.md and DNA-CONFIG.yaml to extract info.
    2. Assigns nickname + archetype from OFFICIAL_NICKNAMES registry.
    3. Generates ACTIVATION.yaml in the agent's directory.
    4. Generates/updates IDE command files:
       - .claude/commands/agents/{slug}.md
       - .cursor/agents.yaml (append entry)
       - .windsurf/agents.yaml (append entry)
       - .gemini/agents/{slug}.md (if .gemini/ exists)
    5. Updates agents/_master-registry.yaml with activation metadata.

Constraints:
    - Python 3, stdlib + PyYAML only.
    - Imports from core.paths.
    - Never overwrites existing ACTIVATION.yaml without --force.
    - Logs every operation.

Version: 1.0.0
Date: 2026-03-09
Story: S16 (EPIC-REORG-001 extension)
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT))

from core.paths import AGENTS, COMMANDS, LOGS  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OFFICIAL NICKNAMES REGISTRY
# ---------------------------------------------------------------------------

OFFICIAL_NICKNAMES: dict[str, dict[str, str]] = {
    # -- External Experts --
    "alex-hormozi": {
        "name": "Alex",
        "icon": "\U0001f48a",
        "archetype": "Visionary",
        "tagline": "Scaling, offers, unit economics",
    },
    "cole-gordon": {
        "name": "Cole",
        "icon": "\U0001f3af",
        "archetype": "Builder",
        "tagline": "Sales systems, compensation",
    },
    "jeremy-miner": {
        "name": "Miner",
        "icon": "\U0001f9e0",
        "archetype": "Flow Master",
        "tagline": "NEPQ, neuro-persuasion",
    },
    "jeremy-haynes": {
        "name": "Haynes",
        "icon": "\U0001f4e1",
        "archetype": "Architect",
        "tagline": "Paid media, client acquisition",
    },
    "sam-oven": {
        "name": "Sam",
        "icon": "\u2699\ufe0f",
        "archetype": "Engineer",
        "tagline": "Systems, scaling, operations",
    },
    "jordan-lee": {
        "name": "Jordan",
        "icon": "\U0001f4ca",
        "archetype": "Analyst",
        "tagline": "Data-driven sales",
    },
    "richard-linder": {
        "name": "Linder",
        "icon": "\U0001f3d7\ufe0f",
        "archetype": "Builder",
        "tagline": "Founder-first hiring",
    },
    "full-sales-system": {
        "name": "FSS",
        "icon": "\U0001f4cb",
        "archetype": "Guardian",
        "tagline": "Full sales methodology",
    },
    "g4-educacao": {
        "name": "G4",
        "icon": "\U0001f393",
        "archetype": "Visionary",
        "tagline": "Brazilian business education",
    },
    "the-scalable-company": {
        "name": "TSC",
        "icon": "\U0001f4c8",
        "archetype": "Architect",
        "tagline": "Scalable business models",
    },
    # -- External Roles (hybrid) --
    "cfo": {
        "name": "Warren",
        "icon": "\U0001f4b0",
        "archetype": "Guardian",
        "tagline": "Financial health, margins, cash flow",
    },
    "cmo": {
        "name": "Madison",
        "icon": "\U0001f4e3",
        "archetype": "Visionary",
        "tagline": "Marketing strategy, positioning",
    },
    "cro": {
        "name": "Revenue",
        "icon": "\U0001f4c8",
        "archetype": "Architect",
        "tagline": "Revenue engine, pipeline",
    },
    "coo": {
        "name": "Atlas",
        "icon": "\U0001f3db\ufe0f",
        "archetype": "Operator",
        "tagline": "Operations, efficiency, scale",
    },
    "closer": {
        "name": "Hawk",
        "icon": "\U0001f3af",
        "archetype": "Builder",
        "tagline": "Deal closing, objection handling",
    },
    "bdr": {
        "name": "Scout",
        "icon": "\U0001f50d",
        "archetype": "Explorer",
        "tagline": "Prospecting, outbound",
    },
    "sds": {
        "name": "Bridge",
        "icon": "\U0001f309",
        "archetype": "Flow Master",
        "tagline": "Sales development, qualification",
    },
    "sales-manager": {
        "name": "Captain",
        "icon": "\u2693",
        "archetype": "Guardian",
        "tagline": "Team leadership, pipeline management",
    },
    "sales-lead": {
        "name": "Compass",
        "icon": "\U0001f9ed",
        "archetype": "Balancer",
        "tagline": "Sales direction, team alignment",
    },
    "sales-coordinator": {
        "name": "Relay",
        "icon": "\U0001f4e1",
        "archetype": "Operator",
        "tagline": "Coordination, scheduling, ops",
    },
    "lns": {
        "name": "Gardener",
        "icon": "\U0001f331",
        "archetype": "Empathizer",
        "tagline": "Lead nurturing, relationship building",
    },
    "customer-success": {
        "name": "Keeper",
        "icon": "\U0001f91d",
        "archetype": "Empathizer",
        "tagline": "Retention, satisfaction, growth",
    },
    "nepq-specialist": {
        "name": "Mirror",
        "icon": "\U0001fa9e",
        "archetype": "Flow Master",
        "tagline": "Neuro-emotional questioning",
    },
    "setter": {
        "name": "Arrow",
        "icon": "\U0001f3f9",
        "archetype": "Builder",
        "tagline": "Appointment setting, qualification",
    },
    "sdr": {
        "name": "Radar",
        "icon": "\U0001f4e1",
        "archetype": "Explorer",
        "tagline": "Sales development, outreach",
    },
    "paid-media-specialist": {
        "name": "Pixel",
        "icon": "\U0001f5a5\ufe0f",
        "archetype": "Engineer",
        "tagline": "Paid traffic, ROAS optimization",
    },
    # -- System --
    "conclave": {
        "name": "Council",
        "icon": "\u2696\ufe0f",
        "archetype": "Balancer",
        "tagline": "Multi-agent deliberation",
    },
    "boardroom": {
        "name": "Boardroom",
        "icon": "\U0001f399\ufe0f",
        "archetype": "Visionary",
        "tagline": "Executive episodes",
    },
}

# Archetype -> default tone mapping
_ARCHETYPE_TONES: dict[str, str] = {
    "Guardian": "analytical",
    "Builder": "pragmatic",
    "Visionary": "inspirational",
    "Architect": "systematic",
    "Operator": "direct",
    "Engineer": "precise",
    "Explorer": "curious",
    "Flow Master": "adaptive",
    "Balancer": "measured",
    "Empathizer": "empathetic",
    "Analyst": "data-driven",
    "Oracle": "synthesizing",
}

# Archetype -> default closing
_ARCHETYPE_CLOSINGS: dict[str, str] = {
    "Guardian": "Consider it protected.",
    "Builder": "Let's build.",
    "Visionary": "The future is clear.",
    "Architect": "The blueprint is set.",
    "Operator": "Executing now.",
    "Engineer": "Calibrated and ready.",
    "Explorer": "New territory mapped.",
    "Flow Master": "In flow.",
    "Balancer": "Equilibrium reached.",
    "Empathizer": "Your people, your priority.",
    "Analyst": "Data doesn't lie.",
    "Oracle": "All signals converge.",
}


def _load_agent_nicknames() -> None:
    """Scan agents/ directories for additional nicknames not in OFFICIAL_NICKNAMES.

    Discovers agent slugs from agents/external/, agents/business/, and
    agents/personal/ and auto-generates nickname entries for any that are
    not already registered. This keeps OFFICIAL_NICKNAMES free of
    hardcoded personal/business names.
    """
    for category_dir in ("external", "business", "personal"):
        category_path = AGENTS / category_dir
        if not category_path.exists():
            continue
        for child in category_path.iterdir():
            if child.is_dir() and child.name not in OFFICIAL_NICKNAMES:
                auto_name = child.name.replace("-", " ").title().split()[0]
                OFFICIAL_NICKNAMES[child.name] = {
                    "name": auto_name,
                    "icon": "\U0001f464",
                    "archetype": "Builder",
                    "tagline": f"Agent: {child.name}",
                }


_load_agent_nicknames()


# ---------------------------------------------------------------------------
# CATEGORY RESOLUTION
# ---------------------------------------------------------------------------

# Maps category labels to the relative path under agents/
_CATEGORY_PATHS: dict[str, str] = {
    "external/experts": "external",
    "external/roles": "cargo",
    "business/people": "business",
    "business/roles": "business",
    "personal": "personal",
    "system": "system",
    # Convenience aliases
    "external": "external",
    "cargo": "cargo",
    "business": "business",
}


def _resolve_agent_dir(slug: str, category: str) -> Path | None:
    """Find the actual directory for an agent, searching subdirectories.

    Cargo agents live inside subcategories like ``cargo/sales/closer/``
    so we need to walk.
    """
    base_folder = _CATEGORY_PATHS.get(category, category)
    base = AGENTS / base_folder

    # Direct hit
    if (base / slug).is_dir():
        return base / slug

    # Search one level deeper (cargo/sales/closer, cargo/c-level/cfo, etc.)
    # Prefer dirs that actually have AGENT.md
    candidates: list[Path] = []
    for child in base.iterdir():
        if child.is_dir() and (child / slug).is_dir():
            candidates.append(child / slug)

    # Return first candidate with AGENT.md, else first candidate
    for c in candidates:
        if (c / "AGENT.md").exists():
            return c
    if candidates:
        return candidates[0]

    # System agents may nest further (system/conclave/sintetizador)
    if base_folder == "system":
        for child in base.rglob(slug):
            if child.is_dir():
                return child

    return None


def _relative_to_root(path: Path) -> str:
    """Return path relative to project root."""
    try:
        return str(path.relative_to(_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# YAML / FILE HELPERS
# ---------------------------------------------------------------------------


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML file, returning empty dict on failure."""
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        logger.warning("Failed to parse YAML: %s", path)
        return {}


def _read_text(path: Path) -> str:
    """Read a text file, returning empty string on failure."""
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _write_text(path: Path, content: str) -> None:
    """Write text to a file, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_yaml(path: Path, data: dict[str, Any], header: str = "") -> None:
    """Write a YAML file with optional header comment."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = header + yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# AGENT INFO EXTRACTION
# ---------------------------------------------------------------------------


def _extract_title_from_agent_md(text: str, slug: str) -> str:
    """Extract a title from AGENT.md content."""
    # Look for a heading like "# PERSON AGENT" or first ## heading
    # Skip decorator lines (===, ---, ```, empty, or purely symbolic)
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## QUEM SOU"):
            continue
        if stripped.startswith("## "):
            candidate = stripped.lstrip("# ").strip()
            if _is_valid_title(candidate):
                return candidate
        if stripped.startswith("# "):
            candidate = stripped.lstrip("# ").strip()
            if _is_valid_title(candidate):
                return candidate
    # Fallback: look for > **Type:** or > **Version:** lines for context
    return slug.replace("-", " ").title()


def _is_valid_title(text: str) -> bool:
    """Check if a string is a valid title (not a decorator/border)."""
    if not text:
        return False
    # Skip lines that are purely decorators
    decorators = {"---", "===", "```", "~~~"}
    if text in decorators:
        return False
    # Skip lines made of only decorator characters (ASCII + Unicode box-drawing).
    # Unicode box-drawing: ═ ─ │ ╔ ╗ ╚ ╝ ╠ ╣ ╦ ╩ ╬ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ ║
    decorator_chars = set("=-`~*# \t═─│╔╗╚╝╠╣╦╩╬┌┐└┘├┤┬┴┼║░▒▓█▀▄")
    if all(ch in decorator_chars for ch in text):
        return False
    # Also reject if fewer than 3 alphanumeric characters remain
    alpha_count = sum(1 for ch in text if ch.isalnum())
    if alpha_count < 3:
        return False
    return True


def _extract_keywords_from_dna(dna_config: dict[str, Any], max_words: int = 5) -> list[str]:
    """Pull vocabulary words from DNA-CONFIG distribution keys or sources."""
    keywords: list[str] = []

    dist = dna_config.get("distribuicao", {})
    for key in dist:
        clean = key.replace("_", " ").title()
        if clean and clean not in keywords:
            keywords.append(clean)
        if len(keywords) >= max_words:
            break

    if len(keywords) < max_words:
        sources = dna_config.get("dna_sources", {}).get("primario", [])
        for src in sources:
            title = src.get("source_title", "")
            if title:
                words = title.split()[:2]
                for w in words:
                    if w not in keywords and len(keywords) < max_words:
                        keywords.append(w)

    return keywords[:max_words]


# ---------------------------------------------------------------------------
# ACTIVATION.yaml GENERATOR
# ---------------------------------------------------------------------------


def _generate_activation_yaml(
    slug: str,
    category: str,
    agent_dir: Path,
    nickname_data: dict[str, str],
    title: str,
    keywords: list[str],
) -> dict[str, Any]:
    """Build the ACTIVATION.yaml data dict."""
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    archetype = nickname_data.get("archetype", "Builder")
    tone = _ARCHETYPE_TONES.get(archetype, "pragmatic")
    closing = _ARCHETYPE_CLOSINGS.get(archetype, "Ready.")
    icon = nickname_data.get("icon", "")
    name = nickname_data.get("name", slug)
    tagline = nickname_data.get("tagline", "")

    category_path = _relative_to_root(agent_dir).replace("agents/", "", 1).rsplit(f"/{slug}", 1)[0]
    if not category_path or category_path == _relative_to_root(agent_dir):
        category_path = category

    return {
        "version": "1.0.0",
        "generated_at": now,
        "agent": {
            "name": name,
            "id": slug,
            "title": title,
            "icon": icon,
            "category": category,
            "whenToUse": tagline,
        },
        "persona_profile": {
            "archetype": archetype,
            "communication": {
                "tone": tone,
                "vocabulary": keywords,
                "greeting_levels": {
                    "minimal": f"{icon} {slug} ready",
                    "named": f"{icon} {name} ({archetype}) ready. {tagline}",
                },
                "signature_closing": closing,
            },
        },
        "commands": [
            {
                "name": "help",
                "visibility": ["full", "quick", "key"],
                "description": f"Show {name}'s commands",
            },
            {
                "name": "consult",
                "visibility": ["full", "quick"],
                "description": f"Ask {name} a question",
            },
            {
                "name": "analyze",
                "visibility": ["full"],
                "description": f"{name} analyzes a topic in their domain",
            },
            {
                "name": "exit",
                "visibility": ["full", "quick", "key"],
                "description": f"Exit {name} mode",
            },
        ],
        "sources": {
            "agent_md": _relative_to_root(agent_dir / "AGENT.md"),
            "soul_md": _relative_to_root(agent_dir / "SOUL.md"),
            "dna_config": _relative_to_root(agent_dir / "DNA-CONFIG.yaml"),
        },
        "ide_registration": {
            "claude": f".claude/commands/agents/{slug}.md",
            "cursor": ".cursor/agents.yaml",
            "windsurf": ".windsurf/agents.yaml",
            "gemini": f".gemini/agents/{slug}.md",
        },
    }


# ---------------------------------------------------------------------------
# IDE COMMAND GENERATORS
# ---------------------------------------------------------------------------


def _generate_claude_command(
    slug: str,
    nickname_data: dict[str, str],
    title: str,
    agent_dir: Path,
    category: str,
) -> str:
    """Generate .claude/commands/agents/{slug}.md content."""
    name = nickname_data.get("name", slug)
    icon = nickname_data.get("icon", "")
    archetype = nickname_data.get("archetype", "Builder")
    tagline = nickname_data.get("tagline", "")
    rel = _relative_to_root(agent_dir)

    lines = [
        f"# {slug}\n",
        f"Activate the {name} agent ({title}).",
        f"Category: {category}\n",
        "## Instructions\n",
        f"1. Read the agent definition: `{rel}/AGENT.md`",
        f"2. Read the soul: `{rel}/SOUL.md`",
        f"3. Load DNA: `{rel}/DNA-CONFIG.yaml`",
        f"4. Adopt {name}'s persona and respond as them.\n",
        f"> {icon} {name} ({archetype}) -- {tagline}\n",
    ]
    return "\n".join(lines)


def _update_cursor_windsurf_yaml(
    yaml_path: Path,
    slug: str,
    nickname_data: dict[str, str],
    title: str,
    category: str,
    agent_dir: Path,
) -> bool:
    """Append or update an entry in .cursor/agents.yaml or .windsurf/agents.yaml.

    Returns True if file was written.
    """
    if not yaml_path.parent.exists():
        return False

    name = nickname_data.get("name", slug)
    icon = nickname_data.get("icon", "")
    rel = _relative_to_root(agent_dir)

    existing: list[dict[str, Any]] = []
    if yaml_path.exists():
        try:
            raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                existing = raw
            elif isinstance(raw, dict) and "agents" in raw:
                existing = raw.get("agents", [])
        except Exception:
            existing = []

    # Remove existing entry for this slug
    existing = [e for e in existing if e.get("id") != slug]

    entry: dict[str, Any] = {
        "id": slug,
        "name": name,
        "title": title,
        "icon": icon,
        "category": category,
        "instructions": f"Read {rel}/AGENT.md and adopt {name}'s persona",
    }
    existing.append(entry)

    _write_yaml(
        yaml_path,
        {"agents": existing},
        f"# Agents registry - Auto-generated by activation_generator.py\n"
        f"# Last updated: {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n",
    )
    return True


def _generate_gemini_command(
    slug: str,
    nickname_data: dict[str, str],
    title: str,
    agent_dir: Path,
    category: str,
) -> str:
    """Generate .gemini/agents/{slug}.md content."""
    name = nickname_data.get("name", slug)
    icon = nickname_data.get("icon", "")
    archetype = nickname_data.get("archetype", "Builder")
    tagline = nickname_data.get("tagline", "")
    rel = _relative_to_root(agent_dir)

    lines = [
        f"# {name} ({archetype})\n",
        f"{icon} {tagline}\n",
        f"Load `{rel}/AGENT.md`, `{rel}/SOUL.md`, and `{rel}/DNA-CONFIG.yaml`.",
        f"Adopt {name}'s persona and respond as them.\n",
        f"Category: {category}\n",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MASTER REGISTRY UPDATER
# ---------------------------------------------------------------------------


def _update_master_registry(
    slug: str,
    category: str,
    nickname_data: dict[str, str],
    agent_dir: Path,
) -> bool:
    """Add activation metadata to _master-registry.yaml.

    Finds the entry for the slug and adds nickname/icon/archetype fields.
    Returns True if file was updated.
    """
    registry_path = AGENTS / "_master-registry.yaml"
    if not registry_path.exists():
        logger.warning("Master registry not found at %s", registry_path)
        return False

    # Load, modify, save approach.
    data = _read_yaml(registry_path)
    if not data:
        return False

    name = nickname_data.get("name", slug)
    icon = nickname_data.get("icon", "")
    archetype = nickname_data.get("archetype", "")

    updated = False

    # Search across all top-level category lists
    for section_key in ("external", "business", "personal"):
        agents_list = data.get(section_key, [])
        if not isinstance(agents_list, list):
            continue
        for entry in agents_list:
            if isinstance(entry, dict) and entry.get("id") == slug:
                entry["nickname"] = name
                entry["icon"] = icon
                entry["archetype"] = archetype
                entry["activation"] = True
                updated = True

    # Cargo is nested: cargo.sales, cargo.marketing, cargo.c-level
    cargo = data.get("cargo", {})
    if isinstance(cargo, dict):
        for _sub_key, agents_list in cargo.items():
            if not isinstance(agents_list, list):
                continue
            for entry in agents_list:
                if isinstance(entry, dict) and entry.get("id") == slug:
                    entry["nickname"] = name
                    entry["icon"] = icon
                    entry["archetype"] = archetype
                    entry["activation"] = True
                    updated = True

    # System is nested: system.conclave, system.boardroom
    system = data.get("system", {})
    if isinstance(system, dict):
        for _sub_key, agents_list in system.items():
            if not isinstance(agents_list, list):
                continue
            for entry in agents_list:
                if isinstance(entry, dict) and entry.get("id") == slug:
                    entry["nickname"] = name
                    entry["icon"] = icon
                    entry["archetype"] = archetype
                    entry["activation"] = True
                    updated = True

    if updated:
        header = (
            "# _master-registry.yaml\n"
            f"# Last updated: {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
            "# Auto-updated by activation_generator.py\n\n"
        )
        _write_yaml(registry_path, data, header)

    return updated


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

_LOG_PATH = LOGS / "activation-generator.jsonl"


def _log_event(
    slug: str,
    action: str,
    created: list[str] | None = None,
    updated: list[str] | None = None,
    errors: list[str] | None = None,
) -> None:
    """Append an event to the activation log."""
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "action": action,
        "slug": slug,
        "created": created or [],
        "updated": updated or [],
        "errors": errors or [],
        "generator": "activation_generator.py v1.0.0",
    }
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# CORE: generate_activation
# ---------------------------------------------------------------------------


def generate_activation(
    slug: str,
    category: str,
    *,
    force: bool = False,
) -> dict[str, list[str]]:
    """Generate ACTIVATION.yaml and register agent in all IDEs.

    Args:
        slug: Kebab-case agent identifier (e.g. 'alex-hormozi', 'closer').
        category: One of 'external/experts', 'external/roles', 'business/people',
                  'business/roles', 'personal', 'system', or shorthand
                  'external', 'cargo', 'business'.
        force: If True, overwrite existing ACTIVATION.yaml.

    Returns:
        {"created": [files], "updated": [files], "errors": []}
    """
    result: dict[str, list[str]] = {"created": [], "updated": [], "errors": []}

    # Resolve agent directory
    agent_dir = _resolve_agent_dir(slug, category)
    if agent_dir is None or not agent_dir.exists():
        msg = f"Agent directory not found for slug='{slug}' category='{category}'"
        result["errors"].append(msg)
        logger.error(msg)
        _log_event(slug, "generate_activation", errors=[msg])
        return result

    # Check AGENT.md exists
    agent_md_path = agent_dir / "AGENT.md"
    if not agent_md_path.exists():
        msg = f"No AGENT.md found at {agent_dir}"
        result["errors"].append(msg)
        logger.error(msg)
        _log_event(slug, "generate_activation", errors=[msg])
        return result

    # Check if ACTIVATION.yaml already exists
    activation_path = agent_dir / "ACTIVATION.yaml"
    if activation_path.exists() and not force:
        msg = f"ACTIVATION.yaml already exists at {activation_path}. Use force=True to overwrite."
        result["errors"].append(msg)
        logger.warning(msg)
        _log_event(slug, "generate_activation", errors=[msg])
        return result

    # Read agent data
    agent_md_text = _read_text(agent_md_path)
    dna_config = _read_yaml(agent_dir / "DNA-CONFIG.yaml")

    # Get nickname data (fall back to auto-generated)
    nickname_data = OFFICIAL_NICKNAMES.get(slug, {})
    if not nickname_data:
        # Auto-generate for unknown agents
        auto_name = slug.replace("-", " ").title().split()[0]
        nickname_data = {
            "name": auto_name,
            "icon": "\U0001f464",
            "archetype": "Builder",
            "tagline": f"Agent: {slug}",
        }
        logger.info("No official nickname for '%s', auto-generated: %s", slug, auto_name)

    title = _extract_title_from_agent_md(agent_md_text, slug)
    keywords = _extract_keywords_from_dna(dna_config)

    # 1. Generate ACTIVATION.yaml
    activation_data = _generate_activation_yaml(
        slug=slug,
        category=category,
        agent_dir=agent_dir,
        nickname_data=nickname_data,
        title=title,
        keywords=keywords,
    )
    activation_header = (
        "# ACTIVATION.yaml -- Auto-generated by activation_generator.py\n"
        "# DO NOT EDIT MANUALLY -- regenerated on agent creation/update\n\n"
    )
    _write_yaml(activation_path, activation_data, activation_header)
    rel_activation = _relative_to_root(activation_path)
    result["created"].append(rel_activation)
    logger.info("[CREATED] %s", rel_activation)

    # 2. Generate Claude Code slash command
    claude_cmd_dir = COMMANDS / "agents"
    claude_cmd_dir.mkdir(parents=True, exist_ok=True)
    claude_cmd_path = claude_cmd_dir / f"{slug}.md"
    claude_content = _generate_claude_command(slug, nickname_data, title, agent_dir, category)
    _write_text(claude_cmd_path, claude_content)
    rel_claude = _relative_to_root(claude_cmd_path)
    result["created"].append(rel_claude)
    logger.info("[CREATED] %s", rel_claude)

    # 3. Update .cursor/agents.yaml
    cursor_yaml = _ROOT / ".cursor" / "agents.yaml"
    if cursor_yaml.parent.exists() or True:
        # Create .cursor/ if it doesn't exist for future use
        wrote = _update_cursor_windsurf_yaml(
            cursor_yaml,
            slug,
            nickname_data,
            title,
            category,
            agent_dir,
        )
        if wrote:
            rel_cursor = _relative_to_root(cursor_yaml)
            result["updated"].append(rel_cursor)
            logger.info("[UPDATED] %s", rel_cursor)

    # 4. Update .windsurf/agents.yaml
    windsurf_yaml = _ROOT / ".windsurf" / "agents.yaml"
    if windsurf_yaml.parent.exists() or True:
        wrote = _update_cursor_windsurf_yaml(
            windsurf_yaml,
            slug,
            nickname_data,
            title,
            category,
            agent_dir,
        )
        if wrote:
            rel_windsurf = _relative_to_root(windsurf_yaml)
            result["updated"].append(rel_windsurf)
            logger.info("[UPDATED] %s", rel_windsurf)

    # 5. Generate .gemini command (only if .gemini/ exists)
    gemini_dir = _ROOT / ".gemini" / "agents"
    if (_ROOT / ".gemini").exists():
        gemini_path = gemini_dir / f"{slug}.md"
        gemini_content = _generate_gemini_command(
            slug,
            nickname_data,
            title,
            agent_dir,
            category,
        )
        _write_text(gemini_path, gemini_content)
        rel_gemini = _relative_to_root(gemini_path)
        result["created"].append(rel_gemini)
        logger.info("[CREATED] %s", rel_gemini)

    # 6. Update master registry
    registry_updated = _update_master_registry(slug, category, nickname_data, agent_dir)
    if registry_updated:
        result["updated"].append("agents/_master-registry.yaml")
        logger.info("[UPDATED] agents/_master-registry.yaml for '%s'", slug)

    _log_event(
        slug,
        "generate_activation",
        created=result["created"],
        updated=result["updated"],
        errors=result["errors"],
    )
    return result


# ---------------------------------------------------------------------------
# BATCH: generate_all
# ---------------------------------------------------------------------------


def _discover_all_agents() -> list[tuple[str, str, Path]]:
    """Walk the agents/ tree and find all directories with AGENT.md.

    Returns list of (slug, category, agent_dir).
    """
    found: list[tuple[str, str, Path]] = []

    # External experts
    external_dir = AGENTS / "external"
    if external_dir.exists():
        for child in sorted(external_dir.iterdir()):
            if child.is_dir() and (child / "AGENT.md").exists():
                found.append((child.name, "external", child))

    # Cargo roles (nested: cargo/sales/closer, cargo/c-level/cfo, etc.)
    cargo_dir = AGENTS / "cargo"
    if cargo_dir.exists():
        for sub in sorted(cargo_dir.iterdir()):
            if sub.is_dir():
                for agent in sorted(sub.iterdir()):
                    if agent.is_dir() and (agent / "AGENT.md").exists():
                        found.append((agent.name, "cargo", agent))

    # Business people
    business_dir = AGENTS / "business"
    if business_dir.exists():
        for child in sorted(business_dir.iterdir()):
            if child.is_dir() and (child / "AGENT.md").exists():
                found.append((child.name, "business", child))

    # Personal
    personal_dir = AGENTS / "personal"
    if personal_dir.exists():
        for child in sorted(personal_dir.iterdir()):
            if child.is_dir() and (child / "AGENT.md").exists():
                found.append((child.name, "personal", child))

    # System agents (nested: system/conclave/sintetizador, system/boardroom)
    system_dir = AGENTS / "system"
    if system_dir.exists():
        for sub in sorted(system_dir.iterdir()):
            if sub.is_dir():
                if (sub / "AGENT.md").exists():
                    found.append((sub.name, "system", sub))
                else:
                    for agent in sorted(sub.iterdir()):
                        if agent.is_dir() and (agent / "AGENT.md").exists():
                            found.append((agent.name, "system", agent))

    return found


def batch_generate_all(*, force: bool = False) -> dict[str, Any]:
    """Generate activations for all agents that have AGENT.md.

    Args:
        force: If True, regenerate even if ACTIVATION.yaml exists.

    Returns:
        Summary dict with per-agent results.
    """
    agents = _discover_all_agents()
    summary: dict[str, Any] = {
        "total_discovered": len(agents),
        "activated": 0,
        "skipped": 0,
        "errored": 0,
        "details": [],
    }

    for slug, category, agent_dir in agents:
        activation_path = agent_dir / "ACTIVATION.yaml"
        if activation_path.exists() and not force:
            summary["skipped"] += 1
            summary["details"].append(
                {
                    "slug": slug,
                    "category": category,
                    "status": "skipped",
                    "reason": "ACTIVATION.yaml exists",
                }
            )
            continue

        result = generate_activation(slug, category, force=force)

        if result["errors"]:
            summary["errored"] += 1
            summary["details"].append(
                {
                    "slug": slug,
                    "category": category,
                    "status": "error",
                    "errors": result["errors"],
                }
            )
        else:
            summary["activated"] += 1
            summary["details"].append(
                {
                    "slug": slug,
                    "category": category,
                    "status": "activated",
                    "created": result["created"],
                    "updated": result["updated"],
                }
            )

    _log_event(
        "_batch",
        "batch_generate_all",
        created=[f"total_activated={summary['activated']}"],
        errors=[f"total_errored={summary['errored']}"],
    )
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate ACTIVATION.yaml + IDE commands for agents.",
    )
    sub = parser.add_subparsers(dest="command", help="Sub-command")

    # Single agent
    single = sub.add_parser("generate", help="Generate activation for a single agent")
    single.add_argument("slug", help="Agent slug (e.g. 'alex-hormozi', 'closer')")
    single.add_argument(
        "--category",
        default="external",
        help="Agent category (external, cargo, business, personal, system)",
    )
    single.add_argument("--force", action="store_true", help="Overwrite existing ACTIVATION.yaml")

    # Batch
    batch = sub.add_parser("batch", help="Generate activations for ALL agents")
    batch.add_argument("--force", action="store_true", help="Regenerate all, even existing")

    # List
    sub.add_parser("list", help="List all discoverable agents")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.command == "generate":
        result = generate_activation(args.slug, args.category, force=args.force)
        _print_result(args.slug, result)
        if result["errors"]:
            sys.exit(1)

    elif args.command == "batch":
        summary = batch_generate_all(force=args.force)
        _print_batch_summary(summary)
        if summary["errored"] > 0:
            sys.exit(1)

    elif args.command == "list":
        agents = _discover_all_agents()
        print(f"\nDiscovered {len(agents)} agents:\n")
        for slug, category, agent_dir in agents:
            has_activation = (agent_dir / "ACTIVATION.yaml").exists()
            marker = "[A]" if has_activation else "[ ]"
            nick = OFFICIAL_NICKNAMES.get(slug, {}).get("name", "?")
            print(f"  {marker} {slug:<30} {category:<12} nickname={nick}")
        print("\n[A] = has ACTIVATION.yaml, [ ] = needs generation\n")

    else:
        parser.print_help()


def _print_result(slug: str, result: dict[str, list[str]]) -> None:
    """Pretty-print single agent result."""
    print(f"\n{'=' * 60}")
    print(f"  ACTIVATION GENERATOR - '{slug}'")
    print(f"{'=' * 60}")

    if result["created"]:
        print(f"\n  CREATED ({len(result['created'])}):")
        for f in result["created"]:
            print(f"    [+] {f}")

    if result["updated"]:
        print(f"\n  UPDATED ({len(result['updated'])}):")
        for f in result["updated"]:
            print(f"    [~] {f}")

    if result["errors"]:
        print(f"\n  ERRORS ({len(result['errors'])}):")
        for e in result["errors"]:
            print(f"    [!] {e}")

    print(f"{'=' * 60}\n")


def _print_batch_summary(summary: dict[str, Any]) -> None:
    """Pretty-print batch summary."""
    print(f"\n{'=' * 60}")
    print("  ACTIVATION GENERATOR - BATCH RESULTS")
    print(f"{'=' * 60}")
    print(f"\n  Discovered:  {summary['total_discovered']}")
    print(f"  Activated:   {summary['activated']}")
    print(f"  Skipped:     {summary['skipped']}")
    print(f"  Errors:      {summary['errored']}")

    if summary["errored"] > 0:
        print("\n  ERRORS:")
        for d in summary["details"]:
            if d["status"] == "error":
                print(f"    [!] {d['slug']}: {d.get('errors', [])}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
