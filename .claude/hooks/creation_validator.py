#!/usr/bin/env python3
"""
Creation Validator - PreToolUse Hook v1.0

Valida criações ANTES de executar, garantindo conformidade com ANTHROPIC-STANDARDS.md.

REGRAS ENFORCED:
- Hooks: DEVEM ter timeout: 30
- Skills: DEVEM ter header com Auto-Trigger, Keywords, Prioridade, Tools
- MCP configs: NUNCA tokens em plaintext
- SDK Sub-Agents: DEVEM ter allowedTools explícito (não ["*"]) e maxTurns

EXIT CODES:
- 0: Passou (validação OK)
- 1: Aviso (continua mas notifica)
- 2: Erro (bloqueia execução)

ERROR HANDLING: fail-CLOSED (2026-02-22 hardening)
  - Internal exceptions -> exit(2) BLOCK (can't validate = block)
  - Log failures -> pass (logging never blocks)

Executado via settings.local.json PreToolUse hook.
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
LOG_FILE = PROJECT_ROOT / "logs" / "creation_validations.jsonl"


class CreationValidator:
    """Validador de criações para conformidade Anthropic."""

    def __init__(self, tool_input: str):
        self.tool_input = tool_input
        self.warnings = []
        self.errors = []
        self.file_path = ""
        self.content = ""

        # Parse tool input
        self._parse_input()

    def _parse_input(self):
        """Extrai file_path e content do tool input."""
        try:
            # Tool input pode ser JSON ou string
            if self.tool_input.startswith('{'):
                data = json.loads(self.tool_input)
                self.file_path = data.get('file_path', '')
                self.content = data.get('content', '')
            else:
                # Tenta extrair de formato string
                self.file_path = self.tool_input
        except json.JSONDecodeError:
            self.file_path = self.tool_input

    def validate(self) -> int:
        """
        Executa validação baseada no tipo de arquivo.

        Returns:
            Exit code: 0 (pass), 1 (warn), 2 (block)
        """
        if not self.file_path:
            return 0  # Não conseguiu determinar arquivo, passa silenciosamente

        path = Path(self.file_path)

        # Detectar tipo de criação
        if self._is_hook_creation(path):
            self._validate_hook()
        elif self._is_skill_creation(path):
            self._validate_skill()
        elif self._is_mcp_creation(path):
            self._validate_mcp()
        elif self._is_sdk_subagent(path):
            self._validate_sdk_subagent()
        else:
            # Arquivo não é de tipo monitorado
            return 0

        # Logar resultado
        self._log_validation()

        # Determinar exit code
        if self.errors:
            self._output_errors()
            return 2  # Block
        elif self.warnings:
            self._output_warnings()
            return 1  # Warn but continue
        else:
            return 0  # Pass

    #=============================
    # DETECÇÃO DE TIPO
    #=============================

    def _is_hook_creation(self, path: Path) -> bool:
        """Detecta se é criação/modificação de hook."""
        # settings.local.json contém hooks
        if path.name == 'settings.local.json':
            return True
        # Scripts em .claude/hooks/
        if '.claude/hooks/' in str(path) and path.suffix == '.py':
            return True
        return False

    def _is_skill_creation(self, path: Path) -> bool:
        """Detecta se é criação/modificação de skill."""
        # SKILL.md em .claude/skills/
        if '.claude/skills/' in str(path) and path.name == 'SKILL.md':
            return True
        # Commands em .claude/commands/
        if '.claude/commands/' in str(path) and path.suffix == '.md':
            return True
        return False

    def _is_mcp_creation(self, path: Path) -> bool:
        """Detecta se é criação/modificação de MCP config."""
        # settings.local.json com mcpServers
        if path.name == 'settings.local.json' and self.content:
            return '"mcpServers"' in self.content
        return False

    def _is_sdk_subagent(self, path: Path) -> bool:
        """Detecta se é criação/modificação de SDK sub-agent."""
        # AGENT.md em .claude/jarvis/sub-agents/
        if '.claude/jarvis/sub-agents/' in str(path):
            if path.name in ('AGENT.md', 'CONFIG.yaml'):
                return True
        return False

    #=============================
    # VALIDAÇÕES
    #=============================

    def _validate_hook(self):
        """
        Valida hook contra ANTHROPIC-STANDARDS.md:
        - DEVE ter timeout: 30
        - DEVE usar exit codes apropriados (não 2>/dev/null || true)
        """
        if not self.content:
            return

        # Validar settings.local.json
        if self.file_path.endswith('settings.local.json'):
            try:
                data = json.loads(self.content)
                hooks = data.get('hooks', {})

                for event, matchers in hooks.items():
                    for matcher in matchers:
                        for hook in matcher.get('hooks', []):
                            # Verificar timeout
                            if 'timeout' not in hook:
                                self.warnings.append(
                                    f"Hook em {event} sem 'timeout'. "
                                    f"Regra Anthropic: todo hook DEVE ter timeout: 30"
                                )

                            # Verificar supressão de erros
                            command = hook.get('command', '')
                            if '2>/dev/null || true' in command:
                                self.warnings.append(
                                    f"Hook em {event} usa '2>/dev/null || true'. "
                                    f"Regra Anthropic: usar exit codes apropriados (0, 1, 2)"
                                )
            except json.JSONDecodeError:
                self.warnings.append("settings.local.json com JSON inválido")

        # Validar script Python de hook
        elif self.file_path.endswith('.py'):
            # Verificar se usa sys.exit com códigos corretos
            if 'sys.exit' not in self.content:
                self.warnings.append(
                    f"Hook Python sem sys.exit(). "
                    f"Regra Anthropic: usar exit code 0 (ok), 1 (warn), 2 (block)"
                )

    def _validate_skill(self):
        """
        Valida skill contra ANTHROPIC-STANDARDS.md:
        - DEVE ter header com Auto-Trigger, Keywords, Prioridade, Tools
        - DEVE ter seção "Quando NÃO Ativar"
        """
        if not self.content:
            return

        required_headers = [
            ('Auto-Trigger:', 'Auto-Trigger'),
            ('Keywords:', 'Keywords'),
            ('Prioridade:', 'Prioridade'),
            ('Tools:', 'Tools')
        ]

        for pattern, name in required_headers:
            if pattern not in self.content:
                self.warnings.append(
                    f"SKILL.md sem '{name}' no header. "
                    f"Regra Anthropic: header obrigatório para auto-routing"
                )

        # Verificar seção "Quando NÃO Ativar"
        if 'Quando NÃO Ativar' not in self.content and 'When NOT to Activate' not in self.content:
            self.warnings.append(
                f"SKILL.md sem seção 'Quando NÃO Ativar'. "
                f"Regra Anthropic: seção obrigatória"
            )

    def _validate_mcp(self):
        """
        Valida MCP config contra ANTHROPIC-STANDARDS.md:
        - NUNCA tokens em plaintext
        - Usar variáveis de ambiente
        """
        if not self.content:
            return

        # Padrões de tokens sensíveis
        sensitive_patterns = [
            (r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', 'JWT token'),
            (r'sk-[A-Za-z0-9]{20,}', 'API key (sk-)'),
            (r'pk_[A-Za-z0-9_]{20,}', 'API key (pk_)'),
            (r'ntn_[A-Za-z0-9]{20,}', 'Notion token'),
            (r'xox[baprs]-[A-Za-z0-9-]+', 'Slack token'),
        ]

        for pattern, token_type in sensitive_patterns:
            if re.search(pattern, self.content):
                self.errors.append(
                    f"CRÍTICO: {token_type} detectado em plaintext! "
                    f"Regra Anthropic: NUNCA tokens em configs. "
                    f"Use variáveis de ambiente em ~/.zshrc"
                )

    def _validate_sdk_subagent(self):
        """
        Valida SDK sub-agent contra ANTHROPIC-STANDARDS.md:
        - DEVE ter allowedTools explícito (não ["*"])
        - DEVE ter maxTurns definido
        - DEVE ter header com Keywords
        """
        if not self.content:
            return

        # Validar AGENT.md
        if self.file_path.endswith('AGENT.md'):
            required_headers = [
                ('Keywords:', 'Keywords'),
                ('allowedTools:', 'allowedTools'),
                ('maxTurns:', 'maxTurns')
            ]

            for pattern, name in required_headers:
                if pattern not in self.content:
                    self.warnings.append(
                        f"Sub-Agent sem '{name}' no header. "
                        f"Regra Anthropic: menor privilégio obrigatório"
                    )

            # Verificar ["*"] proibido
            if '["*"]' in self.content or "['*']" in self.content:
                self.errors.append(
                    f"CRÍTICO: Sub-Agent com allowedTools: [\"*\"]! "
                    f"Regra Anthropic: NUNCA dar acesso total. "
                    f"Use lista explícita de tools."
                )

        # Validar CONFIG.yaml
        elif self.file_path.endswith('CONFIG.yaml'):
            if 'allowedTools:' not in self.content:
                self.warnings.append(
                    f"CONFIG.yaml sem 'allowedTools'. "
                    f"Regra Anthropic: definir tools permitidas"
                )
            if 'maxTurns:' not in self.content:
                self.warnings.append(
                    f"CONFIG.yaml sem 'maxTurns'. "
                    f"Regra Anthropic: definir limite de iterações"
                )

    #=============================
    # OUTPUT
    #=============================

    def _output_warnings(self):
        """Output warnings em formato JSON para Claude processar."""
        output = {
            "status": "warning",
            "file": self.file_path,
            "warnings": self.warnings,
            "message": f"Criação permitida com {len(self.warnings)} aviso(s). Revise conformidade Anthropic."
        }
        print(json.dumps(output, ensure_ascii=False))

    def _output_errors(self):
        """Output errors em formato JSON para Claude processar."""
        output = {
            "status": "blocked",
            "file": self.file_path,
            "errors": self.errors,
            "message": f"Criação BLOQUEADA! {len(self.errors)} violação(ões) crítica(s) de segurança."
        }
        print(json.dumps(output, ensure_ascii=False))

    def _log_validation(self):
        """Loga resultado da validação para auditoria."""
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "file": self.file_path,
                "warnings": self.warnings,
                "errors": self.errors,
                "exit_code": 2 if self.errors else (1 if self.warnings else 0)
            }

            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception:
            pass  # Falha de log não deve bloquear operação


def main():
    """Função principal - entry point do hook."""
    try:
        # Ler input do stdin ou argumento
        if len(sys.argv) > 1:
            tool_input = sys.argv[1]
        else:
            tool_input = sys.stdin.read()

        if not tool_input.strip():
            sys.exit(0)  # Sem input, passa

        validator = CreationValidator(tool_input)
        exit_code = validator.validate()
        sys.exit(exit_code)

    except Exception as e:
        # Fail-CLOSED: internal error = can't validate = BLOCK
        print(json.dumps({
            "status": "blocked",
            "internal_error": str(e),
            "message": "Validador falhou internamente. Operação BLOQUEADA por segurança (fail-closed)."
        }))
        sys.exit(2)


if __name__ == "__main__":
    main()
