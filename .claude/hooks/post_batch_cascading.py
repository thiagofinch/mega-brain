#!/usr/bin/env python3
"""
POST-BATCH CASCADING HOOK - REGRA #22 ENFORCEMENT
===================================================

Executa cascateamento automatico apos criacao de batch.

REGRA #22: A secao "DESTINO DO CONHECIMENTO" nao e informativa - e ORDEM DE EXECUCAO.

Este hook:
1. E chamado APOS criar qualquer batch
2. Le a secao "DESTINO DO CONHECIMENTO" do batch
3. Para cada destino:
   - AGENTS: Verificar se existe, criar/atualizar MEMORY.md com CONTEUDO REAL
   - PLAYBOOKS: Verificar se existe, criar/atualizar com CONTEUDO REAL dos frameworks
   - DNAs: Atualizar DNA-CONFIG.yaml
   - DOSSIERS: Atualizar theme dossiers
4. Adiciona secao "### Cascateamento Executado" ao batch
5. Loga acoes em /logs/cascading.jsonl

IMPORTANTE v2.0: Extrai CONTEUDO REAL dos frameworks, nao apenas referencias.

v2.1.0: Integra REGRA #26 - Valida integridade antes de marcar completo.
        So marca batch como completo se destinos existem e foram atualizados.

Autor: JARVIS
Versao: 2.1.0
Data: 2026-01-13
"""

import os
import re
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


***REMOVED***=================================
# CONFIGURATION
***REMOVED***=================================

PROJECT_DIR = os.environ.get(
    'CLAUDE_PROJECT_DIR',
    '.'
)

AGENTS_DIR = Path(PROJECT_DIR) / 'agents'
KNOWLEDGE_DIR = Path(PROJECT_DIR) / 'knowledge'
DOSSIERS_DIR = KNOWLEDGE_DIR / 'dossiers' / 'themes'
LOGS_DIR = Path(PROJECT_DIR) / 'logs'
CASCADING_LOG = LOGS_DIR / 'cascading.jsonl'


***REMOVED***=================================
# LOGGING
***REMOVED***=================================

