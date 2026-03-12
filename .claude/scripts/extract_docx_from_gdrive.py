#!/usr/bin/env python3
"""
Script para extrair texto de arquivos .docx baixados do Google Drive (base64)
"""

import base64
import zipfile
import io
import re
import sys
import os

def decode_base64_docx(base64_content):
    """Decodifica conteúdo base64 para bytes"""
    # Remove possíveis prefixos de data URI
    if ',' in base64_content:
        base64_content = base64_content.split(',')[1]

    # Remove whitespace
    base64_content = base64_content.strip().replace('\n', '').replace('\r', '')

    return base64.b64decode(base64_content)

def extract_text_from_docx_bytes(docx_bytes):
    """Extrai texto de um arquivo .docx (que é um ZIP)"""
    try:
        # Abre como ZIP
        with zipfile.ZipFile(io.BytesIO(docx_bytes)) as zf:
            # Lê word/document.xml
            with zf.open('word/document.xml') as doc:
                xml_content = doc.read().decode('utf-8')

        # Remove tags XML, mantendo apenas texto
        # Padrão para encontrar texto entre tags <w:t>
        text_parts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml_content)

        # Junta tudo
        raw_text = ''.join(text_parts)

        # Limpa e formata
        # Substitui múltiplos espaços por um
        text = re.sub(r' +', ' ', raw_text)

        # Tenta preservar parágrafos baseado em padrões comuns
        # Adiciona quebras antes de números que parecem timestamps ou marcadores
        text = re.sub(r'(\d{1,2}:\d{2})', r'\n\1', text)

        return text.strip()

    except Exception as e:
        return f"ERRO ao extrair texto: {str(e)}"

def process_file(base64_content, output_path):
    """Processa um arquivo: decode + extract + save"""
    try:
        # Decodifica base64
        docx_bytes = decode_base64_docx(base64_content)

        # Extrai texto
        text = extract_text_from_docx_bytes(docx_bytes)

        # Cria diretório se necessário
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Salva como .txt
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        return True, len(text)

    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    # Teste básico
    if len(sys.argv) > 1:
        print(f"Script pronto. Use as funções: decode_base64_docx, extract_text_from_docx_bytes, process_file")
