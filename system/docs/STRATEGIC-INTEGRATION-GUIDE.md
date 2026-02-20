# MEGA BRAIN - GUIA ESTRATEGICO DE INTEGRACAO

> **Documento para IAs:** Este guia fornece visao completa do sistema Mega Brain para integracao estrategica.
> **Versao:** 1.0.0
> **Data:** 2025-12-22
> **Sistema:** v3.29.0

---

## 1. VISAO GERAL DO SISTEMA

### 1.1 O Que E o Mega Brain

Mega Brain e um **sistema de gestao de conhecimento** que transforma conteudo bruto (videos, PDFs, transcricoes) em **conhecimento acionavel** atraves de:

1. **Pipeline de Processamento Semantico** (Jarvis) - 8 fases
2. **Sistema Multi-Agente** - 12 agentes especializados + memorias
3. **Organizacao Viva (ORG-LIVE)** - Cargos humanos documentados
4. **RAG (Retrieval Augmented Generation)** - Busca semantica
5. **GitHub Actions** - Auto-review de codigo

### 1.2 Proposito

Construir **playbooks de vendas B2B high-ticket** ($10k+) a partir de especialistas como:
- Alex Hormozi
- Cole Gordon
- Jordan Lee (AI Business)

### 1.3 Arquitetura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MEGA BRAIN v3.29.0                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  inbox    │    │processing │    │ knowledge │    │  agents   │   │
│  │  (Brutos)    │───▶│   (Jarvis)   │───▶│  (Extraido)  │───▶│(Especializ.) │   │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘   │
│         │                   │                   │                   │            │
│         │                   │                   │                   │            │
│         ▼                   ▼                   ▼                   ▼            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  Transcricao │    │   Chunks     │    │   DOSSIERS   │    │   MEMORY     │   │
│  │  YouTube/    │    │   Insights   │    │   SOURCES    │    │   Por Agente │   │
│  │  AssemblyAI  │    │   Narrativas │    │              │    │              │   │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                           system (Governanca)                          │   │
│  │  SESSION-STATE.md | EVOLUTION-LOG.md | REGISTRY | GLOSSARY | LOGS        │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                           SCRIPTS (Automacao)                             │   │
│  │  rag_index.py | rag_query.py | file_registry.py | decision_logger.py     │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. ESTRUTURA DE PASTAS

