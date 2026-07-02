# TEMPLATE MASTER - MEGA BRAIN

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ████████╗███████╗███╗   ███╗██████╗ ██╗      █████╗ ████████╗███████╗       ║
║   ╚══██╔══╝██╔════╝████╗ ████║██╔══██╗██║     ██╔══██╗╚══██╔══╝██╔════╝       ║
║      ██║   █████╗  ██╔████╔██║██████╔╝██║     ███████║   ██║   █████╗         ║
║      ██║   ██╔══╝  ██║╚██╔╝██║██╔═══╝ ██║     ██╔══██║   ██║   ██╔══╝         ║
║      ██║   ███████╗██║ ╚═╝ ██║██║     ███████╗██║  ██║   ██║   ███████╗       ║
║      ╚═╝   ╚══════╝╚═╝     ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝       ║
║                                                                               ║
║                    M A S T E R   R E F E R E N C E                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

**Versão:** 3.0
**Última Atualização:** 2026-01-06
**Autor:** JARVIS Meta-Agente

---

## ÍNDICE DE TEMPLATES

| # | Template | Quando Usar | Local |
|---|----------|-------------|-------|
| 1 | BATCH-XXX.md | Após processar cada batch | logs/batches/ |
| 2 | SOURCE-XX.md | Após completar todos batches de uma fonte | logs/SOURCES/ |
| 3 | PHASE-X-COMPLETE.md | Após completar cada fase (1-5) | logs/ |
| 4 | MISSION-PROGRESS.md | Atualizar a cada sessão | logs/MISSIONS/ |
| 5 | SESSION-LOG.md | A cada sessão de trabalho | logs/LIVE-SESSION/ |
| 6 | **PHASE5 TEMPLATES** | Toda execução da Fase 5 (7 sub-templates) | reference/templates/PHASE5/ |

### 📦 TEMPLATES DA FASE 5 (CONSOLIDAÇÃO)

> **Localização:** `/reference/templates/PHASE5/MOGA-BRAIN-PHASE5-TEMPLATES.md`
> **Guia:** `/reference/templates/PHASE5/IMPLEMENTATION-GUIDE.md`

| Sub-Template | Quando Usar |
|--------------|-------------|
| 5.1 - FOUNDATION | Após extrair DNA + criar dossiers críticos |
| 5.2 - PERSON AGENTS | Após criar/atualizar agentes de pessoa |
| 5.3 - CARGO AGENTS | Após criar/atualizar agentes de cargo |
| 5.4 - THEME DOSSIERS | Após consolidar conhecimento por tema |
| 5.5 - ORG-LIVE | Após sincronizar estrutura organizacional |
| 5.6 - VALIDATION | Após validar referências e estados |
| 5.FINAL - CONSOLIDADO | Após processar TODAS as fontes |

**REGRA:** Fase 5 executada = Template exibido. Sem exceções.

---

# TEMPLATE 1: BATCH LOG (V2)

**Arquivo:** `logs/batches/BATCH-XXX.md`
**Quando:** Após processar cada batch de arquivos
**Trigger:** Todo batch completo DEVE gerar este log
**Versão:** 2.0 (com contexto completo da missão)

