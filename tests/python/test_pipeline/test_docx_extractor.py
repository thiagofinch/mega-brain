"""Tests for DOCX text extraction module.

Tests cover:
- extract_docx (markdown output)
- extract_docx_raw (plain text output)
- extract_docx_to_inbox (inbox routing)
- Error handling (missing file, missing mammoth)
"""

from __future__ import annotations

# Check if mammoth is available
import importlib.util
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

HAS_MAMMOTH = importlib.util.find_spec("mammoth") is not None

needs_mammoth = pytest.mark.skipif(not HAS_MAMMOTH, reason="mammoth not installed")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _FakeResult:
    """Mimics mammoth's Result object."""

    def __init__(self, value: str, messages=None):
        self.value = value
        self.messages = messages or []


@pytest.fixture()
def fake_mammoth():
    """Create a fake mammoth module with working extract/convert methods."""
    mod = types.ModuleType("mammoth")
    mod.convert_to_html = MagicMock(return_value=_FakeResult("<p>Hello <strong>world</strong></p>"))
    mod.extract_raw_text = MagicMock(return_value=_FakeResult("Hello world"))
    return mod


@pytest.fixture()
def sample_docx(tmp_path: Path) -> Path:
    """Create a minimal .docx file for path-existence tests.

    Note: This is NOT a valid DOCX -- we mock mammoth calls so the
    file content doesn't matter, only its existence on disk.
    """
    docx = tmp_path / "sample.docx"
    docx.write_bytes(b"PK\x03\x04fake-docx-content")
    return docx


# ---------------------------------------------------------------------------
# extract_docx (markdown mode)
# ---------------------------------------------------------------------------


@needs_mammoth
class TestExtractDocx:
    def test_raises_file_not_found(self):
        from core.intelligence.pipeline.extractors.docx_extractor import extract_docx

        with pytest.raises(FileNotFoundError, match="DOCX not found"):
            extract_docx("/nonexistent/path/missing.docx")

    def test_returns_markdown(self, fake_mammoth, sample_docx):
        with patch.dict("sys.modules", {"mammoth": fake_mammoth}):
            # Force reimport so the patched mammoth is picked up
            from core.intelligence.pipeline.extractors import docx_extractor

            # Clear any cached import
            result = docx_extractor.extract_docx(sample_docx)

        assert isinstance(result, str)
        assert "**world**" in result  # markdown bold from <strong>
        assert "sample" in result  # stem in header

    def test_writes_output_file(self, fake_mammoth, sample_docx, tmp_path):
        out = tmp_path / "out" / "result.md"
        with patch.dict("sys.modules", {"mammoth": fake_mammoth}):
            from core.intelligence.pipeline.extractors import docx_extractor

            docx_extractor.extract_docx(sample_docx, out)

        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "**world**" in content

    def test_creates_parent_dirs_for_output(self, fake_mammoth, sample_docx, tmp_path):
        deep_path = tmp_path / "a" / "b" / "c" / "output.md"
        with patch.dict("sys.modules", {"mammoth": fake_mammoth}):
            from core.intelligence.pipeline.extractors import docx_extractor

            docx_extractor.extract_docx(sample_docx, deep_path)

        assert deep_path.exists()


# ---------------------------------------------------------------------------
# extract_docx_raw (plain text mode)
# ---------------------------------------------------------------------------


@needs_mammoth
class TestExtractDocxRaw:
    def test_raises_file_not_found(self):
        from core.intelligence.pipeline.extractors.docx_extractor import extract_docx_raw

        with pytest.raises(FileNotFoundError, match="DOCX not found"):
            extract_docx_raw("/nonexistent/path/missing.docx")

    def test_returns_plain_text(self, fake_mammoth, sample_docx):
        with patch.dict("sys.modules", {"mammoth": fake_mammoth}):
            from core.intelligence.pipeline.extractors import docx_extractor

            result = docx_extractor.extract_docx_raw(sample_docx)

        assert result == "Hello world"
        fake_mammoth.extract_raw_text.assert_called_once()

    def test_writes_output_file(self, fake_mammoth, sample_docx, tmp_path):
        out = tmp_path / "plain.txt"
        with patch.dict("sys.modules", {"mammoth": fake_mammoth}):
            from core.intelligence.pipeline.extractors import docx_extractor

            docx_extractor.extract_docx_raw(sample_docx, out)

        assert out.exists()
        assert out.read_text(encoding="utf-8") == "Hello world"


# ---------------------------------------------------------------------------
# extract_docx_to_inbox
# ---------------------------------------------------------------------------


