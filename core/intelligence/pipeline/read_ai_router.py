"""
Read.ai Meeting Router — classifies meetings into empresa/pessoal buckets.

Scoring system:
  +3  organizer email domain matches company domains
  +2  per participant whose domain matches company domains
  +2  title contains company keyword
  +1  per business keyword in title/description
  Score >= 3 → empresa, else → pessoal

Usage:
    from core.intelligence.pipeline.read_ai_router import MeetingRouter
    router = MeetingRouter(config)
    decision = router.classify(meeting_data)
"""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from core.intelligence.pipeline.read_ai_config import ReadAIConfig


@dataclass
class RoutingDecision:
    """Result of meeting classification."""

    meeting_id: str
    bucket: str  # "empresa" or "pessoal"
    score: int
    confidence: str  # "high" (>= 5), "medium" (3-4), "low" (< 3)
    reasons: list[str]
    title: str
    filename: str


class MeetingRouter:
    """Classifies meetings and moves transcript files to inbox buckets."""

    EMPRESA_THRESHOLD = 3

    def __init__(self, config: ReadAIConfig):
        self.config = config
        self._domains = {d.lower() for d in config.company_domains}
        self._keywords = {k.lower() for k in config.company_keywords}
        self._company_lower = config.company_name.lower()
        self._log_path = config.log_dir / "routing.jsonl"

    def classify(self, meeting: dict[str, Any]) -> RoutingDecision:
        """
        Score a meeting and return routing decision.

        Args:
            meeting: Dict with keys: id, title, organizer_email,
                     participants (list of emails), description (optional)
        """
        score = 0
        reasons: list[str] = []
        title = meeting.get("title", "Untitled Meeting")

        # --- Organizer domain ---
        organizer = meeting.get("organizer_email", "")
        if self._email_matches_domain(organizer):
            score += 3
            reasons.append(f"organizer domain match ({organizer})")

        # --- Participant domains ---
        participants = meeting.get("participants", [])
        for p in participants:
            email = p if isinstance(p, str) else p.get("email", "")
            if self._email_matches_domain(email):
                score += 2
                reasons.append(f"participant domain match ({email})")

        # --- Title keyword match ---
        title_lower = title.lower()
        for kw in self._keywords:
            if kw in title_lower:
                score += 2
                reasons.append(f"title keyword match ({kw})")
                break  # Only count once for title

        if self._company_lower and self._company_lower in title_lower:
            if not any("title keyword" in r for r in reasons):
                score += 2
                reasons.append("title contains company name")

        # --- Business keywords in title/description ---
        description = meeting.get("description", "")
        combined_text = f"{title_lower} {description.lower()}"
        biz_keywords = [
            "standup", "sprint", "daily", "weekly", "retrospective",
            "planning", "review", "sync", "1:1", "one-on-one",
            "onboarding", "kickoff", "roadmap", "pipeline",
            "interview", "candidate",
        ]
        for bk in biz_keywords:
            if bk in combined_text:
                score += 1
                reasons.append(f"business keyword ({bk})")
                break  # Only +1 total

        # --- Decision ---
        bucket = "empresa" if score >= self.EMPRESA_THRESHOLD else "pessoal"
        if score >= 5:
            confidence = "high"
        elif score >= self.EMPRESA_THRESHOLD:
            confidence = "medium"
        else:
            confidence = "low"

        meeting_id = meeting.get("id", "unknown")

        decision = RoutingDecision(
            meeting_id=meeting_id,
            bucket=bucket,
            score=score,
            confidence=confidence,
            reasons=reasons,
            title=title,
            filename="",  # Set by move_file
        )
        return decision

    def move_file(
        self,
        source: Path,
        decision: RoutingDecision,
        tag: str,
    ) -> Path:
        """
        Move transcript from staging to final inbox destination.

        Args:
            source: Path to staged transcript file
            decision: RoutingDecision from classify()
            tag: Tag string like "[MEET-0042]"

        Returns:
            Final destination path
        """
        # Clean title for filename
        safe_title = self._sanitize_filename(decision.title)
        filename = f"{tag} {safe_title}.txt"
        decision.filename = filename

        if decision.bucket == "empresa":
            dest_dir = self.config.empresa_dir
        else:
            dest_dir = self.config.pessoal_dir

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

        # Log
        self._log(decision, dest)

        return dest

    def _email_matches_domain(self, email: str) -> bool:
        """Check if email belongs to one of the company domains."""
        if not email or "@" not in email:
            return False
        domain = email.split("@", 1)[1].lower()
        return domain in self._domains

    def _sanitize_filename(self, title: str) -> str:
        """Remove characters unsafe for filenames."""
        unsafe = '<>:"/\\|?*'
        result = title
        for ch in unsafe:
            result = result.replace(ch, "")
        # Collapse whitespace
        result = " ".join(result.split())
        # Truncate
        if len(result) > 120:
            result = result[:120].rstrip()
        return result or "Untitled"

    def _log(self, decision: RoutingDecision, dest: Path) -> None:
        """Append routing decision to JSONL log."""
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
