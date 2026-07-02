# Board Review — Rodada {N}: {título do Battle}

## Metadata
- **Battle:** {battle-id}
- **Squad:** {squad-id}
- **Fase:** 5 — Revisão pelo Board
- **Rodada:** {N} de {max_rounds}
- **Data/Hora:** {YYYY-MM-DD HH:MM}
- **Peça revisada:** {team-id vencedor} (versão {original | corrigida r{N-1}})

## Contexto

- **Veredito da Fase 4:** {team vencedor} com score {score}
- **Must-fix aplicados:** {Sim/Não — listar quais foram aplicados}
- **Correções da rodada anterior:** {N/A se primeira rodada, ou listar correções aplicadas}

---

## Revisor 1: {agent-id}

**Framework:** {framework-name}

### Avaliação

{Avaliação estruturada conforme o framework do revisor.
Ex: para David Ogilvy usando "Big Idea Evaluation":
- A peça têm uma Big Idea clara? {Sim/Não — análise}
- A Big Idea é simples de comunicar? {análise}
- A Big Idea resiste ao teste dos 10 anos? {análise}
- A execução faz jus à ideia? {análise}}

### Must-Fix (bloqueantes para aprovação)

1. {Correção obrigatória — sem esta, não pode ser aprovada}
2. {Correção obrigatória}

### Nice-to-Have (melhorias opcionais)

1. {Melhoria que elevaria a qualidade, mas não bloqueia aprovação}

### Voto

**{APROVADO | REPROVAR_COM_CORREÇÕES}**

---

## Revisor 2: {agent-id}

**Framework:** {framework-name}

### Avaliação

{Avaliação estruturada conforme o framework do revisor}

### Must-Fix

1. {Correção obrigatória}

### Nice-to-Have

1. {Melhoria opcional}

### Voto

**{APROVADO | REPROVAR_COM_CORREÇÕES}**

---

## Revisor 3: {agent-id} (se aplicável)

**Framework:** {framework-name}

### Avaliação

{Avaliação estruturada}

### Must-Fix

1. {Correção obrigatória}

### Nice-to-Have

1. {Melhoria opcional}

### Voto

**{APROVADO | REPROVAR_COM_CORREÇÕES}**

---

## Resultado Consolidado

### Votos

| Revisor | Framework | Voto | Must-Fix Count |
|---------|-----------|------|----------------|
| {agent-1} | {framework} | {APROVADO/REPROVAR} | {N} |
| {agent-2} | {framework} | {APROVADO/REPROVAR} | {N} |
| {agent-3} | {framework} | {APROVADO/REPROVAR} | {N} |

### Gate Verificado

- **Tipo de gate:** {unanimous | majority}
- **Votos APROVADO:** {N} de {total}
- **Gate satisfeito:** {Sim | Não}

### Decisão Final

**{APROVADO — Peça aprovada pelo board | REPROVAR — Nova rodada necessária}**

### Correções Unificadas para Próxima Rodada (se REPROVAR)

> Consolidação de todas as must-fix dos revisores, removendo duplicatas.
> Prioridade para correções mencionadas por ≥2 revisores.

1. {Correção consolidada 1} — Mencionada por: {revisor1, revisor2}
2. {Correção consolidada 2} — Mencionada por: {revisor1}
3. {Correção consolidada 3} — Mencionada por: {revisor2, revisor3}

### Escalação (se rodada {N} = max_rounds e REPROVAR)

> Se esta é a última rodada permitida e o board reprovou:
> - `human`: Notificar usuário para decisão manual
> - `force_approve`: Aprovar com nota de que o board não chegou a consenso

**Ação de escalação:** {human | force_approve | N/A}

---

*Template: `squads/orquestrador-global/templates/battle-logging/06-board-review-rN.md`*
*Padrão base: `.claude/rules/execution-logging.md`*
