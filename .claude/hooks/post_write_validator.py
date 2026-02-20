#!/usr/bin/env python3
"""
POST-WRITE VALIDATOR HOOK
=========================
Valida automaticamente arquivos criados/editados.

Baseado no workflow Boris Cherny: "give Claude a way to verify its work"

Triggers:
- Após Write de BATCH-*.md → Valida estrutura do batch
- Após Write de AGENT.md → Valida template V3
- Após Write de SOUL.md → Valida rastreabilidade
- Após Write de DNA-CONFIG.yaml → Valida estrutura

Output:
- Se válido: exit 0 (silencioso)
- Se inválido: print erros para Claude corrigir
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime

# Paths
PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
LOGS_PATH = PROJECT_ROOT / 'logs' / 'validation'
LOGS_PATH.mkdir(parents=True, exist_ok=True)

def log_validation(file_path: str, file_type: str, is_valid: bool, errors: list):
    """Log validation result"""
    log_file = LOGS_PATH / 'validation.jsonl'
    entry = {
        'timestamp': datetime.now().isoformat(),
        'file': file_path,
        'type': file_type,
        'valid': is_valid,
        'errors': errors
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def validate_batch(content: str, file_path: str) -> tuple[bool, list]:
    """Validate BATCH-*.md structure"""
    errors = []

    # Required sections
    required_sections = [
        ('ASCII ART HEADER', r'[╔═╗║╚]'),
        ('CONTEXTO DA MISSÃO', r'CONTEXTO DA MISS[ÃA]O|MISSION CONTEXT'),
        ('BATCH SUMMARY', r'BATCH SUMMARY|RESUMO DO BATCH'),
        ('ARQUIVOS PROCESSADOS', r'ARQUIVOS PROCESSADOS|FILES PROCESSED'),
        ('DESTINO DO CONHECIMENTO', r'DESTINO DO CONHECIMENTO|KNOWLEDGE DESTINATION'),
        ('KEY FRAMEWORKS', r'KEY FRAMEWORKS|FRAMEWORKS'),
    ]

    for section_name, pattern in required_sections:
        if not re.search(pattern, content, re.IGNORECASE):
            errors.append(f"Missing section: {section_name}")

    # Check for cascading section (REGRA #22)
    if 'Cascateamento Executado' not in content and 'CASCATEAMENTO' not in content.upper():
        errors.append("Missing section: Cascateamento Executado (REGRA #22)")

    # Check for DNA layers
    dna_layers = ['FILOSOFIA', 'MODELO-MENTAL', 'HEURISTICA', 'FRAMEWORK', 'METODOLOGIA']
    found_layers = sum(1 for layer in dna_layers if layer in content.upper())
    if found_layers < 3:
        errors.append(f"Only {found_layers}/5 DNA layers found. Expected at least 3.")

    is_valid = len(errors) == 0
    log_validation(file_path, 'BATCH', is_valid, errors)
    return is_valid, errors

def validate_agent(content: str, file_path: str) -> tuple[bool, list]:
    """Validate AGENT.md template V3 structure"""
    errors = []

    # Required parts from Template V3
    required_parts = [
        ('PARTE 0: ÍNDICE', r'PARTE 0|ÍNDICE|INDEX'),
        ('PARTE 1: COMPOSIÇÃO', r'PARTE 1|COMPOSI[ÇC][ÃA]O'),
        ('PARTE 3: MAPA NEURAL', r'PARTE 3|MAPA NEURAL|DNA'),
        ('PARTE 5: SISTEMA DE VOZ', r'PARTE 5|VOZ|VOICE'),
    ]

    for part_name, pattern in required_parts:
        if not re.search(pattern, content, re.IGNORECASE):
            errors.append(f"Missing: {part_name}")

    # Check for ASCII header
    if not re.search(r'[╔═╗║╚]', content):
        errors.append("Missing ASCII art header")

    # Check for version
    if not re.search(r'[Vv]ers[ãa]o|Version', content):
        errors.append("Missing version declaration")

    # Check for sources/fontes
    if not re.search(r'[Ff]ontes?|[Ss]ources?', content):
        errors.append("Missing source attribution")

    is_valid = len(errors) == 0
    log_validation(file_path, 'AGENT', is_valid, errors)
    return is_valid, errors

def validate_soul(content: str, file_path: str) -> tuple[bool, list]:
    """Validate SOUL.md rastreabilidade"""
    errors = []

    # Check for source citations
    citation_patterns = [
        r'\^\[FONTE:',
        r'\^\[chunk_id',
        r'\^\[insight_id',
        r'\^\[RAIZ:',
        r'\[FONTE:',
    ]

    has_citations = any(re.search(p, content) for p in citation_patterns)
    if not has_citations:
        errors.append("No traceable citations found (REGRA #24 requires ^[FONTE:] or similar)")

    # Check for DNA layers
    if not re.search(r'FILOSOFIA|MODELO.MENTAL|HEURISTICA|FRAMEWORK|METODOLOGIA', content, re.IGNORECASE):
        errors.append("No DNA layers referenced")

    is_valid = len(errors) == 0
    log_validation(file_path, 'SOUL', is_valid, errors)
    return is_valid, errors

def validate_dna_config(content: str, file_path: str) -> tuple[bool, list]:
    """Validate DNA-CONFIG.yaml structure"""
    errors = []

    # Required fields
    required_fields = ['name', 'type', 'version']
    for field in required_fields:
        if f'{field}:' not in content.lower():
            errors.append(f"Missing required field: {field}")

    # Check for layers
    layers = ['filosofias', 'modelos_mentais', 'heuristicas', 'frameworks', 'metodologias']
    found_layers = sum(1 for layer in layers if layer in content.lower())
    if found_layers < 3:
        errors.append(f"Only {found_layers}/5 DNA layers defined")

    is_valid = len(errors) == 0
    log_validation(file_path, 'DNA_CONFIG', is_valid, errors)
    return is_valid, errors

def main():
    """Main validation dispatcher"""
    if len(sys.argv) < 2:
        sys.exit(0)

    file_path = sys.argv[1]

    # Skip if file doesn't exist or is not relevant
    if not os.path.exists(file_path):
        sys.exit(0)

    filename = os.path.basename(file_path).upper()

    # Determine file type and validate
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        sys.exit(0)

    is_valid = True
    errors = []

    if 'BATCH-' in filename and filename.endswith('.MD'):
        is_valid, errors = validate_batch(content, file_path)
    elif filename == 'AGENT.MD':
        is_valid, errors = validate_agent(content, file_path)
    elif filename == 'SOUL.MD':
        is_valid, errors = validate_soul(content, file_path)
    elif 'DNA-CONFIG' in filename and filename.endswith('.YAML'):
        is_valid, errors = validate_dna_config(content, file_path)
    else:
        # Not a file we validate
        sys.exit(0)

    # Output for Claude to see
    if not is_valid:
        print(f"\n⚠️ VALIDATION FAILED for {os.path.basename(file_path)}:")
        for error in errors:
            print(f"  ❌ {error}")
        print("\nPlease fix these issues before proceeding.\n")
        # Exit 0 anyway to not block, but Claude sees the output

    sys.exit(0)

if __name__ == '__main__':
    main()
