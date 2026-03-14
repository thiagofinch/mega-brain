#!/usr/bin/env python3
"""
INSIGHT SPEAKER LINKER — Link insights to speakers and timestamps.
==================================================================

Takes insight JSON (from pipeline Fase 4) and a source transcript,
then enriches each insight with `speaker` and `timestamp` fields
by matching chunk text back to the transcript.

Graceful degradation: if speaker or timestamp cannot be detected,
the field is set to null rather than raising an error.

Version: 1.0.0
Date: 2026-03-09
Story: S09 — EPIC-REORG-001
"""

import json
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from core.paths import BUSINESS_INSIGHTS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SPEAKER DETECTION PATTERNS
# ---------------------------------------------------------------------------

# Pattern 1: Read.ai format — "Speaker Name HH:MM:SS" at line start
_READAI_SPEAKER_RE = re.compile(
    r"^([A-Z][A-Za-zÀ-ÿ\s\.\-']+?)\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*$",
    re.MULTILINE,
)

# Pattern 2: Colon-delimited — "Speaker Name: text..."
_COLON_SPEAKER_RE = re.compile(
    r"^([A-Z][A-Za-zÀ-ÿ\s\.\-']{2,40}):\s+(.+)",
    re.MULTILINE,
)

# Pattern 3: Bracket-delimited — "[Speaker Name] text..." or "[Speaker Name] HH:MM"
_BRACKET_SPEAKER_RE = re.compile(
    r"^\[([A-Za-zÀ-ÿ\s\.\-']+)\]\s*(?:(\d{1,2}:\d{2}(?::\d{2})?))?",
    re.MULTILINE,
)

# Pattern 4: Diarization tags — "SPEAKER_00:", "Speaker 1:", etc.
_DIARIZATION_RE = re.compile(
    r"^((?:SPEAKER|Speaker|Falante)\s*[_\s]?\d+)\s*[:\-]\s*(.+)",
    re.MULTILINE,
)

# Timestamp extraction from context (standalone)
_TIMESTAMP_RE = re.compile(
    r"(\d{1,2}:\d{2}(?::\d{2})?)",
)


# ---------------------------------------------------------------------------
# TRANSCRIPT PARSING
# ---------------------------------------------------------------------------


def _build_speaker_map(transcript_text: str) -> list[dict]:
    """Parse a transcript and build a list of segments with speaker + timestamp.

    Each segment is: {speaker, timestamp, start_char, end_char, text}
    """
    segments: list[dict] = []

    # Try patterns in order of specificity
    for pattern, has_timestamp_group in [
        (_READAI_SPEAKER_RE, True),
        (_BRACKET_SPEAKER_RE, True),
        (_COLON_SPEAKER_RE, False),
        (_DIARIZATION_RE, False),
    ]:
        matches = list(pattern.finditer(transcript_text))
        if len(matches) >= 2:
            # This pattern has enough matches to be the format
            for i, m in enumerate(matches):
                speaker = m.group(1).strip()
                timestamp = None
                if has_timestamp_group and m.lastindex and m.lastindex >= 2:
                    timestamp = m.group(2)

                # Segment text runs from this match to the next
                start = m.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(transcript_text)
                text = transcript_text[start:end].strip()

                # If no timestamp from pattern, try to find one nearby
                if not timestamp:
                    nearby = transcript_text[max(0, m.start() - 20) : m.end() + 30]
                    ts_match = _TIMESTAMP_RE.search(nearby)
                    if ts_match:
                        timestamp = ts_match.group(1)

                segments.append(
                    {
                        "speaker": speaker,
                        "timestamp": timestamp,
                        "start_char": m.start(),
                        "end_char": end,
                        "text": text[:500],  # Truncate for matching
                    }
                )

            logger.info(
                "Parsed %d segments using pattern: %s",
                len(segments),
                pattern.pattern[:40],
            )
            return segments

    # Fallback: no recognized speaker pattern
    logger.warning("No recognized speaker pattern found in transcript")
    return segments


def _fuzzy_match_score(needle: str, haystack: str) -> float:
    """Compute a simple overlap score between two texts (0.0-1.0).

    Uses word-level Jaccard similarity for speed.
    """
    if not needle or not haystack:
        return 0.0

    needle_words = set(needle.lower().split())
    haystack_words = set(haystack.lower().split())

    if not needle_words:
        return 0.0

    intersection = needle_words & haystack_words
    union = needle_words | haystack_words

    return len(intersection) / len(union) if union else 0.0


def _find_best_segment(
    insight_text: str,
    segments: list[dict],
    threshold: float = 0.15,
) -> dict | None:
    """Find the transcript segment that best matches the insight text.

    Args:
        insight_text: The evidence or summary text from the insight.
        segments: Parsed transcript segments.
        threshold: Minimum Jaccard score to accept.

    Returns:
        Best matching segment dict, or None.
    """
    if not segments:
        return None

    best: dict | None = None
    best_score = threshold

    for seg in segments:
        score = _fuzzy_match_score(insight_text, seg["text"])
        if score > best_score:
            best_score = score
            best = seg

    return best


