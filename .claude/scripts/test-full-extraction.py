#!/usr/bin/env python3
"""
Test script to verify extraction works with known base64 content
"""

import base64
import tempfile
import zipfile
import re
from xml.etree import ElementTree as ET

WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def extract_text_from_xml(xml_content: str) -> str:
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml_content)
        return ' '.join(texts)

    texts = []
    for elem in root.iter():
        if elem.tag == f'{WORD_NAMESPACE}t':
            if elem.text:
                texts.append(elem.text)
        elif elem.tag == f'{WORD_NAMESPACE}p':
            if texts and not texts[-1].endswith('\n'):
                texts.append('\n')
        elif elem.tag == f'{WORD_NAMESPACE}br':
            texts.append('\n')

    text = ''.join(texts)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

# Read test base64 from file
TEST_FILE = ".claude/temp/full_base64.txt"

try:
    with open(TEST_FILE, 'r') as f:
        base64_content = f.read().strip()

    print(f"Read {len(base64_content)} chars of base64")

    docx_bytes = base64.b64decode(base64_content)
    print(f"Decoded to {len(docx_bytes)} bytes")

    # Save temporarily and check structure
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        tmp.write(docx_bytes)
        tmp_path = tmp.name

    if zipfile.is_zipfile(tmp_path):
        print("Valid ZIP/DOCX structure")
        with zipfile.ZipFile(tmp_path, 'r') as z:
            files = z.namelist()
            print(f"Contains {len(files)} files")
            if 'word/document.xml' in files:
                xml_content = z.read('word/document.xml').decode('utf-8')
                print(f"document.xml: {len(xml_content)} chars")
                text = extract_text_from_xml(xml_content)
                print(f"\nExtracted text ({len(text)} chars, {len(text.split())} words):")
                print("="*60)
                print(text[:2000] if len(text) > 2000 else text)
                print("="*60)
    else:
        print("Not a valid ZIP file")

except FileNotFoundError:
    print(f"Test file not found: {TEST_FILE}")
    print("Please save base64 content to this file first")
except Exception as e:
    print(f"Error: {e}")
