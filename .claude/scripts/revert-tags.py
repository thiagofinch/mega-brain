#!/usr/bin/env python3
"""
REVERT - Remove TAGs incorretas dos arquivos
"""

import os
import re
from pathlib import Path

INBOX_PATH = "inbox"

def revert_tags():
    print("=" * 60)
    print("REVERTENDO TAGS INCORRETAS")
    print("=" * 60)

    # Encontrar arquivos com TAG
    tagged_files = []
    pattern = re.compile(r'^\[[\w-]+\]\s*')

    for root, dirs, files in os.walk(INBOX_PATH):
        if '_BACKUP' in root or '_TEMPLATE' in root:
            continue
        for filename in files:
            if pattern.match(filename):
                tagged_files.append(Path(root) / filename)

    print(f"\nEncontrados: {len(tagged_files)} arquivos com TAG")

    # Reverter
    success = 0
    errors = []

    for filepath in tagged_files:
        old_name = filepath.name
        # Remove [TAG] do início
        new_name = pattern.sub('', old_name)
        new_path = filepath.parent / new_name

        # Verificar se destino já existe
        if new_path.exists():
            errors.append({'path': str(filepath), 'error': f'Destino já existe: {new_name}'})
            continue

        try:
            filepath.rename(new_path)
            success += 1
            if success % 50 == 0:
                print(f"  Revertidos: {success}/{len(tagged_files)}")
        except Exception as e:
            errors.append({'path': str(filepath), 'error': str(e)})

    print()
    print("=" * 60)
    print("RESULTADO")
    print("=" * 60)
    print(f"  Sucesso: {success}")
    print(f"  Erros: {len(errors)}")

    if errors:
        print("\nERROS:")
        for e in errors[:20]:
            print(f"  - {e['path']}: {e['error']}")
        if len(errors) > 20:
            print(f"  ... e mais {len(errors) - 20} erros")

    return success, errors

if __name__ == '__main__':
    revert_tags()
