# Battle Report: {título}

## Resumo Executivo

| Métrica | Valor |
|---------|-------|
| **Peça vencedora** | {team-name} ({team-id}) |
| **Líder da equipe** | {leader-agent-id} |
| **Ângulo** | {angle da equipe vencedora} |
| **Score na votação** | {score final} |
| **Rodadas de debate** | {3 + tiebreaker se houve} |
| **Rodadas de board review** | {N de max_rounds} |
| **Custo total** | ${X.XX} (~{N}K tokens) |
| **Tempo total** | {HH:MM} (início → fim) |
| **Status** | {CONCLUÍDO | PARCIALMENTE CONCLUÍDO | CANCELADO} |

## Histórico por Fase

### Fase 1 — Briefing e Distribuição
- **Arquivo:** `00-battle-plan.md`
- **Resumo:** Brief recebido e padronizado. {N} equipes configuradas. Team criado.
- **Duração:** ~{MM} min

### Fase 2 — Produção Paralela
- **Arquivos:** `01-{team-a}-output.md`, `02-{team-b}-output.md`, `03-{team-c}-output.md`
- **Resumo:** {N} equipes produziram versões completas. {Notas sobre produções rejeitadas pelo format validation gate, se houver}
- **Duração:** ~{MM} min

### Fase 3 — Votação Cruzada
- **Arquivo:** `04-voting-results.md`
- **Resumo:** Ranking: 1º {team} ({score}), 2º {team} ({score}), 3º {team} ({score}). {Notas sobre empates, se houver}
- **Duração:** ~{MM} min

### Fase 4 — Debate Estruturado
- **Arquivo:** `05-debate-transcript.md`
- **Resumo:** {team vencedor} venceu o debate. Must-fix: {N itens}. {Tiebreaker round: sim/não}
- **Duração:** ~{MM} min

### Fase 5 — Revisão pelo Board
- **Arquivos:** `06-board-review-r1.md` {, `07-board-review-r2.md` se necessário}
- **Resumo:** Aprovado na rodada {N}. {Correções aplicadas entre rodadas, se houver}
- **Duração:** ~{MM} min

## Versão Final Aprovada

> Conteúdo completo da peça aprovada pelo board.
> Também salva separadamente em `08-final-version.md`.

{Conteúdo integral da peça final aprovada}

## Comparativo de Produções

| Equipe | Ângulo | Score | Classificação | Destaque |
|--------|--------|-------|---------------|----------|
| {team-a} | {angle} | {score} | {1º/2º/3º} | {principal ponto forte} |
| {team-b} | {angle} | {score} | {1º/2º/3º} | {principal ponto forte} |
| {team-c} | {angle} | {score} | {1º/2º/3º} | {principal ponto forte} |

## Lições Aprendidas

### O que funcionou bem
- {Insight 1 sobre o que produziu qualidade superior}
- {Insight 2}

### O que pode melhorar
- {Sugestão 1 para próximos Battles}
- {Sugestão 2}

### O que falhou (se aplicável)
- {Problema encontrado e como foi resolvido}

## Custo Detalhado

| Fase | Agentes | Modelo | Tokens (est.) | Custo |
|------|---------|--------|---------------|-------|
| Briefing | 1 | opus | {N}K | ${X.XX} |
| Produção | {N} | sonnet | {N}K | ${X.XX} |
| Votação | {N} | sonnet | {N}K | ${X.XX} |
| Debate | 3 | opus+sonnet | {N}K | ${X.XX} |
| Board | {N} | opus | {N}K | ${X.XX} |
| **Total** | — | — | **{N}K** | **${X.XX}** |

## Metadata

- **Battle ID:** {battle-id}
- **Squad:** {squad-id}
- **Data início:** {YYYY-MM-DD HH:MM}
- **Data fim:** {YYYY-MM-DD HH:MM}
- **Duração total:** {HH:MM}
- **Modo de execução:** {yolo | interativo | dry-run}
- **Config usada:** {path para config}
- **Diretório de execução:** `.data/executions/{dir}/`

---

<!--
EXEMPLO PREENCHIDO (para referência do agente que gerar o relatório):

# Battle Report: Carta de Vendas MPG — Perpétua Q1

## Resumo Executivo

| Métrica | Valor |
|---------|-------|
| **Peça vencedora** | Equipe Emocional (team-emotional) |
| **Líder da equipe** | gary-halbert |
| **Ângulo** | Emocional — dor, desejo, transformação pessoal |
| **Score na votação** | 8.2 |
| **Rodadas de debate** | 3 (sem tiebreaker) |
| **Rodadas de board review** | 2 de 3 |
| **Custo total** | $2.34 (~48K tokens) |
| **Tempo total** | 00:22 (início → fim) |
| **Status** | CONCLUÍDO |

(restante do exemplo omitido por brevidade)
-->

*Template: `squads/orquestrador-global/templates/battle-logging/99-battle-report.md`*
*Padrão base: `.claude/rules/execution-logging.md`*
