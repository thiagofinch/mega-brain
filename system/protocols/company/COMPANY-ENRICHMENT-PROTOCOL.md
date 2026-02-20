# ORG-LIVE ENRICHMENT PROTOCOL

> **Versao:** 2.1.0 | **Criado:** 2025-12-20 | **Atualizado:** 2025-12-23
> **Pipeline:** Jarvis → Phase 8.1.6 (apos Role-Tracking)
> **Ecossistema:** [SUA EMPRESA]
> **Dependencia:** ORG-PROTOCOL.md
> **Navegação:** 5 NÍVEIS (DOSSIER → NARRATIVE → INSIGHT → CANONICAL → CHUNK)

---

## PROPOSITO

Alimentar automaticamente os ROLEs e MEMORYs do ecossistema [SUA EMPRESA] com conhecimento de TRES fontes sincronizadas:
1. **Agentes IA** (AGENT-*-MEMORY.md) - Conhecimento processado
2. **Pipeline Jarvis** (knowledge/) - Fontes brutas mais ricas
3. **Cargos Relacionados** (MEMORY-*.md) - Dependencias organizacionais

Mantendo rastreabilidade total e sincronizacao 100% com a estrutura de agentes (C-LEVEL, SALES).

---

## POSICAO NO PIPELINE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE JARVIS v2.1                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 7: AGENT ENRICHMENT                                                  │
│  └─ Atualiza AGENTES IA (AGENT-*.md, MEMORY-*.md)                          │
│                                                                             │
│  PHASE 8: FINALIZATION                                                      │
│  ├─ 8.1.1-8.1.5: RAG, Registry, Session, Evolution, Role-Tracking          │
│  │                                                                          │
│  └─ 8.1.6: ★ ORG-LIVE ENRICHMENT ★ ←── ESTE PROTOCOLO                      │
│            │                                                                │
│            ├── Input: INSIGHTS_STATE.json + NARRATIVES_STATE.json          │
│            ├── Mapeamento: THEME_TO_ROLES                                   │
│            ├── Output: ROLE-*.md + MEMORY-*.md ([SUA EMPRESA])                   │
│            └── Regra: Citacao [FONTE] obrigatoria                          │
│                                                                             │
│  PHASE 8.2: CHECKPOINT FINAL                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## DIFERENCA: ROLE-TRACKING vs ORG-LIVE

| Aspecto | Role-Tracking | ORG-LIVE Enrichment |
|---------|---------------|---------------------|
| **Proposito** | Criar AGENTES IA | Documentar CARGOS humanos |
| **Threshold** | 10+ mencoes | Sempre (sem threshold) |
| **Scope** | Sistema Mega Brain | Ecossistema [SUA EMPRESA] |
| **Output** | `/agents/SALES/AGENT-*.md` | `/agents/ORG-LIVE/ROLES/ROLE-*.md` |
| **Trigger** | Mencao atinge threshold | Insight relevante para cargo |

---

## ARQUITETURA DE SINCRONIZACAO (3 NIVEIS)

> **REGRA FUNDAMENTAL:** As MEMORYs de cargos (ORG-LIVE) devem estar 100% sincronizadas com a estrutura de conhecimento do sistema.

