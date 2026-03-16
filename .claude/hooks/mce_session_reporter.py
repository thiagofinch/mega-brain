#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          MCE SESSION REPORTER  —  Stop Hook                                  ║
║          Version: 2.0.0  —  Session Concatenator                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  O QUE FAZ:                                                                  ║
║  Disparado ao final de cada sessão Claude Code. Lê todos os logs JSONL       ║
║  da sessão atual e produz um SESSION REPORT completo:                        ║
║                                                                              ║
║    • Para cada slug processado: jornada completa de steps                    ║
║    • Totais de insights, chunks, entidades, agentes criados                  ║
║    • Artefatos gerados com tamanhos                                          ║
║    • Validação consolidada (pass/fail por step)                              ║
║    • Timeline visual da sessão                                               ║
║                                                                              ║
║  OUTPUT:                                                                     ║
║    • Salva em logs/sessions/SESSION-YYYY-MM-DD-HH-MM-SS.md                  ║
║    • Imprime como feedback no Claude Code                                    ║
║                                                                              ║
║  JANELA DE SESSÃO:                                                           ║
║    Padrão: últimas 8 horas. Override via: MCE_SESSION_HOURS=N               ║
║                                                                              ║
║  CONSTRAINTS:                                                                ║
║    - stdlib apenas + PyYAML                                                  ║
║    - Exit 0 always — never blocks Claude Code shutdown                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# ─────────────────────────────────────────────────────────────────────────────
# PATH CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

PROJECT_DIR     = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
LOGS_DIR        = PROJECT_DIR / "logs"
SESSIONS_DIR    = LOGS_DIR / "sessions"
STEP_LOG        = LOGS_DIR / "mce-step-logger.jsonl"
ORCHESTRATE_LOG = LOGS_DIR / "mce-orchestrate.jsonl"
SCOPE_LOG       = LOGS_DIR / "scope-classifier.jsonl"
METRICS_LOG     = LOGS_DIR / "mce-metrics.jsonl"

SESSION_HOURS   = int(os.environ.get("MCE_SESSION_HOURS", "8"))

# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

RW = 72  # report width (inner)

STEP_NAMES = {
    0: "DETECT",    1: "INGEST",      2: "BATCH",
    3: "CHUNK",     4: "ENTITY",      5: "INSIGHT",
    6: "BEHAVIORAL",7: "IDENTITY",    8: "VOICE-DNA",
    9: "CHECKPOINT",10: "COMPILE",   11: "FINALIZE",   12: "REPORT",
}

BUCKET_ICON = {
    "external":  "📚",
    "business":  "🏢",
    "personal":  "🧠",
    "workspace": "🗂️",
}

# ─────────────────────────────────────────────────────────────────────────────
# RENDERING HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def _row(content: str) -> str:
    return f"║  {content[:RW].ljust(RW)}  ║"


def _top() -> str:
    return f"╔{'═' * (RW + 4)}╗"


def _bottom() -> str:
    return f"╚{'═' * (RW + 4)}╝"


def _div() -> str:
    return f"╠{'═' * (RW + 4)}╣"


def _thin() -> str:
    return f"╟{'─' * (RW + 4)}╢"


def _section(title: str) -> str:
    return _row(f"  ▸ {title}")


def _bar(val: int, maxv: int, width: int = 20) -> str:
    if maxv <= 0:
        return "░" * width
    n = min(width, round(val / maxv * width))
    return "█" * n + "░" * (width - n)


def _steps_timeline(completed_steps: set[int]) -> str:
    """Render compact step timeline: ●=done ○=missed"""
    parts = []
    for s in range(13):
        sym = "●" if s in completed_steps else "○"
        parts.append(f"S{s:02d}{sym}")
    return "  ".join(parts[:7]) + "\n" + "  " + "  ".join(parts[7:])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024 / 1024:.1f} MB"


def _fmt_duration(start_ts: str, end_ts: str) -> str:
    """Format duration between two ISO timestamps."""
    try:
        fmt = "%Y-%m-%dT%H:%M:%S"
        t1 = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
        t2 = datetime.fromisoformat(end_ts.replace("Z", "+00:00"))
        delta = t2 - t1
        total = int(delta.total_seconds())
        if total < 60:
            return f"{total}s"
        if total < 3600:
            return f"{total // 60}m {total % 60}s"
        return f"{total // 3600}h {(total % 3600) // 60}m"
    except Exception:
        return "—"


