# DOSSIER COMPILATION PROTOCOL (Prompt 4.0)

> **Versão:** 1.6.0
> **Pipeline:** Jarvis → Etapa 4.0 (antes de SOURCES)
> **Output:** `/knowledge/dossiers/persons/` e `/knowledge/dossiers/THEMES/`
> **Protocolo de Escrita:** `NARRATIVE-METABOLISM-PROTOCOL.md` (OBRIGATÓRIO)
> **Próxima Etapa:** SOURCES-COMPILATION-PROTOCOL.md (Phase 6.6)
> **Navegação:** 5 NÍVEIS (lê DOSSIER → NARRATIVE → INSIGHT → CANONICAL → CHUNK)

---

## 🔴 REGRA INVIOLÁVEL: RASTREABILIDADE INLINE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  TODA AFIRMAÇÃO NO DOSSIÊ DEVE TER REFERÊNCIA DE CHUNK INLINE               │
│                                                                             │
│  ✅ CORRETO:                                                                │
│     "Closers devem fazer 5 calls por dia" [chunk_CG001_012]                 │
│     > "{citação exata}" [chunk_AH003_045]                                   │
│                                                                             │
│  ❌ ERRADO:                                                                 │
│     "Closers devem fazer 5 calls por dia" (sem referência)                  │
│     Apenas listar chunks no final do documento                              │
│                                                                             │
│  FORMATO OBRIGATÓRIO:                                                       │
│     [chunk_{SOURCE_ID}_{CHUNK_NUMBER}]                                      │
│                                                                             │
│  ONDE USAR:                                                                 │
│     • Após cada afirmação factual                                           │
│     • Após cada citação                                                     │
│     • Após cada métrica/número                                              │
│     • Em tabelas de evidências                                              │
│     • Em tabelas de tensões/contradições                                    │
│                                                                             │
│  BENEFÍCIO:                                                                 │
│     Sistema pode navegar do dossiê consolidado até o texto original         │
│     em qualquer momento, permitindo verificação e aprofundamento.           │
│                                                                             │
│  ⚠️ DOSSIÊS SEM CHUNK REFERENCES INLINE DEVEM SER REPROCESSADOS             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📖 NARRATIVE METABOLISM (OBRIGATÓRIO)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  TODO dossiê DEVE seguir o NARRATIVE-METABOLISM-PROTOCOL.md                 │
│                                                                             │
│  ESTRUTURA OBRIGATÓRIA:                                                     │
│  1. TL;DR (Em resumo: + Versão + Atualizado + Densidade)                    │
│  2. Filosofia Central (o "porquê")                                          │
│  3. Modus Operandi (o "como")                                               │
│  4. Arsenal Técnico (o "o quê")                                             │
│  5. Armadilhas (o que NÃO fazer)                                            │
│  6. Citações Originais (quotes preservadas)                                 │
│  7. Metadados (fonte, chunks, insights)                                     │
│                                                                             │
│  VOZ:                                                                       │
│  • DOSSIERS/persons: 1ª pessoa (voz da fonte)                               │
│  • DOSSIERS/THEMES: Narrador neutro (síntese multi-fonte)                   │
│                                                                             │
│  DIAGRAMAS: ASCII (┌─┐│└┘├┤) onde framework visual ajuda                    │
│  IDIOMA: Português BR + termos técnicos em inglês                           │
│  DENSIDADE: Indicador ◯ a ◐ (1-5) obrigatório no header                     │
│                                                                             │
│  Ver: core/templates/PIPELINE/NARRATIVE-METABOLISM-PROTOCOL.md                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ PRINCÍPIO FUNDAMENTAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  O SISTEMA DIGESTIVO NÃO TEM THRESHOLDS.                                    │
│                                                                             │
│  • Captura TUDO                                                             │
│  • Organiza TUDO                                                            │
│  • Referencia TUDO                                                          │
│  • Cria dossiê para TODA pessoa                                             │
│  • Cria dossiê para TODO tema                                               │
│                                                                             │
│  A decisão de "isso é relevante?" é feita pelos AGENTES no momento          │
│  da consulta, NÃO pelo sistema digestivo no momento da ingestão.            │
│                                                                             │
│  ÚNICO THRESHOLD NO JARVIS: Role-Tracking para criação de novos agentes.    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 ESTRUTURA DE CONHECIMENTO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  /knowledge/                                                             │
│  ├── DOSSIERS/          ← Consolidação MULTI-FONTE                          │
│  │   ├── PERSONS/       → 1 pessoa, TODOS os temas                          │
│  │   └── THEMES/        → 1 tema, MÚLTIPLAS pessoas                         │
│  │                                                                          │
│  └── SOURCES/           ← Consolidação UNI-FONTE                            │
│      └── {PESSOA}/      → 1 pessoa, 1 tema por arquivo                      │
│          └── {TEMA}.md  → Tudo que esta pessoa disse sobre este tema        │
│                                                                             │
│  FLUXO: DOSSIERS (Phase 6.5) → SOURCES (Phase 6.6)                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Ver:** `core/templates/PIPELINE/SOURCES-COMPILATION-PROTOCOL.md`

