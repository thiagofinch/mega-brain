# 🧠 MEGA BRAIN - MISSION CONTROL SYSTEM v3.0
## Sistema Completo de Processamento e Rastreamento

```
███╗   ███╗██╗███████╗███████╗██╗ ██████╗ ███╗   ██╗
████╗ ████║██║██╔════╝██╔════╝██║██╔═══██╗████╗  ██║
██╔████╔██║██║███████╗███████╗██║██║   ██║██╔██╗ ██║
██║╚██╔╝██║██║╚════██║╚════██║██║██║   ██║██║╚██╗██║
██║ ╚═╝ ██║██║███████║███████║██║╚██████╔╝██║ ╚████║
╚═╝     ╚═╝╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                                                     
 ██████╗ ██████╗ ███╗   ██╗████████╗██████╗  ██████╗ ██╗     
██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔══██╗██╔═══██╗██║     
██║     ██║   ██║██╔██╗ ██║   ██║   ██████╔╝██║   ██║██║     
██║     ██║   ██║██║╚██╗██║   ██║   ██╔══██╗██║   ██║██║     
╚██████╗╚██████╔╝██║ ╚████║   ██║   ██║  ██║╚██████╔╝███████╗
 ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
```

---

## 📦 O QUE ESTÁ INCLUÍDO

Este pacote contém **5 arquivos** que formam o sistema completo:

| # | Arquivo | Descrição | Tamanho |
|---|---------|-----------|---------|
| 1 | `MISSION-CONTROL-MASTER.md` | Documentação completa do sistema | ~45KB |
| 2 | `JARVIS-EXECUTOR-PROMPT.md` | Prompt otimizado para Claude Code | ~18KB |
| 3 | `QUICK-REFERENCE-CARD.md` | Referência rápida de comandos | ~8KB |
| 4 | `JSON-TEMPLATES.md` | Templates e schemas de dados | ~25KB |
| 5 | `SETUP-GUIDE.md` | Guia de instalação | ~10KB |
| 6 | `README.md` | Este arquivo | ~5KB |

---

## 🎯 O QUE O SISTEMA FAZ

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   📊 PLANILHA     →    🔄 PIPELINE    →    🤖 AGENTES         │
│   com conteúdos        5 fases            atualizados          │
│                        automáticas                              │
│                                                                 │
│   + Retomada exata de onde parou                               │
│   + Status visual em tempo real                                │
│   + Rastreabilidade total (chunk → insight → agente)           │
│   + Extração automática de heurísticas com números             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### As 5 Fases

1. **INVENTÁRIO** - Mapeia planilha fonte vs inbox existente
2. **DOWNLOAD** - Baixa/transcreve materiais novos
3. **ORGANIZAÇÃO** - Estrutura e padroniza arquivos
4. **PIPELINE JARVIS** - Processa em batches (chunking, insights, etc)
5. **ALIMENTAÇÃO** - Atualiza agentes, souls e temas

---

## ⚡ QUICK START (2 minutos)

### 1. Copie os arquivos para seu projeto:
```
/.claude/mission-control/
├── MISSION-CONTROL-MASTER.md
├── JARVIS-EXECUTOR-PROMPT.md
├── QUICK-REFERENCE-CARD.md
├── JSON-TEMPLATES.md
├── SETUP-GUIDE.md
└── README.md
```

### 2. Cole no Claude Code:
```
Leia /.claude/mission-control/JARVIS-EXECUTOR-PROMPT.md e ative modo JARVIS.
Depois execute /mission status
```

### 3. Inicie sua primeira missão:
```
/mission new [link da sua planilha]
```

---

## 📋 COMANDOS PRINCIPAIS

```
/mission status          Ver status completo
/mission status compact  Status resumido
/mission resume          Continuar de onde parou
/mission pause           Pausar após batch atual
/mission new [file]      Nova missão
/mission report          Relatório final
```

---

## 🔧 CARACTERÍSTICAS

### ✅ Retomada Exata
- Sistema salva estado após cada operação
- Pode parar e continuar a qualquer momento
- Nunca perde progresso

### ✅ Status Visual
- Barras de progresso
- Métricas em tempo real
- Próximo passo sempre claro