```
/Mega Brain/
├── .claude/                          # Configuracao Claude Code
│   ├── commands/                     # 21 slash commands disponiveis
│   │   ├── process-jarvis.md         # Pipeline principal (43KB)
│   │   ├── chat.md                   # Abertura de sessao (34KB)
│   │   ├── extract-knowledge.md      # Extracao de conhecimento
│   │   ├── scan-inbox.md             # Escanear pendencias
│   │   ├── rag-search.md             # Busca semantica
│   │   ├── ingest.md                 # Ingerir material novo
│   │   ├── loops.md                  # Gerenciar Open Loops
│   │   └── ...                       # Outros comandos
│   ├── agents/                       # Subagentes Claude Code
│   │   ├── apex.md                   # Meta-agente de prompts
│   │   └── b2b-sales-expert.md       # Analise de conteudo
│   └── settings.local.json           # Configuracoes locais
│
├── .github/workflows/                # GitHub Actions
│   ├── claude.yml                    # Auto-review + @claude mentions
│   └── claude-code-review.yml        # Review dedicado
│
├── inbox/                         # Arquivos brutos (entrada)
│   ├── ALEX HORMOZI/
│   ├── COLE GORDON/
│   ├── JORDAN LEE (AI BUSINESS)/
│   ├── SETTERLUN (SETTERLUN UNIVERSITY)/
│   └── ...                           # Outras fontes
│
├── processing/                    # Pipeline Jarvis (intermediario)
│   ├── chunks/                       # Fase 2: Quebra semantica
│   │   └── CHUNKS-STATE.json         # 260 chunks acumulados
│   ├── canonical/                    # Fase 3: Mapa de entidades
│   │   └── CANONICAL-MAP.json        # 11 pessoas, 6 conceitos
│   ├── insights/                     # Fase 4: Insights priorizados
│   │   └── INSIGHTS-STATE.json       # 157 insights (HIGH/MEDIUM/LOW)
│   └── narratives/                   # Fase 5: Narrativas consolidadas
│       └── NARRATIVES-STATE.json     # 8 pessoas narrativas
│
├── knowledge/                     # Conhecimento extraido (saida)
│   ├── DOSSIERS/                     # Consolidacao MULTI-FONTE
│   │   ├── PERSONS/                  # 8 dossies de pessoas
│   │   │   ├── DOSSIER-COLE-GORDON.md
│   │   │   ├── DOSSIER-ALEX-HORMOZI.md
│   │   │   ├── DOSSIER-JORDAN-LEE.md
│   │   │   └── ...
│   │   └── THEMES/                   # 10 dossies de temas
│   │       ├── DOSSIER-01-ESTRUTURA-TIME.md
│   │       ├── DOSSIER-02-PROCESSO-VENDAS.md
│   │       └── ...
│   ├── SOURCES/                      # Consolidacao UNI-FONTE
│   │   ├── ALEX-HORMOZI/             # Tudo de 1 pessoa por tema
│   │   ├── COLE-GORDON/
│   │   └── ...
│   └── archive/                      # Estrutura antiga (backup)
│
├── knowledge/playbooks/                      # Playbooks gerados
│   ├── drafts/
│   └── final/
│
├── system/                        # Governanca do sistema
│   ├── SESSION-STATE.md              # Estado atual (LEIA PRIMEIRO)
│   ├── EVOLUTION-LOG.md              # Historico de mudancas
│   ├── OPEN-LOOPS.json               # Tarefas pendentes
│   ├── REGISTRY/                     # File registry (MD5, timestamps)
│   ├── GLOSSARY/                     # Terminologia padronizada
│   ├── LOGS/                         # Decision logs
│   ├── TRACES/                       # War Room traces
│   └── DOCS/                         # Documentacao (este arquivo)
│
├── agents/                        # Sistema multi-agente
│   ├── C-LEVEL/                      # 4 agentes estrategicos
│   │   ├── AGENT-CRO.md + MEMORY
│   │   ├── AGENT-CFO.md + MEMORY
│   │   ├── AGENT-CMO.md + MEMORY
│   │   └── AGENT-COO.md + MEMORY
│   ├── SALES/                        # 8 agentes operacionais
│   │   ├── AGENT-CLOSER.md + MEMORY
│   │   ├── AGENT-BDR.md + MEMORY
│   │   ├── AGENT-SDS.md + MEMORY
│   │   ├── AGENT-LNS.md + MEMORY
│   │   ├── AGENT-SALES-MANAGER.md + MEMORY
│   │   ├── AGENT-SALES-LEAD.md + MEMORY
│   │   ├── AGENT-SALES-COORDINATOR.md + MEMORY
│   │   └── AGENT-CUSTOMER-SUCCESS.md + MEMORY
│   ├── ORG-LIVE/                     # Cargos humanos (nao IA)
│   │   ├── ROLES/                    # 13 definicoes de cargo
│   │   ├── JDS/                      # 13 Job Descriptions
│   │   ├── MEMORY/                   # 14 memorias de cargo
│   │   ├── ORG/                      # Organograma vivo
│   │   └── AGENT-ROLE-MAPPING.md     # Mapeamento IA → Humano
│   ├── PROTOCOLS/                    # 19 protocolos
│   │   ├── PIPELINE-JARVIS-v2.1.md   # Pipeline master
│   │   ├── ENFORCEMENT.md            # Regras de bloqueio
│   │   ├── EPISTEMIC-PROTOCOL.md     # Anti-alucinacao
│   │   ├── CORTEX-PROTOCOL.md        # Governanca sistemica
│   │   └── ...
│   └── MASTER-AGENT.md               # Orquestrador
│
├── logs/                          # Logs de execucao
│   ├── AUDIT/                        # audit.jsonl
│   ├── EXECUTION/                    # Relatorios por execucao
│   └── DIGEST/                       # System digests
│
├── scripts/                          # Automacao Python
│   ├── rag/                          # Modulo RAG completo
│   ├── rag_index.py                  # Indexar documentos
│   ├── rag_query.py                  # Busca semantica
│   ├── file_registry.py              # Registry de arquivos
│   ├── decision_logger.py            # Log de decisoes
│   └── trace_generator.py            # War Room traces
│
├── CLAUDE.md                         # Instrucoes para IA (PRD)
└── README.md                         # Documentacao publica
```

---

## 3. PIPELINE JARVIS (PROCESSAMENTO SEMANTICO)

### 3.1 Visao Geral

O Pipeline Jarvis transforma conteudo bruto em conhecimento estruturado atraves de **8 fases obrigatorias**.

