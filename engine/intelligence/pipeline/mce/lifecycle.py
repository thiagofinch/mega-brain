"""Inbox → processed/ lifecycle (Story MCE-7.0 AC-2).

After successful cmd_finalize for a slug, move all source files from
knowledge/{bucket}/inbox/{slug}/ to knowledge/{bucket}/processed/{slug}/.
Preserves subdirectory structure. Sidecars (.entity-discovery.json) move
with their parent.

Design decisions:
- Fail-open per Art. XII — never blocks pipeline. Any per-file error is
  logged and counted in failed_count, pipeline continues.
- Atomic per-file: shutil.move is used (rename if same fs, copy+unlink otherwise).
- Idempotent: if the destination file already exists, it is NOT overwritten
  (counted as skipped). This handles partial previous moves cleanly.
- cmd_batch and _resolve_chunks_for_slug in orchestrate.py already scan
  BOTH inbox/{slug}/ AND processed/{slug}/ so the move is transparent to
  the extraction pipeline.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger("pipeline.lifecycle")

# ── repo root resolution (no hardcoded paths) ──────────────────────────────
try:
    from engine.paths import KNOWLEDGE_BUSINESS, KNOWLEDGE_EXTERNAL
except ImportError:
    _repo = Path(__file__).resolve().parents[4]
    KNOWLEDGE_EXTERNAL = _repo / "knowledge" / "external"
    KNOWLEDGE_BUSINESS = _repo / "knowledge" / "business"

_BUCKET_ROOTS: dict[str, Path] = {
    "external": KNOWLEDGE_EXTERNAL,
    "business": KNOWLEDGE_BUSINESS,
    "personal": Path(__file__).resolve().parents[4] / "knowledge" / "personal",
}


def _bucket_root(bucket: str) -> Path:
    root = _BUCKET_ROOTS.get(bucket)
    if root is None:
        # Unknown bucket — derive portably
        root = Path(__file__).resolve().parents[4] / "knowledge" / bucket
    return root


def move_slug_to_processed(slug: str, bucket: str) -> dict:
    """Move all source files for slug from inbox/{slug}/ to processed/{slug}/.

    Returns dict with keys: moved_count, failed_count, skipped_count.
    Fail-open per Art. XII — never blocks pipeline.

    Args:
        slug:   Person/source slug (e.g. "alex-hormozi").
        bucket: Knowledge bucket ("external", "business", or "personal").
    """
    moved_count = 0
    failed_count = 0
    skipped_count = 0

    root = _bucket_root(bucket)
    inbox_dir = root / "inbox" / slug
    processed_dir = root / "processed" / slug

    if not inbox_dir.exists():
        logger.debug("[lifecycle] inbox dir not found for %s/%s — nothing to move", bucket, slug)
        return {
            "moved_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "inbox_dir": str(inbox_dir),
            "processed_dir": str(processed_dir),
            "note": "inbox_dir_not_found",
        }

    # Collect all files recursively (preserves subdirectory structure)
    all_files = [f for f in inbox_dir.rglob("*") if f.is_file()]

    if not all_files:
        logger.debug("[lifecycle] inbox dir empty for %s/%s", bucket, slug)
        return {
            "moved_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "inbox_dir": str(inbox_dir),
            "processed_dir": str(processed_dir),
            "note": "inbox_empty",
        }

    for src in all_files:
        # Compute destination preserving subdirectory structure relative to inbox_dir
        try:
            rel = src.relative_to(inbox_dir)
        except ValueError:
            failed_count += 1
            logger.warning("[lifecycle] Cannot relativize %s from %s", src, inbox_dir)
            continue

        dst = processed_dir / rel

        # Idempotent: skip if destination already exists
        if dst.exists():
            skipped_count += 1
            logger.debug("[lifecycle] SKIP (already at destination): %s", rel)
            continue

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved_count += 1
            logger.debug("[lifecycle] MOVED: %s -> processed/%s/%s", rel, slug, rel)
        except Exception as exc:
            failed_count += 1
            logger.warning("[lifecycle] FAILED to move %s: %s", src, exc)

    logger.info(
        "[lifecycle] %s/%s: moved=%d  skipped=%d  failed=%d",
        bucket,
        slug,
        moved_count,
        skipped_count,
        failed_count,
    )

    return {
        "moved_count": moved_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "inbox_dir": str(inbox_dir),
        "processed_dir": str(processed_dir),
    }
