# LOG-TEMPLATES v5.1

> **Versão:** 5.1.0
> **Última atualização:** 2025-12-19
> **Propósito:** Templates padronizados para todos os logs do sistema

---

## FILOSOFIA DE LOGS v5.0

Cada log responde 4 perguntas fundamentais:
1. **O que foi feito?** - Ações executadas
2. **O que foi criado/modificado?** - Artefatos afetados
3. **Para onde vai?** - Próximos passos no pipeline
4. **O que está pendente?** - Ações que requerem atenção

---

## ÍCONES SEMÂNTICOS

| Ícone | Significado |
|-------|-------------|
| ✅ | Sucesso, completo |
| ⚠️ | Aviso, atenção necessária |
| ❌ | Erro, falha |
| 🔴 | Crítico, ação imediata |
| 🟡 | Monitorar, atenção |
| 🟢 | OK, saudável |
| 📥 | Input, entrada |
| 📤 | Output, saída |
| 📊 | Métricas, estatísticas |
| 🔗 | Conexão, referência |
| 🤖 | Agente, automação |
| 👤 | Pessoa, dossier pessoal |
| 📚 | Tema, dossier temático |
| ⏱️ | Tempo, duração |
| 🎯 | Objetivo, meta |
| 💡 | Insight, descoberta |

---

## RESUMO DOS 7 LOGS

| # | Log | Quando | Propósito |
|---|-----|--------|-----------|
| 1 | EXECUTION REPORT | Após Phase 6 | O que foi feito |
| 2 | SYSTEM DIGEST | /system-digest | Estado completo |
| 3 | ROLE-TRACKING | Com LOG 1 | Novos agentes |
| 4 | AGENT ENRICHMENT | Após Phase 7 | O que agentes receberam |
| 5 | INGEST REPORT | /ingest | Material entrou |
| 6 | INBOX STATUS | /inbox | O que aguarda |
| 7 | FULL PIPELINE REPORT | /jarvis-full | Tudo consolidado |

---

## 1. EXECUTION REPORT v5.0

> **Gerado:** Após conclusão do Pipeline Jarvis (Phase 8)
> **Propósito:** Resumo completo de uma execução do pipeline

