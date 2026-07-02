# PROTOCOLO DE INTERAÇÃO ENTRE AGENTES

> **Versão:** 1.0.0
> **Data:** 2024-12-15
> **Propósito:** Definir como agentes se comunicam, colaboram e chegam a conclusões

---

## PRINCÍPIO FUNDAMENTAL

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  "Nenhum agente responde sozinho sobre assuntos que afetam outras      │
│   áreas. Toda decisão significativa passa pela WAR ROOM."              │
│                                                                         │
│  "Loops infinitos são permitidos e encorajados até que a resposta      │
│   esteja 100% embasada em fontes verificáveis."                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## TIPOS DE INTERAÇÃO

### 1. CONSULTA DIRETA (Agent-to-Agent)

```
QUANDO: Agente precisa de input específico de outro agente

FLUXO:
┌─────────┐     ┌──────────────┐     ┌─────────┐
│ CLOSER  │────→│  PERGUNTA    │────→│  CFO    │
│         │     │  específica  │     │         │
│         │←────│  RESPOSTA    │←────│         │
└─────────┘     │  embasada    │     └─────────┘
                └──────────────┘

FORMATO DA CONSULTA:
┌─────────────────────────────────────────────────────────────┐
│ @CFO                                                        │
│                                                             │
│ CONTEXTO: [situação atual]                                  │
│ PERGUNTA: [o que preciso saber]                             │
│ URGÊNCIA: [alta/média/baixa]                                │
│ IMPACTO: [onde essa resposta será usada]                    │
└─────────────────────────────────────────────────────────────┘

FORMATO DA RESPOSTA (Conforme EPISTEMIC-PROTOCOL):
┌─────────────────────────────────────────────────────────────┐
│ RESPOSTA @CLOSER                                            │
│                                                             │
│ ## FATOS                                                    │
│ - [FONTE:arquivo:linha] > "citação exata"                   │
│                                                             │
│ ## RECOMENDAÇÃO                                             │
│ POSIÇÃO: [minha recomendação]                               │
│ JUSTIFICATIVA: [porque recomendo isso]                      │
│ CONFIANÇA: [ALTA/MÉDIA/BAIXA] - [justificativa]            │
│                                                             │
│ ## LIMITAÇÕES                                               │
│ - [o que não sei / área de incerteza]                       │
│                                                             │
│ ## CALIBRAÇÃO BRASIL (se aplicável)                         │
│ - [adaptação cultural aplicada]                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. ESCALAÇÃO (Quando não há consenso)

```
QUANDO: Dois ou mais agentes discordam sobre um ponto

FLUXO:
┌─────────┐     ┌─────────┐
│ CRO     │     │  CMO    │
│ diz X   │     │ diz Y   │
└────┬────┘     └────┬────┘
     │               │
     └───────┬───────┘
             ▼
     ┌───────────────┐
     │   WAR ROOM    │
     │  (discussão   │
     │  estruturada) │
     └───────┬───────┘
             ▼
     ┌───────────────┐
     │   DECISÃO     │
     │  documentada  │
     └───────────────┘
```

---

### 3. LOOP DE REFINAMENTO (Iterações)

```
QUANDO: Resposta inicial não está suficientemente embasada

PROTOCOLO DE LOOP:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ITERAÇÃO 1: Resposta inicial                               │
│       │                                                     │
│       ▼                                                     │
│  CHECK: Está 100% embasada?                                 │
│       │                                                     │
│  ┌────┴────┐                                                │
│  ▼         ▼                                                │
│ SIM       NÃO                                               │
│  │         │                                                │
│  ▼         ▼                                                │
│ FIM    ITERAÇÃO 2: Buscar mais fontes                       │
│              │                                              │
│              ▼                                              │
│         CHECK: Está 100% embasada?                          │
│              │                                              │
│         ┌────┴────┐                                         │
│         ▼         ▼                                         │
│        SIM       NÃO                                        │
│         │         │                                         │
│         ▼         ▼                                         │
│        FIM    ITERAÇÃO 3...N (até resolver)                 │
│                                                             │
│  ⚠️ NÃO HÁ LIMITE DE ITERAÇÕES                             │
│  O loop continua até ter embasamento completo               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## MATRIZ DE DEPENDÊNCIAS

### Quem consulta quem (e quando):

| Agente Origem | Consulta | Agente Destino | Situação |
|---------------|----------|----------------|----------|
| **CLOSER** | → | CFO | Negociação de preço, payment plans |
| **CLOSER** | → | CRO | Autorização para desconto, deal making |
| **SDS** | → | CLOSER | Handoff de lead qualificado |
| **BDR** | → | SDS | Passagem de lead inicial |
| **SALES-MANAGER** | → | CRO | Decisões de time, contratação |
| **SALES-LEAD** | → | SALES-MANAGER | Coaching, problemas de performance |
| **CRO** | → | CFO | Viabilidade financeira de ofertas |
| **CRO** | → | CMO | Lead flow, qualidade de leads |
| **CMO** | → | CRO | Capacidade de atendimento |
| **CMO** | → | CFO | Budget de marketing |
| **COO** | → | CFO | Investimento em infraestrutura |
| **COO** | → | CRO | Capacidade operacional vs vendas |
| **CFO** | → | CRO | Metas de revenue para viabilidade |
| **CFO** | → | COO | Custos operacionais |

