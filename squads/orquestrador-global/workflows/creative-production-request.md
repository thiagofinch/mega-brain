# Workflow: Creative Production Request

> Fluxo para squads que precisam de producao de criativos visuais.
> Roteia demanda para creative-studio com briefing estruturado.

## Configuration

```yaml
workflow:
  name: creative-production-request
  type: trigger
  estimated_time: "10-20min (roteamento) + tempo de producao"
  triggers:
    - "Squad precisa de criativos visuais produzidos (imagens, banners, ads)"
    - "Traffic-squad precisa de assets visuais alem de hooks/briefs/DSL"
    - "Qualquer squad precisa de design/criativo visual"
  source_squads:
    - traffic-squad
    - media-buy
    - funnel-creator
    - copywriting
    - content-ecosystem
  target_squad: creative-studio
```

---

## Quando Acionar

Este workflow e acionado quando um squad precisa de **producao visual** que vai alem de texto/copy.

### traffic-squad (caso principal)

O traffic-squad tem capacidade interna (NOVA) para:
- Hooks textuais
- Creative briefs
- Ad copy (primary, headline, description)
- DSL Revolution scripts

Mas quando precisa de **assets visuais produzidos**, deve acionar este workflow:

| NOVA resolve internamente | Precisa de creative-studio |
|---------------------------|---------------------------|
| Hooks textuais | Imagens para Meta Ads |
| Briefs criativos | Banners Google Display |
| Ad copy | Videos de anuncio |
| DSL script | Carrosseis visuais |
| Angulos criativos | Thumbnails |
| Analise de fadiga | Variantes visuais A/B |

### Sinal de acionamento

```yaml
sinais:
  - NOVA gera brief criativo → precisa de producao visual
  - MIDAS identifica fadiga criativa → precisa de novos visuais
  - Campanha nova → precisa de assets visuais completos
  - A/B test → precisa de variantes visuais
```

---

## Stage 1: Preparacao do Brief

**Agent**: squad de origem (ex: creative-analyst NOVA do traffic-squad)

```yaml
inputs:
  - creative_brief (gerado por NOVA ou equivalente)
  - platform (Meta | Google | YouTube | Instagram)
  - format (imagem | video | carrossel | story | banner)
  - quantity (numero de variantes)
  - campaign_context (produto, audiencia, angulo)

actions:
  - Consolidar brief criativo com todas as specs
  - Incluir hooks/copy ja aprovados (se houver)
  - Definir platform specs (tamanho, ratio, formato)
  - Incluir referencias visuais (se houver)

outputs:
  - production_brief:
      squad_origem: "[traffic-squad | media-buy | ...]"
      tipo_criativo: "[imagem | video | carrossel | banner | story]"
      plataforma: "[Meta | Google | YouTube | Instagram]"
      specs:
        tamanho: "[1080x1080 | 1200x628 | ...]"
        ratio: "[1:1 | 16:9 | 9:16 | ...]"
      quantidade_variantes: "[N]"
      copy_aprovada:
        headline: "[texto]"
        primary_text: "[texto]"
        description: "[texto]"
      hooks: "[lista de hooks aprovados]"
      angulo_criativo: "[angulo principal]"
      produto: "[nome do produto]"
      audiencia: "[publico-alvo]"
      referencias_visuais: "[URLs ou descricoes]"
      deadline: "[data se aplicavel]"
      prioridade: "[alta | media | baixa]"
```

---

## Stage 2: Roteamento via Orquestrador

**Agent**: roteador (orquestrador-global)

```yaml
actions:
  - Receber production_brief do squad de origem
  - Validar completude do brief (campos obrigatorios preenchidos)
  - Classificar complexidade:
      simples: "1-3 imagens estaticas, mesmo formato"
      medio: "4-10 variantes, multiplos formatos"
      complexo: "video, animacao, campanha completa multi-formato"
  - Rotear para creative-studio com task apropriada

routing_rules:
  simples:
    action: "@creative-studio *criar-ad --brief {production_brief}"
  medio:
    action: "@creative-studio *brief --campaign {production_brief}"
    workflow: "wf-campaign-creative"
  complexo:
    action: "@creative-studio *brief --campaign {production_brief}"
    workflow: "wf-campaign-creative"
    note: "Requer aprovacao do creative-director antes de producao"

outputs:
  - routing_confirmation
  - estimated_delivery
```

---

## Stage 3: Producao (creative-studio)

**Agent**: creative-director (creative-studio)

```yaml
actions:
  - Receber production_brief
  - Ativar workflow adequado (wf-campaign-creative ou task direta)
  - Produzir assets visuais
  - Validar com brand-guardian
  - Entregar assets finais

outputs:
  - creative_assets (imagens/videos gerados)
  - prompt_log (prompts usados para reproducibilidade)
  - quality_report (validacao brand-guardian)
```

