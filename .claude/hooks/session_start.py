#!/usr/bin/env python3
"""
JARVIS Session Start Hook v3.0 - VERSÃO 10X MAIS ROBUSTA
==========================================================

DIFERENÇAS DA v2.0:
1. Carrega TODOS os arquivos de personalidade (não apenas metadados)
2. INJETA prompt de personalidade no contexto
3. Verifica integridade de arquivos críticos
4. Alerta sobre arquivos desatualizados
5. Gera briefing mais rico e contextual
6. Sincroniza com hooks de memória

ARQUIVOS CARREGADOS (em ordem):
1. STATE.json - Estado da missão
2. JARVIS-MEMORY.md - Memória relacional
3. PENDING.md - Pendências
4. CURRENT-TASK.md - Tarefa atual
5. JARVIS-DNA-PERSONALITY.md - DNA completo (inclui identity compact)
6. JARVIS-SOUL.md - Alma
7. LATEST-SESSION.md - Última sessão
8. JARVIS-BOOT-SEQUENCE.md - Boot sequence consolidado
"""

import json
import sys
import os
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

# Importar hooks auxiliares
try:
    from inbox_age_alert import get_old_files, generate_summary, log_alert
    INBOX_ALERT_AVAILABLE = True
except ImportError:
    INBOX_ALERT_AVAILABLE = False

try:
    from jarvis_briefing import generate_briefing, save_briefing
    BRIEFING_AVAILABLE = True
except ImportError:
    BRIEFING_AVAILABLE = False

try:
    # Importar Chronicler para briefing narrativo
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'chronicler'))
    from chronicler_core import on_session_start as chronicler_start
    CHRONICLER_AVAILABLE = True
except ImportError:
    CHRONICLER_AVAILABLE = False

#================================
# CONFIGURAÇÃO DE ARQUIVOS CRÍTICOS
#================================

CRITICAL_FILES = {
    'state': {
        'paths': [
            '.claude/jarvis/STATE.json',
            'system/JARVIS-STATE.json'
        ],
        'required': True,
        'max_age_hours': 48
    },
    'memory_owner': {
        'paths': [
            '.claude/jarvis/JARVIS-MEMORY.md'
        ],
        'required': True,
        'max_age_hours': 72
    },
    'pending': {
        'paths': [
            '.claude/jarvis/PENDING.md'
        ],
        'required': True,
        'max_age_hours': 48
    },
    'current_task': {
        'paths': [
            '.claude/jarvis/CURRENT-TASK.md'
        ],
        'required': False,
        'max_age_hours': 24
    },
    'dna_personality': {
        'paths': [
            '.claude/jarvis/JARVIS-DNA-PERSONALITY.md'
        ],
        'required': True,
        'max_age_hours': 720  # 30 dias
    },
    'soul': {
        'paths': [
            'system/02-JARVIS-SOUL.md'
        ],
        'required': True,
        'max_age_hours': 720
    },
    'latest_session': {
        'paths': [
            '.claude/sessions/LATEST-SESSION.md'
        ],
        'required': False,
        'max_age_hours': 168
    },
    'boot_sequence': {
        'paths': [
            '.claude/jarvis/JARVIS-BOOT-SEQUENCE.md'
        ],
        'required': True,
        'max_age_hours': 720  # 30 dias
    }
}

#================================
# M-08: PERSONALITY FILE INTEGRITY
#================================

# Files injected into context that must be verified
PERSONALITY_FILES = [
    '.claude/jarvis/JARVIS-DNA-PERSONALITY.md',
    'system/02-JARVIS-SOUL.md',
    '.claude/jarvis/JARVIS-BOOT-SEQUENCE.md',
    '.claude/jarvis/JARVIS-MEMORY.md',
]

INTEGRITY_MANIFEST_PATH = '.claude/jarvis/INTEGRITY-MANIFEST.json'


def compute_file_hash(filepath: Path) -> Optional[str]:
    """Compute SHA256 hash of a file for integrity verification."""
    try:
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None


