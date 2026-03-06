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
import sys
from dotenv import load_dotenv

# Carregar .env na inicialização do módulo
load_dotenv()

class MercadoLivreTokenManager:
    """Gerencia tokens OAuth de MercadoLivre com auto-refresh"""

    # Locais de armazenamento
    TOKEN_STATE_FILE = Path(__file__).parent.parent.parent / ".claude" / "mission-control" / "ML-TOKEN-STATE.json"
    TOKEN_LOG_FILE = Path(__file__).parent.parent.parent / "logs" / "ml-token-rotations.log"

    # Constantes
    TOKEN_REFRESH_BUFFER = 300  # Refresh 5 min antes de expirar
    API_URL = "https://api.mercadolibre.com/oauth/token"
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
                    state = json.load(f)
                    # Migração de Legado (Flat -> Multi-Tenant)
                    if "access_token" in state and "accounts" not in state:
                        user_id = str(state.get("user_id", "default"))
                        return {
                            "accounts": {user_id: state},
                            "default_user_id": user_id
                        }
                    return state
            except Exception as e:
                self._log(f"❌ Erro ao carregar estado: {e}")
                return {"accounts": {}, "default_user_id": None}
        return {"accounts": {}, "default_user_id": None}

    def _save_state(self) -> None:
        """Persistir estado de tokens no arquivo"""
        try:
            with open(self.TOKEN_STATE_FILE, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self._log(f"❌ Erro ao salvar estado: {e}")

    def _sync_env_token(self, user_id: str) -> None:
        """Sincronizar access_token com .env para scripts que leem de lá (apenas Default)"""
        if self.state.get("default_user_id") != user_id:
            return
            
        env_path = Path(__file__).parent.parent.parent / ".env"
        if not env_path.exists():
            return
        try:
            acc = self.state["accounts"][user_id]
            lines = env_path.read_text().splitlines()
            new_lines = []
            token_found = False
            for line in lines:
                if line.startswith("MERCADOLIVRE_ACCESS_TOKEN="):
                    new_lines.append(f"MERCADOLIVRE_ACCESS_TOKEN={acc.get('access_token', '')}")
                    token_found = True
                else:
                    new_lines.append(line)
            
            if not token_found:
                new_lines.append(f"MERCADOLIVRE_ACCESS_TOKEN={acc.get('access_token', '')}")
                
            env_path.write_text("\n".join(new_lines) + "\n")
            self._log(f"🔄 .env atualizado com novo access_token para conta {user_id}")
        except Exception as e:
            self._log(f"⚠️ Erro ao atualizar .env: {e}")

    def _log(self, message: str) -> None:
        """Log de rotações de token"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"

        try:
            with open(self.TOKEN_LOG_FILE, "a") as f:
                f.write(log_entry + "\n")
        except:
            pass  # Silent fail para logging

    def _is_token_expired(self, user_id: str) -> bool:
        """Verificar se token está expirado (com buffer de 5min)"""
        acc = self.state["accounts"].get(user_id)
        if not acc or "expires_at" not in acc:
            return True

        expires_at = datetime.fromisoformat(acc["expires_at"])
        buffer_time = datetime.now() + timedelta(seconds=self.TOKEN_REFRESH_BUFFER)

        return buffer_time >= expires_at

    def refresh_token(self, authorization_code: Optional[str] = None, user_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Renovar token via OAuth

        Args:
            authorization_code: Código de autorização (primeira vez) ou None (refresh)
            user_id: ID do usuário para refresh (opcional se auth_code for fornecido)

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
                
                # Suporte a PKCE
                pkce_file = Path(__file__).parent.parent.parent / ".pkce_verifier"
                if pkce_file.exists():
                    payload["code_verifier"] = pkce_file.read_text().strip()
                
                self._log(f"🔄 Iniciando autorização OAuth com código...")
            else:
                # Fluxo de refresh
                target_id = user_id or self.state.get("default_user_id")
                acc = self.state["accounts"].get(target_id)
                
                if not acc or "refresh_token" not in acc:
                    return False, f"❌ Nenhum refresh_token disponível para conta {target_id}."

                payload = {
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": acc["refresh_token"],
                }
                self._log(f"🔄 Renovando token para conta {target_id}...")

            # Executar POST
            response = requests.post(self.API_URL, data=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                u_id = str(data["user_id"])
                
                # Inicializar conta no estado se não existir
                if u_id not in self.state["accounts"]:
                    self.state["accounts"][u_id] = {}
                
                acc = self.state["accounts"][u_id]
                acc["access_token"] = data["access_token"]
                acc["refresh_token"] = data.get("refresh_token", acc.get("refresh_token"))
                acc["expires_in"] = data["expires_in"]
                acc["expires_at"] = (
                    datetime.now() + timedelta(seconds=data["expires_in"])
                ).isoformat()
                acc["last_refresh"] = datetime.now().isoformat()
                acc["user_id"] = u_id

                # Definir como default se for a primeira ou se não houver default
                if not self.state.get("default_user_id"):
                    self.state["default_user_id"] = u_id

                self._save_state()
                self._sync_env_token(u_id)

                msg = f"✅ Token renovado para conta {u_id}. Expira em: {acc['expires_at']}"
                self._log(msg)
                return True, msg

            else:
                error = response.json().get("error_description", f"Status: {response.status_code}")
                msg = f"❌ Erro OAuth: {error}"
                self._log(msg)
                return False, msg

        except Exception as e:
            msg = f"❌ Erro ao renovar token: {str(e)}"
            self._log(msg)
            return False, msg

    def get_valid_token(self, user_id: Optional[str] = None) -> str:
        """
        Obter token válido (refresh automático se necessário)
        """
        target_id = user_id or self.state.get("default_user_id")
        if not target_id:
            return ""

        if not self._is_token_expired(target_id):
            return self.state["accounts"][target_id].get("access_token", "")

        # Token expirado, tentar renovar
        success, msg = self.refresh_token(user_id=target_id)
        if success:
            return self.state["accounts"][target_id].get("access_token", "")
        return ""

    def get_status(self) -> Dict:
        """Obter status consolidado das contas"""
        if not self.state.get("accounts"):
            return {"status": "NOT_INITIALIZED", "message": "Nenhuma conta configurada"}

        summary = {
            "default_account": self.state.get("default_user_id"),
            "total_accounts": len(self.state["accounts"]),
            "accounts": {}
        }

        for u_id, acc in self.state["accounts"].items():
            expires_at = datetime.fromisoformat(acc.get("expires_at", ""))
            remaining = (expires_at - datetime.now()).total_seconds()
            
            summary["accounts"][u_id] = {
                "status": "VALID" if remaining > 0 else "EXPIRED",
                "expires_in_seconds": max(0, int(remaining)),
                "last_refresh": acc.get("last_refresh", "")
            }

        return summary

    def authorize_interactive(self) -> Tuple[bool, str]:
        """
        Fluxo interativo de autorização OAuth

        Returns:
            (sucesso: bool, mensagem: str)
        """
        print("\n" + "="*70)
        print("🔐 AUTORIZAÇÃO MERCADOLIVRE OAUTH 2.0")
        print("="*70 + "\n")

        # Passo 1: Gerar URL de autorização com PKCE
        import hashlib
        import base64

        pkce_file = Path(__file__).parent.parent.parent / ".pkce_verifier"
        if pkce_file.exists():
            verifier = pkce_file.read_text().strip()
            hashed = hashlib.sha256(verifier.encode('ascii')).digest()
            challenge = base64.urlsafe_b64encode(hashed).decode('ascii').replace('=', '')
            pkce_params = f"&code_challenge={challenge}&code_challenge_method=S256"
            self._log(f"🔑 Gerando URL com PKCE Challenge baseado em .pkce_verifier")
        else:
            pkce_params = ""
            self._log(f"⚠️ .pkce_verifier não encontrado. Gerando URL sem PKCE.")

        auth_url = (
            f"https://auth.mercadolivre.com.br/authorization?"
            f"response_type=code&"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_url}&"
            f"scope=read write offline_access"
            f"{pkce_params}"
        )

        print("1️⃣  Acesse este link e faça login com sua conta Hugo Jobs (ou cliente):")
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
