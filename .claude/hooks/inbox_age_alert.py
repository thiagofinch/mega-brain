#!/usr/bin/env python3
"""
INBOX AGE ALERT HOOK - REGRA #7 ENFORCEMENT
============================================

Alerta sobre arquivos antigos no INBOX no inicio de cada sessao.

REGRA #7: INBOX E TEMPORARIO
- NAO PODE deixar arquivos no INBOX indefinidamente
- NAO PODE mover para INBOX sem plano de organizacao
- DEVE organizar cada arquivo que entra no INBOX

Este hook:
1. Executa no inicio de cada sessao (session_start hook)
2. Verifica arquivos no INBOX com mais de 3 dias
3. Se encontrar, gera alerta formatado para o JARVIS exibir
4. Loga em /logs/inbox_alerts.jsonl

Autor: JARVIS Autonomous System
Data: 2026-01-11
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

***REMOVED***==================================
# CONFIGURACAO
***REMOVED***==================================

PROJECT_ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))
INBOX_PATH = PROJECT_ROOT / "inbox"
MAX_AGE_DAYS = 3
ALERT_LOG = PROJECT_ROOT / "logs" / "inbox_alerts.jsonl"

# Extensoes de arquivos para monitorar
MONITORED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf", ".json", ".yaml", ".yml"}

# Pastas/prefixos a ignorar
IGNORE_PREFIXES = {"_", ".", "__"}
IGNORE_FOLDERS = {"_BACKUP", "_OLD", "_ARCHIVE", "__pycache__"}


***REMOVED***==================================
# FUNCOES PRINCIPAIS
***REMOVED***==================================


def get_old_files(max_age_days: int = MAX_AGE_DAYS) -> List[Dict]:
    """
    Retorna lista de arquivos mais velhos que max_age_days.

    Args:
        max_age_days: Numero maximo de dias que um arquivo pode ficar no INBOX

    Returns:
        Lista de dicts com informacoes dos arquivos antigos
    """
    old_files = []
    cutoff = datetime.now() - timedelta(days=max_age_days)

    if not INBOX_PATH.exists():
        return []

    for root, dirs, files in os.walk(INBOX_PATH):
        # Ignorar pastas de backup e ocultas
        dirs[:] = [
            d
            for d in dirs
            if not any(d.startswith(p) for p in IGNORE_PREFIXES)
            and d not in IGNORE_FOLDERS
        ]

        for f in files:
            # Ignorar arquivos ocultos
            if any(f.startswith(p) for p in IGNORE_PREFIXES):
                continue

            # Verificar extensao
            ext = Path(f).suffix.lower()
            if ext not in MONITORED_EXTENSIONS:
                continue

            try:
                fpath = Path(root) / f
                mtime = datetime.fromtimestamp(fpath.stat().st_mtime)

                if mtime < cutoff:
                    # Calcular caminho relativo ao INBOX
                    rel_path = fpath.relative_to(INBOX_PATH)
                    folder = rel_path.parent if rel_path.parent != Path(".") else "ROOT"

                    old_files.append(
                        {
                            "path": str(fpath),
                            "relative_path": str(rel_path),
                            "name": f,
                            "age_days": (datetime.now() - mtime).days,
                            "folder": str(folder),
                            "size_kb": round(fpath.stat().st_size / 1024, 2),
                            "modified_at": mtime.isoformat(),
                        }
                    )
            except (OSError, PermissionError) as e:
                # Ignorar arquivos inacessiveis
                continue

    return sorted(old_files, key=lambda x: x["age_days"], reverse=True)


def count_by_folder(old_files: List[Dict]) -> Dict[str, int]:
    """Agrupa arquivos antigos por pasta."""
    folder_counts = {}
    for f in old_files:
        folder = f["folder"]
        folder_counts[folder] = folder_counts.get(folder, 0) + 1
    return dict(sorted(folder_counts.items(), key=lambda x: x[1], reverse=True))


def generate_alert(old_files: List[Dict]) -> str:
    """
    Gera mensagem de alerta formatada no estilo JARVIS.

    Args:
        old_files: Lista de arquivos antigos

    Returns:
        String formatada com o alerta
    """
    if not old_files:
        return ""

    folder_counts = count_by_folder(old_files)
    total_size = sum(f["size_kb"] for f in old_files)

    # Construir alerta visual
    alert = f"""
+==============================================================================+
|                    REGRA #7 ALERTA - INBOX TEMPORARIO                        |
+==============================================================================+

ATENCAO, senhor. {len(old_files)} arquivo(s) no INBOX com mais de {MAX_AGE_DAYS} dias.

+------------------------------------------------------------------------------+
|  METRICAS                                                                    |
+------------------------------------------------------------------------------+
|  Total de arquivos antigos:  {len(old_files):>4}                                            |
|  Tamanho total:              {total_size:>8.1f} KB                                       |
|  Arquivo mais antigo:        {old_files[0]["age_days"]:>4} dias                                         |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
|  POR PASTA                                                                   |
+------------------------------------------------------------------------------+
"""

    for folder, count in list(folder_counts.items())[:8]:
        folder_display = folder[:40] if len(folder) <= 40 else folder[:37] + "..."
        alert += f"|  {folder_display:<42} {count:>3} arquivo(s)                   |\n"

    if len(folder_counts) > 8:
        alert += f"|  ... e mais {len(folder_counts) - 8} pastas                                                   |\n"

    alert += """+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