---

## Stage 4: Entrega ao Squad de Origem

**Agent**: roteador (orquestrador-global)

```yaml
actions:
  - Receber assets finais do creative-studio
  - Notificar squad de origem que assets estao prontos
  - Entregar assets + metadata

notification_template: |
  Criativos prontos para {squad_origem}:
  - Tipo: {tipo_criativo}
  - Plataforma: {plataforma}
  - Variantes: {quantidade}
  - Assets: {lista_de_arquivos}
  - Status: PRONTO PARA USO

  Proximo passo: Configurar campanha com os assets recebidos.
```

---

## Fluxo Resumido (traffic-squad → creative-studio)

```
1. NOVA (traffic-squad) gera brief criativo + hooks + copy
2. MIDAS identifica necessidade de producao visual
3. MIDAS envia production_brief ao orquestrador
4. Orquestrador valida e roteia para creative-studio
5. creative-director recebe, produz, valida
6. Orquestrador entrega assets de volta ao traffic-squad
7. MIDAS configura campanha com assets recebidos
```

---

## Stage 1 — Detalhes: Preparacao do Brief

### Inputs Requeridos

A squad de origem DEVE fornecer:

```yaml
inputs_obrigatorios:
  - creative_brief: "Descricao estruturada do criativo desejado"
  - platform: "Qual plataforma (Meta, Google, YouTube, Instagram)"
  - format: "Tipo: imagem | video | carrossel | story | banner"
  - quantity: "Quantas variantes (N >= 1)"
  - campaign_context:
      product_name: "Nome exato do produto (use naming-convention.md)"
      target_audience: "Publico-alvo preciso"
      main_angle: "Angulo criativo principal"
      value_prop: "Proposicao de valor principal"

inputs_opcionais:
  - reference_images: "[URLs ou paths para inspiracao]"
  - approved_hooks: "[Hooks textuais ja aprovados]"
  - brand_colors: "[Cores principais a usar]"
  - deadline: "[Data esperada de entrega]"
  - exclusions: "[O que NUNCA mostrar]"
  - tone: "[Tom desejado: direto | energetico | clinico | luxo]"
```

### Processo Detalhado

1. **Consolidacao** (5-10 min)
   - Squad de origem coleta todos os inputs acima
   - Valida contra naming-convention.md para sigla do produto
   - Verifica se copy ja foi aprovado (se aplicavel)

2. **Validacao Interna** (5 min)
   - Brief tem informacao suficiente para um designer produzir?
   - Specs sao claros (tamanhos, ratios)?
   - Existe contexto de negocio (produto, audiencia, angulo)?

3. **Estruturacao** (5 min)
   - Formata brief em structure padrao
   - Adiciona timestamp de criacao
   - Referencia o squad de origem via ID

4. **Sinalizacao ao Orquestrador** (0 min)
   - Envia brief ao orquestrador via canal definido
   - Aguarda confirmacao de roteamento

### Outputs Esperados

```yaml
production_brief:
  id: "{squad-origem}_{timestamp}_{uuid}"
  squad_origem: "[id do squad]"
  timestamp_criacao: "[ISO 8601]"
  tipo_criativo: "[imagem | video | carrossel | banner | story]"
  plataforma: "[Meta | Google | YouTube | Instagram]"
  specs:
    tamanho: "[1080x1080 | 1200x628 | ...]"
    ratio: "[1:1 | 16:9 | 9:16 | ...]"
    duracao_video: "[segundos, se video]"
  quantidade_variantes: "[N >= 1]"
  copy_aprovada:
    headline: "[texto]"
    primary_text: "[texto ou null]"
    description: "[texto ou null]"
  hooks_aprovados: "[lista ou null]"
  angulo_criativo: "[descricao]"
  produto_sigla: "[MPG | GPO | FDS | MAM | MCPM | MAV | ...]"
  audiencia_target: "[descricao]"
  referencias_visuais: "[URLs ou descricoes]"
  deadline: "[data se houver urgencia]"
  prioridade: "[alta | media | baixa]"
  status: "READY_FOR_ROUTING"
```

---

## Stage 2 — Detalhes: Roteamento via Orquestrador

### Proceso Detalhado

1. **Recepcao do Brief** (1 min)
   - Orquestrador recebe production_brief
   - Log no sistema: timestamp, squad_origem, tipo_criativo

2. **Validacao de Completude** (2-3 min)
   - Checklist de campos obrigatorios:
     ✓ tipo_criativo preenchido?
     ✓ plataforma valida?
     ✓ quantity >= 1?
     ✓ specs claros?
     ✓ product_sigla em naming-convention.md?
     ✓ deadline (se houver) no futuro?
   - Se falha: REJECT com feedback de campos faltantes

