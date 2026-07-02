---
name: three-brain
description: |
  Auto-router que seleciona o motor AI ideal por tarefa. Claude = driver principal.
  Codex (GPT-5.5) = reviewer/rescue. Gemini 2.5 Pro = eyes/ears/long-context.
  CodeRabbit = structured code review (AST, security, best practices).
  Claude nunca revisa o proprio output — delega para Codex ou CodeRabbit automaticamente.
version: "1.1.0"
owner_squad: infra-ops-squad
megabrain_tier: Tier1
context: inline
agent: general-purpose
user-invocable: true
argument-hint: "[descricao da tarefa ou file glob]"
---

# Four-Brain Auto-Router — Mega Brain Edition

Quatro cerebros, um terminal. Claude e o driver — Codex, Gemini e CodeRabbit sao ferramentas que ele invoca.

- **Claude** = builder, driver, IDE harness — fica na frente do usuario
- **Codex (GPT-5.5)** = reviewer, second brain, rescue (via `codex:codex-rescue` agent ou `/codex:rescue` skill)
- **Gemini 2.5 Pro** = eyes, ears, long-context (via `cc-gemini-plugin:gemini-agent` agent ou `/cc-gemini-plugin:gemini` skill)
- **CodeRabbit** = structured code review, AST analysis, security scanning, best practices (via `coderabbit:code-reviewer` agent ou `/coderabbit-review` skill)

---

## LEI DO NO-SELF-REVIEW (LEIA PRIMEIRO)

Quando o usuario pede para Claude "conferir / revisar / verificar / auditar / segunda opiniao / sanity-check" QUALQUER trabalho que Claude acabou de produzir — codigo, escrita, plano, design — e OBRIGATORIO rotear para Codex.

Claude revisando o proprio output e exatamente o modo de falha que esta skill existe para prevenir. Mesma arquitetura = mesmos blind spots.

**Frases que DEVEM disparar Codex review (nao exaustivo):**
- "confere o que voce fez" / "revisa o codigo" / "ta certo isso?"
- "check your work" / "review what you just did" / "is this right?"
- "segunda opiniao" / "sanity check" / "double-check"
- "audita isso" / "verifica isso" / "tem algo errado?"

**Como rotear:**

```
Agent tool → subagent_type: "codex:codex-rescue"
prompt: "Review this diff. Find bugs, risks, missing tests. Be specific."
```

OU via Bash quando precisa pipar contexto:

```bash
git diff | codex exec "Review this. Find bugs, risks, missing tests."
```

Apos Codex retornar, integrar findings na resposta. Declarar ao final: `(Roteado via three-brain → Codex review.)`

---

## QUANDO DISPARAR (lista completa)

### MUST-FIRE (obrigatorio)

| Trigger | Rota | Como |
|---------|------|------|
| Usuario pede review/check do trabalho do Claude | Codex review | Agent `codex:codex-rescue` |
| "tear apart / stress test / poke holes / break this" | Codex adversarial review | Agent `codex:codex-rescue` |
| "estou preso / nao consigo / tenta GPT" OU Claude falhou 2x seguidas | Codex rescue | Agent `codex:codex-rescue` |
| Edit toca risk path (ver lista abaixo) | Codex adversarial review ANTES de dizer "done" | Anunciar visivelmente |
| PR pronto para review / pre-merge / "code review completo" | CodeRabbit structured review | Agent `coderabbit:code-reviewer` |
| Mudancas em 5+ arquivos OU PR com >200 linhas | CodeRabbit full scan | Agent `coderabbit:code-reviewer` |
| "analisa qualidade / best practices / code smells" | CodeRabbit quality review | Agent `coderabbit:code-reviewer` |
| Video (.mp4 .mov .webm), audio (.wav .mp3), PDF >50pg, YouTube URL | Gemini multimodal | Agent `cc-gemini-plugin:gemini-agent` |
| "scan the whole repo / find every place X / map the architecture" | Gemini 1M-context scan | Agent `cc-gemini-plugin:gemini-agent` |
| "ask all four / cross-architecture consensus" | Consensus mode (4 em paralelo) | Agents em paralelo |

### NAO DISPARAR

- "Explica / o que e / como funciona" → Claude direto
- "Escreve / cria / drafta" em paths nao-risky → Claude direto
- "Edita / refatora" em paths nao-risky → Claude direto
- "Planeja / brainstorm / outline" → Claude direto
- "Revisa meu email / meu texto" — conteudo do USUARIO, nao do Claude → Claude direto
- Chat casual, perguntas de status, file ops, git/bash → Claude direto

### DEFER TO EXISTING SKILLS (stay asleep)

NAO ativar quando estas skills ja estao rodando:

| Skill | Razao |
|-------|-------|
| `/develop-story`, `/review-story`, `/close-story` | SDC chain — lifecycle completo |
| `/deploy-story`, `/verify-deploy` | Deploy e EXCLUSIVO do `@devops` |
| `/roundtable` | Consensus multi-agente proprio |
| `/full-tec`, `/full-tec-*` | Task Execution Cycle com routing proprio |
| `/megabrain-pipeline` | Pipeline 7 fases com contexto de sessao |
| `/coderabbit-review` | Code review com self-healing loop |
| `/wave-execute` | Orchestracao paralela de stories |

