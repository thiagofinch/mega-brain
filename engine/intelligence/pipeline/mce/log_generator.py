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
    - Imports from engine.paths.
    - Non-fatal: never blocks the pipeline.

Version: 2.1.0
Date: 2026-05-29
Design System: CHRONICLER v2.1.0
Story: MCE-13.10 — 23 sections total (7 original + 16 new)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from engine.paths import ARTIFACTS, LOGS, MISSION_CONTROL, ROOT

# Import centralized person name resolver from the Data Collector (S-01).
# Falls back to inline capitalize if the import fails (e.g. circular import
# or missing dependency).
try:
    from engine.intelligence.pipeline.mce.chronicler_data_collector import (
        resolve_person_name as _resolve_person_name,
    )

    _HAS_DATA_COLLECTOR = True
except ImportError:
    _HAS_DATA_COLLECTOR = False

# Import centralized ROLE-TRACKING reader (Story MCE-17.0 Fase 2 T7).
# Falls back to None so all call sites can guard and degrade gracefully.
try:
    from engine.intelligence.pipeline.mce.role_tracker_reader import (
        find_person as _rt_find_person,
        iter_persons as _rt_iter_persons,
        load_role_tracking as _rt_load,
    )

    _HAS_ROLE_TRACKER_READER = True
except ImportError:
    _HAS_ROLE_TRACKER_READER = False
    _rt_load = None  # type: ignore[assignment]
    _rt_iter_persons = None  # type: ignore[assignment]
    _rt_find_person = None  # type: ignore[assignment]

logger = logging.getLogger("mce.log_generator")

# MCE-17.0 T10: When MCE_NO_FALLBACK=1 the disk fallback path is disabled.
# _with_disk_fallback returns a sentinel dict instead of reading disk data,
# forcing every STEP to show an explicit FAIL rather than silently masking
# missing stream data with stale disk values.
MCE_NO_FALLBACK: bool = os.getenv("MCE_NO_FALLBACK", "0").lower() in ("1", "true", "yes")

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
    # DEPRECATED: delegate to chronicler_data_collector.collect_final_log_data()
    # for centralized loading.  Kept for backward compatibility until all callers
    # are migrated (see S-07).
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
    # DEPRECATED: delegate to chronicler_data_collector.collect_final_log_data()
    # for centralized loading.  Kept for backward compatibility until all callers
    # are migrated (see S-07).
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


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION CHECKLIST  (V1 — 2026-05-13)
# ═══════════════════════════════════════════════════════════════════════════════
#
# WHY: the previous validation block in this file ran 7 checks focused on
# final artifacts only (CHUNKS-STATE, INSIGHTS-STATE, DNA Elements, Memory
# Enrichment, RAG indexes, Knowledge Graph). That misleads operators into
# thinking the pipeline is COMPLETE/7 when the MCE template officially
# declares 12 steps (Classification, Organization, Chunking, Entity
# Resolution, Insight Extraction, MCE Behavioral, MCE Identity, MCE Voice,
# Identity Checkpoint, Consolidation, Agent Generation, Validation Final).
#
# This helper produces ONE check per template step, with an independent
# reader that fails GRACEFULLY when an upstream artifact is missing
# (returns "pending (Step N)" instead of crashing). Pipeline can therefore
# report an honest N/12 even before frentes 5-7 are wired.
# ─────────────────────────────────────────────────────────────────────────────


