# DOSSIER -- WORKSPACE GOVERNANCE

> **Tipo:** Tema (Cross-meeting)
> **Meetings:** MEET-0097, MEET-0098, MEET-0099
> **Ultima atualizacao:** 2026-03-14
> **Versao:** 1.0.0

---

## Definicao

Conjunto de regras, restricoes e boas praticas sobre como workspaces (estruturas de pastas, paths, registries) devem ser criados, mantidos e protegidos dentro do ecossistema AIOX/Allfluence/Mega Brain. Tema central porque 3 founders (Alan, Thiago, Pedro) operam workspaces paralelos com abordagens diferentes que precisam convergir.

---

## Consensos

1. **Squads NAO devem criar novos caminhos no workspace.** Devem reconhecer estrutura existente e usar apenas o que esta registrado. Todos concordam com este principio. ^[chunk_MEET-0098_020, chunk_MEET-0098_010]

2. **Narrativa (dados do negocio) e sagrada.** Company Profile, DNA, produtos nao devem ser alterados automaticamente. Mudancas vao para backlog, precisam confirmacao humana. ^[chunk_MEET-0098_009, chunk_MEET-0098_014]

3. **Registries sao obrigatorios.** Service Registry, Tool Registry, Squad Registry, Process Registry. Sistema OBRIGA uso de ferramentas registradas. ^[chunk_MEET-0098_018, chunk_MEET-0098_019]

4. **Taxonomia de 4 categorias.** Workspace (dados canonicos), Docs (documentacao), Artifacts (outputs por squad), Apps (solucoes). Rafael implementou no dashboard. ^[chunk_MEET-0099_002]

---

## Divergencias

1. **Approach de implementacao:**
   - **Pedro:** Registries + 46 steps + restricao tecnica (sistema nao permite desvio). Ja implementou na Ofluente.
   - **Alan:** Velocidade criativa + ajustes manuais. Renomeou paths manualmente quebrando scripts. Pedro alertou: "nao ta doido?"
   - **Thiago:** 3-bucket architecture (external/business/personal) com entity canonicalization e confidence scoring.
   ^[MEET-0098 Tensao 1, Tensao 5]

2. **C-level por dominio:**
   - **Pedro:** Cada dominio precisa de C-level representante. Domain pessoal = clone do founder.
   - **Thiago:** Ja tem cargo agents (CFO, CRO, etc.) mas sem mapping formal para dominios do workspace.
   ^[chunk_MEET-0098_020]

---

## Decisoes Tomadas

| # | Decisao | Meeting | Status |
|---|---------|---------|--------|
| 1 | Squads nao criam paths novos -- usar registries | MEET-0098 | CONFIRMADA (diretriz) |
| 2 | Dashboard taxonomy: Workspace/Docs/Artifacts/Apps | MEET-0099 | CONFIRMADA (implementada) |
| 3 | Alan cria repo limpo com apenas 6 squads do evento | MEET-0098 | CONFIRMADA |
| 4 | Workspace needs formal sync (3 approaches) | MEET-0098 | PENDENTE |
| 5 | Push direto na main (pre-evento, temporario) | MEET-0099 | CONFIRMADA |

---

## Open Loops

1. **Sync formal de workspace** entre Alan + Thiago + Pedro -- Nenhum sync aconteceu ainda. 3 estruturas paralelas.
2. **Oficializacao de Tool Registry e Service Registry** para AIOX -- Thiago responsavel, sem prazo.
3. **Mapping de C-level por dominio** -- Pedro propos, nao implementado.
4. **Multi-tool abstraction** -- Dashboard precisa funcionar com ClickUp, Asana, Trello, Jira. Sem solucao definida.
5. **Naming convention** -- Alan renomeou de kebab-case para AIOX naming. Precisa convergir com scripts existentes.

---

## Evolucao Temporal

```
MEET-0097 (Equipe completa)
├── Problema identificado: cada membro instalou de forma diferente
├── Alan assume ownership da padronizacao
├── Tensao: Thiago e Alan trabalhando em workspace de forma independente
└── Decisao: workspace sync entre Thiago e Alan e necessario

MEET-0098 (Alan + Thiago + Pedro)
├── Pedro introduz 4 Registries como solucao formal
├── Pedro alerta sobre paths manuais do Alan
├── Thiago demonstra 3-bucket architecture
├── Consenso: squads nao criam paths novos
└── Gap: sync formal nao aconteceu, apenas reconhecido como urgente

MEET-0099 (Rafael + Alan + Thiago + Erica)
├── Rafael implementa taxonomy no dashboard (Workspace/Docs/Artifacts/Apps)
├── Repo compartilhado criado (dashboard-premium)
├── Decisao: push direto na main (pre-evento)
└── MCP context bloat identificado como problema de governanca
```
