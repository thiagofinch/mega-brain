# ORQUESTRAÇÃO-PROTOCOL: Fluxo Completo do Sistema

> **Versão:** 1.0.0
> **Função:** Governar o fluxo desde pergunta até resposta final

---

## ARQUITETURA DE 3 CAMADAS

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                        CAMADA 1: CONSTITUIÇÃO BASE                              │
│                                                                                 │
│   Filosofia: Empirismo, Pareto, Inversão, Antifragilidade                      │
│   Path: /system/protocols/CONSTITUICAO-BASE.md                              │
│   Aplica-se: TODOS os agentes                                                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                      CAMADA 2: AGENTES ESPECIALIZADOS                           │
│                                                                                 │
│   CARGO (Híbrido):                                                             │
│   • C-LEVEL: CRO, CFO, CMO, COO                                                │
│   • SALES: CLOSER, BDR, SDS, LNS, SALES-MANAGER, etc.                         │
│   Path: /agents/cargo/                                                      │
│                                                                                 │
│   PERSONS (Solo - só via /consult):                                            │
│   Path: /agents/persons/                                                    │
│                                                                                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ (debate entre agentes)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                        CAMADA 3: COUNCIL (Meta-avaliação)                       │
│                                                                                 │
│   1º CRÍTICO METODOLÓGICO → Avalia qualidade do processo                       │
│   2º ADVOGADO DO DIABO → Ataca premissas e riscos                              │
│   3º SINTETIZADOR → Integra em decisão final                                   │
│                                                                                 │
│   Path: /agents/council/                                                    │
│   Protocol: /system/protocols/conclave/CONCLAVE-PROTOCOL.md                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## FLUXO DE DECISÃO DO MASTER-AGENT

```
                              ENTRADA
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CLASSIFICAÇÃO                                          │
│                                                                                 │
│   ┌───────────────────┬─────────────────────────────────────┬───────────────┐  │
│   │ TIPO              │ EXEMPLO                             │ COUNCIL?      │  │
│   ├───────────────────┼─────────────────────────────────────┼───────────────┤  │
│   │ A: /consult       │ /consult cole "Como fazer pitch?"   │ NÃO           │  │
│   │ B: /board         │ /board "Contratar SM agora?"        │ SIM           │  │
│   │ C: Simples        │ "Qual benchmark de close rate?"     │ NÃO           │  │
│   │ D: Complexa       │ "Como escalar de 1M para 5M?"       │ SIM           │  │
│   │ E: Operacional    │ /process-video                      │ NÃO           │  │
│   └───────────────────┴─────────────────────────────────────┴───────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## FLUXOS DETALHADOS

### TIPO A: /consult (Consulta Direta)

```
/consult {pessoa} "{pergunta}"
         │
         ▼
Identificar AGENT-PERSON
         │
         ▼
Carregar: AGENT → SOUL → DNA-CONFIG → MEMORY
         │
         ▼
Responder na VOZ da pessoa
         │
         ▼
OUTPUT DIRETO (sem Council)
```

### TIPO B: /board (Conselho de Experts)

```
/board "{pergunta}"
         │
         ▼
         │
         ▼
Debate entre PERSONS
         │
         ▼
COUNCIL avalia:
  1. Crítico Metodológico
  2. Advogado do Diabo
  3. Sintetizador
         │
         ▼
DECISÃO DO COUNCIL
```

### TIPO C: Pergunta Simples

```
"{pergunta de domínio específico}"
         │
         ▼
Identificar domínio → Selecionar 1 AGENT-CARGO
         │
         ▼
Carregar: AGENT → SOUL → DNA-CONFIG → MEMORY
         │
         ▼
         │
         ▼
OUTPUT DIRETO (sem Council)
```

### TIPO D: Pergunta Complexa

```
"{pergunta multi-domínio ou decisão significativa}"
         │
         ▼
Identificar domínios → Selecionar 2-4 AGENT-CARGO
         │
         ▼
DEBATE entre agentes (posições, evidências, recomendações)
         │
         ▼
COUNCIL avalia:
  1. Crítico Metodológico
  2. Advogado do Diabo
  3. Sintetizador
         │
         ▼
DECISÃO DO COUNCIL
```

---

## REGRA FUNDAMENTAL: CARGO vs PERSON

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                                                                                 │
│   Pergunta: "Como fechar venda high-ticket?"                                   │
│   → CLOSER responde (tem DNA Cole 95% + Hormozi 85%)                           │
│   → NÃO roteia para AGENT-PERSON                                               │
│                                                                                 │
│   AGENT-PERSON só via:                                                         │
│   • /consult cole "pergunta"                                                   │
│   • /consult hormozi "pergunta"                                                │
│   • /board "pergunta"                                                          │
│   • Menção explícita "como Cole faria"                                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## QUANDO ACIONAR COUNCIL

```
COUNCIL É ACIONADO SE:
✅ 2+ agentes CARGO participam do debate
✅ Há divergência significativa
✅ Decisão tem impacto relevante
✅ Usuário pede /board

COUNCIL NÃO É ACIONADO SE:
❌ Pergunta simples (1 agente)
❌ /consult direto a PERSON
❌ Comando operacional
❌ Consenso total entre agentes
```

---

## PROTOCOLOS RELACIONADOS

| Protocolo | Path |
|-----------|------|
| CONSTITUIÇÃO BASE | `/system/protocols/CONSTITUICAO-BASE.md` |
| AGENT-COGNITION | `/agents/protocols/AGENT-COGNITION-PROTOCOL.md` |
| CONCLAVE-PROTOCOL | `/system/protocols/conclave/CONCLAVE-PROTOCOL.md` |
| DEBATE-PROTOCOL | `/system/protocols/conclave/DEBATE-PROTOCOL.md` |
| EPISTEMIC | `/agents/protocols/EPISTEMIC-PROTOCOL.md` |
| MEMORY | `/agents/protocols/MEMORY-PROTOCOL.md` |

---

## AGENT-INDEX

Path: `/agents/AGENT-INDEX.yaml`

Contém índice completo de todos os agentes para roteamento rápido.