```
═══════════════════════════════════════════════════════════════════════════════
                         EXECUTION REPORT
                         Pipeline Jarvis v2.1
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📥 SOURCE PROCESSED
───────────────────────────────────────────────────────────────────────────────
   Source ID:    {SOURCE_ID}
   File:         {FILE_PATH}
   Person:       {PERSON_NAME}
   Duration:     {DURATION} min
   Processed:    {TIMESTAMP}

═══════════════════════════════════════════════════════════════════════════════
                              PIPELINE PHASES
═══════════════════════════════════════════════════════════════════════════════

┌─ Phase 1-2: CHUNKING + ENTITY RESOLUTION ─────────────────────────────────┐
│                                                                            │
│   📊 CHUNKS CREATED: {N}                                                   │
│   ├─ Semantic breaks: {N}                                                  │
│   ├─ Avg chunk size: {N} chars                                             │
│   └─ Stored: /processing/chunks/CHUNKS-{SOURCE_ID}.json                 │
│                                                                            │
│   🔗 ENTITIES RESOLVED: {N}                                                │
│   ├─ Persons: {LIST}                                                       │
│   ├─ Frameworks: {LIST}                                                    │
│   ├─ Metrics: {LIST}                                                       │
│   └─ Updated: CANONICAL-MAP.json                                           │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌─ Phase 3-4: INSIGHT EXTRACTION + PRIORITIZATION ──────────────────────────┐
│                                                                            │
│   💡 INSIGHTS EXTRACTED: {N}                                               │
│   ├─ 🔴 HIGH priority: {N}                                                 │
│   ├─ 🟡 MEDIUM priority: {N}                                               │
│   └─ 🟢 LOW priority: {N}                                                  │
│                                                                            │
│   📊 BY TYPE:                                                              │
│   ├─ Frameworks: {N}                                                       │
│   ├─ Metrics: {N}                                                          │
│   ├─ Processes: {N}                                                        │
│   ├─ Principles: {N}                                                       │
│   └─ Tensions: {N}                                                         │
│                                                                            │
│   📁 Updated: INSIGHTS-STATE.json                                          │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌─ Phase 5-6: NARRATIVE SYNTHESIS + DOSSIER COMPILATION ────────────────────┐
│                                                                            │
│   📝 NARRATIVES CREATED: {N}                                               │
│   ├─ Consolidated from {N} insights                                        │
│   └─ Stored: NARRATIVES-STATE.json                                         │
│                                                                            │
│   📚 DOSSIERS AFFECTED:                                                    │
│                                                                            │
│   👤 PERSONS:                                                              │
│   ┌────────────────────────┬────────────┬────────────┬───────────────────┐ │
│   │ Dossier                │ Status     │ +Insights  │ +Narratives       │ │
│   ├────────────────────────┼────────────┼────────────┼───────────────────┤ │
│   │ DOSSIER-{PERSON}.md    │ {NEW/UPD}  │ +{N}       │ +{N}              │ │
│   └────────────────────────┴────────────┴────────────┴───────────────────┘ │
│                                                                            │
│   📚 THEMES:                                                               │
│   ┌────────────────────────┬────────────┬────────────┬───────────────────┐ │
│   │ Dossier                │ Status     │ +Insights  │ +Narratives       │ │
│   ├────────────────────────┼────────────┼────────────┼───────────────────┤ │
│   │ DOSSIER-{THEME}.md     │ {NEW/UPD}  │ +{N}       │ +{N}              │ │
│   └────────────────────────┴────────────┴────────────┴───────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌─ Phase 7: AGENT ENRICHMENT ───────────────────────────────────────────────┐
│                                                                            │
│   🤖 AGENTS UPDATED: {N}                                                   │
│   ┌────────────────────────┬────────────────────────┬─────────────────────┐│
│   │ Agent                  │ MEMORY Updated         │ New Knowledge       ││
│   ├────────────────────────┼────────────────────────┼─────────────────────┤│
│   │ CLOSER                 │ ✅ MEMORY-CLOSER.md    │ +{N} frameworks     ││
│   │ SDS                    │ ✅ MEMORY-SDS.md       │ +{N} metrics        ││
│   │ SALES-MANAGER          │ ✅ MEMORY-SM.md        │ +{N} processes      ││
│   └────────────────────────┴────────────────────────┴─────────────────────┘│
│                                                                            │
│   🆕 ROLES TRACKED:                                                        │
│   ├─ {ROLE_1}: {N} mentions (threshold: 10)                                │
│   ├─ {ROLE_2}: {N} mentions                                                │
│   └─ Updated: role-tracking.md                                             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌─ Phase 8: ORG-LIVE ENRICHMENT ───────────────────────────────────────────────┐
│                                                                              │
│   🏢 ORG-LIVE STATUS (Cargos Humanos)                                        │
│                                                                              │
│   📋 ROLES UPDATED:                                                          │
│   ┌────────────────────────┬────────────────────────┬───────────────────────┐│
│   │ Role                   │ MEMORY Updated         │ New Insights          ││
│   ├────────────────────────┼────────────────────────┼───────────────────────┤│
│   │ CLOSER-CHEFE           │ ✅ MEMORY-CLOSER-CHEFE │ +{N} aplicados        ││
│   │ SALES-MANAGER          │ ✅ MEMORY-SALES-MANAGER│ +{N} aplicados        ││
│   │ SDR                    │ ✅ MEMORY-SDR.md       │ +{N} aplicados        ││
│   └────────────────────────┴────────────────────────┴───────────────────────┘│
│                                                                              │
│   📄 JDs AFFECTED:                                                           │
│   └─ {list of JD-*.md files affected or "Nenhum"}                            │
│                                                                              │
│   📊 ORG STATUS:                                                             │
│   ├─ ROLEs definidos: {N} em /agents/ORG-LIVE/ROLES/                      │
│   ├─ JDs prontos: {N} em /agents/ORG-LIVE/JDS/                            │
│   ├─ MEMORYs ORG: {N} em /agents/ORG-LIVE/MEMORY/                         │
│   └─ ORG-CHART: /agents/ORG-LIVE/ORG/ORG-CHART.md                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                              TRACEABILITY
═══════════════════════════════════════════════════════════════════════════════

🔗 CHAIN: SOURCE → CHUNKS → INSIGHTS → NARRATIVES → DOSSIERS → AGENTS

   {SOURCE_ID}
      │
      ├─► Chunks: {CHUNK_IDS}
      │      │
      │      ├─► Insights: {INSIGHT_IDS}
      │      │      │
      │      │      └─► Narratives: {NARRATIVE_IDS}
      │      │             │
      │      │             └─► Dossiers: {DOSSIER_LIST}
      │      │                    │
      │      │                    └─► Agents: {AGENT_LIST}
      │      │
      │      └─► [Direct to Dossiers for factual data]
      │
      └─► Registry: file-registry.json (MD5: {HASH})

═══════════════════════════════════════════════════════════════════════════════
                              STATISTICS
═══════════════════════════════════════════════════════════════════════════════

   ⏱️ TIMING:
      Total duration: {DURATION}
      Chunking: {TIME}
      Extraction: {TIME}
      Synthesis: {TIME}
      Compilation: {TIME}
      Enrichment: {TIME}

   📊 TOTALS:
      Chunks: {N}
      Entities: {N}
      Insights: {N}
      Narratives: {N}
      Dossiers affected: {N}
      Agents updated: {N}

═══════════════════════════════════════════════════════════════════════════════
                              NEXT ACTIONS
═══════════════════════════════════════════════════════════════════════════════

   🔴 IMMEDIATE:
      {action if any critical}

   🟡 RECOMMENDED:
      - Review DOSSIER-{PERSON}.md for accuracy
      - Check role-tracking.md for threshold alerts
      - Run /system-digest for full system view

   🟢 OPTIONAL:
      - Re-index RAG: python rag_index.py --knowledge
      - Export audit: /export-audit

═══════════════════════════════════════════════════════════════════════════════
                         END EXECUTION REPORT
═══════════════════════════════════════════════════════════════════════════════
```

---

## 2. SYSTEM DIGEST v5.0

> **Gerado:** Via comando `/system-digest` ou `/d`
> **Propósito:** Visão completa do estado do sistema

