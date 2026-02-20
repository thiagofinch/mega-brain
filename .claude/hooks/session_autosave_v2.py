#!/usr/bin/env python3
"""
SESSION AUTOSAVE V2 - REGRA #11 ENFORCEMENT
============================================

Sistema de auto-save robusto para sessoes do JARVIS.
Garante que NUNCA mais se perde contexto entre sessoes.

TRIGGERS DE AUTO-SAVE:
- Apos completar qualquer batch
- Apos qualquer tarefa significativa
- A cada 30 minutos de atividade
- Antes de operacoes destrutivas
- Quando detectar pausa prolongada (>10 min sem atividade)
- Quando usuario mencionar que vai sair
- Manualmente via /save

CONTEUDO DO SESSION LOG:
- Estado da missao (fase, progresso)
- Resumo da conversa atual
- Acoes executadas com detalhes
- Arquivos modificados
- Pendencias identificadas
- Decisoes tomadas e razoes
- Proximos passos planejados
- Notas importantes

Author: JARVIS
Version: 2.0.0
Date: 2026-01-11
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import atexit


***REMOVED***=================================
# CONFIGURATION
***REMOVED***=================================

class Config:
    """Configuracao centralizada do sistema de autosave."""

    # Diretorios
    PROJECT_DIR = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
    SESSIONS_DIR = PROJECT_DIR / ".claude" / "sessions"
    MISSION_CONTROL_DIR = PROJECT_DIR / ".claude" / "mission-control"
    LOGS_DIR = PROJECT_DIR / "logs"
    HANDOFFS_DIR = LOGS_DIR / "handoffs"

    # Arquivos principais
    LATEST_SESSION = SESSIONS_DIR / "LATEST-SESSION.md"
    MISSION_STATE = MISSION_CONTROL_DIR / "MISSION-STATE.json"
    JARVIS_STATE = PROJECT_DIR / "system" / "JARVIS-STATE.json"
    AUTOSAVE_STATE = MISSION_CONTROL_DIR / "AUTOSAVE-STATE.json"

    # Timings (em segundos)
    AUTO_SAVE_INTERVAL = 1800  # 30 minutos
    PAUSE_DETECTION_THRESHOLD = 600  # 10 minutos
    MIN_SAVE_INTERVAL = 60  # Minimo 1 minuto entre saves

    # Thresholds
    MAX_UNSAVED_ACTIONS = 10  # Salva se tiver mais que isso
    MAX_UNSAVED_FILES = 5  # Salva se modificar mais que isso


class SaveTrigger(Enum):
    """Tipos de trigger para auto-save."""
    BATCH_COMPLETE = "batch_complete"
    TASK_COMPLETE = "task_complete"
    TIME_INTERVAL = "time_interval"
    DESTRUCTIVE_OP = "destructive_operation"
    PAUSE_DETECTED = "pause_detected"
    USER_EXIT = "user_exit"
    MANUAL = "manual"
    ACTION_THRESHOLD = "action_threshold"
    FILE_THRESHOLD = "file_threshold"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


class ActionType(Enum):
    """Tipos de acao registraveis."""
    BATCH_PROCESS = "batch_process"
    FILE_CREATE = "file_create"
    FILE_MODIFY = "file_modify"
    FILE_DELETE = "file_delete"
    PHASE_CHANGE = "phase_change"
    DECISION = "decision"
    COMMAND = "command"
    SEARCH = "search"
    ANALYSIS = "analysis"
    OTHER = "other"


***REMOVED***=================================
# DATA CLASSES
***REMOVED***=================================

@dataclass
class Action:
    """Representa uma acao registrada na sessao."""
    timestamp: str
    action_type: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    files_affected: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        return cls(**data)


@dataclass
class FileModification:
    """Representa uma modificacao de arquivo."""
    filepath: str
    operation: str  # created, modified, deleted
    timestamp: str
    size_before: Optional[int] = None
    size_after: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileModification':
        return cls(**data)


@dataclass
class SessionData:
    """Dados completos de uma sessao."""
    session_id: str
    started_at: str
    last_activity: str
    last_save: Optional[str]
    save_count: int
    mission_state: Dict[str, Any]
    actions: List[Action]
    files_modified: List[FileModification]
    pending_tasks: List[str]
    decisions: List[Dict[str, Any]]
    next_steps: List[str]
    notes: List[str]
    conversation_summary: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['actions'] = [a.to_dict() if isinstance(a, Action) else a for a in self.actions]
        data['files_modified'] = [f.to_dict() if isinstance(f, FileModification) else f for f in self.files_modified]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        data['actions'] = [Action.from_dict(a) if isinstance(a, dict) else a for a in data.get('actions', [])]
        data['files_modified'] = [FileModification.from_dict(f) if isinstance(f, dict) else f for f in data.get('files_modified', [])]
        return cls(**data)


***REMOVED***=================================
# SESSION MANAGER
***REMOVED***=================================

class SessionManager:
    """
    Gerenciador principal de sessoes.
    Implementa REGRA #11 do CLAUDE.md.
    """

    _instance: Optional['SessionManager'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern para garantir uma unica instancia."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._ensure_directories()
        self._load_or_create_session()

        # Registrar save no encerramento
        atexit.register(self._on_exit)

    def _ensure_directories(self):
        """Garante que todos os diretorios existam."""
        for directory in [Config.SESSIONS_DIR, Config.MISSION_CONTROL_DIR,
                          Config.LOGS_DIR, Config.HANDOFFS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    def _generate_session_id(self) -> str:
        """Gera ID unico para a sessao."""
        now = datetime.now()
        return f"SESSION-{now.strftime('%Y-%m-%d-%H%M')}"

    def _load_or_create_session(self):
        """Carrega sessao existente ou cria nova."""
        if Config.AUTOSAVE_STATE.exists():
            try:
                with open(Config.AUTOSAVE_STATE, 'r', encoding='utf-8') as f:
                    state = json.load(f)

                # Verificar se sessao ainda e valida (menos de 2 horas)
                last_activity = datetime.fromisoformat(state.get('last_activity', '2000-01-01'))
                if datetime.now() - last_activity < timedelta(hours=2):
                    self.session = SessionData.from_dict(state)
                    self.session.last_activity = datetime.now().isoformat()
                    return
            except Exception:
                pass

        # Criar nova sessao
        self.session = self._create_new_session()

    def _create_new_session(self) -> SessionData:
        """Cria uma nova sessao."""
        now = datetime.now().isoformat()
        mission_state = self._load_mission_state()

        return SessionData(
            session_id=self._generate_session_id(),
            started_at=now,
            last_activity=now,
            last_save=None,
            save_count=0,
            mission_state=mission_state,
            actions=[],
            files_modified=[],
            pending_tasks=[],
            decisions=[],
            next_steps=[],
            notes=[],
            conversation_summary=""
        )

    def _load_mission_state(self) -> Dict[str, Any]:
        """Carrega estado da missao do MISSION-STATE.json."""
        if Config.MISSION_STATE.exists():
            try:
                with open(Config.MISSION_STATE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"status": "unknown", "message": "MISSION-STATE.json nao encontrado"}

    def _load_jarvis_state(self) -> Dict[str, Any]:
        """Carrega estado do JARVIS."""
        if Config.JARVIS_STATE.exists():
            try:
                with open(Config.JARVIS_STATE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    ***REMOVED***=============================
    # LOGGING ACTIONS
    ***REMOVED***=============================

    def log_action(self,
                   action_type: ActionType,
                   description: str,
                   details: Dict[str, Any] = None,
                   files_affected: List[str] = None) -> None:
        """
        Registra uma acao na sessao.

        Args:
            action_type: Tipo da acao (ActionType enum)
            description: Descricao legivel da acao
            details: Detalhes adicionais (opcional)
            files_affected: Lista de arquivos afetados (opcional)
        """
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type=action_type.value if isinstance(action_type, ActionType) else str(action_type),
            description=description,
            details=details or {},
            files_affected=files_affected or []
        )

        self.session.actions.append(action)
        self.session.last_activity = datetime.now().isoformat()

        # Verificar se deve salvar (threshold de acoes)
        if len(self.session.actions) >= Config.MAX_UNSAVED_ACTIONS:
            self._check_and_save(SaveTrigger.ACTION_THRESHOLD)

        # Persistir estado temporario
        self._save_autosave_state()

    def log_file_modified(self,
                          filepath: str,
                          operation: str = "modified",
                          size_before: int = None,
                          size_after: int = None) -> None:
        """
        Registra modificacao de arquivo.

        Args:
            filepath: Caminho do arquivo
            operation: Tipo de operacao (created, modified, deleted)
            size_before: Tamanho antes (opcional)
            size_after: Tamanho depois (opcional)
        """
        mod = FileModification(
            filepath=filepath,
            operation=operation,
            timestamp=datetime.now().isoformat(),
            size_before=size_before,
            size_after=size_after
        )

        self.session.files_modified.append(mod)
        self.session.last_activity = datetime.now().isoformat()

        # Verificar se deve salvar (threshold de arquivos)
        if len(self.session.files_modified) >= Config.MAX_UNSAVED_FILES:
            self._check_and_save(SaveTrigger.FILE_THRESHOLD)

        self._save_autosave_state()

    def log_decision(self,
                     decision: str,
                     reasoning: str,
                     alternatives: List[str] = None) -> None:
        """
        Registra uma decisao tomada.

        Args:
            decision: A decisao tomada
            reasoning: Raciocinio por tras
            alternatives: Alternativas consideradas
        """
        self.session.decisions.append({
            'timestamp': datetime.now().isoformat(),
            'decision': decision,
            'reasoning': reasoning,
            'alternatives': alternatives or []
        })

        self.session.last_activity = datetime.now().isoformat()
        self._save_autosave_state()

    def add_pending_task(self, task: str) -> None:
        """Adiciona tarefa pendente."""
        if task not in self.session.pending_tasks:
            self.session.pending_tasks.append(task)
            self._save_autosave_state()

    def complete_pending_task(self, task: str) -> None:
        """Marca tarefa como completa."""
        if task in self.session.pending_tasks:
            self.session.pending_tasks.remove(task)
            self._save_autosave_state()

    def add_next_step(self, step: str) -> None:
        """Adiciona proximo passo planejado."""
        if step not in self.session.next_steps:
            self.session.next_steps.append(step)
            self._save_autosave_state()

    def add_note(self, note: str) -> None:
        """Adiciona nota importante."""
        timestamped_note = f"[{datetime.now().strftime('%H:%M')}] {note}"
        self.session.notes.append(timestamped_note)
        self._save_autosave_state()

    def update_conversation_summary(self, summary: str) -> None:
        """Atualiza resumo da conversa."""
        self.session.conversation_summary = summary
        self._save_autosave_state()

    ***REMOVED***=============================
    # SAVE TRIGGERS
    ***REMOVED***=============================

    def trigger_batch_complete(self, batch_id: str, details: Dict = None) -> str:
        """Trigger: Batch completado."""
        self.log_action(
            ActionType.BATCH_PROCESS,
            f"Batch {batch_id} completado",
            details
        )
        return self.save(SaveTrigger.BATCH_COMPLETE)

    def trigger_task_complete(self, task_name: str, details: Dict = None) -> str:
        """Trigger: Tarefa significativa completada."""
        self.log_action(
            ActionType.OTHER,
            f"Tarefa completada: {task_name}",
            details
        )
        return self.save(SaveTrigger.TASK_COMPLETE)

    def trigger_destructive_operation(self, operation: str) -> str:
        """Trigger: Antes de operacao destrutiva."""
        self.add_note(f"ALERTA: Operacao destrutiva iminente - {operation}")
        return self.save(SaveTrigger.DESTRUCTIVE_OP)

    def trigger_user_exit(self) -> str:
        """Trigger: Usuario mencionou que vai sair."""
        return self.save(SaveTrigger.USER_EXIT)

    def trigger_phase_change(self, old_phase: int, new_phase: int) -> str:
        """Trigger: Mudanca de fase."""
        self.log_action(
            ActionType.PHASE_CHANGE,
            f"Mudanca de fase: {old_phase} -> {new_phase}"
        )
        return self.save(SaveTrigger.TASK_COMPLETE)

    ***REMOVED***=============================
    # CORE SAVE LOGIC
    ***REMOVED***=============================

    def should_save(self, trigger: SaveTrigger = None) -> bool:
        """
        Verifica se deve salvar baseado em triggers.

        Returns:
            True se deve salvar, False caso contrario
        """
        # Sempre salva em triggers criticos
        critical_triggers = [
            SaveTrigger.BATCH_COMPLETE,
            SaveTrigger.DESTRUCTIVE_OP,
            SaveTrigger.USER_EXIT,
            SaveTrigger.SESSION_END,
            SaveTrigger.MANUAL
        ]

        if trigger in critical_triggers:
            return True

        # Verificar intervalo minimo
        if self.session.last_save:
            last_save_time = datetime.fromisoformat(self.session.last_save)
            if datetime.now() - last_save_time < timedelta(seconds=Config.MIN_SAVE_INTERVAL):
                return False

        # Verificar intervalo de tempo (30 min)
        if self.session.last_save:
            last_save_time = datetime.fromisoformat(self.session.last_save)
            if datetime.now() - last_save_time > timedelta(seconds=Config.AUTO_SAVE_INTERVAL):
                return True
        else:
            # Nunca salvou, e passou tempo desde inicio
            start_time = datetime.fromisoformat(self.session.started_at)
            if datetime.now() - start_time > timedelta(seconds=Config.AUTO_SAVE_INTERVAL):
                return True

        # Verificar threshold de acoes
        if len(self.session.actions) >= Config.MAX_UNSAVED_ACTIONS:
            return True

        # Verificar threshold de arquivos
        if len(self.session.files_modified) >= Config.MAX_UNSAVED_FILES:
            return True

        # Verificar pausa prolongada
        last_activity = datetime.fromisoformat(self.session.last_activity)
        if datetime.now() - last_activity > timedelta(seconds=Config.PAUSE_DETECTION_THRESHOLD):
            return True

        return False

    def _check_and_save(self, trigger: SaveTrigger) -> Optional[str]:
        """Verifica e salva se necessario."""
        if self.should_save(trigger):
            return self.save(trigger)
        return None

    def save(self, trigger: SaveTrigger = SaveTrigger.MANUAL) -> str:
        """
        Salva estado da sessao.

        Args:
            trigger: O que disparou o save

        Returns:
            Caminho do arquivo de sessao salvo
        """
        now = datetime.now()

        # Atualizar estado da missao
        self.session.mission_state = self._load_mission_state()
        self.session.last_save = now.isoformat()
        self.session.save_count += 1

        # Gerar conteudo do arquivo de sessao
        session_content = self._format_session_markdown(trigger)

        # Salvar arquivo da sessao
        session_filename = f"{self.session.session_id}.md"
        session_filepath = Config.SESSIONS_DIR / session_filename

        with open(session_filepath, 'w', encoding='utf-8') as f:
            f.write(session_content)

        # Atualizar LATEST-SESSION.md
        self._update_latest_session(session_content, trigger)

        # Salvar estado do autosave
        self._save_autosave_state()

        # Criar HANDOFF se trigger critico
        if trigger in [SaveTrigger.USER_EXIT, SaveTrigger.SESSION_END]:
            self._create_handoff()

        return str(session_filepath)

    def _save_autosave_state(self):
        """Salva estado temporario do autosave."""
        try:
            with open(Config.AUTOSAVE_STATE, 'w', encoding='utf-8') as f:
                json.dump(self.session.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[JARVIS] Erro ao salvar autosave state: {e}")

    def _update_latest_session(self, content: str, trigger: SaveTrigger):
        """Atualiza LATEST-SESSION.md."""
        latest_content = f"""# LATEST SESSION - Auto-Updated

