# Debate Transcript: {título do Battle}

## Metadata
- **Battle:** {battle-id}
- **Squad:** {squad-id}
- **Fase:** 4 — Debate Estruturado
- **Data/Hora:** {YYYY-MM-DD HH:MM}

## Participantes

| Papel | Agente | Equipe | Score na Votação |
|-------|--------|--------|-----------------|
| **Defensor** | {agent-id} | {team-name} (#{1 no ranking}) | {score} |
| **Desafiante** | {agent-id} | {team-name} (#{2 no ranking}) | {score} |
| **Juiz** | {chief-id} | — | — |

## Rodada 1 — Apresentação

**Limite:** {max_words} palavras

### Defensor ({agent-id}):

{Argumento de apresentação do Defensor — pontos fortes da sua peça, por que deve vencer}

### Desafiante ({agent-id}):

{Argumento de apresentação do Desafiante — pontos fortes da sua peça, por que deve vencer}

---

## Rodada 2 — Ataque

**Limite:** {max_words} palavras

### Defensor ({agent-id}):

{Ataque aos pontos fracos da peça do Desafiante}

### Desafiante ({agent-id}):

{Ataque aos pontos fracos da peça do Defensor}

---

## Rodada 3 — Síntese

**Limite:** {max_words} palavras

### Defensor ({agent-id}):

{Síntese final — incorporando argumentos de ataque, defesa e apresentação}

### Desafiante ({agent-id}):

{Síntese final — incorporando argumentos de ataque, defesa e apresentação}

---

## Tiebreaker Round (se aplicável)

> Ativado quando margem entre Top 1 e Top 2 é ≤5%.
> Remover esta seção se não houve tiebreaker.

**Limite:** {max_words} palavras

### Defensor: {argumento extra}

### Desafiante: {argumento extra}

---

## Veredito do Juiz

```yaml
verdict:
  winner: {team-id}
  score_winner: {score final do vencedor}
  score_runner_up: {score final do segundo}
  must_fix:
    - "{correção obrigatória 1}"
    - "{correção obrigatória 2}"
  nice_to_have:
    - "{melhoria opcional 1}"
  judge_notes: "{justificativa detalhada do veredito}"
```

### Justificativa Expandida

{Texto livre do Juiz explicando:
- Por que a peça vencedora é superior
- Quais argumentos do debate foram mais convincentes
- O que cada lado fez bem e mal
- Por que as must_fix são necessárias}

---

*Template: `squads/orquestrador-global/templates/battle-logging/05-debate-transcript.md`*
*Padrão base: `.claude/rules/execution-logging.md`*