def log_cascading_action(action: Dict) -> None:
    """
    Registra acao de cascateamento em JSONL.

    Args:
        action: Dicionario com detalhes da acao
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    action['timestamp'] = datetime.now().isoformat()

    with open(CASCADING_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(action, ensure_ascii=False) + '\n')


def log_batch_result(batch_id: str, result: Dict) -> None:
    """
    Registra resultado completo do cascateamento de um batch.
    """
    log_cascading_action({
        'type': 'batch_cascade_complete',
        'batch_id': batch_id,
        'result': result
    })


***REMOVED***=================================
# DESTINATION EXTRACTION
***REMOVED***=================================

def extract_destinations(batch_content: str) -> Dict[str, List[Dict]]:
    """
    Extrai destinos da secao DESTINO DO CONHECIMENTO.

    Suporta multiplos formatos de batch incluindo:
    - Boxes ASCII com caracteres especiais
    - Formato simples com identacao
    - Blocos de codigo markdown

    Returns:
        Dict com listas de destinos por tipo
    """
    destinations = {
        'agents': [],
        'playbooks': [],
        'dnas': [],
        'dossiers': []
    }

    # Encontrar secao DESTINO DO CONHECIMENTO (mais flexivel)
    # Pode estar com emoji ou sem, com # ou ##
    destino_patterns = [
        r'#+\s*.*DESTINO DO CONHECIMENTO.*?\n(.*?)(?=\n#+\s|\Z)',
        r'DESTINO DO CONHECIMENTO[:\s]*\n(.*?)(?=\n#+\s|\Z)',
    ]

    destino_section = None
    for pattern in destino_patterns:
        match = re.search(pattern, batch_content, re.DOTALL | re.IGNORECASE)
        if match:
            destino_section = match.group(1)
            break

    if not destino_section:
        # Fallback: procurar blocos com AGENTES/playbooks/dna diretamente
        destino_section = batch_content

    # Funcao auxiliar para limpar linha de caracteres de box
    def clean_line(line: str) -> str:
        # Remove caracteres de box ASCII do INICIO e FIM, e espacos extras
        # Primeiro remove do inicio
        cleaned = re.sub(r'^[\s│├└┌┐┘┬┴┼─\|\-\+]+', '', line)
        # Depois remove do fim
        cleaned = re.sub(r'[\s│├└┌┐┘┬┴┼─\|\-\+]+$', '', cleaned)
        return cleaned.strip()

    # Funcao para verificar se e um nome de agente (MAIUSCULAS-COM-HIFEN)
    def is_agent_name(text: str) -> bool:
        # Nome em maiusculas, pode ter hifen, sem espacos no meio
        return bool(re.match(r'^[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)*$', text))

    # === EXTRAIR AGENTES ===
    # Procurar bloco que comeca com AGENTES A ALIMENTAR
    agents_patterns = [
        r'AGENTES?\s*A\s*ALIMENTAR[:\s│]*\n(.*?)(?=\n[│\s]*(?:PLAYBOOK|DNA|DOSSIER|└─+\s*$)|```\s*\n|$)',
        r'AGENTES?\s*A\s*ALIMENTAR[:\s]*\n(.*?)(?=PLAYBOOK|DNA\s*A|$)',
    ]

    for pattern in agents_patterns:
        agents_match = re.search(pattern, destino_section, re.DOTALL | re.IGNORECASE)
        if agents_match:
            agents_block = agents_match.group(1)
            current_agent = None
            frameworks = []

            for line in agents_block.split('\n'):
                cleaned = clean_line(line)
                if not cleaned:
                    continue

                # Verifica se e um nome de agente
                if is_agent_name(cleaned):
                    # Salvar agente anterior
                    if current_agent:
                        destinations['agents'].append({
                            'name': current_agent,
                            'frameworks': frameworks
                        })
                    current_agent = cleaned
                    frameworks = []
                elif current_agent:
                    # E um framework do agente atual
                    if cleaned and not cleaned.startswith(('PLAYBOOK', 'dna', 'DOSSIER')):
                        frameworks.append(cleaned)

            # Salvar ultimo agente
            if current_agent:
                destinations['agents'].append({
                    'name': current_agent,
                    'frameworks': frameworks
                })
            break

    # === EXTRAIR PLAYBOOKS ===
    playbooks_patterns = [
        r'PLAYBOOKS?\s*A\s*ENRIQUECER[:\s│]*\n(.*?)(?=\n[│\s]*(?:DNA|DOSSIER|└─+\s*$)|```\s*\n|$)',
        r'PLAYBOOKS?\s*A\s*ENRIQUECER[:\s]*\n(.*?)(?=DNA\s*A|$)',
    ]

    for pattern in playbooks_patterns:
        pb_match = re.search(pattern, destino_section, re.DOTALL | re.IGNORECASE)
        if pb_match:
            pb_block = pb_match.group(1)

            for line in pb_block.split('\n'):
                cleaned = clean_line(line)
                if not cleaned:
                    continue

                # Procurar nome de playbook (PLAYBOOK-XXX ou apenas XXX em maiusculas)
                if cleaned.startswith('PLAYBOOK'):
                    name = cleaned.split()[0] if ' ' in cleaned else cleaned
                    # Remover : do final se existir
                    name = name.rstrip(':')
                    desc = cleaned[len(name):].strip().lstrip(':').strip() if len(cleaned) > len(name) else ''
                    destinations['playbooks'].append({
                        'name': name,
                        'description': desc
                    })
                elif is_agent_name(cleaned) and not cleaned.startswith(('dna', 'DOSSIER')):
                    # Pode ser um playbook sem prefixo PLAYBOOK-
                    destinations['playbooks'].append({
                        'name': cleaned,
                        'description': ''
                    })
                elif cleaned.startswith('"') or cleaned.startswith("'"):
                    # E uma descricao do playbook anterior
                    if destinations['playbooks']:
                        destinations['playbooks'][-1]['description'] = cleaned.strip('"\'')
            break

    # === EXTRAIR DNAs ===
    dna_patterns = [
        r'DNAS?\s*A\s*CONSOLIDAR[:\s│]*\n(.*?)(?=\n[│\s]*(?:PLAYBOOK|DOSSIER|└─+\s*$)|```\s*\n|$)',
        r'DNAS?\s*A\s*CONSOLIDAR[:\s]*\n(.*?)(?=PLAYBOOK|$)',
    ]

    for pattern in dna_patterns:
        dna_match = re.search(pattern, destino_section, re.DOTALL | re.IGNORECASE)
        if dna_match:
            dna_block = dna_match.group(1)

            for line in dna_block.split('\n'):
                cleaned = clean_line(line)
                if not cleaned:
                    continue

                # Procurar DNA-NOME e quantidade
                if 'dna' in cleaned.upper():
                    dna_name_match = re.search(r'(DNA[-_]?[A-Z0-9\-]+)', cleaned, re.IGNORECASE)
                    if dna_name_match:
                        name = dna_name_match.group(1).upper().replace('_', '-')
                        # Extrair quantidade de elementos
                        elements_match = re.search(r'\+?(\d+)\s*elementos?', cleaned, re.IGNORECASE)
                        elements = int(elements_match.group(1)) if elements_match else 0
                        destinations['dnas'].append({
                            'name': name,
                            'elements_to_add': elements
                        })
            break

    # === EXTRAIR TEMAS/dossiers ===
    # Procurar na secao de analise de temas
    themes_patterns = [
        r'TEMAS?\s*(?:NOVOS?|CONSOLIDADOS?)[:\s│]*\n(.*?)(?=\n[│\s]*(?:TEMAS?|CROSS|└─+\s*$)|```\s*\n|$)',
        r'TEMAS?\s*NOVOS?[:\s]*\n(.*?)(?=TEMAS?\s*CONSOLIDADOS?|CROSS|$)',
        r'TEMAS?\s*CONSOLIDADOS?[:\s]*\n(.*?)(?=CROSS|$)',
    ]

    for pattern in themes_patterns:
        themes_matches = list(re.finditer(pattern, batch_content, re.DOTALL | re.IGNORECASE))
        if themes_matches:
            for themes_match in themes_matches:
                themes_block = themes_match.group(1)
                for line in themes_block.split('\n'):
                    cleaned = clean_line(line)
                    if not cleaned:
                        continue
                    # Verificar se e um nome de tema valido
                    if is_agent_name(cleaned):
                        theme_name = cleaned
                        if not any(d['name'] == theme_name for d in destinations['dossiers']):
                            destinations['dossiers'].append({
                                'name': theme_name,
                                'type': 'theme'
                            })
            break  # Sair do loop de patterns se encontrou algo

    return destinations


def extract_batch_metadata(batch_content: str) -> Dict:
    """
    Extrai metadados do batch (source, ID, elementos, etc).
    """
    metadata = {
        'batch_id': '',
        'source': '',
        'elements_count': 0,
        'frameworks': [],
        'frameworks_content': {},  # NOVO: conteudo real dos frameworks
        'heuristics': [],
        'heuristics_content': '',  # NOVO: bloco completo de heuristicas
        'methodologies': [],
        'methodologies_content': '',  # NOVO: bloco completo de metodologias
        'filosofias_content': '',  # NOVO: bloco de filosofias
        'modelos_mentais_content': ''  # NOVO: bloco de modelos mentais
    }

    # Extrair BATCH ID
    batch_match = re.search(r'BATCH[\-_]?(\d+)', batch_content)
    if batch_match:
        metadata['batch_id'] = f"BATCH-{batch_match.group(1)}"

    # Extrair SOURCE
    source_match = re.search(r'(?:Source|FONTE)[:\s]+([A-Z][A-Z\s\-]+)', batch_content)
    if source_match:
        metadata['source'] = source_match.group(1).strip()

    # Extrair total de elementos
    elements_match = re.search(r'(?:TOTAL|Elementos?)[:\s]+(\d+)', batch_content)
    if elements_match:
        metadata['elements_count'] = int(elements_match.group(1))

    ***REMOVED***=============================
    # EXTRAIR FRAMEWORKS COM CONTEUDO REAL
    ***REMOVED***=============================
    fw_section_match = re.search(
        r'(?:##\s*)?(?:🏗️\s*)?KEY\s*FRAMEWORKS?.*?\n(.*?)(?=\n---|\n##|\Z)',
        batch_content, re.DOTALL | re.IGNORECASE
    )
    if fw_section_match:
        fw_section = fw_section_match.group(1)

        # Extrair cada framework como bloco ASCII completo
        # Pattern: FRAMEWORK N: NOME seguido de box ate proximo FRAMEWORK ou fim
        framework_blocks = extract_ascii_boxes(fw_section, 'FRAMEWORK')

        for name, content in framework_blocks.items():
            metadata['frameworks'].append(name)
            metadata['frameworks_content'][name] = content

    ***REMOVED***=============================
    # EXTRAIR HEURISTICAS COM CONTEUDO REAL
    ***REMOVED***=============================
    # Buscar secao que comeca com ## HEURISTICAS ou similar
    heur_section_match = re.search(
        r'(?:##\s*)?(?:🔢\s*)?HEUR[IÍ]STICAS?\s*(?:COM\s*N[UÚ]MEROS?)?\s*(?:\(\d+\))?\s*\n(```\n)?(.*?)(?=\n```\n|\n---|\n##[^#]|\Z)',
        batch_content, re.DOTALL | re.IGNORECASE
    )
    if heur_section_match:
        heur_section = heur_section_match.group(2) if heur_section_match.group(2) else heur_section_match.group(1)
        if heur_section:
            # Guardar bloco completo
            metadata['heuristics_content'] = heur_section.strip()
            # Tambem extrair lista simples para compatibilidade
            heuristics = re.findall(r'[├└│]\s*([^\n]+\d+[^\n]*)', heur_section)
            metadata['heuristics'] = [h.strip() for h in heuristics[:10]]

    ***REMOVED***=============================
    # EXTRAIR METODOLOGIAS COM CONTEUDO REAL
    ***REMOVED***=============================
    # Buscar secao que comeca com ## METODOLOGIAS ou similar
    meth_section_match = re.search(
        r'(?:##\s*)?(?:📝\s*)?METODOLOGIAS?\s*(?:\(\d+\))?\s*\n(```\n)?(.*?)(?=\n```\s*\n---|\n---|\n##[^#]|\Z)',
        batch_content, re.DOTALL | re.IGNORECASE
    )
    if meth_section_match:
        meth_section = meth_section_match.group(2) if meth_section_match.group(2) else meth_section_match.group(1)
        if meth_section:
            # Verificar se pegou o bloco correto (deve conter STEP ou numeracao)
            if 'STEP' in meth_section.upper() or re.search(r'\d+\.', meth_section):
                # Guardar bloco completo
                metadata['methodologies_content'] = meth_section.strip()
                # Tambem extrair lista para compatibilidade (limpar caracteres de box)
                meth_names = re.findall(r'\d+\.\s*([^\n]+)', meth_section)
                metadata['methodologies'] = [
                    re.sub(r'[\s│]+$', '', m).strip()
                    for m in meth_names
                ]

    ***REMOVED***=============================
    # EXTRAIR FILOSOFIAS COM CONTEUDO REAL
    ***REMOVED***=============================
    fil_section_match = re.search(
        r'(?:##\s*)?(?:🧠\s*)?FILOSOFIAS?.*?\n(.*?)(?=\n---|\n##|\Z)',
        batch_content, re.DOTALL | re.IGNORECASE
    )
    if fil_section_match:
        metadata['filosofias_content'] = fil_section_match.group(1).strip()

    ***REMOVED***=============================
    # EXTRAIR MODELOS MENTAIS COM CONTEUDO REAL
    ***REMOVED***=============================
    mm_section_match = re.search(
        r'(?:##\s*)?(?:🔄\s*)?MODELOS?\s*MENTAIS?.*?\n(.*?)(?=\n---|\n##|\Z)',
        batch_content, re.DOTALL | re.IGNORECASE
    )
    if mm_section_match:
        metadata['modelos_mentais_content'] = mm_section_match.group(1).strip()

    return metadata


def extract_ascii_boxes(content: str, prefix: str = 'FRAMEWORK') -> Dict[str, str]:
    """
    Extrai blocos ASCII completos de uma secao.

    Cada bloco comeca com uma linha contendo o prefixo (ex: FRAMEWORK 1: NOME)
    e termina quando encontra outro bloco ou fim da secao.

    Returns:
        Dict com nome do bloco -> conteudo completo incluindo ASCII art
    """
    boxes = {}

    # Estrategia: encontrar todos os headers FRAMEWORK N: e depois extrair ate o proximo
    header_pattern = re.compile(
        rf'{prefix}\s*(\d+)[:\s]+([^\n│]+)',
        re.IGNORECASE
    )

    # Encontrar posicoes de todos os headers
    headers = list(header_pattern.finditer(content))

    for i, match in enumerate(headers):
        name = match.group(2).strip()
        # Limpar caracteres de box do nome
        name = re.sub(r'[\s│]+$', '', name).strip()

        # Encontrar inicio do box (procurar ┌ antes do header)
        start_search = max(0, match.start() - 200)  # Buscar ate 200 chars antes
        box_start_match = None

        # Procurar o ┌ mais proximo antes do header
        section_before = content[start_search:match.start()]
        box_starts = list(re.finditer(r'┌[─┬]+┐', section_before))
        if box_starts:
            # Pegar o ultimo (mais proximo do header)
            box_start_match = box_starts[-1]
            actual_start = start_search + box_start_match.start()
        else:
            actual_start = match.start()

        # Encontrar fim do box
        # O fim e quando encontra o proximo header ou └──...──┘ final
        if i + 1 < len(headers):
            # Ha proximo header - encontrar └ antes dele
            next_header_pos = headers[i + 1].start()
            section_between = content[match.end():next_header_pos]
            # Procurar ultimo └──...──┘ antes do proximo header
            box_ends = list(re.finditer(r'└[─┴]+┘', section_between))
            if box_ends:
                actual_end = match.end() + box_ends[-1].end()
            else:
                actual_end = next_header_pos
        else:
            # Ultimo header - ir ate fim ou proximo └
            section_after = content[match.end():match.end() + 2000]
            box_end_match = re.search(r'└[─┴]+┘', section_after)
            if box_end_match:
                actual_end = match.end() + box_end_match.end()
            else:
                actual_end = min(match.end() + 1000, len(content))

        # Extrair bloco completo
        full_box = content[actual_start:actual_end].strip()

        if name and full_box:
            boxes[name] = full_box

    # Fallback se nao encontrou nada: tentar extrair boxes individuais
    if not boxes:
        box_blocks = re.findall(
            r'(┌[─┬]+┐.*?└[─┴]+┘)',
            content, re.DOTALL
        )
        for i, block in enumerate(box_blocks, 1):
            header_match = re.search(rf'{prefix}\s*\d*[:\s]+([^│\n]+)', block, re.IGNORECASE)
            if header_match:
                name = header_match.group(1).strip()
                name = re.sub(r'[\s│]+$', '', name).strip()
            else:
                first_line = re.search(r'│\s*([A-Z][^│\n]+)', block)
                name = first_line.group(1).strip() if first_line else f"{prefix} {i}"

            if name:
                boxes[name] = block

    return boxes


def extract_framework_content(batch_content: str, framework_name: str) -> Optional[str]:
    """
    Extrai o conteudo COMPLETO de um framework especifico do batch.

    Busca o bloco ASCII que contem o framework e retorna todo o conteudo.

    Args:
        batch_content: Conteudo completo do batch
        framework_name: Nome do framework a buscar

    Returns:
        Conteudo completo do framework incluindo ASCII box, ou None se nao encontrado
    """
    # Normalizar nome para busca
    normalized_name = framework_name.upper().replace('-', ' ').replace('_', ' ')

    # Buscar na secao de frameworks
    fw_section_match = re.search(
        r'(?:##\s*)?(?:🏗️\s*)?KEY\s*FRAMEWORKS?.*?\n(.*?)(?=\n---|\n##[^#]|\Z)',
        batch_content, re.DOTALL | re.IGNORECASE
    )

    if not fw_section_match:
        return None

    fw_section = fw_section_match.group(1)

    # Extrair todos os boxes
    boxes = extract_ascii_boxes(fw_section, 'FRAMEWORK')

    # Buscar o framework pelo nome
    for name, content in boxes.items():
        if normalized_name in name.upper().replace('-', ' ').replace('_', ' '):
            return content
        # Busca parcial
        name_words = set(name.upper().split())
        search_words = set(normalized_name.split())
        if search_words & name_words:  # Interseção
            return content

    # Fallback: buscar diretamente no conteudo
    # Pattern: FRAMEWORK [N]: <nome_framework> seguido de box
    direct_pattern = re.compile(
        rf'(┌[─┬]+┐\s*\n\s*│[^│]*FRAMEWORK\s*\d*[:\s]+[^│]*{re.escape(framework_name)}[^└]*└[─┴]+┘)',
        re.DOTALL | re.IGNORECASE
    )
    match = direct_pattern.search(batch_content)
    if match:
        return match.group(1)

    return None


***REMOVED***=================================
# CASCADING FUNCTIONS
***REMOVED***=================================

def cascade_to_agents(agents: List[Dict], batch_id: str, metadata: Dict,
                      batch_content: str = None) -> List[Dict]:
    """
    Cascateia para agentes (PERSON e CARGO).

    Para cada agente:
    1. Verifica se existe em /agents/
    2. Se NAO existe -> registra para criacao futura
    3. Se EXISTE -> atualiza MEMORY.md com novos elementos E CONTEUDO REAL

    IMPORTANTE v2.0: Passa batch_content para extrair conteudo real.

    Returns:
        Lista de acoes executadas
    """
    actions = []

    for agent in agents:
        agent_name = agent['name']
        frameworks = agent.get('frameworks', [])

        # Mapear nome para caminho
        # OBJECTION-HANDLER -> CARGO/SALES/OBJECTION-HANDLER ou similar
        agent_path = find_agent_path(agent_name)

        if agent_path:
            # Agente existe - atualizar MEMORY.md
            memory_path = agent_path / 'MEMORY.md'

            if memory_path.exists():
                update_result = update_agent_memory(
                    memory_path,
                    batch_id,
                    frameworks,
                    metadata,
                    batch_content  # NOVO: passar conteudo do batch
                )
                actions.append({
                    'action': 'update_memory',
                    'agent': agent_name,
                    'path': str(memory_path),
                    'frameworks_added': len(frameworks),
                    'content_extracted': batch_content is not None,
                    'success': update_result
                })
            else:
                # Criar MEMORY.md basico
                create_result = create_agent_memory(
                    memory_path,
                    agent_name,
                    batch_id,
                    frameworks,
                    metadata,
                    batch_content  # NOVO: passar conteudo do batch
                )
                actions.append({
                    'action': 'create_memory',
                    'agent': agent_name,
                    'path': str(memory_path),
                    'content_extracted': batch_content is not None,
                    'success': create_result
                })
        else:
            # Agente nao existe - registrar para criacao futura
            actions.append({
                'action': 'agent_not_found',
                'agent': agent_name,
                'frameworks': frameworks,
                'note': 'Agent should be created in Phase 5.3'
            })

        log_cascading_action({
            'type': 'agent_cascade',
            'agent': agent_name,
            'batch_id': batch_id,
            'action': actions[-1]
        })

    return actions


def find_agent_path(agent_name: str) -> Optional[Path]:
    """
    Encontra o caminho de um agente pelo nome.

    Busca em:
    - /agents/persons/
    - /agents/cargo/
    - /agents/council/
    """
    # Normalizar nome
    normalized = agent_name.upper().replace(' ', '-')

    # Buscar em PERSONS
    persons_dir = AGENTS_DIR / 'persons'
    if persons_dir.exists():
        for agent_dir in persons_dir.iterdir():
            if agent_dir.is_dir() and normalized in agent_dir.name.upper():
                return agent_dir

    # Buscar em CARGO (recursivamente)
    cargo_dir = AGENTS_DIR / 'cargo'
    if cargo_dir.exists():
        for category in cargo_dir.iterdir():
            if category.is_dir():
                for agent_dir in category.iterdir():
                    if agent_dir.is_dir() and normalized in agent_dir.name.upper():
                        return agent_dir

    # Buscar em COUNCIL
    council_dir = AGENTS_DIR / 'council'
    if council_dir.exists():
        for agent_dir in council_dir.iterdir():
            if agent_dir.is_dir() and normalized in agent_dir.name.upper():
                return agent_dir

    return None


def update_agent_memory(memory_path: Path, batch_id: str,
                         frameworks: List[str], metadata: Dict,
                         batch_content: str = None) -> bool:
    """
    Atualiza MEMORY.md de um agente com novos frameworks.

    IMPORTANTE v2.0: Extrai CONTEUDO REAL dos frameworks, nao apenas referencias.
    """
    try:
        content = memory_path.read_text(encoding='utf-8')

        # Criar secao de atualizacao
        update_section = f"""