3. **Classificacao de Complexidade** (2 min)
   - SIMPLES (1-3 imagens, mesmo formato): DIRECT TASK
   - MEDIO (4-10 variantes, multiplos formatos): WORKFLOW
   - COMPLEXO (video, animacao, multi-fase): WORKFLOW + APPROVAL

4. **Selecao de Rota** (1 min)
   - Determina qual agente do creative-studio recebe
   - SIMPLES → @photo-editor ou @designer-junior
   - MEDIO → @creative-director
   - COMPLEXO → @creative-director + approval gate

5. **Criacao de Task/Workflow** (2 min)
   - ClickUp: criar task com production_brief
   - Etiqueta: process:creative-production, squad_origem
   - Timeline: estimada baseada em complexidade
   - Atribuicao: agente selecionado

6. **Confirmacao de Roteamento** (1 min)
   - Notifica squad_origem que brief foi roteado
   - Inclui: ETA, agente atribuido, task_id

### Roteamento Baseado em Complexidade

```
┌─────────────────┐
│ production_brief│
└────────┬────────┘
         │
    ┌────▼────┐
    │Complexidade?
    └────┬──┬──┬────┘
         │  │  │
    SIMPLES│ │ COMPLEXO
         │  │  │
    ┌────▼──▼──▼────┐
    │ @creative-st  │
    │ udio routing  │
    └────┬──┬──┬────┘
         │  │  │
    ┌────▼──┴──▼────┐
    │ Task → designer│ ou
    │       Workflow│
    └────────┬──────┘
         ┌───▼────┐
         │Production
         │  Start
         └────────┘
```

---

## Stage 3 — Detalhes: Producao (creative-studio)

### Processo Detalhado

1. **Recepcao da Task/Workflow** (2 min)
   - creative-director ou designer recebe brief
   - Valida se todos os inputs estao presentes
   - Estima tempo de producao baseado em quantidade + complexity

2. **Planejamento de Producao** (5-10 min)
   - Divide variantes em grupos (se muitas)
   - Planeja sequencia de producao
   - Reserva assets (imagens de stock, templates)
   - COMPLEXO: convoca meeting com squad_origem se necessario

3. **Producao de Assets** (time variavel)
   - Cria designs conforme brief
   - Usa design-system tokens (squads/design-system/...)
   - Exporta em formatos requeridos
   - Mantém log de prompts/decisoes (reproducibilidade)

4. **Validacao Interna** (5-10 min)
   - brand-guardian verifica:
     ✓ Cores e tom de voz consistentes?
     ✓ Tamanhos corretos?
     ✓ Copra nao foi alterada?
     ✓ Product sigla consistente?
   - Se falha: volta para producao

5. **Entrega ao Orquestrador** (2 min)
   - Empacota assets em ZIP (ou Cloud URL)
   - Gera relatório de qualidade
   - Inclui: prompts usados, decisões criativas, notas

### Estimativas de Tempo por Complexidade

| Complexidade | Variantes | Tempo Estimado | Passos |
|--------------|-----------|----------------|--------|
| **SIMPLES** | 1-3 imagens estáticas | 20-40 min | Desig → Validação → Entrega |
| **MEDIO** | 4-10 variantes, multiplos formatos | 2-4 horas | Planej → Design iterativo → Val → Entrega |
| **COMPLEXO** | Video, animacao, campanha multi-fase | 6-24 horas | Planej → Review → Design → Revision → Val → Entrega |

---

## Stage 4 — Detalhes: Entrega ao Squad de Origem

### Processo Detalhado

1. **Recepcao do Orquestrador** (2 min)
   - Orquestrador recebe assets + relatorio
   - Valida integridade dos arquivos
   - Cria notification com URL ou ZIP

2. **Notificacao ao Squad** (1 min)
   - Envia notificacao ao squad_origem
   - Inclui: arquivo/URL, relatório, próximos passos

3. **Fechamento da Task** (1 min)
   - Marca task como COMPLETA no ClickUp
   - Adiciona comentário com summary final
   - Libera recursos do creative-studio

---

## Quality Gates (Criterios de Avanco)

### Gate 1: Brief Valido (Stage 1 → Stage 2)

**Criterios para PASSAR:**
- [ ] Todos os campos obrigatorios preenchidos
- [ ] Product sigla existe em naming-convention.md
- [ ] Format e platform sao valores validos
- [ ] Quantity >= 1
- [ ] Specs (tamanho, ratio) sao claros e validos

