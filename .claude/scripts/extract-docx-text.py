#!/usr/bin/env python3
"""
Extract text from base64-encoded .docx files from Google Drive
"""

import base64
import subprocess
import tempfile
import os
import sys

def extract_text_from_base64_docx(base64_content: str) -> str:
    """
    Decode base64 docx content and extract text using pandoc
    """
    # Decode base64
    docx_bytes = base64.b64decode(base64_content)

    # Create temp file
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        tmp.write(docx_bytes)
        tmp_path = tmp.name

    try:
        # Use pandoc to extract text
        result = subprocess.run(
            ['pandoc', tmp_path, '-t', 'plain', '--wrap=none'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    finally:
        # Clean up
        os.unlink(tmp_path)

def save_transcription(text: str, tag: str, name: str, output_dir: str) -> str:
    """
    Save extracted text to file with proper naming
    """
    # Clean filename
    clean_name = name.replace('.docx', '').replace('.mp4', '').strip()
    filename = f"[{tag}] {clean_name}.txt"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

    return filepath

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract-docx-text.py <base64_content>")
        sys.exit(1)

    base64_content = sys.argv[1]
    text = extract_text_from_base64_docx(base64_content)
    print(text)
