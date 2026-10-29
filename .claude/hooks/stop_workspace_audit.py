#!/usr/bin/env python3
"""
Workspace Audit — Stop Hook (no-op nesta distribuicao)
======================================================
Na instalacao completa, comparava o score de saude do workspace no fim da
sessao com o do inicio. Os validadores de governanca que ele usava
(``engine/governance``) nao fazem parte desta distribuicao publica, entao o
hook ficou como no-op silencioso: consome o stdin, nao imprime nada e sai com
codigo 0. Mantido registrado em ``settings.json`` para nao alterar a fiacao.

Hook Type: Stop
EXIT CODES:
- 0: sempre (nunca interfere no encerramento da sessao)
"""

import sys


def main():
    """Hook entry point."""
    try:
        sys.stdin.read()  # contrato do hook: consumir o stdin
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
