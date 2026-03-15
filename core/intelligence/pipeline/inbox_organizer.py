#!/usr/bin/env python3
"""
INBOX ORGANIZER — Auto-organize files dropped into bucket inboxes
=================================================================
Detects files in any bucket inbox (external, business, personal) and
organizes them by entity (person/company) and content type into
subdirectories: {inbox}/{entity-slug}/{type}/

Entity detection uses the known persons from knowledge/external/dna/persons/
plus configurable aliases. Content type is classified from filename keywords.

Version: 1.0.0
Date: 2026-03-09
Story: S07 — EPIC-REORG-001
"""

import json
import logging
import os
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from core.paths import (
    KNOWLEDGE_EXTERNAL,
    LOGS,
    ROUTING,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Bucket inbox paths — resolved from core.paths ROUTING table
BUCKET_INBOXES: dict[str, Path] = {
    "external": ROUTING["external_inbox"],
    "business": ROUTING["business_inbox"],
    "personal": ROUTING["personal_inbox"],
}

# Where known person directories live (source of truth for entity detection)
DNA_PERSONS_DIR = KNOWLEDGE_EXTERNAL / "dna" / "persons"

# Files we can organize (everything else is skipped silently)
SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".docx",
    ".pdf",
    ".doc",
    ".xlsx",
    ".xls",
    ".mp3",
    ".mp4",
    ".wav",
    ".m4a",
    ".webm",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
}

# Skip dotfiles and OS metadata
SKIP_NAMES = {".DS_Store", "Thumbs.db", ".gitkeep"}


# ---------------------------------------------------------------------------
# ENTITY DETECTION
# ---------------------------------------------------------------------------

# Static aliases that map alternative names/spellings to the canonical slug.
# The canonical slug MUST match a directory name in DNA_PERSONS_DIR or be
# a known company/entity.
ENTITY_ALIASES: dict[str, str] = {
    # ── Examples (replace with your own in MEGA_BRAIN_ENTITY_ALIASES env var) ──
    # Format: "alternate name": "canonical-slug"
    # "example person": "example-person",
    # "example company": "example-company",
}

# User-specific aliases loaded from env (MEGA_BRAIN_ENTITY_ALIASES=name:slug,name:slug)
_custom_aliases = os.environ.get("MEGA_BRAIN_ENTITY_ALIASES", "")
for _pair in _custom_aliases.split(","):
    _pair = _pair.strip()
    if ":" in _pair:
        _name, _slug = _pair.split(":", 1)
        ENTITY_ALIASES[_name.strip().lower()] = _slug.strip()


def _load_known_entities() -> set[str]:
    """Load canonical entity slugs from multiple sources.

    Scans:
        1. DNA persons directory (external experts)
        2. Business inbox subdirectories (existing company entities)
        3. Business people directory (collaborator clones)
        4. Personal inbox subdirectories (personal projects)
        5. All alias targets

    Returns:
        Set of kebab-case entity slugs (e.g., {'alex-hormozi', 'cole-gordon'}).
    """
    entities: set[str] = set()

    # 1. DNA persons directory (source of truth for external experts)
    if DNA_PERSONS_DIR.exists():
        for entry in DNA_PERSONS_DIR.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                entities.add(entry.name)

    # Names that are content-type folders, NOT entities — must be excluded
    _CONTENT_TYPE_NAMES = {
        "calls",
        "courses",
        "documents",
        "email",
        "masterclasses",
        "masterminds",
        "meetings",
        "misc",
        "notes",
        "podcasts",
        "recordings",
        "screenshots",
        "scripts",
        "voice-memos",
        "whatsapp",
        "youtube",
    }

    # 2. Business inbox subdirectories (already-organized entities)
    biz_inbox = BUCKET_INBOXES.get("business")
    if biz_inbox and biz_inbox.exists():
        for entry in biz_inbox.iterdir():
            if (
                entry.is_dir()
                and not entry.name.startswith((".", "_"))
                and entry.name not in _CONTENT_TYPE_NAMES
            ):
                entities.add(entry.name)

    # 3. Business people directory (collaborator clones)
    try:
        biz_people = ROUTING.get("business_people")
        if biz_people and Path(biz_people).exists():
            for entry in Path(biz_people).iterdir():
                if entry.is_dir() and not entry.name.startswith("."):
                    entities.add(entry.name)
    except (TypeError, KeyError):
        pass

    # 4. Personal inbox subdirectories (exclude content-type folders)
    personal_inbox = BUCKET_INBOXES.get("personal")
    if personal_inbox and personal_inbox.exists():
        for entry in personal_inbox.iterdir():
            if (
                entry.is_dir()
                and not entry.name.startswith((".", "_"))
                and entry.name not in _CONTENT_TYPE_NAMES
            ):
                entities.add(entry.name)

    # 5. All alias targets (may not have dirs yet)
    entities.update(ENTITY_ALIASES.values())
    return entities


