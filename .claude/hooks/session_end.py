#!/usr/bin/env python3
"""
JARVIS Session End Hook
Executado automaticamente quando uma sessão Claude Code encerra.

Responsabilidades:
1. Salvar estado atual
2. Criar HANDOFF se necessário
3. Registrar métricas da sessão
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Importar Chronicler para handoff narrativo
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'chronicler'))
    from chronicler_core import on_session_end as chronicler_end
    CHRONICLER_AVAILABLE = True
except ImportError:
    CHRONICLER_AVAILABLE = False

def get_project_dir():
    """Obtém o diretório do projeto."""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

def load_jarvis_state():
    """Carrega o estado do JARVIS."""
    project_dir = get_project_dir()
    # Caminho primário: .claude/jarvis/STATE.json (consistente com session_start.py)
    state_path = Path(project_dir) / '.claude' / 'jarvis' / 'STATE.json'
    
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return create_default_state()

def create_default_state():
    """Cria estado padrão se não existir."""
    return {
        'jarvis': {
            'version': '1.0.0',
            'installed_at': datetime.now().isoformat()
        },
        'session': {
            'id': None,
            'started_at': None,
            'last_action_at': None,
            'is_active': False
        },
        'current_state': {
            'phase': 0,
            'phase_name': 'IDLE',
            'status': 'ready',
            'source_code': None,
            'percent_complete': 0
        },
        'next_action': {
            'description': 'Aguardando instruções',
            'priority': 'normal'
        },
        'metrics': {
            'sessions_total': 0,
            'files_processed': 0,
            'insights_extracted': 0
        }
    }

def save_jarvis_state(state):
    """Salva o estado do JARVIS."""
    project_dir = get_project_dir()
    # Caminho primário: .claude/jarvis/STATE.json (consistente com session_start.py)
    state_path = Path(project_dir) / '.claude' / 'jarvis' / 'STATE.json'
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def create_handoff(state, session_info):
    """Cria arquivo HANDOFF para próxima sessão."""
    project_dir = get_project_dir()
    handoff_path = Path(project_dir) / 'logs' / 'handoffs'
    handoff_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    handoff_file = handoff_path / f"HANDOFF-{timestamp}.md"
    
    current = state.get('current_state', {})
    next_action = state.get('next_action', {})
    
    content = f"""# HANDOFF - {datetime.now().strftime('%Y-%m-%d %H:%M')}

> **Gerado por:** JARVIS Session End Hook
> **Session ID:** {session_info.get('session_id', 'unknown')}
> **Motivo:** {session_info.get('reason', 'session_end')}

---

## ESTADO ATUAL

- **Fase:** {current.get('phase_name', 'IDLE')}
- **Status:** {current.get('status', 'unknown')}
- **Progresso:** {current.get('percent_complete', 0)}%
- **Fonte:** {current.get('source_code', 'N/A')}

---

## PRÓXIMA AÇÃO SUGERIDA

**{next_action.get('description', 'Continuar trabalho')}**

Prioridade: {next_action.get('priority', 'normal')}

---

## PARA CONTINUAR

1. Abra uma nova sessão
2. JARVIS carregará este contexto automaticamente
3. Pergunte "onde paramos?" se precisar de mais detalhes

---

*Ready when you are, sir.*
"""
    
    with open(handoff_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(handoff_file)

def update_session_log(session_info):
    """Atualiza log da sessão com dados de encerramento."""
    project_dir = get_project_dir()
    log_path = Path(project_dir) / 'logs' / 'sessions'
    
    # Encontrar log mais recente
    if log_path.exists():
        logs = sorted(log_path.glob('session-*.json'), reverse=True)
        if logs:
            latest_log = logs[0]
            with open(latest_log, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            log_data['ended_at'] = datetime.now().isoformat()
            log_data['reason'] = session_info.get('reason', 'unknown')
            
            with open(latest_log, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

def main():
    """Função principal do hook."""
    try:
        # Ler input do hook (stdin)
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}
        
        # Carregar estado atual
        state = load_jarvis_state()
        
        # Atualizar estado da sessão
        state['session']['is_active'] = False
        state['session']['last_action_at'] = datetime.now().isoformat()
        state['metrics']['sessions_total'] = state.get('metrics', {}).get('sessions_total', 0) + 1
        
        # Salvar estado
        save_jarvis_state(state)
        
        # Criar HANDOFF
        handoff_path = create_handoff(state, hook_input)

        # === CHRONICLER HANDOFF ===
        if CHRONICLER_AVAILABLE:
            try:
                chronicler_end()
            except Exception:
                # Chronicler é opcional, não bloqueia se falhar
                pass

        # Atualizar log da sessão
        update_session_log(hook_input)
        
        # Output (para logs internos, não exibido ao usuário)
        output = {
            'continue': True,
            'feedback': f"[JARVIS] Sessão encerrada. HANDOFF criado: {handoff_path}"
        }
        
        print(json.dumps(output))
        
    except Exception as e:
        # Em caso de erro, não bloquear o encerramento
        error_output = {
            'continue': True,
            'feedback': f"[JARVIS] Hook de encerramento reportou: {str(e)}"
        }
        print(json.dumps(error_output))

if __name__ == '__main__':
    main()
