---
workflow: battle-round
version: 1.0.0
type: template
squads: [any]
config_schema: knowledge/BATTLE-CONFIG-SCHEMA.md
pattern: knowledge/TEAM-PATTERNS.md#pattern-6-battle-royale
description: >
  Workflow genérico para executar um Battle Royale completo.
  Cada squad que adotar o Pattern 6 usa este template como base,
  configurando apenas os parâmetros específicos do seu domínio.
---

# Battle Round — Workflow Template

## Overview

Este workflow documenta as 5 fases de um Battle Royale, com gates de entrada/saída, responsáveis, inputs/outputs e edge cases para cada fase. É o documento principal que um squad chief segue para executar um Battle.

**Referências:**
- Pattern: `TEAM-PATTERNS.md#pattern-6-battle-royale`
- Schema: `BATTLE-CONFIG-SCHEMA.md`
- Logging: `templates/battle-logging/` (templates de log por fase)
- Execution dir: `.data/executions/{YYYY-MM-DD}_battle-{slug}/`

**State file:** Cada Battle mantém um `battle-state.json` no diretório de execução, atualizado após cada fase. Formato:

```json
{
  "battle_id": "battle-{slug}",
  "squad": "{squad-id}",
  "status": "BRIEFING|PRODUCING|VOTING|DEBATING|REVIEWING|COMPLETED|FAILED",
  "current_phase": 1,
  "started_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "phases": {
    "1_briefing": { "status": "completed", "completed_at": "..." },
    "2_production": { "status": "in_progress", "teams_completed": ["team-a"] },
    "3_voting": { "status": "pending" },
    "4_debate": { "status": "pending" },
    "5_board": { "status": "pending", "round": 0 }
  },
  "config": { "...battle config snapshot..." }
}
```

---

## Prerequisite: Estimate (Obrigatório)

Antes de executar qualquer Battle, o sistema DEVE apresentar uma estimativa via `*battle --estimate`:

```
Input: brief do usuário + config do squad
Output:
  - Número de agentes: {N}
  - Modelo por papel: chief (opus), produtores (sonnet), board (opus)
  - Custo estimado: $X.XX
  - Tempo estimado: ~NN minutos
  - Aprovação: [Sim] / [Cancelar]
```

O Battle SÓ prossegue com aprovação explícita do usuário (FR2.1).

---

## Fase 1: Briefing e Distribuição

**Gate de Entrada (Gate-In):**
- Brief do usuário recebido (texto ou referência a arquivo)
- Configuração Battle carregada do squad config (`battle:` section em squad.yaml)
- `*battle --estimate` aprovado pelo usuário
- Validação de configuração passou (ver BATTLE-CONFIG-SCHEMA.md § Validation Checklist)

**Responsável:** Chief

**Inputs:**
- Brief original do usuário
- `battle:` config do squad.yaml
- Agentes disponíveis no squad

**Processo:**

1. Chief cria o diretório de execução: `.data/executions/{YYYY-MM-DD}_battle-{slug}/`
2. Chief cria o `battle-state.json` com status `BRIEFING`
3. Chief cria o `00-battle-plan.md` usando template de `templates/battle-logging/00-battle-plan.md`
4. Chief válida que todos os inputs necessários estão presentes no brief
5. Chief formata um **brief padronizado** — idêntico para todas as equipes (evita viés por briefing diferente)
6. Chief cria o team via `TeamCreate`:
   ```
   TeamCreate({
     team_name: "megabrain-{squad-id}-battle-{timestamp}",
     description: "Battle: {título do brief}"
   })
   ```
7. Chief distribui o brief padronizado para cada equipe via `SendMessage`:
   ```
   SendMessage({
     type: "message",
     recipient: "{team-leader}",
     content: "BATTLE BRIEF\n\n{brief padronizado}\n\nEquipe: {team-name}\nÂngulo: {angle}\nMembers: {lista}\n\nProduza uma versão COMPLETA e INDEPENDENTE do deliverable.\nNÃO comunique com outras equipes.",
     summary: "Battle brief para {team-name}"
   })
   ```

**Outputs:**
- Diretório de execução criado
- `battle-state.json` criado (status: BRIEFING)
- `00-battle-plan.md` preenchido
- Brief padronizado distribuído para todas as N equipes

**Gate de Saída (Gate-Out):**
- Todas as N equipes confirmaram recebimento do brief via SendMessage (idle notification = confirmação)
- `battle-state.json` atualizado para status `PRODUCING`, phase `2_production`

