#!/usr/bin/env python3
"""
NOTIFICATION SYSTEM
===================
Envia notificações do sistema quando Claude precisa de input ou completa tarefas.

Baseado no workflow Boris Cherny: "I use system notifications to know when a Claude needs input"

Platforms:
- macOS: osascript (native notifications)
- Terminal: bell + print

Usage:
    python3 notification_system.py "Title" "Message" [type]

Types:
- info: Informational (default)
- success: Task completed
- warning: Needs attention
- error: Something failed
"""

import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Fix Windows cp1252 encoding — emojis crash without this
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
LOGS_PATH = PROJECT_ROOT / 'logs' / 'notifications'
LOGS_PATH.mkdir(parents=True, exist_ok=True)

def send_macos_notification(title: str, message: str, sound: str = "default"):
    """Send native macOS notification"""
    script = f'''
    display notification "{message}" with title "{title}" sound name "{sound}"
    '''
    try:
        subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        return True
    except Exception:
        return False

def send_terminal_bell():
    """Send terminal bell character"""
    print('\a', end='', flush=True)

def log_notification(title: str, message: str, notif_type: str):
    """Log notification"""
    log_file = LOGS_PATH / 'notifications.jsonl'
    import json
    entry = {
        'timestamp': datetime.now().isoformat(),
        'title': title,
        'message': message,
        'type': notif_type
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def get_sound_for_type(notif_type: str) -> str:
    """Get appropriate sound for notification type"""
    sounds = {
        'info': 'Pop',
        'success': 'Glass',
        'warning': 'Basso',
        'error': 'Sosumi'
    }
    return sounds.get(notif_type, 'default')

def main():
    import json as json_module

    if len(sys.argv) < 3:
        print(json_module.dumps({"continue": True, "feedback": "notification_system: missing args"}))
        sys.exit(0)

    title = sys.argv[1]
    message = sys.argv[2]
    notif_type = sys.argv[3] if len(sys.argv) > 3 else 'info'

    log_notification(title, message, notif_type)

    sound = get_sound_for_type(notif_type)
    send_macos_notification(title, message, sound)
    send_terminal_bell()

    # Output valid JSON for Claude Code hooks
    print(json_module.dumps({"continue": True, "feedback": f"[{title}] {message}"}))
    sys.exit(0)

# Convenience functions for direct import
def notify_needs_input(context: str = ""):
    """Notify that Claude needs user input"""
    msg = f"Claude needs your input{': ' + context if context else ''}"
    send_macos_notification("🤖 JARVIS", msg, "Basso")
    send_terminal_bell()

def notify_task_complete(task: str = ""):
    """Notify that a task completed"""
    msg = f"Task completed{': ' + task if task else ''}"
    send_macos_notification("✅ JARVIS", msg, "Glass")

def notify_error(error: str = ""):
    """Notify about an error"""
    msg = f"Error{': ' + error if error else ''}"
    send_macos_notification("❌ JARVIS", msg, "Sosumi")

if __name__ == '__main__':
    main()