# ─────────────────────────────────────────────────────────────────────────────
# JSONL READER
# ─────────────────────────────────────────────────────────────────────────────


def _read_jsonl_since(path: Path, cutoff: datetime) -> list[dict]:
    """Read all JSONL entries at or after cutoff datetime."""
    results = []
    if not path.exists():
        return results
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts_str = entry.get("timestamp", "")
                    if ts_str:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts >= cutoff:
                            results.append(entry)
                except (json.JSONDecodeError, ValueError):
                    pass
    except Exception:
        pass
    return results


def _read_jsonl_all(path: Path) -> list[dict]:
    """Read all JSONL entries from a file."""
    results = []
    if not path.exists():
        return results
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    return results


# ─────────────────────────────────────────────────────────────────────────────
# DATA AGGREGATION
# ─────────────────────────────────────────────────────────────────────────────


def _aggregate_session(step_entries: list[dict]) -> dict[str, dict]:
    """
    Group step entries by slug and aggregate per-step data.
    Returns: {slug: {steps: {step_num: entry}, timeline: [...], ...}}
    """
    by_slug: dict[str, dict] = defaultdict(lambda: {
        "steps":       {},       # step_num -> latest entry for that step
        "substeps":    [],       # all step-10 sub-steps in order
        "first_ts":    None,
        "last_ts":     None,
        "bucket":      "external",
        "completed":   set(),
    })

    for e in step_entries:
        slug = e.get("slug", "unknown")
        step = e.get("step", -1)
        ts   = e.get("timestamp", "")
        bucket = e.get("bucket", "external")

        rec = by_slug[slug]
        rec["bucket"] = bucket

        if rec["first_ts"] is None:
            rec["first_ts"] = ts
        rec["last_ts"] = ts

        if step == 10:
            rec["substeps"].append(e)
        else:
            # Keep latest entry per step
            rec["steps"][step] = e

        rec["completed"].add(step)

    return dict(by_slug)


def _aggregate_orchestrate(orch_entries: list[dict]) -> dict[str, list[dict]]:
    """Group orchestrate log entries by slug."""
    by_slug: dict[str, list[dict]] = defaultdict(list)
    for e in orch_entries:
        slug = e.get("slug", "")
        if slug:
            by_slug[slug].append(e)
    return dict(by_slug)


# ─────────────────────────────────────────────────────────────────────────────
# PER-SLUG REPORT SECTION
# ─────────────────────────────────────────────────────────────────────────────


