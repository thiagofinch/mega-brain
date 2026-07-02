---
task: processar-solicitacao
name: 'Task: Processar Solicitação'
version: "3.1.1"
category: operations
difficulty: intermediate
responsavel: '@intent-parser'
responsavel_type: Agent
atomic_layer: Molecule
elicit: false
estimated_time: 30-60min
model: sonnet
Entrada:
- campo: brief
  tipo: markdown
  obrigatorio: true
  default: null
Saida:
- campo: deliverable
  tipo: markdown
pre_condition: User request payload received with text and optional context/priority
post_condition: Request classified, target squad selected, and routing dispatch emitted to executor
performance:
  error_handling: graceful with fallback + retry
domain: tactical
task_id: processar-solicitacao
squad: orquestrador-global
status: ready
execution_type: hybrid
orchestration_boundary:
  live_routing_performed: false
  external_dispatch_performed: false
  workspace_write_performed: false
megabrain_validation:
  last_run: "20260514-validate-deep"
  validated_at: "2026-05-15T00:00:00Z"
  validator: mega-brain/megabrain-chief
  mode: deep
  squad: orquestrador-global
  status: pass
  evidence:
    - schema_contract_normalized
    - task_boundary_declared
    - plan_only_orchestration_preserved
---

# Task: Processar Solicitação

## Metadata
```yaml
id: processar-solicitacao
name: Processar Solicitação do Usuário
version: 1.0.0
executor: classificador-intencao
workflow: processar-solicitacao
estimated_time: 3-10s
```

## Purpose

Receber uma solicitação do usuário/sistema, classificar a intenção, encontrar o squad mais adequado e rotear para execução.

---

## Input Requirements

| Campo | Tipo | Obrigatório | Exemplo |
|-------|------|-------------|---------|
| solicitacao | string | Sim | "Criar posts para Instagram sobre massagem" |
| contexto_usuario | object | Não | {nome: "X", squad_anterior: "Y"} |
| prioridade | string | Não | "normal" / "urgente" |

## Trigger

```yaml
trigger:
  type: automatic
  event: "Nova solicitação recebida"
  sources:
    - "Input do usuário"
    - "Sistema externo"
    - "Outro squad"
```

---

## Execution Flow

### Fase 1: Classificação (1-2s)

**Task 1.1: Classificar Intenção**
- Executor: @classificador-intencao
- Input: solicitação, contexto_usuario
- Output: intenção estruturada
- Tempo: ~1s

```yaml
output_intencao:
  dominio: "marketing | vendas | operacional | ..."
  tipo_tarefa: "criar | analisar | executar | ..."
  complexidade: "baixa | media | alta"
  urgencia: "baixa | normal | alta | critica"
  palavras_chave: ["keyword1", "keyword2"]
  confianca: 0.XX
  resumo: "Resumo da solicitação"
```

### Fase 2: Matching (1-2s)

**Task 2.1: Consultar Índice**
- Executor: @indexador-squads
- Input: intenção.dominio, intenção.palavras_chave
- Output: squads candidatos

**Task 2.2: Calcular Scores**
- Executor: @roteador
- Input: intenção, squad_registry
- Output: scores de compatibilidade

```yaml
algoritmo_scoring:
  dominio: 40%
  problemas: 35%
  tipo_tarefa: 15%
  keywords: 10%
```

### Fase 3: Decisão (1-2s)

**Task 3.1: Decidir Roteamento**
- Executor: @roteador
- Input: scores calculados
- Output: decisão de roteamento

```yaml
thresholds:
  rotear_direto: ">= 0.80"
  confirmar_humano: "0.60 - 0.79"
  escalar: "< 0.60"
```

### Fase 4: Execução

**Cenário A: Roteamento Direto (Score >= 0.80)**
```yaml
acao: rotear
destino: squad_mais_compativel
agente: agente_sugerido
notificar: false
```

