#!/usr/bin/env python3
"""
FASE 2.5 v2 - Tagueamento por MATCHING DE NOMES
Mega Brain - Sistema de Inteligência de Negócios

ABORDAGEM CORRETA:
1. Extrair de TODAS as abas: nome_video → TAG
2. Para cada arquivo INBOX, fazer matching por nome similar
3. Se match encontrado, usar TAG da planilha
4. Se não, manter órfão
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

# Configurações
INBOX_PATH = "inbox"
SCHEMA_PATH = ".claude/mission-control/SPREADSHEET-SCHEMA.json"
INDEX_PATH = ".claude/mission-control/PLANILHA-INDEX.json"
OUTPUT_PATH = ".claude/mission-control/TAG-MAPPING-V2.json"

def normalize_name(name):
    """Normaliza nome para matching."""
    # Remove extensão
    name = os.path.splitext(name)[0]
    # Lowercase
    name = name.lower()
    # Remove timestamps
    name = re.sub(r'_\d{14}$', '', name)
    name = re.sub(r'\d{1,2}-\d{1,2}-\d{2,4}', '', name)  # Remove datas tipo 12-25-24
    # Remove número inicial
    name = re.sub(r'^\d+[\s\.\-]+', '', name)
    # Remove [youtube.com...] e similares
    name = re.sub(r'\[youtube\.com[^\]]*\]', '', name)
    name = re.sub(r'\[[^\]]*\]', '', name)
    # Remove (1), (2), etc
    name = re.sub(r'\s*\(\d+\)\s*', '', name)
    # Remove caracteres especiais
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def similar(a, b):
    """Calcula similaridade entre dois nomes (0-1)."""
    return SequenceMatcher(None, a, b).ratio()

def load_planilha_index():
    """Carrega índice da planilha (nome → TAG)."""
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def scan_inbox_files():
    """Varre todos os arquivos do INBOX."""
    files = []
    extensions = {'.txt', '.docx', '.pdf'}

    for root, dirs, filenames in os.walk(INBOX_PATH):
        if '_BACKUP' in root or '_TEMPLATE' in root:
            continue

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in extensions:
                filepath = Path(root) / filename

                # Verificar se já tem TAG
                has_tag = bool(re.match(r'^\[[\w-]+\]', filename))

                files.append({
                    'path': str(filepath),
                    'filename': filename,
                    'folder': os.path.basename(root),
                    'parent_folder': os.path.basename(os.path.dirname(root)),
                    'normalized': normalize_name(filename),
                    'has_tag': has_tag
                })

    return files

def match_file_to_index(file_info, index, threshold=0.7):
    """Tenta encontrar match no índice da planilha."""
    normalized_name = file_info['normalized']

    if not normalized_name:
        return None, 0

    best_match = None
    best_score = 0

    for entry in index['entries']:
        # Comparar com nome normalizado da planilha
        score = similar(normalized_name, entry['normalized'])
        if score > best_score and score >= threshold:
            best_score = score
            best_match = entry

    return best_match, best_score

def main(execute=False, threshold=0.7):
    print("=" * 60)
    print("FASE 2.5 v2 - TAGUEAMENTO POR MATCHING")
    print("=" * 60)
    print()

    # 1. Carregar índice da planilha
    print("[1/4] Carregando índice da planilha...")
    index = load_planilha_index()
    if not index:
        print("  ERRO: Índice não encontrado!")
        print("  Execute primeiro: /criar-indice-planilha")
        return None
    print(f"       {len(index['entries'])} entradas no índice")

    # 2. Escanear INBOX
    print("[2/4] Escaneando INBOX...")
    files = scan_inbox_files()
    print(f"       {len(files)} arquivos encontrados")

    # 3. Fazer matching
    print(f"[3/4] Matching (threshold={threshold})...")

    matched = []
    orphans = []
    already_tagged = []

    for f in files:
        if f['has_tag']:
            already_tagged.append(f)
            continue

        match, score = match_file_to_index(f, index, threshold)
        if match:
            matched.append({
                'file': f,
                'match': match,
                'score': score
            })
        else:
            orphans.append(f)

    print(f"       Já tagueados: {len(already_tagged)}")
    print(f"       Match encontrado: {len(matched)}")
    print(f"       Órfãos: {len(orphans)}")

    # 4. Gerar relatório
    print("[4/4] Gerando relatório...")

    report = {
        'timestamp': datetime.now().isoformat(),
        'threshold': threshold,
        'summary': {
            'total_files': len(files),
            'already_tagged': len(already_tagged),
            'matched': len(matched),
            'orphans': len(orphans)
        },
        'matches': [],
        'orphans': []
    }

    for m in matched:
        report['matches'].append({
            'current_path': m['file']['path'],
            'filename': m['file']['filename'],
            'folder': m['file']['folder'],
            'matched_to': m['match']['original_name'],
            'tag': m['match']['tag'],
            'sheet': m['match']['sheet'],
            'score': round(m['score'], 3)
        })

    for o in orphans:
        report['orphans'].append({
            'path': o['path'],
            'filename': o['filename'],
            'folder': o['folder'],
            'normalized': o['normalized']
        })

    # Salvar relatório
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print("RELATÓRIO GERADO")
    print("=" * 60)
    print(f"Arquivo: {OUTPUT_PATH}")

    # 5. Executar renomeação se solicitado
    if execute and matched:
        print()
        print("=" * 60)
        print("EXECUTANDO RENOMEAÇÃO")
        print("=" * 60)

        success = 0
        errors = []

        for m in matched:
            filepath = Path(m['file']['path'])
            tag = m['match']['tag']
            new_name = f"[{tag}] {filepath.name}"
            new_path = filepath.parent / new_name

            if new_path.exists():
                errors.append({'path': str(filepath), 'error': 'Destino já existe'})
                continue

            try:
                filepath.rename(new_path)
                success += 1
                if success % 50 == 0:
                    print(f"  Renomeados: {success}/{len(matched)}")
            except Exception as e:
                errors.append({'path': str(filepath), 'error': str(e)})

        print()
        print(f"Sucesso: {success}")
        print(f"Erros: {len(errors)}")

        report['execution'] = {
            'success': success,
            'errors': len(errors),
            'error_details': errors
        }

        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    else:
        print()
        print("PRÓXIMO PASSO: Execute com --execute para renomear")
        print(f"              Threshold atual: {threshold}")
        print("              Use --threshold=0.6 para matching mais flexível")

    return report


if __name__ == '__main__':
    import sys
    execute = '--execute' in sys.argv
    threshold = 0.7
    for arg in sys.argv:
        if arg.startswith('--threshold='):
            threshold = float(arg.split('=')[1])
    main(execute=execute, threshold=threshold)
