#!/usr/bin/env python3
"""
Workspace Contract Guard — PreToolUse Hook
==========================================
Intercepts Write/Edit operations targeting ``workspace/`` paths and validates
them against the CSO governance model.

Hook Type: PreToolUse (Write|Edit)
Original: 2026-03-23 (fail-open legacy checks)

ACTOR-CONSCIOUSNESS (why this hook is safe for the MCE pipeline)
----------------------------------------------------------------
This is a **PreToolUse** hook — it ONLY fires on Claude tool calls (Write/Edit).
The MCE pipeline and the ``@jarvis-workspace`` governance motor write L0-L4 via
**native Python filesystem** (``engine/**`` — ``open()`` / ``Path.write_text``),
which never routes through a Claude tool, so it is exempt **by construction**
(risk F4). This guard, like the ``settings.json`` deny[], only gates the
ad-hoc session-agent write path. No agent-name allow-list is needed — the actor
distinction is structural (Python-native path vs. Claude-tool path).

CHECKS (in order)
-----------------
1. macOS duplicate filename (``* 2.*`` / `` <N>.``) -> block (all workspace layers).
2. Legacy hygiene from workspace.yaml (forbidden_patterns, uppercase dirs,
   sacred boundaries) — preserved for backward compat.

Nota: a consulta ao registry por documento (``document-registry.yaml``) nao faz
parte desta distribuicao; o guard aplica somente as checagens 1 e 2.

ENV KILL-SWITCHES
-----------------
- ``WORKSPACE_GUARD_DISABLED=1``   -> full rollback: guard becomes advisory-only
  everywhere (never blocks).

EXIT CODES
----------
- 0: approve (allow operation)
- 2: block (violation detected)

ERROR HANDLING
--------------
- Qualquer erro interno: fail-OPEN (allow).
"""

import fnmatch
import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
WORKSPACE_CONFIG = PROJECT_ROOT / "workspace" / "_system" / "config" / "workspace.yaml"

# macOS Finder/iCloud duplicate suffix: "name 2.ext", "name 3.ext", ...
_DUPE_RE = re.compile(r" \d+\.[^/]+$")

# Layer segment like "l0-identity" / "L0-identity" / "L1-strategy" -> canonical "L0".."L4".
_LAYER_RE = re.compile(r"^[lL]([0-4])-")

_config_cache: "dict | None" = None


def _guard_disabled() -> bool:
    """Full rollback flag — guard becomes advisory-only (never blocks)."""
    return os.environ.get("WORKSPACE_GUARD_DISABLED", "").strip() in ("1", "true", "yes", "on")