---

## ⛔ CHECKPOINT OBRIGATÓRIO (executar ANTES de processar)

```
VALIDAR ANTES DE EXECUTAR:
[ ] CP-4.0.A: NARRATIVES-STATE.json existe em /artifacts/narratives/
[ ] CP-4.0.B: Pelo menos 1 pessoa com narrativa
[ ] CP-4.0.C: open_loops identificados (verificar pendências)

Se CP-4.0.A falhar: ⛔ PARAR - "Execute Etapa 3.1 primeiro"
Se CP-4.0.B falhar: ⛔ PARAR - "Nenhuma narrativa para compilar"
Se CP-4.0.C falhar: ⚠️ WARN - "Verificar open_loops pendentes"
```

Ver: `core/templates/SYSTEM/CHECKPOINT-ENFORCEMENT.md`

---

## PROPÓSITO

Transformar o output JSON do Prompt 3.1 em documentos Markdown estruturados, legíveis e prontos para consulta humana.

---

## INPUTS

### Input A: narratives_state (output do Prompt 3.1)
```json
{
  "narratives_state": {
    "persons": {
      "Nome Canônico": {
        "narrative": "...",
        "last_updated": "...",
        "patterns": [...],
        "positions_by_theme": {...},
        "tensions": [...],
        "open_loops": [...],
        "next_questions": [...]
      }
    },
    "themes": { /* mesmo formato */ }
  }
}
```

### Input B: insights_state (output do Prompt 2.1 — para detalhes)

### Input C: canonical_state (output do Prompt 1.2 — para mapa de entidades)

### Input D: dossier_anterior (se existir — para atualização incremental)

---

## TAREFA PARA PESSOA

Para cada PESSOA em narratives_state.persons:

### 1. PERFIL EXECUTIVO
- Sintetize a narrativa em 3-5 linhas de alto nível
- Extraia palavras-chave dos temas associados

### 2. PADRÕES DECISÓRIOS
- Analise os insights HIGH priority
- Identifique padrões comportamentais recorrentes
- Agrupe por tipo de padrão
- Para cada padrão:
  - Nome descritivo
  - Descrição do comportamento
  - Evidências (id_chunk com citação)
  - Implicação prática
- **REGRA:** Novos padrões são ADICIONADOS, não substituem anteriores

### 3. POSICIONAMENTOS POR TEMA
- Para cada tema associado à pessoa nos insights:
  - Posição central (2-3 linhas)
  - Nuances e condições (lista)
  - Evidências (chunks)
  - Confiança (ALTA/MÉDIA/BAIXA) + justificativa
- **REGRA:** Novos temas são ADICIONADOS, existentes são REFINADOS

### 4. HISTÓRICO DE EVOLUÇÃO
- Ordene por data (source_datetime)
- Para cada data/fonte: o que foi adicionado, mudanças
- **REGRA:** NUNCA apagar entradas anteriores

