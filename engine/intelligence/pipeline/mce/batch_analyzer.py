"""
batch_analyzer.py — Cross-Batch Analysis + Executive Briefing
==============================================================

Implements OLD MegaBrain subphases 8.7-8.9 that were absent in NEW:

  8.7  cross_batch_analysis()       — compare current batch vs last-5 avg,
                                       flag anomalies when deviation > 25%
  8.8  generate_executive_briefing() — PT-BR executive summary (LLM or fallback)
  8.9  update_batch_history()        — append entry to BATCH-HISTORY.json,
                                       prune to last 100

Story: MCE-11.11
Design rules:
  - stdlib + PyYAML only (no LLM import inside this module; LLM called via
    optional anthropic SDK that may be absent — graceful fallback required)
  - All I/O is non-blocking; caller wraps in try/except
  - BATCH-HISTORY.json uses atomic write (tmp → rename)
  - Briefings saved to logs/executive-briefings/{slug}-{YYYYMMDD}.md
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path resolution (mirrors orchestrate.py pattern)
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_DATA_ARTIFACTS = _PROJECT_ROOT / ".data" / "artifacts"
_BATCH_HISTORY_PATH = _DATA_ARTIFACTS / "BATCH-HISTORY.json"
_BRIEFINGS_DIR = _PROJECT_ROOT / "logs" / "executive-briefings"

# Maximum entries to keep in BATCH-HISTORY.json (AC2)
_MAX_HISTORY = 100

# Window for cross-batch comparison (AC3)
_COMPARISON_WINDOW = 5

# Anomaly threshold — deviations beyond this are flagged (AC4)
_ANOMALY_THRESHOLD_PCT = 25.0


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


def _load_batch_history() -> list[dict[str, Any]]:
    """Load BATCH-HISTORY.json. Returns empty list if missing or corrupt."""
    if not _BATCH_HISTORY_PATH.exists():
        return []
    try:
        raw = _BATCH_HISTORY_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        # Unexpected shape — treat as empty
        logger.warning("batch_analyzer: BATCH-HISTORY.json has unexpected shape, resetting")
        return []
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("batch_analyzer: cannot read BATCH-HISTORY.json: %s", exc)
        return []


def _save_batch_history(entries: list[dict[str, Any]]) -> None:
    """Atomically write BATCH-HISTORY.json (tmp → rename pattern)."""
    _DATA_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(entries, ensure_ascii=False, indent=2)
    # Write to tmp in same directory so rename is atomic on POSIX
    fd, tmp_path = tempfile.mkstemp(
        dir=str(_DATA_ARTIFACTS), prefix=".BATCH-HISTORY-", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        Path(tmp_path).replace(_BATCH_HISTORY_PATH)
    except Exception:
        # Clean up tmp on failure
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass
        raise


def _generate_batch_id(history: list[dict[str, Any]]) -> str:
    """Generate BATCH-{YYYYMMDD}-{NNN} where NNN = count of batches same day (1-based)."""
    today = datetime.now().strftime("%Y%m%d")
    today_prefix = f"BATCH-{today}-"
    same_day_count = sum(
        1 for e in history if isinstance(e, dict) and e.get("batch_id", "").startswith(today_prefix)
    )
    return f"{today_prefix}{same_day_count + 1:03d}"


# ---------------------------------------------------------------------------
# AC3 + AC4 — Cross-Batch Analysis
# ---------------------------------------------------------------------------


def cross_batch_analysis(
    slug: str,
    current_metrics: dict[str, Any],
    history: list[dict[str, Any]] | None = None,
    threshold_pct: float = _ANOMALY_THRESHOLD_PCT,
) -> dict[str, Any]:
    """Compare current batch metrics against the last-5 historical batches.

    Args:
        slug:             Source slug (e.g. "alex-hormozi")
        current_metrics:  Metrics dict for the current batch (see AC1 schema)
        history:          Pre-loaded history list; loaded from disk if None
        threshold_pct:    Deviation % that triggers an anomaly flag

    Returns:
        Dict with keys:
          - ``anomalies``    : list[dict] — each flagged metric
          - ``historical_avg``: dict — avg values used for comparison
          - ``comparison_window``: int — how many historical batches used
          - ``has_history``  : bool
          - ``note``         : str — human note (e.g. insufficient history)
    """
    if history is None:
        history = _load_batch_history()

    # Filter history to same slug (or use global if slug not in history at all)
    slug_history = [e for e in history if isinstance(e, dict) and e.get("source_id") == slug]
    # Fall back to global if slug has no dedicated history yet
    comparison_pool = slug_history if slug_history else history

    if not comparison_pool:
        return {
            "anomalies": [],
            "historical_avg": {},
            "comparison_window": 0,
            "has_history": False,
            "note": "Sem histórico anterior — primeira execução registrada.",
        }

    window = comparison_pool[-_COMPARISON_WINDOW:]
    window_size = len(window)

    # Metrics to compare (numeric only)
    metrics_to_check = [
        "chunks",
        "insights_total",
        "insights_high",
        "insights_medium",
        "insights_low",
    ]

    historical_avg: dict[str, float] = {}
    for metric in metrics_to_check:
        values = [
            e.get("metrics", {}).get(metric, 0)
            for e in window
            if isinstance(e.get("metrics"), dict)
        ]
        if values:
            historical_avg[metric] = sum(values) / len(values)

    if not historical_avg:
        return {
            "anomalies": [],
            "historical_avg": {},
            "comparison_window": window_size,
            "has_history": True,
            "note": f"Histórico disponível ({window_size} batches) mas sem métricas comparáveis.",
        }

    # MCE-13.20: Duration-normalised anomaly detection.
    # Compute per-minute density for both current batch and history window
    # to avoid false anomalies caused solely by shorter/longer sources.
    # Example: a 26-min video vs 45-min historical avg should not flag -97%
    # on chunks if the per-minute rate is similar.
    current_duration = float(current_metrics.get("processing_time_minutes", 0) or 0)
    historical_duration_values = [
        float(e.get("metrics", {}).get("processing_time_minutes", 0) or 0)
        for e in window
        if isinstance(e.get("metrics"), dict)
    ]
    hist_avg_duration = (
        sum(historical_duration_values) / len(historical_duration_values)
        if historical_duration_values
        else 0.0
    )

    def _normalise(raw_val: float, duration_min: float) -> float:
        """Return per-minute rate if duration available, else raw value."""
        if duration_min and duration_min > 0:
            return raw_val / duration_min
        return raw_val

    anomalies: list[dict[str, Any]] = []
    for metric, avg in historical_avg.items():
        if avg == 0:
            # Avoid division by zero — skip metric
            continue
        current_val = float(current_metrics.get(metric, 0))

        # Normalise by duration when both current and historical durations available
        if current_duration > 0 and hist_avg_duration > 0:
            current_norm = _normalise(current_val, current_duration)
            avg_norm = _normalise(avg, hist_avg_duration)
        else:
            current_norm = current_val
            avg_norm = avg

        if avg_norm == 0:
            continue
        deviation_pct = round(((current_norm - avg_norm) / avg_norm) * 100.0, 1)
        if abs(deviation_pct) > threshold_pct:
            norm_note = " (normalizado por duração)" if current_duration > 0 else ""
            if deviation_pct < 0:
                flag_msg = (
                    f"{metric} {abs(deviation_pct):.0f}% abaixo da média{norm_note} — "
                    f"possível vídeo curto ou extração ruim"
                    if metric == "chunks"
                    else f"{metric} {abs(deviation_pct):.0f}% abaixo da média histórica{norm_note}"
                )
            else:
                flag_msg = (
                    f"{metric} {deviation_pct:.0f}% acima da média{norm_note} — "
                    f"conteúdo incomumente denso"
                    if metric == "chunks"
                    else f"{metric} {deviation_pct:.0f}% acima da média histórica{norm_note}"
                )
            anomalies.append(
                {
                    "metric": metric,
                    "current": current_val,
                    "current_norm": round(current_norm, 3),
                    "historical_avg": round(avg, 1),
                    "historical_avg_norm": round(avg_norm, 3),
                    "deviation_pct": deviation_pct,
                    "duration_normalised": current_duration > 0 and hist_avg_duration > 0,
                    "flag": flag_msg,
                }
            )

    if window_size < _COMPARISON_WINDOW:
        note = (
            f"Histórico insuficiente para análise comparativa — "
            f"{window_size} run(s) disponível(is) de {_COMPARISON_WINDOW} necessários."
        )
    else:
        note = f"Análise baseada nos últimos {window_size} batches."

    return {
        "anomalies": anomalies,
        "historical_avg": historical_avg,
        "comparison_window": window_size,
        "has_history": True,
        "note": note,
    }


# ---------------------------------------------------------------------------
# AC5 — Executive Briefing (LLM or mechanical fallback)
# ---------------------------------------------------------------------------


def _health_status_label(metrics: dict[str, Any], anomalies: list[dict]) -> str:
    """Return EXCELENTE / BOM / ATENCAO / CRITICO based on anomaly count and metrics."""
    if not anomalies:
        chunks = metrics.get("chunks", 0)
        insights_h = metrics.get("insights_high", 0)
        insights_t = metrics.get("insights_total", 1) or 1
        high_ratio = insights_h / insights_t
        if chunks >= 30 and high_ratio >= 0.25:
            return "EXCELENTE"
        return "BOM"
    critical = [a for a in anomalies if abs(a.get("deviation_pct", 0)) > 60]
    if critical:
        return "CRITICO"
    return "ATENCAO"


def _mechanical_briefing(
    slug: str,
    source_id: str,
    source_person: str,
    metrics: dict[str, Any],
    anomalies: list[dict],
    agents_updated: list[str],
    themes_touched: list[str],
    analysis: dict[str, Any],
    timestamp: str,
    files_modified: list[dict] | None = None,
) -> str:
    """Mechanical (no-LLM) executive briefing template."""
    chunks = metrics.get("chunks", 0)
    insights_t = metrics.get("insights_total", 0)
    insights_h = metrics.get("insights_high", 0)
    proc_time = metrics.get("processing_time_minutes", 0.0)
    health = _health_status_label(metrics, anomalies)

    # Health indicator
    health_icons = {
        "EXCELENTE": "EXCELENTE",
        "BOM": "BOM",
        "ATENCAO": "ATENCAO",
        "CRITICO": "CRITICO",
    }
    health_label = health_icons.get(health, health)

    # One-sentence summary
    agents_str = ", ".join(agents_updated) if agents_updated else slug
    themes_str = ", ".join(themes_touched[:3]) if themes_touched else "temas gerais"
    em_uma_frase = (
        f"Processado {chunks} chunks de {source_person or slug} "
        f"com {insights_t} insights extraídos ({insights_h} de alta prioridade) "
        f"sobre {themes_str}."
    )

    # Insights section
    insights_list = []
    if chunks:
        insights_list.append(
            f"Extração gerou {chunks} chunks — densidade indica conteúdo "
            + ("rico e denso." if chunks >= 40 else "moderado ou vídeo curto.")
        )
    if insights_h:
        high_pct = round(insights_h / max(insights_t, 1) * 100)
        insights_list.append(
            f"{insights_h} insights classificados como HIGH ({high_pct}% do total) — "
            "estes têm prioridade para atualização de agentes."
        )
    if agents_updated:
        insights_list.append(
            f"Agentes atualizados: {', '.join(agents_updated)} — "
            "memória enriquecida com novos padrões desta fonte."
        )
    if not insights_list:
        insights_list.append("Extração concluída sem dados adicionais disponíveis.")
    # Pad to 3
    while len(insights_list) < 3:
        insights_list.append("Sem insight adicional para este batch.")

    # Automated decisions
    decisions = []
    if agents_updated:
        decisions.append(f"MEMORY.md atualizado para: {', '.join(agents_updated)}")
    if themes_touched:
        decisions.append(f"Temas indexados: {', '.join(themes_touched[:5])}")
    decisions.append("RAG index re-gerado para bucket correspondente")
    if not decisions:
        decisions.append("Sem decisões automáticas registradas neste batch.")

    # Anomalies section
    if anomalies:
        anomaly_lines = [f"- {a['flag']}" for a in anomalies]
    else:
        anomaly_lines = ["- Nenhuma anomalia — batch dentro do padrão histórico."]

    # Next steps
    next_steps = []
    if anomalies:
        critical_metrics = [a["metric"] for a in anomalies if a.get("deviation_pct", 0) < 0]
        if "chunks" in critical_metrics:
            next_steps.append(
                "Verificar qualidade da transcrição — chunks abaixo da média indicam possível falha no áudio ou vídeo muito curto."
            )
        else:
            next_steps.append(
                "Revisar métricas anômalas antes de usar insights desta extração em decisões."
            )
    else:
        next_steps.append(
            f"Revisar insights HIGH ({insights_h} itens) e validar se estão corretos antes de propagar."
        )
    if insights_t > 0:
        next_steps.append(
            f"Checar MEMORY.md de {agents_str} para confirmar que os novos padrões foram absorvidos corretamente."
        )
    next_steps.append(
        "Rodar `/jarvis-briefing` para ver o status geral do pipeline e próximos batches na fila."
    )
    # Pad to 3
    while len(next_steps) < 3:
        next_steps.append("Sem ação adicional recomendada para este batch.")

    # Note
    history_note = analysis.get("note", "")

    lines = [
        f"# Executive Briefing — {source_person or slug} ({source_id})",
        f"> Gerado em: {timestamp}",
        "> Modo: template mecanico (LLM nao disponivel)",
        "",
        "## Em Uma Frase",
        em_uma_frase,
        "",
        "## O Que Aprendemos",
    ]
    for i, ins in enumerate(insights_list[:3], 1):
        lines.append(f"{i}. {ins}")

    lines += [
        "",
        "## Decisões Automáticas",
    ]
    for d in decisions:
        lines.append(f"- {d}")

    lines += [
        "",
        "## Anomalias Detectadas",
    ]
    lines += anomaly_lines

    lines += [
        "",
        "## Próximos Passos Sugeridos",
    ]
    for i, step in enumerate(next_steps[:3], 1):
        lines.append(f"{i}. {step}")

    # Files modified section (Bug #8)
    files_section_lines = _render_files_modified_section(files_modified or [])
    if files_section_lines:
        lines += files_section_lines

    lines += [
        "",
        "## Análise Cross-Batch",
        f"_{history_note}_",
        "",
        "## Status de Saúde",
        f"{health_label} | Chunks: {chunks} | Insights: {insights_t} ({round(insights_h / max(insights_t, 1) * 100)}% HIGH) | Tempo: {proc_time} min",
    ]

    return "\n".join(lines)


def _readable_agent_name(agent_path: str) -> str:
    """Convert an agent path to a human-readable display name.

    Examples:
      "agents/external/alex-hormozi"           → "Alex Hormozi"
      "agents/external/cargo/sales/closer"     → "Closer"
      "agents/external/cargo/sales/bdr"        → "BDR"
      "agents/external/cargo/c-level/cfo"      → "CFO"
    """
    # Take the last path component, strip common prefixes
    parts = agent_path.replace("\\", "/").strip("/").split("/")
    name = parts[-1] if parts else agent_path
    # Title-case hyphen-separated words, keeping all-caps acronyms intact
    segments = name.split("-")
    readable_parts = []
    for seg in segments:
        if seg.upper() in ("BDR", "SDR", "SDS", "CFO", "CRO", "CMO", "CEO", "CTO", "COO"):
            readable_parts.append(seg.upper())
        else:
            readable_parts.append(seg.capitalize())
    return " ".join(readable_parts)


def _render_files_modified_section(files_modified: list[dict]) -> list[str]:
    """Render the '## Arquivos Modificados' section lines.

    Each entry in files_modified is a dict with keys:
      - path (str): e.g. "agents/external/alex-hormozi"
      - type (str): "agent" | "dna" | "dossier" | "memory" | other
      - change_summary (str): e.g. "+2500 linhas em MEMORY.md"
      - readable_name (str, optional): override for display name
    """
    if not files_modified:
        return []

    TYPE_ICON = {
        "agent": "Agente",
        "dna": "DNA",
        "dossier": "Dossier",
        "memory": "Memoria",
        "config": "Config",
    }

    lines = ["", "## Arquivos Modificados"]
    for entry in files_modified:
        path = entry.get("path", "")
        ftype = entry.get("type", "agent")
        summary = entry.get("change_summary", "")
        readable = entry.get("readable_name") or _readable_agent_name(path)
        icon = TYPE_ICON.get(ftype, "Arquivo")
        short_path = path.replace("agents/external/", "").replace("agents/", "")
        if summary:
            lines.append(f"- [{icon}] **{readable}** (`{short_path}`): {summary}")
        else:
            lines.append(f"- [{icon}] **{readable}** (`{short_path}`)")
    return lines


def _build_briefing_prompt(
    slug: str,
    source_id: str,
    source_person: str,
    metrics: dict[str, Any],
    anomalies: list[dict],
    agents_updated: list[str],
    themes_touched: list[str],
    analysis: dict[str, Any],
    timestamp: str,
    files_modified: list[dict] | None = None,
) -> str:
    """Build the PT-BR prompt for LLM briefing generation."""
    chunks = metrics.get("chunks", 0)
    insights_t = metrics.get("insights_total", 0)
    insights_h = metrics.get("insights_high", 0)
    insights_m = metrics.get("insights_medium", 0)
    insights_l = metrics.get("insights_low", 0)
    proc_time = metrics.get("processing_time_minutes", 0.0)
    health = _health_status_label(metrics, anomalies)

    anomaly_text = (
        "\n".join(f"- {a['flag']} (desvio: {a['deviation_pct']}%)" for a in anomalies)
        if anomalies
        else "Nenhuma anomalia detectada."
    )

    # Build files modified block for prompt context
    files_modified = files_modified or []
    if files_modified:
        files_lines = []
        for entry in files_modified:
            path = entry.get("path", "")
            readable = entry.get("readable_name") or _readable_agent_name(path)
            summary = entry.get("change_summary", "")
            files_lines.append(
                f"  - {readable} ({path}): {summary}" if summary else f"  - {readable} ({path})"
            )
        files_block = "\n".join(files_lines)
    else:
        files_block = "  (não disponível)"

    files_section_template = """
