# CORTEX PROTOCOL v1.0

> **Propósito:** Sistema de governança que monitora dependências e ramificações de mudanças
> **Papel:** MONITORADOR - mantém consciência sistêmica do projeto
> **Criado:** 2025-12-20
> **Gatilho:** Sempre que um protocolo, comando ou estrutura for criado/modificado

---

## Conceito Central

O CORTEX é o "sistema nervoso central" do Mega Brain. Ele conhece todas as conexões entre arquivos e garante que mudanças em um ponto se propaguem corretamente para todos os pontos dependentes.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CORTEX PROTOCOL                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   NOVA MUDANÇA (protocolo, comando, estrutura)                              │
│        │                                                                    │
│        ▼                                                                    │
│   ┌────────────────────────────────────────┐                               │
│   │  1. CLASSIFICAR MUDANÇA                │                               │
│   │     Qual tipo? (protocolo/comando/     │                               │
│   │     estrutura/agente/script)           │                               │
│   └────────────────────────────────────────┘                               │
│        │                                                                    │
│        ▼                                                                    │
│   ┌────────────────────────────────────────┐                               │
│   │  2. CONSULTAR GRAFO DE DEPENDÊNCIAS    │                               │
│   │     Quem depende deste arquivo?        │                               │
│   │     Este arquivo depende de quem?      │                               │
│   └────────────────────────────────────────┘                               │
│        │                                                                    │
│        ▼                                                                    │
│   ┌────────────────────────────────────────┐                               │
│   │  3. GERAR CHECKLIST DE INTEGRAÇÃO      │                               │
│   │     Lista arquivos que precisam        │                               │
│   │     referenciar/atualizar              │                               │
│   └────────────────────────────────────────┘                               │
│        │                                                                    │
│        ▼                                                                    │
│   ┌────────────────────────────────────────┐                               │
│   │  4. EXECUTAR INTEGRAÇÃO                │                               │
│   │     Aplicar mudanças em cascata        │                               │
│   │     Atualizar referências              │                               │
│   └────────────────────────────────────────┘                               │
│        │                                                                    │
│        ▼                                                                    │
│   ┌────────────────────────────────────────┐                               │
│   │  5. VALIDAR E REGISTRAR                │                               │
│   │     Verificar integridade              │                               │
│   │     Atualizar EVOLUTION-LOG            │                               │
│   └────────────────────────────────────────┘                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Grafo de Dependências do Sistema

### Hierarquia de Arquivos Críticos

```
CLAUDE.md (ROOT - Regra máxima)
    │
    ├── system/SESSION-STATE.md
    │   └─ IMPACTS: Estado atual, versão, resumo sessões
    │
    ├── system/EVOLUTION-LOG.md
    │   └─ IMPACTS: Histórico de mudanças, changelog
    │
    └── agents/protocols/
        ├── PIPELINE-JARVIS-v2.1.md (Master Pipeline)
        │   ├── DEPENDS_ON: Todos os PROMPT-*.md
        │   └── IMPACTS: process-jarvis.md, jarvis-full.md
        │
        ├── ENFORCEMENT.md
        │   └── IMPACTS: Todos os protocolos de escrita
        │
        ├── NARRATIVE-METABOLISM-PROTOCOL.md
        │   ├── DEPENDS_ON: Nenhum
        │   └── IMPACTS: DOSSIER-COMPILATION, SOURCES-COMPILATION,
        │                process-jarvis.md, jarvis-full.md
        │
        ├── DOSSIER-COMPILATION-PROTOCOL.md
        │   ├── DEPENDS_ON: NARRATIVE-METABOLISM-PROTOCOL
        │   └── IMPACTS: process-jarvis.md, DOSSIERS/
        │
        ├── SOURCES-COMPILATION-PROTOCOL.md
        │   ├── DEPENDS_ON: NARRATIVE-METABOLISM-PROTOCOL
        │   └── IMPACTS: process-jarvis.md, SOURCES/
        │
        ├── EPISTEMIC-PROTOCOL.md
        │   └── IMPACTS: Todos os AGENT-*.md
        │
        └── WAR-ROOM-DEBATE-PROTOCOL.md
            ├── DEPENDS_ON: EPISTEMIC-PROTOCOL (confiança), LOG-TEMPLATES
            └── IMPACTS: process-jarvis.md, War Room Sessions, logs/EXECUTION/
```

### Comandos e suas Dependências

