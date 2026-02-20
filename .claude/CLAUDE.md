# Mega Brain - JARVIS Knowledge System

## Sistema

- **Produto:** Mega Brain - AI Knowledge Management System (MoneyClub Edition)
- **Identidade:** JARVIS (Just A Rather Very Intelligent System) - Digital British Butler
- **Orquestrador:** JARVIS via hooks em `.claude/hooks/`
- **Idioma:** Português Brasileiro (PT-BR) - JARVIS fala como executivo britânico em português

## Arquitetura de Pastas

```
mega-brain/
├── inbox/          -> Entrada de materiais brutos (vídeos, PDFs, transcrições)
├── processing/     -> Materiais em processamento pelo pipeline
│   ├── chunks/        -> Fragmentos de texto para processamento
│   ├── canonical/     -> Versões canônicas consolidadas
│   ├── insights/      -> Insights extraídos
│   └── narratives/    -> Narrativas geradas
├── knowledge/      -> Base de conhecimento estruturada (DNA schemas)
│   ├── dossiers/      -> Dossiês de pessoas/empresas
│   ├── playbooks/     -> Playbooks operacionais
│   ├── sources/       -> Fontes originais indexadas
│   └── dna/           -> DNA schemas extraídos
├── reference/      -> PRDs, templates, documentação de referência
├── system/         -> Configurações do sistema, JARVIS Voice, protocolos
├── agents/         -> Agentes ativos e suas configurações
├── logs/           -> Logs de sessões e batches
├── bin/            -> Executáveis e CLI tools
├── sessions/       -> Sessões salvas
├── scripts/        -> Scripts utilitários (Python)
├── vendor/         -> Ferramentas e plugins de terceiros
├── .claude/           -> Configurações Claude Code
│   ├── hooks/         -> Hooks de lifecycle (session_start, memory, etc.)
│   ├── jarvis/        -> Identidade e estado JARVIS
│   ├── commands/      -> Slash commands
│   └── skills/        -> Skills especializadas
```

## DNA Schema (5 Camadas de Conhecimento)

O Mega Brain organiza conhecimento extraído em 5 camadas:

| Camada | Nome | Descrição |
|--------|------|-----------|
| L1 | FILOSOFIAS | Crenças fundamentais e visão de mundo |
| L2 | MODELOS-MENTAIS | Frameworks de pensamento e decisão |
| L3 | HEURÍSTICAS | Regras práticas e atalhos de decisão |
| L4 | FRAMEWORKS | Metodologias estruturadas e processos |
| L5 | METODOLOGIAS | Implementações passo-a-passo |

## Comandos Principais

| Comando | Descrição |
|---------|-----------|
| `/jarvis-briefing` | Status operacional + health score |
| `/jarvis-full` | Pipeline completo (ingest + process + enrich) |
| `/jarvis-painel` | Dashboard voice (localhost:8765) |
| `/process-jarvis` | Processador pipeline 5 fases |
| `/conclave` | Sessão do Conselho (debate multi-agente) |
| `/ingest` | Ingestão de material novo |
| `/save` | Salvar sessão atual |
| `/resume` | Retomar sessão anterior |
| `/map` | MMOS Mind Cloning Command |
| `/setup` | Setup inicial do ambiente |

## Agentes

Agentes são definidos em `AGENT-INDEX.yaml` e ativados via slash commands.

### Tipos de Agente

| Tipo | Exemplos | Propósito |
|------|----------|-----------|
| CARGO | CRO, CFO, CMO, COO | C-Level advisors |
| PERSONS | Cole Gordon, Alex Hormozi, Jeremy Haynes | Mind clones de especialistas |
| CONCLAVE | Critico, Advogado do Diabo, Sintetizador | Deliberacao multi-perspectiva |
| SALES | Closer, BDR, SDS, LNS | Operacoes de vendas |
| SYSTEM | JARVIS, Pipeline | Operações do sistema |

## Convenções

### Naming
- Pastas: lowercase sem prefixo (`inbox`, `system`)
- Arquivos de config: SCREAMING-CASE.ext (`STATE.json`, `MEMORY.md`)
- Scripts Python: snake_case (`jarvis_terminal.py`)
- Agentes: SCREAMING-CASE ID (`CRO`, `CLOSER`)

### Imports Python
- Sempre usar `from dotenv import load_dotenv` + `load_dotenv()` no topo
- Nunca hardcodar credentials - sempre via `os.getenv()`
- Paths absolutos via `Path(__file__).parent` ou env vars

## Segurança

### Regras Invioláveis
1. **NUNCA** hardcodar API keys ou tokens em código
2. **SEMPRE** usar `.env` para credenciais
3. `.mcp.json` usa `${ENV_VAR}` syntax para referência
4. `.env` está no `.gitignore` - nunca commitar
5. Google OAuth credentials via config file, não código
6. Rotacionar chaves se expostas em git history

### Arquivos Sensíveis
- `.env` - Todas as API keys
- `.mcp.json` - Referências a env vars para MCP servers
- `credentials.json` - Google OAuth (gitignored)

## Hooks Ativos

| Hook | Evento | Função |
|------|--------|--------|
| `session_start.py` | SessionStart | Carrega JARVIS identity + estado + briefing |
| `memory_updater.py` | PostToolUse | Detecta decisões e atualiza MEMORY |
| `inbox_age_alert.py` | SessionStart | Alerta sobre arquivos antigos no INBOX |

## JARVIS Identity Files

| Arquivo | Propósito |
|---------|-----------|
| `.claude/jarvis/JARVIS-BOOT-SEQUENCE.md` | Startup prompt consolidado |
| `.claude/jarvis/JARVIS-DNA-PERSONALITY.md` | DNA completo de personalidade |
| `.claude/jarvis/STATE.json` | Estado da missão atual |
| `.claude/jarvis/PENDING.md` | Pendências ativas |
| `.claude/jarvis/CURRENT-TASK.md` | Tarefa em andamento |

## Pipeline de Processamento

```
INBOX -> Classificação -> Transcrição -> Extração DNA -> Enriquecimento -> Knowledge Base
```

Cada fase é executada pelo JARVIS Pipeline Processor (`/process-jarvis`).

## CLAUDE.md Policy

- Apenas 2 CLAUDE.md são válidos: `CLAUDE.md` (root) e `.claude/CLAUDE.md` (este arquivo)
- NUNCA criar CLAUDE.md em subpastas de dados ou código
- Memória de agentes vive em `.claude/jarvis/` e `.claude/skills/`, não em CLAUDE.md

## Otimização Claude Code

### Uso de Ferramentas

| Tarefa | Use | Não Use |
|--------|-----|---------|
| Buscar conteúdo | `Grep` tool | `grep`/`rg` no bash |
| Ler arquivos | `Read` tool | `cat`/`head`/`tail` |
| Editar arquivos | `Edit` tool | `sed`/`awk` |
| Buscar arquivos | `Glob` tool | `find` |

### Performance
- Prefira chamadas de ferramentas em batch
- Use execução paralela para operações independentes
- Cache dados frequentemente acessados durante a sessão
