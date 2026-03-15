"""
core/governance/pipeline_guard.py — Pipeline Output Validator

Validates that outputs from pipeline scripts land in ROUTING-defined paths.
Used as both a library and a hook.

Usage as library:
    from core.governance.pipeline_guard import validate_output_path
    is_valid, reason = validate_output_path("/path/to/output.json")

Usage as hook (PostToolUse):
    Automatically validates Write/Edit tool outputs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# ── PATHS ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent

# Lazy import to avoid circular deps
_ROUTING: dict[str, Path] | None = None
_ROUTING_PATHS: set[Path] | None = None


def _load_routing() -> tuple[dict[str, Path], set[Path]]:
    """Load ROUTING dict from core/paths.py."""
    global _ROUTING, _ROUTING_PATHS
    if _ROUTING is not None and _ROUTING_PATHS is not None:
        return _ROUTING, _ROUTING_PATHS

    try:
        from core.paths import ROUTING
        _ROUTING = {k: v if isinstance(v, Path) else Path(v) for k, v in ROUTING.items()}
        _ROUTING_PATHS = set(_ROUTING.values())
        return _ROUTING, _ROUTING_PATHS
    except ImportError:
        _ROUTING = {}
        _ROUTING_PATHS = set()
        return _ROUTING, _ROUTING_PATHS


# ── ALLOWED DIRECTORIES (not in ROUTING but always valid) ────────────────────

def _get_allowed_dirs() -> list[Path]:
    """Get list of directories that are always allowed for writes."""
    return [
        ROOT / ".claude" / "sessions",  # Session logs
        ROOT / ".claude" / "mission-control",  # State files
        ROOT / ".claude" / "jarvis",  # JARVIS state
        ROOT / ".claude" / "trash",  # Soft deletes
        ROOT / ".claude" / "skills",  # Generated skills
        ROOT / "logs",  # All logs
        ROOT / "artifacts",  # Pipeline artifacts
        ROOT / "processing",  # Pipeline processing
        ROOT / ".data",  # RAG indexes, caches
        ROOT / "knowledge",  # All knowledge buckets
        ROOT / "workspace",  # Business operations
        ROOT / "agents",  # Agent files
        ROOT / "docs" / "architecture",  # Governance-generated docs
        ROOT / "docs" / "plans",  # Planning docs
    ]


def _get_prohibited_dirs() -> list[Path]:
    """Get list of directories that should NEVER receive new files."""
    return [
        ROOT / "docs" / "framework",  # Deprecated
        ROOT / "workspace" / "domains",  # Removed S13
        ROOT / "workspace" / "providers",  # Removed S13
    ]


# ── VALIDATION ────────────────────────────────────────────────────────────────


def validate_output_path(path: str | Path) -> tuple[bool, str]:
    """Validate that an output path is in an allowed location.

    Args:
        path: The path to validate.

    Returns:
        Tuple of (is_valid, reason).
        - is_valid: True if path is allowed.
        - reason: Explanation of why valid or invalid.
    """
    path = Path(path).resolve()
    routing, routing_paths = _load_routing()

    # Check if in prohibited directories
    for prohibited in _get_prohibited_dirs():
        if path == prohibited or prohibited in path.parents:
            return False, f"Path is in prohibited directory: {prohibited.relative_to(ROOT)}"

    # Check if in allowed directories
    for allowed in _get_allowed_dirs():
        if path == allowed or allowed in path.parents:
            return True, f"Path is in allowed directory: {allowed.relative_to(ROOT)}"

    # Check if matches a ROUTING path
    for key, routing_path in routing.items():
        if path == routing_path or routing_path in path.parents:
            return True, f"Path matches ROUTING['{key}']"

    # Check if within ROOT but not in any registered path
    if ROOT in path.parents:
        # Allow top-level config files
        if path.parent == ROOT:
            allowed_extensions = {".md", ".yaml", ".yml", ".json", ".toml", ".txt"}
            if path.suffix.lower() in allowed_extensions:
                return True, "Top-level config file"

        # Warn but don't block unregistered paths
        return True, f"WARN: Path not in ROUTING, consider registering: {path.relative_to(ROOT)}"

    # Outside ROOT entirely
    return False, f"Path is outside project root: {path}"


def validate_write_tool(tool_input: dict[str, Any]) -> dict[str, Any]:
    """Validate a Write/Edit tool call.

    Args:
        tool_input: The tool input containing file_path.

    Returns:
        Dict with 'valid', 'path', and 'reason' keys.
    """
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return {"valid": False, "path": "", "reason": "No file_path provided"}

    is_valid, reason = validate_output_path(file_path)
    return {
        "valid": is_valid,
        "path": file_path,
        "reason": reason,
    }


# ── HOOK INTERFACE ────────────────────────────────────────────────────────────


def run_hook(event_data: dict[str, Any]) -> dict[str, Any]:
    """Hook entry point for PostToolUse event.

    Args:
        event_data: Contains 'tool_name' and 'tool_input'.

    Returns:
        Dict with validation result.
    """
    tool_name = event_data.get("tool_name", "")
    tool_input = event_data.get("tool_input", {})

    # Only validate write operations
    if tool_name not in ("Write", "Edit", "NotebookEdit"):
        return {"status": "skip", "reason": f"Not a write tool: {tool_name}"}

    result = validate_write_tool(tool_input)

    if not result["valid"]:
        return {
            "status": "warn",  # warn, not block
            "message": f"Pipeline guard: {result['reason']}",
            "path": result["path"],
        }

    if result["reason"].startswith("WARN:"):
        return {
            "status": "warn",
            "message": result["reason"],
            "path": result["path"],
        }

    return {
        "status": "pass",
        "message": result["reason"],
        "path": result["path"],
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Read from stdin for hook mode
    if len(sys.argv) > 1 and sys.argv[1] == "--hook":
        try:
            data = json.loads(sys.stdin.read())
            result = run_hook(data)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}))
            sys.exit(1)
    elif len(sys.argv) > 1:
        # Validate a specific path
        path = sys.argv[1]
        is_valid, reason = validate_output_path(path)
        print(f"{'✓' if is_valid else '✗'} {reason}")
        sys.exit(0 if is_valid else 1)
    else:
        print("Usage:")
        print("  python pipeline_guard.py <path>      # Validate a path")
        print("  python pipeline_guard.py --hook      # Run as hook (stdin JSON)")
