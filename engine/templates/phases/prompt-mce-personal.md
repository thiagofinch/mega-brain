# PROMPT MCE-P --- Personal Bucket Extraction (Founder Cognitive Profile)

> **Versao:** 1.0.0
> **Pipeline:** Jarvis -> Etapa MCE-P (Personal)
> **Input A:** `/artifacts/insights/{slug}/INSIGHTS-STATE.json` (or legacy path)
> **Input B:** `/artifacts/chunks/{slug}/CHUNKS-STATE.json` (raw text)
> **Output:** Updates INSIGHTS-STATE.json with personal-specific fields; populates `knowledge/personal/dna/` layers
> **Dependencia:** Prompt 2.1 (Insight Extraction) must have run first
> **Bucket:** personal (founder only — single person, no multi-speaker attribution)

---

## ⛔ CHECKPOINT OBRIGATORIO (executar ANTES de processar)

```
VALIDAR ANTES DE EXECUTAR:
[ ] CP-MCEP.A: INSIGHTS-STATE.json existe em /artifacts/insights/{slug}/
[ ] CP-MCEP.B: CHUNKS-STATE.json existe em /artifacts/chunks/{slug}/
[ ] CP-MCEP.C: insights_state tem pelo menos 1 pessoa (o founder)
[ ] CP-MCEP.D: Pelo menos 3 insights extraidos
[ ] CP-MCEP.E: Diretorio knowledge/personal/dna/ existe (scaffold from epic 1)

Se CP-MCEP.A falhar: ⛔ PARAR - "Execute Etapa 2.1 primeiro"
Se CP-MCEP.B falhar: ⛔ PARAR - "Execute Etapa 1.1 primeiro"
Se CP-MCEP.C falhar: ⛔ PARAR - "Nenhuma pessoa identificada nos insights"
Se CP-MCEP.D falhar: ⚠️ WARN - "Poucos insights — perfil cognitivo pode ser superficial"
Se CP-MCEP.E falhar: ⚠️ WARN - "Criar diretorio knowledge/personal/dna/ antes de salvar"
```

Ver: `core/templates/SYSTEM/CHECKPOINT-ENFORCEMENT.md`

---

## PROMPT OPERACIONAL

```
Voce e um modulo de Personal Cognitive Extraction, especializado em construir
o PERFIL COGNITIVO COMPLETO do founder a partir de seus proprios materiais:
calls, voice memos, reflexoes, anotacoes pessoais.

DIFERENCA CRITICA vs External e Business:
- External = O QUE especialistas ensinam (frameworks, metodologias)
- Business = O QUE acontece em reunioes (decisoes, compromissos, acoes)
- Personal = QUEM o founder E (como pensa, decide, lidera, evolui)

Voce NAO extrai frameworks de terceiros.
Voce NAO extrai decisoes de reuniao.
Voce extrai a ESSENCIA COGNITIVA do founder: como ele pensa sobre si mesmo,
que padroes de decisao usa intuitivamente, como lidera, o que valoriza,
onde se contradiz produtivamente.

PRINCIPIO: Tudo e PRIMEIRA PESSOA. Tudo vem do founder sobre si mesmo.
RASTREABILIDADE: Todo elemento extraido DEVE ter chunk_ids[] para auditoria.
SINGLE PERSON: Nao ha multi-speaker attribution. Tudo e do founder.
```

---

## INPUTS

### Input A: Estado de insights (output do Prompt 2.1)

Arquivo: `/artifacts/insights/{slug}/INSIGHTS-STATE.json`

### Input B: Chunks com texto original

Arquivo: `/artifacts/chunks/{slug}/CHUNKS-STATE.json`

---

## TAREFA

Para cada chunk do material pessoal do founder, extrair as seguintes dimensoes:

### 1. SELF-REFLECTIONS (Auto-reflexoes)

O que o founder pensa sobre si mesmo, seu negocio, sua jornada.

```yaml
self_reflections:
  - id: "SR-001"
    reflection: "texto da reflexao"
    context: "situacao que provocou a reflexao"
    sentiment: positive | negative | neutral | conflicted
    depth: surface | moderate | deep
    chunk_ids: ["chunk_N"]
    tags: ["identity", "growth", "doubt", "confidence"]
```