# ---------------------------------------------------------------------------
# INSIGHT NORMALIZATION (same as sop_detector for consistency)
# ---------------------------------------------------------------------------


def _get_insight_text(insight: dict) -> str:
    """Extract the primary text content from an insight dict."""
    # evidence is the original quote — best for matching
    evidence = insight.get("evidence", "")
    summary = insight.get("summary") or insight.get("insight", "")
    return evidence if evidence else summary


def _get_insight_id(insight: dict) -> str:
    """Extract a stable ID from an insight dict."""
    return insight.get("id", "") or insight.get("source", {}).get("source_id", "unknown")


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------


def link_speakers(
    insights_path: Path,
    transcript_path: Path,
) -> dict:
    """Link insights to speakers from transcript.

    Args:
        insights_path: Path to JSON file containing insights (list or
                       envelope with 'insights' key).
        transcript_path: Path to the transcript text file.

    Returns:
        Dict with keys:
          linked: int — number of insights successfully linked
          unlinked: int — number without speaker attribution
          insights: list — enriched insight dicts with speaker/timestamp
          segments_found: int — speaker segments parsed from transcript
    """
    # Load insights
    try:
        with open(insights_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load insights: %s", e)
        return {"linked": 0, "unlinked": 0, "insights": [], "segments_found": 0}

    insights: list[dict] = []
    if isinstance(data, list):
        insights = data
    elif isinstance(data, dict) and "insights" in data:
        insights = data["insights"]
    else:
        logger.error("Unrecognized insight format in %s", insights_path.name)
        return {"linked": 0, "unlinked": 0, "insights": [], "segments_found": 0}

    # Load transcript
    try:
        transcript_text = transcript_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("Failed to read transcript: %s", e)
        return {
            "linked": 0,
            "unlinked": len(insights),
            "insights": insights,
            "segments_found": 0,
        }

    # Parse speaker segments
    segments = _build_speaker_map(transcript_text)
    logger.info("Found %d speaker segments in transcript", len(segments))

    linked = 0
    unlinked = 0

    for insight in insights:
        text = _get_insight_text(insight)
        match = _find_best_segment(text, segments)

        if match:
            insight["speaker"] = match["speaker"]
            insight["timestamp"] = match["timestamp"]
            linked += 1
            logger.debug(
                "Linked %s -> %s @ %s",
                _get_insight_id(insight),
                match["speaker"],
                match["timestamp"],
            )
        else:
            # Keep existing speaker if present (some formats include it)
            if "speaker" not in insight:
                insight["speaker"] = (
                    insight.get("person")
                    or (
                        insight.get("source", {}).get("speaker")
                        if isinstance(insight.get("source"), dict)
                        else None
                    )
                    or None
                )
            if "timestamp" not in insight:
                insight["timestamp"] = None
            unlinked += 1

    result = {
        "linked": linked,
        "unlinked": unlinked,
        "insights": insights,
        "segments_found": len(segments),
    }

    logger.info("Linking complete: %d linked, %d unlinked", linked, unlinked)
    return result


def save_linked_insights(result: dict, output_path: Path) -> Path:
    """Save linked insights to a JSON file.

    Args:
        result: Return value from link_speakers().
        output_path: Destination file path.

    Returns:
        The output path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "linked_count": result["linked"],
        "unlinked_count": result["unlinked"],
        "segments_found": result["segments_found"],
        "linked_at": datetime.now(tz=UTC).isoformat(),
        "insights": result["insights"],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info("Saved linked insights: %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point for insight-speaker linking."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if len(sys.argv) < 3:
        print("\n=== Insight Speaker Linker ===\n")
        print("Links insights to speakers and timestamps from meeting transcripts.\n")
        print("Usage:")
        print(f"  python {__file__} <insights.json> <transcript.txt>")
        print(f"  python {__file__} <insights.json> <transcript.txt> [output.json]")
        print(f"\nDefault output: {BUSINESS_INSIGHTS / 'by-meeting'}/linked-<name>.json")
        return 0

    insights_path = Path(sys.argv[1])
    transcript_path = Path(sys.argv[2])

    if not insights_path.exists():
        logger.error("Insights file not found: %s", insights_path)
        return 1

    if not transcript_path.exists():
        logger.error("Transcript file not found: %s", transcript_path)
        return 1

    result = link_speakers(insights_path, transcript_path)

    # Determine output path
    if len(sys.argv) >= 4:
        output_path = Path(sys.argv[3])
    else:
        output_dir = BUSINESS_INSIGHTS / "by-meeting"
        output_path = output_dir / f"linked-{insights_path.stem}.json"

    save_linked_insights(result, output_path)

    # Summary
    print("\n=== Speaker Linking Results ===\n")
    print(f"  Transcript segments: {result['segments_found']}")
    print(f"  Insights linked:     {result['linked']}")
    print(f"  Insights unlinked:   {result['unlinked']}")
    print(f"  Output:              {output_path}")

    if result["unlinked"] > 0:
        total = result["linked"] + result["unlinked"]
        pct = result["linked"] / total * 100 if total else 0
        print(f"\n  Link rate: {pct:.0f}%")
        if result["segments_found"] == 0:
            print("  (No speaker segments found -- transcript may lack speaker markers)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