def _load_config() -> "dict | None":
    """Load workspace.yaml once per invocation. Returns None if not found."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    if not WORKSPACE_CONFIG.exists():
        return None
    try:
        import yaml

        with open(WORKSPACE_CONFIG, encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f)
        return _config_cache
    except Exception:
        return None


def _normalize_path(file_path: str) -> str:
    """Normalize to a repo-relative, forward-slash path."""
    fp = Path(file_path)
    if not fp.is_absolute():
        fp = (PROJECT_ROOT / fp)
    fp = fp.resolve()
    pd = PROJECT_ROOT.resolve()
    try:
        return str(fp.relative_to(pd)).replace("\\", "/")
    except ValueError:
        return file_path.replace("\\", "/")


def _is_workspace_path(relative_path: str) -> bool:
    return relative_path.startswith("workspace/") or relative_path == "workspace"


def _bu_and_layer(relative_path: str) -> "tuple[str | None, str | None]":
    """Extract (bu_slug, canonical_layer) for workspace/businesses/{bu}/{layer}/...

    ``canonical_layer`` is ``L0``..``L4`` (casing-normalized), or None if the path
    is not under a business-unit L*-layer directory.
    """
    parts = relative_path.split("/")
    # workspace / businesses / {bu} / {layer} / ...
    if len(parts) >= 5 and parts[0] == "workspace" and parts[1] == "businesses":
        bu_slug = parts[2]
        m = _LAYER_RE.match(parts[3])
        if m:
            return bu_slug, "L" + m.group(1)
        return bu_slug, None
    return None, None


def _check_dupe(filename: str) -> "str | None":
    """macOS duplicate filename (`* 2.*`) — AC4."""
    if fnmatch.fnmatch(filename, "* 2.*") or _DUPE_RE.search(filename):
        return f"Filename '{filename}' is a macOS duplicate (matches '* 2.*') — remove the copy"
    return None


def _check_forbidden_patterns(filename: str, forbidden_patterns: list) -> "str | None":
    for pattern in forbidden_patterns:
        if fnmatch.fnmatch(filename, pattern):
            return f"Filename '{filename}' matches forbidden pattern '{pattern}'"
    return None


def _check_uppercase_dirs(relative_path: str) -> "str | None":
    parts = Path(relative_path).parts
    for part in parts[:-1]:
        if part.startswith("_"):
            check_part = part[1:]
        elif re.match(r"^L[0-4]-", part):
            # Canonical layer directory (uppercase L*) — allowed.
            continue
        else:
            check_part = part
        if check_part != check_part.lower():
            return f"Uppercase in directory name: '{part}' in path {relative_path}"
    return None


def _check_sacred_boundaries(relative_path: str, sacred_boundaries: list) -> "str | None":
    for boundary in sacred_boundaries:
        sacred_path = boundary.get("path", "")
        if sacred_path and relative_path.startswith(sacred_path):
            reason = boundary.get("reason", "protected path")
            return f"Path '{relative_path}' is in sacred boundary '{sacred_path}': {reason}"
    return None


def _block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": f"[Workspace Contract Guard] {reason}"}))
    sys.exit(2)


def _approve(note: "str | None" = None) -> None:
    out = {"decision": "approve"}
    if note:
        out["note"] = note
    print(json.dumps(out))
    sys.exit(0)


def main() -> None:
    try:
        input_data = sys.stdin.read()
        if not input_data:
            _approve()

        hook_input = json.loads(input_data)
        tool_name = hook_input.get("tool_name", "")
        tool_input = hook_input.get("tool_input", {})

        if tool_name not in ("Write", "Edit", "write", "edit"):
            _approve()

        file_path = tool_input.get("file_path", "")
        if not file_path:
            _approve()

        relative_path = _normalize_path(file_path)
        if not _is_workspace_path(relative_path):
            _approve()

        filename = Path(relative_path).name
        bu_slug, layer = _bu_and_layer(relative_path)
        disabled = _guard_disabled()

        # --- Hard hygiene violations (dupe + legacy) — always block unless rollback ---
        hard: list = []
        # AC4: macOS duplicate (`* 2.*`) — unconditional (all workspace layers).
        reason = _check_dupe(filename)
        if reason:
            hard.append(reason)
        # Legacy hygiene from workspace.yaml (backward compat).
        config = _load_config()
        if config is not None:
            governance = config.get("governance", {}) or {}
            structure = governance.get("structure", {}) or {}
            forbidden_patterns = structure.get("forbidden_patterns", []) or []
            sacred_boundaries = config.get("sacred_boundaries", []) or []
            for chk in (
                _check_forbidden_patterns(filename, forbidden_patterns),
                _check_uppercase_dirs(relative_path),
                _check_sacred_boundaries(relative_path, sacred_boundaries),
            ):
                if chk:
                    hard.append(chk)

        # --- Decision ---
        if disabled:
            # Rollback: advisory-only everywhere (never blocks).
            if hard:
                _approve(note=f"[advisory][WORKSPACE_GUARD_DISABLED] {'; '.join(hard)}")
            _approve()

        # Hard hygiene blocks regardless of layer.
        if hard:
            _block("; ".join(hard))

        _approve()

    except json.JSONDecodeError:
        _approve()  # fail-OPEN: can't parse input
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        # Fail-OPEN for unexpected top-level errors (non-workspace-scoped).
        print(json.dumps({"decision": "approve", "error": str(e)}))
        sys.exit(0)


if __name__ == "__main__":
    main()
