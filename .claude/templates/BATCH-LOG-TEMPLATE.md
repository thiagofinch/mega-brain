# BATCH LOG TEMPLATE v1.0.0

> **Uso Obrigatório:** Este template DEVE ser usado para TODOS os logs de batch durante Phase 4.
> **Entrega:** Em conversa apenas (não salvar arquivo)
> **Autor:** [OWNER] + Claude
> **Data:** 2026-01-05

---

## Formato Completo

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  📦 BATCH-{NNN} COMPLETE                                     {TIMESTAMP}    │
├──────────────────────────────────────────────────────────────────────────────┤
│  SOURCE: {SOURCE_ID} ({PESSOA})                                              │
│  ARQUIVOS: {N}/8                                                             │
│  STATUS: ✅ PROCESSADO                                                       │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 📄 ARQUIVOS PROCESSADOS ────────────────────────────────────────────────────┐
│  1. [✅] {NOME_ARQUIVO_1}                                                    │
│  2. [✅] {NOME_ARQUIVO_2}                                                    │
│  3. [✅] {NOME_ARQUIVO_3}                                                    │
│  ...                                                                         │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 🧠 DNA COGNITIVO EXTRAÍDO (5 CAMADAS) ──────────────────────────────────────┐
│                                                                              │
│  ┌─ 1. FILOSOFIAS ───────────────────────────────────────────────────────┐  │
│  │  • "{Filosofia 1}"                                                    │  │
│  │  • "{Filosofia 2}"                                                    │  │
│  │  • ...                                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ 2. MODELOS MENTAIS ──────────────────────────────────────────────────┐  │
│  │  • {Modelo 1}                                                         │  │
│  │  • {Modelo 2}                                                         │  │
│  │  • ...                                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ 3. HEURÍSTICAS ★ (com números) ──────────────────────────────────────┐  │
│  │  ★ "{Heurística com número 1}"                                        │  │
│  │  ★ "{Heurística com número 2}"                                        │  │
│  │  ★ ...                                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ 4. FRAMEWORKS ───────────────────────────────────────────────────────┐  │
│  │  📐 {Nome Framework 1}: {Descrição breve}                             │  │
│  │  📐 {Nome Framework 2}: {Descrição breve}                             │  │
│  │  📐 ...                                                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ 5. METODOLOGIAS ─────────────────────────────────────────────────────┐  │
│  │  📋 {Nome Metodologia 1}: {Steps resumidos}                           │  │
│  │  📋 {Nome Metodologia 2}: {Steps resumidos}                           │  │
│  │  📋 ...                                                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 🏷️ TEMAS DETECTADOS ────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌─ CONSOLIDADOS (já existem, enriquecidos) ─────────────────────────────┐  │
│  │  • 02-PROCESSO-VENDAS: +{N} insights                                  │  │
│  │  • 05-METRICAS: +{N} insights                                         │  │
│  │  • ...                                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ POSSÍVEIS NOVOS TEMAS (threshold: 5+ insights) ──────────────────────┐  │
│  │  • {tema-candidato-1}: {N} insights detectados                        │  │
│  │  • {tema-candidato-2}: {N} insights detectados                        │  │
│  │  • (ou "Nenhum neste batch")                                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ ÚNICOS/ISOLADOS (específicos desta fonte) ───────────────────────────┐  │
│  │  • {tema-unico-1}: aparece apenas em {SOURCE}                         │  │
│  │  • {tema-unico-2}: menção única                                       │  │
│  │  • (ou "Nenhum identificado")                                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 🤖 AGENTES IMPACTADOS ──────────────────────────────────────────────────────┐
│                                                                              │
│  ┌─ A ALIMENTAR (Phase 5) ───────────────────────────────────────────────┐  │
│  │  • CLOSER: +{N} insights ({temas})                                    │  │
│  │  • SALES-MANAGER: +{N} insights ({temas})                             │  │
│  │  • CFO: +{N} insights ({temas})                                       │  │
│  │  • ...                                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ POSSÍVEIS NOVOS AGENTES (threshold ≥3 menções) ──────────────────────┐  │
│  │  • {cargo-detectado}: {N} menções → Criar?                            │  │
│  │  • (ou "Nenhum detectado neste batch")                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ DOSSIÊS IMPACTADOS ──────────────────────────────────────────────────┐  │
│  │  • PERSONS/{PESSOA}: +{N} insights                                    │  │
│  │  • THEMES/{TEMA}: +{N} insights                                       │  │
│  │  • ...                                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 📊 MÉTRICAS DO BATCH ───────────────────────────────────────────────────────┐
│                                                                              │
│  ┌────────────────┬────────────────┬────────────────┬────────────────────┐  │
│  │ Chunks         │ Insights       │ Heurísticas★   │ Frameworks         │  │
│  ├────────────────┼────────────────┼────────────────┼────────────────────┤  │
│  │ {N}            │ {N}            │ {N}            │ {N}                │  │
│  └────────────────┴────────────────┴────────────────┴────────────────────┘  │
│                                                                              │
│  ┌────────────────┬────────────────┬────────────────┬────────────────────┐  │
│  │ Filosofias     │ Modelos        │ Metodologias   │ ROI               │  │
│  ├────────────────┼────────────────┼────────────────┼────────────────────┤  │
│  │ {N}            │ {N}            │ {N}            │ {ratio} ins/chunk │  │
│  └────────────────┴────────────────┴────────────────┴────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ 📈 ACUMULADO DA MISSÃO ─────────────────────────────────────────────────────┐
│                                                                              │
│  ┌─ VOLUME ──────────────────────────────────────────────────────────────┐  │
│  │  Arquivos: {N}/{TOTAL} │ Batches: {N}/{TOTAL} │ Progresso: {%}%       │  │
│  │  Chunks: {N} │ Insights: {N}                                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ DNA COGNITIVO (acumulado) ───────────────────────────────────────────┐  │
│  │  Filosofias: {N} │ Modelos: {N} │ Heurísticas★: {N}                   │  │
│  │  Frameworks: {N} │ Metodologias: {N}                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ FONTES PROCESSADAS ──────────────────────────────────────────────────┐  │
│  │  ✅ {SOURCE_1}: {N} arquivos                                          │  │
│  │  ✅ {SOURCE_2}: {N} arquivos                                          │  │
│  │  🔄 {SOURCE_ATUAL}: {N}/{TOTAL} arquivos (em andamento)               │  │
│  │  ⏳ {SOURCE_PENDENTE}: {N} arquivos                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

