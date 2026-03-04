#!/usr/bin/env python3
"""
JARVIS Pending Tracker Hook
Atualiza PENDING.md automaticamente.

Triggers:
- TodoWrite tool usado
- Perguntas feitas ao usuario
- Tarefas incompletas detectadas
- Final de sessao
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

def load_pending():
    """Carrega PENDING.md atual."""
    project_dir = get_project_dir()
    pending_path = Path(project_dir) / '.claude' / 'jarvis' / 'PENDING.md'

    if pending_path.exists():
        with open(pending_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def update_pending_file(priority, item, action='add'):
    """Atualiza PENDING.md com novo item ou remove existente."""
    project_dir = get_project_dir()
    pending_path = Path(project_dir) / '.claude' / 'jarvis' / 'PENDING.md'

    if not pending_path.exists():
        return False

    with open(pending_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Mapear prioridade para secao
    section_map = {
        'high': '## Alta Prioridade',
        'medium': '## Media Prioridade',
        'low': '## Baixa Prioridade',
        'waiting': '## Aguardando Resposta do Usuario'
    }

    section_header = section_map.get(priority, '## Media Prioridade')

    if action == 'add':
        # Encontrar secao e adicionar item
        if section_header in content:
            parts = content.split(section_header)
            if len(parts) >= 2:
                # Encontrar fim da secao (proximo ##)
                section_content = parts[1]
                next_section = section_content.find('\n## ')

                if next_section == -1:
                    next_section = section_content.find('\n---')

                if next_section > 0:
                    before = section_content[:next_section]
                    after = section_content[next_section:]

                    # Remover "Nenhum item" se existir
                    before = before.replace('*Nenhum item de alta prioridade.*', '')
                    before = before.replace('*Nenhum item de media prioridade.*', '')
                    before = before.replace('*Nenhum item de baixa prioridade.*', '')
                    before = before.replace('*Nenhuma pergunta pendente.*', '')

                    # Adicionar novo item
                    new_item = f"\n- [ ] {item}"
                    before = before.rstrip() + new_item + '\n'

                    parts[1] = before + after
                    content = section_header.join(parts)

    elif action == 'complete':
        # Marcar item como completo (mudar [ ] para [x])
        content = content.replace(f'- [ ] {item}', f'- [x] {item}')

    elif action == 'remove':
        # Remover item completamente
        content = re.sub(rf'- \[.\] {re.escape(item)}\n?', '', content)

    # Atualizar timestamp
    content = re.sub(
        r'\*Ultima atualizacao: \d{4}-\d{2}-\d{2}\*',
        f'*Ultima atualizacao: {datetime.now().strftime("%Y-%m-%d")}*',
        content
    )

    # Recalcular estatisticas
    high_count = len(re.findall(r'## Alta Prioridade.*?(?=##)', content, re.DOTALL)[0].split('- [ ]')) - 1 if '## Alta Prioridade' in content else 0
    medium_count = len(re.findall(r'## Media Prioridade.*?(?=##)', content, re.DOTALL)[0].split('- [ ]')) - 1 if '## Media Prioridade' in content else 0
    low_count = len(re.findall(r'## Baixa Prioridade.*?(?=##)', content, re.DOTALL)[0].split('- [ ]')) - 1 if '## Baixa Prioridade' in content else 0
    waiting_count = len(re.findall(r'## Aguardando.*?(?=##)', content, re.DOTALL)[0].split('- ')) - 1 if '## Aguardando' in content else 0

    # Corrigir contagens negativas
    high_count = max(0, high_count)
    medium_count = max(0, medium_count)
    low_count = max(0, low_count)
    waiting_count = max(0, waiting_count)
    total = high_count + medium_count + low_count + waiting_count

    # Atualizar tabela de estatisticas
    content = re.sub(r'\| Alta Prioridade \| \d+ \|', f'| Alta Prioridade | {high_count} |', content)
    content = re.sub(r'\| Media Prioridade \| \d+ \|', f'| Media Prioridade | {medium_count} |', content)
    content = re.sub(r'\| Baixa Prioridade \| \d+ \|', f'| Baixa Prioridade | {low_count} |', content)
    content = re.sub(r'\| Aguardando Usuario \| \d+ \|', f'| Aguardando Usuario | {waiting_count} |', content)
    content = re.sub(r'\| \*\*TOTAL PENDENTE\*\* \| \*\*\d+\*\* \|', f'| **TOTAL PENDENTE** | **{total}** |', content)

    with open(pending_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def sync_from_todos(todos):
    """Sincroniza pendencias do TodoWrite com PENDING.md."""
    for todo in todos:
        if todo.get('status') == 'pending':
            content = todo.get('content', '')
            if content:
                update_pending_file('medium', content, 'add')
        elif todo.get('status') == 'completed':
            content = todo.get('content', '')
            if content:
                update_pending_file('medium', content, 'complete')

def log_update(action, item):
    """Loga a atualizacao de pendencias."""
    project_dir = get_project_dir()
    log_path = Path(project_dir) / 'logs' / 'pending_updates.jsonl'

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'item': item[:200]
    }

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

def main():
    """Funcao principal do hook."""
    try:
        # Ler input do hook
        input_data = sys.stdin.read()
        if not input_data:
            print(json.dumps({'continue': True}))
            return

        hook_input = json.loads(input_data)

        # Verificar se ha todos para sincronizar
        todos = hook_input.get('todos', [])
        if todos:
            sync_from_todos(todos)
            log_update('sync', f'{len(todos)} todos sincronizados')

        # Verificar se ha pergunta pendente
        question = hook_input.get('question', '')
        if question:
            update_pending_file('waiting', question, 'add')
            log_update('add_question', question)

        # Output
        output = {
            'continue': True
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
