"""
Tests for Skill Seekers Bridge — subprocess wrapper for Mega Brain pipeline.
=============================================================================
ALL MOCKED. No real Skill Seekers CLI calls, no real filesystem outside tmp_path.

Tests cover:
- Availability checks (is_ss_available, is_ss_video_available)
- PDF ingestion (with SS, with fallback, error cases)
- DOCX ingestion (with SS, with fallback, error cases)
- Video ingestion (URL parsing, local file, error cases)
- Website ingestion
- Configuration loading
- Utility functions (version, status)
- Low-level call_ss wrapper
- Output path resolution
- Operation logging
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers: patch core.paths at module level to avoid import-time side effects
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate_ss_bridge(tmp_path, monkeypatch):
    """Isolate ss_bridge from real filesystem and clear config cache."""
    root = tmp_path / "mega-brain"
    root.mkdir()

    knowledge_ext = root / "knowledge" / "external"
    knowledge_biz = root / "knowledge" / "business"
    knowledge_per = root / "knowledge" / "personal"
    for d in [knowledge_ext, knowledge_biz, knowledge_per]:
        (d / "inbox").mkdir(parents=True, exist_ok=True)

    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Patch core.paths constants used by ss_bridge
    import core.intelligence.pipeline.ss_bridge as bridge_mod

    monkeypatch.setattr(bridge_mod, "KNOWLEDGE_EXTERNAL", knowledge_ext)
    monkeypatch.setattr(bridge_mod, "KNOWLEDGE_BUSINESS", knowledge_biz)
    monkeypatch.setattr(bridge_mod, "KNOWLEDGE_PERSONAL", knowledge_per)
    monkeypatch.setattr(bridge_mod, "_CONFIG_PATH", None)
    monkeypatch.setattr(bridge_mod, "_LOG_PATH", logs_dir / "ss-bridge.jsonl")

    # Clear cached config between tests
    if hasattr(bridge_mod._get_config, "_cache"):
        del bridge_mod._get_config._cache

    yield


# ---------------------------------------------------------------------------
# Availability checks
# ---------------------------------------------------------------------------


class TestIsSSAvailable:
    """Tests for is_ss_available()."""

    def test_returns_false_when_venv_missing(self, tmp_path, monkeypatch):
        """If venv directory does not exist, SS is not available."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "_get_venv_path", lambda: tmp_path / "no-such-venv")
        assert mod.is_ss_available() is False

    def test_returns_false_when_python_missing(self, tmp_path, monkeypatch):
        """If venv exists but python binary is missing, SS is not available."""
        import core.intelligence.pipeline.ss_bridge as mod

        venv = tmp_path / "fake-venv"
        venv.mkdir()
        monkeypatch.setattr(mod, "_get_venv_path", lambda: venv)
        assert mod.is_ss_available() is False

    def test_returns_false_when_import_fails(self, tmp_path, monkeypatch):
        """If python exists but skill_seekers cannot be imported, returns False."""
        import core.intelligence.pipeline.ss_bridge as mod

        venv = tmp_path / "fake-venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").touch()
        monkeypatch.setattr(mod, "_get_venv_path", lambda: venv)

        failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="ModuleNotFoundError")
        with patch.object(subprocess, "run", return_value=failed):
            assert mod.is_ss_available() is False

    def test_returns_true_when_import_succeeds(self, tmp_path, monkeypatch):
        """If python exists and skill_seekers can be imported, returns True."""
        import core.intelligence.pipeline.ss_bridge as mod

        venv = tmp_path / "fake-venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").touch()
        monkeypatch.setattr(mod, "_get_venv_path", lambda: venv)

        success = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok\n", stderr="")
        with patch.object(subprocess, "run", return_value=success):
            assert mod.is_ss_available() is True

    def test_returns_false_on_timeout(self, tmp_path, monkeypatch):
        """If subprocess times out, returns False gracefully."""
        import core.intelligence.pipeline.ss_bridge as mod

        venv = tmp_path / "fake-venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").touch()
        monkeypatch.setattr(mod, "_get_venv_path", lambda: venv)

        with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=10)):
            assert mod.is_ss_available() is False


