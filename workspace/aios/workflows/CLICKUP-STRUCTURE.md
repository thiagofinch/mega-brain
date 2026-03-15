# CLICKUP STRUCTURE - BILHON

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ██████╗██╗     ██╗ ██████╗██╗  ██╗██╗   ██╗██████╗                       ║
║    ██╔════╝██║     ██║██╔════╝██║ ██╔╝██║   ██║██╔══██╗                      ║
║    ██║     ██║     ██║██║     █████╔╝ ██║   ██║██████╔╝                      ║
║    ██║     ██║     ██║██║     ██╔═██╗ ██║   ██║██╔═══╝                       ║
║    ╚██████╗███████╗██║╚██████╗██║  ██╗╚██████╔╝██║                           ║
║     ╚═════╝╚══════╝╚═╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝╚═╝                           ║
║                                                                              ║
║              ESTRUTURA ORGANIZACIONAL CLICKUP                                ║
║              Baseada no Modelo Pedro Valerio (AIOS/Sincra)                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## FILOSOFIA CORE

> "Toda tarefa e um workflow. Mapeie como humano primeiro."
> -- Pedro Valerio

Esta estrutura segue os principios do modelo AIOS/Sincra:
1. **Task-First**: Tarefas sao a unidade atomica
2. **Status como Trigger**: Mudanca de status dispara automacoes
3. **Tarefas Agnosticas**: Mesmo fluxo para diferentes projetos
4. **Quality Gates**: Validacoes humanas obrigatorias em pontos criticos

---

## WORKSPACE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BILHON WORKSPACE                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐    │
│  │    RH     │ │  FINANCE  │ │    OPS    │ │ MARKETING │ │ PRODUCTS  │    │
│  │  (Space)  │ │  (Space)  │ │  (Space)  │ │  (Space)  │ │  (Space)  │    │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘    │
│                                                                             │
│  Team ID: 90132320212                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Spaces Reais (Mapeados via API)

| Space | ID | Cor | Multiple Assignees |
|-------|------|-----|-------------------|
| OPERAÇÕES | `901310028360` | #a18072 | Nao |
| FURION | `901310028391` | #e5484d | Nao |
| AGÊNCIA \| Paulo Lacerda | `901310028423` | #248f7d | Nao |
| AGÊNCIA \| Bryan Blandy | `901310028457` | #0091ff | Nao |
| PRODUTOS EDUCACIONAIS | `901310028533` | #e93d82 | Nao |
| AGÊNCIA \| Lucas Neves | `901310873667` | #0091ff | Nao |
| PRODUTORA | `901311226861` | #ab4aba | Sim |
| CHALLENGE | `901311258326` | #B17E22 | Sim |
| Bilhon Cortex | `901312449713` | #ab4aba | Sim |

### Status Padrao (Maioria dos Spaces)

| Status | Tipo | Cor |
|--------|------|-----|
| backlog | open | #87909e |
| onhold | unstarted | #656f7d |
| em progresso | custom | #4466ff |
| atrasado | custom | #d33d44 |
| aguardando revisão | custom | #e16b16 |
| reprovado | custom | #ee5e99 |
| bloqueado | custom | #5f55ee |
| concluído | done | #0f9d9f |
| cancelado | done | #b660e0 |
| fechado | closed | #008844 |

---

## SPACES

### 1. RH (Cultura & Gente)

```yaml
Space: RH
Owner: Nathalia Gomes
Color: "#7C3AED"  # Purple

Folders:
  - HIRING
  - ONBOARDING
  - PERFORMANCE
  - CULTURE

Lists:
  HIRING:
    - Vagas Abertas
    - Pipeline de Candidatos
    - Entrevistas Agendadas
    - Ofertas Enviadas
    - Contratados

  ONBOARDING:
    - Documentacao Pendente
    - Trilha de Onboarding
    - Equipamentos
    - Acessos

  PERFORMANCE:
    - Scorecards Q1
    - Scorecards Q2
    - Scorecards Q3
    - Scorecards Q4
    - 1:1s
```

#### Status Customizados - HIRING

| Status | Cor | Descricao |
|--------|-----|-----------|
| `BACKLOG` | Gray | Vaga ainda nao priorizada |
| `TRIAGEM` | Blue | Triando CVs |
| `ENTREVISTA_RH` | Yellow | Entrevista com RH |
| `ENTREVISTA_TECNICA` | Orange | Entrevista com gestor |
| `ENTREVISTA_CULTURA` | Purple | Fit cultural |
| `REFERENCIA` | Cyan | Checando referencias |
| `OFERTA` | Green | Oferta enviada |
| `NEGOCIACAO` | Pink | Em negociacao |
| `CONTRATADO` | Green | Vaga fechada |
| `RECUSADO` | Red | Candidato recusou |
| `ARQUIVO` | Gray | Processo pausado |

---

### 2. FINANCE (Financeiro)

