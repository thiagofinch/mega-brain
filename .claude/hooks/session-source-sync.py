#!/usr/bin/env python3
"""
SESSION SOURCE SYNC HOOK
========================

Hook executado no início de cada sessão para verificar:
1. Se há delta pendente de sincronização
2. Se última sincronização está muito antiga (>7 dias)
3. Se há arquivos no INBOX sem TAG

Alertas são exibidos no início da sessão para lembrar o usuário.

Autor: JARVIS
Versão: 1.0.0
Data: 2026-01-13
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

# Fix Windows cp1252 encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# =================================
# CONFIGURAÇÃO
# =================================

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
MISSION_CONTROL = PROJECT_ROOT / ".claude" / "mission-control"
INBOX_ROOT = PROJECT_ROOT / "inbox"

SYNC_STATE_FILE = MISSION_CONTROL / "SOURCE-SYNC-STATE.json"
DELTA_PENDING_FILE = MISSION_CONTROL / "DELTA-PENDING.json"

# Configuração de alertas
STALE_THRESHOLD_DAYS = 7  # Dias sem sync para considerar "stale"

# =================================
# FUNÇÕES AUXILIARES
# =================================


def load_json(path: Path) -> dict:
    """Carrega arquivo JSON com tratamento de erro."""
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def days_since(iso_timestamp: str) -> int:
    """Calcula dias desde um timestamp ISO."""
    if not iso_timestamp:
        return 999  # Muito tempo
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        delta = datetime.now(dt.tzinfo) - dt if dt.tzinfo else datetime.now() - dt
        return delta.days
    except (ValueError, TypeError):
        return 999


def count_untagged_inbox_files() -> int:
    """Conta arquivos no INBOX que não têm TAG."""
    untagged = 0
    if not INBOX_ROOT.exists():
        return 0

    for root, dirs, files in os.walk(INBOX_ROOT):
        for f in files:
            # Ignora arquivos do sistema
            if f.startswith(".") or f.endswith(".md"):
                continue
            # Verifica se tem TAG [XX-XXXX]
            if not f.startswith("["):
                untagged += 1

    return untagged


# =================================
# FUNÇÕES DE VERIFICAÇÃO
# =================================


def check_pending_delta() -> tuple[bool, int, str]:
    """
    Verifica se há delta pendente.

    Returns:
        (has_pending, count, timestamp)
    """
    delta = load_json(DELTA_PENDING_FILE)
    total = delta.get("total", 0)
    timestamp = delta.get("timestamp", "")

    return total > 0, total, timestamp


def check_stale_sync() -> tuple[bool, int]:
    """
    Verifica se última sincronização está muito antiga.

    Returns:
        (is_stale, days_since_sync)
    """
    state = load_json(SYNC_STATE_FILE)
    last_sync = state.get("last_sync", "")
    days = days_since(last_sync)

    return days > STALE_THRESHOLD_DAYS, days


def check_untagged_files() -> tuple[bool, int]:
    """
    Verifica arquivos no INBOX sem TAG.

    Returns:
        (has_untagged, count)
    """
    count = count_untagged_inbox_files()
    return count > 0, count


# =================================
# GERAÇÃO DE ALERTAS
# =================================


def generate_alerts() -> list[dict]:
    """Gera lista de alertas baseado nas verificações."""
    alerts = []

    # 1. Delta pendente
    has_pending, count, timestamp = check_pending_delta()
    if has_pending:
        alerts.append(
            {
                "type": "PENDING_DELTA",
                "severity": "HIGH",
                "message": f"{count} arquivos NOVOS detectados aguardando download",
                "action": "Execute /source-sync --execute para processar",
                "timestamp": timestamp,
            }
        )

    # 2. Sync antigo
    is_stale, days = check_stale_sync()
    if is_stale:
        alerts.append(
            {
                "type": "STALE_SYNC",
                "severity": "MEDIUM",
                "message": f"Última sincronização há {days} dias",
                "action": "Execute /source-sync --check para verificar novos conteúdos",
            }
        )

    # 3. Arquivos sem TAG
    has_untagged, count = check_untagged_files()
    if has_untagged:
        alerts.append(
            {
                "type": "UNTAGGED_FILES",
                "severity": "LOW",
                "message": f"{count} arquivos no INBOX sem TAG",
                "action": "Execute Fase 2.5 ou /source-sync para tagueamento",
            }
        )

    return alerts


def print_alerts(alerts: list[dict]) -> None:
    """Exibe alertas no formato visual."""
    if not alerts:
        return

    print()
    print("┌" + "─" * 78 + "┐")
    print("│" + "SOURCE SYNC - ALERTAS DE SESSÃO".center(78) + "│")
    print("├" + "─" * 78 + "┤")

    for alert in alerts:
        severity_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(alert["severity"], "⚪")

        print(f"│  [{alert['type']}]" + " " * (68 - len(alert["type"])) + "│")
        print(f"│    {severity_icon} {alert['message']:<73}│")
        print(f"│    → {alert['action']:<72}│")
        print("│" + " " * 78 + "│")

    print("└" + "─" * 78 + "┘")
    print()


def get_alerts_json() -> str:
    """Retorna alertas em formato JSON para integração."""
    alerts = generate_alerts()
    return json.dumps(
        {"timestamp": datetime.now().isoformat(), "alerts": alerts, "count": len(alerts)},
        ensure_ascii=False,
        indent=2,
    )


# =================================
# MAIN
# =================================


def main():
    """Executa verificação e exibe alertas."""
    alerts = generate_alerts()

    if alerts:
        print_alerts(alerts)
    else:
        print("\n✅ SOURCE SYNC: Nenhum alerta pendente.\n")

    # SEMPRE exit 0 - alertas são informativos, não erros
    # Exit code != 0 bloqueia operações do Claude Code
    sys.exit(0)


if __name__ == "__main__":
    # Verifica se deve retornar JSON
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print(get_alerts_json())
    else:
        main()
