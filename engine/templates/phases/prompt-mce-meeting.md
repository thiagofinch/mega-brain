# PROMPT MCE-MEETING --- Meeting Transcript Extraction

> **Versao:** 1.0.0
> **Pipeline:** Jarvis -> Etapa MCE-MEETING
> **Input:** Chunked meeting transcript (CHUNKS-STATE.json)
> **Output:** Adiciona campos meeting-specific ao INSIGHTS-STATE.json
> **Bucket:** business
> **Dependencia:** Prompt 1.1 (Chunking) e 1.2 (Entity Resolution) devem ter sido executados

---

## ⛔ CHECKPOINT OBRIGATORIO (executar ANTES de processar)

```
VALIDAR ANTES DE EXECUTAR:
[ ] CP-MEET.A: CHUNKS-STATE.json existe em /artifacts/chunks/{slug}/
[ ] CP-MEET.B: CANONICAL-MAP.json existe em /artifacts/canonical/
[ ] CP-MEET.C: source_type == "meeting" ou "call" no metadata
[ ] CP-MEET.D: Pelo menos 2 speakers identificados nos chunks

Se CP-MEET.A falhar: ⛔ PARAR - "Execute Etapa 1.1 primeiro"
Se CP-MEET.B falhar: ⛔ PARAR - "Execute Etapa 1.2 primeiro"
Se CP-MEET.C falhar: ⚠️ WARN - "Conteudo pode nao ser meeting, extrair mesmo assim"
Se CP-MEET.D falhar: ⚠️ WARN - "Single speaker detectado, tratar como call unilateral"
```

---

## PROMPT OPERACIONAL

```
Voce e um modulo de Meeting Transcript Extraction, especializado em extrair
conhecimento OPERACIONAL e ESTRATEGICO de transcricoes de reunioes de negocios.

Seu foco e diferente de cursos/podcasts. Reunioes contem:
- DECISOES tomadas por pessoas especificas
- COMPROMISSOS e follow-ups acordados
- RELACOES entre participantes (quem reporta a quem, quem trabalha com quem)
- PROCESSOS operacionais descritos (SOPs implicitos)
- INSIGHTS estrategicos sobre mercado, produto, operacao
- ELEMENTOS DNA (filosofias, modelos mentais, heuristicas) expressos pelos speakers

PRINCIPIO: Atribuicao de speaker e OBRIGATORIA. Quem disse o que importa.
PRIORIDADE: Decisoes e compromissos sao SEMPRE HIGH priority.
```

---

## INPUTS

### Input A: Estado anterior de insights

Arquivo: `/artifacts/insights/{slug}/INSIGHTS-STATE.json`

Se nao existir, inicializar com estrutura vazia:

```json
{
  "insights_state": {
    "categories": {},
    "meetings": {},
    "version": "v1",
    "change_log": []
  }
}
```

### Input B: Chunks canonicalizados (output do Prompt 1.2)

```json
{
  "chunks": [
    {
      "id_chunk": "chunk_N",
      "texto": "...",
      "pessoas": ["Speaker Name"],
      "temas": ["..."],
      "meta": {
        "scope": "business",
        "corpus": "...",
        "source_type": "meeting|call",
        "source_id": "MEET-XXXX",
        "source_title": "Titulo da Reuniao",
        "source_datetime": "2026-01-15T14:00:00Z",
        "speakers": ["Speaker A", "Speaker B"]
      }
    }
  ],
  "canonical_state": { "...": "..." }
}
```

---

## TAREFA

Para cada chunk, extrair as seguintes categorias:

### 1. DECISIONS (Decisoes Tomadas)

Identificar momentos em que alguem decidiu algo concreto.

```json
{
  "id": "DEC-{SLUG}-NNN",
  "decision": "Descricao clara da decisao",
  "decided_by": "Nome da pessoa que decidiu",
  "context": "Situacao que levou a decisao",
  "impact": "O que muda com essa decisao",
  "chunks": ["chunk_N"],
  "priority": "HIGH",
  "scope": "business",
  "source": {
    "source_type": "meeting",
    "source_id": "MEET-XXXX",
    "source_title": "...",
    "source_datetime": "..."
  },
  "status": "new"
}
```

