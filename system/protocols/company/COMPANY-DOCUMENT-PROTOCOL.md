# ORG-LIVE DOCUMENT PROTOCOL v1.0

> **Proposito:** Padronizar linguagem, estrutura e rastreabilidade de TODOS os documentos do ecossistema ORG-LIVE
> **Aplicacao:** ORG/, ROLES/, JDS/, MEMORY/
> **Criado:** 2025-12-21
> **Principio Central:** Nenhuma informacao sem fonte. Nenhuma decisao sem responsavel.

---

## Conceito Central: Organizacao Viva

O sistema ORG-LIVE e um **organismo vivo** que:
- **Respira** conhecimento dos AGENTS IA (Pipeline Jarvis → Agents → ROLEs)
- **Evolui** conforme a empresa cresce (gatilhos de escala)
- **Rastreia** toda informacao ate sua origem
- **Prescreve** acoes claras (quem, o que, quando, como)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PIRAMIDE DE RASTREABILIDADE ORG-LIVE                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                          ┌─────────────────┐                                │
│                          │  DECISAO [SUA EMPRESA] │ ← Decisoes internas empresa    │
│                          └────────┬────────┘                                │
│                                   │                                         │
│                          ┌────────▼────────┐                                │
│                          │  FONTE EXTERNA  │ ← Cole Gordon, Hormozi, etc.   │
│                          │  [CODIGO]       │                                │
│                          └────────┬────────┘                                │
│                                   │                                         │
│                          ┌────────▼────────┐                                │
│                          │   AGENT IA      │ ← Processamento do conhecimento│
│                          │ AGENT-CLOSER    │                                │
│                          └────────┬────────┘                                │
│                                   │                                         │
│                          ┌────────▼────────┐                                │
│                          │  ROLE/JD/ORG    │ ← Documento operacional        │
│                          │  ORG-LIVE       │                                │
│                          └─────────────────┘                                │
│                                                                             │
│  FORMATO DE CITACAO:                                                        │
│  [VIA: AGENT-X → Fonte CODIGO] - Conhecimento via agente IA                 │
│  [FONTE: Nome - CODIGO] - Citacao direta de fonte externa                   │
│  [DECISAO [SUA EMPRESA]] - Decisao interna da empresa                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Regra Fundamental: Zero Invencao

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LEI ABSOLUTA DE RASTREABILIDADE                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TODA informacao em documentos ORG-LIVE DEVE ter UMA destas origens:        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. [VIA: AGENT-X → Fonte CODIGO]                                    │    │
│  │    Conhecimento processado por um Agente IA                         │    │
│  │    Ex: [VIA: AGENT-CLOSER → Cole Gordon CG003]                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 2. [FONTE: Nome - CODIGO]                                           │    │
│  │    Citacao direta de expert/fonte externa                           │    │
│  │    Ex: [FONTE: Richard Linder - RL001]                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 3. [DECISAO [SUA EMPRESA]]                                                 │    │
│  │    Decisao interna da empresa (pricing, limites, politicas)         │    │
│  │    Ex: Desconto maximo 10% = [DECISAO [SUA EMPRESA]]                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ⛔ PROIBIDO:                                                               │
│  - Informacao sem marcador de origem                                        │
│  - "Provavelmente", "Talvez", "Geralmente"                                  │
│  - Numeros arredondados quando fonte tem exatos                             │
│  - Opiniao apresentada como fato                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Estruturas por Tipo de Documento

### 1. ROLE-*.md (Cargos)

