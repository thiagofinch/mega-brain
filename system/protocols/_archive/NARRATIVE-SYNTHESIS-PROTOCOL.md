# NARRATIVE SYNTHESIS PROTOCOL (Prompt 3.1)

> **Versão:** 1.0.0
> **Pipeline:** Jarvis → Etapa 3.1
> **Output:** `/processing/narratives/NARRATIVES-STATE.json`

---

## PROPÓSITO

Sintetizar insights em narrativas coerentes por entidade:
- Consolidar conhecimento fragmentado
- Identificar padrões e tensões
- Preparar estrutura para dossiês

---

## INPUTS

### Input A: insights_state (output do Prompt 2.1)
```json
{
  "insights_state": {
    "persons": {
      "Alex Hormozi": [ /* lista de insights */ ]
    },
    "themes": {
      "comissionamento": [ /* lista de insights */ ]
    }
  }
}
```

### Input B: narratives_state (estado acumulado anterior)
```json
{
  "narratives_state": {
    "persons": { /* narrativas existentes */ },
    "themes": { /* narrativas existentes */ }
  }
}
```

---

## TAREFA

### 1. Para cada PESSOA com insights:

#### Síntese Narrativa:
- Ler TODOS os insights da pessoa
- Identificar padrões recorrentes
- Construir narrativa coerente de "quem é essa pessoa"
- Destacar posicionamentos por tema

#### Identificar:
- **Padrões decisórios:** Como a pessoa pensa/decide
- **Posições por tema:** O que pensa sobre assuntos específicos
- **Tensões:** Contradições aparentes nos insights
- **Open loops:** Questões não respondidas
- **Next questions:** O que ainda precisamos saber

### 2. Para cada TEMA com insights:

#### Síntese Temática:
- Ler TODOS os insights do tema
- Identificar consensos entre pessoas
- Identificar divergências
- Consolidar métricas e benchmarks
- Extrair frameworks aplicáveis

#### Identificar:
- **Consensos:** Onde múltiplas fontes concordam
- **Divergências:** Onde fontes discordam
- **Gaps:** O que falta saber sobre o tema
- **Frameworks:** Modelos práticos extraídos

---

## OUTPUT

