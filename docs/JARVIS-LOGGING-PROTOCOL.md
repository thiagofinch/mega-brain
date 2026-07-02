# JARVIS LOGGING PROTOCOL

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║      ██╗      ██████╗  ██████╗  ██████╗ ██╗███╗   ██╗ ██████╗                 ║
║      ██║     ██╔═══██╗██╔════╝ ██╔════╝ ██║████╗  ██║██╔════╝                 ║
║      ██║     ██║   ██║██║  ███╗██║  ███╗██║██╔██╗ ██║██║  ███╗                ║
║      ██║     ██║   ██║██║   ██║██║   ██║██║██║╚██╗██║██║   ██║                ║
║      ███████╗╚██████╔╝╚██████╔╝╚██████╔╝██║██║ ╚████║╚██████╔╝                ║
║      ╚══════╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝                 ║
║                                                                               ║
║   ██████╗ ██████╗  ██████╗ ████████╗ ██████╗  ██████╗ ██████╗ ██╗            ║
║   ██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔═══██╗██╔════╝██╔═══██╗██║            ║
║   ██████╔╝██████╔╝██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║            ║
║   ██╔═══╝ ██╔══██╗██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║            ║
║   ██║     ██║  ██║╚██████╔╝   ██║   ╚██████╔╝╚██████╗╚██████╔╝███████╗       ║
║   ╚═╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝       ║
║                                                                               ║
║                    REGRAS INVIOLÁVEIS DE LOGGING                              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

**Versão:** 1.0
**Data:** 2026-01-06
**Status:** MANDATÓRIO

---

## PRINCÍPIO FUNDAMENTAL

> **TODO PROCESSAMENTO GERA LOG. SEM EXCEÇÕES.**
>
> Se processou, logou. Se não logou, não processou.
> Logs são a memória do sistema. Sem logs, o sistema esquece.

---

## REGRAS INVIOLÁVEIS

### REGRA #1: DUAL-LOCATION LOGGING

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TODA INFORMAÇÃO DEVE SER PERSISTIDA EM DOIS LUGARES                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LOCAL 1: JSON (Machine-Readable)                                          │
│  ├── /.claude/mission-control/batch-logs/BATCH-XXX-[XX].json              │
│  └── /.claude/mission-control/MISSION-STATE.json                          │
│                                                                             │
│  LOCAL 2: MARKDOWN (Human-Readable)                                        │
│  ├── /logs/batches/BATCH-XXX.md                                        │
│  ├── /logs/SOURCES/SOURCE-XX.md                                        │
│  └── /logs/MISSIONS/MISSION-XXXX-XXX-PROGRESS.md                       │
│                                                                             │
│  SE APENAS UM LOCAL FOI ATUALIZADO = LOGGING INCOMPLETO = ERRO             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### REGRA #2: TRIGGERS AUTOMÁTICOS

| Evento | Log Obrigatório | Local |
|--------|-----------------|-------|
| Batch processado | BATCH-XXX.md | logs/batches/ |
| Fonte completa | SOURCE-XX.md | logs/SOURCES/ |
| Fase completa | PHASE-X-COMPLETE.md | logs/ |
| Sessão encerrada | Atualizar PROGRESS.md | logs/MISSIONS/ |
| Qualquer processamento | Atualizar MISSION-STATE.json | .claude/mission-control/ |

### REGRA #3: CHECKLIST PRÉ-PROCESSAMENTO

Antes de processar qualquer batch, JARVIS deve:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKLIST PRÉ-BATCH                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [ ] Verificar qual é o próximo BATCH-XXX                                  │
│  [ ] Confirmar que BATCH anterior está logado                              │
│  [ ] Verificar se é o último batch da fonte (trigger SOURCE-XX.md)        │
│  [ ] Verificar se é o último batch da fase (trigger PHASE-X.md)           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### REGRA #4: CHECKLIST PÓS-PROCESSAMENTO

