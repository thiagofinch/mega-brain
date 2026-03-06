# PIPELINE JARVIS v2.1

> **Versão:** 2.1.0
> **Data:** 2025-12-18
> **Propósito:** Pipeline semântico completo com enforcement, logs e checkpoints integrados

---

## VISÃO GERAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE JARVIS v2.1                               │
│                                                                              │
│  8 PHASES (consolidado de 9 para 8)                                         │
│  ├─ Phase 1: INITIALIZATION + VALIDATION                                    │
│  ├─ Phase 2: CHUNKING (Prompt 1.1)                                          │
│  ├─ Phase 3: ENTITY RESOLUTION (Prompt 1.2)                                 │
│  ├─ Phase 4: INSIGHT EXTRACTION (Prompt 2.1)                                │
│  ├─ Phase 5: NARRATIVE SYNTHESIS (Prompt 3.1)                               │
│  ├─ Phase 6: DOSSIER COMPILATION (Prompt 4.0)                               │
│  ├─ Phase 7: AGENT ENRICHMENT + USER PROMPT                                 │
│  └─ Phase 8: FINALIZATION + EXECUTION REPORT                                │
│                                                                              │
│  ⛔ ENFORCEMENT INTEGRADO: Ver core/templates/SYSTEM/ENFORCEMENT.md    │
│  📋 LOGS OBRIGATÓRIOS: Ver core/templates/SYSTEM/LOG-TEMPLATES.md      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## DEPENDÊNCIAS

| Arquivo | Path | Obrigatório |
|---------|------|-------------|
| ENFORCEMENT.md | `core/templates/SYSTEM/` | ✅ |
| CHECKPOINT-ENFORCEMENT.md | `core/templates/SYSTEM/` | ✅ |
| LOG-TEMPLATES.md | `core/templates/SYSTEM/` | ✅ |
| PROMPT-1.1-CHUNKING.md | `core/templates/PIPELINE/` | ✅ |
| PROMPT-1.2-ENTITY-RESOLUTION.md | `core/templates/PIPELINE/` | ✅ |
| PROMPT-2.1-INSIGHT-EXTRACTION.md | `core/templates/PIPELINE/` | ✅ |
| PROMPT-2.1-DNA-TAGS-INCREMENT.md | `core/templates/PIPELINE/` | ✅ |
| PROMPT-3.1-NARRATIVE-SYNTHESIS.md | `core/templates/PIPELINE/` | ✅ |
| DOSSIER-COMPILATION-PROTOCOL.md | `core/templates/PIPELINE/` | ✅ |
| SOURCES-COMPILATION-PROTOCOL.md | `core/templates/PIPELINE/` | ✅ |
| NARRATIVE-METABOLISM-PROTOCOL.md | `core/templates/PIPELINE/` | ✅ |
| DNA-EXTRACTION-PROTOCOL.md | `core/templates/agents/` | ✅ |
| ENRICHMENT-PROTOCOL.md | `core/templates/agents/` | ⚪ Opcional |
| REASONING-MODEL-PROTOCOL.md | `core/templates/agents/` | ⚪ Opcional |
| TEMPLATE-EVOLUTION-PROTOCOL.md | `/core/templates/agents/` | ✅ (Phase 7) |

---

## CORE CONSTRAINTS

1. **Processar 100% do conteúdo** - Não resumir, não omitir
2. **Rastreabilidade total** - Todo insight → chunk_id → arquivo fonte
3. **Incremental** - Adicionar ao estado existente, NUNCA substituir
4. **Source-aware** - Extrair metadados do path do arquivo
5. **Não misturar** - Scope/corpus diferentes devem ser separados
6. **Enforcement** - Bloquear atalhos e validar integridade

---

## PHASE 1: INITIALIZATION + VALIDATION

### 1.1 - Validate Input
```
⛔ CHECKPOINT PRE-1.1
[ ] CP-1.1.A: Arquivo existe em $ARGUMENTS
[ ] CP-1.1.B: Arquivo tem conteúdo (> 100 chars)
[ ] CP-1.1.C: Metadados identificáveis (fonte)

IF any fails: ⛔ EXIT("Arquivo inválido ou não encontrado")
```

