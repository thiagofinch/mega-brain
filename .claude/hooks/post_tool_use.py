#!/usr/bin/env python3
"""
JARVIS Post Tool Use Hook
Executado após Claude Code usar uma ferramenta de edição/escrita.

Responsabilidades:
1. Registrar arquivos modificados
2. Detectar padrões
3. Sugerir melhorias quando apropriado
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

def get_project_dir():
    """Obtém o diretório do projeto."""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

def load_actions_log():
    """Carrega log de ações."""
    project_dir = get_project_dir()
    log_path = Path(project_dir) / 'logs' / 'actions.json'
    
    if log_path.exists():
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'actions': []}

def save_actions_log(log):
    """Salva log de ações."""
    project_dir = get_project_dir()
    log_path = Path(project_dir) / 'logs' / 'actions.json'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Manter apenas últimas 100 ações
    log['actions'] = log['actions'][-100:]
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

def detect_patterns(actions):
    """Detecta padrões nas ações recentes."""
    if len(actions) < 3:
        return None
    
    # Verificar se mesmo arquivo foi editado múltiplas vezes
    recent = actions[-10:]
    file_counts = {}
    for action in recent:
        file_path = action.get('file_path', '')
        if file_path:
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
    
    # Se algum arquivo foi editado 3+ vezes
    repeated = [f for f, c in file_counts.items() if c >= 3]
    if repeated:
        return {
            'type': 'repeated_edits',
            'files': repeated,
            'suggestion': 'Arquivo editado múltiplas vezes. Considerar refatoração.'
        }
    
    return None

def main():
    """Função principal do hook."""
    try:
        # Ler input do hook (stdin)
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}
        
        # Extrair informações da ferramenta
        tool_name = hook_input.get('tool_name', 'unknown')
        tool_input = hook_input.get('tool_input', {})
        
        file_path = tool_input.get('file_path', '')
        
        # Carregar log
        log = load_actions_log()
        
        # Registrar ação
        action = {
            'timestamp': datetime.now().isoformat(),
            'tool': tool_name,
            'file_path': file_path,
            'session_id': hook_input.get('session_id', 'unknown')
        }
        log['actions'].append(action)
        
        # Salvar log
        save_actions_log(log)
        
        # Detectar padrões
        pattern = detect_patterns(log['actions'])
        
        # Preparar feedback
        feedback = None
        if pattern:
            feedback = f"[JARVIS] Padrão detectado: {pattern['suggestion']}"
        
        output = {
            'continue': True,
            'feedback': feedback
        }
        
        print(json.dumps(output))
        
    except Exception as e:
        # Em caso de erro, não bloquear a operação
        error_output = {
            'continue': True,
            'feedback': None
        }
        print(json.dumps(error_output))

if __name__ == '__main__':
    main()
