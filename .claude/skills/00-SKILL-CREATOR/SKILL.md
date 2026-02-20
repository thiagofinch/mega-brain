# SKILL-CREATOR
## Meta-Skill: Guia Automático para Criação de Skills

> **Auto-Trigger:** Ativado quando detectar intenção de criar nova skill
> **Keywords:** "criar skill", "nova skill", "skill para", "automatizar"
> **Prioridade:** ALTA

---

## PROPÓSITO

Esta skill guia a criação de novas skills no sistema Mega Brain, garantindo:
- Estrutura padronizada
- Triggers bem definidos
- Integração automática
- Documentação completa

---

## ESTRUTURA OBRIGATÓRIA DE UMA SKILL

```
/SKILLS/
└── [NOME-DA-SKILL]/
    ├── SKILL.md           # Arquivo principal (OBRIGATÓRIO)
    ├── EXAMPLES/          # Exemplos de uso (opcional)
    │   ├── good.md        # Exemplos corretos
    │   └── bad.md         # Anti-patterns
    └── TEMPLATES/         # Templates reutilizáveis (opcional)
```

---

## TEMPLATE DE SKILL.md

```markdown
# [NOME DA SKILL]
## [Descrição em uma linha]

> **Auto-Trigger:** [Quando esta skill é ativada automaticamente]
> **Keywords:** [palavras-chave que ativam, separadas por vírgula]
> **Prioridade:** [ALTA | MÉDIA | BAIXA]

---

## PROPÓSITO

[Explique O QUE esta skill faz e POR QUE existe]

---

## QUANDO USAR

### ✅ USAR quando:
- [Situação 1]
- [Situação 2]
- [Situação 3]

### ❌ NÃO USAR quando:
- [Situação 1]
- [Situação 2]

---

## REGRAS OBRIGATÓRIAS

### [Categoria 1]
| Regra | Valor/Padrão |
|-------|--------------|
| [Item] | [Especificação] |

### [Categoria 2]
- [Regra 1]
- [Regra 2]

---

## ANTI-PATTERNS (NUNCA FAZER)

1. ❌ [O que não fazer]
2. ❌ [O que não fazer]

---

## CHECKLIST PRÉ-ENTREGA

- [ ] [Verificação 1]
- [ ] [Verificação 2]
- [ ] [Verificação 3]

---

## EXEMPLOS

### ✅ Correto
\`\`\`
[Exemplo de uso correto]
\`\`\`

### ❌ Incorreto
\`\`\`
[Exemplo de uso incorreto]
\`\`\`
```

---

## REGRAS PARA CRIAR SKILLS

### 1. Naming Convention
```
SKILL-[DOMÍNIO]-[FUNÇÃO].md

Exemplos:
- SKILL-PYTHON-PROCESSING.md
- SKILL-DOCS-PLAYBOOK.md
- SKILL-AGENT-CREATION.md
```

### 2. Auto-Triggers Obrigatórios

Toda skill DEVE ter triggers claros:

| Tipo de Trigger | Exemplo |
|-----------------|---------|
| **Keyword** | "criar playbook", "processar vídeo" |
| **Contexto** | Quando arquivo .py é criado |
| **Extensão** | Quando output é .md, .json, .py |
| **Comando** | /process, /create-agent |

### 3. Prioridade de Skills

Quando múltiplas skills aplicam:

```
ALTA    → Sempre aplicar primeiro
MÉDIA   → Aplicar se não conflitar
BAIXA   → Aplicar apenas se explicitamente relevante
```

### 4. Composição de Skills

Skills podem chamar outras:

```markdown
## DEPENDÊNCIAS
- Requer: SKILL-DOCS-FORMATTING
- Complementa: SKILL-PYTHON-STANDARDS
```

---

## CHECKLIST PARA NOVA SKILL

Antes de finalizar uma skill, verificar:

- [ ] Nome segue convenção SKILL-[DOMÍNIO]-[FUNÇÃO]
- [ ] Auto-Trigger definido claramente
- [ ] Keywords listadas (mínimo 3)
- [ ] Prioridade definida
- [ ] Seção "QUANDO USAR" completa
- [ ] Seção "ANTI-PATTERNS" presente
- [ ] Checklist pré-entrega incluído
- [ ] Pelo menos 1 exemplo correto e 1 incorreto
- [ ] Integração com outras skills documentada

---

## REGISTRO DE SKILLS

Ao criar nova skill, registrar em `/SKILLS/SKILL-REGISTRY.md`:

```markdown
| Skill | Domínio | Triggers | Prioridade | Status |
|-------|---------|----------|------------|--------|
| SKILL-X | Python | .py, código | ALTA | Ativo |
```

---

## META-INFORMAÇÃO

- **Versão:** 1.0.0
- **Criado:** Janeiro 2025
- **Domínio:** Sistema
- **Dependências:** Nenhuma (skill raiz)