### Visao Geral

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA DE SINCRONIZACAO v2.0                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   NIVEL 1: AGENTES IA (conhecimento processado)                            │
│   ├── /agents/SALES/                                                     │
│   │   ├── AGENT-CLOSER-MEMORY.md                                           │
│   │   ├── AGENT-SALES-MANAGER-MEMORY.md                                    │
│   │   ├── AGENT-SDS-MEMORY.md                                              │
│   │   ├── AGENT-LNS-MEMORY.md                                              │
│   │   └── AGENT-BDR-MEMORY.md                                              │
│   │                                                                         │
│   └── /agents/C-LEVEL/                                                   │
│       ├── AGENT-CMO-MEMORY.md                                              │
│       ├── AGENT-CRO-MEMORY.md                                              │
│       ├── AGENT-CFO-MEMORY.md                                              │
│       └── AGENT-COO-MEMORY.md                                              │
│                                                                             │
│   NIVEL 2: PIPELINE JARVIS (fontes brutas - MAIS RICAS)                    │
│   ├── /knowledge/dossiers/persons/                                       │
│   │   └── DOSSIER-{PESSOA}.md  → Tudo que 1 pessoa disse                   │
│   │                                                                         │
│   ├── /knowledge/dossiers/THEMES/                                        │
│   │   └── DOSSIER-{TEMA}.md    → 1 tema, multiplas pessoas                 │
│   │                                                                         │
│   ├── /knowledge/SOURCES/{PESSOA}/                                       │
│   │   └── {TEMA}.md            → 1 pessoa × 1 tema                         │
│   │                                                                         │
│   └── /inbox/               → Material bruto original                   │
│                                                                             │
│   NIVEL 3: CARGOS RELACIONADOS (dependencias organizacionais)              │
│   └── /agents/ORG-LIVE/MEMORY/                                           │
│       ├── MEMORY-SDR.md        ← → MEMORY-CLOSER.md                        │
│       ├── MEMORY-CLOSER.md     ← → MEMORY-CLOSER-CHEFE.md                  │
│       ├── MEMORY-CLOSER-CHEFE.md ← → MEMORY-SALES-MANAGER.md               │
│       ├── MEMORY-SALES-MANAGER.md ← → MEMORY-CMO.md                        │
│       └── MEMORY-CMO.md                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**O que isso significa na pratica:**
Quando voce consulta uma MEMORY de cargo (exemplo: MEMORY-SDR.md), voce NAO esta limitado ao que esta escrito ali. Voce tem links diretos para:
1. As MEMORYs dos agentes IA (AGENT-SDS-MEMORY, AGENT-LNS-MEMORY) - conhecimento ja processado
2. Os DOSSIERs no Pipeline - fontes brutas com mais detalhes e contexto
3. As MEMORYs de cargos relacionados - para entender dependencias (quem envia leads, quem supervisiona)

---

### Mapeamento ROLE → AGENT(s)

| Cargo (ROLE) | Agente(s) Fonte | Localizacao |
|--------------|-----------------|-------------|
| ROLE-SDR | AGENT-SDS, AGENT-LNS, AGENT-BDR | `/agents/SALES/` |
| ROLE-CLOSER | AGENT-CLOSER | `/agents/SALES/` |
| ROLE-CLOSER-CHEFE | AGENT-CLOSER, AGENT-SALES-MANAGER | `/agents/SALES/` |
| ROLE-SALES-MANAGER | AGENT-SALES-MANAGER | `/agents/SALES/` |
| ROLE-CMO | AGENT-CMO | `/agents/C-LEVEL/` |

---

### Mapeamento ROLE → Cargos Relacionados

| Cargo | Envia Para | Recebe De | Supervisiona | Supervisionado Por |
|-------|------------|-----------|--------------|-------------------|
| SDR | CLOSER | Marketing/Leads | - | CLOSER-CHEFE ou SM |
| CLOSER | - | SDR | - | CLOSER-CHEFE ou SM |
| CLOSER-CHEFE | - | SDR | CLOSERs | FOUNDER ou CRO |
| SALES-MANAGER | - | - | SDRs, CLOSERs | CRO |
| CMO | SDR (leads) | - | Marketing Team | CEO |

---

### Regra de Sincronizacao Automatica

```
QUANDO Pipeline Jarvis processa novo material:

1. FASE 7 (Agent Enrichment):
   → Atualiza AGENT-*-MEMORY.md em /agents/SALES/ e /C-LEVEL/

2. FASE 8.1.6 (ORG-LIVE Enrichment):
   → Propaga para ROLE-*.md com citacao [VIA: AGENT-X → Fonte]
   → Atualiza MEMORY-*.md com:
      a) Registro da fonte processada
      b) Link para AGENT-*-MEMORY.md correspondente
      c) Link para DOSSIERs relevantes
      d) Links para cargos relacionados afetados

3. VALIDACAO:
   → Verificar se links estao funcionando
   → Verificar se citacao [VIA] esta presente
   → Verificar se cargos relacionados foram notificados
```

---

### Estrutura Padrao de MEMORY-*.md (v4.0)

