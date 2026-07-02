# PHASE-4-VERIFICATION-CHECKPOINT

> **Versão:** 1.1.0
> **Criado:** 2026-01-05
> **Atualizado:** 2026-03-10 (MCE metrics section added)
> **Status:** OBRIGATÓRIO - NUNCA PULAR

---

## 🚨 ORIGEM DESTE PROTOCOLO

Este checkpoint foi criado após erro crítico na MISSION-2026-001:
- 32 batches processados SEM verificação de integridade
- Fontes marcadas como "COMPLETE" sem validação arquivo-por-arquivo
- Discrepâncias descobertas tardiamente (176 arquivos faltantes)

**ESTE ERRO NUNCA DEVE SE REPETIR.**

---

## ✅ CHECKLIST OBRIGATÓRIO PRÉ-PHASE-4

Antes de iniciar QUALQUER batch da Phase 4, VERIFICAR:

### 1. Inventário Completo

```
□ PLANILHA-COMPLETE-LIST.json está atualizado?
□ Todas as abas da planilha foram lidas?
□ Contagem total de itens conhecida?
```

### 2. Mapeamento Arquivo-por-Arquivo

```
□ DE-PARA-VERIFICACAO.md existe?
□ Para CADA fonte na planilha:
  □ Pasta correspondente existe no INBOX?
  □ Contagem de arquivos .txt verificada?
  □ Delta calculado (esperado vs disponível)?
```

### 3. Critérios de Continuação

```
┌─────────────────────────────────────────────────────────────────────┐
│  REGRA DE MATCH RATE                                                │
├─────────────────────────────────────────────────────────────────────┤
│  Match Rate >= 80%:  ✅ PROSSEGUIR                                  │
│  Match Rate 50-79%:  ⚠️ PROSSEGUIR COM RESSALVA (documentar)       │
│  Match Rate < 50%:   ❌ PARAR - Resolver discrepâncias primeiro     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4. Decisões Explícitas

```
□ Decisão sobre arquivos FALTANTES documentada?
  - Baixar? → Voltar para Phase 2
  - Ignorar? → Registrar motivo

□ Decisão sobre arquivos EXTRAS documentada?
  - Processar? → Adicionar ao inventário
  - Ignorar? → Registrar motivo

□ Arquivos _UNKNOWN classificados?
```

### 5. Atualização de Estado

```
□ MISSION-STATE.json atualizado com:
  □ verification_status: "VERIFIED"
  □ verification_timestamp: YYYY-MM-DDTHH:MM:SS
  □ match_rate: X%
  □ discrepancies_acknowledged: true
  □ decisions_documented: true
```

---

## 🔒 BLOQUEIO AUTOMÁTICO

Se este checklist NÃO estiver completo:

```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ⛔ PHASE 4 BLOQUEADA                                            ║
║                                                                   ║
║   Motivo: Verificação de integridade incompleta                   ║
║   Ação: Completar DE-PARA e verificações acima                    ║
║                                                                   ║
║   JARVIS não pode processar sem verificação.                      ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 📋 TEMPLATE DE VERIFICAÇÃO

Usar este formato ao verificar:

```markdown
## VERIFICAÇÃO PRÉ-PHASE-4

**Data:** YYYY-MM-DD HH:MM
**Missão:** MISSION-XXXX-NNN
**Verificador:** JARVIS

### Resultado da Verificação

| Check | Status | Nota |
|-------|--------|------|
| Inventário atualizado | ✅/❌ | |
| DE-PARA existe | ✅/❌ | |
| Match rate calculado | X% | |
| Decisão faltantes | DOC/PEND | |
| Decisão extras | DOC/PEND | |
| MISSION-STATE atualizado | ✅/❌ | |

### Decisão Final

[ ] ✅ APROVADO - Prosseguir com Phase 4
[ ] ❌ BLOQUEADO - Resolver pendências

**Justificativa:** [texto]
```

---

## 🔄 INTEGRAÇÃO COM JARVIS

Este checkpoint é executado automaticamente por JARVIS antes de:
- Iniciar nova missão Phase 4
- Retomar missão pausada
- Processar novo batch

JARVIS deve:
1. Verificar existência de DE-PARA-VERIFICACAO.md
2. Verificar verification_status em MISSION-STATE.json
3. Se falhar em qualquer check → BLOQUEAR e reportar

---

## MCE EXTRACTION METRICS (conditional)

This section appears in batch output ONLY when MCE extraction was run during the batch.
If batch was legacy-only (L1-L5 DNA extraction), this section is omitted -- backward compatible.

```markdown
## MCE EXTRACTION METRICS
<!-- Only shown when MCE extraction was part of this batch -->

### Behavioral Patterns (BEHAVIORAL-PATTERNS.yaml)

| Metric | Value |
|--------|-------|
| Patterns Found | N |
| With chunk_ids | N/N (XX%) |
| Categories | [decision, reaction, habit, communication, ...] |

### Values Hierarchy (VALUES-HIERARCHY.yaml)

| Metric | Value |
|--------|-------|
| Values Identified | N |
| With Numeric Score | N/N (XX%) |
| Obsessions Found | N |
| Paradoxes Found | N |

### Voice DNA (VOICE-DNA.yaml)

| Metric | Value |
|--------|-------|
| Tone Profile | [defined/missing] |
| Signature Phrases | N |
| Metaphors | N |
| Verbal Patterns | N |
| Catchphrases | N |

### MCE Quality Score

| Check | Status |
|-------|--------|
| MCE-01: Behavioral >= 3 entries | PASS/FAIL |
| MCE-02: Values with scores | PASS/FAIL |
| MCE-03a: Voice DNA exists | PASS/FAIL |
| MCE-03b: Tone profile defined | PASS/FAIL |
| MCE-03c: >= 5 phrases | PASS/FAIL |
| MCE-04: chunk_ids coverage | XX% |

### MCE Files Generated

| File | Path | Size |
|------|------|------|
| BEHAVIORAL-PATTERNS.yaml | knowledge/external/dna/persons/{slug}/ | X KB |
| VALUES-HIERARCHY.yaml | knowledge/external/dna/persons/{slug}/ | X KB |
| VOICE-DNA.yaml | knowledge/external/dna/persons/{slug}/ | X KB |
```

### When to Include MCE Metrics

```
┌─────────────────────────────────────────────────────────────────────┐
│  INCLUDE MCE METRICS WHEN:                                          │
│  - MCE extraction was run via /mce skill or MCE CLI                │
│  - Batch processing included MCE prompts                           │
│  - Any of the 3 MCE files were created or updated                  │
│                                                                     │
│  OMIT MCE METRICS WHEN:                                             │
│  - Batch was legacy L1-L5 only                                     │
│  - No MCE extraction was performed                                 │
│  - MCE files were not touched                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Este protocolo é INQUEBRÁVEL. Nenhuma exceção permitida.*