def _slugify(name: str) -> str:
    """Convert a name string to a kebab-case slug.

    Examples:
        'Alex Hormozi' -> 'alex-hormozi'
        'COLE_GORDON' -> 'cole-gordon'
        'Jeremy Haynes (EAD)' -> 'jeremy-haynes-ead'
    """
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", " ", s)  # remove non-word chars except hyphens
    s = re.sub(r"[\s_]+", "-", s)  # spaces/underscores to hyphens
    s = re.sub(r"-+", "-", s)  # collapse multiple hyphens
    return s.strip("-")


def detect_entity(filepath: Path) -> str:
    """Detect the entity (person or company) a file belongs to.

    Detection order:
        1. Check if the file is already inside an entity subdirectory
        2. Check filename against known entity names and aliases
        3. Check parent folder name against known entities
        4. Fallback to '_unclassified'

    Args:
        filepath: Path to the file being classified.

    Returns:
        Kebab-case entity slug (e.g., 'alex-hormozi') or '_unclassified'.
    """
    known = _load_known_entities()
    filename_lower = filepath.stem.lower()
    parent_name = filepath.parent.name.lower()

    # 1. Check if already inside an entity-named subdirectory
    #    e.g., inbox/alex-hormozi/some-file.txt
    parent_slug = _slugify(parent_name)
    if parent_slug in known:
        return parent_slug

    # Also check grandparent (inbox/alex-hormozi/courses/file.txt)
    grandparent_name = filepath.parent.parent.name.lower()
    grandparent_slug = _slugify(grandparent_name)
    if grandparent_slug in known:
        return grandparent_slug

    # 2. Check filename for known entity patterns
    #    Build a lookup combining canonical names and aliases.
    #    Strategy: find ALL matching entities and pick the one that appears
    #    EARLIEST in the filename. Among ties at the same position, prefer
    #    the longer match (more specific).
    candidates: list[tuple[str, str]] = []
    for slug in known:
        # Match the slug itself (with hyphens replaced by various separators)
        pattern_parts = slug.split("-")
        for sep in ["-", " ", "_", ""]:
            candidates.append((sep.join(pattern_parts), slug))

    for alias, slug in ENTITY_ALIASES.items():
        candidates.append((alias, slug))

    # Find all matches with their position in the filename
    matches: list[tuple[int, int, str]] = []  # (position, -length, slug)
    for pattern, slug in candidates:
        if not pattern:
            continue
        pos = filename_lower.find(pattern)
        if pos >= 0:
            matches.append((pos, -len(pattern), slug))

    if matches:
        # Sort by position (earliest first), then by -length (longest first)
        matches.sort()
        return matches[0][2]

    # 3. Check parent folder name via alias lookup
    if parent_name in ENTITY_ALIASES:
        return ENTITY_ALIASES[parent_name]
    if parent_slug in ENTITY_ALIASES:
        return ENTITY_ALIASES[parent_slug]

    return "_unclassified"


# ---------------------------------------------------------------------------
# CONTENT TYPE DETECTION
# ---------------------------------------------------------------------------

