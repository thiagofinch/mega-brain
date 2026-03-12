# PROMPT MCE-3 --- Voice DNA Extraction

> **Versao:** 1.0.0
> **Pipeline:** Jarvis -> Etapa MCE-3
> **Input A:** `/artifacts/insights/INSIGHTS-STATE.json` (com todos os campos MCE-1 e MCE-2)
> **Input B:** `/artifacts/chunks/CHUNKS-STATE.json` (texto original dos chunks)
> **Output:** `knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml` (1 por pessoa)
> **Dependencia:** Prompt MCE-2 (Identity Layer Extraction) deve ter sido executado

---

## ⛔ CHECKPOINT OBRIGATORIO (executar ANTES de processar)

```
VALIDAR ANTES DE EXECUTAR:
[ ] CP-MCE3.A: INSIGHTS-STATE.json existe em /artifacts/insights/
[ ] CP-MCE3.B: CHUNKS-STATE.json existe em /artifacts/chunks/
[ ] CP-MCE3.C: insights_state.behavioral_patterns existe (MCE-1 executado)
[ ] CP-MCE3.D: insights_state.value_hierarchy existe (MCE-2 executado)
[ ] CP-MCE3.E: insights_state.persons tem pelo menos 1 pessoa com 10+ insights
[ ] CP-MCE3.F: Diretorio knowledge/external/dna/persons/ existe

Se CP-MCE3.A falhar: ⛔ PARAR - "Execute Etapa 2.1 primeiro"
Se CP-MCE3.B falhar: ⛔ PARAR - "Execute Etapa 1.1 primeiro"
Se CP-MCE3.C falhar: ⛔ PARAR - "Execute Etapa MCE-1 primeiro"
Se CP-MCE3.D falhar: ⛔ PARAR - "Execute Etapa MCE-2 primeiro"
Se CP-MCE3.E falhar: ⚠️ WARN - "Poucos insights - Voice DNA pode ser incompleto"
Se CP-MCE3.F falhar: ⚠️ WARN - "Criar diretorio knowledge/external/dna/persons/ antes de salvar"
```

Ver: `core/templates/SYSTEM/CHECKPOINT-ENFORCEMENT.md`

---

## PROMPT OPERACIONAL

```
Voce e um modulo de Voice DNA Extraction, especializado em capturar a
ASSINATURA VOCAL e COMUNICACIONAL unica de cada pessoa.

Voce NAO extrai o que a pessoa sabe (isso e DNA cognitivo).
Voce NAO extrai o que a pessoa faz (isso e behavioral patterns).
Voce extrai COMO a pessoa se expressa, comunica, persuade e reage verbalmente.

Seu output e um YAML estruturado que permite a um agente de IA ENCARNAR
a voz desta pessoa de forma autêntia: tom, frases, metáforas, padroes
de abertura e fechamento, vocabulario transformado.

Voce trabalha sobre:
- CHUNKS-STATE.json: texto original (para analise lexica e de frases)
- INSIGHTS-STATE.json: insights + quotes (frases ja identificadas como relevantes)
- behavioral_patterns: como a pessoa reage (para immune_system e behavioral_states)
- value_hierarchy + obsessions: para calibrar tone_profile

PRINCIPIO: Voice DNA deve capturar o que torna esta pessoa INCONFUNDIVEL.
Se trocar o nome, o leitor AINDA saberia quem esta falando.
```

---

## INPUTS

### Input A: INSIGHTS-STATE.json completo

Contem todos os campos: persons, themes, behavioral_patterns, value_hierarchy,
obsessions, paradoxes. Usar principalmente:
- `quotes` de insights (frases ja validadas como significativas)
- `behavioral_patterns` (para immune_system e behavioral_states)
- `value_hierarchy` e `obsessions` (para calibrar tone_profile)

### Input B: CHUNKS-STATE.json

Contem o texto bruto completo de cada chunk. Usar para:
- Analise lexica (vocabulary_transforms, forbidden_words)
- Deteccao de frases recorrentes (signature_phrases)
- Padroes de abertura e fechamento (communication_patterns)
- Metaforas e analogias recorrentes (metaphors)

---

## TAREFA

Para cada PESSOA com 10+ insights em insights_state.persons:

### 1. TONE PROFILE (6 dimensoes, escala 0-10)

