# nero-identity

Ativa o @nero-identity para extração de Deep Identity Layers (L6-L8 GOLD).

## Uso

```
/AIOS:agents:nero-identity
@nero-identity
```

## Quando Usar

- Extrair obsessões core (L6)
- Identificar singularidades (L7)
- Mapear paradoxos produtivos (L8 - GOLD Layer)
- Análise de identidade profunda

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*obsessions {persona}` | Extrai Layer 6 - Obsessões |
| `*singularities {persona}` | Extrai Layer 7 - Singularidades |
| `*paradoxes {persona}` | Extrai Layer 8 - Paradoxos (GOLD) |
| `*full-deep {persona}` | Extração completa L6-L8 |
| `*gate-status` | Status do Human Approval Gate |
| `*request-approval` | Solicita aprovação humana para L8 |
| `*exit` | Desativa agente |

## Deep Identity Layers (GOLD)

| Layer | Nome | Descrição | Gate |
|-------|------|-----------|------|
| L6 | Obsessões | Temas recorrentes, fixações | Auto |
| L7 | Singularidades | Contradições que definem | Auto |
| L8 | Paradoxos | Tensões produtivas | **Human Required** |

## Gate: Human Approval (L8)

```
⚠️ Layer 8 NUNCA é automático
→ Requer revisão humana explícita
→ Paradoxos são sensíveis demais para auto-approve
→ Use *request-approval para solicitar
```

## Exemplo

```
@nero-identity *paradoxes --persona jeremy-miner --evidence-required 3
```

## Agentes Relacionados

- `@nero-cognitive` - Upstream (L1-L5 extraídos)
- `@nero-synthesis` - Downstream (para canonicalização)
