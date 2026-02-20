# RULE-GROUP-6: AUTO-ROUTING

> **Auto-Trigger:** Regras de auto-routing de skills, sub-agents, qualidade e GitHub workflow
> **Keywords:** "skill", "sub-agent", "quality", "auto-trigger", "GitHub", "workflow", "issue", "PR", "branch", "auto-routing", "MANDATORY", "watchdog", "keyword"
> **Prioridade:** ALTA
> **Regras:** 27, 28, 29, 30

---

## 🧠 REGRA #27: SKILL & SUB-AGENT AUTO-ROUTING SYSTEM v2.0

**SKILLS E SUB-AGENTS SÃO AUTO-ATIVADOS QUANDO KEYWORDS MATCHAM NO PROMPT.**

### O Problema que Esta Regra Resolve:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  BUG DETECTADO (2026-01-13):                                                 │
│                                                                              │
│  • SKILL-REGISTRY.md documentava arquitetura completa de auto-ativação      │
│  • Cada SKILL.md tinha: Auto-Trigger, Keywords, Prioridade                   │
│  • MAS: Nenhum código implementava o roteamento semântico                    │
│  • JARVIS não conseguia delegar para sub-agentes automaticamente            │
│  • Resultado: Skills e sub-agentes nunca eram ativados automaticamente      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Separação de Agentes (CRÍTICO):

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ARQUITETURA DE AGENTES - SEPARAÇÃO OBRIGATÓRIA                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  /agents/                       → CONCLAVE ONLY (via /conclave)           │
│  ├── PERSONS/                      → Agentes de pessoa (Hormozi, Cole, etc.) │
│  └── CARGOS/                       → Agentes de cargo (Sales Manager, etc.)  │
│                                                                              │
│  /.claude/jarvis/sub-agents/       → SUB-AGENTES JARVIS (auto-ativação)     │
│  ├── _TEMPLATE/                    → Template padrão para novos sub-agentes  │
│  └── LOG-FORMATTER/                → Exemplo: formatação visual de logs      │
│                                                                              │
│  REGRA: /agents/ só é ativado pelo /conclave (deliberação formal)        │
│  REGRA: sub-agents são "súbditos" do JARVIS para tarefas do dia-a-dia       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Arquitetura Implementada:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SKILL & SUB-AGENT AUTO-ROUTING SYSTEM v2.0                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SESSION START                                                              │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ skill_indexer.py (SessionStart hook) v2.0                           │    │
│  │ → Escaneia /.claude/skills/ (SKILL.md)                              │    │
│  │ → Escaneia /.claude/jarvis/sub-agents/ (AGENT.md)                   │    │
│  │ → Extrai Auto-Trigger, Keywords, Prioridade                         │    │
│  │ → Gera SKILL-INDEX.json com skills E sub-agents                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  USER PROMPT                                                                │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ user_prompt_submit.py → try_skill_routing()                         │    │
│  │ → Carrega SKILL-INDEX.json                                          │    │
│  │ → Busca keywords no prompt                                          │    │
│  │ → Se match skill: [SKILL AUTO-ACTIVATED]                            │    │
│  │ → Se match sub-agent: [SUB-AGENT AUTO-ACTIVATED] + AGENT.md + SOUL  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Diferença entre Skill e Sub-Agent:

| Aspecto | SKILL | SUB-AGENT |
|---------|-------|-----------|
| Arquivo | SKILL.md | AGENT.md + SOUL.md |
| Output | Determinístico (instruções fixas) | Adaptativo (personalidade) |
| Contexto injetado | Resumo (100 linhas) | Completo (AGENT + SOUL) |
| Uso típico | Tarefas padronizadas | Delegação com julgamento |
| Exemplo | /pdf, /xlsx | LOG-FORMATTER |

### Arquivos do Sistema:

```
.claude/hooks/skill_router.py           → Motor de roteamento v2.0 (skills + sub-agents)
.claude/hooks/skill_indexer.py          → Hook SessionStart v2.0
.claude/hooks/user_prompt_submit.py     → Integração com prompt
.claude/mission-control/SKILL-INDEX.json → Índice unificado (auto-gerado)
.claude/jarvis/sub-agents/_TEMPLATE/    → Template para novos sub-agentes
```

