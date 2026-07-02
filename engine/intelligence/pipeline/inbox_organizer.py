#!/usr/bin/env python3
"""
INBOX ORGANIZER — Auto-organize files dropped into bucket inboxes
=================================================================
Detects files in any bucket inbox (external, business, personal) and
organizes them by entity (person/company) and content type into
subdirectories: {inbox}/{entity-slug}/{type}/

Entity detection uses the known persons from knowledge/external/dna/persons/
plus configurable aliases. Content type is classified from filename keywords.

Version: 1.2.0
Date: 2026-05-13
Story: S07 — EPIC-REORG-001
        STORY-MCE-ROUND-TRIP (N1/G4 — filename sidecar)
        G7 — sidecar-aware detect_entity (re-contamination fix)

Filename sidecar (G4):
    Before any move, the organizer emits
    `<file>.entity-discovery.json` next to the source file, conforming to
    `engine/intelligence/pipeline/filename_sidecar_schema.json`. This preserves
    the verbatim source name plus the dropped tokens so downstream consumers
    (smart_router, batch_auto_creator) can prefer the EXPLICIT entity signal
    over the legacy first-token heuristic. Failure to emit a sidecar is
    fail-open: the move still proceeds and a warning is logged.

Sidecar consumption (G7):
    ``detect_entity`` now reads ``<file>.entity-discovery.json`` BEFORE
    running its legacy heuristic. When the sidecar carries a
    ``decision.entity_author`` (written by the /ingest N5 orchestrator)
    or a non-empty ``entity_candidates[0]`` (written by the pre_03
    organizer/N1 emit), that slug WINS — the legacy first-token heuristic
    is bypassed entirely. This prevents re-contamination when ``cmd_full``
    re-invokes ``inbox_organizer`` after the orchestrator already routed
    the file (real /ingest test — a course .mp4 was being re-routed to
    ``example-company/youtube`` because the legacy heuristic ignored the
    sidecar's ``example-author`` decision).
"""

