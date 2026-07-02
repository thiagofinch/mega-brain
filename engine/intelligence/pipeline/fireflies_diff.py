"""Fireflies <-> Megabrain diff dashboard.

Read-only utility. Queries the Fireflies GraphQL listing endpoint for each
configured account, reads the local Megabrain state files, and renders an
ASCII dashboard that highlights:

- Remote total visible to each API key (window-limited by Fireflies API)
- Local processed / skipped / pending counts
- The actual diff (remote ids NOT in local processed_ids)
- Empresa vs Pessoal classification distribution
- Sync staleness and health flags

The script never mutates state. It only reads .json files and performs
GraphQL list queries (no full-transcript fetches).

CLI:
    python3 -m engine.intelligence.pipeline.fireflies_diff
    python3 -m engine.intelligence.pipeline.fireflies_diff --top 20
    python3 -m engine.intelligence.pipeline.fireflies_diff --account default
    python3 -m engine.intelligence.pipeline.fireflies_diff --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ============================================================================
# Constants
# ============================================================================

REPO_ROOT = Path(__file__).resolve().parents[3]
MISSION_CONTROL = REPO_ROOT / ".claude" / "mission-control"

GRAPHQL_URL = "https://api.fireflies.ai/graphql"
QUERY_LIST = "{ transcripts { id title date duration organizer_email } }"
REQUEST_TIMEOUT = 30

# Primary/default account label. The legacy single-account state file
# (FIREFLIES-STATE.json) and the unsuffixed FIREFLIES_API_KEY env var both map
# to this label. Configure via MEGA_BRAIN_FIREFLIES_DEFAULT_ACCOUNT.
DEFAULT_ACCOUNT_LABEL = os.environ.get(
    "MEGA_BRAIN_FIREFLIES_DEFAULT_ACCOUNT", "default"
).strip() or "default"

# Accounts to scan by default. Override via MEGA_BRAIN_FIREFLIES_ACCOUNTS
# (comma-separated); otherwise just the primary account.
DEFAULT_ACCOUNTS = [
    a.strip()
    for a in os.environ.get("MEGA_BRAIN_FIREFLIES_ACCOUNTS", "").split(",")
    if a.strip()
] or [DEFAULT_ACCOUNT_LABEL]

TOP_N_DEFAULT = 10
STALE_THRESHOLD_MIN = 60
SKIP_RATE_WARN_PCT = 15.0

RSM_WIDTH = 80  # Regra de Estilo MegaBrain — width <= 80 cols (compact mode)
RICH_WIDTH = 90  # Pretty dashboard width

UTC = timezone.utc
BRT = timezone(timedelta(hours=-3))  # Brasilia, no DST


# ============================================================================
# .env loader (stdlib only — no dotenv dependency)
# ============================================================================


def _load_dotenv() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip surrounding quotes
            if value and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            # Don't clobber values already in env
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        return


# Auto-load .env on import so the CLI works out of the box
_load_dotenv()


# ============================================================================
# Dataclasses
# ============================================================================


@dataclass
class Transcript:
    id: str
    title: str
    date_ms: int
    duration_min: float
    organizer: str


@dataclass
class AccountSnapshot:
    account: str
    api_available: bool
    state_exists: bool
    state_path: Path
    remote_total: int
    remote_error: str | None
    processed_count: int
    skipped: int
    routed_empresa: int
    routed_pessoal: int
    last_sync_at: str | None
    next_tag: int | None
    pending: list[Transcript] = field(default_factory=list)


# ============================================================================
# State file resolution
# ============================================================================


def _state_path(account: str) -> Path:
    """Resolve state file path. Multi-account convention is
    FIREFLIES-STATE-{account}.json; legacy single-account is
    FIREFLIES-STATE.json (primary/default account only).

    For the primary account: if both files exist, return whichever was
    modified more recently. This handles the case where `fireflies_sync run`
    writes to the legacy file while `multi_fireflies.py` writes to the
    suffixed one — the dashboard always reflects the freshest snapshot.
    """
    suffixed = MISSION_CONTROL / f"FIREFLIES-STATE-{account}.json"
    if account == DEFAULT_ACCOUNT_LABEL:
        legacy = MISSION_CONTROL / "FIREFLIES-STATE.json"
        if suffixed.exists() and legacy.exists():
            return suffixed if suffixed.stat().st_mtime >= legacy.stat().st_mtime else legacy
        if legacy.exists():
            return legacy
    return suffixed


def _load_state(account: str) -> tuple[dict[str, Any] | None, Path]:
    p = _state_path(account)
    if not p.exists():
        return None, p
    try:
        return json.loads(p.read_text(encoding="utf-8")), p
    except (OSError, json.JSONDecodeError):
        return None, p


# ============================================================================
# API key resolution
# ============================================================================


def _api_key_for(account: str) -> str:
    label = account.upper().replace("-", "_")
    key = os.environ.get(f"FIREFLIES_API_KEY_{label}", "")
    if key:
        return key
    if account == DEFAULT_ACCOUNT_LABEL:
        return os.environ.get("FIREFLIES_API_KEY", "")
    return ""


# ============================================================================
# Remote query (lightweight list only — no transcript bodies)
# ============================================================================


def _fetch_remote(api_key: str) -> tuple[list[Transcript], str | None]:
    if not api_key:
        return [], "api key missing"
    body = json.dumps({"query": QUERY_LIST}).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "MegaBrain-FirefliesDiff/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return [], f"HTTP {exc.code}"
    except (urllib.error.URLError, OSError) as exc:
        return [], f"network: {exc}"
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [], f"network: {exc}"
    if isinstance(result, dict) and result.get("errors"):
        return [], f"graphql: {result['errors']}"
    data = result.get("data", {}) if isinstance(result, dict) else {}
    transcripts = data.get("transcripts", []) if isinstance(data, dict) else []
    out: list[Transcript] = []
    for t in transcripts:
        if not isinstance(t, dict):
            continue
        out.append(
            Transcript(
                id=str(t.get("id", "")).strip(),
                title=str(t.get("title", "Untitled")).strip() or "Untitled",
                date_ms=int(t.get("date", 0) or 0),
                duration_min=float(t.get("duration", 0) or 0),
                organizer=str(t.get("organizer_email", "") or "").strip(),
            )
        )
    return out, None


# ============================================================================
# Snapshot builder
# ============================================================================


def snapshot(account: str) -> AccountSnapshot:
    state, sp = _load_state(account)
    state_exists = state is not None
    if state is None:
        state = {}
    api_key = _api_key_for(account)
    remote_list, remote_error = _fetch_remote(api_key)
    processed_ids = set(state.get("processed_ids", []))
    pending = [t for t in remote_list if t.id not in processed_ids]
    pending.sort(key=lambda t: t.date_ms, reverse=True)
    return AccountSnapshot(
        account=account,
        api_available=bool(api_key),
        state_exists=state_exists,
        state_path=sp,
        remote_total=len(remote_list),
        remote_error=remote_error,
        processed_count=len(processed_ids) or int(state.get("meetings_processed", 0)),
        skipped=int(state.get("skipped", 0)),
        routed_empresa=int(state.get("routed_empresa", 0)),
        routed_pessoal=int(state.get("routed_pessoal", 0)),
        last_sync_at=state.get("last_sync_at"),
        next_tag=state.get("next_tag_number"),
        pending=pending,
    )


# ============================================================================
# Staleness helpers
# ============================================================================


def _staleness(iso: str | None) -> str:
    if not iso:
        return "never"
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
    except ValueError:
        return "?"
    secs = int((datetime.now(UTC) - dt).total_seconds())
    if secs < 0:
        return "just now"
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"


def _is_stale(iso: str | None, threshold_min: int = 60) -> bool:
    if not iso:
        return True
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
    except ValueError:
        return True
    return (datetime.now(UTC) - dt).total_seconds() > threshold_min * 60


# ============================================================================
# Rendering primitives
# ============================================================================


def _eq_line(label: str | None = None) -> str:
    """Pytest-style section separator at RSM_WIDTH (80 cols)."""
    if label is None:
        return "=" * RSM_WIDTH
    spacer = 4
    left = (RSM_WIDTH - len(label) - 2) // 2
    right = RSM_WIDTH - len(label) - 2 - left
    return "=" * left + " " + label + " " + "=" * right


def _dash_line() -> str:
    return "-" * RSM_WIDTH


def _compact_status(s: AccountSnapshot) -> str:
    """Status word in CAPS, max 13 chars (fits compact column)."""
    if not s.api_available:
        return "API MISSING"
    if s.remote_error:
        return f"ERR {s.remote_error}"[:13]
    if not s.state_exists:
        return "STATE MISSING"
    if _is_stale(s.last_sync_at):
        return "STALE"
    if len(s.pending) > 0:
        return f"PEND {len(s.pending)}"
    return "OK"


def _collect_flags(s: AccountSnapshot) -> list[str]:
    """Health flags (status words, no emoji)."""
    flags: list[str] = []
    if not s.api_available:
        flags.append("api key MISSING")
    if not s.state_exists:
        flags.append("state file MISSING")
    if s.last_sync_at and _is_stale(s.last_sync_at):
        flags.append(f"sync STALE ({_staleness(s.last_sync_at)})")
    if s.remote_error:
        flags.append(f"remote: {s.remote_error}")
    seen_total = s.processed_count + s.skipped
    if seen_total > 0:
        skip_rate = (s.skipped / seen_total) * 100
        if skip_rate > SKIP_RATE_WARN_PCT:
            flags.append(f"skip rate HIGH ({skip_rate:.0f}%)")
    return flags


# ============================================================================
# Dashboard renderers
# ============================================================================


def _box_top(width: int, label: str | None = None, double: bool = False) -> str:
    """Top border with optional centered label."""
    if double:
        tl, tr, h = "╔", "╗", "═"
    else:
        tl, tr, h = "┌", "┐", "─"
    if label is None:
        return tl + h * (width - 2) + tr
    label_decorated = f" {label} "
    pad = width - 2 - len(label_decorated)
    left = pad // 2
    right = pad - left
    return tl + h * left + label_decorated + h * right + tr


def _box_bottom(width: int, double: bool = False) -> str:
    if double:
        return "╚" + "═" * (width - 2) + "╝"
    return "└" + "─" * (width - 2) + "┘"


def _box_line(content: str, width: int, double: bool = False) -> str:
    """Wrap a single line in box vertical borders, padded to width."""
    side = "║" if double else "│"
    inner = width - 4  # 2 borders + 2 spaces padding
    # Strip trailing whitespace, then pad
    body = content.rstrip()
    if len(body) > inner:
        body = body[:inner]
    return f"{side} {body:<{inner}} {side}"


def _bar(ratio: float, width: int = 50, filled: str = "█", empty: str = "░") -> str:
    """Render a horizontal progress bar."""
    ratio = max(0.0, min(1.0, ratio))
    fill = int(round(ratio * width))
    return filled * fill + empty * (width - fill)


def _render_status_word(s: AccountSnapshot) -> str:
    if not s.api_available:
        return "API KEY MISSING"
    if s.remote_error:
        return f"ERROR: {s.remote_error}"
    if not s.state_exists:
        return "STATE FILE MISSING"
    if _is_stale(s.last_sync_at):
        return f"STALE ({_staleness(s.last_sync_at)})"
    if len(s.pending) > 0:
        return f"PENDING ({len(s.pending)})"
    return "OK"


def _render_account_card(s: AccountSnapshot, width: int = RICH_WIDTH) -> list[str]:
    """Render one account as a visually rich card."""
    lines: list[str] = []
    lines.append(_box_top(width, label=f"ACCOUNT  ::  {s.account}"))
    lines.append(_box_line("", width))

    # Status row
    status = _render_status_word(s)
    sync_str = _staleness(s.last_sync_at)
    lines.append(_box_line(f"STATUS   : {status:<32}     SYNC  : {sync_str}", width))
    api_str = "presente" if s.api_available else "AUSENTE"
    state_str = "presente" if s.state_exists else "AUSENTE"
    lines.append(_box_line(f"API KEY  : {api_str:<32}     STATE : {state_str}", width))
    lines.append(_box_line("", width))

    # Big number blocks: Remote | Processados | Pendentes
    remote_n = "--" if s.remote_error else str(s.remote_total)
    proc_n = str(s.processed_count)
    pend_n = str(len(s.pending))

    # Layout math: 3 cells of width 24 (cell total = 26 incl borders),
    # with 4-space gap = 26*3 + 4*2 = 86 chars, fits inside width 90 (86 + 4 border/pad)
    cell_w = 24  # interior cell width (excluding borders)
    cell_gap = "    "  # 4-space gap between cells
    cell_top = "┌" + "─" * cell_w + "┐"
    cell_bot = "└" + "─" * cell_w + "┘"
    cell_blank = "│" + " " * cell_w + "│"

    def big_number_cell(label: str, value: str) -> tuple[str, str, str, str, str]:
        label_line = "│" + f"{label:^{cell_w}}" + "│"
        value_line = "│" + f"{value:^{cell_w}}" + "│"
        return cell_top, label_line, cell_blank, value_line, cell_bot

    cells = [
        big_number_cell("REMOTE (API window)", remote_n),
        big_number_cell("PROCESSADOS (local)", proc_n),
        big_number_cell("PENDENTES (diff)", pend_n),
    ]
    # Stack 5 rows of 3 cells side by side
    for row_idx in range(5):
        joined = cell_gap.join(cell[row_idx] for cell in cells)
        lines.append(_box_line(joined, width))
    lines.append(_box_line("", width))

    # Classificação bars
    total_cls = s.routed_empresa + s.routed_pessoal
    lines.append(_box_line("CLASSIFICACAO", width))
    if total_cls > 0:
        emp_ratio = s.routed_empresa / total_cls
        pes_ratio = s.routed_pessoal / total_cls
        emp_pct = round(emp_ratio * 100)
        pes_pct = 100 - emp_pct
        bar_w = 50
        emp_bar = _bar(emp_ratio, bar_w)
        pes_bar = _bar(pes_ratio, bar_w)
        lines.append(_box_line(
            f"  Empresa  {s.routed_empresa:>4}/{total_cls:<4}  [{emp_bar}]  {emp_pct:>3}%",
            width
        ))
        lines.append(_box_line(
            f"  Pessoal  {s.routed_pessoal:>4}/{total_cls:<4}  [{pes_bar}]  {pes_pct:>3}%",
            width
        ))
    else:
        lines.append(_box_line("  (sem material classificado ainda)", width))
    lines.append(_box_line("", width))

    # Extras
    next_tag_str = f"MEET-{s.next_tag}" if s.next_tag else "n/a"
    lines.append(_box_line(f"SKIPPED  : {s.skipped:<10}     PROX. TAG : {next_tag_str}", width))
    state_path_short = str(s.state_path).replace(str(REPO_ROOT.parent), "").lstrip("/")
    lines.append(_box_line(f"STATE    : {state_path_short[:width - 16]}", width))
    lines.append(_box_line("", width))
    lines.append(_box_bottom(width))
    return lines


def _render_flags_block(snapshots: list[AccountSnapshot], width: int = RICH_WIDTH) -> list[str]:
    lines: list[str] = []
    all_flags: list[tuple[str, str]] = []
    for s in snapshots:
        for flag in _collect_flags(s):
            all_flags.append((s.account, flag))
    lines.append(_box_top(width, label="HEALTH FLAGS"))
    lines.append(_box_line("", width))
    if not all_flags:
        lines.append(_box_line("  OK -- nenhum problema detectado", width))
    else:
        for account, flag in all_flags:
            lines.append(_box_line(f"  [{account}] {flag}", width))
    lines.append(_box_line("", width))
    lines.append(_box_bottom(width))
    return lines


def _render_tips_block(width: int = RICH_WIDTH) -> list[str]:
    lines: list[str] = []
    lines.append(_box_top(width, label="PROXIMOS PASSOS"))
    lines.append(_box_line("", width))
    lines.append(_box_line("  Atualizar sync : python3 -m engine.intelligence.pipeline.fireflies_sync run", width))
    lines.append(_box_line("  Top pendentes  : /fireflies-diff --top 25", width))
    lines.append(_box_line("  Output JSON    : /fireflies-diff --json", width))
    lines.append(_box_line("  Modo compacto  : /fireflies-diff --compact", width))
    lines.append(_box_line("", width))
    lines.append(_box_bottom(width))
    return lines


def render_dashboard(snapshots: list[AccountSnapshot], top_n: int = 10) -> str:
    """Visually rich dashboard with per-account cards, big number blocks,
    progress bars for classification, and dedicated flags/tips sections.

    Width 90 cols. Pure ASCII (uses Unicode box-drawing for borders,
    but no emoji). Designed for readability over compactness.
    Use render_dashboard_compact() for the RSM-1 80-col variant.
    """
    now_brt = datetime.now(BRT).strftime("%Y-%m-%d %H:%M BRT")
    now_utc = datetime.now(UTC).strftime("%H:%M UTC")
    width = RICH_WIDTH
    lines: list[str] = []

    # Outer header (double-line)
    lines.append(_box_top(width, double=True))
    title = "FIREFLIES  <->  MEGABRAIN  ::  DIFF DASHBOARD"
    inner = width - 4
    lines.append(f"║ {title:^{inner}} ║")
    timestamp = f"{now_brt}   |   {now_utc}"
    lines.append(f"║ {timestamp:^{inner}} ║")
    lines.append(_box_bottom(width, double=True))
    lines.append("")

    # Per-account cards
    for s in snapshots:
        lines.extend(_render_account_card(s, width=width))
        lines.append("")

    # Flags block
    lines.extend(_render_flags_block(snapshots, width=width))
    lines.append("")

    # Tips block
    lines.extend(_render_tips_block(width=width))

    return "\n".join(lines)


def render_dashboard_compact(snapshots: list[AccountSnapshot], top_n: int = 10) -> str:
    """RSM-1 compliant compact dashboard.

    Width 80, max 10 lines, pure ASCII, status words in CAPS, no emoji.
    Survives Claude Code collapsagem (Issue #26954) and chat copy-paste.
    """
    now = datetime.now(BRT).strftime("%Y-%m-%d %H:%M BRT")
    lines: list[str] = []
    lines.append(_eq_line(f"FIREFLIES <-> MEGABRAIN DIFF ({now})"))

    # Header row — single space between cols, 2 spaces only between Sync & Status
    lines.append(
        f"{'Account':<12} "
        f"{'Remote':>6} "
        f"{'Proc':>5} "
        f"{'Skip':>5} "
        f"{'Pend':>5} "
        f"{'Emp':>5} "
        f"{'Pes':>5} "
        f"{'Sync':>8}  "
        f"{'Status':<13}".rstrip()
    )

    for s in snapshots:
        remote_str = "--" if s.remote_error else str(s.remote_total)
        line = (
            f"{s.account:<12} "
            f"{remote_str:>6} "
            f"{s.processed_count:>5} "
            f"{s.skipped:>5} "
            f"{len(s.pending):>5} "
            f"{s.routed_empresa:>5} "
            f"{s.routed_pessoal:>5} "
            f"{_staleness(s.last_sync_at):>8}  "
            f"{_compact_status(s):<13}"
        )
        lines.append(line.rstrip())

    lines.append(_dash_line())

    # PENDING summary line
    pending_parts: list[str] = []
    for s in snapshots:
        if s.remote_error:
            pending_parts.append(f"{s.account}: ERR")
        else:
            pending_parts.append(f"{s.account}: {len(s.pending)}")
    pending_str = " | ".join(pending_parts)
    lines.append(f"PENDING       : {pending_str[: RSM_WIDTH - 16]}")

    # CLASSIFICACAO line
    cls_added = False
    cls_parts: list[str] = []
    for s in snapshots:
        total = s.routed_empresa + s.routed_pessoal
        if total > 0:
            emp_pct = round((s.routed_empresa / total) * 100)
            pes_pct = 100 - emp_pct
            cls_parts.append(
                f"[{s.account}] emp {s.routed_empresa}/{total} ({emp_pct}%), "
                f"pes {s.routed_pessoal}/{total} ({pes_pct}%)"
            )
            cls_added = True
    cls_msg = "; ".join(cls_parts) if cls_added else "--"
    lines.append(f"CLASSIFICACAO : {cls_msg[: RSM_WIDTH - 16]}")

    # FLAGS line
    all_flags: list[str] = []
    for s in snapshots:
        for flag in _collect_flags(s):
            all_flags.append(f"[{s.account}] {flag}")
    flags_str = "; ".join(all_flags) if all_flags else "OK"
    lines.append(f"FLAGS         : {flags_str[: RSM_WIDTH - 16]}")

    lines.append(_eq_line("Tip: fireflies_sync run to refresh"))
    return "\n".join(lines)


def render_pending_detail(snapshots: list[AccountSnapshot], top_n: int = 10) -> str:
    """Boxed pending detail block — one card per account with pendings.
    Each row shows date BRT, title, organizer, duration. Long titles
    are truncated. Header and separators match the rich dashboard style."""
    width = RICH_WIDTH
    blocks: list[str] = []
    for s in snapshots:
        if not s.pending:
            continue
        shown = min(top_n, len(s.pending))
        remaining = len(s.pending) - shown
        block: list[str] = []
        label = f"PENDENTES  ::  {s.account}  ::  top {shown} de {len(s.pending)}"
        block.append(_box_top(width, label=label))
        block.append(_box_line("", width))
        # Header row
        header = (
            f"  {'Data BRT':<16}  {'Titulo':<38}  "
            f"{'Organizador':<18}  {'Dur':>4}"
        )
        block.append(_box_line(header, width))
        block.append(_box_line("  " + "-" * (width - 8), width))
        for t in s.pending[:shown]:
            try:
                dt = datetime.fromtimestamp(t.date_ms / 1000, tz=BRT)
                date_brt = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, OSError, OverflowError):
                date_brt = "--"
            title = (t.title or "Untitled")[:38]
            organizer = (t.organizer or "--")[:18]
            dur = f"{int(t.duration_min):>3}m"
            block.append(_box_line(
                f"  {date_brt:<16}  {title:<38}  {organizer:<18}  {dur:>4}",
                width
            ))
        if remaining > 0:
            block.append(_box_line("", width))
            block.append(_box_line(f"  ... + {remaining} adicionais", width))
        block.append(_box_line("", width))
        block.append(_box_bottom(width))
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


# ============================================================================
# JSON emitter (for programmatic consumers)
# ============================================================================


def to_json(snapshots: list[AccountSnapshot]) -> dict[str, Any]:
    return {
        "rendered_at_utc": datetime.now(UTC).isoformat(),
        "rendered_at_brt": datetime.now(BRT).isoformat(),
        "accounts": [
            {
                "account": s.account,
                "api_available": s.api_available,
                "state_exists": s.state_exists,
                "state_path": str(s.state_path),
                "remote_total": s.remote_total,
                "remote_error": s.remote_error,
                "processed_count": s.processed_count,
                "skipped": s.skipped,
                "routed_empresa": s.routed_empresa,
                "routed_pessoal": s.routed_pessoal,
                "last_sync_at": s.last_sync_at,
                "next_tag": s.next_tag,
                "pending_count": len(s.pending),
                "pending": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "date_ms": t.date_ms,
                        "date_brt": (
                            datetime.fromtimestamp(t.date_ms / 1000, tz=BRT).isoformat()
                            if t.date_ms
                            else None
                        ),
                        "duration_min": t.duration_min,
                        "organizer": t.organizer,
                    }
                    for t in s.pending
                ],
            }
            for s in snapshots
        ],
    }


# ============================================================================
# CLI entrypoint
# ============================================================================


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render ASCII dashboard comparing Fireflies remote listing vs local Megabrain state files.",
    )
    parser.add_argument(
        "--account",
        action="append",
        help="Account label. Repeatable. Defaults to the configured primary account "
             "(MEGA_BRAIN_FIREFLIES_DEFAULT_ACCOUNT / MEGA_BRAIN_FIREFLIES_ACCOUNTS).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=TOP_N_DEFAULT,
        help=f"Top N pending per account (default {TOP_N_DEFAULT})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of ASCII",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Use RSM-1 compact 80-col layout instead of the rich dashboard",
    )
    args = parser.parse_args(argv)

    accounts = args.account or DEFAULT_ACCOUNTS
    snapshots = [snapshot(a) for a in accounts]

    if args.json:
        print(json.dumps(to_json(snapshots), ensure_ascii=False, indent=2))
        return 0

    if args.compact:
        print(render_dashboard_compact(snapshots, top_n=args.top))
    else:
        print(render_dashboard(snapshots, top_n=args.top))
    if args.top > 0:
        detail = render_pending_detail(snapshots, top_n=args.top)
        if detail:
            print()
            print(detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