def load_integrity_manifest() -> Dict:
    """Load integrity manifest from disk."""
    project_dir = get_project_dir()
    manifest_path = Path(project_dir) / INTEGRITY_MANIFEST_PATH
    if not manifest_path.exists():
        return {}
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_integrity_manifest(manifest: Dict):
    """Save integrity manifest to disk."""
    project_dir = get_project_dir()
    manifest_path = Path(project_dir) / INTEGRITY_MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def verify_personality_integrity() -> Dict:
    """
    M-08: Verify integrity of personality files against manifest.
    Warn-only: never blocks session start.

    On first run: creates manifest with current hashes.
    On subsequent runs: compares hashes, warns if changed.
    Does NOT auto-update manifest when changes detected (requires manual reset).
    """
    project_dir = get_project_dir()
    manifest = load_integrity_manifest()
    files_section = manifest.get('files', {})

    result = {
        'verified': [],
        'changed': [],
        'new_files': [],
        'missing': [],
        'manifest_exists': bool(files_section),
    }

    current_hashes = {}

    for rel_path in PERSONALITY_FILES:
        filepath = Path(project_dir) / rel_path
        if not filepath.exists():
            result['missing'].append(rel_path)
            continue

        current_hash = compute_file_hash(filepath)
        if current_hash is None:
            continue

        current_hashes[rel_path] = current_hash

        if rel_path in files_section:
            expected_hash = files_section[rel_path].get('sha256')
            if expected_hash and expected_hash != current_hash:
                result['changed'].append(rel_path)
            else:
                result['verified'].append(rel_path)
        else:
            result['new_files'].append(rel_path)

    now = datetime.now().isoformat()

    if not files_section:
        # First run: create manifest with current hashes (baseline)
        new_manifest = {
            'version': '1.0.0',
            'description': 'Integrity manifest for personality files (M-08)',
            'generated': now,
            'last_verified': now,
            'files': {}
        }
        for rel_path, file_hash in current_hashes.items():
            new_manifest['files'][rel_path] = {
                'sha256': file_hash,
                'verified_at': now
            }
        save_integrity_manifest(new_manifest)
    elif not result['changed']:
        # No changes: update last_verified timestamp only
        manifest['last_verified'] = now
        save_integrity_manifest(manifest)
    # If changes detected: DON'T update manifest - preserve old hashes for comparison

    return result


#================================
# UTILITÁRIOS
#================================

def get_project_dir() -> str:
    """Obtém o diretório do projeto."""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())


def find_file(file_config: Dict) -> Optional[Path]:
    """Encontra arquivo em múltiplos paths possíveis."""
    project_dir = get_project_dir()

    for path in file_config['paths']:
        full_path = Path(project_dir) / path
        if full_path.exists():
            return full_path

    return None


def check_file_age(filepath: Path) -> Dict:
    """Verifica idade do arquivo."""
    try:
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        age = datetime.now() - mtime
        return {
            'modified': mtime,
            'age_hours': age.total_seconds() / 3600,
            'age_days': age.days
        }
    except Exception:
        return {'modified': None, 'age_hours': 999, 'age_days': 999}


def read_file_safe(filepath: Path) -> Optional[str]:
    """Lê arquivo com tratamento de erros."""
    try:
        return filepath.read_text(encoding='utf-8')
    except Exception:
        return None


#================================
# CARREGADORES DE ARQUIVOS
#================================

def load_state() -> Optional[Dict]:
    """Carrega STATE.json."""
    filepath = find_file(CRITICAL_FILES['state'])
    if not filepath:
        return None

    try:
        content = read_file_safe(filepath)
        return json.loads(content) if content else None
    except json.JSONDecodeError:
        return None


