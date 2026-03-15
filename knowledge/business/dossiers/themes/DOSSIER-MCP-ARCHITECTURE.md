# DOSSIER -- MCP ARCHITECTURE

> **Tipo:** Tema (Cross-meeting)
> **Meetings:** MEET-0098, MEET-0099
> **Ultima atualizacao:** 2026-03-14
> **Versao:** 1.0.0

---

## Definicao

Arquitetura e governanca de MCP (Model Context Protocol) servers dentro do ecossistema AIOX e Mega Brain. Tema emergiu com a descoberta de que MCPs consomem ate 50% da janela de contexto no startup da sessao, causando "context bloat" e degradacao de performance.

---

## Consensos

1. **MCP context bloat e problema real.** Muitos MCPs inflam a sessao. Solucao: converter data fetchers de MCP para servicos background. IA so toca nos dados para analise/insights, nao para coleta. ^[chunk_MEET-0099_008, chunk_MEET-0099_009]

2. **CEO do Perplexity vai parar de usar MCPs.** Migracao para SQS e SLE. Alan referenciou como validacao externa da decisao. ^[chunk_MEET-0099_008]

3. **Separacao data fetching vs intelligence.** Crons + API para coleta de dados. IA reservada para geracao de reports, insights, analise. ^[chunk_MEET-0099_008, chunk_MEET-0099_009]

4. **Webhook > Polling para ingestao.** Fathom/Fireflies dispara webhook no fim da reuniao, N8N captura, processamento sob demanda. Evita polling e garante captura real-time. ^[chunk_MEET-0099_011]

---

## Divergencias

1. **Timing da migracao:**
   - **Rafael:** Quer migrar MCPs para servicos imediatamente. Ja sentiu a dor.
   - **Alan:** Concorda mas prioriza evento. Migracao pos-evento.
   - **Thiago:** Ja opera com modelo hibrido no Mega Brain (3 MCPs ativos: knowledge, n8n, read-ai). Pratica validada.

2. **Scope de MCPs a manter:**
   - MCPs de inteligencia/analise (RAG, knowledge search) provavelmente devem permanecer.
   - MCPs de data fetching (ClickUp, Notion, etc.) devem migrar para servicos.
   - Fronteira exata nao definida.

---

## Decisoes Tomadas

| # | Decisao | Meeting | Status |
|---|---------|---------|--------|
| 1 | Reduzir MCPs -- converter data fetchers para servicos background | MEET-0099 | CONFIRMADA |
| 2 | Webhook-based pipeline para meetings | MEET-0099 | CONFIRMADA (Thiago ja opera) |
| 3 | IA reservada para intelligence, nao data collection | MEET-0099 | CONFIRMADA (principio) |

---

## Open Loops

1. **Lista de MCPs a migrar vs manter** -- Nao inventariada formalmente.
2. **Implementacao de servicos background** -- Decidido mas nao executado.
3. **Cost impact** -- Quanto da R$30K de API foi consumido por MCPs inflando contexto? Nao calculado.
4. **Multi-tool abstraction** -- Se MCPs saem, como dashboard conecta com ClickUp/Asana/Trello/Jira? Sem solucao.
5. **Mega Brain MCP governance** -- Ja tem 3 MCPs com regras documentadas (mcp-governance.md). Pode servir de referencia.

---

## Evolucao Temporal

```
MEET-0098 (3 founders)
├── Thiago demonstra 3-bucket architecture (usa MCPs seletivamente)
├── Entity canonicalization via MCP local (mega-brain-knowledge)
└── Contexto: MCPs como parte da arquitetura, sem questionamento

MEET-0099 (Dashboard team)
├── Rafael descobre MCP context bloat na pratica
├── Alan referencia CEO Perplexity parando de usar MCPs
├── DECISAO: converter data fetchers para servicos background
├── Rafael propoe: IA so para intelligence/analysis
└── Thiago valida: webhook pipeline ja funciona no Mega Brain
```
