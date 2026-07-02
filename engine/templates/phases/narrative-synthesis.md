# NARRATIVE-SYNTHESIS-PROTOCOL.md

> **Phase:** 3.1 (após Insight Extraction, antes de DNA Extraction)
> **Input:** INSIGHTS-STATE.json (insights categorizados por fonte)
> **Output:** `/processing/narratives/NARRATIVES-STATE.json`
> **Versão:** 1.0.0
> **Criado:** 2026-01-04

---

## PROPÓSITO

Consolidar insights isolados em **narrativas coerentes** por tema. Não é mais "o que a pessoa disse", mas "como a pessoa PENSA sobre X" - uma visão consolidada que captura a filosofia e a lógica por trás das táticas.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│  INSIGHT EXTRACTION (Phase 2.1)          NARRATIVE SYNTHESIS (Phase 3.1)           │
│  ───────────────────────────────────────────────────────────────────────────────   │
│                                                                                     │
│  ✅ Extrai PONTOS DISCRETOS               ✅ Consolida em NARRATIVAS TEMÁTICAS     │
│  ✅ "Jeremy diz X sobre ads"              ✅ "A filosofia de Jeremy sobre ads é..." │
│  ✅ Categoriza por tipo                   ✅ Identifica PADRÕES entre categorias   │
│  ✅ 50 insights separados                 ✅ 5-10 narrativas consolidadas          │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## CONCEITOS-CHAVE

### Narrativa vs Insight

| Insight | Narrativa |
|---------|-----------|
| Ponto discreto | História consolidada |
| "Hammer Them: 15-20 peças em 72h" | "A filosofia central de JH é pré-vender antes da call..." |
| Pode ser aplicado isoladamente | Requer compreensão do sistema todo |
| Cita número específico | Explica o PORQUÊ do número |

### Tipos de Síntese

1. **INTRA-CATEGORIA**: Insights da mesma categoria → 1 narrativa
   - Ex: 10 insights de `ad_strategies_jh` → "Filosofia de Ads de JH"

2. **INTER-CATEGORIA**: Padrões entre categorias
   - Ex: `ad_strategies` + `sales_psychology` → "Sistema de Pré-Venda de JH"

3. **TENSÕES**: Aparentes contradições que revelam nuance
   - Ex: "Alta frequência" vs "Qualidade de conteúdo" → Tensão explicada

---

## INPUT

### Fontes Primárias

1. **INSIGHTS-STATE.json** - Insights categorizados
2. **Filtro por fonte** - Ex: todas categorias com sufixo `_jh`

### Formato de Entrada

```json
{
  "ad_strategies_jh": {
    "count": 10,
    "insights": [
      { "id": "ASJH001", "insight": "...", "chunks": [...], "heuristic": true },
      ...
    ]
  }
}
```

---

## OUTPUT

### NARRATIVES-STATE.json (Schema)

```json
{
  "version": "1.0.0",
  "created": "2026-01-04T16:00:00Z",
  "last_updated": "2026-01-04T16:00:00Z",
  "total_narratives": 8,
  "pessoa": "jeremy-haynes",
  "fonte_ids": ["JH-SOP001", "JH-SOP002", "..."],

  "narratives": [
    {
      "id": "NAR-JH-001",
      "titulo": "O Sistema Hammer Them: Pré-Venda como Filosofia Central",
      "tema_principal": "AD_STRATEGY",
      "temas_relacionados": ["SALES_PSYCHOLOGY", "SHOW_RATE"],
      "insights_consolidados": ["ASJH001", "ASJH002", "SPJH001", "SPJH002"],
      "chunks_raiz": ["JH-SOP002_001", "JH-SOP002_002", "..."],

      "narrativa": "Jeremy Haynes construiu sua abordagem de marketing em torno de uma ideia central: a venda começa ANTES da call. O sistema 'Hammer Them' não é apenas uma tática - é uma filosofia. A premissa é que em mercados sofisticados (Stage 3-4), o prospect precisa de 15-20+ pontos de contato em uma janela de 72 horas antes da call para converter. Isso se baseia em princípios psicológicos como Familiarity Bias e Mere-Exposure Effect...",

      "filosofia_central": "A confused mind says no. Elimine confusão com saturação estratégica.",

      "heuristicas": [
        {"regra": "15-20+ peças em 72h", "fonte": "ASJH001"},
        {"regra": "CPE $0.01-0.02 vs CPC $0.50-2.00", "fonte": "ASJH005"}
      ],

      "frameworks": [
        {"nome": "4 Pillars of Pre-Call Content", "fonte": "ASJH002"},
        {"nome": "3 Critical Nurture Lines", "fonte": "ASJH003"}
      ],

      "tensoes": [
        {
          "aparente": "Alta frequência vs Qualidade de conteúdo",
          "resolucao": "JH resolve com biblioteca pré-construída: 30-50 short + 15-30 long antes de lançar campanhas"
        }
      ],

      "confidence": "HIGH",
      "completude": "ALTA"
    }
  ],

  "meta_patterns": [
    {
      "pattern": "Pre-sell before sell",
      "narratives": ["NAR-JH-001", "NAR-JH-003"],
      "insight": "JH inverte o funil tradicional: gasta mais em awareness que em direct response"
    }
  ],

  "gaps_identificados": [
    "Sem insights sobre pricing específico de JH",
    "Pouco sobre estrutura de time interno"
  ]
}
```

