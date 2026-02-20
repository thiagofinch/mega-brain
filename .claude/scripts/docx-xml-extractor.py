#!/usr/bin/env python3
"""
DOCX XML Text Extractor for Mega Brain
---------------------------------------
Extrai texto de arquivos .docx usando parsing XML direto.
Não requer pandoc ou outras dependências externas.
"""

import base64
import tempfile
import os
import sys
import re
import zipfile
from xml.etree import ElementTree as ET

# OOXML namespace
WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def extract_text_from_xml(xml_content: str) -> str:
    """
    Extract text from Word document.xml content
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        # Fallback to regex if XML parsing fails
        texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml_content)
        return ' '.join(texts)

    texts = []

    # Find all <w:t> elements (text runs)
    for elem in root.iter():
        if elem.tag == f'{WORD_NAMESPACE}t':
            if elem.text:
                texts.append(elem.text)
        # Handle paragraph breaks
        elif elem.tag == f'{WORD_NAMESPACE}p':
            if texts and not texts[-1].endswith('\n'):
                texts.append('\n')
        # Handle line breaks
        elif elem.tag == f'{WORD_NAMESPACE}br':
            texts.append('\n')

    # Join and clean up
    text = ''.join(texts)
    # Normalize whitespace but preserve paragraph breaks
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()

    return text

def extract_from_docx_bytes(docx_bytes: bytes) -> str:
    """
    Extract text from docx file bytes
    """
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        tmp.write(docx_bytes)
        tmp_path = tmp.name

    try:
        if not zipfile.is_zipfile(tmp_path):
            return "[ERROR] Invalid docx file (not a valid ZIP)"

        with zipfile.ZipFile(tmp_path, 'r') as z:
            if 'word/document.xml' not in z.namelist():
                return "[ERROR] Invalid docx file (no document.xml)"

            xml_content = z.read('word/document.xml').decode('utf-8')
            return extract_text_from_xml(xml_content)

    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass

def process_base64_file(input_file: str) -> str:
    """
    Process a file containing base64-encoded docx content
    """
    with open(input_file, 'r') as f:
        base64_content = f.read().strip()

    # Clean base64 content
    base64_clean = base64_content.replace('\n', '').replace('\r', '').replace(' ', '')

    try:
        docx_bytes = base64.b64decode(base64_clean)
    except Exception as e:
        return f"[ERROR] Base64 decode failed: {e}"

    return extract_from_docx_bytes(docx_bytes)

def save_transcription(text: str, tag: str, name: str, output_dir: str) -> str:
    """
    Save transcription with proper [TAG] naming
    """
    # Clean the name
    clean_name = name
    for ext in ['.docx', '.mp4', '.txt']:
        clean_name = clean_name.replace(ext, '')
    clean_name = clean_name.strip(' -.')

    filename = f"[{tag}] {clean_name}.txt"
    filepath = os.path.join(output_dir, filename)

    os.makedirs(output_dir, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

    return filepath

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Extract text from base64-encoded docx')
    parser.add_argument('base64_file', help='File containing base64 content')
    parser.add_argument('--tag', help='TAG for output file (e.g., JM-0003)')
    parser.add_argument('--name', help='Original filename for output')
    parser.add_argument('--output-dir', help='Output directory')

    args = parser.parse_args()

    text = process_base64_file(args.base64_file)

    if text.startswith('[ERROR]'):
        print(text, file=sys.stderr)
        sys.exit(1)

    if args.tag and args.name and args.output_dir:
        filepath = save_transcription(text, args.tag, args.name, args.output_dir)
        print(f"Saved: {filepath}")
        print(f"Characters: {len(text)}")
        print(f"Words: {len(text.split())}")
    else:
        # Just print the text
        print(text)
