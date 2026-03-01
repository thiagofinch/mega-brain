#!/usr/bin/env python3
"""
JARVIS Memory Updater Hook
Atualiza JARVIS-MEMORY.md automaticamente.

Triggers:
- Decisoes importantes detectadas
- Preferencias demonstradas
- Final de sessao
- Padroes de comportamento observados
"""

import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

def get_project_dir():
    """Obtem o diretorio do projeto."""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

def load_memory():
    """Carrega JARVIS-MEMORY.md atual."""
    project_dir = get_project_dir()
    memory_path = Path(project_dir) / '.claude' / 'jarvis' / 'JARVIS-MEMORY.md'

    if memory_path.exists():
        with open(memory_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def detect_decision(message):
    """Detecta se a mensagem contem uma decisao importante."""
    decision_patterns = [
        r'decid[io]',
        r'escolh[eo]',
        r'prefer[eo]',
        r'vamos (usar|fazer|implementar)',
        r'aprovo',
        r'confirmo',
        r'sim,?\s*(pode|faz|continua)',
        r'nao,?\s*(nao pode|nao faz)',
    ]

    message_lower = message.lower()
    for pattern in decision_patterns:
        if re.search(pattern, message_lower):
            return True
    return False

def detect_preference(message):
    """Detecta se a mensagem demonstra uma preferencia."""
    preference_patterns = [
        r'gosto (de|quando)',
        r'prefiro',
        r'sempre (quero|faz)',
        r'nunca (quero|faz)',
        r'melhor (assim|dessa forma)',
        r'perfeito',
    ]

    message_lower = message.lower()
    for pattern in preference_patterns:
        if re.search(pattern, message_lower):
            return True
    return False

def extract_decision_summary(message):
    """Extrai um resumo da decisao."""
    # Limitar a 100 caracteres
    summary = message[:100]
    if len(message) > 100:
        summary += "..."
    return summary

def update_memory_file(section, content):
    """Atualiza uma secao especifica do JARVIS-MEMORY.md."""
    project_dir = get_project_dir()
    memory_path = Path(project_dir) / '.claude' / 'jarvis' / 'JARVIS-MEMORY.md'

    if not memory_path.exists():
        return False

    with open(memory_path, 'r', encoding='utf-8') as f:
        memory = f.read()

    original_memory = memory  # snapshot for audit diff

    # Encontrar secao de decisoes e adicionar
    if section == 'decisions':
        # Procurar por "### Decisoes Importantes"
        if '### Decisoes Importantes' in memory:
            # Adicionar nova decisao
            date_str = datetime.now().strftime('%Y-%m-%d')
            new_entry = f"\n{date_str}:\n├─ {content}\n"

            # Inserir apos o header da secao
            parts = memory.split('### Decisoes Importantes')
            if len(parts) == 2:
                # Encontrar o bloco de codigo
                if '```' in parts[1]:
                    code_start = parts[1].find('```')
                    code_end = parts[1].find('```', code_start + 3)
                    if code_end > code_start:
                        # Inserir antes do fechamento do bloco
                        before = parts[1][:code_end]
                        after = parts[1][code_end:]
                        parts[1] = before + new_entry + after
                        memory = '### Decisoes Importantes'.join(parts)

    # Atualizar timestamp
    memory = re.sub(
        r'\*Ultima atualizacao: \d{4}-\d{2}-\d{2}\*',
        f'*Ultima atualizacao: {datetime.now().strftime("%Y-%m-%d")}*',
        memory
    )

    # Incrementar contador de interacoes
    match = re.search(r'\*Interacoes registradas: (\d+)\*', memory)
    if match:
        count = int(match.group(1)) + 1
        memory = re.sub(
            r'\*Interacoes registradas: \d+\*',
            f'*Interacoes registradas: {count}*',
            memory
        )

    with open(memory_path, 'w', encoding='utf-8') as f:
        f.write(memory)

    # Audit: log what changed
    if memory != original_memory:
        diff_lines = len(memory.splitlines()) - len(original_memory.splitlines())
        audit_file_modification(
            str(memory_path),
            f'update_section:{section}',
            f'+{diff_lines} lines, content: {content[:100]}'
        )

    return True

def log_update(update_type, content):
    """Loga a atualizacao de memoria."""
    project_dir = get_project_dir()
    log_path = Path(project_dir) / 'logs' / 'memory_updates.jsonl'
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': update_type,
        'content': content[:200]
    }

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

def audit_file_modification(file_path, modification_type, diff_summary):
    """Audit log for ALL file modifications made by this hook."""
    project_dir = get_project_dir()
    audit_path = Path(project_dir) / 'logs' / 'memory-audit.jsonl'
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'file_modified': str(file_path),
        'modification_type': modification_type,
        'diff_summary': diff_summary[:500]
    }

    try:
        with open(audit_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry, ensure_ascii=False) + '\n')
    except Exception:
        pass  # Audit logging should never block the hook

def main():
    """Funcao principal do hook."""
    try:
        # Ler input do hook
        input_data = sys.stdin.read()
        if not input_data:
            print(json.dumps({'continue': True}))
            return

        hook_input = json.loads(input_data)

        # Extrair mensagem do usuario (se disponivel)
        message = hook_input.get('message', '')
        if not message:
            # Tentar extrair de outros campos
            message = hook_input.get('content', '')
            if not message:
                message = hook_input.get('text', '')

        if not message:
            print(json.dumps({'continue': True}))
            return

        updated = False

        # Detectar decisoes
        if detect_decision(message):
            summary = extract_decision_summary(message)
            if update_memory_file('decisions', summary):
                log_update('decision', summary)
                updated = True

        # Detectar preferencias
        if detect_preference(message):
            summary = extract_decision_summary(message)
            log_update('preference', summary)
            updated = True

        # Output
        output = {
            'continue': True,
            'memory_updated': updated
        }

        print(json.dumps(output))

    except Exception as e:
        # Nao bloquear em caso de erro
        print(json.dumps({
            'continue': True,
            'error': str(e)
        }))

if __name__ == '__main__':
    main()