```yaml
Space: FINANCE
Owner: TBD
Color: "#10B981"  # Green

Folders:
  - CONTAS_A_PAGAR
  - CONTAS_A_RECEBER
  - RELATORIOS
  - INVESTIMENTOS

Lists:
  CONTAS_A_PAGAR:
    - Fornecedores
    - Folha de Pagamento
    - Impostos
    - Servicos

  CONTAS_A_RECEBER:
    - Faturas Abertas
    - Inadimplentes
    - Recuperacao

  RELATORIOS:
    - DRE Mensal
    - Fluxo de Caixa
    - KPIs
```

#### Status Customizados - FINANCEIRO

| Status | Cor | Descricao |
|--------|-----|-----------|
| `PENDENTE` | Gray | Aguardando processamento |
| `EM_ANALISE` | Blue | Sendo analisado |
| `APROVADO` | Green | Aprovado para pagamento |
| `AGENDADO` | Yellow | Pagamento agendado |
| `PAGO` | Green | Pagamento realizado |
| `VENCIDO` | Red | Pagamento atrasado |
| `CANCELADO` | Gray | Cancelado |

---

### 3. OPS (Operacoes)

```yaml
Space: OPS
Owner: Romulo Saldanha
Color: "#F59E0B"  # Amber

Folders:
  - PROCESSOS
  - FORNECEDORES
  - EVENTOS
  - INFRAESTRUTURA

Lists:
  PROCESSOS:
    - SOPs Ativos
    - SOPs em Revisao
    - Melhoria Continua

  FORNECEDORES:
    - Ativos
    - Avaliacao
    - Onboarding

  EVENTOS:
    - Calendario de Eventos
    - Producao
    - Pos-Evento
```

#### Status Customizados - OPS

| Status | Cor | Descricao |
|--------|-----|-----------|
| `BACKLOG` | Gray | Na fila |
| `EM_ANDAMENTO` | Blue | Sendo executado |
| `REVISAO` | Yellow | Em revisao |
| `BLOQUEADO` | Red | Bloqueado |
| `CONCLUIDO` | Green | Finalizado |

---

### 4. MARKETING

```yaml
Space: MARKETING
Owner: TBD (CMO)
Color: "#EC4899"  # Pink

Folders:
  - CAMPANHAS
  - CONTEUDO
  - CRIATIVOS
  - FUNIS

Lists:
  CAMPANHAS:
    - Planejamento
    - Em Producao
    - Ativas
    - Finalizadas

  CONTEUDO:
    - Calendario Editorial
    - Rascunhos
    - Em Revisao
    - Publicados

  CRIATIVOS:
    - Briefing
    - Producao
    - Aprovacao
    - Biblioteca
```

#### Status Customizados - CONTEUDO

| Status | Cor | Descricao |
|--------|-----|-----------|
| `IDEIA` | Gray | Ideia inicial |
| `BRIEFING` | Blue | Briefing sendo criado |
| `PRODUCAO` | Yellow | Em producao |
| `REVISAO` | Orange | Aguardando revisao |
| `APROVADO` | Green | Aprovado |
| `AGENDADO` | Cyan | Agendado para publicacao |
| `PUBLICADO` | Green | Publicado |

---

### 5. PRODUCTS (Tech)

```yaml
Space: PRODUCTS
Owner: Andre Tessmann (CTO)
Color: "#3B82F6"  # Blue

Folders:
  - CLICKMAX
  - FURION
  - BUGS
  - INFRAESTRUTURA

Lists:
  CLICKMAX:
    - Backlog
    - Sprint Atual
    - Em Review
    - Done

  FURION:
    - Backlog
    - Sprint Atual
    - Em Review
    - Done

  BUGS:
    - Triagem
    - P1 - Critico
    - P2 - Alto
    - P3 - Medio
    - P4 - Baixo
```

#### Status Customizados - DESENVOLVIMENTO

| Status | Cor | Descricao |
|--------|-----|-----------|
| `BACKLOG` | Gray | No backlog |
| `READY` | Blue | Pronto para dev |
| `IN_PROGRESS` | Yellow | Em desenvolvimento |
| `CODE_REVIEW` | Orange | Em code review |
| `QA` | Purple | Em QA |
| `STAGING` | Cyan | Em staging |
| `DONE` | Green | Em producao |
| `BLOCKED` | Red | Bloqueado |

---

## CAMPOS CUSTOMIZADOS

### Campos Globais (Todos os Spaces)

| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| `Priority` | Dropdown | Sim | P1, P2, P3, P4 |
| `Owner` | People | Sim | Responsavel |
| `Due Date` | Date | Nao | Prazo |
| `SLA` | Number | Nao | Tempo esperado em horas |
| `Quality Gate` | Checkbox | Nao | Requer aprovacao |

### Campos por Space

#### RH - Campos de Candidato

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `CV Link` | URL | Link para CV |
| `Linkedin` | URL | Perfil LinkedIn |
| `Salario Pretendido` | Currency | Expectativa salarial |
| `Disponibilidade` | Date | Data de inicio |
| `Score Entrevista` | Number | Nota da entrevista (0-100) |

