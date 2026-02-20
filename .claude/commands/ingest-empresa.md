---
description: Ingere material sobre a empresa do usuário e roteia para agents/sua-empresa/
allowed-tools: Bash(cd:*), Bash(python:*), Read, Write, Edit, Glob, Grep
argument-hint: [path or URL] [--type TYPE]
---

# INGEST-EMPRESA - Ingestão de Material de Empresa

> **Versão:** 1.0.0
> **Pipeline:** Jarvis v2.1 → Routing para `agents/sua-empresa/`

---

## PROPÓSITO

Processa material sobre a **empresa do usuário** (organograma, JDs, processos, KPIs) e roteia o output para a estrutura `agents/sua-empresa/`.

**Diferença do `/ingest`:** O `/ingest` roteia para `knowledge/` (expert minds). O `/ingest-empresa` roteia para `agents/sua-empresa/` (dados organizacionais).

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
--type ORG|ROLE|JD|OPS|METRICS|SOW    # Força tipo de routing
--batch                                 # Processa todos os arquivos de uma pasta
```

---

## ROUTING RULES

O pipeline classifica cada material e roteia automaticamente:

| Tipo de Conteúdo | Detecta | Destino |
|------------------|---------|---------|
| Organograma | "organograma", "org chart", "hierarquia", "estrutura" | `agents/sua-empresa/org/` |
| Role (Cargo) | "cargo", "role", "função", "responsabilidades do" | `agents/sua-empresa/roles/` |
| Job Description | "vaga", "job description", "JD", "contratação", "requisitos" | `agents/sua-empresa/jds/` |
| Operações | "processo", "ritual", "daily", "standup", "ferramenta", "CRM" | `agents/sua-empresa/operations/` |
| Métricas | "KPI", "meta", "métrica", "dashboard", "OKR", "resultado" | `agents/sua-empresa/metrics/` |
| Scope of Work | "escopo", "SOW", "scope of work", "entregáveis" | `agents/sua-empresa/sow/` |

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
  TYPE = $type_flag
ELSE:
  ANALYZE content keywords → match routing table above
  IF ambiguous:
    ASK user: "Este material parece ser sobre [X]. Confirma?"
```

### Step 3: Extrair e Estruturar

```
BASED ON TYPE:

ORG → Extract:
  - Hierarquia (quem reporta a quem)
  - Departamentos
  - Headcount
  - Scaling triggers
  FORMAT: ORG-{COMPANY-NAME}.md

ROLE → Extract:
  - Nome do cargo
  - Missão
  - Responsabilidades
  - KPIs
  - Competências
  FORMAT: ROLE-{CARGO-NAME}.md

JD → Extract:
  - Informações da vaga
  - Requisitos obrigatórios/diferenciais
  - Processo seletivo
  FORMAT: JD-{CARGO-NAME}.md

OPS → Extract:
  - Nome do processo/ritual
  - Frequência
  - Participantes
  - Passos
  FORMAT: {PROCESS-NAME}.md

METRICS → Extract:
  - KPIs por cargo/departamento
  - Metas e benchmarks
  - Frequência de medição
  FORMAT: KPI-{AREA}.md

SOW → Extract:
  - Cargo
  - Entregáveis
  - SLAs
  - Ferramentas
  FORMAT: SOW-{CARGO-NAME}.md
```

### Step 4: Salvar no Destino

```
DESTINATION = agents/sua-empresa/{TYPE_FOLDER}/{FILENAME}
WRITE structured content to DESTINATION
```

### Step 5: Report

```
====================================================================
                    INGEST-EMPRESA REPORT
                    {TIMESTAMP}
====================================================================

  MATERIAL PROCESSADO
   Fonte: {SOURCE}
   Tipo detectado: {TYPE}

  DESTINO
   Path: agents/sua-empresa/{TYPE_FOLDER}/{FILENAME}

  CONTEUDO EXTRAIDO
   {Resumo do que foi extraído - 3-5 bullets}

  PROXIMA ETAPA
   - Revisar: Read agents/sua-empresa/{TYPE_FOLDER}/{FILENAME}
   - Processar mais: /ingest-empresa [próximo arquivo]
   - Ver estrutura: /agents sua-empresa

====================================================================
```

---

## REGRAS IMPORTANTES

1. **Somente indivíduos identificados viram agentes** — temas viram dossiês, não agentes
2. **Material sobre pessoa** → roteia para `roles/` ou `jds/` (não para `agents/persons/`)
3. **Material sobre processo/operação** → roteia para `operations/`
4. **Material sobre organograma** → roteia para `org/`
5. **Material sobre métricas/KPIs** → roteia para `metrics/`
6. **Na dúvida, perguntar** ao usuário o tipo correto

---

## EXEMPLOS

```bash
# Processar organograma
/ingest-empresa ./organograma-empresa.pdf

# Processar JD de uma vaga
/ingest-empresa ./vaga-closer.txt --type JD

# Processar KPIs do time
/ingest-empresa "O closer precisa fazer 5 calls/dia, converter 30%..."

# Batch: processar pasta inteira
/ingest-empresa ./docs-empresa/ --batch
```
