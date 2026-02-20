#!/usr/bin/env python3
"""
JARVIS Token Checkpoint System v1.0
Sistema de checkpoint baseado em estimativa de uso de tokens.

Como Claude Code não expõe contagem direta de tokens aos hooks,
usamos heurísticas baseadas em:
- Número de ações/tool calls
- Tamanho do conteúdo processado
- Turnos de conversa

Triggers de checkpoint:
- 50% do limite estimado (WARNING)
- 75% do limite estimado (CHECKPOINT)
- 90% do limite estimado (CRITICAL)

Integra com:
- STATE.json (estado JARVIS)
- Session autosave (persistência)
- HANDOFF system (continuidade)
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
import threading


***REMOVED***=================================
# CONFIGURATION
***REMOVED***=================================

class Config:
    """Configuração do sistema de checkpoint."""
    PROJECT_DIR = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
    JARVIS_DIR = PROJECT_DIR / ".claude" / "jarvis"
    MISSION_CONTROL_DIR = PROJECT_DIR / ".claude" / "mission-control"
    LOGS_DIR = PROJECT_DIR / "logs"

    # Estimativas de tokens por tipo de ação
    TOKENS_PER_TOOL_CALL = 500      # Média estimada por tool call
    TOKENS_PER_CHAR_INPUT = 0.25   # ~4 chars por token
    TOKENS_PER_CHAR_OUTPUT = 0.25

    # Limites de contexto (conservador para Opus)
    CONTEXT_LIMIT = 200000          # Limite estimado de contexto
    WARNING_THRESHOLD = 0.50        # 50% - warning
    CHECKPOINT_THRESHOLD = 0.75    # 75% - checkpoint automático
    CRITICAL_THRESHOLD = 0.90      # 90% - checkpoint crítico

    # Checkpoint por ações (fallback)
    MAX_ACTIONS_BETWEEN_CHECKPOINTS = 50
    MAX_FILES_BETWEEN_CHECKPOINTS = 20

    # Arquivos de estado
    STATE_FILE = JARVIS_DIR / "STATE.json"
    CHECKPOINT_FILE = JARVIS_DIR / "TOKEN-CHECKPOINT.json"
    CHECKPOINT_LOG = LOGS_DIR / "token_checkpoints.jsonl"


class CheckpointLevel(Enum):
    """Níveis de checkpoint."""
    NORMAL = "normal"
    WARNING = "warning"
    CHECKPOINT = "checkpoint"
    CRITICAL = "critical"


***REMOVED***=================================
# DATA STRUCTURES
***REMOVED***=================================

@dataclass
class TokenEstimate:
    """Estimativa de uso de tokens."""
    input_tokens: int = 0
    output_tokens: int = 0
    tool_call_tokens: int = 0
    total_estimated: int = 0
    percent_of_limit: float = 0.0
    level: str = "normal"


@dataclass
class ActionRecord:
    """Registro de uma ação para estimativa."""
    timestamp: str
    action_type: str
    input_chars: int = 0
    output_chars: int = 0
    is_tool_call: bool = False
    estimated_tokens: int = 0


@dataclass
class CheckpointData:
    """Dados de um checkpoint."""
    checkpoint_id: str
    session_id: str
    created_at: str
    level: str
    token_estimate: TokenEstimate
    actions_since_last: int
    files_modified_since_last: int
    summary: str
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    continuation_hint: str = ""


@dataclass
class TokenCheckpointState:
    """Estado completo do sistema de checkpoint."""
    session_id: str
    started_at: str
    last_checkpoint_at: Optional[str] = None
    checkpoint_count: int = 0
    current_estimate: TokenEstimate = field(default_factory=TokenEstimate)
    actions: List[ActionRecord] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    checkpoints: List[str] = field(default_factory=list)  # IDs dos checkpoints


***REMOVED***=================================
# TOKEN CHECKPOINT MANAGER
***REMOVED***=================================

class TokenCheckpointManager:
    """Gerenciador singleton de checkpoints de token."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.state = self._load_or_create_state()
        self._ensure_directories()

    def _ensure_directories(self):
        """Garante que diretórios existem."""
        Config.JARVIS_DIR.mkdir(parents=True, exist_ok=True)
        Config.MISSION_CONTROL_DIR.mkdir(parents=True, exist_ok=True)
        Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def _generate_session_id(self) -> str:
        """Gera ID de sessão."""
        return f"TOKEN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def _generate_checkpoint_id(self) -> str:
        """Gera ID de checkpoint."""
        return f"CKPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{self.state.checkpoint_count + 1:03d}"

    def _load_or_create_state(self) -> TokenCheckpointState:
        """Carrega estado existente ou cria novo."""
        if Config.CHECKPOINT_FILE.exists():
            try:
                with open(Config.CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Reconstruir objetos
                state = TokenCheckpointState(
                    session_id=data.get('session_id', self._generate_session_id()),
                    started_at=data.get('started_at', datetime.now().isoformat()),
                    last_checkpoint_at=data.get('last_checkpoint_at'),
                    checkpoint_count=data.get('checkpoint_count', 0),
                    checkpoints=data.get('checkpoints', []),
                    files_modified=data.get('files_modified', [])
                )

                # Reconstruir token estimate
                if 'current_estimate' in data:
                    est = data['current_estimate']
                    state.current_estimate = TokenEstimate(
                        input_tokens=est.get('input_tokens', 0),
                        output_tokens=est.get('output_tokens', 0),
                        tool_call_tokens=est.get('tool_call_tokens', 0),
                        total_estimated=est.get('total_estimated', 0),
                        percent_of_limit=est.get('percent_of_limit', 0.0),
                        level=est.get('level', 'normal')
                    )

                # Reconstruir actions
                if 'actions' in data:
                    state.actions = [
                        ActionRecord(**a) for a in data['actions'][-100:]  # Manter últimas 100
                    ]

                return state

            except Exception:
                pass

        return TokenCheckpointState(
            session_id=self._generate_session_id(),
            started_at=datetime.now().isoformat()
        )

    def _save_state(self):
        """Salva estado atual."""
        data = {
            'session_id': self.state.session_id,
            'started_at': self.state.started_at,
            'last_checkpoint_at': self.state.last_checkpoint_at,
            'checkpoint_count': self.state.checkpoint_count,
            'checkpoints': self.state.checkpoints,
            'files_modified': self.state.files_modified[-50:],  # Limitar
            'current_estimate': asdict(self.state.current_estimate),
            'actions': [asdict(a) for a in self.state.actions[-100:]],
            'updated_at': datetime.now().isoformat()
        }

        with open(Config.CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _calculate_level(self, percent: float) -> str:
        """Determina nível baseado na porcentagem."""
        if percent >= Config.CRITICAL_THRESHOLD:
            return CheckpointLevel.CRITICAL.value
        elif percent >= Config.CHECKPOINT_THRESHOLD:
            return CheckpointLevel.CHECKPOINT.value
        elif percent >= Config.WARNING_THRESHOLD:
            return CheckpointLevel.WARNING.value
        return CheckpointLevel.NORMAL.value

    def _update_estimate(self):
        """Atualiza estimativa total de tokens."""
        est = self.state.current_estimate
        est.total_estimated = est.input_tokens + est.output_tokens + est.tool_call_tokens
        est.percent_of_limit = est.total_estimated / Config.CONTEXT_LIMIT
        est.level = self._calculate_level(est.percent_of_limit)

    def record_action(
        self,
        action_type: str,
        input_chars: int = 0,
        output_chars: int = 0,
        is_tool_call: bool = False
    ) -> Dict[str, Any]:
        """
        Registra uma ação e atualiza estimativa.

        Returns:
            Dict com status e se checkpoint é necessário
        """
        # Calcular tokens estimados
        input_tokens = int(input_chars * Config.TOKENS_PER_CHAR_INPUT)
        output_tokens = int(output_chars * Config.TOKENS_PER_CHAR_OUTPUT)
        tool_tokens = Config.TOKENS_PER_TOOL_CALL if is_tool_call else 0
        total = input_tokens + output_tokens + tool_tokens

        # Criar registro
        record = ActionRecord(
            timestamp=datetime.now().isoformat(),
            action_type=action_type,
            input_chars=input_chars,
            output_chars=output_chars,
            is_tool_call=is_tool_call,
            estimated_tokens=total
        )

        # Atualizar estado
        self.state.actions.append(record)
        self.state.current_estimate.input_tokens += input_tokens
        self.state.current_estimate.output_tokens += output_tokens
        self.state.current_estimate.tool_call_tokens += tool_tokens

        # Recalcular
        self._update_estimate()

        # Verificar se precisa checkpoint
        needs_checkpoint = self._check_checkpoint_needed()

        # Salvar estado
        self._save_state()

        return {
            'recorded': True,
            'estimated_tokens': total,
            'total_estimated': self.state.current_estimate.total_estimated,
            'percent_of_limit': self.state.current_estimate.percent_of_limit,
            'level': self.state.current_estimate.level,
            'needs_checkpoint': needs_checkpoint
        }

    def record_file_modified(self, file_path: str):
        """Registra arquivo modificado."""
        if file_path not in self.state.files_modified:
            self.state.files_modified.append(file_path)
        self._save_state()

    def _check_checkpoint_needed(self) -> bool:
        """Verifica se checkpoint é necessário."""
        est = self.state.current_estimate

        # Por porcentagem de contexto
        if est.percent_of_limit >= Config.CHECKPOINT_THRESHOLD:
            return True

        # Por número de ações desde último checkpoint
        actions_since = len([
            a for a in self.state.actions
            if not self.state.last_checkpoint_at or
            a.timestamp > self.state.last_checkpoint_at
        ])
        if actions_since >= Config.MAX_ACTIONS_BETWEEN_CHECKPOINTS:
            return True

        # Por número de arquivos
        files_since = len([
            f for i, f in enumerate(self.state.files_modified)
            if i >= len(self.state.files_modified) - Config.MAX_FILES_BETWEEN_CHECKPOINTS
        ])
        if files_since >= Config.MAX_FILES_BETWEEN_CHECKPOINTS:
            return True

        return False

    def create_checkpoint(self, summary: str = "") -> CheckpointData:
        """
        Cria um checkpoint.

        Args:
            summary: Resumo do trabalho até agora

        Returns:
            CheckpointData com informações do checkpoint
        """
        checkpoint_id = self._generate_checkpoint_id()

        # Carregar estado JARVIS para snapshot
        state_snapshot = {}
        if Config.STATE_FILE.exists():
            try:
                with open(Config.STATE_FILE, 'r', encoding='utf-8') as f:
                    state_snapshot = json.load(f)
            except Exception:
                pass

        # Calcular ações desde último checkpoint
        actions_since = len([
            a for a in self.state.actions
            if not self.state.last_checkpoint_at or
            a.timestamp > self.state.last_checkpoint_at
        ])

        # Criar checkpoint
        checkpoint = CheckpointData(
            checkpoint_id=checkpoint_id,
            session_id=self.state.session_id,
            created_at=datetime.now().isoformat(),
            level=self.state.current_estimate.level,
            token_estimate=self.state.current_estimate,
            actions_since_last=actions_since,
            files_modified_since_last=len(self.state.files_modified),
            summary=summary or f"Checkpoint automático - {self.state.current_estimate.percent_of_limit:.1%} do contexto",
            state_snapshot=state_snapshot,
            continuation_hint=self._generate_continuation_hint()
        )

        # Atualizar estado
        self.state.checkpoints.append(checkpoint_id)
        self.state.checkpoint_count += 1
        self.state.last_checkpoint_at = checkpoint.created_at

        # Logar checkpoint
        self._log_checkpoint(checkpoint)

        # Salvar estado
        self._save_state()

        return checkpoint

    def _generate_continuation_hint(self) -> str:
        """Gera dica de continuação para próxima sessão."""
        recent_actions = self.state.actions[-10:]
        action_types = [a.action_type for a in recent_actions]

        if 'batch_process' in action_types:
            return "Continuar processamento de batch"
        elif 'file_write' in action_types or 'file_edit' in action_types:
            return "Continuar modificações de arquivos"
        elif 'search' in action_types:
            return "Continuar pesquisa/análise"

        return "Verificar estado e continuar trabalho"

    def _log_checkpoint(self, checkpoint: CheckpointData):
        """Loga checkpoint em arquivo."""
        log_entry = {
            'timestamp': checkpoint.created_at,
            'checkpoint_id': checkpoint.checkpoint_id,
            'session_id': checkpoint.session_id,
            'level': checkpoint.level,
            'percent_of_limit': checkpoint.token_estimate.percent_of_limit,
            'total_tokens': checkpoint.token_estimate.total_estimated,
            'actions_since_last': checkpoint.actions_since_last,
            'summary': checkpoint.summary[:200]
        }

        with open(Config.CHECKPOINT_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do sistema."""
        return {
            'session_id': self.state.session_id,
            'started_at': self.state.started_at,
            'checkpoint_count': self.state.checkpoint_count,
            'last_checkpoint_at': self.state.last_checkpoint_at,
            'token_estimate': {
                'total': self.state.current_estimate.total_estimated,
                'percent': self.state.current_estimate.percent_of_limit,
                'level': self.state.current_estimate.level
            },
            'actions_count': len(self.state.actions),
            'files_modified': len(self.state.files_modified),
            'needs_checkpoint': self._check_checkpoint_needed()
        }

    def reset_session(self):
        """Reseta para nova sessão."""
        self.state = TokenCheckpointState(
            session_id=self._generate_session_id(),
            started_at=datetime.now().isoformat()
        )
        self._save_state()


***REMOVED***=================================
# GLOBAL API
***REMOVED***=================================

_manager: Optional[TokenCheckpointManager] = None


def get_manager() -> TokenCheckpointManager:
    """Obtém instância do manager."""
    global _manager
    if _manager is None:
        _manager = TokenCheckpointManager()
    return _manager


def record_action(
    action_type: str,
    input_chars: int = 0,
    output_chars: int = 0,
    is_tool_call: bool = False
) -> Dict[str, Any]:
    """Registra uma ação."""
    return get_manager().record_action(action_type, input_chars, output_chars, is_tool_call)


def record_file(file_path: str):
    """Registra arquivo modificado."""
    get_manager().record_file_modified(file_path)


def create_checkpoint(summary: str = "") -> Dict[str, Any]:
    """Cria checkpoint."""
    checkpoint = get_manager().create_checkpoint(summary)
    return asdict(checkpoint)


def get_status() -> Dict[str, Any]:
    """Obtém status atual."""
    return get_manager().get_status()


def needs_checkpoint() -> bool:
    """Verifica se checkpoint é necessário."""
    return get_manager()._check_checkpoint_needed()


def reset_session():
    """Reseta sessão."""
    get_manager().reset_session()


***REMOVED***=================================
# HOOK INTEGRATION
***REMOVED***=================================

def process_hook_input(hook_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa input de hook e registra ação.

    Chamado por outros hooks para registrar ações automaticamente.
    """
    action_type = hook_input.get('tool_name', 'unknown')
    input_content = hook_input.get('tool_input', {})
    output_content = hook_input.get('tool_result', '')

    # Estimar tamanho
    input_chars = len(json.dumps(input_content)) if input_content else 0
    output_chars = len(str(output_content)) if output_content else 0

    result = record_action(
        action_type=action_type,
        input_chars=input_chars,
        output_chars=output_chars,
        is_tool_call=True
    )

    # Se arquivo foi modificado, registrar
    if action_type in ['Write', 'Edit', 'NotebookEdit']:
        file_path = input_content.get('file_path', '')
        if file_path:
            record_file(file_path)

    return result


***REMOVED***=================================
# CLI
***REMOVED***=================================

def main():
    """CLI para teste e debug."""
    import argparse

    parser = argparse.ArgumentParser(description='JARVIS Token Checkpoint System')
    parser.add_argument('command', choices=['status', 'checkpoint', 'reset', 'test', 'record'])
    parser.add_argument('--summary', '-s', help='Resumo para checkpoint')
    parser.add_argument('tool_name', nargs='?', default='unknown', help='Nome da tool (para record)')

    args = parser.parse_args()

    if args.command == 'status':
        status = get_status()
        print(json.dumps(status, indent=2))

    elif args.command == 'checkpoint':
        checkpoint = create_checkpoint(args.summary or '')
        print(f"Checkpoint criado: {checkpoint['checkpoint_id']}")
        print(json.dumps(checkpoint, indent=2, default=str))

    elif args.command == 'reset':
        reset_session()
        print("Sessão resetada")

    elif args.command == 'test':
        # Simular algumas ações
        for i in range(5):
            result = record_action(
                action_type=f'test_action_{i}',
                input_chars=1000,
                output_chars=2000,
                is_tool_call=True
            )
            print(f"Action {i}: {result['percent_of_limit']:.2%}")

        status = get_status()
        print(f"\nStatus final:")
        print(json.dumps(status, indent=2))

    elif args.command == 'record':
        # Registrar ação de tool (chamado pelos hooks)
        result = record_action(
            action_type=args.tool_name,
            input_chars=500,  # Estimativa média
            output_chars=1000,  # Estimativa média
            is_tool_call=True
        )
        # Output silencioso para não poluir - apenas JSON para debug
        print(json.dumps({'recorded': True, 'tool': args.tool_name, 'percent': result['percent_of_limit']}))


if __name__ == '__main__':
    main()
