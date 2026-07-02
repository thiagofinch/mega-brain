"""
sources_compiler.py — MCE Phase 6.6: Sources Compilation
=========================================================

Bucket-aware compiler that aggregates source materials for a person slug and
emits structured Markdown files at the canonical path::

    knowledge/{bucket}/sources/{PERSON_UPPER}/{TEMA}.md

Three public functions (AC2):

* ``resolve_bucket_for_slug(slug, *, root=None) -> str``
  Resolves which knowledge bucket a slug belongs to.
  Priority: NARRATIVES-STATE.json → filesystem heuristics → default "external".

* ``format_source_md(slug, tema, sources, *, bucket) -> str``
  Renders frontmatter YAML + Markdown body for a single tema file.
  Returns a string ready for atomic write.

* ``compile_sources_for_slug(slug, *, root=None) -> dict``
  Orchestrates the full compilation: discovers sources, groups by tema,
  writes atomic MD files. Returns a status dict.

Constraints (Art. XIII, V2, V5):
- Cross-bucket write raises ValueError.
- stdlib + PyYAML only — zero LLM, zero imports from orchestrate.py.
- Atomic write: tempfile.mkstemp → os.replace.
- Idempotent: skips unchanged files, updates when source_paths changed.

Story: MCE-4.2
Constitution Articles: X (Artifact Contracts), XII (Pipeline MCE Integrity),
                       XIII (Knowledge Bucket Isolation)
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_VALID_BUCKETS: frozenset[str] = frozenset({"external", "business", "personal"})
_SCHEMA_VERSION = "1.0.0"

# Canonical NARRATIVES-STATE path relative to project root.
_NARRATIVES_STATE_REL = ".data/artifacts/narratives/NARRATIVES-STATE.json"

# Default project root — overridden by root= kwarg in all public functions.
_DEFAULT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _project_root(root: Path | None) -> Path:
    """Return the effective project root."""
    return root if root is not None else _DEFAULT_ROOT


def _now_iso() -> str:
    """Return current UTC timestamp in ISO8601 format."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug_to_display_variants(slug: str) -> list[str]:
    """Return candidate display-name variants that might match a slug.

    NARRATIVES-STATE.json keys are display names like "Alex Hormozi", not slugs.
    We generate plausible variants to look up a slug in the persons dict.

    Examples:
        "alex-hormozi" -> ["Alex Hormozi", "alex-hormozi", "ALEX-HORMOZI",
                           "Alex-Hormozi", "Alex hormozi"]
    """
    # Title-case with spaces: "Alex Hormozi"
    spaced = slug.replace("-", " ")
    return [
        spaced.title(),  # "Alex Hormozi"
        spaced,  # "alex hormozi"
        spaced.upper(),  # "ALEX HORMOZI"
        slug,  # "alex-hormozi"
        slug.upper(),  # "ALEX-HORMOZI"
        slug.title(),  # "Alex-Hormozi"
    ]


def _load_narratives_state(root: Path) -> dict[str, Any]:
    """Load NARRATIVES-STATE.json from root. Returns empty dict on any error."""
    path = root / _NARRATIVES_STATE_REL
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.debug("sources_compiler: failed to load NARRATIVES-STATE: %s", exc)
    return {}


def _bucket_from_narratives_state(slug: str, root: Path) -> str | None:
    """Probe NARRATIVES-STATE.json for the slug's bucket.

    The state file uses display names as keys ("Alex Hormozi") with
    an optional `slug` field that may be None. We try display-name
    variants and also fall back to matching by the `slug` field.

    Returns bucket string if found and valid, else None.
    """
    state = _load_narratives_state(root)
    persons = state.get("persons", {})
    if not isinstance(persons, dict):
        return None

    # Try direct display-name match via variants
    for variant in _slug_to_display_variants(slug):
        entry = persons.get(variant)
        if isinstance(entry, dict):
            bucket = entry.get("bucket")
            if bucket in _VALID_BUCKETS:
                return bucket

    # Try matching by the `slug` field stored inside each entry
    slug_normalized = slug.lower().strip()
    for _key, entry in persons.items():
        if not isinstance(entry, dict):
            continue
        entry_slug = entry.get("slug")
        if entry_slug and entry_slug.lower().strip() == slug_normalized:
            bucket = entry.get("bucket")
            if bucket in _VALID_BUCKETS:
                return bucket

    return None