**Criterios para FALHAR:**
- [ ] Faltam campos obrigatorios
- [ ] Product sigla invalida ou nao existe
- [ ] Format ou platform desconhecido
- [ ] Quantity <= 0
- [ ] Specs ambiguas ou contraditorios

**Acao se FALHAR:**
- Orquestrador REJEITA brief
- Retorna ao squad_origem com lista exata de campos faltantes
- Squad pode reenviar brief corrigido

### Gate 2: Brief Roteado (Stage 2 → Stage 3)

**Criterios para PASSAR:**
- [ ] Complexidade classificada (SIMPLES | MEDIO | COMPLEXO)
- [ ] Agente atribuido (selecionado baseado em capacidade)
- [ ] Task criada no ClickUp com timeline estimada
- [ ] Notificacao enviada ao squad_origem

**Criterios para FALHAR:**
- [ ] Nao foi possivel classificar complexidade
- [ ] Nenhum agente disponivel para o tipo de criativo
- [ ] Task nao pode ser criada (erro de API)

**Acao se FALHAR:**
- Orquestrador PAUSA e aguarda intervencao manual
- Notifica squad_origem de delay
- Pode rotear para outro agente ou squad

### Gate 3: Assets Produzidos (Stage 3 → Stage 4)

**Criterios para PASSAR:**
- [ ] Todos os assets gerados conforme specs
- [ ] Brand-guardian validou (cores, tom, tamanhos)
- [ ] Relatório de qualidade preenchido
- [ ] Nenhum blocker pendente

**Criterios para FALHAR:**
- [ ] Assets estao incompletos ou com erro
- [ ] Brand-guardian reprovou (cor errada, tamanho invalido)
- [ ] Relatório incompleto
- [ ] Issues encontradas que requerem revisao

**Acao se FALHAR:**
- Assets voltam para creative-director
- Issues sao listadas em comentario no ClickUp
- Creative-director corrige e resubmete

### Gate 4: Entrega Completa (Stage 4 → FIM)

**Criterios para PASSAR:**
- [ ] Squad_origem confirmou recepcao dos assets
- [ ] Assets foram integrados na campanha
- [ ] Task marcada como COMPLETA
- [ ] Feedback (qualidade: 1-5) fornecido

**Criterios para FALHAR:**
- [ ] Squad nao conseguiu usar assets (erro no arquivo?)
- [ ] Assets nao correspondem ao brief original
- [ ] Feedback negativo (qualidade < 3)

**Acao se FALHAR:**
- Orquestrador abre task de revisao
- Creative-studio faz ajustes
- Reentrega ao squad

---

## Decision Trees

### Arvore 1: Quando Acionar Este Workflow?

```
Squad precisa de criativo visual?
├─ SIM: "Imagem | Video | Carrossel | Banner | Story"
│   └─ E squad nao tem capacidade interna de produzir?
│       ├─ SIM (ex: traffic-squad): Aciona ESTE workflow
│       └─ NAO (ex: creative-studio ja tem designer): Resolve internamente
│
└─ NAO: Nao aciona workflow
    └─ (Ex: Squad precisa so de copy, hooks, ou estrategia)
```

### Arvore 2: Qual Rota de Roteamento?

```
Production_brief valido?
├─ NAO: Orquestrador REJEITA + feedback
│
└─ SIM: Classifica complexidade
    ├─ SIMPLES (1-3 imagens, mesmo formato)
    │   └─ Rota: @photo-editor ou @designer-junior
    │       └─ Workflow: Task direta (20-40 min)
    │
    ├─ MEDIO (4-10 variantes, multiplos formatos)
    │   └─ Rota: @creative-director
    │       └─ Workflow: wf-campaign-creative (2-4 horas)
    │
    └─ COMPLEXO (video, animacao, multi-fase)
        └─ Rota: @creative-director + approval gate
            └─ Workflow: wf-campaign-creative + review antes de producao
```

### Arvore 3: O Que Fazer se Brand-Guardian Rejeita?

```
Brand-Guardian validou assets?
├─ SIM (passa gate 3): Segue para entrega
│
└─ NAO: Issues encontradas?
    ├─ Issue critica (ex: tamanho invalido):
    │   └─ Acao: Creative-director REFAZ asset
    │       └─ Resubmete para validacao
    │
    ├─ Issue menor (ex: cor ligeiramente off):
    │   ├─ Color: Se é dentro de 5% do Pantone: APROVA
    │   ├─ Copy: Se alteracao foi mínima: APROVA
    │   └─ Tamanho: Se erro < 2%: APROVA (mas loga para proxima vez)
    │
    └─ Issues multiplas ou severas:
        └─ Acao: Volta para creative-director para revisao completa
```

---

## Risk & Mitigation

### Risk 1: Brief Incompleto ou Ambiguo

