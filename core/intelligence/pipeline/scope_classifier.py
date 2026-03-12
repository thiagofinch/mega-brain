"""
scope_classifier.py -- Unified Content-Aware Bucket Classifier
===============================================================
Decides which knowledge bucket(s) a file belongs to using 6 independent
signal passes: path analysis, participant analysis, entity detection,
content type detection, cognitive patterns, and topic keywords.

Replaces the binary meeting-only routing (empresa/pessoal) with a
multi-bucket classifier that handles ALL file types entering the pipeline.

Integration model:
    File arrives -> scope_classifier.classify() -> ScopeDecision
                 -> inbox_organizer.organize_inbox() (within bucket)
                 -> pipeline_orchestrator.py (downstream processing)

Version: 1.0.0
Date: 2026-03-10
Spec: docs/plans/epic1-phase1.1-scope-classifier-spec.md
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import unicodedata
from dataclasses import dataclass, field

import yaml

from core.paths import (
    KNOWLEDGE_EXTERNAL,
    LOGS,
    ROOT,
    WORKSPACE,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SIGNAL WEIGHT CONSTANTS (Tuning Knobs)
# ---------------------------------------------------------------------------

# Signal 1: Path Analysis
PATH_INBOX_WEIGHT = 10
PATH_WORKSPACE_WEIGHT = 8

# Signal 2: Participant Analysis
PARTICIPANT_ORGANIZER = 5
PARTICIPANT_ATTENDEE = 2
PARTICIPANT_OWNER = 3
PARTICIPANT_EXTERNAL = 1
PARTICIPANT_ALL_INTERNAL = 5
PARTICIPANT_PERSONAL_MEETING = 5

# Signal 3: Entity Detection
ENTITY_EXPERT = 5
ENTITY_TEAM = 3
ENTITY_OWNER = 2

# Signal 4: Content Type Detection
CONTENT_COURSE = 8
CONTENT_MEETING = 6
CONTENT_PERSONAL = 8
CONTENT_TEMPLATE = 4

# Signal 5: Cognitive Patterns
COGNITIVE_FIRST_PERSON = 3
COGNITIVE_TEACHING = 4
COGNITIVE_DISCUSSION = 3

# Signal 6: Topic Keywords
TOPIC_COMPANY_KEYWORD = 3
TOPIC_EXPERT_MARKERS = 3
TOPIC_BUSINESS_MARKERS = 3

# Thresholds
CASCADE_THRESHOLD = 5
TEXT_SAMPLE_SIZE = 5000

# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------


@dataclass
class ClassificationContext:
    """Input context for scope classification.

    Attributes:
        text: File content (first N chars sampled by caller or internally).
        filename: Original filename (e.g., 'hormozi-course-01.txt').
        file_path: Absolute path (may hint at bucket via directory structure).
        participants: Email addresses of attendees (empty for non-meetings).
        organizer_email: Meeting organizer email (empty for non-meetings).
        title: Meeting title or document title.
        source_type_hint: Upstream hint like 'meeting', 'transcript', 'document'.
        metadata: Arbitrary key-value pairs from upstream callers.
    """

    text: str = ""
    filename: str = ""
    file_path: str = ""
    participants: list[str] = field(default_factory=list)
    organizer_email: str = ""
    title: str = ""
    source_type_hint: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class ScopeDecision:
    """Output of scope classification.

    Attributes:
        primary_bucket: The winning bucket ('external', 'business', 'personal').
        cascade_buckets: Additional buckets that also scored above threshold.
        confidence: How dominant the winner is (0.0 - 1.0).
        reasons: Human-readable justification trail.
        source_type: Detected source type ('meeting', 'course', 'document', etc.).
        detected_entities: Entity slugs found (e.g., ['alex-hormozi']).
        signals: Raw signal scores per pass for debugging.
    """

    primary_bucket: str = "external"
    cascade_buckets: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reasons: list[str] = field(default_factory=list)
    source_type: str = "unknown"
    detected_entities: list[str] = field(default_factory=list)
    signals: dict[str, object] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# LAZY-LOADED REGISTRIES (cached at module level)
# ---------------------------------------------------------------------------

_known_experts: set[str] | None = None
_known_team: dict[str, str] | None = None
_owner_aliases: list[str] | None = None
_owner_email: str | None = None
_company_domains: list[str] | None = None
_company_keywords: list[str] | None = None
_company_name: str | None = None

# DNA persons directory (source of truth for known experts)
_DNA_PERSONS_DIR = KNOWLEDGE_EXTERNAL / "dna" / "persons"

# ORGANOGRAM location (source of truth for known team members)
_ORGANOGRAM_PATH = WORKSPACE / "team" / "ORGANOGRAM.yaml"


def _load_known_experts() -> set[str]:
    """Load known expert slugs from DNA persons directory.

    Scans ``knowledge/external/dna/persons/`` for subdirectory names.
    Falls back to ENTITY_ALIASES from inbox_organizer as a secondary source.

    Returns:
        Set of kebab-case expert slugs.
    """
    global _known_experts
    if _known_experts is not None:
        return _known_experts

    experts: set[str] = set()

    # Primary: scan DNA persons directory
    if _DNA_PERSONS_DIR.exists():
        for entry in _DNA_PERSONS_DIR.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                experts.add(entry.name)

    # Secondary: add alias targets from inbox_organizer
    try:
        from core.intelligence.pipeline.inbox_organizer import ENTITY_ALIASES

        _company_kws = {k.strip().lower() for k in os.environ.get("MEGA_BRAIN_COMPANY_KEYWORDS", "").split(",") if k.strip()}
        for _alias, slug in ENTITY_ALIASES.items():
            # Only add slugs that look like person names (contain a hyphen)
            # and are not company names
            if "-" in slug and slug not in _company_kws:
                experts.add(slug)
    except ImportError:
        logger.debug("inbox_organizer not importable; skipping alias enrichment")

    _known_experts = experts
    return _known_experts


def _load_known_team() -> dict[str, str]:
    """Load known team members from ORGANOGRAM.yaml.

    Returns:
        Dict mapping normalized name (lowercase) to member ID.
        E.g., ``{'joao silva': 'JS001', 'maria santos': 'MS001'}``.
    """
    global _known_team
    if _known_team is not None:
        return _known_team

    team: dict[str, str] = {}

    if _ORGANOGRAM_PATH.exists():
        try:
            with open(_ORGANOGRAM_PATH, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            members = data.get("members", []) if isinstance(data, dict) else []
            for member in members:
                if not isinstance(member, dict):
                    continue
                name = member.get("nome", "")
                member_id = member.get("id", "")
                if name and member_id:
                    team[_normalize_name(name)] = member_id
        except Exception:
            logger.debug("Failed to parse ORGANOGRAM.yaml", exc_info=True)

    _known_team = team
    return _known_team


def _load_owner_aliases() -> list[str]:
    """Load owner name aliases from pipeline_router.get_owner_aliases().

    Returns:
        List of lowercase owner name aliases.
    """
    global _owner_aliases
    if _owner_aliases is not None:
        return _owner_aliases

    try:
        from core.intelligence.pipeline.pipeline_router import get_owner_aliases

        _owner_aliases = get_owner_aliases()
    except ImportError:
        _owner_aliases = []

    # Fallback: read directly from env if pipeline_router didn't provide
    if not _owner_aliases:
        owner_name = os.environ.get("MEGA_BRAIN_OWNER_NAME", "").strip()
        if owner_name:
            _owner_aliases = [owner_name.lower()]
            parts = owner_name.split()
            if len(parts) > 1:
                _owner_aliases.append(parts[0].lower())

    return _owner_aliases


def _load_owner_email() -> str:
    """Load owner email from environment.

    Returns:
        Lowercase owner email or empty string.
    """
    global _owner_email
    if _owner_email is not None:
        return _owner_email

    try:
        from core.intelligence.pipeline.pipeline_router import OWNER_EMAIL

        _owner_email = OWNER_EMAIL.lower().strip()
    except ImportError:
        _owner_email = os.environ.get("MEGA_BRAIN_OWNER_EMAIL", "").lower().strip()

    return _owner_email


def _load_company_domains() -> list[str]:
    """Load company domains from READ_AI_COMPANY_DOMAINS env var.

    Returns:
        List of lowercase company domain strings.
    """
    global _company_domains
    if _company_domains is not None:
        return _company_domains

    raw = os.environ.get("READ_AI_COMPANY_DOMAINS", "")
    _company_domains = [d.strip().lower() for d in raw.split(",") if d.strip()]
    return _company_domains


def _load_company_keywords() -> list[str]:
    """Load company keywords from READ_AI_COMPANY_KEYWORDS env var.

    Returns:
        List of lowercase company keyword strings.
    """
    global _company_keywords
    if _company_keywords is not None:
        return _company_keywords

    raw = os.environ.get("READ_AI_COMPANY_KEYWORDS", "")
    _company_keywords = [k.strip().lower() for k in raw.split(",") if k.strip()]
    return _company_keywords


def _load_company_name() -> str:
    """Load company name from READ_AI_COMPANY_NAME env var.

    Returns:
        Lowercase company name or empty string.
    """
    global _company_name
    if _company_name is not None:
        return _company_name

    _company_name = os.environ.get("READ_AI_COMPANY_NAME", "").lower().strip()
    return _company_name


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------


def _normalize_name(name: str) -> str:
    """Normalize a name for matching: lowercase, strip accents.

    Uses ``unicodedata.normalize('NFKD')`` to handle accented characters
    (e.g., 'Nathalia' matches 'nathalia').

    Args:
        name: Raw name string.

    Returns:
        Lowercase, accent-stripped name.
    """
    normalized = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in normalized if not unicodedata.combining(c))
    return stripped.lower().strip()


def _email_domain(email: str) -> str:
    """Extract the domain from an email address.

    Args:
        email: Email address string.

    Returns:
        Lowercase domain part, or empty string if invalid.
    """
    if not email or "@" not in email:
        return ""
    # Filter Google Calendar group/resource addresses
    if "@resource.calendar.google.com" in email:
        return ""
    if "@group.calendar.google.com" in email:
        return ""
    return email.rsplit("@", 1)[1].lower()


def _email_matches_company(email: str) -> bool:
    """Check if an email belongs to a known company domain.

    Args:
        email: Email address to check.

    Returns:
        True if the email domain matches any company domain.
    """
    domain = _email_domain(email)
    if not domain:
        return False
    return domain in _load_company_domains()


# ---------------------------------------------------------------------------
# SIGNAL 1: PATH ANALYSIS
# ---------------------------------------------------------------------------


def _signal_path(file_path: str, scores: dict[str, int], reasons: list[str], signals: dict[str, object]) -> None:
    """Analyze file path to determine bucket affinity.

    Mutually exclusive: exactly one sub-signal fires (the most specific match).

    Args:
        file_path: Absolute or project-relative file path.
        scores: Accumulator dict to update.
        reasons: Reason trail to append to.
        signals: Debug signal dict to update.
    """
    path_lower = file_path.lower().replace("\\", "/")

    # Resolve to relative path for pattern matching
    root_str = str(ROOT).lower().replace("\\", "/")
    if path_lower.startswith(root_str):
        path_lower = path_lower[len(root_str):].lstrip("/")

    # Order: most specific first

    # 1f: workspace/inbox/PESSOAL/ -> personal (deprecated backward compat)
    if "workspace/inbox/pessoal/" in path_lower:
        scores["personal"] += PATH_INBOX_WEIGHT
        reasons.append("path:personal (workspace/inbox/pessoal -- DEPRECATED)")
        signals["S1_path"] = "personal"
        return

    # 1g: workspace/inbox/EMPRESA/ -> business (deprecated backward compat)
    if "workspace/inbox/empresa/" in path_lower:
        scores["business"] += PATH_INBOX_WEIGHT
        reasons.append("path:business (workspace/inbox/empresa -- DEPRECATED)")
        signals["S1_path"] = "business"
        return

    # 1e: workspace/inbox/meetings/ -> business (strongest workspace signal)
    if "workspace/inbox/meetings/" in path_lower or "workspace/inbox/meeting" in path_lower:
        scores["business"] += PATH_INBOX_WEIGHT
        reasons.append("path:business (workspace/inbox/meetings)")
        signals["S1_path"] = "business"
        return

    # 1a: knowledge/external/inbox/ -> external
    if "knowledge/external/inbox/" in path_lower:
        scores["external"] += PATH_INBOX_WEIGHT
        reasons.append("path:external")
        signals["S1_path"] = "external"
        return

    # 1b: knowledge/business/inbox/ -> business
    if "knowledge/business/inbox/" in path_lower:
        scores["business"] += PATH_INBOX_WEIGHT
        reasons.append("path:business")
        signals["S1_path"] = "business"
        return

    # 1c: knowledge/personal/inbox/ -> personal
    if "knowledge/personal/inbox/" in path_lower:
        scores["personal"] += PATH_INBOX_WEIGHT
        reasons.append("path:personal")
        signals["S1_path"] = "personal"
        return

    # 1d: workspace/inbox/ (generic, DEPRECATED) -> business (weaker)
    if "workspace/inbox/" in path_lower:
        scores["business"] += PATH_WORKSPACE_WEIGHT
        reasons.append("path:business (workspace/inbox -- DEPRECATED)")
        signals["S1_path"] = "business"
        return

    signals["S1_path"] = None


# ---------------------------------------------------------------------------
# SIGNAL 2: PARTICIPANT ANALYSIS (meetings only)
# ---------------------------------------------------------------------------


def _signal_participants(
    ctx: ClassificationContext,
    scores: dict[str, int],
    reasons: list[str],
    signals: dict[str, object],
) -> None:
    """Analyze meeting participants to determine bucket affinity.

    Only fires if participants or organizer_email is present.

    Args:
        ctx: Classification context.
        scores: Accumulator dict to update.
        reasons: Reason trail to append to.
        signals: Debug signal dict to update.
    """
    if not ctx.participants and not ctx.organizer_email:
        signals["S2_participants"] = "skipped"
        return

    owner_email = _load_owner_email()

    company_attendees = 0
    external_attendees = 0
    total_attendees = 0

    # 2a: Organizer email matches company domain
    if ctx.organizer_email and _email_matches_company(ctx.organizer_email):
        scores["business"] += PARTICIPANT_ORGANIZER
        reasons.append(f"organizer-company:{ctx.organizer_email}")

    # 2c: Organizer is owner specifically
    if ctx.organizer_email and owner_email and ctx.organizer_email.lower() == owner_email:
        scores["personal"] += PARTICIPANT_OWNER
        reasons.append("organizer-is-owner")

    # 2b/2d: Per-attendee scoring
    for email in ctx.participants:
        if not email or "@" not in email:
            continue
        total_attendees += 1

        if _email_matches_company(email):
            company_attendees += 1
            scores["business"] += PARTICIPANT_ATTENDEE
            reasons.append(f"attendee-company:{email}")
        elif owner_email and email.lower() == owner_email:
            # Owner email in attendee list -- don't double-count as external
            pass
        else:
            external_attendees += 1
            scores["external"] += PARTICIPANT_EXTERNAL
            reasons.append(f"attendee-external:{email}")

    # 2e: ALL attendees are company domain (internal meeting)
    if total_attendees > 0 and company_attendees == total_attendees:
        scores["business"] += PARTICIPANT_ALL_INTERNAL
        reasons.append("all-internal-meeting")

    # 2f: Only owner + non-company attendees (personal meeting)
    is_owner_organizer = (
        ctx.organizer_email
        and owner_email
        and ctx.organizer_email.lower() == owner_email
    )
    if is_owner_organizer and company_attendees == 0 and external_attendees > 0:
        scores["personal"] += PARTICIPANT_PERSONAL_MEETING
        reasons.append("personal-meeting (owner + non-company only)")

    signals["S2_company_attendees"] = company_attendees
    signals["S2_external_attendees"] = external_attendees
    signals["S2_total_attendees"] = total_attendees


# ---------------------------------------------------------------------------
# SIGNAL 3: ENTITY DETECTION (content scan)
# ---------------------------------------------------------------------------


def _signal_entities(
    text_sample: str,
    scores: dict[str, int],
    reasons: list[str],
    signals: dict[str, object],
    detected_entities: list[str],
) -> None:
    """Scan text for known experts, team members, and owner mentions.

    Args:
        text_sample: First N characters of file content.
        scores: Accumulator dict to update.
        reasons: Reason trail to append to.
        signals: Debug signal dict to update.
        detected_entities: Entity list to append to.
    """
    text_lower = text_sample.lower()
    text_normalized = _normalize_name(text_sample)

    # 3a: Known expert names
    experts = _load_known_experts()
    experts_found: list[str] = []

    # Build search patterns from expert slugs
    # e.g., 'alex-hormozi' -> search for 'alex hormozi', 'alex-hormozi', 'alexhormozi'
    for slug in experts:
        parts = slug.split("-")
        patterns = [
            " ".join(parts),     # "alex hormozi"
            "-".join(parts),     # "alex-hormozi"
            "".join(parts),      # "alexhormozi"
        ]
        for pattern in patterns:
            if pattern in text_lower:
                experts_found.append(slug)
                break

    # Also check via ENTITY_ALIASES for additional fuzzy matching
    try:
        from core.intelligence.pipeline.inbox_organizer import ENTITY_ALIASES

        for alias, slug in ENTITY_ALIASES.items():
            if slug in experts and alias in text_lower and slug not in experts_found:
                experts_found.append(slug)
    except ImportError:
        pass

    for expert in experts_found:
        scores["external"] += ENTITY_EXPERT
        detected_entities.append(expert)
        reasons.append(f"expert:{expert}")

    # 3b: Known team members
    team = _load_known_team()
    team_found: list[tuple[str, str]] = []

    for name, member_id in team.items():
        # Use normalized comparison for accent-insensitive matching
        if name in text_normalized:
            team_found.append((name, member_id))

    for member_name, member_id in team_found:
        scores["business"] += ENTITY_TEAM
        detected_entities.append(member_id)
        reasons.append(f"team:{member_name}")

    # 3c: Owner name/alias
    owner_aliases = _load_owner_aliases()
    owner_found = False
    if owner_aliases:
        for alias in owner_aliases:
            if alias in text_lower:
                owner_found = True
                break

    if owner_found:
        scores["personal"] += ENTITY_OWNER
        detected_entities.append("owner")
        reasons.append("owner-mentioned")

    signals["S3_experts"] = len(experts_found)
    signals["S3_team"] = len(team_found)
    signals["S3_owner"] = int(owner_found)


# ---------------------------------------------------------------------------
# SIGNAL 4: CONTENT TYPE DETECTION
# ---------------------------------------------------------------------------

# Filename patterns for source type detection
_COURSE_PATTERNS = re.compile(
    r"(?:course|masterclass|master[\-_\s]class|podcast|youtube|"
    r"\bead\b|module|modulo|aula|lesson|treinamento|training|"
    r"mastermind|inner[\-_\s]circle)",
    re.IGNORECASE,
)

_MEETING_PATTERNS = re.compile(
    r"(?:\bcall\b|\bmeet\b|meeting|reuni[aã]o|standup|"
    r"grava[cç][aã]o|recording|zoom|google\s*meet|"
    r"weekly|daily|sync|1:1|\bata\b|semanal)",
    re.IGNORECASE,
)

_PERSONAL_PATTERNS = re.compile(
    r"(?:journal|reflexao|reflexão|diario|diário|personal|pessoal|"
    r"private|cognitive|nota[\-_\s]pessoal|my[\-_\s]notes)",
    re.IGNORECASE,
)

_TEMPLATE_PATTERNS = re.compile(
    r"(?:\bscript\b|\btemplate\b|roteiro|\bsop\b|"
    r"checklist|playbook|processo|procedure)",
    re.IGNORECASE,
)


def _detect_source_type(filename: str, source_type_hint: str) -> str:
    """Detect the source type of a file from its filename and hint.

    Args:
        filename: The filename to analyze.
        source_type_hint: Upstream hint (e.g., 'meeting', 'transcript').

    Returns:
        Source type string: 'course', 'meeting', 'personal', 'document', 'unknown'.
    """
    # Honor explicit hints
    if source_type_hint:
        hint_lower = source_type_hint.lower()
        if hint_lower in {"meeting", "call"}:
            return "meeting"
        if hint_lower in {"course", "masterclass", "podcast", "youtube"}:
            return "course"
        if hint_lower in {"transcript"}:
            # Transcript could be meeting or course -- fall through to filename check
            pass
        if hint_lower in {"document", "pdf", "doc"}:
            return "document"

    # Check filename patterns
    name_lower = filename.lower()

    if _COURSE_PATTERNS.search(name_lower):
        return "course"
    if _MEETING_PATTERNS.search(name_lower):
        return "meeting"
    if _PERSONAL_PATTERNS.search(name_lower):
        return "personal"
    if _TEMPLATE_PATTERNS.search(name_lower):
        return "document"

    return "unknown"


def _signal_content_type(
    source_type: str,
    scores: dict[str, int],
    reasons: list[str],
    signals: dict[str, object],
) -> None:
    """Apply content type signal based on detected source type.

    Args:
        source_type: Detected source type from ``_detect_source_type()``.
        scores: Accumulator dict to update.
        reasons: Reason trail to append to.
        signals: Debug signal dict to update.
    """
    if source_type == "course":
        scores["external"] += CONTENT_COURSE
        reasons.append("content:course")
    elif source_type == "meeting":
        scores["business"] += CONTENT_MEETING
        reasons.append("content:meeting")
    elif source_type == "personal":
        scores["personal"] += CONTENT_PERSONAL
        reasons.append("content:personal")
    elif source_type == "document":
        scores["business"] += CONTENT_TEMPLATE
        reasons.append("content:document")

    signals["S4_type"] = source_type


# ---------------------------------------------------------------------------
# SIGNAL 5: COGNITIVE PATTERNS (text scan)
# ---------------------------------------------------------------------------

# 5a: Owner first-person patterns (PT + EN)
_FIRST_PERSON_PATTERN = re.compile(
    r"(?:eu\s+(?:acredito|penso|decidi|acho|sinto|quero)|"
    r"I\s+(?:think|believe|decided|feel|want)|"
    r"minha\s+(?:vis[aã]o|estrat[eé]gia|filosofia|opini[aã]o)|"
    r"my\s+(?:vision|strategy|philosophy|opinion|view))",
    re.IGNORECASE,
)

# 5b: Teaching/lecturing pattern (expert monologue)
_TEACHING_PATTERN = re.compile(
    r"(?:the\s+way\s+I\s+do\s+it|here\'?s\s+(?:what|how)|"
    r"let\s+me\s+(?:teach|show|explain|walk\s+you)|"
    r"step\s+(?:one|1|number\s+one)|"
    r"o\s+(?:que\s+eu\s+fa[cç]o|segredo)\s+[eé]|"
    r"(?:primeiro|segundo|terceiro)\s+(?:passo|ponto)|"
    r"vou\s+(?:te\s+ensinar|mostrar|explicar))",
    re.IGNORECASE,
)

# 5c: Multi-party discussion with decisions
_DISCUSSION_PATTERN = re.compile(
    r"(?:(?:decidimos|agreed|decided)\s+(?:que|that|to)|"
    r"action\s+items?|pr[oó]ximos\s+passos|"
    r"(?:vamos|let\'?s)\s+(?:fazer|go\s+with|move\s+forward)|"
    r"(?:aprovado|approved|fechado|done)\b)",
    re.IGNORECASE,
)


def _signal_cognitive(
    text_sample: str,
    scores: dict[str, int],
    reasons: list[str],
    signals: dict[str, object],
) -> None:
    """Detect cognitive patterns in text to refine classification.

    Args:
        text_sample: First N characters of file content.
        scores: Accumulator dict to update.
        reasons: Reason trail to append to.
        signals: Debug signal dict to update.
    """
    # 5a: First-person owner patterns
    if _FIRST_PERSON_PATTERN.search(text_sample):
        scores["personal"] += COGNITIVE_FIRST_PERSON
        reasons.append("cognitive:first-person")
        signals["S5_first_person"] = True
    else:
        signals["S5_first_person"] = False

    # 5b: Teaching/lecturing pattern
    if _TEACHING_PATTERN.search(text_sample):
        scores["external"] += COGNITIVE_TEACHING
        reasons.append("cognitive:teaching")
        signals["S5_teaching"] = True
    else:
        signals["S5_teaching"] = False

    # 5c: Multi-party discussion with decisions
    if _DISCUSSION_PATTERN.search(text_sample):
        scores["business"] += COGNITIVE_DISCUSSION
        reasons.append("cognitive:discussion")
        signals["S5_discussion"] = True
    else:
        signals["S5_discussion"] = False


# ---------------------------------------------------------------------------
# SIGNAL 6: TOPIC KEYWORDS (text scan)
# ---------------------------------------------------------------------------

# 6b: Expert teaching markers
_EXPERT_MARKERS = re.compile(
    r"(?:\bframework\b|\bmethodology\b|\bthe\s+way\s+I\b|"
    r"\bstep\s+(?:\d+|one|two|three)\b|\bplaybook\b|"
    r"\bblueprint\b|\bfunnel\b|\boffer\b|"
    r"\bmetodologia\b|\bprocesso\b|\betapa\b)",
    re.IGNORECASE,
)

# 6c: Business operational markers
_BUSINESS_MARKERS = re.compile(
    r"(?:\bKPI\b|\bOKR\b|\bsprint\b|\bpipeline\b|"
    r"\bcontrata[cç][aã]o\b|\bhiring\b|\bonboarding\b|"
    r"\bfaturamento\b|\brevenue\b|\bMRR\b|\bchurn\b|"
    r"\bscorecard\b|\b1:1\b|\bstandup\b|\bretrospective\b)",
    re.IGNORECASE,
)


def _signal_topics(
    text_sample: str,
    scores: dict[str, int],
    reasons: list[str],
    signals: dict[str, object],
) -> None:
    """Scan text for domain-specific topic keywords.

    Args:
        text_sample: First N characters of file content.
        scores: Accumulator dict to update.
        reasons: Reason trail to append to.
        signals: Debug signal dict to update.
    """
    text_lower = text_sample.lower()

    # 6a: Company keywords (from env var, max 2x contribution)
    company_keywords = _load_company_keywords()
    company_hits = 0
    for kw in company_keywords:
        if kw in text_lower:
            company_hits += 1
            if company_hits <= 2:
                scores["business"] += TOPIC_COMPANY_KEYWORD
                reasons.append(f"topic:company-keyword({kw})")
    signals["S6_company_keywords"] = company_hits

    # 6b: Expert teaching markers
    if _EXPERT_MARKERS.search(text_sample):
        scores["external"] += TOPIC_EXPERT_MARKERS
        reasons.append("topic:expert-markers")
        signals["S6_expert_markers"] = True
    else:
        signals["S6_expert_markers"] = False

    # 6c: Business operational markers
    if _BUSINESS_MARKERS.search(text_sample):
        scores["business"] += TOPIC_BUSINESS_MARKERS
        reasons.append("topic:business-markers")
        signals["S6_business_markers"] = True
    else:
        signals["S6_business_markers"] = False


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

_SCOPE_LOG = LOGS / "scope-classifier.jsonl"


def _log_decision(decision: ScopeDecision, file_path: str, duration_ms: int) -> None:
    """Append classification decision to JSONL log.

    Args:
        decision: The classification result.
        file_path: Path of the classified file.
        duration_ms: Time taken in milliseconds.
    """
    try:
        _SCOPE_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "file_path": file_path,
            "primary_bucket": decision.primary_bucket,
            "cascade_buckets": decision.cascade_buckets,
            "confidence": decision.confidence,
            "source_type": decision.source_type,
            "detected_entities": decision.detected_entities,
            "signals": {k: v for k, v in decision.signals.items()},
            "reasons": decision.reasons,
            "duration_ms": duration_ms,
        }
        with open(_SCOPE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        logger.debug("Failed to write scope classifier log", exc_info=True)


# ---------------------------------------------------------------------------
# MAIN CLASSIFICATION FUNCTION
# ---------------------------------------------------------------------------


def classify(ctx: ClassificationContext) -> ScopeDecision:
    """Classify a file into knowledge bucket(s) using 6 signal passes.

    This is the main public API. It runs all signal passes, aggregates
    scores, and returns a ``ScopeDecision`` with the primary bucket,
    optional cascade buckets, confidence level, and debug information.

    The function never raises exceptions -- all errors are caught and
    result in a safe default (external bucket, zero confidence).

    Args:
        ctx: Classification context with file content, metadata, etc.

    Returns:
        ScopeDecision with routing information.

    Example::

        from core.intelligence.pipeline.scope_classifier import classify, ClassificationContext

        ctx = ClassificationContext(
            text=open("some-file.txt").read()[:5000],
            filename="hormozi-course-01.txt",
            file_path="/path/to/knowledge/external/inbox/hormozi-course-01.txt",
        )
        decision = classify(ctx)
        print(decision.primary_bucket)  # "external"
        print(decision.confidence)      # 0.87
    """
    start_time = time.monotonic()

    try:
        return _classify_internal(ctx, start_time)
    except Exception:
        logger.warning("scope_classifier crashed; returning safe default", exc_info=True)
        elapsed = int((time.monotonic() - start_time) * 1000)
        decision = ScopeDecision(
            primary_bucket="external",
            confidence=0.0,
            reasons=["error:classifier-crash"],
            source_type="unknown",
            signals={"error": True},
        )
        _log_decision(decision, ctx.file_path, elapsed)
        return decision


def _classify_internal(ctx: ClassificationContext, start_time: float) -> ScopeDecision:
    """Internal classification logic (separated for clean error handling).

    Args:
        ctx: Classification context.
        start_time: Monotonic start time for duration measurement.

    Returns:
        Fully populated ScopeDecision.
    """
    scores: dict[str, int] = {"external": 0, "business": 0, "personal": 0}
    reasons: list[str] = []
    signals: dict[str, object] = {}
    detected_entities: list[str] = []

    # --- SIGNAL 1: Path Analysis ---
    _signal_path(ctx.file_path, scores, reasons, signals)

    # --- SIGNAL 2: Participant Analysis (meetings only) ---
    _signal_participants(ctx, scores, reasons, signals)

    # --- SIGNAL 3: Entity Detection (content scan) ---
    text_sample = ctx.text[:TEXT_SAMPLE_SIZE]
    _signal_entities(text_sample, scores, reasons, signals, detected_entities)

    # --- SIGNAL 4: Content Type Detection ---
    source_type = _detect_source_type(ctx.filename, ctx.source_type_hint)
    _signal_content_type(source_type, scores, reasons, signals)

    # --- SIGNAL 5: Cognitive Patterns ---
    _signal_cognitive(text_sample, scores, reasons, signals)

    # --- SIGNAL 6: Topic Keywords ---
    _signal_topics(text_sample, scores, reasons, signals)

    # --- AGGREGATION ---
    primary = max(scores, key=lambda k: scores[k])
    primary_score = scores[primary]
    total_score = sum(scores.values())

    # Confidence = how dominant the winner is
    if total_score == 0:
        confidence = 0.0
    else:
        confidence = primary_score / total_score
        confidence = min(1.0, max(0.0, confidence))

    # Cascade: non-primary buckets scoring above threshold
    cascade = [
        b for b in scores
        if b != primary and scores[b] >= CASCADE_THRESHOLD
    ]

    decision = ScopeDecision(
        primary_bucket=primary,
        cascade_buckets=cascade,
        confidence=round(confidence, 2),
        reasons=reasons,
        source_type=source_type,
        detected_entities=detected_entities,
        signals=signals,
    )

    elapsed = int((time.monotonic() - start_time) * 1000)
    _log_decision(decision, ctx.file_path, elapsed)

    return decision
