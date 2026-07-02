#!/usr/bin/env python3
"""
Extract a single transcription directly from Google Drive
Uses the MCP gdrive API output format
"""

import base64
import subprocess
import tempfile
import os
import sys
import re
import zipfile

def extract_text_from_docx_bytes(docx_bytes: bytes) -> str:
    """
    Extract text from docx bytes using pandoc or fallback to XML parsing
    """
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        tmp.write(docx_bytes)
        tmp_path = tmp.name

    try:
        # First try pandoc
        result = subprocess.run(
            ['pandoc', tmp_path, '-t', 'plain', '--wrap=none'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return result.stdout

        # Fallback: extract from XML directly
        with zipfile.ZipFile(tmp_path, 'r') as z:
            if 'word/document.xml' in z.namelist():
                xml_content = z.read('word/document.xml').decode('utf-8')
                # Extract text from <w:t> tags
                texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml_content)
                return ' '.join(texts)

        return "[ERROR] Could not extract text"

    except Exception as e:
        return f"[ERROR] {e}"
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass

def main():
    # Read base64 from stdin
    base64_content = sys.stdin.read().strip()

    if not base64_content:
        print("[ERROR] No base64 content provided via stdin")
        sys.exit(1)

    try:
        docx_bytes = base64.b64decode(base64_content)
        print(f"[INFO] Decoded {len(docx_bytes)} bytes", file=sys.stderr)

        text = extract_text_from_docx_bytes(docx_bytes)
        print(text)

    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
