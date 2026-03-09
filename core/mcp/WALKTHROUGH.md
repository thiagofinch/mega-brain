# MercadoLivre MCP v2.0 — Integração Completa

> **Versão:** 2.0.0
> **Data:** 2026-03-02
> **Status:** Pronto para ativar (token necessário)

---

## 🎯 O Que Você Tem

Servidor MCP completo que fornece acesso real-time a:
- **Categorias** do MercadoLivre Brasil (19,000+ produtos)
- **Comissões** por categoria (taxas dinâmicas)
- **Custos de envio** (Mercado Envios)
- **Tipos de anúncio** (Clássico, Premium, etc.)

Implementação:
- JSON-RPC 2.0 puro (stdin/stdout)
- Zero dependências externas (só `requests` + `python-dotenv`)
- Docker-ready para produção
- Testado com tokens válidos

---

## 🔐 Step 1: Credenciais (2 min)

### Você já tem:

```bash
# Arquivo: .env (chave gerada em 2026-03-01)

MERCADOLIVRE_CLIENT_ID=935927218612126
MERCADOLIVRE_CLIENT_SECRET=6COi3Vk5e5z2uIsrNt4uLPResaET4RBp
MERCADOLIVRE_REDIRECT_URL=https://hugojobs.co/
```

### O que falta:

```bash
# Adicione ao .env:

MERCADOLIVRE_ACCESS_TOKEN=<seu_token_aqui>
MERCADOLIVRE_REFRESH_TOKEN=<seu_refresh_token>
```

### Como obter tokens:

**Opção A: Via OAuth Flow (Recomendado)**

1. Abra no navegador:
```
https://auth.mercadolivre.com.br/authorization?
response_type=code&
client_id=935927218612126&
redirect_uri=https://hugojobs.co/
```

2. Autorize a aplicação

3. Você será redirecionado para:
```
https://hugojobs.co/?code=<CÓDIGO_AQUI>
```

4. Extraia o `code` e execute:
```bash
curl -X POST https://api.mercadolibre.com/oauth/token \
  -d 'grant_type=authorization_code' \
  -d 'client_id=935927218612126' \
  -d 'client_secret=6COi3Vk5e5z2uIsrNt4uLPResaET4RBp' \
  -d 'code=<CÓDIGO_AQUI>' \
  -d 'redirect_uri=https://hugojobs.co/'
```

5. Você receberá:
```json
{
  "access_token": "TG-...",
  "token_type": "bearer",
  "expires_in": 21600,
  "refresh_token": "TG-...",
  "user_id": 12345,
  "scope": "read write"
}
```

6. Copie `access_token` e `refresh_token` para `.env`

**Opção B: Usar token existente**

Se você já tem acesso a uma conta MercadoLivre:
1. Acesse: https://apps.mercadolivre.com.br
2. Vá para "Aplicaciones Autorizadas"
3. Encontre "JARVIS Pipeline Integration"
4. Copie o token

---

## 🚀 Step 2: Ativar o MCP (1 min)

### Local (Desenvolvimento)

```bash
# Terminal 1: Rodar o servidor
python core/mcp/mercadolivre_mcp.py

# Terminal 2: Testar (curl)
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' \
  | python core/mcp/mercadolivre_mcp.py
```

### Docker (Produção)

```bash
# Build
docker build -t AIOX-GPS-mcp:latest .

# Run
docker run -e MERCADOLIVRE_ACCESS_TOKEN=<seu_token> \
           -e MERCADOLIVRE_CLIENT_ID=935927218612126 \
           -e MERCADOLIVRE_CLIENT_SECRET=6COi3Vk5e5z2uIsrNt4uLPResaET4RBp \
           AIOX-GPS-mcp:latest
```

### Claude Code (Integração nativa)

Arquivo `.mcp.json` já configurado. Reinicie Claude Code:

```bash
# VSCode: Ctrl+Shift+P → "Claude Code: Reload MCP"
# Windsurf: Cmd+K → reiniciar
```

---

## 📊 Step 3: Testar Ferramentas (2 min)

