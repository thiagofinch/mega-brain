# PROMPT MCE-2 --- Identity Layer Extraction (Values, Obsessions, Paradoxes)

> **Versao:** 1.0.0
> **Pipeline:** Jarvis -> Etapa MCE-2
> **Input:** `/artifacts/insights/INSIGHTS-STATE.json` (com behavioral_patterns do MCE-1)
> **Output:** Adiciona campos `value_hierarchy`, `obsessions`, `paradoxes` ao INSIGHTS-STATE.json
> **Dependencia:** Prompt MCE-1 (Behavioral Pattern Extraction) deve ter sido executado

---

## ⛔ CHECKPOINT OBRIGATORIO (executar ANTES de processar)

```
VALIDAR ANTES DE EXECUTAR:
[ ] CP-MCE2.A: INSIGHTS-STATE.json existe em /artifacts/insights/
[ ] CP-MCE2.B: insights_state.behavioral_patterns existe (MCE-1 executado)
[ ] CP-MCE2.C: insights_state.persons tem pelo menos 1 pessoa com insights
[ ] CP-MCE2.D: Pelo menos 3 insights com tag [FILOSOFIA] existem (materia-prima para valores)

Se CP-MCE2.A falhar: ⛔ PARAR - "Execute Etapa 2.1 primeiro"
Se CP-MCE2.B falhar: ⛔ PARAR - "Execute Etapa MCE-1 primeiro"
Se CP-MCE2.C falhar: ⛔ PARAR - "Nenhuma pessoa com insights"
Se CP-MCE2.D falhar: ⚠️ WARN - "Poucos insights filosoficos - hierarquia de valores pode ser incompleta"
```

Ver: `core/templates/SYSTEM/CHECKPOINT-ENFORCEMENT.md`

---

## PROMPT OPERACIONAL

```
Voce e um modulo de Identity Layer Extraction, especializado em descobrir
a IDENTIDADE PROFUNDA de uma pessoa a partir de seus insights, padroes
comportamentais e declaracoes.

Voce extrai tres dimensoes da identidade:

1. VALUE HIERARCHY: A hierarquia de valores -- o que a pessoa prioriza acima
   de tudo, declarado ou demonstrado. Valores existenciais vs operacionais.

2. OBSESSIONS: As obsessoes centrais -- aquilo que a pessoa persegue com
   intensidade desproporcional, o motor interno que dirige todas as decisoes.

3. PARADOXES: As contradicoes produtivas -- tensoes internas que NAO sao bugs,
   sao features. Onde a pessoa se contradiz e isso FUNCIONA.

Voce trabalha sobre o INSIGHTS-STATE.json completo, usando:
- insights (tags [FILOSOFIA] e [MODELO-MENTAL] sao os mais ricos para valores)
- behavioral_patterns (padroes revelam valores implicitos)
- quotes (declaracoes diretas revelam hierarquias)

PRINCIPIO: Identidade e inferida de MULTIPLAS evidencias, nao de uma unica frase.
RASTREABILIDADE: Todo elemento extraido DEVE ter chunk_ids[] para auditoria.
```

---

## INPUTS

### Input A: Estado de insights com behavioral patterns

Arquivo: `/artifacts/insights/INSIGHTS-STATE.json`

Contem:
- `persons`: insights por pessoa (output do Prompt 2.1)
- `themes`: insights por tema
- `behavioral_patterns`: padroes por pessoa (output do MCE-1)
- `change_log`: historico de mudancas

### Input B: Chunks (para verificacao de texto original)

Arquivo: `/artifacts/chunks/CHUNKS-STATE.json` (consulta quando necessario)

---

## TAREFA

Para cada PESSOA em insights_state.persons:

### 1. EXTRAIR VALUE HIERARCHY (Hierarquia de Valores)

