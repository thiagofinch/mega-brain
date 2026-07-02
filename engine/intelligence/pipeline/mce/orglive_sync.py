"""engine/intelligence/pipeline/mce/orglive_sync.py — Story MCE-11.9.

Sincroniza MEMORY técnica de cargo agents para versão executiva ORG-LIVE
em workspace/{bu}/L4-operational/org-live/{role-slug}.md.

Analogia: se MEMORY do Closer é o manual técnico completo (500 linhas),
o ORG-LIVE do Closer é o one-pager executivo que o CEO lê.

Fluxo:
    agents/external/cargo/{area}/{role}/MEMORY.md  (fonte)
        │
        ▼
    orglive_sync.sync_cargo_to_orglive()           (condensação)
        │
        ▼
    workspace/{bu}/L4-operational/org-live/{role}.md  (destino)

Uso em cmd_finalize (non-blocking):
    from engine.intelligence.pipeline.mce.orglive_sync import sync_all_cargo_agents
    sync_all_cargo_agents()  # BU detectada automaticamente
"""

from __future__ import annotations

import logging
import re
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# Lazy import to avoid circular deps at module load
def _agents_cargo() -> Path:
    from engine.paths import AGENTS_CARGO

    return AGENTS_CARGO


def _workspace_businesses() -> Path:
    from engine.paths import WORKSPACE_BUSINESSES

    return WORKSPACE_BUSINESSES


# ---------------------------------------------------------------------------
# BU discovery
# ---------------------------------------------------------------------------


def _resolve_default_bu() -> str:
    """Discover default BU from workspace config or filesystem fallback.

    Priority:
    1. workspace/_system/config.yaml → first active business slug
    2. Single directory under workspace/businesses/
    3. Env override: MEGA_BRAIN_DEFAULT_BU
    4. Hard fallback: 'default'
    """
    import os
    try:
        config_path = _PROJECT_ROOT / "workspace" / "_system" / "config.yaml"
        if config_path.exists():
            import yaml  # type: ignore[import-untyped]

            with config_path.open(encoding="utf-8") as fh:
                cfg = yaml.safe_load(fh) or {}
            businesses = cfg.get("businesses", [])
            if isinstance(businesses, list):
                for biz in businesses:
                    if isinstance(biz, dict) and biz.get("status") == "active":
                        slug = biz.get("slug", "")
                        if slug:
                            return slug
    except Exception as exc:
        logger.debug("orglive_sync: config.yaml read failed: %s", exc)

    # Filesystem fallback: single BU directory
    try:
        businesses_dir = _workspace_businesses()
        if businesses_dir.is_dir():
            dirs = [
                d.name
                for d in businesses_dir.iterdir()
                if d.is_dir() and not d.name.startswith("_")
            ]
            if len(dirs) == 1:
                return dirs[0]
    except Exception as exc:
        logger.debug("orglive_sync: filesystem BU discovery failed: %s", exc)

    return os.environ.get("MEGA_BRAIN_DEFAULT_BU", "").strip() or "default"


# ---------------------------------------------------------------------------
# MEMORY.md parser — extracts structured sections defensively
# ---------------------------------------------------------------------------

# Seção headers para identificar blocos relevantes da MEMORY
_SECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "frameworks",
        re.compile(
            r"##\s+(FRAMEWORKS?|FRAMEWORKS? INCORPORADOS?|FRAMEWORKS? EM USO)", re.IGNORECASE
        ),
    ),
    (
        "tecnicas",
        re.compile(r"##\s+(TÉCNICAS?|TECNICAS? ADQUIRIDAS?|TÉCNICAS? EM USO)", re.IGNORECASE),
    ),
    ("metricas", re.compile(r"##\s+(MÉTRICAS?|METRICAS? DE REFERÊNCIA|METRICAS?)", re.IGNORECASE)),
    ("gaps", re.compile(r"##\s+(GAPS? IDENTIFICADOS?|GAPS?|LACUNAS?)", re.IGNORECASE)),
    (
        "prioridade",
        re.compile(r"##\s+(PRIORIDADE|FOCO ATUAL|PRIORITY|CURRENT FOCUS)", re.IGNORECASE),
    ),
    (
        "aprendizados",
        re.compile(r"##\s+(APRENDIZADOS?|INSIGHTS? ACUMULADOS?|LEARNINGS?)", re.IGNORECASE),
    ),
    ("decisoes", re.compile(r"##\s+(PADRÕES? DECISÓRIOS?|DECISOES?|DECISION)", re.IGNORECASE)),
]

