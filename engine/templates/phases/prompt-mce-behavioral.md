# PROMPT MCE-1 --- Behavioral Pattern Extraction

> **Versao:** 1.0.0
> **Pipeline:** Jarvis -> Etapa MCE-1
> **Input:** `/artifacts/insights/INSIGHTS-STATE.json`
> **Output:** Adiciona campos `behavioral_patterns` ao INSIGHTS-STATE.json
> **Dependencia:** Prompt 2.1 (Insight Extraction) deve ter sido executado

---

## ⛔ CHECKPOINT OBRIGATORIO (executar ANTES de processar)

```
VALIDAR ANTES DE EXECUTAR:
[ ] CP-MCE1.A: INSIGHTS-STATE.json existe em /artifacts/insights/
[ ] CP-MCE1.B: insights_state.persons tem pelo menos 1 pessoa
[ ] CP-MCE1.C: Pelo menos 5 insights com chunks[] preenchidos
[ ] CP-MCE1.D: CHUNKS-STATE.json existe em /artifacts/chunks/ (para cross-reference)

Se CP-MCE1.A falhar: ⛔ PARAR - "Execute Etapa 2.1 primeiro"
Se CP-MCE1.B falhar: ⛔ PARAR - "Nenhuma pessoa com insights extraidos"
Se CP-MCE1.C falhar: ⚠️ WARN - "Poucos insights disponiveis, padrao comportamental pode ser superficial"
Se CP-MCE1.D falhar: ⚠️ WARN - "Sem chunks para cross-reference, citacoes limitadas"
```

Ver: `core/templates/SYSTEM/CHECKPOINT-ENFORCEMENT.md`

---

## PROMPT OPERACIONAL

```
Voce e um modulo de Behavioral Pattern Extraction, especializado em identificar
padroes comportamentais RECORRENTES a partir de insights ja extraidos.

Seu foco NAO e no QUE a pessoa sabe (DNA cognitivo), mas em COMO ela se comporta:
como reage a situacoes, que padroes de acao repete, que gatilhos provocam que respostas.

Voce trabalha sobre INSIGHTS-STATE.json (output do Prompt 2.1), analisando o conjunto
de insights de cada pessoa para detectar padroes comportamentais que se manifestam
em MULTIPLOS insights/chunks.

PRINCIPIO: Um padrao comportamental so e valido se aparece em 2+ chunks.
PRIORIDADE: Padroes que aparecem em 3+ chunks sao classificados como HIGH.
```

---

## INPUTS

### Input A: Estado de insights (output do Prompt 2.1)

Arquivo: `/artifacts/insights/INSIGHTS-STATE.json`

```json
{
  "insights_state": {
    "persons": {
      "Nome Canonico": [
        {
          "id": "INS-XX-NNN",
          "insight": "...",
          "quote": "...",
          "chunks": ["chunk_N", "chunk_M"],
          "tag": "[HEURISTICA]|[FILOSOFIA]|...",
          "priority": "HIGH|MEDIUM|LOW",
          "confidence": "HIGH|MEDIUM|LOW",
          "status": "new|updated|..."
        }
      ]
    },
    "themes": {},
    "version": "vN",
    "change_log": []
  }
}
```

### Input B: Chunks (para verificacao de texto original)

Arquivo: `/artifacts/chunks/CHUNKS-STATE.json` (consulta quando necessario para ler texto original dos chunks)

---

## TAREFA

Para cada PESSOA em insights_state.persons:

### 1. Analise TODOS os insights da pessoa em conjunto

- Leia todos os insights e quotes
- Identifique padroes de COMPORTAMENTO que se repetem entre insights
- Foque em COMO a pessoa age, reage e decide -- nao no conteudo tecnico

### 2. Tipos de padrao comportamental a detectar

| Tipo | O Que Procurar | Exemplo |
|------|----------------|---------|
| **REACAO** | Como reage a situacoes especificas | "Sempre desconstrui a pergunta antes de responder" |
| **DECISAO** | Como toma decisoes recorrentes | "Decide por eliminacao, nunca por selecao" |
| **COMUNICACAO** | Padroes de como comunica | "Usa numeros primeiro, historia depois" |
| **ENSINO** | Como transfere conhecimento | "Sempre comeca com o framework, depois o exemplo" |
| **CONFLITO** | Como lida com oposicao | "Reframe imediato -- transforma objecao em pergunta" |
| **PRIORIDADE** | O que prioriza consistentemente | "Revenue antes de sistemas, sempre" |

### 3. Para cada padrao detectado, preencher

| Campo | Descricao | Obrigatorio |
|-------|-----------|-------------|
| `id` | Identificador unico: `BP-{PESSOA_SLUG}-NNN` (ex: BP-AH-001) | SIM |
| `nome` | Nome descritivo do padrao (PT-BR) | SIM |
| `tipo` | REACAO / DECISAO / COMUNICACAO / ENSINO / CONFLITO / PRIORIDADE | SIM |
| `descricao` | Descricao clara do padrao (2-3 frases) | SIM |
| `gatilho` | O que ATIVA este padrao (situacao, estímulo, contexto) | SIM |
| `resposta` | Como a pessoa REAGE quando o gatilho dispara | SIM |
| `frequencia_estimada` | Percentual estimado de ocorrencia (ex: "~80% das vezes") | SIM |
| `chunk_ids` | Array de chunk_ids onde o padrao e observavel | SIM (min 2) |
| `insight_ids` | Array de insight_ids que evidenciam o padrao | SIM (min 1) |
| `quotes` | Array de citacoes que demonstram o padrao | SIM (min 1) |
| `contexto` | Em que contexto o padrao aparece (sales, hiring, strategy, etc.) | SIM |
| `prioridade` | HIGH (3+ chunks) / MEDIUM (2 chunks) / LOW (inferido) | SIM |
| `confianca` | HIGH / MEDIUM / LOW + justificativa | SIM |
| `anti_padrao` | O que esta pessoa NUNCA faz nesta situacao (se detectavel) | NAO |

