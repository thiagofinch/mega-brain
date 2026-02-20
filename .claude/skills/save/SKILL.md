# SAVE SESSION - Persistência de Contexto

## Trigger
`/save` ou automaticamente ao final de cada tarefa significativa

## Objetivo
Salvar o estado COMPLETO da sessão atual para recuperação posterior.

## Execução

Quando acionado:

### 1. Coletar Estado Atual
```
- Timestamp da sessão
- Missão ativa (se houver)
- Fase atual
- Últimas ações executadas
- Arquivos modificados
- Pendências identificadas
- Contexto de conversa (resumo estruturado)
```

### 2. Gerar SESSION-LOG
Criar arquivo em `.claude/sessions/` com formato:
```
SESSION-YYYY-MM-DD-HHmm.md
```

### 3. Template Obrigatório

```markdown
# SESSION LOG - [TIMESTAMP]

## ESTADO DA MISSÃO
- **Missão**: [NOME]
- **Fase**: [N] de 5
- **Progresso**: [X]%

## CONTEXTO DA CONVERSA
[Resumo detalhado do que foi discutido/decidido]

## AÇÕES EXECUTADAS
1. [Ação 1 com detalhes]
2. [Ação 2 com detalhes]
...

## ARQUIVOS MODIFICADOS
- [arquivo1.ext] - [o que mudou]
- [arquivo2.ext] - [o que mudou]

## PENDÊNCIAS
- [ ] [Pendência 1]
- [ ] [Pendência 2]

## DECISÕES TOMADAS
- [Decisão 1]: [Razão]
- [Decisão 2]: [Razão]

## PRÓXIMOS PASSOS PLANEJADOS
1. [Próximo passo 1]
2. [Próximo passo 2]

## NOTAS IMPORTANTES
[Qualquer coisa crítica para não esquecer]

---
Session ID: [UUID]
Saved at: [ISO timestamp]
```

### 4. Atualizar LATEST-SESSION.md
Sempre manter um link para a última sessão em:
`.claude/sessions/LATEST-SESSION.md`

### 5. Confirmar
Responder: "Sessão salva: SESSION-YYYY-MM-DD-HHmm.md"

## Auto-Save Triggers
- Após completar qualquer batch
- Antes de qualquer operação destrutiva
- A cada 30 minutos de atividade
- Quando detectar pausa prolongada
- Quando usuário expressar que vai sair

## Output
Arquivo de sessão + confirmação visual