def _atomic_write_md(content: str, target: Path) -> None:
    """Write content to target atomically using tmp + os.replace.

    Reuses the exact pattern from orchestrate.py:1128 (_save_insights_state).
    Raises on failure after cleaning up the temp file.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, target)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _discover_sources_for_slug(slug: str, root: Path) -> list[dict[str, Any]]:
    """Discover source files for a slug across the knowledge tree.

    Scans (non-recursively deep) known source locations:
    1. knowledge/{bucket}/dna/persons/{slug}/ — DNA YAML layers
    2. processing/batches/ — chunk .md files whose name contains slug

    Returns list of dicts: {path: str (relative to root), tipo: str, tema: str}.
    The tema is inferred from the file name / directory name.
    """
    sources: list[dict[str, Any]] = []
    slug_norm = slug.lower().replace("-", "").replace("_", "")

    # 1. DNA layers across all buckets
    for bucket in ("external", "business", "personal"):
        dna_dir = root / "knowledge" / bucket / "dna" / "persons" / slug
        if dna_dir.is_dir():
            for f in sorted(dna_dir.iterdir()):
                if f.suffix in (".yaml", ".yml", ".json", ".md"):
                    # tema = simplified layer name
                    stem = f.stem.lower()
                    # Remove leading layer prefix like "L1-", "L6-" etc.
                    tema = re.sub(r"^l\d+-", "", stem).replace("-", "_").replace("_", "-")
                    sources.append(
                        {
                            "path": str(f.relative_to(root)),
                            "tipo": "dna-layer",
                            "tema": tema,
                            "filename": f.name,
                        }
                    )

    # 2. Processing batch chunks that reference the slug
    batches_dir = root / "processing" / "batches"
    if batches_dir.is_dir():
        for batch_dir in sorted(batches_dir.iterdir()):
            if not batch_dir.is_dir():
                continue
            # Quick heuristic: batch name contains slug letters
            batch_norm = batch_dir.name.lower().replace("-", "").replace("_", "")
            # Use first 4 chars of slug as a prefix check (e.g. "alex" in "AHML001")
            slug_prefix = slug_norm[:4]
            if slug_prefix and slug_prefix not in batch_norm:
                continue
            chunks_dir = batch_dir / "chunks"
            if not chunks_dir.is_dir():
                continue
            for f in sorted(chunks_dir.iterdir()):
                if f.suffix == ".md":
                    sources.append(
                        {
                            "path": str(f.relative_to(root)),
                            "tipo": "chunk",
                            "tema": "content",
                            "filename": f.name,
                        }
                    )

    return sources


def _group_by_tema(
    sources: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group source dicts by their 'tema' field."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for s in sources:
        tema = s.get("tema", "general")
        groups.setdefault(tema, []).append(s)
    return groups


def _read_existing_frontmatter(path: Path) -> dict[str, Any] | None:
    """Read existing frontmatter from a .md file. Returns None on any error."""
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return None
        end = content.find("\n---", 3)
        if end < 0:
            return None
        fm_text = content[3:end].strip()
        data = yaml.safe_load(fm_text)
        if isinstance(data, dict):
            return data
    except (OSError, yaml.YAMLError) as exc:
        logger.debug("sources_compiler: failed to read frontmatter from %s: %s", path, exc)
    return None


# ---------------------------------------------------------------------------
# Public API — exactly 3 functions (AC2)
# ---------------------------------------------------------------------------


def resolve_bucket_for_slug(slug: str, *, root: Path | None = None) -> str:
    """Resolve the knowledge bucket for a slug.

    STORY-MCE-BUCKET-AWARE-WRITES (D2): this is now a thin delegate to the single
    canonical resolver ``person_paths.resolve_bucket``. The previous narrow chain
    (NARRATIVES-STATE first -> agents -> dna -> external) is removed — it trusted
    the poisoned NARRATIVES-STATE SOT and missed the entity-discovery sidecar,
    which produced the Art. XIII cross-bucket leak (sources landing in external
    for a business-routed person).

    Args:
        slug: Lowercase hyphenated person slug, e.g. ``"alex-hormozi"``.
        root: Override project root (used in tests with tempdir).

    Returns:
        Bucket string: ``"external"``, ``"business"``, or ``"personal"``.
    """
    from engine.intelligence.pipeline.mce.person_paths import resolve_bucket

    return resolve_bucket(slug, root=_project_root(root))


def format_source_md(
    slug: str,
    tema: str,
    sources: list[dict[str, Any]],
    *,
    bucket: str,
) -> str:
    """Format a sources .md file with YAML frontmatter + Markdown body.

    Args:
        slug: Person slug, e.g. ``"alex-hormozi"``.
        tema: Theme identifier, e.g. ``"vendas"``.
        sources: List of source dicts with keys: path, tipo, filename.
        bucket: Knowledge bucket (``"external"``, ``"business"``, ``"personal"``).

    Returns:
        Complete file content as a string, ready for atomic write.
    """
    person_upper = slug.upper()
    compiled_at = _now_iso()
    source_paths = [s["path"] for s in sources]

    # --- Frontmatter ---
    frontmatter_data = {
        "schema_version": _SCHEMA_VERSION,
        "slug": slug,
        "person_upper": person_upper,
        "bucket": bucket,
        "tema": tema,
        "sources_count": len(sources),
        "compiled_at": compiled_at,
        "source_paths": source_paths,
    }
    frontmatter_yaml = yaml.dump(
        frontmatter_data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=True,
    )

    # --- Body ---
    lines: list[str] = [
        "---",
        frontmatter_yaml.rstrip(),
        "---",
        "",
        f"# Sources: {person_upper} / {tema}",
        "",
        f"**Pessoa:** {person_upper}",
        f"**Bucket:** {bucket}",
        f"**Tema:** {tema}",
        f"**Compilado em:** {compiled_at}",
        f"**Total de fontes:** {len(sources)}",
        "",
        "## Fontes",
        "",
    ]

    for idx, src in enumerate(sources, 1):
        filename = src.get("filename", Path(src["path"]).name)
        tipo = src.get("tipo", "unknown")
        path = src["path"]
        lines += [
            f"### {idx}. {filename}",
            "",
            f"- **Tipo:** {tipo}",
            f"- **Path:** {path}",
            f"- **Relevancia:** {tema}",
            "",
        ]

    return "\n".join(lines)


def compile_sources_for_slug(
    slug: str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Compile sources catalog for a person slug.

    Discovers source files, groups by tema, writes atomic .md files at:
    ``knowledge/{bucket}/sources/{PERSON_UPPER}/{TEMA}.md``

    Cross-bucket write is blocked: if the inferred bucket does not match
    the attempted write path, raises ValueError (Art. XIII).

    Idempotent: if source_paths are identical to an existing file, emits
    status ``"skipped"`` for that tema. If paths changed, rewrites with
    status ``"updated"``.

    Args:
        slug: Person slug, e.g. ``"alex-hormozi"``.
        root: Override project root (used in tests with tempdir).

    Returns:
        dict with keys: status, files_written, bucket, person_upper, temas.
        status is ``"written"`` if any file was written, ``"skipped"`` if
        all were unchanged, or ``"no_sources"`` if nothing was discovered.
    """
    r = _project_root(root)

    bucket = resolve_bucket_for_slug(slug, root=r)
    person_upper = slug.upper()

    # Discover all sources
    all_sources = _discover_sources_for_slug(slug, r)

    if not all_sources:
        logger.info("compile_sources_for_slug: no sources found for %s", slug)
        return {
            "status": "no_sources",
            "files_written": 0,
            "bucket": bucket,
            "person_upper": person_upper,
            "temas": [],
        }

    grouped = _group_by_tema(all_sources)

    files_written = 0
    temas_written: list[str] = []
    temas_skipped: list[str] = []

    for tema, sources in sorted(grouped.items()):
        target_dir = r / "knowledge" / bucket / "sources" / person_upper
        target = target_dir / f"{tema}.md"

        # --- Cross-bucket guard (AC1, AC6, V2, Art. XIII) ---
        # The canonical bucket must match the path we're about to write to.
        # Verify there is no pre-existing file at a different bucket path.
        for other_bucket in _VALID_BUCKETS - {bucket}:
            wrong_path = r / "knowledge" / other_bucket / "sources" / person_upper / f"{tema}.md"
            if wrong_path.exists():
                raise ValueError(
                    f"cross-bucket write blocked: slug={slug} belongs to "
                    f"bucket={bucket}, attempted path exists in bucket={other_bucket} "
                    f"at {wrong_path}"
                )

        # --- Idempotency check ---
        existing_fm = _read_existing_frontmatter(target)
        current_paths = sorted(s["path"] for s in sources)
        if existing_fm is not None:
            existing_paths = sorted(existing_fm.get("source_paths", []))
            if existing_paths == current_paths:
                logger.debug(
                    "compile_sources_for_slug: %s/%s unchanged — skipping",
                    slug,
                    tema,
                )
                temas_skipped.append(tema)
                continue

        # --- Render and write atomically (AC5) ---
        content = format_source_md(slug, tema, sources, bucket=bucket)
        _atomic_write_md(content, target)
        files_written += 1
        temas_written.append(tema)
        logger.info(
            "compile_sources_for_slug: wrote %s (%d sources)",
            target.relative_to(r),
            len(sources),
        )

    overall_status: str
    if files_written > 0:
        overall_status = "written"
    elif temas_skipped:
        overall_status = "skipped"
    else:
        overall_status = "no_sources"

    return {
        "status": overall_status,
        "files_written": files_written,
        "bucket": bucket,
        "person_upper": person_upper,
        "temas": temas_written + temas_skipped,
        "temas_written": temas_written,
        "temas_skipped": temas_skipped,
    }
