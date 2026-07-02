"""
Generalized Meeting Router -- classifies meetings into empresa/pessoal buckets.

Single source of truth for meeting classification. Absorbs all routing logic
previously split between read_ai_router.py and this module.
(Story W1-001.3b -- consolidation)

Scoring system:
  +3  organizer email domain matches company domains
  +2  per participant whose domain matches company domains
  +2  title contains company keyword OR company_name
  +1  per business keyword in title/description
  Score >= THRESHOLD (3) -> empresa, else -> pessoal

Usage:
    from engine.intelligence.pipeline.meeting_router import MeetingRouter
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

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

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
# Routing Decision (compat with read_ai_router.py consumers)
# ============================================================================


@dataclass
class RoutingDecision:
    """Full routing decision including file-move metadata.

    Superset of ClassificationResult -- used by callers that need
    move_file() and JSONL logging (previously in read_ai_router.py).
    """

    meeting_id: str
    bucket: str  # "empresa" or "pessoal"
    score: int
    confidence: str  # "high", "medium", "low"
    reasons: list[str]
    title: str
    filename: str


# ============================================================================
# Router
# ============================================================================


class MeetingRouter:
    """Score-based meeting classifier.

    Stateless for ``classify()`` -- instantiate once, call many times.

    Optional file-move and logging capabilities (``move_file``) require
    ``log_dir`` to be set at init time.
    """

    THRESHOLD = 3

    def __init__(
        self,
        company_domains: list[str],
        company_keywords: list[str],
        company_name: str = "",
        biz_keywords: list[str] | None = None,
        log_dir: Path | None = None,
    ) -> None:
        self._domains: set[str] = {d.lower() for d in company_domains}
        self._keywords: set[str] = {k.lower() for k in company_keywords}
        self._company_lower: str = company_name.lower() if company_name else ""
        self._biz_keywords: list[str] = (
            biz_keywords if biz_keywords is not None else _DEFAULT_BIZ_KEYWORDS
        )
        self._log_path: Path | None = log_dir / "routing.jsonl" if log_dir else None

    # ── public API ─────────────────────────────────────────────────

    def classify(
        self,
        organizer_email: str,
        attendee_emails: list[str],
        title: str,
        description: str = "",
    ) -> ClassificationResult:
        """Score a meeting and return classification.

        Args:
            organizer_email: Email address of the meeting organizer.
            attendee_emails: List of attendee email addresses.
            title: Meeting title / subject line.
            description: Optional meeting description/body text.

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
        keyword_matched = False
        for kw in self._keywords:
            if kw in title_lower:
                score += 2
                reasons.append(f"company keyword in title ({kw})")
                keyword_matched = True
                break  # count once

        # --- Company name in title (only if keyword didn't already match) ---
        if not keyword_matched and self._company_lower and self._company_lower in title_lower:
            score += 2
            reasons.append("title contains company name")

        # --- Business keyword in title/description ---
        combined_text = f"{title_lower} {description.lower()}" if description else title_lower
        for bk in self._biz_keywords:
            if bk in combined_text:
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

    def classify_meeting(self, meeting: dict) -> RoutingDecision:
        """Classify from a meeting dict (compat with read_ai_router.py API).

        Accepts a dict with keys: id, title, organizer_email,
        participants (list of emails or dicts), description (optional).
        """
        title = meeting.get("title", "Untitled Meeting")
        organizer = meeting.get("organizer_email", "")
        description = meeting.get("description", "")
        participants = meeting.get("participants", [])

        attendee_emails = []
        for p in participants:
            email = p if isinstance(p, str) else p.get("email", "")
            if email:
                attendee_emails.append(email)

        result = self.classify(
            organizer_email=organizer,
            attendee_emails=attendee_emails,
            title=title,
            description=description,
        )

        return RoutingDecision(
            meeting_id=meeting.get("id", "unknown"),
            bucket=result.bucket,
            score=result.score,
            confidence=result.confidence,
            reasons=result.reasons,
            title=title,
            filename="",  # Set by move_file
        )

    def move_file(
        self,
        source: Path,
        decision: RoutingDecision,
        tag: str,
        empresa_dir: Path,
        pessoal_dir: Path,
    ) -> Path:
        """Move transcript from staging to final inbox destination.

        Args:
            source: Path to staged transcript file.
            decision: RoutingDecision from classify_meeting().
            tag: Tag string like "[MEET-0042]".
            empresa_dir: Destination directory for business meetings.
            pessoal_dir: Destination directory for personal meetings.

        Returns:
            Final destination path.
        """
        safe_title = self._sanitize_filename(decision.title)
        filename = f"{tag} {safe_title}.txt"
        decision.filename = filename

        dest_dir = empresa_dir if decision.bucket == "empresa" else pessoal_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename

        # Avoid overwriting
        if dest.exists():
            stem = dest.stem
            suffix = dest.suffix
            counter = 1
            while dest.exists():
                dest = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        shutil.move(str(source), str(dest))
        self._log(decision, dest)
        return dest

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

    @staticmethod
    def _sanitize_filename(title: str) -> str:
        """Remove characters unsafe for filenames."""
        unsafe = '<>:"/\\|?*'
        result = title
        for ch in unsafe:
            result = result.replace(ch, "")
        result = " ".join(result.split())
        if len(result) > 120:
            result = result[:120].rstrip()
        return result or "Untitled"

    def _log(self, decision: RoutingDecision, dest: Path) -> None:
        """Append routing decision to JSONL log."""
        if not self._log_path:
            return
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "meeting_id": decision.meeting_id,
            "bucket": decision.bucket,
            "score": decision.score,
            "confidence": decision.confidence,
            "reasons": decision.reasons,
            "title": decision.title,
            "filename": decision.filename,
            "destination": str(dest),
        }
        with open(self._log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
