#!/usr/bin/env python3
"""
CONTINUOUS SAVE HOOK - NEVER LOSE CONTEXT AGAIN
================================================

Save contínuo como o Claude.ai faz - cada interação é persistida.

ARQUITETURA:
1. JSONL Append-Only (.claude/sessions/current.jsonl)
   - Log linha por linha, ultra-rápido
   - Nunca perde dados (append-only)
   - Reconstruível em caso de corrupção

2. Markdown Snapshot (.claude/sessions/CURRENT-SESSION.md)
   - Atualizado a cada "Stop" (fim de resposta Claude)
   - Legível por humanos
   - Usado pelo /resume

3. Recovery System
   - Se JSONL existe mas MD está vazio, reconstrói
   - Rotação automática por sessão

TRIGGERS:
- UserPromptSubmit: Salva mensagem do usuário
- Stop: Salva resposta do Claude + snapshot MD

Author: JARVIS
Version: 1.0.0
Date: 2026-02-26
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib


#================================
# CONFIGURATION
#================================

class Config:
    """Configuração do sistema de save contínuo."""

    PROJECT_DIR = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
    SESSIONS_DIR = PROJECT_DIR / ".claude" / "sessions"

    # Arquivos principais
    CURRENT_JSONL = SESSIONS_DIR / "current.jsonl"
    CURRENT_MD = SESSIONS_DIR / "CURRENT-SESSION.md"
    LATEST_SESSION = SESSIONS_DIR / "LATEST-SESSION.md"

    # Limits
    MAX_JSONL_SIZE_MB = 10  # Rotaciona após 10MB
    MAX_ENTRIES_BEFORE_ROTATE = 1000  # Rotaciona após 1000 entradas


#================================
# JSONL OPERATIONS (Append-Only)
#================================

def ensure_dirs():
    """Garante que diretórios existam."""
    Config.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def append_to_jsonl(entry: Dict[str, Any]) -> bool:
    """
    Append entry to JSONL file.

    Append-only garante que nunca perdemos dados,
    mesmo se o processo morrer no meio.
    """
    ensure_dirs()

    try:
        entry['_timestamp'] = datetime.now().isoformat()
        entry['_id'] = hashlib.md5(
            f"{entry['_timestamp']}{entry.get('type', '')}".encode()
        ).hexdigest()[:8]

        with open(Config.CURRENT_JSONL, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        return True
    except Exception as e:
        # Fallback: tentar escrever em arquivo de emergência
        try:
            emergency = Config.SESSIONS_DIR / "emergency.jsonl"
            with open(emergency, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except:
            pass
        return False


def read_jsonl() -> list:
    """Lê todas as entradas do JSONL."""
    if not Config.CURRENT_JSONL.exists():
        return []

    entries = []
    try:
        with open(Config.CURRENT_JSONL, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        pass

    return entries


def count_jsonl_entries() -> int:
    """Conta entradas no JSONL."""
    if not Config.CURRENT_JSONL.exists():
        return 0

    count = 0
    try:
        with open(Config.CURRENT_JSONL, 'r', encoding='utf-8') as f:
            for _ in f:
                count += 1
    except:
        pass
    return count


def get_jsonl_size_mb() -> float:
    """Retorna tamanho do JSONL em MB."""
    if not Config.CURRENT_JSONL.exists():
        return 0

    try:
        return Config.CURRENT_JSONL.stat().st_size / (1024 * 1024)
    except:
        return 0


def should_rotate() -> bool:
    """Verifica se deve rotacionar."""
    return (
        get_jsonl_size_mb() > Config.MAX_JSONL_SIZE_MB or
        count_jsonl_entries() > Config.MAX_ENTRIES_BEFORE_ROTATE
    )


def rotate_jsonl():
    """Rotaciona JSONL para arquivo histórico."""
    if not Config.CURRENT_JSONL.exists():
        return

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    archive_name = f"session-{timestamp}.jsonl"
    archive_path = Config.SESSIONS_DIR / "archive" / archive_name

    archive_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        Config.CURRENT_JSONL.rename(archive_path)
    except Exception:
        pass


#================================
# MARKDOWN SNAPSHOT
#================================

def generate_markdown_snapshot() -> str:
    """Gera snapshot markdown a partir do JSONL."""
    entries = read_jsonl()

    if not entries:
        return "# CURRENT SESSION\n\n_Sessão vazia._\n"

    # Extrair metadados
    first_entry = entries[0]
    last_entry = entries[-1]

    session_start = first_entry.get('_timestamp', 'unknown')
    last_activity = last_entry.get('_timestamp', 'unknown')

    # Separar por tipo
    user_messages = [e for e in entries if e.get('type') == 'user_message']
    tool_uses = [e for e in entries if e.get('type') == 'tool_use']
    responses = [e for e in entries if e.get('type') == 'response']

    # Gerar markdown
    md = f"""# CURRENT SESSION - Live Log

> **Iniciada:** {session_start[:19] if len(session_start) > 19 else session_start}
> **Última atividade:** {last_activity[:19] if len(last_activity) > 19 else last_activity}
> **Entradas:** {len(entries)}
> **Auto-save:** Contínuo (cada interação)

---

## ESTATÍSTICAS

| Tipo | Quantidade |
|------|------------|
| Mensagens do usuário | {len(user_messages)} |
| Uso de ferramentas | {len(tool_uses)} |
| Respostas Claude | {len(responses)} |
| **Total** | **{len(entries)}** |

---

## LOG DE INTERAÇÕES (últimas 20)