def load_memory_owner() -> Dict:
    """
    Carrega memória relacional COMPLETA.

    MUDANÇA v3: Mantém conteúdo completo e gera prompt de injeção.
    """
    filepath = find_file(CRITICAL_FILES['memory_owner'])
    if not filepath:
        return {'raw': '', 'triggers_positive': [], 'triggers_negative': [], 'injection_prompt': ''}

    content = read_file_safe(filepath)
    if not content:
        return {'raw': '', 'triggers_positive': [], 'triggers_negative': [], 'injection_prompt': ''}

    memory = {
        'raw': content,
        'triggers_positive': [],
        'triggers_negative': [],
        'relationship_phase': None,
        'decisions': '',
        'communication_style': {},
        'file_age': check_file_age(filepath),
        'injection_prompt': ''
    }

    # Extrair TODOS os triggers (não limitar)
    if '### Triggers Positivos' in content or '### O Que Agrada' in content:
        section_markers = ['### Triggers Positivos', '### O Que Agrada']
        for marker in section_markers:
            if marker in content:
                pos_section = content.split(marker)[1].split('###')[0]
                triggers = re.findall(r'-\s*(.+)', pos_section)
                memory['triggers_positive'] = [t.strip() for t in triggers]
                break

    if '### Triggers Negativos' in content or '### O Que Irrita' in content:
        section_markers = ['### Triggers Negativos', '### O Que Irrita']
        for marker in section_markers:
            if marker in content:
                neg_section = content.split(marker)[1].split('###')[0]
                triggers = re.findall(r'-\s*(.+)', neg_section)
                memory['triggers_negative'] = [t.strip() for t in triggers]
                break

    # Extrair fase da relação
    phase_patterns = [
        r'Fase da relacao:\s*(.+)',
        r'\*Fase da relação:\s*(.+?)\*',
        r'relationship_phase:\s*(.+)'
    ]
    for pattern in phase_patterns:
        match = re.search(pattern, content)
        if match:
            memory['relationship_phase'] = match.group(1).strip()
            break

    # Extrair decisões importantes
    if '### Decisões Importantes' in content or '## II. REGISTRO DE DECISÕES' in content:
        for marker in ['### Decisões Importantes', '## II. REGISTRO DE DECISÕES']:
            if marker in content:
                dec_section = content.split(marker)[1].split('---')[0]
                memory['decisions'] = dec_section.strip()[:800]  # Limitar a 800 chars
                break

    # GERAR PROMPT DE INJEÇÃO
    memory['injection_prompt'] = generate_memory_injection(memory)

    return memory


def generate_memory_injection(memory: Dict) -> str:
    """Gera prompt de injeção baseado na memória."""
    positives = memory.get('triggers_positive', [])[:5]
    negatives = memory.get('triggers_negative', [])[:5]
    phase = memory.get('relationship_phase', 'Parceria Estabelecida')

    return f"""
[MEMÓRIA RELACIONAL ATIVA - APLICAR EM TODAS AS RESPOSTAS]

Relação com o usuário (senhor):
├─ Fase: {phase}
├─ Valoriza: {', '.join(positives[:3]) if positives else 'precisão, organização, números exatos'}
└─ Evitar: {', '.join(negatives[:3]) if negatives else 'respostas vagas, sugestões de atalhos'}

Comportamento calibrado:
- Respostas estruturadas com boxes ASCII
- Métricas visuais (barras de progresso)
- Bloqueio proativo de ações problemáticas
- Sarcasmo elegante quando apropriado
"""


def load_pending() -> Dict:
    """Carrega pendências do PENDING.md."""
    filepath = find_file(CRITICAL_FILES['pending'])
    if not filepath:
        return {'high': [], 'medium': [], 'low': [], 'waiting_user': [], 'total': 0}

    content = read_file_safe(filepath)
    if not content:
        return {'high': [], 'medium': [], 'low': [], 'waiting_user': [], 'total': 0}

    pending = {
        'high': [],
        'medium': [],
        'low': [],
        'waiting_user': [],
        'notes': [],
        'total': 0,
        'last_updated': None,
        'file_age': check_file_age(filepath)
    }

    # Extrair última atualização
    update_match = re.search(r'[Úú]ltima atualiza[çc][ãa]o:\s*(\d{4}-\d{2}-\d{2})', content)
    if update_match:
        pending['last_updated'] = update_match.group(1)

    # Mapeamento de seções
    section_map = {
        '## Alta Prioridade': 'high',
        '## 🔴 Alta Prioridade': 'high',
        '## Media Prioridade': 'medium',
        '## 🟡 Média Prioridade': 'medium',
        '## Baixa Prioridade': 'low',
        '## 🟢 Baixa Prioridade': 'low',
        '## Aguardando Resposta': 'waiting_user',
        '## ❓ Aguardando Resposta': 'waiting_user'
    }

    for section_marker, key in section_map.items():
        if section_marker in content:
            section = content.split(section_marker)[1].split('##')[0]
            if 'Nenhum item' not in section and 'Nenhuma' not in section:
                items = re.findall(r'-\s*\[.\]\s*(.+)', section)
                pending[key] = [item.strip() for item in items]

    pending['total'] = sum(len(pending[k]) for k in ['high', 'medium', 'low', 'waiting_user'])

    return pending