def _slug_card(slug: str, data: dict, orch_data: list[dict]) -> list[str]:
    """Build a complete card for one slug."""
    steps     = data.get("steps", {})
    substeps  = data.get("substeps", [])
    completed = data.get("completed", set())
    bucket    = data.get("bucket", "external")
    first_ts  = data.get("first_ts", "")
    last_ts   = data.get("last_ts", "")
    bucket_ic = BUCKET_ICON.get(bucket, "📁")

    # ── Compute total stats ───────────────────────────────────────────────
    total_chunks  = steps.get(3, {}).get("metrics", {}).get("chunks_created", 0)
    total_insights= steps.get(5, {}).get("metrics", {}).get("total_insights", 0)
    total_entities= steps.get(4, {}).get("metrics", {}).get("total_entities", 0)
    total_patterns= steps.get(6, {}).get("metrics", {}).get("total_patterns", 0)
    values_count  = steps.get(7, {}).get("metrics", {}).get("values_count", 0)
    sig_phrases   = steps.get(8, {}).get("metrics", {}).get("signature_phrases", 0)

    # Step-10 artifact counts
    dossiers_w = sum(1 for s in substeps if s.get("metrics", {}).get("substep") == "10.1_dossier")
    dna_yamls_w= sum(1 for s in substeps if s.get("metrics", {}).get("substep") == "10.3_dna_yaml")
    agent_files= sum(1 for s in substeps if s.get("metrics", {}).get("substep") == "10.4_agent")
    sources_w  = sum(1 for s in substeps if s.get("metrics", {}).get("substep") == "10.2_sources")

    # Duration
    duration = _fmt_duration(first_ts, last_ts) if first_ts and last_ts else "—"

    # Completion %
    expected_steps = {3, 4, 5, 6, 7, 8, 9, 10}
    done = len(completed & expected_steps)
    pct  = round(done / len(expected_steps) * 100)
    prog = _bar(done, len(expected_steps), 20)

    # Ingest info from orchestrate log
    ingest_count = sum(1 for e in orch_data if e.get("command") == "ingest")
    batch_count  = sum(1 for e in orch_data if e.get("command") == "batch")

    lines = [
        _div(),
        _row(f"  {bucket_ic} SLUG: {slug.upper().replace('-',' '):<35s}  {bucket.upper()}"),
        _thin(),
        _row(f"  Steps Completos : {done}/{len(expected_steps)}  {prog}  {pct}%"),
        _row(f"  Duração Total   : {duration}"),
        _row(f"  Ingests         : {ingest_count:>4d}    Batches : {batch_count:>3d}"),
        _thin(),
        _section("EXTRAÇÃO — RESULTADOS"),
        _row(f"  🧩 Chunks       : {total_chunks:>6,d}"),
        _row(f"  🏷️  Entidades    : {total_entities:>6,d}"),
        _row(f"  💡 Insights     : {total_insights:>6,d}"),
        _row(f"  🧠 Beh. Patterns: {total_patterns:>6,d}"),
        _row(f"  🎯 Values       : {values_count:>6,d}"),
        _row(f"  🎤 Sig. Phrases : {sig_phrases:>6,d}"),
        _thin(),
        _section("ARTEFATOS COMPILADOS (STEP 10)"),
        _row(f"  📄 Dossiers     : {dossiers_w:>3d}"),
        _row(f"  🧬 DNA YAMLs    : {dna_yamls_w:>3d}"),
        _row(f"  🤖 Agent Files  : {agent_files:>3d}"),
        _row(f"  📚 Source Docs  : {sources_w:>3d}"),
    ]

    # Step validation summary
    lines += [_thin(), _section("VALIDAÇÃO POR STEP")]
    for step_num in sorted(completed):
        if step_num not in {3, 4, 5, 6, 7, 8, 9}:
            continue
        entry = steps.get(step_num, {})
        vdict = entry.get("validation", {})
        sname = STEP_NAMES.get(step_num, f"S{step_num:02d}")
        # Quick overall status: all booleans True?
        bool_vals = [v for k, v in vdict.items()
                     if isinstance(v, bool) and not k.endswith("_count")]
        ok = all(bool_vals) if bool_vals else True
        mark = "✅" if ok else "⚠️ "
        ts_short = entry.get("timestamp", "")[-8:-3] if entry.get("timestamp") else "--:--"
        lines.append(_row(f"  {mark} S{step_num:02d} {sname:<13s} @ {ts_short}"))

    # DNA tag breakdown from Step 5
    by_tag = steps.get(5, {}).get("metrics", {}).get("by_dna_tag", {})
    if by_tag:
        lines += [_thin(), _section("DNA LAYERS — DISTRIBUIÇÃO")]
        max_t = max(by_tag.values(), default=1)
        dna_display = [
            ("FILOSOFIA",     "Filosofia   "),
            ("MODELO-MENTAL", "Mod. Mental "),
            ("HEURISTICA",    "Heurística  "),
            ("FRAMEWORK",     "Framework   "),
            ("METODOLOGIA",   "Metodologia "),
        ]
        for tag, label in dna_display:
            count = by_tag.get(tag, 0)
            lines.append(_row(f"  {label} {_bar(count, max_t, 16)} {count:>3d}"))

    # Voice DNA summary from Step 8
    tone = steps.get(8, {}).get("metrics", {}).get("tone_profile", {})
    if tone:
        lines += [_thin(), _section("VOICE-DNA — PERFIL DE TOM")]
        tone_rows = [
            ("certainty", "Certainty  "),
            ("authority", "Authority  "),
            ("warmth",    "Warmth     "),
            ("directness","Directness "),
        ]
        for key, label in tone_rows:
            score = float(tone.get(key, 0))
            bar   = "●" * min(10, round(score)) + "○" * (10 - min(10, round(score)))
            lines.append(_row(f"  {label}  {bar}  {score:.0f}/10"))

    return lines


