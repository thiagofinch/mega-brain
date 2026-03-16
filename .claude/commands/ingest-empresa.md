---
description: Ingere material sobre a empresa do usuário e roteia para knowledge/business/inbox/
allowed-tools: Bash(cd:*), Bash(python:*), Read, Write, Edit, Glob, Grep
argument-hint: [path or URL] [--type TYPE]
---

# INGEST-EMPRESA - Ingestão de Material de Empresa (Bucket 2)

> **Versão:** 2.0.0
> **Pipeline:** Jarvis v2.1 → Routing para `knowledge/business/inbox/` → `bucket_processor.py workspace`
> **Bucket:** 2 (Business Intelligence) — 🔴

---

## PROPÓSITO

Processa material sobre a **empresa do usuário** (organograma, JDs, processos, KPIs) e roteia para `knowledge/business/inbox/`. O `bucket_processor.py` classifica e distribui para os subdirs corretos (`_org/`, `_team/`, `_finance/`, `_meetings/`, `_automations/`, `_tools/`).

**Diferença do `/ingest`:** O `/ingest` roteia para `knowledge/external/inbox/` (expert minds). O `/ingest-empresa` roteia para `knowledge/business/inbox/` (dados do negócio).

---

## SINTAXE

```
/ingest-empresa [SOURCE] [FLAGS]
```

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| Local path | Arquivo ou pasta | `/ingest-empresa ./organograma.pdf` |
| URL | Documento online | `/ingest-empresa https://docs.google.com/...` |
| Texto direto | Descrição inline | `/ingest-empresa "O time de vendas tem 3 closers..."` |

---

## FLAGS OPCIONAIS

```
--type ORG|TEAM|FINANCE|MEETINGS|AUTOMATIONS|TOOLS    # Força subdir de destino
--batch                                                 # Processa todos os arquivos de uma pasta
--process                                               # Após salvar, executa bucket_processor.py
```

---

## ROUTING RULES

O pipeline classifica cada material e roteia automaticamente para `knowledge/business/inbox/{subdir}/`:

| Tipo de Conteúdo | Detecta | Destino Inbox | Destino Final |
|------------------|---------|---------------|---------------|
| Organograma | "organograma", "org chart", "hierarquia", "headcount" | `knowledge/business/inbox/org/` | `workspace/_org/` |
| Team/RH | "cargo", "role", "JD", "contrata", "onboarding" | `knowledge/business/inbox/team/` | `workspace/_team/` |
| Financeiro | "MRR", "CAC", "LTV", "churn", "DRE", "receita", "budget" | `knowledge/business/inbox/finance/` | `workspace/_finance/` |
| Reuniões | "reunião", "meeting", "call", "standup", "daily", "ata" | `knowledge/business/inbox/meetings/` | `workspace/_meetings/` |
| Automações | "automação", "n8n", "zapier", "workflow", "integração" | `knowledge/business/inbox/automations/` | `workspace/_automations/` |
| Ferramentas | "CRM", "ferramenta", "software", "clickup", "slack" | `knowledge/business/inbox/tools/` | `workspace/_tools/` |

---

## EXECUÇÃO

### Step 1: Identificar Fonte e Carregar Conteúdo

```
IF $SOURCE is path:
  READ file content
ELSE IF $SOURCE is URL:
  FETCH content (Google Docs, PDF, etc.)
ELSE IF $SOURCE is text:
  USE as inline content
```

### Step 2: Classificar Tipo

```
IF --type provided:
  SUBDIR = $type_flag (lowercase)
ELSE:
  ANALYZE content keywords → match routing table above
  IF ambiguous:
    ASK user: "Este material parece ser sobre [X]. Confirma?"
```

### Step 3: Salvar no Inbox

```
DESTINATION = knowledge/business/inbox/{SUBDIR}/{FILENAME}
CREATE directory if not exists
WRITE content to DESTINATION
```

### Step 4: Processar (se --process)

```
IF --process flag:
  python3 core/intelligence/pipeline/bucket_processor.py workspace
```

### Step 5: Report

```
════════════════════════════════════════════════════════════════════════════════
                    🔴 INGEST-EMPRESA REPORT
                    {TIMESTAMP}
════════════════════════════════════════════════════════════════════════════════

  MATERIAL PROCESSADO
   Fonte: {SOURCE}
   Tipo detectado: {TYPE}

  DESTINO
   Inbox: knowledge/business/inbox/{SUBDIR}/{FILENAME}
   Final: workspace/_{SUBDIR}/{FILENAME} (após bucket_processor)

  PRÓXIMA ETAPA
   - Processar inbox: python3 core/intelligence/pipeline/bucket_processor.py workspace
   - Ver status: python3 core/intelligence/pipeline/bucket_processor.py
   - Ingerir mais: /ingest-empresa [próximo arquivo]

════════════════════════════════════════════════════════════════════════════════
```

---

## EXEMPLOS

```bash
# Processar organograma
/ingest-empresa ./organograma-empresa.pdf

# Processar JD de uma vaga
/ingest-empresa ./vaga-closer.txt --type team

# Processar KPIs do time
/ingest-empresa "O closer precisa fazer 5 calls/dia, converter 30%..."

# Batch: processar pasta inteira
/ingest-empresa ./docs-empresa/ --batch

# Ingerir e já processar via bucket_processor
/ingest-empresa ./ata-reuniao.md --process
```
