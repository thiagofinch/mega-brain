# DOSSIER -- Rafael Costa

> **Tipo:** Pessoa (Business)
> **Meetings:** MEET-0099
> **Ultima atualizacao:** 2026-03-14
> **Versao:** 1.0.0

---

## Perfil

Desenvolvedor do Dashboard AIOX. Responsavel por frontend, integracao de views, pipeline de lives/conteudo, e arquitetura de widgets. Perfil tecnico com visao de produto -- propoe solucoes de UX e governanca de dados alem de implementacao.

---

## Posicionamentos-Chave

### 1. MCP Context Bloat e Problema Real
Descobriu que muitos MCPs inflam a sessao e consomem contexto. Propoe converter data fetchers de MCP para servicos background (crons + API). IA so toca nos dados para analise/insights, nao para coleta. ^[chunk_MEET-0099_008, chunk_MEET-0099_009]

### 2. Disney Experience para Onboarding
Empresarios sao ocupados demais para data entry manual. Sistema deve extrair informacao automaticamente de integracoes existentes (meeting recordings, Notion, ClickUp, Google Drive) e popular o workspace. Unica acao do usuario: conectar servicos e autenticar. ^[chunk_MEET-0099_003]

### 3. Pipeline Completo de Lives
Concebeu fluxo end-to-end: ideia -> titulo -> thumbnail -> descricao YouTube -> agenda -> convite WhatsApp -> slides (via design system) -> transmissao -> download automatico -> Google Drive -> transcricao com timestamps -> cortes -> aprovacao/recusa -> slots de publicacao -> sync com time de trafego. ^[chunk_MEET-0099_014]

### 4. Dashboard com Views Consolidadas
Principio UX: consolidar multiplas views (terminals, orchestration, world/3D, kanban) em abas dentro da mesma interface em vez de itens separados no menu. Reduz cliques e carga cognitiva. ^[chunk_MEET-0099_007, chunk_MEET-0099_008]

---

## Frameworks/Metodologias

| Framework | Descricao | Fonte |
|-----------|-----------|-------|
| Lives Pipeline (2 fases) | Pre-producao (idea -> slides) + Pos-producao (download -> cortes -> distribuicao) | INS-MEET-0099-008 |
| Creative Approval Flow | Gera criativos -> pagina de aprovacao -> approve/reject com motivos -> sync trafego | INS-MEET-0099-009 |
| Overnight Agent Pattern | Agentes calculam instancias, executam tasks autonomamente off-hours, entregam relatorio matinal | INS-MEET-0099-006 |
| Dashboard Taxonomy (Workspace/Docs/Artifacts/Apps) | 4 categorias canonicas para organizacao de dados no dashboard | INS-MEET-0099-003 (co-criado com Alan) |

---

## Padroes de Pensamento

1. **UX-first** -- Pensa em experiencia do usuario antes de arquitetura tecnica. "Comprou, voltou no chat, ja esta disponivel."
2. **Automation-maximalist** -- Tudo que pode ser automatizado deve ser. Pipeline de lives e exemplo extremo.
3. **Gate-based quality** -- Aprovacao com motivos de rejeicao. Nao deixa conteudo ruim passar sem feedback.
4. **Pragmatico com evento** -- Focou em fazer tudo funcionar para o evento, reorganizou menus e priorizou estabilidade.

---

## Tensoes Identificadas

1. **Prazo do evento vs qualidade:** "O evento foi muito do nada" -- correria para entregar algo funcional sem planejamento adequado. Frustracao com timeline.
2. **Multi-tool fragmentation:** ClickUp, Asana, Trello, Jira -- dashboard precisa abstrair mas sem solucao definida ainda.
3. **Integracao de trafego:** Meta Ads requer developer account, levou 4 horas para configurar uma pessoa. Friccao real no onboarding.

---

## Open Loops

1. Push dashboard atual no repo compartilhado -- IMEDIATO
2. Integracao World (3D) no dashboard -- PRE-EVENTO
3. Resolucao de multi-tool abstraction (ClickUp/Asana/Trello/Jira) -- NAO RESOLVIDO
4. Developer accounts para participantes do evento -- PENDENTE (Meta/Google)

---

## Fontes

| Meeting | Data | Tema Principal | Insights Relacionados |
|---------|------|----------------|----------------------|
| MEET-0099 | 2026-03-13 | Dashboard AIOX + Pipeline + MCP | INS-MEET-0099-001 a 014 |