```markdown
# MEMORY-{CARGO}

> **Cargo:** {NOME COMPLETO}
> **Ecossistema:** [SUA EMPRESA]
> **Versao:** X.X.X
> **Protocolo:** ORG-LIVE-DOCUMENT-PROTOCOL v1.0

---

## RESUMO DO CARGO
[Explicacao em portugues claro do que o cargo faz]

---

## SINCRONIZACAO DE CONHECIMENTO

### Fontes de Alimentacao (3 Niveis)
[Diagrama ASCII mostrando os 3 niveis]

### Links Diretos para Agentes IA
[Tabela com links para AGENT-*-MEMORY.md]

### Links Diretos para Pipeline (Fontes Brutas)
[Tabela com links para DOSSIERs]

---

## FONTES QUE ALIMENTAM ESTE CARGO
[Tabela de fontes com data, codigo, secao, insight]

---

## DECISOES E PRECEDENTES
[Registro de decisoes tomadas]

---

## TENSOES DOCUMENTADAS
[Conflitos entre fontes, com decisao [SUA EMPRESA]]

---

## APRENDIZADOS ACUMULADOS
[Frameworks e insights por fonte]

---

## METRICAS MONITORADAS
[Tabela com benchmarks]

---

## FERRAMENTAS E RECURSOS
[Links para documentos relacionados]

---

## HISTORICO DE ATUALIZACOES
[Log de mudancas]
```

---

## MAPEAMENTO: THEME_TO_ROLES

```
THEME_TO_ROLES_[SUA EMPRESA] = {
  "01-ESTRUTURA-TIME": ["CLOSER-CHEFE", "SALES-MANAGER"],
  "02-PROCESSO-VENDAS": ["closer", "CLOSER-CHEFE", "SDR"],
  "03-CONTRATACAO": ["CLOSER-CHEFE", "SALES-MANAGER", "CMO"],
  "04-COMISSIONAMENTO": ["closer", "CLOSER-CHEFE", "SALES-MANAGER"],
  "05-METRICAS": ["CLOSER-CHEFE", "SALES-MANAGER", "CMO"],
  "06-FUNIL-APLICACAO": ["SDR", "CMO"],
  "07-PRICING": ["CMO"],
  "08-FERRAMENTAS": ["CLOSER-CHEFE", "SALES-MANAGER"],
  "09-GESTAO": ["CLOSER-CHEFE", "SALES-MANAGER"],
  "10-CULTURA-GAMIFICACAO": ["CLOSER-CHEFE", "SALES-MANAGER"]
}
```

---

## EXECUCAO: Step 8.1.6

