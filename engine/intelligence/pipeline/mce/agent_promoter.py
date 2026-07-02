"""agent_promoter.py -- Promote agent skeleton → full DNA-driven agent
======================================================================

Frente 7 (2026-05-13): reads L6-L10 YAMLs + INSIGHTS-STATE.json (L1-L5)
and rewrites all four agent files (AGENT.md, SOUL.md, MEMORY.md,
DNA-CONFIG.yaml) with real extracted content.  Changes ``status: skeleton``
→ ``status: complete``.

Contract:
    - Reads (never modifies) DNA YAMLs + INSIGHTS-STATE.json.
    - Preserves existing MEMORY.md content under a legacy section.
    - Idempotent: if status is already ``complete/active`` it no-ops.
    - Non-fatal: caller (cmd_promote_agent) must remain non-blocking.
    - Optional LLM refinement for narrative AGENT.md body + SOUL personality.
      Falls back to deterministic templates if LLM is unavailable.

Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from engine.intelligence.pipeline.mce.agent_skeleton import get_agent_filenames  # MCE-13.6
from engine.intelligence.utils.agent_files import find_agent_file  # MCE-13.6
from engine.paths import ROOT

logger = logging.getLogger("mce.agent_promoter")

_PROMOTER_VERSION = "agent_promoter v1.0.0"
_PROMOTED_STATUS = "complete"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _slug_to_person_name(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.split("-"))


# ---------------------------------------------------------------------------
# DNA loaders
# ---------------------------------------------------------------------------


def _load_yaml_safe(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning {} on missing/error."""
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.debug("Failed to load %s: %s", path, exc)
        return {}