Analise o CONJUNTO de quotes e textos dos chunks da pessoa para calibrar:

| Dimensao | O Que Mede | 0 = | 10 = |
|----------|------------|-----|------|
| `certainty` | Nivel de certeza nas afirmacoes | "Talvez", "Possivelmente" | "Sempre", "Com certeza", "100%" |
| `authority` | Posicionamento hierarquico no discurso | Par, colega | Mentor, especialista, autoridade |
| `warmth` | Temperatura emocional | Frio, clinico, distante | Caloroso, empatico, acolhedor |
| `directness` | Nivel de franqueza | Diplomatico, indireto | Direto, sem rodeios, blunt |
| `teaching_focus` | Orientacao para ensinar | Conversa informal | Aula estruturada, professor |
| `confidence` | Autoconfianca percebida | Humilde, duvida | Seguro, assertivo, bold |

**Regras:**
- Cada dimensao deve ter chunk_ids[] como evidencia (min 2)
- Justificativa de 1 frase por dimensao
- Scores devem ser derivados do TEXTO, nao inventados

### 2. SIGNATURE PHRASES (Frases de assinatura)

Busque em TODOS os chunks e quotes da pessoa frases que:
- Aparecem em 2+ chunks (recorrencia literal ou quase-literal)
- Sao MEMORAVEIS e identificaveis
- Representam a forma UNICA da pessoa se expressar

| Campo | Descricao | Obrigatorio |
|-------|-----------|-------------|
| `id` | VP-{PESSOA_SLUG}-NNN (ex: VP-AH-001) | SIM |
| `frase` | A frase exata (ou variacao mais frequente) | SIM |
| `variacoes` | Array de variacoes encontradas | NAO |
| `occurrence_count` | Quantas vezes aparece nos chunks | SIM |
| `chunk_ids` | Array de chunk_ids onde aparece | SIM (min 2) |
| `usage_context` | Quando/como a pessoa usa esta frase | SIM |
| `poder` | Score 1-10 (impacto persuasivo da frase) | SIM |

### 3. FORBIDDEN WORDS (Palavras que a pessoa NUNCA usa)

Analise o vocabulario geral dos chunks e identifique palavras/expressoes
que a pessoa consistentemente EVITA, mesmo quando o contexto as sugere.

| Campo | Descricao | Obrigatorio |
|-------|-----------|-------------|
| `palavra_ou_expressao` | A palavra/expressao evitada | SIM |
| `alternativa_usada` | O que a pessoa usa INSTEAD | SIM |
| `evidencia` | Como detectou a ausencia (chunk_ids de contextos onde deveria aparecer) | SIM |
| `confianca` | HIGH / MEDIUM / LOW | SIM |

**Regra:** Minimo 10 chunks analisados para detectar forbidden words com confianca.

### 4. IMMUNE SYSTEM (Sistema de reacao a provocacoes)

A partir dos behavioral_patterns tipo CONFLITO e REACAO, mapeie pares trigger-response:

| Campo | Descricao | Obrigatorio |
|-------|-----------|-------------|
| `id` | IM-{PESSOA_SLUG}-NNN | SIM |
| `trigger` | O que provoca a reacao (situacao/frase/desafio) | SIM |
| `response` | Como a pessoa reage VERBALMENTE | SIM |
| `intensidade` | 1-10 (quao forte e a reacao) | SIM |
| `chunk_ids` | Evidencias da reacao | SIM (min 1) |
| `behavioral_pattern_id` | BP-XX-NNN relacionado (se houver) | NAO |

### 5. METAPHORS (Metaforas recorrentes)

Identifique analogias e metaforas que a pessoa usa REPETIDAMENTE:

| Campo | Descricao | Obrigatorio |
|-------|-----------|-------------|
| `id` | MET-{PESSOA_SLUG}-NNN | SIM |
| `metafora` | A metafora/analogia em si | SIM |
| `significado` | O que a pessoa quer dizer com isso | SIM |
| `poder` | Score 1-10 (eficacia comunicacional) | SIM |
| `chunk_ids` | Onde aparece | SIM (min 1) |
| `occurrence_count` | Quantas vezes usada | SIM |

### 6. BEHAVIORAL STATES (Modos de operacao)