|  ARQUIVOS MAIS ANTIGOS                                                       |
+------------------------------------------------------------------------------+
"""

    for f in old_files[:10]:
        name_display = (
            f["name"][:50] if len(f["name"]) <= 50 else f["name"][:47] + "..."
        )
        alert += f"|  [{f['age_days']:>3}d] {name_display:<50}      |\n"

    if len(old_files) > 10:
        alert += f"|  ... e mais {len(old_files) - 10} arquivos                                                   |\n"

    alert += """+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
|  ACAO RECOMENDADA                                                            |
+------------------------------------------------------------------------------+
|  Executar: python3 SCRIPTS/organize_inbox_to_knowledge.py --execute          |
|  Ou:       /inbox para ver lista completa                                    |
+------------------------------------------------------------------------------+

REGRA #7: INBOX E TEMPORARIO - Organizar, nao acumular.
"""

    return alert


def generate_summary(old_files: List[Dict]) -> str:
    """Gera resumo curto para o contexto do JARVIS."""
    if not old_files:
        return ""

    return f"REGRA #7: {len(old_files)} arquivo(s) antigos no INBOX (>{MAX_AGE_DAYS} dias). Mais antigo: {old_files[0]['age_days']} dias."


def log_alert(old_files: List[Dict]) -> bool:
    """
    Loga alerta em jsonl para historico.

    Args:
        old_files: Lista de arquivos antigos

    Returns:
        True se logou com sucesso
    """
    try:
        # Garantir que diretorio existe
        ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "alert_type": "inbox_age",
            "rule": "REGRA_7",
            "total_files": len(old_files),
            "max_age_days_threshold": MAX_AGE_DAYS,
            "oldest_file_days": old_files[0]["age_days"] if old_files else 0,
            "folders_affected": count_by_folder(old_files),
            "files": old_files[:20],  # Limitar a 20 arquivos no log
            "action_suggested": "python3 SCRIPTS/organize_inbox_to_knowledge.py --execute",
        }

        with open(ALERT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return True

    except Exception as e:
        # Nao bloquear execucao por falha de log
        sys.stderr.write(f"[INBOX_ALERT] Erro ao logar: {e}\n")
        return False


def check_inbox_health() -> Dict:
    """
    Verifica saude geral do INBOX.

    Returns:
        Dict com metricas de saude
    """
    if not INBOX_PATH.exists():
        return {"status": "error", "message": "INBOX path not found"}

    total_files = 0
    total_size = 0

    for root, dirs, files in os.walk(INBOX_PATH):
        # Ignorar pastas de backup
        dirs[:] = [
            d
            for d in dirs
            if not any(d.startswith(p) for p in IGNORE_PREFIXES)
            and d not in IGNORE_FOLDERS
        ]

        for f in files:
            if any(f.startswith(p) for p in IGNORE_PREFIXES):
                continue
            try:
                fpath = Path(root) / f
                total_files += 1
                total_size += fpath.stat().st_size
            except:
                continue

    old_files = get_old_files()

    # Determinar status
    if len(old_files) == 0:
        status = "healthy"
    elif len(old_files) < 10:
        status = "warning"
    else:
        status = "critical"

    return {
        "status": status,
        "total_files": total_files,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "old_files_count": len(old_files),
        "oldest_file_days": old_files[0]["age_days"] if old_files else 0,
        "threshold_days": MAX_AGE_DAYS,
    }


***REMOVED***==================================
# INTEGRACAO COM SESSION_START
***REMOVED***==================================


def get_session_context(old_files: List[Dict]) -> Dict:
    """
    Retorna contexto para integracao com session_start.

    Args:
        old_files: Lista de arquivos antigos

    Returns:
        Dict com contexto para o JARVIS
    """
    if not old_files:
        return {"has_alert": False, "summary": "", "alert": ""}

    return {
        "has_alert": True,
        "summary": generate_summary(old_files),
        "alert": generate_alert(old_files),
        "file_count": len(old_files),
        "oldest_days": old_files[0]["age_days"],
        "health": check_inbox_health(),
    }


***REMOVED***==================================
# MAIN
***REMOVED***==================================


def main():
    """
    Hook entry point for Claude Code SessionStart event.
    Reads JSON from stdin, outputs JSON to stdout.
    """
    try:
        input_data = sys.stdin.read()
        hook_input = json.loads(input_data) if input_data else {}

        old_files = get_old_files()

        if old_files:
            log_alert(old_files)
            summary = generate_summary(old_files)
            print(json.dumps({'continue': True, 'feedback': summary}))
        else:
            print(json.dumps({'continue': True}))

    except Exception:
        print(json.dumps({'continue': True}))


def cli_test():
    """CLI test mode - run directly for debugging."""
    old_files = get_old_files()
    if old_files:
        alert = generate_alert(old_files)
        print(alert)
    else:
        print("[INBOX_ALERT] No old files found. INBOX is clean.")

    health = check_inbox_health()
    print(f"\nHealth: {json.dumps(health, indent=2)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        cli_test()
    else:
        main()
