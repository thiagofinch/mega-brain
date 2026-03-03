# CONSTITUTION - MEGA BRAIN SYSTEM

> **Versão:** 2.0.0
> **Criado:** 2026-02-18
> **Base:** Evolução da CONSTITUICAO-BASE.md v1.0.0
> **Escopo:** TODOS os agentes, hooks, skills e pipelines operam sob esta Constitution
> **Hierarquia:** Este documento tem precedência ABSOLUTA sobre qualquer outro

---

## HIERARQUIA NORMATIVA

```
CONSTITUTION.md (este documento)
        │ NON-NEGOTIABLE — prevalece sobre tudo
        ▼
AGENT-AUTHORITY.md
        │ MUST — define quem faz o quê
        ▼
ENFORCEMENT.md + ANTHROPIC-STANDARDS.md
        │ MUST — enforcement técnico
        ▼
Protocolos Específicos (pipeline/, council/, dna/)
        │ SHOULD — processos operacionais
        ▼
Instruções de Agente Individual
        │ MAY — customizações locais
        ▼
CONSTITUICAO-BASE.md (princípios filosóficos)
```

---

## ARTIGOS

### Article I: Pipeline Integrity — NON-NEGOTIABLE

> Todo conteúdo em `knowledge/` DEVE ter passado pelo pipeline completo.

**Regra:** Nenhum arquivo pode ser escrito em `knowledge/dossiers/`, `knowledge/themes/`, ou agent memories sem ter passado por todas as fases do pipeline (Chunks → Entities → Insights → Narratives → Output).

**Enforcement:**
- Hook: `enforce_before_knowledge_write()` em `ENFORCEMENT.md`
- Checkpoints bloqueantes entre fases (PHASE_2 → PHASE_7)
- State files (`CHUNKS-STATE.json`, `INSIGHTS-STATE.json`, `NARRATIVES-STATE.json`) devem existir e ser válidos

**Violação:** BLOQUEAR operação. Exibir `ENFORCEMENT ERROR` com código e resolução.

**Bypass:** Apenas com `--bypass-enforcement --reason "justificativa com 10+ chars"`. Gera log de auditoria especial.

---

### Article II: Source Isolation — NON-NEGOTIABLE

> Cada source (pessoa/framework) mantém dados isolados e rastreáveis.

**Regra:**
1. Cada source tem um `source_id` canônico (ex: `AH`, `JH`, `CG`)
2. Chunks, insights e narrativas DEVEM referenciar o `source_id` de origem
3. Cross-contamination (dados de Source A aparecendo em Output de Source B) é proibida
4. Entity resolution deve usar `CANONICAL_ENTITIES` com fuzzy matching (threshold 0.85)

**Enforcement:**
- `mission_pipeline.py`: `resolve_entities()` com two-pass matching
- `mission_feed.py`: `SOURCE_TO_SLUG` mapping com edge cases

**Violação:** BLOQUEAR. Output contaminado deve ser regenerado a partir dos chunks.

---

### Article III: Cascateamento Obrigatório — MUST

> Alterações em dados upstream DEVEM propagar para downstream.

**Regra:** Quando chunks são atualizados, TODOS os derivados devem ser regenerados:

```
Chunks (upstream) → Insights → Narratives → Dossiers → Agent Memories (downstream)
```

**Enforcement:**
- Hook: `post_batch_cascading.py` (PostToolUse)
- Flag `cascading_executed` em batch logs
- `--continuous` mode propaga automaticamente

**Violação:** WARNING. Agent memories podem ficar stale. `mission_feed.py` deve ser re-executado.

---

### Article IV: Agent Authority — MUST

> Cada categoria de agente tem domínio exclusivo e intransferível.

**Regra:** Ver `AGENT-AUTHORITY.md` para matrix completa. Resumo:

| Categoria | Domínio | Pode Escrever Em |
|-----------|---------|-------------------|
| PERSON agents | Conhecimento do expert | `agents/persons/{slug}/`, `knowledge/dossiers/persons/` |
| CARGO agents | Conhecimento do cargo | `agents/cargo/{cargo}/` |
| SYSTEM agents | Operações do sistema | `.claude/`, `system/`, `logs/` |
| COUNCIL agents | Decisões coletivas | `agents/council/`, `agents/boardroom/` |
| PIPELINE agents | Processamento de dados | `processing/`, `logs/` |

**Enforcement:**
- Agent memory isolation: `.claude/agent-memory/{slug}/MEMORY.md`
- Hooks: `skill_router.py` (READ), `agent_memory_persister.py` (WRITE)
- Definição (`.aios-core/`, `agents/`) ≠ Memória de runtime (`.claude/agent-memory/`)

**Violação:** WARNING. Operações cross-domain devem ser justificadas e logadas.

---

### Article V: Quality Gates — MUST

> Nenhum batch avança se quality gate falhar.

**Regra:**
1. Batch com >25% failure rate é BLOQUEADO (modo `--strict`)
2. Anomalias (ZERO_CHUNKS, NO_INSIGHTS, HIGH_FAILURE_RATE) são logadas em `logs/anomalies/`
3. Missing files são rastreados em `logs/missing-files.json`
4. Chunk indexer (`chunk_indexer.py`) mantém `_INDEX.json` atualizado

**Enforcement:**
- `check_batch_quality_gate()` em `jarvis_mission.py`
- `_detect_batch_anomalies()` em `mission_pipeline.py`
- State tracking: `state['totals']['anomalies_detected']`, `state['totals']['missing_files']`

