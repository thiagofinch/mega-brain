# Epic: Resolucao de Debitos Tecnicos + Consolidacao de Repositorios
## Mega Brain AI v1.4.0 -> v1.5.0

> **Epic ID:** EPIC-TD-001
> **Version:** 1.0.0
> **Date:** 2026-03-14
> **Author:** Beth Smith (PM)
> **Source Documents:**
> - `docs/prd/technical-debt-assessment.md` (39-item inventory, Phase 8 FINAL)
> - `docs/reports/TECHNICAL-DEBT-REPORT.md` (business impact analysis)
> - `docs/plans/surgical-merge-plan-2026-03-14.md` (repo consolidation)

---

## Objetivo

O Mega Brain funciona. Mas funciona sobre uma base que acumula riscos a cada semana: um CI decorativo que nunca rejeitou nada, uma chave de API exposta em texto aberto, 21 modulos duplicados que confundem qualquer pessoa que toque no codigo, e 92 referencias a um diretorio que nao existe mais.

Este epic existe para transformar a base de codigo de "funciona por acidente" em "funciona por design". Cada story ataca um cluster de debitos tecnicos relacionados, seguindo a ordem de dependencia definida na avaliacao tecnica.

A consolidacao de repositorios e incluida porque a existencia de dois repos com o mesmo nome e a mesma origem e um debito organizacional que amplifica confusao.

---

## Escopo

### Incluido

| Sprint | Categoria | Stories | Debitos Cobertos |
|--------|-----------|---------|------------------|
| Sprint 1 | Seguranca + CI | 1.1, 1.2 | TD-032, TD-033, TD-014, TD-019 |
| Sprint 1 | Limpeza de Codigo | 1.3, 1.4 | TD-001, TD-003, TD-004, TD-002, TD-008 |
| Sprint 1 | Consolidacao | 1.5 | Repo merge (3 inbox sources + archive) |
| Sprint 2 | Testes + Hooks | 2.1, 2.2 | TD-017, TD-038, TD-010 Phase 1, TD-034, TD-015 |

### Excluido (futuras epics)

- TD-010 Phases 2-4 (testes para RAG, hooks, entities -- 60h, melhor como epic separada)
- TD-011 (migracao BASE_DIR -- 6h, P2)
- TD-018 (validacao de schema JSON -- 8h, P2)
- TD-020 (consolidacao de hooks -- 8h, P2)
- TD-025, TD-026 (documentacao de referencia -- 18h, P2)
- TD-027 (pruning de regras -- 16h, P3)
- Todos os demais P2/P3 ficam no backlog

---

## Success Criteria

### Metricas Quantitativas

| Criterio | Valor Atual | Meta | Comando de Verificacao |
|----------|-------------|------|------------------------|
| Modulos duplicados em core/intelligence/ | 21 | 0 | `ls core/intelligence/*.py \| grep -v __init__ \| wc -l` retorna 2 |
| Referencias a agents/minds/ | 92 em 27 arquivos | 0 | `grep -r "agents/minds/" . --include="*.{py,md,yaml,json}"` retorna 0 |
| Versao package.json vs pyproject.toml | 1.4.0 vs 1.3.0 | Identicas | Script de validacao retorna OK |
| Segredos em auto-memory | 2 (API key + webhook URL) | 0 | `grep -i "api.key\|bearer" ~/.claude/.../MEMORY.md` retorna 0 |
| pickle.load() no codebase | 1 ocorrencia | 0 | `grep -r "pickle.load" core/` retorna 0 |
| CI rejeita PR com teste falhando | Nunca (hardcoded PASSED) | Sempre | Push PR com teste quebrado, CI marca falha |
| Testes rastreados pelo git | 0 (gitignore contradiz) | 50+ | `git ls-files tests/python/ \| wc -l` > 0 |
| Hooks com exit codes padronizados | Inconsistente | 37/37 | Audit report mostra 100% compliance |

### Criterio Qualitativo

