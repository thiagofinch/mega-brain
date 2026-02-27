---
name: ask-[sua-empresa]
description: "Consulta o contexto completo da [SUA EMPRESA] para responder perguntas. Injeta automaticamente métricas, organograma, processos, estratégia. Use quando: perguntas sobre a empresa, decisões estratégicas, contexto de negócio."
---

# Ask [SUA EMPRESA] - Consulta Contextualizada

Responde perguntas sobre a [SUA EMPRESA] com contexto completo injetado automaticamente.

---

## Quando Usar

- Perguntas sobre a empresa [SUA EMPRESA]
- Decisões estratégicas que precisam de contexto
- Consultas sobre métricas, time, processos
- Geração de playbooks, SOPs, documentos internos

---

## O Que Faz

1. **Recebe** pergunta do usuário
2. **Carrega** contexto [SUA EMPRESA] relevante
3. **Injeta** métricas, organograma, processos
4. **Responde** com dados reais da empresa
5. **Cita** fontes dos dados (`^[[SUA EMPRESA]:arquivo:linha]`)

---

## Fontes de Contexto

```yaml
contexto_obrigatorio:
  - /[sua-empresa]/[SUA EMPRESA]-CONTEXT.md           # Contexto master
  - /[sua-empresa]/team/ORGANOGRAM.yaml     # Estrutura organizacional
  - /[sua-empresa]/07-STRATEGY/PROCESS-MAP.md  # Processos mapeados

contexto_financeiro:
  - /[sua-empresa]/02-FINANCE/DAILY-SNAPSHOT.yaml  # Métricas atuais (se existir)
  - Google Drive: ${GDRIVE_SHEET_ID}  # KPIs Master

contexto_estrategico:
  - /[sua-empresa]/07-STRATEGY/INSIGHTS-PROCESS-AUDITOR.md
  - /[sua-empresa]/07-STRATEGY/BUSINESS-MODEL.md (se existir)
  - /[sua-empresa]/07-STRATEGY/FLYWHEEL.md (se existir)

contexto_time:
  - /[sua-empresa]/team/SOW/*.md (se existir)
  - /[sua-empresa]/team/HIRING-STRUCTURE.md
```

---

## Fluxo de Execução

```
┌────────────────────────────────────────────────────────────────────────────┐
│  PASSO 1: CLASSIFICAR PERGUNTA                                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TIPOS:                                                                     │
│  - FINANCIAL: "qual o MRR?", "custos fixos?", "runway?"                    │
│  - TEAM: "quem é responsável por X?", "organograma?"                       │
│  - PROCESS: "como funciona o processo de Y?", "SOP de Z?"                  │
│  - STRATEGY: "qual a estratégia de?", "flywheel?", "roadmap?"              │
│  - PRODUCT: "quais produtos temos?", "preço de X?"                         │
│  - GENERAL: perguntas gerais sobre a empresa                                │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  PASSO 2: CARREGAR CONTEXTO                                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SEMPRE CARREGAR:                                                           │
│  - [SUA EMPRESA]-CONTEXT.md (contexto master)                                     │
│  - ORGANOGRAM.yaml (quem faz o quê)                                        │
│                                                                             │
│  CARREGAR SE TIPO = FINANCIAL:                                             │
│  - Consultar Google Drive (KPIs Master, DRE)                               │
│  - Carregar DAILY-SNAPSHOT.yaml se existir                                 │
│                                                                             │
│  CARREGAR SE TIPO = PROCESS:                                               │
│  - PROCESS-MAP.md                                                          │
│  - SOWs relevantes                                                         │
│                                                                             │
│  CARREGAR SE TIPO = STRATEGY:                                              │
│  - INSIGHTS-PROCESS-AUDITOR.md                                               │
│  - BUSINESS-MODEL.md                                                       │
│  - FLYWHEEL.md                                                             │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  PASSO 3: RESPONDER COM CONTEXTO                                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FORMATO DA RESPOSTA:                                                       │
│                                                                             │
│  [Resposta direta à pergunta]                                               │
│                                                                             │
│  **Contexto [SUA EMPRESA]:**                                                       │
│  - Dado relevante 1 ^[[SUA EMPRESA]:arquivo1:linha]                               │
│  - Dado relevante 2 ^[[SUA EMPRESA]:arquivo2:linha]                               │
│                                                                             │
│  **Métricas atuais:** (se FINANCIAL)                                       │
│  - MRR: R$ X ^[[SUA EMPRESA]:KPIs-Master]                                         │
│  - Custos fixos: R$ Y ^[[SUA EMPRESA]:[SUA EMPRESA]-CONTEXT.md:45]                       │
│                                                                             │
│  **Responsável:** (se TEAM)                                                 │
│  - [Pessoa] - [Cargo] ^[[SUA EMPRESA]:ORGANOGRAM.yaml:23]                         │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Exemplos de Uso

### Pergunta Financeira
```
/ask-[sua-empresa] Qual nosso MRR atual e runway?

RESPOSTA:
Baseado nos dados mais recentes da [SUA EMPRESA]:

**MRR [Produto]:** R$ XXXk ^[[SUA EMPRESA]:[SUA EMPRESA]-CONTEXT.md:financeiro]
**Custos Fixos:** ~R$ XXXk/mês ^[[SUA EMPRESA]:[SUA EMPRESA]-CONTEXT.md:custos]
**Projeção Saldo:** R$ X.XM ^[[SUA EMPRESA]:[SUA EMPRESA]-CONTEXT.md:projecao]

Para runway exato, consultei a planilha KPIs Master...
[dados do Google Drive se disponíveis]
```

### Pergunta de Time
```
/ask-[sua-empresa] Quem é responsável por operações?

RESPOSTA:
**Head de Operações:** [Head Ops] (RS001)
- Reports to: CEO
- OTD Target: 95%+
- Áreas sob responsabilidade: Logística, Processos, Qualidade
^[[SUA EMPRESA]:ORGANOGRAM.yaml:head_ops]
```

### Pergunta de Processo
```
/ask-[sua-empresa] Como funciona o processo de contratação?

RESPOSTA:
O processo de contratação da [SUA EMPRESA] segue 6 etapas:

1. **Abertura de Vaga** (HUMANO)
   - Input: Necessidade identificada
   - Output: Job Description aprovado
   - Responsável: Head da área
   ^[[SUA EMPRESA]:PROCESS-MAP.md:hiring_step1]

2. **Triagem** (AGENT IA)
   - Input: Currículos recebidos
   - Output: Shortlist 5-10 candidatos
   - Quality Gate: Score mínimo 70/100
   ^[[SUA EMPRESA]:PROCESS-MAP.md:hiring_step2]

[continua...]
```

---

## Regras

1. **SEMPRE** carregar [SUA EMPRESA]-CONTEXT.md antes de responder
2. **SEMPRE** citar fontes com formato `^[[SUA EMPRESA]:arquivo:seção]`
3. **NUNCA** inventar dados - se não souber, dizer explicitamente
4. **SE** dados estiverem desatualizados, alertar o usuário
5. **PRIORIZAR** dados de planilhas Google Drive quando disponíveis

---

## Checklist [SUA EMPRESA] (Verificar Antes de Recomendações)

```
[ ] Contexto [SUA EMPRESA] consultado?
[ ] Métricas atuais consideradas?
[ ] Impacto no objetivo [META FINANCEIRA] calculado?
[ ] Recursos disponíveis verificados?
[ ] Time atual pode executar?
[ ] Alinhado com flywheel?
```

---

**Versão:** 1.0.0
**Última atualização:** 2026-01-11