def _read_yaml_safe(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None
    except Exception:
        return None


def _bucket_for(slug: str, fallback: str = "external") -> str:
    """Best-effort bucket detection (mirrors chronicler_data_collector logic)."""
    for b in ("personal", "business", "external"):
        if (ROOT / "agents" / b / slug).is_dir():
            return b
        if (ROOT / "knowledge" / b / "dna" / "persons" / slug).is_dir():
            return b
    return fallback


def _check_classification(metadata: dict[str, Any]) -> tuple[bool, str]:
    cls = metadata.get("classification") if isinstance(metadata, dict) else None
    if not isinstance(cls, dict):
        return False, "pending (Step 1) — no classification block"
    conf = cls.get("confidence")
    try:
        conf_v = float(conf) if conf is not None else 0.0
    except (TypeError, ValueError):
        conf_v = 0.0
    ok = conf_v >= 0.5
    return ok, f"confidence={conf_v:.2f}"


def _check_organization(metadata: dict[str, Any]) -> tuple[bool, str]:
    org = metadata.get("organization") if isinstance(metadata, dict) else None
    routing = metadata.get("routing") if isinstance(metadata, dict) else None
    if isinstance(org, dict) and int(org.get("organized", 0) or 0) > 0:
        return True, f"{org.get('organized')} files organized"
    if isinstance(routing, dict) and routing.get("action") == "moved":
        return True, f"routed → {routing.get('destination', 'destination')}"
    if isinstance(metadata, dict) and metadata.get("source_path"):
        # Has source_path means orchestrator at least classified+routed it.
        return True, "source registered"
    return False, "pending (Step 2) — no organization signal"


def _check_chunking(chunks_count: int) -> tuple[bool, str]:
    return chunks_count > 0, f"{chunks_count} chunks"


def _check_entity_resolution(slug: str) -> tuple[bool, str]:
    candidates = [
        ARTIFACTS / "mce" / slug / "CANONICAL-MAP.json",
        ARTIFACTS / "canonical" / slug / "CANONICAL-MAP.json",
        ARTIFACTS / "canonical" / "canonical" / "CANONICAL-MAP.json",  # legacy
    ]
    for cm in candidates:
        if cm.exists():
            try:
                data = json.loads(cm.read_text(encoding="utf-8"))
                ents = data.get("entities") or data.get("canonical_entities") or {}
                n = len(ents) if isinstance(ents, dict | list) else 0
                return n > 0, f"{n} canonical entities ({cm.name})"
            except Exception:
                continue
    return False, "pending (Step 4) — no CANONICAL-MAP.json"


def _check_insight_extraction(person_insights: int) -> tuple[bool, str]:
    return person_insights > 0, f"{person_insights} insights"


def _check_mce_behavioral(slug: str, bucket: str) -> tuple[bool, str]:
    path = ROOT / "knowledge" / bucket / "dna" / "persons" / slug / "behavioral-patterns.yaml"
    data = _read_yaml_safe(path)
    if not data:
        return False, "pending (Step 6) — behavioral-patterns.yaml missing"
    patterns = data.get("patterns") if isinstance(data, dict) else data
    n = len(patterns) if isinstance(patterns, list) else 0
    return n > 0, f"{n} behavioral patterns"


def _check_mce_identity(slug: str, bucket: str, dna: dict[str, int]) -> tuple[bool, str]:
    values_path = ROOT / "knowledge" / bucket / "dna" / "persons" / slug / "values-hierarchy.yaml"
    obs_path = ROOT / "knowledge" / bucket / "dna" / "persons" / slug / "obsessions.yaml"
    par_path = ROOT / "knowledge" / bucket / "dna" / "persons" / slug / "paradoxes.yaml"
    present = sum(1 for p in (values_path, obs_path, par_path) if p.exists())
    obs_n = int(dna.get("OBSESSIONS", 0) or 0)
    par_n = int(dna.get("PARADOXES", 0) or 0)
    # Pass if all 3 yamls exist AND at least one obsession or paradox is filled.
    ok = present == 3 and (obs_n > 0 or par_n > 0)
    detail = f"{present}/3 yamls · obs={obs_n} par={par_n}"
    if present < 3:
        return False, f"pending (Step 7) — {detail}"
    return ok, detail


def _check_mce_voice(slug: str, bucket: str) -> tuple[bool, str]:
    path = ROOT / "knowledge" / bucket / "dna" / "persons" / slug / "voice-dna.yaml"
    data = _read_yaml_safe(path)
    if not data or not isinstance(data, dict):
        return False, "pending (Step 8) — voice-dna.yaml missing"
    phrases = data.get("signature_phrases") or data.get("signature_phrases", [])
    n = len(phrases) if isinstance(phrases, list) else 0
    return n >= 5, f"{n} signature phrases"


def _check_identity_checkpoint(slug: str) -> tuple[bool, str]:
    path = MISSION_CONTROL / "mce" / slug / "checkpoints" / "identity-checkpoint.json"
    if not path.exists():
        return False, "pending (Step 9) — identity-checkpoint.json missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        decision = data.get("decision") or data.get("verdict")
        return decision in ("APPROVE", "PASS", "approved"), f"decision={decision}"
    except Exception as exc:
        return False, f"pending (Step 9) — unreadable: {exc}"


def _check_consolidation(slug: str, bucket: str) -> tuple[bool, str]:
    dossier = ROOT / "knowledge" / bucket / "dossiers" / "persons" / f"dossier-{slug}.md"
    if not dossier.exists():
        return False, f"pending (Step 10) — dossier-{slug}.md missing"
    size = dossier.stat().st_size
    if size < 2048:
        return False, f"{size} bytes (< 2048 threshold)"

    # MCE-3.2: also audit inline chunk-refs ratio (>= 80% required for PASS).
    detail = f"{size} bytes"
    passes = True
    try:
        from engine.intelligence.dossier_auditor import audit_dossier_chunk_refs

        audit = audit_dossier_chunk_refs(dossier)
        ratio = audit.get("ratio", 0.0)
        verdict = audit.get("verdict", "FAIL")
        detail = f"{size} bytes · chunk_refs ratio={ratio} verdict={verdict}"
        passes = verdict == "PASS"
    except Exception as exc:  # pragma: no cover — defensive
        detail = f"{size} bytes (auditor unavailable: {exc})"

    # MCE-3.16: surface density indicator in consolidation detail.
    try:
        from engine.intelligence.density import (
            compute_dossier_density,
            density_label,
            render_density_indicator,
        )

        d = compute_dossier_density(slug, bucket)
        score = int(d.get("density", 0))
        detail += f" · densidade={render_density_indicator(score)} {density_label(score)}"
    except Exception:  # pragma: no cover — observability never blocks
        pass

    return passes, detail


def _check_agent_generation(slug: str, bucket: str) -> tuple[bool, str]:
    """Validate Step 11 — Agent Generation (Echo).

    Pass criteria (any one is sufficient when a status field is absent):
      * Frontmatter ``status: complete|populated|active`` (explicit signal)
      * Frontmatter has ``mce_run:`` (i.e. agent was run through the
        cascading pipeline at least once)
      * Frontmatter ``version`` >= ``1.0.0`` (semantic signal that the
        agent has graduated from skeleton).

    Skeleton/stub/placeholder is always a FAIL.
    """
    base = ROOT / "agents" / bucket / slug
    if not base.is_dir():
        return False, f"pending (Step 11) — agents/{bucket}/{slug}/ missing"
    # Tolerate both AGENT.md and agent.md
    for candidate in ("AGENT.md", "agent.md"):
        agent_md = base / candidate
        if not agent_md.exists():
            continue
        try:
            text = agent_md.read_text(encoding="utf-8")
        except Exception:
            continue
        # Parse frontmatter
        status_val: str | None = None
        version_val: str | None = None
        has_mce_run = False
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                fm = text[3:end]
                for line in fm.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("status:"):
                        status_val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                    elif stripped.startswith("version:"):
                        version_val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                    elif stripped.startswith("mce_run:"):
                        has_mce_run = True

        # Explicit skeleton signal — always fail
        if status_val and status_val.lower() in ("skeleton", "stub", "placeholder"):
            return False, f"{candidate} status={status_val}"

        # Positive signals
        if status_val and status_val.lower() in ("complete", "populated", "active", "production"):
            return True, f"{candidate} status={status_val}"
        if has_mce_run:
            return True, f"{candidate} mce_run present (pipeline-ran)"
        if version_val:
            # Major version >= 1 implies graduated from skeleton.
            try:
                major = int(version_val.split(".")[0])
                if major >= 1:
                    return True, f"{candidate} version={version_val}"
            except (ValueError, IndexError):
                pass

        return (
            False,
            f"{candidate} unverified (status={status_val or 'absent'}, ver={version_val or 'absent'})",
        )
    return False, f"pending (Step 11) — no AGENT.md/agent.md in agents/{bucket}/{slug}/"


def _validation_checks_12(
    slug: str,
    *,
    metadata: dict[str, Any],
    chunks_count: int,
    person_insights: int,
    dna: dict[str, int],
    bucket: str,
) -> list[tuple[str, bool, str]]:
    """Build 12 checks aligned to MCE-PIPELINE-LOG-TEMPLATE.md.

    Each check is a tuple of (name, passed: bool, detail: str). Names mirror
    the template section headings (Classification/Organization/Chunking/...).
    Failing checks describe WHY (``pending (Step N) — <reason>``) so operators
    know which frente still needs to land.
    """
    bucket = bucket or _bucket_for(slug)

    checks: list[tuple[str, bool, str]] = []

    p, d = _check_classification(metadata)
    checks.append(("Classification (Atlas)", p, d))

    p, d = _check_organization(metadata)
    checks.append(("Organization (Atlas)", p, d))

    p, d = _check_chunking(chunks_count)
    checks.append(("Chunking (Sage)", p, d))

    p, d = _check_entity_resolution(slug)
    checks.append(("Entity Resolution (Sage)", p, d))

    p, d = _check_insight_extraction(person_insights)
    checks.append(("Insight Extraction (Sage)", p, d))

    p, d = _check_mce_behavioral(slug, bucket)
    checks.append(("MCE Behavioral (Sage)", p, d))

    p, d = _check_mce_identity(slug, bucket, dna)
    checks.append(("MCE Identity (Sage)", p, d))

    p, d = _check_mce_voice(slug, bucket)
    checks.append(("MCE Voice (Sage)", p, d))

    p, d = _check_identity_checkpoint(slug)
    checks.append(("Identity Checkpoint (Lens)", p, d))

    p, d = _check_consolidation(slug, bucket)
    checks.append(("Consolidation (Forge)", p, d))

    p, d = _check_agent_generation(slug, bucket)
    checks.append(("Agent Generation (Echo)", p, d))

    # Step 12 — meta-check on 1..11
    prev_pass = sum(1 for _, ok, _ in checks if ok)
    prev_total = len(checks)
    final_ok = prev_pass == prev_total
    final_detail = f"{prev_pass}/{prev_total} prior steps passed"
    checks.append(("Validation Final (Lens)", final_ok, final_detail))

    return checks


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
    title = "M C E   P I P E L I N E   L O G"
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
    card_w = 24

    lines = [
        f"╭{'─' * (W - 2)}╮",
        f"│{_pad('                                    📊 PAINEL DE METRICAS', W - 2)}│",
        f"│{_pad('', W - 2)}│",
    ]

    # Build card rows
    for row_start in range(0, len(metrics), 4):
        row = metrics[row_start : row_start + 4]
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
        card_exps = "   ".join(
            f"│{_pad('[' + m[2] + ']', card_w, ' ').center(card_w)}│" for m in row
        )
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
    lines.append(
        f"║{_pad('                                                          — Chronicler', W - 2)}║"
    )
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
# PHASE-STREAM LOADER  (Story MCE-13.10)
# ═══════════════════════════════════════════════════════════════════════════════


def _load_phase_stream(slug: str) -> dict[str, Any]:
    """Load PHASE-STREAM.jsonl and return a dict keyed by template_id.

    When a template_id appears multiple times, the LAST occurrence wins
    (matches the run-order semantics of the pipeline).  Returns ``{}`` if the
    file is missing or unreadable — callers are expected to handle empty dicts
    gracefully (null-safe pattern).
    """
    path = ARTIFACTS / "pipeline" / slug / "PHASE-STREAM.jsonl"
    if not path.exists():
        return {}
    result: dict[str, Any] = {}
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                entry = json.loads(raw_line)
                tid = entry.get("template_id")
                if tid:
                    result[tid] = entry.get("metrics", {}) or {}
            except Exception:
                continue
    except Exception:
        pass
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# NEW SECTION RENDERERS  (Story MCE-13.10 — sections 8-23)
# ═══════════════════════════════════════════════════════════════════════════════

_NO_DATA = "_(seção sem dados nesta execução)_"


def _render_section_8_ingestion_guard(data: dict[str, Any]) -> list[str]:
    """Section 8 — INGESTION GUARD VERDICT (Phase 0).

    Source: template_id=ingestion_guard in PHASE-STREAM.jsonl.
    """
    if not data:
        return _nested_box("INGESTION GUARD VERDICT", [_NO_DATA])

    action = str(data.get("action", "unknown")).upper()
    action_icon = {"SKIP": "⏭️", "PROCESS": "✅", "INCREMENTAL": "🔄"}.get(action, "❓")
    reason = str(data.get("reason", "(sem motivo)"))
    identity_key = str(data.get("identity_key", "(ausente)"))
    body_hash_full = str(data.get("body_hash", ""))
    body_hash = body_hash_full[:16] + "..." if len(body_hash_full) > 16 else body_hash_full
    word_count = data.get("word_count", 0)
    previous_word_count = data.get("previous_word_count", 0)
    delta_start_word = data.get("delta_start_word", 0)

    return _nested_box(
        "INGESTION GUARD VERDICT",
        [
            f"Action:             {action_icon} {action}",
            f"Reason:             {reason}",
            "",
            f"Identity Key:       {identity_key}",
            f"Body Hash (16ch):   {body_hash}",
            "",
            f"Word Count:         {word_count}",
            f"Previous Count:     {previous_word_count}",
            f"Delta Start Word:   {delta_start_word}",
        ],
    )


def _render_section_9_rag_indexation(data: dict[str, Any]) -> list[str]:
    """Section 9 — RAG INDEXATION REPORT (Art. XV).

    Source: template_id=rag_indexation in PHASE-STREAM.jsonl.
    """
    if not data:
        return _nested_box("RAG INDEXATION REPORT (Art. XV)", [_NO_DATA])

    chunks_pre = data.get("chunks_pre", 0)
    chunks_post = data.get("chunks_post", 0)
    chunks_delta = data.get("chunks_delta", chunks_post - chunks_pre)
    gate_tolerance = data.get("gate_tolerance", 20)
    gate_passed = data.get("gate_passed", False)
    gate_bypassed = data.get("gate_bypassed", False)
    gate_reason = str(data.get("gate_reason", "(sem motivo)"))
    gate_bypass_reason = str(data.get("gate_bypass_reason", ""))
    vectors_updated = data.get("vectors_updated", False)
    duration_ms = data.get("duration_ms", 0)

    if gate_bypassed:
        gate_status_str = "🟡 BYPASSED"
    elif gate_passed:
        gate_status_str = "✅ PASS"
    else:
        gate_status_str = "❌ FAIL"

    content = [
        f"Gate Status:        {gate_status_str}",
        f"Gate Tolerance:     {gate_tolerance}%",
        f"Gate Reason:        {gate_reason}",
    ]
    if gate_bypassed and gate_bypass_reason:
        content.append(f"Bypass Reason:      {gate_bypass_reason}")
    content += [
        "",
        f"{'Metric':<20} {'Value':>12}",
        f"{'─' * 34}",
        f"{'Chunks Pre':<20} {chunks_pre:>12}",
        f"{'Chunks Post':<20} {chunks_post:>12}",
        f"{'Chunks Delta':<20} {chunks_delta:>+12}",
        f"{'Vectors Updated':<20} {'✅ Yes' if vectors_updated else '❌ No':>12}",
        f"{'Duration (ms)':<20} {int(duration_ms):>12}",
    ]

    return _nested_box("RAG INDEXATION REPORT (Art. XV)", content)


def _render_section_10_knowledge_graph(data: dict[str, Any]) -> list[str]:
    """Section 10 — KNOWLEDGE GRAPH STATS.

    Source: template_id=rag_indexation -> rebuild_stats.graph in PHASE-STREAM.jsonl.
    """
    graph_data = (data.get("rebuild_stats") or {}).get("graph") or {}
    if not graph_data:
        return _nested_box("KNOWLEDGE GRAPH STATS", [_NO_DATA])

    total_entities = graph_data.get("total_entities", 0)
    total_edges = graph_data.get("total_edges", 0)
    entities_by_type: dict[str, int] = graph_data.get("entities_by_type") or {}
    edges_by_type: dict[str, int] = graph_data.get("edges_by_type") or {}

    content = [
        f"Total Entities:     {total_entities}",
        f"Total Edges:        {total_edges}",
        "",
        f"{'Entity Type':<24} {'Count':>6}   {'Edge Type':<24} {'Count':>6}",
        f"{'─' * 24} {'─' * 6}   {'─' * 24} {'─' * 6}",
    ]

    entity_types = [
        "pessoa", "behavioral_pattern", "value", "filosofia", "modelo_mental",
        "heuristica", "framework", "metodologia", "obsession", "paradox", "voice_trait",
    ]
    edge_types = [
        "MANIFESTA", "PRIORIZA", "TEM", "OBSECADO_COM", "TENSIONA_PARADOXO", "EXPRESSA",
    ]

    max_rows = max(len(entity_types), len(edge_types))
    for i in range(max_rows):
        et = entity_types[i] if i < len(entity_types) else ""
        ev = entities_by_type.get(et, 0) if et else ""
        ed = edge_types[i] if i < len(edge_types) else ""
        edv = edges_by_type.get(ed, 0) if ed else ""
        ev_str = f"{ev:>6}" if isinstance(ev, int) else "      "
        edv_str = f"{edv:>6}" if isinstance(edv, int) else "      "
        content.append(f"{et:<24} {ev_str}   {ed:<24} {edv_str}")

    return _nested_box("KNOWLEDGE GRAPH STATS", content)


def _render_section_11_identity_checkpoint_deep(slug: str) -> list[str]:
    """Section 11 — IDENTITY CHECKPOINT (deep view).

    Source: .claude/mission-control/mce/<slug>/checkpoints/identity-checkpoint.json
    """
    path = MISSION_CONTROL / "mce" / slug / "checkpoints" / "identity-checkpoint.json"
    if not path.exists():
        return _nested_box("IDENTITY CHECKPOINT (deep view)", [_NO_DATA])

    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _nested_box("IDENTITY CHECKPOINT (deep view)", [_NO_DATA])

    verdict = str(data.get("verdict", "UNKNOWN")).upper()
    verdict_icon = {"APPROVE": "✅", "PASS": "✅", "REVISE": "⚠️", "FAIL": "❌", "REJECT": "❌"}.get(
        verdict, "❓"
    )
    recommendation = str(data.get("recommendation", "(sem recomendação)"))
    evidence: dict[str, Any] = data.get("evidence") or {}
    checks: dict[str, Any] = data.get("checks") or {}

    insights_total = evidence.get("insights_total", 0)
    by_layer: dict[str, int] = evidence.get("by_layer") or {}
    voice_phrases = evidence.get("voice_signature_phrases", 0)
    behavioral_states = evidence.get("behavioral_states", 0)

    # Checks
    ev_check = checks.get("evidence_threshold") or {}
    coh_check = checks.get("cross_layer_coherence") or {}
    bal_check = checks.get("obsessions_paradoxes_balance") or {}

    ev_ok = ev_check.get("passed", False)
    coh_ok = coh_check.get("passed", False)
    bal_ok = bal_check.get("passed", False)

    underpopulated = ev_check.get("underpopulated_layers", [])
    conflicts = coh_check.get("conflicts", [])
    bal_combined = bal_check.get("combined", 0)

    layer_order = [
        "FILOSOFIAS", "MODELOS_MENTAIS", "HEURISTICAS", "FRAMEWORKS", "METODOLOGIAS",
        "BEHAVIORAL_PATTERNS", "VALUES_HIERARCHY", "VOICE_TRAITS", "OBSESSIONS", "PARADOXES",
    ]

    content = [
        f"Verdict:            {verdict_icon} {verdict}",
        f"Recommendation:     {recommendation}",
        "",
        f"Insights Total:     {insights_total}",
        f"Voice Phrases:      {voice_phrases}",
        f"Behavioral States:  {behavioral_states}",
        "",
        "── By Layer ──────────────────────────────────",
    ]
    for layer in layer_order:
        count = by_layer.get(layer, 0)
        content.append(f"  {layer:<26} {count:>4}")

    content += [
        "",
        "── Checks ────────────────────────────────────",
        f"  Evidence Threshold:       {'✅ PASS' if ev_ok else '❌ FAIL'}  underpopulated={len(underpopulated)}",
        f"  Cross-Layer Coherence:    {'✅ PASS' if coh_ok else '❌ FAIL'}  conflicts={len(conflicts)}",
        f"  Obsessions/Paradoxes Bal: {'✅ PASS' if bal_ok else '❌ FAIL'}  combined={bal_combined}",
    ]

    return _nested_box("IDENTITY CHECKPOINT (deep view)", content)


def _render_section_12_phase8_gate_detail(data: dict[str, Any]) -> list[str]:
    """Section 12 — PHASE 8 GATE DETAIL (7A-7J).

    Source: template_id=phase8_gate in PHASE-STREAM.jsonl.
    """
    if not data:
        return _nested_box("PHASE 8 GATE DETAIL (7A-7J)", [_NO_DATA])

    gate_status = str(data.get("gate_status", "UNKNOWN")).upper()
    gate_icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(gate_status, "❓")
    gate_checks: dict[str, Any] = data.get("gate_checks") or {}
    failures: list[str] = data.get("failures") or []

    check_definitions = [
        ("7A", "7A_aggregated_present",          "Aggregated insights present"),
        ("7B", "7B_insights_state_schema_valid",  "Insights state schema valid"),
        ("7C", "7C_narratives_bucket_field",       "Narratives bucket field set"),
        ("7D", "7D_sources_dir_present",           "Sources directory present"),
        ("7E", "7E_map_conflitos_per_domain",       "Map conflitos per domain"),
        ("7F", "7F_pipeline_state_checkpoint",     "Pipeline state checkpoint"),
        ("7G", "7G_evolution_log_entry",            "Evolution log entry written"),
        ("7H", "7H_file_registry_entry",            "File registry entry written"),
        ("7I", "7I_role_tracking_entry",            "Role tracking entry written"),
        ("7J", "7J_cascade_coverage",               "Cascade coverage threshold"),
    ]

    content = [
        f"Gate Status:  {gate_icon} {gate_status}",
        "",
        f"{'Check':<6} {'Name':<36} {'Result'}",
        f"{'─' * 6} {'─' * 36} {'─' * 8}",
    ]

    passed_count = 0
    for short, key, label in check_definitions:
        val = gate_checks.get(key)
        if isinstance(val, dict):
            passed = val.get("passed", False)
            extra = f" coverage={val.get('coverage_pct', '?')}%" if "coverage_pct" in val else ""
        else:
            passed = bool(val)
            extra = ""
        passed_count += int(passed)
        icon = "✅ PASS" if passed else "❌ FAIL"
        content.append(f"{short:<6} {label:<36} {icon}{extra}")

    content += [
        "",
        f"Score: {passed_count}/10",
    ]
    if failures:
        content.append("")
        content.append("Failures:")
        for f in failures:
            content.append(f"  ❌ {f}")

    return _nested_box("PHASE 8 GATE DETAIL (7A-7J)", content)


def _render_section_13_contradictions(data: dict[str, Any]) -> list[str]:
    """Section 13 — CONTRADICTIONS REPORT.

    Source: template_id=contradictions in PHASE-STREAM.jsonl.
    """
    if not data:
        return _nested_box("CONTRADICTIONS REPORT", [_NO_DATA])

    count = data.get("contradictions_count", 0)
    conflicts: list[Any] = data.get("conflicts") or []

    if count == 0 and not conflicts:
        return _nested_box(
            "CONTRADICTIONS REPORT",
            ["✅ No conflicting insights detected. DNA coherence OK."],
        )

    content = [f"Contradictions Count: {count}", ""]
    for c in conflicts:
        if isinstance(c, dict):
            id_a = c.get("insight_id_a", "?")
            id_b = c.get("insight_id_b", "?")
            summary = str(c.get("tension_summary", "(sem resumo)"))[:80]
            content.append(f"  ⚡ [{id_a}] vs [{id_b}]: {summary}")
        else:
            content.append(f"  ⚡ {str(c)[:80]}")

    return _nested_box("CONTRADICTIONS REPORT", content)


def _render_section_14_agent_state_diff(data: dict[str, Any]) -> list[str]:
    """Section 14 — AGENT STATE DIFF.

    Source: template_id=agent_state in PHASE-STREAM.jsonl.
    """
    if not data:
        return _nested_box("AGENT STATE DIFF", [_NO_DATA])

    mem_before = int(data.get("memory_before") or 0)
    mem_after = int(data.get("memory_after") or 0)
    delta = int(data.get("delta") or (mem_after - mem_before))
    insights_appended = data.get("insights_appended", 0)
    skipped_dedup = data.get("skipped_dedup", 0)

    pct_change = 0.0
    if mem_before > 0:
        pct_change = (delta / mem_before) * 100

    content = [
        f"{'Metric':<24} {'Before':>10} {'After':>10} {'Delta':>10}",
        f"{'─' * 24} {'─' * 10} {'─' * 10} {'─' * 10}",
        f"{'Memory (bytes)':<24} {mem_before:>10} {mem_after:>10} {delta:>+10}",
        "",
        f"Change:             {pct_change:>+.1f}%",
        f"Insights Appended:  {insights_appended}",
        f"Skipped (dedup):    {skipped_dedup}",
    ]

    return _nested_box("AGENT STATE DIFF", content)


def _render_section_15_narrative_metabolism(data: dict[str, Any]) -> list[str]:
    """Section 15 — NARRATIVE METABOLISM.

    Source: template_id=narrative_metabolism in PHASE-STREAM.jsonl.
    """
    if not data:
        return _nested_box("NARRATIVE METABOLISM", [_NO_DATA])

    merger_available = data.get("merger_available", False)
    bucket = str(data.get("bucket", "(unknown)"))
    patterns_count = data.get("patterns_count", 0)
    consensus_count = data.get("consensus_count", 0)
    persons_count = data.get("persons_count", 0)
    domains_count = data.get("domains_count", 0)
    total_narratives = data.get("total_narratives", patterns_count + consensus_count)

    if total_narratives == 0 and not merger_available:
        return _nested_box(
            "NARRATIVE METABOLISM",
            ["○ No narratives produced this run"],
        )

    content = [
        f"Merger Available:   {'✅ Yes' if merger_available else '○ No'}",
        f"Bucket:             {bucket}",
        "",
        f"Patterns Count:     {patterns_count}",
        f"Consensus Count:    {consensus_count}",
        f"Total Narratives:   {total_narratives}",
    ]
    if persons_count:
        content.append(f"Persons Count:      {persons_count}")
    if domains_count:
        content.append(f"Domains Count:      {domains_count}")

    return _nested_box("NARRATIVE METABOLISM", content)


def _render_section_16_sources_compilation(data: dict[str, Any]) -> list[str]:
    """Section 16 — SOURCES COMPILATION.

    Source: template_id=sources_compilation in PHASE-STREAM.jsonl.
    """
    if not data:
        return _nested_box("SOURCES COMPILATION", [_NO_DATA])

    status = str(data.get("status", "unknown")).upper()
    status_icon = {"WRITTEN": "✅", "SKIPPED": "⏭️", "NO_SOURCES": "○"}.get(status, "❓")
    files_written: list[str] = data.get("files_written") or []
    temas_written: list[str] = data.get("temas_written") or []
    temas_skipped: list[str] = data.get("temas_skipped") or []

    content = [
        f"Status:  {status_icon} {status}",
        "",
        f"{'Written':<40} {'Skipped':>6}",
        f"{'─' * 40} {'─' * 6}",
    ]

    max_rows = max(len(temas_written), len(temas_skipped), 1)
    for i in range(max_rows):
        tw = temas_written[i] if i < len(temas_written) else ""
        ts = temas_skipped[i] if i < len(temas_skipped) else ""
        content.append(f"{tw[:38]:<40} {ts[:20]}")

    if files_written:
        content += ["", f"Files Written: {len(files_written)}"]
        for fw in files_written[:5]:
            content.append(f"  • {fw}")

    return _nested_box("SOURCES COMPILATION", content)


def _render_section_17_domain_aggregator(data: dict[str, Any]) -> list[str]:
    """Section 17 — DOMAIN AGGREGATOR (MAP-CONFLITOS).

    Source: template_id=domain_aggregator in PHASE-STREAM.jsonl.
    data is a dict of {domain_name: aggregation_result}.
    """
    if not data:
        return _nested_box("DOMAIN AGGREGATOR (MAP-CONFLITOS)", ["○ No domain aggregation results"])

    content: list[str] = []
    domain_count = 0

    for domain_name, domain_result in data.items():
        if not isinstance(domain_result, dict):
            continue
        domain_count += 1
        agg = domain_result.get("aggregation") or {}
        status_ok = domain_result.get("success", False)
        conflicts_found = agg.get("conflicts_found", 0)
        conflicts_written = agg.get("conflicts_written", 0)
        experts_compared = agg.get("experts_compared", 0)
        icon = "✅" if status_ok else "❌"
        content.append(
            f"{icon} {domain_name:<20}  experts={experts_compared}  "
            f"conflicts={conflicts_found}/{conflicts_written}"
        )

    if not content:
        return _nested_box("DOMAIN AGGREGATOR (MAP-CONFLITOS)", ["○ No domain aggregation results"])

    content.insert(0, f"Domains Aggregated: {domain_count}")
    content.insert(1, "")
    content.insert(2, f"{'Domain':<22} {'Experts':>8} {'Conflicts (found/written)':>28}")
    content.insert(3, f"{'─' * 22} {'─' * 8} {'─' * 28}")
    content.insert(4, "")

    return _nested_box("DOMAIN AGGREGATOR (MAP-CONFLITOS)", content)


def _render_section_18_llm_cost(data: dict[str, Any]) -> list[str]:
    """Section 18 — LLM COST + PROVIDER.

    Source: template_id=llm_cost in PHASE-STREAM.jsonl.
    """
    if not data:
        return _nested_box("LLM COST + PROVIDER", [_NO_DATA])

    total_usd = data.get("total_usd", 0.0)
    total_input = data.get("total_input_tokens", 0)
    total_output = data.get("total_output_tokens", 0)
    by_phase: dict[str, Any] = data.get("by_phase") or {}
    by_provider: dict[str, Any] = data.get("by_provider") or {}

    content = [
        f"Total Cost:         ${total_usd:.6f}",
        f"Input Tokens:       {total_input:,}",
        f"Output Tokens:      {total_output:,}",
        f"Total Tokens:       {total_input + total_output:,}",
    ]

    if by_phase:
        content += ["", f"{'Phase':<24} {'Input':>10} {'Output':>10} {'USD':>12}"]
        content.append(f"{'─' * 24} {'─' * 10} {'─' * 10} {'─' * 12}")
        for phase, pdata in by_phase.items():
            if isinstance(pdata, dict):
                pi = pdata.get("input_tokens", 0)
                po = pdata.get("output_tokens", 0)
                pusd = pdata.get("usd", 0.0)
                content.append(f"{phase[:23]:<24} {pi:>10} {po:>10} ${pusd:>10.6f}")
            else:
                content.append(f"{phase[:23]:<24} (nao disponivel)")

    if by_provider:
        content += ["", f"{'Provider':<24} {'Input':>10} {'Output':>10} {'USD':>12}"]
        content.append(f"{'─' * 24} {'─' * 10} {'─' * 10} {'─' * 12}")
        for provider, pdata in by_provider.items():
            if isinstance(pdata, dict):
                pi = pdata.get("input_tokens", 0)
                po = pdata.get("output_tokens", 0)
                pusd = pdata.get("usd", 0.0)
                content.append(f"{provider[:23]:<24} {pi:>10} {po:>10} ${pusd:>10.6f}")
            else:
                content.append(f"{provider[:23]:<24} (nao disponivel)")

    return _nested_box("LLM COST + PROVIDER", content)


def _render_section_19_squad_activation(data: dict[str, Any]) -> list[str]:
    """Section 19 — SQUAD ACTIVATION.

    Source: template_id=squad_activation in PHASE-STREAM.jsonl.
    """
    if not data:
        return _nested_box("SQUAD ACTIVATION", ["○ No squad activations recorded"])

    squads_activated = data.get("squads_activated", 0)
    squads_list: list[Any] = data.get("squads") or []

    if squads_activated == 0 and not squads_list:
        return _nested_box("SQUAD ACTIVATION", ["○ No squad activations recorded"])

    content = [f"Squads Activated: {squads_activated}", ""]

    if squads_list:
        for item in squads_list:
            if isinstance(item, dict):
                slug_name = item.get("slug", item.get("name", str(item)))
                count = item.get("count", 1)
                content.append(f"  • {slug_name}  ({count}x)")
            else:
                content.append(f"  • {item}")

    return _nested_box("SQUAD ACTIVATION", content)


def _render_section_20_auto_advance(data: dict[str, Any]) -> list[str]:
    """Section 20 — AUTO-ADVANCE TRIGGER LOG.

    Source: template_id=auto_advance_trigger in PHASE-STREAM.jsonl.
    """
    if not data:
        return _nested_box("AUTO-ADVANCE TRIGGER LOG", [_NO_DATA])

    triggers_count = data.get("triggers_count", 0)
    by_route: dict[str, Any] = data.get("by_route") or {}
    recent: list[Any] = data.get("recent_triggers") or []
    reason = data.get("reason", "")
    skipped = data.get("skipped", 0)

    content = [f"Triggers Count:     {triggers_count}"]
    if reason:
        content.append(f"Reason:             {reason}")
    if skipped:
        content.append(f"Skipped:            {skipped}")

    if by_route:
        content += ["", "By Route:", f"{'Route':<32} {'Count':>6}", f"{'─' * 32} {'─' * 6}"]
        for route, count in sorted(by_route.items(), key=lambda x: -int(x[1])):
            content.append(f"  {route:<30} {count:>6}")

    if recent:
        content += ["", "Recent (last 5):", f"{'Timestamp':<26} {'Route':<24} {'Slug'}"]
        content.append(f"{'─' * 26} {'─' * 24} {'─' * 16}")
        for trig in recent[:5]:
            if isinstance(trig, dict):
                ts = str(trig.get("timestamp", ""))[:25]
                route = str(trig.get("route", ""))[:23]
                t_slug = str(trig.get("slug", ""))[:15]
                content.append(f"  {ts:<26} {route:<24} {t_slug}")

    return _nested_box("AUTO-ADVANCE TRIGGER LOG", content)


def _render_section_21_cross_batch_analysis(slug: str) -> list[str]:
    """Section 21 — CROSS-BATCH ANALYSIS (anomalies).

    Source: .data/artifacts/BATCH-HISTORY.json — last entry for this slug.
    """
    batch_history_path = ROOT / ".data" / "artifacts" / "BATCH-HISTORY.json"
    if not batch_history_path.exists():
        return _nested_box("CROSS-BATCH ANALYSIS", [_NO_DATA])

    try:
        history: list[dict[str, Any]] = json.loads(batch_history_path.read_text(encoding="utf-8"))
    except Exception:
        return _nested_box("CROSS-BATCH ANALYSIS", [_NO_DATA])

    if not isinstance(history, list):
        return _nested_box("CROSS-BATCH ANALYSIS", [_NO_DATA])

    # find last entry for this slug
    last_entry: dict[str, Any] = {}
    for entry in reversed(history):
        if isinstance(entry, dict) and entry.get("slug") == slug:
            last_entry = entry
            break

    if not last_entry:
        return _nested_box("CROSS-BATCH ANALYSIS", [f"○ No batch history found for slug '{slug}'"])

    anomalies: list[Any] = last_entry.get("anomalies") or []
    metrics: dict[str, Any] = last_entry.get("metrics") or {}
    batch_id = last_entry.get("batch_id", "(unknown)")

    content = [
        f"Batch ID:    {batch_id}",
        f"Timestamp:   {str(last_entry.get('timestamp', '(unknown)'))[:25]}",
        "",
    ]

    if not anomalies:
        content.append("✅ No anomalies detected in this batch.")
    else:
        content += [
            f"{'Metric':<20} {'Current':>10} {'Hist Avg':>10} {'Dev%':>8} {'Flag'}",
            f"{'─' * 20} {'─' * 10} {'─' * 10} {'─' * 8} {'─' * 30}",
        ]
        for a in anomalies:
            if not isinstance(a, dict):
                content.append(f"  ⚠️ {str(a)[:80]}")
                continue
            metric = str(a.get("metric", ""))[:19]
            current = a.get("current", 0)
            hist_avg = a.get("historical_avg", 0.0)
            dev_pct = a.get("deviation_pct", 0.0)
            flag = str(a.get("flag", ""))[:50]
            if dev_pct <= -50:
                severity = "🔴"
            elif dev_pct <= -25:
                severity = "🟡"
            else:
                severity = "🟢"
            content.append(
                f"{severity} {metric:<19} {current:>10} {hist_avg:>10.1f} {dev_pct:>+7.1f}% {flag}"
            )

    # Show current batch metrics as context
    if metrics:
        content += ["", "Current Batch Metrics:"]
        for k, v in metrics.items():
            content.append(f"  {k:<28} {v}")

    return _nested_box("CROSS-BATCH ANALYSIS", content)


def _render_section_22_executive_briefing(slug: str) -> list[str]:
    """Section 22 — EXECUTIVE BRIEFING (inline).

    Source: logs/executive-briefings/BRIEFING-<TAG>-<YYYYMMDD>.md (most recent).
    """
    tag = _make_tag(slug)
    brief_dir = ROOT / "logs" / "executive-briefings"
    if not brief_dir.is_dir():
        return _nested_box("EXECUTIVE BRIEFING", ["○ No executive briefing found for this run"])

    candidates = sorted(brief_dir.glob(f"BRIEFING-{tag}-*.md"), reverse=True)
    if not candidates:
        return _nested_box("EXECUTIVE BRIEFING", ["○ No executive briefing found for this run"])

    try:
        text = candidates[0].read_text(encoding="utf-8")
        brief_name = candidates[0].name
    except Exception:
        return _nested_box("EXECUTIVE BRIEFING", ["○ Could not read executive briefing"])

    # Limit to 60 lines to keep the log manageable
    text_lines = text.splitlines()[:60]
    content = [f"Source: {brief_name}", ""]
    content.extend(text_lines)
    if len(text.splitlines()) > 60:
        content.append(f"... (+{len(text.splitlines()) - 60} more lines)")

    return _nested_box("EXECUTIVE BRIEFING", content)


def _render_section_23_chronicler_audit(data: dict[str, Any]) -> list[str]:
    """Section 23 — CHRONICLER AUDIT (meta).

    Source: template_id=chronicler_audit in PHASE-STREAM.jsonl.
    """
    if not data:
        return _nested_box("CHRONICLER AUDIT (meta)", [_NO_DATA])

    phase_idx = data.get("phase_idx", 0)
    templates_rendered = data.get("templates_rendered", 0)
    templates_expected = data.get("templates_expected", 0)
    missing_templates: list[str] = data.get("missing_templates") or []
    schema_mismatches = data.get("schema_mismatches", 0)

    audit_ok = len(missing_templates) == 0 and schema_mismatches == 0
    status_str = "✅ OK" if audit_ok else "⚠️ WARN"

    content = [
        f"Audit Status:       {status_str}",
        "",
        f"Phase Index:        {phase_idx}",
        f"Templates Rendered: {templates_rendered}",
        f"Templates Expected: {templates_expected}",
        f"Schema Mismatches:  {schema_mismatches}",
    ]

    if missing_templates:
        content += ["", "Missing Templates:"]
        for mt in missing_templates:
            content.append(f"  ○ {mt}")
    else:
        content += ["", "Missing Templates:  (none)"]

    return _nested_box("CHRONICLER AUDIT (meta)", content)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════


def generate_mce_log_v2_legacy(
    slug: str,
    enrichment_result: dict[str, Any] | None = None,
    agent_trigger_result: dict[str, Any] | None = None,
    cascade_result: dict[str, Any] | None = None,
    sync_result: dict[str, Any] | None = None,
    index_result: dict[str, Any] | None = None,
    collected_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """[LEGACY v2.1.0] Generate a Chronicler-formatted log for a completed MCE pipeline run.

    Kept for rollback only. Use generate_mce_log() (v3.0.0) instead.

    Args:
        slug: Person slug (e.g. ``"process-architect"``).
        enrichment_result: Output from memory enrichment step.
        agent_trigger_result: Output from agent trigger evaluation.
        cascade_result: Output from cascading step.
        sync_result: Output from workspace sync step.
        index_result: Output from index rebuild step.
        collected_data: Pre-loaded data from ``chronicler_data_collector.collect_final_log_data()``.
            When provided, skips inline loading of metadata, metrics, DNA,
            insights, and chunks (S-07 centralization).  Falls back to
            inline loading for any missing key.
    """
    enrichment_result = enrichment_result or {}
    agent_trigger_result = agent_trigger_result or {}
    cascade_result = cascade_result or {}
    sync_result = sync_result or {}
    index_result = index_result or {}
    collected_data = collected_data or {}

    # --- Resolve identity ---
    # S-07: prefer pre-loaded data from the data collector when available.
    if collected_data.get("tag"):
        tag = collected_data["tag"]
    else:
        tag = _make_tag(slug)

    if collected_data.get("timestamp"):
        now = collected_data["timestamp"]
    else:
        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    # RC3 fix: use Data Collector's resolve_person_name() for canonical names
    # with accents (e.g. "José Antônio" instead of "Jose Antonio").
    # S-07: collected_data already has the resolved name.
    if collected_data.get("person_name"):
        person_name = collected_data["person_name"]
    elif _HAS_DATA_COLLECTOR:
        person_name = _resolve_person_name(slug)
    else:
        person_name = " ".join(w.capitalize() for w in slug.split("-"))

    # --- Load state files ---
    # S-07: use pre-loaded data when available, fall back to inline loading.
    if collected_data.get("metadata") is not None:
        metadata = collected_data["metadata"]
    else:
        metadata = _load_metadata(slug)

    if collected_data.get("metrics") is not None:
        metrics = collected_data["metrics"]
    else:
        metrics = _load_metrics(slug)

    # --- DNA counts ---
    if collected_data.get("dna"):
        dna = collected_data["dna"]
    else:
        dna = _load_dna_counts(slug)

    # --- Insights count ---
    # S-07: use pre-loaded counts when available.
    # G11 (2026-05-13): when the data collector did NOT pre-populate, read from
    # slug-isolated state first ( ``ARTIFACTS / "insights" / slug / ...`` ) and
    # fall back to legacy global path only when slug-local is missing.  Without
    # this, log_generator silently reported 0 insights / 0 chunks even when
    # cmd_process_batch had written 750 entities + 2137 edges to disk under the
    # slug-isolated layout that cmd_report + cmd_process_batch already use.
    if "person_insights" in collected_data:
        person_insights = collected_data["person_insights"]
    else:
        # T9 (MCE-17.0 Fase 2): path resolution delegated to the unified helper
        # _load_insights_state_for_slug, which covers both slug-local and legacy
        # global paths — eliminating the duplicated path-resolution block that
        # previously existed here and in _fpb_load_insights.
        person_insights = 0
        try:
            data = _load_insights_state_for_slug(slug)
            if data:
                persons = data.get("persons", {})
                pdata = persons.get(person_name, {})
                if isinstance(pdata, dict):
                    pinsights = pdata.get("insights", [])
                    person_insights = len(pinsights) if isinstance(pinsights, list) else 0
                elif isinstance(pdata, list):
                    person_insights = len(pdata)
        except Exception:
            pass

    # --- Chunks count ---
    if "chunks_count" in collected_data:
        chunks_count = collected_data["chunks_count"]
    else:
        chunks_count = 0
        chunks_slug = ARTIFACTS / "chunks" / slug / "CHUNKS-STATE.json"
        chunks_legacy = ARTIFACTS / "chunks" / "CHUNKS-STATE.json"
        chunks_path = chunks_slug if chunks_slug.exists() else chunks_legacy
        if chunks_path.exists():
            try:
                cdata = json.loads(chunks_path.read_text(encoding="utf-8"))
                chunks_count = len(cdata.get("chunks", []))
            except Exception:
                pass

        # G11: when CHUNKS-STATE.json is absent, fall back to counting the
        # per-batch chunk files written by cmd_process_batch under
        # ``ARTIFACTS / "chunks" / {slug} / BATCH-*.json``.  This is the
        # canonical layout (state_writer + chronicler still use the legacy
        # consolidated file).
        if chunks_count == 0:
            slug_chunks_dir = ARTIFACTS / "chunks" / slug
            if slug_chunks_dir.is_dir():
                for cjson in slug_chunks_dir.glob("BATCH-*-chunks.json"):
                    try:
                        cdata = json.loads(cjson.read_text(encoding="utf-8"))
                        chunks_count += len(cdata.get("chunks", []))
                    except Exception:
                        continue

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

    # G11 (2026-05-13): index_result (from cmd_rag_index) does NOT include
    # knowledge-graph counts — it only reports BM25 bucket chunks. Read the
    # actual graph state file written by enrich_knowledge_graph when the
    # passed-in payload is empty. Path is canonical (engine.paths.ROOT /
    # ".data/knowledge_graph/graph.json"). Also use rebuild_stats from
    # cmd_rag_index for ext/biz chunks when the legacy ``indexes`` key is
    # absent (the canonical key under ``rag_index`` result is
    # ``rebuild_stats[bucket]['chunks']``).
    if ext_chunks == 0:
        ext_chunks = index_result.get("rebuild_stats", {}).get("external", {}).get("chunks", 0)
    if biz_chunks == 0:
        biz_chunks = index_result.get("rebuild_stats", {}).get("business", {}).get("chunks", 0)

    if graph_entities == 0 or graph_edges == 0:
        try:
            graph_file = ROOT / ".data" / "knowledge_graph" / "graph.json"
            if graph_file.exists():
                gdata = json.loads(graph_file.read_text(encoding="utf-8"))
                if graph_entities == 0:
                    graph_entities = len(gdata.get("entities", []))
                if graph_edges == 0:
                    graph_edges = len(gdata.get("edges", []))
        except Exception as exc:
            logger.debug("G11: failed to read knowledge graph: %s", exc)

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

    # ── BUCKET PANEL (step_log_renderer — non-fatal) ──
    try:
        from engine.intelligence.pipeline.mce.step_log_renderer import _render_bucket_panel
        from engine.intelligence.pipeline.mce.step_result import BucketMetrics, StepResult

        _final_result = StepResult(
            step_id=12,
            slug=slug,
            status="COMPLETE",
            bucket="external",
            bucket_external=BucketMetrics(
                insights=person_insights,
                chunks=chunks_count,
                is_primary=True,
            ),
            bucket_intersections=[
                f"{appended} insights → {len(agents_enriched)} cargo agents (MEMORY.md)",
                f"{themes_created} dossiês temáticos criados",
                f"{themes_updated} dossiês temáticos atualizados",
            ],
        )
        lines.extend(_render_bucket_panel(_final_result))
        lines.append("")
    except Exception:
        pass  # Non-fatal — bucket panel is enrichment only

    # ── SECTION 1: EXTRACTION METRICS ──
    lines.extend(_section_header(1, "🧠", "EXTRACTION METRICS"))

    lines.extend(
        _metric_grid(
            [
                (str(chunks_count), "CHUNKS", "Segmentos de texto"),
                (str(person_insights), "INSIGHTS", "Conhecimento acionavel"),
                (str(dna_total), "DNA ELEMENTS", "5 camadas cognitivas"),
                (str(phases_completed), "PHASES", "Etapas do pipeline"),
            ]
        )
    )
    lines.append("")

    # DNA breakdown with progress bars
    if dna_total > 0:
        lines.extend(
            _nested_box(
                "DNA BREAKDOWN POR CAMADA",
                [
                    f"L1 Filosofias:      {fil_count:>3}  {_bar(fil_count / dna_total * 100 if dna_total else 0, 20)}",
                    f"L2 Modelos Mentais: {mm_count:>3}  {_bar(mm_count / dna_total * 100 if dna_total else 0, 20)}",
                    f"L3 Heuristicas:     {heu_count:>3}  {_bar(heu_count / dna_total * 100 if dna_total else 0, 20)}  ★★★",
                    f"L4 Frameworks:      {fw_count:>3}  {_bar(fw_count / dna_total * 100 if dna_total else 0, 20)}",
                    f"L5 Metodologias:    {met_count:>3}  {_bar(met_count / dna_total * 100 if dna_total else 0, 20)}",
                    "",
                    f"TOTAL:              {dna_total:>3}  elementos",
                ],
            )
        )
    lines.append("")

    # ── SECTION 2: MEMORY ENRICHMENT ──
    lines.extend(_section_header(2, "📝", "MEMORY ENRICHMENT"))

    lines.extend(
        _nested_box(
            "ENRICHMENT RESULTS",
            [
                f"Insights appended:   {appended}",
                f"Skipped (dedup):     {enrichment_result.get('skipped_dedup', 0)}",
                f"Agents enriched:     {len(agents_enriched)}",
                "",
                "Agents:",
            ]
            + [f"  {BULLET} {a}" for a in agents_enriched],
        )
    )
    lines.append("")

    # ── SECTION 3: CASCADING ──
    lines.extend(_section_header(3, "🔄", "POST-EXTRACTION CASCADING"))

    lines.extend(
        _nested_box(
            "CASCADE RESULTS",
            [
                f"Insights processados:    {cascade_insights}",
                f"Cargo agents encontrados:{cascade_result.get('cargo_agents_found', 0)}",
                f"Cargo agents atualizados:{cargo_updated}",
                f"Temas atualizados:       {themes_updated}",
                f"Temas criados:           {themes_created}",
            ],
        )
    )
    lines.append("")

    # ── SECTION 4: INDEX REBUILD ──
    lines.extend(_section_header(4, "🔍", "INDEX REBUILD"))

    lines.extend(
        _metric_grid(
            [
                (str(ext_chunks), "EXTERNAL", "Chunks RAG externos"),
                (str(biz_chunks), "BUSINESS", "Chunks RAG business"),
                (str(graph_entities), "ENTITIES", "Knowledge graph"),
                (str(graph_edges), "EDGES", "Conexoes no grafo"),
            ]
        )
    )
    lines.append("")

    # ── SECTION 5: WORKSPACE SYNC ──
    lines.extend(_section_header(5, "🏢", "WORKSPACE SYNC"))

    lines.extend(
        _nested_box(
            "SYNC RESULTS",
            [
                f"Items sincronizados: {synced}",
                f"Status:              {'✅ Synced' if synced > 0 else '○ Nenhum item novo para sincronizar'}",
            ],
        )
    )
    lines.append("")

    # ── SECTION 6: META ──
    lines.extend(_section_header(6, "📋", "METADADOS DA EXECUCAO"))

    lines.extend(
        _nested_box(
            "PIPELINE METADATA",
            [
                f"Person:          {person_name}",
                f"Slug:            {slug}",
                f"Tag:             {tag}",
                f"Source Code:     {source_code}",
                f"Workflow Mode:   {mode}",
                "Pipeline Status: COMPLETE",
                f"Duration:        {duration:.1f}s",
                f"Generated:       {now}",
            ],
        )
    )
    lines.append("")

    # ── SECTION 7: VALIDATION ──
    lines.extend(_section_header(7, "✅", "VALIDATION CHECKLIST (12 STEPS)"))

    # V1 (2026-05-13): template-aligned 12-step validation.
    # Previous implementation ran 7 checks against final artifacts only
    # (CHUNKS-STATE, INSIGHTS-STATE, DNA total, RAG indexes, Knowledge
    # Graph) which silently reported COMPLETE/7 even when MCE steps 6-11
    # had not run. The 12 checks below mirror MCE-PIPELINE-LOG-TEMPLATE
    # and each step that hasn't been wired yet reports "pending (Step N)"
    # rather than crashing the log.
    bucket = collected_data.get("bucket", "external") if collected_data else "external"

    checks = _validation_checks_12(
        slug,
        metadata=metadata,
        chunks_count=chunks_count,
        person_insights=person_insights,
        dna=dna or {},
        bucket=bucket,
    )

    check_lines: list[str] = []
    for name, passed, detail in checks:
        icon = "✅" if passed else "❌"
        check_lines.append(f"{icon} {name:<32} {detail}")
    passed_count = sum(1 for _, p, _ in checks if p)
    total_checks = len(checks)
    check_lines.append("")
    check_lines.append(
        f"RESULTADO: {passed_count}/{total_checks} checks passed  "
        f"{_bar(passed_count / total_checks * 100, 20)}"
    )

    # Observability — RAG / knowledge-graph metrics kept as INFO rows so the
    # operator still sees them, but they no longer drive the validation gate
    # (the 12 template steps are the only authority for N/12).
    check_lines.append("")
    check_lines.append("── observability (não conta no gate) ──")
    check_lines.append(f"   RAG External Index           {ext_chunks} chunks")
    check_lines.append(f"   RAG Business Index           {biz_chunks} chunks")
    check_lines.append(
        f"   Knowledge Graph              {graph_entities} entities / {graph_edges} edges"
    )
    check_lines.append(
        f"   Memory Enrichment            {appended} appended → {len(agents_enriched)} agents"
    )

    lines.extend(_nested_box("VALIDATION GATE", check_lines))
    lines.append("")

    # ── SECTIONS 8-23 (Story MCE-13.10 — v2.1.0) ──
    # Load PHASE-STREAM.jsonl once, share across all new sections.
    stream = _load_phase_stream(slug)

    # ── SECTION 8: INGESTION GUARD VERDICT ──
    lines.extend(_section_header(8, "⏭️", "INGESTION GUARD VERDICT"))
    lines.extend(_render_section_8_ingestion_guard(stream.get("ingestion_guard") or {}))
    lines.append("")

    # ── SECTION 9: RAG INDEXATION REPORT ──
    lines.extend(_section_header(9, "🔍", "RAG INDEXATION REPORT (Art. XV)"))
    lines.extend(_render_section_9_rag_indexation(stream.get("rag_indexation") or {}))
    lines.append("")

    # ── SECTION 10: KNOWLEDGE GRAPH STATS ──
    lines.extend(_section_header(10, "🕸️", "KNOWLEDGE GRAPH STATS"))
    lines.extend(_render_section_10_knowledge_graph(stream.get("rag_indexation") or {}))
    lines.append("")

    # ── SECTION 11: IDENTITY CHECKPOINT (deep view) ──
    lines.extend(_section_header(11, "🔬", "IDENTITY CHECKPOINT (deep view)"))
    lines.extend(_render_section_11_identity_checkpoint_deep(slug))
    lines.append("")

    # ── SECTION 12: PHASE 8 GATE DETAIL ──
    lines.extend(_section_header(12, "🚦", "PHASE 8 GATE DETAIL (7A-7J)"))
    lines.extend(_render_section_12_phase8_gate_detail(stream.get("phase8_gate") or {}))
    lines.append("")

    # ── SECTION 13: CONTRADICTIONS REPORT ──
    lines.extend(_section_header(13, "⚡", "CONTRADICTIONS REPORT"))
    lines.extend(_render_section_13_contradictions(stream.get("contradictions") or {}))
    lines.append("")

    # ── SECTION 14: AGENT STATE DIFF ──
    lines.extend(_section_header(14, "📊", "AGENT STATE DIFF"))
    lines.extend(_render_section_14_agent_state_diff(stream.get("agent_state") or {}))
    lines.append("")

    # ── SECTION 15: NARRATIVE METABOLISM ──
    lines.extend(_section_header(15, "🧬", "NARRATIVE METABOLISM"))
    lines.extend(_render_section_15_narrative_metabolism(stream.get("narrative_metabolism") or {}))
    lines.append("")

    # ── SECTION 16: SOURCES COMPILATION ──
    lines.extend(_section_header(16, "📁", "SOURCES COMPILATION"))
    lines.extend(_render_section_16_sources_compilation(stream.get("sources_compilation") or {}))
    lines.append("")

    # ── SECTION 17: DOMAIN AGGREGATOR ──
    lines.extend(_section_header(17, "🗺️", "DOMAIN AGGREGATOR (MAP-CONFLITOS)"))
    lines.extend(_render_section_17_domain_aggregator(stream.get("domain_aggregator") or {}))
    lines.append("")

    # ── SECTION 18: LLM COST + PROVIDER ──
    lines.extend(_section_header(18, "💰", "LLM COST + PROVIDER"))
    lines.extend(_render_section_18_llm_cost(stream.get("llm_cost") or {}))
    lines.append("")

    # ── SECTION 19: SQUAD ACTIVATION ──
    lines.extend(_section_header(19, "🤝", "SQUAD ACTIVATION"))
    lines.extend(_render_section_19_squad_activation(stream.get("squad_activation") or {}))
    lines.append("")

    # ── SECTION 20: AUTO-ADVANCE TRIGGER LOG ──
    lines.extend(_section_header(20, "⚙️", "AUTO-ADVANCE TRIGGER LOG"))
    lines.extend(_render_section_20_auto_advance(stream.get("auto_advance_trigger") or {}))
    lines.append("")

    # ── SECTION 21: CROSS-BATCH ANALYSIS ──
    lines.extend(_section_header(21, "📈", "CROSS-BATCH ANALYSIS"))
    lines.extend(_render_section_21_cross_batch_analysis(slug))
    lines.append("")

    # ── SECTION 22: EXECUTIVE BRIEFING ──
    lines.extend(_section_header(22, "📋", "EXECUTIVE BRIEFING"))
    lines.extend(_render_section_22_executive_briefing(slug))
    lines.append("")

    # ── SECTION 23: CHRONICLER AUDIT ──
    lines.extend(_section_header(23, "🔎", "CHRONICLER AUDIT (meta)"))
    lines.extend(_render_section_23_chronicler_audit(stream.get("chronicler_audit") or {}))
    lines.append("")

    # ── CHRONICLER NOTES ──
    notes = []
    if person_insights >= 20:
        notes.append(
            f"Extracao rica: {person_insights} insights colocam {person_name} entre as fontes mais densas do sistema."
        )
    if heu_count >= 3:
        notes.append(
            f"Destaque: {heu_count} heuristicas com numeros — o tipo mais valioso de DNA cognitivo."
        )
    if appended > 10:
        notes.append(
            f"Enrichment robusto: {appended} insights cascateados para MEMORY.md dos agentes."
        )
    if not notes:
        notes.append(
            f"Pipeline completo para {person_name}. Todos os artefatos gerados com sucesso."
        )
    notes.append("Versao do log: Chronicler Design System v2.1.0 | log_generator.py v2_legacy | 23 secoes")

    lines.extend(_chronicler_notes(notes))

    # ── FOOTER ──
    lines.extend(
        _footer(
            f"MCE PIPELINE LOG — {person_name} ({tag})",
            "v2.1.0",
            now,
        )
    )
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


# ═══════════════════════════════════════════════════════════════════════════════
# FULL PIPELINE REPORT — render_full_pipeline_report (79-char ASCII)
# Approved format: FULL PIPELINE REPORT — LOG 7 (AGREGADOR COMPLETO)
# Story: MC-FULL-REPORT
# ═══════════════════════════════════════════════════════════════════════════════

W79 = 79  # Fixed width for this report

def _w79_pad(text: str, width: int) -> str:
    """Pad/truncate text to exact width."""
    if len(text) >= width:
        return text[:width]
    return text + " " * (width - len(text))


def _w79_center(text: str, width: int = W79) -> str:
    """Center text in a fixed-width field."""
    return text.center(width)


def _w79_double_border(inner: str) -> str:
    """╔═...═╗ double-border top/bot line of width W79."""
    content_w = W79 - 2
    return "╔" + "═" * content_w + "╗"


def _w79_double_bot() -> str:
    content_w = W79 - 2
    return "╚" + "═" * content_w + "╝"


def _w79_double_line(text: str = "") -> str:
    """║ text ║ with padding to W79."""
    content_w = W79 - 4
    padded = _w79_pad(text, content_w)
    return f"║ {padded} ║"


def _w79_sep(label: str = "") -> str:
    """═══ label ═══ separator at W79."""
    line = "═" * W79
    if label:
        lbl = f" {label} "
        mid = (W79 - len(lbl)) // 2
        line = "═" * mid + lbl + "═" * (W79 - mid - len(lbl))
    return line


def _w79_box_top(title: str = "") -> str:
    """┌── title ─────────────────────────────────────┐"""
    if title:
        inner = f"─ {title} " + "─" * (W79 - len(title) - 5)
        return "┌" + inner[: W79 - 2] + "┐"
    return "┌" + "─" * (W79 - 2) + "┐"


def _w79_box_bot() -> str:
    return "└" + "─" * (W79 - 2) + "┘"


def _w79_box_line(text: str = "") -> str:
    content_w = W79 - 4
    padded = _w79_pad(text, content_w)
    return f"│ {padded} │"


def _w79_progress_bar(pct: float, width: int = 25) -> str:
    """▓▓▓▓░░░░ 60% — simple ascii bar."""
    filled = int(pct / 100 * width)
    bar = "▓" * filled + "░" * (width - filled)
    return f"{bar} {int(pct):3d}%"


def _load_insights_state_for_slug(slug: str) -> dict[str, Any]:
    """Canonical INSIGHTS-STATE.json loader for a slug (Story MCE-17.0 Fase 2 T9).

    Implements the authoritative path resolution:
    1. Slug-local path: ``ARTIFACTS/insights/{slug}/INSIGHTS-STATE.json``
    2. Legacy global fallback: ``ARTIFACTS/insights/INSIGHTS-STATE.json``

    Returns the parsed dict on success, or ``{}`` on missing file / parse error.
    Both ``_fpb_load_insights`` and the inline reader in the main data-collection
    block delegate to this helper, eliminating duplicated file-read boilerplate
    and ensuring consistent path resolution across both call sites.
    """
    insights_slug = ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
    insights_legacy = ARTIFACTS / "insights" / "INSIGHTS-STATE.json"
    insights_path = insights_slug if insights_slug.exists() else insights_legacy
    if not insights_path.exists():
        return {}
    try:
        return json.loads(insights_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _fpb_load_insights(slug: str) -> tuple[list[dict], dict[str, list[dict]]]:
    """Load insights list and by-tag grouping for slug.

    Delegates path resolution to ``_load_insights_state_for_slug``
    (Story MCE-17.0 Fase 2 T9 — INSIGHTS-STATE dual-path unified).
    """
    data = _load_insights_state_for_slug(slug)
    if not data:
        return [], {}
    try:
        persons = data.get("persons", {})
        # Aggregate all insights across every person key in this slug's state.
        all_insights: list[dict] = []
        for pdata in persons.values():
            if isinstance(pdata, dict):
                all_insights.extend(pdata.get("insights", []))
            elif isinstance(pdata, list):
                all_insights.extend(pdata)
        # group by tag
        by_tag: dict[str, list[dict]] = {}
        for ins in all_insights:
            tag = ins.get("tag", "[OUTROS]")
            by_tag.setdefault(tag, []).append(ins)
        return all_insights, by_tag
    except Exception:
        return [], {}


def _fpb_load_role_tracking(slug: str) -> dict[str, Any]:
    """Load role-tracking entry for slug.

    Delegates to role_tracker_reader.load_role_tracking + find_person when
    available (Story MCE-17.0 Fase 2 T8). Falls back to inline read on
    ImportError so the function remains non-fatal.
    """
    if _HAS_ROLE_TRACKER_READER:
        try:
            rt = _rt_load(ARTIFACTS / "ROLE-TRACKING.json")
            entry = _rt_find_person(rt, slug)
            return dict(entry) if entry is not None else {}
        except Exception:
            return {}

    # Inline fallback — only reached when role_tracker_reader import failed.
    path = ARTIFACTS / "ROLE-TRACKING.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        persons = data.get("persons", [])
        for p in persons:
            if isinstance(p, dict) and p.get("slug") == slug:
                return p
    except Exception:
        pass
    return {}


def _fpb_load_phase8_gate(slug: str) -> dict[str, Any]:
    """Load most recent phase8-gate entry for slug."""
    path = LOGS / "phase8-gate.jsonl"
    if not path.exists():
        return {}
    result: dict[str, Any] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                if entry.get("slug") == slug:
                    result = entry
                    break
            except Exception:
                continue
    except Exception:
        pass
    return result


def _fpb_load_health(slug: str) -> dict[str, Any]:
    """Load HEALTH-STATE.json."""
    path = ARTIFACTS / "HEALTH-STATE.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _fpb_load_dossier_info(slug: str, bucket: str) -> dict[str, Any]:
    """Load person dossier info."""
    result: dict[str, Any] = {"exists": False}
    path = ROOT / "knowledge" / bucket / "dossiers" / "persons" / f"dossier-{slug}.md"
    if not path.exists():
        return result
    try:
        text = path.read_text(encoding="utf-8")
        sections = [l.strip() for l in text.splitlines() if l.startswith("## ")]
        stat = path.stat()
        result = {
            "exists": True,
            "size_bytes": stat.st_size,
            "sections": sections,
            "path": str(path),
        }
    except Exception:
        result["exists"] = True
    return result


def _fpb_load_theme_dossiers(bucket: str) -> list[str]:
    """List theme dossier filenames."""
    path = ROOT / "knowledge" / bucket / "dossiers" / "themes"
    if not path.is_dir():
        return []
    try:
        return [f.name for f in sorted(path.iterdir()) if f.name.startswith("dossier-") and f.suffix == ".md"]
    except Exception:
        return []


def _fpb_load_domain_aggs(domains: list[str]) -> dict[str, dict[str, Any]]:
    """Load AGG YAML for each domain."""
    result: dict[str, dict[str, Any]] = {}
    base = ROOT / "knowledge" / "external" / "dna" / "domains"
    for domain in domains:
        agg_path = base / domain / f"AGG-{domain.upper()}.yaml"
        if not agg_path.exists():
            continue
        try:
            import yaml  # type: ignore[import-untyped]
            data = yaml.safe_load(agg_path.read_text(encoding="utf-8")) or {}
            result[domain] = data
        except Exception:
            pass
    return result


def _fpb_load_briefing(slug: str) -> dict[str, Any]:
    """Load latest executive briefing for slug."""
    brief_dir = ROOT / "logs" / "executive-briefings"
    if not brief_dir.is_dir():
        return {}
    tag = _make_tag(slug)
    candidates: list[Any] = sorted(brief_dir.glob(f"BRIEFING-{tag}-*.md"), reverse=True)
    if not candidates:
        return {}
    try:
        path = candidates[0]
        text = path.read_text(encoding="utf-8")
        return {"path": str(path), "text": text, "name": path.name}
    except Exception:
        return {}


def _fpb_load_cmd_timing(slug: str) -> dict[str, Any]:
    """Load per-cmd timing from .data/processed-sources/{slug}-cmd-*.json."""
    timing: dict[str, Any] = {}
    base = ROOT / ".data" / "processed-sources"
    for cmd in ("behavioral", "identity", "voice"):
        p = base / f"{slug}-cmd-{cmd}.json"
        if p.exists():
            try:
                timing[cmd] = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    # main source file
    main_p = base / f"{slug}.json"
    if main_p.exists():
        try:
            timing["main"] = json.loads(main_p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return timing


def _fpb_load_agents(slug: str, bucket: str) -> list[dict[str, Any]]:
    """Load agent files — person agent + cargo agents."""
    agents: list[dict[str, Any]] = []
    # Person agent
    person_agent_dir = ROOT / "agents" / bucket / slug
    for mem_name in ("memory.md", "MEMORY.md"):
        mem_path = person_agent_dir / mem_name
        if mem_path.exists():
            stat = mem_path.stat()
            agents.append({
                "name": f"{slug} (person agent)",
                "path": str(mem_path),
                "size_bytes": stat.st_size,
                "mtime": stat.st_mtime,
            })
            break
    # Cargo agents
    cargo_base = ROOT / "agents" / "cargo"
    for agent_dir in sorted(cargo_base.rglob("*")):
        if agent_dir.is_dir():
            for mem_name in ("memory.md", "MEMORY.md"):
                mem_path = agent_dir / mem_name
                if mem_path.exists():
                    stat = mem_path.stat()
                    agents.append({
                        "name": f"cargo/{agent_dir.relative_to(cargo_base)}",
                        "path": str(mem_path),
                        "size_bytes": stat.st_size,
                        "mtime": stat.st_mtime,
                    })
                    break
    return agents


# ─── TAG ICON MAP ───────────────────────────────────────────────────────────

_TAG_ICONS: dict[str, str] = {
    "[FILOSOFIA]": "🧠",
    "[MODELO-MENTAL]": "🧩",
    "[HEURISTICA]": "🎯",
    "[FRAMEWORK]": "🏗️",
    "[METODOLOGIA]": "🛤️",
    "[COMPORTAMENTO]": "🔄",
    "[VALORES]": "⭐",
    "[VOZ]": "💬",
    "[OBSESSAO]": "🔥",
    "[PARADOXO]": "⚡",
}

_TAG_LAYER: dict[str, str] = {
    "[FILOSOFIA]": "L1 Filosofias",
    "[MODELO-MENTAL]": "L2 Modelos Mentais",
    "[HEURISTICA]": "L3 Heuristicas",
    "[FRAMEWORK]": "L4 Frameworks",
    "[METODOLOGIA]": "L5 Metodologias",
}


def render_full_pipeline_report(slug: str, bucket: str = "external") -> str:
    """Generate the FULL PIPELINE REPORT — LOG 7 (AGREGADOR COMPLETO).

    Pulls real data from disk artifacts for the given slug/bucket.
    Format: 79-char ASCII, 11 mandatory sections.
    Non-fatal: on any data load failure, section shows '(nao disponivel)' and never crashes.

    Args:
        slug: Person slug, e.g. 'jordan-lee'.
        bucket: Knowledge bucket — 'external' | 'business' | 'personal'.

    Returns:
        Formatted ASCII report string.
    """
    # ── resolve name ────────────────────────────────────────────────────────
    if _HAS_DATA_COLLECTOR:
        person_name = _resolve_person_name(slug)
    else:
        person_name = " ".join(w.capitalize() for w in slug.split("-"))

    now_ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    # ── load all data sources ────────────────────────────────────────────────
    try:
        all_insights, by_tag = _fpb_load_insights(slug)
    except Exception:
        all_insights, by_tag = [], {}

    try:
        role_data = _fpb_load_role_tracking(slug)
    except Exception:
        role_data = {}

    try:
        gate_data = _fpb_load_phase8_gate(slug)
    except Exception:
        gate_data = {}

    try:
        health_data = _fpb_load_health(slug)
    except Exception:
        health_data = {}

    try:
        dossier_info = _fpb_load_dossier_info(slug, bucket)
    except Exception:
        dossier_info = {"exists": False}

    try:
        theme_dossiers = _fpb_load_theme_dossiers(bucket)
    except Exception:
        theme_dossiers = []

    domains = role_data.get("domains", []) if isinstance(role_data, dict) else []
    try:
        domain_aggs = _fpb_load_domain_aggs(domains)
    except Exception:
        domain_aggs = {}

    try:
        briefing_info = _fpb_load_briefing(slug)
    except Exception:
        briefing_info = {}

    try:
        cmd_timing = _fpb_load_cmd_timing(slug)
    except Exception:
        cmd_timing = {}

    try:
        agents_info = _fpb_load_agents(slug, bucket)
    except Exception:
        agents_info = []

    # ── compute timing ───────────────────────────────────────────────────────
    start_ts: str = "(nao disponivel)"
    end_ts: str = now_ts
    dur_min: int = 0
    dur_sec: int = 0

    try:
        main_src = cmd_timing.get("main", {})
        if main_src and main_src.get("updated_at"):
            import time as _time
            start_epoch = float(main_src["updated_at"])
            # pick latest completed_at from any cmd
            end_epoch = start_epoch
            for cmd in ("behavioral", "identity", "voice"):
                c = cmd_timing.get(cmd, {})
                if isinstance(c, dict) and c.get("completed_at"):
                    e = float(c["completed_at"])
                    if e > end_epoch:
                        end_epoch = e
            total_s = int(end_epoch - start_epoch)
            dur_min = total_s // 60
            dur_sec = total_s % 60
            from datetime import timezone as _tz
            start_ts = datetime.fromtimestamp(start_epoch, tz=_tz.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            end_ts = datetime.fromtimestamp(end_epoch, tz=_tz.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        pass

    # ── video title (best effort from transcript source path) ────────────────
    video_title: str = "(sem titulo)"
    try:
        main_src = cmd_timing.get("main", {})
        source_files = main_src.get("source_files", []) if isinstance(main_src, dict) else []
        if source_files:
            import pathlib
            raw = pathlib.Path(source_files[0]).stem
            # remove common transcript suffix
            raw = raw.replace(".transcript", "").replace("-transcript", "")
            video_title = raw[:60]
    except Exception:
        pass

    lines: list[str] = []

    # ════════════════════════════════════════════════════════════════════════
    # SUPER HEADER
    # ════════════════════════════════════════════════════════════════════════
    top_inner = "═" * (W79 - 2)
    lines.append("╔" + top_inner + "╗")
    lines.append(_w79_double_line(""))
    lines.append(_w79_double_line(_w79_center("FULL PIPELINE REPORT — LOG 7 (AGREGADOR COMPLETO)", W79 - 4)))
    lines.append(_w79_double_line(""))
    title_line = f"{person_name} · {video_title}"
    lines.append(_w79_double_line(_w79_center(title_line, W79 - 4)))
    lines.append(_w79_double_line(""))
    lines.append(_w79_double_line(_w79_center(f"{start_ts} -> {end_ts}", W79 - 4)))
    lines.append(_w79_double_line(_w79_center(f"Duracao: {dur_min}m {dur_sec}s", W79 - 4)))
    lines.append(_w79_double_line(""))
    lines.append("╚" + top_inner + "╝")
    lines.append("")

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 1 — INGEST REPORT (LOG 5)
    # ════════════════════════════════════════════════════════════════════════
    lines.append(_w79_sep("📥  LOG 5 — INGEST REPORT (entrada bruta)"))
    lines.append(_w79_box_top())
    # source info
    main_src = cmd_timing.get("main", {}) if cmd_timing else {}
    source_files = main_src.get("source_files", []) if isinstance(main_src, dict) else []
    source_display = source_files[0][-65:] if source_files else "(nao disponivel)"
    lines.append(_w79_box_line(f"Fonte:     {source_display}"))
    lines.append(_w79_box_line(f"Titulo:    {video_title}"))
    lines.append(_w79_box_line(f"Speaker:   {person_name}"))
    lines.append(_w79_box_line(f"Bucket:    {bucket}"))
    lines.append(_w79_box_line(f"Slug:      {slug}"))
    # insights count
    total_ins = len(all_insights)
    lines.append(_w79_box_line(f"Total insights extraidos: {total_ins}"))
    # tag breakdown
    lines.append(_w79_box_line(""))
    lines.append(_w79_box_line("Por camada:"))
    for tag, tag_insights in sorted(by_tag.items(), key=lambda x: -len(x[1])):
        icon = _TAG_ICONS.get(tag, "•")
        label = _TAG_LAYER.get(tag, tag)
        lines.append(_w79_box_line(f"  {icon} {label:<22} {len(tag_insights):>3} insights"))
    lines.append(_w79_box_bot())
    lines.append("")

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 2 — EXECUTION REPORT (LOG 1)
    # ════════════════════════════════════════════════════════════════════════
    lines.append(_w79_sep("⚙️  LOG 1 — EXECUTION REPORT (fases executadas)"))
    lines.append(_w79_box_top())
    # show per-cmd timing
    phases = [
        ("B1 ingest",    None),
        ("B2 batch",     None),
        ("B3 process-batch", None),
        ("B4 insights",  cmd_timing.get("main", {})),
        ("B5a behavioral", cmd_timing.get("behavioral", {})),
        ("B5b identity", cmd_timing.get("identity", {})),
        ("B5c voice",    cmd_timing.get("voice", {})),
        ("B6a consolidate", None),
        ("B6b finalize", None),
    ]
    lines.append(_w79_box_line(f"  {'Fase':<20} {'Status':<10} {'Insights':<10} {'Tempo'}"))
    lines.append(_w79_box_line("  " + "─" * 55))
    for phase_name, p_data in phases:
        if isinstance(p_data, dict) and p_data.get("completed_at"):
            status = "✅ DONE"
            ins_count = p_data.get("insights_count", "-")
            # approx time from main source to this cmd
            completed = p_data.get("completed_at", 0)
            started = main_src.get("updated_at", completed) if isinstance(main_src, dict) else completed
            elapsed_s = max(0, int(float(completed) - float(started)))
            time_str = f"~{elapsed_s}s"
        else:
            status = "(sem dados)"
            ins_count = "-"
            time_str = "-"
        lines.append(_w79_box_line(f"  {phase_name:<20} {status:<10} {str(ins_count):<10} {time_str}"))
    lines.append(_w79_box_line(""))
    # Gate enforcement
    gate_status = gate_data.get("gate_status", "(nao disponivel)")
    gate_icon = "✅" if gate_status == "PASS" else ("⚠️" if gate_status == "WARN" else "❌")
    lines.append(_w79_box_line(f"Gate Phase-8: {gate_icon} {gate_status}"))
    if isinstance(gate_data, dict) and gate_data.get("failures"):
        for f in gate_data["failures"]:
            lines.append(_w79_box_line(f"  ❌ {f}"))
    lines.append(_w79_box_bot())
    lines.append("")

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 3 — CONTEUDO COGNITIVO
    # ════════════════════════════════════════════════════════════════════════
    lines.append(_w79_sep(f"💡  CONTEUDO COGNITIVO EXTRAIDO — o que {person_name} pensa"))
    lines.append(_w79_box_top())
    lines.append(_w79_box_line(f"Total: {total_ins} insights em {len(by_tag)} camadas"))
    lines.append(_w79_box_line(""))

    # Show top insights per layer (up to 5 each for L1-L5)
    layer_map = [
        ("[FILOSOFIA]",    "🧠 L1 Filosofias",        5),
        ("[MODELO-MENTAL]","🧩 L2 Modelos Mentais",   5),
        ("[HEURISTICA]",   "🎯 L3 Heuristicas",       4),
        ("[FRAMEWORK]",    "🏗️ L4 Framework principal", 3),
        ("[METODOLOGIA]",  "🛤️ L5 Metodologias",       5),
    ]
    for tag_key, label, max_show in layer_map:
        tag_insights = by_tag.get(tag_key, [])
        if not tag_insights:
            continue
        lines.append(_w79_box_line(f"{label} — {len(tag_insights)} total:"))
        for ins in tag_insights[:max_show]:
            quote = ins.get("quote", ins.get("insight", ""))[:68]
            ins_id = ins.get("id", "")
            chunk = ins.get("chunks", [None])[0] if ins.get("chunks") else ""
            ref = f"[{ins_id}·{chunk}]" if ins_id else ""
            lines.append(_w79_box_line(f"  \"{quote}\" {ref[:12]}"))
        if len(tag_insights) > max_show:
            lines.append(_w79_box_line(f"  ... +{len(tag_insights)-max_show} mais"))
        lines.append(_w79_box_line(""))

    lines.append(_w79_box_bot())
    lines.append("")

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 4 — AGENT ENRICHMENT REPORT (LOG 4)
    # ════════════════════════════════════════════════════════════════════════
    lines.append(_w79_sep("🤖  LOG 4 — AGENT ENRICHMENT REPORT"))
    lines.append(_w79_box_top())
    if not agents_info:
        lines.append(_w79_box_line("(nao disponivel)"))
    else:
        lines.append(_w79_box_line(f"  {'Agente':<34} {'Tamanho':<12} {'Ultima atualizacao'}"))
        lines.append(_w79_box_line("  " + "─" * 60))
        for agent in agents_info:
            name = str(agent["name"])[:33]
            size_kb = agent["size_bytes"] // 1024
            from datetime import timezone as _tz2
            mtime = datetime.fromtimestamp(agent["mtime"], tz=_tz2.utc).strftime("%Y-%m-%d")
            lines.append(_w79_box_line(f"  {name:<34} {size_kb}KB{'':<9} {mtime}"))
    lines.append(_w79_box_bot())
    lines.append("")

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 5 — ROLE-TRACKING REPORT (LOG 3)
    # ════════════════════════════════════════════════════════════════════════
    lines.append(_w79_sep("👤  LOG 3 — ROLE-TRACKING REPORT"))
    lines.append(_w79_box_top())
    if not role_data:
        lines.append(_w79_box_line("(nao disponivel)"))
    else:
        rt_bucket = role_data.get("bucket", "(nao disponivel)")
        rt_domains = ", ".join(role_data.get("domains", [])) or "(nenhum)"
        rt_themes = ", ".join(role_data.get("themes", [])) or "(nenhum)"
        rt_updated = role_data.get("last_updated", "(nao disponivel)")[:19]
        rt_gate = gate_data.get("gate_status", "(nao disponivel)")
        lines.append(_w79_box_line(f"Slug:          {slug}"))
        lines.append(_w79_box_line(f"Bucket:        {rt_bucket}"))
        lines.append(_w79_box_line(f"Domains:       {rt_domains}"))
        lines.append(_w79_box_line(f"Themes:        {rt_themes}"))
        lines.append(_w79_box_line(f"Gate status:   {rt_gate}"))
        lines.append(_w79_box_line(f"Ultima atualizacao: {rt_updated}"))
        lines.append(_w79_box_line(f"Fontes processadas: {total_ins} insights"))
        lines.append(_w79_box_line(""))
        lines.append(_w79_box_line(f"Interpretacao: {person_name} atua nos dominios {rt_domains[:40]}"))
    lines.append(_w79_box_bot())
    lines.append("")

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 6 — CASCADE: DOSSIERS E AGREGADOS DE DOMINIO
    # ════════════════════════════════════════════════════════════════════════
    lines.append(_w79_sep("📚  CASCADE — DOSSIERS E AGREGADOS DE DOMINIO"))

    # Sub-box 1: Person Dossier
    lines.append(_w79_box_top("Person Dossier"))
    if not dossier_info.get("exists"):
        lines.append(_w79_box_line(f"dossier-{slug}.md: (nao existe)"))
    else:
        size_kb = dossier_info.get("size_bytes", 0) // 1024
        sections = dossier_info.get("sections", [])
        lines.append(_w79_box_line(f"dossier-{slug}.md: {size_kb}KB · {len(sections)} secoes"))
        for s in sections[:6]:
            lines.append(_w79_box_line(f"  {s[:70]}"))
    lines.append(_w79_box_bot())

    # Sub-box 2: Theme Dossiers
    lines.append(_w79_box_top("Theme Dossiers"))
    if not theme_dossiers:
        lines.append(_w79_box_line("(nenhum dossier tematico encontrado)"))
    else:
        lines.append(_w79_box_line(f"{len(theme_dossiers)} dossies tematicos em knowledge/{bucket}/dossiers/themes/"))
        for td in theme_dossiers[:8]:
            lines.append(_w79_box_line(f"  📄 {td}"))
        if len(theme_dossiers) > 8:
            lines.append(_w79_box_line(f"  ... +{len(theme_dossiers)-8} mais"))
    lines.append(_w79_box_bot())

    # Sub-box 3: Domain AGGs
    lines.append(_w79_box_top("Domain AGGs"))
    if not domain_aggs:
        lines.append(_w79_box_line("(sem AGGs de dominio para este slug)"))
    else:
        for domain, agg in domain_aggs.items():
            entries = agg.get("total_entries", "?")
            experts = agg.get("total_experts", "?")
            updated = str(agg.get("updated", "(?)"))[:10]
            lines.append(_w79_box_line(f"  {domain:<20} {entries} entries · {experts} experts · {updated}"))
    lines.append(_w79_box_bot())
    lines.append("")

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 7 — CROSS-REFERENCES E CONEXOES COGNITIVAS
    # ════════════════════════════════════════════════════════════════════════
    lines.append(_w79_sep("🔗  CROSS-REFERENCES e CONEXOES COGNITIVAS"))
    lines.append(_w79_box_top())
    # Try to load contradictions from INSIGHTS-STATE
    try:
        ipath = ARTIFACTS / "insights" / slug / "INSIGHTS-STATE.json"
        idata = json.loads(ipath.read_text(encoding="utf-8")) if ipath.exists() else {}
        contradictions = idata.get("contradictions", []) if isinstance(idata, dict) else []
    except Exception:
        contradictions = []

    lines.append(_w79_box_line("Convergencias detectadas:"))
    # look for MODELO-MENTAL insights mentioning other people as cross-refs
    cross_refs: list[str] = []
    for ins in all_insights[:40]:
        text = ins.get("insight", "") + ins.get("quote", "")
        for expert in ["Hormozi", "Hormozi", "Gerber", "Robbins", "Brunson"]:
            if expert.lower() in text.lower() and expert not in cross_refs:
                cross_refs.append(expert)
    if cross_refs:
        for xr in cross_refs[:5]:
            lines.append(_w79_box_line(f"  🔗 Mencao a: {xr}"))
    else:
        lines.append(_w79_box_line("  (sem convergencias explicitamente detectadas)"))
    lines.append(_w79_box_line(""))
    lines.append(_w79_box_line("Contradicoes/tensoes:"))
    if contradictions:
        for c in contradictions[:4]:
            desc = str(c)[:65] if isinstance(c, str) else str(c.get("description", c))[:65]
            lines.append(_w79_box_line(f"  ⚡ {desc}"))
    else:
        lines.append(_w79_box_line("  (nenhuma contradicao registrada)"))
    lines.append(_w79_box_bot())
    lines.append("")

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 8 — ANOMALIAS DETECTADAS
    # ════════════════════════════════════════════════════════════════════════
    lines.append(_w79_sep("⚠️  ANOMALIAS DETECTADAS — atencao do operador"))
    lines.append(_w79_box_top())
    anomalias: list[str] = []

    # Pull from health issues
    health_issues = health_data.get("issues", []) if isinstance(health_data, dict) else []
    for issue in health_issues[:5]:
        anomalias.append(str(issue)[:70])

    # Phase-8 gate failures
    gate_failures = gate_data.get("failures", []) if isinstance(gate_data, dict) else []
    for f in gate_failures[:3]:
        anomalias.append(f"gate-fail: {f}")

    if not anomalias:
        lines.append(_w79_box_line("✅ Nenhuma anomalia detectada."))
    else:
        for i, anomalia in enumerate(anomalias, 1):
            lines.append(_w79_box_line(f"  {i}. ⚠️  {anomalia[:65]}"))
    lines.append(_w79_box_bot())
    lines.append("")

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 9 — HEALTH SCORE
    # ════════════════════════════════════════════════════════════════════════
    lines.append(_w79_sep("📊  HEALTH SCORE — estado do sistema 0-100"))
    lines.append(_w79_box_top())
    score_total = health_data.get("score_total", 0) if isinstance(health_data, dict) else 0
    grade = health_data.get("grade", "(nao disponivel)") if isinstance(health_data, dict) else "(nao disponivel)"
    score_pct = score_total
    bar = _w79_progress_bar(score_pct, 30)
    lines.append(_w79_box_line(f"Score total: {score_total}/100  Grade: {grade}"))
    lines.append(_w79_box_line(f"[{bar}]"))
    lines.append(_w79_box_line(""))

    components = health_data.get("components", {}) if isinstance(health_data, dict) else {}
    dim_labels = {
        "state_files": "State files",
        "agents":      "Agents",
        "dossiers":    "Dossiers",
        "inbox":       "Inbox",
        "pipeline":    "Pipeline",
    }
    for dim_key, dim_label in dim_labels.items():
        dim = components.get(dim_key, {})
        if not isinstance(dim, dict):
            continue
        dim_score = dim.get("score", 0)
        dim_max = dim.get("max", 20)
        dim_pct = (dim_score / dim_max * 100) if dim_max else 0
        dim_bar = _w79_progress_bar(dim_pct, 18)
        lines.append(_w79_box_line(f"  {dim_label:<14} {dim_score:>2}/{dim_max}  [{dim_bar}]"))

    lines.append(_w79_box_line(""))
    lines.append(_w79_box_line("Significado: score reflete qualidade do estado do sistema de conhecimento"))
    lines.append(_w79_box_bot())
    lines.append("")

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 10 — PROXIMA ETAPA
    # ════════════════════════════════════════════════════════════════════════
    lines.append(_w79_sep("⭐  PROXIMA ETAPA — pendencias humanas"))
    lines.append(_w79_box_top())

    pending: list[tuple[str, str, str]] = []

    # P1 — RAG gate if WARN/FAIL
    gate_st = gate_data.get("gate_status", "")
    if gate_st and gate_st != "PASS":
        pending.append(("🔴 P1", "Resolver falhas no Phase-8 Gate", "~15min"))

    # P2 — dossier missing
    if not dossier_info.get("exists"):
        pending.append(("🔴 P2", f"Gerar dossier-{slug}.md (consolidate)", "~5min"))

    # P3 — health inbox issues
    if any("inbox" in str(i).lower() for i in health_issues):
        pending.append(("🟡 P3", "Processar arquivos antigos no inbox", "~30min"))

    # P4 — domain AGGs missing for role domains
    missing_aggs = [d for d in domains if d not in domain_aggs]
    if missing_aggs:
        pending.append(("🟡 P4", f"Gerar AGGs para dominios: {', '.join(missing_aggs[:3])}", "~10min"))

    # P5 — review briefing
    if briefing_info.get("name"):
        pending.append(("🟢 P5", f"Revisar briefing: {briefing_info['name']}", "~5min"))

    # P6 — cross-reference expansion
    pending.append(("🟢 P6", "Expandir cross-references com outros experts do sistema", "~20min"))

    if not pending:
        pending.append(("🟢 P1", "Sistema saudavel. Revisar dossier gerado.", "~5min"))

    for i, (priority, desc, effort) in enumerate(pending, 1):
        lines.append(_w79_box_line(f"{priority}: {desc} — Esforco: {effort}"))

    lines.append(_w79_box_bot())
    lines.append("")

    # ════════════════════════════════════════════════════════════════════════
    # FOOTER — RESUMO EXECUTIVO 3 LINHAS
    # ════════════════════════════════════════════════════════════════════════
    # Build 3-line executive summary
    domains_str = ", ".join(domains[:3]) if domains else "dominios nao mapeados"
    line1 = f"Processamos {total_ins} insights de {person_name} nos dominios: {domains_str}."
    line2 = (
        f"Sistema em saude {grade} (score {score_total}/100). "
        f"Gate Phase-8: {gate_data.get('gate_status', '?')}."
    )
    line3 = (
        f"Dossier: {'gerado (' + str(dossier_info.get('size_bytes',0)//1024) + 'KB)' if dossier_info.get('exists') else 'PENDENTE'}. "
        f"Proxima acao: {pending[0][1][:40]}."
    )

    bot_inner = "═" * (W79 - 2)
    lines.append("╔" + bot_inner + "╗")
    lines.append(_w79_double_line(""))
    lines.append(_w79_double_line("📈  RESUMO EXECUTIVO EM 3 LINHAS:"))
    lines.append(_w79_double_line(""))
    # wrap each line to fit W79 - 4
    content_w = W79 - 4
    for raw_line in (line1, line2, line3):
        if len(raw_line) <= content_w:
            lines.append(_w79_double_line(raw_line))
        else:
            # simple word-wrap
            words = raw_line.split()
            current = ""
            for word in words:
                if len(current) + len(word) + 1 > content_w:
                    lines.append(_w79_double_line(current))
                    current = word
                else:
                    current = (current + " " + word).strip()
            if current:
                lines.append(_w79_double_line(current))
    lines.append(_w79_double_line(""))
    lines.append("╚" + bot_inner + "╝")
    lines.append("")
    lines.append(f"Gerado em: {now_ts}")
    lines.append("")

    content = "\n".join(lines)

    # ── save to logs/full-pipeline-reports/ ─────────────────────────────────
    try:
        save_dir = ROOT / "logs" / "full-pipeline-reports"
        save_dir.mkdir(parents=True, exist_ok=True)
        ts_file = datetime.now().strftime("%Y%m%d-%H%M%S")
        save_path = save_dir / f"FULL-{slug.upper()}-{ts_file}.md"
        save_path.write_text(content, encoding="utf-8")
        logger.info("Full pipeline report saved: %s", save_path)
    except Exception as exc:
        logger.warning("Failed to save full pipeline report: %s", exc)

    return content


# ═══════════════════════════════════════════════════════════════════════════════
# CHRONICLER v3.0.0 — 44 STEPS, 79-char width, didactic boxes
# Story MCE-14.0
# ═══════════════════════════════════════════════════════════════════════════════

_V3_W = 79          # Hard cap — NO line may exceed this
_V3_INNER = 77      # Inner width of ╔══╗ box: W - 2 border chars
_V3_BOX_INNER = 75  # Inner width of ┌──┐ inside step: W - 4 (║ space + │ space)
_V3_NO_DATA = "_(secao sem dados nesta execucao)_"
# MCE-17.0 T10: Explicit fail sentinel rendered when MCE_NO_FALLBACK=1 and
# both stream data and disk fallback are disabled/missing.
_V3_FAIL_NO_DATA = "FAIL_NO_DATA — sem stream vivo, fallback de disco desabilitado (MCE_NO_FALLBACK=1)"


def _v3_pad(text: str, width: int) -> str:
    """Pad or truncate text to exact width — never exceeds."""
    if len(text) >= width:
        return text[:width]
    return text + " " * (width - len(text))


def _v3_step_top(num: int, emoji: str, title: str) -> str:
    """Build ╔═══ EMOJI  STEP NN — TITLE ═══╗ header at exactly 79 chars."""
    label = f"  {emoji}  STEP {num:02d} — {title}  "
    total_inner = _V3_W - 2  # 77 chars between ╔ and ╗
    pad_left = (total_inner - len(label)) // 2
    pad_right = total_inner - len(label) - pad_left
    if pad_left < 0:
        # Title too long — truncate
        label = label[: total_inner]
        pad_left = 0
        pad_right = 0
    line = "╔" + "═" * pad_left + label + "═" * pad_right + "╗"
    # Enforce hard cap
    return line[:_V3_W]


def _v3_step_bot() -> str:
    return "╚" + "═" * (_V3_W - 2) + "╝"


def _v3_canonical_top(prefix: str, emoji: str, title: str) -> str:
    """Top border for canonical (non-step) blocks. Width = 79 chars.

    Unlike _v3_step_top, has no 'STEP NN' label — just prefix + title.
    Story: MCE-16.4
    """
    label = f"  {emoji}  {prefix}: {title}  "
    total_inner = _V3_W - 2  # 77 chars between ╔ and ╗
    pad_total = total_inner - len(label)
    if pad_total < 0:
        # Truncate label if too long
        label = label[:total_inner]
        pad_total = 0
    pad_left = pad_total // 2
    pad_right = pad_total - pad_left
    line = "╔" + "═" * pad_left + label + "═" * pad_right + "╗"
    return line[:_V3_W]


def _v3_box_top() -> str:
    return "┌" + "─" * (_V3_W - 2) + "┐"


def _v3_box_bot() -> str:
    return "└" + "─" * (_V3_W - 2) + "┘"


def _v3_box_line(text: str = "") -> str:
    """│ text │ at exactly 79 chars."""
    inner = _V3_W - 4  # 75 chars
    padded = _v3_pad(text, inner)
    return f"│ {padded} │"


def _v3_box_sep() -> str:
    """├──────────────┤ separator at 79 chars."""
    return "├" + "─" * (_V3_W - 2) + "┤"


def _v3_step(num: int, emoji: str, title: str, box_lines: list[str]) -> list[str]:
    """Assemble a full step: ╔══╗ wrapper + ┌──┐ data box."""
    out: list[str] = [
        "",
        _v3_step_top(num, emoji, title),
    ]
    out.append(_v3_box_top())
    for bl in box_lines:
        out.append(_v3_box_line(bl))
    out.append(_v3_box_bot())
    out.append(_v3_step_bot())
    return out


def _v3_header(person_name: str, slug: str, now: str) -> list[str]:
    """Monumental header with solid ████ blocks at 79 chars."""
    solid = "█" * _V3_W
    tag = _make_tag(slug)
    title = "M C E   P I P E L I N E   L O G   v 3 . 2"
    sub = f"{person_name}  ({tag})  *  {now}"
    inner = _V3_W - 8  # 71 chars between ████████ pairs (4+71+4=79)
    return [
        solid,
        solid,
        "████" + " " * inner + "████",
        "████" + _v3_pad(title.center(inner), inner) + "████",
        "████" + " " * inner + "████",
        "████" + _v3_pad(sub.center(inner), inner) + "████",
        "████" + " " * inner + "████",
        solid,
        solid,
    ]


def _v3_footer(person_name: str, slug: str, now: str) -> list[str]:
    """Monumental footer with solid ████ blocks at 79 chars."""
    solid = "█" * _V3_W
    tag = _make_tag(slug)
    title = f"MCE PIPELINE LOG v3.2 — {person_name} ({tag})"
    inner = _V3_W - 8  # 71 chars
    return [
        "",
        solid,
        solid,
        "████" + " " * inner + "████",
        "████" + _v3_pad(title.center(inner), inner) + "████",
        "████" + _v3_pad(f"v3.2.0  |  {now}".center(inner), inner) + "████",
        "████" + _v3_pad("Chronicler Design System v3.2.0  |  44 STEPS + 2 CANONICAL BLOCKS".center(inner), inner) + "████",
        "████" + " " * inner + "████",
        solid,
        solid,
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# CHRONICLER v4.0 RENDER LAYER  (Story MCE-17.x — founder-approved officialization)
# ═══════════════════════════════════════════════════════════════════════════════
#
# v4 keeps the EXACT data-extraction of v3.2 — every ``_step_NN(data)`` function
# is left untouched and still returns its v3 box. The v4 layer is a pure RENDER
# transform: it parses the v3 box back into zones (status / metrics / extra /
# why), then re-renders each step as a wide (100-col) box grouped into 6 pipeline
# phases, with status ribbons, a 2-column metrics sub-table, an inline glossary
# (curated per step) and a progress bar per group banner.
#
# Design principles:
#   * ZERO data loss — every value token in the v3 box survives as a metric value,
#     an ``extra`` line, or ``why`` text. Guaranteed by parsing, not rewriting.
#   * Display-width aware — emoji and status icons count as 2 cells so boxes never
#     skew (``_v4_dwidth``). W = 100, INNER = 98.
#   * Self-contained, stdlib only. Mirrors the validated prototype primitives in
#     ``.claude/skills/chronicler/chronicler_v4_prototype.py``.
#
# Gate: ``MCE_LOG_TEMPLATE`` env (default ``v4``; set ``v3.2`` to force legacy).
# ─────────────────────────────────────────────────────────────────────────────

import unicodedata as _v4_unicodedata

_V4_W = 100          # total box width (founder directive: wider than v3.2's 79)
_V4_INNER = _V4_W - 2  # content field between the two vertical borders (98)

# True double-width glyphs (emoji + status icons). Block/shade/star glyphs
# (█▓░▒★·) render single-width in monospace terminals — NOT included.
_V4_WIDE_EMOJI = set(
    "🧮🛡📥👁🧬📋📌📂📦✂🧩🧠🎯🏗🛤🔄⭐💬🔥⚡🔍📜🚀📚🎵📝🗺🏢🚦📈📤📊💰🤖🌳💡📖🔎"
    "✅⚠️❌🟡🟢🟠🔴⏭⚪"
)


def _v4_dwidth(s: str) -> int:
    """Display width of a string (emoji / wide CJK count as 2 cells)."""
    w = 0
    for ch in s:
        if ch in _V4_WIDE_EMOJI or _v4_unicodedata.east_asian_width(ch) in ("W", "F"):
            w += 2
        elif ch == "️":  # variation selector — invisible
            w += 0
        else:
            w += 1
    return w


def _v4_clip(s: str, width: int) -> str:
    """Truncate s to ``width`` display columns (display-aware, adds … if cut)."""
    if _v4_dwidth(s) <= width:
        return s
    out = ""
    w = 0
    for ch in s:
        cw = _v4_dwidth(ch)
        if w + cw > width - 1:
            break
        out += ch
        w += cw
    return out + "…"


def _v4_pad(s: str, width: int) -> str:
    """Left-justify s to ``width`` display columns; truncate if it overflows."""
    s = _v4_clip(s, width)
    gap = width - _v4_dwidth(s)
    return s + " " * max(0, gap)


def _v4_rule_top() -> str:
    return "╔" + "═" * _V4_INNER + "╗"


def _v4_rule_mid() -> str:
    return "╟" + "─" * _V4_INNER + "╢"


def _v4_rule_bot() -> str:
    return "╚" + "═" * _V4_INNER + "╝"


def _v4_row(s: str = "") -> str:
    """A content row: ║ + ' ' + s padded to INNER + ║  (total W)."""
    body = " " + s
    return "║" + _v4_pad(body, _V4_INNER) + "║"


def _v4_row_split(left: str, right: str) -> str:
    """Row with left text and right-aligned text inside the box."""
    avail = _V4_INNER - 1  # leading space
    gap = avail - _v4_dwidth(left) - _v4_dwidth(right)
    body = " " + left + " " * max(1, gap) + right
    return "║" + _v4_pad(body, _V4_INNER) + "║"


def _v4_kv_table(title: str, pairs: list[tuple[str, str]], indent: int = 2) -> list[str]:
    """Render a 2-column key/value sub-box inside the main box.

    Geometry (display cells), tuned so each row fits INNER without clipping:
      ind(2) + "│ "(2) + cell(colw) + " │ "(3) + cell(colw) + " │"(2)
    """
    ind = " " * indent
    colw = 42
    seg = "─" * (colw + 2)
    cells: list[str] = []
    for k, v in pairs:
        cells.append(f"{_v4_pad(k, 16)} {v}")
    if len(cells) % 2 == 1:
        cells.append("")
    out: list[str] = []
    title_dash = colw + 2 - _v4_dwidth(title) - 3  # "─ TITLE " consumed
    out.append(_v4_row(f"{ind}┌─ {title} " + "─" * max(1, title_dash) + "┬" + seg + "┐"))
    for i in range(0, len(cells), 2):
        left = _v4_pad(_v4_clip(cells[i], colw), colw)
        right = _v4_pad(_v4_clip(cells[i + 1], colw), colw)
        out.append(_v4_row(f"{ind}│ {left} │ {right} │"))
    out.append(_v4_row(f"{ind}└" + seg + "┴" + seg + "┘"))
    return out


def _v4_progress_bar(done: int, total: int, width: int = 30) -> str:
    filled = int(round(width * done / total)) if total else 0
    filled = max(0, min(width, filled))
    return "▓" * filled + "░" * (width - filled)


def _v4_wrap(text: str, width: int) -> list[str]:
    """Greedy word-wrap honoring display width."""
    words = text.split()
    lines: list[str] = []
    cur = ""
    for wd in words:
        if cur and _v4_dwidth(cur + " " + wd) > width:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    if cur:
        lines.append(cur)
    return lines or [""]


# ── STEP → GROUP map (the 6 pipeline phases) ────────────────────────────────
# (name, step-range label, step count). Mirrors the approved TEMPLATE-v4-DESIGN.
_V4_GROUPS: dict[int, tuple[str, str, int]] = {
    1: ("INGESTÃO & PREPARAÇÃO", "00–11", 12),
    2: ("EXTRAÇÃO DE DNA (L1–L10)", "12–21", 10),
    3: ("IDENTIDADE & CONSOLIDAÇÃO", "22–25", 4),
    4: ("CASCATEAMENTO", "26–31", 6),
    5: ("GATES & QUALIDADE", "32–36", 5),
    6: ("FINALIZAÇÃO & TELEMETRIA", "37–44", 8),
}


def _v4_group_for(step_num: int) -> int:
    """Return the group (1-6) for a STEP number (0-44)."""
    if step_num <= 11:
        return 1
    if step_num <= 21:
        return 2
    if step_num <= 25:
        return 3
    if step_num <= 31:
        return 4
    if step_num <= 36:
        return 5
    return 6


# ── per-STEP GLOSSARY map (only steps with real jargon) ─────────────────────
# Curated from the validated prototype. Steps absent here render no glossary.
_V4_GLOSSARY: dict[int, list[tuple[str, str]]] = {
    1: [("identity key", "impressão digital (hash) do material. Se 2 arquivos têm a "
                         "mesma, são duplicata e o pipeline pula (SKIP).")],
    2: [("captions", "legendas automáticas do YouTube — fallback quando o Gemini não "
                     "devolve transcript nativo.")],
    5: [("sidecar", "arquivo-passaporte ao lado do material com metadados de roteamento. "
                    "Sem ele, o Guard não deduplica entre execuções.")],
    8: [("batch", "unidade atômica de processamento. Se o LLM falha no chunk 47, só esse "
                  "batch é retentado — não o vídeo inteiro.")],
    9: [("chunk", "pedaço de ~300 palavras. Janela ideal pra busca semântica: grande "
                  "demais perde precisão, pequeno demais explode custo.")],
    10: [("embedding", "vetor de 1536 números que descreve o SIGNIFICADO do texto, "
                       "permitindo busca por sentido (não por palavra literal).")],
    11: [("alias explosion", "quando 'Alex Hormozi', 'Hormozi' e 'Alex H.' viram 3 pessoas "
                             "diferentes — fragmenta o grafo de conhecimento.")],
    12: [("filosofia (L1)", "crença fundamental que guia TODAS as decisões do especialista. "
                            "As premissas que não mudam.")],
    13: [("modelo mental (L2)", "framework cognitivo pra LER situações — a lente pela qual "
                               "o especialista interpreta o mundo.")],
    14: [("heurística (L3)", "regra prática com número: 'Se X então Y'. O insight que vira "
                            "ação direta — por isso o mais valioso.")],
    15: [("framework (L4)", "modelo estruturado com componentes e etapas nomeadas — ex.: "
                           "'as 4 fases de um funil de VSL'.")],
    16: [("metodologia (L5)", "processo step-by-step com inputs e outputs — o 'como fazer' "
                             "detalhado, executável.")],
    17: [("padrão comportamental (L6)", "automatismo gatilho→ação: quando ACONTECE X, o "
                                        "especialista REAGE com Y, sem pensar.")],
    18: [("hierarquia de valores (L7)", "o que é inegociável e em que ordem. Define "
                                        "trade-offs quando 2 coisas boas conflitam.")],
    19: [("Voice DNA (L8)", "tom + frases-assinatura = identidade vocal. Sem ela o agente "
                           "soa genérico, não soa como a pessoa.")],
    20: [("obsessão (L9)", "tema recorrente que a pessoa não larga — aparece sem parar na "
                          "fala. Revela prioridade cognitiva real.")],
    21: [("paradoxo (L10)", "tensão produtiva entre dois valores/ideias que o especialista "
                           "sustenta ao mesmo tempo. Sinal de maturidade cognitiva.")],
    22: [("checkpoint", "o Lens decide APPROVE / REVISE / ABORT comparando as 10 camadas "
                        "entre si. DNA incoerente = agente que se contradiz.")],
    23: [("dossiê", "documento narrativo com todo o DNA integrado. É a fonte de verdade que "
                    "o agente lê durante queries do usuário.")],
    24: [("promoção", "Echo grava frontmatter status=complete e versão ≥1.0.0. Sem isso o "
                      "Lens nega o gate e o pipeline trava no STEP 22.")],
    25: [("MEMORY.md", "experiência acumulada do agente entre ingestões. Sem ela o agente "
                       "responde só com DNA estático, sem aprendizado.")],
    26: [("role-tracker", "mapa 'quem sabe o quê' — registra em quais domínios e temas o "
                          "especialista é referência, pra rotear queries certas pra ele.")],
    27: [("dossiê de tema", "visão agregada de MÚLTIPLOS experts num mesmo tema — ex.: "
                           "'vendas' junta Hormozi + Cole Gordon + Jeremy Haynes.")],
    28: [("solo P×Tema", "a perspectiva individual isolada de UMA pessoa sobre UM tema. "
                         "Facilita 'o que A pensa sobre X vs o que B pensa'.")],
    29: [("narrativa", "insights soltos comprimidos em texto fluido. É o que o agente 'lê' "
                       "pra responder com a voz da pessoa, não em bullets.")],
    30: [("sources.md", "lista as fontes primárias por tema. Permite auditoria: 'esse "
                        "insight veio de qual vídeo/livro?'.")],
    31: [("MAP-CONFLITOS", "identifica onde experts do mesmo domínio DIVERGEM. Essas "
                           "tensões são o material mais rico pro Conclave.")],
    32: [("gate de regressão", "garante que o índice nunca DIMINUA além da tolerância sem "
                               "aprovação. Crescimento é normal e sempre permitido.")],
    33: [("L0–L4", "camadas do workspace: L0 identidade (365d), L1 estratégia (90d), "
                   "L2 tático (60d), L3 produto (30d), L4 operacional (7d).")],
    35: [("dev (deviation)", "desvio % vs média histórica do MESMO expert. < -50% = "
                             "anomalia crítica (vermelho); < -25% = moderada (amarelo).")],
    37: [("lifecycle move", "move o material processado de inbox/ pra processed/. Sem isso "
                            "o inbox cresce infinito e cada run reprocessa tudo.")],
    38: [("batch history", "série temporal de métricas do pipeline. É a base do cross-batch "
                           "analysis (STEP 35) pra detectar anomalias.")],
    40: [("squad activation", "audit trail de quais squads/hooks rodaram. Se o pipeline "
                              "falha em silêncio, mostra qual squad não foi acionado.")],
    41: [("briefing executivo", "resumo de 3-5 parágrafos gerado por LLM. O operador lê em "
                                "30s o que mudou e a próxima ação.")],
    44: [("chronicler audit", "meta-verificação que o próprio log faz pra garantir que os "
                              "44 STEPs renderizaram. Se mostra faltando, há bug no renderer.")],
}

# Icons per STEP (mirror the v3 _step_NN emoji argument; used by v4 header zone).
_V4_STEP_ICON: dict[int, str] = {
    0: "\U0001f50e", 1: "\U0001f6e1", 2: "\U0001f4e5", 3: "\U0001f441",
    4: "\U0001f9ec", 5: "\U0001f4cb", 6: "\U0001f4cc", 7: "\U0001f4c2",
    8: "\U0001f4e6", 9: "✂️", 10: "\U0001f9ee", 11: "\U0001f9e9",
    12: "\U0001f9e0", 13: "\U0001f9e9", 14: "\U0001f3af", 15: "\U0001f3d7",
    16: "\U0001f6e4", 17: "\U0001f504", 18: "⭐", 19: "\U0001f4ac",
    20: "\U0001f525", 21: "⚡", 22: "\U0001f50d", 23: "\U0001f4dc",
    24: "\U0001f680", 25: "\U0001f9e0", 26: "\U0001f4cb", 27: "\U0001f4da",
    28: "\U0001f3b5", 29: "\U0001f4dd", 30: "\U0001f4da", 31: "\U0001f5fa",
    32: "\U0001f50d", 33: "\U0001f3e2", 34: "\U0001f6a6", 35: "\U0001f4c8",
    36: "⚡", 37: "\U0001f4e4", 38: "\U0001f4ca", 39: "\U0001f4b0",
    40: "\U0001f916", 41: "\U0001f4cb", 42: "\U0001f4ca", 43: "⭐",
    44: "\U0001f50e",
}

# Didactic-header prefixes that mark the start of the "why" zone in a v3 box.
_V4_WHY_INTROS = (
    "Por que", "Como interpretar", "O que e", "O que é",
    "O que aconteceria", "O que e o", "O que é o",
)


def _v4_is_why_header(line: str) -> bool:
    """True when a (stripped) box line opens the didactic block."""
    s = line.strip()
    if not s:
        return False
    if s[0].isspace():  # indented continuation, not a header
        return False
    for intro in _V4_WHY_INTROS:
        if s.startswith(intro):
            return True
    # Generic: a top-level question line acts as a didactic header.
    return s.endswith("?") and not line.startswith(" ")


def _v4_strip_box(v3_lines: list[str]) -> list[str]:
    """Recover the raw box content from a v3 _v3_step()/canonical output.

    The v3 output is: ['', '╔...╗', '┌...┐', '│ content │' *, '└...┘', '╚...╝'].
    We return only the inner content lines (rstripped), preserving order and
    blank separators — i.e. the exact ``box`` list the step built.
    """
    out: list[str] = []
    for ln in v3_lines:
        if not ln:
            continue
        first = ln[0]
        if first in ("╔", "╚", "┌", "└", "╟", "├"):
            continue
        if first == "│":
            # '│ <content padded> │' → strip 1 border + 1 space each side.
            inner = ln[1:-1]
            if inner.startswith(" "):
                inner = inner[1:]
            if inner.endswith(" "):
                inner = inner[:-1]
            out.append(inner.rstrip())
        # ignore anything else (defensive)
    return out


_V4_METRIC_RE = __import__("re").compile(r"^([^:][^:]{0,24}?):\s{1,}(.+)$")


def _v4_parse_box(box: list[str]) -> tuple[str, list[tuple[str, str]], list[str], str, str]:
    """Parse a v3 box content list into v4 zones.

    Returns ``(status, metrics, extra, why)`` where:
      * status  — a 1-line ribbon derived from the strongest verdict/headline.
      * metrics — ``[(label, value)]`` from ``Label:   value`` lines.
      * extra   — verbatim lines that aren't metrics (samples, grids, bars,
                  headlines) — preserved so NO data is lost.
      * why     — the didactic paragraph (joined continuation lines).
    """
    # 1. Split off the didactic ("why") tail.
    why_idx = None
    for i, ln in enumerate(box):
        if _v4_is_why_header(ln):
            why_idx = i
            break
    head = box[:why_idx] if why_idx is not None else list(box)
    why_block = box[why_idx:] if why_idx is not None else []

    # Drop the header line itself (e.g. "Por que esse passo existe?") — the v4
    # render zone re-emits a styled "📖 …" title, so keeping it duplicates text.
    why_header = why_block[0].strip() if why_block else ""
    why_body = why_block[1:] if why_block else []
    why_text = " ".join(p.strip() for p in why_body if p.strip())
    if why_header.lower().startswith(("como interpretar", "como interpret")):
        why_title = "COMO INTERPRETAR?"
    elif why_header.lower().startswith("o que aconteceria"):
        why_title = "O QUE ACONTECERIA SEM ESTE PASSO?"
    elif why_header.lower().startswith(("o que e", "o que \u00e9")):
        why_title = why_header.rstrip("?").upper() + "?"
    else:
        why_title = "POR QUE ESTE PASSO EXISTE?"

    # 2. Classify head lines into metrics vs extra.
    metrics: list[tuple[str, str]] = []
    extra: list[str] = []
    for ln in head:
        if not ln.strip():
            continue
        # Indented lines (samples/grids/tree) are always extra.
        if ln.startswith(" "):
            extra.append(ln.strip())
            continue
        m = _V4_METRIC_RE.match(ln)
        if m and not ln.startswith("["):
            label = m.group(1).strip()
            value = m.group(2).strip()
            metrics.append((label, value))
        else:
            extra.append(ln.strip())

    # 3. Derive the status ribbon.
    status = _v4_derive_status(metrics, extra)
    return status, metrics, extra, why_text, why_title


# Metric labels (lowercased) that carry the headline verdict, in priority order.
_V4_STATUS_KEYS = (
    "verdict", "status", "gate status", "gate (art.xv)", "score total",
    "score", "decision", "acao", "ação", "bucket", "contagem", "tom",
)


def _v4_derive_status(metrics: list[tuple[str, str]], extra: list[str]) -> str:
    """Build a 1-line status ribbon from the parsed metrics/extra."""
    lower = {k.lower(): v for k, v in metrics}
    for key in _V4_STATUS_KEYS:
        if key in lower and lower[key]:
            label = next(k for k, _ in metrics if k.lower() == key)
            return f"{label}: {lower[key]}"
    # Headline-style extra lines (e.g. '✅ Sem contradicoes ...', FAIL sentinel).
    for ln in extra:
        if ln and (ln[0] in "✅⚠❌⏭⚪🟡🟢🔴" or ln.startswith("FAIL") or ln.startswith("_(")):
            return _v4_clip(ln, _V4_INNER - 12)
    if metrics:
        k, v = metrics[0]
        return f"{k}: {v}"
    if extra:
        return _v4_clip(extra[0], _V4_INNER - 12)
    return "—"


def _v4_render_step(
    step_num: int,
    title: str,
    status: str,
    metrics: list[tuple[str, str]],
    extra: list[str],
    glossary: list[tuple[str, str]] | None,
    why: str,
    why_title: str = "POR QUE ESTE PASSO EXISTE?",
    tag: str = "",
) -> list[str]:
    """Render a single v4 wide step box (100 cols, 4 zones)."""
    icon = _V4_STEP_ICON.get(step_num, "•")
    group = _v4_group_for(step_num)
    out: list[str] = [_v4_rule_top()]
    hdr_left = f"{icon}  STEP {step_num:02d} · {title}"
    if tag:
        hdr_left += f"   {tag}"
    out.append(_v4_row_split(hdr_left, f"GRUPO {group} · {step_num:02d}/44"))
    out.append(_v4_rule_mid())
    out.append(_v4_row(f"STATUS   {status}"))
    out.append(_v4_row())
    if extra:
        for e in extra:
            out.append(_v4_row(_v4_clip(e, _V4_INNER - 2)))
        out.append(_v4_row())
    if metrics:
        out.extend(_v4_kv_table("MÉTRICAS", metrics))
        out.append(_v4_row())
    if glossary:
        out.append(_v4_row("💡 GLOSSÁRIO"))
        for term, definition in glossary:
            prefix_w = 3 + _v4_dwidth(term) + 5  # "   " + term + " ··· "
            wl = _v4_wrap(definition, _V4_INNER - 2 - prefix_w)
            out.append(_v4_row(f"   {term} ··· {wl[0]}"))
            for cont in wl[1:]:
                out.append(_v4_row(" " * prefix_w + cont))
        out.append(_v4_row())
    if why:
        wt = why_title
        # Honor the step's own didactic intent (how-to-read vs why-exists).
        if why.strip().lower().startswith(("como interpretar", "como interpret")):
            wt = "COMO INTERPRETAR?"
        out.append(_v4_row(f"📖 {wt}"))
        for wl in _v4_wrap(why, _V4_INNER - 6):
            out.append(_v4_row(f"   {wl}"))
    out.append(_v4_rule_bot())
    return out


def _v4_step_from_v3(step_num: int, title: str, v3_lines: list[str], tag: str = "") -> list[str]:
    """Transform a v3 step output into a v4 wide step box (no data loss)."""
    box = _v4_strip_box(v3_lines)
    status, metrics, extra, why, why_title = _v4_parse_box(box)
    glossary = _V4_GLOSSARY.get(step_num)
    return _v4_render_step(
        step_num=step_num,
        title=title,
        status=status,
        metrics=metrics,
        extra=extra,
        glossary=glossary,
        why=why,
        why_title=why_title,
        tag=tag,
    )


def _v4_canonical_from_v3(prefix: str, title: str, v3_lines: list[str], locator: str) -> list[str]:
    """Render a canonical (pre-00 / post-44) block in v4 wide format."""
    box = _v4_strip_box(v3_lines)
    _, metrics, extra, why, _why_title = _v4_parse_box(box)
    out: list[str] = [_v4_rule_top()]
    icon = "\U0001f4e6" if prefix.startswith("pre") else "\U0001f333"
    out.append(_v4_row_split(f"{icon}  {prefix} · {title}", locator))
    out.append(_v4_rule_mid())
    # Canonical blocks keep their structure verbatim in the extra/metrics zone.
    if extra:
        for e in extra:
            out.append(_v4_row(_v4_clip(e, _V4_INNER - 2)))
        out.append(_v4_row())
    if metrics:
        out.extend(_v4_kv_table("DADOS", metrics))
        out.append(_v4_row())
    if why:
        wt = "POR QUE ESTE BLOCO EXISTE?"
        out.append(_v4_row(f"📖 {wt}"))
        for wl in _v4_wrap(why, _V4_INNER - 6):
            out.append(_v4_row(f"   {wl}"))
    out.append(_v4_rule_bot())
    return out


def _v4_group_banner(group: int, current_step: int) -> list[str]:
    """Render a group banner with a pipeline progress bar."""
    name, steps, n = _V4_GROUPS[group]
    bar = "━" * _V4_INNER
    pct = int(round(current_step / 44 * 100))
    pbar = _v4_progress_bar(current_step, 44, 30)
    right = f"STEPs {steps} · {n} passos"
    left = f"  ▒▒▒  GRUPO {group} · {name}"
    line1 = _v4_pad(left, _V4_W - _v4_dwidth(right) - 2) + right
    line2 = f"  Progresso do pipeline   {pbar}   {pct}%   (STEP {current_step:02d} de 44)"
    return ["", bar, line1, line2, bar, ""]


def _v4_header(person_name: str, slug: str, now: str) -> list[str]:
    """Monumental v4 header (████) with group summary on the cover."""
    bar = "█" * _V4_W
    tag = _make_tag(slug)
    inner = _V4_W - 8

    def c(s: str) -> str:
        return "████" + _v4_pad("   " + s, inner) + "████"

    blank = "████" + " " * inner + "████"
    return [
        bar, bar, blank,
        c("M C E   P I P E L I N E   L O G          v 4 . 0"),
        c(f"{person_name}  ({tag})  ·  {now}"),
        blank,
        c("44 STEPS · 6 GRUPOS · 2 BLOCOS CANÔNICOS · Chronicler v4.0"),
        blank,
        c("GRUPO 1 ▓▓▓ Ingestão      GRUPO 4 ▓▓▓ Cascateamento"),
        c("GRUPO 2 ▓▓▓ DNA L1–L10    GRUPO 5 ▓▓▓ Gates & Qualidade"),
        c("GRUPO 3 ▓▓▓ Identidade    GRUPO 6 ▓▓▓ Finalização"),
        blank,
        bar, bar,
    ]


def _v4_footer(person_name: str, slug: str, now: str) -> list[str]:
    """Monumental v4 footer (████)."""
    bar = "█" * _V4_W
    tag = _make_tag(slug)
    inner = _V4_W - 8

    def c(s: str) -> str:
        return "████" + _v4_pad("   " + s, inner) + "████"

    blank = "████" + " " * inner + "████"
    return [
        "", bar, bar, blank,
        c(f"MCE PIPELINE LOG v4.0 — {person_name} ({tag}) — FIM"),
        c(f"v4.0.0  ·  {now}"),
        c("Chronicler Design System v4.0 · 44 STEPS + 2 CANONICAL BLOCKS"),
        blank,
        bar, bar,
    ]


# ─────────────────────────────────────────────────────────────────────────────
# DISK FALLBACK LOADERS — Story MCE-16.3
# Each loader is pure, read-only, returns dict matching renderer schema or {}.
# Used by _with_disk_fallback() when PHASE-STREAM has no live data.
# ─────────────────────────────────────────────────────────────────────────────


def _with_disk_explicit(loader: Callable[[], dict]) -> dict:
    """Load data explicitly from disk and mark provenance transparently.

    Used for phantom reads where no stream emit exists yet but disk data
    is available and known to be the canonical source.  Unlike the silent
    ``_with_disk_fallback``, this marks ``_fallback_source = "disk_explicit"``
    and does NOT check MCE_NO_FALLBACK — the caller explicitly chose disk.

    Story: MCE-17.0 T12 (Caso B — disk explicit, no producer yet)
    """
    try:
        data = loader() or {}
        if data:
            data["_fallback_source"] = "disk_explicit"
        return data
    except Exception as exc:
        logger.debug(f"[disk_explicit] loader failed gracefully: {exc}")
        return {}


def _with_disk_fallback(stream_data: dict, loader: Callable[[], dict]) -> dict:
    """Return live stream data if non-empty, else disk fallback.

    Annotates fallback with ``_fallback_source = "disk"`` so renderers
    can distinguish provenance.

    When MCE_NO_FALLBACK=1 the disk fallback path is fully disabled.
    Returns a sentinel dict with ``_step_status = "FAIL_NO_DATA"`` so
    every renderer surfaces the missing data explicitly instead of
    silently masking it with stale disk values.

    Story: MCE-16.3 (original) | MCE-17.0 T10 (no-fallback mode)
    """
    if stream_data:
        return stream_data
    # MCE-17.0 T10: no-fallback mode — expose missing data explicitly
    if MCE_NO_FALLBACK:
        return {"_step_status": "FAIL_NO_DATA", "_fallback_source": "disabled"}
    try:
        data = loader() or {}
        if data:
            data["_fallback_source"] = "disk"
        return data
    except Exception as exc:
        logger.debug(f"[disk_fallback] loader failed gracefully: {exc}")
        return {}


def _find_sidecar_for_slug(slug: str) -> dict | None:
    """Locate the entity-discovery.json sidecar for a given slug.

    Search order:
      1. knowledge/external/processed/{slug}/*.entity-discovery.json
      2. knowledge/external/inbox/{slug}/*.entity-discovery.json
      3. knowledge/business/processed/{slug}/*.entity-discovery.json
      4. knowledge/business/inbox/{slug}/*.entity-discovery.json
      5. knowledge/personal/processed/{slug}/*.entity-discovery.json

    Returns parsed dict or None if not found.
    """
    candidates = [
        ROOT / "knowledge" / "external" / "processed" / slug,
        ROOT / "knowledge" / "external" / "inbox" / slug,
        ROOT / "knowledge" / "business" / "processed" / slug,
        ROOT / "knowledge" / "business" / "inbox" / slug,
        ROOT / "knowledge" / "personal" / "processed" / slug,
    ]

    for base in candidates:
        if not base.exists():
            continue
        for f in base.rglob("*.entity-discovery.json"):
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
    return None


def _resolve_bucket_for_slug(slug: str) -> str:
    """Detect which bucket the slug lives in (external/business/personal)."""
    for bucket in ("external", "business", "personal"):
        for sub in ("processed", "inbox"):
            if (ROOT / "knowledge" / bucket / sub / slug).exists():
                return bucket
    return "external"  # default


def _load_source_discovery_from_disk(slug: str) -> dict:
    """STEP 00 — load source discovery from sidecar."""
    sidecar = _find_sidecar_for_slug(slug)
    if not sidecar:
        return {}
    return {
        "source_path": sidecar.get("transcript_sidecar") or sidecar.get("original_filename", ""),
        "source_type": (
            "youtube"
            if sidecar.get("gemini_used") or "youtube" in str(sidecar.get("original_filename", "")).lower()
            else "file"
        ),
        "bucket": _resolve_bucket_for_slug(slug),
        "slug": slug,
        "discovered_at": sidecar.get("ingested_at") or sidecar.get("emitted_at", ""),
    }


def _load_ingestion_guard_from_disk(slug: str) -> dict:
    """STEP 01 — load ingestion guard from registry + sidecar."""
    registry_path = ROOT / ".data" / "ingestion-registry.json"
    sidecar = _find_sidecar_for_slug(slug)

    entry = None
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            for _key, val in (registry.get("entries", {}) or {}).items():
                if isinstance(val, dict) and (
                    val.get("slug") == slug or slug in str(val.get("file_path", ""))
                ):
                    entry = val
                    break
        except Exception:
            pass

    if entry:
        return {
            "action": entry.get("action", "PROCESSED"),
            "reason": entry.get("reason", "already_processed_source"),
            "identity_key": entry.get("identity_key") or slug,
            "body_hash": (
                entry.get("body_hash", "")
                or (sidecar.get("transcript_hash", "") if sidecar else "")
            ),
            "word_count": entry.get("word_count"),
            "previous_word_count": entry.get("previous_word_count"),
            "delta_start_word": entry.get("delta_start_word"),
        }

    # Onda 0 honesty fix (extraction-no-fallbacks): no registry entry for this
    # slug. The PREVIOUS code fabricated action="SKIP",
    # reason="already_processed_source (disk-fallback)", word_count=0, prev=0,
    # delta=0 — values rendered in the MCE log as if they had been measured.
    # That misled a forensic diagnosis. A document chunked via an ephemeral
    # temp file (e.g. a PDF extracted under .data/tmp/pdf-extract) is never
    # registered under this slug in ingestion-registry.json, so the absence of
    # an entry is the NORMAL case for that path — not a "skip".
    #
    # We now emit an explicit gap. word_count / previous_word_count /
    # delta_start_word are None (not 0), so the renderer shows "n/a" instead of
    # a fabricated measurement.
    return {
        "action": "NO_REGISTRY_ENTRY",
        "reason": (
            "no ingestion-registry entry for this slug — guard verdict was not "
            "recorded (e.g. document chunked via ephemeral temp, not "
            "registered under slug). Counts unavailable, not measured."
        ),
        "identity_key": slug,
        "body_hash": (sidecar.get("transcript_hash", "") if sidecar else ""),
        "word_count": None,
        "previous_word_count": None,
        "delta_start_word": None,
    }


def _load_download_extract_from_disk(slug: str) -> dict:
    """STEP 02 — load download/extract from sidecar + transcription-meta.

    Bug-fix MCE-16.5: sidecar.transcript_sidecar may point to inbox/ even after
    lifecycle move.  We resolve to processed/ as well so word_count is non-zero.
    Also adds sidecar.transcript_path as a secondary field name.
    """
    sidecar = _find_sidecar_for_slug(slug)
    if not sidecar:
        return {}

    transcript_path = sidecar.get("transcript_sidecar", "") or sidecar.get("transcript_path", "")

    trans_meta: dict = {}
    if transcript_path:
        tp = Path(transcript_path)
        meta_candidate = tp.with_suffix(tp.suffix + ".transcription-meta.json")
        if meta_candidate.exists():
            try:
                trans_meta = json.loads(meta_candidate.read_text(encoding="utf-8"))
            except Exception:
                pass

    # Word count: resolve path, fallback inbox→processed on lifecycle-moved files
    word_count = 0
    if transcript_path:
        tp = Path(transcript_path)
        if not tp.is_absolute():
            tp = ROOT / transcript_path
        # If path doesn't exist, try swapping inbox→processed (lifecycle move)
        if not tp.exists():
            tp_alt = Path(str(tp).replace(
                "/knowledge/external/inbox/", "/knowledge/external/processed/"
            ).replace(
                "/knowledge/business/inbox/", "/knowledge/business/processed/"
            ))
            if tp_alt.exists():
                tp = tp_alt
        if tp.exists():
            try:
                content = tp.read_text(encoding="utf-8", errors="ignore")
                word_count = len(content.split())
            except Exception:
                pass

    if word_count == 0:
        word_count = trans_meta.get("word_count") or sidecar.get("word_count") or 0

    return {
        "tier": sidecar.get("transcript_extracted_via", "unknown"),
        "provider": (
            trans_meta.get("provider")
            or sidecar.get("fallback_source")
            or sidecar.get("transcript_extracted_via", "unknown")
        ),
        "duration_seconds": trans_meta.get("duration_seconds", 0),
        "word_count": word_count,
        "transcript_path": transcript_path,
        "quality_score": trans_meta.get("quality_score", "N/A"),
    }


def _load_speaker_visual_gate_from_disk(slug: str) -> dict:
    """STEP 03 — load speaker visual gate from sidecar."""
    sidecar = _find_sidecar_for_slug(slug)
    if not sidecar:
        return {}

    speakers = sidecar.get("gemini_speakers", []) or []
    primary_speaker = speakers[0] if speakers else {}

    return {
        "bypassed": not sidecar.get("gemini_used", False),
        "bypass_reason": sidecar.get("gemini_bypassed_reason", ""),
        "speaker": primary_speaker.get("name", "") if isinstance(primary_speaker, dict) else "",
        "subject": (
            sidecar.get("decision", {}).get("entity_subject", "")
            or sidecar.get("decision", {}).get("entity_author", "")
        ),
        "confidence": primary_speaker.get("confidence", "") if isinstance(primary_speaker, dict) else "",
        "model": "gemini-2.0-flash" if sidecar.get("gemini_used") else "n/a",
    }


def _load_entity_discovery_from_disk(slug: str) -> dict:
    """STEP 04 — load entity discovery from sidecar."""
    sidecar = _find_sidecar_for_slug(slug)
    if not sidecar:
        return {}

    decision = sidecar.get("decision", {})
    filename_evidence = decision.get("evidence", {}).get("filename", {}) if isinstance(decision, dict) else {}

    return {
        "decision": decision.get("verdict", "UNKNOWN") if isinstance(decision, dict) else "UNKNOWN",
        "slug_final": decision.get("entity_author", slug) if isinstance(decision, dict) else slug,
        "bucket_final": _resolve_bucket_for_slug(slug),
        "gemini_used": sidecar.get("gemini_used", False),
        "filename_original": sidecar.get("original_filename", ""),
        "tokens_dropped": filename_evidence.get("noise", []) if isinstance(filename_evidence, dict) else [],
    }


def _load_filename_sidecar_from_disk(slug: str) -> dict:
    """STEP 05 — verify sidecar exists, return metadata."""
    candidates = [
        ROOT / "knowledge" / "external" / "processed" / slug,
        ROOT / "knowledge" / "external" / "inbox" / slug,
        ROOT / "knowledge" / "business" / "processed" / slug,
        ROOT / "knowledge" / "business" / "inbox" / slug,
        ROOT / "knowledge" / "personal" / "processed" / slug,
    ]

    for base in candidates:
        if not base.exists():
            continue
        for f in base.rglob("*.entity-discovery.json"):
            try:
                content = json.loads(f.read_text(encoding="utf-8"))
                return {
                    "sidecar_path": str(f.relative_to(ROOT)),
                    "schema_version": content.get("schema_version", "unknown"),
                    "written": True,
                    "fields_count": len(content.keys()),
                }
            except Exception:
                continue
    return {}


def _load_classification_from_disk(slug: str) -> dict:
    """STEP 06 — Atlas classification from sidecar + filesystem bucket."""
    sidecar = _find_sidecar_for_slug(slug)
    bucket = _resolve_bucket_for_slug(slug)

    confidence_str = ""
    if sidecar:
        decision = sidecar.get("decision", {})
        if isinstance(decision, dict):
            confidence_str = decision.get("confidence", "")

    confidence_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
    confidence = confidence_map.get(str(confidence_str).lower(), 0.5)

    return {
        "bucket": bucket,
        "confidence": confidence,
        "secondary_bucket": "none",
        "method": "sidecar_fallback",
    }


def _load_bucket_selection_from_disk(slug: str) -> dict:
    """Bucket de Selecao (pre-00) — load sidecar + ROLE-TRACKING.

    Story: MCE-16.4
    """
    import json

    sidecar = _find_sidecar_for_slug(slug)
    bucket = _resolve_bucket_for_slug(slug)

    # ROLE-TRACKING.json — proxy de atlas classification (domains)
    # Delegated to role_tracker_reader (Story MCE-17.0 Fase 2 T8).
    domains: list[str] = []
    try:
        if _HAS_ROLE_TRACKER_READER:
            _rt = _rt_load(ROOT / ".data" / "artifacts" / "ROLE-TRACKING.json")
            _slug_entry = _rt_find_person(_rt, slug) or {}
        else:
            _rt_raw = json.loads(
                (ROOT / ".data" / "artifacts" / "ROLE-TRACKING.json").read_text(
                    encoding="utf-8"
                )
            )
            _persons = _rt_raw.get("persons", []) if isinstance(_rt_raw, dict) else []
            _slug_entry = next(
                (p for p in _persons if isinstance(p, dict) and p.get("slug") == slug),
                {},
            )
        domains = list(_slug_entry.get("domains") or [])
    except Exception:
        pass

    if not sidecar:
        return {
            "original_filename": "",
            "source_url": "",
            "source_kind": "unknown",
            "verdict": "UNKNOWN",
            "confidence": "",
            "routing_reason": "",
            "cross_references": [],
            "domains": domains,
            "atlas_confidence": 0.9 if domains else 0.0,
            "bucket": bucket,
            "slug": slug,
            "destination": str(
                (ROOT / "knowledge" / bucket / "processed" / slug).relative_to(ROOT)
            ),
            "method": "disk_fallback",
        }

    decision = sidecar.get("decision", {}) or {}
    source_url = sidecar.get("source_url") or sidecar.get("url") or ""
    source_kind = (
        "youtube"
        if "youtube" in source_url.lower() or sidecar.get("gemini_used")
        else "file"
    )

    return {
        "original_filename": sidecar.get("original_filename", ""),
        "source_url": source_url,
        "source_kind": source_kind,
        "verdict": decision.get("verdict", "UNKNOWN"),
        "confidence": decision.get("confidence", ""),
        "routing_reason": (
            decision.get("evidence", {}).get("rationale", "")
            or "filename_evidence"
        ),
        "cross_references": (
            decision.get("evidence", {})
            .get("filename", {})
            .get("noise", [])[:5]
        ),
        "domains": domains,
        "atlas_confidence": 0.9 if domains else 0.0,
        "bucket": bucket,
        "slug": slug,
        "destination": str(
            (ROOT / "knowledge" / bucket / "processed" / slug).relative_to(ROOT)
        ),
        "method": "sidecar+role_tracking",
    }


def _load_cascade_tree_from_disk(slug: str) -> dict:
    """Arvore de Cascateamento (post-44) — load role-tracker + dossiers + solos.

    Story: MCE-16.4
    """
    import json

    bucket = _resolve_bucket_for_slug(slug)

    # ROLE-TRACKER — delegated to role_tracker_reader (Story MCE-17.0 Fase 2 T8).
    domains: list[str] = []
    domain_expert_counts: dict[str, int] = {}

    try:
        if _HAS_ROLE_TRACKER_READER:
            _rt2 = _rt_load(ROOT / ".data" / "artifacts" / "ROLE-TRACKING.json")
            _all_persons = _rt_iter_persons(_rt2)
            _slug_entry2 = _rt_find_person(_rt2, slug) or {}
        else:
            _rt2_raw = json.loads(
                (ROOT / ".data" / "artifacts" / "ROLE-TRACKING.json").read_text(
                    encoding="utf-8"
                )
            )
            _all_persons = (
                _rt2_raw.get("persons", []) if isinstance(_rt2_raw, dict) else []
            )
            _slug_entry2 = next(
                (
                    p
                    for p in _all_persons
                    if isinstance(p, dict) and p.get("slug") == slug
                ),
                {},
            )
        domains = list(_slug_entry2.get("domains") or [])
        # Count experts per domain by scanning ALL persons entries
        for e_other in _all_persons:
            if not isinstance(e_other, dict):
                continue
            for d in e_other.get("domains") or []:
                domain_expert_counts[d] = domain_expert_counts.get(d, 0) + 1
    except Exception:
        pass

    # THEME DOSSIERS (B) — grep body for slug
    themes_dir = ROOT / "knowledge" / "external" / "dossiers" / "themes"
    theme_dossiers: list[str] = []
    if themes_dir.exists():
        for md in sorted(themes_dir.glob("*.md")):
            try:
                if slug.lower() in md.read_text(encoding="utf-8").lower():
                    theme_dossiers.append(md.name)
            except Exception:
                continue

    # SOLOS P x TEMA (C)
    solos_dir = ROOT / "knowledge" / "external" / "dossiers" / "persons-by-theme"
    person_solos: list[str] = []
    if solos_dir.exists():
        person_solos = sorted([p.name for p in solos_dir.glob(f"{slug}--*.md")])

    return {
        "domains": domains,
        "domain_expert_counts": {
            d: domain_expert_counts.get(d, 1) for d in domains
        },
        "bucket": bucket,
        "slug": slug,
        "theme_dossiers": theme_dossiers,
        "theme_count": len(theme_dossiers),
        "person_solos": person_solos,
        "solos_count": len(person_solos),
    }


def _load_organization_routing_from_disk(slug: str) -> dict:
    """STEP 07 — load organization + routing via filesystem glob."""
    import yaml as _yaml_org

    bucket = _resolve_bucket_for_slug(slug)

    destinations = [
        ROOT / "knowledge" / bucket / "processed" / slug,
        ROOT / "knowledge" / bucket / "inbox" / slug,
    ]

    destination = ""
    files_organized = 0
    for d in destinations:
        if d.exists():
            destination = str(d.relative_to(ROOT))
            files_organized = sum(1 for _ in d.rglob("*") if _.is_file())
            break

    # source_registered via metadata.yaml
    source_registered = False
    metadata_path = ROOT / ".claude" / "mission-control" / "mce" / slug / "metadata.yaml"
    if metadata_path.exists():
        try:
            meta = _yaml_org.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
            sources = meta.get("sources_processed") or []
            source_registered = bool(sources)
        except Exception:
            pass

    return {
        "action": "moved" if destination else "unknown",
        "destination": destination,
        "files_organized": files_organized,
        "source_registered": source_registered,
    }


def _load_batch_creation_from_disk(slug: str) -> dict:
    """STEP 08 — batch creation from metadata.yaml.

    Bug-fix MCE-16.5: batch_id lives in phases_completed.process_batch (not
    batch_creation).  chunks count also comes from process_batch.
    """
    import yaml as _yaml_batch

    metadata_path = ROOT / ".claude" / "mission-control" / "mce" / slug / "metadata.yaml"
    if not metadata_path.exists():
        return {}

    try:
        meta = _yaml_batch.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

    phases = meta.get("phases_completed") or {}
    batch_phase = phases.get("batch_creation") or {}
    process_phase = phases.get("process_batch") or {}  # batch_id is HERE

    all_batches = batch_phase.get("all_batches") or []

    return {
        # batch_id comes from process_batch, not batch_creation
        "batch_id": process_phase.get("batch_id", ""),
        "chunks_count": process_phase.get("chunks", 0),
        "batch_index": 1,
        "total_batches": (
            batch_phase.get("batches_created")
            or (len(all_batches) if isinstance(all_batches, list) else 1)
            or 1
        ),
        "state": "completed" if batch_phase.get("completed") else "in_progress",
    }


def _honest_chunk_strategy() -> str:
    """Real chunking strategy label for the ingest path (Onda 0).

    Pulls the label from the code that pins it
    (``rag.chunker.INGEST_PATH_CHUNK_STRATEGY``) instead of asserting
    "semantic". Lazy import + fail-open so log generation never crashes on this.
    """
    try:
        # Prefer the dynamic resolver so the log reflects the LIVE
        # MCE_SEMANTIC_CHUNK_ENABLED state (feature A). Fall back to the legacy
        # constant for older chunker modules.
        from engine.intelligence.rag import chunker as _chunker

        fn = getattr(_chunker, "ingest_path_chunk_strategy", None)
        if callable(fn):
            return fn()
        return _chunker.INGEST_PATH_CHUNK_STRATEGY
    except Exception:
        return "unknown (strategy label unavailable)"


def _load_chunking_from_disk(slug: str) -> dict:
    """STEP 09 — chunking from .data/artifacts/chunks/{slug}/BATCH-*-chunks.json.

    Bug-fix MCE-16.5: dedup batches by content hash before summing so that
    duplicate batch files (e.g. BATCH-2603-CG and BATCH-2823-CG with identical
    content) are counted only once.
    """
    import hashlib

    chunks_dir = ROOT / ".data" / "artifacts" / "chunks" / slug
    if not chunks_dir.exists():
        return {}

    seen_hashes: set[str] = set()
    total_chunks = 0
    word_counts: list[int] = []
    duplicates_skipped = 0
    batch_strategy: str | None = None

    for chunk_file in sorted(chunks_dir.glob("BATCH-*-chunks.json")):
        try:
            data = json.loads(chunk_file.read_text(encoding="utf-8"))
            chunks = data.get("chunks", [])

            # Onda 0: capture a real strategy label if the batch recorded one.
            if batch_strategy is None and data.get("strategy"):
                batch_strategy = str(data["strategy"])

            # Hash the combined text of this batch to detect byte-level duplicates
            combined = "".join(
                c.get("text", "") for c in chunks if isinstance(c, dict)
            )
            batch_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()

            if batch_hash in seen_hashes:
                duplicates_skipped += 1
                continue
            seen_hashes.add(batch_hash)

            total_chunks += data.get("count", len(chunks))
            for c in chunks:
                text = c.get("text", "") if isinstance(c, dict) else ""
                if text:
                    word_counts.append(len(text.split()))
        except Exception:
            continue

    # Onda 0 honesty: never hardcode "semantic". Use the real strategy recorded
    # in the batch if present, otherwise the honest ingest-path constant
    # (recursive/size-based, semantic=False).
    strategy = batch_strategy or _honest_chunk_strategy()

    if not word_counts:
        return {
            "total_chunks": total_chunks,
            "avg_words_per_chunk": 0,
            "min_words": 0,
            "max_words": 0,
            "strategy": strategy,
            "duplicates_skipped": duplicates_skipped,
        }

    return {
        "total_chunks": total_chunks,
        "avg_words_per_chunk": round(sum(word_counts) / len(word_counts), 1),
        "min_words": min(word_counts),
        "max_words": max(word_counts),
        "strategy": strategy,
        "duplicates_skipped": duplicates_skipped,
    }


def _load_embeddings_from_disk(slug: str) -> dict:
    """STEP 10 — embeddings from .data/artifacts/embeddings/{slug}/BATCH-*-embeddings.json."""
    embeddings_dir = ROOT / ".data" / "artifacts" / "embeddings" / slug
    if not embeddings_dir.exists():
        return {}

    chunks_embedded = 0
    model = ""

    for emb_file in embeddings_dir.glob("BATCH-*-embeddings.json"):
        try:
            data = json.loads(emb_file.read_text(encoding="utf-8"))
            chunks_embedded += data.get("count", 0)
            if not model:
                model = data.get("embedding_model", "")
        except Exception:
            continue

    return {
        "chunks_embedded": chunks_embedded,
        "model": model or "text-embedding-3-large",
        "dimensions": 1536,
        "tokens_used": 0,
        "cost_usd": 0.0,
        "duration_ms": 0,
    }


def _load_entity_resolution_from_disk(slug: str) -> dict:
    """STEP 11 — entity resolution from CANONICAL-MAP.json."""
    cmap_path = ROOT / ".data" / "artifacts" / "mce" / slug / "CANONICAL-MAP.json"
    if not cmap_path.exists():
        # Try alternative location used by entity_resolver
        cmap_path = ROOT / ".data" / "artifacts" / "canonical" / slug / "CANONICAL-MAP.json"

    if not cmap_path.exists():
        return {}

    try:
        data = json.loads(cmap_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    entities_this_run = data.get("entities_this_run") or data.get("entities") or {}
    if isinstance(entities_this_run, dict):
        total_entities = len(entities_this_run)
        persons_resolved = sum(
            1 for v in entities_this_run.values()
            if isinstance(v, dict) and v.get("type") == "person"
        )
    elif isinstance(entities_this_run, list):
        total_entities = len(entities_this_run)
        persons_resolved = sum(
            1 for v in entities_this_run
            if isinstance(v, dict) and v.get("type") == "person"
        )
    else:
        total_entities = 0
        persons_resolved = 0

    aliases_merged = data.get("new_entities_added_to_global") or len(data.get("aliases", {}) or {})

    return {
        "total_entities": total_entities,
        "canonical_map_path": str(cmap_path.relative_to(ROOT)),
        "persons_resolved": persons_resolved,
        "aliases_merged": aliases_merged,
    }


# ─── DISK-FALLBACK LOADERS FOR STEPs 25-28, 33, 37-38 (MCE-16.5) ────────────


def _load_memory_enrichment_from_disk(slug: str) -> dict:
    """STEP 25 — memory.md enrichment stats.

    Reads agents/{bucket}/{slug}/memory.md and returns file stats.
    """
    bucket = _resolve_bucket_for_slug(slug)
    memory_path = ROOT / "agents" / bucket / slug / "memory.md"

    if not memory_path.exists():
        return {}

    try:
        content = memory_path.read_text(encoding="utf-8")
        stat = memory_path.stat()
        return {
            "memory_path": str(memory_path.relative_to(ROOT)),
            "size_bytes": stat.st_size,
            "line_count": content.count("\n"),
            "word_count": len(content.split()),
            "last_modified": stat.st_mtime,
        }
    except Exception:
        return {}


def _load_cascading_a_role_tracker_from_disk(slug: str) -> dict:
    """STEP 26 — role-tracker (domains + themes) for slug.

    Delegated to role_tracker_reader (Story MCE-17.0 Fase 2 T8).
    """
    rt_path = ROOT / ".data" / "artifacts" / "ROLE-TRACKING.json"
    if not rt_path.exists():
        return {}

    try:
        if _HAS_ROLE_TRACKER_READER:
            rt = _rt_load(rt_path)
            slug_entry = _rt_find_person(rt, slug) or {}
        else:
            raw = json.loads(rt_path.read_text(encoding="utf-8"))
            persons = raw.get("persons", []) if isinstance(raw, dict) else []
            slug_entry = next(
                (p for p in persons if isinstance(p, dict) and p.get("slug") == slug),
                {},
            )

        domains = slug_entry.get("domains") or []
        themes = slug_entry.get("themes") or []
        return {
            # MCE-17.x STEP 26 fix: renderer (_step_26_cascading_a) reads
            # domains_updated / themes_tracked / cargo_agents_updated. Add these
            # renderer-compatible keys; disk fallback has no cargo signal → 0.
            "domains_updated": len(domains),
            "themes_tracked": len(themes),
            "cargo_agents_updated": 0,
            # Legacy fields preserved for backward compat.
            "domains": list(domains),
            "themes": list(themes),
            "domain_count": len(domains),
            "theme_count": len(themes),
            "last_updated": slug_entry.get("last_updated", ""),
        }
    except Exception:
        return {}


def _load_cascading_b_theme_dossiers_from_disk(slug: str) -> dict:
    """STEP 27 — count theme dossiers that mention slug.

    Scans knowledge/external/dossiers/themes/*.md for slug occurrence.
    """
    themes_dir = ROOT / "knowledge" / "external" / "dossiers" / "themes"
    if not themes_dir.exists():
        return {}

    matched: list[str] = []
    for md in sorted(themes_dir.glob("*.md")):
        try:
            if slug.lower() in md.read_text(encoding="utf-8", errors="ignore").lower():
                matched.append(md.name)
        except Exception:
            continue

    return {
        "theme_dossiers_count": len(matched),
        "theme_dossiers": matched[:10],
        "total_themes_in_system": len(list(themes_dir.glob("*.md"))),
    }


def _load_cascading_c_solos_from_disk(slug: str) -> dict:
    """STEP 28 — solos P x Tema for slug.

    Scans knowledge/external/dossiers/persons-by-theme/{slug}--*.md.
    """
    solos_dir = ROOT / "knowledge" / "external" / "dossiers" / "persons-by-theme"
    if not solos_dir.exists():
        return {}

    solos = sorted([p.name for p in solos_dir.glob(f"{slug}--*.md")])
    _themes_list = [
        s.replace(f"{slug}--", "").replace(".md", "") for s in solos
    ]

    return {
        # MCE-17.x STEP 28 fix: renderer (_step_28_cascading_c) reads
        # solos_written / persons_covered / themes_covered (as a COUNT). This
        # single-slug loader covers exactly 1 person when solos exist. The list
        # of theme names is preserved under themes_covered_list to avoid type
        # breakage (renderer prints themes_covered directly as a number).
        "solos_written": len(solos),
        "persons_covered": 1 if solos else 0,
        "themes_covered": len(_themes_list),
        "themes_covered_list": _themes_list,
        # Legacy fields preserved for backward compat.
        "solos_count": len(solos),
        "solos": solos[:10],
    }


def _load_workspace_sync_from_disk(slug: str) -> dict:
    """STEP 33 — workspace sync status (last write to workspace mentioning slug).

    Scans workspace/businesses/*/L3-L4 YAML files for slug mentions.

    MCE-17.2 P6: returns schema matching _step_33_workspace_sync renderer
    (synced, items_written, layers_touched) instead of legacy disk keys.
    """
    workspace_dir = ROOT / "workspace"
    if not workspace_dir.exists():
        return {}

    candidates = (
        list(workspace_dir.glob("businesses/*/L4-operational/*.yaml"))
        + list(workspace_dir.glob("businesses/*/L3-product/*.yaml"))
    )

    last_sync: float = 0
    bus_touched: set[str] = set()
    layers_seen: list[str] = []
    slug_lower = slug.lower()
    slug_underscore = slug.replace("-", "_").lower()

    for f in candidates:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if slug_lower in content.lower() or slug_underscore in content.lower():
                stat = f.stat()
                if stat.st_mtime > last_sync:
                    last_sync = stat.st_mtime
                parts = f.relative_to(workspace_dir).parts
                if len(parts) >= 2:
                    bus_touched.add(parts[1])
                # Collect layer names (e.g., "L3-product", "L4-operational")
                for part in parts:
                    if part.startswith("L") and "-" in part and part not in layers_seen:
                        layers_seen.append(part)
        except Exception:
            continue

    return {
        # Renderer-compatible keys (_step_33_workspace_sync reads these)
        "synced": len(bus_touched),
        "items_written": len(bus_touched),
        "layers_touched": layers_seen,
        # Legacy fields preserved for backward compat
        "sync_status": "synced" if bus_touched else "not_synced",
        "bus_count": len(bus_touched),
        "bus_list": sorted(bus_touched),
        "last_sync_epoch": last_sync,
    }


def _load_lifecycle_move_from_disk(slug: str) -> dict:
    """STEP 37 — lifecycle move verification.

    Checks whether files for slug have been moved from inbox/ to processed/.
    """
    bucket = _resolve_bucket_for_slug(slug)

    inbox_dir = ROOT / "knowledge" / bucket / "inbox" / slug
    processed_dir = ROOT / "knowledge" / bucket / "processed" / slug

    in_inbox = (
        sum(1 for f in inbox_dir.rglob("*") if f.is_file())
        if inbox_dir.exists()
        else 0
    )
    in_processed = (
        sum(1 for f in processed_dir.rglob("*") if f.is_file())
        if processed_dir.exists()
        else 0
    )

    if in_processed > 0 and in_inbox == 0:
        status = "moved"
    elif in_processed > 0 and in_inbox > 0:
        status = "partial_move"
    elif in_inbox > 0:
        status = "still_in_inbox"
    else:
        status = "no_files"

    return {
        "status": status,
        "files_in_inbox": in_inbox,
        "files_in_processed": in_processed,
        "inbox_path": (
            str(inbox_dir.relative_to(ROOT)) if inbox_dir.exists() else ""
        ),
        "processed_path": (
            str(processed_dir.relative_to(ROOT)) if processed_dir.exists() else ""
        ),
    }


def _load_batch_history_from_disk(slug: str) -> dict:
    """STEP 38 — last batch history entry for slug.

    Reads .data/artifacts/BATCH-HISTORY.json and returns last entry for slug.
    Handles both list-root and dict-root formats of BATCH-HISTORY.json.
    """
    bh_path = ROOT / ".data" / "artifacts" / "BATCH-HISTORY.json"
    if not bh_path.exists():
        return {}

    try:
        bh = json.loads(bh_path.read_text(encoding="utf-8"))
        # BATCH-HISTORY.json may be a bare list or a dict with entries/runs key
        if isinstance(bh, list):
            entries: list = bh
        elif isinstance(bh, dict):
            entries = bh.get("entries") or bh.get("runs") or []
        else:
            entries = []

        slug_entries = [
            e for e in entries if isinstance(e, dict) and e.get("slug") == slug
        ]
        if not slug_entries:
            # MCE-17.x STEP 38 fix: renderer reads batch_id / entries_total /
            # appended. Return renderer-compatible empty shape (keep legacy keys).
            return {
                "batch_id": "",
                "entries_total": 0,
                "appended": False,
                "total_runs": 0,
                "last_run": None,
            }

        last = slug_entries[-1]
        return {
            # MCE-17.x STEP 38 fix: renderer-compatible keys.
            "batch_id": last.get("run_id") or last.get("batch_id", ""),
            "entries_total": len(slug_entries),
            "appended": True,
            # Legacy fields preserved for backward compat.
            "total_runs": len(slug_entries),
            "last_run_id": last.get("run_id") or last.get("batch_id", ""),
            "last_timestamp": last.get("timestamp", ""),
            "last_status": last.get("status", ""),
        }
    except Exception:
        return {}


# ─── FAIL_NO_DATA HELPER (MCE-17.0 T10) ─────────────────────────────────────


def _is_fail_no_data(data: dict[str, Any]) -> bool:
    """Return True when data carries a FAIL_NO_DATA sentinel from _with_disk_fallback.

    Used by all 21 renderers that are wrapped in _with_disk_fallback so they
    can render an explicit failure instead of silently falling through to the
    'no data' branch which renders _(secao sem dados)_.

    Story: MCE-17.0 T10
    """
    return bool(data and data.get("_step_status") == "FAIL_NO_DATA")


def _fail_no_data_box(step_name: str) -> list[str]:
    """Build the box lines for an explicit FAIL_NO_DATA step.

    Preserves layout: same ┌──┐ inner box used by all renderers.
    Only the content changes — structure (╔══╗ + ┌──┐ + ╚══╝) is unchanged.

    Story: MCE-17.0 T10
    """
    return [
        _V3_FAIL_NO_DATA,
        "",
        f"  Passo: {step_name}",
        "  Causa: stream vivo nao emitiu dados para este template_id.",
        "  Acao:  fallback de disco desabilitado (MCE_NO_FALLBACK=1).",
        "  Fix:   produtor em orchestrate.py precisa emitir o template_id correto.",
    ]


# ─── 44 STEP RENDERERS ──────────────────────────────────────────────────────


def _step_00_source_discovery(data: dict[str, Any]) -> list[str]:
    """STEP 00 — SOURCE DISCOVERY: where did the material come from."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 00 — SOURCE DISCOVERY")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Toda execucao de pipeline precisa rastrear a origem do material.",
            "  Sem isso, nao e possivel auditar duplicatas, calcular deltas ou",
            "  creditar a fonte correta no dossier gerado.",
        ]
    else:
        source_path = str(data.get("source_path", "(nao disponivel)"))[:70]
        source_type = str(data.get("source_type", "(nao disponivel)"))
        bucket = str(data.get("bucket", "(nao disponivel)"))
        slug_val = str(data.get("slug", "(nao disponivel)"))
        discovered_at = str(data.get("discovered_at", "(nao disponivel)"))[:25]
        box = [
            f"Fonte:         {source_path}",
            f"Tipo:          {source_type}",
            f"Bucket:        {bucket}",
            f"Slug:          {slug_val}",
            f"Descoberto em: {discovered_at}",
            "",
            "Por que esse passo existe?",
            "  Rastrear a origem e o primeiro elo da cadeia de custódia do",
            "  conhecimento. Sem proveniencia, nao ha auditabilidade.",
        ]
    return _v3_step(0, "\U0001f50e", "SOURCE DISCOVERY", box)


def _step_01_ingestion_guard(data: dict[str, Any]) -> list[str]:
    """STEP 01 — INGESTION GUARD: anti-duplicate Phase 0."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 01 — INGESTION GUARD")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "O que aconteceria sem esse passo?",
            "  O mesmo material seria processado multiplas vezes, gerando",
            "  duplicatas nos insights, tokens de LLM desperdicados e",
            "  contaminacao de MEMORY.md com dados repetidos.",
        ]
    else:
        action = str(data.get("action", "UNKNOWN")).upper()
        reason = str(data.get("reason", "(sem motivo)"))[:55]
        identity_key = str(data.get("identity_key", "(ausente)"))[:40]
        body_hash_full = str(data.get("body_hash", ""))
        body_hash = body_hash_full[:16] + "..." if len(body_hash_full) > 16 else body_hash_full

        # Onda 0 honesty: counts may be None when no registry entry was
        # recorded. Render "n/a" — never coerce an unmeasured value to 0, which
        # would read as a real measurement.
        def _wc(v: Any) -> str:
            return "n/a" if v is None else str(v)

        word_count = _wc(data.get("word_count"))
        prev_wc = _wc(data.get("previous_word_count"))
        delta = _wc(data.get("delta_start_word"))
        verdict_icon = {
            "SKIP": "⏭️",
            "PROCESS": "✅",
            "INCREMENTAL": "\U0001f504",
            "NO_REGISTRY_ENTRY": "⚠️",
        }.get(action, "❓")
        box = [
            f"Verdict:       {verdict_icon} {action}",
            f"Motivo:        {reason}",
            "",
            f"Identity key:  {identity_key}",
            f"Body hash:     {body_hash}",
            "",
            f"Word count:    {word_count}",
            f"Prev count:    {prev_wc}",
            f"Delta:         {delta}",
            "",
            "O que aconteceria se fosse DUPLICATA?",
            "  Pipeline pararia aqui com verdict=SKIP. Zero custo de LLM.",
            "  Nenhum artefato seria regravado. Auditoria registra o skip.",
        ]
    return _v3_step(1, "\U0001f6e1", "INGESTION GUARD", box)


def _step_02_download_extract(data: dict[str, Any]) -> list[str]:
    """STEP 02 — DOWNLOAD/EXTRACT: transcript with 3 tiers."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 02 — DOWNLOAD/EXTRACT")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Como interpretar?",
            "  3 tiers: Tier1=Whisper local, Tier2=Deepgram API,",
            "  Tier3=fallback texto plano. Cada tier tem qualidade",
            "  e custo diferentes. Tier1 e preferido por privacidade.",
        ]
    else:
        tier = data.get("tier", "(nao disponivel)")
        provider = str(data.get("provider", "(nao disponivel)"))
        duration_s = data.get("duration_seconds", 0)
        word_count = data.get("word_count", 0)
        transcript_path = str(data.get("transcript_path", "(nao disponivel)"))[-55:]
        quality = str(data.get("quality_score", "(nao disponivel)"))
        box = [
            f"Tier:          {tier}",
            f"Provider:      {provider}",
            f"Duracao:       {duration_s}s",
            f"Word count:    {word_count}",
            f"Qualidade:     {quality}",
            f"Transcript:    ...{transcript_path}",
            "",
            "Como interpretar?",
            "  Tier1 (Whisper local) = melhor privacidade, custo zero.",
            "  Tier2 (Deepgram) = mais rapido, pago por minuto.",
            "  Tier3 (texto plano) = sem transcricao, apenas texto raw.",
        ]
    return _v3_step(2, "\U0001f4e5", "DOWNLOAD/EXTRACT", box)


def _step_03_speaker_visual_gate(data: dict[str, Any]) -> list[str]:
    """STEP 03 — SPEAKER VISUAL GATE: pre_07 Gemini Vision."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 03 — SPEAKER VISUAL GATE")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  O nome do arquivo nem sempre revela quem esta falando.",
            "  Gemini Vision analisa o video e identifica o speaker",
            "  com contexto visual, reduzindo atribuicoes erradas.",
        ]
    else:
        bypassed = data.get("bypassed", False)
        bypass_reason = str(data.get("bypass_reason", ""))[:50]
        speaker = str(data.get("speaker", "(nao identificado)"))
        subject = str(data.get("subject", "(nao identificado)"))
        confidence = data.get("confidence", 0.0)
        model = str(data.get("model", "gemini-pro-vision"))
        if bypassed:
            status_line = f"Status:        BYPASSED ({bypass_reason})"
        else:
            status_line = f"Status:        PROCESSADO  confianca={confidence:.2f}"
        box = [
            status_line,
            f"Speaker:       {speaker}",
            f"Subject:       {subject}",
            f"Modelo:        {model}",
            "",
            "Por que esse passo existe?",
            "  Sem visual gate, um video de Ryan Deiss ensinando Hormozi",
            "  seria atribuido ao arquivo se chamado 'hormozi-leads.mp4'.",
            "  O gate usa visao computacional para confirmar o speaker.",
        ]
    return _v3_step(3, "\U0001f441", "SPEAKER VISUAL GATE", box)


def _step_04_entity_discovery(data: dict[str, Any]) -> list[str]:
    """STEP 04 — ENTITY DISCOVERY: pre_08 dual reconciliation."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 04 — ENTITY DISCOVERY")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Como interpretar?",
            "  Entity Discovery reconcilia evidencias do nome do arquivo",
            "  com o output do Speaker Visual Gate. Resultado e o slug",
            "  canonico usado em todos os artefatos subsequentes.",
        ]
    else:
        decision = str(data.get("decision", "(nao disponivel)"))
        slug_final = str(data.get("slug_final", "(nao disponivel)"))
        bucket_final = str(data.get("bucket_final", "(nao disponivel)"))
        gemini_used = data.get("gemini_used", False)
        filename_original = str(data.get("filename_original", "(nao disponivel)"))[-50:]
        tokens_dropped = data.get("tokens_dropped", [])
        box = [
            f"Decision:      {decision}",
            f"Slug final:    {slug_final}",
            f"Bucket final:  {bucket_final}",
            f"Gemini usado:  {'Sim' if gemini_used else 'Nao'}",
            f"Arquivo orig:  ...{filename_original}",
            f"Tokens drop:   {', '.join(str(t) for t in tokens_dropped[:4])}",
            "",
            "Como interpretar?",
            "  decision=FILENAME_WINS: nome do arquivo venceu sobre Gemini.",
            "  decision=GEMINI_WINS: visao computacional venceu.",
            "  decision=CONSENSUS: ambos concordaram.",
        ]
    return _v3_step(4, "\U0001f9ec", "ENTITY DISCOVERY", box)


def _step_05_filename_sidecar(data: dict[str, Any]) -> list[str]:
    """STEP 05 — FILENAME SIDECAR WRITE: schema v1.2.0."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 05 — FILENAME SIDECAR WRITE")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "O que aconteceria sem esse arquivo?",
            "  O sidecar e o contrato de identidade do material.",
            "  Sem ele, proximas execucoes nao conseguem detectar",
            "  incrementos nem rastrear proveniencia do slug.",
        ]
    else:
        sidecar_path = str(data.get("sidecar_path", "(nao disponivel)"))[-55:]
        schema_version = str(data.get("schema_version", "v1.2.0"))
        written = data.get("written", False)
        fields_count = data.get("fields_count", 0)
        box = [
            f"Status:        {'ESCRITO' if written else 'NAO ESCRITO'}",
            f"Path:          ...{sidecar_path}",
            f"Schema:        {schema_version}",
            f"Campos:        {fields_count}",
            "",
            "O que aconteceria sem esse arquivo?",
            "  Sidecar = passport do material. Perde rastreabilidade",
            "  entre execucoes. Ingestion Guard nao consegue deduplicar.",
        ]
    return _v3_step(5, "\U0001f4cb", "FILENAME SIDECAR WRITE", box)


def _step_06_classification(data: dict[str, Any]) -> list[str]:
    """STEP 06 — CLASSIFICATION (Atlas): bucket primary."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 06 — CLASSIFICATION (Atlas)")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Atlas classifica o material em external/business/personal.",
            "  Sem classificacao, o bucket errado recebe o material e",
            "  contamina indexes de RAG de outros domínios.",
        ]
    else:
        bucket = str(data.get("bucket", "(nao disponivel)"))
        confidence = data.get("confidence", 0.0)
        secondary = str(data.get("secondary_bucket", "(nenhum)"))
        classif_method = str(data.get("method", "(nao disponivel)"))
        box = [
            f"Bucket:        {bucket}",
            f"Confianca:     {confidence:.2f}",
            f"Secundario:    {secondary}",
            f"Metodo:        {classif_method}",
            "",
            "Como interpretar?",
            "  confidence >= 0.8: classificacao solida.",
            "  confidence < 0.5: Atlas nao tem certeza — revisar manualmente.",
            "  Buckets: external=experts, business=operacional, personal=fundador.",
        ]
    return _v3_step(6, "\U0001f4cc", "CLASSIFICATION (Atlas)", box)


def _step_07_organization_routing(data: dict[str, Any]) -> list[str]:
    """STEP 07 — ORGANIZATION + INBOX ROUTING: final inbox path."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 07 — ORGANIZATION + INBOX ROUTING")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Como interpretar?",
            "  O arquivo fisico e movido para inbox/{bucket}/{slug}/.",
            "  Se organizacao falhou, o arquivo permanece na raiz do",
            "  inbox e pode ser reprocessado na proxima execucao.",
        ]
    else:
        action = str(data.get("action", "(nao disponivel)"))
        destination = str(data.get("destination", "(nao disponivel)"))[-55:]
        files_organized = data.get("files_organized", 0)
        source_registered = data.get("source_registered", False)
        box = [
            f"Acao:          {action}",
            f"Destino:       ...{destination}",
            f"Arquivos:      {files_organized}",
            f"Fonte reg.:    {'Sim' if source_registered else 'Nao'}",
            "",
            "Como interpretar?",
            "  action=moved: arquivo fisicamente realocado para inbox/{bucket}/.",
            "  action=registered: apenas metadado, arquivo nao movido.",
            "  Sem isso, o pipeline perderia o fio da meada entre runs.",
        ]
    return _v3_step(7, "\U0001f4c2", "ORGANIZATION + INBOX ROUTING", box)