**Session ID:** {self.session.session_id}
**Last Save:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Trigger:** {trigger.value}
**Save Count:** {self.session.save_count}

---

{content}
"""

        with open(Config.LATEST_SESSION, 'w', encoding='utf-8') as f:
            f.write(latest_content)

    def _create_handoff(self):
        """Cria arquivo HANDOFF para proxima sessao."""
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        handoff_file = Config.HANDOFFS_DIR / f"HANDOFF-{timestamp}.md"

        mission = self.session.mission_state
        current_state = mission.get('current_state', {})

        content = f"""# HANDOFF - {datetime.now().strftime('%Y-%m-%d %H:%M')}

> **Gerado por:** Session Autosave V2
> **Session ID:** {self.session.session_id}
> **Save Count:** {self.session.save_count}

---

## ESTADO ATUAL DA MISSAO

| Campo | Valor |
|-------|-------|
| Fase | {current_state.get('phase', 'N/A')} - {current_state.get('phase_name', 'N/A')} |
| Status | {current_state.get('status', 'N/A')} |
| Progresso | {current_state.get('percent_complete', 0):.1f}% |
| Fonte Atual | {current_state.get('source_code', 'N/A')} |

---

## ULTIMAS ACOES ({len(self.session.actions)})

"""
        # Ultimas 10 acoes
        for action in self.session.actions[-10:]:
            if isinstance(action, Action):
                content += f"- [{action.timestamp[-8:-3]}] {action.description}\n"
            else:
                content += f"- {action.get('description', 'Acao')}\n"

        content += f"""