---

## PROCESSO DE SÍNTESE

### Passo 1: Agrupar por Tema

```
PARA cada categoria com sufixo da fonte (ex: "_jh"):
  AGRUPAR insights por tema principal
  IDENTIFICAR temas relacionados
```

### Passo 2: Identificar Núcleo Narrativo

```
PARA cada grupo temático:
  IDENTIFICAR insight mais fundamental (geralmente uma filosofia)
  CONSTRUIR narrativa ao redor deste núcleo
  CONECTAR insights relacionados como "evidências"
```

### Passo 3: Extrair Padrões Meta

```
ANALISAR narrativas como conjunto:
  DETECTAR padrões recorrentes entre narrativas
  IDENTIFICAR tensões aparentes
  DOCUMENTAR resolução de tensões (se existir)
```

### Passo 4: Documentar Gaps

```
COMPARAR insights disponíveis vs temas esperados:
  LISTAR temas sem cobertura
  PRIORIZAR gaps por relevância
```

---

## TEMPLATES DE NARRATIVA

### Template: Narrativa de Sistema

```markdown
## [TÍTULO DO SISTEMA]

### Filosofia Central
> "[Citação ou princípio fundamental]"

### O Que É
[Descrição em 2-3 parágrafos do sistema]

### Componentes
1. **[Componente 1]** - [descrição]
2. **[Componente 2]** - [descrição]

### Números-Chave (Heurísticas)
- [Heurística 1] ^[chunk_id]
- [Heurística 2] ^[chunk_id]

### Quando Usar
- [Contexto 1]
- [Contexto 2]

### Tensões Conhecidas
- **[Tensão]**: [Como JH resolve]

### Insights Fonte
[Lista de IDs dos insights consolidados]
```

---

## REGRAS DE SÍNTESE

### Princípios

1. **FIDELIDADE**: Narrativa deve ser derivável dos insights fonte
2. **RASTREABILIDADE**: Todo claim liga a chunk_id
3. **COMPLETUDE**: Não omitir insights que contradizem
4. **CLAREZA**: Explicar o "porquê", não apenas o "o quê"

### O Que NUNCA Fazer

```
❌ NUNCA inventar conexões não evidenciadas
❌ NUNCA omitir tensões/contradições
❌ NUNCA generalizar sem sufixo de confidence
❌ NUNCA perder rastreabilidade a chunks
```

### O Que SEMPRE Fazer

```
✅ SEMPRE citar insight_ids consolidados
✅ SEMPRE manter chunks_raiz para navegação
✅ SEMPRE declarar confidence level
✅ SEMPRE documentar gaps
```

---

## VALIDAÇÃO

Antes de considerar Phase 3.1 completa:

```
□ NARRATIVES-STATE.json existe e é JSON válido?
□ Todos os insights da fonte foram considerados?
□ Toda narrativa tem insights_consolidados?
□ Toda narrativa tem chunks_raiz?
□ Tensões foram documentadas?
□ Gaps foram identificados?
□ Meta-patterns foram extraídos?
```

---

## INTEGRAÇÃO COM PIPELINE

### Antes (Phase 2.1)
- INSIGHTS-STATE.json deve estar atualizado
- Categorias com sufixo da fonte (ex: `_jh`) identificadas

### Depois (Phase 3.2)
- DNA Extraction usa narrativas como contexto adicional
- SOUL.md pode citar narrativas diretamente

### Dossier Compilation (Phase 4.0)
- Dossiês REFERENCIAM narrativas
- Estrutura de DOSSIER segue temas das narrativas

---

**Versão:** 1.0.0
**Autor:** JARVIS + [OWNER]
**Última atualização:** 2026-01-04