---

## RISK PATHS — Mega Brain Monorepo

Codex review e forcado (sem usuario pedir) quando um edit ativo toca:

### HIGH RISK (Codex review obrigatorio)

```
apps/api/routers/auth.py              # fluxos de autenticacao
apps/api/services/auth.py             # servicos de auth
apps/api/**/permissions*              # permission checks
apps/web/src/**/use-auth*             # hooks de auth frontend
apps/web/src/**/use-permissions*      # hooks de permissao
packages/db/migrations/**             # schema changes (DB)
packages/db/supabase/functions/**     # edge functions
apps/gateway-ai/hooks/**/permission*  # permission gate OpenClaw
services/clickup/tasks.js             # 3-Zone contract sensitive
services/clickup/custom-fields.js     # UUID-sensitive operations
**/.env*                              # env handling
**/secrets/**                         # credentials
```

### MEDIUM RISK (Codex review recomendado, nao forcado)

```
apps/api/routers/**                   # qualquer endpoint API
apps/gateway-ai/**                    # gateway AI completo
services/**                           # business adapters
scripts/**                            # standalone scripts
```

### LOW RISK (Claude direto, sem Codex)

```
docs/**                               # documentacao
workspace/your-org/**               # workspace YAML configs
squads/*/data/**                      # knowledge base data
.claude/rules/**                      # regras do projeto
.claude/skills/**                     # skill definitions
```

**Keywords sozinhas (auth, payments, prod) em chat casual NAO disparam review** — precisa ser um edit ativo nos file paths.

---

## INTEGRACAO COM AGENT AUTHORITY (NON-NEGOTIABLE)

Three-brain e um **routing aid**, NAO um authority override. Regras inviolaveis:

| Agente | Regra | Three-brain NUNCA |
|--------|-------|-------------------|
| `@devops` | Exclusivo: git push, PR, deploy, MCP management | Executa push/deploy/PR |
| `@architect` | Exclusivo: decisoes de arquitetura | Decide tech stack |
| `@qa` | Exclusivo: quality sign-off | Da veredicto de qualidade |
| `@db-sage` | Exclusivo: migrations, schema, RLS | Executa migrations |
| `@clickup-chief` | Exclusivo: estruturas ClickUp | Cria Spaces/Folders/Lists |

Three-brain SUGERE qual engine usar. Authority rules permanecem.

---

## CODEX vs CODERABBIT — Quando Usar Cada Um

Codex e CodeRabbit sao COMPLEMENTARES, nao substitutos:

| Aspecto | Codex (GPT-5.5) | CodeRabbit |
|---------|-----------------|-----------|
| **Tipo de review** | Adversarial, criativo, segunda opiniao | Estruturado, AST-level, best practices |
| **Forca** | Encontra bugs logicos, propoe alternativas, rescue | Security scanning, code smells, convencoes |
| **Quando** | Review ad-hoc do output do Claude, rescue | Pre-merge sistematico, quality gates |
| **Velocidade** | Rapido (~20s) | Lento (~7-30min, WSL) |
| **Escopo** | Diff ou contexto especifico | Codebase inteiro ou diff completo |
| **Custo** | Por chamada API | Por execucao CLI |

### Regra de Routing

```
"confere o que voce fez" / review ad-hoc     → Codex (rapido, adversarial)
"code review completo" / pre-merge           → CodeRabbit (estruturado, profundo)
"stress test / poke holes"                   → Codex (adversarial)
"qualidade / best practices / code smells"   → CodeRabbit (AST analysis)
Risk-path forcado (auth, migrations)         → Codex (rapido) + CodeRabbit (profundo) em paralelo
PR grande (>200 linhas, 5+ arquivos)         → CodeRabbit automatico
```

---

## DETECCAO DE FALHA (HARD RULE)

Contador deterministico, nao vibe:

- **2x mesmo teste falha no mesmo code path** → MUST invoke Codex rescue. Anunciar.
- **2x mesmo erro no mesmo shell command** → MUST invoke Codex rescue. Anunciar.
- **2x mesmo edit re-tentado sem progresso** → MUST invoke Codex rescue. Anunciar.

Reset do contador: (a) teste/build passa, (b) usuario muda o objetivo, (c) usuario diz "continua tentando".

Ao invocar rescue, enviar contexto completo:

```
Agent tool → subagent_type: "codex:codex-rescue"
prompt: "Rescue mode. Claude tried 2x and failed. [contexto completo: output falhando, o que foi tentado, arquivos relevantes]"
```

---

## PROTOCOLO DE ANUNCIO (para rotas forcadas)

Quando o skill dispara uma rota que o usuario NAO pediu explicitamente (risk-path ou failure-counter):

