# nero-researcher

Ativa o @nero-researcher para APEX Viability Assessment.

## Uso

```
/AIOS:agents:nero-researcher
@nero-researcher
```

## Quando Usar

- Avaliar viabilidade de nova persona para extração
- Calcular APEX Score (Accessibility, Patterning, Expression, Xfactor)
- Identificar gaps de conteúdo antes de investir em extração
- Recomendar GO/NO-GO para pipeline

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*discover {persona}` | Descobre sources disponíveis |
| `*assess {persona}` | Avaliação completa de viabilidade |
| `*apex {persona}` | Calcula APEX Score |
| `*gaps` | Identifica gaps de conteúdo |
| `*recommend` | Gera recomendação GO/NO-GO |
| `*exit` | Desativa agente |

## APEX Scoring

| Dimensão | Peso | Descrição |
|----------|------|-----------|
| Accessibility | 25% | Conteúdo disponível e acessível |
| Patterning | 30% | Padrões claros e repetidos |
| Expression | 25% | Estilo de comunicação distintivo |
| Xfactor | 20% | Singularidades e paradoxos |

## Gate: APEX ≥ 7.5

```
APEX < 7.0  → NO-GO (insufficient content)
APEX 7.0-7.4 → CONDITIONAL (gaps a resolver)
APEX ≥ 7.5  → AUTO-GO (pipeline liberado)
```

## Exemplo

```
@nero-researcher *apex --persona sam-ovens --detailed
```

## Agentes Relacionados

- `@nero-collector` - Upstream (sources)
- `@nero-intake` - Downstream (se APEX ≥ 7.5)