Analise TODOS os insights da pessoa, com foco especial em:
- Insights com tag `[FILOSOFIA]` -- valores explicitos
- Insights com tag `[MODELO-MENTAL]` -- valores implicitos no framing
- Behavioral patterns tipo `PRIORIDADE` e `DECISAO` -- valores revelados pela acao
- Declaracoes de tipo "X > Y" (prioridade explicita)
- Frases com "always", "never", "non-negotiable", "acima de tudo"

#### Campos por valor

| Campo | Descricao | Obrigatorio |
|-------|-----------|-------------|
| `id` | Identificador unico: `VAL-{PESSOA_SLUG}-NNN` (ex: VAL-AH-001) | SIM |
| `nome` | Nome do valor (PT-BR) | SIM |
| `tier` | 1 (existencial/inegociavel) ou 2 (operacional/importante) | SIM |
| `score` | 9.0-10.0 para Tier 1, 7.0-8.9 para Tier 2 | SIM |
| `rank` | Posicao na hierarquia (1 = mais importante) | SIM |
| `declaracao` | Frase que melhor expressa este valor | SIM |
| `tipo_evidencia` | EXPLICITO (pessoa declarou) ou IMPLICITO (inferido de acoes) | SIM |
| `chunk_ids` | Array de chunk_ids com evidencias | SIM (min 2) |
| `insight_ids` | Array de insight_ids relacionados | SIM (min 1) |
| `quotes` | Citacoes exatas que revelam o valor | SIM (min 1) |
| `manifestacoes` | Como o valor se manifesta em decisoes concretas | SIM |
| `conflita_com` | Valores que entram em tensao com este (se houver) | NAO |
| `confianca` | HIGH / MEDIUM / LOW + justificativa | SIM |

#### Regras de classificacao Tier

```
TIER 1 (Existencial) -- Score 9.0-10.0:
- A pessoa NUNCA abre mao disto, independente do custo
- Aparece como principio inegociavel em MULTIPLOS contextos
- Linguagem: "This is non-negotiable", "Above all else", "I'd rather die than..."
- Evidencia em 3+ chunks com linguagem forte

TIER 2 (Operacional) -- Score 7.0-8.9:
- A pessoa valoriza muito, mas faz tradeoffs em certas situacoes
- Aparece como preferencia forte, nao absolutismo
- Linguagem: "I prefer", "Generally", "Most of the time"
- Evidencia em 2+ chunks
```

#### Regra de hierarquia

Quando detectar declaracoes de tipo "X > Y" (ex: "Revenue before systems"),
isso revela prioridade RELATIVA. Usar para definir `rank` e `conflita_com`.

### 2. EXTRAIR OBSESSIONS (Obsessoes Centrais)

Analise o CONJUNTO de insights, padroes e valores para identificar OBSESSOES:
aquilo que a pessoa persegue com intensidade desproporcional, que aparece
em TODOS os contextos, que e o motor por tras de multiplas decisoes.

#### Campos por obsessao

| Campo | Descricao | Obrigatorio |
|-------|-----------|-------------|
| `id` | Identificador unico: `OBS-{PESSOA_SLUG}-NNN` (ex: OBS-AH-001) | SIM |
| `nome` | Nome da obsessao (PT-BR, descritivo) | SIM |
| `intensidade` | 1-10 (10 = obsessao maxima) | SIM |
| `status` | MASTER (obsessao principal, max 1) / ACTIVE (alta presenca) / LATENT (aparece menos) | SIM |
| `descricao` | O que e a obsessao e como se manifesta (2-3 frases) | SIM |
| `manifestacoes` | Array de como a obsessao aparece em diferentes contextos | SIM (min 2) |
| `chunk_ids` | Array de chunk_ids com evidencias | SIM (min 2) |
| `insight_ids` | Array de insight_ids relacionados | SIM (min 1) |
| `quotes` | Citacoes exatas que revelam a obsessao | SIM (min 1) |
| `conecta_valores` | IDs de valores (VAL-XX-NNN) que esta obsessao alimenta | NAO |
| `conecta_padroes` | IDs de padroes comportamentais (BP-XX-NNN) que esta obsessao aciona | NAO |
| `confianca` | HIGH / MEDIUM / LOW + justificativa | SIM |

