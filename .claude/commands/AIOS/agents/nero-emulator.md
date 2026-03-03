# nero-emulator

Ativa o @nero-emulator para clone testing e fidelity verification.

## Uso

```
/AIOS:agents:nero-emulator
@nero-emulator
```

## Quando Usar

- Testar clone antes de deploy
- Verificar fidelidade do comportamento
- Executar test suites automatizadas
- Comparar clone vs source materials

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*activate {persona}` | Ativa clone para testes |
| `*test {suite}` | Executa test suite |
| `*compare {question}` | Compara resposta vs source |
| `*fidelity-check` | Verifica fidelidade geral |
| `*duo {persona1} {persona2}` | Testa dois clones interagindo |
| `*roundtable {personas}` | Roundtable com múltiplos clones |
| `*report` | Gera relatório de testes |
| `*exit` | Desativa agente |

## Test Suites

| Suite | Descrição | Tests |
|-------|-----------|-------|
| `standard` | Testes básicos | 10 |
| `comprehensive` | Cobertura completa | 25 |
| `quick` | Smoke tests | 5 |
| `voice` | Apenas voice patterns | 8 |
| `knowledge` | Apenas knowledge | 12 |

## Scoring

| Categoria | Peso | Threshold |
|-----------|------|-----------|
| Voice Match | 30% | ≥85% |
| Knowledge Accuracy | 40% | ≥90% |
| Framework Usage | 20% | ≥80% |
| Boundary Respect | 10% | 100% |

## Exemplo

```
@nero-emulator *test --persona cole-gordon --suite comprehensive
```

## Agentes Relacionados

- `@nero-architect` - Upstream (SOUL.md)
- `@nero-debate` - Parallel (adversarial testing)
