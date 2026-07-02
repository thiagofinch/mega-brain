# MCE PIPELINE LOG — Chronicler v4.0 (DESIGN PROPOSAL)

> Sucessor do v3.2. Mantém 44 STEPs + pre-00 + post-44, boxes largos de 79 colunas.
> Objetivo: **mais bonito + mais didático**, sem perder nenhum dado nem passo.
> Status: PROPOSTA — aguarda aprovação do founder antes de tocar o renderer.
> Autor: Chronicler · Referência viva: `.data/logs/mce/jeremy-haynes/MCE-JH.md`

---

## 1. O QUE MUDA vs v3.2 (resumo executivo)

| Dimensão | v3.2 (atual) | v4.0 (proposto) |
|----------|--------------|-----------------|
| Largura | 79 col (oficial) | **79 col (mantido)** |
| Box por STEP | `╔ título ╗` + `┌ dados ┐` aninhado | **box único `║` com 4 zonas internas** |
| Agrupamento | nenhum — 44 boxes em fila | **6 GRUPOS com banner + barra ▓░ de progresso** |
| Status | texto solto | **ribbon de STATUS no topo de cada STEP** |
| Métricas | lista vertical | **mini-tabela 2 colunas alinhada** |
| Didática | "Por que esse passo existe?" | **mantido + 💡 GLOSSÁRIO inline de jargão** |
| Navegação | só número do STEP | **`GRUPO X · NN/44` no header de cada STEP** |
| Header/footer | ████ monumental | **mantido + sumário de grupos na capa** |

**Princípio:** zero perda de dado. Todo campo do v3.2 continua. As mudanças são de
**layout e didática** — agrupar, rotular, explicar e dar hierarquia visual.

---

## 2. OS 6 GRUPOS (nova espinha visual)

Os 44 STEPs passam a ser visualmente agrupados pelas fases reais do pipeline.
Antes de cada grupo entra um BANNER com barra de progresso e uma frase-síntese.

| Grupo | Nome | STEPs | O que acontece |
|-------|------|-------|----------------|
| 1 | INGESTÃO & PREPARAÇÃO | pre-00, 00–11 | fonte crua → chunks vetorizados |
| 2 | EXTRAÇÃO DE DNA (L1–L10) | 12–21 | filosofias, heurísticas, voz, obsessões |
| 3 | IDENTIDADE & CONSOLIDAÇÃO | 22–25 | checkpoint, dossiê, promoção do agente |
| 4 | CASCATEAMENTO | 26–31 | role-tracker, dossiês de tema, solos |
| 5 | GATES & QUALIDADE | 32–36 | RAG gate, Phase-8, cross-batch, contradições |
| 6 | FINALIZAÇÃO & TELEMETRIA | 37–44, post-44 | lifecycle, custo, squads, health, árvore |

### Banner de grupo (mockup)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ▒▒▒  GRUPO 2 · EXTRAÇÃO DE DNA (L1–L10)              STEPs 12–21  ·  10 passos
  ▒▒▒  De insights crus às 10 camadas cognitivas do especialista
  Progresso do pipeline   ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░   48%   (STEP 21 de 44)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 3. ANATOMIA DO NOVO STEP BOX

Box único de 79 colunas com 4 zonas: **HEADER · STATUS · MÉTRICAS · DIDÁTICA**.

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  <icon>  STEP NN · <TÍTULO>                            GRUPO <g> · NN/44       ║  ← HEADER
╟───────────────────────────────────────────────────────────────────────────────╢
║  STATUS   <✅|⚠️|❌> <VERDITO> · <resumo de 1 linha>                          ║  ← RIBBON
║                                                                               ║
║  ┌─ MÉTRICAS ────────────────────────┬───────────────────────────────────┐   ║  ← TABELA
║  │ <campo>            <valor>        │ <campo>            <valor>        │   ║
║  └───────────────────────────────────┴───────────────────────────────────┘   ║
║                                                                               ║
║  💡 GLOSSÁRIO                                                                  ║  ← JARGÃO
║     <termo> ··· <definição curta em linguagem de negócio>                     ║
║                                                                               ║
║  📖 POR QUE ESTE PASSO EXISTE?                                                 ║  ← DIDÁTICA
║     <parágrafo didático preservado do v3.2>                                    ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

