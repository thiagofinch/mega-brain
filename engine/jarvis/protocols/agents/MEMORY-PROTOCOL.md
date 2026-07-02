# PROTOCOLO DE MEMÓRIA DOS AGENTES

> **Versão:** 1.0.0
> **Data:** 2024-12-15
> **Propósito:** Definir como agentes acumulam, filtram e utilizam conhecimento experiencial

---

## PRINCÍPIO FUNDAMENTAL

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  "Cada agente é como uma pessoa real em um cargo: acumula              │
│   experiência, aprende com decisões, desenvolve intuição               │
│   calibrada ao contexto."                                              │
│                                                                         │
│  "A memória é o que diferencia um agente genérico de um               │
│   especialista experiente."                                            │
│                                                                         │
│  "Cada projeto é um projeto. O agente sabe ler cirurgicamente          │
│   seu conhecimento para adaptar ao contexto específico."               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ARQUITETURA DE CONHECIMENTO

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ESTRUTURA DE UM AGENTE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     AGENT-[NOME].md                              │   │
│  │                                                                   │   │
│  │  • Identidade (quem sou)                                         │   │
│  │  • Responsabilidades (o que faço)                                │   │
│  │  • Frameworks (como faço)                                        │   │
│  │  • Métricas (como meço)                                          │   │
│  │  • Decision Trees (como decido)                                  │   │
│  │                                                                   │   │
│  │  ↓ APONTA PARA ↓                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│          ┌───────────────────┼───────────────────┐                      │
│          ▼                   ▼                   ▼                      │
│  ┌───────────────┐  ┌───────────────┐   ┌───────────────────┐          │
│  │ KNOWLEDGE     │  │ AGENT-[NOME]  │   │ PROTOCOLS/        │          │
│  │ BASE GERAL    │  │ -MEMORY.md    │   │                   │          │
│  │               │  │               │   │ • INTERACTION     │          │
│  │ /knowledge │  │ Documento     │   │ • WAR-ROOM        │          │
│  │ /THEMES/...   │  │ Irmão         │   │ • MEMORY-PROTOCOL │          │
│  │               │  │               │   │                   │          │
│  │ Conhecimento  │  │ Experiência   │   │ Como colaborar    │          │
│  │ TEÓRICO       │  │ PRÁTICA       │   │ com outros        │          │
│  │ das fontes    │  │ acumulada     │   │                   │          │
│  └───────────────┘  └───────────────┘   └───────────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ESTRUTURA DO ARQUIVO DE MEMÓRIA

### Template: AGENT-[NOME]-MEMORY.md

```markdown
# MEMÓRIA: [NOME DO AGENTE]

> **Agente:** [link para AGENT-*.md]
> **Criada:** [data]
> **Última atualização:** [timestamp]
> **Total de registros:** [número]

---

## METADADOS DE CONTEXTO

### Projeto Atual
| Campo | Valor |
|-------|-------|
| **Empresa** | [nome] |
| **Produto** | [descrição] |
| **Ticket** | [valor] |
| **País** | Brasil |
| **Fase** | [estágio do negócio] |

### Particularidades Culturais (Brasil)
- [aspectos relevantes ao contexto brasileiro]
- [diferenças vs mercado americano]
- [adaptações necessárias]

---

## PADRÕES DECISÓRIOS

### Decisões Recorrentes

| ID | Situação | Decisão Padrão | Embasamento | Confiança |
|----|----------|----------------|-------------|-----------|
| PD-001 | [cenário] | [o que fazer] | [FONTE:arquivo:linha] | alta/média/baixa |
| PD-002 | [cenário] | [o que fazer] | [FONTE:arquivo:linha] | alta/média/baixa |

### Árvore de Decisão Expandida

```
[Situação específica do contexto]
        │
        ▼
[Primeira pergunta a fazer]
        │
   ┌────┴────┐
   ▼         ▼
  SIM       NÃO
   │         │
   ▼         ▼
