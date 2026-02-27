---
description: Mostra status dos dossies de pessoas e temas
argument-hint: [--persons] [--themes] [--incomplete] [--person "Name"]
---

# DOSSIERS - Status dos Dossiês

> **Versão:** 1.0.0

---

## SINTAXE

```
/dossiers [FLAGS]
```

| Flag | Descrição |
|------|-----------|
| (nenhuma) | Lista todos dossiers |
| `--persons` | Apenas dossiers de pessoas |
| `--themes` | Apenas dossiers de temas |
| `--incomplete` | Dossiers criados por atalho (sem rastreabilidade) |
| `--person "Nome"` | Dossier específico |

---

## EXECUÇÃO

### Step 1: Scan Dossiers
```
SCAN /knowledge/dossiers/persons/ for DOSSIER-*.md
SCAN /knowledge/dossiers/THEMES/ for DOSSIER-*.md

FOR each dossier:
  READ header for: last_updated, sources, version
  COUNT sections
  CHECK for rastreabilidade (chunk_refs present)
```

### Step 2: Verificar Integridade
```
FOR each dossier:
  VERIFY sources exist in CHUNKS-STATE.json
  VERIFY insights_included are valid
  FLAG if missing rastreabilidade
```

### Step 3: Gerar DOSSIERS STATUS
```
═══════════════════════════════════════════════════════════════════════════════
                              DOSSIERS STATUS
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📁 TOTAIS:
   Pessoas: {N} dossiers
   Temas: {N} dossiers

───────────────────────────────────────────────────────────────────────────────

👤 DOSSIERS DE PESSOAS:

   DOSSIER-Cole-Gordon.md
   ├─ Atualizado: {DATE} │ Versão: v{N}
   ├─ Fontes: CG001, CG002, CG003, CG004
   ├─ Chunks: {N} │ Insights: {N}
   └─ Status: ✅ COMPLETO

   DOSSIER-Jordan-Lee.md
   ├─ Atualizado: {DATE} │ Versão: v{N}
   ├─ Fontes: JL001-JL007, CJ001, MT001
   ├─ Chunks: {N} │ Insights: {N}
   └─ Status: ✅ COMPLETO

   DOSSIER-Jeremy-Haynes.md
   ├─ Atualizado: {DATE} │ Versão: v{N}
   ├─ Fontes: JH001
   ├─ Chunks: {N} │ Insights: {N}
   └─ Status: ✅ COMPLETO

───────────────────────────────────────────────────────────────────────────────

📚 DOSSIERS DE TEMAS:

   DOSSIER-Processo-Vendas.md
   ├─ Atualizado: {DATE}
   ├─ Pessoas: Cole Gordon, Jordan Lee, Jeremy Haynes
   └─ Status: ✅ COMPLETO

   DOSSIER-Comissionamento.md
   ├─ Atualizado: {DATE}
   ├─ Pessoas: Cole Gordon
   └─ Status: ✅ COMPLETO

═══════════════════════════════════════════════════════════════════════════════
```

---

## OUTPUT COM --incomplete

```
═══════════════════════════════════════════════════════════════════════════════
                         DOSSIERS INCOMPLETOS
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

⚠️ DOSSIERS SEM RASTREABILIDADE COMPLETA:

   DOSSIER-{NAME}.md
   ├─ Problema: Criado por atalho (sem passar pelo Pipeline Jarvis)
   ├─ Faltam: chunk_refs, source_ids
   └─ Sugestão: Reprocessar fonte original

   DOSSIER-{NAME}.md
   ├─ Problema: insights_included referencia chunks inexistentes
   ├─ Chunks órfãos: {LIST}
   └─ Sugestão: Reconstruir via /rebuild-state

═══════════════════════════════════════════════════════════════════════════════
```

---

## OUTPUT COM --person "Nome"

```
═══════════════════════════════════════════════════════════════════════════════
                    DOSSIER: {PESSOA}
                         {TIMESTAMP}
═══════════════════════════════════════════════════════════════════════════════

📄 ARQUIVO: /knowledge/dossiers/persons/DOSSIER-{PESSOA}.md

📊 METADADOS:
   Versão: v{N}
   Última atualização: {DATE}
   Fontes: {SOURCE_IDS}

📚 CONTEÚDO:
   Insights: {N} total ({HIGH} HIGH, {MED} MEDIUM, {LOW} LOW)
   Frameworks: {N}
   Tensões: {N}
   Open Loops: {N}

🔗 RASTREABILIDADE:
   Chunks referenciados: {N}
   Todos válidos: ✅

🤖 AGENTES COM ESTE CONHECIMENTO:
   CLOSER, CRO, SALES-MANAGER

⭐️ AÇÕES
   Abrir: code "/knowledge/dossiers/persons/DOSSIER-{PESSOA}.md"
   Reprocessar: /process-jarvis [sources]

═══════════════════════════════════════════════════════════════════════════════
```

---

## EXEMPLOS

```bash
# Ver todos dossiers
/dossiers

# Apenas pessoas
/dossiers --persons

# Apenas temas
/dossiers --themes

# Ver dossier específico
/dossiers --person "Cole Gordon"

# Ver incompletos
/dossiers --incomplete
```
