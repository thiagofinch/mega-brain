# 🎯 SKILLS MEGA BRAIN
## Sistema de Skills Auto-Invocáveis

> **Versão:** 1.0.0
> **Skills Ativas:** 6
> **Modo:** Auto-Invocação por Contexto

---

## O QUE SÃO SKILLS?

Skills são **instruções padronizadas** que o sistema invoca automaticamente baseado em:
- **Extensão de arquivo** (.md, .py, .json)
- **Comandos** (/process, /create-agent)
- **Keywords** detectadas na conversa
- **Contexto** da operação

### Benefícios
✅ Consistência em todos os outputs
✅ Padrões aplicados automaticamente
✅ Sem necessidade de comandos manuais
✅ Conhecimento institucional preservado

---

## COMO FUNCIONA

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEMA DE SKILLS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   USUÁRIO                                                        │
│      │                                                           │
│      ▼                                                           │
│   ┌─────────────────┐                                           │
│   │  INPUT/COMANDO  │                                           │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │    DETECTOR     │ ◄── Analisa: extensão, keywords, contexto │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │ SKILL-REGISTRY  │ ◄── Mapeia para skill(s) apropriada(s)   │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │  SKILL(S).md    │ ◄── Carrega regras e padrões             │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │    EXECUÇÃO     │ ◄── Aplica padrões automaticamente        │
│   └────────┬────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │     OUTPUT      │ ◄── Resultado padronizado                 │
│   └─────────────────┘                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## SKILLS DISPONÍVEIS

| # | Skill | Quando é Invocada |
|---|-------|-------------------|
| 00 | **SKILL-CREATOR** | Ao criar novas skills |
| 01 | **SKILL-DOCS-MEGABRAIN** | Ao criar/editar arquivos .md |
| 02 | **SKILL-PYTHON-MEGABRAIN** | Ao criar/editar arquivos .py |
| 03 | **SKILL-AGENT-CREATION** | Ao criar agentes |
| 04 | **SKILL-KNOWLEDGE-EXTRACTION** | Ao extrair insights |
| 05 | **SKILL-PIPELINE-JARVIS** | Ao processar material novo |

---

## TRIGGERS AUTOMÁTICOS

### Por Extensão
```
.md  → SKILL-DOCS-MEGABRAIN
.py  → SKILL-PYTHON-MEGABRAIN
```

### Por Comando
```
/process      → SKILL-PIPELINE-JARVIS
/create-agent → SKILL-AGENT-CREATION
/scan-inbox   → SKILL-PIPELINE-JARVIS
```

### Por Keywords
```
"criar playbook"  → SKILL-DOCS-MEGABRAIN
"script python"   → SKILL-PYTHON-MEGABRAIN
"novo agente"     → SKILL-AGENT-CREATION
"extrair insight" → SKILL-KNOWLEDGE-EXTRACTION
"processar video" → SKILL-PIPELINE-JARVIS
```

---

## ESTRUTURA DE PASTAS

```
/SKILLS/
├── README.md                          # Este arquivo
├── SKILL-REGISTRY.md                  # Índice de todas as skills
│
├── 00-SKILL-CREATOR/
│   └── SKILL.md                       # Meta-skill para criar skills
│
├── 01-SKILL-DOCS-MEGABRAIN/
│   └── SKILL.md                       # Padrões de documentação
│
├── 02-SKILL-PYTHON-MEGABRAIN/
│   └── SKILL.md                       # Padrões de código Python
│
├── 03-SKILL-AGENT-CREATION/
│   └── SKILL.md                       # Criação de agentes
│
├── 04-SKILL-KNOWLEDGE-EXTRACTION/
│   └── SKILL.md                       # Extração de conhecimento
│
└── 05-SKILL-PIPELINE-JARVIS/
    └── SKILL.md                       # Pipeline de processamento
```

---

## COMO USAR

### Uso Automático (Padrão)
Simplesmente trabalhe normalmente. O sistema detecta o contexto e aplica as skills apropriadas.

```
Você: "Cria um playbook para o Closer"
Sistema: [Detecta "playbook" → Invoca SKILL-DOCS-MEGABRAIN]
         [Aplica padrões de documentação automaticamente]
```

### Verificar Skill Ativa
```
"Qual skill está sendo usada?"
"Mostre os padrões aplicados"
```

### Ignorar Skill (Raro)
```
"Ignore as skills neste caso"
"Não aplique formatação padrão"
```

---

## CRIAR NOVA SKILL

1. **Consulte SKILL-CREATOR**
   ```
   "Quero criar uma skill para [X]"
   ```

2. **Siga o template** em `00-SKILL-CREATOR/SKILL.md`

3. **Registre** em `SKILL-REGISTRY.md`

4. **Teste** os triggers automáticos

---

## MANUTENÇÃO

### Ao Modificar Skill
- [ ] Atualizar versão na skill
- [ ] Verificar SKILL-REGISTRY
- [ ] Testar triggers

### Ao Criar Nova Skill
- [ ] Seguir template do SKILL-CREATOR
- [ ] Registrar no SKILL-REGISTRY
- [ ] Definir todos os triggers
- [ ] Documentar dependências

---

## FILOSOFIA

> **"Padrões são libertadores, não restritivos."**

As skills existem para:
1. **Liberar carga cognitiva** - não precisa lembrar padrões
2. **Garantir consistência** - outputs sempre profissionais
3. **Acelerar execução** - sem discussão sobre formato
4. **Preservar conhecimento** - boas práticas institucionalizadas

---

## INTEGRAÇÃO COM CLAUDE CODE

Para implementar no Claude Code, adicione ao CLAUDE.md:

```markdown
## 🎯 SISTEMA DE SKILLS

> **Localização:** `/SKILLS/`
> **Registry:** `/SKILLS/SKILL-REGISTRY.md`

### Auto-Invocação

Antes de executar qualquer tarefa, verificar:
1. Extensão do arquivo sendo criado/editado
2. Comando sendo executado
3. Keywords na solicitação
4. Contexto da operação

Consultar SKILL-REGISTRY para identificar skill(s) aplicável(is).

### Aplicação

Ao identificar skill relevante:
1. Carregar SKILL.md correspondente
2. Aplicar regras automaticamente
3. Não perguntar ao usuário (é automático)
4. Seguir checklist da skill antes de entregar
```

---

## META-INFORMAÇÃO

- **Versão:** 1.0.0
- **Criado:** Janeiro 2025
- **Mantido por:** Sistema Mega Brain
- **Última atualização:** [Auto-atualizado]