⚡️ PRÓXIMO: {Descrição do próximo passo}
```

---

## Seções Obrigatórias

| Seção | Obrigatório | Descrição |
|-------|-------------|-----------|
| Header | ✅ | BATCH-NNN, SOURCE, timestamp |
| Arquivos Processados | ✅ | Lista com ✅ de cada arquivo |
| DNA Cognitivo (5 Camadas) | ✅ | SEMPRE mostrar as 5 camadas separadas |
| Temas Detectados | ✅ | 3 categorias: Consolidados, Possíveis Novos, Únicos |
| Agentes Impactados | ✅ | 3 categorias: A Alimentar, Possíveis Novos, Dossiês |
| Métricas do Batch | ✅ | 8 métricas em 2 grids |
| Acumulado da Missão | ✅ | Volume + DNA + Fontes |
| Próximo Passo | ✅ | Indicação clara do próximo |

---

## Regras de Preenchimento

### 5 Camadas Cognitivas
1. **Filosofias**: Crenças, valores, axiomas (aspas obrigatórias)
2. **Modelos Mentais**: Formas de pensar, analogias
3. **Heurísticas ★**: SEMPRE com números específicos (★ obrigatório)
4. **Frameworks**: Sistemas nomeados com descrição breve
5. **Metodologias**: Processos passo-a-passo

### Temas
- **Consolidados**: Temas que JÁ existem no sistema e foram enriquecidos
- **Possíveis Novos**: Threshold = 5+ insights no mesmo tema
- **Únicos/Isolados**: Específicos desta fonte, sem consolidação cross-source

### Agentes
- **A Alimentar**: Agentes existentes que receberão insights na Phase 5
- **Possíveis Novos**: Cargos mencionados ≥3 vezes = considerar criação
- **Dossiês**: PERSONS e THEMES impactados

---

## Quando Usar

- ✅ Após CADA batch completo na Phase 4
- ❌ NÃO usar para SOURCE logs (esses têm formato próprio)
- ❌ NÃO salvar em arquivo (apenas conversa)

---

## Changelog

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0.0 | 2026-01-05 | Template inicial oficializado |


---

## Cascateamento Executado

**Data:** 2026-02-18 21:27
**Regra aplicada:** REGRA #22 (Cascateamento Multi-Destino)
**Sistema:** Mega Brain

### Resumo

| Tipo | Quantidade | Sucesso |
|------|------------|---------|
| Agentes | 0 | 0 |
| Playbooks | 0 | 0 |
| DNAs | 0 | 0 |
| Dossiers | 0 | 0 |

### Detalhes


---

*Cascateamento automatico via `post_batch_cascading.py` (Mega Brain)*