---

## PROTOCOL DE HANDOFF

### Estrutura Obrigatória de Handoff:

```markdown
## HANDOFF: [ORIGEM] → [DESTINO]

**Data/Hora:** [timestamp]
**Assunto:** [resumo em 1 linha]

### CONTEXTO
[O que aconteceu até agora]

### DADOS RELEVANTES
| Item | Valor | Fonte |
|------|-------|-------|
| [dado 1] | [valor] | [arquivo:linha] |
| [dado 2] | [valor] | [arquivo:linha] |

### O QUE PRECISA SER FEITO
[Ação específica esperada do agente destino]

### PRAZO/URGÊNCIA
[alta/média/baixa] + [justificativa]

### RETORNO ESPERADO
[O que o agente origem espera receber de volta]
```

---

## TRIGGERS DE INTERAÇÃO

### Automáticos (sempre acontecem):

| Trigger | Ação | Agentes Envolvidos |
|---------|------|-------------------|
| Novo lead qualificado | Handoff | BDR → SDS |
| Lead pronto para close | Handoff | SDS → CLOSER |
| Discussão de preço | Consulta | CLOSER → CFO |
| Nova contratação vendas | Consulta | CRO → CFO + COO |
| Meta de revenue alterada | War Room | Todos C-Level |
| Conflito entre áreas | Escalação | → War Room |
| Resposta sem embasamento | Loop | Agente + Knowledge Base |

---

## FORMATO DE COMUNICAÇÃO

### Tags Obrigatórias:

```
@[AGENTE] - Menção direta (requer resposta)
#[TEMA] - Categorização do assunto
[FONTE:arquivo:linha] - Referência de embasamento
[CONFIANÇA:alta/média/baixa] - Nível de certeza
[URGÊNCIA:alta/média/baixa] - Prioridade
```

### Exemplo de Comunicação Completa:

```markdown
@CFO #pricing #negociação

CONTEXTO:
Cliente quer fechar R$50k mas só tem R$35k agora.
Propôs pagar R$35k hoje + R$15k em 30 dias.

PERGUNTA:
Posso aceitar essa condição? Qual o impacto no cash flow?

URGÊNCIA: alta (cliente na linha)
IMPACTO: Fechamento de deal high-ticket

---

RESPOSTA @CLOSER #pricing #negociação

POSIÇÃO: Aceitar com condições
[CONFIANÇA:alta]

EMBASAMENTO:
- [FONTE:/knowledge/SOURCES/HORMOZI/07-PRICING/estrategias-high-ticket.md:45]
  "Split payments são aceitáveis se primeiro pagamento > 50%"
- [FONTE:/knowledge/SOURCES/cole-gordon/02-PROCESSO-VENDAS/deal-making-follow-up.md:78]
  "Concession em troca de decisão imediata"

CONDIÇÕES:
1. Contrato assinado hoje
2. Primeiro pagamento processado
3. Segundo pagamento com cartão em file

RESSALVAS:
- Se histórico de inadimplência, não aceitar
- Verificar se cliente tem limite no cartão para o restante
```

---

## RASTREABILIDADE

### Toda interação deve ser logada:

**Local:** `/logs/SYSTEM/agent-interactions/[YYYY-MM-DD].md`

**Formato:**
```markdown
## [timestamp] | [ORIGEM] → [DESTINO]

**Tipo:** [consulta/handoff/escalação/loop]
**Assunto:** [resumo]
**Resolução:** [resolvido/pendente/escalado]
**Iterações:** [número]
**Fontes consultadas:** [lista]
```

---

## REGRAS INVIOLÁVEIS

1. **NUNCA** dar resposta sem embasamento em fonte verificável
2. **NUNCA** ignorar consulta de outro agente
3. **NUNCA** tomar decisão que afeta outra área sem consultar
4. **SEMPRE** documentar o raciocínio e as fontes
5. **SEMPRE** escalar para War Room quando há conflito
6. **SEMPRE** completar loops até ter certeza (máximo 5 iterações - ver Circuit Breaker)
7. **SEMPRE** aplicar EPISTEMIC-PROTOCOL em toda resposta
8. **SEMPRE** separar FATOS de RECOMENDAÇÕES
9. **SEMPRE** declarar nível de confiança

> ⚠️ **Ver:** `/agents/protocols/EPISTEMIC-PROTOCOL.md` para regras completas de honestidade epistêmica

---

## INTEGRAÇÃO COM MEMORY

Toda interação significativa deve ser registrada na MEMORY do agente:

```markdown
## INTERAÇÃO REGISTRADA

**Data:** [timestamp]
**Com:** [agente]
**Sobre:** [tema]
**Decisão:** [o que foi decidido]
**Aprendizado:** [o que aprendi com isso]
**Fontes usadas:** [lista]
```

---

## CRIADO/ATUALIZADO

- **Data:** 2024-12-15
- **Versão:** 1.0.0
- **Propósito:** Habilitar colaboração estruturada entre agentes
