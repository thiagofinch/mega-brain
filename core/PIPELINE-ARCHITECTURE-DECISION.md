# Pipeline Architecture Decision

> **Data:** 2026-03-05
> **Status:** APROVADO
> **Decisão:** Pipeline única com branches condicionais

---

## Contexto

O Mega Brain agora opera em 3 dimensões (Expert, Business, Personal). Precisamos decidir como processar ingestão de materiais.

## Opções Avaliadas

| Critério | Pipeline única (3 branches) | Pipelines separadas |
|---|---|---|
| Manutenção | Mais simples — 1 codebase | Mais complexo — 3 codebases |
| Segurança | Requer isolamento cuidadoso | Isolamento natural |
| Flexibilidade | Branch condicional por metadado | Input handlers independentes |
| Risco de vazamento L3 | Médio (mitigado com guards) | Baixo |
| Reutilização | Alta — chunking, indexing, entity extraction compartilhados | Baixa — código duplicado |

## Decisão

**Pipeline única com branches condicionais** baseadas em metadado `bucket` no cabeçalho de cada arquivo ingerido.

### Como Funciona

1. Todo material ingerido recebe header com metadado:
   ```yaml
   bucket: external|workspace|personal
   source: nome-da-fonte
   type: video|pdf|transcript|slack|email|call|note
   ```

2. O pipeline verifica `bucket` e roteia:
   - `external` → Pipeline JARVIS existente (5 fases)
   - `workspace` → Business pipeline (normalize → classify → index)
   - `personal` → Personal pipeline (sanitize → classify → index)

3. Cada branch tem:
   - Seu próprio RAG index (.data/rag_expert, .data/rag_business, knowledge/personal/index/)
   - Suas próprias regras de privacidade
   - Seus próprios output destinations

### Guardrails de Segurança

- Personal pipeline NUNCA escreve fora de knowledge/personal/
- Business pipeline NUNCA escreve em knowledge/external/
- Cross-bucket queries passam por bucket_router.py com access control

## Impacto

- core/intelligence/rag/ precisa de bucket_router.py (novo)
- Chunker recebe parâmetro `bucket` para escolher destino do índice
- MCP server atualizado com parâmetro `buckets` em search_knowledge

---

*Decisão documentada conforme PRD Megabrain 3D, Tarefa 6.1*