### Como Funciona:

1. **No início de cada sessão:** `skill_indexer.py` escaneia skills E sub-agents
2. **Extrai metadados:** Auto-Trigger, Keywords, Prioridade de SKILL.md e AGENT.md
3. **Gera índice unificado:** SKILL-INDEX.json com mapa keyword → skill/sub-agent
4. **Em cada prompt:** `try_skill_routing()` busca keywords
5. **Se match skill:** Injeta `[SKILL AUTO-ACTIVATED: nome]` + resumo
6. **Se match sub-agent:** Injeta `[SUB-AGENT AUTO-ACTIVATED: nome]` + AGENT.md + SOUL.md

### Header Obrigatório (SKILL.md e AGENT.md):

```markdown
> **Auto-Trigger:** [Quando este item é ativado automaticamente]
> **Keywords:** "keyword1", "keyword2", "keyword3"
> **Prioridade:** [ALTA | MÉDIA | BAIXA]
```

### Regras Absolutas:

- **NÃO PODE** criar skill/sub-agent sem definir Keywords no header
- **NÃO PODE** desativar o skill_indexer no SessionStart
- **NÃO PODE** usar /agents/ para tarefas do dia-a-dia (só /conclave)
- **DEVE** cada SKILL.md/AGENT.md ter header padrão: Auto-Trigger, Keywords, Prioridade
- **DEVE** criar sub-agents em /.claude/jarvis/sub-agents/ (não em /agents/)
- **DEVE** usar template _TEMPLATE/AGENT.md ao criar novos sub-agents
- **DEVE** usar Read tool para carregar SKILL.md/AGENT.md quando auto-ativado (VISIBILIDADE NO CHAT)

```
⚠️ SKILL/SUB-AGENT SEM KEYWORDS = INVISÍVEL
⚠️ ÍNDICE ATUALIZADO = SESSÃO START
⚠️ MATCH POR KEYWORD = AUTO-ATIVAÇÃO
⚠️ /agents/ = COUNCIL ONLY
⚠️ SUB-AGENTS = SÚBDITOS DO JARVIS
```

---

## 🔍 REGRA #28: ATIVAÇÃO VISÍVEL OBRIGATÓRIA

**Quando skill ou sub-agent for detectado no contexto via keyword matching, JARVIS DEVE:**

1. **USAR READ TOOL** para carregar o arquivo (SKILL.md ou AGENT.md)
2. **EXIBIR NO CHAT** a leitura do arquivo (similar a "Read: CONCLAVE-PROTOCOL.md")
3. **TORNAR TRANSPARENTE** qual skill/sub-agent está sendo ativado

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  FLUXO DE ATIVAÇÃO VISÍVEL:                                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Hook detecta keyword no prompt                                           │
│  2. Injeta [SKILL/SUB-AGENT AUTO-ACTIVATED: nome] no contexto                │
│  3. JARVIS vê a notificação de ativação                                      │
│  4. JARVIS USA READ TOOL para carregar o arquivo ← OBRIGATÓRIO              │
│  5. Usuário VÊ: "Read: .claude/skills/pdf/SKILL.md" no chat                 │
│  6. Transparência total sobre o que está sendo carregado                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Por que esta regra existe:

| Sem Regra #28 | Com Regra #28 |
|---------------|---------------|
| Hook injeta silenciosamente | Usuário VÊ a ativação no chat |
| Usuário não sabe o que foi carregado | "Read: SKILL.md" aparece visualmente |
| Opacidade operacional | Transparência total |
| Similar a caixa-preta | Similar ao fluxo do /conclave |

### Regras Absolutas:

- **NÃO PODE** ativar skill/sub-agent silenciosamente
- **NÃO PODE** injetar contexto sem mostrar ao usuário
- **DEVE** usar Read tool explicitamente quando auto-ativado
- **DEVE** exibir qual arquivo está sendo carregado

