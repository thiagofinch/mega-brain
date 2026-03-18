"""PDF text extraction for Mega Brain pipeline.

Extracts text from PDF files using PyMuPDF (fitz).
Outputs plain text suitable for pipeline ingestion.
"""

import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def extract_pdf(pdf_path: str | Path, output_path: str | Path | None = None) -> str:
    """Extract text from a PDF file.

    Args:
        pdf_path: Path to the PDF file.
        output_path: Optional path to write extracted text. If None, returns text only.

    Returns:
        Extracted text as a string.

    Raises:
        ImportError: If pymupdf is not installed.
        FileNotFoundError: If pdf_path doesn't exist.
    """
    if fitz is None:
        raise ImportError(
            "pymupdf is required for PDF extraction. Install with: pip install pymupdf"
        )

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    pages = []

    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        if text.strip():
            pages.append(f"--- Page {page_num} ---\n{text}")

    doc.close()

    full_text = "\n\n".join(pages)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(full_text, encoding="utf-8")

    return full_text


def extract_pdf_to_inbox(pdf_path: str | Path, source_tag: str) -> Path:
    """Extract PDF and save to the external inbox with proper naming.

    Args:
        pdf_path: Path to the PDF file.
        source_tag: Source identifier (e.g., "alex-hormozi", "cole-gordon").

    Returns:
        Path to the extracted text file in the inbox.
    """
    from core.paths import KNOWLEDGE_EXTERNAL

    pdf_path = Path(pdf_path)
    inbox_dir = KNOWLEDGE_EXTERNAL / "inbox" / source_tag
    inbox_dir.mkdir(parents=True, exist_ok=True)

    output_name = pdf_path.stem + ".txt"
    output_path = inbox_dir / output_name

    extract_pdf(pdf_path, output_path)
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <pdf_path> [output_path]")
        sys.exit(1)

    pdf = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None

    text = extract_pdf(pdf, out)
    if not out:
        print(text)