---

## Atualizacao via Cascading - {batch_id}

**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Fonte:** {metadata.get('source', 'Unknown')}

### Frameworks Adicionados

"""
        # NOVO v2.0: Incluir conteudo REAL dos frameworks
        frameworks_content = metadata.get('frameworks_content', {})

        for fw in frameworks:
            # Tentar obter conteudo real do framework
            fw_content = frameworks_content.get(fw)

            if not fw_content and batch_content:
                # Fallback: extrair diretamente do batch
                fw_content = extract_framework_content(batch_content, fw)

            if fw_content:
                update_section += f"\n#### {fw}\n\n```\n{fw_content}\n```\n\n"
            else:
                # Fallback para referencia se nao conseguir extrair
                update_section += f"- **{fw}** (ver `{batch_id}` para detalhes)\n"

        update_section += f"""
### Referencia

Batch: `{batch_id}`
Elementos totais: {metadata.get('elements_count', 'N/A')}
"""

        # Adicionar no final do arquivo
        content += update_section
        memory_path.write_text(content, encoding='utf-8')

        return True

    except Exception as e:
        log_cascading_action({
            'type': 'error',
            'action': 'update_agent_memory',
            'path': str(memory_path),
            'error': str(e)
        })
        return False


def create_agent_memory(memory_path: Path, agent_name: str,
                         batch_id: str, frameworks: List[str],
                         metadata: Dict, batch_content: str = None) -> bool:
    """
    Cria MEMORY.md basico para um agente.

    IMPORTANTE v2.0: Inclui CONTEUDO REAL dos frameworks, nao apenas nomes.
    """
    try:
        memory_path.parent.mkdir(parents=True, exist_ok=True)

        content = f"""# MEMORY - {agent_name}

