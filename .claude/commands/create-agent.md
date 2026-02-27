---
description: Cria novo agente seguindo padrão aios-core com layers e persona-registry
argument-hint: [ID] --layer [L0|L1|L2|L3|L4|SUB] --name "..." --role "..." [--element Fire|Earth|Air|Water]
---

# CREATE-AGENT - Agent Factory (aios-core Pattern)

> **Versão:** 2.0.0
> **Agent-Creator:** `core/jarvis/agent-creator/`
> **Registry:** `agents/persona-registry.yaml`

---

## SINTAXE

```
/create-agent [ID] --layer [LAYER] --name "..." --role "..."
```

| Flag | Descrição | Obrigatório |
|------|-----------|-------------|
| `--layer` | L0, L1, L2, L3, L4, SUB | ✅ |
| `--name` | Display name | ✅ |
| `--role` | Role description | ✅ |
| `--element` | Fire, Earth, Air, Water | ❌ |
| `--source` | Origin (pipeline source_id) | ❌ |

## LAYERS (aios-core pattern)

| Layer | Folder | Description | Trigger |
|-------|--------|-------------|---------|
| L0 | `core/jarvis/` | System agents | Manual |
| L1 | `agents/conclave/` | Conclave (debate) | `/conclave` |
| L2 | `agents/boardroom/` | C-Level executives | Threshold ≥10 |
| L3 | `agents/minds/` | Expert mind clones | Pipeline Phase 5.2 |
| L4 | `agents/cargo/` | Operational roles | Threshold ≥5 |
| SUB | `.claude/jarvis/sub-agents/` | JARVIS operatives | Keywords |

---

## PRÉ-REQUISITOS

```
⛔ ANTES DE CRIAR:
[ ] Role atingiu threshold (>=10 menções) em role-tracking.md
[ ] Não existe sinônimo no glossário
[ ] Categoria definida (SALES, OPERATIONS, C-LEVEL)
```

---

## EXECUÇÃO

### Step 1: Validar Role
```
READ /agents/DISCOVERY/role-tracking.md

FIND role entry for {NOME}

IF mentions < 10:
  ⚠️ "Role não atingiu threshold. Menções: {N}/10"
  ASK: "Criar mesmo assim? [s/N]"

IF role already has agent:
  ⛔ "Agente já existe: /agents/{CAT}/AGENT-{NOME}.md"
  EXIT
```

### Step 2: Coletar Informações do Role-Tracking
```
FROM role-tracking.md, extract:
  - All sources mentioning this role
  - All responsibilities mentioned
  - All contexts of use
  - Related roles

COMPILE into KNOWLEDGE_BASE for agent
```

### Step 3: Definir Estrutura
```
CATEGORY = --category value
PARENT = --sub-of value (or null)
EXPERTISE = --expertise value (or infer from role-tracking)

AGENT_PATH = /agents/{CATEGORY}/AGENT-{NOME}.md
MEMORY_PATH = /agents/{CATEGORY}/MEMORY-{NOME}.md
```

### Step 4: Criar AGENT-*.md
```
TEMPLATE:

# AGENT-{NOME}

> **Versão:** 1.0.0
> **Categoria:** {CATEGORY}
> **Hierarquia:** Reporta a {PARENT}
> **Criado:** {DATE}

---

## IDENTIDADE

Você é o {NOME}, especialista em {EXPERTISE_LIST}.

---

## EXPERTISE

### {EXPERTISE_1}
Este agente domina {EXPERTISE_1} e aplica naturalmente em:
- {contexto_1}
- {contexto_2}

[Populated from role-tracking insights]

---

## QUANDO SOU ACIONADO

- {situação_1}
- {situação_2}
- {situação_3}

---

## NAVEGAÇÃO

### Eu consulto:
- {DOSSIERs relevantes}
- {MEMORYs que informam}

### Eu escalo para:
- {Agentes superiores}

### Eu colaboro com:
- {Agentes do mesmo nível}

---

## PROTOCOLS

| Protocolo | Propósito |
|-----------|-----------|
| EPISTEMIC-PROTOCOL.md | Anti-alucinação |
| AGENT-INTERACTION.md | Comunicação entre agentes |

---

## REGRA DE OPERAÇÃO

```
SEMPRE:
1. Separar FATO de RECOMENDAÇÃO
2. Incluir nível de CONFIANÇA
3. Citar FONTE quando disponível
4. Declarar LIMITAÇÕES
```
```

