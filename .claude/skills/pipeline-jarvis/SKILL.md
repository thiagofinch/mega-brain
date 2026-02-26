# SKILL-PIPELINE-JARVIS
## Padrões do Pipeline de Processamento Jarvis

> **Auto-Trigger:** Processamento de novo material, comando /process
> **Keywords:** "processar", "pipeline", "jarvis", "novo material", "inbox"
> **Prioridade:** ALTA

---

## PROPÓSITO

Garantir que todo processamento via Pipeline Jarvis siga:
- As 8 fases obrigatórias
- Checkpoints de validação
- Logs estruturados
- Integração completa

---

## QUANDO USAR

### ✅ USAR quando:
- Processar qualquer material novo
- Executar /process ou /scan-inbox
- Material entra no inbox
- Reprocessar material existente

### ❌ NÃO USAR quando:
- Consultas (queries ao RAG)
- Criação manual de documentos
- Operações que não envolvem novo conteúdo

---

## AS 8 FASES DO PIPELINE

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE JARVIS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FASE 1: INITIALIZATION                                          │
│  └── Validação, setup, identificação de fonte                   │
│                                                                  │
│  FASE 2: CHUNKING                                                │
│  └── Segmentação semântica do conteúdo                          │
│                                                                  │
│  FASE 3: ENTITY RESOLUTION                                       │
│  └── Canonicalização de entidades                               │
│                                                                  │
│  FASE 4: INSIGHT EXTRACTION                                      │
│  └── Extração com tags DNA                                      │
│                                                                  │
│  FASE 5: NARRATIVE SYNTHESIS                                     │
│  └── Síntese narrativa coerente                                 │
│                                                                  │
│  FASE 6: DOSSIER COMPILATION                                     │
│  └── Compilação de dossiês                                      │
│                                                                  │
│  FASE 6.6: SOURCES COMPILATION                                   │
│  └── Compilação pessoa + tema                                   │
│                                                                  │
│  FASE 7: AGENT ENRICHMENT                                        │
│  └── Alimentação dos agentes                                    │
│                                                                  │
│  FASE 8: FINALIZATION                                            │
│  └── Relatório, logs, cleanup                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## FASE 1: INITIALIZATION

### Input
- Arquivo em `inbox/[FONTE]/`
- URL de vídeo
- Documento anexado

### Validações
```python
checklist = {
    "arquivo_existe": True,
    "formato_suportado": True,  # .mp4, .pdf, .txt, .md, .docx
    "tamanho_ok": True,         # < 500MB
    "fonte_identificada": True,  # Quem é o autor?
    "id_gerado": True           # Ex: CG004, AH-HR002
}
```

### Output
```json
{
  "source_id": "CG004",
  "source_type": "video",
  "source_person": "Cole Gordon",
  "source_company": "Cole Gordon",
  "original_path": "/inbox/cole-gordon/video.mp4",
  "estimated_duration": "45:00",
  "status": "ready_for_processing"
}
```

### Checkpoint
```
✅ FASE 1 COMPLETA
├── Source ID: CG004
├── Tipo: Video (45min)
├── Pessoa: Cole Gordon
└── Status: Pronto para chunking
```

---

## FASE 2: CHUNKING

### Regras de Segmentação

| Critério | Valor |
|----------|-------|
| Tamanho mínimo | 200 caracteres |
| Tamanho máximo | 1000 caracteres |
| Overlap | 50 caracteres |
| Break natural | Pausa > 2s, mudança de tema |

### Processo
1. Transcrever (se áudio/vídeo)
2. Identificar breaks naturais
3. Segmentar respeitando limites
4. Manter contexto suficiente
5. Registrar timestamps

### Output
```json
{
  "source_id": "CG004",
  "total_chunks": 127,
  "chunks": [
    {
      "chunk_id": "CG004-CHK-001",
      "start_time": "00:00:00",
      "end_time": "00:00:45",
      "content": "Texto do chunk...",
      "speaker": "Cole Gordon",
      "confidence": 0.94
    }
  ]
}
```

### Checkpoint
```
✅ FASE 2 COMPLETA
├── Chunks gerados: 127
├── Duração média: 21s
├── Confiança média: 0.91
└── Status: Pronto para entity resolution
```

---

## FASE 3: ENTITY RESOLUTION

### Entidades a Detectar

| Tipo | Exemplo | Ação |
|------|---------|------|
| Pessoa | "Cole Gordon" | Mapear para CANONICAL-MAP |
| Empresa | "Cole Gordon" | Mapear para companies |
| Conceito | "Show Rate" | Verificar glossário |
| Framework | "CLOSER Framework" | Mapear para frameworks |
| Métrica | "30% close rate" | Extrair valor numérico |

### Processo
1. Identificar menções de entidades
2. Resolver aliases (Sam = Sam Ovens)
3. Verificar CANONICAL-MAP
4. Criar novas entradas se necessário
5. Linkar chunks às entidades

### Output
```json
{
  "source_id": "CG004",
  "entities_found": {
    "persons": ["Cole Gordon", "Alex Hormozi"],
    "companies": ["Cole Gordon", "Alex Hormozi"],
    "concepts": ["Show Rate", "Close Rate", "Qualification"],
    "frameworks": ["CLOSER Framework"],
    "metrics": [
      {"name": "close_rate", "value": 0.30, "context": "target"}
    ]
  },
  "new_entities": 2,
  "resolved_aliases": 5
}
```

### Checkpoint
```
✅ FASE 3 COMPLETA
├── Entidades encontradas: 23
├── Pessoas: 4
├── Conceitos: 12
├── Novas entidades: 2
└── Status: Pronto para insight extraction
```

