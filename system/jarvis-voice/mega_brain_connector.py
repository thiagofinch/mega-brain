# mega_brain_connector.py
"""
JARVIS Voice System - Mega Brain Connector
==========================================
Conecta o JARVIS Voice ao sistema Mega Brain existente.

Responsabilidades:
- Ler e atualizar STATE.json
- Ler logs de decisões
- Consultar contexto de agentes
- Manter histórico de ações
- Fornecer contexto completo para o Claude
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any

from config import Config


class MegaBrainConnector:
    """
    Conecta JARVIS Voice ao sistema Mega Brain.
    Lê estado, agentes, histórico de decisões.
    """

    def __init__(self):
        self.config = Config()
        self.state = self._load_state()
        self._ensure_paths_exist()

    def _ensure_paths_exist(self):
        """Garante que os diretórios necessários existem."""
        jarvis_path = Path(self.config.JARVIS_BASE_PATH)
        jarvis_path.mkdir(parents=True, exist_ok=True)

        # Cria checkpoints se não existir
        checkpoints_path = jarvis_path / "checkpoints"
        checkpoints_path.mkdir(exist_ok=True)

        # Cria patterns se não existir
        patterns_path = jarvis_path / "patterns"
        patterns_path.mkdir(exist_ok=True)

    def _load_state(self) -> Dict:
        """Carrega STATE.json do JARVIS."""
        try:
            with open(self.config.JARVIS_STATE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_state()
        except json.JSONDecodeError:
            print(f"[WARN] STATE.json corrompido, criando novo...")
            return self._create_default_state()

    def _create_default_state(self) -> Dict:
        """Cria estado padrão se não existir."""
        state = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "voice_system": {
                "version": "1.0.0",
                "last_session": None,
                "total_interactions": 0
            },
            "mission": {
                "id": None,
                "phase": 0,
                "subphase": 0,
                "batch": 0,
                "total_batches": 0,
                "status": "NOT_STARTED"
            },
            "pipeline": {
                "files_processed": 0,
                "files_remaining": 0,
                "insights_extracted": 0,
                "heuristics_found": 0,
                "chunks_created": 0,
                "narratives_synthesized": 0
            },
            "agents": {
                "active": [],
                "last_consulted": None
            },
            "context": {
                "last_10_actions": [],
                "pending_questions": [],
                "session_start": None
            }
        }

        # Salva o estado inicial
        self._save_state_to_file(state)
        return state

    def _save_state_to_file(self, state: Dict):
        """Salva estado no arquivo."""
        try:
            with open(self.config.JARVIS_STATE_PATH, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Falha ao salvar STATE.json: {e}")

    def save_state(self):
        """Salva estado atualizado."""
        self.state["last_updated"] = datetime.now().isoformat()
        self._save_state_to_file(self.state)

    def reload_state(self):
        """Recarrega estado do arquivo."""
        self.state = self._load_state()

    ***REMOVED***==============================
    # CONTEXT FOR CLAUDE
    ***REMOVED***==============================

    def get_context_for_claude(self) -> str:
        """
        Monta contexto completo para enviar ao Claude.
        Isso dá ao JARVIS conhecimento do estado do sistema.
        """
        mission = self.state.get("mission", {})
        pipeline = self.state.get("pipeline", {})
        context = self.state.get("context", {})
        voice = self.state.get("voice_system", {})

        return f"""
ESTADO ATUAL DO MEGA BRAIN:
==========================

MISSÃO:
- ID: {mission.get('id', 'Nenhuma')}
- Phase: {mission.get('phase', '?')}.{mission.get('subphase', '?')}
- Status: {mission.get('status', 'UNKNOWN')}
- Batch: {mission.get('batch', '?')}/{mission.get('total_batches', '?')}

PIPELINE:
- Arquivos processados: {pipeline.get('files_processed', 0)}
- Arquivos restantes: {pipeline.get('files_remaining', 0)}
- Insights extraídos: {pipeline.get('insights_extracted', 0)}
- Heurísticas encontradas: {pipeline.get('heuristics_found', 0)}
- Chunks criados: {pipeline.get('chunks_created', 0)}
- Narrativas sintetizadas: {pipeline.get('narratives_synthesized', 0)}