---

## ARQUIVOS MODIFICADOS ({len(self.session.files_modified)})

"""
        # Ultimos 10 arquivos
        for mod in self.session.files_modified[-10:]:
            if isinstance(mod, FileModification):
                content += f"- `{mod.operation}`: {mod.filepath}\n"
            else:
                content += f"- `{mod.get('operation', 'mod')}`: {mod.get('filepath', '')}\n"

        content += f"""

---

## PENDENCIAS ({len(self.session.pending_tasks)})

"""
        for task in self.session.pending_tasks:
            content += f"- [ ] {task}\n"

        content += f"""

---

## PROXIMOS PASSOS ({len(self.session.next_steps)})

"""
        for i, step in enumerate(self.session.next_steps, 1):
            content += f"{i}. {step}\n"

        content += f"""

---

## NOTAS IMPORTANTES

"""
        for note in self.session.notes:
            content += f"- {note}\n"

        content += f"""

---

## PARA CONTINUAR

1. Execute `/resume` para carregar este contexto
2. Pergunte "onde paramos?" para status detalhado
3. JARVIS carregara memoria automaticamente

---

*Ready when you are, sir.*
*Auto-generated by Session Autosave V2*
"""

        with open(handoff_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # Atualizar link para ultimo HANDOFF
        latest_handoff = Config.HANDOFFS_DIR / "HANDOFF-LATEST.md"
        with open(latest_handoff, 'w', encoding='utf-8') as f:
            f.write(content)

    def _format_session_markdown(self, trigger: SaveTrigger) -> str:
        """Formata sessao em Markdown estruturado."""
        now = datetime.now()
        mission = self.session.mission_state
        current_state = mission.get('current_state', {})

        # Calcular estatisticas
        actions_by_type = {}
        for action in self.session.actions:
            atype = action.action_type if isinstance(action, Action) else action.get('action_type', 'other')
            actions_by_type[atype] = actions_by_type.get(atype, 0) + 1

        files_by_op = {}
        for mod in self.session.files_modified:
            op = mod.operation if isinstance(mod, FileModification) else mod.get('operation', 'modified')
            files_by_op[op] = files_by_op.get(op, 0) + 1

        md = f"""# {self.session.session_id}

