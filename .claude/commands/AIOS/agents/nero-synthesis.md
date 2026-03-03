# nero-synthesis

Ativa o @nero-synthesis para canonicalização e knowledge graph.

## Uso

```
/AIOS:agents:nero-synthesis
@nero-synthesis
```

## Quando Usar

- Consolidar extrações de todos os 8 layers
- Resolver conflitos entre patterns
- Gerar unified_dna.yaml canônico
- Construir knowledge graph de relacionamentos

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*receive {persona}` | Recebe extrações de L1-L8 |
| `*analyze` | Analisa padrões e conflitos |
| `*canonicalize` | Gera unified_dna.yaml |
| `*graph` | Constrói knowledge graph |
| `*package` | Empacota DNA para architect |
| `*conflicts` | Lista conflitos a resolver |
| `*exit` | Desativa agente |

## Outputs

| Output | Descrição |
|--------|-----------|
| `unified_dna.yaml` | DNA Mental™ canônico |
| `knowledge_graph.json` | Grafo de entidades |
| `cross_references.md` | Referências cruzadas |
| `synthesis_report.md` | Relatório de síntese |

## Cross-Layer Analysis

```
L1 (Filosofia) ←→ L3 (Framework)
   "Qual framework implementa qual filosofia?"

L4 (Heurística) ←→ L8 (Paradoxo)
   "Quando heurísticas entram em conflito?"

L5 (Voz) ←→ L6 (Obsessão)
   "Quais obsessões se manifestam no estilo?"
```

## Exemplo

```
@nero-synthesis *canonicalize --persona cole-gordon --resolve-conflicts auto
```

## Agentes Relacionados

- `@nero-cognitive` + `@nero-identity` - Upstream (extrações L1-L8)
- `@nero-fidelity` - Downstream (para validação)