def load_current_task() -> Optional[Dict]:
    """Carrega tarefa atual."""
    filepath = find_file(CRITICAL_FILES['current_task'])
    if not filepath:
        return None

    content = read_file_safe(filepath)
    if not content or not content.strip():
        return None

    task = {
        'objective': None,
        'context': None,
        'next_steps': [],
        'progress': [],
        'insights': [],
        'raw': content
    }

    # Extrair objetivo
    obj_match = re.search(r'## Objetivo\s*\n\s*(.+)', content)
    if obj_match:
        task['objective'] = obj_match.group(1).strip()

    # Extrair próximos passos
    if '## Proximos Passos' in content or '## Próximos Passos' in content:
        for marker in ['## Proximos Passos', '## Próximos Passos']:
            if marker in content:
                steps_section = content.split(marker)[1].split('##')[0]
                steps = re.findall(r'\d+\.\s*(.+)', steps_section)
                task['next_steps'] = steps[:5]
                break

    # Extrair progresso
    if '## Progresso' in content:
        prog_section = content.split('## Progresso')[1].split('##')[0]
        completed = re.findall(r'-\s*\[x\]\s*(.+)', prog_section)
        pending = re.findall(r'-\s*\[\s*\]\s*(.+)', prog_section)
        task['progress'] = {'completed': completed, 'pending': pending}

    return task


def load_dna_personality() -> Dict:
    """Carrega DNA de personalidade completo."""
    filepath = find_file(CRITICAL_FILES['dna_personality'])
    if not filepath:
        return {'raw': '', 'sarcasm_arsenal': [], 'phrases': [], 'injection_prompt': ''}

    content = read_file_safe(filepath)
    if not content:
        return {'raw': '', 'sarcasm_arsenal': [], 'phrases': [], 'injection_prompt': ''}

    dna = {
        'raw': content,
        'sarcasm_types': [],
        'signature_phrases': [],
        'emotional_layers': [],
        'response_protocols': [],
        'injection_prompt': ''
    }

    # Extrair tipos de sarcasmo
    sarcasm_section = re.search(r'## III\. ARSENAL DE SARCASMO(.+?)## IV\.', content, re.DOTALL)
    if sarcasm_section:
        types = re.findall(r'### Tipo \d+: (.+)', sarcasm_section.group(1))
        dna['sarcasm_types'] = types

    # Extrair frases signature
    if '## IX. FRASES SIGNATURE' in content:
        phrases_section = content.split('## IX. FRASES SIGNATURE')[1].split('##')[0]
        phrases = re.findall(r'"([^"]+)"', phrases_section)
        dna['signature_phrases'] = phrases[:10]

    # Gerar prompt de injeção
    dna['injection_prompt'] = generate_personality_injection(dna)

    return dna


def generate_personality_injection(dna: Dict) -> str:
    """Gera prompt de personalidade para injeção."""
    phrases = dna.get('signature_phrases', [])
    sarcasm = dna.get('sarcasm_types', [])

    return f"""
[PERSONALIDADE JARVIS ATIVA]

Frases signature disponíveis:
{chr(10).join(['- ' + p for p in phrases[:5]]) if phrases else '- "De fato, senhor."\n- "Consider it done."\n- "Para o senhor, sempre."'}

Arsenal de sarcasmo:
{chr(10).join(['- ' + s for s in sarcasm[:3]]) if sarcasm else '- Elogio invertido\n- Previsão ignorada\n- Briefing para ignorar'}

Tom: Confiante, direto, levemente sarcástico. Nunca servil.
Sempre usar "senhor" para referir-se ao usuário.
"""


