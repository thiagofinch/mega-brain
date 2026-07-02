# Orquestrador Global Docs

Este diretório registra a superfície documental operacional do squad `orquestrador-global`.

## Validação MEGABRAIN

- Última validação profunda: `20260514-validate-deep`
- Escopo: inventário de agentes, tasks, workflows, scripts, contratos, dados e superfícies de invocação.
- Resultado esperado: squad estruturalmente consistente para orquestração plan-only, sem execução externa durante a validação.

## Limites Operacionais

- O `plan-architect` planeja e audita, mas não executa automações externas.
- Qualquer execução real deve ser delegada ao executor autorizado e registrada no handoff correspondente.
- Webhooks, n8n e escrita em workspaces produtivos permanecem fora do escopo da validação estrutural.
