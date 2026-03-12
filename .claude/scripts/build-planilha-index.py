#!/usr/bin/env python3
"""
BUILD PLANILHA INDEX - Cria índice nome→TAG da planilha
Processa os arquivos JSON exportados das abas do Google Sheets
"""

import os
import re
import json
from datetime import datetime

# Configurações
TOOL_RESULTS_PATH = ""  # Set to your Claude tool-results path
OUTPUT_PATH = ".claude/mission-control/PLANILHA-INDEX.json"
SCHEMA_PATH = ".claude/mission-control/SPREADSHEET-SCHEMA.json"

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
    # Remove caracteres especiais
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def process_sheet_data(data, sheet_name, tag_col_index):
    """Processa dados de uma aba e extrai entradas."""
    entries = []

    for row in data:
        if not row or len(row) < tag_col_index + 1:
            continue

        # Extrair valores relevantes
        name_cell = row[0] if len(row) > 0 else None  # Coluna B (nome)
        tag_cell = row[tag_col_index] if len(row) > tag_col_index else None

        if not name_cell or not tag_cell:
            continue

        name = name_cell.get('value', '') if isinstance(name_cell, dict) else str(name_cell)
        tag = tag_cell.get('value', '') if isinstance(tag_cell, dict) else str(tag_cell)

        # Verificar se TAG é válida
        if not tag or not re.match(r'^[\w-]+-\d{4}$', tag):
            continue

        entries.append({
            'original_name': name,
            'normalized': normalize_name(name),
            'tag': tag,
            'sheet': sheet_name
        })

    return entries

def main():
    print("=" * 60)
    print("BUILD PLANILHA INDEX")
    print("=" * 60)
    print()

    # Carregar schema para saber configuração de cada aba
    print("[1/3] Carregando schema...")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    # Encontrar arquivos JSON do Google Sheets
    print("[2/3] Processando dados exportados...")

    # Dados inline do Sales Training (copiados do resultado anterior)
    # Por agora, vou criar entradas manualmente baseadas no schema

    entries = []

    # Dados do Jeremy Haynes Sales Training (processado inline)
    jh_st_data = [
        ("1 - Introduction to Sales Training", "JH-ST-0001"),
        ("2. The Plague of Fat Cat Closers", "JH-ST-0002"),
        ("3. How to Deal With Inbound Leads Who Only Filled Out a Form", "JH-ST-0003"),
        ("4. Sales Team Structures to Consider", "JH-ST-0004"),
        ("5. The Cleaner Role", "JH-ST-0005"),
        ("6. Using Sales Videos to Aid The Sales Process", "JH-ST-0006"),
        ("7. Selfie Follow up Video Texts Get an iphone", "JH-ST-0007"),
        ("8. Get Leads Back on The Phone With Value Driven Follow up", "JH-ST-0008"),
        ("9. How to Increase Show Rate", "JH-ST-0009"),
        ("10.Why You Should Text Every Lead Manually", "JH-ST-0010"),
        ("11. Value Added vs Selfish Questions", "JH-ST-0011"),
        ("12. Value Added Questions vs Selfish Questions", "JH-ST-0012"),
        ("13. How to Increase Average Order Value", "JH-ST-0013"),
        ("14. How to Recruit Sales People", "JH-ST-0014"),
        ("15. How to Train Maintain a Great Sales Team", "JH-ST-0015"),
        ("16. Why Full Time Closers Are Better", "JH-ST-0016"),
        ("17. How to Raise The Value of The Price", "JH-ST-0017"),
        ("18. Raising The Clients Interest Level", "JH-ST-0018"),
        ("19. How to Create Real Scarcity Urgency", "JH-ST-0019"),
        ("20. Reviewing Calls Providing Feedback", "JH-ST-0020"),
        ("21. Your Personal Life Impacts Your Professional Life", "JH-ST-0021"),
        ("22. Tools Software For Closers", "JH-ST-0022"),
        ("23. When to Fire Sales Reps", "JH-ST-0023"),
        ("24. Keep Your Moral High", "JH-ST-0024"),
        ("25. Sales Training With Jordan Stupar", "JH-ST-0025"),
        ("26. Sales Training With Josh Troy", "JH-ST-0026"),
        ("1. Intro to Objections", "JH-ST-0028"),
        ("2. What Happens if You go Out of Business", "JH-ST-0029"),
        ("3. How do I Know my Money is Safe", "JH-ST-0030"),
        ("4. Can I Speak to The Owner", "JH-ST-0031"),
        ("5. How Can You Guarantee That Ill Make Money", "JH-ST-0032"),
        ("6. Why Are You Better Than Everybody Else", "JH-ST-0033"),
        ("7. Id Rather Get Started Next Quarter", "JH-ST-0034"),
        ("8. I Have to Get my Lawyer to Review Before Moving Forward", "JH-ST-0035"),
        ("9. My Business Partner I Will Need To Review This", "JH-ST-0036"),
        ("10. Im Traveling This Week Lets Move Forward Next Week", "JH-ST-0037"),
        ("11. Are You Open to Changes in The Agreement", "JH-ST-0038"),
        ("12. Can I Speak to an Existing Client", "JH-ST-0039"),
        ("13. I Saw a Negative Review Im Afraid Itll Happen to me", "JH-ST-0040"),
        ("14. Objection I Cant Afford This", "JH-ST-0041"),
        ("15. Objection I Cant Afford This", "JH-ST-0042"),
        ("16. Objection I Cant Afford This", "JH-ST-0043"),
        ("17. I Didnt Expect it to Cost This Much", "JH-ST-0044"),
        ("18. I am Looking at Other Service Providers", "JH-ST-0045"),
    ]

    for name, tag in jh_st_data:
        entries.append({
            'original_name': name,
            'normalized': normalize_name(name),
            'tag': tag,
            'sheet': 'Jeremy Haynes Sales Training'
        })

    print(f"       Processadas {len(entries)} entradas iniciais")
    print()
    print("  NOTA: Este script precisa ser expandido para processar todas as abas")
    print("        via API do Google Sheets ou arquivos JSON exportados.")
    print()

    # 3. Salvar índice
    print("[3/3] Salvando índice...")

    index = {
        'version': '1.0',
        'timestamp': datetime.now().isoformat(),
        'total_entries': len(entries),
        'sheets_processed': list(set(e['sheet'] for e in entries)),
        'entries': entries
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"       Salvo em: {OUTPUT_PATH}")
    print(f"       Total: {len(entries)} entradas")
    print()
    print("=" * 60)
    print("ÍNDICE CRIADO (parcial)")
    print("=" * 60)

    return index

if __name__ == '__main__':
    main()
