# MercadoLivre Token Management System

## 📋 Visão Geral

Sistema robusto de gerenciamento de tokens OAuth 2.0 do MercadoLivre com:
- ✅ **Auto-refresh automático** (5 min antes de expirar)
- ✅ **Persistência segura** (arquivo JSON gitignored)
- ✅ **Retry com backoff exponencial** (3 tentativas)
- ✅ **Health check automático** (SessionStart hook)
- ✅ **Logging completo** (auditoria de rotações)

## 🔐 Autorização Inicial

### Passo 1: Executar Script de Autorização

```bash
# Da raiz do projeto:
python3 core/mcp/token_manager.py --authorize

# Ou usando o script shell:
bash authorize-ml.sh
```

### Passo 2: Fazer Login

Um link será exibido. Copie e abra no navegador com sua conta Hugo Jobs:

```
https://auth.mercadolibre.com.br/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://hugojobs.co/
```

### Passo 3: Copiar Código de Autorização

Após fazer login, você será redirecionado para uma URL similar a:

```
https://hugojobs.co/?code=TG5lQXVleV9kZXYxNzQzMTI2MTI2NV8xMjM0NTY3ODkwYWJjZGVm...
```

**Copie apenas o valor do `code`** e cole no prompt.

### Passo 4: Confirmação

Se tudo funcionou, você verá:

```
✅ Token renovado com sucesso. Expira em: 2026-03-10T12:45:30.123456
```

## 📂 Arquivos do Sistema

| Arquivo | Propósito | Gitignored |
|---------|-----------|------------|
| `.claude/mission-control/ML-TOKEN-STATE.json` | Estado atual do token | ✅ Sim |
| `logs/ml-token-rotations.log` | Auditoria de renovações | ✅ Sim |
| `core/mcp/token_manager.py` | Gerenciador de tokens | ❌ Não |
| `.claude/hooks/ml_token_health.py` | Health check | ❌ Não |

## 🤖 Fluxo Automático

```
SessionStart
    ↓
ml_token_health.py hook executa
    ↓
┌─────────────────────────────────┐
│ Token válido por > 5 min?       │
│ └─ SIM → Sessão continua        │
│ └─ NÃO → Tenta renovar          │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ Renovação bem-sucedida?         │
│ └─ SIM → Log de sucesso         │
│ └─ NÃO → Aviso (sem bloqueio)   │
└─────────────────────────────────┘
    ↓
Sessão continua normalmente
```

## 🔧 Comandos Disponíveis

### Verificar Status

```bash
python3 core/mcp/token_manager.py --status
```

**Saída:**
```json
{
  "status": "VALID",
  "access_token": "APP_USR-935927218612...",
  "expires_at": "2026-03-10T12:45:30.123456",
  "expires_in_seconds": 72000,
  "last_refresh": "2026-03-03T12:45:30.123456",
  "refresh_token_available": true
}
```

### Renovar Manualmente

```bash
python3 core/mcp/token_manager.py --refresh
```

Útil para:
- Forçar renovação antes de expirar
- Testes de renovação
- Recuperação de falhas

### Autorizar Novamente

```bash
python3 core/mcp/token_manager.py --authorize
```

Execute se:
- O refresh_token foi revogado
- Mudança de credenciais
- Reset completo necessário

## 🚨 Troubleshooting

### "Token inválido - 401 Unauthorized"

**Causa:** Token expirou e refresh_token não é válido

**Solução:**
```bash
python3 core/mcp/token_manager.py --authorize
```

### "Nenhum refresh_token disponível"

**Causa:** Arquivo de estado corrompido ou primeiro acesso

**Solução:**
```bash
# Remover arquivo de estado
rm .claude/mission-control/ML-TOKEN-STATE.json

# Autorizar novamente
python3 core/mcp/token_manager.py --authorize
```

### "Timeout na renovação"

**Causa:** Problema de conexão com OAuth MercadoLivre

**Diagnóstico:**
```bash
# Verificar conectividade
curl -I https://auth.mercadolibre.com.br/

# Logs de tentativas
tail -20 logs/ml-token-rotations.log
```

### "MERCADOLIVRE_CLIENT_ID não encontrado"

**Causa:** Variáveis não configuradas em .env

**Solução:** Verificar arquivo `.env` contém:
```
MERCADOLIVRE_CLIENT_ID=935927218612126
MERCADOLIVRE_CLIENT_SECRET=6COi3Vk5e5z2uIsrNt4u...
MERCADOLIVRE_REDIRECT_URL=https://hugojobs.co/
```

## 📊 Monitoramento

### Ver Histórico de Rotações

```bash
tail -50 logs/ml-token-rotations.log
```

### Verificar Próxima Renovação

```bash
python3 -c "
import json
from datetime import datetime
from pathlib import Path

state = json.load(open('.claude/mission-control/ML-TOKEN-STATE.json'))
expires = datetime.fromisoformat(state['expires_at'])
now = datetime.now()
remaining = expires - now

print(f'Token expira em: {remaining.total_seconds() / 3600:.1f} horas')
"
```

## 🔄 Integração com APIs

### Usar Token em Requisições Manuais

```python
from core.mcp.token_manager import MercadoLivreTokenManager

manager = MercadoLivreTokenManager()
token = manager.get_valid_token()  # Auto-renova se necessário

# Usar token em requisição
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("https://api.mercadolibre.com/users/me", headers=headers)
```

### Usar com MCP

O MCP do MercadoLivre usará automaticamente o TokenManager:

```bash
python3 core/mcp/mercadolivre_mcp.py
```

## 🛡️ Segurança

| Medida | Implementação |
|--------|---------------|
| **Tokens armazenados** | Arquivo local, não em .env |
| **Arquivo gitignored** | Nunca entra no git |
| **Refresh automático** | Evita tokens expirados |
| **Retry com backoff** | Proteção contra rate limiting |
| **Logging de auditoria** | Rastreamento completo |

## 📝 Logs

### Formato de Log

```
[2026-03-03T12:45:30.123456] ✅ Token renovado com sucesso. Expira em: 2026-03-10T12:45:30.123456
[2026-03-03T13:00:00.000000] 🔄 Renovando token...
[2026-03-03T13:00:05.000000] ✅ Token renovado com sucesso. Expira em: 2026-03-10T13:00:05.000000
```

### Entradas de Log por Status

- ✅ `✅ Token renovado` - Renovação bem-sucedida
- 🔄 `🔄 Renovando token` - Tentativa de renovação
- 🔄 `🔄 Iniciando autorização` - Primeiro acesso
- ⏳ `⏳ Tentativa X/3` - Retry em andamento
- ❌ `❌ Erro` - Falha de renovação

## 🚀 Próximas Sessões

Nenhuma ação necessária! O sistema:

1. ✅ Verifica token na SessionStart
2. ✅ Renova automaticamente se expirado
3. ✅ Registra tudo em logs
4. ✅ Está pronto para APIs

---

**Última atualização:** 2026-03-03
**Versão:** 1.0.0
**Status:** ✅ Produção
