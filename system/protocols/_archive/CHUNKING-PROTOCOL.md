# CHUNKING PROTOCOL (Prompt 1.1)

> **Versão:** 1.0.0
> **Pipeline:** Jarvis → Etapa 1.1
> **Output:** `/processing/chunks/CHUNKS-{SOURCE}-{DATE}.json`

---

## PROPÓSITO

Transformar conteúdo bruto em chunks semânticos preservando:
- Contexto suficiente para compreensão isolada
- Metadados de rastreabilidade
- Estrutura para processamento downstream

---

## INPUT

```
{
  "source": {
    "source_id": "unique_id",
    "source_type": "call|video|doc|meeting",
    "source_title": "Título do conteúdo",
    "source_datetime": "YYYY-MM-DD HH:MM",
    "source_duration_minutes": N,
    "corpus": "empresa|pessoal|cursos",
    "participants": ["Nome1", "Nome2"]
  },
  "raw_content": "Conteúdo completo da transcrição ou documento..."
}
```

---

## TAREFA

### 1. Identificação de Quebras Naturais

Identificar pontos de quebra onde:
- Muda o tópico principal sendo discutido
- Muda o speaker (em transcrições)
- Há conclusão de um argumento/ideia
- Inicia nova seção/capítulo (em docs)

### 2. Criação de Chunks

Para cada segmento identificado, criar chunk com:

```json
{
  "id_chunk": "chunk_{source_id}_{sequential_number}",
  "content": "Texto do segmento...",
  "timestamp_start": "HH:MM:SS",
  "timestamp_end": "HH:MM:SS",
  "speaker": "Nome ou null",
  "topic_hint": "Descrição curta do tópico (5-10 palavras)",
  "mentions": {
    "persons": ["Nome1", "Nome2"],
    "companies": ["Empresa1"],
    "themes": ["tema1", "tema2"]
  },
  "metadata": {
    "word_count": N,
    "has_numbers": true|false,
    "has_framework": true|false,
    "sentiment": "positive|negative|neutral",
    "actionability": "high|medium|low"
  }
}
```

### 3. Regras de Tamanho

| Tipo de Conteúdo | Tamanho Ideal | Máximo |
|------------------|---------------|--------|
| Transcrição call | 200-400 palavras | 600 palavras |
| Vídeo longo | 300-500 palavras | 800 palavras |
| Documento | 400-600 palavras | 1000 palavras |

### 4. Regras de Contexto

- **Overlap:** Se necessário, incluir 1-2 frases do chunk anterior para contexto
- **Referências:** Se chunk menciona "isso" ou "aquilo", incluir contexto suficiente
- **Completude:** Chunk deve ser compreensível isoladamente

---

## OUTPUT

```json
{
  "chunking_result": {
    "source": { /* cópia do input source */ },
    "processing_datetime": "YYYY-MM-DD HH:MM:SS",
    "chunks_total": N,
    "chunks": [
      {
        "id_chunk": "chunk_source123_001",
        "content": "...",
        "timestamp_start": "00:01:30",
        "timestamp_end": "00:03:45",
        "speaker": "Alex Hormozi",
        "topic_hint": "Estrutura de comissionamento para closers",
        "mentions": {
          "persons": ["Alex Hormozi"],
          "companies": ["Alex Hormozi"],
          "themes": ["comissionamento", "closer", "high-ticket"]
        },
        "metadata": {
          "word_count": 287,
          "has_numbers": true,
          "has_framework": false,
          "sentiment": "neutral",
          "actionability": "high"
        }
      },
      /* ... mais chunks ... */
    ],
    "summary": {
      "total_words": N,
      "avg_chunk_size": N,
      "unique_speakers": ["Nome1", "Nome2"],
      "main_topics": ["topic1", "topic2", "topic3"]
    }
  }
}
```

---

## REGRAS DE QUALIDADE

### FAZER:
- Preservar citações exatas quando relevantes
- Manter números e métricas precisos
- Incluir contexto suficiente para compreensão
- Identificar todos os speakers mencionados
- Extrair temas mesmo que implícitos

### NÃO FAZER:
- Quebrar no meio de uma ideia/argumento
- Criar chunks muito pequenos (<100 palavras) exceto se for citação importante
- Remover contexto que deixaria chunk ambíguo
- Inferir informações não presentes no texto

---

## EXEMPLO DE CHUNKING

### Input (trecho):
```
[00:12:30] Alex Hormozi: "A estrutura de comissão que funciona é simples:
25-30% do valor do deal para o closer. Não complique. Se você está pagando
menos que isso em high-ticket, seus melhores closers vão embora.

[00:13:15] O que eu vejo muito é empresa querendo pagar 10-15% e depois
reclamando que não consegue reter talento. É óbvio. Você está competindo
com quem paga o dobro.

[00:14:00] Entrevistador: E como você estrutura o ramp-up de novos closers?

[00:14:10] Alex Hormozi: Primeiro, dou 90 dias de garantia. O cara recebe
um salário base garantido enquanto está aprendendo o processo..."
```

### Output (chunk):
```json
{
  "id_chunk": "chunk_hormozi_podcast_001",
  "content": "Alex Hormozi: \"A estrutura de comissão que funciona é simples: 25-30% do valor do deal para o closer. Não complique. Se você está pagando menos que isso em high-ticket, seus melhores closers vão embora. O que eu vejo muito é empresa querendo pagar 10-15% e depois reclamando que não consegue reter talento. É óbvio. Você está competindo com quem paga o dobro.\"",
  "timestamp_start": "00:12:30",
  "timestamp_end": "00:13:45",
  "speaker": "Alex Hormozi",
  "topic_hint": "Estrutura de comissão para closers high-ticket",
  "mentions": {
    "persons": ["Alex Hormozi"],
    "companies": [],
    "themes": ["comissionamento", "closer", "high-ticket", "retenção"]
  },
  "metadata": {
    "word_count": 89,
    "has_numbers": true,
    "has_framework": false,
    "sentiment": "neutral",
    "actionability": "high"
  }
}
```

---

## SALVAMENTO

Salvar output em:
```
/processing/chunks/CHUNKS-{SOURCE_ID}-{YYYYMMDD}.json
```

Exemplo: `CHUNKS-HORMOZI-PODCAST-234-20251215.json`

---

## PRÓXIMA ETAPA

Output alimenta **Prompt 1.2: Entity Resolution** para canonicalização de entidades.