# Linhas a ignorar para condensação mecânica (meta, rastreabilidade, etc.)
_SKIP_LINE_PATTERNS = [
    re.compile(r"^\s*>\s*\*?\*?Agente\*?\*?:"),
    re.compile(r"^\s*>\s*\*?\*?Criada\*?\*?:"),
    re.compile(r"^\s*>\s*\*?\*?Última atualização\*?\*?:"),
    re.compile(r"^\s*>\s*\*?\*?Versão\*?\*?:"),
    re.compile(r"^\s*>\s*\*?\*?Rastreabilidade\*?\*?:"),
    re.compile(r"^\s*\^?\[insight_id:"),
    re.compile(r"^\s*\^?\[RAIZ:"),
    re.compile(r"^\s*\^?\[chunk_id:"),
    re.compile(r"^\s*---\s*$"),
]


def _parse_memory_sections(memory_text: str) -> dict[str, list[str]]:
    """Divide MEMORY.md em seções nomeadas (lista de linhas por seção).

    Parser defensivo: se estrutura for inconsistente, retorna o que encontrou
    sem levantar exceção.
    """
    sections: dict[str, list[str]] = {
        "frameworks": [],
        "tecnicas": [],
        "metricas": [],
        "gaps": [],
        "prioridade": [],
        "aprendizados": [],
        "decisoes": [],
        "_raw_header": [],
    }

    lines = memory_text.splitlines()
    current_section = "_raw_header"

    for line in lines:
        # Verifica se linha é um header de seção conhecida
        matched = False
        for sec_name, pattern in _SECTION_PATTERNS:
            if pattern.match(line):
                current_section = sec_name
                matched = True
                break

        if not matched:
            # Filtra linhas de metadados/rastreabilidade
            skip = any(p.match(line) for p in _SKIP_LINE_PATTERNS)
            if not skip:
                sections.setdefault(current_section, []).append(line)

    return sections


def _extract_header_meta(memory_text: str) -> dict[str, Any]:
    """Extrai metadados do header da MEMORY: versão, última atualização, role."""
    meta: dict[str, Any] = {}
    for line in memory_text.splitlines()[:30]:
        m = re.search(r"\*\*Versão\*\*:\s*([\d.]+)", line)
        if m:
            meta["versao"] = m.group(1)
        m = re.search(r"\*\*Última atualização\*\*:\s*(\S+)", line)
        if m:
            meta["ultima_atualizacao"] = m.group(1)
    return meta


# ---------------------------------------------------------------------------
# Condensation — LLM path + deterministic fallback
# ---------------------------------------------------------------------------

_LLM_TIMEOUT_S = 30
_ORG_LIVE_MAX_TOKENS = 2000


def _build_llm_prompt(role_slug: str, sections: dict[str, list[str]], meta: dict[str, Any]) -> str:
    """Monta prompt para condensação LLM da MEMORY técnica → ORG-LIVE executivo."""
    role_display = role_slug.replace("-", " ").title()

    # Concatena seções relevantes (max 3000 chars total para não exceder context)
    relevant = []
    for key in ("prioridade", "frameworks", "tecnicas", "gaps", "metricas", "aprendizados"):
        lines = sections.get(key, [])
        if lines:
            relevant.append(f"### {key.upper()}\n" + "\n".join(lines[:40]))

    content_block = "\n\n".join(relevant)[:3000]

    return f"""Você é um assistente executivo que converte documentação técnica de agentes em resumos executivos.

Role: {role_display}
Última atualização MEMORY: {meta.get("ultima_atualizacao", "desconhecida")}

MEMORY técnica (excerto):
---
{content_block}
---

Gere um ORG-LIVE executivo em português brasileiro com exatamente esta estrutura markdown:

## Prioridade Atual
[1 parágrafo — o que o {role_display} está focando agora, baseado nos aprendizados]

## Frameworks em Uso
| Framework | Aplicação | KPI Impactado |
|-----------|-----------|---------------|
[até 5 linhas, baseadas nos frameworks/técnicas encontrados]

## Gaps Identificados
[lista bullet — gaps encontrados com impacto para o negócio. Se nenhum gap identificado, escreva "Nenhum gap crítico identificado."]

## Métricas de Referência
| Métrica | Valor | Fonte |
|---------|-------|-------|
[até 5 métricas encontradas na MEMORY]

## Próximos Ingests Recomendados
[1-2 frases sugerindo conteúdo a ingerir baseado nos gaps identificados]

REGRAS:
- Use português brasileiro com acentuação correta
- Seja conciso: máximo 220 linhas no total
- Baseie-se APENAS no conteúdo fornecido, sem inventar
- Se uma seção não tem dados, escreva uma linha explicando a ausência
"""


