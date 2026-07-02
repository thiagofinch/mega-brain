# Output Format — DS_KE Entity Schema v1.0.0

## File Naming

```
DS_KE_{CATEGORY_PREFIX}_{NNN}.md
```

| Categoria | Prefixo | Exemplo |
|-----------|---------|---------|
| framework | FW | DS_KE_FW_028.md |
| heuristic | HE | DS_KE_HE_068.md |
| algorithm | AL | DS_KE_AL_022.md |
| concept | CO | DS_KE_CO_057.md |
| methodology | ME | DS_KE_ME_015.md |
| code_snippet | CS | DS_KE_CS_004.md |

**NNN** é sequencial por categoria, auto-detectado a partir dos ficheiros existentes no diretório de output.

## Directory Organization

Quando `organize_by_category: true` (default para `data/etl/knowledge-base/`):

```
data/etl/knowledge-base/
  index.yaml
  frameworks/     DS_KE_FW_*.md
  heuristics/     DS_KE_HE_*.md
  algorithms/     DS_KE_AL_*.md
  concepts/       DS_KE_CO_*.md
  methodologies/  DS_KE_ME_*.md
  code-snippets/  DS_KE_CS_*.md
```

Quando `organize_by_category: false` (flat mode):
```
output-dir/
  DS_KE_FW_028.md
  DS_KE_HE_068.md
  ...
```

## Entity File Structure

```markdown
---
id: DS_KE_FW_028
name: "Nome Descritivo do Conceito"
category: framework
source_name: "nome_do_ficheiro_fonte.pdf"
confidence: 0.88
extraction_method: llm
schema_version: "1.0.0"
cross_refs: [DS_KE_CO_012, DS_KE_AL_005]
tags: ["tag1", "tag2", "tag3"]
extracted_at: "2026-04-28T14:30:00.000Z"
---

# Nome Descritivo do Conceito

## Summary
2-3 frases concisas capturando a essência do conceito.

## Problem
Qual problema este conceito resolve? Por que existe?

## Content
Explicação detalhada com sub-seções se necessário.
Este é o campo mais longo — deve expandir significativamente o que está no texto-fonte.

## Benefits
- Benefício 1
- Benefício 2
- Benefício 3

## When to Use
Cenários ideais para aplicar este conceito. Condições que favorecem o uso.

## When NOT to Use
Cenários onde NÃO aplicar. Anti-patterns de uso. Condições que desfavorecem.

## Application Rules
- SE condição específica → ENTÃO aplicar desta forma
- SE outra condição → ENTÃO adaptar assim
- NUNCA fazer X porque causa Y

## Code Blocks

Descrição do que o código faz

```python
# código extraído ou derivado do texto
def example():
    pass
```

## Source Context
Extracted from: nome_do_ficheiro_fonte.pdf
```

## Frontmatter Fields

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | string | SIM | Identificador único (DS_KE_{PREFIX}_{NNN}) |
| `name` | string | SIM | Nome descritivo (≥ 3 palavras ou termo técnico) |
| `category` | string | SIM | framework/heuristic/algorithm/concept/methodology/code_snippet |
| `source_name` | string | SIM | Nome do ficheiro/fonte de origem |
| `confidence` | float | SIM | 0.0 a 1.0 — score de confiança da extração |
| `extraction_method` | string | SIM | "llm" ou "regex" |
| `schema_version` | string | SIM | "1.0.0" |
| `cross_refs` | string[] | NÃO | IDs de entidades relacionadas |
| `tags` | string[] | SIM | ≥ 2 tags técnicas relevantes |
| `extracted_at` | string | SIM | ISO 8601 timestamp |

## Body Sections

| Seção | Obrigatória | Descrição |
|-------|-------------|-----------|
| `Summary` | SIM | 2-3 frases. Nunca idêntica ao name. |
| `Problem` | SIM | Contexto do problema que resolve. |
| `Content` | SIM | Campo mais longo. Explicação detalhada. |
| `Benefits` | NÃO | Lista de vantagens. Omitir se não aplicável. |
| `When to Use` | NÃO | Cenários ideais. Omitir se não aplicável. |
| `When NOT to Use` | NÃO | Anti-patterns. Omitir se não aplicável. |
| `Application Rules` | SIM | ≥ 2 regras SE/ENTÃO/NUNCA acionáveis. |
| `Code Blocks` | NÃO | Código extraído. Omitir se sem código. |
| `Source Context` | SIM | Referência à fonte original. |

## Quality Thresholds

| Uso | Confidence mínima |
|-----|-------------------|
| Inclusão na knowledge base | ≥ 0.70 |
| Referência em squad config | ≥ 0.85 |
| Injection em agent persona | ≥ 0.85 |
| Candidata a promoção (heuristic → PV_KE_*) | ≥ 0.90 |

## Decision Cards (Formato L2 — opcional)

Quando `--decision-cards` ativo, gera/atualiza `decision-cards.yaml`:

```yaml
- id: DS_KE_HE_068
  name: "Nome da Heurística"
  rule: "SE condição → ENTÃO ação"
  zone: "excelencia"  # genialidade | excelencia | impacto
  trigger: "quando se aplica"
  anti_pattern: "o que acontece quando ignora"
  evidence: "dado empírico [SOURCE: ficheiro.pdf]"
  confidence: 0.88
  tags: ["tag1", "tag2"]
```

Este formato é compatível com `squads/squad-creator-pro/minds/{owner}/heuristics/decision-cards.yaml`.
