#!/usr/bin/env python3
"""
PLANILHA TAGGER - Tagueamento na Fonte
Mega Brain - Sistema de Inteligência de Negócios

Escreve TAGs diretamente na planilha de controle via MCP gdrive.
TAGs são escritas NA FONTE, não localmente.

USO: Este script é chamado pelo JARVIS via MCP, não diretamente.
"""

import os
import json
from datetime import datetime
from pathlib import Path

# Configurações
MISSION_CONTROL = ".claude/mission-control"
PLANILHA_INDEX = f"{MISSION_CONTROL}/PLANILHA-INDEX.json"
SOURCE_SYNC_STATE = f"{MISSION_CONTROL}/SOURCE-SYNC-STATE.json"

# Mapeamento de abas → prefixos de TAG
SHEET_TO_PREFIX = {
    "Jeremy Miner": "JM",
    "Jeremy Haynes Sales Training": "JH-ST",
    "Jeremy Haynes Inner Circle": "JH-IC",
    "Inner Circle Weekly Group Call Recordings": "JH-WK",
    "Agency Blueprint": "AOBA",
    "Cold Video Pitch": "PCVP",
    "Land Your First Agency Client": "LYFC",
    "Marketer Mindset Masterclass": "MMM",
    "30 Days Challenge": "30DC",
    "Scale The Agency": "STA",
    "Ultra High Ticket Closer": "UHTC",
    "Cole Gordon": "CG",
    "The Scalable Company": "TSC",
    "Sales Training BR": "EDC",
    "Alex Hormozi": "AH",
    "Jeremy Haynes Program": "CA",
}

TAG_COLUMN = "I"
TAG_COLUMN_INDEX = 8


def load_planilha_index():
    """Carrega índice da planilha."""
    if os.path.exists(PLANILHA_INDEX):
        with open(PLANILHA_INDEX, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"entries": [], "timestamp": None}


def get_existing_tags(index, prefix):
    """Retorna todas as TAGs existentes para um prefixo."""
    tags = set()
    for entry in index.get('entries', []):
        tag = entry.get('tag', '')
        if tag.startswith(prefix + "-"):
            tags.add(tag)
    return tags


def generate_next_tag(prefix, existing_tags):
    """Gera próxima TAG sequencial para um prefixo."""
    max_num = 0
    for tag in existing_tags:
        if tag.startswith(prefix + "-"):
            try:
                num_part = tag.split("-")[-1]
                num = int(num_part)
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    return f"{prefix}-{str(max_num + 1).zfill(4)}"


def identify_untagged_entries(delta_entries, index):
    """Identifica entradas que precisam de TAG."""
    untagged = []

    for entry in delta_entries:
        if entry.get('tag') and entry['tag'].strip():
            continue

        sheet_name = entry.get('sheet', '')
        prefix = SHEET_TO_PREFIX.get(sheet_name)

        if not prefix:
            for sheet, pf in SHEET_TO_PREFIX.items():
                if sheet.lower() in sheet_name.lower():
                    prefix = pf
                    break

        if prefix:
            untagged.append({
                'entry': entry,
                'prefix': prefix,
                'sheet': sheet_name
            })

    return untagged


def prepare_tag_operations(untagged, index):
    """Prepara operações de tagueamento para MCP."""
    operations = []
    by_prefix = {}

    for item in untagged:
        prefix = item['prefix']
        if prefix not in by_prefix:
            by_prefix[prefix] = []
        by_prefix[prefix].append(item)

    for prefix, items in by_prefix.items():
        existing_tags = get_existing_tags(index, prefix)

        for item in items:
            new_tag = generate_next_tag(prefix, existing_tags)
            existing_tags.add(new_tag)

            entry = item['entry']
            operations.append({
                'type': 'write_tag',
                'spreadsheet_id': entry.get('spreadsheet_id'),
                'sheet_name': item['sheet'],
                'row': entry.get('row'),
                'column': TAG_COLUMN,
                'range': f"'{item['sheet']}'!{TAG_COLUMN}{entry.get('row')}",
                'value': new_tag,
                'original_name': entry.get('name', ''),
                'prefix': prefix
            })

    return operations


def generate_tag_report(operations):
    """Gera relatório de operações de tagueamento."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_operations': len(operations),
        'by_prefix': {},
        'operations': operations
    }

    for op in operations:
        prefix = op['prefix']
        if prefix not in report['by_prefix']:
            report['by_prefix'][prefix] = 0
        report['by_prefix'][prefix] += 1

    return report


def main(delta_entries=None, preview=True):
    """Função principal do tagger."""
    index = load_planilha_index()

    if delta_entries is None:
        print("PLANILHA TAGGER - Modo Standalone")
        print("Passe delta_entries para executar.")
        return None

    untagged = identify_untagged_entries(delta_entries, index)

    if not untagged:
        print("✅ Todas as entradas já possuem TAG!")
        return []

    operations = prepare_tag_operations(untagged, index)
    report = generate_tag_report(operations)

    print(f"TAGs a escrever: {report['total_operations']}")
    for prefix, count in sorted(report['by_prefix'].items()):
        print(f"  {prefix}: {count}")

    if preview:
        return None

    return operations


if __name__ == '__main__':
    main()