# Map of keyword patterns to content type directory names.
# Order matters: first match wins, so more specific patterns come first.
CONTENT_TYPE_PATTERNS: list[tuple[str, list[str]]] = [
    (
        "masterclasses",
        [
            r"masterclass",
            r"master[\-_\s]class",
        ],
    ),
    (
        "masterminds",
        [
            r"mastermind",
            r"inner[\-_\s]circle",
        ],
    ),
    (
        "courses",
        [
            r"course",
            r"module",
            r"modulo",
            r"aula",
            r"\bead\b",
            r"lesson",
            r"licao",
            r"treinamento",
            r"training",
        ],
    ),
    (
        "podcasts",
        [
            r"podcast",
            r"\bep\b\.?",
            r"episode",
            r"episodio",
        ],
    ),
    (
        "youtube",
        [
            r"youtube",
            r"\byt\b",
            r"\[yt\]",
            r"video",
            r"youtube\.com",
            r"watch\?v=",
        ],
    ),
    (
        "calls",
        [
            r"\bcall\b",
            r"\bmeet\b",
            r"meeting",
            r"reuni[aã]o",
            r"grava[cç][aã]o",
            r"recording",
            r"zoom",
            r"google\s*meet",
            r"lideranc",
            r"semanal",
            r"standup",
        ],
    ),
    (
        "scripts",
        [
            r"\bscript\b",
            r"\btemplate\b",
            r"roteiro",
        ],
    ),
    (
        "documents",
        [
            r"blueprint",
            r"\bpdf\b",
            r"\bdoc\b",
            r"contrato",
            r"contract",
            r"proposta",
            r"proposal",
            r"planilha",
            r"spreadsheet",
            r"whitepaper",
            r"ebook",
            r"e[\-_]book",
            r"guia",
            r"guide",
        ],
    ),
]

# Extension-based fallbacks when filename keywords don't match
EXTENSION_TYPE_MAP: dict[str, str] = {
    ".mp3": "podcasts",
    ".wav": "podcasts",
    ".m4a": "podcasts",
    ".mp4": "youtube",
    ".webm": "youtube",
    ".pdf": "documents",
    ".doc": "documents",
    ".docx": "documents",
    ".xlsx": "documents",
    ".xls": "documents",
    ".png": "documents",
    ".jpg": "documents",
    ".jpeg": "documents",
    ".gif": "documents",
    ".svg": "documents",
}


def detect_content_type(filepath: Path) -> str:
    """Classify a file's content type from its filename and extension.

    Args:
        filepath: Path to the file being classified.

    Returns:
        Content type string (e.g., 'courses', 'youtube', 'calls').
        Falls back to 'misc' if nothing matches.
    """
    filename_lower = filepath.stem.lower()
    parent_lower = filepath.parent.name.lower()
    search_text = f"{filename_lower} {parent_lower}"

    # 1. Check keyword patterns against filename + parent folder
    for content_type, patterns in CONTENT_TYPE_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, search_text, re.IGNORECASE):
                return content_type

    # 2. Fallback to extension-based classification
    ext = filepath.suffix.lower()
    if ext in EXTENSION_TYPE_MAP:
        return EXTENSION_TYPE_MAP[ext]

    return "misc"


# ---------------------------------------------------------------------------
# COMBINED CLASSIFIER
# ---------------------------------------------------------------------------


def classify_file(filepath: Path) -> tuple[str, str]:
    """Classify a file into (entity_slug, content_type).

    Args:
        filepath: Path to the file to classify.

    Returns:
        Tuple of (entity_slug, content_type).
        e.g., ('alex-hormozi', 'courses') or ('_unclassified', 'misc')
    """
    entity = detect_entity(filepath)
    content_type = detect_content_type(filepath)
    return entity, content_type


# ---------------------------------------------------------------------------
# ORGANIZER
# ---------------------------------------------------------------------------


def _is_already_organized(filepath: Path, inbox_root: Path) -> bool:
    """Check if a file is already in an entity/type subdirectory.

    A file is considered organized if its path relative to the inbox root
    has at least 2 directory levels (entity/type/file.ext).

    Args:
        filepath: Absolute path to the file.
        inbox_root: Absolute path to the bucket inbox root.

    Returns:
        True if the file appears to already be organized.
    """
    try:
        rel = filepath.relative_to(inbox_root)
    except ValueError:
        return False

    # rel.parts: ('entity', 'type', 'filename') = organized
    # rel.parts: ('filename',) = not organized
    # rel.parts: ('entity', 'filename') = partially organized
    if len(rel.parts) >= 3:
        # Already has entity/type structure
        return True
    return False


