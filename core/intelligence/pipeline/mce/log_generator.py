"""
log_generator.py -- MCE Pipeline Log Generator (Chronicler Design System)
=========================================================================
Generates a visual markdown log file after cmd_finalize() completes,
following the CHRONICLER Design System (120 chars, nested boxes,
metric grids, progress bars, super_header/footer).

Writes to: logs/mce/{slug}/MCE-{TAG}.md

Called as the last step of cmd_finalize() in orchestrate.py.

Constraints:
    - Python 3, stdlib + PyYAML only.
    - Imports from core.paths.
    - Non-fatal: never blocks the pipeline.

Version: 2.0.0
Date: 2026-03-16
Design System: CHRONICLER v2.0.0
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from core.paths import ARTIFACTS, LOGS, MISSION_CONTROL, ROOT

logger = logging.getLogger("mce.log_generator")

# ═══════════════════════════════════════════════════════════════════════════════
# CHRONICLER DESIGN TOKENS (inline — no JSON dependency for resilience)
# ═══════════════════════════════════════════════════════════════════════════════

W = 120  # Full width
W1 = 112  # Level 1 (double border)
W2 = 106  # Level 2 (single border)

SOLID = "█"
BAR_FILL = "▓"
BAR_EMPTY = "░"
HEADER_BAR = "▀"
BULLET = "▸"

SOLID_LINE = SOLID * W
DOUBLE_LINE = "═" * W1
SINGLE_LINE = "─" * W2


def _bar(pct: float, width: int = 30) -> str:
    """Generate a progress bar: ▓▓▓▓▓▓░░░░ 60%"""
    filled = int(pct / 100 * width)
    return BAR_FILL * filled + BAR_EMPTY * (width - filled) + f" {int(pct)}%"


def _pad(text: str, width: int, pad_char: str = " ") -> str:
    """Pad text to exact width, truncating if needed."""
    if len(text) >= width:
        return text[:width]
    return text + pad_char * (width - len(text))


def _box_line(content: str, border: str = "║", inner_width: int = W1) -> str:
    """Create a bordered line: ║  content...  ║"""
    padded = _pad(f"  {content}", inner_width - 2)
    return f"{border} {padded} {border}"


def _inner_box_line(content: str, inner_width: int = W2) -> str:
    """Create inner box line: ║    │  content...  │    ║"""
    padded = _pad(f"  {content}", inner_width - 4)
    return f"║    │ {padded} │    ║"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADERS
# ═══════════════════════════════════════════════════════════════════════════════


def _load_metadata(slug: str) -> dict[str, Any]:
    meta_path = MISSION_CONTROL / "mce" / slug / "metadata.yaml"
    if not meta_path.exists():
        return {}
    try:
        import yaml
        with open(meta_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _load_metrics(slug: str) -> dict[str, Any]:
    metrics_path = MISSION_CONTROL / "mce" / slug / "metrics.yaml"
    if not metrics_path.exists():
        return {}
    try:
        import yaml
        with open(metrics_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _load_dna_counts(slug: str) -> dict[str, int]:
    """Load DNA element counts from DNA-CONFIG.yaml."""
    dna_config = ROOT / "knowledge" / "external" / "dna" / "persons" / slug / "DNA-CONFIG.yaml"
    if not dna_config.exists():
        return {}
    try:
        import yaml
        with open(dna_config, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("composition", {})
    except Exception:
        return {}


def _make_tag(slug: str) -> str:
    parts = slug.split("-")
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return slug[:2].upper()


# ═══════════════════════════════════════════════════════════════════════════════
# CHRONICLER COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════


def _super_header(tag: str, person_name: str, status: str, now: str) -> list[str]:
    """Chronicler super_header with solid blocks."""
    title = f"M C E   P I P E L I N E   L O G"
    subtitle = f"{person_name}  ({tag})  ·  {status}  ·  {now}"
    return [
        SOLID_LINE,
        SOLID_LINE,
        f"████{_pad('', W - 8)}████",
        f"████     {_pad(title, W - 14)}████",
        f"████{_pad('', W - 8)}████",
        f"████          ╔{_pad('', 86, '═')}╗          ████",
        f"████          ║  {_pad(subtitle, 84)}║          ████",
        f"████          ╚{_pad('', 86, '═')}╝          ████",
        f"████{_pad('', W - 8)}████",
        SOLID_LINE,
        SOLID_LINE,
    ]


def _section_header(num: int, emoji: str, title: str) -> list[str]:
    """Chronicler section header with ▀ bars."""
    bar = HEADER_BAR * (W - 3)
    return [
        "",
        "",
        f"## {bar}",
        f"## {emoji} SECAO {num}: {title}",
        f"## {bar}",
        "",
    ]


def _changes_box(changes: list[str]) -> list[str]:
    """Chronicler changes box (O QUE MUDOU)."""
    cw = W - 6  # inner width for ┃ padding
    lines = [
        f"┏{'━' * (W - 2)}┓",
        f"┃{_pad('', W - 2)}┃",
        f"┃{_pad('                    O QUE MUDOU NESTA EXECUCAO', W - 2)}┃",
        f"┃{_pad('', W - 2)}┃",
    ]
    for change in changes:
        lines.append(f"┃   {BULLET} {_pad(change, W - 7)}┃")
    lines.append(f"┃{_pad('', W - 2)}┃")
    lines.append(f"┗{'━' * (W - 2)}┛")
    return lines


def _metric_grid(metrics: list[tuple[str, str, str]]) -> list[str]:
    """Chronicler metric_grid: list of (value, label, explanation)."""
    # Calculate card width based on number of metrics (max 4 per row)
    per_row = min(len(metrics), 4)
    card_w = 24
    total_inner = per_row * (card_w + 3) + 1
    grid_w = min(total_inner + 6, W - 4)

    lines = [
        f"╭{'─' * (W - 2)}╮",
        f"│{_pad('                                    📊 PAINEL DE METRICAS', W - 2)}│",
        f"│{_pad('', W - 2)}│",
    ]

    # Build card rows
    for row_start in range(0, len(metrics), 4):
        row = metrics[row_start:row_start + 4]
        # Top borders
        card_tops = "   ".join(f"┌{'─' * card_w}┐" for _ in row)
        lines.append(f"│   {_pad(card_tops, W - 5)}│")
        # Values
        card_vals = "   ".join(f"│{_pad(m[0], card_w, ' ').center(card_w)}│" for m in row)
        lines.append(f"│   {_pad(card_vals, W - 5)}│")
        # Labels
        card_lbls = "   ".join(f"│{_pad(m[1], card_w, ' ').center(card_w)}│" for m in row)
        lines.append(f"│   {_pad(card_lbls, W - 5)}│")
        # Explanations
        card_exps = "   ".join(f"│{_pad('[' + m[2] + ']', card_w, ' ').center(card_w)}│" for m in row)
        lines.append(f"│   {_pad(card_exps, W - 5)}│")
        # Bottom borders
        card_bots = "   ".join(f"└{'─' * card_w}┘" for _ in row)
        lines.append(f"│   {_pad(card_bots, W - 5)}│")

    lines.append(f"│{_pad('', W - 2)}│")
    lines.append(f"╰{'─' * (W - 2)}╯")
    return lines


def _nested_box(title: str, content_lines: list[str]) -> list[str]:
    """Chronicler nested box: double outer + single inner."""
    lines = [
        f"╔{'═' * W1}╗",
        _box_line(""),
        _box_line(f"▸ {title}"),
        _box_line(""),
        f"║    ┌{'─' * W2}┐    ║",
        _box_line(""),
    ]
    for cl in content_lines:
        lines.append(_inner_box_line(cl))
    lines.append(_box_line(""))
    lines.append(f"║    └{'─' * W2}┘    ║")
    lines.append(_box_line(""))
    lines.append(f"╚{'═' * W1}╝")
    return lines


def _chronicler_notes(observations: list[str]) -> list[str]:
    """Chronicler notes section."""
    lines = [
        f"╔{'═' * (W - 2)}╗",
        f"║{_pad('', W - 2)}║",
        f"║{_pad('                         NOTAS DO CHRONICLER', W - 2)}║",
        f"║{_pad('', W - 2)}║",
    ]
    for obs in observations:
        lines.append(f"║   {_pad(obs, W - 5)}║")
    lines.append(f"║{_pad('', W - 2)}║")
    lines.append(f"║{_pad('                                                          — Chronicler', W - 2)}║")
    lines.append(f"║{_pad('', W - 2)}║")
    lines.append(f"╚{'═' * (W - 2)}╝")
    return lines


def _footer(title: str, version: str, date: str) -> list[str]:
    """Chronicler footer with solid blocks."""
    return [
        "",
        SOLID_LINE,
        f"████{_pad('', W - 8)}████",
        f"████{_pad(title.center(W - 8), W - 8)}████",
        f"████{_pad(f'{version} | {date}'.center(W - 8), W - 8)}████",
        f"████{_pad('', W - 8)}████",
        SOLID_LINE,
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════


def generate_mce_log(
    slug: str,
    enrichment_result: dict[str, Any] | None = None,
    agent_trigger_result: dict[str, Any] | None = None,
    cascade_result: dict[str, Any] | None = None,
    sync_result: dict[str, Any] | None = None,
    index_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a Chronicler-formatted log for a completed MCE pipeline run."""
    enrichment_result = enrichment_result or {}
    agent_trigger_result = agent_trigger_result or {}
    cascade_result = cascade_result or {}
    sync_result = sync_result or {}
    index_result = index_result or {}

    tag = _make_tag(slug)
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    person_name = " ".join(w.capitalize() for w in slug.split("-"))

    metadata = _load_metadata(slug)
    metrics = _load_metrics(slug)
    dna = _load_dna_counts(slug)

    # Count insights
    insights_count = 0
    person_insights = 0
    insights_path = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
    if insights_path.exists():
        try:
            data = json.loads(insights_path.read_text(encoding="utf-8"))
            insights_count = data.get("total_insights", len(data.get("insights", [])))
            persons = data.get("persons", {})
            pdata = persons.get(person_name, {})
            if isinstance(pdata, dict):
                pinsights = pdata.get("insights", [])
                person_insights = len(pinsights) if isinstance(pinsights, list) else 0
            elif isinstance(pdata, list):
                person_insights = len(pdata)
        except Exception:
            pass

    # Count chunks
    chunks_count = 0
    chunks_path = ARTIFACTS / "chunks" / "CHUNKS-STATE.json"
    if chunks_path.exists():
        try:
            cdata = json.loads(chunks_path.read_text(encoding="utf-8"))
            chunks_count = len(cdata.get("chunks", []))
        except Exception:
            pass

    appended = enrichment_result.get("appended", 0)
    agents_enriched = enrichment_result.get("agents_enriched", [])
    mode = metadata.get("mode", "unknown")
    source_code = metadata.get("source_code", tag)
    duration = metrics.get("total", {}).get("duration_seconds", 0)
    phases_completed = len(metadata.get("phases_completed", {}))

    cascade_insights = cascade_result.get("insights_processed", 0)
    cargo_updated = cascade_result.get("cargo_agents_updated", 0)
    themes_updated = cascade_result.get("themes_updated", 0)
    themes_created = cascade_result.get("themes_created", 0)

    indexes = index_result.get("indexes", {})
    ext_chunks = indexes.get("external", {}).get("chunks", 0)
    biz_chunks = indexes.get("business", {}).get("chunks", 0)
    graph_entities = indexes.get("graph", {}).get("total_entities", 0)
    graph_edges = indexes.get("graph", {}).get("total_edges", 0)

    synced = sync_result.get("synced", 0)

    fil_count = dna.get("FILOSOFIAS", 0)
    mm_count = dna.get("MODELOS_MENTAIS", 0)
    heu_count = dna.get("HEURISTICAS", 0)
    fw_count = dna.get("FRAMEWORKS", 0)
    met_count = dna.get("METODOLOGIAS", 0)
    dna_total = dna.get("total", fil_count + mm_count + heu_count + fw_count + met_count)

    # ─── BUILD LOG ───

    lines: list[str] = []

    # ── SUPER HEADER ──
    lines.extend(_super_header(tag, person_name, "COMPLETE", now))
    lines.append("")

    # ── CHANGES BOX ──
    changes = [
        f"{person_insights} insights extraidos para {person_name}",
        f"{dna_total} elementos DNA gerados (5 camadas)",
        f"{appended} insights enriquecidos em MEMORY.md de agentes",
        f"{themes_updated + themes_created} dossies tematicos atualizados/criados",
        f"RAG indexes reconstruidos (ext={ext_chunks}, biz={biz_chunks})",
        f"Knowledge graph: {graph_entities} entidades, {graph_edges} arestas",
    ]
    lines.extend(_changes_box(changes))
    lines.append("")

    # ── SECTION 1: EXTRACTION METRICS ──
    lines.extend(_section_header(1, "🧠", "EXTRACTION METRICS"))

    lines.extend(_metric_grid([
        (str(chunks_count), "CHUNKS", "Segmentos semanticos"),
        (str(person_insights), "INSIGHTS", "Conhecimento acionavel"),
        (str(dna_total), "DNA ELEMENTS", "5 camadas cognitivas"),
        (str(phases_completed), "PHASES", "Etapas do pipeline"),
    ]))
    lines.append("")

    # DNA breakdown with progress bars
    if dna_total > 0:
        lines.extend(_nested_box("DNA BREAKDOWN POR CAMADA", [
            f"L1 Filosofias:      {fil_count:>3}  {_bar(fil_count / dna_total * 100 if dna_total else 0, 20)}",
            f"L2 Modelos Mentais: {mm_count:>3}  {_bar(mm_count / dna_total * 100 if dna_total else 0, 20)}",
            f"L3 Heuristicas:     {heu_count:>3}  {_bar(heu_count / dna_total * 100 if dna_total else 0, 20)}  ★★★",
            f"L4 Frameworks:      {fw_count:>3}  {_bar(fw_count / dna_total * 100 if dna_total else 0, 20)}",
            f"L5 Metodologias:    {met_count:>3}  {_bar(met_count / dna_total * 100 if dna_total else 0, 20)}",
            f"",
            f"TOTAL:              {dna_total:>3}  elementos",
        ]))
    lines.append("")

    # ── SECTION 2: MEMORY ENRICHMENT ──
    lines.extend(_section_header(2, "📝", "MEMORY ENRICHMENT"))

    lines.extend(_nested_box("ENRICHMENT RESULTS", [
        f"Insights appended:   {appended}",
        f"Skipped (dedup):     {enrichment_result.get('skipped_dedup', 0)}",
        f"Agents enriched:     {len(agents_enriched)}",
        f"",
        f"Agents:",
    ] + [f"  {BULLET} {a}" for a in agents_enriched]))
    lines.append("")

    # ── SECTION 3: CASCADING ──
    lines.extend(_section_header(3, "🔄", "POST-EXTRACTION CASCADING"))

    lines.extend(_nested_box("CASCADE RESULTS", [
        f"Insights processados:    {cascade_insights}",
        f"Cargo agents encontrados:{cascade_result.get('cargo_agents_found', 0)}",
        f"Cargo agents atualizados:{cargo_updated}",
        f"Temas atualizados:       {themes_updated}",
        f"Temas criados:           {themes_created}",
    ]))
    lines.append("")

    # ── SECTION 4: INDEX REBUILD ──
    lines.extend(_section_header(4, "🔍", "INDEX REBUILD"))

    lines.extend(_metric_grid([
        (str(ext_chunks), "EXTERNAL", "Chunks RAG externos"),
        (str(biz_chunks), "BUSINESS", "Chunks RAG business"),
        (str(graph_entities), "ENTITIES", "Knowledge graph"),
        (str(graph_edges), "EDGES", "Conexoes no grafo"),
    ]))
    lines.append("")

    # ── SECTION 5: WORKSPACE SYNC ──
    lines.extend(_section_header(5, "🏢", "WORKSPACE SYNC"))

    lines.extend(_nested_box("SYNC RESULTS", [
        f"Items sincronizados: {synced}",
        f"Status:              {'✅ Synced' if synced > 0 else '○ Nenhum item novo para sincronizar'}",
    ]))
    lines.append("")

    # ── SECTION 6: META ──
    lines.extend(_section_header(6, "📋", "METADADOS DA EXECUCAO"))

    lines.extend(_nested_box("PIPELINE METADATA", [
        f"Person:          {person_name}",
        f"Slug:            {slug}",
        f"Tag:             {tag}",
        f"Source Code:     {source_code}",
        f"Workflow Mode:   {mode}",
        f"Pipeline Status: COMPLETE",
        f"Duration:        {duration:.1f}s",
        f"Generated:       {now}",
    ]))
    lines.append("")

    # ── SECTION 7: VALIDATION ──
    lines.extend(_section_header(7, "✅", "VALIDATION CHECKLIST"))

    checks = [
        ("CHUNKS-STATE.json", chunks_count > 0, f"{chunks_count} chunks"),
        ("INSIGHTS-STATE.json", person_insights > 0, f"{person_insights} insights"),
        ("DNA Elements", dna_total > 0, f"{dna_total} elementos"),
        ("Memory Enrichment", appended > 0, f"{appended} appended"),
        ("RAG External Index", ext_chunks > 0, f"{ext_chunks} chunks"),
        ("RAG Business Index", biz_chunks > 0, f"{biz_chunks} chunks"),
        ("Knowledge Graph", graph_entities > 0, f"{graph_entities} entities"),
    ]
    check_lines = []
    for name, passed, detail in checks:
        icon = "✅" if passed else "❌"
        check_lines.append(f"{icon} {name:<30} {detail}")
    passed_count = sum(1 for _, p, _ in checks if p)
    total_checks = len(checks)
    check_lines.append("")
    check_lines.append(f"RESULTADO: {passed_count}/{total_checks} checks passed  {_bar(passed_count / total_checks * 100, 20)}")

    lines.extend(_nested_box("VALIDATION GATE", check_lines))
    lines.append("")

    # ── CHRONICLER NOTES ──
    notes = []
    if person_insights >= 20:
        notes.append(f"Extracao rica: {person_insights} insights colocam {person_name} entre as fontes mais densas do sistema.")
    if heu_count >= 3:
        notes.append(f"Destaque: {heu_count} heuristicas com numeros — o tipo mais valioso de DNA cognitivo.")
    if appended > 10:
        notes.append(f"Enrichment robusto: {appended} insights cascateados para MEMORY.md dos agentes.")
    if not notes:
        notes.append(f"Pipeline completo para {person_name}. Todos os artefatos gerados com sucesso.")
    notes.append(f"Versao do log: Chronicler Design System v2.0.0 | log_generator.py v2.0.0")

    lines.extend(_chronicler_notes(notes))

    # ── FOOTER ──
    lines.extend(_footer(
        f"MCE PIPELINE LOG — {person_name} ({tag})",
        "v2.0.0",
        now,
    ))
    lines.append("")

    # ─── WRITE FILE ───

    log_dir = LOGS / "mce" / slug
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"MCE-{tag}.md"

    content = "\n".join(lines)
    try:
        log_path.write_text(content, encoding="utf-8")
        logger.info("MCE log written to %s (%d bytes)", log_path, len(content))
        return {"log_path": str(log_path), "status": "written", "size_bytes": len(content)}
    except Exception as exc:
        logger.warning("Failed to write MCE log: %s", exc)
        return {"error": str(exc)}