> **JARVIS Session Log - Autosave V2**
> **REGRA #11 Enforcement: Persistencia de Sessao Obrigatoria**

---

## META INFORMACAO

| Campo | Valor |
|-------|-------|
| **Session ID** | `{self.session.session_id}` |
| **Iniciada** | {self.session.started_at} |
| **Ultima Atividade** | {self.session.last_activity} |
| **Este Save** | {now.isoformat()} |
| **Trigger** | `{trigger.value}` |
| **Save Count** | {self.session.save_count} |

---

## ESTADO DA MISSAO

```
+{'='*70}+
|{'MISSION STATE':^70}|
+{'='*70}+
| Fase: {str(current_state.get('phase', 'N/A')):>3} - {current_state.get('phase_name', 'N/A'):<54} |
| Status: {current_state.get('status', 'N/A'):<60} |
| Progresso: {str(current_state.get('percent_complete', 0)) + '%':<58} |
| Fonte: {current_state.get('source_code', 'N/A'):<61} |
+{'='*70}+
```

---

## RESUMO DA CONVERSA

{self.session.conversation_summary or '_Nenhum resumo registrado nesta sessao._'}

---

## ACOES EXECUTADAS ({len(self.session.actions)})

### Por Tipo
"""

        for atype, count in sorted(actions_by_type.items(), key=lambda x: -x[1]):
            md += f"- **{atype}**: {count}\n"

        md += "\n### Cronologia\n\n"
        md += "| Timestamp | Tipo | Descricao |\n"
        md += "|-----------|------|----------|\n"

        for action in self.session.actions[-20:]:  # Ultimas 20
            if isinstance(action, Action):
                ts = action.timestamp[-8:-3] if len(action.timestamp) > 8 else action.timestamp
                md += f"| {ts} | {action.action_type} | {action.description[:50]} |\n"
            else:
                md += f"| - | - | {action.get('description', '-')[:50]} |\n"

        if len(self.session.actions) > 20:
            md += f"\n_... e mais {len(self.session.actions) - 20} acoes anteriores_\n"

        md += f"""