## Arquivos Modificados
[Para cada arquivo modificado da lista de contexto, em formato:
- [Tipo] **Nome Legível** (`path-curto`): resumo da mudança
Use exatamente os dados fornecidos no contexto — não invente arquivos.]"""

    return f"""Você é JARVIS, mordomo-assistente interno do MegaBrain, sistema de gestão de conhecimento do CEO o fundador.
Após cada pipeline de extração, você gera um briefing executivo em PT-BR para o fundador.
Tom: mordomo brit, preciso, direto, sem enrolação — como se estivesse reportando ao patrão após missão completada.

Dados do batch processado:
- Fonte: {source_person or slug} ({source_id})
- Data/hora: {timestamp}
- Chunks extraídos: {chunks}
- Insights totais: {insights_t} (HIGH: {insights_h}, MEDIUM: {insights_m}, LOW: {insights_l})
- Agentes atualizados: {', '.join(agents_updated) if agents_updated else 'nenhum'}
- Temas abordados: {', '.join(themes_touched) if themes_touched else 'sem registro'}
- Tempo de processamento: {proc_time} min
- Status de saúde: {health}
- Análise cross-batch: {analysis.get('note', 'sem histórico')}
- Anomalias detectadas:
{anomaly_text}

Arquivos modificados neste run:
{files_block}

