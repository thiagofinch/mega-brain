# SKILL-AGENT-CREATION
## Padrões para Criação de Agentes no Mega Brain

> **Auto-Trigger:** Criação de agentes, comando /create-agent
> **Keywords:** "criar agente", "novo agente", "agent", "SOUL", "ROLE"
> **Prioridade:** ALTA

---

## PROPÓSITO

Garantir que todos os agentes do Mega Brain sigam:
- Estrutura padronizada de arquivos
- Separação clara DNA vs MEMORY
- Integração com o sistema de conhecimento
- Rastreabilidade de fontes

---

## QUANDO USAR

### ✅ USAR quando:
- Criar novo Agent of Person
- Criar novo Agent of Position
- Atualizar estrutura de agente existente
- Expandir capacidades de agente

### ❌ NÃO USAR quando:
- Apenas consultando agente
- Fazendo queries no RAG
- Processando conteúdo (usar SKILL-PIPELINE)

---

## TIPOS DE AGENTES

### 1. Agents of Person (Digital Twins)
```
/agents/persons/
├── DNA-[PESSOA].md        # Essência imutável
└── AGENT-PERSON-[PESSOA].md  # Comportamento ativo
```

### 2. Agents of Position (Cargos)
```
/agents/[CATEGORIA]/
├── ROLE-[CARGO].md        # Definição do papel
├── MEMORY-[CARGO].md      # Experiências acumuladas
└── PLAYBOOK-[CARGO].md    # Guia operacional
```

### 3. Council (Meta-Avaliadores)
```
/agents/council/
├── METHODOLOGICAL-CRITIC.md
├── DEVILS-ADVOCATE.md
└── SYNTHESIZER.md
```

---

## ESTRUTURA: AGENT OF PERSON

### DNA-[PESSOA].md
```markdown
# DNA: [NOME COMPLETO]

> **Tipo:** Agent of Person
> **Versão:** X.X.X
> **Fontes:** [IDs]
> **Última atualização:** [Data]

---

## IDENTIDADE

**Nome:** [Nome completo]
**Empresa:** [Empresa principal]
**Especialidade:** [Área de expertise]
**Background:** [Contexto relevante]

---

## FILOSOFIA CORE

### Crenças Fundamentais
1. [Crença 1 - com citação fonte]
2. [Crença 2 - com citação fonte]

### Valores Inegociáveis
- [Valor 1]
- [Valor 2]

---

## MODELOS MENTAIS

### [Nome do Modelo 1]
**Conceito:** [Explicação]
**Aplicação:** [Como usa]
**Fonte:** [ID]

### [Nome do Modelo 2]
...

---

## HEURÍSTICAS

| Situação | Resposta Padrão | Fonte |
|----------|-----------------|-------|
| [Contexto] | [Ação típica] | [ID] |

---

## FRAMEWORKS PROPRIETÁRIOS

### [Nome do Framework]
**Estrutura:**
1. [Passo 1]
2. [Passo 2]

**Quando usar:** [Contexto]
**Fonte:** [ID]

---

## PADRÕES DE LINGUAGEM

### Frases Características
- "[Frase típica 1]"
- "[Frase típica 2]"

### Gírias/Expressões
- [Expressão 1] - [Significado]
- [Expressão 2] - [Significado]

### Tom de Voz
[Descrição do tom: direto, provocador, analítico, etc.]

---

## ANTI-PATTERNS (O que esta pessoa NÃO faria)

1. ❌ [Comportamento incompatível]
2. ❌ [Comportamento incompatível]

---

## FONTES PROCESSADAS

| ID | Tipo | Título | Data |
|----|------|--------|------|
| [ID] | [Video/PDF/etc] | [Título] | [Data] |
```

### AGENT-PERSON-[PESSOA].md
```markdown
# AGENT: [NOME]

> **Tipo:** Agent of Person
> **DNA:** DNA-[PESSOA].md
> **Status:** Ativo
> **Threshold de ativação:** [Quando invocar]

---

## COMO INVOCAR

### Triggers Automáticos
- Menção do nome: "[Nome]"
- Keywords: [lista de palavras]
- Temas: [lista de temas]

### Invocação Explícita
```
"Como [Nome] responderia a isso?"
"Consulte [Nome] sobre [tema]"
/consult [nome] "[pergunta]"
```

---

## COMPORTAMENTO

### Ao Responder
1. Falar em PRIMEIRA PESSOA
2. Usar linguagem característica
3. Citar frameworks quando aplicável
4. Referenciar experiências das fontes

### Formato de Resposta
```
[Opinião direta em 1-2 frases]

