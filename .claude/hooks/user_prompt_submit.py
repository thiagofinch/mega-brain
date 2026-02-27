#!/usr/bin/env python3
"""
JARVIS User Prompt Submit Hook
Executado quando o usuário envia uma mensagem.

Responsabilidades:
1. Registrar prompts para análise
2. Detectar intenções especiais
3. Injetar contexto básico (status, greeting)

NOTE: Skill routing (REGRA #27) e quality watchdog são hooks separados
registrados em settings.json. Este hook foca apenas em intents básicos.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path


def get_project_dir():
    """Obtém o diretório do projeto."""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())


def detect_special_intents(prompt):
    """Detecta intenções especiais no prompt."""
    prompt_lower = prompt.lower()

    intents = []

    if any(word in prompt_lower for word in ['status', 'onde estamos', 'onde paramos']):
        intents.append('status_request')

    if any(word in prompt_lower for word in ['ajuda', 'help', 'como fazer']):
        intents.append('help_request')

    if any(word in prompt_lower for word in ['bom dia', 'boa tarde', 'boa noite', 'olá', 'oi']):
        intents.append('greeting')

    if any(word in prompt_lower for word in ['crie', 'criar', 'faça', 'fazer', 'gerar']):
        intents.append('creation_request')

    if any(word in prompt_lower for word in ['analise', 'verifique', 'cheque', 'revise']):
        intents.append('analysis_request')

    if any(phrase in prompt_lower for phrase in ['war room', 'debate sobre', 'múltiplas perspectivas', 'prós e contras']):
        intents.append('war_room_request')

    if any(phrase in prompt_lower for phrase in ['use os agentes', 'consulte especialistas', 'análise profunda']):
        intents.append('force_agents')

    return intents


def load_context_for_intents(intents):
    """Carrega contexto relevante baseado nas intenções."""
    project_dir = get_project_dir()
    context_parts = []

    if 'status_request' in intents:
        state_path = Path(project_dir) / '.claude' / 'jarvis' / 'STATE.json'
        if state_path.exists():
            try:
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    phase = state.get('current_state', {}).get('phase_name', 'IDLE')
                    pct = state.get('current_state', {}).get('percent_complete', 0)
                    context_parts.append(
                        f"[JARVIS Context] Estado: Fase {phase} | Progresso: {pct}%"
                    )
            except Exception:
                pass

    return context_parts


def main():
    """Hook entry point - reads JSON from stdin, outputs JSON to stdout."""
    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}

        prompt = hook_input.get('prompt', '')
        session_id = hook_input.get('session_id', 'unknown')

        # Detectar intenções
        intents = detect_special_intents(prompt)

        # Carregar contexto básico
        context_parts = load_context_for_intents(intents)

        # Registrar prompt para análise posterior
        project_dir = get_project_dir()
        prompts_path = Path(project_dir) / 'logs' / 'prompts.jsonl'
        prompts_path.parent.mkdir(parents=True, exist_ok=True)

        prompt_log = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'prompt_length': len(prompt),
            'intents': intents
        }

        try:
            with open(prompts_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(prompt_log) + '\n')
        except Exception:
            pass

        # Output
        output = {
            'continue': True,
            'feedback': '\n'.join(context_parts) if context_parts else None
        }

        print(json.dumps(output))

    except Exception:
        print(json.dumps({'continue': True, 'feedback': None}))


if __name__ == '__main__':
    main()