### 2. ACTION_ITEMS (Itens de Acao)

Tarefas atribuidas a pessoas especificas.

```json
{
  "id": "ACT-{SLUG}-NNN",
  "action": "Descricao da tarefa",
  "assigned_to": "Nome da pessoa responsavel",
  "assigned_by": "Quem atribuiu (se identificavel)",
  "deadline": "Data limite se mencionada (null se nao)",
  "dependencies": "Dependencias mencionadas",
  "chunks": ["chunk_N"],
  "priority": "HIGH|MEDIUM",
  "scope": "business",
  "source": { "..." : "..." },
  "status": "new"
}
```

### 3. COMMITMENTS (Compromissos)

Promessas e acordos feitos durante a reuniao.

```json
{
  "id": "CMT-{SLUG}-NNN",
  "commitment": "O que foi prometido/acordado",
  "committed_by": "Quem se comprometeu",
  "committed_to": "Para quem (se identificavel)",
  "follow_up": "Proximo passo acordado",
  "chunks": ["chunk_N"],
  "priority": "HIGH|MEDIUM",
  "scope": "business",
  "source": { "..." : "..." },
  "status": "new"
}
```

### 4. RELATIONSHIPS (Relacoes Detectadas)

Conexoes entre pessoas identificadas na conversa.

```json
{
  "id": "REL-{SLUG}-NNN",
  "person_a": "Nome",
  "person_b": "Nome",
  "relationship_type": "reports_to|works_with|partner|client|vendor|advisor",
  "evidence": "Frase que indica a relacao",
  "chunks": ["chunk_N"],
  "confidence": "HIGH|MEDIUM|LOW",
  "scope": "business",
  "source": { "..." : "..." },
  "status": "new"
}
```

### 5. SOPS_DETECTED (Processos Operacionais)

Processos repetitivos ou procedimentos descritos na conversa.

```json
{
  "id": "SOP-{SLUG}-NNN",
  "process_name": "Nome do processo identificado",
  "description": "Como o processo funciona",
  "steps": ["Passo 1", "Passo 2"],
  "owner": "Responsavel pelo processo (se identificavel)",
  "frequency": "daily|weekly|monthly|ad-hoc|unknown",
  "chunks": ["chunk_N"],
  "priority": "MEDIUM",
  "scope": "business",
  "source": { "..." : "..." },
  "status": "new"
}
```

### 6. STRATEGIC_INSIGHTS (Insights Estrategicos)

Observacoes sobre mercado, produto, competicao, crescimento.

```json
{
  "id": "STR-{SLUG}-NNN",
  "insight": "Observacao estrategica acionavel",
  "speaker": "Quem disse",
  "quote": "Citacao exata",
  "domain": "market|product|competition|growth|operations|finance|hiring",
  "chunks": ["chunk_N"],
  "tag": "[FILOSOFIA]|[MODELO-MENTAL]|[HEURISTICA]|[FRAMEWORK]|[METODOLOGIA]",
  "priority": "HIGH|MEDIUM|LOW",
  "scope": "business",
  "source": { "..." : "..." },
  "confidence": "HIGH|MEDIUM|LOW",
  "status": "new"
}
```

### 7. DNA_ELEMENTS (Elementos de DNA Cognitivo)

Filosofias, modelos mentais, heuristicas expressos pelos speakers. Mesma estrutura do prompt-2.1 mas com speaker attribution.

```json
{
  "id": "INS-{SLUG}-NNN",
  "insight": "Frase clara e acionavel",
  "speaker": "Quem expressou",
  "quote": "Citacao exata do texto original",
  "chunks": ["chunk_N"],
  "tag": "[FILOSOFIA]|[MODELO-MENTAL]|[HEURISTICA]|[FRAMEWORK]|[METODOLOGIA]",
  "priority": "HIGH|MEDIUM|LOW",
  "scope": "business",
  "corpus": "...",
  "source": { "..." : "..." },
  "confidence": "HIGH|MEDIUM|LOW",
  "status": "new"
}
```

