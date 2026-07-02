"""
batch_auto_creator.py -- Automatic Batch Creator for Pipeline Jarvis
====================================================================
Scans organized inbox directories, detects when enough unprocessed files
accumulate for a person, and auto-creates batches using batch_governor's
partition logic.

Closes the organize-to-process gap: after files are classified, routed,
and organized into ``knowledge/external/inbox/{person}/{type}/``, this
module detects unprocessed files and creates BATCH-XXX JSON + MD logs
(dual-location per REGRA #8).

Usage::

    # Default: scan and create batches
    python3 core/intelligence/pipeline/batch_auto_creator.py

    # Dry-run: show what would be created, write nothing
    python3 core/intelligence/pipeline/batch_auto_creator.py --dry-run

    # Status: show registry stats
    python3 core/intelligence/pipeline/batch_auto_creator.py status

    # Force: batch even if below MIN_FILES threshold
    python3 core/intelligence/pipeline/batch_auto_creator.py --force

Version: 1.0.0
Date: 2026-03-10
Spec: docs/plans/epic1-phase1.4-batch-auto-creator-spec.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# IMPORTS: core.paths and batch_governor
# ---------------------------------------------------------------------------

try:
    from engine.paths import ARTIFACTS, LOGS, MISSION_CONTROL, ROUTING
except ImportError:
    # Fallback for standalone execution
    _ROOT = Path(__file__).resolve().parent.parent.parent.parent
    LOGS = _ROOT / "logs"
    MISSION_CONTROL = _ROOT / ".claude" / "mission-control"
    ARTIFACTS = _ROOT / ".data" / "artifacts"  # S15: was ROOT/artifacts
    ROUTING = {
        "external_inbox": _ROOT / "knowledge" / "external" / "inbox",
        "batch_log": LOGS / "batches",
        "batch_registry": MISSION_CONTROL / "BATCH-REGISTRY.json",
        "batch_auto_creator_log": LOGS / "batch-auto-creator.jsonl",
    }

try:
    from engine.intelligence.pipeline.batch_governor import MAX_BATCH_SIZE, partition_files
except ImportError:
    MAX_BATCH_SIZE = 5

    def partition_files(files: list[Path], max_size: int = MAX_BATCH_SIZE) -> list[dict]:
        """Minimal fallback if batch_governor is not importable."""
        batches = []
        num = 1
        for i in range(0, len(files), max_size):
            chunk = files[i : i + max_size]
            batches.append(
                {
                    "id": f"BATCH-{num:03d}",
                    "source_hint": "unknown",
                    "files": [str(f) for f in chunk],
                    "count": len(chunk),
                    "total_size": sum(f.stat().st_size for f in chunk if f.exists()),
                }
            )
            num += 1
        return batches


logger = logging.getLogger("batch_auto_creator")

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# Minimum unprocessed files per person to trigger auto-batching.
MIN_FILES: int = int(os.environ.get("BATCH_MIN_FILES", "3"))

# Registry file path.
BATCH_REGISTRY_PATH: Path = ROUTING.get("batch_registry", MISSION_CONTROL / "BATCH-REGISTRY.json")

# Log paths (dual-location per REGRA #8).
BATCH_JSON_DIR: Path = MISSION_CONTROL / "batch-logs"
BATCH_MD_DIR: Path = ROUTING.get("batch_log", LOGS / "batches")

# JSONL audit log.
AUTO_CREATOR_LOG: Path = ROUTING.get("batch_auto_creator_log", LOGS / "batch-auto-creator.jsonl")

# Scan all 3 knowledge buckets.
SCAN_BUCKETS: list[str] = ["external", "business", "personal"]

# File extensions eligible for batching.
BATCHABLE_EXTENSIONS: set[str] = {".txt", ".md", ".docx", ".pdf"}

# Files to always skip.
SKIP_NAMES: set[str] = {".DS_Store", "Thumbs.db", ".gitkeep", "__pycache__"}

# ---------------------------------------------------------------------------
# SOURCE CODE MAP
# ---------------------------------------------------------------------------

SOURCE_CODE_MAP: dict[str, str] = {
    # Populate via MEGA_BRAIN_SOURCE_CODES env var.
    # Format: "slug:CODE,slug:CODE"
    # Example: "alex-hormozi:AH,cole-gordon:CG"
}

# Load user-specific source codes from env
_custom_source_codes = os.environ.get("MEGA_BRAIN_SOURCE_CODES", "")
for _pair in _custom_source_codes.split(","):
    _pair = _pair.strip()
    if ":" in _pair:
        _slug, _code = _pair.split(":", 1)
        SOURCE_CODE_MAP[_slug.strip()] = _code.strip()


# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------


@dataclass
class BatchResult:
    """Represents one created batch."""

    batch_id: str = ""
    source_code: str = ""
    source_name: str = ""
    files: list[str] = field(default_factory=list)
    file_count: int = 0
    total_size_bytes: int = 0
    json_path: str = ""
    md_path: str = ""
    cascading_triggered: bool = False
    created_at: str = ""


@dataclass
class ScanResult:
    """Aggregated result of a full scan."""

    batches_created: list[BatchResult] = field(default_factory=list)
    files_scanned: int = 0
    files_already_batched: int = 0
    files_below_threshold: dict[str, int] = field(default_factory=dict)
    persons_scanned: int = 0
    duration_ms: int = 0


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(UTC).isoformat()


def derive_source_code(entity_slug: str) -> str:
    """Convert entity slug to a 2-3 char source code for batch IDs.

    Strategy:
        1. Check SOURCE_CODE_MAP for known overrides.
        2. Fall back to first letter of each hyphen-separated word, uppercased.
        3. Cap at 3 characters.

    Examples::

        'jeremy-haynes'      -> 'JH'
        'cole-gordon'        -> 'CG'
        'the-scalable-company' -> 'TSC'
        'new-person'         -> 'NP'
    """
    if entity_slug in SOURCE_CODE_MAP:
        return SOURCE_CODE_MAP[entity_slug]

    parts = entity_slug.split("-")
    code = "".join(p[0].upper() for p in parts if p)
    return code[:3] if code else "UNK"


def _humanize_source_name(entity_slug: str) -> str:
    """Convert entity slug to a human-readable name.

    Example: 'jeremy-haynes' -> 'Jeremy Haynes'
    """
    return " ".join(w.capitalize() for w in entity_slug.split("-"))


# ---------------------------------------------------------------------------
# ENTITY DISCOVERY (Phase 2, 2026-05-12) — filename + content cross-reference
# ---------------------------------------------------------------------------
#
# The pipeline previously inferred entity from filename token #0 ALONE. That
# enabled silent misclassification (e.g. "Acme-Widget-Jane-Doe.mp4" became
# entity=acme, when in reality the AUTHOR is jane-doe and the SUBJECT is
# widget, with acme being a cross-reference / co-host).
#
# Entity Discovery Dual fixes this with three passes:
#   PASS 1: parse_filename_evidence  — deterministic, no LLM
#   PASS 2: parse_content_evidence   — from Gemini speakers + entities_mentioned
#   PASS 3: infer_entities           — reconcile + decision

# Noise tokens that NEVER form a person/company name (technical metadata)
NOISE_TOKENS = {
    "parte",
    "part",
    "p1",
    "p2",
    "p3",
    "p4",
    "1080p",
    "720p",
    "480p",
    "360p",
    "4k",
    "8k",
    "h264",
    "h265",
    "h.264",
    "h.265",
    "av1",
    "vp9",
    "youtube",
    "youtu",
    "yt",
    "mp4",
    "mov",
    "webm",
    "mkv",
    "avi",
    "audio",
    "video",
    "transcript",
    "raw",
    "original",
    "edit",
}

# Words that indicate the immediately following token is a name (PT-BR/EN)
NAME_HINT_PREFIXES = {
    "com",
    "with",
    "feat",
    "featuring",
    "by",
    "host",
    "guest",
    "apresenta",
    "presenta",
    "speaker",
    "presenter",
}


def parse_filename_evidence(filename: str) -> dict:
    """Extract entity candidates from a filename WITHOUT LLM.

    Strategy:
        1. STRONG SPLIT on -, +, _, parentheses, commas — produces "groups"
        2. WITHIN each group, split on space → tokens
        3. Per-group classification:
            - 2-3 Title-Case tokens consecutive → person (e.g. "Jane Doe")
            - 1 Title-Case token alone → company
            - Tokens after a person separated by 2+ spaces → separate company
        4. Filter noise (resolution, codec, container, hashes, numbers)

    Args:
        filename: Filename as STORED on disk. Use the ORIGINAL name from
                 the user's download — NOT a normalized slug.

    Returns:
        Dict with:
          - tokens: list[str] — all cleaned tokens (flat)
          - persons: list[str] — multi-token person names
          - companies: list[str] — single-token company names
          - noise: list[str] — filtered out
          - raw_stem: str — stem without extension
          - groups: list[list[str]] — tokens grouped by strong separators
    """
    import re as _re
    from pathlib import Path as _Path

    stem = _Path(filename).stem

    # PARENTHETICAL BIAS (STORY-ONDA1-author-routing): capture the normalized
    # content of every (...) and [...] span BEFORE the strong-split discards
    # the bracket boundaries. A person token that lives inside parentheses —
    # e.g. "...(Alex Hormozi)..." — is a much stronger author signal than a
    # bare title-cased phrase from the title body ("Playbook Pricing"). We use
    # this to weight parenthetical persons above title-word persons downstream.
    _paren_spans: list[str] = [
        m.strip().lower()
        for m in _re.findall(r"\(([^)]*)\)|\[([^\]]*)\]", stem)
        for m in (m[0] or m[1],)
        if m and m.strip()
    ]

    # STRONG SEPARATORS: -, +, parentheses, commas, brackets, underscores, dots
    # WEAK SEPARATOR: space (preserved INSIDE groups)
    # Multiple spaces (2+) also count as STRONG separator
    # Split on strong separators, keeping space-separated within each group
    raw_groups = _re.split(r"[\-+_,()\[\].]+|\s{2,}", stem)
    raw_groups = [g.strip() for g in raw_groups if g.strip()]

    cleaned_groups: list[list[str]] = []
    all_noise: list[str] = []

    for group in raw_groups:
        tokens = group.split()  # split on single spaces
        if not tokens:
            continue

        cleaned: list[str] = []
        skip_next = False
        for i, tok in enumerate(tokens):
            if skip_next:
                skip_next = False
                all_noise.append(tok)
                continue
            # "Parte #1", "Part 2"
            if tok.lower() in {"parte", "part"} and i + 1 < len(tokens):
                all_noise.append(tok)
                nxt = tokens[i + 1]
                if nxt.startswith("#") or nxt.isdigit() or _re.match(r"^#?\d+$", nxt):
                    skip_next = True
                continue
            # Pure numbers, hashes, version tags
            if (
                tok.isdigit()
                or tok.startswith("#")
                or _re.match(r"^\d{1,4}[a-z]{1,2}$", tok.lower())
            ):
                all_noise.append(tok)
                continue
            # Noise vocabulary
            if tok.lower() in NOISE_TOKENS:
                all_noise.append(tok)
                continue
            cleaned.append(tok)

        if cleaned:
            cleaned_groups.append(cleaned)

    # CLASSIFICATION per group
    persons: list[str] = []
    companies: list[str] = []

    def is_title_case(tok: str) -> bool:
        return len(tok) >= 2 and tok[0].isupper() and any(c.isalpha() for c in tok[1:])

    for group in cleaned_groups:
        # Filter to Title-Case tokens only
        tc_tokens = [t for t in group if is_title_case(t)]

        if not tc_tokens:
            continue

        # If group has 2-3 Title-Case tokens → likely person (FirstName LastName [Middle])
        # If group has exactly 1 Title-Case → likely company
        # If group has 4+ Title-Case → ambiguous, take first 2 as person + rest as companies
        if len(tc_tokens) == 1:
            companies.append(tc_tokens[0])
        elif 2 <= len(tc_tokens) <= 3:
            persons.append(" ".join(tc_tokens))
        else:
            # 4+ tokens: take first 2 as person, rest as separate companies
            persons.append(" ".join(tc_tokens[:2]))
            for extra in tc_tokens[2:]:
                if extra not in companies:
                    companies.append(extra)

        # Non-Title-Case tokens in same group (lowercase like "jeremy") — skip silently
        # (could be slug-style: "jeremy-haynes" already separated by strong sep)

    # Dedupe companies preserving order
    seen = set()
    deduped_companies = []
    for c in companies:
        if c.lower() not in seen:
            seen.add(c.lower())
            deduped_companies.append(c)

    flat_tokens = [t for group in cleaned_groups for t in group]

    # PARENTHETICAL BIAS (STORY-ONDA1-author-routing): mark which discovered
    # person names came from inside a (...) / [...] span. A person whose
    # normalized form is a substring of any parenthetical span is flagged.
    # infer_entities weights these above title-word persons when picking the
    # author candidate.
    persons_in_parens: list[str] = []
    if _paren_spans:
        for p in persons:
            p_norm = p.lower().strip()
            if any(p_norm in span for span in _paren_spans):
                persons_in_parens.append(p)

    return {
        "tokens": flat_tokens,
        "persons": persons,
        "persons_in_parens": persons_in_parens,
        "companies": deduped_companies,
        "noise": all_noise,
        "raw_stem": stem,
        "groups": cleaned_groups,
    }


def parse_content_evidence(gemini_result: dict | None) -> dict:
    """Extract entity candidates from Gemini output (speakers + entities_mentioned).

    Args:
        gemini_result: Output dict from extract_local_video_via_gemini.
                       Can be None (no Gemini call made).

    Returns:
        Dict with:
          - top_speaker: str | None — highest-confidence identified speaker name
          - speaker_confidence: str — "high" | "medium" | "low" | "none"
          - top_subject: str | None — entity_mentioned with is_subject=true, most mentions
          - subject_mention_count: int
          - all_speakers: list[str] — all named speakers
          - all_entities: list[dict] — all entities_mentioned
    """
    result = {
        "top_speaker": None,
        "speaker_confidence": "none",
        "top_subject": None,
        "subject_mention_count": 0,
        "all_speakers": [],
        "all_entities": [],
    }

    if not gemini_result or not isinstance(gemini_result, dict):
        return result

    # Speakers
    speakers = gemini_result.get("speakers", []) or []
    named_speakers = []
    for s in speakers:
        if isinstance(s, dict):
            name = s.get("name", "")
            if name and not name.upper().startswith("SPEAKER_UNKNOWN"):
                named_speakers.append(s)
        elif isinstance(s, str):
            if not s.upper().startswith("SPEAKER_UNKNOWN"):
                named_speakers.append({"name": s, "confidence": "low"})

    if named_speakers:
        # Prefer high confidence
        named_speakers.sort(
            key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("confidence", "low"), 3)
        )
        result["top_speaker"] = named_speakers[0].get("name")
        result["speaker_confidence"] = named_speakers[0].get("confidence", "low")
        result["all_speakers"] = [s.get("name") for s in named_speakers]

    # Subject discovery
    entities = gemini_result.get("entities_mentioned", []) or []
    result["all_entities"] = entities

    subjects = [e for e in entities if isinstance(e, dict) and e.get("is_subject")]
    if subjects:
        subjects.sort(key=lambda e: e.get("mention_count", 0), reverse=True)
        result["top_subject"] = subjects[0].get("name")
        result["subject_mention_count"] = subjects[0].get("mention_count", 0)

    return result


def _slugify(name: str) -> str:
    """Convert a Title-Case name to kebab-case slug.

    'Jane Doe' -> 'jane-doe'
    'Acme' -> 'acme'
    """
    import re as _re

    s = name.lower().strip()
    s = _re.sub(r"[^\w\s-]", "", s)
    s = _re.sub(r"[\s_]+", "-", s)
    s = _re.sub(r"-+", "-", s)
    return s.strip("-")


# STORY-MCE-INGEST-ROBUSTNESS AC-4 + AC-7 (2026-05-27)
# Local content evidence (header parsing) + FirefliesSync state consultation.
# Used by infer_entities to recover bucket signal for non-video files when
# Gemini Speaker Visual Gate is bypassed.

# Host/founder email domains. Sourced from internal_people.FOUNDER_DOMAINS
# (configured via MEGA_BRAIN_FOUNDER_DOMAINS); falls back to empty so the
# engine ships free of any organization-specific identity.
try:
    from engine.intelligence.pipeline.internal_people import FOUNDER_DOMAINS as _FOUNDER_DOMAINS

    _HOST_DOMAINS = set(_FOUNDER_DOMAINS)
except Exception:
    _HOST_DOMAINS = set()


def parse_local_content_evidence(
    file_path: "Path | None" = None,
    filename: str = "",
) -> dict:
    """Parse Fireflies / Read.ai / generic transcript headers from .txt/.md.

    Looks for:
        - "Source: Fireflies.ai | Transcript ID: <ID>"  -> consult FirefliesSync state
        - "Participants: a@x.com, b@y.com"               -> infer bucket from domains
        - "[MEET-NNNN]" or "[CALL-NNNN]" in filename     -> meeting business signal

    Returns:
        Dict with:
          - bucket_hint: str | None  — "business" | "external" | None
          - bucket_confidence: str   — "high" | "medium" | "low" | "none"
          - host_emails: list[str]   — participants whose domain is a host
          - external_emails: list[str] — participants whose domain is NOT host
          - transcript_id: str | None — Fireflies / Read.ai transcript ID
          - tag_match: str | None    — "[MEET-NNNN]" or "[CALL-NNNN]" if present
          - reasons: list[str]       — human-readable signal trail
    """
    import re as _re
    from pathlib import Path as _Path

    result: dict = {
        "bucket_hint": None,
        "bucket_confidence": "none",
        "host_emails": [],
        "external_emails": [],
        "transcript_id": None,
        "tag_match": None,
        "reasons": [],
    }

    # 1. Tag detection in filename (strongest single signal for meetings)
    if filename:
        m = _re.search(r"\[(MEET|CALL)-(\d+)\]", filename)
        if m:
            result["tag_match"] = m.group(0)
            result["bucket_hint"] = "business"
            result["bucket_confidence"] = "medium"
            result["reasons"].append(f"filename tag {m.group(0)} = meeting/call (business)")

    # 2. Read header (first ~2000 bytes) of file
    if file_path is None or not isinstance(file_path, _Path) or not file_path.exists():
        return result

    try:
        head = file_path.read_text(encoding="utf-8", errors="ignore")[:4096]
    except Exception:
        return result

    # 2a. Source: Fireflies | Transcript ID
    src_match = _re.search(
        r"Source:\s*(Fireflies\.ai|Read\.ai|Otter\.ai)\s*\|\s*Transcript ID:\s*([A-Z0-9]+)",
        head,
        _re.IGNORECASE,
    )
    if src_match:
        result["transcript_id"] = src_match.group(2)
        if result["bucket_hint"] is None:
            result["bucket_hint"] = "business"
            result["bucket_confidence"] = "medium"
        result["reasons"].append(
            f"header Source={src_match.group(1)} transcript_id={src_match.group(2)}"
        )

    # 2b. Participants line
    part_match = _re.search(r"Participants?:\s*(.+)", head)
    if part_match:
        line = part_match.group(1)
        # split by comma, semicolon, or pipe
        tokens = _re.split(r"[,;|]", line)
        emails = []
        for t in tokens:
            em = _re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", t)
            if em:
                emails.append(em.group(0).lower())
        host = []
        external = []
        for em in emails:
            domain = em.rsplit("@", 1)[-1]
            if domain in _HOST_DOMAINS:
                host.append(em)
            else:
                external.append(em)
        result["host_emails"] = host
        result["external_emails"] = external
        if host:
            # Strong business signal: host email in participants
            result["bucket_hint"] = "business"
            result["bucket_confidence"] = "high"
            result["reasons"].append(
                f"participants include host emails: {host[:3]}"
            )

    # 3. Consult FIREFLIES-STATE.json (AC-7) if transcript_id present
    if result["transcript_id"]:
        try:
            import os as _os

            from engine.paths import MISSION_CONTROL

            # Generic state file is always checked. Per-account state files
            # (FIREFLIES-STATE-<account>.json) are opt-in via env var.
            _accounts = [
                a.strip()
                for a in _os.environ.get("MEGA_BRAIN_FIREFLIES_ACCOUNTS", "").split(",")
                if a.strip()
            ]
            _state_names = ["FIREFLIES-STATE.json"] + [
                f"FIREFLIES-STATE-{a}.json" for a in _accounts
            ]
            for state_name in _state_names:
                state_path = MISSION_CONTROL / state_name
                if not state_path.exists():
                    continue
                import json as _json
                try:
                    state = _json.loads(state_path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                processed_ids = state.get("processed_ids", []) or []
                if result["transcript_id"] in processed_ids:
                    routed_empresa = state.get("routed_empresa", 0)
                    routed_pessoal = state.get("routed_pessoal", 0)
                    # If transcript was processed and empresa count > 0, sinal forte
                    if routed_empresa >= routed_pessoal:
                        result["bucket_hint"] = "business"
                        result["bucket_confidence"] = "high"
                        result["reasons"].append(
                            f"FirefliesSync state[{state_name}] processed_id matched "
                            f"and routed_empresa={routed_empresa} >= routed_pessoal={routed_pessoal}"
                        )
                    break
        except Exception:
            # Fail-open: missing FIREFLIES-STATE shouldn't break discovery
            pass

    return result


# STORY-MCE-FOUNDER-ROUTING (2026-06-09)
# Founder-in-call detection. When the founder (the configured owner / any
# @<founder-domain> email / a name matching a people-registry) is a
# PARTICIPANT, the call is a BUSINESS relationship, NOT an external expert —
# even if the filename carries a person token that the legacy heuristic would
# route to external.


def detect_internal_party(
    fn_evidence: dict,
    cn_evidence: dict,
    local_evidence: dict,
) -> dict:
    """Detect whether an internal/founder party is present in the material.

    Signal precedence (strongest first), per @architect design 2026-06-09:
        1. PARTICIPANT EMAILS  — host_emails parsed from a ``Participants:``
           header (local content evidence). A founder-domain email is the
           single strongest, least-ambiguous signal.
        2. SPEAKER NAMES       — named speakers from the Gemini Speaker Gate.
        3. CONTENT/FILENAME NAME MENTIONS — founder/collaborator names that
           appear among filename persons OR content entities/speakers.

    Degrades gracefully: if NONE of the signals name an internal party, the
    result is ``present=False`` and the caller keeps the external default —
    solo-expert material (Alex Hormozi YouTube) is never forced to business.

    Args:
        fn_evidence:    output of parse_filename_evidence.
        cn_evidence:    output of parse_content_evidence.
        local_evidence: output of parse_local_content_evidence.

    Returns:
        Dict with:
          - present: bool
          - relationship_type: str | None — "founder"|"collaborator"|"partner"|"advisor"
          - internal_slug: str | None — slug of the internal party found
          - internal_display: str | None
          - signal: str | None — which signal fired ("participant_email"|"speaker"|"name_mention")
          - counterpart_display: str | None — the strongest NON-internal person name
          - counterpart_is_collaborator: bool — counterpart itself matched a registry
          - reasons: list[str]
    """
    result: dict = {
        "present": False,
        "relationship_type": None,
        "internal_slug": None,
        "internal_display": None,
        "signal": None,
        "counterpart_display": None,
        "counterpart_slug": None,
        "counterpart_is_collaborator": False,
        "reasons": [],
    }

    try:
        from engine.intelligence.pipeline.internal_people import classify
    except Exception:
        # Fail-open: without the lookup module, no founder rule (keep legacy).
        return result

    # Collect all PERSON-like signals across evidence sources, tagged by signal.
    # Order matters: we record the strongest signal that yielded an internal hit.
    persons_fn = list(fn_evidence.get("persons", []) or [])
    speakers = list(cn_evidence.get("all_speakers", []) or [])
    host_emails = list(local_evidence.get("host_emails", []) or [])
    external_emails = list(local_evidence.get("external_emails", []) or [])

    internal_hit: tuple[str, str, str] | None = None  # (slug, rel, signal)
    internal_display: str | None = None

    # --- Signal 1: participant emails (strongest) -----------------------
    for em in host_emails:
        c = classify(em)
        if c:
            internal_hit = (c[0], c[1], "participant_email")
            internal_display = em
            result["reasons"].append(f"participant email {em} -> internal ({c[1]})")
            break

    # --- Signal 2: named speakers ---------------------------------------
    if internal_hit is None:
        for sp in speakers:
            if not sp:
                continue
            c = classify(sp)
            if c:
                internal_hit = (c[0], c[1], "speaker")
                internal_display = sp
                result["reasons"].append(f"speaker '{sp}' -> internal ({c[1]})")
                break

    # --- Signal 3: filename person + content entity name mentions -------
    name_mentions: list[str] = list(persons_fn)
    for e in cn_evidence.get("all_entities", []) or []:
        if isinstance(e, dict) and e.get("name"):
            name_mentions.append(e["name"])
    if internal_hit is None:
        for nm in name_mentions:
            c = classify(nm)
            if c:
                internal_hit = (c[0], c[1], "name_mention")
                internal_display = nm
                result["reasons"].append(f"name mention '{nm}' -> internal ({c[1]})")
                break

    if internal_hit is None:
        return result  # no internal party — graceful degradation

    internal_slug, relationship, signal = internal_hit
    result["present"] = True
    result["relationship_type"] = relationship
    result["internal_slug"] = internal_slug
    result["internal_display"] = internal_display
    result["signal"] = signal

    # --- Counterpart: the strongest NON-internal person -----------------
    # Prefer an external participant email's local-part name, else a filename
    # person who is NOT the internal party, else a non-internal speaker.
    #
    # Robustness: a filename person blob may glue a name to a host/company
    # token ("Jane Doe Acme"). We try the full string AND progressive
    # sub-spans (dropping trailing tokens) so a registered collaborator inside
    # the blob is still detected. The first sub-span that classifies internal
    # (and is NOT the primary internal party) wins as a collaborator
    # counterpart; otherwise the full blob is kept as an external counterpart.
    def _classify_name_or_subspan(name: str) -> tuple[str, str] | None:
        c0 = classify(name)
        if c0 is not None:
            return c0
        toks = name.split()
        # Try leading sub-spans of length 3,2 (drop trailing host/company tokens).
        for span in (3, 2):
            if len(toks) > span:
                c1 = classify(" ".join(toks[:span]))
                if c1 is not None:
                    return c1
        return None

    counterpart_display: str | None = None
    counterpart_slug: str | None = None
    counterpart_is_collab = False

    for nm in persons_fn + speakers:
        if not nm:
            continue
        c = _classify_name_or_subspan(nm)
        if c is None:
            counterpart_display = nm  # genuine external party
            break
        # Person is internal too (e.g. two collaborators). If it is NOT the
        # primary internal party, treat as a collaborator counterpart and use
        # the REGISTRY slug (not the raw filename blob) as the routing slug.
        if c[0] != internal_slug:
            counterpart_display = nm
            counterpart_slug = c[0]
            counterpart_is_collab = True
            break

    if counterpart_display is None and external_emails:
        counterpart_display = external_emails[0].rsplit("@", 1)[0]

    result["counterpart_display"] = counterpart_display
    result["counterpart_slug"] = counterpart_slug
    result["counterpart_is_collaborator"] = counterpart_is_collab
    return result


def infer_entities(
    filename_original: str,
    gemini_result: dict | None = None,
    file_path: "Path | None" = None,
    forced_author: str | None = None,
    forced_subject: str | None = None,
) -> dict:
    """Three-pass entity discovery: filename evidence + content evidence + reconciliation.

    Args:
        filename_original: Filename AS STORED on disk (NOT normalized).
        gemini_result: Optional output from extract_local_video_via_gemini.
                      If None, decision relies only on filename.
        file_path: Optional Path to the file. When provided AND non-video,
                   parse_local_content_evidence reads transcript headers
                   (Source:, Participants:, [MEET-NNNN]) for bucket hints —
                   STORY-MCE-INGEST-ROBUSTNESS AC-4 + AC-7.
        forced_author: Optional HARD override (from CLI --author). When set,
                   it short-circuits ALL author heuristics — the slugified
                   value becomes entity_author with high confidence + ROUTE.
                   STORY-ONDA1-author-routing.
        forced_subject: Optional HARD override (from CLI --subject). Same
                   precedence semantics as forced_author, for the subject.

    Returns:
        Dict with:
          - entity_author: str | None — slug of the presenter (Jane Doe -> jane-doe)
          - entity_subject: str | None — slug of the main subject (Widget -> widget)
          - cross_references: list[str] — other entities mentioned (not author/subject)
          - confidence: "high" | "medium" | "low"
          - verdict: "ROUTE" | "REVIEW" | "BLOCK"
          - reasoning: str — human-readable explanation
          - evidence: dict — raw inputs for audit
          - bucket_hint: str | None — "business"/"external" hint from local content evidence
          - bucket_hint_reasons: list[str] — provenance trail

    Decision tree:
        HIGH   = filename person + content subject confirmed + speaker matches
        MEDIUM = filename has person OR content has subject (but not both)
        LOW    = only filename, no content, ambiguous
        BLOCK  = no person AND no subject identifiable
    """
    fn_evidence = parse_filename_evidence(filename_original)
    cn_evidence = parse_content_evidence(gemini_result)
    local_evidence = parse_local_content_evidence(file_path=file_path, filename=filename_original)

    # STORY-MCE-FOUNDER-ROUTING: detect internal/founder party across all
    # evidence sources BEFORE reconciliation. Surfaced on the decision dict so
    # decide_destination can override the person->external default.
    internal_party = detect_internal_party(fn_evidence, cn_evidence, local_evidence)

    # PASS 3: reconcile
    author_candidate = None
    subject_candidate = None
    cross_refs = []

    # STORY-ONDA1-author-routing: track WHY we picked the author so confidence
    # / verdict can be promoted when a known external expert was matched.
    author_via_known_external = False

    # Author selection precedence:
    #   1. Gemini high/medium-confidence speaker (visual/content signal).
    #   2. KNOWN EXTERNAL EXPERT among filename persons — parenthetical
    #      candidates first, then bare title-word candidates. This is the
    #      Onda-1 fix: "100M Playbook Pricing (Alex Hormozi)" yields persons
    #      ["Playbook Pricing", "Alex Hormozi"]; the positional default would
    #      pick the FAKE "Playbook Pricing". Consulting external_people lets
    #      the REAL author "Alex Hormozi" win because she resolves to a known
    #      agents/external/ slug and "Playbook Pricing" does not.
    #   3. Positional fallback: first person in filename (legacy behaviour).
    if cn_evidence["top_speaker"] and cn_evidence["speaker_confidence"] in {"high", "medium"}:
        author_candidate = cn_evidence["top_speaker"]
    elif fn_evidence["persons"]:
        try:
            from engine.intelligence.pipeline.external_people import (
                classify as _classify_external,
            )
        except Exception:
            _classify_external = None  # type: ignore[assignment]

        if _classify_external is not None:
            # Parenthetical persons outrank title-word persons (parens bias).
            paren_persons = fn_evidence.get("persons_in_parens", []) or []
            bare_persons = [p for p in fn_evidence["persons"] if p not in paren_persons]
            for cand in [*paren_persons, *bare_persons]:
                if _classify_external(cand) is not None:
                    author_candidate = cand
                    author_via_known_external = True
                    break

        # No known external expert matched — positional fallback (legacy).
        if author_candidate is None:
            author_candidate = fn_evidence["persons"][0]

    # Subject: prefer Gemini subject (mention_count > threshold), else company from filename
    if cn_evidence["top_subject"] and cn_evidence["subject_mention_count"] >= 3:
        subject_candidate = cn_evidence["top_subject"]
    elif fn_evidence["companies"]:
        # FILENAME-ONLY HEURISTIC for subject discovery:
        # When the filename has multiple companies, the REPEATED token is
        # usually a tag/cross-ref/host (e.g. "Acme" repeated 2x = the host
        # company), and the UNIQUE token is the actual subject.
        # Example: "Acme + Widget - ... - Acme" → subject=Widget
        # because Acme appears 2x (host tag) and Widget 1x (real topic).

        # Use stem to count raw occurrences (case-insensitive)
        stem_lower = fn_evidence["raw_stem"].lower()
        company_counts = []
        for fc in fn_evidence["companies"]:
            # Count whole-word occurrences in stem
            import re as _re

            cnt = len(_re.findall(rf"\b{_re.escape(fc.lower())}\b", stem_lower))
            company_counts.append((fc, cnt))

        # Prefer company that appears in Gemini content entities (strongest signal)
        content_company_names = {
            e.get("name", "").lower() for e in cn_evidence["all_entities"] if isinstance(e, dict)
        }
        for fc, _cnt in company_counts:
            if fc.lower() in content_company_names:
                subject_candidate = fc
                break

        if not subject_candidate:
            # No Gemini hint — prefer UNIQUE companies (count==1) over repeated ones,
            # because repeated tokens in filenames are usually tags/hosts.
            unique = [fc for fc, cnt in company_counts if cnt == 1]
            repeated = [fc for fc, cnt in company_counts if cnt > 1]

            if unique:
                # Pick last unique (often the "more specific" one in filenames
                # like "Host + Topic" where Topic comes second)
                subject_candidate = unique[-1] if len(unique) > 1 else unique[0]
            elif repeated:
                # Everyone repeats — fall back to first
                subject_candidate = repeated[0]
            else:
                subject_candidate = fn_evidence["companies"][0]

    # Cross-references: filename companies not chosen as subject + filename persons not chosen as author
    for fc in fn_evidence["companies"]:
        if subject_candidate and fc.lower() == subject_candidate.lower():
            continue
        cross_refs.append(fc)
    for fp in fn_evidence["persons"]:
        if author_candidate and fp.lower() == author_candidate.lower():
            continue
        cross_refs.append(fp)

    # Verdict + confidence
    has_author = author_candidate is not None
    has_subject = subject_candidate is not None
    speaker_visually_confirmed = (
        cn_evidence["top_speaker"] and cn_evidence["speaker_confidence"] == "high"
    )
    subject_confirmed_in_content = cn_evidence["top_subject"] is not None

    if has_author and has_subject and (speaker_visually_confirmed or subject_confirmed_in_content):
        confidence = "high"
        verdict = "ROUTE"
        reasoning = (
            f"Author '{author_candidate}' + subject '{subject_candidate}' both identified. "
            f"Speaker visual confirmation: {speaker_visually_confirmed}. "
            f"Subject content confirmation: {subject_confirmed_in_content}."
        )
    elif has_author and has_subject:
        confidence = "medium"
        verdict = "ROUTE"
        reasoning = (
            f"Author '{author_candidate}' + subject '{subject_candidate}' from filename only. "
            f"No Gemini visual confirmation — route with medium confidence."
        )
    elif has_subject or has_author:
        confidence = "low"
        verdict = "REVIEW"
        reasoning = (
            f"Partial identification: author={author_candidate}, subject={subject_candidate}. "
            f"Flag for human review."
        )
    else:
        confidence = "low"
        verdict = "BLOCK"
        reasoning = "No entity author OR subject identified from filename or content."

    # STORY-ONDA1-author-routing: when the author was matched against a KNOWN
    # external expert (agents/external/<slug> or partners-registry), that is a
    # strong identity signal. Promote a low/REVIEW author-only decision so it
    # ROUTEs to external/<slug>/ instead of stalling in human-review limbo.
    if author_via_known_external and confidence == "low":
        confidence = "medium"
        if verdict in ("REVIEW", "BLOCK"):
            verdict = "ROUTE"
        reasoning += (
            f" | known-external author match: '{author_candidate}' resolves to a "
            f"registered external expert -> route external (medium confidence)"
        )

    # STORY-MCE-INGEST-ROBUSTNESS AC-4/AC-7: promote confidence when local
    # content evidence corroborates the decision, and expose bucket_hint
    # so decide_destination can route business calls without person tokens.
    if local_evidence.get("bucket_confidence") in ("high", "medium") and confidence == "low":
        confidence = "medium"
        reasoning += (
            f" | local-content boost: {local_evidence.get('bucket_hint')} "
            f"({local_evidence.get('bucket_confidence')})"
        )
        if verdict == "BLOCK" and local_evidence.get("bucket_hint") == "business":
            verdict = "REVIEW"
            reasoning += " | local evidence rescued from BLOCK to REVIEW"

    # STORY-MCE-FOUNDER-ROUTING: when an internal/founder party is present the
    # material is a BUSINESS relationship. Promote a BLOCK/low decision out of
    # the dead-zone so it routes (decide_destination handles the bucket), and
    # annotate the reasoning trail. We do NOT mutate author/subject here — the
    # counterpart slug is chosen in decide_destination from internal_party.
    if internal_party.get("present"):
        rel = internal_party.get("relationship_type")
        if confidence == "low":
            confidence = "medium"
        if verdict == "BLOCK":
            verdict = "ROUTE"
        reasoning += (
            f" | founder-in-call: internal party "
            f"'{internal_party.get('internal_display')}' present "
            f"(signal={internal_party.get('signal')}, relationship={rel}) "
            f"-> business"
        )

    # STORY-ONDA1-author-routing: CLI --author / --subject HARD override.
    # HIGHEST PRECEDENCE — set AFTER every heuristic so an explicit human
    # decision always wins. We override the chosen candidate(s) and force a
    # high-confidence ROUTE, because a human naming the author is the strongest
    # possible signal. Makes real the dead recommendation at
    # ingest-with-entity-discovery.py:1028 ("provide --author or --subject").
    if forced_author or forced_subject:
        forced_bits = []
        if forced_author:
            author_candidate = forced_author
            has_author = True
            forced_bits.append(f"author='{forced_author}'")
        if forced_subject:
            subject_candidate = forced_subject
            has_subject = True
            forced_bits.append(f"subject='{forced_subject}'")
        confidence = "high"
        verdict = "ROUTE"
        reasoning += f" | CLI HARD override: {', '.join(forced_bits)} (operator-supplied)"

    return {
        "entity_author": _slugify(author_candidate) if author_candidate else None,
        "entity_author_display": author_candidate,
        "entity_subject": _slugify(subject_candidate) if subject_candidate else None,
        "entity_subject_display": subject_candidate,
        "cross_references": [_slugify(c) for c in cross_refs],
        "cross_references_display": cross_refs,
        "confidence": confidence,
        "verdict": verdict,
        "reasoning": reasoning,
        "bucket_hint": local_evidence.get("bucket_hint"),
        "bucket_hint_confidence": local_evidence.get("bucket_confidence"),
        "bucket_hint_reasons": local_evidence.get("reasons", []),
        # Founder-in-call routing signal (STORY-MCE-FOUNDER-ROUTING).
        "internal_party_present": internal_party.get("present", False),
        "relationship_type": internal_party.get("relationship_type"),
        "internal_party_slug": internal_party.get("internal_slug"),
        "internal_party_signal": internal_party.get("signal"),
        "counterpart_display": internal_party.get("counterpart_display"),
        "counterpart_slug": internal_party.get("counterpart_slug"),
        "counterpart_is_collaborator": internal_party.get(
            "counterpart_is_collaborator", False
        ),
        "internal_party_reasons": internal_party.get("reasons", []),
        "evidence": {
            "filename": fn_evidence,
            "content": cn_evidence,
            "local": local_evidence,
        },
    }


def validate_entity_classification(
    parent_entity_slug: str,
    files: list[Path],
) -> dict:
    """Cross-validate that filenames agree with the parent directory's entity slug.

    Entity Discovery (Phase 2): When a file lives in
    `inbox/business/acme/misc/Acme-Widget-Parte1.txt`, the parent slug
    is "acme" — but the FILENAME suggests the subject is actually Widget
    (and possibly the author is Jane Doe). This function detects that
    divergence.

    Args:
        parent_entity_slug: Slug derived from the parent inbox directory name.
        files: List of Path objects (the batch's files).

    Returns:
        Dict with:
          - parent_slug: str
          - filename_inferences: list[dict] — one per file
          - divergence_detected: bool
          - dominant_subject: str | None — most common subject across files
          - dominant_author: str | None — most common author across files
          - mismatch_count: int — how many files diverge from parent
          - recommendation: "PROCEED" | "REVIEW" | "RECLASSIFY"
    """
    from collections import Counter

    inferences = []
    subject_votes: Counter[str] = Counter()
    author_votes: Counter[str] = Counter()
    mismatch_count = 0

    for f in files:
        # Use only filename (no path), so we test what disk shows
        fn_evidence = parse_filename_evidence(f.name)
        decision = infer_entities(f.name, gemini_result=None)

        # Slugify parent for comparison
        parent_slug_lower = parent_entity_slug.lower()
        subj = decision.get("entity_subject")
        author = decision.get("entity_author")

        # Mismatch if subject exists and != parent_slug
        is_mismatch = bool(subj and subj != parent_slug_lower)
        if is_mismatch:
            mismatch_count += 1

        if subj:
            subject_votes[subj] += 1
        if author:
            author_votes[author] += 1

        inferences.append(
            {
                "file": f.name,
                "filename_author": decision.get("entity_author"),
                "filename_subject": decision.get("entity_subject"),
                "filename_cross_refs": decision.get("cross_references", []),
                "mismatch_with_parent": is_mismatch,
                "persons_in_filename": fn_evidence.get("persons", []),
                "companies_in_filename": fn_evidence.get("companies", []),
            }
        )

    dominant_subject = subject_votes.most_common(1)[0][0] if subject_votes else None
    dominant_author = author_votes.most_common(1)[0][0] if author_votes else None
    divergence_detected = mismatch_count > 0

    # Recommendation
    if not divergence_detected:
        recommendation = "PROCEED"
    elif mismatch_count >= len(files) // 2 + 1:
        # Majority of files disagree with parent → strong signal to reclassify
        recommendation = "RECLASSIFY"
    else:
        recommendation = "REVIEW"

    return {
        "parent_slug": parent_entity_slug,
        "filename_inferences": inferences,
        "divergence_detected": divergence_detected,
        "dominant_subject": dominant_subject,
        "dominant_author": dominant_author,
        "mismatch_count": mismatch_count,
        "total_files": len(files),
        "recommendation": recommendation,
    }


def collect_batchable_files(person_dir: Path) -> list[Path]:
    """Recursively collect all batchable files under a person directory.

    Walks ``{person_dir}/{type}/`` subdirectories. Includes only files
    with extensions in ``BATCHABLE_EXTENSIONS``. Skips dotfiles,
    ``.ref.yaml``, and ``SKIP_NAMES``.

    Returns:
        Sorted list of absolute Paths.
    """
    files: list[Path] = []
    if not person_dir.is_dir():
        return files

    for f in person_dir.rglob("*"):
        if not f.is_file():
            continue
        if f.name in SKIP_NAMES:
            continue
        if f.name.startswith("."):
            continue
        if f.name.endswith(".ref.yaml"):
            continue
        if f.suffix.lower() not in BATCHABLE_EXTENSIONS:
            continue
        files.append(f.resolve())

    return sorted(files)


def _extract_batch_number(batch_id: str) -> int:
    """Extract the numeric portion from a batch ID.

    Examples::

        'BATCH-128-JH' -> 128
        'BATCH-001'    -> 1
        'BATCH-2025'   -> 2025
    """
    match = re.search(r"BATCH-(\d+)", batch_id)
    if match:
        return int(match.group(1))
    return 0


# ---------------------------------------------------------------------------
# REGISTRY (load / save / bootstrap)
# ---------------------------------------------------------------------------


def _try_flock(f: object, operation: int) -> None:
    """Attempt fcntl.flock; no-op on platforms without fcntl (Windows)."""
    try:
        import fcntl

        fcntl.flock(f.fileno(), operation)  # type: ignore[union-attr]
    except (ImportError, AttributeError, OSError):
        pass  # Non-Unix or virtual file; skip locking


def load_or_init_registry() -> dict:
    """Load ``BATCH-REGISTRY.json`` or create it via bootstrap.

    On first run, scans existing batch JSON logs to seed the registry
    so that previously-batched files are not re-processed.

    MCE-2.5: auto-prunes entries whose ``file_path`` no longer exists on
    disk. Without this, deleted/moved files keep blocking re-batching
    forever. Legacy entries (``legacy=True``, filename-only keys) are
    preserved because we cannot validate them against the filesystem.
    """
    if BATCH_REGISTRY_PATH.exists():
        try:
            text = BATCH_REGISTRY_PATH.read_text(encoding="utf-8")
            data = json.loads(text)
            if isinstance(data, dict) and "version" in data:
                _prune_stale_entries(data)
                return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Corrupt registry, bootstrapping fresh: %s", exc)

    return _bootstrap_registry()


def _prune_stale_entries(registry: dict) -> int:
    """Drop registry entries whose absolute path no longer exists.

    Returns the number of entries removed. Legacy entries (key starting
    with ``legacy:``) are kept because they are filename-only and not
    backed by an absolute path.
    """
    files = registry.get("files")
    if not isinstance(files, dict):
        return 0
    removed = 0
    for key in list(files):
        if key.startswith("legacy:"):
            continue
        # Absolute-path keys only. A missing file means the registry is stale.
        try:
            if not Path(key).exists():
                del files[key]
                removed += 1
        except OSError:
            # Symlink loops or permission errors → leave as-is, conservative.
            continue
    if removed:
        logger.info("BATCH-REGISTRY auto-pruned %d stale entries", removed)
    return removed


def _bootstrap_registry() -> dict:
    """Scan existing batch-logs to create the initial registry."""
    registry: dict = {
        "version": 1,
        "updated_at": _now_iso(),
        "next_batch_number": 1,
        "files": {},
        "batches": {},
    }

    if not BATCH_JSON_DIR.exists():
        return registry

    max_num = 0
    for json_file in sorted(BATCH_JSON_DIR.glob("BATCH-*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        batch_id = data.get("batch_id", "")
        source = data.get("source", "")
        source_name = data.get("source_name", "")

        num = _extract_batch_number(batch_id)
        if num > max_num:
            max_num = num

        # Register files from this batch (legacy: filenames only, not full paths).
        files_processed = data.get("files_processed", [])
        if not isinstance(files_processed, list):
            # Some old batches store file count as int, not file list.
            files_processed = []
        for filename in files_processed:
            key = f"legacy:{filename}"
            registry["files"][key] = {
                "batch_id": batch_id,
                "batched_at": data.get("generated_at", ""),
                "source_name": source_name,
                "legacy": True,
            }

        registry["batches"][batch_id] = {
            "source_name": source_name,
            "source_code": source,
            "file_count": data.get("files_count", 0),
            "created_at": data.get("generated_at", ""),
            "status": data.get("status", "UNKNOWN"),
        }

    registry["next_batch_number"] = max_num + 1
    return registry


def save_registry(registry: dict) -> None:
    """Write the registry to disk with file locking."""
    BATCH_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    registry["updated_at"] = _now_iso()

    try:
        with open(BATCH_REGISTRY_PATH, "w", encoding="utf-8") as f:
            _try_flock(f, 2)  # LOCK_EX
            json.dump(registry, f, indent=2, ensure_ascii=False, default=str)
            f.flush()
            _try_flock(f, 8)  # LOCK_UN
    except ImportError:
        # fcntl not available (Windows) -- write without locking
        BATCH_REGISTRY_PATH.write_text(
            json.dumps(registry, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )


def _is_file_batched(registry: dict, file_path: Path) -> bool:
    """Check if file is in registry AND its batch JSON exists in disk.

    MCE-13.8 Bug I: prior version only checked registry, leading to phantom
    "batched" state when registry entry exists but batch JSON was never written
    (e.g., interrupted process, manual cleanup).
    """
    abs_str = str(file_path)
    files = registry.get("files", {})

    entry = None
    if abs_str in files:
        entry = files[abs_str]
    else:
        # Check against legacy entries by filename stem.
        stem = file_path.stem
        for prefix in (f"legacy:{stem}", f"legacy:{file_path.name}"):
            if prefix in files:
                entry = files[prefix]
                break

    if entry is None:
        return False

    # MCE-13.8: verify the batch JSON actually exists in disk
    batch_id = entry.get("batch_id")
    source_name = entry.get("source_name", "")
    if not batch_id:
        return False  # malformed entry, treat as not batched

    # Construct expected batch JSON path and try candidate locations.
    # ARTIFACTS is module-level (engine.paths or fallback) — always safe to use.
    batches_root = ARTIFACTS / "batches"
    candidates: list[Path] = [
        batches_root / source_name / f"{batch_id}.json",
        batches_root / f"{batch_id}.json",
    ]
    # Also glob partial matches in the source_name subdir (e.g. batch_id prefix)
    source_dir = batches_root / source_name
    if source_dir.exists():
        candidates.extend(source_dir.glob(f"{batch_id}*.json"))

    if any(c.exists() for c in candidates):
        return True

    # Registry says batched but no JSON found in disk — phantom entry
    logger.warning(
        "_is_file_batched: phantom entry for %s (batch_id=%s, source=%s) — "
        "registry says batched but no JSON in disk. Treating as NOT batched.",
        file_path,
        batch_id,
        source_name,
    )
    return False


def register_files(
    registry: dict,
    batch_id: str,
    entity_slug: str,
    source_code: str,
    file_paths: list[str],
) -> None:
    """Add files to the registry's files dict and batches dict.

    Mutates *registry* in-place. Caller is responsible for saving.
    """
    now = _now_iso()

    for fp in file_paths:
        registry["files"][fp] = {
            "batch_id": batch_id,
            "batched_at": now,
            "source_name": entity_slug,
        }

    registry["batches"][batch_id] = {
        "source_name": entity_slug,
        "source_code": source_code,
        "file_count": len(file_paths),
        "created_at": now,
        "status": "CREATED",
    }


# ---------------------------------------------------------------------------
# BATCH FILE WRITERS
# ---------------------------------------------------------------------------


def write_batch_json(
    batch_id: str,
    source_code: str,
    entity_slug: str,
    file_paths: list[str],
    total_size: int,
) -> Path:
    """Write ``BATCH-XXX-YY.json`` to ``.claude/mission-control/batch-logs/``.

    Format matches existing batch JSONs for backward compatibility.
    """
    BATCH_JSON_DIR.mkdir(parents=True, exist_ok=True)

    json_filename = f"{batch_id}.json"
    json_path = BATCH_JSON_DIR / json_filename

    # Avoid collision: if file already exists, increment
    attempts = 0
    while json_path.exists() and attempts < 10:
        num = _extract_batch_number(batch_id)
        num += 1
        batch_id = f"BATCH-{num:03d}-{source_code}"
        json_filename = f"{batch_id}.json"
        json_path = BATCH_JSON_DIR / json_filename
        attempts += 1

    data = {
        "batch_id": batch_id,
        "source": source_code,
        "source_name": _humanize_source_name(entity_slug),
        "created_at": datetime.now(UTC).strftime("%Y-%m-%d"),
        "md_file": f"{batch_id.split('-' + source_code)[0]}.md"
        if source_code
        else f"{batch_id}.md",
        "files_processed": [Path(f).name for f in file_paths],
        "files_count": len(file_paths),
        "themes": [],
        "dna_metrics": {
            "filosofias": 0,
            "modelos_mentais": 0,
            "heuristicas": 0,
            "frameworks": 0,
            "metodologias": 0,
        },
        "frameworks_extracted": [],
        "total_elements": 0,
        "status": "CREATED",
        "cascading_executed": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "auto_created": True,
    }

    json_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    return json_path


def write_batch_md(
    batch_id: str,
    source_code: str,
    entity_slug: str,
    file_paths: list[str],
    total_size: int,
) -> Path:
    """Write ``BATCH-XXX.md`` to ``logs/batches/`` (dual-location per REGRA #8).

    Generates a pre-extraction batch log compatible with the MCE pipeline.
    Full MCE progressive log is generated by the pipeline orchestrator using
    ``core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md``.
    """
    BATCH_MD_DIR.mkdir(parents=True, exist_ok=True)

    # MD filename uses the numeric part only (e.g., BATCH-130.md)
    num = _extract_batch_number(batch_id)
    md_filename = f"BATCH-{num:03d}.md"
    md_path = BATCH_MD_DIR / md_filename

    human_name = _humanize_source_name(entity_slug)
    now_date = datetime.now(UTC).strftime("%Y-%m-%d")
    now_full = datetime.now(UTC).isoformat()

    file_list_lines = "\n".join(
        f"| {i + 1} | `{Path(f).name}` | pending |" for i, f in enumerate(file_paths)
    )

    content = f"""# {batch_id}

> **Auto-generated by batch_auto_creator.py**
> **Date:** {now_date}
> **Status:** CREATED (pre-extraction)
> **Template:** MCE-PIPELINE-LOG-TEMPLATE.md v1.0.0

---

## META

| Field | Value |
|-------|-------|
| Batch ID | {batch_id} |
| Source | {source_code} ({human_name}) |
| Entity slug | {entity_slug} |
| Files | {len(file_paths)} |
| Total Size | {total_size:,} bytes |
| Pipeline status | CLASSIFIED |
| Auto-Created | Yes |
| Generated At | {now_full} |

---

## 1. CLASSIFICATION -- Atlas [@] COMPLETO

**Decision:** external @ auto-created
**Routing:** AUTO (batch_auto_creator)

---

## 2. ORGANIZATION -- Atlas [@] COMPLETO

| Field | Value |
|-------|-------|
| Entity detected | {entity_slug} |
| Batch ID | {batch_id} |
| Files in batch | {len(file_paths)} |

---

## EXTRACTION METRICS (populated by pipeline)

### DNA Layers (5-layer)

| Layer | Count |
|-------|-------|
| Filosofias | 0 |
| Modelos Mentais | 0 |
| Heuristicas | 0 |
| Frameworks | 0 |
| Metodologias | 0 |
| **Total** | **0** |

### MCE Layers (populated by MCE pipeline)

| Layer | Count |
|-------|-------|
| Behavioral Patterns | 0 |
| Values Hierarchy | 0 |
| Voice DNA phrases | 0 |

> Run `/pipeline-mce {entity_slug}` to execute full MCE extraction.
> Full progressive log: `core/templates/logs/MCE-PIPELINE-LOG-TEMPLATE.md`

---

## ARQUIVOS PROCESSADOS

| # | Arquivo | Tema |
|---|---------|------|
{file_list_lines}

---

## DESTINO DO CONHECIMENTO

> Pre-extraction placeholder destinations. Pipeline orchestrator updates this
> section post-extraction with the actual files touched.
> C-17 fix (2026-05-12): batches now declare expected destinations upfront
> so post_batch_cascading + validate_cascading_integrity can verify delivery.

🤖 AGENTES A ALIMENTAR
   • {entity_slug}/MEMORY.md
   • {entity_slug}/DNA-CONFIG.yaml

📘 PLAYBOOKS IMPACTADOS
   (pending — populated by pipeline orchestrator post-extraction)

🧬 DNAs ENRIQUECIDOS
   • {entity_slug}/voice-dna.yaml
   • {entity_slug}/behavioral-patterns.yaml

📁 DOSSIERS
   • dossier-{entity_slug}.md

---

*Auto-created by batch_auto_creator.py at {now_full}*
"""

    md_path.write_text(content, encoding="utf-8")
    return md_path


# ---------------------------------------------------------------------------
# G10 (2026-05-13): COPY BATCH FILES TO ARTIFACTS DIRECTORY
# ---------------------------------------------------------------------------
#
# cmd_process_batch (engine/intelligence/pipeline/mce/orchestrate.py) discovers
# documents from ``ARTIFACTS / "batches" / slug``. Previously batch_auto_creator
# wrote BATCH-*.md/json but did not COPY the actual files there, so the FSM
# advanced to "batching" but cmd_process_batch found zero documents and bailed.
#
# G10 fix: after writing the batch logs, copy each batched file (with metadata
# preserved via shutil.copy2) to ``ARTIFACTS / "batches" / {slug}``. Idempotent:
# if a file with the same SHA256 already exists at the destination, skip the
# copy. Inbox stays intact (copy, not move) so /resume + re-ingestion remain
# possible.


def _sha256_file(path: Path, *, chunk_size: int = 65536) -> str:
    """Return the SHA256 hex digest of ``path``. Empty string on failure."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                buf = f.read(chunk_size)
                if not buf:
                    break
                h.update(buf)
        return h.hexdigest()
    except OSError:
        return ""


def copy_batch_files_to_artifacts(
    entity_slug: str,
    file_paths: list[str],
) -> dict:
    """Copy each batch file into ``ARTIFACTS / "batches" / {slug}/`` (G10).

    Uses shutil.copy2 so timestamps + permissions are preserved. Idempotent:
    re-running with the same hashes is a no-op (counted as ``skipped``).
    Inbox source is never modified — this is a one-way copy.

    Args:
        entity_slug: Person/source slug (e.g. ``"jane-doe"``).
        file_paths: Absolute paths of files originally batched (from the
            knowledge/external/inbox/{slug}/ tree).

    Returns:
        Dict with ``dest_dir``, ``copied``, ``skipped``, ``failed`` (lists of
        filenames) so callers can include the result in batch logs.
    """
    dest_dir = ARTIFACTS / "batches" / entity_slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    skipped: list[str] = []
    failed: list[dict] = []

    for src_str in file_paths:
        src = Path(src_str)
        if not src.exists():
            failed.append({"file": src.name, "reason": "source not found"})
            continue

        dest = dest_dir / src.name

        # Idempotency check: if dest exists AND content matches, skip.
        if dest.exists():
            try:
                if dest.stat().st_size == src.stat().st_size:
                    src_hash = _sha256_file(src)
                    dst_hash = _sha256_file(dest)
                    if src_hash and src_hash == dst_hash:
                        skipped.append(src.name)
                        continue
            except OSError:
                # Stat failed — fall through to overwrite.
                pass

        try:
            shutil.copy2(str(src), str(dest))
            copied.append(src.name)
        except OSError as exc:
            failed.append({"file": src.name, "reason": str(exc)})
            logger.warning("G10: failed to copy %s -> %s: %s", src, dest, exc)

    return {
        "dest_dir": str(dest_dir),
        "copied": copied,
        "skipped": skipped,
        "failed": failed,
    }


# ---------------------------------------------------------------------------
# CASCADING
# ---------------------------------------------------------------------------


def emit_advance_trigger(
    batch_id: str,
    entity_slug: str,
    *,
    expected_state: str = "CLASSIFIED",
) -> Path | None:
    """Write ``<batch_id>.advance-trigger.json`` next to the batch JSON.

    Per @architect N3 sign-off (2026-05-13, conditions C-1 to C-6):

    - C-6a: ``schema_version: 1`` + ``expected_state`` recorded for state check.
    - C-6b: Sibling ``.consumed`` sentinel is checked by the listener.
    - C-3a: This file is the SOLE trigger for ``cmd_auto_advance``.
    - C-3c: Listener verifies FSM state ∈ {init, ingesting, batching} before spawn.

    Args:
        batch_id: BATCH-XXX-YY identifier.
        entity_slug: Slug of the source/person owning this batch.
        expected_state: FSM state the pipeline must be in. Default ``CLASSIFIED``.

    Returns:
        Path to the trigger file written, or ``None`` if write failed (logged).
    """
    BATCH_JSON_DIR.mkdir(parents=True, exist_ok=True)
    trigger_path = BATCH_JSON_DIR / f"{batch_id}.advance-trigger.json"

    payload = {
        "schema_version": 1,
        "status": "CLASSIFIED",
        "expected_state": expected_state,
        "slug": entity_slug,
        "batch_id": batch_id,
        "ts": _now_iso(),
        "ttl_hours": 24,
        "retry_count": 0,
    }

    try:
        trigger_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(
            "Emitted advance-trigger for %s (slug=%s) at %s",
            batch_id,
            entity_slug,
            trigger_path,
        )
        return trigger_path
    except OSError as exc:
        logger.warning("Failed to emit advance-trigger for %s: %s", batch_id, exc)
        return None


def trigger_cascading(md_path: Path) -> bool:
    """Invoke ``post_batch_cascading.py`` on a newly created batch.

    Returns True if cascading completed successfully, False otherwise.
    """
    try:
        from engine.intelligence.pipeline.post_batch_cascading import (
            process_batch_for_cascading,
        )

        process_batch_for_cascading(md_path)
        return True
    except ImportError:
        logger.debug("post_batch_cascading not available; skipping cascading")
        return False
    except Exception as exc:
        logger.warning("Cascading failed for %s: %s", md_path, exc)
        return False


def trigger_memory_enrichment(
    batch_id: str,
    entity_slug: str,
    file_paths: list[str],
) -> bool:
    """Invoke ``memory_enricher.enrich()`` with stub insights from this batch.

    Creates minimal Insight dicts (one per file) so the enricher can route
    them to the correct agents. Full insight extraction happens in Phase 4;
    this seeds the connection so enrichment can occur incrementally.

    Returns True if enrichment ran without errors, False otherwise.
    """
    try:
        from engine.intelligence.pipeline.memory_enricher import enrich

        insights = [
            {
                "person_slug": entity_slug,
                "chunk_id": f"{batch_id}:{Path(fp).stem}",
                "title": f"Batch file: {Path(fp).name}",
                "content": "",
                "tag": derive_source_code(entity_slug),
                "batch_id": batch_id,
                "path_raiz": fp,
            }
            for fp in file_paths
        ]
        result = enrich(insights)
        if result.get("errors"):
            logger.warning(
                "Memory enrichment had errors for %s: %s",
                batch_id,
                result["errors"],
            )
        return not result.get("errors")
    except ImportError:
        logger.debug("memory_enricher not available; skipping enrichment")
        return False
    except Exception as exc:
        logger.warning("Memory enrichment failed for %s: %s", batch_id, exc)
        return False


def trigger_workspace_sync() -> bool:
    """Invoke ``workspace_sync.sync()`` after batch creation and enrichment.

    Syncs validated business knowledge to the prescriptive workspace layer.
    Non-fatal: if workspace_sync is not importable or fails, batch creation
    still succeeds.

    Returns True if sync ran without errors, False otherwise.
    """
    try:
        from engine.intelligence.pipeline.workspace_sync import sync

        result = sync()
        if result.errors:
            logger.warning("Workspace sync had errors: %s", result.errors)
        return not result.errors
    except ImportError:
        logger.debug("workspace_sync not available; skipping workspace sync")
        return False
    except Exception as exc:
        logger.warning("Workspace sync failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# JSONL AUDIT LOG
# ---------------------------------------------------------------------------


def _log_scan_result(result: ScanResult, *, dry_run: bool = False) -> None:
    """Append one JSONL line to the auto-creator audit log."""
    try:
        AUTO_CREATOR_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": _now_iso(),
            "files_scanned": result.files_scanned,
            "files_already_batched": result.files_already_batched,
            "persons_scanned": result.persons_scanned,
            "batches_created": len(result.batches_created),
            "batch_ids": [b.batch_id for b in result.batches_created],
            "files_below_threshold": result.files_below_threshold,
            "dry_run": dry_run,
            "duration_ms": result.duration_ms,
        }
        with open(AUTO_CREATOR_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write auto-creator log", exc_info=True)


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------


def scan_and_create(
    *,
    dry_run: bool = False,
    buckets: list[str] | None = None,
    force: bool = False,
    scope_slug: str | None = None,
) -> ScanResult:
    """Scan organized inbox directories and create batches for unprocessed files.

    Args:
        dry_run: If True, report what would be created but do not write anything.
        buckets: Override ``SCAN_BUCKETS`` (for testing or future multi-bucket).
        force: If True, batch even if below ``MIN_FILES`` threshold (min 1 file).
        scope_slug: If provided, restrict the scan to the single inbox
            person-directory named ``scope_slug`` across all target buckets.
            When ``None`` (default) the full inbox is walked exactly as before
            (byte-for-byte backward compatible). When set, only
            ``inbox/{scope_slug}/`` is considered in each bucket; a slug dir
            absent from a bucket contributes nothing, and a slug absent from
            every bucket yields an empty :class:`ScanResult` without raising.
            Eliminates the global walk (and its phantom-entry log spam) for
            single-slug ingests (STORY-MCE-BATCH-SLUG-SCOPE).

    Returns:
        ScanResult describing all actions taken.
    """
    start_time = time.monotonic()
    registry = load_or_init_registry()
    target_buckets = buckets or SCAN_BUCKETS
    threshold = 1 if force else MIN_FILES

    result = ScanResult()

    for bucket in target_buckets:
        inbox_key = f"{bucket}_inbox"
        inbox_root = ROUTING.get(inbox_key)
        if inbox_root is None:
            logger.warning("No ROUTING key for %r, skipping", inbox_key)
            continue

        inbox_root = Path(inbox_root)
        if not inbox_root.exists():
            logger.debug("Inbox root does not exist: %s", inbox_root)
            continue

        # Collect person directories (first-level subdirs).
        # When ``scope_slug`` is set, restrict to that single dir so the scan
        # touches only the target slug's inbox instead of the whole inbox
        # (STORY-MCE-BATCH-SLUG-SCOPE). Default path (scope_slug is None) is
        # unchanged: walk every non-underscore person dir.
        if scope_slug is not None:
            scoped_dir = inbox_root / scope_slug
            person_dirs = (
                [scoped_dir]
                if scoped_dir.is_dir() and not scoped_dir.name.startswith("_")
                else []
            )
        else:
            person_dirs = sorted(
                d for d in inbox_root.iterdir() if d.is_dir() and not d.name.startswith("_")
            )
        result.persons_scanned += len(person_dirs)

        for person_dir in person_dirs:
            entity_slug = person_dir.name
            source_code = derive_source_code(entity_slug)

            # Collect all batchable files under this person.
            all_files = collect_batchable_files(person_dir)
            result.files_scanned += len(all_files)

            # Filter out already-batched files.
            unprocessed = [f for f in all_files if not _is_file_batched(registry, f)]
            already_batched = len(all_files) - len(unprocessed)
            result.files_already_batched += already_batched

            # Check threshold.
            if len(unprocessed) < threshold:
                if unprocessed:
                    result.files_below_threshold[entity_slug] = len(unprocessed)
                continue

            # ENTITY VALIDATION (Phase 2): cross-check that the parent
            # directory slug matches what the filenames suggest. If filenames
            # consistently disagree (e.g. parent=acme but all filenames
            # mention widget), log a misclassification warning so cascade can
            # flag for review instead of routing blindly.
            validation = validate_entity_classification(entity_slug, unprocessed)
            if validation["divergence_detected"]:
                logger.warning(
                    "Entity misclassification detected for parent=%s: "
                    "%d/%d files diverge. Dominant subject from filenames: %s. "
                    "Recommendation: %s",
                    entity_slug,
                    validation["mismatch_count"],
                    validation["total_files"],
                    validation["dominant_subject"],
                    validation["recommendation"],
                )

            # Partition using batch_governor (respects MAX_BATCH_SIZE=5).
            batches = partition_files(unprocessed, max_size=MAX_BATCH_SIZE)

            for batch_plan in batches:
                batch_files: list[str] = batch_plan["files"]
                batch_count: int = batch_plan["count"]
                batch_total_size: int = batch_plan.get("total_size", 0)

                if dry_run:
                    result.batches_created.append(
                        BatchResult(
                            batch_id=f"BATCH-{registry['next_batch_number']:03d}-{source_code}",
                            source_code=source_code,
                            source_name=entity_slug,
                            files=batch_files,
                            file_count=batch_count,
                            total_size_bytes=batch_total_size,
                            json_path="(dry-run)",
                            md_path="(dry-run)",
                            cascading_triggered=False,
                            created_at=_now_iso(),
                        )
                    )
                    registry["next_batch_number"] += 1
                    continue

                # Assign batch ID.
                batch_num = registry["next_batch_number"]
                batch_id = f"BATCH-{batch_num:03d}-{source_code}"

                # Collision check: if JSON file already exists, increment.
                collision_attempts = 0
                while (BATCH_JSON_DIR / f"{batch_id}.json").exists() and collision_attempts < 10:
                    batch_num += 1
                    batch_id = f"BATCH-{batch_num:03d}-{source_code}"
                    collision_attempts += 1

                registry["next_batch_number"] = batch_num + 1

                # Create JSON log.
                json_path = write_batch_json(
                    batch_id, source_code, entity_slug, batch_files, batch_total_size
                )

                # Create MD log (dual-location, REGRA #8).
                md_path = write_batch_md(
                    batch_id, source_code, entity_slug, batch_files, batch_total_size
                )

                # G10 (2026-05-13): copy batch files to ARTIFACTS/batches/{slug}/
                # so cmd_process_batch can discover them. Inbox stays intact.
                copy_result = copy_batch_files_to_artifacts(entity_slug, batch_files)
                logger.info(
                    "G10: %s -> copied=%d skipped=%d failed=%d",
                    copy_result["dest_dir"],
                    len(copy_result["copied"]),
                    len(copy_result["skipped"]),
                    len(copy_result["failed"]),
                )

                # Register files in registry.
                register_files(registry, batch_id, entity_slug, source_code, batch_files)

                # Emit auto-advance trigger marker [N3/G1, @architect C-1..C-6].
                # The pipeline_orchestrator hook listens for this marker and
                # spawns ``cmd_auto_advance`` as a detached subprocess.
                emit_advance_trigger(batch_id, entity_slug)

                # Trigger cascading (non-fatal if it fails).
                cascading_ok = trigger_cascading(md_path)

                # Trigger memory enrichment (non-fatal if it fails).
                trigger_memory_enrichment(batch_id, entity_slug, batch_files)

                # Trigger workspace sync (non-fatal if it fails).
                trigger_workspace_sync()

                result.batches_created.append(
                    BatchResult(
                        batch_id=batch_id,
                        source_code=source_code,
                        source_name=entity_slug,
                        files=batch_files,
                        file_count=batch_count,
                        total_size_bytes=batch_total_size,
                        json_path=str(json_path),
                        md_path=str(md_path),
                        cascading_triggered=cascading_ok,
                        created_at=_now_iso(),
                    )
                )

                logger.info(
                    "Created %s: %d files from %s (%s)",
                    batch_id,
                    batch_count,
                    entity_slug,
                    source_code,
                )

    # Save registry (skip in dry-run).
    if not dry_run:
        save_registry(registry)

    # Append to JSONL audit log.
    _log_scan_result(result, dry_run=dry_run)

    result.duration_ms = int((time.monotonic() - start_time) * 1000)
    return result


# ---------------------------------------------------------------------------
# STATUS COMMAND
# ---------------------------------------------------------------------------


def show_status() -> None:
    """Print registry statistics to stdout."""
    if not BATCH_REGISTRY_PATH.exists():
        print("No BATCH-REGISTRY.json found. Run scan_and_create() first.")
        return

    registry = load_or_init_registry()
    total_files = len(registry.get("files", {}))
    total_batches = len(registry.get("batches", {}))
    next_num = registry.get("next_batch_number", 0)
    updated = registry.get("updated_at", "never")
    legacy_count = sum(1 for v in registry.get("files", {}).values() if v.get("legacy"))

    print("BATCH-REGISTRY.json Status")
    print(f"  Total files registered:  {total_files}")
    print(f"  Legacy entries:          {legacy_count}")
    print(f"  New-style entries:       {total_files - legacy_count}")
    print(f"  Total batches:           {total_batches}")
    print(f"  Next batch number:       {next_num}")
    print(f"  Last updated:            {updated}")


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------


def main() -> int:
    """Parse CLI arguments and run the appropriate command."""
    parser = argparse.ArgumentParser(
        prog="batch_auto_creator",
        description="Automatic batch creator for the Pipeline Jarvis.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="scan",
        choices=["scan", "status"],
        help="Command to run (default: scan).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created, write nothing.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Batch even if below MIN_FILES threshold (min 1 file).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Set log level to DEBUG.",
    )

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    if args.command == "status":
        show_status()
        return 0

    result = scan_and_create(
        dry_run=args.dry_run,
        force=args.force,
    )

    # Print summary.
    prefix = "[DRY-RUN] " if args.dry_run else ""
    print(f"\n{prefix}Scan complete in {result.duration_ms}ms")
    print(f"  Persons scanned:    {result.persons_scanned}")
    print(f"  Files scanned:      {result.files_scanned}")
    print(f"  Already batched:    {result.files_already_batched}")
    print(f"  Batches created:    {len(result.batches_created)}")

    if result.batches_created:
        for b in result.batches_created:
            print(f"    {b.batch_id}: {b.file_count} files ({b.source_name})")

    if result.files_below_threshold:
        print("  Below threshold:")
        for person, count in result.files_below_threshold.items():
            print(f"    {person}: {count} files (need {MIN_FILES})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
