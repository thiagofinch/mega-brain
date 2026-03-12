#!/usr/bin/env python3
"""
GDRIVE REAUTH - Reautenticacao com escopo de escrita
Execute este script para obter novos tokens com permissao de upload.
"""

import os
import json
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERRO: Dependencias nao instaladas.")
    print("Execute: pip install google-auth-oauthlib")
    exit(1)

# Escopos necessarios para ESCRITA
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]

# Paths
OAUTH_KEYS = Path(r"~/.config/mcp-gdrive/gcp-oauth.keys.json")
TOKEN_FILE = Path(r"~/.config/mcp-gdrive/.gdrive-server-credentials.json")


def main():
    print("=== GOOGLE DRIVE REAUTH ===")
    print(f"OAuth Keys: {OAUTH_KEYS}")
    print(f"Token File: {TOKEN_FILE}")
    print(f"Scopes: {SCOPES}")
    print()

    if not OAUTH_KEYS.exists():
        print(f"ERRO: OAuth keys nao encontradas: {OAUTH_KEYS}")
        return

    # Inicia flow de autenticacao
    flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_KEYS), SCOPES)

    print("Abrindo navegador para autenticacao...")
    print("Autorize o acesso ao Google Drive com permissao de ESCRITA.")
    print()

    # Executa autenticacao local
    credentials = flow.run_local_server(port=8080)

    # Salva novos tokens
    token_data = {
        'access_token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'scope': ' '.join(SCOPES),
        'token_type': 'Bearer',
        'expiry_date': int(credentials.expiry.timestamp() * 1000) if credentials.expiry else None
    }

    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)

    print()
    print("=== AUTENTICACAO CONCLUIDA ===")
    print(f"Token salvo em: {TOKEN_FILE}")
    print(f"Scopes: {SCOPES}")
    print()
    print("Agora voce pode usar /sync-docs para fazer upload!")


if __name__ == "__main__":
    main()
