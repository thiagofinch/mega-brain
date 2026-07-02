# Checklist: Qualidade de Roteamento

## Metadata
```yaml
id: roteamento-checklist
name: Checklist de Qualidade de Roteamento
version: 1.0.0
executor: roteador
related_task: processar-solicitacao
```

## Purpose

Garantir que cada decisão de roteamento é precisa, fundamentada e adequada ao contexto da solicitação.

---

## Fase 1: Classificação de Intenção

| # | Check | Status | Notas |
|---|-------|--------|-------|
| 1 | Domínio identificado (não "desconhecido")? | [ ] | Domínio: ___ |
| 2 | Tipo de tarefa claro? | [ ] | Tipo: ___ |
| 3 | Complexidade avaliada? | [ ] | Complexidade: ___ |
| 4 | Urgência determinada? | [ ] | Urgência: ___ |
| 5 | Palavras-chave extraídas (>= 2)? | [ ] | Total: ___ |
| 6 | Confiança >= 0.70? | [ ] | Confiança: ___ |
| 7 | Resumo captura essência? | [ ] | |

**Score Classificação:** ___/7

---

## Fase 2: Cálculo de Scores

| # | Check | Status |
|---|-------|--------|
| 8 | Todos os squads foram avaliados? | [ ] |
| 9 | Score de domínio calculado (40%)? | [ ] |
| 10 | Score de problemas calculado (35%)? | [ ] |
| 11 | Score de tipo de tarefa calculado (15%)? | [ ] |
| 12 | Score de keywords calculado (10%)? | [ ] |
| 13 | Score final correto (soma ponderada)? | [ ] |
| 14 | Breakdown disponível para top matches? | [ ] |

**Scores Calculados:**

| Squad | Domínio | Problemas | Tipo | Keywords | Final |
|-------|---------|-----------|------|----------|-------|
| ___ | ___% | ___% | ___% | ___% | ___ |
| ___ | ___% | ___% | ___% | ___% | ___ |
| ___ | ___% | ___% | ___% | ___% | ___ |

**Score Cálculo:** ___/7

---

## Fase 3: Aplicação de Thresholds

| # | Check | Status |
|---|-------|--------|
| 15 | Melhor score identificado? | [ ] |
| 16 | Threshold correto aplicado? | [ ] |
| 17 | Decisão consistente com threshold? | [ ] |

**Verificação de Threshold:**

| Score | Threshold | Ação Esperada | Ação Tomada | OK? |
|-------|-----------|---------------|-------------|-----|
| ___ | >= 0.80 | Rotear direto | ___ | [ ] |
| ___ | 0.60-0.79 | Confirmar | ___ | [ ] |
| ___ | < 0.60 | Escalar | ___ | [ ] |

**Score Thresholds:** ___/3

---

## Fase 4: Qualidade da Decisão

### Se Roteamento Direto
| # | Check | Status |
|---|-------|--------|
| 18 | Squad destino mais adequado? | [ ] |
| 19 | Agente sugerido correto para tipo de tarefa? | [ ] |
| 20 | Confiança >= 0.80? | [ ] |
| 21 | Justificativa clara e fundamentada? | [ ] |

### Se Confirmação Necessária
| # | Check | Status |
|---|-------|--------|
| 22 | Múltiplas opções apresentadas (2-3)? | [ ] |
| 23 | Scores das opções informados? | [ ] |
| 24 | Justificativas por opção? | [ ] |
| 25 | Recomendação incluída? | [ ] |

### Se Escalar/Criar Squad
| # | Check | Status |
|---|-------|--------|
| 26 | Motivo da escalação claro? | [ ] |
| 27 | Gap identificado? | [ ] |
| 28 | Briefing completo (se criar)? | [ ] |
| 29 | Verificado se demanda é recorrente? | [ ] |

**Score Decisão:** ___/4-6

---

## Fase 5: Execução

| # | Check | Status |
|---|-------|--------|
| 30 | Solicitação entregue ao destino? | [ ] |
| 31 | Contexto preservado? | [ ] |
| 32 | Tempo de processamento < 3s? | [ ] |
| 33 | Log de decisão registrado? | [ ] |

**Score Execução:** ___/4

---

## Scoring Final

```
Itens aplicáveis: ___
Itens completados: ___
Porcentagem: ___%

Qualidade do Roteamento:
[ ] EXCELENTE (>90%) - Decisão precisa
[ ] BOM (80-90%) - Pequenos ajustes
[ ] REGULAR (70-80%) - Revisar processo
[ ] FRACO (<70%) - Investigar falha
```

---

## Quick Reference

### Algoritmo de Scoring

| Componente | Peso | Descrição |
|------------|------|-----------|
| Domínio | 40% | Match entre domínio da intenção e do squad |
| Problemas | 35% | Relevância dos problemas que o squad resolve |
| Tipo de Tarefa | 15% | Capacidade do agente para o tipo de tarefa |
| Keywords | 10% | Palavras-chave em comum |

### Thresholds de Decisão

| Score | Ação | Descrição |
|-------|------|-----------|
| >= 0.80 | Rotear | Alta confiança, sem intervenção |
| 0.60-0.79 | Confirmar | Apresentar opções ao humano |
| < 0.60 | Escalar | Humano decide ou criar squad |

### Cálculo do Score de Domínio

| Match | Score |
|-------|-------|
| Exato | 1.0 |
| Relacionado | 0.7 |
| Parcialmente relacionado | 0.3 |
| Sem relação | 0.0 |

### Red Flags

| ❌ Situação | Ação |
|-------------|------|
| Domínio "desconhecido" | Escalar imediatamente |
| Confiança < 0.50 | Pedir reformulação |
| Scores muito próximos (<0.05) | Confirmar mesmo se alto |
| Múltiplos squads empatados | Apresentar opções |
| Capacidade especial necessária | Verificar se squad tem |

### Logs Obrigatórios

```yaml
log_roteamento:
  timestamp: "YYYY-MM-DD HH:MM:SS"
  solicitacao_id: "uuid"
  intencao:
    dominio: "..."
    confianca: 0.XX
  decisao:
    acao: "rotear|confirmar|escalar"
    destino: "squad-nome"
    score: 0.XX
  tempo_ms: XXX
```