class TestIsSSVideoAvailable:
    """Tests for is_ss_video_available()."""

    def test_returns_false_when_ss_not_available(self, monkeypatch):
        """If base SS is not available, video is also not available."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_available", lambda: False)
        assert mod.is_ss_video_available() is False

    def test_returns_true_when_torch_and_whisper_present(self, tmp_path, monkeypatch):
        """Returns True when torch and faster_whisper importable."""
        import core.intelligence.pipeline.ss_bridge as mod

        venv = tmp_path / "fake-venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").touch()
        monkeypatch.setattr(mod, "_get_venv_path", lambda: venv)
        monkeypatch.setattr(mod, "is_ss_available", lambda: True)

        success = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok\n", stderr="")
        with patch.object(subprocess, "run", return_value=success):
            assert mod.is_ss_video_available() is True

    def test_returns_false_when_torch_missing(self, tmp_path, monkeypatch):
        """Returns False when torch cannot be imported."""
        import core.intelligence.pipeline.ss_bridge as mod

        venv = tmp_path / "fake-venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").touch()
        monkeypatch.setattr(mod, "_get_venv_path", lambda: venv)
        monkeypatch.setattr(mod, "is_ss_available", lambda: True)

        failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="No module named 'torch'")
        with patch.object(subprocess, "run", return_value=failed):
            assert mod.is_ss_video_available() is False


# ---------------------------------------------------------------------------
# call_ss (low-level wrapper)
# ---------------------------------------------------------------------------


class TestCallSS:
    """Tests for the low-level call_ss() function."""

    def test_raises_runtime_error_when_ss_unavailable(self, monkeypatch):
        """Should raise RuntimeError when SS is not installed."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_available", lambda: False)
        with pytest.raises(RuntimeError, match="not installed"):
            mod.call_ss(["skill-seekers-pdf", "test.pdf"])

    def test_calls_subprocess_with_correct_env(self, tmp_path, monkeypatch):
        """Should set PATH and VIRTUAL_ENV to SS venv."""
        import core.intelligence.pipeline.ss_bridge as mod

        venv = tmp_path / "ss-venv"
        (venv / "bin").mkdir(parents=True)
        monkeypatch.setattr(mod, "is_ss_available", lambda: True)
        monkeypatch.setattr(mod, "_get_venv_path", lambda: venv)
        monkeypatch.setattr(mod, "_get_timeout", lambda: 60)

        captured_kwargs = {}

        def fake_run(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="ok", stderr="")

        with patch.object(subprocess, "run", side_effect=fake_run):
            mod.call_ss(["skill-seekers-pdf", "test.pdf"])

        env = captured_kwargs["env"]
        assert str(venv / "bin") in env["PATH"]
        assert env["VIRTUAL_ENV"] == str(venv)
        assert "PYTHONHOME" not in env

    def test_uses_configured_timeout(self, tmp_path, monkeypatch):
        """Should use timeout from configuration."""
        import core.intelligence.pipeline.ss_bridge as mod

        venv = tmp_path / "ss-venv"
        (venv / "bin").mkdir(parents=True)
        monkeypatch.setattr(mod, "is_ss_available", lambda: True)
        monkeypatch.setattr(mod, "_get_venv_path", lambda: venv)
        monkeypatch.setattr(mod, "_get_timeout", lambda: 42)

        captured_kwargs = {}

        def fake_run(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="", stderr="")

        with patch.object(subprocess, "run", side_effect=fake_run):
            mod.call_ss(["test-cmd"])

        assert captured_kwargs["timeout"] == 42

    def test_explicit_timeout_overrides_config(self, tmp_path, monkeypatch):
        """Explicit timeout parameter should override config value."""
        import core.intelligence.pipeline.ss_bridge as mod

        venv = tmp_path / "ss-venv"
        (venv / "bin").mkdir(parents=True)
        monkeypatch.setattr(mod, "is_ss_available", lambda: True)
        monkeypatch.setattr(mod, "_get_venv_path", lambda: venv)
        monkeypatch.setattr(mod, "_get_timeout", lambda: 300)

        captured_kwargs = {}

        def fake_run(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="", stderr="")

        with patch.object(subprocess, "run", side_effect=fake_run):
            mod.call_ss(["test-cmd"], timeout=99)

        assert captured_kwargs["timeout"] == 99