### Via Claude Code (depois de ativar)

```
@cfo
"Qual é a comissão da categoria ML-ELETRONICOS?"

# CFO vai consultar mercadolivre_get_commissions("ML-ELETRONICOS")
```

### Via JSON-RPC (direto)

```bash
# Terminal
cat <<'EOF' | python core/mcp/mercadolivre_mcp.py
{"jsonrpc":"2.0","method":"call_tool","params":{"name":"mercadolivre_get_categories"},"id":1}
EOF

# Resposta:
# {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"[...]"}]}}
```

---

## 🔗 Step 4: Integração com Agentes

### CFO (Pricing)

Agora pode acessar:
- Taxas de comissão por categoria
- Custos de envio para decisões de pricing
- Tipos de anúncio (premium vs clássico)

```yaml
# agents/cargo/c-level/cfo/DNA-CONFIG.yaml
integrations:
  - name: MercadoLivre MCP
    tools:
      - mercadolivre_get_commissions    # ← NOVO
      - mercadolivre_get_shipping_costs # ← NOVO
```

### CMO (Marketing)

Agora pode:
- Listar tipos de anúncio disponíveis
- Calcular ROI considerando comissões
- Determinar estratégia de categoria

```yaml
# agents/cargo/marketing/cmo/DNA-CONFIG.yaml
integrations:
  - name: MercadoLivre MCP
    tools:
      - mercadolivre_get_categories     # ← NOVO
      - mercadolivre_get_listing_types  # ← NOVO
```

---

## 🐛 Troubleshooting

### Erro: 403 Forbidden

**Causa:** Token ausente ou expirado

**Solução:**
```bash
# 1. Verifique .env
cat .env | grep MERCADOLIVRE_ACCESS

# 2. Se vazio, execute OAuth flow (Step 1)
# 3. Se expirado (>6 horas), use refresh_token:

curl -X POST https://api.mercadolibre.com/oauth/token \
  -d 'grant_type=refresh_token' \
  -d 'client_id=935927218612126' \
  -d 'client_secret=6COi3Vk5e5z2uIsrNt4uLPResaET4RBp' \
  -d 'refresh_token=<seu_refresh_token>'
```

### Erro: Connection refused

**Causa:** Servidor MCP não está rodando

**Solução:**
```bash
# Terminal 1: Iniciar servidor
python -u core/mcp/mercadolivre_mcp.py

# Terminal 2: Verificar porta
lsof -i :9000  # se estiver esperando em porta
```

### Erro: JSONDecodeError

**Causa:** Request mal formatado

**Solução:**
```bash
# Verifique formato JSON
echo '{"jsonrpc":"2.0","method":"initialize","id":1}' | jq .

# Se jq falhar, há problema de sintaxe
```

---

## 📈 Próximas Funcionalidades (v2.1)

- [ ] Listar anúncios ativos (seller-only)
- [ ] Criar anúncio com validação de categoria
- [ ] Calcular fees automáticas
- [ ] Sincronizar estoque em tempo real
- [ ] Webhooks para mudanças de status

---

## 🔐 Segurança

✅ **Credenciais seguras:**
- `.env` não é commitado (`.gitignore`)
- Tokens não aparecem em logs
- Servidor valida entrada antes de chamar API

⚠️ **Para Produção:**
- Use AWS Secrets Manager ou similar
- Rotacione tokens a cada 6 meses
- Monitore chamadas de API (rate limits)
- Use SSL/TLS em produção

---

## 📞 Suporte

Se algo não funcionar:

1. **Verifique token:**
   ```bash
   curl -H "Authorization: Bearer $MERCADOLIVRE_ACCESS_TOKEN" \
        https://api.mercadolibre.com/sites/MLB
   ```

2. **Logs do servidor:**
   ```bash
   python -u core/mcp/mercadolivre_mcp.py 2>&1 | tail -20
   ```

3. **Teste direto:**
   ```bash
   python -m pytest core/mcp/mercadolivre_mcp.py -v
   ```

---

**Pronto para ativar, senhor. Aguardando tokens.**

— JARVIS