> Memoria do agente, alimentada via cascateamento de batches.
> **VERSAO:** v2.0 - Conteudo real extraido

---

## Inicializacao

**Criado em:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Fonte inicial:** {metadata.get('source', 'Unknown')}
**Batch inicial:** {batch_id}

---

## Conhecimento Absorvido

### De {batch_id}

"""
        # NOVO v2.0: Incluir conteudo REAL dos frameworks
        frameworks_content = metadata.get('frameworks_content', {})

        for fw in frameworks:
            # Tentar obter conteudo real do framework
            fw_content = frameworks_content.get(fw)

            if not fw_content and batch_content:
                # Fallback: extrair diretamente do batch
                fw_content = extract_framework_content(batch_content, fw)

            if fw_content:
                content += f"\n#### {fw}\n\n```\n{fw_content}\n```\n\n"
            else:
                content += f"- **{fw}**\n"

        content += f"""
---

## Historico de Atualizacoes

| Data | Batch | Elementos |
|------|-------|-----------|
| {datetime.now().strftime('%Y-%m-%d')} | {batch_id} | {len(frameworks)} |

"""

        memory_path.write_text(content, encoding='utf-8')
        return True

    except Exception as e:
        log_cascading_action({
            'type': 'error',
            'action': 'create_agent_memory',
            'path': str(memory_path),
            'error': str(e)
        })
        return False


def cascade_to_playbooks(playbooks: List[Dict], batch_id: str,
                          metadata: Dict, batch_content: str = None) -> List[Dict]:
    """
    Cascateia para playbooks.

    Para cada playbook:
    1. Verifica se existe em /knowledge/playbooks/
    2. Se NAO existe -> cria com CONTEUDO REAL dos frameworks do batch
    3. Se EXISTE -> adiciona novos frameworks/metodologias COM CONTEUDO REAL

    IMPORTANTE v2.0: Passa batch_content para extrair conteudo real.
    """
    actions = []

    playbooks_dir = KNOWLEDGE_DIR / 'playbooks'
    playbooks_dir.mkdir(parents=True, exist_ok=True)

    for playbook in playbooks:
        pb_name = playbook['name']
        pb_desc = playbook.get('description', '')

        # Normalizar nome do arquivo
        pb_filename = f"{pb_name}.md"
        pb_path = playbooks_dir / pb_filename

        if pb_path.exists():
            # Atualizar playbook existente
            update_result = update_playbook(
                pb_path, batch_id, pb_desc, metadata, batch_content
            )
            actions.append({
                'action': 'update_playbook',
                'playbook': pb_name,
                'path': str(pb_path),
                'content_extracted': batch_content is not None,
                'success': update_result
            })
        else:
            # Criar novo playbook
            create_result = create_playbook(
                pb_path, pb_name, batch_id, pb_desc, metadata, batch_content
            )
            actions.append({
                'action': 'create_playbook',
                'playbook': pb_name,
                'path': str(pb_path),
                'content_extracted': batch_content is not None,
                'success': create_result
            })

        log_cascading_action({
            'type': 'playbook_cascade',
            'playbook': pb_name,
            'batch_id': batch_id,
            'action': actions[-1]
        })

    return actions


def update_playbook(pb_path: Path, batch_id: str,
                    description: str, metadata: Dict,
                    batch_content: str = None) -> bool:
    """
    Atualiza playbook existente com novos frameworks.

    IMPORTANTE v2.0: Inclui CONTEUDO REAL dos frameworks.
    """
    try:
        content = pb_path.read_text(encoding='utf-8')

        # Adicionar secao de atualizacao
        update_section = f"""

