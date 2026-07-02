"""
progress_panel.py -- Master Progress Panel: ASCII Renderer
===========================================================
Renders a live ASCII progress panel for /process-inbox pipeline.
Uses ANSI escape codes for in-place terminal update (no scroll).

Story: PIP-008
Version: 1.0.0
Date: 2026-04-16
"""

from __future__ import annotations

import sys
from typing import Any

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

PANEL_WIDTH = 58
PANEL_LINES = 7  # Number of lines in the panel (for ANSI cursor movement)


# ---------------------------------------------------------------------------
# ProgressPanel
# ---------------------------------------------------------------------------


class ProgressPanel:
    """ASCII progress panel renderer with in-place terminal update.

    Panel format:
        +----------------------------------------------------------+
        | MEGA BRAIN -- PROCESS INBOX                 [RUNNING]    |
        +----------------------------------------------------------+
        | Progress:   [================>          ] 45/118 (38%)   |
        | Workers:    [W1: hormozi] [W2: cole-gordon] [--] [--]    |
        | Failed:     2                                            |
        | ETA:        01:23 remaining                              |
        | Elapsed:    00:32                                        |
        +----------------------------------------------------------+
    """

    def __init__(self) -> None:
        self._first_render = True

    def render(self, status: dict[str, Any]) -> str:
        """Generate ASCII panel string from status dict."""
        total = status.get("total", 0)
        processed = status.get("processed", 0)
        failed = status.get("failed", 0)
        eta = status.get("eta", "--:--")
        batch_status = status.get("status", "running")
        active_slugs = status.get("active_slugs", [])
        max_workers = status.get("max_workers", 4)

        # Progress bar
        pct = round(processed / total * 100) if total > 0 else 0
        bar_width = 28
        filled = round(processed / total * bar_width) if total > 0 else 0
        bar = (
            "=" * filled + ">" + " " * (bar_width - filled - 1)
            if filled < bar_width
            else "=" * bar_width
        )
        progress_str = f"[{bar}] {processed}/{total} ({pct}%)"

        # Worker status
        worker_parts = []
        for i in range(max_workers):
            if i < len(active_slugs):
                slug_short = active_slugs[i][:12]
                worker_parts.append(f"[W{i+1}: {slug_short}]")
            else:
                worker_parts.append("[--]")
        workers_str = " ".join(worker_parts)

        # Status label
        if batch_status == "completed":
            status_label = "[DONE]"
        elif batch_status == "running":
            status_label = "[RUNNING]"
        else:
            status_label = f"[{batch_status.upper()}]"

        # Elapsed time
        elapsed = status.get("elapsed", "00:00")

        # Build panel
        border = "+" + "-" * PANEL_WIDTH + "+"
        lines = [
            border,
            self._pad(f"MEGA BRAIN -- PROCESS INBOX{status_label:>30s}"),
            border,
            self._pad(f"Progress:   {progress_str}"),
            self._pad(f"Workers:    {workers_str}"),
            self._pad(f"Failed:     {failed}"),
            self._pad(f"ETA:        {eta} remaining"),
            self._pad(f"Elapsed:    {elapsed}"),
            border,
        ]
        return "\n".join(lines)

    def render_done(self, total: int, processed: int, elapsed: str) -> str:
        """Render final DONE panel."""
        border = "+" + "-" * PANEL_WIDTH + "+"
        done_str = f"DONE -- {processed}/{total} files processed in {elapsed}"
        lines = [
            border,
            self._pad(f"MEGA BRAIN -- PROCESS INBOX{'[DONE]':>30s}"),
            border,
            self._pad(done_str),
            border,
        ]
        return "\n".join(lines)

    def print_update(self, status: dict[str, Any]) -> None:
        """Print panel using ANSI escape codes for in-place update.

        First render: prints normally.
        Subsequent renders: moves cursor up and overwrites previous panel.
        Preserves log lines above the panel.
        """
        panel_str = self.render(status)
        line_count = panel_str.count("\n") + 1

        if not self._first_render:
            # Move cursor up to overwrite previous panel
            sys.stdout.write(f"\033[{line_count}A")

        sys.stdout.write(panel_str + "\n")
        sys.stdout.flush()
        self._first_render = False

    def print_done(self, total: int, processed: int, elapsed: str) -> None:
        """Print final DONE panel (overwrites running panel)."""
        panel_str = self.render_done(total, processed, elapsed)

        if not self._first_render:
            # Move up to overwrite previous panel (running panel is taller)
            sys.stdout.write(f"\033[{PANEL_LINES + 2}A")
            # Clear the extra lines from the running panel
            for _ in range(PANEL_LINES + 2):
                sys.stdout.write("\033[2K\n")
            sys.stdout.write(f"\033[{PANEL_LINES + 2}A")

        sys.stdout.write(panel_str + "\n")
        sys.stdout.flush()

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _pad(content: str) -> str:
        """Pad content to fill panel width."""
        truncated = content[: PANEL_WIDTH - 2]
        return f"| {truncated.ljust(PANEL_WIDTH - 2)} |"