```
.claude/commands/
    │
    ├── jarvis-full.md
    │   ├── DEPENDS_ON: ingest.md, process-jarvis.md
    │   ├── DEPENDS_ON: NARRATIVE-METABOLISM-PROTOCOL.md
    │   └── IMPACTS: inbox → knowledge pipeline
    │
    ├── process-jarvis.md
    │   ├── DEPENDS_ON: PIPELINE-JARVIS-v2.1.md
    │   ├── DEPENDS_ON: ENFORCEMENT.md
    │   ├── DEPENDS_ON: NARRATIVE-METABOLISM-PROTOCOL.md
    │   ├── DEPENDS_ON: DOSSIER-COMPILATION-PROTOCOL.md
    │   ├── DEPENDS_ON: SOURCES-COMPILATION-PROTOCOL.md
    │   └── IMPACTS: processing, knowledge
    │
    ├── ingest.md
    │   └── IMPACTS: inbox
    │
    ├── extract-knowledge.md
    │   ├── DEPENDS_ON: process-jarvis.md
    │   └── IMPACTS: knowledge
    │
    └── rag-search.md
        ├── DEPENDS_ON: scripts/rag_query.py
        └── IMPACTS: Consultas semânticas
```

### Agentes e suas Dependências (INTEGRIDADE INVIOLÁVEL)

```
agents/cargo/{NIVEL}/{CARGO}/
    │
    ├── AGENT.md (Prompt Principal)
    │   │
    │   ├── DEPENDS_ON (FONTES PRIMÁRIAS - OBRIGATÓRIO):
    │   │   ├── SOUL.md ─────────→ Seções: QUEM SOU, COMO FALO, O QUE ESPERAR
    │   │   ├── MEMORY.md ───────→ Seções: O QUE JÁ SEI, DECISÕES PADRÃO
    │   │   └── DNA-CONFIG.yaml ─→ Seções: MINHA FORMAÇÃO, PROFUNDIDADE
    │   │
    │   ├── DEPENDS_ON (KNOWLEDGE - Mapa Navegação):
    │   │   ├── /knowledge/dna/persons/{fontes}/*.yaml
    │   │   ├── /knowledge/SOURCES/{fontes}/*.md
    │   │   └── /knowledge/dossiers/{PERSONS|THEMES}/*.md
    │   │
    │   └── FOLLOWS: AGENT-INTEGRITY-PROTOCOL.md (INQUEBRÁVEL)
    │
    ├── SOUL.md
    │   └── IMPACTS: AGENT.md (QUEM SOU, COMO FALO, O QUE ESPERAR)
    │
    ├── MEMORY.md
    │   └── IMPACTS: AGENT.md (O QUE JÁ SEI, DECISÕES PADRÃO, contagens)
    │
    └── DNA-CONFIG.yaml
        └── IMPACTS: AGENT.md (MINHA FORMAÇÃO, fontes, pesos)

REGRA DE PROPAGAÇÃO:
    QUANDO SOUL.md muda    → AGENT.md seções dependentes DEVEM atualizar
    QUANDO MEMORY.md muda  → AGENT.md contagens e decisões DEVEM atualizar
    QUANDO DNA-CONFIG muda → AGENT.md formação e navegação DEVEM atualizar

VALIDAÇÃO OBRIGATÓRIA (AGENT-INTEGRITY-PROTOCOL):
    □ Todo texto em AGENT.md tem ^[FONTE:arquivo:linha]
    □ Todos números são derivados (não escritos)
    □ Texto é citação direta, não paráfrase
    □ Arquivos listados existem no filesystem
```

### Estrutura Legada de Agentes