```
LOG: "Executando ORG-LIVE Enrichment para ecossistema [SUA EMPRESA]..."

═══════════════════════════════════════════════════════════════════════════
STEP 8.1.6.0 - CARREGAR TODOS OS 5 NÍVEIS PARA EXTRAÇÃO RICA
═══════════════════════════════════════════════════════════════════════════
# PRINCÍPIO: EXTRAÇÃO RICA > ECONOMIA DE TOKENS
# Cargos [SUA EMPRESA] devem ser alimentados com a MÁXIMA profundidade disponível
# MESMO PADRÃO usado em Role Discovery (8.1.7) e Agent Enrichment (7.4)
#
# ARQUITETURA DE NAVEGAÇÃO COMPLETA (5 NÍVEIS):
# ┌─────────────────────────────────────────────────────────────────────┐
# │  NÍVEL 5: DOSSIERS/*.md         ← Mais consolidado (markdown)       │
# │  NÍVEL 4: NARRATIVES-STATE.json ← Síntese por pessoa/tema          │
# │  NÍVEL 3: INSIGHTS-STATE.json   ← Insights com confiança/prioridade │
# │  NÍVEL 2: CANONICAL-MAP.json    ← Resolução de entidades           │
# │  NÍVEL 1: CHUNKS-STATE.json     ← Texto bruto original              │
# └─────────────────────────────────────────────────────────────────────┘

# NÍVEL 5 - DOSSIERS (mais consolidado)
DOSSIERS_PERSONS = LIST /knowledge/dossiers/persons/DOSSIER-*.md
DOSSIERS_THEMES = LIST /knowledge/dossiers/THEMES/DOSSIER-*.md

# NÍVEL 4 - NARRATIVES
READ /processing/narratives/NARRATIVES-STATE.json as NARRATIVES_DATA

# NÍVEL 3 - INSIGHTS
READ /processing/insights/INSIGHTS-STATE.json as INSIGHTS_DATA

# NÍVEL 2 - CANONICAL (entidades)
READ /processing/canonical/CANONICAL-MAP.json as CANONICAL_DATA

# NÍVEL 1 - CHUNKS (texto bruto)
READ /processing/chunks/CHUNKS-STATE.json as CHUNKS_DATA

═══════════════════════════════════════════════════════════════════════════
STEP 8.1.6.1 - IDENTIFICAR INSIGHTS RELEVANTES (NAVEGAÇÃO RICA)
═══════════════════════════════════════════════════════════════════════════

FOR each INSIGHT in INSIGHTS_DATA where priority == "HIGH":

  THEME = INSIGHT.theme
  ROLES_IMPACTED = THEME_TO_ROLES_[SUA EMPRESA][THEME]

  IF ROLES_IMPACTED is not empty:

    # NAVEGAÇÃO RICA: Descer para níveis mais profundos
    # ─────────────────────────────────────────────────────────────────────
    # NÍVEL 2 - Buscar entidade canônica
    CANONICAL_ENTITY = CANONICAL_DATA.entities.find(THEME)
    ENTITY_VARIATIONS = CANONICAL_ENTITY.aliases if exists else []

    # NÍVEL 1 - Buscar citações exatas nos chunks
    CHUNK = CHUNKS_DATA.find(INSIGHT.chunk_id)
    EXACT_QUOTE = CHUNK.conteudo if CHUNK exists else null
    TIMESTAMP = CHUNK.timestamp if CHUNK exists else null
    SPEAKER = CHUNK.speaker if CHUNK exists else null

    # NÍVEL 4 - Buscar contexto narrativo
    PERSON_NARRATIVE = NARRATIVES_DATA.persons[INSIGHT.source_person]
    NARRATIVE_CONTEXT = extract_excerpt(PERSON_NARRATIVE.narrative, THEME) if exists else null

    # NÍVEL 5 - Buscar referências do dossiê
    DOSSIER_PATH = find_dossier(INSIGHT.source_person, DOSSIERS_PERSONS)
    DOSSIER_CONTEXT = extract_relevant_section(DOSSIER_PATH, THEME) if exists else null

    ADD to ORG_LIVE_QUEUE:
      {
        "insight_id": INSIGHT.id,
        "theme": THEME,
        "content": INSIGHT.content,
        "source_id": INSIGHT.source_id,
        "source_person": INSIGHT.source_person,
        "chunk_ref": INSIGHT.chunk_id,
        "roles": ROLES_IMPACTED,

        # DADOS RICOS (5 NÍVEIS)
        "exact_quote": EXACT_QUOTE,
        "timestamp": TIMESTAMP,
        "speaker": SPEAKER,
        "narrative_context": NARRATIVE_CONTEXT,
        "dossier_path": DOSSIER_PATH,
        "dossier_context": DOSSIER_CONTEXT,
        "entity_variations": ENTITY_VARIATIONS,
        "extraction_levels": ["DOSSIER", "NARRATIVE", "INSIGHT", "CANONICAL", "CHUNK"]
      }

LOG: "{count} insights HIGH identificados para ORG-LIVE"

═══════════════════════════════════════════════════════════════════════════
STEP 8.1.6.2 - ATUALIZAR ROLEs
═══════════════════════════════════════════════════════════════════════════

FOR each ROLE in unique(ORG_LIVE_QUEUE.roles):

  ROLE_PATH = /agents/ORG-LIVE/ROLES/ROLE-{ROLE}.md
  MEMORY_PATH = /agents/ORG-LIVE/MEMORY-{ROLE}.md

  IF ROLE_PATH exists:
    READ existing_role

    # Identificar secoes a atualizar
    INSIGHTS_FOR_ROLE = filter(ORG_LIVE_QUEUE, role == ROLE)

    FOR each INSIGHT in INSIGHTS_FOR_ROLE:

      # Determinar onde inserir baseado no tipo de insight
      SECTION = determine_section(INSIGHT.theme):
        - 02-PROCESSO-VENDAS → "## 2. RESPONSABILIDADES" ou "## 6. FRAMEWORKS"
        - 05-METRICAS → "## 5. METRICAS DE SUCESSO"
        - 09-GESTAO → "## 3. LINHAS DE COMUNICACAO"
        - DEFAULT → "## X. FONTES UTILIZADAS"

      # Formatar com [FONTE] obrigatória + DADOS RICOS de todos os níveis
      NEW_CONTENT = format_with_rich_source(INSIGHT):

        > **[FONTE: {SOURCE_PERSON} - {SOURCE_ID}]** | [chunk_{chunk_ref}]
        > "{EXACT_QUOTE}" — {SPEAKER}, {TIMESTAMP}

        **Contexto narrativo:** {NARRATIVE_CONTEXT}

        **Aplicação prática:**
        {conteudo estruturado derivado do insight}

        **Para aprofundamento:**
        - Dossiê: {DOSSIER_PATH}
        - Chunk original: chunk_{chunk_ref}
        - Variações de entidade: {ENTITY_VARIATIONS}

      # Verificar se ja existe (evitar duplicatas)
      IF NOT already_exists(existing_role, INSIGHT.chunk_ref):
        APPEND NEW_CONTENT to SECTION
        LOG: "ROLE-{ROLE}: Adicionado insight de {SOURCE_PERSON}"

    WRITE updated_role to ROLE_PATH

  ELSE:
    LOG WARNING: "ROLE-{ROLE}.md nao existe - criar manualmente primeiro"

═══════════════════════════════════════════════════════════════════════════
STEP 8.1.6.3 - ATUALIZAR MEMORYs DOS CARGOS
═══════════════════════════════════════════════════════════════════════════

FOR each ROLE updated:

  MEMORY_PATH = /agents/ORG-LIVE/MEMORY-{ROLE}.md

  IF MEMORY_PATH exists:
    READ existing_memory

    LOCATE or CREATE section "## FONTES PROCESSADAS"
    APPEND row to table:
      | {TODAY} | {SOURCE_PERSON} ({SOURCE_ID}) | {summary_of_insights} |

    WRITE updated_memory to MEMORY_PATH
    LOG: "MEMORY-{ROLE}: Fonte registrada"

  ELSE:
    # Criar MEMORY se nao existe
    CREATE MEMORY_PATH with template:
      # MEMORY-{ROLE}

      > **Cargo:** {ROLE}
      > **Ecossistema:** [SUA EMPRESA] (ISOLATED)
      > **Criado:** {TODAY}

      ---

      ## FONTES PROCESSADAS

      | Data | Fonte | Insights Principais |
      |------|-------|---------------------|
      | {TODAY} | {SOURCE_PERSON} ({SOURCE_ID}) | {summary} |

      ---

      ## DECISOES E PRECEDENTES

      *Nenhuma decisao registrada ainda*

      ---

      *MEMORY-{ROLE} v1.0.0*
      *Ecossistema [SUA EMPRESA] - ISOLATED*

    LOG: "MEMORY-{ROLE} criado"

═══════════════════════════════════════════════════════════════════════════
STEP 8.1.6.4 - LOG FINAL ORG-LIVE
═══════════════════════════════════════════════════════════════════════════

LOG:
  ===============================================================================
  ORG-LIVE ENRICHMENT COMPLETE
  ===============================================================================

  Ecossistema: [SUA EMPRESA]
  Fonte: {SOURCE_PERSON} ({SOURCE_ID})

  ROLEs atualizados:
  {list of ROLE-*.md files updated}

  MEMORYs atualizados:
  {list of MEMORY-*.md files updated}

  Insights HIGH aplicados: {count}

  ===============================================================================
```

