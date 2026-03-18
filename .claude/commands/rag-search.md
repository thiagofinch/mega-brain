# /rag-search - Busca Semântica no Mega Brain

Execute uma busca inteligente na knowledge base usando o Hybrid RAG System.

## Uso

```
/rag-search "sua pergunta aqui"
```

## Argumentos

$ARGUMENTS é a query de busca em linguagem natural.

## Instruções para Claude

Ao receber este comando:

1. **Executar busca via Adaptive Router (seleciona pipeline ideal):**
   ```bash
   python3 -m core.intelligence.rag.adaptive_router "$ARGUMENTS"
   ```

2. **Se precisar de busca cross-expert (grafo):**
   ```bash
   python3 -m core.intelligence.rag.graph_query "$ARGUMENTS"
   ```

3. **Se precisar de busca associativa (HippoRAG):**
   ```bash
   python3 -m core.intelligence.rag.associative_memory "$ARGUMENTS"
   ```

4. **Analisar resultados:**
   - Ler o contexto retornado
   - Identificar as fontes mais relevantes (chunk_ids, persons, domains)
   - Sintetizar uma resposta baseada no conhecimento encontrado

5. **Formatar resposta:**
   ```
   ## Resposta
   [Síntese baseada nos resultados da busca]

   ## Fontes Consultadas
   - [Lista de chunk_ids e arquivos relevantes]

   ## Pipeline Utilizado
   [A=BM25 | B=Hybrid | C=Graph+Hybrid | D=Full | E=LLM-only]

   ## Confiança
   [ALTA/MÉDIA/BAIXA] - [justificativa]
   ```

## Opções Avançadas

```bash
# Busca padrão (router seleciona pipeline)
python3 -m core.intelligence.rag.adaptive_router "commission structure"

# Busca híbrida direta (BM25 + vector)
python3 -m core.intelligence.rag.hybrid_query "commission structure"

# Busca cross-expert via grafo
python3 -m core.intelligence.rag.graph_query "O que todos experts dizem sobre comissão?"

# Busca associativa (HippoRAG - conexões que vector search não encontra)
python3 -m core.intelligence.rag.associative_memory "Christmas Tree Structure"

# Cross-expert connections para um conceito
python3 -m core.intelligence.rag.associative_memory --cross-expert "CLOSER Framework" --source-person "cole-gordon"

# MCP Server test mode (simula tool call)
python3 -m core.intelligence.rag.mcp_server --test search_knowledge --query "hiring process"
python3 -m core.intelligence.rag.mcp_server --test search_deep --query "best compensation model"
python3 -m core.intelligence.rag.mcp_server --test resolve_chunk --chunk-id "HEUR-AH-025"
```

## Pipelines Disponíveis

| Pipeline | Latência | Quando Usa | Intent |
|----------|----------|------------|--------|
| A: BM25 Only | ~15ms | Lookup factual simples | factual_simple |
| B: Hybrid | ~80ms | Semântico + keyword | factual_complex |
| C: Hybrid+Graph | ~200ms | Cross-expert, analítico | analytical, cross_expert |
| D: Full | ~500ms | Máximo recall | hierarchical |
| E: LLM-only | ~0ms | Sem retrieval | greeting, meta |

## MCP Tools (via .mcp.json)

| Tool | O Que Faz |
|------|-----------|
| `search_knowledge` | Hybrid search com filtros (person, domain) |
| `search_cross_expert` | Graph query para cruzar fontes |
| `search_deep` | Full pipeline com todos layers |
| `get_agent_context` | Contexto trimado de um agente |
| `resolve_chunk` | chunk_id → texto completo + source |

## Exemplos

```
/rag-search "Como estruturar comissionamento para closers?"
/rag-search "Qual o framework CLOSER?"
/rag-search "O que Hormozi e Cole Gordon dizem sobre hiring?"
/rag-search "Heurísticas para ticket acima de 50k"
```

## Pré-requisitos

- Index BM25 construído: `python3 -m core.intelligence.rag.hybrid_index --bm25-only`
- Knowledge graph construído: `python3 -m core.intelligence.rag.graph_builder --build`
- Para embeddings: VOYAGE_API_KEY no .env + `pip install voyageai`

## Rebuild do Índice

```bash
# Rebuild BM25 (após novo conteúdo no knowledge/)
python3 -m core.intelligence.rag.hybrid_index --bm25-only

# Rebuild knowledge graph (após novos DNAs)
python3 -m core.intelligence.rag.graph_builder --build

# Ver stats do index
python3 -m core.intelligence.rag.chunker --stats
python3 -m core.intelligence.rag.graph_builder --stats
```
