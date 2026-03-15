#!/usr/bin/env python3
"""
AGENT GENERATOR - Intelligence Layer v2.0
==========================================
Auto-creates agent files (AGENT.md + SOUL.md + MEMORY.md + DNA-CONFIG.yaml)
when agent_trigger.py decides CREATE and density >= 3.

Behavior:
    1. Takes a person slug and category (external/business/personal).
    2. Reads the person's DNA from knowledge/{bucket}/dna/persons/{slug}/.
    3. Reads the person's dossier from knowledge/{bucket}/dossiers/persons/.
    4. Reads MCE layers (L6-L8) if present (graceful degradation).
    5. Generates 4 files using templates from core/templates/agents/.
    6. Saves to agents/{category}/{slug}/.

Constraints:
    - Python 3, stdlib + PyYAML only.
    - Imports from core.paths.
    - Category determines destination: agents/{category}/{slug}/.
    - Never overwrites existing agents -- skips with warning.
    - Logs every file created.
    - BACKWARD COMPATIBLE: missing MCE files produce identical v1 output.

Version: 2.0.0
Date: 2026-03-10
Story: EPIC-2 Phase 2.3/2.4 (MCE Integration)
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

from core.paths import (  # noqa: E402
    AGENTS,
    KNOWLEDGE_BUSINESS,
    KNOWLEDGE_EXTERNAL,
    KNOWLEDGE_PERSONAL,
    LOGS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

_CATEGORY_MAP: dict[str, Path] = {
    "external": AGENTS / "external",
    "business": AGENTS / "business",
    "personal": AGENTS / "personal",
}

_BUCKET_MAP: dict[str, Path] = {
    "external": KNOWLEDGE_EXTERNAL,
    "business": KNOWLEDGE_BUSINESS,
    "personal": KNOWLEDGE_PERSONAL,
}

_DNA_LAYERS = (
    ("FILOSOFIAS", "filosofias", "L1: Filosofias"),
    ("MODELOS-MENTAIS", "modelos_mentais", "L2: Modelos Mentais"),
    ("HEURISTICAS", "heuristicas", "L3: Heuristicas"),
    ("FRAMEWORKS", "frameworks", "L4: Frameworks"),
    ("METODOLOGIAS", "metodologias", "L5: Metodologias"),
)

_MCE_LAYERS = (
    ("BEHAVIORAL-PATTERNS", "behavioral_patterns", "L6: Behavioral Patterns"),
    ("VALUES-HIERARCHY", "values_hierarchy", "L7: Values Hierarchy"),
    ("VOICE-DNA", "voice_dna", "L8: Voice DNA"),
)


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


def _extract_items(data: dict[str, Any], yaml_key: str) -> list[dict]:
    """Extract item list from DNA YAML, handling both old and new key formats.

    Old format: items stored under lowercase layer name (e.g. ``filosofias``).
    New format: items stored under ``itens`` key.
    """
    items = data.get(yaml_key) or data.get("itens", [])
    return items if isinstance(items, list) else []


# ---------------------------------------------------------------------------
# DNA LOADERS
# ---------------------------------------------------------------------------


def _load_dna_config(slug: str, category: str) -> dict[str, Any]:
    """Load CONFIG.yaml from the person's DNA directory."""
    bucket = "external" if category == "external" else category
    base = _BUCKET_MAP.get(bucket, KNOWLEDGE_EXTERNAL)
    return _read_yaml(base / "dna" / "persons" / slug / "CONFIG.yaml")


def _load_dna_layer_counts(slug: str, category: str) -> dict[str, int]:
    """Count elements per DNA layer."""
    bucket = "external" if category == "external" else category
    base = _BUCKET_MAP.get(bucket, KNOWLEDGE_EXTERNAL)
    dna_dir = base / "dna" / "persons" / slug

    counts: dict[str, int] = {}
    for filename, yaml_key, _label in _DNA_LAYERS:
        data = _read_yaml(dna_dir / f"{filename}.yaml")
        items = _extract_items(data, yaml_key)
        counts[filename] = len(items)

    return counts


def _load_dna_highlights(slug: str, category: str, max_per_layer: int = 3) -> dict[str, list[str]]:
    """Load a few highlight items per DNA layer for AGENT.md summary."""
    bucket = "external" if category == "external" else category
    base = _BUCKET_MAP.get(bucket, KNOWLEDGE_EXTERNAL)
    dna_dir = base / "dna" / "persons" / slug

    highlights: dict[str, list[str]] = {}
    for filename, yaml_key, _label in _DNA_LAYERS:
        data = _read_yaml(dna_dir / f"{filename}.yaml")
        items = _extract_items(data, yaml_key)
        if not items:
            highlights[filename] = []
            continue
        names = []
        for item in items[:max_per_layer]:
            name = item.get("nome", item.get("name", ""))
            if name:
                names.append(name)
        highlights[filename] = names

    return highlights


