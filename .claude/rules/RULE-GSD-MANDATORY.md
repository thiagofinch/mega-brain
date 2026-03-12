# RULE-GSD-MANDATORY: GSD Obrigatório para Planos

> **Auto-Trigger:** Qualquer tarefa de planejamento ou implementação
> **Keywords:** "plano", "implementar", "criar feature", "refatorar", "hardening", "pipeline", "projeto novo"
> **Prioridade:** CRÍTICA
> **Versão:** 1.0.0

---

## REGRA ABSOLUTA

**TODO PLANO DE IMPLEMENTAÇÃO DEVE USAR GSD (Get Shit Done).**

### Detecção Automática

Quando detectar intenção de:
- Criar novo projeto/feature
- Refatorar código existente
- Implementar mudanças significativas
- Planejar trabalho multi-step

### Ação Obrigatória

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ANTES DE QUALQUER IMPLEMENTAÇÃO:                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Verificar se .planning/ existe                                           │
│     └── NÃO existe? → Executar /gsd:new-project                             │
│     └── Existe? → Verificar PROJECT.md e ROADMAP.md                         │
│                                                                              │
│  2. Verificar se tem roadmap                                                 │
│     └── NÃO tem? → Completar /gsd:new-project                               │
│     └── Tem? → Usar /gsd:plan-phase N                                       │
│                                                                              │
│  3. Executar via GSD                                                         │
│     └── /gsd:discuss-phase N → contexto                                     │
│     └── /gsd:plan-phase N → plano detalhado                                 │
│     └── /gsd:execute-phase N → implementação                                │
│     └── /gsd:verify-work N → validação                                      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Workflow GSD Obrigatório

```
/gsd:new-project
       │
       ▼
PROJECT.md + REQUIREMENTS.md + ROADMAP.md
       │
       ▼
/gsd:plan-phase 1 → /gsd:execute-phase 1 → /gsd:verify-work 1
       │
       ▼
Repetir para cada fase até completar
       │
       ▼
/gsd:complete-milestone
```

### Comandos GSD Principais

| Comando | Quando Usar |
|---------|-------------|
| `/gsd:new-project` | Iniciar novo projeto |
| `/gsd:progress` | Ver status atual |
| `/gsd:plan-phase N` | Planejar fase N |
| `/gsd:execute-phase N` | Executar fase N |
| `/gsd:verify-work N` | Verificar fase N |
| `/gsd:pause-work` | Pausar e salvar estado |
| `/gsd:resume-work` | Retomar trabalho |

### O Que É Proibido

- ❌ Implementar sem PROJECT.md
- ❌ Executar sem ROADMAP.md
- ❌ Pular fases do GSD
- ❌ Ignorar verificação (/gsd:verify-work)
- ❌ Planejar "na cabeça" sem documentar

### Benefícios

1. **Rastreabilidade** - Todo trabalho documentado
2. **Checkpoints** - Estado salvo, pode pausar/retomar
3. **Qualidade** - Verificação obrigatória
4. **Contexto** - Funciona mesmo com compactação

---

## ENFORCEMENT

Esta regra é carregada automaticamente quando keywords são detectadas.
O sistema DEVE verificar existência de .planning/ antes de qualquer implementação.

```
⚠️ SEM GSD = SEM IMPLEMENTAÇÃO
⚠️ GSD É OBRIGATÓRIO, NÃO OPCIONAL
⚠️ PLANEJAR ANTES DE EXECUTAR
```

---

**FIM DO RULE-GSD-MANDATORY**
