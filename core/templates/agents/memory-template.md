# MEMORY-PROTOCOL

> **Versão:** 2.0.0
> **Propósito:** Governar uso e atualização de MEMORY.md para todos os agentes
> **Escopo:** Agentes HÍBRIDO (CARGO) e SOLO (PESSOA)
> **Integrado com:** AGENT-COGNITION-PROTOCOL (FASE 1.5), AGENT-INTEGRITY-PROTOCOL

---

## ⚠️ REGRA INQUEBRÁVEL: RASTREABILIDADE 100%

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   TODA ENTRADA NO MEMORY.md DEVE TER RASTREABILIDADE COMPLETA               ║
║                                                                              ║
║   Campos OBRIGATÓRIOS em cada insight/padrão:                               ║
║   ┌────────────────────────────────────────────────────────────────────┐    ║
║   │ chunk_id        → ID do chunk em CHUNKS-STATE.json                 │    ║
║   │ insight_id      → ID do insight em INSIGHTS-STATE.json             │    ║
║   │ PATH_RAIZ       → Caminho completo até inbox/*.txt              │    ║
║   │ linha           → Número da linha no arquivo original              │    ║
║   └────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║   INSIGHT SEM PATH_RAIZ = NÃO RASTREÁVEL = NÃO CONFIÁVEL                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Navegação Reversa Garantida

```
MEMORY.md → chunk_id → CHUNKS-STATE.json → source_file → inbox/*.txt
                                               ↑
                                    Texto bruto original
```

### Formato de Citação Expandido

```markdown
| Data | Insight | chunk_id | PATH_RAIZ | Testado? |
|------|---------|----------|-----------|----------|
| 2024-12-15 | LTV/CAC < 3 = problema | chunk_201 | /inbox/ALEX HORMOZI/.../arquivo.txt:45 | não |
```

---

## VISÃO GERAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  MEMORY.md = EXPERIÊNCIA ACUMULADA                                          │
│                                                                             │
│  DNA = Conhecimento teórico extraído das fontes (estático, estruturado)    │
│  MEMORY = Experiência prática, decisões, padrões (dinâmico, acumulativo)   │
│                                                                             │
│  DNA responde: "O que as fontes dizem?"                                    │
│  MEMORY responde: "O que já experimentamos/observamos?"                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## DIFERENÇA: HÍBRIDO vs SOLO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  MEMORY DE AGENTE HÍBRIDO (CARGO)                                           │
│  ─────────────────────────────────                                          │
│                                                                             │
│  Localização: /agents/cargo/{AREA}/{CARGO}/MEMORY.md                    │
│                                                                             │
│  CONTÉM:                                                                    │
│  • Decisões tomadas no contexto do cargo                                   │
│  • Precedentes (situações similares já enfrentadas)                        │
│  • Aprendizados operacionais (o que funcionou/não funcionou)               │
│  • Calibrações Brasil (adaptações para mercado local)                      │
│  • Resoluções de conflitos entre fontes                                    │
│  • Feedback recebido sobre recomendações                                   │
│                                                                             │
│  PROPÓSITO:                                                                 │
│  Acumular sabedoria prática do CARGO, não da pessoa individual             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MEMORY DE AGENTE SOLO (PESSOA)                                             │
│  ───────────────────────────────                                            │
│                                                                             │
│  Localização: /agents/persons/{PESSOA}/MEMORY.md                        │
│                                                                             │
│  CONTÉM:                                                                    │
│  • Insights extraídos das fontes processadas                               │
│  • Padrões de pensamento identificados                                     │
│  • Frases características e expressões típicas                             │
│  • Analogias e metáforas preferidas                                        │
│  • Lista de materiais já processados                                       │
│  • Contradições internas (se a pessoa mudou de opinião)                    │
│                                                                             │
│  PROPÓSITO:                                                                 │
│  Capturar a ESSÊNCIA de como a pessoa pensa e se expressa                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ESTRUTURA DO MEMORY.md

### Para Agentes HÍBRIDO (CARGO)

```markdown
# MEMORY: {CARGO}

> **Atualizado:** {DATA}
> **Versão:** X.Y.Z

---

## TEAM AGREEMENT

> Princípios acordados pelo time que este cargo segue

### Como Este Cargo Opera
- {Princípio 1}
- {Princípio 2}

### Alinhamento com Outros Cargos
- {Relação 1}
- {Relação 2}

---

## METADADOS DE CONTEXTO

| Contexto | Valor | Fonte |
|----------|-------|-------|
| Mercado | Brasil B2B High-Ticket | Calibração local |
| Ticket médio | R$ X.XXX | {se conhecido} |
| Fase atual | MVP/Escala/Maturidade | {se conhecido} |

---

## PADRÕES DECISÓRIOS

### {Categoria de Decisão}

**Padrão identificado:**
{Descrição do padrão}

**Rastreabilidade:**
| Fonte | chunk_id | insight_id | PATH_RAIZ |
|-------|----------|------------|-----------|
| {FONTE-1} | chunk_XXX | insight_YYY | /inbox/.../arquivo.txt:linha |
| {FONTE-2} | chunk_XXX | insight_YYY | /inbox/.../arquivo.txt:linha |

**Citação bruta:**
> "{Texto original da fonte}" — ^[chunk_id]

**Aplicabilidade:**
{Quando usar este padrão}

**Exceções conhecidas:**
{Quando NÃO usar}

---

## APRENDIZADOS ACUMULADOS

### {DATA} - {Título do Aprendizado}

**Contexto:**
{Situação que gerou o aprendizado}

**Decisão tomada:**
{O que foi decidido}

**Rastreabilidade das fontes:**
| Fonte | chunk_id | PATH_RAIZ | Citação |
|-------|----------|-----------|---------|
| {FONTE-1} | chunk_XXX | /inbox/.../arquivo.txt:linha | "{texto bruto}" |

**Resultado:**
{Se conhecido, o que aconteceu}

**Status:** ✅ Testado | ⏳ Não testado

**Lição:**
{O que aprendemos para próxima vez}

---

## CALIBRAÇÕES BRASIL

### {Área de Calibração}

**Original (fonte EUA):**
{O que a fonte diz}

**Rastreabilidade:**
| chunk_id | PATH_RAIZ | Citação original |
|----------|-----------|------------------|
| chunk_XXX | /inbox/.../arquivo.txt:linha | "{texto bruto em inglês}" |

**Adaptação Brasil:**
{Como aplicamos aqui}

**Justificativa:**
{Por que a adaptação - esta é interpretação local, não tem fonte primária}

---

## RESOLUÇÕES DE CONFLITOS

### {CONF-XXX} - {Descrição}

**Fontes em conflito com rastreabilidade:**

| Fonte | Posição | chunk_id | PATH_RAIZ | Citação |
|-------|---------|----------|-----------|---------|
| {FONTE-1} | {posição} | chunk_XXX | /inbox/.../arquivo.txt:linha | "{bruto}" |
| {FONTE-2} | {posição} | chunk_YYY | /inbox/.../arquivo.txt:linha | "{bruto}" |

**Resolução adotada:**
{Como resolvemos}
*Esta resolução é síntese do sistema, não tem fonte primária única.*

**Contexto da resolução:**
{Quando aplicar esta resolução}

---

## HISTÓRICO DE ATUALIZAÇÕES

| Data | Mudança | Gatilho |
|------|---------|---------|
| {DATA} | {Descrição} | {O que causou} |
```

### Para Agentes SOLO (PESSOA)

```markdown
# MEMORY: {PESSOA}

> **Atualizado:** {DATA}
> **Versão:** X.Y.Z

---

## MATERIAIS PROCESSADOS

| Material | Tipo | Data Processamento |
|----------|------|-------------------|
| {Título} | {Podcast/Curso/Livro} | {DATA} |

---

## PADRÕES DE PENSAMENTO

### {Padrão Identificado}

**Descrição:**
{Como a pessoa raciocina sobre isso}

**Exemplos de uso:**
- {Exemplo 1}
- {Exemplo 2}

**Rastreabilidade:**
| chunk_id | insight_id | PATH_RAIZ | Citação bruta |
|----------|------------|-----------|---------------|
| chunk_XXX | insight_YYY | /inbox/{PESSOA}/...txt:linha | "{texto original}" |

---

## EXPRESSÕES CARACTERÍSTICAS

| Expressão | Contexto de Uso | chunk_id | PATH_RAIZ |
|-----------|-----------------|----------|-----------|
| "{Frase típica exata}" | {Quando usa} | chunk_XXX | /inbox/.../arquivo.txt:linha |

---

## ANALOGIAS E METÁFORAS

### {Analogia}

**Uso:**
{Como a pessoa usa esta analogia}

**Contexto:**
{Quando é aplicada}

**Rastreabilidade:**
| chunk_id | PATH_RAIZ | Citação bruta |
|----------|-----------|---------------|
| chunk_XXX | /inbox/.../arquivo.txt:linha | "{texto exato onde usa a analogia}" |

---

## INSIGHTS EXTRAÍDOS

### {DATA} - {Título do Insight}

**Rastreabilidade:**
| Campo | Valor |
|-------|-------|
| insight_id | insight_XXX |
| chunk_id | chunk_YYY |
| PATH_RAIZ | /inbox/{PESSOA}/.../arquivo.txt |
| Linha | 45-52 |

**Insight:**
{Padrão ou pensamento extraído}

**Citação bruta:**
> "{Texto exato do material original}" — ^[chunk_id]

**Contexto de uso:**
{Quando a pessoa usa este raciocínio}

---

## CONTRADIÇÕES/EVOLUÇÕES

### {Tema com Mudança}

**Posição anterior:**
{O que dizia antes}

| chunk_id | PATH_RAIZ | Citação |
|----------|-----------|---------|
| chunk_XXX | /inbox/.../arquivo_antigo.txt:linha | "{bruto}" |

**Posição atual:**
{O que diz agora}

| chunk_id | PATH_RAIZ | Citação |
|----------|-----------|---------|
| chunk_YYY | /inbox/.../arquivo_recente.txt:linha | "{bruto}" |

**Nota:**
{Interpretação da mudança - esta é análise do sistema, não fonte primária}

---

## HISTÓRICO DE ATUALIZAÇÕES

| Data | Mudança | Material Processado |
|------|---------|---------------------|
| {DATA} | {Descrição} | {Material} |
```

---

## QUANDO ATUALIZAR MEMORY

### Gatilhos para Agentes HÍBRIDO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  GATILHOS DE ATUALIZAÇÃO (HÍBRIDO)                                          │
│                                                                             │
│  ✅ ATUALIZAR quando:                                                       │
│  • Nova decisão tomada com justificativa documentável                      │
│  • Conflito entre fontes resolvido de forma nova                           │
│  • Calibração específica para contexto Brasil identificada                 │
│  • Feedback do usuário sobre recomendação (positivo ou negativo)           │
│  • Padrão novo identificado que se repetirá                                │
│  • Exceção importante a uma regra existente                                │
│                                                                             │
│  ❌ NÃO ATUALIZAR quando:                                                   │
│  • Informação já está no DNA (evitar duplicação)                           │
│  • Caso único que não se repetirá                                          │
│  • Apenas aplicou conhecimento existente sem novo insight                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Gatilhos para Agentes SOLO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  GATILHOS DE ATUALIZAÇÃO (SOLO)                                             │
│                                                                             │
│  ✅ ATUALIZAR quando:                                                       │
│  • Novo material da pessoa processado                                      │
│  • Nova expressão característica identificada                              │
│  • Novo padrão de pensamento descoberto                                    │
│  • Contradição/evolução de posição identificada                            │
│  • Nova analogia ou metáfora típica encontrada                             │
│                                                                             │
│  ❌ NÃO ATUALIZAR quando:                                                   │
│  • Informação já está no DNA (evitar duplicação)                           │
│  • Conteúdo genérico sem marca pessoal                                     │
│  • Repetição de algo já documentado                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## COMO CONSULTAR MEMORY

### Ordem de Consulta

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  1. MEMORY primeiro (experiência prática)                                   │
│     └─ "Já enfrentamos situação similar?"                                  │
│     └─ "Há precedente para esta decisão?"                                  │
│     └─ "Existe calibração Brasil para isso?"                               │
│                                                                             │
│  2. DNA depois (conhecimento teórico)                                       │
│     └─ Cascata: Metodologia → Framework → Heurística → etc.                │
│                                                                             │
│  3. Combinar                                                                │
│     └─ MEMORY dá contexto prático                                          │
│     └─ DNA dá embasamento teórico                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Citação de MEMORY

```
Formato:
[MEMORY:{CARGO/PESSOA}:{SEÇÃO}] > "conteúdo"

Exemplos:
[MEMORY:CLOSER:CALIBRAÇÕES] > "Em Brasil, objeção de preço é mais frequente"
[MEMORY:ALEX-HORMOZI:EXPRESSÕES] > "Volume negates luck"
```

---

## REGRAS DE INTEGRIDADE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  REGRAS INVIOLÁVEIS                                                         │
│                                                                             │
│  1. NÃO DUPLICAR DNA                                                        │
│     └─ Se está no DNA, não precisa estar no MEMORY                         │
│     └─ MEMORY = experiência, DNA = teoria                                  │
│                                                                             │
│  2. SEMPRE DATAR                                                            │
│     └─ Toda entrada tem data de criação                                    │
│     └─ Permite rastrear evolução temporal                                  │
│                                                                             │
│  3. RASTREABILIDADE                                                         │
│     └─ Toda entrada indica fonte/gatilho                                   │
│     └─ "Por que isso está aqui?"                                           │
│                                                                             │
│  4. INCREMENTAR, NÃO SUBSTITUIR                                            │
│     └─ Novas entradas se somam às antigas                                  │
│     └─ Histórico é preservado                                              │
│     └─ Exceção: correção de erro factual                                   │
│                                                                             │
│  5. VERSIONAR                                                               │
│     └─ Incrementar versão a cada atualização significativa                 │
│     └─ Formato: MAJOR.MINOR.PATCH                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FLUXO DE ATUALIZAÇÃO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  GATILHO IDENTIFICADO                                                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────┐                                                        │
│  │ Já está no DNA? │                                                        │
│  └─────────────────┘                                                        │
│         │                                                                   │
│    ┌────┴────┐                                                              │
│    ▼         ▼                                                              │
│   SIM       NÃO                                                             │
│    │         │                                                              │
│    ▼         ▼                                                              │
│  IGNORAR  ┌─────────────────┐                                               │
│           │ É experiência   │                                               │
│           │ prática?        │                                               │
│           └─────────────────┘                                               │
│                  │                                                          │
│             ┌────┴────┐                                                     │
│             ▼         ▼                                                     │
│            SIM       NÃO                                                    │
│             │         │                                                     │
│             ▼         ▼                                                     │
│         ADICIONAR  Considerar                                               │
│         ao MEMORY  adicionar ao DNA                                         │
│             │                                                               │
│             ▼                                                               │
│  ┌─────────────────────┐                                                    │
│  │ Formatar entrada    │                                                    │
│  │ conforme template   │                                                    │
│  └─────────────────────┘                                                    │
│             │                                                               │
│             ▼                                                               │
│  ┌─────────────────────┐                                                    │
│  │ Incrementar versão  │                                                    │
│  └─────────────────────┘                                                    │
│             │                                                               │
│             ▼                                                               │
│  ┌─────────────────────┐                                                    │
│  │ Atualizar histórico │                                                    │
│  └─────────────────────┘                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## INTEGRAÇÃO COM OUTROS PROTOCOLOS

| Protocolo | Integração |
|-----------|------------|
| **AGENT-COGNITION-PROTOCOL** | MEMORY é carregado na FASE 0 (Ativação) e atualizado na FASE 3 |
| **EPISTEMIC-PROTOCOL** | MEMORY pode ser citado como "fonte" de experiência prática |
| **REASONING-MODEL-PROTOCOL** | Consultar MEMORY antes de aplicar cascata DNA |

---

## VALIDAÇÃO DE RASTREABILIDADE

Antes de publicar um MEMORY.md, verificar:

```
┌─────────────────────────────────────────────────────────────────────┐
│  CHECKLIST DE VALIDAÇÃO                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [ ] Toda tabela de insight tem chunk_id                           │
│  [ ] Toda tabela tem PATH_RAIZ com linha                           │
│  [ ] Toda citação bruta está entre aspas                           │
│  [ ] Sínteses/interpretações estão marcadas como tal               │
│  [ ] Navegação reversa funciona até inbox                       │
│  [ ] Números específicos têm fonte primária                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## HISTÓRICO

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0.0 | 2024-12-25 | Criação inicial |
| 2.0.0 | 2025-12-25 | Integração com rastreabilidade completa (FASE 1.5) |

---

*MEMORY-PROTOCOL v2.0.0*
*Integrado com AGENT-COGNITION-PROTOCOL (FASE 1.5) e AGENT-INTEGRITY-PROTOCOL*