```
agents/
    │
    ├── SALES/
    │   ├── AGENT-CLOSER.md
    │   │   ├── DEPENDS_ON: EPISTEMIC-PROTOCOL.md
    │   │   ├── DEPENDS_ON: DOSSIERS/persons/DOSSIER-COLE-GORDON.md
    │   │   └── MEMORY: MEMORY-CLOSER.md
    │   │
    │   └── (outros agentes seguem mesmo padrão)
    │
    ├── ORG-LIVE/ (Cargos Humanos - Sistema Isolado)
    │   ├── ROLES/
    │   │   └── ROLE-{CARGO}.md
    │   │       ├── DEPENDS_ON: DOSSIERS/THEMES/DOSSIER-{TEMA}.md
    │   │       ├── DEPENDS_ON: DOSSIERS/persons/DOSSIER-{PESSOA}.md
    │   │       ├── DEPENDS_ON: ORG-LIVE-ENRICHMENT-PROTOCOL.md
    │   │       └── MEMORY: MEMORY/MEMORY-{CARGO}.md
    │   │
    │   ├── JDS/
    │   │   └── JD-{CARGO}.md
    │   │       └── DEPENDS_ON: ROLES/ROLE-{CARGO}.md
    │   │
    │   ├── MEMORY/
    │   │   └── MEMORY-{CARGO}.md
    │   │       └── DEPENDS_ON: ROLES/ROLE-{CARGO}.md
    │   │
    │   ├── ORG/
    │   │   ├── ORG-CHART.md
    │   │   │   └── DEPENDS_ON: Todos os ROLE-*.md
    │   │   ├── ORG-PROTOCOL.md
    │   │   └── SCALING-TRIGGERS.md
    │   │
    │   └── AGENT-ROLE-MAPPING.md
    │       ├── DEPENDS_ON: Todos os AGENT-*.md
    │       └── DEPENDS_ON: Todos os ROLE-*.md
    │
    └── PROTOCOLS/
        ├── ORG-LIVE-ENRICHMENT-PROTOCOL.md
        │   ├── IMPACTS: ORG-LIVE/ROLES/*.md
        │   ├── IMPACTS: ORG-LIVE/MEMORY/*.md
        │   └── IMPACTS: process-jarvis.md (Phase 8.1.6)
        │
        └── (outros protocolos já listados)
```

---

## Matriz de Impacto por Tipo de Mudança

### Quando CRIAR novo protocolo:

| Arquivo a Atualizar | Seção | Ação |
|---------------------|-------|------|
| process-jarvis.md | Header + Fase relevante + Referências | Adicionar referência |
| jarvis-full.md | Se afeta pipeline completo | Adicionar nota |
| CLAUDE.md | Se afeta regras globais | Atualizar seção |
| SESSION-STATE.md | Última sessão | Registrar criação |
| EVOLUTION-LOG.md | Changelog | Documentar |

### Quando MODIFICAR protocolo existente:

| Arquivo a Verificar | Critério |
|---------------------|----------|
| Todos que têm DEPENDS_ON deste protocolo | Verificar compatibilidade |
| Comandos que usam este protocolo | Atualizar versão/comportamento |
| Agentes que seguem este protocolo | Verificar alinhamento |

### Quando CRIAR novo comando:

| Arquivo a Atualizar | Ação |
|---------------------|------|
| CLAUDE.md | Adicionar à tabela de comandos |
| README.md | Adicionar à documentação |
| SESSION-STATE.md | Registrar criação |
| EVOLUTION-LOG.md | Documentar |

### Quando CRIAR novo agente:

| Arquivo a Atualizar | Ação |
|---------------------|------|
| CLAUDE.md | Adicionar à tabela de agentes |
| README.md | Adicionar à documentação |
| agents/DISCOVERY/ROLE-TRACKING.md | Verificar threshold |
| SESSION-STATE.md | Registrar criação |
| EVOLUTION-LOG.md | Documentar |
| MEMORY-{AGENTE}.md | Criar arquivo de memória |
| agents/ORG-LIVE/AGENT-ROLE-MAPPING.md | Atualizar paridade Agent↔Role |

### Quando CRIAR/MODIFICAR ORG-LIVE (Cargo Humano):

| Arquivo a Atualizar | Ação |
|---------------------|------|
| ROLE-{CARGO}.md | Criar/atualizar definição do cargo |
| JD-{CARGO}.md | Criar/atualizar Job Description |
| MEMORY-{CARGO}.md (ORG-LIVE) | Criar/atualizar memória do cargo |
| ORG-CHART.md | Atualizar organograma |
| AGENT-ROLE-MAPPING.md | Atualizar paridade Agent↔Role |
| chat.md | Verificar se dashboard mostra novo cargo |
| LOG-TEMPLATES.md | Verificar se logs mostram ORG-LIVE |
| SESSION-STATE.md | Registrar criação/modificação |
| EVOLUTION-LOG.md | Documentar mudança estrutural |

### Quando MODIFICAR estrutura ORG-LIVE:

