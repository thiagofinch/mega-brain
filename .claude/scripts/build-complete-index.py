#!/usr/bin/env python3
"""
BUILD COMPLETE INDEX - Extrai dados de todos os JSONs da planilha
Mega Brain - Sistema de Inteligência de Negócios

Processa os arquivos JSON salvos das chamadas do Google Sheets API
e constrói o índice completo nome→TAG
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

# Configurações
TOOL_RESULTS_PATH = ""  # Set to your Claude tool-results path
OUTPUT_PATH = ".claude/mission-control/PLANILHA-INDEX.json"
SCHEMA_PATH = ".claude/mission-control/SPREADSHEET-SCHEMA.json"

# Mapeamento de sheet -> coluna da TAG (índice baseado em 0 da row)
SHEET_CONFIG = {
    "Jeremy Haynes Sales Training": {"tag_col": -1, "prefix": "JH-ST"},  # última coluna
    "Jeremy Haynes Inner Circle": {"tag_col": -1, "prefix": "JH-IC"},
    "Inner Circle Weekly Group Call Recordings": {"tag_col": -1, "prefix": "JH-WK"},
    "Agency Blueprint": {"tag_col": -1, "prefix": "AOBA"},
    "Cold Video Pitch": {"tag_col": -1, "prefix": "PCVP"},
    "Land Your First Agency Client": {"tag_col": -1, "prefix": "LYFC"},
    "Marketer Mindset Masterclass": {"tag_col": -1, "prefix": "MMM"},
    "30 Days Challenge": {"tag_col": -1, "prefix": "30DC"},
    "Scale The Agency": {"tag_col": -1, "prefix": "STA"},
    "Ultra High Ticket Closer": {"tag_col": -1, "prefix": "UHTC"},
    "Jeremy Miner": {"tag_col": -1, "prefix": "JM"},
    "The Scalable Company": {"tag_col": -1, "prefix": "TSC"},
    "Sales Training BR": {"tag_col": -1, "prefix": "EDC"},
    "Alex Hormozi": {"tag_col": -1, "prefix": "AH"},
    "Jeremy Haynes Program": {"tag_col": -1, "prefix": "CA"},
}

def normalize_name(name):
    """Normaliza nome para matching."""
    if not name:
        return ""
    # Lowercase
    name = str(name).lower()
    # Remove extensão
    name = re.sub(r'\.(mp4|docx|txt|pdf)$', '', name, flags=re.IGNORECASE)
    # Remove número inicial
    name = re.sub(r'^\d+[\s\.\-]+', '', name)
    # Remove (1), (2), etc
    name = re.sub(r'\s*\(\d+\)\s*', '', name)
    # Remove youtube references
    name = re.sub(r'\[youtube\.com[^\]]*\]', '', name)
    # Remove caracteres especiais
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def is_valid_tag(tag, prefix=None):
    """Verifica se é uma TAG válida."""
    if not tag:
        return False
    tag = str(tag).strip()

    # Formato básico: XXX-NNNN ou XX-XXX-NNNN
    if not re.match(r'^[\w-]+-\d{4}$', tag):
        return False

    # Se prefix especificado, verificar
    if prefix and not tag.startswith(prefix):
        return False

    return True

def extract_from_row(row, sheet_name):
    """Extrai nome e TAG de uma row."""
    if not row:
        return None, None

    # Extrair valores
    values = []
    for cell in row:
        if isinstance(cell, dict):
            values.append(cell.get('value', ''))
        else:
            values.append(str(cell) if cell else '')

    if not values:
        return None, None

    # Nome está na primeira coluna
    name = values[0] if values else None

    # TAG está na última coluna (geralmente)
    # Procurar TAG no formato correto de trás para frente
    tag = None
    for v in reversed(values):
        if v and is_valid_tag(v):
            tag = v
            break

    return name, tag

def process_json_file(filepath):
    """Processa um arquivo JSON do Google Sheets."""
    entries = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # Formato: [{type: text, text: JSON_STRING}]
        if isinstance(raw_data, list) and raw_data:
            if isinstance(raw_data[0], dict) and 'text' in raw_data[0]:
                data = json.loads(raw_data[0]['text'])
            else:
                data = raw_data
        else:
            data = raw_data

        # Processar dados
        if isinstance(data, list):
            # Lista de sheets
            for sheet_data in data:
                if isinstance(sheet_data, dict) and 'sheetName' in sheet_data:
                    sheet_name = sheet_data['sheetName']
                    rows = sheet_data.get('data', [])

                    for row in rows:
                        name, tag = extract_from_row(row, sheet_name)
                        if name and tag:
                            entries.append({
                                'original_name': name,
                                'normalized': normalize_name(name),
                                'tag': tag,
                                'sheet': sheet_name
                            })

        elif isinstance(data, dict):
            # Pode ser formato valueRanges ou outro
            if 'valueRanges' in data:
                for range_data in data.get('valueRanges', []):
                    # Extrair sheet name do range
                    range_str = range_data.get('range', '')
                    sheet_name = range_str.split('!')[0].strip("'")

                    for row in range_data.get('values', []):
                        name, tag = extract_from_row(row, sheet_name)
                        if name and tag:
                            entries.append({
                                'original_name': name,
                                'normalized': normalize_name(name),
                                'tag': tag,
                                'sheet': sheet_name
                            })

    except Exception as e:
        print(f"  Erro processando {filepath}: {e}")

    return entries

def main():
    print("=" * 60)
    print("BUILD COMPLETE INDEX")
    print("=" * 60)
    print()

    all_entries = []
    sheets_found = set()

    # 1. Processar todos os arquivos JSON em tool-results
    print("[1/3] Processando arquivos JSON...")

    if os.path.exists(TOOL_RESULTS_PATH):
        json_files = list(Path(TOOL_RESULTS_PATH).glob("mcp-gdrive*.txt"))
        print(f"       {len(json_files)} arquivos encontrados")

        for filepath in json_files:
            entries = process_json_file(filepath)
            if entries:
                print(f"       {filepath.name}: {len(entries)} entradas")
                all_entries.extend(entries)
                sheets_found.update(e['sheet'] for e in entries)
    else:
        print(f"       AVISO: Pasta não encontrada: {TOOL_RESULTS_PATH}")

    # 2. Remover duplicatas (manter mais recente por tag)
    print()
    print("[2/3] Removendo duplicatas...")

    seen_tags = {}
    unique_entries = []

    for entry in all_entries:
        tag = entry['tag']
        if tag not in seen_tags:
            seen_tags[tag] = entry
            unique_entries.append(entry)
        else:
            # Se mesma tag, manter a entrada com nome mais completo
            existing = seen_tags[tag]
            if len(entry['original_name']) > len(existing['original_name']):
                seen_tags[tag] = entry
                unique_entries = [e for e in unique_entries if e['tag'] != tag]
                unique_entries.append(entry)

    print(f"       De {len(all_entries)} para {len(unique_entries)} entradas únicas")

    # 3. Ordenar por sheet e tag
    unique_entries.sort(key=lambda x: (x['sheet'], x['tag']))

    # 4. Salvar índice
    print()
    print("[3/3] Salvando índice...")

    index = {
        'version': '2.0',
        'timestamp': datetime.now().isoformat(),
        'total_entries': len(unique_entries),
        'sheets_processed': sorted(list(sheets_found)),
        'entries': unique_entries
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"       Salvo em: {OUTPUT_PATH}")
    print()

    # 5. Resumo por sheet
    print("=" * 60)
    print("RESUMO POR SHEET")
    print("=" * 60)

    sheet_counts = {}
    for entry in unique_entries:
        sheet = entry['sheet']
        sheet_counts[sheet] = sheet_counts.get(sheet, 0) + 1

    for sheet, count in sorted(sheet_counts.items()):
        print(f"  {sheet}: {count} TAGs")

    print()
    print(f"TOTAL: {len(unique_entries)} entradas")
    print("=" * 60)

    return index

if __name__ == '__main__':
    main()
