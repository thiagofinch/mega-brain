"""
Extractors -- Format-specific text extraction utilities.
=========================================================

These extractors convert various input formats to markdown text
suitable for the MCE pipeline. They use lightweight libraries
(pymupdf, mammoth) that can be installed independently.

For advanced extraction (video, web scraping), use the ss_bridge
module which calls Skill Seekers in an isolated venv.

Extractors:
    - extract_pdf: PDF text extraction (pymupdf)
    - extract_docx: DOCX text extraction (mammoth)
    - extract_video: Video transcription (requires SS video support)
    - is_video_support_available: Check if video extraction is ready
"""

from __future__ import annotations

__all__ = [
    "extract_pdf",
    "extract_docx",
    "extract_video",
    "is_video_support_available",
]

# Lazy imports to avoid ImportError when deps not installed
_pdf_extractor = None
_docx_extractor = None


def extract_pdf(path: str, *, include_images: bool = False) -> str:
    """Extract text from PDF file.

    Args:
        path: Path to PDF file
        include_images: Whether to include image descriptions (OCR not supported)

    Returns:
        Markdown-formatted text content

    Raises:
        ImportError: If pymupdf is not installed
        FileNotFoundError: If path does not exist
    """
    global _pdf_extractor
    if _pdf_extractor is None:
        from .pdf_extractor import extract_pdf as _pdf_extractor
    return _pdf_extractor(path, include_images=include_images)


def extract_docx(path: str) -> str:
    """Extract text from DOCX file.

    Args:
        path: Path to DOCX file

    Returns:
        Markdown-formatted text content

    Raises:
        ImportError: If mammoth is not installed
        FileNotFoundError: If path does not exist
    """
    global _docx_extractor
    if _docx_extractor is None:
        from .docx_extractor import extract_docx as _docx_extractor
    return _docx_extractor(path)