Gere um briefing executivo EXATAMENTE neste formato markdown:

# Executive Briefing — {source_person or slug} ({source_id})
> Gerado em: {timestamp}

## Em Uma Frase
[1 frase descrevendo o que foi processado e o principal aprendizado — direto, sem jargão técnico]

## O Que Aprendemos
1. [Insight principal com implicação de negócio — "isso significa..."]
2. [Insight 2 com implicação prática]
3. [Insight 3 com implicação prática]{files_section_template}

## Decisões Automáticas
- [O que o sistema fez: agentes atualizados, dossiers, indexação, etc.]

## Anomalias Detectadas
- [Se houver anomalias, explique em linguagem business. Senão: "Nenhuma anomalia — batch dentro do padrão histórico."]

## Próximos Passos Sugeridos
1. [Ação concreta 1 — específica e executável]
2. [Ação concreta 2]
3. [Ação concreta 3]

## Status de Saúde
{health} | Chunks: {chunks} | Insights: {insights_t} ({round(insights_h / max(insights_t, 1) * 100)}% HIGH) | Tempo: {proc_time} min

Regras:
- Tom JARVIS mordomo: preciso, brit, sem jargão técnico no corpo do briefing
- "Isso significa..." transforma dado em implicação de negócio
- Máximo 3 bullets por seção (exceto Arquivos Modificados — liste todos)
- Responda SOMENTE com o markdown acima, sem texto adicional antes ou depois"""


def _llm_briefing(
    slug: str,
    source_id: str,
    source_person: str,
    metrics: dict[str, Any],
    anomalies: list[dict],
    agents_updated: list[str],
    themes_touched: list[str],
    analysis: dict[str, Any],
    timestamp: str,
    files_modified: list[dict] | None = None,
) -> str | None:
    """Attempt to generate executive briefing via LLM (Anthropic → OpenAI fallback).

    Priority:
      1. Anthropic Claude Haiku (ANTHROPIC_API_KEY) — 60s client timeout
      2. OpenAI gpt-4o-mini (OPENAI_API_KEY) — 60s client timeout
      3. Returns None → mechanical fallback

    Logs the exact reason for any fallback (never silent).
    """
    prompt = _build_briefing_prompt(
        slug=slug,
        source_id=source_id,
        source_person=source_person,
        metrics=metrics,
        anomalies=anomalies,
        agents_updated=agents_updated,
        themes_touched=themes_touched,
        analysis=analysis,
        timestamp=timestamp,
        files_modified=files_modified,
    )

    # ── 1. Try Anthropic ───────────────────────────────────────────────────────
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        # Try reading from .env (mirrors llm_router pattern)
        _env_file = _PROJECT_ROOT / ".env"
        if _env_file.exists():
            try:
                for _line in _env_file.read_text(encoding="utf-8").splitlines():
                    _line = _line.strip()
                    if _line.startswith("ANTHROPIC_API_KEY="):
                        _candidate = _line.split("=", 1)[1].strip().strip('"').strip("'")
                        if _candidate:
                            anthropic_key = _candidate
                            os.environ.setdefault("ANTHROPIC_API_KEY", _candidate)
                            break
            except OSError:
                pass

    if anthropic_key:
        try:
            import anthropic  # type: ignore

            # Timeout goes on the client, NOT on messages.create() — SDK contract.
            client = anthropic.Anthropic(api_key=anthropic_key, timeout=60.0)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            content = ""
            for block in response.content or []:
                if getattr(block, "type", None) == "text":
                    content = (block.text or "").strip()
                    break
            if content.startswith("# Executive Briefing"):
                logger.info("batch_analyzer: briefing generated via Anthropic Haiku")
                return content
            logger.warning(
                "batch_analyzer: Anthropic response did not start with expected header "
                "(got: %r...) — falling back to OpenAI",
                content[:80],
            )
        except ImportError:
            logger.warning("batch_analyzer: anthropic SDK not installed — falling back to OpenAI")
        except Exception as exc:
            logger.warning(
                "batch_analyzer: Anthropic LLM call failed (%s) — falling back to OpenAI", exc
            )
    else:
        logger.info("batch_analyzer: ANTHROPIC_API_KEY not set — skipping Anthropic, trying OpenAI")

    # ── 2. Try OpenAI ─────────────────────────────────────────────────────────
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai_key:
        _env_file = _PROJECT_ROOT / ".env"
        if _env_file.exists():
            try:
                for _line in _env_file.read_text(encoding="utf-8").splitlines():
                    _line = _line.strip()
                    if _line.startswith("OPENAI_API_KEY="):
                        _candidate = _line.split("=", 1)[1].strip().strip('"').strip("'")
                        if _candidate:
                            openai_key = _candidate
                            os.environ.setdefault("OPENAI_API_KEY", _candidate)
                            break
            except OSError:
                pass

    if openai_key:
        try:
            from openai import OpenAI  # type: ignore

            client_oai = OpenAI(api_key=openai_key, timeout=60.0, max_retries=2)
            oai_response = client_oai.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            content = (oai_response.choices[0].message.content or "").strip()
            if content.startswith("# Executive Briefing"):
                logger.info("batch_analyzer: briefing generated via OpenAI gpt-4o-mini")
                return content
            logger.warning(
                "batch_analyzer: OpenAI response did not start with expected header "
                "(got: %r...) — falling back to mechanical template",
                content[:80],
            )
        except ImportError:
            logger.warning(
                "batch_analyzer: openai SDK not installed — falling back to mechanical template"
            )
        except Exception as exc:
            logger.warning(
                "batch_analyzer: OpenAI LLM call failed (%s) — falling back to mechanical template",
                exc,
            )
    else:
        logger.warning(
            "batch_analyzer: OPENAI_API_KEY also not set — using mechanical template fallback"
        )

    return None


def generate_executive_briefing(
    slug: str,
    source_id: str,
    source_person: str,
    metrics: dict[str, Any],
    anomalies: list[dict],
    agents_updated: list[str],
    themes_touched: list[str],
    analysis: dict[str, Any],
    files_modified: list[dict] | None = None,
) -> dict[str, Any]:
    """Generate executive briefing and save to logs/executive-briefings/.

    Tries LLM (Anthropic Haiku → OpenAI gpt-4o-mini) first; falls back to
    mechanical template only on explicit exception. Fallback reason is always
    logged — never silent.

    Args:
        slug:            Source slug
        source_id:       Source ID (e.g. "LO-0003")
        source_person:   Human-readable person name (e.g. "liam-ottley")
        metrics:         Current batch metrics dict
        anomalies:       Output of cross_batch_analysis()["anomalies"]
        agents_updated:  List of agent slugs updated in this run
        themes_touched:  List of themes/domains touched
        analysis:        Full output of cross_batch_analysis()
        files_modified:  Optional list of dicts with keys:
                           path, type, change_summary, readable_name (opt)

    Returns:
        Dict with ``briefing_path``, ``mode`` (llm|mechanical), ``written``
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    files_modified = files_modified or []

    # Try LLM (Anthropic → OpenAI), fall back to mechanical
    briefing_md = _llm_briefing(
        slug=slug,
        source_id=source_id,
        source_person=source_person,
        metrics=metrics,
        anomalies=anomalies,
        agents_updated=agents_updated,
        themes_touched=themes_touched,
        analysis=analysis,
        timestamp=timestamp,
        files_modified=files_modified,
    )
    mode = "llm"
    if briefing_md is None:
        logger.info(
            "batch_analyzer: both LLM providers unavailable — using mechanical template for %s",
            slug,
        )
        briefing_md = _mechanical_briefing(
            slug=slug,
            source_id=source_id,
            source_person=source_person,
            metrics=metrics,
            anomalies=anomalies,
            agents_updated=agents_updated,
            themes_touched=themes_touched,
            analysis=analysis,
            timestamp=timestamp,
            files_modified=files_modified,
        )
        mode = "mechanical"

    # Save to disk (AC5)
    _BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"BRIEFING-{source_id}-{date_str}.md"
    briefing_path = _BRIEFINGS_DIR / filename

    try:
        briefing_path.write_text(briefing_md, encoding="utf-8")
        written = True
        logger.info("batch_analyzer: executive briefing written to %s", briefing_path)
    except OSError as exc:
        logger.warning("batch_analyzer: cannot write briefing to %s: %s", briefing_path, exc)
        written = False

    return {
        "briefing_path": str(briefing_path),
        "mode": mode,
        "written": written,
        "timestamp": timestamp,
    }