def _load_dossier_tldr(slug: str, category: str) -> str:
    """Extract TL;DR / first paragraph from the person's dossier."""
    bucket = "external" if category == "external" else category
    base = _BUCKET_MAP.get(bucket, KNOWLEDGE_EXTERNAL)
    slug_upper = slug.upper()
    dossier_path = base / "dossiers" / "persons" / f"DOSSIER-{slug_upper}.md"

    if not dossier_path.exists():
        dossier_path = base / "dossiers" / "persons" / f"DOSSIER-{slug}.md"

    text = _read_text(dossier_path)
    if not text:
        return ""

    lines = text.split("\n")
    capture = False
    tldr_lines: list[str] = []
    for line in lines:
        if line.strip().startswith("## TL;DR") or line.strip().startswith("## Identidade"):
            capture = True
            continue
        if capture and line.strip().startswith("## "):
            break
        if capture:
            tldr_lines.append(line)

    result = "\n".join(tldr_lines).strip()
    if not result:
        for line in lines:
            stripped = line.strip()
            if (
                stripped
                and not stripped.startswith("#")
                and not stripped.startswith(">")
                and not stripped.startswith("---")
            ):
                return stripped
    return result


# ---------------------------------------------------------------------------
# MCE LOADERS
# ---------------------------------------------------------------------------


def _get_dna_dir(slug: str, category: str) -> Path:
    """Return the DNA directory for a person."""
    bucket = "external" if category == "external" else category
    base = _BUCKET_MAP.get(bucket, KNOWLEDGE_EXTERNAL)
    return base / "dna" / "persons" / slug


def _load_mce_data(slug: str, category: str) -> dict[str, dict[str, Any]]:
    """Load all MCE layer YAMLs that exist, returning {filename: data}.

    Missing files are silently omitted -- callers check presence.
    """
    dna_dir = _get_dna_dir(slug, category)
    result: dict[str, dict[str, Any]] = {}
    for filename, _yaml_key, _label in _MCE_LAYERS:
        data = _read_yaml(dna_dir / f"{filename}.yaml")
        if data:
            result[filename] = data
    return result


def _has_mce(mce_data: dict[str, dict[str, Any]]) -> bool:
    """Return True if any MCE layer is present."""
    return len(mce_data) > 0


def _extract_behavioral_highlights(data: dict[str, Any], max_items: int = 3) -> list[str]:
    """Extract top behavioral pattern names from BEHAVIORAL-PATTERNS.yaml."""
    patterns = data.get("behavioral_patterns") or data.get("patterns") or []
    if not isinstance(patterns, list):
        return []
    names: list[str] = []
    for item in patterns[:max_items]:
        if isinstance(item, dict):
            name = item.get("pattern", item.get("nome", item.get("name", "")))
            if name:
                names.append(str(name))
        elif isinstance(item, str):
            names.append(item)
    return names


def _extract_values_highlights(data: dict[str, Any], max_items: int = 3) -> list[str]:
    """Extract top values from VALUES-HIERARCHY.yaml."""
    values = data.get("values_hierarchy") or data.get("values") or data.get("hierarchy") or []
    if not isinstance(values, list):
        return []
    names: list[str] = []
    for item in values[:max_items]:
        if isinstance(item, dict):
            name = item.get("value", item.get("nome", item.get("name", "")))
            if name:
                names.append(str(name))
        elif isinstance(item, str):
            names.append(item)
    return names


def _extract_voice_highlights(data: dict[str, Any]) -> dict[str, Any]:
    """Extract key voice DNA elements from VOICE-DNA.yaml."""
    result: dict[str, Any] = {}

    # Signature phrases
    phrases = data.get("signature_phrases") or data.get("frases_de_efeito") or []
    if isinstance(phrases, list):
        result["signature_phrases"] = [str(p) for p in phrases[:5]]

    # Tone profile
    tone = data.get("tone_profile") or data.get("tom") or {}
    if isinstance(tone, dict):
        result["tone_profile"] = tone

    # Forbidden words
    forbidden = data.get("forbidden_words") or data.get("palavras_proibidas") or []
    if isinstance(forbidden, list):
        result["forbidden_words"] = [str(w) for w in forbidden[:10]]

    # Immune system
    immune = data.get("immune_system") or data.get("sistema_imunologico") or {}
    if isinstance(immune, dict):
        result["immune_system"] = immune

    # Obsessions
    obsessions = data.get("obsessions") or data.get("obsessoes") or []
    if isinstance(obsessions, list):
        result["obsessions"] = [str(o) for o in obsessions[:5]]

    # Paradoxes
    paradoxes = data.get("paradoxes") or data.get("paradoxos") or []
    if isinstance(paradoxes, list):
        result["paradoxes"] = paradoxes[:3]

    return result