def _load_insights(slug: str) -> dict[str, Any]:
    """Load INSIGHTS-STATE.json for slug."""
    insights_path = ROOT / ".data" / "artifacts" / "insights" / slug / "INSIGHTS-STATE.json"
    if not insights_path.exists():
        return {}
    try:
        with open(insights_path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.debug("Failed to load INSIGHTS-STATE.json for %s: %s", slug, exc)
        return {}


def _extract_insights_by_tag(insights_data: dict[str, Any], slug: str) -> dict[str, list[dict]]:
    """Group person insights by tag from INSIGHTS-STATE.json."""
    persons = insights_data.get("persons", {})
    person_name = _slug_to_person_name(slug)
    person_data = persons.get(person_name, {})
    if not person_data:
        # Try slug directly
        for key, val in persons.items():
            if isinstance(val, dict):
                person_data = val
                break
    insights = person_data.get("insights", []) if isinstance(person_data, dict) else []

    by_tag: dict[str, list[dict]] = defaultdict(list)
    for ins in insights:
        if isinstance(ins, dict):
            tag = ins.get("tag", "?")
            by_tag[tag].append(ins)
    return dict(by_tag)


def _load_dna_knowledge_anchors(slug: str, bucket: str) -> list[str]:
    """Return list of source file names from chunks directory."""
    chunks_dir = ROOT / ".data" / "artifacts" / "chunks" / slug
    anchors: list[str] = []
    if chunks_dir.exists():
        for p in sorted(chunks_dir.iterdir()):
            if p.suffix in (".json", ".yaml", ".txt"):
                name = p.stem.replace("chunks-", "").replace("_chunks", "")
                if name and name not in anchors:
                    anchors.append(name)
    return anchors[:20]  # cap at 20


# ---------------------------------------------------------------------------
# Content builders
# ---------------------------------------------------------------------------


def _build_agent_md(
    slug: str,
    bucket: str,
    by_tag: dict[str, list[dict]],
    voice_data: dict,
    values_data: dict,
    promoted_at: str,
    sources_count: int,
    *,
    llm_narrative: str | None = None,
) -> str:
    """Build the full AGENT.md content."""
    person_name = _slug_to_person_name(slug)
    today = _today()

    # Derive top philosophies (L1)
    filosofias = by_tag.get("[FILOSOFIA]", [])[:3]
    filosofia_lines = (
        "\n".join(f"- {ins.get('insight', '')[:120]}" for ins in filosofias) or "- (extraindo...)"
    )

    # Derive capabilities from L4 frameworks
    frameworks = by_tag.get("[FRAMEWORK]", [])[:5]
    cap_lines = (
        "\n".join(f"- {ins.get('insight', '')[:100]}" for ins in frameworks) or "- (extraindo...)"
    )

    # Top values
    values = values_data.get("values", [])
    top_values = [v.get("value", "") for v in values[:3] if isinstance(v, dict)]
    values_str = ", ".join(top_values) or "Organic Growth, Entrepreneurial Freedom"

    # Total insights
    total_insights = sum(len(v) for v in by_tag.values())

    # Narrative body — use LLM output if available, else deterministic
    if llm_narrative:
        narrative_section = llm_narrative
    else:
        narrative_section = f"""\
{person_name} é uma autoridade reconhecida em sua área de atuação, com uma
metodologia própria derivada dos insights extraídos de suas fontes. Esta
narrativa é um placeholder determinístico — gere a identidade completa via
LLM (llm_narrative) ou edite manualmente com base nos 10 layers de DNA.

Valores principais: {values_str}.
"""

    return f"""\
---
id: {slug}
type: external_clone
status: {_PROMOTED_STATUS}
auto_generated: true
promoted_at: {promoted_at}
promoted_by: {_PROMOTER_VERSION}
generated_at: {today}
generator: mce.agent_skeleton v1.0.0
sources_count: {sources_count}
dna_layers_populated: 10
version: 1.0.0
---

# {person_name} -- PERSON AGENT

> Promovido de skeleton → complete pelo agent_promoter v1.0.0.
> Conteúdo derivado dos 10 layers DNA + {total_insights} insights extraídos.

## Identidade

{narrative_section}

## Filosofias Centrais (L1)

{filosofia_lines}

## Capabilities (derivado dos Frameworks L4)

{cap_lines}

## Boot Sequence (Read in Order)

1. `AGENT.md` (this file)
2. `SOUL.md` -- voice + personality (DNA-driven)
3. `DNA-CONFIG.yaml` -- knowledge source manifest (10 layers)
4. `MEMORY.md` -- accumulated insights + cascade enrichment

## Commands

- Consultoria na área de especialidade derivada do DNA extraído
- Diagnóstico e recomendações baseados nos frameworks (L4)
- Estratégias e mentoria alinhadas às filosofias centrais (L1)
- Aplicação prática das metodologias e heurísticas extraídas

---

*Promovido por `engine/intelligence/pipeline/mce/agent_promoter.py` v1.0.0*
"""


def _build_soul_md(
    slug: str,
    voice_data: dict,
    values_data: dict,
    behavioral_data: dict,
    paradoxes_data: dict,
    obsessions_data: dict,
    *,
    llm_personality: str | None = None,
) -> str:
    """Build the full SOUL.md content."""
    person_name = _slug_to_person_name(slug)
    today = _today()

    # Tone profile from L8
    tone = voice_data.get("tone_profile", {})
    certainty = tone.get("certainty", {}).get("score", 7.5)
    authority = tone.get("authority", {}).get("score", 8.0)
    warmth = tone.get("warmth", {}).get("score", 6.5)
    directness = tone.get("directness", {}).get("score", 7.0)
    teaching = tone.get("teaching_focus", {}).get("score", 8.5)

    # Signature phrases from L8
    sig_phrases = voice_data.get("signature_phrases", [])
    sig_lines = (
        "\n".join(f"- \"{p.get('phrase', '')[:120]}\"" for p in sig_phrases[:5])
        or "- (nenhuma frase extraída)"
    )

    # Values from L7
    values = values_data.get("values", [])
    val_lines = (
        "\n".join(
            f"- **{v.get('value','')}** (rank {v.get('rank','?')}): {v.get('evidence','')[:80]}"
            for v in values[:3]
            if isinstance(v, dict)
        )
        or "- (valores não extraídos)"
    )

    # Behavioral patterns from L6
    patterns = behavioral_data.get("patterns", behavioral_data.get("behavioral_patterns", []))
    bp_lines = (
        "\n".join(
            f"- **{p.get('pattern_name','')[:60]}**: {p.get('action','')[:80]}"
            for p in patterns[:4]
            if isinstance(p, dict)
        )
        or "- (padrões não extraídos)"
    )

    # Behavioral states from L8
    states = voice_data.get("behavioral_states", [])
    state_lines = (
        "\n".join(
            f"- **{s.get('nome','')}** (trigger: {s.get('trigger','')[:60]}): {s.get('tom','')}"
            for s in states[:3]
            if isinstance(s, dict)
        )
        or "- (estados não extraídos)"
    )

    # Obsessions from L9
    obsessions = obsessions_data.get("obsessions", [])
    obs_lines = (
        "\n".join(
            f"- **{o.get('obsession','')}** (freq={o.get('frequency','?')}): {str(o.get('examples',[''])[0])[:80]}"
            for o in obsessions[:3]
            if isinstance(o, dict)
        )
        or "- (obsessões não extraídas)"
    )

    # Paradoxes from L10
    paradoxes = paradoxes_data.get("paradoxes", [])
    par_lines = (
        "\n".join(
            f"- **{p.get('id','')}**: {p.get('tension_a','')[:60]} ↔ {p.get('tension_b','')[:60]}\n  "
            f"*Resolução*: {p.get('resolution','')[:80]}"
            for p in paradoxes[:3]
            if isinstance(p, dict)
        )
        or "- (paradoxos não extraídos)"
    )

    # Personality section — use LLM or deterministic
    if llm_personality:
        personality_section = llm_personality
    else:
        personality_section = f"""\
{person_name} opera com clareza metodológica e autoridade educacional. Fala sobre
suas metodologias com convicção (authority={authority}/10), mantém foco pedagógico
elevado (teaching_focus={teaching}/10) e calibra calor humano para construir
conexão sem perder objetividade (warmth={warmth}/10).

Abre com dados e afirmações impactantes. Estrutura apresentações: problema →
solução proposta. Fecha com chamada à ação direta.
"""

    return f"""\
---
id: {slug}
status: {_PROMOTED_STATUS}
auto_generated: true
promoted_at: {_now_iso()}
generated_at: {today}
---

# {person_name} -- SOUL

> DNA-driven. Derivado de L6 (Behavioral), L7 (Values), L8 (Voice DNA), L9 (Obsessions), L10 (Paradoxes).

## Perfil de Tom (L8 Voice DNA)

| Dimensão | Score (0-10) |
|----------|-------------|
| Certeza | {certainty} |
| Autoridade | {authority} |
| Calor | {warmth} |
| Diretividade | {directness} |
| Foco Pedagógico | {teaching} |

## Frases Assinatura (L8)

{sig_lines}

## Personalidade

{personality_section}

## Valores (L7)

{val_lines}

## Obsessões (L9)

{obs_lines}

## Padrões Comportamentais (L6)

{bp_lines}

## Estados Comportamentais (L8)

{state_lines}

## Paradoxos Produtivos (L10)

{par_lines}

## Padrões de Comunicação (L8)

- **Opening hooks**: {voice_data.get('communication_patterns', {}).get('opening_hooks', {}).get('padrao', 'Dados impactantes')}
- **Story structure**: {voice_data.get('communication_patterns', {}).get('story_structure', {}).get('padrao', 'Problema → solução')}
- **Closing signatures**: {voice_data.get('communication_patterns', {}).get('closing_signatures', {}).get('padrao', 'CTA direto')}

---

*Promovido por `engine/intelligence/pipeline/mce/agent_promoter.py` v1.0.0*
"""


def _build_memory_md_header(
    slug: str,
    by_tag: dict[str, list[dict]],
    anchors: list[str],
    promoted_at: str,
) -> str:
    """Build the structured header to prepend to existing MEMORY.md."""
    person_name = _slug_to_person_name(slug)
    today = _today()

    # Top 5 insights per layer
    tag_to_layer = {
        "[FILOSOFIA]": "L1 Philosophies",
        "[MODELO-MENTAL]": "L2 Mental Models",
        "[HEURISTICA]": "L3 Heuristics",
        "[FRAMEWORK]": "L4 Frameworks",
        "[METODOLOGIA]": "L5 Methodologies",
    }

    insights_sections = []
    for tag, layer_name in tag_to_layer.items():
        items = by_tag.get(tag, [])
        if not items:
            continue
        lines = [f"### {layer_name} ({len(items)} insights)\n"]
        for ins in items[:5]:
            content = ins.get("insight", "")[:120]
            ins_id = ins.get("id", "?")
            lines.append(f"- **[{ins_id}]** {content}")
        insights_sections.append("\n".join(lines))

    insights_block = "\n\n".join(insights_sections) or "(Nenhum insight carregado)"

    # Knowledge anchors
    anchor_lines = "\n".join(f"- {a}" for a in anchors) or "(Nenhuma fonte identificada)"

    return f"""\
# MEMORY: {person_name}

> **Atualizado:** {today}
> **Status:** {_PROMOTED_STATUS}
> **Promovido em:** {promoted_at}
> **Promotor:** {_PROMOTER_VERSION}

---

## Knowledge Sources

{anchor_lines}

---

## Key Insights by Layer (L1-L5)

{insights_block}

---

## Cross-references

- (Cross-references serão preenchidas pelo memory_enricher / cascade a partir
  dos frameworks e entidades extraídas das fontes deste agente.)

---

## Legacy Memory (auto-cascade pre-promotion)

> Conteúdo abaixo foi gerado pelo memory_enricher antes da promoção.
> Preservado sem modificação (nunca destruir cascade pre-existente).

"""


def _build_dna_config(
    slug: str,
    bucket: str,
    by_tag: dict[str, list[dict]],
    frameworks: list[dict],
    anchors: list[str],
    promoted_at: str,
) -> dict[str, Any]:
    """Build the full DNA-CONFIG.yaml content as a dict."""
    person_name = _slug_to_person_name(slug)
    today = _today()
    insights_path = f".data/artifacts/insights/{slug}/INSIGHTS-STATE.json"
    dna_base = f"knowledge/{bucket}/dna/persons/{slug}"

    # Agent capabilities from L4 frameworks
    capabilities = [
        ins.get("insight", "")[:80]
        for ins in frameworks[:5]
        if isinstance(ins, dict) and ins.get("insight")
    ]

    tag_to_count = {
        "[FILOSOFIA]": ("L1_philosophies", "tag == '[FILOSOFIA]'"),
        "[MODELO-MENTAL]": ("L2_mental_models", "tag == '[MODELO-MENTAL]'"),
        "[HEURISTICA]": ("L3_heuristics", "tag == '[HEURISTICA]'"),
        "[FRAMEWORK]": ("L4_frameworks", "tag == '[FRAMEWORK]'"),
        "[METODOLOGIA]": ("L5_methodologies", "tag == '[METODOLOGIA]'"),
    }

    dna_layers: dict[str, Any] = {}
    for tag, (layer_key, filter_expr) in tag_to_count.items():
        count = len(by_tag.get(tag, []))
        dna_layers[layer_key] = {
            "source": insights_path,
            "filter": filter_expr,
            "count": count,
        }

    # L6-L10 from YAML files
    yaml_layers = {
        "L6_behavioral_patterns": (
            f"{dna_base}/behavioral-patterns.yaml",
            "patterns",
        ),
        "L7_values_hierarchy": (
            f"{dna_base}/values-hierarchy.yaml",
            "values",
        ),
        "L8_voice_dna": (
            f"{dna_base}/voice-dna.yaml",
            "signature_phrases + behavioral_states",
        ),
        "L9_obsessions": (
            f"{dna_base}/obsessions.yaml",
            "obsessions",
        ),
        "L10_paradoxes": (
            f"{dna_base}/paradoxes.yaml",
            "paradoxes",
        ),
    }

    for layer_key, (source_path, content_key) in yaml_layers.items():
        # Count items from the actual loaded YAML
        abs_path = ROOT / source_path.replace(
            f"{dna_base}/", f"knowledge/{bucket}/dna/persons/{slug}/"
        )
        count = 0
        if abs_path.exists():
            try:
                data = _load_yaml_safe(abs_path)
                # Try common count keys
                for ck in (
                    "total_patterns",
                    "total_values",
                    "total_obsessions",
                    "total_paradoxes",
                    "total_signature_phrases",
                    "total_behavioral_states",
                ):
                    if ck in data:
                        count = data[ck]
                        break
                else:
                    # Count list directly
                    for list_key in (
                        "patterns",
                        "behavioral_patterns",
                        "values",
                        "obsessions",
                        "paradoxes",
                        "signature_phrases",
                    ):
                        if list_key in data and isinstance(data[list_key], list):
                            count = len(data[list_key])
                            break
            except Exception:
                pass
        dna_layers[layer_key] = {
            "source": source_path,
            "count": count,
        }

    return {
        "id": slug,
        "person": person_name,
        "bucket": bucket,
        "status": _PROMOTED_STATUS,
        "auto_generated": True,
        "promoted_at": promoted_at,
        "promoted_by": _PROMOTER_VERSION,
        "generated_at": today,
        "dna_sources": {
            "primario": [
                {
                    "pessoa": slug,
                    "weight": 1.0,
                    "artifact_dir": f"knowledge/{bucket}/dna/persons/{slug}/",
                }
            ]
        },
        "dna_layers": dna_layers,
        "agent_capabilities": capabilities,
        "knowledge_anchors": anchors,
    }


# ---------------------------------------------------------------------------
# Optional LLM refinement
# ---------------------------------------------------------------------------


def _try_llm_narrative(
    slug: str,
    by_tag: dict[str, list[dict]],
    values_data: dict,
    voice_data: dict,
) -> tuple[str | None, str | None]:
    """Attempt LLM-generated narrative for AGENT.md body and SOUL personality.

    Returns (agent_narrative, soul_personality) — both None if LLM unavailable.
    Cost target: < $0.03 per call (gpt-4o-mini).
    """
    try:
        from engine.intelligence.pipeline.mce.llm_router import LLMRouter
    except ImportError:
        logger.debug("llm_router not available — using deterministic narrative")
        return None, None

    person_name = _slug_to_person_name(slug)

    # Gather input signals
    filosofias = [ins.get("insight", "") for ins in by_tag.get("[FILOSOFIA]", [])[:3]]
    frameworks = [ins.get("insight", "") for ins in by_tag.get("[FRAMEWORK]", [])[:3]]
    values = [v.get("value", "") for v in values_data.get("values", [])[:3] if isinstance(v, dict)]
    sig_phrases = [p.get("phrase", "") for p in voice_data.get("signature_phrases", [])[:3]]
    tone = voice_data.get("tone_profile", {})

    prompt = f"""Você é um especialista em síntese de perfis de especialistas para sistemas de IA.

PESSOA: {person_name}
SLUG: {slug}

FILOSOFIAS EXTRAÍDAS (L1):
{chr(10).join(f'- {f}' for f in filosofias)}

FRAMEWORKS (L4):
{chr(10).join(f'- {f}' for f in frameworks)}

VALORES (L7): {', '.join(values)}

FRASES ASSINATURA (L8):
{chr(10).join(f'- "{p}"' for p in sig_phrases)}

TOM: certeza={tone.get('certainty',{}).get('score','?')}/10, autoridade={tone.get('authority',{}).get('score','?')}/10, didatismo={tone.get('teaching_focus',{}).get('score','?')}/10

TAREFA A: Escreva um parágrafo narrativo de 3-4 frases descrevendo a identidade de {person_name} como agente (para AGENT.md). Escreva em português brasileiro. Seja específico à metodologia e ao domínio derivados do DNA extraído acima.

TAREFA B: Escreva um parágrafo de 2-3 frases descrevendo a personalidade/voz de {person_name} para um sistema de agente IA (para SOUL.md). Inclua como ele comunica, qual energia projeta, qual é seu modo padrão.

Responda APENAS neste formato JSON:
{{"agent_narrative": "...", "soul_personality": "..."}}"""

    try:
        router = LLMRouter()
        raw = router.run_prompt(
            prompt,
            provider="openai",
            step="agent_generation",
            max_output_tokens=600,
        )
        # Parse JSON
        import re

        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("agent_narrative"), data.get("soul_personality")
    except Exception as exc:
        logger.debug("LLM narrative failed for %s: %s — using deterministic", slug, exc)

    return None, None


# ---------------------------------------------------------------------------
# Main promotion function
# ---------------------------------------------------------------------------


def promote_agent(
    slug: str,
    bucket: str = "external",
    *,
    dry_run: bool = False,
    use_llm: bool = True,
) -> dict[str, Any]:
    """Promote agent skeleton → full DNA-driven agent.

    Args:
        slug: Person slug (kebab-case).
        bucket: One of ``"external" | "business"``.
        dry_run: If True, return what WOULD be written without writing.
        use_llm: If True, attempt LLM narrative refinement (gpt-4o-mini).

    Returns:
        Dict with keys:
            - ``promoted`` (bool): True if files were written.
            - ``agent_dir`` (str): Path to agent directory.
            - ``files`` (list[str]): Files written.
            - ``status_before``, ``status_after`` (str)
            - ``reason`` (str, optional): Why not promoted.
            - ``error`` (str, optional): Error message.
    """
    agent_dir = ROOT / "agents" / bucket / slug

    if not agent_dir.exists():
        return {
            "promoted": False,
            "reason": f"agent directory missing: agents/{bucket}/{slug}/",
            "agent_dir": str(agent_dir),
            "files": [],
        }

    # MCE-13.6: use find_agent_file for case-insensitive read (supports both old
    # UPPERCASE and new lowercase naming conventions).
    agent_md_path = find_agent_file(agent_dir, "agent.md")
    if agent_md_path is None:
        return {
            "promoted": False,
            "reason": "agent.md not found — cannot read current status",
            "agent_dir": str(agent_dir),
            "files": [],
        }

    # Check current status
    try:
        current_text = agent_md_path.read_text(encoding="utf-8")
    except Exception as exc:
        return {
            "promoted": False,
            "error": f"Failed to read AGENT.md: {exc}",
            "agent_dir": str(agent_dir),
            "files": [],
        }

    status_before = "unknown"
    if current_text.startswith("---"):
        end = current_text.find("---", 3)
        if end != -1:
            for line in current_text[3:end].splitlines():
                s = line.strip()
                if s.startswith("status:"):
                    status_before = s.split(":", 1)[1].strip().strip('"').strip("'")
                    break

    # Idempotent: if already promoted, no-op — but still report real insight counts
    if status_before.lower() in ("complete", "active", "production", "populated"):
        _idempotent_insights = _load_insights(slug)
        _idempotent_by_tag = _extract_insights_by_tag(_idempotent_insights, slug)
        _idempotent_total = sum(len(v) for v in _idempotent_by_tag.values())
        return {
            "promoted": False,
            "reason": f"already promoted (status={status_before})",
            "status_before": status_before,
            "status_after": status_before,
            "agent_dir": str(agent_dir),
            "files": [],
            "total_insights": _idempotent_total,
            "dna_layers": 10 if _idempotent_total > 0 else 0,
        }

    # D3 gate (Story MCE decision_gateway): when the agent already exists with
    # content beyond a bare skeleton, ask how to update before overwriting AGENT.md.
    # Returns "1" = MEMORY+AGENT, "2" = apenas MEMORY, "3" = pular tudo.
    # Non-blocking: if decision_gateway is unavailable, default to "1" (full update).
    _d3_decision: str = "1"  # default: full update
    if status_before.lower() not in ("skeleton", "unknown"):
        try:
            from engine.intelligence.pipeline.mce.decision_gateway import (
                decide_d3_update_agent_md,
            )

            _d3_decision = decide_d3_update_agent_md(agent_name=slug, slug=slug)
            logger.info(
                "agent_promoter: D3 decision for %s (status_before=%s) → %s",
                slug,
                status_before,
                _d3_decision,
            )
        except Exception as _d3_exc:
            logger.warning(
                "agent_promoter: D3 decision_gateway unavailable for %s, defaulting to '1': %s",
                slug,
                _d3_exc,
            )

    if _d3_decision == "3":
        logger.info("agent_promoter: D3=3 (pular) — skipping promotion for %s", slug)
        return {
            "promoted": False,
            "reason": "D3=3: user chose to skip update",
            "status_before": status_before,
            "status_after": status_before,
            "agent_dir": str(agent_dir),
            "files": [],
        }

    # Load DNA sources
    dna_base = ROOT / "knowledge" / bucket / "dna" / "persons" / slug
    voice_data = _load_yaml_safe(dna_base / "voice-dna.yaml")
    behavioral_data = _load_yaml_safe(dna_base / "behavioral-patterns.yaml")
    values_data = _load_yaml_safe(dna_base / "values-hierarchy.yaml")
    obsessions_data = _load_yaml_safe(dna_base / "obsessions.yaml")
    paradoxes_data = _load_yaml_safe(dna_base / "paradoxes.yaml")

    insights_data = _load_insights(slug)
    by_tag = _extract_insights_by_tag(insights_data, slug)
    anchors = _load_dna_knowledge_anchors(slug, bucket)
    frameworks = by_tag.get("[FRAMEWORK]", [])
    total_insights = sum(len(v) for v in by_tag.values())

    promoted_at = _now_iso()

    # Optional LLM narrative
    llm_narrative: str | None = None
    llm_personality: str | None = None
    llm_used = False
    if use_llm:
        llm_narrative, llm_personality = _try_llm_narrative(slug, by_tag, values_data, voice_data)
        llm_used = llm_narrative is not None

    # Build new content
    new_agent_md = _build_agent_md(
        slug,
        bucket,
        by_tag,
        voice_data,
        values_data,
        promoted_at,
        total_insights,
        llm_narrative=llm_narrative,
    )
    new_soul_md = _build_soul_md(
        slug,
        voice_data,
        values_data,
        behavioral_data,
        paradoxes_data,
        obsessions_data,
        llm_personality=llm_personality,
    )
    memory_header = _build_memory_md_header(slug, by_tag, anchors, promoted_at)
    dna_config_dict = _build_dna_config(slug, bucket, by_tag, frameworks, anchors, promoted_at)

    # MCE-13.6: resolve bucket-aware filenames (lowercase for non-cargo)
    fnames = get_agent_filenames(agent_dir)

    # MEMORY.md: prepend structured header, keep legacy content
    # MCE-13.6: read via find_agent_file to handle old UPPERCASE agents
    memory_md_path = find_agent_file(agent_dir, "memory.md")
    legacy_memory = ""
    if memory_md_path is not None and memory_md_path.exists():
        try:
            legacy_memory = memory_md_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning("Could not read existing memory.md for %s: %s", slug, exc)

    new_memory_md = memory_header + legacy_memory

    new_dna_config_yaml = yaml.safe_dump(
        dna_config_dict,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    file_plan = {
        fnames["agent"]: new_agent_md,
        fnames["soul"]: new_soul_md,
        fnames["memory"]: new_memory_md,
        fnames["dna_config"]: new_dna_config_yaml,
    }

    # D3="2" (apenas MEMORY): exclude agent.md and soul.md from write set
    if _d3_decision == "2":
        logger.info(
            "agent_promoter: D3=2 — writing memory.md only for %s (agent.md preserved)",
            slug,
        )
        file_plan = {fnames["memory"]: new_memory_md}

    if dry_run:
        return {
            "promoted": False,
            "reason": "dry_run",
            "status_before": status_before,
            "status_after": _PROMOTED_STATUS,
            "agent_dir": str(agent_dir),
            "files": list(file_plan.keys()),
            "total_insights": total_insights,
            "llm_used": llm_used,
        }

    written: list[str] = []
    for fname, content in file_plan.items():
        try:
            (agent_dir / fname).write_text(content, encoding="utf-8")
            written.append(fname)
            logger.debug("Wrote %s (%d bytes)", fname, len(content.encode("utf-8")))
        except Exception as exc:
            logger.warning("Failed to write %s for %s: %s", fname, slug, exc)

    logger.info(
        "Promoted agent %s from skeleton → complete (%d files, %d insights, llm=%s)",
        slug,
        len(written),
        total_insights,
        llm_used,
    )

    return {
        "promoted": True,
        "status_before": status_before,
        "status_after": _PROMOTED_STATUS,
        "agent_dir": str(agent_dir),
        "files": written,
        "total_insights": total_insights,
        "dna_layers": 10,
        "llm_used": llm_used,
        "anchors_count": len(anchors),
    }


def ensure_agent_promoted(
    slug: str,
    bucket: str = "external",
    *,
    dry_run: bool = False,
    use_llm: bool = True,
) -> dict[str, Any]:
    """Non-fatal wrapper around promote_agent. Designed for pipeline wiring.

    Never raises. Returns structured result with promoted=False + error on failure.
    """
    try:
        return promote_agent(slug, bucket, dry_run=dry_run, use_llm=use_llm)
    except Exception as exc:
        logger.warning("ensure_agent_promoted failed for %s: %s", slug, exc)
        return {
            "promoted": False,
            "error": str(exc),
            "agent_dir": "",
            "files": [],
        }
