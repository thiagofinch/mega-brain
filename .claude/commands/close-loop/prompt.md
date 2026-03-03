# /close-loop - Fechar Loop Aberto

Fecha o loop ativo no sistema JARVIS.

## Execução

1. Ler `.claude/jarvis/STATE.json`
2. Verificar se `open_loops.active == true`
3. Se sim, definir `open_loops.active = false`
4. Confirmar fechamento com visual

## Output

```
┌─────────────────────────────────────────────────────────────────┐
│  ✅ LOOP FECHADO                                                │
├─────────────────────────────────────────────────────────────────┤
│  Contexto: {context}                                            │
│  Opções oferecidas: {count}                                     │
│  Fechado em: {timestamp}                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Notas

- Não exclui o histórico, apenas desativa
- Pode reabrir com `/open-loop`
