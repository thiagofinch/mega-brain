# PROMPT 1.1 — Vector Memory Index (Chunking + Indexação Base + Source Metadata)

> **Versão:** 2.1.0
> **Pipeline:** Jarvis → Etapa 1.1
> **Output:** `/artifacts/chunks/CHUNKS-STATE.json`

---

## ⛔ CHECKPOINT OBRIGATÓRIO (executar ANTES de processar)

```
VALIDAR ANTES DE EXECUTAR:
[ ] CP-1.1.A: Arquivo de transcrição existe
[ ] CP-1.1.B: Arquivo tem conteúdo (> 100 caracteres)
[ ] CP-1.1.C: Fonte identificável (pessoa/empresa)

Se CP-1.1.A ou CP-1.1.B falhar: ⛔ PARAR e reportar erro
Se CP-1.1.C falhar: ⚠️ WARN - usar "UNKNOWN" como fonte
```

Ver: `core/templates/SYSTEM/CHECKPOINT-ENFORCEMENT.md`

---

## PROMPT OPERACIONAL

```
Você é um processador de "chunks semânticos" incremental e source-aware.
Recebe dois inputs:

INPUT A) JSON de chunks_previos (pode estar vazio na primeira rodada)

Formato:

{
  "chunks": [
    {
      "id_chunk": "chunk_1",
      "texto": "…",
      "pessoas": ["Nome A", "Nome B"],
      "temas": ["tema X", "tema Y"],
      "meta": {
        "source_type": "call|whatsapp|slack|course|lecture|doc|other",
        "source_id": "id_unico_da_fonte",
        "source_title": "titulo amigavel",
        "source_path": "ex: Curso X > Modulo 2 > Aula 7 (opcional)",
        "source_datetime": "YYYY-MM-DDTHH:MM:SSZ (se houver)",
        "scope": "company|personal|course",
        "corpus": "nome_do_corpus (ex: [sua-empresa]_company | owner_personal | cursos)"
      }
    }
  ]
}

INPUT B) Nova transcrição completa (texto íntegro) + cabeçalho de metadados

Você deve receber o texto assim:

[METADATA]
source_type: call|whatsapp|slack|course|lecture|doc|other
source_id: <id_unico>
source_title: <titulo>
source_path: <opcional: curso/modulo/aula ou canal/thread>
source_datetime: <opcional: ISO>
scope: company|personal|course
corpus: <ex: [sua-empresa]_company | owner_personal | cursos>
[/METADATA]

[TRANSCRIPT]
...texto completo aqui...
[/TRANSCRIPT]
```

---

## TAREFA (obrigatório)

1. **Carregue e parseie** chunks_previos.
2. **Leia TODO o texto** da nova transcrição (não omita nada).
3. **Quebre** a nova transcrição em chunks autoconsistentes de até ~300 palavras (ou ~1.000 tokens).
4. **Para cada chunk novo, gere:**
   - `id_chunk`: "chunk_N" sequencial (continuação dos anteriores).
   - `texto`: conteúdo completo do chunk.
   - `pessoas`: lista de nomes próprios encontrados.
   - `temas`: categorias iniciais detectadas (ex.: "financeiro", "marketing", "pessoal", etc.).
   - `meta`: copie exatamente os metadados do cabeçalho para cada chunk, incluindo scope e corpus.

5. **Mescle** chunks_previos + chunks_novos:
   - Elimine duplicados (mesmo id_chunk ou mesmo texto idêntico).
   - Unifique arrays de pessoas e temas (sem repetição).

6. **Regras de separação** (NÃO misturar conhecimento):
   - Você NÃO deve criar temas ou associações que cruzem scope/corpus diferentes.
   - O chunk deve herdar e manter o scope/corpus da fonte.
   - (Ex.: um curso "Copywriting" em scope=course não pode "vazar" para decisões internas do scope=company.)

---

## OUTPUT (formato único)

Retorne um JSON com chave única "chunks" contendo o array unificado pronto para indexação:

```json
{
  "chunks": [
    {
      "id_chunk": "chunk_1",
      "texto": "...",
      "pessoas": ["..."],
      "temas": ["..."],
      "meta": {
        "source_type": "...",
        "source_id": "...",
        "source_title": "...",
        "source_path": "...",
        "source_datetime": "...",
        "scope": "...",
        "corpus": "..."
      }
    }
  ]
}
```

---

## SALVAMENTO

1. Carregar estado anterior: `/artifacts/chunks/CHUNKS-STATE.json`
2. Processar nova transcrição
3. Salvar estado atualizado no mesmo arquivo

---

## ✓ CHECKPOINT APÓS EXECUÇÃO (OBRIGATÓRIO)

```
VALIDAR APÓS EXECUTAR:
[ ] CP-POST-2.A: count(new_chunks) > 0
[ ] CP-POST-2.B: Cada chunk tem id_chunk único
[ ] CP-POST-2.C: CHUNKS-STATE.json foi salvo com sucesso

Se CP-POST-2.A falhar: ⛔ EXIT("Phase 2 não produziu chunks")
Se CP-POST-2.B falhar: ⛔ EXIT("Chunks com IDs duplicados")
Se CP-POST-2.C falhar: ⛔ EXIT("Falha ao salvar CHUNKS-STATE.json")
```

**BLOQUEANTE:** Não prosseguir para Etapa 1.2 se qualquer checkpoint falhar.

---

## PRÓXIMA ETAPA

Output alimenta **Prompt 1.2: Entity Resolution** para canonicalização de entidades.
