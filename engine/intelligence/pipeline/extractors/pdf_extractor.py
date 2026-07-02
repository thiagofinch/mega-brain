"""
PDF Extractor -- Convert PDF files to markdown text.
=====================================================

Uses pymupdf (fitz) for text extraction. Handles:
- Multi-page documents
- Basic table structure preservation
- Heading detection from font size
- Page number markers for traceability

Install: pip install pymupdf
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import fitz  # noqa: F401


def extract_pdf(path: str | Path, *, include_images: bool = False) -> str:
    """Extract text from PDF and convert to markdown.

    Args:
        path: Path to PDF file
        include_images: If True, add placeholder for images (no OCR)

    Returns:
        Markdown-formatted text with page markers

    Raises:
        ImportError: If pymupdf is not installed
        FileNotFoundError: If file does not exist
    """
    try:
        import fitz
    except ImportError as e:
        raise ImportError("pymupdf not installed. Run: pip install pymupdf") from e

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    doc = fitz.open(str(path))
    output_lines: list[str] = []

    # Document metadata
    title = doc.metadata.get("title") or path.stem
    output_lines.append(f"# {title}\n")
    output_lines.append(f"*Source: {path.name}*\n")
    output_lines.append("---\n")

    for page_num, page in enumerate(doc, start=1):
        # Page marker for traceability
        output_lines.append(f"\n<!-- PAGE {page_num} -->\n")

        # Extract text blocks with position info
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

        for block in blocks:
            if block["type"] == 0:  # Text block
                text = _process_text_block(block)
                if text.strip():
                    output_lines.append(text)
            elif block["type"] == 1 and include_images:  # Image block
                output_lines.append("\n*[Image placeholder]*\n")

    doc.close()

    # Clean up excessive whitespace
    result = "\n".join(output_lines)
    result = _clean_markdown(result)

    return result


def _process_text_block(block: dict) -> str:
    """Process a text block into markdown.

    Attempts to detect headings based on font size relative to body text.
    """
    lines: list[str] = []
    max_size = 0.0
    sizes: list[float] = []

    # First pass: collect font sizes
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            size = span.get("size", 12)
            sizes.append(size)
            if size > max_size:
                max_size = size

    # Determine threshold for "heading" (significantly larger than median)
    if sizes:
        sorted_sizes = sorted(sizes)
        median_size = sorted_sizes[len(sorted_sizes) // 2]
        heading_threshold = median_size * 1.3
    else:
        heading_threshold = 14

    # Second pass: extract text with formatting
    for line in block.get("lines", []):
        line_text: list[str] = []
        is_heading = False

        for span in line.get("spans", []):
            text = span.get("text", "")
            size = span.get("size", 12)
            flags = span.get("flags", 0)

            # Check for heading
            if size >= heading_threshold and text.strip():
                is_heading = True

            # Check for bold (flag bit 0) or italic (flag bit 1)
            is_bold = bool(flags & 1 << 4)  # Bold flag in fitz
            is_italic = bool(flags & 1 << 1)  # Italic flag

            if is_bold and not is_heading:
                text = f"**{text}**"
            if is_italic:
                text = f"*{text}*"

            line_text.append(text)

        combined = "".join(line_text).strip()
        if combined:
            if is_heading:
                # Use ## for detected headings (# reserved for title)
                lines.append(f"\n## {combined}\n")
            else:
                lines.append(combined)

    return "\n".join(lines)


def _clean_markdown(text: str) -> str:
    """Clean up markdown output."""
    import re

    # Remove excessive blank lines (3+ -> 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove trailing whitespace on lines
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Ensure single trailing newline
    text = text.strip() + "\n"

    return text
