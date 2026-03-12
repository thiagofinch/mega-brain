#!/usr/bin/env python3
"""
DE-PARA COMPLETO: Planilha vs INBOX
====================================

Script que faz o cruzamento completo entre:
- Planilha de controle (fonte da verdade)
- Arquivos no INBOX

Autor: JARVIS
Data: 2026-01-08
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
from collections import defaultdict

# Tentar importar unidecode para normalizar acentos
try:
    from unidecode import unidecode
except ImportError:
    def unidecode(s):
        """Fallback se unidecode nao estiver instalado"""
        return s

# Tentar importar Google Sheets API
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("AVISO: Google API nao disponivel. Instale: pip install google-auth-oauthlib google-api-python-client")

# Configuracoes
PROJECT_ROOT = Path(__file__).parent.parent
INBOX_PATH = PROJECT_ROOT / '00-INBOX'
OUTPUT_PATH = PROJECT_ROOT / '.claude' / 'mission-control'
SPREADSHEET_ID = os.environ.get('MEGA_BRAIN_SPREADSHEET_ID', '')

# OAuth Config (mesma do gdrive_manager.py)
CONFIG_DIR = Path.home() / ".config" / "moga-brain-gdrive"
TOKEN_FILE = CONFIG_DIR / "token.json"
CREDENTIALS_FILE = Path.home() / ".config" / "google-drive-mcp" / "gcp-oauth.keys.json"
# Usa os mesmos escopos do gdrive_manager.py para reutilizar o token
SCOPES = [
    'https://www.googleapis.com/auth/drive',           # Acesso completo ao Drive
    'https://www.googleapis.com/auth/spreadsheets'     # Acesso completo a planilhas
]

# Pastas a ignorar no INBOX
IGNORE_FOLDERS = [
    '_BACKUP', '_DEDUP', '_DUPLICATAS', '_STAGING', '_TEMPLATES',
    '_UNKNOWN', '_LIMPEZA', 'DRIVE-DOWNLOADS'
]

# Extensoes validas
VALID_EXTENSIONS = {'.txt', '.docx', '.pdf', '.md'}

# Mapeamento de cursos para pastas INBOX
COURSE_TO_FOLDER = {
    'FullSales System': 'FULL SALES SYSTEM',
    'Alex Hormozi': 'ALEX HORMOZI (ACQUISITION.COM)',
    'Grupo Silva': 'GRUPO SILVA',
    'Client Accelerator': 'CLIENT ACCELERATOR',
    'EAD de Closer': ['COLE GORDON (CLOSERS.IO)', 'EAD CLOSER (G4)'],
    'G4': 'G4 EDUCACAO (GESTAO 4.0)',
    'Viver de AI': 'VIVER DE AI',
    'Sales Training With Jeremy Haynes': 'JEREMY HAYNES',
    'Inner Circle Mastermind Talks': 'JEREMY HAYNES',
    'Inner Circle Weekly Group Call Recordings': 'JEREMY HAYNES',
    'Ultra High Ticket Closer': 'JEREMY HAYNES',
    'Agency Owners Blueprint Accelerator': 'JEREMY HAYNES',
    'Perfect Cold Video Pitch': 'JEREMY HAYNES',
    'Land Your First Agency Client': 'JEREMY HAYNES',
    '30 Days Challenge': 'JEREMY HAYNES',
    'Scale The Agency': 'JEREMY HAYNES',
    'Marketer Mindset Masterclass': 'JEREMY HAYNES',
    'Jeremy Miner': 'JEREMY MINER (7TH LEVEL)',
    'The Scalable Company': 'THE SCALABLE COMPANY',
    'Programa de Aceleração Fullsales': 'FULL SALES SYSTEM',
}


def get_credentials():
    """Obtem credenciais OAuth"""
    if not GOOGLE_API_AVAILABLE:
        return None

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"ERRO: Arquivo de credenciais nao encontrado: {CREDENTIALS_FILE}")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds


def get_sheets_service():
    """Retorna servico autenticado do Google Sheets"""
    creds = get_credentials()
    if not creds:
        return None
    return build('sheets', 'v4', credentials=creds)


def normalize_name(name: str) -> str:
    """Normaliza nome para matching"""
    if not name:
        return ""

    # Remove extensao
    name = re.sub(r'\.(txt|docx|pdf|md)$', '', name, flags=re.IGNORECASE)

    # Remove tags [XXX-XXXX]
    name = re.sub(r'\[[\w-]+\]', '', name)

    # Remove numeros de ordem no inicio (1. 01. etc)
    name = re.sub(r'^[\d]+\.\s*', '', name)

    # Remove URLs do YouTube
    name = re.sub(r'\s*\[?youtube\.com.*?\]?', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*-\s*YouTube', '', name, flags=re.IGNORECASE)

    # Remove informacoes de resolucao
    name = re.sub(r'\s*\(720p.*?\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(1080p.*?\)', '', name, flags=re.IGNORECASE)

    # Remove datas no formato _20251231162947
    name = re.sub(r'_\d{14}$', '', name)

    # Normaliza acentos
    name = unidecode(name)

    # Remove caracteres especiais
    name = re.sub(r'[^\w\s]', ' ', name)

    # Remove espacos extras
    name = re.sub(r'\s+', ' ', name).strip()

    return name.lower()


def extract_youtube_id(text: str) -> str:
    """Extrai YouTube ID de texto/filename"""
    patterns = [
        r'youtube\.com_watch_v=([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'watch\?v=([a-zA-Z0-9_-]{11})',
        r'\[([a-zA-Z0-9_-]{11})\]$'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def similarity_score(s1: str, s2: str) -> float:
    """Calcula similaridade entre duas strings (0-1)"""
    n1 = normalize_name(s1)
    n2 = normalize_name(s2)

    if not n1 or not n2:
        return 0.0

    return SequenceMatcher(None, n1, n2).ratio()


def get_all_inbox_files() -> list:
    """Retorna todos arquivos validos do INBOX"""
    files = []

    for root, dirs, filenames in os.walk(INBOX_PATH):
        # Filtra pastas a ignorar
        dirs[:] = [d for d in dirs if not any(
            d.startswith(ignore) for ignore in IGNORE_FOLDERS
        )]

        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext in VALID_EXTENSIONS:
                filepath = Path(root) / filename
                rel_path = filepath.relative_to(INBOX_PATH)

                # Extrai fonte do caminho
                parts = str(rel_path).split(os.sep)
                source = parts[0] if len(parts) > 1 else 'ROOT'

                files.append({
                    'path': str(filepath),
                    'rel_path': str(rel_path),
                    'filename': filename,
                    'source': source,
                    'normalized': normalize_name(filename),
                    'youtube_id': extract_youtube_id(filename)
                })

    return files


def read_spreadsheet_all_tabs():
    """Le todas as abas da planilha de controle"""
    service = get_sheets_service()
    if not service:
        print("ERRO: Nao foi possivel conectar ao Google Sheets")
        return None

    try:
        # Primeiro, obtem metadata para listar abas
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()

        sheets = spreadsheet.get('sheets', [])
        tab_names = [s['properties']['title'] for s in sheets]

        print(f"\n  Abas encontradas: {len(tab_names)}")
        for name in tab_names:
            print(f"    - {name}")

        all_items = []

        for tab_name in tab_names:
            # Pula aba de visao geral
            if 'Visão Geral' in tab_name or 'visao geral' in tab_name.lower():
                continue

            try:
                # Le dados da aba - aumentado para 1000 linhas
                result = service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"'{tab_name}'!A1:Z1000"
                ).execute()

                values = result.get('values', [])

                if len(values) < 4:  # Precisa de pelo menos 4 linhas (titulo, header, header2, dados)
                    continue

                # Encontra a linha de header (geralmente linha 3, com MODULO, AULA, etc)
                header_row_idx = -1
                for i, row in enumerate(values[:5]):  # Procura nas primeiras 5 linhas
                    row_str = ' '.join([str(c).upper() for c in row if c])
                    if 'AULA' in row_str or 'MODULO' in row_str:
                        header_row_idx = i
                        break

                if header_row_idx == -1:
                    header_row_idx = 2  # Default: linha 3 (indice 2)

                header = values[header_row_idx] if header_row_idx < len(values) else []

                # Encontra indices das colunas relevantes
                col_indices = {
                    'modulo': -1,
                    'aula': -1,
                    'titulo': -1,
                    'transcricao_visual': -1,  # Visual + Verbal (preferencial)
                    'transcricao': -1,
                    'tag': -1,
                    'youtube': -1,
                    'drive': -1
                }

                for i, col in enumerate(header):
                    col_str = str(col).strip()
                    col_lower = col_str.lower()
                    col_upper = col_str.upper()

                    if col_upper == 'MÓDULO' or col_upper == 'MODULO':
                        col_indices['modulo'] = i
                    elif col_upper == 'AULA':
                        col_indices['aula'] = i
                    elif col_upper in ['ASSUNTO/TEMA', 'ASSUNTO', 'TEMA', 'DESCRIÇÃO', 'DESCRICAO']:
                        col_indices['titulo'] = i
                    elif 'visual' in col_lower and 'verbal' in col_lower:
                        col_indices['transcricao_visual'] = i
                    elif 'transcri' in col_lower:
                        if col_indices['transcricao'] == -1:  # Nao sobrescreve se ja encontrou
                            col_indices['transcricao'] = i
                    elif col_upper == 'TAG':
                        col_indices['tag'] = i
                    elif 'youtube' in col_lower:
                        col_indices['youtube'] = i
                    elif 'drive' in col_lower:
                        col_indices['drive'] = i

                # Se nao encontrou coluna AULA, pode ser coluna B por padrao
                if col_indices['aula'] == -1 and len(header) > 1:
                    col_indices['aula'] = 1  # Coluna B

                # Se nao encontrou TRANSCRICAO, procura coluna G (indice 6)
                if col_indices['transcricao'] == -1 and len(header) > 6:
                    col_indices['transcricao'] = 6

                # Se nao encontrou TAG, procura coluna H (indice 7)
                if col_indices['tag'] == -1 and len(header) > 7:
                    col_indices['tag'] = 7

                # Processa linhas de dados (apos o header)
                tab_items = 0
                for row_idx, row in enumerate(values[header_row_idx + 1:], start=header_row_idx + 2):
                    if not row or all(not cell for cell in row):
                        continue

                    # Pula linhas de separadores/headers repetidos
                    first_cell = str(row[0]).strip() if row else ''
                    if not first_cell:
                        continue
                    if first_cell.startswith('#') or first_cell.startswith('---'):
                        continue
                    if first_cell.upper() in ['AULA', 'VIDEO', 'MODULO', 'MÓDULO', 'NOME', 'TITULO']:
                        continue

                    def get_cell(idx):
                        if idx >= 0 and idx < len(row):
                            val = row[idx]
                            return str(val).strip() if val else ''
                        return ''

                    # Prefere transcricao visual+verbal
                    transcricao = get_cell(col_indices['transcricao_visual'])
                    if not transcricao:
                        transcricao = get_cell(col_indices['transcricao'])

                    # Se nao encontrou transcricao, tenta pegar de colunas com .docx
                    if not transcricao:
                        for i, cell in enumerate(row):
                            if cell and '.docx' in str(cell).lower():
                                transcricao = str(cell).strip()
                                break

                    # Monta titulo - usa coluna AULA como principal
                    aula = get_cell(col_indices['aula'])
                    assunto = get_cell(col_indices['titulo'])

                    # Titulo principal e da coluna AULA
                    titulo = aula if aula else first_cell

                    # Se titulo muito curto, combina com assunto
                    if titulo and len(titulo) < 10 and assunto:
                        titulo = f"{titulo} - {assunto}"

                    if not titulo or len(titulo) < 3:
                        continue

                    # Extrai YouTube ID
                    youtube_url = get_cell(col_indices['youtube'])
                    youtube_id = extract_youtube_id(youtube_url)

                    # Se nao tem ID do YouTube URL, tenta extrair do titulo
                    if not youtube_id:
                        youtube_id = extract_youtube_id(titulo)

                    item = {
                        'source': tab_name,
                        'source_folder': COURSE_TO_FOLDER.get(tab_name, tab_name),
                        'titulo': titulo,
                        'transcricao_filename': transcricao,
                        'tag': get_cell(col_indices['tag']),
                        'youtube_url': youtube_url,
                        'drive_url': get_cell(col_indices['drive']),
                        'row': row_idx,
                        'normalized_titulo': normalize_name(titulo),
                        'normalized_transcricao': normalize_name(transcricao) if transcricao else '',
                        'youtube_id': youtube_id
                    }

                    all_items.append(item)
                    tab_items += 1

                print(f"    {tab_name}: {tab_items} items")

            except Exception as e:
                print(f"    ERRO ao ler '{tab_name}': {e}")
                import traceback
                traceback.print_exc()
                continue

        return all_items

    except Exception as e:
        print(f"ERRO ao ler planilha: {e}")
        import traceback
        traceback.print_exc()
        return None


def find_match(planilha_item: dict, inbox_files: list, matched_paths: set) -> dict:
    """
    Encontra match de um item da planilha no INBOX

    Retorna: {match_type, file_path, confidence, matched_by}
    """
    best_match = None
    best_score = 0
    match_type = 'NO_MATCH'
    matched_by = None

    # Prioridade 1: Match exato por YouTube ID
    if planilha_item.get('youtube_id'):
        for f in inbox_files:
            if f['path'] in matched_paths:
                continue
            if f['youtube_id'] == planilha_item['youtube_id']:
                return {
                    'match_type': 'YOUTUBE_ID_EXACT',
                    'file_path': f['path'],
                    'rel_path': f['rel_path'],
                    'filename': f['filename'],
                    'confidence': 1.0,
                    'matched_by': 'youtube_id'
                }

    # Prioridade 2: Match por nome de arquivo de transcricao
    if planilha_item.get('transcricao_filename'):
        norm_transcricao = planilha_item['normalized_transcricao']
        for f in inbox_files:
            if f['path'] in matched_paths:
                continue
            score = similarity_score(f['filename'], planilha_item['transcricao_filename'])
            if score > best_score:
                best_score = score
                best_match = f
                matched_by = 'transcricao_filename'

    # Prioridade 3: Match por titulo
    norm_titulo = planilha_item['normalized_titulo']
    for f in inbox_files:
        if f['path'] in matched_paths:
            continue
        score = similarity_score(f['filename'], planilha_item['titulo'])
        if score > best_score:
            best_score = score
            best_match = f
            matched_by = 'titulo'

    # Determina tipo de match baseado no score
    if best_match:
        if best_score >= 0.9:
            match_type = 'EXACT'
        elif best_score >= 0.7:
            match_type = 'STRONG'
        elif best_score >= 0.5:
            match_type = 'POSSIBLE'
        else:
            match_type = 'WEAK'

        return {
            'match_type': match_type,
            'file_path': best_match['path'],
            'rel_path': best_match['rel_path'],
            'filename': best_match['filename'],
            'confidence': best_score,
            'matched_by': matched_by
        }

    return {
        'match_type': 'NO_MATCH',
        'file_path': None,
        'rel_path': None,
        'filename': None,
        'confidence': 0.0,
        'matched_by': None
    }


def run_de_para():
    """Executa o DE-PARA completo"""
    if not SPREADSHEET_ID:
        print("ERRO: MEGA_BRAIN_SPREADSHEET_ID nao configurado no ambiente")
        return None

    print("="*70)
    print(" DE-PARA COMPLETO: PLANILHA vs INBOX")
    print("="*70)
    print(f"\n Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Planilha ID: {SPREADSHEET_ID}")
    print(f" INBOX: {INBOX_PATH}")

    # 1. Ler planilha
    print("\n" + "-"*70)
    print(" FASE 1: Lendo planilha de controle...")
    print("-"*70)

    planilha_items = read_spreadsheet_all_tabs()
    if not planilha_items:
        print("ERRO: Nao foi possivel ler a planilha")
        return None

    print(f"\n  Total de items na planilha: {len(planilha_items)}")

    # 2. Listar arquivos no INBOX
    print("\n" + "-"*70)
    print(" FASE 2: Escaneando INBOX...")
    print("-"*70)

    inbox_files = get_all_inbox_files()
    print(f"\n  Total de arquivos no INBOX: {len(inbox_files)}")

    # Agrupa por fonte
    inbox_by_source = defaultdict(list)
    for f in inbox_files:
        inbox_by_source[f['source']].append(f)

    print("\n  Por fonte:")
    for source, files in sorted(inbox_by_source.items()):
        print(f"    {source}: {len(files)}")

    # 3. Fazer matching
    print("\n" + "-"*70)
    print(" FASE 3: Matching planilha vs INBOX...")
    print("-"*70)

    matched = []
    missing = []
    matched_paths = set()

    for item in planilha_items:
        match = find_match(item, inbox_files, matched_paths)

        if match['match_type'] != 'NO_MATCH' and match['confidence'] >= 0.7:
            matched_paths.add(match['file_path'])
            matched.append({
                'planilha': item,
                'inbox': match
            })
        else:
            missing.append({
                'planilha': item,
                'best_match': match if match['confidence'] > 0.3 else None
            })

    # Identificar extras (no INBOX mas nao na planilha)
    extra = []
    for f in inbox_files:
        if f['path'] not in matched_paths:
            extra.append(f)

    # 4. Calcular metricas
    print("\n" + "-"*70)
    print(" RESULTADOS")
    print("-"*70)

    total_planilha = len(planilha_items)
    total_inbox = len(inbox_files)
    total_matched = len(matched)
    total_missing = len(missing)
    total_extra = len(extra)
    match_rate = (total_matched / total_planilha * 100) if total_planilha > 0 else 0

    print(f"""
  PLANILHA (fonte da verdade):
    Total de items: {total_planilha}

  INBOX:
    Total de arquivos: {total_inbox}

  MATCHING:
    Matched: {total_matched} ({match_rate:.1f}%)
    Missing (na planilha, nao no INBOX): {total_missing}
    Extra (no INBOX, nao na planilha): {total_extra}