Após processar qualquer batch, JARVIS deve:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKLIST PÓS-BATCH                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [x] Criar BATCH-XXX.md em logs/batches/                               │
│  [x] Atualizar BATCH-XXX-[XX].json em .claude/mission-control/batch-logs/ │
│  [x] Atualizar MISSION-STATE.json                                          │
│  [x] Atualizar MISSION-PROGRESS.md                                         │
│                                                                             │
│  SE FONTE COMPLETA:                                                         │
│  [x] Criar SOURCE-XX.md em logs/SOURCES/                               │
│                                                                             │
│  SE FASE COMPLETA:                                                          │
│  [x] Criar PHASE-X-COMPLETE.md em logs/                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### REGRA #5: FORMATO OBRIGATÓRIO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ELEMENTOS OBRIGATÓRIOS EM TODO LOG                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. ASCII ART HEADER (identificação visual)                                │
│  2. METADATA (source, data, status)                                        │
│  3. MÉTRICAS (arquivos, chunks, insights, heurísticas, frameworks)        │
│  4. ARQUIVOS PROCESSADOS (lista completa)                                  │
│  5. KEY FRAMEWORKS (com descrição)                                         │
│  6. FILOSOFIAS DESTAQUE (em box)                                           │
│  7. HEURÍSTICAS COM NÚMEROS (tabela com rating)                            │
│  8. TIMESTAMP (data/hora de geração)                                       │
│  9. REFERÊNCIA AO LOG JSON DETALHADO                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FLUXO DE LOGGING

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUXO DE LOGGING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BATCH PROCESSADO                                                          │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────┐                                                       │
│  │ BATCH-XXX.json  │ ◄─── JSON detalhado (machine)                        │
│  │ BATCH-XXX.md    │ ◄─── Markdown visual (human)                         │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ MISSION-STATE   │ ◄─── Atualizar contador, current_batch               │
│  │ .json           │                                                       │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ PROGRESS.md     │ ◄─── Atualizar métricas acumuladas                   │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  É ÚLTIMO BATCH DA FONTE? ─────────┐                                       │
│       │ SIM                        │ NÃO                                   │
│       ▼                            │                                       │
│  ┌─────────────────┐              │                                       │
│  │ SOURCE-XX.md    │              │                                       │
│  └────────┬────────┘              │                                       │
│           │◄───────────────────────┘                                       │
│           ▼                                                                 │
│  É ÚLTIMO BATCH DA FASE? ──────────┐                                       │
│       │ SIM                        │ NÃO                                   │
│       ▼                            │                                       │
│  ┌─────────────────┐              │                                       │
│  │ PHASE-X.md      │              │                                       │
│  └────────┬────────┘              │                                       │
│           │◄───────────────────────┘                                       │
│           ▼                                                                 │
│      ✅ LOGGING COMPLETO                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## NOMENCLATURA PADRÃO

### Batch Logs
```
FORMATO: BATCH-XXX.md
EXEMPLO: BATCH-035.md, BATCH-036.md

FORMATO JSON: BATCH-XXX-[SOURCE_ID].json
EXEMPLO: BATCH-035-CG.json (CG = Cole Gordon)
```

### Source Logs
```
FORMATO: SOURCE-XX.md
XX = Iniciais da fonte

EXEMPLOS:
- SOURCE-AH.md (Alex Hormozi)
- SOURCE-CG.md (Cole Gordon)
- SOURCE-JH.md (Jeremy Haynes)
```

### Phase Logs
```
FORMATO: PHASE-X-COMPLETE-LOG.md
X = Número da fase (1-5)

EXEMPLOS:
- PHASE1-CONSOLIDADO-20251231.md
- PHASE-4-COMPLETE-LOG.md
```

### Mission Progress
```
FORMATO: MISSION-YYYY-XXX-PROGRESS.md

EXEMPLO: MISSION-2026-001-PROGRESS.md
```

---

## LOCALIZAÇÃO DOS LOGS

```
/mega-brain/
│
├── .claude/
│   └── mission-control/
│       ├── MISSION-STATE.json          ◄── Estado central (JSON)
│       └── BATCH-LOGS/
│           ├── BATCH-033-CG.json       ◄── Logs detalhados (JSON)
│           ├── BATCH-034-CG.json
│           └── BATCH-035-CG.json
│
├── reference/
│   ├── TEMPLATE-MASTER.md              ◄── Templates (este arquivo)
│   └── JARVIS-LOGGING-PROTOCOL.md      ◄── Protocolo de logging
│
└── logs/
    ├── BATCHES/
    │   ├── BATCH-001.md                ◄── Logs visuais (Markdown)
    │   ├── BATCH-002.md
    │   ├── ...
    │   └── BATCH-035.md
    │
    ├── SOURCES/
    │   ├── SOURCE-AH.md                ◄── Consolidação por fonte
    │   ├── SOURCE-CG.md (pendente)
    │   └── SOURCE-JH.md
    │
    ├── MISSIONS/
    │   └── MISSION-2026-001-PROGRESS.md ◄── Progresso geral
    │
    └── LIVE-SESSION/
        └── SESSION-YYYY-MM-DD.md       ◄── Log de sessão
```