```
inbox (brutos)
     │
     │ [PHASE 1: Initialization]
     │ Validar arquivo, extrair metadados, carregar estados
     ▼
     │ [PHASE 2: Chunking]
     │ Quebrar em chunks de ~300 palavras
     ▼
processing/chunks/
     │
     │ [PHASE 3: Entity Resolution]
     │ Resolver entidades canonicas (pessoas, conceitos)
     ▼
processing/canonical/
     │
     │ [PHASE 4: Insight Extraction]
     │ Extrair insights HIGH/MEDIUM/LOW com rastreabilidade
     ▼
processing/insights/
     │
     │ [PHASE 5: Narrative Synthesis]
     │ Sintetizar narrativas por pessoa/tema
     ▼
processing/narratives/
     │
     │ [PHASE 6: Dossier Compilation]
     │ Compilar DOSSIERs e SOURCES
     ▼
knowledge/dossiers/ + SOURCES/
     │
     │ [PHASE 7: Agent Enrichment]
     │ Alimentar AGENT-*.md + MEMORY-*.md
     ▼
agents/
     │
     │ [PHASE 8: Finalization]
     │ RAG Index, File Registry, SESSION-STATE, Role Tracking, ORG-LIVE
     ▼
Sistema 100% atualizado
```

### 3.2 Como Iniciar o Pipeline

**Comando:**
```
/process-jarvis inbox/PASTA/arquivo.txt
```

**Ou via YouTube:**
```
/process-video https://www.youtube.com/watch?v=VIDEO_ID
```

### 3.3 Checkpoints e Paradas Humanas

| Fase | Checkpoint | Parada Humana? |
|------|-----------|----------------|
| 1 | PRE-1 + POST-1 | NAO |
| 2 | PRE-2 + POST-2 | NAO |
| 3 | PRE-3 + POST-3 | SIM se review_queue > 0 |
| 4 | PRE-4 + POST-4 | NAO |
| 5 | PRE-5 + POST-5 | NAO |
| 6 | PRE-6 + POST-6 | NAO |
| 7 | User Prompt | **SIM** - Pergunta se alimentar agentes |
| 8 | CHECKPOINT 7 (9 items) | NAO |

### 3.4 Arquivos de Estado (JSON)

| Arquivo | Conteudo | Acumulado |
|---------|----------|-----------|
| CHUNKS-STATE.json | Chunks semanticos | 260 |
| CANONICAL-MAP.json | Entidades canonicas | 11 pessoas, 6 conceitos |
| INSIGHTS-STATE.json | Insights priorizados | 157 |
| NARRATIVES-STATE.json | Narrativas consolidadas | 8 pessoas |

---

## 4. SISTEMA MULTI-AGENTE

### 4.1 Agentes Disponiveis

#### C-Level (Estrategico)

| Agente | Responsabilidade | Fontes Principais |
|--------|------------------|-------------------|
| **CRO** | Revenue, ofertas, pricing, metodologias | MM001, SS001 |
| **CFO** | Financas, margens, unit economics | MM001, SU020-30 |

#### Sales (Operacional)

| Agente | Responsabilidade | Fontes Principais |
|--------|------------------|-------------------|
| **SDS** | Qualificacao, Discovery, ICP triplice | SS001, CG001 |
| **LNS** | Nurture, Show Rate, Sales Farming | CG002-004 |
| **SALES-LEAD** | Player-coach, coaching operacional | CG003 |
| **SALES-COORDINATOR** | Admin, CRM, atribuicao leads | CG003 |

### 4.2 Estrutura de Cada Agente

```
AGENT-{NOME}.md          # Definicao do papel (Job Description)
├── Responsabilidades
├── Frameworks que domina
├── Decision trees
├── Quando acionar
└── Para quem escala

AGENT-{NOME}-MEMORY.md   # Memoria do agente (Team Agreement)
├── Knowledge Base Acumulada
├── Decisoes tomadas
├── Precedentes
├── Calibracao BR
└── Fontes consultadas
```

### 4.3 Hierarquia de Decisao

```
NIVEL 1: AUTONOMO
└── Decisao existe na MEMORY, afeta so sua area, baixo risco
    → Agente decide sozinho

NIVEL 2: CONSULTA
└── Precisa input de outra area, sem conflito
    → Consulta entre agentes, logado em decision_logger

NIVEL 3: WAR ROOM
└── Multiplas areas, sem precedente, alto impacto
    → Escalado para War Room, trace gerado

NIVEL 4: LIDERANCA (Override)
└── Empate, excecao, mudanca estrategica
    → Humano decide
```

