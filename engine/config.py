"""
Mega Brain - Centralised configuration lookup.

Single entry point for settings and credentials used across the engine::

    from engine.config import get_config

    api_key = get_config("OPENAI_API_KEY")            # None when absent
    model = get_config("RAG_SYNTHESIS_MODEL", default="gpt-4o-mini")

Resolution order (first non-empty value wins):
    1. process environment (``os.environ``)
    2. ``.env`` file at the repository root
    3. ``default`` passed by the caller (``None`` if omitted)

Design rules:
    - ``.env`` is the only source of credentials (see .claude/CLAUDE.md).
    - Never raises for a missing key: absence returns ``default`` / ``None``,
      so every optional integration stays disabled instead of failing.
    - No network, no new dependencies (stdlib only).
    - The ``.env`` file is parsed once and cached; the process environment is
      always read live. The ``.env`` values never overwrite ``os.environ``.
    - Empty or whitespace-only values count as "not set".
"""

import os
from functools import lru_cache
from pathlib import Path

__all__ = ["get_config", "reload_config"]

# engine/config.py -> repository root
_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _REPO_ROOT / ".env"


def _parse_env_line(line: str):
    """Parse one ``KEY=VALUE`` line. Returns ``(key, value)`` or ``None``."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[len("export "):].lstrip()
    key, sep, value = line.partition("=")
    key = key.strip()
    if not sep or not key:
        return None
    value = value.strip()
    if value[:1] in ("'", '"'):
        # Quoted value: keep everything up to the matching closing quote.
        end = value.find(value[0], 1)
        value = value[1:end] if end != -1 else value[1:]
    else:
        # Unquoted value: a leading "#" is a comment (KEY=  # fill in), and so is
        # a trailing " # ...".
        if value.startswith("#"):
            value = ""
        hash_at = value.find(" #")
        if hash_at != -1:
            value = value[:hash_at].rstrip()
    return key, value


@lru_cache(maxsize=1)
def _load_env_file() -> dict:
    """Read the repository ``.env`` once. Missing/unreadable file -> ``{}``."""
    values: dict = {}
    try:
        text = _ENV_FILE.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return values
    for raw in text.splitlines():
        parsed = _parse_env_line(raw)
        if parsed:
            values[parsed[0]] = parsed[1]
    return values


def get_config(key: str, default=None):
    """
    Resolve a configuration value.

    Args:
        key: Variable name (e.g. ``"OPENAI_API_KEY"``).
        default: Returned when the key is unset or empty.

    Returns:
        The value as ``str``, or ``default`` (``None`` when omitted).
    """
    value = os.environ.get(key)
    if value is None or not value.strip():
        value = _load_env_file().get(key)
    if value is None or not value.strip():
        return default
    return value


def reload_config() -> None:
    """Drop the cached ``.env`` so the next ``get_config`` re-reads it."""
    _load_env_file.cache_clear()