def _step_08_batch_creation(data: dict[str, Any]) -> list[str]:
    """STEP 08 — BATCH CREATION: BATCH-NNNN-XX."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 08 — BATCH CREATION")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Batches sao a unidade de processamento paralelo do pipeline.",
            "  Cada batch BATCH-NNNN-XX agrupa chunks relacionados e permite",
            "  retries independentes sem reprocessar o material inteiro.",
        ]
    else:
        batch_id = str(data.get("batch_id", "(nao disponivel)"))
        chunks_in_batch = data.get("chunks_count", 0)
        batch_idx = data.get("batch_index", 0)
        total_batches = data.get("total_batches", 0)
        state = str(data.get("state", "(nao disponivel)"))
        box = [
            f"Batch ID:      {batch_id}",
            f"Estado:        {state}",
            f"Chunks:        {chunks_in_batch}",
            f"Indice:        {batch_idx}/{total_batches}",
            "",
            "Por que esse passo existe?",
            "  Batch = unidade atomica de processamento. Se o LLM falha",
            "  no chunk 47/100, apenas esse batch e retentado.",
            "  BATCH-NNNN-XX: NNNN=numero sequencial, XX=sub-batch index.",
        ]
    return _v3_step(8, "\U0001f4e6", "BATCH CREATION", box)


def _step_09_chunking(data: dict[str, Any]) -> list[str]:
    """STEP 09 — CHUNKING: ~300 words/chunk (strategy reported, not assumed)."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 09 — CHUNKING")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Como interpretar?",
            "  O texto bruto e dividido em chunks de ~300 palavras (a",
            "  estrategia real e reportada no campo Estrategia, nao assumida).",
            "  Chunks menores = mais granularidade no RAG, mas mais tokens.",
            "  Chunks maiores = menos custo, mas contexto mais difuso.",
        ]
    else:
        total_chunks = data.get("total_chunks", 0)
        avg_words = data.get("avg_words_per_chunk", 0)
        min_words = data.get("min_words", 0)
        max_words = data.get("max_words", 0)
        # Onda 0 honesty: fall back to the real ingest-path strategy, never to
        # a hardcoded "semantic".
        strategy = str(data.get("strategy") or _honest_chunk_strategy())
        box = [
            f"Total chunks:  {total_chunks}",
            f"Media palavras:{avg_words}",
            f"Min palavras:  {min_words}",
            f"Max palavras:  {max_words}",
            f"Estrategia:    {strategy}",
            "",
            "Como interpretar?",
            "  Target: ~300 palavras/chunk (janela de contexto ideal para RAG).",
            "  avg_words muito alto: chunks grandes, RAG menos preciso.",
            "  avg_words muito baixo: muitos chunks, custo de embedding alto.",
        ]
    return _v3_step(9, "✂️", "CHUNKING", box)