### 5. TENSÕES E CONTRADIÇÕES
- Formate em tabela comparativa (Ponto A vs Ponto B)
- Inclua possível explicação
- Status com emoji

### 6. OPEN LOOPS
- Tabela com: questão, impacto, dono provável, status

### 7. PRÓXIMAS PERGUNTAS
- Lista numerada baseada em gaps atuais
- **REGRA:** Esta seção PODE ser substituída a cada atualização

### 8. ÍNDICE DE FONTES
- Tabela com todos os chunks

---

## TAREFA PARA TEMA

Para cada TEMA em narratives_state.themes (TODOS, SEM EXCEÇÃO):

### 1. SÍNTESE EXECUTIVA
- Resumo do estado do conhecimento

### 2. CONSENSOS IDENTIFICADOS
- Encontre pontos onde múltiplas pessoas convergem
- Cite evidências cruzadas
- Classifique força do consenso

### 3. POSIÇÕES POR PESSOA
- Para cada pessoa nos insights do tema:
  - Posição resumida
  - Nuances
  - Link para dossiê da pessoa

### 4. DIVERGÊNCIAS
- Onde pessoas discordam
- Tabela comparativa
- Análise do porquê
- Recomendação contextual

### 5. FRAMEWORKS E MODELOS
- Extraia frameworks práticos
- Estruture de forma aplicável
- Inclua quando usar e limitações

### 6. MÉTRICAS E BENCHMARKS
- Tabela com: métrica, valor, fonte, contexto, confiança

### 7. HISTÓRICO DE EVOLUÇÃO
- Mesmo formato de pessoa

### 8. GAPS DE CONHECIMENTO
- O que falta saber, impacto, como resolver

---

## TEMPLATE: DOSSIÊ PESSOA

```markdown
# DOSSIÊ: {NOME CANÔNICO}

> **Última atualização:** {YYYY-MM-DD HH:MM}
> **Corpus:** {empresa|pessoal|cursos}
> **Sources:** {source_1}, {source_2}, ... | **Chunks:** {N} | **Insights:** {N}
> **Status:** 🟢 Ativo | 🟡 Revisão pendente | 🔴 Contradições

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 PERFIL EXECUTIVO

{Parágrafo síntese de 3-5 linhas}

**Palavras-chave:** {tag1}, {tag2}, {tag3}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🧠 PADRÕES DECISÓRIOS

### Padrão 1: {Nome do Padrão}

{Descrição do padrão comportamental/decisório}

**Evidências:**
- [chunk_X] "{citação}"
- [chunk_Y] "{citação}"

**Implicação:** {Consequência prática}

---

### Padrão N: {Nome}

{Descrição}

**Evidências:**
- [chunk_Z] "{citação}"

**Implicação:** {Consequência}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 POSICIONAMENTOS POR TEMA

### {TEMA 1}

**Posição central:**
{2-3 linhas}

**Nuances e condições:**
- {Condição 1}
- {Condição 2}

**Evidências:** [chunk_A], [chunk_B]

**Confiança:** {ALTA|MÉDIA|BAIXA} — {justificativa}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📈 HISTÓRICO DE EVOLUÇÃO

### {DATA: YYYY-MM-DD}
**Fonte:** {source_title} ({source_type})
**Adição:** {O que foi adicionado}
**Chunks:** [chunk_1, chunk_2]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚠️ TENSÕES E CONTRADIÇÕES

### Tensão 1: {Título}

| Ponto A | Ponto B |
|---------|---------|
| {Afirmação 1} | {Afirmação contraditória} |
| [chunk_X] | [chunk_Y] |

**Possível explicação:** {Hipótese}

**Status:** 🔴 Não resolvida | 🟡 Parcialmente explicada | 🟢 Resolvida

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔓 OPEN LOOPS

| # | Questão | Por que importa | Dono provável | Status |
|---|---------|-----------------|---------------|--------|
| 1 | {Pergunta} | {Impacto} | {Pessoa} | 🔴 Aberto |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ❓ PRÓXIMAS PERGUNTAS

1. {Pergunta estratégica 1}
2. {Pergunta estratégica 2}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📚 ÍNDICE DE FONTES

| Chunk | Fonte | Tipo | Data |
|-------|-------|------|------|
| chunk_1 | {title} | {type} | {date} |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔗 SOURCES POR TEMA

| Tema | Arquivo SOURCES | Status |
|------|-----------------|--------|
| {TEMA-1} | → [/knowledge/SOURCES/{PESSOA}/{TEMA-1}.md] | 🟢 |
| {TEMA-2} | → [/knowledge/SOURCES/{PESSOA}/{TEMA-2}.md] | 🟢 |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                              FIM DO DOSSIÊ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## TEMPLATE: DOSSIÊ TEMA

```markdown
# DOSSIÊ TEMÁTICO: {NOME DO TEMA}