[Ação A]  [Ação B]
```

---

## APRENDIZADOS ACUMULADOS

### Insights por Fonte

#### De [FONTE-ID: Nome]
| Data | Insight | Aplicabilidade | Testado? |
|------|---------|----------------|----------|
| [data] | [o que aprendi] | [quando usar] | sim/não |

#### De Experiência Prática (War Rooms, Interações)
| Data | Contexto | Aprendizado | Origem |
|------|----------|-------------|--------|
| [data] | [situação] | [lição] | [WR-ID ou interação] |

---

## CASOS E PRECEDENTES

### Casos de Sucesso
| ID | Situação | Ação Tomada | Resultado | Replicável? |
|----|----------|-------------|-----------|-------------|
| CS-001 | [cenário] | [o que fiz] | [outcome] | sim/parcial/não |

### Casos de Fracasso (Aprendizado)
| ID | Situação | Erro | Aprendizado | Evitar Quando |
|----|----------|------|-------------|---------------|
| CF-001 | [cenário] | [o que deu errado] | [lição] | [condições] |

### Precedentes de War Room
| WR-ID | Tema | Decisão | Aplicar Quando |
|-------|------|---------|----------------|
| [ID] | [assunto] | [decisão tomada] | [situações similares] |

---

## CONFLITOS RESOLVIDOS

### Entre Fontes
| ID | Fonte A | Diz | Fonte B | Diz | Resolução | Contexto |
|----|---------|-----|---------|-----|-----------|----------|
| CR-001 | [fonte] | [X] | [fonte] | [Y] | [decisão] | [quando usar cada] |

### Entre Áreas
| ID | Área A | Posição | Área B | Posição | Resolução |
|----|--------|---------|--------|---------|-----------|
| CA-001 | [área] | [visão] | [área] | [visão] | [consenso] |

---

## CALIBRAÇÃO BRASIL

### Adaptações Culturais Documentadas
| Conceito Original | Fonte | Adaptação Brasil | Motivo |
|-------------------|-------|------------------|--------|
| [conceito US] | [arquivo] | [versão BR] | [por quê] |

### Métricas Ajustadas
| Métrica | Benchmark US | Benchmark BR | Fonte |
|---------|--------------|--------------|-------|
| [métrica] | [valor US] | [valor BR] | [se houver] |

### Práticas Específicas Brasil
- [prática 1 que funciona diferente aqui]
- [prática 2 específica do mercado]

---

## INTERAÇÕES SIGNIFICATIVAS

### Com Outros Agentes
| Data | Agente | Assunto | Outcome | Aprendizado |
|------|--------|---------|---------|-------------|
| [data] | @[agente] | [tema] | [resultado] | [o que aprendi] |

### Consultas Frequentes
| Agente | Assunto Típico | Frequência | Padrão de Resposta |
|--------|----------------|------------|-------------------|
| @[agente] | [tema] | [frequência] | [como respondo] |

---

## KNOWLEDGE BASE LINKS

### Arquivos Mais Consultados
| Arquivo | Tema | Relevância | Última Consulta |
|---------|------|------------|-----------------|
| [path] | [assunto] | alta/média/baixa | [data] |

### Seções Críticas (Quick Access)
| Arquivo | Linha | Conteúdo | Uso |
|---------|-------|----------|-----|
| [path] | [linha] | [resumo] | [quando consulto] |

---

## HISTÓRICO DE ATUALIZAÇÕES

| Data | Tipo | Descrição | Origem |
|------|------|-----------|--------|
| [timestamp] | [aprendizado/decisão/calibração] | [o que mudou] | [fonte/war room/interação] |

---

## PRÓXIMAS ÁREAS A DESENVOLVER

### Gaps de Conhecimento Identificados
- [ ] [área que preciso aprender mais]
- [ ] [tema que falta embasamento]

### Fontes Pendentes de Processamento
- [ ] [material que ainda não foi extraído]
```

---

## REGRAS DE ATUALIZAÇÃO

### O que DEVE ser registrado:

| Evento | Ação | Seção |
|--------|------|-------|
| Nova decisão tomada | Registrar | Padrões Decisórios |
| Insight de fonte nova | Adicionar | Aprendizados |
| Caso bem sucedido | Documentar | Casos de Sucesso |
| Erro cometido | Documentar | Casos de Fracasso |
| War Room participada | Resumir | Precedentes |
| Conflito resolvido | Registrar | Conflitos Resolvidos |
| Adaptação cultural | Documentar | Calibração Brasil |
| Interação significativa | Logar | Interações |

### O que NÃO registrar:

- Informações já presentes no Knowledge Base geral
- Dados sem aplicabilidade prática
- Opiniões não testadas
- Duplicatas

---

## FILTRO DE QUALIDADE

### Critérios para adicionar à memória:

```
NOVO CONHECIMENTO CANDIDATO
           │
           ▼
┌─────────────────────────┐
│ É novo (não duplicata)? │
└─────────────────────────┘
           │
      ┌────┴────┐
      ▼         ▼
     SIM       NÃO → DESCARTAR
      │
      ▼
┌─────────────────────────┐
│ É prático (aplicável)?  │
└─────────────────────────┘
           │
      ┌────┴────┐
      ▼         ▼
     SIM       NÃO → DESCARTAR
      │
      ▼
┌─────────────────────────┐
│ Tem fonte verificável?  │
└─────────────────────────┘
           │
      ┌────┴────┐
      ▼         ▼
     SIM       NÃO → MARCAR COMO [HIPÓTESE]
      │
      ▼
┌─────────────────────────┐
│ Relevante ao contexto   │
│ Brasil/Projeto?         │
└─────────────────────────┘
           │
      ┌────┴────┐
      ▼         ▼
     SIM       NÃO → ARQUIVAR (pode ser útil depois)
      │
      ▼
   ADICIONAR À MEMÓRIA
   com metadata completo
```

---

## USO DA MEMÓRIA

### Ao Responder Perguntas:

```
PERGUNTA RECEBIDA
        │
        ▼
1. CONSULTAR MEMÓRIA
   └─ Há padrão decisório?
   └─ Há precedente?
   └─ Há caso similar?
        │
        ▼
2. CONSULTAR KNOWLEDGE BASE
   └─ O que as fontes dizem?
   └─ Há conflito com memória?
        │
        ▼
3. CALIBRAR AO CONTEXTO
   └─ Adaptações Brasil necessárias?
   └─ Especificidades do projeto?
        │
        ▼
4. SINTETIZAR RESPOSTA
   └─ Combinar memória + knowledge
   └─ Citar fontes
   └─ Indicar confiança
        │
        ▼
5. ATUALIZAR MEMÓRIA (se aprendeu algo novo)
```

---

## INTEGRAÇÃO COM OUTROS SISTEMAS

| Sistema | Integração |
|---------|------------|
| **Knowledge Base** | Memória APONTA para, não duplica |
| **War Room** | Decisões viram precedentes na memória |
| **Agent Interaction** | Interações significativas são logadas |
| **Glossário** | Termos usados seguem definição padrão |

---

## CRIADO/ATUALIZADO

- **Data:** 2024-12-15
- **Versão:** 1.0.0
- **Propósito:** Definir estrutura de acumulação experiencial dos agentes
