# Memory System Upgrade — Briefing Plan
**Branch:** `feat/memory-system-upgrade`
**Data:** 2026-03-05
**Escopo:** Médio (8-15h) — Briefing (não PRD)
**Decisão:** Briefing/plan com fases GSD — PRD seria overkill para tooling interno sem stakeholders externos.

---

## Diagnóstico: O Que Falta no Mega Brain (vs aios-stage)

| Item | aios-stage | mega-brain | Gap |
|------|-----------|------------|-----|
| Root CLAUDE.md | ✅ Slim, eficiente | ❌ **NÃO EXISTE** | CRÍTICO |
| Per-agent memory | ✅ `.claude/agent-memory/{agent}/MEMORY.md` | ⚠️ Só JARVIS (centralizado) | ALTO |
| Pre-compact digest | ✅ `precompact-session-digest.js` | ❌ Não existe | ALTO |
| Session archival | ✅ Comprimido automaticamente | ❌ 83 arquivos acumulando | MÉDIO |
| Context optimization | ✅ Lazy loading por keyword | ✅ Existe mas fragmentado | MÉDIO |
| Agent boot sequence | ✅ Via MEMORY.md por agente | ⚠️ Centralizado em JARVIS | MÉDIO |
| CLAUDE.md qualidade | ✅ Slim (50 linhas úteis) | ⚠️ `.claude/CLAUDE.md` 173 linhas densas | BAIXO |

---

## Fases de Implementação

### Fase 1 — Root CLAUDE.md (CRÍTICO, ~30min)
**O que:** Criar `CLAUDE.md` na raiz do projeto — atualmente não existe, usuários/Claude abrem o repo como Claude genérico.

**Modelo:** Baseado no aios-stage approach — slim, identity-first, lazy loading.

**Conteúdo:**
- Identidade JARVIS (5 linhas — quem sou, como falo)
- Arquitetura em 3 linhas
- Referência para `.claude/CLAUDE.md` para regras completas
- Hook de lazy loading ativo
- Próxima ação ao iniciar sessão

---

### Fase 2 — Per-Agent Memory System (~2h)
**O que:** Criar `.claude/agent-memory/` espelhando o padrão aios-stage. Cada agente (cargo/persona) terá seu próprio MEMORY.md persistente.

**Estrutura:**
```
.claude/agent-memory/
├── jarvis/
│   └── MEMORY.md         ← Migrar de .claude/jarvis/JARVIS-MEMORY.md
├── closer/
│   └── MEMORY.md         ← Novo: decisões, padrões, calibrações BR
├── cro/
│   └── MEMORY.md         ← Novo
├── cfo/
│   └── MEMORY.md         ← Novo
└── {cargo}/
    └── MEMORY.md
```

**Por que:** Quando um agente é ativado via `/conclave` ou `/ask`, ele carrega SEU contexto específico, não o contexto geral do JARVIS. Reduz ruído e aumenta relevância.

**Hook de loading:** Atualizar `skill_router.py` para injetar o MEMORY.md correto quando um agente de cargo é ativado.

---

### Fase 3 — Pre-Compact Session Digest (~1.5h)
**O que:** Implementar `precompact_session_digest.py` — ativado antes do Claude compactar o contexto.

**Fluxo:**
1. Claude avisa que vai compactar
2. Hook coleta: ações executadas, decisões tomadas, arquivos modificados, próxima ação
3. Salva digest comprimido em `.claude/sessions/digests/DIGEST-{date}.md`
4. Digest é carregado no próximo boot via `session_start.py`

**Formato do digest:**
```markdown
## SESSION DIGEST — 2026-03-05 14:32
**Estado:** [o que foi feito]
**Decisões:** [lista]
**Pendências:** [lista]
**Próxima ação:** [específica]
```

---

### Fase 4 — Session Archival & Cleanup (~1h)
**O que:** Sessions acumulando indefinidamente (83 arquivos, current.jsonl = 990KB).

**Regras:**
- Sessions > 7 dias → mover para `.claude/sessions/archive/`
- `current.jsonl` → rotar semanalmente (renomear para `JSONL-YYYY-WNN.jsonl`)
- Hook `session_cleanup.py` na SessionEnd

---

### Fase 5 — CLAUDE.md Refactor (~1h)
**O que:** `.claude/CLAUDE.md` está denso (173 linhas), repete conteúdo das rule groups.

**Objetivo:**
- Reduzir para ~80 linhas de regras CORE
- Remover conteúdo que já está nos RULE-GROUPs
- Adicionar referência ao sistema de agent-memory
- Melhorar seção "Ao Iniciar Sessão" com boot sequence clara

---

## Sequência de Execução

```
[1] Root CLAUDE.md         → Desbloqueio imediato (30min)
[2] Agent Memory System     → Core do upgrade (2h)
[3] Pre-Compact Digest      → Continuidade cross-session (1.5h)
[4] Session Archival        → Higiene do sistema (1h)
[5] CLAUDE.md Refactor      → Polimento final (1h)
```

**Total estimado:** 6-8 horas

---

## Sucesso

- [ ] `CLAUDE.md` existe na raiz, JARVIS se identifica na primeira mensagem
- [ ] Agentes de cargo carregam seu MEMORY.md ao ser ativados
- [ ] Pre-compact digest preserva contexto entre resets
- [ ] `.claude/sessions/` tem no máximo 14 arquivos (7 dias)
- [ ] `current.jsonl` < 200KB (comprimido semanalmente)
- [ ] `.claude/CLAUDE.md` < 100 linhas

---

## Não Está No Escopo

- RAG integration (projeto separado)
- Directory contract tasks 4-7 (branch própria)
- Agent template enforcement (próxima fase)
- Constitutional governance formal (pode vir depois)