> **Última atualização:** {YYYY-MM-DD HH:MM}
> **Corpus:** {empresa|pessoal|cursos}
> **Sources:** {source_1}, {source_2}, ... | **Pessoas:** {N} | **Chunks:** {N}
> **Status:** 🟢 Consolidado | 🟡 Em construção | 🔴 Divergências críticas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 SÍNTESE EXECUTIVA

{Parágrafo de 3-5 linhas}

**Subtemas relacionados:** {subtema1}, {subtema2}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 CONSENSOS IDENTIFICADOS

### Consenso 1: {Título}

**Afirmação:** {O que é consenso}

**Quem concorda:** {Pessoa A}, {Pessoa B}

**Evidências:** [chunk_X], [chunk_Y]

**Força:** {FORTE|MODERADO|FRACO}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 👥 POSIÇÕES POR PESSOA

### {PESSOA 1}

**Posição resumida:**
{2-3 linhas}

**Nuances:**
- {Condição}

**Evidências:** [chunk_A]

**Link:** → [DOSSIER-NOME.md]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ⚔️ DIVERGÊNCIAS

### Divergência 1: {Título}

| {Pessoa A} | {Pessoa B} |
|------------|------------|
| {Posição A} | {Posição B} |
| [chunk_X] | [chunk_Y] |

**Análise:** {Por que divergem?}

**Recomendação:** {Qual seguir em qual contexto}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📐 FRAMEWORKS E MODELOS

### Framework 1: {Nome}

**Fonte:** {Pessoa} via [chunk_X]

```
{Descrição estruturada}
```

**Quando usar:** {Contexto}

**Limitações:** {Quando NÃO usar}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 MÉTRICAS E BENCHMARKS

| Métrica | Valor | Fonte | Contexto | Confiança |
|---------|-------|-------|----------|-----------|
| {métrica} | {valor} | {pessoa} [chunk] | {contexto} | {ALTA|MÉDIA|BAIXA} |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📈 HISTÓRICO DE EVOLUÇÃO

### {DATA: YYYY-MM-DD}
**Fonte:** {source_title}
**Adição:** {O que foi aprendido}
**Chunks:** [chunk_1, chunk_2]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔓 GAPS DE CONHECIMENTO

| # | Gap | Impacto | Como resolver | Status |
|---|-----|---------|---------------|--------|
| 1 | {O que falta} | {Por que importa} | {Ação} | 🔴 Aberto |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📚 ÍNDICE DE FONTES

| Chunk | Fonte | Tipo | Pessoa | Data |
|-------|-------|------|--------|------|
| chunk_1 | {title} | {type} | {person} | {date} |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔗 SOURCES POR PESSOA

| Pessoa | Arquivo SOURCES | Status |
|--------|-----------------|--------|
| {PESSOA-1} | → [/knowledge/SOURCES/{PESSOA-1}/{TEMA}.md] | 🟢 |
| {PESSOA-2} | → [/knowledge/SOURCES/{PESSOA-2}/{TEMA}.md] | 🟢 |

