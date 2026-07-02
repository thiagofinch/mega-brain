# Workflow: New Deliverable Request

> Fluxo acionado quando copy/estratégia sugere entregaveis novos que são aprovados pelo usuario.
> Roteia demanda para infoproduct-creation squad com briefing estruturado.

## Configuration

```yaml
workflow:
  name: new-deliverable-request
  type: trigger
  estimated_time: "15-30min"
  triggers:
    - "Copy sugeriu bonus/entregavel novo e usuario aprovou"
    - "Estrategia identificou gap de produto que precisa ser criado"
    - "Oferta precisa de entregavel que nao existe ainda"
  source_squads:
    - copywriting
    - agora-direct-response
    - funnel-creator
  target_squad: infoproduct-creation
```

---

## Quando Acionar

Este workflow e acionado quando:

1. **Stage 0** de qualquer workflow (copywriting ou agora) identifica que a copy/estratégia sugere entregaveis marcados como `[NOVO - REQUER APROVACAO]`
2. O **usuario aprova** a criação do novo entregavel
3. O squad de origem envia a demanda para o orquestrador rotear

### Sinais de Acionamento

| Sinal | Exemplo |
|-------|---------|
| Copy sugere bônus novo | "Bônus: Checklist de 30 dias [NOVO - REQUER APROVACAO]" |
| Estratégia identifica gap | "Product Pyramid gap: falta produto de R$97 front-end" |
| Oferta precisa de material | "Order bump precisa de ebook complementar" |
| Usuario pede entregavel | "Quero adicionar um módulo sobre X ao curso" |

---

## Stage 1: Validacao da Demanda

**Agent**: roteador (orquestrador-global)

```yaml
inputs:
  - source_squad (quem originou a demanda)
  - deliverable_description (o que precisa ser criado)
  - deliverable_type (bonus | modulo | material | curso | ebook | checklist | template | outro)
  - target_product (produto ao qual sera vinculado)
  - priority (alta | media | baixa)
  - context (por que foi sugerido, qual copy/estrategia motivou)
  - approval_status (aprovado_pelo_usuario: true)

actions:
  - Validar que o entregavel NAO existe (checar hotmart-offers.yaml)
  - Confirmar que o usuario realmente aprovou
  - Classificar tipo e complexidade

outputs:
  - validated_request
  - complexity_assessment (simples | medio | complexo)

gate: "Entregavel confirmado como inexistente E aprovado pelo usuario?"
```

---

## Stage 2: Briefing Estruturado

**Agent**: roteador (orquestrador-global)

```yaml
inputs:
  - validated_request (from Stage 1)
  - offer_data (do Stage 0 do workflow de origem)

actions:
  - Montar briefing estruturado para infoproduct-creation
  - Incluir contexto completo (produto-pai, publico, oferta atual)
  - Definir criterios de aceite
  - Definir deadline (se aplicavel)

outputs:
  - deliverable_briefing:
      titulo: "[nome do entregavel]"
      tipo: "[bonus | modulo | material | ebook | checklist | template]"
      produto_pai: "[nome do produto principal]"
      descricao: "[o que deve conter]"
      publico_alvo: "[para quem]"
      contexto_copy: "[por que foi sugerido — qual copy/estrategia motivou]"
      criterios_aceite:
        - "[criterio 1]"
        - "[criterio 2]"
      deadline: "[data se aplicavel]"
      prioridade: "[alta | media | baixa]"
      squad_origem: "[copywriting | agora-direct-response | funnel-creator]"
```

---

## Stage 3: Roteamento para infoproduct-creation

**Agent**: roteador (orquestrador-global)

```yaml
actions:
  - Rotear demanda para @infoproduct-creation
  - Entregar deliverable_briefing como input
  - Se complexidade = simples: acionar task especifica (*criar-material)
  - Se complexidade = medio/complexo: acionar workflow completo (*criar-infoproduto)
  - Registrar demanda no ClickUp (se habilitado)

routing_rules:
  simples:
    description: "Checklist, template, PDF, ebook curto"
    action: "@infoproduct-creation *criar-material --briefing {deliverable_briefing}"
  medio:
    description: "Modulo de curso, bonus com video, material extenso"
    action: "@infoproduct-creation *estruturar --briefing {deliverable_briefing}"
  complexo:
    description: "Curso completo, novo produto, conteudo extenso"
    action: "@infoproduct-creation *criar-infoproduto --briefing {deliverable_briefing}"

outputs:
  - routing_confirmation
  - clickup_task_id (se criado)
```

