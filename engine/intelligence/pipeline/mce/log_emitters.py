"""ASCII log emitters — port of OLD MegaBrain LOG-TEMPLATES.md v5.1 into NEW pipeline.

STORY-MCE-LOG-PARITY (2026-05-19, founder directive): the NEW pipeline emits a
single MCE-{TAG}.md narrative at the end of cmd_finalize. The OLD pipeline
(reference: ~/Desktop/Mega Brain/04-SYSTEM/PROTOCOLS/SYSTEM/
LOG-TEMPLATES.md v5.1.0) emitted 7 distinct ASCII logs at specific moments of
the 8 phases. The founder asked for parity — keep the OLD visual format (79
char width, ╔═╗/┌─┐ boxes, semantic icons) and MERGE the NEW phases (Phase 0
dedup, Phase 4.5 RAG, Phase 8 gates, 3 buckets, etc.) into the OLD 5-box
phase grouping.

Mapping NEW → 5 OLD boxes (surgical merge, L1):
  Box 1 (Phase 1-2: CHUNK+ENTITY): Phase 0 dedup + Phase 1 ingest + Phase 2
                                   chunk + Phase 3 entity resolution
  Box 2 (Phase 3-4: INSIGHT+PRIORITY): Phase 4 process_batch (DNA L1-L10
                                       extraction) + Phase 4.5 RAG indexation
  Box 3 (Phase 5-6: NARRATIVE+DOSSIER): Sources + Domain Aggregator +
                                        Consolidate + Promote
  Box 4 (Phase 7: AGENT ENRICH): Memory enrichment + Agent memory diff
  Box 5 (Phase 8: ORG-LIVE): Gates 7A-7I + ROLE-TRACKING + Workspace Sync +
                             Cross-bucket cascade

PIPELINE: All emitters are PURE FUNCTIONS that return ASCII strings. Callers
decide whether to print to stdout, write to file, or both. This keeps the
emitters testable without side effects.

WIDTH: 79 characters (OLD baseline). Box top/bottom lines use ═ for outer
frame and ─ for inner phase boxes. Tables use ┌┬┐├┼┤└┴┘. Semantic icons:
  📥 source, 📊 metrics, 🔗 entities, 💡 insights, 📝 narratives,
  📚 dossiers, 👤 person, 🤖 agent, 🆕 new, 🏢 org, 📋 list,
  🔴 high, 🟡 medium, 🟢 low, ✅ ok, ⚠️ warn, ❌ fail.

Sprint 1 MVP — these 5 emitters first:
  1. emit_execution_report     (Box 1-5 full, end of cmd_finalize)
  2. emit_ingestion_guard      (Phase 0 verdict, after cmd_ingest)
  3. emit_full_pipeline_report (Timeline 8 phases, end of cmd_full)
  4. emit_batch_log            (after each cmd_process_batch)
  5. emit_rag_indexation       (Phase 4.5, after cmd_rag_index)

Sprints 2-3: 15 remaining emitters (LLM Cost, Identity Checkpoint, Phase 8
Gate, Contradictions, Agent State, Ingest Report, Inbox Status, System Digest,
Narrative Metabolism, Sources Compilation, Domain Aggregator, Cross-bucket
Cascade, Workspace Sync, Squad Activation, JSONL Trigger).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Width constants (OLD reference)
W = 79  # outer frame width
W_INNER = 75  # inner phase box width (W - 4 for left/right borders + padding)


# ===========================================================================
# DATA CLASSES — context objects forwarded from cmd_* to emitters
# ===========================================================================


@dataclass
class FinalizeContext:
    """Aggregated context for emit_execution_report.

    cmd_finalize accumulates sub-step results in local variables. To emit a
    consolidated EXECUTION REPORT we either re-read state from disk (fragile)
    or forward the live results via this dataclass. Forwarding wins.

    All fields default to empty so partial population (e.g. when a sub-step
    fails) still yields a renderable report with "(unknown)" sections.
    """

    slug: str = ""
    bucket: str = ""
    person_name: str = ""
    source_id: str = ""
    file_path: str = ""
    duration_min: float = 0.0
    timestamp: str = ""

    # Phase 0-3 (Box 1)
    ingestion_guard: dict[str, Any] = field(default_factory=dict)
    chunks_total: int = 0
    chunks_path: str = ""
    entities_resolved: int = 0
    persons_list: list[str] = field(default_factory=list)
    frameworks_list: list[str] = field(default_factory=list)
    metrics_list: list[str] = field(default_factory=list)

    # Phase 4-4.5 (Box 2)
    insights_total: int = 0
    insights_high: int = 0
    insights_medium: int = 0
    insights_low: int = 0
    insights_by_type: dict[str, int] = field(default_factory=dict)
    rag_indexation: dict[str, Any] = field(default_factory=dict)

    # Phase 5-6 (Box 3)
    narratives_total: int = 0
    sources_compiled: int = 0
    domains_aggregated: list[str] = field(default_factory=list)
    dossiers_persons: list[dict[str, Any]] = field(default_factory=list)
    dossiers_themes: list[dict[str, Any]] = field(default_factory=list)

    # Phase 7 (Box 4)
    agents_updated: list[dict[str, Any]] = field(default_factory=list)
    memory_diffs: list[dict[str, Any]] = field(default_factory=list)
    roles_tracked: list[dict[str, Any]] = field(default_factory=list)

    # Phase 8 (Box 5)
    phase8_gates: dict[str, bool] = field(default_factory=dict)
    org_roles_updated: list[dict[str, Any]] = field(default_factory=list)
    workspace_sync: dict[str, Any] = field(default_factory=dict)
    cross_bucket_cascade: dict[str, Any] = field(default_factory=dict)

    # Statistics
    phase_timings: dict[str, float] = field(default_factory=dict)
    total_duration_s: float = 0.0


# ===========================================================================
# PRIMITIVE RENDER HELPERS — bordas e linhas no estilo OLD v5.1
# ===========================================================================


def _hr_thick() -> str:
    """═══ (79 chars) — top/bottom frame."""
    return "═" * W


def _hr_thin() -> str:
    """─── (79 chars) — phase separator inside box."""
    return "─" * W


def _center(text: str) -> str:
    """Center-align text within W=79."""
    pad = max(0, (W - len(text)) // 2)
    return " " * pad + text


def _box_top(title: str) -> str:
    """┌─ TITLE ─────┐ — phase box opener (W=78 inner)."""
    prefix = f"┌─ {title} "
    suffix = "┐"
    fill_len = W - len(prefix) - len(suffix)
    return prefix + ("─" * fill_len) + suffix


def _box_bot() -> str:
    """└──────────┘ — phase box closer."""
    return "└" + ("─" * (W - 2)) + "┘"


def _box_line(content: str = "") -> str:
    """│  content                                                              │"""
    inner = f"   {content}"
    padded = inner.ljust(W - 2)
    if len(padded) > W - 2:
        padded = padded[: W - 2]
    return "│" + padded + "│"


def _box_empty() -> str:
    """│                                                                       │"""
    return "│" + (" " * (W - 2)) + "│"


# ===========================================================================
# EMITTER 1 — EXECUTION REPORT (Sprint 1 #1)
# ===========================================================================


def emit_execution_report(ctx: FinalizeContext) -> str:
    """Generate EXECUTION REPORT ASCII string from FinalizeContext.

    Layout: 5-box OLD v5.1 structure preserved 1:1 (founder directive L1).
    Content: NEW phases internalized inside the matching OLD box.

    Returns a multi-line string ready for stdout or file write.
    """
    lines: list[str] = []
    ts = ctx.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Header (OLD v5.1 lines 62-66)
    lines.append(_hr_thick())
    lines.append(_center("EXECUTION REPORT"))
    lines.append(_center("Pipeline Jarvis v2.1 (NEW — 14 phases merged)"))
    lines.append(_center(ts))
    lines.append(_hr_thick())
    lines.append("")

    # ── SOURCE PROCESSED (OLD lines 68-74)
    lines.append("📥 SOURCE PROCESSED")
    lines.append(_hr_thin())
    lines.append(f"   Source ID:    {ctx.source_id or '(unknown)'}")
    lines.append(f"   File:         {ctx.file_path or '(unknown)'}")
    lines.append(f"   Person:       {ctx.person_name or ctx.slug}")
    lines.append(f"   Bucket:       {ctx.bucket or '(unknown)'}")  # NEW field
    lines.append(f"   Duration:     {ctx.duration_min:.1f} min")
    lines.append(f"   Processed:    {ts}")
    lines.append("")

    # ── PIPELINE PHASES (5 boxes, OLD layout, NEW content)
    lines.append(_hr_thick())
    lines.append(_center("PIPELINE PHASES (14 NEW phases → 5 OLD boxes)"))
    lines.append(_hr_thick())
    lines.append("")

    # ── BOX 1: Phase 1-2 (CHUNK+ENTITY) merged with Phase 0 dedup + Phase 3 entity
    lines.append(_box_top("Phase 1-2: CHUNKING + ENTITY RESOLUTION"))
    lines.append(_box_empty())
    ig = ctx.ingestion_guard
    if ig:
        verdict = ig.get("verdict", "?")
        icon = {"NEW": "✅", "SKIP": "⏭️", "INCREMENTAL": "🔄", "CORRUPTED": "❌"}.get(verdict, "❓")
        lines.append(_box_line(f"{icon} PHASE 0 INGESTION GUARD: {verdict}"))
        if ig.get("reason"):
            lines.append(_box_line(f"   └─ Reason: {str(ig['reason'])[:60]}"))
        lines.append(_box_empty())
    lines.append(_box_line(f"📊 CHUNKS CREATED: {ctx.chunks_total}"))
    if ctx.chunks_path:
        lines.append(_box_line(f"   └─ Stored: {ctx.chunks_path[:60]}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"🔗 ENTITIES RESOLVED: {ctx.entities_resolved}"))
    if ctx.persons_list:
        lines.append(_box_line(f"   ├─ Persons: {', '.join(ctx.persons_list[:5])}"[: W - 4]))
    if ctx.frameworks_list:
        lines.append(_box_line(f"   ├─ Frameworks: {', '.join(ctx.frameworks_list[:5])}"[: W - 4]))
    if ctx.metrics_list:
        lines.append(_box_line(f"   └─ Metrics: {', '.join(ctx.metrics_list[:5])}"[: W - 4]))
    lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")

    # ── BOX 2: Phase 3-4 (INSIGHT+PRIORITY) merged with Phase 4.5 RAG
    lines.append(_box_top("Phase 3-4: INSIGHT EXTRACTION + PRIORITIZATION + RAG"))
    lines.append(_box_empty())
    lines.append(_box_line(f"💡 INSIGHTS EXTRACTED: {ctx.insights_total}"))
    lines.append(_box_line(f"   ├─ 🔴 HIGH:   {ctx.insights_high}"))
    lines.append(_box_line(f"   ├─ 🟡 MEDIUM: {ctx.insights_medium}"))
    lines.append(_box_line(f"   └─ 🟢 LOW:    {ctx.insights_low}"))
    lines.append(_box_empty())
    if ctx.insights_by_type:
        lines.append(_box_line("📊 BY TYPE:"))
        keys = list(ctx.insights_by_type.keys())[:5]
        for i, k in enumerate(keys):
            prefix = "   └─" if i == len(keys) - 1 else "   ├─"
            lines.append(_box_line(f"{prefix} {k}: {ctx.insights_by_type[k]}"))
        lines.append(_box_empty())
    rag = ctx.rag_indexation
    if rag:
        gate = rag.get("gate_passed", False)
        icon = "✅" if gate else "❌"
        chunks_pre = rag.get("chunks_pre", 0)
        chunks_post = rag.get("chunks_post", 0)
        chunks_delta = rag.get("chunks_delta", chunks_post - chunks_pre)
        lines.append(_box_line(f"{icon} PHASE 4.5 RAG INDEXATION (Art. XV)"))
        lines.append(_box_line(f"   ├─ Chunks before:  {chunks_pre}"))
        lines.append(_box_line(f"   ├─ Chunks after:   {chunks_post}"))
        lines.append(_box_line(f"   ├─ Delta:          {chunks_delta:+d}"))
        lines.append(_box_line(f"   └─ Gate passed:    {gate}"))
    lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")

    # ── BOX 3: Phase 5-6 (NARRATIVE+DOSSIER) merged with Sources + Domain Agg
    lines.append(_box_top("Phase 5-6: NARRATIVE SYNTHESIS + DOSSIER COMPILATION"))
    lines.append(_box_empty())
    lines.append(_box_line(f"📝 NARRATIVES CREATED: {ctx.narratives_total}"))
    lines.append(_box_line(f"📁 SOURCES COMPILED:   {ctx.sources_compiled}"))
    if ctx.domains_aggregated:
        lines.append(_box_line(f"🗂️  DOMAINS AGG:       {', '.join(ctx.domains_aggregated[:5])}"))
    lines.append(_box_empty())
    if ctx.dossiers_persons:
        lines.append(_box_line("📚 DOSSIERS — PERSONS:"))
        for d in ctx.dossiers_persons[:5]:
            name = d.get("name", "?")[:30]
            status = d.get("status", "?")[:6]
            ins = d.get("insights", 0)
            nar = d.get("narratives", 0)
            lines.append(
                _box_line(f"   │ {name:30s} │ {status:6s} │ +{ins:3d} ins │ +{nar:3d} nar")
            )
        lines.append(_box_empty())
    if ctx.dossiers_themes:
        lines.append(_box_line("📚 DOSSIERS — THEMES:"))
        for d in ctx.dossiers_themes[:5]:
            name = d.get("name", "?")[:30]
            status = d.get("status", "?")[:6]
            ins = d.get("insights", 0)
            lines.append(_box_line(f"   │ {name:30s} │ {status:6s} │ +{ins:3d} ins"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")

    # ── BOX 4: Phase 7 (AGENT ENRICH) merged with Memory Diff
    lines.append(_box_top("Phase 7: AGENT ENRICHMENT + MEMORY DIFF"))
    lines.append(_box_empty())
    lines.append(_box_line(f"🤖 AGENTS UPDATED: {len(ctx.agents_updated)}"))
    for a in ctx.agents_updated[:5]:
        name = a.get("name", "?")[:30]
        mem = a.get("memory", "?")[:30]
        delta = a.get("delta", "")[:15]
        lines.append(_box_line(f"   │ {name:30s} │ {mem:30s} │ {delta}"))
    lines.append(_box_empty())
    if ctx.memory_diffs:
        lines.append(_box_line("📋 MEMORY DIFFS:"))
        for d in ctx.memory_diffs[:5]:
            agent = d.get("agent", "?")[:25]
            before = d.get("before_bytes", 0)
            after = d.get("after_bytes", 0)
            delta_pct = ((after - before) / before * 100) if before > 0 else 0
            lines.append(
                _box_line(
                    f"   │ {agent:25s} │ {before:>6d}B → {after:>6d}B " f"({delta_pct:+.1f}%)"
                )
            )
        lines.append(_box_empty())
    if ctx.roles_tracked:
        lines.append(_box_line("🆕 ROLES TRACKED:"))
        for r in ctx.roles_tracked[:5]:
            name = r.get("name", "?")[:30]
            mentions = r.get("mentions", 0)
            thresh = r.get("threshold", 10)
            lines.append(_box_line(f"   │ {name:30s}: {mentions} mentions (thresh {thresh})"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")

    # ── BOX 5: Phase 8 (ORG-LIVE) merged with Gates + Workspace Sync + Cascade
    lines.append(_box_top("Phase 8: ORG-LIVE + PHASE 8 GATES + WORKSPACE SYNC"))
    lines.append(_box_empty())
    if ctx.phase8_gates:
        lines.append(_box_line("🚦 PHASE 8 GATES (7A-7I):"))
        for gate_id, passed in sorted(ctx.phase8_gates.items()):
            icon = "✅" if passed else "❌"
            lines.append(_box_line(f"   │ {icon} {gate_id}: {'PASS' if passed else 'FAIL'}"))
        lines.append(_box_empty())
    lines.append(_box_line(f"🏢 ORG ROLES UPDATED: {len(ctx.org_roles_updated)}"))
    for r in ctx.org_roles_updated[:5]:
        name = r.get("name", "?")[:30]
        mem = r.get("memory", "?")[:30]
        lines.append(_box_line(f"   │ {name:30s} │ {mem}"))
    lines.append(_box_empty())
    ws = ctx.workspace_sync
    if ws:
        lines.append(_box_line("🔄 WORKSPACE SYNC (L0-L4):"))
        for layer in ("L0", "L1", "L2", "L3", "L4"):
            cnt = ws.get(layer, 0)
            if cnt:
                lines.append(_box_line(f"   │ {layer}: +{cnt} artifact(s)"))
        lines.append(_box_empty())
    cbc = ctx.cross_bucket_cascade
    if cbc:
        lines.append(_box_line("🌐 CROSS-BUCKET CASCADE:"))
        for b in ("external", "business", "personal"):
            cnt = cbc.get(b, 0)
            if cnt:
                lines.append(_box_line(f"   │ → {b}: +{cnt} ref(s)"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")

    # ── STATISTICS
    lines.append(_hr_thick())
    lines.append(_center("STATISTICS"))
    lines.append(_hr_thick())
    lines.append("")
    lines.append("   ⏱️  TIMING:")
    lines.append(f"      Total duration: {ctx.total_duration_s:.1f}s")
    for phase, dur in ctx.phase_timings.items():
        lines.append(f"      {phase:24s}: {dur:.2f}s")
    lines.append("")
    lines.append("   📊 TOTALS:")
    lines.append(f"      Chunks:    {ctx.chunks_total}")
    lines.append(f"      Entities:  {ctx.entities_resolved}")
    lines.append(f"      Insights:  {ctx.insights_total}")
    lines.append(f"      Narrative: {ctx.narratives_total}")
    lines.append(f"      Dossiers:  {len(ctx.dossiers_persons) + len(ctx.dossiers_themes)}")
    lines.append(f"      Agents:    {len(ctx.agents_updated)}")
    lines.append("")
    lines.append(_hr_thick())
    lines.append(_center("END EXECUTION REPORT"))
    lines.append(_hr_thick())

    return "\n".join(lines)


# ===========================================================================
# EMITTER 2 — INGESTION GUARD LOG (Sprint 1 #2, NEW dedicated)
# ===========================================================================


def emit_ingestion_guard(verdict: dict[str, Any]) -> str:
    """Phase 0 ingestion guard verdict — NEW-exclusive log.

    Args:
        verdict: dict with keys: action, reason, identity_key, body_hash,
                 word_count, previous_word_count, delta_start_word.

    Returns:
        ASCII block in OLD v5.1 style.
    """
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("INGESTION GUARD VERDICT (Phase 0)"))
    lines.append(_hr_thick())
    lines.append("")
    action = verdict.get("action") or verdict.get("verdict") or "?"
    icon = {
        "process": "✅",
        "NEW": "✅",
        "skip": "⏭️",
        "SKIP": "⏭️",
        "incremental": "🔄",
        "INCREMENTAL": "🔄",
        "corrupted": "❌",
        "CORRUPTED": "❌",
    }.get(action, "❓")
    lines.append(_box_top(f"VERDICT: {icon} {action.upper()}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"Reason:           {str(verdict.get('reason', ''))[:50]}"))
    lines.append(_box_line(f"Identity key:     {str(verdict.get('identity_key', ''))[:50]}"))
    lines.append(_box_line(f"Body hash:        {str(verdict.get('body_hash', ''))[:50]}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"Word count:       {verdict.get('word_count', 0)}"))
    lines.append(_box_line(f"Previous count:   {verdict.get('previous_word_count', 0)}"))
    delta = verdict.get("delta_start_word", 0)
    if delta:
        lines.append(_box_line(f"Delta start:      word #{delta}"))
    lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


# ===========================================================================
# EMITTER 3 — FULL PIPELINE REPORT (Sprint 1 #3)
# ===========================================================================


def emit_full_pipeline_report(
    slug: str,
    phases: dict[str, Any],
    total_duration_s: float,
    success: bool,
) -> str:
    """Full pipeline timeline report — end of cmd_full.

    Args:
        slug: source slug.
        phases: dict of phase_name -> result_dict (subset of cmd_full output).
        total_duration_s: total wall time.
        success: overall success/failure of cmd_full.

    Returns:
        ASCII block: 14-phase timeline with icons + durations.
    """
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("FULL PIPELINE REPORT"))
    lines.append(_center(f"Slug: {slug}"))
    lines.append(_center(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    lines.append(_hr_thick())
    lines.append("")

    overall_icon = "✅" if success else "❌"
    lines.append(
        f"   {overall_icon} OVERALL: {'SUCCESS' if success else 'FAILED'}  "
        f"({total_duration_s:.1f}s total)"
    )
    lines.append("")
    lines.append(_box_top("EXECUTION TIMELINE (14 phases of NEW pipeline)"))
    lines.append(_box_empty())

    # Order matches cmd_full chain
    phase_order = [
        ("ingest", "1. INGEST"),
        ("batch", "2. BATCH"),
        ("process_batch", "3. CHUNK+EMBED (process_batch)"),
        ("insights", "4. INSIGHTS"),
        ("entities", "5. ENTITIES"),
        ("behavioral", "6. BEHAVIORAL (L6)"),
        ("identity", "7. IDENTITY (L7/L9/L10)"),
        ("voice", "8. VOICE DNA (L8)"),
        ("identity_checkpoint", "9. IDENTITY CHECKPOINT"),
        ("consolidate", "10. CONSOLIDATE (DOSSIER)"),
        ("promote_agent", "11. PROMOTE AGENT"),
        ("finalize", "12. FINALIZE (incl. Phase 4.5 RAG)"),
        ("phase8", "13. PHASE 8 GATES (7A-7I)"),
    ]
    for key, label in phase_order:
        p = phases.get(key)
        if p is None:
            icon = "⏭️"
            duration = "—"
            status = "skipped"
        elif isinstance(p, list):
            # process_batch returns a list
            ok = all(b.get("success") for b in p) if p else False
            icon = "✅" if ok else "❌"
            total_ms = sum(b.get("duration_ms", 0) for b in p)
            duration = f"{total_ms / 1000:.1f}s"
            status = f"{len(p)} batches"
        elif isinstance(p, dict):
            ok = p.get("success", False)
            icon = "✅" if ok else "❌"
            duration = f"{p.get('duration_ms', 0) / 1000:.1f}s"
            # extra column for key metric
            if key == "insights":
                status = f"{p.get('insights_extracted', 0)} extracted"
            elif key == "process_batch":
                status = f"{p.get('chunks_indexed', 0)} chunks"
            elif key == "finalize":
                status = f"phase8 gate={p.get('phase8', {}).get('gate_status', '?')}"
            else:
                status = "ok" if ok else p.get("error", "fail")[:30]
        else:
            icon = "❓"
            duration = "?"
            status = "unknown"
        lines.append(_box_line(f"{icon} {label:38s} {duration:>8s}  {status[:25]}"))
    lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    lines.append(_center("END FULL PIPELINE REPORT"))
    lines.append(_hr_thick())

    return "\n".join(lines)


# ===========================================================================
# EMITTER 4 — BATCH LOG (Sprint 1 #4, OLD expanded)
# ===========================================================================


def emit_batch_log(
    batch_id: str,
    slug: str,
    source_code: str,
    file_count: int,
    chunks_created: int,
    dna_extracted: dict[str, int] | None = None,
    insights_total: int = 0,
    high: int = 0,
    medium: int = 0,
    low: int = 0,
) -> str:
    """Per-batch log — emitted after each cmd_process_batch.

    OLD template had 5 DNA layers (FILOSOFIAS, MODELOS, HEURÍSTICAS, FRAMEWORKS,
    METODOLOGIAS). NEW has 10 (L1-L10). Layout preserved; layers expanded.
    """
    lines: list[str] = []
    dna_extracted = dna_extracted or {}
    lines.append(_box_top(f"BATCH-{batch_id} COMPLETE | {source_code} | {file_count} files"))
    lines.append(_box_empty())
    lines.append(_box_line(f"📊 CHUNKS: {chunks_created}    💡 INSIGHTS: {insights_total}"))
    lines.append(_box_line(f"   🔴 HIGH: {high}   🟡 MEDIUM: {medium}   🟢 LOW: {low}"))
    lines.append(_box_empty())
    lines.append(_box_line("🧬 DNA EXTRACTED (10 LAYERS L1-L10):"))
    layer_labels = [
        ("L1", "FILOSOFIAS"),
        ("L2", "MODELOS-MENTAIS"),
        ("L3", "HEURÍSTICAS"),
        ("L4", "FRAMEWORKS"),
        ("L5", "METODOLOGIAS"),
        ("L6", "BEHAVIORAL"),
        ("L7", "VALUES"),
        ("L8", "VOICE-DNA"),
        ("L9", "OBSESSIONS"),
        ("L10", "PARADOXES"),
    ]
    for code, name in layer_labels:
        cnt = dna_extracted.get(name.lower().replace("-", ""), 0)
        if not cnt:
            cnt = dna_extracted.get(code.lower(), 0)
        star = " ★" if code == "L3" and cnt else ""
        lines.append(_box_line(f"   │ {code} {name:18s}: {cnt:>3d}{star}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"📁 Slug: {slug}"))
    lines.append(_box_bot())
    return "\n".join(lines)


# ===========================================================================
# EMITTER 5 — RAG INDEXATION REPORT (Sprint 1 #5, NEW dedicated)
# ===========================================================================


def emit_rag_indexation(rag_result: dict[str, Any]) -> str:
    """Phase 4.5 RAG indexation log — Constitution Art. XV enforcement.

    Args:
        rag_result: dict from cmd_rag_index with keys: success, gate_passed,
                    chunks_pre, chunks_post, chunks_delta, bucket, rebuild_stats.
    """
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("RAG INDEXATION REPORT (Phase 4.5, Art. XV)"))
    lines.append(_hr_thick())
    lines.append("")
    gate = rag_result.get("gate_passed", False)
    icon = "✅" if gate else "❌"
    lines.append(_box_top(f"GATE: {icon} {'PASSED' if gate else 'BLOCKED'}"))
    lines.append(_box_empty())
    # Read real fields: cmd_rag_index returns chunks_pre/chunks_post/chunks_delta
    chunks_pre = rag_result.get("chunks_pre", 0)
    chunks_post = rag_result.get("chunks_post", 0)
    chunks_delta = rag_result.get("chunks_delta", chunks_post - chunks_pre)
    rebuild_stats = rag_result.get("rebuild_stats", {})
    graph_stats = rebuild_stats.get("graph", {}) if isinstance(rebuild_stats, dict) else {}
    lines.append(_box_line(f"Bucket:           {rag_result.get('bucket', '?')}"))
    lines.append(_box_line("Provider:         openai (text-embedding-3-large)"))
    lines.append(_box_line("Dimension:        1536"))
    lines.append(_box_empty())
    lines.append(_box_line(f"Chunks BEFORE:    {chunks_pre}"))
    lines.append(_box_line(f"Chunks AFTER:     {chunks_post}"))
    delta_icon = "🟢" if chunks_delta >= 0 else "🔴"
    lines.append(_box_line(f"Delta:            {delta_icon} {chunks_delta:+d}"))
    if graph_stats:
        ents = graph_stats.get("total_entities", 0)
        edges = graph_stats.get("total_edges", 0)
        lines.append(_box_empty())
        lines.append(_box_line(f"Graph entities:   {ents}"))
        lines.append(_box_line(f"Graph edges:      {edges}"))
    lines.append(_box_empty())
    reason = rag_result.get("gate_reason", "")
    if reason:
        lines.append(_box_line(f"Reason: {str(reason)[:60]}"))
        lines.append(_box_empty())
    if rag_result.get("error"):
        lines.append(_box_line(f"❌ Error: {str(rag_result['error'])[:55]}"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


# ===========================================================================
# UTILITY — write log to disk + stdout
# ===========================================================================


def emit_to(text: str, path: Any = None, stdout: bool = True) -> None:
    """Convenience: print to stdout and/or write to file.

    Keeps emitters pure (no side effects) — callers compose.
    """
    if stdout:
        print(text, flush=True)
    if path is not None:
        from pathlib import Path

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text + "\n", encoding="utf-8")


# ===========================================================================
# SPRINT 2 EMITTERS (Tier 2 — 5 logs)
# ===========================================================================


def emit_llm_cost_log(
    slug: str,
    cost_breakdown: dict[str, Any],
) -> str:
    """LLM Cost + Provider Log — NEW-exclusive.

    Args:
        slug: source slug.
        cost_breakdown: dict with keys: total_usd, by_phase, by_provider,
                        total_input_tokens, total_output_tokens.
    """
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("LLM COST + PROVIDER REPORT"))
    lines.append(_hr_thick())
    lines.append("")
    lines.append(_box_top(f"slug: {slug}"))
    lines.append(_box_empty())
    total = cost_breakdown.get("total_usd", 0.0)
    inp = cost_breakdown.get("total_input_tokens", 0)
    out = cost_breakdown.get("total_output_tokens", 0)
    lines.append(_box_line(f"💰 TOTAL COST:        ${total:.4f}"))
    lines.append(_box_line(f"📥 Input tokens:      {inp:,}"))
    lines.append(_box_line(f"📤 Output tokens:     {out:,}"))
    lines.append(_box_empty())
    by_phase = cost_breakdown.get("by_phase", {})
    if by_phase:
        lines.append(_box_line("BY PHASE:"))
        for phase, cost in sorted(by_phase.items(), key=lambda x: -x[1]):
            lines.append(_box_line(f"   │ {phase:30s}: ${cost:.4f}"))
        lines.append(_box_empty())
    by_prov = cost_breakdown.get("by_provider", {})
    if by_prov:
        lines.append(_box_line("BY PROVIDER:"))
        for prov, cost in by_prov.items():
            lines.append(_box_line(f"   │ {prov:20s}: ${cost:.4f}"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_identity_checkpoint_log(slug: str, checkpoint_result: dict[str, Any]) -> str:
    """Identity Checkpoint Log — Step 9 deterministic cross-layer gate.

    Args:
        checkpoint_result: from cmd_identity_checkpoint. Keys: verdict,
                          reasons, layer_coverage, source_attribution_pct.
    """
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("IDENTITY CHECKPOINT REPORT (Step 9, deterministic gate)"))
    lines.append(_hr_thick())
    lines.append("")
    verdict = (checkpoint_result.get("verdict") or "UNKNOWN").upper()
    icon = {"APPROVE": "✅", "REWORK": "⚠️", "ABORT": "❌", "UNKNOWN": "❓"}.get(verdict, "❓")
    lines.append(_box_top(f"VERDICT: {icon} {verdict}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"Slug:                 {slug}"))
    lines.append(_box_empty())
    cov = checkpoint_result.get("layer_coverage", {}) or {}
    if cov:
        lines.append(_box_line("LAYER COVERAGE:"))
        for layer in ("L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9", "L10"):
            v = cov.get(layer, cov.get(layer.lower(), "—"))
            lines.append(_box_line(f"   │ {layer:4s}: {v}"))
        lines.append(_box_empty())
    sap = checkpoint_result.get("source_attribution_pct", 0)
    if sap:
        lines.append(_box_line(f"📊 Source attribution: {sap:.1f}%"))
        lines.append(_box_empty())
    reasons = checkpoint_result.get("reasons") or []
    if reasons:
        lines.append(_box_line("REASONS:"))
        for r in reasons[:8]:
            lines.append(_box_line(f"   │ • {str(r)[:60]}"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_phase8_gate_log(slug: str, phase8_result: dict[str, Any]) -> str:
    """Phase 8 Gate Log — 9 checks 7A-7I."""
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("PHASE 8 GATE REPORT (7A-7I, 9 checks)"))
    lines.append(_hr_thick())
    lines.append("")
    gate_status = phase8_result.get("gate_status", "UNKNOWN")
    icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(gate_status, "❓")
    lines.append(_box_top(f"GATE STATUS: {icon} {gate_status}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"Slug:    {slug}"))
    lines.append(_box_line(f"Bucket:  {phase8_result.get('bucket', '?')}"))
    lines.append(_box_empty())
    checks = phase8_result.get("gate_checks", {})
    pass_count = 0
    fail_count = 0
    if checks:
        lines.append(_box_line("CHECKS:"))
        for k in sorted(checks.keys()):
            v = checks[k]
            check_icon = "✅" if v else "❌"
            if v:
                pass_count += 1
            else:
                fail_count += 1
            lines.append(_box_line(f"   │ {check_icon} {k}: {'PASS' if v else 'FAIL'}"))
        lines.append(_box_empty())
        lines.append(_box_line(f"📊 Score: {pass_count}/{pass_count + fail_count} passing"))
        lines.append(_box_empty())
    artifacts = phase8_result.get("artifacts_written", []) or []
    if artifacts:
        lines.append(_box_line("ARTIFACTS WRITTEN:"))
        for a in artifacts[:8]:
            lines.append(_box_line(f"   │ ✓ {str(a)[:60]}"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_contradictions_log(slug: str, contradictions: list[dict[str, Any]]) -> str:
    """Contradictions Log — insight conflicts detected (NEW-exclusive)."""
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("CONTRADICTIONS REPORT (insight conflicts)"))
    lines.append(_hr_thick())
    lines.append("")
    total = len(contradictions)
    icon = "✅" if total == 0 else "⚠️"
    lines.append(_box_top(f"{icon} {total} contradiction(s) detected for {slug}"))
    lines.append(_box_empty())
    if total == 0:
        lines.append(_box_line("No conflicting insights detected. DNA coherence OK."))
        lines.append(_box_empty())
    else:
        for i, c in enumerate(contradictions[:10], start=1):
            lines.append(_box_line(f"[{i}] {c.get('id', '?')}"))
            lines.append(_box_line(f"    Type:       {c.get('type', '?')}"))
            lines.append(_box_line(f"    Severity:   {c.get('severity', '?')}"))
            desc = c.get("description", "")[:55]
            if desc:
                lines.append(_box_line(f"    Description: {desc}"))
            lines.append(_box_empty())
        if total > 10:
            lines.append(_box_line(f"... and {total - 10} more"))
            lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_agent_state_log(
    slug: str,
    enrichment_result: dict[str, Any],
    before_bytes: int,
    after_bytes: int,
) -> str:
    """Agent State Log — merged Agent Enrichment + Memory Diff (board consolidation).

    Args:
        slug: agent slug.
        enrichment_result: dict from memory_enricher with appended/skipped_dedup.
        before_bytes: MEMORY.md size before enrichment.
        after_bytes: MEMORY.md size after enrichment.
    """
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("AGENT STATE REPORT (enrichment + memory diff)"))
    lines.append(_hr_thick())
    lines.append("")
    lines.append(_box_top(f"AGENT: {slug}"))
    lines.append(_box_empty())
    appended = enrichment_result.get("appended", 0) if isinstance(enrichment_result, dict) else 0
    skipped = (
        enrichment_result.get("skipped_dedup", 0) if isinstance(enrichment_result, dict) else 0
    )
    delta_bytes = after_bytes - before_bytes
    delta_pct = (delta_bytes / before_bytes * 100) if before_bytes > 0 else 0
    lines.append(_box_line(f"🆕 Insights appended:    {appended}"))
    lines.append(_box_line(f"⏭️  Skipped (dedup):     {skipped}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"📏 MEMORY.md BEFORE:    {before_bytes:,} bytes"))
    lines.append(_box_line(f"📏 MEMORY.md AFTER:     {after_bytes:,} bytes"))
    diff_icon = "🟢" if delta_bytes > 0 else ("🔵" if delta_bytes == 0 else "🔴")
    lines.append(
        _box_line(
            f"📊 Delta:                {diff_icon} {delta_bytes:+,} bytes ({delta_pct:+.1f}%)"
        )
    )
    lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


# ===========================================================================
# SPRINT 3 EMITTERS (Tier 3 — 10 logs)
# ===========================================================================


def emit_ingest_report(
    file_path: str,
    decision: dict[str, Any],
    destination: str,
    word_count: int = 0,
) -> str:
    """INGEST REPORT — emitted after /ingest classify+route+organize."""
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("INGEST REPORT"))
    lines.append(_hr_thick())
    lines.append("")
    lines.append(_box_top("MATERIAL INGESTED"))
    lines.append(_box_empty())
    lines.append(_box_line(f"📥 File:         {file_path}"))
    lines.append(_box_line(f"📊 Words:        {word_count}"))
    lines.append(_box_line(f"📂 Destination:  {destination}"))
    lines.append(_box_empty())
    lines.append(_box_line("ENTITY DECISION:"))
    lines.append(_box_line(f"   ├─ Author:    {decision.get('entity_author') or '(none)'}"))
    lines.append(_box_line(f"   ├─ Subject:   {decision.get('entity_subject') or '(none)'}"))
    lines.append(_box_line(f"   ├─ Confidence:{decision.get('confidence', '?')}"))
    lines.append(_box_line(f"   └─ Verdict:   {decision.get('verdict', '?')}"))
    lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_inbox_status(inbox_summary: dict[str, Any]) -> str:
    """INBOX STATUS — emitted on demand or after batch run."""
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("INBOX STATUS"))
    lines.append(_hr_thick())
    lines.append("")
    total = inbox_summary.get("total_files", 0)
    by_bucket = inbox_summary.get("by_bucket", {})
    by_person = inbox_summary.get("by_person", {})
    pending = inbox_summary.get("pending", 0)
    lines.append(_box_top(f"PENDING: {pending} / TOTAL: {total}"))
    lines.append(_box_empty())
    if by_bucket:
        lines.append(_box_line("BY BUCKET:"))
        for b in ("external", "business", "personal"):
            n = by_bucket.get(b, 0)
            lines.append(_box_line(f"   │ {b:12s}: {n} files"))
        lines.append(_box_empty())
    if by_person:
        lines.append(_box_line("TOP 10 BY PERSON:"))
        items = sorted(by_person.items(), key=lambda x: -x[1])[:10]
        for p, n in items:
            lines.append(_box_line(f"   │ {p[:40]:40s}: {n}"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_system_digest(digest: dict[str, Any]) -> str:
    """SYSTEM DIGEST — operational health snapshot (ad-hoc /digest command)."""
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("MEGA BRAIN SYSTEM DIGEST"))
    lines.append(_hr_thick())
    lines.append("")
    health = digest.get("health_score", 0)
    icon = "🟢" if health >= 90 else ("🟡" if health >= 50 else "🔴")
    lines.append(_box_top(f"HEALTH: {icon} {health}/100"))
    lines.append(_box_empty())
    lines.append(_box_line("KNOWLEDGE BASE:"))
    lines.append(_box_line(f"   │ Persons indexed:    {digest.get('persons_count', 0)}"))
    lines.append(_box_line(f"   │ Insights total:     {digest.get('insights_total', 0)}"))
    lines.append(_box_line(f"   │ Dossiers total:     {digest.get('dossiers_count', 0)}"))
    lines.append(_box_empty())
    lines.append(_box_line("AGENT ECOSYSTEM:"))
    lines.append(_box_line(f"   │ External agents:    {digest.get('agents_external', 0)}"))
    lines.append(_box_line(f"   │ Business agents:    {digest.get('agents_business', 0)}"))
    lines.append(_box_line(f"   │ Cargo agents:       {digest.get('agents_cargo', 0)}"))
    lines.append(_box_empty())
    lines.append(_box_line("RAG INDEXES:"))
    lines.append(_box_line(f"   │ External chunks:    {digest.get('rag_external', 0)}"))
    lines.append(_box_line(f"   │ Business chunks:    {digest.get('rag_business', 0)}"))
    lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_narrative_metabolism(slug: str, narratives_state: dict[str, Any]) -> str:
    """Narrative Metabolism Log — NARRATIVES-STATE v3.1.0 view."""
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("NARRATIVE METABOLISM LOG (v3.1.0)"))
    lines.append(_hr_thick())
    lines.append("")
    lines.append(_box_top(f"slug: {slug}"))
    lines.append(_box_empty())
    persons = narratives_state.get("persons", {}) if isinstance(narratives_state, dict) else {}
    domains = narratives_state.get("by_domain", {}) if isinstance(narratives_state, dict) else {}
    total_narr = 0
    for pdata in persons.values():
        if isinstance(pdata, dict):
            total_narr += len(pdata.get("narratives", []) or [])
    lines.append(_box_line(f"📝 Total narratives: {total_narr}"))
    lines.append(_box_line(f"👥 Persons:          {len(persons)}"))
    lines.append(_box_line(f"🗂️  Domains:          {len(domains)}"))
    lines.append(_box_empty())
    if persons:
        lines.append(_box_line("BY PERSON:"))
        items = sorted(
            (
                (k, len(v.get("narratives", []) if isinstance(v, dict) else []))
                for k, v in persons.items()
            ),
            key=lambda x: -x[1],
        )[:5]
        for p, n in items:
            lines.append(_box_line(f"   │ {p[:35]:35s}: {n} narratives"))
        lines.append(_box_empty())
    if domains:
        lines.append(_box_line("BY DOMAIN:"))
        for d, dval in list(domains.items())[:5]:
            cnt = (
                len(dval)
                if isinstance(dval, list)
                else (dval.get("count", 0) if isinstance(dval, dict) else 0)
            )
            lines.append(_box_line(f"   │ {d[:35]:35s}: {cnt}"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_sources_compilation(slug: str, sources_result: dict[str, Any]) -> str:
    """Sources Compilation Log — per slug sources/ output."""
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("SOURCES COMPILATION LOG"))
    lines.append(_hr_thick())
    lines.append("")
    inner = (
        sources_result.get("sources", sources_result) if isinstance(sources_result, dict) else {}
    )
    status = inner.get("status", "?") if isinstance(inner, dict) else "?"
    files_written = inner.get("files_written", 0) if isinstance(inner, dict) else 0
    icon = {"written": "✅", "skipped": "⏭️", "no_sources": "⚠️", "error": "❌"}.get(status, "❓")
    lines.append(_box_top(f"{icon} status: {status}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"slug:           {slug}"))
    lines.append(_box_line(f"files written:  {files_written}"))
    lines.append(_box_empty())
    paths = inner.get("paths", []) if isinstance(inner, dict) else []
    if paths:
        lines.append(_box_line("WRITTEN PATHS:"))
        for p in paths[:8]:
            lines.append(_box_line(f"   │ ✓ {str(p)[:60]}"))
        lines.append(_box_empty())
    err = inner.get("error") if isinstance(inner, dict) else None
    if err:
        lines.append(_box_line(f"❌ Error: {str(err)[:55]}"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_domain_aggregator(domain_results: dict[str, Any]) -> str:
    """Domain Aggregator Log — MAP-CONFLITOS per domain."""
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("DOMAIN AGGREGATOR LOG (MAP-CONFLITOS per domain)"))
    lines.append(_hr_thick())
    lines.append("")
    if not domain_results:
        lines.append(_box_top("No domain aggregation results"))
        lines.append(_box_empty())
        lines.append(_box_bot())
        lines.append("")
        lines.append(_hr_thick())
        return "\n".join(lines)
    lines.append(_box_top(f"{len(domain_results)} domain(s) aggregated"))
    lines.append(_box_empty())
    for domain, dres in domain_results.items():
        if domain == "error":
            continue
        if not isinstance(dres, dict):
            continue
        status = dres.get("status") or dres.get("agg", {}).get("status", "?")
        confl = dres.get("conflicts_found") or dres.get("agg", {}).get("conflicts_found", 0)
        experts = dres.get("experts_compared") or dres.get("agg", {}).get("experts_compared", 0)
        lines.append(_box_line(f"🗂️  {domain[:30]:30s}"))
        lines.append(_box_line(f"   │ Status:           {status}"))
        lines.append(_box_line(f"   │ Conflicts found:  {confl}"))
        lines.append(_box_line(f"   │ Experts compared: {experts}"))
        lines.append(_box_empty())
    if "error" in domain_results:
        lines.append(_box_line(f"❌ Error: {str(domain_results['error'])[:55]}"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_cross_bucket_cascade(cascade_result: dict[str, Any]) -> str:
    """Cross-bucket Cascade Log — 1 source enriched N buckets (NEW Art. XIII)."""
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("CROSS-BUCKET CASCADE LOG (Art. XIII)"))
    lines.append(_hr_thick())
    lines.append("")
    lines.append(_box_top("Bucket enrichment summary"))
    lines.append(_box_empty())
    for bucket in ("external", "business", "personal"):
        cnt = (
            cascade_result.get(f"{bucket}_updates", cascade_result.get(bucket, 0))
            if isinstance(cascade_result, dict)
            else 0
        )
        icon = "✅" if cnt > 0 else "—"
        lines.append(_box_line(f"   {icon} {bucket:12s}: {cnt} update(s)"))
    lines.append(_box_empty())
    if isinstance(cascade_result, dict):
        cargo = cascade_result.get("cargo_agents_updated", [])
        themes = cascade_result.get("themes_updated", [])
        if cargo:
            lines.append(_box_line(f"🤖 Cargo agents updated: {len(cargo)}"))
            for c in cargo[:5]:
                name = c if isinstance(c, str) else c.get("name", "?")
                lines.append(_box_line(f"   │ • {name}"))
            lines.append(_box_empty())
        if themes:
            lines.append(_box_line(f"🗂️  Themes updated: {len(themes)}"))
            for t in themes[:5]:
                name = t if isinstance(t, str) else t.get("name", "?")
                lines.append(_box_line(f"   │ • {name}"))
            lines.append(_box_empty())
        if cascade_result.get("error"):
            lines.append(_box_line(f"❌ Error: {str(cascade_result['error'])[:55]}"))
            lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_workspace_sync(sync_result: dict[str, Any]) -> str:
    """Workspace Sync Log — L0-L4 deltas (NEW Art. XIV)."""
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("WORKSPACE SYNC LOG (L0-L4, Art. XIV)"))
    lines.append(_hr_thick())
    lines.append("")
    lines.append(_box_top("Workspace layer deltas"))
    lines.append(_box_empty())
    if not isinstance(sync_result, dict) or not sync_result:
        lines.append(_box_line("(no workspace sync data — slug not bound to BU)"))
        lines.append(_box_empty())
    else:
        total_artifacts = 0
        for layer in ("L0", "L1", "L2", "L3", "L4"):
            cnt = sync_result.get(layer, 0)
            if not cnt and isinstance(sync_result.get(layer.lower()), int):
                cnt = sync_result[layer.lower()]
            total_artifacts += cnt if isinstance(cnt, int) else 0
            icon = "✅" if (isinstance(cnt, int) and cnt > 0) else "—"
            lines.append(_box_line(f"   {icon} {layer}: +{cnt if cnt else 0} artifact(s)"))
        lines.append(_box_empty())
        lines.append(_box_line(f"📊 Total artifacts touched: {total_artifacts}"))
        lines.append(_box_empty())
        bu = sync_result.get("business_unit")
        if bu:
            lines.append(_box_line(f"BU: {bu}"))
            lines.append(_box_empty())
        if sync_result.get("error"):
            lines.append(_box_line(f"❌ Error: {str(sync_result['error'])[:55]}"))
            lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_squad_activation(squads_activated: list[dict[str, Any]]) -> str:
    """Squad Activation Log — 79 squads NEW exclusive.

    Best-effort: when no source events exist yet, prints empty placeholder.
    """
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("SQUAD ACTIVATION LOG"))
    lines.append(_hr_thick())
    lines.append("")
    n = len(squads_activated)
    lines.append(_box_top(f"{n} squad(s) activated this run"))
    lines.append(_box_empty())
    if n == 0:
        lines.append(_box_line("(no squad activations recorded — instrumentation pending)"))
        lines.append(_box_empty())
    else:
        for s in squads_activated[:10]:
            name = s.get("squad", "?")[:30] if isinstance(s, dict) else str(s)[:30]
            task = s.get("task", "?")[:30] if isinstance(s, dict) else ""
            agent = s.get("agent", "?")[:25] if isinstance(s, dict) else ""
            lines.append(_box_line(f"   │ {name:30s} → {agent:25s} ({task})"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


def emit_jsonl_trigger_summary(triggers: list[dict[str, Any]]) -> str:
    """JSONL Trigger summary — auto-advance triggers from pipeline-orchestrator.jsonl."""
    lines: list[str] = []
    lines.append(_hr_thick())
    lines.append(_center("AUTO-ADVANCE TRIGGER LOG (JSONL summary)"))
    lines.append(_hr_thick())
    lines.append("")
    n = len(triggers)
    lines.append(_box_top(f"{n} trigger event(s) in last run"))
    lines.append(_box_empty())
    if n == 0:
        lines.append(_box_line("(no auto-advance triggers recorded)"))
        lines.append(_box_empty())
    else:
        by_route: dict[str, int] = {}
        for t in triggers:
            r = t.get("route", "?") if isinstance(t, dict) else "?"
            by_route[r] = by_route.get(r, 0) + 1
        lines.append(_box_line("BY ROUTE:"))
        for r, cnt in sorted(by_route.items(), key=lambda x: -x[1]):
            lines.append(_box_line(f"   │ {r:30s}: {cnt}"))
        lines.append(_box_empty())
        lines.append(_box_line("RECENT (last 5):"))
        for t in triggers[-5:]:
            if isinstance(t, dict):
                ts = t.get("timestamp", "")[:19]
                r = t.get("route", "?")[:25]
                detail = str(t.get("detail", ""))[:30]
                lines.append(_box_line(f"   │ {ts} {r:25s} {detail}"))
        lines.append(_box_empty())
    lines.append(_box_bot())
    lines.append("")
    lines.append(_hr_thick())
    return "\n".join(lines)


# ===========================================================================
# COGNITIVE CMD EMITTERS (Story MCE-6.0.1 — 5 rich ASCII boxes for cognitive
# cmds that previously passed ascii_block="" to emit_phase_payload)
# ===========================================================================


def emit_execution_insights_box(slug: str, metrics: dict[str, Any]) -> str:
    """Rich ASCII box for cmd_insights (template_id: execution_insights).

    Args:
        slug: source slug.
        metrics: dict with keys from emit_phase_payload metrics arg:
                 insights_extracted, batches_processed, batches_failed.
                 Optional additional keys: duration_ms, cost_usd, high, medium, low.
    """
    lines: list[str] = []
    insights_extracted = metrics.get("insights_extracted", 0)
    batches_processed = metrics.get("batches_processed", 0)
    batches_failed = metrics.get("batches_failed", 0)
    duration_s = metrics.get("duration_ms", 0) / 1000.0
    cost_usd = metrics.get("cost_usd", 0.0)
    high = metrics.get("high", metrics.get("insights_high", 0))
    medium = metrics.get("medium", metrics.get("insights_medium", 0))
    low = metrics.get("low", metrics.get("insights_low", 0))

    lines.append(_box_top(f"EXECUTION: cmd_insights | {slug}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"💡 INSIGHTS EXTRACTED: {insights_extracted}"))
    if high or medium or low:
        lines.append(_box_line(f"   🔴 HIGH: {high}   🟡 MEDIUM: {medium}   🟢 LOW: {low}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"📊 BATCHES PROCESSED: {batches_processed}"))
    if batches_failed:
        lines.append(_box_line(f"   ❌ Failed: {batches_failed}"))
    lines.append(_box_empty())
    if duration_s > 0:
        lines.append(_box_line(f"⏱️  DURATION: {duration_s:.1f}s"))
    if cost_usd:
        lines.append(_box_line(f"💰 COST: ${cost_usd:.4f}"))
    lines.append(_box_empty())
    lines.append(_box_bot())
    return "\n".join(lines)


def emit_execution_behavioral_box(slug: str, metrics: dict[str, Any]) -> str:
    """Rich ASCII box for cmd_behavioral (template_id: execution_behavioral).

    Args:
        slug: source slug.
        metrics: dict with keys: patterns_extracted, llm_used.
                 Optional: duration_ms, extraction_skipped.
    """
    lines: list[str] = []
    patterns_extracted = metrics.get("patterns_extracted", 0)
    llm_used = metrics.get("llm_used", False)
    duration_s = metrics.get("duration_ms", 0) / 1000.0
    skipped = metrics.get("extraction_skipped", False)

    status_icon = "✅" if patterns_extracted > 0 else ("⏭️" if skipped else "⚠️")
    lines.append(_box_top(f"EXECUTION: cmd_behavioral | {slug}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"🧬 BEHAVIORAL PATTERNS (L6): {patterns_extracted}"))
    lines.append(
        _box_line(
            f"   {status_icon} Extraction: {'skipped (no insights)' if skipped else 'completed'}"
        )
    )
    lines.append(_box_empty())
    lines.append(_box_line(f"🤖 LLM USED: {'yes' if llm_used else 'no (deterministic)'}"))
    lines.append(_box_empty())
    if duration_s > 0:
        lines.append(_box_line(f"⏱️  DURATION: {duration_s:.1f}s"))
    lines.append(_box_empty())
    lines.append(_box_bot())
    return "\n".join(lines)


def emit_execution_voice_box(slug: str, metrics: dict[str, Any]) -> str:
    """Rich ASCII box for cmd_voice (template_id: execution_voice).

    Args:
        slug: source slug.
        metrics: dict with keys: signature_phrases, llm_used.
                 Optional: duration_ms, extraction_skipped.
    """
    lines: list[str] = []
    signature_phrases = metrics.get("signature_phrases", 0)
    llm_used = metrics.get("llm_used", False)
    duration_s = metrics.get("duration_ms", 0) / 1000.0
    skipped = metrics.get("extraction_skipped", False)

    status_icon = "✅" if signature_phrases > 0 else ("⏭️" if skipped else "⚠️")
    lines.append(_box_top(f"EXECUTION: cmd_voice | {slug}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"📊 VOICE DNA (L8) — SIGNATURE PHRASES: {signature_phrases}"))
    lines.append(
        _box_line(
            f"   {status_icon} Extraction: {'skipped (no insights)' if skipped else 'completed'}"
        )
    )
    lines.append(_box_empty())
    lines.append(_box_line(f"🤖 LLM USED: {'yes' if llm_used else 'no (deterministic)'}"))
    lines.append(_box_empty())
    if duration_s > 0:
        lines.append(_box_line(f"⏱️  DURATION: {duration_s:.1f}s"))
    lines.append(_box_empty())
    lines.append(_box_bot())
    return "\n".join(lines)


def emit_execution_identity_box(slug: str, metrics: dict[str, Any]) -> str:
    """Rich ASCII box for cmd_identity (template_id: execution_identity).

    Args:
        slug: source slug.
        metrics: dict with keys: values_extracted, obsessions_extracted,
                 paradoxes_extracted, llm_used.
                 Optional: duration_ms, extraction_skipped.
    """
    lines: list[str] = []
    values_extracted = metrics.get("values_extracted", 0)
    obsessions_extracted = metrics.get("obsessions_extracted", 0)
    paradoxes_extracted = metrics.get("paradoxes_extracted", 0)
    llm_used = metrics.get("llm_used", False)
    duration_s = metrics.get("duration_ms", 0) / 1000.0
    skipped = metrics.get("extraction_skipped", False)
    total = values_extracted + obsessions_extracted + paradoxes_extracted

    status_icon = "✅" if total > 0 else ("⏭️" if skipped else "⚠️")
    lines.append(_box_top(f"EXECUTION: cmd_identity | {slug}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"🧬 IDENTITY LAYERS (L7/L9/L10): {total} elements"))
    lines.append(_box_line(f"   ├─ L7 Values:    {values_extracted}"))
    lines.append(_box_line(f"   ├─ L9 Obsessions:{obsessions_extracted}"))
    lines.append(_box_line(f"   └─ L10 Paradoxes:{paradoxes_extracted}"))
    lines.append(
        _box_line(
            f"   {status_icon} Extraction: {'skipped (no insights)' if skipped else 'completed'}"
        )
    )
    lines.append(_box_empty())
    lines.append(_box_line(f"🤖 LLM USED: {'yes' if llm_used else 'no (deterministic)'}"))
    lines.append(_box_empty())
    if duration_s > 0:
        lines.append(_box_line(f"⏱️  DURATION: {duration_s:.1f}s"))
    lines.append(_box_empty())
    lines.append(_box_bot())
    return "\n".join(lines)


def emit_consolidate_dossier_box(slug: str, metrics: dict[str, Any]) -> str:
    """Rich ASCII box for cmd_consolidate (template_id: consolidate_dossier).

    Args:
        slug: source slug.
        metrics: dict with keys: dossier_status, sections_filled, size_bytes, llm_used.
                 Optional: duration_ms.
    """
    lines: list[str] = []
    dossier_status = metrics.get("dossier_status", "?")
    sections_filled = metrics.get("sections_filled", 0)
    size_bytes = metrics.get("size_bytes", 0)
    llm_used = metrics.get("llm_used", False)
    duration_s = metrics.get("duration_ms", 0) / 1000.0

    status_icon = {
        "written": "✅",
        "skipped": "⏭️",
        "error": "❌",
    }.get(dossier_status, "⚠️")
    size_kb = size_bytes / 1024.0

    lines.append(_box_top(f"EXECUTION: cmd_consolidate | {slug}"))
    lines.append(_box_empty())
    lines.append(_box_line(f"📚 DOSSIER: {status_icon} {dossier_status.upper()}"))
    lines.append(_box_line(f"   ├─ Sections filled: {sections_filled}"))
    lines.append(_box_line(f"   └─ Size: {size_kb:.1f} KB ({size_bytes} bytes)"))
    lines.append(_box_empty())
    lines.append(_box_line(f"🤖 LLM USED: {'yes' if llm_used else 'no (deterministic)'}"))
    lines.append(_box_empty())
    if duration_s > 0:
        lines.append(_box_line(f"⏱️  DURATION: {duration_s:.1f}s"))
    lines.append(_box_empty())
    lines.append(_box_bot())
    return "\n".join(lines)