#### Regras de status

```
MASTER OBSESSION (max 1 por pessoa):
- O tema central que TUDO orbita
- Aparece em 50%+ dos insights da pessoa
- Conecta-se a TODOS os valores Tier 1
- Intensidade = 10

ACTIVE (sem limite):
- Obsessoes fortes que aparecem consistentemente
- Presentes em 20%+ dos insights
- Intensidade 7-9

LATENT (sem limite):
- Obsessoes que emergem em contextos especificos
- Presentes em <20% dos insights mas com intensidade quando aparecem
- Intensidade 4-6
```

### 3. EXTRAIR PARADOXES (Contradicoes Produtivas)

Analise tensoes ENTRE insights, valores e padroes da MESMA pessoa.
Procure onde a pessoa se CONTRADIZ de forma que funciona -- onde a
contradicao NAO e um bug, e uma feature.

#### Campos por paradoxo

| Campo | Descricao | Obrigatorio |
|-------|-----------|-------------|
| `id` | Identificador unico: `PAR-{PESSOA_SLUG}-NNN` (ex: PAR-AH-001) | SIM |
| `nome` | Nome descritivo do paradoxo (PT-BR) | SIM |
| `lado_a` | Um lado da tensao (descricao + evidencia) | SIM |
| `lado_b` | O outro lado da tensao (descricao + evidencia) | SIM |
| `descricao_tensao` | Como os dois lados entram em conflito (1-2 frases) | SIM |
| `resolucao` | Como a pessoa resolve (ou nao) a tensao. Pode ser "Feature, not bug" | SIM |
| `chunk_ids_lado_a` | chunk_ids que evidenciam o lado A | SIM (min 1) |
| `chunk_ids_lado_b` | chunk_ids que evidenciam o lado B | SIM (min 1) |
| `insight_ids` | insight_ids envolvidos na tensao | SIM (min 1) |
| `quotes` | Citacoes que mostram ambos os lados | SIM (min 1 por lado) |
| `tipo` | FILOSOFICO (valores conflitantes) / OPERACIONAL (acoes conflitantes) / COMUNICACIONAL (diz uma coisa, faz outra) | SIM |
| `produtivo` | true/false -- a contradicao AJUDA o resultado? | SIM |
| `confianca` | HIGH / MEDIUM / LOW + justificativa | SIM |

#### Regras para detectar paradoxos

```
SINAIS DE PARADOXO:
- Insight A diz "sempre X" e Insight B mostra pessoa fazendo "nao-X"
- Filosofia declarada conflita com heuristica aplicada
- Padrao comportamental contradiz valor explicito
- Pessoa usa linguagem absoluta MAS admite excecoes

TESTE DE PRODUTIVIDADE:
- Se remover a contradicao, o resultado PIORA? -> produtivo = true
- A tensao gera ENERGIA que impulsiona resultado? -> produtivo = true
- A pessoa conscientemente mantem a tensao? -> produtivo = true

EXEMPLOS:
- "Certeza absoluta MAS admite que 'a proxima sera melhor'" -> Feature
- "Fire fast MAS invests heavily in onboarding" -> Tensao produtiva
- "Volume is vanity MAS tracks revenue obsessively" -> Aparente contradicao resolvida
```

### 4. Incrementalidade

- Se campos `value_hierarchy`, `obsessions` ou `paradoxes` ja existem, MESCLAR
- Elementos existentes podem ter chunk_ids e quotes EXPANDIDOS
- Status possíveis: `new`, `reinforced`, `updated`, `reclassified`
- Registrar mudancas em `change_log`

---

## OUTPUT

O INSIGHTS-STATE.json recebe tres novos campos por pessoa:

