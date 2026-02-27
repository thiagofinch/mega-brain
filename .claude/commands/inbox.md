---
description: Lista arquivos pendentes de processamento no INBOX
---

# INBOX - Verificar e Organizar Arquivos

> **Versão:** 2.0.0
> **Alias:** `/i`

---

## SINTAXE

```
/inbox [FLAGS]
```

| Flag | Descrição |
|------|-----------|
| (nenhuma) | Lista arquivos pendentes de processamento |
| `--pending` | Mesmo que padrão |
| `--all` | Lista todos (processados e pendentes) |
| `--person "Nome"` | Filtra por pessoa |
| `--organize` | Preview da auto-organização (dry-run) |
| `--organize --execute` | Executa auto-organização |

---

## EXECUÇÃO

### Step 1: Scan INBOX
```
SCAN /inbox/ recursively for .txt, .md, .pdf files

FOR each file:
  CHECK if file exists in CHUNKS-STATE.json (already processed)
  GET file metadata: size, date added, word count
  DETECT person from path
```

### Step 2: Categorizar
```
PENDING = files NOT in CHUNKS-STATE.json
PROCESSED = files IN CHUNKS-STATE.json

IF --all: show both
IF --person: filter by person
ELSE: show only PENDING
```

### Step 3: Gerar INBOX STATUS
```
═══════════════════════════════════════════════════════════════════════════════
                              INBOX STATUS
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📥 AGUARDANDO PROCESSAMENTO: {COUNT}

   1. {PERSON}/PODCASTS/{filename}.txt
      ├─ Adicionado: {relative_date} | ~{WORD_COUNT} palavras
      └─ Comando: /process-jarvis "inbox/{full_path}"

   2. {PERSON}/MASTERCLASS/{filename}.txt
      ├─ Adicionado: {relative_date} | ~{WORD_COUNT} palavras
      └─ Comando: /process-jarvis "inbox/{full_path}"

───────────────────────────────────────────────────────────────────────────────

📊 POR PESSOA:
   • {PERSON_1}: {COUNT} arquivo(s)
   • {PERSON_2}: {COUNT} arquivo(s)

⭐️ AÇÃO RÁPIDA
   Processar todos: /process-inbox --all
   Processar próximo: /process-inbox --next
   Processar pessoa: /process-inbox --person "Nome"

═══════════════════════════════════════════════════════════════════════════════
```

---

## OUTPUT SE VAZIO

```
═══════════════════════════════════════════════════════════════════════════════
                              INBOX STATUS
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

✅ INBOX LIMPO - Nenhum arquivo pendente de processamento

📊 TOTAIS:
   • Arquivos processados: {COUNT}
   • Pessoas no sistema: {COUNT}
   • Último processamento: {DATE}

⭐️ PRÓXIMOS PASSOS
   Adicionar material: /ingest [URL ou PATH]
   Ver estado do sistema: /system-digest

═══════════════════════════════════════════════════════════════════════════════
```

---

## OUTPUT COM --all FLAG

```
═══════════════════════════════════════════════════════════════════════════════
                         INBOX COMPLETO
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📥 PENDENTES: {COUNT}
   [lista como acima]

✅ PROCESSADOS: {COUNT}

   1. {PERSON}/PODCASTS/{filename}.txt
      ├─ Processado: {DATE} | Source ID: {ID}
      └─ Chunks: {N} | Insights: {N}

   2. {PERSON}/MASTERCLASS/{filename}.txt
      ├─ Processado: {DATE} | Source ID: {ID}
      └─ Chunks: {N} | Insights: {N}

═══════════════════════════════════════════════════════════════════════════════
```

---

## EXEMPLOS

```bash
# Ver pendentes
/inbox

# Ver tudo
/inbox --all

# Filtrar por pessoa
/inbox --person "Cole Gordon"

# Preview de organização (dry-run)
/inbox --organize

# Executar organização
/inbox --organize --execute
```

---

## 🤖 AUTO-ORGANIZAÇÃO

### Processo (7 Steps)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: SCAN                                                               │
│  └─ Listar todos os arquivos em inbox/ recursivamente                    │
│                                                                             │
│  STEP 2: DETECT SOURCE                                                      │
│  └─ Identificar pessoa/empresa pelo nome do arquivo ou conteúdo             │
│                                                                             │
│  STEP 3: DETECT TYPE                                                        │
│  └─ Classificar tipo de conteúdo (PODCASTS, COURSES, etc.)                  │
│                                                                             │
│  STEP 4: STANDARDIZE                                                        │
│  └─ Padronizar nome do arquivo (CAIXA ALTA, [youtube link])                 │
│                                                                             │
│  STEP 5: ORGANIZE                                                           │
│  └─ Mover para pasta correta: {PESSOA}/TIPO/                                │
│                                                                             │
│  STEP 6: HASH                                                               │
│  └─ Calcular MD5 para rastreabilidade                                       │
│                                                                             │
│  STEP 7: REGISTRY                                                           │
│  └─ Registrar em INBOX-REGISTRY.md com status NEW                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Detecção de Fonte