```markdown
# BATCH-XXX

┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│     ██████╗  █████╗ ████████╗ ██████╗██╗  ██╗    ██╗  ██╗██╗  ██╗██╗  ██╗   │
│     ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██║  ██║    ╚██╗██╔╝╚██╗██╔╝╚██╗██╔╝   │
│     ██████╔╝███████║   ██║   ██║     ███████║     ╚███╔╝  ╚███╔╝  ╚███╔╝    │
│     ██╔══██╗██╔══██║   ██║   ██║     ██╔══██║     ██╔██╗  ██╔██╗  ██╔██╗    │
│     ██████╔╝██║  ██║   ██║   ╚██████╗██║  ██║    ██╔╝ ██╗██╔╝ ██╗██╔╝ ██╗  │
│     ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  │
│                                                                              │
│               [SOURCE NAME] - [Tema Principal]                               │
│                                                                              │
│     ⭐ [RATING: EXCELLENT/HIGH/STANDARD]           [DATA] [HORA]            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  🎯 CONTEXTO DA MISSÃO                                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   MISSÃO           [MISSION-XXXX-XXX]                                       │
│   FASE             [N] de 5 ([NOME_FASE])                                   │
│   FONTE            [NOME] - Batch [N] de [TOTAL]                            │
│   PROGRESSO        [X]/[Y] arquivos ([Z]%)                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  BATCH-XXX SUMMARY                                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   📂 SOURCE         [NOME DA FONTE]                                         │
│   📁 SUBPASTA       [COURSES/MARKETING/PODCASTS/etc]                        │
│   📄 ARQUIVOS       [N] processados                                         │
│   ⚠️  TEMA          [Temas principais]                                      │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────┐   ┌─────────────────────────────┐         │
│   │  MÉTRICAS DO BATCH          │   │  FOCUS AREAS                │         │
│   ├─────────────────────────────┤   ├─────────────────────────────┤         │
│   │  Filosofias      [N]        │   │  [Area 1]                   │         │
│   │  Modelos Mentais [N]        │   │  [Area 2]                   │         │
│   │  Heurísticas ★   [N]        │   │  [Area 3]                   │         │
│   │  Frameworks      [N]        │   │  [Area 4]                   │         │
│   │  Metodologias    [N]        │   │  [Area 5]                   │         │
│   ├─────────────────────────────┤   └─────────────────────────────┘         │
│   │  TOTAL           [N]        │                                           │
│   └─────────────────────────────┘                                           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  🚀 DESTINO DO CONHECIMENTO                                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   🤖 AGENTES A ALIMENTAR:                                                   │
│      • [AGENT-1].md ([área])                                                │
│      • [AGENT-2].md ([área])                                                │
│      • [AGENT-3].md ([área])                                                │
│                                                                              │
│   📘 PLAYBOOKS IMPACTADOS:                                                  │
│      • PLAYBOOK-[NOME].md                                                   │
│      • PLAYBOOK-[NOME].md                                                   │
│                                                                              │
│   🧬 DNAs ENRIQUECIDOS:                                                     │
│      • DNA-[SOURCE].md (+[N] elementos)                                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  🏷️ ANÁLISE DE TEMAS                                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   🆕 TEMAS NOVOS (primeira vez identificados):                              │
│      • [Tema novo 1]                                                        │
│      • [Tema novo 2]                                                        │
│                                                                              │
│   🔄 TEMAS CONSOLIDADOS (já existiam, reforçados):                          │
│      • [Tema existente 1]                                                   │
│      • [Tema existente 2]                                                   │
│                                                                              │
│   🔗 TEMAS CROSS-SOURCE (aparecem em múltiplas fontes):                     │
│      • [Tema] ([Fonte 1], [Fonte 2])                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  📊 MÉTRICAS DE QUALIDADE                                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ⭐ RATING                [EXCELLENT/HIGH/STANDARD]                        │
│   📊 DENSIDADE             [N] elementos/arquivo                            │
│   🔢 HEURÍSTICAS C/ NÚMERO [X]/[Y] ([Z]%)                                   │
│   🎯 FRAMEWORKS ACIONÁVEIS [X]/[Y] ([Z]%)                                   │
│   📝 SCRIPTS PRÁTICOS      [N] incluídos                                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  📈 PROGRESSÃO CUMULATIVA                                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   HEURÍSTICAS    [anterior] + [batch] = [total]  ██████████████████████     │
│   FRAMEWORKS     [anterior] + [batch] = [total]  ██████████████             │
│   FILOSOFIAS     [anterior] + [batch] = [total]  ████████████████████       │
│   METODOLOGIAS   [anterior] + [batch] = [total]  ██████████                 │
│                                                  ─────────────────────────  │
│                       TOTAL ACUMULADO: [N] elementos                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  ➡️ PRÓXIMOS PASSOS (Preview Fase 5)                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Após SOURCE-[XX].md completo:                                             │
│   1. Alimentar [AGENT].md com DNA consolidado                               │
│   2. Criar PLAYBOOK-[NOME].md                                               │
│   3. Gerar COUNCIL questions sobre [tema]                                   │
│   4. Cross-reference com [OUTRA_FONTE] para síntese                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

## ARQUIVOS PROCESSADOS

| # | Arquivo | Tema |
|---|---------|------|
| 1 | [NOME DO ARQUIVO 1] | [tema] |
| 2 | [NOME DO ARQUIVO 2] | [tema] |
| ... | ... | ... |

## KEY FRAMEWORKS

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  [FRAMEWORK NAME]                                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   [Descrição do framework com passos numerados]                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## FILOSOFIAS DESTAQUE ([N])

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  TOP PHILOSOPHIES - BATCH XXX                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  🧠 "[Filosofia 1]"                                                         │
│  🧠 "[Filosofia 2]"                                                         │
│  🧠 "[Filosofia 3]"                                                         │
│  ...                                                                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## HEURÍSTICAS ★ (TOP [N])

| # | Heurística | Rating |
|---|------------|--------|
| 1 | [Heurística com número específico] | ★★★★★ |
| 2 | [Heurística com número específico] | ★★★★★ |
| ... | ... | ... |

---

**Arquivo:** `/logs/batches/BATCH-XXX.md`
**Source:** [FONTE] - [Status]
**Log Detalhado:** `/.claude/mission-control/batch-logs/BATCH-XXX-[XX].json`
**Gerado por:** JARVIS Meta-Agente
**Timestamp:** [DATA HORA]
```