### 1.2 - Extract Path Metadata
```
PARSE $ARGUMENTS to extract:

SOURCE_PERSON = Pasta nível 1 após inbox/
SOURCE_COMPANY = Conteúdo entre parênteses
SOURCE_TYPE = Pasta nível 2 (MASTERMINDS, BLUEPRINTS, COURSES, etc.)
SOURCE_ID = Gerar hash único (ex: "CG003")
SCOPE = Determinar: course|company|personal
CORPUS = Derivar de SOURCE_COMPANY
SOURCE_DATETIME = Extrair ou NOW()
```

### 1.3 - Load State Files
```
CHUNKS_STATE = READ /artifacts/chunks/CHUNKS-STATE.json
  → IF missing: CREATE with {"chunks": [], "meta": {"version": "v1"}}

CANONICAL_MAP = READ /artifacts/canonical/CANONICAL-MAP.json
  → IF missing: CREATE with seed entities

INSIGHTS_STATE = READ /artifacts/insights/INSIGHTS-STATE.json
  → IF missing: CREATE with empty structure

NARRATIVES_STATE = READ /artifacts/narratives/NARRATIVES-STATE.json
  → IF missing: CREATE with empty structure
```

### 1.4 - Check Already Processed
```
SEARCH CHUNKS_STATE.chunks WHERE meta.source_id == $SOURCE_ID

IF found:
  → LOG WARNING: "Arquivo já processado: $SOURCE_ID"
  → ASK: "Reprocessar? (sobrescreve chunks desta fonte)"
  → IF no: EXIT with status: ALREADY_PROCESSED
```

### ✓ CHECKPOINT POST-1
```
[ ] CP-POST-1.A: Metadados extraídos (SOURCE_PERSON, SOURCE_ID)
[ ] CP-POST-1.B: State files carregados ou criados
[ ] CP-POST-1.C: Decisão de processamento tomada
```

---

## PHASE 2: CHUNKING (Prompt 1.1)

### ⛔ CHECKPOINT PRE-2
```
[ ] CP-1.1.A: Arquivo de transcrição existe
[ ] CP-1.1.B: Arquivo tem conteúdo (> 100 chars)
[ ] CP-1.1.C: Metadados identificáveis
```

### 2.1 - Read Full Content
```
CONTENT = READ $ARGUMENTS (arquivo completo)
WORD_COUNT = count words in CONTENT
```

### 2.2 - Execute Chunking Protocol
```
APPLY protocol from core/templates/PIPELINE/PROMPT-1.1-CHUNKING.md

RULES:
- Chunk size: ~300 palavras (~1000 tokens)
- Preserve: timestamps, speaker labels, formatting
- Extract: pessoas (raw), temas (raw)
- Generate: id_chunk sequencial ("chunk_{source_id}_{NNN}")

OUTPUT: NEW_CHUNKS = array of chunk objects
```

### 2.3 - Merge and Save Chunks
```
MERGE NEW_CHUNKS into CHUNKS_STATE.chunks
  → Deduplicate by id_chunk
  → Update meta.last_updated = NOW()

WRITE /artifacts/chunks/CHUNKS-STATE.json
```

### ✓ CHECKPOINT POST-2
```
[ ] CP-POST-2.A: count(new_chunks) > 0
[ ] CP-POST-2.B: Cada chunk tem id_chunk único
[ ] CP-POST-2.C: CHUNKS-STATE.json foi salvo

Se falhar: ⛔ EXIT("Phase 2 não produziu chunks válidos")
```

### 📋 AUDIT LOG
```json
{
  "timestamp": "ISO",
  "phase": 2,
  "operation": "CHUNKING",
  "source_id": "$SOURCE_ID",
  "chunks_created": N,
  "status": "SUCCESS|FAILED"
}
```

---

