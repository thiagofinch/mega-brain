"""
person_paths.py — Single Source of Truth for person-artifact destinations
==========================================================================

Story: STORY-MCE-BUCKET-AWARE-WRITES (Art. XIII — Knowledge Bucket Isolation).

This module is the ONLY place that maps ``(slug, bucket, artifact_type) -> Path``
for person-scoped MCE artifacts (DNA, dossiers, sources, solos, by-person
insights). Every writer imports from here; no writer constructs a
``knowledge/...`` person path inline.

It also exposes the single canonical bucket resolver ``resolve_bucket(slug)``
that collapses the three divergent resolvers previously living in
``orchestrate.py``, ``sources_compiler.py`` and ``cascading.py``.

Design decisions (from the story §4):
  - D1: business DNA uses convention B (``knowledge/business/dna/persons/{slug}``),
        matching external and what dossier_generator/sources_compiler already read.
        Convention A (``knowledge/business/people/{slug}``) is deprecated.
  - D2: one resolver, not three. ``resolve_bucket`` is the widest chain and is
        the delegate target for sources_compiler/cascading.
  - D3: the entity-discovery sidecar (``*.entity-discovery.json``) is the routing
        SOT and is consulted FIRST — closing the timing gap that let
        NARRATIVES-STATE record ``external`` for a business-routed person.

Constraints: leaf module — stdlib + engine.paths only. ``MetadataManager`` is
lazy-imported inside ``resolve_bucket`` to avoid a circular import with
orchestrate.py.

Version: 1.0.0
Date: 2026-06-09
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from engine.paths import ROOT

logger = logging.getLogger("mce.person_paths")

VALID_BUCKETS: frozenset[str] = frozenset({"external", "business", "personal"})

# Search order for the entity-discovery sidecar (matches log_generator's
# _find_sidecar_for_slug — kept in sync; duplicated to keep this a leaf module).
_SIDECAR_BUCKET_PROBE_ORDER: tuple[str, ...] = ("business", "personal", "external")


# ---------------------------------------------------------------------------
# PersonArtifactPaths — the single destination resolver
# ---------------------------------------------------------------------------


class PersonArtifactPaths:
    """Resolve every person-artifact destination for a ``(slug, bucket)`` pair.

    All paths are bucket-templated. The ``personal`` bucket is single-person:
    its DNA lives at ``knowledge/personal/dna`` with no ``{slug}`` subdir.

    Example::

        paths = PersonArtifactPaths("carlos-magno", "business")
        paths.dna             # knowledge/business/dna/persons/carlos-magno
        paths.sources_dir     # knowledge/business/sources/CARLOS-MAGNO
        paths.solo("vendas")  # knowledge/business/dossiers/persons-by-theme/carlos-magno--vendas.md
    """

    __slots__ = ("bucket", "root", "slug")

    def __init__(self, slug: str, bucket: str = "external", *, root: Path | None = None) -> None:
        if bucket not in VALID_BUCKETS:
            raise ValueError(f"invalid bucket {bucket!r} (expected one of {sorted(VALID_BUCKETS)})")
        self.slug = slug
        self.bucket = bucket
        self.root = root or ROOT

    @property
    def _kb(self) -> Path:
        """Bucket root: ``knowledge/{bucket}``."""
        return self.root / "knowledge" / self.bucket

    @property
    def dna(self) -> Path:
        """DNA layer directory.

        - external/business: ``knowledge/{bucket}/dna/persons/{slug}`` (convention B)
        - personal: ``knowledge/personal/dna`` (single-person, no subdir)
        """
        if self.bucket == "personal":
            return self.root / "knowledge" / "personal" / "dna"
        return self._kb / "dna" / "persons" / self.slug

    @property
    def dossier_person(self) -> Path:
        """Person dossier file: ``knowledge/{bucket}/dossiers/persons/dossier-{slug}.md``."""
        return self._kb / "dossiers" / "persons" / f"dossier-{self.slug}.md"

    @property
    def dossier_theme_dir(self) -> Path:
        """Cross-person theme dossiers dir: ``knowledge/{bucket}/dossiers/themes``."""
        return self._kb / "dossiers" / "themes"

    @property
    def solos_dir(self) -> Path:
        """Person-theme solo dossiers dir: ``knowledge/{bucket}/dossiers/persons-by-theme``."""
        return self._kb / "dossiers" / "persons-by-theme"

    def solo(self, category: str) -> Path:
        """Solo dossier file for ``{slug}--{category}.md``."""
        return self.solos_dir / f"{self.slug}--{category}.md"

    @property
    def sources_dir(self) -> Path:
        """Sources catalog dir: ``knowledge/{bucket}/sources/{SLUG_UPPER}``."""
        return self._kb / "sources" / self.slug.upper()

    @property
    def insights_by_person(self) -> Path:
        """By-person insights file: ``knowledge/{bucket}/insights/by-person/{slug}.md``."""
        return self._kb / "insights" / "by-person" / f"{self.slug}.md"

    @property
    def inbox(self) -> Path:
        """Ingest inbox dir: ``knowledge/{bucket}/inbox/{slug}``."""
        return self._kb / "inbox" / self.slug

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"PersonArtifactPaths(slug={self.slug!r}, bucket={self.bucket!r})"


# ---------------------------------------------------------------------------
# Bucket resolution — the single canonical chain (D2 + D3)
# ---------------------------------------------------------------------------


def _bucket_from_sidecar(slug: str, root: Path) -> str | None:
    """Derive the routed bucket from the entity-discovery sidecar (D3).

    The sidecar is the routing SOT. Two signals, in order:
      1. ``decision.bucket_hint`` — explicit business/personal override emitted
         by batch_auto_creator when internal-party / business evidence is found.
      2. ``destination`` absolute path — parse the ``knowledge/{bucket}/`` segment;
         this is the actual routed destination and exists on every sidecar.

    Returns a valid bucket string or ``None`` when no sidecar / no signal.
    """
    bases = [
        root / "knowledge" / b / sub / slug
        for b in _SIDECAR_BUCKET_PROBE_ORDER
        for sub in ("processed", "inbox")
    ]
    for base in bases:
        if not base.exists():
            continue
        for f in sorted(base.rglob("*.entity-discovery.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            # Signal 1: explicit bucket_hint inside the decision block.
            decision = data.get("decision")
            if isinstance(decision, dict):
                hint = decision.get("bucket_hint")
                if hint in VALID_BUCKETS:
                    return hint

            # Signal 2: the routed destination path.
            dest = data.get("destination")
            if isinstance(dest, str):
                parts = Path(dest).parts
                if "knowledge" in parts:
                    idx = parts.index("knowledge")
                    if idx + 1 < len(parts) and parts[idx + 1] in VALID_BUCKETS:
                        return parts[idx + 1]
    return None


def resolve_bucket(slug: str, *, root: Path | None = None) -> str:
    """Resolve the canonical knowledge bucket for *slug* (single SOT — D2).

    Priority chain (widest, sidecar-first — D3):
      1. entity-discovery sidecar (``decision.bucket_hint`` -> ``destination`` path)
      2. ``MetadataManager.bucket``
      3. ``MetadataManager.classification.primary_bucket``
      4. ``knowledge/{b}/inbox/{slug}``
      5. ``knowledge/{b}/processed/{slug}``
      6. ``agents/{b}/{slug}``
      7. ``knowledge/{b}/dna/persons/{slug}`` (convention B)  OR
         ``knowledge/business/people/{slug}`` (convention A legacy)
      8. default ``external`` (emits a journey-log fallback event)

    NARRATIVES-STATE is intentionally NOT consulted: it was the poisoned SOT
    (story §2). Inbox/processed/sidecar carry the current routing truth.
    """
    r = root or ROOT

    # 1. Sidecar (routing SOT) — closes the cmd_narrative timing gap.
    sidecar_bucket = _bucket_from_sidecar(slug, r)
    if sidecar_bucket:
        return sidecar_bucket

    # 2 + 3. MetadataManager (lazy import — avoids circular import w/ orchestrate).
    try:
        from engine.intelligence.pipeline.mce.metadata_manager import MetadataManager

        mgr = MetadataManager.load(slug)
    except Exception:  # pragma: no cover - defensive
        mgr = None
    if mgr is not None:
        bucket = getattr(mgr, "bucket", None)
        if bucket in VALID_BUCKETS:
            return bucket
        classification = getattr(mgr, "classification", None) or {}
        primary = classification.get("primary_bucket") if isinstance(classification, dict) else None
        if primary in VALID_BUCKETS:
            return primary

    # 4. inbox — most recent upstream classification.
    for b in ("personal", "business", "external"):
        if (r / "knowledge" / b / "inbox" / slug).is_dir():
            return b
    # 5. processed — post lifecycle move.
    for b in ("personal", "business", "external"):
        if (r / "knowledge" / b / "processed" / slug).is_dir():
            return b
    # 6. agents dir.
    for b in ("personal", "business", "external"):
        if (r / "agents" / b / slug).is_dir():
            return b
    # 7. DNA evidence — convention B (all buckets) + convention A (business legacy).
    for b in ("personal", "business", "external"):
        if (r / "knowledge" / b / "dna" / "persons" / slug).is_dir():
            return b
    if (r / "knowledge" / "business" / "people" / slug).is_dir():
        return "business"

    # 8. default external — record the fallback for observability (Art. IX).
    logger.warning(
        "resolve_bucket fallback to 'external' for slug=%s "
        "(no sidecar/metadata/inbox/processed/agents/dna evidence).",
        slug,
    )
    try:
        from engine.intelligence.pipeline.journey_logger import emit_bucket_decision

        emit_bucket_decision(
            entity_id=slug,
            entity_type="slug",
            from_state=None,
            to_state="external",
            triggered_by="person_paths.resolve_bucket.fallback",
            evidence={"reason": "no upstream signal — defaulted to external"},
        )
    except Exception:
        pass
    return "external"