| Arquivo a Verificar | Ação |
|---------------------|------|
| Todos ROLE-*.md | Verificar referências |
| Todos JD-*.md | Verificar referências |
| Todos MEMORY-*.md (ORG-LIVE) | Verificar referências |
| ORG-CHART.md | Atualizar hierarquia |
| SCALING-TRIGGERS.md | Verificar gatilhos |
| ORG-PROTOCOL.md | Verificar regras |
| process-jarvis.md | Verificar Phase 8.1.6 |
| LOG-TEMPLATES.md | Verificar seções ORG-LIVE |
| chat.md | Verificar dashboard |

### Quando MODIFICAR estrutura de pastas:

| Arquivo a Verificar | Ação |
|---------------------|------|
| CLAUDE.md | Atualizar Project Structure |
| .claude/settings.local.json | Atualizar env paths |
| .claude/commands/*.md | Verificar referências |
| agents/*.md | Verificar knowledge paths |
| scripts/*.py | Verificar paths hardcoded |

---

## Checklist Generator

### Template: Novo Protocolo

```markdown
## CHECKLIST DE INTEGRAÇÃO: [NOME-PROTOCOLO]

### Pré-Requisitos
- [ ] Protocolo está em /agents/protocols/
- [ ] Tem versão no header (v1.0.0)
- [ ] Tem data de criação

### Integrações Obrigatórias
- [ ] process-jarvis.md: Adicionar referência no header
- [ ] process-jarvis.md: Adicionar na fase relevante
- [ ] process-jarvis.md: Adicionar na tabela de referências
- [ ] jarvis-full.md: Adicionar nota se afeta pipeline completo
- [ ] CLAUDE.md: Atualizar se afeta regras globais

### Registros
- [ ] SESSION-STATE.md: Atualizar última sessão
- [ ] EVOLUTION-LOG.md: Adicionar ao changelog
- [ ] Incrementar versão do sistema se necessário

### Validação
- [ ] Testar execução do protocolo
- [ ] Verificar que nenhuma referência ficou órfã
```

### Template: Novo Comando

```markdown
## CHECKLIST DE INTEGRAÇÃO: [NOME-COMANDO]

### Pré-Requisitos
- [ ] Comando está em /.claude/commands/
- [ ] Tem YAML frontmatter (description, argument-hint)
- [ ] Tem versão documentada

### Integrações Obrigatórias
- [ ] CLAUDE.md: Adicionar à tabela "Available Commands"
- [ ] README.md: Adicionar à documentação de comandos

### Dependências
- [ ] Listar protocolos que este comando usa
- [ ] Verificar que todos os protocolos referenciados existem

### Registros
- [ ] SESSION-STATE.md: Atualizar última sessão
- [ ] EVOLUTION-LOG.md: Adicionar ao changelog
```

### Template: Novo Agente

```markdown
## CHECKLIST DE INTEGRAÇÃO: [NOME-AGENTE]

### Pré-Requisitos
- [ ] AGENT-{NOME}.md em /agents/{CATEGORIA}/
- [ ] MEMORY-{NOME}.md criado
- [ ] Segue EPISTEMIC-PROTOCOL.md

### Integrações Obrigatórias
- [ ] CLAUDE.md: Adicionar à tabela de agentes
- [ ] README.md: Adicionar à documentação
- [ ] ROLE-TRACKING.md: Verificar/atualizar threshold

### Knowledge Base
- [ ] Listar DOSSIERS que o agente deve conhecer
- [ ] Listar SOURCES relevantes
- [ ] Configurar hierarquia de knowledge no AGENT-*.md

### Registros
- [ ] SESSION-STATE.md: Atualizar última sessão
- [ ] EVOLUTION-LOG.md: Adicionar ao changelog
```

---

## Regras de Execução Automática

### GATILHO: Criar Arquivo Novo

```
WHEN file_created IN [
    /agents/protocols/*.md,
    /.claude/commands/*.md,
    /agents/*/*.md
]:

    1. CLASSIFICAR tipo (protocolo/comando/agente)
    2. CARREGAR checklist correspondente
    3. EXECUTAR cada item do checklist
    4. VALIDAR integridade do sistema
    5. REGISTRAR em EVOLUTION-LOG