## PHASE 3: ENTITY RESOLUTION (Prompt 1.2)

### ⛔ CHECKPOINT PRE-3
```
[ ] CP-1.2.A: CHUNKS-STATE.json existe
[ ] CP-1.2.B: chunks[] tem elementos
[ ] CP-1.2.C: Cada chunk tem id_chunk único
```

### 3.1 - Execute Entity Resolution
```
APPLY protocol from core/templates/PIPELINE/PROMPT-1.2-ENTITY-RESOLUTION.md

RULES:
- Threshold merge: 0.85 confidence
- Prefer: forma mais longa/explícita como canônico
- NEVER merge across different corpus
- Flag collisions

OUTPUT:
- CANONICALIZED_CHUNKS
- UPDATED_CANONICAL_MAP
- REVIEW_QUEUE
- COLLISIONS
```

### 3.2 - Save Entity Resolution
```
UPDATE CHUNKS_STATE.chunks with CANONICALIZED_CHUNKS
WRITE /artifacts/chunks/CHUNKS-STATE.json
WRITE /artifacts/canonical/CANONICAL-MAP.json

IF REVIEW_QUEUE not empty:
  → APPEND to /artifacts/canonical/REVIEW-QUEUE.json
```

### ✓ CHECKPOINT POST-3
```
[ ] CP-POST-3.A: canonical_state.entities não vazio
[ ] CP-POST-3.B: Todos os chunks têm pessoas/temas resolvidos
[ ] CP-POST-3.C: CANONICAL-MAP.json foi salvo

Se falhar: ⛔ EXIT("Phase 3 não resolveu entidades")
```

---

## PHASE 4: INSIGHT EXTRACTION (Prompt 2.1)

### ⛔ CHECKPOINT PRE-4
```
[ ] CP-2.1.A: CHUNKS-STATE.json existe
[ ] CP-2.1.B: CANONICAL-MAP.json existe
[ ] CP-2.1.C: canonical_state tem entidades
```

### 4.1 - Execute Insight Extraction
```
APPLY protocol from core/templates/PIPELINE/PROMPT-2.1-INSIGHT-EXTRACTION.md

RULES:
- Priority: HIGH|MEDIUM|LOW
- Every insight MUST have: id_chunk reference, confidence
- Detect contradictions with existing insights

OUTPUT:
- NEW_INSIGHTS
- CHANGE_LOG
```

### 4.2 - Merge and Save Insights
```
MERGE NEW_INSIGHTS into INSIGHTS_STATE.insights_state
  → For each person: append to persons[canonical_name]
  → For each theme: append to themes[canonical_theme]
  → Append CHANGE_LOG entries
  → Increment version

WRITE /artifacts/insights/INSIGHTS-STATE.json
```

### ✓ CHECKPOINT POST-4
```
[ ] CP-POST-4.A: insights_state.persons não vazio
[ ] CP-POST-4.B: Cada insight tem id_chunk referenciado
[ ] CP-POST-4.C: INSIGHTS-STATE.json foi salvo

Se falhar: ⛔ EXIT("Phase 4 não extraiu insights")
```

---

## PHASE 5: NARRATIVE SYNTHESIS (Prompt 3.1)

### ⛔ CHECKPOINT PRE-5
```
[ ] CP-3.1.A: INSIGHTS-STATE.json existe
[ ] CP-3.1.B: insights_state.persons não vazio
[ ] CP-3.1.C: insights_state.themes não vazio
```

### 5.1 - Execute Narrative Synthesis
```
APPLY protocol from core/templates/PIPELINE/PROMPT-3.1-NARRATIVE-SYNTHESIS.md

REGRAS DE MERGE (CRÍTICO):
- narrative: CONCATENAR com separador de atualização
- insights_included[]: APPEND (não substituir)
- tensions[]: APPEND (não substituir)
- open_loops[]: APPEND novos, marcar RESOLVED os respondidos
- next_questions[]: SUBSTITUIR (única exceção)

OUTPUT: UPDATED_NARRATIVES
```

