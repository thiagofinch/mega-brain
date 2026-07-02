---
name: Pipeline Task
about: Tarefa relacionada ao Pipeline de Conhecimento (Fases 1-5)
title: '[PIPELINE] '
labels: ['pipeline', 'knowledge']
assignees: ''
---

## Fase do Pipeline
<!-- Selecione a fase relacionada -->
- [ ] Fase 1 - Download (baixar arquivos das fontes)
- [ ] Fase 2 - Organização (organizar por fonte, marcar origem)
- [ ] Fase 3 - De-Para (validar planilha vs computador)
- [ ] Fase 4 - Pipeline (processar chunks, insights)
- [ ] Fase 5 - Agentes (alimentar agentes com conhecimento)

## Descrição da Tarefa
<!-- O que precisa ser feito nesta fase -->

## Fonte(s) Envolvida(s)
<!-- Quais fontes de conhecimento são afetadas -->
- [ ] HORMOZI (AH)
- [ ] COLE-GORDON (CG)
- [ ] JEREMY MINER (JM)
- [ ] JEREMY HAYNES (JH)
- [ ] Outra:

## Métricas Atuais
<!-- Preencha os números antes de iniciar -->
| Métrica | Valor |
|---------|-------|
| Arquivos na Planilha | |
| Arquivos no Computador | |
| % Fase Completa | |
| Batch Atual | /  |

## Dependências
<!-- O que precisa estar completo antes desta tarefa -->
- [ ] Fase anterior 100% completa
- [ ] De-Para validado
- [ ] Sem arquivos faltantes
- [ ] Sem duplicatas

## Critérios de Conclusão
<!-- Quando esta tarefa está completa -->
- [ ] Critério 1
- [ ] Critério 2
- [ ] Logs gerados (dual-location)
- [ ] MISSION-STATE.json atualizado

## Regras Aplicáveis
<!-- Regras do CLAUDE.md que devem ser seguidas -->
- REGRA #1: Fases são bloqueantes
- REGRA #2: De-Para obrigatório
- REGRA #8: Logging obrigatório (dual-location)
- REGRA #:

## Logs Esperados
```
/logs/batches/BATCH-XXX.md
/.claude/mission-control/batch-logs/BATCH-XXX.json
```

## Checklist de Verificação (6 Níveis)
- [ ] 1. Hooks/Lint passed
- [ ] 2. Tests passed
- [ ] 3. Build successful
- [ ] 4. Visual verification
- [ ] 5. Staging tested
- [ ] 6. Security audit