```

### GATILHO: Modificar Arquivo Existente

```
WHEN file_modified IN [
    /agents/protocols/*.md,
    /.claude/commands/*.md,
    /CLAUDE.md
]:

    1. IDENTIFICAR arquivos dependentes (via grafo)
    2. VERIFICAR se dependentes precisam atualização
    3. PROPAGAR mudanças necessárias
    4. INCREMENTAR versão se breaking change
    5. REGISTRAR em EVOLUTION-LOG
```

### GATILHO: Mudança Estrutural

```
WHEN folder_renamed OR folder_moved:

    1. LISTAR todos os arquivos que referenciam este path
    2. ATUALIZAR referências em cada arquivo
    3. VERIFICAR integridade de links
    4. ATUALIZAR CLAUDE.md Project Structure
    5. REGISTRAR em EVOLUTION-LOG
```

---

## Validação de Integridade

### Health Check do Sistema

Executar periodicamente ou após mudanças significativas:

```
[ ] Todos os protocolos em /agents/protocols/ estão referenciados?
[ ] Todos os comandos em /.claude/commands/ estão documentados em CLAUDE.md?
[ ] Todos os agentes em /agents/ estão documentados?
[ ] Nenhum arquivo referencia path inexistente?
[ ] SESSION-STATE.md está atualizado?
[ ] Versão do sistema está consistente em todos os arquivos?
```

### Detecção de Inconsistências

Sinais de que o CORTEX não foi seguido:

| Sintoma | Causa Provável | Ação |
|---------|----------------|------|
| Protocolo não aplicado | Faltou integração | Rodar checklist retroativo |
| Comando não funciona | Dependência não atualizada | Verificar grafo |
| Agente dá resposta incorreta | MEMORY desatualizada | Sincronizar |
| Path não encontrado | Estrutura mudou sem propagação | Atualizar referências |

---

## Integração com Fluxo de Trabalho

### Ao Iniciar Sessão

```
1. LER SESSION-STATE.md (estado atual)
2. LER EVOLUTION-LOG.md (última versão)
3. VERIFICAR se há pendências do CORTEX
4. SE houver → resolver antes de continuar
```

### Ao Criar/Modificar Arquivo de Sistema

```
1. ANTES de salvar → consultar CORTEX-PROTOCOL
2. IDENTIFICAR tipo de mudança
3. CARREGAR checklist apropriado
4. EXECUTAR checklist COMPLETAMENTE
5. SÓ ENTÃO considerar tarefa concluída
```

### Ao Encerrar Sessão

```
1. VERIFICAR se todas as integrações foram feitas
2. ATUALIZAR SESSION-STATE.md
3. ATUALIZAR EVOLUTION-LOG.md se houve mudança estrutural
4. VALIDAR integridade do sistema
```

---

## Referência Rápida: Onde Atualizar

| Tipo de Mudança | Arquivos a Atualizar |
|-----------------|----------------------|
| Novo protocolo | process-jarvis.md, jarvis-full.md (se aplicável), SESSION-STATE, EVOLUTION-LOG |
| Modificar protocolo | Dependentes (via grafo), SESSION-STATE, EVOLUTION-LOG |
| Novo comando | CLAUDE.md, README.md, SESSION-STATE, EVOLUTION-LOG |
| Novo agente IA | CLAUDE.md, README.md, ROLE-TRACKING, MEMORY-*.md, AGENT-ROLE-MAPPING, SESSION-STATE, EVOLUTION-LOG |
| Novo cargo ORG-LIVE | ROLE-*.md, JD-*.md, MEMORY-*.md (ORG-LIVE), ORG-CHART, AGENT-ROLE-MAPPING, chat.md, LOG-TEMPLATES, SESSION-STATE, EVOLUTION-LOG |
| Modificar ORG-LIVE | process-jarvis.md (8.1.6), LOG-TEMPLATES, chat.md, dependentes via grafo |
| Mudança estrutural | CLAUDE.md, todos com referência ao path, .claude/settings.local.json, chat.md, LOG-TEMPLATES |
| Nova fonte processada | SESSION-STATE, MEMORY dos agentes relevantes, ORG-LIVE/MEMORY (se aplicável) |

---

## Meta-Regra

> **O CORTEX PROTOCOL é AUTOAPLICÁVEL.**
>
> Este próprio protocolo deve ser:
> 1. Referenciado em CLAUDE.md
> 2. Seguido sempre que qualquer mudança for feita
> 3. Atualizado quando novas categorias de mudança surgirem
>
> **Se você está lendo isso, deve seguir este protocolo AGORA.**

---

*CORTEX Protocol v1.0 — Sistema de Governança Sistêmica*
*Mega Brain System v3.23.0*