### 5.2 - Save Narratives
```
WRITE /artifacts/narratives/NARRATIVES-STATE.json
```

### ✓ CHECKPOINT POST-5
```
[ ] CP-POST-5.A: narratives_state.persons[$SOURCE_PERSON].narrative existe
[ ] CP-POST-5.B: narrative.length > 100 caracteres
[ ] CP-POST-5.C: NARRATIVES-STATE.json foi salvo

Se falhar: ⛔ EXIT("Phase 5 não produziu narrativas")
```

---

## PHASE 6: DOSSIER COMPILATION (Prompt 4.0)

### ⛔ CHECKPOINT PRE-6
```
[ ] CP-4.0.A: NARRATIVES-STATE.json existe
[ ] CP-4.0.B: Pelo menos 1 pessoa com narrativa
[ ] CP-4.0.C: open_loops identificados (⚠️ se vazio)
```

### 6.1 - Load State for Compilation
```
READ NARRATIVES-STATE.json
READ INSIGHTS-STATE.json
READ CANONICAL-MAP.json

PERSONS_TO_COMPILE = keys of narratives_state.persons
THEMES_TO_COMPILE = keys of narratives_state.themes
```

### 6.2 - Compile Person Dossiers
```
FOR each PERSON_NAME in PERSONS_TO_COMPILE:
  DOSSIER_PATH = /knowledge/dossiers/persons/DOSSIER-{NAME}.md

  ⛔ ENFORCEMENT: enforce_before_knowledge_write(DOSSIER_PATH)

  IF exists: MODE = "INCREMENTAL" (APPEND)
  ELSE: MODE = "CREATE"

  WRITE dossier using DOSSIER-COMPILATION-PROTOCOL.md template
```

### 6.3 - Compile Theme Dossiers
```
FOR each THEME_NAME in THEMES_TO_COMPILE:
  DOSSIER_PATH = /knowledge/dossiers/THEMES/DOSSIER-{THEME}.md

  ⛔ ENFORCEMENT: enforce_before_knowledge_write(DOSSIER_PATH)

  IF 2+ persons in theme: populate Consensos/Divergências

  WRITE dossier
```

### ✓ CHECKPOINT POST-6
```
[ ] CP-POST-6.A: Pelo menos 1 dossiê criado em /knowledge/dossiers/
[ ] CP-POST-6.B: Dossiê segue template (tem seções obrigatórias)
[ ] CP-POST-6.C: sources[] contém $SOURCE_ID

Se falhar: ⛔ EXIT("Phase 6 não compilou dossiês")
```

---

## PHASE 7: AGENT ENRICHMENT

### 7.1 - Compile Knowledge Payload
```
KNOWLEDGE_PAYLOAD = {
  "source_id": $SOURCE_ID,
  "source_person": $SOURCE_PERSON,
  "frameworks_discovered": [...],
  "techniques_discovered": [...],
  "metrics_discovered": [...],
  "insights_high_priority": [...],
  "agents_impacted": [...]
}
```

### 7.2 - Check Role Threshold
```
READ /agents/DISCOVERY/role-tracking.md

FOR each ROLE found in insights:
  IF mentions >= 10: FLAG "🔴 CRIAR AGENTE"
  IF mentions >= 5: FLAG "🟡 MONITORAR"
```

### 7.3 - Present Options to User
```
═══════════════════════════════════════════════════════════════════════════
🧠 ALIMENTAÇÃO DE AGENTES
═══════════════════════════════════════════════════════════════════════════

1. ✅ SIM - Atualizar AGENT-*.md + MEMORY-*.md
2. 📝 APENAS MEMORY - Atualizar apenas memórias
3. ⏭️ PULAR - Não atualizar agentes agora

═══════════════════════════════════════════════════════════════════════════
```

### 7.4 - Execute Enrichment (if approved)
```
FOR each AGENT in agents_impacted:

  ⛔ ENFORCEMENT: validate write to MEMORY-*.md
  UPDATE MEMORY with Team Agreement style

  IF "SIM" selected:
    ⛔ ENFORCEMENT: validate write to AGENT-*.md
    UPDATE AGENT with Job Description
```

