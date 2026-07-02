"""
theme_router.py -- Semantic theme dossier routing for MCE cascade
=================================================================
Resolves an insight dict to the canonical dossier path for its theme.

Resolution priority (Story MCE-11.5 AC2):
    1. Exact slug match against theme-routing.yaml keys
    2. Alias match (case-insensitive)
    3. Match via ``category`` field of insight (normalised to kebab-case)
    4. Fallback: "general"

Auto-discovery (AC3):
    If no entry in theme-routing.yaml matches, ThemeRouter derives a
    kebab-case slug from the insight's category/dna_layer value and
    returns a path under DOSSIERS_DIR.  If that path does not exist the
    caller is responsible for creating it (``ensure_dossier_exists``).

Constraints:
    - Python 3, stdlib + PyYAML only.
    - Thread-safe after construction (read-only after ``__init__``).
    - theme-routing.yaml is loaded once per ThemeRouter instance.

Version: 1.0.0
Date: 2026-05-27
Story: MCE-11.5
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

# Canonical config path relative to project root
_DEFAULT_CONFIG = Path(__file__).parents[4] / "engine" / "config" / "theme-routing.yaml"


def _slugify(value: str) -> str:
    """Normalise a string to lowercase kebab-case.

    Examples:
        "MODELO-MENTAL"  -> "modelo-mental"
        "ai operating systems" -> "ai-operating-systems"
        "HEURISTICA_OPERACIONAL" -> "heuristica-operacional"
    """
    v = value.lower().strip()
    v = re.sub(r"[\s_]+", "-", v)
    v = re.sub(r"[^a-z0-9-]", "", v)
    v = re.sub(r"-{2,}", "-", v)
    v = v.strip("-")
    return v or "general"


class ThemeRouter:
    """Maps insight dicts to canonical dossier paths.

    Args:
        config_path: Path to theme-routing.yaml.  Defaults to
            ``engine/config/theme-routing.yaml`` relative to project root.
        dossiers_dir: Base directory for dossier files.  Defaults to
            ``knowledge/external/dossiers/themes/`` relative to project root.
    """

    def __init__(
        self,
        config_path: Path | None = None,
        dossiers_dir: Path | None = None,
    ) -> None:
        self._config_path = config_path or _DEFAULT_CONFIG
        project_root = self._config_path.parents[2]  # engine/ -> root
        self._dossiers_dir = dossiers_dir or (
            project_root / "knowledge" / "external" / "dossiers" / "themes"
        )

        raw = yaml.safe_load(self._config_path.read_text(encoding="utf-8"))
        routes: dict[str, dict] = (raw or {}).get("routes", {})

        # Build forward index: slug -> absolute Path
        self._slug_to_path: dict[str, Path] = {}
        # Build reverse alias index: alias_lower -> canonical slug
        self._alias_to_slug: dict[str, str] = {}

        for slug, entry in routes.items():
            rel = entry.get("dossier_path", "")
            if not rel:
                continue
            abs_path = project_root / rel
            self._slug_to_path[slug] = abs_path
            # slug itself is also an alias
            self._alias_to_slug[slug.lower()] = slug
            for alias in entry.get("aliases", []):
                self._alias_to_slug[alias.lower()] = slug

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self, insight: dict[str, Any]) -> Path:
        """Return the dossier Path for *insight*.

        Tries (in order):
            1. insight["category"]  -> slug / alias lookup
            2. insight["theme"]     -> slug / alias lookup
            3. insight["dna_layer"] -> slug / alias lookup
            4. insight["tag"]       -> slug / alias lookup (brackets stripped)
            5. Auto-discovery: derive slug from best available field
            6. General fallback

        Returns an absolute Path (may not exist yet for new dossiers).
        """
        # Strip surrounding brackets from tag so "[METODOLOGIA]" matches
        # the alias "METODOLOGIA" already declared in theme-routing.yaml.
        tag_raw = insight.get("tag") or ""
        tag_stripped = tag_raw.strip("[]") if tag_raw else ""

        candidates = [
            insight.get("category") or "",
            insight.get("theme") or "",
            insight.get("dna_layer") or "",
            tag_stripped,
        ]

        for raw in candidates:
            if not raw:
                continue
            path = self._lookup(raw)
            if path is not None:
                return path

        # Auto-discovery: use first non-empty candidate
        raw_best = next((c for c in candidates if c), "general")
        return self._auto_discover(raw_best)

    def resolve_path_str(self, insight: dict[str, Any]) -> str:
        """Same as ``resolve`` but returns a string (for backwards compat)."""
        return str(self.resolve(insight))

    def ensure_dossier_exists(self, path: Path, slug: str, now: str) -> bool:
        """Create a minimal dossier file at *path* if it does not exist.

        Args:
            path: Target file path.
            slug: Human-readable slug for the dossier header.
            now: ISO date string for the metadata header.

        Returns:
            True if created, False if it already existed.
        """
        if path.exists():
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            f"# DOSSIER: {slug}\n\n"
            f"> **Versao:** 1.0.0\n"
            f"> **Criado:** {now}\n"
            f"> **Auto-gerado por:** theme_router.py (auto-discovery)\n\n"
            f"---\n\n"
            f"## VISAO GERAL\n\n"
            f"Theme dossier criado automaticamente pelo pipeline MCE.\n"
            f"Adicione contexto manual aqui conforme o tema acumular insights.\n\n"
            f"---\n\n"
        )
        path.write_text(content, encoding="utf-8")
        return True

    def known_slugs(self) -> list[str]:
        """Return all canonical slugs in the routing table (sorted)."""
        return sorted(self._slug_to_path.keys())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _lookup(self, raw: str) -> Path | None:
        """Attempt to resolve *raw* via exact slug or alias.

        Returns None on no match.
        """
        # 1. Exact key match (case-insensitive)
        slug = self._alias_to_slug.get(raw.lower())
        if slug:
            return self._slug_to_path.get(slug)

        # 2. Normalised kebab-case match
        normalised = _slugify(raw)
        slug = self._alias_to_slug.get(normalised)
        if slug:
            return self._slug_to_path.get(slug)

        return None

    def _auto_discover(self, raw: str) -> Path:
        """Derive a dossier path for an unknown theme.

        Does NOT create the file — caller must call ``ensure_dossier_exists``.
        Does NOT modify theme-routing.yaml — that is a human operation.
        """
        slug = _slugify(raw)
        if not slug or slug == "general":
            return self._slug_to_path.get("general", self._dossiers_dir / "dossier-general.md")
        return self._dossiers_dir / f"dossier-{slug}.md"