---

## Stage 4: Notificação ao Squad de Origem

**Agent**: roteador (orquestrador-global)

```yaml
actions:
  - Notificar squad de origem que a demanda foi roteada
  - Informar prazo estimado
  - Recomendar prosseguir com copy usando placeholder para o entregavel
  - Marcar entregavel como [EM PRODUCAO] na copy

notification_template: |
  Demanda roteada para infoproduct-creation:
  - Entregavel: {titulo}
  - Tipo: {tipo}
  - Complexidade: {complexidade}
  - Status: EM PRODUCAO

  Recomendacao: Prossiga com a copy usando placeholder.
  O entregavel sera integrado quando finalizado.
```

---

## Integracao com ClickUp (Opcional)

```yaml
clickup_integration:
  enabled: true
  space: "MISSION CONTROL"
  list: "Demandas Infoproduto"
  task_template:
    name: "[INFOPRODUTO] {titulo}"
    description: "{deliverable_briefing}"
    priority: "{prioridade}"
    tags: ["infoproduto", "novo-entregavel", "{squad_origem}"]
    custom_fields:
      produto_pai: "{produto_pai}"
      tipo_entregavel: "{tipo}"
      complexidade: "{complexidade}"
```

---

## Stage 5: Entregavel Final

Quando infoproduct-creation finaliza:

```yaml
agent: roteador (orquestrador-global)

inputs:
  - deliverable_output (arquivo/arquivo(s) entregues)
  - completion_report (resumo do que foi criado)
  - product_id (hotmart offer ID)

actions:
  - Validar qualidade do entregavel contra criterios de aceite
  - Atualizar hotmart-offers.yaml com novo entregavel
  - Notificar squad de origem que o entregavel esta pronto
  - Atualizar copy/oferta se necessario (replace placeholders [EM PRODUCAO] com referencia real)
  - Registrar no SuperMemory (containerTag: "megabrain-master") como completed
  - Registrar na execução log (.data/executions/) com status final

outputs:
  - final_deliverable_record
  - updated_offer_reference
  - completion_timestamp

callback:
  post_delivery:
    - Archivar task no ClickUp como "Done"
    - Adicionar comment com path final do entregavel
    - Log de auditoria com timestamp de conclusao
    - Sugerir atualizacoes na landing page se houver placeholders
```

---

## Arquitetura e Dependências

### Fluxo de Fases (Sequencial)

```
┌─────────────────────────────────────────────────────────────────┐
│ TRIGGER: Copy/Strategy sugere novo entregavel                   │
│ Entrada: User aprova + Squad de origem envia demanda            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: Validacao da Demanda [Orquestrador]                    │
│ Gate: "Entregavel inexistente + Usuario aprovou?"               │
│ Saida: validated_request + complexity_assessment                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: Briefing Estruturado [Orquestrador]                    │
│ Gate: "Briefing montar completo com todos dados contextuais?"   │
│ Saida: deliverable_briefing                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: Roteamento [Orquestrador → Infoproduct-Creation]       │
│ Gate: "Roteamento confirmado + Task criado?"                    │
│ Saida: routing_confirmation + clickup_task_id                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: Notificacao [Orquestrador → Squad Origem]              │
│ Gate: "Squad informado + Recomendacoes repassadas?"             │
│ Saida: notification_sent                                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ├─── EXECUCAO EM PARALELO ───┐
                           │  (Infoproduct cria)        │
                           │                            │
                           ▼                            ▼
              ┌──────────────────────┬─────────────────────────┐
              │ Infoproduct-Creation │  Squad Origem (em hold)  │
              │ cria o entregavel    │ Continua com copy      │
              │ usando placeholders  │ usando [EM PRODUCAO]   │
              │                      │                        │
              │ ~5-20 dias           │ ~2-3 dias              │
              └──────────────┬──────┘ └─────────────────────────┘
                             │
                             ▼
              ┌─────────────────────────────────────┐
              │ STAGE 5: Entregavel Final            │
              │ Orquestrador recebe + Integra       │
              │ Gate: "Qualidade validada?"         │
              │ Saida: final_deliverable_record     │
              └──────────────────────────────────────┘

Dependencias Criticas:
- Stage 2 DEPENDE de Stage 1 (nao validar = nao brief)
- Stage 3 DEPENDE de Stage 2 (nao brief = nao roteamento)
- Stage 4 NAO depende de Stage 3 (pode notificar em paralelo)
- Stage 5 NAO depende de Stage 4 (notificacao nao bloqueia entrega)
```

