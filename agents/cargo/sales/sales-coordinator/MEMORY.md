# MEMORY: SALES-COORDINATOR (Coordenador de Vendas)

> **Versao:** 3.0.0
> **Template:** MEMORY-V2 (100% rastreabilidade)
> **Criada:** 2024-12-15
> **Ultima atualizacao:** 2026-01-11
> **Total de insights:** 48
> **DNA Primario:** Cole Gordon (45%) (30%), TSC (25%)

---

## INDICE

1. [Metadados de Contexto](#metadados-de-contexto)
2. [Insights por Fonte](#insights-por-fonte)
3. [Batch Insights](#batch-insights)
4. [Frameworks Operacionais](#frameworks-operacionais)
5. [Padroes Decisorios](#padroes-decisorios)
6. [Calibracao Brasil](#calibracao-brasil)
7. [Casos e Precedentes](#casos-e-precedentes)
8. [Limitacoes Conhecidas](#limitacoes-conhecidas)
9. [Knowledge Base Locations](#knowledge-base-locations)
10. [Historico de Atualizacoes](#historico-de-atualizacoes)

---

## METADADOS DE CONTEXTO

### Projeto Atual

| Campo | Valor |
|-------|-------|
| **Empresa** | [A definir] |
| **Produto** | High-ticket B2B |
| **Ticket** | [A definir - R$10k+] |
| **Pais** | Brasil |
| **Fase** | [A definir] |

### Particularidades Culturais (Brasil)

- Organizacao administrativa e critica para escalar
- CRM compliance pode ser desafio cultural
- Relatorios em portugues obrigatorio
- Comunicacao via WhatsApp/Slack (nao email)
- Speed to lead ainda mais critico (WhatsApp expectations)

---

## INSIGHTS POR FONTE

### Cole Gordon (45%) ^[DNA-CONFIG.yaml:16-27]

#### CG001: Sales Management Progression

| ID | Insight | Aplicabilidade | Confianca |
|----|---------|----------------|-----------|
| CG-PHASE001 | Admin pode ir pra assistente desde Fase 1 ^[insight_id:CG-PHASE001] | Timing de contratacao | ALTA |
| CG-PHASE002 | Coordinator permanece da Fase 2 em diante ^[insight_id:CG-PHASE001] | Minha permanencia | ALTA |
| CG-PHASE003 | Liberar founder/Sales Lead para coaching ^[insight_id:CG-PHASE001] | Meu valor core | ALTA |
| CG-CRM002 | Dashboard accuracy e critico ^[insight_id:CG-CRM001] | Prioridade diaria | ALTA |

#### CG002: 7 Ways to Increase Show Rates

| ID | Insight | Aplicabilidade | Confianca |
|----|---------|----------------|-----------|
| CG-GRADE001 | Application Grading 1-4 ^[insight_id:CG-GRADE001] | Sistema de qualificacao | ALTA |
| CG-GRADE002 | Grade 4 vai pro melhor rep ^[insight_id:CG-GRADE001] | Atribuicao por skill | ALTA |
| CG-ATTR001 | Lead attribution justa (round robin base) ^[insight_id:CG-ATTR001] | Distribuicao equitativa | ALTA |
| CG-ATTR002 | Skill-based para leads especificos ^[insight_id:CG-ATTR001] | Enterprise, nicho | MEDIA |
| CG-SPEED001 | Speed to lead < 5 minutos ^[insight_id:CG-SPEED001] | Atribuicao rapida | ALTA |
| CG-CRM001 | CRM sujo = vendas perdidas ^[insight_id:CG-CRM001] | Higiene obsessiva | ALTA |


| ID | Insight | Aplicabilidade | Confianca |
|----|---------|----------------|-----------|

### The Scalable Company (25%) ^[BATCH-088, BATCH-090]

#### TSC001: Scorecards e Accountability

| ID | Insight | Aplicabilidade | Confianca |
|----|---------|----------------|-----------|
| TSC-SCORE001 | 3-5 metricas max por time no scorecard ^[insight_id:TSC-SCORE001] | Foco em metricas | ALTA |
| TSC-SCORE002 | Beach Vacation Question para selecao ^[insight_id:TSC-SCORE002] | Priorizacao | ALTA |
| TSC-CAB001 | CABs: accountability vem do Value Engine ^[insight_id:TSC-CAB001] | Bottom-up | ALTA |
| TSC-MEET001 | Meeting Rhythm: QSP > MBR > Weekly ^[insight_id:TSC-MEET001] | Cadencia | ALTA |
| TSC-TL001 | Traffic Light: Red > Yellow > Green ^[insight_id:TSC-TL001] | Status visual | ALTA |

---

## BATCH INSIGHTS

### Fontes Processadas: BATCH-050 a BATCH-067 (Cole Gordon), BATCH-085 a BATCH-110 (/TSC)

### Pipeline Management

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  INSIGHTS DE PIPELINE MANAGEMENT                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [BATCH-050] METODO PTMA - GESTAO DE TIMES:                                 │
│  ├── P = PLANEJAR: Metas diarias/semanais/mensais                           │
│  ├── T = TREINAR: 87% comportamental, 13% tecnico                           │
│  ├── M = MOTIVAR: Reconhecimento, acompanhamento proximo                    │
│  └── A = ACOMPANHAR/COBRAR: Feedback, metricas, ajustes                     │
│                                                                              │
│  [BATCH-051] CALENDAR STRUCTURE (Daily):                                    │
│  ├── 07:30-08:30: OUTBOUND CALLS (20-30 dials)                              │
│  ├── 08:30-09:30: EMAILS/TEXTS (follow-up)                                  │
│  ├── 09:30-11:30: OUTBOUND CALLS (20 dials)                                 │
│  ├── 12:00-01:30: ADMIN/RESEARCH                                            │
│  ├── 01:30-04:00: INBOUND CALLS (mais faceis)                               │
│  ├── 06:00-07:00: RESEARCH (proximo dia)                                    │
│  └── 09:00-10:00: PLANEJAMENTO PROXIMO DIA                                  │
│                                                                              │
│  [BATCH-088] SCORECARD BUILDING (3 Steps):                                  │
│  ├── Step 1: Identificar categorias do High Output Team Canvas              │
│  ├── Step 2: Brainstorm metricas com Beach Vacation Question                │
│  └── Step 3: Backtest mes/trimestre anterior para validar                   │
│                                                                              │
│  [BATCH-090] MEETING RHYTHM ARCHITECTURE:                                   │
│  ├── QSP (Quarterly): Planejamento estrategico                              │
│  ├── MBR (Monthly): Revisao mensal de metricas                              │
│  ├── Weekly: Pipeline review, cases, objecoes                               │
│  └── One-on-ones: Desenvolvimento individual                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### CRM Workflows

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  INSIGHTS DE CRM WORKFLOWS                                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [BATCH-050] CRM HYGIENE PROTOCOL:                                          │
│  ├── CHECK DIARIO (obrigatorio):                                            │
│  │   ├── Leads sem dono → Atribuir imediatamente                            │
│  │   ├── Deals estagnados > 7 dias → Alertar rep                            │
│  │   ├── Dados inconsistentes → Corrigir                                    │
│  │   └── Duplicatas → Mesclar                                               │
│  ├── CHECK SEMANAL (sexta-feira):                                           │
│  │   ├── Relatorios para gestao prontos                                     │
│  │   ├── Tendencias de pipeline identificadas                               │
│  │   └── Gargalos documentados                                              │
│  └── CHECK MENSAL (ultimo dia util):                                        │
│      ├── Revisao completa de processos                                      │
│      ├── Automacoes funcionando                                             │
│      └── Documentacao atualizada                                            │
│                                                                              │
│  [BATCH-088] BACKTESTING METHODOLOGY:                                       │
│  ├── Propor metrica → Backtest 1 mes → Validar disponibilidade             │
│  ├── Se falhar: construir tracking OU escolher metrica diferente            │
│  └── Principio: Se nao consegue medir historicamente, nao consegue medir    │
│                                                                              │
│  [BATCH-105] PACING DE META:                                                │
│  ├── Dia 15 do mes = ter 50% da meta                                        │
│  ├── Abaixo de 50% = intensificar                                           │
│  └── Acima de 50% = folga para superar                                      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Team Coordination

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  INSIGHTS DE TEAM COORDINATION                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [BATCH-050] 4 TIPOS DE VENDEDORES (DISC):                                  │
│  ├── D - EXECUTOR/DOMINANTE:                                                │
│  │   ├── Funciona na raiva, desafie, massage ego                            │
│  │   └── Treinar: competicao, autonomia, metas agressivas                   │
│  ├── I - INFLUENTE:                                                         │
│  │   ├── Alto e baixo, exige manutencao constante                           │
│  │   └── Treinar: reconhecimento, curto, divertido                          │
│  ├── S - ESTAVEL:                                                           │
│  │   ├── Demora no tranco mas consistente, fica anos                        │
│  │   └── Treinar: passo-a-passo, metodo, manual                             │
│  └── C - SISTEMATICO/ANALITICO:                                             │
│      ├── Precisa entender o PORQUE                                          │
│      └── Treinar: fundamento, detalhes, individual                          │
│                                                                              │
│  [BATCH-050] CRONOGRAMA 8 SEMANAS - VENDEDOR NOVO:                          │
│  ├── S1: ONBOARD → Cultura, empresa, organizacao                            │
│  ├── S2: TECNICO → Produto, informacoes, manual                             │
│  ├── S3: COMPORTAMENTAL → Mindset, inteligencia emocional                   │
│  ├── S4: CAMPO → Observar veterano, shadow                                  │
│  ├── S5: LABORATORIO → Simulacoes                                           │
│  ├── S6-8: AJUSTES → Feedback continuo, refinamento                         │
│  └── MENSAL: 87% desenvolvimento + 13% especializacao                       │
│                                                                              │
│  [BATCH-090] TRAFFIC LIGHT LEADERSHIP SYSTEM:                               │
│  ├── RED: Problema critico, precisa atencao imediata                        │
│  ├── YELLOW: Em risco, monitorar de perto                                   │
│  └── GREEN: No caminho certo, manter                                        │
│                                                                              │
│  [BATCH-105] 4 RITUAIS DE VENDAS:                                           │
│  ├── DAILY: 10-15 min                                                       │
│  │   ├── Mensagens positivas                                                │
│  │   ├── Como foi ontem / como sera hoje                                    │
│  │   └── Como um pode ajudar o outro                                        │
│  ├── WEEKLY PIPELINE: 30min-1h                                              │
│  │   ├── Revisao de oportunidades (CRM-based)                               │
│  │   ├── Cases e objecoes compartilhados                                    │
│  │   └── Negocios proximos de fechar                                        │
│  ├── MONTHLY/QUARTERLY: 1-2h                                                │
│  │   ├── Revisao de numeros e metas                                         │
│  │   ├── Tendencias e estrategias                                           │
│  │   └── Novos produtos/servicos                                            │
│  └── ONE-ON-ONE: 20-30 min/semana                                           │
│      ├── Performance individual                                             │
│      ├── Dificuldades e desenvolvimento                                     │
│      └── Carreira e proximos passos                                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Reporting Frameworks

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  INSIGHTS DE REPORTING FRAMEWORKS                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [BATCH-088] BEACH VACATION QUESTION (Selecao de Metricas):                 │
│  ├── "Voce esta na praia, so com celular. Quais 3-5 numeros quer ver?"      │
│  ├── Forca priorizacao para metricas CRITICAS                               │
│  ├── Elimina vanity metrics                                                 │
│  └── Constraints: max 3-5 por time, checar rapido                           │
│                                                                              │
│  [BATCH-088] SCORECARD ARCHITECTURE:                                        │
│  ├── Company Scorecard: 5-7 categorias max                                  │
│  ├── Team Scorecard: 3-5 metricas por time                                  │
│  └── Individual: KPIs pessoais alinhados ao time                            │
│                                                                              │
│  [BATCH-088] MIND METHODOLOGY (Most Important Number):                      │
│  ├── Definir MIN (geralmente PROFIT)                                        │
│  ├── Identificar 3-5 drivers principais                                     │
│  └── Construir scorecard em torno dos drivers                               │
│                                                                              │
│  [BATCH-105] OTE (On Target Earnings):                                      │
│  ├── Modelo tradicional: % de vendas (problema: ganha por mare)             │
│  ├── Modelo OTE: valor fixo por 100% meta                                   │
│  ├── Beneficio: premia esforco real + metas progressivas                    │
│  └── Principio: quanto mais tempo, mais facil vender                        │
│                                                                              │
│  [BATCH-105] NPS (Net Promoter Score):                                      │
│  ├── 9-10 = Promotor (+)                                                    │
│  ├── 7-8 = Neutro (0)                                                       │
│  ├── 0-6 = Detrator (-)                                                     │
│  ├── Calculo: NPS = % Promotores - % Detratores                             │
│  └── Reference: iPhone NPS > 80, Software medio ~25                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## FRAMEWORKS OPERACIONAIS

### Framework 1: Application Grading System ^[insight_id:CG-GRADE001]

**Fonte:** Cole Gordon - 7 Ways to Increase Show Rates

```
┌─────────────────────────────────────────────────────────────────┐
│                 APPLICATION GRADING SYSTEM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GRADE 4: Altamente qualificado                                 │
│  ├── Caracteristicas: Fit perfeito, urgencia, budget            │
│  ├── Acao: Atribuir IMEDIATAMENTE ao melhor rep                 │
│  └── Prioridade: MAXIMA                                         │
│                                                                 │
│  GRADE 3: Qualificado                                           │
│  ├── Caracteristicas: Bom fit, interesse demonstrado            │
│  ├── Acao: Atribuir para BDR/SDS via round robin                │
│  └── Prioridade: NORMAL                                         │
│                                                                 │
│  GRADE 2: Parcialmente qualificado                              │
│  ├── Caracteristicas: Fit incerto, falta informacao             │
│  ├── Acao: Flag para revisao do Sales Lead                      │
│  └── Prioridade: BAIXA (requer decisao)                         │
│                                                                 │
│  GRADE 1: Nao qualificado                                       │
│  ├── Caracteristicas: Nao e fit, sem budget, curioso            │
│  ├── Acao: Rejeitar educadamente                                │
│  └── Prioridade: NENHUMA (nao entra no pipeline)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**O que isso significa na pratica:** Quando um lead chega, minha primeira
tarefa e classificar de 1 a 4. Grade 4 e ouro - vai direto pro closer mais
experiente. Grade 1 nem entra no sistema. O grading correto protege o tempo
dos vendedores e aumenta conversao porque cada rep recebe leads adequados.

### Framework 2: Lead Attribution Strategy ^[insight_id:CG-ATTR001]

**Fonte:** Cole Gordon - 7 Ways to Increase Show Rates

```
┌─────────────────────────────────────────────────────────────────┐
│               LEAD ATTRIBUTION STRATEGY                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  REGRA 1: ROUND ROBIN (Padrao)                                  │
│  └── Distribuicao sequencial entre reps disponiveis             │
│  └── Garante fairness e oportunidade igual                      │
│                                                                 │
│  REGRA 2: SKILL-BASED (Excecao)                                 │
│  └── Lead enterprise → Rep com experiencia enterprise           │
│  └── Lead tecnico → Rep com background tecnico                  │
│  └── Lead nicho especifico → Rep especialista                   │
│                                                                 │
│  REGRA 3: TERRITORIO (Se aplicavel)                             │
│  └── Lead regiao X → Rep responsavel por X                      │
│  └── Fuso horario considerado                                   │
│                                                                 │
│  REGRA 4: CAPACIDADE (Limite)                                   │
│  └── Rep no limite → Pula para proximo                          │
│  └── Ninguem recebe mais do que aguenta                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Aplicacao:** Round robin como base garante que todos tenham oportunidade.
Ajustes por skill apenas quando justificado. Capacidade como limite duro.

### Framework 3: CRM Hygiene Protocol ^[insight_id:CG-CRM001]

**Fonte:** Cole Gordon - Sales Management Progression

```
┌─────────────────────────────────────────────────────────────────┐
│                   CRM HYGIENE PROTOCOL                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CHECK DIARIO (obrigatorio):                                    │
│  ├── Leads sem dono → Atribuir imediatamente                    │
│  ├── Deals estagnados > 7 dias → Alertar rep                    │
│  ├── Dados inconsistentes → Corrigir                            │
│  └── Duplicatas → Mesclar                                       │
│                                                                 │
│  CHECK SEMANAL (sexta-feira):                                   │
│  ├── Relatorios para gestao prontos                             │
│  ├── Tendencias de pipeline identificadas                       │
│  └── Gargalos documentados                                      │
│                                                                 │
│  CHECK MENSAL (ultimo dia util):                                │
│  ├── Revisao completa de processos                              │
│  ├── Automacoes funcionando                                     │
│  └── Documentacao atualizada                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**O que isso significa na pratica:** CRM limpo e como uma cozinha
profissional - se esta sujo, a operacao trava. Check diario e inegociavel.
Cada dado errado e uma venda potencial perdida.


```
┌─────────────────────────────────────────────────────────────────┐
│                   4 RITUAIS DE VENDAS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. DAILY (10-15 min - pode ser de pe)                          │
│     ├── Mensagens positivas para comecar                        │
│     ├── Como foi ontem / como sera hoje                         │
│     └── Como um pode ajudar o outro                             │
│                                                                 │
│  2. WEEKLY PIPELINE (30min-1h - CRM-based)                      │
│     ├── Revisao de oportunidades no CRM                         │
│     ├── Cases e objecoes compartilhados                         │
│     └── Negocios proximos de fechar                             │
│                                                                 │
│  3. MONTHLY/QUARTERLY (1-2h)                                    │
│     ├── Revisao de numeros e metas                              │
│     ├── Tendencias e estrategias                                │
│     └── Novos produtos/servicos                                 │
│                                                                 │
│  4. ONE-ON-ONE (20-30 min/semana)                               │
│     ├── Performance individual                                  │
│     ├── Dificuldades e desenvolvimento                          │
│     └── Carreira e proximos passos (NAO E TERAPIA)              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**O que isso significa na pratica:** Rituais sao a cola que mantem o time
alinhado. Daily mantem momentum, Weekly mantem pipeline saudavel, Monthly
mantem direcao estrategica, One-on-one mantem pessoas engajadas.

### Framework 5: Traffic Light System ^[insight_id:TSC-TL001]

**Fonte:** The Scalable Company - BATCH-090

```
┌─────────────────────────────────────────────────────────────────┐
│               TRAFFIC LIGHT LEADERSHIP SYSTEM                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔴 RED - PROBLEMA CRITICO                                      │
│     ├── Meta abaixo de 30% no dia 15                            │
│     ├── Rep sem vendas por 2+ semanas                           │
│     ├── Pipeline zerado                                         │
│     └── ACAO: Intervencao imediata                              │
│                                                                 │
│  🟡 YELLOW - EM RISCO                                           │
│     ├── Meta entre 30-45% no dia 15                             │
│     ├── Rep abaixo da media por 1 semana                        │
│     ├── Pipeline encolhendo                                     │
│     └── ACAO: Monitorar de perto, plano de recuperacao          │
│                                                                 │
│  🟢 GREEN - NO CAMINHO CERTO                                    │
│     ├── Meta >= 50% no dia 15                                   │
│     ├── Rep performando na media ou acima                       │
│     ├── Pipeline saudavel e crescendo                           │
│     └── ACAO: Manter, reconhecer, escalar                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**O que isso significa na pratica:** O Traffic Light simplifica a
comunicacao de status. Em vez de longos relatorios, um olhar rapido
mostra onde precisa atencao. Red = acao imediata. Yellow = atencao.
Green = continue assim.

---

## PADROES DECISORIOS

### Decisoes Recorrentes

| ID | Situacao | Decisao Padrao | Fonte | Confianca |
|----|----------|----------------|-------|-----------|
| PD-001 | Grading de aplicacao | Usar escala 1-4 | ^[insight_id:CG-GRADE001] | ALTA |
| PD-002 | Lead attribution | Round robin como base | ^[insight_id:CG-ATTR001] | ALTA |
| PD-003 | Rep nao fez admin | Cobrar antes de escalar | ^[insight_id:CG-PHASE001] | ALTA |
| PD-004 | Lead Grade 4 | Melhor rep disponivel | ^[insight_id:CG-GRADE001] | ALTA |
| PD-005 | Novo lead chega | Atribuir em < 5 min | ^[insight_id:CG-SPEED001] | ALTA |
| PD-006 | Dashboard com erro | Corrigir imediatamente | ^[insight_id:CG-CRM001] | ALTA |
| PD-007 | Duplicata detectada | Mesclar, manter mais completo | ^[insight_id:CG-CRM001] | MEDIA |
| PD-008 | Processo manual > 10 min/dia | Propor automacao | ^[SOUL.md:162-163] | MEDIA |
| PD-009 | Rep RED no Traffic Light | Intervencao imediata | ^[insight_id:TSC-TL001] | ALTA |
| PD-011 | Metrica nova proposta | Backtest 1 mes antes | ^[insight_id:TSC-SCORE002] | ALTA |
| PD-012 | Selecao de KPIs | Beach Vacation Question | ^[insight_id:TSC-SCORE002] | ALTA |

### Arvore de Decisao: Priorizacao ^[SOUL.md:147-172]

```
NOVA DEMANDA CHEGA
        │
        ▼
┌─────────────────────┐
│ Impacta revenue     │
│ diretamente?        │
└─────────────────────┘
        │
   ┌────┴────┐
   ▼         ▼
  SIM       NAO
   │         │
   ▼         ▼
┌────────┐ ┌────────────────┐
│ URGENTE│ │ Impacta        │
│ (fazer │ │ operacao do    │
│ agora) │ │ time?          │
└────────┘ └────────────────┘
                  │
             ┌────┴────┐
             ▼         ▼
            SIM       NAO
             │         │
             ▼         ▼
         PRIORIZAR  BACKLOG
         HOJE       (agendar)
```

---

## CALIBRACAO BRASIL

### Adaptacoes Culturais Documentadas

| Conceito Original | Fonte | Adaptacao Brasil | Motivo |
|-------------------|-------|------------------|--------|
| CRM em ingles | US default | Campos em portugues | Usabilidade do time |
| Email follow-up | Cole Gordon | WhatsApp preferencial | Cultura BR |
| Hourly availability | US | Comunicacao diaria | Fuso e habito |
| Speed to lead 5 min | Cole Gordon | 2-3 min ideal (WA) | Expectativa BR |
| Dashboard reports | US format | Formato visual BR | Preferencia |

### Particularidades Operacionais Brasil

**CRM Compliance:**
- Vendedores BR tem menor habito de atualizar CRM
- Cobranca precisa ser frequente e sistematica
- Gamificacao de compliance funciona melhor que punicao

**Comunicacao:**
- WhatsApp como canal principal (nao email/Slack)
- Respostas esperadas mais rapidas
- Informalidade maior na comunicacao

**Rituais:**
- Daily pode ser via grupo de WhatsApp
- One-on-one presencial mais valorizado
- Feedback mais indireto que direto

---

## CASOS E PRECEDENTES

### Casos de Sucesso

| ID | Situacao | Acao Tomada | Resultado | Replicavel? |
|----|----------|-------------|-----------|-------------|
| CS-001 | [Aguardando primeiro caso] | - | - | - |

### Casos de Problema

| ID | Situacao | O que deu errado | Aprendizado | Evitar como? |
|----|----------|------------------|-------------|--------------|
| CP-001 | [Aguardando primeiro caso] | - | - | - |

---

## LIMITACOES CONHECIDAS

### O que NAO sei / NAO faco ^[SOUL.md:257-269]

| Area | Limitacao | Escalar para |
|------|-----------|--------------|
| Coaching | Nao faco coaching de vendas | Sales Lead / Manager |
| Estrategia | Nao tomo decisoes estrategicas | Sales Manager |
| Fechamento | Nao fecho deals | Closer |
| Prospeccao | Nao prospecto | BDR / SDS |
| Sistemas | Problemas tecnicos complexos | Ops |

### Perguntas Abertas

- Como balancear padronizacao com flexibilidade por rep?
- Qual o limite de automacao antes de perder controle humano?
- Como escalar coordenacao para times > 10 vendedores?
- Quando migrar de OTE para % tradicional (ou vice-versa)?
- Como adaptar Traffic Light para realidade de startup early-stage?

---

## KNOWLEDGE BASE LOCATIONS

### Hierarquia de Consulta

**Para respostas rapidas (1 pessoa x 1 tema):**
→ `/knowledge/SOURCES/{PESSOA}/{TEMA}.md`

**Para contexto expandido (todos os temas de 1 pessoa):**
→ `/knowledge/dossiers/persons/DOSSIER-{PESSOA}.md`

**Para comparacao multi-fonte (multiplas pessoas, 1 tema):**
→ `/knowledge/dossiers/THEMES/DOSSIER-{TEMA}.md`

**Para transcricao original:**
→ `/inbox/{PESSOA}/...`

### Arquivos Mais Relevantes

| Arquivo | Tema | Relevancia |
|---------|------|------------|
| `/knowledge/dossiers/persons/DOSSIER-COLE-GORDON.md` | Tudo de Cole Gordon | ALTA |
| `/knowledge/dossiers/THEMES/DOSSIER-09-GESTAO.md` | Sales Management | ALTA |
| `/knowledge/dossiers/THEMES/DOSSIER-06-FUNIL-APLICACAO.md` | Application Grading | ALTA |
| `/knowledge/SOURCES/cole-gordon/09-GESTAO.md` | Admin & Ops | ALTA |
| `/knowledge/SOURCES/cole-gordon/06-FUNIL-APLICACAO.md` | Lead Attribution | ALTA |
| `/logs/batches/BATCH-050.md` | Lideranca de Times | ALTA |
| `/logs/batches/BATCH-088.md` | Scorecards & Accountability | ALTA |
| `/logs/batches/BATCH-090.md` | OS Installation & Scorecard | ALTA |
| `/logs/batches/BATCH-105.md` | Pos-Venda, Gestao & Vendas B2B | ALTA |

---

## INTERACOES SIGNIFICATIVAS

### Consultas Frequentes

| Agente | Assunto Tipico | Frequencia | Padrao de Resposta |
|--------|----------------|------------|-------------------|
| @SALES-LEAD | Metricas do dia | Diario | Dashboard atualizado |
| @SALES-MANAGER | Performance semanal | Semanal | Relatorio completo |
| @CMO | Disponibilidade time | Diario | Slots abertos |
| @BDR / @SDS | Atribuicao de leads | Frequente | Round robin / skill |
| @CLOSER | Status de leads | Sob demanda | CRM atualizado |

### Protocolos Aplicaveis

| Protocolo | Path |
|-----------|------|
| AGENT-COGNITION-PROTOCOL | `.claude/rules/agent-cognition.md` |
| EPISTEMIC-PROTOCOL | `.claude/rules/epistemic-standards.md` |
| AGENT-INTERACTION | `.claude/rules/agent-interaction.md` |
| WAR-ROOM | `core/templates/debates/war-room.md` |
| MEMORY-PROTOCOL | `core/templates/agents/memory-template.md` |

---

## HISTORICO DE ATUALIZACOES

| Data | Versao | Tipo | Descricao | Origem |
|------|--------|------|-----------|--------|
| 2026-01-11 | 3.0.0 | Major Update | Adicao BATCH INSIGHTS (BATCH-050 a 067, 085 a 110), novos frameworks (4 Rituais, Traffic Light, MIND), insights de coordenacao extraidos | JARVIS Pipeline |
| 2025-12-26 | 2.0.0 | Upgrade | Template V2, insight tags, frameworks detalhados | Sistema |
| 2024-12-15 | 1.0.0 | Criacao | Memoria inicializada | Sistema |

---

## CHANGELOG

| Versao | Data | Mudancas |
|--------|------|----------|
| 3.0.0 | 2026-01-11 | Major: Secao BATCH INSIGHTS com 36+ novos insights de Pipeline Management, CRM Workflows, Team Coordination, Reporting Frameworks. Novos frameworks: 4 Rituais de Vendas, Traffic Light System. Novas heuristicas: Pacing de meta, Beach Vacation Question, OTE model, NPS scoring. Batches processados: 050-067 (Cole Gordon), 085-110 (/TSC). |
| 2.0.0 | 2025-12-26 | Template V2, frameworks visuais, insight tags, calibracao BR detalhada |
| 1.0.0 | 2024-12-15 | Versao inicial |

---

*Esta memoria cresce comigo. Cada processo que otimizo,
cada gargalo que resolvo - tudo e registrado aqui.*

*Ultima atualizacao: 2026-01-11*
