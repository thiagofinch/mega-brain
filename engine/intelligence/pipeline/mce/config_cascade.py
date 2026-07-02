"""
config_cascade.py -- 5-Level Configuration Cascade for MCE Pipeline
====================================================================

Resolves pipeline settings through a strict precedence hierarchy:

    Level 1 (highest):  CLI arguments (passed at construction)
    Level 2:            Environment variables (MCE_* prefix)
    Level 3:            Per-slug config (.claude/mission-control/mce/{SLUG}/config.yaml)
    Level 4:            Squad config (mega-brain/squads/mega-brain/config.yaml)
    Level 5 (lowest):   Defaults (defaults.yaml shipped with the pipeline)

First match wins. ``get(key)`` walks levels 1-5 and returns the first
non-None value found.

@include Directive (Story MCE22-2.4)
------------------------------------
YAML config files may contain ``@include`` directives to pull in other
config files.  Three path formats are supported:

    @include "absolute/path.yaml"     -- absolute path
    @include "./relative/path.yaml"   -- relative to the including file
    @include "~/home/path.yaml"       -- user home expansion

Circular references are detected and raise ``CircularIncludeError``.

Walk-Up Discovery (Story MCE22-2.4)
------------------------------------
``discover_configs(start_dir)`` walks from *start_dir* up to the
filesystem root, collecting every ``config.yaml`` found.  Files are
loaded from root downward so that closer (deeper) configs override
farther (shallower) ones -- "last loaded wins".

Constraints:
    - stdlib + PyYAML only (no LLM calls, no network).
    - Immutable after construction except for explicit ``override()``.
    - Thread-safe for reads (no mutation during get).

Usage::

    cfg = CascadeConfig(slug="alex-hormozi", cli_args={"model": "claude-sonnet-4-20250514"})
    model = cfg.get("model")                    # -> "claude-sonnet-4-20250514" (CLI wins)
    val, src = cfg.get_with_source("qa_mode")   # -> ("warning", "default")
    cfg.override("parallel", True)              # runtime override at level 1
    print(cfg.to_dict())                        # all resolved values with sources

    # Walk-up discovery
    merged = discover_configs(Path("/project/sub/deep"))
    # -> loads /project/config.yaml, then /project/sub/config.yaml,
    #    then /project/sub/deep/config.yaml (deeper overrides shallower)

Version: 2.0.0
Date: 2026-04-02
Story: MCE2-1.6, MCE22-2.4
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("mce.config_cascade")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ENV_PREFIX = "MCE_"

_DEFAULTS_PATH = Path(__file__).resolve().parent / "defaults.yaml"

# Source labels returned by get_with_source
SOURCE_CLI = "cli"
SOURCE_ENV = "env"
SOURCE_SLUG = "slug"
SOURCE_SQUAD = "squad"
SOURCE_DEFAULT = "default"

# Default config filename for walk-up discovery
_CONFIG_FILENAME = "config.yaml"


# ---------------------------------------------------------------------------
# Exceptions (Story MCE22-2.4)
# ---------------------------------------------------------------------------


class CircularIncludeError(Exception):
    """Raised when @include directives form a cycle.

    Attributes:
        chain: List of file paths forming the circular reference.
    """

    def __init__(self, chain: list[str]) -> None:
        self.chain = chain
        cycle_display = " -> ".join(chain)
        super().__init__(f"Circular @include detected: {cycle_display}")


# ---------------------------------------------------------------------------
# YAML loader (safe, returns empty dict on failure)
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict.

    Returns an empty dict when the file does not exist, is empty,
    or contains invalid YAML -- never raises.
    """
    if not path.is_file():
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.debug("Failed to load YAML %s: %s", path, exc)
        return {}


