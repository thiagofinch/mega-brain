---
name: extract-knowledge
description: "Extrai conhecimento estruturado (frameworks, heurísticas, algoritmos, conceitos, metodologias, code snippets) de qualquer fonte: PDFs, sessões, transcrições, meetings, lives."
version: "1.0.0"
owner_squad: etl-ops-squad
megabrain_tier: Tier2
context: inline
agent: general-purpose
user-invocable: true
argument-hint: "[source path | --session | --youtube URL | --batch dir/]"
depends_on: []
---

# Extract Knowledge

Skill agnóstica de extração de conhecimento. Transforma qualquer fonte textual em entidades DS_KE estruturadas usando o pipeline híbrido (regex pre-filter + LLM curation) do `services/etl/`.

## Activation

```
/extract-knowledge data/etl/raw/Build_a_Multi-Agent*.pdf
/extract-knowledge --session
/extract-knowledge docs/sessions/2026-04/meeting.md
/extract-knowledge --youtube "https://youtube.com/watch?v=..."
/extract-knowledge --batch data/etl/raw/ --limit 10
/extract-knowledge --session --category heuristic --pareto
```

## Process

**ID:** SP-EXTRACT-KNOWLEDGE
**Mode:** CRIAR
**Agent:** runtime-resolved
**Estimated:** 5-30 min (depende do volume e uso de LLM)

## Pre-Requisites

1. Para PDFs: ficheiros existem no path indicado
2. Para `--session`: contexto da conversa atual disponível
3. Para `--youtube`: MCP scrapling disponível
4. Para LLM enrichment: `ANTHROPIC_API_KEY` definida no ambiente
5. Para batch: diretório com ficheiros processáveis (.pdf, .md, .txt)

## Arguments

| Arg | Type | Default | Description |
|-----|------|---------|-------------|
| `<path>` | positional | — | Ficheiro ou diretório a processar |
| `--session` | flag | false | Extrair da conversa atual do Claude Code |
| `--youtube <url>` | option | — | Extrair transcrição de vídeo YouTube |
| `--batch <dir>` | option | — | Processar todos os ficheiros de um diretório |
| `--category <cat>` | option | all | Filtrar para categoria(s): framework, heuristic, algorithm, concept, methodology, code_snippet |
| `--pareto` | flag | false | Aplicar Pareto ao Cubo (genialidade/excelência/impacto/descarte) |
| `--output <dir>` | option | data/etl/approved/ | Diretório de output (fonte canónica) |
| `--limit <n>` | option | 0 (all) | Máximo de ficheiros em batch |
| `--min-confidence <n>` | option | 0.70 | Threshold mínimo de confiança |
| `--decision-cards` | flag | false | Gerar L2 decision cards (compat squad-creator-pro) |
| `--dry-run` | flag | false | Listar candidatos sem persistir |

## Execution

### Phase 0: INPUT RESOLUTION

Detectar tipo de input e converter para markdown unificado.

**Adapter Selection:**

| Input | Adapter | Módulo |
|-------|---------|--------|
| `*.pdf` | PDF adapter | `services/etl/lib/pdf-parser.js` → `PdfParser.parseFile()` → `textToMarkdown()` |
| `--session` | Session adapter | Ler contexto completo da conversa atual (tool results + user messages) |
| `*.md` / `*.txt` | Markdown adapter | Ler direto, strip frontmatter YAML se existir |
| `--youtube <url>` | YouTube adapter | scrapling MCP `stealthy_fetch(url)` → extrair transcrição da página |
| `--batch <dir>` | Batch adapter | Listar ficheiros, aplicar adapter por extensão, processar sequencialmente |

**Regras:**
- PDF adapter detecta PDFs scanned (< 100 chars/página) e rejeita com aviso
- Session adapter extrai APENAS mensagens com conteúdo substantivo (ignora tool calls curtos)
- YouTube adapter tenta extrair transcrição da página; se não disponível, avisa e aborta
- Batch adapter respeita `--limit` e processa em ordem alfabética

**Gate:** Input convertido para markdown com ≥ 200 chars. Abaixo disso → abort com mensagem.

**Output deste phase:** `{ markdown: string, source_metadata: { source_id, source_name, source_type } }`

### Phase 1: CANDIDATE DETECTION

Detectar candidatos a entidades de conhecimento no markdown.

**Estratégia dual baseada no tipo de input:**

**SE input = session (--session):**
1. Varrer a conversa procurando candidatas em 5 categorias CDM:
   - **Decisões pivot** — momentos que mudaram o rumo
   - **Bugs/incidentes** — erros que revelaram regras
   - **Anti-patterns evitados** — o que quase deu errado
   - **Patterns validados** — o que funcionou e por quê
   - **Research insights** — confirmação/refutação externa