---

## REGRAS DE ESCRITA E CLAREZA

> **OBRIGATORIO: Todo conteudo deve ser escrito de forma clara, detalhada e acessivel.**

### Principio Central

Os documentos do ORG-LIVE sao lidos por humanos que precisam entender EXATAMENTE o que fazer. Nao sao documentos tecnicos para desenvolvedores. Sao guias praticos para gestores e profissionais de vendas.

### Regras de Linguagem

| Regra | Errado | Correto |
|-------|--------|---------|
| Traduzir termos comuns | "morning meetings" | "reunioes pela manha" |
| Traduzir termos comuns | "daily standup" | "reuniao diaria rapida" |
| Traduzir termos comuns | "one-on-ones" | "reunioes individuais" |
| Manter termos tecnicos | - | "pipeline" (sem traducao facil) |
| Manter termos tecnicos | - | "CRM" (sigla universal) |
| Manter termos tecnicos | - | "closer" (cargo especifico) |

**Criterio:** Manter em ingles APENAS termos que nao tem traducao facil ou que sao universalmente usados no mercado de vendas B2B.

### Regra do Paragrafo Completo

**TODA secao deve terminar com uma explicacao verbal clara.**

Isso significa que, apos apresentar um framework, metrica ou conceito, voce deve adicionar um paragrafo final explicando em linguagem simples o que aquilo significa na pratica do dia a dia.