# ---------------------------------------------------------------------------
# AC1 + AC2 — Update Batch History
# ---------------------------------------------------------------------------


def update_batch_history(
    slug: str,
    metrics: dict[str, Any],
    source_id: str,
    source_person: str,
    themes_touched: list[str],
    agents_updated: list[str],
    anomalies: list[dict],
    health_status: str,
) -> dict[str, Any]:
    """Append a new entry to BATCH-HISTORY.json, pruning to last 100.

    Args:
        slug:           Source slug
        metrics:        Batch metrics (AC1 schema)
        source_id:      Source ID (e.g. "LO-0003")
        source_person:  Person name
        themes_touched: List of theme strings
        agents_updated: List of updated agent slugs
        anomalies:      Anomaly list from cross_batch_analysis()
        health_status:  "EXCELENTE" | "BOM" | "ATENCAO" | "CRITICO"

    Returns:
        Dict with ``batch_id``, ``entries_total``, ``pruned``
    """
    history = _load_batch_history()
    batch_id = _generate_batch_id(history)

    entry: dict[str, Any] = {
        "batch_id": batch_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "source_id": source_id,
        "source_person": source_person,
        "slug": slug,
        "metrics": {
            "chunks": int(metrics.get("chunks", 0)),
            "insights_total": int(metrics.get("insights_total", 0)),
            "insights_high": int(metrics.get("insights_high", 0)),
            "insights_medium": int(metrics.get("insights_medium", 0)),
            "insights_low": int(metrics.get("insights_low", 0)),
            "new_entities": int(metrics.get("new_entities", 0)),
            "processing_time_minutes": float(metrics.get("processing_time_minutes", 0.0)),
            "errors_recovered": int(metrics.get("errors_recovered", 0)),
        },
        "themes_touched": themes_touched or [],
        "agents_updated": agents_updated or [],
        "anomalies": anomalies or [],
        "health_status": health_status,
    }

    history.append(entry)

    # Prune to last _MAX_HISTORY (AC2)
    pruned = 0
    if len(history) > _MAX_HISTORY:
        excess = len(history) - _MAX_HISTORY
        history = history[excess:]
        pruned = excess

    _save_batch_history(history)

    return {
        "batch_id": batch_id,
        "entries_total": len(history),
        "pruned": pruned,
        "path": str(_BATCH_HISTORY_PATH),
    }


