---
name: extract-session-heuristics
description: "Extrai heurísticas operacionais de sessões de trabalho usando metodologia Pareto ao Cubo."
version: "3.3.0"
user-invocable: true
argument-hint: "[session context, project context, global scan or handoff path]"
---

# Extract Session Heuristics

Extrai heurísticas operacionais de sessões de trabalho reais. Diferente de extração de experts (pessoas) — esta extrai de **execução** (o que aprendemos fazendo).

## Activation

```
/extract-session-heuristics
/extract-session-heuristics --scope session
/extract-session-heuristics --scope project "your-org"
/extract-session-heuristics --scope global
/extract-session-heuristics "Epic 71 — runner-lib v2 consolidation"
/extract-session-heuristics docs/sessions/2026-03/handoff.md
```

## Process

**ID:** SP-EXTRACT-SESSION-HEURISTICS
**Mode:** VALIDAR
**Agent:** runtime-resolved
**Estimated:** 15 min

## Runtime Owner Resolution

Antes da Phase 1, resolver obrigatoriamente estas variáveis:

- `extraction_scope`
- `heuristic_owner_slug`
- `heuristic_owner_handle`
- `heuristic_owner_display_name`
- `heuristic_id_prefix`

Scopes válidos:

- `session`: extrair apenas a sessão alvo
- `project`: extrair e consolidar todas as sessões do projeto alvo
- `global`: extrair e consolidar todas as sessões elegíveis de forma global

Ordem de resolução:

1. override explícito informado pelo usuário
2. usuário/operador ativo da sessão com namespace em `squads/squad-creator-pro/minds/`
3. ownership inferido do contexto da sessão/projeto
4. perguntar uma vez, apenas se continuar ambíguo

Regras:

- Nunca assumir `@knowledge-architect` como default só porque existe um exemplo legado.
- Sempre escrever no namespace do owner resolvido: `squads/squad-creator-pro/minds/{heuristic_owner_slug}/heuristics/`.
- Reutilizar a família `*_KE_*` do owner quando ela já existir.
- Se o owner ainda não tiver família de extração de sessão, criar `{owner_initials}_KE`.
- Exemplo concreto: sessões do arquiteto de processos devem resolver para `process_architect` e usar `PA_KE` como família default.

## Execution

1. **Read the task file** at `squads/squad-creator-pro/tasks/an-extract-session-heuristics.md`
2. **Read the checklist** at `squads/squad-creator-pro/checklists/session-heuristics-extraction.md`
3. **Read the base template** at `squads/squad-creator-pro/templates/heuristic-base-tmpl.md`
4. **Read the overlay** for the target family:
   - KE (mind_heuristic): `squads/squad-creator-pro/templates/overlays/mind-heuristic-overlay.md`
   - BS/PM/PA (checkpoint): `squads/squad-creator-pro/templates/overlays/checkpoint-overlay.md`
   - Default for session extraction: mind_heuristic (KE)
5. **Read the family registry** at `squads/squad-creator-pro/data/family-registry.yaml`
6. **Read the scope report template** at `squads/squad-creator-pro/templates/scope-extraction-report-tmpl.md`
7. **Read existing decision cards** at `squads/squad-creator-pro/minds/{heuristic_owner_slug}/heuristics/decision-cards.yaml`
8. **If the owner has no `decision-cards.yaml` yet, initialize it before writing**
9. **Resolve source corpus by scope before IDENTIFY**
8. **For `project` and `global`, create a scope extraction report**
9. **Follow the 5-phase pipeline exactly**

Bootstrap mínimo:

```yaml
version: "1.0.0"
owner: "{heuristic_owner_display_name}"
id_prefix: "{heuristic_id_prefix}"
total: 0
last_updated: "{YYYY-MM-DD}"
cards: []
```

Scope source corpus:

- `session`: usar apenas o contexto/handoff/log da sessão recebida
- `project`: agregar todas as sessões elegíveis do projeto, deduplicar por sessão e consolidar evidências
- `global`: agregar todas as sessões elegíveis dos projetos, priorizar repetição cross-project e promover regras sistêmicas

Regras de consolidação por scope:

- `session`: evidências podem permanecer totalmente locais
- `project`: toda heurística nova deve refletir se é local do projeto ou recorrente no projeto
- `global`: toda heurística nova deve explicitar se é global, cross-project ou ainda dependente de contexto específico

### Phase 1: IDENTIFY (5 min)

Varrer a sessão procurando candidatas em 5 categorias:

- **Decisões pivot** — momentos que mudaram o rumo
- **Bugs/incidentes** — erros que revelaram regras
- **Anti-patterns evitados** — o que quase deu errado
- **Patterns validados** — o que funcionou e por quê
- **Research insights** — confirmação/refutação externa

Apply Critical Decision Method questions:
1. "O que deu certo que NÃO ERA ÓBVIO?"
2. "O que quase deu errado? Em que PONTO EXATO?"
3. "Que regra SE/ENTÃO emergiu?"

