#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          MCE STEP LOGGER  —  PostToolUse Hook (Write|Edit)                   ║
║          Version: 2.0.0  —  Realtime Observability Edition                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  O QUE FAZ:                                                                  ║
║  Detecta writes em artefatos MCE durante Steps 3-10. Para cada step:         ║
║    1. Grava entrada JSONL estruturada em logs/mce-step-logger.jsonl           ║
║    2. Retorna painel ASCII rico como feedback ao Claude Code                  ║
║                                                                              ║
║  ARTEFATOS MONITORADOS:                                                      ║
║    Step 3   →  artifacts/chunks/CHUNKS-STATE.json                            ║
║    Step 4   →  artifacts/canonical/CANONICAL-MAP.json                        ║
║    Step 5   →  artifacts/insights/INSIGHTS-STATE.json (sem behavioral)       ║
║    Step 6   →  artifacts/insights/INSIGHTS-STATE.json (com behavioral)       ║
║    Step 7   →  artifacts/insights/INSIGHTS-STATE.json (com value_hierarchy)  ║
║    Step 8   →  knowledge/external/dna/persons/*/VOICE-DNA.yaml               ║
║    Step 9   →  .claude/mission-control/mce/*/pipeline_state.yaml (transição) ║
║    Step 10  →  dossiers, DNA YAMLs, sources, agent files (sub-steps)         ║
║                                                                              ║
║  CONSTRAINTS:                                                                ║
║    - stdlib apenas + PyYAML (já instalado)                                   ║
║    - Exit 0 always — logging NUNCA bloqueia pipeline                         ║
║    - Timeout: 5000ms                                                         ║
║    - Swallow all exceptions                                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
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

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
LOG_PATH = PROJECT_DIR / "logs" / "mce-step-logger.jsonl"
MCE_STATE_DIR = PROJECT_DIR / ".claude" / "mission-control" / "mce"

# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

# Panel inner width (characters between borders)
PW = 62

STEP_DISPLAY = {
    0: "DETECT",
    1: "INGEST",
    2: "BATCH",
    3: "CHUNK",
    4: "ENTITY",
    5: "INSIGHT",
    6: "BEHAVIORAL",
    7: "IDENTITY",
    8: "VOICE-DNA",
    9: "CHECKPOINT",
    10: "COMPILE",
    11: "FINALIZE",
    12: "REPORT",
}

BUCKET_ICON = {
    "external": "📚 EXTERNAL",
    "business": "🏢 BUSINESS",
    "personal": "🧠 PERSONAL",
    "workspace": "🗂️  WORKSPACE",
}

DNA_TAGS = [
    ("FILOSOFIA",    "Filosofia   "),
    ("MODELO-MENTAL","Mod. Mental "),
    ("HEURISTICA",   "Heurística  "),
    ("FRAMEWORK",    "Framework   "),
    ("METODOLOGIA",  "Metodologia "),
]

TONE_DIMS = [
    ("certainty",  "Certainty  "),
    ("authority",  "Authority  "),
    ("warmth",     "Warmth     "),
    ("directness", "Directness "),
    ("humor",      "Humor      "),
    ("formality",  "Formality  "),
]

DNA_YAML_LAYERS = {
    "FILOSOFIAS.yaml":      "L1 — Filosofias e Crenças",
    "MODELOS-MENTAIS.yaml": "L2 — Modelos Mentais",
    "HEURISTICAS.yaml":     "L3 — Heurísticas",
    "FRAMEWORKS.yaml":      "L4 — Frameworks",
    "METODOLOGIAS.yaml":    "L5 — Metodologias",
}

AGENT_FILE_ROLES = {
    "AGENT.md":      "Definição completa (Template V3, 11 pts)",
    "SOUL.md":       "Filosofia, inner game, identidade profunda",
    "MEMORY.md":     "Insights acumulados, scripts, citações",
    "DNA-CONFIG.yaml": "Rastreabilidade de fontes + pesos",
}

SUBSTEP_ICON = {
    "10.1_dossier": "📄",
    "10.2_sources": "📚",
    "10.3_dna_yaml": "🧬",
    "10.4_agent":   "🤖",
}

# ─────────────────────────────────────────────────────────────────────────────
# ASCII BOX RENDERING ENGINE
# ─────────────────────────────────────────────────────────────────────────────


def _bar(value: int, max_val: int, width: int = 18,
         filled: str = "█", empty: str = "░") -> str:
    """Render a proportional fill bar."""
    if max_val <= 0:
        return empty * width
    n = min(width, round(value / max_val * width))
    return filled * n + empty * (width - n)


def _tone_bar(score: float, width: int = 10,
              filled: str = "●", empty: str = "○") -> str:
    """Render a tone score bar (0-10 scale)."""
    n = min(width, max(0, round(float(score))))
    return filled * n + empty * (width - n)


def _row(content: str) -> str:
    """Pad content to fill one row inside the box borders."""
    truncated = content[:PW]
    return f"║  {truncated.ljust(PW)}  ║"