# ---------------------------------------------------------------------------
# Output path resolution
# ---------------------------------------------------------------------------


class TestResolveOutputPath:
    """Tests for _resolve_output_path()."""

    def test_external_bucket_default(self):
        """Default bucket should be external."""
        import core.intelligence.pipeline.ss_bridge as mod

        result = mod._resolve_output_path("alex-hormozi", "test.md")
        assert "external" in str(result)
        assert "inbox" in str(result)
        assert "alex-hormozi" in str(result)
        assert result.name == "test.md"

    def test_business_bucket(self):
        """Should route to business bucket."""
        import core.intelligence.pipeline.ss_bridge as mod

        result = mod._resolve_output_path("team-meeting", "notes.md", bucket="business")
        assert "business" in str(result)
        assert "inbox" in str(result)

    def test_personal_bucket(self):
        """Should route to personal bucket."""
        import core.intelligence.pipeline.ss_bridge as mod

        result = mod._resolve_output_path("journal", "entry.md", bucket="personal")
        assert "personal" in str(result)

    def test_creates_directory_if_missing(self, tmp_path):
        """Output directory should be created automatically."""
        import core.intelligence.pipeline.ss_bridge as mod

        result = mod._resolve_output_path("new-source", "file.md")
        assert result.parent.exists()

    def test_unknown_bucket_falls_back_to_external(self):
        """Unknown bucket should default to external."""
        import core.intelligence.pipeline.ss_bridge as mod

        result = mod._resolve_output_path("tag", "f.md", bucket="nonexistent")
        assert "external" in str(result)


# ---------------------------------------------------------------------------
# PDF ingestion
# ---------------------------------------------------------------------------


class TestIngestPdf:
    """Tests for ingest_pdf()."""

    def test_raises_file_not_found_for_missing_pdf(self, tmp_path):
        """Should raise FileNotFoundError when PDF does not exist."""
        import core.intelligence.pipeline.ss_bridge as mod

        with pytest.raises(FileNotFoundError, match="PDF not found"):
            mod.ingest_pdf(tmp_path / "nonexistent.pdf", "test-tag")

    def test_successful_ss_extraction(self, tmp_path, monkeypatch):
        """Should call SS and return output path on success."""
        import core.intelligence.pipeline.ss_bridge as mod

        pdf = tmp_path / "document.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake pdf content")

        monkeypatch.setattr(mod, "is_ss_available", lambda: True)

        success = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
        with patch.object(mod, "call_ss", return_value=success) as mock_call:
            result = mod.ingest_pdf(pdf, "alex-hormozi")

        assert result.name == "document.md"
        assert "alex-hormozi" in str(result)
        mock_call.assert_called_once()
        args = mock_call.call_args[0][0]
        assert "skill-seekers-pdf" in args[0]

    def test_falls_back_to_extractor_when_ss_unavailable(self, tmp_path, monkeypatch):
        """Should use fallback extractor when SS is not installed."""
        import core.intelligence.pipeline.ss_bridge as mod

        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        monkeypatch.setattr(mod, "is_ss_available", lambda: False)
        monkeypatch.setattr(mod, "_is_fallback_enabled", lambda: True)

        # Mock the fallback extractor
        mock_extract = MagicMock(return_value="Extracted text from PDF")
        with patch.dict("sys.modules", {}):
            with patch("core.intelligence.pipeline.extractors.extract_pdf", mock_extract, create=True):
                result = mod.ingest_pdf(pdf, "test-tag", use_fallback=True)

        assert result.name == "doc.md"

    def test_raises_when_ss_unavailable_and_fallback_disabled(self, tmp_path, monkeypatch):
        """Should raise RuntimeError when SS not available and fallback disabled."""
        import core.intelligence.pipeline.ss_bridge as mod

        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        monkeypatch.setattr(mod, "is_ss_available", lambda: False)
        monkeypatch.setattr(mod, "_is_fallback_enabled", lambda: False)

        with pytest.raises(RuntimeError, match="fallback disabled"):
            mod.ingest_pdf(pdf, "tag", use_fallback=False)

    def test_falls_back_when_ss_command_fails(self, tmp_path, monkeypatch):
        """Should try fallback if SS returns non-zero exit code."""
        import core.intelligence.pipeline.ss_bridge as mod

        pdf = tmp_path / "broken.pdf"
        pdf.write_bytes(b"%PDF-1.4 broken")

        monkeypatch.setattr(mod, "is_ss_available", lambda: True)
        monkeypatch.setattr(mod, "_is_fallback_enabled", lambda: True)

        failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="parse error")
        mock_extract = MagicMock(return_value="Fallback text")

        with patch.object(mod, "call_ss", return_value=failed):
            with patch("core.intelligence.pipeline.extractors.extract_pdf", mock_extract, create=True):
                result = mod.ingest_pdf(pdf, "tag")

        assert result.name == "broken.md"