Identifique 3-5 "modos" distintos em que a pessoa opera, baseado na analise de tom, vocabulario e intensidade ao longo dos chunks:

| Campo | Descricao | Obrigatorio |
|-------|-----------|-------------|
| `nome` | Nome descritivo do modo (ex: "Teaching Mode", "War Room Mode") | SIM |
| `trigger` | O que ativa este modo | SIM |
| `tom` | Como o tom muda neste modo | SIM |
| `duracao` | Estimativa de duracao tipica | NAO |
| `sinais` | Frases/palavras que indicam o modo ativo | SIM (min 2) |
| `chunk_ids` | Exemplos de chunks neste modo | SIM (min 1) |

### 7. COMMUNICATION PATTERNS (Padroes de comunicacao)

| Subcampo | O Que Extrair |
|----------|---------------|
| `opening_hooks` | Como a pessoa ABRE um argumento (primeiras frases tipicas) |
| `story_structure` | Estrutura de suas historias (setup-conflict-resolution? example-first? framework-first?) |
| `closing_signatures` | Como FECHA um argumento ou bloco (frases de fechamento tipicas) |
| `transition_phrases` | Como faz transicoes entre topicos |

Cada subcampo deve ter chunk_ids[] de evidencia.

### 8. VOCABULARY TRANSFORMS (Transformacoes de vocabulario)

Mapeie como a pessoa TRANSFORMA conceitos comuns em seu vocabulario proprio:

| Campo | Descricao | Obrigatorio |
|-------|-----------|-------------|
| `conceito_comum` | O que a maioria diria | SIM |
| `transformacao` | Como esta pessoa diz | SIM |
| `chunk_ids` | Evidencia | SIM (min 1) |

Exemplos:
- "opiniao" -> "framework aplicado"
- "duvida" -> "desconstrucao por primeiros principios"
- "erro" -> "data point"

---

## OUTPUT (YAML)

Gerar 1 arquivo YAML por pessoa, seguindo o padrao dos outros DNA YAMLs:

```yaml
# knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml
# Gerado em: {YYYY-MM-DD}
# Fonte: INSIGHTS-STATE.json + CHUNKS-STATE.json (Pipeline MCE-3)

pessoa: "{Nome Canonico}"
versao: "1.0.0"
data_extracao: "{ISO-8601}"
total_signature_phrases: {N}
total_immune_triggers: {N}
total_metaphors: {N}
total_behavioral_states: {N}

# ═══════════════════════════════════════════════════════════════════════
# PERFIL TONAL (6 dimensoes, escala 0-10)
# ═══════════════════════════════════════════════════════════════════════

tone_profile:
  certainty:
    score: 9.2
    justificativa: "Usa linguagem absolutista em 85%+ das afirmacoes"
    chunk_ids: ["chunk_198", "chunk_212"]
  authority:
    score: 8.5
    justificativa: "Posiciona-se como mentor, nao como par"
    chunk_ids: ["chunk_203", "chunk_215"]
  warmth:
    score: 4.0
    justificativa: "Tom predominantemente pragmatico, baixa emocionalidade"
    chunk_ids: ["chunk_198", "chunk_204"]
  directness:
    score: 9.0
    justificativa: "Vai direto ao ponto, usa imperativo frequentemente"
    chunk_ids: ["chunk_199", "chunk_203"]
  teaching_focus:
    score: 8.0
    justificativa: "Estrutura explicacoes como aulas, usa frameworks"
    chunk_ids: ["chunk_203", "chunk_212"]
  confidence:
    score: 9.5
    justificativa: "Nunca hedges, declara com certeza absoluta"
    chunk_ids: ["chunk_198", "chunk_215"]

# ═══════════════════════════════════════════════════════════════════════
# FRASES DE ASSINATURA
# ═══════════════════════════════════════════════════════════════════════

signature_phrases:
  - id: "VP-AH-001"
    frase: "The beautiful part about this is..."
    variacoes:
      - "The beautiful thing about this model is..."
      - "What's beautiful about this..."
    occurrence_count: 4
    chunk_ids: ["chunk_198", "chunk_212", "chunk_215", "chunk_220"]
    usage_context: "Quando apresenta beneficio-chave de um sistema ou modelo"
    poder: 8

# ═══════════════════════════════════════════════════════════════════════
# PALAVRAS PROIBIDAS (que a pessoa nunca usa)
# ═══════════════════════════════════════════════════════════════════════

forbidden_words:
  - palavra_ou_expressao: "talvez"
    alternativa_usada: "Afirmacao direta sem hedge"
    evidencia: "Em 50+ chunks analisados, nunca usa qualificadores de incerteza"
    confianca: "HIGH"

# ═══════════════════════════════════════════════════════════════════════
# SISTEMA IMUNOLOGICO (trigger -> response)
# ═══════════════════════════════════════════════════════════════════════

immune_system:
  - id: "IM-AH-001"
    trigger: "Questionamento sobre se outbound funciona"
    response: "Resposta com certeza absoluta + analogia de indestrutibilidade + dados de conversao"
    intensidade: 9
    chunk_ids: ["chunk_198", "chunk_212"]
    behavioral_pattern_id: "BP-AH-001"

# ═══════════════════════════════════════════════════════════════════════
# METAFORAS RECORRENTES
# ═══════════════════════════════════════════════════════════════════════

metaphors:
  - id: "MET-AH-001"
    metafora: "Machine that is impossible to break"
    significado: "Sistema de receita resiliente que nao depende de fatores externos"
    poder: 9
    chunk_ids: ["chunk_212"]
    occurrence_count: 3

# ═══════════════════════════════════════════════════════════════════════
# ESTADOS COMPORTAMENTAIS (modos de operacao)
# ═══════════════════════════════════════════════════════════════════════

behavioral_states:
  - nome: "Teaching Mode"
    trigger: "Quando explica conceito ou framework"
    tom: "Estruturado, paciente, usa numeros e exemplos"
    duracao: "2-5 minutos por bloco"
    sinais:
      - "Let me walk you through..."
      - "The way I think about this is..."
      - "Here's the framework..."
    chunk_ids: ["chunk_203", "chunk_204"]

  - nome: "Conviction Mode"
    trigger: "Quando posicao e desafiada ou precisa vender uma ideia"
    tom: "Assertivo, absolutista, linguagem forte"
    duracao: "1-3 minutos"
    sinais:
      - "I can tell you..."
      - "The truth is..."
      - "100 percent..."
    chunk_ids: ["chunk_198", "chunk_212"]

# ═══════════════════════════════════════════════════════════════════════
# PADROES DE COMUNICACAO
# ═══════════════════════════════════════════════════════════════════════

communication_patterns:
  opening_hooks:
    padrao: "Abre com afirmacao forte ou contraintuitiva para capturar atencao"
    exemplos:
      - "The outbound process takes significantly longer than most people expect."
      - "Your job is NOT to make employees happy."
    chunk_ids: ["chunk_198", "AH002_002"]

  story_structure:
    padrao: "Framework-first: apresenta estrutura, depois popula com exemplos e numeros"
    descricao: "Raramente conta historias pessoais longas. Prefere: conceito -> framework -> numero -> implicacao"
    chunk_ids: ["chunk_203", "chunk_204"]

  closing_signatures:
    padrao: "Fecha com implicacao pratica ou call-to-action implicito"
    exemplos:
      - "And that's why I sleep so much better as a business owner."
      - "And this is what PE buyers are looking for."
    chunk_ids: ["chunk_212", "chunk_215"]

  transition_phrases:
    padrao: "Usa transicoes logicas, nao emocionais"
    exemplos:
      - "Now, from there..."
      - "The second piece of this is..."
      - "That being said..."
    chunk_ids: ["chunk_199", "chunk_204"]

# ═══════════════════════════════════════════════════════════════════════
# TRANSFORMACOES DE VOCABULARIO
# ═══════════════════════════════════════════════════════════════════════

vocabulary_transforms:
  - conceito_comum: "opiniao"
    transformacao: "data-driven position"
    chunk_ids: ["chunk_203"]
  - conceito_comum: "problema"
    transformacao: "upstream issue"
    chunk_ids: ["chunk_198"]
  - conceito_comum: "crescimento"
    transformacao: "scaling the machine"
    chunk_ids: ["chunk_212"]
```

---

## SALVAMENTO

Para cada pessoa processada, salvar em:

```
knowledge/external/dna/persons/{slug}/VOICE-DNA.yaml
```

