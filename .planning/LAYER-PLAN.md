# LAYER PUBLISHING PLAN - v1.2

**Criado:** 2026-02-27
**Status:** PENDENTE IMPLEMENTAÇÃO

## LAYER 1 - PÚBLICO (npx mega-brain-ai)

### VAI:
- `bin/` (CLI, setup)
- `core/` (workflows, tasks, templates, scripts)
- `.claude/commands/` (incluindo /conclave)
- `.claude/hooks/`
- `.claude/rules/`
- `.claude/skills/` (públicas)
- `agents/conclave/` (CONCLAVE!)
- `agents/_templates/`
- `agents/boardroom/`
- Estruturas VAZIAS (inbox/.gitkeep, knowledge/**/.gitkeep, etc)

### NÃO VAI:
- Conteúdo absorvido (dossiers, DNAs, playbooks reais)
- agents/minds/** (populados)
- agents/cargo/** (populados)

---

## LAYER 2 - PREMIUM (máquina + conteúdo absorvido)

### VAI (L1 + ):
- `agents/minds/**` (mind clones POPULADOS)
- `agents/cargo/**` (cargo agents POPULADOS)
- `knowledge/dossiers/**` (dossiers REAIS)
- `knowledge/playbooks/**` (playbooks REAIS)
- `knowledge/dna/**` (DNAs extraídos)
- `knowledge/sources/**` (fontes compiladas)
- `artifacts/insights/` (INSIGHTS processados)
- `artifacts/chunks/` (chunks processados)
- Skills premium

### NÃO VAI:
- `inbox/**` (material bruto original)

### DELETAR de todos:
- finance-agent
- talent-agent

---

## LAYER 3 - PESSOAL (backup completo)

### VAI (L1 + L2 + ):
- `inbox/**` (material bruto)
- `logs/**` (histórico completo)
- `.claude/sessions/`
- `.claude/mission-control/`
- `agents/sua-empresa/`

### NUNCA (boas práticas):
- `.env`
- `.mcp.json`
- `credentials.json`
- `token.json`
- `*.key`, `*.pem`, `*.secret`

---

## TAREFAS DE IMPLEMENTAÇÃO

1. [ ] Renomear council → conclave em todos os arquivos
2. [ ] Deletar finance-agent e talent-agent
3. [ ] Atualizar package.json "files" para L1
4. [ ] Atualizar .npmignore para L1
5. [ ] Criar script de build para L2 (inclui conteúdo absorvido)
6. [ ] Atualizar .gitignore para L3
7. [ ] Testar `npm pack --dry-run` para L1
8. [ ] Testar setup wizard funcional
9. [ ] Publicar L1 no npm
10. [ ] Configurar repo L2 privado
11. [ ] Configurar repo L3 privado
12. [ ] Sistema de validação por email (futuro)

---

## RESUMO VISUAL

```
┌─────────────────────────────────────────────────────────────┐
│           LAYER 1         LAYER 2         LAYER 3          │
│          (PÚBLICO)       (PREMIUM)       (PESSOAL)         │
├─────────────────────────────────────────────────────────────┤
│ Máquina/Casca      ✅            ✅            ✅           │
│ Conclave           ✅            ✅            ✅           │
│ Estruturas vazias  ✅            ✅            ✅           │
│ ─────────────────────────────────────────────────────────  │
│ minds/ POPULADOS   ❌            ✅            ✅           │
│ cargo/ POPULADOS   ❌            ✅            ✅           │
│ dossiers/playbooks ❌            ✅            ✅           │
│ DNAs extraídos     ❌            ✅            ✅           │
│ ─────────────────────────────────────────────────────────  │
│ inbox/ (bruto)     ❌            ❌            ✅           │
│ logs/sessions      ❌            ❌            ✅           │
│ sua-empresa/       ❌            ❌            ✅           │
│ ─────────────────────────────────────────────────────────  │
│ .env/secrets       ❌            ❌            ❌           │
└─────────────────────────────────────────────────────────────┘
```