_(Cada link leva ao que esta pessoa específica disse sobre este tema)_

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                           FIM DO DOSSIÊ TEMÁTICO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## REGRAS DE FORMATAÇÃO

1. Use os templates padronizados
2. Mantenha separadores visuais (━━━) entre seções
3. Use emojis nos headers para navegação rápida
4. Toda afirmação deve ter [chunk_X] como referência
5. Tabelas para dados estruturados, prosa para análises
6. Confiança sempre justificada
7. Status com emoji: 🟢 🟡 🔴
8. Marque seções novas com "— NOVO EM {DATA}"
9. Links entre dossiês: → [DOSSIER-NOME.md]

---

## REGRAS DE ATUALIZAÇÃO INCREMENTAL

| Seção | Comportamento |
|-------|---------------|
| Perfil Executivo | REESCREVER se padrão fundamental mudou |
| Padrões Decisórios | ADICIONAR novos, EXPANDIR evidências |
| Posicionamentos | ADICIONAR temas novos, ATUALIZAR nuances |
| Histórico | SEMPRE ADICIONAR (nunca apagar) |
| Tensões | ADICIONAR novas, ATUALIZAR status |
| Open Loops | ADICIONAR novos, FECHAR resolvidos |
| Próximas Perguntas | SUBSTITUIR com base em gaps atuais |
| Índice de Fontes | SEMPRE ADICIONAR novos chunks |

---

## SALVAMENTO

### Dossiês de Pessoas:
```
/knowledge/dossiers/persons/DOSSIER-{NOME-CANONICO}.md
```
- Nome em UPPERCASE
- Espaços substituídos por hífen
- Exemplo: `DOSSIER-ALEX-HORMOZI.md`

### Dossiês de Temas:
```
/knowledge/dossiers/THEMES/DOSSIER-{NOME-TEMA}.md
```
- Nome em UPPERCASE
- Espaços substituídos por hífen
- Exemplo: `DOSSIER-COMISSIONAMENTO.md`

---

## INTEGRAÇÃO COM RAG

Ao salvar dossiê, indexar no ChromaDB com metadados:

```python
{
    "id": "DOSSIER-HORMOZI-padrao-velocidade",
    "content": "Conteúdo da seção...",
    "metadata": {
        "type": "dossier_section",
        "entity_type": "person",
        "entity_name": "Alex Hormozi",
        "section": "padroes_decisorios",
        "priority": "high",
        "confidence": "alta",
        "source_chunks": ["chunk_12", "chunk_34"],
        "last_updated": "2025-12-15"
    }
}
```

---

## EXECUÇÃO AUTOMÁTICA (CHAMADA PELO PROCESS-JARVIS)

Este protocolo é executado pela PHASE 6.5 do process-jarvis.md.

### Modo de Operação

```
FOR each PERSON in NARRATIVES_STATE.persons:

  DOSSIER_PATH = /knowledge/dossiers/persons/DOSSIER-{NOME_UPPERCASE}.md

  IF file EXISTS at DOSSIER_PATH:
    MODE = "INCREMENTAL"
    READ existing_dossier
    APPLY regras de atualização incremental (tabela acima)
    APPEND new source to sources[] no header
  ELSE:
    MODE = "CREATE"
    GENERATE dossier from template
    SET sources[] = [current_source]

  WRITE to DOSSIER_PATH

FOR each THEME in NARRATIVES_STATE.themes:

  # SEM VERIFICAÇÃO DE ELEGIBILIDADE
  # CRIAR DOSSIÊ PARA TODO TEMA, SEM EXCEÇÃO
  # O sistema digestivo CAPTURA TUDO - agentes decidem relevância depois

  DOSSIER_PATH = /knowledge/dossiers/THEMES/DOSSIER-{TEMA_UPPERCASE}.md

  IF file EXISTS at DOSSIER_PATH:
    MODE = "INCREMENTAL"
    READ existing_dossier
    APPLY regras de atualização incremental (tabela acima)
    APPEND new source to sources[] no header
    UPDATE seção "POSIÇÕES POR PESSOA" com novos contributors
  ELSE:
    MODE = "CREATE"
    GENERATE dossier from template
    SET sources[] = [current_source]
    SET contributors[] from THEME.contributors

  WRITE to DOSSIER_PATH
  LOG("✅ Dossiê de tema criado/atualizado: {DOSSIER_PATH}")
```