ÚLTIMAS AÇÕES:
{self._format_last_actions(context.get('last_10_actions', []))}

PENDÊNCIAS:
{self._format_pending(context.get('pending_questions', []))}

VOICE SYSTEM:
- Interações totais: {voice.get('total_interactions', 0)}
- Última sessão: {voice.get('last_session', 'Primeira sessão')}
"""

    def _format_last_actions(self, actions: List) -> str:
        """Formata últimas ações para o contexto."""
        if not actions:
            return "- Nenhuma ação recente registrada"
        return "\n".join([f"- {a}" for a in actions[-5:]])

    def _format_pending(self, pending: List) -> str:
        """Formata pendências para o contexto."""
        if not pending:
            return "- Nenhuma pendência"
        return "\n".join([f"- {p}" for p in pending])

    ***REMOVED***==============================
    # ACTION LOGGING
    ***REMOVED***==============================

    def add_action(self, action: str):
        """Registra uma ação no histórico."""
        if "context" not in self.state:
            self.state["context"] = {}

        if "last_10_actions" not in self.state["context"]:
            self.state["context"]["last_10_actions"] = []

        timestamp = datetime.now().strftime('%H:%M')
        self.state["context"]["last_10_actions"].append(
            f"[{timestamp}] {action}"
        )

        # Mantém apenas últimas 10
        self.state["context"]["last_10_actions"] = \
            self.state["context"]["last_10_actions"][-10:]

        self.save_state()

    def log_decision(self, decision: str, rationale: str = ""):
        """
        Registra uma decisão no DECISIONS-LOG.md.

        Args:
            decision: A decisão tomada
            rationale: Justificativa (opcional)
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            entry = f"""
## [{timestamp}] Voice Decision

**Decisão:** {decision}
"""
            if rationale:
                entry += f"**Justificativa:** {rationale}\n"

            entry += "\n---\n"

            # Append ao arquivo
            with open(self.config.JARVIS_DECISIONS_PATH, 'a', encoding='utf-8') as f:
                f.write(entry)

        except Exception as e:
            print(f"[ERROR] Falha ao registrar decisão: {e}")

    ***REMOVED***==============================
    # AGENT CONTEXT
    ***REMOVED***==============================

    def get_agent_context(self, agent_name: str) -> Optional[str]:
        """
        Carrega contexto de um agente específico.

        Args:
            agent_name: Nome do agente (ex: 'closer', 'CRO')

        Returns:
            Conteúdo do SOUL.md ou AGENT.md do agente
        """
        # Tenta diferentes caminhos possíveis
        possible_paths = [
            f"{self.config.AGENTS_PATH}/cargo/SALES/{agent_name}/SOUL.md",
            f"{self.config.AGENTS_PATH}/cargo/C-LEVEL/{agent_name}/SOUL.md",
            f"{self.config.AGENTS_PATH}/cargo/MARKETING/{agent_name}/SOUL.md",
            f"{self.config.AGENTS_PATH}/cargo/OPERATIONS/{agent_name}/SOUL.md",
            f"{self.config.AGENTS_PATH}/persons/{agent_name}/SOUL.md",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Registra que consultou o agente
                    self.state["agents"]["last_consulted"] = agent_name
                    self.save_state()

                    return content
                except Exception as e:
                    return f"Erro ao carregar agente {agent_name}: {e}"

        return f"Agente {agent_name} não encontrado"

    def get_available_agents(self) -> List[str]:
        """Lista agentes disponíveis no sistema."""
        agents = []

        base_paths = [
            f"{self.config.AGENTS_PATH}/cargo/SALES",
            f"{self.config.AGENTS_PATH}/cargo/C-LEVEL",
            f"{self.config.AGENTS_PATH}/cargo/MARKETING",
            f"{self.config.AGENTS_PATH}/cargo/OPERATIONS",
            f"{self.config.AGENTS_PATH}/persons",
        ]

        for base in base_paths:
            if os.path.exists(base):
                for item in os.listdir(base):
                    item_path = os.path.join(base, item)
                    if os.path.isdir(item_path):
                        # Verifica se tem SOUL.md ou AGENT.md
                        if os.path.exists(os.path.join(item_path, "SOUL.md")) or \
                           os.path.exists(os.path.join(item_path, "AGENT.md")):
                            agents.append(item)

        return sorted(set(agents))

    ***REMOVED***==============================
    # PIPELINE STATUS
    ***REMOVED***==============================

    def update_pipeline_status(self, **kwargs):
        """Atualiza status do pipeline."""
        if "pipeline" not in self.state:
            self.state["pipeline"] = {}

        for key, value in kwargs.items():
            if key in self.state["pipeline"] or True:  # Aceita novos campos
                self.state["pipeline"][key] = value

        self.save_state()

    def update_mission_status(self, **kwargs):
        """Atualiza status da missão."""
        if "mission" not in self.state:
            self.state["mission"] = {}

        for key, value in kwargs.items():
            self.state["mission"][key] = value

        self.save_state()

    def get_mission_summary(self) -> str:
        """Retorna resumo da missão atual."""
        mission = self.state.get("mission", {})
        pipeline = self.state.get("pipeline", {})

        if mission.get("status") == "NOT_STARTED":
            return "Nenhuma missão em andamento."

        return (
            f"Missão {mission.get('id', '?')}: "
            f"Phase {mission.get('phase', '?')}.{mission.get('subphase', '?')}, "
            f"batch {mission.get('batch', '?')}/{mission.get('total_batches', '?')}. "
            f"{pipeline.get('files_processed', 0)} arquivos processados, "
            f"{pipeline.get('insights_extracted', 0)} insights."
        )

    ***REMOVED***==============================
    # SESSION MANAGEMENT
    ***REMOVED***==============================

    def start_voice_session(self):
        """Marca início de uma sessão de voz."""
        if "voice_system" not in self.state:
            self.state["voice_system"] = {}

        self.state["voice_system"]["last_session"] = datetime.now().isoformat()
        self.state["context"]["session_start"] = datetime.now().isoformat()

        self.save_state()

    def increment_interaction(self):
        """Incrementa contador de interações."""
        if "voice_system" not in self.state:
            self.state["voice_system"] = {}

        current = self.state["voice_system"].get("total_interactions", 0)
        self.state["voice_system"]["total_interactions"] = current + 1

        self.save_state()

    ***REMOVED***==============================
    # PENDING ITEMS
    ***REMOVED***==============================

    def add_pending_question(self, question: str):
        """Adiciona uma pergunta pendente."""
        if "pending_questions" not in self.state["context"]:
            self.state["context"]["pending_questions"] = []

        self.state["context"]["pending_questions"].append(question)
        self.save_state()

    def clear_pending_questions(self):
        """Limpa perguntas pendentes."""
        self.state["context"]["pending_questions"] = []
        self.save_state()

    def get_pending_questions(self) -> List[str]:
        """Retorna perguntas pendentes."""
        return self.state.get("context", {}).get("pending_questions", [])


***REMOVED***==============================
# TESTE
***REMOVED***==============================

if __name__ == "__main__":
    print("=" * 60)
    print("MEGA BRAIN CONNECTOR - TESTE")
    print("=" * 60)

    connector = MegaBrainConnector()

    print("\n📊 Estado atual:")
    print(connector.get_mission_summary())

    print("\n📋 Contexto para Claude:")
    print(connector.get_context_for_claude())

    print("\n👥 Agentes disponíveis:")
    agents = connector.get_available_agents()
    for agent in agents[:10]:  # Mostra primeiros 10
        print(f"   - {agent}")
    if len(agents) > 10:
        print(f"   ... e mais {len(agents) - 10} agentes")

    print("\n✅ Connector funcionando!")
    print("=" * 60)