**Gate:** ≥ 5 candidatas brutas (TKN-ESH-THR-002). Se < 5, sessão rasa — pedir mais contexto.

### Phase 2: FILTER — Pareto ao Cubo (3 min)

Classificar cada candidata:

| Zone | Criteria | Action |
|------|----------|--------|
| 0,8% Genialidade | Muda paradigma | FORMALIZAR primeiro |
| 4% Excelência | Guardrail contra retrabalho | FORMALIZAR |
| 20% Impacto | Boa prática | FORMALIZAR se [SOURCE:] |
| 80% Merda | Genérico, sem evidência | DESCARTAR |

**Gate:** ≤ 30% genéricas (TKN-ESH-THR-003). Se > 30%, varredura rasa.

### Phase 3: OVERLAP — Dedup (3 min)

```bash
# Check existing heuristics
cat squads/squad-creator-pro/minds/{heuristic_owner_slug}/heuristics/decision-cards.yaml
```

- Duplicata COM nova evidência → **UPDATE** card existente
- Sem match → **CREATE** nova
- 3+ sessões confirmam mesma → **PROMOTE** zona
- Em `project` e `global`, consolidar evidências por sessão antes de decidir por promote

### Phase 4: FORMALIZE — 3 Camadas (4 min)

Para cada heurística aprovada, criar **ambas** camadas:

**L2 — Decision Card** (em `decision-cards.yaml`):

```yaml
- id: {heuristic_id}
  name: "{Nome}"
  rule: "SE {condição} → ENTÃO {ação}"
  zone: "{genialidade|excelencia|impacto}"
  trigger: "{quando se aplica}"
  anti_pattern: "{o que acontece quando ignora}"
  evidence: "{dado empírico [SOURCE:]}"
```

**L3 — Full Doc** (arquivo `{heuristic_id}.md`):

Use base template em `squads/squad-creator-pro/templates/heuristic-base-tmpl.md` + overlay da família:
- KE (mind_heuristic): `squads/squad-creator-pro/templates/overlays/mind-heuristic-overlay.md`
- BS/PM/PA (checkpoint): `squads/squad-creator-pro/templates/overlays/checkpoint-overlay.md`

**Scope Report** (obrigatório em `project` e `global`):

Criar `scope-extraction-report.md` a partir de `squads/squad-creator-pro/templates/scope-extraction-report-tmpl.md`.

**Numeração:**

```bash
ls squads/squad-creator-pro/minds/{heuristic_owner_slug}/heuristics/{heuristic_id_prefix}_*.md | sort | tail -1
```

### Phase 4.5: EXIT GATE — Template Compliance (1 min)

Antes de persistir, validar CADA heurística formalizada contra o template canônico.

**Campos obrigatórios (BLOCKER — não persistir sem eles):**

| Campo | Localização | Exemplo |
|-------|------------|---------|
| `[SOURCE:]` | L3 header + L2 evidence | `[SOURCE: sessão 048a, 2026-03-30]` |
| `Zone` | L3 header + L2 zone | `genialidade\|excelencia\|impacto` |
| `rule: SE...ENTÃO...NUNCA` | L2 card + L3 Configuration YAML | Regra imperativa |
| `sys_tension` | L3 Configuration YAML | tension_with + resolution |
| `failure_modes` | L3 Configuration YAML | omission + misapplication |
| `anti_pattern` | L2 card | O que acontece quando ignora |

**Campos recomendados (WARN — persistir mas marcar `status: draft`):**

| Campo | Localização |
|-------|------------|
| `Confidence Requirements` | L3 seção própria (obrigatório para zone=genialidade, opcional para impacto) |
| `Cross-Mind Divergence` | L3 seção própria |
| `Behavioral Evidence` | L3 seção própria |

**Gate decision:**
- 6/6 campos obrigatórios presentes → `status: validated` — prosseguir para Phase 5
- 5/6 campos obrigatórios (faltando não-SOURCE) → `status: draft` — persistir com flag, enriquecer depois
- Faltando `[SOURCE:]` → **BLOCK** (VETO-ESH-001) — não persistir

### Phase 5: PERSIST (2 min)

1. Update `decision-cards.yaml` com novos cards
2. Create `{heuristic_id}.md` files
3. Em `project` e `global`, create `scope-extraction-report.md`
4. Update `MEMORY.md` se cross-session relevante
5. Commit: `feat(minds): add {heuristic_id_prefix}_NNN-NNN {extraction_scope} heuristics to {heuristic_owner_handle}`

## Veto Conditions