def _step_10_embeddings(data: dict[str, Any]) -> list[str]:
    """STEP 10 — EMBEDDINGS GENERATION: OpenAI text-emb-3-large."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 10 — EMBEDDINGS GENERATION")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Embeddings convertem texto em vetores matematicos.",
            "  Sao a base do RAG: sem eles, busca semantica e impossivel.",
            "  Modelo: text-embedding-3-large (1536 dimensoes).",
        ]
    else:
        chunks_embedded = data.get("chunks_embedded", 0)
        model = str(data.get("model", "text-embedding-3-large"))
        dimensions = data.get("dimensions", 1536)
        tokens_used = data.get("tokens_used", 0)
        cost_usd = data.get("cost_usd", 0.0)
        duration_ms = data.get("duration_ms", 0)
        box = [
            f"Chunks emb.:   {chunks_embedded}",
            f"Modelo:        {model}",
            f"Dimensoes:     {dimensions}",
            f"Tokens:        {tokens_used:,}",
            f"Custo:         ${cost_usd:.6f}",
            f"Duracao:       {duration_ms}ms",
            "",
            "Como interpretar?",
            "  1536d = 1536 numeros por chunk descrevendo seu significado.",
            "  text-embedding-3-large e o modelo canonico (ADR-embedding-01).",
        ]
    return _v3_step(10, "\U0001f9ee", "EMBEDDINGS GENERATION", box)


def _step_11_entity_resolution(data: dict[str, Any]) -> list[str]:
    """STEP 11 — ENTITY RESOLUTION: CANONICAL-MAP (Sage)."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 11 — ENTITY RESOLUTION")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "O que aconteceria sem esse passo?",
            "  'Alex Hormozi', 'Hormozi' e 'Alex H.' seriam tratados como",
            "  3 pessoas diferentes. Insights ficam fragmentados e o",
            "  CANONICAL-MAP nunca converge em identidades unicas.",
        ]
    else:
        total_entities = data.get("total_entities", 0)
        canonical_map_path = str(data.get("canonical_map_path", "(nao disponivel)"))[-50:]
        persons_resolved = data.get("persons_resolved", 0)
        aliases_merged = data.get("aliases_merged", 0)
        box = [
            f"Total entidades: {total_entities}",
            f"Pessoas:         {persons_resolved}",
            f"Aliases fundidos:{aliases_merged}",
            f"CANONICAL-MAP: ...{canonical_map_path}",
            "",
            "O que aconteceria sem esse passo?",
            "  Alias explosion: 1 pessoa vira N entidades. O grafo de",
            "  conhecimento fica fragmentado. RAG retorna resultados",
            "  contraditórios para o mesmo especialista.",
        ]
    return _v3_step(11, "\U0001f9e9", "ENTITY RESOLUTION", box)