import inspect
import json
import logging
import os
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from engine.paths import (
    KNOWLEDGE_EXTERNAL,
    LOGS,
    ROUTING,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Bucket inbox paths — resolved from engine.paths ROUTING table
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
JOURNEY_LOG_DIR = LOGS / "journey-log"
JOURNEY_LOG_FILE = JOURNEY_LOG_DIR / "inbox-organizer.jsonl"
SAFE_MODE_ENV_VAR = "INBOX_SAFE_MODE"
SAFE_MODE_DEPRECATION_WARNING = (
    "DEPRECATION: INBOX_SAFE_MODE not set. _unclassified/ routing is permanently "
    "disabled. Set INBOX_SAFE_MODE=1 to suppress this warning."
)

# Path to the keyword fallback dictionary (AC2 — Story CALL-4)
ENTITY_KEYWORDS_FILE = Path(__file__).parent / "config" / "entity-keywords.yaml"

# Minimum keyword length for safety (shorter = too generic, risk of false positives)
_KEYWORD_MIN_LEN = 5


# ---------------------------------------------------------------------------
# ENTITY DETECTION
# ---------------------------------------------------------------------------

# Static aliases that map alternative names/spellings to the canonical slug.
# The canonical slug MUST match a directory name in DNA_PERSONS_DIR or be
# a known company/entity.
ENTITY_ALIASES: dict[str, str] = {
    # Populate via MEGA_BRAIN_ENTITY_ALIASES env var.
    # Format: "alias:slug,alias:slug"
    # Example: "hormozi:alex-hormozi,cole:cole-gordon"
}

# User-specific aliases loaded from env (MEGA_BRAIN_ENTITY_ALIASES=name:slug,name:slug)
_custom_aliases = os.environ.get("MEGA_BRAIN_ENTITY_ALIASES", "")
for _pair in _custom_aliases.split(","):
    _pair = _pair.strip()
    if ":" in _pair:
        _name, _slug = _pair.split(":", 1)
        ENTITY_ALIASES[_name.strip().lower()] = _slug.strip()


def _load_entity_keywords() -> dict[str, list[str]]:
    """Load the entity keyword dictionary from entity-keywords.yaml.

    Returns a mapping of entity_slug -> list[keyword] (lowercase).
    Keywords shorter than _KEYWORD_MIN_LEN chars AND that are single tokens
    are skipped to avoid false-positive matches.

    Failures are logged and return an empty dict — fail-open.
    Story: CALL-4 (AC2)
    """
    try:
        if not ENTITY_KEYWORDS_FILE.exists():
            logger.debug("Entity keywords file not found: %s", ENTITY_KEYWORDS_FILE)
            return {}
        data = yaml.safe_load(ENTITY_KEYWORDS_FILE.read_text(encoding="utf-8")) or {}
        entities = data.get("entities", {})
        result: dict[str, list[str]] = {}
        for slug, config in entities.items():
            if not isinstance(config, dict):
                continue
            keywords = config.get("keywords", [])
            valid_kws: list[str] = []
            for kw in keywords:
                if not isinstance(kw, str):
                    continue
                kw_lower = kw.lower().strip()
                # Accept: >= KEYWORD_MIN_LEN chars OR multi-token (contains space/hyphen)
                token_count = len(re.split(r"[\s\-]+", kw_lower))
                if len(kw_lower) >= _KEYWORD_MIN_LEN or token_count >= 2:
                    valid_kws.append(kw_lower)
            if valid_kws:
                result[slug] = valid_kws
        return result
    except Exception:
        logger.warning(
            "Failed to load entity keywords from %s — keyword fallback disabled",
            ENTITY_KEYWORDS_FILE,
            exc_info=True,
        )
        return {}


def _keyword_fallback(filename: str, entity_keywords: dict[str, list[str]]) -> str | None:
    """Layer-2 entity detection: keyword matching against entity-keywords.yaml.

    Iterates over all entity entries and checks if any keyword appears in the
    filename stem using case-insensitive whole-word matching. Returns the first
    match found (dict iteration order = file definition order, which places
    more specific entities first).

    Args:
        filename: The file's basename (with or without extension).
        entity_keywords: Loaded keyword dict from _load_entity_keywords().

    Returns:
        Entity slug if matched, or None.

    Story: CALL-4 (AC2)
    """
    if not entity_keywords:
        return None

    stem = Path(filename).stem.lower()
    # Normalize filename for matching: replace hyphens and underscores with spaces.
    # This allows multi-token keywords like "weekly sync" to match
    # "weekly-sync" in filenames without duplicating keywords.
    stem_normalized = re.sub(r"[-_]", " ", stem)

    for slug, keywords in entity_keywords.items():
        for kw in keywords:
            # Escape the keyword for regex, then wrap with word-boundary-like
            # lookaround. We use \b for word boundaries but also handle
            # Portuguese accented words by using lookahead/lookbehind for
            # non-alphanumeric boundaries.
            escaped = re.escape(kw)
            # Build pattern: match keyword surrounded by non-alphanumeric or
            # start/end of string (handles accented chars and spaces in normalized stems)
            pattern = r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])"
            # Match against both original and normalized (hyphen-free) stems
            if re.search(pattern, stem, re.IGNORECASE) or re.search(
                pattern, stem_normalized, re.IGNORECASE
            ):
                return slug

    return None


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

    # Names that are content-type folders or system dirs, NOT entities — must be excluded
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
        # Quarantine/system dirs — Story CALL-4
        "unclassified",
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