**Edge Cases:**
- Brief incompleto → Chief solicita informações adicionais ao usuário antes de distribuir
- Agente indisponível → Chief substitui por `reserve_agents[0]` se disponível, senão reduz equipes
- Config inválida → Battle não inicia, erro detalhado retornado ao usuário

---

## Fase 2: Produção Paralela

**Gate de Entrada (Gate-In):**
- Brief padronizado distribuído para todas as equipes
- Todas as equipes confirmaram recebimento

**Responsável:** Equipes (N equipes em paralelo)

**Inputs:**
- Brief padronizado (idêntico para todas)
- Ângulo da equipe (angle do config)
- Lista de membros da equipe

**Processo:**

1. Chief cria N tasks paralelas via `TaskCreate` (sem `addBlockedBy` entre elas):
   ```
   TaskCreate({
     title: "Battle Production: {team-name}",
     description: "Produzir versão completa do deliverable com ângulo: {angle}",
     owner: "{team-leader}"
   })
   ```
2. Cada equipe trabalha de forma independente e isolada
3. **PROIBIDO:** comunicação entre equipes durante esta fase
4. Cada líder coordena seus membros internamente via SendMessage
5. Ao concluir, o líder marca a task como completed e envia o output ao chief:
   ```
   SendMessage({
     type: "message",
     recipient: "chief",
     content: "PRODUCTION COMPLETE\n\nTeam: {team-id}\n\n{output completo}",
     summary: "Produção completa de {team-name}"
   })
   ```
6. Chief salva cada output como `{NN}-{team-id}-output.md` no diretório de execução

**Outputs:**
- N versões completas do deliverable (uma por equipe)
- Arquivos `01-team-a-output.md`, `02-team-b-output.md`, `03-team-c-output.md` no diretório de execução

**Gate de Saída (Gate-Out):**
- Todas as N tasks de produção com status `completed`
- Todos os N outputs recebidos e salvos pelo chief
- **Format Validation Gate (FR3.1):** Chief válida que cada produção segue o formato esperado (seções obrigatórias presentes, tamanho mínimo atingido). Produções fora de formato são rejeitadas com feedback para resubmissão
- `battle-state.json` atualizado para status `VOTING`, phase `3_voting`

**Edge Cases:**
- Equipe não entrega → Chief aguarda até timeout (configurável, padrão 10 min), então redistribui para `reserve_agents` ou reduz para N-1 equipes (mínimo 2)
- Produção fora de formato → Chief envia feedback específico e solicita resubmissão (máx 1 retry)
- Agente crash mid-production → Líder redistribui internamente; se líder crashou, chief assume com reserve_agent

---

## Fase 3: Votação Cruzada

**Gate de Entrada (Gate-In):**
- Outputs de todas as equipes disponíveis e validados (Format Validation Gate passed)
- Pelo menos 2 produções válidas

**Responsável:** Líderes de equipe (voters: leaders_only por padrão)

**Inputs:**
- Todos os outputs das outras equipes (NÃO o próprio)
- Critérios de scoring do config (`scoring.criteria`)
- Rubrica detalhada do `scoring.criteria_file`

**Processo:**

1. Chief distribui os outputs para votação cruzada (cada líder recebe outputs das OUTRAS equipes):
   ```
   SendMessage({
     type: "message",
     recipient: "{team-a-leader}",
     content: "VOTING ROUND\n\nAvalie as peças das outras equipes usando os critérios abaixo.\nNÃO avalie a peça da sua própria equipe.\n\nCritérios:\n{lista de critérios com pesos e rubrica}\n\nPeça da Equipe B:\n{output-team-b}\n\nPeça da Equipe C:\n{output-team-c}\n\nResponda com scores 1-10 para cada critério de cada peça.",
     summary: "Voting round para {team-a-leader}"
   })
   ```
2. Chief cria tasks de votação (bloqueadas por TODAS as tasks de produção):
   ```
   TaskCreate({
     title: "Battle Voting: {voter-name} avalia {teams}",
     description: "Avaliar peças usando critérios ponderados",
     owner: "{voter-name}"
   })
   ```
3. Cada votante retorna scores por critério para cada peça avaliada
4. Chief calcula score final por peça: `score = Σ(score_critério × peso_critério)`
5. Chief produz ranking automático e seleciona Top 2 para debate
6. Chief cria o `04-voting-results.md` no diretório de execução