# ---------------------------------------------------------------------------
# DOCX ingestion
# ---------------------------------------------------------------------------


class TestIngestDocx:
    """Tests for ingest_docx()."""

    def test_raises_file_not_found_for_missing_docx(self, tmp_path):
        """Should raise FileNotFoundError for missing DOCX."""
        import core.intelligence.pipeline.ss_bridge as mod

        with pytest.raises(FileNotFoundError, match="DOCX not found"):
            mod.ingest_docx(tmp_path / "missing.docx", "tag")

    def test_successful_docx_extraction(self, tmp_path, monkeypatch):
        """Should call SS with docx command and return output path."""
        import core.intelligence.pipeline.ss_bridge as mod

        docx = tmp_path / "notes.docx"
        docx.write_bytes(b"PK fake docx")

        monkeypatch.setattr(mod, "is_ss_available", lambda: True)

        success = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
        with patch.object(mod, "call_ss", return_value=success) as mock_call:
            result = mod.ingest_docx(docx, "cole-gordon")

        assert result.name == "notes.md"
        assert "cole-gordon" in str(result)
        args = mock_call.call_args[0][0]
        assert "skill-seekers-word" in args[0]

    def test_docx_business_bucket(self, tmp_path, monkeypatch):
        """Should route DOCX output to business bucket."""
        import core.intelligence.pipeline.ss_bridge as mod

        docx = tmp_path / "meeting.docx"
        docx.write_bytes(b"PK fake")

        monkeypatch.setattr(mod, "is_ss_available", lambda: True)

        success = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
        with patch.object(mod, "call_ss", return_value=success):
            result = mod.ingest_docx(docx, "weekly", bucket="business")

        assert "business" in str(result)


# ---------------------------------------------------------------------------
# Video ingestion
# ---------------------------------------------------------------------------


