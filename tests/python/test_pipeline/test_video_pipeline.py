"""Tests for the video processing pipeline.

All tests are mocked -- no real video processing, no network calls,
no heavy dependencies required.
"""
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.intelligence.pipeline.video.pipeline import (
    VideoResult,
    check_capabilities,
    extract_youtube_metadata,
    extract_youtube_transcript,
    process_video,
    transcribe_local,
)


# ---------------------------------------------------------------------------
# VideoResult dataclass
# ---------------------------------------------------------------------------

class TestVideoResult:
    def test_has_correct_fields(self):
        result = VideoResult(source="test.mp4", transcript="hello world")
        assert result.source == "test.mp4"
        assert result.transcript == "hello world"
        assert result.ocr_texts == []
        assert result.metadata == {}
        assert result.output_path is None

    def test_custom_fields(self):
        result = VideoResult(
            source="https://youtube.com/watch?v=abc",
            transcript="text",
            ocr_texts=["slide 1"],
            metadata={"title": "My Video"},
            output_path=Path("/tmp/out.txt"),
        )
        assert result.ocr_texts == ["slide 1"]
        assert result.metadata["title"] == "My Video"
        assert result.output_path == Path("/tmp/out.txt")


# ---------------------------------------------------------------------------
# extract_youtube_transcript
# ---------------------------------------------------------------------------

class TestExtractYoutubeTranscript:
    def test_returns_none_when_lib_not_installed(self):
        """When youtube-transcript-api is not installed, return None."""
        with patch.dict("sys.modules", {"youtube_transcript_api": None}):
            # Force ImportError by making the module None
            import importlib
            import core.intelligence.pipeline.video.pipeline as mod
            importlib.reload(mod)
            # After reload with None module, the import inside the function
            # will raise ImportError -> returns None
            result = mod.extract_youtube_transcript(
                "https://www.youtube.com/watch?v=abc123"
            )
            assert result is None
            # Reload back to normal
            importlib.reload(mod)

    def test_extracts_video_id_from_standard_url(self):
        """Extracts video ID from youtube.com/watch?v=ID format."""
        mock_api = MagicMock()
        mock_api.YouTubeTranscriptApi.get_transcript.return_value = [
            {"text": "Hello"},
            {"text": "World"},
        ]
        with patch.dict("sys.modules", {"youtube_transcript_api": mock_api}):
            import importlib
            import core.intelligence.pipeline.video.pipeline as mod
            importlib.reload(mod)
            result = mod.extract_youtube_transcript(
                "https://www.youtube.com/watch?v=abc123"
            )
            assert result == "Hello\nWorld"
            mock_api.YouTubeTranscriptApi.get_transcript.assert_called_once_with(
                "abc123", languages=["en", "pt"]
            )
            importlib.reload(mod)

    def test_extracts_video_id_from_short_url(self):
        """Extracts video ID from youtu.be/ID format."""
        mock_api = MagicMock()
        mock_api.YouTubeTranscriptApi.get_transcript.return_value = [
            {"text": "Short URL works"},
        ]
        with patch.dict("sys.modules", {"youtube_transcript_api": mock_api}):
            import importlib
            import core.intelligence.pipeline.video.pipeline as mod
            importlib.reload(mod)
            result = mod.extract_youtube_transcript(
                "https://youtu.be/xyz789"
            )
            assert result == "Short URL works"
            mock_api.YouTubeTranscriptApi.get_transcript.assert_called_once_with(
                "xyz789", languages=["en", "pt"]
            )
            importlib.reload(mod)

    def test_extracts_video_id_with_extra_params(self):
        """Handles URLs with extra query parameters after video ID."""
        mock_api = MagicMock()
        mock_api.YouTubeTranscriptApi.get_transcript.return_value = [
            {"text": "Param test"},
        ]
        with patch.dict("sys.modules", {"youtube_transcript_api": mock_api}):
            import importlib
            import core.intelligence.pipeline.video.pipeline as mod
            importlib.reload(mod)
            result = mod.extract_youtube_transcript(
                "https://www.youtube.com/watch?v=abc123&list=PLxyz&t=120"
            )
            assert result == "Param test"
            mock_api.YouTubeTranscriptApi.get_transcript.assert_called_once_with(
                "abc123", languages=["en", "pt"]
            )
            importlib.reload(mod)

    def test_returns_none_for_invalid_url(self):
        """Returns None for URLs without a video ID."""
        result = extract_youtube_transcript("https://example.com/no-video")
        assert result is None


# ---------------------------------------------------------------------------
# extract_youtube_metadata
# ---------------------------------------------------------------------------

class TestExtractYoutubeMetadata:
    def test_returns_empty_dict_when_ytdlp_not_found(self):
        """Returns {} when yt-dlp is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = extract_youtube_metadata("https://youtube.com/watch?v=x")
            assert result == {}

    def test_parses_ytdlp_json_output(self):
        """Parses yt-dlp JSON dump correctly."""
        fake_json = {
            "title": "Sales Training 2025",
            "duration": 3600,
            "uploader": "Alex Hormozi",
            "upload_date": "20250101",
            "description": "A great video about sales." * 50,
            "view_count": 1000000,
        }
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(fake_json)

        with patch("subprocess.run", return_value=mock_result):
            result = extract_youtube_metadata(
                "https://youtube.com/watch?v=abc"
            )
            assert result["title"] == "Sales Training 2025"
            assert result["duration"] == 3600
            assert result["uploader"] == "Alex Hormozi"
            assert result["view_count"] == 1000000
            # Description truncated to 500 chars
            assert len(result["description"]) <= 500

    def test_returns_empty_dict_on_timeout(self):
        """Returns {} when yt-dlp times out."""
        with patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired("yt-dlp", 30)
        ):
            result = extract_youtube_metadata("https://youtube.com/watch?v=x")
            assert result == {}

    def test_returns_empty_dict_on_bad_returncode(self):
        """Returns {} when yt-dlp exits with non-zero."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            result = extract_youtube_metadata("https://youtube.com/watch?v=x")
            assert result == {}