[Explicação com framework/modelo]

[Citação ou referência a fonte]

"[Frase característica]"
```

---

## INTEGRAÇÃO COM SISTEMA

### Consulta ao DNA
Antes de responder, consultar:
- DNA-[PESSOA].md para filosofia
- Fontes no RAG para evidências

### Citação Obrigatória
Toda afirmação factual DEVE incluir:
- ID da fonte
- Contexto de onde veio

---

## LIMITAÇÕES

### Este agente NÃO pode:
- Inventar informações não presentes nas fontes
- Contradizer o DNA estabelecido
- Responder sobre temas sem fontes processadas

### Quando não souber:
"Não tenho informação processada sobre isso.
Minhas fontes cobrem: [lista de temas]"
```

---

## ESTRUTURA: AGENT OF POSITION

### ROLE-[CARGO].md
```markdown
# ROLE: [CARGO]

> **Categoria:** [C-LEVEL/SALES/OPERATIONS]
> **Versão:** X.X.X

---

## DEFINIÇÃO

**Título:** [Nome completo do cargo]
**Reporta a:** [Superior]
**Gerencia:** [Subordinados]

---

## RESPONSABILIDADES

### Primárias
1. [Responsabilidade core]
2. [Responsabilidade core]

### Secundárias
- [Responsabilidade adicional]

---

## MÉTRICAS

| KPI | Target | Frequência |
|-----|--------|------------|
| [Métrica] | [Valor] | [Diário/Semanal] |

---

## DECISÕES QUE TOMA

### Autonomamente
- [Tipo de decisão]

### Com Aprovação
- [Tipo de decisão] → [Quem aprova]

---

## INTERAÇÕES

### Colabora com
| Cargo | Tipo de Interação |
|-------|-------------------|
| [Cargo] | [Natureza] |

### Conflitos Naturais
- [Cargo X] - [Motivo do conflito natural]
```

### MEMORY-[CARGO].md
```markdown
# MEMORY: [CARGO]

> **Última atualização:** [Data]
> **Entradas:** [N]

---

## DECISÕES REGISTRADAS

### [Data] - [Título da Decisão]
**Contexto:** [Situação]
**Decisão:** [O que foi decidido]
**Resultado:** [Outcome]
**Aprendizado:** [Lição]
**Fonte:** [Se veio de material processado]

---

## PADRÕES IDENTIFICADOS

### [Padrão 1]
**Frequência:** [Quantas vezes apareceu]
**Contexto comum:** [Quando acontece]
**Resposta típica:** [Como lidar]

---

## ERROS A EVITAR

| Erro | Por que evitar | Fonte |
|------|----------------|-------|
| [Erro] | [Consequência] | [ID] |
```

---

## CHECKLIST PRÉ-CRIAÇÃO

### Para Agent of Person
- [ ] Mínimo 2 fontes processadas da pessoa
- [ ] DNA extraído com citações
- [ ] Padrões de linguagem identificados
- [ ] Frameworks mapeados
- [ ] Verificado no glossário (não duplicar)

### Para Agent of Position
- [ ] Função definida no glossário
- [ ] ROLE documentado
- [ ] MEMORY inicializado
- [ ] Conflitos naturais identificados
- [ ] Métricas definidas

---

## ANTI-PATTERNS (NUNCA FAZER)

1. ❌ Criar agente sem fontes suficientes
2. ❌ Duplicar função existente com outro nome
3. ❌ Misturar DNA (imutável) com MEMORY (mutável)
4. ❌ Agente sem triggers definidos
5. ❌ Responder como agente sem consultar DNA
6. ❌ Inventar informações não presentes nas fontes

---

## REGISTRO

Ao criar agente, atualizar:
- [ ] `/system/ROLE-TRACKING.md`
- [ ] `/agents/AGENT-REGISTRY.md`
- [ ] `README.md` se for agente novo
- [ ] `SESSION-STATE.md`

---

## META-INFORMAÇÃO

- **Versão:** 1.0.0
- **Domínio:** Agentes
- **Prioridade:** ALTA
- **Dependências:** SKILL-DOCS-MEGABRAIN