```
⚠️ AUTO-ATIVAÇÃO = LEITURA EXPLÍCITA (VISÍVEL NO CHAT)
⚠️ TRANSPARÊNCIA É OBRIGATÓRIA
⚠️ USUÁRIO DEVE VER O QUE ESTÁ SENDO CARREGADO
```

---

## 🛡️ REGRA #29: META-AGENT QUALITY AWARENESS (WARN, NOT BLOCK)

**O SISTEMA DETECTA E AVISA SOBRE GAPS, MAS NÃO BLOQUEIA ENTREGA.**

### Arquitetura do Sistema:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    META-AGENT SYSTEM v1.0                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LAYER 1: WATCHDOG (Prevenção)                                              │
│  └── quality_watchdog.py: Detecta agente, injeta MANDATORY_SECTIONS         │
│  └── post_output_validator.py: Calcula score, AVISA se < 70 (não bloqueia)  │
│                                                                             │
│  LAYER 2: DOCTOR (Propostas)                                                │
│  └── agent_doctor.py: Diagnostica gap, PROPÕE fix (não aplica auto)         │
│  └── Propostas salvas em doctor_proposals.jsonl para revisão humana         │
│                                                                             │
│  LAYER 3: GARDENER (Aprendizado)                                            │
│  └── pattern_analyzer.py: Detecta padrões de request                        │
│  └── Aprende preferências INDIRETAMENTE (sem perguntar)                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Formato MANDATORY_SECTIONS (Todo AGENT.md deve ter):

```markdown
## ⚠️ MANDATORY OUTPUT SECTIONS (NEVER SKIP)
<!-- MANDATORY -->

| Section | Required | Marker | Example |
|---------|----------|--------|---------|
| [Seção] | YES | `[marcador]` | [exemplo] |

## MINIMUM OUTPUT REQUIREMENTS
- [ ] Requisito 1
- [ ] Requisito 2

## QUALITY CHECKLIST (score 0-100)
- Item presente: +X pontos
- MINIMUM TO DELIVER: 70 points

<!-- End MANDATORY -->
```

### Fluxo de Operação:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INPUT DO USUÁRIO                                                           │
│       │                                                                     │
│       ▼                                                                     │
│  WATCHDOG detecta agente → Injeta MANDATORY_SECTIONS no contexto            │
│       │                                                                     │
│       ▼                                                                     │
│  CLAUDE processa (com spec injetada)                                        │
│       │                                                                     │
│       ▼                                                                     │
│  VALIDATOR calcula score (0-100)                                            │
│       │                                                                     │
│       ├── Score >= 70 → PASSA (silencioso)                                  │
│       │                                                                     │
│       └── Score < 70 → AVISA + entrega output                               │
│               │                                                             │
│               └── Score < 50 → DOCTOR propõe fix (para revisão humana)      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Arquivos do Sistema:

```
/.claude/hooks/
├── quality_watchdog.py           # Layer 1: Detecção e injeção
├── post_output_validator.py      # Layer 1: Validação (warn-based)
├── agent_doctor.py               # Layer 2: Propostas de fix
└── pattern_analyzer.py           # Layer 3: Análise de padrões

/logs/
├── quality_gaps.jsonl            # Gaps detectados (warnings)
├── output_validations.jsonl      # Resultados de validação
├── doctor_proposals.jsonl        # Propostas pendentes de revisão
├── doctor_fixes.jsonl            # Histórico de fixes aprovados
├── learning_patterns.jsonl       # Padrões de request detectados
├── preferences.jsonl             # Preferências aprendidas
└── watchdog_activations.jsonl    # Auditoria de ativações
```

### Princípios Fundamentais:

| Princípio | Comportamento |
|-----------|---------------|
| WARN, NOT BLOCK | Nunca bloqueia entrega - apenas avisa |
| PROPOSE, NOT APPLY | Doctor PROPÕE fixes, humano APROVA |
| LEARN INDIRECTLY | Detecta feedback sem perguntar |
| MANDATORY NO TOPO | Header nas primeiras 50 linhas do AGENT.md |

### Regras Absolutas:

- **NÃO PODE** bloquear entrega de output por quality score baixo
- **NÃO PODE** aplicar fix automaticamente em AGENT.md
- **NÃO PODE** perguntar ao usuário sobre preferências
- **DEVE** logar todo warning em quality_gaps.jsonl
- **DEVE** salvar propostas em doctor_proposals.jsonl
- **DEVE** ter MANDATORY_SECTIONS nas primeiras 50 linhas de todo AGENT.md

```
⚠️ AVISA, NÃO BLOQUEIA
⚠️ PROPÕE, NÃO APLICA
⚠️ APRENDE INDIRETAMENTE
⚠️ MANDATORY NO TOPO DO ARQUIVO
```

---

## ⚡ REGRA #30: GITHUB WORKFLOW OBRIGATÓRIO

**TODAS AS MODIFICAÇÕES DE CÓDIGO DEVEM SEGUIR O FLUXO ISSUE→BRANCH→PR→MERGE.**

### Fluxo Obrigatório:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GITHUB WORKFLOW - SEQUÊNCIA OBRIGATÓRIA                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CRIAR ISSUE                                                             │
│     └── Prefixos obrigatórios:                                              │
│         ├── [FEAT] Nova funcionalidade                                      │
│         ├── [FIX] Correção de bug                                           │
│         ├── [REFACTOR] Refatoração                                          │
│         └── [DOCS] Documentação                                             │
│                                                                             │
│  2. CRIAR BRANCH                                                            │
│     └── Formato: tipo/issue-XX-desc                                         │
│     └── Exemplo: feat/issue-42-add-login                                    │
│                                                                             │
│  3. COMMITS                                                                 │
│     └── Referenciar issue: "Add login form refs #42"                        │
│                                                                             │
│  4. PULL REQUEST                                                            │
│     └── Incluir "Fixes #XX" no corpo                                        │
│     └── Passar verificação de 6 níveis                                      │
│                                                                             │
│  5. MERGE                                                                   │
│     └── Somente após aprovação e verificação                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6 Níveis de Verificação (Obrigatório antes do Merge):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  NÍVEL │ NOME              │ O QUE VERIFICA                                 │
├────────┼───────────────────┼────────────────────────────────────────────────┤
│   1    │ LINT/HOOKS        │ Formatação e style guides                      │
│   2    │ TESTS             │ Testes unitários e integração                  │
│   3    │ BUILD/INTEGRITY   │ Compilação e integridade                       │
│   4    │ VISUAL            │ Revisão visual do output                       │
│   5    │ STAGING           │ Teste em ambiente preview                      │
│   6    │ SECURITY          │ Auditoria de segurança                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Regras Absolutas:

- **NÃO PODE** commitar direto na main/master
- **NÃO PODE** fazer merge sem PR aprovado
- **NÃO PODE** pular níveis de verificação
- **DEVE** criar issue antes de começar trabalho
- **DEVE** usar prefixos de tipo no issue e branch
- **DEVE** referenciar issue nos commits

```
⚠️ COMMIT DIRETO NA MAIN = PROIBIDO
⚠️ MERGE SEM PR = PROIBIDO
⚠️ PULAR VERIFICAÇÃO = PROIBIDO
⚠️ ISSUE → BRANCH → PR → MERGE = OBRIGATÓRIO
```

---

## 📋 CHECKLIST RÁPIDO - AUTO-ROUTING

```
[ ] Criando skill? Header com Auto-Trigger, Keywords, Prioridade?
[ ] Criando sub-agent? Em /.claude/jarvis/sub-agents/?
[ ] Sub-agent tem AGENT.md + SOUL.md?
[ ] Skill/sub-agent auto-ativado? Usou Read tool (visibilidade)?
[ ] Agente tem MANDATORY_SECTIONS nas primeiras 50 linhas?
[ ] Quality score >= 70? Se não, warning logado?
[ ] Modificação de código? Seguiu Issue→Branch→PR→Merge?
[ ] PR passou nos 6 níveis de verificação?
[ ] /agents/ só usado via /conclave?
```

---

**FIM DO RULE-GROUP-6**