```
═══════════════════════════════════════════════════════════════════════════════
                         MEGA BRAIN SYSTEM DIGEST
                         v{VERSION} • {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📊 HEALTH SCORE: {SCORE}/100 {EMOJI}
───────────────────────────────────────────────────────────────────────────────
   State Files:     {OK/WARN/ERR} │ Schema validation
   Agents:          {OK/WARN/ERR} │ MEMORY freshness
   Dossiers:        {OK/WARN/ERR} │ Traceability complete
   INBOX:           {OK/WARN/ERR} │ Pending files
   Pipeline:        {OK/WARN/ERR} │ No orphan states

═══════════════════════════════════════════════════════════════════════════════
                              KNOWLEDGE BASE
═══════════════════════════════════════════════════════════════════════════════

📥 inbox STATUS:
───────────────────────────────────────────────────────────────────────────────
   Pending files: {N}
   ├─ 🔴 Urgent (>7 days): {N}
   ├─ 🟡 Normal (1-7 days): {N}
   └─ 🟢 Recent (<24h): {N}

   By Source:
   ┌────────────────────────────────────┬───────────┬──────────────────────────┐
   │ Source                             │ Files     │ Oldest                   │
   ├────────────────────────────────────┼───────────┼──────────────────────────┤
   │ COLE GORDON           │ {N}       │ {DATE}                   │
   │ JORDAN LEE (AI BUSINESS)           │ {N}       │ {DATE}                   │
   │ ALEX HORMOZI     │ {N}       │ {DATE}                   │
   └────────────────────────────────────┴───────────┴──────────────────────────┘

📊 processing STATUS:
───────────────────────────────────────────────────────────────────────────────
   CHUNKS-STATE.json:
   ├─ Total chunks: {N}
   ├─ Sources: {N}
   └─ Last updated: {TIMESTAMP}

   CANONICAL-MAP.json:
   ├─ Persons: {N}
   ├─ Frameworks: {N}
   ├─ Metrics: {N}
   └─ Last updated: {TIMESTAMP}

   INSIGHTS-STATE.json:
   ├─ Total insights: {N}
   ├─ 🔴 HIGH: {N} │ 🟡 MED: {N} │ 🟢 LOW: {N}
   └─ Last updated: {TIMESTAMP}

   NARRATIVES-STATE.json:
   ├─ Total narratives: {N}
   └─ Last updated: {TIMESTAMP}

📚 knowledge/dossiers:
───────────────────────────────────────────────────────────────────────────────
   👤 PERSONS: {N} dossiers
   ┌────────────────────────────────────┬───────────┬──────────────────────────┐
   │ Person                             │ Sources   │ Last Updated             │
   ├────────────────────────────────────┼───────────┼──────────────────────────┤
   │ Cole Gordon                        │ {N}       │ {DATE}                   │
   │ Jordan Lee                         │ {N}       │ {DATE}                   │
   │ Jeremy Haynes                      │ {N}       │ {DATE}                   │
   └────────────────────────────────────┴───────────┴──────────────────────────┘

   📚 THEMES: {N} dossiers
   ┌────────────────────────────────────┬───────────┬──────────────────────────┐
   │ Theme                              │ Sources   │ Last Updated             │
   ├────────────────────────────────────┼───────────┼──────────────────────────┤
   │ Processo de Vendas                 │ {N}       │ {DATE}                   │
   │ Estrutura de Time                  │ {N}       │ {DATE}                   │
   │ Comissionamento                    │ {N}       │ {DATE}                   │
   └────────────────────────────────────┴───────────┴──────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                              AGENT ECOSYSTEM
═══════════════════════════════════════════════════════════════════════════════

🤖 AGENTS ACTIVE: {N}
───────────────────────────────────────────────────────────────────────────────

   C-LEVEL:
   ┌─────────────┬─────────────┬───────────┬──────────────────────────────────┐
   │ Agent       │ MEMORY      │ Sources   │ Status                           │
   ├─────────────┼─────────────┼───────────┼──────────────────────────────────┤
   │ CRO         │ v{N}        │ {N}       │ {✅/⚠️} {reason}                 │
   │ CFO         │ v{N}        │ {N}       │ {✅/⚠️} {reason}                 │
   │ CMO         │ v{N}        │ {N}       │ {✅/⚠️} {reason}                 │
   │ COO         │ v{N}        │ {N}       │ {✅/⚠️} {reason}                 │
   └─────────────┴─────────────┴───────────┴──────────────────────────────────┘

   SALES:
   ┌─────────────┬─────────────┬───────────┬──────────────────────────────────┐
   │ Agent       │ MEMORY      │ Sources   │ Status                           │
   ├─────────────┼─────────────┼───────────┼──────────────────────────────────┤
   │ CLOSER      │ v{N}        │ {N}       │ {✅/⚠️} {reason}                 │
   │ BDR         │ v{N}        │ {N}       │ {✅/⚠️} {reason}                 │
   │ SDS         │ v{N}        │ {N}       │ {✅/⚠️} {reason}                 │
   │ SALES-MGR   │ v{N}        │ {N}       │ {✅/⚠️} {reason}                 │
   └─────────────┴─────────────┴───────────┴──────────────────────────────────┘

👥 ROLE TRACKING:
───────────────────────────────────────────────────────────────────────────────
   🔴 AT THRESHOLD (>=10 mentions):
      {ROLE}: {N} mentions → /create-agent {ROLE} --category {CAT}

   🟡 APPROACHING (5-9 mentions):
      {ROLE}: {N} mentions

   ✅ ALREADY CREATED:
      CLOSER (20+), BDR (15+), SDS (12+), ...

🏢 ORG-LIVE (Cargos Humanos):
───────────────────────────────────────────────────────────────────────────────
   📋 ROLES: {N} definidos
   ┌─────────────┬─────────────┬───────────┬──────────────────────────────────┐
   │ Role        │ JD          │ MEMORY    │ Status                           │
   ├─────────────┼─────────────┼───────────┼──────────────────────────────────┤
   │ CLOSER-CHEFE│ ✅          │ ✅        │ {✅/⚠️} Ativo                    │
   │ SALES-MGR   │ ✅          │ ✅        │ {✅/⚠️} Planejado                │
   │ SDR         │ ✅          │ ✅        │ {✅/⚠️} Planejado                │
   │ CLOSER      │ ✅          │ ✅        │ {✅/⚠️} Planejado                │
   │ ...         │             │           │                                  │
   └─────────────┴─────────────┴───────────┴──────────────────────────────────┘

   📊 PARIDADE Agent IA ↔ Role Humano:
   ┌─────────────────────────┬─────────────────────────┬──────────────────────┐
   │ Agent IA                │ Role Humano             │ Status               │
   ├─────────────────────────┼─────────────────────────┼──────────────────────┤
   │ AGENT-CLOSER            │ ROLE-CLOSER             │ ✅ Mapeado           │
   │ AGENT-SALES-MANAGER     │ ROLE-SALES-MANAGER      │ ✅ Mapeado           │
   │ (não existe)            │ ROLE-CLOSER-CHEFE       │ ⚠️ Híbrido           │
   └─────────────────────────┴─────────────────────────┴──────────────────────┘

   📁 Estrutura ORG-LIVE:
   ├─ /agents/ORG-LIVE/ROLES/    → {N} roles definidos
   ├─ /agents/ORG-LIVE/JDS/      → {N} job descriptions
   ├─ /agents/ORG-LIVE/MEMORY/   → {N} memórias de cargos
   └─ /agents/ORG-LIVE/ORG/      → ORG-CHART, PROTOCOL, SCALING-TRIGGERS

═══════════════════════════════════════════════════════════════════════════════
                              RECENT ACTIVITY
═══════════════════════════════════════════════════════════════════════════════

📅 LAST 7 DAYS:
───────────────────────────────────────────────────────────────────────────────
   Sources processed: {N}
   Insights extracted: {N}
   Agents updated: {N}
   Dossiers modified: {N}

📋 LAST OPERATIONS:
   ┌──────────────────────┬────────────────────┬──────────┬─────────┐
   │ Timestamp            │ Operation          │ Source   │ Status  │
   ├──────────────────────┼────────────────────┼──────────┼─────────┤
   │ {TIMESTAMP}          │ PIPELINE_COMPLETE  │ {ID}     │ ✅      │
   │ {TIMESTAMP}          │ AGENT_ENRICHMENT   │ {ID}     │ ✅      │
   │ {TIMESTAMP}          │ INGEST             │ {ID}     │ ✅      │
   └──────────────────────┴────────────────────┴──────────┴─────────┘

═══════════════════════════════════════════════════════════════════════════════
                              RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════════════

🔴 CRITICAL:
   {List critical issues or "None"}

🟡 RECOMMENDED:
   - {action 1}
   - {action 2}

🟢 OPTIONAL:
   - {optional improvement 1}

═══════════════════════════════════════════════════════════════════════════════
                         QUICK COMMANDS
═══════════════════════════════════════════════════════════════════════════════

   /inbox              → Ver arquivos pendentes
   /process-inbox      → Processar próximo arquivo
   /agents             → Status detalhado dos agentes
   /dossiers           → Status dos dossiês
   /log execution      → Último execution report
   /rag-search "query" → Busca semântica

═══════════════════════════════════════════════════════════════════════════════
                         END SYSTEM DIGEST
═══════════════════════════════════════════════════════════════════════════════
```