class TestIngestVideo:
    """Tests for ingest_video()."""

    def test_raises_when_video_support_missing(self, monkeypatch):
        """Should raise RuntimeError when SS video not available."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_video_available", lambda: False)

        with pytest.raises(RuntimeError, match="video support not installed"):
            mod.ingest_video("https://youtube.com/watch?v=abc123defgh", "test")

    def test_youtube_url_extracts_video_id(self, tmp_path, monkeypatch):
        """Should extract video ID from YouTube URL for filename."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_video_available", lambda: True)

        success = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
        with patch.object(mod, "call_ss", return_value=success) as mock_call:
            result = mod.ingest_video("https://youtube.com/watch?v=abc123defgh", "hormozi")

        assert "abc123defgh" in result.name
        assert result.name.endswith("_transcript.md")
        mock_call.assert_called_once()

    def test_local_file_raises_for_missing(self, monkeypatch):
        """Should raise FileNotFoundError for missing local video file."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_video_available", lambda: True)

        with pytest.raises(FileNotFoundError, match="Video not found"):
            mod.ingest_video("/tmp/nonexistent-video.mp4", "tag")

    def test_local_file_uses_stem_for_filename(self, tmp_path, monkeypatch):
        """Should use file stem for local video output filename."""
        import core.intelligence.pipeline.ss_bridge as mod

        video = tmp_path / "lecture.mp4"
        video.write_bytes(b"fake video data")

        monkeypatch.setattr(mod, "is_ss_video_available", lambda: True)

        success = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
        with patch.object(mod, "call_ss", return_value=success):
            result = mod.ingest_video(str(video), "course")

        assert result.name == "lecture_transcript.md"

    def test_raises_on_nonzero_exit(self, monkeypatch):
        """Should raise RuntimeError when SS video command fails."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_video_available", lambda: True)

        failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="ffmpeg error")
        with patch.object(mod, "call_ss", return_value=failed):
            with pytest.raises(RuntimeError, match="Video ingestion failed"):
                mod.ingest_video("https://youtube.com/watch?v=test12345ab", "tag")

    def test_raises_on_timeout(self, monkeypatch):
        """Should raise RuntimeError on timeout."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_video_available", lambda: True)

        with patch.object(mod, "call_ss", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=300)):
            with pytest.raises(RuntimeError, match="timed out"):
                mod.ingest_video("https://youtube.com/watch?v=test12345ab", "tag")


# ---------------------------------------------------------------------------
# Website ingestion
# ---------------------------------------------------------------------------


class TestIngestWebsite:
    """Tests for ingest_website()."""

    def test_raises_when_ss_unavailable(self, monkeypatch):
        """Should raise RuntimeError when SS is not installed."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_available", lambda: False)

        with pytest.raises(RuntimeError, match="not installed"):
            mod.ingest_website("https://example.com", "example")

    def test_generates_hash_based_filename(self, monkeypatch):
        """Should generate deterministic filename from URL hash."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_available", lambda: True)

        success = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
        with patch.object(mod, "call_ss", return_value=success):
            result = mod.ingest_website("https://example.com/page", "example")

        assert result.name.startswith("web_")
        assert result.name.endswith(".md")
        assert len(result.name) > len("web_.md")  # hash is present

    def test_same_url_produces_same_filename(self, monkeypatch):
        """Same URL should produce same output filename (deterministic)."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_available", lambda: True)

        success = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
        with patch.object(mod, "call_ss", return_value=success):
            result1 = mod.ingest_website("https://example.com/page", "tag")
            result2 = mod.ingest_website("https://example.com/page", "tag")

        assert result1.name == result2.name


# ---------------------------------------------------------------------------
# Configuration loading
# ---------------------------------------------------------------------------


class TestConfiguration:
    """Tests for config loading and defaults."""

    def test_defaults_when_no_config_file(self, monkeypatch):
        """Should use default config when no YAML file exists."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "_CONFIG_PATH", None)
        if hasattr(mod._get_config, "_cache"):
            del mod._get_config._cache

        config = mod._load_config()
        assert config["skill_seekers"]["venv_path"] == "~/.venvs/skill-seekers"
        assert config["skill_seekers"]["timeout_seconds"] == 300
        assert config["commands"]["pdf"] == "skill-seekers-pdf"

    def test_loads_yaml_when_present(self, tmp_path, monkeypatch):
        """Should load config from YAML file when it exists."""
        import core.intelligence.pipeline.ss_bridge as mod

        config_file = tmp_path / "ss_config.yaml"
        config_file.write_text(
            "skill_seekers:\n"
            "  venv_path: /custom/path\n"
            "  timeout_seconds: 600\n"
            "commands:\n"
            "  pdf: custom-pdf-cmd\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(mod, "_CONFIG_PATH", config_file)
        if hasattr(mod._get_config, "_cache"):
            del mod._get_config._cache

        config = mod._load_config()
        assert config["skill_seekers"]["venv_path"] == "/custom/path"
        assert config["skill_seekers"]["timeout_seconds"] == 600
        assert config["commands"]["pdf"] == "custom-pdf-cmd"

    def test_config_is_cached(self, monkeypatch):
        """Config should be cached after first load."""
        import core.intelligence.pipeline.ss_bridge as mod

        if hasattr(mod._get_config, "_cache"):
            del mod._get_config._cache

        config1 = mod._get_config()
        config2 = mod._get_config()
        assert config1 is config2

    def test_get_command_returns_default_for_unknown(self, monkeypatch):
        """Should return skill-seekers-{type} for unknown command types."""
        import core.intelligence.pipeline.ss_bridge as mod

        if hasattr(mod._get_config, "_cache"):
            del mod._get_config._cache

        result = mod._get_command("unknown-type")
        assert result == "skill-seekers-unknown-type"


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


class TestUtilities:
    """Tests for get_ss_version() and get_bridge_status()."""

    def test_version_returns_none_when_unavailable(self, monkeypatch):
        """Should return None when SS is not available."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_available", lambda: False)
        assert mod.get_ss_version() is None

    def test_version_returns_string_when_available(self, tmp_path, monkeypatch):
        """Should return version string on success."""
        import core.intelligence.pipeline.ss_bridge as mod

        venv = tmp_path / "venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").touch()
        monkeypatch.setattr(mod, "_get_venv_path", lambda: venv)
        monkeypatch.setattr(mod, "is_ss_available", lambda: True)

        success = subprocess.CompletedProcess(args=[], returncode=0, stdout="1.2.3\n", stderr="")
        with patch.object(subprocess, "run", return_value=success):
            assert mod.get_ss_version() == "1.2.3"

    def test_bridge_status_returns_dict(self, monkeypatch):
        """get_bridge_status() should return a dict with expected keys."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_available", lambda: False)
        monkeypatch.setattr(mod, "is_ss_video_available", lambda: False)
        monkeypatch.setattr(mod, "get_ss_version", lambda: None)

        status = mod.get_bridge_status()
        assert isinstance(status, dict)
        assert "ss_available" in status
        assert "ss_video_available" in status
        assert "ss_version" in status
        assert "venv_path" in status
        assert "fallback_enabled" in status
        assert "timeout_seconds" in status

    def test_bridge_status_reflects_availability(self, monkeypatch):
        """Status should reflect actual availability state."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "is_ss_available", lambda: True)
        monkeypatch.setattr(mod, "is_ss_video_available", lambda: True)
        monkeypatch.setattr(mod, "get_ss_version", lambda: "2.0.0")

        status = mod.get_bridge_status()
        assert status["ss_available"] is True
        assert status["ss_video_available"] is True
        assert status["ss_version"] == "2.0.0"