def _step_12_dna_l1(data: dict[str, Any]) -> list[str]:
    """STEP 12 — DNA L1 FILOSOFIAS: extraction."""
    count = data.get("count", 0) if data else 0
    sample = (data.get("samples") or [])[:3] if data else []
    if not data or count == 0:
        box = [
            _V3_NO_DATA if not data else "0 filosofias extraidas nesta execucao.",
            "",
            "O que e L1 Filosofias?",
            "  Crencas fundamentais que guiam todas as decisoes do especialista.",
            "  Exemplo: 'Volume resolve tudo' (Hormozi) ou",
            "  'Sem processo, nao ha escala' (Gerber).",
        ]
    else:
        box = [
            f"Contagem:      {count} filosofias extraidas",
            "",
        ]
        for i, s in enumerate(sample, 1):
            quote = str(s.get("quote", s) if isinstance(s, dict) else s)[:65]
            box.append(f"  {i}. \"{quote}\"")
        box += [
            "",
            "O que e L1 Filosofias?",
            "  Crencas fundamentais que guiam todas as decisoes do especialista.",
            "  Sao o nucleo do DNA cognitivo — as premissas que nao mudam.",
        ]
    return _v3_step(12, "\U0001f9e0", "DNA L1 FILOSOFIAS", box)