---

## 3. ROLE-TRACKING REPORT v5.0

> **Gerado:** Via comando `/log roles`
> **Propósito:** Status de roles sendo rastreados para criação de novos agentes

```
═══════════════════════════════════════════════════════════════════════════════
                         ROLE-TRACKING REPORT
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📊 SUMMARY:
───────────────────────────────────────────────────────────────────────────────
   Roles tracked: {N}
   At threshold: {N}
   Approaching: {N}
   Agents created: {N}

═══════════════════════════════════════════════════════════════════════════════
                         THRESHOLD REACHED (>=10)
═══════════════════════════════════════════════════════════════════════════════

🔴 READY FOR AGENT CREATION:

┌─────────────────────────┬──────────┬───────────────────────┬────────────────┐
│ Role                    │ Mentions │ Sources               │ Action         │
├─────────────────────────┼──────────┼───────────────────────┼────────────────┤
│ Appointment Setter      │ 12       │ CG001, CG002, JH001   │ /create-agent  │
│ Revenue Operations      │ 10       │ JL003, CG004          │ /create-agent  │
└─────────────────────────┴──────────┴───────────────────────┴────────────────┘

   📋 Suggested commands:
      /create-agent APPOINTMENT-SETTER --category SALES --sub-of SALES-MANAGER
      /create-agent REVENUE-OPS --category OPERATIONS

═══════════════════════════════════════════════════════════════════════════════
                         APPROACHING THRESHOLD (5-9)
═══════════════════════════════════════════════════════════════════════════════

🟡 MONITORING:

┌─────────────────────────┬──────────┬───────────────────────┬────────────────┐
│ Role                    │ Mentions │ Sources               │ Trend          │
├─────────────────────────┼──────────┼───────────────────────┼────────────────┤
│ Sales Enablement        │ 7        │ CG001, CG003          │ ↑ +2 this week │
│ Customer Success Mgr    │ 5        │ JL001, JL002          │ → stable       │
└─────────────────────────┴──────────┴───────────────────────┴────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                         AGENTS ALREADY CREATED
═══════════════════════════════════════════════════════════════════════════════

✅ ACTIVE AGENTS (from role-tracking):

┌─────────────────────────┬──────────┬───────────────────────┬────────────────┐
│ Role → Agent            │ Mentions │ Created               │ MEMORY Version │
├─────────────────────────┼──────────┼───────────────────────┼────────────────┤
│ Closer → AGENT-CLOSER   │ 45+      │ 2024-01-15            │ v3.0           │
│ BDR → AGENT-BDR         │ 28+      │ 2024-01-20            │ v2.1           │
│ SDS → AGENT-SDS         │ 22+      │ 2024-02-01            │ v1.5           │
└─────────────────────────┴──────────┴───────────────────────┴────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                         ROLE DETAILS
═══════════════════════════════════════════════════════════════════════════════

🔍 APPOINTMENT SETTER (12 mentions):
───────────────────────────────────────────────────────────────────────────────
   First seen: CG001 (2024-12-10)
   Last seen: JH001 (2024-12-18)

   Context mentions:
   ├─ CG001: "The appointment setter is critical for booking calls..."
   ├─ CG002: "Train your setters on qualification frameworks..."
   └─ JH001: "My setter team books 80% of all discovery calls..."

   Responsibilities identified:
   ├─ Booking discovery calls
   ├─ Initial qualification
   ├─ Lead handoff to SDR/Closer
   └─ Show rate optimization

   Suggested expertise:
   ├─ Qualification frameworks
   ├─ Appointment booking
   └─ Lead nurturing

═══════════════════════════════════════════════════════════════════════════════
                         END ROLE-TRACKING REPORT
═══════════════════════════════════════════════════════════════════════════════
```

