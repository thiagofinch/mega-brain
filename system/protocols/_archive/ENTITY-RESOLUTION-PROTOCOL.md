# ENTITY RESOLUTION PROTOCOL (Prompt 1.2)

> **Versão:** 1.0.0
> **Pipeline:** Jarvis → Etapa 1.2
> **Output:** `/processing/canonical/CANONICAL-MAP.json`

---

## PROPÓSITO

Resolver variações de nomes para formas canônicas, garantindo:
- Consistência entre chunks e fontes
- Rastreabilidade de entidades
- Base para agregação de insights

---

## INPUTS

### Input A: chunking_result (output do Prompt 1.1)
```json
{
  "chunking_result": {
    "chunks": [
      {
        "id_chunk": "...",
        "mentions": {
          "persons": ["Alex", "Hormozi", "Alex Hormozi"],
          "companies": ["Acquisition", "Alex Hormozi"],
          "themes": ["comissão", "comissionamento"]
        }
      }
    ]
  }
}
```

### Input B: canonical_state (estado acumulado anterior)
```json
{
  "canonical_state": {
    "persons": {
      "Alex Hormozi": {
        "canonical": "Alex Hormozi",
        "aliases": ["Alex", "Hormozi", "AH"],
        "type": "person",
        "metadata": {
          "company": "Alex Hormozi",
          "role": "CEO/Founder",
          "first_seen": "2025-12-10"
        }
      }
    },
    "companies": { /* ... */ },
    "themes": { /* ... */ }
  }
}
```

---

## TAREFA

### 1. Para cada menção nos chunks:

#### Pessoas:
- Verificar se existe no canonical_state
- Se existe: mapear para forma canônica, adicionar alias se novo
- Se não existe: criar nova entrada canônica

#### Empresas:
- Mesma lógica de pessoas
- Normalizar variações (Alex Hormozi, Acquisition, alex-hormozi → Alex Hormozi)

#### Temas:
- Mapear sinônimos para tema canônico
- Usar glossário existente como referência
- Criar novo tema canônico se genuinamente novo

### 2. Regras de Canonicalização

| Tipo | Regra | Exemplo |
|------|-------|---------|
| Pessoa | Nome completo preferido | "Alex" → "Alex Hormozi" |
| Empresa | Nome oficial com domínio | "Acquisition" → "Alex Hormozi" |
| Tema | Termo do glossário | "comissão" → "comissionamento" |

### 3. Resolução de Ambiguidades

Se não for possível determinar:
- Marcar como `"confidence": "low"`
- Adicionar `"needs_review": true`
- Não assumir — documentar incerteza

---

## OUTPUT

### canonical_state (atualizado)
```json
{
  "canonical_state": {
    "version": "1.0.0",
    "last_updated": "YYYY-MM-DD HH:MM:SS",

    "persons": {
      "Alex Hormozi": {
        "canonical": "Alex Hormozi",
        "aliases": ["Alex", "Hormozi", "AH", "Hormozi, Alex"],
        "type": "person",
        "metadata": {
          "company": "Alex Hormozi",
          "role": "CEO/Founder",
          "expertise": ["scaling", "sales", "offers"],
          "first_seen": "2025-12-10",
          "last_seen": "2025-12-15",
          "chunk_count": 47
        }
      },
      "Cole Gordon": {
        "canonical": "Cole Gordon",
        "aliases": ["Cole", "Gordon", "CG"],
        "type": "person",
        "metadata": {
          "company": "Cole Gordon",
          "role": "Founder",
          "expertise": ["closing", "sales training"],
          "first_seen": "2025-12-12",
          "last_seen": "2025-12-15",
          "chunk_count": 32
        }
      }
    },

    "companies": {
      "Alex Hormozi": {
        "canonical": "Alex Hormozi",
        "aliases": ["Acquisition", "alex-hormozi", "Acq"],
        "type": "company",
        "metadata": {
          "founder": "Alex Hormozi",
          "industry": "business education",
          "first_seen": "2025-12-10"
        }
      }
    },

    "themes": {
      "comissionamento": {
        "canonical": "comissionamento",
        "aliases": ["comissão", "commission", "comp", "compensação variável"],
        "type": "theme",
        "category": "04-COMISSIONAMENTO",
        "related_themes": ["closer", "vendas", "incentivos"],
        "first_seen": "2025-12-10"
      },
      "estrutura-time": {
        "canonical": "estrutura-time",
        "aliases": ["estrutura de time", "team structure", "org chart"],
        "type": "theme",
        "category": "01-ESTRUTURA-TIME",
        "related_themes": ["hiring", "roles", "escalabilidade"],
        "first_seen": "2025-12-10"
      }
    },

    "stats": {
      "total_persons": 15,
      "total_companies": 8,
      "total_themes": 23,
      "pending_review": 3
    }
  }
}
```

### chunks_resolved (chunks com entidades canonicalizadas)
```json
{
  "chunks_resolved": {
    "processing_datetime": "YYYY-MM-DD HH:MM:SS",
    "source_chunking_file": "CHUNKS-HORMOZI-PODCAST-234-20251215.json",
    "chunks": [
      {
        "id_chunk": "chunk_hormozi_podcast_001",
        "content": "...",
        "mentions_canonical": {
          "persons": ["Alex Hormozi"],
          "companies": ["Alex Hormozi"],
          "themes": ["comissionamento", "closer", "high-ticket"]
        },
        "mentions_raw": {
          "persons": ["Alex", "Hormozi"],
          "companies": ["Acquisition"],
          "themes": ["comissão", "closer", "high-ticket"]
        },
        "resolution_confidence": "high"
      }
    ]
  }
}
```

---

## REGRAS DE MERGE

### Ao encontrar entidade existente:
1. **Aliases:** ADICIONAR novo alias se não existir
2. **Metadata:** ATUALIZAR last_seen, INCREMENT chunk_count
3. **Expertise/Related:** ADICIONAR novos, não remover existentes

### Ao encontrar entidade nova:
1. Criar entrada completa
2. Buscar possíveis conexões com existentes
3. Marcar `first_seen` com data atual

### Ao encontrar conflito:
1. NÃO resolver arbitrariamente
2. Documentar em `pending_review`
3. Manter ambas formas até resolução manual

---

## VALIDAÇÃO

Antes de salvar, verificar:

| Check | Critério |
|-------|----------|
| Unicidade | Nenhum alias aparece em múltiplas entidades |
| Completude | Todo chunk tem mentions_canonical |
| Consistência | Aliases não conflitam entre tipos |
| Rastreabilidade | Todo canonical tem first_seen |

---

## SALVAMENTO

### Canonical Map:
```
/processing/canonical/CANONICAL-MAP.json
```
(Arquivo único, atualizado incrementalmente)

### Chunks Resolvidos:
```
/processing/canonical/CHUNKS-RESOLVED-{YYYYMMDD}.json
```
(Um por rodada de processamento)

---

## INTEGRAÇÃO COM GLOSSÁRIO

Consultar `/system/GLOSSARY/` para:
- Termos canônicos de temas
- Sinônimos oficiais
- Categorização correta

Se tema não existe no glossário:
- Criar entrada no canonical_state
- Sugerir adição ao glossário apropriado

---

## PRÓXIMA ETAPA

Output alimenta **Prompt 2.1: Insight Extraction** para extração priorizada de insights.