---

## ARQUIVOS MODIFICADOS ({len(self.session.files_modified)})

### Por Operacao
"""

        for op, count in sorted(files_by_op.items(), key=lambda x: -x[1]):
            md += f"- **{op}**: {count}\n"

        md += "\n### Lista\n\n"

        for mod in self.session.files_modified[-15:]:  # Ultimos 15
            if isinstance(mod, FileModification):
                md += f"- `{mod.operation}` {mod.filepath}\n"
            else:
                md += f"- `{mod.get('operation', 'mod')}` {mod.get('filepath', '')}\n"

        if len(self.session.files_modified) > 15:
            md += f"\n_... e mais {len(self.session.files_modified) - 15} arquivos anteriores_\n"

        md += f"""

---

## DECISOES TOMADAS ({len(self.session.decisions)})

"""

        for decision in self.session.decisions:
            md += f"""### {decision.get('decision', 'Decisao')[:50]}

- **Raciocinio:** {decision.get('reasoning', '-')}
- **Alternativas:** {', '.join(decision.get('alternatives', [])) or 'Nenhuma'}
- **Quando:** {decision.get('timestamp', '-')}

"""

        if not self.session.decisions:
            md += "_Nenhuma decisao registrada nesta sessao._\n"

        md += f"""

---

## PENDENCIAS ({len(self.session.pending_tasks)})

