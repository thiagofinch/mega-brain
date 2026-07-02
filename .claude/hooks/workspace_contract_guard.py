#!/usr/bin/env python3
"""
Workspace Contract Guard — PreToolUse Hook
===========================================
Intercepts Write/Edit operations targeting workspace/ paths and validates
them against workspace.yaml governance rules.

Hook Type: PreToolUse (Write|Edit)
Date: 2026-03-23

CHECKS:
1. Filename does not match forbidden_patterns from workspace.yaml
2. No uppercase in directory names under workspace/
3. Path is not in sacred_boundaries

EXIT CODES:
- 0: Passed (allow operation)
- 2: Blocked (violation detected)

ERROR HANDLING: fail-OPEN
- If workspace.yaml does not exist -> allow all (first-time setup)
- If JSON parsing fails -> allow (don't block on hook errors)
- Any internal exception -> allow
"""

import fnmatch
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
WORKSPACE_CONFIG = PROJECT_ROOT / "workspace" / "_system" / "config" / "workspace.yaml"

# Cache parsed config (one read per invocation)
_config_cache: dict | None = None


def _load_config() -> dict | None:
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
    """Normalize path to relative, forward-slash format."""
    fp = Path(file_path).resolve()
    pd = PROJECT_ROOT.resolve()

    try:
        rel = fp.relative_to(pd)
        return str(rel).replace("\\", "/")
    except ValueError:
        return file_path.replace("\\", "/")


def _is_workspace_path(relative_path: str) -> bool:
    """Check if the path is under workspace/."""
    return relative_path.startswith("workspace/") or relative_path == "workspace"


def _check_forbidden_patterns(filename: str, forbidden_patterns: list[str]) -> str | None:
    """Check if filename matches any forbidden pattern. Returns reason or None."""
    for pattern in forbidden_patterns:
        if fnmatch.fnmatch(filename, pattern):
            return f"Filename '{filename}' matches forbidden pattern '{pattern}'"
    return None


def _check_uppercase_dirs(relative_path: str) -> str | None:
    """Check for uppercase in directory names under workspace/."""
    import re as _re

    parts = Path(relative_path).parts
    # Skip the file itself (last part), check directories only
    for part in parts[:-1]:
        if part.startswith("_"):
            # Skip _system, _templates etc — convention allows leading underscore
            check_part = part[1:]
        elif _re.match(r"^L[0-4]-", part):
            # Skip L0-identity, L1-strategy, etc — canonical layer directories
            continue
        else:
            check_part = part
        if check_part != check_part.lower():
            return f"Uppercase in directory name: '{part}' in path {relative_path}"
    return None


def _check_sacred_boundaries(relative_path: str, sacred_boundaries: list[dict]) -> str | None:
    """Check if path is in a sacred boundary (should not be in workspace/, but verify)."""
    for boundary in sacred_boundaries:
        sacred_path = boundary.get("path", "")
        if relative_path.startswith(sacred_path):
            reason = boundary.get("reason", "protected path")
            return f"Path '{relative_path}' is in sacred boundary '{sacred_path}': {reason}"
    return None


def main():
    """Hook entry point. Reads JSON from stdin, outputs JSON to stdout."""
    try:
        input_data = sys.stdin.read()
        if not input_data:
            print(json.dumps({"decision": "approve"}))
            return

        hook_input = json.loads(input_data)
        tool_name = hook_input.get("tool_name", "")
        tool_input = hook_input.get("tool_input", {})

        # Only check Write and Edit tools
        if tool_name not in ("Write", "Edit", "write", "edit"):
            print(json.dumps({"decision": "approve"}))
            return

        file_path = tool_input.get("file_path", "")
        if not file_path:
            print(json.dumps({"decision": "approve"}))
            return

        relative_path = _normalize_path(file_path)

        # Only activate for workspace/ paths
        if not _is_workspace_path(relative_path):
            print(json.dumps({"decision": "approve"}))
            return

        # Load config — if missing, allow all (first-time setup)
        config = _load_config()
        if config is None:
            print(json.dumps({"decision": "approve"}))
            return

        governance = config.get("governance", {})
        structure = governance.get("structure", {})
        forbidden_patterns = structure.get("forbidden_patterns", [])
        sacred_boundaries = config.get("sacred_boundaries", [])

        # Run checks
        violations: list[str] = []

        filename = Path(relative_path).name

        # Check 1: Forbidden patterns
        reason = _check_forbidden_patterns(filename, forbidden_patterns)
        if reason:
            violations.append(reason)

        # Check 2: Uppercase in directory names
        reason = _check_uppercase_dirs(relative_path)
        if reason:
            violations.append(reason)

        # Check 3: Sacred boundaries (workspace writes should NOT target sacred paths,
        # but this guards against confused paths)
        reason = _check_sacred_boundaries(relative_path, sacred_boundaries)
        if reason:
            violations.append(reason)

        if violations:
            combined = "; ".join(violations)
            print(
                json.dumps(
                    {
                        "decision": "block",
                        "reason": f"[Workspace Contract Guard] {combined}",
                    }
                )
            )
            sys.exit(2)
        else:
            print(json.dumps({"decision": "approve"}))
            sys.exit(0)

    except json.JSONDecodeError:
        # Fail-OPEN: can't parse input
        print(json.dumps({"decision": "approve"}))
        sys.exit(0)
    except Exception as e:
        # Fail-OPEN: don't block on internal errors
        print(json.dumps({"decision": "approve", "error": str(e)}))
        sys.exit(0)


if __name__ == "__main__":
    main()