```markdown
# ROLE: [CARGO]

> **Status:** ATIVO | PLANEJADO | HIBRIDO (com detalhamento)
> **Versao:** X.X.X | **Atualizado:** YYYY-MM-DD
> **Ecossistema:** [SUA EMPRESA]
> **Alimentado por:** AGENT-X, AGENT-Y (lista completa)

---

## CONEXAO COM AGENTES IA

| AGENT Fonte | Conhecimento Herdado | Localizacao |
|-------------|----------------------|-------------|
| AGENT-X | [Lista especifica] | [Path] |

---

## 1. POSICAO NO ORGANOGRAMA

[ASCII diagram OBRIGATORIO mostrando posicao]

**Reporta a:** [Cargo]
**Subordinados Diretos:** [Lista ou "Nenhum"]
**Tipo:** [EXECUCAO | GESTAO | HIBRIDO | ESTRATEGICO]

> **[FONTE/VIA que justifica esta estrutura]**
> "Citacao que embasa"

---

## 2. RESPONSABILIDADES

### Primarias ([%] do tempo)

| Atividade | Frequencia | Meta/Metrica | Fonte |
|-----------|------------|--------------|-------|
| [Atividade] | [Quando] | [KPI] | [FONTE] |

> **[VIA: AGENT → Fonte]**
> "Citacao que embasa esta responsabilidade"

### Secundarias ([%] do tempo)

[Mesmo formato]

### NAO E SUA RESPONSABILIDADE

| Atividade | Responsavel | Fonte |
|-----------|-------------|-------|
| [O que] | [Quem faz] | [FONTE] |

---

## 3. LINHAS DE COMUNICACAO

### Report Obrigatorio

| Para Quem | O Que | Quando | Canal | Fonte |
|-----------|-------|--------|-------|-------|

### Escalar Imediatamente

| Situacao | Para Quem | Prazo | Fonte |
|----------|-----------|-------|-------|

### Decidir Sozinho

| Situacao | Limite | Registro | Fonte |
|----------|--------|----------|-------|

### Consultar Antes de Agir

| Situacao | Consultar | Canal | Fonte |
|----------|-----------|-------|-------|

---

## 4. FRAMEWORKS OPERACIONAIS

### [Nome do Framework]

> **[VIA: AGENT → Fonte CODIGO]**

```
[ASCII diagram ou tabela do framework]
```

**APLICACAO [SUA EMPRESA]:**
[Como aplicar especificamente na [SUA EMPRESA]]

---

## 5. FERRAMENTAS OBRIGATORIAS

| Ferramenta | Uso | Frequencia | Dono |
|------------|-----|------------|------|

---

## 6. METRICAS DE SUCESSO

| KPI | Meta | Frequencia | Peso | Fonte |
|-----|------|------------|------|-------|

---

## 7. EXEMPLOS PRATICOS

### Cenario N: [Titulo descritivo]

> **[FONTE que embasa este cenario]**
> "Citacao se houver"

```
❌ ERRADO: "[Acao incorreta]"
   → Por que: [Explicacao com fonte]

✅ CERTO:
   1. [Passo 1]
   2. [Passo 2]
   → Resultado: [O que acontece]
   → Registro: [Onde documentar]
```

---

## 8. ARMADILHAS

| Armadilha | Por que e ruim | Como evitar | Fonte |
|-----------|----------------|-------------|-------|

---

## 9. GATILHOS DE MUDANCA

> Ver: [SCALING-TRIGGERS.md](path) para detalhes completos

| Gatilho | Acao | Quando | Fonte |
|---------|------|--------|-------|

---

## 10. FONTES UTILIZADAS NESTE ROLE

### Agentes IA que alimentam

| AGENT | Conhecimento Herdado | Localizacao |
|-------|---------------------|-------------|

### Fontes Externas Citadas

| Codigo | Fonte | Contribuicao Principal |
|--------|-------|------------------------|

### Decisoes [SUA EMPRESA]

| Decisao | Descricao | Data |
|---------|-----------|------|

---

## TEAM AGREEMENT

- [ ] Li e entendi todas as responsabilidades
- [ ] Sei quando escalar vs decidir sozinho
- [ ] Tenho acesso a todas as ferramentas
- [ ] Conheco minhas metricas de sucesso
- [ ] Entendo os gatilhos de mudanca

**Assinatura:** _________________ **Data:** _________

---

*ROLE-[CARGO] v[X.X.X]*
*Sistema ORG-LIVE*
*Alimentado por: ORG-PROTOCOL.md*
```

---

### 2. JD-*.md (Job Descriptions)

