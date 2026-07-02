#!/usr/bin/env python3
"""
render_dispatcher.py -- Chronicler Render Dispatcher
=====================================================
Orchestrates ASCII template rendering via Sonnet subprocess with
deterministic Python fallback.

Renders the 7 MCE Output Templates defined in:
    core/templates/output/MCE-OUTPUT-TEMPLATES.md

Uses the Chronicler Design System (DESIGN-TOKENS.json) for dimensions,
characters, and box-drawing conventions.

Public API
----------
- ``render_template(render_context, mode, output_path)``  -- Main entry
- ``render_all(slug, mode)``                               -- All templates

Internal
--------
- ``_render_via_sonnet(render_context, template_text)``    -- Sonnet subprocess
- ``_render_via_python(render_context, template_id)``      -- Python fallback
- ``_load_template(template_id)``                          -- Template extractor
- ``_validate_output(rendered)``                           -- Output validator

CLI
---
::

    python3 render_dispatcher.py render --context /tmp/ctx.json --output /tmp/out.md
    python3 render_dispatcher.py render-all --slug process-architect
    python3 render_dispatcher.py render --context /tmp/ctx.json --mode python

Constraints
~~~~~~~~~~~
- Python 3, stdlib + subprocess only (no PyYAML, no core/ imports).
- Never raises fatally -- always produces some output.
- Does NOT use --dangerously-skip-permissions for Sonnet calls.

Version: 1.0.0
Date: 2026-03-20
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# PATH SETUP -- reach project root for data collector imports and template access
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parents[2]  # .claude/skills/chronicler -> project root
sys.path.insert(0, str(_PROJECT_ROOT))

# Template file locations (relative to project root)
_TEMPLATES_PATH = _PROJECT_ROOT / "core" / "templates" / "output" / "MCE-OUTPUT-TEMPLATES.md"
_DESIGN_TOKENS_PATH = _PROJECT_ROOT / "core" / "templates" / "chronicler" / "DESIGN-TOKENS.json"
_LOGS_DIR = _PROJECT_ROOT / "logs" / "mce"

# ---------------------------------------------------------------------------
# CHRONICLER DESIGN TOKENS (inline fallbacks if JSON unavailable)
# ---------------------------------------------------------------------------

W = 120       # Full width
W1 = 112      # Level 1 (double border)
W2 = 106      # Level 2 (single border)

SOLID = "\u2588"        # Block: solid
BAR_FILL = "\u2593"     # Block: dark shade
BAR_EMPTY = "\u2591"    # Block: light shade
HEADER_BAR = "\u2580"   # Block: upper half
BULLET = "\u25b8"       # Decorator: bullet

SOLID_LINE = SOLID * W
DOUBLE_LINE = "\u2550" * W1
SINGLE_LINE = "\u2500" * W2


# =========================================================================
# PRIMITIVES (Python fallback rendering helpers)
# =========================================================================


def _bar(pct: float, width: int = 30) -> str:
    """Generate a progress bar: (filled)(empty) N%"""
    filled = int(pct / 100 * width)
    return BAR_FILL * filled + BAR_EMPTY * (width - filled) + f" {int(pct)}%"


def _pad(text: str, width: int, pad_char: str = " ") -> str:
    """Pad text to exact width, truncating if needed."""
    if len(text) >= width:
        return text[:width]
    return text + pad_char * (width - len(text))


def _box_line(content: str, border: str = "\u2551", inner_width: int = W1) -> str:
    """Create a bordered line: (vert)(space)(content padded)(space)(vert)"""
    padded = _pad(f"  {content}", inner_width - 2)
    return f"{border} {padded} {border}"


def _inner_box_line(content: str, inner_width: int = W2) -> str:
    """Create inner box line with double outer + single inner borders."""
    padded = _pad(f"  {content}", inner_width - 4)
    return f"\u2551    \u2502 {padded} \u2502    \u2551"


def _nested_box(title: str, content_lines: list[str]) -> list[str]:
    """Chronicler nested box: double outer + single inner."""
    lines = [
        f"\u2554{'\u2550' * W1}\u2557",
        _box_line(""),
        _box_line(f"{BULLET} {title}"),
        _box_line(""),
        f"\u2551    \u250c{'\u2500' * W2}\u2510    \u2551",
        _box_line(""),
    ]
    for cl in content_lines:
        lines.append(_inner_box_line(cl))
    lines.append(_box_line(""))
    lines.append(f"\u2551    \u2514{'\u2500' * W2}\u2518    \u2551")
    lines.append(_box_line(""))
    lines.append(f"\u255a{'\u2550' * W1}\u255d")
    return lines


def _super_header(tag: str, person_name: str, status: str, now: str) -> list[str]:
    """Chronicler super_header with solid blocks."""
    title = "M C E   P I P E L I N E   L O G"
    subtitle = f"{person_name}  ({tag})  \u00b7  {status}  \u00b7  {now}"
    return [
        SOLID_LINE,
        SOLID_LINE,
        f"\u2588\u2588\u2588\u2588{_pad('', W - 8)}\u2588\u2588\u2588\u2588",
        f"\u2588\u2588\u2588\u2588     {_pad(title, W - 14)}\u2588\u2588\u2588\u2588",
        f"\u2588\u2588\u2588\u2588{_pad('', W - 8)}\u2588\u2588\u2588\u2588",
        f"\u2588\u2588\u2588\u2588          \u2554{_pad('', 86, '\u2550')}\u2557          \u2588\u2588\u2588\u2588",
        f"\u2588\u2588\u2588\u2588          \u2551  {_pad(subtitle, 84)}\u2551          \u2588\u2588\u2588\u2588",
        f"\u2588\u2588\u2588\u2588          \u255a{_pad('', 86, '\u2550')}\u255d          \u2588\u2588\u2588\u2588",
        f"\u2588\u2588\u2588\u2588{_pad('', W - 8)}\u2588\u2588\u2588\u2588",
        SOLID_LINE,
        SOLID_LINE,
    ]


def _section_header(num: int, emoji: str, title: str) -> list[str]:
    """Chronicler section header with upper-half-block bars."""
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
        f"\u250f{'\u2501' * (W - 2)}\u2513",
        f"\u2503{_pad('', W - 2)}\u2503",
        f"\u2503{_pad('                    O QUE MUDOU NESTA EXECUCAO', W - 2)}\u2503",
        f"\u2503{_pad('', W - 2)}\u2503",
    ]
    for change in changes:
        lines.append(f"\u2503   {BULLET} {_pad(change, W - 7)}\u2503")
    lines.append(f"\u2503{_pad('', W - 2)}\u2503")
    lines.append(f"\u2517{'\u2501' * (W - 2)}\u251b")
    return lines


def _metric_grid(metrics: list[tuple[str, str, str]]) -> list[str]:
    """Chronicler metric_grid: list of (value, label, explanation)."""
    per_row = min(len(metrics), 4)
    card_w = 24

    lines = [
        f"\u256d{'\u2500' * (W - 2)}\u256e",
        f"\u2502{_pad('                                    PAINEL DE METRICAS', W - 2)}\u2502",
        f"\u2502{_pad('', W - 2)}\u2502",
    ]

    for row_start in range(0, len(metrics), 4):
        row = metrics[row_start:row_start + 4]
        card_tops = "   ".join(f"\u250c{'\u2500' * card_w}\u2510" for _ in row)
        lines.append(f"\u2502   {_pad(card_tops, W - 5)}\u2502")
        card_vals = "   ".join(f"\u2502{_pad(m[0], card_w, ' ').center(card_w)}\u2502" for m in row)
        lines.append(f"\u2502   {_pad(card_vals, W - 5)}\u2502")
        card_lbls = "   ".join(f"\u2502{_pad(m[1], card_w, ' ').center(card_w)}\u2502" for m in row)
        lines.append(f"\u2502   {_pad(card_lbls, W - 5)}\u2502")
        card_exps = "   ".join(f"\u2502{_pad('[' + m[2] + ']', card_w, ' ').center(card_w)}\u2502" for m in row)
        lines.append(f"\u2502   {_pad(card_exps, W - 5)}\u2502")
        card_bots = "   ".join(f"\u2514{'\u2500' * card_w}\u2518" for _ in row)
        lines.append(f"\u2502   {_pad(card_bots, W - 5)}\u2502")

    lines.append(f"\u2502{_pad('', W - 2)}\u2502")
    lines.append(f"\u2570{'\u2500' * (W - 2)}\u256f")
    return lines


def _chronicler_notes(observations: list[str]) -> list[str]:
    """Chronicler notes section."""
    lines = [
        f"\u2554{'\u2550' * (W - 2)}\u2557",
        f"\u2551{_pad('', W - 2)}\u2551",
        f"\u2551{_pad('                         NOTAS DO CHRONICLER', W - 2)}\u2551",
        f"\u2551{_pad('', W - 2)}\u2551",
    ]
    for obs in observations:
        lines.append(f"\u2551   {_pad(obs, W - 5)}\u2551")
    lines.append(f"\u2551{_pad('', W - 2)}\u2551")
    lines.append(f"\u2551{_pad('                                                          -- Chronicler', W - 2)}\u2551")
    lines.append(f"\u2551{_pad('', W - 2)}\u2551")
    lines.append(f"\u255a{'\u2550' * (W - 2)}\u255d")
    return lines


def _footer(title: str, version: str, date: str) -> list[str]:
    """Chronicler footer with solid blocks."""
    return [
        "",
        SOLID_LINE,
        f"\u2588\u2588\u2588\u2588{_pad('', W - 8)}\u2588\u2588\u2588\u2588",
        f"\u2588\u2588\u2588\u2588{_pad(title.center(W - 8), W - 8)}\u2588\u2588\u2588\u2588",
        f"\u2588\u2588\u2588\u2588{_pad(f'{version} | {date}'.center(W - 8), W - 8)}\u2588\u2588\u2588\u2588",
        f"\u2588\u2588\u2588\u2588{_pad('', W - 8)}\u2588\u2588\u2588\u2588",
        SOLID_LINE,
    ]


# =========================================================================
# TEMPLATE LOADER
# =========================================================================


def _load_template(template_id: int) -> str:
    """Extract a specific template from MCE-OUTPUT-TEMPLATES.md.

    Finds the ``## N.`` header for the given template_id, then extracts
    the content between the next pair of triple-backtick code fences.

    Args:
        template_id: Template number (1-7).

    Returns:
        Raw template text (without the enclosing backtick lines), or
        empty string if the template cannot be found.
    """
    if not _TEMPLATES_PATH.exists():
        return ""

    try:
        content = _TEMPLATES_PATH.read_text(encoding="utf-8")
    except Exception:
        return ""

    # Find the header line for this template: "## N. TITLE"
    # Pattern matches "## 1." or "## 7." etc at line start
    header_pattern = re.compile(rf"^## {template_id}\.\s", re.MULTILINE)
    header_match = header_pattern.search(content)
    if not header_match:
        return ""

    # From the header position, find the next code fence block
    rest = content[header_match.start():]

    # Find opening ``` (the line must be just ```)
    fence_pattern = re.compile(r"^```\s*$", re.MULTILINE)
    fences = list(fence_pattern.finditer(rest))

    if len(fences) < 2:
        return ""

    # Extract content between first and second fence
    start = fences[0].end()
    end = fences[1].start()
    template_text = rest[start:end].strip()

    return template_text


# =========================================================================
# OUTPUT VALIDATOR
# =========================================================================


_BOX_CHARS = set("\u2554\u2557\u255a\u255d\u2550\u2551\u250c\u2510\u2514\u2518\u2500\u2502\u2593\u2591\u2588")


def _validate_output(rendered: str) -> bool:
    """Check if rendered output looks like valid ASCII art.

    Validates:
        - Contains box-drawing characters
        - No line exceeds 120 characters (Chronicler width contract)

    Args:
        rendered: The rendered template string.

    Returns:
        True if the output passes validation checks.
    """
    if not rendered or len(rendered) < 50:
        return False

    # Check for box-drawing characters
    has_box_chars = any(c in _BOX_CHARS for c in rendered)
    if not has_box_chars:
        return False

    # Check width constraint (120 chars max per line)
    for line in rendered.split("\n"):
        # Allow slight overshoot for emoji characters (they take 2 display columns)
        if len(line) > 130:
            return False

    return True


# =========================================================================
# SONNET RENDERER
# =========================================================================


_SONNET_SYSTEM_PROMPT = (
    "You are a deterministic ASCII template renderer. "
    "Fill ALL {PLACEHOLDER} variables with data from the JSON context. "
    "Generate progress bars using \u2593 and \u2591. "
    "Preserve box-drawing characters exactly "
    "(\u2554\u2550\u2557\u2551\u255a\u2550\u255d\u250c\u2500\u2510\u2502\u2514\u2500\u2518). "
    "Follow the Chronicler Design System: width 120 chars, mandatory "
    "super_header + changes_box + chronicler_notes + footer. "
    "Return ONLY the rendered ASCII output, nothing else."
)


def _render_via_sonnet(render_context: dict[str, Any], template_text: str) -> str:
    """Render a template by spawning ``claude -p --model sonnet``.

    Passes the template and JSON context as a prompt. Timeout: 30s.
    Does NOT use ``--dangerously-skip-permissions`` (Sonnet only formats
    text, no file I/O needed).

    Args:
        render_context: The data context dict.
        template_text: Raw template with {PLACEHOLDER} variables.

    Returns:
        Rendered ASCII string, or empty string on failure.
    """
    context_json = json.dumps(render_context, indent=2, ensure_ascii=False, default=str)

    prompt = (
        f"Render the following ASCII template by replacing all "
        f"{{PLACEHOLDER}} variables with data from the JSON context below.\n\n"
        f"--- TEMPLATE ---\n{template_text}\n--- END TEMPLATE ---\n\n"
        f"--- JSON CONTEXT ---\n{context_json}\n--- END JSON CONTEXT ---\n\n"
        f"Rules:\n"
        f"- Replace every {{PLACEHOLDER}} with the corresponding value from the context.\n"
        f"- Generate progress bars using \u2593 (filled) and \u2591 (empty).\n"
        f"- Preserve ALL box-drawing characters exactly as they appear.\n"
        f"- If a value is missing from the context, use a sensible default (0, N/A, or empty).\n"
        f"- Output ONLY the rendered template. No explanations, no markdown fences, no comments.\n"
    )

    try:
        result = subprocess.run(
            ["claude", "-p", "--model", "sonnet"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return ""
    except FileNotFoundError:
        # claude CLI not available
        return ""
    except subprocess.TimeoutExpired:
        return ""
    except Exception:
        return ""


# =========================================================================
# PYTHON FALLBACK RENDERER
# =========================================================================


def _render_via_python(render_context: dict[str, Any], template_id: int) -> str:
    """Pure Python fallback renderer using log_generator.py primitives.

    Produces a simpler but correct rendering with:
    super_header, metrics section, changes section, footer.

    Args:
        render_context: The data context dict.
        template_id: Template number (1-7).

    Returns:
        Rendered ASCII string. Always produces output (never empty).
    """
    ctx = render_context or {}
    slug = ctx.get("slug", "unknown")
    person_name = ctx.get("person_name", slug.replace("-", " ").title())
    tag = _make_tag(slug)
    now = ctx.get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
    template_id = ctx.get("template_id", template_id)
    bucket = ctx.get("bucket", "external")

    metrics = ctx.get("metrics", {})
    dna = ctx.get("dna", {})
    validation = ctx.get("validation", {})
    deltas = ctx.get("deltas", {})
    progress = ctx.get("progress", {})
    insights = ctx.get("insights", {})

    # Template name mapping
    template_names = {
        1: "EXTRACTION SUMMARY",
        2: "PERSON AGENT",
        3: "CARGO AGENT ENRICHMENT",
        4: "THEME DOSSIER",
        5: "WORKSPACE SYNC",
        6: "VALIDATION GATE",
        7: "SESSION CONSOLIDATION",
    }
    template_name = template_names.get(template_id, f"TEMPLATE {template_id}")

    # Step mapping
    template_steps = {
        1: "STEP 03-05",
        2: "STEP 10",
        3: "STEP 10",
        4: "STEP 10",
        5: "STEP 11",
        6: "STEP 12",
        7: "SESSION",
    }
    step_label = template_steps.get(template_id, f"STEP {template_id}")

    # Bucket icons
    bucket_icons = {
        "external": "EXTERNAL",
        "business": "BUSINESS",
        "personal": "PERSONAL",
    }
    bucket_label = bucket_icons.get(bucket, bucket.upper())

    lines: list[str] = []

    # -- SUPER HEADER --
    status = metrics.get("pipeline_status", "RENDERING")
    lines.extend(_super_header(tag, person_name, status.upper(), now))
    lines.append("")

    # -- CHANGES BOX --
    chunks_count = metrics.get("chunks_count", 0)
    person_insights_count = metrics.get("person_insights", insights.get("person", 0))
    dna_total = dna.get("total", 0)
    phases_completed = metrics.get("phases_completed", progress.get("phases_completed", 0))

    changes = [
        f"Template: {template_name} ({step_label})",
        f"Pessoa: {person_name} | Bucket: {bucket_label}",
        f"{person_insights_count} insights extraidos",
        f"{dna_total} elementos DNA (5 camadas)",
        f"{chunks_count} chunks processados",
        f"Pipeline: {phases_completed}/5 fases completas",
    ]
    lines.extend(_changes_box(changes))
    lines.append("")

    # -- METRICS SECTION --
    lines.extend(_section_header(1, ">>", f"{template_name} METRICS"))

    lines.extend(_metric_grid([
        (str(chunks_count), "CHUNKS", "Segmentos semanticos"),
        (str(person_insights_count), "INSIGHTS", "Conhecimento acionavel"),
        (str(dna_total), "DNA ELEMENTS", "5 camadas cognitivas"),
        (str(phases_completed), "PHASES", "Etapas do pipeline"),
    ]))
    lines.append("")

    # -- DNA BREAKDOWN (if available) --
    if dna_total > 0:
        fil = dna.get("FILOSOFIAS", 0)
        mm = dna.get("MODELOS_MENTAIS", 0)
        heu = dna.get("HEURISTICAS", 0)
        fw = dna.get("FRAMEWORKS", 0)
        met = dna.get("METODOLOGIAS", 0)

        def _pct(v: int) -> float:
            return v / dna_total * 100 if dna_total else 0

        lines.extend(_nested_box("DNA BREAKDOWN POR CAMADA", [
            f"L1 Filosofias:      {fil:>3}  {_bar(_pct(fil), 20)}",
            f"L2 Modelos Mentais: {mm:>3}  {_bar(_pct(mm), 20)}",
            f"L3 Heuristicas:     {heu:>3}  {_bar(_pct(heu), 20)}",
            f"L4 Frameworks:      {fw:>3}  {_bar(_pct(fw), 20)}",
            f"L5 Metodologias:    {met:>3}  {_bar(_pct(met), 20)}",
            "",
            f"TOTAL:              {dna_total:>3}  elementos",
        ]))
        lines.append("")

    # -- TEMPLATE-SPECIFIC SECTION --
    if template_id == 1:
        # Extraction summary -- show files processed
        sources = ctx.get("files", {}).get("sources_processed", [])
        sources_count = deltas.get("sources_count", len(sources))
        lines.extend(_nested_box("EXTRACTION DETAILS", [
            f"Fontes processadas: {sources_count}",
            f"Chunks gerados:     {chunks_count}",
            f"Insights extraidos: {person_insights_count}",
            f"DNA total:          {dna_total} elementos",
        ]))
        lines.append("")

    elif template_id == 2:
        # Person agent
        agent_exists = deltas.get("agent_exists", ctx.get("files", {}).get("agent_exists", False))
        agent_files = deltas.get("agent_files", [])
        agent_lines = [
            f"Agent existe: {'SIM' if agent_exists else 'NAO'}",
            f"Arquivos do agente: {len(agent_files)}",
        ]
        for af in agent_files[:6]:
            agent_lines.append(f"  {BULLET} {af}")
        lines.extend(_nested_box("PERSON AGENT DETAILS", agent_lines))
        lines.append("")

    elif template_id == 3:
        # Cargo enrichment
        cargo_count = deltas.get("cargo_count", 0)
        lines.extend(_nested_box("CARGO AGENT ENRICHMENT", [
            f"Cargo agents encontrados: {cargo_count}",
        ]))
        lines.append("")

    elif template_id == 4:
        # Theme dossier
        dossier_exists = deltas.get("dossier_exists", False)
        dossier_file = deltas.get("dossier_file", "N/A")
        lines.extend(_nested_box("THEME DOSSIER DETAILS", [
            f"Dossier existe: {'SIM' if dossier_exists else 'NAO'}",
            f"Arquivo: {dossier_file}",
        ]))
        lines.append("")

    elif template_id == 5:
        # Workspace sync
        lines.extend(_nested_box("WORKSPACE SYNC RESULTS", [
            f"Status: Sync pendente de execucao",
        ]))
        lines.append("")

    elif template_id == 6:
        # Validation gate
        v = validation
        check_items = [
            (f"Chunks OK", v.get("chunks_ok", False)),
            (f"Insights OK", v.get("insights_ok", False)),
            (f"DNA OK", v.get("dna_ok", False)),
            (f"Metadata OK", v.get("metadata_ok", False)),
            (f"Metrics OK", v.get("metrics_ok", False)),
        ]
        check_lines = []
        for name, passed in check_items:
            icon = "[PASS]" if passed else "[FAIL]"
            check_lines.append(f"{icon} {name}")
        passed_count = sum(1 for _, p in check_items if p)
        total = len(check_items)
        check_lines.append("")
        check_lines.append(f"RESULTADO: {passed_count}/{total} checks  {_bar(passed_count / total * 100 if total else 0, 20)}")
        lines.extend(_nested_box("VALIDATION GATE", check_lines))
        lines.append("")

    elif template_id == 7:
        # Session consolidation
        session_data = ctx.get("session", ctx)
        slugs = session_data.get("slugs_processed", [slug])
        lines.extend(_nested_box("SESSION CONSOLIDATION", [
            f"Slugs processados: {', '.join(slugs) if slugs else slug}",
            f"Total steps: {session_data.get('total_steps', 0)}",
            f"Agents: {session_data.get('agents_count', 0)}",
            f"Dossiers: {session_data.get('dossiers_count', 0)}",
        ]))
        lines.append("")

    # -- PIPELINE PROGRESS --
    pct = progress.get("percentage", 0)
    total_phases = progress.get("total_phases", 5)
    completed_phases = progress.get("phases_completed", 0)
    lines.extend(_nested_box("PIPELINE PROGRESS", [
        f"{completed_phases}/{total_phases} phases  [{pct}%]",
        f"{_bar(pct, 30)}",
    ]))
    lines.append("")

    # -- CHRONICLER NOTES --
    notes = [
        f"Template {template_id} ({template_name}) renderizado via Python fallback.",
        f"Pessoa: {person_name} | Slug: {slug} | Tag: {tag}",
        f"Chronicler Design System v1.0.0 | render_dispatcher.py v1.0.0",
    ]
    lines.extend(_chronicler_notes(notes))

    # -- FOOTER --
    lines.extend(_footer(
        f"MCE TEMPLATE {template_id} -- {person_name} ({tag})",
        "v1.0.0",
        now,
    ))
    lines.append("")

    return "\n".join(lines)


def _make_tag(slug: str) -> str:
    """Generate a short tag from slug (e.g. 'process-architect' -> 'PA')."""
    parts = slug.split("-")
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return slug[:2].upper() if slug else "XX"


# =========================================================================
# MAIN ENTRY POINT
# =========================================================================


def render_template(
    render_context: dict[str, Any],
    mode: str = "auto",
    output_path: str | None = None,
) -> dict[str, Any]:
    """Render an MCE output template.

    Main entry point. Delegates to Sonnet subprocess or Python fallback
    depending on ``mode``.

    Args:
        render_context: Data context dict (from ``collect_checkpoint_data()``).
            Must include at least ``template_id`` and ``slug``.
        mode: Rendering mode.
            - ``"auto"``   -- Try Sonnet first, fall back to Python.
            - ``"sonnet"`` -- Sonnet only (returns error if unavailable).
            - ``"python"`` -- Python fallback only (no subprocess).
        output_path: Optional path to write the rendered output.

    Returns:
        Dict with keys:
        - ``rendered`` (str): The rendered ASCII text.
        - ``output_path`` (str): Where the file was saved (if applicable).
        - ``renderer`` (str): ``"sonnet"`` or ``"python"``.
        - ``duration_ms`` (float): Rendering time in milliseconds.
    """
    start = time.monotonic()
    template_id = render_context.get("template_id", 1)
    slug = render_context.get("slug", "unknown")
    rendered = ""
    renderer_used = "python"

    if mode in ("auto", "sonnet"):
        # Try Sonnet first
        template_text = _load_template(template_id)
        if template_text:
            rendered = _render_via_sonnet(render_context, template_text)
            if rendered and _validate_output(rendered):
                renderer_used = "sonnet"
            else:
                rendered = ""  # Will fall through to Python

    if not rendered and mode in ("auto", "python"):
        # Python fallback
        rendered = _render_via_python(render_context, template_id)
        renderer_used = "python"

    if not rendered:
        # Absolute minimum fallback -- should never happen
        rendered = (
            f"{SOLID_LINE}\n"
            f"  RENDER ERROR: Template {template_id} for {slug}\n"
            f"  Mode: {mode} | Time: {datetime.now(timezone.utc).isoformat()}\n"
            f"{SOLID_LINE}\n"
        )
        renderer_used = "python"

    duration_ms = (time.monotonic() - start) * 1000

    # Determine output path
    resolved_output = output_path
    if not resolved_output:
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        log_dir = _LOGS_DIR / slug
        log_dir.mkdir(parents=True, exist_ok=True)
        resolved_output = str(log_dir / f"TEMPLATE-{template_id}-{now_str}.md")

    # Write output
    if resolved_output:
        try:
            out_path = Path(resolved_output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
        except Exception:
            pass  # Non-fatal

    return {
        "rendered": rendered,
        "output_path": resolved_output,
        "renderer": renderer_used,
        "duration_ms": round(duration_ms, 2),
    }


def render_all(slug: str, mode: str = "auto") -> list[dict[str, Any]]:
    """Render all applicable templates for a given slug.

    Collects checkpoint data for each template (1-7) and renders them.

    Args:
        slug: Person slug (e.g. ``"process-architect"``).
        mode: Rendering mode (``"auto"``, ``"sonnet"``, ``"python"``).

    Returns:
        List of result dicts from ``render_template()``.
    """
    results = []

    # Try to import data collector for context
    try:
        from engine.intelligence.pipeline.mce.chronicler_data_collector import (
            collect_checkpoint_data,
            collect_session_data,
        )
        has_collector = True
    except ImportError:
        has_collector = False

    for template_id in range(1, 8):
        if has_collector:
            if template_id == 7:
                # Session consolidation uses session data
                session_ctx = collect_session_data()
                ctx = collect_checkpoint_data(slug, template_id)
                ctx["session"] = session_ctx
            else:
                ctx = collect_checkpoint_data(slug, template_id)
        else:
            # Minimal context fallback
            ctx = {
                "template_id": template_id,
                "slug": slug,
                "person_name": slug.replace("-", " ").title(),
                "bucket": "external",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "metrics": {},
                "dna": {},
                "validation": {},
                "deltas": {},
                "progress": {},
                "insights": {},
                "files": {},
            }

        result = render_template(ctx, mode=mode)
        results.append(result)

    return results


# =========================================================================
# CLI
# =========================================================================


def _cli_render(args: argparse.Namespace) -> None:
    """Handle the ``render`` CLI subcommand."""
    # Load context from JSON file
    ctx_path = Path(args.context)
    if not ctx_path.exists():
        print(f"ERROR: Context file not found: {args.context}", file=sys.stderr)
        sys.exit(1)

    try:
        ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, Exception) as e:
        print(f"ERROR: Failed to parse context JSON: {e}", file=sys.stderr)
        sys.exit(1)

    result = render_template(ctx, mode=args.mode, output_path=args.output)

    print(f"Renderer: {result['renderer']}")
    print(f"Duration: {result['duration_ms']:.1f}ms")
    print(f"Output: {result['output_path']}")
    print(f"Length: {len(result['rendered'])} chars")
    print(f"Valid: {_validate_output(result['rendered'])}")
    print("---")
    print(result["rendered"])


def _cli_render_all(args: argparse.Namespace) -> None:
    """Handle the ``render-all`` CLI subcommand."""
    results = render_all(args.slug, mode=args.mode)

    print(f"Rendered {len(results)} templates for slug: {args.slug}")
    print("---")
    for r in results:
        print(f"  Template: {r['output_path']}")
        print(f"    Renderer: {r['renderer']} | Duration: {r['duration_ms']:.1f}ms | Length: {len(r['rendered'])} chars")
    print("---")
    print("All templates rendered successfully.")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Chronicler Render Dispatcher -- MCE template rendering",
        prog="render_dispatcher.py",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # render subcommand
    render_parser = subparsers.add_parser("render", help="Render a single template")
    render_parser.add_argument(
        "--context", required=True, help="Path to JSON context file"
    )
    render_parser.add_argument(
        "--output", default=None, help="Output file path (auto-generated if omitted)"
    )
    render_parser.add_argument(
        "--mode",
        choices=["auto", "sonnet", "python"],
        default="auto",
        help="Rendering mode (default: auto)",
    )

    # render-all subcommand
    render_all_parser = subparsers.add_parser("render-all", help="Render all templates for a slug")
    render_all_parser.add_argument(
        "--slug", required=True, help="Person slug (e.g. process-architect)"
    )
    render_all_parser.add_argument(
        "--mode",
        choices=["auto", "sonnet", "python"],
        default="auto",
        help="Rendering mode (default: auto)",
    )

    args = parser.parse_args()

    if args.command == "render":
        _cli_render(args)
    elif args.command == "render-all":
        _cli_render_all(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
