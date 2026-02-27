#!/usr/bin/env python3
"""
ENFORCE PLAN MODE HOOK v1.0.0
=============================

Hook: UserPromptSubmit
Propósito: Detecta quando o usuário solicita modificação de arquivos e
           avisa se Plan Mode não foi ativado.

REGRA #13: PLAN MODE OBRIGATÓRIO PARA MODIFICAÇÃO DE ARQUIVOS
REGRA #29: WARN, NOT BLOCK (avisa, não bloqueia)

Criado: 2026-01-14
Autor: JARVIS
"""

import json
import sys
import re
from datetime import datetime
from pathlib import Path

# Keywords que indicam intenção de modificar arquivos
MODIFYING_KEYWORDS = [
    # Português
    "criar", "crie", "criando", "criação",
    "atualizar", "atualize", "atualizando", "atualização",
    "modificar", "modifique", "modificando", "modificação",
    "implementar", "implemente", "implementando", "implementação",
    "adicionar", "adicione", "adicionando", "adição",
    "remover", "remova", "removendo", "remoção",
    "deletar", "delete", "deletando",
    "refatorar", "refatore", "refatorando", "refatoração",
    "corrigir", "corrija", "corrigindo", "correção",
    "fix", "fixing", "fixed",
    "editar", "edite", "editando", "edição",
    "escrever", "escreva", "escrevendo",
    "gerar", "gere", "gerando", "geração",
    "mudar", "mude", "mudando", "mudança",

    # Inglês
    "create", "creating", "creation",
    "update", "updating",
    "modify", "modifying", "modification",
    "implement", "implementing", "implementation",
    "add", "adding",
    "remove", "removing", "removal",
    "delete", "deleting", "deletion",
    "refactor", "refactoring",
    "edit", "editing",
    "write", "writing",
    "generate", "generating",
    "change", "changing",

    # Comandos específicos
    "novo arquivo", "new file",
    "nova feature", "new feature",
    "novo hook", "new hook",
    "nova skill", "new skill",
    "novo agente", "new agent",
    "bug fix", "bugfix",
]

# Keywords que indicam exceções (não precisa Plan Mode)
EXCEPTION_KEYWORDS = [
    # Leitura/consulta
    "mostrar", "show", "exibir", "display",
    "ler", "read", "leia",
    "buscar", "search", "find", "procurar",
    "verificar", "check", "verify",
    "status", "estado",
    "listar", "list",
    "onde estamos", "where are we",
    "o que é", "what is",
    "como funciona", "how does",
    "explique", "explain",
    "descreva", "describe",

    # Comandos slash (já são skills)
    "/jarvis", "/status", "/save", "/resume",
    "/conclave", "/verify", "/config",
]

# Log file
LOG_FILE = Path(__file__).parent.parent / "mission-control" / "plan_mode_warnings.jsonl"


def check_plan_mode_required(prompt: str) -> dict:
    """
    Analisa o prompt para determinar se Plan Mode é necessário.

    Returns:
        dict com:
        - required: bool (se Plan Mode é necessário)
        - keywords_found: list (keywords de modificação encontradas)
        - exception_found: str|None (exceção que foi encontrada)
        - confidence: str (HIGH, MEDIUM, LOW)
    """
    prompt_lower = prompt.lower()

    # Verificar exceções primeiro
    for exc in EXCEPTION_KEYWORDS:
        if exc in prompt_lower:
            return {
                "required": False,
                "keywords_found": [],
                "exception_found": exc,
                "confidence": "HIGH"
            }

    # Verificar keywords de modificação
    found_keywords = []
    for kw in MODIFYING_KEYWORDS:
        # Usar word boundary para evitar falsos positivos
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, prompt_lower):
            found_keywords.append(kw)

    if not found_keywords:
        return {
            "required": False,
            "keywords_found": [],
            "exception_found": None,
            "confidence": "HIGH"
        }

    # Determinar confiança baseado em quantidade de keywords
    if len(found_keywords) >= 3:
        confidence = "HIGH"
    elif len(found_keywords) >= 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "required": True,
        "keywords_found": found_keywords,
        "exception_found": None,
        "confidence": confidence
    }


def log_warning(prompt: str, analysis: dict):
    """Loga warning para auditoria."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "hook": "enforce_plan_mode",
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "keywords_found": analysis["keywords_found"],
            "confidence": analysis["confidence"],
            "action": "WARNING_ISSUED"
        }

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # Não falhar por erro de log
        pass


def main():
    try:
        # Ler input do hook
        input_data = json.loads(sys.stdin.read())

        # Extrair prompt do usuário
        prompt = input_data.get("prompt", "")

        if not prompt:
            # Sem prompt, não há o que analisar
            print(json.dumps({"continue": True}))
            sys.exit(0)

        # Analisar se Plan Mode é necessário
        analysis = check_plan_mode_required(prompt)

        if not analysis["required"]:
            # Não precisa de Plan Mode
            print(json.dumps({"continue": True}))
            sys.exit(0)

        # Plan Mode é necessário - emitir WARNING (não bloquear)
        # REGRA #29: WARN, NOT BLOCK

        log_warning(prompt, analysis)

        # Construir mensagem de aviso
        warning_msg = (
            f"[PLAN MODE WARNING] Detectada intenção de modificação de arquivos. "
            f"Keywords: {', '.join(analysis['keywords_found'][:5])}. "
            f"Confiança: {analysis['confidence']}. "
            f"REGRA #13 recomenda Plan Mode para modificações. "
            f"Use Shift+Tab 2x para ativar ou digite 'plan mode'."
        )

        # Retornar com aviso (não bloqueia - exit 0)
        print(json.dumps({
            "continue": True,
            "feedback": warning_msg
        }))
        sys.exit(0)

    except json.JSONDecodeError:
        # Input inválido - continuar silenciosamente
        print(json.dumps({"continue": True}))
        sys.exit(0)
    except Exception as e:
        # Erro inesperado - logar e continuar (não bloquear)
        print(json.dumps({
            "continue": True,
            "warning": f"enforce_plan_mode hook error: {str(e)}"
        }))
        sys.exit(0)  # Don't block on internal errors


if __name__ == "__main__":
    main()
