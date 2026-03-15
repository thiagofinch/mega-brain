# Regras de Gerenciamento de Estado

> **DEPRECATION NOTICE (S16):** MISSION-STATE.json references legacy 5-phase system.
> The MCE pipeline uses its own state in `core/intelligence/pipeline/mce/`.
> The principle (single source of truth for pipeline state) remains valid.

## 🔴 MISSION-STATE.json é SAGRADO

**Localização:** `/.claude/mission-control/MISSION-STATE.json`

## 📖 Ler ANTES de

- Qualquer resposta ao usuário
- Qualquer processamento
- Qualquer sugestão de próxima ação
- Qualquer estimativa de tempo/progresso

## ✏️ Atualizar APÓS

- Completar um batch
- Mudar de source
- Mudar de fase
- Iniciar sessão
- Encerrar sessão
- Qualquer ação significativa

## 📋 Campos críticos

```json
{
  "current_state": {
    "phase": 4,              // 1-5
    "phase_name": "Pipeline",
    "status": "IN_PROGRESS", // NOT_STARTED, IN_PROGRESS, COMPLETE
    "source_code": "CG",
    "source_name": "Cole Gordon",
    "batch_current": 3,
    "batch_total": 8,
    "percent_complete": 37.5
  },
  "session": {
    "id": "SESSION-2026-01-08-001",
    "started_at": "2026-01-08T14:00:00Z",
    "last_action_at": "2026-01-08T14:35:00Z",
    "is_active": true
  },
  "next_action": {
    "description": "Processar BATCH-004 Cole Gordon",
    "phase": 4,
    "details": "Arquivos CG_sales-8.txt até CG_sales-15.txt"
  }
}
```

## 🎯 Posição EXATA sempre

❌ ERRADO: "Estamos na fase 4"
❌ ERRADO: "Processando Cole Gordon"
❌ ERRADO: "Quase terminando"

✅ CERTO: "Fase 4, Batch 3/8, Cole Gordon, arquivo 8/23"
✅ CERTO: "37.5% da fase 4 completa"

## 🔄 Ao iniciar sessão

```bash
# 1. Ler estado
cat /.claude/mission-control/MISSION-STATE.json

# 2. Atualizar sessão
# session.id = novo ID
# session.started_at = agora
# session.is_active = true

# 3. Exibir status visual
# 4. Perguntar se continua
```

## 🔄 Ao encerrar sessão

```bash
# 1. Atualizar estado
# session.last_action_at = agora
# session.is_active = false

# 2. Criar HANDOFF
# /logs/handoffs/HANDOFF-LATEST.md

# 3. Salvar estado
```

## ⚠️ Nunca

- Modificar sem ler primeiro
- Deixar session.is_active = true ao sair
- Esquecer de atualizar next_action
- Deixar percent_complete desatualizado