---

## Critérios de Sucesso por Fase

| Fase | Critério Mensuravel | Evidência |
|------|-------------------|-----------|
| **Stage 1** | Validacao confirmada e complexidade classificada | validated_request.status = "approved" |
| **Stage 2** | Briefing montar com mínimo 8 campos preenchidos | deliverable_briefing tem: título, tipo, descrição, público, critérios, deadline, squad_origem |
| **Stage 3** | Task criado no ClickUp com tags corretas | clickup_task_id != null, tags contem "infoproduto" + squad_origem |
| **Stage 4** | Notificação enviada ao squad de origem | notification_sent.status = "delivered", squad recebeu briefing |
| **Stage 5** | Entregavel validado contra AC e integrado | final_deliverable_record.status = "integrated", hotmart_offers.yaml atualizado |

---

## Gestão de Riscos por Fase

### Riscos Stage 1-2 (Validacao + Briefing)

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|--------|-----------|
| **Entregavel já existe** (discoverta late) | MEDIA | ALTO | Checklist explícito: hotmart-offers.yaml + search na base |
| **Contexto incompleto** (squad origem não informa direito) | MEDIA | MÉDIO | Template de briefing obrigatório com 8 campos |
| **User aprova mas muda ideia** (contradição depois) | BAIXA | MÉDIO | Registrar aprovação com timestamp no ClickUp |
| **Complexidade mal classificada** | MEDIA | ALTO | Segunda validação por @infoproduct-creation chief antes de aceitar |

### Riscos Stage 3 (Roteamento)

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|--------|-----------|
| **Infoproduct-creation não tem capacidade** (backlog cheio) | MEDIA | ALTO | Negociar prazo/escopo ANTES de rotear (Stage 2.5) |
| **Briefing incompleto chegou** | BAIXA | ALTO | Validacao obrigatória antes de criar task |
| **Task criado mas não assignado** | BAIXA | MÉDIO | Atribuir automaticamente a @infoproduct chief no ClickUp |
| **Routing duplicado** (mesma demanda enviada 2x) | BAIXA | MÉDIO | Check de duplicatas por hash(título + produto) |

### Riscos Stage 4-5 (Execucao + Entrega)

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|--------|-----------|
| **Entregavel não atinge critérios AC** | MEDIA | ALTO | Quality gate mandatorio: 100% de AC atendidos antes de liberar |
| **Squad origem esquece do placeholder** | MEDIA | MÉDIO | Reminder automatico a cada 3 dias enquanto em [EM PRODUÇÃO] |
| **Integração com hotmart-offers.yaml falha** | BAIXA | ALTO | Validação de schema YAML antes de atualizar |
| **Copy desatualizada** (referência errada no placeholder) | MEDIA | MÉDIO | Orquestrador revisa copy antes de dar approve final |
| **Perda de comunicação** com squad origem | BAIXA | MÉDIO | Telegram/WhatsApp notification além de ClickUp |

---

## Procedimentos de Rollback

### Rollback Stage 1 → Rejeitar Demanda

**Quando:** Validacao falha (entregavel já existe, user não aprovou, contexto errado)

```yaml
actions:
  1. Informar squad origem que demanda foi rejeitada
  2. Explicar motivo (qual validacao falhou)
  3. Se aplicavel: sugerir alternativas (usar entregavel existente em vez de criar novo)
  4. Registrar rejeição no SuperMemory
```

### Rollback Stage 2 → Redefinir Briefing

**Quando:** Briefing incompleto ou ambíguo, infoproduct-creation não consegue entender

```yaml
actions:
  1. Pedir ao squad origem clarificacoes especificas
  2. Atualizar briefing_v2 com novas informacoes
  3. Validar novamente antes de rotear
  4. Não enviar tarefa até briefing estar 100% claro
```

### Rollback Stage 3 → Pausar Roteamento

**Quando:** Infoproduct-creation comunicou que está no teto de capacidade

```yaml
actions:
  1. Criar task no ClickUp mas marcar como "Backlog" (nao "In Progress")
  2. Notificar squad origem que entregavel foi enfileirado
  3. Fornecer prazo estimado de quando sera acionado
  4. Colocar na fila de espera (enqueue para proxima capac.slot)
```

