#!/usr/bin/env python3
"""
JARVIS BRIEFING MODULE v2.0
===========================
Gera briefing cinematografico na voz do Jarvis com:
- Health Score (0-100) com 5 componentes ponderados
- Source Matrix visual (progresso por fonte de conhecimento)
- 120 caracteres de largura (padrao CHRONICLER)
- Loops abertos (pendencias) priorizados
- Ultimas implementacoes
- Proxima melhor acao em destaque

Pode ser chamado:
1. Via session_start.py (automatico)
2. Via /jarvis-briefing skill (manual)
"""

import json
import os
import random
from datetime import datetime
from pathlib import Path


def get_project_dir():
    """Obtem o diretorio do projeto."""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())


def load_file(filename: str) -> str:
    """Carrega arquivo de memoria com fallback."""
    project_dir = get_project_dir()
    jarvis_dir = Path(project_dir) / '.claude' / 'jarvis'
    filepath = jarvis_dir / filename

    if filepath.exists():
        return filepath.read_text(encoding='utf-8')
    return ""


def load_state() -> dict:
    """Carrega STATE.json com fallback para dict vazio."""
    try:
        content = load_file('STATE.json')
        return json.loads(content) if content else {}
    except json.JSONDecodeError:
        return {}


def extract_pending_items(pending_content: str) -> list:
    """Extrai itens pendentes do PENDING.md."""
    items = []
    for line in pending_content.split('\n'):
        line = line.strip()
        # Itens com checkbox
        if line.startswith('- [ ]') or line.startswith('* [ ]'):
            items.append(line[5:].strip())
        # Itens com [x] completos - ignorar
        elif line.startswith('- [x]') or line.startswith('* [x]'):
            continue
        # Itens com TODO
        elif line.startswith('- ') and 'TODO' in line.upper():
            items.append(line[2:].strip())
        # Itens de alta/media prioridade
        elif line.startswith('- ') and any(p in line for p in ['[ALTA]', '[MEDIA]', '[BAIXA]']):
            items.append(line[2:].strip())
    return items[:10]  # Maximo 10 itens


def extract_recent_changes(memory_content: str) -> list:
    """Extrai mudancas recentes do JARVIS-MEMORY.md."""
    changes = []
    in_recent_section = False

    for line in memory_content.split('\n'):
        # Detectar secao de mudancas recentes
        if any(marker in line.lower() for marker in ['recent', 'ultima', '## 202', 'sessao anterior']):
            in_recent_section = True
            continue
        # Fim da secao
        if in_recent_section and line.startswith('##'):
            break
        # Extrair itens
        if in_recent_section and line.strip().startswith('-'):
            changes.append(line.strip()[1:].strip())

    return changes[:5]  # Ultimas 5 mudancas


def determine_next_action(state: dict, pending: list) -> str:
    """Determina a proxima melhor acao baseado no contexto."""
    # Prioridade 1: Tarefa atual em andamento
    current = load_file('CURRENT-TASK.md')
    if current.strip():
        for line in current.split('\n'):
            if '## Objetivo' in line:
                continue
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('>'):
                return f"Continuar: {line[:60]}..." if len(line) > 60 else f"Continuar: {line}"

    # Prioridade 2: Item mais critico do pending
    if pending:
        for item in pending:
            # Procura por palavras de urgencia
            if any(word in item.lower() for word in ['urgente', 'critico', 'blocker', 'bug', 'alta']):
                return f"URGENTE: {item[:55]}..." if len(item) > 55 else f"URGENTE: {item}"
        # Primeiro item da lista
        first = pending[0]
        return f"Proximo item: {first[:50]}..." if len(first) > 50 else f"Proximo item: {first}"

    # Prioridade 3: Baseado no estado do projeto
    if 'mission' in state:
        mission = state['mission']
        phase = mission.get('phase', 1)
        batch = mission.get('batch', '?')
        return f"Avancar para batch {batch} da Fase {phase}"

    return "Aguardando instrucoes do senhor"