---

## 4. AGENT ENRICHMENT REPORT v5.0

> **Gerado:** Após Phase 7 do Pipeline Jarvis
> **Propósito:** Detalhar atualizações feitas aos agentes

```
═══════════════════════════════════════════════════════════════════════════════
                         AGENT ENRICHMENT REPORT
                         Pipeline Jarvis • Phase 7
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📥 SOURCE: {SOURCE_ID}
   Person: {PERSON_NAME}
   File: {FILE_PATH}

═══════════════════════════════════════════════════════════════════════════════
                         THEME → AGENT MAPPING
═══════════════════════════════════════════════════════════════════════════════

   Themes detected in source:
   ┌────────────────────────┬────────────────────────────────────────────────┐
   │ Theme                  │ Mapped Agents                                  │
   ├────────────────────────┼────────────────────────────────────────────────┤
   │ 02-PROCESSO-VENDAS     │ CLOSER, SDS, SALES-MANAGER                     │
   │ 04-COMISSIONAMENTO     │ CRO, SALES-MANAGER                             │
   │ 05-METRICAS            │ CRO, CFO                                       │
   └────────────────────────┴────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                         MEMORY UPDATES
═══════════════════════════════════════════════════════════════════════════════

🤖 AGENT: CLOSER
───────────────────────────────────────────────────────────────────────────────
   MEMORY file: /agents/SALES/MEMORY-CLOSER.md
   Version: v2.5 → v3.0

   ✅ ADDED TO KNOWLEDGE BASE:
   ┌─────────────────────────────────────────────────────────────────────────┐
   │ Type        │ Content                           │ Source    │ Priority │
   ├─────────────┼───────────────────────────────────┼───────────┼──────────┤
   │ Framework   │ 5 Armas do Closer                 │ CG004     │ HIGH     │
   │ Framework   │ Objection Loop Method             │ CG004     │ HIGH     │
   │ Metric      │ Close rate benchmark: 25-35%      │ CG004     │ MEDIUM   │
   │ Process     │ Stack building in final pitch     │ CG004     │ HIGH     │
   └─────────────┴───────────────────────────────────┴───────────┴──────────┘

   📊 MEMORY GROWTH:
   ├─ Frameworks: 12 → 14 (+2)
   ├─ Metrics: 8 → 9 (+1)
   └─ Processes: 5 → 6 (+1)

🤖 AGENT: SDS
───────────────────────────────────────────────────────────────────────────────
   MEMORY file: /agents/SALES/MEMORY-SDS.md
   Version: v1.4 → v1.5

   ✅ ADDED TO KNOWLEDGE BASE:
   ┌─────────────────────────────────────────────────────────────────────────┐
   │ Type        │ Content                           │ Source    │ Priority │
   ├─────────────┼───────────────────────────────────┼───────────┼──────────┤
   │ Process     │ Warm transfer protocol            │ CG004     │ MEDIUM   │
   │ Metric      │ Qualification rate: 40%           │ CG004     │ MEDIUM   │
   └─────────────┴───────────────────────────────────┴───────────┴──────────┘

🤖 AGENT: SALES-MANAGER
───────────────────────────────────────────────────────────────────────────────
   MEMORY file: /agents/SALES/MEMORY-SALES-MANAGER.md
   Version: v2.0 → v2.1

   ✅ ADDED TO KNOWLEDGE BASE:
   ┌─────────────────────────────────────────────────────────────────────────┐
   │ Type        │ Content                           │ Source    │ Priority │
   ├─────────────┼───────────────────────────────────┼───────────┼──────────┤
   │ Framework   │ QC Call Review Framework          │ CG004     │ HIGH     │
   │ Process     │ Weekly 1:1 structure              │ CG004     │ MEDIUM   │
   └─────────────┴───────────────────────────────────┴───────────┴──────────┘

═══════════════════════════════════════════════════════════════════════════════
                         AGENT NOT UPDATED (Reason)
═══════════════════════════════════════════════════════════════════════════════

   🔸 CFO - No relevant financial insights in source
   🔸 CMO - No marketing content detected
   🔸 BDR - Content focused on closing, not prospecting

═══════════════════════════════════════════════════════════════════════════════
                         ROLE TRACKING UPDATE
═══════════════════════════════════════════════════════════════════════════════

   New roles mentioned in source:
   ┌────────────────────────┬──────────┬────────────────────────────────────┐
   │ Role                   │ Mentions │ Status                             │
   ├────────────────────────┼──────────┼────────────────────────────────────┤
   │ Appointment Setter     │ +3       │ Total: 12 (🔴 THRESHOLD)           │
   │ Sales Trainer          │ +1       │ Total: 4 (monitoring)              │
   └────────────────────────┴──────────┴────────────────────────────────────┘

   ⚠️ ACTION REQUIRED:
      Role "Appointment Setter" atingiu threshold.
      Executar: /create-agent APPOINTMENT-SETTER --category SALES

═══════════════════════════════════════════════════════════════════════════════
                         TRACEABILITY
═══════════════════════════════════════════════════════════════════════════════

   All updates traceable to:
   ├─ Chunks: {CHUNK_IDS}
   ├─ Insights: {INSIGHT_IDS}
   └─ Narratives: {NARRATIVE_IDS}

═══════════════════════════════════════════════════════════════════════════════
                         END AGENT ENRICHMENT REPORT
═══════════════════════════════════════════════════════════════════════════════
```