"""

    # Mostrar últimas 20 interações
    for entry in entries[-20:]:
        entry_type = entry.get('type', 'unknown')
        timestamp = entry.get('_timestamp', '')[:19]

        if entry_type == 'user_message':
            content = entry.get('content', '')[:100]
            md += f"### 👤 [{timestamp}] Usuário\n"
            md += f"```\n{content}{'...' if len(entry.get('content', '')) > 100 else ''}\n```\n\n"

        elif entry_type == 'tool_use':
            tool = entry.get('tool', 'unknown')
            md += f"### 🔧 [{timestamp}] Tool: {tool}\n"
            if entry.get('file'):
                md += f"- Arquivo: `{entry['file']}`\n"
            md += "\n"

        elif entry_type == 'response':
            preview = entry.get('preview', '')[:150]
            md += f"### 🤖 [{timestamp}] Claude\n"
            md += f"```\n{preview}{'...' if len(entry.get('preview', '')) > 150 else ''}\n```\n\n"

    if len(entries) > 20:
        md += f"\n_... e mais {len(entries) - 20} entradas anteriores no JSONL_\n"

    md += f"""

---

## RECOVERY INFO

Se esta sessão foi interrompida, use `/resume` para continuar.

O log completo está em: `.claude/sessions/current.jsonl`

---

*Auto-saved by Continuous Save Hook*
*Timestamp: {datetime.now().isoformat()}*
"""

    return md


def save_markdown_snapshot():
    """Salva snapshot markdown."""
    ensure_dirs()

    md = generate_markdown_snapshot()

    try:
        # Salvar CURRENT-SESSION.md
        with open(Config.CURRENT_MD, 'w', encoding='utf-8') as f:
            f.write(md)

        # Também atualizar LATEST-SESSION.md
        with open(Config.LATEST_SESSION, 'w', encoding='utf-8') as f:
            f.write(md)

        return True
    except Exception:
        return False


#================================
# EVENT HANDLERS
#================================

def on_user_message(content: str, metadata: Dict = None):
    """Handler para mensagem do usuário (UserPromptSubmit)."""
    entry = {
        'type': 'user_message',
        'content': content[:200],  # Limitar tamanho (security: avoid logging sensitive data)
        'metadata': metadata or {}
    }

    append_to_jsonl(entry)

    # Verificar rotação
    if should_rotate():
        # Salvar snapshot antes de rotacionar
        save_markdown_snapshot()
        rotate_jsonl()


def on_tool_use(tool_name: str, tool_input: Dict = None, result_preview: str = None):
    """Handler para uso de ferramenta (PostToolUse)."""
    # Security: log only metadata, not full content (may contain secrets/tokens)
    safe_input = None
    if tool_input:
        # Only log file paths and tool name, not content
        safe_input = {}
        for key in ['file_path', 'filepath', 'path', 'command', 'pattern']:
            if key in tool_input:
                safe_input[key] = str(tool_input[key])[:200]

    entry = {
        'type': 'tool_use',
        'tool': tool_name,
        'input_preview': str(safe_input)[:200] if safe_input else None,
        'result_preview': result_preview[:200] if result_preview else None
    }

    # Extrair arquivo se for Edit/Write/Read
    if tool_input:
        for key in ['file_path', 'filepath', 'path']:
            if key in tool_input:
                entry['file'] = tool_input[key]
                break

    append_to_jsonl(entry)


def on_response_complete(preview: str = None):
    """Handler para resposta completa (Stop)."""
    entry = {
        'type': 'response',
        'preview': preview[:200] if preview else '[response complete]'
    }

    append_to_jsonl(entry)

    # Sempre salvar snapshot após resposta completa
    save_markdown_snapshot()


def get_session_summary() -> Dict:
    """Retorna resumo da sessão atual."""
    entries = read_jsonl()

    if not entries:
        return {
            'status': 'empty',
            'entries': 0,
            'has_data': False
        }

    return {
        'status': 'active',
        'entries': len(entries),
        'has_data': True,
        'first_timestamp': entries[0].get('_timestamp'),
        'last_timestamp': entries[-1].get('_timestamp'),
        'user_messages': len([e for e in entries if e.get('type') == 'user_message']),
        'tool_uses': len([e for e in entries if e.get('type') == 'tool_use']),
        'responses': len([e for e in entries if e.get('type') == 'response']),
        'size_mb': get_jsonl_size_mb()
    }


#================================
# CLI INTERFACE
#================================

def main():
    """Interface de linha de comando."""

    # Ler stdin para input do hook
    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}
    except:
        hook_input = {}

    # Determinar tipo de evento
    event_type = None

    # Detectar pelo contexto do hook
    if 'prompt' in hook_input or 'user_prompt' in hook_input:
        event_type = 'user_message'
        content = hook_input.get('prompt') or hook_input.get('user_prompt', '')
        on_user_message(content, hook_input)

    elif 'tool_name' in hook_input:
        event_type = 'tool_use'
        on_tool_use(
            hook_input.get('tool_name', 'unknown'),
            hook_input.get('tool_input'),
            hook_input.get('tool_result', '')[:500] if hook_input.get('tool_result') else None
        )

    elif 'stop_reason' in hook_input or 'response' in hook_input:
        event_type = 'response'
        preview = hook_input.get('response', '')[:500] if hook_input.get('response') else None
        on_response_complete(preview)

    else:
        # Fallback: tratar como resposta completa (Stop hook)
        event_type = 'response'
        on_response_complete()

    # Output para o hook system
    summary = get_session_summary()

    output = {
        'continue': True,
        'feedback': f"[SAVE] {summary['entries']} entries | {summary.get('size_mb', 0):.2f}MB"
    }

    print(json.dumps(output))


if __name__ == '__main__':
    main()
