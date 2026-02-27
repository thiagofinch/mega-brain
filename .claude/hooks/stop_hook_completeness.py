#!/usr/bin/env python3
"""
STOP HOOK - TASK COMPLETENESS CHECKER
=====================================
Intercepta quando Claude quer parar e verifica se a tarefa realmente completou.

Baseado no workflow Boris Cherny: Stop hooks para tarefas longas

Verifica:
1. Se havia uma tarefa em andamento (LEDGER.md)
2. Se a tarefa foi completada
3. Se há arquivos pendentes no INBOX
4. Se há batches incompletos

Output:
- Se completo: exit 0 (permite parar)
- Se incompleto: print mensagem sugerindo continuar
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Fix Windows cp1252 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
MISSION_CONTROL = PROJECT_ROOT / '.claude' / 'mission-control'
LEDGER_PATH = PROJECT_ROOT / '.claude' / 'LEDGER.md'
INBOX_PATH = PROJECT_ROOT / 'inbox'
LOGS_PATH = PROJECT_ROOT / 'logs' / 'stop_hooks'
LOGS_PATH.mkdir(parents=True, exist_ok=True)

def count_inbox_files() -> int:
    """Count processable files in INBOX"""
    if not INBOX_PATH.exists():
        return 0

    count = 0
    exclude_patterns = ['_DUPLICATAS', '_BACKUP', '.DS_Store', '_INDEX']

    for item in INBOX_PATH.rglob('*'):
        if item.is_file():
            # Skip excluded patterns
            if any(excl in str(item) for excl in exclude_patterns):
                continue
            # Count txt, md, docx files
            if item.suffix.lower() in ['.txt', '.md', '.docx', '.pdf']:
                count += 1

    return count

def check_pending_batches() -> tuple[int, int]:
    """Check if there are pending batches based on MISSION-STATE"""
    state_file = MISSION_CONTROL / 'MISSION-STATE.json'

    if not state_file.exists():
        return 0, 0

    try:
        with open(state_file, 'r') as f:
            state = json.load(f)

        current = state.get('current_state', {})
        batch_current = current.get('batch_current', 0)
        batch_total = current.get('batch_total', 0)

        return batch_current, batch_total
    except Exception:
        return 0, 0

def read_ledger() -> dict:
    """Read current ledger state"""
    if not LEDGER_PATH.exists():
        return {}

    try:
        content = LEDGER_PATH.read_text()

        # Parse simple ledger format
        ledger = {
            'has_pending_task': '⏳' in content or 'PENDING' in content.upper(),
            'last_task': '',
            'next_action': ''
        }

        # Extract next action
        if 'Próxima Ação:' in content or 'Next Action:' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'Próxima Ação' in line or 'Next Action' in line:
                    if i + 1 < len(lines):
                        ledger['next_action'] = lines[i + 1].strip('- ')

        return ledger
    except Exception:
        return {}

def log_stop_check(reason: str, should_continue: bool, details: dict):
    """Log stop check"""
    log_file = LOGS_PATH / 'stop_checks.jsonl'
    entry = {
        'timestamp': datetime.now().isoformat(),
        'reason': reason,
        'should_continue': should_continue,
        'details': details
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def check_completeness():
    """Core completeness check logic. Returns list of issues."""
    issues = []
    details = {}

    # Check 1: INBOX files
    inbox_count = count_inbox_files()
    details['inbox_files'] = inbox_count
    if inbox_count > 10:
        issues.append(f"INBOX has {inbox_count} files waiting to be processed")

    # Check 2: Pending batches
    batch_current, batch_total = check_pending_batches()
    details['batch_current'] = batch_current
    details['batch_total'] = batch_total
    if batch_total > 0 and batch_current < batch_total:
        remaining = batch_total - batch_current
        issues.append(f"Batch processing incomplete: {batch_current}/{batch_total} ({remaining} remaining)")

    # Check 3: Ledger pending tasks
    ledger = read_ledger()
    details['ledger'] = ledger
    if ledger.get('has_pending_task'):
        next_action = ledger.get('next_action', 'Unknown')
        issues.append(f"Ledger shows pending task: {next_action}")

    # Log the check
    log_stop_check('stop_hook_check', len(issues) > 0, details)

    return issues


def main():
    """
    Hook entry point for Claude Code Stop event.
    Reads JSON from stdin, outputs JSON to stdout.
    Must output valid JSON per Anthropic hook standards.
    """
    try:
        issues = check_completeness()

        if issues:
            feedback = "Tasks may be incomplete: " + "; ".join(issues)
            result = {"continue": True, "feedback": feedback}
        else:
            result = {"continue": True, "feedback": "All clear, no pending tasks detected."}

        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        # Even on error, output valid JSON
        result = {"continue": True, "feedback": f"Stop hook check error: {e}"}
        print(json.dumps(result))
        sys.exit(0)


def cli_test():
    """CLI test mode - run directly for debugging."""
    issues = check_completeness()
    if issues:
        print("STOP HOOK: Tasks may be incomplete")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("STOP HOOK: All clear, no pending tasks detected.")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        cli_test()
    else:
        main()
