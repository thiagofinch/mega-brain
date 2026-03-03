# nero-cognitive

Ativa o @nero-cognitive para extração de Observable Layers (L1-L5).

## Uso

```
/AIOS:agents:nero-cognitive
@nero-cognitive
```

## Quando Usar

- Extrair filosofias e crenças (L1)
- Identificar modelos mentais (L2)
- Mapear frameworks e metodologias (L3)
- Catalogar heurísticas (L4)
- Documentar padrões de voz (L5)

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*extract {persona}` | Extrai todos os 5 layers |
| `*extract-layer {n}` | Extrai layer específico (1-5) |
| `*consolidate` | Consolida padrões extraídos |
| `*coverage` | Verifica cobertura por layer |
| `*validate` | Valida consistência |
| `*handoff` | Entrega para nero-identity |
| `*exit` | Desativa agente |

## Observable Layers

| Layer | Nome | Mínimo | Target |
|-------|------|--------|--------|
| L1 | Filosofias | 5 | 15+ |
| L2 | Modelos Mentais | 3 | 10+ |
| L3 | Frameworks | 3 | 8+ |
| L4 | Heurísticas | 5 | 15+ |
| L5 | Padrões de Voz | 3 | 8+ |

## Formato de Extração

```yaml
pattern_id: FIL-{persona}-{NNN}
evidence:
  - chunk_id: chunk_AH047_12
    quote: "Exact quote from source"
    confidence: 0.92
frequency: 12  # Vezes mencionado
conviction: high  # low/medium/high
```

## Exemplo

```
@nero-cognitive *extract --persona alex-hormozi --layers 1,2,3
```

## Agentes Relacionados

- `@nero-intake` - Upstream (chunks tagueados)
- `@nero-identity` - Downstream (para L6-L8)