**Exemplo ERRADO:**

```markdown
## Metricas de Sucesso

- Show rate: 80%+
- Close rate: 25-35%
- CCR < 30%
```

**Exemplo CORRETO:**

```markdown
## Metricas de Sucesso

- Taxa de comparecimento nas reunioes: 80% ou mais
- Taxa de fechamento: entre 25% e 35%
- Cancelamento de clientes: menos de 30% ao ano

**O que isso significa na pratica:** Se voce agenda 10 reunioes, pelo menos 8 pessoas devem comparecer. Dessas 8, voce deve fechar entre 2 e 3 vendas. E dos clientes que voce fecha, menos de 1 em cada 3 deve cancelar no primeiro ano. Esses numeros mostram uma operacao saudavel. Se a taxa de comparecimento esta abaixo de 80%, o problema esta na qualificacao ou no tempo entre agendamento e reuniao. Se o fechamento esta abaixo de 25%, o closer precisa de treinamento ou os leads nao estao qualificados. Se o cancelamento esta acima de 30%, o produto ou a entrega tem problemas.
```

### Regra de Nao Abreviar

| Proibido | Usar |
|----------|------|
| SM | Sales Manager (ou Gerente de Vendas) |
| BDR | Business Development Representative (ou Prospector) |
| SDR | Sales Development Representative (ou Qualificador) |
| BC | Business Closer (ou Closer de Negocios) |
| MRR | Receita Recorrente Mensal |
| LTV | Valor do Tempo de Vida do Cliente |
| CAC | Custo de Aquisicao de Cliente |

**Excecao:** Apos a primeira mencao com o termo completo, pode-se usar a sigla entre parenteses. Exemplo: "O Gerente de Vendas (Sales Manager) deve..."

### Regra de Explicacao Contextual

Cada conceito novo deve vir acompanhado de:

1. **Definicao clara** - O que e isso?
2. **Por que importa** - Por que o cargo precisa saber disso?
3. **Como aplicar** - O que fazer com essa informacao?
4. **Exemplo pratico** - Como isso se parece no dia a dia?

---

## REGRAS DE ESCALABILIDADE

> **Os documentos sao FLEXIVEIS e crescem conforme a operacao cresce.**

### Principio de Crescimento

Os ROLEs em ORG-LIVE refletem os AGENTS em `/agents/C-LEVEL/` e `/agents/SALES/`. Conforme mais conteudo e processado, mais detalhes sao adicionados a cada cargo.

### Tamanho de Equipe vs Funcoes

O sistema deve ser capaz de responder: "Com X pessoas, o que consigo fazer?"

```
EQUIPE DE 1 PESSOA (Fundador/Closer):
├── Fecha todas as vendas
├── Faz propria qualificacao
├── Define precos
└── Limitacao: Nao escala, gargalo total

EQUIPE DE 2 PESSOAS (Fundador + Closer):
├── Fundador: Estrategia, pricing, ofertas
├── Closer: Todas as vendas
└── Limitacao: Closer sobrecarregado, sem qualificacao dedicada

EQUIPE DE 3 PESSOAS (Fundador + Closer + SDR):
├── Fundador: Estrategia, pricing, ofertas
├── SDR: Qualificacao de leads
├── Closer: Apenas fechamento
└── Limitacao: Fundador ainda no operacional

EQUIPE DE 5+ PESSOAS:
├── Sales Manager: Gestao do time
├── SDR(s): Qualificacao
├── Closer(s): Fechamento
├── Fundador: Estrategia apenas
└── Limitacao: Depende de volume de leads
```

### Regra de Nao Misturar Funcoes

**CRITICO:** O sistema deve deixar claro que certas funcoes NAO podem ser misturadas.

| Funcao A | Funcao B | Pode Misturar? | Por que? |
|----------|----------|----------------|----------|
| Closer | SDR | ❌ NAO | Closer que qualifica perde tempo de fechamento |
| Sales Manager | Closer | ⚠️ TEMPORARIO | SM no calendario vira gargalo rapidamente |
| SDR | Marketing | ❌ NAO | Mentalidades diferentes, metricas conflitantes |
| Closer | CS | ❌ NAO | Pos-venda exige mindset diferente |

