#!/usr/bin/env python3
"""
Subagent Tracker - SubagentStop Hook v1.0

Rastreia conclusão de sub-agentes SDK para auditoria e visibilidade.

Executado automaticamente via settings.local.json SubagentStop hook.

ANTROPIC STANDARDS:
- Exit code 0: Sucesso (registrado)
- Exit code 1: Aviso (registrado com warning)
- Exit code 2: Erro (não bloqueia, apenas loga)

Logs em: /logs/subagent_completions.jsonl
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
LOG_FILE = PROJECT_ROOT / "logs" / "subagent_completions.jsonl"


class SubagentTracker:
    """Rastreador de conclusão de sub-agentes."""

    def __init__(self):
        self.agent_id = None
        self.result = None
        self.duration = None
        self.exit_reason = None
        self.metadata = {}

    def parse_environment(self):
        """
        Extrai informações do ambiente do SubagentStop.

        Variáveis disponíveis no hook SubagentStop:
        - AGENT_ID: ID do sub-agente
        - AGENT_RESULT: Resultado/output do agente
        - AGENT_DURATION: Duração em segundos
        - AGENT_EXIT_REASON: Motivo do término
        """
        self.agent_id = os.environ.get('AGENT_ID', 'unknown')
        self.result = os.environ.get('AGENT_RESULT', '')
        self.exit_reason = os.environ.get('AGENT_EXIT_REASON', 'completed')

        # Parse duration
        duration_str = os.environ.get('AGENT_DURATION', '0')
        try:
            self.duration = float(duration_str)
        except ValueError:
            self.duration = 0.0

        # Metadata adicional
        self.metadata = {
            'model': os.environ.get('AGENT_MODEL', 'unknown'),
            'tools_used': os.environ.get('AGENT_TOOLS_USED', ''),
            'turns': os.environ.get('AGENT_TURNS', '0'),
        }

    def track(self) -> int:
        """
        Registra conclusão do sub-agente.

        Returns:
            Exit code: 0 (sucesso), 1 (warning), 2 (erro interno)
        """
        self.parse_environment()

        # Preparar entry de log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "exit_reason": self.exit_reason,
            "duration_seconds": self.duration,
            "result_summary": self._summarize_result(),
            "metadata": self.metadata,
            "status": "completed"
        }

        # Detectar problemas
        warnings = []

        if self.duration > 300:  # > 5 minutos
            warnings.append(f"Sub-agente demorou {self.duration:.1f}s (> 5 min)")

        if self.exit_reason == 'error':
            warnings.append(f"Sub-agente terminou com erro")
            log_entry["status"] = "error"

        if self.exit_reason == 'timeout':
            warnings.append(f"Sub-agente excedeu timeout")
            log_entry["status"] = "timeout"

        # Adicionar warnings ao log
        if warnings:
            log_entry["warnings"] = warnings

        # Salvar log
        try:
            self._write_log(log_entry)
        except Exception as e:
            # Erro de escrita não deve bloquear sistema
            print(json.dumps({
                "status": "error",
                "message": f"Falha ao gravar log: {str(e)}",
                "agent_id": self.agent_id
            }))
            return 0  # Não bloqueia mesmo com erro de log

        # Output para contexto
        if warnings:
            print(json.dumps({
                "status": "warning",
                "agent_id": self.agent_id,
                "warnings": warnings,
                "duration": self.duration
            }))
            return 1  # Warning mas não bloqueia
        else:
            # Sucesso silencioso - apenas log
            return 0

    def _summarize_result(self) -> str:
        """Cria resumo do resultado (max 500 chars)."""
        if not self.result:
            return "[sem resultado]"

        result_str = str(self.result)
        if len(result_str) > 500:
            return result_str[:497] + "..."
        return result_str

    def _write_log(self, entry: dict):
        """Escreve entrada no log JSONL."""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def main():
    """Função principal - entry point do hook."""
    try:
        tracker = SubagentTracker()
        exit_code = tracker.track()
        sys.exit(exit_code)
    except Exception as e:
        # Erro interno não bloqueia sistema
        print(json.dumps({
            "status": "internal_error",
            "error": str(e),
            "message": "Tracker falhou mas operação continua."
        }))
        sys.exit(0)  # Não bloqueia


if __name__ == "__main__":
    main()