```markdown
# JOB DESCRIPTION: [CARGO]

> **Empresa:** [SUA EMPRESA]
> **Tipo de Cargo:** EXECUTIVO | OPERACIONAL | ESPECIALISTA
> **Reporta a:** [Cargo]
> **Criado:** YYYY-MM-DD
> **Framework Base:** [Ex: Founder First Hiring (Richard Linder)]

---

## HEADER VISUAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           [CARGO] - [SUA EMPRESA]                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  MISSAO: [Uma linha que resume o proposito]                                  │
│                                                                             │
│  REPORTA A: [Cargo]          │  SUBORDINADOS: [Quem/Quantos]               │
│  TIPO: [Executivo/Op/Esp]    │  STATUS: [Aberto/Planejado]                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## VISAO GERAL

### Sobre a Vaga

[Descricao 2-3 paragrafos com citacoes de fonte]

> **[FONTE: X - CODIGO]**
> "Citacao que embasa a existencia desta vaga"

### Por que Esta Vaga Existe

| # | Motivo | Fonte |
|---|--------|-------|
| 1 | [Motivo] | [FONTE] |

---

## RESPONSABILIDADES PRINCIPAIS

### 1. [Area] ([%])

| Atividade | Entregavel | Frequencia | Fonte |
|-----------|------------|------------|-------|

> **[VIA: AGENT → Fonte]**
> "Citacao que embasa"

[Repetir para cada area]

---

## METRICAS DE SUCESSO

| Metrica | Target | Peso | Frequencia | Fonte |
|---------|--------|------|------------|-------|

---

## REQUISITOS TECNICOS (Competencia)

### Obrigatorios

| # | Requisito | Como Validar | Fonte |
|---|-----------|--------------|-------|
| 1 | [Requisito] | [Pergunta/Teste] | [FONTE] |

### Desejaveis

| # | Requisito | Diferencial | Fonte |
|---|-----------|-------------|-------|

### Red Flags Tecnicos

| # | Red Flag | Por que | Fonte |
|---|----------|---------|-------|

---

## PERFIL COMPORTAMENTAL (Compatibilidade)

### DISC Ideal

| Perfil | Nivel | Justificativa | Fonte |
|--------|-------|---------------|-------|

> **[FONTE: Richard Linder - RL001]**
> "Competency plus compatibility. Not just one. Both."

### Working Genius Ideal

| Categoria | Tipo | Justificativa |
|-----------|------|---------------|
| **Genius** | [X, Y] | [Por que] |
| **Competency** | [X, Y] | [Por que] |
| **Frustration** | [X] | [Por que OK] |

---

## TRUST TRAITS CRITICOS

### Trust-Building (Avaliar em Entrevista)

| Trait | Peso | Pergunta Scenario-Based | Resposta Ideal | Fonte |
|-------|------|-------------------------|----------------|-------|

> **[FONTE: Richard Linder - RL001]**
> "Citacao sobre trust traits"

### Trust-Breaking (Red Flags)

| Trait | Red Flag | Como Identificar | Consequencia | Fonte |
|-------|----------|------------------|--------------|-------|

---

## PERGUNTAS DE ENTREVISTA

### NON-NEGOTIABLES (Eliminatorias)

| # | Categoria | Pergunta | Criterio Pass/Fail | Fonte |
|---|-----------|----------|-------------------|-------|

### ESSENTIAL TO ROLE

| # | Competencia | Pergunta | O que Avaliar | Fonte |
|---|-------------|----------|---------------|-------|

### CORE COMPETENCIES

| # | Trait | Pergunta | Resposta Ideal | Fonte |
|---|-------|----------|----------------|-------|

---

## SCORING CRITERIA

### Scorecard Structure

| Categoria | Peso | Minimum Score | Fonte |
|-----------|------|---------------|-------|

### Regras de Avaliacao

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          HELL YES OR NO                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ⛔ SEM NOTAS 7 (7 = 6 otimista ou 8 pessimista)                           │
│                                                                             │
│  ✅ Score Total minimo: 8.0/10                                              │
│                                                                             │
│  ⛔ Qualquer Trust-Breaking trait identificado = ELIMINADO                  │
│                                                                             │
│  ✅ Todos os Non-Negotiables devem ser PASS                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

> **[FONTE: Richard Linder - RL001]**
> "There is no seven. Sevens are total BS."
```

---

## COMPENSACAO

| Componente | Range/Estrutura | Notas |
|------------|-----------------|-------|

---

## PROCESSO SELETIVO

