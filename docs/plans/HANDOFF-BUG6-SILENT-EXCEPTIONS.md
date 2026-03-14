# HANDOFF: Bug 6 — 101 Silent Exception Patterns in Hooks

> **Data:** 2026-03-14
> **Status:** PENDENTE — ultimo bug aberto
> **Prioridade:** ALTA
> **Sessao anterior:** 9 commits, 502 testes, bugs 1-5 corrigidos

---

## O Problema

101 ocorrencias de `except Exception` em 37 hooks Python (.claude/hooks/).
A maioria engole erros silenciosamente com `sys.exit(0)` ou `{"continue": True}`.
O usuario NUNCA ve que algo falhou.

Story 2.2 corrigiu 14 hooks (bare `except:` e JSON output), mas 101 patterns restam.

## O Que Fazer

Para CADA hook em .claude/hooks/*.py:

1. Ler o arquivo
2. Encontrar TODOS os `except Exception` blocks
3. Classificar cada um:
   - **FAIL-OPEN intencional** (enhancement opcional que nao deve bloquear) → mudar exit(0) para exit(1) + JSON warning
   - **Erro real engolido** (validacao ou check que deveria reportar) → mudar para exit(2) + JSON error
   - **Ja correto** (tem JSON output e exit code adequado) → skip
4. Adicionar `import json` se nao existir
5. Garantir output JSON estruturado: `{"warning": "msg"}` ou `{"error": "msg"}`

## Padrao Anthropic (REGRA)

```
exit(0) = Sucesso
exit(1) = Warning (continua mas notifica)
exit(2) = Erro/Bloqueio (para execucao)
```

## Piores Ofensores (priorizar)

| Hook | Count | Impacto |
|------|-------|---------|
| post_batch_cascading.py | 13 | Cascateamento falha silenciosamente |
| continuous_save.py | 8 | Sessao perde dados sem aviso |
| skill_router.py | 8 | Skills nao ativam sem aviso |
| session_autosave_v2.py | 5 | Auto-save falha silenciosamente |
| pipeline_orchestrator.py | 5 | Pipeline para sem explicacao |

## Criterio de Conclusao

- `grep -r "except Exception" .claude/hooks/ --include="*.py" | wc -l` retorna 0
  (OU cada ocorrencia tem JSON output + exit code adequado)
- Nenhum hook usa bare `except:` sem tipo
- Nenhum hook engole erro com exit(0)
- Todos os hooks modificados testados com `echo '{}' | python3 .claude/hooks/HOOK.py`

## Audit Existente

Ja existe: `docs/reports/hook-compliance-audit.md` (criado na Story 2.2)
Usar como referencia para quais hooks ja foram corrigidos.

## Comando para Proxima Sessao

```
Leia docs/plans/HANDOFF-BUG6-SILENT-EXCEPTIONS.md e corrija todos os
except Exception silenciosos nos hooks. Use o audit em
docs/reports/hook-compliance-audit.md como base. Objetivo: ZERO
patterns que engolem erros. Cada except deve ter JSON output + exit
code correto (0/1/2).
```