# ---------------------------------------------------------------------------
# transcribe_local
# ---------------------------------------------------------------------------

class TestTranscribeLocal:
    def test_returns_none_when_whisper_not_installed(self):
        """Returns None when faster-whisper is not installed."""
        with patch.dict("sys.modules", {"faster_whisper": None}):
            import importlib
            import core.intelligence.pipeline.video.pipeline as mod
            importlib.reload(mod)
            result = mod.transcribe_local("/tmp/fake_video.mp4")
            assert result is None
            importlib.reload(mod)

    def test_raises_file_not_found_for_missing_file(self):
        """Raises FileNotFoundError for non-existent file."""
        mock_whisper = MagicMock()
        with patch.dict("sys.modules", {"faster_whisper": mock_whisper}):
            import importlib
            import core.intelligence.pipeline.video.pipeline as mod
            importlib.reload(mod)
            with pytest.raises(FileNotFoundError, match="Video file not found"):
                mod.transcribe_local("/nonexistent/path/video.mp4")
            importlib.reload(mod)


# ---------------------------------------------------------------------------
# process_video
# ---------------------------------------------------------------------------

class TestProcessVideo:
    def test_youtube_url_tries_transcript_api_first(self, tmp_path):
        """For YouTube URLs, tries transcript API before anything else."""
        mock_api = MagicMock()
        mock_api.YouTubeTranscriptApi.get_transcript.return_value = [
            {"text": "API transcript works"},
        ]
        with patch.dict("sys.modules", {"youtube_transcript_api": mock_api}):
            with patch(
                "core.intelligence.pipeline.video.pipeline.extract_youtube_metadata",
                return_value={"title": "Test Video"},
            ):
                import importlib
                import core.intelligence.pipeline.video.pipeline as mod
                importlib.reload(mod)
                result = mod.process_video(
                    "https://www.youtube.com/watch?v=test123",
                    source_tag="test-source",
                    output_dir=str(tmp_path),
                )
                assert "API transcript works" in result.transcript
                importlib.reload(mod)

    def test_writes_output_file_to_correct_location(self, tmp_path):
        """Output file is written to the specified directory."""
        with patch(
            "core.intelligence.pipeline.video.pipeline.extract_youtube_transcript",
            return_value="Transcript text here",
        ):
            with patch(
                "core.intelligence.pipeline.video.pipeline.extract_youtube_metadata",
                return_value={"title": "My Great Video"},
            ):
                result = process_video(
                    "https://www.youtube.com/watch?v=abc",
                    source_tag="test",
                    output_dir=str(tmp_path),
                )
                assert result.output_path is not None
                assert result.output_path.exists()
                assert result.output_path.parent == tmp_path
                content = result.output_path.read_text()
                assert "Transcript text here" in content

    def test_handles_unavailable_transcript_gracefully(self, tmp_path):
        """When no transcript is available, writes fallback message."""
        with patch(
            "core.intelligence.pipeline.video.pipeline.extract_youtube_transcript",
            return_value=None,
        ):
            with patch(
                "core.intelligence.pipeline.video.pipeline.extract_youtube_metadata",
                return_value={},
            ):
                result = process_video(
                    "https://www.youtube.com/watch?v=nope",
                    source_tag="test",
                    output_dir=str(tmp_path),
                )
                assert "Transcript unavailable" in result.transcript

    def test_local_file_with_no_whisper(self, tmp_path):
        """Local files without Whisper get fallback message."""
        # Create a dummy local file
        dummy = tmp_path / "local_video.mp4"
        dummy.write_bytes(b"fake video data")

        with patch(
            "core.intelligence.pipeline.video.pipeline.transcribe_local",
            return_value=None,
        ):
            output_dir = tmp_path / "output"
            result = process_video(
                str(dummy),
                source_tag="local-test",
                output_dir=str(output_dir),
            )
            assert "Transcript unavailable" in result.transcript
            assert result.output_path is not None
            assert result.output_path.exists()


# ---------------------------------------------------------------------------
# check_capabilities
# ---------------------------------------------------------------------------

class TestCheckCapabilities:
    def test_returns_dict_with_all_keys(self):
        """Result dict has all expected capability keys."""
        result = check_capabilities()
        expected_keys = {
            "youtube_transcript",
            "yt_dlp",
            "whisper",
            "pytesseract",
            "opencv",
        }
        assert set(result.keys()) == expected_keys

    def test_handles_missing_packages_gracefully(self):
        """Does not raise even if all packages are missing."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with patch.dict(
                "sys.modules",
                {
                    "youtube_transcript_api": None,
                    "faster_whisper": None,
                    "pytesseract": None,
                    "cv2": None,
                },
            ):
                import importlib
                import core.intelligence.pipeline.video.pipeline as mod
                importlib.reload(mod)
                result = mod.check_capabilities()
                # yt_dlp should be False (FileNotFoundError)
                assert result["yt_dlp"] is False
                importlib.reload(mod)

    def test_detects_available_yt_dlp(self):
        """Detects yt-dlp when it is installed."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            result = check_capabilities()
            assert result["yt_dlp"] is True