- Um desenvolvedor novo consegue clonar o repo, rodar `pytest`, e ter TODOS os testes passando sem intervencao manual
- O CI bloqueia PRs que introduzem erros de lint ou testes falhando
- Nenhuma credencial existe em texto aberto fora do `.env`

---

## Timeline

```
+----------+------------------------------+--------+----------+
| SPRINT   | FOCO                         | EFFORT | DEADLINE |
+----------+------------------------------+--------+----------+
| Sprint 1 | Security + CI + Cleanup      | ~18h   | Semana 1 |
| (1 week) | + Repo Consolidation         |        |          |
|          | Stories: 1.1 - 1.5           |        |          |
+----------+------------------------------+--------+----------+
| Sprint 2 | Tests + Hook Standardization | ~14h   | Semanas  |
| (2 weeks)| Stories: 2.1 - 2.2           |        | 2-3      |
+----------+------------------------------+--------+----------+
| TOTAL    |                              | ~32h   | 3 weeks  |
+----------+------------------------------+--------+----------+
```

Nota: O esforco total deste epic (~32h) e um subconjunto dos ~163.5h do debt completo. Este epic cobre os P0 (14.5h) + partes selecionadas de P1 (~17.5h). Os P2/P3 restantes serao epics futuras.

---

## Budget

| Item | Horas | Custo (R$150/h) |
|------|-------|-----------------|
| Sprint 1 (Stories 1.1-1.5) | ~18h | R$2.700 |
| Sprint 2 (Stories 2.1-2.2) | ~14h | R$2.100 |
| **Total Epic** | **~32h** | **R$4.800** |
| Buffer (15%) | ~5h | R$750 |
| **Total com Buffer** | **~37h** | **R$5.550** |

Comparado com o custo de NAO resolver (R$55.000-R$215.000 em 12 meses segundo o relatorio de negocios), o investimento de R$5.550 se paga se evitar um unico incidente.

---

## Stories

### Sprint 1: Security + CI + Cleanup (Semana 1)

| ID | Titulo | Debitos | Esforco | Arquivo |
|----|--------|---------|---------|---------|
| 1.1 | Security: Remove Exposed API Keys | TD-032, TD-033 | ~3h | `story-1.1-security-credentials.md` |
| 1.2 | CI: Rewrite Quality Pipeline | TD-014, TD-019 | ~4h | `story-1.2-ci-pipeline-rewrite.md` |
| 1.3 | Codebase: Eliminate Duplicate Modules | TD-001, TD-003 | ~4h | `story-1.3-duplicate-modules.md` |
| 1.4 | Paths: Fix Stale References | TD-004, TD-002, TD-008 | ~4h | `story-1.4-stale-path-references.md` |
| 1.5 | Repo Consolidation | Merge plan | ~1h | `story-1.5-repo-consolidation.md` |

### Sprint 2: Testing + Hook Standardization (Semanas 2-3)

| ID | Titulo | Debitos | Esforco | Arquivo |
|----|--------|---------|---------|---------|
| 2.1 | Testing: Restore Test Coverage | TD-017, TD-038, TD-010 Phase 1 | ~8h | `story-2.1-test-coverage.md` |
| 2.2 | Hooks: Standardize Error Handling | TD-034, TD-015 | ~6h | `story-2.2-hook-standardization.md` |

---

## Dependencies

### Dependency Chain (P0 Resolution Order)

A ordem de execucao dentro do Sprint 1 segue a cadeia de dependencias definida na avaliacao tecnica:

```
Story 1.1 (Security) -----> Nenhuma dependencia. Executar primeiro.
       |
       v
Story 1.3 (Duplicates) ---> TD-003 (versoes) nao tem dependencia.
       |                     TD-001 (duplicatas) depende de TD-004 (story 1.4)
       |                     para contagem correta de ruff errors.
       v
Story 1.4 (Paths) --------> TD-004 (agents/minds refs) DEVE vir ANTES de:
       |                     TD-002 (AGENT-INDEX regeneration)
       |                     TD-008 (delete agents/minds/)
       v
Story 1.2 (CI) -----------> TD-019 depende de TD-014 (fix test path)
       |                     TD-019 depende de TD-001 (clean codebase)
       v
Story 1.5 (Repo) ---------> Independente. Pode rodar em paralelo.
```