### Step 5: Criar MEMORY-*.md
```
TEMPLATE:

# MEMORY-{NOME}

> **Última atualização:** {DATE}
> **Fontes incorporadas:** {SOURCE_LIST}

---

## TEAM AGREEMENT

### Missão
{Derived from role-tracking}

### Relacionamentos
- **Reporta a:** {PARENT}
- **Colabora com:** {PEERS}
- **Gerencia:** {SUBORDINATES if any}

---

## KNOWLEDGE BASE ACUMULADA

### Fontes
| Source ID | Pessoa | Data | Insights |
|-----------|--------|------|----------|
| {ID} | {PERSON} | {DATE} | {N} |

### Frameworks Conhecidos
{List from role-tracking insights}

### Métricas de Referência
{List from role-tracking insights}

---

## HISTÓRICO DE DECISÕES

[Seção para decisões importantes tomadas por este agente]
```

### Step 6: Atualizar Role-Tracking
```
UPDATE /agents/DISCOVERY/role-tracking.md

MARK role as: ✅ CRIADO
ADD: Agente: /agents/{CAT}/AGENT-{NOME}.md
ADD: Criado em: {DATE}
```

### Step 7: Trigger SUA-EMPRESA (Cascata de Arquivos Humanos)
```
# CORREÇÃO ARQUITETURAL: Criar paridade Agent IA ↔ Role Humano
# Todo agente IA DEVE ter correspondente sua-empresa para ecossistema [SUA EMPRESA]

LOG: "Iniciando cascata sua-empresa para {NOME}..."

═══════════════════════════════════════════════════════════════════════════════
7.1 - CRIAR ROLE-*.md (Cargo Humano)
═══════════════════════════════════════════════════════════════════════════════

ROLE_PATH = /agents/sua-empresa/roles/ROLE-{NOME}.md

IF NOT EXISTS ROLE_PATH:
  GENERATE from template:

  # ROLE: {NOME}

  > **Versão:** 1.0.0
  > **Agente IA correspondente:** AGENT-{NOME}.md
  > **Status:** 🟡 Planejado
  > **Criado:** {DATE}

  ---

  ## MISSÃO

  {Derived from AGENT expertise}

  ---

  ## RESPONSABILIDADES

  {Derived from role-tracking insights}

  ---

  ## MÉTRICAS DE SUCESSO

  | Métrica | Target | Frequência |
  |---------|--------|------------|
  | {TBD} | {TBD} | {TBD} |

  ---

  ## RELACIONAMENTOS

  - **Reporta a:** {PARENT}
  - **Colabora com:** {PEERS}

  ---

  ## FONTES DE CONHECIMENTO

  [FONTE: {SOURCE_IDS}] → Ver MEMORY-{NOME}.md

  WRITE ROLE_PATH
  LOG: "ROLE criado: {ROLE_PATH}"

═══════════════════════════════════════════════════════════════════════════════
7.2 - CRIAR JD-*.md (Job Description)
═══════════════════════════════════════════════════════════════════════════════

JD_PATH = /agents/sua-empresa/jds/JD-{NOME}.md

IF NOT EXISTS JD_PATH:
  GENERATE from template:

  # Job Description: {NOME}

  > **Versão:** 1.0.0
  > **Status:** 🟡 Draft
  > **Criado:** {DATE}

  ---

  ## SOBRE O CARGO

  {Síntese do role baseada em insights acumulados}

  ---

  ## REQUISITOS

  ### Obrigatórios
  - {TBD - extrair de insights}

  ### Desejáveis
  - {TBD}

  ---

  ## RESPONSABILIDADES PRINCIPAIS

  {Derived from AGENT expertise and role-tracking}

  ---

  ## PERFIL COMPORTAMENTAL

  {Based on patterns from source experts}

  ---

  ## COMPENSAÇÃO

  Ver: ROLE-{NOME}.md → Seção Métricas

  WRITE JD_PATH
  LOG: "JD criado: {JD_PATH}"

═══════════════════════════════════════════════════════════════════════════════
7.3 - CRIAR MEMORY-*.md (SUA-EMPRESA)
═══════════════════════════════════════════════════════════════════════════════

ORG_MEMORY_PATH = /agents/sua-empresa/memory/MEMORY-{NOME}.md

IF NOT EXISTS ORG_MEMORY_PATH:
  GENERATE from template:

  # MEMORY: {NOME} (SUA-EMPRESA)

  > **Última atualização:** {DATE}
  > **Agente IA:** AGENT-{NOME}.md
  > **Fontes:** {SOURCE_LIST}

  ---

  ## CONHECIMENTO ACUMULADO

  ### Insights Fundacionais
  {Copiar de MEMORY-{NOME}.md do agente IA}

  ### Decisões Documentadas
  [Seção para decisões tomadas sobre este cargo]

  ### Precedentes
  [Seção para situações resolvidas que informam futuras]

  WRITE ORG_MEMORY_PATH
  LOG: "MEMORY sua-empresa criado: {ORG_MEMORY_PATH}"

═══════════════════════════════════════════════════════════════════════════════
7.4 - ATUALIZAR AGENT-ROLE-MAPPING.md
═══════════════════════════════════════════════════════════════════════════════

MAPPING_PATH = /agents/sua-empresa/AGENT-ROLE-MAPPING.md

READ MAPPING_PATH
LOCATE table "## Mapeamento Agent IA ↔ Role Humano"
APPEND row:
| AGENT-{NOME} | ROLE-{NOME} | JD-{NOME} | MEMORY-{NOME} | ✅ Pareado | {DATE} |

WRITE MAPPING_PATH
LOG: "Mapping atualizado: AGENT-{NOME} ↔ ROLE-{NOME}"

═══════════════════════════════════════════════════════════════════════════════
7.5 - ATUALIZAR ORG-CHART.md (se aplicável)
═══════════════════════════════════════════════════════════════════════════════

ORG_CHART_PATH = /agents/ORG-LIVE/ORG/ORG-CHART.md

IF EXISTS ORG_CHART_PATH:
  READ ORG_CHART_PATH

  # Adicionar novo cargo na hierarquia
  IF {PARENT} exists in chart:
    ADD {NOME} as subordinate of {PARENT}
  ELSE:
    ADD {NOME} to appropriate level based on CATEGORY

  WRITE ORG_CHART_PATH
  LOG: "ORG-CHART atualizado com {NOME}"

ORG_LIVE_STATS = {
  role_created: ROLE_PATH,
  jd_created: JD_PATH,
  memory_created: ORG_MEMORY_PATH,
  mapping_updated: true,
  org_chart_updated: EXISTS(ORG_CHART_PATH)
}

LOG: "Cascata ORG-LIVE completa: {stats}"
```