---

## 5. ORG-LIVE (ORGANIZACAO VIVA)

### 5.1 O Que E

ORG-LIVE e a representacao de **cargos humanos** (nao agentes IA) com documentacao completa para contratacao e gestao.

### 5.2 Estrutura

```
agents/ORG-LIVE/
├── ROLES/                    # 13 definicoes de cargo
│   ├── ROLE-CLOSER-CHEFE.md  # Cargo hibrido (supervisao)
│   ├── ROLE-CLOSER.md
│   ├── ROLE-SDR.md
│   ├── ROLE-BDR.md
│   ├── ROLE-LNS.md
│   ├── ROLE-SALES-MANAGER.md
│   ├── ROLE-SALES-LEAD.md
│   ├── ROLE-SALES-COORDINATOR.md
│   ├── ROLE-CUSTOMER-SUCCESS.md
│   ├── ROLE-CRO.md
│   ├── ROLE-CFO.md
│   ├── ROLE-COO.md
│   └── ROLE-CMO.md
│
├── JDS/                      # Job Descriptions para contratacao
│   └── JD-{CARGO}.md         # Framework Founder First Hiring
│
├── MEMORY/                   # Memoria dos cargos
│   └── MEMORY-{CARGO}.md     # Conhecimento acumulado por cargo
│
├── ORG/                      # Organograma
│   ├── ORG-CHART.md          # Visual + fases (ATIVO/PLANEJADO/FUTURO)
│   ├── ORG-PROTOCOL.md       # Regras de alimentacao
│   └── SCALING-TRIGGERS.md   # Gatilhos de crescimento
│
└── AGENT-ROLE-MAPPING.md     # Mapeamento Agente IA → Cargo Humano
```

### 5.3 Paridade IA ↔ Humano

| Agente IA | Cargo Humano ORG-LIVE |
|-----------|----------------------|
| AGENT-CLOSER | ROLE-CLOSER, ROLE-CLOSER-CHEFE |
| AGENT-BDR | ROLE-BDR |
| AGENT-SDS | ROLE-SDR |
| AGENT-LNS | ROLE-LNS |
| AGENT-SALES-MANAGER | ROLE-SALES-MANAGER |
| AGENT-CRO | ROLE-CRO |
| AGENT-CFO | ROLE-CFO |
| AGENT-CMO | ROLE-CMO |
| AGENT-COO | ROLE-COO |

---

## 6. COMANDOS DISPONIVEIS

### 6.1 Comandos Principais

| Comando | Funcao | Parada Humana |
|---------|--------|---------------|
| `/chat` | Abre sessao com dashboard completo | NAO |
| `/process-jarvis [path]` | Pipeline completo para arquivo | SIM (Phase 7) |
| `/process-video [URL]` | Processa video YouTube | SIM |
| `/extract-knowledge [path]` | Extrai conhecimento de transcricao | NAO |
| `/scan-inbox` | Escaneia pendencias no INBOX | NAO |
| `/rag-search [query]` | Busca semantica na knowledge base | NAO |

### 6.2 Comandos de Monitoramento

| Comando | Funcao |
|---------|--------|
| `/system-digest` | Diagnostico completo do sistema |
| `/log [tipo]` | Visualiza logs (execution, digest, roles, etc.) |
| `/agents` | Status dos agentes e MEMORYs |
| `/dossiers` | Status dos dossies |
| `/inbox` | Lista arquivos pendentes |
| `/loops` | Gerenciador de Open Loops |
| `/config` | Configuracoes do sistema |

### 6.3 Comandos de Processamento em Lote

| Comando | Funcao |
|---------|--------|
| `/process-inbox` | Processa multiplos arquivos do INBOX |
| `/jarvis-full` | Pipeline completo sem paradas |
| `/jarvis-control [cmd]` | Controle durante checkpoints (continue/abort/skip) |

### 6.4 Comandos de Integracao

| Comando | Funcao |
|---------|--------|
| `/ingest [URL/path]` | Ingere material com metadados |
| `/ler-drive [resource]` | Le recursos do Google Drive via MCP |
| `/create-agent [role]` | Cria novo agente quando threshold atingido |

---

## 7. FERRAMENTAS CLI (SCRIPTS)

### 7.1 RAG (Busca Semantica)

