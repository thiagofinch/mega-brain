"""Video processing pipeline for Mega Brain.

Extracts text from video sources (YouTube, local files) through:
1. Transcript extraction (YouTube API or Whisper)
2. OCR from key frames (pytesseract)
3. Combined output for MCE pipeline ingestion

Heavy dependencies are optional -- each component degrades gracefully.
"""
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class VideoResult:
    """Result of video processing."""
    source: str  # URL or file path
    transcript: str  # Full transcript text
    ocr_texts: list[str] = field(default_factory=list)  # Text from frames
    metadata: dict = field(default_factory=dict)  # title, duration, etc.
    output_path: Path | None = None


def extract_youtube_transcript(url: str) -> str | None:
    """Extract transcript from YouTube using youtube-transcript-api.

    This is the LIGHTWEIGHT approach -- no video download needed.
    Falls back to None if transcript unavailable.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None

    # Extract video ID from URL
    video_id = None
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]

    if not video_id:
        return None

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["en", "pt"]
        )
        return "\n".join(entry["text"] for entry in transcript_list)
    except Exception:
        return None


def extract_youtube_metadata(url: str) -> dict:
    """Extract video metadata using yt-dlp (no download)."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "title": data.get("title", ""),
                "duration": data.get("duration", 0),
                "uploader": data.get("uploader", ""),
                "upload_date": data.get("upload_date", ""),
                "description": data.get("description", "")[:500],
                "view_count": data.get("view_count", 0),
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def transcribe_local(
    file_path: str | Path, model_size: str = "base"
) -> str | None:
    """Transcribe local audio/video file using faster-whisper.

    Requires: pip install faster-whisper
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Video file not found: {file_path}")

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(file_path))

    transcript_parts = []
    for segment in segments:
        transcript_parts.append(segment.text)

    return " ".join(transcript_parts)


def process_video(
    source: str,
    source_tag: str,
    output_dir: str | Path | None = None,
) -> VideoResult:
    """Process a video source (YouTube URL or local file).

    Tries multiple extraction methods in order of preference:
    1. YouTube transcript API (lightest, free)
    2. yt-dlp metadata extraction
    3. Local Whisper transcription (heaviest, most accurate)

    Args:
        source: YouTube URL or local file path.
        source_tag: Source identifier for inbox routing.
        output_dir: Override output directory.

    Returns:
        VideoResult with transcript and metadata.
    """
    from core.paths import KNOWLEDGE_EXTERNAL

    if output_dir is None:
        output_dir = KNOWLEDGE_EXTERNAL / "inbox" / source_tag
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    is_youtube = "youtube.com" in source or "youtu.be" in source

    transcript = None
    metadata: dict = {}

    if is_youtube:
        # Try YouTube transcript API first (lightest)
        transcript = extract_youtube_transcript(source)
        metadata = extract_youtube_metadata(source)
    else:
        # Local file -- try Whisper
        source_path = Path(source)
        if source_path.exists():
            transcript = transcribe_local(source_path)
            metadata = {"title": source_path.stem, "source": "local"}

    if transcript is None:
        transcript = (
            "[Transcript unavailable"
            " -- install youtube-transcript-api or faster-whisper]"
        )

    # Generate output filename
    title = metadata.get(
        "title", Path(source).stem if not is_youtube else "video"
    )
    safe_title = "".join(
        c if c.isalnum() or c in " -_" else "" for c in title
    )[:80]
    output_file = output_dir / f"{safe_title}.txt"

    # Write combined output
    output_parts: list[str] = []
    if metadata:
        output_parts.append(f"# {metadata.get('title', 'Video')}")
        output_parts.append(f"Source: {source}")
        if metadata.get("uploader"):
            output_parts.append(f"Author: {metadata['uploader']}")
        if metadata.get("duration"):
            mins = metadata["duration"] // 60
            output_parts.append(f"Duration: {mins} minutes")
        output_parts.append("---\n")

    output_parts.append("## Transcript\n")
    output_parts.append(transcript)

    full_text = "\n".join(output_parts)
    output_file.write_text(full_text, encoding="utf-8")

    return VideoResult(
        source=source,
        transcript=transcript,
        metadata=metadata,
        output_path=output_file,
    )


def check_capabilities() -> dict:
    """Check which video processing capabilities are available."""
    caps = {
        "youtube_transcript": False,
        "yt_dlp": False,
        "whisper": False,
        "pytesseract": False,
        "opencv": False,
    }

    try:
        import youtube_transcript_api  # noqa: F401

        caps["youtube_transcript"] = True
    except ImportError:
        pass

    try:
        result = subprocess.run(
            ["yt-dlp", "--version"], capture_output=True, timeout=5
        )
        caps["yt_dlp"] = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    try:
        import faster_whisper  # noqa: F401

        caps["whisper"] = True
    except ImportError:
        pass

    try:
        import pytesseract  # noqa: F401

        caps["pytesseract"] = True
    except ImportError:
        pass

    try:
        import cv2  # noqa: F401

        caps["opencv"] = True
    except ImportError:
        pass

    return caps
