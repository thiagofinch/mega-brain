#!/usr/bin/env python3
"""
ORGANIZED DOWNLOADER - Download com TAG
Mega Brain - Sistema de Inteligência de Negócios

Baixa arquivos do Google Drive JÁ com [TAG] no nome.
Organiza automaticamente em inbox/[SOURCE]/

USO: Este script é chamado pelo JARVIS via MCP, não diretamente.
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

# Configurações
MEGA_BRAIN = "."
INBOX = f"{MEGA_BRAIN}/inbox"
MISSION_CONTROL = f"{MEGA_BRAIN}/.claude/mission-control"
PLANILHA_INDEX = f"{MISSION_CONTROL}/PLANILHA-INDEX.json"
DOWNLOAD_LOG = f"{MISSION_CONTROL}/DOWNLOAD-LOG.json"

# Mapeamento de prefixo → pasta no INBOX
PREFIX_TO_FOLDER = {
    "JM": "JEREMY MINER",
    "JH-ST": "JEREMY HAYNES/SALES TRAINING",
    "JH-IC": "JEREMY HAYNES/INNER CIRCLE",
    "JH-WK": "JEREMY HAYNES/WEEKLY CALLS",
    "AOBA": "JEREMY HAYNES/AOBA",
    "PCVP": "JEREMY HAYNES/PCVP",
    "LYFC": "JEREMY HAYNES/LYFC",
    "MMM": "JEREMY HAYNES/MMM",
    "30DC": "JEREMY HAYNES/30DC",
    "STA": "JEREMY HAYNES/STA",
    "UHTC": "JEREMY HAYNES/UHTC",
    "CG": "COLE GORDON",
    "TSC": "COLE GORDON/TSC",
    "EDC": "COLE GORDON/EAD",
    "AH": "ALEX HORMOZI",
    "CA": "JEREMY HAYNES PROGRAM"
}


def sanitize_filename(name):
    """Remove caracteres inválidos do nome do arquivo."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()


def get_folder_for_tag(tag):
    """Retorna pasta de destino baseada no prefixo da TAG."""
    for prefix, folder in PREFIX_TO_FOLDER.items():
        if tag.startswith(prefix + "-"):
            return folder
    return "OUTROS"


def format_tagged_filename(tag, original_name):
    """Formata nome do arquivo com TAG."""
    clean_name = sanitize_filename(original_name)
    return f"[{tag}] {clean_name}"


def prepare_download_operations(tagged_entries):
    """
    Prepara operações de download para MCP.

    Args:
        tagged_entries: Lista de entradas já tagueadas na planilha
        Formato: [{'tag': 'JM-0001', 'name': '...', 'file_id': '...', ...}]

    Returns:
        Lista de operações de download
    """
    operations = []

    for entry in tagged_entries:
        tag = entry.get('tag', '')
        original_name = entry.get('name', entry.get('original_name', 'arquivo'))
        file_id = entry.get('file_id', entry.get('drive_id', ''))

        if not tag or not file_id:
            continue

        folder = get_folder_for_tag(tag)
        dest_folder = os.path.join(INBOX, folder)
        tagged_name = format_tagged_filename(tag, original_name)
        dest_path = os.path.join(dest_folder, tagged_name)

        operations.append({
            'type': 'download',
            'file_id': file_id,
            'original_name': original_name,
            'tagged_name': tagged_name,
            'tag': tag,
            'dest_folder': dest_folder,
            'dest_path': dest_path,
            'source': folder.split('/')[0] if '/' in folder else folder
        })

    return operations


def ensure_folders_exist(operations):
    """Cria pastas de destino se não existirem."""
    folders = set(op['dest_folder'] for op in operations)
    created = []

    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            created.append(folder)

    return created


def generate_download_report(operations):
    """Gera relatório de downloads."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_downloads': len(operations),
        'by_source': {},
        'operations': operations
    }

    for op in operations:
        source = op['source']
        if source not in report['by_source']:
            report['by_source'][source] = 0
        report['by_source'][source] += 1

    return report


def log_downloads(operations, success_ids):
    """Registra downloads realizados."""
    log_path = DOWNLOAD_LOG

    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            log = json.load(f)
    else:
        log = {'downloads': [], 'stats': {'total': 0, 'by_date': {}}}

    today = datetime.now().strftime('%Y-%m-%d')

    for op in operations:
        if op['file_id'] in success_ids:
            log['downloads'].append({
                'timestamp': datetime.now().isoformat(),
                'tag': op['tag'],
                'file_id': op['file_id'],
                'dest_path': op['dest_path']
            })
            log['stats']['total'] += 1

            if today not in log['stats']['by_date']:
                log['stats']['by_date'][today] = 0
            log['stats']['by_date'][today] += 1

    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    return log


def update_planilha_index(operations, success_ids):
    """Atualiza índice da planilha com status de download."""
    if not os.path.exists(PLANILHA_INDEX):
        return

    with open(PLANILHA_INDEX, 'r', encoding='utf-8') as f:
        index = json.load(f)

    downloaded_tags = {op['tag'] for op in operations if op['file_id'] in success_ids}

    for entry in index.get('entries', []):
        if entry.get('tag') in downloaded_tags:
            entry['downloaded'] = True
            entry['download_date'] = datetime.now().isoformat()

    with open(PLANILHA_INDEX, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def main(tagged_entries=None, preview=True):
    """
    Função principal do downloader.

    Args:
        tagged_entries: Lista de entradas já tagueadas
        preview: Se True, apenas mostra relatório

    Returns:
        Se preview=True: relatório
        Se preview=False: lista de operações para MCP
    """
    print("=" * 60)
    print("ORGANIZED DOWNLOADER - Download com TAG")
    print("=" * 60)
    print()

    if tagged_entries is None:
        print("[MODO STANDALONE]")
        print("Passe tagged_entries para executar.")
        return None

    operations = prepare_download_operations(tagged_entries)

    if not operations:
        print("✅ Nenhum download pendente!")
        return []

    report = generate_download_report(operations)

    print(f"Downloads preparados: {report['total_downloads']}")
    print()
    print("Por fonte:")
    for source, count in sorted(report['by_source'].items()):
        print(f"  {source}: {count}")
    print()

    if preview:
        print("Arquivos:")
        for i, op in enumerate(operations[:5], 1):
            print(f"  {i}. [{op['tag']}] → {op['source']}")
        if len(operations) > 5:
            print(f"  ... e mais {len(operations) - 5}")
        print()
        print("MODO PREVIEW - Nenhum download realizado.")
        return report

    # Criar pastas
    created_folders = ensure_folders_exist(operations)
    if created_folders:
        print(f"Pastas criadas: {len(created_folders)}")

    return operations


if __name__ == '__main__':
    main()
