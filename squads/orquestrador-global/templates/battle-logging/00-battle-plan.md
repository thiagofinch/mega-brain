# Battle Plan: {título}

## Metadata
- **Data:** {YYYY-MM-DD}
- **Squad:** {squad-id}
- **Tipo de Battle:** {tipo: sales-letter | headline | vsl | roteiro | criativo | etc}
- **Comando ativado:** {comando exato usado, ex: *battle sales-letter}
- **Config usada:** {caminho para o config YAML do squad}
- **Modo de execução:** {yolo | interativo | dry-run}
- **Status:** {pendente | em_execucao | concluido | cancelado}
- **Aprovado em:** {data/hora da aprovação do estimate}

## Brief Original

{Transcrição exata do brief recebido do usuário}

## Brief Padronizado (distribuído para todas as equipes)

{Brief formatado e padronizado que foi enviado para cada equipe — idêntico para todas}

## Configuração do Battle

### Equipes

| ID | Nome | Líder | Membros | Ângulo |
|----|------|-------|---------|--------|
| {team-id} | {team-name} | {leader} | {member1, member2, ...} | {angle} |
| {team-id} | {team-name} | {leader} | {member1, member2, ...} | {angle} |
| {team-id} | {team-name} | {leader} | {member1, member2, ...} | {angle} |

**Reservas:** {lista de reserve_agents ou "Nenhum"}

### Critérios de Votação

| Critério | Peso | Descrição |
|----------|------|-----------|
| {criterion-name} | {weight} | {description} |
| {criterion-name} | {weight} | {description} |
| {criterion-name} | {weight} | {description} |

**Soma dos pesos:** {deve ser 1.00}
**Votantes:** {leaders_only | all_members}
**Rubrica detalhada:** {path para criteria_file}

### Debate

| Campo | Valor |
|-------|-------|
| Rodadas | {rounds} |
| Tiebreaker | {true/false} |
| Juiz | {chief} |
| Relay mode | true |

### Board de Revisão

| Revisor | Framework | Peso do voto |
|---------|-----------|--------------|
| {agent-id} | {framework-name} | {vote_weight} |
| {agent-id} | {framework-name} | {vote_weight} |

**Gate de aprovação:** {unanimous | majority}
**Máx. rodadas:** {max_rounds}
**Escalação:** {human | force_approve}

### Model Strategy

| Papel | Modelo |
|-------|--------|
| Chief/Juiz | {opus} |
| Board | {opus} |
| Produtores | {sonnet} |
| Votantes | {sonnet} |

## Estimativa Aprovada

| Métrica | Valor |
|---------|-------|
| Total de agentes | {N} |
| Custo estimado | ${X.XX} |
| Tempo estimado | ~{NN} minutos |

## Estado das Fases

- [ ] Fase 1: Briefing e Distribuição
- [ ] Fase 2: Produção Paralela
- [ ] Fase 3: Votação Cruzada
- [ ] Fase 4: Debate Estruturado
- [ ] Fase 5: Revisão pelo Board

---

*Template: `squads/orquestrador-global/templates/battle-logging/00-battle-plan.md`*
*Padrão base: `.claude/rules/execution-logging.md`*