### Rollback Stage 5 → Rejeitar Entregavel

**Quando:** QA encontra falhas contra critérios de aceite

```yaml
actions:
  1. Marcar task no ClickUp como "Awaiting Approval" (nao Done)
  2. Adicionar comment com lista detalhada de falhas
  3. Devolver para infoproduct-creation com instrucoes de correcao
  4. NAO atualizar hotmart-offers.yaml ate passar QA
  5. Registrar tempo de rework no task (impacto no prazo)
```

---

## Arvore de Decisão

### Decisão Crítica #1: Complexidade do Entregavel

```
┌─ VALIDACAO INICIAL ─────────────────────────────────┐
│                                                     │
│  Entregavel: ?                                      │
│                                                     │
│  ┌─ SIMPLES ────────────────────────────────┐      │
│  │ (Checklist, template, PDF < 20 páginas)  │      │
│  │                                           │      │
│  │ Briefing: 4-5 campos suficientes         │      │
│  │ Action: @infoproduct *criar-material    │      │
│  │ Prazo: 3-5 dias                          │      │
│  │ ClickUp: Prioridade NORMAL               │      │
│  └─────────────────────────────────────────┘      │
│         │                                          │
│         ├─ MEDIO ─────────────────────────┐        │
│         │ (Modulo, bonus com video,      │        │
│         │  material 20-50 págs)          │        │
│         │                                 │        │
│         │ Briefing: 6-7 campos completos │        │
│         │ Action: @infoproduct           │        │
│         │         *estruturar            │        │
│         │ Prazo: 7-15 dias               │        │
│         │ ClickUp: Prioridade NORMAL     │        │
│         └─────────────────────────────────┘        │
│                  │                                 │
│                  └─ COMPLEXO ──────────────┐      │
│                     (Curso completo,       │      │
│                      novo produto,         │      │
│                      > 50 páginas)         │      │
│                                            │      │
│                     Briefing: 8 campos     │      │
│                     Action: @infoproduct  │      │
│                             *criar-infop  │      │
│                     Prazo: 20-30 dias     │      │
│                     ClickUp: Prioridade   │      │
│                             ALTA          │      │
│                     Escalate: Chief       │      │
│                     review antes de       │      │
│                     aceitar               │      │
│                     └──────────────────────┘      │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Decisão Crítica #2: Product Fit (Entregavel Existe?)

```
┌─ CHECAGEM DE EXISTENCIA ──────────────────────┐
│                                               │
│  hotmart-offers.yaml + local search           │
│  + SuperMemory recall: "produto similar?"     │
│                                               │
│  ┌─ SIM, EXISTE ────────────────┐            │
│  │ Action: REJEITAR              │            │
│  │ Motivo: "Entregavel duplicado"│            │
│  │ Sugestão: Usar versão        │            │
│  │           existente em vez de │            │
│  │           criar novo          │            │
│  │ Registrar em execução log     │            │
│  └──────────────────────────────┘            │
│         │                                     │
│         └─ NAO, E NOVO ──────────┐           │
│            Prosseguir para       │           │
│            Stage 2: Briefing     │           │
│            └────────────────────┘           │
│                                             │
└─────────────────────────────────────────────┘
```

### Decisão Crítica #3: Capacidade do Infoproduct Squad

```
┌─ VERIFICACAO DE CAPACIDADE ─────────────────┐
│ (Feito no Stage 2, antes de rotear)         │
│                                             │
│ infoproduct-creation chief comunica:        │
│ "Temos capacidade agora?"                   │
│                                             │
│ ┌─ SIM ──────────────────────────┐         │
│ │ Prosseguir normalmente          │         │
│ │ Stage 3: Rotear com prazo OK   │         │
│ └─────────────────────────────────┘         │
│         │                                    │
│         └─ NAO ──────────────┐              │
│            Opções:           │              │
│                              │              │
│            A) PAUSAR          │              │
│               Backlog a       │              │
│               demanda, com    │              │
│               data estimada   │              │
│               de quando sera  │              │
│               possível        │              │
│                              │              │
│            B) DESCARTAR      │              │
│               Se nao ha      │              │
│               prioridade     │              │
│               critica, pode  │              │
│               nao fazer agora│              │
│                              │              │
│            Registrar decisao │              │
│            no ClickUp + Notify │           │
│            squad origem      │              │
│            └──────────────────┘             │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Estimativas de Tempo e Custo