---

# TEMPLATE 2: SOURCE COMPLETION LOG

**Arquivo:** `logs/SOURCES/SOURCE-XX.md`
**Quando:** Após completar TODOS os batches de uma fonte/pessoa
**Trigger:** Último batch de uma fonte DEVE gerar este log

```markdown
# SOURCE-XX.md - [Nome Completo] Complete

```
     [ASCII ART DO NOME DA PESSOA/EMPRESA]

   ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
   █                                                                    █
   █   [EMPRESA/cargo]  │  [CREDENCIAIS]  │  [RESULTADOS]              █
   █                                                                    █
   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
```

---

## METADATA

| Campo | Valor |
|-------|-------|
| **SOURCE_ID** | [XX] |
| **Pessoa** | [Nome] |
| **Empresa** | [Empresa] |
| **Batches** | [lista de batches] |
| **Arquivos Processados** | [N]/[N] |
| **Data Conclusão** | [DATA] |
| **Status** | ✅ COMPLETO |

---

## 1. RESUMO EXECUTIVO

[Parágrafo resumindo a pessoa, suas credenciais, e principais contribuições]

**Principais Contribuições:**
- [Contribuição 1]
- [Contribuição 2]
- [Contribuição 3]

**Densidade do Conteúdo:** [MUITO ALTA/ALTA/MÉDIA]

---

## 2. ARQUIVOS PROCESSADOS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📁 [FONTE] ([EMPRESA])                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [SUBPASTA]/ ([N] arquivos)                                                │
│  ├── [Arquivo 1]                                                           │
│  ├── [Arquivo 2]                                                           │
│  └── [Arquivo N]                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. DNA COGNITIVO (5 CAMADAS)

### 3.1 FILOSOFIAS

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           FILOSOFIAS - [NOME]                                 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  SOBRE [CATEGORIA]:                                                           ║
║  ─────────────                                                                ║
║  • "[Filosofia 1]"                                                           ║
║  • "[Filosofia 2]"                                                           ║
║                                                                               ║
║  TOTAL: [N] filosofias documentadas                                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 3.2 MODELOS MENTAIS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MODELOS MENTAIS - [NOME]                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🧠 [CATEGORIA]:                                                           │
│  ─────────────────                                                          │
│  • [Modelo 1]                                                              │
│  • [Modelo 2]                                                              │
│                                                                             │
│  TOTAL: [N] modelos mentais documentados                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 HEURÍSTICAS ★ (COM NÚMEROS)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         HEURÍSTICAS ★ - [NOME]                               ║
║                        (Regras com números específicos)                       ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ★★★★★ [CATEGORIA]:                                                          ║
║  • [Heurística com número específico]                                        ║
║  • [Heurística com número específico]                                        ║
║                                                                               ║
║  TOTAL: [N] heurísticas com números documentadas                             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 3.4 FRAMEWORKS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRAMEWORKS - [NOME]                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ════════════════════════════════════════════════════════════════════════  │
│  📋 [FRAMEWORK NAME] (Core)                                                │
│  ════════════════════════════════════════════════════════════════════════  │
│  [Passo 1]                                                                 │
│  [Passo 2]                                                                 │
│  [Passo N]                                                                 │
│                                                                             │
│  TOTAL: [N] frameworks documentados                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.5 METODOLOGIAS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        METODOLOGIAS - [NOME]                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  📋 [METODOLOGIA NAME]                                                     │
│  ───────────────────────────────────────────────────────────────────────    │
│  [Passo detalhado 1]                                                       │
│  [Passo detalhado 2]                                                       │
│                                                                             │
│  TOTAL: [N] metodologias documentadas                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. TEMAS COBERTOS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TEMAS - [NOME]                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┬───────────────┬────────────────────────────────┐  │
│  │ Tema                │ Insights      │ Destaques                      │  │
│  ├─────────────────────┼───────────────┼────────────────────────────────┤  │
│  │ [TEMA-01]           │ [N]+          │ [Framework X, Y]               │  │
│  │ [TEMA-02]           │ [N]+          │ [Framework Z]                  │  │
│  └─────────────────────┴───────────────┴────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. MÉTRICAS CONSOLIDADAS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MÉTRICAS - SOURCE XX                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                         VOLUME                                     │    │
│  ├────────────────┬────────────────┬────────────────┬─────────────────┤    │
│  │ Arquivos       │ Chunks         │ Insights       │ Batches         │    │
│  ├────────────────┼────────────────┼────────────────┼─────────────────┤    │
│  │ [N]            │ [N]            │ [N]            │ [N]             │    │
│  └────────────────┴────────────────┴────────────────┴─────────────────┘    │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      DNA COGNITIVO                                 │    │
│  ├────────────────┬────────────────┬────────────────┬─────────────────┤    │
│  │ Filosofias     │ Modelos        │ Heurísticas★   │ Frameworks      │    │
│  ├────────────────┼────────────────┼────────────────┼─────────────────┤    │
│  │ [N]            │ [N]            │ [N]            │ [N]             │    │
│  └────────────────┴────────────────┴────────────────┴─────────────────┘    │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                       QUALIDADE                                    │    │
│  ├────────────────┬────────────────┬────────────────┬─────────────────┤    │
│  │ Metodologias   │ ROI            │ Densidade      │ Status          │    │
│  ├────────────────┼────────────────┼────────────────┼─────────────────┤    │
│  │ [N]            │ [N] ins/chunk  │ [ALTA/MÉDIA]   │ ✅ COMPLETO     │    │
│  └────────────────┴────────────────┴────────────────┴─────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. AGENTES ALIMENTADOS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGENTES ALIMENTADOS - SOURCE XX                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────┬───────────┬─────────────────────────────────────┐  │
│  │ Agente             │ Insights  │ Principais Contribuições            │  │
│  ├────────────────────┼───────────┼─────────────────────────────────────┤  │
│  │ [AGENTE-1]         │ [N]+      │ [Framework X, Y]                    │  │
│  │ [AGENTE-2]         │ [N]+      │ [Framework Z]                       │  │
│  └────────────────────┴───────────┴─────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. CONTRADIÇÕES/TENSÕES DETECTADAS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TENSÕES DETECTADAS - SOURCE XX                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ⚠️ INTRA-SOURCE ([Nome] vs [Nome]):                                       │
│  ─────────────────────────────────────                                      │
│  1. "[Afirmação A]" vs "[Afirmação B]"                                     │
│     → Contexto: [Explicação]                                               │
│                                                                             │
│  ⚠️ CROSS-SOURCE ([Nome] vs Others):                                       │
│  ─────────────────────────────────────                                      │
│  1. [Nome]: "[Afirmação]"                                                  │
│     [Outro]: "[Afirmação diferente]"                                       │
│     → Contexto: [Explicação]                                               │
│                                                                             │
│  STATUS: Documentado para resolução contextual em Phase 5                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. CITAÇÕES MEMORÁVEIS

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       CITAÇÕES MEMORÁVEIS - [NOME]                            ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  "[Citação memorável 1]"                                                     ║
║                                                                               ║
║  "[Citação memorável 2]"                                                     ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 9. PRÓXIMOS PASSOS (PHASE 5)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRÓXIMOS PASSOS - SOURCE XX                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. ALIMENTAR AGENTES:                                                      │
│     □ [AGENTE]: Adicionar [conteúdo específico]                            │
│                                                                             │
│  2. ATUALIZAR DOSSIÊS:                                                      │
│     □ PERSONS/[NOME].md: Criar dossiê completo                             │
│     □ THEMES/[TEMA].md: Adicionar [conteúdo]                               │
│                                                                             │
│  3. RESOLVER TENSÕES:                                                       │
│     □ [Tensão específica] - [resolução proposta]                           │
│                                                                             │
│  4. EXTRAIR DNA:                                                            │
│     □ Criar DNA-CONFIG.yaml para [Nome]                                    │
│     □ Criar SOUL.md com filosofias em prosa                                │
│     □ Criar MEMORY.md com decisões e precedentes                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. RASTREABILIDADE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       RASTREABILIDADE - SOURCE XX                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  inbox/[FONTE]/           SOURCE LOG                             │   │
│  │       │                         │                                   │   │
│  │       ▼                         ▼                                   │   │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────────┐    ┌───────────┐   │   │
│  │  │ [N] TXT │ →  │ [N]     │ →  │ [N]         │ →  │ SOURCE-XX │   │   │
│  │  │ files   │    │ chunks  │    │ insights    │    │ .md       │   │   │
│  │  └─────────┘    └─────────┘    └─────────────┘    └───────────┘   │   │
│  │                                                                    │   │
│  │  Batch-XXX: [N] arquivos ([N] insights)                           │   │
│  │  Batch-XXX: [N] arquivos ([N] insights)                           │   │
│  │                                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SOURCE-XX.md → MISSION-STATE.json → INSIGHTS-STATE.json → CHUNKS-STATE    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Gerado por:** JARVIS Pipeline v2.2
**Data:** [DATA]
**Mission:** MISSION-2026-001
**Status:** ✅ SOURCE COMPLETO
```

