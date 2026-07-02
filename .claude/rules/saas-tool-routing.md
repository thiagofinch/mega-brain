# SaaS Tool Routing — Mega Brain

Applies PROACTIVELY whenever Claude needs to interact with any external SaaS tool.

## Comportamento Proativo (ALWAYS-ON)

Este NAO e uma skill invocada manualmente. E comportamento base que Claude DEVE seguir automaticamente toda vez que uma tarefa envolve interacao com SaaS externo.

**Regra fundamental:** Claude NUNCA tenta API externa antes de consultar o registry. A unica pausa aceitavel e para credenciais ausentes ou prerequisitos manuais.

## Fluxo de Decisao (NON-NEGOTIABLE)

Antes de interagir com QUALQUER SaaS externo:

```
1. Identificar SaaS(es) necessario(s) para a tarefa
2. Consultar workspace/domains/tech/saas-api-readiness.yaml
3. Classificar:
   ┌─────────────────────────────────────────────────────────────┐
   │ CONNECTED  → Usar API diretamente com auth_method documentado│
   ├─────────────────────────────────────────────────────────────┤
   │ AVAILABLE  → Checar prerequisite_status:                     │
   │              CONFIRMED      → Usar API                       │
   │              NOT_AUTHORIZED → Declarar bloqueio + workaround │
   │              MANUAL_ONLY    → Usar workaround direto         │
   ├─────────────────────────────────────────────────────────────┤
   │ NO_API     → Declarar acao manual ou Playwright              │
   └─────────────────────────────────────────────────────────────┘
4. Executar tarefa completa autonomamente
5. Atualizar last_verified ao final da operacao bem-sucedida
```

## Comunicacao Estruturada

| Momento | Formato |
|---------|---------|
| Descoberta | `[{SaaS}] e {STATUS}.` |
| Inicio | `Usando API/MCP.` ou `Usando workaround: {descricao}.` |
| Credencial ausente | `Aguardando credencial {ENV_KEY}. Documentar em .env e re-tentar.` |
| Prerequisito nao autorizado | `[{SaaS}] requer {prerequisite}. Status: {prerequisite_status}. Sugestao: {workaround}.` |
| Conclusao | `[{SaaS}] {operacao} completa.` |
| Governanca | `Encontrei {token/endpoint} novo. Posso registrar em saas-api-readiness.yaml.` |

## Exemplos

### CONNECTED
```
Pedido: "Liste workflows do N8N"
Acao:
  1. [N8N] e CONNECTED.
  2. Usando API com X-N8N-API-KEY.
  3. curl {{N8N_BASE_URL}}/api/v1/workflows
  4. [N8N] list completa. {N} workflows ativos.
```

### AVAILABLE com prerequisito CONFIRMED
```
Pedido: "Crie um Meet space pra um participante"
Acao:
  1. [Google Meet] e AVAILABLE com prerequisito DWD.
  2. prerequisite_status: CONFIRMED.
  3. Usando SA via getGoogleTokenDWD.
  4. POST https://meet.googleapis.com/v2/spaces
  5. [Google Meet] space criado: spaces/{SPACE_ID}.
```

### AVAILABLE com prerequisito NOT_AUTHORIZED
```
Pedido: "Crie usuario novo no Workspace via API"
Acao:
  1. [Google Admin SDK Directory] e AVAILABLE com prerequisito DWD admin.directory.user.
  2. prerequisite_status: NOT_AUTHORIZED (validado 2026-05-15 com 401 unauthorized_client).
  3. Bloqueio declarado.
  4. Workaround: criar usuario manualmente em admin.google.com.
  5. Aguardando confirmacao humana antes de prosseguir.
```

### NO_API
```
Pedido: "Cancele add-on de storage no Workspace"
Acao:
  1. [Google Workspace Admin Billing] e NO_API.
  2. Reason: Billing nao gerenciavel via SA API.
  3. Workaround: Playwright contra admin.google.com.
  4. Iniciando browser via MCP playwright...
```

## Fontes de Verdade

| Arquivo | Funcao | Quando consultar |
|---------|--------|-----------------|
| `workspace/domains/tech/saas-api-readiness.yaml` | Classificador primario (CONNECTED/AVAILABLE/NO_API) | PRIMEIRO — antes de qualquer acesso a SaaS |
| `.claude/credentials-map.md` | Mapa de tokens + IDs fixos | Para resolver `env_key` e `base_url` |
| `agents/_registry/capability-registry.yaml` | Service adapters internos do mega-brain | Para descobrir SE existe wrapper Python/JS |
| `services/{tool}/` | Adapters concretos (e.g. google-meet/, fireflies_webhook/) | Antes de criar codigo novo |

## Ciclo de Vida — SaaS Novo

```
1. Pedido envolve SaaS nao listado em saas-api-readiness.yaml
2. Pesquisar:
   a. Tem documentacao API publica? → AVAILABLE ou CONNECTED
   b. Apenas dashboard? → NO_API
3. Validar credenciais:
   a. Existe ENV_KEY no .env? → tentar token
   b. Existe SA configurada? → tentar DWD
   c. Nenhum → AVAILABLE com prerequisite "configurar credencial"
4. Registrar entry em saas-api-readiness.yaml com last_verified
5. Atualizar credentials-map.md se token novo
```

## Anti-Padroes (NUNCA fazer)

1. Tentar API externa sem consultar saas-api-readiness.yaml primeiro
2. Recuperar empiricamente um endpoint que ja esta documentado
3. Fazer 3+ tentativas com auth errado quando o registry tem o auth_method correto
4. Marcar last_verified sem validar operacao real (false positive)
5. Adicionar entry CONNECTED sem ter validado base_url + auth_method funcionais
6. Ignorar prerequisite_status NOT_AUTHORIZED e tentar mesmo assim

## Quando NAO Aplicar

- Operacoes inteiramente locais (Read, Write, Edit, Grep, Glob no filesystem)
- Subagent tasks que recebem credenciais pre-validadas como input
- Smoke tests internos onde a falha esperada e parte do teste

## Origem

Regra de tool-routing focada exclusivamente em SaaS externos (capability-registry.yaml cobre rotas internas).