@needs_mammoth
class TestExtractDocxToInbox:
    def test_creates_file_in_inbox(self, fake_mammoth, sample_docx, tmp_path):
        fake_knowledge = tmp_path / "knowledge" / "external"

        with (
            patch.dict("sys.modules", {"mammoth": fake_mammoth}),
            patch("core.paths.KNOWLEDGE_EXTERNAL", fake_knowledge),
        ):
            from core.intelligence.pipeline.extractors import docx_extractor

            result = docx_extractor.extract_docx_to_inbox(sample_docx, "alex-hormozi")

        expected_dir = fake_knowledge / "inbox" / "alex-hormozi"
        assert result == expected_dir / "sample.txt"
        assert result.exists()
        assert result.read_text(encoding="utf-8") == "Hello world"

    def test_output_filename_matches_stem(self, fake_mammoth, tmp_path):
        """Output .txt file should have same stem as input .docx."""
        fake_knowledge = tmp_path / "knowledge" / "external"
        docx = tmp_path / "My Lecture Notes.docx"
        docx.write_bytes(b"PK\x03\x04fake")

        with (
            patch.dict("sys.modules", {"mammoth": fake_mammoth}),
            patch("core.paths.KNOWLEDGE_EXTERNAL", fake_knowledge),
        ):
            from core.intelligence.pipeline.extractors import docx_extractor

            result = docx_extractor.extract_docx_to_inbox(docx, "cole-gordon")

        assert result.name == "My Lecture Notes.txt"
        assert result.parent.name == "cole-gordon"

    def test_raises_file_not_found(self):
        from core.intelligence.pipeline.extractors.docx_extractor import (
            extract_docx_to_inbox,
        )

        with pytest.raises(FileNotFoundError, match="DOCX not found"):
            extract_docx_to_inbox("/nonexistent/missing.docx", "test-source")


# ---------------------------------------------------------------------------
# ImportError when mammoth is missing
# ---------------------------------------------------------------------------


class TestMammothMissing:
    def test_extract_docx_raises_import_error(self, sample_docx):
        with patch.dict("sys.modules", {"mammoth": None}):
            from core.intelligence.pipeline.extractors import docx_extractor

            with pytest.raises(ImportError, match="mammoth is required"):
                docx_extractor._import_mammoth()

    def test_extract_docx_raw_raises_import_error(self, sample_docx):
        with patch.dict("sys.modules", {"mammoth": None}):
            from core.intelligence.pipeline.extractors import docx_extractor

            with pytest.raises(ImportError, match="mammoth is required"):
                docx_extractor.extract_docx_raw(sample_docx)


# ---------------------------------------------------------------------------
# _html_to_markdown helper
# ---------------------------------------------------------------------------


class TestHtmlToMarkdown:
    def test_converts_headings(self):
        from core.intelligence.pipeline.extractors.docx_extractor import _html_to_markdown

        result = _html_to_markdown("<h1>Title</h1>")
        assert "# Title" in result

    def test_converts_bold(self):
        from core.intelligence.pipeline.extractors.docx_extractor import _html_to_markdown

        result = _html_to_markdown("<strong>bold</strong>")
        assert "**bold**" in result

    def test_converts_italic(self):
        from core.intelligence.pipeline.extractors.docx_extractor import _html_to_markdown

        result = _html_to_markdown("<em>italic</em>")
        assert "*italic*" in result

    def test_converts_links(self):
        from core.intelligence.pipeline.extractors.docx_extractor import _html_to_markdown

        result = _html_to_markdown('<a href="https://example.com">link</a>')
        assert "[link](https://example.com)" in result

    def test_converts_lists(self):
        from core.intelligence.pipeline.extractors.docx_extractor import _html_to_markdown

        result = _html_to_markdown("<ul><li>item</li></ul>")
        assert "- item" in result

    def test_strips_unknown_tags(self):
        from core.intelligence.pipeline.extractors.docx_extractor import _html_to_markdown

        result = _html_to_markdown("<div><span>text</span></div>")
        assert "text" in result
        assert "<" not in result


# ---------------------------------------------------------------------------
# _decode_entities helper
# ---------------------------------------------------------------------------


class TestDecodeEntities:
    def test_decodes_named_entities(self):
        from core.intelligence.pipeline.extractors.docx_extractor import _decode_entities

        assert _decode_entities("&amp;") == "&"
        assert _decode_entities("&lt;") == "<"
        assert _decode_entities("&mdash;") == "\u2014"

    def test_decodes_numeric_entities(self):
        from core.intelligence.pipeline.extractors.docx_extractor import _decode_entities

        assert _decode_entities("&#65;") == "A"
        assert _decode_entities("&#x41;") == "A"