---

# TEMPLATE 3: PHASE COMPLETION LOG

**Arquivo:** `logs/PHASE-X-COMPLETE-LOG.md`
**Quando:** Após completar cada fase (1-5) da missão
**Trigger:** Conclusão de fase DEVE gerar este log

```markdown
# PHASE [X] COMPLETION REPORT
## Pipeline Jarvis - [Nome da Fase]
### Consolidated Report: [DATA]

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██████╗ ██╗  ██╗ █████╗ ███████╗███████╗    ██╗  ██╗                        ║
║   ██╔══██╗██║  ██║██╔══██╗██╔════╝██╔════╝    ╚██╗██╔╝                        ║
║   ██████╔╝███████║███████║███████╗█████╗       ╚███╔╝                         ║
║   ██╔═══╝ ██╔══██║██╔══██║╚════██║██╔══╝       ██╔██╗                         ║
║   ██║     ██║  ██║██║  ██║███████║███████╗    ██╔╝ ██╗                        ║
║   ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝    ╚═╝  ╚═╝                        ║
║                                                                               ║
║   ██████╗ ██████╗ ███╗   ███╗██████╗ ██╗     ███████╗████████╗███████╗        ║
║  ██╔════╝██╔═══██╗████╗ ████║██╔══██╗██║     ██╔════╝╚══██╔══╝██╔════╝        ║
║  ██║     ██║   ██║██╔████╔██║██████╔╝██║     █████╗     ██║   █████╗          ║
║  ██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██║     ██╔══╝     ██║   ██╔══╝          ║
║  ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ███████╗███████╗   ██║   ███████╗        ║
║   ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝╚══════╝   ╚═╝   ╚══════╝        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## EXECUTIVE SUMMARY

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  📊 PHASE [X]: [NOME] - PROCESSAMENTO COMPLETO                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  EM UMA FRASE:                                                                  │
│  [Resumo em uma frase do que foi conquistado]                                   │
│                                                                                 │
│  O QUE CONQUISTAMOS:                                                            │
│  • [Conquista 1]                                                                │
│  • [Conquista 2]                                                                │
│  • [Conquista 3]                                                                │
│                                                                                 │
│  DECISÕES DO SISTEMA:                                                           │
│  • [Decisão 1]                                                                  │
│  • [Decisão 2]                                                                  │
│                                                                                 │
│  STATUS: ✅ PHASE [X] CONCLUÍDA COM SUCESSO                                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## MÉTRICAS CONSOLIDADAS

| Métrica | Valor |
|---------|-------|
| Arquivos | [N] |
| Sources | [N] |
| Batches | [N] |
| Chunks | [N] |
| Insights | [N] |
| Heurísticas | [N] |
| Frameworks | [N] |

---

## QUALITY INDICATORS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  QUALITY INDICATORS - PHASE [X]                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [Indicador 1]: [Valor]                                                    │
│  [Indicador 2]: [Valor]                                                    │
│  [Indicador 3]: [Valor]                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Gerado por:** JARVIS Pipeline v2.2
**Data:** [DATA]
**Mission:** MISSION-2026-001
**Status:** ✅ PHASE COMPLETE
```