2. Aplicar Critical Decision Method questions:
   - "O que deu certo que NÃO ERA ÓBVIO?"
   - "O que quase deu errado? Em que PONTO EXATO?"
   - "Que regra SE/ENTÃO emergiu?"
3. Gerar candidate windows (~800 chars) ao redor de cada momento detectado

**SE input = PDF/markdown/youtube:**
1. Executar `extractCandidateWindows()` de `services/etl/lib/enrichment/regex-extractor.js`
   - Detecta: headings estruturados, code blocks, tabelas, referências bibliográficas
   - Detecta: AI named patterns (ReAct, RAG, LangGraph, etc.)
   - Detecta: Rule/heuristic patterns (if/when/never/always)
   - Detecta: Academic sections numeradas, key term definitions, numbered lists
2. Cada candidato inclui: `{ name, window (~800 chars), location, pattern_type, source_metadata }`

**Gate:** ≥ 3 candidatos brutos. Se < 3, fonte rasa → avisar e perguntar se quer prosseguir com menos.

### Phase 2: CLASSIFICATION

Classificar cada candidato numa das 6 categorias.

**Categorias válidas:**

| Categoria | Código | Descrição |
|-----------|--------|-----------|
| `framework` | FW | Arquiteturas, patterns de design, sistemas compostos |
| `heuristic` | HE | Regras SE/ENTÃO/NUNCA, princípios operacionais |
| `algorithm` | AL | Procedimentos computacionais, complexidade, otimização |
| `concept` | CO | Definições, termos técnicos, conceitos teóricos |
| `methodology` | ME | Processos, métodos, procedimentos step-by-step |
| `code_snippet` | CS | Código executável, exemplos práticos, snippets |

**SE `--category` especificado:** filtrar candidatos para apenas a(s) categoria(s) pedida(s) após classificação.

**SE `--pareto` flag ativo:** aplicar Pareto ao Cubo antes de prosseguir:

| Zone | Critério | Ação |
|------|----------|------|
| 0.8% Genialidade | Muda paradigma, insight único | PRIORIZAR |
| 4% Excelência | Guardrail contra retrabalho | PROCESSAR |
| 20% Impacto | Boa prática com evidência | PROCESSAR se ≥ 0.75 confidence |
| 80% Descarte | Genérico, sem evidência | DESCARTAR |

### Phase 3: LLM ENRICHMENT

Enriquecer candidatos aprovados com conteúdo estruturado via LLM.

**Módulo:** `services/etl/lib/enrichment/llm-extractor.js`
- Model: claude-sonnet-4-6 via Anthropic API
- Batch: 5 candidatos por chamada
- Retry: exponential backoff (2s, 4s, 8s) — máx 3 tentativas
- Fallback: se `ANTHROPIC_API_KEY` ausente → marcar como `llm_pending: true`

**Campos gerados por candidato:**

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `name` | SIM | Nome descritivo (≥ 3 palavras ou termo técnico conhecido) |
| `category` | SIM | Uma das 6 categorias |
| `confidence` | SIM | 0.0 a 1.0 |
| `summary` | SIM | 2-3 frases concisas |
| `problem` | SIM | Qual problema resolve |
| `content` | SIM | Explicação detalhada (campo mais longo) |
| `benefits` | NÃO | Lista de vantagens |
| `when_to_use` | NÃO | Cenários ideais |
| `when_not_to_use` | NÃO | Anti-patterns de uso |
| `application_rules` | SIM | Regras SE/ENTÃO/NUNCA (mín 2) |
| `tags` | SIM | Mín 2 tags relevantes |
| `code_blocks` | NÃO | Código extraído (language + description + code) |
| `cross_refs` | NÃO | Referências cruzadas a outras entidades |

**SE `--session` + `--category heuristic`:** enriquecer adicionalmente com:
- `sys_tension` (tension_with + resolution)
- `failure_modes` (omission + misapplication)
- Formato SE/ENTÃO/NUNCA obrigatório em `application_rules`

### Phase 4: DEDUP

Verificar duplicatas contra entidades existentes.

**Módulo:** `services/etl/lib/dedup-engine.js`

**3 estratégias (em ordem de prioridade):**

| Estratégia | Threshold | Confiança | Ação |
|------------|-----------|-----------|------|
| Exact name match | — | high | Auto-merge (manter mais recente) |
| Tags overlap (Jaccard) | > 0.70 | medium | Flag para review |
| Cosine similarity (TF-IDF) | > 0.85 | medium | Flag para review |