Regras de zona:
- **HEADER**: ícone + nome + localizador `GRUPO g · NN/44`. Sempre presente.
- **STATUS**: ribbon com semáforo + verdito + resumo. Se o STEP não tem status
  natural (ex.: contagem de DNA), o verdito vira a métrica-chave (ex.: "61 heurísticas").
- **MÉTRICAS**: mini-tabela 2 colunas. Campos do v3.2, só realinhados.
- **GLOSSÁRIO**: opcional, só quando há jargão (embedding, chunk, RAG, DNA-L8…).
  Some quando o STEP não introduz termo novo.
- **DIDÁTICA**: o "Por que esse passo existe?" do v3.2, intacto, com ícone 📖.

---

## 4. MOCKUPS — 1 STEP REPRESENTATIVO POR GRUPO

### GRUPO 1 · STEP 01 — INGESTION GUARD

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🛡  STEP 01 · INGESTION GUARD                              GRUPO 1 · 01/44    ║
╟───────────────────────────────────────────────────────────────────────────────╢
║  STATUS   ✅ PROCESS · conteúdo novo, sem duplicata — pipeline liberado        ║
║                                                                               ║
║  ┌─ MÉTRICAS ────────────────────────┬───────────────────────────────────┐   ║
║  │ Verdito            ✅ PROCESS      │ Word count          9.534         │   ║
║  │ Motivo             new content    │ Prev count          0             │   ║
║  │ Identity key       58a1f977…      │ Delta               0             │   ║
║  └───────────────────────────────────┴───────────────────────────────────┘   ║
║                                                                               ║
║  💡 GLOSSÁRIO                                                                  ║
║     identity key ··· impressão digital do material (hash). Se 2 arquivos      ║
║                      têm a mesma, são duplicata e o pipeline pula (SKIP).     ║
║                                                                               ║
║  📖 POR QUE ESTE PASSO EXISTE?                                                 ║
║     Se fosse duplicata, o pipeline pararia aqui (SKIP) — zero custo de LLM,   ║
║     nenhum artefato regravado. A auditoria registra o skip.                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### GRUPO 2 · STEP 14 — DNA L3 HEURÍSTICAS

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🎯  STEP 14 · DNA L3 · HEURÍSTICAS                  GRUPO 2 · 14/44  ⭐ TOP   ║
╟───────────────────────────────────────────────────────────────────────────────╢
║  STATUS   ✅ 61 heurísticas extraídas · a camada mais acionável do DNA         ║
║                                                                               ║
║  ┌─ MÉTRICAS ────────────────────────┬───────────────────────────────────┐   ║
║  │ Heurísticas         61            │ Camada              L3            │   ║
║  │ Valor relativo      ★★★★★ (top)   │ Acionável           imediata      │   ║
║  └───────────────────────────────────┴───────────────────────────────────┘   ║
║                                                                               ║
║  💡 GLOSSÁRIO                                                                  ║
║     heurística ··· regra prática com número: "Se X então Y". É o tipo de      ║
║                    insight que vira ação direta — por isso é o mais valioso.  ║
║                                                                               ║
║  📖 POR QUE ESTE PASSO EXISTE?                                                 ║
║     Heurísticas são o conhecimento operacional do especialista — o que ele    ║
║     faz na prática quando a situação X aparece. Núcleo do agente mind-clone.  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### GRUPO 3 · STEP 22 — IDENTITY CHECKPOINT

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🔍  STEP 22 · IDENTITY CHECKPOINT                          GRUPO 3 · 22/44    ║
╟───────────────────────────────────────────────────────────────────────────────╢
║  STATUS   ✅ APPROVE · DNA coerente entre as 10 camadas · 144 insights         ║
║                                                                               ║
║  ┌─ GATES DE COERÊNCIA ──────────────┬───────────────────────────────────┐   ║
║  │ Evidence gate       ✅ PASS        │ Total insights      144           │   ║
║  │ Coerência L1–L10    ✅ PASS        │ Recomendação        → Consolidar  │   ║
║  │ Obs / paradoxos     ✅ PASS        │ Verdito             ✅ APPROVE     │   ║
║  └───────────────────────────────────┴───────────────────────────────────┘   ║
║                                                                               ║
║  📖 POR QUE ESTE PASSO EXISTE?                                                 ║
║     O Lens valida coerência cruzada entre as camadas L1–L10. DNA incoerente   ║
║     = agente que se contradiz. Aqui o pipeline decide APPROVE / REVISE / ABORT.║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### GRUPO 4 · STEP 29 — NARRATIVE SYNTHESIS

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  📝  STEP 29 · NARRATIVE SYNTHESIS                          GRUPO 4 · 29/44    ║
╟───────────────────────────────────────────────────────────────────────────────╢
║  STATUS   ✅ 6 narrativas · 6 padrões · 5 pontos de consenso                   ║
║                                                                               ║
║  ┌─ MÉTRICAS ────────────────────────┬───────────────────────────────────┐   ║
║  │ Total narrativas    6             │ Padrões             6             │   ║
║  │ Consenso            5             │                                   │   ║
║  └───────────────────────────────────┴───────────────────────────────────┘   ║
║                                                                               ║
║  💡 GLOSSÁRIO                                                                  ║
║     narrativa ··· insights soltos comprimidos em texto fluido. É o que o      ║
║                   agente "lê" pra responder com a voz da pessoa, não em bullets.║
║                                                                               ║
║  📖 POR QUE ESTE PASSO EXISTE?                                                 ║
║     Sem narrativa o agente responde em tópicos desconexos. Aqui os insights   ║
║     viram prosa coerente — a matéria-prima das respostas fluidas.             ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### GRUPO 5 · STEP 34 — PHASE 8 GATE

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🚦  STEP 34 · PHASE 8 GATE                                 GRUPO 5 · 34/44    ║
╟───────────────────────────────────────────────────────────────────────────────╢
║  STATUS   ✅ PASS · 10/10 checks · qualidade final aprovada                    ║
║                                                                               ║
║  ┌─ 10 CHECKS (7A–7J) ───────────────────────────────────────────────────┐   ║
║  │  7A ✅   7B ✅   7C ✅   7D ✅   7E ✅                                    │   ║
║  │  7F ✅   7G ✅   7H ✅   7I ✅   7J ✅          Score  ▓▓▓▓▓▓▓▓▓▓ 10/10  │   ║
║  └───────────────────────────────────────────────────────────────────────┘   ║
║                                                                               ║
║  📖 POR QUE ESTE PASSO EXISTE?                                                 ║
║     10 checks em paralelo validam insights, narrativas, fontes, state files,  ║
║     role-tracking, cobertura de cascateamento e evolution log. É o crivo final.║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### GRUPO 6 · STEP 42 — HEALTH SCORE

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  📊  STEP 42 · HEALTH SCORE                                 GRUPO 6 · 42/44    ║
╟───────────────────────────────────────────────────────────────────────────────╢
║  STATUS   ⚠️ 65/100 · ATENÇÃO · inbox e pipeline puxando o score pra baixo     ║
║                                                                               ║
║  Score total   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░  65/100   Grade: ATENÇÃO              ║
║                                                                               ║
║  ┌─ COMPONENTES ─────────────────────┬───────────────────────────────────┐   ║
║  │ State files   ▓▓▓▓▓▓▓▓░░  15/20    │ Inbox         ▓▓░░░░░░░░   5/20   │   ║
║  │ Agents        ▓▓▓▓▓▓▓▓▓▓  20/20    │ Pipeline      ▓▓░░░░░░░░   5/20   │   ║
║  │ Dossiers      ▓▓▓▓▓▓▓▓▓▓  20/20    │                                   │   ║
║  └───────────────────────────────────┴───────────────────────────────────┘   ║
║                                                                               ║
║  📖 COMO INTERPRETAR?                                                          ║
║     A (90–100) saudável · B (70–89) pequenas lacunas · C (<70) atenção já.    ║
║     Aqui: agentes e dossiês perfeitos; inbox/pipeline acumulados derrubam.    ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 5. CAPA (header monumental v4) + RODAPÉ