def _load_mce_layer_counts(mce_data: dict[str, dict[str, Any]]) -> dict[str, int]:
    """Count elements per MCE layer."""
    counts: dict[str, int] = {}
    for filename, _yaml_key, _label in _MCE_LAYERS:
        data = mce_data.get(filename, {})
        if filename == "BEHAVIORAL-PATTERNS":
            items = data.get("behavioral_patterns") or data.get("patterns") or []
        elif filename == "VALUES-HIERARCHY":
            items = (
                data.get("values_hierarchy") or data.get("values") or data.get("hierarchy") or []
            )
        elif filename == "VOICE-DNA":
            # Count total top-level keys as a proxy for richness
            items = [k for k in data if k not in ("version", "versao", "metadata", "metadados")]
        else:
            items = []
        counts[filename] = len(items) if isinstance(items, list) else 0
    return counts


# ---------------------------------------------------------------------------
# FILE GENERATORS
# ---------------------------------------------------------------------------


def _generate_agent_md(
    slug: str,
    category: str,
    config: dict[str, Any],
    layer_counts: dict[str, int],
    highlights: dict[str, list[str]],
    dossier_tldr: str,
    mce_data: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Generate AGENT.md content with key sections.

    When *mce_data* is provided and non-empty, PARTE 3B (MCE DNA) is appended
    after the DNA SUMMARY block.  Otherwise the output is identical to v1.
    """
    now = datetime.now(UTC).strftime("%Y-%m-%d")
    person_name = config.get("pessoa", slug.replace("-", " ").title())
    name_upper = person_name.upper()
    total_elements = sum(layer_counts.values())
    mce_data = mce_data or {}

    border_len = max(len(name_upper) + 8, 40)
    border = "=" * border_len
    pad = " " * ((border_len - len(name_upper)) // 2)

    sections = []

    sections.append(f"```\n{border}\n{pad}{name_upper}\n{pad}PERSON AGENT\n{border}\n```\n")
    sections.append(f"> **Version:** 1.0.0\n> **Type:** SOLO (PERSON)\n> **Category:** {category}")
    sections.append(f"> **Created:** {now}\n> **Generator:** agent_generator.py v2.0.0 (EPIC-2)")
    sections.append(f"> **DNA Source:** knowledge/external/dna/persons/{slug}/\n\n---\n")

    sections.append("## QUEM SOU\n")
    if dossier_tldr:
        sections.append(dossier_tldr)
        sections.append(
            f"\n^[SOURCE:knowledge/external/dossiers/persons/DOSSIER-{slug.upper()}.md:TL;DR]\n"
        )
    else:
        sintese = config.get("sintese", {})
        em_uma_frase = sintese.get("em_uma_frase", "")
        paragrafo = sintese.get("paragrafo", "")
        if em_uma_frase:
            sections.append(f"> {em_uma_frase}")
            sections.append(
                f"^[SOURCE:knowledge/external/dna/persons/{slug}/CONFIG.yaml:sintese]\n"
            )
        if paragrafo:
            sections.append(paragrafo.strip() + "\n")
        if not em_uma_frase and not paragrafo:
            sections.append(
                f"*Agente {person_name} - identidade a ser populada com dados do Pipeline.*\n"
            )
    sections.append("\n---\n")

    sections.append("## FORMACAO\n")
    fontes = config.get("metadados", {}).get("fontes_utilizadas", [])
    if fontes:
        sections.append("| Source ID | Titulo | Chunks |")
        sections.append("|-----------|--------|--------|")
        for f in fontes:
            sid = f.get("source_id", "?")
            title = f.get("source_title", "?")
            chunks = f.get("chunks_usados", 0)
            sections.append(f"| {sid} | {title} | {chunks} |")
        sections.append(
            f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/CONFIG.yaml:fontes_utilizadas]\n"
        )
    else:
        sections.append("*Fontes a serem registradas via Pipeline.*\n")
    sections.append("\n---\n")

    sections.append("## DNA SUMMARY\n")
    sections.append(f"**Total elementos:** {total_elements}\n")
    sections.append("| Camada | Elementos | Destaques |")
    sections.append("|--------|-----------|-----------|")
    for filename, _yaml_key, label in _DNA_LAYERS:
        count = layer_counts.get(filename, 0)
        hl = highlights.get(filename, [])
        hl_str = ", ".join(hl) if hl else "-"
        sections.append(f"| {label} | {count} | {hl_str} |")
    sections.append(
        f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/CONFIG.yaml:distribuicao_por_camada]\n"
    )
    sections.append("\n---\n")

    # --- PARTE 3B: MCE DNA (Behavioral + Identity) ---
    if _has_mce(mce_data):
        mce_counts = _load_mce_layer_counts(mce_data)
        sections.append("## MCE DNA (Behavioral + Identity)\n")
        sections.append("*[MCE-ENHANCED] Mind-Clone Enhancement layers detected.*\n")
        sections.append("| Camada | Elementos | Destaques |")
        sections.append("|--------|-----------|-----------|")
        for filename, _yaml_key, label in _MCE_LAYERS:
            data = mce_data.get(filename, {})
            count = mce_counts.get(filename, 0)
            if filename == "BEHAVIORAL-PATTERNS":
                hl = _extract_behavioral_highlights(data)
            elif filename == "VALUES-HIERARCHY":
                hl = _extract_values_highlights(data)
            elif filename == "VOICE-DNA":
                voice_hl = _extract_voice_highlights(data)
                phrases = voice_hl.get("signature_phrases", [])
                hl = [f'"{p}"' for p in phrases[:3]] if phrases else ["-"]
            else:
                hl = []
            hl_str = ", ".join(hl) if hl else "-"
            sections.append(f"| {label} | {count} | {hl_str} |")

        # Behavioral patterns detail
        bp_data = mce_data.get("BEHAVIORAL-PATTERNS", {})
        if bp_data:
            bp_highlights = _extract_behavioral_highlights(bp_data, max_items=5)
            if bp_highlights:
                sections.append("\n### Top Behavioral Patterns\n")
                for i, pat in enumerate(bp_highlights, 1):
                    sections.append(f"{i}. **{pat}**")
                sections.append(
                    f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/BEHAVIORAL-PATTERNS.yaml]\n"
                )

        # Values hierarchy detail
        vh_data = mce_data.get("VALUES-HIERARCHY", {})
        if vh_data:
            val_highlights = _extract_values_highlights(vh_data, max_items=5)
            if val_highlights:
                sections.append("\n### Top Values\n")
                for i, val in enumerate(val_highlights, 1):
                    sections.append(f"{i}. **{val}**")
                sections.append(
                    f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/VALUES-HIERARCHY.yaml]\n"
                )

        # Voice DNA snippet
        vd_data = mce_data.get("VOICE-DNA", {})
        if vd_data:
            voice_info = _extract_voice_highlights(vd_data)
            phrases = voice_info.get("signature_phrases", [])
            if phrases:
                sections.append("\n### Signature Phrases\n")
                for phrase in phrases[:5]:
                    sections.append(f'- "{phrase}"')
                sections.append(
                    f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml]\n"
                )

        sections.append("\n---\n")
    else:
        sections.append("## MCE DNA (Behavioral + Identity)\n")
        sections.append("*[MCE layers pendentes -- executar /pipeline-mce]*\n\n---\n")

    sections.append("## MEMORY\n")
    sections.append("*Stub - to be populated by Pipeline processing and agent interactions.*\n")
    sections.append("See `MEMORY.md` for structured experience tracking.\n\n---\n")

    sections.append("## SOURCE REFERENCES\n")
    sections.append(f"- DNA: `knowledge/external/dna/persons/{slug}/`")
    sections.append(f"- Dossier: `knowledge/external/dossiers/persons/DOSSIER-{slug.upper()}.md`")
    sections.append(f"- CONFIG: `knowledge/external/dna/persons/{slug}/CONFIG.yaml`")
    sections.append("- Insights: `artifacts/insights/`")
    if _has_mce(mce_data):
        sections.append(
            f"- MCE Behavioral: `knowledge/external/dna/persons/{slug}/BEHAVIORAL-PATTERNS.yaml`"
        )
        sections.append(
            f"- MCE Values: `knowledge/external/dna/persons/{slug}/VALUES-HIERARCHY.yaml`"
        )
        sections.append(f"- MCE Voice: `knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml`")
    sections.append("\n\n---\n")
    sections.append(f"*Auto-generated by `agent_generator.py` v2.0.0 on {now}*\n")
    sections.append("*Story: EPIC-2 Phase 2.3/2.4 (MCE Integration)*\n")

    return "\n".join(sections)


def _generate_soul_md(
    slug: str,
    category: str,
    config: dict[str, Any],
    mce_data: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Generate SOUL.md content from DNA config.

    When *mce_data* contains MCE YAML data, additional sections (COMO REAJO,
    O QUE PRIORIZO, MINHAS OBSESSOES, MINHAS CONTRADICOES, MINHA VOZ) are
    appended.  Otherwise output is identical to v1.
    """
    now = datetime.now(UTC).strftime("%Y-%m-%d")
    person_name = config.get("pessoa", slug.replace("-", " ").title())
    sintese = config.get("sintese", {})
    em_uma_frase = sintese.get("em_uma_frase", "")
    paragrafo = sintese.get("paragrafo", "")
    pergunta = sintese.get("pergunta_que_sempre_faz", "")
    ponto_cego = sintese.get("ponto_cego", "")
    mce_data = mce_data or {}

    parts = []
    parts.append(f"# SOUL: {person_name}\n")
    parts.append(f"> **Versao:** 1.0\n> **Nascido em:** {now}\n> **Ultima evolucao:** {now}")
    parts.append(f"> **Natureza:** SOLO\n> **DNA:** {person_name} (100%)\n\n---\n")

    parts.append("## IDENTITY CARD\n")
    parts.append("```")
    parts.append("=" * 64)
    parts.append(f"{'':>{(64 - len(person_name.upper())) // 2}}{person_name.upper()}")
    parts.append(
        f'{"":>{(64 - len(em_uma_frase or "Identidade em construcao") - 2) // 2}}"{em_uma_frase or "Identidade em construcao"}"'
    )
    parts.append("=" * 64)
    parts.append(f"\n  DNA COMPOSITION\n  {person_name:<30} ████████████████████  100%")
    parts.append(f'\n  FRASE QUE ME DEFINE\n  "{pergunta or em_uma_frase or "..."}"')
    parts.append("```\n\n---\n")

    parts.append("## QUEM SOU EU\n")
    if paragrafo:
        parts.append(paragrafo.strip())
        parts.append(
            f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/CONFIG.yaml:sintese:paragrafo]\n"
        )
    else:
        parts.append(f"*Identidade de {person_name} a ser construida com dados do Pipeline.*\n")
    parts.append("\n---\n")

    parts.append("## O QUE ACREDITO\n")
    parts.append("*Filosofias a serem populadas a partir de FILOSOFIAS.yaml do Pipeline.*\n")
    parts.append(f"^[SOURCE:knowledge/external/dna/persons/{slug}/FILOSOFIAS.yaml]\n\n---\n")

    parts.append("## COMO PENSO\n")
    parts.append(
        "*Modelos mentais a serem populados a partir de MODELOS-MENTAIS.yaml do Pipeline.*\n"
    )
    parts.append(f"^[SOURCE:knowledge/external/dna/persons/{slug}/MODELOS-MENTAIS.yaml]\n\n---\n")

    parts.append("## MINHAS REGRAS DE DECISAO\n")
    parts.append("*Heuristicas a serem populadas a partir de HEURISTICAS.yaml do Pipeline.*\n")
    parts.append(f"^[SOURCE:knowledge/external/dna/persons/{slug}/HEURISTICAS.yaml]\n\n---\n")

    parts.append("## COMO EVOLUI\n\n### Linha do Tempo da Minha Consciencia\n\n```")
    parts.append(f"{now}  | NASCIMENTO (v1.0)\n         | Auto-gerado por agent_generator.py")
    parts.append(f"         | DNA Source: knowledge/external/dna/persons/{slug}/\n         |")
    parts.append("   ?     | PROXIMO\n         | Enriquecimento via Pipeline + interacoes")
    parts.append("```\n\n---\n")

    parts.append("## O QUE AINDA NAO SEI\n")
    if ponto_cego:
        parts.append("### Limitacoes que Reconheco\n")
        parts.append(ponto_cego)
        parts.append(
            f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/CONFIG.yaml:sintese:ponto_cego]\n"
        )
    else:
        parts.append("*Limitacoes a serem identificadas com processamento adicional.*\n")
    # --- MCE-ENHANCED SECTIONS ---
    bp_data = mce_data.get("BEHAVIORAL-PATTERNS", {})
    vh_data = mce_data.get("VALUES-HIERARCHY", {})
    vd_data = mce_data.get("VOICE-DNA", {})

    if bp_data:
        parts.append("\n---\n")
        parts.append("## COMO REAJO\n")
        parts.append("*[MCE-ENHANCED] Behavioral Patterns*\n")
        bp_highlights = _extract_behavioral_highlights(bp_data, max_items=5)
        if bp_highlights:
            for pat in bp_highlights:
                parts.append(f"- **{pat}**")
        # Behavioral states
        states = bp_data.get("behavioral_states") or bp_data.get("estados") or {}
        if isinstance(states, dict):
            parts.append("\n### Estados Comportamentais\n")
            for state_name, state_info in list(states.items())[:5]:
                if isinstance(state_info, dict):
                    trigger = state_info.get("trigger", state_info.get("gatilho", ""))
                    behavior = state_info.get("behavior", state_info.get("comportamento", ""))
                    parts.append(f"- **{state_name}:** {trigger} -> {behavior}")
                else:
                    parts.append(f"- **{state_name}:** {state_info}")
        parts.append(
            f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/BEHAVIORAL-PATTERNS.yaml]\n"
        )

    if vh_data:
        parts.append("\n---\n")
        parts.append("## O QUE PRIORIZO\n")
        parts.append("*[MCE-ENHANCED] Values Hierarchy*\n")
        val_highlights = _extract_values_highlights(vh_data, max_items=7)
        if val_highlights:
            for i, val in enumerate(val_highlights, 1):
                parts.append(f"{i}. **{val}**")
        parts.append(f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/VALUES-HIERARCHY.yaml]\n")

    if vd_data:
        voice_info = _extract_voice_highlights(vd_data)

        # Obsessions
        obsessions = voice_info.get("obsessions", [])
        if obsessions:
            parts.append("\n---\n")
            parts.append("## MINHAS OBSESSOES\n")
            parts.append("*[MCE-ENHANCED] Core Obsessions*\n")
            for obs in obsessions:
                parts.append(f"- {obs}")
            parts.append(
                f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml:obsessions]\n"
            )

        # Paradoxes
        paradoxes = voice_info.get("paradoxes", [])
        if paradoxes:
            parts.append("\n---\n")
            parts.append("## MINHAS CONTRADICOES\n")
            parts.append("*[MCE-ENHANCED] Paradoxes*\n")
            for paradox in paradoxes:
                if isinstance(paradox, dict):
                    tension = paradox.get("tension", paradox.get("tensao", ""))
                    resolution = paradox.get("resolution", paradox.get("resolucao", ""))
                    parts.append(f"- **{tension}** -> {resolution}")
                else:
                    parts.append(f"- {paradox}")
            parts.append(
                f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml:paradoxes]\n"
            )

        # Voice DNA
        tone = voice_info.get("tone_profile", {})
        forbidden = voice_info.get("forbidden_words", [])
        immune = voice_info.get("immune_system", {})
        phrases = voice_info.get("signature_phrases", [])

        if tone or forbidden or immune or phrases:
            parts.append("\n---\n")
            parts.append("## MINHA VOZ\n")
            parts.append("*[MCE-ENHANCED] Voice DNA*\n")
            if tone:
                parts.append("### Tom\n")
                for key, val in tone.items():
                    parts.append(f"- **{key}:** {val}")
            if phrases:
                parts.append("\n### Frases Assinatura\n")
                for phrase in phrases:
                    parts.append(f'- "{phrase}"')
            if forbidden:
                parts.append("\n### Palavras Proibidas\n")
                parts.append(", ".join(f"`{w}`" for w in forbidden))
            if immune:
                parts.append("\n### Sistema Imunologico\n")
                for key, val in immune.items():
                    parts.append(f"- **{key}:** {val}")
            parts.append(f"\n^[SOURCE:knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml]\n")

    parts.append("\n---\n")
    mce_tag = " [MCE-ENHANCED]" if _has_mce(mce_data) else ""
    parts.append(f"*Auto-gerado por `agent_generator.py` v2.0.0 em {now}{mce_tag}*\n")
    parts.append("*Este documento cresce com cada insight processado.*\n")

    return "\n".join(parts)