# ---------------------------------------------------------------------------
# Operation logging
# ---------------------------------------------------------------------------


class TestOperationLogging:
    """Tests for _log_operation() JSONL logging."""

    def test_writes_jsonl_entry(self, tmp_path, monkeypatch):
        """Should append JSONL entry to log file."""
        import core.intelligence.pipeline.ss_bridge as mod

        log_file = tmp_path / "ss-bridge.jsonl"
        monkeypatch.setattr(mod, "_LOG_PATH", log_file)

        mod._log_operation(
            "ingest_pdf",
            success=True,
            input_path="/tmp/test.pdf",
            output_path="/tmp/out.md",
            duration_ms=150,
        )

        assert log_file.exists()
        entry = json.loads(log_file.read_text(encoding="utf-8").strip())
        assert entry["operation"] == "ingest_pdf"
        assert entry["success"] is True
        assert entry["input"] == "/tmp/test.pdf"
        assert entry["duration_ms"] == 150

    def test_does_nothing_when_log_path_none(self, monkeypatch):
        """Should silently skip when _LOG_PATH is None."""
        import core.intelligence.pipeline.ss_bridge as mod

        monkeypatch.setattr(mod, "_LOG_PATH", None)
        # Should not raise
        mod._log_operation("test", success=True)

    def test_logs_error_entry(self, tmp_path, monkeypatch):
        """Should log error information."""
        import core.intelligence.pipeline.ss_bridge as mod

        log_file = tmp_path / "ss-bridge.jsonl"
        monkeypatch.setattr(mod, "_LOG_PATH", log_file)

        mod._log_operation("ingest_pdf", success=False, error="File not found")

        entry = json.loads(log_file.read_text(encoding="utf-8").strip())
        assert entry["success"] is False
        assert entry["error"] == "File not found"

    def test_appends_multiple_entries(self, tmp_path, monkeypatch):
        """Should append, not overwrite, log entries."""
        import core.intelligence.pipeline.ss_bridge as mod

        log_file = tmp_path / "ss-bridge.jsonl"
        monkeypatch.setattr(mod, "_LOG_PATH", log_file)

        mod._log_operation("op1", success=True)
        mod._log_operation("op2", success=False, error="boom")

        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["operation"] == "op1"
        assert json.loads(lines[1])["operation"] == "op2"
