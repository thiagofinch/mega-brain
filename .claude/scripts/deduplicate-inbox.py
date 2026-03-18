#!/usr/bin/env python3
"""
Deduplication Script - Remove duplicate files keeping only the most recent
"""

import os
import re
import shutil
from collections import defaultdict
from datetime import datetime

INBOX_PATH = "inbox"
BACKUP_PATH = os.path.join(INBOX_PATH, "_DEDUP_BACKUP")

def find_tagged_files():
    """Find all files with [TAG-XXXX] format"""
    tagged_files = defaultdict(list)
    tag_pattern = re.compile(r'^\[([A-Z0-9\-]+)\]')

    for root, dirs, files in os.walk(INBOX_PATH):
        # Skip the backup folder itself
        if "_DEDUP_BACKUP" in root:
            continue

        for filename in files:
            if not filename.endswith('.txt'):
                continue

            match = tag_pattern.match(filename)
            if match:
                tag = match.group(1)
                full_path = os.path.join(root, filename)
                mtime = os.path.getmtime(full_path)
                tagged_files[tag].append({
                    'filename': filename,
                    'path': full_path,
                    'mtime': mtime,
                    'rel_path': os.path.relpath(full_path, INBOX_PATH)
                })

    return tagged_files

def deduplicate(execute=False):
    """Remove duplicates, keeping the most recent file for each TAG"""

    print("=" * 70)
    print("DEDUPLICAÇÃO DO INBOX - MEGA BRAIN")
    print("=" * 70)
    print(f"\nModo: {'EXECUTAR' if execute else 'PREVIEW (--execute para aplicar)'}")
    print("=" * 70)

    # Ensure backup folder exists
    if execute and not os.path.exists(BACKUP_PATH):
        os.makedirs(BACKUP_PATH)

    tagged_files = find_tagged_files()

    # Stats
    total_tags = len(tagged_files)
    duplicated_tags = 0
    files_to_remove = 0

    duplicates_list = []

    for tag, files in sorted(tagged_files.items()):
        if len(files) > 1:
            duplicated_tags += 1
            # Sort by mtime descending (most recent first)
            files_sorted = sorted(files, key=lambda x: x['mtime'], reverse=True)
            keep = files_sorted[0]
            remove = files_sorted[1:]

            print(f"\n[{tag}] {len(files)} cópias encontradas:")
            print(f"  ✓ MANTER: {keep['rel_path']}")
            print(f"    (modificado: {datetime.fromtimestamp(keep['mtime']).strftime('%Y-%m-%d %H:%M')})")

            for f in remove:
                files_to_remove += 1
                print(f"  ✗ REMOVER: {f['rel_path']}")
                print(f"    (modificado: {datetime.fromtimestamp(f['mtime']).strftime('%Y-%m-%d %H:%M')})")
                duplicates_list.append({
                    'tag': tag,
                    'file': f,
                    'keep': keep
                })

    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    print(f"Total de TAGs únicas: {total_tags}")
    print(f"TAGs com duplicatas: {duplicated_tags}")
    print(f"Arquivos a remover: {files_to_remove}")

    if execute and duplicates_list:
        print("\n" + "=" * 70)
        print("EXECUTANDO REMOÇÃO")
        print("=" * 70)

        success = 0
        errors = 0

        for dup in duplicates_list:
            src = dup['file']['path']
            # Create subfolder in backup based on original relative path
            rel_dir = os.path.dirname(dup['file']['rel_path'])
            if rel_dir:
                dest_dir = os.path.join(BACKUP_PATH, rel_dir)
            else:
                dest_dir = BACKUP_PATH

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            dest = os.path.join(dest_dir, dup['file']['filename'])

            try:
                shutil.move(src, dest)
                print(f"✓ Movido: {dup['file']['rel_path']}")
                success += 1
            except Exception as e:
                print(f"✗ Erro: {dup['file']['rel_path']} - {e}")
                errors += 1

        print("\n" + "=" * 70)
        print("RESULTADO FINAL")
        print("=" * 70)
        print(f"✓ Arquivos movidos para backup: {success}")
        print(f"✗ Erros: {errors}")
        print(f"\nBackup em: {BACKUP_PATH}")

    elif not execute:
        print(f"\nExecute com: python3 deduplicate-inbox.py --execute")

    return duplicated_tags, files_to_remove

if __name__ == "__main__":
    import sys
    execute = '--execute' in sys.argv
    deduplicate(execute)