**Ordem recomendada de execucao:**

```
PARALELO: Story 1.1 (security) + Story 1.5 (repo merge)
      |
      v
SEQUENCIAL: Story 1.4 (paths) -> Story 1.3 (duplicates) -> Story 1.2 (CI)
      |
      v
Sprint 2: Story 2.1 (tests) + Story 2.2 (hooks) em paralelo
```

### Cross-Sprint Dependencies

| Story | Depende De | Razao |
|-------|------------|-------|
| 2.1 (tests) | 1.2 (CI) | CI precisa funcionar para validar novos testes |
| 2.1 (tests) | 1.3 (duplicates) | Remover duplicatas antes de contar cobertura |
| 2.2 (hooks) | Nenhuma | Independente |

---

## Risks

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|---------------|---------|-----------|
| 1 | Deletar modulo duplicado quebra import em runtime | ALTA | ALTO | Atualizar imports ANTES de deletar. Smoke test apos cada batch. Story 1.3 tem pre-deletion checklist. |
| 2 | CI continua passando com codigo quebrado apos "fix" | CERTA (se parcial) | ALTO | Reescrever CI completamente (story 1.2), nao tentar consertar. Testar com PR que tem teste falhando. |
| 3 | Rename agents/minds/ causa falha em path resolution dinamica | MEDIA | ALTO | Rodar pytest completo + teste manual do pipeline apos story 1.4. Alguns scripts constroem paths dinamicamente. |
| 4 | Fix do .gitignore causa diff enorme | ALTA | MEDIO | Esperado e documentado. PR description explica que arquivos de teste aparecem como "novos". |
| 5 | Chave de API ja foi vazada via backup/sync | MEDIA | ALTO | Rotacionar chave do Fireflies imediatamente (story 1.1, task 3). |
| 6 | Consolidacao de hooks introduz novos bugs | MEDIA | MEDIO | Story 2.2 padroniza error handling SEM consolidar hooks. Consolidacao e epic futura (TD-020). |

---

## Definition of Done

Este epic esta DONE quando:

**Sprint 1 Complete:**
- [ ] Zero segredos em texto aberto fora do `.env`
- [ ] Chave do Fireflies rotacionada
- [ ] pickle.load() substituido por JSON/numpy
- [ ] CI rejeita PRs com testes falhando (verificado com PR de teste)
- [ ] Zero modulos duplicados em `core/intelligence/` root
- [ ] Zero referencias a `agents/minds/` em todo o codebase
- [ ] Diretorio `agents/minds/` deletado
- [ ] Versoes sincronizadas (package.json = pyproject.toml)
- [ ] Repo consolidado (3 inbox sources copiados, outro repo arquivado)
- [ ] RAG pipeline funcional apos cleanup: `python3 -c "from core.intelligence.rag.pipeline import RAGPipeline"` sucede

**Sprint 2 Complete:**
- [ ] Testes rastreados pelo git (`git ls-files tests/python/ | wc -l` > 0)
- [ ] Regressao de 248->50 testes investigada e documentada
- [ ] Testes para `core/intelligence/pipeline/` com >= 40% coverage
- [ ] 37/37 hooks seguem convencao de exit codes (0/1/2)
- [ ] `memory_capture.py` com timeout corrigido ou removido
- [ ] Nenhum hook silencia erros com `sys.exit(0)` em catch-all

**Epic DONE = Sprint 1 Complete + Sprint 2 Complete**

---

## Historico

| Versao | Data | Mudanca |
|--------|------|---------|
| 1.0.0 | 2026-03-14 | Criacao inicial. 7 stories cobrindo P0 + P1 selecionados. |

---

**Beth Smith -- I'm a horse surgeon. Not a heart surgeon. But I'm the best at what I do.**
