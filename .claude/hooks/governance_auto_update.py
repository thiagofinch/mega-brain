#!/usr/bin/env python3
"""Governance Cascade Hook — PostToolUse (Write|Edit)

Detects when source code modules are modified and reports which
governance documents need propagation updates.

Strategy: dynamic grep of the governance docs (CLAUDE.md files and
.claude/rules/*.md) for keywords taken from the modified module's name.

Output: JSON with governance propagation report visible in chat.
Never blocks (exit 0 always — advisory only).

Version: 3.0.0 — W3-001.6 (2026-04-16): absorbed governance_cascade.py (archived)
"""

from __future__ import annotations

import json
import re
import sys
from fnmatch import fnmatch
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent.parent

# Governance doc locations to scan in fallback mode
_GOV_SCAN_PATHS = [
    _ROOT / "CLAUDE.md",
    _ROOT / ".claude" / "CLAUDE.md",
]
_GOV_SCAN_DIR = _ROOT / ".claude" / "rules"

# Patterns that trigger governance cascade check
_WATCHED = [
    "engine/**/*.py",
    "agents/**/*.md",
    "workspace/**/*.yaml",
    ".claude/hooks/*.py",
    ".claude/skills/*/SKILL.md",
    "squads/*/config.yaml",
    "services/**/*.js",
    "engine/paths.py",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_relative(file_path: str) -> str:
    try:
        return str(Path(file_path).resolve().relative_to(_ROOT))
    except (ValueError, OSError):
        return file_path


def _match_glob(rel: str, pattern: str) -> bool:
    """Match a relative path against a glob pattern (supports **)."""
    if "**" in pattern:
        prefix = pattern.split("**")[0].rstrip("/")
        suffix = pattern.split("**")[-1].lstrip("/")
        if not rel.startswith(prefix):
            return False
        return not suffix or fnmatch(Path(rel).name, suffix.lstrip("*"))
    return fnmatch(rel, pattern)


def _is_watched(rel: str) -> bool:
    return any(_match_glob(rel, p) for p in _WATCHED)


# ---------------------------------------------------------------------------
# Dynamic grep of governance docs
# ---------------------------------------------------------------------------


def _grep_for_keywords(keywords: list[str]) -> list[dict]:
    """Scan governance docs for keyword references."""
    hits = []
    files_to_scan = list(_GOV_SCAN_PATHS)
    if _GOV_SCAN_DIR.is_dir():
        files_to_scan.extend(_GOV_SCAN_DIR.glob("*.md"))

    seen = set()
    for f in files_to_scan:
        if not f.exists() or not f.is_file():
            continue
        rel = str(f.relative_to(_ROOT))
        if rel in seen:
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")[:50_000]
            for kw in keywords:
                if re.search(re.escape(kw), content, re.IGNORECASE):
                    seen.add(rel)
                    hits.append({"path": rel, "section": f"(matched: {kw})"})
                    break
        except OSError:
            continue
    return hits


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        event = json.loads(raw)
        if event.get("tool_name", "") not in ("Write", "Edit"):
            sys.exit(0)

        file_path = event.get("tool_input", {}).get("file_path", "")
        if not file_path:
            sys.exit(0)

        rel = _to_relative(file_path)
        if not _is_watched(rel):
            sys.exit(0)

        stem_words = [w for w in Path(rel).stem.replace("_", " ").split() if len(w) > 3]
        docs = _grep_for_keywords(stem_words[:3]) if stem_words else []

        if not docs:
            sys.exit(0)

        # Build report
        fname = Path(rel).name
        lines = [f"[GOVERNANCE] {fname} modified"]
        for d in docs:
            section = f" ({d['section']})" if d.get("section") else ""
            lines.append(f"  -> {d['path']}{section} — NEEDS REVIEW")
        lines.append(f"  Cascade targets: {len(docs)}")

        print(json.dumps({"result": "\n".join(lines)}))
        sys.exit(0)

    except Exception as exc:
        # Never block — advisory only
        sys.stderr.write(f"governance_cascade: {exc!s}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