---

## 5. INGEST REPORT v5.0

> **Gerado:** Após comando `/ingest`
> **Propósito:** Confirmar ingestão de material no sistema

```
═══════════════════════════════════════════════════════════════════════════════
                         INGEST REPORT
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📥 MATERIAL INGESTED
───────────────────────────────────────────────────────────────────────────────
   Source ID:      {SOURCE_ID}
   Type:           {youtube/local/gdrive}
   Original URL:   {URL if applicable}

📁 FILES CREATED
───────────────────────────────────────────────────────────────────────────────
   Video/Audio:    {FILENAME}.mp4
   Transcript:     {FILENAME}.txt
   Location:       /inbox/{PERSON}/{CONTENT_TYPE}/

   File sizes:
   ├─ Video: {SIZE} MB
   └─ Transcript: {SIZE} KB ({N} characters)

👤 SOURCE DETECTED
───────────────────────────────────────────────────────────────────────────────
   Person:         {PERSON_NAME}
   Company:        {COMPANY}
   Content Type:   {PODCAST/MASTERCLASS/COURSE/etc}

📊 TRANSCRIPT STATS
───────────────────────────────────────────────────────────────────────────────
   Duration:       {DURATION} minutes
   Words:          {N}
   Estimated read: {N} minutes
   Language:       {LANG}

═══════════════════════════════════════════════════════════════════════════════
                         QUALITY CHECK
═══════════════════════════════════════════════════════════════════════════════

   ✅ Transcript quality: {GOOD/MEDIUM/LOW}
   ✅ Speaker identified: {YES/NO}
   ✅ Timestamps present: {YES/NO}
   ⚠️ Issues detected: {none/list}

═══════════════════════════════════════════════════════════════════════════════
                         NEXT STEPS
═══════════════════════════════════════════════════════════════════════════════

   Para processar este material:

   /process-jarvis "{SOURCE_ID}"

   Ou para ver todos pendentes:

   /inbox

═══════════════════════════════════════════════════════════════════════════════
                         END INGEST REPORT
═══════════════════════════════════════════════════════════════════════════════
```

---

## 6. INBOX STATUS v5.0

> **Gerado:** Via comando `/inbox` ou `/i`
> **Propósito:** Listar arquivos pendentes de processamento

```
═══════════════════════════════════════════════════════════════════════════════
                              INBOX STATUS
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📊 SUMMARY:
───────────────────────────────────────────────────────────────────────────────
   Total pending:  {N} files
   🔴 Urgent:      {N} (>7 days old)
   🟡 Normal:      {N} (1-7 days old)
   🟢 Recent:      {N} (<24h old)

═══════════════════════════════════════════════════════════════════════════════
                         PENDING BY SOURCE
═══════════════════════════════════════════════════════════════════════════════

📁 COLE GORDON:
───────────────────────────────────────────────────────────────────────────────
   🟡 [CG005] Objection Handling Masterclass.txt
      ├─ Added: 2024-12-15 (3 days ago)
      ├─ Size: 45KB │ Duration: ~60 min
      └─ Process: /process-jarvis "CG005"

   🟢 [CG006] Sales Team Structure Q&A.txt
      ├─ Added: 2024-12-18 (today)
      ├─ Size: 32KB │ Duration: ~45 min
      └─ Process: /process-jarvis "CG006"

📁 JORDAN LEE (AI BUSINESS):
───────────────────────────────────────────────────────────────────────────────
   🔴 [JL008] AI Sales Integration.txt
      ├─ Added: 2024-12-10 (8 days ago) ⚠️
      ├─ Size: 55KB │ Duration: ~75 min
      └─ Process: /process-jarvis "JL008"

📁 ALEX HORMOZI:
───────────────────────────────────────────────────────────────────────────────
   ⏳ [AH001] Offers Framework Breakdown.mp4
      ├─ Status: AWAITING TRANSCRIPTION
      ├─ Added: 2024-12-17
      └─ Action: Transcribe first, then ingest

═══════════════════════════════════════════════════════════════════════════════
                         BATCH ACTIONS
═══════════════════════════════════════════════════════════════════════════════

   📋 QUICK ACTIONS:

   Process next (oldest first):
      /process-inbox --next

   Process all from person:
      /process-inbox --person "Cole Gordon"

   Process everything (careful!):
      /process-inbox --all --dry-run    # Preview first
      /process-inbox --all              # Execute

═══════════════════════════════════════════════════════════════════════════════
                         FILES NOT READY
═══════════════════════════════════════════════════════════════════════════════

   ⏳ AWAITING TRANSCRIPTION:
   ┌────────────────────────────────────────────────────────────────────────┐
   │ File                                          │ Status                 │
   ├───────────────────────────────────────────────┼────────────────────────┤
   │ AH001 - Offers Framework Breakdown.mp4            │ Needs transcription    │
   │ AH002 - Business Launch Behind Scenes.mp4          │ Needs transcription    │
   └───────────────────────────────────────────────┴────────────────────────┘

   To transcribe:
      /ingest --local "/path/to/file.mp4" --transcribe

═══════════════════════════════════════════════════════════════════════════════
                         END INBOX STATUS
═══════════════════════════════════════════════════════════════════════════════
```

