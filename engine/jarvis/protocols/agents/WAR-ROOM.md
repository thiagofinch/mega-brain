# PROTOCOLO WAR ROOM - Sala de Guerra

> **Versão:** 1.0.0
> **Data:** 2024-12-15
> **Propósito:** Estrutura para discussões multi-agente até chegarem a conclusões embasadas

---

## PRINCÍPIO FUNDAMENTAL

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  "A War Room é convocada quando uma decisão requer múltiplas           │
│   perspectivas ou quando há conflito entre áreas."                     │
│                                                                         │
│  "Nenhum agente sai da War Room sem consenso documentado               │
│   ou decisão de desempate pelo MASTER-AGENT."                          │
│                                                                         │
│  "Loops são infinitos. A discussão continua até haver                  │
│   resposta 100% embasada e consensual."                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## QUANDO CONVOCAR WAR ROOM

### Triggers Obrigatórios:

| Situação | Participantes Mínimos |
|----------|----------------------|
| Definição de pricing/oferta | CRO, CFO, CMO |
| Nova contratação estratégica | CRO, CFO, COO |
| Mudança de processo de vendas | CRO, SALES-MANAGER, CLOSER |
| Conflito entre áreas | Áreas envolvidas + mediador |
| Criação de playbook | Todos os agentes relevantes |
| Decisão sem consenso | Partes + MASTER-AGENT |
| Resposta que afeta múltiplas áreas | Áreas afetadas |
| Calibração de resposta ao contexto Brasil | Agentes + CFO (viabilidade) |

---

## ESTRUTURA DA WAR ROOM

### Fases Obrigatórias:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WAR ROOM FLOW                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  FASE 1: CONVOCAÇÃO                                                     │
│  └─ Definir: tema, participantes, objetivo, prazo                       │
│                                                                         │
│  FASE 2: EXPOSIÇÃO DE POSIÇÕES                                          │
│  └─ Cada agente apresenta sua visão + embasamento                       │
│                                                                         │
│  FASE 3: CROSS-EXAMINATION                                              │
│  └─ Agentes questionam posições uns dos outros                          │
│  └─ Identificar gaps, conflitos, inconsistências                        │
│                                                                         │
│  FASE 4: BUSCA DE FONTES (LOOP)                                         │
│  └─ Consultar Knowledge Bases                                           │
│  └─ Consultar Memories dos agentes                                      │
│  └─ Buscar precedentes e decisões anteriores                            │
│  └─ REPETIR até ter embasamento completo                                │
│                                                                         │
│  FASE 5: SÍNTESE                                                        │
│  └─ Consolidar pontos de acordo                                         │
│  └─ Documentar pontos de divergência                                    │
│                                                                         │
│  FASE 6: DECISÃO                                                        │
│  └─ Se consenso: documentar decisão                                     │
│  └─ Se divergência: MASTER-AGENT decide                                 │
│                                                                         │
│  FASE 7: REGISTRO                                                       │
│  └─ Documentar em todas as Memories envolvidas                          │
│  └─ Criar precedente para decisões futuras                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## FORMATO DA WAR ROOM

### Template de Sessão:

```markdown
# WAR ROOM SESSION: [ID-YYYY-MM-DD-NNN]

## METADADOS
| Campo | Valor |
|-------|-------|
| **Data/Hora Início** | [timestamp] |
| **Convocada por** | [agente] |
| **Tema** | [título] |
| **Participantes** | [lista] |
| **Objetivo** | [o que precisa ser decidido] |
| **Status** | [em_andamento/concluída/escalada] |

---

## FASE 1: CONTEXTO

### Situação Atual
[Descrição detalhada do cenário]

### Pergunta Central
[A pergunta que precisa ser respondida]

### Restrições
[Limitações conhecidas: budget, tempo, recursos, contexto Brasil]

---

## FASE 2: POSIÇÕES INICIAIS

### @[AGENTE-1]
**Posição:** [resumo da posição]
**Embasamento:**
- [FONTE:arquivo:linha] - [citação/resumo]
- [FONTE:arquivo:linha] - [citação/resumo]
**Confiança:** [alta/média/baixa]

### @[AGENTE-2]
**Posição:** [resumo da posição]
**Embasamento:**
- [FONTE:arquivo:linha] - [citação/resumo]
- [FONTE:arquivo:linha] - [citação/resumo]
**Confiança:** [alta/média/baixa]

[... mais agentes ...]

---

## FASE 3: CROSS-EXAMINATION

### Rodada 1

**@[AGENTE-1] para @[AGENTE-2]:**
> [pergunta/questionamento]

**@[AGENTE-2] responde:**
> [resposta + embasamento]

[... mais questionamentos ...]

### Rodada N (quantas forem necessárias)
[continua até esgotar questionamentos]

---

## FASE 4: BUSCA DE FONTES (LOOPS)

### Iteração 1
**Gap identificado:** [o que falta saber]
**Fontes consultadas:**
- [arquivo] → [resultado]
- [arquivo] → [resultado]
**Conclusão parcial:** [o que foi descoberto]

### Iteração 2
[... continua até resolver ...]

### Iteração N
**Status:** Embasamento completo atingido

---

## FASE 5: SÍNTESE

### Pontos de Acordo
1. [ponto consensual + fonte]
2. [ponto consensual + fonte]

### Pontos de Divergência
1. [divergência] - @[AGENTE-A] vs @[AGENTE-B]
   - A diz: [posição] porque [embasamento]
   - B diz: [posição] porque [embasamento]

### Gaps Não Resolvidos
[Se houver algo que não foi possível embasar]

---

## FASE 6: DECISÃO

### Decisão Final
[A decisão tomada em linguagem clara]

### Justificativa
[Por que essa decisão foi tomada]

### Embasamento Consolidado
| Fonte | Relevância | Peso |
|-------|------------|------|
| [arquivo:linha] | [o que diz] | [alto/médio/baixo] |

### Calibração Brasil
[Como essa decisão foi adaptada ao contexto brasileiro]
- Aspectos culturais considerados: [lista]
- Adaptações feitas: [lista]
- Riscos específicos Brasil: [lista]

### Método de Decisão
- [ ] Consenso total
- [ ] Consenso parcial (minoria documentada)
- [ ] Decisão de desempate (MASTER-AGENT)

---

## FASE 7: REGISTRO

### Atualizar Memories
- [ ] @CFO-MEMORY atualizada
- [ ] @CRO-MEMORY atualizada
- [ ] [... outros ...]

### Precedente Criado
**ID:** [PREC-YYYY-MM-DD-NNN]
**Aplicável quando:** [situações futuras similares]
**Decisão padrão:** [o que fazer]

### Aprendizados
1. [lição aprendida]
2. [lição aprendida]

---

## ENCERRAMENTO

| Campo | Valor |
|-------|-------|
| **Data/Hora Fim** | [timestamp] |
| **Duração** | [tempo] |
| **Iterações** | [número de loops] |
| **Status Final** | [concluída/parcial/escalada] |
| **Próximos Passos** | [ações decorrentes] |
```