**Risco:** Squad de origem envia brief sem specs claros
**Probabilidade:** MEDIA
**Impacto:** Delay de 24h, assets inutiveis, retrabalho

**Mitigacao:**
- Orquestrador valida OBRIGATORIAMENTE contra checklist antes de rotear
- Se falha validacao: REJEITA + feedback especifico
- Squad nao pode re-rotear sem corrigir campos obrigatorios
- Brief template pre-preenchido disponivel em squads/creative-studio/templates/

### Risk 2: Agente Criativo Indisponivel

**Risco:** Nenhum agente do creative-studio disponivel
**Probabilidade:** BAIXA (team e multidisciplinario)
**Impacto:** Delay de 24h a 72h

**Mitigacao:**
- Orquestrador checa capacidade ANTES de rotear (dashboard de occupancy)
- Se indisponivel: oferece opcoes:
  1. Fila (aguarda proximo slot disponivel)
  2. Terceirizar (busca freelancer via n8n)
  3. Atrasar deadline (negocia com squad_origem)
- Para complexo: pode ativar squad paralelo (creative-studio + design-system)

### Risk 3: Assets Nao Correspondem ao Brief

**Risco:** Criativo produzido nao atende ao briefing original
**Probabilidade:** MEDIA (creative-director pode interpretar diferente)
**Impacto:** Rejeicao, retrabalho, delay de 24h

**Mitigacao:**
- Brand-guardian valida EXPLICITAMENTE contra brief original (checklist)
- Se desvio > 10%: REJEITA com feedback detalhado
- Se desvio < 10%: APROVA com anotacao para proxima vez
- Creative-studio documenta decisoes criativas (por que desviou, se aplicavel)

### Risk 4: Specs Tecnicas Invalidas

**Risco:** Tamanho ou ratio informado e invalido para plataforma
**Probabilidade:** BAIXA (plataformas mudaram specs? v2 novo? )
**Impacto:** Assets gerados em tamanho errado, inutiveis

**Mitigacao:**
- Orquestrador valida specs contra tabela padrao de plataformas (vault/platform-specs.yaml)
- Se spec desconhecida: REJEITA com specs recomendadas
- Creative-studio mantém reference doc de specs por plataforma (atualizado quarterly)
- Antes de gerar: creative-director confirma specs com squad_origem

### Risk 5: Feedback Negativo (Qualidade < 3)

**Risco:** Squad_origem rejeita assets (qualidade ruim, nao combina)
**Probabilidade:** MEDIA (criatividade e subjetiva)
**Impacto:** Retrabalho completo, loss of time

**Mitigacao:**
- Se feedback < 3: Abre task de revisao automaticamente
- Creative-studio recebe feedback em detalhe (o que estava ruim?)
- Feedback armazenado em SuperMemory (creative-studio container) para aprender padrao
- Se feedback repetido (mesmo squad): escalona para creative-director 1:1

---

## Handoff Procedures

### Handoff 1: Squad Origem → Orquestrador

**Responsavel:** Squad origin agent (ex: NOVA, MIDAS, creative-analyst)

```
Input:
- production_brief (estrutura completa)
- Qualquer arquivo de referencia (imagens, copy aprovado)

Handoff:
1. Squad cria arquivo em .data/handoffs/{timestamp}_{squad-origem}_to_orchestrator/
   - brief.yaml (production_brief estrutura)
   - reference_images/ (se houver)
   - approved_copy.md (se houver)

2. Squad notifica orquestrador via ClickUp comment ou channel
   - Link para pasta de handoff
   - Urgencia + deadline (se houver)

3. Orquestrador:
   - Reconhece recepcao (1 min)
   - Valida brief (2-3 min)
   - Aprova ou REJEITA com feedback

Expected SLA: Reconhecimento em < 5 min
```

### Handoff 2: Orquestrador → Creative-Studio

**Responsavel:** Orquestrador (orchestrator agent)

```
Input:
- production_brief (validado)
- ClickUp task (criada com briefing)

Handoff:
1. Orquestrador cria pasta em .data/handoffs/{timestamp}_{squad-origem}_to_studio/
   - production_brief.yaml (final)
   - task_link.txt (link ClickUp)
   - reference_images/ (copiado do squad_origem)

2. Orquestrador notifica creative-director:
   - @creative-studio *brief --task {task_id} --squad {squad-origem}
   - Inclui: ETA, prioridade, restrictions

3. Creative-director:
   - Reconhece (1 min)
   - Estima tempo final (2-3 min)
   - Inicia producao

Expected SLA: Inicio da producao em < 15 min
```

### Handoff 3: Creative-Studio → Orquestrador

**Responsavel:** Creative-director (creative-studio)