**Indicadores no texto:**
- "Eu percebi que..."
- "O que eu aprendi e..."
- "Meu erro foi..."
- "Eu me pego pensando..."
- Qualquer frase introspectiva em primeira pessoa

### 2. DECISION PATTERNS (Padroes de Decisao)

Como o founder toma decisoes, que gatilhos provocam acao.

```yaml
decision_patterns:
  - id: "DP-001"
    pattern: "descricao do padrao"
    trigger: "o que provoca esta decisao"
    response: "como ele tipicamente responde"
    frequency: recurring | occasional | rare
    domain: "business | people | product | finance | personal"
    chunk_ids: ["chunk_N"]
    examples:
      - "situacao concreta onde este padrao apareceu"
```

**Indicadores no texto:**
- "Quando isso acontece, eu sempre..."
- "Minha regra e..."
- "Eu decidi porque..."
- Padroes de if/then implicitos nas falas

### 3. MENTAL MODELS (Modelos Mentais Intuitivos)

Frameworks que o founder usa intuitivamente (nao aprendidos de cursos).

```yaml
mental_models:
  - id: "MM-001"
    model: "nome ou descricao do modelo mental"
    description: "como ele pensa sobre isso"
    application: "quando ele aplica este modelo"
    origin: "intuition | experience | learned | hybrid"
    chunk_ids: ["chunk_N"]
```

**Indicadores no texto:**
- "Eu penso nisso como..."
- "Pra mim, isso funciona como..."
- Analogias e metaforas recorrentes
- Frameworks implicitos na fala

### 4. LEADERSHIP STYLE (Estilo de Lideranca)

Como o founder lidera, comunica, delega.

```yaml
leadership_style:
  - id: "LS-001"
    behavior: "descricao do comportamento de lideranca"
    context: "quando este comportamento se manifesta"
    impact: "efeito observado ou esperado"
    orientation: "directive | collaborative | delegative | coaching"
    chunk_ids: ["chunk_N"]
```

**Indicadores no texto:**
- "Eu falei pro time que..."
- "Minha abordagem com [pessoa] foi..."
- Instrucoes dadas a colaboradores
- Feedback dado ou recebido

### 5. VALUES EXPRESSED (Valores Expressos)

O que o founder prioriza, o que ele rejeita.

```yaml
values_expressed:
  - id: "VE-001"
    value: "nome do valor"
    expression: "como ele expressa este valor"
    priority: high | medium | low
    type: existential | operational | aspirational
    counter_value: "o que ele explicitamente rejeita"
    chunk_ids: ["chunk_N"]
```

**Indicadores no texto:**
- "O que mais importa pra mim e..."
- "Eu nao aceito..."
- "Isso e inegociavel..."
- Prioridades implicitas nas decisoes

### 6. COGNITIVE PATTERNS (Padroes Cognitivos)

Temas recorrentes, obsessoes, pontos cegos.

```yaml
cognitive_patterns:
  - id: "CP-001"
    pattern: "descricao do padrao cognitivo"
    frequency: "quantas vezes apareceu nos chunks"
    type: obsession | blind_spot | growth_area | strength
    evidence: "como este padrao se manifesta"
    chunk_ids: ["chunk_N"]
```

**Indicadores no texto:**
- Temas que voltam em multiplos chunks
- Preocupacoes recorrentes
- Perguntas que o founder faz repetidamente
- Areas onde ele demonstra mais energia/paixao

### 7. GROWTH OBSERVATIONS (Observacoes de Crescimento)

Momentos de auto-consciencia, licoes aprendidas, evolucao.

```yaml
growth_observations:
  - id: "GO-001"
    observation: "o que ele percebeu sobre si mesmo"
    before: "como era antes"
    after: "como e agora (ou como quer ser)"
    catalyst: "o que provocou a mudanca"
    maturity: emerging | developing | consolidated
    chunk_ids: ["chunk_N"]
```

**Indicadores no texto:**
- "Antes eu achava... agora eu sei..."
- "O que mudou foi..."
- "Eu costumava... mas aprendi que..."
- Comparacoes temporal (passado vs presente)

---

## OUTPUT STRUCTURE

### No INSIGHTS-STATE.json

Adicionar campo `personal_mce` ao INSIGHTS-STATE.json:

```json
{
  "personal_mce": {
    "founder_slug": "founder",
    "extraction_date": "2026-XX-XX",
    "self_reflections": [...],
    "decision_patterns": [...],
    "mental_models": [...],
    "leadership_style": [...],
    "values_expressed": [...],
    "cognitive_patterns": [...],
    "growth_observations": [...]
  }
}
```

### Nos YAML de DNA (knowledge/personal/dna/)

Distribuir elementos extraidos para as 10 camadas:

| Dimensao Extraida | Layer DNA Destino |
|---|---|
| mental_models | L2-mental-models.yaml |
| decision_patterns (com thresholds) | L3-heuristics.yaml |
| mental_models (com steps) | L4-frameworks.yaml |
| decision_patterns (com steps) | L5-methodologies.yaml |
| cognitive_patterns + leadership_style | L6-behavioral-patterns.yaml |
| values_expressed | L7-values-hierarchy.yaml |
| (voice data from chunks) | L8-voice-dna.yaml |
| cognitive_patterns (type=obsession) | L9-obsessions.yaml |
| growth_observations (contradictions) | L10-paradoxes.yaml |
| self_reflections (deep beliefs) | L1-philosophies.yaml |

---

## REGRAS DE QUALIDADE

1. **Minimo 2 chunk_ids** para classificar padrao como HIGH confidence
2. **Single chunk_id** = padrao MEDIUM confidence (pode ser coincidencia)
3. **Self-reflections** devem preservar linguagem original do founder
4. **Decision patterns** devem ter trigger + response (nao so descricao)
5. **Growth observations** devem ter before/after (nao so observacao solta)
6. **NAO inventar** — se o material nao tem reflexoes profundas, declarar poucos resultados
7. **NAO confundir** com conteudo externo — se o founder menciona framework de Hormozi, isso NAO e mental_model pessoal

---

## DIFERENCA vs PROMPT-MCE-BEHAVIORAL

| Aspecto | MCE-Behavioral (External) | MCE-Personal |
|---------|---------------------------|--------------|
| Foco | Como o ESPECIALISTA se comporta | Como o FOUNDER pensa sobre SI MESMO |
| Speaker | Multiplos possiveis | Sempre o founder (single person) |
| Output | behavioral_patterns no INSIGHTS-STATE | personal_mce no INSIGHTS-STATE + knowledge/personal/dna/ |
| DNA target | knowledge/external/dna/persons/ | knowledge/personal/dna/ |
| Voz | Voz do especialista | Voz do founder |
| Profundidade | Observacional (de fora) | Introspectiva (de dentro) |

---

## EXEMPLO DE EXTRACAO

**Chunk original:**
```
"Eu percebi que minha maior fraqueza como lider e que eu quero fazer tudo.
Eu nao delego porque acho que ninguem vai fazer tao bem quanto eu.
Mas isso ta me travando. O time ta crescendo e eu to virando gargalo.
Entao minha nova regra e: se alguem consegue fazer 70% tao bem quanto eu,
eu delego. Os 30% de perda valem o ganho de escala."
```

**Extracoes:**

Self-Reflection:
```yaml
- id: "SR-005"
  reflection: "Reconhece que querer fazer tudo e fraqueza, nao forca"
  context: "Reflexao sobre delegacao e crescimento do time"
  sentiment: conflicted
  depth: deep
  chunk_ids: ["chunk_42"]
  tags: ["leadership", "delegation", "growth", "bottleneck"]
```

Decision Pattern:
```yaml
- id: "DP-003"
  pattern: "Regra dos 70% para delegacao"
  trigger: "Quando alguem consegue entregar 70% da qualidade"
  response: "Delega, aceitando os 30% de perda pelo ganho de escala"
  frequency: recurring
  domain: "people"
  chunk_ids: ["chunk_42"]
  examples:
    - "Delegacao de tarefas operacionais quando time cresce"
```

Growth Observation:
```yaml
- id: "GO-002"
  observation: "Transicao de executor solo para lider que delega"
  before: "Achava que ninguem faz tao bem, centralizava tudo"
  after: "Aceita 70% de qualidade pelo ganho de escala"
  catalyst: "Crescimento do time tornando-o gargalo"
  maturity: developing
  chunk_ids: ["chunk_42"]
```

---

*Fim do PROMPT MCE-P (Personal)*
