# SKILL-REGISTRY
## Sistema de Detecção Automática de Skills

> **Versão:** 3.0.0
> **Atualizado:** 2026-02-18
> **Tipo:** Registry + Scanner
> **Naming Convention:** HYBRID — numbered (00-11) for core, semantic for domain-specific

---

## COMO O SISTEMA FUNCIONA

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DETECÇÃO AUTOMÁTICA DE SKILLS                                              │
│                                                                              │
│  1. ESCANEAR    → Listar pastas em /.claude/skills/                         │
│  2. DETECTAR    → Para cada pasta, verificar se existe SKILL.md             │
│  3. EXTRAIR     → Ler header: Auto-Trigger, Keywords, Prioridade            │
│  4. INDEXAR     → Construir mapa de triggers                                │
│  5. APLICAR     → Comparar input do usuário com triggers                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## PROCESSO DE SCAN

### Ao Iniciar Sessão

1. Listar todas as pastas em `/.claude/skills/`
2. Ignorar arquivos (apenas pastas)
3. Ignorar pastas que começam com `_` (backup/templates)
4. Para cada pasta válida:
   - Verificar se existe `SKILL.md` dentro
   - Se existe → Skill ativa
   - Se não existe → Ignorar

### Extração de Metadados

Para cada `SKILL.md` encontrada, extrair do header:

```markdown
> **Auto-Trigger:** [texto que define quando ativar]
> **Keywords:** [palavras separadas por vírgula]
> **Prioridade:** [ALTA | MÉDIA | BAIXA]
```

Se `Prioridade` não estiver definida, assumir `MÉDIA`.

---

## REGRAS DE MATCHING

### Por Keywords (Detecção no Input)

```python
# Pseudocódigo
para cada skill em skills_ativas:
    para cada keyword em skill.keywords:
        se keyword.lower() em input.lower():
            skill_match = True
```

### Por Auto-Trigger (Contexto)

| Auto-Trigger Contém | Contexto de Match |
|---------------------|-------------------|
| "criar", "criação" | Input pede para criar algo |
| "editar", "modificar" | Input pede para alterar algo |
| "arquivo .md" | Operação em arquivo Markdown |
| "arquivo .py" | Operação em arquivo Python |
| "agente", "agent" | Operação em agents/ |
| "pipeline", "processar" | Operação de processamento |

### Por Extensão de Arquivo

| Extensão | Skill(s) Relevante(s) |
|----------|----------------------|
| `.md` | Skills com keywords: "markdown", "docs", "documentação" |
| `.py` | Skills com keywords: "python", "código", "script" |
| `.json` | Skills com keywords: "json", "config", "schema" |
| `.yaml` | Skills com keywords: "yaml", "config" |

---

## ORDEM DE PRECEDÊNCIA

Quando múltiplas skills fazem match:

```
ALTA    → Sempre aplicar primeiro (obrigatório)
MÉDIA   → Aplicar se não conflitar com ALTA
BAIXA   → Aplicar apenas se explicitamente relevante
```

Se duas skills têm mesma prioridade → Aplicar em ordem numérica (00, 01, 02...).

---

## SKILLS ATIVAS (SCAN AUTOMÁTICO)

> Esta seção é preenchida automaticamente pelo scan.
> Última Atualização: 2026-02-18
> Naming Convention: HYBRID (numbered 00-11 for core, semantic for domain-specific)

### Skills Core (Numbered 00-11)

| # | Skill | Path | Keywords | Prioridade | Header |
|---|-------|------|----------|------------|--------|
| 00 | SKILL-CREATOR | `00-SKILL-CREATOR/` | criar skill, nova skill | ALTA | OK |
| 01 | DOCS-MEGABRAIN | `01-SKILL-DOCS-MEGABRAIN/` | documentar, md, playbook | ALTA | OK |
| 02 | PYTHON-MEGABRAIN | `02-SKILL-PYTHON-MEGABRAIN/` | python, script, codigo | ALTA | OK |
| 03 | AGENT-CREATION | `03-SKILL-AGENT-CREATION/` | criar agente, novo agent | ALTA | OK |
| 04 | KNOWLEDGE-EXTRACTION | `04-SKILL-KNOWLEDGE-EXTRACTION/` | extrair, insight, chunk | ALTA | OK |
| 05 | PIPELINE-JARVIS | `05-SKILL-PIPELINE-JARVIS/` | processar, pipeline, jarvis | ALTA | OK |
| 06 | BRAINSTORMING | `06-SKILL-BRAINSTORMING/` | brainstorm, ideias | MEDIA | OK |
| 07 | DISPATCHING-PARALLEL | `07-SKILL-DISPATCHING-PARALLEL-AGENTS/` | paralelo, dispatch, batch | ALTA | OK |
| 08 | EXECUTING-PLANS | `08-SKILL-EXECUTING-PLANS/` | executar, plano | ALTA | OK |
| 09 | WRITING-PLANS | `09-SKILL-WRITING-PLANS/` | plano, planejamento | MEDIA | OK |
| 10 | VERIFICATION | `10-SKILL-VERIFICATION-BEFORE-COMPLETION/` | verificar, validar, checklist | ALTA | OK |
| 11 | USING-SUPERPOWERS | `11-SKILL-USING-SUPERPOWERS/` | superpower, avancado | MEDIA | OK |

### Skills Domain-Specific (Semantic Names)