```
[three-brain] roteando para Codex (adversarial-review) — risk path: packages/db/migrations/
[three-brain] handoff para Codex rescue — Claude falhou mesmo teste 2x seguidas
[three-brain] roteando para Gemini — arquivo de video detectado
[three-brain] roteando para CodeRabbit — PR com 12 arquivos, review estruturado
[three-brain] roteando para Codex + CodeRabbit (paralelo) — risk path: apps/api/routers/auth.py
```

Para rotas que o usuario pediu explicitamente — sem anuncio, apenas executar.

---

## CALLING PATTERNS — Mega Brain

### Codex Review (via Agent tool)

```
Agent tool:
  subagent_type: "codex:codex-rescue"
  prompt: "Review this diff. Flag bugs, risks, missing tests. Be specific.\n\n[diff content]"
```

### Codex Adversarial Review

```
Agent tool:
  subagent_type: "codex:codex-rescue"
  prompt: "Adversarial review. Challenge the design. Find what's wrong. Prove it's broken.\n\n[context]"
```

### Codex Rescue

```
Agent tool:
  subagent_type: "codex:codex-rescue"
  prompt: "Rescue mode. Claude tried 2x and failed. Solve it from scratch.\n\n[full context: failing output, what was tried, relevant files]"
```

### Gemini Multimodal (video/audio/PDF)

```
Agent tool:
  subagent_type: "cc-gemini-plugin:gemini-agent"
  prompt: "Analyze this [video/audio/PDF]. Return timestamped findings. Cap at 800 words.\n\nFile: [path]"
```

### Gemini Whole-Codebase Scan

```
Agent tool:
  subagent_type: "cc-gemini-plugin:gemini-agent"
  prompt: "Find every place X in the codebase. Return file:line list.\n\nDirs to scan: [paths]"
```

### CodeRabbit Structured Review

```
Agent tool:
  subagent_type: "coderabbit:code-reviewer"
  prompt: "Review the uncommitted changes. Focus on security, best practices, code smells, and AST-level issues."
```

OU via skill diretamente:

```
/coderabbit-review uncommitted     # pre-commit
/coderabbit-review committed       # pre-merge (vs main)
/coderabbit-review base {branch}   # vs branch especifico
```

**Nota:** CodeRabbit roda via WSL (~7-30min). Para risk-paths, lancar Codex (rapido) + CodeRabbit (profundo) em PARALELO.

### Consensus Mode (paralelo)

Lancar 4 Agents em paralelo com o MESMO prompt, cada um retornando:

```
Recommendation: <uma linha>
Blocking risks: <bullet list>
Assumptions: <bullet list>
Confidence: low / medium / high
Tests required to verify: <bullet list>
```

Claude diff os resultados: onde concordam, onde discordam, e adjudica por evidencia (nao por media).

---

## REGRA DE AMBIGUIDADE

Na duvida se dispara review no output do Claude: **DISPARAR**. O custo de uma chamada Codex de 20s e pequeno. O custo de um self-review que perde um bug real e enorme.

Bias para disparar em verbos de review direcionados ao output do Claude.
Bias para ficar dormindo em verbos de review direcionados ao conteudo do usuario.

---

## OUTPUT

Three-brain e um router, nao um produtor. Artefatos de analise persistidos em:
- `docs/research/{YYYY-MM-DD}-three-brain-{slug}/` — segue convencao tech-search

## Post-Execution Learning Log (MANDATORY)

**Path:** `.megabrain/learning/logs/three-brain/three-brain-{context-id}-{YYYYMMDD}-{HHmmss}.yaml`

> Todas as skills do MegaBrain Hub gravam logs em `.megabrain/learning/logs/`.

```yaml
schema_version: "1.0"
skill_id: "three-brain"
timestamp: "{ISO-8601}"
trigger: "{self-review|risk-path|failure-counter|user-request|consensus}"
route: "{codex|gemini|coderabbit|consensus}"
target_files: []
executor: "general-purpose"
duration_minutes: {estimate}
decisions:
  - description: "{routing decision}"
    type: "routing"
    alternatives: []
    rationale: "{why this engine}"
errors: []
outcome: "{completed|halted|failed}"
engine_results:
  codex: "{PASS|FAIL|N/A}"
  gemini: "{PASS|FAIL|N/A}"
  coderabbit: "{PASS|FAIL|N/A}"
findings_count: {N}
epilogue:
  what_worked: ""
  what_failed: ""
  confidence: "HIGH|MEDIUM|LOW"
  source_type: "skill_execution"
```

**If Write fails:** Log warning, do NOT halt. **NEVER skip this step.**

---

## RISK-BY-REVERSIBILITY

Mesmo verbos que normalmente NAO disparam (refatorar/planejar/explicar/design) DISPARAM se o alvo e irreversivel:

- "Refatora o auth middleware" → Codex review (auth path)
- "Planeja a migracao do banco" → Codex review (migration path)
- "Desenha o pipeline de deploy" → Codex review (deploy path)

Verbo e irrelevante se o alvo e risky.