| ID | Condition | Action |
|----|-----------|--------|
| VETO-ESH-001 | Heurística sem [SOURCE:] | BLOCK |
| VETO-ESH-002 | Inferida sem evidência empírica | BLOCK |
| VETO-ESH-003 | Duplicata sem nova evidência | BLOCK — update existing |
| VETO-ESH-004 | < 5 candidatas brutas | BLOCK — sessão rasa |
| VETO-ESH-005 | > 30% genéricas | WARN — aprofundar |
| VETO-ESH-006 | Fonte não fornecida pelo usuário ou auto-inferida de git/branch/working dir | BLOCK — voltar ao prompt da Phase 0 |

## Quality Gate

Run checklist at `squads/squad-creator-pro/checklists/session-heuristics-extraction.md`.
Minimum: 15/18 checks pass. Phase 4 items 1-2 ([SOURCE:]) are BLOCKER.

## Output Location

```
squads/squad-creator-pro/minds/{heuristic_owner_slug}/heuristics/
|- decision-cards.yaml          <- L2 cards (all heuristics, 1 file)
|- {heuristic_id_prefix}_001.md ... {heuristic_id_prefix}_NNN.md  <- L3 full docs
|- scope-extraction-report.md   <- required for `project` and `global`
```

## Tokens

| Token | Value | Purpose |
|-------|-------|---------|
| TKN-ESH-THR-001 | 100% | Source traceability |
| TKN-ESH-THR-002 | ≥ 5 | Min candidatas brutas |
| TKN-ESH-THR-003 | ≤ 30% | Max genérico ratio |
| TKN-ESH-THR-004 | 5/6 | Quality check minimum |
| TKN-ESH-BEH-001 | update_existing | Overlap action |
| TKN-ESH-BEH-002 | 3_sessions | Triangulation promotion |

## Promotion Protocol (RT-HEURISTICS-001 Ação 6)

Heurísticas consolidadas podem ser promovidas para `.claude/rules/` ou MEGABRAIN tokens.

### Critérios de Promoção

Uma heurística é `promotion_candidate` quando:
1. `confirmed_sessions >= 3` (TKN-ESH-BEH-002)
2. `evidence_threshold: [EMPIRICAL]` (não SYNTHESIZED)
3. Pelo menos 1 squad downstream a consome (via `heuristic_subscriptions`)

### Fluxo

```
Heurística criada (Phase 5)
  → confirmed_sessions++ a cada sessão que confirma
  → Ao atingir 3 sessions:
      1. Skill marca no L2 card: promotion_candidate: true
      2. Notifica no output: "PV_KE_NNN é candidata a promoção"
      3. Human gate: o arquiteto de processos (ou @squad-chief) aprova
      4. SE aprovado:
         a. Criar/atualizar .claude/rules/{domain}.md com source_heuristic: {ID}
         b. Atualizar L2 card: promoted_to_rule: ".claude/rules/{file}.md"
         c. SE zone=genialidade: candidata a MEGABRAIN token (token-registry.yaml)
```

### Mapeamento Heurística → MEGABRAIN

| Campo heurística | Target MEGABRAIN | Mapeamento |
|-----------------|---------------|-----------|
| `sys_tension.tension_with` | token-registry → Behavior family | Token conflitante |
| `failure_modes.omission` | composition-rules → anti_patterns[] | type: omission |
| `failure_modes.misapplication` | composition-rules → anti_patterns[] | type: misapplication |
| `rule (SE/ENTÃO/NUNCA)` | composition-rules → behavioral_rules[] | condition/action/violation |
| `evidence_threshold` | Token confidence | SYNTHESIZED→advisory, EMPIRICAL→operational |

### Campos L2 para Promoção

Adicionar nos cards que atingem threshold:
```yaml
confirmed_sessions: 3          # Contagem de sessões que confirmaram
promotion_candidate: true      # Flag automático ao atingir threshold
promoted_to_rule: null         # Path da rule após promoção
promoted_to_token: null        # Token ID após promoção MEGABRAIN
```

### Gate Humano (NON-NEGOTIABLE)

Promoção automática sem revisão viola "No Invention" (Constitution Art. IV).
Tokens operacionais afetam todos os squads — human gate obrigatório.

## Hub↔Spoke Sync Protocol (RT-HEURISTICS-001 Ação 11)

### Versionamento

| Tipo de mudança | Bump | Hub sync |
|----------------|------|----------|
| Patch (typo, fix menor) | x.x.+1 | Opcional — sync no próximo minor |
| Minor (nova feature, novo campo) | x.+1.0 | **Obrigatório** — PR para Hub |
| Major (breaking change) | +1.0.0 | **Obrigatório** — Roundtable + PR para Hub |

### Regras

1. Skill no Hub (`the-hub/.claude/skills/`) é SOT para estrutura base
2. Spoke (your-org) pode adicionar scopes (project/global) como extensão
3. Minor+ bump no Spoke DEVE gerar PR para Hub dentro de 7 dias
4. Checklist version DEVE acompanhar skill version (ambos v3.x.x)
5. `context: conversation` é invariante — NUNCA mudar para `fork`