**Cross-dedup:** comparar candidatos novos contra TODAS as entidades no diretório de output.
- SE `--output data/etl/approved/` → comparar contra entidades existentes em approved/
- SE `--output minds/{owner}/heuristics/` → comparar contra decision-cards.yaml do owner

**Regra:** Duplicata COM nova evidência → flag `UPDATE` (enriquecer existente, não descartar).
Duplicata SEM nova evidência → `SKIP`.

### Phase 5: QUALITY GATE

Validar cada entidade contra critérios de qualidade.

**Regras base** (de `services/etl/lib/quality-gate.js`):

| # | Regra | Threshold |
|---|-------|-----------|
| 1 | Content + Summary ≥ 200 chars | BLOCK |
| 2 | Name ≥ 3 palavras (ou termo técnico conhecido) | BLOCK |
| 3 | Sem artefatos OCR | BLOCK |
| 4 | Application rules não vazio nem TODO/TBD | BLOCK |
| 5 | Confidence ≥ `--min-confidence` (default 0.70) | BLOCK |
| 6 | Tags ≥ 2 | BLOCK |
| 7 | Summary ≠ name (não idênticos) | BLOCK |

**Regras adicionais para category=heuristic:**

| # | Regra | Threshold |
|---|-------|-----------|
| 8 | Tem `[SOURCE:]` | BLOCK (VETO-ESH-001) |
| 9 | Evidência empírica (não sintetizada) | BLOCK (VETO-ESH-002) |
| 10 | sys_tension preenchido | WARN (status: draft) |

**Gate decision:**
- Todas as regras BLOCK passam → `status: validated`
- Regra WARN falha → `status: draft` (persistir com flag)
- Regra BLOCK falha → `REJECT` (não persistir)

**SE `--dry-run`:** listar resultado do quality gate sem persistir. Mostrar:
- Total candidatos: N
- Passaram: M (X%)
- Rejeitados: K (motivos)
- Duplicatas: J

### Phase 6: PERSIST

Gerar ficheiros de output em `data/etl/approved/` (FLAT).

**Output format:** `DS_KE_{CAT}_{NNN}.md` — ver `references/output-format.md`

**Sequência:**

1. **Auto-detect next ID** por categoria a partir dos ficheiros existentes em `data/etl/approved/`
2. **Gerar ficheiro markdown** com frontmatter YAML + 9 seções (Summary, Problem, Content, Benefits, When to Use, When NOT to Use, Application Rules, Code Blocks, Source Context)
3. **Ficheiros são FLAT em `data/etl/approved/`** (sem subdiretórios). Exemplo: `approved/DS_KE_HE_237.md`
4. **SE output = outro dir (ex: minds/):** ficheiros flat no dir indicado
5. **SE `--decision-cards`:** gerar/atualizar `decision-cards.yaml` no formato L2 compatível com squad-creator-pro

### Phase 7: FINALIZE (OBRIGATÓRIO — NON-NEGOTIABLE)

Após escrever TODOS os ficheiros em `approved/`, executar o pipeline de finalização:

**Step 7.1 — Dedup + Quality Gate + Merge + Renumber:**
```bash
node services/etl/bin/finalize-etl.js --input data/etl/approved
```
Este script executa:
- **Dedup** (3 estratégias: exact name, Jaccard tags > 0.70, TF-IDF cosine > 0.85)
- **Quality Gate** (7 regras: content≥200, name≥3 words, tags≥2, confidence≥0.70, etc.)
- **Merge** duplicatas com evidência nova
- **Renumber** IDs sequenciais por categoria (elimina gaps)
- **Backup** antes de alterar (data/etl/backup-finalize/)

**Step 7.2 — Rebuild Knowledge Base:**
```bash
node services/etl/bin/build-kb-index.js
```
Este script:
- Copia `approved/` + `gold-standard/` → `knowledge-base/` (com subdiretórios por categoria)
- Reconstrói `index.yaml` com contagem, confidence média, fontes

**Step 7.3 — Report final:**
Mostrar resumo com:
- Entidades antes vs depois da finalização
- Duplicatas removidas (count + lista)
- Entidades rejeitadas pelo QG (count + motivos)
- Total por categoria
- Confidence média

> **NUNCA escrever directamente em `data/etl/knowledge-base/`.** Este directório é DERIVADO.
> Pipeline: `approved/` → `finalize-etl.js` → `build-kb-index.js` → `knowledge-base/`
> Escrever em knowledge-base/ resulta em perda de dados na próxima execução do build.

**Naming convention:**

