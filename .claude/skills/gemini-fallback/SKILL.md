---
name: gemini-fallback
description: Usa Gemini CLI para acessar sites bloqueados (Reddit, etc)
triggers:
  - "buscar no reddit"
  - "acessar site bloqueado"
  - "gemini fetch"
  - "/gemini"
---

# Gemini CLI Fallback

Use este skill quando precisar acessar sites que Claude Code não consegue (Reddit, sites com bloqueio).

## Pré-requisitos

```bash
# Instalar Gemini CLI (se não instalado)
npm install -g @anthropic-ai/gemini-cli
# ou
pip install google-generativeai
```

## Como Usar

### Via Skill
```
/gemini [URL ou query]
```

### Exemplos
```
/gemini https://reddit.com/r/ClaudeAI/top
/gemini "melhores práticas claude code reddit"
```

## Execução

Quando acionado, este skill:

1. Verifica se Gemini CLI está disponível
2. Usa tmux para criar sessão isolada
3. Executa query via Gemini (que tem acesso web)
4. Captura e retorna o resultado

### Script de Execução

Execute o script auxiliar:
```bash
python3 .claude/skills/gemini-fallback/gemini_fetch.py "URL_OU_QUERY"
```

## Alternativa Manual

Se Gemini CLI não estiver disponível, use:

1. Abrir nova aba do terminal
2. Usar browser ou curl para acessar
3. Copiar conteúdo relevante
4. Colar no Claude Code

## Sites Comumente Bloqueados

- Reddit (r/ClaudeAI, r/LocalLLaMA)
- Twitter/X
- LinkedIn
- Alguns docs sites
