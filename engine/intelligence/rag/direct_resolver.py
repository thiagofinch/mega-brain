#!/usr/bin/env python3
"""
DIRECT RESOLVER - Pipeline F (Pre-RAG Bypass)
================================================
Deterministic file resolver that bypasses RAG for queries targeting
known entities and artifact types.

When a query matches a known entity + artifact pattern, the resolver
reads the target files directly instead of going through vector/BM25
search. Unresolvable queries return None and fall through to RAG.

Performance target: <100ms for resolved queries.

Versao: 1.0.0
Data: 2026-03-25
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PATHS (relative to project root, resolved at load time)
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_CANONICAL_MAP_PATHS = [
    _ROOT / "artifacts" / "canonical" / "CANONICAL-MAP.json",
]

# Where knowledge artifacts live, keyed by artifact type
_KNOWLEDGE_PATHS = {
    "dna": _ROOT / "knowledge" / "external" / "dna" / "persons",
    "dossier": _ROOT / "knowledge" / "external" / "dossiers" / "persons",
    "dossier_theme": _ROOT / "knowledge" / "external" / "dossiers" / "themes",
    "playbook": _ROOT / "knowledge" / "external" / "playbooks",
    "agent": _ROOT / "agents" / "external",
    "source": _ROOT / "knowledge" / "external" / "sources",
}

# DNA layer name mapping (L1-L5 -> filename stems)
DNA_LAYERS = {
    "l1": "FILOSOFIAS",
    "l2": "MODELOS-MENTAIS",
    "l3": "HEURISTICAS",
    "l4": "FRAMEWORKS",
    "l5": "METODOLOGIAS",
    "filosofias": "FILOSOFIAS",
    "modelos-mentais": "MODELOS-MENTAIS",
    "modelos mentais": "MODELOS-MENTAIS",
    "heuristicas": "HEURISTICAS",
    "frameworks": "FRAMEWORKS",
    "metodologias": "METODOLOGIAS",
    "voice": "VOICE-DNA",
    "voice-dna": "VOICE-DNA",
}

# Artifact type keywords found in queries
_ARTIFACT_KEYWORDS = {
    "dna": ["dna", "cognitivo", "cognitive", "knowledge layer"],
    "dossier": ["dossier", "dossiê", "dossie", "profile", "perfil"],
    "playbook": ["playbook", "playbooks", "manual", "guia"],
    "agent": ["agent", "agente", "soul", "activation", "memory"],
    "source": ["source", "fonte", "transcript", "transcription"],
}

# Agent sub-file keywords (ordered: specific first, generic last)
_AGENT_FILES = {
    "soul": "SOUL.md",
    "memory": "MEMORY.md",
    "activation": "ACTIVATION.yaml",
    "dna-config": "DNA-CONFIG.yaml",
    "config": "DNA-CONFIG.yaml",
}


# ---------------------------------------------------------------------------
# ENTITY INDEX (built from CANONICAL-MAP)
# ---------------------------------------------------------------------------
class EntityIndex:
    """Maps entity names/aliases to their canonical slug and known files."""

    def __init__(self) -> None:
        self._alias_to_canonical: dict[str, str] = {}
        self._canonical_to_slug: dict[str, str] = {}
        self._slug_to_files: dict[str, dict[str, list[Path]]] = {}
        self._loaded = False

    @property
    def loaded(self) -> bool:
        return self._loaded

    def load(self, canonical_map_paths: list[Path] | None = None) -> None:
        """Load entity mappings from CANONICAL-MAP JSON files."""
        paths = canonical_map_paths or _CANONICAL_MAP_PATHS
        t0 = time.time()

        for path in paths:
            if not path.exists():
                logger.debug("CANONICAL-MAP not found: %s", path)
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._ingest_canonical_map(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to load CANONICAL-MAP %s: %s", path, e)

        # Scan filesystem for actual files per slug
        self._scan_knowledge_files()

        self._loaded = True
        elapsed = (time.time() - t0) * 1000
        logger.debug(
            "EntityIndex loaded: %d aliases, %d slugs, %.1fms",
            len(self._alias_to_canonical),
            len(self._canonical_to_slug),
            elapsed,
        )

    def _ingest_canonical_map(self, data: dict) -> None:
        """Extract entity aliases and slugs from CANONICAL-MAP JSON."""
        entities = data.get("entities", {})
        for canonical_name, info in entities.items():
            if not isinstance(info, dict):
                continue
            slug = info.get("source", "")
            if not slug:
                # Derive slug from canonical name
                slug = canonical_name.lower().replace(" ", "-")

            self._canonical_to_slug[canonical_name.lower()] = slug
            self._alias_to_canonical[canonical_name.lower()] = canonical_name.lower()

            for variant in info.get("variants", []):
                if isinstance(variant, str) and len(variant) > 1:
                    self._alias_to_canonical[variant.lower()] = canonical_name.lower()

    def _scan_knowledge_files(self) -> None:
        """Scan filesystem to discover actual files per entity slug."""
        for slug in set(self._canonical_to_slug.values()):
            files: dict[str, list[Path]] = {}

            # DNA files
            dna_dir = _KNOWLEDGE_PATHS["dna"] / slug
            if dna_dir.is_dir():
                yaml_files = sorted(dna_dir.glob("*.yaml"))
                if yaml_files:
                    files["dna"] = yaml_files

            # Dossier files (person-level)
            dossier_dir = _KNOWLEDGE_PATHS["dossier"]
            if dossier_dir.is_dir():
                # Match DOSSIER-{SLUG}.md pattern
                slug_upper = slug.upper()
                for f in dossier_dir.iterdir():
                    if f.is_file() and slug_upper in f.stem.upper():
                        files.setdefault("dossier", []).append(f)

            # Agent files
            agent_dir = _KNOWLEDGE_PATHS["agent"] / slug
            if agent_dir.is_dir():
                agent_files = sorted(
                    f for f in agent_dir.iterdir() if f.is_file() and not f.name.startswith(".")
                )
                if agent_files:
                    files["agent"] = agent_files

            # Source files
            source_dir = _KNOWLEDGE_PATHS["source"] / slug
            if source_dir.is_dir():
                source_files = sorted(
                    f for f in source_dir.iterdir() if f.is_file() and not f.name.startswith(".")
                )
                if source_files:
                    files["source"] = source_files

            if files:
                self._slug_to_files[slug] = files

    def resolve_entity(self, name: str) -> str | None:
        """Resolve a name/alias to a canonical entity slug.

        Returns: slug string or None if not found.
        """
        canonical = self._alias_to_canonical.get(name.lower())
        if canonical is None:
            return None
        return self._canonical_to_slug.get(canonical)

    def get_files(self, slug: str, artifact_type: str | None = None) -> list[Path]:
        """Get known files for an entity slug, optionally filtered by type."""
        slug_files = self._slug_to_files.get(slug, {})
        if artifact_type:
            return list(slug_files.get(artifact_type, []))
        # Return all files across all types
        all_files: list[Path] = []
        for file_list in slug_files.values():
            all_files.extend(file_list)
        return all_files

    def get_all_slugs(self) -> list[str]:
        """Return all known entity slugs."""
        return list(self._slug_to_files.keys())

    def stats(self) -> dict[str, int]:
        """Return index statistics."""
        total_files = sum(len(f) for files in self._slug_to_files.values() for f in files.values())
        return {
            "aliases": len(self._alias_to_canonical),
            "slugs": len(self._canonical_to_slug),
            "slugs_with_files": len(self._slug_to_files),
            "total_files": total_files,
        }


# ---------------------------------------------------------------------------
# QUERY PARSER
# ---------------------------------------------------------------------------
class ParsedQuery:
    """Structured representation of a parsed direct-resolve query."""

    def __init__(
        self,
        entity: str | None = None,
        slug: str | None = None,
        artifact_type: str | None = None,
        dna_layer: str | None = None,
        agent_file: str | None = None,
    ):
        self.entity = entity
        self.slug = slug
        self.artifact_type = artifact_type
        self.dna_layer = dna_layer
        self.agent_file = agent_file

    @property
    def resolvable(self) -> bool:
        return self.slug is not None

    def __repr__(self) -> str:
        return (
            f"ParsedQuery(entity={self.entity!r}, slug={self.slug!r}, "
            f"type={self.artifact_type!r}, layer={self.dna_layer!r})"
        )


def parse_query(query: str, index: EntityIndex) -> ParsedQuery:
    """Parse a query to extract entity, artifact type, and DNA layer.

    Uses a simple heuristic approach:
    1. Tokenize the query
    2. Try to match entity names/aliases
    3. Look for artifact type keywords
    4. Look for DNA layer references
    """
    query_lower = query.lower().strip()
    parsed = ParsedQuery()

    # Step 1: Detect entity. Try longest match first (multi-word names).
    tokens = query_lower.split()
    best_slug = None
    best_entity = None
    best_len = 0

    # Try all n-grams from length=3 down to 1
    for n in range(min(4, len(tokens)), 0, -1):
        for i in range(len(tokens) - n + 1):
            candidate = " ".join(tokens[i : i + n])
            slug = index.resolve_entity(candidate)
            if slug and n > best_len:
                best_slug = slug
                best_entity = candidate
                best_len = n

    if best_slug:
        parsed.entity = best_entity
        parsed.slug = best_slug

    # Step 2: Detect artifact type
    for atype, keywords in _ARTIFACT_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                parsed.artifact_type = atype
                break
        if parsed.artifact_type:
            break

    # Step 3: Detect DNA layer
    # Check L1-L5 pattern
    layer_match = re.search(r"\bl([1-5])\b", query_lower)
    if layer_match:
        parsed.dna_layer = f"l{layer_match.group(1)}"
        if not parsed.artifact_type:
            parsed.artifact_type = "dna"

    # Check layer names
    for layer_key in DNA_LAYERS:
        if layer_key in query_lower:
            parsed.dna_layer = layer_key
            if not parsed.artifact_type:
                parsed.artifact_type = "dna"
            break

    # Step 4: Detect agent sub-file
    for file_key in _AGENT_FILES:
        if file_key in query_lower:
            parsed.agent_file = file_key
            if not parsed.artifact_type:
                parsed.artifact_type = "agent"
            break

    return parsed


# ---------------------------------------------------------------------------
# RESOLVER
# ---------------------------------------------------------------------------
class DirectResolver:
    """Resolves queries to specific files without RAG.

    Usage:
        resolver = DirectResolver()
        resolver.load()
        result = resolver.resolve("Hormozi DNA L4 frameworks")
        if result:
            # Direct resolution succeeded
            print(result["files"], result["resolution_path"])
        else:
            # Fall through to RAG
            pass
    """

    def __init__(self) -> None:
        self._index = EntityIndex()

    @property
    def loaded(self) -> bool:
        return self._index.loaded

    def load(self, canonical_map_paths: list[Path] | None = None) -> None:
        """Load the entity index from CANONICAL-MAP files."""
        self._index.load(canonical_map_paths)

    def resolve(self, query: str) -> dict[str, Any] | None:
        """Attempt to resolve a query to specific files.

        Returns:
            dict with keys:
                - query: original query
                - entity: matched entity name
                - slug: entity slug
                - artifact_type: resolved artifact type
                - dna_layer: specific DNA layer (if applicable)
                - files: list of Path objects
                - content: concatenated file content
                - resolution_path: "direct"
                - latency_ms: float
            None if the query cannot be resolved directly.
        """
        if not self._index.loaded:
            self.load()

        t0 = time.time()
        parsed = parse_query(query, self._index)

        if not parsed.resolvable:
            logger.debug("Direct resolver: no entity match for query: %s", query)
            return None

        # Get files for the entity
        files = self._index.get_files(parsed.slug, parsed.artifact_type)

        if not files:
            logger.debug(
                "Direct resolver: entity '%s' matched slug '%s' but no files found for type '%s'",
                parsed.entity,
                parsed.slug,
                parsed.artifact_type,
            )
            return None

        # If DNA layer specified, filter to that specific file
        if parsed.dna_layer and parsed.artifact_type == "dna":
            layer_stem = DNA_LAYERS.get(parsed.dna_layer)
            if layer_stem:
                files = [f for f in files if f.stem == layer_stem]

        # If agent sub-file specified, filter to that file
        if parsed.agent_file and parsed.artifact_type == "agent":
            target_name = _AGENT_FILES.get(parsed.agent_file, "")
            if target_name:
                files = [f for f in files if f.name == target_name]

        if not files:
            logger.debug(
                "Direct resolver: files filtered to empty for query: %s (layer=%s)",
                query,
                parsed.dna_layer,
            )
            return None

        # Read file content (cap at reasonable size)
        content_parts: list[str] = []
        max_chars = 32000  # ~8K tokens
        total_chars = 0

        for f in files:
            if not f.exists():
                continue
            try:
                text = f.read_text(encoding="utf-8")
                if total_chars + len(text) > max_chars:
                    remaining = max_chars - total_chars
                    if remaining > 200:
                        text = text[:remaining]
                    else:
                        break
                content_parts.append(f"[FILE:{f.name}]\n{text}")
                total_chars += len(text)
            except (OSError, UnicodeDecodeError) as e:
                logger.warning("Failed to read %s: %s", f, e)

        if not content_parts:
            return None

        latency = (time.time() - t0) * 1000

        return {
            "query": query,
            "entity": parsed.entity,
            "slug": parsed.slug,
            "artifact_type": parsed.artifact_type,
            "dna_layer": parsed.dna_layer,
            "files": files,
            "file_paths": [str(f) for f in files],
            "content": "\n\n".join(content_parts),
            "resolution_path": "direct",
            "latency_ms": round(latency, 1),
        }

    def stats(self) -> dict[str, Any]:
        """Return resolver statistics."""
        return self._index.stats()


# ---------------------------------------------------------------------------
# SINGLETON
# ---------------------------------------------------------------------------
_resolver: DirectResolver | None = None


def get_resolver() -> DirectResolver:
    """Get or create the singleton DirectResolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = DirectResolver()
        _resolver.load()
    return _resolver


def direct_resolve(query: str) -> dict[str, Any] | None:
    """Convenience function: resolve a query using the singleton resolver."""
    return get_resolver().resolve(query)