```
███████████████████████████████████████████████████████████████████████████████
████                                                                       ████
████            M C E   P I P E L I N E   L O G        v 4 . 0              ████
████            Jeremy Haynes  (JH)  ·  2026-06-08 16:09 UTC               ████
████                                                                       ████
████   44 STEPS · 6 GRUPOS · 2 BLOCOS CANÔNICOS · Chronicler v4.0          ████
████                                                                       ████
████   GRUPO 1 ▓▓▓▓ Ingestão    GRUPO 4 ▓▓▓▓ Cascateamento                ████
████   GRUPO 2 ▓▓▓▓ DNA L1–L10  GRUPO 5 ▓▓▓▓ Gates                        ████
████   GRUPO 3 ▓▓▓▓ Identidade  GRUPO 6 ▓▓▓▓ Finalização                  ████
████                                                                       ████
███████████████████████████████████████████████████████████████████████████████
```

Rodapé mantém o ████ + linha de versão + Chronicler Audit (44/44 COMPLETO).

---

## 6. CAMINHO DE IMPLEMENTAÇÃO (para @dev, pós-aprovação)

O renderer atual vive em 2 arquivos. A mudança é **só de layout** — os dados
(metrics dos payloads de PHASE-STREAM) não mudam, então producers ficam intactos.