"""

        for task in self.session.pending_tasks:
            md += f"- [ ] {task}\n"

        if not self.session.pending_tasks:
            md += "_Nenhuma pendencia registrada._\n"

        md += f"""

---

## PROXIMOS PASSOS PLANEJADOS ({len(self.session.next_steps)})

"""

        for i, step in enumerate(self.session.next_steps, 1):
            md += f"{i}. {step}\n"

        if not self.session.next_steps:
            md += "_Nenhum proximo passo definido._\n"

        md += f"""

---

## NOTAS IMPORTANTES

"""

        for note in self.session.notes:
            md += f"- {note}\n"

        if not self.session.notes:
            md += "_Nenhuma nota registrada._\n"

        md += f"""

---

## INFORMACOES TECNICAS

```json
{{
  "session_id": "{self.session.session_id}",
  "started_at": "{self.session.started_at}",
  "last_save": "{self.session.last_save}",
  "save_count": {self.session.save_count},
  "trigger": "{trigger.value}",
  "total_actions": {len(self.session.actions)},
  "total_files_modified": {len(self.session.files_modified)},
  "total_decisions": {len(self.session.decisions)},
  "total_pending": {len(self.session.pending_tasks)},
  "total_next_steps": {len(self.session.next_steps)}
}}
```

---

