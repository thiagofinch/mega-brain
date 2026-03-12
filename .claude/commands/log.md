---
description: Visualiza logs especificos (execution, digest, roles, enrichment, audit)
argument-hint: [execution|digest|roles|enrichment|audit] [--source ID] [--full]
---

# LOG - Visualizar Logs Específicos

> **Versão:** 1.0.0

---

## SINTAXE

```
/log [TIPO] [FLAGS]
```

| Tipo | Descrição |
|------|-----------|
| `execution` | Último Execution Report |
| `execution --source JH001` | Execution Report de source específico |
| `digest` | Último System Digest |
| `roles` | Último Role-Tracking Report |
| `enrichment` | Último Agent Enrichment Report |
| `audit` | Audit log (últimas 50 operações) |
| `audit --full` | Audit log completo |

---

## EXECUÇÃO

### execution
```
IF --source provided:
  FIND /logs/EXECUTION/EXEC-{SOURCE_ID}-*.md
ELSE:
  FIND most recent /logs/EXECUTION/EXEC-*.md

READ and DISPLAY file content
```

### digest
```
FIND most recent /logs/DIGEST/DIGEST-*.md
READ and DISPLAY file content

IF none found:
  -> "Nenhum digest encontrado. Execute /system-digest para gerar."
```

### roles
```
READ /agents/DISCOVERY/role-tracking.md
DISPLAY role tracking table
HIGHLIGHT:
  - Roles at threshold (>=10)
  - Roles approaching (>=5)
```

### enrichment
```
FIND most recent Agent Enrichment log in /logs/EXECUTION/
DISPLAY enrichment details
```

### audit
```
READ /logs/AUDIT/audit.jsonl

IF --full:
  DISPLAY all entries
ELSE:
  DISPLAY last 50 entries

FORMAT as table:
| Timestamp | Operation | Source | Status |
|-----------|-----------|--------|--------|
```

---

## OUTPUT: audit

```
═══════════════════════════════════════════════════════════════════════════════
                              AUDIT LOG
                    Últimas {N} operações
═══════════════════════════════════════════════════════════════════════════════

┌──────────────────────┬────────────────────┬──────────┬─────────┐
│ Timestamp            │ Operation          │ Source   │ Status  │
├──────────────────────┼────────────────────┼──────────┼─────────┤
│ 2024-12-18 23:45:00  │ PIPELINE_COMPLETE  │ JH001    │ SUCCESS │
│ 2024-12-18 23:30:00  │ INGEST             │ JH001    │ SUCCESS │
│ 2024-12-18 22:15:00  │ PIPELINE_COMPLETE  │ CG004    │ SUCCESS │
│ 2024-12-18 21:00:00  │ SYSTEM_INIT        │ -        │ SUCCESS │
└──────────────────────┴────────────────────┴──────────┴─────────┘

📊 ESTATÍSTICAS:
   Total operações: {N}
   Sucesso: {N} ({%})
   Falhas: {N} ({%})
   Período: {FIRST_DATE} - {LAST_DATE}

═══════════════════════════════════════════════════════════════════════════════
```

---

## OUTPUT: roles

```
═══════════════════════════════════════════════════════════════════════════════
                         ROLE-TRACKING STATUS
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

🔴 THRESHOLD ATINGIDO (>=10 menções):
┌───────────────────────┬──────────┬─────────────────────┬────────┐
│ Role                  │ Menções  │ Fontes              │ Status │
├───────────────────────┼──────────┼─────────────────────┼────────┤
│ Appointment Setter    │ 12       │ CG001, CG002, JH001 │ CRIAR  │
└───────────────────────┴──────────┴─────────────────────┴────────┘

🟡 MONITORAR (5-9 menções):
┌───────────────────────┬──────────┬─────────────────────┬────────┐
│ Role                  │ Menções  │ Fontes              │ Status │
├───────────────────────┼──────────┼─────────────────────┼────────┤
│ Revenue Operations    │ 7        │ JH001, CG003        │ WATCH  │
│ Sales Enablement      │ 5        │ CG001               │ WATCH  │
└───────────────────────┴──────────┴─────────────────────┴────────┘

✅ AGENTES JÁ CRIADOS:
   CLOSER (20+), BDR (15+), SDS (12+), SALES-MANAGER (40+), ...

═══════════════════════════════════════════════════════════════════════════════
```

---

## EXEMPLOS

```bash
# Ver último execution report
/log execution

# Ver execution de fonte específica
/log execution --source CG001

# Ver último digest
/log digest

# Ver role tracking
/log roles

# Ver audit completo
/log audit --full
```