**Cenário B: Confirmação Necessária (Score 0.60-0.79)**
```yaml
acao: confirmar
opcoes:
  - squad_1
  - squad_2
  - criar_novo
aguardar: decisao_humana
```

**Cenário C: Escalar/Criar (Score < 0.60)**
```yaml
acao: escalar | criar_squad
verificar: demanda_recorrente
gerar: briefing_para_arquiteto
```

---

## Output Structure

```yaml
resultado:
  status: "roteado | aguardando_confirmacao | escalado | criando_squad"

  # Se roteado
  destino:
    squad: "nome-do-squad"
    agente: "nome-do-agente"
    confianca: 0.XX

  # Se aguardando confirmação
  opcoes:
    - squad: "squad-1"
      score: 0.XX
      justificativa: "..."
    - squad: "squad-2"
      score: 0.XX
      justificativa: "..."

  # Se escalado/criando
  motivo: "Score baixo, nenhum squad adequado"
  briefing: {objeto se criar_squad}

  # Sempre
  tempo_processamento: "Xs"
  intencao_classificada: {objeto}
```

---

## Quality Gates

### Gate 1: Classificação
- [ ] Domínio identificado (não "desconhecido")
- [ ] Confiança >= 0.70
- [ ] Palavras-chave extraídas (>= 2)

### Gate 2: Matching
- [ ] Todos os squads foram avaliados
- [ ] Scores calculados corretamente
- [ ] Breakdown disponível

### Gate 3: Decisão
- [ ] Threshold correto aplicado
- [ ] Justificativa clara
- [ ] Agente sugerido é adequado

### Gate 4: Execução
- [ ] Solicitação chegou ao destino
- [ ] Contexto preservado
- [ ] Log registrado

---

## Success Metrics

| Métrica | Alvo | Descrição |
|---------|------|-----------|
| Tempo total | < 3s | Classificação + matching + decisão |
| Taxa roteamento direto | > 80% | Sem intervenção humana |
| Precisão | > 90% | Roteamentos corretos |
| Taxa escalação | < 5% | Solicitações escaladas |

---

## Rollback Points

```yaml
rollback:
  classificacao_falha:
    acao: "Pedir reformulação ao usuário"
    mensagem: "Não consegui entender a solicitação. Pode reformular?"

  score_muito_baixo:
    acao: "Apresentar opções genéricas"
    mensagem: "Não encontrei squad específico. Escolha uma opção:"

  squad_indisponivel:
    acao: "Sugerir alternativa"
    mensagem: "Squad preferido não disponível. Alternativa: X"
```

---

## Example

### Input
```yaml
solicitacao: "Preciso criar posts para o Instagram da clínica sobre massagem relaxante"
contexto_usuario:
  nome: "um cliente"
  empresa: "Clínica de um nicho de saúde"
```

### Processing
```yaml
# Fase 1: Classificação
intencao:
  dominio: "marketing"
  tipo_tarefa: "criar"
  complexidade: "media"
  urgencia: "normal"
  palavras_chave: ["posts", "instagram", "massagem", "relaxante"]
  confianca: 0.92
  resumo: "Criar conteúdo para Instagram sobre massagem relaxante"

# Fase 2: Matching
matches:
  - squad: "content-ecosystem"
    score: 0.89
    breakdown:
      dominio: 0.95
      problemas: 0.85
      tipo_tarefa: 0.90
      keywords: 0.80

# Fase 3: Decisão
decisao:
  acao: "rotear"
  squad_destino: "content-ecosystem"
  agente_sugerido: "copywriter"
  confianca: 0.89
  justificativa: "Squad especializado em conteúdo educativo e distribuição"
```

### Output
```yaml
resultado:
  status: "roteado"
  destino:
    squad: "content-ecosystem"
    agente: "copywriter"
    confianca: 0.89
  tempo_processamento: "1.8s"
  intencao_classificada: {...}
```

## Integration

- **Squad:** orquestrador-global
- **Upstream:** *definir tasks que alimentam esta*
- **Downstream:** *definir tasks que esta alimenta*