def _sidecar_path_for(filepath: Path) -> Path:
    """Resolve sidecar location for a given file.

    Primary: ``<filename>.entity-discovery.json`` (canonical, generated by
    ``organize_inbox`` itself).

    Fallback: ``*.entity-discovery.json`` in same dir whose name shares the
    stem prefix of ``filepath``. Covers sidecars like
    ``<stem>.youtube.entity-discovery.json`` generated by
    ``ingest-with-entity-discovery.py`` (URL flow), where the sidecar name is
    constructed from a stem-prefix + source-tag + extension, not the full
    transcript filename.

    Idempotent: if ``filepath`` already ends with ``.entity-discovery.json``
    we DO NOT append another suffix — that path IS the sidecar. This guards
    against the ``.entity-discovery.json.entity-discovery.json`` accumulation
    bug observed when ``cmd_full`` re-invokes the organizer and a sibling
    helper had treated a sidecar as a normal file.

    Returns the canonical primary path even if it does not exist, so callers
    can ``.exists()``-check downstream.

    MCE-13.7: added stem-prefix fallback glob for URL-flow sidecars.
    """
    if filepath.name.endswith(".entity-discovery.json"):
        return filepath
    primary = filepath.parent / f"{filepath.name}.entity-discovery.json"
    if primary.exists():
        return primary
    # Fallback: glob with base-name prefix match (case-insensitive).
    # Use the portion before the first dot (e.g. "how-to-make-business-growth"
    # from "how-to-make-business-growth.transcript.txt") so that a sidecar
    # named "how-to-make-business-growth.youtube.entity-discovery.json" matches.
    # Limit to 30 chars to avoid false matches on very short prefixes.
    base_prefix = filepath.name.split(".")[0].lower()[:30]
    if base_prefix:
        for candidate in sorted(filepath.parent.glob("*.entity-discovery.json")):
            if base_prefix in candidate.name.lower():
                return candidate
    return primary  # non-existent canonical path; caller handles