# ---------------------------------------------------------------------------
# Deep dict merge (Story MCE22-2.4)
# ---------------------------------------------------------------------------


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*.

    For nested dicts, the merge is recursive.  For all other types
    (lists, scalars), the override value replaces the base value
    entirely.  Neither input dict is mutated -- a new dict is returned.

    Args:
        base: The lower-priority config dict.
        override: The higher-priority config dict (wins on conflict).

    Returns:
        New merged dict.
    """
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


# ---------------------------------------------------------------------------
# @include directive resolution (Story MCE22-2.4)
# ---------------------------------------------------------------------------


def _resolve_include_path(directive: str, base_dir: Path) -> Path:
    """Resolve an @include path to an absolute Path.

    Supports 3 formats:
        @include "path/to/file.yaml"     -- absolute or relative to cwd
        @include "./relative/file.yaml"  -- relative to the including file
        @include "~/home/file.yaml"      -- user home expansion

    Args:
        directive: The raw path string from the @include directive.
        base_dir: Directory of the file containing the @include.

    Returns:
        Resolved absolute Path.
    """
    path_str = directive.strip()

    # Format 3: ~/home expansion
    if path_str.startswith("~"):
        return Path(os.path.expanduser(path_str)).resolve()

    # Format 2: ./relative -- resolve relative to including file's dir
    if path_str.startswith("./") or path_str.startswith("../"):
        return (base_dir / path_str).resolve()

    # Format 1: absolute path or path relative to including file's dir
    candidate = Path(path_str)
    if candidate.is_absolute():
        return candidate.resolve()

    # Non-absolute, non-dot-prefixed -- resolve relative to including file
    return (base_dir / path_str).resolve()


def load_yaml_with_includes(
    path: Path,
    *,
    _visited: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Load a YAML file, recursively resolving @include directives.

    Any top-level key whose value is a string starting with ``@include ``
    (or the special key ``@include``) triggers inclusion of the referenced
    file.  The included file's contents are deep-merged into the result.

    Alternatively, the value of a key can be a string like
    ``@include "./other.yaml"`` to inline that file's content under
    the key (but typically @include is used as a standalone top-level
    value to merge at root level).

    The function also scans for a special ``_includes`` list at the top
    level -- a list of paths to include in order:

    .. code-block:: yaml

        _includes:
          - "./base.yaml"
          - "~/shared/common.yaml"
        model: "custom-model"

    Circular references are detected via the *_visited* set.

    Args:
        path: Path to the YAML file.
        _visited: Internal set of already-processed file paths (for
                  circular reference detection).

    Returns:
        Merged dict with all @include directives resolved.

    Raises:
        CircularIncludeError: If a circular reference is detected.
    """
    resolved_path = str(path.resolve())

    if _visited is None:
        _visited = frozenset()

    if resolved_path in _visited:
        chain = list(_visited) + [resolved_path]
        raise CircularIncludeError(chain)

    new_visited = _visited | {resolved_path}

    raw = _load_yaml(path)
    if not raw:
        return {}

    base_dir = path.resolve().parent
    result: dict[str, Any] = {}

    # Process _includes list first (ordered, base layer)
    includes_list = raw.pop("_includes", None)
    if isinstance(includes_list, list):
        for inc_path_str in includes_list:
            if isinstance(inc_path_str, str):
                inc_path = _resolve_include_path(inc_path_str, base_dir)
                included = load_yaml_with_includes(inc_path, _visited=new_visited)
                result = _deep_merge(result, included)

    # Process remaining keys -- look for @include string values
    for key, value in raw.items():
        if isinstance(value, str) and value.strip().startswith("@include "):
            # Inline include: the value references another file
            inc_ref = value.strip()[len("@include ") :].strip().strip("'\"")
            inc_path = _resolve_include_path(inc_ref, base_dir)
            included = load_yaml_with_includes(inc_path, _visited=new_visited)
            # If key is "@include", merge at root level
            if key == "@include":
                result = _deep_merge(result, included)
            else:
                result[key] = included
        else:
            result[key] = value

    return result


# ---------------------------------------------------------------------------
# Walk-up config discovery (Story MCE22-2.4)
# ---------------------------------------------------------------------------


def discover_configs(
    start_dir: Path,
    *,
    config_filename: str = _CONFIG_FILENAME,
    stop_at: Path | None = None,
) -> dict[str, Any]:
    """Walk from *start_dir* up to root, collecting config files.

    Config files are loaded from the shallowest (closest to root) to
    the deepest (closest to cwd).  Deeper configs override shallower
    ones via deep merge -- "last loaded wins".

    Args:
        start_dir: Directory to start walking up from.
        config_filename: Name of config files to look for (default:
                         ``config.yaml``).
        stop_at: Optional directory to stop at (exclusive).  Useful
                 for testing to avoid walking the entire real filesystem.

    Returns:
        Deep-merged dict of all discovered config files.
    """
    configs_found: list[Path] = []
    current = start_dir.resolve()
    stop_resolved = stop_at.resolve() if stop_at else None

    while True:
        candidate = current / config_filename
        if candidate.is_file():
            configs_found.append(candidate)

        parent = current.parent
        if parent == current:
            # Reached filesystem root
            break
        if stop_resolved and parent == stop_resolved:
            break
        current = parent

    # Reverse: shallowest first, deepest last (last loaded wins)
    configs_found.reverse()

    merged: dict[str, Any] = {}
    for config_path in configs_found:
        loaded = load_yaml_with_includes(config_path)
        merged = _deep_merge(merged, loaded)
        logger.debug("Walk-up: loaded %s (%d keys)", config_path, len(loaded))

    return merged


