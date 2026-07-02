"""
step_log_renderer.py -- Generic MCE Pipeline Log Renderer
==========================================================

Renders ASCII Chronicler blocks for any pipeline step or microstep.
Does NOT hardcode step behavior — reads PIPELINE-MANIFEST.json to
understand what each step should produce, then compares with what
the StepResult says actually happened.

This means: add a new step or microstep to the pipeline manifest,
and this renderer displays it automatically on next run.

Design principles:
  1. manifest-driven  — knows WHAT via manifest, not hardcode
  2. delta-rendering  — shows expected vs actual (integrity)
  3. generic panels   — metrics/outputs/impacts/alerts render ANY data
  4. identity per bucket — EXTERNAL=gold, BUSINESS=purple, PERSONAL=green
  5. non-fatal        — every function returns fallback on exception

Visual system: Chronicler Design System v3.0 (W=120)
  - Solid block borders: ████ for banners
  - Box-drawing: ╔═╗║╚╝╠╣ for main panels
  - Light box: ┌─┐│└┘├┤ for sub-panels and grids
  - Progress bars: ▓▓▓░░░
  - Bullets: ▸ → ★ ✅ ❌ ⚠️ 🆕 ⚡ ⚔️

Squad codenames (13-agent structure):
  "gate" | "parse" | "canon" | "dig" | "behav" | "psych" | "voice" |
  "guard" | "scribe" | "weave" | "clone" | "index" | "ops"

Version: 1.0.0
Date: 2026-03-28
Design System: CHRONICLER v3.0
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from engine.intelligence.pipeline.mce.pipeline_manifest_builder import manifest_loader
from engine.intelligence.pipeline.mce.step_result import (
    StepAlert,
    StepImpact,
    StepResult,
)

logger = logging.getLogger("mce.step_log_renderer")

# ═══════════════════════════════════════════════════════════════════════════════
# CHRONICLER DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════════════════════

W = 120
W_INNER = W - 4
SEP_D = "═" * (W - 2)
SEP_S = "─" * (W - 2)
SEP_BOLD = "━" * W
SOLID = "█"
BAR_FILL = "▓"
BAR_EMPTY = "░"
BULLET = "▸"
ARROW = "→"

# Bucket visual identity
BUCKET_BANNER_CHAR = {
    "external": "Y",  # gold  — rendered as SOLID blocks
    "business": "P",  # purple
    "personal": "G",  # green
}

BUCKET_LABEL = {
    "external": "EXTERNAL  [Expert Knowledge]",
    "business": "BUSINESS  [Company Operations]",
    "personal": "PERSONAL  [Founder Cognitive]",
}

# Step banners in block letters (full set)
_BANNER_EXTERNAL = [
    "████████╗██╗  ██╗████████╗███████╗██████╗ ███╗   ██╗ █████╗ ██╗",
    "██╔═════╝╚██╗██╔╝╚══██╔══╝██╔════╝██╔══██╗████╗  ██║██╔══██╗██║",
    "█████╗    ╚███╔╝    ██║   █████╗  ██████╔╝██╔██╗ ██║███████║██║",
    "██╔══╝    ██╔██╗    ██║   ██╔══╝  ██╔══██╗██║╚██╗██║██╔══██║██║",
    "████████╗██╔╝ ██╗   ██║   ███████╗██║  ██║██║ ╚████║██║  ██║███████╗",
    "╚═══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝",
]
_BANNER_BUSINESS = [
    "██████╗ ██╗   ██╗███████╗██╗███╗   ██╗███████╗███████╗███████╗",
    "██╔══██╗██║   ██║██╔════╝██║████╗  ██║██╔════╝██╔════╝██╔════╝",
    "██████╔╝██║   ██║███████╗██║██╔██╗ ██║█████╗  ███████╗███████╗",
    "██╔══██╗██║   ██║╚════██║██║██║╚██╗██║██╔══╝  ╚════██║╚════██║",
    "██████╔╝╚██████╔╝███████║██║██║ ╚████║███████╗███████║███████║",
    "╚═════╝  ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚══════╝",
]
_BANNER_PERSONAL = [
    "██████╗ ███████╗██████╗ ███████╗ ██████╗ ███╗   ██╗ █████╗ ██╗",
    "██╔══██╗██╔════╝██╔══██╗██╔════╝██╔═══██╗████╗  ██║██╔══██╗██║",
    "██████╔╝█████╗  ██████╔╝███████╗██║   ██║██╔██╗ ██║███████║██║",
    "██╔═══╝ ██╔══╝  ██╔══██╗╚════██║██║   ██║██║╚██╗██║██╔══██║██║",
    "██║     ███████╗██║  ██║███████║╚██████╔╝██║ ╚████║██║  ██║███████╗",
    "╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝",
]

BUCKET_BANNERS = {
    "external": _BANNER_EXTERNAL,
    "business": _BANNER_BUSINESS,
    "personal": _BANNER_PERSONAL,
}

QUALITY_ICONS = {
    "LEGENDARY": "🏆",
    "EXCELLENT": "⭐",
    "GOOD": "✅",
    "ACCEPTABLE": "🔶",
    "LOW": "⚠️",
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def _pad(text: str, width: int, char: str = " ") -> str:
    text = str(text)
    return text[:width] if len(text) >= width else text + char * (width - len(text))


def _center(text: str, width: int) -> str:
    text = str(text)
    if len(text) >= width:
        return text[:width]
    pad = width - len(text)
    return " " * (pad // 2) + text + " " * (pad - pad // 2)


def _bar(pct: float, width: int = 28) -> str:
    pct = max(0.0, min(100.0, pct))
    filled = int(pct / 100 * width)
    return BAR_FILL * filled + BAR_EMPTY * (width - filled) + f" {int(pct):>3}%"


def _box_line(content: str) -> str:
    return f"║{_pad(f'  {content}', W_INNER)}║"


def _sub_box_line(content: str, w: int = W - 6) -> str:
    return f"│{_pad(f'  {content}', w)}│"


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


# ═══════════════════════════════════════════════════════════════════════════════
# BANNER — bucket-identity + step header
# ═══════════════════════════════════════════════════════════════════════════════


def _build_banner(result: StepResult) -> list[str]:
    """
    Full-width SOLID block banner with bucket identity (color via bucket letter)
    and step information. Microsteps get a compact sub-banner instead.
    """
    try:
        if result.is_microstep():
            return _build_microstep_sub_banner(result)

        bucket = result.bucket.lower()
        banner_lines = BUCKET_BANNERS.get(bucket, _BANNER_EXTERNAL)
        solid = SOLID * W

        step_label = f"Step {result.step_id:02d}/12  ·  {result.step_name}"
        meta_label = f"Squad: {result.squad}  ·  Type: {result.step_type.upper()}"
        source_label = f"Source: {result.slug}"
        status_label = f"Status: {result.status}  ·  {result.timestamp or _now()}"
        if result.duration_seconds > 0:
            status_label += f"  ·  {result.duration_seconds:.1f}s"

        inner_pad = W - 8
        lines = [solid, solid]
        lines.append(f"████{_pad('', W - 8)}████")
        for bl in banner_lines:
            lines.append(f"████  {_pad(bl, inner_pad - 2)}████")
        lines.append(f"████{_pad('', W - 8)}████")
        lines.append(f"████  {_pad(step_label, inner_pad - 2)}████")
        lines.append(f"████          ╔{_pad('', W - 22, '═')}╗          ████")
        lines.append(f"████          ║  {_pad(meta_label,   W - 28)}  ║          ████")
        lines.append(f"████          ║  {_pad(source_label, W - 28)}  ║          ████")
        lines.append(f"████          ║  {_pad(status_label, W - 28)}  ║          ████")
        lines.append(f"████          ╚{_pad('', W - 22, '═')}╝          ████")
        lines.append(f"████{_pad('', W - 8)}████")
        lines.extend([solid, solid])
        return lines
    except Exception as exc:
        logger.debug("_build_banner error: %s", exc)
        return [SOLID * W, f"  STEP {result.step_id} — {result.slug} — {result.status}", SOLID * W]


def _build_microstep_sub_banner(result: StepResult) -> list[str]:
    """Compact banner for microsteps — no block letters, just a bordered header."""
    label = f"  {result.microstep_id}  {result.microstep_name or ''}  ·  {result.squad}  ·  {result.status}"
    return [
        "",
        f"┌{'━' * (W - 2)}┐",
        f"┃{_pad(label, W - 2)}┃",
        f"└{'━' * (W - 2)}┘",
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# QUALITY SCORE
# ═══════════════════════════════════════════════════════════════════════════════


def _render_quality(result: StepResult) -> list[str]:
    if not result.quality_score:
        return []
    icon = QUALITY_ICONS.get(result.quality_score, "")
    roi_str = f"  ·  ROI: {result.quality_roi:.2f}" if result.quality_roi else ""
    label = f"  {icon}  {result.quality_score}{roi_str}"
    return [
        "",
        f"╔{SEP_D}╗",
        f"║{_pad('  🏆 QUALITY SCORE', W_INNER)}║",
        f"╠{SEP_D}╣",
        _box_line(label),
        f"╚{SEP_D}╝",
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS — generic, renders any dict
# ═══════════════════════════════════════════════════════════════════════════════


def _render_metrics_generic(result: StepResult, step_spec: dict) -> list[str]:
    """
    Render any metrics dict from StepResult.
    For known sub-dicts (by_tag, by_type, etc.) renders as progress bars.
    For simple k/v renders as two-column grid.
    Unknown keys render generically — new microsteps get full rendering
    without any code change here.
    """
    if not result.metrics:
        return []

    step_name = result.microstep_name or result.step_name
    lines = [
        "",
        f"╔{SEP_D}╗",
        _box_line(f"  {step_name}  ·  {result.slug}"),
        f"╠{SEP_D}╣",
        _box_line(""),
    ]

    flat: dict[str, Any] = {}
    sub_dicts: dict[str, dict] = {}
    sub_lists: dict[str, list] = {}

    for k, v in result.metrics.items():
        if isinstance(v, dict):
            sub_dicts[k] = v
        elif isinstance(v, list):
            sub_lists[k] = v
        else:
            flat[k] = v

    # Flat metrics — two column
    flat_items = list(flat.items())
    for i in range(0, len(flat_items), 2):
        left_k, left_v = flat_items[i]
        left_str = f"{left_k}: {left_v}"
        if i + 1 < len(flat_items):
            right_k, right_v = flat_items[i + 1]
            right_str = f"{right_k}: {right_v}"
            half = (W_INNER - 4) // 2
            row = _pad(left_str, half) + "   " + right_str
        else:
            row = left_str
        lines.append(_box_line(row))

    # Sub-dicts as progress bars (by_tag, by_type, etc.)
    total_for_pct = flat.get("total_insights", flat.get("total", flat.get("count", 0)))
    for sub_k, sub_v in sub_dicts.items():
        lines.append(_box_line(""))
        lines.append(_box_line(f"  {sub_k}:"))
        sub_total = (
            sum(sub_v.values()) if all(isinstance(x, (int, float)) for x in sub_v.values()) else 1
        )
        use_total = total_for_pct if total_for_pct else sub_total
        for tag, count in sub_v.items():
            pct = (count / use_total * 100) if use_total else 0
            star = "  ★★★" if pct >= 30 else ""
            lines.append(
                _box_line(
                    f"    [{tag}]{_pad('', 18 - min(len(tag), 18))}: {count:>4}  {_bar(pct, 20)}{star}"
                )
            )

    # Sub-lists as bullet items
    for list_k, list_v in sub_lists.items():
        lines.append(_box_line(""))
        lines.append(_box_line(f"  {list_k} ({len(list_v)}):"))
        for item in list_v[:6]:
            lines.append(_box_line(f"    {BULLET} {item}"))
        if len(list_v) > 6:
            lines.append(_box_line(f"    (+{len(list_v) - 6} more)"))

    lines.append(_box_line(""))
    lines.append(f"╚{SEP_D}╝")
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRITY — manifest vs reality comparison
# ═══════════════════════════════════════════════════════════════════════════════


def _render_integrity(result: StepResult, step_spec: dict) -> list[str]:
    """
    Compares what the manifest says should exist with what StepResult reports.
    This is where digest errors and partial executions become visible.
    """
    expected = step_spec.get("expected_artifacts", [])
    if not expected and not result.artifacts_expected:
        return []

    expected_count = result.artifacts_expected or len(expected)
    found_count = result.artifacts_found
    missing = result.artifacts_missing

    if expected_count == 0:
        return []

    pct = (
        result.integrity_pct
        if result.integrity_pct != 100.0
        else ((found_count / expected_count * 100) if expected_count else 100.0)
    )

    status_icon = "✅" if pct >= 100 else ("⚠️" if pct >= 50 else "❌")

    lines = [
        "",
        f"┌{SEP_S}┐",
        _sub_box_line(f"  🔬 INTEGRIDADE DO STEP  ·  {status_icon}  {pct:.0f}%"),
        f"├{SEP_S}┤",
        _sub_box_line(
            f"  Artefatos esperados: {expected_count}  ·  Encontrados: {found_count}  ·  Ausentes: {len(missing)}"
        ),
        _sub_box_line(f"  {_bar(pct, 40)}"),
    ]

    if result.digest_error:
        lines.append(_sub_box_line(""))
        lines.append(_sub_box_line("  ❌ ERRO DE DIGESTÃO DETECTADO"))
        lines.append(_sub_box_line(f"     {result.digest_error_detail}"))
        lines.append(
            _sub_box_line("     Pipeline interrompida parcialmente — pode retomar com resume")
        )

    if missing:
        lines.append(_sub_box_line(""))
        lines.append(_sub_box_line("  Artefatos ausentes:"))
        for m in missing[:5]:
            lines.append(_sub_box_line(f"    ❌ {m}"))

    lines.append(f"└{SEP_S}┘")
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# OUTPUTS — generic, renders any list[StepOutput]
# ═══════════════════════════════════════════════════════════════════════════════


def _render_outputs_generic(result: StepResult) -> list[str]:
    if not result.outputs:
        return []

    lines = [
        "",
        f"┌{SEP_S}┐",
        _sub_box_line("  📦 OUTPUTS PRODUZIDOS"),
        f"├{SEP_S}┤",
    ]
    for out in result.outputs:
        icon = (
            "🆕"
            if "new" in out.output_type.lower() or "created" in out.output_type.lower()
            else "✅"
            if "artifact" in out.output_type
            else "🔗"
            if "linked" in out.output_type
            else "🆕"
            if out.highlight
            else "▸"
        )
        star = "  ★" if out.highlight else ""
        chunk_str = (
            f"  [chunks: {', '.join(out.chunk_ids[:3])}{'...' if len(out.chunk_ids) > 3 else ''}]"
            if out.chunk_ids
            else ""
        )
        lines.append(
            _sub_box_line(f"  {icon}  {out.label:<30}  {str(out.value)[:45]}{star}{chunk_str}")
        )
    lines.append(f"└{SEP_S}┘")
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# IMPACTS — cascading chain
# ═══════════════════════════════════════════════════════════════════════════════


def _render_impacts_generic(result: StepResult) -> list[str]:
    if not result.impacts:
        return []

    lines = [
        "",
        f"╔{SEP_D}╗",
        _box_line("  🔄 CADEIA DE CASCATEAMENTO"),
        f"╠{SEP_D}╣",
        _box_line(""),
    ]

    # Group by bucket
    by_bucket: dict[str, list[StepImpact]] = {
        "external": [],
        "business": [],
        "personal": [],
        "other": [],
    }
    for imp in result.impacts:
        bucket = imp.bucket.lower() if imp.bucket else "other"
        by_bucket.setdefault(bucket, []).append(imp)

    for bucket, impacts in by_bucket.items():
        if not impacts:
            continue
        label = BUCKET_LABEL.get(bucket, bucket.upper())
        lines.append(_box_line(f"  {label}"))
        for imp in impacts:
            cross = "  ← cross-bucket" if imp.is_cross_bucket else ""
            bar_w = min(imp.count * 2, 40)
            bar_str = BAR_FILL * bar_w + f"  {imp.count} {imp.impact_type}"
            lines.append(_box_line(f"    {imp.target[:45]:<45}  {bar_str}{cross}"))

    # Rastreabilidade
    lines.append(_box_line(""))
    lines.append(_box_line("  RASTREABILIDADE:"))
    # Show first few source chunk_ids → targets
    for imp in result.impacts[:3]:
        lines.append(_box_line(f"    SOURCE → chunk_id → insight_id → {imp.target}"))

    lines.append(_box_line(""))
    lines.append(f"╚{SEP_D}╝")
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# BUCKET PANEL — 3-column routing with intersections
# ═══════════════════════════════════════════════════════════════════════════════


def _render_bucket_panel(result: StepResult) -> list[str]:
    col_w = (W - 8) // 3
    remainder = W - 2 - 2 * col_w

    def cell_line(label: str, value: Any, is_primary: bool, w: int) -> str:
        marker = " ★" if is_primary and value not in (0, "—", None) else ""
        return _center(f"{label}: {value}{marker}", w)

    ext = result.bucket_external
    biz = result.bucket_business
    per = result.bucket_personal
    primary = result.bucket.lower()

    lines = [
        "",
        f"╔{SEP_D}╗",
        _box_line("  🗂️  KNOWLEDGE ROUTING — 3 BUCKETS"),
        f"╠{'═' * col_w}╦{'═' * col_w}╦{'═' * remainder}╣",
        f"║{_center('EXTERNAL', col_w)}║{_center('BUSINESS', col_w)}║{_pad(_center('PERSONAL', remainder), remainder)}║",
        f"║{_center('[Expert Knowledge]', col_w)}║{_center('[Company Ops]', col_w)}║{_pad(_center('[Founder Cognitive]', remainder), remainder)}║",
        f"╠{'═' * col_w}╬{'═' * col_w}╬{'═' * remainder}╣",
    ]

    for label, e_v, b_v, p_v in [
        ("Arquivos", ext.files, biz.files, per.files),
        ("Chunks", ext.chunks, biz.chunks, per.chunks),
        ("Insights", ext.insights, biz.insights, per.insights),
        (
            "Conf.",
            f"{ext.confidence:.0f}%" if ext.confidence else "—",
            f"{biz.confidence:.0f}%" if biz.confidence else "—",
            f"{per.confidence:.0f}%" if per.confidence else "—",
        ),
    ]:
        ec = cell_line(label, e_v, primary == "external", col_w)
        bc = cell_line(label, b_v, primary == "business", col_w)
        pc = cell_line(label, p_v, primary == "personal", remainder)
        lines.append(f"║{ec}║{bc}║{_pad(pc, remainder)}║")

    lines.append(f"╠{'═' * col_w}╩{'═' * col_w}╩{'═' * remainder}╣")
    mode_line = f"  {BULLET} Bucket primário: {primary.upper()}  ·  Routing: {result.routing_mode}"
    lines.append(_box_line(mode_line))

    if result.bucket_intersections:
        lines.append(_box_line(""))
        lines.append(_box_line(f"  {BULLET} INTERSECÇÕES DETECTADAS (cross-bucket cascade):"))
        for ix in result.bucket_intersections[:6]:
            lines.append(_box_line(f"    {ARROW} {ix}"))
    else:
        lines.append(_box_line(f"  {BULLET} Sem intersecções nesta fase"))

    lines.append(_box_line(""))
    lines.append(f"╚{SEP_D}╝")
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# ALERTS — role tracking, conflicts, anomalias, decisions
# ═══════════════════════════════════════════════════════════════════════════════


def _render_alerts_generic(result: StepResult) -> list[str]:
    if not result.alerts:
        return []

    # Group by category
    by_cat: dict[str, list[StepAlert]] = {}
    for alert in result.alerts:
        by_cat.setdefault(alert.category, []).append(alert)

    lines: list[str] = []

    # Role tracking / new cargo
    cargo_alerts = by_cat.get("new_cargo", []) + by_cat.get("threshold", [])
    if cargo_alerts:
        lines += [
            "",
            f"╔{SEP_D}╗",
            _box_line("  🚨 ROLE TRACKING — GATILHOS DE AGENTES"),
            f"╠{SEP_D}╣",
            _box_line(""),
        ]
        for a in cargo_alerts:
            icon = "🆕" if "novo" in a.message.lower() or "new" in a.message.lower() else "⚡"
            lines.append(_box_line(f"  {icon}  {a.message}"))
            if a.detail:
                lines.append(_box_line(f"       {a.detail}"))
            lines.append(
                _box_line(
                    f"       Reversível: {'Sim' if a.reversible else 'Não'}  ·  Ação: {'NECESSÁRIA ⚠️' if a.action_required else 'Automática ✅'}"
                )
            )
        lines += [_box_line(""), f"╚{SEP_D}╝"]

    # Conflicts
    conflict_alerts = by_cat.get("conflict", [])
    if conflict_alerts:
        lines += [
            "",
            f"╔{SEP_D}╗",
            _box_line("  ⚔️  CONFLITOS CROSS-SOURCE"),
            f"╠{SEP_D}╣",
            _box_line(""),
        ]
        for a in conflict_alerts:
            level_icon = "🔴" if a.level == "critical" else ("🟡" if a.level == "warn" else "🟢")
            lines.append(_box_line(f"  {level_icon}  {a.message}"))
            if a.detail:
                lines.append(_box_line(f"       {a.detail}"))
            action_str = (
                "⚠️ PENDENTE RESOLUÇÃO HUMANA"
                if a.action_required
                else "✅ Resolvido automaticamente"
            )
            lines.append(_box_line(f"       Status: {action_str}"))
        lines += [_box_line(""), f"╚{SEP_D}╝"]

    # Auto decisions
    decision_alerts = by_cat.get("decision_auto", [])
    if decision_alerts:
        lines += [
            "",
            f"╔{SEP_D}╗",
            _box_line("  🧠 DECISÕES AUTOMÁTICAS JARVIS"),
            f"╠{SEP_D}╣",
            _box_line(""),
        ]
        for a in decision_alerts:
            lines.append(_box_line(f"  •  {a.message}"))
            if a.detail:
                lines.append(_box_line(f"     Motivo: {a.detail}"))
            lines.append(_box_line(f"     Reversível: {'Sim' if a.reversible else 'Não'}"))
        lines += [_box_line(""), f"╚{SEP_D}╝"]

    # Anomalias / digest errors
    anomaly_alerts = by_cat.get("anomaly", []) + by_cat.get("digest_error", [])
    if anomaly_alerts:
        lines += [
            "",
            f"╔{SEP_D}╗",
            _box_line("  ⚠️  ANOMALIAS & RESOLUÇÕES"),
            f"╠{SEP_D}╣",
            _box_line(""),
        ]
        for a in anomaly_alerts:
            icon = "❌" if a.level == "critical" else "⚠️"
            lines.append(_box_line(f"  {icon}  {a.message}"))
            if a.detail:
                lines.append(_box_line(f"     {a.detail}"))
        lines += [_box_line(""), f"╚{SEP_D}╝"]

    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# THEMES PANEL
# ═══════════════════════════════════════════════════════════════════════════════


def _render_themes_panel(result: StepResult) -> list[str]:
    themes = result.metrics.get("themes_detected", {})
    if not themes:
        return []

    primary = themes.get("primary", [])
    secondary = themes.get("secondary", [])
    new = themes.get("new", [])
    cross = themes.get("cross_source", [])
    total = len(primary) + len(secondary) + len(new)

    if total == 0:
        return []

    lines = [
        "",
        f"╔{SEP_D}╗",
        _box_line(
            f"  🏷️  TEMAS DETECTADOS — {total} total  ({len(new)} novos · {len(primary) + len(secondary)} consolidados)"
        ),
        f"╠{SEP_D}╣",
        _box_line(""),
    ]

    half = (W_INNER - 6) // 2
    # Primary + secondary as two columns
    for i in range(max(len(primary), len(secondary))):
        p = f"▸ {primary[i]}" if i < len(primary) else ""
        s = f"▸ {secondary[i]}" if i < len(secondary) else ""
        lines.append(_box_line(f"  {_pad(p, half)}  {s}"))

    if new:
        lines.append(_box_line(""))
        lines.append(_box_line(f"  NOVOS NESTA EXECUÇÃO ({len(new)}):"))
        for n in new:
            lines.append(_box_line(f"    🆕 {n}"))

    if cross:
        lines.append(_box_line(""))
        cross_str = " · ".join(cross[:4])
        lines.append(_box_line(f"  CROSS-SOURCE: {cross_str}"))

    lines += [_box_line(""), f"╚{SEP_D}╝"]
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# IMPACT PREVIEW GRIDS — 4 grids
# ═══════════════════════════════════════════════════════════════════════════════


def _render_impact_preview(result: StepResult) -> list[str]:
    preview = result.metrics.get("impact_preview", {})
    if not preview:
        return []

    temas = preview.get("temas", [])
    dossiers = preview.get("dossiers", [])
    agents = preview.get("agents", [])
    cargos = preview.get("new_cargos", [])

    if not any([temas, dossiers, agents, cargos]):
        return []

    col_w = (W - 8) // 4

    lines = [
        "",
        f"╔{SEP_D}╗",
        _box_line("  📋 PREVIEW DE IMPACTO — O que acontece com esses dados"),
        f"╠{SEP_D}╣",
        _box_line(""),
    ]

    headers = [
        f"TEMAS ({len(temas)})",
        f"DOSSIÊS ({len(dossiers)})",
        f"AGENTES ({len(agents)})",
        f"CARGOS NOVOS ({len(cargos)})",
    ]
    h_row = "".join(_center(h, col_w) for h in headers)
    lines.append(_box_line(h_row))
    lines.append(_box_line("  " + ("─" * (col_w - 1) + "  ") * 4))

    max_rows = max(len(temas), len(dossiers), len(agents), len(cargos), 0)
    for i in range(min(max_rows, 6)):
        t = temas[i] if i < len(temas) else ""
        d = dossiers[i] if i < len(dossiers) else ""
        a = agents[i] if i < len(agents) else ""
        c = cargos[i] if i < len(cargos) else ""
        row = (
            _center(str(t)[: col_w - 2], col_w)
            + _center(str(d)[: col_w - 2], col_w)
            + _center(str(a)[: col_w - 2], col_w)
            + _center(str(c)[: col_w - 2], col_w)
        )
        lines.append(_box_line(row))

    lines += [_box_line(""), f"╚{SEP_D}╝"]
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# CANONICAL MAP UPDATE
# ═══════════════════════════════════════════════════════════════════════════════


def _render_canonical_map(result: StepResult) -> list[str]:
    new_entities = result.metrics.get("new_canonical_entities", [])
    if not new_entities:
        return []

    lines = [
        "",
        f"╔{SEP_D}╗",
        _box_line(f"  🗺️  CANONICAL MAP UPDATE ({len(new_entities)} novas entidades)"),
        f"╠{SEP_D}╣",
        _box_line(""),
        _box_line(f"  {'Tipo':<12}  {'Canonical':<20}  Aliases Detectados"),
        _box_line(
            f"  {'────────────':<12}  {'────────────────────':<20}  ────────────────────────────────────"
        ),
    ]
    for ent in new_entities[:8]:
        ent_type = ent.get("type", "?")[:12]
        canonical = ent.get("canonical", "?")[:20]
        aliases = ", ".join(ent.get("aliases", [])[:4])
        lines.append(_box_line(f"  {ent_type:<12}  {canonical:<20}  {aliases}"))
    lines += [_box_line(""), f"╚{SEP_D}╝"]
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# ACCUMULATED SOURCE + MISSION
# ═══════════════════════════════════════════════════════════════════════════════


def _render_accumulated(result: StepResult) -> list[str]:
    acc_source = result.metrics.get("accumulated_source", {})
    acc_mission = result.metrics.get("accumulated_mission", {})

    if not acc_source and not acc_mission:
        return []

    lines: list[str] = []
    half = (W_INNER - 6) // 2

    if acc_source:
        slug_name = acc_source.get("name", result.slug)
        lines += [
            "",
            f"╔{SEP_D}╗",
            _box_line(f"  📊 ACUMULADO SOURCE: {slug_name.upper()}"),
            f"╠{'═' * half}╦{'═' * (W_INNER - 2 - half)}╣",
        ]
        left_items = [
            ("Arquivos", acc_source.get("files", "?")),
            ("Insights", acc_source.get("insights", "?")),
            ("Heurísticas", str(acc_source.get("heuristicas", "?")) + " ★"),
            ("Frameworks", acc_source.get("frameworks", "?")),
            ("Conflitos", acc_source.get("conflitos", "?")),
            ("ETA", acc_source.get("eta", "?")),
        ]
        dna = acc_source.get("dna_preview", {})
        dna_items = list(dna.items()) if dna else []

        max_rows = max(len(left_items), len(dna_items))
        for i in range(max_rows):
            left_str = ""
            right_str = ""
            if i < len(left_items):
                lk, lv = left_items[i]
                left_str = f"  {lk}: {lv}"
            if i < len(dna_items):
                dk, dv = dna_items[i]
                pct = dv / max(sum(dna.values()), 1) * 100
                right_str = f"  {dk}: {dv}  {_bar(pct, 16)}"
            left_cell = _pad(left_str, half)
            right_cell = _pad(right_str, W_INNER - 2 - half)
            lines.append(f"║{left_cell}║{right_cell}║")

        lines.append(f"╚{SEP_D}╝")

    if acc_mission:
        lines += [
            "",
            f"╔{SEP_D}╗",
            _box_line("  📈 ACUMULADO MISSÃO"),
            f"╠{SEP_D}╣",
            _box_line(""),
        ]
        items = [
            ("Arquivos", acc_mission.get("files", "?"), acc_mission.get("files_pct", 0)),
            ("Chunks", acc_mission.get("chunks", "?"), acc_mission.get("chunks_pct", 0)),
            ("Insights", acc_mission.get("insights", "?"), acc_mission.get("insights_pct", 0)),
            ("Heurísticas", acc_mission.get("heuristicas", "?"), acc_mission.get("heur_pct", 0)),
            ("Frameworks", acc_mission.get("frameworks", "?"), acc_mission.get("fw_pct", 0)),
            ("Dossiês", acc_mission.get("dossiers", "?"), acc_mission.get("dossiers_pct", 0)),
            ("Agentes", acc_mission.get("agents", "?"), acc_mission.get("agents_pct", 0)),
            ("Batches", acc_mission.get("batches", "?"), acc_mission.get("batches_pct", 0)),
        ]
        half_m = (W_INNER - 6) // 2
        for i in range(0, len(items), 2):
            lk, lv, lp = items[i]
            left_str = f"  {lk:<12}  {lv!s:<8}  {_bar(lp, 20)}"
            right_str = ""
            if i + 1 < len(items):
                rk, rv, rp = items[i + 1]
                right_str = f"  {rk:<12}  {rv!s:<8}  {_bar(rp, 20)}"
            row = _pad(left_str, half_m) + "   " + right_str
            lines.append(_box_line(row))

        lines += [_box_line(""), f"╚{SEP_D}╝"]

    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# QA GATE PANEL
# ═══════════════════════════════════════════════════════════════════════════════


def _render_qa_gate(result: StepResult, step_spec: dict) -> list[str]:
    checkpoints = result.checkpoints or step_spec.get("checkpoints", [])
    gate_spec = step_spec.get("quality_gate", {})

    if not checkpoints and not gate_spec:
        return []

    passed = sum(1 for c in checkpoints if c.get("passed", True))
    total = len(checkpoints)
    pct = (passed / total * 100) if total else 100
    gate_id = gate_spec.get("id", f"MCE-QG-{result.step_id}")
    gate_name = gate_spec.get("name", "")
    gate_status = "OPEN ✅" if pct >= 100 else ("WARN ⚠️" if pct >= 50 else "BLOCKED ❌")

    lines = [
        "",
        f"╔{SEP_D}╗",
        _box_line(f"  ✅ QA GATE · {gate_id}{' · ' + gate_name if gate_name else ''}"),
        f"╠{SEP_D}╣",
        _box_line(""),
    ]

    for cp in checkpoints[:8]:
        icon = "✅" if cp.get("passed", True) else ("❌" if cp.get("blocking") else "⚠️")
        cp_id = cp.get("id", "?")
        desc = cp.get("description", "?")[:70]
        lines.append(_box_line(f"  {icon}  {cp_id:<18}  {desc}"))

    if total > 8:
        lines.append(_box_line(f"  ... (+{total - 8} more checkpoints)"))

    lines.append(_box_line(""))
    lines.append(
        _box_line(f"  Resultado: {passed}/{total} checks  {_bar(pct, 30)}  ·  Gate: {gate_status}")
    )
    lines.append(_box_line(""))
    lines.append(f"╚{SEP_D}╝")
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PROGRESS
# ═══════════════════════════════════════════════════════════════════════════════


def _render_pipeline_progress(result: StepResult) -> list[str]:
    manifest = manifest_loader.get()
    total = manifest.get("_meta", {}).get("total_steps", 12)
    step_id = result.step_id
    pct = (step_id / total) * 100

    done = " ".join(f"[✓]S{i:02d}" for i in range(1, step_id))
    now_ = f"[→]S{step_id:02d} {result.step_name}"
    ahead = " ".join(f"[ ]S{i:02d}" for i in range(step_id + 1, min(step_id + 4, total + 1)))

    return [
        "",
        f"╔{SEP_D}╗",
        _box_line(f"  PIPELINE PROGRESS  ·  {step_id}/{total} steps  ·  {_bar(pct, 40)}"),
        f"╠{SEP_D}╣",
        _box_line(f"  {done}  {now_}  {ahead}"),
        f"╚{SEP_D}╝",
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# CHRONICLER NOTE
# ═══════════════════════════════════════════════════════════════════════════════


def _render_chronicler(note: str) -> list[str]:
    if not note:
        return []
    return [
        "",
        f"╔{SEP_D}╗",
        _box_line("  🖋️  CHRONICLER"),
        f"╠{SEP_D}╣",
        _box_line(f'  "{note}"'),
        f"╚{SEP_D}╝",
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════


def _build_footer(result: StepResult) -> list[str]:
    step_label = f"MCE · {result.bucket.upper()} · STEP {result.step_id:02d}"
    if result.is_microstep():
        step_label += f" · {result.microstep_id}"
    step_label += f" · {result.slug.upper()} · {result.status}"
    ts = result.timestamp or _now()
    solid = SOLID * W
    return [
        "",
        solid,
        f"████  {_pad(step_label, W - 12)}  ████",
        f"████  {_pad(f'Chronicler Design System v3.0  ·  {ts}', W - 12)}  ████",
        solid,
        "",
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════


def render_step_block(result: StepResult) -> str:
    """
    Render a complete ASCII log block for any step or microstep.

    Flow:
        1. Load step spec from manifest (what SHOULD exist)
        2. Build banner (bucket identity)
        3. Quality score (if present)
        4. Integrity check (spec vs reality)
        5. Metrics panel (generic — any dict renders)
        6. Outputs panel (generic — any list renders)
        7. Themes panel (if themes in metrics)
        8. Role tracking / alerts (generic — any alert category renders)
        9. Impact preview grids
        10. Canonical map updates
        11. Cascading chain (impacts)
        12. Bucket routing panel
        13. Accumulated source + mission
        14. QA gate
        15. Pipeline progress bar
        16. Chronicler note
        17. Footer

    Adding a new step or microstep to the manifest means it renders
    automatically here — no code change needed.
    """
    try:
        if not result.timestamp:
            result.timestamp = _now()

        # Load step spec from manifest
        if result.is_microstep():
            step_spec = manifest_loader.microstep(result.step_id, result.microstep_id or "")
        else:
            step_spec = manifest_loader.step(result.step_id)

        # Fill missing step metadata from manifest
        if not result.step_name and step_spec:
            result.step_name = step_spec.get("name", f"STEP {result.step_id}")
        if not result.step_type and step_spec:
            result.step_type = step_spec.get("type", "?")
        if not result.squad and step_spec:
            result.squad = step_spec.get("squad", "—")

        lines: list[str] = []

        # 1. Banner
        lines.extend(_build_banner(result))
        lines.append("")

        # 2. Quality score
        if result.quality_score:
            lines.extend(_render_quality(result))

        # 3. Integrity (spec vs reality)
        if step_spec and (result.artifacts_expected or step_spec.get("expected_artifacts")):
            lines.extend(_render_integrity(result, step_spec))

        # 4. Metrics (generic)
        if result.metrics:
            lines.extend(_render_metrics_generic(result, step_spec))

        # 5. Outputs
        if result.outputs:
            lines.extend(_render_outputs_generic(result))

        # 6. Themes
        if result.metrics.get("themes_detected"):
            lines.extend(_render_themes_panel(result))

        # 7. Alerts (role tracking, conflicts, decisions, anomalies)
        if result.alerts:
            lines.extend(_render_alerts_generic(result))

        # 8. Impact preview grids
        if result.metrics.get("impact_preview"):
            lines.extend(_render_impact_preview(result))

        # 9. Canonical map
        if result.metrics.get("new_canonical_entities"):
            lines.extend(_render_canonical_map(result))

        # 10. Cascading chain
        if result.impacts:
            lines.extend(_render_impacts_generic(result))

        # 11. Bucket routing
        if any(
            [
                result.bucket_external.files,
                result.bucket_business.files,
                result.bucket_personal.files,
                result.bucket_intersections,
            ]
        ):
            lines.extend(_render_bucket_panel(result))

        # 12. Accumulated source + mission
        if result.metrics.get("accumulated_source") or result.metrics.get("accumulated_mission"):
            lines.extend(_render_accumulated(result))

        # 13. QA Gate
        if result.checkpoints or step_spec.get("quality_gate"):
            lines.extend(_render_qa_gate(result, step_spec))

        # 14. Pipeline progress
        if not result.is_microstep():
            lines.extend(_render_pipeline_progress(result))

        # 15. Chronicler
        if result.chronicler_note:
            lines.extend(_render_chronicler(result.chronicler_note))

        # 16. Footer
        lines.extend(_build_footer(result))

        return "\n".join(lines)

    except Exception as exc:
        logger.warning("render_step_block failed step=%s: %s", result.step_id, exc)
        return f"\n{'─' * W}\n  [STEP {result.step_id}] {result.slug} — {result.status} — render error: {exc}\n{'─' * W}\n"


# ═══════════════════════════════════════════════════════════════════════════════
# BRIEFING RENDERER (Tipo 2 — session consolidation)
# ═══════════════════════════════════════════════════════════════════════════════


def render_briefing(  # DEPRECATED -- use render_pipeline_audit
    session_data: dict[str, Any],
    step_entries: list[dict[str, Any]],
) -> str:
    """
    Render the Jarvis Briefing — consolidated session log.

    .. deprecated::
        Use :func:`pipeline_audit_renderer.render_pipeline_audit` instead.
        This function is preserved for backward compatibility and will be
        removed in a future version.

    Shows only the buckets that were actually active (1, 2, or 3).
    Each active bucket gets a medium-sized block letter banner + metrics.
    Non-active buckets are omitted entirely.
    Cross-bucket intersections rendered at the end.
    """
    import warnings

    warnings.warn(
        "render_briefing is deprecated; use render_pipeline_audit",
        DeprecationWarning,
        stacklevel=2,
    )
    try:
        now = _now()
        solid = SOLID * W
        lines: list[str] = []

        # ── BRIEFING HEADER ──────────────────────────────────────────────────
        slugs = session_data.get("slugs_processed", [])
        active_bkts = session_data.get("active_buckets", ["external"])
        steps_total = session_data.get("total_steps", 0)
        agents_cnt = session_data.get("agents_count", 0)
        dossiers_cnt = session_data.get("dossiers_count", 0)
        new_cargos = session_data.get("new_cargos", [])
        conflicts_pending = session_data.get("conflicts_pending", [])
        duration = session_data.get("duration_seconds", 0)

        bkt_str = " + ".join(b.upper() for b in active_bkts)
        subtitle = (
            f"Sessão: {now}  ·  {len(slugs)} fontes  ·  {len(active_bkts)} bucket(s): {bkt_str}"
        )

        lines += [
            solid,
            solid,
            f"████{_pad('', W - 8)}████",
            f"████     J  A  R  V  I  S     B  R  I  E  F  I  N  G{_pad('', W - 56)}████",
            f"████{_pad('', W - 8)}████",
            f"████          ╔{_pad('', W - 22, '═')}╗          ████",
            f"████          ║  {_pad(subtitle, W - 28)}  ║          ████",
            f"████          ╚{_pad('', W - 22, '═')}╝          ████",
            f"████{_pad('', W - 8)}████",
            solid,
            solid,
            "",
        ]

        # ── SESSION SUMMARY ──────────────────────────────────────────────────
        summary_line = (
            f"  Agentes: {agents_cnt}  ·  Dossiês: {dossiers_cnt}  ·  "
            f"Steps: {steps_total}  ·  Duração: {duration:.0f}s"
        )
        if new_cargos:
            summary_line += f"  ·  Novos cargos: {', '.join(new_cargos)}"
        if conflicts_pending:
            summary_line += f"  ·  ⚠️ Conflitos pendentes: {len(conflicts_pending)}"

        lines += [
            f"╔{SEP_D}╗",
            _box_line(summary_line),
            f"╚{SEP_D}╝",
            "",
        ]

        # ── PER-BUCKET BLOCKS ─────────────────────────────────────────────────
        # Group step_entries by bucket
        from collections import defaultdict

        by_bucket: dict[str, list] = defaultdict(list)
        for entry in step_entries:
            b = entry.get("bucket", "external").lower()
            by_bucket[b].append(entry)

        for bucket in active_bkts:
            entries = by_bucket.get(bucket, [])
            bucket_banner = BUCKET_BANNERS.get(bucket, _BANNER_EXTERNAL)

            # Group entries by slug within this bucket
            by_slug: dict[str, list] = defaultdict(list)
            for e in entries:
                by_slug[e.get("slug", "unknown")].append(e)

            # Compact banner for this bucket
            lines += [""]
            lines += [f"╔{SEP_D}╗"]
            for bl in bucket_banner:
                lines += [_box_line(bl)]
            n_sources = len(by_slug)
            lines += [
                _box_line(""),
                _box_line(f"  [ {n_sources} fonte(s) ]"),
                f"╠{SEP_D}╣",
            ]

            # Per-slug within this bucket
            for slug, slug_entries in by_slug.items():
                steps_done = sorted(
                    {e.get("step", -1) for e in slug_entries if isinstance(e.get("step"), int)}
                )
                max_step = max(steps_done) if steps_done else 0
                total_m = manifest_loader.get().get("_meta", {}).get("total_steps", 12)
                pct = (max_step / total_m) * 100

                status_str = (
                    "✅ COMPLETO"
                    if max_step >= total_m
                    else f"⚡ em andamento — próximo: Step {max_step + 1}"
                )
                quality = slug_entries[-1].get("quality_score", "") if slug_entries else ""
                quality_str = f"  ·  {QUALITY_ICONS.get(quality, '')} {quality}" if quality else ""

                lines += [
                    _box_line(""),
                    _box_line(f"  {slug}  ·  {_bar(pct, 30)}  {status_str}{quality_str}"),
                    _box_line(""),
                ]

                # Latest metrics from last entry
                last = slug_entries[-1] if slug_entries else {}
                metrics = last.get("metrics", {})
                if metrics:
                    flat_m = {k: v for k, v in metrics.items() if not isinstance(v, (dict, list))}
                    pairs = list(flat_m.items())
                    for i in range(0, min(len(pairs), 6), 2):
                        k1, v1 = pairs[i]
                        k2, v2 = pairs[i + 1] if i + 1 < len(pairs) else ("", "")
                        half_w = (W_INNER - 6) // 2
                        left = _pad(f"  {BULLET} {k1}: {v1}", half_w)
                        right = f"  {BULLET} {k2}: {v2}" if k2 else ""
                        lines.append(_box_line(left + right))

                # Dossiers and new cargos for this slug
                dossiers = last.get("dossiers", [])
                new_cargo_slug = last.get("new_cargos", [])
                if dossiers:
                    lines.append(
                        _box_line(f"  Dossiês: {' · '.join(str(d) for d in dossiers[:5])}")
                    )
                if new_cargo_slug:
                    lines.append(_box_line(f"  Novos cargos: {' · '.join(new_cargo_slug)}"))

            lines += [_box_line(""), f"╚{SEP_D}╝"]

        # ── CONFLICTS PENDING ─────────────────────────────────────────────────
        if conflicts_pending:
            lines += [
                "",
                f"╔{SEP_D}╗",
                _box_line("  ⚔️  CONFLITOS PENDENTES — AÇÃO HUMANA NECESSÁRIA"),
                f"╠{SEP_D}╣",
                _box_line(""),
            ]
            for conf in conflicts_pending:
                lines.append(
                    _box_line(
                        f"  🔴  {conf.get('id', '?')} · {conf.get('tema', '?')} · {conf.get('descricao', '')}"
                    )
                )
                lines.append(_box_line("       Bloqueante para Phase 5 até resolução"))
            lines += [_box_line(""), f"╚{SEP_D}╝"]

        # ── CROSS-BUCKET INTERSECTIONS ────────────────────────────────────────
        intersections = session_data.get("intersections", [])
        if intersections:
            lines += [
                "",
                f"╔{SEP_D}╗",
                _box_line("  🔄 INTERSECÇÕES CROSS-BUCKET DA SESSÃO"),
                f"╠{SEP_D}╣",
                _box_line(""),
            ]
            for ix in intersections:
                lines.append(_box_line(f"  {ARROW} {ix}"))
            lines += [_box_line(""), f"╚{SEP_D}╝"]

        # ── MISSION ACCUMULATED ───────────────────────────────────────────────
        acc = session_data.get("accumulated_mission", {})
        if acc:
            items = [
                ("Arquivos", acc.get("files", "?"), acc.get("files_pct", 0)),
                ("Insights", acc.get("insights", "?"), acc.get("insights_pct", 0)),
                ("Dossiês", acc.get("dossiers", "?"), acc.get("dossiers_pct", 0)),
                ("Agentes", acc.get("agents", "?"), acc.get("agents_pct", 0)),
            ]
            lines += [
                "",
                f"╔{SEP_D}╗",
                _box_line("  📈 ACUMULADO MISSÃO"),
                f"╠{SEP_D}╣",
                _box_line(""),
            ]
            for i in range(0, len(items), 2):
                k1, v1, p1 = items[i]
                row = f"  {k1:<12}  {v1!s:<8}  {_bar(p1, 20)}"
                if i + 1 < len(items):
                    k2, v2, p2 = items[i + 1]
                    row += f"     {k2:<12}  {v2!s:<8}  {_bar(p2, 20)}"
                lines.append(_box_line(row))
            lines += [_box_line(""), f"╚{SEP_D}╝"]

        # ── CHRONICLER ────────────────────────────────────────────────────────
        note = session_data.get("chronicler_note", "")
        if note:
            lines.extend(_render_chronicler(note))

        # ── FOOTER ───────────────────────────────────────────────────────────
        bkt_label = f"{len(active_bkts)} BUCKET(S): {bkt_str}"
        lines += [
            "",
            solid,
            f"████  {_pad(f'JARVIS BRIEFING  ·  {bkt_label}', W - 12)}  ████",
            f"████  {_pad(f'Chronicler Design System v3.0  ·  {now}', W - 12)}  ████",
            solid,
            "",
        ]

        return "\n".join(lines)

    except Exception as exc:
        logger.warning("render_briefing failed: %s", exc)
        return f"\n[JARVIS BRIEFING] Render error: {exc}\n"
