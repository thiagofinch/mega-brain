#!/usr/bin/env python3
"""
GDRIVE SYNC - Sincronizacao de arquivos com Google Drive
Skill: /sync-docs

Usa autenticacao OAuth (access_token + refresh_token)
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("ERRO: Dependencias nao instaladas.")
    print("Execute: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


class GDriveSync:
    """Sincronizador de arquivos com Google Drive usando OAuth."""

    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
    ]

    def __init__(self, config_path: str = None):
        """Inicializa com configuracao."""
        self.config_path = config_path or self._default_config_path()
        self.config = self._load_config()
        self.service = None
        self.credentials = None

    def _default_config_path(self) -> str:
        """Retorna path padrao do config.json."""
        skill_dir = Path(__file__).parent
        return str(skill_dir / "config.json")

    def _load_config(self) -> dict:
        """Carrega configuracao do config.json."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config nao encontrado: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def authenticate(self) -> bool:
        """Autentica com OAuth tokens."""
        try:
            token_path = self.config['google']['token_path']
            oauth_keys_path = self.config['google']['oauth_keys_path']

            if not os.path.exists(token_path):
                print(f"ERRO: Token nao encontrado: {token_path}")
                return False

            if not os.path.exists(oauth_keys_path):
                print(f"ERRO: OAuth keys nao encontradas: {oauth_keys_path}")
                return False

            # Carrega tokens
            with open(token_path, 'r') as f:
                token_data = json.load(f)

            # Carrega client info
            with open(oauth_keys_path, 'r') as f:
                oauth_data = json.load(f)
                client_info = oauth_data.get('installed', oauth_data.get('web', {}))

            # Cria credentials
            self.credentials = Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=client_info.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=client_info.get('client_id'),
                client_secret=client_info.get('client_secret'),
                scopes=self.SCOPES
            )

            # Refresh se expirado
            if self.credentials.expired and self.credentials.refresh_token:
                print("Token expirado, renovando...")
                self.credentials.refresh(Request())
                # Salva novo token
                new_token_data = {
                    'access_token': self.credentials.token,
                    'refresh_token': self.credentials.refresh_token,
                    'scope': ' '.join(self.SCOPES),
                    'token_type': 'Bearer',
                    'expiry_date': int(self.credentials.expiry.timestamp() * 1000) if self.credentials.expiry else None
                }
                with open(token_path, 'w') as f:
                    json.dump(new_token_data, f, indent=2)
                print("Token renovado e salvo.")

            self.service = build('drive', 'v3', credentials=self.credentials)
            print("Autenticacao: OK")
            return True

        except Exception as e:
            print(f"ERRO na autenticacao: {e}")
            import traceback
            traceback.print_exc()
            return False

    def find_folder(self, folder_name: str, parent_id: str = None) -> str:
        """Encontra pasta pelo nome."""
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"

        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        files = results.get('files', [])

        if files:
            return files[0]['id']
        return None

    def list_folder_contents(self, folder_id: str) -> list:
        """Lista conteudo de uma pasta."""
        query = f"'{folder_id}' in parents and trashed=false"

        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        return results.get('files', [])

    def create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """Cria pasta no Drive."""
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_id:
            file_metadata['parents'] = [parent_id]

        folder = self.service.files().create(
            body=file_metadata,
            supportsAllDrives=True,
            fields='id'
        ).execute()

        return folder.get('id')

    def get_or_create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """Obtem ou cria pasta."""
        folder_id = self.find_folder(folder_name, parent_id)
        if folder_id:
            return folder_id
        return self.create_folder(folder_name, parent_id)

    def file_exists(self, filename: str, folder_id: str) -> dict:
        """Verifica se arquivo existe na pasta."""
        query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"

        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, webViewLink)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        files = results.get('files', [])

        if files:
            return files[0]
        return None

    def upload_file(self, local_path: str, folder_id: str = None, folder_name: str = None) -> dict:
        """
        Upload de arquivo para o Drive.

        Args:
            local_path: Caminho local do arquivo
            folder_id: ID da pasta destino (tem prioridade)
            folder_name: Nome da pasta destino (usa se folder_id for None)

        Returns:
            dict com id, name, webViewLink ou None se falhar
        """
        if not os.path.exists(local_path):
            print(f"ERRO: Arquivo nao encontrado: {local_path}")
            return None

        # Determina pasta destino
        target_folder_id = folder_id
        if not target_folder_id:
            target_folder_id = self.config['google'].get('target_folder_id')

        # Se folder_name especificado, busca/cria dentro do target
        if folder_name and target_folder_id:
            target_folder_id = self.get_or_create_folder(folder_name, target_folder_id)

        filename = os.path.basename(local_path)

        # Verifica se arquivo ja existe
        existing = None
        if target_folder_id:
            existing = self.file_exists(filename, target_folder_id)

        # Determina mimetype
        if local_path.endswith('.md'):
            mimetype = 'text/markdown'
        elif local_path.endswith('.png'):
            mimetype = 'image/png'
        elif local_path.endswith('.json'):
            mimetype = 'application/json'
        elif local_path.endswith('.pdf'):
            mimetype = 'application/pdf'
        else:
            mimetype = 'application/octet-stream'

        media = MediaFileUpload(local_path, mimetype=mimetype, resumable=True)

        try:
            if existing:
                # Update arquivo existente
                file = self.service.files().update(
                    fileId=existing['id'],
                    media_body=media,
                    supportsAllDrives=True,
                    fields='id, name, webViewLink'
                ).execute()
                print(f"Arquivo atualizado: {filename}")
            else:
                # Upload novo arquivo
                file_metadata = {
                    'name': filename
                }

                if target_folder_id:
                    file_metadata['parents'] = [target_folder_id]

                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    supportsAllDrives=True,
                    fields='id, name, webViewLink'
                ).execute()
                print(f"Arquivo criado: {filename}")

            return file

        except Exception as e:
            print(f"ERRO no upload: {e}")
            import traceback
            traceback.print_exc()
            return None

    def sync(self, local_path: str, folder_name: str = None) -> dict:
        """
        Sincroniza arquivo com Google Drive.

        Args:
            local_path: Caminho local do arquivo
            folder_name: Pasta destino no Drive (ex: "Strategy", "Reports")

        Returns:
            dict com resultado ou None
        """
        print(f"\n=== SYNC GOOGLE DRIVE ===")
        print(f"Arquivo: {local_path}")

        # Autenticar
        if not self.service:
            if not self.authenticate():
                return None

        # Upload
        result = self.upload_file(local_path, folder_name=folder_name)

        if result:
            print(f"URL: {result.get('webViewLink', 'N/A')}")
            return {
                'success': True,
                'file_id': result.get('id'),
                'file_name': result.get('name'),
                'url': result.get('webViewLink'),
                'timestamp': datetime.now().isoformat()
            }

        return {
            'success': False,
            'error': 'Upload falhou',
            'timestamp': datetime.now().isoformat()
        }

    def list_target_folder(self) -> list:
        """Lista conteudo da pasta alvo configurada."""
        if not self.service:
            if not self.authenticate():
                return []

        folder_id = self.config['google'].get('target_folder_id')
        if not folder_id:
            print("ERRO: target_folder_id nao configurado")
            return []

        return self.list_folder_contents(folder_id)