| Arquivo | Função | O que muda |
|---------|--------|------------|
| `engine/intelligence/pipeline/mce/log_generator.py` | `_v3_step()`, `_v3_header()`, `_v3_footer()`, os 44 `_step_NN_*()` | criar `_v4_step()` (box único 4-zonas), `_v4_group_banner()`, `_v4_header()`; cada `_step_NN` passa a chamar `_v4_step` com as 4 zonas |
| `engine/intelligence/pipeline/mce/step_log_renderer.py` | helpers de box/borda | novos helpers `_zone_status()`, `_zone_metrics_2col()`, `_zone_glossary()`, `_progress_bar(pct)` |
| `.claude/skills/chronicler/renderers.py` | render dispatcher | só se o despejo em chat também passar a usar v4 |

**Estratégia segura (versionada, com rollback):**
1. `_v4_step` NOVO ao lado de `_v3_step` (não substituir). Flag `MCE_LOG_TEMPLATE=v4`.
2. Mapa GRUPO: dict `STEP→grupo` + `grupo→(nome, range, frase)`.
3. `_progress_bar(done, total, width=24)` → string ▓░.
4. Glossário: dict `STEP→[(termo, definição)]` curado (só jargão real).
5. Tabela 2-col: helper que alinha pares `(campo,valor)` em 2 colunas dentro de 79.
6. Teste de fidelidade: `test_v4_preserves_all_v3_data` — todo valor que aparece no
   v3.2 tem que aparecer no v4 (nenhum dado perdido) + largura ≤79 em toda linha.
7. Default fica v3.2 até aprovação; vira v4 default quando o founder OK.

**Não-quebra:** producers, PHASE-STREAM, chronicler_audit (44/44) e o contrato
de FASE C (despejo verbatim) continuam idênticos — só o desenho do box muda.

---

## 7. DECISÕES PRO FOUNDER

1. **Largura:** manter 79 col estrito? (mockups acima respeitam). [default: sim]
2. **Glossário inline:** manter (didático) ou virar um único box-glossário no fim?
   [recomendo inline — aprende no contexto do STEP]
3. **Barras ▓░:** nos grupos + health + gate score (como nos mockups)? [recomendo sim]
4. **Ribbon de STATUS:** semáforo ✅⚠️❌ no topo de cada STEP? [recomendo sim]
5. **Versão:** v4.0 com flag e rollback pro v3.2, ou substituição direta? [recomendo flag]

─── Chronicler • Mega Brain ───
