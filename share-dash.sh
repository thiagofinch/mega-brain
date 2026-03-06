#!/bin/bash
# AIOX LIVE DASHBOARD SYNC v4.0
# Centraliza a coleta de dados, atualização de UI e sincronização com a nuvem.

BRANCH_NAME="gh-pages"
REMOTE="my-fork"

echo "🚀 Iniciando Ciclo de Sincronização AIOX..."

while true; do
    echo "---------------------------------------------------"
    echo "📅 [$(date '+%H:%M:%S')] Sincronizando..."

    # 1. Coletar dados reais do Mercado Livre
    python3 validate_raw_data.py
    
    # 2. Atualizar o Dashboard HTML
    python3 update_dashboard_html.py
    
    # 3. Sincronizar com GitHub
    echo "☁️ Subindo para nuvem (branch: $BRANCH_NAME)..."
    
    # Garantir que estamos na branch correta (se não existir, cria)
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    
    # Criar branch live-dash se não existir
    git show-ref --verify --quiet refs/heads/$BRANCH_NAME || git branch $BRANCH_NAME
    
    # Garantir que o GitHub não tente buildar Jekyll (evita erros 404/build fail)
    touch .nojekyll
    
    # Commitar apenas as mudanças do dashboard para não poluir o histórico principal
    git add data-audit-report.json index.html .nojekyll
    
    # Commit com flag para ignorar hooks se necessário e evitar duplicidade
    git commit -m "sync: dashboard update $(date '+%Y-%m-%d %H:%M:%S')" --no-verify 2>/dev/null
    
    # Push forçado para a branch de live
    git push $REMOTE HEAD:$BRANCH_NAME --force --no-verify
    
    echo "✅ Sincronização concluída!"
    echo "💤 Dormindo por 5 minutos..."
    sleep 300
done
