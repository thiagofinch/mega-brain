#!/usr/bin/env python3
"""
Skill Indexer - Hook de SessionStart v2.0

Indexa todas as skills E sub-agents no início de cada sessão.
Executado automaticamente via settings.local.json SessionStart hook.

REGRA #27: Skills e Sub-Agents são indexados automaticamente no início de cada sessão.

v2.0: Suporta tanto skills quanto sub-agents JARVIS
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "hooks"))

try:
    from skill_router import build_index
except ImportError:
    # Fallback se import falhar
    def build_index():
        return {"skills_count": 0, "subagents_count": 0, "error": "skill_router not found"}


def main():
    """Função principal - executa indexação."""
    try:
        index = build_index()
        skills_count = index.get('skills_count', 0)
        subagents_count = index.get('subagents_count', 0)
        keywords_count = len(index.get('keyword_map', {}))

        # Output compacto para não poluir o chat
        # Formato compatível com outros hooks SessionStart
        print(f"Skills: {skills_count} | Sub-Agents: {subagents_count} | Keywords: {keywords_count}")

    except Exception as e:
        # Falha silenciosa para não bloquear sessão
        # Erro é logado mas não impede uso do sistema
        print(f"Skill indexer: {str(e)[:50]}")


if __name__ == "__main__":
    main()