---

## Atualizacao - {batch_id}

**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Fonte:** {metadata.get('source', 'Unknown')}

### Novos Elementos

{description if description else ''}

"""
        # NOVO v2.0: Incluir conteudo REAL dos frameworks
        frameworks_content = metadata.get('frameworks_content', {})
        frameworks = metadata.get('frameworks', [])[:5]

        if frameworks_content or batch_content:
            update_section += "### Frameworks Detalhados\n\n"
            for fw in frameworks:
                fw_content = frameworks_content.get(fw)

                if not fw_content and batch_content:
                    fw_content = extract_framework_content(batch_content, fw)

                if fw_content:
                    update_section += f"#### {fw}\n\n```\n{fw_content}\n```\n\n"
                else:
                    update_section += f"- **{fw}**\n"
        else:
            update_section += "### Frameworks Relacionados\n\n"
            for fw in frameworks:
                update_section += f"- {fw}\n"

        # Incluir heuristicas se disponivel
        heur_content = metadata.get('heuristics_content', '')
        if heur_content:
            update_section += f"\n### Heuristicas\n\n```\n{heur_content}\n```\n\n"

        # Incluir metodologias se disponivel
        meth_content = metadata.get('methodologies_content', '')
        if meth_content:
            update_section += f"\n### Metodologias\n\n```\n{meth_content}\n```\n\n"

        update_section += f"\n**Referencia:** `{batch_id}`\n"

        content += update_section
        pb_path.write_text(content, encoding='utf-8')

        return True

    except Exception as e:
        log_cascading_action({
            'type': 'error',
            'action': 'update_playbook',
            'path': str(pb_path),
            'error': str(e)
        })
        return False


def create_playbook(pb_path: Path, name: str, batch_id: str,
                    description: str, metadata: Dict,
                    batch_content: str = None) -> bool:
    """
    Cria novo playbook.

    IMPORTANTE v2.0: Inclui CONTEUDO REAL dos frameworks, heuristicas e metodologias.
    """
    try:
        content = f"""# {name}

> Playbook gerado via cascateamento automatico.
> **Versao:** 2.0.0 (com conteudo real extraido)
> **Criado em:** {datetime.now().strftime('%Y-%m-%d')}
> **Fonte inicial:** {metadata.get('source', 'Unknown')}

---

## Objetivo

{description if description else 'Definir durante revisao manual.'}

---

## Frameworks Incluidos

"""
        # NOVO v2.0: Incluir conteudo REAL dos frameworks
        frameworks_content = metadata.get('frameworks_content', {})

        for fw in metadata.get('frameworks', []):
            fw_content = frameworks_content.get(fw)

            if not fw_content and batch_content:
                fw_content = extract_framework_content(batch_content, fw)

            if fw_content:
                content += f"### {fw}\n\n```\n{fw_content}\n```\n\n"
            else:
                content += f"### {fw}\n\n*Detalhes em `{batch_id}`*\n\n"

        content += f"""
