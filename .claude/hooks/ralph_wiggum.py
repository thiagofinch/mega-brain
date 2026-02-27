#!/usr/bin/env python3
"""
RALPH WIGGUM - COMPLETION PROMISE HOOK
======================================
Baseado no plugin original de Boris Cherny.

O "completion promise" é um pattern onde Claude deve outputtar uma string
específica para sinalizar que a tarefa está REALMENTE completa.

Funcionamento:
1. Claude recebe instrução para usar <promise>DONE</promise> quando terminar
2. Este hook verifica se o completion promise foi dado
3. Se não foi, re-prompta Claude para continuar ou confirmar

Token: <promise>DONE</promise>

Referência: https://github.com/chernyshov/ralph-wiggum
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime

# Fix Windows cp1252 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
STATE_FILE = PROJECT_ROOT / '.claude' / 'ralph_wiggum_state.json'
LOG_FILE = PROJECT_ROOT / 'logs' / 'ralph_wiggum.jsonl'

# Completion promise token
PROMISE_TOKEN = '<promise>DONE</promise>'
PROMISE_PATTERN = re.compile(r'<promise>DONE</promise>', re.IGNORECASE)

# Tasks that require completion promise
COMPLEX_TASK_KEYWORDS = [
    'processar', 'pipeline', 'batch', 'criar agente',
    'implementar', 'refatorar', 'migrar', 'varredura',
    'fase 4', 'fase 5', 'dossier', 'playbook'
]


def ensure_dirs():
    """Ensure log directory exists"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    """Load Ralph Wiggum state"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {
        'active_task': None,
        'promise_required': False,
        'promise_received': False,
        'reprompt_count': 0,
        'max_reprompts': 3
    }


def save_state(state: dict):
    """Save Ralph Wiggum state"""
    ensure_dirs()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def log_event(event_type: str, details: dict):
    """Log Ralph Wiggum events"""
    ensure_dirs()
    entry = {
        'timestamp': datetime.now().isoformat(),
        'event': event_type,
        **details
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def is_complex_task(task_description: str) -> bool:
    """Determine if task requires completion promise"""
    if not task_description:
        return False
    task_lower = task_description.lower()
    return any(keyword in task_lower for keyword in COMPLEX_TASK_KEYWORDS)


def check_promise_in_output() -> bool:
    """Check if completion promise was given in recent output"""
    # Check LEDGER for promise
    ledger_path = PROJECT_ROOT / '.claude' / 'LEDGER.md'
    if ledger_path.exists():
        content = ledger_path.read_text()
        if PROMISE_PATTERN.search(content):
            return True

    # Check recent session log
    sessions_dir = PROJECT_ROOT / '.claude' / 'sessions'
    if sessions_dir.exists():
        session_files = sorted(sessions_dir.glob('SESSION-*.md'), reverse=True)
        if session_files:
            recent = session_files[0].read_text()
            if PROMISE_PATTERN.search(recent):
                return True

    return False


def start_task(task_description: str):
    """Call when a complex task starts"""
    state = load_state()

    if is_complex_task(task_description):
        state['active_task'] = task_description
        state['promise_required'] = True
        state['promise_received'] = False
        state['reprompt_count'] = 0
        save_state(state)
        log_event('task_started', {'task': task_description, 'promise_required': True})

        # Inject instruction about completion promise
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🎯 RALPH WIGGUM ACTIVE                                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Tarefa complexa detectada: {task_description[:50]:<50} ║
║                                                                              ║
║  Quando COMPLETAR a tarefa, inclua na sua resposta:                          ║
║                                                                              ║
║      <promise>DONE</promise>                                                 ║
║                                                                              ║
║  Isso confirma que a tarefa está REALMENTE completa.                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


def check_completion() -> bool:
    """Check if task is complete (has promise)"""
    state = load_state()

    if not state.get('promise_required'):
        return True

    if state.get('promise_received'):
        return True

    # Check if promise was given
    if check_promise_in_output():
        state['promise_received'] = True
        save_state(state)
        log_event('promise_received', {'task': state.get('active_task')})
        return True

    return False


def reprompt():
    """Generate reprompt message if task incomplete"""
    state = load_state()

    if state.get('reprompt_count', 0) >= state.get('max_reprompts', 3):
        # Max reprompts reached, allow exit
        log_event('max_reprompts_reached', {'task': state.get('active_task')})
        clear_task()
        return None

    state['reprompt_count'] = state.get('reprompt_count', 0) + 1
    save_state(state)

    task = state.get('active_task', 'current task')
    count = state['reprompt_count']
    max_count = state.get('max_reprompts', 3)

    log_event('reprompt_generated', {'task': task, 'count': count})

    return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️  RALPH WIGGUM: Completion promise not detected ({count}/{max_count})      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Task: {task[:66]:<66} ║
║                                                                              ║
║  Você ainda não confirmou que a tarefa está completa.                        ║
║                                                                              ║
║  Se a tarefa está COMPLETA, responda com:                                    ║
║      <promise>DONE</promise>                                                 ║
║                                                                              ║
║  Se há mais trabalho, continue de onde parou.                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


def clear_task():
    """Clear the current task"""
    state = load_state()
    if state.get('active_task'):
        log_event('task_cleared', {'task': state.get('active_task')})
    state['active_task'] = None
    state['promise_required'] = False
    state['promise_received'] = False
    state['reprompt_count'] = 0
    save_state(state)


def main():
    """Main Ralph Wiggum logic for Stop hook. Must output valid JSON."""
    ensure_dirs()
    state = load_state()

    # If no task active, allow exit
    if not state.get('active_task'):
        print(json.dumps({"continue": True, "feedback": ""}))
        sys.exit(0)

    # If promise not required, allow exit
    if not state.get('promise_required'):
        print(json.dumps({"continue": True, "feedback": ""}))
        sys.exit(0)

    # Check if promise was given
    if check_completion():
        clear_task()
        print(json.dumps({"continue": True, "feedback": "Ralph Wiggum: Completion promise received. Task complete."}))
        sys.exit(0)

    # Generate reprompt
    reprompt_msg = reprompt()

    if reprompt_msg:
        # Task incomplete, but still output valid JSON
        feedback = f"Ralph Wiggum: Task incomplete. Reprompt count: {state.get('reprompt_count', 0)}"
        print(json.dumps({"continue": True, "feedback": feedback}))
    else:
        # Max reprompts reached
        print(json.dumps({"continue": True, "feedback": "Ralph Wiggum: Max reprompts reached. Allowing exit."}))

    sys.exit(0)


# CLI interface for manual control
if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'start' and len(sys.argv) > 2:
            task = ' '.join(sys.argv[2:])
            start_task(task)

        elif cmd == 'check':
            if check_completion():
                print("✅ Task complete (promise received)")
            else:
                print("⏳ Task incomplete (no promise)")

        elif cmd == 'clear':
            clear_task()
            print("🗑️ Task cleared")

        elif cmd == 'status':
            state = load_state()
            print(json.dumps(state, indent=2))

        else:
            print("""
Ralph Wiggum - Completion Promise Hook

Usage:
    ralph_wiggum.py              # Stop hook mode
    ralph_wiggum.py start TASK   # Start tracking complex task
    ralph_wiggum.py check        # Check if promise received
    ralph_wiggum.py clear        # Clear current task
    ralph_wiggum.py status       # Show current state
""")
    else:
        main()
