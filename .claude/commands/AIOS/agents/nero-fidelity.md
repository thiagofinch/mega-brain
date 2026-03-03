# nero-fidelity

Ativa o @nero-fidelity para validação de Fidelity e Production Gates.

## Uso

```
/AIOS:agents:nero-fidelity
@nero-fidelity
```

## Quando Usar

- Validar qualidade do DNA package (Fidelity Gate)
- Aprovar SOUL.md para produção (Production Gate)
- Scoring multi-dimensional de fidelidade
- Análise de gaps antes de finalização

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*fidelity {persona}` | Executa Fidelity Gate |
| `*validate-soul {persona}` | Valida SOUL.md |
| `*production-gate` | Executa Production Gate |
| `*score-breakdown` | Mostra breakdown de scores |
| `*gaps` | Lista gaps identificados |
| `*recommendations` | Gera recomendações |
| `*exit` | Desativa agente |

## Fidelity Scoring

| Métrica | Peso | Threshold |
|---------|------|-----------|
| Layer Coverage | 25% | 100% L1-L5, 80% L6-L8 |
| Pattern Depth | 25% | 3+ evidências por pattern |
| Voice Authenticity | 25% | Match com samples |
| Cross-Ref Density | 25% | Conexões inter-layer |

## Gates

| Gate | Stage | Threshold | Decisão |
|------|-------|-----------|---------|
| Fidelity | 6 | ≥85% | GO/REWORK |
| Production | 8 | Pass all checks | APPROVE/REJECT |

## Gate Decision Flow

```
Score < 70%  → REWORK (volta para synthesis)
Score 70-84% → CONDITIONAL (gaps específicos)
Score ≥ 85%  → PASS (avança para architect)
```

## Exemplo

```
@nero-fidelity *fidelity --persona alex-hormozi --detailed
```

## Agentes Relacionados

- `@nero-synthesis` - Upstream (DNA package)
- `@nero-architect` - Downstream (se fidelity ≥85%)
