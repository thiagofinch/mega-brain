# SAVE SESSION CONTEXT

Salva o contexto atual da sessão para recuperação posterior.

## Instruções

1. Leia o arquivo atual de sessão: `/logs/LIVE-SESSION/CURRENT-SESSION.md`
2. Pergunte ao usuário: "O que você quer que eu salve como contexto?"
3. Adicione ao arquivo de sessão:
   - Timestamp atual
   - Resumo do que foi feito
   - Tarefas pendentes
   - Próximos passos
   - Qualquer contexto importante que o usuário mencionar

4. Salve também em `/logs/LIVE-SESSION/CONTEXT.json`:
```json
{
  "last_task": "descrição da tarefa",
  "status": "in_progress|completed|blocked",
  "pending": ["lista de pendências"],
  "next_steps": ["próximos passos"],
  "important_files": ["arquivos relevantes"],
  "notes": "notas do usuário"
}
```

5. Confirme ao usuário que foi salvo.

## Formato de Output

```
[SAVED] Contexto salvo em:
- /logs/LIVE-SESSION/CURRENT-SESSION.md
- /logs/LIVE-SESSION/CONTEXT.json

Próxima sessão: execute `/resume` para carregar contexto
```