### Tempo Total por Complexidade

| Complexidade | Stage 1-4 | Stage 5 (Entrega) | **TOTAL** | Prazo Start-to-Finish |
|---|---|---|---|---|
| **SIMPLES** | 1-2h | 3-5 dias | 3-5 dias | 2-3h + 3-5 dias |
| **MÉDIO** | 2-3h | 7-15 dias | 7-15 dias | 3h + 1-2 semanas |
| **COMPLEXO** | 3-5h | 20-30 dias | 20-30 dias | 5h + 3-4 semanas |

### Custo em Tokens (Claude API)

Estimativa por fase (valores em millares de tokens):

| Fase | Simples | Médio | Complexo |
|------|---------|-------|----------|
| Stage 1 (Validacao) | 2-3k | 3-4k | 4-5k |
| Stage 2 (Briefing) | 3-4k | 5-6k | 6-8k |
| Stage 3 (Roteamento) | 1-2k | 2-3k | 3-4k |
| Stage 4 (Notificação) | 1-2k | 2-3k | 3-4k |
| **Orquestrador Total** | **7-11k** | **12-16k** | **16-21k** |
| Infoproduct-Creation | **30-50k** | **80-150k** | **200-350k** |
| **GRAND TOTAL** | **37-61k** | **92-166k** | **216-371k** |

> Nota: Valores são estimativas. Custo real depende de quantas iteracoes de feedback/rework acontecem.

### Checkpoints e Validacoes Obrigatorias

| Checkpoint | Quando | Validacao |
|-----------|--------|-----------|
| **CP1: Entregavel Inexistente** | Fim Stage 1 | hotmart-offers.yaml query + SuperMemory recall |
| **CP2: User Approved** | Fim Stage 1 | approval_status.user_confirmed == true |
| **CP3: Briefing Completo** | Fim Stage 2 | 8 campos preenchidos, nenhum null |
| **CP4: Task Criado** | Fim Stage 3 | clickup_task_id != null, assignado, tags OK |
| **CP5: Squad Notificado** | Fim Stage 4 | notification.delivered == true, WhatsApp sent |
| **CP6: QA Passed** | Antes Stage 5 | 100% de critérios de aceite atendidos |
| **CP7: Integrado** | Fim Stage 5 | hotmart_offers.yaml actualizado, SuperMemory logged |

---

## Handoffs e Transicoes Entre Squads

### Handoff 1: Squad Origem → Orquestrador

```yaml
momento: Quando copy/strategy aprova novo entregavel
quem_inicia: Squad de origem (copywriting, agora, funnel-creator)
quem_recebe: Orquestrador (roteador agent)

inputs_entregues:
  - source_squad (identificacao do squad)
  - deliverable_description (descricao clara)
  - deliverable_type (bonus|modulo|material|curso|ebook|checklist|template|outro)
  - target_product (qual produto pai)
  - priority (alta|media|baixa)
  - context (por que foi sugerido)
  - approval_status (confirmado usuario aprovou?)
  - sugestao_prazo (se houver deadline)

canal_comunicacao: ClickUp task + WhatsApp notification
criterio_aceite: Roteador confirma recebimento e agenda Stage 1

pos_handoff: Squad origem entra em hold, prossegue com placeholder [EM PRODUCAO]
```

### Handoff 2: Orquestrador → Infoproduct-Creation

```yaml
momento: Quando briefing foi validado (fim Stage 2)
quem_inicia: Orquestrador (roteador agent)
quem_recebe: Infoproduct-Creation Squad (chief + specialized agents)

inputs_entregues:
  - deliverable_briefing (estruturado com 8 campos)
  - complexity_assessment (simples|medio|complexo)
  - clickup_task_id (task aberto)
  - product_context (dados do produto pai)
  - squad_origem (quem originou)
  - deadline (se aplicavel)

canal_comunicacao: ClickUp task + @infoproduct-creation command
criterio_aceite: Infoproduct chief aceita task, muda para "In Progress"

pos_handoff: Infoproduct comeca trabalho, entra em loop de execucao
checkpoint: Weekly updates no ClickUp ate conclusao
```

### Handoff 3: Infoproduct-Creation → Orquestrador (Entrega)

