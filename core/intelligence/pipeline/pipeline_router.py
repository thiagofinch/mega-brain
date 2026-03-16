"""
pipeline_router.py — Tridimensional Bucket Router
===================================================
Determines which knowledge bucket a file belongs to based on its path,
and provides output routing for each pipeline phase.

Used by Pipeline Jarvis (Phase 1) to decide:
  - Which bucket: external / business / personal
  - Which subdirectory within the bucket
  - Whether dual-routing applies (owner insights → personal too)

Version: 1.0.0
Date: 2026-03-07
"""

import os
import re
from pathlib import Path

from core.paths import (
    KNOWLEDGE_BUSINESS,
    KNOWLEDGE_EXTERNAL,
    KNOWLEDGE_PERSONAL,
)

# ---------------------------------------------------------------------------
# OWNER DETECTION (for dual-routing)
# ---------------------------------------------------------------------------

OWNER_NAME = os.environ.get("MEGA_BRAIN_OWNER_NAME", "").strip()
OWNER_EMAIL = os.environ.get("MEGA_BRAIN_OWNER_EMAIL", "").strip()

# Build owner alias list for matching in transcripts/insights
_owner_aliases: list[str] = []
if OWNER_NAME:
    _owner_aliases.append(OWNER_NAME.lower())
    # Add first name
    parts = OWNER_NAME.split()
    if len(parts) > 1:
        _owner_aliases.append(parts[0].lower())


def get_owner_aliases() -> list[str]:
    """Return list of lowercase owner name aliases for matching."""
    return list(_owner_aliases)


# ---------------------------------------------------------------------------
# BUCKET DETECTION
# ---------------------------------------------------------------------------

# Path patterns that indicate each bucket
_WORKSPACE_INDICATORS = [
    "empresa",
    "business",
    "meetings",
    "workspace",
    "financeiro",
    "financial",
    "calls",
    "ata",
]
_PERSONAL_INDICATORS = [
    "pessoal",
    "personal",
    "cognitive",
    "journal",
    "reflexao",
    "saude",
    "health",
    "private",
]


def detect_bucket(file_path: str | Path) -> str:
    """Detect which bucket a file belongs to based on its path.

    Priority:
      1. Explicit bucket inbox paths (knowledge/business/inbox/, knowledge/personal/inbox/, etc.)
      2. Path-based indicators (business/personal keywords in path)
      3. Default to external (fallback)

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        One of: 'external', 'business', 'personal'
    """
    path = Path(file_path).resolve()
    path_str = str(path).lower()

    # --- Priority 1: Explicit bucket inbox ---
    business_inbox = str(KNOWLEDGE_BUSINESS / "inbox").lower()
    personal_inbox = str(KNOWLEDGE_PERSONAL / "inbox").lower()
    external_inbox = str(KNOWLEDGE_EXTERNAL / "inbox").lower()

    if business_inbox in path_str:
        return "business"
    if personal_inbox in path_str:
        return "personal"
    if external_inbox in path_str:
        return "external"

    # --- Priority 2: Path-based indicators (content analysis) ---
    # Check for workspace/business/personal indicators in the path
    for ind in _WORKSPACE_INDICATORS:
        if ind in path_str:
            return "business"
    for ind in _PERSONAL_INDICATORS:
        if ind in path_str:
            return "personal"

    # --- Priority 3: Default to external (expert content) ---
    return "external"


# ---------------------------------------------------------------------------
# OUTPUT ROUTING PER PHASE
# ---------------------------------------------------------------------------

