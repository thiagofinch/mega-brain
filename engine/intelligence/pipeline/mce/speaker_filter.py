"""
speaker_filter.py — Speaker-aware transcript filtering for DNA extraction.
==========================================================================

Story: STORY-MCE-SPEAKER-AWARE-EXTRACTION.

Problem: the chunker is speaker-blind — it splits a transcript by size/punctuation,
so each chunk mixes ALL speakers. For a multi-person call routed to a single
person slug, the DNA extractor then attributes EVERYONE's statements to that slug.
Re-ingesting a guest call (a 4-person call dominated by the founder)
produced a guest's DNA full of the founder's pitch instead of the guest's.

Fix: before chunking a transcript for a person-routed slug, keep ONLY the target
speaker's turns. Single-speaker transcripts (courses, monologue podcasts) are a
no-op (the <2-speakers guard). When the target cannot be confidently matched, fall
back to the FULL transcript (never silently drop everything).

Constraints: leaf module — stdlib only. Self-contained speaker segmenter (does NOT
reuse insight_speaker_linker's regex, which requires uppercase speaker names and
would drop lowercase labels like ``jane doe:``).

Version: 1.0.0
Date: 2026-06-11
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger("mce.speaker_filter")

# A speaker turn starts a line with "<Name>: " where Name starts with a letter
# (so "## 00:00:16" timestamps and "00:00:16" digits are NOT matched) and is
# 2-40 chars of letters/digits/space/.-'_. Case-insensitive on the name itself.
_TURN_RE = re.compile(
    r"^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9\s\.\-'_]{1,39}):\s",
    re.MULTILINE,
)

# STORY-RAW-4: the ingest sidecar writes a provenance header at the TOP of every
# transcript (``Source:``, ``Author:``, ``Subject:``, ``Extracted via:``,
# ``Extracted at:`` — see ingest-with-entity-discovery.py:1013-1021 / 1422-1428).
# Those labels match ``_TURN_RE`` exactly, so a SOLO monologue is mis-detected as
# a 5-speaker call → the target is "not matched" → ``kept_chars=0`` → degraded
# extraction (the Liam "0 insights" bug). These are metadata keys, never speakers:
# turns whose label normalizes to one of these are dropped from segmentation, so a
# solo+header transcript correctly resolves to ``single_or_no_speaker`` (no-op).
# Stored normalized (alphanumerics-only lowercase) to match ``_norm_name`` output.
_METADATA_KEYS = frozenset(
    {
        "source",
        "author",
        "subject",
        "extractedvia",
        "extractedat",
    }
)


def _norm_name(s: str) -> str:
    """Normalize a name to alphanumerics-only lowercase for matching."""
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _is_metadata_label(speaker: str) -> bool:
    """True when a ``Name:`` label is a sidecar-header metadata key, not a speaker.

    Guards the false-positive at its source: a transcript's provenance header
    (``Source:``/``Author:``/``Subject:``/``Extracted via:``/``Extracted at:``)
    must never be counted as a speaker turn. See STORY-RAW-4 / ADR-RAG-006 §4.
    """
    return _norm_name(speaker) in _METADATA_KEYS


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-zà-ÿ0-9]+", (s or "").lower()))


def _name_matches(seg_speaker: str, target: str) -> bool:
    """True when a transcript speaker label refers to the target person.

    Robust to case, accents, and first/last-name subsets ("jane doe" vs
    "Jane Doe"; "jane" vs "Jane Doe").
    """
    a, b = _norm_name(seg_speaker), _norm_name(target)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    at, bt = _tokens(seg_speaker), _tokens(target)
    if not at or not bt:
        return False
    common = at & bt
    # Match when one name's tokens are a subset of the other (e.g. "jane"
    # ⊆ "jane doe"), or when 2+ name tokens overlap.
    return bool(common) and (at <= bt or bt <= at or len(common) >= 2)


def segment_by_speaker(text: str) -> list[dict[str, str]]:
    """Split a transcript into ``{speaker, text}`` turns by ``Name:`` markers.

    STORY-RAW-4: turns whose label is a sidecar-header metadata key
    (``Source:``/``Author:``/``Subject:``/``Extracted via:``/``Extracted at:``)
    are skipped — they are provenance metadata, not speakers. This keeps a solo
    transcript with the standard header a single-speaker source (no-op) instead
    of a false multi-speaker call.
    """
    matches = list(_TURN_RE.finditer(text))
    segments: list[dict[str, str]] = []
    for i, m in enumerate(matches):
        speaker = m.group(1).strip()
        if _is_metadata_label(speaker):
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        segments.append({"speaker": speaker, "text": body})
    return segments


def distinct_speakers(segments: list[dict[str, str]]) -> set[str]:
    return {_norm_name(s["speaker"]) for s in segments if _norm_name(s["speaker"])}


def filter_transcript_to_speaker(
    text: str,
    target_display_name: str,
    *,
    min_keep_ratio: float = 0.04,
    min_keep_chars: int = 150,
) -> tuple[str, dict]:
    """Return only *target_display_name*'s turns from a multi-speaker transcript.

    Returns ``(filtered_text, stats)``. ``stats["applied"]`` is False (and the
    original text is returned unchanged) when:
      - fewer than 2 distinct speakers are detected (single-speaker source), or
      - the target speaker cannot be matched / yields too little text
        (below ``max(min_keep_chars, min_keep_ratio * len(text))``).

    Never returns empty/near-empty text — falling back to the full transcript is
    always safer than silently dropping the person's content.
    """
    segments = segment_by_speaker(text)
    speakers = distinct_speakers(segments)

    if len(speakers) < 2:
        return text, {
            "applied": False,
            "reason": "single_or_no_speaker",
            "n_speakers": len(speakers),
        }

    kept = [s for s in segments if _name_matches(s["speaker"], target_display_name)]
    kept_text = "\n".join(f"{s['speaker']}: {s['text']}" for s in kept if s["text"])

    threshold = max(min_keep_chars, int(len(text) * min_keep_ratio))
    if not kept or len(kept_text) < threshold:
        logger.warning(
            "[speaker-filter] target=%r not confidently matched in transcript "
            "(speakers=%s, kept_chars=%d, threshold=%d) — falling back to FULL text",
            target_display_name,
            sorted(speakers),
            len(kept_text),
            threshold,
        )
        return text, {
            "applied": False,
            "reason": "target_not_matched_or_too_short",
            "target": target_display_name,
            "speakers": sorted(speakers),
            "kept_chars": len(kept_text),
            "threshold": threshold,
        }

    return kept_text, {
        "applied": True,
        "target": target_display_name,
        "kept_segments": len(kept),
        "total_segments": len(segments),
        "kept_chars": len(kept_text),
        "total_chars": len(text),
        "speakers": sorted(speakers),
    }