```yaml
momento: Quando entregavel foi finalizado
quem_inicia: Infoproduct-Creation Squad
quem_recebe: Orquestrador (QA + Integration)

outputs_entregues:
  - deliverable_files (arquivo(s) principal(is))
  - completion_report (resumo do que foi criado)
  - asset_list (lista de assets usados)
  - qa_self_check (checklist de AC auto-validacao)
  - product_id (ID hotmart da oferta parent, se aplicavel)

canal_comunicacao: ClickUp task (muda para "Review") + entrega de arquivos
criterio_aceite: Orquestrador valida contra AC, aprova ou rejeita

pos_handoff: Se aprovado → Stage 5; Se rejeitado → Rework loop
```

### Handoff 4: Orquestrador → Squad Origem (Notificação Final)

```yaml
momento: Quando entregavel foi validado e integrado
quem_inicia: Orquestrador
quem_recebe: Squad de origem

comunicacao:
  canal: WhatsApp + ClickUp comment
  mensagem: |
    Entregavel pronto: {titulo}
    Local: {file_path}
    Hotmart: {offer_reference}
    Você pode agora atualizar sua copy
    (remover placeholder [EM PRODUCAO])

actions_required: Atualizar copy, testar integracao, Deploy
```

---

## Integracao com Sistemas Externos

### ClickUp Integration Detalhada

```yaml
list_id: "CLICKUP_ID"  # Infoproduct Demands
task_fields:
  name: "[INFOPRODUTO] {titulo_entregavel}"
  description: |
    {deliverable_briefing em formato legivel}

    **Squad Origem:** {squad_origem}
    **Produto Pai:** {target_product}
    **Tipo:** {deliverable_type}
    **Complexidade:** {complexity_assessment}
    **Deadline:** {deadline_if_applicable}

  custom_fields:
    squad_origem: "{copywriting|agora-direct-response|funnel-creator}"
    tipo_entregavel: "{bonus|modulo|material|curso|ebook|checklist|template|outro}"
    complexidade: "{simples|medio|complexo}"
    produto_pai: "{product_name}"
    status_entrega: "{em_espera|em_producao|em_revisao|entregue|rejeitado}"

  tags: ["infoproduto", "novo-entregavel", "{squad_origem}", "workflow:new-deliverable"]
  priority: "3"  # Normal por padrao, elevar se complexidade COMPLEXO
  assignee: "infoproduct-creation-chief"
  due_date: "{calculated_deadline}"

automated_status_updates:
  Stage1_Approved: "In Progress" (orquestrador iniciou validacao)
  Stage2_Ready: "In Progress" (briefing pronto para rotear)
  Stage3_Routed: "In Progress" (task aceito por infoproduct)
  Stage5_Completed: "Done" (entregavel validado e integrado)
  Rejected: "Awaiting Approval" (voltar para rework)
```

### SuperMemory Integration

```yaml
containerTag: "megabrain-master"
tipo_memoria: "execution_log"
apos_cada_stage:
  - Registrar: {stage_numero, status, timestamp, agentes_envolvidos}
  - Exemplo: "Stage 2: Briefing estruturado para entregavel 'Checklist 30 Dias' do produto MPG"

apos_conclusao:
  - Registrar completo: { deliverable_id, tipo, produto_pai, squad_origem, prazo_total, status_final}
  - Tags: [infoproduto, {squad_origem}, {deliverable_type}, completed]
  - Enable para future recalls: "Entregavel similar para {produto}?"
```

---

## Referências e Linking

Este workflow é parte do ecossistema orquestrador:

- **Workflow relacionado:** `full-funnel-pipeline.md` (quando entregavel e integrado em oferta completa)
- **Squad destino:** `squads/infoproduct-creation/`
- **Config orquestrador:** `squads/orquestrador-global/config.yaml`
- **Data sources:** `.data/clients/hotmart-offers.yaml`
- **Execution logs:** `.data/executions/{YYYY-MM-DD}_new-deliverable-{slug}/`
- **ClickUp namespace:** "MISSION CONTROL" space, "Demandas Infoproduto" list
- **Memory system:** `.claude/rules/memory-system.md` (execution logging)

## MEGABRAIN Deep Validation

- Last run: `20260514-validate-deep`
- Validator: `mega-brain/megabrain-chief`
- Mode: `deep`
- Workflow ID: `new-deliverable-request`
- Status: `pass`
- External execution: not performed during structural validation.