def _load_sidecar_decision(filepath: Path) -> str | None:
    """Return the explicit entity slug declared in a filename sidecar, if any.

    The sidecar (``<file>.entity-discovery.json``) is written by either:

        * the /ingest N5 orchestrator (carries ``decision.entity_author``),
        * the pre_03/N1 organizer emit (carries ``entity_candidates``).

    Precedence (G7):
        1. ``decision.entity_author`` — orchestrator verdict after Speaker
           Visual Gate + filename evidence reconciliation. Honored when not
           in {None, "", "unclassified"}.
        2. ``entity_candidates[0]`` — N1 emit's recommended slug.

    Failures are logged at debug level and return ``None`` so the legacy
    heuristic can take over (fail-open).

    Returns:
        Kebab-case entity slug declared in the sidecar, or ``None`` when no
        sidecar exists, the file is unreadable, or no usable slug is present.
    """
    try:
        sidecar = _sidecar_path_for(filepath)
        if not sidecar.exists():
            return None
        data = json.loads(sidecar.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None

        decision = data.get("decision")
        if isinstance(decision, dict):
            author = decision.get("entity_author")
            if isinstance(author, str):
                slug = author.strip()
                if slug and slug.lower() not in {"unclassified", "_unclassified", "unknown"}:
                    return slug

        candidates = data.get("entity_candidates")
        if isinstance(candidates, list):
            for cand in candidates:
                if isinstance(cand, str) and cand.strip():
                    return cand.strip()
        return None
    except Exception:
        logger.debug(
            "Sidecar parse failed for %s — falling back to heuristic detect_entity",
            filepath,
            exc_info=True,
        )
        return None


def detect_entity(filepath: Path) -> str | None:
    """Detect the entity (person or company) a file belongs to.

    Detection order:
        0. (G7) Sidecar precedence — honor decision.entity_author or
           entity_candidates[0] from ``<file>.entity-discovery.json``.
           Bypasses the legacy heuristic entirely when present.
        1. Check if the file is already inside an entity subdirectory
        2. Check filename against known entity names and aliases
        3. Check parent folder name against known entities
        4. Fallback to None (stay in place)

    Args:
        filepath: Path to the file being classified.

    Returns:
        Kebab-case entity slug (e.g., 'alex-hormozi') or None.
    """
    # G7 (2026-05-13): sidecar takes precedence over heuristic detection.
    # If <filename>.entity-discovery.json exists, honor decision.entity_author
    # (written by /ingest N5 orchestrator) or entity_candidates[0] (written
    # by pre_03/N1 emit). Prevents re-contamination when cmd_full re-invokes
    # inbox_organizer AFTER the orchestrator already routed the file.
    sidecar_slug = _load_sidecar_decision(filepath)
    if sidecar_slug:
        return sidecar_slug

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

    return None


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


def classify_file(
    filepath: Path,
    entity_keywords: dict[str, list[str]] | None = None,
) -> tuple[str | None, str, str]:
    """Classify a file into (entity_slug, content_type, classification_path).

    Two-layer classification (Story CALL-4):
        Layer 1: strict-parse via detect_entity() — slug/alias/sidecar heuristic
        Layer 2: keyword-fallback via _keyword_fallback() — entity-keywords.yaml

    Args:
        filepath: Path to the file to classify.
        entity_keywords: Pre-loaded keyword dict (optional — loads from disk when None).

    Returns:
        Tuple of (entity_slug, content_type, classification_path).
        - entity_slug: kebab-case slug or None (unresolved)
        - content_type: e.g. 'calls', 'misc'
        - classification_path: 'strict-parse' | 'keyword-fallback' | 'unresolved'
    """
    # Layer 1: existing heuristic (sidecar + slug + alias)
    entity = detect_entity(filepath)
    content_type = detect_content_type(filepath)

    if entity is not None:
        logger.info(
            "[organizer] CLASSIFIED via strict-parse: %s <- %s",
            entity,
            filepath.name,
        )
        return entity, content_type, "strict-parse"

    # Layer 2: keyword fallback
    if entity_keywords is None:
        entity_keywords = _load_entity_keywords()

    entity = _keyword_fallback(filepath.name, entity_keywords)
    if entity is not None:
        logger.info(
            "[organizer] CLASSIFIED via keyword-fallback: %s <- %s",
            entity,
            filepath.name,
        )
        return entity, content_type, "keyword-fallback"

    # Both layers failed
    logger.info(
        "[organizer] QUARANTINED: no entity match <- %s",
        filepath.name,
    )
    return None, content_type, "unresolved"


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


def _warn_safe_mode_if_unset() -> None:
    """Emit one-way migration warning when INBOX_SAFE_MODE is not explicitly set."""
    if os.environ.get(SAFE_MODE_ENV_VAR) != "1":
        logger.warning(SAFE_MODE_DEPRECATION_WARNING)


def _relative_inbox_state(path: Path, inbox_root: Path, bucket: str) -> str:
    """Convert an inbox path into a journey-log state label."""
    try:
        rel_parent = path.parent.relative_to(inbox_root)
    except ValueError:
        return f"inbox_{bucket}"

    if not rel_parent.parts:
        return f"inbox_{bucket}"

    suffix = "__".join(rel_parent.parts)
    return f"inbox_{bucket}__{suffix}"


def _write_journey_log(event: dict) -> None:
    """Append a journey log event to the organizer-specific JSONL stream."""
    JOURNEY_LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(JOURNEY_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _emit_transition_event(
    *,
    source_path: Path,
    dest_path: Path,
    inbox_root: Path,
    bucket: str,
    triggered_by: str,
) -> None:
    """Emit Art. IX-compliant journey event for a successful file move."""
    event = {
        "entity_id": source_path.name,
        "entity_type": "knowledge_file",
        "event_type": "transition",
        "from_state": _relative_inbox_state(source_path, inbox_root, bucket),
        "to_state": _relative_inbox_state(dest_path, inbox_root, bucket),
        "timestamp": datetime.now(UTC).isoformat(),
        "triggered_by": triggered_by,
    }
    _write_journey_log(event)


def _emit_classification_deferred_event(
    *,
    filepath: Path,
    inbox_root: Path,
    bucket: str,
) -> None:
    """Emit journey event when organizer cannot classify a file."""
    state = _relative_inbox_state(filepath, inbox_root, bucket)
    event = {
        "entity_id": filepath.name,
        "entity_type": "knowledge_file",
        "event_type": "classification_deferred",
        "from_state": state,
        "to_state": state,
        "timestamp": datetime.now(UTC).isoformat(),
        "triggered_by": "inbox_organizer.py",
        "notes": "Cannot classify — operator must /ingest with explicit --bucket",
    }
    _write_journey_log(event)


# ---------------------------------------------------------------------------
# FILENAME SIDECAR (N1 / G4 — STORY-MCE-ROUND-TRIP)
# ---------------------------------------------------------------------------

# Schema this file conforms to. Single source of truth lives next to this
# module so writer + reader cannot drift apart.
SIDECAR_SCHEMA_VERSION = "1.0.0"
SIDECAR_SUFFIX = ".entity-discovery.json"


def _compute_filename_diff(
    filename_original: str, filename_normalized: str
) -> tuple[list[str], list[str]]:
    """Diff two filenames at the token level for the sidecar.

    The organizer itself does NOT rename files today (it moves into entity/type
    subdirectories preserving the basename), but downstream pre_04+ stages
    historically dropped tokens like ``Jane Doe``. Emitting the diff
    against an intended ``filename_normalized`` keeps the sidecar honest
    regardless of which downstream step does the destructive rename.

    Returns:
        (tokens_kept, tokens_dropped) — both lowercased for stable comparison.
    """
    if not filename_original:
        return [], []

    def _tok(name: str) -> list[str]:
        stem = Path(name).stem
        # Split on common filename separators (parens, brackets, hyphens, dots, plus, comma, underscore, multi-space)
        raw = re.split(r"[+\-_,()\[\]\.]|\s+", stem)
        return [t.strip() for t in raw if t.strip()]

    orig_tokens_raw = _tok(filename_original)
    norm_tokens_set = {t.lower() for t in _tok(filename_normalized)}

    kept: list[str] = []
    dropped: list[str] = []
    seen_kept: set[str] = set()
    seen_dropped: set[str] = set()
    for tok in orig_tokens_raw:
        key = tok.lower()
        if key in norm_tokens_set:
            if key not in seen_kept:
                kept.append(tok)
                seen_kept.add(key)
        else:
            if key not in seen_dropped:
                dropped.append(tok)
                seen_dropped.add(key)
    return kept, dropped


def write_filename_sidecar(
    *,
    source_path: Path,
    bucket: str,
    filename_normalized: str | None = None,
    entity_candidates: list[str] | None = None,
    entity_evidence: dict | None = None,
    normalizer_rule: str = "noop",
    emitter: str = "engine.intelligence.pipeline.inbox_organizer.organize_inbox",
    sidecar_dir: Path | None = None,
) -> Path | None:
    """Emit a filename sidecar JSON next to a source file.

    Conforms to ``engine/intelligence/pipeline/filename_sidecar_schema.json``.

    The sidecar lands at ``<source_path>.entity-discovery.json`` by default
    (next to the source file BEFORE any move). Caller may pass ``sidecar_dir``
    to write it elsewhere — e.g., at the post-move destination — but the
    default keeps the evidence with the original file location for forensics.

    Behaviour:
        - Always sets ``schema_version``, ``emitted_at``, ``filename_original``,
          ``filename_normalized``, ``tokens_dropped``, ``original_path``, ``bucket``.
        - ``filename_normalized`` defaults to the source basename (no rename).
        - On any IO error this function logs a warning and returns ``None`` —
          NEVER raises, so callers can stay fail-open per N1 retry_policy.

    Returns:
        Path to the sidecar file on success, or ``None`` on failure.
    """
    try:
        target_dir = sidecar_dir if sidecar_dir is not None else source_path.parent
        # G7 (2026-05-13): idempotent sidecar naming. If ``source_path`` is
        # itself the sidecar (re-entry guard) or already carries the suffix
        # we MUST NOT append again — that produced
        # ``.entity-discovery.json.entity-discovery.json`` accumulation when
        # the organizer ran a second time post-orchestrator routing.
        if source_path.name.endswith(SIDECAR_SUFFIX):
            sidecar_path = target_dir / source_path.name
        else:
            sidecar_path = target_dir / f"{source_path.name}{SIDECAR_SUFFIX}"

        if filename_normalized is None:
            filename_normalized = source_path.name

        tokens_kept, tokens_dropped = _compute_filename_diff(source_path.name, filename_normalized)

        payload: dict = {
            "schema_version": SIDECAR_SCHEMA_VERSION,
            "emitted_at": datetime.now(UTC).isoformat(),
            "emitter": emitter,
            "filename_original": source_path.name,
            "filename_normalized": filename_normalized,
            "tokens_dropped": tokens_dropped,
            "tokens_kept": tokens_kept,
            "entity_candidates": list(entity_candidates) if entity_candidates else [],
            "entity_evidence": dict(entity_evidence) if entity_evidence else {},
            "original_path": str(source_path),
            "bucket": bucket if bucket in {"external", "business", "personal"} else "unknown",
            "normalizer_rule": normalizer_rule,
        }

        sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        sidecar_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return sidecar_path
    except Exception:
        logger.warning(
            "Failed to write filename sidecar for %s — falling back to current normalizer without sidecar",
            source_path,
            exc_info=True,
        )
        return None


def _derive_entity_candidates(filepath: Path, entity_slug: str | None) -> tuple[list[str], dict]:
    """Build the entity_candidates list + evidence dict for the sidecar.

    Combines the organizer's classifier verdict with the richer
    ``parse_filename_evidence`` output from batch_auto_creator (when import
    succeeds — pipeline-internal modules are circular-safe via local import).

    Returns:
        (candidates, evidence). Empty/empty when unknown — never raises.
    """
    candidates: list[str] = []
    if entity_slug:
        candidates.append(entity_slug)

    evidence: dict = {}
    try:
        # Local import: avoid module-level circular dependency in pipeline.
        from engine.intelligence.pipeline.batch_auto_creator import (
            parse_filename_evidence,
        )

        evidence = parse_filename_evidence(filepath.name)
        for person in evidence.get("persons", []):
            slug = _slugify(person)
            if slug and slug not in candidates:
                candidates.append(slug)
    except Exception:
        logger.debug(
            "parse_filename_evidence unavailable for %s — sidecar will lack evidence block",
            filepath.name,
            exc_info=True,
        )

    return candidates, evidence


def _compute_quarantine_destination(filepath: Path, inbox_root: Path) -> Path:
    """Compute where a file should land in _unclassified/ quarantine.

    Prefixes the filename with the current date: {YYYY-MM-DD}-{original-name}.
    If a file with that name already exists, appends a timestamp suffix.

    Args:
        filepath: Current file path.
        inbox_root: The bucket inbox root.

    Returns:
        Destination Path inside _unclassified/.

    Story: CALL-4 (AC3)
    """
    date_prefix = datetime.now(UTC).strftime("%Y-%m-%d")
    dest_dir = inbox_root / "_unclassified"
    dest_file = dest_dir / f"{date_prefix}-{filepath.name}"
    if dest_file.exists() and dest_file.resolve() != filepath.resolve():
        ts = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        stem = Path(filepath.name).stem
        suffix = filepath.suffix
        dest_file = dest_dir / f"{date_prefix}-{stem}_{ts}{suffix}"
    return dest_file


def _emit_quarantine_event(
    *,
    source_path: Path,
    dest_path: Path,
    inbox_root: Path,
    bucket: str,
) -> None:
    """Emit journey event for a file moved to _unclassified/ quarantine.

    Story: CALL-4 (AC3 + AC4)
    """
    event = {
        "entity_id": source_path.name,
        "entity_type": "knowledge_file",
        "event_type": "quarantined",
        "from_state": _relative_inbox_state(source_path, inbox_root, bucket),
        "to_state": f"inbox_{bucket}__unclassified",
        "timestamp": datetime.now(UTC).isoformat(),
        "triggered_by": "inbox_organizer.py:_emit_quarantine_event",
        "notes": "No entity match after strict-parse + keyword-fallback (CALL-4)",
    }
    _write_journey_log(event)


def organize_inbox(bucket: str = "external") -> dict:
    """Organize files in the specified bucket inbox.

    Scans the inbox for unorganized files, classifies each by entity and
    content type, and moves them to {inbox}/{entity}/{type}/.

    Two-layer classification (Story CALL-4):
        Layer 1 (strict-parse): sidecar + slug/alias heuristic
        Layer 2 (keyword-fallback): entity-keywords.yaml matching
        Fallback (quarantine): moves to _unclassified/ with date prefix

    Args:
        bucket: One of 'external', 'business', or 'personal'.

    Returns:
        Summary dict: {'organized': N, 'skipped': N, 'already_organized': N,
                       'quarantined': N, 'errors': [...], 'moves': [...]}
    """
    if bucket not in BUCKET_INBOXES:
        return {
            "error": f"Unknown bucket: {bucket}. Valid: {list(BUCKET_INBOXES.keys())}",
            "organized": 0,
            "skipped": 0,
            "already_organized": 0,
            "quarantined": 0,
            "errors": [],
            "moves": [],
        }

    inbox_root = BUCKET_INBOXES[bucket]
    _warn_safe_mode_if_unset()

    if not inbox_root.exists():
        logger.info("Inbox does not exist: %s — nothing to organize.", inbox_root)
        return {
            "bucket": bucket,
            "inbox": str(inbox_root),
            "organized": 0,
            "skipped": 0,
            "already_organized": 0,
            "quarantined": 0,
            "errors": [],
            "moves": [],
        }

    organized = 0
    skipped = 0
    already_organized = 0
    quarantined = 0
    errors: list[str] = []
    moves: list[dict] = []

    # Load keyword dict once per run (avoid re-parsing YAML per file)
    entity_keywords = _load_entity_keywords()

    # Collect all files first (avoid mutating directory during iteration)
    all_files = sorted(
        f
        for f in inbox_root.rglob("*")
        if f.is_file() and f.name not in SKIP_NAMES and not f.name.startswith(".")
    )

    for filepath in all_files:
        # Anti-symlink guard: reject symlinks to prevent traversal attacks.
        if filepath.is_symlink():
            logger.warning("Skipping symlink (security guard): %s", filepath)
            skipped += 1
            continue

        # Skip .ref.yaml reference files (created by smart_router)
        if filepath.name.endswith(".ref.yaml"):
            skipped += 1
            continue

        # G7 (2026-05-13): skip filename sidecars — they are NOT primary
        # files. The organizer mirrors them adjacent to their owning file
        # via the move block; iterating them directly would (a) try to
        # classify them as JSON content and (b) accumulate
        # .entity-discovery.json.entity-discovery.json suffixes.
        if filepath.name.endswith(SIDECAR_SUFFIX):
            skipped += 1
            continue

        # Skip unsupported extensions
        if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
            skipped += 1
            continue

        # Skip files already in _unclassified/ — they are already quarantined
        try:
            rel = filepath.relative_to(inbox_root)
            if rel.parts and rel.parts[0] == "_unclassified":
                already_organized += 1
                continue
        except ValueError:
            pass

        # Skip files already in entity/type structure
        if _is_already_organized(filepath, inbox_root):
            already_organized += 1
            continue

        # Two-layer classification (Story CALL-4)
        entity, content_type, classification_path = classify_file(filepath, entity_keywords)

        if entity is None:
            # Both layers failed — quarantine the file (AC3)
            dest = _compute_quarantine_destination(filepath, inbox_root)
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(filepath), str(dest))
                _emit_quarantine_event(
                    source_path=filepath,
                    dest_path=dest,
                    inbox_root=inbox_root,
                    bucket=bucket,
                )
                quarantined += 1
                move_record = {
                    "source": str(filepath),
                    "destination": str(dest),
                    "entity": None,
                    "content_type": content_type,
                    "classification_path": "quarantined",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
                moves.append(move_record)
            except OSError as e:
                # If quarantine move fails, fall back to old behavior (leave in place)
                error_msg = f"Failed to quarantine {filepath}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                _emit_classification_deferred_event(
                    filepath=filepath,
                    inbox_root=inbox_root,
                    bucket=bucket,
                )
                skipped += 1
            continue

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

        # Filename sidecar (N1 / G4): emit BEFORE the move so the
        # entity-discovery evidence sits next to the source file even if the
        # downstream destructive normalizer later renames the file.
        # The organizer itself is non-destructive on the basename, so
        # filename_normalized == source name here; downstream stages that DO
        # rename may rewrite the sidecar via the same helper.
        candidates, evidence = _derive_entity_candidates(filepath, entity)
        write_filename_sidecar(
            source_path=filepath,
            bucket=bucket,
            filename_normalized=filepath.name,
            entity_candidates=candidates,
            entity_evidence=evidence,
            normalizer_rule="organizer.noop",
            emitter="engine.intelligence.pipeline.inbox_organizer.organize_inbox",
        )

        # Move
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(filepath), str(dest))
            # Mirror the sidecar to the destination so consumers reading from
            # the post-organize location still find it adjacent to the file.
            # G7 (2026-05-13): use _sidecar_path_for() so we NEVER append the
            # suffix to a path that already ends with .entity-discovery.json.
            # Earlier the naive concatenation produced
            # ``foo.mp4.entity-discovery.json.entity-discovery.json`` when the
            # routine ran a second time over an already-moved sidecar pair.
            try:
                src_sidecar = _sidecar_path_for(filepath)
                if src_sidecar.exists() and src_sidecar != filepath:
                    dest_sidecar = _sidecar_path_for(dest)
                    if not dest_sidecar.exists():
                        dest_sidecar.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(src_sidecar), str(dest_sidecar))
            except Exception:
                logger.debug("Failed to mirror sidecar after move for %s", filepath, exc_info=True)
            caller_line = inspect.currentframe().f_lineno - 1
            _emit_transition_event(
                source_path=filepath,
                dest_path=dest,
                inbox_root=inbox_root,
                bucket=bucket,
                triggered_by=f"inbox_organizer.py:{caller_line}",
            )

            move_record = {
                "source": str(filepath),
                "destination": str(dest),
                "entity": entity,
                "content_type": content_type,
                "classification_path": classification_path,
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
        "quarantined": quarantined,
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
                    entity, ctype, layer = classify_file(f)
                    print(f"    -> {f.name}")
                    print(f"       entity={entity}, type={ctype}, layer={layer}")
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
        entity, content_type, classification_path = classify_file(filepath)
        print(f"File:    {filepath.name}")
        print(f"Entity:  {entity}")
        print(f"Type:    {content_type}")
        print(f"Layer:   {classification_path}")
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
    print(f"  Quarantined:       {summary.get('quarantined', 0)}")
    print(f"  Skipped:           {summary.get('skipped', 0)}")
    if summary.get("errors"):
        print(f"  Errors:            {len(summary['errors'])}")
        for err in summary["errors"]:
            print(f"    ! {err}")
    if summary.get("moves"):
        print("  Moves:")
        for m in summary["moves"]:
            src_name = Path(m["source"]).name
            layer = m.get("classification_path", "?")
            if m.get("entity"):
                print(f"    [{layer}] {src_name} -> {m['entity']}/{m['content_type']}/")
            else:
                print(f"    [quarantined] {src_name} -> _unclassified/")


if __name__ == "__main__":
    sys.exit(main())