**Explicacao:** Quando alguem tenta fazer duas funcoes ao mesmo tempo, nenhuma e feita bem. O closer que tambem qualifica passa 50% do tempo em atividades de baixo valor (qualificacao) ao inves de fazer o que gera mais receita (fechamento). O Sales Manager que ainda fecha vendas regularmente nao consegue treinar, fazer quality control, ou otimizar o processo - e o time para de crescer.

### Como Crescer o Time de Forma Eficaz

O sistema deve orientar:

1. **Primeiro gargalo a resolver:** Qualificacao (contratar SDR antes de segundo closer)
2. **Segundo gargalo:** Gestao (promover ou contratar Sales Manager quando tiver 3+ closers)
3. **Terceiro gargalo:** Especializacao (separar closers por ticket/produto)

**Regra de ouro:** Nunca contratar funcao seniores antes de ter as funcoes juniores preenchidas. Exemplo: Nao contratar CMO antes de ter SDRs funcionando.

---

## REGRAS DE FORMATACAO

### Citacao de Fonte (OBRIGATORIA)

```markdown
> **[FONTE: Cole Gordon - CG003]**
> "Sales Manager nao deve estar no calendario regular de vendas. Vender e um poco sem fundo de atividade que consome todo o tempo disponivel."

**O que isso significa:** O Gerente de Vendas (Sales Manager) nao pode ter reunioes de vendas agendadas regularmente no calendario dele. Se ele entrar no calendario como closer, vai passar o dia todo fechando vendas e nao vai sobrar tempo para treinar o time, revisar ligacoes, ou melhorar processos. Vender sempre parece mais urgente do que gerenciar, entao o gerente que vende acaba virando um closer caro que nao gerencia ninguem.
```

### Adicionar a Secao Correta

| Tipo de Insight | Secao no ROLE |
|-----------------|---------------|
| Framework/Metodologia | ## 6. FRAMEWORKS OPERACIONAIS |
| Metrica/Benchmark | ## 5. METRICAS DE SUCESSO |
| Responsabilidade | ## 2. RESPONSABILIDADES |
| Comunicacao/Report | ## 3. LINHAS DE COMUNICACAO |
| Armadilha/Anti-pattern | ## 8. ARMADILHAS |
| Trust Trait | ## 7. TRUST TRAITS CRITICOS |

### Evitar Duplicatas

```
BEFORE adding insight:
  SEARCH existing_role for INSIGHT.chunk_ref
  IF found:
    SKIP (ja existe)
  ELSE:
    ADD insight
```

---

## CHECKPOINT ORG-LIVE

```
APOS EXECUCAO, VALIDAR:

[ ] CP-ORG-1: Pelo menos 1 ROLE atualizado (se houve insights relevantes)
[ ] CP-ORG-2: Todas citacoes tem [FONTE: PESSOA - ID]
[ ] CP-ORG-3: MEMORYs correspondentes atualizados
[ ] CP-ORG-4: Nenhuma duplicata adicionada

Se CP-ORG-1 falhar e havia insights HIGH: ⚠️ WARN
Se CP-ORG-2 falhar: ⛔ BLOQUEANTE - citacao obrigatoria
Se CP-ORG-3 falhar: ⚠️ WARN - criar MEMORY manualmente
Se CP-ORG-4 falhar: ⚠️ WARN - revisar duplicatas
```

---

## INTEGRACAO COM ORG-PROTOCOL

Este protocolo IMPLEMENTA as regras definidas em:
→ `/agents/ORG-LIVE/ORG/ORG-PROTOCOL.md`

Especificamente:
1. **FONTE OBRIGATORIA** - Toda adicao tem [FONTE] citada
2. **ALIMENTACAO AUTOMATICA** - Pipeline Jarvis alimenta ROLEs
3. **RASTREABILIDADE** - insight_id → chunk_id → arquivo fonte

---

## ARQUIVOS RELACIONADOS

| Arquivo | Proposito |
|---------|-----------|
| `ORG-PROTOCOL.md` | Regras gerais de alimentacao |
| `ORG-CHART.md` | Organograma visual |
| `SCALING-TRIGGERS.md` | Quando separar funcoes |
| `ROLE-*.md` | Documentos de cargo |
| `MEMORY-*.md` | Memorias dos cargos |

---

*ORG-LIVE-ENRICHMENT-PROTOCOL v1.0.0*
*Ecossistema [SUA EMPRESA] - ISOLATED*
