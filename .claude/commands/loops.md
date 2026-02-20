# /loops - Gerenciador de Open Loops

Mostra todos os loops abertos e permite gerencia-los.

## ACAO OBRIGATORIA

1. Ler `/system/OPEN-LOOPS.json`
2. Agrupar por prioridade (HIGH, MEDIUM, LOW)
3. Exibir o dashboard abaixo

## OUTPUT

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔓 OPEN LOOPS ({N} pendentes)                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🔴 HIGH PRIORITY                                                            ║
║  ─────────────────────────────────────────────────────────────────────────── ║
║  [{ID}] {DESCRIPTION}                                                        ║
║         Criado: {TEMPO_RELATIVO}                                             ║
║         Tipo: {TYPE}                                                         ║
║         Comando: {SUGGESTED_COMMAND}                                         ║
║                                                                              ║
║  🟡 MEDIUM PRIORITY                                                          ║
║  ─────────────────────────────────────────────────────────────────────────── ║
║  [{ID}] {DESCRIPTION}                                                        ║
║         Criado: {TEMPO_RELATIVO}                                             ║
║         Tipo: {TYPE}                                                         ║
║         Comando: {SUGGESTED_COMMAND}                                         ║
║                                                                              ║
║  🟢 LOW PRIORITY                                                             ║
║  ─────────────────────────────────────────────────────────────────────────── ║
║  (Se nenhum: "Nenhum loop de baixa prioridade")                              ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ❓ O QUE FAZER?                                                             ║
║  ─────────────────────────────────────────────────────────────────────────── ║
║  [A] Executar todos HIGH priority                                            ║
║  [B] Executar loop especifico: /loop exec OL-XXX                             ║
║  [C] Fechar loop especifico: /loop close OL-XXX                              ║
║  [D] Dispensar loop: /loop dismiss OL-XXX                                    ║
║  [E] Fechar todos: /loop close-all                                           ║
║  [F] Dispensar todos: /loop dismiss-all                                      ║
║  [G] Continuar sem resolver                                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## SE NAO HA LOOPS

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ✅ NENHUM OPEN LOOP                                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Todos os loops foram resolvidos ou dispensados.                             ║
║                                                                              ║
║  💡 Loops sao criados automaticamente quando:                                ║
║     • Uma sugestao de acao nao e executada                                   ║
║     • Um patch e criado mas nao aplicado                                     ║
║     • Materiais pendentes sao identificados                                  ║
║     • Um bug e encontrado mas nao corrigido                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## COMPORTAMENTO

1. Aguardar escolha do usuario
2. Se usuario escolher opcao, executar acao correspondente
3. Atualizar OPEN-LOOPS.json apos qualquer mudanca
