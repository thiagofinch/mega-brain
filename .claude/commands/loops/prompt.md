# /loops - Listar Loops Abertos

Lista todos os loops ativos no sistema JARVIS.

## Execução

1. Ler `.claude/jarvis/STATE.json`
2. Verificar `open_loops`
3. Exibir status e opções

## Output

```
┌─────────────────────────────────────────────────────────────────┐
│  🔄 LOOPS ATIVOS                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LOOP #1: {context}                                             │
│  Criado: {created_at}                                           │
│  Status: {active ? 'ABERTO' : 'FECHADO'}                        │
│                                                                 │
│  Opções:                                                        │
│  [A] {option_a}                                                 │
│  [B] {option_b}                                                 │
│  [C] {option_c}                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Comandos: /close-loop (fechar) | A/B/C (executar opção)
```

## Se Não Houver Loops

```
┌─────────────────────────────────────────────────────────────────┐
│  ✅ NENHUM LOOP ABERTO                                          │
│                                                                 │
│  Use /open-loop para criar um novo loop de decisão.             │
└─────────────────────────────────────────────────────────────────┘
```
