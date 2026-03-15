"""
Generalized Meeting Router -- classifies meetings into empresa/pessoal buckets.

Extracted from read_ai_router.py so both Read.ai and Fireflies adapters
can use the same classification logic without coupling to a specific config.

Scoring system:
  +3  organizer email domain matches company domains
  +2  per participant whose domain matches company domains
  +2  title contains company keyword
  +1  per business keyword in title
  Score >= THRESHOLD (3) -> empresa, else -> pessoal

Usage:
    from core.intelligence.pipeline.meeting_router import MeetingRouter
    router = MeetingRouter(
        company_domains=["example.com", "example.com.br"],
        company_keywords=["example", "brandname"],
    )
    result = router.classify(
        organizer_email="user@example.com",
        attendee_emails=["john@example.com"],
        title="Weekly Sync",
    )
    print(result.bucket, result.score)
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ============================================================================
# Defaults
# ============================================================================

_DEFAULT_BIZ_KEYWORDS: list[str] = [
    "standup",
    "sprint",
    "daily",
    "weekly",
    "retrospective",
    "planning",
    "review",
    "sync",
    "1:1",
    "one-on-one",
    "onboarding",
    "kickoff",
    "roadmap",
    "pipeline",
    "interview",
    "candidate",
    "alinhamento",
    "reuniao",
    "pulso",
    "pente fino",
]


# ============================================================================
# Result
# ============================================================================


@dataclass
class ClassificationResult:
    """Outcome of meeting classification."""

    bucket: str  # "empresa" or "pessoal"
    score: int
    confidence: str  # "high", "medium", "low"
    reasons: list[str] = field(default_factory=list)


# ============================================================================
# Router
# ============================================================================


class MeetingRouter:
    """Score-based meeting classifier.

    Stateless -- instantiate once, call ``classify()`` many times.
    """

    THRESHOLD = 3

    def __init__(
        self,
        company_domains: list[str],
        company_keywords: list[str],
        biz_keywords: list[str] | None = None,
    ) -> None:
        self._domains: set[str] = {d.lower() for d in company_domains}
        self._keywords: set[str] = {k.lower() for k in company_keywords}
        self._biz_keywords: list[str] = (
            biz_keywords if biz_keywords is not None else _DEFAULT_BIZ_KEYWORDS
        )

    # ── public API ─────────────────────────────────────────────────

    def classify(
        self,
        organizer_email: str,
        attendee_emails: list[str],
        title: str,
    ) -> ClassificationResult:
        """Score a meeting and return classification.

        Args:
            organizer_email: Email address of the meeting organizer.
            attendee_emails: List of attendee email addresses.
            title: Meeting title / subject line.

        Returns:
            ClassificationResult with bucket, score, confidence, reasons.
        """
        score = 0
        reasons: list[str] = []

        # --- Organizer domain ---
        if self._email_matches_domain(organizer_email):
            score += 3
            reasons.append(f"organizer domain match ({organizer_email})")

        # --- Participant domains ---
        for email in attendee_emails:
            if self._email_matches_domain(email):
                score += 2
                reasons.append(f"participant domain match ({email})")

        # --- Company keyword in title ---
        title_lower = title.lower()
        for kw in self._keywords:
            if kw in title_lower:
                score += 2
                reasons.append(f"company keyword in title ({kw})")
                break  # count once

        # --- Business keyword in title ---
        for bk in self._biz_keywords:
            if bk in title_lower:
                score += 1
                reasons.append(f"business keyword ({bk})")
                break  # count once

        # --- Decision ---
        bucket = "empresa" if score >= self.THRESHOLD else "pessoal"
        if score >= 5:
            confidence = "high"
        elif score >= self.THRESHOLD:
            confidence = "medium"
        else:
            confidence = "low"

        return ClassificationResult(
            bucket=bucket,
            score=score,
            confidence=confidence,
            reasons=reasons,
        )

    # ── internals ──────────────────────────────────────────────────

    def _email_matches_domain(self, email: str) -> bool:
        """Check if *email* belongs to one of the configured company domains.

        Filters out obviously invalid addresses (no ``@``, Google Calendar
        group IDs, resource addresses, etc.).
        """
        if not email or "@" not in email:
            return False

        # Filter Google Calendar group / resource addresses
        if email.startswith("group.calendar.google.com"):
            return False
        if "@resource.calendar.google.com" in email:
            return False
        if "@group.calendar.google.com" in email:
            return False

        domain = email.rsplit("@", 1)[1].lower()
        return domain in self._domains