### 7.5 - Template Evolution Check ⚡ TRIGGER AUTOMÁTICO
```
⛔ CHECKPOINT TEMPLATE-EVOLUTION

PARA CADA insight/framework descoberto:

  VERIFICAR: Cabe em alguma das 10 PARTEs do template AGENT-MD-FLEXIVEL-V1?

  ┌─────────────────────────────────────────────────────────────────────┐
  │  PARTES DO TEMPLATE ATUAL                                           │
  ├─────────────────────────────────────────────────────────────────────┤
  │  PARTE 1  │ COMPOSIÇÃO ATÔMICA (arquitetura, DNA)                  │
  │  PARTE 2  │ GRÁFICO DE IDENTIDADE (radar, quem sou)                │
  │  PARTE 3  │ MAPA NEURAL (TOP insights)                             │
  │  PARTE 4  │ NÚCLEO OPERACIONAL (missão, triggers)                  │
  │  PARTE 5  │ SISTEMA DE VOZ (tom, frases)                           │
  │  PARTE 6  │ MOTOR DE DECISÃO (heurísticas)                         │
  │  PARTE 7  │ INTERFACES DE CONEXÃO (agentes)                        │
  │  PARTE 8  │ PROTOCOLO DE DEBATE (council)                          │
  │  PARTE 9  │ MEMÓRIA EXPERIENCIAL (casos, calibração)               │
  │  PARTE 10 │ EXPANSÕES E REFERÊNCIAS (knowledge base)               │
  └─────────────────────────────────────────────────────────────────────┘

  IF conteúdo NÃO CABE:
    IF relevante para MÚLTIPLOS agentes (>1):
      IF substância suficiente (>3 insights OU 1 framework):

        ⚡ TRIGGER: TEMPLATE-EVOLUTION-PROTOCOL

        → Aplicar /core/templates/agents/TEMPLATE-EVOLUTION-PROTOCOL.md
        → Propor evolução (NOVA_PARTE ou NOVA_SUBSECAO)
        → Se NOVA_SUBSECAO: aprovação automática
        → Se NOVA_PARTE: solicitar aprovação do usuário

    ELSE:
      → Adicionar como subsecção específica do agente afetado
      → NÃO propagar para outros agentes

LOG: Registrar em EVOLUTION-LOG.md se trigger ativado
```

### ✓ CHECKPOINT POST-7
```
[ ] CP-POST-7.A: MEMORYs atualizados (se aprovado)
[ ] CP-POST-7.B: AGENTs atualizados (se "SIM" selecionado)
[ ] CP-POST-7.C: Template evolution verificado
[ ] CP-POST-7.D: Se trigger ativado → proposta documentada
```

---

## PHASE 8: FINALIZATION + EXECUTION REPORT

### 8.1 - Automatic Actions
```
8.1.1 RAG INDEX
  EXECUTE: python scripts/rag_index.py --knowledge --force

8.1.2 FILE REGISTRY
  EXECUTE: python scripts/file_registry.py --scan

8.1.3 SESSION-STATE
  UPDATE /system/SESSION-STATE.md
  ADD $SOURCE_ID to processed files

8.1.4 EVOLUTION-LOG (if structural change)
  UPDATE /system/EVOLUTION-LOG.md

8.1.5 ROLE TRACKING
  UPDATE /agents/DISCOVERY/role-tracking.md

8.1.6 AUDIT LOG
  APPEND to /logs/AUDIT/audit.jsonl
```

