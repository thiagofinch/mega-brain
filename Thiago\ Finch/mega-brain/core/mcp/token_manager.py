#!/usr/bin/env python3
"""
MercadoLivre Token Manager com Auto-Refresh

Responsabilidades:
1. Armazenar tokens de forma segura (arquivo .json)
2. Auto-refresh antes de expiração (com 5min de buffer)
3. Retry automático com backoff exponencial
4. Logging de rotações de token
5. API simples para obter token válido

Tokens são armazenados em: .claude/mission-control/ML-TOKEN-STATE.json
(gitignored, não entra em .env)
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple
import time

class MercadoLivreTokenManager:
    """Gerencia tokens OAuth de MercadoLivre com auto-refresh"""

    # Locais de armazenamento
    TOKEN_STATE_FILE = Path(__file__).parent.parent.parent / ".claude" / "mission-control" / "ML-TOKEN-STATE.json"
    TOKEN_LOG_FILE = Path(__file__).parent.parent.parent / "logs" / "ml-token-rotations.log"

    # Constantes
    TOKEN_REFRESH_BUFFER = 300  # Refresh 5 min antes de expirar
    API_URL = "https://auth.mercadolibre.com.br/oauth/token"
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self):
        self.client_id = os.getenv("MERCADOLIVRE_CLIENT_ID", "")
        self.client_secret = os.getenv("MERCADOLIVRE_CLIENT_SECRET", "")
        self.redirect_url = os.getenv("MERCADOLIVRE_REDIRECT_URL", "")

        # Criar diretórios se não existirem
        self.TOKEN_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.TOKEN_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Carregar estado de tokens do arquivo"""
        if self.TOKEN_STATE_FILE.exists():
            try:
                with open(self.TOKEN_STATE_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                self._log(f"❌ Erro ao carregar estado: {e}")
                return {}
        return {}

    def _save_state(self) -> None:
        """Persistir estado de tokens no arquivo"""
        try:
            with open(self.TOKEN_STATE_FILE, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self._log(f"❌ Erro ao salvar estado: {e}")

    def _log(self, message: str) -> None:
        """Log de rotações de token"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"

        try:
            with open(self.TOKEN_LOG_FILE, "a") as f:
                f.write(log_entry + "\n")
        except:
            pass  # Silent fail para logging

    def _is_token_expired(self) -> bool:
        """Verificar se token está expirado (com buffer de 5min)"""
        if "expires_at" not in self.state:
            return True

        expires_at = datetime.fromisoformat(self.state["expires_at"])
        buffer_time = datetime.now() + timedelta(seconds=self.TOKEN_REFRESH_BUFFER)

        return buffer_time >= expires_at

    def refresh_token(self, authorization_code: Optional[str] = None) -> Tuple[bool, str]:
        """
        Renovar token via OAuth

        Args:
            authorization_code: Código de autorização (primeira vez) ou None (refresh)

        Returns:
            (sucesso: bool, mensagem: str)
        """
        try:
            if authorization_code:
                # Fluxo de autorização inicial
                payload = {
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": authorization_code,
                    "redirect_uri": self.redirect_url,
                }
                self._log(f"🔄 Iniciando autorização OAuth com código...")
            else:
                # Fluxo de refresh
                if "refresh_token" not in self.state:
                    return False, "❌ Nenhum refresh_token disponível. Execute autorização inicial."

                payload = {
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.state["refresh_token"],
                }
                self._log(f"🔄 Renovando token...")

            # Retry com backoff
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = requests.post(
                        self.API_URL,
                        data=payload,
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()

                        # Atualizar estado
                        self.state["access_token"] = data["access_token"]
                        self.state["refresh_token"] = data.get("refresh_token", self.state.get("refresh_token"))
                        self.state["expires_in"] = data["expires_in"]
                        self.state["expires_at"] = (
                            datetime.now() + timedelta(seconds=data["expires_in"])
                        ).isoformat()
                        self.state["last_refresh"] = datetime.now().isoformat()

                        self._save_state()

                        msg = f"✅ Token renovado com sucesso. Expira em: {self.state['expires_at']}"
                        self._log(msg)
                        return True, msg

                    elif response.status_code == 400:
                        error = response.json().get("error_description", "Unknown error")
                        msg = f"❌ Erro OAuth 400: {error}"
                        self._log(msg)
                        return False, msg

                    else:
                        if attempt < self.MAX_RETRIES - 1:
                            wait_time = self.RETRY_DELAY * (2 ** attempt)
                            self._log(f"⏳ Tentativa {attempt+1}/{self.MAX_RETRIES} falhou. Aguardando {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            msg = f"❌ Falha após {self.MAX_RETRIES} tentativas. Status: {response.status_code}"
                            self._log(msg)
                            return False, msg

                except requests.exceptions.Timeout:
                    if attempt < self.MAX_RETRIES - 1:
                        self._log(f"⏳ Timeout. Tentativa {attempt+1}/{self.MAX_RETRIES}...")
                        time.sleep(self.RETRY_DELAY * (2 ** attempt))
                    else:
                        msg = "❌ Timeout após múltiplas tentativas"
                        self._log(msg)
                        return False, msg

        except Exception as e:
            msg = f"❌ Erro ao renovar token: {str(e)}"
            self._log(msg)
            return False, msg

    def get_valid_token(self) -> str:
        """
        Obter token válido (refresh automático se necessário)

        Returns:
            Token válido ou vazio se falhar
        """
        if not self._is_token_expired():
            # Token ainda válido
            return self.state.get("access_token", "")

        # Token expirado, tentar renovar
        success, msg = self.refresh_token()

        if success:
            return self.state.get("access_token", "")
        else:
            return ""

    def get_status(self) -> Dict:
        """Obter status atual dos tokens"""
        if not self.state:
            return {
                "status": "NOT_INITIALIZED",
                "message": "Nenhum token configurado"
            }

        expires_at = datetime.fromisoformat(self.state.get("expires_at", ""))
        now = datetime.now()
        remaining = expires_at - now

        status = "VALID" if remaining.total_seconds() > 0 else "EXPIRED"

        return {
            "status": status,
            "access_token": self.state.get("access_token", "")[:20] + "...",
            "expires_at": self.state.get("expires_at", ""),
            "expires_in_seconds": max(0, int(remaining.total_seconds())),
            "last_refresh": self.state.get("last_refresh", ""),
            "refresh_token_available": "refresh_token" in self.state
        }

    def authorize_interactive(self) -> Tuple[bool, str]:
        """
        Fluxo interativo de autorização OAuth

        Returns:
            (sucesso: bool, mensagem: str)
        """
        print("\n" + "="*70)
        print("🔐 AUTORIZAÇÃO MERCADOLIVRE OAUTH 2.0")
        print("="*70 + "\n")

        # Passo 1: Gerar URL de autorização
        auth_url = (
            f"https://auth.mercadolibre.com.br/authorization?"
            f"response_type=code&"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_url}"
        )

        print("1️⃣  Acesse este link e faça login com sua conta Hugo Jobs:")
        print(f"\n{auth_url}\n")

        print("2️⃣  Você será redirecionado para uma URL similar a:")
        print("   https://hugojobs.co/?code=AUTHORIZATION_CODE\n")

        # Passo 2: Obter código do usuário
        auth_code = input("3️⃣  Cole o valor de 'code' aqui (ou URL completa): ").strip()

        # Se for URL, extrair code
        if auth_code.startswith("http"):
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(auth_code)
                code_param = parse_qs(parsed.query).get("code", [None])[0]
                if code_param:
                    auth_code = code_param
            except:
                pass

        if not auth_code:
            return False, "❌ Código inválido"

        # Passo 3: Trocar code por token
        print("\n⏳ Trocando código por token...\n")
        success, msg = self.refresh_token(authorization_code=auth_code)

        print(msg + "\n")

        if success:
            status = self.get_status()
            print(f"✅ Token ativo até: {status['expires_at']}")
            print(f"✅ Renovação automática está habilitada\n")

        return success, msg


# Script standalone para autorização
if __name__ == "__main__":
    import sys

    manager = MercadoLivreTokenManager()

    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        # Mostrar status
        status = manager.get_status()
        print(json.dumps(status, indent=2))

    elif len(sys.argv) > 1 and sys.argv[1] == "--refresh":
        # Renovar manualmente
        success, msg = manager.refresh_token()
        print(msg)
        sys.exit(0 if success else 1)

    elif len(sys.argv) > 1 and sys.argv[1] == "--authorize":
        # Autorização interativa
        success, msg = manager.authorize_interactive()
        sys.exit(0 if success else 1)

    else:
        # Verificar e renovar se necessário
        token = manager.get_valid_token()
        if token:
            print(f"✅ Token válido: {token[:20]}...")
        else:
            print("❌ Token inválido. Execute com --authorize para autorizar.")
            sys.exit(1)
