# ⚡ Autorizar MercadoLivre - Guia Rápido

## 🎯 O Que Fazer

Sistema de auto-refresh está **100% implementado e pronto**. Falta apenas UMA coisa: fazer login no MercadoLivre e copiar o código de autorização.

---

## 📋 Passo 1: Abrir Link de Autorização

**Copie e abra este link no navegador:**

```
https://auth.mercadolibre.com.br/authorization?response_type=code&client_id=935927218612126&redirect_uri=https://hugojobs.co/
```

---

## 🔑 Passo 2: Fazer Login

1. Navegador vai abrir login do MercadoLivre
2. **Faça login com a conta Hugo Jobs**
3. Autorize o aplicativo (clicar em "Autorizar" ou similar)

---

## 📌 Passo 3: Copiar Código

Após fazer login, você será redirecionado para:

```
https://hugojobs.co/?code=TG5lQXVleV9kZXYxNzQzMTI2MTI2NV9jb2RlXzEyMzQ1Njc4OTA...
```

**Copie APENAS o valor do código:**
- Começa com `TG5l...`
- Pode ter até 100+ caracteres
- É único e válido por 1 hora

---

## 🤖 Passo 4: Usar o Token Manager

**Opção A (Interativa - terminal com input):**

```bash
python3 core/mcp/token_manager.py --authorize
```

Colar o código quando pedir.

**Opção B (CLI com argumento):**

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, 'core/mcp')
from token_manager import MercadoLivreTokenManager

manager = MercadoLivreTokenManager()
code = "COLE_O_CODIGO_AQUI"  # ← Substituir
success, msg = manager.refresh_token(authorization_code=code)
print(msg)
EOF
```

---

## ✅ Após Autorização

```bash
# Verificar status
python3 core/mcp/token_manager.py --status
```

Se retornar com `"status": "VALID"`, está pronto!

---

## 🚀 O Que Acontece Depois

1. ✅ Token salvo em `.claude/mission-control/ML-TOKEN-STATE.json` (gitignored)
2. ✅ Renovação automática em cada SessionStart
3. ✅ Nenhuma ação manual necessária
4. ✅ Logs de todas as rotações em `logs/ml-token-rotations.log`

---

## 🔍 Troubleshooting

### "Código inválido" ou "Autorização recusada"

Possíveis causas:
- Código copiado incorretamente
- Código expirou (válido por 1 hora)
- Conta errada (deve ser Hugo Jobs)

**Solução:** Voltar ao Passo 1 e repetir

### "Erro de conexão"

- Verifique internet
- Tente novamente
- Se persistir, veja: `.claude/mission-control/ML-TOKEN-README.md`

### "Token renovado, mas não funciona"

Execute:
```bash
python3 core/mcp/token_manager.py --status
```

Deve mostrar:
```json
{
  "status": "VALID",
  "expires_at": "2026-03-10T12:45:30...",
  "expires_in_seconds": 604800
}
```

---

## 📊 Resumo do Sistema

```
┌─────────────────────────────────────────────────────┐
│  AUTORIZAÇÃO                                        │
│  (Você faz UMA VEZ)                                 │
│  ↓ ↓ ↓                                              │
│  Token armazenado em .json (gitignored)             │
│  ↓ ↓ ↓                                              │
│  HOOK (SessionStart)                                │
│  ├─ Verifica se token está válido                   │
│  ├─ Se expirado → Renova automaticamente            │
│  └─ Sem fazer nada manualmente                      │
│  ↓ ↓ ↓                                              │
│  APIs funcionando! 🎉                               │
└─────────────────────────────────────────────────────┘
```

---

## 📞 Resumo dos Comandos

| Ação | Comando |
|------|---------|
| **Autorizar (1ª vez)** | `python3 core/mcp/token_manager.py --authorize` |
| **Ver status** | `python3 core/mcp/token_manager.py --status` |
| **Renovar manualmente** | `python3 core/mcp/token_manager.py --refresh` |
| **Ver logs** | `tail -20 logs/ml-token-rotations.log` |

---

**Status:** 🟡 Aguardando autorização
**Próximo passo:** Abrir link acima e fazer login
**Tempo estimado:** 2-3 minutos

---

*Após autorizar, você nunca mais perderá token. Renovação automática a partir de então.*