# ─────────────────────────────────────────────────────────────────────────────
# GRAND SUMMARY HEADER
# ─────────────────────────────────────────────────────────────────────────────


def _report_header(session_ts: str, slug_count: int,
                   total_chunks: int, total_insights: int,
                   total_agents: int, window_hours: int) -> list[str]:
    ts_display = session_ts[:19].replace("T", " ")
    lines = [
        _top(),
        _row(""),
        _row("  ███╗   ███╗ ██████╗███████╗    ██████╗ ███████╗██████╗  ██████╗ ██████╗ ████████╗"),
        _row("  ████╗ ████║██╔════╝██╔════╝    ██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝"),
        _row("  ██╔████╔██║██║     █████╗      ██████╔╝█████╗  ██████╔╝██║   ██║██████╔╝   ██║"),
        _row("  ██║╚██╔╝██║██║     ██╔══╝      ██╔══██╗██╔══╝  ██╔═══╝ ██║   ██║██╔══██╗   ██║"),
        _row("  ██║ ╚═╝ ██║╚██████╗███████╗    ██║  ██║███████╗██║     ╚██████╔╝██║  ██║   ██║"),
        _row("  ╚═╝     ╚═╝ ╚═════╝╚══════╝    ╚═╝  ╚═╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝"),
        _row(""),
        _row(f"  MCE SESSION REPORT  ·  {ts_display}"),
        _row(f"  Janela: últimas {window_hours}h  ·  Slugs processados: {slug_count}"),
        _div(),
        _section("TOTAIS DA SESSÃO"),
        _row(f"  🧩 Chunks Processados  : {total_chunks:>8,d}"),
        _row(f"  💡 Insights Extraídos  : {total_insights:>8,d}"),
        _row(f"  🤖 Agent Files Criados : {total_agents:>8,d}"),
        _row(f"  📊 Slugs Processados   : {slug_count:>8,d}"),
    ]
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# SESSION LOG FILES SECTION
# ─────────────────────────────────────────────────────────────────────────────


def _log_inventory(cutoff: datetime) -> list[str]:
    """List all JSONL logs and their recent entry counts."""
    log_files = [
        (LOGS_DIR / "mce-orchestrate.jsonl",    "mce-orchestrate"),
        (LOGS_DIR / "mce-step-logger.jsonl",     "mce-step-logger"),
        (LOGS_DIR / "scope-classifier.jsonl",    "scope-classifier"),
        (LOGS_DIR / "smart-router.jsonl",        "smart-router"),
        (LOGS_DIR / "batch-auto-creator.jsonl",  "batch-auto-creator"),
        (LOGS_DIR / "memory-enricher.jsonl",     "memory-enricher"),
        (LOGS_DIR / "workspace-sync.jsonl",      "workspace-sync"),
        (LOGS_DIR / "agent-creation.jsonl",      "agent-creation"),
        (LOGS_DIR / "pipeline-checkpoints.jsonl","pipeline-checkpoints"),
    ]
    lines = [_thin(), _section("INVENTÁRIO DE LOGS DA SESSÃO")]
    for path, name in log_files:
        entries = _read_jsonl_since(path, cutoff)
        total   = sum(1 for _ in _read_jsonl_all(path) if True)  # all time
        mark = "●" if entries else "○"
        lines.append(_row(f"  {mark} {name:<30s}  {len(entries):>4d} entradas na sessão"))
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# MARKDOWN REPORT BUILDER
# ─────────────────────────────────────────────────────────────────────────────