*Auto-saved by JARVIS Session Autosave V2*
*REGRA #11: Contexto perdido = Trabalho perdido*
*Timestamp: {now.isoformat()}*
"""

        return md

    def _on_exit(self):
        """Handler para encerramento."""
        try:
            self.save(SaveTrigger.SESSION_END)
        except Exception:
            pass


***REMOVED***=================================
# GLOBAL API
***REMOVED***=================================

_session_manager: Optional[SessionManager] = None


def get_session() -> SessionManager:
    """Obtem instancia do SessionManager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def trigger_save(reason: str = "manual") -> str:
    """
    Trigger para salvar sessao manualmente.

    Args:
        reason: Motivo do save

    Returns:
        Caminho do arquivo salvo
    """
    session = get_session()
    trigger = SaveTrigger.MANUAL

    # Mapear reason para trigger
    reason_map = {
        'batch_complete': SaveTrigger.BATCH_COMPLETE,
        'task_complete': SaveTrigger.TASK_COMPLETE,
        'destructive': SaveTrigger.DESTRUCTIVE_OP,
        'user_exit': SaveTrigger.USER_EXIT,
        'pause': SaveTrigger.PAUSE_DETECTED,
        'time': SaveTrigger.TIME_INTERVAL
    }

    for key, val in reason_map.items():
        if key in reason.lower():
            trigger = val
            break

    return session.save(trigger)


def log_action(action: str,
               action_type: str = "other",
               details: dict = None,
               files: list = None) -> None:
    """
    API para registrar acao.

    Args:
        action: Descricao da acao
        action_type: Tipo (batch_process, file_create, etc)
        details: Detalhes adicionais
        files: Arquivos afetados
    """
    session = get_session()

    # Converter string para enum
    try:
        atype = ActionType(action_type)
    except ValueError:
        atype = ActionType.OTHER

    session.log_action(atype, action, details, files)


def log_file(filepath: str, operation: str = "modified") -> None:
    """
    API para registrar arquivo modificado.

    Args:
        filepath: Caminho do arquivo
        operation: Tipo (created, modified, deleted)
    """
    get_session().log_file_modified(filepath, operation)


def log_decision(decision: str, reasoning: str, alternatives: list = None) -> None:
    """
    API para registrar decisao.

    Args:
        decision: A decisao tomada
        reasoning: Raciocinio
        alternatives: Alternativas consideradas
    """
    get_session().log_decision(decision, reasoning, alternatives)


def add_pending(task: str) -> None:
    """Adiciona tarefa pendente."""
    get_session().add_pending_task(task)


def complete_pending(task: str) -> None:
    """Marca tarefa como completa."""
    get_session().complete_pending_task(task)


def add_next_step(step: str) -> None:
    """Adiciona proximo passo."""
    get_session().add_next_step(step)


def add_note(note: str) -> None:
    """Adiciona nota importante."""
    get_session().add_note(note)


def update_summary(summary: str) -> None:
    """Atualiza resumo da conversa."""
    get_session().update_conversation_summary(summary)


def on_batch_complete(batch_id: str, details: dict = None) -> str:
    """Trigger para batch completado."""
    return get_session().trigger_batch_complete(batch_id, details)


def on_task_complete(task_name: str, details: dict = None) -> str:
    """Trigger para tarefa completada."""
    return get_session().trigger_task_complete(task_name, details)


def on_destructive_operation(operation: str) -> str:
    """Trigger antes de operacao destrutiva."""
    return get_session().trigger_destructive_operation(operation)


def on_user_exit() -> str:
    """Trigger quando usuario vai sair."""
    return get_session().trigger_user_exit()