```
Input:
- Assets finais (imagens/videos)
- Quality report (brand-guardian validacao)
- Prompt log (reproducibilidade)

Handoff:
1. Creative-studio cria pasta em .data/handoffs/{timestamp}_{squad-origem}_from_studio/
   - assets/ (imagens/videos em formatos requeridos)
   - quality_report.md (brand-guardian checklist)
   - prompt_log.md (prompts usados, decisoes)
   - metadata.yaml (sizes, formats, variantes info)

2. Creative-studio notifica orquestrador:
   - Comment no ClickUp task: "Assets prontos para entrega"
   - Link para pasta de handoff

3. Orquestrador:
   - Valida integridade (ficheiros nao corrompidos?)
   - Compacta em ZIP (se multiplos ficheiros)
   - Prepara notificacao para squad_origem

Expected SLA: Entrega ao squad em < 5 min
```

### Handoff 4: Orquestrador → Squad Origem

**Responsavel:** Orquestrador

```
Input:
- Assets finais (ZIP ou URL)
- Quality report + notes
- Metadata

Handoff:
1. Orquestrador envia notificacao ao squad_origem:
   - Email ou ClickUp ou Slack (configurable)
   - Link para download ou Cloud URL
   - Relatório de qualidade (resumido)
   - Instrucoes proximas (como integrar na campanha)

2. Squad_origem recebe assets e:
   - Valida se correspondem ao brief
   - Integra na campanha
   - Fornece feedback (qualidade 1-5)

Expected SLA: Notificacao em < 5 min
```

---

## Rollback Procedures

### Rollback 1: Brief Invalido (Pre-Roteamento)

**Trigger:** Orquestrador detecta campos obrigatorios faltando

```
1. Orquestrador REJEITA brief automaticamente
2. Erro enviado ao squad_origem com lista exata de campos faltantes
3. Squad_origem corrige e reenvira brief
4. Orquestrador revalida

Status: RESET_TO_STAGE_1
```

### Rollback 2: Agente Indisponivel (Roteamento Falha)

**Trigger:** Nenhum agente disponivel para rota selecionada

```
1. Orquestrador NAO roteia brief
2. Oferece 3 opcoes ao squad_origem:
   A) Entrar em fila (aguarda < 24h)
   B) Terceirizar (freelancer)
   C) Atrasar deadline

3. Squad_origem escolhe opcao
4. Se opcao A: brief aguarda em fila, rerroteado quando agente fica livre

Status: WAITING_FOR_AGENT
```

### Rollback 3: Assets Rejeitados por Brand-Guardian

**Trigger:** Brand-guardian aprova == NO em gate 3

```
1. Creative-director recebe lista de issues
2. Se issues sao CRITICAS (tamanho errado, cor muito diferente):
   - Descarta version atual (se puder salvaguardar)
   - REFAZ assets do zero
   - Resubmete para validacao

3. Se issues sao MENORES (cor muito ligeiramente diferente, typo):
   - Creative-director ajusta em 15-30 min
   - Resubmete para validacao

4. If issues sao MULTIPLAS:
   - Creative-director agenda 1:1 com creative-chief para alinhamento
   - Torna a produzir com learnings
   - Resubmete

Status: REVISION_IN_PROGRESS
```

### Rollback 4: Squad_Origem Rejeita Assets (Pos-Entrega)

**Trigger:** Squad_origem fornece feedback qualidade < 3

```
1. Orquestrador abre task de revisao no ClickUp
2. Creative-studio recebe feedback em detalhe
3. Dependendo do feedback:
   A) Se assets "nao correspondem ao brief": Voltar ao inicio da producao
   B) Se "tamanho errado": Quick fix (10-15 min)
   C) Se "cor/tom errado": Ajuste e reentrega (30-45 min)

4. Creative-studio marca ajustes e reenvia

Status: REVISION_IN_PROGRESS → Volta para Gate 3 (Validacao)

SLA para revisao: < 4 horas
```

---

## Success Criteria per Phase

### Stage 1: Brief Completo & Validado

```yaml
criterios_sucesso:
  - todos_campos_obrigatorios_preenchidos: boolean (true)
  - product_sigla_valida: boolean (true)
  - specs_claros: boolean (true)
  - quantity_ge_1: boolean (true)
  - brief_timestamp: ISO 8601
  - squad_origem_id: string

metricas:
  - duration: "< 15 min"
  - rejection_rate: "< 5%" (briefs que precisam de revisao)

exemplo_sucesso:
  - Production_brief criado e validado em 10 min
  - 0 campos faltando
  - Specs: 1080x1080, ratio 1:1, quantidade: 3 variantes
```

### Stage 2: Brief Roteado & Accepted by Creative-Studio