### Update de Agent MEMORYs

```
# NOTA: Atualização de Agent MEMORYs foi CONSOLIDADA em Phase 7 (Agent Enrichment)
# Motivo: Evitar duplicação (antes executava em Phase 6.5.5, Phase 7.4, e Phase 8.4)
# Ver: process-jarvis.md → Phase 7.4

# NÃO executar update de MEMORYs nesta fase
# A lógica abaixo é REFERÊNCIA para Phase 7:

THEME_TO_AGENTS = {
  "01-ESTRUTURA-TIME": ["SALES-MANAGER"],
  "02-PROCESSO-VENDAS": ["closer", "SDS", "BDR"],
  "03-CONTRATACAO": ["SALES-MANAGER", "COO"],
  "04-COMISSIONAMENTO": ["SALES-MANAGER", "CRO", "CFO"],
  "05-METRICAS": ["CRO", "CFO"],
  "06-FUNIL-APLICACAO": ["SDS", "BDR", "LNS"],
  "07-PRICING": ["CRO", "CFO"],
  "08-FERRAMENTAS": ["SALES-COORDINATOR", "COO"],
  "09-GESTAO": ["COO", "SALES-MANAGER"],
  "10-CULTURA-GAMIFICACAO": ["COO", "SALES-MANAGER"],
  "EXIT-SCALING": ["CRO", "CFO", "COO"]
}

# Executado em Phase 7.4, não aqui
```

### Indexação RAG em Dois Eixos

```
# EIXO 1: POR PESSOA
FOR each PERSON dossier created/updated:
  INDEX in ChromaDB with:
    - collection: "dossiers_persons"
    - metadata.entity_type: "person"
    - metadata.entity_name: PERSON_NAME

# EIXO 2: POR TEMA
FOR each THEME dossier created/updated:
  INDEX in ChromaDB with:
    - collection: "dossiers_themes"
    - metadata.entity_type: "theme"
    - metadata.entity_name: THEME_NAME
```

### Update de SESSION-STATE.md

```
LOCATE /system/SESSION-STATE.md
LOCATE tabela de "Arquivos Processados"
INSERT row:
| {SOURCE_ID} | {SOURCE_TITLE} | {SOURCE_PERSON} | {SOURCE_TYPE} | ✅ Completo | {TODAY} |
```

### Update de role-tracking.md

```
# NOTA: Role-Tracking foi MOVIDO para Phase 8.1.7 (Role Discovery)
# Execução centralizada usando INSIGHTS-STATE.json (dados mais ricos)
# Ver: process-jarvis.md → Phase 8.1.7

# NÃO executar role-tracking nesta fase
# Motivo: INSIGHTS têm confidence levels, priority, chunk_refs
```

---

## VALIDAÇÃO FINAL

Antes de salvar dossiê:

| Check | Critério |
|-------|----------|
| Estrutura | Todas as seções obrigatórias presentes |
| Rastreabilidade | Todo parágrafo tem chunk de referência |
| Consistência | Links entre dossiês funcionam |
| Completude | Histórico não tem gaps |
| Formatação | Separadores e emojis corretos |

---

## ✓ CHECKPOINT APÓS EXECUÇÃO (OBRIGATÓRIO)

