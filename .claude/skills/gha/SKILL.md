---
name: gha
description: Diagnóstico de GitHub Actions failures
triggers:
  - "/gha"
  - "github actions"
  - "ci failed"
  - "workflow failed"
  - "build failed"
---

# GitHub Actions Diagnostics

Diagnóstico automático de falhas em GitHub Actions.

## Uso

```
/gha                    # Verifica último workflow run
/gha [run_id]           # Analisa run específico
/gha --flaky           # Identifica testes flaky
/gha --history         # Histórico de falhas
```

## O Que Faz

1. **Busca último workflow run com falha**
2. **Baixa logs do job**
3. **Analisa erro e identifica causa raiz**
4. **Sugere correção**

## Execução Manual

Se precisar debugar manualmente:

```bash
# Listar workflows
gh run list --limit 10

# Ver detalhes de um run
gh run view [RUN_ID]

# Baixar logs
gh run view [RUN_ID] --log

# Ver jobs de um run
gh run view [RUN_ID] --job [JOB_ID]
```

## Análise Automática

Quando acionado, JARVIS irá:

1. Executar `gh run list --status failure --limit 5`
2. Identificar o run mais recente
3. Executar `gh run view [ID] --log`
4. Analisar os logs buscando:
   - Erros de teste
   - Erros de build
   - Erros de lint
   - Timeout
   - Dependências faltando
5. Reportar causa provável e sugerir fix

## Padrões Comuns de Erro

| Padrão | Causa Provável | Sugestão |
|--------|----------------|----------|
| `npm ERR!` | Dependência | `npm ci` ou limpar cache |
| `ENOENT` | Arquivo faltando | Verificar paths |
| `timeout` | Teste lento/flaky | Aumentar timeout ou otimizar |
| `FAILED` em test | Teste quebrado | Ver stack trace |
| `TypeScript error` | Tipo incorreto | Fix no código |
| `ESLint` | Lint error | Auto-fix ou manual |

## Exemplo de Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  GITHUB ACTIONS DIAGNOSTIC                                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Run ID:      12345678                                                       ║
║  Workflow:    CI                                                             ║
║  Status:      FAILED                                                         ║
║  Duration:    3m 42s                                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  CAUSA RAIZ:                                                                 ║
║  Test failure in src/__tests__/api.test.ts:42                                ║
║                                                                              ║
║  Error: Expected 200, got 404                                                ║
║                                                                              ║
║  SUGESTÃO:                                                                   ║
║  O endpoint /api/users foi removido ou renomeado.                            ║
║  Verificar se o route existe em src/routes/users.ts                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