```yaml
criterios_sucesso:
  - brief_classificado: "[SIMPLES | MEDIO | COMPLEXO]"
  - agente_atribuido: string (agente_id)
  - task_criada: boolean (true)
  - timeline_estimada: string (ex: "2 hours")
  - notificacao_enviada_squad: boolean (true)

metricas:
  - duration: "< 10 min"
  - roteamento_sucesso_rate: "> 95%"
  - agente_aceitacao_rate: "> 95%"

exemplo_sucesso:
  - Brief classificado como MEDIO
  - Atribuido a @creative-director
  - Task criada: ClickUp #12345
  - ETA: 3 horas
```

### Stage 3: Assets Produzidos & Validated by Brand-Guardian

```yaml
criterios_sucesso:
  - assets_count_eq_quantity: boolean (true)
  - specs_validos: boolean (true) (tamanho exato, ratio, formatos)
  - brand_guardian_aprova: boolean (true)
  - prompt_log_completo: boolean (true)
  - qualidade_rating: int (1-5, >= 4)

metricas:
  - duration_estimada: "2-4 horas (MEDIO)"
  - assets_rejeicao_rate: "< 10%"
  - primeira_passagem_rate: "> 85%"
  - revision_ciclos: "<= 2"

exemplo_sucesso:
  - 3 imagens produzidas (1080x1080)
  - Brand-guardian aprova (cores OK, tamanho OK)
  - Prompt log: 5 prompts documentados
  - Qualidade rating: 4/5
```

### Stage 4: Assets Entregues & Integrated by Squad

```yaml
criterios_sucesso:
  - arquivos_integros: boolean (true)
  - squad_confirmou_recepcao: boolean (true)
  - assets_integrados_campanha: boolean (true)
  - feedback_qualidade: int (1-5, >= 3)
  - task_marcada_completa: boolean (true)

metricas:
  - duration: "< 5 min (entrega)"
  - squad_satisfacao_rate: "> 90%"
  - retrabalho_rate: "< 15%"
  - end_to_end_success_rate: "> 85%"

exemplo_sucesso:
  - Arquivos ZIP entregues e descompactados
  - Squad confirmou recepcao em < 10 min
  - Assets integrados em campanha Meta Ads em < 1 hora
  - Feedback qualidade: 5/5 ("Exatamente o que pedi!")
```

---

## Cost & Time Estimates

### Tempo Total por Complexidade

| Complexidade | Brief → Validacao | Roteamento | Producao | Entrega | Total |
|--------------|------------------|-----------|----------|---------|-------|
| **SIMPLES** | 10 min | 5 min | 25 min | 3 min | ~45 min |
| **MEDIO** | 15 min | 8 min | 180 min (3h) | 5 min | ~210 min (3.5h) |
| **COMPLEXO** | 20 min | 10 min | 480-1440 min (8-24h) | 10 min | ~8-24h + 40 min |

### Custo Aproximado (em tokens/recursos)

| Fase | Simples | Medio | Complexo |
|------|---------|-------|----------|
| **Stage 1** (Brief) | 2k tokens | 3k tokens | 5k tokens |
| **Stage 2** (Roteamento) | 1k tokens | 2k tokens | 3k tokens |
| **Stage 3** (Producao) | 15k-25k tokens | 40k-80k tokens | 100k-300k tokens |
| **Stage 4** (Entrega) | 0.5k tokens | 1k tokens | 2k tokens |
| **TOTAL** | 18-28k | 46-86k | 110-310k |

Notas:
- Tokens variam baseado em modelo (Haiku vs Sonnet vs Opus)
- Producao com image gen (nano-banana) e mais cara que design
- Video production e MUITO mais cara (outsource)

---

## Dependencies Matrix

### Dependencias Explícitas

```
Stage 1 (Brief Preparacao)
  ├─ DEPENDS_ON: Squad de origem estar online + capaz de fornecer input
  ├─ BLOCKS: Nada (outras etapas aguardam output desta)
  └─ MUST_COMPLETE_BEFORE: Stage 2

Stage 2 (Roteamento)
  ├─ DEPENDS_ON: Stage 1 completo + Orquestrador online
  ├─ DEPENDS_ON: Creative-studio agentes disponibilidade (para rota)
  ├─ BLOCKS: Stage 3 (production nao comeca sem rota)
  └─ MUST_COMPLETE_BEFORE: Stage 3

Stage 3 (Producao)
  ├─ DEPENDS_ON: Stage 2 completo + Task criada em ClickUp
  ├─ DEPENDS_ON: Creative-studio designer/agente selecionado
  ├─ DEPENDS_ON: Brand-guardian disponivel (para validacao)
  ├─ BLOCKS: Stage 4 (entrega nao comeca sem assets)
  └─ MUST_COMPLETE_BEFORE: Stage 4

Stage 4 (Entrega)
  ├─ DEPENDS_ON: Stage 3 completo + Assets prontos
  ├─ DEPENDS_ON: Orquestrador online (para notificar)
  ├─ DEPENDS_ON: Squad origem disponivel (para receber)
  ├─ BLOCKS: Workflow termina (sem dependencias seguintes)
  └─ FINAL_STAGE: SIM
```