def _top() -> str:
    return f"╔{'═' * (PW + 4)}╗"


def _bottom() -> str:
    return f"╚{'═' * (PW + 4)}╝"


def _div() -> str:
    """Heavy divider (section separator)."""
    return f"╠{'═' * (PW + 4)}╣"


def _thin() -> str:
    """Light divider (sub-section separator)."""
    return f"╟{'─' * (PW + 4)}╢"


def _section(title: str) -> str:
    return _row(f"  ▸ {title}")


def _blank() -> str:
    return _row("")


def _check(ok: bool, label: str) -> str:
    return ("✅ " if ok else "❌ ") + label


def _fmt_slug(slug: str) -> str:
    return slug.upper().replace("-", " ")


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024 / 1024:.1f} MB"


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE PROGRESS BAR
# ─────────────────────────────────────────────────────────────────────────────


def _progress_section(current_step: int) -> list[str]:
    """
    Two-row pipeline progress bar:
      Row 1: S00–S06
      Row 2: S07–S12
    Symbols: ● done  ◉ current  ○ pending
    """
    def sym(s: int) -> str:
        if s < current_step:
            return f"S{s:02d}●"
        if s == current_step:
            return f"S{s:02d}◉"
        return f"S{s:02d}○"

    row1 = "  ".join(sym(s) for s in range(7))
    row2 = "  ".join(sym(s) for s in range(7, 13))
    pct = round(current_step / 12 * 100)
    steps_done = current_step
    bar_done = round(current_step / 12 * 30)
    prog_bar = "█" * bar_done + "░" * (30 - bar_done)

    return [
        _thin(),
        _section(f"PIPELINE PROGRESS  {steps_done}/12 steps  [{pct:>3d}%]"),
        _row(f"  {prog_bar}"),
        _row(f"  {row1}"),
        _row(f"  {row2}"),
        _bottom(),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# PANEL HEADER
# ─────────────────────────────────────────────────────────────────────────────


def _panel_header(step: int, slug: str, bucket: str) -> list[str]:
    step_str = f"STEP {step:02d} — {STEP_DISPLAY.get(step, '???'):>12s}"
    slug_str = f"[ {_fmt_slug(slug)} ]"
    bucket_str = BUCKET_ICON.get(bucket, bucket.upper())
    ts_str = datetime.now().strftime("%H:%M:%S")

    line1 = f"{step_str:<35s}{slug_str:>27s}"
    line2 = f"  Bucket : {bucket_str:<20s}  ⏱ {ts_str}"

    return [
        _top(),
        _row(line1),
        _row(line2),
        _div(),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION ROWS
# ─────────────────────────────────────────────────────────────────────────────


def _validation_section(validation: dict) -> list[str]:
    if not validation:
        return []
    lines = [_thin(), _section("VALIDAÇÃO")]
    items = [(k, v) for k, v in validation.items() if not k.endswith("_count")]
    # Two checks per row
    for i in range(0, len(items), 2):
        pair = items[i:i + 2]
        parts = [_check(v, k.replace("_", " ")) for k, v in pair]
        lines.append(_row("   ".join(parts)))
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# STEP-SPECIFIC PANEL BUILDERS
# ─────────────────────────────────────────────────────────────────────────────


def _panel_step3(slug: str, bucket: str, m: dict, v: dict) -> str:
    dist = m.get("word_counts_distribution", {})
    total = max(m.get("chunks_created", 1), 1)
    persons = m.get("persons_detected", [])

    lines = _panel_header(3, slug, bucket)
    lines += [
        _section("RESULTADO DO CHUNKING SEMÂNTICO"),
        _row(f"  Chunks Criados  : {m.get('chunks_created', 0):>6,d}"),
        _row(f"  Média de Palavras: {m.get('avg_chunk_words', 0):>5,d} words/chunk"),
        _row(f"  Tokens (est.)   : {m.get('total_tokens_estimate', 0):>6,d}"),
        _row(f"  Arquivos Fonte  : {m.get('source_files_processed', 0):>6d}"),
    ]
    if persons:
        lines.append(_row(f"  Pessoas         : {', '.join(persons[:4])}"))

    lines += [
        _thin(),
        _section("DISTRIBUIÇÃO DE TAMANHO"),
    ]
    lt200 = dist.get("lt_200", 0)
    mid   = dist.get("btw_200_350", 0)
    gt350 = dist.get("gt_350", 0)
    lines += [
        _row(f"  < 200 words   {_bar(lt200, total)} {lt200:>4d}"),
        _row(f"  200–350 wds   {_bar(mid,   total)} {mid:>4d}  ← ideal"),
        _row(f"  > 350 words   {_bar(gt350, total)} {gt350:>4d}"),
    ]

    lines += _validation_section(v)
    lines += _progress_section(3)
    return "\n".join(lines)


def _panel_step4(slug: str, bucket: str, m: dict, v: dict) -> str:
    top_entities = m.get("top_entities", [])

    lines = _panel_header(4, slug, bucket)
    lines += [
        _section("CANONICAL MAP — ESTADO ATUAL"),
        _row(f"  Total Entidades : {m.get('total_entities', 0):>6,d}"),
        _row(f"  Total Variantes : {m.get('total_variants', 0):>6,d}"),
        _thin(),
        _section("DELTA — INCREMENTO DESTA EXECUÇÃO"),
        _row(f"  + Entidades Novas : {m.get('new_entities_added', 0):>5,d}"),
        _row(f"  + Variantes Novas : {m.get('new_variants_added', 0):>5,d}"),
    ]
    if top_entities:
        lines += [_thin(), _section("TOP ENTIDADES CANÔNICAS")]
        for e in top_entities[:5]:
            lines.append(_row(f"    • {e}"))

    lines += _validation_section(v)
    lines += _progress_section(4)
    return "\n".join(lines)


def _panel_step5(slug: str, bucket: str, m: dict, v: dict) -> str:
    by_tag  = m.get("by_dna_tag", {})
    by_prio = m.get("by_priority", {})
    total   = max(m.get("total_insights", 1), 1)
    max_tag = max(by_tag.values(), default=1)

    lines = _panel_header(5, slug, bucket)
    lines += [
        _section("INSIGHTS EXTRAÍDOS"),
        _row(f"  Total Insights  : {m.get('total_insights', 0):>6,d}"),
        _row(f"  Persons         : {m.get('persons_with_insights', 0):>6d}"),
        _thin(),
        _section("PRIORIDADE"),
        _row(f"  HIGH   {_bar(by_prio.get('HIGH', 0),   total)} {by_prio.get('HIGH', 0):>4d}"),
        _row(f"  MEDIUM {_bar(by_prio.get('MEDIUM', 0), total)} {by_prio.get('MEDIUM', 0):>4d}"),
        _row(f"  LOW    {_bar(by_prio.get('LOW', 0),    total)} {by_prio.get('LOW', 0):>4d}"),
        _thin(),
        _section("DNA LAYERS EXTRAÍDAS"),
    ]
    for tag, label in DNA_TAGS:
        count = by_tag.get(tag, 0)
        pct   = round(count / total * 100)
        lines.append(_row(
            f"  {label} {_bar(count, max_tag)} {count:>4d} ({pct:>2d}%)"
        ))

    lines += _validation_section(v)
    lines += _progress_section(5)
    return "\n".join(lines)


def _panel_step6(slug: str, bucket: str, m: dict, v: dict) -> str:
    by_type = m.get("by_type", {})
    total   = max(m.get("total_patterns", 1), 1)
    max_t   = max(by_type.values(), default=1)

    lines = _panel_header(6, slug, bucket)
    lines += [
        _section("PADRÕES COMPORTAMENTAIS (MCE)"),
        _row(f"  Total Patterns      : {m.get('total_patterns', 0):>5,d}"),
        _row(f"  Com evidência 2+ ck : {m.get('patterns_with_evidence', 0):>5,d}"),
        _row(f"  Avg evidence chunks : {m.get('avg_evidence_chunks', 0.0):>5.1f}"),
    ]
    if by_type:
        lines += [_thin(), _section("TIPOS DE PADRÃO")]
        for ptype, count in sorted(by_type.items(), key=lambda x: -x[1]):
            lbl = f"{ptype:<16s}"
            lines.append(_row(f"  {lbl} {_bar(count, max_t)} {count:>3d}"))

    lines += _validation_section(v)
    lines += _progress_section(6)
    return "\n".join(lines)


def _panel_step7(slug: str, bucket: str, m: dict, v: dict) -> str:
    top_vals    = m.get("top_values", [])
    master_obs  = m.get("master_obsession", "—")
    t1          = m.get("tier1_count", 0)

    lines = _panel_header(7, slug, bucket)
    lines += [
        _section("HIERARQUIA DE VALORES"),
        _row(f"  Total Values  : {m.get('values_count', 0):>4d}"
             f"   (Tier-1: {t1}  Tier-2: {m.get('tier2_count', 0)})"),
    ]
    if top_vals:
        for i, v_name in enumerate(top_vals):
            tier = "T1 ★" if i < t1 else "T2"
            lines.append(_row(f"    [{tier}] {v_name}"))

    lines += [
        _thin(),
        _section("OBSESSÕES"),
        _row(f"  Total        : {m.get('obsessions_count', 0):>4d}"),
        _row(f"  MASTER (1x)  : {master_obs}"),
        _thin(),
        _section("PARADOXOS"),
        _row(f"  Total        : {m.get('paradoxes_count', 0):>4d}"),
        _row(f"  Produtivos   : {m.get('productive_paradoxes', 0):>4d}"),
    ]

    lines += _validation_section(v)
    lines += _progress_section(7)
    return "\n".join(lines)


def _panel_step8(slug: str, bucket: str, m: dict, v: dict) -> str:
    tone = m.get("tone_profile", {})
    samples = m.get("sample_phrases", [])

    lines = _panel_header(8, slug, bucket)
    lines += [_section("VOICE-DNA — 6 DIMENSÕES DE TOM")]
    for key, label in TONE_DIMS:
        score = float(tone.get(key, 0))
        bar   = _tone_bar(score)
        lines.append(_row(f"  {label}  {bar}  {score:.0f}/10"))

    lines += [
        _thin(),
        _row(f"  Signature Phrases : {m.get('signature_phrases', 0):>3d}"),
        _row(f"  Behavioral States : {m.get('behavioral_states', 0):>3d}"),
        _row(f"  Forbidden Patterns: {m.get('forbidden_patterns', 0):>3d}"),
        _row(f"  Tone Dims Defined : {m.get('tone_dimensions_defined', 0):>3d} / 6"),
    ]
    if samples:
        lines += [_thin(), _section("FRASES ASSINATURA (amostra)")]
        for p in samples[:3]:
            t = (p[:PW - 5] + "…") if len(p) > PW - 5 else p
            lines.append(_row(f"  › {t}"))

    lines += _validation_section(v)
    lines += _progress_section(8)
    return "\n".join(lines)


def _panel_step9(slug: str, bucket: str, m: dict, v: dict) -> str:
    decision = m.get("decision", "UNKNOWN")
    icon = "✅ APROVADO → COMPILE" if decision == "APPROVE" else \
           "🔄 REVISÃO  → MCE re-run" if decision == "REVISE" else \
           "❓ DESCONHECIDO"

    lines = _panel_header(9, slug, bucket)
    lines += [
        _section("IDENTITY CHECKPOINT — DECISÃO HUMANA"),
        _row(f"  Decisão         : {icon}"),
        _row(f"  Estado Anterior : {m.get('previous_state', '—')}"),
        _row(f"  Estado Atual    : {m.get('new_state', '—')}"),
        _row(f"  Transições FSM  : {m.get('total_transitions', 0):>3d}"),
    ]
    if decision == "APPROVE":
        lines += [_thin(), _row("  → Pipeline avança para STEP 10 (CONSOLIDATION)")]
    elif decision == "REVISE":
        lines += [_thin(), _row("  → Pipeline retorna para MCE EXTRACTION (revision loop)")]

    lines += _validation_section(v)
    lines += _progress_section(9)
    return "\n".join(lines)


def _panel_step10(slug: str, bucket: str, m: dict, v: dict) -> str:
    substep  = m.get("substep", "10.x_other")
    label    = m.get("label", substep)
    icon     = SUBSTEP_ICON.get(substep, "📁")
    size_str = _fmt_bytes(m.get("file_size_bytes", 0))

    lines = _panel_header(10, slug, bucket)
    lines += [
        _section(f"{icon} ARTEFATO ESCRITO — {substep.upper()}"),
        _row(f"  Arquivo   : {label}"),
        _row(f"  Tamanho   : {size_str}"),
    ]

    if substep == "10.1_dossier":
        path = m.get("dossier_path", "—")
        short = path if len(path) <= PW - 10 else "…" + path[-(PW - 11):]
        lines += [_thin(), _row(f"  Path: {short}")]

    elif substep == "10.3_dna_yaml":
        yaml_name = m.get("yaml_name", "—")
        layer_desc = DNA_YAML_LAYERS.get(yaml_name, yaml_name)
        lines += [
            _thin(),
            _row(f"  DNA Layer : {layer_desc}"),
        ]

    elif substep == "10.4_agent":
        agent_file = m.get("agent_file", "—")
        role = AGENT_FILE_ROLES.get(agent_file, "—")
        lines += [
            _thin(),
            _row(f"  Função    : {role}"),
        ]

    elif substep == "10.2_sources":
        lines += [_thin(), _row(f"  Source doc: {m.get('source_doc', '—')}")]

    lines += _validation_section(v)
    lines += _progress_section(10)
    return "\n".join(lines)


def _panel_fallback(step: int, step_name: str, slug: str, rel: str) -> str:
    lines = [
        _top(),
        _row(f"  STEP {step:02d} — {STEP_DISPLAY.get(step, step_name.upper()):<20s}  [ {_fmt_slug(slug)} ]"),
        _div(),
        _row(f"  Artifact  : {rel[:PW - 13]}"),
        _row("  ✅ Entrada JSONL registrada"),
    ]
    lines += _progress_section(step)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# PANEL DISPATCHER
# ─────────────────────────────────────────────────────────────────────────────


def _build_panel(step: int, step_name: str, slug: str, rel: str,
                 bucket: str, m: dict, v: dict) -> str:
    dispatch = {
        3:  _panel_step3,
        4:  _panel_step4,
        5:  _panel_step5,
        6:  _panel_step6,
        7:  _panel_step7,
        8:  _panel_step8,
        9:  _panel_step9,
        10: _panel_step10,
    }
    fn = dispatch.get(step)
    if fn:
        return fn(slug, bucket, m, v)
    return _panel_fallback(step, step_name, slug, rel)


# ─────────────────────────────────────────────────────────────────────────────
# JSONL INFRASTRUCTURE
# ─────────────────────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_relative(file_path: str) -> str:
    try:
        return str(Path(file_path).resolve().relative_to(PROJECT_DIR))
    except (ValueError, OSError):
        return file_path


def _append_jsonl(entry: dict[str, Any]) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass  # Never block pipeline


def _read_json(path: Path) -> dict | list | None:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _read_yaml(path: Path) -> dict | None:
    if not HAS_YAML:
        return None
    try:
        if path.exists():
            return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def _read_last_entry(step: int, slug: str) -> dict | None:
    """Read the most recent JSONL entry for step+slug (for delta computation)."""
    try:
        if not LOG_PATH.exists():
            return None
        last: dict | None = None
        with open(LOG_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if e.get("step") == step and e.get("slug") == slug:
                        last = e
                except json.JSONDecodeError:
                    pass
        return last
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# SLUG & BUCKET DETECTION
# ─────────────────────────────────────────────────────────────────────────────


def _slug_from_path(rel: str) -> str:
    """Extract slug from path segment after 'persons' or 'external'."""
    parts = Path(rel).parts
    for i, part in enumerate(parts):
        if part in ("persons", "external", "business", "personal") and i + 1 < len(parts):
            cand = parts[i + 1]
            if "." not in cand:
                return cand
    return ""


def _slug_from_state() -> str:
    """Scan MCE state dirs for the active (non-complete) pipeline."""
    if not MCE_STATE_DIR.exists():
        return ""
    for d in sorted(MCE_STATE_DIR.iterdir()):
        if not d.is_dir():
            continue
        data = _read_yaml(d / "pipeline_state.yaml")
        if data and data.get("state") not in ("complete", "failed", None):
            return d.name
    return ""


def _detect_slug(rel: str) -> str:
    return _slug_from_path(rel) or _slug_from_state() or "unknown"


def _detect_bucket(rel: str) -> str:
    if "knowledge/external" in rel or "agents/external" in rel:
        return "external"
    if "knowledge/business" in rel or "agents/business" in rel:
        return "business"
    if "knowledge/personal" in rel or "agents/personal" in rel:
        return "personal"
    if "workspace/" in rel:
        return "workspace"
    return "external"


# ─────────────────────────────────────────────────────────────────────────────
# ARTIFACT MATCHING
# ─────────────────────────────────────────────────────────────────────────────


def _match_artifact(rel: str) -> tuple[int, str] | None:
    """
    Return (step, step_name) for a relative artifact path, or None.

    Detection priority (specific → general):
      1. VOICE-DNA.yaml  → Step 8
      2. pipeline_state.yaml in mission-control → Step 9
      3. DNA YAMLs (FILOSOFIAS, MODELOS-MENTAIS, etc.) → Step 10
      4. DOSSIER-*.md in dossiers/persons/ → Step 10
      5. Agent files (AGENT.md, SOUL.md, MEMORY.md, DNA-CONFIG.yaml) → Step 10
      6. Sources docs in knowledge/*/sources/ → Step 10
      7. CHUNKS-STATE.json → Step 3
      8. CANONICAL-MAP.json → Step 4
      9. INSIGHTS-STATE.json → Steps 5/6/7 (differentiated by content)
    """
    fname = Path(rel).name

    # 1. Voice DNA
    if fname == "VOICE-DNA.yaml" and "dna/persons/" in rel:
        return (8, "mce_voice")

    # 2. FSM state (Step 9 checkpoint detection)
    if fname == "pipeline_state.yaml" and ".claude/mission-control/mce/" in rel:
        return (9, "identity_checkpoint")

    # 3. DNA YAML layers
    if fname in DNA_YAML_LAYERS and "dna/persons/" in rel:
        return (10, "consolidation")

    # 4. Dossier
    if fname.startswith("DOSSIER-") and "dossiers/persons/" in rel:
        return (10, "consolidation")

    # 5. Agent files
    if fname in AGENT_FILE_ROLES and "/agents/" in rel:
        return (10, "consolidation")

    # 6. Source theme docs (in knowledge/*/sources/ but not the shared artifacts)
    if (
        "/sources/" in rel
        and fname not in ("CHUNKS-STATE.json", "CANONICAL-MAP.json", "INSIGHTS-STATE.json")
        and (fname.endswith(".md") or fname.endswith(".yaml"))
    ):
        return (10, "consolidation")

    # 7. Chunks
    if rel.endswith("artifacts/chunks/CHUNKS-STATE.json"):
        return (3, "chunking")

    # 8. Canonical map
    if rel.endswith("artifacts/canonical/CANONICAL-MAP.json"):
        return (4, "entity_resolution")

    # 9. Insights (differentiate by content)
    if rel.endswith("artifacts/insights/INSIGHTS-STATE.json"):
        return (-1, "_insights_detect")  # caller resolves to 5/6/7

    return None


def _detect_insights_step(data: dict) -> tuple[int, str]:
    """Differentiate Steps 5/6/7 from INSIGHTS-STATE content."""
    # Check at top level and inside persons
    persons = data.get("persons", {})
    any_person: dict = {}
    if isinstance(persons, dict) and persons:
        first = next(iter(persons.values()), {})
        any_person = first if isinstance(first, dict) else {}

    # Step 7: value_hierarchy present (added last, most specific)
    if data.get("value_hierarchy") or any_person.get("value_hierarchy"):
        return (7, "mce_identity")

    # Step 6: behavioral_patterns present
    if data.get("behavioral_patterns") or any_person.get("behavioral_patterns"):
        return (6, "mce_behavioral")

    # Step 5: insights arrays present
    return (5, "insight_extraction")


# ─────────────────────────────────────────────────────────────────────────────
# METRIC EXTRACTORS
# ─────────────────────────────────────────────────────────────────────────────


def _metrics_step3(data: Any) -> tuple[dict, dict]:
    chunks = []
    if isinstance(data, dict):
        chunks = data.get("chunks", [])
    elif isinstance(data, list):
        chunks = data

    words = []
    persons_set: set[str] = set()
    sources_set: set[str] = set()
    all_ids = True

    for c in chunks:
        if not isinstance(c, dict):
            continue
        text = c.get("text", "")
        words.append(len(text.split()))
        for f in ("speaker", "person", "persona"):
            val = c.get(f, "")
            if val:
                persons_set.add(str(val))
        src = c.get("source_file", c.get("source", ""))
        if src:
            sources_set.add(str(src))
        if not c.get("id_chunk") and not c.get("id"):
            all_ids = False

    total_w = sum(words)
    avg_w   = round(total_w / max(len(words), 1))

    m = {
        "chunks_created":         len(chunks),
        "avg_chunk_words":        avg_w,
        "total_tokens_estimate":  round(total_w * 1.3),
        "persons_detected":       sorted(persons_set),
        "source_files_processed": len(sources_set),
        "word_counts_distribution": {
            "lt_200":       sum(1 for w in words if w < 200),
            "btw_200_350":  sum(1 for w in words if 200 <= w <= 350),
            "gt_350":       sum(1 for w in words if w > 350),
        },
    }
    v = {
        "has_chunks":          len(chunks) > 0,
        "all_chunks_have_ids": all_ids,
        "chunk_count":         len(chunks),
    }
    return m, v


def _metrics_step4(data: Any, slug: str) -> tuple[dict, dict]:
    entities: dict = {}
    if isinstance(data, dict):
        entities = data.get("entities", data)

    total_e, total_v = 0, 0
    top: list[str] = []
    for key, val in entities.items():
        if isinstance(val, list):
            total_e += 1
            total_v += len(val)
            top.append(str(key))
        elif isinstance(val, dict) and "variants" in val:
            total_e += 1
            total_v += len(val.get("variants", []))
            top.append(str(key))

    prev = _read_last_entry(4, slug)
    prev_e = prev.get("metrics", {}).get("total_entities", 0) if prev else 0
    prev_v = prev.get("metrics", {}).get("total_variants", 0) if prev else 0

    m = {
        "total_entities":    total_e,
        "total_variants":    total_v,
        "new_entities_added": total_e - prev_e if prev else total_e,
        "new_variants_added": total_v - prev_v if prev else total_v,
        "top_entities":      top[:5],
    }
    v = {
        "has_entities":  total_e > 0,
        "entity_count":  total_e,
    }
    return m, v


def _metrics_step5(data: dict) -> tuple[dict, dict]:
    persons    = data.get("persons", {})
    total_ins  = 0
    by_prio:   dict[str, int] = {}
    by_tag:    dict[str, int] = {}
    chunk_refs = True

    if isinstance(persons, dict):
        for _name, pdata in persons.items():
            ins_list = pdata.get("insights", []) if isinstance(pdata, dict) else \
                       (pdata if isinstance(pdata, list) else [])
            total_ins += len(ins_list)
            for ins in ins_list:
                if not isinstance(ins, dict):
                    continue
                p = ins.get("priority", "UNKNOWN")
                by_prio[p] = by_prio.get(p, 0) + 1
                t = ins.get("tag", "UNKNOWN")
                by_tag[t] = by_tag.get(t, 0) + 1
                if not ins.get("chunk_id") and not ins.get("chunk_ids"):
                    chunk_refs = False

    m = {
        "total_insights":        total_ins,
        "by_priority":           by_prio,
        "by_dna_tag":            by_tag,
        "persons_with_insights": len(persons) if isinstance(persons, dict) else 0,
    }
    v = {
        "has_persons":              len(persons) > 0 if isinstance(persons, dict) else False,
        "has_insights":             total_ins > 0,
        "insights_have_chunk_refs": chunk_refs,
        "insight_count":            total_ins,
    }
    return m, v


def _metrics_step6(data: dict) -> tuple[dict, dict]:
    patterns: list = data.get("behavioral_patterns", [])
    if not patterns:
        persons = data.get("persons", {})
        if isinstance(persons, dict):
            for pdata in persons.values():
                if isinstance(pdata, dict):
                    patterns.extend(pdata.get("behavioral_patterns", []))

    by_type:    dict[str, int] = {}
    with_evid   = 0
    total_chunks = 0

    for p in patterns:
        if not isinstance(p, dict):
            continue
        ptype = p.get("type", "unknown")
        by_type[ptype] = by_type.get(ptype, 0) + 1
        cids = p.get("chunk_ids", p.get("chunks", []))
        if len(cids) >= 2:
            with_evid += 1
        total_chunks += len(cids)

    m = {
        "total_patterns":       len(patterns),
        "by_type":              by_type,
        "patterns_with_evidence": with_evid,
        "avg_evidence_chunks":  round(total_chunks / max(len(patterns), 1), 1),
    }
    v = {
        "has_behavioral_patterns":        len(patterns) > 0,
        "all_patterns_have_2plus_chunks":  with_evid == len(patterns) and len(patterns) > 0,
        "pattern_count":                  len(patterns),
    }
    return m, v


def _metrics_step7(data: dict) -> tuple[dict, dict]:
    values     = data.get("value_hierarchy", [])
    obsessions = data.get("obsessions", [])
    paradoxes  = data.get("paradoxes", [])

    if not values:
        persons = data.get("persons", {})
        if isinstance(persons, dict):
            for pdata in persons.values():
                if isinstance(pdata, dict):
                    if not values:      values     = pdata.get("value_hierarchy", [])
                    if not obsessions:  obsessions = pdata.get("obsessions", [])
                    if not paradoxes:   paradoxes  = pdata.get("paradoxes", [])

    tier1    = sum(1 for v in values if isinstance(v, dict) and v.get("tier") == 1)
    tier2    = sum(1 for v in values if isinstance(v, dict) and v.get("tier") == 2)
    masters  = sum(1 for o in obsessions if isinstance(o, dict)
                   and str(o.get("status", "")).upper() == "MASTER")
    prod     = sum(1 for p in paradoxes if isinstance(p, dict) and p.get("productive"))

    top_vals = []
    for v in values[:3]:
        if isinstance(v, dict):
            top_vals.append(v.get("name", v.get("value", "?")))

    master_names = [o.get("name", "?") for o in obsessions
                    if isinstance(o, dict) and str(o.get("status","")).upper() == "MASTER"]

    m = {
        "values_count":       len(values),
        "tier1_count":        tier1,
        "tier2_count":        tier2,
        "obsessions_count":   len(obsessions),
        "master_obsessions":  masters,
        "paradoxes_count":    len(paradoxes),
        "productive_paradoxes": prod,
        "top_values":         top_vals,
        "master_obsession":   master_names[0] if master_names else "—",
    }
    v = {
        "has_value_hierarchy": len(values) > 0,
        "has_tier1_value":     tier1 > 0,
        "has_obsessions":      len(obsessions) > 0,
        "exactly_one_master":  masters == 1,
        "has_paradoxes":       len(paradoxes) > 0,
    }
    return m, v


def _metrics_step8(data: dict) -> tuple[dict, dict]:
    tone_data = data.get("tone_profile", data.get("tone", {}))
    tone      = {}
    if isinstance(tone_data, dict):
        for key, _ in TONE_DIMS:
            val = tone_data.get(key)
            if val is not None:
                tone[key] = val

    phrases  = data.get("signature_phrases", [])
    states   = data.get("behavioral_states", [])
    forbidden = data.get("forbidden_patterns", data.get("forbidden_words", []))
    samples  = [p if isinstance(p, str) else p.get("phrase", str(p)) for p in phrases[:3]]

    m = {
        "tone_dimensions_defined": len(tone),
        "signature_phrases":       len(phrases),
        "behavioral_states":       len(states),
        "forbidden_patterns":      len(forbidden) if isinstance(forbidden, list) else 0,
        "tone_profile":            tone,
        "sample_phrases":          samples,
    }
    v = {
        "has_tone_profile":        len(tone) > 0,
        "has_signature_phrases":   len(phrases) > 0,
        "signature_phrases_gte_5": len(phrases) >= 5,
        "has_behavioral_states":   len(states) > 0,
        "tone_dimensions_complete": len(tone) == 6,
    }
    return m, v


def _metrics_step9(data: dict) -> tuple[dict, dict]:
    history = data.get("history", [])
    state   = data.get("state", "")
    decision, prev_state = "UNKNOWN", ""

    for entry in reversed(history):
        if not isinstance(entry, dict):
            continue
        if entry.get("to") == "consolidation" and entry.get("from") == "identity_checkpoint":
            decision, prev_state = "APPROVE", "identity_checkpoint"
            break
        if entry.get("from") == "identity_checkpoint":
            decision, prev_state = "REVISE", "identity_checkpoint"
            break

    m = {
        "decision":          decision,
        "previous_state":    prev_state,
        "new_state":         state,
        "total_transitions": len(history),
    }
    v = {"checkpoint_resolved": decision != "UNKNOWN"}
    return m, v


def _metrics_step10(rel: str, abs_path: Path) -> tuple[dict, dict]:
    fname    = Path(rel).name
    size     = abs_path.stat().st_size if abs_path.exists() else 0
    m: dict  = {}
    v: dict  = {}

    if fname.startswith("DOSSIER-") and "dossiers/persons/" in rel:
        m = {"substep": "10.1_dossier", "label": fname, "dossier_path": rel, "file_size_bytes": size}
        v = {"has_dossier": abs_path.exists()}

    elif fname in DNA_YAML_LAYERS:
        m = {"substep": "10.3_dna_yaml", "label": f"DNA › {fname}", "yaml_name": fname, "file_size_bytes": size}
        v = {"has_dna_yaml": abs_path.exists()}

    elif fname in AGENT_FILE_ROLES:
        m = {"substep": "10.4_agent", "label": f"Agent › {fname}", "agent_file": fname, "file_size_bytes": size}
        v = {"has_agent_file": abs_path.exists()}

    elif "/sources/" in rel:
        m = {"substep": "10.2_sources", "label": f"Source › {fname}", "source_doc": fname, "file_size_bytes": size}
        v = {"has_source_doc": abs_path.exists()}

    else:
        m = {"substep": "10.x_other", "label": fname, "file": fname, "file_size_bytes": size}
        v = {"file_exists": abs_path.exists()}

    return m, v


# ─────────────────────────────────────────────────────────────────────────────
# MAIN HOOK ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    def _noop() -> None:
        print(json.dumps({"continue": True, "feedback": None}))
        sys.exit(0)

    try:
        raw = sys.stdin.read()
        if not raw.strip():
            _noop()

        event      = json.loads(raw)
        tool_name  = event.get("tool_name", "")
        tool_input = event.get("tool_input", {})

        if tool_name not in ("Write", "Edit"):
            _noop()

        file_path = tool_input.get("file_path", "")
        if not file_path:
            _noop()

        rel      = _to_relative(file_path)
        abs_path = Path(file_path).resolve()

        match = _match_artifact(rel)
        if match is None:
            _noop()

        step, step_name = match
        slug   = _detect_slug(rel)
        bucket = _detect_bucket(rel)

        # ── Resolve insights step (5/6/7) ──────────────────────────────────
        if step == -1:
            data = _read_json(abs_path)
            if data is None or not isinstance(data, dict):
                _noop()
            step, step_name = _detect_insights_step(data)  # type: ignore[arg-type]

        # ── Step 9: only log on actual checkpoint transition ────────────────
        if step == 9:
            data = _read_yaml(abs_path)
            if not data:
                _noop()
            history = data.get("history", [])
            if not history:
                _noop()
            last = history[-1] if history else {}
            if last.get("from") != "identity_checkpoint":
                _noop()

        # ── Step 8: only VOICE-DNA.yaml ─────────────────────────────────────
        if step == 8 and Path(rel).name != "VOICE-DNA.yaml":
            _noop()

        # ── Extract metrics ──────────────────────────────────────────────────
        m: dict = {}
        v: dict = {}

        if step == 3:
            d = _read_json(abs_path)
            if d is not None:
                m, v = _metrics_step3(d)

        elif step == 4:
            d = _read_json(abs_path)
            if d is not None:
                m, v = _metrics_step4(d, slug)

        elif step == 5:
            d = _read_json(abs_path)
            if isinstance(d, dict):
                m, v = _metrics_step5(d)

        elif step == 6:
            d = _read_json(abs_path)
            if isinstance(d, dict):
                m, v = _metrics_step6(d)

        elif step == 7:
            d = _read_json(abs_path)
            if isinstance(d, dict):
                m, v = _metrics_step7(d)

        elif step == 8:
            d = _read_yaml(abs_path)
            if isinstance(d, dict):
                m, v = _metrics_step8(d)

        elif step == 9:
            d = _read_yaml(abs_path)
            if isinstance(d, dict):
                m, v = _metrics_step9(d)

        elif step == 10:
            m, v = _metrics_step10(rel, abs_path)

        # ── Write JSONL entry ────────────────────────────────────────────────
        entry: dict[str, Any] = {
            "timestamp":    _now_iso(),
            "step":         step,
            "step_name":    step_name,
            "slug":         slug,
            "bucket":       bucket,
            "artifact_path": rel,
            "metrics":      m,
            "validation":   v,
        }
        _append_jsonl(entry)

        # ── Build ASCII panel ─────────────────────────────────────────────
        panel = _build_panel(step, step_name, slug, rel, bucket, m, v)

        print(json.dumps({"continue": True, "feedback": panel}))
        sys.exit(0)

    except Exception:
        # Logging MUST NEVER block pipeline execution
        print(json.dumps({"continue": True, "feedback": None}))
        sys.exit(0)


if __name__ == "__main__":
    main()
