#!/usr/bin/env python3
"""
Workspace Contract Guard — PreToolUse Hook (schema-aware)
=========================================================
Intercepts Write/Edit operations targeting ``workspace/`` paths and validates
them against the CSO governance model.

Hook Type: PreToolUse (Write|Edit)
Story: 211.W3.1 (upgrade fail-open -> schema-aware fail-closed) — Wave 3 Enforcement ON
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
3. Schema-aware **registry-consult** (option (b), ratified default — the per-BU
   ``document-registry.yaml`` is 100%/drift-0/deterministic since W1.1; we do NOT
   require in-file ``_meta`` and do NOT mass-edit the 423 YAMLs):
     - L0-identity / L1-strategy: **fail-CLOSED** — an unregistered doc, a doc
       whose registry entry lacks ``state``/``owner``/``layer``, OR any internal
       error (registry unavailable) -> **block**.
     - L2/L3/L4: **advisory** (warn + allow) by default; flips to blocking under
       the ``WORKSPACE_GUARD_L2L4_MODE=blocking`` kill-switch (TK-RG-004 pattern).

ENV KILL-SWITCHES
-----------------
- ``WORKSPACE_GUARD_DISABLED=1``   -> full rollback: guard becomes advisory-only
  everywhere (never blocks). PLANO §E.5 rollback flag.
- ``WORKSPACE_GUARD_L2L4_MODE``    -> ``advisory`` (default) | ``blocking``.

EXIT CODES
----------
- 0: approve (allow operation)
- 2: block (violation detected)

ERROR HANDLING
--------------
- Non-workspace paths, L2-L4 (advisory): fail-OPEN (allow) on any error.
- L0/L1 layered docs: fail-CLOSED (block) on any internal error (AC3).
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

# Layers that are fail-closed (human sign-off required; guarded hard).
_FAIL_CLOSED_LAYERS = {"L0", "L1"}

_config_cache: "dict | None" = None


def _guard_disabled() -> bool:
    """Full rollback flag — guard becomes advisory-only (never blocks)."""
    return os.environ.get("WORKSPACE_GUARD_DISABLED", "").strip() in ("1", "true", "yes", "on")


def _l2l4_blocking() -> bool:
    """Kill-switch: flip L2-L4 from advisory (default) to blocking."""
    return os.environ.get("WORKSPACE_GUARD_L2L4_MODE", "advisory").strip().lower() == "blocking"


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


def _schema_check(relative_path: str, bu_slug: str) -> "str | None":
    """Registry-consult (option b): the target doc must be a registered document
    whose registry entry carries the governance schema (``state``/``owner``/``layer``).

    Returns a violation reason (str) when the doc is unregistered or its entry is
    schema-incomplete, or None when it validates. Raises on internal errors — the
    caller decides fail-closed (L0/L1) vs advisory (L2-L4).
    """
    # Import the CSO registry read-side (AC3: guard imports engine/governance/registry.py).
    root_str = str(PROJECT_ROOT.resolve())
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    from engine.governance.registry import load_registry  # may raise ImportError

    registry = load_registry(PROJECT_ROOT, bu_slug)  # may raise FileNotFoundError
    path_map = {
        doc.get("path"): doc
        for doc in registry.get("documents", [])
        if isinstance(doc, dict) and doc.get("path")
    }
    entry = path_map.get(relative_path)
    if entry is None:
        return (
            f"Document '{relative_path}' is not registered in the {bu_slug} "
            "document-registry.yaml — governed docs must be registered "
            "(written by the MCE pipeline / @jarvis-workspace, not ad-hoc)"
        )
    missing = [k for k in ("state", "owner", "layer") if entry.get(k) in (None, "")]
    if missing:
        return (
            f"Registry entry for '{relative_path}' is schema-incomplete "
            f"(missing/empty: {', '.join(missing)})"
        )
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
        fail_closed = layer in _FAIL_CLOSED_LAYERS
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

        # --- Schema-aware registry-consult for L0-L4 layered docs (AC3) ---
        schema_reason: "str | None" = None
        schema_error = False
        if bu_slug and layer:
            try:
                schema_reason = _schema_check(relative_path, bu_slug)
            except Exception as exc:  # noqa: BLE001 — internal error handling is the point
                schema_error = True
                schema_reason = f"schema validation unavailable ({exc})"

        # --- Decision ---
        if disabled:
            # PLANO §E.5 rollback: advisory-only everywhere (never blocks).
            notes = hard + ([schema_reason] if schema_reason else [])
            if notes:
                _approve(note=f"[advisory][WORKSPACE_GUARD_DISABLED] {'; '.join(notes)}")
            _approve()

        # Hard hygiene blocks regardless of layer.
        if hard:
            _block("; ".join(hard))

        # Schema: L0/L1 fail-closed (block); L2-L4 advisory unless kill-switch blocking.
        if schema_reason:
            if fail_closed:
                if schema_error:
                    _block(f"{schema_reason} for {layer} doc '{relative_path}' — fail-closed")
                _block(schema_reason)
            if _l2l4_blocking():
                _block(schema_reason)
            _approve(note=f"[advisory][{layer}] {schema_reason}")

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
