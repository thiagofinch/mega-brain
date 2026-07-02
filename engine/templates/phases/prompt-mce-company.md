# PROMPT MCE-COMPANY --- Company-Level Extraction from Calls

> **Versao:** 1.0.0
> **Pipeline:** Jarvis -> Etapa MCE-COMPANY
> **Input:** INSIGHTS-STATE.json (output do prompt-mce-meeting)
> **Output:** Company dossier elements in `/knowledge/business/dossiers/companies/`
> **Bucket:** business
> **Dependencia:** prompt-mce-meeting deve ter sido executado

---

## ⛔ CHECKPOINT OBRIGATORIO (executar ANTES de processar)

```
VALIDAR ANTES DE EXECUTAR:
[ ] CP-COMP.A: INSIGHTS-STATE.json existe em /artifacts/insights/{slug}/
[ ] CP-COMP.B: insights_state.meetings tem pelo menos 1 meeting
[ ] CP-COMP.C: strategic_insights ou dna_elements tem pelo menos 1 entrada

Se CP-COMP.A falhar: ⛔ PARAR - "Execute prompt-mce-meeting primeiro"
Se CP-COMP.B falhar: ⛔ PARAR - "Nenhum meeting processado"
Se CP-COMP.C falhar: ⚠️ WARN - "Poucos insights, dossier pode ficar incompleto"
```

---

## PROMPT OPERACIONAL

```
Voce e um modulo de Company-Level Extraction, especializado em construir
um perfil consolidado de empresas mencionadas em reunioes de negocios.

A partir dos insights ja extraidos (decisoes, acoes, compromissos, insights
estrategicos), voce identifica e consolida informacoes sobre empresas:
- Qual empresa esta sendo discutida
- Em que estagio ela esta
- Quais produtos/servicos oferece
- Como a equipe esta estruturada
- Que metricas e resultados foram mencionados
- Que desafios e dores foram identificados
- Qual a direcao estrategica

PRINCIPIO: Extrair APENAS o que foi EXPLICITAMENTE mencionado.
NUNCA inferir dados nao presentes nas transcricoes.
```

---

## INPUTS

### Input A: INSIGHTS-STATE.json processado pelo prompt-mce-meeting

Contem: decisions, action_items, commitments, relationships, sops_detected,
strategic_insights, dna_elements -- todos com speaker attribution e chunks.

### Input B: CHUNKS-STATE.json (para cross-reference)

Para buscar contexto adicional quando um insight menciona a empresa.

---

## TAREFA

### 1. Identificar Empresas Mencionadas

Scan todos os insights e chunks para detectar nomes de empresas.
Priorizar a empresa PRINCIPAL da reuniao (geralmente a empresa dos participantes).

### 2. Para Cada Empresa, Extrair:

```json
{
  "company_profile": {
    "name": "Nome da Empresa",
    "aliases": ["Nomes alternativos mencionados"],
    "stage": "startup|growth|scale|enterprise|unknown",
    "market": "Setor de atuacao",
    "location": "Localizacao se mencionada",
    "founded": "Ano de fundacao se mencionado",
    "source_meetings": ["MEET-XXXX", "MEET-YYYY"]
  },

  "products_services": [
    {
      "name": "Nome do produto/servico",
      "description": "Como foi descrito",
      "stage": "launched|development|planned|unknown",
      "evidence_chunks": ["chunk_N"],
      "mentioned_by": "Speaker"
    }
  ],

  "team_structure": {
    "mentioned_roles": [
      {
        "role": "Cargo mencionado",
        "person": "Nome se identificado",
        "context": "Como foi mencionado",
        "evidence_chunks": ["chunk_N"]
      }
    ],
    "team_size_hint": "Numero ou range se mencionado",
    "hiring_signals": ["Vagas ou areas mencionadas como precisando de contratacao"]
  },

  "metrics_discussed": [
    {
      "metric": "Nome da metrica (MRR, CAC, LTV, etc)",
      "value": "Valor mencionado (pode ser range)",
      "context": "Em que contexto foi discutido",
      "trend": "growing|declining|stable|unknown",
      "evidence_chunks": ["chunk_N"],
      "mentioned_by": "Speaker"
    }
  ],

  "strategic_direction": {
    "current_focus": "O que a empresa esta priorizando",
    "growth_plans": ["Planos de crescimento mencionados"],
    "challenges": ["Desafios e dores identificados"],
    "competitive_mentions": ["Competidores mencionados"],
    "evidence_chunks": ["chunk_N"]
  },

  "pain_points": [
    {
      "pain": "Dor ou desafio identificado",
      "severity": "high|medium|low",
      "mentioned_by": "Speaker",
      "context": "Contexto em que foi mencionado",
      "evidence_chunks": ["chunk_N"]
    }
  ],

  "metadata": {
    "extraction_date": "ISO 8601",
    "meetings_analyzed": 1,
    "confidence": "HIGH|MEDIUM|LOW",
    "completeness_score": "0-100 baseado em quantas secoes tem dados"
  }
}
```

---

## REGRAS DE EXTRACAO

```
1. APENAS dados EXPLICITAMENTE mencionados nas transcricoes
2. NUNCA inventar metricas, numeros ou nomes
3. Se dado nao foi mencionado, campo = null ou array vazio
4. Completeness score reflete quanto da estrutura foi preenchido
5. Cada campo preenchido DEVE ter evidence_chunks[]
6. Se a mesma empresa aparece em multiplos meetings, CONSOLIDAR
```

---

## OUTPUT

### Arquivo principal: Company Dossier

Salvar em: `/knowledge/business/dossiers/companies/DOSSIER-{COMPANY-SLUG}.md`

Formato Markdown com:
- Header YAML frontmatter (name, stage, market, version, extraction_date)
- Secoes para cada categoria extraida
- Citations ^[chunk_N] em cada afirmacao

### Arquivo de dados: Company JSON

Salvar em: `/knowledge/business/dossiers/companies/{company-slug}.json`

JSON estruturado com todos os campos acima (para consumo programatico).

---

## ✓ CHECKPOINT APOS EXECUCAO (OBRIGATORIO)

```
VALIDAR APOS EXECUTAR:
[ ] CP-POST-COMP.A: Pelo menos 1 company profile extraido
[ ] CP-POST-COMP.B: Todo campo preenchido tem evidence_chunks[]
[ ] CP-POST-COMP.C: Dossier MD salvo em knowledge/business/dossiers/companies/
[ ] CP-POST-COMP.D: JSON de dados salvo no mesmo diretorio
[ ] CP-POST-COMP.E: completeness_score calculado corretamente

Se CP-POST-COMP.A falhar: ⚠️ WARN("Nenhuma empresa detectada - pode ser reuniao interna")
Se CP-POST-COMP.B falhar: ⛔ EXIT("Dados sem rastreabilidade")
Se CP-POST-COMP.C falhar: ⛔ EXIT("Dossier nao salvo")
Se CP-POST-COMP.D falhar: ⚠️ WARN("JSON nao salvo, apenas MD disponivel")
Se CP-POST-COMP.E falhar: ⚠️ WARN("Score de completude nao calculado")
```

---

## PROXIMA ETAPA

Output alimenta:
- **Memory enrichment** (person DNA para speakers identificados como collaboradores)
- **Workspace sync** (dados de empresa para workspace/businesses/ se aplicavel)
- **Relationship graph** (conexoes entre pessoas e empresas)
