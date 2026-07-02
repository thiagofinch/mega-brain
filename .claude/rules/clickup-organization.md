---
paths:
  - "services/clickup/**"
  - "squads/clickup-*/**"
  - "squads/team-ops-squad/**"
---

# ClickUp Organization Rules — MegaBrain Hub

Applies when creating, modifying, or proposing ClickUp Spaces, Folders, Lists, or Custom Fields.

> **Nota:** Este arquivo contém apenas heurísticas universais (framework-level). Spokes adicionam heurísticas específicas no seu `.claude/rules/clickup-organization.md`.

## Authority

**ONLY `@clickup-chief`** (via materializer) can create new Spaces, Folders, or Lists in ClickUp.
Other agents propose; `@clickup-chief` materializes after Pre-Materialization Check.

## Heurísticas Universais de Organização

### BLOCKING (violação impede materialização)

#### H3: List = Entidade com Lifecycle

Cada lista contém 1 tipo de entidade com state machine (status workflow) própria. Se a entidade não tem lifecycle rastreável, provavelmente não precisa de lista.

```
CORRETO:   List "Alunos" (lifecycle: enrolled → active → completed | churned)
CORRETO:   List "Links" (lifecycle simples mas volume justifica)
EVITAR:    List "Anotações" (sem lifecycle, sem volume)
```

#### H7: Registry ANTES de criar lista

Toda nova lista ClickUp DEVE ter entry no `document-registry.yaml` ANTES de ser criada no ClickUp. Sem entry = Mandamento 10 violado = materialização bloqueada.

```
SEQUÊNCIA OBRIGATÓRIA:
1. Adicionar entry CLICKUP-* no document-registry.yaml
2. Commit ou aprovar
3. @clickup-chief materializa no ClickUp
```

#### H11: Space de Clientes/Alunos = visibilidade ONLY

Spaces com guests (alunos, clientes, parceiros) são para VISUALIZAÇÃO, não para processo. Tasks são adicionadas ali por agentes/workers operando nos Spaces operacionais.

```
CORRETO:   Área de Membros (guests veem conteúdo, não criam tasks)
ERRADO:    Área de Membros com automações que criam subtasks
```

### ADVISORY (warning, Human pode override com justificativa)

#### H10: Trigger Hierarchy

Automações devem seguir esta prioridade:
1. **Status change** (trigger primário) — state machine da entidade
2. **Custom Field change** (secundário) — micro-workflows entre transições
3. **Checkbox/Manual** (último recurso) — temporário/teste only

## Pre-Materialization Checklist

Antes de @clickup-chief materializar qualquer nova estrutura:

- [ ] Space novo tem justificativa de permissão? Se não, usar Folder em Space existente
- [ ] Folder NÃO é nomeado por instância (turma, projeto, cliente específico)?
- [ ] Lista tem entidade com lifecycle definido? (H3)
- [ ] Entry CLICKUP-* existe no document-registry.yaml? (H7)
- [ ] Space de guests é read-only (sem automações de criação)? (H11)
- [ ] Status workflow definido e aprovado?
- [ ] Custom Fields listados e dentro do limite do plano?
- [ ] SuperAgent decisão: precisa de SA? Se sim, registrado no superagent-registry.yaml?
- [ ] Rollback plan documentado?

## IDS Aplicado a ClickUp

Antes de criar qualquer nova estrutura, aplicar IDS (REUSE > ADAPT > CREATE):

| Gate | Aplicação ClickUp |
|------|-------------------|
| G1 (Existe?) | Já existe lista que serve este tipo de entidade? |
| G2 (Funciona?) | A lista existente cobre 100% do requisito? |
| G3 (Adaptável?) | Adicionar CF ou view resolve? |
| G4 (Custo?) | ADAPT (add CF, ~1h) < CREATE (nova lista, ~4h)? |
| G5 (Compatível?) | Custom Fields dentro do limite? Status workflow coerente? |
| G6 (Manutenível?) | Tem owner squad? Tem SuperAgent se necessário? Registrado? |

---

*ClickUp Organization Rules v1.0 — MegaBrain Hub (Universal Heuristics)*
*Framework-level only — spokes extend with business-specific heuristics*
