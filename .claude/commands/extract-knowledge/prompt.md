# Extract Knowledge Command

## Purpose

Extract structured knowledge from content following the DNA YAML schema. This command analyzes text content (transcripts, articles, books, courses) and extracts:

- FILOSOFIAS (core philosophical principles)
- FRAMEWORKS (structured methodologies)
- HEURISTICAS (decision rules and heuristics)
- METODOLOGIAS (step-by-step processes)
- MODELOS-MENTAIS (conceptual thinking models)

## Usage

```
*extract-knowledge {content_path_or_source}
*extract-knowledge --inline (for content in conversation)
*extract-knowledge --batch {folder_path}
```

## Arguments

- `content_path_or_source`: Path to file or content identifier
- `--inline`: Extract from content provided in the message
- `--batch`: Process multiple files in a folder
- `--output`: Output path (default: .aiox/data/knowledge/dna/)
- `--source-id`: Source identifier for citation tracking

## Extraction Process

### Phase 1: Content Analysis

1. Read and parse the source content
2. Identify the speaker/author (e.g., "Cole Gordon", "Alex Hormozi")
3. Determine content type (video transcript, article, book chapter)
4. Note source metadata (title, date, URL if applicable)

### Phase 2: Extract FILOSOFIAS (Philosophical Principles)

Look for:

- Core beliefs and values expressed
- Fundamental truths the author operates by
- "I believe...", "The truth is...", "Always remember..."
- Principles that guide decision-making

Output format:

```yaml
filosofias:
  - id: 'FIL-{SOURCE}-{NUM}'
    nome: '{principle_name}'
    descricao: '{what it means}'
    citacao_original: '{exact quote}'
    chunk_id: '{source_reference}'
    peso: { 0.0-1.0 } # confidence/importance
```

### Phase 3: Extract FRAMEWORKS (Structured Methodologies)

Look for:

- Named systems or frameworks ("The CLOSER Framework")
- Acronyms that stand for processes
- Multi-step approaches with clear structure
- "There are X steps to...", "The framework has..."

Output format:

```yaml
frameworks:
  - id: 'FW-{SOURCE}-{NUM}'
    nome: '{framework_name}'
    tipo: 'sequencia|lista|matriz|ciclo|progressao'
    estrutura:
      componentes:
        - nome: '{step/component}'
          descricao: '{what this does}'
    como_usar: '{instructions}'
    quando_usar: ['{scenario1}', '{scenario2}']
    evidencias:
      - citacao: '{exact quote}'
        chunk_id: '{reference}'
    peso: { 0.0-1.0 }
```

### Phase 4: Extract HEURISTICAS (Rules of Thumb)

Look for:

- Quick decision rules
- "If X, then Y" patterns
- "Never do X", "Always do Y"
- Rules that simplify complex decisions

Output format:

```yaml
heuristicas:
  - id: 'HEU-{SOURCE}-{NUM}'
    regra: '{the rule}'
    contexto: '{when it applies}'
    consequencia_positiva: '{what happens if followed}'
    consequencia_negativa: '{what happens if ignored}'
    evidencias:
      - citacao: '{exact quote}'
    peso: { 0.0-1.0 }
```

### Phase 5: Extract METODOLOGIAS (Step-by-Step Processes)

Look for:

- Detailed step-by-step instructions
- "First... then... finally..."
- Processes with clear sequence and expected outcomes
- Repeatable procedures

Output format:

```yaml
metodologias:
  - id: 'MET-{SOURCE}-{NUM}'
    nome: '{methodology_name}'
    descricao: '{what it accomplishes}'
    passos:
      - ordem: 1
        acao: '{what to do}'
        resultado_esperado: '{expected outcome}'
    quando_usar: '{context}'
    indicadores_sucesso: ['{indicator1}']
    erros_comuns: ['{mistake1}']
    evidencias:
      - citacao: '{exact quote}'
    peso: { 0.0-1.0 }
```

### Phase 6: Extract MODELOS-MENTAIS (Mental Models)

Look for:

- Conceptual frameworks for thinking
- Analogies and metaphors used to explain
- Ways to view or interpret situations
- "Think of it like...", "The way I see it..."

Output format:

```yaml
modelos_mentais:
  - id: 'MM-{SOURCE}-{NUM}'
    nome: '{model_name}'
    descricao: '{how to think about it}'
    aplicacao: '{how to use this model}'
    exemplo: '{concrete example}'
    evidencias:
      - citacao: '{exact quote}'
    peso: { 0.0-1.0 }
```

## Output Structure

### Single Source Output

```yaml
# {source_name} - Knowledge Extraction
# Generated: {date}
# Source: {source_id}

pessoa: '{author_name}'
versao: '1.0.0'
data_extracao: '{ISO_date}'
fonte: '{source_identifier}'

filosofias:
  # ... extracted items

frameworks:
  # ... extracted items

heuristicas:
  # ... extracted items

metodologias:
  # ... extracted items

modelos_mentais:
  # ... extracted items
```

### File Naming Convention

- `{source-id}-filosofias.yaml`
- `{source-id}-frameworks.yaml`
- `{source-id}-heuristicas.yaml`
- `{source-id}-metodologias.yaml`
- `{source-id}-modelos-mentais.yaml`

Or single consolidated file:

- `{source-id}-complete.yaml`

## Quality Guidelines

### Extraction Rules

1. **Cite exactly**: Always include the exact quote as evidence
2. **Assign confidence**: peso = 0.9+ for explicit statements, 0.7-0.8 for implied
3. **Use original language**: Preserve technical terms and expressions
4. **Cross-reference**: Link related items across categories
5. **Don't invent**: Only extract what's explicitly stated or clearly implied

### ID Convention

- FIL = Filosofia
- FW = Framework
- HEU = Heuristica
- MET = Metodologia
- MM = Modelo Mental
- Source codes: CG (Cole Gordon), AH (Alex Hormozi), JM (Jeremy Miner)

### Domains

Tag each item with relevant domains for searchability:

```yaml
dominios:
  - 'sales-process'
  - 'objection-handling'
  - 'closing'
  - 'prospecting'
  - 'qualification'
  - 'follow-up'
  - 'mindset'
  - 'leadership'
```

## Integration

### Output Location

Default: `.aiox/data/knowledge/dna/{persona}/`

### Update INDEX.yaml

After extraction, update `.aiox/data/knowledge/dna/INDEX.yaml` with new source.

### Validate Output

Run YAML linter on all generated files before committing.

## Examples

### Example 1: Extract from transcript

```
*extract-knowledge "transcripts/cole-gordon-sales-training.txt" --source-id CG-ST001
```

### Example 2: Inline extraction

```
*extract-knowledge --inline
[paste content here]
```

### Example 3: Batch processing

```
*extract-knowledge --batch "raw-transcripts/" --output "dna/cole-gordon/"
```

---

_AIOS Knowledge Extraction Command - Mega Brain Integration_
