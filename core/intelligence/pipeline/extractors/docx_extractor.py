"""
DOCX Extractor -- Convert Word documents to markdown text.
===========================================================

Uses mammoth for clean HTML conversion, then converts to markdown.
Handles:
- Headings (H1-H6)
- Lists (ordered and unordered)
- Bold, italic, underline
- Tables (basic)
- Hyperlinks

Install: pip install mammoth
"""

from __future__ import annotations

import re
from pathlib import Path


def extract_docx(path: str | Path) -> str:
    """Extract text from DOCX and convert to markdown.

    Args:
        path: Path to DOCX file

    Returns:
        Markdown-formatted text

    Raises:
        ImportError: If mammoth is not installed
        FileNotFoundError: If file does not exist
    """
    try:
        import mammoth
    except ImportError as e:
        raise ImportError(
            "mammoth not installed. Run: pip install mammoth"
        ) from e

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX not found: {path}")

    # Extract to HTML first (mammoth's native output)
    with open(path, "rb") as f:
        result = mammoth.convert_to_html(f)

    html = result.value
    messages = result.messages  # Warnings, if any

    # Convert HTML to markdown
    markdown = _html_to_markdown(html)

    # Add header with source info
    output = f"# {path.stem}\n\n*Source: {path.name}*\n\n---\n\n{markdown}"

    # Add warnings as comments if any
    if messages:
        warnings = "\n".join(f"<!-- Warning: {m.message} -->" for m in messages)
        output = f"{warnings}\n\n{output}"

    return output


def _html_to_markdown(html: str) -> str:
    """Convert mammoth HTML output to markdown.

    Simple regex-based conversion for common elements.
    """
    # Headings
    for i in range(6, 0, -1):
        pattern = rf"<h{i}>(.*?)</h{i}>"
        replacement = "\n" + "#" * i + r" \1\n"
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)

    # Paragraphs
    html = re.sub(r"<p>(.*?)</p>", r"\n\1\n", html, flags=re.DOTALL)

    # Bold
    html = re.sub(r"<strong>(.*?)</strong>", r"**\1**", html, flags=re.DOTALL)
    html = re.sub(r"<b>(.*?)</b>", r"**\1**", html, flags=re.DOTALL)

    # Italic
    html = re.sub(r"<em>(.*?)</em>", r"*\1*", html, flags=re.DOTALL)
    html = re.sub(r"<i>(.*?)</i>", r"*\1*", html, flags=re.DOTALL)

    # Underline (no markdown equiv, use emphasis)
    html = re.sub(r"<u>(.*?)</u>", r"*\1*", html, flags=re.DOTALL)

    # Links
    html = re.sub(r'<a href="(.*?)">(.*?)</a>', r"[\2](\1)", html, flags=re.DOTALL)

    # Unordered lists
    html = re.sub(r"<ul>", "\n", html)
    html = re.sub(r"</ul>", "\n", html)
    html = re.sub(r"<li>(.*?)</li>", r"- \1\n", html, flags=re.DOTALL)

    # Ordered lists (simple -- doesn't track numbering)
    html = re.sub(r"<ol>", "\n", html)
    html = re.sub(r"</ol>", "\n", html)

    # Line breaks
    html = re.sub(r"<br\s*/?>", "\n", html)

    # Tables (basic -- convert to pipe tables)
    html = _convert_tables(html)

    # Remove remaining HTML tags
    html = re.sub(r"<[^>]+>", "", html)

    # Decode HTML entities
    html = _decode_entities(html)

    # Clean up whitespace
    html = re.sub(r"\n{3,}", "\n\n", html)
    html = re.sub(r"[ \t]+", " ", html)
    lines = [line.strip() for line in html.split("\n")]
    html = "\n".join(lines)

    return html.strip() + "\n"


def _convert_tables(html: str) -> str:
    """Convert HTML tables to markdown pipe tables."""
    # Find all tables
    table_pattern = r"<table>(.*?)</table>"

    def table_replacer(match: re.Match) -> str:
        table_html = match.group(1)

        # Extract rows
        rows: list[list[str]] = []
        row_pattern = r"<tr>(.*?)</tr>"

        for row_match in re.finditer(row_pattern, table_html, re.DOTALL):
            row_html = row_match.group(1)
            cells: list[str] = []

            # Headers or data cells
            cell_pattern = r"<t[hd]>(.*?)</t[hd]>"
            for cell_match in re.finditer(cell_pattern, row_html, re.DOTALL):
                cell_text = re.sub(r"<[^>]+>", "", cell_match.group(1))
                cells.append(cell_text.strip())

            if cells:
                rows.append(cells)

        if not rows:
            return ""

        # Build markdown table
        md_lines: list[str] = []

        # Header row
        if rows:
            md_lines.append("| " + " | ".join(rows[0]) + " |")
            md_lines.append("| " + " | ".join(["---"] * len(rows[0])) + " |")

        # Data rows
        for row in rows[1:]:
            md_lines.append("| " + " | ".join(row) + " |")

        return "\n" + "\n".join(md_lines) + "\n"

    return re.sub(table_pattern, table_replacer, html, flags=re.DOTALL)


def _decode_entities(text: str) -> str:
    """Decode common HTML entities."""
    entities = {
        "&nbsp;": " ",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'",
        "&apos;": "'",
        "&mdash;": "—",
        "&ndash;": "–",
        "&ldquo;": '"',
        "&rdquo;": '"',
        "&lsquo;": "'",
        "&rsquo;": "'",
        "&hellip;": "...",
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)

    # Numeric entities
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)

    return text