```
VALIDAR APÓS EXECUTAR:

# PESSOA (obrigatório - TODOS)
[ ] CP-POST-6.A: /knowledge/dossiers/persons/DOSSIER-{SOURCE_PERSON}.md existe
[ ] CP-POST-6.B: Dossiê contém seção "PERFIL EXECUTIVO"
[ ] CP-POST-6.C: Dossiê contém seção "ÍNDICE DE FONTES"

# TEMA (obrigatório - TODOS, SEM THRESHOLD)
[ ] CP-POST-6.D: Para CADA TEMA em NARRATIVES_STATE.themes:
                 /knowledge/dossiers/THEMES/DOSSIER-{TEMA}.md DEVE existir
                 (NÃO HÁ THRESHOLD - TODO tema gera dossiê)
[ ] CP-POST-6.E: Dossiê de tema contém seção "SÍNTESE EXECUTIVA"
[ ] CP-POST-6.F: Dossiê de tema contém seção "POSIÇÕES POR PESSOA"

Se CP-POST-6.A falhar: ⛔ EXIT("Phase 6 não criou DOSSIER para pessoa principal")
Se CP-POST-6.B falhar: ⚠️ WARN("Dossiê incompleto - sem PERFIL EXECUTIVO")
Se CP-POST-6.C falhar: ⚠️ WARN("Dossiê sem ÍNDICE DE FONTES")
Se CP-POST-6.D falhar: ⛔ EXIT("Phase 6 não criou DOSSIER para tema: {TEMA}")
Se CP-POST-6.E falhar: ⚠️ WARN("Dossiê de tema incompleto - sem SÍNTESE EXECUTIVA")
Se CP-POST-6.F falhar: ⚠️ WARN("Dossiê de tema sem POSIÇÕES POR PESSOA")
```

**BLOQUEANTES (A e D):** Não prosseguir para Phase 7 se DOSSIER de pessoa OU tema não foi criado.

**IMPORTANTE:** NÃO HÁ THRESHOLD. Todo tema em NARRATIVES_STATE.themes DEVE ter seu dossiê.
O sistema digestivo CAPTURA TUDO. A decisão de relevância é dos AGENTES na consulta.

---

## ✓ CHECKPOINT 7 - VERIFICAÇÃO FINAL (11 itens)

```
CHECKLIST FINAL OBRIGATÓRIO:
[ ] 1. CHUNKS-STATE.json contém chunks do $SOURCE_ID
[ ] 2. CANONICAL-MAP.json atualizado com entidades
[ ] 3. INSIGHTS-STATE.json contém insights
[ ] 4. NARRATIVES-STATE.json contém narrativa (persons + themes)
[ ] 5. DOSSIER-{SOURCE_PERSON}.md existe
[ ] 6. DOSSIER-{TEMA}.md existe para CADA tema (SEM THRESHOLD)
[ ] 7. Pelo menos 1 agent MEMORY atualizado
[ ] 8. RAG index inclui novos arquivos (persons + themes)
[ ] 9. file-registry.json tem entrada
[ ] 10. SESSION-STATE.md atualizado
[ ] 11. Dossiês de tema linkam para dossiês de pessoa (cross-reference)

Se qualquer item 1-6 falhar: ⛔ EXIT(VERIFICATION_FAILED) com detalhes
Se qualquer item 7-11 falhar: ⚠️ WARN com detalhes (não bloqueante)
```

**ITENS 1-6 SÃO BLOQUEANTES. ITENS 7-11 SÃO WARNINGS.**

**REGRA FUNDAMENTAL:** O sistema digestivo NÃO FILTRA. Ele captura, organiza e referencia TUDO.
O único threshold no sistema Jarvis está no ROLE-TRACKING para criação de novos agentes.

---

## PRÓXIMA ETAPA

Após conclusão do DOSSIER COMPILATION (Phase 6.5), executar:

→ **SOURCES-COMPILATION-PROTOCOL.md (Phase 6.6)**

```
core/templates/PIPELINE/SOURCES-COMPILATION-PROTOCOL.md
```

Este protocolo cria arquivos em `/knowledge/SOURCES/{PESSOA}/{TEMA}.md` para consolidar
tudo que UMA pessoa disse sobre UM tema, permitindo consulta rápida e rastreabilidade.
