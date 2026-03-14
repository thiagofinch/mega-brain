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
    - extract_docx: DOCX text extraction to markdown (mammoth)
    - extract_docx_raw: DOCX plain text extraction (mammoth)
    - extract_docx_to_inbox: DOCX extraction with inbox routing (mammoth)
    - extract_video: Video transcription (requires SS video support)
    - is_video_support_available: Check if video extraction is ready
"""

from __future__ import annotations

__all__ = [
    "extract_docx",
    "extract_docx_raw",
    "extract_docx_to_inbox",
    "extract_pdf",
    "extract_video",
    "is_video_support_available",
]

# Lazy imports to avoid ImportError when deps not installed
_pdf_extractor = None
_docx_extractor = None
_docx_raw_extractor = None
_docx_inbox_extractor = None


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


def extract_docx(path: str, output_path: str | None = None) -> str:
    """Extract text from DOCX file as markdown.

    Args:
        path: Path to DOCX file
        output_path: Optional path to write extracted markdown

    Returns:
        Markdown-formatted text content

    Raises:
        ImportError: If mammoth is not installed
        FileNotFoundError: If path does not exist
    """
    global _docx_extractor
    if _docx_extractor is None:
        from .docx_extractor import extract_docx as _docx_extractor
    return _docx_extractor(path, output_path)


def extract_docx_raw(path: str, output_path: str | None = None) -> str:
    """Extract plain text from DOCX file (no formatting).

    Args:
        path: Path to DOCX file
        output_path: Optional path to write extracted text

    Returns:
        Plain text content

    Raises:
        ImportError: If mammoth is not installed
        FileNotFoundError: If path does not exist
    """
    global _docx_raw_extractor
    if _docx_raw_extractor is None:
        from .docx_extractor import extract_docx_raw as _docx_raw_extractor
    return _docx_raw_extractor(path, output_path)


def extract_docx_to_inbox(docx_path: str, source_tag: str):
    """Extract DOCX and save to external inbox with proper naming.

    Args:
        docx_path: Path to the .docx file
        source_tag: Source identifier (e.g., "alex-hormozi")

    Returns:
        Path to the extracted text file in the inbox

    Raises:
        ImportError: If mammoth is not installed
        FileNotFoundError: If docx_path does not exist
    """
    global _docx_inbox_extractor
    if _docx_inbox_extractor is None:
        from .docx_extractor import extract_docx_to_inbox as _docx_inbox_extractor
    return _docx_inbox_extractor(docx_path, source_tag)
