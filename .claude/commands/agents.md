---
description: Mostra status dos agentes e suas MEMORYs
---

# AGENTS - Status dos Agentes

> **Versão:** 1.0.0
> **Alias:** `/a`

---

## SINTAXE

```
/agents [FLAGS]
```

| Flag | Descrição |
|------|-----------|
| (nenhuma) | Lista todos agentes e status |
| `--outdated` | Lista agentes com MEMORY desatualizada (>3 dias) |
| `--knowledge "pessoa"` | Quais agentes têm conhecimento sobre pessoa |
| `--category SALES` | Filtra por categoria (SALES, C-LEVEL, OPERATIONS) |

---

## EXECUÇÃO

### Step 1: Scan Agentes
```
SCAN /agents/ for AGENT-*.md and MEMORY-*.md files

FOR each agent:
  READ AGENT-*.md header for version, last_updated
  READ MEMORY-*.md for:
    - Last update date
    - Persons mentioned
    - Sources included
  CALCULATE staleness (days since update)
```

### Step 2: Verificar Role-Tracking
```
READ /agents/DISCOVERY/role-tracking.md

IDENTIFY:
  - Roles at threshold (>=10 mentions) without agent
  - Roles approaching threshold (>=5 mentions)
```

### Step 3: Gerar AGENTS STATUS
```
═══════════════════════════════════════════════════════════════════════════════
                              AGENTS STATUS
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

🤖 AGENTES ATIVOS: {TOTAL_COUNT}

C-LEVEL:
   CRO      │ MEMORY atualizada: {DATE} │ Conhece: {N} pessoas
   CFO      │ MEMORY atualizada: {DATE} │ Conhece: {N} pessoas
   CMO      │ MEMORY atualizada: {DATE} │ Conhece: {N} pessoas
   COO      │ MEMORY atualizada: {DATE} │ Conhece: {N} pessoas

SALES:
   CLOSER           │ MEMORY: {DATE} │ {N} pessoas │ v{VERSION}
   BDR              │ MEMORY: {DATE} │ {N} pessoas │ v{VERSION}
   SDS              │ MEMORY: {DATE} │ {N} pessoas │ v{VERSION}
   LNS              │ MEMORY: {DATE} │ {N} pessoas │ v{VERSION}
   SALES-MANAGER    │ MEMORY: {DATE} │ {N} pessoas │ v{VERSION}
   SALES-LEAD       │ MEMORY: {DATE} │ {N} pessoas │ v{VERSION}
   SALES-COORDINATOR│ MEMORY: {DATE} │ {N} pessoas │ v{VERSION}
   CUSTOMER-SUCCESS │ MEMORY: {DATE} │ {N} pessoas │ v{VERSION}

───────────────────────────────────────────────────────────────────────────────

⚠️ DESATUALIZADOS (>3 dias):
   {AGENT_1}, {AGENT_2} precisam de refresh

🚨 SUGERIDOS PARA CRIAÇÃO:
   🔴 {ROLE_NAME} ({N} menções - threshold atingido)
   🟡 {ROLE_NAME} ({N} menções - monitorar)

═══════════════════════════════════════════════════════════════════════════════
```

---

## OUTPUT COM --outdated

```
═══════════════════════════════════════════════════════════════════════════════
                         AGENTES DESATUALIZADOS
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

⚠️ AGENTES COM MEMORY > 3 DIAS:

   CFO
   ├─ Última atualização: {DATE} ({N} dias atrás)
   ├─ Conhece: {PERSONS_LIST}
   └─ Faltam fontes: {SOURCES_NOT_INCLUDED}

   COO
   ├─ Última atualização: {DATE} ({N} dias atrás)
   ├─ Conhece: {PERSONS_LIST}
   └─ Faltam fontes: {SOURCES_NOT_INCLUDED}

⭐️ AÇÃO SUGERIDA
   Atualizar MEMORYs: executar /process-jarvis para novas fontes
   Ou: sync manual das fontes faltantes

═══════════════════════════════════════════════════════════════════════════════
```

---

## OUTPUT COM --knowledge "pessoa"

```
═══════════════════════════════════════════════════════════════════════════════
                    CONHECIMENTO SOBRE: {PESSOA}
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📚 AGENTES QUE CONHECEM {PESSOA}:

   CLOSER
   ├─ Fontes: {SOURCE_IDS}
   ├─ Insights: {N} (HIGH: {N}, MEDIUM: {N}, LOW: {N})
   └─ Frameworks: {LIST}

   CRO
   ├─ Fontes: {SOURCE_IDS}
   ├─ Insights: {N}
   └─ Frameworks: {LIST}

📄 DOSSIER DISPONÍVEL:
   /knowledge/dossiers/persons/DOSSIER-{PESSOA}.md

═══════════════════════════════════════════════════════════════════════════════
```

---

## EXEMPLOS

```bash
# Ver todos agentes
/agents

# Ver desatualizados
/agents --outdated

# Quem conhece Cole Gordon?
/agents --knowledge "Cole Gordon"

# Apenas agentes de vendas
/agents --category SALES
```
