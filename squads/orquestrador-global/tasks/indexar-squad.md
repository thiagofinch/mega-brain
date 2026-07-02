---
task: indexar-squad
name: 'Task: Indexar Squad'
version: "3.1.1"
category: operations
difficulty: intermediate
responsavel: '@capability-cartographer'
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
pre_condition: Squad path exists with config.yaml and agents/ directory
post_condition: Squad indexed in ecosystem-registry.yaml with capabilities, domain, problems, and keywords
performance:
  error_handling: graceful with fallback + retry
domain: tactical
task_id: indexar-squad
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

# Task: Indexar Squad

## Metadata
```yaml
id: indexar-squad
name: Indexar Squad no Registry
version: 1.0.0
executor: indexador-squads
workflow: atualizar-indice
estimated_time: 30s
```

## Purpose

Descobrir, analisar e indexar um squad no SQUAD-REGISTRY, extraindo suas capacidades, domínio, problemas e keywords para habilitar matching futuro.

---

## Input Requirements

| Campo | Tipo | Obrigatório | Exemplo |
|-------|------|-------------|---------|
| squad_path | string | Sim | "squads/novo-squad" |
| evento | string | Sim | "criado" / "atualizado" / "removido" |
| force_reindex | boolean | Não | false |

## Trigger

```yaml
trigger:
  type: event
  events:
    - "Squad criado"
    - "Squad atualizado"
    - "Reindexação manual"
    - "Startup do sistema"
```

---

## Execution Flow

### Fase 1: Descoberta (5s)

**Task 1.1: Ler Estrutura do Squad**
- Ler SQUAD.md e config.yaml
- Identificar agentes disponíveis
- Mapear workflows e capacidades

### Fase 2: Extração (15s)

**Task 2.1: Extrair Metadados**
```yaml
extrair:
  - nome
  - descrição
  - domínio
  - problemas_que_resolve
  - agentes (lista)
  - workflows (lista)
  - capacidades_especiais
  - prioridade
```

**Task 2.2: Gerar Keywords**
- Extrair de títulos e descrições
- Identificar termos técnicos
- Mapear sinônimos

**Task 2.3: Mapear Capacidades**
- Actions de cada agente
- Tipos de tarefa suportados
- Integrações disponíveis

### Fase 3: Indexação (10s)

**Task 3.1: Atualizar SQUAD-REGISTRY**
- Adicionar/atualizar entrada
- Calcular hash de versão
- Registrar timestamp

---

## Output Structure

```yaml
squad_indexado:
  id: "nome-do-squad"
  nome: "Nome Display do Squad"
  dominio: "área de atuação"

  problemas_que_resolve:
    - "problema 1"
    - "problema 2"

  agentes:
    - id: "agente-1"
      papel: "descrição do papel"
      tipos_tarefa: ["criar", "analisar"]
      prioridade: "P0"
    - id: "agente-2"
      # ...

  workflows:
    - id: "workflow-1"
      trigger: "descrição"
      output: "tipo de output"

  capacidades_especiais:
    - "CAPACIDADE_X"

  keywords:
    - "keyword1"
    - "keyword2"
    - "keyword3"

  metadata:
    versao: "1.0.0"
    criado_em: "YYYY-MM-DD"
    atualizado_em: "YYYY-MM-DD"
    hash: "abc123..."
```

---

## Quality Gates

### Gate 1: Estrutura
- [ ] SQUAD.md existe e é válido
- [ ] config.yaml existe e é válido
- [ ] Pelo menos 1 agente encontrado
- [ ] Domínio identificado

### Gate 2: Extração
- [ ] Nome extraído
- [ ] Problemas extraídos (>= 1)
- [ ] Keywords geradas (>= 3)
- [ ] Tipos de tarefa mapeados

### Gate 3: Indexação
- [ ] Entrada criada/atualizada no registry
- [ ] Hash de versão gerado
- [ ] Timestamp registrado

---

## Registry Entry Format

```markdown
### [nome-do-squad]

| Campo | Valor |
|-------|-------|
| ID | nome-do-squad |
| Domínio | [domínio] |
| Prioridade | [P0/P1/P2] |
| Versão | [X.X.X] |

**Problemas que Resolve:**
- [Problema 1]
- [Problema 2]

**Agentes:**
| Agente | Papel | Tipos de Tarefa |
|--------|-------|-----------------|
| [agente-1] | [papel] | criar, analisar |

**Keywords:**
`keyword1` `keyword2` `keyword3`

**Capacidades Especiais:**
- [CAPACIDADE_X] (se houver)

---
```

---

## Success Metrics

| Métrica | Alvo | Descrição |
|---------|------|-----------|
| Tempo indexação | < 30s | Por squad |
| Cobertura | 100% | Todos os squads indexados |
| Precisão keywords | > 90% | Keywords relevantes |
| Atualização | < 5min | Após mudança em squad |

---

## Example

### Input
```yaml
squad_path: "squads/content-ecosystem"
evento: "criado"
```

### Output
```yaml
squad_indexado:
  id: "youtube-content"
  nome: "YouTube Content"
  dominio: "content-production"

  problemas_que_resolve:
    - "Pesquisa fragmentada para criar conteúdo"
    - "Roteiros sem embasamento científico"
    - "Títulos que não convertem"
    - "Thumbnails amadoras"

  agentes:
    - id: "briefing-creator"
      papel: "Orchestrator"
      tipos_tarefa: ["criar", "sintetizar"]
      prioridade: "P0"
    - id: "roteirista"
      papel: "Script Writer"
      tipos_tarefa: ["criar", "otimizar"]
      prioridade: "P0"
    # ...

  workflows:
    - id: "criar-aula-completa"
      trigger: "Novo tópico de vídeo"
      output: "Todos os assets"

  keywords:
    - "youtube"
    - "vídeo"
    - "roteiro"
    - "thumbnail"
    - "título"
    - "conteúdo educacional"
    - "retenção"

  metadata:
    versao: "1.0.0"
    atualizado_em: "2026-02-04"
    hash: "x7f9a2..."

resultado:
  status: "indexado"
  acao: "criado"
  tempo: "12s"
```

## Integration

- **Squad:** orquestrador-global
- **Upstream:** *definir tasks que alimentam esta*
- **Downstream:** *definir tasks que esta alimenta*
