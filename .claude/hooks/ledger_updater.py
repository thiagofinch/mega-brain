#!/usr/bin/env python3
"""
LEDGER UPDATER HOOK
===================
Atualiza o LEDGER.md automaticamente em pontos chave.

Baseado no Continuous Claude: Context persistence via ledgers

Triggers:
- SessionEnd: Salva estado final
- Após completar tarefa significativa
- Antes de parar

Usage:
    python3 ledger_updater.py [action] [details]

Actions:
- complete_task: Marca tarefa como completada
- add_blocker: Adiciona bloqueio
- set_next_action: Define próxima ação
- update_status: Atualiza status geral
- session_end: Finaliza sessão
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
LEDGER_PATH = PROJECT_ROOT / ".claude" / "LEDGER.md"
MISSION_STATE_PATH = (
    PROJECT_ROOT / ".claude" / "mission-control" / "MISSION-STATE.json"
)
INBOX_PATH = PROJECT_ROOT / "inbox"


def count_inbox_files() -> int:
    """Count files in INBOX"""
    if not INBOX_PATH.exists():
        return 0

    count = 0
    exclude = ["_DUPLICATAS", "_BACKUP", ".DS_Store", "_INDEX"]

    for item in INBOX_PATH.rglob("*"):
        if item.is_file() and not any(e in str(item) for e in exclude):
            if item.suffix.lower() in [".txt", ".md", ".docx", ".pdf"]:
                count += 1
    return count


def get_mission_state() -> dict:
    """Get current mission state"""
    if not MISSION_STATE_PATH.exists():
        return {}
    try:
        with open(MISSION_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def read_ledger() -> str:
    """Read current ledger content"""
    if not LEDGER_PATH.exists():
        return ""
    return LEDGER_PATH.read_text(encoding="utf-8")


def write_ledger(content: str):
    """Write ledger content"""
    LEDGER_PATH.write_text(content, encoding="utf-8")


def update_timestamp(content: str) -> str:
    """Update the timestamp in ledger"""
    now = datetime.now().isoformat()

    # Update timestamp line
    pattern = r"\*\*Timestamp:\*\* .+"
    replacement = f"**Timestamp:** {now}"
    content = re.sub(pattern, replacement, content)

    return content


def update_inbox_status(content: str) -> str:
    """Update INBOX status in ledger"""
    inbox_count = count_inbox_files()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Find and update INBOX table
    # Pattern for "Arquivos pendentes" row
    pattern = r"\| \*\*Arquivos pendentes\*\* \| .+ \|"
    replacement = f"| **Arquivos pendentes** | {inbox_count} |"
    content = re.sub(pattern, replacement, content)

    # Update last scan
    pattern = r"\| \*\*Última varredura\*\* \| .+ \|"
    replacement = f"| **Última varredura** | {now} |"
    content = re.sub(pattern, replacement, content)

    return content


def update_mission_status(content: str) -> str:
    """Update mission status from MISSION-STATE.json"""
    state = get_mission_state()

    if not state:
        return content

    current = state.get("current_state", {})

    # Update mission ID
    mission_id = current.get("mission_id", state.get("mission_id", "-"))
    pattern = r"\| \*\*ID\*\* \| .+ \|"
    replacement = f"| **ID** | {mission_id} |"
    content = re.sub(pattern, replacement, content)

    # Update phase
    phase = current.get("phase", "-")
    phase_name = current.get("phase_name", "")
    pattern = r"\| \*\*Fase\*\* \| .+ \|"
    replacement = f"| **Fase** | {phase} ({phase_name}) |"
    content = re.sub(pattern, replacement, content)

    # Update status
    status = current.get("status", "-")
    pattern = r"\| \*\*Status\*\* \| .+ \|"
    replacement = f"| **Status** | {status} |"
    content = re.sub(pattern, replacement, content)

    # Update batch info if available
    batch_current = current.get("batch_current", "-")
    batch_total = current.get("batch_total", "-")
    percent = current.get("percent_complete", "-")

    pattern = r"\| \*\*Batch atual\*\* \| .+ \|"
    content = re.sub(pattern, f"| **Batch atual** | {batch_current} |", content)

    pattern = r"\| \*\*Batch total\*\* \| .+ \|"
    content = re.sub(pattern, f"| **Batch total** | {batch_total} |", content)

    pattern = r"\| \*\*Progresso\*\* \| .+ \|"
    content = re.sub(pattern, f"| **Progresso** | {percent}% |", content)

    return content


def add_completed_task(content: str, task: str) -> str:
    """Add a completed task to the ledger"""
    now = datetime.now().strftime("%H:%M")
    task_line = f"- [x] [{now}] {task}"

    # Find the completed tasks section and add
    marker = "## ✅ Tarefas Completadas"
    if marker in content:
        # Find the next section
        parts = content.split(marker)
        if len(parts) >= 2:
            # Find where to insert (after the header)
            section = parts[1]
            lines = section.split("\n")

            # Find first empty checkbox or "Nenhuma tarefa"
            insert_idx = None
            for i, line in enumerate(lines):
                if "(Nenhuma tarefa" in line:
                    lines[i] = task_line
                    insert_idx = -1  # Signal we replaced
                    break
                elif line.strip().startswith("- ["):
                    insert_idx = i + 1

            if insert_idx is None:
                # Add after section header
                for i, line in enumerate(lines):
                    if line.strip() == "" and i > 0:
                        lines.insert(i, task_line)
                        break
            elif insert_idx > 0:
                lines.insert(insert_idx, task_line)

            parts[1] = "\n".join(lines)
            content = marker.join(parts)

    return content


def add_blocker(content: str, blocker: str) -> str:
    """Add a blocker to the ledger"""
    now = datetime.now().strftime("%H:%M")
    blocker_line = f"- [{now}] {blocker}"

    marker = "## ⚠️ Bloqueios Encontrados"
    if marker in content:
        # Remove "(Nenhum bloqueio registrado)" if present
        content = content.replace("- (Nenhum bloqueio registrado)", blocker_line)

    return content


def set_next_action(content: str, action: str, priority: str = "Alta") -> str:
    """Set the next action"""
    pattern = r"AÇÃO: .+"
    replacement = f"AÇÃO: {action}"
    content = re.sub(pattern, replacement, content)

    pattern = r"PRIORIDADE: .+"
    replacement = f"PRIORIDADE: {priority}"
    content = re.sub(pattern, replacement, content)

    return content


def add_iteration(content: str, duration: str, tasks: str, status: str) -> str:
    """Add iteration to history"""
    now = datetime.now().strftime("%Y-%m-%d")

    # Find the history table
    marker = "## 📊 Histórico de Iterações"
    if marker in content:
        parts = content.split(marker)
        if len(parts) >= 2:
            # Find last row number
            matches = re.findall(r"\| (\d+) \|", parts[1])
            last_num = int(matches[-1]) if matches else 0
            new_num = last_num + 1

            # Add new row before the closing
            new_row = f"| {new_num} | {now} | {duration} | {tasks} | {status} |"

            # Find where to insert
            lines = parts[1].split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith("---") and i > 5:
                    lines.insert(i, new_row)
                    break

            parts[1] = "\n".join(lines)
            content = marker.join(parts)

    return content


def main():
    try:
        if len(sys.argv) < 2:
            # Default: update all status
            action = "update_status"
        else:
            action = sys.argv[1]

        details = sys.argv[2] if len(sys.argv) > 2 else ""

        # Read current ledger
        content = read_ledger()

        if not content:
            print("Ledger not found - skipping update")
            sys.exit(0)  # Não bloquear se ledger não existe

        # Always update timestamp and status
        content = update_timestamp(content)
        content = update_inbox_status(content)
        content = update_mission_status(content)

        # Handle specific action
        if action == "complete_task" and details:
            content = add_completed_task(content, details)
            print(f"✅ Task marked complete: {details}")

        elif action == "add_blocker" and details:
            content = add_blocker(content, details)
            print(f"⚠️ Blocker added: {details}")

        elif action == "set_next_action" and details:
            content = set_next_action(content, details)
            print(f"🎯 Next action set: {details}")

        elif action == "session_end":
            # Add iteration to history
            content = add_iteration(content, "-", "Session ended", "✅")
            print("📝 Session recorded in ledger")

        # Write updated ledger
        write_ledger(content)

    except Exception as e:
        # NUNCA bloquear operações do Claude Code por erro no ledger
        sys.stderr.write(f"[LEDGER_UPDATER] Erro: {e}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
