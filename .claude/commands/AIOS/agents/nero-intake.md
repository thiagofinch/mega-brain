# nero-intake

Ativa o @nero-intake para chunking e tagging de sources.

## Uso

```
/AIOS:agents:nero-intake
@nero-intake
```

## Quando Usar

- Processar sources aprovados pelo APEX Gate
- Chunking inteligente de conteúdo longo
- Tagging de chunks por layer potencial
- Preparar material para extração cognitiva

## Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `*help` | Lista comandos disponíveis |
| `*intake {source}` | Processa source individual |
| `*chunk {source}` | Aplica chunking strategy |
| `*tag {chunk_id}` | Adiciona tags a chunk |
| `*batch {folder}` | Processa pasta de sources |
| `*stats` | Estatísticas de processamento |
| `*handoff` | Entrega chunks para nero-cognitive |
| `*exit` | Desativa agente |

## Chunking Strategy

| Conteúdo | Estratégia | Tamanho |
|----------|------------|---------|
| Transcrição | Semantic breaks | 500-1500 tokens |
| Texto longo | Paragraph groups | 800-1200 tokens |
| Posts curtos | Aggregation | Múltiplos juntos |

## Tags Aplicáveis

- `L1-L5` - Layer potencial (Observable)
- `L6-L8` - Layer potencial (Deep Identity)
- `HIGH-VALUE` - Chunk com framework/modelo mental
- `VOICE` - Chunk com padrões de comunicação
- `PARADOX` - Contradição aparente detectada

## Exemplo

```
@nero-intake *batch --folder ./sources/cole-gordon/ --strategy semantic
```

## Agente Downstream

- `@nero-cognitive` - Recebe chunks tagueados para extração L1-L5
