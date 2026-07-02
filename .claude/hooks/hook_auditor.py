#!/usr/bin/env python3
"""
Hook Auditor Meta-Hook -- SessionStart
========================================
Audits the health of ALL hooks wired in settings.json on every session start.

Checks performed:
  1. File existence for each hook referenced in settings.json
  2. AST parse validity for Python hooks
  3. Execute permission for shell hooks
  4. Stale core/ path detection (delegates to scripts/validate_hook_imports.py logic)

Output: Compact health score printed to stdout on startup.

Hook: SessionStart | Timeout: 10s
Story: W4-001.5
AC: hook_auditor.py exists, runs on SessionStart, reports score, uses validate_hook_imports

EXIT CODES:
  0 -- ALLOW (always, never blocks session start)

ERROR HANDLING: fail-OPEN
"""

import ast
import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
SETTINGS_PATH = PROJECT_ROOT / ".claude" / "settings.json"
STALE_CORE_PATTERN = re.compile(r"(?<!\.mega-brain-)(?<!\w)core/")

# The env var prefix to strip from hook command paths
_ENV_PREFIX = "$CLAUDE_PROJECT_DIR/"


def extract_hook_paths(settings: dict) -> list[str]:
    """Extract unique hook file paths from settings.json hooks config."""
    paths: list[str] = []
    hooks_block = settings.get("hooks", {})
    for _event, matchers in hooks_block.items():
        if not isinstance(matchers, list):
            continue
        for matcher_obj in matchers:
            hook_list = matcher_obj.get("hooks", [])
            if not isinstance(hook_list, list):
                continue
            for hook in hook_list:
                cmd = hook.get("command", "")
                parts = cmd.split('"')
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    clean = part.replace(_ENV_PREFIX, "")
                    if clean.endswith("pyrun.sh") or clean == "bash":
                        continue
                    if clean.endswith(".py") or clean.endswith(".sh"):
                        paths.append(clean)
    seen: set[str] = set()
    unique: list[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def check_existence(relpath: str):
    """Returns error string if file missing, else None."""
    if not (PROJECT_ROOT / relpath).exists():
        return f"MISSING: {relpath}"
    return None


def check_python_ast(relpath: str):
    """Returns error string if Python AST parse fails, else None."""
    full = PROJECT_ROOT / relpath
    try:
        source = full.read_text(encoding="utf-8")
        ast.parse(source, filename=relpath)
    except SyntaxError as e:
        return f"SYNTAX: {relpath}:{e.lineno} {e.msg}"
    except Exception as e:
        return f"READ: {relpath} {str(e)[:60]}"
    return None


def check_shell_exec(relpath: str):
    """Returns error string if shell hook lacks exec permission, else None."""
    full = PROJECT_ROOT / relpath
    if not os.access(full, os.X_OK):
        return f"NO_EXEC: {relpath}"
    return None


def check_stale_core_paths(relpath: str) -> list[str]:
    """Returns list of stale core/ path warnings."""
    full = PROJECT_ROOT / relpath
    warnings: list[str] = []
    try:
        lines = full.read_text(encoding="utf-8").splitlines()
    except Exception:
        return warnings
    in_docstring = False
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Skip comments
        if stripped.startswith("#"):
            continue
        # Track triple-quote docstrings
        triple_count = line.count('"""') + line.count("'''")
        if triple_count % 2 == 1:
            in_docstring = not in_docstring
        if in_docstring:
            continue
        # Skip lines that are string literals or regex patterns
        if stripped.startswith(("r'", 'r"', "'", '"')):
            continue
        # Skip regex compile definitions (they contain patterns, not paths)
        if "re.compile(" in stripped:
            continue
        if STALE_CORE_PATTERN.search(line):
            warnings.append(f"STALE_PATH: {relpath}:{lineno}")
    return warnings


def main() -> None:
    try:
        if not SETTINGS_PATH.exists():
            print("[HookAudit] settings.json not found -- skipping")
            sys.exit(0)

        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"[HookAudit] settings.json parse error: {str(e)[:60]}")
            sys.exit(0)

        hook_paths = extract_hook_paths(settings)
        if not hook_paths:
            print("[HookAudit] No hooks found in settings.json")
            sys.exit(0)

        total = len(hook_paths)
        issues: list[str] = []

        for relpath in hook_paths:
            # 1. Existence
            err = check_existence(relpath)
            if err:
                issues.append(err)
                continue

            # 2. Language-specific checks
            if relpath.endswith(".py"):
                err = check_python_ast(relpath)
                if err:
                    issues.append(err)
                stale = check_stale_core_paths(relpath)
                issues.extend(stale)

            elif relpath.endswith(".sh"):
                err = check_shell_exec(relpath)
                if err:
                    issues.append(err)
                stale = check_stale_core_paths(relpath)
                issues.extend(stale)

        # Calculate score
        hooks_with_issues: set[str] = set()
        for issue in issues:
            parts = issue.split(": ", 1)
            if len(parts) > 1:
                path_part = parts[1].split(":")[0].strip()
                hooks_with_issues.add(path_part)

        healthy = total - len(hooks_with_issues)
        pct = (healthy / total * 100) if total > 0 else 0

        if not issues:
            print(f"[HookAudit] {healthy}/{total} hooks healthy ({pct:.0f}%)")
        else:
            sample = issues[:3]
            remaining = len(issues) - 3
            summary = "; ".join(sample)
            if remaining > 0:
                summary += f" (+{remaining} more)"
            print(f"[HookAudit] {healthy}/{total} hooks healthy ({pct:.0f}%) | Issues: {summary}")

    except Exception as e:
        print(f"[HookAudit] error: {str(e)[:80]}")

    sys.exit(0)


if __name__ == "__main__":
    main()