| Padrão no Nome/Conteúdo | Pessoa Detectada | Empresa |
|-------------------------|------------------|---------|
| hormozi, alex, acquisition | ALEX HORMOZI | ALEX HORMOZI |
| cole, gordon, closers | COLE GORDON | COLE GORDON |
| jordan, lee, ai business | JORDAN LEE | AI BUSINESS |
| jeremy, haynes, jeremy haynes program | JEREMY HAYNES | JEREMY HAYNES PROGRAM |
| sam, ovens, setterlun | SAM OVENS | SETTERLUN UNIVERSITY |

### Detecção de Tipo

| Padrão | Tipo Detectado |
|--------|----------------|
| podcast, episode, entrevista | PODCASTS |
| mastermind, summit, evento | MASTERMINDS |
| course, module, aula, treinamento | COURSES |
| blueprint, playbook, pdf, doc | BLUEPRINTS |
| vsl, sales letter, oferta | VSL |
| script, copy, template | SCRIPTS |

### Output do --organize (Dry-Run)

```
═══════════════════════════════════════════════════════════════════════════════
                         INBOX AUTO-ORGANIZE (PREVIEW)
                              {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📋 AÇÕES PLANEJADAS: {COUNT}

   1. 📁 MOVER: how-i-scaled-sales.txt
      ├─ De: inbox/
      ├─ Para: inbox/alex hormozi/PODCASTS/
      ├─ Renomear: HOW I SCALED MY SALES TEAM.txt
      └─ Detectado: Fonte=HORMOZI | Tipo=PODCAST

   2. 📁 CRIAR PASTA: inbox/JEREMY HAYNES (JEREMY HAYNES PROGRAM)/COURSES/
      └─ Motivo: Novo conteúdo detectado

   3. 📁 MOVER: client-accelerator-module1.txt
      ├─ De: inbox/
      ├─ Para: inbox/JEREMY HAYNES (JEREMY HAYNES PROGRAM)/COURSES/
      └─ Detectado: Fonte=JEREMY | Tipo=COURSE

───────────────────────────────────────────────────────────────────────────────

📊 RESUMO:
   • Arquivos a mover: {N}
   • Pastas a criar: {N}
   • Arquivos a renomear: {N}
   • Sem mudança: {N}

⚠️ NENHUMA AÇÃO EXECUTADA (dry-run)
   Para executar: /inbox --organize --execute

═══════════════════════════════════════════════════════════════════════════════
```

### Output do --organize --execute

```
═══════════════════════════════════════════════════════════════════════════════
                         INBOX AUTO-ORGANIZE (EXECUTADO)
                              {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

✅ AÇÕES EXECUTADAS: {COUNT}

   1. ✅ MOVIDO: how-i-scaled-sales.txt → ALEX HORMOZI/PODCASTS/
   2. ✅ CRIADA PASTA: JEREMY HAYNES (JEREMY HAYNES PROGRAM)/COURSES/
   3. ✅ MOVIDO: client-accelerator-module1.txt → JEREMY HAYNES/COURSES/

───────────────────────────────────────────────────────────────────────────────

📊 RESUMO:
   • Arquivos movidos: {N}
   • Pastas criadas: {N}
   • Arquivos renomeados: {N}
   • Erros: {N}

⭐️ PRÓXIMOS PASSOS:
   Ver status atualizado: /inbox
   Processar arquivos: /process-inbox --all

═══════════════════════════════════════════════════════════════════════════════
```

### Workflow Recomendado

| Passo | Comando | Descrição |
|-------|---------|-----------|
| 1 | `/inbox --organize` | Preview das ações (seguro) |
| 2 | Revisar output | Verificar se detecções estão corretas |
| 3 | `/inbox --organize --execute` | Executar organização |
| 4 | `/inbox` | Confirmar novo estado |
| 5 | `/process-inbox --all` | Processar arquivos organizados |

---

## INTEGRAÇÃO COM PIPELINE

Após organização, arquivos ficam prontos para Pipeline Jarvis:

```
inbox/{PESSOA}/{TIPO}/{arquivo}.txt
       │
       └──→ /process-jarvis "inbox/{path}"
              │
              └──→ processing/ (chunks, insights, narratives)
                      │
                      └──→ knowledge/dossiers/ (output final)
```
