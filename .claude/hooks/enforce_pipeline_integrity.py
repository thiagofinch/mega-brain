#!/usr/bin/env python3
"""
enforce_pipeline_integrity.py — UserPromptSubmit hook

Bloqueia qualquer tentativa de processar arquivos do inbox
fora do fluxo oficial /ingest → /process-jarvis → Pipeline MCE 8 fases.

Regra criada em 2026-04-20 após dano real ao knowledge base.
"""

import json
import sys

FORBIDDEN_PATTERNS = [
    # Tentar processar inbox com agentes genéricos
    ("general-purpose", "inbox"),
    ("general-purpose", "process"),
    # Tentar fazer rebuild como substituto de ingestão
    ("rebuild_all_indexes", "inbox"),
    # Tentar download + ingestão manual sem process-jarvis
    ("download_fireflies", "process"),
]

PIPELINE_RULE = """
⛔ VIOLAÇÃO DA REGRA DE PIPELINE (CLAUDE.md — NON-NEGOTIABLE)

O fluxo de ingestão É FIXO e INVIOLÁVEL:
  /ingest → /process-inbox → /process-jarvis (8 fases completas)

NÃO é permitido:
  - Substituir /process-jarvis por agentes genéricos
  - Criar scripts alternativos de ingestão
  - "Simular" as fases do pipeline MCE

Use: /process-inbox --all --auto-enrich
"""


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
        prompt = data.get("message", "").lower()

        # Detectar tentativas de bypassar o pipeline
        if "inbox" in prompt and any(
            w in prompt
            for w in [
                "agent",
                "agente",
                "script",
                "download",
                "criar dossier",
                "processar manualmente",
                "batch",
                "lote",
            ]
        ):
            # Verificar se está usando process-jarvis (permitido)
            if "process-jarvis" in prompt or "process-inbox" in prompt or "ingest" in prompt:
                sys.exit(0)  # OK — está usando o fluxo correto

            # Inject warning context (não bloqueia, apenas avisa)
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "UserPromptSubmit",
                            "additionalContext": PIPELINE_RULE,
                        }
                    }
                )
            )
            sys.exit(0)

    except Exception:
        pass  # Fail-open — nunca bloquear por erro no hook

    sys.exit(0)


if __name__ == "__main__":
    main()