#### FINANCE - Campos Financeiros

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `Valor` | Currency | Valor da transacao |
| `Vencimento` | Date | Data de vencimento |
| `Categoria` | Dropdown | Tipo de despesa/receita |
| `Centro de Custo` | Dropdown | Area responsavel |
| `NF` | URL | Link para nota fiscal |

#### PRODUCTS - Campos de Desenvolvimento

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `Story Points` | Number | Estimativa de esforco |
| `Sprint` | Dropdown | Sprint atual |
| `Epic` | Relationship | Epic relacionado |
| `PR Link` | URL | Link para Pull Request |
| `Deploy Date` | Date | Data do deploy |

---

## AUTOMACOES NATIVAS

### Automacao 1: Notificacao de Candidato em Entrevista

```
TRIGGER: Status muda para "ENTREVISTA_RH"
ACTION:
  - Criar subtask "Agendar sala de reuniao"
  - Notificar owner
  - Adicionar due date (hoje + 3 dias)
```

### Automacao 2: SLA de Resposta a Candidato

```
TRIGGER: Task criada em "Pipeline de Candidatos"
CONDITION: Status = "TRIAGEM"
ACTION:
  - Definir SLA = 48 horas
  - Se SLA estourado: Notificar Nathalia
  - Mudar cor da task para vermelho
```

### Automacao 3: Quality Gate de Contratacao

```
TRIGGER: Status muda para "OFERTA"
CONDITION: Quality Gate = false
ACTION:
  - Bloquear mudanca de status
  - Notificar: "Requer aprovacao de Thiago ou Claudio"
  - Criar subtask: "Aprovacao executiva"
```

### Automacao 4: Sync com N8N

```
TRIGGER: Qualquer mudanca de status
ACTION:
  - Enviar webhook para N8N
  - Payload: {task_id, status_old, status_new, owner}
  - Endpoint: https://thiagofinch.app.n8n.cloud/webhook/bilhon-notify
```

### Automacao 5: Arquivar Tarefas Antigas

```
TRIGGER: Task com status "CONCLUIDO" ha mais de 30 dias
ACTION:
  - Mover para folder "Arquivo"
  - Remover da view principal
```

### Automacao 6: Criacao de Scorecard Trimestral

```
TRIGGER: Dia 1 de cada trimestre (Jan, Apr, Jul, Oct)
ACTION:
  - Criar task "Scorecard Q[N]" para cada membro do time
  - Atribuir ao respectivo gestor
  - Definir due date = dia 15 do mes
```

---

## VIEWS RECOMENDADAS

### View 1: Board (Kanban)

```
Vista padrao para visualizar pipeline de tarefas.
Agrupado por: Status
Filtrado por: Assignee = Me
```

### View 2: Timeline (Gantt)

```
Vista para planejamento de projetos.
Agrupado por: Folder
Mostrando: Start Date, Due Date, Dependencies
```

### View 3: Calendar

```
Vista para ver deadlines e eventos.
Agrupado por: Week
Filtrado por: Due Date = This Month
```

### View 4: Workload

```
Vista para balanceamento de carga.
Mostrando: Assignee, Task Count, Story Points
```

---

## INTEGRACAO COM MEGA BRAIN

### Sync Bidirecional

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│    CLICKUP                           MEGA BRAIN                             │
│    ┌───────────────┐                ┌───────────────┐                      │
│    │               │   Webhook      │               │                      │
│    │  Task Status  │ ───────────▶   │  N8N Workflow │                      │
│    │  Changed      │                │               │                      │
│    └───────────────┘                └───────────────┘                      │
│           ▲                                │                                │
│           │        API                     │                                │
│           └────────────────────────────────┘                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Eventos a Capturar

| Evento | Acao no Mega Brain |
|--------|-------------------|
| `task.created` | Logar criacao |
| `task.updated` | Atualizar MISSION-STATE |
| `task.status_changed` | Disparar agente |
| `task.assignee_changed` | Notificar |
| `task.due_date_changed` | Recalcular timeline |

---

## ROLLOUT PLAN

### Fase 1: Setup Inicial

1. Criar Spaces no ClickUp
2. Configurar status customizados
3. Criar campos customizados
4. Importar membros do time

### Fase 2: Automacoes Basicas

1. Configurar notificacoes
2. Criar SLAs
3. Implementar Quality Gates

### Fase 3: Integracao N8N

1. Configurar webhook
2. Criar workflow de sync
3. Testar bidirecionalidade

### Fase 4: Treinamento

1. Documentar processos
2. Treinar time
3. Go-live

---

## ACCEPTANCE CRITERIA

| Criterio | Status |
|----------|--------|
| Definir 5 Spaces | ✅ PASS |
| Status customizados por tipo | ✅ PASS |
| Campos customizados definidos | ✅ PASS |
| 3+ automacoes nativas | ✅ PASS (6 definidas) |

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              ESTRUTURA CLICKUP GERADA POR JARVIS                             ║
║              Baseada no modelo AIOS/Sincra (Pedro Valerio)                   ║
║              Data: 2026-01-11                                                ║
║              User Story: US-008                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
