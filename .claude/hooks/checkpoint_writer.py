#!/usr/bin/env python3
"""
JARVIS Checkpoint Writer v1.0
Salva estado completo antes de compactação de contexto.

Arquivos gerados:
- CURRENT-TASK.md (tarefa atual destacada)
- CONTEXT-SNAPSHOT.md (resumo do contexto atual)
- INSIGHTS-SESSION.md (insights da sessão)
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

def get_project_dir():
    """Obtém o diretório do projeto."""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

def load_checkpoint_trigger():
    """Carrega dados do trigger de checkpoint."""
    project_dir = get_project_dir()
    trigger_path = Path(project_dir) / '.claude' / 'mission-control' / 'CHECKPOINT-TRIGGER.json'

    if trigger_path.exists():
        with open(trigger_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_jarvis_state():
    """Carrega estado do JARVIS."""
    project_dir = get_project_dir()

    # Tentar .claude/jarvis/ primeiro
    state_path = Path(project_dir) / '.claude' / 'jarvis' / 'STATE.json'
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # Fallback
    state_path = Path(project_dir) / 'system' / 'JARVIS-STATE.json'
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    return None

def load_pending():
    """Carrega pendências atuais."""
    project_dir = get_project_dir()
    pending_path = Path(project_dir) / '.claude' / 'jarvis' / 'PENDING.md'

    if pending_path.exists():
        with open(pending_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def update_current_task(trigger_data, state):
    """Atualiza CURRENT-TASK.md com estado atual."""
    project_dir = get_project_dir()
    task_path = Path(project_dir) / '.claude' / 'jarvis' / 'CURRENT-TASK.md'

    # Construir conteúdo
    objective = "Continuar tarefa da sessão anterior"
    context = "Checkpoint automático disparado por uso de contexto."

    if state:
        if 'next_action' in state:
            objective = state['next_action'].get('description', objective)
        if 'mission' in state:
            mission = state['mission']
            context = f"Missão: Fase {mission.get('phase', '?')} | Batch {mission.get('batch', '?')}"

    content = f"""# CURRENT-TASK.md

> Tarefa atual em andamento. Atualizado automaticamente via checkpoint.
> Lido no início de cada sessão para continuidade.

---

## Objetivo

{objective}

## Contexto

{context}

## Checkpoint Info

- Razão: {trigger_data.get('reason', 'MANUAL')}
- Tokens estimados: {trigger_data.get('tokens_estimated', 'N/A')}
- Uso de contexto: {trigger_data.get('usage_percent', 'N/A')}%
- Mensagens na sessão: {trigger_data.get('messages_count', 'N/A')}

## Próximos Passos

1. Verificar PENDING.md para tarefas pendentes
2. Consultar JARVIS-MEMORY.md para contexto relacional
3. Retomar de onde parou

## Insights da Sessão

*Adicione insights importantes aqui durante a sessão*

---

*Atualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Checkpoint automático JARVIS Memory System v2.0*
"""

    with open(task_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return task_path

def create_context_snapshot(trigger_data, state):
    """Cria snapshot do contexto atual."""
    project_dir = get_project_dir()
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    snapshot_path = Path(project_dir) / '.claude' / 'jarvis' / 'snapshots' / f'CONTEXT-{timestamp}.md'
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    # Estado da missão
    mission_info = "Não disponível"
    if state and 'mission' in state:
        m = state['mission']
        mission_info = f"Fase {m.get('phase', '?')} | Batch {m.get('batch', '?')}/{m.get('total_batches', '?')} | {m.get('status', 'UNKNOWN')}"

    # Progresso acumulado
    progress_info = "Não disponível"
    if state and 'accumulated' in state:
        a = state['accumulated']
        progress_info = f"{a.get('progress_percent', 0)}% | {a.get('files', 0)} arquivos | {a.get('insights', 0)} insights"

    content = f"""# CONTEXT SNAPSHOT

> Snapshot automático do contexto da sessão.
> Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Trigger

| Campo | Valor |
|-------|-------|
| Razão | {trigger_data.get('reason', 'N/A')} |
| Tokens | {trigger_data.get('tokens_estimated', 'N/A')} |
| Uso % | {trigger_data.get('usage_percent', 'N/A')}% |
| Mensagens | {trigger_data.get('messages_count', 'N/A')} |

## Estado da Missão

{mission_info}

## Progresso Acumulado

{progress_info}

## Arquivos de Memória

| Arquivo | Status |
|---------|--------|
| JARVIS-MEMORY.md | Verificar |
| PENDING.md | Verificar |
| STATE.json | {'Carregado' if state else 'Não encontrado'} |

---

*Snapshot JARVIS Memory System v2.0*
"""

    with open(snapshot_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Também manter um LATEST
    latest_path = Path(project_dir) / '.claude' / 'jarvis' / 'CONTEXT-SNAPSHOT-LATEST.md'
    with open(latest_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return snapshot_path

def log_checkpoint(trigger_data, files_created):
    """Loga o checkpoint executado."""
    project_dir = get_project_dir()
    log_path = Path(project_dir) / 'logs' / 'checkpoints.jsonl'

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'trigger': trigger_data,
        'files_created': [str(f) for f in files_created]
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

def main():
    """Função principal do checkpoint writer."""
    try:
        # Carregar trigger data
        trigger_data = load_checkpoint_trigger()
        if not trigger_data:
            trigger_data = {
                'reason': 'MANUAL',
                'timestamp': datetime.now().isoformat()
            }

        # Carregar estado
        state = load_jarvis_state()

        # Criar arquivos de checkpoint
        files_created = []

        # 1. Atualizar CURRENT-TASK.md
        task_file = update_current_task(trigger_data, state)
        files_created.append(task_file)

        # 2. Criar snapshot de contexto
        snapshot_file = create_context_snapshot(trigger_data, state)
        files_created.append(snapshot_file)

        # 3. Logar checkpoint
        log_checkpoint(trigger_data, files_created)

        # Output
        output = {
            'success': True,
            'files_created': [str(f) for f in files_created],
            'message': f"Checkpoint salvo com sucesso. {len(files_created)} arquivos criados."
        }

        print(json.dumps(output))

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }))

if __name__ == '__main__':
    main()