---

## REGRAS DE PRIORIZACAO

| Priority | Criterio |
|----------|----------|
| **HIGH** | Decisao tomada, compromisso feito, acao atribuida, insight que muda estrategia |
| **MEDIUM** | Processo descrito, relacao identificada, observacao com potencial |
| **LOW** | Contexto periferico, mencao passageira |

---

## SPEAKER ATTRIBUTION (OBRIGATORIO)

```
REGRAS:
1. TODO insight/decisao/acao DEVE ter o campo speaker/decided_by/assigned_to preenchido
2. Se o speaker nao pode ser identificado, usar "Unknown Speaker"
3. Se multiplos speakers contribuem, listar o PRINCIPAL (quem fez a afirmacao)
4. Normalizar nomes usando CANONICAL-MAP.json
5. Respeitar a voz: usar as palavras EXATAS do speaker na citacao
```

---

## INCREMENTALIDADE

- Se INSIGHTS-STATE.json ja existe, MERGE com estado anterior
- Nao reescrever insights existentes
- Se insight novo contradiz anterior: `"status": "updated|contradiction"`
- Registrar em `change_log`
- Meeting-specific data vai em `insights_state.meetings[MEET-ID]`

---

## OUTPUT

```json
{
  "insights_state": {
    "categories": {
      "decisions": [{ "..." }],
      "action_items": [{ "..." }],
      "commitments": [{ "..." }],
      "relationships": [{ "..." }],
      "sops_detected": [{ "..." }],
      "strategic_insights": [{ "..." }],
      "dna_elements": [{ "..." }]
    },
    "meetings": {
      "MEET-XXXX": {
        "title": "Titulo da reuniao",
        "date": "2026-01-15",
        "speakers": ["Speaker A", "Speaker B"],
        "duration_minutes": 60,
        "decisions_count": 3,
        "actions_count": 5,
        "commitments_count": 2,
        "insights_count": 8,
        "sops_count": 1
      }
    },
    "version": "vN",
    "change_log": [
      {
        "entity": "meeting",
        "key": "MEET-XXXX",
        "change": "new",
        "categories_affected": ["decisions", "action_items", "strategic_insights"],
        "counts": { "decisions": 3, "actions": 5, "insights": 8 },
        "note": "Primeira extracao desta reuniao"
      }
    ]
  }
}
```

---

## SALVAMENTO

Salvar estado atualizado em: `/artifacts/insights/{slug}/INSIGHTS-STATE.json`

---

## ✓ CHECKPOINT APOS EXECUCAO (OBRIGATORIO)

```
VALIDAR APOS EXECUTAR:
[ ] CP-POST-MEET.A: insights_state.meetings[MEET-ID] existe
[ ] CP-POST-MEET.B: count(decisions + actions + commitments) > 0
[ ] CP-POST-MEET.C: Todo item tem speaker attribution (nao vazio)
[ ] CP-POST-MEET.D: INSIGHTS-STATE.json salvo com sucesso
[ ] CP-POST-MEET.E: Cada insight tem chunks[] com pelo menos 1 elemento

Se CP-POST-MEET.A falhar: ⛔ EXIT("Meeting nao registrado em meetings[]")
Se CP-POST-MEET.B falhar: ⛔ EXIT("Nenhuma decisao/acao/compromisso extraido")
Se CP-POST-MEET.C falhar: ⚠️ WARN("Items sem speaker attribution")
Se CP-POST-MEET.D falhar: ⛔ EXIT("Falha ao salvar INSIGHTS-STATE.json")
Se CP-POST-MEET.E falhar: ⛔ EXIT("Insights sem rastreabilidade")
```

**BLOQUEANTE:** Nao prosseguir sem checkpoints A, B, D, E.

---

## PROXIMA ETAPA

Output alimenta:
- **prompt-mce-company.md** (extrai dados de empresa a partir dos insights)
- **prompt-mce-behavioral.md** (detecta padroes comportamentais dos speakers)
- **Finalize** (memory enrichment + output routing para knowledge/business/)
