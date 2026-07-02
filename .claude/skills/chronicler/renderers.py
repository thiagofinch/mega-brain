#!/usr/bin/env python3
"""
Chronicler Render-Phase Protocol — 24 Canonical Render Functions
=================================================================

Each function maps a template_id to a rendered Markdown block.

Contract:
  render(template_id, payload, history, mode='canonical') -> str

Every canonical render function:
  1. Preserves payload.ascii_block verbatim (zero modification)
  2. Adds dynamic header above the ASCII block
  3. Adds delta history footer when history is present
  4. Applies tom adaptativo (expanded vs enxuto) based on source_minutes

Free-form mode:
  mint_free_form(signal_type, signal_data, ascii_body) -> str
  Enforces 5 anti-invention contracts.

STORY-MCE-6.0 Phase 4 (2026-05-22).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Width constant (Chronicler Design System)
# ---------------------------------------------------------------------------
W = 79  # Free-form uses 79-char width per AC-9 style guide


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _ts_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _duration_s(payload: dict) -> str:
    metrics = payload.get("metrics", {})
    dur = metrics.get("duration_s") or metrics.get("duration_ms")
    if dur is None:
        return "N/A"
    if metrics.get("duration_ms") and not metrics.get("duration_s"):
        return f"{float(dur)/1000:.1f}s"
    return f"{float(dur):.1f}s"


def _eta_remaining(payload: dict, total_phases: int = 23) -> str:
    metrics = payload.get("metrics", {})
    phase_idx = metrics.get("phase_idx", "?")
    if phase_idx == "?":
        return "N/A"
    try:
        remaining = total_phases - int(phase_idx) - 1
        return f"{remaining} phases"
    except (TypeError, ValueError):
        return "N/A"


def _dynamic_header(phase_idx: int | str, total: int, template_id: str, slug: str, payload: dict) -> str:
    dur = _duration_s(payload)
    eta = _eta_remaining(payload, total)
    line1 = f"  PHASE {phase_idx}/{total} · {template_id} · slug: {slug}"
    line2 = f"  duration: {dur} · ETA remaining: {eta}"
    width = 75
    return (
        f"╔{'═' * width}╗\n"
        f"║{line1:<{width}}║\n"
        f"║{line2:<{width}}║\n"
        f"╚{'═' * width}╝"
    )


def _delta_footer(slug: str, history: list[dict]) -> str | None:
    """Compute delta footer comparing current vs last history entry for same slug."""
    if not history:
        return None
    # Find last entry with same slug
    prev = None
    for h in reversed(history):
        if h.get("slug") == slug:
            prev = h
            break
    if not prev:
        return None

    curr_metrics = {}  # Will be set by caller
    prev_metrics = prev.get("metrics", {})

    delta_parts = []
    for key in ("insights", "chunks", "dna_total", "embeddings"):
        curr_val = curr_metrics.get(key, 0)
        prev_val = prev_metrics.get(key, 0)
        if prev_val and curr_val != prev_val:
            diff = curr_val - prev_val
            sign = "+" if diff >= 0 else ""
            delta_parts.append(f"{sign}{diff} {key}")

    if not delta_parts:
        return None
    return f"▼ Delta vs last ingestion of {slug}: {' / '.join(delta_parts)}"


def _compute_delta_footer(payload: dict, history: list[dict]) -> str | None:
    """Full delta footer with actual payload metrics."""
    slug = payload.get("slug", "")
    if not history:
        return None
    prev = None
    for h in reversed(history):
        if h.get("slug") == slug:
            prev = h
            break
    if not prev:
        return None

    curr_m = payload.get("metrics", {})
    prev_m = prev.get("metrics", {})

    delta_parts = []
    for key in ("insights", "chunks", "dna_total", "embeddings"):
        curr_val = curr_m.get(key, 0) or 0
        prev_val = prev_m.get(key, 0) or 0
        if prev_val and curr_val != prev_val:
            diff = curr_val - prev_val
            sign = "+" if diff >= 0 else ""
            delta_parts.append(f"{sign}{diff} {key}")

    if not delta_parts:
        return None
    return f"▼ Delta vs last ingestion of {slug}: {' / '.join(delta_parts)}"


def _is_long_source(payload: dict) -> bool:
    return (payload.get("metrics", {}).get("source_minutes", 0) or 0) >= 30


def _wrap(rendered: str, header: str, footer: str | None = None) -> str:
    parts = [header, "", rendered]
    if footer:
        parts.extend(["", footer])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Core render dispatcher
# ---------------------------------------------------------------------------


def render(
    template_id: str,
    payload: dict,
    history: list[dict],
    mode: str = "canonical",
) -> str:
    """Dispatch render to the appropriate canonical function.

    Args:
        template_id: one of the 24 canonical template IDs.
        payload: PHASE-STREAM.jsonl entry dict.
        history: previous payloads for the same slug.
        mode: "canonical" | "free-form"

    Returns:
        Rendered Markdown block ready to paste in chat.
    """
    from .heuristics import check_all_heuristics

    slug = payload.get("slug", "unknown")
    metrics = payload.get("metrics", {})
    phase_idx = metrics.get("phase_idx", "?")

    # Dynamic header
    header = _dynamic_header(phase_idx, 23, template_id, slug, payload)

    # Delta footer
    delta = _compute_delta_footer(payload, history)

    # Route to canonical renderer
    _RENDERERS = {
        "ingestion_guard": render_ingestion_guard,
        "ingest_report": render_ingest_report,
        "rag_indexation": render_rag_indexation,
        "graphrag_index": render_graphrag_index,
        "execution_chunks": render_execution_chunks,
        "execution_embeddings": render_execution_embeddings,
        "execution_insights": render_execution_insights,
        "execution_behavioral": render_execution_behavioral,
        "execution_voice": render_execution_voice,
        "execution_identity": render_execution_identity,
        "identity_checkpoint": render_identity_checkpoint,
        "phase8_gate": render_phase8_gate,
        "contradictions": render_contradictions,
        "agent_state": render_agent_state,
        "narrative_metabolism": render_narrative_metabolism,
        "sources_compilation": render_sources_compilation,
        "domain_aggregator": render_domain_aggregator,
        "workspace_sync": render_workspace_sync,
        "full_pipeline_report": render_full_pipeline_report,
        "llm_cost": render_llm_cost,
        "auto_advance_trigger": render_auto_advance_trigger,
        "squad_activation": render_squad_activation,
        "batch_log": render_batch_log,
        "pipeline_recover": render_pipeline_recover,
        "chronicler_audit": render_chronicler_audit,
    }

    fn = _RENDERERS.get(template_id)
    ascii_block = payload.get("ascii_block", "")

    if mode == "free-form":
        # Free-form still needs to be signal-referenced — handled by mint_free_form
        body = ascii_block or f"[no ascii_block for {template_id}]"
        rendered = mint_free_form(
            signal_type=f"template_missing_{template_id}",
            signal_data={"template_id": template_id, "slug": slug},
            ascii_body=body,
        )
    elif fn is None:
        # Unknown template — emit a SILENT-PHASE box
        rendered = _silent_phase_box(template_id, slug, payload)
    else:
        rendered = fn(payload, history)

    # Check heuristics and prepend warnings
    warnings = check_all_heuristics(payload, history)
    warning_block = ""
    if warnings:
        warning_block = "\n".join(warnings) + "\n\n"

    return warning_block + _wrap(rendered, header, delta)


# ---------------------------------------------------------------------------
# Silent phase box (coverage gate)
# ---------------------------------------------------------------------------


def _silent_phase_box(template_id: str, slug: str, payload: dict) -> str:
    ts = _ts_now()
    return (
        f"╔{'═' * 77}╗\n"
        f"║  SILENT-PHASE WARNING                                                       ║\n"
        f"║  expected template_id: {template_id:<53}║\n"
        f"║  slug: {slug:<69}║\n"
        f"║  ts: {ts:<71}║\n"
        f"║  No payload emitted for this phase — coverage gap detected                  ║\n"
        f"╚{'═' * 77}╝"
    )


# ---------------------------------------------------------------------------
# 24 Canonical render functions
# (Each preserves payload.ascii_block verbatim + returns it)
# ---------------------------------------------------------------------------


def _base_render(payload: dict, history: list[dict], phase_label: str) -> str:
    """Base render — returns ascii_block verbatim.
    Subclasses can enrich, but ascii_block is ALWAYS the core."""
    ascii_block = payload.get("ascii_block", "")
    if not ascii_block:
        m = payload.get("metrics", {})
        slug = payload.get("slug", "?")
        ascii_block = (
            f"[{phase_label}] slug={slug} status={payload.get('status','?')} "
            f"ts={datetime.fromtimestamp(payload.get('ts', 0), timezone.utc).strftime('%H:%M:%S')}\n"
            + "\n".join(f"  {k}: {v}" for k, v in m.items())
        )
    return ascii_block


def render_ingestion_guard(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "INGESTION GUARD")


def render_ingest_report(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "INGEST REPORT")


def render_rag_indexation(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "RAG INDEXATION")


def render_graphrag_index(payload: dict, history: list[dict]) -> str:
    # Opt-in phase (MCE_GRAPHRAG_ENABLED). When skipped, payload carries a
    # self-contained BYPASSED ascii_block; _base_render emits it verbatim.
    return _base_render(payload, history, "GRAPHRAG INDEX")


def render_execution_chunks(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "EXECUTION REPORT — CHUNKS")


def render_execution_embeddings(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "EXECUTION REPORT — EMBEDDINGS")


def render_execution_insights(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "EXECUTION REPORT — INSIGHTS")


def render_execution_behavioral(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "EXECUTION REPORT — BEHAVIORAL")


def render_execution_voice(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "EXECUTION REPORT — VOICE")


def render_execution_identity(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "EXECUTION REPORT — IDENTITY")


def render_identity_checkpoint(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "IDENTITY CHECKPOINT")


def render_phase8_gate(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "PHASE 8 GATE")


def render_contradictions(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "CONTRADICTIONS")


def render_agent_state(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "AGENT STATE")


def render_narrative_metabolism(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "NARRATIVE METABOLISM")


def render_sources_compilation(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "SOURCES COMPILATION")


def render_domain_aggregator(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "DOMAIN AGGREGATOR")


def render_workspace_sync(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "WORKSPACE SYNC")


def render_full_pipeline_report(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "FULL PIPELINE REPORT")


def render_llm_cost(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "LLM COST")


def render_auto_advance_trigger(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "AUTO-ADVANCE TRIGGER")


def render_squad_activation(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "SQUAD ACTIVATION")


def render_batch_log(payload: dict, history: list[dict]) -> str:
    return _base_render(payload, history, "BATCH LOG")


def render_pipeline_recover(payload: dict, history: list[dict]) -> str:
    """Renders pipeline recovery events (new — no existing emitter)."""
    ascii_block = payload.get("ascii_block", "")
    if not ascii_block:
        m = payload.get("metrics", {})
        slug = payload.get("slug", "?")
        recovered_phase = m.get("recovered_phase", "?")
        reason = m.get("recover_reason", "unspecified")
        ascii_block = (
            f"╔{'═' * 77}╗\n"
            f"║  PIPELINE RECOVER                                                           ║\n"
            f"║  slug: {slug:<69}║\n"
            f"║  recovered from phase: {str(recovered_phase):<53}║\n"
            f"║  reason: {reason:<67}║\n"
            f"╚{'═' * 77}╝"
        )
    return ascii_block


def render_chronicler_audit(payload: dict, history: list[dict]) -> str:
    """Post-finalize audit pass — 18th canonical template (index 22).

    Reports coverage%, missing templates, schema mismatches.
    This is the chronicler's self-audit box.
    """
    ascii_block = payload.get("ascii_block", "")
    if ascii_block:
        return ascii_block

    m = payload.get("metrics", {})
    slug = payload.get("slug", "?")
    templates_rendered = m.get("templates_rendered", 0)
    templates_expected = m.get("templates_expected", 24)
    missing = m.get("missing_templates", [])
    schema_mismatches = m.get("schema_mismatches", 0)
    free_form_count = m.get("free_form_count", 0)

    coverage_pct = int(templates_rendered / templates_expected * 100) if templates_expected else 0
    bar_filled = int(coverage_pct / 100 * 30)
    bar = "▓" * bar_filled + "░" * (30 - bar_filled)

    lines = [
        f"╔{'═' * 77}╗",
        f"║{'CHRONICLER AUDIT — POST-FINALIZE':^77}║",
        f"╠{'═' * 77}╣",
        f"║  slug: {slug:<69}║",
        f"║  coverage: {templates_rendered}/{templates_expected} templates  [{bar}] {coverage_pct}%{'':17}║",
        f"║  schema mismatches: {schema_mismatches:<56}║",
        f"║  free-form boxes emitted: {free_form_count:<50}║",
    ]
    if missing:
        lines.append(f"║  MISSING TEMPLATES:{'':57}║")
        for t in missing[:5]:
            lines.append(f"║    - {t:<73}║")
    lines.append(f"╚{'═' * 77}╝")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Free-form mode — 5 anti-invention contracts
# ---------------------------------------------------------------------------


def mint_free_form(
    signal_type: str,
    signal_data: dict,
    ascii_body: str,
) -> str:
    """Mint a free-form box enforcing all 5 anti-invention contracts.

    Contract 1: signal-referencing — signal_type must be non-empty and
                reference a real signal (heuristic_id, audit_id, schema_field,
                history_event). Raises ValueError if signal_type is empty.
    Contract 2: [FREE-FORM] MUST appear in the header line.
    Contract 3: triggered_by: <signal_source> MUST appear as last line.
    Contract 4: 79-char width, same border chars as canonical.
    Contract 5: Audit-tracking — caller must log this via chronicler_audit.
                This function returns the rendered box; logging is caller's duty.

    Args:
        signal_type: identifier of the real signal that triggered this box.
                     Examples: "heuristic_gates_failed", "audit_missing_coverage",
                     "unmapped_observations.confidence".
        signal_data: structured signal payload (audit_id, values, etc.)
        ascii_body: the inner text / ASCII art for the box body.

    Returns:
        Rendered free-form box string.
    """
    # Contract 1 — signal must be non-empty
    if not signal_type or not signal_type.strip():
        raise ValueError(
            "mint_free_form: signal_type must be non-empty. "
            "Free-form boxes without a real signal reference are forbidden (AC-9, anti-invention contract 1)."
        )

    # Contract 4 — width = 79
    w = W
    border_h = "─"
    border_v = "│"
    corner_tl = "┌"
    corner_tr = "┐"
    corner_bl = "└"
    corner_br = "┘"

    # Contract 2 — [FREE-FORM] in header
    header_text = f" [FREE-FORM] {signal_type} "
    header_padded = header_text[:w - 2]

    lines = [
        f"{corner_tl}{border_h * (w - 2)}{corner_tr}",
        f"{border_v}{header_padded:<{w - 2}}{border_v}",
        f"{border_v}{' ' * (w - 2)}{border_v}",
    ]

    # Body lines (wrapped at w-4)
    for line in ascii_body.splitlines():
        # Preserve line, but clip to width
        clipped = line[:w - 4]
        lines.append(f"{border_v}  {clipped:<{w - 4}}{border_v}")

    lines.append(f"{border_v}{' ' * (w - 2)}{border_v}")

    # Contract 3 — triggered_by as last line before border
    source_ref = signal_data.get("source", signal_type)
    triggered_by = f"triggered_by: {source_ref}"[:w - 4]
    lines.append(f"{border_v}  {triggered_by:<{w - 4}}{border_v}")
    lines.append(f"{corner_bl}{border_h * (w - 2)}{corner_br}")

    return "\n".join(lines)