| Categoria | Prefixo | Exemplo |
|-----------|---------|---------|
| framework | FW | DS_KE_FW_028.md |
| heuristic | HE | DS_KE_HE_068.md |
| algorithm | AL | DS_KE_AL_022.md |
| concept | CO | DS_KE_CO_057.md |
| methodology | ME | DS_KE_ME_015.md |
| code_snippet | CS | DS_KE_CS_004.md |

**Commit message template:**
```
feat(kb): extract N entities from {source_name} [/extract-knowledge]
```

## Reused Modules

Esta skill NÃO duplica código — importa diretamente dos módulos existentes:

| Módulo | Path | Usado em |
|--------|------|----------|
| PdfParser | `services/etl/lib/pdf-parser.js` | Phase 0 (PDF adapter) |
| regex-extractor | `services/etl/lib/enrichment/regex-extractor.js` | Phase 1 (extractCandidateWindows) |
| llm-extractor | `services/etl/lib/enrichment/llm-extractor.js` | Phase 3 (LLM enrichment) |
| DedupEngine | `services/etl/lib/dedup-engine.js` | Phase 4 (dedup) |
| quality-gate | `services/etl/lib/quality-gate.js` | Phase 5 (validation) |
| DskeGenerator | `services/etl/lib/dske-generator.js` | Phase 6 (output) |
| EnrichmentPipeline | `services/etl/lib/enrichment/enrichment-pipeline.js` | Orquestrador L1→L2→L3 |

## Compatibility with extract-session-heuristics

| Cenário | Comportamento |
|---------|---------------|
| `/extract-session-heuristics` | Inalterado — continua v3.3, owner squad-creator-pro |
| `/extract-knowledge --session --category heuristic --pareto` | Replica comportamento, output em knowledge-base/ |
| Heurísticas com confidence ≥ 0.90 | Candidatas a promoção para PV_KE_* via protocolo existente |

**Regra:** `/extract-session-heuristics` permanece a skill canónica para heurísticas operacionais de sessão com Pareto ao Cubo completo, decision cards L2/L3, e promotion protocol. `/extract-knowledge` é complementar — extrai de qualquer fonte com foco em volume e diversidade de categorias.

## Veto Conditions

| ID | Condition | Action |
|----|-----------|--------|
| VETO-EK-001 | Input com < 200 chars após conversão | ABORT |
| VETO-EK-002 | < 3 candidatos brutos detectados | WARN (prosseguir com confirmação) |
| VETO-EK-003 | Entidade com confidence < min-confidence | REJECT |
| VETO-EK-004 | Heuristic sem [SOURCE:] | REJECT |
| VETO-EK-005 | Duplicata sem nova evidência | SKIP |
| VETO-EK-006 | PDF scanned (< 100 chars/página) | SKIP com aviso |

## Quality Gate

**Minimum pass rate:** 50% dos candidatos devem passar quality gate.
Se < 50% → avisar que a fonte pode ter baixa qualidade e sugerir revisão manual.

## Output Location

**Default:** `data/etl/approved/` (FLAT — sem subdiretórios por categoria)

> **NUNCA escrever directamente em `data/etl/knowledge-base/`.** Este directório é DERIVADO —
> reconstruído pelo `build-kb-index.js` a partir de `approved/` + `gold-standard/`.
> Escrever lá resulta em perda de dados na próxima execução do build script.

**Pipeline correcto:**
```
1. Skill escreve em → data/etl/approved/DS_KE_{CAT}_{NNN}.md (FLAT)
2. Rodar → node services/etl/bin/build-kb-index.js
3. Script copia approved/ + gold-standard/ → knowledge-base/ (com subdiretórios)
4. Script reconstrói index.yaml
```

**Alternativas via `--output`:**
- `data/etl/candidates/` — staging para review manual (Human-in-the-Loop)
- `squads/squad-creator-pro/minds/{owner}/heuristics/` — compat com extract-session-heuristics

## Tokens

| Token | Value | Purpose |
|-------|-------|---------|
| TKN-EK-THR-001 | ≥ 200 | Min chars após conversão para processar |
| TKN-EK-THR-002 | ≥ 3 | Min candidatos brutos |
| TKN-EK-THR-003 | ≥ 0.70 | Default min confidence |
| TKN-EK-THR-004 | ≥ 0.85 | Confidence para injection em squads |
| TKN-EK-THR-005 | > 0.85 | Cosine similarity threshold (dedup) |
| TKN-EK-THR-006 | > 0.70 | Tags overlap threshold (dedup) |
| TKN-EK-THR-007 | ≥ 50% | Min pass rate quality gate |
| TKN-EK-BEH-001 | 5 | LLM batch size |
| TKN-EK-BEH-002 | 3 | LLM max retries |
| TKN-EK-BEH-003 | 800 | Candidate window size (chars) |