def _build_markdown_report(session_ts: str, by_slug: dict, orch_by_slug: dict,
                            total_chunks: int, total_insights: int,
                            total_agents: int, cutoff: datetime) -> str:
    """Build the full Markdown report content."""
    lines: list[str] = []

    # Header
    lines += _report_header(
        session_ts, len(by_slug), total_chunks, total_insights,
        total_agents, SESSION_HOURS
    )

    # Per-slug cards
    for slug, data in sorted(by_slug.items()):
        orch = orch_by_slug.get(slug, [])
        lines += _slug_card(slug, data, orch)

    # Log inventory
    lines += _log_inventory(cutoff)

    # Footer
    ts_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines += [
        _div(),
        _row(f"  Relatório gerado em  : {ts_end}"),
        _row(f"  Salvado em           : logs/sessions/"),
        _row("  \"Se não foi logado, não foi processado.\"  — JARVIS"),
        _bottom(),
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# SAVE REPORT
# ─────────────────────────────────────────────────────────────────────────────


def _save_report(content: str) -> Path:
    """Save the session report to logs/sessions/ and return the path."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ts_file = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_path = SESSIONS_DIR / f"SESSION-{ts_file}.md"
    try:
        output_path.write_text(content, encoding="utf-8")
    except Exception:
        pass
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    try:
        # ── Read stdin (Stop hooks receive session summary JSON) ────────────
        raw = sys.stdin.read()
        # We don't use the Stop hook input directly; we build from JSONL logs

        session_ts = _now_iso()
        cutoff     = datetime.now(timezone.utc) - timedelta(hours=SESSION_HOURS)

        # ── Read JSONL logs ──────────────────────────────────────────────────
        step_entries = _read_jsonl_since(STEP_LOG, cutoff)
        orch_entries = _read_jsonl_since(ORCHESTRATE_LOG, cutoff)

        if not step_entries and not orch_entries:
            # No MCE activity in session — emit minimal report
            minimal = "\n".join([
                _top(),
                _row("  MCE SESSION REPORT — Sem atividade MCE nesta sessão"),
                _row(f"  Janela verificada: últimas {SESSION_HOURS}h"),
                _bottom(),
            ])
            print(json.dumps({"continue": True, "feedback": minimal}))
            sys.exit(0)

        # ── Aggregate data ───────────────────────────────────────────────────
        by_slug      = _aggregate_session(step_entries)
        orch_by_slug = _aggregate_orchestrate(orch_entries)

        # Also add slugs that appear in orchestrate but not in step_entries
        for slug in orch_by_slug:
            if slug and slug not in by_slug:
                by_slug[slug] = {
                    "steps":    {},
                    "substeps": [],
                    "first_ts": orch_by_slug[slug][0].get("timestamp") if orch_by_slug[slug] else None,
                    "last_ts":  orch_by_slug[slug][-1].get("timestamp") if orch_by_slug[slug] else None,
                    "bucket":   "external",
                    "completed": set(),
                }

        # ── Compute grand totals ─────────────────────────────────────────────
        total_chunks   = sum(
            d.get("steps", {}).get(3, {}).get("metrics", {}).get("chunks_created", 0)
            for d in by_slug.values()
        )
        total_insights = sum(
            d.get("steps", {}).get(5, {}).get("metrics", {}).get("total_insights", 0)
            for d in by_slug.values()
        )
        total_agents   = sum(
            sum(1 for s in d.get("substeps", [])
                if s.get("metrics", {}).get("substep") == "10.4_agent")
            for d in by_slug.values()
        )

        # ── Build report ─────────────────────────────────────────────────────
        content = _build_markdown_report(
            session_ts, by_slug, orch_by_slug,
            total_chunks, total_insights, total_agents, cutoff
        )

        # ── Save to disk ──────────────────────────────────────────────────────
        saved_path = _save_report(content)

        # ── Add save confirmation to report ──────────────────────────────────
        save_note = f"\n\n→ Relatório salvo: {saved_path}"
        full_feedback = content + save_note

        print(json.dumps({"continue": True, "feedback": full_feedback}))
        sys.exit(0)

    except Exception as exc:
        # Never block Claude Code shutdown
        fallback = "\n".join([
            _top() if callable(_top) else "╔" + "═" * 76 + "╗",
            "║  MCE SESSION REPORTER — erro ao gerar relatório  ║",
            "╚" + "═" * 76 + "╝",
        ])
        print(json.dumps({"continue": True, "feedback": fallback}))
        sys.exit(0)


if __name__ == "__main__":
    main()
