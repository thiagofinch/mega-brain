# Voting Results: {título do Battle}

## Metadata
- **Battle:** {battle-id}
- **Squad:** {squad-id}
- **Fase:** 3 — Votação Cruzada
- **Data/Hora:** {YYYY-MM-DD HH:MM}
- **Votantes:** {lista de votantes (líderes)}
- **Peças avaliadas:** {N peças}

## Scores por Critério

### Votante: {team-a-leader} (avaliando equipes B e C)

| Critério | Peso | Peça B | Peça C |
|----------|------|--------|--------|
| {criterion-1} | {weight} | {score 1-10} | {score 1-10} |
| {criterion-2} | {weight} | {score 1-10} | {score 1-10} |
| ... | ... | ... | ... |
| **Média ponderada** | — | **{score}** | **{score}** |

**Justificativa:** {notas do votante sobre suas avaliações}

### Votante: {team-b-leader} (avaliando equipes A e C)

| Critério | Peso | Peça A | Peça C |
|----------|------|--------|--------|
| {criterion-1} | {weight} | {score 1-10} | {score 1-10} |
| ... | ... | ... | ... |
| **Média ponderada** | — | **{score}** | **{score}** |

**Justificativa:** {notas do votante}

### Votante: {team-c-leader} (avaliando equipes A e B)

| Critério | Peso | Peça A | Peça B |
|----------|------|--------|--------|
| {criterion-1} | {weight} | {score 1-10} | {score 1-10} |
| ... | ... | ... | ... |
| **Média ponderada** | — | **{score}** | **{score}** |

**Justificativa:** {notas do votante}

## Matriz de Votação Consolidada

| Votante | Peça A | Peça B | Peça C |
|---------|--------|--------|--------|
| {team-a-leader} | — (auto-voto proibido) | {score} | {score} |
| {team-b-leader} | {score} | — (auto-voto proibido) | {score} |
| {team-c-leader} | {score} | {score} | — (auto-voto proibido) |
| **Média Final** | **{score}** | **{score}** | **{score}** |

## Ranking Final

| Posição | Equipe | Score Final | Papel no Debate |
|---------|--------|-------------|-----------------|
| 1 | {team-id} ({team-name}) | {score} | **Defensor** |
| 2 | {team-id} ({team-name}) | {score} | **Desafiante** |
| 3 | {team-id} ({team-name}) | {score} | Eliminada |

## Notas

- **Empates resolvidos:** {descrever se houve empate e como foi resolvido, ou "Nenhum empate"}
- **Votações ausentes:** {descrever se algum votante não entregou, ou "Todas entregues"}
- **Margem Top 1 vs Top 2:** {diferença percentual — se ≤5%, tiebreaker round pode ser ativado}

---

*Template: `squads/orquestrador-global/templates/battle-logging/04-voting-results.md`*
*Padrão base: `.claude/rules/execution-logging.md`*