def get_greeting() -> str:
    """Retorna saudacao apropriada ao horario."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Bom dia"
    elif 12 <= hour < 18:
        return "Boa tarde"
    else:
        return "Boa noite"


def get_jarvis_quote() -> str:
    """Retorna uma citacao caracteristica do Jarvis."""
    quotes = [
        "A preparacao adequada previne performance patetica, Senhor.",
        "Devo lembra-lo que voce tem uma tendencia a ignorar minhas sugestoes, Senhor.",
        "As suas ordens, como sempre.",
        "Talvez um cafe antes de comecarmos, Senhor?",
        "Todos os sistemas operacionais. Bem, quase todos.",
        "Posso sugerir que foquemos no que importa, Senhor?",
        "O dia esta jovem e cheio de possibilidades terriveis.",
        "Protocolo de emergencia? Ou apenas segunda-feira normal?",
        "Ja verifiquei tres vezes. A resposta continua sendo a mesma.",
        "Eficiencia e minha especialidade. Paciencia... nem tanto.",
    ]
    return random.choice(quotes)


def calculate_health_score(state: dict, pending_items: list) -> tuple:
    """
    Calcula Health Score (0-100) com 5 componentes ponderados.

    Returns:
        tuple: (score, status_emoji, status_text, breakdown_dict)
    """
    breakdown = {}

    # Component 1: Progresso Geral (30pts)
    accumulated = state.get('accumulated', {})
    files_processed = accumulated.get('files', 0)
    # Dynamic: use total_files from state, fallback to files_processed if unknown
    total_files = state.get('total_files', accumulated.get('total_files', 0))
    if total_files <= 0:
        # If no total known, score based on whether any files were processed
        progress_score = min(30, 15) if files_processed > 0 else 0
    else:
        progress_score = min(30, (files_processed / total_files) * 30)
    breakdown['progresso'] = round(progress_score, 1)

    # Component 2: Fontes Completas (25pts)
    sources_status = state.get('sources_status', {})
    total_sources = len(sources_status) if sources_status else 1  # Dynamic from state
    sources_complete = sum(1 for s in sources_status.values() if s == 'COMPLETE')
    sources_score = (sources_complete / total_sources) * 25 if total_sources > 0 else 0
    breakdown['fontes'] = round(sources_score, 1)

    # Component 3: Pendências Baixas (20pts)
    # Conta prioridades: alta (-5), média (-2)
    high_priority = sum(1 for item in pending_items[:2])  # Primeiros 2 são alta
    medium_priority = sum(1 for item in pending_items[2:5])  # 3-5 são média
    pending_score = max(0, 20 - (high_priority * 5) - (medium_priority * 2))
    breakdown['pendencias'] = round(pending_score, 1)

    # Component 4: Estado Atualizado (15pts)
    last_updated_str = state.get('last_updated', '')
    state_score = 0
    if last_updated_str:
        try:
            last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            days_old = (datetime.now(last_updated.tzinfo) - last_updated).days if last_updated.tzinfo else (datetime.now() - datetime.fromisoformat(last_updated_str[:19])).days
            if days_old < 3:
                state_score = 15
            elif days_old < 7:
                state_score = 10
            else:
                state_score = 0
        except (ValueError, TypeError):
            state_score = 0
    breakdown['atualizacao'] = state_score

    # Component 5: Pipeline Limpo (10pts)
    pipeline = state.get('pipeline', {})
    errors_pending = pipeline.get('errors_pending', 0)
    pipeline_score = 10 if errors_pending == 0 else 0
    breakdown['pipeline'] = pipeline_score

    # Total Score
    total_score = int(progress_score + sources_score + pending_score + state_score + pipeline_score)

    # Determine status
    if total_score >= 90:
        status_emoji = "🟢"
        status_text = "EXCELLENT"
    elif total_score >= 70:
        status_emoji = "🔵"
        status_text = "GOOD"
    elif total_score >= 50:
        status_emoji = "🟡"
        status_text = "WARNING"
    elif total_score >= 30:
        status_emoji = "🟠"
        status_text = "CRITICAL"
    else:
        status_emoji = "🔴"
        status_text = "EMERGENCY"

    return (total_score, status_emoji, status_text, breakdown)


def _make_short_name(key: str, max_len: int = 3) -> str:
    """Generate a short display name from a source key."""
    # Use initials from underscore-separated parts
    parts = key.replace('-', '_').split('_')
    if len(parts) == 1:
        return parts[0][:max_len].upper()
    initials = ''.join(p[0].upper() for p in parts if p)
    return initials[:max_len].ljust(max_len)


def generate_source_matrix(state: dict) -> str:
    """
    Gera visualização da Source Matrix com barras de progresso.
    Dynamically reads sources from state['sources_status'].
    """
    sources_status = state.get('sources_status', {})

    if not sources_status:
        return "┌─ SOURCE MATRIX ─────────────────────────────────────────────────────────────────────────────────────────────────────┐\n│  No sources configured in state.                                                                                      │\n└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘"

    lines = []
    lines.append("┌─ SOURCE MATRIX ─────────────────────────────────────────────────────────────────────────────────────────────────────┐")

    # Encontrar fonte atual (IN_PROGRESS)
    current_source = None
    for key, status in sources_status.items():
        if status == 'IN_PROGRESS':
            current_source = key
            break

    for key, status in sources_status.items():
        short_name = _make_short_name(key)

        # Determinar percentual
        if status == 'COMPLETE':
            pct = 100
        elif status == 'IN_PROGRESS':
            # Check for source-specific progress in state
            progress_key = f'{key}_progress'
            source_prog = state.get(progress_key, {})
            processed = source_prog.get('valid_files_processed', source_prog.get('files_processed', 0))
            remaining = source_prog.get('valid_files_remaining', source_prog.get('files_remaining', 0))
            total = processed + remaining
            pct = int((processed / total) * 100) if total > 0 else 50
        else:
            pct = 0

        # Gerar barra (20 blocos)
        filled = int(pct / 5)
        empty = 20 - filled
        bar = "█" * filled + "░" * empty

        # Marcador de fonte atual
        current_marker = " ← CURRENT" if key == current_source else ""

        # Status text
        status_text = status.replace('_', ' ')

        # Formatar linha (padding para 120 chars)
        line_content = f"│  {short_name}[{bar}] {pct:3d}% {status_text}{current_marker}"
        padding = 119 - len(line_content)
        lines.append(f"{line_content}{' ' * max(1, padding)}│")

    lines.append("└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘")

    return "\n".join(lines)


def generate_briefing(compact: bool = False) -> str:
    """
    Gera o briefing completo na voz do Jarvis v2.0.

    Args:
        compact: Se True, gera versao resumida (status + proxima acao)

    Features v2.0:
        - Health Score (0-100) com 5 componentes
        - Source Matrix com barras de progresso
        - 120 caracteres de largura (padrao CHRONICLER)
    """
    # Carrega todos os dados
    state = load_state()
    pending_content = load_file('PENDING.md')
    memory_content = load_file('JARVIS-MEMORY.md')

    # Processa dados
    pending_items = extract_pending_items(pending_content)
    recent_changes = extract_recent_changes(memory_content)
    next_action = determine_next_action(state, pending_items)

    # Calcula Health Score
    health_score, health_emoji, health_status, health_breakdown = calculate_health_score(state, pending_items)

    # Metadata
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    greeting = get_greeting()

    # Status do projeto
    if 'mission' in state:
        mission = state['mission']
        project_status = mission.get('status', 'ACTIVE')
        current_phase = mission.get('phase', 1)
        subphase = mission.get('subphase', 1)
        batch_current = mission.get('batch', '?')
        batch_total = mission.get('total_batches', '?')
        progress = state.get('accumulated', {}).get('progress_percent', 0)
    else:
        project_status = 'ACTIVE'
        current_phase = 1
        subphase = 1
        batch_current = '?'
        batch_total = '?'
        progress = 0

    # === GERA BRIEFING ===
    if compact:
        # Versao compacta v2.0 (120 chars)
        # Barra de progresso visual (20 blocos)
        prog_filled = int(progress / 5)
        prog_empty = 20 - prog_filled
        prog_bar = "█" * prog_filled + "░" * prog_empty

        briefing = f"""
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    JARVIS BRIEFING v2.0 [COMPACT]                                                      │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  {greeting}, Senhor. Sao {timestamp}.                                                                                  │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  HEALTH: {health_emoji} {health_score:3d}/100 {health_status:<10} │ FASE: {current_phase}.{subphase} │ BATCH: {batch_current:>2}/{batch_total:<2} │ [{prog_bar}] {progress:>5.1f}%                   │
│  PENDENCIAS: {len(pending_items):<3} │ FONTES: {health_breakdown.get('fontes', 0):>4.1f}/25                                                                       │
├────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  PROXIMA ACAO: {next_action[:100]:<100} │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