# Where each pipeline phase writes its output, per bucket
PHASE_OUTPUT_MAP = {
    "external": {
        "dossiers_persons": KNOWLEDGE_EXTERNAL / "dossiers" / "persons",
        "dossiers_themes": KNOWLEDGE_EXTERNAL / "dossiers" / "THEMES",
        "dna": KNOWLEDGE_EXTERNAL / "dna" / "persons",
        "playbooks": KNOWLEDGE_EXTERNAL / "playbooks",
        "sources": KNOWLEDGE_EXTERNAL / "sources",
    },
    "business": {
        "dossiers_persons": KNOWLEDGE_BUSINESS / "dossiers",
        "dossiers_themes": KNOWLEDGE_BUSINESS / "dossiers" / "THEMES",
        "dna": None,  # business bucket doesn't produce DNA
        "playbooks": None,  # business bucket doesn't produce playbooks
        "sources": KNOWLEDGE_BUSINESS / "inbox",
    },
    "personal": {
        "dossiers_persons": KNOWLEDGE_PERSONAL / "_cognitive",
        "dossiers_themes": KNOWLEDGE_PERSONAL / "_cognitive" / "themes",
        "dna": KNOWLEDGE_PERSONAL / "_cognitive" / "dna",
        "playbooks": None,
        "sources": KNOWLEDGE_PERSONAL / "_cognitive",
    },
}


def get_output_path(bucket: str, phase_output: str) -> Path | None:
    """Get the output path for a given bucket and phase output type.

    Args:
        bucket: One of 'external', 'workspace', 'personal'.
        phase_output: One of the keys in PHASE_OUTPUT_MAP.

    Returns:
        Path or None if that output type doesn't apply to this bucket.
    """
    bucket_map = PHASE_OUTPUT_MAP.get(bucket, PHASE_OUTPUT_MAP["external"])
    return bucket_map.get(phase_output)


# ---------------------------------------------------------------------------
# DUAL-ROUTING
# ---------------------------------------------------------------------------


def should_dual_route(text: str) -> bool:
    """Check if content mentions the owner and should be dual-routed.

    Dual-routing means: insights about the owner go to BOTH the primary
    bucket AND knowledge/personal/_cognitive/.

    Args:
        text: Content to check (first 3000 chars used).

    Returns:
        True if owner is mentioned and dual-routing should apply.
    """
    if not _owner_aliases:
        return False

    sample = text[:3000].lower()
    return any(alias in sample for alias in _owner_aliases)


# Cognitive patterns that indicate personal/founder insights
COGNITIVE_PATTERNS = [
    r"(?:eu|I)\s+(?:acredito|believe|penso|think|decidi|decided)",
    r"(?:minha|my)\s+(?:vis[aã]o|vision|estrat[eé]gia|strategy|filosofia|philosophy)",
    r"(?:aprendi|learned|percebi|realized|notei|noticed)",
    r"(?:decisão|decision)\s+(?:do|de|by)\s+(?:founder|fundador|CEO|dono)",
    r"padrão\s+de\s+(?:pensamento|decisão|comportamento)",
    r"(?:reflexão|reflection|insight\s+pessoal|personal\s+insight)",
]


def extract_cognitive_insights(text: str) -> list[str]:
    """Extract sentences that contain cognitive/founder patterns.

    These are the insights that get dual-routed to knowledge/personal/_cognitive/.

    Args:
        text: Full text to scan.

    Returns:
        List of sentences matching cognitive patterns.
    """
    insights = []
    # Split into sentences (rough)
    sentences = re.split(r"[.!?\n]+", text)

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue
        for pattern in COGNITIVE_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                insights.append(sentence)
                break

    return insights


# ---------------------------------------------------------------------------
# ROUTE SUMMARY (for pipeline Phase 1 output)
# ---------------------------------------------------------------------------


def route_file(file_path: str | Path) -> dict:
    """Complete routing decision for a file entering the pipeline.

    This is the main entry point used by Pipeline Jarvis Phase 1.

    Args:
        file_path: Path to the file being processed.

    Returns:
        Routing decision dict with bucket, paths, and flags.
    """
    bucket = detect_bucket(file_path)
    outputs = PHASE_OUTPUT_MAP.get(bucket, PHASE_OUTPUT_MAP["external"])

    return {
        "bucket": bucket,
        "file_path": str(file_path),
        "outputs": {k: str(v) if v else None for k, v in outputs.items()},
        "dual_route": bool(_owner_aliases),  # Will check content later
        "owner_name": OWNER_NAME or None,
        "owner_aliases": _owner_aliases,
    }