def _generate_memory_md(slug, category, config):
    """Generate MEMORY.md stub."""
    now = datetime.now(UTC).strftime("%Y-%m-%d")
    person_name = config.get("pessoa", slug.replace("-", " ").title())
    fontes = config.get("metadados", {}).get("fontes_utilizadas", [])

    parts = []
    parts.append(f"# MEMORY: {person_name}\n")
    parts.append(f"> **Atualizado:** {now}\n> **Versao:** 1.0.0\n\n---\n")
    parts.append("## MATERIAIS PROCESSADOS\n")

    if fontes:
        parts.append("| Material | Tipo | Data Processamento |")
        parts.append("|----------|------|-------------------|")
        for f in fontes:
            title = f.get("source_title", "?")
            parts.append(f"| {title} | Pipeline | {now} |")
    else:
        parts.append("*Nenhum material processado ainda.*")

    parts.append("\n\n---\n\n## PADROES DE PENSAMENTO\n")
    parts.append("*A ser populado com processamento de materiais via Pipeline.*\n\n---\n")
    parts.append("## EXPRESSOES CARACTERISTICAS\n")

    frases = (
        config.get("padroes_comportamentais", {})
        .get("linguagem_caracteristica", {})
        .get("frases_de_efeito", [])
    )
    if frases:
        parts.append("| Expressao | Contexto de Uso | chunk_id | PATH_RAIZ |")
        parts.append("|-----------|-----------------|----------|-----------|")
        for frase in frases[:10]:
            parts.append(f'| "{frase}" | Geral | - | ^[CONFIG.yaml:frases_de_efeito] |')
    else:
        parts.append("*Nenhuma expressao identificada ainda.*")

    parts.append("\n\n---\n\n## INSIGHTS EXTRAIDOS\n")
    parts.append("*A ser populado com insights do Pipeline.*\n\n---\n")
    parts.append("## HISTORICO DE ATUALIZACOES\n")
    parts.append("| Data | Mudanca | Material Processado |")
    parts.append("|------|---------|---------------------|")
    parts.append(f"| {now} | Criacao inicial (auto-gerado) | agent_generator.py v1.0.0 |\n\n---\n")
    parts.append("*MEMORY.md v1.0.0 - Auto-gerado por `agent_generator.py`*\n")
    parts.append("*Story: S08 (EPIC-REORG-001)*\n")

    return "\n".join(parts)


