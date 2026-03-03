# nero-lead

Ativa o @nero-lead para orquestração completa do NERO Pipeline.

## Uso

```
/AIOS:agents:nero-lead
@nero-lead
```

## Quando Usar

- Iniciar pipeline de extração de persona
- Monitorar status de extrações ativas
- Gerenciar gates e handoffs entre agentes
- Finalizar e aprovar SOUL.md para produção

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*start {persona}` | Inicia pipeline completo para persona |
| `*status` | Mostra todas as extrações ativas |
| `*gates` | Lista gates pendentes de aprovação |
| `*dispatch {agent}` | Despacha agente específico |
| `*report` | Gera relatório de pipeline |
| `*finalize` | Executa Production Gate e finaliza |
| `*exit` | Desativa agente |

## Pipeline Stages

| Stage | Agente | Gate |
|-------|--------|------|
| PRE-0 | nero-collector | - |
| 0.5 | nero-researcher | APEX ≥7.5 |
| 1-2 | nero-intake | - |
| 3-3.1 | nero-cognitive | - |
| 3.2 | nero-identity | Human Approval (L8) |
| 4-5 | nero-synthesis | - |
| 6 | nero-fidelity | Fidelity ≥85% |
| 7 | nero-architect + nero-enricher | - |
| 8 | nero-lead | Production Gate |
| Post-8 | nero-emulator + nero-debate | - |

## Exemplo

```
@nero-lead *start --persona cole-gordon --mode full
```

## Agentes Relacionados

- `@nero-researcher` - APEX Viability Gate (Stage 0.5)
- `@nero-fidelity` - Fidelity/Production Gates (Stage 6, 8)
- `@nero-architect` - SOUL.md Generation (Stage 7)