# ---------------------------------------------------------------------------
# CascadeConfig
# ---------------------------------------------------------------------------


class CascadeConfig:
    """5-level configuration cascade for the MCE pipeline.

    Parameters
    ----------
    slug:
        Persona slug (e.g. ``"alex-hormozi"``).  Used to locate the
        per-slug config file at level 3.
    cli_args:
        Dict of CLI-provided overrides (level 1).  ``None`` values are
        ignored so callers can pass ``vars(argparse.Namespace)`` directly.
    project_root:
        Root of the mega-brain project.  Defaults to auto-detection
        (5 parents up from this file).
    megabrain_hub_root:
        Root of the mega-brain project.  If ``None`` or the path does
        not exist, level 4 (squad config) is silently skipped.
    """

    def __init__(
        self,
        slug: str,
        *,
        cli_args: dict[str, Any] | None = None,
        project_root: Path | None = None,
        megabrain_hub_root: Path | None = None,
    ) -> None:
        self._slug = slug

        # Resolve project root (same pattern used by cli.py / orchestrate.py)
        if project_root is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        self._project_root = project_root

        self._megabrain_hub_root = megabrain_hub_root

        # ── Level 1: CLI args (strip None values) ──
        self._cli: dict[str, Any] = {}
        if cli_args:
            self._cli = {k: v for k, v in cli_args.items() if v is not None}

        # ── Level 2: Environment variables (loaded once at init) ──
        self._env: dict[str, Any] = self._load_env()

        # ── Level 3: Per-slug config ──
        slug_config_path = (
            self._project_root / ".claude" / "mission-control" / "mce" / slug / "config.yaml"
        )
        self._slug_config: dict[str, Any] = _load_yaml(slug_config_path)
        if self._slug_config:
            logger.debug("Loaded per-slug config from %s", slug_config_path)

        # ── Level 4: Squad config ──
        self._squad_config: dict[str, Any] = self._load_squad_config()

        # ── Level 5: Defaults ──
        self._defaults: dict[str, Any] = _load_yaml(_DEFAULTS_PATH)
        if not self._defaults:
            logger.warning(
                "defaults.yaml not found or empty at %s -- all level-5 lookups will miss",
                _DEFAULTS_PATH,
            )

    # -- env loading --------------------------------------------------------

    @staticmethod
    def _load_env() -> dict[str, Any]:
        """Collect MCE_* environment variables into a key-value dict.

        The prefix is stripped and the key is lowercased:
        ``MCE_MODEL=claude-sonnet-4-20250514`` becomes ``{"model": "claude-sonnet-4-20250514"}``.

        Boolean-ish values (``"true"``/``"false"``, ``"1"``/``"0"``) are
        coerced to Python ``bool``.  Numeric strings are coerced to ``int``
        or ``float``.
        """
        result: dict[str, Any] = {}
        for key, raw in os.environ.items():
            if not key.startswith(_ENV_PREFIX):
                continue
            clean_key = key[len(_ENV_PREFIX) :].lower()
            result[clean_key] = _coerce_value(raw)
        return result

    # -- squad config loading -----------------------------------------------

    def _load_squad_config(self) -> dict[str, Any]:
        """Load squad-level config from mega-brain if available.

        Looks for ``squads/mega-brain/config.yaml`` under
        ``self._megabrain_hub_root``.  Falls back to the ``MEGABRAIN_HUB_ROOT``
        environment variable.  Returns empty dict if nothing is found.
        """
        hub_root = self._megabrain_hub_root

        # Fallback: check env var
        if hub_root is None:
            env_hub = os.environ.get("MEGABRAIN_HUB_ROOT")
            if env_hub:
                hub_root = Path(env_hub)

        if hub_root is None or not hub_root.is_dir():
            logger.debug("mega-brain root not available -- skipping squad config")
            return {}

        squad_path = hub_root / "squads" / "mega-brain" / "config.yaml"
        data = _load_yaml(squad_path)
        if data:
            logger.debug("Loaded squad config from %s", squad_path)

            # The squad config.yaml is a full squad manifest.  We extract
            # pipeline-relevant keys from the ``quality`` section and any
            # top-level keys that match known pipeline settings.
            flat: dict[str, Any] = {}
            quality = data.get("quality", {}) if isinstance(data.get("quality"), dict) else {}
            for k, v in quality.items():
                flat[k] = v

            # Also pick well-known top-level keys (if present)
            for top_key in (
                "model",
                "qa_mode",
                "parallel",
                "streaming",
                "isolation",
                "max_parallel",
                "context_budget_pct",
                "circuit_breaker_max",
            ):
                if top_key in data:
                    flat[top_key] = data[top_key]

            return flat

        return {}

    # -- public API ---------------------------------------------------------

    @property
    def slug(self) -> str:
        """The persona slug this config was built for."""
        return self._slug

    def get(self, key: str, default: Any = None) -> Any:
        """Resolve a config key through the 5-level cascade.

        Returns the first non-None value found walking levels 1-5.
        If no level has the key, returns *default*.
        """
        # Level 1: CLI
        if key in self._cli:
            return self._cli[key]

        # Level 2: ENV
        if key in self._env:
            return self._env[key]

        # Level 3: Per-slug
        if key in self._slug_config:
            return self._slug_config[key]

        # Level 4: Squad
        if key in self._squad_config:
            return self._squad_config[key]

        # Level 5: Defaults
        if key in self._defaults:
            return self._defaults[key]

        return default

    def get_with_source(self, key: str) -> tuple[Any, str]:
        """Resolve a key and return ``(value, source_label)``.

        *source_label* is one of:
        ``"cli"``, ``"env"``, ``"slug"``, ``"squad"``, ``"default"``.

        Returns ``(None, "default")`` when the key is not found at any
        level (including defaults).
        """
        levels: list[tuple[dict[str, Any], str]] = [
            (self._cli, SOURCE_CLI),
            (self._env, SOURCE_ENV),
            (self._slug_config, SOURCE_SLUG),
            (self._squad_config, SOURCE_SQUAD),
            (self._defaults, SOURCE_DEFAULT),
        ]

        for store, label in levels:
            if key in store:
                return store[key], label

        return None, SOURCE_DEFAULT

    def override(self, key: str, value: Any) -> None:
        """Inject a runtime override at level 1 (CLI).

        This is the highest-precedence level, so subsequent ``get()``
        calls for *key* will always return *value*.
        """
        self._cli[key] = value

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Dump all resolved values with their sources.

        Returns a dict where each key maps to
        ``{"value": ..., "source": ...}``.
        """
        # Collect all known keys from every level
        all_keys: set[str] = set()
        all_keys.update(self._cli)
        all_keys.update(self._env)
        all_keys.update(self._slug_config)
        all_keys.update(self._squad_config)
        all_keys.update(self._defaults)

        result: dict[str, dict[str, Any]] = {}
        for key in sorted(all_keys):
            value, source = self.get_with_source(key)
            result[key] = {"value": value, "source": source}

        return result

    def __repr__(self) -> str:
        levels_loaded = []
        if self._cli:
            levels_loaded.append(f"cli({len(self._cli)})")
        if self._env:
            levels_loaded.append(f"env({len(self._env)})")
        if self._slug_config:
            levels_loaded.append(f"slug({len(self._slug_config)})")
        if self._squad_config:
            levels_loaded.append(f"squad({len(self._squad_config)})")
        if self._defaults:
            levels_loaded.append(f"defaults({len(self._defaults)})")
        return f"CascadeConfig(slug={self._slug!r}, " f"levels=[{', '.join(levels_loaded)}])"


# ---------------------------------------------------------------------------
# Value coercion helper
# ---------------------------------------------------------------------------


def _coerce_value(raw: str) -> Any:
    """Coerce a string value from an env var to a Python type.

    Handles booleans, integers, and floats.  Falls back to the
    original string if no conversion applies.
    """
    lowered = raw.lower().strip()

    # Booleans
    if lowered in ("true", "1", "yes"):
        return True
    if lowered in ("false", "0", "no"):
        return False

    # Integers
    try:
        return int(raw)
    except ValueError:
        pass

    # Floats
    try:
        return float(raw)
    except ValueError:
        pass

    return raw