**Violação (--strict mode):** BLOQUEAR avanço. Requer correção manual.
**Violação (normal mode):** WARNING + log. Pipeline continua.

---

### Article VI: Documentation — SHOULD

> Todo componente significativo deve ter documentação mínima.

**Regra:**
1. Agentes DEVEM ter header com: nome, categoria, dependências
2. Skills DEVEM ter: Auto-Trigger, Keywords, Prioridade, Tools, "Quando NÃO Ativar"
3. Hooks DEVEM ter: timeout: 30, exit codes (0/1/2), lifecycle event
4. Protocolos DEVEM ter: versão, data, propósito, escopo

**Enforcement:**
- `ANTHROPIC-STANDARDS.md`: checklists de validação
- `creation_validator.py` (PreToolUse): valida criações

**Violação:** WARN (aviso, não bloqueia). Documentar na próxima oportunidade.

---

## SEVERITY LEVELS

| Nível | Tag | Ação | Exemplos |
|-------|-----|------|----------|
| NON-NEGOTIABLE | `[NON-NEG]` | BLOQUEAR automaticamente, sem exceções | Pipeline Integrity, Source Isolation |
| MUST | `[MUST]` | WARNING + confirmação obrigatória | Cascateamento, Agent Authority, Quality Gates |
| SHOULD | `[SHOULD]` | Sugestão, pode ignorar com justificativa | Documentation |

---

## PRINCÍPIOS FILOSÓFICOS (Herdados da CONSTITUICAO-BASE)

Os 4 princípios fundamentais da CONSTITUICAO-BASE.md v1.0.0 permanecem vigentes:

1. **EMPIRISMO** — Decisões baseadas em dados, não opiniões
2. **PARETO (80/20)** — 20% das ações que geram 80% dos resultados
3. **INVERSÃO** — Antes de decidir o que fazer, perguntar o que faria falhar
4. **ANTIFRAGILIDADE** — Preferir opções que se beneficiam de volatilidade

Estes princípios guiam a TOMADA DE DECISÃO dos agentes. Os Articles acima guiam a OPERAÇÃO do sistema.

---

## ARCHITECTURAL DECISIONS

### ADR-001: Python-Only Pipeline (No YAML Workflows)

**Decisão:** Mega Brain usa Python scripts como workflow engine. NÃO usar YAML workflow definitions.

**Contexto:** aios-core usa YAML workflows para orchestration declarativa. Mega Brain avaliou a mesma abordagem.

**Razão:**
1. Pipeline já implementado em Python (`jarvis_mission.py`, `mission_pipeline.py`, `mission_feed.py`)
2. Lógica de entity resolution, fuzzy matching e anomaly detection é complexa demais para YAML
3. Python permite debugging direto, step-through e unit testing
4. Overhead de YAML parser + interpreter não justificado para um único pipeline
5. Configuração parametrizada já via argparse flags (`--loop`, `--continuous`, `--strict`, `--incremental`)

**Consequência:** Novos workflows devem ser implementados como Python scripts em `.claude/mission-control/` ou `scripts/`.

### ADR-002: Semantic Routing via Keyword Matching

**Decisão:** Auto-routing de skills/sub-agents usa keyword matching no prompt, implementado em `skill_router.py`.

**Intent Table:**

| Intent | Keywords | Roteado Para | Tipo |
|--------|----------|--------------|------|
| Pipeline execution | "pipeline", "batch", "processar", "ingest" | JARVIS Pipeline | SYSTEM |
| Knowledge query | "dossier", "knowledge", "consultar" | Relevant PERSON/CARGO agent | AGENT |
| Council deliberation | "debate", "council", "deliberar", "war room" | Council agents | COUNCIL |
| Session management | "save", "resume", "sessão" | Session skills | SKILL |
| Mind cloning | "map", "clone", "DNA", "extração" | MMOS skills | SKILL |
| Briefing | "briefing", "status", "health" | JARVIS Briefing | SYSTEM |
| Validation | "validar", "verificar", "check" | Quality Watchdog | SYSTEM |
| Design/Visual | "figma", "miro", "design", "board" | MCP (figma/miro) | MCP |
| Task management | "clickup", "task", "tarefa" | MCP (clickup) | MCP |
| Automation | "n8n", "workflow", "automação" | MCP (n8n) | MCP |

**Cadeia de prioridade:** Slash command explícito → Keyword match → Fallback to JARVIS

---

## REFERÊNCIAS

| Documento | Path | Relação |
|-----------|------|---------|
| CONSTITUICAO-BASE.md | `system/protocols/CONSTITUICAO-BASE.md` | Princípios filosóficos |
| AGENT-AUTHORITY.md | `system/protocols/AGENT-AUTHORITY.md` | Authority matrix |
| ENFORCEMENT.md | `system/protocols/system/ENFORCEMENT.md` | Regras técnicas |
| ANTHROPIC-STANDARDS.md | `.claude/rules/ANTHROPIC-STANDARDS.md` | Standards de compliance |
| mcp-governance.md | `.claude/rules/mcp-governance.md` | MCP governance |

---

## CHANGELOG

| Versão | Data | Mudança |
|--------|------|---------|
| 2.0.0 | 2026-02-18 | Constitution formal com 6 Articles e severity levels |
| 1.0.0 | — | CONSTITUICAO-BASE.md (4 princípios filosóficos) |