---

## FASE 4: INSIGHT EXTRACTION

### Aplicar SKILL-KNOWLEDGE-EXTRACTION

Para cada chunk:
1. Identificar se contém insight acionável
2. Classificar com tag DNA
3. Extrair em linguagem clara
4. Atribuir prioridade e confidence
5. Verificar duplicatas

### Output
```json
{
  "source_id": "CG004",
  "total_insights": 47,
  "by_dna_layer": {
    "FILOSOFIA": 3,
    "MODELO-MENTAL": 8,
    "HEURISTICA": 15,
    "FRAMEWORK": 12,
    "METODOLOGIA": 9
  },
  "by_priority": {
    "HIGH": 18,
    "MEDIUM": 21,
    "LOW": 8
  }
}
```

### Checkpoint
```
✅ FASE 4 COMPLETA
├── Insights extraídos: 47
├── Alta prioridade: 18
├── Média confiança: 0.87
└── Status: Pronto para narrative synthesis
```

---

## FASE 5: NARRATIVE SYNTHESIS

### Processo
1. Agrupar insights por tema
2. Ordenar cronologicamente
3. Criar narrativa coerente
4. Manter referências aos chunks
5. Gerar resumo executivo

### Output: SOURCE-[ID].md
```markdown
# SOURCE: CG004 - Cole Gordon - [Título]

> **Processado:** [Data]
> **Duração:** 45:00
> **Insights:** 47

---

## RESUMO EXECUTIVO

[Síntese de 3-5 parágrafos do conteúdo principal]

---

## PRINCIPAIS INSIGHTS

### [FILOSOFIA]
- [Insight 1]
- [Insight 2]

### [FRAMEWORK]
- [Framework principal explicado]

...

---

## TIMELINE

| Tempo | Tema | Insight Key |
|-------|------|-------------|
| 00:05 | Intro | [Insight] |
| 05:30 | Core | [Insight] |

---

## FONTES DOS CHUNKS

[Lista de chunk_ids para rastreabilidade]
```

---

## FASE 6: DOSSIER COMPILATION

### Atualizar ou Criar Dossiê

```markdown
# DOSSIER: [PESSOA/TEMA]

> **Última atualização:** [Data]
> **Fontes processadas:** [N]

---

## SÍNTESE CUMULATIVA

[Conhecimento acumulado de todas as fontes]

---

## FONTES

| ID | Tipo | Data | Insights |
|----|------|------|----------|
| CG001 | Video | [Data] | 32 |
| CG002 | PDF | [Data] | 18 |
| CG003 | Video | [Data] | 45 |
| CG004 | Video | [Data] | 47 |
```

---

## FASE 6.6: SOURCES COMPILATION

### Criar/Atualizar SOURCE por Pessoa + Tema

```
/knowledge/SOURCES/
└── COLE-GORDON/
    ├── SOURCE-SALES-MANAGEMENT.md  # Compilação de múltiplas fontes
    ├── SOURCE-CLOSING.md
    └── SOURCE-SHOW-RATES.md
```

---

## FASE 7: AGENT ENRICHMENT

### Para cada insight HIGH priority:
1. Identificar agentes afetados
2. Atualizar MEMORY dos agentes
3. Se nova metodologia → atualizar ROLE
4. Se novo framework → registrar

### Verificação de Threshold
```
Se pessoa tem 3+ fontes processadas E
   100+ insights extraídos:
   → Verificar se merece AGENT-PERSON
```

---

## FASE 8: FINALIZATION

### Relatório Final
```
════════════════════════════════════════════════════════════════
📊 PROCESSAMENTO CONCLUÍDO: CG004
════════════════════════════════════════════════════════════════

ESTATÍSTICAS
├── Chunks: 127
├── Insights: 47 (18 HIGH, 21 MEDIUM, 8 LOW)
├── Entidades: 23 (2 novas)
├── Tempo: 12m 34s

ARQUIVOS GERADOS
├── /processing/chunks/CG004-chunks.json
├── /processing/insights/CG004-insights.json
├── /knowledge/SOURCES/cole-gordon/SOURCE-CG004.md
├── /knowledge/dossiers/persons/DOSSIER-COLE-GORDON.md (atualizado)

AGENTES ATUALIZADOS
├── MEMORY-CLOSER.md (+5 entries)
├── MEMORY-SALES-MANAGER.md (+3 entries)

PRÓXIMAS AÇÕES
├── [ ] Revisar insights HIGH priority
├── [ ] Verificar conflitos detectados
└── [ ] Confirmar novas entidades no glossário

════════════════════════════════════════════════════════════════
```

### Atualizações Obrigatórias
- [ ] SESSION-STATE.md
- [ ] CANONICAL-MAP.json (se novas entidades)
- [ ] Glossário (se novos termos)
- [ ] FILE-REGISTRY
- [ ] RAG index

---

## ANTI-PATTERNS (NUNCA FAZER)

1. ❌ Pular fases do pipeline
2. ❌ Processar sem gerar source_id
3. ❌ Não verificar duplicatas
4. ❌ Não atualizar SESSION-STATE
5. ❌ Chunks sem timestamp
6. ❌ Insights sem referência ao chunk
7. ❌ Não indexar no RAG
8. ❌ Ignorar relatório final

---

## META-INFORMAÇÃO

- **Versão:** 1.0.0
- **Domínio:** Processamento
- **Prioridade:** ALTA
- **Dependências:** 
  - SKILL-KNOWLEDGE-EXTRACTION
  - SKILL-DOCS-MEGABRAIN