def _condense_with_llm(
    role_slug: str, sections: dict[str, list[str]], meta: dict[str, Any]
) -> str | None:
    """Tenta condensar via LLM (Haiku). Retorna texto ou None se LLM indisponível/timeout."""
    try:
        from engine.intelligence.pipeline.mce.llm_router import LLMRouter, ProviderUnavailableError

        router = LLMRouter()

        # Timeout via signal (Unix only; graceful degradation em Windows)
        result_holder: list[str] = []
        prompt = _build_llm_prompt(role_slug, sections, meta)

        def _run():
            try:
                text = router.run_prompt(
                    prompt,
                    step="orglive_condensation",
                    max_output_tokens=_ORG_LIVE_MAX_TOKENS,
                )
                result_holder.append(text)
            except ProviderUnavailableError:
                pass
            except Exception as exc:
                logger.debug("orglive_sync: LLM call failed for %s: %s", role_slug, exc)

        if hasattr(signal, "SIGALRM"):

            def _timeout_handler(signum, frame):
                raise TimeoutError("LLM timeout")

            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(_LLM_TIMEOUT_S)
            try:
                _run()
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        else:
            # Windows: sem alarm, timeout não garantido mas tentamos
            _run()

        return result_holder[0] if result_holder else None

    except Exception as exc:
        logger.debug("orglive_sync: LLM condensation unavailable for %s: %s", role_slug, exc)
        return None


def _condense_mechanical(
    role_slug: str, sections: dict[str, list[str]], meta: dict[str, Any]
) -> str:
    """Condensação mecânica determinística (fallback quando LLM indisponível).

    Pega as primeiras 3-5 linhas de cada seção relevante.
    Resultado menos elegante mas funcional e rastreável.
    """
    lines: list[str] = []

    # Prioridade atual
    prioridade_lines = [
        ln for ln in sections.get("prioridade", []) if ln.strip() and not ln.startswith("#")
    ]
    if prioridade_lines:
        lines.append("## Prioridade Atual")
        lines.extend(prioridade_lines[:3])
        lines.append("")
    else:
        # Fallback: primeiras linhas de aprendizados
        aprendizados = [
            ln for ln in sections.get("aprendizados", []) if ln.strip() and not ln.startswith("#")
        ]
        if aprendizados:
            lines.append("## Prioridade Atual")
            lines.extend(aprendizados[:3])
            lines.append("")

    # Frameworks
    fw_lines = [
        ln for ln in sections.get("frameworks", []) if ln.strip() and not ln.startswith("#")
    ]
    if fw_lines:
        lines.append("## Frameworks em Uso")
        lines.append("| Framework | Aplicação | KPI Impactado |")
        lines.append("|-----------|-----------|---------------|")
        for fw_line in fw_lines[:5]:
            # Tenta extrair nome do framework de linhas com bullets ou tabela
            fw_name = fw_line.lstrip("- *|").split("|")[0].strip()
            if fw_name and len(fw_name) < 80:
                lines.append(f"| {fw_name} | — | — |")
        lines.append("")
    else:
        lines.append("## Frameworks em Uso")
        lines.append("Dados de frameworks não identificados na MEMORY atual.")
        lines.append("")

    # Gaps
    gap_lines = [ln for ln in sections.get("gaps", []) if ln.strip() and not ln.startswith("#")]
    lines.append("## Gaps Identificados")
    if gap_lines:
        for gap in gap_lines[:5]:
            gap_clean = gap.lstrip("- *").strip()
            if gap_clean:
                lines.append(f"- {gap_clean}")
    else:
        lines.append("- Nenhum gap crítico identificado na MEMORY atual.")
    lines.append("")

    # Métricas
    met_lines = [ln for ln in sections.get("metricas", []) if ln.strip() and not ln.startswith("#")]
    lines.append("## Métricas de Referência")
    if met_lines:
        lines.append("| Métrica | Valor | Fonte |")
        lines.append("|---------|-------|-------|")
        for met in met_lines[:5]:
            met_clean = met.lstrip("- *|").strip()
            if met_clean and len(met_clean) < 80:
                lines.append(f"| {met_clean} | — | — |")
    else:
        lines.append("Métricas de referência não identificadas na MEMORY atual.")
    lines.append("")

    # Próximos ingests
    gap_summary = (
        "; ".join(ln.lstrip("- *").strip() for ln in gap_lines[:2] if ln.strip())
        if gap_lines
        else "gaps não identificados"
    )
    lines.append("## Próximos Ingests Recomendados")
    lines.append(f"Baseado em: {gap_summary}. Consulte knowledge/external/ para fontes relevantes.")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ORG-LIVE document builder