---

# TEMPLATE 4: MISSION PROGRESS

**Arquivo:** `logs/MISSIONS/MISSION-XXXX-XXX-PROGRESS.md`
**Quando:** Atualizar a cada sessão de trabalho
**Trigger:** Início e fim de cada sessão DEVE atualizar este log

Ver arquivo atual: [MISSION-2026-001-PROGRESS.md](../logs/MISSIONS/MISSION-2026-001-PROGRESS.md)

---

# TEMPLATE 5: SESSION LOG

**Arquivo:** `logs/LIVE-SESSION/SESSION-YYYY-MM-DD.md`
**Quando:** A cada sessão de trabalho
**Trigger:** Início de sessão DEVE criar ou atualizar este log

```markdown
# SESSION LOG - [DATA]

## Objetivos da Sessão
- [ ] [Objetivo 1]
- [ ] [Objetivo 2]

## Progresso
| Hora | Ação | Resultado |
|------|------|-----------|
| [HH:MM] | [Ação] | [Resultado] |

## Decisões Tomadas
- [Decisão 1]
- [Decisão 2]

## Próximos Passos
- [ ] [Próximo passo 1]
- [ ] [Próximo passo 2]

---
**Sessão encerrada:** [HH:MM]
**Progresso total:** [X]%
```

---

# REGRA DE OURO

> **NUNCA processar um batch sem gerar BATCH-XXX.md**
> **NUNCA completar uma fonte sem gerar SOURCE-XX.md**
> **NUNCA completar uma fase sem gerar PHASE-X-COMPLETE.md**
> **NUNCA encerrar sessão sem atualizar MISSION-PROGRESS.md**

---

**Arquivo:** `/reference/TEMPLATE-MASTER.md`
**Versão:** 3.0
**Última Atualização:** 2026-01-06
**Gerado por:** JARVIS Meta-Agente
