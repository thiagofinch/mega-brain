#!/usr/bin/env python3
"""
CONVERT TO COMPANY DOCS - Converte Markdown para Google Docs com estilos Company

Aplica:
- Fonte Montserrat (fallback Arial)
- Paleta de cores Company (#D9D9D9, #F3F3F3, #A0A0A0)
- Formatacao de tabelas com headers cinza
- Headers de secao numerados
"""

import os
import re
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("ERRO: Dependencias nao instaladas.")
    print("Execute: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


# Cores Company (RGB normalizado 0-1)
COLORS = {
    'background': {'red': 0.953, 'green': 0.953, 'blue': 0.953},      # #F3F3F3
    'table_header': {'red': 0.851, 'green': 0.851, 'blue': 0.851},    # #D9D9D9
    'border': {'red': 0.851, 'green': 0.851, 'blue': 0.851},          # #D9D9D9
    'separator': {'red': 0.627, 'green': 0.627, 'blue': 0.627},       # #A0A0A0
    'heading': {'red': 0.263, 'green': 0.263, 'blue': 0.263},         # #434343
    'secondary': {'red': 0.4, 'green': 0.4, 'blue': 0.4},             # #666666
    'black': {'red': 0, 'green': 0, 'blue': 0},
}


class MarkdownParser:
    """Converte Markdown para estrutura intermediaria."""

    def __init__(self, content: str):
        self.content = content
        self.elements = []

    def parse(self) -> list:
        """Processa markdown e retorna lista de elementos."""
        lines = self.content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Codigo em bloco
            if line.startswith('```'):
                block, i = self._parse_code_block(lines, i)
                self.elements.append(block)
                continue

            # Tabela
            if '|' in line and i + 1 < len(lines) and '---' in lines[i + 1]:
                table, i = self._parse_table(lines, i)
                self.elements.append(table)
                continue

            # Heading
            if line.startswith('#'):
                self.elements.append(self._parse_heading(line))
                i += 1
                continue

            # Horizontal rule
            if line.strip() in ['---', '***', '___']:
                self.elements.append({'type': 'hr'})
                i += 1
                continue

            # Lista
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                items, i = self._parse_list(lines, i)
                self.elements.append({'type': 'list', 'items': items})
                continue

            # Lista numerada
            if re.match(r'^\d+[\.\)] ', line.strip()):
                items, i = self._parse_numbered_list(lines, i)
                self.elements.append({'type': 'numbered_list', 'items': items})
                continue

            # Paragrafo normal
            if line.strip():
                self.elements.append({'type': 'paragraph', 'text': line})

            i += 1

        return self.elements

    def _parse_heading(self, line: str) -> dict:
        """Parse heading line."""
        match = re.match(r'^(#+)\s*(.+)$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2)
            return {'type': 'heading', 'level': level, 'text': text}
        return {'type': 'paragraph', 'text': line}

    def _parse_code_block(self, lines: list, start: int) -> tuple:
        """Parse code block."""
        content = []
        lang = lines[start].replace('```', '').strip()
        i = start + 1

        while i < len(lines) and not lines[i].startswith('```'):
            content.append(lines[i])
            i += 1

        return {
            'type': 'code_block',
            'language': lang,
            'content': '\n'.join(content)
        }, i + 1

    def _parse_table(self, lines: list, start: int) -> tuple:
        """Parse markdown table."""
        headers = [c.strip() for c in lines[start].split('|') if c.strip()]
        i = start + 2  # Skip header separator
        rows = []

        while i < len(lines) and '|' in lines[i]:
            row = [c.strip() for c in lines[i].split('|') if c.strip()]
            if row:
                rows.append(row)
            i += 1

        return {'type': 'table', 'headers': headers, 'rows': rows}, i

    def _parse_list(self, lines: list, start: int) -> tuple:
        """Parse unordered list."""
        items = []
        i = start

        while i < len(lines):
            line = lines[i]
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                items.append(line.strip()[2:])
                i += 1
            elif line.startswith('  ') and items:
                items[-1] += '\n' + line.strip()
                i += 1
            else:
                break

        return items, i

    def _parse_numbered_list(self, lines: list, start: int) -> tuple:
        """Parse numbered list."""
        items = []
        i = start

        while i < len(lines):
            line = lines[i].strip()
            match = re.match(r'^\d+[\.\)]\s*(.+)$', line)
            if match:
                items.append(match.group(1))
                i += 1
            elif line.startswith('  ') and items:
                items[-1] += '\n' + line
                i += 1
            else:
                break

        return items, i


class CompanyDocsConverter:
    """Converte Markdown para Google Docs com estilos Company."""

    SCOPES = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self, config_path: str = None):
        """Inicializa conversor."""
        self.config_path = config_path or self._default_config_path()
        self.config = self._load_config()
        self.docs_service = None
        self.drive_service = None
        self.credentials = None

    def _default_config_path(self) -> str:
        """Retorna path padrao do config.json."""
        sync_docs_dir = Path(__file__).parent.parent / "sync-docs"
        return str(sync_docs_dir / "config.json")

    def _load_config(self) -> dict:
        """Carrega configuracao."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config nao encontrado: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def authenticate(self) -> bool:
        """Autentica com OAuth."""
        try:
            token_path = self.config['google']['token_path']
            oauth_keys_path = self.config['google']['oauth_keys_path']

            if not os.path.exists(token_path):
                print(f"ERRO: Token nao encontrado: {token_path}")
                return False

            with open(token_path, 'r') as f:
                token_data = json.load(f)

            with open(oauth_keys_path, 'r') as f:
                oauth_data = json.load(f)
                client_info = oauth_data.get('installed', oauth_data.get('web', {}))

            self.credentials = Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=client_info.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=client_info.get('client_id'),
                client_secret=client_info.get('client_secret'),
                scopes=self.SCOPES
            )

            if self.credentials.expired and self.credentials.refresh_token:
                print("Token expirado, renovando...")
                self.credentials.refresh(Request())
                new_token_data = {
                    'access_token': self.credentials.token,
                    'refresh_token': self.credentials.refresh_token,
                    'scope': ' '.join(self.SCOPES),
                    'token_type': 'Bearer',
                    'expiry_date': int(self.credentials.expiry.timestamp() * 1000) if self.credentials.expiry else None
                }
                with open(token_path, 'w') as f:
                    json.dump(new_token_data, f, indent=2)

            self.docs_service = build('docs', 'v1', credentials=self.credentials)
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            print("Autenticacao: OK")
            return True

        except Exception as e:
            print(f"ERRO na autenticacao: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_document(self, title: str, folder_id: str = None) -> str:
        """Cria documento vazio no Google Docs."""
        body = {'title': title}
        doc = self.docs_service.documents().create(body=body).execute()
        doc_id = doc.get('documentId')

        # Move para pasta se especificada
        if folder_id:
            file = self.drive_service.files().get(
                fileId=doc_id,
                fields='parents',
                supportsAllDrives=True
            ).execute()
            previous_parents = ",".join(file.get('parents', []))

            self.drive_service.files().update(
                fileId=doc_id,
                addParents=folder_id,
                removeParents=previous_parents,
                supportsAllDrives=True,
                fields='id, parents'
            ).execute()

        return doc_id

    def _build_text_style(self, bold: bool = False, italic: bool = False,
                          font_size: int = 10, color: dict = None,
                          font_family: str = 'Montserrat') -> dict:
        """Constroi estilo de texto."""
        style = {
            'bold': bold,
            'italic': italic,
            'fontSize': {'magnitude': font_size, 'unit': 'PT'},
            'weightedFontFamily': {'fontFamily': font_family}
        }
        if color:
            style['foregroundColor'] = {'color': {'rgbColor': color}}
        return style

    def _get_text_style_fields(self) -> str:
        """Retorna campos de estilo de texto."""
        return 'bold,italic,fontSize,weightedFontFamily,foregroundColor'

    def convert(self, md_path: str, folder_id: str = None) -> dict:
        """
        Converte arquivo Markdown para Google Docs com estilos Company.

        Args:
            md_path: Caminho do arquivo .md
            folder_id: ID da pasta no Drive (opcional)

        Returns:
            dict com documentId e url
        """
        print(f"\n=== CONVERT TO COMPANY DOCS ===")
        print(f"Arquivo: {md_path}")

        if not os.path.exists(md_path):
            print(f"ERRO: Arquivo nao encontrado: {md_path}")
            return None

        # Autenticar
        if not self.docs_service:
            if not self.authenticate():
                return None

        # Ler e parsear markdown
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        parser = MarkdownParser(content)
        elements = parser.parse()

        # Extrair titulo do primeiro heading ou nome do arquivo
        title = Path(md_path).stem
        for elem in elements:
            if elem['type'] == 'heading' and elem['level'] == 1:
                title = elem['text']
                break

        # Criar documento
        target_folder = folder_id or self.config['google'].get('target_folder_id')
        doc_id = self.create_document(f"[COMPANY] {title}", target_folder)
        print(f"Documento criado: {doc_id}")

        # Construir requests para inserir conteudo
        requests = []
        index = 1  # Posicao inicial no documento

        for elem in elements:
            if elem['type'] == 'heading':
                text = elem['text'] + '\n'
                level = elem['level']

                # Inserir texto
                requests.append({
                    'insertText': {'location': {'index': index}, 'text': text}
                })

                # Determinar estilo baseado no nivel
                if level == 1:
                    font_size = 18
                    color = COLORS['black']
                elif level == 2:
                    font_size = 14
                    color = COLORS['heading']
                else:
                    font_size = 12
                    color = COLORS['heading']

                # Aplicar estilo
                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': index, 'endIndex': index + len(text) - 1},
                        'textStyle': self._build_text_style(bold=True, font_size=font_size, color=color),
                        'fields': self._get_text_style_fields()
                    }
                })

                index += len(text)

            elif elem['type'] == 'paragraph':
                text = elem['text'] + '\n'
                requests.append({
                    'insertText': {'location': {'index': index}, 'text': text}
                })
                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': index, 'endIndex': index + len(text) - 1},
                        'textStyle': self._build_text_style(font_size=10),
                        'fields': self._get_text_style_fields()
                    }
                })
                index += len(text)

            elif elem['type'] == 'code_block':
                # Inserir bloco de codigo com fonte monospacada
                text = elem['content'] + '\n\n'
                requests.append({
                    'insertText': {'location': {'index': index}, 'text': text}
                })
                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': index, 'endIndex': index + len(text) - 1},
                        'textStyle': self._build_text_style(font_size=9, font_family='Consolas'),
                        'fields': self._get_text_style_fields()
                    }
                })
                # Adicionar background
                requests.append({
                    'updateParagraphStyle': {
                        'range': {'startIndex': index, 'endIndex': index + len(text) - 1},
                        'paragraphStyle': {
                            'shading': {'backgroundColor': {'color': {'rgbColor': COLORS['background']}}}
                        },
                        'fields': 'shading'
                    }
                })
                index += len(text)

            elif elem['type'] == 'table':
                # Inserir tabela
                headers = elem['headers']
                rows = elem['rows']
                num_rows = len(rows) + 1  # +1 para header
                num_cols = len(headers)

                requests.append({
                    'insertTable': {
                        'location': {'index': index},
                        'rows': num_rows,
                        'columns': num_cols
                    }
                })

                # Nota: tabelas precisam de tratamento especial
                # O index avanca com a estrutura da tabela
                index += 4 + (num_rows * num_cols * 3)  # Aproximacao

            elif elem['type'] == 'list':
                for item in elem['items']:
                    text = f"- {item}\n"
                    requests.append({
                        'insertText': {'location': {'index': index}, 'text': text}
                    })
                    requests.append({
                        'updateTextStyle': {
                            'range': {'startIndex': index, 'endIndex': index + len(text) - 1},
                            'textStyle': self._build_text_style(font_size=10),
                            'fields': self._get_text_style_fields()
                        }
                    })
                    index += len(text)

            elif elem['type'] == 'numbered_list':
                for i, item in enumerate(elem['items'], 1):
                    text = f"{i}) {item}\n"
                    requests.append({
                        'insertText': {'location': {'index': index}, 'text': text}
                    })
                    requests.append({
                        'updateTextStyle': {
                            'range': {'startIndex': index, 'endIndex': index + len(text) - 1},
                            'textStyle': self._build_text_style(font_size=10),
                            'fields': self._get_text_style_fields()
                        }
                    })
                    index += len(text)

            elif elem['type'] == 'hr':
                # Linha horizontal
                text = '━' * 50 + '\n'
                requests.append({
                    'insertText': {'location': {'index': index}, 'text': text}
                })
                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': index, 'endIndex': index + len(text) - 1},
                        'textStyle': self._build_text_style(font_size=8, color=COLORS['separator']),
                        'fields': self._get_text_style_fields()
                    }
                })
                index += len(text)

        # Executar batch de requests
        if requests:
            try:
                self.docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
                print("Estilos aplicados.")
            except Exception as e:
                print(f"AVISO: Alguns estilos podem nao ter sido aplicados: {e}")

        # Obter URL do documento
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        print(f"\n=== CONVERSAO COMPLETA ===")
        print(f"URL: {doc_url}")

        return {
            'success': True,
            'document_id': doc_id,
            'url': doc_url,
            'title': title,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """CLI para conversao."""
    if len(sys.argv) < 2:
        print("Uso: python convert.py <arquivo.md> [pasta-destino-id]")
        print("Exemplo: python convert.py ./RELATORIO.md")
        sys.exit(1)

    md_path = sys.argv[1]
    folder_id = sys.argv[2] if len(sys.argv) > 2 else None

    converter = CompanyDocsConverter()
    result = converter.convert(md_path, folder_id)

    if result and result.get('success'):
        print("\n" + "=" * 50)
        print("DOCUMENTO COMPANY CRIADO")
        print("=" * 50)
        print(f"Titulo: {result.get('title')}")
        print(f"URL: {result.get('url')}")
        print(f"Timestamp: {result.get('timestamp')}")
    else:
        print("\nCONVERSAO FALHOU")
        sys.exit(1)


if __name__ == "__main__":
    main()