```
ETAPA 1: [Nome] ([Duracao])
└── [O que avaliar]
    └── [Quem conduz]

ETAPA 2: [Nome] ([Duracao])
└── [O que avaliar]
    └── [Quem conduz]

[...]

ETAPA FINAL: [Nome] ([Duracao])
└── [O que avaliar]
    └── DECISAO: Hell Yes or No
```

---

## FONTES UTILIZADAS NESTE JD

| Codigo | Fonte | Contribuicao |
|--------|-------|--------------|

---

*JD-[CARGO] v[X.X.X]*
*Framework: [Nome do Framework base]*
*Sistema ORG-LIVE*
```

---

### 3. ORG-*.md (Documentos Organizacionais)

```markdown
# [TITULO]: [Subtitulo Descritivo]

> **Versao:** X.X.X | **Atualizado:** YYYY-MM-DD
> **Estagio Atual:** [INICIAL | CRESCIMENTO | ESCALA]
> **Ecossistema:** [SUA EMPRESA]

---

## HEADER VISUAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    [TITULO EM CAIXA ALTA]                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Descricao de uma linha do proposito deste documento]                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FILOSOFIA

> **[FONTE: X - CODIGO]**
> "Citacao que embasa a filosofia"

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRINCIPIO FUNDAMENTAL                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [Principio em destaque visual]                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## [SECAO PRINCIPAL DO DOCUMENTO]

[Conteudo com citacoes obrigatorias]

> **[VIA: AGENT → Fonte]** ou **[FONTE: X - CODIGO]**
> "Citacao que embasa"

### Subsecao

| [Header] | [Header] | [Header] | Fonte |
|----------|----------|----------|-------|

---

## DECISOES [SUA EMPRESA]

| Decisao | Valor/Politica | Justificativa | Data |
|---------|----------------|---------------|------|

---

## FONTES UTILIZADAS

| Codigo | Fonte | Contribuicao |
|--------|-------|--------------|

---

## HISTORICO DE MUDANCAS

| Data | Versao | Mudanca | Motivo |
|------|--------|---------|--------|

---

*[TITULO] v[X.X.X]*
*Sistema ORG-LIVE*
```

---

## Padroes Visuais Obrigatorios

### 1. ASCII Diagrams

```
ORGANOGRAMAS:
┌─────────────┐
│    CARGO    │
└──────┬──────┘
       │
┌──────▼──────┐
│    CARGO    │
└─────────────┘

FLUXOS:
[INPUT] ──► [PROCESSO] ──► [OUTPUT]

CAIXAS DE DESTAQUE:
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TITULO DA CAIXA                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Conteudo importante                                                        │
└─────────────────────────────────────────────────────────────────────────────┘

SIMBOLOS:
⛔ Proibido/Erro
✅ Correto/Aprovado
⚠️ Atencao/Cuidado
► Fluxo/Direcao
★ Destaque especial
```

### 2. Tabelas

SEMPRE incluir coluna "Fonte" em tabelas com informacoes factuais:

```markdown
| Dado | Valor | Fonte |
|------|-------|-------|
| [X]  | [Y]   | [FONTE/VIA] |
```

### 3. Citacoes

```markdown
> **[VIA: AGENT-X → Fonte CODIGO]**
> "Citacao exata preservada"

**APLICACAO [SUA EMPRESA]:**
[Como isso se aplica especificamente]
```

### 4. Exemplos Praticos

```markdown
### Cenario: [Titulo]

> **[FONTE que embasa]**

