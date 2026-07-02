# Session Preflight — Mega Brain

Applies at the START of every session.

## Rule: Preflight Obrigatorio (NON-NEGOTIABLE)

Antes de QUALQUER trabalho, verificar conectividade de servicos criticos e carregar contexto operacional pendente.

### Checklist de Conectividade (executar em paralelo)

```
1. SUPABASE    — curl {{SUPABASE_URL}}/rest/v1/ com SUPABASE_SERVICE_ROLE_KEY  → espera 200
2. N8N         — curl {{N8N_API_URL}}/api/v1/workflows com X-N8N-API-KEY        → espera 200
3. GITHUB      — gh auth status                                                 → espera autenticado
```

Adapte a lista aos servicos que voce realmente configurou. Cada servico externo adicional
(transcricao, gestao de tarefas, etc.) segue o mesmo padrao: endpoint + credencial → espera 200.

Tabela de resultados deve ser impressa antes de qualquer outro output. Se servico falhar, gerar WARN — NUNCA bloquear a sessao.

### Fontes de Credenciais (ordem de prioridade)

1. `.claude/credentials-map.md` — mapa canonico de tokens (consultar PRIMEIRO)
2. `~/Projects/mega-brain/.env` — tokens raw
3. `.credentials/google-sa-*.json` — Service Accounts Google

Nao fazer grep no `.env` para informacoes ja documentadas em credentials-map.

### IDs Fixos

Tabela canonica em `.claude/credentials-map.md` secao "IDs Fixos (referencia rapida)". Consultar antes de redescobrir empiricamente:

- Supabase project ref, profile
- N8N base URL + header format
- GitHub orgs
- Google Workspace domains + SA emails
- DWD scopes autorizados (e nao autorizados)

### Handoffs Pendentes

Apos checklist de conectividade, verificar `.mega-brain/handoffs/` por handoffs com:
- `handoff.to == "next-session"`
- `handoff.consumed == false`

Para cada handoff pendente:
1. Emitir `scope` e `next_action` no contexto
2. Listar `context.what_remains` items
3. Hook `handoff_loader.py` (SessionStart) automatiza essa varredura

### Tool/SaaS Routing

Antes de interagir com SaaS externo, consultar `workspace/domains/tech/saas-api-readiness.yaml` para classificar como CONNECTED/AVAILABLE/NO_API. Referencia: `.claude/rules/saas-tool-routing.md`.

## Comunicacao Estruturada

| Momento | Formato |
|---------|---------|
| Status checklist | Tabela com `Servico | Status | Latencia` |
| Handoff detectado | `[Handoff] {scope}: {next_action}` + items what_remains |
| SaaS classificado | `[{Servico}] e {STATUS}. {Acao}` (ex: "{Servico} e CONNECTED. Usando API.") |
| Service falha | `[WARN] {Servico} falhou: {motivo}. Sugestao: {acao_corretiva}` |

## Anti-Padroes (NUNCA fazer)

1. Pular preflight em sessoes "rapidas" — todo trabalho operacional depende de servicos
2. Bloquear sessao se preflight falhar — sempre WARN, nunca BLOCK (exit 0)
3. Pedir credencial ao usuario antes de consultar `credentials-map.md`
4. Fazer grep no `.env` para descobrir valor ja documentado em "IDs Fixos"
5. Tentar API externa antes de classificar via `saas-api-readiness.yaml`

## Quando NAO Aplicar

- Sessoes que executam apenas leitura local (sem touch em servicos externos)
- Continuacao de turno onde checklist ja foi exibido na sessao atual
- Modo `--dangerously-skip-permissions` com `--no-preflight` flag explicito

## Origem

Regra de preflight de sessao. Adapte os servicos e credenciais ao seu proprio ecossistema
(perfil Supabase, base URL do N8N, orgs GitHub, etc.).