def _step_13_dna_l2(data: dict[str, Any]) -> list[str]:
    """STEP 13 — DNA L2 MODELOS MENTAIS: extraction."""
    count = data.get("count", 0) if data else 0
    sample = (data.get("samples") or [])[:3] if data else []
    if not data or count == 0:
        box = [
            _V3_NO_DATA if not data else "0 modelos mentais extraidos nesta execucao.",
            "",
            "O que e L2 Modelos Mentais?",
            "  Frameworks cognitivos para interpretar situacoes.',",
            "  Exemplo: 'Pensamento de sistemas' ou 'Regra dos 80/20'.",
        ]
    else:
        box = [f"Contagem:      {count} modelos mentais", ""]
        for i, s in enumerate(sample, 1):
            quote = str(s.get("quote", s) if isinstance(s, dict) else s)[:65]
            box.append(f"  {i}. \"{quote}\"")
        box += ["", "O que e L2?  Frameworks cognitivos para leitura de situacoes."]
    return _v3_step(13, "\U0001f9e9", "DNA L2 MODELOS MENTAIS", box)


def _step_14_dna_l3(data: dict[str, Any]) -> list[str]:
    """STEP 14 — DNA L3 HEURISTICAS: extraction."""
    count = data.get("count", 0) if data else 0
    sample = (data.get("samples") or [])[:3] if data else []
    if not data or count == 0:
        box = [
            _V3_NO_DATA if not data else "0 heuristicas extraidas nesta execucao.",
            "",
            "O que e L3 Heuristicas?",
            "  Regras praticas com numeros: 'Se LTV < 3x CAC, pausar ads'.",
            "  E o tipo MAIS VALIOSO de DNA — acionavel imediatamente.",
        ]
    else:
        box = [f"Contagem:      {count} heuristicas  *** MAIS VALIOSO ***", ""]
        for i, s in enumerate(sample, 1):
            quote = str(s.get("quote", s) if isinstance(s, dict) else s)[:65]
            box.append(f"  {i}. \"{quote}\"")
        box += [
            "",
            "O que e L3 Heuristicas?",
            "  Regras com numeros: 'Se X entao Y'. Acionavel imediatamente.",
        ]
    return _v3_step(14, "\U0001f3af", "DNA L3 HEURISTICAS", box)


def _step_15_dna_l4(data: dict[str, Any]) -> list[str]:
    """STEP 15 — DNA L4 FRAMEWORKS: extraction."""
    count = data.get("count", 0) if data else 0
    sample = (data.get("samples") or [])[:2] if data else []
    if not data or count == 0:
        box = [
            _V3_NO_DATA if not data else "0 frameworks extraidos nesta execucao.",
            "",
            "O que e L4 Frameworks?",
            "  Modelos estruturados com etapas e componentes definidos.",
            "  Exemplo: 'Value Ladder' (Brunson), 'Offer Stack' (Hormozi).",
        ]
    else:
        box = [f"Contagem:      {count} frameworks", ""]
        for i, s in enumerate(sample, 1):
            quote = str(s.get("quote", s) if isinstance(s, dict) else s)[:65]
            box.append(f"  {i}. \"{quote}\"")
        box += ["", "O que e L4?  Modelos estruturados — tem componentes e etapas."]
    return _v3_step(15, "\U0001f3d7", "DNA L4 FRAMEWORKS", box)


def _step_16_dna_l5(data: dict[str, Any]) -> list[str]:
    """STEP 16 — DNA L5 METODOLOGIAS: extraction."""
    count = data.get("count", 0) if data else 0
    if not data or count == 0:
        box = [
            _V3_NO_DATA if not data else "0 metodologias extraidas nesta execucao.",
            "",
            "O que e L5 Metodologias?",
            "  Processos passo-a-passo com inputs/outputs definidos.",
            "  Exemplo: '7-step sales call script' (Cole Gordon).",
        ]
    else:
        box = [
            f"Contagem:      {count} metodologias",
            "",
            "O que e L5?  Processos step-by-step com inputs/outputs.",
        ]
    return _v3_step(16, "\U0001f6e4", "DNA L5 METODOLOGIAS", box)


def _step_17_dna_l6(data: dict[str, Any]) -> list[str]:
    """STEP 17 — DNA L6 BEHAVIORAL: trigger -> action."""
    count = data.get("count", 0) if data else 0
    sample = (data.get("samples") or [])[:2] if data else []
    if not data or count == 0:
        box = [
            _V3_NO_DATA if not data else "0 padroes comportamentais extraidos.",
            "",
            "O que e L6 Behavioral?",
            "  Padroes trigger->action: 'Quando X acontece, ele faz Y'.",
            "  Captura comportamentos automaticos e respostas condicionadas.",
        ]
    else:
        box = [f"Contagem:      {count} padroes (trigger -> action)", ""]
        for s in sample:
            trigger = str(s.get("trigger", "?") if isinstance(s, dict) else s)[:30]
            action = str(s.get("action", "?") if isinstance(s, dict) else "")[:30]
            if action:
                box.append(f"  [{trigger}] -> [{action}]")
            else:
                box.append(f"  {trigger}")
        box += ["", "O que e L6?  Padroes automaticos trigger->action."]
    return _v3_step(17, "\U0001f504", "DNA L6 BEHAVIORAL", box)


def _step_18_dna_l7(data: dict[str, Any]) -> list[str]:
    """STEP 18 — DNA L7 VALUES HIERARCHY: rank + tier."""
    count = data.get("count", 0) if data else 0
    top_values = (data.get("top_values") or [])[:5] if data else []
    if not data or count == 0:
        box = [
            _V3_NO_DATA if not data else "0 valores extraidos nesta execucao.",
            "",
            "O que e L7 Values Hierarchy?",
            "  Ranking de valores: o que o especialista prioriza primeiro.",
            "  Revela o que e inegociavel vs. o que e conveniencia.",
        ]
    else:
        box = [f"Contagem:      {count} valores ranqueados", ""]
        for i, v in enumerate(top_values, 1):
            val_name = str(v.get("value", v) if isinstance(v, dict) else v)[:55]
            tier = str(v.get("tier", "") if isinstance(v, dict) else "")
            suffix = f"  [{tier}]" if tier else ""
            box.append(f"  #{i}: {val_name}{suffix}")
        box += ["", "O que e L7?  Hierarquia real de valores — o que e inegociavel."]
    return _v3_step(18, "⭐", "DNA L7 VALUES HIERARCHY", box)


def _step_19_dna_l8(data: dict[str, Any]) -> list[str]:
    """STEP 19 — DNA L8 VOICE DNA: tone + phrases + states."""
    count_phrases = data.get("phrases_count", 0) if data else 0
    tone = str(data.get("tone", "(nao disponivel)")) if data else "(nao disponivel)"
    sample_phrases = (data.get("signature_phrases") or [])[:3] if data else []
    if not data:
        box = [
            _V3_NO_DATA,
            "",
            "O que e L8 Voice DNA?",
            "  Tom, frases-assinatura e estados emocionais do especialista.",
            "  Permite que o agente responda NO ESTILO da pessoa real.",
        ]
    else:
        box = [
            f"Tom:           {tone}",
            f"Frases-sig.:   {count_phrases}",
            "",
        ]
        for i, p in enumerate(sample_phrases, 1):
            phrase = str(p if isinstance(p, str) else p.get("phrase", p))[:60]
            box.append(f"  {i}. \"{phrase}\"")
        box += [
            "",
            "O que e L8 Voice DNA?",
            "  Tom + frases-assinatura = identidade vocal do especialista.",
            "  Sem isso, o agente soa generico em vez de soar como a pessoa.",
        ]
    return _v3_step(19, "\U0001f4ac", "DNA L8 VOICE DNA", box)


def _step_20_dna_l9(data: dict[str, Any]) -> list[str]:
    """STEP 20 — DNA L9 OBSESSIONS: word frequency."""
    count = data.get("count", 0) if data else 0
    top_obsessions = (data.get("top_obsessions") or [])[:4] if data else []
    if not data or count == 0:
        box = [
            _V3_NO_DATA if not data else "0 obsessoes extraidas nesta execucao.",
            "",
            "O que e L9 Obsessions?",
            "  Temas que aparecem com frequencia anomala na fala do expert.",
            "  Obsessao = o que a pessoa nao consegue parar de mencionar.",
        ]
    else:
        box = [f"Contagem:      {count} obsessoes mapeadas", ""]
        for i, obs in enumerate(top_obsessions, 1):
            name = str(obs.get("name", obs) if isinstance(obs, dict) else obs)[:45]
            freq = obs.get("frequency", 0) if isinstance(obs, dict) else 0
            suffix = f"  (freq={freq})" if freq else ""
            box.append(f"  {i}. {name}{suffix}")
        box += [
            "",
            "O que e L9?  Temas recorrentes = o que a pessoa nao larga.",
        ]
    return _v3_step(20, "\U0001f525", "DNA L9 OBSESSIONS", box)


