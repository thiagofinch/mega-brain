"""
log_renderer.py -- Progressive MCE Pipeline Log Renderer
========================================================

Renders ASCII progress output for each of the 12 MCE pipeline steps.
Designed for real-time feedback in Bash tool output so operators can
track pipeline progress visually.

Usage::

    from core.intelligence.pipeline.mce.log_renderer import render_progressive

    # Basic step output
    print(render_progressive("alex-hormozi", step=1, total=12))

    # With step-specific details
    print(render_progressive("alex-hormozi", step=3, total=12, details={
        "chunks": 42,
        "persons": ["Alex Hormozi", "Leila Hormozi"],
    }))

Each step number maps to a canonical step name and description.
Steps 3-8 accept ``details`` dicts with step-specific metrics.

Constraints:
    - stdlib only (no external deps).
    - Pure string formatting -- no I/O or side effects.

Version: 1.0.0
Date: 2026-03-16
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Canonical step definitions for the 12-step MCE pipeline
# ---------------------------------------------------------------------------

_STEPS: dict[int, dict[str, str]] = {
    0: {"name": "DETECT INPUT", "desc": "Identify file, slug, or resume mode"},
    1: {"name": "INGEST", "desc": "Classify, route, and organize source file"},
    2: {"name": "BATCH", "desc": "Create batches from organized inbox"},
    3: {"name": "CHUNK", "desc": "Semantic chunking of source material"},
    4: {"name": "ENTITY RESOLUTION", "desc": "Resolve entity name variants to canonical forms"},
    5: {"name": "INSIGHT EXTRACTION", "desc": "Extract actionable insights from chunks"},
    6: {"name": "MCE BEHAVIORAL", "desc": "Extract behavioral patterns from insights"},
    7: {"name": "MCE IDENTITY", "desc": "Extract value hierarchy, obsessions, paradoxes"},
    8: {"name": "MCE VOICE", "desc": "Extract Voice DNA -- speech patterns, signature phrases"},
    9: {"name": "IDENTITY CHECKPOINT", "desc": "Present identity core for human validation"},
    10: {"name": "CONSOLIDATION", "desc": "Compile dossiers, DNA YAMLs, agents"},
    11: {"name": "FINALIZE", "desc": "Memory enrichment, workspace sync, metrics"},
    12: {"name": "REPORT", "desc": "Display completion report with validation"},
}

# Width of the rendered panel (characters)
_PANEL_WIDTH = 60


# ---------------------------------------------------------------------------
# Step-specific detail formatters
# ---------------------------------------------------------------------------


def _format_details_step3(details: dict[str, Any]) -> list[str]:
    """Format details for Step 3 (CHUNK): chunk count + person list."""
    lines: list[str] = []
    chunk_count = details.get("chunks", details.get("chunk_count", "?"))
    lines.append(f"  Chunks created:    {chunk_count}")
    persons = details.get("persons", details.get("person_list", []))
    if persons:
        names = ", ".join(str(p) for p in persons[:5])
        if len(persons) > 5:
            names += f" (+{len(persons) - 5} more)"
        lines.append(f"  Persons detected:  {names}")
    files_processed = details.get("files_processed", details.get("files", None))
    if files_processed is not None:
        lines.append(f"  Files processed:   {files_processed}")
    return lines


def _format_details_step5(details: dict[str, Any]) -> list[str]:
    """Format details for Step 5 (INSIGHT EXTRACTION): insight count by tag."""
    lines: list[str] = []
    total = details.get("total_insights", details.get("insights", "?"))
    lines.append(f"  Total insights:    {total}")
    by_tag = details.get("by_tag", details.get("tags", {}))
    if by_tag and isinstance(by_tag, dict):
        tag_parts = [f"{tag}: {count}" for tag, count in by_tag.items()]
        lines.append(f"  By tag:            {', '.join(tag_parts)}")
    persons_count = details.get("persons_count", None)
    if persons_count is not None:
        lines.append(f"  Persons:           {persons_count}")
    return lines


def _format_details_step6(details: dict[str, Any]) -> list[str]:
    """Format details for Step 6 (MCE BEHAVIORAL): behavioral pattern names."""
    lines: list[str] = []
    patterns = details.get("patterns", details.get("behavioral_patterns", []))
    count = details.get("pattern_count", len(patterns) if isinstance(patterns, list) else "?")
    lines.append(f"  Patterns found:    {count}")
    if isinstance(patterns, list):
        for p in patterns[:4]:
            name = p if isinstance(p, str) else p.get("name", str(p))
            lines.append(f"    - {name}")
        if len(patterns) > 4:
            lines.append(f"    (+{len(patterns) - 4} more)")
    return lines


def _format_details_step8(details: dict[str, Any]) -> list[str]:
    """Format details for Step 8 (MCE VOICE): voice DNA dimensions."""
    lines: list[str] = []
    dims = details.get("dimensions", details.get("voice_dimensions", {}))
    phrases = details.get("signature_phrases", details.get("phrases", "?"))
    states = details.get("behavioral_states", details.get("states", "?"))
    lines.append(f"  Signature phrases: {phrases}")
    lines.append(f"  Behavioral states: {states}")
    if dims and isinstance(dims, dict):
        dim_parts = []
        for key in ("certainty", "authority", "warmth", "directness"):
            val = dims.get(key)
            if val is not None:
                dim_parts.append(f"{key.capitalize()}: {val}/10")
        if dim_parts:
            lines.append(f"  Dimensions:        {' | '.join(dim_parts)}")
    return lines


# Map of step numbers to their detail formatter functions
_DETAIL_FORMATTERS: dict[int, Any] = {
    3: _format_details_step3,
    5: _format_details_step5,
    6: _format_details_step6,
    8: _format_details_step8,
}


# ---------------------------------------------------------------------------
# Generic detail formatter (for steps without a specific formatter)
# ---------------------------------------------------------------------------


def _format_details_generic(details: dict[str, Any]) -> list[str]:
    """Format arbitrary key-value details for display."""
    lines: list[str] = []
    for key, value in details.items():
        if isinstance(value, (list, dict)):
            if isinstance(value, list):
                lines.append(f"  {key}: {len(value)} items")
            else:
                lines.append(f"  {key}: {len(value)} entries")
        else:
            lines.append(f"  {key}: {value}")
    return lines[:4]  # Cap at 4 lines to keep panel compact


# ---------------------------------------------------------------------------
# Progress bar builder
# ---------------------------------------------------------------------------


def _progress_bar(step: int, total: int, width: int = 24) -> str:
    """Build an ASCII progress bar like [=========>          ] 5/12."""
    if total <= 0:
        return f"[{'?' * width}] {step}/{total}"
    filled = int((step / total) * width)
    remaining = width - filled
    if filled > 0 and remaining > 0:
        bar = "=" * (filled - 1) + ">" + " " * remaining
    elif remaining == 0:
        bar = "=" * width
    else:
        bar = " " * width
    return f"[{bar}] {step}/{total} steps"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_progressive(
    slug: str,
    step: int,
    total: int = 12,
    details: dict[str, Any] | None = None,
    bucket: str | None = None,
    status: str = "DONE",
) -> str:
    """Render an ASCII progress panel for a single MCE pipeline step.

    Args:
        slug: The person/source slug (e.g. ``"alex-hormozi"``).
        step: Current step number (0-12).
        total: Total step count (default 12).
        details: Optional dict with step-specific metrics. Steps 3, 5, 6, 8
                 have specialized formatters; other steps get generic k/v display.
        bucket: Knowledge bucket name (e.g. ``"external"``). Shown if provided.
        status: Status marker (default ``"DONE"``). Other values: ``"RUNNING"``,
                ``"FAILED"``, ``"SKIPPED"``.

    Returns:
        Multi-line string with the progress panel, ready for ``print()``.
    """
    step_info = _STEPS.get(step, {"name": f"STEP {step}", "desc": "Custom step"})
    step_name = step_info["name"]
    step_desc = step_info["desc"]

    # Status marker
    status_map = {
        "DONE": "[OK]",
        "RUNNING": "[..]",
        "FAILED": "[!!]",
        "SKIPPED": "[--]",
    }
    status_marker = status_map.get(status.upper(), f"[{status[:2]}]")

    # Header line
    header = f"  STEP {step} -- {step_name}"
    header_padded = header.ljust(_PANEL_WIDTH - len(status_marker) - 2) + status_marker

    # Slug + bucket line
    slug_line = f"  Slug: {slug}"
    if bucket:
        slug_line += f" | Bucket: {bucket}"

    # Detail lines
    detail_lines: list[str] = []
    if details:
        formatter = _DETAIL_FORMATTERS.get(step, _format_details_generic)
        detail_lines = formatter(details)

    # If no details, show the step description
    if not detail_lines:
        detail_lines = [f"  {step_desc}"]

    # Progress bar
    bar = _progress_bar(step, total)
    progress_line = f"  Progress: {bar}"

    # Build the panel
    sep_outer = "\u2501" * _PANEL_WIDTH
    sep_inner = "  " + "\u2500" * (_PANEL_WIDTH - 4)

    lines = [
        sep_outer,
        header_padded,
        slug_line,
        sep_inner,
        *detail_lines,
        sep_inner,
        progress_line,
        sep_outer,
    ]

    return "\n".join(lines)


def render_step_start(slug: str, step: int, total: int = 12) -> str:
    """Render a compact one-line message indicating a step is starting.

    Useful for printing before a long-running step so the operator sees
    immediate feedback.

    Args:
        slug: The person/source slug.
        step: Current step number (0-12).
        total: Total step count.

    Returns:
        Single-line string like ``"Step 3/12: CHUNK -- Semantic chunking..."``.
    """
    step_info = _STEPS.get(step, {"name": f"STEP {step}", "desc": "Custom step"})
    return f"Step {step}/{total}: {step_info['name']} -- {step_info['desc']}..."


def render_pipeline_header(slug: str, person_name: str = "", source_code: str = "") -> str:
    """Render the pipeline start header.

    Args:
        slug: The person/source slug.
        person_name: Full person name (optional).
        source_code: 2-char source code (optional).

    Returns:
        Multi-line ASCII header for pipeline start.
    """
    sep = "=" * _PANEL_WIDTH
    title = "M C E   P I P E L I N E"
    person_display = person_name or slug
    if source_code:
        person_display += f" ({source_code})"

    lines = [
        sep,
        f"  {title}",
        f"  Source: {person_display}",
        f"  Slug:   {slug}",
        sep,
    ]
    return "\n".join(lines)


def render_pipeline_footer(slug: str, success: bool = True, duration_ms: float = 0.0) -> str:
    """Render the pipeline completion footer.

    Args:
        slug: The person/source slug.
        success: Whether the pipeline completed successfully.
        duration_ms: Total duration in milliseconds.

    Returns:
        Multi-line ASCII footer.
    """
    sep = "=" * _PANEL_WIDTH
    result = "COMPLETE" if success else "FAILED"
    duration_str = f"{duration_ms / 1000:.1f}s" if duration_ms else "N/A"

    lines = [
        sep,
        f"  PIPELINE {result} -- {slug}",
        f"  Duration: {duration_str}",
        sep,
    ]
    return "\n".join(lines)
