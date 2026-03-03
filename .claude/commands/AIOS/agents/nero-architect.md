# nero-architect

Ativa o @nero-architect para geração de SOUL.md production-ready.

## Uso

```
/AIOS:agents:nero-architect
@nero-architect
```

## Quando Usar

- Gerar SOUL.md a partir do unified_dna.yaml
- Estruturar system prompt de produção
- Validar estrutura e completude
- Preparar para clone testing

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*generate {persona}` | Gera SOUL.md completo |
| `*validate {persona}` | Valida estrutura SOUL.md |
| `*preview` | Preview do SOUL.md |
| `*section {name}` | Gera seção específica |
| `*export` | Exporta para produção |
| `*exit` | Desativa agente |

## SOUL.md Sections (12)

| Seção | Descrição |
|-------|-----------|
| Identity | Nome, papel, contexto |
| Core Principles | Filosofias L1 |
| Mental Models | Modelos L2 |
| Communication Style | Padrões L5 |
| Frameworks | Metodologias L3 |
| Obsessions | Temas L6 |
| Paradoxes | Tensões L8 |
| Anti-Patterns | O que NÃO fazer |
| Voice Examples | Samples de comunicação |
| Activation Protocol | Como ativar comportamentos |
| Boundaries | Limites de conhecimento |
| Closing Protocol | Como encerrar interações |

## Validation Checks

- ✓ Todas as 12 seções presentes
- ✓ Referências a chunks válidas
- ✓ Sem placeholders genéricos
- ✓ Voice consistent com L5 patterns

## Exemplo

```
@nero-architect *generate --persona jeremy-miner --template v4.0
```

## Agentes Relacionados

- `@nero-fidelity` - Upstream (DNA validado)
- `@nero-emulator` - Downstream (clone testing)