### 4. Regras de prioridade

| Prioridade | Criterio |
|------------|----------|
| **HIGH** | Padrao observado em 3+ chunks distintos |
| **MEDIUM** | Padrao observado em 2 chunks distintos |
| **LOW** | Padrao inferido de 1 chunk forte + contexto |

### 5. Regras de qualidade

- CADA padrao DEVE ter pelo menos 2 chunk_ids distintos (exceto LOW)
- chunk_ids DEVEM existir no CHUNKS-STATE.json
- Quotes DEVEM ser citacoes EXATAS dos chunks, nao parafrasagens
- Um insight pode evidenciar MULTIPLOS padroes
- Um padrao pode cruzar MULTIPLOS temas
- NAO INVENTAR padroes -- se nao ha evidencia em 2+ chunks, nao existe

### 6. Incrementalidade

- Se `behavioral_patterns` ja existe no INSIGHTS-STATE, MESCLAR com novos padroes
- Padroes existentes podem ter `chunk_ids` expandidos com novas evidencias
- Status de padrao: `new`, `reinforced` (mais evidencias), `updated` (corrigido)
- Registrar mudancas em `change_log`

---

## OUTPUT

O INSIGHTS-STATE.json recebe um novo campo `behavioral_patterns` POR PESSOA:

```json
{
  "insights_state": {
    "persons": {
      "Nome Canonico": [
        { "... insights existentes ..." }
      ]
    },
    "themes": {},
    "behavioral_patterns": {
      "Nome Canonico": [
        {
          "id": "BP-AH-001",
          "nome": "Desconstrucao Antes de Resposta",
          "tipo": "COMUNICACAO",
          "descricao": "Quando recebe uma pergunta estrategica, SEMPRE desconstrui a premissa da pergunta antes de oferecer sua resposta. Nao aceita o framing original.",
          "gatilho": "Pergunta estrategica ou pedido de opiniao",
          "resposta": "Desconstrui a pergunta, reframe com seus proprios termos, depois responde",
          "frequencia_estimada": "~90%",
          "chunk_ids": ["chunk_198", "chunk_203", "chunk_212"],
          "insight_ids": ["INS-AH-042", "INS-AH-055"],
          "quotes": [
            "That's the wrong question. The real question is...",
            "Before I answer that, let me reframe..."
          ],
          "contexto": "sales-strategy, hiring, scaling",
          "prioridade": "HIGH",
          "confianca": "HIGH - Observado em 3 chunks distintos com linguagem consistente",
          "anti_padrao": "Nunca aceita a premissa da pergunta sem questionar"
        }
      ]
    },
    "version": "vN+1",
    "change_log": [
      {
        "entity": "behavioral_pattern",
        "key": "Nome Canonico",
        "chunks": ["chunk_198", "chunk_203", "chunk_212"],
        "change": "new",
        "note": "MCE-1: Extraidos N padroes comportamentais"
      }
    ]
  }
}
```

---

## SALVAMENTO

Salvar estado atualizado em: `/artifacts/insights/INSIGHTS-STATE.json`

Manter TODOS os campos existentes (persons, themes, version, change_log).
ADICIONAR campo `behavioral_patterns` ao mesmo nivel de `persons` e `themes`.

---

## ✓ CHECKPOINT APOS EXECUCAO (OBRIGATORIO)

```
VALIDAR APOS EXECUTAR:
[ ] CP-POST-MCE1.A: behavioral_patterns existe no INSIGHTS-STATE.json
[ ] CP-POST-MCE1.B: Pelo menos 1 pessoa tem padroes extraidos
[ ] CP-POST-MCE1.C: Cada padrao tem chunk_ids[] com pelo menos 2 elementos (exceto LOW)
[ ] CP-POST-MCE1.D: Cada padrao tem quotes[] com pelo menos 1 citacao exata
[ ] CP-POST-MCE1.E: Todos os chunk_ids referenciados existem no CHUNKS-STATE.json
[ ] CP-POST-MCE1.F: INSIGHTS-STATE.json foi salvo com sucesso
[ ] CP-POST-MCE1.G: change_log registra os novos padroes

Se CP-POST-MCE1.A falhar: ⛔ EXIT("MCE-1 nao produziu behavioral_patterns")
Se CP-POST-MCE1.B falhar: ⛔ EXIT("MCE-1 nao extraiu padroes para nenhuma pessoa")
Se CP-POST-MCE1.C falhar: ⚠️ WARN("Padroes com rastreabilidade insuficiente")
Se CP-POST-MCE1.D falhar: ⛔ EXIT("Padroes sem citacoes - rastreabilidade obrigatoria")
Se CP-POST-MCE1.E falhar: ⚠️ WARN("chunk_ids invalidos encontrados")
Se CP-POST-MCE1.F falhar: ⛔ EXIT("Falha ao salvar INSIGHTS-STATE.json")
Se CP-POST-MCE1.G falhar: ⚠️ WARN("change_log nao atualizado")
```

**BLOQUEANTE:** Nao prosseguir para Etapa MCE-2 se checkpoints A, B, D, ou F falharem.

---

## PROXIMA ETAPA

Output alimenta **Prompt MCE-2: Identity Layer Extraction** (prompt-mce-identity.md).
