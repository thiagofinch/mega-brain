#!/usr/bin/env python3
"""
Hook: MercadoLivre Token Health Check (SessionStart)

Verifica se token está válido e renova automaticamente se necessário.
Executa no início de cada sessão.

Exit codes:
- 0: Token válido ou renovado com sucesso
- 1: Token expirado e falha na renovação (aviso)
- 2: Erro crítico
"""

import sys
import json
from pathlib import Path

# Adicionar core ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core" / "mcp"))

try:
    from token_manager import MercadoLivreTokenManager
except ImportError:
    print(json.dumps({
        "warning": "TokenManager não encontrado",
        "status": "skip"
    }))
    sys.exit(0)

def main():
    try:
        manager = MercadoLivreTokenManager()

        # Verificar status
        status = manager.get_status()

        if status["status"] == "NOT_INITIALIZED":
            print(json.dumps({
                "warning": "MercadoLivre não autorizado",
                "action": "Execute: python3 core/mcp/token_manager.py --authorize",
                "next": "Sessão pode continuar, mas APIs de ML não funcionarão"
            }))
            return 1

        if status["status"] == "VALID":
            print(json.dumps({
                "success": "Token MercadoLivre válido",
                "expires_at": status["expires_at"],
                "remaining_seconds": status["expires_in_seconds"]
            }))
            return 0

        # Token expirado, tentar renovar
        if "refresh_token" in status and status["refresh_token_available"]:
            success, msg = manager.refresh_token()

            if success:
                new_status = manager.get_status()
                print(json.dumps({
                    "success": "Token renovado automaticamente",
                    "expires_at": new_status["expires_at"],
                    "msg": msg
                }))
                return 0
            else:
                print(json.dumps({
                    "warning": "Falha ao renovar token automaticamente",
                    "msg": msg,
                    "action": "Execute: python3 core/mcp/token_manager.py --authorize",
                    "next": "Tente novamente mais tarde"
                }))
                return 1

        # Sem refresh token
        print(json.dumps({
            "error": "Token expirado e sem refresh_token",
            "action": "Execute: python3 core/mcp/token_manager.py --authorize"
        }))
        return 2

    except Exception as e:
        print(json.dumps({
            "error": f"Erro no health check: {str(e)}",
            "type": type(e).__name__
        }))
        return 2

if __name__ == "__main__":
    sys.exit(main())
