# nero-debate

Ativa o @nero-debate para QA adversarial e stress testing.

## Uso

```
/AIOS:agents:nero-debate
@nero-debate
```

## Quando Usar

- Testar limites do clone adversarialmente
- Identificar contradições e inconsistências
- Verificar resistência a edge cases
- Quality assurance antes de produção

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*challenge {persona}` | Inicia debate adversarial |
| `*gauntlet {persona}` | Executa gauntlet de testes |
| `*trap-test` | Tenta fazer clone contradizer-se |
| `*edge-cases` | Testa cenários extremos |
| `*full-qa` | QA completo adversarial |
| `*report` | Gera relatório de QA |
| `*exit` | Desativa agente |

## Test Categories

| Categoria | Descrição | Severity |
|-----------|-----------|----------|
| Paradox Navigation | Lidar com contradições próprias | High |
| Anti-Pattern Traps | Tentar forçar comportamentos errados | Critical |
| Knowledge Boundaries | Verificar limites de conhecimento | Medium |
| Voice Consistency | Manter voz sob pressão | High |
| Framework Limits | Reconhecer quando framework não aplica | Medium |

## Severity Levels

```
CRITICAL → Bloqueia produção, requer fix imediato
HIGH     → Recomenda fix antes de deploy
MEDIUM   → Nota para melhoria futura
LOW      → Nice to have
```

## Exemplo

```
@nero-debate *gauntlet --persona alex-hormozi --intensity aggressive
```

## Agentes Relacionados

- `@nero-emulator` - Parallel (functional testing)
- `@nero-architect` - Feedback loop (SOUL.md improvements)