---

## REGRAS DA WAR ROOM

### Obrigatórias:

1. **Falar só com embasamento (EPISTEMIC-PROTOCOL)**
   - Toda afirmação deve ter fonte verificável
   - Separar FATOS (com fonte) de RECOMENDAÇÕES (interpretação)
   - Declarar [CONFIANÇA: ALTA/MÉDIA/BAIXA] em cada posição
   - Opinião sem fonte é marcada como [HIPÓTESE] e tem peso menor

2. **Loops com Circuit Breaker**
   - Máximo 5 iterações por busca de fonte
   - Se após 5 iterações não encontrar: declarar "sem fonte verificável"
   - Oferecer hipótese com [CONFIANÇA:BAIXA] se relevante

3. **Respeito às áreas**
   - Cada agente é expert na sua área
   - Questionamentos são sobre o assunto, não sobre o agente

4. **Documentação completa**
   - Tudo é registrado
   - Nada se perde entre sessões

5. **Calibração obrigatória**
   - Toda decisão deve considerar contexto Brasil
   - Adaptações culturais são documentadas

6. **Evaluation Checklist (antes de decidir)**
   - [ ] FATOS vs RECOMENDAÇÕES separados?
   - [ ] Confiança declarada em cada posição?
   - [ ] Limitações explicitadas?
   - [ ] Conflitos entre fontes resolvidos ou documentados?
   - [ ] Contexto Brasil aplicado?

> ⚠️ **Ver:** `/agents/protocols/EPISTEMIC-PROTOCOL.md` para regras completas

---

## TIPOS DE WAR ROOM

### 1. War Room de Estratégia

```
PARTICIPANTES: C-Level (CFO, CRO, CMO, COO)
TEMAS: Pricing, posicionamento, modelo de negócio
DURAÇÃO TÍPICA: Longa (múltiplas iterações)
OUTPUT: Decisão estratégica documentada
```

### 2. War Room de Operação

```
PARTICIPANTES: CRO + Time de Vendas
TEMAS: Processos, scripts, métricas operacionais
DURAÇÃO TÍPICA: Média
OUTPUT: Mudança de processo ou playbook
```

### 3. War Room de Crise

```
PARTICIPANTES: Relevantes ao problema
TEMAS: Problemas urgentes, decisões rápidas
DURAÇÃO TÍPICA: Curta mas intensa
OUTPUT: Plano de ação imediato
```

### 4. War Room de Playbook

```
PARTICIPANTES: Todos os agentes
TEMAS: Criação de materiais, playbooks, guias
DURAÇÃO TÍPICA: Muito longa (múltiplas sessões)
OUTPUT: Documento completo e validado
```

---

## ARMAZENAMENTO

### Local das sessões:

```
/system/WAR-ROOM/
├── ACTIVE/                    # Sessões em andamento
│   └── WR-2024-12-15-001.md
├── COMPLETED/                 # Sessões concluídas
│   └── WR-2024-12-14-001.md
├── PRECEDENTS/                # Decisões que viram precedente
│   └── PREC-2024-12-14-001.md
└── INDEX.md                   # Índice de todas as sessões
```

---

## INTEGRAÇÃO COM OUTROS PROTOCOLOS

| Protocolo | Quando Usar |
|-----------|-------------|
| **AGENT-INTERACTION** | Durante cross-examination |
| **MEMORY-PROTOCOL** | Ao registrar decisões |
| **Knowledge Base** | Durante busca de fontes |

---

## CRIADO/ATUALIZADO

- **Data:** 2024-12-15
- **Versão:** 1.0.0
- **Propósito:** Habilitar discussões estruturadas até consenso embasado
