# 🤖 Ralph Cascateamento - FASE 5.7

> Processamento autônomo de 78 batches para MISSION-2026-001

---

## ⚡ Quick Start

```bash
# Navegar para o diretório
# Navigate to the Mega Brain project root
cd "<your-AIOX-GPS-path>"

# Executar o Ralph (processa todos os batches pendentes)
./ralph-cascateamento.sh
```

---

## 📋 Como Funciona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RALPH CASCATEAMENTO LOOP                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐         │
│    │ LER PRD  │────▶│ PEGAR    │────▶│ EXECUTAR │────▶│ MARCAR   │         │
│    │          │     │ PRÓXIMO  │     │ CASCATEAR│     │ COMPLETO │         │
│    └──────────┘     └──────────┘     └──────────┘     └──────────┘         │
│         │                                                   │               │
│         │                                                   │               │
│         │               ┌──────────┐                        │               │
│         └───────────────│ TODOS    │◀───────────────────────┘               │
│                         │ COMPLETOS│                                        │
│                         │    ?     │                                        │
│                         └──────────┘                                        │
│                              │                                              │
│                    NÃO ──────┴────── SIM                                    │
│                     │                  │                                    │
│                     ▼                  ▼                                    │
│              [PRÓXIMA ITER.]    [<promise>COMPLETE</promise>]               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Por iteração, o Ralph:**
1. Lê o PRD (`prd-batches-cascateamento.json`)
2. Pega o batch de maior prioridade onde `passes: false`
3. Spawna uma instância do Claude Code
4. Executa o protocolo de cascateamento completo
5. Atualiza o PRD com `passes: true`
6. Registra no audit log e atualiza dashboard
7. Repete até todos os 78 batches passarem

---

## 🚀 Modos de Execução

### 1. Execução Completa (Default)
```bash
./ralph-cascateamento.sh
```
Processa todos os batches pendentes (até 100 iterações).

### 2. Número Limitado de Iterações
```bash
./ralph-cascateamento.sh 5
```
Processa no máximo 5 batches e para.

### 3. Execução em Background (recomendado para muitos batches)
```bash
nohup ./ralph-cascateamento.sh > ralph-output.log 2>&1 &
```
Executa em background. Veja progresso com:
```bash
tail -f ralph-output.log
```

### 4. Com Screen/Tmux (ideal para sessões longas)
```bash
# Com screen
screen -S ralph
./ralph-cascateamento.sh
# Ctrl+A, D para desconectar
# screen -r ralph para reconectar

# Com tmux
tmux new -s ralph
./ralph-cascateamento.sh
# Ctrl+B, D para desconectar
# tmux attach -t ralph para reconectar
```

---

## 📊 Monitoramento

### Dashboard Visual
```bash
cat cascading-dashboard.md
```

### Progresso no PRD
```bash
# Quantos completos
jq '[.userStories[] | select(.passes == true)] | length' prd-batches-cascateamento.json

# Próximo pendente
jq '[.userStories[] | select(.passes == false)] | .[0].id' prd-batches-cascateamento.json
```

### Audit Log
```bash
# Último batch processado
tail -1 audit-cascateamento.jsonl | jq .

# Batches com erros
jq 'select(.summary.errors | length > 0)' audit-cascateamento.jsonl

# Total de batches no log
wc -l audit-cascateamento.jsonl
```

### Progress Log
```bash
# Ver learnings e patterns
head -100 progress-batches.txt
```

---

## 📁 Arquivos do Sistema

```
<your-AIOX-GPS-path>/
├── ralph-cascateamento.sh           # Script principal (EXECUTAR)
├── prd-batches-cascateamento.json   # PRD com 78 batches
├── prompt-batches.md                # Protocolo de cascateamento
├── progress-batches.txt             # Learnings e patterns
├── audit-cascateamento.jsonl        # Log de auditoria (1 linha/batch)
├── cascading-dashboard.md           # Dashboard visual
└── .ralph-cascateamento.lock        # Lock file (auto-gerenciado)
```

---

## ⚠️ Troubleshooting

### "Claude Code CLI não encontrado"
```bash
npm install -g @anthropic-ai/claude-code
```

### "Ralph já está rodando"
```bash
# Verificar se realmente está rodando
ps aux | grep ralph

# Se não estiver, remover lock
rm .ralph-cascateamento.lock
```

### Batch falhou
```bash
# Ver qual batch falhou
jq '[.userStories[] | select(.passes == false)] | .[0]' prd-batches-cascateamento.json

# Executar manualmente
claude
# Então executar o batch manualmente seguindo prompt-batches.md
```

### Retomar de onde parou
O Ralph automaticamente retoma do próximo batch pendente.
Basta executar novamente:
```bash
./ralph-cascateamento.sh
```

---

## 📈 Progresso Esperado

| Fonte | Batches | Estimativa |
|-------|---------|------------|
| JM (Jeremy Miner) | 18 | ~2-3 horas |
| JH (Jeremy Haynes) | 31 | ~4-5 horas |
| CG (Cole Gordon) | 13 | ~1.5-2 horas |
| AH (Alex Hormozi) | 2 | ~20 min |
| **TOTAL** | **78** | **~10-12 horas** |

*Tempos estimados para execução sequencial. Recomenda-se executar em background.*

---

## 🎯 Stop Condition

O Ralph para automaticamente quando:
1. Todos os 78 batches têm `passes: true`
2. Responde com `<promise>COMPLETE</promise>`

---

*Criado para MISSION-2026-001 - FASE 5.7 Cascateamento Retroativo*
*JARVIS v3.33.0*