| Skill | Path | Keywords | Prioridade | Header |
|-------|------|----------|------------|--------|
| ask-[sua-empresa] | `ask-[sua-empresa]/` | [sua-empresa], empresa | MEDIA | NO |
| chronicler | `chronicler/` | briefing, handoff, log | ALTA | OK |
| council | `council/` | council, debate | MEDIA | NO |
| executor | `executor/` | executar, tarefa | MEDIA | NO |
| fase-2-5-tagging | `fase-2-5-tagging/` | fase, tagging | MEDIA | NO |
| finance-agent | `finance-agent/` | financeiro, finance | MEDIA | NO |
| gdrive-transcription | `gdrive-transcription-downloader/` | gdrive, transcricao | MEDIA | NO |
| gemini-fallback | `gemini-fallback/` | gemini, fallback | MEDIA | NO |
| gha | `gha/` | github actions, gha | MEDIA | NO |
| github-workflow | `github-workflow/` | github, issue, PR | ALTA | OK |
| hybrid-source-reading | `hybrid-source-reading/` | source, reading | MEDIA | NO |
| jarvis | `jarvis/` | jarvis, orquestrador | ALTA | OK |
| jarvis-briefing | `jarvis-briefing/` | briefing, status | ALTA | OK |
| ler-planilha | `ler-planilha/` | planilha, spreadsheet | MEDIA | NO |
| process-[sua-empresa]-inbox | `process-[sua-empresa]-inbox/` | processar, [sua-empresa], inbox | MEDIA | NO |
| resume | `resume/` | resume, retomar | MEDIA | NO |
| save | `save/` | save, salvar | MEDIA | NO |
| skill-writer | `skill-writer/` | skill, writer | MEDIA | NO |
| smart-download-tagger | `smart-download-tagger/` | download, tagger | MEDIA | NO |
| source-sync | `source-sync/` | source, sync | MEDIA | NO |
| sync-docs | `sync-docs/` | sync, gdrive | MEDIA | NO |
| talent-agent | `talent-agent/` | talent, rh | MEDIA | NO |
| verify | `verify/` | verificar, check | MEDIA | NO |
| verify-6-levels | `verify-6-levels/` | verificar, 6 levels | ALTA | OK |

### Total: 37 Skills Ativas (12 core + 25 domain-specific)
### With proper header: 17/37 (46%) — 20 skills need header update

---

## HEADER PADRÃO OBRIGATÓRIO

Para uma skill ser detectada automaticamente, o `SKILL.md` DEVE ter este header:

```markdown
# [NOME DA SKILL]
## [Descrição em uma linha]

> **Auto-Trigger:** [Quando esta skill é ativada]
> **Keywords:** [palavras-chave separadas por vírgula]
> **Prioridade:** [ALTA | MÉDIA | BAIXA]

---
```

### Exemplo Mínimo Válido

```markdown
# SKILL-EXAMPLE
## Exemplo de skill para demonstração

> **Auto-Trigger:** Ativado quando usuário menciona "exemplo"
> **Keywords:** "exemplo", "demo", "teste"
> **Prioridade:** BAIXA

---

## REGRAS

1. Esta skill faz X
2. Esta skill não faz Y
```

---

## COMO ADICIONAR NOVA SKILL

### Skill Própria

```bash
# 1. Criar pasta
mkdir -p /.claude/skills/XX-SKILL-[NOME]/

# 2. Criar SKILL.md com header padrão
# 3. Pronto! Skill detectada automaticamente
```

### Skill de Repositório Externo

```bash
# 1. Clonar/baixar skill para pasta
git clone [repo] /.claude/skills/[nome]/

# 2. Verificar que existe SKILL.md com header padrão
# 3. Se não existir header → adicionar

# 4. Pronto! Skill detectada automaticamente
```

### Requisitos para Reconhecimento

- [ ] Pasta diretamente em `/.claude/skills/`
- [ ] Arquivo `SKILL.md` na raiz da pasta
- [ ] Header com pelo menos: Auto-Trigger e Keywords
- [ ] Prioridade definida (ou assume MÉDIA)

---

## GRAFO DE DEPENDÊNCIAS

```
SKILL-CREATOR (meta-skill, raiz)
    │
    ├── SKILL-DOCS-MEGABRAIN
    │       │
    │       ├── SKILL-AGENT-CREATION
    │       │
    │       └── SKILL-KNOWLEDGE-EXTRACTION
    │               │
    │               └── SKILL-PIPELINE-JARVIS
    │
    └── SKILL-PYTHON-MEGABRAIN
```

### Dependências Declaradas

```yaml
# Formato no SKILL.md (opcional)
## DEPENDÊNCIAS
- Requer: SKILL-DOCS-MEGABRAIN
- Complementa: SKILL-PYTHON-MEGABRAIN
```

---

## MANUTENÇÃO

### Verificação de Integridade

Para verificar se todas as skills estão válidas:

1. Listar pastas em `/.claude/skills/`
2. Para cada pasta, verificar:
   - [ ] SKILL.md existe
   - [ ] Header tem Auto-Trigger
   - [ ] Header tem Keywords
   - [ ] Prioridade é válida (ALTA/MÉDIA/BAIXA)

### Resolver Skill Órfã

Se uma skill não está sendo detectada:

1. Verificar que pasta está em `/.claude/skills/` (não em subpasta)
2. Verificar que `SKILL.md` existe (não `skill.md` ou `README.md`)
3. Verificar que header está no formato correto
4. Adicionar header se não existir

---

## META-INFORMAÇÃO

- **Versão:** 3.0.0
- **Tipo:** Registry + Scanner
- **Atualização:** Automática via scan + manual audit
- **Dependências:** Nenhuma (arquivo raiz)
- **Last Full Audit:** 2026-02-18 (Quality Uplift F4)