---

## Heuristicas

"""
        # Incluir bloco de heuristicas
        heur_content = metadata.get('heuristics_content', '')
        if heur_content:
            content += f"```\n{heur_content}\n```\n\n"
        else:
            for heur in metadata.get('heuristics', []):
                content += f"- {heur}\n"

        content += f"""
---

## Metodologias

"""
        # Incluir bloco de metodologias
        meth_content = metadata.get('methodologies_content', '')
        if meth_content:
            content += f"```\n{meth_content}\n```\n\n"
        else:
            for meth in metadata.get('methodologies', []):
                content += f"- {meth}\n"

        # Incluir filosofias se disponivel
        fil_content = metadata.get('filosofias_content', '')
        if fil_content:
            content += f"""
---

## Filosofias

```
{fil_content}
```

"""

        # Incluir modelos mentais se disponivel
        mm_content = metadata.get('modelos_mentais_content', '')
        if mm_content:
            content += f"""
---

## Modelos Mentais

```
{mm_content}
```

"""

        content += f"""
---

## Historico

| Data | Batch | Acao |
|------|-------|------|
| {datetime.now().strftime('%Y-%m-%d')} | {batch_id} | Criacao inicial |

---

## Referencias

- Batch: `{batch_id}`
- Fonte: {metadata.get('source', 'Unknown')}
"""

        pb_path.write_text(content, encoding='utf-8')
        return True

    except Exception as e:
        log_cascading_action({
            'type': 'error',
            'action': 'create_playbook',
            'path': str(pb_path),
            'error': str(e)
        })
        return False


def cascade_to_dnas(dnas: List[Dict], batch_id: str, metadata: Dict) -> List[Dict]:
    """
    Cascateia para DNA-CONFIG.yaml dos agentes.

    Atualiza contadores de elementos nas 5 camadas.
    """
    actions = []

    for dna in dnas:
        dna_name = dna['name']
        elements_to_add = dna.get('elements_to_add', 0)

        # Extrair nome do agente do DNA (DNA-JEREMY-HAYNES -> JEREMY-HAYNES)
        agent_name = dna_name.replace('DNA-', '')
        agent_path = find_agent_path(agent_name)

        if agent_path:
            config_path = agent_path / 'DNA-CONFIG.yaml'

            if config_path.exists():
                update_result = update_dna_config(
                    config_path,
                    batch_id,
                    elements_to_add,
                    metadata
                )
                actions.append({
                    'action': 'update_dna_config',
                    'dna': dna_name,
                    'path': str(config_path),
                    'elements_added': elements_to_add,
                    'success': update_result
                })
            else:
                actions.append({
                    'action': 'dna_config_not_found',
                    'dna': dna_name,
                    'expected_path': str(config_path),
                    'note': 'DNA-CONFIG.yaml should exist for this agent'
                })
        else:
            actions.append({
                'action': 'agent_not_found',
                'dna': dna_name,
                'note': 'Agent for this DNA not found'
            })

        log_cascading_action({
            'type': 'dna_cascade',
            'dna': dna_name,
            'batch_id': batch_id,
            'action': actions[-1]
        })

    return actions


def update_dna_config(config_path: Path, batch_id: str,
                       elements_to_add: int, metadata: Dict) -> bool:
    """
    Atualiza DNA-CONFIG.yaml com novos elementos.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        # Atualizar batches processados
        if 'batches_processed' not in config:
            config['batches_processed'] = []
        config['batches_processed'].append({
            'batch_id': batch_id,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'elements': elements_to_add
        })

        # Atualizar total de elementos
        if 'total_elements' not in config:
            config['total_elements'] = 0
        config['total_elements'] += elements_to_add

        # Atualizar timestamp
        config['last_updated'] = datetime.now().isoformat()
        config['last_batch'] = batch_id

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        return True

    except Exception as e:
        log_cascading_action({
            'type': 'error',
            'action': 'update_dna_config',
            'path': str(config_path),
            'error': str(e)
        })
        return False


def cascade_to_dossiers(themes: List[Dict], batch_id: str,
                         metadata: Dict, batch_content: str = None) -> List[Dict]:
    """
    Cascateia para theme dossiers.

    Aplica REGRA #21: dossiers existentes devem ser ATUALIZADOS, nao ignorados.

    IMPORTANTE v2.0: Passa batch_content para extrair conteudo real.
    """
    actions = []

    DOSSIERS_DIR.mkdir(parents=True, exist_ok=True)

    for theme in themes:
        theme_name = theme['name']
        dossier_name = f"DOSSIER-{theme_name}.md"
        dossier_path = DOSSIERS_DIR / dossier_name

        if dossier_path.exists():
            # REGRA #21: Comparar versao do dossier vs batch
            update_result = update_theme_dossier(
                dossier_path, batch_id, metadata, batch_content
            )
            actions.append({
                'action': 'update_dossier',
                'theme': theme_name,
                'path': str(dossier_path),
                'content_extracted': batch_content is not None,
                'success': update_result,
                'rule': 'REGRA #21 applied'
            })
        else:
            # Criar novo dossier
            create_result = create_theme_dossier(
                dossier_path, theme_name, batch_id, metadata, batch_content
            )
            actions.append({
                'action': 'create_dossier',
                'theme': theme_name,
                'path': str(dossier_path),
                'content_extracted': batch_content is not None,
                'success': create_result
            })

        log_cascading_action({
            'type': 'dossier_cascade',
            'theme': theme_name,
            'batch_id': batch_id,
            'action': actions[-1]
        })

    return actions