# ---------------------------------------------------------------------------


def _build_orglive_document(
    role_slug: str,
    memory_path: Path,
    condensed_body: str,
    ingests_count: int,
    health_indicator: str,
) -> str:
    """Monta o documento ORG-LIVE completo com header + corpo condensado."""
    role_display = role_slug.replace("-", " ").title()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        fonte_display = str(memory_path.relative_to(_PROJECT_ROOT))
    except ValueError:
        fonte_display = str(memory_path)

    header = (
        f"# ORG-LIVE — {role_display}\n"
        f"> Atualizado: {now_str} | Ingests processados: {ingests_count} | Status: {health_indicator} ATIVO\n"
        f"> Fonte: `{fonte_display}`\n\n"
    )

    return header + condensed_body.strip() + "\n"


def _count_ingests_from_memory(memory_text: str) -> int:
    """Conta número aproximado de fontes/ingests referenciadas na MEMORY."""
    # Padrão: chunks_id como *SRC004*, *JH002*, etc. — conta fontes únicas
    source_prefixes = set(re.findall(r"\*([A-Z]+)\d+\*", memory_text))
    if source_prefixes:
        return len(source_prefixes)
    # Fallback: conta headers de seção "De FONTE: ..."
    return len(re.findall(r"####\s+De\s+\w+:", memory_text))


def _determine_health(memory_text: str) -> str:
    """Determina indicador de saúde baseado em conteúdo da MEMORY."""
    gap_count = len(re.findall(r"(?i)gap\s*[\d:]|lacuna\s*[\d:]|\-\s*gap\s", memory_text))
    insight_count = len(re.findall(r"\^?\[insight_id:|chunk_id:", memory_text))

    if insight_count >= 20 and gap_count <= 2:
        return "🟢"
    if insight_count >= 5:
        return "🟡"
    return "🔴"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def sync_cargo_to_orglive(
    cargo_agent_path: Path,
    workspace_bu: str | None = None,
) -> Path | None:
    """Sincroniza MEMORY técnica de um cargo agent para ORG-LIVE executivo.

    AC1 (Story MCE-11.9): função principal do módulo.

    Args:
        cargo_agent_path: Path para o diretório do cargo agent
            (contendo MEMORY.md). Ex: agents/external/cargo/sales/closer/
        workspace_bu: Slug da business unit. Quando None, é resolvido
            automaticamente via _resolve_default_bu() (config/filesystem/env).

    Returns:
        Path do arquivo ORG-LIVE gerado, ou None se não houver MEMORY.md.
    """
    if workspace_bu is None:
        workspace_bu = _resolve_default_bu()

    memory_path = cargo_agent_path / "MEMORY.md"

    if not memory_path.exists():
        logger.debug("orglive_sync: MEMORY.md não encontrada em %s — skip", cargo_agent_path)
        return None

    role_slug = cargo_agent_path.name  # Ex: 'closer', 'bdr', 'sales-manager'
    area_slug = cargo_agent_path.parent.name  # Ex: 'sales', 'marketing', 'c-level'

    # Output path: workspace/{bu}/L4-operational/org-live/{role}.md
    orglive_dir = _workspace_businesses() / workspace_bu / "L4-operational" / "org-live"
    orglive_path = orglive_dir / f"{role_slug}.md"

    # AC5: Timestamp check — skip se ORG-LIVE mais recente que MEMORY
    if orglive_path.exists():
        memory_mtime = memory_path.stat().st_mtime
        orglive_mtime = orglive_path.stat().st_mtime
        if orglive_mtime >= memory_mtime:
            logger.info(
                "orglive_sync: %s SKIPPED — ORG-LIVE is current (orglive_mtime=%.0f >= memory_mtime=%.0f)",
                role_slug,
                orglive_mtime,
                memory_mtime,
            )
            return orglive_path

    # Lê MEMORY.md
    try:
        memory_text = memory_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("orglive_sync: falha ao ler MEMORY.md de %s: %s", cargo_agent_path, exc)
        return None

    # Parse seções
    sections = _parse_memory_sections(memory_text)
    meta = _extract_header_meta(memory_text)

    # Condensação: LLM first, fallback mecânico
    condensed_body = _condense_with_llm(role_slug, sections, meta)
    llm_used = condensed_body is not None
    if not llm_used:
        logger.debug(
            "orglive_sync: LLM indisponível para %s/%s — usando condensação mecânica",
            area_slug,
            role_slug,
        )
        condensed_body = _condense_mechanical(role_slug, sections, meta)

    # Metadados para header
    ingests_count = _count_ingests_from_memory(memory_text)
    health = _determine_health(memory_text)

    # Monta documento completo
    doc = _build_orglive_document(
        role_slug=role_slug,
        memory_path=memory_path,
        condensed_body=condensed_body,
        ingests_count=ingests_count,
        health_indicator=health,
    )

    # AC7: Cria diretório se não existe
    orglive_dir.mkdir(parents=True, exist_ok=True)

    # Escreve arquivo
    try:
        orglive_path.write_text(doc, encoding="utf-8")
        try:
            _orglive_display = str(orglive_path.relative_to(_PROJECT_ROOT))
        except ValueError:
            _orglive_display = str(orglive_path)
        logger.info(
            "orglive_sync: %s/%s → %s (llm=%s ingests=%d health=%s)",
            area_slug,
            role_slug,
            _orglive_display,
            llm_used,
            ingests_count,
            health,
        )
        return orglive_path
    except OSError as exc:
        logger.warning(
            "orglive_sync: falha ao escrever ORG-LIVE para %s/%s: %s",
            area_slug,
            role_slug,
            exc,
        )
        return None