""")

    # Detalhe por fonte - missing
    if missing:
        print("\n  MISSING por fonte:")
        missing_by_source = defaultdict(list)
        for m in missing:
            source = m['planilha']['source']
            missing_by_source[source].append(m)

        for source, items in sorted(missing_by_source.items(), key=lambda x: -len(x[1])):
            print(f"    {source}: {len(items)}")
            # Mostra primeiros 3
            for item in items[:3]:
                titulo = item['planilha']['titulo'][:50]
                print(f"      - {titulo}...")
            if len(items) > 3:
                print(f"      ... e mais {len(items) - 3}")

    # 5. Gerar relatorio JSON
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'spreadsheet_id': SPREADSHEET_ID,
            'inbox_path': str(INBOX_PATH),
            'script': 'de_para_completo.py'
        },
        'summary': {
            'planilha_total': total_planilha,
            'inbox_total': total_inbox,
            'matched': total_matched,
            'missing': total_missing,
            'extra': total_extra,
            'match_rate': f"{match_rate:.1f}%"
        },
        'by_source': {},
        'matched': [],
        'missing': [],
        'extra': []
    }

    # Agrupa por fonte
    planilha_by_source = defaultdict(int)
    matched_by_source = defaultdict(int)
    missing_by_source_count = defaultdict(int)

    for item in planilha_items:
        planilha_by_source[item['source']] += 1

    for m in matched:
        matched_by_source[m['planilha']['source']] += 1

    for m in missing:
        missing_by_source_count[m['planilha']['source']] += 1

    for source in planilha_by_source:
        report['by_source'][source] = {
            'planilha': planilha_by_source[source],
            'matched': matched_by_source.get(source, 0),
            'missing': missing_by_source_count.get(source, 0)
        }

    # Detalhes matched (simplificado)
    for m in matched:
        report['matched'].append({
            'source': m['planilha']['source'],
            'titulo': m['planilha']['titulo'],
            'inbox_file': m['inbox']['rel_path'],
            'confidence': round(m['inbox']['confidence'], 3),
            'match_type': m['inbox']['match_type']
        })

    # Detalhes missing
    for m in missing:
        item = {
            'source': m['planilha']['source'],
            'titulo': m['planilha']['titulo'],
            'transcricao': m['planilha'].get('transcricao_filename', ''),
            'tag': m['planilha'].get('tag', '')
        }
        if m.get('best_match') and m['best_match'].get('confidence', 0) > 0.3:
            item['possible_match'] = {
                'file': m['best_match']['rel_path'],
                'confidence': round(m['best_match']['confidence'], 3)
            }
        report['missing'].append(item)

    # Detalhes extra (simplificado)
    for f in extra:
        report['extra'].append({
            'source': f['source'],
            'filename': f['filename'],
            'rel_path': f['rel_path']
        })

    # Salva relatorio
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_PATH / 'DE-PARA-DETAILED.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n  Relatorio salvo em: {output_file}")

    # Salva versao resumida legivel
    summary_file = OUTPUT_PATH / 'DE-PARA-SUMMARY.md'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# DE-PARA SUMMARY\n\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## TOTAIS\n\n")
        f.write(f"- Planilha: {total_planilha} items\n")
        f.write(f"- INBOX: {total_inbox} arquivos\n")
        f.write(f"- Match Rate: {match_rate:.1f}%\n\n")
        f.write(f"## STATUS\n\n")
        f.write(f"- MATCHED: {total_matched}\n")
        f.write(f"- MISSING: {total_missing}\n")
        f.write(f"- EXTRA: {total_extra}\n\n")
        f.write(f"## POR FONTE\n\n")
        for source, data in sorted(report['by_source'].items()):
            status = 'OK' if data['missing'] == 0 else f"{data['missing']} faltando"
            f.write(f"- {source}: {data['matched']}/{data['planilha']} ({status})\n")

        if missing:
            f.write(f"\n## TOP FALTANTES\n\n")
            for source, items in sorted(missing_by_source.items(), key=lambda x: -len(x[1]))[:5]:
                f.write(f"\n### {source} ({len(items)} faltando)\n\n")
                for item in items[:10]:
                    titulo = item['planilha']['titulo']
                    f.write(f"- {titulo}\n")
                if len(items) > 10:
                    f.write(f"- ... e mais {len(items) - 10}\n")

    print(f"  Summary salvo em: {summary_file}")

    print("\n" + "="*70)
    print(" DE-PARA COMPLETO")
    print("="*70)

    return report


def main():
    """Funcao principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description='DE-PARA Completo: Planilha vs INBOX',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python de_para_completo.py                    # Executa analise completa
  python de_para_completo.py --json             # Mostra resumo em JSON
  python de_para_completo.py --missing-only     # Lista apenas arquivos faltantes
  python de_para_completo.py --extra-only       # Lista apenas arquivos extras
  python de_para_completo.py --source "Jeremy"  # Filtra por fonte
        """
    )
    parser.add_argument('--json', action='store_true', help='Exibe resultado em JSON')
    parser.add_argument('--missing-only', action='store_true', help='Exibe apenas arquivos faltantes')
    parser.add_argument('--extra-only', action='store_true', help='Exibe apenas arquivos extras')
    parser.add_argument('--source', type=str, help='Filtra por fonte (parcial, case insensitive)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verboso')

    args = parser.parse_args()

    report = run_de_para()

    if not report:
        sys.exit(1)

    # Filtra por fonte se especificado
    if args.source:
        source_filter = args.source.lower()
        report['missing'] = [m for m in report['missing'] if source_filter in m['source'].lower()]
        report['extra'] = [e for e in report['extra'] if source_filter in e['source'].lower()]
        report['matched'] = [m for m in report['matched'] if source_filter in m['source'].lower()]

    if args.json:
        print("\n" + json.dumps(report['summary'], indent=2))

    if args.missing_only:
        print("\n" + "="*70)
        print(" ARQUIVOS FALTANTES (na planilha, nao no INBOX)")
        print("="*70 + "\n")

        # Agrupa por fonte
        by_source = defaultdict(list)
        for m in report['missing']:
            by_source[m['source']].append(m)

        for source, items in sorted(by_source.items(), key=lambda x: -len(x[1])):
            print(f"\n[{source}] - {len(items)} arquivos\n")
            for item in items:
                transcricao = item.get('transcricao', '')[:50] if item.get('transcricao') else ''
                print(f"  - {item['titulo'][:60]}")
                if transcricao and args.verbose:
                    print(f"    Transcricao: {transcricao}")

    if args.extra_only:
        print("\n" + "="*70)
        print(" ARQUIVOS EXTRAS (no INBOX, nao na planilha)")
        print("="*70 + "\n")

        # Agrupa por fonte
        by_source = defaultdict(list)
        for e in report['extra']:
            by_source[e['source']].append(e)

        for source, items in sorted(by_source.items(), key=lambda x: -len(x[1])):
            print(f"\n[{source}] - {len(items)} arquivos\n")
            for item in items[:20]:  # Limita a 20 por fonte
                print(f"  - {item['filename'][:70]}")
            if len(items) > 20:
                print(f"  ... e mais {len(items) - 20} arquivos")


if __name__ == '__main__':
    main()