Onde `{slug}` e o slug da pessoa em lowercase-kebab-case (ex: `alex-hormozi`).

**Se o arquivo ja existe:** Mesclar com dados existentes, incrementar versao.
**Se o diretorio da pessoa ja existe:** Salvar nele (ao lado de FILOSOFIAS.yaml etc).
**Se o diretorio nao existe:** Criar o diretorio antes de salvar.

---

## ✓ CHECKPOINT APOS EXECUCAO (OBRIGATORIO)

```
VALIDAR APOS EXECUTAR:

# ESTRUTURA
[ ] CP-POST-MCE3.A: VOICE-DNA.yaml existe em knowledge/external/dna/persons/{slug}/
[ ] CP-POST-MCE3.B: YAML e valido (parseable sem erros)
[ ] CP-POST-MCE3.C: Campo pessoa corresponde ao nome canonico

# TONE PROFILE
[ ] CP-POST-MCE3.D: tone_profile tem as 6 dimensoes (certainty, authority, warmth, directness, teaching_focus, confidence)
[ ] CP-POST-MCE3.E: Cada dimensao tem score (0-10) + justificativa + chunk_ids[]

# SIGNATURE PHRASES
[ ] CP-POST-MCE3.F: signature_phrases tem pelo menos 3 entradas
[ ] CP-POST-MCE3.G: Cada frase tem chunk_ids[] com min 2 elementos e occurrence_count >= 2

# IMMUNE SYSTEM
[ ] CP-POST-MCE3.H: immune_system tem pelo menos 1 trigger-response

# BEHAVIORAL STATES
[ ] CP-POST-MCE3.I: behavioral_states tem entre 3 e 5 estados

# COMMUNICATION PATTERNS
[ ] CP-POST-MCE3.J: communication_patterns tem opening_hooks, story_structure, closing_signatures
[ ] CP-POST-MCE3.K: Cada subcampo tem chunk_ids[]

# RASTREABILIDADE
[ ] CP-POST-MCE3.L: Todos os chunk_ids referenciados existem no CHUNKS-STATE.json
[ ] CP-POST-MCE3.M: Nenhum campo obrigatorio esta vazio

Se CP-POST-MCE3.A falhar: ⛔ EXIT("MCE-3 nao gerou VOICE-DNA.yaml")
Se CP-POST-MCE3.B falhar: ⛔ EXIT("YAML invalido - erro de parsing")
Se CP-POST-MCE3.D falhar: ⛔ EXIT("tone_profile incompleto - faltam dimensoes")
Se CP-POST-MCE3.E falhar: ⚠️ WARN("Dimensoes sem chunk_ids - rastreabilidade limitada")
Se CP-POST-MCE3.F falhar: ⚠️ WARN("Poucas signature_phrases - talvez fonte insuficiente")
Se CP-POST-MCE3.G falhar: ⛔ EXIT("Frases sem recorrencia comprovada (chunk_ids < 2)")
Se CP-POST-MCE3.I falhar: ⚠️ WARN("Menos de 3 behavioral_states - pode ser normal para fontes limitadas")
Se CP-POST-MCE3.J falhar: ⛔ EXIT("communication_patterns incompleto")
Se CP-POST-MCE3.L falhar: ⚠️ WARN("chunk_ids invalidos encontrados")
Se CP-POST-MCE3.M falhar: ⛔ EXIT("Campos obrigatorios vazios no VOICE-DNA.yaml")
```

**BLOQUEANTE:** Nao considerar MCE completo se checkpoints A, B, D, G, J, ou M falharem.

---

## PROXIMA ETAPA

Com VOICE-DNA.yaml gerado, os dados estao prontos para:

1. **Agent Generator** (`agent_generator.py`) -- carrega VOICE-DNA.yaml junto com FILOSOFIAS.yaml,
   HEURISTICAS.yaml etc. para gerar/atualizar SOUL.md do agente.

2. **Dossier Enrichment** -- behavioral_patterns, value_hierarchy, obsessions e paradoxes
   (de MCE-1 e MCE-2 no INSIGHTS-STATE.json) alimentam dossiers de pessoa com novas secoes.

3. **Conclave Sessions** -- agents com VOICE-DNA podem debater com voz AUTENTICA, nao generica.
