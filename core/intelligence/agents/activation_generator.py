#!/usr/bin/env python3
"""
ACTIVATION GENERATOR - Compiled Persona Engine v2.0
====================================================
Generates ACTIVATION.yaml and self-contained compiled command files for agents.

Behavior:
    1. Reads agent's AGENT.md, SOUL.md, MEMORY.md, and DNA-CONFIG.yaml.
    2. Assigns nickname + archetype from OFFICIAL_NICKNAMES registry.
    3. Extracts voice, operations, decisions, insights, and connections.
    4. Generates ACTIVATION.yaml with source hashes in the agent's directory.
    5. Generates compiled, self-contained IDE command files:
       - .claude/commands/agents/{slug}.md (zero-indirection persona)
       - .cursor/agents.yaml (append entry)
       - .windsurf/agents.yaml (append entry)
       - .gemini/agents/{slug}.md (if .gemini/ exists)
    6. Updates agents/_master-registry.yaml with activation metadata.

Constraints:
    - Python 3, stdlib + PyYAML only.
    - Imports from core.paths.
    - Never overwrites existing ACTIVATION.yaml without --force.
    - Logs every operation.

Version: 2.0.0
Date: 2026-03-16
Story: S1.0-S1.9 (Self-Contained Agent Activation)
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------
from core.paths import AGENTS, COMMANDS, LOGS, ROOT

_ROOT = ROOT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OFFICIAL NICKNAMES REGISTRY
# ---------------------------------------------------------------------------

OFFICIAL_NICKNAMES: dict[str, dict[str, str]] = {
    # -- External experts and persons loaded dynamically from agents/ directories --
    # See _load_agent_nicknames() below.
    # -- Cargo Roles (hybrid) --
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
    # -- Personal agents loaded dynamically from agents/personal/ --
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

def _load_agent_nicknames() -> None:
    """Scan agents/ directories and populate OFFICIAL_NICKNAMES dynamically."""
    for category in ("external", "business", "personal"):
        agents_dir = AGENTS / category
        if not agents_dir.is_dir():
            continue
        for agent_dir in sorted(agents_dir.iterdir()):
            if not agent_dir.is_dir() or agent_dir.name.startswith(("_", ".")):
                continue
            slug = agent_dir.name
            if slug in OFFICIAL_NICKNAMES:
                continue
            # Try to read DNA-CONFIG.yaml for metadata
            dna_path = agent_dir / "DNA-CONFIG.yaml"
            name = slug.split("-")[0].title()
            icon = "\U0001f4a1"
            archetype = "Expert"
            tagline = ""
            if dna_path.exists():
                try:
                    data = yaml.safe_load(dna_path.read_text(encoding="utf-8")) or {}
                    name = data.get("display_name", name)
                    icon = data.get("icon", icon)
                    archetype = data.get("archetype", archetype)
                    tagline = data.get("tagline", tagline)
                except Exception:
                    pass
            OFFICIAL_NICKNAMES[slug] = {
                "name": name,
                "icon": icon,
                "archetype": archetype,
                "tagline": tagline,
            }


_load_agent_nicknames()

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

    # System and business agents may nest further (system/conclave/sintetizador,
    # business/collaborators/finance/diego-monet)
    for child in base.rglob(slug):
        if child.is_dir() and (child / "AGENT.md").exists():
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
# HEADER ALIAS CONSTANTS (S1.0)
# ---------------------------------------------------------------------------
# Each constant lists known header variants across all AGENT/SOUL.md formats.
# Used by _find_section() for multi-format extraction.

VOICE_HEADERS: list[str] = [
    "SISTEMA DE VOZ",
    "COMO FALO",
    "COMO EU FALO",
    "VOZ",
    "COMO PENSO",
]

IDENTITY_HEADERS: list[str] = [
    "QUEM SOU EU",
    "QUEM SOU",
    "IDENTIDADE",
    "WHO AM I",
]

BELIEFS_HEADERS: list[str] = [
    "O QUE ACREDITO",
    "CRENCAS",
    "BELIEFS",
    "FILOSOFIAS CENTRAIS",
]

ANTI_PATTERN_HEADERS: list[str] = [
    "O QUE NAO SOU",
    "O QUE NÃO SOU",
    "WHAT I AM NOT",
    "NUNCA",
]

OPERATIONAL_HEADERS: list[str] = [
    "PARTE 4",
    "NUCLEO OPERACIONAL",
    "NÚCLEO OPERACIONAL",
    "QUANDO CONSULTAR",
    "QUANDO ATIVAR",
    "MISSAO",
    "MISSÃO",
    "4.1 MISS",
]

DECISION_HEADERS: list[str] = [
    "PARTE 6",
    "MOTOR DE DECISAO",
    "MOTOR DE DECISÃO",
    "REGRAS DE DECISAO",
    "REGRAS DE DECISÃO",
    "REGRAS IF-THEN",
    "DECISION",
    "6.1 HEUR",
    "MINHAS REGRAS DE DECISAO",
    "3.1 REGRAS DE DECISAO",
]

CONNECTION_HEADERS: list[str] = [
    "PARTE 7",
    "INTERFACES DE CONEXAO",
    "INTERFACES DE CONEXÃO",
    "COMPLEMENTA",
    "TENSIONA",
    "8.3 INTERFACE",
    "7.1 CONEX",
    "7.1 INTEGRA",
]

INSIGHTS_HEADERS: list[str] = [
    "APRENDIZADOS",
    "INSIGHTS",
    "LEARNINGS",
]

PATTERNS_HEADERS: list[str] = [
    "PADROES DECISORIOS",
    "PADRÕES DECISÓRIOS",
    "DECISION PATTERNS",
    "PADROES",
    "PADRÕES",
]

FORBIDDEN_HEADERS: list[str] = [
    "NUNCA DIGO",
    "NUNCA USO",
    "FRASES QUE NUNCA",
    "FORBIDDEN",
    "FRASES QUE EU NUNCA USO",
]


# ---------------------------------------------------------------------------
# SECTION FINDER (S1.0)
# ---------------------------------------------------------------------------


def _find_section(text: str, aliases: list[str]) -> str:
    """Find a markdown section by trying header aliases in order.

    For each alias, searches for ``## .*{alias}.*`` (case-insensitive).
    Returns content between the matching header and the next ``## `` header
    (or EOF). Returns empty string if no alias matches. Never raises.
    """
    if not text:
        return ""

    try:
        for alias in aliases:
            # Build pattern: ## followed by anything containing the alias
            pattern = re.compile(
                r"^##\s+.*" + re.escape(alias) + r".*$",
                re.IGNORECASE | re.MULTILINE,
            )
            match = pattern.search(text)
            if match:
                # Find the end: next ## header or EOF
                start = match.end()
                next_header = re.search(r"^## ", text[start:], re.MULTILINE)
                if next_header:
                    section = text[start : start + next_header.start()]
                else:
                    section = text[start:]
                return section.strip()
    except Exception:
        pass

    return ""


# ---------------------------------------------------------------------------
# VOICE BLOCK EXTRACTOR (S1.1 + S1.2)
# ---------------------------------------------------------------------------


def _extract_voice_block(soul_md_path: Path) -> dict:
    """Extract voice data from SOUL.md into structured dict.

    Returns dict with keys: identity, beliefs, tone, mandatory_vocabulary,
    forbidden_vocabulary, signature_phrases, argumentation_pattern, anti_patterns.
    Returns empty dict on failure. Never raises.
    """
    text = _read_text(soul_md_path)
    if not text:
        return {}

    result: dict[str, Any] = {}

    try:
        # --- Identity (first 2-3 sentences from QUEM SOU EU) ---
        identity_text = _find_section(text, IDENTITY_HEADERS)
        if identity_text:
            sentences = [
                s.strip()
                for s in identity_text.split(".")
                if s.strip() and not s.strip().startswith("^[")
            ]
            result["identity"] = ". ".join(sentences[:3]) + "." if sentences else ""

        # --- Beliefs (from O QUE ACREDITO - extract bullet points, max 5) ---
        beliefs_text = _find_section(text, BELIEFS_HEADERS)
        if beliefs_text:
            beliefs: list[str] = []
            for line in beliefs_text.split("\n"):
                line = line.strip()
                if line.startswith(("- ", "* ", "• ")):
                    clean = line.lstrip("-*• ").split("^[")[0].strip()
                    if clean:
                        beliefs.append(clean)
                elif line.startswith("**") and ":" in line:
                    # Handle bold-label format: **Label:** description
                    clean = line.split("^[")[0].strip()
                    if clean:
                        beliefs.append(clean)
            result["beliefs"] = beliefs[:5]

        # --- Voice section parsing (tone, vocab, phrases, argumentation) ---
        voice_text = _find_section(text, VOICE_HEADERS)
        if voice_text:
            tone: list[str] = []
            vocab: list[str] = []
            phrases: list[str] = []
            argumentation: list[str] = []

            current_subsection = ""
            for line in voice_text.split("\n"):
                stripped = line.strip()
                lower_stripped = stripped.lower()

                # Detect subsection headers
                if stripped.startswith("### ") or (
                    stripped.startswith("**") and stripped.endswith("**")
                ):
                    current_subsection = lower_stripped
                    continue

                # Special handling for compact "VOZ" format (conclave):
                # **Tom:** Cetico, direto, construtivo
                if stripped.startswith("**Tom") or stripped.startswith("**Tone"):
                    tone_val = stripped.split(":", 1)
                    if len(tone_val) > 1:
                        for t in tone_val[1].split(","):
                            t = t.strip().rstrip("*")
                            if t:
                                tone.append(t)
                    continue
                if stripped.startswith("**Nunca digo") or stripped.startswith(
                    "**Nunca uso"
                ):
                    # Handled in forbidden section below
                    continue
                if stripped.startswith("**Sempre digo"):
                    phrase_val = stripped.split(":", 1)
                    if len(phrase_val) > 1:
                        for p in phrase_val[1].split('",'):
                            p = p.strip().strip('"').strip()
                            if p and len(p) > 5:
                                phrases.append(p)
                    continue

                if "tom" in current_subsection or "tone" in current_subsection:
                    if stripped.startswith(("- **", "- ")):
                        clean = stripped.lstrip("- ").split("^[")[0].strip()
                        if clean:
                            tone.append(clean)

                elif (
                    "vocabul" in current_subsection
                    or "lexico" in current_subsection
                    or "léxico" in current_subsection
                ):
                    if stripped.startswith(("- ", "* ", "• ")):
                        clean = stripped.lstrip("-*• ").split("^[")[0].strip()
                        if clean:
                            vocab.append(clean)

                elif (
                    "frase" in current_subsection
                    or "phrase" in current_subsection
                    or "tipica" in current_subsection
                    or "típica" in current_subsection
                    or "signature" in current_subsection
                ):
                    if stripped.startswith(("- ", "* ", "• ")):
                        clean = stripped.lstrip("-*• ").split("^[")[0].strip()
                        if clean and len(clean) > 10:
                            phrases.append(clean)

                elif (
                    "argumenta" in current_subsection
                    or ("pattern" in current_subsection and "anti" not in current_subsection)
                ):
                    if stripped.startswith(
                        ("- ", "* ", "• ", "1", "2", "3", "4", "5")
                    ):
                        clean = (
                            stripped.lstrip("-*•0123456789. ").split("^[")[0].strip()
                        )
                        if clean:
                            argumentation.append(clean)

            if tone:
                result["tone"] = tone[:4]
            if vocab:
                result["mandatory_vocabulary"] = vocab[:15]
            if phrases:
                result["signature_phrases"] = phrases[:7]
            if argumentation:
                result["argumentation_pattern"] = argumentation[:5]

        # --- Argumentation pattern (try separate ## section if not found in voice) ---
        if "argumentation_pattern" not in result:
            arg_text = _find_section(text, ["PADROES DE ARGUMENTACAO", "PADRÕES DE ARGUMENTAÇÃO", "ARGUMENTATION PATTERN"])
            if arg_text:
                arg_items: list[str] = []
                for line in arg_text.split("\n"):
                    stripped = line.strip()
                    if stripped.startswith(("1", "2", "3", "4", "5")):
                        clean = stripped.lstrip("0123456789. ").split("^[")[0].strip()
                        # Remove bold markers like **text**
                        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", clean)
                        if clean:
                            arg_items.append(clean)
                    elif stripped.startswith(("- ", "• ")):
                        clean = stripped.lstrip("-• ").split("^[")[0].strip()
                        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", clean)
                        if clean:
                            arg_items.append(clean)
                if arg_items:
                    result["argumentation_pattern"] = arg_items[:5]

        # --- Anti-patterns (from O QUE NAO SOU) ---
        anti_text = _find_section(text, ANTI_PATTERN_HEADERS)
        if anti_text:
            anti: list[str] = []
            for line in anti_text.split("\n"):
                line = line.strip()
                if line.startswith(("- ", "* ", "• ")):
                    clean = line.lstrip("-*• ").split("^[")[0].strip()
                    if clean:
                        anti.append(clean)
            result["anti_patterns"] = anti[:7]

        # --- Forbidden vocabulary (from NUNCA DIGO / NUNCA USO sections) ---
        forbidden_text = _find_section(text, FORBIDDEN_HEADERS)
        forbidden: list[str] = []
        if forbidden_text:
            for line in forbidden_text.split("\n"):
                line = line.strip()
                if line.startswith(("- ", "* ", "• ")):
                    clean = (
                        line.lstrip('-*• "').rstrip('"').split("^[")[0].strip()
                    )
                    if clean:
                        forbidden.append(clean)

        # Also mine "Nunca digo:" / "Nunca uso:" from compact VOZ format
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("**Nunca digo") or stripped.startswith(
                "**Nunca uso"
            ):
                val = stripped.split(":", 1)
                if len(val) > 1:
                    for item in val[1].split('",'):
                        item = item.strip().strip('"*').strip()
                        if item and item not in forbidden:
                            forbidden.append(item)

        # Also derive from anti-patterns if present
        if not forbidden and "anti_patterns" in result:
            anti_items = result["anti_patterns"]
            for ap in anti_items[:5]:
                # Filter out prose lines to avoid false positives
                if "nunca" in ap.lower() or "não" in ap.lower() or "nao" in ap.lower():
                    forbidden.append(ap)
            # If still empty after filtering, use all anti-patterns
            if not forbidden:
                forbidden = [f"Avoid: {ap}" for ap in anti_items[:5]]

        if forbidden:
            result["forbidden_vocabulary"] = forbidden[:10]

    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# OPERATIONAL CORE EXTRACTOR (S1.3)
# ---------------------------------------------------------------------------


def _extract_operational_core(agent_md_path: Path) -> dict:
    """Extract operational core from AGENT.md (PARTE 4 or equivalent).

    Returns dict with keys: use_cases (list[str]), boundaries (list[str]).
    Returns empty dict on failure. Never raises.
    """
    text = _read_text(agent_md_path)
    if not text:
        return {}

    result: dict[str, list[str]] = {}

    try:
        op_text = _find_section(text, OPERATIONAL_HEADERS)
        if not op_text:
            return {}

        use_cases: list[str] = []
        boundaries: list[str] = []
        current = "use_cases"

        for line in op_text.split("\n"):
            stripped = line.strip()
            lower = stripped.lower()

            # Detect "when not" / "NAO" sections
            if any(
                kw in lower
                for kw in [
                    "nao consultar",
                    "não consultar",
                    "when not",
                    "quando nao",
                    "quando não",
                    "nao ativar",
                    "não ativar",
                    "nao sou",
                    "não sou",
                ]
            ):
                current = "boundaries"
                continue
            # Detect "when to" / "ativar" sections
            if any(
                kw in lower
                for kw in [
                    "quando consultar",
                    "when to",
                    "ativar quando",
                    "trigger prim",
                ]
            ):
                current = "use_cases"
                continue

            if stripped.startswith(("- ", "* ", "• ")):
                clean = stripped.lstrip("-*• ").split("^[")[0].strip()
                if clean:
                    if current == "use_cases":
                        use_cases.append(clean)
                    else:
                        boundaries.append(clean)

        if use_cases:
            result["use_cases"] = use_cases[:7]
        if boundaries:
            result["boundaries"] = boundaries[:5]

    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# DECISION ENGINE EXTRACTOR (S1.4)
# ---------------------------------------------------------------------------


def _extract_decision_engine(
    agent_md_path: Path,
    soul_md_path: Path,
) -> list[dict]:
    """Extract decision rules from AGENT.md and SOUL.md as IF/THEN pairs.

    Searches AGENT.md first; if empty, falls back to SOUL.md.
    Returns list of dicts with keys: situation, decision, source.
    Returns empty list on failure. Never raises.
    """
    rules: list[dict[str, str]] = []

    try:
        for path in [agent_md_path, soul_md_path]:
            text = _read_text(path)
            if not text:
                continue

            dec_text = _find_section(text, DECISION_HEADERS)
            if not dec_text:
                continue

            for line in dec_text.split("\n"):
                stripped = line.strip()

                # Handle table rows: | Regra | Decisao | Source |
                if stripped.startswith("|") and not stripped.startswith("|--"):
                    cells = [c.strip() for c in stripped.split("|") if c.strip()]
                    if len(cells) >= 2:
                        # Skip header rows
                        header_words = {"regra", "decisao", "decisão", "#", "situação", "situacao"}
                        if cells[0].lower() in header_words:
                            continue
                        source = cells[2] if len(cells) >= 3 else ""
                        rules.append(
                            {
                                "situation": cells[0],
                                "decision": cells[1],
                                "source": source,
                            }
                        )
                        continue

                # Handle IF/THEN format
                lower = stripped.lower()
                if lower.startswith("if ") or lower.startswith("se "):
                    # Try to find the THEN part on the same or next line
                    if "then" in lower or "→" in stripped or "->" in stripped:
                        parts = re.split(r"(?i)\bthen\b|→|->", stripped, maxsplit=1)
                        if len(parts) == 2:
                            situation = re.sub(r"^(?:IF|SE)\s+", "", parts[0].strip(), flags=re.IGNORECASE).strip()
                            decision = parts[1].split("^[")[0].strip()
                            source_match = re.findall(r"\^?\[([^\]]+)\]", stripped)
                            source = source_match[-1] if source_match else ""
                            rules.append(
                                {
                                    "situation": situation,
                                    "decision": decision,
                                    "source": source,
                                }
                            )
                            continue

                # Handle bullet-style rules: "- **Always/Sempre:** ..."
                # or "- SE ... → ..."
                if stripped.startswith(("- **", "- SE ", "- se ")):
                    if "→" in stripped or "->" in stripped:
                        parts = re.split(r"→|->", stripped, maxsplit=1)
                        if len(parts) == 2:
                            situation = parts[0].lstrip("-*• ").split("^[")[0].strip()
                            decision = parts[1].split("^[")[0].strip()
                            source_match = re.findall(r"\^?\[([^\]]+)\]", stripped)
                            source = source_match[-1] if source_match else ""
                            rules.append(
                                {
                                    "situation": situation,
                                    "decision": decision,
                                    "source": source,
                                }
                            )
                            continue

                # Handle numbered rules: "1. SE founder preso → ..."
                if (
                    stripped
                    and stripped[0].isdigit()
                    and ("→" in stripped or "->" in stripped)
                ):
                    parts = re.split(r"→|->", stripped, maxsplit=1)
                    if len(parts) == 2:
                        situation = (
                            parts[0].lstrip("0123456789. ").split("^[")[0].strip()
                        )
                        decision = parts[1].split("^[")[0].strip()
                        source_match = re.findall(r"\^?\[([^\]]+)\]", stripped)
                        source = source_match[-1] if source_match else ""
                        rules.append(
                            {
                                "situation": situation,
                                "decision": decision,
                                "source": source,
                            }
                        )

            if rules:
                break  # Got rules from first source, no need to check fallback

    except Exception:
        pass

    return rules[:7]


# ---------------------------------------------------------------------------
# TOP INSIGHTS EXTRACTOR (S1.5)
# ---------------------------------------------------------------------------


def _extract_top_insights(memory_md_path: Path) -> dict:
    """Extract top insights and decision patterns from MEMORY.md.

    Returns dict with keys: insights (list of up to 10 strings),
    decision_patterns (list of up to 5 dicts with situation/decision keys).
    Returns empty dict on failure. Never raises.
    """
    text = _read_text(memory_md_path)
    if not text:
        return {}

    result: dict[str, Any] = {}

    try:
        # --- Extract insights ---
        insights_text = _find_section(text, INSIGHTS_HEADERS)
        insights: list[str] = []

        if insights_text:
            for line in insights_text.split("\n"):
                stripped = line.strip()

                # Table format: | # | Insight | Fonte | Ref |
                if stripped.startswith("|") and not stripped.startswith("|--"):
                    cells = [c.strip() for c in stripped.split("|") if c.strip()]
                    if len(cells) >= 2:
                        # Skip header row
                        if cells[0].lower() in ("#", "id", "num"):
                            continue
                        # The insight text is typically in cells[1]
                        insight_text = cells[1] if len(cells) >= 2 else ""
                        if insight_text and not insight_text.startswith("---"):
                            insights.append(insight_text)

                # Bullet format
                elif stripped.startswith(("- ", "* ", "• ")):
                    clean = stripped.lstrip("-*• ").split("^[")[0].strip()
                    if clean:
                        insights.append(clean)

                # Numbered format: "1. something"
                elif stripped and stripped[0].isdigit() and ". " in stripped:
                    clean = stripped.split(". ", 1)[1].split("^[")[0].strip()
                    if clean:
                        insights.append(clean)

        if insights:
            result["insights"] = insights[:10]

        # --- Extract decision patterns ---
        patterns_text = _find_section(text, PATTERNS_HEADERS)
        patterns: list[dict[str, str]] = []

        if patterns_text:
            for line in patterns_text.split("\n"):
                stripped = line.strip()

                # Table format: | Situacao | Decisao Padrao | Fonte |
                if stripped.startswith("|") and not stripped.startswith("|--"):
                    cells = [c.strip() for c in stripped.split("|") if c.strip()]
                    if len(cells) >= 2:
                        header_words = {
                            "situacao",
                            "situação",
                            "situation",
                            "id",
                            "#",
                        }
                        if cells[0].lower() in header_words:
                            continue
                        patterns.append(
                            {
                                "situation": cells[0],
                                "decision": cells[1] if len(cells) >= 2 else "",
                            }
                        )

                # Bullet format
                elif stripped.startswith(("- ", "* ", "• ")):
                    clean = stripped.lstrip("-*• ").split("^[")[0].strip()
                    if clean:
                        patterns.append(
                            {"situation": clean, "decision": ""}
                        )

        if patterns:
            result["decision_patterns"] = patterns[:5]

    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# CONNECTION INTERFACES EXTRACTOR (S1.6)
# ---------------------------------------------------------------------------


def _extract_connections(agent_md_path: Path) -> list[dict]:
    """Extract connection interfaces from AGENT.md (PARTE 7 or equivalent).

    Also handles split-header Format C where COMPLEMENTA and TENSIONA are
    separate ## sections.
    Returns list of dicts with keys: agent, interaction_type.
    Returns empty list on failure. Never raises.
    """
    text = _read_text(agent_md_path)
    if not text:
        return []

    connections: list[dict[str, str]] = []

    try:
        # First try the unified section (PARTE 7 / 7.1 INTEGRACOES)
        conn_text = _find_section(text, CONNECTION_HEADERS)
        if conn_text:
            connections.extend(_parse_connection_block(conn_text, "reference"))

        # Also try split headers: COMPLEMENTA, TENSIONA, ALINHA
        for header, interaction_type in [
            (["COMPLEMENTA"], "complementary"),
            (["TENSIONA"], "conflicting"),
            (["ALINHA"], "aligned"),
        ]:
            split_text = _find_section(text, header)
            if split_text:
                connections.extend(
                    _parse_connection_block(split_text, interaction_type)
                )

        # Deduplicate by agent name
        seen: set[str] = set()
        unique: list[dict[str, str]] = []
        for conn in connections:
            agent_name = conn.get("agent", "")
            if agent_name and agent_name not in seen:
                seen.add(agent_name)
                unique.append(conn)
        connections = unique

    except Exception:
        pass

    return connections


def _parse_connection_block(
    text: str, default_interaction: str
) -> list[dict[str, str]]:
    """Parse a connection block for agent names and interaction types."""
    connections: list[dict[str, str]] = []

    # Handle table format: | Agente | Tipo de Interacao |
    for line in text.split("\n"):
        stripped = line.strip()

        if stripped.startswith("|") and not stripped.startswith("|--"):
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            if len(cells) >= 2:
                header_words = {"agente", "agent", "tipo", "type", "nome"}
                if cells[0].lower() in header_words:
                    continue
                agent_name = cells[0].strip("* ")
                interaction_desc = cells[1] if len(cells) >= 2 else ""
                interaction_type = _classify_interaction(
                    interaction_desc, default_interaction
                )
                connections.append(
                    {"agent": agent_name, "interaction_type": interaction_type}
                )
                continue

        # Handle named blocks (all-caps name followed by description lines)
        if (
            stripped
            and stripped.isupper()
            and len(stripped) > 2
            and not stripped.startswith(("─", "═", "┌", "├", "└", "│", "┐"))
        ):
            connections.append(
                {"agent": stripped.title(), "interaction_type": default_interaction}
            )

    return connections


def _classify_interaction(desc: str, default: str) -> str:
    """Classify interaction type from description text."""
    lower = desc.lower()
    if any(w in lower for w in ["complementar", "complementa", "alinhado", "aligned"]):
        return "complementary"
    if any(w in lower for w in ["tensiona", "conflito", "conflicting", "tensão"]):
        return "conflicting"
    if any(w in lower for w in ["delega", "delegating"]):
        return "delegating"
    if any(w in lower for w in ["referencia", "reference", "cruzada"]):
        return "reference"
    if any(w in lower for w in ["alinha", "aligned"]):
        return "aligned"
    return default


# ---------------------------------------------------------------------------
# CATEGORY RESOLVER (S1.8)
# ---------------------------------------------------------------------------

_CATEGORY_CACHE: dict[str, str] = {}


def _resolve_category_from_slug(slug: str) -> str | None:
    """Resolve category from slug by scanning agents/ directories.

    Uses a module-level cache to avoid repeated tree walks.
    Returns category string or None if not found. Never raises.
    """
    if slug in _CATEGORY_CACHE:
        return _CATEGORY_CACHE[slug]

    try:
        # Populate cache on first call
        if not _CATEGORY_CACHE:
            for s, cat, _ in _discover_all_agents():
                _CATEGORY_CACHE[s] = cat

        return _CATEGORY_CACHE.get(slug)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# COMPILED COMMAND FORMATTER (S1.7)
# ---------------------------------------------------------------------------

# Section line caps
_MAX_VOICE_LINES = 100
_MAX_OPERATIONAL_LINES = 40
_MAX_DECISION_LINES = 60
_MAX_INSIGHTS_LINES = 80
_MAX_CONNECTION_LINES = 40
_TOTAL_HARD_CAP = 400


def _format_compiled_command(
    slug: str,
    nickname_data: dict[str, str],
    title: str,
    agent_dir: Path,
    category: str,
    voice_data: dict,
    operations: dict,
    decisions: list[dict],
    insights: dict,
    connections: list[dict],
) -> str:
    """Format a self-contained compiled command file.

    Combines all extracted sections into a single zero-indirection persona file.
    Returns the full markdown content string.
    """
    name = nickname_data.get("name", slug)
    icon = nickname_data.get("icon", "")
    archetype = nickname_data.get("archetype", "Builder")
    tagline = nickname_data.get("tagline", "")
    rel = _relative_to_root(agent_dir)

    # Find DNA path
    dna_config_path = agent_dir / "DNA-CONFIG.yaml"
    dna_path = _relative_to_root(dna_config_path) if dna_config_path.exists() else ""

    lines: list[str] = []

    # --- Header ---
    lines.append(f"# {slug}\n")
    lines.append(f"Activate the {name} agent ({title}).")
    lines.append(f"Category: {category}\n")

    # --- Activation Notice ---
    lines.append("## ACTIVATION NOTICE\n")
    lines.append("> **COMPILED ARTIFACT** -- All context needed for activation is embedded below.")
    lines.append(f"> Source files at `{rel}/` are the canonical source of truth for editing.")
    lines.append("> Do NOT read external files for activation.")
    lines.append("> Generated by activation_generator.py v2.0 -- do not edit manually.\n")

    # --- Voice Injection Block ---
    voice_lines = _format_voice_section(voice_data, name)
    if len(voice_lines) > _MAX_VOICE_LINES:
        voice_lines = voice_lines[:_MAX_VOICE_LINES]
        voice_lines.append(f"\n> Voice data truncated. See `{rel}/SOUL.md` for complete data.")
    lines.extend(voice_lines)

    # --- Operational Core ---
    op_lines = _format_operational_section(operations)
    if len(op_lines) > _MAX_OPERATIONAL_LINES:
        op_lines = op_lines[:_MAX_OPERATIONAL_LINES]
        op_lines.append(f"\n> Operational data truncated. See `{rel}/AGENT.md` for complete data.")
    lines.extend(op_lines)

    # --- Decision Engine ---
    dec_lines = _format_decision_section(decisions)
    if len(dec_lines) > _MAX_DECISION_LINES:
        dec_lines = dec_lines[:_MAX_DECISION_LINES]
        dec_lines.append(f"\n> Decision data truncated. See `{rel}/AGENT.md` for complete data.")
    lines.extend(dec_lines)

    # --- Top Insights ---
    ins_lines = _format_insights_section(insights)
    if len(ins_lines) > _MAX_INSIGHTS_LINES:
        ins_lines = ins_lines[:_MAX_INSIGHTS_LINES]
        ins_lines.append(f"\n> Insights truncated. See `{rel}/MEMORY.md` for complete data.")
    lines.extend(ins_lines)

    # --- Connection Interfaces ---
    conn_lines = _format_connections_section(connections)
    if len(conn_lines) > _MAX_CONNECTION_LINES:
        conn_lines = conn_lines[:_MAX_CONNECTION_LINES]
        conn_lines.append(f"\n> Connections truncated. See `{rel}/AGENT.md` for complete data.")
    lines.extend(conn_lines)

    # --- Identity Checkpoint ---
    lines.append("\n## IDENTITY CHECKPOINT\n")
    lines.append("Before every response, verify:")
    lines.append(f"- Am I using {name}'s vocabulary naturally?")
    lines.append(f"- Am I following {name}'s argumentation pattern?")
    lines.append("- Am I staying within my operational boundaries?")
    lines.append(f"- Would {name} actually say this?\n")

    # --- Deep Context ---
    lines.append("## Deep Context (for depth-seeking only)\n")
    lines.append("If you need more detail beyond what is embedded above:")
    lines.append(f"- Full agent definition: `{rel}/AGENT.md`")
    lines.append(f"- Full soul/voice: `{rel}/SOUL.md`")
    lines.append(f"- Full memory: `{rel}/MEMORY.md`")
    if dna_path:
        lines.append(f"- DNA layers: `{dna_path}`")
    lines.append("")

    # --- Footer ---
    lines.append(f"> {icon} {name} ({archetype}) -- {tagline}\n")

    # --- Hard cap ---
    if len(lines) > _TOTAL_HARD_CAP:
        lines = lines[:_TOTAL_HARD_CAP]
        lines.append(f"\n> [TRUNCATED] File exceeds {_TOTAL_HARD_CAP} lines. See source files for complete data.\n")

    return "\n".join(lines)


def _format_voice_section(voice_data: dict, name: str) -> list[str]:
    """Format the VOICE INJECTION BLOCK section."""
    lines: list[str] = []
    lines.append("## VOICE INJECTION BLOCK\n")

    if not voice_data:
        lines.append("<!-- [VOICE INJECTION BLOCK]: Pending MCE processing. Run /pipeline-mce to populate. -->\n")
        return lines

    # Identity
    identity = voice_data.get("identity", "")
    lines.append("### IDENTITY\n")
    if identity:
        lines.append(identity)
    else:
        lines.append("<!-- [IDENTITY]: Pending MCE processing. Run /pipeline-mce to populate. -->")
    lines.append("")

    # Beliefs
    beliefs = voice_data.get("beliefs", [])
    lines.append("### ACTIVE BELIEFS\n")
    if beliefs:
        for i, b in enumerate(beliefs, 1):
            lines.append(f"{i}. {b}")
    else:
        lines.append("<!-- [BELIEFS]: Pending MCE processing. Run /pipeline-mce to populate. -->")
    lines.append("")

    # Tone
    tone = voice_data.get("tone", [])
    lines.append("### TONE\n")
    if tone:
        for t in tone:
            lines.append(f"- {t}")
    else:
        lines.append("<!-- [TONE]: Pending MCE processing. Run /pipeline-mce to populate. -->")
    lines.append("")

    # Mandatory vocabulary
    vocab = voice_data.get("mandatory_vocabulary", [])
    lines.append("### MANDATORY VOCABULARY (USE THESE TERMS)\n")
    if vocab:
        for v in vocab:
            lines.append(f"- {v}")
    else:
        lines.append("<!-- [VOCABULARY]: Pending MCE processing. Run /pipeline-mce to populate. -->")
    lines.append("")

    # Forbidden vocabulary
    forbidden = voice_data.get("forbidden_vocabulary", [])
    lines.append("### FORBIDDEN VOCABULARY (NEVER USE THESE)\n")
    if forbidden:
        for f in forbidden:
            lines.append(f"- {f}")
    else:
        lines.append("<!-- [FORBIDDEN]: Pending MCE processing. Run /pipeline-mce to populate. -->")
    lines.append("")

    # Signature phrases
    phrases = voice_data.get("signature_phrases", [])
    lines.append("### SIGNATURE PHRASES\n")
    if phrases:
        for p in phrases:
            # Ensure quotes around phrases
            if not p.startswith('"'):
                lines.append(f'- "{p}"')
            else:
                lines.append(f"- {p}")
    else:
        lines.append("<!-- [PHRASES]: Pending MCE processing. Run /pipeline-mce to populate. -->")
    lines.append("")

    # Argumentation pattern
    pattern = voice_data.get("argumentation_pattern", [])
    lines.append("### ARGUMENTATION PATTERN\n")
    if pattern:
        for i, p in enumerate(pattern, 1):
            lines.append(f"{i}. {p}")
    else:
        lines.append("<!-- [ARGUMENTATION]: Pending MCE processing. Run /pipeline-mce to populate. -->")
    lines.append("")

    # Anti-patterns
    anti = voice_data.get("anti_patterns", [])
    lines.append("### ANTI-PATTERNS (WHAT I AM NOT)\n")
    if anti:
        for a in anti:
            lines.append(f"- {a}")
    else:
        lines.append("<!-- [ANTI-PATTERNS]: Pending MCE processing. Run /pipeline-mce to populate. -->")
    lines.append("")

    return lines


def _format_operational_section(operations: dict) -> list[str]:
    """Format the OPERATIONAL CORE section."""
    lines: list[str] = []
    lines.append("## OPERATIONAL CORE\n")

    if not operations:
        lines.append("<!-- [OPERATIONAL CORE]: Pending MCE processing. Run /pipeline-mce to populate. -->\n")
        return lines

    use_cases = operations.get("use_cases", [])
    lines.append("### When to Consult\n")
    if use_cases:
        for uc in use_cases:
            lines.append(f"- {uc}")
    else:
        lines.append("<!-- [USE CASES]: Pending MCE processing. Run /pipeline-mce to populate. -->")
    lines.append("")

    boundaries = operations.get("boundaries", [])
    lines.append("### When NOT to Consult\n")
    if boundaries:
        for b in boundaries:
            lines.append(f"- {b}")
    else:
        lines.append("<!-- [BOUNDARIES]: Pending MCE processing. Run /pipeline-mce to populate. -->")
    lines.append("")

    return lines


def _format_decision_section(decisions: list[dict]) -> list[str]:
    """Format the DECISION ENGINE section."""
    lines: list[str] = []
    lines.append("## DECISION ENGINE\n")

    if not decisions:
        lines.append("<!-- [DECISION ENGINE]: Pending MCE processing. Run /pipeline-mce to populate. -->\n")
        return lines

    for rule in decisions:
        situation = rule.get("situation", "")
        decision = rule.get("decision", "")
        source = rule.get("source", "")
        source_tag = f" [{source}]" if source else ""
        lines.append(f"- IF {situation} -> THEN {decision}{source_tag}")

    lines.append("")
    return lines


def _format_insights_section(insights: dict) -> list[str]:
    """Format the TOP INSIGHTS section."""
    lines: list[str] = []
    lines.append("## TOP INSIGHTS\n")

    if not insights:
        lines.append("<!-- [TOP INSIGHTS]: Pending MCE processing. Run /pipeline-mce to populate. -->\n")
        return lines

    insight_list = insights.get("insights", [])
    if insight_list:
        for i, ins in enumerate(insight_list, 1):
            lines.append(f"{i}. {ins}")
        lines.append("")

    patterns = insights.get("decision_patterns", [])
    if patterns:
        lines.append("### Decision Patterns\n")
        for p in patterns:
            situation = p.get("situation", "")
            decision = p.get("decision", "")
            if decision:
                lines.append(f"- **{situation}** -> {decision}")
            else:
                lines.append(f"- {situation}")
        lines.append("")

    if not insight_list and not patterns:
        lines.append("<!-- [TOP INSIGHTS]: Pending MCE processing. Run /pipeline-mce to populate. -->\n")

    return lines


def _format_connections_section(connections: list[dict]) -> list[str]:
    """Format the CONNECTION INTERFACES section."""
    lines: list[str] = []
    lines.append("## CONNECTION INTERFACES\n")

    if not connections:
        lines.append("<!-- [CONNECTIONS]: Pending MCE processing. Run /pipeline-mce to populate. -->\n")
        return lines

    lines.append("| Agent | Interaction |")
    lines.append("|-------|-------------|")
    for conn in connections:
        agent = conn.get("agent", "")
        interaction = conn.get("interaction_type", "reference")
        lines.append(f"| {agent} | {interaction} |")
    lines.append("")

    return lines


def _compute_source_hash(path: Path) -> str:
    """Compute SHA256 hash of a file. Returns empty string if file missing."""
    if not path.exists():
        return ""
    try:
        content = path.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# AGENT INFO EXTRACTION
# ---------------------------------------------------------------------------


def _extract_title_from_agent_md(text: str, slug: str) -> str:
    """Extract a title from AGENT.md content."""
    # Look for a heading like "# PERSON AGENT" or first ## heading
    # Skip decorator lines (===, ---, ```, empty, or purely symbolic)
    # Skip PARTE X headers and internal section headers
    skip_prefixes = (
        "## QUEM SOU", "## PARTE ", "## IDENTIDADE", "## MISS",
        "## METADADOS", "## DEPENDENCIES", "## DEPEND",
        "## 🛡", "## 🧬", "## 🗣", "## 📊", "## 💼",
        "## O QUE", "## COMO ", "## OBSESS", "## PARADOX",
        "## SISTEMA DE VOZ", "## REGRAS", "## PADR",
    )
    for line in text.split("\n"):
        stripped = line.strip()
        if any(stripped.startswith(p) for p in skip_prefixes):
            continue
        if stripped.startswith("## "):
            candidate = stripped.lstrip("# ").strip()
            if _is_valid_title(candidate):
                return candidate
        if stripped.startswith("# ") and not stripped.startswith("# ="):
            candidate = stripped.lstrip("# ").strip()
            if _is_valid_title(candidate):
                return candidate

    # Fallback 1: check YAML frontmatter for role field
    frontmatter_match = re.search(r"^role:\s*[\"']?(.+?)[\"']?\s*$", text, re.MULTILINE)
    if frontmatter_match:
        return frontmatter_match.group(1).strip()

    # Fallback 2: check for > **Tipo:** or > **Versao:** header block with title context
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("> **Tipo:**"):
            candidate = stripped.split("**Tipo:**")[1].strip()
            if candidate:
                return candidate

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
        dna_sources = dna_config.get("dna_sources", {})
        if not isinstance(dna_sources, dict):
            dna_sources = {}
        sources = dna_sources.get("primario", [])
        if not isinstance(sources, list):
            sources = []
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
        "compilation": {
            "format": "v2.0",
            "sections_embedded": 5,
            "generated_at": now,
            "source_hashes": {
                "agent_md": _compute_source_hash(agent_dir / "AGENT.md"),
                "soul_md": _compute_source_hash(agent_dir / "SOUL.md"),
                "memory_md": _compute_source_hash(agent_dir / "MEMORY.md"),
            },
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
    """Generate compiled .claude/commands/agents/{slug}.md content.

    Calls all 6 extractors and produces a self-contained persona file.
    Zero occurrences of 'Read AGENT.md' or 'Read SOUL.md' in output.
    """
    soul_path = agent_dir / "SOUL.md"
    agent_md_path = agent_dir / "AGENT.md"
    memory_path = agent_dir / "MEMORY.md"

    # Run all extractors
    voice_data = _extract_voice_block(soul_path)
    operations = _extract_operational_core(agent_md_path)
    decisions = _extract_decision_engine(agent_md_path, soul_path)
    insights = _extract_top_insights(memory_path)
    connections = _extract_connections(agent_md_path)

    return _format_compiled_command(
        slug=slug,
        nickname_data=nickname_data,
        title=title,
        agent_dir=agent_dir,
        category=category,
        voice_data=voice_data,
        operations=operations,
        decisions=decisions,
        insights=insights,
        connections=connections,
    )


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
        "generator": "activation_generator.py v2.0.0",
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
    dry_run: bool = False,
) -> dict[str, Any]:
    """Generate ACTIVATION.yaml and register agent in all IDEs.

    Args:
        slug: Kebab-case agent identifier (e.g. 'alex-hormozi', 'closer').
        category: One of 'external/experts', 'external/roles', 'business/people',
                  'business/roles', 'personal', 'system', or shorthand
                  'external', 'cargo', 'business'.
        force: If True, overwrite existing ACTIVATION.yaml.
        dry_run: If True, compile output but do not write any files.

    Returns:
        {"created": [files], "updated": [files], "errors": [], "dry_run_output": str | None}
    """
    result: dict[str, Any] = {"created": [], "updated": [], "errors": []}

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

    # Generate compiled command content (used for both dry_run and real write)
    claude_content = _generate_claude_command(slug, nickname_data, title, agent_dir, category)

    # --- Dry run: return content without writing ---
    if dry_run:
        result["dry_run_output"] = claude_content
        logger.info("[DRY RUN] Generated compiled command for '%s' (%d lines)", slug, claude_content.count("\n"))
        return result

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

    # Business people (may nest: business/collaborators/finance/diego-monet/)
    business_dir = AGENTS / "business"
    if business_dir.exists():
        for agent_md in sorted(business_dir.rglob("AGENT.md")):
            agent_dir = agent_md.parent
            if not agent_dir.name.startswith(("_", ".")):
                found.append((agent_dir.name, "business", agent_dir))

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


def batch_generate_all(
    *,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Generate activations for all agents that have AGENT.md.

    Args:
        force: If True, regenerate even if ACTIVATION.yaml exists.
        dry_run: If True, compile output but do not write any files.

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
        if activation_path.exists() and not force and not dry_run:
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

        result = generate_activation(slug, category, force=force, dry_run=dry_run)

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
    single.add_argument("--dry-run", action="store_true", help="Compile output without writing files")

    # Batch
    batch = sub.add_parser("batch", help="Generate activations for ALL agents")
    batch.add_argument("--force", action="store_true", help="Regenerate all, even existing")
    batch.add_argument("--dry-run", action="store_true", help="Compile output without writing files")

    # List
    sub.add_parser("list", help="List all discoverable agents")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.command == "generate":
        dry_run = getattr(args, "dry_run", False)
        result = generate_activation(args.slug, args.category, force=args.force, dry_run=dry_run)
        if dry_run and "dry_run_output" in result:
            print(result["dry_run_output"])
        else:
            _print_result(args.slug, result)
        if result.get("errors"):
            sys.exit(1)

    elif args.command == "batch":
        dry_run = getattr(args, "dry_run", False)
        summary = batch_generate_all(force=args.force, dry_run=dry_run)
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
