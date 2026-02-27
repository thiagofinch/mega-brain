#!/usr/bin/env python3
"""
FASE 2.5 - Script de Tagueamento de Arquivos INBOX
Mega Brain - Sistema de Inteligencia de Negocios

Este script:
1. Le a planilha de controle e extrai mapeamento nome -> TAG
2. Varre todos os arquivos do INBOX recursivamente
3. Faz matching entre arquivos e TAGs
4. Renomeia arquivos com prefixo [TAG]
5. Gera relatorio de arquivos processados vs orfaos
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

# Configuracoes
INBOX_PATH = "inbox"
SCHEMA_PATH = ".claude/mission-control/SPREADSHEET-SCHEMA.json"
OUTPUT_PATH = ".claude/mission-control/TAG-MAPPING-REPORT.json"

# Mapeamento de pasta INBOX -> prefixo TAG
FOLDER_TO_PREFIX = {
    "JEREMY MINER": "JM",
    "JEREMY HAYNES": ["JH-ST", "JH-IC", "JH-WK", "AOBA", "PCVP", "LYFC", "MMM", "30DC", "STA", "UHTC"],
    "THE SCALABLE COMPANY": "TSC",
    "ALEX HORMOZI": "AH",
    "JEREMY HAYNES PROGRAM": "CA",
    "SAM OVEN (SETTERLUN UNIVERSITY)": None,  # Nao tem na planilha ainda
    "SETTERLUN (SETTERLUN UNIVERSITY)": None,
}

def extract_number_from_filename(filename):
    """Extrai o numero do inicio do nome do arquivo."""
    # Padroes comuns:
    # "6 - 42 Minutes of Sales Training.txt"
    # "112. How To Get Prospects.txt"
    # "44 - LIVE CALL A Masterclass.txt"

    patterns = [
        r'^(\d+)\s*[-\.]\s*',  # "123 - " ou "123. "
        r'^(\d+)\.\s*',        # "123. "
        r'^(\d+)\s+',          # "123 "
    ]

    for pattern in patterns:
        match = re.match(pattern, filename)
        if match:
            return int(match.group(1))
    return None

def clean_filename_for_matching(filename):
    """Limpa o nome do arquivo para facilitar matching."""
    # Remove extensao
    name = os.path.splitext(filename)[0]
    # Remove timestamps no final
    name = re.sub(r'_\d{14}$', '', name)
    # Remove numero inicial
    name = re.sub(r'^\d+\s*[-\.]\s*', '', name)
    # Lowercase e remove caracteres especiais
    name = name.lower()
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def determine_prefix_from_path(filepath):
    """Determina o prefixo TAG baseado no caminho do arquivo."""
    path_str = str(filepath).upper()

    for folder, prefix in FOLDER_TO_PREFIX.items():
        if folder in path_str:
            return prefix
    return None

def scan_inbox_files():
    """Varre todos os arquivos do INBOX recursivamente."""
    files = []
    extensions = {'.txt', '.docx', '.pdf'}

    for root, dirs, filenames in os.walk(INBOX_PATH):
        # Ignorar pastas de backup/template
        if '_BACKUP' in root or '_TEMPLATE' in root:
            continue

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in extensions:
                filepath = Path(root) / filename

                # Verificar se ja tem TAG no nome
                has_tag = bool(re.match(r'^\[[\w-]+\]', filename))

                files.append({
                    'path': str(filepath),
                    'filename': filename,
                    'folder': os.path.basename(root),
                    'parent_folder': os.path.basename(os.path.dirname(root)),
                    'number': extract_number_from_filename(filename),
                    'clean_name': clean_filename_for_matching(filename),
                    'has_tag': has_tag,
                    'suggested_prefix': determine_prefix_from_path(filepath)
                })

    return files

def generate_tag_from_number(prefix, number):
    """Gera TAG no formato [PREFIX]-[NNNN]."""
    if isinstance(prefix, list):
        prefix = prefix[0]  # Usar primeiro prefixo como padrao
    return f"{prefix}-{number:04d}"

def rename_file_with_tag(filepath, tag):
    """Renomeia arquivo adicionando prefixo [TAG]."""
    path = Path(filepath)
    new_name = f"[{tag}] {path.name}"
    new_path = path.parent / new_name

    # Verificar se destino ja existe
    if new_path.exists():
        return None, "Destino ja existe"

    try:
        path.rename(new_path)
        return str(new_path), None
    except Exception as e:
        return None, str(e)

def execute_rename(report, dry_run=False):
    """Executa a renomeacao dos arquivos."""
    print()
    print("=" * 60)
    print("EXECUTANDO RENOMEACAO" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)
    print()

    success = 0
    errors = []

    for item in report['to_tag']:
        filepath = item['current_path']
        tag = item['suggested_tag']

        if dry_run:
            path = Path(filepath)
            new_name = f"[{tag}] {path.name}"
            print(f"  [DRY] {path.name}")
            print(f"     -> {new_name}")
            success += 1
        else:
            new_path, error = rename_file_with_tag(filepath, tag)
            if error:
                errors.append({'path': filepath, 'error': error})
                print(f"  [ERRO] {item['filename']}: {error}")
            else:
                success += 1
                if success % 50 == 0:
                    print(f"  Renomeados: {success}/{len(report['to_tag'])}")

    print()
    print("=" * 60)
    print("RESULTADO")
    print("=" * 60)
    print(f"  Sucesso: {success}")
    print(f"  Erros: {len(errors)}")

    if errors:
        print()
        print("ERROS:")
        for e in errors[:10]:  # Mostrar apenas primeiros 10
            print(f"  - {e['path']}: {e['error']}")
        if len(errors) > 10:
            print(f"  ... e mais {len(errors) - 10} erros")

    return success, errors


def main(execute=False, dry_run=False):
    print("=" * 60)
    print("FASE 2.5 - TAGUEAMENTO DE ARQUIVOS INBOX")
    print("=" * 60)
    print()

    # 1. Carregar schema
    print("[1/4] Carregando schema...")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    # 2. Escanear arquivos
    print("[2/4] Escaneando INBOX...")
    files = scan_inbox_files()
    print(f"       Encontrados: {len(files)} arquivos")

    # 3. Classificar arquivos
    print("[3/4] Classificando arquivos...")

    already_tagged = [f for f in files if f['has_tag']]
    to_tag = [f for f in files if not f['has_tag'] and f['suggested_prefix'] and f['number']]
    orphans = [f for f in files if not f['has_tag'] and (not f['suggested_prefix'] or not f['number'])]

    print(f"       Ja tagueados: {len(already_tagged)}")
    print(f"       Para taguear: {len(to_tag)}")
    print(f"       Orfaos: {len(orphans)}")

    # 4. Gerar relatorio
    print("[4/4] Gerando relatorio...")

    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_files': len(files),
            'already_tagged': len(already_tagged),
            'to_tag': len(to_tag),
            'orphans': len(orphans)
        },
        'to_tag': [],
        'orphans': []
    }

    for f in to_tag:
        prefix = f['suggested_prefix']
        if isinstance(prefix, list):
            prefix = prefix[0]
        tag = generate_tag_from_number(prefix, f['number'])
        report['to_tag'].append({
            'current_path': f['path'],
            'suggested_tag': tag,
            'filename': f['filename'],
            'folder': f['folder']
        })

    for f in orphans:
        report['orphans'].append({
            'path': f['path'],
            'filename': f['filename'],
            'folder': f['folder'],
            'reason': 'Sem prefixo conhecido' if not f['suggested_prefix'] else 'Sem numero no nome'
        })

    # Salvar relatorio
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print("RELATORIO GERADO")
    print("=" * 60)
    print(f"Arquivo: {OUTPUT_PATH}")

    # 5. Executar renomeacao se solicitado
    if execute:
        success, errors = execute_rename(report, dry_run)
        report['execution'] = {
            'success': success,
            'errors': len(errors),
            'error_details': errors
        }
        # Atualizar relatorio com resultado
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    else:
        print()
        print("PROXIMO PASSO: Executar com --execute para renomear")
        print("              Ou --dry-run para simular")

    print()
    return report


if __name__ == '__main__':
    import sys
    execute = '--execute' in sys.argv
    dry_run = '--dry-run' in sys.argv
    main(execute=execute, dry_run=dry_run)