---

## 7. FULL PIPELINE REPORT v5.1

> **Gerado:** Após comando `/jarvis-full` completar
> **Propósito:** Log consolidado de execução full auto (ingest + pipeline + enrichment)

```
═══════════════════════════════════════════════════════════════════════════════
                         FULL PIPELINE REPORT
                         Pipeline Jarvis v2.1 • Full Auto
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📥 SOURCE PROCESSED
───────────────────────────────────────────────────────────────────────────────
   Source ID:    {SOURCE_ID}
   File:         {FILE_PATH}
   Person:       {PERSON_NAME}
   Type:         {CONTENT_TYPE}
   Origin:       {youtube/local/gdrive}

═══════════════════════════════════════════════════════════════════════════════
                              EXECUTION TIMELINE
═══════════════════════════════════════════════════════════════════════════════

⏱️ PHASE BREAKDOWN:
┌───────┬──────────────────────────┬──────────┬─────────────────────┬─────────┐
│ Phase │ Name                     │ Duration │ Output              │ Status  │
├───────┼──────────────────────────┼──────────┼─────────────────────┼─────────┤
│   0   │ Ingest                   │ {TIME}   │ Arquivo em INBOX    │ ✅      │
│   1   │ Initialization           │ {TIME}   │ Metadados           │ ✅      │
│   2   │ Chunking                 │ {TIME}   │ {N} chunks          │ ✅      │
│   3   │ Entity Resolution        │ {TIME}   │ {N} entidades       │ ✅      │
│   4   │ Insight Extraction       │ {TIME}   │ {N} insights        │ ✅      │
│   5   │ Narrative Synthesis      │ {TIME}   │ {N} narrativas      │ ✅      │
│   6   │ Dossier Compilation      │ {TIME}   │ {N} dossiers        │ ✅      │
│   7   │ Agent Enrichment         │ {TIME}   │ {N} agents          │ ✅      │
│   8   │ Finalization             │ {TIME}   │ Reports gerados     │ ✅      │
└───────┴──────────────────────────┴──────────┴─────────────────────┴─────────┘

   ⏱️ TOTAL DURATION: {TOTAL_TIME}

═══════════════════════════════════════════════════════════════════════════════
                              ARTIFACTS CREATED
═══════════════════════════════════════════════════════════════════════════════

📊 PROCESSING:
───────────────────────────────────────────────────────────────────────────────
   Chunks:     {N} created in CHUNKS-STATE.json
   Entities:   {N} resolved in CANONICAL-MAP.json
   Insights:   {N} extracted (🔴 {HIGH} HIGH, 🟡 {MED} MED, 🟢 {LOW} LOW)
   Narratives: {N} synthesized in NARRATIVES-STATE.json

📚 DOSSIERS:
───────────────────────────────────────────────────────────────────────────────
   👤 PERSONS:
   ┌────────────────────────────────┬────────────┬────────────────────────────┐
   │ Dossier                        │ Status     │ Changes                    │
   ├────────────────────────────────┼────────────┼────────────────────────────┤
   │ DOSSIER-{PERSON}.md            │ {NEW/UPD}  │ +{N} insights, +{N} narr   │
   └────────────────────────────────┴────────────┴────────────────────────────┘

   📚 THEMES:
   ┌────────────────────────────────┬────────────┬────────────────────────────┐
   │ Dossier                        │ Status     │ Changes                    │
   ├────────────────────────────────┼────────────┼────────────────────────────┤
   │ DOSSIER-{THEME}.md             │ {NEW/UPD}  │ +{N} insights              │
   └────────────────────────────────┴────────────┴────────────────────────────┘

🤖 AGENTS UPDATED:
───────────────────────────────────────────────────────────────────────────────
   ┌────────────────────────┬────────────────────────┬─────────────────────────┐
   │ Agent                  │ MEMORY Updated         │ New Knowledge           │
   ├────────────────────────┼────────────────────────┼─────────────────────────┤
   │ {AGENT_1}              │ ✅ MEMORY-{AGENT}.md   │ +{N} items              │
   │ {AGENT_2}              │ ✅ MEMORY-{AGENT}.md   │ +{N} items              │
   └────────────────────────┴────────────────────────┴─────────────────────────┘

🏢 ORG-LIVE ENRICHMENT (Cargos Humanos):
───────────────────────────────────────────────────────────────────────────────
   📋 ROLES UPDATED:
   ┌────────────────────────┬────────────────────────┬─────────────────────────┐
   │ Role                   │ MEMORY Updated         │ New Insights            │
   ├────────────────────────┼────────────────────────┼─────────────────────────┤
   │ {ROLE_1}               │ ✅ MEMORY-{ROLE}.md    │ +{N} aplicados          │
   │ {ROLE_2}               │ ✅ MEMORY-{ROLE}.md    │ +{N} aplicados          │
   └────────────────────────┴────────────────────────┴─────────────────────────┘

   📄 JDs AFFECTED: {list or "Nenhum"}
   📊 ORG STATUS: {N} ROLEs | {N} JDs | {N} MEMORYs ORG

═══════════════════════════════════════════════════════════════════════════════
                              ROLE TRACKING
═══════════════════════════════════════════════════════════════════════════════

   🆕 ROLES MENTIONED:
   ┌────────────────────────┬──────────┬────────────────────────────────────────┐
   │ Role                   │ +Mentions│ Total (Status)                         │
   ├────────────────────────┼──────────┼────────────────────────────────────────┤
   │ {ROLE_1}               │ +{N}     │ {TOTAL} (🔴 THRESHOLD / 🟡 monitoring) │
   └────────────────────────┴──────────┴────────────────────────────────────────┘

   ⚠️ ACTION REQUIRED:
      {Role atingiu threshold → /create-agent ROLE --category CAT}

═══════════════════════════════════════════════════════════════════════════════
                              TRACEABILITY
═══════════════════════════════════════════════════════════════════════════════

🔗 COMPLETE CHAIN:

   {SOURCE} ({ORIGIN})
      │
      ├─► inbox/{PERSON}/{TYPE}/{FILE}
      │
      ├─► processing/
      │      ├─► chunks/ (+{N} chunks)
      │      ├─► canonical/ (CANONICAL-MAP.json)
      │      ├─► insights/ (+{N} insights)
      │      └─► narratives/ (+{N} narratives)
      │
      ├─► knowledge/dossiers/
      │      ├─► PERSONS/{PERSON}.md
      │      └─► THEMES/{THEME}.md
      │
      ├─► agents/SALES/ & C-LEVEL/
      │      └─► MEMORY-{AGENT}.md (x{N})
      │
      ├─► agents/ORG-LIVE/
      │      ├─► ROLES/ROLE-{ROLE}.md (x{N})
      │      ├─► MEMORY/MEMORY-{ROLE}.md (x{N})
      │      └─► JDS/JD-{ROLE}.md (se afetado)
      │
      └─► logs/FULL/FULL-{SOURCE_ID}-{TIMESTAMP}.md

═══════════════════════════════════════════════════════════════════════════════
                              STATISTICS
═══════════════════════════════════════════════════════════════════════════════

   📊 SUMMARY:
   ┌────────────────────────────────────────────────────────────────────────────┐
   │ Metric                              │ Value                                │
   ├─────────────────────────────────────┼──────────────────────────────────────┤
   │ Total Duration                      │ {TOTAL_TIME}                         │
   │ Source Words                        │ {WORD_COUNT}                         │
   │ Chunks Created                      │ {N}                                  │
   │ Entities Resolved                   │ {N}                                  │
   │ Insights Extracted                  │ {N}                                  │
   │ Narratives Synthesized              │ {N}                                  │
   │ Dossiers Affected                   │ {N}                                  │
   │ Agents Updated                      │ {N}                                  │
   │ Files Created                       │ {N}                                  │
   │ Files Modified                      │ {N}                                  │
   └─────────────────────────────────────┴──────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                              NEXT ACTIONS
═══════════════════════════════════════════════════════════════════════════════

   🔴 IMMEDIATE:
      {action if any critical - e.g., create agent for threshold role}

   🟡 RECOMMENDED:
      - Review DOSSIER-{PERSON}.md for accuracy
      - Run /system-digest for full system view
      - Check /inbox for more pending files

   🟢 OPTIONAL:
      - Re-index RAG: python rag_index.py --knowledge
      - Export audit: /export-audit

═══════════════════════════════════════════════════════════════════════════════
                         END FULL PIPELINE REPORT
═══════════════════════════════════════════════════════════════════════════════
```