# ---------------------------------------------------------------------------
# Public facade — called from cmd_finalize (subphases 8.7 → 8.8 → 8.9)
# ---------------------------------------------------------------------------


def run_cross_batch_pipeline(
    slug: str,
    metrics: dict[str, Any],
    source_id: str = "",
    source_person: str = "",
    themes_touched: list[str] | None = None,
    agents_updated: list[str] | None = None,
    files_modified: list[dict] | None = None,
) -> dict[str, Any]:
    """Entry point for cmd_finalize — runs 8.7 → 8.8 → 8.9 in sequence.

    All sub-steps are individually guarded; a failure in one does NOT
    abort the others (Art. XII: Pipeline MCE Integrity).

    Args:
        slug:           Source slug
        metrics:        Current batch metrics (chunks, insights_*, etc.)
        source_id:      Source ID code (derived from slug if empty)
        source_person:  Human-readable person name (derived if empty)
        themes_touched: Optional list of themes from extraction
        agents_updated: Optional list of agents updated in this run
        files_modified: Optional list of dicts with keys:
                          path, type, change_summary, readable_name (opt)

    Returns:
        Dict with keys ``analysis``, ``briefing``, ``history_update``
    """
    themes_touched = themes_touched or []
    agents_updated = agents_updated or []
    files_modified = files_modified or []

    if not source_id:
        # Best-effort derive
        source_id = slug.upper().replace("-", "_")[:10]
    if not source_person:
        source_person = slug

    result: dict[str, Any] = {
        "slug": slug,
        "analysis": {},
        "briefing": {},
        "history_update": {},
    }

    # --- 8.7: Cross-Batch Analysis ---
    try:
        history = _load_batch_history()
        analysis = cross_batch_analysis(
            slug=slug,
            current_metrics=metrics,
            history=history,
        )
        result["analysis"] = analysis
        anomalies = analysis.get("anomalies", [])
    except Exception as exc:
        logger.warning("batch_analyzer: cross_batch_analysis failed: %s", exc)
        analysis = {"anomalies": [], "note": f"error: {exc}"}
        anomalies = []
        result["analysis"] = {"error": str(exc)}

    # Determine health status for this batch
    health_status = _health_status_label(metrics, anomalies)

    # --- 8.8: Executive Briefing ---
    try:
        briefing = generate_executive_briefing(
            slug=slug,
            source_id=source_id,
            source_person=source_person,
            metrics=metrics,
            anomalies=anomalies,
            agents_updated=agents_updated,
            themes_touched=themes_touched,
            analysis=analysis,
            files_modified=files_modified,
        )
        result["briefing"] = briefing
        if briefing.get("written") and briefing.get("briefing_path"):
            print(f"\nExecutive Briefing: {briefing['briefing_path']}\n", flush=True)
    except Exception as exc:
        logger.warning("batch_analyzer: generate_executive_briefing failed: %s", exc)
        result["briefing"] = {"error": str(exc), "written": False}

    # --- 8.9: Update Batch History ---
    try:
        history_update = update_batch_history(
            slug=slug,
            metrics=metrics,
            source_id=source_id,
            source_person=source_person,
            themes_touched=themes_touched,
            agents_updated=agents_updated,
            anomalies=anomalies,
            health_status=health_status,
        )
        result["history_update"] = history_update
    except Exception as exc:
        logger.warning("batch_analyzer: update_batch_history failed: %s", exc)
        result["history_update"] = {"error": str(exc)}

    return result