### Dependencias Entre Squads

```yaml
squad_dependencies:
  traffic_squad:
    depends_on: creative_studio
    when: "precisa de criativos visuais"
    handoff: "production_brief"

  creative_studio:
    depends_on: traffic_squad (input)
    depends_on: brand_guardian (validacao)
    depends_on: design_system (tokens/componentes)
    when: "producao de assets"

  brand_guardian:
    depends_on: creative_studio (assets para validar)
    when: "validacao de brand consistency"

  orquestrador_global:
    depends_on: traffic_squad (input brief)
    depends_on: creative_studio (output assets)
    when: "roteamento e coordenacao"
```

---

## Checkpoints

### Checkpoint 1: Brief Validation Complete

**Localizacao:** fim de Stage 1
**Responsavel:** Orquestrador
**Verificacoes:**
- [ ] Brief tem todos campos obrigatorios
- [ ] Specs sao validos
- [ ] Product sigla existe
- [ ] Arquivo brief.yaml criado

**Criterio de Avanco:** SIM (brief valido e completo)
**Acao se FALHA:** Rejeitar e pedir squad corrigir

---

### Checkpoint 2: Routing Complete

**Localizacao:** fim de Stage 2
**Responsavel:** Orquestrador
**Verificacoes:**
- [ ] Complexidade classificada
- [ ] Agente atribuido (ou fila se nao disponivel)
- [ ] ClickUp task criada
- [ ] Notificacao enviada ao squad

**Criterio de Avanco:** SIM (brief roteado com sucesso)
**Acao se FALHA:** Pausar e oferecer opcoes (fila, terceirizar)

---

### Checkpoint 3: Assets Quality Validated

**Localizacao:** fim de Stage 3 (producao)
**Responsavel:** Brand-Guardian
**Verificacoes:**
- [ ] Assets count == quantity solicitada
- [ ] Specs validos (tamanho, ratio, formato)
- [ ] Cores / tom consistentes com brand
- [ ] Copy nao foi alterada
- [ ] Qualidade visual >= 4/5

**Criterio de Avanco:** SIM (brand-guardian aprova)
**Acao se FALHA:** Voltar para creative-director para revisao

---

### Checkpoint 4: Delivery Confirmed

**Localizacao:** fim de Stage 4
**Responsavel:** Squad Origen
**Verificacoes:**
- [ ] Squad confirmou recepcao de assets
- [ ] Assets descompactados e integrados
- [ ] Feedback qualidade fornecido (1-5)
- [ ] ClickUp task marcada COMPLETA

**Criterio de Avanco:** SIM (entrega completa e confirmada)
**Acao se FALHA:** Abrir task de revisao (feedback < 3)

---

## Automations & Triggers

### Trigger 1: Auto-Reject Invalid Briefs

```yaml
trigger: "Orquestrador detecta campos faltando no brief"
action:
  - status: "REJECTED"
  - message: "Brief invalido. Faltam: {lista_campos}"
  - notifica: squad_origem
  - permite_reenvio: true (sem delay penalty)
```

### Trigger 2: Auto-Escalate to Creative-Chief

```yaml
trigger: "Feedback qualidade < 3 OU Revision ciclos > 2"
action:
  - escalate_to: creative_chief
  - task_priority: "HIGH"
  - message: "Revisao multipla necessaria. Creative-chief review solicitado"
```

### Trigger 3: Auto-Archive Completed Task

```yaml
trigger: "Squad confirmou recepcao + feedback fornecido"
action:
  - close_clickup_task: true
  - archive_handoff_folder: true
  - log_completion: SuperMemory
  - save_artifacts: ".data/executions/{date}/{workflow_id}/"
```

---

## Post-Workflow Learning

Apos cada workflow completion:
1. Salvar assets e metadata em `.data/executions/{date}_{squad-origem}/`
2. Registrar feedback em SuperMemory (creative-studio container)
3. Atualizar design-system com novos components se aplicavel
4. Log em ds-feedback-log.md qualquer novo pattern criado

## MEGABRAIN Deep Validation

- Last run: `20260514-validate-deep`
- Validator: `mega-brain/megabrain-chief`
- Mode: `deep`
- Workflow ID: `creative-production-request`
- Status: `pass`
- External execution: not performed during structural validation.