---

## HEALTH SCORE CALCULATION

```
HEALTH_SCORE = sum of component scores (max 100)

COMPONENTS:
├─ State Files (20 pts)
│  ├─ All JSON valid: +10
│  ├─ Schema validated: +5
│  └─ Recent updates (<7d): +5
│
├─ Agents (20 pts)
│  ├─ All MEMORYs exist: +10
│  ├─ MEMORYs updated (<30d): +5
│  └─ No orphan agents: +5
│
├─ Dossiers (20 pts)
│  ├─ All traceable: +10
│  ├─ No orphan chunks: +5
│  └─ Complete coverage: +5
│
├─ INBOX (20 pts)
│  ├─ No urgent files (>7d): +10
│  ├─ <10 pending: +5
│  └─ All have transcripts: +5
│
└─ Pipeline (20 pts)
   ├─ No failed states: +10
   ├─ No orphan insights: +5
   └─ Last run <7d: +5

SCORE INTERPRETATION:
├─ 90-100: 🟢 Excellent
├─ 70-89:  🟡 Good (minor issues)
├─ 50-69:  🟠 Needs attention
└─ <50:    🔴 Critical issues
```

---

## INCONSISTENCY DETECTION

Ao gerar qualquer log, verificar e reportar:

```
⚠️ INCONSISTENCIES DETECTED:
───────────────────────────────────────────────────────────────────────────────

1. ORPHAN CHUNKS
   Chunks sem insights associados:
   ├─ chunk_JL003_015: No insights extracted
   └─ chunk_CG002_008: Referenced but not in state

2. MISSING TRACEABILITY
   Insights sem chunk_ref:
   └─ insight_047: Missing source chunk

3. STALE MEMORIES
   MEMORYs não atualizados após novos insights:
   └─ MEMORY-BDR.md: Last update 2024-11-15, new insights from 2024-12-18

4. UNRESOLVED ENTITIES
   Entidades mencionadas mas não no CANONICAL-MAP:
   └─ "Revenue Operations Manager" - not mapped

───────────────────────────────────────────────────────────────────────────────
   Fix: /validate --fix
───────────────────────────────────────────────────────────────────────────────
```

---

## CHANGELOG

| Versão | Data | Mudanças |
|--------|------|----------|
| v5.1.0 | 2025-12-19 | +LOG 7 (FULL PIPELINE REPORT), +Tabela resumo dos 7 logs |
| v5.0.0 | 2025-12-19 | Reescrita completa, 6 tipos de log, Health Score, Inconsistency Detection |
| v4.0.0 | - | (versão interna) |
| v3.0.0 | - | (versão interna) |
| v2.0.0 | - | (versão interna) |
| v1.0.0 | 2024-12-17 | Versão inicial com 4 tipos de log |