### ✅ Rastreabilidade Total
- Cada insight tem chunk_id
- Pode voltar à fonte original
- Auditoria completa

### ✅ Extração de Heurísticas
- Detecta automaticamente números específicos
- Extrai thresholds estruturados
- Classifica como ★★★★★

### ✅ Error Recovery
- Quarentena de arquivos problemáticos
- Retry automático
- Não bloqueia o processo

---

## 📁 ESTRUTURA DE ARQUIVOS GERADOS

```
/.claude/mission-control/
├── MISSION-STATE.json      ← Estado central (CRÍTICO)
├── INVENTORY.json          ← Mapeamento fonte vs inbox
├── DOWNLOAD-LOG.json       ← Log de downloads
├── ORG-LOG.json            ← Log de organização
├── BATCH-LOGS/
│   ├── BATCH-001.json
│   ├── BATCH-002.json
│   └── ...
├── SESSION-LOGS/
│   └── SESSION-YYYY-MM-DD-NNN.json
├── ERROR-QUARANTINE/
│   └── [arquivos com problema]
└── REPORTS/
    └── MISSION-XXXX-FINAL.md
```

---

## 🤝 INTEGRAÇÕES

### Com Sistema Constitucional
O Mission Control pode invocar o Council para decisões complexas como:
- Criar novos agentes
- Resolver conflitos entre fontes

### Com Skills
Pode usar Skills específicas para:
- Documentação
- Extração de conhecimento
- Pipeline processing

### Com RAG
Atualiza automaticamente:
- Índices de chunks
- CANONICAL-MAP de entidades
- Base de conhecimento

---

## 📊 EXEMPLO DE STATUS

```
🧠 MEGA BRAIN - MISSION CONTROL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mission: MISSION-2026-001
Fonte:   Master-Playbook-Sources.xlsx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Fase 1: Inventário     ██████████████████████████  100%
✅ Fase 2: Download       ██████████████████████████  100%
✅ Fase 3: Organização    ██████████████████████████  100%
🔄 Fase 4: Pipeline       ██████████░░░░░░░░░░░░░░░░  37.5%
⏳ Fase 5: Alimentação    ░░░░░░░░░░░░░░░░░░░░░░░░░░  0%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 PRÓXIMO PASSO: /mission resume
```

---

## 📚 DOCUMENTAÇÃO DETALHADA

| Precisa de... | Leia... |
|---------------|---------|
| Visão geral completa | `MISSION-CONTROL-MASTER.md` |
| Instalar o sistema | `SETUP-GUIDE.md` |
| Referência de comandos | `QUICK-REFERENCE-CARD.md` |
| Estrutura de dados | `JSON-TEMPLATES.md` |
| Ativar no Claude Code | `JARVIS-EXECUTOR-PROMPT.md` |

---

## ⚠️ REQUISITOS

- Claude Code (Claude Projects ou Claude.ai)
- Planilha fonte (Google Sheets ou XLSX)
- Estrutura de pastas do Mega Brain

---

## 🆘 SUPORTE

Se algo não funcionar:

1. **Verifique** `MISSION-STATE.json` existe e é válido
2. **Execute** `/mission validate` para checar integridade
3. **Veja** `/mission errors` para arquivos com problema
4. **Consulte** `SETUP-GUIDE.md` seção Troubleshooting

---

## 📜 CHANGELOG

### v3.0.0 (2026-01-02)
- Sistema unificado (consolidou 2 documentos anteriores)
- Detecção inteligente de estrutura de planilha
- Error recovery robusto com quarentena
- Status visual aprimorado
- Integração com Sistema Constitucional
- Templates JSON completos

### v2.0.0 (anterior)
- Primeira versão faseada
- Sistema de checkpoints

### v1.0.0 (anterior)
- Versão inicial

---

## 📄 LICENÇA

Sistema proprietário do projeto Mega Brain.
Desenvolvido para uso interno.

---

```
                    ╔═══════════════════════════════╗
                    ║   MEGA BRAIN MISSION CONTROL  ║
                    ║          v3.0.0               ║
                    ║                               ║
                    ║   "Onde você parou,           ║
                    ║    eu continuo."              ║
                    ╚═══════════════════════════════╝
```
