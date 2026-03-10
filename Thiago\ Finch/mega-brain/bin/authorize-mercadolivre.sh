#!/bin/bash
# Script de autorização interativa para MercadoLivre

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║       AUTORIZAÇÃO MERCADOLIVRE - SISTEMA DE TOKEN AUTO-REFRESH        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar se estamos no diretório correto
if [ ! -f ".env" ]; then
    echo "❌ Erro: .env não encontrado. Execute este script da raiz do projeto:"
    echo "   cd mega-brain"
    echo "   bash bin/authorize-mercadolivre.sh"
    exit 1
fi

# Verificar credenciais básicas
if ! grep -q "MERCADOLIVRE_CLIENT_ID" .env; then
    echo "❌ Erro: MERCADOLIVRE_CLIENT_ID não está em .env"
    exit 1
fi

echo "📋 Credenciais carregadas do .env"
echo ""

# Executar autorização
cd "$(dirname "$0")/.."
python3 core/mcp/token_manager.py --authorize

if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ AUTORIZAÇÃO CONCLUÍDA                            ║"
    echo "╠════════════════════════════════════════════════════════════════════════╣"
    echo "║                                                                        ║"
    echo "║  ✓ Token salvo em: .claude/mission-control/ML-TOKEN-STATE.json        ║"
    echo "║  ✓ Renovação automática ativada (5 min antes de expirar)              ║"
    echo "║  ✓ Logs de rotação em: logs/ml-token-rotations.log                    ║"
    echo "║                                                                        ║"
    echo "║  🚀 Próximos passos:                                                   ║"
    echo "║     - A renovação automática iniciará na próxima sessão               ║"
    echo "║     - Nenhuma ação manual é necessária                                ║"
    echo "║     - Tokens são sincronizados entre sessões                          ║"
    echo "║                                                                        ║"
    echo "╚════════════════════════════════════════════════════════════════════════╝"
    echo ""
    exit 0
else
    echo ""
    echo "❌ Erro na autorização. Tente novamente."
    exit 1
fi