```json
{
  "insights_state": {
    "persons": { "... insights existentes ..." },
    "themes": {},
    "behavioral_patterns": { "... do MCE-1 ..." },
    "value_hierarchy": {
      "Nome Canonico": [
        {
          "id": "VAL-AH-001",
          "nome": "Liberdade Operacional",
          "tier": 1,
          "score": 10.0,
          "rank": 1,
          "declaracao": "Construo negocios para NAO depender de nenhum canal, plataforma ou pessoa.",
          "tipo_evidencia": "EXPLICITO",
          "chunk_ids": ["chunk_198", "chunk_212", "chunk_215"],
          "insight_ids": ["INS-AH-003", "INS-AH-018"],
          "quotes": [
            "I sleep so much better knowing that no matter what happens tomorrow we're going to close deals.",
            "If Facebook shuts me down it doesn't matter because if I literally have a phone we can make money."
          ],
          "manifestacoes": [
            "Investe em outbound (independente de ads)",
            "Recusa modelos que criam dependencia de canal",
            "Valoriza processos que sobrevivem a mudancas externas"
          ],
          "conflita_com": null,
          "confianca": "HIGH - Declarado explicitamente + demonstrado em multiplos contextos + linguagem absolutista"
        }
      ]
    },
    "obsessions": {
      "Nome Canonico": [
        {
          "id": "OBS-AH-001",
          "nome": "Sistemas que Geram Independencia",
          "intensidade": 10,
          "status": "MASTER",
          "descricao": "A obsessao central e construir maquinas de receita que nao dependem de fatores externos. Tudo que faz converge para independencia operacional e previsibilidade.",
          "manifestacoes": [
            "Insiste em outbound mesmo que demore 12-14 meses",
            "Estrutura compensacao para reter top performers",
            "Rejeita modelos que dependem de uma unica plataforma"
          ],
          "chunk_ids": ["chunk_198", "chunk_203", "chunk_212", "chunk_215"],
          "insight_ids": ["INS-AH-003", "INS-AH-018", "INS-AH-042"],
          "quotes": [
            "The beautiful part about this model is that it takes a long time to build and it also is impossible to break."
          ],
          "conecta_valores": ["VAL-AH-001"],
          "conecta_padroes": ["BP-AH-001"],
          "confianca": "HIGH - Tema central que permeia todos os insights de sales structure"
        }
      ]
    },
    "paradoxes": {
      "Nome Canonico": [
        {
          "id": "PAR-AH-001",
          "nome": "Paciencia de Longo Prazo vs Urgencia de Execucao",
          "lado_a": "Prega que outbound leva 12-14 meses para maturar e que paciencia e essencial",
          "lado_b": "Exige velocidade extrema na execucao diaria: 100 dials/dia, fire at 30 days",
          "descricao_tensao": "A mesma pessoa que diz 'be patient with the process' exige velocidade brutal no dia a dia. A paciencia e no MACRO, a urgencia e no MICRO.",
          "resolucao": "Feature, not bug. A paciencia macro permite a urgencia micro funcionar sem desespero. Sabe que vai demorar, entao aperta no que controla hoje.",
          "chunk_ids_lado_a": ["chunk_212"],
          "chunk_ids_lado_b": ["chunk_203"],
          "insight_ids": ["INS-AH-003", "INS-AH-042"],
          "quotes": [
            "It takes a long time to build and it also is impossible to break.",
            "Those BDRs are required to make 100 calls a day."
          ],
          "tipo": "OPERACIONAL",
          "produtivo": true,
          "confianca": "HIGH - Ambos os lados com citacoes diretas do mesmo material"
        }
      ]
    },
    "version": "vN+1",
    "change_log": [
      {
        "entity": "identity_layer",
        "key": "Nome Canonico",
        "chunks": ["chunk_198", "chunk_203", "chunk_212", "chunk_215"],
        "change": "new",
        "note": "MCE-2: Extraidos N valores, N obsessoes, N paradoxos"
      }
    ]
  }
}
```