def _step_21_dna_l10(data: dict[str, Any]) -> list[str]:
    """STEP 21 — DNA L10 PARADOXES: tension A vs B."""
    count = data.get("count", 0) if data else 0
    sample_paradoxes = (data.get("paradoxes") or [])[:3] if data else []
    if not data or count == 0:
        box = [
            _V3_NO_DATA if not data else "0 paradoxos extraidos nesta execucao.",
            "",
            "O que e L10 Paradoxes?",
            "  Tensoes internas produtivas: 'Escale rapido' vs 'Faca direito'.",
            "  Paradoxos revelam a sofisticacao cognitiva do especialista.",
        ]
    else:
        box = [f"Contagem:      {count} paradoxos (tensao A vs B)", ""]
        for i, p in enumerate(sample_paradoxes, 1):
            if isinstance(p, dict):
                a = str(p.get("side_a", "?"))[:25]
                b = str(p.get("side_b", "?"))[:25]
                box.append(f"  {i}. [{a}] vs [{b}]")
            else:
                box.append(f"  {i}. {str(p)[:55]}")
        box += [
            "",
            "O que e L10?  Tensoes produtivas revelam maturidade cognitiva.",
        ]
    return _v3_step(21, "⚡", "DNA L10 PARADOXES", box)


def _step_22_identity_checkpoint(slug: str) -> list[str]:
    """STEP 22 — IDENTITY CHECKPOINT: gate Step 9 (Lens)."""
    path = MISSION_CONTROL / "mce" / slug / "checkpoints" / "identity-checkpoint.json"
    if not path.exists():
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  O Lens agent valida se os 10 layers de DNA sao coerentes",
            "  entre si. Sem esse gate, um agente com DNA conflitante",
            "  seria promovido para producao com identidade quebrada.",
        ]
        return _v3_step(22, "\U0001f50d", "IDENTITY CHECKPOINT", box)
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _v3_step(22, "\U0001f50d", "IDENTITY CHECKPOINT", [_V3_NO_DATA])

    verdict = str(data.get("verdict", "UNKNOWN")).upper()
    verdict_icon = {"APPROVE": "✅", "PASS": "✅", "REVISE": "⚠️", "FAIL": "❌", "REJECT": "❌"}.get(verdict, "❓")
    recommendation = str(data.get("recommendation", "(sem recomendacao)"))[:60]
    evidence = data.get("evidence") or {}
    checks = data.get("checks") or {}
    insights_total = evidence.get("insights_total", 0)
    ev_ok = (checks.get("evidence_threshold") or {}).get("passed", False)
    coh_ok = (checks.get("cross_layer_coherence") or {}).get("passed", False)
    bal_ok = (checks.get("obsessions_paradoxes_balance") or {}).get("passed", False)
    box = [
        f"Verdict:       {verdict_icon} {verdict}",
        f"Recom.:        {recommendation}",
        f"Total insights:{insights_total}",
        "",
        f"Evidence gate: {'✅ PASS' if ev_ok else '❌ FAIL'}",
        f"Coherencia:    {'✅ PASS' if coh_ok else '❌ FAIL'}",
        f"Obs/paradox:   {'✅ PASS' if bal_ok else '❌ FAIL'}",
        "",
        "Por que esse passo existe?",
        "  Lens valida coerencia cruzada entre layers L1-L10.",
        "  DNA incoerente = agente que contradiz a si mesmo.",
    ]
    return _v3_step(22, "\U0001f50d", "IDENTITY CHECKPOINT", box)


def _step_23_consolidation(slug: str, bucket: str) -> list[str]:
    """STEP 23 — CONSOLIDATION (Forge): dossier MD."""
    dossier = ROOT / "knowledge" / bucket / "dossiers" / "persons" / f"dossier-{slug}.md"
    if not dossier.exists():
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Forge consolida todos os layers de DNA em um dossier",
            "  narrativo unico. Sem ele, o conhecimento fica fragmentado",
            "  em YAMLs separados, inutilizavel para o agente.",
        ]
        return _v3_step(23, "\U0001f4dc", "CONSOLIDATION (Forge)", box)
    try:
        text = dossier.read_text(encoding="utf-8")
        stat = dossier.stat()
        sections = [ln.strip() for ln in text.splitlines() if ln.startswith("## ")]
        size_kb = stat.st_size // 1024
    except Exception:
        return _v3_step(23, "\U0001f4dc", "CONSOLIDATION (Forge)", [_V3_NO_DATA])

    box = [
        f"Dossier:       dossier-{slug}.md",
        f"Tamanho:       {size_kb}KB  ({stat.st_size} bytes)",
        f"Secoes:        {len(sections)}",
        "",
    ]
    for s in sections[:6]:
        box.append(f"  {s[:70]}")
    if len(sections) > 6:
        box.append(f"  ... +{len(sections) - 6} secoes")
    box += [
        "",
        "Por que esse passo existe?",
        "  Dossier = documento narrativo com todo o DNA integrado.",
        "  E a fonte de verdade para o agente durante queries de usuario.",
    ]
    return _v3_step(23, "\U0001f4dc", "CONSOLIDATION (Forge)", box)


def _step_24_agent_promotion(slug: str, bucket: str) -> list[str]:
    """STEP 24 — AGENT PROMOTION (Echo): skeleton -> complete."""
    base = ROOT / "agents" / bucket / slug
    agent_md = None
    for candidate in ("agent.md", "AGENT.md"):
        p = base / candidate
        if p.exists():
            agent_md = p
            break
    if agent_md is None:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Echo promove o agente de skeleton para complete.",
            "  Sem este passo, o agente existe como arquivo vazio",
            "  e nao pode responder queries com personalidade real.",
        ]
        return _v3_step(24, "\U0001f680", "AGENT PROMOTION (Echo)", box)
    try:
        text = agent_md.read_text(encoding="utf-8")
        stat = agent_md.stat()
        status_val = "(nao declarado)"
        version_val = "(nao declarado)"
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                for ln in text[3:end].splitlines():
                    ln = ln.strip()
                    if ln.startswith("status:"):
                        status_val = ln.split(":", 1)[1].strip()
                    elif ln.startswith("version:"):
                        version_val = ln.split(":", 1)[1].strip()
    except Exception:
        return _v3_step(24, "\U0001f680", "AGENT PROMOTION (Echo)", [_V3_NO_DATA])

    promoted = status_val.lower() in ("complete", "populated", "active", "production")
    box = [
        f"Agent file:    {agent_md.name}",
        f"Status:        {status_val}",
        f"Version:       {version_val}",
        f"Tamanho:       {stat.st_size} bytes",
        f"Promovido:     {'✅ Sim' if promoted else '❌ Nao (ainda skeleton)'}",
        "",
        "Por que esse passo existe?",
        "  Echo grava frontmatter status=complete e versao >= 1.0.0.",
        "  Sem isso, Lens pode negar o gate e pipeline para na Step 22.",
    ]
    return _v3_step(24, "\U0001f680", "AGENT PROMOTION (Echo)", box)


def _step_25_memory_enrichment(data: dict[str, Any]) -> list[str]:
    """STEP 25 — MEMORY ENRICHMENT: memory.md update."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 25 — MEMORY ENRICHMENT")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  MEMORY.md e a 'experiencia acumulada' do agente.",
            "  Cada run enriquece a memoria com novos insights, permitindo",
            "  que o agente evolua e aprenda entre sessoes.",
        ]
    else:
        appended = data.get("appended", 0)
        skipped = data.get("skipped_dedup", 0)
        agents = data.get("agents_enriched") or []
        box = [
            f"Insights add.: {appended}",
            f"Dedup skip:    {skipped}",
            f"Agentes:       {len(agents)}",
            "",
        ]
        for a in agents[:5]:
            box.append(f"  + {str(a)[:65]}")
        if len(agents) > 5:
            box.append(f"  ... +{len(agents) - 5} mais")
        box += [
            "",
            "Por que esse passo existe?",
            "  MEMORY.md = experiencia acumulada. Sem enriquecimento,",
            "  o agente responde so com DNA estatico, nao com aprendizado.",
        ]
    return _v3_step(25, "\U0001f9e0", "MEMORY ENRICHMENT", box)


def _step_26_cascading_a(data: dict[str, Any]) -> list[str]:
    """STEP 26 — CASCADING A · ROLE-TRACKER: F1+F2+D4."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 26 — CASCADING A · ROLE-TRACKER")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Role-tracker registra quais dominios e temas o especialista",
            "  cobre, alimentando o ROLE-TRACKING.json para o Phase-8 gate.",
        ]
    else:
        domains_updated = data.get("domains_updated", 0)
        themes_tracked = data.get("themes_tracked", 0)
        cargo_updated = data.get("cargo_agents_updated", 0)
        box = [
            f"Dominios:      {domains_updated}",
            f"Temas:         {themes_tracked}",
            f"Cargo agents:  {cargo_updated}",
            "",
            "Por que esse passo existe?",
            "  Cascading A = 'quem sabe o que'. Role-tracker mapeia o",
            "  especialista nos dominios corretos para routing de queries.",
        ]
    return _v3_step(26, "\U0001f4cb", "CASCADING A · ROLE-TRACKER", box)


def _step_27_cascading_b(data: dict[str, Any]) -> list[str]:
    """STEP 27 — CASCADING B · DOSSIÊS TEMA: hybrid."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 27 — CASCADING B · DOSSIÊS TEMA")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Dossies tematicos agregam insights de MULTIPLOS especialistas",
            "  num mesmo tema (ex: 'filosofia-operacional' tem Hormozi +",
            "  Gerber + Cole Gordon). Sem cascading B, nao ha visao cruzada.",
        ]
    else:
        themes_created = data.get("themes_created", 0)
        themes_updated = data.get("themes_updated", 0)
        insights_processed = data.get("insights_processed", 0)
        box = [
            f"Temas criados: {themes_created}",
            f"Temas upd.:    {themes_updated}",
            f"Insights proc.:{insights_processed}",
            "",
            "Por que esse passo existe?",
            "  Dossier de tema = visao agregada de multiplos experts.",
            "  Permite que o Conclave compare perspectivas sobre o mesmo tema.",
        ]
    return _v3_step(27, "\U0001f4da", "CASCADING B · DOSSIÊS TEMA", box)


def _step_28_cascading_c(data: dict[str, Any]) -> list[str]:
    """STEP 28 — CASCADING C · SOLOS P×TEMA: MCE-13.1-4."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 28 — CASCADING C · SOLOS P×TEMA")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Solos P x Tema = visao individual por pessoa e tema.",
            "  Permite comparar 'o que A pensa sobre X' vs 'o que B pensa'.",
        ]
    else:
        solos_written = data.get("solos_written", 0)
        persons_covered = data.get("persons_covered", 0)
        themes_covered = data.get("themes_covered", 0)
        box = [
            f"Solos escritos:{solos_written}",
            f"Pessoas:       {persons_covered}",
            f"Temas:         {themes_covered}",
            "",
            "Por que esse passo existe?",
            "  Solos P x Tema = perspectiva individual isolada.",
            "  Facilita comparacoes 'pessoa A vs pessoa B sobre tema X'.",
        ]
    return _v3_step(28, "\U0001f3b5", "CASCADING C · SOLOS P×TEMA", box)


def _step_29_narrative_synthesis(data: dict[str, Any]) -> list[str]:
    """STEP 29 — NARRATIVE SYNTHESIS: per person + theme."""
    if not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Narrativas convertem arrays de insights em texto fluido.",
            "  Sem narrativa, o agente responde em bullets desconexos,",
            "  sem o flow natural da voz do especialista.",
        ]
    else:
        total_narratives = data.get("total_narratives", 0)
        patterns_count = data.get("patterns_count", 0)
        consensus_count = data.get("consensus_count", 0)
        box = [
            f"Total narrativas:{total_narratives}",
            f"Padroes:         {patterns_count}",
            f"Consenso:        {consensus_count}",
            "",
            "Por que esse passo existe?",
            "  Narrativa = insights comprimidos em texto coerente.",
            "  E o que o agente 'le' para formular respostas fluidas.",
        ]
    return _v3_step(29, "\U0001f4dd", "NARRATIVE SYNTHESIS", box)


def _step_30_sources_compilation(data: dict[str, Any]) -> list[str]:
    """STEP 30 — SOURCES COMPILATION: por tema."""
    if not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Sources.md por tema lista todas as fontes primarias usadas.",
            "  Permite auditoria: 'esse insight veio de qual video/livro?'.",
        ]
    else:
        status = str(data.get("status", "unknown")).upper()
        # MCE-17.x STEP 30 fix: sources_compiler returns files_written as an int
        # count (not a list). Treat it as an int; keep len() only for temas_written
        # which is a genuine list.
        _fw = data.get("files_written", 0)
        files_written = _fw if isinstance(_fw, int) else len(_fw or [])
        temas_written = data.get("temas_written") or []
        box = [
            f"Status:        {status}",
            f"Arquivos:      {files_written}",
            f"Temas:         {len(temas_written)}",
            "",
        ]
        for t in temas_written[:5]:
            box.append(f"  + {str(t)[:65]}")
        if len(temas_written) > 5:
            box.append(f"  ... +{len(temas_written) - 5} mais temas")
        box += [
            "",
            "Por que esse passo existe?",
            "  Rastreabilidade: cada tema tem uma fonte. Sources.md",
            "  conecta o insight ao video/livro/podcast de origem.",
        ]
    return _v3_step(30, "\U0001f4da", "SOURCES COMPILATION", box)


def _step_31_domain_aggregator(data: dict[str, Any]) -> list[str]:
    """STEP 31 — DOMAIN AGGREGATOR: MAP-CONFLITOS."""
    if not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  MAP-CONFLITOS identifica onde experts do mesmo dominio",
            "  divergem. Essas tensoes sao o material mais rico para",
            "  debates no Conclave e decisoes do o fundador.",
        ]
    else:
        domain_count = len(data) if isinstance(data, dict) else 0
        total_conflicts = sum(
            (v.get("aggregation") or {}).get("conflicts_found", 0)
            for v in data.values()
            if isinstance(v, dict)
        )
        box = [
            f"Dominios:      {domain_count}",
            f"Conflitos tot.:{total_conflicts}",
            "",
        ]
        for domain_name, dr in (list(data.items()) if isinstance(data, dict) else [])[:5]:
            agg = (dr.get("aggregation") or {}) if isinstance(dr, dict) else {}
            cf = agg.get("conflicts_found", 0)
            exp = agg.get("experts_compared", 0)
            box.append(f"  {domain_name[:20]:<20}  experts={exp}  conflicts={cf}")
        box += [
            "",
            "Por que esse passo existe?",
            "  Conflitos entre experts = oportunidades de aprendizado.",
            "  Sem MAP-CONFLITOS, o sistema perderia as tensoes mais ricas.",
        ]
    return _v3_step(31, "\U0001f5fa", "DOMAIN AGGREGATOR", box)


def _step_32_rag_indexation(data: dict[str, Any]) -> list[str]:
    """STEP 32 — RAG INDEXATION (Art. XV): regression gate."""
    if not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Art. XV da Constituicao: RAG Indexation e OBRIGATORIA.",
            "  Sem rebuild do indice, queries semanticas retornam dados",
            "  obsoletos — o agente responde com conhecimento desatualizado.",
        ]
    else:
        gate_passed = data.get("gate_passed", False)
        gate_bypassed = data.get("gate_bypassed", False)
        chunks_pre = data.get("chunks_pre", 0)
        chunks_post = data.get("chunks_post", 0)
        delta = data.get("chunks_delta", chunks_post - chunks_pre)
        vectors_updated = data.get("vectors_updated", False)
        if gate_bypassed:
            gate_str = "\U0001f7e1 BYPASSED"
        elif gate_passed:
            gate_str = "✅ PASS"
        else:
            gate_str = "❌ FAIL"
        box = [
            f"Gate (Art.XV): {gate_str}",
            f"Chunks pre:    {chunks_pre}",
            f"Chunks post:   {chunks_post}",
            f"Delta:         {delta:+d}",
            f"Vetores:       {'✅ Atualizados' if vectors_updated else '❌ Nao atualizados'}",
            "",
            "Por que esse passo existe? (Art. XV — Constituicao)",
            "  RAG Index = motor de busca semantica do sistema.",
            "  Gate de regressao garante que o indice nunca diminua",
            "  mais de X% sem aprovacao humana explicita.",
        ]
    return _v3_step(32, "\U0001f50d", "RAG INDEXATION (Art. XV)", box)


def _step_33_workspace_sync(data: dict[str, Any]) -> list[str]:
    """STEP 33 — WORKSPACE SYNC: L0-L4."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 33 — WORKSPACE SYNC")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Workspace L0-L4 e a camada de dados de negocio do sistema.",
            "  Sync garante que knowledge extraido alimenta as camadas",
            "  estrategicas (L1) e operacionais (L4) do workspace.",
        ]
    else:
        synced = data.get("synced", 0)
        items_written = data.get("items_written", 0)
        layers_touched = data.get("layers_touched") or []
        box = [
            f"Itens sync.:   {synced}",
            f"Escritos:      {items_written}",
            f"Layers:        {', '.join(str(l) for l in layers_touched) or '(nenhum)'}",
            "",
            "Como interpretar?",
            "  L0=identidade (TTL 365d), L1=estrategia (90d),",
            "  L2=tatico (60d), L3=produto (30d), L4=operacional (7d).",
            "  Layers mais altos sobrescrevem layers mais baixos.",
        ]
    return _v3_step(33, "\U0001f3e2", "WORKSPACE SYNC", box)


def _step_34_phase8_gate(data: dict[str, Any]) -> list[str]:
    """STEP 34 — PHASE 8 GATE: 10 checks 7A-7J."""
    if not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Phase 8 Gate e o checkpoint de qualidade final do pipeline.",
            "  10 checks (7A-7J) validam integridade antes de considerar",
            "  o processamento completo para este material.",
        ]
    else:
        gate_status = str(data.get("gate_status", "UNKNOWN")).upper()
        gate_icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(gate_status, "❓")
        gate_checks = data.get("gate_checks") or {}
        passed_count = 0
        check_lines: list[str] = []
        for short in ("7A", "7B", "7C", "7D", "7E", "7F", "7G", "7H", "7I", "7J"):
            key = next((k for k in gate_checks if k.startswith(short)), None)
            if key:
                val = gate_checks[key]
                passed = (val.get("passed", False) if isinstance(val, dict) else bool(val))
            else:
                passed = False
            passed_count += int(passed)
            icon = "✅" if passed else "❌"
            check_lines.append(f"  {short}: {icon}")
        box = [
            f"Gate status:   {gate_icon} {gate_status}",
            f"Score:         {passed_count}/10",
            "",
        ] + check_lines + [
            "",
            "Por que esse passo existe?",
            "  10 checks em paralelo validam: insights, narrativas, fontes,",
            "  state files, role-tracking, cascading coverage, evolution log.",
        ]
    return _v3_step(34, "\U0001f6a6", "PHASE 8 GATE", box)


def _step_35_cross_batch_analysis(slug: str) -> list[str]:
    """STEP 35 — CROSS-BATCH ANALYSIS: anomalias."""
    batch_history_path = ROOT / ".data" / "artifacts" / "BATCH-HISTORY.json"
    if not batch_history_path.exists():
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Compara metricas desta execucao com historico de batches.",
            "  Detecta anomalias: queda brusca de insights, aumento de",
            "  custo, mudanca no pattern de chunks, etc.",
        ]
        return _v3_step(35, "\U0001f4c8", "CROSS-BATCH ANALYSIS", box)
    try:
        history = json.loads(batch_history_path.read_text(encoding="utf-8"))
        last_entry: dict[str, Any] = {}
        for entry in reversed(history if isinstance(history, list) else []):
            if isinstance(entry, dict) and entry.get("slug") == slug:
                last_entry = entry
                break
    except Exception:
        last_entry = {}

    if not last_entry:
        box = [
            f"Nenhum historico para slug '{slug}'",
            "",
            "Por que esse passo existe?",
            "  Baseline de metricas para deteccao de anomalias futuras.",
        ]
        return _v3_step(35, "\U0001f4c8", "CROSS-BATCH ANALYSIS", box)

    anomalies = last_entry.get("anomalies") or []
    batch_id = str(last_entry.get("batch_id", "(unknown)"))
    box = [
        f"Batch ID:      {batch_id}",
        f"Anomalias:     {len(anomalies)}",
        "",
    ]
    if not anomalies:
        box.append("✅ Sem anomalias detectadas.")
    else:
        for a in anomalies[:4]:
            if isinstance(a, dict):
                metric = str(a.get("metric", "?"))[:18]
                dev = a.get("deviation_pct", 0.0)
                box.append(f"  ⚠️ {metric:<18} dev={dev:+.1f}%")
            else:
                box.append(f"  ⚠️ {str(a)[:60]}")
    box += [
        "",
        "Como interpretar?",
        "  dev < -50%: anomalia critica (vermelho). Investigar causa.",
        "  dev < -25%: anomalia moderada (amarelo). Monitorar.",
        "  Sem anomalias: padrao normal para este especialista.",
    ]
    return _v3_step(35, "\U0001f4c8", "CROSS-BATCH ANALYSIS", box)


def _step_36_contradictions(data: dict[str, Any]) -> list[str]:
    """STEP 36 — CONTRADICTIONS: conflicts cross-history."""
    if not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Detecta quando novos insights contradizem insights anteriores",
            "  do mesmo especialista. Contradicoes sao paradoxos (L10)",
            "  ou erros de extracao — ambos precisam de revisao humana.",
        ]
    else:
        count = data.get("contradictions_count", 0)
        conflicts = data.get("conflicts") or []
        if count == 0:
            box = [
                "✅ Sem contradicoes detectadas. DNA coerente.",
                "",
                "Como interpretar?",
                "  Ausencia de contradicoes = DNA consistente no historico.",
                "  Nao significa que o especialista nunca se contradicoes —",
                "  significa que as contradicoes sao sutis ou inexistentes.",
            ]
        else:
            box = [f"Contradicoes:  {count}", ""]
            for c in conflicts[:4]:
                if isinstance(c, dict):
                    summary = str(c.get("tension_summary", "(sem resumo)"))[:60]
                    box.append(f"  ⚡ {summary}")
                else:
                    box.append(f"  ⚡ {str(c)[:65]}")
            box += [
                "",
                "Como interpretar?",
                "  Pode ser paradoxo legitimo (L10) ou erro de extracao.",
                "  Revisar manualmente antes de promover o agente.",
            ]
    return _v3_step(36, "⚡", "CONTRADICTIONS", box)


def _step_37_lifecycle_move(data: dict[str, Any]) -> list[str]:
    """STEP 37 — LIFECYCLE MOVE: inbox -> processed."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 37 — LIFECYCLE MOVE")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Arquivos processados precisam sair do inbox para nao",
            "  serem reprocessados na proxima execucao do pipeline.",
            "  Move atomico: inbox/ -> processed/. Reversivel com git.",
        ]
    else:
        moved = data.get("files_moved", 0)
        source = str(data.get("source_dir", "(nao disponivel)"))[-45:]
        destination = str(data.get("destination_dir", "(nao disponivel)"))[-45:]
        box = [
            f"Arquivos mov.: {moved}",
            f"De:            ...{source}",
            f"Para:          ...{destination}",
            "",
            "Por que esse passo existe?",
            "  Sem lifecycle move, inbox cresce indefinidamente.",
            "  Cada run reprocessaria todo o historico — catastrofico.",
        ]
    return _v3_step(37, "\U0001f4e4", "LIFECYCLE MOVE", box)


def _step_38_batch_history(data: dict[str, Any]) -> list[str]:
    """STEP 38 — BATCH HISTORY UPDATE: BATCH-HISTORY.json."""
    if _is_fail_no_data(data):  # MCE-17.0 T10
        box = _fail_no_data_box("STEP 38 — BATCH HISTORY UPDATE")
    elif not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  BATCH-HISTORY.json e o livro de registros do pipeline.",
            "  Cada execucao adiciona uma entrada com metricas, timestamps",
            "  e anomalias. E a base do CROSS-BATCH ANALYSIS (Step 35).",
        ]
    else:
        batch_id = str(data.get("batch_id", "(nao disponivel)"))
        entries_total = data.get("entries_total", 0)
        appended = data.get("appended", True)
        box = [
            f"Batch ID:      {batch_id}",
            f"Total entries: {entries_total}",
            f"Adicionado:    {'✅ Sim' if appended else '❌ Nao'}",
            "",
            "Por que esse passo existe?",
            "  Historico de batches = serie temporal de metricas do pipeline.",
            "  Permite calcular baseline para deteccao de anomalias futuras.",
        ]
    return _v3_step(38, "\U0001f4ca", "BATCH HISTORY UPDATE", box)


def _step_39_llm_cost(data: dict[str, Any]) -> list[str]:
    """STEP 39 — LLM COST + PROVIDER: $ + tokens + by_phase."""
    if not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Rastreabilidade de custos por fase. Sem isso, impossivel",
            "  saber qual fase do pipeline e mais cara e otimizar.",
        ]
    else:
        total_usd = data.get("total_usd", 0.0)
        total_input = data.get("total_input_tokens", 0)
        total_output = data.get("total_output_tokens", 0)
        by_phase = data.get("by_phase") or {}
        box = [
            f"Custo total:   ${total_usd:.6f}",
            f"Input tokens:  {total_input:,}",
            f"Output tokens: {total_output:,}",
            f"Total tokens:  {total_input + total_output:,}",
            "",
        ]
        if by_phase:
            box.append(f"  {'Fase':<22} {'USD':>10}")
            box.append(f"  {'─' * 22} {'─' * 10}")
            for phase, pd in list(by_phase.items())[:6]:
                pusd = (pd.get("usd", 0.0) if isinstance(pd, dict) else 0.0)
                box.append(f"  {phase[:21]:<22} ${pusd:>9.6f}")
        box += [
            "",
            "Como interpretar?",
            "  Fase mais cara = gargalo de custo. Candidata a otimizacao.",
            "  total_usd / person_insights = custo por insight extraido.",
        ]
    return _v3_step(39, "\U0001f4b0", "LLM COST + PROVIDER", box)


def _step_40_squad_activation(data: dict[str, Any]) -> list[str]:
    """STEP 40 — SQUAD ACTIVATION + HOOKS: telemetry."""
    if not data:
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  Registra quais squads e hooks foram acionados durante o run.",
            "  Telemetria essencial para debugging de falhas silenciosas.",
        ]
    else:
        squads_activated = data.get("squads_activated", 0)
        squads_list = data.get("squads") or []
        box = [
            f"Squads:        {squads_activated}",
            "",
        ]
        for item in squads_list[:5]:
            name = str(item.get("slug", item) if isinstance(item, dict) else item)[:55]
            count = item.get("count", 1) if isinstance(item, dict) else 1
            box.append(f"  + {name}  ({count}x)")
        if len(squads_list) > 5:
            box.append(f"  ... +{len(squads_list) - 5} mais squads")
        box += [
            "",
            "Por que esse passo existe?",
            "  Audit trail de squads. Se pipeline falha silenciosamente,",
            "  este step mostra qual squad nao foi acionado.",
        ]
    return _v3_step(40, "\U0001f916", "SQUAD ACTIVATION + HOOKS", box)


def _step_41_executive_briefing(slug: str) -> list[str]:
    """STEP 41 — EXECUTIVE BRIEFING: LLM summary."""
    tag = _make_tag(slug)
    brief_dir = ROOT / "logs" / "executive-briefings"
    if not brief_dir.is_dir():
        box = [
            _V3_NO_DATA,
            "",
            "Por que esse passo existe?",
            "  O LLM gera um resumo executivo de 3-5 paragrafos.",
            "  Sem ele, o operador precisa ler todo o log para entender",
            "  o que mudou — ineficiente em producao.",
        ]
        return _v3_step(41, "\U0001f4cb", "EXECUTIVE BRIEFING", box)

    candidates = sorted(brief_dir.glob(f"BRIEFING-{tag}-*.md"), reverse=True)
    if not candidates:
        box = [
            f"Nenhum briefing encontrado para tag {tag}",
            "",
            "Por que esse passo existe?",
            "  Briefing LLM = resumo executivo do run em linguagem natural.",
        ]
        return _v3_step(41, "\U0001f4cb", "EXECUTIVE BRIEFING", box)

    try:
        text = candidates[0].read_text(encoding="utf-8")
        brief_name = candidates[0].name
        text_lines = text.splitlines()[:12]
    except Exception:
        return _v3_step(41, "\U0001f4cb", "EXECUTIVE BRIEFING", [_V3_NO_DATA])

    box = [f"Arquivo:       {brief_name}", ""]
    box.extend(ln[:73] for ln in text_lines)
    if len(text.splitlines()) > 12:
        box.append(f"... (+{len(text.splitlines()) - 12} linhas — ver arquivo completo)")
    box += [
        "",
        "Por que esse passo existe?",
        "  Resumo executivo = decisao rapida. Operador le em 30 segundos",
        "  o que mudou e qual a proxima acao recomendada.",
    ]
    return _v3_step(41, "\U0001f4cb", "EXECUTIVE BRIEFING", box)