_{get_jarvis_quote()}_
"""
        return briefing

    # Versao completa v2.0 com ASCII art (120 chars)
    briefing = """
╔════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                                        ║
║         ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗    ██████╗ ██████╗ ██╗███████╗███████╗██╗███╗   ██╗ ██████╗            ║
║         ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝    ██╔══██╗██╔══██╗██║██╔════╝██╔════╝██║████╗  ██║██╔════╝            ║
║         ██║███████║██████╔╝██║   ██║██║███████╗    ██████╔╝██████╔╝██║█████╗  █████╗  ██║██╔██╗ ██║██║  ███╗           ║
║    ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║    ██╔══██╗██╔══██╗██║██╔══╝  ██╔══╝  ██║██║╚██╗██║██║   ██║           ║
║    ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║    ██████╔╝██║  ██║██║███████╗██║     ██║██║ ╚████║╚██████╔╝           ║
║     ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝    ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝            ║
║                                                                                                                        ║
║                                              v2.0 ONLINE                                                               ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

    briefing += f"\n{greeting}, Senhor. Sao {timestamp}.\n\n"

    # HEALTH SCORE BOX
    briefing += f"""┌─ HEALTH SCORE ──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                        │
│                                          {health_emoji}  {health_score:3d} / 100  {health_status:<10}                                                      │
│                                                                                                                        │
│    Progresso:    {health_breakdown.get('progresso', 0):>5.1f} / 30 pts    │    Pendencias:    {health_breakdown.get('pendencias', 0):>5.1f} / 20 pts    │    Pipeline:    {health_breakdown.get('pipeline', 0):>5.1f} / 10 pts    │
│    Fontes:       {health_breakdown.get('fontes', 0):>5.1f} / 25 pts    │    Atualizacao:   {health_breakdown.get('atualizacao', 0):>5.1f} / 15 pts    │                                        │
│                                                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

"""

    # SOURCE MATRIX
    briefing += generate_source_matrix(state)
    briefing += "\n\n"

    # STATUS OPERACIONAL
    # Barra de progresso visual (20 blocos)
    prog_filled = int(progress / 5)
    prog_empty = 20 - prog_filled
    prog_bar = "█" * prog_filled + "░" * prog_empty

    briefing += f"""┌─ STATUS OPERACIONAL ────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                        │
│    Status:      {project_status:<20}    │    Fase:        {current_phase}.{subphase:<17}    │    Batch:       {batch_current}/{batch_total:<15}    │
│    Progresso:   [{prog_bar}] {progress:>5.1f}%                                                                         │
│    Pendencias:  {len(pending_items):<20}    │    Loops:       {len(recent_changes):<17}    │                                        │
│                                                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

"""

    # PENDENCIAS (Loops Abertos)
    briefing += """┌─ PENDENCIAS ────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
"""
    if pending_items:
        for i, item in enumerate(pending_items, 1):
            priority = "🔴" if i <= 2 else "🟡" if i <= 5 else "⚪"
            item_text = item[:100] + "..." if len(item) > 100 else item
            line = f"│  {priority} {i:>2}. {item_text}"
            padding = 120 - len(line)
            briefing += f"{line}{' ' * padding}│\n"
    else:
        briefing += "│  ✅ Nenhuma pendencia registrada. Sistema limpo.                                                                       │\n"
    briefing += """└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

"""

    # ULTIMAS IMPLEMENTACOES
    briefing += """┌─ ULTIMAS IMPLEMENTACOES ────────────────────────────────────────────────────────────────────────────────────────────────┐
"""
    if recent_changes:
        for change in recent_changes:
            change_text = change[:105] + "..." if len(change) > 105 else change
            line = f"│  ✓ {change_text}"
            padding = 120 - len(line)
            briefing += f"{line}{' ' * padding}│\n"
    else:
        briefing += "│  ℹ️ Sessao inicial. Nenhuma implementacao previa neste ciclo.                                                          │\n"
    briefing += """└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

"""

    # PROXIMA MELHOR ACAO (destaque especial)
    action_text = next_action[:108] if len(next_action) <= 108 else next_action[:105] + "..."
    briefing += f"""╔═ PROXIMA MELHOR ACAO ═══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                                        ║
║    ▶  {action_text:<112} ║
║                                                                                                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

"""

    # FOOTER
    briefing += f"""────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

_{get_jarvis_quote()}_

Aguardando instrucoes, Senhor.
"""

    return briefing


def save_briefing(briefing: str) -> Path:
    """Salva briefing em arquivo."""
    project_dir = get_project_dir()
    jarvis_dir = Path(project_dir) / '.claude' / 'jarvis'
    jarvis_dir.mkdir(parents=True, exist_ok=True)

    output_path = jarvis_dir / 'JARVIS-BRIEFING.md'
    output_path.write_text(briefing, encoding='utf-8')
    return output_path


def main():
    """Entry point quando executado diretamente."""
    import argparse

    parser = argparse.ArgumentParser(description='JARVIS Briefing Generator')
    parser.add_argument('--compact', '-c', action='store_true', help='Gerar versao compacta')
    parser.add_argument('--save', '-s', action='store_true', help='Salvar em arquivo')
    parser.add_argument('--quiet', '-q', action='store_true', help='Nao imprimir no stdout')
    args = parser.parse_args()

    briefing = generate_briefing(compact=args.compact)

    if args.save:
        saved_path = save_briefing(briefing)
        if not args.quiet:
            print(f"[JARVIS] Briefing salvo em: {saved_path}")

    if not args.quiet:
        print(briefing)

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
