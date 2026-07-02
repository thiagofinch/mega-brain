---
description: Comandos de controle durante checkpoints do Pipeline Jarvis (continue, abort, skip)
---

# JARVIS CONTROL - Comandos de Controle

> **Versão:** 1.0.0
> **Uso:** Durante checkpoints do Pipeline Jarvis

---

## COMANDOS DISPONÍVEIS

Estes comandos são usados durante o checkpoint após Phase 6 do Pipeline Jarvis.

---

## /continue

**Propósito:** Continuar para Phase 7-8 (Agent Enrichment + Finalization)

```
/continue
```

**Execução:**
1. Inicia Phase 7: Agent Enrichment
2. Atualiza MEMORYs dos agentes impactados
3. Atualiza AGENTs se selecionado
4. Executa Phase 8: Finalization
5. Gera Execution Report + Agent Enrichment Report

---

## /skip-enrichment

**Propósito:** Pular enrichment de agentes, ir direto para finalização

```
/skip-enrichment
```

**Execução:**
1. Pula Phase 7 (Agent Enrichment)
2. Executa Phase 8: Finalization (parcial)
3. State files já salvos permanecem
4. Agentes NÃO são atualizados
5. Conhecimento fica disponível nos DOSSIERs

**Quando usar:**
- Quer revisar dossiês antes de atualizar agentes
- Não concorda com mapeamento theme→agent
- Quer fazer enrichment manual depois

---

## /review-dossiers

**Propósito:** Abrir DOSSIERs criados/atualizados para revisão antes de continuar

```
/review-dossiers
```

**Execução:**
1. Lista DOSSIERs criados/atualizados nesta sessão
2. Abre cada um para revisão (ou mostra path)
3. Aguarda confirmação para continuar

**Output:**
```
═══════════════════════════════════════════════════════════════════════════════
                         DOSSIERS PARA REVISÃO
═══════════════════════════════════════════════════════════════════════════════

📄 CRIADOS/ATUALIZADOS NESTA SESSÃO:

   1. DOSSIER-{PESSOA}.md (NOVO)
      Path: /knowledge/external/dossiers/persons/DOSSIER-{PESSOA}.md
      Insights: {N}
      Frameworks: {N}

   2. DOSSIER-{TEMA}.md (ATUALIZADO)
      Path: /knowledge/external/dossiers/THEMES/DOSSIER-{TEMA}.md
      Novos insights: +{N}

───────────────────────────────────────────────────────────────────────────────

Após revisar, escolha:
   /continue          → Prosseguir com enrichment
   /skip-enrichment   → Finalizar sem atualizar agentes
   /abort             → Cancelar

═══════════════════════════════════════════════════════════════════════════════
```

---

## /abort

**Propósito:** Cancelar processamento (state files já salvos permanecem)

```
/abort
```

**Execução:**
1. Cancela processamento atual
2. NÃO reverte state files (CHUNKS, INSIGHTS, NARRATIVES já salvos)
3. NÃO atualiza agentes
4. NÃO gera Execution Report completo

**Quando usar:**
- Identificou problema nos dados
- Quer reprocessar com configurações diferentes
- Erro durante processamento

**Output:**
```
═══════════════════════════════════════════════════════════════════════════════
                         PROCESSAMENTO CANCELADO
═══════════════════════════════════════════════════════════════════════════════

⚠️ Pipeline interrompido na Phase 6.

📁 STATE FILES (já salvos, NÃO revertidos):
   ✅ CHUNKS-STATE.json: +{N} chunks de {SOURCE_ID}
   ✅ CANONICAL-MAP.json: +{N} entidades
   ✅ INSIGHTS-STATE.json: +{N} insights
   ✅ NARRATIVES-STATE.json: +{N} narrativas

🚫 NÃO EXECUTADO:
   ❌ Agent Enrichment (Phase 7)
   ❌ Finalization (Phase 8)
   ❌ Execution Report

⭐️ OPÇÕES:
   Retomar: /continue (irá do ponto onde parou)
   Reprocessar: /process-jarvis "{PATH}" (reinicia do zero)
   Reverter: /rollback {SOURCE_ID} (remove chunks desta fonte)

═══════════════════════════════════════════════════════════════════════════════
```

---

## ALIASES

```
/c    → /continue
/s    → /skip-enrichment
/r    → /review-dossiers
/x    → /abort
```

---

## CONTEXTO DE USO

Estes comandos só são válidos durante um checkpoint ativo do Pipeline Jarvis.

Se executados fora de contexto:
```
⚠️ Nenhum checkpoint ativo.

Para processar material: /process-jarvis [PATH]
Para ver inbox: /inbox
Para ver estado: /system-digest
```
