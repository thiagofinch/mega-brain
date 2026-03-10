# MercadoLivre Token Setup - Checklist

## Status: ✅ IMPLEMENTADO

### ✅ Componentes Instalados

- [x] `core/mcp/token_manager.py` - Gerenciador de tokens OAuth
- [x] `.claude/hooks/ml_token_health.py` - Health check SessionStart
- [x] `.claude/settings.local.json` - Configuração de hooks
- [x] `authorize-ml.sh` - Script de autorização
- [x] `.claude/mission-control/ML-TOKEN-README.md` - Documentação

### ✅ Funcionalidades

- [x] Auto-refresh antes de expirar (5 min buffer)
- [x] Persistência segura em JSON (gitignored)
- [x] Retry automático com backoff exponencial (3 tentativas)
- [x] Health check automático (SessionStart hook)
- [x] Logging completo de rotações

### 📋 Próxima Ação

**Execute a autorização inicial:**

```bash
python3 core/mcp/token_manager.py --authorize
```

Ou:

```bash
bash authorize-ml.sh
```

### 🎯 O que Acontece

1. Abre link de OAuth do MercadoLivre
2. Você faz login com Hugo Jobs
3. Copia código de autorização
4. Token é salvo e verificado
5. ✅ Pronto!

### 🚀 Depois da Autorização

- Sessões futuras: Renovação automática
- Sem ação manual necessária
- Logs em: `logs/ml-token-rotations.log`
- Status: `python3 core/mcp/token_manager.py --status`

### ⚠️ Se Falhar

Veja: `.claude/mission-control/ML-TOKEN-README.md` seção "Troubleshooting"

---

**Status:** 🟢 Pronto para autorização
**Data:** 2026-03-03