def _compute_destination(
    filepath: Path,
    inbox_root: Path,
    entity: str,
    content_type: str,
) -> Path:
    """Compute where a file should be moved to.

    Args:
        filepath: Current file path.
        inbox_root: The bucket inbox root.
        entity: Detected entity slug.
        content_type: Detected content type.

    Returns:
        Destination Path.
    """
    dest_dir = inbox_root / entity / content_type
    dest_file = dest_dir / filepath.name
    return dest_file


def organize_inbox(bucket: str = "external") -> dict:
    """Organize files in the specified bucket inbox.

    Scans the inbox for unorganized files, classifies each by entity and
    content type, and moves them to {inbox}/{entity}/{type}/.

    Args:
        bucket: One of 'external', 'business', or 'personal'.

    Returns:
        Summary dict: {'organized': N, 'skipped': N, 'already_organized': N,
                        'errors': [...], 'moves': [...]}
    """
    if bucket not in BUCKET_INBOXES:
        return {
            "error": f"Unknown bucket: {bucket}. Valid: {list(BUCKET_INBOXES.keys())}",
            "organized": 0,
            "skipped": 0,
            "already_organized": 0,
            "errors": [],
            "moves": [],
        }

    inbox_root = BUCKET_INBOXES[bucket]
    if not inbox_root.exists():
        logger.info("Inbox does not exist: %s — nothing to organize.", inbox_root)
        return {
            "bucket": bucket,
            "inbox": str(inbox_root),
            "organized": 0,
            "skipped": 0,
            "already_organized": 0,
            "errors": [],
            "moves": [],
        }

    organized = 0
    skipped = 0
    already_organized = 0
    errors: list[str] = []
    moves: list[dict] = []

    # Collect all files first (avoid mutating directory during iteration)
    all_files = sorted(
        f
        for f in inbox_root.rglob("*")
        if f.is_file() and f.name not in SKIP_NAMES and not f.name.startswith(".")
    )

    for filepath in all_files:
        # Skip .ref.yaml reference files (created by smart_router)
        if filepath.name.endswith(".ref.yaml"):
            skipped += 1
            continue

        # Skip unsupported extensions
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
            skipped += 1
            continue

        # Skip files already in entity/type structure
        if _is_already_organized(filepath, inbox_root):
            already_organized += 1
            continue

        # Classify
        entity, content_type = classify_file(filepath)

        # Compute destination
        dest = _compute_destination(filepath, inbox_root, entity, content_type)

        # Idempotency: if file already exists at destination, skip
        if dest.exists():
            if dest.resolve() == filepath.resolve():
                already_organized += 1
                continue
            # Same name but different source — append timestamp to avoid collision
            ts = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
            stem = dest.stem
            suffix = dest.suffix
            dest = dest.with_name(f"{stem}_{ts}{suffix}")

        # Move
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(filepath), str(dest))

            move_record = {
                "source": str(filepath),
                "destination": str(dest),
                "entity": entity,
                "content_type": content_type,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            moves.append(move_record)
            organized += 1
            logger.info(
                "Moved: %s -> %s/%s/%s",
                filepath.name,
                entity,
                content_type,
                filepath.name,
            )

        except OSError as e:
            error_msg = f"Failed to move {filepath}: {e}"
            errors.append(error_msg)
            logger.error(error_msg)

    # Clean up empty directories left behind after moves
    _cleanup_empty_dirs(inbox_root)

    summary = {
        "bucket": bucket,
        "inbox": str(inbox_root),
        "organized": organized,
        "skipped": skipped,
        "already_organized": already_organized,
        "errors": errors,
        "moves": moves,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    # Write log
    _write_organize_log(summary)

    return summary


def organize_all_inboxes() -> dict:
    """Organize files across all three bucket inboxes.

    Returns:
        Dict keyed by bucket name with individual summaries.
    """
    results = {}
    for bucket in BUCKET_INBOXES:
        results[bucket] = organize_inbox(bucket)
    return results


# ---------------------------------------------------------------------------
# CLEANUP
# ---------------------------------------------------------------------------


def _cleanup_empty_dirs(root: Path) -> None:
    """Remove empty directories under root (bottom-up).

    Does not remove root itself, and skips directories containing only
    dotfiles (.DS_Store, etc.).
    """
    if not root.exists():
        return

    # Walk bottom-up
    for dirpath in sorted(root.rglob("*"), reverse=True):
        if not dirpath.is_dir():
            continue
        if dirpath == root:
            continue

        # Check if dir is empty or contains only skippable files
        contents = list(dirpath.iterdir())
        real_contents = [
            c for c in contents if c.name not in SKIP_NAMES and not c.name.startswith(".")
        ]
        if not real_contents:
            # Remove dotfiles too, then the empty dir
            for c in contents:
                if c.is_file():
                    c.unlink()
            try:
                dirpath.rmdir()
            except OSError:
                pass  # Not empty after all


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------


def _write_organize_log(summary: dict) -> None:
    """Append organize log entry to JSONL file."""
    log_dir = LOGS / "inbox-organizer"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"organize-{summary.get('bucket', 'unknown')}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False, default=str) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point.

    Usage:
        python inbox_organizer.py                   # dry-run status of all inboxes
        python inbox_organizer.py external           # organize external inbox
        python inbox_organizer.py business           # organize business inbox
        python inbox_organizer.py personal           # organize personal inbox
        python inbox_organizer.py all                # organize all inboxes
        python inbox_organizer.py classify <path>    # classify a single file
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if len(sys.argv) < 2:
        # Status mode — show what WOULD be organized
        print("\n=== INBOX ORGANIZER — Status ===\n")
        for bucket, inbox_path in BUCKET_INBOXES.items():
            if not inbox_path.exists():
                print(f"  [{bucket:10s}] (inbox does not exist)")
                continue

            files = [
                f
                for f in inbox_path.rglob("*")
                if f.is_file()
                and f.name not in SKIP_NAMES
                and not f.name.startswith(".")
                and f.suffix.lower() in SUPPORTED_EXTENSIONS
            ]

            unorganized = [f for f in files if not _is_already_organized(f, inbox_path)]

            print(f"  [{bucket:10s}] {len(files)} files total, {len(unorganized)} need organizing")

            if unorganized:
                for f in unorganized[:5]:
                    entity, ctype = classify_file(f)
                    print(f"    -> {f.name}")
                    print(f"       entity={entity}, type={ctype}")
                if len(unorganized) > 5:
                    print(f"    ... and {len(unorganized) - 5} more")
        print()
        return 0

    cmd = sys.argv[1]

    if cmd == "classify" and len(sys.argv) >= 3:
        filepath = Path(sys.argv[2]).resolve()
        if not filepath.exists():
            print(f"File not found: {filepath}")
            return 1
        entity, content_type = classify_file(filepath)
        print(f"File:    {filepath.name}")
        print(f"Entity:  {entity}")
        print(f"Type:    {content_type}")
        return 0

    if cmd == "all":
        results = organize_all_inboxes()
        for bucket, summary in results.items():
            _print_summary(bucket, summary)
        return 0

    if cmd in BUCKET_INBOXES:
        summary = organize_inbox(cmd)
        _print_summary(cmd, summary)
        return 0

    print("Usage: python inbox_organizer.py [external|business|personal|all|classify <path>]")
    return 1


def _print_summary(bucket: str, summary: dict) -> None:
    """Print a formatted summary for a bucket organize run."""
    print(f"\n--- {bucket.upper()} ---")
    if "error" in summary:
        print(f"  Error: {summary['error']}")
        return
    print(f"  Organized:         {summary.get('organized', 0)}")
    print(f"  Already organized: {summary.get('already_organized', 0)}")
    print(f"  Skipped:           {summary.get('skipped', 0)}")
    if summary.get("errors"):
        print(f"  Errors:            {len(summary['errors'])}")
        for err in summary["errors"]:
            print(f"    ! {err}")
    if summary.get("moves"):
        print("  Moves:")
        for m in summary["moves"]:
            src_name = Path(m["source"]).name
            print(f"    {src_name} -> {m['entity']}/{m['content_type']}/")


if __name__ == "__main__":
    sys.exit(main())
