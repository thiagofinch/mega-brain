"""
theme_agent_map.py -- Deterministic theme/framework → cargo agent mapping
=========================================================================
Loads engine/config/theme-to-agents.yaml and exposes resolve functions
used by cascading.py as the SECOND lookup mechanism (complement to the
DNA-CONFIG reverse lookup which is mechanism 1).

Story MCE-11.6: THEME_TO_AGENTS + FRAMEWORK_TO_AGENTS mapping.

Ported from OLD MegaBrain THEME_TO_AGENTS / FRAMEWORK_TO_AGENTS Python
dicts (MEGA-BRAIN-PIPELINE-TECHNICAL-DOC.md §7.1, lines 802-835).

Constraints:
    - Python 3, stdlib + PyYAML only.
    - Raises no exceptions to callers — all errors logged + empty set returned.
    - Slug validation: warns for slugs not found on filesystem, never crashes.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("mce.theme_agent_map")

# Canonical path for the mapping config.
_CONFIG_PATH: Path = Path(__file__).parent.parent.parent.parent / "config" / "theme-to-agents.yaml"


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


class ThemeAgentMap:
    """Holds the loaded theme_to_agents and framework_to_agents tables.

    Provides resolve methods for both lookups.  The instance is loaded once
    and cached (see load_theme_agent_map()).

    Args:
        config_path: Path to theme-to-agents.yaml.  Defaults to
            engine/config/theme-to-agents.yaml resolved relative to this
            module's location.
        agents_cargo_root: Root of cargo agents tree used for slug validation.
            When None, validation is skipped (useful in tests).
    """

    def __init__(
        self,
        config_path: Path | None = None,
        agents_cargo_root: Path | None = None,
    ) -> None:
        self._config_path: Path = config_path or _CONFIG_PATH
        self._agents_cargo_root: Path | None = agents_cargo_root
        self._theme_map: dict[str, list[str]] = {}
        self._framework_map: dict[str, list[str]] = {}
        self._loaded: bool = False
        self._load()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Parse YAML and populate internal maps.  Non-fatal on errors."""
        if not self._config_path.exists():
            logger.warning(
                "theme_agent_map: config not found at %s — deterministic routing disabled",
                self._config_path,
            )
            return

        try:
            raw = yaml.safe_load(self._config_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("theme_agent_map: failed to parse YAML — %s", exc)
            return

        if not isinstance(raw, dict):
            logger.warning("theme_agent_map: unexpected YAML root type %s", type(raw).__name__)
            return

        # Validate known cargo slugs if cargo root is available.
        known_slugs: set[str] | None = None
        if self._agents_cargo_root and self._agents_cargo_root.is_dir():
            known_slugs = {p.parent.name for p in self._agents_cargo_root.rglob("DNA-CONFIG.yaml")}

        # -- theme_to_agents --
        for theme_key, entry in (raw.get("theme_to_agents") or {}).items():
            agents = self._extract_agents(str(theme_key), entry, known_slugs)
            self._theme_map[str(theme_key).upper()] = agents

        # -- framework_to_agents --
        for fw_key, entry in (raw.get("framework_to_agents") or {}).items():
            agents = self._extract_agents(str(fw_key), entry, known_slugs)
            self._framework_map[str(fw_key)] = agents

        self._loaded = True
        logger.debug(
            "theme_agent_map: loaded %d themes, %d frameworks from %s",
            len(self._theme_map),
            len(self._framework_map),
            self._config_path,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_agents(
        self,
        key: str,
        entry: Any,
        known_slugs: set[str] | None,
    ) -> list[str]:
        """Extract and validate agent list from a YAML entry dict."""
        if not isinstance(entry, dict):
            logger.warning("theme_agent_map: entry for '%s' is not a dict", key)
            return []

        raw_agents = entry.get("agents", [])
        if not isinstance(raw_agents, list):
            return []

        result: list[str] = []
        for slug in raw_agents:
            slug_lower = str(slug).strip().lower()
            if not slug_lower:
                continue
            if known_slugs is not None and slug_lower not in known_slugs:
                logger.warning(
                    "theme_agent_map: slug '%s' for key '%s' not found in cargo filesystem "
                    "(cascade will still attempt it)",
                    slug_lower,
                    key,
                )
            result.append(slug_lower)

        return result

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def loaded(self) -> bool:
        """True when config was successfully loaded."""
        return self._loaded

    def resolve_theme(self, theme: str) -> list[str]:
        """Return cargo agent slugs for a given theme string.

        Matching is case-insensitive.  If no match, returns empty list
        (caller falls back to DNA-CONFIG lookup only — AC5).

        Args:
            theme: Theme identifier as it appears in the insight, e.g.
                "02-PROCESSO-VENDAS" or "processo-vendas".

        Returns:
            List of lowercase cargo agent slugs.
        """
        if not theme or not self._theme_map:
            return []
        return list(self._theme_map.get(theme.upper().strip(), []))

    def resolve_framework(self, framework_tag: str) -> list[str]:
        """Return cargo agent slugs for a given framework tag.

        Matching is exact (case-sensitive, as framework names have mixed
        capitalisation with semantic meaning).  Falls back to case-insensitive
        if no exact match.

        Args:
            framework_tag: Framework name as stored in the insight, e.g.
                "7 Universal Closes".

        Returns:
            List of lowercase cargo agent slugs.
        """
        if not framework_tag or not self._framework_map:
            return []

        # Exact match first.
        direct = self._framework_map.get(framework_tag)
        if direct is not None:
            return list(direct)

        # Case-insensitive fallback.
        fw_lower = framework_tag.lower().strip()
        for key, slugs in self._framework_map.items():
            if key.lower() == fw_lower:
                return list(slugs)

        return []

    def resolve_for_insight(self, insight: dict) -> tuple[list[str], str]:
        """Resolve all cargo agents for an insight using both sub-tables.

        Combines theme lookup and framework_tag lookup, deduplicates.

        Args:
            insight: Insight dict with optional keys: "tag", "theme",
                "dna_layer", "framework_tag".

        Returns:
            Tuple of (deduplicated_slug_list, routing_log_string).
            The routing_log_string describes which table(s) contributed
            (AC6 — log of routing mechanism).
        """
        theme_agents: list[str] = []
        framework_agents: list[str] = []
        routing_notes: list[str] = []

        # Theme: try "tag", "theme", "dna_layer" fields (in order of preference)
        theme_raw = insight.get("tag") or insight.get("theme") or insight.get("dna_layer") or ""
        if theme_raw:
            theme_agents = self.resolve_theme(str(theme_raw))
            if theme_agents:
                routing_notes.append(
                    f"routed via theme_to_agents({theme_raw}): {', '.join(theme_agents)}"
                )

        # Framework tag (AC4)
        fw_raw = insight.get("framework_tag") or ""
        if fw_raw:
            framework_agents = self.resolve_framework(str(fw_raw))
            if framework_agents:
                routing_notes.append(
                    f"routed via framework_to_agents({fw_raw}): {', '.join(framework_agents)}"
                )

        # Union without duplicates, preserving order.
        seen: set[str] = set()
        merged: list[str] = []
        for slug in theme_agents + framework_agents:
            if slug not in seen:
                seen.add(slug)
                merged.append(slug)

        routing_log = "; ".join(routing_notes) if routing_notes else "no deterministic mapping"
        return merged, routing_log


# ---------------------------------------------------------------------------
# Module-level singleton (lazy, cached per config path)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _cached_map(config_path: str) -> ThemeAgentMap:
    """Cached loader keyed on config path string."""
    from engine.paths import AGENTS_CARGO  # imported lazily to avoid circular

    return ThemeAgentMap(
        config_path=Path(config_path),
        agents_cargo_root=AGENTS_CARGO,
    )


def load_theme_agent_map(config_path: Path | None = None) -> ThemeAgentMap:
    """Return the cached ThemeAgentMap singleton.

    Args:
        config_path: Override path.  None uses engine/config/theme-to-agents.yaml.

    Returns:
        ThemeAgentMap instance (loaded once, reused on subsequent calls).
    """
    path = str(config_path or _CONFIG_PATH)
    return _cached_map(path)
