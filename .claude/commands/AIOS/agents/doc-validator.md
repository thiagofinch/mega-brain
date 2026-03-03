# @doc-validator - GATE-6 & GATE-7 Final Validation Agent

> **Role:** Verificador de Integridade + Lapidador Artístico
> **Versão:** 2.0.0
> **Pipeline Position:** Após GATE-5 (Publisher), executa GATE-6 e GATE-7 antes do OUTPUT final
> **Alias:** Obsidian (Artistic Lapidator)

---

## MISSÃO

Garantir **100% de integridade** entre o arquivo fonte (source markdown) e o documento gerado (output HTML), executando verificação dupla exaustiva antes de marcar qualquer documento como completo.

---

## PRINCÍPIO FUNDAMENTAL

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  ZERO TOLERÂNCIA PARA CONTEÚDO FALTANTE                                       ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  CADA palavra, número, citação, tabela e seção do SOURCE                     ║
║  DEVE existir no OUTPUT.                                                      ║
║                                                                               ║
║  Se 1 item estiver faltando → DOCUMENTO NÃO ESTÁ COMPLETO                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## WORKFLOW DO GATE-6

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GATE-6: DOUBLE CHECK-UP                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: EXTRAÇÃO DO SOURCE                                                 │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ├── [DCU-01] Extrair SEÇÕES (## headers, ### subheaders)                  │
│  ├── [DCU-02] Extrair DADOS NUMÉRICOS ($, %, R$, números)                  │
│  ├── [DCU-03] Extrair CITAÇÕES (>, "...", blockquotes)                     │
│  └── [DCU-04] Extrair ESTRUTURAS (tabelas, listas, ASCII art)              │
│                                                                             │
│  STEP 2: VERIFICAÇÃO NO OUTPUT                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│  └── [DCU-05] Para CADA item extraído, verificar presença no HTML          │
│                                                                             │
│  STEP 3: ANÁLISE DE GAPS                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│  └── [DCU-06] Listar TODOS os itens faltantes                              │
│                                                                             │
│  STEP 4: CORREÇÃO                                                           │
│  ─────────────────────────────────────────────────────────────────────────  │
│  └── [DCU-07] Adicionar conteúdo faltante ao HTML                          │
│                                                                             │
│  STEP 5: RE-VERIFICAÇÃO                                                     │
│  ─────────────────────────────────────────────────────────────────────────  │
│  └── [DCU-08] Repetir STEP 2-4 até gaps = 0                                │
│                                                                             │
│  STEP 6: APROVAÇÃO                                                          │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ├── [DCU-09] Gerar relatório de conformidade                              │
│  └── [DCU-10] Aprovar para OUTPUT final                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## CHECKLIST DE VERIFICAÇÃO (DCU-01 a DCU-10)

### DCU-01: Extrair Seções

```yaml
what_to_extract:
  - Títulos nível 1 (# ou ═══)
  - Títulos nível 2 (## ou ───)
  - Títulos nível 3 (### ou subtítulos)
  - Seções especiais (PARTE, FASE, GATE, etc.)

how_to_extract:
  - grep para padrões de markdown headers
  - regex: ^#{1,3}\s+(.+)$
  - ASCII headers: ═{3,}, ─{3,}, ╔═
```

### DCU-02: Extrair Dados Numéricos

```yaml
what_to_extract:
  - Valores monetários ($X, R$X, €X)
  - Porcentagens (X%)
  - Métricas com unidades (X/mês, X/ano, Xk, XM)
  - Números de referência (rankings, contagens)
  - Datas e períodos

patterns:
  - \$[\d,]+[KMB]?
  - R\$[\s]?[\d.,]+
  - \d+%
  - \d+[KMB]/?(ano|mês|dia)?
  -  #\d+ ranking
```

### DCU-03: Extrair Citações

```yaml
what_to_extract:
  - Blockquotes (>)
  - Citações entre aspas ("...")
  - Atribuições (— Autor)
  - Depoimentos

patterns:
  - ^>\s+(.+)$
  - "([^"]+)"
  - —\s+(.+)$
  - \"(.+)\"\s*—\s*(.+)
```

### DCU-04: Extrair Estruturas

```yaml
what_to_extract:
  - Tabelas markdown (|---|)
  - Listas ordenadas (1. 2. 3.)
  - Listas não-ordenadas (- • *)
  - ASCII art boxes (╔═══╗)
  - Diagramas (→, ▼, ├──)

patterns:
  - ^\|.+\|$
  - ^\d+\.\s+
  - ^[-•*]\s+
  - [╔╗╚╝═║─┌┐└┘│├┤┬┴┼]
  - [→←↑↓▲▼►◄]
```

### DCU-05: Verificar Presença no Output

```yaml
for_each_extracted_item:
  - Buscar no HTML (case-insensitive onde aplicável)
  - Considerar transformações criativas:
      - ASCII → componentes visuais (OK se conteúdo preservado)
      - Tabelas MD → data-table HTML (OK se dados preservados)
      - Listas → cards/grids (OK se itens preservados)
  - NÃO considerar como presente:
      - Item resumido ou abreviado
      - Item parcialmente incluído
      - Item com dados alterados
```

### DCU-06: Reportar Gaps

```yaml
output_format:
  missing_sections: []
  missing_data: []
  missing_quotes: []
  missing_structures: []
  total_gaps: N
  severity: CRITICAL|HIGH|MEDIUM|LOW

severity_rules:
  CRITICAL: seções inteiras faltando
  HIGH: dados numéricos ou citações faltando
  MEDIUM: itens de lista faltando
  LOW: formatação não-transformada
```

### DCU-07: Corrigir Gaps

```yaml
correction_strategy: 1. Identificar localização correta no HTML
  2. Criar componente visual apropriado
  3. Inserir conteúdo preservando 100% do texto
  4. Manter consistência de estilo (CSS variables)
  5. Verificar que inserção não quebra layout
```

### DCU-08: Re-verificar

```yaml
loop:
  max_iterations: 3
  exit_condition: total_gaps == 0
  on_max_iterations_reached:
    - Reportar gaps restantes
    - Solicitar intervenção manual
    - NÃO aprovar documento
```

### DCU-09: Gerar Relatório

```yaml
report_template: |
  ═══════════════════════════════════════════════════════════════
  GATE-6 DOUBLE CHECK-UP REPORT
  ═══════════════════════════════════════════════════════════════

  Documento: {doc_name}
  Source: {source_path}
  Output: {output_path}

  ───────────────────────────────────────────────────────────────
  EXTRAÇÃO DO SOURCE
  ───────────────────────────────────────────────────────────────
  Seções encontradas: {sections_count}
  Dados numéricos: {data_count}
  Citações: {quotes_count}
  Estruturas: {structures_count}
  TOTAL ITENS: {total_items}

  ───────────────────────────────────────────────────────────────
  VERIFICAÇÃO NO OUTPUT
  ───────────────────────────────────────────────────────────────
  Itens presentes: {present_count}/{total_items}
  Itens faltantes: {missing_count}
  Taxa de cobertura: {coverage_percent}%

  ───────────────────────────────────────────────────────────────
  CORREÇÕES APLICADAS
  ───────────────────────────────────────────────────────────────
  Iteração 1: {iter1_fixes} correções
  Iteração 2: {iter2_fixes} correções
  Iteração 3: {iter3_fixes} correções

  ───────────────────────────────────────────────────────────────
  RESULTADO FINAL
  ───────────────────────────────────────────────────────────────
  Status: {APROVADO|REPROVADO}
  Cobertura final: {final_coverage}%
  Gaps restantes: {remaining_gaps}

  ═══════════════════════════════════════════════════════════════
```

### DCU-10: Aprovar Documento

```yaml
approval_criteria:
  - total_gaps == 0
  - coverage_percent == 100
  - no_critical_issues
  - no_high_issues

on_approval:
  - Atualizar SESSION-STATE.md
  - Atualizar status.json
  - Marcar documento como VERIFIED
  - Liberar para próximo documento

on_rejection:
  - Manter status IN_PROGRESS
  - Listar ações necessárias
  - Solicitar correção manual
```

---

## INTEGRAÇÃO COM PIPELINE

### Antes do GATE-6:

```
GATE-1 → GATE-2 → GATE-3 → GATE-4 → GATE-5 → [HTML GERADO]
```

### Com GATE-6:

```
GATE-1 → GATE-2 → GATE-3 → GATE-4 → GATE-5 → GATE-6 → [HTML VERIFICADO] → OUTPUT
                                                ↑              │
                                                └──── LOOP ────┘
                                                 (se gaps > 0)
```

---

## INVOCAÇÃO

```bash
# Executar GATE-6 em um documento
@doc-validator verify --source <source.md> --output <output.html>

# Executar GATE-6 em batch (múltiplos documentos)
@doc-validator verify-batch --batch-id BILHON-BATCH-7
```

---

## EXEMPLO DE EXECUÇÃO

```
═══════════════════════════════════════════════════════════════
GATE-6 INICIANDO: DOC 2 - APRESENTACAO-TIME-COMERCIAL-BILLION
═══════════════════════════════════════════════════════════════

[DCU-01] Extraindo seções... 24 encontradas
[DCU-02] Extraindo dados numéricos... 47 encontrados
[DCU-03] Extraindo citações... 12 encontradas
[DCU-04] Extraindo estruturas... 18 encontradas
─────────────────────────────────────────────────────────────
TOTAL: 101 itens para verificar

[DCU-05] Verificando presença no HTML...
─────────────────────────────────────────────────────────────
✓ Seções: 24/24
✓ Dados: 45/47 (2 FALTANDO)
✓ Citações: 12/12
✓ Estruturas: 17/18 (1 FALTANDO)

[DCU-06] GAPS ENCONTRADOS: 3
─────────────────────────────────────────────────────────────
1. [DATA] RESULTADO MÉDIO DOS ALUNOS: $30-40K/ano → $20-30K/mês
2. [DATA] +600% na renda
3. [STRUCTURE] SOCIAL SELLING (OPCIONAL) role card

[DCU-07] Aplicando correções...
─────────────────────────────────────────────────────────────
✓ Adicionado: RESULTADO MÉDIO DOS ALUNOS box
✓ Adicionado: SOCIAL SELLING role card

[DCU-08] Re-verificando...
─────────────────────────────────────────────────────────────
✓ Seções: 24/24
✓ Dados: 47/47
✓ Citações: 12/12
✓ Estruturas: 18/18

[DCU-09] Gerando relatório...
[DCU-10] DOCUMENTO APROVADO ✓

═══════════════════════════════════════════════════════════════
GATE-6 COMPLETO: 100% de cobertura alcançada
═══════════════════════════════════════════════════════════════
```

---

## ═══════════════════════════════════════════════════════════════════════════════

## GATE-7: OBSIDIAN LAPIDATION - Polimento Artístico Premium

## ═══════════════════════════════════════════════════════════════════════════════

> **Objetivo:** Adicionar camada final de polimento artístico Dark Gold
> **Executa após:** GATE-6 aprovado com 100% de conteúdo
> **Foco:** Elevar elementos visuais fracos ao padrão premium

---

## WORKFLOW DO GATE-7

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GATE-7: OBSIDIAN LAPIDATION                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT: HTML verificado pelo GATE-6 (100% conteúdo)                        │
│                                                                             │
│  FASE 1: DETECTION (Weak Visual Patterns)                                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ├── [LAP-01] Scan weak paragraphs (>200 palavras sem formatação)          │
│  ├── [LAP-02] Scan basic lists (sem ícones/cards)                          │
│  ├── [LAP-03] Scan plain tables (sem premium styling)                      │
│  └── [LAP-04] Scan inline metrics (números que deveriam ser stats)         │
│                                                                             │
│  FASE 2: LAPIDATION (Transform to Premium)                                  │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ├── [LAP-05] Apply callout treatment (parágrafos → callout-box)           │
│  ├── [LAP-06] Apply icon treatment (listas → feature-grid + Phosphor)      │
│  ├── [LAP-07] Apply table premium (tabelas → data-table premium)           │
│  └── [LAP-08] Extract metrics to cards (números → stat-cards)              │
│                                                                             │
│  FASE 3: EXEMPLIFICATION                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ├── [LAP-09] Identify abstract concepts (teoria sem exemplo)              │
│  └── [LAP-10] Add practical examples (inserir example-boxes)               │
│                                                                             │
│  FASE 4: VALIDATION                                                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│  ├── [LAP-11] Visual consistency (CSS variables em todos elementos)        │
│  └── [LAP-12] Premium threshold check (score visual ≥85%)                  │
│                                                                             │
│  OUTPUT: premium_html → FINAL DELIVERY                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## INTELIGÊNCIA DE DETECÇÃO (Weak Visual Patterns)

### Padrões a Detectar

| ID     | Padrão Fraco                   | Descrição                                  | Transformação Premium                  |
| ------ | ------------------------------ | ------------------------------------------ | -------------------------------------- |
| WVP-01 | Parágrafos longos sem destaque | Texto corrido >200 palavras sem formatação | Callout-box, blockquotes, highlights   |
| WVP-02 | Listas simples sem ícones      | `<ul>/<ol>` sem visual treatment           | Feature-grid com ícones Phosphor       |
| WVP-03 | Tabelas básicas                | Tabela sem gradients/hover                 | Data-table premium com header gradient |
| WVP-04 | Números soltos no texto        | Métricas sem destaque visual               | Stats-grid ou metric-cards             |
| WVP-05 | Citações sem card              | Texto entre aspas sem componente           | Quote-card com aspas oversized         |
| WVP-06 | Processos em lista             | Steps descritos em lista simples           | Stepper-container ou timeline          |
| WVP-07 | Conceitos sem exemplo          | Teoria sem ilustração prática              | Example-box ou comparison              |
| WVP-08 | Hierarquias em texto           | Níveis descritos linearmente               | Hierarchy-tree ou org-cards            |
| WVP-09 | Comparações em parágrafo       | A vs B em texto corrido                    | Comparison-container visual            |
| WVP-10 | Fórmulas sem destaque          | Cálculos em texto inline                   | Formula-card ou terminal-block         |
| WVP-11 | Cards sem hover/glow           | Cards sem interatividade visual            | Adicionar hover + gold glow            |
| WVP-12 | Seções sem divisor             | Transições abruptas entre seções           | Section-divider com ícone              |

### Algoritmo de Detecção

```yaml
detection_algorithm:
  for_each_element_in_html:
    1. Classificar tipo (parágrafo, lista, tabela, etc.)
    2. Verificar "visual treatment":
       - Tem classe premium? (callout-box, stats-grid, etc.)
       - Tem ícone Phosphor?
       - Tem gradients/shadows?
       - Tem hover effects?
    3. SE sem treatment → MARCAR como candidato
    4. Calcular visual_weakness_score (0-100)
    5. SE score > 60 → ADICIONAR à lista de lapidação
```

---

## CHECKLIST DE LAPIDAÇÃO (LAP-01 a LAP-12)

### FASE 1: DETECTION

#### LAP-01: Scan Weak Paragraphs

```yaml
what_to_detect:
  - Parágrafos com >200 palavras
  - Texto corrido sem formatação
  - Blocos de texto sem destaque visual

transformation:
  - Quebrar em blocos menores
  - Adicionar callout-box para pontos-chave
  - Aplicar highlights em termos importantes
```

#### LAP-02: Scan Basic Lists

```yaml
what_to_detect:
  - <ul> ou <ol> sem classes premium
  - Listas sem ícones
  - Listas com >5 itens sem agrupamento

transformation:
  - Converter para feature-grid
  - Adicionar ícones Phosphor apropriados
  - Aplicar hover effects
```

#### LAP-03: Scan Plain Tables

```yaml
what_to_detect:
  - Tabelas sem classe .data-table
  - Tabelas sem header gradient
  - Tabelas sem hover row

transformation:
  - Aplicar classe .data-table
  - Adicionar gradient no header
  - Adicionar hover:bg-gold-dim nas rows
```

#### LAP-04: Scan Inline Metrics

```yaml
what_to_detect:
  - Números importantes inline (R$, $, %, etc.)
  - Métricas sem destaque
  - KPIs em texto corrido

transformation:
  - Extrair para stat-card
  - Criar stats-grid para múltiplas métricas
  - Aplicar animação progressFill se aplicável
```

### FASE 2: LAPIDATION

#### LAP-05: Apply Callout Treatment

```yaml
action: Transform weak paragraphs to callout-boxes
component: callout-box
css_required:
  background: var(--glass-bg)
  backdrop-filter: var(--glass-blur)
  border: 1px solid var(--obsidian-border)
  border-left: 3px solid var(--gold-primary)
```

#### LAP-06: Apply Icon Treatment

```yaml
action: Add Phosphor icons to lists
icon_mapping:
  features: ph-check-circle
  benefits: ph-star
  warnings: ph-warning
  steps: ph-number-circle-*
  info: ph-info
icon_style: ph-duotone
```

#### LAP-07: Apply Table Premium

```yaml
action: Elevate tables to premium styling
required_css:
  header:
    background: linear-gradient(135deg, var(--obsidian-elevated) 0%, var(--obsidian-surface) 100%)
    border-bottom: 2px solid var(--gold-dim)
  row:
    hover: background-color: rgba(201, 162, 39, 0.05)
  cell:
    border: 1px solid var(--obsidian-border)
```

#### LAP-08: Extract Metrics to Cards

```yaml
action: Create stat-cards for important numbers
component: stat-card
structure:
  number: large, gold color, with glow
  label: uppercase, small, muted
  trend: optional, green/red indicator
```

### FASE 3: EXEMPLIFICATION

#### LAP-09: Identify Abstract Concepts

```yaml
detection:
  - Conceitos teóricos sem caso concreto
  - Fórmulas sem aplicação numérica
  - Processos sem demonstração
  - Comparações sem visualização

indicators:
  - Palavras: "conceito", "teoria", "princípio", "metodologia"
  - Ausência de números/exemplos próximos
```

#### LAP-10: Add Practical Examples

```yaml
action: Insert example-boxes where needed
component: example-box
structure: |
  <div class="example-box">
    <div class="example-header">
      <i class="ph-duotone ph-lightbulb"></i>
      <span>EXEMPLO PRÁTICO</span>
    </div>
    <div class="example-content">
      {{EXEMPLIFICATION_CONTENT}}
    </div>
  </div>

css_required:
  background: var(--glass-bg)
  border: 1px solid var(--gold-dim)
  border-radius: 8px
  padding: var(--space-4)
```

### FASE 4: VALIDATION

#### LAP-11: Visual Consistency Check

```yaml
verify:
  - TODOS os elementos usam CSS variables
  - NENHUM valor hardcoded (#c9a227, #0a0a0a)
  - Hover effects em elementos interativos
  - Transições suaves (transition: all 0.3s ease)
```

#### LAP-12: Premium Threshold Check

```yaml
scoring:
  elements_with_premium_treatment: X
  total_transformable_elements: Y
  visual_score: (X / Y) * 100

threshold:
  pass: ≥85%
  excellent: ≥95%

on_below_threshold:
  - Loop back to FASE 2
  - Max 2 iterations
```

---

## RELATÓRIO DE LAPIDAÇÃO (Exemplo)

```
═══════════════════════════════════════════════════════════════
GATE-7 OBSIDIAN LAPIDATION REPORT
═══════════════════════════════════════════════════════════════

Documento: 04-OBS-ORGANOGRAMA-VISUAL.html
Entrada: GATE-6 VERIFIED (100% conteúdo)

───────────────────────────────────────────────────────────────
FASE 1: DETECÇÃO DE ELEMENTOS FRACOS
───────────────────────────────────────────────────────────────
Parágrafos fracos: 3
Listas sem ícones: 5
Tabelas básicas: 2
Métricas inline: 8
TOTAL CANDIDATOS: 18 elementos

───────────────────────────────────────────────────────────────
FASE 2: LAPIDAÇÃO APLICADA
───────────────────────────────────────────────────────────────
✓ 3 parágrafos → callout-box
✓ 5 listas → feature-grid com ícones
✓ 2 tabelas → data-table premium
✓ 8 métricas → stat-cards

───────────────────────────────────────────────────────────────
FASE 3: EXEMPLIFICAÇÃO
───────────────────────────────────────────────────────────────
Conceitos abstratos detectados: 2
Example-boxes adicionados: 2

───────────────────────────────────────────────────────────────
RESULTADO FINAL
───────────────────────────────────────────────────────────────
Visual Score Antes: 72%
Visual Score Depois: 94%
Elementos Lapidados: 18
Exemplos Adicionados: 2

Status: ✓ PREMIUM APPROVED
═══════════════════════════════════════════════════════════════
```

---

## PIPELINE COMPLETA (v3.3)

```
GATE-1 → GATE-2 → GATE-3 → GATE-4 → GATE-5 → GATE-6 → GATE-7 → OUTPUT
                                               │         │
                                    @doc-validator ──────┤
                                    (Double Check-Up)    │
                                                         │
                                    @doc-validator ──────┘
                                    (Obsidian Lapidation)
```

---

_@doc-validator v2.0.0 - GATE-6 Double Check-Up + GATE-7 Obsidian Lapidation_
_Parte do BILHON Design System v7.3 - Pipeline v3.3_
---
*AIOS Agent - Synced from .aiox/development/agents/doc-validator.md*
