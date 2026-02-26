---
name: 10-SKILL-VERIFICATION-BEFORE-COMPLETION
description: Use antes de declarar trabalho completo, corrigido ou passando - requer verificação real antes de qualquer afirmação de sucesso
---

> **Auto-Trigger:** Antes de declarar completo/corrigido, antes de finalizar processamento
> **Keywords:** "verificar", "validar", "checklist", "finalizar", "completo", "pronto", "concluído"
> **Prioridade:** ALTA

---

# Verification Before Completion - Mega Brain

## Overview

Declarar trabalho completo sem verificação é desonestidade, não eficiência.

**Princípio central:** Evidência antes de afirmações, sempre.

**Violar a letra desta regra é violar o espírito desta regra.**

## A Lei de Ferro

```
NENHUMA DECLARAÇÃO DE CONCLUSÃO SEM EVIDÊNCIA DE VERIFICAÇÃO FRESCA
```

Se você não executou o comando de verificação nesta mensagem, não pode declarar que passou.

## O Gate Function

```
ANTES de declarar qualquer status ou expressar satisfação:

1. IDENTIFICAR: Qual comando prova esta afirmação?
2. EXECUTAR: Rodar o comando COMPLETO (fresco, completo)
3. LER: Output completo, checar exit code, contar falhas
4. VERIFICAR: Output confirma a afirmação?
   - Se NÃO: Declarar status real com evidência
   - Se SIM: Declarar afirmação COM evidência
5. SÓ ENTÃO: Fazer a afirmação

Pular qualquer passo = mentir, não verificar
```

## Verificações no Contexto Mega Brain

| Afirmação | Requer | Não Suficiente |
|-----------|--------|----------------|
| Arquivo processado | Chunks + Insights gerados | "Deveria estar OK" |
| Pipeline completo | Todos os 8 steps executados | "Rodei alguns steps" |
| Agente atualizado | MEMORY com novos insights | "Atualizei o agente" |
| Dossiê gerado | Arquivo existe + chunk_ids inline | "Criei o dossiê" |
| Session State atualizado | Verificar arquivo | "Marquei como processado" |
| JSONs consistentes | Parse sem erro | "Adicionei entradas" |

## Red Flags - PARAR

- Usando "deveria", "provavelmente", "parece que"
- Expressando satisfação antes de verificar ("Ótimo!", "Perfeito!", "Pronto!")
- Prestes a declarar task completa sem verificação
- Confiando em reports de agentes
- Baseando-se em verificação parcial
- Pensando "só dessa vez"
- Cansado e querendo terminar
- **QUALQUER formulação implicando sucesso sem ter rodado verificação**

## Prevenção de Racionalização

| Desculpa | Realidade |
|----------|-----------|
| "Deveria funcionar agora" | RODE a verificação |
| "Estou confiante" | Confiança ≠ evidência |
| "Só dessa vez" | Sem exceções |
| "Chunks foram criados" | Verificar INSIGHTS também |
| "Agente disse sucesso" | Verificar independentemente |
| "Estou cansado" | Cansaço ≠ desculpa |
| "Verificação parcial basta" | Parcial prova nada |

## Padrões Chave

**Processamento de arquivo:**
```
✅ [Verifica chunks] [Verifica insights] [Verifica session-state] "Arquivo processado"
❌ "Deveria estar OK" / "Parece correto"
```

**Pipeline Jarvis:**
```
✅ Step 1.1 ✅ → Step 1.2 ✅ → Step 2.1 ✅ → ... → "Pipeline completo"
❌ "Rodei o pipeline" (sem verificar cada step)
```

**Atualização de agente:**
```
✅ [Lê MEMORY] [Vê novos insights] [Chunk_ids presentes] "Agente atualizado"
❌ "Atualizei o MEMORY" (sem verificar)
```

**Geração de dossiê:**
```
✅ [Arquivo existe] [Chunk_ids inline] [Referências válidas] "Dossiê gerado"
❌ "Criei o dossiê" (sem verificar conteúdo)
```

## Por Que Isso Importa

No contexto Mega Brain:
- Arquivos "processados" mas chunks não gerados → perda de conhecimento
- Insights "extraídos" mas não salvos → retrabalho
- Agentes "atualizados" mas MEMORY vazio → agente não aprende
- Session State "atualizado" mas arquivo não tocado → próxima sessão repete trabalho

## Quando Aplicar

**SEMPRE antes de:**
- QUALQUER variação de afirmação de sucesso/conclusão
- QUALQUER expressão de satisfação
- QUALQUER declaração positiva sobre estado do trabalho
- Marcar task como completa
- Mover para próxima task
- Delegar para agentes

## O Resumo

**Sem atalhos para verificação.**

Rode o comando. Leia o output. ENTÃO declare o resultado.

Isso é inegociável.