```bash
# Indexar knowledge base
python scripts/rag_index.py --knowledge

# Indexar tudo
python scripts/rag_index.py --full

# Forcar reindexacao
python scripts/rag_index.py --knowledge --force

# Buscar
python scripts/rag_query.py "CLOSER framework" --top 5

# Status do indice
python scripts/rag_status.py
```

**Tecnologias:** ChromaDB (vector DB) + Voyage AI (embeddings)

### 7.2 File Registry

```bash
# Escanear todos os arquivos
python scripts/file_registry.py --scan

# Verificar se arquivo mudou
python scripts/file_registry.py --check "inbox/arquivo.txt"

# Estatisticas
python scripts/file_registry.py --status
```

### 7.3 Decision Logger

```bash
# Log interativo
python scripts/decision_logger.py --log

# Log rapido
python scripts/decision_logger.py --decision "CRO->CFO: pricing | decisao | fonte"

# Buscar decisoes
python scripts/decision_logger.py --query "pricing"

# Estatisticas
python scripts/decision_logger.py --stats
```

### 7.4 Trace Generator (War Room)

```bash
# Nova sessao
python scripts/trace_generator.py --new "Titulo"

# Adicionar interacao
python scripts/trace_generator.py --add-interaction

# Iniciar War Room
python scripts/trace_generator.py --war-room

# Fechar sessao
python scripts/trace_generator.py --close
```

---

## 8. INTEGRACAO GITHUB

### 8.1 Workflows Ativos

```yaml
# claude.yml - Dois jobs:

# Job 1: Auto-review em PRs
on:
  pull_request:
    types: [opened, synchronize]
# Claude analisa codigo, encontra bugs, cria commits com correcoes

# Job 2: @claude mentions
on:
  issue_comment:
    types: [created]
# Responde quando mencionam @claude em PR/Issue
```

### 8.2 Permissoes Configuradas

- `contents: write` - Pode criar commits
- `pull-requests: write` - Pode comentar e modificar PRs
- `issues: write` - Pode responder Issues
- Ferramentas: `Edit(*), Write(*), Read(*), Bash(gh:*)`

### 8.3 Como Usar

```bash
# Criar branch e PR para review automatico
git checkout -b minha-feature
# ... fazer mudancas ...
git add .
git commit -m "Nova feature"
git push -u origin minha-feature
gh pr create --title "Minha feature"

# Claude revisa automaticamente e pode criar commits com correcoes

# Ou pedir correcao especifica:
# Comentar na PR: "@claude fix the bug in line 42"
```

---

## 9. PROTOCOLOS IMPORTANTES

### 9.1 EPISTEMIC-PROTOCOL (Anti-Alucinacao)

```markdown
## Principios:
1. FATO vs RECOMENDACAO - Sempre separar
2. Confidence Levels - ALTA/MEDIA/BAIXA obrigatorio
3. Circuit Breaker - Maximo 5 iteracoes antes de declarar "nao encontrado"
4. Epistemic Honesty - Nunca apresentar hipotese como fato

## Formato de Resposta:
FATOS:
- [FONTE:arquivo:linha] > "citacao exata"

RECOMENDACAO:
POSICAO: [minha recomendacao]
JUSTIFICATIVA: [porque]
CONFIANCA: [ALTA/MEDIA/BAIXA]

LIMITACOES:
- [o que nao sei]
```

### 9.2 CORTEX-PROTOCOL (Governanca Sistemica)

Garante que mudancas em protocolos se propaguem para todos os arquivos dependentes.

```
Mudanca em Protocolo → Atualizar:
├── process-jarvis.md
├── Comandos relevantes
├── LOG-TEMPLATES.md
├── SESSION-STATE.md
└── README.md
```

### 9.3 ENFORCEMENT (Bloqueio de Atalhos)

```
ANTES DE ESCREVER EM /knowledge/:
1. Verificar TODOS os checkpoints PRE passaram
2. Verificar TODOS os checkpoints POST passaram
3. SEM ATALHOS. SEM EXCECOES.
```

---

## 10. FLUXO DE SESSAO TIPICA

### 10.1 Inicio de Sessao

```
1. IA le /system/SESSION-STATE.md (OBRIGATORIO)
2. IA le /system/OPEN-LOOPS.json (loops pendentes)
3. Usuario pede tarefa
```

### 10.2 Processamento de Novo Conteudo

```
1. Usuario: /process-jarvis inbox/FONTE/arquivo.txt
2. Sistema executa 8 fases automaticamente
3. Parada em Phase 7: "Deseja alimentar agentes?"
4. Usuario aprova
5. Sistema finaliza (RAG, Registry, SESSION-STATE)
6. Sistema pergunta: "Deseja processar outro arquivo?"
```

