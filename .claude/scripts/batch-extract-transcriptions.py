#!/usr/bin/env python3
"""
Batch Extraction Script for Mega Brain Transcriptions
------------------------------------------------------
Este script extrai transcrições de arquivos .docx no Google Drive
e salva como arquivos .txt com TAG no INBOX.

Uso:
    python batch-extract-transcriptions.py <base64_file> <tag> <output_name> <output_dir>

O arquivo base64_file deve conter o conteúdo base64 puro do .docx
"""

import base64
import subprocess
import tempfile
import os
import sys
import json

def decode_and_extract(base64_content: str) -> str:
    """
    Decode base64 docx content and extract text using pandoc
    """
    # Remove whitespace/newlines from base64
    base64_clean = base64_content.strip().replace('\n', '').replace(' ', '')

    # Decode base64
    try:
        docx_bytes = base64.b64decode(base64_clean)
    except Exception as e:
        return f"[ERROR] Base64 decode failed: {e}"

    # Create temp file
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        tmp.write(docx_bytes)
        tmp_path = tmp.name

    try:
        # Check if pandoc is available
        result = subprocess.run(
            ['which', 'pandoc'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Try using unzip to extract document.xml directly
            import zipfile
            try:
                with zipfile.ZipFile(tmp_path, 'r') as z:
                    if 'word/document.xml' in z.namelist():
                        xml_content = z.read('word/document.xml').decode('utf-8')
                        # Basic XML text extraction
                        import re
                        text = re.sub(r'<[^>]+>', '', xml_content)
                        text = re.sub(r'\s+', ' ', text)
                        return text.strip()
            except Exception as e:
                return f"[ERROR] ZIP extraction failed: {e}"

        # Use pandoc to extract text
        result = subprocess.run(
            ['pandoc', tmp_path, '-t', 'plain', '--wrap=none'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout

    except subprocess.CalledProcessError as e:
        return f"[ERROR] Pandoc failed: {e.stderr}"
    except Exception as e:
        return f"[ERROR] Extraction failed: {e}"
    finally:
        # Clean up
        try:
            os.unlink(tmp_path)
        except:
            pass

def save_transcription(text: str, tag: str, name: str, output_dir: str) -> str:
    """
    Save extracted text to file with proper naming
    """
    # Clean filename
    clean_name = name.replace('.docx', '').replace('.mp4', '').strip()
    # Remove leading numbers and dashes if duplicated
    clean_name = clean_name.strip(' -.')

    filename = f"[{tag}] {clean_name}.txt"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

    return filepath

def process_from_file(base64_file: str, tag: str, name: str, output_dir: str) -> dict:
    """
    Process a single file from base64 content file
    """
    with open(base64_file, 'r') as f:
        base64_content = f.read()

    text = decode_and_extract(base64_content)

    if text.startswith('[ERROR]'):
        return {'success': False, 'error': text, 'tag': tag}

    filepath = save_transcription(text, tag, name, output_dir)
    return {
        'success': True,
        'filepath': filepath,
        'tag': tag,
        'chars': len(text),
        'words': len(text.split())
    }

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python batch-extract-transcriptions.py <base64_file> <tag> <output_name> <output_dir>")
        print("Example: python batch-extract-transcriptions.py /tmp/content.b64 JM-0003 'Your Prospects Are Lying' ./INBOX/")
        sys.exit(1)

    base64_file = sys.argv[1]
    tag = sys.argv[2]
    name = sys.argv[3]
    output_dir = sys.argv[4]

    result = process_from_file(base64_file, tag, name, output_dir)
    print(json.dumps(result, indent=2))