---

## VALIDAÇÃO DE LOGGING

### Antes de Continuar para Próximo Batch

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  VALIDAÇÃO OBRIGATÓRIA                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  JARVIS deve verificar:                                                     │
│                                                                             │
│  1. BATCH-[N-1].md existe em logs/batches/?                            │
│     └── SE NÃO: CRIAR ANTES DE CONTINUAR                                  │
│                                                                             │
│  2. BATCH-[N-1]-[XX].json existe em .claude/mission-control/batch-logs/?  │
│     └── SE NÃO: CRIAR ANTES DE CONTINUAR                                  │
│                                                                             │
│  3. MISSION-STATE.json está atualizado?                                    │
│     └── batches_completed = N-1                                            │
│     └── current_batch = BATCH-N                                            │
│                                                                             │
│  4. MISSION-PROGRESS.md reflete o estado atual?                            │
│     └── SE NÃO: ATUALIZAR ANTES DE CONTINUAR                              │
│                                                                             │
│  SE QUALQUER VALIDAÇÃO FALHAR:                                              │
│  ⛔ PARAR E CORRIGIR ANTES DE PROCESSAR PRÓXIMO BATCH                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## COMANDOS ÚTEIS

### Verificar Estado dos Logs

```bash
# Listar batches existentes
ls -la logs/batches/

# Listar sources existentes
ls -la logs/SOURCES/

# Verificar último batch
ls -la logs/batches/ | tail -5

# Verificar mission state
cat .claude/mission-control/MISSION-STATE.json | jq '.4_pipeline.batches_completed'
```

---

## PENALIDADES POR VIOLAÇÃO

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           VIOLAÇÕES E CONSEQUÊNCIAS                           ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ⛔ PROCESSAR SEM LOGAR:                                                      ║
║     → Conhecimento perdido = trabalho jogado fora                            ║
║     → Obrigatório: voltar e criar logs retroativamente                       ║
║                                                                               ║
║  ⛔ LOGAR EM APENAS UM LOCAL:                                                 ║
║     → Inconsistência = erro futuro garantido                                 ║
║     → Obrigatório: criar log no local faltante                               ║
║                                                                               ║
║  ⛔ LOGAR COM FORMATO INCORRETO:                                              ║
║     → Informação inacessível = informação inútil                             ║
║     → Obrigatório: reformatar seguindo TEMPLATE-MASTER.md                    ║
║                                                                               ║
║  ⛔ ESQUECER SOURCE LOG:                                                      ║
║     → Conhecimento fragmentado = análise impossível                          ║
║     → Obrigatório: criar SOURCE-XX.md antes de próxima fonte                 ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## RESUMO EXECUTIVO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RESUMO DO PROTOCOLO                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. TODO BATCH GERA:                                                        │
│     • BATCH-XXX.md (visual)                                                │
│     • BATCH-XXX-[XX].json (detalhado)                                      │
│     • Atualização em MISSION-STATE.json                                    │
│     • Atualização em PROGRESS.md                                           │
│                                                                             │
│  2. TODA FONTE COMPLETA GERA:                                               │
│     • SOURCE-XX.md (consolidação)                                          │
│                                                                             │
│  3. TODA FASE COMPLETA GERA:                                                │
│     • PHASE-X-COMPLETE.md                                                  │
│                                                                             │
│  4. VALIDAÇÃO É OBRIGATÓRIA:                                                │
│     • Verificar logs existentes antes de processar                         │
│     • Corrigir faltantes antes de continuar                                │
│                                                                             │
│  5. DUAL-LOCATION É REGRA:                                                  │
│     • JSON + Markdown sempre                                               │
│     • Nunca um sem o outro                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Arquivo:** `/reference/JARVIS-LOGGING-PROTOCOL.md`
**Versão:** 1.0
**Data:** 2026-01-06
**Gerado por:** JARVIS Meta-Agente
**Status:** MANDATÓRIO - LEIA ANTES DE QUALQUER PROCESSAMENTO
