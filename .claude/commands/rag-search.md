# /rag-search - Busca Semântica no Mega Brain

Execute uma busca semântica na knowledge base usando RAG.

## Uso

```
/rag-search "sua pergunta aqui"
```

## Argumentos

$ARGUMENTS é a query de busca em linguagem natural.

## Instruções para Claude

Ao receber este comando:

1. **Executar busca RAG:**
   ```bash
   cd "scripts/tmp-scripts"
   python rag_query.py "$ARGUMENTS" --context
   ```

2. **Analisar resultados:**
   - Ler o contexto retornado
   - Identificar as fontes mais relevantes
   - Sintetizar uma resposta baseada no conhecimento encontrado

3. **Formatar resposta:**
   ```
   ## Resposta
   [Síntese baseada nos resultados da busca]

   ## Fontes Consultadas
   - [Lista de arquivos/seções relevantes]

   ## Confiança
   [ALTA/MÉDIA/BAIXA] - [justificativa]
   ```

## Opções Avançadas

Para buscas filtradas, execute manualmente:

```bash
cd "scripts/tmp-scripts"

# Filtrar por tema
python rag_query.py "query" --theme "PROCESSO-VENDAS"

# Filtrar por fonte
python rag_query.py "query" --source "Alex Hormozi"

# Mais resultados
python rag_query.py "query" --top-k 15

# Output JSON (para análise)
python rag_query.py "query" --json
```

## Exemplos

```
/rag-search "Como estruturar comissionamento para closers?"
/rag-search "Qual o framework CLOSER?"
/rag-search "Métricas de conversão B2B"
```

## Pré-requisitos

- Index RAG criado: `cd scripts/tmp-scripts && python rag_index.py --full`
- VOYAGE_API_KEY configurada no .env
- Dependências instaladas: `pip install chromadb voyageai tiktoken`

## Status do Índice

Para verificar status: `cd scripts/tmp-scripts && python rag_status.py`
