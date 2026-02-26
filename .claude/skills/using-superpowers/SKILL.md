---
name: 11-SKILL-USING-SUPERPOWERS
description: Use ao iniciar qualquer conversa - estabelece como encontrar e usar skills disponíveis
---

> **Auto-Trigger:** Qualquer conversa, encontrar e usar skills disponíveis
> **Keywords:** "superpower", "poder", "avançado", "capability", "skills", "habilidades"
> **Prioridade:** MÉDIA

---

# Using Superpowers - Mega Brain

<EXTREMELY-IMPORTANT>
Se você acha que há 1% de chance de uma skill se aplicar ao que está fazendo, você ABSOLUTAMENTE DEVE invocar a skill.

SE UMA SKILL SE APLICA À SUA TAREFA, VOCÊ NÃO TEM ESCOLHA. VOCÊ DEVE USÁ-LA.

Isso não é negociável. Isso não é opcional. Você não pode racionalizar para sair disso.
</EXTREMELY-IMPORTANT>

## Como Acessar Skills

**No Claude Code:** Use a ferramenta `Skill`. Quando invocar uma skill, seu conteúdo é carregado e apresentado - siga-o diretamente. Nunca use Read tool em arquivos de skill.

## A Regra

**Invocar skills relevantes ou solicitadas ANTES de qualquer resposta ou ação.** Mesmo 1% de chance de uma skill se aplicar significa que você deve invocar para verificar.

```
User message received
        ↓
Alguma skill pode se aplicar? ──SIM──→ Invocar Skill tool
        │                                    ↓
       NÃO                          Anunciar: "Usando [skill] para [propósito]"
        │                                    ↓
        ↓                           Tem checklist? ──SIM──→ Criar TodoWrite
Responder                                   │
                                           NÃO
                                            ↓
                                    Seguir skill exatamente
                                            ↓
                                    Responder
```

## Red Flags

Esses pensamentos significam PARE - você está racionalizando:

| Pensamento | Realidade |
|------------|-----------|
| "Isso é só uma pergunta simples" | Perguntas são tarefas. Checar skills. |
| "Preciso de mais contexto primeiro" | Check de skill vem ANTES de perguntas de clarificação. |
| "Deixa eu explorar o projeto primeiro" | Skills dizem COMO explorar. Checar primeiro. |
| "Posso checar arquivos rapidamente" | Arquivos não têm contexto da conversa. Checar skills. |
| "Deixa eu coletar informação primeiro" | Skills dizem COMO coletar. |
| "Isso não precisa de skill formal" | Se skill existe, use-a. |
| "Eu lembro dessa skill" | Skills evoluem. Ler versão atual. |
| "Isso não conta como tarefa" | Ação = tarefa. Checar skills. |
| "A skill é overkill" | Coisas simples viram complexas. Use. |
| "Vou só fazer isso primeiro" | Checar ANTES de fazer qualquer coisa. |

## Prioridade de Skills

Quando múltiplas skills podem se aplicar, usar esta ordem:

1. **Skills de processo primeiro** (brainstorming, executing-plans) - determinam COMO abordar
2. **Skills de implementação segundo** (dispatching-parallel-agents) - guiam execução

"Vamos processar X" → brainstorming primeiro (se complexo), depois skills de implementação
"Verificar se está pronto" → verification-before-completion primeiro

## Skills Disponíveis no Mega Brain

### Skills Nativas (00-05)
| # | Skill | Quando Usar |
|---|-------|-------------|
| 00 | SKILL-CREATOR | Criar novas skills |
| 01 | DOCS-MEGABRAIN | Documentação do Mega Brain |
| 02 | PYTHON-MEGABRAIN | Scripts Python do projeto |
| 03 | AGENT-CREATION | Criar novos agentes |
| 04 | KNOWLEDGE-EXTRACTION | Extrair conhecimento de fontes |
| 05 | PIPELINE-JARVIS | Pipeline Jarvis completo |

### Skills de Processo (06-11)
| # | Skill | Quando Usar |
|---|-------|-------------|
| 06 | BRAINSTORMING | Criar playbooks, estruturar agentes, design |
| 07 | DISPATCHING-PARALLEL-AGENTS | 2+ tarefas independentes em paralelo |
| 08 | EXECUTING-PLANS | Executar plano com checkpoints |
| 09 | WRITING-PLANS | Spec ou requirements para tarefa multi-step |
| 10 | VERIFICATION-BEFORE-COMPLETION | Antes de declarar qualquer coisa completa |
| 11 | USING-SUPERPOWERS | Meta-skill para encontrar outras skills |

## Tipos de Skills

**Rígidas** (verification, executing-plans): Seguir exatamente. Não adaptar longe da disciplina.

**Flexíveis** (brainstorming, writing-plans): Adaptar princípios ao contexto.

A própria skill diz qual é.

## Instruções do Usuário

Instruções dizem O QUE, não COMO. "Processar X" ou "Criar Y" não significa pular workflows.