### 10.3 Consulta a Agentes

```
Usuario: "Como Closer, como lidar com objecao de preco?"
Sistema:
1. Consulta MEMORY-CLOSER.md (precedentes)
2. Consulta AGENT-CLOSER.md (frameworks)
3. Se necessario, consulta DOSSIERs via RAG
4. Responde com FATOS + RECOMENDACAO + CONFIANCA
```

### 10.4 Fim de Sessao

```
Verificar antes de encerrar:
[ ] SESSION-STATE.md atualizado?
[ ] EVOLUTION-LOG.md atualizado (se mudanca estrutural)?
[ ] README.md atualizado (se novo agente/fonte)?
[ ] Versao incrementada?
```

---

## 11. ESTATISTICAS ATUAIS (v3.29.0)

| Metrica | Valor |
|---------|-------|
| Chunks processados | 260 |
| Insights extraidos | 157 (HIGH/MEDIUM/LOW) |
| Pessoas mapeadas | 11 |
| Dossies Pessoas | 8 |
| Dossies Temas | 10 |
| Agentes IA | 12 (8 SALES + 4 C-LEVEL) |
| MEMORYs | 12 |
| ROLEs ORG-LIVE | 13 |
| JDs | 13 |
| Comandos | 21 |
| Protocolos | 19 |
| Arquivos processados | 115+ |
| Tamanho total | ~105 MB |

---

## 12. PONTOS DE INTEGRACAO ESTRATEGICA

### 12.1 Para Adicionar Nova Fonte

1. Colocar arquivo em `inbox/{PESSOA} ({EMPRESA})/{TIPO}/`
2. Executar `/process-jarvis [path]`
3. Sistema processa automaticamente todas as 8 fases
4. Aprovar alimentacao de agentes em Phase 7

### 12.2 Para Consultar Conhecimento

1. `/rag-search [query]` - Busca semantica
2. Consultar agente especifico pelo papel
3. Consultar DOSSIER especifico

### 12.3 Para Criar Novo Agente

1. Sistema monitora mencoes via role-tracking
2. Quando threshold 10+ atingido, sistema sugere criacao
3. Executar `/create-agent [role]`

### 12.4 Para Integrar com Sistema Externo

1. Usar GitHub Actions para automacao de codigo
2. Usar MCP (Model Context Protocol) para conexoes:
   - `gdrive` - Google Drive
   - `context7` - Documentacao de bibliotecas
   - `ide` - VS Code diagnostics

---

## 13. ARQUIVOS CRITICOS (LEIA PRIMEIRO)

| Arquivo | Proposito | Prioridade |
|---------|-----------|------------|
| `/system/SESSION-STATE.md` | Estado atual, arquivos processados | 1 |
| `/system/OPEN-LOOPS.json` | Tarefas pendentes | 2 |
| `/CLAUDE.md` | Instrucoes operacionais (PRD) | 3 |
| `/agents/protocols/PIPELINE-JARVIS-v2.1.md` | Pipeline master | 4 |
| `/agents/protocols/ENFORCEMENT.md` | Regras de bloqueio | 5 |

---

## 14. CONVENCOES DO PROJETO

| Item | Convencao |
|------|-----------|
| Pastas | CAIXA ALTA |
| Idioma conteudo | Portugues BR |
| Idioma codigo | Ingles |
| Fontes | Sempre atribuidas com ID (CG003) |
| Numeros | Nunca arredondados |
| Agentes | Sempre com MEMORY correspondente |
| Insights | Sempre com chunk_ref para rastreabilidade |
| Decisoes | Sempre com [FONTE] |

---

## 15. TROUBLESHOOTING

| Problema | Solucao |
|----------|---------|
| Arquivo ja processado | Sistema pergunta se quer reprocessar |
| Checkpoint falhou | Verificar ENFORCEMENT.md, nao pular etapas |
| RAG sem resultados | Re-indexar: `python rag_index.py --knowledge --force` |
| Agente nao sabe responder | Verificar se MEMORY foi alimentada |
| Open Loop pendente | Consultar `/system/OPEN-LOOPS.json` |

---

**FIM DO GUIA ESTRATEGICO DE INTEGRACAO**

> Este documento foi gerado para permitir que outra IA compreenda e integre-se ao sistema Mega Brain de forma completa e estrategica.
