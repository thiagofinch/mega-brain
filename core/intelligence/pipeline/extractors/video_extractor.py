"""
Video Extractor — Transcription extraction from video files.
=============================================================

This module provides video transcription using Skill Seekers (when available)
or returns instructions for manual processing when SS video support is not
installed.

Video support requires heavy dependencies (~2GB for PyTorch + faster-whisper),
so it's kept separate from the base extractors.

Usage:
    from core.intelligence.pipeline.extractors.video_extractor import (
        extract_video,
        is_video_support_available,
    )

    if is_video_support_available():
        transcript_path = extract_video("https://youtube.com/watch?v=xxx", "alex-hormozi")
    else:
        print("Run bin/install-skill-seekers-video.sh to enable video support")

Version: 1.0.0
Date: 2026-03-14
Story: Plan 2 — Skill Seekers Integration
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


def is_video_support_available() -> bool:
    """Check if video transcription support is available.

    Returns:
        True if SS video support is installed and working.
    """
    try:
        from core.intelligence.pipeline.ss_bridge import is_ss_video_available
        return is_ss_video_available()
    except ImportError:
        return False


def extract_video(
    url_or_path: str,
    source_tag: str,
    bucket: Literal["external", "business", "personal"] = "external",
) -> Path:
    """Extract transcript from a video (YouTube URL or local file).

    Args:
        url_or_path: YouTube URL or path to local video file
        source_tag: Source identifier for organization
        bucket: Knowledge bucket for output

    Returns:
        Path to generated transcript markdown file

    Raises:
        RuntimeError: If video support is not available
        FileNotFoundError: If local file doesn't exist
    """
    from core.intelligence.pipeline.ss_bridge import ingest_video, is_ss_video_available

    if not is_ss_video_available():
        raise RuntimeError(
            "Video support not available. "
            "Run bin/install-skill-seekers-video.sh to install."
        )

    return ingest_video(url_or_path, source_tag, bucket)


def extract_youtube(
    url: str,
    source_tag: str,
    bucket: Literal["external", "business", "personal"] = "external",
) -> Path:
    """Extract transcript from a YouTube video.

    Convenience wrapper that validates YouTube URL format.

    Args:
        url: YouTube video URL
        source_tag: Source identifier for organization
        bucket: Knowledge bucket for output

    Returns:
        Path to generated transcript markdown file

    Raises:
        ValueError: If URL is not a valid YouTube URL
        RuntimeError: If video support is not available
    """
    # Validate YouTube URL
    youtube_patterns = [
        r"youtube\.com/watch\?v=",
        r"youtu\.be/",
        r"youtube\.com/embed/",
        r"youtube\.com/v/",
    ]

    is_youtube = any(re.search(p, url) for p in youtube_patterns)
    if not is_youtube:
        raise ValueError(f"Not a valid YouTube URL: {url}")

    return extract_video(url, source_tag, bucket)


def extract_local_video(
    filepath: Path,
    source_tag: str,
    bucket: Literal["external", "business", "personal"] = "external",
) -> Path:
    """Extract transcript from a local video file.

    Args:
        filepath: Path to video file (mp4, webm, etc.)
        source_tag: Source identifier for organization
        bucket: Knowledge bucket for output

    Returns:
        Path to generated transcript markdown file

    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If video support is not available
    """
    filepath = Path(filepath).resolve()
    if not filepath.exists():
        raise FileNotFoundError(f"Video file not found: {filepath}")

    return extract_video(str(filepath), source_tag, bucket)


def get_video_status() -> dict:
    """Get current video extraction capability status.

    Returns:
        Dict with availability info and installation instructions.
    """
    available = is_video_support_available()

    status = {
        "available": available,
        "supports_youtube": available,
        "supports_local_files": available,
    }

    if not available:
        status["installation"] = {
            "command": "bin/install-skill-seekers-video.sh",
            "note": "Adds ~2GB of dependencies (PyTorch, faster-whisper)",
            "prerequisite": "Run bin/install-skill-seekers.sh first",
        }
    else:
        # Get more details from ss_bridge
        try:
            from core.intelligence.pipeline.ss_bridge import get_bridge_status
            bridge_status = get_bridge_status()
            status["ss_version"] = bridge_status.get("ss_version")
            status["venv_path"] = bridge_status.get("venv_path")
        except ImportError:
            pass

    return status


# ── CLI ─────────────────────────────────────────────────────────────────────

def main() -> int:
    """CLI entry point for video extraction.

    Usage:
        python video_extractor.py status
        python video_extractor.py <youtube_url> <source_tag>
        python video_extractor.py <local_file> <source_tag>
    """
    import sys
    import json

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if len(sys.argv) < 2:
        status = get_video_status()
        print(json.dumps(status, indent=2))
        return 0

    cmd = sys.argv[1]

    if cmd == "status":
        status = get_video_status()
        print(json.dumps(status, indent=2))
        return 0

    if len(sys.argv) < 3:
        print("Usage: python video_extractor.py <url_or_path> <source_tag>")
        return 1

    url_or_path = sys.argv[1]
    source_tag = sys.argv[2]

    try:
        output_path = extract_video(url_or_path, source_tag)
        print(f"Transcript saved to: {output_path}")
        return 0
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