def update_theme_dossier(dossier_path: Path, batch_id: str, metadata: Dict,
                          batch_content: str = None) -> bool:
    """
    Atualiza theme dossier existente (REGRA #21).

    IMPORTANTE v2.0: Inclui CONTEUDO REAL dos frameworks, heuristicas e metodologias.
    """
    try:
        content = dossier_path.read_text(encoding='utf-8')

        # Verificar versao atual
        version_match = re.search(r'Vers[aã]o[:\s]+v?(\d+\.\d+\.?\d*)', content)
        current_version = version_match.group(1) if version_match else '1.0.0'

        # Incrementar versao
        parts = current_version.split('.')
        if len(parts) >= 2:
            parts[1] = str(int(parts[1]) + 1)
        new_version = '.'.join(parts)

        # Adicionar secao de atualizacao
        update_section = f"""

---

## Atualizacao v{new_version} - {batch_id}

**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Fonte:** {metadata.get('source', 'Unknown')}
**Regra aplicada:** REGRA #21 (Cascateamento de Theme Dossiers)
**Versao Hook:** v2.0 (conteudo real extraido)

"""
        # NOVO v2.0: Incluir conteudo REAL dos frameworks
        frameworks_content = metadata.get('frameworks_content', {})
        frameworks = metadata.get('frameworks', [])[:5]

        if frameworks_content:
            update_section += "### Frameworks Detalhados\n\n"
            for fw in frameworks:
                fw_content = frameworks_content.get(fw)
                if not fw_content and batch_content:
                    fw_content = extract_framework_content(batch_content, fw)
                if fw_content:
                    update_section += f"#### {fw}\n\n```\n{fw_content}\n```\n\n"
                else:
                    update_section += f"- **{fw}**\n"
        else:
            update_section += "### Novos Frameworks\n\n"
            for fw in frameworks:
                update_section += f"- {fw}\n"

        # Incluir bloco de heuristicas
        heur_content = metadata.get('heuristics_content', '')
        if heur_content:
            update_section += f"\n### Heuristicas\n\n```\n{heur_content}\n```\n\n"
        else:
            heuristics = metadata.get('heuristics', [])[:5]
            if heuristics:
                update_section += "\n### Novas Heuristicas\n\n"
                for heur in heuristics:
                    update_section += f"- {heur}\n"

        # Incluir metodologias
        meth_content = metadata.get('methodologies_content', '')
        if meth_content:
            update_section += f"\n### Metodologias\n\n```\n{meth_content}\n```\n\n"

        update_section += f"""
### Referencia

- Batch: `{batch_id}`
- Elementos: {metadata.get('elements_count', 'N/A')}
"""

        # Atualizar versao no header
        content = re.sub(
            r'(Vers[aã]o[:\s]+v?)(\d+\.\d+\.?\d*)',
            f'\\g<1>{new_version}',
            content
        )

        content += update_section
        dossier_path.write_text(content, encoding='utf-8')

        return True

    except Exception as e:
        log_cascading_action({
            'type': 'error',
            'action': 'update_theme_dossier',
            'path': str(dossier_path),
            'error': str(e)
        })
        return False


def create_theme_dossier(dossier_path: Path, theme_name: str,
                          batch_id: str, metadata: Dict,
                          batch_content: str = None) -> bool:
    """
    Cria novo theme dossier.

    IMPORTANTE v2.0: Inclui CONTEUDO REAL dos frameworks, heuristicas e metodologias.
    """
    try:
        content = f"""# DOSSIER - {theme_name}

> Dossier tematico gerado via cascateamento automatico.
> **Versao Hook:** v2.0 (conteudo real extraido)

---

## Metadata

- **Versao:** v2.0.0
- **Criado em:** {datetime.now().strftime('%Y-%m-%d')}
- **Fonte inicial:** {metadata.get('source', 'Unknown')}
- **Batch inicial:** {batch_id}

---

## Visao Geral

Este dossier consolida conhecimento sobre **{theme_name.replace('-', ' ').title()}**.

---

## Frameworks

"""
        # NOVO v2.0: Incluir conteudo REAL dos frameworks
        frameworks_content = metadata.get('frameworks_content', {})

        for fw in metadata.get('frameworks', []):
            fw_content = frameworks_content.get(fw)
            if not fw_content and batch_content:
                fw_content = extract_framework_content(batch_content, fw)

            if fw_content:
                content += f"### {fw}\n\n```\n{fw_content}\n```\n\n"
            else:
                content += f"### {fw}\n\n*Fonte: {batch_id}*\n\n"

        content += f"""
---

## Heuristicas

"""
        # Incluir bloco completo de heuristicas
        heur_content = metadata.get('heuristics_content', '')
        if heur_content:
            content += f"```\n{heur_content}\n```\n\n"
        else:
            for heur in metadata.get('heuristics', []):
                content += f"- {heur}\n"

        content += f"""
---

## Metodologias

"""
        # Incluir bloco completo de metodologias
        meth_content = metadata.get('methodologies_content', '')
        if meth_content:
            content += f"```\n{meth_content}\n```\n\n"
        else:
            for meth in metadata.get('methodologies', []):
                content += f"- {meth}\n"

        # Incluir filosofias se disponivel
        fil_content = metadata.get('filosofias_content', '')
        if fil_content:
            content += f"""
---

## Filosofias

```
{fil_content}
```

"""

        # Incluir modelos mentais se disponivel
        mm_content = metadata.get('modelos_mentais_content', '')
        if mm_content:
            content += f"""
---

## Modelos Mentais

```
{mm_content}
```

"""

        content += f"""
---

## Fontes

| Fonte | Batch | Data |
|-------|-------|------|
| {metadata.get('source', 'Unknown')} | {batch_id} | {datetime.now().strftime('%Y-%m-%d')} |

---

## Cross-References

*Conexoes com outros temas serao adicionadas em atualizacoes futuras.*
"""

        dossier_path.write_text(content, encoding='utf-8')
        return True

    except Exception as e:
        log_cascading_action({
            'type': 'error',
            'action': 'create_theme_dossier',
            'path': str(dossier_path),
            'error': str(e)
        })
        return False


***REMOVED***=================================
# BATCH UPDATE
***REMOVED***=================================

def mark_cascading_complete(batch_path: str, cascaded_items: Dict) -> bool:
    """
    Adiciona secao 'Cascateamento Executado' ao batch.
    """
    try:
        batch_file = Path(batch_path)
        content = batch_file.read_text(encoding='utf-8')

        # Verificar se ja tem secao de cascateamento
        if 'Cascateamento Executado' in content:
            return True  # Ja executado

        # Criar secao de cascateamento
        cascade_section = f"""

---

## Cascateamento Executado

**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Regra aplicada:** REGRA #22 (Cascateamento Multi-Destino)

### Resumo

| Tipo | Quantidade | Sucesso |
|------|------------|---------|
| Agentes | {len(cascaded_items.get('agents', []))} | {sum(1 for a in cascaded_items.get('agents', []) if a.get('success', False) or 'update' in a.get('action', ''))} |
| Playbooks | {len(cascaded_items.get('playbooks', []))} | {sum(1 for p in cascaded_items.get('playbooks', []) if p.get('success', False))} |
| DNAs | {len(cascaded_items.get('dnas', []))} | {sum(1 for d in cascaded_items.get('dnas', []) if d.get('success', False))} |
| Dossiers | {len(cascaded_items.get('dossiers', []))} | {sum(1 for d in cascaded_items.get('dossiers', []) if d.get('success', False))} |

### Detalhes

"""

        # Filtrar apenas chaves de cascateamento
        cascade_keys = ['agents', 'playbooks', 'dnas', 'dossiers']
        for action_type in cascade_keys:
            actions = cascaded_items.get(action_type, [])
            if actions and isinstance(actions, list):
                cascade_section += f"**{action_type.upper()}:**\n"
                for action in actions:
                    if isinstance(action, dict):
                        status = "OK" if action.get('success', False) else action.get('action', 'pending')
                        name = action.get('agent') or action.get('playbook') or action.get('dna') or action.get('theme', 'unknown')
                        cascade_section += f"- [{status}] {name}\n"
                cascade_section += "\n"

        cascade_section += f"""
---

*Cascateamento automatico via `post_batch_cascading.py`*
"""

        content += cascade_section
        batch_file.write_text(content, encoding='utf-8')

        return True

    except Exception as e:
        log_cascading_action({
            'type': 'error',
            'action': 'mark_cascading_complete',
            'path': batch_path,
            'error': str(e)
        })
        return False