def sync_all_cargo_agents(bu: str | None = None) -> dict[str, Any]:
    """Itera todos os cargo agents e sincroniza MEMORY → ORG-LIVE.

    AC6 (Story MCE-11.9): chamado de cmd_finalize como non-blocking.

    Args:
        bu: Slug da business unit. Se None, detecta automaticamente.

    Returns:
        Dict com sumário: synced, skipped, failed, paths.
    """
    if bu is None:
        bu = _resolve_default_bu()

    agents_cargo_root = _agents_cargo()

    if not agents_cargo_root.is_dir():
        logger.warning("orglive_sync: AGENTS_CARGO não é diretório: %s", agents_cargo_root)
        return {
            "synced": 0,
            "skipped": 0,
            "failed": 0,
            "error": f"AGENTS_CARGO not a directory: {agents_cargo_root}",
            "bu": bu,
        }

    # AC6: Itera via rglob("MEMORY.md") — cobre todas as áreas (sales, marketing, c-level, etc.)
    memory_files = list(agents_cargo_root.rglob("MEMORY.md"))

    synced: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

    for memory_file in memory_files:
        cargo_dir = memory_file.parent
        role_slug = cargo_dir.name

        # AC6: Non-blocking — falha em um agent não para os demais
        try:
            result_path = sync_cargo_to_orglive(
                cargo_agent_path=cargo_dir,
                workspace_bu=bu,
            )
            if result_path is None:
                skipped.append(role_slug)
            else:
                # Distingue skip-por-timestamp de sync genuíno
                # (sync_cargo_to_orglive retorna o path em ambos os casos;
                #  se o arquivo foi escrito agora ele é mais novo que MEMORY;
                #  se foi skip-por-timestamp ele é ainda mais antigo — mas
                #  a distinção já foi logada dentro de sync_cargo_to_orglive)
                try:
                    _rp_display = str(result_path.relative_to(_PROJECT_ROOT))
                except ValueError:
                    _rp_display = str(result_path)
                synced.append(_rp_display)
        except Exception as exc:
            logger.warning("orglive_sync: falha em %s (non-blocking): %s", role_slug, exc)
            failed.append(f"{role_slug}: {exc}")

    result = {
        "synced": len(synced),
        "skipped": len(skipped),
        "failed": len(failed),
        "synced_paths": synced,
        "skipped_agents": skipped,
        "failed_agents": failed,
        "bu": bu,
        "cargo_root": (
            str(agents_cargo_root.relative_to(_PROJECT_ROOT))
            if agents_cargo_root.is_relative_to(_PROJECT_ROOT)
            else str(agents_cargo_root)
        ),
    }

    logger.info(
        "orglive_sync: sync_all_cargo_agents bu=%s → synced=%d skipped=%d failed=%d",
        bu,
        len(synced),
        len(skipped),
        len(failed),
    )

    return result