def on_phase_change(old_phase: int, new_phase: int) -> str:
    """Trigger para mudanca de fase."""
    return get_session().trigger_phase_change(old_phase, new_phase)


def get_session_status() -> dict:
    """Retorna status atual da sessao."""
    session = get_session()
    return {
        'session_id': session.session.session_id,
        'started_at': session.session.started_at,
        'last_activity': session.session.last_activity,
        'last_save': session.session.last_save,
        'save_count': session.session.save_count,
        'actions_count': len(session.session.actions),
        'files_modified_count': len(session.session.files_modified),
        'pending_tasks': len(session.session.pending_tasks),
        'should_save': session.should_save()
    }


***REMOVED***=================================
# CLI INTERFACE
***REMOVED***=================================

def main():
    """Interface de linha de comando."""
    import sys

    if len(sys.argv) < 2:
        print("JARVIS Session Autosave V2")
        print("-" * 40)
        print("Uso: session_autosave_v2.py <comando>")
        print("")
        print("Comandos:")
        print("  save [reason]     - Salvar sessao")
        print("  status            - Status da sessao")
        print("  log <action>      - Registrar acao")
        print("  file <path> <op>  - Registrar arquivo")
        print("  pending <task>    - Adicionar pendencia")
        print("  note <note>       - Adicionar nota")
        print("  test              - Executar teste")
        return

    cmd = sys.argv[1].lower()

    if cmd == 'save':
        reason = sys.argv[2] if len(sys.argv) > 2 else 'manual'
        result = trigger_save(reason)
        print(f"[JARVIS] Sessao salva: {result}")

    elif cmd == 'status':
        status = get_session_status()
        print("[JARVIS] Status da Sessao:")
        print("-" * 40)
        for key, val in status.items():
            print(f"  {key}: {val}")

    elif cmd == 'log':
        action = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else 'Acao generica'
        log_action(action)
        print(f"[JARVIS] Acao registrada: {action}")

    elif cmd == 'file':
        if len(sys.argv) < 3:
            print("Uso: file <path> [operation]")
            return
        filepath = sys.argv[2]
        operation = sys.argv[3] if len(sys.argv) > 3 else 'modified'
        log_file(filepath, operation)
        print(f"[JARVIS] Arquivo registrado: {operation} - {filepath}")

    elif cmd == 'pending':
        task = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else 'Tarefa pendente'
        add_pending(task)
        print(f"[JARVIS] Pendencia adicionada: {task}")

    elif cmd == 'note':
        note = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else 'Nota importante'
        add_note(note)
        print(f"[JARVIS] Nota adicionada: {note}")

    elif cmd == 'test':
        print("[JARVIS] Executando teste do Session Autosave V2...")
        print("-" * 40)

        # Teste completo
        session = get_session()

        # Registrar acoes
        log_action("Teste de acao 1", "other", {"teste": True})
        log_action("Teste de acao 2", "batch_process", {"batch": "TEST-001"})

        # Registrar arquivos
        log_file("/test/arquivo1.md", "created")
        log_file("/test/arquivo2.txt", "modified")

        # Registrar decisao
        log_decision(
            "Usar formato Markdown para logs",
            "Melhor legibilidade e compatibilidade",
            ["JSON puro", "YAML", "Plain text"]
        )

        # Pendencias e notas
        add_pending("Finalizar documentacao")
        add_next_step("Testar em producao")
        add_note("Sistema funcionando corretamente")

        # Atualizar resumo
        update_summary("Sessao de teste do autosave v2. Todas as funcionalidades testadas.")

        # Salvar
        result = trigger_save("test")

        print(f"[JARVIS] Teste concluido!")
        print(f"[JARVIS] Sessao salva em: {result}")
        print("-" * 40)

        # Mostrar status
        status = get_session_status()
        print("[JARVIS] Status Final:")
        for key, val in status.items():
            print(f"  {key}: {val}")

    else:
        print(f"[JARVIS] Comando desconhecido: {cmd}")
        print("Use 'session_autosave_v2.py' sem argumentos para ver ajuda.")


if __name__ == "__main__":
    main()