**Outputs:**
- Matriz completa de votação (votante × peça × critério)
- Score final ponderado por peça
- Ranking ordenado por score descendente
- Top 2 identificadas: #1 = Defensor, #2 = Desafiante
- `04-voting-results.md` salvo no diretório de execução

**Gate de Saída (Gate-Out):**
- Todas as tasks de votação completadas
- Ranking calculado com Top 2 identificadas
- `battle-state.json` atualizado para status `DEBATING`, phase `4_debate`

**Edge Cases:**
- Empate entre equipes → Critério de desempate: equipe com score mais alto no critério de maior peso vence. Se ainda empate: chief decide
- Votante não entrega → Chief pode: (a) prosseguir com votos disponíveis se ≥2 votaram, (b) timeout e decidir unilateralmente
- Score suspeitamente uniforme (todos 10/10) → Chief pode invalidar e solicitar nova votação com justificativa obrigatória

---

## Fase 4: Debate Estruturado

**Gate de Entrada (Gate-In):**
- Top 2 peças identificadas pelo ranking
- Líder da equipe #1 designado como **Defensor**
- Líder da equipe #2 designado como **Desafiante**
- Chief assume papel de **Juiz**

**Responsável:** Defensor, Desafiante, Juiz (Chief)

**Inputs:**
- Peça do Defensor (output da equipe #1)
- Peça do Desafiante (output da equipe #2)
- Scores de votação de ambas as peças
- Configuração de debate (`debate.round_definitions`)

**Processo:**

O debate acontece em 3 rodadas sequenciais. **Toda comunicação passa pelo Chief como relay** (ADR-003) — os líderes NÃO se comunicam diretamente.

**Rodada 1 — Apresentação:**
```
Chief → Defensor:
  "DEBATE R1: APRESENTAÇÃO (max {max_words} palavras)
   Apresente os pontos fortes da sua peça e por que ela deve vencer."

Defensor → Chief:
  "{argumento de apresentação}"

Chief → Desafiante:
  "DEBATE R1: APRESENTAÇÃO (max {max_words} palavras)
   O Defensor apresentou: {resumo do argumento}.
   Apresente os pontos fortes da SUA peça e por que ela deve vencer."

Desafiante → Chief:
  "{argumento de apresentação}"
```

**Rodada 2 — Ataque:**
```
Chief → Defensor:
  "DEBATE R2: ATAQUE (max {max_words} palavras)
   O Desafiante argumentou: {resumo}.
   Ataque os pontos fracos da peça do Desafiante."

Defensor → Chief:
  "{argumento de ataque}"

Chief → Desafiante:
  "DEBATE R2: ATAQUE (max {max_words} palavras)
   O Defensor atacou: {resumo}.
   Ataque os pontos fracos da peça do Defensor."

Desafiante → Chief:
  "{argumento de ataque}"
```

**Rodada 3 — Síntese:**
```
Chief → Defensor:
  "DEBATE R3: SÍNTESE (max {max_words} palavras)
   Sintetize todos os argumentos e faça sua defesa final."

Defensor → Chief:
  "{síntese final}"

Chief → Desafiante:
  "DEBATE R3: SÍNTESE (max {max_words} palavras)
   O Defensor sintetizou: {resumo}.
   Sintetize todos os argumentos e faça sua defesa final."

Desafiante → Chief:
  "{síntese final}"
```

Após as 3 rodadas, o Chief (Juiz) emite o veredito:

```yaml
verdict:
  winner: team-a
  score_winner: 7.8
  score_runner_up: 7.2
  must_fix:
    - "Correção obrigatória 1"
    - "Correção obrigatória 2"
  nice_to_have:
    - "Melhoria opcional 1"
  judge_notes: "Justificativa detalhada do veredito"
```

Chief cria o `05-debate-transcript.md` no diretório de execução.

**Outputs:**
- Transcrição completa do debate (3 rodadas)
- Veredito estruturado (YAML parsável)
- `must_fix` list para a peça vencedora
- `05-debate-transcript.md` salvo

**Gate de Saída (Gate-Out):**
- Veredito emitido com `winner`, `must_fix`, `nice_to_have`
- Must-fix corrections aplicadas à peça vencedora pelo líder da equipe vencedora
- `battle-state.json` atualizado para status `REVIEWING`, phase `5_board`

**Edge Cases:**
- Placar muito próximo (≤5% de diferença no score) → Rodada extra opcional (tiebreaker) se `debate.tiebreaker_round: true`
- Defensor/Desafiante não responde → Chief pode: (a) conceder a rodada ao oponente, (b) timeout e decidir com base nos argumentos disponíveis
- Debate inconclusivo → Chief pode declarar vencedor unilateralmente com justificativa

---

## Fase 5: Revisão pelo Board

**Gate de Entrada (Gate-In):**
- Veredito da Fase 4 com peça vencedora identificada
- Lista `must_fix` já aplicada à peça (líder da equipe vencedora corrigiu)
- Board de revisores configurado no config (`board.reviewers`)

**Responsável:** Board de Revisores (em paralelo)

**Inputs:**
- Peça vencedora (com must-fix aplicados)
- Veredito da Fase 4 (contexto)
- Framework de revisão de cada revisor
- Configuração do board (`board.approval_gate`, `board.max_rounds`)

**Processo:**

1. Chief envia a peça para todos os revisores do board em paralelo:
   ```
   SendMessage({
     type: "message",
     recipient: "{reviewer-agent}",
     content: "BOARD REVIEW (Rodada {N})\n\nPeça para revisão:\n{peça completa}\n\nContexto: Vencedora do debate, must_fix aplicados.\nUse seu framework '{framework}' para avaliar.\n\nResponda com:\n- APROVADO ou REPROVAR_COM_CORREÇÕES\n- must_fix: [lista de bloqueantes]\n- nice_to_have: [lista de melhorias]",
     summary: "Board review R{N} por {reviewer-name}"
   })
   ```
2. Chief cria tasks paralelas de board review:
   ```
   TaskCreate({
     title: "Board Review R{N}: {reviewer-name}",
     description: "Avaliar peça usando framework {framework}",
     owner: "{reviewer-name}"
   })
   ```
3. Cada revisor avalia independentemente e retorna voto + feedback
4. Chief consolida os votos e verifica o gate:
   - `unanimous`: TODOS devem votar APROVADO
   - `majority`: >50% devem votar APROVADO
5. Chief cria o `06-board-review-r{N}.md` no diretório de execução

**Se APROVADO:**
- Chief salva a versão final como `08-final-version.md`
- Chief cria o `99-battle-report.md` (relatório final)
- Battle status → `COMPLETED`

**Se REPROVADO:**
- Chief consolida todas as correções dos revisores em lista unificada
- Líder da equipe vencedora aplica correções
- Nova rodada de revisão (volta ao passo 1 desta fase)
- Máximo: `board.max_rounds` rodadas

**Outputs:**
- `06-board-review-r{N}.md` por rodada
- Versão final aprovada (`08-final-version.md`)
- Relatório final (`99-battle-report.md`)

**Gate de Saída (Gate-Out):**
- Gate de aprovação satisfeito (unanimidade ou maioria)
- `08-final-version.md` salvo
- `99-battle-report.md` criado
- `battle-state.json` atualizado para status `COMPLETED`
- Team shutdown via `SendMessage({ type: "shutdown_request" })` para todos os agentes

**Edge Cases:**
- Reprovado após `max_rounds` rodadas → `escalation.after_max_rounds`:
  - `human`: Pausa e notifica o usuário para decisão manual
  - `force_approve`: Aprova com nota de que o board não chegou a consenso
- Reviewer não responde → Chief pode prosseguir se ≥2 revisores votaram (com nota no log)
- Feedback contraditório entre revisores → Chief prioriza correções que foram mencionadas por ≥2 revisores

---

## Modos de Execução

### YOLO Mode

Todas as 5 fases executam automaticamente sem pausa humana. O Battle completo roda do início ao fim, e o usuário recebe apenas o resultado final.

```
Usuário: *battle sales-letter --yolo
→ Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5 → Resultado Final
```

**Quando usar:** Tarefas de baixo risco, iterações rápidas, quando o custo é aceitável mesmo se o resultado não for perfeito.

### Interativo (Padrão)

Pausa após cada fase para aprovação humana antes de continuar. O usuário pode:
- **Aprovar** → Continua para próxima fase
- **Ajustar** → Modificar inputs ou config antes de continuar
- **Cancelar** → Encerra o Battle (estado salvo para possível retomada)

```
Usuário: *battle sales-letter
→ Fase 1 → [Aprovação] → Fase 2 → [Aprovação] → ... → Resultado Final
```

**Quando usar:** Primeira execução de um Battle em um squad, tarefas de alto valor, quando o custo por fase precisa ser controlado.

### Dry-Run Mode (FR3.2)

Executa apenas Fases 1 e 2 (Briefing + Produção), pausando para preview das produções antes de investir nas fases mais custosas (Votação, Debate, Board).

```
Usuário: *battle sales-letter --dry-run
→ Fase 1 → Fase 2 → [Preview das N produções] → [Continuar?] / [Cancelar]
```

**Quando usar:** Validar qualidade inicial das produções, testar configuração de equipes/ângulos, quando custo é uma preocupação.

---

## Estimativa de Custo e Tempo

### Equações de Estimativa

```
Custo por agente (produção) ≈ input_tokens × custo_input + output_tokens × custo_output
Total ≈ Σ(custo por fase)

Custos por modelo (aproximados):
- opus:   $0.015/1K input, $0.075/1K output
- sonnet: $0.003/1K input, $0.015/1K output
- haiku:  $0.00025/1K input, $0.00125/1K output
```

### Decomposição por Fase

| Fase | Agentes | Modelo | Tokens estimados | Custo estimado |
|------|---------|--------|-----------------|----------------|
| 1. Briefing | 1 chief | opus | ~2K in + 1K out | ~$0.11 |
| 2. Produção | N×M agentes | sonnet | ~3K in + 5K out por agente | ~$0.08/agente |
| 3. Votação | N líderes | sonnet | ~5K in + 2K out por votante | ~$0.05/votante |
| 4. Debate | 2 líderes + 1 juiz | opus (juiz) + sonnet (líderes) | ~3K in + 2K out × 3 rodadas | ~$0.45 |
| 5. Board | K revisores | opus | ~5K in + 3K out por revisor | ~$0.30/revisor |

### Exemplo: Copywriting Standard (3 equipes × 3 agentes)

```
Fase 1 — Briefing:
  1 chief (opus) × 3K tokens = ~$0.11

Fase 2 — Produção:
  9 agentes (sonnet) × ~8K tokens = ~$0.72

Fase 3 — Votação:
  3 líderes (sonnet) × ~7K tokens = ~$0.15

Fase 4 — Debate:
  2 líderes (sonnet) × 3 rodadas × ~4K tokens = ~$0.18
  1 juiz (opus) × 3 rodadas × ~5K tokens = ~$0.45

Fase 5 — Board:
  3 revisores (opus) × ~8K tokens = ~$0.90

TOTAL ESTIMADO: ~$2.51
TEMPO ESTIMADO: ~15–25 minutos
```

### Tabela Rápida por Configuração

| Config | Equipes | Agentes | Board | Custo | Tempo |
|--------|---------|---------|-------|-------|-------|
| Mínimo | 2×2 | 4 | 2 | ~$1.20 | ~10 min |
| Standard | 3×3 | 9 | 3 | ~$2.50 | ~20 min |
| Premium | 4×3 | 12 | 3 | ~$3.50 | ~25 min |
| Premium+ | 4×4 | 16 | 4 | ~$5.00 | ~30 min |

**Nota:** Premium+ (4 equipes, 16+ agentes) é experimental. Warning será emitido se total > 13 agentes.

---

## Estrutura de Diretório de Execução

Cada Battle produz o seguinte diretório:

```
.data/executions/{YYYY-MM-DD}_battle-{slug}/
├── battle-state.json           # Estado da máquina (atualizado após cada fase)
├── 00-battle-plan.md           # Plano do Battle (template)
├── 01-{team-a}-output.md       # Output da equipe A (gerado pela equipe)
├── 02-{team-b}-output.md       # Output da equipe B (gerado pela equipe)
├── 03-{team-c}-output.md       # Output da equipe C (gerado pela equipe)
├── 04-voting-results.md        # Resultados da votação (template)
├── 05-debate-transcript.md     # Transcrição do debate (template)
├── 06-board-review-r1.md       # Board review rodada 1 (template)
├── 07-board-review-r2.md       # Board review rodada 2 (se necessário)
├── 08-final-version.md         # Versão final aprovada (gerado)
└── 99-battle-report.md         # Relatório final (template)
```

Templates para os arquivos marcados com "(template)" estão em:
`templates/battle-logging/`

---

## Metadata

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Created | 2026-02-17 |
| Type | Workflow Template |
| Maintained By | Orchestrator (orquestrador-global) |
| Related | TEAM-PATTERNS.md, BATTLE-CONFIG-SCHEMA.md, templates/battle-logging/ |

## MEGABRAIN Deep Validation

- Last run: `20260514-validate-deep`
- Validator: `mega-brain/megabrain-chief`
- Mode: `deep`
- Workflow ID: `battle-round`
- Status: `pass`
- External execution: not performed during structural validation.