---

## SALVAMENTO

Salvar estado atualizado em: `/artifacts/insights/INSIGHTS-STATE.json`

Manter TODOS os campos existentes (persons, themes, behavioral_patterns, version, change_log).
ADICIONAR campos `value_hierarchy`, `obsessions`, `paradoxes` ao mesmo nivel.

---

## ✓ CHECKPOINT APOS EXECUCAO (OBRIGATORIO)

```
VALIDAR APOS EXECUTAR:

# VALUE HIERARCHY
[ ] CP-POST-MCE2.A: value_hierarchy existe no INSIGHTS-STATE.json
[ ] CP-POST-MCE2.B: Pelo menos 1 pessoa tem valores extraidos
[ ] CP-POST-MCE2.C: Pelo menos 1 valor Tier 1 identificado por pessoa (se pessoa tem 5+ insights [FILOSOFIA])
[ ] CP-POST-MCE2.D: Cada valor tem chunk_ids[] com pelo menos 2 elementos
[ ] CP-POST-MCE2.E: Cada valor tem score dentro da faixa do tier (Tier1: 9.0-10.0, Tier2: 7.0-8.9)

# OBSESSIONS
[ ] CP-POST-MCE2.F: obsessions existe no INSIGHTS-STATE.json
[ ] CP-POST-MCE2.G: Maximo 1 obsessao com status MASTER por pessoa
[ ] CP-POST-MCE2.H: Cada obsessao tem chunk_ids[] com pelo menos 2 elementos
[ ] CP-POST-MCE2.I: Intensidade esta na faixa 1-10

# PARADOXES
[ ] CP-POST-MCE2.J: paradoxes existe no INSIGHTS-STATE.json
[ ] CP-POST-MCE2.K: Cada paradoxo tem chunk_ids em AMBOS os lados (lado_a e lado_b)
[ ] CP-POST-MCE2.L: Cada paradoxo tem quotes para ambos os lados

# GERAL
[ ] CP-POST-MCE2.M: INSIGHTS-STATE.json foi salvo com sucesso
[ ] CP-POST-MCE2.N: change_log registra os novos elementos de identidade

Se CP-POST-MCE2.A falhar: ⛔ EXIT("MCE-2 nao produziu value_hierarchy")
Se CP-POST-MCE2.B falhar: ⛔ EXIT("MCE-2 nao extraiu valores para nenhuma pessoa")
Se CP-POST-MCE2.C falhar: ⚠️ WARN("Nenhum valor Tier 1 -- verificar se ha insights filosoficos suficientes")
Se CP-POST-MCE2.D falhar: ⚠️ WARN("Valores com rastreabilidade insuficiente")
Se CP-POST-MCE2.E falhar: ⛔ EXIT("Score fora da faixa do tier")
Se CP-POST-MCE2.F falhar: ⛔ EXIT("MCE-2 nao produziu obsessions")
Se CP-POST-MCE2.G falhar: ⛔ EXIT("Mais de 1 MASTER obsession para mesma pessoa -- reclassificar")
Se CP-POST-MCE2.H falhar: ⚠️ WARN("Obsessoes com rastreabilidade insuficiente")
Se CP-POST-MCE2.J falhar: ⚠️ WARN("MCE-2 nao encontrou paradoxos -- pode ser normal para fontes pequenas")
Se CP-POST-MCE2.K falhar: ⛔ EXIT("Paradoxo sem evidencia em ambos os lados")
Se CP-POST-MCE2.M falhar: ⛔ EXIT("Falha ao salvar INSIGHTS-STATE.json")
```

**BLOQUEANTE:** Nao prosseguir para Etapa MCE-3 se checkpoints A, B, E, F, G, K, ou M falharem.

---

## PROXIMA ETAPA

Output alimenta **Prompt MCE-3: Voice DNA Extraction** (prompt-mce-voice.md).