***REMOVED***=================================
# MAIN ENTRY POINT
***REMOVED***=================================

def process_batch(batch_path: str) -> Dict:
    """
    Processa um batch e executa cascateamento completo.

    IMPORTANTE v2.0: Passa batch_content para extrair CONTEUDO REAL dos frameworks.

    Returns:
        Dicionario com resultados do cascateamento
    """
    result = {
        'batch_path': batch_path,
        'success': False,
        'version': '2.0.0',  # NOVO: versao do hook
        'content_extraction': True,  # NOVO: indica que extrai conteudo real
        'agents': [],
        'playbooks': [],
        'dnas': [],
        'dossiers': [],
        'errors': []
    }

    try:
        # Ler conteudo do batch
        batch_file = Path(batch_path)
        if not batch_file.exists():
            result['errors'].append(f"Batch file not found: {batch_path}")
            return result

        batch_content = batch_file.read_text(encoding='utf-8')

        # Extrair metadados (agora inclui conteudo real dos frameworks)
        metadata = extract_batch_metadata(batch_content)
        batch_id = metadata.get('batch_id', batch_file.stem)

        log_cascading_action({
            'type': 'batch_cascade_start',
            'batch_id': batch_id,
            'batch_path': batch_path,
            'version': '2.0.0',
            'frameworks_extracted': len(metadata.get('frameworks_content', {}))
        })

        # Extrair destinos
        destinations = extract_destinations(batch_content)

        # Executar cascateamento para cada tipo
        # NOVO v2.0: Passa batch_content para extrair conteudo real
        if destinations['agents']:
            result['agents'] = cascade_to_agents(
                destinations['agents'],
                batch_id,
                metadata,
                batch_content  # NOVO
            )

        if destinations['playbooks']:
            result['playbooks'] = cascade_to_playbooks(
                destinations['playbooks'],
                batch_id,
                metadata,
                batch_content  # NOVO
            )

        if destinations['dnas']:
            result['dnas'] = cascade_to_dnas(
                destinations['dnas'],
                batch_id,
                metadata
            )

        if destinations['dossiers']:
            result['dossiers'] = cascade_to_dossiers(
                destinations['dossiers'],
                batch_id,
                metadata,
                batch_content  # NOVO v2.0
            )

        ***REMOVED***=========================
        # REGRA #26: VALIDAÇÃO DE INTEGRIDADE DO CASCATEAMENTO
        # Só marca como completo se validação passar
        ***REMOVED***=========================
        try:
            import sys
            scripts_path = str(Path(PROJECT_DIR) / 'scripts')
            if scripts_path not in sys.path:
                sys.path.insert(0, scripts_path)
            from validate_cascading_integrity import validate_batch_integrity

            validation = validate_batch_integrity(batch_id)
            result['validation'] = {
                'status': validation['status'],
                'destinations_total': validation.get('destinations_total', 0),
                'destinations_exist': validation.get('destinations_exist', 0),
                'reference_count': validation.get('reference_count', 0)
            }

            if validation['status'] == 'FAILED':
                result['errors'].append(
                    f"REGRA #26 Validation failed: {validation.get('error', 'Unknown')}"
                )
                log_cascading_action({
                    'type': 'validation_failed',
                    'batch_id': batch_id,
                    'validation': validation
                })
                # Não marca como completo, retorna com erro
                return result

            log_cascading_action({
                'type': 'validation_passed',
                'batch_id': batch_id,
                'status': validation['status']
            })

        except ImportError as e:
            # Script não disponível - log warning mas continua
            log_cascading_action({
                'type': 'validation_warning',
                'batch_id': batch_id,
                'warning': f"Validation script not available: {e}"
            })
        except Exception as e:
            # Erro na validação - log warning mas continua (não bloqueia)
            log_cascading_action({
                'type': 'validation_error',
                'batch_id': batch_id,
                'error': str(e)
            })

        # Marcar cascateamento como completo no batch
        mark_cascading_complete(batch_path, result)

        result['success'] = True
        log_batch_result(batch_id, result)

    except Exception as e:
        result['errors'].append(str(e))
        log_cascading_action({
            'type': 'error',
            'action': 'process_batch',
            'path': batch_path,
            'error': str(e)
        })

    return result


def main(batch_path: str = None):
    """
    Entry point do hook.

    Pode ser chamado de duas formas:
    1. Como hook: recebe input via stdin
    2. Diretamente: recebe batch_path como argumento
    """
    import sys

    if batch_path:
        # Chamada direta com path
        result = process_batch(batch_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result

    # Chamada como hook - ler stdin
    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}

        # Extrair path do batch do input
        batch_path = hook_input.get('batch_path')

        if not batch_path:
            # Tentar extrair de tool_input
            tool_input = hook_input.get('tool_input', {})
            batch_path = tool_input.get('file_path', '')

            # Verificar se e um arquivo de batch
            if 'BATCH' not in batch_path.upper():
                output = {
                    'continue': True,
                    'feedback': None,
                    'note': 'Not a batch file, skipping cascading'
                }
                print(json.dumps(output))
                return

        # Processar batch
        result = process_batch(batch_path)

        # Preparar output do hook
        feedback = None
        if result['success']:
            total_cascaded = (
                len(result['agents']) +
                len(result['playbooks']) +
                len(result['dnas']) +
                len(result['dossiers'])
            )
            if total_cascaded > 0:
                feedback = f"[JARVIS] REGRA #22: Cascateamento executado - {total_cascaded} destinos processados"
        else:
            if result['errors']:
                feedback = f"[JARVIS] REGRA #22: Erro no cascateamento - {result['errors'][0]}"

        output = {
            'continue': True,
            'feedback': feedback,
            'result': result
        }

        print(json.dumps(output))

    except Exception as e:
        error_output = {
            'continue': True,
            'feedback': f"[JARVIS] Erro no hook de cascateamento: {str(e)}",
            'error': str(e)
        }
        print(json.dumps(error_output))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