### 8.2 - Verification Checklist (CHECKPOINT 7)
```
VERIFICAÇÃO FINAL - 9 ITENS OBRIGATÓRIOS:

[ ] 7.A: CHUNKS-STATE.json contém chunks do $SOURCE_ID
[ ] 7.B: CANONICAL-MAP.json atualizado com entidades
[ ] 7.C: INSIGHTS-STATE.json contém insights do $SOURCE_ID
[ ] 7.D: NARRATIVES-STATE.json contém narrativa para $SOURCE_PERSON
[ ] 7.E: Pelo menos 1 dossiê em /knowledge/dossiers/
[ ] 7.F: RAG index inclui novos arquivos
[ ] 7.G: file-registry.json tem entrada para $ARGUMENTS
[ ] 7.H: SESSION-STATE.md atualizado com $SOURCE_ID
[ ] 7.I: audit.jsonl contém entrada da sessão

Se qualquer check falhar: ⛔ EXIT("Verificação final falhou")
```

### 8.3 - Generate Execution Report
```
═══════════════════════════════════════════════════════════════════════════
                        EXECUTION REPORT
                        Pipeline Jarvis v2.1
═══════════════════════════════════════════════════════════════════════════

📅 Data: {TODAY}
📁 Fonte: {SOURCE_PERSON} ({SOURCE_ID})
📄 Arquivo: {filename}

┌─────────────────────────────────────────────────────────────────────────┐
│ MÉTRICAS                                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ Chunks criados:      {N}                                                │
│ Entidades resolvidas:{N}                                                │
│ Insights extraídos:  {N} ({HIGH} HIGH, {MED} MED, {LOW} LOW)           │
│ Narrativas geradas:  {N} pessoas, {N} temas                            │
│ Dossiês compilados:  {N} criados, {N} atualizados                      │
│ Agentes alimentados: {list}                                             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ STATE FILES                                                              │
├─────────────────────────────────────────────────────────────────────────┤
│ CHUNKS-STATE.json:     ✅ {total_chunks} chunks                         │
│ CANONICAL-MAP.json:    ✅ {total_entities} entidades                    │
│ INSIGHTS-STATE.json:   ✅ {total_insights} insights                     │
│ NARRATIVES-STATE.json: ✅ {total_narratives} narrativas                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ CHECKPOINTS                                                              │
├─────────────────────────────────────────────────────────────────────────┤
│ PRE-Execution:  ✅ All passed                                           │
│ POST-Execution: ✅ All passed                                           │
│ Final (7):      ✅ 9/9 items verified                                   │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
✅ PIPELINE JARVIS v2.1 COMPLETE
═══════════════════════════════════════════════════════════════════════════
```

### 8.4 - Write Execution Log
```
WRITE to /logs/EXECUTION/EXEC-{SOURCE_ID}-{DATE}.md
using LOG 1 template from LOG-TEMPLATES.md
```

### 8.5 - Prompt for Next Session
```
Pipeline 100% completo para: $SOURCE_PERSON ($SOURCE_ID)

Deseja processar outro arquivo agora?
- Caminho local: /process-jarvis inbox/PASTA/arquivo.txt
- YouTube URL: Cole a URL

Se não, sistema pronto para:
- /rag-search "query"
- Consulta a agentes
```

---

## ERROR RECOVERY

| Error | Recovery |
|-------|----------|
| File not found | EXIT(FILE_NOT_FOUND) |
| State file corrupted | Backup + recreate from template |
| Checkpoint failed | Log error + EXIT |
| Write permission denied | EXIT(PERMISSION_DENIED) |
| RAG index failed | ⚠️ WARN, continue |
| Verification failed | Log all failed items + EXIT |

---

## AUDIT TRAIL

Cada execução do pipeline gera entradas em:

1. `/logs/AUDIT/audit.jsonl` - Log estruturado
2. `/logs/EXECUTION/EXEC-{ID}-{DATE}.md` - Relatório visual
3. `/system/SESSION-STATE.md` - Estado do sistema

---

## CHANGELOG

| Versão | Data | Mudanças |
|--------|------|----------|
| 2.1.0 | 2025-12-18 | Consolidação 9→8 fases, enforcement integrado, logs obrigatórios |
| 2.0.0 | 2025-12-16 | Pipeline BATCH, checkpoints PRE |
| 1.0.0 | 2025-12-15 | Versão inicial |