def _generate_dna_config_yaml(
    slug: str,
    category: str,
    config: dict[str, Any],
    layer_counts: dict[str, int],
    mce_data: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Generate DNA-CONFIG.yaml for the agent.

    When *mce_data* is provided and non-empty, an ``mce_sources`` section is
    included pointing at the MCE YAML files.  Otherwise output is identical
    to v1.
    """
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    person_name = config.get("pessoa", slug.replace("-", " ").title())
    fontes = config.get("metadados", {}).get("fontes_utilizadas", [])
    mce_data = mce_data or {}
    total = sum(layer_counts.values())

    dna_config: dict[str, Any] = {
        "cargo": person_name,
        "versao": "1.0.0",
        "nivel": "PERSON",
        "natureza": "SOLO",
        "data_criacao": now,
        "ultima_atualizacao": now,
        "soul": {"path": "./SOUL.md", "versao": "1.0"},
        "memoria": {"path": "./MEMORY.md", "versao": "1.0.0"},
        "dna_sources": {"primario": []},
        "distribuicao": {},
        "total_elementos": total,
        "generator": "agent_generator.py v2.0.0 (EPIC-2)",
    }

    for f in fontes:
        entry = {
            "source_id": f.get("source_id", "?"),
            "source_title": f.get("source_title", "?"),
            "chunks_usados": f.get("chunks_usados", 0),
            "path": f"knowledge/external/dna/persons/{slug}/",
        }
        dna_config["dna_sources"]["primario"].append(entry)

    for filename, _yaml_key, _label in _DNA_LAYERS:
        key = filename.lower().replace("-", "_")
        dna_config["distribuicao"][key] = layer_counts.get(filename, 0)

    # MCE sources -- only emitted when at least one MCE layer exists
    if _has_mce(mce_data):
        mce_sources: dict[str, Any] = {}
        dna_base = f"knowledge/external/dna/persons/{slug}"
        for filename, _yaml_key, label in _MCE_LAYERS:
            key = filename.lower().replace("-", "_")
            if filename in mce_data:
                mce_sources[key] = {
                    "path": f"{dna_base}/{filename}.yaml",
                    "label": label,
                    "present": True,
                }
            else:
                mce_sources[key] = {
                    "path": f"{dna_base}/{filename}.yaml",
                    "label": label,
                    "present": False,
                }
        mce_counts = _load_mce_layer_counts(mce_data)
        dna_config["mce_sources"] = mce_sources
        for filename, _yaml_key, _label in _MCE_LAYERS:
            key = filename.lower().replace("-", "_")
            dna_config["distribuicao"][key] = mce_counts.get(filename, 0)

    header = (
        f"# DNA-CONFIG.yaml for {person_name}\n"
        f"# Auto-generated by agent_generator.py v2.0.0\n"
        f"# Story: EPIC-2 Phase 2.3/2.4 (MCE Integration)\n"
        f"# Date: {now}\n"
        f"# DNA Source: knowledge/external/dna/persons/{slug}/\n\n"
    )

    return header + yaml.dump(
        dna_config, default_flow_style=False, allow_unicode=True, sort_keys=False
    )


# ---------------------------------------------------------------------------
# CORE: generate_agent
# ---------------------------------------------------------------------------


def generate_agent(slug: str, category: str) -> dict[str, list[str]]:
    """Generate agent files from DNA + Dossier.

    Args:
        slug: Kebab-case identifier (e.g. 'alex-hormozi').
        category: Agent category ('external', 'business', 'personal').

    Returns:
        {"created": [list of file paths], "skipped": [...], "errors": []}
    """
    if category not in _CATEGORY_MAP:
        msg = f"Unknown category '{category}'. Valid: {list(_CATEGORY_MAP)}"
        raise ValueError(msg)

    agent_dir = _CATEGORY_MAP[category] / slug
    result: dict[str, list[str]] = {"created": [], "skipped": [], "errors": []}

    if agent_dir.exists() and any(agent_dir.iterdir()):
        existing = [f.name for f in agent_dir.iterdir() if f.is_file()]
        logger.warning(
            "Agent directory '%s' already exists with files: %s. Skipping.", agent_dir, existing
        )
        result["skipped"].append(str(agent_dir))
        _log_generation(slug, category, result)
        return result

    config = _load_dna_config(slug, category)
    layer_counts = _load_dna_layer_counts(slug, category)
    highlights = _load_dna_highlights(slug, category)
    dossier_tldr = _load_dossier_tldr(slug, category)
    mce_data = _load_mce_data(slug, category)
    total_elements = sum(layer_counts.values())

    if not config and total_elements == 0:
        error_msg = f"No DNA data found for '{slug}' in category '{category}'"
        logger.error(error_msg)
        result["errors"].append(error_msg)
        _log_generation(slug, category, result)
        return result

    files_to_create = {
        "AGENT.md": _generate_agent_md(
            slug,
            category,
            config,
            layer_counts,
            highlights,
            dossier_tldr,
            mce_data,
        ),
        "SOUL.md": _generate_soul_md(slug, category, config, mce_data),
        "MEMORY.md": _generate_memory_md(slug, category, config),
        "DNA-CONFIG.yaml": _generate_dna_config_yaml(
            slug,
            category,
            config,
            layer_counts,
            mce_data,
        ),
    }

    agent_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in files_to_create.items():
        filepath = agent_dir / filename
        try:
            _write_text(filepath, content)
            rel_path = str(filepath.relative_to(_ROOT))
            result["created"].append(rel_path)
            logger.info("[CREATED] %s", rel_path)
        except Exception as e:
            error_msg = f"Failed to write {filepath}: {e}"
            result["errors"].append(error_msg)
            logger.error(error_msg)

    _log_generation(slug, category, result)
    return result


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------


def _log_generation(slug, category, result):
    """Append a generation event to the agent creation log."""
    log_path = LOGS / "agent-creation.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "action": "agent_generate",
        "slug": slug,
        "category": category,
        "created": result["created"],
        "skipped": result["skipped"],
        "errors": result["errors"],
        "generator": "agent_generator.py v2.0.0",
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate agent files from DNA + Dossier.")
    parser.add_argument("slug", help="Kebab-case slug (e.g. 'alex-hormozi')")
    parser.add_argument(
        "--category",
        default="external",
        choices=["external", "business", "personal"],
        help="Agent category (default: external)",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        result = generate_agent(slug=args.slug, category=args.category)

        print(f"\n{'=' * 60}")
        print(f"  AGENT GENERATOR - Results for '{args.slug}'")
        print(f"{'=' * 60}")

        if result["created"]:
            print(f"\n  CREATED ({len(result['created'])}):")
            for f in result["created"]:
                print(f"    [+] {f}")

        if result["skipped"]:
            print(f"\n  SKIPPED ({len(result['skipped'])}):")
            for f in result["skipped"]:
                print(f"    [~] {f}")

        if result["errors"]:
            print(f"\n  ERRORS ({len(result['errors'])}):")
            for e in result["errors"]:
                print(f"    [!] {e}")

        total = len(result["created"])
        print(f"\n  Total files created: {total}")
        print(f"{'=' * 60}")

        if result["errors"]:
            sys.exit(1)

    except ValueError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