### narratives_state
```json
{
  "narratives_state": {
    "version": "1.0.0",
    "last_updated": "YYYY-MM-DD HH:MM:SS",

    "persons": {
      "Alex Hormozi": {
        "canonical": "Alex Hormozi",
        "narrative": "Alex Hormozi emerge como estrategista de escala agressiva, consistentemente priorizando velocidade de execução sobre perfeição e simplicidade operacional sobre complexidade técnica. Sua abordagem é marcada por recomendações absolutas, testadas extensivamente antes de compartilhar, com baixa tolerância para nuances.",
        "last_updated": "2025-12-15",
        "scope": "completo",
        "corpus": "cursos",
        "insights_included": ["insight_001", "insight_003", "insight_015"],
        "patterns": [
          {
            "name": "Velocidade sobre Perfeição",
            "description": "Prioriza execução rápida sobre planejamento extensivo",
            "evidence_chunks": ["chunk_12", "chunk_34", "chunk_41"],
            "confidence": "high"
          },
          {
            "name": "Incentivo Financeiro Direto",
            "description": "Compensação generosa supera microgerenciamento",
            "evidence_chunks": ["chunk_8", "chunk_22", "chunk_45"],
            "confidence": "high"
          }
        ],
        "positions_by_theme": {
          "comissionamento": {
            "position": "25-30% do deal para closer, pago imediatamente",
            "nuances": [
              "Exige qualificação rigorosa de leads",
              "Pode escalar para 35% em tickets >$25k"
            ],
            "evidence_chunks": ["chunk_8", "chunk_22"],
            "confidence": "high"
          },
          "estrutura-time": {
            "position": "Time magro e especializado, 3 excepcionais > 10 medianos",
            "nuances": [
              "Setter/closer separados em escala",
              "Ratio 1:2-3 closer:setter"
            ],
            "evidence_chunks": ["chunk_18", "chunk_29"],
            "confidence": "high"
          }
        },
        "tensions": [
          {
            "title": "Velocidade vs Qualidade de Contratação",
            "point_a": {
              "statement": "Ship it. Fix later.",
              "chunk": "chunk_12"
            },
            "point_b": {
              "statement": "Esperar 6 meses pela pessoa certa",
              "chunk": "chunk_27"
            },
            "possible_explanation": "Velocidade para processos, paciência para pessoas",
            "status": "resolved"
          }
        ],
        "open_loops": [
          {
            "question": "Estrutura de comp para SDR/BDR?",
            "impact": "Não coberto nas fontes",
            "status": "open"
          }
        ],
        "next_questions": [
          "Qual a estrutura de ramp-up para novos closers?",
          "Como lidar com closer performante mas tóxico?"
        ]
      }
    },

    "themes": {
      "comissionamento": {
        "canonical": "comissionamento",
        "narrative": "O tema comissionamento apresenta consenso forte em torno de estruturas generosas para closers de high-ticket, com benchmark de 25-30% emergindo como padrão recomendado por múltiplas fontes.",
        "last_updated": "2025-12-15",
        "scope": "parcial",
        "corpus": "cursos",
        "insights_included": ["insight_001", "insight_008", "insight_022"],
        "consensuses": [
          {
            "statement": "Comissão generosa (25-30%) para closers high-ticket",
            "agreeing_persons": ["Alex Hormozi", "Cole Gordon"],
            "evidence_chunks": ["chunk_8", "chunk_22", "chunk_45"],
            "strength": "strong"
          }
        ],
        "divergences": [
          {
            "title": "Timing do pagamento",
            "person_a": {
              "name": "Alex Hormozi",
              "position": "Pagamento imediato após fechamento",
              "chunk": "chunk_22"
            },
            "person_b": {
              "position": "Pagamento após período de garantia",
              "chunk": "chunk_78"
            },
            "analysis": "Contextos diferentes: B2C vs B2B"
          }
        ],
        "frameworks": [
          {
            "name": "Estrutura de Comissão High-Ticket",
            "source_person": "Alex Hormozi",
            "structure": "Base 25-30%, escalável por ticket size",
            "when_to_use": "Vendas >$3k com qualificação rigorosa",
            "limitations": "Exige processo de qualificação forte",
            "chunk": "chunk_8"
          }
        ],
        "metrics": [
          {
            "metric": "Comissão closer",
            "value": "25-30%",
            "source": "Alex Hormozi",
            "context": "High-ticket B2C",
            "confidence": "high",
            "chunk": "chunk_8"
          }
        ],
        "gaps": [
          {
            "question": "Estrutura para inside sales (não high-ticket)?",
            "impact": "Não aplicável para todos os modelos",
            "status": "open"
          }
        ]
      }
    },

    "stats": {
      "total_persons": 8,
      "total_themes": 12,
      "persons_with_tensions": 3,
      "themes_with_divergences": 5
    }
  }
}
```

---

## REGRAS DE SÍNTESE

### Para NARRATIVA de Pessoa:
1. Ler todos os insights HIGH primeiro
2. Identificar 2-3 padrões dominantes
3. Escrever narrativa em 3-5 linhas
4. Mapear posições por tema mencionado
5. Documentar tensões aparentes
6. Listar questions que ficaram abertas

### Para NARRATIVA de Tema:
1. Agrupar insights por pessoa
2. Identificar onde concordam (consensos)
3. Identificar onde discordam (divergências)
4. Extrair frameworks aplicáveis
5. Consolidar métricas em tabela
6. Documentar gaps de conhecimento

---

## REGRAS DE ATUALIZAÇÃO

| Elemento | Comportamento |
|----------|---------------|
| Narrativa | REFINAR se novos insights mudam entendimento |
| Patterns | ADICIONAR novos, EXPANDIR evidências |
| Positions | ADICIONAR temas novos, ATUALIZAR nuances |
| Tensions | ADICIONAR novas, ATUALIZAR status |
| Open Loops | ADICIONAR novos, FECHAR resolvidos |
| Next Questions | SUBSTITUIR com base em gaps atuais |

---

## VALIDAÇÃO

Antes de salvar:

| Check | Critério |
|-------|----------|
| Cobertura | Toda pessoa com insights tem narrative |
| Rastreabilidade | Todo pattern tem evidence_chunks |
| Consistência | Tensions documentam ambos os lados |
| Completude | Temas linkam às pessoas e vice-versa |

---

## SALVAMENTO

```
/processing/narratives/NARRATIVES-STATE.json
```
(Arquivo único, atualizado incrementalmente)

---

## PRÓXIMA ETAPA

Output alimenta **Prompt 4.0: Dossier Compilation** para geração de dossiês Markdown.