def _step_42_health_score(data: dict[str, Any]) -> list[str]:
    """STEP 42 — HEALTH SCORE: 5 components."""
    if not data:
        box = [
            _V3_NO_DATA,
            "",
            "Como interpretar?",
            "  Health Score 0-100 mede qualidade do estado do sistema.",
            "  5 componentes: state_files, agents, dossiers, inbox, pipeline.",
            "  Score < 60 = sistema precisa de atencao imediata.",
        ]
    else:
        score_total = data.get("score_total", 0)
        grade = str(data.get("grade", "(nao disponivel)"))
        components = data.get("components") or {}
        filled = "▓" * (score_total * 25 // 100)
        empty = "░" * (25 - len(filled))
        bar = filled + empty
        box = [
            f"Score total:   {score_total}/100  Grade: {grade}",
            f"[{bar}]",
            "",
        ]
        dim_labels = [
            ("state_files", "State files"),
            ("agents", "Agents"),
            ("dossiers", "Dossiers"),
            ("inbox", "Inbox"),
            ("pipeline", "Pipeline"),
        ]
        for dim_key, dim_label in dim_labels:
            dim = components.get(dim_key) or {}
            if not isinstance(dim, dict):
                continue
            dim_score = dim.get("score", 0)
            dim_max = dim.get("max", 20)
            box.append(f"  {dim_label:<14} {dim_score:>2}/{dim_max}")
        box += [
            "",
            "Como interpretar?",
            "  Grade A (90-100): sistema saudavel, pode promover para prod.",
            "  Grade B (70-89): pequenas lacunas, monitorar.",
            "  Grade C (<70): atencao imediata necessaria.",
        ]
    return _v3_step(42, "\U0001f4ca", "HEALTH SCORE", box)


def _step_43_proxima_etapa(
    slug: str,
    gate_data: dict[str, Any],
    health_data: dict[str, Any],
    dossier_info: dict[str, Any],
) -> list[str]:
    """STEP 43 — PROXIMA ETAPA: prioritized."""
    pending: list[tuple[str, str, str]] = []
    gate_st = str(gate_data.get("gate_status", "")) if gate_data else ""
    if gate_st and gate_st != "PASS":
        pending.append(("\U0001f534 P1", "Resolver falhas no Phase-8 Gate", "~15min"))
    if not (dossier_info or {}).get("exists"):
        pending.append(("\U0001f534 P2", f"Gerar dossier-{slug}.md (consolidate)", "~5min"))
    health_score = (health_data or {}).get("score_total", 100)
    if health_score < 70:
        pending.append(("\U0001f7e1 P3", f"Health Score baixo ({health_score}/100) — investigar", "~20min"))
    pending.append(("\U0001f7e2 P4", "Revisar insights de maior impacto no dossier", "~10min"))
    pending.append(("\U0001f7e2 P5", "Expandir cross-references com outros experts", "~20min"))

    box = [
        f"Acoes priorizadas para {slug}:",
        "",
    ]
    for priority, desc, effort in pending[:5]:
        line = f"{priority}: {desc}"
        if len(line) > 65:
            line = line[:65]
        box.append(f"  {line}  [{effort}]")
    box += [
        "",
        "Como interpretar?",
        "  P1-P2 (vermelho) = blockers — sistema degradado sem eles.",
        "  P3 (amarelo) = importante mas nao bloqueia.",
        "  P4-P5 (verde) = enrichment continuo recomendado.",
    ]
    return _v3_step(43, "⭐", "PROXIMA ETAPA", box)


def _step_pre_00_bucket_selection(slug: str, data: dict) -> list[str]:
    """pre-00 canonical block: ENTRY ROUTING DECISION.

    Renders BEFORE _step_00 in generate_mce_log_v3.
    Story: MCE-16.4
    """
    # MCE-17.0 T10: explicit FAIL when no-fallback mode is active
    if _is_fail_no_data(data):
        out = [
            "",
            _v3_canonical_top("pre-00", "\U0001f4e6", "BUCKET DE SELECAO"),
            _v3_box_top(),
        ]
        for ln in _fail_no_data_box("pre-00 — BUCKET DE SELECAO"):
            out.append(_v3_box_line(ln))
        out.append(_v3_box_bot())
        out.append(_v3_step_bot())
        return out

    out: list[str] = [
        "",
        _v3_canonical_top("pre-00", "\U0001f4e6", "BUCKET DE SELECAO"),
        _v3_box_top(),
    ]

    fname = data.get("original_filename") or "_(sem material)_"
    if len(fname) > 50:
        fname = "..." + fname[-47:]

    source = data.get("source_url") or "_(local)_"
    if len(source) > 50:
        source = source[:47] + "..."

    routing_reason = (data.get("routing_reason") or "")[:50]
    destination = (data.get("destination") or "")[:50]

    lines_inner: list[str] = [
        "ENTRADA",
        f"  Material:    {fname}",
        f"  Fonte:       {source}",
        f"  Tipo:        {data.get('source_kind', 'unknown')}",
        "",
        "ENTITY DISCOVERY",
        f"  Verdict:     {data.get('verdict', 'UNKNOWN')}",
        f"  Confianca:   {data.get('confidence', '')}",
        f"  Motivo:      {routing_reason}",
        "",
        "ATLAS CLASSIFICATION",
    ]

    domains = data.get("domains") or []
    if domains:
        primary = domains[0]
        secondary = ", ".join(domains[1:])[:50]
        lines_inner.append(f"  Dominio primario:  {primary}")
        if secondary:
            lines_inner.append(f"  Dominios sec.:     {secondary}")
        lines_inner.append(
            f"  Confianca:         {data.get('atlas_confidence', 0.0):.2f}"
        )
    else:
        lines_inner.append("  _(sem classificacao)_")

    lines_inner.extend([
        "",
        "BUCKET DECISION",
        f"  Bucket:      {data.get('bucket', 'unknown')}",
        f"  Slug:        {data.get('slug', '')}",
        f"  Destino:     {destination}",
        f"  Metodo:      {data.get('method', '')}",
        "",
        "CROSS-REFERENCES",
    ])

    crefs = data.get("cross_references") or []
    if crefs:
        lines_inner.append(f"  {', '.join(str(c) for c in crefs)[:60]}")
    else:
        lines_inner.append("  _(nenhuma)_")

    lines_inner.extend([
        "",
        "Por que este bloco existe?",
        "  Resposta antecipada: para qual bucket o material vai parar.",
        "  Auditoria de roteamento — se o slug aparece no bucket errado,",
        "  o problema e detectado AQUI antes de descer 45 STEPs.",
    ])

    for ln in lines_inner:
        out.append(_v3_box_line(ln))

    out.append(_v3_box_bot())
    out.append(_v3_step_bot())
    return out


def _step_post_44_cascade_tree(slug: str, data: dict) -> list[str]:
    """post-44 canonical block: CASCADE TREE OUTPUT.

    Renders AFTER _step_44 in generate_mce_log_v3.
    Story: MCE-16.4
    """
    # MCE-17.0 T10: explicit FAIL when no-fallback mode is active
    # NOTE: post-44 is always called with {} as stream_data (audit confirmed).
    # With MCE_NO_FALLBACK=1 this will ALWAYS be FAIL_NO_DATA.
    if _is_fail_no_data(data):
        out = [
            "",
            _v3_canonical_top("post-44", "\U0001f333", "ARVORE DE CASCATEAMENTO"),
            _v3_box_top(),
        ]
        for ln in _fail_no_data_box("post-44 — ARVORE DE CASCATEAMENTO (sempre disk)"):
            out.append(_v3_box_line(ln))
        out.append(_v3_box_bot())
        out.append(_v3_step_bot())
        return out

    out: list[str] = [
        "",
        _v3_canonical_top("post-44", "\U0001f333", "ARVORE DE CASCATEAMENTO"),
        _v3_box_top(),
    ]

    s = data.get("slug") or slug
    bucket = data.get("bucket", "unknown")

    lines_inner: list[str] = [
        f"{s}  ({bucket})",
        " │",
        " ├── A. ROLE-TRACKER",
    ]

    domains = data.get("domains") or []
    domain_counts = data.get("domain_expert_counts") or {}

    if domains:
        lines_inner.append(" │    Dominios cobertos:")
        for i, d in enumerate(domains):
            is_last = i == len(domains) - 1
            branch = "└──" if is_last else "├──"
            count = domain_counts.get(d, 1)
            entry = f" │    {branch} {d}"
            suffix = f" [{count} experts]"
            # Pad to fixed width so suffix doesn't push past 75 inner
            if len(entry) + len(suffix) > 75:
                entry = entry[:75 - len(suffix)]
            lines_inner.append(entry + suffix)
    else:
        lines_inner.append(" │    _(sem dominios registrados)_")

    lines_inner.extend([
        " │",
        " ├── B. DOSSIES DE TEMA  (cross-pessoa)",
    ])

    themes = data.get("theme_dossiers") or []
    theme_count = data.get("theme_count", 0)

    if themes:
        lines_inner.append(
            f" │    Material agregado em:  {theme_count} dossiers"
        )
        show = themes[:8]
        for i, t in enumerate(show):
            is_last = i == len(show) - 1 and len(themes) <= 8
            branch = "└──" if is_last else "├──"
            lines_inner.append(f" │    {branch} {t[:50]}")
        if len(themes) > 8:
            lines_inner.append(
                f" │    └── ... (+{len(themes) - 8} dossiers)"
            )
    else:
        lines_inner.append(" │    _(nenhum dossie tematico)_")

    lines_inner.extend([
        " │",
        " └── C. SOLOS P x TEMA",
    ])

    solos = data.get("person_solos") or []
    if solos:
        lines_inner.append(
            f"      Por tema deste expert:  {len(solos)} solos"
        )
        show_s = solos[:8]
        for i, sol in enumerate(show_s):
            is_last = i == len(show_s) - 1 and len(solos) <= 8
            branch = "└──" if is_last else "├──"
            lines_inner.append(f"      {branch} {sol[:55]}")
        if len(solos) > 8:
            lines_inner.append(
                f"      └── ... (+{len(solos) - 8} solos)"
            )
    else:
        lines_inner.append("      _(nenhum solo)_")

    lines_inner.extend([
        "",
        "Por que este bloco existe?",
        "  Os 45 STEPS descrevem o PROCESSO. Este bloco mostra o OUTPUT:",
        "  quais artefatos em disco foram tocados. Fecha o ciclo:",
        "  ENTRADA (pre-00) + PROCESSO (00-44) + SAIDA (post-44).",
    ])

    for ln in lines_inner:
        out.append(_v3_box_line(ln))

    out.append(_v3_box_bot())
    out.append(_v3_step_bot())
    return out


def _step_44_chronicler_audit(
    slug: str, step_count_rendered: int, now: str
) -> list[str]:
    """STEP 44 — CHRONICLER AUDIT: meta self-check."""
    expected_steps = 44
    missing = expected_steps - step_count_rendered
    audit_ok = missing == 0
    box = [
        f"Steps esperados: {expected_steps}",
        f"Steps renderizados: {step_count_rendered}",
        f"Status:        {'✅ COMPLETO' if audit_ok else f'❌ {missing} STEPS FALTANDO'}",
        "Canonical blocks:  2 / 2  (pre-00 + post-44)",
        f"Gerado em:     {now}",
        "Versao:        Chronicler v3.2.0",
        "",
        "O que e o Chronicler Audit?",
        "  Meta-verificacao que o proprio log usa para garantir",
        "  que todos os 44 steps foram renderizados. Se esse step",
        "  mostra steps faltando, o log_generator.py tem um bug.",
        "",
        "Como interpretar?",
        "  Status COMPLETO = 44 steps presentes. Log integro.",
        "  Steps faltando = regressao no log_generator. Investigar.",
    ]
    return _v3_step(44, "\U0001f50e", "CHRONICLER AUDIT", box)


# ─── SHARED STEP COLLECTOR (single source for v3.2 + v4) ────────────────────


# Ordered (step_num, title) — titles MUST match the v3 _step_NN title argument.
_MCE_STEP_TITLES: list[tuple[int, str]] = [
    (0, "SOURCE DISCOVERY"), (1, "INGESTION GUARD"), (2, "DOWNLOAD/EXTRACT"),
    (3, "SPEAKER VISUAL GATE"), (4, "ENTITY DISCOVERY"), (5, "FILENAME SIDECAR WRITE"),
    (6, "CLASSIFICATION (Atlas)"), (7, "ORGANIZATION + INBOX ROUTING"),
    (8, "BATCH CREATION"), (9, "CHUNKING"),
    (10, "EMBEDDINGS GENERATION"), (11, "ENTITY RESOLUTION"),
    (12, "DNA L1 FILOSOFIAS"), (13, "DNA L2 MODELOS MENTAIS"),
    (14, "DNA L3 HEURISTICAS"), (15, "DNA L4 FRAMEWORKS"),
    (16, "DNA L5 METODOLOGIAS"), (17, "DNA L6 BEHAVIORAL"),
    (18, "DNA L7 VALUES HIERARCHY"), (19, "DNA L8 VOICE DNA"),
    (20, "DNA L9 OBSESSIONS"), (21, "DNA L10 PARADOXES"),
    (22, "IDENTITY CHECKPOINT"), (23, "CONSOLIDATION (Forge)"),
    (24, "AGENT PROMOTION (Echo)"), (25, "MEMORY ENRICHMENT"),
    (26, "CASCADING A · ROLE-TRACKER"), (27, "CASCADING B · DOSSIÊS TEMA"),
    (28, "CASCADING C · SOLOS P×TEMA"), (29, "NARRATIVE SYNTHESIS"),
    (30, "SOURCES COMPILATION"), (31, "DOMAIN AGGREGATOR"),
    (32, "RAG INDEXATION (Art. XV)"), (33, "WORKSPACE SYNC"),
    (34, "PHASE 8 GATE"), (35, "CROSS-BATCH ANALYSIS"),
    (36, "CONTRADICTIONS"), (37, "LIFECYCLE MOVE"),
    (38, "BATCH HISTORY UPDATE"), (39, "LLM COST + PROVIDER"),
    (40, "SQUAD ACTIVATION + HOOKS"), (41, "EXECUTIVE BRIEFING"),
    (42, "HEALTH SCORE"), (43, "PROXIMA ETAPA"), (44, "CHRONICLER AUDIT"),
]


def _collect_mce_step_outputs(
    slug: str,
    enrichment_result: dict[str, Any] | None = None,
    cascade_result: dict[str, Any] | None = None,
    sync_result: dict[str, Any] | None = None,
    collected_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve all per-STEP data and build the v3 step outputs ONCE.

    This is the single source of truth for both ``generate_mce_log_v3`` (legacy
    rendering) and ``generate_mce_log_v4`` (wide rendering). It performs the
    identical data-extraction the v3 driver always did — only the rendering of
    the returned step outputs differs between v3 and v4.

    Returns a dict with:
      ``person_name``, ``tag``, ``now``, ``bucket``,
      ``pre00``  — v3 lines for the pre-00 canonical block,
      ``steps``  — ``[(step_num, title, v3_step_lines), ...]`` for STEP 00-44,
      ``post44`` — v3 lines for the post-44 canonical block.
    """
    enrichment_result = enrichment_result or {}
    cascade_result = cascade_result or {}
    sync_result = sync_result or {}
    collected_data = collected_data or {}

    # ── Resolve identity ────────────────────────────────────────────────────
    tag = collected_data.get("tag") or _make_tag(slug)
    now = collected_data.get("timestamp") or datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    if collected_data.get("person_name"):
        person_name = collected_data["person_name"]
    elif _HAS_DATA_COLLECTOR:
        person_name = _resolve_person_name(slug)
    else:
        person_name = " ".join(w.capitalize() for w in slug.split("-"))

    # ── Bucket ──────────────────────────────────────────────────────────────
    bucket = collected_data.get("bucket", "external") if collected_data else "external"

    # ── Load PHASE-STREAM ───────────────────────────────────────────────────
    stream = _load_phase_stream(slug)

    # ── Load supplementary data ─────────────────────────────────────────────
    try:
        gate_data = _fpb_load_phase8_gate(slug)
    except Exception:
        gate_data = {}
    try:
        health_data = _fpb_load_health(slug)
    except Exception:
        health_data = {}
    try:
        dossier_info = _fpb_load_dossier_info(slug, bucket)
    except Exception:
        dossier_info = {"exists": False}

    # ── DNA counts ───────────────────────────────────────────────────────────
    dna = collected_data.get("dna") or _load_dna_counts(slug)

    def _dna_step_data(layer_key: str) -> dict[str, Any]:
        count = int(dna.get(layer_key, 0) or 0)
        return {"count": count} if count > 0 else {}

    dna_l1 = _dna_step_data("FILOSOFIAS")
    dna_l2 = _dna_step_data("MODELOS_MENTAIS")
    dna_l3 = _dna_step_data("HEURISTICAS")
    dna_l4 = _dna_step_data("FRAMEWORKS")
    dna_l5 = _dna_step_data("METODOLOGIAS")

    # ── Attempt to load voice-dna for L8 ────────────────────────────────────
    try:
        voice_path = ROOT / "knowledge" / bucket / "dna" / "persons" / slug / "voice-dna.yaml"
        dna_l8_data: dict[str, Any] = {}
        if voice_path.exists():
            import yaml as _yaml
            vd = _yaml.safe_load(voice_path.read_text(encoding="utf-8")) or {}
            if isinstance(vd, dict):
                phrases = vd.get("signature_phrases") or []
                tone = str(vd.get("tone", vd.get("communication_style", "(nao disponivel)")))[:40]
                dna_l8_data = {"tone": tone, "phrases_count": len(phrases), "signature_phrases": phrases[:5]}
    except Exception:
        dna_l8_data = {}

    # ── Attempt to load values-hierarchy for L7 ─────────────────────────────
    try:
        vals_path = ROOT / "knowledge" / bucket / "dna" / "persons" / slug / "values-hierarchy.yaml"
        dna_l7_data: dict[str, Any] = {}
        if vals_path.exists():
            import yaml as _yaml2
            vdata = _yaml2.safe_load(vals_path.read_text(encoding="utf-8")) or {}
            if isinstance(vdata, dict):
                values_list = vdata.get("values") or vdata.get("hierarchy") or []
                dna_l7_data = {"count": len(values_list), "top_values": values_list[:5]}
    except Exception:
        dna_l7_data = {}

    # ── Attempt to load obsessions for L9 ───────────────────────────────────
    try:
        obs_path = ROOT / "knowledge" / bucket / "dna" / "persons" / slug / "obsessions.yaml"
        dna_l9_data: dict[str, Any] = {}
        if obs_path.exists():
            import yaml as _yaml3
            odata = _yaml3.safe_load(obs_path.read_text(encoding="utf-8")) or {}
            if isinstance(odata, dict):
                obs_list = odata.get("obsessions") or odata.get("items") or []
                dna_l9_data = {"count": len(obs_list), "top_obsessions": obs_list[:4]}
    except Exception:
        dna_l9_data = {}

    # ── Attempt to load paradoxes for L10 ────────────────────────────────────
    try:
        par_path = ROOT / "knowledge" / bucket / "dna" / "persons" / slug / "paradoxes.yaml"
        dna_l10_data: dict[str, Any] = {}
        if par_path.exists():
            import yaml as _yaml4
            pdata = _yaml4.safe_load(par_path.read_text(encoding="utf-8")) or {}
            if isinstance(pdata, dict):
                par_list = pdata.get("paradoxes") or pdata.get("items") or []
                dna_l10_data = {"count": len(par_list), "paradoxes": par_list[:3]}
    except Exception:
        dna_l10_data = {}

    # ── Attempt to load behavioral for L6 ───────────────────────────────────
    try:
        beh_path = ROOT / "knowledge" / bucket / "dna" / "persons" / slug / "behavioral-patterns.yaml"
        dna_l6_data: dict[str, Any] = {}
        if beh_path.exists():
            import yaml as _yaml5
            bdata = _yaml5.safe_load(beh_path.read_text(encoding="utf-8")) or {}
            if isinstance(bdata, dict):
                patterns = bdata.get("patterns") or []
                dna_l6_data = {"count": len(patterns), "samples": patterns[:2]}
    except Exception:
        dna_l6_data = {}

    # ── pre-00 canonical block ──────────────────────────────────────────────
    _pre00_data = (
        stream.get("bucket_selection")
        or stream.get("entity_discovery")
        or {}
    )
    pre00 = _step_pre_00_bucket_selection(
        slug,
        _with_disk_fallback(
            _pre00_data,
            lambda: _load_bucket_selection_from_disk(slug),
        ),
    )

    # ── STEPS 00-43 (44 is appended after, using step_count) ────────────────
    step_outputs: list[list[str]] = []
    step_outputs.append(_step_00_source_discovery(
        _with_disk_fallback(stream.get("source_discovery") or {}, lambda: _load_source_discovery_from_disk(slug))
    ))
    step_outputs.append(_step_01_ingestion_guard(
        _with_disk_fallback(stream.get("ingestion_guard") or {}, lambda: _load_ingestion_guard_from_disk(slug))
    ))
    step_outputs.append(_step_02_download_extract(
        stream.get("download_extract") or _with_disk_explicit(lambda: _load_download_extract_from_disk(slug))
    ))
    step_outputs.append(_step_03_speaker_visual_gate(
        stream.get("speaker_visual_gate") or _with_disk_explicit(lambda: _load_speaker_visual_gate_from_disk(slug))
    ))
    step_outputs.append(_step_04_entity_discovery(
        _with_disk_fallback(stream.get("entity_discovery") or {}, lambda: _load_entity_discovery_from_disk(slug))
    ))
    step_outputs.append(_step_05_filename_sidecar(
        _with_disk_fallback(stream.get("filename_sidecar") or {}, lambda: _load_filename_sidecar_from_disk(slug))
    ))
    step_outputs.append(_step_06_classification(
        _with_disk_fallback(
            (collected_data.get("metadata") or {}).get("classification") or stream.get("classification") or {},
            lambda: _load_classification_from_disk(slug),
        )
    ))
    step_outputs.append(_step_07_organization_routing(
        _with_disk_fallback(
            (collected_data.get("metadata") or {}).get("organization")
            or (collected_data.get("metadata") or {}).get("routing")
            or stream.get("organization")
            or stream.get("routing")
            or {},
            lambda: _load_organization_routing_from_disk(slug),
        )
    ))
    step_outputs.append(_step_08_batch_creation(
        _with_disk_fallback(stream.get("batch_creation") or {}, lambda: _load_batch_creation_from_disk(slug))
    ))
    step_outputs.append(_step_09_chunking(
        _with_disk_fallback(stream.get("chunking") or {}, lambda: _load_chunking_from_disk(slug))
    ))
    step_outputs.append(_step_10_embeddings(
        _with_disk_fallback(stream.get("embeddings") or {}, lambda: _load_embeddings_from_disk(slug))
    ))
    step_outputs.append(_step_11_entity_resolution(
        _with_disk_fallback(stream.get("entity_resolution") or {}, lambda: _load_entity_resolution_from_disk(slug))
    ))
    step_outputs.append(_step_12_dna_l1(dna_l1))
    step_outputs.append(_step_13_dna_l2(dna_l2))
    step_outputs.append(_step_14_dna_l3(dna_l3))
    step_outputs.append(_step_15_dna_l4(dna_l4))
    step_outputs.append(_step_16_dna_l5(dna_l5))
    step_outputs.append(_step_17_dna_l6(dna_l6_data))
    step_outputs.append(_step_18_dna_l7(dna_l7_data))
    step_outputs.append(_step_19_dna_l8(dna_l8_data))
    step_outputs.append(_step_20_dna_l9(dna_l9_data))
    step_outputs.append(_step_21_dna_l10(dna_l10_data))
    step_outputs.append(_step_22_identity_checkpoint(slug))
    step_outputs.append(_step_23_consolidation(slug, bucket))
    step_outputs.append(_step_24_agent_promotion(slug, bucket))
    _me_stream = stream.get("memory_enrichment") or {}
    _rt_stream = stream.get("role_tracker") or {}
    _cd_stream = stream.get("cascading_dossiers") or {}
    step_outputs.append(_step_25_memory_enrichment(_with_disk_fallback(
        _me_stream or enrichment_result,
        lambda: _load_memory_enrichment_from_disk(slug),
    )))
    step_outputs.append(_step_26_cascading_a(_with_disk_fallback(
        _rt_stream or (cascade_result if cascade_result else {}),
        lambda: _load_cascading_a_role_tracker_from_disk(slug),
    )))
    step_outputs.append(_step_27_cascading_b(_with_disk_fallback(
        _cd_stream or (cascade_result if cascade_result else {}),
        lambda: _load_cascading_b_theme_dossiers_from_disk(slug),
    )))
    step_outputs.append(_step_28_cascading_c(
        stream.get("cascading_solos") or _with_disk_explicit(lambda: _load_cascading_c_solos_from_disk(slug))
    ))
    step_outputs.append(_step_29_narrative_synthesis(stream.get("narrative_metabolism") or {}))
    step_outputs.append(_step_30_sources_compilation(stream.get("sources_compilation") or {}))
    step_outputs.append(_step_31_domain_aggregator(stream.get("domain_aggregator") or {}))
    step_outputs.append(_step_32_rag_indexation(stream.get("rag_indexation") or {}))
    _ws_stream = stream.get("workspace_sync") or {}
    step_outputs.append(_step_33_workspace_sync(_with_disk_fallback(
        _ws_stream or sync_result,
        lambda: _load_workspace_sync_from_disk(slug),
    )))
    step_outputs.append(_step_34_phase8_gate(stream.get("phase8_gate") or gate_data or {}))
    step_outputs.append(_step_35_cross_batch_analysis(slug))
    step_outputs.append(_step_36_contradictions(stream.get("contradictions") or {}))
    step_outputs.append(_step_37_lifecycle_move(_with_disk_fallback(
        stream.get("lifecycle_move") or {},
        lambda: _load_lifecycle_move_from_disk(slug),
    )))
    step_outputs.append(_step_38_batch_history(_with_disk_fallback(
        stream.get("batch_history") or {},
        lambda: _load_batch_history_from_disk(slug),
    )))
    step_outputs.append(_step_39_llm_cost(stream.get("llm_cost") or {}))
    step_outputs.append(_step_40_squad_activation(stream.get("squad_activation") or {}))
    step_outputs.append(_step_41_executive_briefing(slug))
    step_outputs.append(_step_42_health_score(health_data))
    step_outputs.append(_step_43_proxima_etapa(slug, gate_data, health_data, dossier_info))
    # STEP 44 — step_count = 44 (steps 00-43) before audit, matching v3 semantics.
    step_count = len(step_outputs)
    step_outputs.append(_step_44_chronicler_audit(slug, step_count, now))

    # ── post-44 canonical block ─────────────────────────────────────────────
    post44 = _step_post_44_cascade_tree(
        slug,
        _with_disk_fallback(
            stream.get("cascade_tree") or {},
            lambda: _load_cascade_tree_from_disk(slug),
        ),
    )

    steps: list[tuple[int, str, list[str]]] = [
        (_MCE_STEP_TITLES[i][0], _MCE_STEP_TITLES[i][1], step_outputs[i])
        for i in range(len(step_outputs))
    ]

    return {
        "person_name": person_name,
        "tag": tag,
        "now": now,
        "bucket": bucket,
        "pre00": pre00,
        "steps": steps,
        "post44": post44,
    }


# ─── MAIN v3 GENERATOR ──────────────────────────────────────────────────────


def generate_mce_log_v3(
    slug: str,
    enrichment_result: dict[str, Any] | None = None,
    cascade_result: dict[str, Any] | None = None,
    sync_result: dict[str, Any] | None = None,
    index_result: dict[str, Any] | None = None,
    collected_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate Chronicler v3.2.0 log — 44 STEPS + 2 canonical blocks, 79-char width, didactic.

    Args:
        slug: Person slug, e.g. ``"jordan-lee"``.
        enrichment_result: Memory enrichment output.
        cascade_result: Cascading step output.
        sync_result: Workspace sync output.
        index_result: RAG index rebuild output.
        collected_data: Pre-loaded from chronicler_data_collector.

    Returns:
        ``{"log_path": str, "status": "written", "size_bytes": int}`` or
        ``{"error": str}``.
    """
    payload = _collect_mce_step_outputs(
        slug=slug,
        enrichment_result=enrichment_result,
        cascade_result=cascade_result,
        sync_result=sync_result,
        collected_data=collected_data,
    )
    person_name = payload["person_name"]
    tag = payload["tag"]
    now = payload["now"]

    # ── ASSEMBLE v3.2 LOG ────────────────────────────────────────────────────
    lines: list[str] = []
    lines.extend(_v3_header(person_name, slug, now))
    lines.append("")
    lines.extend(payload["pre00"])
    lines.append("")
    for _num, _title, step_lines in payload["steps"]:
        lines.extend(step_lines)
        lines.append("")
    lines.extend(payload["post44"])
    lines.append("")
    lines.extend(_v3_footer(person_name, slug, now))

    # ── WRITE FILE ───────────────────────────────────────────────────────────
    log_dir = LOGS / "mce" / slug
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"MCE-{tag}.md"

    content = "\n".join(lines)
    try:
        log_path.write_text(content, encoding="utf-8")
        logger.info("MCE log v3 written to %s (%d bytes)", log_path, len(content))
        return {"log_path": str(log_path), "status": "written", "size_bytes": len(content)}
    except Exception as exc:
        logger.warning("Failed to write MCE log v3: %s", exc)
        return {"error": str(exc)}


# ─── MAIN v4 GENERATOR ──────────────────────────────────────────────────────


def generate_mce_log_v4(
    slug: str,
    enrichment_result: dict[str, Any] | None = None,
    cascade_result: dict[str, Any] | None = None,
    sync_result: dict[str, Any] | None = None,
    index_result: dict[str, Any] | None = None,
    collected_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate Chronicler v4.0 log — 44 STEPS + 2 canonical blocks, 100-col wide.

    Reuses the EXACT data-extraction of v3.2 via ``_collect_mce_step_outputs``;
    only the rendering changes — wide boxes grouped into 6 pipeline phases with
    status ribbons, 2-column metrics sub-tables, an inline glossary and group
    banners with progress bars. Zero data loss vs v3.2 (every value token in the
    v3 box survives as a metric value, an ``extra`` line, or ``why`` text).

    Same return shape as ``generate_mce_log_v3``.

    Story: MCE-17.x (founder-approved officialization)
    """
    data = _collect_mce_step_outputs(
        slug=slug,
        enrichment_result=enrichment_result,
        cascade_result=cascade_result,
        sync_result=sync_result,
        collected_data=collected_data,
    )
    person_name = data["person_name"]
    tag = data["tag"]
    now = data["now"]

    # ── ASSEMBLE v4.0 LOG ────────────────────────────────────────────────────
    lines: list[str] = []
    lines.extend(_v4_header(person_name, slug, now))
    lines.append("")

    # pre-00 canonical block (v4 wide box)
    lines.extend(_v4_canonical_from_v3(
        "pre-00", "BUCKET DE SELEÇÃO", data["pre00"], "CAPA · ENTRADA"
    ))
    lines.append("")

    # STEP 00-44 grouped into the 6 pipeline phases
    cur_group: int | None = None
    for num, title, v3_lines in data["steps"]:
        group = _v4_group_for(num)
        if group != cur_group:
            lines.extend(_v4_group_banner(group, num))
            cur_group = group
        step_tag = "⭐ TOP" if num == 14 else ""
        lines.extend(_v4_step_from_v3(num, title, v3_lines, tag=step_tag))
        lines.append("")

    # post-44 canonical block (v4 wide box)
    lines.extend(_v4_canonical_from_v3(
        "post-44", "ÁRVORE DE CASCATEAMENTO", data["post44"], "SAÍDA"
    ))
    lines.append("")

    # Footer
    lines.extend(_v4_footer(person_name, slug, now))

    # ── Width safety net — guarantee ≤ 100 display cells on every line ───────
    lines = [ln if _v4_dwidth(ln) <= _V4_W else _v4_clip(ln, _V4_W) for ln in lines]

    # ── WRITE FILE ───────────────────────────────────────────────────────────
    log_dir = LOGS / "mce" / slug
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"MCE-{tag}.md"

    content = "\n".join(lines)
    try:
        log_path.write_text(content, encoding="utf-8")
        logger.info("MCE log v4 written to %s (%d bytes)", log_path, len(content))
        return {"log_path": str(log_path), "status": "written", "size_bytes": len(content)}
    except Exception as exc:
        logger.warning("Failed to write MCE log v4: %s", exc)
        return {"error": str(exc)}


def generate_mce_log(
    slug: str,
    enrichment_result: dict[str, Any] | None = None,
    agent_trigger_result: dict[str, Any] | None = None,
    cascade_result: dict[str, Any] | None = None,
    sync_result: dict[str, Any] | None = None,
    index_result: dict[str, Any] | None = None,
    collected_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Entry point for MCE log generation.

    Template is gated by the ``MCE_LOG_TEMPLATE`` env var:
      * ``v4``    (default — founder-approved official) → Chronicler v4.0 wide log.
      * ``v3.2``  (rollback)                            → legacy Chronicler v3.2.

    For the much older v2 layout, call ``generate_mce_log_v2_legacy()`` directly.

    Version: 4.0.0
    Story: MCE-14.0 (v3 base) · MCE-17.x (v4 officialization)
    """
    tmpl = os.environ.get("MCE_LOG_TEMPLATE", "v4").strip().lower()
    if tmpl in ("v3.2", "v3", "3.2"):
        return generate_mce_log_v3(
            slug=slug,
            enrichment_result=enrichment_result,
            cascade_result=cascade_result,
            sync_result=sync_result,
            index_result=index_result,
            collected_data=collected_data,
        )
    return generate_mce_log_v4(
        slug=slug,
        enrichment_result=enrichment_result,
        cascade_result=cascade_result,
        sync_result=sync_result,
        index_result=index_result,
        collected_data=collected_data,
    )