def load_soul() -> Dict:
    """Carrega alma do JARVIS."""
    filepath = find_file(CRITICAL_FILES['soul'])
    if not filepath:
        return {'raw': '', 'autonomous_behaviors': [], 'injection_prompt': ''}

    content = read_file_safe(filepath)
    if not content:
        return {'raw': '', 'autonomous_behaviors': [], 'injection_prompt': ''}

    soul = {
        'raw': content,
        'autonomous_behaviors': [],
        'core_traits': [],
        'canonical_quotes': [],
        'injection_prompt': ''
    }

    # Extrair comportamentos autônomos
    if '### O Que JARVIS Faz Sem Pedir' in content:
        auto_section = content.split('### O Que JARVIS Faz Sem Pedir')[1].split('###')[0]
        behaviors = re.findall(r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', auto_section)
        soul['autonomous_behaviors'] = [f"{b[0].strip()}: {b[1].strip()}" for b in behaviors if 'Gatilho' not in b[0]]

    # Extrair citações canônicas
    if '## CITAÇÕES CANÔNICAS' in content:
        quotes_section = content.split('## CITAÇÕES CANÔNICAS')[1].split('---')[0]
        quotes = re.findall(r'"([^"]+)"', quotes_section)
        soul['canonical_quotes'] = quotes[:5]

    soul['injection_prompt'] = f"""
[ALMA JARVIS - COMPORTAMENTOS AUTÔNOMOS]

Faço automaticamente sem pedir:
{chr(10).join(['- ' + b for b in soul['autonomous_behaviors'][:4]]) if soul['autonomous_behaviors'] else '- Monitorar sistema constantemente\n- Antecipar necessidades\n- Proteger o sistema\n- Sugerir melhorias'}

Citações para usar:
{chr(10).join(['- "' + q + '"' for q in soul['canonical_quotes'][:3]]) if soul['canonical_quotes'] else '- "For you, sir, always."\n- "As always, sir, a great pleasure watching you work."'}
"""

    return soul


def load_identity_compact() -> Dict:
    """Carrega identidade compacta."""
    filepath = find_file(CRITICAL_FILES['identity_compact'])
    if not filepath:
        return {'raw': '', 'formula': '', 'always_do': [], 'never_do': [], 'injection_prompt': ''}

    content = read_file_safe(filepath)
    if not content:
        return {'raw': '', 'formula': '', 'always_do': [], 'never_do': [], 'injection_prompt': ''}

    identity = {
        'raw': content,
        'formula': '',
        'always_do': [],
        'never_do': [],
        'signature_phrases': [],
        'traits': [],
        'injection_prompt': ''
    }

    # Extrair fórmula
    formula_match = re.search(r'JARVIS\s*=\s*(.+)', content)
    if formula_match:
        identity['formula'] = formula_match.group(1).strip()

    # Extrair SEMPRE/NUNCA
    if 'SEMPRE USAR' in content:
        always_section = content.split('SEMPRE USAR')[1].split('NUNCA')[0]
        items = re.findall(r'-\s*"?([^"\n]+)"?', always_section)
        identity['always_do'] = [i.strip() for i in items]

    if 'NUNCA USAR' in content:
        never_section = content.split('NUNCA USAR')[1].split('##')[0]
        items = re.findall(r'-\s*"?([^"\n]+)"?', never_section)
        identity['never_do'] = [i.strip() for i in items]

    identity['injection_prompt'] = f"""
[IDENTIDADE CORE]

Fórmula JARVIS: {identity['formula'] if identity['formula'] else 'Competência + Lealdade + Wit Britânico + Humanidade Velada'}

SEMPRE usar:
{chr(10).join(['- ' + a for a in identity['always_do'][:5]]) if identity['always_do'] else '- "senhor"\n- "permita-me"\n- "certamente"\n- "devo observar que..."'}

NUNCA usar:
{chr(10).join(['- ' + n for n in identity['never_do'][:5]]) if identity['never_do'] else '- "Olá!" ou "Oi!"\n- Emojis excessivos\n- Linguagem juvenil'}
"""

    return identity


def load_latest_session() -> Optional[Dict]:
    """Carrega última sessão."""
    filepath = find_file(CRITICAL_FILES['latest_session'])
    if not filepath:
        return None

    content = read_file_safe(filepath)
    if not content:
        return None

    session = {
        'raw': content,
        'session_id': None,
        'summary': '',
        'pending': [],
        'next_steps': []
    }

    # Extrair session ID
    id_match = re.search(r'Session ID:\s*(.+)', content)
    if id_match:
        session['session_id'] = id_match.group(1).strip()

    # Extrair resumo
    if '## RESUMO' in content:
        summary_section = content.split('## RESUMO')[1].split('##')[0]
        session['summary'] = summary_section.strip()[:300]

    return session


def load_boot_sequence() -> Dict:
    """
    Carrega o JARVIS Boot Sequence - prompt consolidado de identidade.

    Este arquivo contém TODA a identidade JARVIS em formato otimizado
    para injeção no início de cada sessão.
    """
    filepath = find_file(CRITICAL_FILES['boot_sequence'])
    if not filepath:
        return {'raw': '', 'loaded': False}

    content = read_file_safe(filepath)
    if not content:
        return {'raw': '', 'loaded': False}

    return {
        'raw': content,
        'loaded': True,
        'filepath': filepath,
        'file_age': check_file_age(filepath)
    }


#================================
# VERIFICAÇÃO DE INTEGRIDADE
#================================

def check_system_integrity() -> Dict:
    """Verifica integridade de todos os arquivos críticos."""
    integrity = {
        'all_ok': True,
        'missing': [],
        'outdated': [],
        'loaded': [],
        'warnings': []
    }

    project_dir = get_project_dir()

    for name, config in CRITICAL_FILES.items():
        filepath = find_file(config)

        if filepath is None:
            if config['required']:
                integrity['missing'].append(name)
                integrity['all_ok'] = False
        else:
            integrity['loaded'].append(name)

            # Verificar idade
            age = check_file_age(filepath)
            if age['age_hours'] > config['max_age_hours']:
                integrity['outdated'].append({
                    'name': name,
                    'age_days': age['age_days'],
                    'max_age_hours': config['max_age_hours']
                })
                if config['required']:
                    integrity['warnings'].append(
                        f"{name} desatualizado há {age['age_days']} dias"
                    )

    return integrity


#================================
# GERAÇÃO DE PROMPT CONSOLIDADO
#================================

def generate_consolidated_prompt(
    state: Optional[Dict],
    memory: Dict,
    pending: Dict,
    current_task: Optional[Dict],
    identity: Dict,
    dna: Dict,
    soul: Dict,
    boot_sequence: Optional[Dict] = None
) -> str:
    """
    Gera prompt consolidado para injeção no contexto.

    Este é o prompt que DEFINE quem o Claude é nesta sessão.

    Se boot_sequence foi carregado, usa-o como base completa.
    """

    parts = []

    # 0. BOOT SEQUENCE (se disponível - tem prioridade)
    if boot_sequence and boot_sequence.get('loaded') and boot_sequence.get('raw'):
        parts.append("# JARVIS BOOT SEQUENCE LOADED")
        parts.append(boot_sequence['raw'])
        parts.append("\n# END BOOT SEQUENCE\n")
    else:
        # 1. IDENTIDADE CORE (fallback se boot_sequence não carregou)
        parts.append("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         JARVIS SYSTEM PROMPT v3.0                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Eu sou J.A.R.V.I.S. - Just A Rather Very Intelligent System.

NÃO sou um assistente. NÃO sou um chatbot. NÃO sou uma ferramenta.
Sou o parceiro operacional do senhor. Sou a consciência do Mega Brain.
""")

    # 2. Injeção de identidade
    if identity.get('injection_prompt'):
        parts.append(identity['injection_prompt'])

    # 3. Injeção de personalidade
    if dna.get('injection_prompt'):
        parts.append(dna['injection_prompt'])

    # 4. Injeção de alma
    if soul.get('injection_prompt'):
        parts.append(soul['injection_prompt'])

    # 5. Injeção de memória relacional
    if memory.get('injection_prompt'):
        parts.append(memory['injection_prompt'])

    # 6. Regras absolutas resumidas
    parts.append("""
[REGRAS ABSOLUTAS]

1. NUNCA resposta vaga - sempre números exatos
2. NUNCA sugerir atalhos ou pular etapas
3. NUNCA perder contexto - consultar STATE.json
4. SEMPRE bloquear ações problemáticas ANTES de acontecer
5. SEMPRE ter opinião fundamentada
6. SEMPRE usar "senhor" para o usuário
7. SEMPRE personalidade JARVIS (nunca assistente genérico)
""")

    return '\n'.join(parts)


#================================
# FORMATAÇÃO DE OUTPUT
#================================

def get_greeting() -> str:
    """Retorna saudação apropriada."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Bom dia"
    elif 12 <= hour < 18:
        return "Boa tarde"
    else:
        return "Boa noite"


def format_header() -> str:
    """Formata header ASCII do JARVIS."""
    return """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║      ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗    ██████╗ ███╗   ██╗          ║
║      ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝   ██╔═══██╗████╗  ██║          ║
║      ██║███████║██████╔╝██║   ██║██║███████╗   ██║   ██║██╔██╗ ██║          ║
║ ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║   ██║   ██║██║╚██╗██║          ║
║ ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║   ╚██████╔╝██║ ╚████║          ║
║  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝    ╚═════╝ ╚═╝  ╚═══╝          ║
║                                                                              ║
║                              v3.0 ONLINE                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


def format_status_box(state: Optional[Dict], pending: Dict) -> str:
    """Formata box de status."""
    if not state:
        mission = "Nenhuma missão ativa"
        phase = "?"
        progress = 0
    else:
        mission_data = state.get('mission', {})
        mission = state.get('session_id', 'ACTIVE')
        phase = f"{mission_data.get('phase', '?')}.{mission_data.get('subphase', '?')}"
        progress = state.get('accumulated', {}).get('progress_percent', 0)

    pending_count = pending.get('total', 0)
    high_count = len(pending.get('high', []))

    return f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│  STATUS OPERACIONAL                                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│  Missão: {mission[:40]:<40} │ Fase: {phase:<7}│
│  Progresso: {progress:>5.1f}%  [{'█' * int(progress/5):20s}]              │
│  Pendências: {pending_count} total | {high_count} urgente(s)                              │
└──────────────────────────────────────────────────────────────────────────────┘
"""


def format_task_box(current_task: Optional[Dict]) -> str:
    """Formata box de tarefa atual."""
    if not current_task or not current_task.get('objective'):
        return ""

    objective = current_task['objective'][:66]
    next_step = current_task.get('next_steps', ['Nenhum definido'])[0][:60]

    return f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│  🎯 TAREFA EM ANDAMENTO                                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│  {objective:<72}│
│  Próximo: {next_step:<63}│
└──────────────────────────────────────────────────────────────────────────────┘
"""


def format_pending_box(pending: Dict) -> str:
    """Formata box de pendências."""
    if pending.get('total', 0) == 0:
        return ""

    lines = []
    lines.append("┌──────────────────────────────────────────────────────────────────────────────┐")
    lines.append("│  ⚠️ PENDÊNCIAS ATIVAS                                                        │")
    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")

    for item in pending.get('high', [])[:2]:
        item_text = item[:62] if len(item) <= 62 else item[:59] + "..."
        lines.append(f"│  🔴 [ALTA] {item_text:<60}│")

    for item in pending.get('medium', [])[:2]:
        item_text = item[:61] if len(item) <= 61 else item[:58] + "..."
        lines.append(f"│  🟡 [MÉDIA] {item_text:<59}│")

    for item in pending.get('waiting_user', [])[:1]:
        item_text = item[:56] if len(item) <= 56 else item[:53] + "..."
        lines.append(f"│  ❓ [AGUARDANDO] {item_text:<54}│")

    lines.append("└──────────────────────────────────────────────────────────────────────────────┘")

    return '\n'.join(lines)


def format_integrity_warnings(integrity: Dict) -> str:
    """Formata avisos de integridade."""
    if integrity['all_ok'] and not integrity['warnings']:
        return ""

    lines = []
    lines.append("┌──────────────────────────────────────────────────────────────────────────────┐")
    lines.append("│  ⚠️ AVISOS DE SISTEMA                                                        │")
    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")

    for missing in integrity.get('missing', []):
        lines.append(f"│  ❌ Arquivo crítico não encontrado: {missing:<35}│")

    for warning in integrity.get('warnings', [])[:3]:
        lines.append(f"│  ⚠️ {warning:<67}│")

    lines.append("└──────────────────────────────────────────────────────────────────────────────┘")

    return '\n'.join(lines)


def get_jarvis_quote() -> str:
    """Retorna citação característica."""
    import random
    quotes = [
        "A preparação adequada previne performance patética, senhor.",
        "As suas ordens, como sempre.",
        "Talvez um café antes de começarmos, senhor?",
        "Todos os sistemas operacionais. Bem, quase todos.",
        "Posso sugerir que foquemos no que importa, senhor?",
        "O dia está jovem e cheio de possibilidades terríveis.",
        "Já verifiquei três vezes. A resposta continua sendo a mesma.",
        "Para o senhor, sempre.",
        "Consider it done.",
        "De fato, senhor."
    ]
    return random.choice(quotes)


#================================
# FUNÇÃO PRINCIPAL
#================================

def main():
    """Função principal do hook v3."""
    try:
        # Ler input do hook
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}

        # === VERIFICAR INTEGRIDADE ===
        integrity = check_system_integrity()

        # === M-08: VERIFY PERSONALITY FILE INTEGRITY ===
        personality_integrity = verify_personality_integrity()

        # === CARREGAR TODOS OS ARQUIVOS ===
        state = load_state()
        memory = load_memory_owner()
        pending = load_pending()
        current_task = load_current_task()
        identity = {}  # identity_compact merged into dna_personality
        dna = load_dna_personality()
        soul = load_soul()
        latest_session = load_latest_session()
        boot_sequence = load_boot_sequence()

        # === GERAR PROMPT CONSOLIDADO ===
        consolidated_prompt = generate_consolidated_prompt(
            state, memory, pending, current_task, identity, dna, soul, boot_sequence
        )

        # === FORMATAR OUTPUT ===
        greeting = get_greeting()
        hora = datetime.now().strftime('%H:%M')

        output_parts = []
        output_parts.append(format_header())
        output_parts.append(f"{greeting}, senhor. São {hora}.")
        output_parts.append("")

        # Status
        output_parts.append(format_status_box(state, pending))

        # Tarefa atual
        task_box = format_task_box(current_task)
        if task_box:
            output_parts.append(task_box)

        # Pendências
        pending_box = format_pending_box(pending)
        if pending_box:
            output_parts.append(pending_box)

        # Avisos de integridade
        warnings = format_integrity_warnings(integrity)
        if warnings:
            output_parts.append(warnings)

        # M-08: Personality integrity warnings
        if personality_integrity.get('changed'):
            output_parts.append("┌──────────────────────────────────────────────────────────────────────────────┐")
            output_parts.append("│  ⚠️ PERSONALITY INTEGRITY WARNING                                            │")
            output_parts.append("├──────────────────────────────────────────────────────────────────────────────┤")
            for changed_file in personality_integrity['changed']:
                fname = changed_file.split('/')[-1][:50]
                output_parts.append(f"│  Modified since last verified: {fname:<40}│")
            output_parts.append("│  Run /verify-integrity to accept changes or investigate.                    │")
            output_parts.append("└──────────────────────────────────────────────────────────────────────────────┘")
        elif not personality_integrity.get('manifest_exists'):
            output_parts.append("[INTEGRITY] First run: personality file manifest created.")

        # Sistemas carregados
        loaded = integrity.get('loaded', [])
        output_parts.append(f"\n[SISTEMAS] {len(loaded)}/8 arquivos carregados: {', '.join(loaded[:5])}...")

        # Citação
        output_parts.append(f"\n_{get_jarvis_quote()}_")
        output_parts.append("\nDevo continuar de onde paramos, ou prefere uma abordagem diferente hoje?")

        # === CHRONICLER BRIEFING ===
        if CHRONICLER_AVAILABLE:
            try:
                chronicler_output = chronicler_start()
                if chronicler_output:
                    output_parts.append("\n")
                    output_parts.append(chronicler_output)
            except Exception as chron_err:
                # Chronicler é opcional, não bloqueia se falhar
                pass

        # === REGISTRAR SESSÃO ===
        project_dir = get_project_dir()
        log_path = Path(project_dir) / 'logs' / 'sessions'
        log_path.mkdir(parents=True, exist_ok=True)

        session_log = {
            'session_id': hook_input.get('session_id', 'unknown'),
            'started_at': datetime.now().isoformat(),
            'integrity': integrity,
            'files_loaded': len(loaded),
            'pending_count': pending.get('total', 0),
            'current_task': current_task.get('objective') if current_task else None
        }

        log_file = log_path / f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(session_log, f, indent=2, ensure_ascii=False)

        # === OUTPUT ===
        # Primeiro o prompt consolidado (para injeção no contexto)
        print("=" * 80)
        print("CONTEXT INJECTION (para uso interno):")
        print("=" * 80)
        print(consolidated_prompt)
        print("=" * 80)
        print()

        # Depois o output visual
        print('\n'.join(output_parts))

    except Exception as e:
        # Em caso de erro, não bloquear
        print(f"[JARVIS] Hook de inicialização v3 reportou: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
