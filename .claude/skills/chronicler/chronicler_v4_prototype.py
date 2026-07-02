#!/usr/bin/env python3
"""Chronicler v4.0 — PROTOTYPE renderer (design mockup, NOT production).

Renders the full MCE Pipeline Log in the new v4 wide format (100 cols) from
the real Jeremy Haynes run data. Standalone — does NOT touch the production
renderer (log_generator.py). Used to get founder approval on the v4 design
before @dev ports it.

Width: 100 columns (founder directive: "extender mais" — wider than v3.2's 79).
Alignment is COMPUTED (display-width aware, emoji = 2 cells) so boxes never skew.

Run:  python3 .claude/skills/chronicler/chronicler_v4_prototype.py
Out:  .data/logs/mce/jeremy-haynes/MCE-JH-v4-preview.md
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

W = 100  # total box width (founder: wider than 79)
INNER = W - 2  # content field between the two vertical borders


# ── display-width (emoji / wide CJK count as 2 cells) ───────────────────────
# True double-width glyphs (emoji + status icons). Block/shade/star glyphs
# (█▓░▒★·) render single-width in monospace terminals — NOT included.
_WIDE_EMOJI = set(
    "🧮🛡📥👁🧬📋📌📂📦✂🧩🧠🎯🏗🛤🔄⭐💬🔥⚡🔍📜🚀📚🎵📝🗺🏢🚦📈📤📊💰🤖🌳💡📖🔎"
    "✅⚠️❌🟡🟢🟠🔴⏭⚪"
)


def dwidth(s: str) -> int:
    w = 0
    for ch in s:
        if ch in _WIDE_EMOJI or unicodedata.east_asian_width(ch) in ("W", "F"):
            w += 2
        elif ch == "️":  # variation selector — invisible
            w += 0
        else:
            w += 1
    return w


def clip(s: str, width: int) -> str:
    """Truncate s to `width` display columns (display-aware, adds … if cut)."""
    if dwidth(s) <= width:
        return s
    out = ""
    w = 0
    for ch in s:
        cw = dwidth(ch)
        if w + cw > width - 1:
            break
        out += ch
        w += cw
    return out + "…"


def pad(s: str, width: int) -> str:
    """Left-justify s to `width` display columns; truncate if it overflows."""
    s = clip(s, width)
    gap = width - dwidth(s)
    return s + " " * max(0, gap)


def rule_top() -> str:
    return "╔" + "═" * INNER + "╗"


def rule_mid() -> str:
    return "╟" + "─" * INNER + "╢"


def rule_bot() -> str:
    return "╚" + "═" * INNER + "╝"


def row(s: str = "") -> str:
    """A content row: ║ + ' ' + s + pad + ║  (total W)."""
    body = " " + s
    return "║" + pad(body, INNER) + "║"


def row_split(left: str, right: str) -> str:
    """Row with left text and right-aligned text."""
    avail = INNER - 1  # leading space
    gap = avail - dwidth(left) - dwidth(right)
    body = " " + left + " " * max(1, gap) + right
    return "║" + pad(body, INNER) + "║"


# ── inner sub-table (2 columns of key:value) ────────────────────────────────
def kv_table(title: str, pairs: list[tuple[str, str]], indent: int = 2) -> list[str]:
    """Render a 2-column key/value sub-box inside the main box.

    Geometry (display cells), tuned so each row == INNER-1 after the row()
    leading space, never clipped:
      ind(2) + "│ "(2) + cell(colw) + " │ "(3) + cell(colw) + " │"(2)
    """
    ind = " " * indent
    colw = 42  # 2+2+42+3+42+2 = 93 ; +ind already in ind var below
    seg = "─" * (colw + 2)  # dashes spanning a column cell incl. its padding
    cells = []
    for k, v in pairs:
        cells.append(f"{pad(k, 16)} {v}")
    if len(cells) % 2 == 1:
        cells.append("")
    out = []
    title_dash = colw + 2 - dwidth(title) - 3  # "─ TITLE " consumed
    out.append(row(f"{ind}┌─ {title} " + "─" * max(1, title_dash) + "┬" + seg + "┐"))
    for i in range(0, len(cells), 2):
        l = pad(clip(cells[i], colw), colw)
        r = pad(clip(cells[i + 1], colw), colw)
        out.append(row(f"{ind}│ {l} │ {r} │"))
    out.append(row(f"{ind}└" + seg + "┴" + seg + "┘"))
    return out


def progress_bar(done: int, total: int, width: int = 30) -> str:
    filled = int(round(width * done / total)) if total else 0
    return "▓" * filled + "░" * (width - filled)


def wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        if dwidth(cur + " " + wd) > width:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    if cur:
        lines.append(cur)
    return lines


# ── the v4 STEP box ─────────────────────────────────────────────────────────
def step_box(
    icon: str,
    nn: str,
    title: str,
    group: str,
    status: str,
    metrics: list[tuple[str, str]] | None = None,
    glossary: list[tuple[str, str]] | None = None,
    why_title: str = "POR QUE ESTE PASSO EXISTE?",
    why: str = "",
    extra: list[str] | None = None,
    tag: str = "",
) -> str:
    out = [rule_top()]
    hdr_left = f"{icon}  STEP {nn} · {title}"
    if tag:
        hdr_left += f"   {tag}"
    out.append(row_split(hdr_left, f"{group} · {nn}/44"))
    out.append(rule_mid())
    out.append(row(f"STATUS   {status}"))
    out.append(row())
    if extra:
        for e in extra:
            out.append(row(e))
        out.append(row())
    if metrics:
        out.extend(kv_table("MÉTRICAS", metrics))
        out.append(row())
    if glossary:
        out.append(row("💡 GLOSSÁRIO"))
        for term, definition in glossary:
            prefix_w = 3 + dwidth(term) + 5  # "   " + term + " ··· "
            wl = wrap(definition, INNER - 2 - prefix_w)
            out.append(row(f"   {term} ··· {wl[0]}"))
            for cont in wl[1:]:
                out.append(row(" " * prefix_w + cont))
        out.append(row())
    if why:
        out.append(row(f"📖 {why_title}"))
        for wl in wrap(why, INNER - 6):
            out.append(row(f"   {wl}"))
    out.append(rule_bot())
    return "\n".join(out)


def group_banner(g: int, name: str, steps: str, n: int, pct: int, cur: int) -> str:
    bar = "━" * INNER
    b = progress_bar(cur, 44, 30)
    lines = [
        bar,
        pad(f"  ▒▒▒  GRUPO {g} · {name}", W - dwidth(f"STEPs {steps} · {n} passos") - 2)
        + f"STEPs {steps} · {n} passos",
        f"  Progresso do pipeline   {b}   {pct}%   (STEP {cur} de 44)",
        bar,
    ]
    return "\n".join(lines)


def mono_header() -> str:
    bar = "█" * W
    def c(s):
        return "████" + pad("   " + s, W - 8) + "████"
    return "\n".join([
        bar, bar,
        "████" + " " * (W - 8) + "████",
        c("M C E   P I P E L I N E   L O G          v 4 . 0"),
        c("Jeremy Haynes  (JH)  ·  2026-06-08 16:09 UTC"),
        "████" + " " * (W - 8) + "████",
        c("44 STEPS · 6 GRUPOS · 2 BLOCOS CANÔNICOS · Chronicler v4.0"),
        "████" + " " * (W - 8) + "████",
        c("GRUPO 1 ▓▓▓ Ingestão      GRUPO 4 ▓▓▓ Cascateamento"),
        c("GRUPO 2 ▓▓▓ DNA L1–L10    GRUPO 5 ▓▓▓ Gates & Qualidade"),
        c("GRUPO 3 ▓▓▓ Identidade    GRUPO 6 ▓▓▓ Finalização"),
        "████" + " " * (W - 8) + "████",
        bar, bar,
    ])


def mono_footer() -> str:
    bar = "█" * W
    def c(s):
        return "████" + pad("   " + s, W - 8) + "████"
    return "\n".join([
        bar, bar,
        "████" + " " * (W - 8) + "████",
        c("MCE PIPELINE LOG v4.0 — Jeremy Haynes (JH) — FIM"),
        c("Chronicler Design System v4.0 · 44 STEPS + 2 CANONICAL BLOCKS"),
        "████" + " " * (W - 8) + "████",
        bar, bar,
    ])
