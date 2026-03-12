#!/usr/bin/env python3
"""
GITHUB ACTIONS DIAGNOSTIC
=========================
Diagnóstico automático de falhas em GitHub Actions.

Usage:
    python3 gha_diagnostic.py              # Último run com falha
    python3 gha_diagnostic.py [run_id]     # Run específico
    python3 gha_diagnostic.py --flaky      # Testes flaky
    python3 gha_diagnostic.py --history    # Histórico
"""

import sys
import subprocess
import json
import re
from datetime import datetime


def run_gh(args: list) -> tuple[bool, str]:
    """Execute gh CLI command"""
    try:
        result = subprocess.run(
            ['gh'] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except Exception as e:
        return False, str(e)


def get_failed_runs(limit: int = 5) -> list:
    """Get recent failed runs"""
    success, output = run_gh([
        'run', 'list',
        '--status', 'failure',
        '--limit', str(limit),
        '--json', 'databaseId,name,conclusion,createdAt,headBranch'
    ])

    if success:
        try:
            return json.loads(output)
        except:
            pass
    return []


def get_run_logs(run_id: str) -> str:
    """Get logs for a specific run"""
    success, output = run_gh(['run', 'view', run_id, '--log'])
    if success:
        return output
    return f"Error getting logs: {output}"


def get_run_details(run_id: str) -> dict:
    """Get detailed info about a run"""
    success, output = run_gh([
        'run', 'view', run_id,
        '--json', 'databaseId,name,conclusion,createdAt,headBranch,jobs'
    ])

    if success:
        try:
            return json.loads(output)
        except:
            pass
    return {}


def analyze_logs(logs: str) -> dict:
    """Analyze logs to find root cause"""
    analysis = {
        'error_type': 'Unknown',
        'error_message': '',
        'file': '',
        'line': '',
        'suggestion': ''
    }

    # Common patterns
    patterns = [
        # Test failures
        (r'FAIL\s+(.+\.test\.[jt]sx?)', 'Test Failure', 'Verificar o teste indicado'),
        (r'AssertionError:\s*(.+)', 'Assertion Failed', 'Verificar expectativa do teste'),
        (r'Expected:\s*(.+)\s*Received:\s*(.+)', 'Assertion Mismatch', 'Valores não correspondem'),

        # TypeScript errors
        (r'error TS\d+:\s*(.+)', 'TypeScript Error', 'Corrigir tipo no código'),
        (r"Property '(\w+)' does not exist", 'Missing Property', 'Adicionar propriedade ao tipo'),

        # Build errors
        (r'npm ERR!\s*(.+)', 'NPM Error', 'Verificar dependências, rodar npm ci'),
        (r'Module not found:\s*(.+)', 'Module Not Found', 'Instalar módulo faltante'),

        # ESLint
        (r'error\s+(.+)\s+@typescript-eslint', 'ESLint Error', 'Corrigir lint error'),

        # Generic errors
        (r'Error:\s*(.+)', 'Generic Error', 'Ver stack trace para mais detalhes'),
        (r'ENOENT.*?([^\s]+)', 'File Not Found', 'Verificar se arquivo existe'),
        (r'timeout', 'Timeout', 'Aumentar timeout ou otimizar'),
    ]

    for pattern, error_type, suggestion in patterns:
        match = re.search(pattern, logs, re.IGNORECASE)
        if match:
            analysis['error_type'] = error_type
            analysis['error_message'] = match.group(1) if match.groups() else match.group(0)
            analysis['suggestion'] = suggestion
            break

    # Try to find file:line reference
    file_match = re.search(r'([^\s]+\.[jt]sx?):(\d+)', logs)
    if file_match:
        analysis['file'] = file_match.group(1)
        analysis['line'] = file_match.group(2)

    return analysis


def print_diagnostic(run_id: str):
    """Print full diagnostic for a run"""
    details = get_run_details(run_id)
    logs = get_run_logs(run_id)
    analysis = analyze_logs(logs)

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GITHUB ACTIONS DIAGNOSTIC                                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣""")

    if details:
        name = details.get('name', 'Unknown')[:60]
        branch = details.get('headBranch', 'Unknown')[:30]
        conclusion = details.get('conclusion', 'Unknown')

        print(f"║  Run ID:      {run_id:<62} ║")
        print(f"║  Workflow:    {name:<62} ║")
        print(f"║  Branch:      {branch:<62} ║")
        print(f"║  Status:      {conclusion:<62} ║")

    print("╠══════════════════════════════════════════════════════════════════════════════╣")
    print("║  ANÁLISE:                                                                    ║")
    print(f"║  Tipo:        {analysis['error_type']:<62} ║")

    if analysis['error_message']:
        msg = analysis['error_message'][:60]
        print(f"║  Erro:        {msg:<62} ║")

    if analysis['file']:
        loc = f"{analysis['file']}:{analysis['line']}"[:60]
        print(f"║  Local:       {loc:<62} ║")

    print("║                                                                              ║")
    print("║  SUGESTÃO:                                                                   ║")
    suggestion = analysis['suggestion'][:70]
    print(f"║  {suggestion:<76} ║")

    print("╚══════════════════════════════════════════════════════════════════════════════╝")

    # Print relevant log snippet
    if analysis['error_message']:
        print("\n📋 LOG RELEVANTE:")
        print("-" * 80)
        # Find context around error
        lines = logs.split('\n')
        for i, line in enumerate(lines):
            if analysis['error_message'][:30] in line:
                start = max(0, i - 5)
                end = min(len(lines), i + 10)
                print('\n'.join(lines[start:end]))
                break
        print("-" * 80)


def main():
    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        print(__doc__)
        return

    # Check gh CLI
    success, _ = run_gh(['--version'])
    if not success:
        print("❌ GitHub CLI (gh) not installed or not authenticated")
        print("   Install: brew install gh")
        print("   Auth: gh auth login")
        return

    if '--history' in args:
        print("📊 Histórico de falhas recentes:\n")
        runs = get_failed_runs(10)
        for run in runs:
            print(f"  • {run['databaseId']} - {run['name']} ({run['headBranch']})")
        return

    if '--flaky' in args:
        print("🔍 Analisando testes flaky...\n")
        # Get recent runs and look for intermittent failures
        runs = get_failed_runs(20)
        print(f"  {len(runs)} falhas nas últimas 20 runs")
        # Could do more sophisticated analysis here
        return

    # Get specific run or latest failed
    if args and args[0].isdigit():
        run_id = args[0]
    else:
        runs = get_failed_runs(1)
        if not runs:
            print("✅ Nenhuma falha recente encontrada!")
            return
        run_id = str(runs[0]['databaseId'])

    print_diagnostic(run_id)


if __name__ == '__main__':
    main()