def main():
    """CLI para sync manual."""
    if len(sys.argv) < 2:
        print("Uso: python gdrive_sync.py <caminho-do-arquivo> [pasta-destino]")
        print("Exemplo: python gdrive_sync.py ./REPORT.md Strategy")
        print("\nPara listar pasta alvo: python gdrive_sync.py --list")
        sys.exit(1)

    if sys.argv[1] == '--list':
        syncer = GDriveSync()
        contents = syncer.list_target_folder()
        print("\n=== CONTEUDO DA PASTA ===")
        for item in contents:
            tipo = "PASTA" if item['mimeType'] == 'application/vnd.google-apps.folder' else "ARQUIVO"
            print(f"  [{tipo}] {item['name']}")
        sys.exit(0)

    file_path = sys.argv[1]
    folder_name = sys.argv[2] if len(sys.argv) > 2 else None

    syncer = GDriveSync()
    result = syncer.sync(file_path, folder_name)

    if result and result.get('success'):
        print("\n=== SYNC COMPLETO ===")
        print(f"URL: {result.get('url')}")
        print(f"Timestamp: {result.get('timestamp')}")
    else:
        print("\n=== SYNC FALHOU ===")
        print(f"Erro: {result.get('error') if result else 'Desconhecido'}")
        sys.exit(1)


if __name__ == "__main__":
    main()