```
❌ ERRADO: "[Acao]"
   → Por que: [Explicacao]

✅ CERTO:
   1. [Passo]
   2. [Passo]
   → Resultado: [O que acontece]
```
```

---

## Regras de Linguagem

### Tom

| Aspecto | Padrao | Exemplo |
|---------|--------|---------|
| **Voz** | Terceira pessoa, prescritiva | "O Closer DEVE..." nao "Voce deve..." |
| **Tempo** | Presente do indicativo | "Reporta a..." nao "Reportara..." |
| **Idioma** | Portugues BR | Exceto termos tecnicos consagrados em ingles |
| **Numeros** | Exatos quando fonte tem | "25%", nao "cerca de 25%" |
| **Afirmacoes** | Assertivas com fonte | Nunca "geralmente", "provavelmente" |

### Proibicoes

```
⛔ NUNCA USAR:
- "Provavelmente"
- "Talvez"
- "Geralmente"
- "Na maioria das vezes"
- "Aproximadamente" (quando fonte tem numero exato)
- Opiniao sem marcador [DECISAO [SUA EMPRESA]]
- Informacao sem fonte
```

### Termos Preservados em Ingles

| Termo | Por que manter |
|-------|----------------|
| Close Rate | Termo tecnico de vendas |
| QC (Quality Control) | Acronimo consagrado |
| Overhead/Override | Termos de comp |
| Pipeline | Termo de vendas |
| ICP | Ideal Customer Profile |
| Framework | Termo tecnico |
| Trust Traits | Conceito do Richard Linder |
| DISC | Assessment |
| Working Genius | Assessment |

---

## Checklist de Qualidade

Antes de finalizar qualquer documento ORG-LIVE:

```
□ RASTREABILIDADE
  □ Toda informacao factual tem [FONTE], [VIA] ou [DECISAO [SUA EMPRESA]]?
  □ Nenhuma afirmacao sem origem?
  □ Numeros exatos preservados?

□ ESTRUTURA
  □ Segue template do tipo de documento?
  □ Headers visuais presentes?
  □ ASCII diagrams onde necessario?
  □ Tabelas com coluna "Fonte"?

□ LINGUAGEM
  □ Terceira pessoa prescritiva?
  □ Presente do indicativo?
  □ Sem termos vagos (provavelmente, talvez)?
  □ Termos tecnicos em ingles preservados?

□ EXEMPLOS
  □ Cenarios praticos incluidos?
  □ Formato ❌ ERRADO / ✅ CERTO?
  □ Passos claros e acionaveis?

□ METADADOS
  □ Versao atualizada?
  □ Data de atualizacao correta?
  □ Fontes listadas no final?
  □ Conexao com Agents declarada (se ROLE)?
```

---

## Safeguards Obrigatorios

| Regra | Implementacao |
|-------|---------------|
| **Nunca inventar** | Toda info rastreavel a fonte |
| **Preservar numeros** | Metricas exatas sao intocaveis |
| **Versionar** | Incrementar versao a cada mudanca |
| **Historico** | Manter registro de mudancas |
| **Validacao** | Checklist antes de finalizar |

---

## Integracao com Pipeline Jarvis

Este protocolo e executado na fase:

| Fase | Aplicacao |
|------|-----------|
| **8.1.6** | ORG-LIVE Enrichment - Alimentar ROLEs via AGENTs |
| **Manual** | Criacao/atualizacao de JDs e documentos ORG |

---

## Exemplos de Aplicacao Correta

### Exemplo 1: Responsabilidade com Fonte

```markdown
### Primarias (70% do tempo)

| Atividade | Frequencia | Metrica | Fonte |
|-----------|------------|---------|-------|
| QC de calls do time | Diario | 2-3 calls/dia | [CG003] |

> **[VIA: AGENT-SALES-MANAGER → Cole Gordon CG003]**
> "Majority of their job is QC. Not messing with CRM, not redoing the script,
> not doing a fun project, not trying to get significance. Q-C."
```

### Exemplo 2: Decisao [SUA EMPRESA]

```markdown
### Decidir Sozinho

| Situacao | Limite | Registro | Fonte |
|----------|--------|----------|-------|
| Desconto ate 10% | R$5k max | CRM + Slack | [DECISAO [SUA EMPRESA]] |
```

### Exemplo 3: Cenario Pratico

```markdown
### Cenario 1: Lead pede 20% de desconto

> **[FONTE: Richard Linder - RL001]**
> "Descontos significativos devem passar pelo founder para manter
> integridade de pricing."

```
❌ ERRADO: "Vou aprovar pra nao perder a venda"
   → Por que: Quebra integridade de pricing, cria precedente

✅ CERTO:
   1. "Preciso consultar meu diretor. Volto em 2h."
   2. Escalar para FOUNDER via WhatsApp
   3. Aguardar aprovacao
   4. Registrar no CRM motivo do desconto
   → Resultado: Pricing protegido, decisao documentada
```
```

---

*ORG-LIVE-DOCUMENT-PROTOCOL v1.0*
*Principio: Nenhuma informacao sem fonte. Nenhuma decisao sem responsavel.*
*Sistema ORG-LIVE*