### Step 8: Gerar AGENT CREATION LOG
```
═══════════════════════════════════════════════════════════════════════════════
                         AGENT CREATION LOG
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

✅ AGENTE CRIADO: {NOME}

📁 ARQUIVOS AGENT IA:
   AGENT: /agents/{CATEGORY}/AGENT-{NOME}.md
   MEMORY: /agents/{CATEGORY}/MEMORY-{NOME}.md

🏢 ARQUIVOS ORG-LIVE (Cascata):
   ROLE: /agents/ORG-LIVE/ROLES/ROLE-{NOME}.md
   JD: /agents/ORG-LIVE/JDS/JD-{NOME}.md
   MEMORY: /agents/ORG-LIVE/MEMORY/MEMORY-{NOME}.md
   MAPPING: ✅ Atualizado
   ORG-CHART: {status}

📊 BASEADO EM:
   Menções: {N} (threshold: 10)
   Fontes: {SOURCE_LIST}
   Expertise: {EXPERTISE_LIST}

🔗 HIERARQUIA:
   Reporta a: {PARENT}
   Categoria: {CATEGORY}

⭐️ PRÓXIMOS PASSOS:
   1. Revisar AGENT-*.md e ajustar expertise se necessário
   2. Revisar JD-*.md e completar requisitos
   3. Processar mais fontes para enriquecer MEMORYs
   4. Testar agente com consulta

═══════════════════════════════════════════════════════════════════════════════
```

---

## EXEMPLOS

```bash
# Criar agente de vendas
/create-agent APPOINTMENT-SETTER --category SALES --sub-of SALES-MANAGER

# Criar com expertise específica
/create-agent APPOINTMENT-SETTER --category SALES --expertise "Qualificação, Agendamento, First Contact"

# Criar agente C-Level
/create-agent VP-SALES --category C-LEVEL --sub-of CRO
```

---

## LOG

Append to `/logs/AUDIT/audit.jsonl`:
```json
{
  "timestamp": "ISO",
  "operation": "CREATE_AGENT",
  "agent_name": "{NOME}",
  "category": "{CATEGORY}",
  "parent": "{PARENT}",
  "mentions_at_creation": {N},
  "status": "SUCCESS"
}
```
