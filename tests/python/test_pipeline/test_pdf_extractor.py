"""Tests for PDF text extraction module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_test_pdf(path: Path, pages: list[str]) -> None:
    """Create a minimal PDF with given page texts using PyMuPDF."""
    import fitz

    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()


# ---------------------------------------------------------------------------
# extract_pdf
# ---------------------------------------------------------------------------


class TestExtractPdf:
    """Tests for the extract_pdf function."""

    def test_extract_single_page(self, tmp_path: Path) -> None:
        """Extracting a single-page PDF returns text with page marker."""
        pdf_path = tmp_path / "single.pdf"
        _create_test_pdf(pdf_path, ["Hello Pickle Rick"])

        from core.intelligence.pipeline.pdf_extractor import extract_pdf

        result = extract_pdf(pdf_path)

        assert "--- Page 1 ---" in result
        assert "Hello Pickle Rick" in result

    def test_extract_multi_page(self, tmp_path: Path) -> None:
        """Extracting a multi-page PDF returns text from all pages."""
        pdf_path = tmp_path / "multi.pdf"
        _create_test_pdf(pdf_path, ["Page one content", "Page two content"])

        from core.intelligence.pipeline.pdf_extractor import extract_pdf

        result = extract_pdf(pdf_path)

        assert "--- Page 1 ---" in result
        assert "--- Page 2 ---" in result
        assert "Page one content" in result
        assert "Page two content" in result

    def test_extract_nonexistent_raises(self) -> None:
        """Passing a non-existent file raises FileNotFoundError."""
        from core.intelligence.pipeline.pdf_extractor import extract_pdf

        with pytest.raises(FileNotFoundError, match="PDF not found"):
            extract_pdf("/tmp/definitely_does_not_exist_pickle.pdf")

    def test_extract_with_output_path(self, tmp_path: Path) -> None:
        """extract_pdf writes text to output_path when provided."""
        pdf_path = tmp_path / "out_test.pdf"
        _create_test_pdf(pdf_path, ["Output test"])

        output_path = tmp_path / "subdir" / "output.txt"

        from core.intelligence.pipeline.pdf_extractor import extract_pdf

        result = extract_pdf(pdf_path, output_path)

        assert output_path.exists()
        written = output_path.read_text(encoding="utf-8")
        assert written == result
        assert "Output test" in written

    def test_extract_empty_pages_skipped(self, tmp_path: Path) -> None:
        """Pages with no text content are skipped."""
        import fitz

        pdf_path = tmp_path / "empty_pages.pdf"
        doc = fitz.open()
        # Page 1: has text
        page1 = doc.new_page()
        page1.insert_text((72, 72), "Has content")
        # Page 2: completely empty (no text inserted)
        doc.new_page()
        # Page 3: has text
        page3 = doc.new_page()
        page3.insert_text((72, 72), "Also has content")
        doc.save(str(pdf_path))
        doc.close()

        from core.intelligence.pipeline.pdf_extractor import extract_pdf

        result = extract_pdf(pdf_path)

        assert "--- Page 1 ---" in result
        assert "--- Page 2 ---" not in result
        assert "--- Page 3 ---" in result

    def test_extract_returns_string(self, tmp_path: Path) -> None:
        """extract_pdf always returns a string."""
        pdf_path = tmp_path / "type_check.pdf"
        _create_test_pdf(pdf_path, ["Type check"])

        from core.intelligence.pipeline.pdf_extractor import extract_pdf

        result = extract_pdf(pdf_path)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# extract_pdf_to_inbox
# ---------------------------------------------------------------------------


class TestExtractPdfToInbox:
    """Tests for the extract_pdf_to_inbox function."""

    def test_creates_file_in_inbox(self, tmp_path: Path) -> None:
        """extract_pdf_to_inbox creates a .txt file in the correct inbox location."""
        pdf_path = tmp_path / "source_material.pdf"
        _create_test_pdf(pdf_path, ["Inbox test content"])

        # Mock KNOWLEDGE_EXTERNAL to use tmp_path
        fake_knowledge = tmp_path / "knowledge" / "external"

        with patch("core.intelligence.pipeline.pdf_extractor.extract_pdf") as mock_extract:
            mock_extract.return_value = "extracted text"
            # We need to patch the import inside the function
            with patch("core.paths.KNOWLEDGE_EXTERNAL", fake_knowledge):
                from core.intelligence.pipeline.pdf_extractor import extract_pdf_to_inbox

                result = extract_pdf_to_inbox(pdf_path, "alex-hormozi")

        expected_dir = fake_knowledge / "inbox" / "alex-hormozi"
        assert result.parent == expected_dir
        assert result.name == "source_material.txt"

    def test_output_filename_matches_stem(self, tmp_path: Path) -> None:
        """Output filename is the PDF stem with .txt extension."""
        pdf_path = tmp_path / "my-great-book.pdf"
        _create_test_pdf(pdf_path, ["Book content"])

        fake_knowledge = tmp_path / "knowledge" / "external"

        with patch("core.paths.KNOWLEDGE_EXTERNAL", fake_knowledge):
            from core.intelligence.pipeline.pdf_extractor import extract_pdf_to_inbox

            result = extract_pdf_to_inbox(pdf_path, "cole-gordon")

        assert result.name == "my-great-book.txt"
        assert result.exists()


# ---------------------------------------------------------------------------
# ImportError handling
# ---------------------------------------------------------------------------


class TestImportErrorHandling:
    """Tests for graceful handling when pymupdf is not installed."""

    def test_fitz_none_raises_import_error(self) -> None:
        """When fitz is None, extract_pdf raises ImportError."""
        with patch("core.intelligence.pipeline.pdf_extractor.fitz", None):
            from core.intelligence.pipeline.pdf_extractor import extract_pdf

            with pytest.raises(ImportError, match="pymupdf is required"):
                extract_pdf("/any/path.pdf")
