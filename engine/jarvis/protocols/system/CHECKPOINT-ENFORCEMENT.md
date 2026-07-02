# CHECKPOINT ENFORCEMENT PROTOCOL

> **Versão:** 1.0.0
> **Pipeline:** Jarvis → Todas as Etapas
> **Propósito:** Bloquear execução de etapas sem pré-requisitos

---

## PRINCÍPIO FUNDAMENTAL

```
⛔ NENHUMA ETAPA PODE EXECUTAR SEM VALIDAR CHECKPOINTS ANTERIORES
```

---

## MAPA DE DEPENDÊNCIAS

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE JARVIS v2.0                            │
│                                                                         │
│  [ETAPA 1.1] ──────────────────────────────────────────────────────────┐│
│  CHUNKING                                                               ││
│  ├─ INPUT: Transcrição bruta (inbox/*.txt)                          ││
│  ├─ OUTPUT: CHUNKS-STATE.json                                          ││
│  └─ CHECKPOINT: Arquivo existe + chunks[] não vazio                    ││
│                              │                                          ││
│                              ▼                                          ││
│  [ETAPA 1.2] ──────────────────────────────────────────────────────────┐││
│  ENTITY RESOLUTION                                                      │││
│  ├─ REQUIRES: CHUNKS-STATE.json com chunks                             │││
│  ├─ OUTPUT: CANONICAL-MAP.json                                         │││
│  └─ CHECKPOINT: canonical_state existe + entities mapeadas             │││
│                              │                                          │││
│                              ▼                                          │││
│  [ETAPA 2.1] ──────────────────────────────────────────────────────────┐││││
│  INSIGHT EXTRACTION                                                     │││││
│  ├─ REQUIRES: CHUNKS-STATE.json + CANONICAL-MAP.json                   │││││
│  ├─ OUTPUT: INSIGHTS-STATE.json                                        │││││
│  └─ CHECKPOINT: insights_state com persons{} e themes{} não vazios     │││││
│                              │                                          │││││
│                              ▼                                          │││││
│  [ETAPA 3.1] ──────────────────────────────────────────────────────────┐│││││
│  NARRATIVE SYNTHESIS                                                    ││││││
│  ├─ REQUIRES: INSIGHTS-STATE.json com insights                         ││││││
│  ├─ OUTPUT: NARRATIVES-STATE.json                                      ││││││
│  └─ CHECKPOINT: persons{} e themes{} com narrativas                    ││││││
│                              │                                          ││││││
│                              ▼                                          ││││││
│  [ETAPA 4.0] ──────────────────────────────────────────────────────────┐││││││
│  DOSSIER COMPILATION                                                    │││││││
│  ├─ REQUIRES: NARRATIVES-STATE.json                                    │││││││
│  ├─ OUTPUT: DOSSIER-*.md em /knowledge/dossiers/                    │││││││
│  └─ CHECKPOINT: Dossiês gerados para cada entidade com narrativa       │││││││
│                                                                         │││││││
└─────────────────────────────────────────────────────────────────────────┘││││││
```

---

## CHECKPOINTS OBRIGATÓRIOS

### ANTES DE ETAPA 1.1 (Chunking)

| Checkpoint | Validação | Ação se Falhar |
|------------|-----------|----------------|
| CP-1.1.A | Arquivo de transcrição existe | ⛔ PARAR - "Arquivo não encontrado" |
| CP-1.1.B | Arquivo tem conteúdo (> 100 chars) | ⛔ PARAR - "Transcrição vazia ou muito curta" |
| CP-1.1.C | Metadados identificáveis (fonte) | ⚠️ WARN - "Fonte não identificada, usar UNKNOWN" |

### ANTES DE ETAPA 1.2 (Entity Resolution)

| Checkpoint | Validação | Ação se Falhar |
|------------|-----------|----------------|
| CP-1.2.A | CHUNKS-STATE.json existe | ⛔ PARAR - "Execute Etapa 1.1 primeiro" |
| CP-1.2.B | chunks[] tem elementos | ⛔ PARAR - "Nenhum chunk para processar" |
| CP-1.2.C | Cada chunk tem id_chunk único | ⛔ PARAR - "Chunks com IDs duplicados" |

### ANTES DE ETAPA 2.1 (Insight Extraction)

| Checkpoint | Validação | Ação se Falhar |
|------------|-----------|----------------|
| CP-2.1.A | CHUNKS-STATE.json existe | ⛔ PARAR - "Execute Etapa 1.1 primeiro" |
| CP-2.1.B | CANONICAL-MAP.json existe | ⛔ PARAR - "Execute Etapa 1.2 primeiro" |
| CP-2.1.C | canonical_state tem entidades | ⚠️ WARN - "Sem entidades canônicas, usar nomes raw" |

### ANTES DE ETAPA 3.1 (Narrative Synthesis)

| Checkpoint | Validação | Ação se Falhar |
|------------|-----------|----------------|
| CP-3.1.A | INSIGHTS-STATE.json existe | ⛔ PARAR - "Execute Etapa 2.1 primeiro" |
| CP-3.1.B | insights_state.persons não vazio | ⚠️ WARN - "Sem insights de pessoas" |
| CP-3.1.C | insights_state.themes não vazio | ⚠️ WARN - "Sem insights de temas" |

### ANTES DE ETAPA 4.0 (Dossier Compilation)

| Checkpoint | Validação | Ação se Falhar |
|------------|-----------|----------------|
| CP-4.0.A | NARRATIVES-STATE.json existe | ⛔ PARAR - "Execute Etapa 3.1 primeiro" |
| CP-4.0.B | Pelo menos 1 pessoa com narrativa | ⛔ PARAR - "Nenhuma narrativa para compilar" |
| CP-4.0.C | open_loops identificados | ⚠️ WARN - "Verificar open_loops pendentes" |

---

## MENSAGENS DE ERRO PADRONIZADAS

```
⛔ CHECKPOINT FALHOU: {código}
   Etapa: {etapa_atual}
   Requisito: {descrição}
   Ação: {ação_necessária}

   Execute: {comando_ou_etapa_anterior}
```

**Exemplo:**
```
⛔ CHECKPOINT FALHOU: CP-2.1.B
   Etapa: 2.1 (Insight Extraction)
   Requisito: CANONICAL-MAP.json deve existir
   Ação: Entity Resolution não foi executado

   Execute: Etapa 1.2 antes de continuar
```

---

## VALIDAÇÃO DE INTEGRIDADE (opcional)

Script de validação rápida:

```bash
# Verificar estado do pipeline
python scripts/pipeline_validator.py --check

# Output esperado:
# ✅ CHUNKS-STATE.json: 96 chunks
# ✅ CANONICAL-MAP.json: 15 entidades
# ✅ INSIGHTS-STATE.json: 3 persons, 5 themes
# ✅ NARRATIVES-STATE.json: 3 persons, 5 themes
#
# Pipeline Status: READY para Etapa 4.0
```

---

## INTEGRAÇÃO COM PROTOCOLOS

Cada prompt de etapa DEVE iniciar com:

```
ANTES DE EXECUTAR, VALIDE:
[ ] Checkpoint {X} passou
[ ] Checkpoint {Y} passou
[ ] Checkpoint {Z} passou

Se qualquer checkpoint falhar: PARE e reporte o erro.
```

---

## REGRAS INVIOLÁVEIS

1. **NUNCA pular etapas** - Mesmo que pareça desnecessário
2. **NUNCA ignorar ⛔ PARAR** - Warnings (⚠️) podem continuar, PARADAs não
3. **SEMPRE reportar** - Qual checkpoint falhou e por quê
4. **RASTREABILIDADE** - Logar qual checkpoint foi validado

---

## CHANGELOG

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0.0 | 2025-12-18 | Criação inicial do protocolo |
